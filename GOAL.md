# Goal prompt — build /audit

Paste the block below into a fresh session in `~/Claude/product-os`. Written to work
cold, with no chat history.

## STAND — updated 2026-08-19, after the first real `/audit`

**6 local commits, nothing pushed, no remote.** `validate.py` exits 0 · 27 items ·
5 questions · 8 rulings · 55 register entries · **5-hop** confirmed chain ·
byte-deterministic build.

**Built and verified before this session (slice 1a-minus):** the item model, scoring,
`validate.py` / `rank.py` / `build.py` / `new.py` / `stale.py`, the evidence-backed
seed, `wiki/ruled-out.md`, and the plugin with three skills plus the `SessionStart`
hook. Three tool bugs were found only by running them — `_fm.canonicalize` was not a
fixed point, `_git` returned committer-local dates against a UTC API, and `new.py`
wrote a status outside the enum.

**`/audit` — DONE (POS-003).** `tools/audit.py` (read-only) + `tools/apply.py`
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

**Regression tests — DONE.** `tests/test_regressions.py`, 15 assertions over the four
defect classes that have actually shipped here, wired into `validate.py` as
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

## Not done

- **The cold-start test has never been run.** That is the largest untested claim
  this repo makes about itself, and it needs an observer who is not me.
- **`state/audits/` has one entry.** The second run is the one that proves the
  window-since-last-audit path, and it needs a day to pass.
- **The tests cover four defect classes, not the tools.** 2,706 lines of Python
  and ~180 lines of test. Everything not on that list is still only checked by
  somebody running it and looking.
- **Group D is 99 commits.** Most are genuinely outside the seed's 27 items. That is
  the honest finding, not a bug — but it means the seed under-covers `gimbal-bench`.
- **Nine evidence globs are too broad or match nothing**, reported in group B.
  They are human-authority; proposed, not fixed.
- **No remote. `gimbal-bench` still private (`R-049`).** PROP-0001 still unaccepted,
  which v4 says is fine.
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
