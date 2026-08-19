# Prompt · Build `product-os` — the priority + context control plane

*Paste into Claude Code in **plan mode**. Run from a NEW empty directory:*
*`mkdir -p ~/Claude/product-os && cd ~/Claude/product-os && git init`*

*Prerequisite reading before you plan — do not modify either:*
*`~/Claude/engineered-lighting/PROJECT-STATE.md` (a single-project, single-machine*
*v0 of exactly this) and `~/Claude/PICKUP.md`.*

---

# 0 · Read this before you plan

## Who I am and what's broken

Solo maker. A portfolio of interlocking projects, executed almost entirely
through AI chats — Claude Code, the Codex app/CLI, claude.ai — **across multiple
machines**. Live workstreams:

- LED wiring for the fixture (hardware, bench)
- ESP32 firmware talking Zigbee (firmware)
- Gimbal smooth motion — firmware on CAN servos
- Fixture control in the Home App — `github.com/hooterjackson/HomeApp`
  (real repo: Python + JS, `ha-config/`, `addons/`, `predictor/`, sim mode)
- Upgrading the AI models running in my home (infra/ops, **no git repo**)
- The robotic-spotlight build — `github.com/hooterjackson/engineered-lighting-site`,
  published at engineering.engineered.lighting

Six problems:

1. **Priority drift** — no single place says what's next.
2. **Context loss** — every chat starts amnesiac; dozens of live threads, no map.
3. **Invisible dependency chains** — Home App is gated on Zigbee firmware, which
   is gated on LED wiring. I can't see that, so I work on whatever's top of mind
   instead of what's furthest upstream.
4. **Machine fragmentation** — chat history never travels between my machines.
5. **Physical reality** — parts ship in two weeks whether or not I'm ready; half
   my work needs the bench, the printer, or the GPU box.
6. **Lost knowledge** — I re-derive things I already established, especially
   dead ends, because they died with the chat that found them.

## The authority model — the most important section in this document

**I am the orchestrator. That's the value I bring. Do not build an autopilot.**

The system **never changes a priority. It changes a proposal.** Keep computed
and decided permanently separate:

- **Computed** — scores, leverage, lead-time math, reasoning. Agents write freely.
- **Decided** — the actual ranking. Changes only when I accept a proposal.

`/audit` does not reprioritize. It opens a **proposal** — a diff with reasoning
per line — that I merge, amend, or reject. Four mechanisms make this leverage
rather than overhead:

1. **`intent.md`** — I write it; every proposal must defer to and cite it. The
   highest-leverage 200 words in the system.
2. **`standing-orders.md`** — my judgment, made reusable. When I override a
   proposal, ask: *one-off, or a new standing order?* My taste must compound.
3. **A decision queue** — the AI **escalates uncertainty instead of resolving it
   silently**: scores within ~10%, cross-project consequences, anything
   contradicting intent, anything spending money. Everything unambiguous it just
   handles. That ratio is the whole game.
4. **Decisions recorded with my reasoning**, fed back into future proposals, so
   the queue shrinks over time to only genuinely hard calls.

**Never automate:** setting intent · tradeoffs with taste in them · spending
money · anything irreversible · declaring something *good* rather than complete.

**Always automate:** status truth · recomputing rank · assembling context ·
writing handoffs · detecting stalls and drift · compiling knowledge from chats.

## Where the intelligence comes from — no API integration

Be deliberate about this split; it determines reliability:

- **Plain code** (deterministic, free, always right): thread indexing, scoring,
  transitive leverage, critical path, Monte Carlo, site build, stock lookups.
  **Never ask a model to compute a critical path.**
- **Model, from an interactive session I'm already in**: triage, wiki
  compilation, brief writing, audit reasoning, proposals, narrative generation.

**v1 requires no API key and no unattended execution.** The "morning brief" is
an on-demand `/audit` I run when I sit down. Phase 2 may add a local `launchd`
job running `claude -p` (existing local auth, still no key). GitHub Actions +
`anthropics/claude-code-action` is phase 3 and optional.

## Everything is public

Public repo, public site, no auth. Don't design around secrecy — but never copy
transcript *content* into the repo (metadata only), never index `.env`, and gate
CI on a secret-shaped-string check.

