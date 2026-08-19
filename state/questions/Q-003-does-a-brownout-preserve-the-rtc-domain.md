---
{
  "id": "Q-003",
  "title": "Does a brownout preserve the RTC domain?",
  "project": "gimbal-bench",
  "status": "next",
  "gates": [],
  "impact": 3,
  "confidence": 4,
  "effort_minutes": 90,
  "cognitive_load": "medium",
  "lead_time_days": 0,
  "keywords": [
    "brownout",
    "rtc",
    "ring",
    "m5",
    "mirror",
    "power",
    "reset-reason",
    "unknown"
  ],
  "evidence": [
    {
      "repo": "gimbal-bench",
      "path": "captures/gimbal10/fixture/ring-mirror-20260814.md",
      "sha": "669a3a7",
      "date": "2026-08-14",
      "note": "'What is still not verified', first bullet."
    }
  ],
  "created": "2026-08-19",
  "updated": "2026-08-19"
}
---

> **The brownout case**, unknown in both directions. A brownout may or may not
> preserve the RTC domain, and nothing here has produced one.

The M5 ring distinguishes "the fixture rebooted itself" from "somebody cut the
power" using three agreeing signals — reset reason, `lost` flag, and whether the
flash mirror had to be restored. A brownout is the case that table has no row
for, and a ceiling fixture on household mains will meet one.

Answering it is part of GB-001's scope; it is written as a question as well
because the answer is a *fact about the hardware* that outlives whatever the
firmware does with it, and because "unknown in both directions" is a precise
statement worth preserving rather than rounding to "probably fine".
