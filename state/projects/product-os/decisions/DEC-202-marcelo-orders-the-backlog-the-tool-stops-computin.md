---
{
  "id": "DEC-202",
  "title": "Marcelo orders the backlog; the tool stops computing an order",
  "project": "product-os",
  "status": "done",
  "ruling_id": "M2",
  "decided": "2026-08-20",
  "revisit_if": "The backlog grows past what one ordered file can be read and reordered by hand, or a second person starts authoring items. Either would reintroduce the problem scoring was built for.",
  "supersedes": [],
  "superseded_by": null,
  "propagates_to": [
    {
      "repo": "product-os",
      "path": "CLAUDE.md",
      "note": "The 'rank is derived, never stored' paragraph and every rank.py invocation. A reader who knows the old contract must meet the reversal where they already read -- R-065."
    },
    {
      "repo": "product-os",
      "path": "README.md",
      "note": "Same, on the front door of a public repo."
    }
  ],
  "keywords": [
    "rank",
    "ranking",
    "score",
    "scoring",
    "order",
    "backlog",
    "priority",
    "derived",
    "stored",
    "authority",
    "intent",
    "leverage",
    "dependency"
  ],
  "evidence": [
    {
      "repo": "product-os",
      "path": "tools/_model.py",
      "sha": null,
      "date": "2026-08-20",
      "note": "9 of 17 adjacent pairs in the offerable list within 10% of each other -- the threshold CLAUDE.md's own escalation rule names. 18 items, 10 distinct scores, largest tie 4."
    },
    {
      "repo": "product-os",
      "path": "state/projects",
      "sha": null,
      "date": "2026-08-20",
      "note": "12 dependency edges over 41 nodes, 10 of them GB->GB inside one repo, from a phase plan Marcelo wrote by hand. pin set on zero items ever; lead_time_days and cost_usd set on 2 of 41, the same two hardware purchases."
    }
  ],
  "created": "2026-08-20",
  "updated": "2026-08-20"
}
---

**This reverses the single most-quoted line in this repository.** `CLAUDE.md` has
said since the first commit that *"rank is derived, never stored — there is no
ordered list anywhere in this repo."* There is now exactly one ordered list,
`state/backlog.md`, it is authored by hand, and it is the only thing that decides
what comes first.

## What the measurement showed

The argument for a derived rank was that it is a pure function of decided inputs,
and therefore checkable. It is. It just did not discriminate:

| measured 2026-08-20 @ `9b3ff8b` | |
|---|---|
| adjacent pairs within 10% | **9 of 17** — `CLAUDE.md` says *escalate* on each |
| distinct scores across 18 offerable items | 10 |
| largest tie group | 4 items on one score |
| `impact` 3-or-4 | 31 of 41 nodes |
| `confidence` 3-or-4 | 34 of 41 nodes |
| `pin` — the human override — ever set | **0 items** |

By its own constitution the tool should have handed back more than half of its
own ordering. A product of two clustered estimates carries no signal, and no
weighting recovers one.

The dependency half is `R-069`: 12 edges over 41 nodes, 10 of them inside a
single repo, from a phase plan the owner wrote before this tool existed.

## The rule this does NOT reverse

`intent.md`'s third precedence rule is *"What unblocks the most downstream
work."* Phase 1 deletes the mechanism that computed it, and `CLAUDE.md` requires
escalating anything that contradicts `intent.md`, so it was put to Marcelo before
anything was deleted rather than discovered afterwards. His ruling, verbatim:

> **"The criterion stays, the automation goes. `intent.md` describes how I
> decide, not what the tool computes — same as 'what is cheapest to reverse,'
> which nothing ever automated either. Don't edit either file."**

**Neither `intent.md` nor `standing-orders.md` was touched.** The distinction
generalises and is the durable part of this ruling: *a description of judgement
is not a specification of arithmetic.* An `intent.md` line naming something the
tool no longer derives is not a contradiction, and the next agent to find one has
its answer here without re-litigating it.

## What replaces it

`state/backlog.md` — one task ID per line, top is next, global across projects.
Reordering is one edit to one file and the diff shows exactly what moved.
`validate.py` enforces `E-BACKLOG-DRIFT`: every active task appears exactly once,
every listed ID resolves. That check is the whole safety net a hand-ordered list
gets, which is why it is not optional.

The system never creates a task. What the audit derives becomes a
**recommendation**, outside the backlog, one sentence plus its evidence, crossing
into the backlog only when he adopts it — `R-072`.
