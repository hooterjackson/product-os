#!/usr/bin/env python3
"""Inject the ruled-out entries that match the work about to happen.

`wiki/ruled-out.md` is only worth writing if it is read *at the moment of
suggesting*. A register consulted afterwards documents the afternoon you already
burned. So this hook runs at session start, works out which item this session is
most likely to touch, and pushes the matching dead ends into context before
anybody proposes one.

Which item:

  1. $PRODUCT_OS_ITEM, if set -- an explicit "I am working on GB-001".
  2. Otherwise the top of `rank.py`, which is the system's own answer to
     "what should I work on", and therefore the best available guess.

Failure is silent by design. A hook that blocks or errors at session start is
worse than a hook that adds nothing, and this one is an assistant, not a gate.
"""

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MAX_ENTRIES = 6


def find_root():
    """The plugin may be installed anywhere; the repo is what we need."""
    for candidate in (os.environ.get("PRODUCT_OS_ROOT"), ROOT, os.getcwd()):
        if not candidate:
            continue
        path = os.path.abspath(os.path.expanduser(candidate))
        while True:
            if os.path.isdir(os.path.join(path, "state")) and \
               os.path.exists(os.path.join(path, "CLAUDE.md")):
                return path
            parent = os.path.dirname(path)
            if parent == path:
                break
            path = parent
    return None


def parse_entries(text):
    """Split the register into (title, keywords, block) triples.

    An entry ends at the next `## `, but also at the `---` rule and the `# `
    heading that start a new section -- otherwise the last entry of every
    section drags the next section's banner into the injected context, which
    reads as though the banner belongs to the entry.
    """
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
        entries.append((title, words, "## " + body.rstrip()))
    return entries


def pick_item(model, wanted):
    """The named task, or the top of the authored backlog.

    This used to ask the model for a computed order. Deleting `rank.py`
    without rewiring it
    would have broken this hook SILENTLY -- a hook that raises simply does not
    inject, so the ruled-out register would have stopped reaching sessions with
    no error anywhere. `hooks.json` names that failure shape already: "it looks
    installed."
    """
    if wanted:
        return model.nodes.get(wanted.strip().upper())
    ordered = model.backlog()
    return ordered[0] if ordered else None


def main():
    root = find_root()
    if root is None:
        return 0
    register = os.path.join(root, "wiki", "ruled-out.md")
    if not os.path.exists(register):
        return 0

    sys.path.insert(0, os.path.join(root, "tools"))
    try:
        import _model
        model = _model.Model.load(root)
    except Exception:
        return 0

    node = pick_item(model, os.environ.get("PRODUCT_OS_ITEM"))
    if node is None:
        return 0

    keywords = {str(k).strip().lower() for k in (node.get("keywords") or [])}
    if not keywords:
        return 0

    with open(register, "r", encoding="utf-8") as fh:
        entries = parse_entries(fh.read())

    scored = []
    for title, words, block in entries:
        overlap = keywords & words
        if overlap:
            scored.append((len(overlap), title, block, sorted(overlap)))
    scored.sort(key=lambda row: (-row[0], row[1]))

    lines = [
        "# product-os · before you suggest anything",
        "",
        "**%s — %s**" % (node.id, node.title),
        "%s · %s · gate %s%s" % (
            node.project, node.status, node.get("gate") or "none",
            " · machine %s" % node.get("machine_affinity")
            if node.get("machine_affinity") else ""),
        "",
    ]
    if node.get("machine_affinity"):
        lines += ["Machine: **%s**. If that is not this machine, the honest "
                  "answer is \"resume on %s\", not a plan you cannot execute."
                  % (node.get("machine_affinity"), node.get("machine_affinity")),
                  ""]

    if not scored:
        lines += ["No `wiki/ruled-out.md` entry matches this item's keywords "
                  "(%s). That is not the same as nothing having been ruled out — "
                  "skim the register before proposing an approach."
                  % ", ".join(sorted(keywords))]
    else:
        lines += [
            "## Already ruled out, matching this item's keywords",
            "",
            "%d of %d entries in `wiki/ruled-out.md` match. **Read these before "
            "proposing an approach.** If you find something that contradicts an "
            "entry, do not silently overwrite it — flag it."
            % (min(len(scored), MAX_ENTRIES), len(entries)),
            "",
        ]
        for _, _, block, overlap in scored[:MAX_ENTRIES]:
            lines.append("_matched on: %s_" % ", ".join(overlap))
            lines.append("")
            lines.append(block)
            lines.append("")
        if len(scored) > MAX_ENTRIES:
            lines.append("_%d further matching entries in `wiki/ruled-out.md`._"
                         % (len(scored) - MAX_ENTRIES))

    context = "\n".join(lines)
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        }
    }))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        # Never break a session over a context nicety.
        sys.exit(0)
