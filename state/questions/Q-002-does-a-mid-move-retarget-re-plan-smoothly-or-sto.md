---
{
  "id": "Q-002",
  "title": "Does a mid-move retarget re-plan smoothly, or stop and restart?",
  "project": "gimbal-bench",
  "status": "next",
  "gates": [],
  "impact": 4,
  "confidence": 4,
  "effort_minutes": 180,
  "cognitive_load": "high",
  "lead_time_days": 0,
  "keywords": [
    "retarget",
    "follow",
    "broadway",
    "smooth-motion",
    "0xa4",
    "d12",
    "goto",
    "measurement"
  ],
  "evidence": [
    {
      "repo": "gimbal-bench",
      "path": "captures/gimbal10/fixture/owner-decisions-20260814.md",
      "sha": "e4d71a9",
      "date": "2026-08-15",
      "note": "D12's open sub-question."
    }
  ],
  "created": "2026-08-19",
  "updated": "2026-08-19"
}
---

D12 settles the safety half and leaves this open, and states plainly that it is
**a measurement rather than an argument**:

> If the motor re-plans its curve smoothly on a new `0xA4` that arrives before
> deceleration, a follow looks like a Broadway spotlight. If it stops and
> restarts, it looks like a stuttering security camera.

> Nobody has measured which.

Why it is worth a whole question: it is the *only* thing that decides whether
the product's most appealing behaviour exists at all —

> it is the single question whose answer decides whether the follow experience
> is available at all.

Safety is not in play. A follow is a rapid succession of position commands and
preserves the self-terminating property exactly; D12 says so.

It belongs to the smooth-motion project, which product-os does not track. Held
here so it is not lost between two plans, with `gates: []` because no source
draws an edge from it to anything in this repo.