---

# 1 · Multi-machine architecture — the constraint everything else obeys

Git is the transport. That works only if conflicts are **structurally
impossible**, not merely rare.

**Rule 1 — machine-derived data is sharded, never shared.**

```
state/threads/by-machine/
  work-laptop.json     ← ONLY work-laptop's indexer writes this
  studio.json          ← ONLY studio's indexer writes this
```

The build merges all shards. Two machines syncing the same day touch different
files. A single shared `index.json` means each sync silently destroys the
other's history — do not do that.

**Rule 2 — one file per entity.** One file per item, project, decision, audit,
question. Never a monolithic board file with a global ordering. (This is also
why rank is *derived* from scores rather than stored.)

**Machine registry** — `state/machines.yaml`, the one shared file the indexer
touches, and only on first run:

```yaml
- id: work-laptop
  hostname: MLKXRRW1494F    # my hostnames are opaque corporate strings —
  os: darwin                # the friendly id is what the UI shows
  registered: 2026-08-18
  last_sync: 2026-08-18T22:40:00Z
```

Resolve identity: `$PRODUCT_OS_MACHINE` → hostname lookup in `machines.yaml` →
prompt me to name and register it.

**Every thread record carries `machine`; resume commands are machine-qualified.**
I can't resume a studio thread from my laptop, so the UI must say *"resume on
**studio**"*. Telling me which machine to walk to is a feature.

**Sync discipline lives in the plugin, not my head.** Every write skill does
`git pull --rebase` before writing and `push` after. `/handoff` and `/audit` run
the indexer and commit this machine's shard as part of normal flow.

**New-machine bootstrap is two commands** — so **the plugin ships inside this
repo** (`plugin/`), not hand-installed:

```bash
git clone https://github.com/hooterjackson/product-os.git ~/Claude/product-os
cd ~/Claude/product-os && ./tools/install.sh
```

`install.sh`: symlinks `plugin/` into `~/.claude/`, writes Codex config,
registers the machine, runs the indexer, prints `/next` as proof. Idempotent.

---

# 2 · Repo layout — two axes, not one

My projects **overlap**. Zigbee serves both the fixture and HomeApp; CAN
knowledge spans gimbal and firmware. Silo context per project and cross-cutting
knowledge duplicates, then diverges, then lies. So:

**Projects are vertical. Knowledge is horizontal.**

```
product-os/
  CLAUDE.md · AGENTS.md          ← byte-identical; read-first contract
  intent.md                      ← MINE. Portfolio intent. Root authority.
  standing-orders.md             ← MINE. Rules applied everywhere.
  README.md

  state/
    machines.yaml
    now.md                       ← GENERATED. The single current focus.
    queue.md                     ← GENERATED. Decisions awaiting my call.
    inbox/                       ← raw captures, untriaged, unranked
    proposals/                   ← GENERATED. Pending diffs for my review.
    questions/                   ← open questions (FIRST-CLASS — see §5)
    decisions/                   ← cross-project calls, with MY reasoning
    audits/                      ← one file per /audit, append-only
    threads/by-machine/*.json    ← GENERATED per machine
    threads/manual.yaml          ← web/cloud chat URLs
    money/                       ← budgets, spend, per project
    inventory/                   ← what's physically on the shelf

    projects/<slug>/
      README.md                  ← what it is, north star, current phase
      intent.md                  ← MINE. Project-scoped.
      standing-orders.md         ← MINE. Project-scoped.
      state.md                   ← GENERATED by /audit. Ground truth.
      items/*.md
      decisions/*.md
      brief.md                   ← GENERATED. Project cold-start bundle.

  wiki/                          ← HORIZONTAL. Compiled from chats.
    index.md
    ruled-out.md                 ← THE RULED-OUT REGISTER (see §5)
    can-bus.md · zigbee-pairing.md · esphome-patterns.md · petg-printing.md

  plugin/                        ← the Claude Code plugin, versioned with data
  schema/*.schema.json
  tools/                         ← install, index, build, validate, forecast
  site/
```

