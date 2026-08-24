#!/usr/bin/env python3
"""Shared context helpers: the register, the audit stamp, freshness, handoffs.

Not an artifact. This module was `brief.py`, which generated a second per-item
document alongside the kickoff prompt -- and `kickoff.py`'s output turned out to
be a superset of it except for two sections, both of which now live there
(`R-071`). Two surfaces rendering the same content is how they drift apart, and
drift inside an excerpt is `R-065`.

What survived the brief is everything that was actually load-bearing:

    parse_register      wiki/ruled-out.md -> (title, keywords, first paragraph)
    ruled_out_for       the keyword match that decides which entries a task meets
    read_stamp          the audit stamp
    freshness           one honest line, always -- see its own docstring
    whats_next          the last handoff's Next line, or a stated absence
    decisions_in_force  the rulings a task is parented to
"""

import datetime
import json
import os
import re

import _fm
import _git

# The DURABLE half of the audit stamp, tracked and sharded per machine. The
# live half -- per-repo HEAD shas, used only by the volatile freshness probe --
# stays in git-ignored build/, because a sha is a fact about one working copy.
STAMP_SHARD = "stamp.json"
LOCAL_STAMP = "build/audit-stamp.json"
REGISTER = "wiki/ruled-out.md"
MAX_RULED_OUT = 4


def parse_register(root):
    path = os.path.join(root, REGISTER)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    entries = []
    for chunk in re.split(r"\n## ", "\n" + text)[1:]:
        title = chunk.split("\n", 1)[0].strip()
        match = re.search(r"^\*\*keywords:\*\*(.+)$", chunk, re.M)
        if not match:
            continue
        cut = re.search(r"\n(?:---\s*$|# )", chunk, re.M)
        body = chunk[:cut.start()] if cut else chunk
        words = {w.strip().lower() for w in re.split(r"[·,]", match.group(1))
                 if w.strip()}
        # Collect the first whole PARAGRAPH, not the first line. A single line
        # from the middle of a wrapped paragraph ends mid-clause and reads as a
        # transcription error rather than an excerpt.
        first, buf = "", []
        for line in body.splitlines()[1:]:
            line = line.strip()
            if line.startswith(("**keywords", "**source")):
                continue
            if not line:
                if buf:
                    break
                continue
            if line.startswith(("|", "#")):
                continue
            buf.append(line.lstrip("> "))
        if buf:
            first = " ".join(buf)
        entries.append((title, words, first))
    return entries


def read_stamp(root):
    """The newest audit stamp, from TRACKED per-machine shards.

    This read `build/audit-stamp.json` and `build/` is git-ignored, so the
    entire published surface was generated from a file that does not travel.
    Measured in a clean clone with no `build/`: **88 files out of sync**, and
    `publish.py --check` fails on every machine that has not run an audit --
    CI included, permanently.

    That is the same shape as `R-067` one directory over. There the bytes moved
    with the calendar; here they move with which machine ran `publish`. Both
    make a committed artifact unreproducible, and both make the gate red by
    default, which is how a gate stops being read.

    Sharded rather than shared because an audit is a machine's observation:
    `state/audits/<machine>/stamp.json`, the same discipline the thread index
    already follows. Newest wins.
    """
    base = os.path.join(root, "state", "audits")
    if not os.path.isdir(base):
        return None
    best = None
    for machine in sorted(os.listdir(base)):
        path = os.path.join(base, machine, STAMP_SHARD)
        if not os.path.exists(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, ValueError):
            continue
        if not isinstance(data, dict) or not data.get("date"):
            continue
        if best is None or data["date"] > best["date"]:
            best = data
    return best


