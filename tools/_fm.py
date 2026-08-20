#!/usr/bin/env python3
"""JSON frontmatter, in canonical form.

Entity files are markdown with a JSON object between `---` fences:

    ---
    {
      "id": "EL-004",
      ...
    }
    ---

    Why this matters, in prose.

Why JSON and not YAML: this machine has no PyYAML and no package manager path we
want to depend on, and a hand-rolled YAML subset was ~1000 lines of load-bearing
parser. JSON is stdlib. It still parses in Obsidian and Quartz, because a JSON
object is a valid YAML 1.2 flow mapping -- that is an accident of the subset
rather than a defined convention, so it is worth saying out loud and worth the
canonical-form check in validate.py.

Two properties this module exists to guarantee:

1. Key order is EXPLICIT and spec-ordered, never `sort_keys=True`. Alphabetical
   would put `title` 22nd of 24 and scatter impact/confidence/effort across the
   file. Fixed order is what makes a one-field change diff as one line.
2. Canonical form survives only while dump() is the only writer. A human (or
   Obsidian's Properties editor) can produce valid-but-non-canonical files, so
   validate.py reformats-and-diffs and offers a one-line repair.
"""

import json
import os
import re
import tempfile

FENCE = "---"

# Explicit key order per entity kind. Fields not listed here are appended in
# sorted order and flagged by validate.py as unknown.
FIELD_ORDER = {
    "item": [
        "id", "title", "project", "status", "lane", "gate", "machine_affinity",
        "keywords", "evidence", "evidence_found", "repos", "parent_ruling",
        "created", "updated", "completed", "closed_origin",
    ],
    "decision": [
        "id", "title", "project", "status", "ruling_id", "decided",
        "revisit_if", "supersedes", "superseded_by", "propagates_to",
        "keywords", "evidence", "created", "updated",
    ],
    "project": [
        "slug", "name", "prefix", "description", "phase", "repos",
        "decision_authority", "may_rule", "created", "updated",
    ],
    "capture": ["captured", "machine", "source", "cwd"],
}

# Per-field authority.
#
# This table used to support a guarantee about SCORE ORDERING: no agent-authority
# field appeared in the score formula, so an agent could not change the order.
# There is no formula now (DEC-202) and the order is `state/backlog.md`, which no
# agent writes -- so the guarantee is simpler and stronger than the arithmetic
# one it replaces: **the order is a file only he edits.**
#
# The honest limit that remains: `status` is agent-authority, so an agent marking
# something `done` removes it from the backlog. That is bounded by the evidence
# rule, not by this table.
HUMAN = "human"
AGENT = "agent"

AUTHORITY = {
    # decided -- his. Agents draft into state/drafts/; they never write here.
    "project": HUMAN, "gate": HUMAN, "machine_affinity": HUMAN,
    "evidence": HUMAN,
    # automatable.
    "status": AGENT, "keywords": AGENT, "lane": AGENT, "title": AGENT,
    "repos": AGENT, "updated": AGENT, "completed": AGENT,
    "evidence_found": AGENT,
}

# FIELD_ORDER and AUTHORITY must stay in lockstep for `item`: a field that
# exists in one and not the other is how an authority rule goes silently
# unenforced. `test_field_order_and_authority_agree` pins it.

# `dropped` and `parked` are human-authority even though `status` is not: they
# are scope decisions with taste in them, and leverage excludes them, so an
# agent setting one would move every upstream score.
HUMAN_STATUSES = {"dropped", "parked"}


class FrontmatterError(Exception):
    def __init__(self, path, message, line=None):
        self.path = path
        self.message = message
        self.line = line
        loc = "%s:%s" % (path, line) if line else str(path)
        super(FrontmatterError, self).__init__("%s: %s" % (loc, message))


def split(text, path="<string>"):
    """Split raw file text into (frontmatter_dict, body_str)."""
    if not text.startswith(FENCE + "\n"):
        raise FrontmatterError(path, "file must begin with a '---' fence")
    end = text.find("\n" + FENCE, len(FENCE) + 1)
    if end == -1:
        raise FrontmatterError(path, "unterminated frontmatter: no closing '---'")
    raw = text[len(FENCE) + 1:end + 1]
    rest = text[end + 1 + len(FENCE):]
    if rest.startswith("\n"):
        rest = rest[1:]
    try:
        fm = json.loads(raw)
    except ValueError as exc:
        line = 1 + raw[:getattr(exc, "pos", 0)].count("\n")
        raise FrontmatterError(path, "invalid JSON frontmatter: %s" % exc, line)
    if not isinstance(fm, dict):
        raise FrontmatterError(path, "frontmatter must be a JSON object")
    return fm, rest


def load(path):
    with open(path, "r", encoding="utf-8") as fh:
        return split(fh.read(), path)


