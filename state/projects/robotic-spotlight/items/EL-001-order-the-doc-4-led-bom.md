---
{
  "id": "EL-001",
  "title": "Order the Doc 4 LED BoM",
  "project": "robotic-spotlight",
  "status": "next",
  "lane": "hardware",
  "gate": "none",
  "machine_affinity": null,
  "impact": 4,
  "confidence": 4,
  "effort_minutes": 20,
  "cognitive_load": "low",
  "lead_time_days": 14,
  "cost_usd": 205.0,
  "unblocks": [
    "GB-012"
  ],
  "unblocks_inferred": [],
  "answers": [],
  "keywords": [
    "led",
    "bom",
    "doc4",
    "order",
    "purchase",
    "valent-x",
    "btf",
    "fcob",
    "picobuck",
    "star",
    "gate-l",
    "lead-time"
  ],
  "evidence": [
    {
      "repo": "engineered-lighting-site",
      "paths": [
        "docs/bom-checklist.md"
      ],
      "note": "A dated note that the order was placed, plus arrival. Ordering is the completion here; arrival is the downstream item's."
    }
  ],
  "evidence_found": [],
  "repos": [
    "engineered-lighting-site"
  ],
  "parent_ruling": null,
  "created": "2026-08-19",
  "updated": "2026-08-19"
}
---

**Twenty minutes of clicking, and it is a hard prerequisite for a gate that is
otherwise pure firmware work.**

`ZIGBEE-PHASE-PLAN.md` §5 lists it as one of two gate-L prerequisites, and says
why in a phrase worth keeping:

> the **LED photometric path** (GPIO10/11/18 ledc — "join as a light" cannot be
> demonstrated as a *light* without it; today compile-only)

`PROJECT-STATE.md` at HEAD still reads *"Doc 4 (LED bench) and Doc 5 (camera)
BoMs unordered."* That file was last committed 2026-08-01, so the claim is old —
but nothing in either repo since says it was ordered, and this item's evidence
rule is what will settle it rather than a memory.

## The cost figure is contested, and Q-005 is why

`cost_usd: 205` is the midpoint of the site's own published header —
*"Doc 4 · LED bench (~$170–240)"* — and that header **cannot be right for the
build the same table specifies.** Row 4 of that table prices the Valent X spool
at **$486** on its own. $486 alone exceeds the top of a $170–240 range for the
whole stage.

The same row names a **$30 BTF 24 V CCT FCOB** as the "budget bench substitute".
That is almost certainly what the range assumes — and the site never says so.
Q-005 exists to settle it before money moves, because the two readings differ by
about $456.

**This item is not blocked by Q-005.** No source draws that edge, and most of
the BoM is unaffected by which tape is chosen. But do not click "buy" on the
tape row without reading Q-005 first.

## Why gate `none` and not `awaiting-parts`

`awaiting-parts` on a purchase gates the *buy* on the *arrival*, which is the
exact inversion this score's urgency term exists to prevent. The waiting belongs
to GB-012, downstream. Standing order: *"Ordering is not spending… Rank the
click, not the arrival."*
