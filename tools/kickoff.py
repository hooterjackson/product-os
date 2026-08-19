#!/usr/bin/env python3
"""Paste-ready kickoff prompts, one per item. The artifact this tool exists for.

    python3 tools/kickoff.py GB-001      one prompt, to stdout
    python3 tools/kickoff.py --all       every active item, into public/kickoff/

The single most-used artifact across this whole build has been a hand-written
paste-ready prompt: item ID, what is known, what is ruled out, which repo, the
rules, the stop conditions. Written by hand about a dozen times. That is this
tool's job and it was not doing it -- everything else was a nicer way to reach
something you would then still copy and paste by hand.

## Small on purpose

Target ~2-3 KB. This goes into a context window; anything a session would not
ACT on is costing tokens for nothing. Cut prose, keep operands.

## An absent section reads as "nothing known"

If the ruled-out section is empty it SAYS it is empty. Same for the return path
and the handoff. On day one almost everything is absent, and an omitted heading
is indistinguishable from a clean bill of health.
"""

import argparse
import json
import os
import sys

import _fm
import _model
import brief as brief_mod

MAX_RULED_OUT = 4
MANUAL = "state/threads/manual.yaml"


def clip(text, limit):
    """Cut at a word boundary and say so. A quote truncated mid-word reads as
    a transcription error and invites someone to go and check it."""
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip(" ,;:—-")
    return cut + " …"


def load_manual(root):
    """Chat URLs Marcelo pasted in once, keyed by item ID or thread id.

    `state/threads/manual.yaml` was reserved in the spec for exactly this and
    had never been written to. A web chat has no CLI and no session file, so
    without this a cloud thread is unreachable forever -- and a RESUME verdict
    with no way to resume is a dead end wearing a green label.

    Deliberately a flat `key: url` list, parsed in eight lines. No YAML
    dependency, and he can add a line from a phone.
    """
    path = os.path.join(root, MANUAL)
    out = {}
    if not os.path.exists(path):
        return out
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.split("#", 1)[0].strip()
            if not line or ":" not in line:
                continue
            key, _, url = line.partition(":")
            url = url.strip()
            if url:
                out.setdefault(key.strip().upper(), []).append(url)
    return out


def threads_for(root, item_id, manual):
    """Every return path for this item: indexed threads plus manual URLs."""
    paths = []
    shard_dir = os.path.join(root, "state", "threads", "by-machine")
    if os.path.isdir(shard_dir):
        for name in sorted(os.listdir(shard_dir)):
            if not name.endswith(".json"):
                continue
            with open(os.path.join(shard_dir, name), "r", encoding="utf-8") as fh:
                try:
                    shard = json.load(fh)
                except ValueError:
                    continue
            for thread in shard.get("threads") or []:
                if item_id not in (thread.get("items") or []):
                    continue
                paths.append({
                    "machine": shard.get("machine"),
                    "tool": thread.get("tool"),
                    "title": thread.get("title") or thread.get("id"),
                    "verdict": thread.get("verdict"),
                    "reason": thread.get("verdict_reason"),
                    "command": thread.get("command"),
                    "id": thread.get("id"),
                })
    for url in manual.get(item_id.upper(), []):
        paths.append({"machine": None, "tool": "web", "title": "pasted URL",
                      "verdict": "resume", "reason": "he recorded this URL",
                      "command": None, "url": url, "id": None})
    return paths


