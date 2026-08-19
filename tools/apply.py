#!/usr/bin/env python3
"""Apply an accepted audit, and write the record that stops it being re-argued.

Acceptance happens in ONE SENTENCE in chat -- "yes to A, do B1 at $240, drop
B3". The `/audit` skill turns that sentence into the explicit flags below; this
tool does exactly what it is told and nothing else.

    python3 tools/apply.py --evidence GB-004=19dd790,34b9f7c \\
                           --status GB-004=doing \\
                           --said "yes to A, GB-004 to doing" \\
                           --note "armed lane still unproven"

    python3 tools/apply.py --dry-run ...        show, change nothing

Two refusals are hard-coded and do not bend:

1. **`done` without `evidence_found` is refused.** Not warned about; refused.
2. **Human-authority fields are refused.** `impact`, `confidence`,
   `effort_minutes`, `lead_time_days`, `cost_usd`, `unblocks`, `pin`,
   `project`, `gate`, `machine_affinity`, `evidence`, and the `dropped` /
   `parked` statuses. Those get written to `state/proposals/` instead, which is
   what "the system proposes, it never decides" means when it is load-bearing
   rather than decorative.

Every run appends to `state/audits/<machine>/`, including a refused one. A
refusal nobody recorded gets re-litigated next month by somebody who does not
know it was already asked.
"""

import argparse
import datetime
import json
import os
import sys

import _fm
import _model
import new as new_mod


def today():
    return datetime.date.today().isoformat()


def parse_pairs(values):
    """`ID=a,b` repeated -> {ID: [a, b]}."""
    out = {}
    for raw in values or []:
        if "=" not in raw:
            raise SystemExit("expected ID=value, got %r" % raw)
        key, _, rest = raw.partition("=")
        out.setdefault(key.strip().upper(), []).extend(
            [v.strip() for v in rest.split(",") if v.strip()])
    return out


