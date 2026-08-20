---
{
  "id": "GB-009",
  "title": "Z-M4 — commissioning gesture and the reset-call choice",
  "project": "gimbal-bench",
  "status": "next",
  "lane": "firmware",
  "gate": "none",
  "machine_affinity": "formd-t1",
  "keywords": [
    "zigbee",
    "z-m4",
    "commissioning",
    "gesture",
    "nvs",
    "power-on",
    "breadcrumb",
    "parked"
  ],
  "evidence": [
    {
      "repo": "gimbal-bench",
      "paths": [
        "sketches/gimbal/gimbal.ino"
      ],
      "note": "Counter model over synthetic boots: 3 power-ons arm; a software reset never advances it; sub-2 s inert; >20 s resets."
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

> **Z-M4** | **Commissioning gesture + reset-call** — power-on-only counter in
> app-NVS, breadcrumbs, confirm-blink; the F-A5 reset-call choice explicit.

A leaf of the chain, on Z-M3 per §6. The residual fork F-A5 (which reset call)
is listed in §2 as inherited and unresolved, which is why `confidence` is
proposed at 3 rather than 4.