def order_keys(fm, kind):
    order = FIELD_ORDER.get(kind, [])
    known = [k for k in order if k in fm]
    extra = sorted(k for k in fm if k not in order)
    return known + extra


def dump(fm, kind):
    """Render frontmatter to canonical text, including both fences."""
    ordered = {}
    for key in order_keys(fm, kind):
        ordered[key] = fm[key]
    body = json.dumps(ordered, indent=2, ensure_ascii=False)
    return "%s\n%s\n%s\n" % (FENCE, body, FENCE)


def render(fm, body, kind):
    # strip("\n"), not rstrip: canonical form puts exactly one blank line
    # between the closing fence and the body, and split() hands that blank line
    # back as part of the body. With rstrip alone, canonicalize() is not a fixed
    # point -- every round trip grows one more blank line, so the first file
    # new.py wrote would have failed validate.py's canonical check on sight.
    body = body.strip("\n")
    if body:
        return dump(fm, kind) + "\n" + body + "\n"
    return dump(fm, kind)


def canonicalize(text, kind, path="<string>"):
    fm, body = split(text, path)
    return render(fm, body, kind)


def write(path, fm, body, kind):
    """Atomically write an entity file in canonical form."""
    text = render(fm, body, kind)
    directory = os.path.dirname(os.path.abspath(path)) or "."
    fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
    return text


# --- the prefix set, DERIVED ------------------------------------------------
#
# This was three hardcoded tables: `ID_RE`, `MENTION_RE` and `PREFIX_PROJECT`.
# Projects are first-class now and can be created inline, so a new project
# needed a new prefix edited into all three by hand -- and `MENTION_RE` is the
# audit's id-mention fallback, so forgetting one meant the audit silently
# stopped recognising a whole project's commits. Silently is the operative
# word: nothing would have failed.
#
# `Model.load()` calls `set_prefixes()` with what it finds. Two guarantees are
# worth stating because they pull in opposite directions:
#
#   SHAPE matching stays generic. `parse_id` and `sort_key` only ever see a
#   string already sitting in an `id` field, and they only need (prefix,
#   number) to sort. A generic shape there cannot cause a false attribution.
#
#   TEXT matching is never generic. `mention_re()` scans raw conversation and
#   commit subjects, where the spec's `\b[A-Z]{2,4}-\d{3,}\b` matched
#   AES-256, SHA-256 and ISO-8601 916 times -- 100% false positives -- while
#   missing `Q-007`, whose prefix is one letter. So it is built from the live
#   set and RAISES if that set was never loaded. A regex that matches nothing
#   reads exactly like a corpus with nothing in it (`R-075`).

# `{1,6}`, not `{2,6}`. A single-letter prefix is real: `Q-001`..`Q-005` are
# live task ids. Writing `{2,6}` here reproduced, exactly, the bug the old
# comment warned about -- "misses Q-007 entirely because its prefix is one
# letter" -- and it was silent: the derived set simply came back without `Q`,
# so `mention_re()` would have stopped matching five tasks and the thread
# indexer would have quietly stopped binding them. Caught by printing the set
# and reading it, which is the only reason it is not in this commit.
ID_SHAPE = re.compile(r"^([A-Z]{1,6})-(\d{3,})$")

# `DEC` is an entity kind, not a project -- rulings are portfolio-wide. It is
# the only structural prefix, so it is the only one named here.
RESERVED_PREFIXES = {"DEC": None}

_PREFIXES = {}
_MENTION_RE = None


def set_prefixes(mapping):
    """prefix -> project slug (or None for a non-project prefix)."""
    global _PREFIXES, _MENTION_RE
    _PREFIXES = dict(mapping)
    _MENTION_RE = None


def prefixes():
    return dict(_PREFIXES)


def project_for(prefix):
    return _PREFIXES.get(prefix)


def prefix_for(project_slug):
    for prefix, slug in sorted(_PREFIXES.items()):
        if slug == project_slug:
            return prefix
    return None


def mention_re():
    """The id pattern for scanning free text. Never permissive."""
    global _MENTION_RE
    if _MENTION_RE is None:
        if not _PREFIXES:
            raise RuntimeError(
                "prefix set not loaded -- call _model.Model.load() first. "
                "Scanning text with an empty prefix set would match nothing "
                "and read as a corpus with nothing in it (R-075).")
        alternation = "|".join(sorted(_PREFIXES, key=lambda p: (-len(p), p)))
        _MENTION_RE = re.compile(r"\b(?:%s)-\d{3,}\b" % alternation)
    return _MENTION_RE


def parse_id(value):
    match = ID_SHAPE.match(value or "")
    if not match:
        return None
    return match.group(1), int(match.group(2))


def sort_key(item_id):
    parsed = parse_id(item_id)
    if not parsed:
        return ("", 0)
    return parsed