Projects to create: `robotic-spotlight`, `engineering-site`, `home-app`,
`home-ai-infra`, `product-os`.

**Each project gets its own endpoint** — `/robotic-spotlight/llms.txt` — so I
can start a chat scoped to one project without dragging the portfolio into the
context window.

---

# 3 · The item model

```yaml
id: EL-014                 # <PREFIX>-<padded int>, never reused
title: Order 3× RMD-L-5005 from Dings Motion
project: robotic-spotlight
status: inbox | next | doing | blocked | done | dropped | parked
lane: hardware | firmware | app | infra | content
gate: none | awaiting-parts | bench | printer | gpu | external
machine_affinity: null     # null = anywhere
impact: 5  effort: 2  confidence: 4      # 1–5
effort_minutes: 5          # for time-boxed selection (§7)
cognitive_load: low        # low | medium | high — for energy matching (§7)
lead_time_days: 14         # calendar latency once started. THE key field.
cost_usd: 322              # money is a modeled constraint
unblocks: [EL-020, EL-021]
blocked_by: []
answers: [Q-007]           # open questions this would resolve
pin: null                  # integer forces position; my gut overrides math
keywords: [rmd-l-5005, dings, can servo]     # thread auto-attach
evidence:
  - kind: git              # git | file | url | manual
    repo: engineered-lighting-site
    match: "order|dings|5005"
repos: [engineered-lighting-site]
threads: []                # auto-populated: cc:<uuid> | cx:<uuid> | url:<...>
created: 2026-08-18
updated: 2026-08-18
```

Body: why it matters, acceptance notes, and a `## Handoffs` section that
`/handoff` appends dated, machine-stamped entries to.

## Ranking is derived, never an ordered list

```
leverage = items reachable downstream through `unblocks`  (TRANSITIVE)
urgency  = 1 + (lead_time_days / 7) / max(effort_hours, 0.25)
score    = (impact × confidence) / effort × (1 + 0.25 × leverage) × urgency
```

**Transitive leverage, not direct — this is the point.** "Wire the LEDs"
directly unblocks one thing, but that unblocks the Home App, which unblocks
more. True leverage is 4+, not 1.

**The `urgency` term is the differentiator.** Ordering the motors is 3 minutes
and $107 with 14 days of mail time. Every day I don't click buy, the *entire
downstream chain* slides. A conventional board ranks by importance and gets this
exactly backwards. The output should read: *"3 minutes and $322 stand between
you and unblocking 4 workstreams for two weeks."*

`pin` overrides everything. `blocked_by` items not `done` force `status: blocked`
at build time — never offer me something I can't start. `validate.mjs` must
detect dependency cycles and fail loudly.

---

# 4 · Capture and triage

**Capture is dumb and instant. Triage is smart and batched.** Capture asks me
*nothing* — no project, no priority, no estimate. If capture ever asks a
question, capture is broken.

Six paths, one per situation:

1. **Mid-chat, any tool** — "add to backlog: X". Inherits provenance for free
   (which thread, what I was doing). Most common path.
2. **`/capture "..."`** in Claude Code.
3. **Phone** — an iOS Shortcut on the home screen and in the share sheet: tap,
   type or **dictate**, done. Ship the Shortcut definition and setup steps;
   this is not optional, most ideas don't happen at a keyboard.
4. **Site** — a capture box in the same place on every page.
5. **Photo + a few words** from the bench, attached to an item *and to a file*
   (a note on `frame.scad` should surface when someone next edits it).
6. **Bulk source dump** — hand it 15 open tabs or a URL; it reads them, extracts
   what's useful into the wiki, discards the rest. For parts URLs, pull specs,
   price, and stock automatically.

**Captures land in `state/inbox/`** holding only my words and a timestamp. They
do not appear on the board and are not ranked until triaged.

**Triage** (batched, on `/audit` or on demand) infers project, drafts a real
title, guesses scores/gate/cost/lead time/keywords, checks for duplicates,
checks whether it's blocked, and checks whether **I already did it**. Then one
review pass:

