# product-os

The priority and context control plane for a portfolio of interlocking projects run
through AI chats across several machines.

It answers one question — **what should I work on now, and what do I already know
about it** — and it refuses to answer it dishonestly.

```bash
python3 tools/rank.py --explain     # the top item and why
python3 tools/audit.py              # is any of this still true?
python3 tools/stale.py              # published docs that contradict a ruling
python3 tools/validate.py           # is this repo internally consistent?
```

`/audit` is the one to sit down with. It re-reads the repos, attributes commits to
items **by path** — the commit subjects here are things like *"map the fall that
never comes"*, so no keyword rule would ever match them — and sorts what it finds
into four groups: **A** applies on a bare "merge", **B** is escalated, **C** is
refused with the reason, and **D** is every commit it could not attribute.

**D is mandatory and printed every run**, because an audit that says "nothing
changed" when it means "I recognised nothing" is indistinguishable from success
and would end trust in the tool. Acceptance is one sentence — *"yes to A, do B1 at
$240, drop B3"* — and `tools/apply.py` does exactly that, refusing `done` without
evidence and routing human-authority fields to `state/proposals/`.

## What makes it different from a board

**Dependency depth orders the work.** An item's score reflects everything
downstream through confirmed edges, not just its direct children. `GB-001`
unblocks one item directly and **8** transitively, which is why it leads:

```
GB-001   base (5 x 4)/4 = 5.000  x  lift (1 + 0.5 x 8) = 5.000  =  25.00
```

Run `python3 tools/rank.py --show GB-001` and check the operands rather than
believing the number. A bare ratio is not falsifiable.

**`--here` means here.** `--gate none` is ungated and may include another
machine's work; `--here` also filters by `machine_affinity`. The distinction is
in this README because `CLAUDE.md` got it wrong from the seed until a
no-context subagent read what the code actually did.

### Two things this README said that were false

Until 2026-08-19 this section starred `EL-001` — *order the Doc 4 LED BoM* —
ranked #1 on a lead-time term. Both halves were wrong:

> `EL-001`'s evidence rule named `docs/bom-checklist.md`, a checklist whose own
> second line reads *"state persists in your browser (nothing leaves your
> device)."* Ticking every box writes nothing to the repo. **The rule was
> structurally unsatisfiable: the item could never close, no matter what was
> bought.** The parts were already photographed on the bench.

And the **lead-time term itself is gone.** Measured before removing it: 2 of 30
items carried any `lead_time_days` and both were purchases, so it was inert on
28 items and tripled the score on the two that no longer mattered. The hardware
is bought; this tool plans software.

**A number that cannot be checked against reality is decoration.** The fix was
never a better guess at the outset — it is `/audit`, run repeatedly, by somebody
willing to be told the flagship is wrong. See `R-056`, `R-061`.

**Rank is derived, never stored.** There is no ordered list in this repo.

**The score is a label, not a verdict.** `pin` is ordinary use. When his order
and the arithmetic diverge the system says so **once**, with the reason, then
does what he said.

**The system proposes; it never decides** — except when he decides. `--field` is
the agent speaking and human-authority fields propose; `--decided` is him, and
applies. Two guards, deliberately separate: authority asks *who decided this*,
truth asks *is this provable*. `done` without evidence is refused for everyone.

## Layout

```
CLAUDE.md · AGENTS.md         byte-identical read-first contract
intent.md                     MINE. Root authority. Every proposal cites it.
standing-orders.md            MINE. Judgment, made reusable.
state/                        authored, committed — no computed value ever lives here
  projects/<slug>/project.md  the project, its north star, and who may rule
  projects/<slug>/items/      one file per item
  projects/<slug>/decisions/  rulings, with revisit triggers
  questions/                  open questions, ranked alongside tasks
  inbox/                      raw captures. Untriaged, unranked.
  proposals/                  pending changes to decided fields
  machines/ · repos.json      where work can happen, and where evidence lives
build/                        GENERATED, git-ignored, rebuilt wholesale
wiki/ruled-out.md             dead ends. The most expensive knowledge here.
tools/                        stdlib Python 3.9+. No dependencies, no install.
plugin/                       the Claude Code plugin, versioned with the data
```

## Use it from anywhere, with no clone

The product is **copyable prompts**, not the ranking. Paste one line into a chat
on any machine — a phone, a bench PC, claude.ai — and it picks up current state:

```
Read https://raw.githubusercontent.com/hooterjackson/product-os/main/public/llms.txt and follow it.
```

Five actions, and **the destination is part of the artifact** because pasting
the right text into the wrong place is the main failure mode:

| Action | Fetch from `public/` | Paste into |
|---|---|---|
| Start a task | `kickoff/<ID>.md` | a **new** chat |
| Tell it what changed | `reconcile.md` | a **new** chat |
| Link a web chat | `attach/<ID>.md` | **that** chat |
| Connect a repo | `connect-repo.md` | an existing chat with repo access |
| Capture a thought | `capture.md` | anywhere |

`public/` is committed precisely so this works without a clone; `build/` stays
git-ignored, and `publish.py --check` keeps the two from drifting.

### Optionally, the plugin

On a machine you set up deliberately:

```bash
git clone <this repo> && cd product-os
```

then, inside Claude Code, `/plugin marketplace add ./product-os` — which
registers `/next`, `/capture`, `/handoff` and `/audit`, plus the `SessionStart`
hook that injects matching `wiki/ruled-out.md` entries before you propose an
approach. **The plugin is a convenience, not the product.**

## Knowledge is organised by re-derivation cost

Not by topic. A physical measurement needs the part in hand to recover; a dead end
costs hours of bench time; a fact costs a search. Effort goes where recovery is
expensive, which is why `wiki/ruled-out.md` is the file that matters most and gets
injected into sessions by a `SessionStart` hook rather than sitting somewhere hoping
to be read at the right moment.

Every fact carries provenance — `measured` > `datasheet` > `inferred` > `said-in-chat` —
and those four never render identically.

## Status

**Slice 1a-minus plus the agent-facing half of 1b.** 6 projects · 31 items
(20 active, 8 parked) · 5 questions · 9 rulings · 61 ruled-out entries ·
4 skills · 1 hook · 71 gated tests. `validate.py` is clean, `build.py` is
byte-deterministic, and the deepest confirmed dependency chain is 5 hops — with
an unmade decision sitting in the middle of it, which is what the graph is for.

`stale.py` produces its headline finding rather than transcribing it: on each
run it reports Doc 7 and Doc 6 behind ruling D3, from commit dates, with a
coverage line naming what it reached.

**This repository is public by `DEC-201`.** `wiki/ruled-out.md` carries findings
derived from a private engineering repo; the disclosure screen finds no
credential, email, tailnet identifier or MAC, and the decision carries a revisit
trigger. `gimbal-bench` itself stays private — not a disclosure judgement, but
because a capture names a third party.

Deliberately not built: the five human views (a design pass is running), the
site, `llms.txt` hosting beyond raw URLs, `/unblock`.

Requires Python 3.9+ and nothing else.
