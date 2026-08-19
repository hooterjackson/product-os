---
{
  "id": "POS-001",
  "title": "Build product-os slice 1a-minus",
  "project": "product-os",
  "status": "doing",
  "lane": "infra",
  "gate": "none",
  "machine_affinity": "work-laptop",
  "impact": 4,
  "confidence": 4,
  "effort_minutes": 960,
  "cognitive_load": "high",
  "lead_time_days": 0,
  "cost_usd": null,
  "unblocks": [],
  "unblocks_inferred": [],
  "answers": [],
  "keywords": [
    "product-os",
    "slice-1a",
    "seed",
    "rank",
    "validate",
    "plugin",
    "hook",
    "ruled-out",
    "bootstrap"
  ],
  "evidence": [
    {
      "repo": "product-os",
      "paths": [
        "state/**",
        "tools/**",
        "plugin/**",
        "wiki/**"
      ],
      "note": "validate.py exits 0; rank.py returns an ordering; build.py reports a confirmed chain of >= 3 hops; stale.py reproduces the Doc 6 / D3 contradiction unaided."
    }
  ],
  "evidence_found": [],
  "repos": [
    "product-os"
  ],
  "parent_ruling": null,
  "created": "2026-08-19",
  "updated": "2026-08-19"
}
---

This repo, being built. `status: doing`.

Six tools, three skills, one hook, the seed, and the ruled-out register.

**It is not done and will not be marked done here.** The milestone tests are
written into the evidence rule above precisely so that a future session cannot
close this on a feeling. When they pass, they pass on a run somebody can repeat.

Cite `POS-001` in the first message of any session that works on this repo. That
string is what lets a thread indexer link the conversation to the work, later,
for free.
