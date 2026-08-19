---
{
  "id": "GB-004",
  "title": "M6 on hardware: the motor-silent limb, MUTE-CLEAR, and the armed lane",
  "project": "gimbal-bench",
  "status": "next",
  "lane": "firmware",
  "gate": "bench",
  "machine_affinity": "formd-t1",
  "impact": 4,
  "confidence": 4,
  "effort_minutes": 180,
  "cognitive_load": "high",
  "lead_time_days": 0,
  "cost_usd": null,
  "unblocks": [],
  "unblocks_inferred": [],
  "answers": [],
  "keywords": [
    "m6",
    "mute",
    "mute-clear",
    "armed",
    "motor-silent",
    "bus-no-ack",
    "drill",
    "bench-session"
  ],
  "evidence": [
    {
      "repo": "gimbal-bench",
      "paths": [
        "captures/gimbal10/fixture/bench-session*.md",
        "captures/gimbal10/fixture/*mute*"
      ],
      "note": "A bench capture showing MUTE cause=motor-silent on the armed lane, and a MUTE-CLEAR, on real hardware."
    }
  ],
  "evidence_found": [
    {
      "kind": "commit",
      "repo": "gimbal-bench",
      "sha": "19dd790",
      "date": "2026-08-19",
      "note": "attributed by tools/audit.py on 2026-08-19"
    },
    {
      "kind": "commit",
      "repo": "gimbal-bench",
      "sha": "34b9f7c",
      "date": "2026-08-19",
      "note": "attributed by tools/audit.py on 2026-08-19"
    },
    {
      "kind": "commit",
      "repo": "gimbal-bench",
      "sha": "1525192",
      "date": "2026-08-19",
      "note": "attributed by tools/audit.py on 2026-08-19"
    },
    {
      "kind": "commit",
      "repo": "gimbal-bench",
      "sha": "7f5b060",
      "date": "2026-08-19",
      "note": "attributed by tools/audit.py on 2026-08-19"
    }
  ],
  "repos": [
    "gimbal-bench"
  ],
  "parent_ruling": "DEC-016",
  "created": "2026-08-19",
  "updated": "2026-08-19"
}
---

M6's mute machinery landed and flashed on 2026-08-15. One limb is proven live:

> proven live: `MUTE cause=bus-no-ack` at 2.3 s from boot

and the same paragraph names what is not:

> Still unproven on hardware: "the motor-silent limb, MUTE-CLEAR, the armed
> lane."

The 08-15 session tried and lost one of them to an unrelated reboot — the
board reset at PSU-on, so *"the standing 35-minute mute latch died with the
reboot instead of being cleared by first contact; MUTE-CLEAR's live proof moved
to S3."*

Worth carrying into the session: the P1 found in M6's first hour was invisible
to **538 tests, six review mutations, and two green gates, because nothing
offline transmits.** That is the argument for doing this at the bench rather
than adding another offline test.

---

## Handoffs

### 2026-08-19 · work-laptop
**Did:** `/audit` attributed four commits to this item by path. The one that
matters is `19dd790`, *"map the fall that never comes"* — a subject no keyword
rule could ever have linked to a mute drill. Reading it changes what this item
is:

- **motor-silent limb — PROVEN.** `MUTE motor-silent lane=safe` latched at 1.9 s,
  re-announced at 32 s.
- **MUTE-CLEAR — PROVEN.** Cleared on replug, and refused tilt's pose until
  re-verified.
- **armed lane — NOT reached, and the reason is structural, not a miss.**

The capture's own conclusion:

> the armed-lane mute resists physical-unplug drills — the pull's transient
> kills an armed frame before the mute can accrue.

What happened: the instant the connector was pulled, the transient cost an armed
PAN heartbeat its ACK, and the standing armed no-ACK law disarmed within one
frame. The capture's verdict on that is worth keeping —

> arguably the most correct thing the fixture did all day.

**Next:** the remaining limb needs a different method, and the capture names it:
the dev-gated reply-drop drill on the `+mutesim` image (verified built), as its
own short bench moment. Two thirds of this item is done; the last third is not a
retry, it is a different experiment.

**Ruled out:** proving the armed-lane mute by physically unplugging a connector.
It cannot work — see `R-055`.

**Refused:** `status: done`. Two of three limbs is not three. `apply.py` refused
it independently because the evidence had not been read before the run; both
refusals are correct and they are not the same refusal.

**Reached:** gimbal-bench · **Could not reach:** —
