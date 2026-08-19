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

**Lead time is in the ranking.** A three-minute order with fourteen days of mail time
outranks a two-hour task with none, because every day the order isn't placed, the
entire downstream chain slides. A conventional board ranks by importance and gets that
exactly backwards.

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
CLAUDE.md · AGENTS.md     byte-identical read-first contract
intent.md                 MINE. Root authority. Every proposal cites it.
standing-orders.md        MINE. Judgment, made reusable.
state/                    authored, committed — no computed value ever lives here
  projects/<slug>/items/  one file per item
  questions/              open questions, ranked alongside tasks
  decisions/              rulings, with revisit triggers
  inbox/                  raw captures. Untriaged, unranked.
  proposals/              pending changes to decided fields
build/                    GENERATED, git-ignored, rebuilt wholesale
wiki/ruled-out.md         dead ends. The most expensive knowledge here.
tools/                    stdlib Python 3.9+. No dependencies, no install.
plugin/                   the Claude Code plugin, versioned with the data
```

## Knowledge is organised by re-derivation cost

Not by topic. A physical measurement needs the part in hand to recover; a dead end
costs hours of bench time; a fact costs a search. Effort goes where recovery is
expensive, which is why `wiki/ruled-out.md` is the file that matters most and gets
injected into sessions by a `SessionStart` hook rather than sitting somewhere hoping
to be read at the right moment.

Every fact carries provenance — `measured` > `datasheet` > `inferred` > `said-in-chat` —
and those four never render identically.

## Status

Slice 1a-minus. Item model, scoring, validation, the staleness detector, the ruled-out
register and three skills. Deliberately not yet built: the audit proposal engine, the
thread indexer, per-item briefs, the site and `llms.txt`.

Requires Python 3.9+ and nothing else.
