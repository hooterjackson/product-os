---
{
  "id": "EL-004",
  "title": "Update every document that still names the old motor (EL-004 · RMD-L-4005 → 5005)",
  "project": "robotic-spotlight",
  "status": "done",
  "lane": "hardware",
  "gate": "none",
  "machine_affinity": null,
  "keywords": [
    "motor",
    "rmd-l-5005",
    "rmd-l-4005",
    "swap",
    "bom",
    "propagation"
  ],
  "evidence": [
    {
      "repo": "engineered-lighting-site",
      "paths": [
        "docs/**",
        "prompts/**"
      ],
      "note": "A commit propagating the 5005 through everything forward-looking."
    }
  ],
  "evidence_found": [
    {
      "kind": "commit",
      "repo": "engineered-lighting-site",
      "path": "docs/",
      "sha": "8fb39bf",
      "date": "2026-07-21",
      "note": "Motor swap: RMD-L-4005 -> RMD-L-5005 in everything forward-looking."
    },
    {
      "kind": "commit",
      "repo": "engineered-lighting-site",
      "path": "docs/03b-print-the-frame.md",
      "sha": "db41f3f",
      "date": "2026-07-22",
      "note": "Doc 3b + docs/cad/frame.scad: parametric scaffold, coupon-first workflow."
    }
  ],
  "repos": [
    "engineered-lighting-site"
  ],
  "parent_ruling": null,
  "created": "2026-08-19",
  "updated": "2026-08-23",
  "completed": "2026-07-21",
  "closed_origin": "inferred"
}
---

Done, and recorded because of *how* it was nearly re-done.

`PROJECT-STATE.md` listed two prompts as pending. Both had already shipped —
`8fb39bf` (2026-07-21) and `db41f3f` (2026-07-22) — **before the file listing
them as pending was committed** (`88a3a58`, 2026-08-01). The file eventually
corrected itself:

> Earlier revisions of this file listed two prompts as pending; git history
> shows both were executed before it was committed.

This is the failure mode product-os exists to remove, caught in the wild in the
portfolio's own handoff file. It is also why POS-002 exists.
