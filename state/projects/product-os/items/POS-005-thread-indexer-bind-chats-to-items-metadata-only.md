---
{
  "id": "POS-005",
  "title": "Thread indexer: bind chats to items, metadata only",
  "project": "product-os",
  "status": "done",
  "lane": "infra",
  "gate": "none",
  "machine_affinity": null,
  "impact": 4,
  "confidence": 3,
  "effort_minutes": 480,
  "cognitive_load": "high",
  "lead_time_days": 0,
  "cost_usd": null,
  "unblocks": [],
  "keywords": [
    "indexer",
    "threads",
    "codex",
    "claude-code",
    "jsonl",
    "rollout",
    "sharding",
    "machine",
    "attachment",
    "metadata",
    "privacy"
  ],
  "evidence": [],
  "evidence_found": [
    {
      "kind": "file",
      "repo": "product-os",
      "path": "tools/index.py",
      "date": "2026-08-19",
      "note": "1108 codex + 6 claude-code files in 2.0s; 13 threads; 3 bound to items."
    },
    {
      "kind": "file",
      "repo": "product-os",
      "path": "state/threads/by-machine/work-laptop.json",
      "date": "2026-08-19",
      "note": "The shard. 14 allowlisted keys, no message text, paths tilde-relative."
    },
    {
      "kind": "file",
      "repo": "product-os",
      "path": "tools/validate.py",
      "date": "2026-08-19",
      "note": "check_thread_shards: independent allowlist gate. Proven by injecting a 'message' key -> E-SHARD-LEAK."
    }
  ],
  "created": "2026-08-19",
  "updated": "2026-08-19",
  "completed": "2026-08-19",
  "closed_origin": "inferred"
}
---

`tools/index.py`. Reads 1,108 Codex rollouts and 6 Claude Code transcripts in
**2.0 s**, writes `state/threads/by-machine/work-laptop.json`, and touches no
message text on the way.

## Acceptance

| | |
|---|---|
| ~5 s warm | **2.0 s** cold — line 1 + 64 KiB tail, never a full read |
| shard passes the allowlist | 14 keys, verified; injecting `message` → `E-SHARD-LEAK` |
| counts by tool + coverage line | 7 codex · 6 claude-code · malformed/unreadable/excluded all reported |
| ≥1 real attachment by ID | **3 threads → POS-001…POS-005** |

## The finding that matters more than the tool

v6 read the citation counts (602 `EL-001`, 203 `GB-001`, …) as the convention
working. It is working — but **97.3% of every anchor on this machine is inside
this repo's own planning transcripts:**

    ~/Claude/product-os            4072 citations   EL-001x664, GB-001x223, EL-002x204
    ~/Claude/engineered-lighting    114 citations   EL-014x52, EL-020x14, EL-021x14
    ~/Claude                          0 citations

And **every one of those 114 external citations is to an ID that no longer
exists** — `EL-014`, `EL-020`, `EL-031`, `EL-040` are from the discarded 33-item
v1 seed.

So the honest state: outside this repo's own sessions, the corpus contains
**zero valid anchors**. Not a defect — a cold start, and the thing that solves
it is Marcelo using the system on other repos. But "the anchors are already
there" would have been wrong.

## An ID is unique only within a seed generation

The first run bound a real thread to `Q-004` and it was **wrong**. That
transcript's `Q-004` sits beside `EL-040` and `EL-042`:

> Blocks: EL-040, EL-042 · Answers: Q-004

Those are v1-seed IDs. Today's `Q-004` is *"where do 300 liveness taps a second
come from"* — unrelated work that happens to have inherited the number.

Fixed by `gate_by_age()`: a conversation cannot cite an item that did not exist
when it happened. Collisions are counted and reported, never silently dropped.
`R-057`.

## Design notes worth keeping

- **Dedupe on `payload.session_id`, not filename.** 681 of 1,108 files share one
  root; by filename this would report 1,108 threads.
- **`source` is polymorphic** — `str` on roots, object on subagents. Exactly 7
  of 1,108 are roots. A strict parser breaks on it.
- **`session_index.jsonl` is titles only.** Its `updated_at` lagged real activity
  by 9 and 11 days; a date wrong by a week and a half is worse than no date.
- **Claude Code has no `session_meta`.** Line 1 is a queue-operation, so `cwd`
  and `branch` come from scanning forward to the first real record — and
  `last_active` from scanning **backward**, because `timestamp` is absent on the
  title/mode records that are usually last.
- **Own-repo transcripts are scoped, not excluded.** Blanket exclusion loses the
  `POS-*` work that genuinely happened there. Inside this repo's sessions, only
  this repo's items bind: discussion dropped, work kept.

## Handoffs

### 2026-08-19 · work-laptop
**Did:** the indexer, the shard, the CI allowlist gate, 12 tests.
**Also fixed, and it was the more urgent bug:** `audit.py` truncated every
commit query at the API's 100-row page. Group D was reported as 108 and 156 on
the same day; both were capped and neither carried its window. Paginated, the
default-window figure is **301**. `R-058`.
**Next:** Marcelo uses the loop. Anchors accumulate on their own.
**Reached:** codex corpus, claude-code corpus · **Could not reach:** —
