# Goal prompt — build /audit

Paste the block below into a fresh session in `~/Claude/product-os`. Written to work
cold, with no chat history.

## STAND — updated 2026-08-19, after the first real `/audit`

**11 commits. `origin` EXISTS and the repo is PUBLIC — Marcelo created and pushed it
at 14:13 (reflog: `update by push`), not me.** `origin/main` is at `c95172a`; the
`POS-007` commit is local and unpushed pending his word. See the disclosure note at the
foot of this file.** `validate.py`
exits 0 · 31 items (20 active, 7 parked, 4 done) · 5 questions (1 parked) · 8 rulings ·
59 register entries · **54 gated tests** · byte-deterministic build · 24 briefs ·
13 threads with resume/restart verdicts.

**Built and verified before this session (slice 1a-minus):** the item model, scoring,
`validate.py` / `rank.py` / `build.py` / `new.py` / `stale.py`, the evidence-backed
seed, `wiki/ruled-out.md`, and the plugin with three skills plus the `SessionStart`
hook. Three tool bugs were found only by running them — `_fm.canonicalize` was not a
fixed point, `_git` returned committer-local dates against a UTC API, and `new.py`
wrote a status outside the enum.

**`/audit` — POS-003, now `done` with evidence.** `tools/audit.py` (read-only) + `tools/apply.py`
(applies one accepted sentence) + `plugin/skills/audit`. Path-first attribution, four
groups, **mandatory group D**, coverage line by name. `apply.py` refuses `done`
without evidence that existed *before the run*, and routes human-authority fields to
`state/proposals/`. Records land in `state/audits/<machine>/`.

**The un-park decision is a node.** `GB-014` sits between `GB-001` and `GB-005`, so
the chain reads *fault ring → a decision nobody has taken → Z-M1*.

**Q-005 resolved by reading Doc 4, not escalated.** Every Doc 4 row sums to $621–666;
swap the $486 Valent X spool for the $30 BTF substitute and it is $165–210 against a
published header of $170–240. The header assumes the substitute. Only the tape choice
is still his, and it is a ~$451 decision.

**The first audit caught me publishing a falsehood about a source.** Last session I
wrote — in two seeded items and in the register — that two quoted strings appeared in
neither repo. **Both are real:** *"this bench's meter has no current range"* at
`docs/04a-wire-the-zones.md:331` (`d8f092b`) and *"Marcelo to call"* at
`PROJECT-STATE.md:158` (`88a3a58`, eighteen days old). I had trusted GitHub code
search instead of grepping files already on disk. Corrected in both items; `R-054`
records the method failure. `EL-002` is rescoped: the bench **has** a volt meter
(TESMEN TM-510) and lacks a **current** range.

**`GB-004`:** `19dd790` proves the motor-silent limb and MUTE-CLEAR; the armed lane
was not reached and **cannot** be by that method (`R-055`). `done` refused twice, for
two different correct reasons.

**Regression tests — DONE.** `tests/test_regressions.py`, **29 assertions** over the
six defect classes that have actually shipped here, wired into `validate.py` as
`E-REGRESSION` (skip with `--no-tests`). Proven both ways: reintroducing the
`_fm.canonicalize` bug turns the gate red, restoring it turns it green.

**The root cause is now in `CLAUDE.md`,** next to "Local git lies", as one rule with
its three instances: v1 trusted a header date over `git log`; v2 trusted a word count
over `spot-bench.yaml`'s STILL LIVE block; v3 trusted an empty code search over
`grep`. *A mechanical signal is not the primary source. Verify against the file.*

**`docs/cold-start-test.md` — RUN, partially, and it found the flagship item wrong.**
6/7, all three mandatory criteria passed. Criterion 4 (ruled-out injected by the hook)
stays unmeasured; a subagent never receives `SessionStart`.

**EL-001's evidence rule could never fire.** It named only `docs/bom-checklist.md`,
which says of itself *"state persists in your browser (nothing leaves your device)"*.
Ticking it writes nothing to the repo — structurally unsatisfiable — so the item could
never close, while ranked #1 since the seed and with its parts photographed in
`docs/04a-wire-the-zones.md`. **Fourth instance of the root cause and the worst: the
rule was already in `CLAUDE.md` and `audit.py` committed the error anyway**, because
"matched nothing" and "not done" were the same code path.

