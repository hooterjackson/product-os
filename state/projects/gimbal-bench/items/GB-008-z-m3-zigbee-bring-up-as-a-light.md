---
{
  "id": "GB-008",
  "title": "Bring the fixture up on the radio and prove it still behaves like a light (Z-M3)",
  "project": "gimbal-bench",
  "status": "next",
  "lane": "firmware",
  "gate": "none",
  "machine_affinity": "formd-t1",
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
  "updated": "2026-08-23"
}
---

> **Z-M3** | **Zigbee bring-up AS A LIGHT** — router join (`zczr`),
> on/off/level clusters, the APSDE filter (stage-E record, TC source-bind),
> telemetry shell. Greenfield bulk.

The fan-out point: §6 states *"Z-M4/Z-M5/Z-M6 on Z-M3"*, which is where three of
this chain's four leaves attach.

**The relationship to GB-012 (gate L) is an inference, and no source states
it.** What the sources state is that gate L means *"the fixture joins and holds
as a light"* and that Z-M3 is bring-up as a light — which makes the connection
obvious to a reader and still an inference. It was modelled as an edge until
2026-08-20; the edges are gone (`DEC-202`), so this is recorded here as what it
always was: a reading, not a citation. Do not treat it as a prerequisite
without checking.
