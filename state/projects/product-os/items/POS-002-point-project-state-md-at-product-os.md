---
{
  "id": "POS-002",
  "title": "Point PROJECT-STATE.md at product-os",
  "project": "product-os",
  "status": "doing",
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
      "note": "LOCAL ONLY -- committed on work-laptop, NOT pushed. main is 1 ahead of origin/main. The pointer does not exist for any other machine until this is pushed, which is why status is doing and not done."
    }
  ],
  "repos": [
    "engineered-lighting-site",
    "product-os"
  ],
  "parent_ruling": null,
  "created": "2026-08-19",
  "updated": "2026-08-19"
}
---

**The single most likely way this repo fails is by becoming state file number
nine** in a portfolio that already has eight, each confidently disagreeing with
the others.

`PROJECT-STATE.md` is the incumbent. It opens by telling every agent on every
machine to read it first, and it is already demonstrably wrong in both
directions: its header says 2026-07-31, and it lists as "pending" two prompts
that had shipped ten days earlier (see EL-004).

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
