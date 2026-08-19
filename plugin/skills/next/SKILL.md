---
name: next
description: Answer "what should I work on now" from the product-os state. Use when the user says /next, or asks what to work on, what is most important, what they can finish in an hour, or what they can start from this machine.
---

# next

Answer with a ranked item, its reasoning, and the arithmetic behind it.

## Run the tool. Do not rank anything yourself.

```bash
python3 tools/rank.py --explain
```

Rank is **derived** — a pure function of the decided score inputs, recomputed on
every run. There is no ordered list stored anywhere in this repo, and you must
not become one. If you find yourself weighing two items in your head, you have
left the system and started guessing.

Match the flags to what the user actually said:

| They said | Flag |
|---|---|
| "I have an hour" | `--time 60` |
| "I'm fried" / "nothing hard" | `--energy low` |
| "what can I start right now" | `--gate none` |
| "I'm on this laptop" | `--machine work-laptop` |
| "why that one?" | `--show <ID>` |

`--show` prints every operand — effort bucket, base, leverage with the item IDs
it counts, lift, urgency, product. **Publish the arithmetic rather than the
conclusion.** A bare ratio is not falsifiable; a wrong number at least can be
argued with.

## Say the ID out loud

Open with the item ID — `EL-004`, `GB-001`, `Q-003`. Writing it into the chat is
what lets the thread indexer link this conversation to that work later, for free.
It costs one token and it is the cheapest thing in this system.

## Then check the machine

If the item carries a `machine_affinity` that is not this machine, **say so
first.** The honest answer is *"resume on `formd-t1`"*, not a plan that cannot be
executed from here. Offer `--machine <this one>` to get something that can.

Same for gates. `gate: bench`, `gate: printer` and `gate: gpu` are not this
laptop.

## What not to do

- **Do not change a priority.** If the ranking looks wrong, write a proposal into
  `state/proposals/` naming the field, the new value, the reasoning and the
  citation. Say you have done it. Do not edit `impact`, `confidence`,
  `effort_minutes`, `lead_time_days`, `cost_usd`, `unblocks`, `pin`, `gate` or
  `project`.
- **Do not offer a blocked item** without saying what blocks it. `rank.py` hides
  blocked items; `--all` shows them.
- **Do not summarise the list into a recommendation of your own.** The list is
  the recommendation.

## If nothing is startable

`rank.py` says so and counts what is blocked. Report that plainly and name the
blockers. An empty answer with a reason is a good answer; an invented task is not.
