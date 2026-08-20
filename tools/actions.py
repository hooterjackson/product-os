#!/usr/bin/env python3
"""The action artifacts: reconcile, attach, connect-repo, capture.

Generated into `public/` by `publish.py`, committed, fetchable from any machine
with no clone. `kickoff.py` builds the fifth.

## Why these are generated and not written once

A design pass mocked up reconcile and attach with good content. That content
cannot be static: it carries **live state** -- today's ranking with scores, what
is unconfirmed, the item id. A static page saying "here is what product-os
believes" would be wrong within a day and would look right forever.

## The destination is part of the artifact

Three destinations, not interchangeable: a **new** chat, an **existing** chat
with repo access, a terminal. Pasting "link yourself to GB-001" into a fresh
chat fails confusingly. Every artifact here states where it goes IN ITS OWN
TEXT, because it will be read far from whatever page produced it, and pasting
the right text into the wrong place is this design's main failure mode.

## Nothing here may embed a counter that committing it changes

R-061. Freshness comes from the audit stamp and the thread shard -- durable
facts that sit still between audits -- never from a live `rev-list` against the
working copy, which the publishing commit itself increments.
"""

import json
import os

import _fm

MANUAL = "state/threads/manual.yaml"


def _shard_dates(root):
    out = {}
    shard_dir = os.path.join(root, "state", "threads", "by-machine")
    if not os.path.isdir(shard_dir):
        return out
    for name in sorted(os.listdir(shard_dir)):
        if not name.endswith(".json"):
            continue
        try:
            with open(os.path.join(shard_dir, name), "r", encoding="utf-8") as fh:
                shard = json.load(fh)
        except (OSError, ValueError):
            continue
        out[name[:-5]] = shard.get("generated")
    return out


# ------------------------------------------------------------------ reconcile

def reconcile(root, model, stamp, ordered):
    """Paste into a NEW chat. The counterpart to kickoff.

    Kickoff starts work on a known item. This one handles "reality moved and
    the list is stale", which is most times he sits down.
    """
    unconfirmed = sorted(
        [n for n in model.nodes.values()
         if n.status == "done" and n.get("closed_origin") != "his-word"],
        key=lambda n: _fm.sort_key(n.id))
    shards = _shard_dates(root)

    lines = [
        "# Reconcile product-os with what actually happened",
        "",
        "**PASTE THIS INTO A NEW CHAT** — not into a chat that is already",
        "working on something. It needs repo access and a clean head.",
        "",
        "---",
        "",
        "## What I did (replace this line with your own words)",
        "",
        "> _e.g. \"I just finished building the bulb, I need a new version of",
        "> the firmware\" — plain language, no ids, no ceremony. Say what",
        "> changed in the world. Working out what that means for the tracker",
        "> is the job below, not yours._",
        "",
        "---",
        "",
        "## The top of my backlog, in the order I put it in",
        "",
        "This is my judgement about what matters, not a record of what is",
        "true. The order is not yours to change; whether each line is still",
        "accurate is exactly what I am asking.",
        "",
    ]
    for index, node in enumerate(ordered[:8], 1):
        lines.append("%d. `%s` — %s%s"
                     % (index, node.id, node.title,
                        " · gate %s" % node.get("gate")
                        if (node.get("gate") or "none") != "none" else ""))
    lines += ["", "## What is NOT confirmed", ""]

    any_gap = False
    if not stamp:
        lines.append("- **No audit has ever run.** Nothing below has been "
                     "checked against the repos.")
        any_gap = True
    else:
        lines.append("- Last audit **%s**, over commits since %s."
                     % (stamp.get("date"), stamp.get("window_since")))
        if stamp.get("group_d"):
            lines.append("- **%d commits were unattributed** at that audit — "
                         "work no item claims. That number is a to-do list, "
                         "not an error log." % stamp["group_d"])
            any_gap = True
    if unconfirmed:
        lines.append("- **%d item(s) marked done on a machine's judgement**, "
                     "which you have not confirmed: %s."
                     % (len(unconfirmed),
                        ", ".join(n.id for n in unconfirmed)))
        any_gap = True
    for machine, when in sorted(shards.items()):
        lines.append("- Thread index for **%s** was built **%s** — chats "
                     "since then are not in it."
                     % (machine, when or "never"))
        any_gap = True
    if not any_gap:
        lines.append("- Nothing outstanding, which is itself worth checking.")

    lines += [
        "",
        "## What to do",
        "",
        "1. **Fetch before asking git anything.** A tracking ref in this",
        "   portfolio has lied by 54 commits. If a fetch fails, say",
        "   \"I couldn't look\" — never \"no changes\".",
        "2. **Reconcile my words against what the repos actually show.** My",
        "   description is a claim; the commits are the evidence. Where they",
        "   disagree, the repo wins and say so.",
        "3. Come back with:",
        "   - **status changes, each with its evidence** — a commit SHA, a",
        "     file path, or a dated note. No evidence, no status change.",
        "   - **new items** for work that exists and nothing models, with",
        "     `evidence` paths specific enough to fire. A glob matching a",
        "     whole directory is a claim on everything that happens there.",
        "   - **nothing about the order.** `state/backlog.md` is mine. If",
        "     something new belongs near the top, say so in a sentence and",
        "     leave the file alone.",
        "",
        "## Rules",
        "",
        "- **Decided fields are drafted, never written**: `project`, `gate`,",
        "  `machine_affinity`, `parked`/`dropped`, and the `evidence` rule.",
        "  Write them into `state/drafts/`, with a diff against what is there.",
        "- **What I say applies immediately.** If I state a fact about my own",
        "  project, use `tools/apply.py --decided <ID>=<field>:<value> --said",
        "  \"<my words>\"`. Do not file a proposal addressed to me for",
        "  something I just told you.",
        "- `done` without `evidence_found` is refused for everyone, me",
        "  included.",
        "- Cite every item id you touch, in your first message.",
        "",
    ]
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------- attach

