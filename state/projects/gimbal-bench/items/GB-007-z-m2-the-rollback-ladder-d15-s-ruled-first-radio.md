---
{
  "id": "GB-007",
  "title": "Z-M2 — the rollback ladder, D15's ruled first radio commit",
  "project": "gimbal-bench",
  "status": "next",
  "lane": "firmware",
  "gate": "none",
  "machine_affinity": "formd-t1",
  "keywords": [
    "zigbee",
    "z-m2",
    "ota",
    "rollback",
    "c-patch",
    "mark-valid",
    "residual",
    "parked",
    "r2"
  ],
  "evidence": [
    {
      "repo": "gimbal-bench",
      "paths": [
        "sketches/gimbal/gimbal.ino",
        "tests/test_gimbal10_firmware.py"
      ],
      "note": "The mark-valid criterion modelled across synthetic boot states including residual-A and residual-B."
    }
  ],
  "evidence_found": [],
  "repos": [
    "gimbal-bench"
  ],
  "parent_ruling": "DEC-101",
  "created": "2026-08-19",
  "updated": "2026-08-20"
}
---

> **Z-M2** | **The rollback ladder (§8 — D15's ruled first radio commit)** —
> `verifyRollbackLater()→true`; mark-valid strictly on {`zigbeeJoined`,
> `twaiReady`, N iterations, no panic} (NOT readyBlocker terms);
> `ota_reboot_expected`; `joinWasWorking`; park-before-opt-in; **the c-patch
> signature check runs in the OUTGOING image before handoff**

Two orderings apply and they do not conflict, so both are recorded:

- **§6's build order** puts Z-M2 and Z-M3 as parallel siblings, both on Z-M1/Z-M0.
  That is the offline order and it is what `unblocks` encodes.
- **D15's ruling** says that when the phase starts, *"the OTA rollback fix lands
  **first**, before anything else touches the radio."* Z-M2 and Z-M3 are both
  offline milestones, so nothing here touches the radio either way — but the
  first thing that *does* must be this.

Why it matters, in D15's words: *"The rollback fix is one function and it is the
difference between a bad update being an annoyance and being a ladder-and-a-truck."*
