# PROP-0001 — the seed's decided fields

**Status:** open. Nothing here has been accepted.
**Raised:** 2026-08-19, work-laptop, while building POS-001.
**Cites:** `CLAUDE.md` § Authority · `intent.md` § Order of precedence ·
`standing-orders.md` § Money.

---

## What this proposal is, and why it has to exist

The seed sets fields I am not allowed to write.

`CLAUDE.md` reserves `impact`, `confidence`, `effort_minutes`, `lead_time_days`,
`cost_usd`, `unblocks`, `pin`, `project`, `gate`, `dropped`/`parked` and the
`evidence` **rule** to you. But `tools/validate.py` refuses an item that has no
`impact`, no `confidence` and no `effort_minutes` — so a seed with those fields
left blank cannot exist at all, and a seed is what turns an empty repository
into something you can argue with.

So: **every decided value in `state/` is a proposal, and this file is it.** They
are placeholders with reasoning attached, not rulings. Amend, reject, or ignore
them; the point is that they are *visible and enumerated* rather than smuggled
in as defaults.

The enforcement this leans on is real from the next commit onward.
`validate.py --base <ref>` diffs human-authority fields against a base ref and
fails any change that arrives without an `Accepts: PROP-NNNN` trailer. It skips
newly added files, because there is nothing to diff against — which is exactly
the hole the seed drove through, and exactly why this file is here to name it.

---

## 1 · The scores

25 items and 5 questions. Rather than list 30 rows of numbers, here are the four
judgements that produced them. Disagree with a judgement and a whole group moves.

**(a) `impact: 5` is reserved for the two things that can hurt the fixture.**
GB-001 (the fault ring) and GB-012 (gate L) and GB-007 (the rollback ladder).
Everything else caps at 4. This follows `intent.md`'s first precedence rule —
safety of the installed fixture — and nothing else earned a 5.

**(b) `confidence: 3` means "the source says this is unresolved."** Every Z-M
item is at 3, because `ZIGBEE-PHASE-PLAN.md` marks residual forks inside most of
them. GB-003 is at 3 for a different reason: it is recall of an episode a week
old, and recall is weaker evidence than a log. Nothing in the seed is above 4
except where a commit already proves it (EL-004, EL-005, SITE-002, HAI-001,
POS-002, GB-002).

**(c) `effort_minutes` is a wall-clock guess, and it is the score's
denominator.** The buckets are ≤15→1, ≤60→2, ≤240→3, ≤960→4, >960→5, so the only
estimates that actually move a ranking are the ones near a boundary. Two are:
HAI-001 at 15 (bucket 1 — if it is really 20 minutes its score halves, from 20.0
to 10.0) and EL-001 at 20 (bucket 2 — if it is really 15, its score doubles to
60.0). Those two are worth your eye. The rest are not.

**(d) `cognitive_load` I did write** — it is agent-authority — but it drives
`--energy`, so it is listed here anyway. `high` on anything that means reading
firmware; `low` on anything mechanical.

## 2 · The two costs

| Item | `cost_usd` | Where the number comes from |
|---|---|---|
| EL-001 | 205.0 | Midpoint of the site's published *"Doc 4 · LED bench (~$170–240)"* |
| EL-002 | 60.0 | **My estimate. No source.** A bench meter with a current range. |

**EL-001's number is contested and you should not treat it as costed.** Row 4 of
the same BoM table prices the Valent X spool at **$486** by itself — more than
the top of the range for the whole stage. The row also names a **$30** BTF FCOB
substitute, and the range is almost certainly costed against that. The site never
says so. **Q-005** is the question; the two readings differ by about $456.

Per your standing order — *"Escalate anything that spends money"* — I am not
proposing which tape to buy. The two options, what each unblocks, and what each
does to the finish date are laid out in Q-005 and EL-001.

## 3 · The edges

Every `unblocks` entry has a sentence behind it. The Zigbee chain is one
sentence, quoted whole:

> **Dependency order:** Z-M1 (variant/partitions/signing scaffold) → Z-M0
> (mailbox, behind the flag) → Z-M2 (rollback; needs Z-M1) and Z-M3 (bring-up;
> needs Z-M0) → Z-M4/Z-M5/Z-M6 on Z-M3.
> — `docs/ZIGBEE-PHASE-PLAN.md` §6, `5a9bfbd`

The two gate-L prerequisites (EL-001 → GB-012, GB-013 → GB-012) come from §5's
list, quoted in both items.

**One edge is doing constitutional work and you should look at it directly:
GB-001 → GB-005.** That edge is D15's own title — *"Zigbee stays parked until
the fault ring and the drills are done"* — turned into a dependency.

I chose that over `status: parked` on the seven Z-items deliberately, and the
choice is arguable:

- **For:** `parked` is your field, not mine, so I must not set it. And `parked`
  is excluded from leverage, which would have collapsed a 7-item chain to
  nothing and hidden the structure the ruling is *about*.
- **Against:** a dependency edge reads as "do GB-001 and Zigbee unblocks
  itself." It does not. **Un-parking is a decision you have not taken**, and
  nothing in this repo takes it for you. If you want that stated in the data
  rather than in prose, set the seven Z-items to `parked` and accept that the
  chain view goes quiet.

`GB-008 → GB-012` is in `unblocks_inferred` — no source states it, so it is
excluded from leverage and cannot force anything to `blocked`.

**Nothing in the seed is pinned.** `pin` overrides the arithmetic, and there is
no reason to override arithmetic you have not read yet.

## 4 · The gates

Two are worth a second look because both were wrong in an earlier draft:

- **EL-001 and EL-002 are `gate: none`, not `awaiting-parts`.** Gating a
  *purchase* on the parts' *arrival* is circular, and it is the precise failure
  the urgency term exists to prevent. Your standing order says it better:
  *"Ordering is not spending… Rank the click, not the arrival."* The waiting
  belongs to GB-012, downstream.
- **GB-005 through GB-011 are `gate: none`**, because
  `ZIGBEE-PHASE-PLAN.md` §6 is headed *"Agent-side milestones (offline,
  reviewed, mega_gate green, no radio)"*. They carry `machine_affinity:
  formd-t1` instead, because the checkout is there and this Mac has never
  touched it.

## 5 · The evidence rules

The `evidence` **rule** is yours; `evidence_found` is mine. Every non-done item
carries a proposed rule — a repo plus path globs plus a sentence about what would
count.

**Globs are primary and commit subjects are not used**, on purpose. Real commit
subjects in these repos include *"map the fall that never comes"* and *"name the
light's one commander, sign what may replace its mind, keep its brake free"*. Any
evidence rule that pattern-matches on subject lines will miss the commits that
matter most, because the best writing in the portfolio is the least greppable.

## 6 · What I did not propose

- **`dropped` / `parked` on anything.** Not one item. Those are scope decisions
  with taste in them.
- **A change to `intent.md` or `standing-orders.md`.** Both still say
  `"provisional": true`, and both should keep saying it until you rewrite them.
- **Un-parking Zigbee**, publishing `gimbal-bench`, or creating this repo's
  remote.

---

## To accept

Edit whatever is wrong, then commit with:

    Accepts: PROP-0001

From that commit on, `validate.py --base <ref>` will refuse any further change to
a decided field that does not carry its own accepted proposal.
