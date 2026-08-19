---
name: audit
description: Re-check what product-os believes against what the repos actually show, and apply what Marcelo accepts in one sentence. Use when he says /audit, "is any of this still true", "re-check priorities", "what's changed", "catch me up", or sits down to review the portfolio.
---

# audit

This is the one he sits down with. The ranked list is a **conversation starter,
not a contract** — accuracy comes from doing this repeatedly, not from the seed
having been right.

## 1 · Run it

```bash
python3 tools/audit.py --since <last audit date>
```

Default window is 45 days. If `state/audits/<machine>/` has an entry, start from
its date — that is what makes this cheap the second time.

It is read-only. It proposes; it never writes.

## 2 · Present the four groups, in this order

**A · mechanical.** Applies on a bare *"merge"*. Recording found evidence,
bumping `updated`. Nothing here changes what anything means.

**B · escalated.** Do not decide these. Present each with the operands and stop.
Money, scope, status changes, and any rule that turned out to be wrong.

**C · refused, with the reason.** Say what you would not do and why. Refusals
belong in front of him, not swallowed.

**D · commits you could not attribute. MANDATORY, every single run.** A long D
means the seed is missing items — *that is the finding*, not a tool failure. An
audit that says "nothing changed" when it means "I recognised nothing" is the
one failure that ends trust in this tool, because from the outside the two look
identical.

Then the **coverage line**: expected, reached, unreachable, **by name**. Always.
If a repo was unreachable, say **"I couldn't look"** — never "no changes".

## 3 · Read group D yourself before you present it

This is where the intelligence is. The tool can match paths; it cannot read
prose. Skim the unattributed commits and say what they mean.

Real example from the first run: five commits titled *"Doc 4a: …"* were
unattributed, and one of them — `d8f092b`, *"seven more of the builder's parts,
and an honest meter"* — turned out to contain the answer to an open item, plus
a fact that contradicted something this repo had published. No path rule could
have found that. A person reading D did.

## 4 · Acceptance is one sentence

He says *"yes to A, do B1 at $240, drop B3"*. Turn that sentence into flags and
run it. **No file-editing ritual, no confirmation round-trip, no checklist.**

```bash
python3 tools/apply.py \
  --evidence GB-004=19dd790,34b9f7c \
  --status GB-002=doing \
  --said "yes to A, GB-002 to doing" \
  --note "armed lane still unproven" \
  --window 2026-08-10
```

`--said` takes his words **verbatim**. That is what the record is for.

Use `--dry-run` first only if the change is large or you are unsure you parsed
him correctly. Otherwise just do it — asking him to confirm what he just said is
the ritual this is designed to remove.

## 5 · What apply.py will refuse, and you must not work around

- **`status: done` without evidence that existed before the run.** Evidence the
  audit discovered a moment ago has not been read by anyone. Found evidence
  lands this run; closing happens next run, after he has looked. Do not paper
  over this by writing the file directly.
- **Human-authority fields** — `impact`, `confidence`, `effort_minutes`,
  `lead_time_days`, `cost_usd`, `unblocks`, `pin`, `project`, `gate`,
  `machine_affinity`, the `evidence` rule, and the `dropped`/`parked` statuses.
  They go to `state/proposals/` instead.

## 6 · Ordering is his

The computed score is a **label, like a priority chip — not a verdict**. `pin` is
ordinary, not an exception; use it when he tells you an order.

When his order and the math diverge, **say so once, with the reason, then do what
he said.** Once. Not every run, and never as a preamble to doing it anyway.

Worth knowing before you argue: `EL-001` is a 20-minute, $205 order that looks
like a chore and ranks first only because everything downstream slides two weeks
without it. That is the insight a hand-ordered list loses — so it is worth one
sentence, and exactly one.

## 7 · The record

`apply.py` writes `state/audits/<machine>/`, including on a run where everything
was refused. Then:

```bash
python3 tools/validate.py
```

If a finding was a genuine dead end — a rule that cannot work, an approach that
does not — add it to `wiki/ruled-out.md` with keywords, source, date and grade.
The `SessionStart` hook reads that file; a finding that stays in an audit record
is a finding nobody meets at the moment they need it.
