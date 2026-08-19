#!/usr/bin/env python3
"""The CI gate. Exit 0 clean, 1 on any error, 2 on usage failure.

    python3 tools/validate.py
    python3 tools/validate.py --format github     annotate a PR diff
    python3 tools/validate.py --fix-format        rewrite non-canonical files
"""

import argparse
import glob
import graphlib
import json
import os
import re
import subprocess
import sys

import _fm
import _model

# --- the secret / disclosure screen -----------------------------------------
# This repo may become public and is seeded from a private engineering repo, so
# the screen covers more than API keys. The leak classes below are the ones an
# audit of that repo actually found; a generic secret regex catches none of them.

SECRET_PATTERNS = [
    ("api-key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}")),
    ("github-token", re.compile(r"\b(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})")),
    ("aws-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("google-key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("slack-token", re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{10,}")),
    ("private-key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("jwt", re.compile(r"\beyJ[\w-]{10,}\.[\w-]{10,}\.[\w-]{10,}")),
    ("assigned-secret", re.compile(
        r"(?i)\b(api[_-]?key|secret|token|password|passwd)\s*[:=]\s*['\"][^'\"]{16,}['\"]")),
    # disclosure classes, not credentials
    ("email-address", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    ("tailnet-fqdn", re.compile(r"\b[A-Za-z0-9-]+\.[A-Za-z0-9-]+\.ts\.net\b")),
    ("tailnet-ip", re.compile(r"\b100\.(?:6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.\d{1,3}\.\d{1,3}\b")),
    ("mac-address", re.compile(r"\b(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}\b")),
    ("chat-url", re.compile(
        r"https?://(?:claude\.ai/chat/|chatgpt\.com/c/|chat\.openai\.com/c/)"
        r"[0-9a-zA-Z-]{8,}")),
    ("home-path", re.compile(r"/Users/[a-z][a-z0-9_-]+/")),
    ("windows-home", re.compile(r"[Cc]:\\\\?Users\\\\?[A-Z][A-Za-z]+")),
]

FORBIDDEN_PATHS = re.compile(
    r"(^|/)(\.env(\..*)?|auth\.json|secrets\.(ya?ml|json)|id_[rd]sa.*|.*\.pem|.*\.p12)$")

ALLOWLIST_FILE = "state/secret-allowlist.txt"

# A four-digit proposal citation, anywhere in authored prose. Four digits
# exactly: the trailing \b keeps a longer number from half-matching.
PROPOSAL_REF = re.compile(r"\bPROP-(\d{4})\b")

# Thread shards are metadata only. Duplicated from index.py ON PURPOSE: a
# shared constant would let one edit relax both gates at once, and the whole
# point of this check is that it is independent of the tool that writes.
SHARD_THREAD_KEYS = {
    "id", "tool", "title", "started", "last_active", "cwd", "branch",
    "prompts", "items", "cited_unknown", "path", "files", "forks", "parent",
    "verdict", "verdict_reason", "command",
}
FORBIDDEN_SHARD_KEY = re.compile(
    r"(?i)message|content|text|body|prompt_text|summary|snippet|excerpt")

VALID_STATUS = {"next", "doing", "done", "blocked", "dropped", "parked"}
VALID_LANE = {"hardware", "firmware", "app", "infra", "content"}
VALID_GATE = {"none", "awaiting-parts", "bench", "printer", "gpu", "external"}
VALID_LOAD = {"low", "medium", "high"}


class Finding(object):
    def __init__(self, level, code, path, message, line=None):
        self.level = level
        self.code = code
        self.path = path
        self.message = message
        self.line = line

    def human(self):
        loc = self.path if self.line is None else "%s:%d" % (self.path, self.line)
        return "%s: %s %s  %s" % (loc, self.level, self.code, self.message)

    def github(self):
        kind = "error" if self.level == "error" else "warning"
        line = ",line=%d" % self.line if self.line else ""
        return "::%s file=%s%s::%s %s" % (kind, self.path, line, self.code,
                                          self.message)


class Validator(object):
    def __init__(self, root, fix_format=False):
        self.root = root
        self.fix_format = fix_format
        self.findings = []
        self.allowlist = self._load_allowlist()

    def _load_allowlist(self):
        path = os.path.join(self.root, ALLOWLIST_FILE)
        if not os.path.exists(path):
            return set()
        entries = set()
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.split("#", 1)[0].strip()
                if line:
                    entries.add(line)
        return entries

    def add(self, level, code, path, message, line=None):
        rel = os.path.relpath(path, self.root) if os.path.isabs(path) else path
        self.findings.append(Finding(level, code, rel, message, line))

    def error(self, *a, **kw):
        self.add("error", *a, **kw)

    def warn(self, *a, **kw):
        self.add("warning", *a, **kw)

    # -- checks -------------------------------------------------------------

    def entity_files(self):
        patterns = [
            ("item", ("state", "projects", "*", "items", "*.md")),
            ("question", ("state", "questions", "*.md")),
            ("decision", ("state", "decisions", "*.md")),
            ("decision", ("state", "projects", "*", "decisions", "*.md")),
            ("project", ("state", "projects", "*", "project.md")),
            ("capture", ("state", "inbox", "*.md")),
        ]
        for kind, parts in patterns:
            for path in sorted(glob.glob(os.path.join(self.root, *parts))):
                yield kind, path

    def check_format(self):
        for kind, path in self.entity_files():
            with open(path, "r", encoding="utf-8") as fh:
                original = fh.read()
            try:
                canonical = _fm.canonicalize(original, kind, path)
            except _fm.FrontmatterError as exc:
                self.error("E-FRONTMATTER", path, exc.message, exc.line)
                continue
            if canonical != original:
                if self.fix_format:
                    with open(path, "w", encoding="utf-8") as fh:
                        fh.write(canonical)
                else:
                    self.error(
                        "E-NONCANONICAL", path,
                        "not in canonical form; run "
                        "`python3 tools/validate.py --fix-format`")

    def check_model(self, model):
        for err in model.errors:
            if "cycle" in err:
                self.error("E-GRAPH-CYCLE", "state/", err)
            else:
                self.error("E-MODEL", "state/", err)

        nodes = model.nodes
        seen = {}
        for node in list(nodes.values()) + list(model.decisions.values()):
            path = node.path
            parsed = _fm.parse_id(node.id)
            if not parsed:
                self.error("E-ID-FORMAT", path,
                           "id %r does not match <PREFIX>-<3+ digits>" % node.id)
                continue
            prefix = parsed[0]
            if node.id in seen and seen[node.id] != path:
                self.error("E-ID-DUPLICATE", path,
                           "id %s also defined in %s" % (node.id, seen[node.id]))
            seen[node.id] = path

            if node.kind == "item":
                expected = _fm.PREFIX_PROJECT.get(prefix)
                if expected and node.project and node.project != expected:
                    self.error("E-ID-PROJECT-MISMATCH", path,
                               "prefix %s implies project %s, frontmatter says %s"
                               % (prefix, expected, node.project))

            if node.kind in ("item", "question"):
                self.check_scored(node)

        for node in nodes.values():
            for field in ("unblocks", "unblocks_inferred", "answers", "gates"):
                for ref in node.get(field) or []:
                    if ref not in nodes:
                        self.error("E-REF-UNRESOLVED", node.path,
                                   "%s references %s, which does not exist"
                                   % (field, ref))
                    elif ref == node.id:
                        self.error("E-REF-SELF", node.path,
                                   "%s references itself" % field)

        pins = {}
        for node in nodes.values():
            pin = node.get("pin")
            if pin is None:
                continue
            if pin in pins:
                self.error("E-PIN-DUPLICATE", node.path,
                           "pin %d also used by %s" % (pin, pins[pin]))
            pins[pin] = node.id

    def check_scored(self, node):
        path = node.path
        for field in ("impact", "confidence"):
            value = node.get(field)
            if not isinstance(value, int) or not 1 <= value <= 5:
                self.error("E-SCHEMA-RANGE", path,
                           "%s must be an integer 1-5, got %r" % (field, value))
        minutes = node.get("effort_minutes")
        if not isinstance(minutes, int) or minutes < 1:
            self.error("E-SCHEMA-RANGE", path,
                       "effort_minutes must be a positive integer, got %r" % minutes)
        lead = node.get("lead_time_days")
        if lead is not None and (not isinstance(lead, int) or lead < 0):
            self.error("E-SCHEMA-RANGE", path,
                       "lead_time_days must be >= 0, got %r" % lead)
        if node.status not in VALID_STATUS:
            self.error("E-SCHEMA-ENUM", path,
                       "status %r not in %s" % (node.status, sorted(VALID_STATUS)))
        lane = node.get("lane")
        if node.kind == "item" and lane not in VALID_LANE:
            self.error("E-SCHEMA-ENUM", path,
                       "lane %r not in %s" % (lane, sorted(VALID_LANE)))
        gate = node.get("gate")
        if gate is not None and gate not in VALID_GATE:
            self.error("E-SCHEMA-ENUM", path,
                       "gate %r not in %s" % (gate, sorted(VALID_GATE)))
        load = node.get("cognitive_load")
        if load is not None and load not in VALID_LOAD:
            self.error("E-SCHEMA-ENUM", path,
                       "cognitive_load %r not in %s" % (load, sorted(VALID_LOAD)))

        # The rule the whole system rests on: nothing is done without evidence.
        if node.status == "done":
            if not node.get("evidence_found"):
                self.error("E-DONE-NO-EVIDENCE", path,
                           "status is done but evidence_found is empty -- "
                           "a completion nobody can click is not a completion")
            if not node.get("completed"):
                self.error("E-DONE-NO-DATE", path,
                           "status is done but completed date is missing")

        # A derived value must never be written back into authored state,
        # or it quietly becomes authoritative.
        for derived in ("score", "leverage", "rank", "blocked_by", "effort",
                        "threads"):
            if derived in node.fm:
                self.error("E-DERIVED-PRESENT", path,
                           "%r is computed and must not be stored" % derived)

    def check_register_ids(self):
        """A register ID must appear once.

        Two agents appending to `wiki/ruled-out.md` against the same HEAD each
        take "the next free number" and compute the same answer, and appending
        is the one operation that looks conflict-free to git. That produced two
        `R-063`s and two `R-064`s in one afternoon with this tool exiting 0 --
        the register is the most expensive knowledge here, and a duplicate ID
        makes a citation ambiguous about which entry it means. See `R-066`.
        """
        path = os.path.join(self.root, "wiki", "ruled-out.md")
        if not os.path.exists(path):
            return
        seen = {}
        with open(path, "r", encoding="utf-8") as fh:
            for number, line in enumerate(fh, 1):
                found = re.match(r"^## (R-\d+)\b", line)
                if not found:
                    continue
                entry = found.group(1)
                if entry in seen:
                    self.error("E-REGISTER-DUPLICATE", "wiki/ruled-out.md",
                               "%s is already defined at line %d"
                               % (entry, seen[entry]), line=number)
                else:
                    seen[entry] = number

    def check_proposal_refs(self):
        """A cited proposal must exist.

        `check_model` resolves `unblocks`, `answers` and `gates` against the
        node table, and repo names against `repos.json`. Proposal citations
        were the one reference class nothing resolved: `state/repos.json`
        shipped a `See PROP-NNNN` for a file that did not exist and this tool
        exited 0 on it. A citation to a proposal that is not there is the same
        defect as an `unblocks` pointing at no item -- the register asserting a
        provenance it cannot produce.

        `state/inbox/` is exempt deliberately. A capture is raw words; turning
        a half-remembered number into a real citation is what triage is for,
        and a gate on the inbox would make `/capture` ask a question.

        `public/` and `build/` are exempt because they are derived -- a dangling
        citation there is a symptom of one in `state/`, and reporting it twice
        points at the generated copy instead of the file to edit.
        """
        prop_dir = os.path.join(self.root, "state", "proposals")
        known = set()
        if os.path.isdir(prop_dir):
            for name in os.listdir(prop_dir):
                found = PROPOSAL_REF.search(name)
                if found:
                    known.add(found.group(1))
        for path in self.tracked_files():
            rel = os.path.relpath(path, self.root)
            parts = rel.split(os.sep)
            if parts[0] in ("build", "public"):
                continue
            if parts[:2] == ["state", "inbox"]:
                continue
            if not os.path.exists(path) or not self.is_text(path):
                continue
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as fh:
                    lines = fh.readlines()
            except OSError:
                continue
            for number, line in enumerate(lines, 1):
                for ref in PROPOSAL_REF.finditer(line):
                    if ref.group(1) not in known:
                        self.error("E-REF-PROPOSAL", rel,
                                   "cites %s, which does not exist in "
                                   "state/proposals/" % ref.group(0),
                                   line=number)

    def check_secrets(self):
        for path in self.tracked_files():
            rel = os.path.relpath(path, self.root)
            if FORBIDDEN_PATHS.search(rel):
                self.error("E-FORBIDDEN-PATH", path,
                           "this path must never be committed")
                continue
            if not self.is_text(path):
                continue
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                for lineno, line in enumerate(fh, 1):
                    for code, pattern in SECRET_PATTERNS:
                        match = pattern.search(line)
                        if not match:
                            continue
                        token = match.group(0)
                        if token in self.allowlist:
                            continue
                        self.error("E-DISCLOSURE-" + code.upper(), path,
                                   "possible %s; if intended, add the exact "
                                   "string to %s" % (code, ALLOWLIST_FILE),
                                   lineno)

    def is_text(self, path):
        if os.path.splitext(path)[1].lower() in (
                ".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".stl", ".step"):
            return False
        try:
            with open(path, "rb") as fh:
                return b"\0" not in fh.read(4096)
        except OSError:
            return False

    def tracked_files(self):
        out = _run(["git", "-C", self.root, "ls-files", "-z"])
        if out is None:
            for base, dirs, files in os.walk(self.root):
                dirs[:] = [d for d in dirs
                           if d not in (".git", "build", ".cache", "__pycache__")]
                for name in files:
                    yield os.path.join(base, name)
            return
        for rel in out.split("\0"):
            if rel:
                yield os.path.join(self.root, rel)

    def check_contract_docs(self):
        claude = os.path.join(self.root, "CLAUDE.md")
        agents = os.path.join(self.root, "AGENTS.md")
        if not (os.path.exists(claude) and os.path.exists(agents)):
            self.error("E-CONTRACT-MISSING", "CLAUDE.md",
                       "CLAUDE.md and AGENTS.md must both exist")
            return
        with open(claude, "rb") as fh:
            a = fh.read()
        with open(agents, "rb") as fh:
            b = fh.read()
        if a != b:
            self.error("E-CONTRACT-DIVERGED", "AGENTS.md",
                       "AGENTS.md must be byte-identical to CLAUDE.md")

    def check_authority(self, base_ref):
        """A human-authority field must not change without an accepted proposal.

        `fsguard`-style path guards cannot express this: human and agent fields
        live in the same frontmatter block, so a file-level rule cannot see
        which key moved. This is the only layer that can.
        """
        if base_ref is None:
            return
        changed = _run(["git", "-C", self.root, "diff", "--name-only",
                        base_ref, "--", "state/"])
        if changed is None:
            self.warn("W-AUTHORITY-SKIPPED", "state/",
                      "could not diff against %s; authority audit skipped" % base_ref)
            return
        message = _run(["git", "-C", self.root, "log", "-1", "--format=%B"]) or ""
        accepts = re.search(r"^Accepts:\s*(PROP-\d+)", message, re.M)

        for rel in [c for c in changed.splitlines() if c.endswith(".md")]:
            old = _run(["git", "-C", self.root, "show", "%s:%s" % (base_ref, rel)])
            if old is None:
                continue  # newly added; nothing to diff against
            new_path = os.path.join(self.root, rel)
            if not os.path.exists(new_path):
                continue
            try:
                old_fm, _ = _fm.split(old, rel)
                with open(new_path, "r", encoding="utf-8") as fh:
                    new_fm, _ = _fm.split(fh.read(), rel)
            except _fm.FrontmatterError:
                continue
            for key in set(old_fm) | set(new_fm):
                if old_fm.get(key) == new_fm.get(key):
                    continue
                authority = _fm.AUTHORITY.get(key)
                if key == "status":
                    moved = {old_fm.get(key), new_fm.get(key)}
                    authority = _fm.HUMAN if moved & _fm.HUMAN_STATUSES else _fm.AGENT
                if authority == _fm.HUMAN and not accepts:
                    self.error(
                        "E-AUTHORITY-UNBLESSED", rel,
                        "%r is human-authority and changed without an accepted "
                        "proposal (commit needs an 'Accepts: PROP-NNNN' trailer)"
                        % key)

    # -- driver -------------------------------------------------------------

    def check_thread_shards(self):
        """Thread shards carry METADATA ONLY, and this re-checks it here.

        `index.py` filters against its own allowlist on the way out. This check
        exists because that is the wrong place to trust: the shard is derived
        from 405 GiB of unredacted working conversation, this repo may go
        public, and a one-line change to the indexer could start emitting
        message bodies without anything noticing. Two independent gates, one of
        which lives in the CI path.
        """
        pattern = os.path.join(self.root, "state", "threads", "by-machine", "*.json")
        for path in sorted(glob.glob(pattern)):
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    shard = json.load(fh)
            except (OSError, ValueError) as exc:
                self.error("E-SHARD-UNPARSEABLE", path, str(exc))
                continue
            name = os.path.splitext(os.path.basename(path))[0]
            if shard.get("machine") != name:
                self.error("E-SHARD-MACHINE", path,
                           "shard says machine %r but the filename says %r; "
                           "one file per machine, one writer per file"
                           % (shard.get("machine"), name))
            for index, thread in enumerate(shard.get("threads") or []):
                if not isinstance(thread, dict):
                    self.error("E-SHARD-SHAPE", path,
                               "thread %d is not an object" % index)
                    continue
                for key in thread:
                    if FORBIDDEN_SHARD_KEY.search(key):
                        self.error("E-SHARD-LEAK", path,
                                   "thread %d carries %r -- shards are metadata "
                                   "only and this repo may go public"
                                   % (index, key))
                    elif key not in SHARD_THREAD_KEYS:
                        self.error("E-SHARD-KEY", path,
                                   "thread %d carries %r, which is not on the "
                                   "allowlist" % (index, key))

    def check_commit_identities(self):
        """The screen scans FILE CONTENTS. Commit metadata is public too.

        On a public repo every author and committer email is served by the API,
        and `git commit --amend` does not remove the old object -- it orphans
        it, and GitHub keeps serving orphans by SHA. Measured 2026-08-19:
        `e30c955` was amended out of the branch and remained fetchable, still
        carrying a work address in both fields.

        So this checks identities, not files, and it checks ALL refs plus the
        reflog -- because the reachable branch is exactly where an amended
        address is NOT.
        """
        def identities(args):
            found = {}
            out = _run(["git", "-C", self.root] + args)
            for line in (out or "").splitlines():
                parts = line.split("\x1f")
                if len(parts) != 3:
                    continue
                for address in parts[1:]:
                    if (address and address not in found
                            and re.match(r"^[^@]+@[^@]+\.[^@]+$", address)):
                        found[address] = parts[0][:7]
            return found

        reachable = identities(["log", "--all", "--format=%H%x1f%ae%x1f%ce"])
        orphaned = identities(["reflog", "--format=%H%x1f%ae%x1f%ce"])

        # Reachable history is fixable here, so a stray address is an ERROR.
        for address, sha in sorted(reachable.items()):
            if address in self.allowlist:
                continue
            self.error(
                "E-DISCLOSURE-COMMIT-IDENTITY", "git history",
                "commit %s carries %r as an author/committer address, and it "
                "is REACHABLE. On a public repo the API serves it. If "
                "intended, add the exact string to %s"
                % (sha, address, ALLOWLIST_FILE))

        # Orphans are NOT fixable with git: --amend leaves the old object, and
        # GitHub keeps serving it by SHA. Warning, because a permanently red
        # gate on something the tooling cannot fix trains people to ignore it --
        # but never silence, because the address is genuinely public.
        for address, sha in sorted(orphaned.items()):
            if address in self.allowlist or address in reachable:
                continue
            self.warn(
                "W-DISCLOSURE-ORPHANED-IDENTITY", "git history",
                "orphaned commit %s carries %r. It is unreachable from any "
                "branch and STILL served by GitHub by SHA -- `--amend` did not "
                "remove it. Only GitHub support can purge it. See "
                "wiki/ruled-out.md R-060." % (sha, address))

    def check_public_surface(self):
        """Every path llms.txt advertises must exist, and public/ must match a
        fresh generation.

        The cheapest catch available for the most embarrassing failure this
        system can have: a bootstrap file that tells a model with no context to
        fetch something that 404s. The model cannot tell a missing endpoint
        from a broken one; it just fails, on his machine, in front of him.
        """
        public = os.path.join(self.root, "public")
        if not os.path.isdir(public):
            self.warn("W-NO-PUBLIC", "public/",
                      "the agent-facing surface has not been generated")
            return
        sys.path.insert(0, os.path.join(self.root, "tools"))
        try:
            import publish as publish_mod
            import _model as model_mod
        except ImportError:
            return
        model = model_mod.Model.load(self.root)
        for rel in publish_mod.advertised(model):
            if "<" in rel:            # a template, not a literal path
                continue
            if not os.path.exists(os.path.join(public, rel)):
                self.error("E-DEAD-ENDPOINT", "public/llms.txt",
                           "advertises %s, which does not exist" % rel)
        proc = subprocess.run(
            [sys.executable, os.path.join(self.root, "tools", "publish.py"),
             "--check"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if proc.returncode != 0:
            for line in proc.stdout.decode("utf-8", "replace").splitlines()[:6]:
                self.error("E-PUBLIC-STALE", "public/", line.strip())

    def check_regressions(self):
        """Run tests/test_regressions.py as part of the gate.

        Each test there pins a defect that shipped in this repo and was found
        by running the code and reading the output -- a method that works once
        per defect, by luck, possibly after somebody has acted on the wrong
        answer. Wiring them into the gate is what converts that into a check.
        """
        path = os.path.join(self.root, "tests", "test_regressions.py")
        if not os.path.exists(path):
            self.warn("W-NO-REGRESSION-TESTS", "tests/",
                      "tests/test_regressions.py is missing")
            return
        proc = subprocess.run([sys.executable, path],
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if proc.returncode == 0:
            return
        output = proc.stdout.decode("utf-8", "replace")
        failures = [ln for ln in output.splitlines()
                    if ln.startswith(("FAIL:", "ERROR:"))]
        for line in failures or ["see `python3 tests/test_regressions.py`"]:
            self.error("E-REGRESSION", "tests/test_regressions.py", line.strip())

    def run(self, base_ref=None, with_tests=True):
        self.check_format()
        self.check_contract_docs()
        model = _model.Model.load(self.root)
        self.check_model(model)
        self.check_register_ids()
        self.check_proposal_refs()
        self.check_secrets()
        self.check_thread_shards()
        self.check_public_surface()
        self.check_commit_identities()
        self.check_authority(base_ref)
        if with_tests:
            self.check_regressions()
        return model


def _run(args):
    try:
        proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError:
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout.decode("utf-8", "replace")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=["human", "github", "json"],
                        default="human")
    parser.add_argument("--fix-format", action="store_true")
    parser.add_argument("--strict", action="store_true",
                        help="treat warnings as errors")
    parser.add_argument("--base", help="git ref for the authority audit")
    parser.add_argument("--no-tests", action="store_true",
                        help="skip tests/test_regressions.py")
    args = parser.parse_args(argv)

    root = _model.find_root()
    validator = Validator(root, fix_format=args.fix_format)
    validator.run(base_ref=args.base, with_tests=not args.no_tests)

    errors = [f for f in validator.findings if f.level == "error"]
    warnings = [f for f in validator.findings if f.level == "warning"]

    if args.format == "json":
        print(json.dumps({
            "errors": len(errors), "warnings": len(warnings),
            "findings": [{"level": f.level, "code": f.code, "path": f.path,
                          "line": f.line, "message": f.message}
                         for f in validator.findings],
        }, indent=2))
    else:
        for finding in validator.findings:
            print(finding.github() if args.format == "github" else finding.human())
        if not validator.findings:
            print("clean")
        print("%d error(s), %d warning(s)" % (len(errors), len(warnings)))

    if errors or (args.strict and warnings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
