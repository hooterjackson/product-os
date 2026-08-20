---
{
  "slug": "engineering-site",
  "name": "Engineering site",
  "prefix": "SITE",
  "description": "The published eight-document build series stays true to what the bench actually did.",
  "phase": "live at engineering.engineered.lighting; stale in both directions",
  "repos": [
    "engineered-lighting-site"
  ],
  "decision_authority": "gimbal-bench",
  "may_rule": false,
  "created": "2026-08-19",
  "updated": "2026-08-20"
}
---

The public MkDocs site. Narrative, not authority.

**This project may never issue a ruling. Every item here is parented to a ruling
ID in `gimbal-bench`** — the `parent_ruling` field is not decoration; an item
here with no parent is an item proposing to decide something on the site's
behalf, which is the failure mode this rule exists to stop.

The site is currently stale *in both directions at once*, which is the sharpest
argument this portfolio makes for having a system at all:

- Docs 6 and 7 **under-claim** — they still describe the ESPHome transport lane
  that D3 retired on 2026-08-14. `tools/stale.py` produces this finding from
  dates rather than from anyone remembering it.
- Doc 4 **over-claims** — its banner says the C6 "now runs Arduino-based Zigbee
  firmware", while `gimbal-bench`'s own README says the firmware has no Zigbee
  stack yet. Doc 4 is *newer* than that README, so no date arithmetic can catch
  it. `stale.py` will never report SITE-002; a human read it. Recorded so nobody
  mistakes the detector's silence for the site being right.
