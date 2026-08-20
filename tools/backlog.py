#!/usr/bin/env python3
"""The backlog, in the order Marcelo put it in.

    python3 tools/backlog.py                 the order, top first
    python3 tools/backlog.py --project X     one project's tasks, in his order
    python3 tools/backlog.py --unconfirmed   closed by a machine, not by him

This replaces `rank.py`, which computed an order from `impact x confidence /
effort_bucket` lifted by graph reachability. It does not compute anything.
`state/backlog.md` is a file he wrote; this reads it back with the titles
attached. See `DEC-202` and `R-068`.
"""

import argparse
import sys

import _fm
import _model


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", help="only this project's tasks")
    parser.add_argument("--machine", help="only what can happen on this machine")
    parser.add_argument("--unconfirmed", action="store_true",
                        help="items a machine closed that he never confirmed")
    args = parser.parse_args(argv)

    root = _model.find_root()
    model = _model.Model.load(root)
    for err in model.errors:
        sys.stderr.write("warning: %s\n" % err)

    if args.unconfirmed:
        return unconfirmed(model)

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
