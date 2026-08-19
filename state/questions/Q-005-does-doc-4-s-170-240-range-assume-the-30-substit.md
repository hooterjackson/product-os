---
{
  "id": "Q-005",
  "title": "Does Doc 4's $170-240 range assume the $30 substitute, not the $486 spool?",
  "project": "engineering-site",
  "status": "next",
  "gates": [],
  "impact": 3,
  "confidence": 4,
  "effort_minutes": 30,
  "cognitive_load": "low",
  "lead_time_days": 0,
  "keywords": [
    "bom",
    "doc4",
    "cost",
    "valent-x",
    "btf",
    "fcob",
    "money",
    "arithmetic",
    "contradiction",
    "site"
  ],
  "evidence": [
    {
      "repo": "engineered-lighting-site",
      "path": "docs/bom-checklist.md",
      "sha": "88a3a58",
      "date": "2026-08-01",
      "note": "The Doc 4 header and row 4 of the same table."
    }
  ],
  "created": "2026-08-19",
  "updated": "2026-08-19"
}
---

Two numbers in the same table, live on the public site:

    Doc 4 header:  "Doc 4 · LED bench (~$170–240)"
    Row 4:         Diode LED Valent X Tunable White spool ......... $486

    $486  >  $240        by $246
    $486  −  $30  = $456  is the spread between the two readings

The row also names the alternative: a **BTF 24 V CCT FCOB** at about **$30**,
described as the "Budget bench substitute", with the caveats that it is
2-channel and has no 1800 K.

So the header is almost certainly costed against the $30 substitute — and **the
site never says so.** A reader following the BoM in order sees a $170–240 stage
and a $486 line item in it.

## Why this is a question and not a correction

Which tape the build actually wants is a product call with taste in it: the
Valent X is tunable across 1800K–6500K and the substitute is not, and this is a
*lighting* project. Nobody but the owner can rule it.

Once ruled, it produces two things: a site correction, and the real `cost_usd`
for EL-001, which currently carries the midpoint of a range that may be costed
against a part the build does not use.

**Escalated rather than resolved** — standing order: *"Escalate anything that
spends money."*
