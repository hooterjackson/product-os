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

## Two different guards, and conflating them broke this tool

**AUTHORITY guards answer "who decided this?"** They exist to stop *the agent*
silently reprioritising. They were never meant to stop the owner from deciding
his own project. For a while they did exactly that:

    $ apply.py --field EL-001=cost_usd:486 --said "the tape is the Valent X"
    proposed  EL-001  cost_usd — human-authority. Proposed, not written.

He stated a fact about his own build and the tool filed a proposal for him to
approve later. It routed his decision into a queue addressed to himself.

**TRUTH guards answer "is this provable?"** `done` without `evidence_found` is
refused for *everyone*, him included. That is not about authority and it does
not bend.

## How origin is carried

`--field` is the agent speaking; `--decided` is Marcelo speaking. The flag name
IS the claim, which is the point: writing `--decided` when he did not say it is
a deliberate falsehood rather than a slip. `--decided` also requires `--said`,
so his words are on the record beside the change, and every applied entry is
stamped `on his word` or `inferred` so the two never blur later.

    --field    ID=FIELD:JSON   agent-inferred; human-authority fields PROPOSE
    --decided  ID=FIELD:JSON   he said it; applies. Requires --said.

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


AGENT = "agent"
HUMAN = "human"


def today():
    return datetime.date.today().isoformat()


def parse_pairs(values, split=True):
    """`ID=a,b` repeated -> {ID: [a, b]}.

    `split=False` keeps the value whole. It has to exist because --evidence
    genuinely takes a comma list of SHAs, while --field and --decided take a
    single value that may CONTAIN commas -- and they shared this function.

    Measured: `--decided EL-001=unblocks:["GB-001","GB-002"]` parsed as two
    fragments, wrote the string `[{"kind":"commit"` into an item's
    evidence_found and injected five garbage keys into its frontmatter. No
    error; the write succeeded. Worst on --decided, which is the documented way
    for HIM to state a decided field, and `unblocks` feeds leverage -- the
    largest multiplier in the score.
    """
    out = {}
    for raw in values or []:
        if "=" not in raw:
            raise SystemExit("expected ID=value, got %r" % raw)
        key, _, rest = raw.partition("=")
        parts = ([v.strip() for v in rest.split(",") if v.strip()] if split
                 else [rest.strip()])
        out.setdefault(key.strip().upper(), []).extend(parts)
    return out


