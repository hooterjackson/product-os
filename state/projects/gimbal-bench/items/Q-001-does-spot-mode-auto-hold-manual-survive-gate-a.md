---
{
  "id": "Q-001",
  "title": "Does Spot Mode (Auto/Hold/Manual) survive gate A?",
  "project": "gimbal-bench",
  "status": "next",
  "lane": "firmware",
  "gate": "none",
  "machine_affinity": null,
  "keywords": [
    "spot-mode",
    "auto",
    "hold",
    "manual",
    "gate-a",
    "d12",
    "preset",
    "re-derive",
    "retire",
    "product-question"
  ],
  "evidence": [
    {
      "repo": "gimbal-bench",
      "path": "docs/ZIGBEE-PHASE-PLAN.md",
      "sha": "5a9bfbd",
      "date": "2026-08-16",
      "note": "§8, the esphome parity checklist."
    }
  ],
  "evidence_found": [],
  "repos": [
    "gimbal-bench"
  ],
  "parent_ruling": null,
  "created": "2026-08-19",
  "updated": "2026-08-20"
}
---

**This is a question, not a task, and the source is explicit that it is unruled:**

> `Spot Mode` (Auto/Hold/Manual) → a gate-A product question (no deployed-profile
> analog under D12 — re-derive or retire)

The tension it sits in is real and both halves are sourced:

- `spot-bench.yaml` marks the Auto/Hold/Manual gate **STILL LIVE, and not
  superseded by anything** — behaviour, not transport.
- D12 gives the deployed profile position commands only, and there is no
  deployed-profile analog of a mode gate under that shape.

So "still live" and "no analog" are both true, and the resolution is a product
decision about what the fixture is, not a firmware decision about what it can
do. It is `impact: 4` because retiring it silently would delete a live
requirement, and re-deriving it blindly would build a mode gate nobody wants.

**Not for an agent to answer.** An agent can lay out the two shapes and what
each costs.
