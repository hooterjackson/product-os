---
{
  "id": "EL-003",
  "title": "Print the tolerance coupon, then the fit coupon",
  "project": "robotic-spotlight",
  "status": "next",
  "lane": "hardware",
  "gate": "printer",
  "machine_affinity": null,
  "impact": 3,
  "confidence": 4,
  "effort_minutes": 120,
  "cognitive_load": "low",
  "lead_time_days": 0,
  "cost_usd": null,
  "unblocks": [],
  "unblocks_inferred": [],
  "answers": [],
  "keywords": [
    "print",
    "coupon",
    "tol-coupon",
    "fit-coupon",
    "petg",
    "frame",
    "scad",
    "tolerance",
    "bambu"
  ],
  "evidence": [
    {
      "repo": "engineered-lighting-site",
      "paths": [
        "docs/cad/frame.scad",
        "docs/03b-print-the-frame.md"
      ],
      "note": "A dated note recording the measured coupon fit and the clearance value it produced."
    }
  ],
  "evidence_found": [],
  "repos": [
    "engineered-lighting-site"
  ],
  "parent_ruling": null,
  "created": "2026-08-19",
  "updated": "2026-08-19"
}
---

Doc 3b's coupon-first workflow: measure the printer before printing the part.
`db41f3f` added Doc 3b plus `docs/cad/frame.scad` as *"parametric scaffold + fit
coupon"*, and both coupons render today
(`docs/cad/renders/part-tol_coupon.png`, `part-fit_coupon.png`).

The reason this is a separate, cheap, low-load item rather than a step inside
"print the frame" is the standing order it serves: *"Measure before designing
against a dimension. Invented numbers have cost me a full frame revision."*

`gate: printer` — the Bambu X1C is not this laptop.
