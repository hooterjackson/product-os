# Reconcile product-os with what actually happened

**PASTE THIS INTO A NEW CHAT** — not into a chat that is already
working on something. It needs repo access and a clean head.

---

## What I did (replace this line with your own words)

> _e.g. "I just finished building the bulb, I need a new version of
> the firmware" — plain language, no ids, no ceremony. Say what
> changed in the world. Working out what that means for the tracker
> is the job below, not yours._

---

## What product-os currently believes

This is a set of guesses, not a record of reality. Check it.

1. `GB-001` 25.0 — Finish the M5 fault ring: a real fault storm, and the brownout case · gate bench
2. `HAI-001` 20.0 — Rotate the GPU box's Linux password
3. `POS-002` 7.5 — Point PROJECT-STATE.md at product-os
4. `GB-002` 6.7 — Rescue D1-D11 off formd-t1 and commit them
5. `Q-001` 6.0 — Does Spot Mode (Auto/Hold/Manual) survive gate A?
6. `GB-004` 5.3 — M6 on hardware: the motor-silent limb, MUTE-CLEAR, and the armed lane · gate bench
7. `POS-008` 5.3 — Surface inferred closures, record the public decision
8. `Q-002` 5.3 — Does a mid-move retarget re-plan smoothly, or stop and restart?

## What is NOT confirmed

- Last audit **2026-08-19** (today), over commits since 2026-07-05.
- **322 commits were unattributed** at that audit — work no item claims. That number is a to-do list, not an error log.
- **5 item(s) marked done on a machine's judgement**, which you have not confirmed: EL-004, EL-005, POS-003, POS-004, POS-005.

## What to do

1. **Fetch before asking git anything.** A tracking ref in this
   portfolio has lied by 54 commits. If a fetch fails, say
   "I couldn't look" — never "no changes".
2. **Reconcile my words against what the repos actually show.** My
   description is a claim; the commits are the evidence. Where they
   disagree, the repo wins and say so.
3. Come back with:
   - **status changes, each with its evidence** — a commit SHA, a
     file path, or a dated note. No evidence, no status change.
   - **new items** for work that exists and nothing models, with
     `evidence` paths specific enough to fire. A glob matching a
     whole directory is a claim on everything that happens there.
   - **a proposed order, with the arithmetic shown.** Operands, not a
     conclusion. `python3 tools/rank.py --show <ID>` prints them.

## Rules

- **Decided fields are proposed, never written**: `impact`,
  `confidence`, `effort_minutes`, `cost_usd`, `unblocks`, `pin`,
  `gate`, `project`, `parked`/`dropped`, and the `evidence` rule.
  Write them into `state/proposals/`.
- **What I say applies immediately.** If I state a fact about my own
  project, use `tools/apply.py --decided <ID>=<field>:<value> --said
  "<my words>"`. Do not file a proposal addressed to me for
  something I just told you.
- `done` without `evidence_found` is refused for everyone, me
  included.
- Cite every item id you touch, in your first message.

