---
{
  "id": "Q-004",
  "title": "Where do 300 liveness taps a second come from?",
  "project": "gimbal-bench",
  "status": "next",
  "gates": [],
  "impact": 3,
  "confidence": 3,
  "effort_minutes": 120,
  "cognitive_load": "high",
  "lead_time_days": 0,
  "keywords": [
    "serial-flood",
    "57",
    "liveness",
    "tap",
    "d14",
    "browser",
    "retry",
    "disarm",
    "unknown"
  ],
  "evidence": [
    {
      "repo": "gimbal-bench",
      "path": "captures/gimbal10/fixture/owner-decisions-20260814.md",
      "sha": "e4d71a9",
      "date": "2026-08-15",
      "note": "D14, 'The honest wrinkle, carried forward'."
    }
  ],
  "created": "2026-08-19",
  "updated": "2026-08-19"
}
---

The liveness tap should go about 5 times a second. Something sends it about
**300**, which jams the cable so the genuine tap cannot get through, so the
fixture concludes the operator has vanished and disarms.

> Nobody knows where 300/s comes from. Every known sender caps around 30/s even
> degraded, so something is retrying in a tight loop and it has never been
> found.

That is a factor of ten above the fastest thing anyone can name, which is what
makes it a question rather than a bug report — the sender is not in the known
set.

D14 defers the *fix* to an owner-present session (DEC-014) and warns that it may
resist offline reproduction. The question is held separately from the deferral
because the count is the first step of D14's own stated order — *"count where
the messages originate, then fix the browser, then quiet the firmware"* — and
counting is cheaper than fixing.