```
8 captures triaged
✅ 5 filed as-is — 3 robotic-spotlight, 2 home-app
⚠️  "counterweight = battery pack" conflicts with decision 0004. Revisit or drop?
🔁 "yoke arm fillet" duplicates EL-028. Merged.
✔️  "add calipers to BoM" — already done in 8fb39bf. Closing.
❓ "can the yoke print without supports?" — a QUESTION, not a task. Filed as
   Q-011; it gates three print items, so it's ranking high.
```

**Rules:** never coach me on capture quality — "zigbee thing weird at high
brightness" is a perfectly good capture. Allow duplicates freely. Alarm when the
inbox exceeds ~20 items or anything is older than two weeks (means triage
stopped running, or I'm capturing things I don't want).

**Reference captures are not tasks.** A cable-routing trick from a teardown video
goes in the wiki tagged to frame design and surfaces *when I'm designing the
yoke* — never in the queue.

---

# 5 · Knowledge — organized by re-derivation cost

A knowledge base's only job is **preventing re-derivation**. So effort goes
where recovery cost is highest. Most wikis get this backwards, lovingly
documenting facts and losing dead ends.

| Type | Recovery cost | Treatment |
|---|---|---|
| **Physical measurements** | ∞ — needs the part in hand | Most precious bytes in the repo. Never overwrite without confirmation. |
| **Negative results** | Hours of bench time | `wiki/ruled-out.md` — first-class register |
| **Rationale** | Unrecoverable, only re-litigable | `decisions/`, with trigger conditions |
| **Procedures** | Medium | wiki |
| **Facts** | Low but annoying | wiki, with decay |
| **My taste/priors** | Trapped in my head | `standing-orders.md` + decision reasoning |

Every fact carries **provenance** (`measured` > `datasheet` > `inferred` >
`said-in-chat` — never render these identically), **confidence**, and a **decay
rate** (stock/price decay in days; Ø49 mm never decays — auto-recheck only what
rots). Adopt bi-temporal facts: *when it was true* vs. *when I learned it*.

**Contradiction detection is the core maintenance behavior.** When a session
concludes something conflicting with a page, **flag it into the decision queue —
never silently overwrite.** This is how I catch my own drift.

## The ruled-out register must be a live guardrail

Not a document nobody reads at the right moment. `wiki/ruled-out.md` is injected
into sessions via a `SessionStart` hook, scoped to the item's keywords. The
failure to prevent: an agent cheerfully suggests checking RF range on the Zigbee
drop when I eliminated that a month ago on a different machine. **Catch it
before it's said, not after I remember.**

## Open questions bridge knowledge and roadmap

"Can the yoke print without supports?" is *both* a knowledge gap and a work item.
Model it **once**, in `state/questions/`, with its own leverage score
(how many items it gates).

**The highest-leverage open question often beats the highest-scored task**,
because resolving it collapses uncertainty downstream. Rank questions and tasks
in one list. My job is retiring uncertainty, not completing tickets.

## Wiki rendering: use Quartz

Don't build a markdown renderer with backlinks. [Quartz](https://quartz.jzhao.xyz/)
is free, Obsidian-compatible, and ships graph view, backlinks, wikilinks,
transclusion, and full-text search, deploying to GitHub Pages. Evaluate it first
and only hand-roll if it genuinely can't be themed to match.

For retrieval, **SQLite + FTS5 + sqlite-vec** (hybrid keyword + local vector
search, single file, commits fine, no server, local embeddings). I have hundreds
of documents, not millions — GraphRAG/LightRAG/Cognee are overkill. Take
contradiction-extraction as an *idea*, skip the infrastructure.

---

# 6 · Intelligence — noticing, not retrieving

Retrieval is table stakes. Build **detectors**, each emitting a notice ranked by
`(value if true × confidence)`, all flowing into `state/queue.md`:

- **Contradiction** — sources disagree
- **Stall** — threads climbing, commits flat. *Activity is not progress.*
- **Drift** — stated priority vs. hours actually spent
- **Rework** — same problem solved twice, differently, in two repos
- **Fired trigger** — a decision's `revisit_if` came true
- **Risk concentration** — N items resting on one unvalidated assumption
- **Buried cheap win** — high leverage, low effort, ranked low
- **Dead weight** — 60 days in `next` means I don't actually want it
- **External event** — stock, price, lifecycle, dependency release

