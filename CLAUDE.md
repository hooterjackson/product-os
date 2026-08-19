# product-os — read this first

The priority and context control plane for a solo portfolio of interlocking
hardware/firmware/software projects, executed almost entirely through AI chats across
several machines.

**Marcelo is the orchestrator. This is not an autopilot.** The single most important
rule in this repo: *the system never changes a priority. It changes a proposal.*

---

## What to work on right now

```bash
python3 tools/rank.py                 # the ranked list, one line each
python3 tools/rank.py --explain       # the top item, with why
python3 tools/rank.py --time 60       # something that actually finishes in an hour
python3 tools/rank.py --energy low    # mechanical work only
python3 tools/rank.py --gate none     # only what can start from this chair
```

Rank is **derived**, never stored. There is no ordered list anywhere in this repo —
`tools/rank.py` computes it from the score inputs every time.

---

## Cite the item ID in your first message

**This is the most important line in this file.** IDs look like `EL-004`, `GB-002`,
`Q-003`. Writing one into a chat — any chat, any tool — is what lets the thread
indexer link that conversation to that work, permanently and for free.

So: when you start work on something, say its ID out loud in your first message. When
you finish, `/handoff` writes what happened back onto the item.

Prefixes: `EL` robotic-spotlight · `SITE` engineering-site · `GB` gimbal-bench ·
`APP` home-app · `HAI` home-ai-infra · `POS` product-os · `Q` questions ·
`DEC` decisions.

---

## Authority — the rule that governs every agent here

Two categories, permanently separate:

- **Computed** — scores, leverage, reasoning. Agents write these freely, into `build/`.
- **Decided** — the score inputs. These change only when Marcelo accepts a proposal.

Because rank is a pure function of the decided inputs, "the ranking changes only when I
accept a proposal" reduces to "the decided *fields* change only when I accept a
proposal" — and that is mechanically checkable.

**You may write (agent authority):**
`status` (`next`/`doing`/`done`/`blocked`) · `keywords` · `lane` · `title` · `repos` ·
`updated` · `evidence_found` · `completed`

**You may NOT write — propose instead (human authority):**
`impact` · `confidence` · `effort_minutes` · `lead_time_days` · `cost_usd` ·
`unblocks` · `pin` · `project` · `gate` · `dropped`/`parked` · the `evidence` **rule** ·
`intent.md` · `standing-orders.md`

To change any of those, write a file into `state/proposals/` with the change, the
reasoning, and a citation to `intent.md` or a standing order. Marcelo merges, amends,
or rejects. `tools/validate.py` fails CI if a human-authority field changed without an
accepted proposal.

### Never automate

Setting intent · tradeoffs with taste in them · spending money · anything irreversible ·
declaring something *good* rather than merely complete.

### Always automate

Status truth · recomputing rank · assembling context · writing handoffs · detecting
stalls and drift.

### Escalate rather than resolve

If two items score within ~10% of each other, if a change has cross-project
consequences, if it contradicts `intent.md`, or if it spends money — **stop and ask.**
Everything unambiguous, just handle. That ratio is the whole point.

---

## Refuse to mark anything done without evidence

`status: done` requires an `evidence_found` entry: a commit SHA, a file path, or a
dated manual note. If you cannot produce one, the item is not done — say so and leave
it. A system that reports progress it cannot prove is worse than no system.

Same rule for reporting: if you could not reach a repo, **say "I couldn't look."**
Never let that render as "no changes."

---

## Where to write

| Path | Who writes it |
|---|---|
| `state/**` | authored — you, within your authority; Marcelo for decided fields |
| `state/inbox/` | `/capture` only. Raw words plus a timestamp. Nothing else. |
| `state/proposals/` | you, whenever you want to change a decided field |
| `build/**` | generated. Never hand-edit; it is git-ignored and rebuilt wholesale. |
| `wiki/ruled-out.md` | dead ends. Append when something is eliminated — see below. |

---

## Before suggesting an approach, check what has already been ruled out

`wiki/ruled-out.md` is a register of things that were tried and failed, or eliminated
with reasons. It exists so nobody burns an afternoon re-deriving a dead end that died
with a chat six weeks ago. A `SessionStart` hook injects the entries matching the
current item's keywords.

When a session concludes that something does *not* work — **write it there.** Negative
results are the most expensive knowledge in this portfolio and the easiest to lose.

If you find something that contradicts a page, do not silently overwrite it. Flag it.

---

## Multi-machine discipline

Machine-derived data is sharded, never shared: `state/threads/by-machine/<id>.json` is
written by exactly one machine's indexer. Two machines syncing the same day touch
different files.

Every write does `git pull --rebase` before and `push` after. If a rebase conflicts on
an item file, **stop** — do not auto-merge two humans' words.

Work is machine-bound. The bench (`gate: bench`), the printer (`gate: printer`) and the
GPU box are not this laptop. An item's `machine_affinity` says where it can happen; if
it is not here, the honest answer is *"resume on `<machine>`"*, not a plan you cannot
execute.

---

## Working outside this repo

Most work happens in *other* repos — `engineered-lighting-site`, `gimbal-bench`,
`HomeApp`. product-os tracks; it does not host. When you pick up an item, work in the
repo the item names, and come back here only to `/handoff`.

**Local git lies.** `git rev-list --count HEAD..origin/main` returned `0` in
`engineered-lighting` while the remote was 54 commits ahead, because the tracking ref
had not been fetched since July. Always `git fetch` before asking git what landed. If
the fetch fails, report `⚠ unreachable` — never fall back to the local ref.

**One repo outranks the others.** `gimbal-bench` holds the decision ledger (D/R/F/G/Z
rulings). Published documentation on the site is narrative and can be stale; it never
overrides a ruling or current bench evidence. When they disagree, the ruling wins and
the doc gets a propagation item.

---

## When you stop

`/handoff` — writes a dated, machine-stamped entry onto the item: what happened, what
is next, what got ruled out. That entry is what the next session reads instead of this
one's chat history, which it cannot see.

If the work went badly, say so. A dead end recorded is progress; a dead end forgotten
gets re-walked.
