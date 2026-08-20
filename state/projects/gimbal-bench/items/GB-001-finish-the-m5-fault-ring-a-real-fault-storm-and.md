---
{
  "id": "GB-001",
  "title": "Finish the M5 fault ring: a real fault storm, and the brownout case",
  "project": "gimbal-bench",
  "status": "next",
  "lane": "firmware",
  "gate": "none",
  "machine_affinity": "formd-t1",
  "keywords": [
    "m5",
    "fault-ring",
    "mirror",
    "rtc",
    "brownout",
    "watchdog",
    "t5",
    "wear",
    "nvs",
    "soak"
  ],
  "evidence": [
    {
      "repo": "gimbal-bench",
      "paths": [
        "captures/gimbal10/fixture/ring-*.md",
        "sketches/gimbal/gimbal.ino"
      ],
      "note": "A dated capture showing the mirror committing during a fault storm, and a brownout run that reports which way the RTC domain went."
    }
  ],
  "evidence_found": [],
  "repos": [
    "gimbal-bench"
  ],
  "parent_ruling": null,
  "created": "2026-08-19",
  "updated": "2026-08-20"
}
---

**This is the next thing built, and the ruling says so in its own words.**

> The fault ring (M5) needs nothing from any of them, and it is the next thing
> built.
> — D15, `owner-decisions-20260814.md`

Layers one and two exist and are measured (`ring-first-read-20260814.md`
`c02b507`, `ring-mirror-20260814.md` `669a3a7`, both 2026-08-14). Layer one
found three real defects within an hour of existing — *"none of them visible in
the live serial log"*. What is left is the list the mirror capture writes down
about itself:

> - **The brownout case**, unknown in both directions.
> - **The wear budget is arithmetic, not a measurement.**
> - **The mirror has only ever committed on a healthy-ish bench.** It has never
>   been asked to run during a real fault storm, which is when the rate floor
>   and the in-flight guard actually matter.
> - **A task-watchdog panic** (T5) does not exist, so the panic-retention path
>   is untested.

## Why this gates the Zigbee phase

D15's title is the edge: *"Zigbee stays parked until the fault ring and the
drills are done."* But the fault ring is only the **first** of its two
conditions, and neither of them is permission.

So this item does not point at Z-M1. It points at **GB-014**, the un-park
decision itself, which points at Z-M1. The chain reads *fault ring → a decision
nobody has taken → Z-M1*, which is the honest shape: finishing this item does
not un-park anything.

## Acceptance

A capture under `captures/gimbal10/fixture/` showing the mirror committing
during a storm, and a brownout run that answers Q-003 in one direction or the
other. Not "we think it survives".
