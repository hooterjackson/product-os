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

## The top of my backlog, in the order I put it in

This is my judgement about what matters, not a record of what is
true. The order is not yours to change; whether each line is still
accurate is exactly what I am asking.

1. `GB-001` — Finish the M5 fault ring: a real fault storm, and the brownout case
2. `HAI-001` — Rotate the GPU box's Linux password
3. `GB-014` — Un-park Zigbee — the decision D15 leaves open · gate external
4. `GB-005` — Prepare the radio build: memory layout, and a stub for signing updates (Z-M1)
5. `GB-006` — Add the single-slot mailbox the radio and the safety loop pass messages through (Z-M0)
6. `GB-008` — Bring the fixture up on the radio and prove it still behaves like a light (Z-M3)
7. `GB-002` — Rescue D1-D11 off formd-t1 and commit them
8. `Q-001` — Does Spot Mode (Auto/Hold/Manual) survive gate A?

## What is NOT confirmed

- Last audit **2026-08-19**, over commits since 2026-08-10.
- **153 commits were unattributed** at that audit — work no item claims. That number is a to-do list, not an error log.
- **1 item(s) marked done on a machine's judgement**, which you have not confirmed: EL-004.
- Thread index for **work-laptop** was built **2026-08-23** — chats since then are not in it.

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
   - **nothing about the order.** `state/backlog.md` is mine. If
     something new belongs near the top, say so in a sentence and
     leave the file alone.

## Rules

- **Decided fields are drafted, never written**: `project`, `gate`,
  `machine_affinity`, `parked`/`dropped`, and the `evidence` rule.
  Write them into `state/drafts/`, with a diff against what is there.
- **What I say applies immediately.** If I state a fact about my own
  project, use `tools/apply.py --decided <ID>=<field>:<value> --said
  "<my words>"`. Do not file a proposal addressed to me for
  something I just told you.
- `done` without `evidence_found` is refused for everyone, me
  included.
- Cite every item id you touch, in your first message.