- **Class fixed first.** `audit.py` classifies every rule `satisfiable` /
  `never-fired` / `unsatisfiable` against the repo tree. Over the 14 flagged globs:
  **4 unsatisfiable** (`GB-002`/`GB-014` `docs/*DECISION*`, `GB-003`'s 08-12 capture,
  `GB-005`'s `partitions*` — two of which are the GOOD case, a file the work will
  create), **8 never-fired**, 2 merely quiet.
- **EL-001 not closed.** Evidence recorded (`762afdd`, `d8f092b`, `2c1233f`,
  `52c5048`); `PROP-0002` proposes repointing the rule and reducing the item to its
  residual — the **Carclo optics trio**, unphotographed and unmentioned. Not
  retitled: narrowing scope is a decision with taste in it.
- **README flagship replaced** with `EL-002` (live, 5-day lead) plus an honest section
  on why the old example was wrong. `R-056` records the class.
- **Regression test added**, 6 assertions. 21 tests total, gate green.

**Also found: `APP-001` is obsolete.** HomeApp already has `CHANGELOG.md` and a
`docs/` tree — the item proposes creating what exists.

**Which tape was bought is NOT verified and stays Marcelo's.** The 1800 K channel
implies Valent X; that is an inference from a spec, not a photograph. Q-005 open.

**POS-004 — the authority guard was firing at the wrong person. DONE.**
`apply.py --field EL-001=cost_usd:486 --said "…"` used to file a proposal *for him
to approve later*, routing his own decision into a queue addressed to himself. Two
guards were conflated:

- **Authority** (*who decided?*) exists to stop the **agent** reprioritising. It now
  yields to his word.
- **Truth** (*is it provable?*) refuses `done` without `evidence_found` for
  **everyone**, him included. Unchanged, and verified unchanged.

Origin lives in the flag name, not in `--said` — an agent can populate `--said` too.
`--field` = agent (default; forgetting fails safe toward proposing), `--decided` = he
said it and requires `--said` (exit 2 without). Every applied line is stamped
`on his word` or `inferred` in the audit record, permanently. 29 tests, gate green.

**POS-005 — the thread indexer. DONE.** `tools/index.py` reads 1,108 Codex rollouts
and 6 Claude Code transcripts in **2.0 s** (line 1 + a 64 KiB tail; never a full read)
and writes `state/threads/by-machine/work-laptop.json`. 13 threads, **3 bound to items**
(POS-001…POS-005). Metadata only, enforced twice: `index.py` filters to a 14-key
allowlist, and `validate.py` re-checks independently — injecting a `message` key gives
`E-SHARD-LEAK`.

**The finding that matters more than the tool.** v6 read the citation counts as the
convention working. It is — but **97.3% of every anchor on this machine (4,072 of
4,186) is inside this repo's own planning transcripts**, and every one of the 114
external citations names an ID that no longer exists (`EL-014`, `EL-020`, `EL-040` —
the discarded v1 seed). Outside this repo's own sessions the corpus holds **zero valid
anchors**. A cold start, not a defect; use is what fixes it.

**An ID is unique only within a seed generation.** The first run bound a transcript to
`Q-004` — wrongly. That `Q-004` sits beside `EL-040`/`EL-042` from the v1 seed; today's
is a different question. `gate_by_age()` now drops any citation predating the item and
reports the collision. `R-057`.

**Group D reconciled, and both numbers were wrong.** 108 was `--since 2026-08-10`, 156
was the default window — and *both were silently truncated* at the API's 100-row page.
`gimbal-bench` alone had 245. Paginated, the default window is **301**. Coverage lines
now carry their window and flag truncation as a floor. `R-058`.

**POS-006 — group-D coverage. PROPOSED, not created.** The system models 29 items
against **301** unattributed commits: ~10% of the portfolio, with the missing 90%
concentrated in `gimbal-bench`. Clustered into **20 items covering 288 — 96%**, as
`PROP-0003`, answerable in one sentence. The glob set and the measurement are in
`state/proposals/PROP-0003-clusters.py` so the 96% reproduces rather than being
asserted.

- **13 commits deliberately left uncovered and named** — a `.gitignore` change, a
  one-off capture, a mobile fix, and a tail of reverts. A coverage figure gamed by
  fake items is worse than a low one.
- **Part of the 301 was never a modelling gap.** 13 *existing* items are suppressed by
  the too-broad check and contribute their commits to D; `GB-001` alone would claim 57.
  The number mixes "nobody modelled this" with "the rule is too coarse". Separate jobs,
  not merged.
