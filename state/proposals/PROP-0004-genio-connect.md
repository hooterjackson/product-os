# PROP-0004 — genio: 13 items, and the three reasons they will not move group D

**Status:** open. Nothing here has been created.
**Raised:** 2026-08-19, work-laptop, following `public/connect-repo.md`.
**Cites:** `CLAUDE.md` § *A mechanical signal is not the primary source* ·
`CLAUDE.md` § *Refuse to mark anything done without evidence* ·
`public/connect-repo.md` steps 2 and 3.
**Answer in one sentence.** See *The one-sentence answer*.

---

## What is already done, and needs no answer

`genio` is registered in `state/repos.json`. Every field was verified against
the GitHub API rather than assumed:

| field | value | how it was checked |
|---|---|---|
| `owner` | `hooterjackson` | `gh repo view` |
| `local` | `null` | not cloned on work-laptop |
| `default_branch` | `main` | `gh repo view --json defaultBranchRef` — not assumed |
| `authority` | `false` | holds no rulings; `gimbal-bench` keeps that role |
| `public` | `true` | `isPrivate: false` |

**Window: 294 commits since 2026-07-05**, spanning 2026-07-13 to 2026-08-02,
paginated to exhaustion (three pages, the third short — not a capped 100).
57 of the 294 are merge commits. The product is *gênio* / 9enio.com: an AI
playlist builder on Next.js + Postgres, publishing to Apple Music, with an
unusually heavy release-governance and evidence-attestation layer.

---

## The 13 items

Path-attribution measured with `audit.py`'s own `glob_re`, against the real
changed-file lists of all 294 commits (now cached in `.cache/audit/genio-files.json`,
so the first real audit of this repo costs no API calls). **Every glob below is
`SATISFIABLE`** — it matches a path in the tree that commits actually touch. Four
early drafts were `UNSATISFIABLE` and were corrected against the tree, not
guessed.