Attention data comes from **Claude Code OpenTelemetry**
(`CLAUDE_CODE_ENABLE_TELEMETRY=1` → sessions, tokens, cost, tool calls over
OTLP) plus the thread index — not from guessing at message counts.

---

# 7 · Session selection — three axes, not one

"What should I do now" depends on **time available**, **energy available**, and
**what's physically possible**. Support all three:

- **`/next --time 60`** → one thing that genuinely *finishes* in an hour. Half-
  finished work is worse than none. Uses `effort_minutes`.
- **`/next --energy low`** → mechanical work only (file a BoM, run a print, tidy
  docs). Never hand me a debugging session after a long workday. Uses
  `cognitive_load`.
- **`/next --gate none`** → only what I can start from this chair, this machine.

**And a fourth mode: `/unblock`.** Parts are in the mail, nothing's on the bench,
I'm restless. Don't tell me to wait — generate the workaround: simulate it,
prototype the mount in cardboard, write the test harness, develop firmware
against a fake device. HomeApp already has a simulation mode; lean on that
pattern.

---

# 8 · Roadmap — a tradeoff simulator, not a Gantt

**Milestones are predicates, never dates.** "First light" = a *set* of items
being done. The date is always derived; I never type one.

**Monte Carlo the finish** using my real velocity per lane (git + telemetry) and
real part lead times. Output: *"first light: Nov 12, 80% confidence, ±3 weeks."*
~30 lines of code, no dependency.

**Counterfactual simulation — the feature I care most about.** Seeing the
consequence of a choice *before* making it is the whole orchestrator role:

```
What if I drop the docs site?          → 11 days earlier
What if I order everything today?      → 3 weeks earlier   ← the big one
What if gimbal firmware takes 2×?      → 4 days later (not on critical path)
```

**Blast-radius analysis before a change.** The 4005 sold out on me once already.
Before I commit to a part swap, answer: which docs go wrong, which measurements
are void, which items need rescoping, what happens to the finish date.

**Forecast calibration.** Version roadmap snapshots (GitHub Releases work well);
compare predictions against outcomes. *"You've estimated 6 weeks three times; it
took 14, 11, 16."* That improves **my** judgment, the one asset that isn't
regenerable.

**Scope collapse.** `/minimum-path "first light"` → the shortest route, with
everything else moved to `parked` — out of sight, not deleted, no guilt.

---

# 9 · Money and physical inventory

Both are first-class state, and both came from real failures.

**Money** (`state/money/`): budget per project reconciled against the published
estimates in my docs (Doc 3 ~$350–405, end-to-end $640–985 — these live on Home,
Doc 1, Doc 3, and the checklist and must stay in sync). Track committed vs.
spent. When two items compete for one month's budget, show both, what each
unblocks, what each does to the timeline, **and make a recommendation.**

**Inventory** (`state/inventory/`): what's physically on the shelf. I've bought
duplicate M3 hardware twice. Order lists are computed as **need minus have**,
never as raw need. Steal InvenTree's parts/stock/BOM data model; do **not**
deploy InvenTree — far too heavy for one person.

---

# 10 · Threads — index, attach, and know when NOT to resume

Verified paths on this machine — read them before coding:

- **`~/.codex/session_index.jsonl`** — `{id, thread_name, updated_at}`, already
  human-titled. Codex hands you an index for free.
- **`~/.codex/sessions/YYYY/MM/DD/rollout-<ts>-<uuid>.jsonl`** — line 1 is
  `session_meta` with `session_id`, `cwd`, `originator` (`codex_work_desktop`,
  `Codex Desktop`), `forked_from_id`, `parent_thread_id`.
- **`~/.claude/projects/<escaped-cwd>/<uuid>.jsonl`** — dir name encodes cwd;
  early lines carry the opening message and timestamps.

**Auto-attach, three tiers by confidence:**
1. **Item ID mention** — grep `/\b[A-Z]{2,4}-\d{3,}\b/`. Mentioning `EL-014`
   once links the thread permanently. Document this convention prominently in
   `CLAUDE.md` so sessions cite IDs unprompted.
