---
name: next
description: Answer "what should I work on now" from the product-os backlog. Use when the user says /next, or asks what to work on, what is most important, or what they can start from this machine.
---

# next

**Read the top of `state/backlog.md` and hand him the kickoff prompt for it.**
That is the whole skill.

```bash
python3 tools/backlog.py            # his order, top first
python3 tools/kickoff.py <ID>       # the prompt to paste into a NEW chat
```

## The order is his. Do not derive one.

`state/backlog.md` is a file Marcelo wrote. Top is next. There is no score, no
leverage and no dependency graph — they were removed on 2026-08-20 (`DEC-202`)
after measurement showed **9 of 17 adjacent pairs sitting inside the 10% band
this repo's own rules say to escalate on.** The arithmetic was handing back more
than half its own decisions.

So: **if you find yourself weighing two tasks in your head, stop.** That is the
thing that was deleted, and doing it privately is worse than doing it in code,
because nobody can inspect it. Read the file. Take the top one.

If you think the order is wrong, **say so once, with the reason, then work on
what he put at the top.** Once — not as a preamble to doing it anyway. And never
edit `state/backlog.md`; reordering is his, and it is one edit he can make faster
than he can read your argument for it.

## Say the ID out loud

Open with the task ID — `GB-001`, `POS-009`, `Q-003`. Writing it into the chat is
what lets the thread indexer link this conversation to that work later, for free.
It costs one token and it is the cheapest thing in this system.

## Then check the machine

If the task carries a `machine_affinity` that is not this machine, **say so
first.** The honest answer is *"resume on `formd-t1`"*, not a plan that cannot be
executed from here. Offer him the next task that can be.

Gates are the same: `awaiting-parts`, `printer` and `external` need something
that may not be present.

## What not to do

- **Do not reorder the backlog**, and do not create a task. Item creation is his
  alone. What you think should exist goes to `state/recommendations/` — one
  sentence plus the commits and paths that made you think of it — and crosses
  into the backlog only when he adopts it.
- **Do not write his decided fields**: `project`, `gate`, `machine_affinity`,
  `parked`/`dropped`, or the `evidence` rule. Draft into `state/drafts/` with a
  diff against what is there.
- **Do not summarise the list into a recommendation of your own.** The file is
  the recommendation.

## If the backlog is empty

Say so. **That is a real state, not an error** — he authors every task and the
system never invents one, so an empty backlog means there is nothing to start
until he adds something. Offer to show him what the last audit recommended.
An empty answer with a reason is a good answer; an invented task is not.
