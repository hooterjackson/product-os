---
name: handoff
description: Write what happened in this session onto the product-os item, so the next session can read it instead of a chat history it cannot see. Use when the user says /handoff, "wrap up", "write this up", "I'm stopping here", or at the end of a working session.
---

# handoff

Append a dated, machine-stamped entry to the item's `## Handoffs` section. That
entry is what the next session reads **instead of this one's chat history, which
it cannot see.**

## 1 · Find the item

The ID cited at the start of the session. If none was, find it:

```bash
python3 tools/rank.py --json | head -40
```

Ask which one only if it is genuinely ambiguous. Guessing is worse than asking
once.

## 2 · Establish what actually landed

Before writing a word about progress:

```bash
git -C <repo> fetch --quiet && git -C <repo> log origin/<default-branch> --oneline -20
```

**Fetch first, always.** The local tracking ref in this portfolio has lied by 54
commits — `git rev-list --count HEAD..origin/main` answered `0` while the remote
was 54 ahead. `tools/_git.py` exists for this and hard-fails to `unreachable`
rather than falling back.

`gimbal-bench`'s default branch is `master`, not `main`. Do not assume.

**If you could not reach a repo, write "I couldn't look."** Never write "no
changes". Name which repos you reached and which you did not, every time.

## 3 · Write the entry

Append to the item body, newest last:

```markdown
## Handoffs

### 2026-08-19 · work-laptop
**Did:** …
**Next:** …
**Ruled out:** …
**Reached:** gimbal-bench, engineered-lighting-site · **Could not reach:** —
```

- **Did** — what changed, with SHAs and paths. Not intentions.
- **Next** — the single most useful thing for the next session to start on.
- **Ruled out** — anything that turned out not to work. **If this section is
  empty in a session that hit a wall, the handoff has failed.** A dead end
  recorded is progress; a dead end forgotten gets re-walked.
- **Reached / could not reach** — the coverage line. Always present.

**If the work went badly, say so.** A handoff that reads well and reports nothing
is worse than a blunt one.

## 4 · Propagate the negative results

Anything under **Ruled out** that would cost someone an afternoon belongs in
`wiki/ruled-out.md` as its own entry, with `keywords`, a `source` (repo, path,
SHA), a date and a grade on the ladder `measured > datasheet > inferred >
said-in-chat`. The keywords are what the `SessionStart` hook matches on, so an
entry without them is invisible at the moment it would have helped.

## 5 · Update status, within your authority

You may set `status`, `keywords`, `lane`, `title`, `repos`, `updated`,
`evidence_found` and `completed`.

**`status: done` requires an `evidence_found` entry** — a commit SHA, a file
path, or a dated manual note. If you cannot produce one, the item is not done.
Say so and leave it. `validate.py` will reject it anyway, but the point is not to
try.

You may **not** set `impact`, `confidence`, `effort_minutes`, `lead_time_days`,
`cost_usd`, `unblocks`, `pin`, `project`, `gate`, `dropped`, `parked` or the
`evidence` rule. If one of them is wrong, write a proposal into
`state/proposals/` — the change, the reasoning, and a citation to `intent.md` or
a standing order — and say that you have.

## 6 · Verify and sync

```bash
python3 tools/validate.py
```

Then `git pull --rebase` before committing and push after. **If a rebase
conflicts on an item file, stop.** Do not auto-merge two humans' words.
