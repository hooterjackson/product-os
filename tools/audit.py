#!/usr/bin/env python3
"""Re-check the record against reality. Read-only; proposes, never writes.

    python3 tools/audit.py                 the whole portfolio
    python3 tools/audit.py --since 2026-08-01
    python3 tools/audit.py --item GB-004   one item, in detail
    python3 tools/audit.py --json

This is the tool the system exists for. Everything else answers "what should I
work on"; this one answers "is any of that still true."

## Evidence matching is PATH-FIRST, and that is not a preference

The commit subjects in this portfolio include "map the fall that never comes"
and "draw the head the way it hangs, and deafen the journal to its own pulse".
No keyword rule matches those to an item, and a matcher built on message text
would silently attribute nothing while reporting success. So `paths:` globs are
primary; the item-ID mention is a fallback; keyword overlap is a last resort and
is always labelled weak.

## Group D is mandatory

An audit that reports "nothing changed" when it means "I recognised nothing" is
the single failure that would end trust in this tool, because it is
indistinguishable from success. Every commit in the window that no item claimed
is printed, by SHA and subject, every run. If group D is long, the seed is
missing items -- which is itself the finding.

## Four groups

    A  mechanical. Applies on a bare "merge".
    B  needs a decision. Proposed, never applied.
    C  refused, with the reason. Usually: no evidence.
    D  commits I could not attribute to anything.
"""

import argparse
import datetime
import fnmatch
import json
import os
import re
import subprocess
import sys

import _fm
import _git
import _model
import stale

DEFAULT_WINDOW_DAYS = 45

# Above this, a glob is describing a subsystem rather than an item's work.
BROAD_GLOB_COMMITS = 12


# --------------------------------------------------------------- repo access

class Repo(object):
    """One tracked repository, and how (or whether) we can read it."""

    def __init__(self, name, spec):
        self.name = name
        self.spec = spec or {}
        self.mode = None          # "local" | "api" | None
        self.local = None
        self.branch = self.spec.get("default_branch")
        self.reason = None
        self.commits = None       # [(sha, iso, subject)] within the window
        self.files = None         # sha -> [changed paths]
        self.tree = None          # every path at HEAD
        self.unread_files = set()  # shas whose file list could not be read
        self.claimed = set()      # shas some item claimed

    @property
    def reachable(self):
        return self.mode is not None

    def open(self):
        if not self.spec:
            self.reason = "not configured in state/repos.json"
            return False
        local = self.spec.get("local")
        if local:
            local = os.path.expanduser(local)
            if os.path.isdir(local):
                # fetch first, always. A stale tracking ref answers 0 and lies.
                if _git.fetch(local):
                    self.local = local
                    self.branch = self.branch or _git.default_branch(local)
                    self.mode = "local"
                    return True
                # No remote AT ALL is a different fact from a remote we failed
                # to reach. "Never fall back to the local ref" guards against
                # answering from a stale mirror of something authoritative
                # elsewhere; when nothing exists elsewhere, local IS the
                # record. product-os itself is in this state by decision.
                if _git.is_repo(local) and not _git.remotes(local):
                    self.local = local
                    self.mode = "local-only"
                    self.branch = None
                    return True
                self.reason = "clone present but fetch failed"
        if self.spec.get("owner"):
            self.mode = "api"
            self.branch = self.branch or "HEAD"
            return True
        if self.reason is None:
            self.reason = "no owner and no usable clone"
        return False