class Applier(object):
    def __init__(self, root, dry_run=False):
        self.root = root
        self.dry_run = dry_run
        self.model = _model.Model.load(root)
        self.applied = []
        self.refused = []
        self.proposed = []
        # Evidence as it stood BEFORE this run. Closing an item is checked
        # against this snapshot, never against what the same command just
        # appended -- otherwise "no done without evidence" quietly degrades
        # into "no done without a path match", which is the inference the
        # audit explicitly refuses to make. Evidence found by a run has to be
        # read by a person before the next run can close anything on it.
        self.prior_evidence = {
            node.id: list(node.get("evidence_found") or [])
            for node in self.model.nodes.values()
        }

    def node(self, item_id):
        node = self.model.nodes.get(item_id)
        if node is None:
            self.refused.append((item_id, "no such item"))
        return node

    # -- agent authority ----------------------------------------------------

    def add_evidence(self, item_id, shas, repo_hint=None):
        node = self.node(item_id)
        if node is None:
            return
        fm, body = _fm.load(node.path)
        found = list(fm.get("evidence_found") or [])
        known = {str(e.get("sha") or "")[:7] for e in found}
        repos = fm.get("repos") or []
        added = []
        for sha in shas:
            short = sha[:7]
            if short in known:
                continue
            found.append({
                "kind": "commit",
                "repo": repo_hint or (repos[0] if repos else None),
                "sha": short,
                "date": today(),
                "note": "attributed by tools/audit.py on %s" % today(),
            })
            known.add(short)
            added.append(short)
        if not added:
            return
        fm["evidence_found"] = found
        fm["updated"] = today()
        self.write(node.path, fm, body, "item")
        self.applied.append((item_id, "evidence_found += %s" % ", ".join(added)))

    def set_status(self, item_id, status):
        node = self.node(item_id)
        if node is None:
            return
        if status in _fm.HUMAN_STATUSES:
            self.proposed.append(
                (item_id, "status", status,
                 "`%s` is a scope decision with taste in it, and leverage "
                 "excludes it -- so setting it would move every upstream "
                 "score." % status))
            return
        fm, body = _fm.load(node.path)
        if status == "done" and not self.prior_evidence.get(item_id):
            fresh = len(fm.get("evidence_found") or [])
            self.refused.append(
                (item_id,
                 "REFUSED status=done: no evidence_found existed before this "
                 "run%s. A completion nobody can click is not a completion, "
                 "and evidence this command discovered a moment ago has not "
                 "been read by anyone."
                 % (" (%d found just now, unread)" % fresh if fresh else "")))
            return
        if status == "done":
            fm["completed"] = today()
        fm["status"] = status
        fm["updated"] = today()
        self.write(node.path, fm, body, "item")
        self.applied.append((item_id, "status -> %s" % status))

    def set_field(self, item_id, field, value):
        node = self.node(item_id)
        if node is None:
            return
        if _fm.AUTHORITY.get(field) == _fm.HUMAN:
            self.proposed.append(
                (item_id, field, value,
                 "`%s` is human-authority. Proposed, not written." % field))
            return
        fm, body = _fm.load(node.path)
        fm[field] = value
        fm["updated"] = today()
        self.write(node.path, fm, body, "item")
        self.applied.append((item_id, "%s -> %r" % (field, value)))

    def write(self, path, fm, body, kind):
        if self.dry_run:
            return
        _fm.write(path, fm, body, kind)

    # -- the record ---------------------------------------------------------

    def record(self, said, note, window):
        machine = new_mod.machine_id(self.root)
        directory = os.path.join(self.root, "state", "audits", machine)
        stamp = datetime.datetime.now(datetime.timezone.utc)
        name = "%s-audit.md" % stamp.strftime("%Y%m%dT%H%M")
        lines = [
            "# Audit — %s · %s" % (today(), machine),
            "",
            "**Window:** %s → %s" % (window or "(unspecified)", today()),
            "**Accepted, in his words:** %s" % (said or "(not recorded)"),
        ]
        if note:
            lines += ["", "**Note:** %s" % note]
        lines += ["", "## Applied", ""]
        lines += ["- %s — %s" % (i, w) for i, w in self.applied] or ["- nothing"]
        lines += ["", "## Refused", ""]
        if self.refused:
            lines += ["- %s — %s" % (i, w) for i, w in self.refused]
            lines += ["",
                      "A refusal is recorded so it is not re-argued by somebody "
                      "who does not know it was already asked."]
        else:
            lines += ["- nothing"]
        lines += ["", "## Proposed (human authority — not written)", ""]
        if self.proposed:
            for item_id, field, value, why in self.proposed:
                lines.append("- **%s** `%s` → `%r`  \n  %s" % (item_id, field, value, why))
        else:
            lines += ["- nothing"]
        lines += ["", "---", "",
                  "Written by `tools/apply.py`. The ranked list is a "
                  "conversation starter; this file is the part that does not "
                  "have to be had again."]
        text = "\n".join(lines) + "\n"
        path = os.path.join(directory, name)
        if self.dry_run:
            return path, text
        os.makedirs(directory, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path, text


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", action="append", metavar="ID=SHA[,SHA]")
    parser.add_argument("--status", action="append", metavar="ID=STATUS")
    parser.add_argument("--field", action="append", metavar="ID=FIELD:JSON")
    parser.add_argument("--said", help="his acceptance sentence, verbatim")
    parser.add_argument("--note")
    parser.add_argument("--window")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    root = _model.find_root()
    applier = Applier(root, dry_run=args.dry_run)

    for item_id, shas in parse_pairs(args.evidence).items():
        applier.add_evidence(item_id, shas)
    for item_id, values in parse_pairs(args.status).items():
        for value in values:
            applier.set_status(item_id, value)
    for item_id, specs in parse_pairs(args.field).items():
        for spec in specs:
            field, _, raw = spec.partition(":")
            try:
                value = json.loads(raw)
            except ValueError:
                value = raw
            applier.set_field(item_id, field, value)

    path, text = applier.record(args.said, args.note, args.window)

    for item_id, what in applier.applied:
        print("applied   %-9s %s" % (item_id, what))
    for item_id, why in applier.refused:
        print("REFUSED   %-9s %s" % (item_id, why))
    for item_id, field, _value, why in applier.proposed:
        print("proposed  %-9s %s — %s" % (item_id, field, why))
    print()
    print("%s %s" % ("would write" if args.dry_run else "record  ",
                     os.path.relpath(path, root)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