def read_local_stamp(root):
    """The live half: per-repo HEADs, for the volatile probe only. Never
    published -- a sha names one working copy."""
    path = os.path.join(root, LOCAL_STAMP)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def freshness(root, node, stamp, repos_spec, volatile=True):
    """One line, always. Names what it could not check.

    `volatile=False` means "this line is about to be COMMITTED", and drops
    every quantity that is a property of this machine at this moment rather
    than of the audit:

        the "+N commits since the audit" delta   -- moves with local HEAD
        the "(2 days ago)" age                   -- moves with the calendar
        "could not check X offline"              -- moves with what is cloned here

    All three make a committed copy wrong without anything in `state/`
    changing. The delta was measured at `+9` before a commit and `+10` after,
    which is `R-061`.

    `R-067` is the same defect four lines further down, left behind by that
    fix: the age. Measured 2026-08-20 -- `publish.py --check` reported **121
    files out of sync on a clean tree**, the whole difference being
    `(today)` -> `(1 day ago)`. `validate.py` was therefore red every day but
    the audit's, which trains a reader to regenerate-and-commit or to stop
    looking. **A guardrail that is red by default is off.**

    So the published surface carries only the DURABLE half: when the last
    audit ran and what it found. That does not move between audits, and it is
    identical on every machine. The live delta stays in `build/`, for the
    person at the keyboard who can act on it -- and, from Phase 2, in
    `index.html`, where a `data-audit-date` attribute lets the browser render
    the age without the bytes ever changing.
    """
    if not stamp:
        return ("(no audit has ever run — freshness unknown. "
                "`python3 tools/audit.py` sets this.)")
    when = stamp.get("date", "?")
    found = ("" if stamp.get("group_d") is None
             else " · %d commits unattributed then" % stamp["group_d"])

    if not volatile:
        return "last audit %s%s" % (when, found)

    age = ""
    try:
        days = (datetime.date.today()
                - datetime.date.fromisoformat(when)).days
        age = "today" if days == 0 else "%d day%s ago" % (days, "" if days == 1 else "s")
    except ValueError:
        pass

    # Offline delta, where a local clone exists. Repos without one are NAMED,
    # never silently treated as unchanged.
    local = read_local_stamp(root) or {}
    moved, unchecked = [], []
    for name in node.get("repos") or []:
        head = (local.get("heads") or {}).get(name)
        spec = repos_spec.get(name) or {}
        local = spec.get("local")
        local = os.path.expanduser(local) if local else None
        if not head or not local or not os.path.isdir(local):
            unchecked.append(name)
            continue
        out = _git._run(["git", "-C", local, "rev-list", "--count",
                         "%s..HEAD" % head])
        if out is None:
            unchecked.append(name)
            continue
        try:
            n = int(out)
        except ValueError:
            unchecked.append(name)
            continue
        if n:
            moved.append("%s +%d" % (name, n))

    line = ("last audit %s (%s)%s" % (when, age, found) if age
            else "last audit %s%s" % (when, found))
    if moved:
        line = "⚠ %s since the last audit — %s" % (", ".join(moved), line)
    if unchecked:
        line += " · could not check %s offline" % ", ".join(sorted(unchecked))
    return line


def ruled_out_for(node, entries):
    keywords = {str(k).strip().lower() for k in (node.get("keywords") or [])}
    if not keywords:
        return []
    scored = []
    for title, words, first in entries:
        overlap = keywords & words
        if overlap:
            scored.append((len(overlap), title, first, sorted(overlap)))
    scored.sort(key=lambda r: (-r[0], r[1]))
    return scored[:MAX_RULED_OUT]


def whats_next(node):
    """The last handoff's Next line, or an honest absence."""
    body = node.body or ""
    nexts = re.findall(r"^\*\*Next:\*\*\s*(.+)$", body, re.M)
    if nexts:
        return nexts[-1].strip()
    return None


def decisions_in_force(node, model):
    out = []
    parent = node.get("parent_ruling")
    if parent and parent in model.decisions:
        d = model.decisions[parent]
        out.append((d.id, d.get("ruling_id"), d.title))
    for decision in sorted(model.decisions.values(), key=lambda d: d.id):
        if decision.id == parent:
            continue
        if decision.project == node.project and decision.get("propagates_to"):
            out.append((decision.id, decision.get("ruling_id"), decision.title))
    return out[:4]


# --- where the work happens, and how to get there ---------------------------
#
# `site.py` will want to offer a way in -- the terminal is one of the three
# paste destinations and a Copy button is the product. That is the moment this
# becomes dangerous, because a card that renders `cd ~/Claude/gimbal-bench`
# from a template is wrong on this machine and looks right.
#
# Measured 2026-08-20: FOUR of the six repos in `state/repos.json` have
# `local: null` -- HomeApp, genio, gimbal-bench and home-ai-infra are not
# cloned on this Mac. `GB-001` is `machine_affinity: formd-t1`, a Windows box.
# A templated `cd ~/Claude/<repo> && claude` is wrong for most of the
# portfolio.
#
# `kickoff.py` does not have this bug, but it is worth being precise about WHY:
# it is right BY OMISSION, not by derivation. It names a repo and a machine and
# emits no path at all, so it cannot emit a wrong one. Its single `$` command
# comes from the thread indexer, where `resume_command()` already returns None
# when the binary is absent. That safety does not transfer to something that
# wants to offer a command.
#
# So the rule is enforced here, once, by construction: a command comes back
# ONLY when the repo is cloned on this machine AND the task is not bound
# elsewhere. Every other case returns a command of None and says why.

