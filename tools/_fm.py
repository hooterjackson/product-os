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
        "impact", "confidence", "effort_minutes", "cognitive_load",
        "lead_time_days", "cost_usd",
        "unblocks", "unblocks_inferred", "answers", "pin",
        "keywords", "evidence", "evidence_found", "repos", "parent_ruling",
        "created", "updated", "completed", "closed_origin",
    ],
    "question": [
        "id", "title", "project", "status", "gates",
        "impact", "confidence", "effort_minutes", "cognitive_load",
        "lead_time_days", "cost_usd", "pin",
        "keywords", "evidence", "answer", "parent_ruling",
        "created", "updated", "answered",
    ],
    "decision": [
        "id", "title", "project", "status", "ruling_id", "decided",
        "revisit_if", "supersedes", "superseded_by", "propagates_to",
        "keywords", "evidence", "created", "updated",
    ],
    "project": [
        "slug", "name", "prefix", "north_star", "phase", "repos",
        "decision_authority", "may_rule", "created", "updated",
    ],
    "capture": ["captured", "machine", "source", "cwd"],
}

# Per-field authority. The guarantee this table exists to support:
# no agent-authority field appears in the score formula, so an agent acting
# within its authority cannot change score ordering.
#
# Note the honest limit: `status` is agent-authority and a blocked item is not
# offered by rank.py, so an agent CAN change what the system offers -- just not
# how the offered set is ordered. Said plainly rather than papered over.
HUMAN = "human"
AGENT = "agent"

AUTHORITY = {
    # decided -- the score inputs. Agents propose; they never write.
    "impact": HUMAN, "confidence": HUMAN, "effort_minutes": HUMAN,
    "lead_time_days": HUMAN, "cost_usd": HUMAN, "unblocks": HUMAN,
    "gates": HUMAN, "pin": HUMAN, "project": HUMAN, "gate": HUMAN,
    "machine_affinity": HUMAN, "answers": HUMAN, "evidence": HUMAN,
    # automatable -- none of these enter the score.
    "status": AGENT, "keywords": AGENT, "lane": AGENT, "title": AGENT,
    "repos": AGENT, "updated": AGENT, "completed": AGENT,
    "evidence_found": AGENT, "cognitive_load": AGENT,
}

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


ID_RE = re.compile(r"^(EL|SITE|GB|APP|HAI|POS|Q|DEC)-(\d{3,})$")
# Anchored to the live prefix set on purpose. The spec's \b[A-Z]{2,4}-\d{3,}\b
# matches AES-256, SHA-256 and ISO-8601 -- 916 hits, 100% false positives on the
# real corpus -- and misses Q-007 entirely.
MENTION_RE = re.compile(r"\b(?:EL|SITE|GB|APP|HAI|POS|Q|DEC)-\d{3,}\b")

PREFIX_PROJECT = {
    "EL": "robotic-spotlight",
    "SITE": "engineering-site",
    "GB": "gimbal-bench",
    "APP": "home-app",
    "HAI": "home-ai-infra",
    "POS": "product-os",
}


def parse_id(value):
    match = ID_RE.match(value or "")
    if not match:
        return None
    return match.group(1), int(match.group(2))


def sort_key(item_id):
    parsed = parse_id(item_id)
    if not parsed:
        return ("", 0)
    return parsed
