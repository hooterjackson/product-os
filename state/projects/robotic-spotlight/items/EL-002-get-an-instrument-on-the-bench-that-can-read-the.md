---
{
  "id": "EL-002",
  "title": "Get an instrument on the bench that can read the rail",
  "project": "robotic-spotlight",
  "status": "next",
  "lane": "hardware",
  "gate": "none",
  "machine_affinity": null,
  "impact": 3,
  "confidence": 4,
  "effort_minutes": 20,
  "cognitive_load": "low",
  "lead_time_days": 5,
  "cost_usd": 60.0,
  "unblocks": [],
  "unblocks_inferred": [],
  "answers": [],
  "keywords": [
    "meter",
    "multimeter",
    "rail",
    "voltage",
    "current",
    "psu",
    "undervoltage",
    "12v",
    "latch",
    "instrument"
  ],
  "evidence": [
    {
      "repo": "gimbal-bench",
      "paths": [
        "captures/gimbal10/fixture/hw/**"
      ],
      "note": "A capture with a measured rail voltage in it, taken with an instrument rather than inferred from CAN behaviour."
    }
  ],
  "evidence_found": [],
  "repos": [
    "gimbal-bench",
    "engineered-lighting-site"
  ],
  "parent_ruling": null,
  "created": "2026-08-19",
  "updated": "2026-08-19"
}
---

The bench currently reasons about its power rail by inference, and the capture
that does it says so plainly:

> **What it does not establish:** the PSU's actual state. There is no instrument
> on this bench that measures rail voltage, and the CAN transport cannot
> distinguish *unpowered* from *disconnected*.
> — `supply-state-20260814.md`, `17194a1`

That inference is good — the no-ACK signature is real evidence — but it has a
named blind spot, and the bench's worst diagnosed failure lives inside it: 12.0 V
is this motor's undervoltage-latch line, and when it latches the unit takes its
CAN interface down until a power cycle. M18's review caught the same hazard about
to return at stage 6 wearing a new costume — *"the gimbal broke when the lights
joined."*

**A note on provenance.** An earlier draft of this item quoted a source saying
this bench's meter "has no current range". That string does not exist in either
repository — I searched both. The item stands on the quote above, which does.