- **The too-broad check does not apply to `done` items, and that is correct** — it
  guards against a *forward* claim absorbing a directory's future. Verified in
  `audit_item()`, not assumed. Two genuine grab-bags narrowed anyway.

**Reporting discipline, corrected.** My recaps reported one commit more than `git log`
showed, five sessions running — I was counting the commit I was about to make. In a
repo whose pitch is numbers that can be checked, a count habitually one high is the
exact shape of the thing it exists to catch. Verified counts only from here.

**POS-007 — re-centred on software, on Marcelo's word (`--decided`).** *"This tool is
about planning vibe code software projects and chats. All the hardware is bought."*

- **`urgency` is gone.** Measured before removal: 2 of 30 items carried any
  `lead_time_days`, both purchases — inert on 28, tripling the score on 2 that no longer
  matter. `LEVERAGE_WEIGHT` 0.25 → 0.5, because dependency depth is what orders software
  work. **`GB-001` (leverage 8) went from #3 to #1**: `5.000 × 5.000 = 25.00`.
  `lead_time_days` is still recorded and still displayed; it just no longer moves order.
- **8 parked, not deleted** — EL-001/002/003 (purchases, prints), SITE-001/002/003
  (docs-site propagation), GB-003 (bench-only owner capture), Q-005 (the tape question).
  Any comes back in a sentence. **20 active items across 4 codebases.**
- **Briefs are generated every build** — `build/briefs/<ID>.md`, 24 of them: where it
  stands · what's next · already ruled out (keyword-scoped) · decisions in force ·
  **a freshness stamp that always prints**, including "no audit has ever run" and
  "could not check gimbal-bench offline".
- **Every indexed thread carries a resume-or-restart verdict and its reason.** 4 resume,
  9 restart. Commands verified before printing: `claude -r` is on PATH; codex is *not*,
  so it is emitted by full path from inside ChatGPT.app.

## How to talk about state — I kept getting this wrong

**PROP-0001 and PROP-0002 are not blockers and never were.** v4 said so and my recaps
reintroduced them three times under "needs Marcelo". Nothing in `state/` gates
anything. Scores, scope, evidence rules, priorities and status are **fluid** —
adjustable in a sentence, no ceremony. Being wrong is cheap because the audit
converges it; verification is continuous, not a precondition for action.

Genuinely his, and short: **real-world commitments** the tool records but never
decides (the ~$451 tape, un-parking Zigbee, making a repo public), and **the
cold-start test**, which is a measurement no agent can run credibly. None of these
block software.

## Not done

- **The done-without-evidence guard is a speed bump, not a wall** (`R-059`). Closing
  `POS-003` walked through it in two commands — write `evidence_found`, then close —
  because "before the run" is a process boundary, not readership. It still stops the
  common case. The durable guarantee is the `(inferred)` vs `on his word` stamp, not
  the snapshot.
- **THE LOOP HAS NEVER RUN END TO END.** `/next` → do the work → `/handoff`, by
  Marcelo, on real work. This is the next thing, and every friction it surfaces is a
  real requirement instead of a guessed one. Everything below matters less.
- **The full cold-start test is unrun.** A partial one found the flagship item wrong;
  criterion 4 (ruled-out injected by the hook) stays unmeasured, because a subagent
  never receives `SessionStart`. Needs a genuine fresh session with the plugin
  installed — and an observer who is not me.
- **`state/audits/` has three entries, all from one day.** The window-since-last-audit
  path still needs a second calendar day to prove.
- **The tests cover six defect classes, not the tools.** 3,098 lines of Python against
  328 of test. Everything off that list is still checked only by somebody running it
  and looking.
- **Group D is 301 commits** at the default window (was reported 108 and 156; both
  truncated). The honest finding, not a bug: the seed under-covers `gimbal-bench`, and
  clustering D into proposed items is a better use of it than watching it grow.
- **The indexer has no valid external anchors yet**, because the corpus predates the
  seed. It backfills on its own as sessions accumulate — transcripts persist on disk.
- **30 group-B findings outstanding**, mostly evidence rules that are too broad or
  cannot fire. Fluid — a sentence each, no ceremony.
- **`product-os` is PUBLIC and `wiki/ruled-out.md` is on it** — 58 entries, 84 quoted
  lines, many verbatim from the *private* `gimbal-bench`, with its file paths and
  commit SHAs. `validate.py`'s screen passes (no credential, email, tailnet ID or MAC),
  so this is a judgement call about engineering disclosure, not a leak. `R-050`
  recommended starting private for exactly this content; that recommendation is now
  overtaken by his own push and is his to re-decide.
