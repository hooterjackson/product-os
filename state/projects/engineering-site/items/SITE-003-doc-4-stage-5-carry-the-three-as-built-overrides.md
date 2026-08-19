---
{
  "id": "SITE-003",
  "title": "Doc 4 stage 5: carry the three as-built overrides",
  "project": "engineering-site",
  "status": "parked",
  "lane": "content",
  "gate": "none",
  "machine_affinity": null,
  "impact": 3,
  "confidence": 4,
  "effort_minutes": 60,
  "cognitive_load": "medium",
  "lead_time_days": 0,
  "cost_usd": null,
  "unblocks": [],
  "unblocks_inferred": [],
  "answers": [],
  "keywords": [
    "doc4",
    "stage5",
    "star",
    "xp-e2",
    "xp-g2",
    "amber",
    "picobuck",
    "gpio",
    "dlh-3up-eh",
    "as-built",
    "propagation"
  ],
  "evidence": [
    {
      "repo": "engineered-lighting-site",
      "paths": [
        "docs/04-full-fixture-bench.md",
        "docs/bom-checklist.md"
      ],
      "note": "A commit carrying the star, pin-map and mount overrides, or an explicit as-built box saying the bench differs and how."
    }
  ],
  "evidence_found": [
    {
      "kind": "commit",
      "repo": "engineered-lighting-site",
      "sha": "796559c",
      "date": "2026-08-19",
      "note": "attributed by tools/audit.py on 2026-08-19"
    }
  ],
  "repos": [
    "engineered-lighting-site",
    "gimbal-bench"
  ],
  "parent_ruling": "DEC-102",
  "created": "2026-08-19",
  "updated": "2026-08-19"
}
---

Three places where Doc 4 stage 5 and the bench disagree, from
`captures/ui-overhaul/m18-led/RESULTS.md` (`8bc2b5d`, 2026-08-02):

| | Doc 4 says | This bench has |
|---|---|---|
| star | warm/neutral/cool XP-G2 reference | warm XP-E2 + cool XP-E2 + **PC Amber**, amber dark until the WWA component exists |
| pins | GPIO10 warm / 11 neutral / 18 cool | **GPIO10 cold / 11 amber / 18 warm** |
| mount | flat heatsink + thermal adhesive | the **DLH-3UP-EH housing**, which *is* the heatsink and the head's balance mass |

The consequence, which is why this is not cosmetic — Doc 4's done-when requires
the entity to dim *"on all three dies"*, and the bench's amber die is dark by
design:

> He would meter the PicoBuck, reflow the pads, or try to RMA a star that is
> working exactly as specified.

Two more from the same review, worth folding in: the stage-1 **2.0 A supply
limit** must rise to ~3 A by stage 6, and the entity is **"Spot Light"
(`light.spot1`)**, not Doc 4's "Spotlight".

**Provenance note, corrected 2026-08-19.** An earlier draft of this item said
the phrase "Marcelo to call" appeared in neither repository, and withdrew it.
**That was wrong — the string is real**, at `PROJECT-STATE.md:158`, and it makes
the mount row an owner-flagged open decision rather than a documentation gap:

> BoM ripple NOT yet applied (Marcelo to call): where the housing purchase
> lands — it supersedes Doc 4's flat heatsink at the fixture stage.

So the housing is not merely undocumented in Doc 4; **the BoM ripple was
deliberately deferred to him and has not been applied.** The withdrawal came
from trusting GitHub code search instead of grepping the files already on disk
— see `R-054`.