| id | title | commits | evidence paths |
|---|---|---|---|
| `GEN-001` | Hosted Needle: Railway services, gateway policy and owner access | 58 | `.railway/*.ts` `.railway/*.md` `worker/gateway-policy.ts` `server/gateway-auth.ts` `tests/worker-owner-gateway.test.ts` `tests/worker-security.test.ts` `tests/staging-bootstrap.test.ts` |
| `GEN-002` | Apple Music: MusicKit owner authorization and durable validation | 36 | `app/music-kit.ts` `app/owner/apple-authorization-status.ts` `server/apple-write-gateway.ts` `server/apple-provider-control.ts` `server/apple.ts` `server/apple-smoke.ts` `scripts/apple-publication-smoke.ts` `tests/apple-owner-authorization.test.ts` `tests/apple-publication.test.ts` `tests/apple-write-gateway*.test.ts` `tests/apple-provider-control.test.ts` |
| `GEN-003` | Publication reconciliation: Apple catalog aliases and terminal finalization | 9 | `server/publication-reconciliation-v1.ts` `server/publication-reconciliation-persistence.ts` `server/publication-completeness.ts` `server/publication-completion-fence.ts` `server/partial-publication-policy.ts` `server/apple-catalog-cache.ts` `server/catalog-match-recovery.ts` `server/recording-family-selection.ts` `tests/publication-reconciliation-v1.test.ts` `tests/publication-completeness.test.ts` `tests/partial-publication-policy.test.ts` `tests/apple-catalog-cache.test.ts` |
| `GEN-004` | Research durability: fast research, budgets and provider fail-open | 54 | `server/fast-research.ts` `server/research.ts` `server/research-policy.ts` `server/research-resume.ts` `server/guidance-scout-budget.ts` `server/cost-config.ts` `tests/research-integrity.test.ts` `tests/research-policy.test.ts` `tests/research-resume.test.ts` |
| `GEN-005` | Public site: playlist directory, minimalist flow and the gênio rebrand | 34 | `app/playlists/*.tsx` `app/brand-intro.tsx` `app/brand-wordmark.tsx` `app/public-site-header.tsx` `app/primary-nav.tsx` `app/site-menu.tsx` `app/option-one.css` `app/about/*.tsx` `app/privacy/*.tsx` `app/working-indicator.tsx` `app/playlist-waiting-state.ts` `tests/working-indicator.test.ts` |
| `GEN-006` | Private feedback inbox and owner console | 24 | `server/feedback.ts` `app/feedback/*.tsx` `app/owner/owner-console.tsx` `app/owner/page.tsx` `tests/feedback.test.ts` `tests/feedback-repository.test.ts` `tests/e2e/feedback.spec.ts` `tests/e2e/owner-feedback.spec.ts` |
| `GEN-007` | Pipeline V2: the relevance-first curated pipeline and its shadow run | 30 | `server/pipeline-v2-*.ts` `server/selection-plan-v2.ts` `server/pipeline-outcome-v2.ts` `shared/selection-score-v2.ts` `lib/pipeline-v2-release-benchmark.ts` `scripts/evaluate-pipeline-v2-*.ts` `tests/pipeline-v2-*.test.ts` `tests/selection-plan-v2.test.ts` `tests/selection-score-v2.test.ts` |
| `GEN-008` | Pipeline V3: governed discovery, retrieval and worker execution | 96 | `server/pipeline-v3-*.ts` `server/query-plan-v3.ts` `server/selection-plan-v3.ts` `server/v3-activation-bridge.ts` `server/adaptive-fill-v3.ts` `server/music-concepts-v3.ts` `scripts/evaluate-pipeline-v3-benchmark.ts` `scripts/pipeline-v3-benchmark-lib.ts` `tests/pipeline-v3-*.test.ts` `tests/query-plan-v3.test.ts` `tests/selection-plan-v3.test.ts` `tests/v3-activation-bridge.test.ts` |
| `GEN-009` | Guidance contract: adaptive guidance V2-V5 and intelligent follow-ups | 53 | `server/adaptive-guidance-*.ts` `server/guidance-context.ts` `server/guidance-contract-v2.ts` `server/brief-*.ts` `server/custom-guidance-artist-resolution-v1.ts` `server/music-intent-*.ts` `server/music-concept-registry-v1.ts` `tests/adaptive-guidance-*.test.ts` `tests/brief-policy.test.ts` `tests/guided-brief-job.test.ts` |
| `GEN-010` | Fixed track lists: exact identity, membership order and count integrity | 36 | `server/fixed-track-list-policy.ts` `server/fixed-container-resolution-proof-v1.ts` `server/exact-artist-identity-v1.ts` `server/playlist-count-policy.ts` `server/playlist-contract-*.ts` `server/playlist-resolution-service-v1.ts` `server/playlist-feasibility-v1.ts` `server/never-dead-end-policy.ts` `tests/fixed-*.test.ts` `tests/playlist-contract-*.test.ts` |
| `GEN-011` | Evidence and proof architecture: schema 19/20, attestation and integrity | 41 | `server/schema20-proof-architecture.ts` `server/evidence-*.ts` `server/citation-attestation.ts` `server/canonical-*.ts` `server/manifest-*.ts` `server/verification-expression-v1.ts` `server/resolution-facts-v1.ts` `server/strategy-delta-proof-v1.ts` `scripts/backfill-schema20-proof-architecture.ts` `scripts/activate-schema20-proof-authority.ts` `postgres-migrations/*.sql` `tests/schema20-*.test.ts` `tests/evidence-*.test.ts` |
| `GEN-012` | Release governance: canaries, signed artifacts and the offline gate | 57 | `.github/workflows/*.yml` `.github/release/*.Dockerfile` `scripts/release-*.ts` `scripts/authorize-*.ts` `scripts/verify-*.ts` `scripts/stable-*.ts` `scripts/prepare-*.ts` `scripts/*-release-*.ts` `shared/release-*.ts` `shared/signed-artifact.ts` `shared/sites-*.ts` `shared/staging-*.ts` `server/release-*.ts` `server/runtime-release.ts` `tests/release-*.test.ts` `tests/stable-*.test.ts` `tests/runtime-release.test.ts` `tests/sites-*.test.ts` |
| `GEN-013` | Public rollout: V2/V3 cohort assignment and owner canaries | 20 | `server/public-rollout-assignment.ts` `shared/public-rollout-*.ts` `scripts/apply-public-rollout-cohort.ts` `scripts/public-rollout-*.ts` `tests/public-rollout-*.test.ts` |