def attach(node, root):
    """Paste into an EXISTING chat that has repo access.

    For a web chat -- claude.ai, ChatGPT -- which has no transcript on disk, so
    no amount of id-citation will ever let the indexer find it. A human summary
    written into `manual.yaml` is the only record that will ever exist of it.
    """
    return "\n".join([
        "# Link this chat to %s" % node.id,
        "",
        "**PASTE THIS INTO THE CHAT YOU WANT TO LINK** — the one that has been",
        "doing the work. Not a new chat: a new one has nothing to record.",
        "This chat needs access to the `product-os` repo.",
        "",
        "---",
        "",
        "You have been working on **`%s` — %s**." % (node.id, node.title),
        "",
        "There is no transcript of this conversation on disk, so the thread",
        "indexer will never find it on its own. Write the pointer by hand:",
        "",
        "1. **Add a line to `%s`:**" % MANUAL,
        "",
        "   ```",
        "   %s: <the URL of THIS chat, from your browser's address bar>" % node.id,
        "   ```",
        "",
        "   Flat `key: url`, one per line. If you cannot see the URL, ask me",
        "   for it — do not guess one.",
        "",
        "2. **Write what this chat actually achieved** into `%s`'s"
        % node.id,
        "   `## Handoffs` section: what was done, what is next, what got ruled",
        "   out. Be blunt if it went badly — a dead end recorded is progress.",
        "",
        "3. **Anything that turned out not to work goes in**",
        "   `wiki/ruled-out.md`, with keywords, a source, a date and a grade.",
        "   The `SessionStart` hook reads that file; a finding that stays in a",
        "   handoff is a finding nobody meets at the moment they need it.",
        "",
        "## Do not",
        "",
        "- **Do not write into `state/threads/by-machine/`.** Those shards are",
        "  regenerated wholesale by `tools/index.py` and your edit will be",
        "  overwritten without warning. `%s` is the hand-written one." % MANUAL,
        "- **Do not mark anything `done`** without an `evidence_found` entry —",
        "  a commit SHA, a file path, or a dated note.",
        "- **Do not write decided fields** (`project`, `gate`,",
        "  `machine_affinity`, `parked`/`dropped`, the `evidence` rule), and do",
        "  not reorder `state/backlog.md`. Draft into `state/drafts/` instead.",
        "",
        "## Syncing",
        "",
        "```bash",
        "git -C ~/Claude/product-os pull --rebase",
        "#   ... make the edits ...",
        "python3 tools/validate.py && python3 tools/publish.py",
        "git -C ~/Claude/product-os push",
        "```",
        "",
        "**If the rebase conflicts on an item file, stop.** Two people's words",
        "are in that file and merging them automatically loses one.",
        "",
    ]) + "\n"


# --------------------------------------------------------------- connect-repo

