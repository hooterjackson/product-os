---
{
  "id": "HAI-001",
  "title": "Rotate the GPU box's Linux password",
  "project": "home-ai-infra",
  "status": "next",
  "lane": "infra",
  "gate": "none",
  "machine_affinity": null,
  "impact": 4,
  "confidence": 5,
  "effort_minutes": 15,
  "cognitive_load": "low",
  "lead_time_days": 0,
  "cost_usd": null,
  "unblocks": [],
  "unblocks_inferred": [],
  "answers": [],
  "keywords": [
    "password",
    "rotate",
    "credential",
    "ssh",
    "gpu",
    "elserver",
    "hygiene",
    "secret"
  ],
  "evidence": [
    {
      "repo": "home-ai-infra",
      "paths": [],
      "note": "A dated manual note. There is no repository here, so this is a note-or-nothing item and the note must carry the date."
    }
  ],
  "evidence_found": [],
  "repos": [],
  "parent_ruling": null,
  "created": "2026-08-19",
  "updated": "2026-08-19"
}
---

The handoff file for the GPU box says, as step 2 of its SSH setup:

> **Rotate your Linux password** (`passwd` on the box) — it was shared in the
> chat session on the work computer.
> — `~/Claude/PICKUP.md:19`

That file is dated **2026-06-09**. Today is 2026-08-19.

    2026-06-09 → 2026-08-19
      June  30 − 9 = 21 days
      July           31 days
      August         19 days
                  = 71 days

Nothing anywhere records that it was done. That is not the same as knowing it
was not — `home-ai-infra` has **no repository at all** (`state/repos.json`:
`owner: null`), so this system cannot look, and the honest report is
*unreachable*, not *clean*.

Fifteen minutes. Highest score-per-minute in the seed, and it is fifteen minutes
because a password that was pasted into a chat has been sitting live for ten
weeks.

If it has already been rotated, close it with a dated note — that note is the
only evidence this project can produce.
