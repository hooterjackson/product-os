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

STAND
  [done] scaffold; CLAUDE.md+AGENTS.md byte-identical; intent.md + standing-orders.md (provisional v0); README
  [done] tools/{_fm,_git,_model,validate,rank,build,new,stale}.py — compile, unrun
  [next] Seed: 6 projects, ~18 evidence-backed items, 5 questions, 7 decisions
  [ ] wiki/ruled-out.md, ~45 keyword-tagged entries
  [ ] plugin/: plugin.json, skills {next,capture,handoff}, SessionStart hook
  [ ] verify end-to-end; local commits only

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
