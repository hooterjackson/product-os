---
{
  "id": "APP-001",
  "title": "Give HomeApp an evidence rule that does not depend on git history",
  "project": "home-app",
  "status": "next",
  "lane": "app",
  "gate": "none",
  "machine_affinity": null,
  "impact": 2,
  "confidence": 4,
  "effort_minutes": 45,
  "cognitive_load": "low",
  "lead_time_days": 0,
  "cost_usd": null,
  "unblocks": [],
  "unblocks_inferred": [],
  "answers": [],
  "keywords": [
    "homeapp",
    "evidence",
    "squashed",
    "history",
    "changelog",
    "coverage",
    "unreachable"
  ],
  "evidence": [
    {
      "repo": "HomeApp",
      "paths": [
        "CHANGELOG.md",
        "docs/**"
      ],
      "note": "A file-level evidence source in HomeApp that changes when work lands, since commit history cannot."
    }
  ],
  "evidence_found": [],
  "repos": [
    "HomeApp"
  ],
  "parent_ruling": null,
  "created": "2026-08-19",
  "updated": "2026-08-19"
}
---

`hooterjackson/HomeApp` is **one commit**: `b769b30`, 2026-06-12T15:05Z,
"Deploy current Home app snapshot". I verified this against the remote — the
whole `main` history is that single entry.

Every commit-shaped evidence query against this repo therefore returns nothing,
forever, and **nothing is not the same as no work happened.** Left alone, this
project would quietly report "clean" in every audit while being the one place
the system genuinely cannot see.

Smallest honest fix: a `CHANGELOG.md` in HomeApp that gets an entry when work
lands, and an evidence rule pointed at it instead of at `git log`.

Low impact on purpose. This is not important work; it is work that stops an
unimportant project from producing confident wrong answers.
