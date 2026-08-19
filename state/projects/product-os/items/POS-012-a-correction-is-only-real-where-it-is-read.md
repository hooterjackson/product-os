---
{
  "id": "POS-012",
  "title": "A correction is only real where it is read",
  "project": "product-os",
  "status": "doing",
  "lane": "infra",
  "gate": "none",
  "machine_affinity": null,
  "impact": 3,
  "confidence": 3,
  "effort_minutes": 60,
  "cognitive_load": "medium",
  "lead_time_days": 0,
  "cost_usd": null,
  "unblocks": [],
  "keywords": [
    "correction",
    "excerpt",
    "register",
    "ruled-out",
    "proposal",
    "referential-integrity",
    "validate",
    "drift",
    "visibility",
    "concurrency",
    "two-agents",
    "one-tree",
    "banner",
    "closed-origin"
  ],
  "evidence": [],
  "created": "2026-08-19",
  "updated": "2026-08-19"
}
---

A correction that exists but sits outside the window its reader looks through did
not happen. This item exists because that failure was found in production on the
agent-facing surface, and because it is a *different* class from the one
`CLAUDE.md`'s table already covers — different enough that the remedies point in
opposite directions.

`DEC-201` made this repo public on 2026-08-19 and superseded `R-050`. The
register was corrected the same day, by the book: a `SUPERSEDED` block appended
at the foot of `R-050`, original text left standing per the rule at the top of
`wiki/ruled-out.md`. **`brief.py` and `kickoff.py` collect only an entry's first
whole paragraph.** The correction was below the cut, so 121 committed files under
`public/` went on telling every cold-start agent that this repository starts
private — fetched over `raw.githubusercontent.com`, injected by the
`SessionStart` hook, and reported by `publish.py --check` as in sync. It *was* in
sync. `state/repos.json` had the same contradiction and was the reported symptom;
it turned out to be the harmless one, because nothing reads that field.

The second half is referential integrity. `state/repos.json` cited a proposal
that did not exist and `validate.py` exited 0, because reference resolution
covered `unblocks`, `answers`, `gates` and repo names and stopped there.

## Acceptance

- [x] `R-050`'s correction hoisted into the lead paragraph, so every
      `parse_register` consumer carries it. 0 published files still claim the
      repo starts private — was 121.
- [x] `E-REF-PROPOSAL` in `validate.py`: a `PROP-NNNN` citation anywhere in
      authored state or `wiki/` must resolve to a file in `state/proposals/`.
      `state/inbox/` exempt — a capture is raw words and triage is what makes a
      citation real. `public/` and `build/` exempt — derived, and reporting a
      dangling cite there points at the generated copy instead of the source.
      Verified both ways: fires on the `genio` cite at `state/repos.json:20`
      when the proposal is absent, silent when it is present.
- [x] `PROP-0004` committed, which is what makes the `genio` citation resolve.
- [x] `R-063` records the class with its four instances; `R-064` records the
      two-agents-one-tree cascade that surrounded the work.
- [x] The rule added to `CLAUDE.md` **beside** the mechanical-signal table, not
      inside it, and `AGENTS.md` kept byte-identical.
- [x] `CLOSED ON MY JUDGEMENT` present in the first 12 lines of every inferred
      closure's brief, where `test_an_unconfirmed_close_is_flagged_on_the_face_of_its_brief`
      looks.

## Open, and deliberately not fixed here

**The `SessionStart` hook truncates on a different axis and it bites.** The hook
injects whole entry bodies, so a foot-of-entry marker does reach it — but only
for the top `MAX_ENTRIES = 6` entries by keyword-overlap size. Measured
2026-08-19: **7 of 41 items match more than six entries.** `EL-003` matches 13;
seven are reduced to a bare count line. An entry's visibility there depends on
how many keywords it happens to share, not on whether it carries a correction, so
a superseded marker on a low-overlap entry is never injected at all.

Raising the cap trades context budget for coverage, and weighting corrections
above overlap changes what the hook is *for*. Both are judgement calls with taste
in them, so neither is made here. `R-063` carries the measurement.

## Handoffs
