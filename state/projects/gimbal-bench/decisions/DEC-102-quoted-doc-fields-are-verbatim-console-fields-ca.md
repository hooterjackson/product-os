---
{
  "id": "DEC-102",
  "title": "Quoted doc fields are verbatim; console fields carry what the bench has",
  "project": "gimbal-bench",
  "status": "done",
  "ruling_id": "M18-precedence",
  "decided": "2026-08-02",
  "revisit_if": "The published docs are brought level with the as-built bench, at which point the override table should shrink rather than grow.",
  "supersedes": [],
  "superseded_by": null,
  "propagates_to": [],
  "keywords": [
    "m18",
    "precedence",
    "drift-test",
    "as-built",
    "star",
    "xp-e2",
    "amber",
    "picobuck",
    "doc4",
    "stage5"
  ],
  "evidence": [
    {
      "repo": "gimbal-bench",
      "path": "captures/ui-overhaul/m18-led/RESULTS.md",
      "sha": "8bc2b5d",
      "date": "2026-08-02",
      "note": "The precedence rule and the three as-built overrides."
    }
  ],
  "created": "2026-08-19",
  "updated": "2026-08-19"
}
---

The rule, as written into the console's `stages.js` header:

> **quoted fields are the doc, verbatim, and the drift test enforces it;
> console-authored fields carry what this bench actually has — and where the two
> disagree, they say so out loud.**

The consequence it was written to prevent is the reason this is a decision and
not a note. Doc 4's done-when requires the Spotlight entity to dim on **all
three dies**; the bench's star is a one-off whose amber die stays dark by
design. Without the override the owner reaches the finish line and:

> He would meter the PicoBuck, reflow the pads, or try to RMA a star that is
> working exactly as specified.

SITE-003 is the propagation item. Note what this ruling is **not**: it does not
license the site to be edited on the console's say-so. It licenses the console
to disagree out loud, and it makes the site's divergence visible enough to file.
