---
{
  "id": "DEC-101",
  "title": "R2 = c-patch: the outgoing image verifies the new one before handoff",
  "project": "gimbal-bench",
  "status": "done",
  "ruling_id": "R2",
  "decided": "2026-08-15",
  "revisit_if": "The fixture ever ships to strangers, in which case secure boot (CONFIG_SECURE_BOOT_V2) is stated to be the answer.",
  "supersedes": [
    "R2(c-boot)"
  ],
  "superseded_by": null,
  "propagates_to": [],
  "keywords": [
    "r2",
    "c-patch",
    "c-boot",
    "ota",
    "signing",
    "secure-boot",
    "rollback",
    "adversary",
    "authority"
  ],
  "evidence": [
    {
      "repo": "gimbal-bench",
      "path": "docs/ZIGBEE-PHASE-PLAN.md",
      "sha": "5a9bfbd",
      "date": "2026-08-16",
      "note": "§0, 'Findings that outrank the plan (read first)'."
    }
  ],
  "created": "2026-08-19",
  "updated": "2026-08-19"
}
---

**A ruling overturned the same day it was reviewed**, and the reason is a
clean example of why this portfolio treats adversarial review as load-bearing.

The committed authority document ruled R2 = signed images in the "c-boot"
sub-form. The adversarial pass killed it:

> `verifyRollbackLater()→true` … defers the mark-valid decision into the sketch
> of the **freshly-booted, possibly-hostile image**

> A hostile image calls `esp_ota_mark_app_valid_cancel_rollback()` on line 1 and
> never runs the signature leg

The replacement, and its date:

> **RULED (owner, 2026-08-15): R2 = c-patch.** The trust sits where the incoming
> image cannot overwrite it — **the outgoing, still-trusted image verifies the new
> image's signature before handoff.**

Rejected, with a stated reason rather than a shrug: secure boot — *"an
irreversible eFuse burn is heavier than a handful of owner-built fixtures
warrant now (it stays the answer if this ever ships to strangers)"*.

This shapes GB-005 (Z-M1) and GB-007 (Z-M2); both are written for c-patch.