NO_REPO = "no-repo"          # the project has no repository at all
ELSEWHERE = "elsewhere"      # bound to another machine
NO_CLONE = "no-clone"        # repo exists, not cloned here
LOCAL = "local"              # cloned here, and this is the right machine


def reach(node, model, repos_spec, machine):
    """How to get to this task's work FROM THIS MACHINE.

    Returns {kind, command, repos, machine, reason}. `command` is None in
    every case but `LOCAL`, and callers must render it rather than build their
    own -- that is the whole point of this function existing.
    """
    project = model.projects.get(node.project)
    repos = list(node.get("repos") or [])
    if not repos and project:
        repos = list(project.get("repos") or [])

    def out(kind, reason, command=None):
        return {"kind": kind, "command": command, "repos": repos,
                "machine": node.get("machine_affinity"), "reason": reason}

    if not repos:
        return out(NO_REPO,
                   "%s has no repository. Nothing here can be verified from "
                   "commits, so its status changes only when Marcelo says so."
                   % (node.project or "this project"))

    affinity = node.get("machine_affinity")
    if affinity and affinity != machine:
        # Checked BEFORE the clone test on purpose. Even a cloned repo is the
        # wrong answer when the work is bound to another machine -- the bench
        # is not this laptop, and a command that runs is not a command that
        # helps.
        return out(ELSEWHERE,
                   "This is %s work. The honest answer is \"resume on %s\", "
                   "not a plan that cannot be executed from here."
                   % (affinity, affinity))

    missing = []
    paths = []
    for name in repos:
        local = (repos_spec.get(name) or {}).get("local")
        expanded = os.path.expanduser(local) if local else None
        if expanded and os.path.isdir(expanded):
            paths.append(local)
        else:
            missing.append(name)
    if missing:
        return out(NO_CLONE,
                   "%s %s not cloned on %s. Clone it, or work on a machine "
                   "that has it — there is no command to give you from here."
                   % (", ".join("`%s`" % m for m in missing),
                      "is" if len(missing) == 1 else "are", machine))

    return out(LOCAL,
               "Cloned here. product-os TRACKS the work; it does not host it.",
               command="cd %s" % paths[0])


def last_handoff(nodes):
    """The most recent handoff's `**Did:**`, in English, across a group.

    Recency has to come from handoffs, not from `updated`. The migration
    stamped every one of the 41 items `2026-08-20`, so that field cannot
    express recency at all -- it says only when the schema last changed.
    Handoffs are dated, machine-stamped and already written for a human, which
    makes them the only honest source for a "last session" line.

    Returns None when nobody has written one. Five of six projects are in that
    state, and the card must SAY so rather than render an empty heading: the
    absence of a record is not the absence of a fact.
    """
    best = None
    for node in nodes:
        body = node.body or ""
        for match in re.finditer(r"^### (\d{4}-\d{2}-\d{2})[^\n]*\n"
                                 r"\*\*Did:\*\*\s*(.+?)(?=\n\n|\n\*\*|\Z)",
                                 body, re.S | re.M):
            when, said = match.group(1), " ".join(match.group(2).split())
            if best is None or when >= best[0]:
                best = (when, said, node.id)
    if best is None:
        return None
    return {"date": best[0], "said": best[1], "item": best[2]}


def latest_audit(root):
    """The TL;DR the audit wrote, from the newest per-machine shard.

    Sharded rather than kept in `build/`: `build/` is git-ignored, so a machine
    without a stamp would silently publish a page with no TL;DR at all and
    `publish.py --check` would call it drift. Machine-derived data is sharded,
    never shared -- the same rule the thread index already follows.

    Returns None before any audit has run, which is a real state on day one and
    renders as a stated absence.
    """
    base = os.path.join(root, "state", "audits")
    if not os.path.isdir(base):
        return None
    newest = None
    for machine in sorted(os.listdir(base)):
        path = os.path.join(base, machine, "latest.md")
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read().strip()
        stamp = os.path.getmtime(path)
        if text and (newest is None or stamp > newest[0]):
            newest = (stamp, text, machine)
    return None if newest is None else newest[1]


# --- the pointer rule ------------------------------------------------------
#
# Stated ONCE, here, because a rule that lives in one tool's docstring is a
# rule applied to one of two sources by construction -- which is `R-067` and
# has now cost three separate fixes.
#
# `manual.yaml` was never the only route a chat URL could reach a public
# surface. Three were live at the same time:
#
#     kickoff.py       "paste its URL into state/threads/manual.yaml"
#     publish.py       the threads.json note, saying the same
#     the design       "put the chat's URL in the task's GitHub issue"
#
# product-os is public, so its issues are world-readable -- and the issue is
# the PRIMARY path the design ships for web chats, which is exactly the case
# `manual.yaml` exists for. Untracking one file closed the narrow route and
# left the wide one open.
#
# So it is a rule about the DATA, not about a file:

