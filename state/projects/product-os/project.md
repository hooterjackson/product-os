---
{
  "slug": "product-os",
  "name": "product-os",
  "prefix": "POS",
  "north_star": "Know what to work on next, and never be told progress that cannot be clicked.",
  "phase": "slice 1a-minus",
  "repos": [
    "product-os"
  ],
  "decision_authority": "product-os",
  "may_rule": true,
  "created": "2026-08-19",
  "updated": "2026-08-19"
}
---

This repo. The priority and context control plane.

It is deliberately the smallest project in the portfolio, because the failure it
is most likely to suffer is becoming the ninth hand-maintained state file in a
portfolio that already has eight. POS-002 exists specifically to guard against
that: the pointer from `PROJECT-STATE.md` into here is what stops the two files
drifting into disagreement about which one is real.
