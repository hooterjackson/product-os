---
{
  "id": "POS-002",
  "title": "Point PROJECT-STATE.md at product-os",
  "project": "product-os",
  "status": "next",
  "lane": "content",
  "gate": "none",
  "machine_affinity": null,
  "impact": 3,
  "confidence": 5,
  "effort_minutes": 25,
  "cognitive_load": "low",
  "lead_time_days": 0,
  "cost_usd": null,
  "unblocks": [],
  "unblocks_inferred": [],
  "answers": [],
  "keywords": [
    "project-state",
    "pointer",
    "handoff",
    "state-file",
    "drift",
    "bootstrap",
    "ninth"
  ],
  "evidence": [
    {
      "repo": "engineered-lighting-site",
      "paths": [
        "PROJECT-STATE.md"
      ],
      "note": "A commit adding a pointer from PROJECT-STATE.md into product-os, naming which file is authoritative for what."
    }
  ],
  "evidence_found": [],
  "repos": [
    "engineered-lighting-site",
    "product-os"
  ],
  "parent_ruling": null,
  "created": "2026-08-19",
  "updated": "2026-08-19"
}
---

**The single most likely way this repo fails is by becoming state file number
nine** in a portfolio that already has eight, each confidently disagreeing with
the others.

`PROJECT-STATE.md` is the incumbent. It opens by telling every agent on every
machine to read it first, and it is already demonstrably wrong in both
directions: its header says 2026-07-31, and it lists as "pending" two prompts
that had shipped ten days earlier (see EL-004).

A pointer is not a merge. It should say which file is authoritative for what —
`PROJECT-STATE.md` for narrative and the site's own build state, product-os for
priority, gating and evidence — and it should be short enough that nobody has to
maintain it.

Twenty-five minutes, and it is the difference between two systems and two
opinions.
