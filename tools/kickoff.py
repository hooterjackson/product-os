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

import _model
import _context

MAX_RULED_OUT = 4
MANUAL = "state/threads/manual.yaml"          # tracked: presence only
MANUAL_LOCAL = "state/threads/manual.local.yaml"   # gitignored: the urls


def clip(text, limit):
    """Cut at a word boundary and say so. A quote truncated mid-word reads as
    a transcription error and invites someone to go and check it."""
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip(" ,;:—-")
    return cut + " …"


def _pairs(path):
    """`key: value` lines, comments stripped. Eight lines, no YAML dependency."""
    out = []
    if not os.path.exists(path):
        return out
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.split("#", 1)[0].strip()
            if not line or ":" not in line:
                continue
            key, _, value = line.partition(":")
            value = value.strip()
            if value:
                out.append((key.strip().upper(), value))
    return out


def load_manual(root):
    """Web-chat pointers, SPLIT: presence is committed, the url is not.

    A web chat has no transcript on disk, so a hand-written pointer is the only
    record that will ever exist of it. But this repo is PUBLIC and
    `manual.yaml` is tracked, so pasting a url there publishes a link to a
    private conversation -- the same class `R-062` removed from `public/`,
    arriving by a third route into authored state, where the generated
    surface's redaction cannot reach.

    So two files:

        state/threads/manual.yaml        TRACKED    `GB-001: work-laptop 2026-08-20`
        state/threads/manual.local.yaml  IGNORED    `GB-001: https://claude.ai/chat/...`

    The tracked half syncs the honest signal -- a chat exists, on that machine,
    since that date -- to every machine and to `public/`. The url stays on the
    one machine that can open it anyway, since it needs his login.

    Why not just gitignore the whole file: `public/` is generated wherever the
    url is and would still say "recorded in manual.yaml", while that file was
    empty everywhere else. A pointer to nothing is the green-label dead end the
    verdict system exists to prevent.

    Why not a hash or a bare id: `claude.ai/chat/<uuid>` is a known template,
    so publishing the uuid publishes the url minus a prefix anyone can supply;
    and a one-way hash cannot be opened by him either, which destroys the
    feature rather than protecting it.

    Returns {ID: [{"url", "machine", "recorded"}]}. `url` is None on any
    machine that does not hold it, and callers must render that as a stated
    absence rather than as nothing.
    """
    entries = {}
    for key, value in _pairs(os.path.join(root, MANUAL)):
        parts = value.split()
        entries.setdefault(key, []).append({
            "url": None,
            "machine": parts[0] if parts else None,
            "recorded": parts[1] if len(parts) > 1 else None,
        })
    for key, url in _pairs(os.path.join(root, MANUAL_LOCAL)):
        rows = entries.setdefault(key, [])
        placed = False
        for row in rows:
            if row["url"] is None:
                row["url"] = url
                placed = True
                break
        if not placed:
            rows.append({"url": url, "machine": None, "recorded": None})
    return entries


def redact_manual(manual):
    """Presence without the url. What `public/` may carry."""
    return {key: [dict(row, url=None) for row in rows]
            for key, rows in manual.items()}


def threads_for(root, item_id, manual):
    """Every return path for this item: indexed threads plus manual URLs."""
    paths = []
    for path in _context.tracked_shards(root):
        if True:
            with open(path, "r", encoding="utf-8") as fh:
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
                    "title": thread.get("title") or thread.get("key"),
                    "verdict": thread.get("verdict"),
                    "reason": thread.get("verdict_reason"),
                    "command": local_ways_back(root).get(thread.get("key")),
                    "id": None,
                })
    for entry in manual.get(item_id.upper(), []):
        machine = entry.get("machine")
        if entry.get("url"):
            reason = "he recorded this URL"
        elif machine:
            reason = ("recorded on %s. The URL lives in %s there, which is not "
                      "committed." % (machine, MANUAL_LOCAL))
        else:
            reason = "recorded, but no URL is available on this machine."
        paths.append({"machine": machine, "tool": "web", "title": "pasted URL",
                      "verdict": "resume", "reason": reason, "command": None,
                      "url": entry.get("url"), "id": None,
                      "web_only_elsewhere": not entry.get("url")})
    return paths


