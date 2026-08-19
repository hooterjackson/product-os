---
{
  "id": "SITE-002",
  "title": "Doc 4's banner over-claims: the firmware has no Zigbee stack",
  "project": "engineering-site",
  "status": "parked",
  "lane": "content",
  "gate": "none",
  "machine_affinity": null,
  "impact": 4,
  "confidence": 5,
  "effort_minutes": 30,
  "cognitive_load": "low",
  "lead_time_days": 0,
  "cost_usd": null,
  "unblocks": [],
  "unblocks_inferred": [],
  "answers": [],
  "keywords": [
    "doc4",
    "zigbee",
    "banner",
    "over-claim",
    "d15",
    "parked",
    "firmware",
    "arduino",
    "propagation"
  ],
  "evidence": [
    {
      "repo": "engineered-lighting-site",
      "paths": [
        "docs/04-full-fixture-bench.md"
      ],
      "note": "A commit correcting the banner to match what the firmware actually has."
    }
  ],
  "evidence_found": [
    {
      "kind": "commit",
      "repo": "engineered-lighting-site",
      "sha": "796559c",
      "date": "2026-08-19",
      "note": "attributed by tools/audit.py on 2026-08-19"
    }
  ],
  "repos": [
    "engineered-lighting-site",
    "gimbal-bench"
  ],
  "parent_ruling": "DEC-015",
  "created": "2026-08-19",
  "updated": "2026-08-19"
}
---

**The site is stale in both directions at once, and this is the other one.**

Doc 4 carries a banner, live on the public site:

> the fixture's C6 now runs Arduino-based Zigbee firmware, not ESPHome

`gimbal-bench`'s own README, at HEAD:

> the firmware has no Zigbee stack, OTA path, or concurrency mailbox yet, and
> Zigbee stays parked (D15) until the build begins.

Both are current. Doc 4 was last committed `796559c` on **2026-08-16T22:18**;
the README `9549189` on **2026-08-16T05:41** — Doc 4 is the *newer* of the two.

**That is why this item matters more than its 30 minutes suggest.**
`tools/stale.py` compares a document's last-commit date against a ruling's date
and reports the doc if it is older. Doc 4 is not older. **stale.py will never
report SITE-002.** A human found it by reading two repos against each other, and
no arithmetic in this system would have.

Recorded in the project file as well, so that nobody mistakes the detector's
silence for the site being right.

The half Doc 4 gets right: the ESPHome *flash lane* no longer applies, which is
what `spot-bench.yaml`'s "config and compile only, never upload or run" rule has
said since before D3.
