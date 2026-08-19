---
{
  "id": "GB-014",
  "title": "Un-park Zigbee — the decision D15 leaves open",
  "project": "gimbal-bench",
  "status": "next",
  "lane": "firmware",
  "gate": "external",
  "machine_affinity": null,
  "impact": 4,
  "confidence": 2,
  "effort_minutes": 60,
  "cognitive_load": "high",
  "lead_time_days": 0,
  "cost_usd": null,
  "unblocks": [
    "GB-005"
  ],
  "unblocks_inferred": [],
  "answers": [],
  "keywords": [
    "zigbee",
    "un-park",
    "d15",
    "decision",
    "owner",
    "parked",
    "fault-ring",
    "drills",
    "sequencing",
    "phase"
  ],
  "evidence": [
    {
      "repo": "gimbal-bench",
      "paths": [
        "captures/gimbal10/fixture/owner-decisions-*.md",
        "docs/*DECISION*"
      ],
      "note": "A dated ruling in the gimbal-bench ledger recording the decision and the state of D15's two conditions when it was taken. A commit that merely starts Z-M1 is not evidence that the decision was made."
    }
  ],
  "evidence_found": [],
  "repos": [
    "gimbal-bench"
  ],
  "parent_ruling": "DEC-015",
  "created": "2026-08-19",
  "updated": "2026-08-19"
}
---

**This is a decision, not a task, and it has not been taken.**

It exists as a node because of what the graph said without it. With `GB-001`
pointing straight at `GB-005`, the chain read *finish the fault ring → Z-M1*,
which invites exactly one wrong inference: that completing the fault ring
un-parks Zigbee automatically. It does not. Something has to happen between them
that no agent can do, and a chain that hides an unmade decision is worse than one
that shows it.

## What D15 actually conditions on

> ## D15 — Zigbee stays parked until the fault ring and the drills are done

Two conditions, and the item modelled only the first. `GB-001` is the fault ring.
**The drills are a second, separate, owner-driven condition** — `ZIGBEE-PHASE-PLAN.md`
§7 is headed *"Owner-session bench ladder (radio-live — owner-driven only)"*, and
D14 bundles the `#57` session into that same class of work.

So this node is not a rubber stamp on `GB-001`. It is the point at which somebody
who is not a program looks at both conditions and says the phase may start.

## Why `status: parked` was the wrong shape for the phase

`parked` means set aside indefinitely, and it is excluded from leverage —
applying it to the seven Z-items would have collapsed a 4-hop chain to nothing
and hidden the very structure the ruling is about. D15 names its own un-park
condition, which makes this **sequencing, not scope**.

## What un-parking commits you to, stated before you are asked

The three costs D15 recorded do not expire when the fault ring is done. Two of
them are about the radio, not about the ring:

- **The radio preempts a superloop with zero mutexes.** `esp_zb_task` at priority
  5 against the Arduino loop at 1, single core. The fault ring does not change
  that; `GB-006`'s mailbox is the defence, and it is downstream of this decision,
  not upstream.
- **If the light is on Zigbee, no hub means no light** — which D15 says
  *"undercuts the plan's own strongest rule, that whatever else fails, it stays a
  light."* That tension is not resolved by any item in this repo.

And one sequencing constraint rides along, from D15: when the phase starts, *"the
OTA rollback fix lands **first**, before anything else touches the radio."*

## Acceptance

Not a commit. A dated ruling in `gimbal-bench`'s ledger, in the same shape as
D12–D16, recording the decision and the state of both conditions when it was
taken. If it is ever taken and not written down, it joins D1–D11 (`GB-002`) as
reasoning nobody can recover.
