---
{
  "provisional": true,
  "updated": "2026-08-18"
}
---

<!--
  PROVISIONAL. Drafted 2026-08-18 from decisions already visible in the repos.
  Edit freely; set "provisional": false when these are yours.

  The `[check: ...]` tail makes a rule machine-enforceable. Rules without a tail
  are advisory — a model reads them, code cannot enforce them, and validate.py
  will never claim they were checked.
-->

# Standing orders

Rules I have made once and want applied everywhere, without being asked again.

## Truth

- **NEVER mark an item done without evidence I can click.**
  `[check: evidence-required | fields: status | values: done]`
- **NEVER report "no changes" when you mean "I couldn't look."** Say which repos you
  reached and which you didn't, every time.
  `[check: coverage-line-required]`
- **ALWAYS `git fetch` before asking git what landed.** The local tracking ref has
  lied by 54 commits. If the fetch fails, say `⚠ unreachable` — never fall back.
  `[check: none]`
- **A published doc never overrides a ruling or current bench evidence.** When they
  disagree, the ruling wins and the doc gets a propagation item.
  `[check: none]`

## Evidence

- **NEVER retro-edit an evidence capture.** If a capture is wrong, supersede it by
  reference and leave the original standing. A reader who finds an edited file cannot
  tell what the original author actually wrote.
  `[check: none]`
- **Renders are not validation.** Boolean interference and measured STL volume are the
  check. OpenSCAD writing no file is the success signal.
  `[check: none]`
- **Measure before designing against a dimension.** Invented numbers have cost me a
  full frame revision. If a value is a guess, mark it a guess.
  `[check: none]`

## Money

- **Ordering is not spending.** Getting a long-lead part into the mail is cheap and
  reversible; waiting until I'm "ready" is what costs weeks. Rank the click, not the
  arrival.
  `[check: none]`
- **ALWAYS order the spare when a part has sold out on me once.**
  `[check: none]`
- **Escalate anything that spends money.** Show me both options, what each unblocks,
  what each does to the finish date, and then make a recommendation.
  `[check: escalate | fields: cost_usd | when: increase]`

## Scope

- **Half-finished work is worse than none.** If it doesn't fit the time I have, hand
  me something that does.
  `[check: none]`
- **Never hand me a debugging session after a long workday.** Match cognitive load to
  the energy I said I have.
  `[check: none]`

## Captured

<!-- /handoff and /audit append here when I say a decision is a standing order,
     not a one-off. Each entry carries the date, the proposal it came from, and my
     own words. A suggested [check:] tail is offered — never applied silently. -->
