---
{
  "id": "DEC-014",
  "title": "The #57 serial flood waits for a session with the owner present",
  "project": "gimbal-bench",
  "status": "done",
  "ruling_id": "D14",
  "decided": "2026-08-14",
  "revisit_if": "The flood is reproduced offline, or it starts biting outside an armed session.",
  "supersedes": [],
  "superseded_by": null,
  "propagates_to": [],
  "keywords": [
    "serial-flood",
    "d14",
    "liveness",
    "tap",
    "57",
    "browser",
    "disarm"
  ],
  "evidence": [
    {
      "repo": "gimbal-bench",
      "path": "captures/gimbal10/fixture/owner-decisions-20260814.md",
      "sha": "e4d71a9",
      "date": "2026-08-15",
      "note": "Full prose, D14."
    }
  ],
  "created": "2026-08-19",
  "updated": "2026-08-19"
}
---

A deferral with a stated reason: it is a *"you-are-sitting-there"* bug that
only bites during an armed session with a person present, which is exactly the
condition the deployed profile never has.

The ruling also fixes the order of the eventual fix, and the reason is the
useful part:

> **Order matters when it is done:** count where the messages originate, then
> fix the browser, then quiet the firmware's own logging. Quieting the firmware
> first would hide the browser bug under a lower volume rather than fixing it.

The unknown it carries forward is Q-004.
