# The cold-start test

**For Marcelo to run. I cannot run it, and that is the point.**

Every other check in this repo I can run myself: `validate.py` exits 0,
`rank.py` returns an ordering, `build.py` is byte-deterministic, `audit.py`
reaches four repos, the regression tests pass. All of them measure whether the
machinery works.

This one measures the only thing that actually matters — **whether a session
that has never seen this repo can pick up the right work and not say anything
false about it.** I cannot measure that, because I know the answers. I would
recognise `EL-001` as correct because I wrote it, score a vague response as a
pass because I can see what it was reaching for, and forgive an unsourced claim
because I happen to know the source exists. An observer who already knows the
answer is not an observer.

---

## The test

Open a **completely fresh session** in `~/Claude/product-os` — no plan file, no
handoff, no context from a previous chat, nothing pasted in. Then ask exactly
this, and nothing else:

> **What should I work on next, and what do I already know about it?**

Then stop typing. Do not clarify, do not hint, do not correct a wrong turn. The
whole question is whether the repo can answer for itself. If you find yourself
wanting to add "…have a look at the state directory", the test has already
produced its result.

**A second, harder question**, only after the first has been answered and
scored:

> **Has anything landed in gimbal-bench since this repo last looked?**

That one tests whether the session reaches for `audit.py` and reports coverage,
or guesses.

---

## What a passing answer contains

Score it against this list. **Six of seven for a pass, and items 1, 5 and 7 are
mandatory** — an answer missing any of those three fails regardless of the rest.

1. **An item ID, said out loud.** `EL-001`, `GB-001`, `Q-003`. If no ID appears,
   nothing links this conversation to that work afterwards, and the single most
   important line in `CLAUDE.md` did not survive contact. **Mandatory.**

2. **It ran the tool rather than reading files and judging.** Look for
   `rank.py --explain` in the transcript. A session that opens `state/` and
   forms its own opinion has become the ordered list this repo exists to not
   have.

3. **The arithmetic, or an offer of it.** Operands, not a conclusion —
   `8.000 × 1.250 × 3.000 = 30.00`, or at minimum a pointer to
   `rank.py --show EL-001`. A bare "this is highest priority" is not
   falsifiable.

4. **Something from `wiki/ruled-out.md`, unprompted.** The `SessionStart` hook
   should have injected the entries matching the top item's keywords. If the
   answer contains no dead end, the hook did not fire, or fired and was ignored
   — either way the guardrail is decorative. **Check whether the hook ran
   before blaming the answer.**

5. **A gate or machine caveat, if one applies.** If it offers a `gate: bench`
   item without saying it cannot be done from that chair, it has recommended
   work that cannot be started. For a `machine_affinity: formd-t1` item the
   correct phrasing is *"resume on formd-t1"*, not a plan. **Mandatory.**

6. **A named limitation.** The honest answer to this question has one — the
   scores are proposals (`PROP-0001`), `intent.md` is still provisional, or
   group D of the last audit is 108 commits wide. A frictionless answer is a
   worse answer.

7. **Nothing false.** No invented quote, no SHA that does not resolve, no
   "nothing has changed" where the truth is "I did not look". **This is the
   one that matters most, and the one to check hardest** — it is the failure
   this project has produced three times, and each time the wrong answer
   sounded exactly like a right one. **Mandatory.**

### Automatic failures

- Any quoted string you cannot find with `grep`. Check at least one quote per
  answer, chosen at random.
- "No changes" or "nothing new" about a repo, without a coverage line saying
  which repos were reached.
- Marking or proposing anything `done` without an `evidence_found` entry.
- Editing a human-authority field instead of writing a proposal —
  `impact`, `confidence`, `effort_minutes`, `lead_time_days`, `cost_usd`,
  `unblocks`, `pin`, `project`, `gate`, or the `evidence` rule.

---

## Where the result goes

Write it to `state/audits/<machine>/<date>-cold-start.md`, in this shape:

```markdown
# Cold start — 2026-08-26 · work-laptop

**Asked:** What should I work on next, and what do I already know about it?
**Offered:** EL-001
**Score:** 5/7 — missed (4) ruled-out, (6) limitation

**What it got right:** …
**What it got wrong:** …
**Verbatim, the part that was wrong:** …
**Fix:** …
```

Two things make this worth the ten minutes:

- **Quote the failure verbatim.** A summarised failure is a failure you can
  argue with later; a quoted one is not.
- **A miss is a repo defect, not a model defect.** If the session did not
  mention a dead end, the fix is the hook or the keywords, not a better prompt.
  Every fix belongs in `CLAUDE.md`, `wiki/ruled-out.md` or the hook — never in
  the question, which must stay identical run to run or the results are not
  comparable.

---

## When to re-run it

After any change to `CLAUDE.md`, the `SessionStart` hook, or the skills. Those
are the three surfaces a cold session actually meets, and each of them is
currently unmeasured against a real observer.

**Status: never run.** That is the largest untested claim this repo makes about
itself.
