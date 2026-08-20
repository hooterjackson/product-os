---
{
  "id": "POS-012",
  "title": "A correction is only real where it is read",
  "project": "product-os",
  "status": "doing",
  "lane": "infra",
  "gate": "none",
  "machine_affinity": null,
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
  "evidence_found": [
    {
      "kind": "commit",
      "repo": "product-os",
      "sha": "093dbe9",
      "date": "2026-08-19",
      "note": "R-050's correction hoisted into the lead paragraph so every parse_register consumer carries it; E-REF-PROPOSAL added; R-065 and R-066 written; the rule added beside the CLAUDE.md table with AGENTS.md kept byte-identical. PUSHED -- verified from origin, not from the local ref: git fetch then git rev-list --count origin/main..HEAD returns 0."
    },
    {
      "kind": "commit",
      "repo": "product-os",
      "sha": "cdb5eb4",
      "date": "2026-08-19",
      "note": "Renumbered this session's register entries to R-065/R-066 after they collided with another session's R-063/R-064, and added E-REGISTER-DUPLICATE so the collision is an error rather than something noticed by reading. PUSHED -- origin/main IS cdb5eb4."
    }
  ],
  "created": "2026-08-19",
  "updated": "2026-08-20"
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
- [x] `R-065` records the class with its four instances; `R-066` records the
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
in them, so neither is made here. `R-065` carries the measurement.

## Handoffs

### 2026-08-19 · work-laptop · `/handoff`

**Did:** Landed the class and its two guards, in `093dbe9` and `cdb5eb4`, both
pushed. `R-050`'s superseded marker was hoisted from the foot of the entry into
its lead paragraph, because `brief.py:66` and `kickoff.py:128` collect only the
first whole paragraph — the correction had been correct, cited, and invisible,
and **121 committed files under `public/` served a claim `DEC-201` had already
reversed** while `publish.py --check` truthfully reported the surface in sync. 0
published files carry it now. `E-REF-PROPOSAL` closes the reference class that
resolution had skipped; `E-REGISTER-DUPLICATE` closes the one the collision
below exposed. Both verified in **both** directions — firing on an injected
defect, silent on a clean tree — because a check only ever tested green is a
check whose failure path has never run. `R-065` and `R-066` written, and the rule
added to `CLAUDE.md:163` **beside** the mechanical-signal table with `AGENTS.md`
kept byte-identical, deliberately not as a fourth row: for a cheap signal you go
and read the primary source, for a misplaced correction you move it to where the
reader already is, and folding them together loses the second remedy.

**Next — an OPEN DECISION, not a task. Do not resolve it by writing code.** The
`SessionStart` hook is the one consumer that escapes the first-paragraph cut: it
injects whole entry bodies. It truncates on a different axis instead —
`MAX_ENTRIES = 6`, ranked by keyword-overlap size. Measured 2026-08-19, not
assumed: **7 of 41 items match more than six entries. `EL-003` matches 13, so
seven are reduced to a bare count line.** Visibility there depends on how many
keywords an entry happens to share, not on whether it carries a correction — so a
superseded marker on a low-overlap entry is never injected at all. Two forks,
each with a real cost:

| fork | what it buys | what it costs |
|---|---|---|
| **Raise `MAX_ENTRIES`** | fewer entries silently reduced to a count; at 13 every current item is covered | context budget, spent on every session start whether or not the entries are relevant. The hook front-loads the window before any work is done, so the cost is unconditional and the benefit is not. |
| **Weight corrections above overlap** | a `SUPERSEDED` marker is injected regardless of how few keywords it shares | changes what the hook is *for*. Today it answers *what is most related to this item*; ranking corrections first makes it answer *what is most likely to be stale*. Those are different questions, and the second one quietly demotes a highly-relevant entry to make room. |

A third option exists and is not obviously worse: leave the cap alone and treat
the count line as the signal, making it name the withheld entries by ID so the
reader can ask for them. Cheap, and it keeps both properties — but it assumes the
reader follows up, which is the assumption this whole item exists to distrust.

**Ruled out:** Appending a superseded marker at the foot of a register entry —
correct by this file's own leave-it-standing rule, and invisible to all four
`parse_register` consumers. `R-065`. · Trusting "the next free R number" as a
lock: both sessions computed the same next number against the same `HEAD` and the
register briefly carried two `R-063`s and two `R-064`s, with `validate.py`
exiting 0 throughout, because appending is the one operation that looks
conflict-free to git. `R-066`. · Regenerating `public/` while another session
held uncommitted state — it would have published their half-finished `POS-002`
closure by proxy on a public surface. Diagnose, do not regenerate; let the owning
session finish. `R-066`. · Trusting a scan script over the data: 49 `PARSE FAIL`
lines that read as repo damage were a wrong function name in my own scanner, and
an `AttributeError` in `brief.py:226` was a torn read of a file being written
concurrently. Both cleared on re-scan. Suspect the instrument before the subject.

**Status:** left at `doing`, deliberately. Everything in `## Acceptance` is
checked and pushed, but the `MAX_ENTRIES` fork above is unresolved and it is the
half that decides whether this class is actually closed or merely documented.
Both remedies trade something real, so per `CLAUDE.md` this escalates rather than
resolves. `evidence_found` carries both SHAs; **`done` needs his word, not
another commit.**

**Reached:** product-os (fetched; `origin/main` **IS** `cdb5eb4`, and
`origin/main..HEAD` is **0**, checked after pushing rather than before) ·
**Could not reach:** `gimbal-bench` — not cloned on work-laptop, private, and I
did not call the GitHub API for it. **I couldn't look.** `engineered-lighting-site`
— **I couldn't look**; I did not fetch it this session. Nothing above rests on
either. The `GB-004` and `EL-005` handoffs inside `e73f99a` are another session's
words, committed as-is so that `public/` had a committed `state/` to be in sync
with; I did not verify their content.