def render(node, model, entries, stamp, repos_spec, root, manual):
    ruled = brief_mod.ruled_out_for(node, entries)[:MAX_RULED_OUT]
    repos = node.get("repos") or []
    machine = node.get("machine_affinity")
    gate = node.get("gate") or "none"
    returns = threads_for(root, node.id, manual)

    lines = [
        "Cite %s in your first message." % node.id,
        "",
        "# %s — %s" % (node.id, node.title),
        "",
        "%s · %s · %d min · gate %s%s"
        % (node.project, node.effective_status, node.effort_minutes, gate,
           " · machine %s" % machine if machine else ""),
        "Freshness: %s"
        % brief_mod.freshness(root, node, stamp, repos_spec),
        "",
    ]

    # --- what this is, from the body, first paragraph only
    lines += ["## What this is", ""]
    picked = []
    for chunk in (node.body or "").split("\n\n"):
        chunk = chunk.strip()
        if not chunk or chunk.startswith(("#", "|", "---", "```", "**Did:**",
                                          "**Next:**", "**Reached:**")):
            continue
        flat = " ".join(chunk.replace("> ", "").split())
        # A lone bold header is a label, not a description. Keep collecting
        # until there is something a session could actually act on.
        picked.append(flat)
        if sum(len(p) for p in picked) > 220 or len(picked) >= 3:
            break
    lines += [clip(" ".join(picked), 700) if picked
              else "The item body says nothing beyond its title.", ""]

    # --- where it stands
    lines += ["## Where it stands", ""]
    if node.effective_status == "blocked":
        lines.append("BLOCKED by %s. Do not start it." % ", ".join(node.blockers))
    if node.leverage:
        lines.append("Unblocks %d item(s): %s."
                     % (node.leverage,
                        ", ".join(sorted(node.reach, key=_fm.sort_key))))
    found = node.get("evidence_found") or []
    if found:
        lines.append("Evidence on file: %s."
                     % ", ".join(str(e.get("sha") or e.get("path"))
                                 for e in found[:5]))
    else:
        lines.append("No evidence recorded. It cannot be closed until "
                     "something can be clicked.")
    nxt = brief_mod.whats_next(node)
    lines.append("Next, from the last handoff: %s"
                 % (nxt if nxt else "NO HANDOFF RECORDED — nobody wrote down "
                    "where this was left."))
    lines.append("")

    # --- the highest-value section
    lines += ["## Already ruled out — read before proposing anything", ""]
    if ruled:
        for _n, title, first, overlap in ruled:
            lines.append("- **%s**" % title)
            if first:
                lines.append("  %s" % clip(first, 190))
    else:
        lines.append("NOTHING in wiki/ruled-out.md matches this item's "
                     "keywords. That is not the same as nothing having been "
                     "ruled out — this section is empty, not clear.")
    lines.append("")

    # --- where the work happens
    lines += ["## Work here, not in product-os", ""]
    if repos:
        lines.append("Repo: %s. product-os TRACKS the work; it does not host "
                     "it. Make the change there and come back only to write "
                     "the handoff." % ", ".join("`%s`" % r for r in repos))
    else:
        lines.append("This item names no repo. Find out where the work lives "
                     "before starting.")
    if machine:
        lines.append("Machine: **%s**. If that is not where you are, the "
                     "honest answer is \"resume on %s\" — not a plan you "
                     "cannot execute." % (machine, machine))
    if gate != "none":
        lines.append("Gate `%s`: this needs hardware or a person that may not "
                     "be present." % gate)
    lines.append("")

    # --- return paths
    lines += ["## Chats already working on this", ""]
    if returns:
        for row in returns:
            head = "- %s · %s · %s" % (row["tool"], row.get("machine") or "—",
                                       (row["title"] or "")[:44])
            lines.append(head)
            lines.append("  %s — %s" % (row["verdict"].upper(), row["reason"]))
            if row.get("command"):
                lines.append("  $ %s" % row["command"])
            elif row.get("url"):
                lines.append("  %s" % row["url"])
            elif row["verdict"] == "resume":
                lines.append("  No verified way back on this machine. Open it "
                             "from the app's own session picker.")
    else:
        lines.append("None indexed. Starting fresh is correct.")
        lines.append("If you are in a web chat, paste its URL into "
                     "`%s` so it is reachable next time." % MANUAL)
    lines.append("")

    # --- rules
    lines += [
        "## Rules",
        "",
        "- Nothing is done without evidence — a commit SHA, a file path, or a",
        "  dated note. If you cannot produce one, it is not done. Say so.",
        "- Say \"I couldn't look\", never \"no changes\". An empty result and an",
        "  unreachable repo are different facts.",
        "- Do not write his decided fields: impact, confidence, effort_minutes,",
        "  cost_usd, unblocks, pin, gate, project, parked/dropped, or the",
        "  evidence rule. Propose instead.",
        "- The score is a label, not a verdict. Disagree once, with a reason,",
        "  then do what he says.",
        "",
    ]
    return "\n".join(lines)


def generate(root, model, target):
    entries = brief_mod.parse_register(root)
    stamp = brief_mod.read_stamp(root)
    manual = load_manual(root)
    with open(os.path.join(root, "state", "repos.json"), "r",
              encoding="utf-8") as fh:
        repos_spec = {k: v for k, v in json.load(fh).items()
                      if not k.startswith("_")}
    written = []
    for node in model.nodes.values():
        if not node.is_active:
            continue
        text = render(node, model, entries, stamp, repos_spec, root, manual)
        path = os.path.join(target, "kickoff", "%s.md" % node.id)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        written.append(node.id)
    return written


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("item", nargs="?")
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args(argv)

    root = _model.find_root()
    model = _model.Model.load(root)
    if args.item:
        node = model.nodes.get(args.item.upper())
        if node is None:
            sys.stderr.write("no such item: %s\n" % args.item)
            return 2
        entries = brief_mod.parse_register(root)
        stamp = brief_mod.read_stamp(root)
        with open(os.path.join(root, "state", "repos.json"), "r",
                  encoding="utf-8") as fh:
            repos_spec = {k: v for k, v in json.load(fh).items()
                          if not k.startswith("_")}
        sys.stdout.write(render(node, model, entries, stamp, repos_spec, root,
                                load_manual(root)))
        return 0
    written = generate(root, model, os.path.join(root, "public"))
    print("wrote %d kickoff prompt(s)" % len(written))
    return 0


if __name__ == "__main__":
    sys.exit(main())
