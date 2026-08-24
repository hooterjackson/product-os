#!/usr/bin/env python3
"""Move finished or superseded work out of the model, without deleting it.

    python3 tools/archive.py --project product-os --said "..."
    python3 tools/archive.py POS-001 POS-006 --said "..."
    python3 tools/archive.py --project product-os --dry-run

## Why archive rather than close

Closing a task leaves it in the model. A `done` item still loads, still counts,
and if a machine closed it, it still sits in the closures section waiting to be
confirmed -- so "close them" would have moved eight rows from one part of the
page to another. Archiving takes them out of the model entirely and leaves the
file, its evidence and its handoffs intact.

## Where it goes, and why exactly there

`state/archive/`. UNDER `state/`, because `new.py:next_id()` walks that whole
tree for max+1 -- move the archive outside it and an id gets reused, which is
`R-057`: a transcript citing `Q-004` bound to the wrong work because the number
had been handed out twice. Nothing loads `state/archive/`; `Model.load` globs
`state/projects/*/items/*.md` and the archive is not on that path.

## An unconfirmed closure archives as unconfirmed

If a machine closed something and he never agreed, that fact travels with it.
Filing it away is not the same as agreeing, and relabelling it on the way out
would be the tool laundering its own guess.
"""

import argparse
import datetime
import os
import shutil
import sys

import _fm
import _model
import new as new_mod


def plan(model, ids, project):
    if project:
        return sorted((n for n in model.items.values()
                       if n.project == project), key=lambda n: _fm.sort_key(n.id))
    wanted = {i.upper() for i in ids}
    return sorted((n for n in model.items.values() if n.id in wanted),
                  key=lambda n: _fm.sort_key(n.id))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ids", nargs="*")
    parser.add_argument("--project")
    parser.add_argument("--said", help="his words. Required: archiving is a "
                                       "scope decision, not a status truth")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    root = _model.find_root()
    model = _model.Model.load(root)
    rows = plan(model, args.ids, args.project)
    if not rows:
        sys.stderr.write("nothing matched\n")
        return 2
    if not args.said and not args.dry_run:
        sys.stderr.write(
            "--said is required. Archiving is a scope decision — it removes "
            "work from the list without claiming it was finished — and a scope\n"
            "decision with no reason on the record is one a future session "
            "re-litigates.\n")
        return 2

    unconfirmed = [n for n in rows if n.status == "done"
                   and n.get("closed_origin") != "his-word"]
    moved = []
    for node in rows:
        rel = os.path.relpath(node.path, os.path.join(root, "state", "projects"))
        dest = os.path.join(root, "state", "archive", rel)
        moved.append((node, dest))
        print("  %-9s %-8s %s" % (node.id, node.status, node.title[:52]))
        if args.dry_run:
            continue
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.move(node.path, dest)

    if args.dry_run:
        print("\n%d item(s) would move. Nothing written." % len(rows))
        return 0

    # Out of the backlog too, or E-BACKLOG-DRIFT fails on ids that no longer
    # resolve -- and the file IS the order, so a dangling line is a dead entry.
    backlog = os.path.join(root, "state", "backlog.md")
    gone = {n.id for n, _ in moved}
    if os.path.exists(backlog):
        with open(backlog, "r", encoding="utf-8") as fh:
            lines = fh.readlines()
        with open(backlog, "w", encoding="utf-8") as fh:
            for line in lines:
                if line.split("#", 1)[0].strip() in gone:
                    continue
                fh.write(line)

    note = os.path.join(root, "state", "archive", "README.md")
    stamp = datetime.date.today().isoformat()
    entry = ["", "## %s · %s" % (stamp, new_mod.machine_id(root)), "",
             "> %s" % args.said, ""]
    for node, _dest in moved:
        entry.append("- `%s` (%s) — %s" % (node.id, node.status, node.title))
    if unconfirmed:
        entry += ["",
                  "**%d of these were closed by a machine and never confirmed"
                  " by him** — %s. They archive AS unconfirmed; filing "
                  "something away is not agreeing with it, and relabelling it "
                  "on the way out would be the tool laundering its own guess."
                  % (len(unconfirmed),
                     ", ".join(n.id for n in unconfirmed))]
    header = ("# Archive\n\nFinished or superseded work. **Nothing loads this "
              "directory** — `Model.load` globs `state/projects/*/items/*.md` "
              "and the archive is not on that path, so these items are out of "
              "the backlog, the dashboard and every prompt.\n\nIt sits under "
              "`state/` on purpose: `new.py:next_id()` walks that tree for "
              "max+1, and moving the archive outside it would let an id be "
              "handed out twice — `R-057`, where a transcript citing `Q-004` "
              "bound to the wrong work.\n\nFiles keep their frontmatter, "
              "evidence and handoffs verbatim.\n")
    existing = ""
    if os.path.exists(note):
        with open(note, "r", encoding="utf-8") as fh:
            existing = fh.read()
    with open(note, "w", encoding="utf-8") as fh:
        fh.write((existing or header) + "\n".join(entry) + "\n")

    print("\n%d item(s) archived. Regenerate: python3 tools/publish.py"
          % len(moved))
    return 0


if __name__ == "__main__":
    sys.exit(main())
