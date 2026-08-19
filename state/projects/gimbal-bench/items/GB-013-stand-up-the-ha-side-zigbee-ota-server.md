---
{
  "id": "GB-013",
  "title": "Stand up the HA-side Zigbee OTA server",
  "project": "gimbal-bench",
  "status": "next",
  "lane": "infra",
  "gate": "none",
  "machine_affinity": null,
  "impact": 3,
  "confidence": 3,
  "effort_minutes": 480,
  "cognitive_load": "medium",
  "lead_time_days": 0,
  "cost_usd": null,
  "unblocks": [
    "GB-012"
  ],
  "unblocks_inferred": [],
  "answers": [],
  "keywords": [
    "ota",
    "zigbee",
    "z2m",
    "zha",
    "provider",
    "image-index",
    "signer",
    "gate-l",
    "home-assistant"
  ],
  "evidence": [
    {
      "repo": "gimbal-bench",
      "paths": [
        "tools/**"
      ],
      "note": "An OTA provider reachable from the coordinator, an image index, and a signer-to-server pipeline that produced one signed image."
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

The second of §5's two stated gate-L prerequisites:

> the **HA-side Zigbee OTA server** (Z2M/ZHA OTA provider + image index + the
> signer→server pipeline — the OTA drill presupposes it)

`gate: none` and no `machine_affinity`: this is Home Assistant-side work, not
bench work, and the HA install already exists. It is the one item in the Zigbee
neighbourhood that can genuinely be started without `formd-t1`.

It is **not** blocked by GB-001. The park in D15 is about touching the radio in
the firmware; standing up a server does not. Drawing that edge would have been
tidy and wrong.
