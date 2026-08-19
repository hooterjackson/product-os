---
{
  "id": "GB-003",
  "title": "The 08-12 witness capture the owner owes, and only the owner",
  "project": "gimbal-bench",
  "status": "next",
  "lane": "content",
  "gate": "bench",
  "machine_affinity": "formd-t1",
  "impact": 3,
  "confidence": 3,
  "effort_minutes": 60,
  "cognitive_load": "medium",
  "lead_time_days": 0,
  "cost_usd": null,
  "unblocks": [],
  "unblocks_inferred": [],
  "answers": [],
  "keywords": [
    "d16",
    "d11",
    "witness",
    "capture",
    "08-12",
    "mute",
    "rail",
    "testimony",
    "owner-only"
  ],
  "evidence": [
    {
      "repo": "gimbal-bench",
      "paths": [
        "captures/gimbal10/fixture/*witness*",
        "captures/gimbal10/fixture/*20260812*"
      ],
      "note": "A dated, attributed capture of the 08-12 episode: what survived the 60-second power cycle and what revived it."
    }
  ],
  "evidence_found": [
    {
      "kind": "commit",
      "repo": "gimbal-bench",
      "sha": "8a4c974",
      "date": "2026-08-19",
      "note": "attributed by tools/audit.py on 2026-08-19"
    },
    {
      "kind": "commit",
      "repo": "gimbal-bench",
      "sha": "b0a472f",
      "date": "2026-08-19",
      "note": "attributed by tools/audit.py on 2026-08-19"
    }
  ],
  "repos": [
    "gimbal-bench"
  ],
  "parent_ruling": "DEC-016",
  "created": "2026-08-19",
  "updated": "2026-08-19"
}
---

D16 ends with an obligation that names its own holder:

> **Still owed by the owner, and only the owner:** a dated, attributed witness
> capture of the 08-12 episode (what survived the 60-second power cycle, what
> revived it). It is the only [T]-grade claim in the M6 decision chain and the
> rail demotion (D11) leans on it. Until it exists, D11's premise rests on plan
> text nobody can source.

This is in the tracker precisely because no agent can close it. It is memory,
not measurement, and it is load-bearing for a hardware decision.

Note the direction of travel: `reader-planV2.md` records that D2's 08-12 half
was already **retracted** on 2026-08-15 — *"testimony its own source
disclaims"*. So the capture is not confirmation of something believed; it is the
only thing that could put a premise back on its feet.

`confidence: 3` is proposed low deliberately. Recall of an episode a week old,
written down for the first time, is weaker evidence than a log — and the item
should say so rather than pretend a capture makes it [V].
