---
{
  "id": "GB-010",
  "title": "Z-M5 — the deployed §4.1 motion predicate",
  "project": "gimbal-bench",
  "status": "next",
  "lane": "firmware",
  "gate": "none",
  "machine_affinity": "formd-t1",
  "keywords": [
    "zigbee",
    "z-m5",
    "predicate",
    "command-authenticated",
    "refusal",
    "gate-a",
    "anchors",
    "parked"
  ],
  "evidence": [
    {
      "repo": "gimbal-bench",
      "paths": [
        "tools/check_anchors.py",
        "tools/bench_ui/serial_bridge.py",
        "tools/bench_ui/test_parser.py"
      ],
      "note": "check_anchors both-ways green, a test_parser case, and a FirmwareSourceContract literal pin."
    }
  ],
  "evidence_found": [],
  "repos": [
    "gimbal-bench"
  ],
  "parent_ruling": "DEC-015",
  "created": "2026-08-19",
  "updated": "2026-08-20"
}
---

> **Z-M5** | **The deployed §4.1 motion predicate + `command_unauthenticated`**
> — realize the authority §4.1 predicate as the deployed+zigbee gate…; the new
> cause through the **atomic** four-link chain; `ota_in_progress` gets its OWN
> chain.

This is the one Z-milestone gate A explicitly names: *"Under R1(a), gate A needs
the Multistate aim cluster, the §4.1 predicate (Z-M5), and the fork closures"*.

Q-001 gates it — Spot Mode's survival is a gate-A product question and this is
the gate-A predicate.

Collision warning worth carrying, from §9: Z-M5 edits `serial_bridge.py`'s
`REFUSAL_CAUSES`, `check_anchors.py` pairs and `test_parser.py`, and a
concurrent agent's work touches the same vocabulary. **Land each four-link
vocabulary change atomically in one commit.**