POINTER_RULE_PUBLIC = (
    "PRESENCE is public: which task has a chat, which machine holds it, and "
    "when it was recorded.")
POINTER_RULE_LOCAL = (
    "THE URL IS LOCAL, wherever it is written — never a tracked file, never a "
    "GitHub issue, never a generated page.")


def pointer_rule(one_line=False):
    """The sentence every instruction site must use, so they cannot drift."""
    if one_line:
        return "%s %s" % (POINTER_RULE_PUBLIC, POINTER_RULE_LOCAL)
    return [POINTER_RULE_PUBLIC, POINTER_RULE_LOCAL]


def tracked_shards(root):
    """The TRACKED thread shards, never the git-ignored local halves.

    Five call sites globbed `by-machine/*.json` independently and
    `<machine>.local.json` matches that pattern. Two of them were fixed when
    the shard was split and three were not, so `publish.py --check` drifted on
    any machine that had never indexed -- CI every time -- because the local
    file exists here and nowhere else.

    A predicate spread across five call sites is five chances to get it wrong,
    and it got it wrong three times out of five. One function now.
    """
    shard_dir = os.path.join(root, "state", "threads", "by-machine")
    if not os.path.isdir(shard_dir):
        return []
    return [os.path.join(shard_dir, name)
            for name in sorted(os.listdir(shard_dir))
            if name.endswith(".json") and not name.endswith(".local.json")]


def machines(root):
    """Registered machines, by id. `product_os` is where the checkout lives on
    that machine, or None if it is not installed there.

    A path here is a FACT ABOUT A NAMED MACHINE, not a claim about whoever is
    reading. That is the distinction the whole surface runs on: `on formd-t1`
    is durable, `elsewhere` is a comparison. So a page may print
    `cd ~/Claude/product-os` when it says "on work-laptop" first, and may not
    print it bare.
    """
    out = {}
    base = os.path.join(root, "state", "machines")
    if not os.path.isdir(base):
        return out
    for name in sorted(os.listdir(base)):
        if not name.endswith(".json"):
            continue
        try:
            with open(os.path.join(base, name), "r", encoding="utf-8") as fh:
                spec = json.load(fh)
        except (OSError, ValueError):
            continue
        if spec.get("id"):
            out[spec["id"]] = spec
    return out


# --- which project a chat belongs to ----------------------------------------

ATTRIBUTION = "state/threads/attribution.yaml"
NOT_MINE = "none"


def attributions(root):
    """thread key -> project slug, or NOT_MINE. Hand-written, tracked.

    A chat's project cannot be derived for most chats: 10 of 15 here cite no
    task at all, and several are not this portfolio in any sense -- a playlist
    tool, an entitlements parser. So attribution is HIS, written once per chat
    and surviving re-indexing, which regenerates the shard wholesale.

    Tracked, and safe to track: a project slug and a thread key, where the key
    is a 12-character hash that cannot resume anything. No url, no session id,
    no path -- the split `R-076` established.
    """
    out = {}
    path = os.path.join(root, ATTRIBUTION)
    if not os.path.exists(path):
        return out
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.split("#", 1)[0].strip()
            if not line or ":" not in line:
                continue
            key, _, value = line.partition(":")
            value = value.strip()
            if value:
                out[key.strip()] = value
    return out


def chat_projects(thread, attributed):
    """Every project this chat touches. Explicit attribution wins.

    Derived from the ID PREFIX, not from a live lookup. Resolving against
    loaded items meant archiving the product-os build history silently orphaned
    four chats that were entirely about product-os -- the tasks left the model
    and took the chats' identity with them. A prefix outlives the task.
    """
    said = attributed.get(thread.get("key"))
    if said == NOT_MINE:
        return set()
    if said:
        return {said}
    if not _fm.prefixes():
        # Loud, not empty. Without the prefix set every chat resolves to no
        # project and the page renders them all as unattributed -- a wrong
        # answer that looks exactly like a correct one, which is R-075.
        raise RuntimeError(
            "prefix set not loaded -- call _model.Model.load() first. "
            "Without it every chat attributes to nothing, and a section of "
            "unattributed chats is indistinguishable from the truth.")
    out = set()
    for item in thread.get("items") or []:
        parsed = _fm.parse_id(item)
        if parsed:
            slug = _fm.project_for(parsed[0])
            if slug:
                out.add(slug)
    return out


