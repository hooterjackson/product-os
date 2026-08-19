---
{
  "id": "DEC-012",
  "title": "The dead-man switch is retired, not replaced: position commands only",
  "project": "gimbal-bench",
  "status": "done",
  "ruling_id": "D12",
  "decided": "2026-08-14",
  "revisit_if": "Goal 3 deploys velocity commands (0xA2), which reopens the 400 ms lease branch with its own design.",
  "supersedes": [],
  "superseded_by": null,
  "propagates_to": [],
  "keywords": [
    "dead-man",
    "d12",
    "position",
    "goto",
    "safety",
    "liveness",
    "follow",
    "broadway"
  ],
  "evidence": [
    {
      "repo": "gimbal-bench",
      "path": "captures/gimbal10/fixture/owner-decisions-20260814.md",
      "sha": "e4d71a9",
      "date": "2026-08-15",
      "note": "Full prose, D12."
    }
  ],
  "created": "2026-08-19",
  "updated": "2026-08-19"
}
---

> The deployed fixture accepts *"go to this exact position"* and never
> *"keep moving in this direction."*

The reasoning is worth keeping in front of anyone touching motion code, because
it reframes a missing mechanism as an existing one:

> The safety value of a position command is not the position — it is that
> **every command carries its own ending**.

And the note about how it was found, which is the most useful sentence in the
file for anyone auditing this system's own claims:

> Plan v2 §1 records that *"self-terminating" appears nowhere in the firmware*,
> which was read at the time as a weakness. It is the opposite: the terminating
> machinery is there, it simply had no name.

The open sub-question this ruling leaves behind is Q-002, and D12 states plainly
that it is a measurement rather than an argument.
