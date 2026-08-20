---
{
  "id": "SITE-001",
  "title": "Retire wifi:/api:/mqtt: as TRANSPORT in Docs 6 and 7",
  "project": "engineering-site",
  "status": "parked",
  "lane": "content",
  "gate": "none",
  "machine_affinity": null,
  "keywords": [
    "doc6",
    "doc7",
    "esphome",
    "mqtt",
    "native-api",
    "transport",
    "d3",
    "zigbee",
    "propagation",
    "stale"
  ],
  "evidence": [
    {
      "repo": "engineered-lighting-site",
      "paths": [
        "docs/06-message-contract.md",
        "docs/07-building-the-software.md"
      ],
      "note": "A commit that marks the transport lane historical in both docs while leaving the behaviour sections standing."
    }
  ],
  "evidence_found": [],
  "repos": [
    "engineered-lighting-site"
  ],
  "parent_ruling": "DEC-003",
  "created": "2026-08-19",
  "updated": "2026-08-20"
}
---

**Scope is the entire point of this item, and getting it wrong would delete a
record the engineering repo says must not be lost.**

Retire, because D3 supersedes them as *transport*:

- Doc 6's MQTT topic table and the native-API light lane. Line 28 today: *"they
  ride ESPHome's native HA API as normal light entities and never touch MQTT
  directly"*.
- Doc 7's resolver-to-fixture client (`aioesphomeapi`, `ReconnectLogic`).

**Explicit non-goal — do not touch:** Doc 6 §1's Auto/Hold/Manual gate, the 2 s
watchdog and its two-stage failsafe, and the one-shot preset semantics.
`spot-bench.yaml` marks exactly these:

> STILL LIVE, and not superseded by anything:
>   - The Auto/Hold/Manual gate, the 2 s watchdog and its two-stage failsafe,
>     and the one-shot preset semantics. Those are BEHAVIOUR, not transport.
>     Whatever carries the commands, a fixture still needs them, and the
>     gimbal-10 firmware does not have them yet.

The last clause is the operative one: the published doc is currently the only
written specification of behaviour the firmware has not implemented. Retiring it
would delete the requirement along with the transport.

**A word count is not a decision.** Doc 6 mentions ESPHome eleven times and
Zigbee once; Doc 7 mentions ESPHome twenty-four times and Zigbee not at all.
Those are counts. They tell you where to look, and they rule nothing.

This item rules nothing either. It is parented to DEC-003.