def primary_project(thread, attributed):
    """The ONE project a chat renders under.

    `chat_projects` returns everything it touches, and one thread here cites
    tasks across six projects -- so rendering it in each card reproduced
    exactly the duplication that moving chats out of the item-major loop was
    meant to end: 15 chats, 20 rows. A chat appears once, under the project it
    cites most, and its row names the others.

    Ties break alphabetically so the choice is stable across runs rather than
    depending on dict order -- otherwise `publish --check` drifts for no
    reason anyone can see.
    """
    said = attributed.get(thread.get("key"))
    if said and said != NOT_MINE:
        return said
    counts = {}
    for item in thread.get("items") or []:
        parsed = _fm.parse_id(item)
        if not parsed:
            continue
        slug = _fm.project_for(parsed[0])
        if slug:
            counts[slug] = counts.get(slug, 0) + 1
    if not counts:
        return None
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]


def is_dismissed(thread, attributed):
    return attributed.get(thread.get("key")) == NOT_MINE


_ARCHIVED = {}


def archived_titles(root):
    """id -> title, for tasks that have left the model.

    `Model.load` walks `state/projects/*/items/` and archived tasks are not
    there, so every chat citing the build history rendered a column of bare
    `POS-001 … +8 more` -- twelve ids and not one word about any of them, on
    the rows most likely to be worth reading. The titles are on disk the whole
    time, one directory across.

    Archiving deliberately keeps ids resolvable rather than deleting them
    (`R-057` is the same lesson about `next_id`), so reading them here is
    consistent with that, not a special case.
    """
    if root in _ARCHIVED:
        return _ARCHIVED[root]
    out = {}
    base = os.path.join(root, "state", "archive")
    for stem, _dirs, files in os.walk(base):
        for name in files:
            if not name.endswith(".md"):
                continue
            try:
                fm, _body = _fm.load(os.path.join(stem, name))
            except _fm.FrontmatterError:
                continue        # `state/archive/README.md` is prose, not an item
            if fm.get("id") and fm.get("title"):
                out[fm["id"]] = fm["title"]
    if os.path.isdir(base) and not out:
        raise RuntimeError(
            "%s exists and holds no readable id/title pair. An empty result "
            "here renders as bare ids and looks like a design choice rather "
            "than a broken read -- R-075." % base)
    _ARCHIVED[root] = out
    return out


def notes(root):
    """key -> the authored sentence saying what that chat was about.

    Deliberately NOT in the shard. `index.py`'s FORBIDDEN_KEY rejects any field
    matching /summary|content|message|text|body/ at any depth, because a shard
    is machine-derived and must never carry conversation content. That guard is
    right and stays -- so the sentence is authored here instead, the way
    `attribution.yaml` is authored, which also makes it editable before it
    reaches a public page.
    """
    out = {}
    path = os.path.join(root, "state", "threads", "notes.yaml")
    if not os.path.exists(path):
        return out
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or ":" not in line:
                continue
            key, _, value = line.partition(":")
            value = value.strip().strip('"').strip("'")
            if value:
                out[key.strip()] = value
    return out


def chat_summary(thread, note=None):
    """What this chat was about -- the authored sentence, or the shape of it.

    `note` is the real answer and comes from `notes()`. Without one, the best
    the index can honestly do is say how MUCH work happened, over what span,
    against what -- which is what rendered before, on every row, and read as
    filler because it described none of them. The fallback stays because nine
    of fifteen chats have no transcript left on this machine to author from,
    and a metadata line is a truthful thin answer where a guessed sentence
    would be a confident wrong one.
    """
    if note:
        return note
    bits = []
    started = (thread.get("started") or "")[:10]
    ended = (thread.get("last_active") or "")[:10]
    if started and ended:
        bits.append("one sitting on %s" % started if started == ended
                    else "%s to %s" % (started, ended))
    prompts = thread.get("prompts") or 0
    if prompts:
        bits.append("%d exchange%s" % (prompts, "" if prompts == 1 else "s"))
    files = thread.get("files") or 0
    if files > 1:
        bits.append("%d files touched" % files)
    if thread.get("branch"):
        bits.append("on `%s`" % thread["branch"])
    if not bits:
        return "The index recorded no detail beyond its name."
    bits.append("no description written yet")
    return bits[0][:1].upper() + bits[0][1:] + (
        " · " + " · ".join(bits[1:]) if len(bits) > 1 else "")