def _gh(path):
    try:
        proc = subprocess.run(["gh", "api", path], stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    try:
        return json.loads(proc.stdout.decode("utf-8", "replace"))
    except ValueError:
        return None


def commits(repo, since, path=None):
    """Commits in the window, optionally restricted to a path prefix.

    Returns a list of (sha, iso_date, subject), or UNREACHABLE. Never an empty
    list to mean "I could not look" -- that distinction is the whole point.
    """
    if repo.mode in ("local", "local-only"):
        ref = "origin/%s" % repo.branch if repo.mode == "local" else "HEAD"
        args = ["log", ref, "--no-merges",
                _git.DATE_FMT, "--since=%s" % since, "--format=%H\x1f%cd\x1f%s"]
        if path:
            args += ["--", path]
        out = (_git.fetch_then_query(repo.local, args) if repo.mode == "local"
               else _git._run(["git", "-C", repo.local] + args))
        if out is _git.UNREACHABLE or out is None:
            return _git.UNREACHABLE
        rows = []
        for line in out.splitlines():
            parts = line.split("\x1f")
            if len(parts) == 3:
                rows.append((parts[0][:7], parts[1], parts[2]))
        return rows
    if repo.mode == "api":
        query = "repos/%s/%s/commits?sha=%s&since=%sT00:00:00Z&per_page=100" % (
            repo.spec["owner"], repo.name, repo.branch, since)
        if path:
            query += "&path=%s" % path
        data = _gh(query)
        if data is None or not isinstance(data, list):
            return _git.UNREACHABLE
        return [(c["sha"][:7], c["commit"]["committer"]["date"],
                 c["commit"]["message"].split("\n")[0]) for c in data]
    return _git.UNREACHABLE


def commit_exists(repo, sha):
    """Does this SHA resolve, on this repo's default branch history?"""
    if repo.mode in ("local", "local-only"):
        out = (_git.fetch_then_query(repo.local, ["cat-file", "-t", sha])
               if repo.mode == "local"
               else _git._run(["git", "-C", repo.local, "cat-file", "-t", sha]))
        return out is not _git.UNREACHABLE and bool(out) and out.strip() == "commit"
    if repo.mode == "api":
        data = _gh("repos/%s/%s/commits/%s" % (repo.spec["owner"], repo.name, sha))
        return bool(data and data.get("sha"))
    return None


# ------------------------------------------------------------- path handling

_GLOB_CACHE = {}


def glob_re(pattern):
    """Compile a path glob where `*` stops at `/` and `**` does not.

    `fnmatch` will not do: its `*` crosses directory separators, so
    `docs/*.md` would match `docs/cad/renders/x.md` and an evidence rule
    scoped to one directory would quietly claim a subtree.
    """
    if pattern in _GLOB_CACHE:
        return _GLOB_CACHE[pattern]
    out, i = [], 0
    while i < len(pattern):
        ch = pattern[i]
        if ch == "*":
            if pattern[i:i + 2] == "**":
                out.append(".*")
                i += 2
                continue
            out.append("[^/]*")
        elif ch == "?":
            out.append("[^/]")
        else:
            out.append(re.escape(ch))
        i += 1
    compiled = re.compile("^" + "".join(out) + "$")
    _GLOB_CACHE[pattern] = compiled
    return compiled


def evidence_globs(node, repo_name):
    out = []
    for rule in node.get("evidence") or []:
        if rule.get("repo") != repo_name:
            continue
        for pattern in rule.get("paths") or []:
            out.append(pattern)
    return out


class FileCache(object):
    """sha -> [changed paths], on disk under `.cache/` (git-ignored).

    Safe to cache forever: a commit's SHA is a hash of its content, so its
    file list is immutable by construction. Nothing here is authority --
    delete the directory and the next run rebuilds it.
    """

    def __init__(self, repo):
        root = _model.find_root()
        self.path = os.path.join(root, ".cache", "audit",
                                 "%s-files.json" % repo.name)
        self.data = {}
        self.dirty = False
        try:
            with open(self.path, "r", encoding="utf-8") as fh:
                loaded = json.load(fh)
            if isinstance(loaded, dict):
                self.data = loaded
        except (OSError, ValueError):
            pass

    def get(self, sha):
        return self.data.get(sha)

    def put(self, sha, paths):
        self.data[sha] = paths
        self.dirty = True

    def flush(self):
        if not self.dirty:
            return
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as fh:
                json.dump(self.data, fh)
        except OSError:
            pass


def load_tree(repo):
    """Every path in the repo at HEAD. One call, used to decide satisfiability.

    "This rule matched nothing" and "this rule CAN NEVER match" were the same
    code path, and an item whose rule cannot fire sat silently at `next`
    forever. That is how EL-001 -- a purchase whose parts are photographed on
    the bench -- stayed the top-ranked item in the portfolio.
    """
    if repo.tree is not None:
        return repo.tree
    repo.tree = []
    if repo.mode in ("local", "local-only"):
        ref = "origin/%s" % repo.branch if repo.mode == "local" else "HEAD"
        out = (_git.fetch_then_query(repo.local, ["ls-tree", "-r", "--name-only", ref])
               if repo.mode == "local"
               else _git._run(["git", "-C", repo.local, "ls-tree", "-r",
                               "--name-only", ref]))
        if out and out is not _git.UNREACHABLE:
            repo.tree = out.splitlines()
        return repo.tree
    if repo.mode == "api":
        data = _gh("repos/%s/%s/git/trees/%s?recursive=1"
                   % (repo.spec["owner"], repo.name, repo.branch))
        if data and isinstance(data.get("tree"), list):
            repo.tree = [e.get("path", "") for e in data["tree"]
                         if e.get("type") == "blob"]
    return repo.tree


# How a rule relates to reality. The distinction this enum exists to make is
# the whole point: only one of these means "nothing has happened".
SATISFIABLE = "satisfiable"        # matches real files that do get committed
NEVER_FIRED = "never-fired"        # matches real files nothing has ever touched
UNSATISFIABLE = "unsatisfiable"    # matches no path in the repo at all


def classify_rule(repo, pattern):
    """Can a commit to this glob ever demonstrate anything?"""
    tree = load_tree(repo)
    if not tree:
        return None                      # could not read the tree; say nothing
    matcher = glob_re(pattern)
    hits = [p for p in tree if matcher.match(p)]
    if not hits:
        return UNSATISFIABLE
    # `is not None`, not truthiness: an EMPTY dict means "this repo produced no
    # commits", which is a fact worth classifying, not missing data.
    if repo.files is not None:
        touched = {p for paths in repo.files.values() for p in paths}
        if not any(matcher.match(p) for p in touched):
            return NEVER_FIRED
    return SATISFIABLE


def load_files(repo, since, progress=True):
    """repo.files[sha] = [paths]. One pass, shared by every item.

    Attribution runs against real filenames rather than a directory prefix,
    because a prefix is not a glob: `captures/gimbal10/fixture/ring-*.md`
    reduced to its prefix claims all 98 commits under that directory, which
    is over-attribution dressed as evidence.
    """
    if repo.files is not None or repo.commits is None:
        return
    repo.files = {}
    if repo.mode in ("local", "local-only"):
        ref = "origin/%s" % repo.branch if repo.mode == "local" else "HEAD"
        args = ["log", ref, "--no-merges", "--name-only",
                "--since=%s" % since, "--format=%x00%H"]
        out = (_git.fetch_then_query(repo.local, args) if repo.mode == "local"
               else _git._run(["git", "-C", repo.local] + args))
        if out is _git.UNREACHABLE or out is None:
            repo.files = None
            return
        for block in out.split("\x00")[1:]:
            lines = [ln for ln in block.splitlines() if ln.strip()]
            if lines:
                repo.files[lines[0][:7]] = lines[1:]
        return
    # A commit's file list never changes, so it is cached on disk. Without
    # this the API path costs one request per commit EVERY run -- ~100
    # sequential calls, several minutes, for a tool whose whole premise is
    # that you sit down with it repeatedly. A re-audit has to be cheap or it
    # does not get run, and a tool that does not get run is worth nothing.
    cache = FileCache(repo)
    total = len(repo.commits)
    progress = progress and sys.stderr.isatty()
    misses = 0
    for index, (sha, _date, _subject) in enumerate(repo.commits, 1):
        hit = cache.get(sha)
        if hit is not None:
            repo.files[sha] = hit
            continue
        misses += 1
        if progress:
            sys.stderr.write("\r  reading %s file lists %d/%d" % (repo.name, index, total))
            sys.stderr.flush()
        data = _gh("repos/%s/%s/commits/%s" % (repo.spec["owner"], repo.name, sha))
        if data is None:
            repo.unread_files.add(sha)
            continue
        paths = [f.get("filename", "") for f in data.get("files") or []]
        repo.files[sha] = paths
        cache.put(sha, paths)
    if misses:
        cache.flush()
    if progress and total:
        sys.stderr.write("\r" + " " * 60 + "\r")
        sys.stderr.flush()


# ------------------------------------------------------------------ findings

class Finding(object):
    def __init__(self, group, item, headline, detail=None, shas=None,
                 change=None):
        self.group = group
        self.item = item
        self.headline = headline
        self.detail = detail or []
        self.shas = shas or []
        self.change = change     # {"field": value} an agent may actually write

    def as_dict(self):
        return {"group": self.group, "item": self.item,
                "headline": self.headline, "detail": self.detail,
                "shas": self.shas, "change": self.change}


def audit(root, since, only_item=None):
    model = _model.Model.load(root)
    repo_specs = stale.load_repos(root)

    wanted = set()
    for node in model.nodes.values():
        for name in node.get("repos") or []:
            wanted.add(name)
    for decision in model.decisions.values():
        for target in decision.get("propagates_to") or []:
            if target.get("repo"):
                wanted.add(target["repo"])

    repos = {}
    for name in sorted(wanted):
        repo = Repo(name, repo_specs.get(name))
        repo.open()
        repos[name] = repo

    # Whole-repo commit lists, for group D. Do this before attribution so an
    # unreachable repo is a stated gap rather than an empty group.
    for repo in repos.values():
        if not repo.reachable:
            continue
        rows = commits(repo, since)
        if rows is _git.UNREACHABLE:
            repo.mode = None
            repo.reason = "commit query failed after a successful fetch"
            repo.commits = None
        else:
            repo.commits = rows
            load_files(repo, since)

    findings = []
    items = sorted(model.items.values(), key=lambda n: _fm.sort_key(n.id))
    if only_item:
        items = [n for n in items if n.id == only_item.upper()]

    for node in items:
        findings.extend(audit_item(node, repos, since))

    # --- the ruling-vs-document case, generalised in rather than duplicated
    reached, unreachable = set(), set()
    st_findings, st_skipped = stale.find_stale(model, repo_specs, reached,
                                               unreachable)
    for f in st_findings:
        findings.append(Finding(
            "B", None,
            "%s is %d days behind %s" % (f["doc"], f["days_stale"], f["decision"]),
            ["%s last edited %s; %s ruled %s."
             % (f["repo"], f["doc_last_edited"], f["decision"], f["decided"]),
             "The doc still claims: %s" % f["claim"]]))

    # Group D = every commit no FINDING mentioned -- deliberately not "every
    # commit some glob touched".
    #
    # The difference bit immediately. `EL-004` is done and its rule is
    # `docs/**`, so the attribution scan had it claiming all five Doc 4a
    # commits; group D then printed nothing for the site, which reads as "the
    # seed covers the site" and actually meant "a broad rule on a finished item
    # ate them". That is precisely the "nothing changed" / "I recognised
    # nothing" confusion this group exists to prevent, reproduced inside the
    # tool written to prevent it. Only a reported SHA counts as recognised.
    reported = {}
    for f in findings:
        for sha in f.shas:
            reported.setdefault(sha, set()).add(f.item)

    unattributed = {}
    for name, repo in repos.items():
        if repo.commits is None:
            continue
        rest = [c for c in repo.commits if c[0] not in reported]
        if rest:
            unattributed[name] = rest

    coverage = {
        "window_since": since,
        "expected": sorted(wanted),
        "reached": sorted(n for n, r in repos.items() if r.reachable),
        "unreachable": {n: r.reason for n, r in repos.items() if not r.reachable},
        "stale_pairs_skipped": st_skipped,
    }
    return findings, unattributed, coverage, model


def audit_item(node, repos, since):
    out = []
    names = node.get("repos") or []
    if not names:
        return out

    attributed = []          # (repo, sha, date, subject, how)
    could_not_look = []
    dead_globs = []

    for name in names:
        repo = repos.get(name)
        if repo is None or not repo.reachable or repo.commits is None:
            reason = (repo.reason if repo else "not configured")
            could_not_look.append((name, reason or "unreachable"))
            continue
        if repo.files is None:
            could_not_look.append((name, "could not read commit file lists"))
            continue
        if not repo.commits:
            # Reachable, and it told me nothing. That is NOT evidence of
            # nothing happening, and it must never render as silence.
            # HomeApp is the live case: one squashed commit dated 2026-06-12,
            # so every window after that date is empty by construction and a
            # commit-shaped question about this project is unanswerable rather
            # than answered "no".
            note = repo.spec.get("note")
            could_not_look.append(
                (name, "reachable, but no commits in the window%s"
                       % (" — %s" % note if note else "")))
            # Satisfiability is a property of the TREE, not of the window, so
            # it is still decidable here -- and this is exactly where an
            # unsatisfiable rule hides best, behind a repo that says nothing.
            dead_globs.extend((name, p) for p in evidence_globs(node, name))
            continue

        globs = evidence_globs(node, name)

        # 1 · PATH-FIRST. The primary matcher, run alone and run first,
        #     against real filenames.
        for pattern in globs:
            matcher = glob_re(pattern)
            hit = False
            for sha, date, subject in repo.commits:
                paths = repo.files.get(sha)
                if not paths:
                    continue
                for path in paths:
                    if matcher.match(path):
                        attributed.append((name, sha, date, subject,
                                           "path %s" % path))
                        hit = True
                        break
            if not hit:
                dead_globs.append((name, pattern))

        # 2 · FALLBACK: the item ID written into a commit message. Only for
        #     commits no path rule claimed. Subjects here read "map the fall
        #     that never comes", so this catches little and is never primary.
        claimed_here = {a[1] for a in attributed}
        for sha, date, subject in repo.commits:
            if sha in claimed_here:
                continue
            if node.id in _fm.MENTION_RE.findall(subject):
                attributed.append((name, sha, date, subject, "id-mention"))

        if repo.unread_files:
            could_not_look.append(
                (name, "%d commit file list(s) unread, so path matching is "
                       "incomplete" % len(repo.unread_files)))

    # dedupe, newest first
    seen, rows = set(), []
    for row in sorted(attributed, key=lambda r: r[2], reverse=True):
        if row[1] in seen:
            continue
        seen.add(row[1])
        rows.append(row)

    for name, reason in could_not_look:
        out.append(Finding(
            "C", node.id,
            "I couldn't look at %s" % name,
            ["%s." % reason.rstrip("."),
             "This item's status is unaudited, which is not the same as "
             "unchanged."]))

    # An evidence rule that cannot fire leaves an item at `next` forever while
    # its work lands somewhere the rule cannot see. Until now "matched nothing"
    # and "can never match" were the same finding, which is how EL-001 stayed
    # top-ranked with its parts photographed on the bench.
    for name, pattern in dead_globs:
        repo = repos.get(name)
        verdict = classify_rule(repo, pattern) if repo else None
        if verdict == UNSATISFIABLE:
            out.append(Finding(
                "B", node.id,
                "no path in %s matches `%s`" % (name, pattern),
                ["Two readings, and only a person can pick: **(a) the rule is "
                 "wrong** and the item can never close no matter what work is "
                 "done, or **(b) the rule is right and the file does not exist "
                 "yet** — correct for an item whose completion CREATES it.",
                 "(b) is the good case. It stops being good the day the work "
                 "lands somewhere else.",
                 "The `evidence` rule is human-authority. Proposed, not changed."],
                change={"evidence": "repoint"}))
        elif verdict == NEVER_FIRED:
            out.append(Finding(
                "B", node.id,
                "rule `%s` matches real files that nothing has touched" % pattern,
                ["The paths exist in %s; no commit in the window changed them."
                 % name,
                 "**\"has not fired\" and \"cannot fire\" look identical from "
                 "here.** If completing this item would not change these files "
                 "— a purchase, a phone call, a browser-local checkbox — the "
                 "rule is unsatisfiable and only a person can tell."]))
        else:
            out.append(Finding(
                "B", node.id,
                "rule `%s` matched nothing in the window" % pattern,
                ["The paths exist and do get committed; nothing touched them "
                 "since %s. Most likely nothing has happened." % since]))

    known = {str(e.get("sha") or "")[:7]
             for e in (node.get("evidence_found") or [])}

    # --- done items: verify what they claim, do not take it on trust
    if node.status == "done":
        for entry in node.get("evidence_found") or []:
            name, sha = entry.get("repo"), str(entry.get("sha") or "")
            repo = repos.get(name)
            if repo is None or not repo.reachable:
                out.append(Finding(
                    "C", node.id,
                    "cannot verify the evidence for a done item",
                    ["%s is unreachable, so `%s` is unchecked." % (name, sha)]))
                continue
            ok = commit_exists(repo, sha)
            if ok is False:
                out.append(Finding(
                    "C", node.id,
                    "claimed evidence does not resolve",
                    ["`%s` is recorded as evidence in %s and does not exist "
                     "there. A completion nobody can click is not a "
                     "completion." % (sha, name)], shas=[sha]))
        return out

    # --- live items with commits touching their evidence paths
    fresh = [r for r in rows if r[1] not in known]
    if not fresh:
        return out

    # A glob that claims most of a repo's traffic is not evidence OF THIS ITEM.
    # `sketches/gimbal/gimbal.ino` is touched by every firmware commit there
    # is, so it identifies the subsystem and not the work -- which reads as a
    # confident attribution and is worth less than no attribution at all.
    if len(fresh) > BROAD_GLOB_COMMITS:
        out.append(Finding(
            "B", node.id,
            "evidence rule is too broad to attribute anything (%d commits)"
            % len(fresh),
            ["Its paths matched %d commits in the window — that identifies the "
             "subsystem, not this item's work." % len(fresh),
             "Newest: %s  %s" % (fresh[0][1], fresh[0][3]),
             "Narrow the rule to files this item alone would touch. The rule "
             "is human-authority, so this is a proposal."]))
        return out

    detail = ["%s touching this item's evidence paths since %s:"
              % ("%d commits" % len(fresh) if len(fresh) > 1 else "1 commit",
                 since)]
    for name, sha, date, subject, how in fresh[:8]:
        detail.append("  %s  %s  %s  (%s)" % (sha, date[:10], subject, how))
    if len(fresh) > 8:
        detail.append("  ... and %d more" % (len(fresh) - 8))
    out.append(Finding(
        "A", node.id,
        "record %d commit(s) as evidence_found" % len(fresh),
        detail, shas=[r[1] for r in fresh],
        change={"evidence_found": "append", "updated": "today"}))
    out.append(Finding(
        "B", node.id,
        "status is %r — has this landed?" % node.status,
        ["Evidence arrived that this item does not know about. Closing it "
         "needs somebody to read the commits above and say what they prove. "
         "I will not infer `done` from a path match."]))
    return out


# -------------------------------------------------------------------- output

GROUP_TITLES = {
    "A": "A · mechanical — applies on a bare \"merge\"",
    "B": "B · escalated — I will not decide these",
    "C": "C · refused, with the reason",
}


def render(findings, unattributed, coverage, model):
    lines = []
    lines.append("# audit · %s" % coverage["window_since"] + " → now")
    lines.append("")

    for group in ("A", "B", "C"):
        rows = [f for f in findings if f.group == group]
        lines.append("## %s   (%d)" % (GROUP_TITLES[group], len(rows)))
        lines.append("")
        if not rows:
            lines.append("  nothing.")
            lines.append("")
            continue
        for f in rows:
            head = "  %s%s" % (("[%s] " % f.item) if f.item else "", f.headline)
            lines.append(head)
            for d in f.detail:
                lines.append("    " + d)
            lines.append("")

    # --- D is mandatory and printed even when empty, so its absence is a fact
    total = sum(len(v) for v in unattributed.values())
    lines.append("## D · commits I could not attribute to any item   (%d)" % total)
    lines.append("")
    lines.append("  These landed in the window and no item's evidence paths "
                 "claimed them.")
    lines.append("  A short list means the seed covers the work. A long one "
                 "means it does not —")
    lines.append("  and that is the finding, not a tool failure.")
    lines.append("")
    if not total:
        lines.append("  nothing unattributed.")
        lines.append("")
    for name in sorted(unattributed):
        rows = unattributed[name]
        lines.append("  %s  (%d)" % (name, len(rows)))
        for sha, date, subject in rows[:14]:
            lines.append("    %s  %s  %s" % (sha, date[:10], subject))
        if len(rows) > 14:
            lines.append("    ... and %d more" % (len(rows) - 14))
        lines.append("")

    # --- coverage, always, by name
    lines.append("## Coverage")
    lines.append("")
    lines.append("  expected:    " + (", ".join(coverage["expected"]) or "none"))
    lines.append("  reached:     " + (", ".join(coverage["reached"]) or "NOTHING"))
    if coverage["unreachable"]:
        lines.append("  unreachable:")
        for name, why in sorted(coverage["unreachable"].items()):
            lines.append("    %-22s %s" % (name, why))
    else:
        lines.append("  unreachable: none")
    if coverage["stale_pairs_skipped"]:
        lines.append("  %d ruling/doc pair(s) could not be checked."
                     % len(coverage["stale_pairs_skipped"]))
    lines.append("")
    lines.append("  An unreachable repo means I couldn't look. It does not mean "
                 "nothing changed.")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--since", help="YYYY-MM-DD; default 45 days back")
    parser.add_argument("--item", help="audit one item in detail")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    since = args.since
    if not since:
        since = (datetime.date.today()
                 - datetime.timedelta(days=DEFAULT_WINDOW_DAYS)).isoformat()
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", since):
        sys.stderr.write("--since must be YYYY-MM-DD\n")
        return 2

    root = _model.find_root()
    findings, unattributed, coverage, model = audit(root, since, args.item)

    if args.json:
        print(json.dumps({
            "findings": [f.as_dict() for f in findings],
            "unattributed": unattributed,
            "coverage": coverage,
        }, indent=2, sort_keys=True))
        return 0

    print(render(findings, unattributed, coverage, model))
    return 0


if __name__ == "__main__":
    sys.exit(main())
