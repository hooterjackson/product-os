# Goal prompt — finish product-os slice 1a-minus

Paste the block below into a fresh session in `~/Claude/product-os`. It is written to
work cold, with no chat history, because that is the failure this repo exists to fix.

Kept under 4000 characters. The `STAND` list is the only part that goes stale —
update it when you stop.

---

```
Cite POS-001 in your first message. Continue building product-os slice 1a-minus in ~/Claude/product-os.

READ FIRST
  ~/.claude/plans/read-bootstrap-md-and-follow-mighty-wave.md  the approved plan (v3)
  ./CLAUDE.md  the contract you work under
  ./GOAL.md    this prompt; fix its status list when you stop

STAND  (updated 2026-08-19; 4 local commits, nothing pushed, no remote)
  [done] scaffold; CLAUDE.md+AGENTS.md byte-identical; intent.md + standing-orders.md (provisional v0); README
  [done] tools/*.py — now RUN, not just compiled. Three bugs found by running them: _fm.canonicalize was not a fixed point (every file new.py wrote would have failed the canonical check); _git returned committer-local dates while the API returns UTC (silent off-by-one-day in stale.py's only number); new.py wrote questions with status "open", not in the enum.
  [done] Seed: 6 projects, 25 items, 5 questions, 8 rulings. validate.py exits 0; rank.py orders; build.py reports a 4-hop confirmed chain and is byte-deterministic; every entity carries evidence. PROP-0001 stands behind every decided field — UNACCEPTED, awaiting Marcelo.
  [done] wiki/ruled-out.md, 53 entries, each with keywords + source + date + grade; passes the disclosure screen
  [done] plugin/: plugin.json, marketplace.json, skills {next,capture,handoff}, SessionStart hook. hooks.json NESTED. /capture asks nothing, run end-to-end.
  [done] verify: lead-time arithmetic published in README (30.00 vs 4.00, operands shown); stale.py reproduces Doc 7 @ 24d and Doc 6 @ 13d behind D3 unaided, with coverage line; authority audit proven both ways (exit 1 unblessed, exit 0 with Accepts:, agent-authority keywords change passed unremarked)

  [ ] NOT DONE — needs Marcelo
      - PROP-0001 is unaccepted. Every score, cost, edge and gate in state/ is a
        proposal wearing a value. Read it before trusting a ranking.
      - intent.md and standing-orders.md are still "provisional": true.
      - Q-005 (does Doc 4's $170-240 assume the $30 substitute, not the $486
        spool?) gates EL-001's real cost. Two readings, ~$456 apart.
      - The remote does not exist. Private when created — see R-050.
      - gimbal-bench publication still BLOCKED — R-049.
  [ ] NOT DONE — deferred by scope
      - /audit's proposal engine, the thread indexer, briefs, the site,
        llms.txt, /unblock.
      - Multi-machine is untested. Its real test needs formd-t1, and 12 of 25
        items carry machine_affinity: formd-t1.
      - wiki/ruled-out.md's real audience is at the bench. It is on this Mac.
      - No fresh-session test yet: nobody but me has been asked what to work on.

Work in order. A milestone is done only when its test passes:
  seed       validate.py exits 0; rank.py returns an ordering; build.py reports a confirmed chain >=3 hops; every item has evidence with a real path+SHA
  ruled-out  every entry has keywords, source, date, and passes validate.py's disclosure screen
  plugin     hooks.json uses the NESTED {"hooks":{...}} form; /capture asks nothing
  verify     publish the arithmetic behind the lead-time claim (rank.py --show ID); stale.py reproduces the Doc 6/D3 contradiction unaided, with its coverage line

RULES — two earlier plan versions were broken by review, both for trusting a mechanical signal over the primary source:
 1 Never seed from a local clone. ~/Claude/engineered-lighting is 54 commits stale and `git rev-list --count HEAD..origin/main` still says 0. Read remotes: gh api repos/hooterjackson/REPO/contents/PATH --jq .content | base64 -d. gimbal-bench is PRIVATE, branch `master`.
 2 Never paraphrase inside quotation marks. v2 shipped a composite quote that existed nowhere. Can't find the string? Don't quote it.
 3 A word count is not a decision. "Doc 6 has 11 ESPHome lines" is not "retire Doc 6" — spot-bench.yaml marks Doc 6's watchdog/failsafe/presets STILL LIVE. Scope retirement to wifi:/api:/mqtt: as TRANSPORT only. engineering-site items may never rule anything; each is parented to a gimbal-bench ruling ID.
 4 Zigbee is RULED (D3, 2026-08-14) AND PARKED (D15). Not dead, not next. D15's successor is the fault ring (M5).
 5 Publish arithmetic, never a bare ratio. v1 printed a wrong number; v2 printed "27x" with no operands.
 6 Draw an edge only if a source states it. Inferred ones go in unblocks_inferred — excluded from leverage, never forces blocked.
 7 Nothing is done without evidence_found. If you couldn't reach a repo, say "I couldn't look", never "no changes".

STOP AND ASK
 - Do NOT flip gimbal-bench public. Authorized but BLOCKED: a capture names a third party's personal email beside a tailnet incident, no sign they were told. Plan §6.
 - Do NOT create the remote or push. product-os starts PRIVATE — ruled-out.md seeds ~45 findings from the private repo. Commit locally; ask first.
 - Do NOT write human-authority fields (impact, confidence, effort_minutes, lead_time_days, cost_usd, unblocks, pin, project, gate, dropped/parked, evidence rule, intent.md, standing-orders.md). Propose instead.

When you stop, update GOAL.md's status list and say plainly what isn't done.
```
