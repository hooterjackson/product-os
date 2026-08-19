---
{
  "id": "GB-011",
  "title": "Z-M6 — telemetry attributes and the chunked dump",
  "project": "gimbal-bench",
  "status": "next",
  "lane": "firmware",
  "gate": "none",
  "machine_affinity": "formd-t1",
  "impact": 3,
  "confidence": 3,
  "effort_minutes": 480,
  "cognitive_load": "high",
  "lead_time_days": 0,
  "cost_usd": null,
  "unblocks": [],
  "unblocks_inferred": [],
  "answers": [],
  "keywords": [
    "zigbee",
    "z-m6",
    "telemetry",
    "attributes",
    "dump",
    "ring",
    "snapshotseq",
    "parked"
  ],
  "evidence": [
    {
      "repo": "gimbal-bench",
      "paths": [
        "sketches/gimbal/gimbal.ino"
      ],
      "note": "Encoding tested and snapshotSeq torn-read detection."
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

> **Z-M6** | **Telemetry attributes + chunked dump over Zigbee** — the §9
> attribute set + RTC-ring dump; `snapshotSeq`.

The remote read of the M5 fault ring — which is the thing D15 says is missing
today:

> Every recovery behaviour added on 2026-08-14 is currently observable only by
> somebody watching a serial port — which is the one state a deployed fixture is
> never in.

Also the place D3's named loss lands: the 1 Hz `spotlight/state` JSON becomes N
attributes arriving at different times, and `spot-bench.yaml` calls losing
**snapshot consistency** *"worse than losing rate"* — *"Named as a real loss, not
a migration detail."*