def redact(rows, volatile):
    """Strip the machine-local way back when this is going to be COMMITTED.

    A resume command is `cd ~/Claude/product-os && claude -r <uuid>`. Both
    halves are wrong to publish, for different reasons:

      the PATH is this machine's layout. `formd-t1` is Windows, `C:\Claude\`.
      A committed command is right on one machine and misleading everywhere
      else -- and `public/` is served to every machine by design.

      the UUID is a private conversation identifier. `publish.py` already
      redacts `manual.yaml` URLs for exactly this reason (`R-062`), and the
      shard's `command` field carries the same class by a second route that
      the redaction never covered. One rule, applied to one of two sources --
      the shape of `R-067`.

    Measured 2026-08-20: 26 such commands across 4 committed files under
    `public/`, on a public repo. The disclosure screen missed them because its
    `home-path` pattern is `/Users/...` and these are the tilde form.

    `build/` keeps the real command, for the person at the keyboard who can
    run it -- so does `python3 tools/kickoff.py <ID>` on stdout. That is the
    same volatile/durable split as the freshness line.
    """
    out = []
    for row in rows:
        row = dict(row)
        if volatile:
            out.append(row)
            continue
        # The invariant is about the VERDICT, not about the deletion. Keying it
        # on "did we just strip a command" meant that once the command stopped
        # being loaded at all -- after the shard was split -- there was nothing
        # to strip, the branch never fired, and every resume rendered with a
        # null way back again. The same bug, reached from the opposite side.
        if row.get("verdict") == "resume" and not row.get("url"):
            # SUBSTITUTE, never delete. The way back is a three-value enum --
            # command, url, instruction -- and "the instruction is a value, not
            # a null". Stripping the command and leaving nothing produced
            # exactly the state the enum was written to forbid: a RESUME label
            # with nothing under it. The machine comes from the row's own
            # field, never from the reader's.
            row["command"] = None
            row["local_only"] = True
            row["instruction"] = (
                "Recorded on %s. In your product-os clone THERE — not your "
                "home directory — run `python3 tools/index.py --ways-back`. "
                "That prints the resume command for every chat worth "
                "returning to. It is machine-local, so this page cannot "
                "print it."
                % (row.get("machine") or "the machine that indexed it"))
        # The session id is the identifier, not just the command that wraps
        # it. Nulling one and publishing the other leaves the private half on
        # the public surface -- which is how this got shipped the first time.
        row["id"] = None
        out.append(row)
    return out


def local_ways_back(root):
    """key -> command, from the git-ignored half. Empty on any machine that has
    not indexed, which is the honest answer there."""
    out = {}
    shard_dir = os.path.join(root, "state", "threads", "by-machine")
    if not os.path.isdir(shard_dir):
        return out
    for name in sorted(os.listdir(shard_dir)):
        if not name.endswith(".local.json"):
            continue
        with open(os.path.join(shard_dir, name), "r", encoding="utf-8") as fh:
            try:
                rows = json.load(fh).get("threads") or []
            except ValueError:
                continue
        for row in rows:
            if row.get("key"):
                out[row["key"]] = row.get("command")
    return out