Counts overlap (a commit touching `server/research.ts` and `server/pipeline-v3-retrieval.ts`
is claimed by two items), so the column sums past the distinct total.

**Proposed for all thirteen:** `impact: 3`, `confidence: 4`,
`effort_minutes: 240`, `status: done`, `gate: none`, `machine_affinity: null`,
`lead_time_days: 0`, `cost_usd: null`, `unblocks: []`, `project: genio`,
`repos: ["genio"]`.

These are **historical workstreams, not new work.** None asks you to do
anything. As with `PROP-0003`, `done` is in `_model.ACTIVE_EXCLUDED`, so the
three numbers are inert — they are recorded and never read by `ranked()`.

---

## Coverage, as a fraction — and the fraction is not the one you want

**Path-attributable: 247 of 294 — 84%.** Before these items: 0.

**Group D reduction: 0.** That is not a typo, and it is the finding.

I ran the experiment rather than reasoning about it: a throwaway `genio`
project and item, in a scratch copy of this repo, with real globs. Three runs:

| item | globs matched | group D for genio |
|---|---|---|
| `status: done`, narrow globs | 5 | **294** (unchanged) |
| `status: next`, broad globs (90 commits) | 90 | **294** (unchanged) |
| `status: next`, narrow globs | 5 | **289** |

`audit()` builds group D from *reported SHAs* — `for f in findings: for sha in
f.shas` — and there are exactly two ways a SHA gets reported: a group-A "record
N commits as evidence_found" finding, or a group-C failure. `audit_item()`
returns from the `if node.status == "done"` branch before any group-A finding is
built, and returns from the `len(fresh) > BROAD_GLOB_COMMITS` branch without
SHAs. So a healthy `done` item reports nothing, and a too-broad live item
reports nothing.

**A `done` item can never shrink group D. A live item can shrink it by at most
12.**

### This makes `PROP-0003`'s headline arithmetic wrong

`PROP-0003` proposes twenty items, all `status: done`, and states: *"yes to
PROP-0003 creates all twenty and drops group D from 301 to 13."* By the
measurement above it drops group D by **zero**. Even if all twenty were live,
the ceiling is 20 × 12 = 240, not 288. The `301 → 13 (96%)` in commit `c95172a`
and on the item `POS-006` is not a number this tool can produce.

I have not touched `PROP-0003` — it is yours. But it should not be accepted on
that sentence.

### And it is unreachable for genio at any item count

`BROAD_GLOB_COMMITS = 12` was calibrated on this portfolio's hardware repos.
genio commits 6.5×/day. **68 of the 572 files touched in the window individually
exceed 12 commits.** `server/repository.ts` is 111, `server/research.ts` is 46,
`app/owner/owner-console.tsx` is 20. There is no glob — not even a single bare
filename — that describes the research work in ≤12 commits. Splitting `GEN-004`
into five items would produce five items that describe nothing, which is exactly
the gamed number `connect-repo.md` step 4 warns against.

So I did not split them. **84% path-attribution with 13 honest items is the real
number; a 96% group-D figure is not available at any price.**

---

## Three defects in `connect-repo.md` itself

**1 · "No code changes anywhere. `audit.py` iterates whatever is configured."
Both halves are false.**

`audit()` does not read `state/repos.json` for its repo set. It builds `wanted`
from item `repos` fields and decision `propagates_to` targets, then looks each
one up in `repos.json`. Registering genio and running `tools/audit.py` leaves it
**absent from the Coverage line entirely** — neither *reached* nor
*unreachable*, which is the one outcome step 3 says must not happen. Verified:
before the fixture item existed, Coverage read `HomeApp,
engineered-lighting-site, gimbal-bench, product-os`; with it, `... genio ...`.

