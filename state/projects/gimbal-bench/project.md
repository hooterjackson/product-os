---
{
  "slug": "gimbal-bench",
  "name": "Gimbal bench",
  "prefix": "GB",
  "description": "Firmware and a commissioning bench that can prove, from a record, that the fixture stays a light.",
  "phase": "M5 fault ring layers one and two measured; Zigbee parked (D15)",
  "repos": [
    "gimbal-bench"
  ],
  "decision_authority": "gimbal-bench",
  "may_rule": true,
  "created": "2026-08-19",
  "updated": "2026-08-20"
}
---

**The authority repo.** It holds the decision ledger — the D-series owner
rulings and the R-series trust rulings — and every bench capture. When a
published document and a ruling disagree, the ruling wins and the document gets
a propagation item.

Two properties of this repo are worth knowing before working in it:

- It **overturns its own rulings when a review earns it.** R2 went `c-boot` →
  `c-patch` on 2026-08-15, the same day, because c-boot "defers the mark-valid
  decision into the sketch of the **freshly-booted, possibly-hostile image**"
  (`docs/ZIGBEE-PHASE-PLAN.md` §0, `5a9bfbd`).
- **Part of the ledger is not in it.** D1–D11 exist here only as one-line
  digests in `reader-planV2.md` §5; the full prose lives in a plan file under
  the owner's `.claude/plans/` on `formd-t1`, uncommitted. That is GB-003.

Private. Publication is authorized but blocked — see `wiki/ruled-out.md`.