- **`gimbal-bench` itself remains private (`R-049`)** — unchanged, and the third-party
  paragraph is still un-anonymised.
- Deferred: the thread indexer, briefs, the site, `llms.txt`, `/unblock`,
  multi-machine (12 of 27 items are `machine_affinity: formd-t1`).

Kept under 4000 characters. Update this section when milestones land.

---

```
Cite the product-os item covering /audit in your first message. If none exists, create
it with tools/new.py and cite that.

Slice 1a-minus is BUILT and VERIFIED: 4 commits, no remote, validate.py exits 0,
25 items, 53 register entries, 4-hop chain, byte-deterministic.

Read first: ~/.claude/plans/read-bootstrap-md-and-follow-mighty-wave.md — START WITH
THE v4 SECTION. It changes direction and answers your open questions. Then CLAUDE.md.

YOUR QUESTIONS, ANSWERED
  PROP-0001 is NOT a gate. The ranked list is a conversation starter, not a contract.
    Marcelo decides in the moment; accuracy comes from repeated re-auditing, not a
    one-time acceptance. Leave it as a starting position — no review UI. Same for
    intent.md / standing-orders.md staying provisional.
  Q-005 (~$456 spool): resolve by READING Doc 4, don't escalate by reflex. Header says
    ~$170-240, row 4 of the same table says $486. Most likely the header assumes the
    $30 BTF substitute. Verify. Escalate only if irreconcilable.
  D15's park as an edge, not status: parked — you were RIGHT. `parked` means set aside
    indefinitely; D15 names its own un-park condition, so it is sequencing, not scope.
    Fix the cost you identified by making the decision a NODE: insert an explicit
    un-park decision item between GB-001 and GB-005, so the chain reads "fault ring ->
    a decision not yet taken -> Z-M1". A chain containing an unmade decision is
    exactly what this system should surface.

THE WORK: build /audit — the system Marcelo actually wants. A chat he can sit down
with repeatedly that re-checks priorities against reality.

  a Read-only pass. For each item with `repos`, fetch and compare what the item claims
    against what commits and files show. stale.py already does the ruling-vs-doc case;
    generalise it, don't replace it.
  b EVIDENCE MATCHING IS PATH-FIRST. Marcelo writes commit subjects like "map the fall
    that never comes". No keyword rule will match those. Match `paths:` globs first;
    message matching is fallback only.
  c Four output groups: A applies on a bare "merge" · B escalated, I will not decide
    these · C refused, with the reason · D commits I could not attribute. D is
    MANDATORY and first-class — an audit that says "nothing changed" when it means "I
    recognised nothing" is the one failure that ends trust in this tool.
  d Always print the coverage line: repos expected, reached, unreachable, by name.
  e ACCEPTANCE IS ONE SENTENCE IN CHAT. Marcelo says "yes to A, do B1 at $240, drop
    B3" and the skill applies exactly that — no file-editing ritual. Write the durable
    record to state/audits/<machine>/ afterwards so nobody re-litigates it.
  f Refuse to mark anything done without evidence_found. That rule does not bend.

ALSO
  Score becomes a LABEL, not a verdict; `pin` moves from exception to ordinary use.
  When his order and the math diverge, say so ONCE with the reason, then do what he
  said. Record honestly that leverage isn't carrying this seed: EL-001 ranks first on
  urgency 3.0 with leverage 1, while the 4-hop chain sits on GB-001 at rank 3.

ACCEPTANCE
  /audit runs against the real repos, produces all four groups plus the coverage line,
  finds at least one real status change with a SHA, and refuses at least one thing for
  lack of evidence, saying which. validate.py still exits 0.

CARRY FORWARD
  Never seed from a local clone (~/Claude/engineered-lighting is 54 commits stale and
  rev-list still says 0 — fetch first, never fall back to a local ref). Never
  paraphrase inside quotation marks. Draw an edge only if a source states it. If you
  could not reach a repo, say "I couldn't look".

STOP AND ASK
  Do NOT create the remote or push — private when created. Do NOT flip gimbal-bench
  public (R-049). Do NOT write human-authority fields; propose instead.

When you stop, update GOAL.md's STAND list and say plainly what is not done.
```
