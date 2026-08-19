---
{
  "id": "GB-004",
  "title": "M6 on hardware: the motor-silent limb, MUTE-CLEAR, and the armed lane",
  "project": "gimbal-bench",
  "status": "next",
  "lane": "firmware",
  "gate": "bench",
  "machine_affinity": "formd-t1",
  "impact": 4,
  "confidence": 4,
  "effort_minutes": 180,
  "cognitive_load": "high",
  "lead_time_days": 0,
  "cost_usd": null,
  "unblocks": [],
  "unblocks_inferred": [],
  "answers": [],
  "keywords": [
    "m6",
    "mute",
    "mute-clear",
    "armed",
    "motor-silent",
    "bus-no-ack",
    "drill",
    "bench-session"
  ],
  "evidence": [
    {
      "repo": "gimbal-bench",
      "paths": [
        "captures/gimbal10/fixture/bench-session*.md",
        "captures/gimbal10/fixture/*mute*"
      ],
      "note": "A bench capture showing MUTE cause=motor-silent on the armed lane, and a MUTE-CLEAR, on real hardware."
    }
  ],
  "evidence_found": [],
  "repos": [
    "gimbal-bench"
  ],
  "parent_ruling": "DEC-016",
  "created": "2026-08-19",
  "updated": "2026-08-19"
}
---

M6's mute machinery landed and flashed on 2026-08-15. One limb is proven live:

> proven live: `MUTE cause=bus-no-ack` at 2.3 s from boot

and the same paragraph names what is not:

> Still unproven on hardware: "the motor-silent limb, MUTE-CLEAR, the armed
> lane."

The 08-15 session tried and lost one of them to an unrelated reboot — the
board reset at PSU-on, so *"the standing 35-minute mute latch died with the
reboot instead of being cleared by first contact; MUTE-CLEAR's live proof moved
to S3."*

Worth carrying into the session: the P1 found in M6's first hour was invisible
to **538 tests, six review mutations, and two green gates, because nothing
offline transmits.** That is the argument for doing this at the bench rather
than adding another offline test.
