---
{
  "id": "EL-002",
  "title": "The bench meter has no current range",
  "project": "robotic-spotlight",
  "status": "next",
  "lane": "hardware",
  "gate": "none",
  "machine_affinity": null,
  "impact": 3,
  "confidence": 4,
  "effort_minutes": 20,
  "cognitive_load": "low",
  "lead_time_days": 5,
  "cost_usd": 60.0,
  "unblocks": [],
  "unblocks_inferred": [],
  "answers": [],
  "keywords": [
    "meter",
    "multimeter",
    "tm-510",
    "current",
    "rail",
    "psu",
    "undervoltage",
    "12v",
    "latch",
    "instrument",
    "cp12",
    "watch-and-expect"
  ],
  "evidence": [
    {
      "repo": "gimbal-bench",
      "paths": [
        "captures/gimbal10/fixture/hw/**"
      ],
      "note": "A capture with a measured rail voltage in it, taken with an instrument rather than inferred from CAN behaviour."
    }
  ],
  "evidence_found": [
    {
      "kind": "commit",
      "repo": "engineered-lighting-site",
      "sha": "d8f092b",
      "date": "2026-08-17",
      "note": "Doc 4a names the bench meter (TESMEN TM-510) and states its limit: volts and ohms, no current range. Found by tools/audit.py in group D."
    }
  ],
  "repos": [
    "gimbal-bench",
    "engineered-lighting-site"
  ],
  "parent_ruling": null,
  "created": "2026-08-19",
  "updated": "2026-08-19"
}
---

**Rescoped 2026-08-19 by the first `/audit` run, and the correction is worth
more than the item.**

## What this item said yesterday, and why it was wrong

It said the bench had no instrument at all, citing `supply-state-20260814.md`:

> There is no instrument on this bench that measures rail voltage, and the CAN
> transport cannot distinguish *unpowered* from *disconnected*.

That was true on 2026-08-14 and **is not true now.** Doc 4a, committed
`d8f092b` on 2026-08-17 — three days later — photographs the bench meter and
names it:

> **CAUTION — two jacks, volts and ohms only. This meter has NO current range.**

A **TESMEN TM-510**. It reads volts. So the rail voltage question is answerable
today, and the item as written would have sent somebody shopping for a meter
that is already on the bench.

## What is actually still missing

A **current** range, and Doc 4a says exactly what that costs:

> this bench's meter has no current range, so they stand as *expectations* until
> a current-capable meter visits

The tape's per-zone current figures are therefore **derived from the spool's
watts-per-foot, not measured**, and CP12 — the first power-on of a zone — is a
*watch-and-expect* check rather than a reading. The mitigation is real and
stated: the wiring is protected by the fuse and by the supply's own overload
hiccup either way.

## Why this matters more than a meter

`R-023`: stage 1 sets a 2.0 A supply limit and stage 6 adds motors to the same
rail. The failure mode is a slew folding the rail toward 12 V, which is this
motor's undervoltage-latch line, which takes its CAN interface down until a
power cycle. **That is a current problem diagnosed with no current instrument.**

## Acceptance

A capture with a measured current in it. Not a derived expectation.

---

## Handoffs

### 2026-08-19 · work-laptop
**Did:** rescoped by `/audit`. The premise ("no instrument") was 3 days stale at
the moment it was written; the bench has a TM-510 that reads volts and ohms.
**Next:** decide whether a current-capable meter is worth buying now or whether
watch-and-expect carries to gate L. `cost_usd` is proposed, not set.
**Ruled out:** nothing new here — but see `R-054`, which is why this was missed.
**Reached:** engineered-lighting-site, gimbal-bench · **Could not reach:** —
