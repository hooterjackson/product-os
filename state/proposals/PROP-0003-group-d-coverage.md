# PROP-0003 — 20 items to cover group D

**Status:** open. Nothing here has been created.
**Raised:** 2026-08-19, work-laptop, from `POS-006`.
**Answer in one sentence.** See *The one-sentence answer* below — the numbers are
inert, so "yes to all" is a safe answer and I have made it the easy one.

---

## The problem, measured

The system models **29 items** against **301 unattributed commits** in the
45-day window. Roughly 10% of the portfolio is described; the missing 90% is
concentrated in `gimbal-bench`, the most active repo there is.

This is what blocks pointing the tool at more repos. Coverage scales with
**items**, not repos: add five repos today and each adds to group D, until the
one honest signal in the audit — *"I recognised nothing here"* — becomes a
number that gets scrolled past.

## What these 20 items would cover

**288 of 301 — 96%.** Before: 301 unattributed. After: 13.

| id | repo | title | commits |
|---|---|---|---|
| GB-015 | gimbal-bench | Bench console UI: the operator-facing rebuild | 62 |
| GB-016 | gimbal-bench | Bench console server and serial bridge | 79 |
| GB-017 | gimbal-bench | Console contract, parser and lane tests | 68 |
| GB-018 | gimbal-bench | mega_gate: the seven-leg offline gate and its sweeps | 78 |
| GB-019 | gimbal-bench | gimbal-10 firmware: SAFE, stop and mute lanes | 56 |
| GB-020 | gimbal-bench | Firmware state-model tests | 42 |
| GB-021 | gimbal-bench | Motion campaign and capture tooling | 2 |
| GB-022 | gimbal-bench | Vision harness and camera qualification | 17 |
| GB-023 | gimbal-bench | Wire suite, bus evidence and anchor checking | 45 |
| GB-024 | gimbal-bench | Planning prompts and design documents | 58 |
| GB-025 | gimbal-bench | G-series offline release evidence | 3 |
| GB-026 | gimbal-bench | UI-overhaul milestone captures | 29 |
| GB-027 | gimbal-bench | Product-aim and group-product runtime | 3 |
| GB-028 | gimbal-bench | Commissioning and probe scripts | 48 |
| GB-029 | gimbal-bench | Fixture bench-session and hardware captures | 52 |
| SITE-004 | engineered-lighting-site | Doc 4a: the connector-level companion | 6 |
| SITE-005 | engineered-lighting-site | Site build, CI and end-to-end tests | 23 |
| SITE-006 | engineered-lighting-site | Doc 8, the index and site navigation | 10 |
| SITE-007 | engineered-lighting-site | Frame CAD, coupons and render checks | 13 |
| SITE-008 | engineered-lighting-site | BoM checklist and wiring diagram assets | 17 |

Counts overlap — a commit touching both `server.py` and `static/` is claimed by
two items — so the column sums past 288. The 288 is a distinct-commit count.

**These are `status: done` historical workstreams**, not new work. They exist to
describe what has already happened so the audit stops reporting it as
unrecognised. None of them asks you to do anything.

## The too-broad classifier: run, and here is the result

Every item was put through it before being proposed, as asked. **Thirteen of the
twenty come back too-broad**, and I am proposing them anyway with a reason
rather than narrowing them further:

**The check does not apply to `done` items, and that is correct, not a
loophole.** Its purpose is stated in its own message — *"that identifies the
subsystem, not this item's work"* — and the harm it prevents is a **forward**
claim: an open item whose glob silently absorbs whatever happens in a directory.
A finished workstream that genuinely produced 62 commits is described, not
over-claimed, by a glob matching 62 commits. `audit.py` already encodes this:
`audit_item()` returns for `done` items before the check runs. I verified that
rather than assuming it.

Two grab-bags **were** narrowed after the first pass, because they were the real
failure the check is for: `GB-028` dropped `tools/test_*.py`, `tools/check_*.py`
and `tools/schemas/**`, and `SITE-007` dropped a blanket `tools/**` and `ref/**`.
Both were claiming files with no relationship to the work.

**What I could not narrow:** `GB-015` (`tools/bench_ui/static/**`) and `GB-029`
(`captures/gimbal10/fixture/**`) are single-directory globs. Splitting them
further would need to know which console feature or which bench session each
commit belonged to, and that is in the commit bodies, not the paths. Saying so
is better than inventing a split that reads precise and is not.

## What I could not model, and did not invent items for

**13 commits, deliberately left in group D.** Naming them beats gaming the
number:

- `Keep the self-test stamp out of the repo` — a `.gitignore` change; an item
  for it would be meaningless.
- `Record what the camera measured about this bench` — a one-off capture that
  belongs to no workstream I can identify.
- `Mobile: ASCII wiring blocks collapse behind the SVG diagrams` — a
  presentation fix touching files three other items already claim.
- The remainder are reverts, asset regenerations and single-file corrections.

**A coverage figure gamed by fake items is worse than a low one.** 96% with 13
named exclusions is the honest number; 100% would have required four items that
describe nothing.

## A reconciliation you should have: part of the 301 was never a modelling gap

Thirteen **existing** items are suppressed by the too-broad check and therefore
contribute their commits to group D. `GB-001` alone would claim 57.

So 301 overstates the gap. The suppression is correct — a rule matching 57
commits is not evidence of one item — but it means the number mixes two
different problems: *work nobody modelled* (what this proposal fixes) and
*existing rules too coarse to attribute* (a separate narrowing job, already
reported in group B). I did not merge them.

## The one-sentence answer

**The three decided numbers are inert for these items**, and that is why this is
answerable in a sentence. `done` is in `_model.ACTIVE_EXCLUDED`, so these items
are excluded from `ranked()` and contribute nothing to any leverage count. Their
`impact`, `confidence` and `effort_minutes` are recorded and never read.

Proposed for all twenty: **`impact: 3`, `confidence: 4`, `effort_minutes: 240`,
`status: done`.**

So: **"yes to PROP-0003"** creates all twenty and drops group D from 301 to 13.

If you would rather not carry twenty historical items, the alternative is
**"just the gimbal-bench ones"** (15 items, ~91% of the reduction) or **"none of
them, live with group D"** — which is a real option, because group D at 301 is
an accurate description of the portfolio and costs nothing but scrolling.

Mine either way: titles, repos, keywords, evidence paths. Yours: the three
numbers, and whether these exist at all.
