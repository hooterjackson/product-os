---
{
  "id": "GB-006",
  "title": "Add the single-slot mailbox the radio and the safety loop pass messages through (Z-M0)",
  "project": "gimbal-bench",
  "status": "next",
  "lane": "firmware",
  "gate": "none",
  "machine_affinity": "formd-t1",
  "keywords": [
    "zigbee",
    "z-m0",
    "mailbox",
    "coalesce",
    "stop-latch",
    "preemption",
    "superloop",
    "parked"
  ],
  "evidence": [
    {
      "repo": "gimbal-bench",
      "paths": [
        "sketches/gimbal/gimbal.ino",
        "tests/test_gimbal10_firmware.py"
      ],
      "note": "Source-contract pin: the callback enqueues only. Python model: newest-wins, a stop is never superseded and purges a pending aim."
    }
  ],
  "evidence_found": [],
  "repos": [
    "gimbal-bench"
  ],
  "parent_ruling": "DEC-015",
  "created": "2026-08-19",
  "updated": "2026-08-23"
}
---

> **Z-M0** | **The §9.1 mailbox primitive** — single-slot coalesce-to-latest
> admission record using **primitive types (uint16/uint8), not esp-zigbee-lib
> enums** [§10 hole 4], so it compiles ahead of the library; the always-honored
> stop latch bypassing + purging the slot; a fake producer.

This is the defence against the hazard D15 parks the phase over — a radio task
at priority 5 preempting a superloop with zero mutexes. The plan is explicit
about its weight:

> the mailbox is the whole defense **against the preemption hazard** [§10 hole
> 12] and this soak is non-negotiable before aim.

Depends on GB-005 per the plan's stated dependency order.
