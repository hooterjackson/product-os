# product-os

The priority and context control plane for a portfolio of interlocking projects run
through AI chats across several machines.

It answers one question — **what should I work on now, and what do I already know
about it** — and it refuses to answer it dishonestly.

```bash
python3 tools/rank.py --explain     # the top item and why
python3 tools/stale.py              # published docs that contradict a ruling
python3 tools/validate.py           # is this repo internally consistent?
```

## What makes it different from a board

**Lead time is in the ranking.** Not asserted — here are the two rows and the
arithmetic, from `rank.py --show`, on the real seed:

```
EL-001  Order the Doc 4 LED BoM                     EL-003  Print the tolerance coupon, then the fit coupon

  effort_bucket(20 min)  = 2                          effort_bucket(120 min) = 3
  base = (4 x 4) / 2     = 8.000                      base = (3 x 4) / 3     = 4.000
  leverage               = 1  (GB-012)                leverage               = 0
  lift = 1 + 0.25 x 1    = 1.250                      lift = 1 + 0.25 x 0    = 1.000
  urgency = 1 + 14/7     = 3.000                      urgency = 1 + 0/7      = 1.000
  score = 8 x 1.25 x 3   = 30.00                      score = 4 x 1 x 1      = 4.00
```

**30.00 against 4.00, and 3.000 of that 7.5× is the urgency term alone.** Twenty
minutes of clicking outranks two hours of real work, because the fourteen days
start when you click and not when you are ready — and `GB-012`, the gate the whole
Zigbee phase converges on, cannot be demonstrated without the part.

A conventional board ranks by importance and gets that exactly backwards. Run
`python3 tools/rank.py --show EL-001` and check the operands rather than
believing the ratio; a bare ratio is not falsifiable.

**Leverage is transitive.** "Wire the LEDs" directly unblocks one thing — but that
unblocks the firmware, which unblocks the app. The score reflects the whole reachable
set, not the direct children.

**Rank is derived, never stored.** There is no ordered list in this repo. `rank.py`
recomputes it from the score inputs every run, so there is nothing to drift.

**The system proposes; it never decides.** Scores and reasoning are computed freely
into `build/`. The inputs those scores read are human-authority and change only when a
proposal is accepted. `validate.py` fails if that boundary is crossed.

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

## Install

Two commands, and they are the same two on every platform:

```bash
git clone <this repo> && cd product-os
```

then, inside Claude Code:

```
/plugin marketplace add ./product-os
```

That registers `/next`, `/capture` and `/handoff`, and the `SessionStart` hook
that pushes matching `wiki/ruled-out.md` entries into context before you propose
an approach.

## Knowledge is organised by re-derivation cost

Not by topic. A physical measurement needs the part in hand to recover; a dead end
costs hours of bench time; a fact costs a search. Effort goes where recovery is
expensive, which is why `wiki/ruled-out.md` is the file that matters most and gets
injected into sessions by a `SessionStart` hook rather than sitting somewhere hoping
to be read at the right moment.

Every fact carries provenance — `measured` > `datasheet` > `inferred` > `said-in-chat` —
and those four never render identically.

## Status

**Slice 1a-minus, seeded and exercised.** 6 projects · 25 items · 5 questions ·
8 rulings · 53 ruled-out entries · 3 skills · 1 hook. `validate.py` is clean,
`build.py` is byte-deterministic across runs, and the deepest confirmed
dependency chain is 4 hops.

`stale.py` produces the headline finding rather than transcribing it — on first
run it reports Doc 7 (24 days) and Doc 6 (13 days) behind D3, from commit dates,
and prints a coverage line naming what it reached.

**This repository is private**, against the original preference, because
`wiki/ruled-out.md` seeds ~50 findings from an unpublished engineering repo —
including security-design detail of the authority model of a brakeless
ceiling-mounted machine. Flipping to public later is one command; unflipping is
not. See `R-050`.

Deliberately not yet built: the audit proposal engine, the thread indexer,
per-item briefs, `/unblock`, the site and `llms.txt`.

Requires Python 3.9+ and nothing else.