def all_threads(root, manual, volatile=False):
    """Every indexed chat, ONCE, newest first.

    `threads_for()` answers "which chats touch this task" and is right for a
    kickoff prompt. The dashboard asks the opposite question -- "what was I
    doing in each chat" -- and looping items over threads rendered one chat
    once per item it cites. One thread here cites FIFTY, so 15 chats became 52
    rows whose primary label was an item id, because the loop's subject was the
    item and not the chat.
    """
    out = []
    ways = local_ways_back(root) if volatile else {}
    for path in _context.tracked_shards(root):
        if True:
            with open(path, "r", encoding="utf-8") as fh:
                try:
                    shard = json.load(fh)
                except ValueError:
                    continue
            for thread in shard.get("threads") or []:
                out.append({
                    "machine": shard.get("machine"),
                    "tool": thread.get("tool"),
                    "title": thread.get("title") or thread.get("key"),
                    "verdict": thread.get("verdict"),
                    "reason": thread.get("verdict_reason"),
                    "command": ways.get(thread.get("key")),
                    "id": None,
                    "items": thread.get("items") or [],
                    "last_active": (thread.get("last_active") or "")[:10],
                })
    for key, entries in sorted(manual.items()):
        for entry in entries:
            out.append({
                "machine": entry.get("machine"), "tool": "web",
                "title": "a web chat, recorded by hand", "verdict": "resume",
                "reason": "no transcript exists on disk; this pointer is the "
                          "only record of it",
                "command": None, "id": None, "items": [key],
                "url": entry.get("url"), "last_active": entry.get("recorded") or "",
            })
    out.sort(key=lambda r: (r.get("last_active") or "", r.get("title") or ""),
             reverse=True)
    return redact(out, volatile)


