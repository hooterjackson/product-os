---
{
  "id": "POS-006",
  "title": "Group D coverage: cluster 301 unattributed commits into items",
  "project": "product-os",
  "status": "doing",
  "lane": "infra",
  "gate": "none",
  "machine_affinity": null,
  "impact": 4,
  "confidence": 3,
  "effort_minutes": 240,
  "cognitive_load": "high",
  "lead_time_days": 0,
  "cost_usd": null,
  "unblocks": [],
  "keywords": [
    "coverage",
    "group-d",
    "unattributed",
    "clustering",
    "items",
    "gimbal-bench",
    "evidence",
    "paths",
    "seed",
    "scaling"
  ],
  "evidence": [
    {
      "repo": "product-os",
      "paths": [
        "state/proposals/PROP-0003-*"
      ],
      "note": "PROP-0003 accepted and the items created; group D measurably reduced from 301 with the fraction stated."
    }
  ],
  "created": "2026-08-19",
  "updated": "2026-08-19"
}
---

Group D is a to-do list, not an error log. At the default window it is **301**
commits that no item claims, against **29** items — roughly 10% of the portfolio
modelled, with the missing 90% concentrated in `gimbal-bench`.

This is what blocks connecting more repos. **Coverage scales with items, not
repos.** Point the tool at five more today and each one adds to group D until
the one honest signal in the audit becomes something to scroll past.

## What was done

Clustered the 301 by path and by what the work actually was, into **20 proposed
items covering 288 — 96%**. Not created: `impact`, `confidence` and
`effort_minutes` are decided fields, so it is `PROP-0003`, answerable in one
sentence.

The glob set and the measurement live in `state/proposals/PROP-0003-clusters.py`
so the 96% is reproducible rather than asserted.

## Three things worth carrying forward

**13 commits are deliberately left uncovered and named** — a `.gitignore`
change, a one-off camera capture, a mobile presentation fix, and a tail of
reverts and asset regenerations. A coverage figure gamed by fake items is worse
than a low one.

**Part of the 301 was never a modelling gap.** Thirteen *existing* items are
suppressed by the too-broad check and so contribute their commits to D; `GB-001`
alone would claim 57. The suppression is right, but it means the number mixes
"nobody modelled this" with "the rule is too coarse to attribute". Those are
separate jobs and I did not merge them.

**The too-broad check does not apply to `done` items, and that is correct.** Its
purpose is to stop a *forward* claim silently absorbing a directory's future.
A finished workstream that produced 62 commits is described, not over-claimed,
by a glob matching 62. Verified in `audit_item()` rather than assumed — and two
genuine grab-bags were narrowed anyway.

## Handoffs

### 2026-08-19 · work-laptop
**Did:** the clustering and `PROP-0003`. Group D unchanged until he answers —
proposing items is where my authority stops.
**Next:** one sentence from him; then create the items and re-measure.
**Reached:** gimbal-bench, engineered-lighting-site, product-os ·
**Could not reach:** —
