---
{
  "id": "DEC-015",
  "title": "Zigbee stays parked until the fault ring and the drills are done",
  "project": "gimbal-bench",
  "status": "done",
  "ruling_id": "D15",
  "decided": "2026-08-14",
  "revisit_if": "The fault ring and the drills are done — the condition is in the ruling's own title, and it is modelled as GB-001 unblocking GB-005.",
  "supersedes": [],
  "superseded_by": null,
  "propagates_to": [
    {
      "repo": "engineered-lighting-site",
      "path": "docs/04-full-fixture-bench.md",
      "claim": "Doc 4's banner says the fixture's C6 now runs Arduino-based Zigbee firmware. gimbal-bench's README says the firmware has no Zigbee stack, OTA path, or concurrency mailbox yet."
    }
  ],
  "keywords": [
    "zigbee",
    "d15",
    "parked",
    "ota",
    "rollback",
    "fault-ring",
    "m5",
    "preemption",
    "esp-zb-task",
    "hub"
  ],
  "evidence": [
    {
      "repo": "gimbal-bench",
      "path": "captures/gimbal10/fixture/owner-decisions-20260814.md",
      "sha": "e4d71a9",
      "date": "2026-08-15",
      "note": "Full prose, D15, and the 'what none of these block' section naming M5 as the successor."
    },
    {
      "repo": "gimbal-bench",
      "path": "README.md",
      "sha": "9549189",
      "date": "2026-08-16",
      "note": "States twice at HEAD that Zigbee is parked and the phase unbuilt."
    }
  ],
  "created": "2026-08-19",
  "updated": "2026-08-19"
}
---

**Zigbee is ruled (D3) and parked (D15). Not dead, and not next.** Anyone
reading one of those two facts without the other will get the priority wrong in
one of two opposite directions, which is why both decisions are in this ledger.

The three parking costs, verbatim, because they are the argument:

> - **The radio interrupts the safety code.** `esp_zb_task` runs at priority 5
>   against the Arduino loop at priority 1 on a single-core chip. This firmware
>   is a flat cooperative superloop with zero mutexes, written on the assumption
>   that nothing preempts it.
> - **OTA is dangerous as built.** `verifyOta()` weak-returns true and the image
>   is marked valid before `setup()` runs a line…
> - **If the light is on Zigbee, no hub means no light** — which undercuts the
>   plan's own strongest rule, that whatever else fails, it stays a light.

D15 names its own successor, and this is the sentence that sets this
portfolio's next move:

> The fault ring (M5) needs nothing from any of them, and it is the next thing
> built.

**Un-parking is an owner decision that has not been taken.** No agent may take
it. The dependency edge GB-001 → GB-005 in this repo is the ruling's own
condition made mechanical; it is not permission.

Note also the sequencing inside the phase: when Zigbee does start, *"the OTA
rollback fix lands **first**, before anything else touches the radio."*
