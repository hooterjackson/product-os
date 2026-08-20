#!/usr/bin/env python3
"""The backlog, in the order Marcelo put it in.

    python3 tools/backlog.py                 the order, top first
    python3 tools/backlog.py --project X     one project's tasks, in his order
    python3 tools/backlog.py --unconfirmed   closed by a machine, not by him

    python3 tools/backlog.py --add GB-020
    python3 tools/backlog.py --move GB-020 1 --said "do the fault ring first"

## Two write operations, and only one of them is gated

**Appending asserts nothing about priority.** A task added at the bottom claims
no position, so `--add` needs no ceremony -- `new.py item` does it
automatically, and adopting a recommendation will too.

**Moving asserts everything.** The order IS his judgement (`DEC-202`), so
`--move` requires `--said "<his words>"`, borrowing `apply.py`'s design: the
origin lives in the flag name, so an agent that forgets it fails safe toward
refusing rather than toward writing. An agent has no business reordering this
file, and if one does it on his instruction, his sentence is on the record.

This replaces `rank.py`, which computed an order from `impact x confidence /
effort_bucket` lifted by graph reachability. It does not compute anything.
`state/backlog.md` is a file he wrote; this reads it back with the titles
attached. See `DEC-202` and `R-068`.
"""

import argparse
import os
import sys

import _fm
import _model


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", help="only this project's tasks")
    parser.add_argument("--machine", help="only what can happen on this machine")
    parser.add_argument("--unconfirmed", action="store_true",
                        help="items a machine closed that he never confirmed")
    parser.add_argument("--add", metavar="ID",
                        help="append at the BOTTOM; asserts no priority")
    parser.add_argument("--move", nargs=2, metavar=("ID", "POSITION"),
                        help="move a task to 1-based POSITION (needs --said)")
    parser.add_argument("--said", metavar="WORDS",
                        help="his words, verbatim. Required by --move")
    args = parser.parse_args(argv)

    root = _model.find_root()
    model = _model.Model.load(root)
    for err in model.errors:
        sys.stderr.write("warning: %s\n" % err)

    if args.unconfirmed:
        return unconfirmed(model)
    if args.add:
        return add(root, model, args.add.upper())
    if args.move:
        return move(root, model, args.move[0].upper(), args.move[1], args.said)

    ordered = model.backlog()
    if args.project:
        ordered = [n for n in ordered if n.project == args.project]
    if args.machine:
        ordered = [n for n in ordered
                   if (n.get("machine_affinity") or args.machine) == args.machine]

    if not ordered:
        print("The backlog is empty.")
        print()
        print("That is a real state, not an error: he authors every task and")
        print("the system never creates one. `tools/new.py item` adds one.")
        return 0

    width = max(len(n.id) for n in ordered)
    for index, node in enumerate(ordered, 1):
        flags = []
        if node.status != "next":
            flags.append(node.status)
        if node.get("machine_affinity"):
            flags.append("on %s" % node.get("machine_affinity"))
        if (node.get("gate") or "none") != "none":
            flags.append("gate %s" % node.get("gate"))
        print("%2d. %-*s  %s%s" % (index, width, node.id, node.title,
                                   "   [%s]" % " · ".join(flags) if flags else ""))

    # A task that is active and absent from the file appears NOWHERE, because
    # the file is the only order there is. Silence about that would make it
    # invisible rather than merely unranked.
    loose = model.unlisted()
    if loose:
        print()
        print("%d active task(s) are NOT in the backlog, so nothing shows them:"
              % len(loose))
        for node in loose:
            print("    %-9s %s" % (node.id, node.title))
        print("Add a line to state/backlog.md, or park them.")
    return 0


REGENERATE = ("\nThe published surface names the top of this file, so it is now "
              "stale.\n  python3 tools/publish.py")


# --- writing the file ------------------------------------------------------