class Applier(object):
    def __init__(self, root, dry_run=False):
        self.root = root
        self.dry_run = dry_run
        self.model = _model.Model.load(root)
        self.applied = []
        self.refused = []
        self.proposed = []
        # What THIS run appended, tracked in memory rather than re-read from
        # disk -- otherwise --dry-run reports a weaker refusal than the real
        # run, and the dry run is the one people trust before committing.
        self.added_this_run = {}
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

    def _apply(self, item_id, what, origin):
        self.applied.append((item_id, what, origin))

    def kind_of(self, item_id):
        """Questions are not items. `_fm` orders their keys differently, so
        writing a question with kind="item" produces a valid file that fails
        the canonical check -- which is exactly what parking Q-005 did."""
        return "item"   # the `question` kind was collapsed -- R-069, Phase 1

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
        self.write(node.path, fm, body, self.kind_of(item_id))
        self.added_this_run.setdefault(item_id, []).extend(added)
        self._apply(item_id, "evidence_found += %s" % ", ".join(added), AGENT)

    def set_status(self, item_id, status, origin=AGENT):
        node = self.node(item_id)
        if node is None:
            return
        # AUTHORITY guard -- about who decided, so his word clears it.
        if status in _fm.HUMAN_STATUSES and origin != HUMAN:
            self.proposed.append(
                (item_id, "status", status,
                 "`%s` is a scope decision with taste in it, and leverage "
                 "excludes it -- so setting it would move every upstream "
                 "score. Say so yourself and it applies." % status))
            return
        fm, body = _fm.load(node.path)
        # TRUTH guard -- about whether it is provable, so origin is
        # irrelevant. This one refuses him too, and that is correct: he cannot
        # make an unevidenced completion evidenced by asserting it.
        if status == "done" and not self.prior_evidence.get(item_id):
            fresh = len(self.added_this_run.get(item_id) or [])
            self.refused.append(
                (item_id,
                 "REFUSED status=done: no evidence_found existed before this "
                 "run%s. A completion nobody can click is not a completion, "
                 "and evidence this command discovered a moment ago has not "
                 "been read by anyone."
                 % (" (%d found just now, unread)" % fresh if fresh else "")))
            return
        if status == "done":
            # Only stamp a NEW completion. Confirming an existing one is the
            # documented flow (`--decided <ID>=status:done`), and re-dating it
            # moved EL-005 from 2026-08-15 to 2026-08-19 -- eating the very
            # fact POS-008 exists to surface.
            fm.setdefault("completed", today())
            # Derived here, never accepted from the caller. `closed_origin` is
            # the answer to "did a machine decide this was finished, or did
            # he?" -- and an agent that could set it would be able to launder
            # its own judgement into his word.
            fm["closed_origin"] = "his-word" if origin == HUMAN else "inferred"
        fm["status"] = status
        fm["updated"] = today()
        self.write(node.path, fm, body, self.kind_of(item_id))
        self._apply(item_id, "status -> %s" % status, origin)

    def set_field(self, item_id, field, value, origin=AGENT):
        node = self.node(item_id)
        if node is None:
            return
        if field == "status":
            return self.set_status(item_id, value, origin=origin)
        if field == "closed_origin":
            self.refused.append(
                (item_id,
                 "REFUSED closed_origin: it is DERIVED from who closed the "
                 "item, never set. To confirm a closure, re-affirm it: "
                 "--decided %s=status:done --said \"...\"" % item_id))
            return
        # AUTHORITY guard. The agent inferring a decided value proposes; the
        # owner stating one applies. Same field, different speaker.
        if _fm.AUTHORITY.get(field) == _fm.HUMAN and origin != HUMAN:
            self.proposed.append(
                (item_id, field, value,
                 "`%s` is human-authority and I inferred this. Proposed, not "
                 "written -- say it yourself and it applies." % field))
            return
        fm, body = _fm.load(node.path)
        fm[field] = value
        fm["updated"] = today()
        self.write(node.path, fm, body, self.kind_of(item_id))
        self._apply(item_id, "%s -> %r" % (field, value), origin)

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
        lines += ["- %s — %s  _(%s)_" % (i, w, "on his word" if o == HUMAN
                                         else "inferred")
                  for i, w, o in self.applied] or ["- nothing"]
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
        if any(o == HUMAN for _, _, o in self.applied):
            lines += ["",
                      "_Entries marked **on his word** were applied because he "
                      "said so, not because anything was inferred. That "
                      "distinction is recorded here permanently: a decided "
                      "value and a guessed one must never become "
                      "indistinguishable after the fact._"]
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
    parser.add_argument("--field", action="append", metavar="ID=FIELD:JSON",
                        help="agent-inferred; human-authority fields propose")
    parser.add_argument("--decided", action="append", metavar="ID=FIELD:JSON",
                        help="HE said it; applies, including decided fields. "
                             "Requires --said.")
    parser.add_argument("--said", help="his acceptance sentence, verbatim")
    parser.add_argument("--note")
    parser.add_argument("--window")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    if args.decided and not (args.said or "").strip():
        sys.stderr.write(
            "--decided claims Marcelo decided this, so --said must carry his "
            "words.\nRefusing to record an unattributed human decision.\n")
        return 2

    root = _model.find_root()
    applier = Applier(root, dry_run=args.dry_run)

    for item_id, shas in parse_pairs(args.evidence).items():
        applier.add_evidence(item_id, shas)
    for item_id, values in parse_pairs(args.status).items():
        for value in values:
            applier.set_status(item_id, value)
    for origin, group in ((AGENT, args.field), (HUMAN, args.decided)):
        for item_id, specs in parse_pairs(group, split=False).items():
            for spec in specs:
                field, _, raw = spec.partition(":")
                try:
                    value = json.loads(raw)
                except ValueError:
                    value = raw
                applier.set_field(item_id, field, value, origin=origin)

    path, text = applier.record(args.said, args.note, args.window)

    for item_id, what, origin in applier.applied:
        print("applied   %-9s %-46s %s"
              % (item_id, what,
                 "(on his word)" if origin == HUMAN else "(inferred)"))
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
