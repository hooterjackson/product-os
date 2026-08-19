---
{
  "id": "DEC-013",
  "title": "The bench may still assert a bus with no motors — warn, do not refuse",
  "project": "gimbal-bench",
  "status": "done",
  "ruling_id": "D13",
  "decided": "2026-08-14",
  "revisit_if": "The warning turns out to be confusing in practice, or a capture is found that was taken under a false assertion.",
  "supersedes": [],
  "superseded_by": null,
  "propagates_to": [],
  "keywords": [
    "bus-assertion",
    "d13",
    "witness",
    "assert-unwitnessed",
    "motorless",
    "wire-suite"
  ],
  "evidence": [
    {
      "repo": "gimbal-bench",
      "path": "captures/gimbal10/fixture/owner-decisions-20260814.md",
      "sha": "e4d71a9",
      "date": "2026-08-15",
      "note": "Full prose, D13."
    }
  ],
  "created": "2026-08-19",
  "updated": "2026-08-19"
}
---

Every motorless tool depends on asserting a bus with no motors on it. The
ruling names why refusing would be the wrong fix:

> The real defect was never that the bench proceeded — the owner knows what is
> plugged in. It was that **the fixture did not know and did not say**.

`revisit_if` is copied from the source rather than invented; D13 states its own
revisit condition, which is rare enough to be worth preserving verbatim.
