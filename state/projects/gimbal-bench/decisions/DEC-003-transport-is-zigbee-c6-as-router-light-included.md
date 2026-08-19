---
{
  "id": "DEC-003",
  "title": "Transport is Zigbee, C6 as router, light included",
  "project": "gimbal-bench",
  "status": "done",
  "ruling_id": "D3",
  "decided": "2026-08-14",
  "revisit_if": "The hub-dependency cost is judged unacceptable against the 'it stays a light' law, which this ruling puts in tension with itself (reader-planV2 §9.5, §15.5).",
  "supersedes": [],
  "superseded_by": null,
  "propagates_to": [
    {
      "repo": "engineered-lighting-site",
      "path": "docs/06-message-contract.md",
      "claim": "Lights ride ESPHome's native HA API; the aim and telemetry lanes ride MQTT topics. Both are the transport D3 retired."
    },
    {
      "repo": "engineered-lighting-site",
      "path": "docs/07-building-the-software.md",
      "claim": "The resolver reaches the fixture over the ESPHome native API with aioesphomeapi. That client is the retired transport."
    }
  ],
  "keywords": [
    "zigbee",
    "d3",
    "transport",
    "esphome",
    "mqtt",
    "native-api",
    "propagation",
    "doc6",
    "doc7"
  ],
  "evidence": [
    {
      "repo": "gimbal-bench",
      "path": "captures/gimbal10/fixture/authority-recon-20260815/reader-planV2.md",
      "sha": "89e9afc",
      "date": "2026-08-16",
      "note": "§5 ledger row D3, and the verbatim consequence cell in §6."
    },
    {
      "repo": "gimbal-bench",
      "path": "esphome/spot-bench.yaml",
      "sha": "d1cda80",
      "date": "2026-08-14",
      "note": "Carries the dated boundary: what D3 supersedes and what it does not."
    }
  ],
  "created": "2026-08-19",
  "updated": "2026-08-19"
}
---

> D3 | **Transport is Zigbee**, C6 as router, **light included**.
> — `reader-planV2.md` §5

**Scope, and this is the whole point of the entry.** `esphome/spot-bench.yaml`
is the only place anyone wrote down where D3's line falls, and it draws it in
two directions:

> SUPERSEDED BY D3, kept only so a working reference exists:
>   - wifi:, api:, mqtt:, and everything reached over them.

> STILL LIVE, and not superseded by anything:
>   - The Auto/Hold/Manual gate, the 2 s watchdog and its two-stage failsafe,
>     and the one-shot preset semantics. Those are BEHAVIOUR, not transport.

So the propagation this ruling licenses is **transport only**. Doc 6 §1's
watchdog, failsafe and preset semantics are not retired by D3 and must survive
SITE-001 intact — the same file that authorises the retirement says the
gimbal-10 firmware "does not have them yet", which makes deleting the record
strictly destructive.

D3's own cost, recorded because the source records it and it argues against
itself:

> **Illumination becomes hub-dependent.** §7's law says 'it stays a light.'…
> The plan's strongest safety law is undermined by its own transport decision

That is quoted in `reader-planV2.md` §6 from plan v2 §9.5.
