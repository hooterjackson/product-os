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

## 5 · `--field` is you. `--decided` is him.

**When he states a fact about his own project, apply it.** Scores, costs, scope,
gates, priorities, `parked` — all of it. Use `--decided`, which requires
`--said` carrying his words:

```bash
python3 tools/apply.py --decided EL-001=cost_usd:486 \
  --said "the tape is the Valent X, cost is 486"
```

**Do not file a proposal for something he just told you.** A proposal is
addressed to him; writing one in response to his own sentence routes his
decision into a queue for himself. That was a real bug in this tool.

Use `--field` when *you* inferred the value — from a commit, a doc, a
calculation. Then human-authority fields propose, correctly, because the person
who should check them is not the person who said them.

**Never write `--decided` for something he did not say.** The flag is a claim
about who spoke, it is recorded permanently in the audit entry, and getting it
wrong makes a guess indistinguishable from a decision forever.

## 6 · The two refusals that do not bend, for anyone

These are **truth** guards, not authority guards. His word does not clear them
and you must not work around them:

- **`status: done` without evidence that existed before the run.** He cannot
  make an unevidenced completion evidenced by asserting it. Found evidence lands
  this run; closing happens next run, after somebody has read it.
- **Anything you would have to write to the file directly** to get past the
  above. If you find yourself reaching for `Edit` on an item file to set
  `status: done`, stop.

If he insists an item is finished and there is no evidence, that is not a
disagreement to win — say what evidence would settle it, and offer to record a
dated manual note, which is evidence.

## 7 · Ordering is his

The computed score is a **label, like a priority chip — not a verdict**. `pin` is
ordinary, not an exception; use it when he tells you an order.

When his order and the math diverge, **say so once, with the reason, then do what
he said.** Once. Not every run, and never as a preamble to doing it anyway.

Worth knowing before you argue: a 20-minute order with a fortnight of shipping
looks like a chore and ranks above real work only because everything downstream
slides while it sits unclicked. That is the insight a hand-ordered list loses —
so it is worth one sentence, and exactly one.

And worth knowing before you argue *too hard*: this skill used to cite `EL-001`
here as the live example of that. `EL-001` turned out to be already bought, on
an evidence rule that could never have told anyone. **Argue for the mechanism,
never for a specific item's number** — the numbers are guesses that the audit
converges, which is the entire point of running it again.

## 8 · The record

`apply.py` writes `state/audits/<machine>/`, including on a run where everything
was refused. Then:

```bash
python3 tools/validate.py
```

If a finding was a genuine dead end — a rule that cannot work, an approach that
does not — add it to `wiki/ruled-out.md` with keywords, source, date and grade.
The `SessionStart` hook reads that file; a finding that stays in an audit record
is a finding nobody meets at the moment they need it.