So **step 3 cannot be satisfied by step 1**, and the doc's own acceptance test
fails on a correctly-followed run.

**2 · A new project prefix needs three code edits.** `tools/_fm.py` hardcodes
`ID_RE`, `MENTION_RE` and `PREFIX_PROJECT` to the live prefix set. `GEN` is not
in them, so `GEN-001` fails `validate.py` and is invisible to the thread
indexer's `MENTION_RE` — the one mechanism `CLAUDE.md` calls the most important
line in the file. `CLAUDE.md` and `AGENTS.md` (byte-identical, enforced) also
carry the prefix list.

**3 · The published `301` was stale.** `public/connect-repo.md` served **301**
while `tools/audit.py` measured **323**. The number comes from
`build/audit-stamp.json`, so it is only as fresh as the last `publish.py` — and
the doc that tells you to run `publish.py` is itself the thing that goes stale.
Re-running it corrected this; no decision needed.

### What I am not doing about them

Making `audit()` iterate `repos.json` would be a two-line change, and it would
immediately add genio's 294 commits to group D on top of the existing 323. That
changes the denominator of the one honest signal in this system, portfolio-wide.
`CLAUDE.md` says escalate rather than resolve when a change has cross-project
consequences, so it is here, not in a commit.

The wording fix in `tools/actions.py` is also held, because the right wording
depends on which way you decide (1): if `audit()` starts iterating `repos.json`,
the sentence becomes true and needs no edit.

---

## What I could not model, and did not invent items for

**47 commits, left unattributed.** Naming them beats gaming the number:

- **6 merge commits** with no file delta of their own (`57184b9`, `b6051ef`,
  `b5bc2cd`, `6ca9bef`, `d028f78`, `5b12109`). An item for a merge is
  meaningless. Note `audit.py` counts these only for API-mode repos — the local
  path passes `--no-merges`. genio is API-mode, so its group D carries 57 merge
  commits the same repo would not contribute if it were cloned here. That
  asymmetry is worth a look and is not something I should silently normalise.
- **~14 release-chore commits** (`a6d84cd` "chore: release v2.4.1", `6c9606f`
  "chore: package Sites release artifact") that touch only `package.json` and
  `shared/releases.json` — the two highest-churn files in the repo, at 89 and 80
  commits. Any glob claiming them claims a third of the repo.
- **~13 cross-cutting diagnostics from the 2026-07-28 burst** ("chore: classify
  canonical preflight failures", "chore: expose safe worker failure origins").
  They touch `server/error-sanitizer.ts` and `server/repository.ts` across every
  subsystem at once. They belong to no workstream; they *are* a workstream, but
  one whose only honest evidence path is a file three other items already claim.
- The remainder are one-file corrections and test stabilisations.

---

## The one-sentence answer

**"Yes to PROP-0004"** creates thirteen `done` items describing 84% of genio's
294-commit window, at `impact: 3`, `confidence: 4`, `effort_minutes: 240` —
inert numbers on excluded items — and **leaves group D exactly where it is**,
because nothing in this tool lets a finished item shrink it.

If that last clause makes the items not worth carrying, the honest alternative
is **"register genio, skip the items"**: the repo is configured, the commit
cache is warm, and the first person to work in genio gets a real audit for free.

Three separate answers I would rather have than a blanket yes:

1. **Should `audit()` iterate `state/repos.json`?** Yes makes the doc true and
   adds 294 to group D. No means `connect-repo.md` step 1 needs rewriting.
2. **Should `done` items shrink group D?** Today they cannot, and `PROP-0003`
   is priced as though they can.
3. **Is `BROAD_GLOB_COMMITS = 12` right for a repo at 6.5 commits/day?** It is
   a per-item cap on how much reality one item may claim, and genio's single
   files breach it.

Mine either way: titles, repos, keywords, evidence paths, and every number
above. Yours: the three decided numbers, the `genio` project and its `GEN`
prefix, and whether any of this exists at all.
