---
{
  "id": "EL-001",
  "title": "Order the Doc 4 LED BoM",
  "project": "robotic-spotlight",
  "status": "parked",
  "lane": "hardware",
  "gate": "none",
  "machine_affinity": null,
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
  "evidence_found": [
    {
      "kind": "commit",
      "repo": "engineered-lighting-site",
      "sha": "762afdd",
      "date": "2026-08-19",
      "note": "attributed by tools/audit.py on 2026-08-19"
    },
    {
      "kind": "commit",
      "repo": "engineered-lighting-site",
      "sha": "d8f092b",
      "date": "2026-08-19",
      "note": "attributed by tools/audit.py on 2026-08-19"
    },
    {
      "kind": "commit",
      "repo": "engineered-lighting-site",
      "sha": "2c1233f",
      "date": "2026-08-19",
      "note": "attributed by tools/audit.py on 2026-08-19"
    },
    {
      "kind": "commit",
      "repo": "engineered-lighting-site",
      "sha": "52c5048",
      "date": "2026-08-19",
      "note": "attributed by tools/audit.py on 2026-08-19"
    }
  ],
  "repos": [
    "engineered-lighting-site"
  ],
  "parent_ruling": null,
  "created": "2026-08-19",
  "updated": "2026-08-20"
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

---

## Handoffs

### 2026-08-19 · work-laptop — found wrong by the cold-start test
**Did:** nothing was ordered by me. What changed is what this item is understood
to be.

**This item's evidence rule could never fire.** It named only
`docs/bom-checklist.md`, which says of itself *"state persists in your browser
(nothing leaves your device)"*. Ticking every box writes nothing to the repo, so
no purchase could ever satisfy the rule — and this item has been ranked #1 in
the portfolio since the seed, on a rule that was structurally incapable of
closing it.

Meanwhile `docs/04a-wire-the-zones.md` photographs the parts on the bench: the
PSU, the PCA9685, the ULN2803, the buck, the fuse kit, the WAGOs, the wire, the
tape pads. And line 179 reads the PicoBuck's chips off the unit itself —
*"this unit's chips read AL8860"*. You cannot read a part number off a part you
have not bought.

**Next:** `PROP-0002` proposes repointing the rule at Doc 4a and reducing this
item to its residual. **The residual is the Carclo 10507 optics trio**, which is
unphotographed and unmentioned — Doc 4a says *"Set it aside until spotlight
day."* Not closed, and deliberately not retitled: narrowing scope is a decision
with taste in it.

**Not verified, and not mine:** which tape was bought. The 1800 K channel
implies Valent X, but that is an inference from a spec rather than a photograph
— which is precisely the reasoning `CLAUDE.md` opens by warning about. Q-005
stays open.

**Ruled out:** browser-local state as a repo evidence rule — `R-056`.

**Reached:** engineered-lighting-site, gimbal-bench · **Could not reach:** —