2. **Keyword match** against item `keywords` + title. **Carries most of the
   weight** — much of my work has no repo and no ID mention (home AI models,
   Zigbee pairing). Mark `inferred`; let me confirm or reject.
3. **cwd → repo → project.** Weakest, project-level only. Never rely on alone.

**Resume vs. restart is not a coin flip — recommend.** A 210-message thread that
solved the real problem 150 messages ago is expensive, confused, and full of
abandoned approaches the model still half-believes. The brief is the distillate.

- **Resume** when: recent, same machine, live working state, **no commits landed
  since its last message**.
- **Start fresh** when: stale, other machine, very long, or work has landed since
  — then the chat's model of reality is provably behind and the brief isn't.

All computable from `last_active`, `machine`, `msg_count`, and commit timestamps.

**Bonus, and nobody does this:** Codex rollouts carry `forked_from_id` and
`parent_thread_id` — you can reconstruct the **lineage tree of my thinking**, not
just a list. Render it.

Read-only w.r.t. `~/.claude` and `~/.codex`. Tolerate malformed JSONL (skip and
count). Metadata only — transcripts contain secrets and this repo is public.

---

# 11 · Briefs — the artifact this whole system exists to produce

Every item carries a live brief: a **build artifact**, regenerated each build
from the last `/handoff` (narrative) + `git log` since (facts) + the wiki
(durable knowledge). Never hand-written, never stale.

```markdown
# EL-031 · ESP32 Zigbee firmware — where we are

Project: robotic-spotlight → fixture control
Status: doing · Gate: none (laptop) · Repo: github.com/hooterjackson/HomeApp
Blocks: EL-040, EL-042 · Answers: Q-004

## Where this stands
Last worked 3 days ago on work-laptop. Pairs with the HA coordinator, reports
on/off, but brightness drops intermittently above ~80%. Suspected: reporting
interval colliding with transition time. Two commits since: a1b3f9 (retry
backoff), 7c2d10 (debug logging) — both unverified.

## What's next
Reproduce with debug logging on; check whether ZCL transition_time is honored.

## Already ruled out — do not re-test
- Not RF range — reproduced at 30 cm (thread cx:019f8b61)
- Not power — bench supply, scoped clean (cx:019f8b61)
- Not coordinator firmware — same on 7.4.x and 7.5.x

## Decisions in force
- Zigbee over WiFi for fixtures → decisions/0007
- HA is the only control surface → decisions/0003

## Go deeper
wiki/zigbee-pairing.md · wiki/esphome-patterns.md

## Rules
Cite EL-031 in your first message. Work in HomeApp, not product-os. /handoff when we stop.

— generated from state @ 7c2d10 · ✅ audit current
```

**"Already ruled out" is the highest-value section** — negative knowledge is
exactly what dies with a chat, and what makes a fresh agent burn an hour
re-testing RF range.

**The freshness stamp is a trust mechanism.** If commits landed after the last
audit, say `⚠ 6 commits since last audit — this brief may be behind`. Never
quietly lie.

---

# 12 · Cold start — the paste, the API, and the hooks

Three tiers, by surface capability.

**Tier 1 — hooks (Claude Code, zero paste).** `SessionStart` injects current item
context + the scoped ruled-out register. `SessionEnd` auto-handoffs and registers
the thread. `PreToolUse` enforces standing orders as guardrails. **This removes
the last bit of discipline the design requires.**

**Tier 2 — MCP server (any tool-capable client).** Expose `now()`, `items()`,
`search_wiki()`, `capture()`, `propose()`, `handoff()`. Claude Code, the Codex
app, and Claude desktop are all MCP clients. Commit `.codex/config.toml`
alongside `AGENTS.md` so cloning auto-configures Codex. Strictly better than
URL-fetching where it's available.

**Tier 3 — the paste (phone, claude.ai, any machine, no setup).** Two lines:

```
Read https://product.engineered.lighting/llms.txt and follow the bootstrap
instructions there. Then tell me what to work on next and start.
```

