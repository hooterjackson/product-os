---
{
  "id": "EL-005",
  "title": "CAN bring-up: both motors answering, and the first READY r=1",
  "project": "robotic-spotlight",
  "status": "done",
  "lane": "hardware",
  "gate": "bench",
  "machine_affinity": "formd-t1",
  "impact": 5,
  "confidence": 5,
  "effort_minutes": 480,
  "cognitive_load": "high",
  "lead_time_days": 0,
  "cost_usd": null,
  "unblocks": [],
  "unblocks_inferred": [],
  "answers": [],
  "keywords": [
    "can",
    "motors",
    "health",
    "ready",
    "bring-up",
    "bench",
    "arm",
    "pose",
    "0x241",
    "0x242"
  ],
  "evidence": [
    {
      "repo": "gimbal-bench",
      "paths": [
        "captures/gimbal10/fixture/bench-session*.md"
      ],
      "note": "A bench capture showing both motors answering and READY r=1."
    }
  ],
  "evidence_found": [
    {
      "kind": "commit",
      "repo": "gimbal-bench",
      "path": "captures/gimbal10/fixture/bench-session-20260815.md",
      "sha": "34b9f7c",
      "date": "2026-08-15",
      "note": "Both motors answering within the first seconds: HEALTH 0x241/0x242 v=23.5 err=0x0000 temp=22 brake=0, 2/s each. READY r=1 reached twice; final verified poses pan 26.14 deg, tilt -35.41 deg."
    },
    {
      "kind": "commit",
      "repo": "gimbal-bench",
      "path": "captures/gimbal10/fixture/bench-session2-20260815.md",
      "sha": "19dd790",
      "date": "2026-08-15",
      "note": "READY r=1 state=armed_idle - armed AND ready, which the capture records as a state this bench had never produced."
    }
  ],
  "repos": [
    "gimbal-bench"
  ],
  "parent_ruling": null,
  "created": "2026-08-19",
  "updated": "2026-08-19",
  "completed": "2026-08-15"
}
---

The milestone the bench had never reached, in its own words:

> **`READY r=1` — the first in this bench's history**

and the next day's session going one better:

> **`READY r=1 state=armed_idle`** — armed AND ready, a state this bench had
> never produced (r=1 had only ever been seen in SAFE).

Marked `done` with two capture SHAs because that is the rule. Note what it does
**not** claim: the motors answer and the fixture reaches ready. That is not the
same as the fixture being finished, and the same capture lists three console
defects found by the owner driving.

Kept `gate: bench` after completion so that filtered views of history stay
honest about where this happened. It was not this Mac.