def render(node, model, entries, stamp, repos_spec, root, manual,
           volatile=True):
    ruled = _context.ruled_out_for(node, entries)[:MAX_RULED_OUT]
    repos = node.get("repos") or []
    machine = node.get("machine_affinity")
    gate = node.get("gate") or "none"
    returns = redact(threads_for(root, node.id, manual), volatile)

    lines = [
        "Cite %s in your first message." % node.id,
        "",
        "# %s — %s" % (node.id, node.title),
        "",
        "%s · %s · gate %s%s"
        % (node.project, node.status, gate,
           " · machine %s" % machine if machine else ""),
        "Freshness: %s"
        % _context.freshness(root, node, stamp, repos_spec, volatile),
        "",
    ]

    # Inherited from the brief along with `decisions_in_force` below -- the two
    # sections kickoff did not already cover (`R-071`). Placed high on purpose:
    # a correction is only real where it is read, and the foot of a prompt is
    # not where a session looks before starting.
    if node.status == "done" and node.get("closed_origin") != "his-word":
        lines += [
            "> ## ⚠ CLOSED ON MY JUDGEMENT, NOT CONFIRMED",
            ">",
            "> A machine decided this was finished. Marcelo has not said so.",
            "> Confirm from a terminal: `python3 tools/backlog.py --unconfirmed`",
            "",
        ]

    # --- the project's own description, injected into every one of its tasks
    #
    # This is the point of `description` being a field rather than prose in
    # the project body: a session that has never seen this portfolio gets the
    # frame before the task, in every prompt, without anyone remembering to
    # paste it. Kept to one short paragraph on purpose -- this file has a
    # ~2-3 KB target and it is spent on operands, not preamble.
    project = model.projects.get(node.project)
    description = (project.get("description") or "").strip() if project else ""
    if description:
        lines += ["## Project context", "", description, ""]
    elif project:
        lines += ["## Project context", "",
                  "`%s` has no description written yet, so this prompt carries "
                  "no project framing. That is a gap, not a clean slate."
                  % node.project, ""]

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
    if node.status == "blocked":
        lines.append("Marked BLOCKED by him. Do not start it without asking why.")
    found = node.get("evidence_found") or []
    if found:
        lines.append("Evidence on file: %s."
                     % ", ".join(str(e.get("sha") or e.get("path"))
                                 for e in found[:5]))
    else:
        lines.append("No evidence recorded. It cannot be closed until "
                     "something can be clicked.")
    nxt = _context.whats_next(node)
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
    project_repos = (project.get("repos") or []) if project else []
    if repos:
        lines.append("Repo: %s. product-os TRACKS the work; it does not host "
                     "it. Make the change there and come back only to write "
                     "the handoff." % ", ".join("`%s`" % r for r in repos))
    elif project and not project_repos:
        # A project with no repository AT ALL is a different fact from a task
        # that forgot to name one, and telling a session to "find out where
        # the work lives" when the answer is "nowhere, it is a GPU box" sends
        # it looking for something that does not exist.
        lines.append("**`%s` has no repository.** Nothing about this task can "
                     "be verified from commits, so its status changes only "
                     "when Marcelo says so. Do not report it as stale, and do "
                     "not close it on anything but his word or a dated note."
                     % node.project)
    else:
        lines.append("This task names no repo, though `%s` has one (%s). Find "
                     "out where the work lives before starting."
                     % (node.project,
                        ", ".join("`%s`" % r for r in project_repos)))
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
            elif row.get("local_only"):
                lines.append("  A verified way back exists on %s, but it names "
                             "that machine's paths and the session id, so it is "
                             "not republished. In your product-os clone THERE, "
                             "run `python3 tools/kickoff.py %s`."
                             % (row.get("machine") or "that machine", node.id))
            elif row.get("url"):
                lines.append("  %s" % row["url"])
            elif row.get("web_only_elsewhere"):
                lines.append("  A web chat is recorded%s. Its URL is in %s, "
                             "which is deliberately not committed — open it "
                             "from that machine."
                             % (" on %s" % row["machine"] if row["machine"]
                                else "", MANUAL_LOCAL))
            elif row["verdict"] == "resume":
                # Names the machine rather than saying "this machine". Latent
                # rather than live -- every resume currently carries a command
                # -- but a claim about the reader's box in a committed file is
                # the same defect whether or not it happens to render today.
                lines.append("  No verified way back was found%s. Open it from "
                             "the app's own session picker."
                             % (" on %s" % row["machine"] if row.get("machine")
                                else ""))
    else:
        lines.append("None indexed. Starting fresh is correct.")
        lines.append("If you are in a web chat, record it so it is reachable "
                     "next time — and mind which half goes where:")
        lines.append("  `%s` (tracked, public): `%s: <machine> <date>`"
                     % (MANUAL, node.id))
        lines.append("  `%s` (git-ignored): the URL." % MANUAL_LOCAL)
        lines.append("  " + _context.POINTER_RULE_LOCAL)
    lines.append("")

    # --- decisions in force, inherited from the brief (R-071)
    rulings = _context.decisions_in_force(node, model)
    if rulings:
        lines += ["## Decisions in force", ""]
        for dec_id, ruling, title in rulings:
            lines.append("- **%s**%s — %s"
                         % (dec_id, " (%s)" % ruling if ruling else "", title))
        lines.append("")

    # --- rules
    lines += [
        "## Rules",
        "",
        "- Nothing is done without evidence — a commit SHA, a file path, or a",
        "  dated note. If you cannot produce one, it is not done. Say so.",
        "- Say \"I couldn't look\", never \"no changes\". An empty result and an",
        "  unreachable repo are different facts.",
        "- Do not write his decided fields: project, gate, machine_affinity,",
        "  parked/dropped, or the evidence rule. Draft into state/drafts/",
        "  instead — never straight into the task.",
        "- Do not reorder state/backlog.md. That file is his judgement, and it",
        "  is the only order there is. Say so once if you disagree, then work",
        "  on what he put at the top.",
        "",
    ]
    return "\n".join(lines)


def generate(root, model, target, volatile=True, manual=None):
    entries = _context.parse_register(root)
    stamp = _context.read_stamp(root)
    manual = load_manual(root) if manual is None else manual
    with open(os.path.join(root, "state", "repos.json"), "r",
              encoding="utf-8") as fh:
        repos_spec = {k: v for k, v in json.load(fh).items()
                      if not k.startswith("_")}
    written = []
    for node in model.nodes.values():
        if not node.is_active:
            continue
        text = render(node, model, entries, stamp, repos_spec, root, manual,
                      volatile)
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
        entries = _context.parse_register(root)
        stamp = _context.read_stamp(root)
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
