---
{
  "id": "POS-008",
  "title": "Surface inferred closures, record the public decision",
  "project": "product-os",
  "status": "doing",
  "lane": "infra",
  "gate": "none",
  "machine_affinity": null,
  "impact": 4,
  "confidence": 4,
  "effort_minutes": 180,
  "cognitive_load": "medium",
  "lead_time_days": 0,
  "cost_usd": null,
  "unblocks": [],
  "keywords": [
    "inferred",
    "closure",
    "confirmed",
    "visibility",
    "brief",
    "decision",
    "public",
    "disclosure",
    "stamp",
    "guarantee"
  ],
  "evidence": [
    {
      "repo": "product-os",
      "paths": [
        "tools/brief.py",
        "tools/rank.py",
        "tools/build.py",
        "state/projects/product-os/decisions/DEC-201-*"
      ],
      "note": "An unconfirmed closure is visible in a brief's first ten lines, in build/now.md, and via rank.py --unconfirmed; DEC-201 exists with a revisit trigger."
    }
  ],
  "created": "2026-08-19",
  "updated": "2026-08-19"
}
---

`R-059` concluded that the durable guarantee against a defeatable `done` guard
was the `(inferred)` stamp — permanently legible as a machine's judgement
rather than Marcelo's word. That reasoning holds. The problem was where the
stamp lived:

    "inferred" in state/audits/work-laptop/   ->  3 records
    "inferred" in build/now.md                ->  0
    "inferred" in build/briefs/POS-003.md     ->  0

It was recorded in the one place nobody reads, including the brief for the very
item it described. **A guarantee nobody can see is not a guarantee** — the same
shape as four earlier findings here, where the rule existed and nothing executed
it.

## What changed

`closed_origin` is **derived by `apply.py` from who actually closed the item**,
never accepted from the caller — an agent able to set it could launder its own
judgement into his word, so `--field`/`--decided closed_origin` is refused
outright.

Surfaced in three places a human actually looks:

- **The brief says it on its face**, inside the first ten lines, above the
  freshness stamp — not in a footer.
- **`build/now.md`** leads with the count.
- **`rank.py --unconfirmed`** answers *"what did the machine close on its own
  judgement that I never confirmed?"* and prints the confirming sentence.

Backfilled all five existing closures honestly as `inferred`, including the two
seeded ones. **Marcelo has confirmed none of them.**

## Two bugs found by testing the visibility, not the mechanism

`build.py` wrote briefs only for **active** items — so the "closed on my
judgement" banner could never appear, because closed items are exactly the ones
that filter skips. And `build/briefs/` was never cleared, so `POS-003`'s brief
sat at `doing` after it was closed. "Regenerated wholesale" was documented and
not implemented.

## Handoffs

### 2026-08-19 · work-laptop
**Did:** the three surfaces, `DEC-201`, and the two build bugs.
**Next:** confirm or reject the five unconfirmed closures — a sentence each.
**Ruled out:** hardening the snapshot guard, again. `R-059` stands.
**Reached:** product-os · **Could not reach:** —