The paste stays tiny **because the instructions live in the fetched file, not in
my muscle memory.** `llms.txt` contains: an ordered bootstrap (fetch
`/api/now.json` → `/api/context.md` → the item → its wiki pages), rules of
engagement (**cite the item ID in your first message** — this is how the thread
auto-links), permission to disagree with the ranking given what I say about my
situation, and an index of every endpoint.

**Also ship "Copy full brief"** — ~3 KB of inlined markdown, for surfaces that
can't fetch. Verify fetchability from each tool I actually use rather than
assuming; the Codex sandbox may block it.

---

# 13 · The site

Static build → GitHub Pages → Squarespace CNAME `product` →
`hooterjackson.github.io`, exactly like engineering.engineered.lighting.
**Read-only** — writes happen in chat, and drag-to-reorder would need a browser
token, a bad trade.

Views:
1. **Now** — one card: the thing, its *why*, its leverage. Never shows an item
   whose gate is unmet. Default.
2. **Board** — by status, sorted by score. Cards show score, project, lane, gate,
   cost, blocked-by, thread count. Buttons: *Copy `/pickup`*, *Copy brief*,
   *Resume on `<machine>`*.
3. **Chain** — the dependency DAG. Cross-project edges drawn boldly (LEDs →
   Zigbee → Home App is the shape I'm blind to). Critical path highlighted.
   **If one view earns its keep, it's this one.**
4. **Forecast** — Monte Carlo dates + the counterfactual panel (§8).
5. **Questions** — open questions ranked by leverage.
6. **Threads** — by project, **machine on every row**, stale flagged, inferred
   links with confirm/reject, lineage tree.
7. **Wiki** — Quartz.
8. **Context** — project files + decisions. Where I send a cold chat.
9. **Audits** — what moved and why.

**Persistent filter bar: gate · lane · machine · time · energy.**
Mobile-first — I check this on my phone more than my laptop. Match the visual
language of engineering.engineered.lighting.

---

# 14 · Seed data — part of the build, not a follow-up

Migrate `PROJECT-STATE.md`: `robotic-spotlight` + `engineering-site` projects,
its 4-item queue as scored items, its 5 ledger lines as decisions. Read
HomeApp's README/CHANGELOG/docs to write an honest `home-app` project file.
Add `home-ai-infra` and `product-os`.

Then seed the live portfolio (LED wiring, Zigbee firmware, gimbal motion, Home
App fixture control, home AI upgrades):

1. **Run the thread indexer FIRST**, and mine indexed transcripts to learn what
   each workstream actually is and where it stands.
2. Draft items, questions, and — most importantly — **your best guess at the
   dependency edges.**
3. **Show me the drafted graph and make me correct it before committing.** Worth
   the interruption; everything downstream keys off those edges.

Seeding only sees *this machine's* history — say so in the output, and make the
first sync from my other machine backfill cleanly.

Leave a pointer in `PROJECT-STATE.md` to product-os so the two don't fork.

---

# 15 · Build phases — do not build this all at once

**Phase 1 must be independently usable.** Ship it, let me live on it, then
extend. Confirm phase boundaries with me in your plan.

**Phase 1 — the spine**
Repo + item model · multi-machine sharding + registry · thread indexer +
auto-attach + resume/restart recommendation · scheduler (transitive leverage +
lead time + gate) · capture (chat, CLI, phone Shortcut) + batched triage ·
per-item briefs · `/capture /next /pickup /audit /handoff /sync` · site (Now,
Board, Chain, Threads, Context) · `llms.txt` + JSON API · `install.sh` · seed
data · `validate.mjs` in CI.

**Phase 2 — intelligence**
Compiled wiki via Quartz · ruled-out register + `SessionStart` guardrail ·
open questions · contradiction detection · SQLite hybrid search · detectors +
decision queue · GitHub Issues as decision queue and **proposals as PRs** (merge
= decide; review from the GitHub mobile app) · three-axis selection + `/unblock` ·
`SessionEnd` auto-handoff · MCP server · OTel telemetry.

**Phase 3 — foresight and economics**
Monte Carlo · counterfactual simulation · blast-radius analysis · calibration ·
money · inventory · Nexar/Octopart sensors wired to decision triggers · re-entry
mode · retro · scheduled unattended runs.

---

# 16 · Acceptance — the user stories this must serve

Verify against these. Phase 1 must serve 1, 4, 10, 12, 19, 20, 21.

1. Voice capture from the shower — no app, no fields
2. Share a part URL → specs, price, stock, filed with comparison context
3. A teardown-video trick → wiki, surfaced when designing the yoke, never queued
4. Bench photo + four words → attached to the item *and* to `frame.scad`
5. Dump 15 tabs → useful bits into the wiki, rest discarded
6. **"I can't decide — go find out"** → indecision becomes a research errand
7. **"Minimum path to first light"** → scope collapses, rest parked
8. Part sells out → blast radius *before* I commit to the swap
9. One month's budget, two wants → compare, recommend
10. **"One hour, laptop"** → one thing that actually finishes
11. **"I'm fried"** → mechanical work only
12. Free Saturday → three agents dispatched in parallel, isolated
13. **Everything blocked, still restless** → generate the workaround
14. Mid-session: discover a dependency → becomes a blocker immediately
15. Need to learn CAN bus first → briefing at my level, from what I already know
16. **Agent suggests a ruled-out approach** → caught before it's said
17. **House automation down** → interrupt mode; lost day recorded honestly
18. Session went badly → dead end recorded, not counted as progress
19. Closed the laptop without handoff → reconstructed, marked `inferred`
20. **Gone a month** → re-entry brief: what changed, what's stale, what I forgot
21. Overnight agents ran → digest with risk triage, not three transcripts
22. Spend per project vs. the published budget — am I fooling myself?
23. Shelf vs. plan → order list = need minus have
24. "What are you building?" → one sentence / a paragraph / a docs post
25. Monthly retro — what stalled, where time vanished, how wrong my estimates were
26. **"Is this even worth continuing?"** → a straight, evidence-grounded answer

**On #26 specifically:** the system must be willing to tell me it's going badly.
A tool that only ever encourages is a tool I stop believing.

---

# 17 · Done when

- `/capture /next /pickup /audit /handoff /link /sync` work end-to-end from a
  repo *other than* product-os.
- **Multi-machine holds under simulation**: hand-create a second machine's shard,
  confirm the merged build shows both, confirm same-day syncs don't conflict,
  confirm the UI labels which machine each thread lives on.
- **New-machine bootstrap is two commands** ending in working `/next`. Reason
  through `install.sh` line by line and state anything that'd fail on a fresh Mac.
- `/audit` finds a real status change in `engineered-lighting-site` or `HomeApp`
  with a commit SHA — and **refuses to mark anything done without evidence.**
- Repo-less work (home AI models) is auditable via `manual`/`file` evidence.
- Thread shard has real Claude Code AND Codex threads, correct machines, working
  resume commands, and a resume-vs-restart recommendation per thread.
- An item ID in a transcript auto-attaches; keyword matching attaches my
  repo-less chats as `inferred`.
- **The chain is real**: Home App shows `blocked`, traceable through Zigbee to
  LED wiring, and LED wiring's leverage reflects the **transitive** count.
- **Lead time changes the answer**: a 3-minute/14-day-mail item outranks a
  2-hour/zero-latency item, and the UI explains why in one sentence.
- `/next --time 60`, `/next --energy low`, and `/unblock` each return
  demonstrably different, correct sets.
- Capture → triage round-trips: a raw one-liner becomes a scored item with a
  project, and a question-shaped capture becomes a question, not a task.
- `validate.mjs` gates CI: valid frontmatter · unique IDs · resolvable refs ·
  **no dependency cycles** · no orphans · no secret-shaped strings.
- Site builds, deploys, renders all views from seeded data, readable on a phone.
- `CLAUDE.md` / `AGENTS.md` orient a cold session with no other input — **test
  by actually starting a fresh session and asking it what to work on.**

# 18 · Report back

Repo layout · the score formula as implemented (show the lead-time term changing
a real ranking) · machine-identity scheme · threads found per tool · what
`/audit` proposed on its first real run · the dependency graph you drafted ·
deploy URL · and most useful to me: **the three places this design will break
first**, with specific attention to what happens the first time two machines
disagree.
