---
{
  "id": "POS-002",
  "title": "Point PROJECT-STATE.md at product-os",
  "project": "product-os",
  "status": "done",
  "lane": "content",
  "gate": "none",
  "machine_affinity": null,
  "impact": 3,
  "confidence": 5,
  "effort_minutes": 25,
  "cognitive_load": "low",
  "lead_time_days": 0,
  "cost_usd": null,
  "unblocks": [],
  "unblocks_inferred": [],
  "answers": [],
  "keywords": [
    "project-state",
    "pointer",
    "handoff",
    "state-file",
    "drift",
    "bootstrap",
    "ninth"
  ],
  "evidence": [
    {
      "repo": "engineered-lighting-site",
      "paths": [
        "PROJECT-STATE.md"
      ],
      "note": "A commit adding a pointer from PROJECT-STATE.md into product-os, naming which file is authoritative for what."
    }
  ],
  "evidence_found": [
    {
      "kind": "commit",
      "repo": "engineered-lighting-site",
      "sha": "a482376",
      "date": "2026-08-19",
      "note": "PUSHED, verified 2026-08-19 on work-laptop: `git fetch origin` then `git branch -r --contains a482376` returns origin/main, and origin/main IS a482376. Supersedes the earlier LOCAL-ONLY note on this same SHA -- the pointer now exists for every machine, which was the one condition this item held itself doing for."
    }
  ],
  "repos": [
    "engineered-lighting-site",
    "product-os"
  ],
  "parent_ruling": null,
  "created": "2026-08-19",
  "updated": "2026-08-19",
  "completed": "2026-08-19",
  "closed_origin": "inferred"
}
---

**The single most likely way this repo fails is by becoming state file number
nine** in a portfolio that already has eight, each confidently disagreeing with
the others.

`PROJECT-STATE.md` is the incumbent. It opens by telling every agent on every
machine to read it first, and its header says 2026-07-31 against a remote that moved on until
2026-08-17 — nineteen days and a whole Doc 4a series later.

**Correction, 2026-08-19.** This item was written claiming the file *still*
lists two shipped prompts as pending. It does not: it self-corrected in
`acd0611` on 2026-07-29, before this item existed. I drafted the premise from a
local clone that was 54 commits behind — `R-044`, reproduced inside an item's
content rather than inside a report, which is sharper than any instance in the
`CLAUDE.md` table. The underlying lesson stands (`R-051`, and `EL-004` records
what happened); the present tense did not.

A pointer is not a merge. It should say which file is authoritative for what —
`PROJECT-STATE.md` for narrative and the site's own build state, product-os for
priority, gating and evidence — and it should be short enough that nobody has to
maintain it.

Twenty-five minutes, and it is the difference between two systems and two
opinions.

## Handoffs

### 2026-08-19 · work-laptop
**Did:** the pointer, as `a482376` in `engineered-lighting-site`. A block at the
top of `PROJECT-STATE.md` naming which file answers which question — product-os
for priority, gating and evidence; this file and `docs/` for narrative and the
site's build state — plus the precedence rule (product-os wins on status; a
`gimbal-bench` ruling or current bench evidence outranks both on what happened).
No dates, counts or item lists in the block, so there is nothing in it to rot.
Also: the "read this file first" opener is gone, the `Last updated` header now
says it describes the file rather than the repo, and the resume ritual asks for
`git fetch` on an existing clone and for the item ID in the first message.

**THE COMMIT IS NOT PUSHED.** `main` is 1 ahead of `origin/main`. Until someone
pushes, the pointer exists on this laptop and nowhere else — which is the exact
failure the item was written to prevent. That is why this is `doing`.
`git -C ~/Claude/engineered-lighting push` finishes it; `git reset --hard
origin/main` discards it.

**Two premises in this item were stale, both from the same cause.** The item
says the file "lists as pending two prompts that had shipped ten days earlier."
On `origin/main` that has been fixed for weeks — the file self-corrected in
`acd0611` and now says so out loud. The local clone this repo reads was **54
commits behind** `origin/main` and had never been fetched since July, so the
item was drafted against a July snapshot. `R-044` predicted this precisely. The
header-date complaint was the half that survived: `PROJECT-STATE.md` was last
touched `88a3a58` (2026-07-31) while `origin/main` had moved to `ac827cd`
(2026-08-16) — 19 days and a whole Doc 4a series later.

**Next:** push `a482376` from `~/Claude/engineered-lighting`, then flip to done.

**Also noticed, unrelated to this item:** `state/repos.json` still describes
product-os as having "No remote yet, by decision -- see R-050", but `DEC-201`
superseded R-050 and a reachable public remote exists; `owner`, `public` and
that note are all wrong there. Not a live bug — `audit.py` probes for remotes at
runtime rather than trusting the file — but it is the register disagreeing with
an accepted decision.

**Reached:** `engineered-lighting-site` (fetched, `ac827cd`), `product-os`
(fetched, in sync), and three `raw.githubusercontent.com` product-os endpoints
— `llms.txt`, `api/now.json`, `kickoff/POS-002.md`, all HTTP 200. ·
**Could not reach:** —

### 2026-08-19 · work-laptop · `/reconcile`

**Did:** nothing to the site repo — **the push had already happened.** Fetched
`~/Claude/engineered-lighting` and `origin/main` *is* `a482376`;
`git branch -r --contains a482376` returns `origin/main`. The one condition the
entry above left open ("push `a482376`, then flip to done") is met, so this
item is `done` and its `evidence_found` note — which still read *LOCAL ONLY,
NOT pushed* — has been corrected on the same SHA.

Note what closed this item: **a fetch, not a report.** The paragraph above,
written by a session that could see the commit locally, would have rendered as
"not pushed" forever to anyone who trusted it instead of the remote. The
correction cost one `git fetch`.

**Next:** nothing. `closed_origin` is `inferred` — a machine judged this
finished off the remote ref, not Marcelo. If that judgement is right, confirming
it costs one sentence.

**Ruled out:** nothing new.

**Reached:** `engineered-lighting-site` (fetched, `a482376`), `gimbal-bench`
(GitHub API, `master` @ `9549189`). · **Could not reach:** `formd-t1` — the
bench PC is not this laptop and product-os is not installed there.
