---
{
  "id": "GB-005",
  "title": "Z-M1 — variant, partitions and the c-patch signing scaffold",
  "project": "gimbal-bench",
  "status": "next",
  "lane": "firmware",
  "gate": "none",
  "machine_affinity": "formd-t1",
  "impact": 4,
  "confidence": 3,
  "effort_minutes": 480,
  "cognitive_load": "high",
  "lead_time_days": 0,
  "cost_usd": null,
  "unblocks": [
    "GB-006",
    "GB-007"
  ],
  "unblocks_inferred": [],
  "answers": [],
  "keywords": [
    "zigbee",
    "z-m1",
    "variant",
    "partitions",
    "signing",
    "c-patch",
    "mega-gate",
    "parked"
  ],
  "evidence": [
    {
      "repo": "gimbal-bench",
      "paths": [
        "tools/mega_gate.py",
        "sketches/gimbal/gimbal.ino",
        "partitions*"
      ],
      "note": "All 7 mega_gate legs green including gimbal-10+deployed+zigbee, and a signer emitting a verifiable signature."
    }
  ],
  "evidence_found": [],
  "repos": [
    "gimbal-bench"
  ],
  "parent_ruling": "DEC-015",
  "created": "2026-08-19",
  "updated": "2026-08-19"
}
---

> **Z-M1** | **Variant + partitions + signing scaffold** — `GIMBAL_ZIGBEE`
> dependent flag + compound suffix + `#error` + the 7th mega_gate leg (flight
> image); `zigbee_zczr`; the c-patch build-time signer + the verify-before-handoff
> scaffold. **No Zigbee code yet.**

The head of the Zigbee chain, and the order is a correction the plan makes about
itself: *"Order corrected [§10 hole 4]: Z-M1 (the variant) precedes Z-M0 (code
behind it)."*

**Blocked by GB-001 by ruling, not by code.** D15: *"Zigbee stays parked until
the fault ring and the drills are done."* Nothing here touches the radio —
§6 is headed "Agent-side milestones (offline, reviewed, mega_gate green, no
radio)" — but the phase as a whole is parked, and this is its first commit.

`gate: none` is correct and worth defending: this is offline code work. What it
needs is the *checkout*, which lives on `formd-t1`.
