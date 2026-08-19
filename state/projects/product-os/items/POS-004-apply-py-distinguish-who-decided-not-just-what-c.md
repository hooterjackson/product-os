---
{
  "id": "POS-004",
  "title": "apply.py: distinguish who decided, not just what changed",
  "project": "product-os",
  "status": "done",
  "lane": "infra",
  "gate": "none",
  "machine_affinity": null,
  "impact": 4,
  "confidence": 4,
  "effort_minutes": 90,
  "cognitive_load": "high",
  "lead_time_days": 0,
  "cost_usd": null,
  "unblocks": [],
  "keywords": [
    "authority",
    "origin",
    "apply",
    "decided",
    "human",
    "agent",
    "proposal",
    "guard",
    "truth",
    "said"
  ],
  "evidence": [],
  "evidence_found": [
    {
      "kind": "file",
      "repo": "product-os",
      "path": "tools/apply.py",
      "date": "2026-08-19",
      "note": "--decided/--field origin split; --decided requires --said (exit 2 without); every applied line stamped on-his-word or inferred."
    },
    {
      "kind": "file",
      "repo": "product-os",
      "path": "tests/test_regressions.py",
      "date": "2026-08-19",
      "note": "AuthorityGuardFiresAtTheAgentNotTheOwner: 8 assertions. 29 tests total, green."
    },
    {
      "kind": "file",
      "repo": "product-os",
      "path": "plugin/skills/audit/SKILL.md",
      "date": "2026-08-19",
      "note": "Sections 5 and 6 teach the field/decided split and the two non-bending truth guards."
    }
  ],
  "created": "2026-08-19",
  "updated": "2026-08-19",
  "completed": "2026-08-19"
}
---

**The authority guard was firing at the wrong person.**

Reproduced before it was touched:

```
$ python3 tools/apply.py --dry-run --field EL-001=cost_usd:486 \
    --said "the tape is the Valent X, cost is 486"

proposed  EL-001  cost_usd — `cost_usd` is human-authority. Proposed, not written.
```

Marcelo states a fact about his own build, in his own words, and the tool files
a proposal **for him to approve later.** It routed his decision into a queue
addressed to himself.

## Two guards, conflated

- **Authority** — *who decided this?* Exists to stop the **agent** silently
  reprioritising. Never meant to stop the owner deciding. Yields to his word.
- **Truth** — *is this provable?* `done` without `evidence_found` is refused for
  **everyone**, him included. Does not bend, and did not.

`apply.py` had `--said` all along and never read it.

## How origin is carried, and why not `--said` alone

`--said` was the obvious signal and it is not good enough: **an agent can
populate `--said` too.** So the origin lives in the flag name, where it is a
claim rather than an inference:

    --field    ID=FIELD:JSON   the agent inferred it -> decided fields PROPOSE
    --decided  ID=FIELD:JSON   he said it            -> APPLIES. Requires --said.

Three properties this buys:

1. **Agent is the default.** Forgetting to state origin fails toward proposing.
2. **`--decided` without `--said` is a hard exit 2.** An unattributed human
   decision is indistinguishable from an agent writing what it likes.
3. **The audit entry stamps every applied line** `on his word` or `inferred`, so
   a decision and a guess never blur after the fact.

## Acceptance

Five behaviours, all verified:

| | |
|---|---|
| he states `cost_usd` | **applies**, stamped `on his word` |
| agent infers `cost_usd` | **proposes** |
| he says `done`, no evidence | **REFUSED** — truth guard held |
| `--decided` with no `--said` | **exit 2** |
| he says `parked` | **applies**; agent saying it still proposes |

8 assertions added; 29 tests total, gate green.

## Handoffs

### 2026-08-19 · work-laptop
**Did:** the origin split, the tests, and §5/§6 of the `/audit` skill.
**Also fixed:** §7 of that skill still taught `EL-001` as the live lead-time
example — the item found already-bought the session before. Replaced with the
mechanism, plus a warning to argue for the mechanism and never for a specific
item's number.
**Next:** Marcelo uses the loop for real. Every friction that surfaces is a real
requirement instead of a guessed one.
**Reached:** product-os · **Could not reach:** —