def read_lines(root):
    """(header, entries, trailer).

    `entries` is a list of (comment_lines, id, raw_line). An interleaved
    comment sticks to the entry BELOW it, because a comment between entries is
    a section marker labelling what follows -- moving an id out from under
    `# --- this week ---` and leaving the marker stranded would silently
    relabel a different task.
    """
    path = os.path.join(root, _model.BACKLOG)
    header, entries, pending = [], [], []
    seen_entry = False
    with open(path, "r", encoding="utf-8") as fh:
        raw = fh.read().splitlines()
    for line in raw:
        stripped = line.split("#", 1)[0].strip()
        if not stripped:
            (pending if seen_entry else header).append(line)
            continue
        seen_entry = True
        entries.append((pending, stripped, line))
        pending = []
    return header, entries, pending


def write_lines(root, header, entries, trailer):
    path = os.path.join(root, _model.BACKLOG)
    out = list(header)
    for comments, _item_id, raw in entries:
        out += comments
        out.append(raw)
    out += trailer
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out).rstrip("\n") + "\n")


def add(root, model, item_id):
    node = model.nodes.get(item_id)
    if node is None:
        sys.stderr.write("no such task: %s\n" % item_id)
        return 2
    header, entries, trailer = read_lines(root)
    if any(e[1] == item_id for e in entries):
        sys.stderr.write("%s is already in the backlog\n" % item_id)
        return 2
    width = max([len(e[1]) for e in entries] + [len(item_id)])
    entries.append(([], item_id, "%-*s  # %s" % (width, item_id, node.title)))
    write_lines(root, header, entries, trailer)
    print("appended %s at position %d (the bottom -- that is not a priority "
          "claim)" % (item_id, len(entries)))
    print(REGENERATE)
    return 0


def move(root, model, item_id, position, said):
    """Reordering is his judgement, so it needs his words."""
    if not said:
        sys.stderr.write(
            "--move needs --said \"<your words>\".\n\n"
            "The order is yours (DEC-202); this file is the only place it\n"
            "exists. An agent reordering it on its own reading is the thing\n"
            "the scoring engine was deleted for. If you told it to, pass what\n"
            "you said.\n")
        return 2
    if item_id not in model.nodes:
        sys.stderr.write("no such task: %s\n" % item_id)
        return 2
    header, entries, trailer = read_lines(root)
    index = next((i for i, e in enumerate(entries) if e[1] == item_id), None)
    if index is None:
        sys.stderr.write("%s is not in the backlog; --add it first\n" % item_id)
        return 2
    try:
        target = int(position)
    except ValueError:
        sys.stderr.write("position must be a number, got %r\n" % position)
        return 2
    if not 1 <= target <= len(entries):
        sys.stderr.write("position must be between 1 and %d\n" % len(entries))
        return 2

    entry = entries.pop(index)
    entries.insert(target - 1, entry)
    write_lines(root, header, entries, trailer)
    print("%s: %d -> %d   (on your word: %s)"
          % (item_id, index + 1, target, said))
    if entry[0]:
        print("note: %d comment line(s) moved with it, on the reading that a "
              "comment above an entry labels it." % len(entry[0]))
    print(REGENERATE)
    return 0


def unconfirmed(model):
    """Closed on a machine's judgement, never confirmed by him.

    Inherited from `rank.py --unconfirmed`. It matters more now, not less:
    every surface that used to render this -- `build/now.md`, the per-item
    briefs -- was deleted with the old model, and a fix whose every rendering
    surface disappears is a fix that stopped happening (`R-065`).
    """
    rows = [n for n in model.nodes.values()
            if n.status == "done" and n.get("closed_origin") != "his-word"]
    rows.sort(key=lambda n: _fm.sort_key(n.id))
    if not rows:
        print("Nothing is closed on my judgement alone.")
        return 0
    print("%d item(s) a machine closed. You have confirmed none of these.\n"
          % len(rows))
    for node in rows:
        found = node.get("evidence_found") or []
        print("  %-9s %s" % (node.id, node.title))
        print("            closed %s on %s · evidence: %s"
              % (node.get("completed") or "?",
                 node.get("closed_origin") or "(unrecorded)",
                 ", ".join(str(e.get("sha") or e.get("path"))
                           for e in found[:3]) or "NONE"))
    print("\nConfirm one in a sentence:")
    print("  python3 tools/apply.py --decided %s=status:done \\" % rows[0].id)
    print("      --said \"yes, %s is finished\"" % rows[0].id)
    return 0


if __name__ == "__main__":
    sys.exit(main())
