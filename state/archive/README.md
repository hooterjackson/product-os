# Archive

Finished or superseded work. **Nothing loads this directory** — `Model.load` globs `state/projects/*/items/*.md` and the archive is not on that path, so these items are out of the backlog, the dashboard and every prompt.

It sits under `state/` on purpose: `new.py:next_id()` walks that tree for max+1, and moving the archive outside it would let an id be handed out twice — `R-057`, where a transcript citing `Q-004` bound to the wrong work.

Files keep their frontmatter, evidence and handoffs verbatim.

## 2026-08-23 · work-laptop

> audited all eight open product-os tasks: every one is done or superseded, and five had no evidence rule at all so they could never have closed. I don't want them clogging up the UI.

- `POS-001` (doing) — Build product-os slice 1a-minus
- `POS-002` (done) — Point PROJECT-STATE.md at product-os
- `POS-003` (done) — Build /audit: re-check priorities against reality
- `POS-004` (done) — apply.py: distinguish who decided, not just what changed
- `POS-005` (done) — Thread indexer: bind chats to items, metadata only
- `POS-006` (doing) — Group D coverage: cluster 301 unattributed commits into items
- `POS-007` (next) — Re-centre on software: kill lead-time, park hardware, briefs and resume verdicts
- `POS-008` (doing) — Surface inferred closures, record the public decision
- `POS-009` (next) — llms.txt and the JSON API: the agent-facing surface
- `POS-010` (next) — Kickoff prompts and thread return paths
- `POS-011` (next) — The remaining action artifacts: reconcile, attach, connect-repo, capture
- `POS-012` (doing) — A correction is only real where it is read

**4 of these were closed by a machine and never confirmed by him** — POS-002, POS-003, POS-004, POS-005. They archive AS unconfirmed; filing something away is not agreeing with it, and relabelling it on the way out would be the tool laundering its own guess.
