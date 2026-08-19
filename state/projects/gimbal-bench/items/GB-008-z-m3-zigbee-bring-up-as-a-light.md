---
{
  "id": "GB-008",
  "title": "Z-M3 — Zigbee bring-up as a light",
  "project": "gimbal-bench",
  "status": "next",
  "lane": "firmware",
  "gate": "none",
  "machine_affinity": "formd-t1",
  "impact": 4,
  "confidence": 3,
  "effort_minutes": 960,
  "cognitive_load": "high",
  "lead_time_days": 0,
  "cost_usd": null,
  "unblocks": [
    "GB-009",
    "GB-010",
    "GB-011"
  ],
  "unblocks_inferred": [
    "GB-012"
  ],
  "answers": [],
  "keywords": [
    "zigbee",
    "z-m3",
    "join",
    "zczr",
    "router",
    "on-off",
    "level",
    "apsde",
    "parked",
    "gate-l"
  ],
  "evidence": [
    {
      "repo": "gimbal-bench",
      "paths": [
        "sketches/gimbal/gimbal.ino"
      ],
      "note": "Compiles, and an APSDE filter model that admits TC on/off and swallows-and-counts foreign and aim writes."
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

> **Z-M3** | **Zigbee bring-up AS A LIGHT** — router join (`zczr`),
> on/off/level clusters, the APSDE filter (stage-E record, TC source-bind),
> telemetry shell. Greenfield bulk.

The fan-out point: §6 states *"Z-M4/Z-M5/Z-M6 on Z-M3"*, which is where three of
this chain's four leaves attach.

**The edge to GB-012 (gate L) is `unblocks_inferred`, not `unblocks`.** No source
states it. What the sources state is that gate L means *"the fixture joins and
holds as a light"* and that Z-M3 is bring-up as a light — which makes the edge
obvious to a reader and still an inference. Inferred edges are excluded from
leverage and never force `blocked`, so nothing in the ranking rests on my
reading of it.