def connect_repo(root, model, stamp):
    """Paste into an EXISTING chat with repo access.

    Absent from the design and the build entirely, and it is the thing that
    makes this scale past the four repos it already knows.
    """
    known = []
    try:
        with open(os.path.join(root, "state", "repos.json"), "r",
                  encoding="utf-8") as fh:
            known = sorted(k for k in json.load(fh) if not k.startswith("_"))
    except (OSError, ValueError):
        pass
    group_d = (stamp or {}).get("group_d")
    return "\n".join([
        "# Connect a new repo to product-os",
        "",
        "**PASTE THIS INTO AN EXISTING CHAT THAT HAS REPO ACCESS** — it needs",
        "to read the new repo and write to `product-os`. A fresh chat with no",
        "filesystem cannot do either.",
        "",
        "---",
        "",
        "## 1 · Register it",
        "",
        "`state/repos.json` is five keys. Add one entry:",
        "",
        "```json",
        '"<repo-name>": {',
        '  "owner": "<github owner, or null if there is no remote>",',
        '  "local": "~/path/to/clone",  // or null if not cloned here',
        '  "default_branch": "main",    // CHECK IT — gimbal-bench uses master',
        '  "authority": false,          // true only if it holds rulings',
        '  "public": false',
        "}",
        "```",
        "",
        "Already registered: %s." % ", ".join("`%s`" % r for r in known),
        "",
        "No code changes anywhere. `audit.py` iterates whatever is configured.",
        "",
        "## 2 · Then model the work, or you have made things worse",
        "",
        "**Coverage scales with ITEMS, not repos.** Registering a repo without",
        "items that name its paths does one thing: it grows group D — the",
        "commits no item claims — until the one honest signal in the audit",
        "becomes a number that gets scrolled past.",
        "",
        ("That number is currently **%d**." % group_d) if group_d else
        "That number has never been measured; run `tools/audit.py` first.",
        " Adding a repo without items makes it bigger, not smaller.",
        "",
        "So, in the same sitting:",
        "",
        "1. **Read the last ~45 days of its commits** and cluster them by what",
        "   the work actually was — not one item per commit. Aim for a handful",
        "   of items covering most of the volume.",
        "2. **Give each item `evidence` paths specific enough to fire.** Run",
        "   them past the classifier: a glob matching a whole directory",
        "   identifies the subsystem, not the item's work. A glob matching no",
        "   file in the tree can never fire at all.",
        "3. **Recommend, do not create.** The system never creates a task —",
        "   that is mine alone. Write candidates into",
        "   `state/recommendations/`, one sentence plus the commits and paths",
        "   that made you think of it, so I can adopt or dismiss in a word.",
        "4. **Report the coverage you achieved as a fraction** — commits",
        "   attributable before versus after. And name what you could not",
        "   model rather than inventing items to drive it to zero. A coverage",
        "   figure gamed by fake items is worse than a low one.",
        "",
        "## 3 · Verify",
        "",
        "```bash",
        "python3 tools/validate.py      # 0 errors",
        "python3 tools/audit.py         # the new repo appears in Coverage",
        "python3 tools/publish.py       # regenerate the public surface",
        "```",
        "",
        "The coverage line must name the new repo under **reached** or under",
        "**unreachable**. If it is unreachable, say \"I couldn't look\" — never",
        "let that render as \"no changes\".",
        "",
    ]) + "\n"


# -------------------------------------------------------------------- capture

def capture():
    """One line. If capture ever asks a question, capture is broken."""
    return "\n".join([
        "# Capture a thought",
        "",
        "**TYPE THIS ANYWHERE** — any chat, any machine, mid-task. It does not",
        "need repo access and it will not interrupt what you are doing.",
        "",
        "```",
        "/capture <whatever you were about to forget>",
        "```",
        "",
        "Or, from a terminal in the repo:",
        "",
        "```bash",
        'python3 tools/new.py capture "spot 1 buzzes at 40% but not at 100"',
        "```",
        "",
        "That is the whole thing. It asks nothing — no project, no priority,",
        "no \"should I file this as an item?\" — because every question is a",
        "reason not to bother next time, and triage does all of that later in",
        "batch. Your words go in verbatim, with a timestamp and the machine.",
        "",
        "**If capture ever asks you a question, capture is broken.**",
        "",
    ]) + "\n"


def generate(root, model, target, stamp, ranked):
    def put(rel, text):
        path = os.path.join(target, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)

    put("reconcile.md", reconcile(root, model, stamp, ranked))
    put("connect-repo.md", connect_repo(root, model, stamp))
    put("capture.md", capture())
    for node in model.nodes.values():
        if node.is_active:
            put(os.path.join("attach", "%s.md" % node.id), attach(node, root))
