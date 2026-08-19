#!/usr/bin/env python3
"""Per-item briefs. Regenerated wholesale on every build; never hand-edited.

    python3 tools/brief.py GB-001        one brief, to stdout
    python3 tools/brief.py --all         every active item, into build/briefs/

A brief is what a session reads instead of the chat history it cannot see:
where this stands, what is next, what is ALREADY RULED OUT, which decisions are
in force, and how stale all of that is.

## The freshness stamp is never optional

Every brief carries one, including when the answer is "I don't know". A brief
without a stamp reads as current, and a brief that is silently three weeks
behind is exactly the failure this repo exists to prevent -- it is the same
shape as `PROJECT-STATE.md` listing two prompts as pending that had already
shipped.

So the stamp has three honest forms and one of them always prints:

    (no audit has ever run -- freshness unknown)
    last audit 2026-08-19 (today) - clean at 108 unattributed
    WARNING 6 commits in gimbal-bench since the last audit

## Day one names the absence

An item with no handoff, no ruled-out match and no ruling in force must SAY so.
Empty headings read as "nothing to worry about"; the absence of a record is not
the absence of a fact, and on day one almost everything is absent.
"""

import argparse
import datetime
import json
import os
import re
import sys

import _fm
import _git
import _model

STAMP_FILE = "build/audit-stamp.json"
REGISTER = "wiki/ruled-out.md"
MAX_RULED_OUT = 4


def parse_register(root):
    path = os.path.join(root, REGISTER)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    entries = []
    for chunk in re.split(r"\n## ", "\n" + text)[1:]:
        title = chunk.split("\n", 1)[0].strip()
        match = re.search(r"^\*\*keywords:\*\*(.+)$", chunk, re.M)
        if not match:
            continue
        cut = re.search(r"\n(?:---\s*$|# )", chunk, re.M)
        body = chunk[:cut.start()] if cut else chunk
        words = {w.strip().lower() for w in re.split(r"[·,]", match.group(1))
                 if w.strip()}
        # Collect the first whole PARAGRAPH, not the first line. A single line
        # from the middle of a wrapped paragraph ends mid-clause and reads as a
        # transcription error rather than an excerpt.
        first, buf = "", []
        for line in body.splitlines()[1:]:
            line = line.strip()
            if line.startswith(("**keywords", "**source")):
                continue
            if not line:
                if buf:
                    break
                continue
            if line.startswith(("|", "#")):
                continue
            buf.append(line.lstrip("> "))
        if buf:
            first = " ".join(buf)
        entries.append((title, words, first))
    return entries


def read_stamp(root):
    path = os.path.join(root, STAMP_FILE)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except ValueError:
        return None


def freshness(root, node, stamp, repos_spec, volatile=True):
    """One line, always. Names what it could not check.

    `volatile=False` drops the "+N commits since the audit" delta.

    That delta is a function of the local working copy's HEAD, so a COMMITTED
    copy of this line is invalidated by the very commit that publishes it:
    measured `+9` before a commit and `+10` after, which made `public/`
    permanently out of sync and shipped a stale stamp to a live URL. No amount
    of "regenerate before committing" fixes it -- regenerating and committing
    increments it again.

    So the published surface carries only the DURABLE half: when the last audit
    ran, over what window, and what it found. That is the fact a remote
    consumer needs and it does not move between audits. The live delta stays in
    `build/`, for the person at the keyboard who can act on it.
    """
    if not stamp:
        return ("(no audit has ever run — freshness unknown. "
                "`python3 tools/audit.py` sets this.)")
    when = stamp.get("date", "?")
    age = ""
    try:
        days = (datetime.date.today()
                - datetime.date.fromisoformat(when)).days
        age = "today" if days == 0 else "%d day%s ago" % (days, "" if days == 1 else "s")
    except ValueError:
        pass

    # Offline delta, where a local clone exists. Repos without one are NAMED,
    # never silently treated as unchanged.
    moved, unchecked = [], []
    for name in node.get("repos") or []:
        head = (stamp.get("heads") or {}).get(name)
        spec = repos_spec.get(name) or {}
        local = spec.get("local")
        local = os.path.expanduser(local) if local else None
        if not head or not local or not os.path.isdir(local):
            unchecked.append(name)
            continue
        out = _git._run(["git", "-C", local, "rev-list", "--count",
                         "%s..HEAD" % head])
        if out is None:
            unchecked.append(name)
            continue
        try:
            n = int(out)
        except ValueError:
            unchecked.append(name)
            continue
        if n:
            moved.append("%s +%d" % (name, n))

    line = "last audit %s (%s)" % (when, age) if age else "last audit %s" % when
    if stamp.get("group_d") is not None:
        line += " · %d commits unattributed then" % stamp["group_d"]
    if moved and volatile:
        line = "⚠ %s since the last audit — %s" % (", ".join(moved), line)
    if unchecked:
        line += " · could not check %s offline" % ", ".join(sorted(unchecked))
    return line


def ruled_out_for(node, entries):
    keywords = {str(k).strip().lower() for k in (node.get("keywords") or [])}
    if not keywords:
        return []
    scored = []
    for title, words, first in entries:
        overlap = keywords & words
        if overlap:
            scored.append((len(overlap), title, first, sorted(overlap)))
    scored.sort(key=lambda r: (-r[0], r[1]))
    return scored[:MAX_RULED_OUT]


def whats_next(node):
    """The last handoff's Next line, or an honest absence."""
    body = node.body or ""
    nexts = re.findall(r"^\*\*Next:\*\*\s*(.+)$", body, re.M)
    if nexts:
        return nexts[-1].strip()
    return None


def decisions_in_force(node, model):
    out = []
    parent = node.get("parent_ruling")
    if parent and parent in model.decisions:
        d = model.decisions[parent]
        out.append((d.id, d.get("ruling_id"), d.title))
    for decision in sorted(model.decisions.values(), key=lambda d: d.id):
        if decision.id == parent:
            continue
        if decision.project == node.project and decision.get("propagates_to"):
            out.append((decision.id, decision.get("ruling_id"), decision.title))
    return out[:4]


def render(node, model, entries, stamp, repos_spec, root, volatile=True):
    lines = ["# %s · %s" % (node.id, node.title), ""]
    lines.append("`%s` · %s · lane %s · gate %s%s" % (
        node.project, node.effective_status, node.get("lane"),
        node.get("gate") or "none",
        " · machine %s" % node.get("machine_affinity")
        if node.get("machine_affinity") else ""))
    if node.status == "done" and node.get("closed_origin") != "his-word":
        lines += ["",
                  "> ## ⚠ CLOSED ON MY JUDGEMENT, NOT CONFIRMED",
                  ">",
                  "> A machine decided this was finished. Marcelo has not said so.",
                  "> The evidence below is what I found; nobody has agreed it is "
                  "enough.",
                  ">",
                  "> Confirm in a sentence: "
                  "`apply.py --decided %s=status:done --said \"...\"`" % node.id]
    lines += ["", "**Freshness:** %s" % freshness(root, node, stamp, repos_spec, volatile), ""]

    lines += ["## Where this stands", ""]
    if node.effective_status == "blocked":
        lines.append("**Blocked** by %s." % ", ".join(node.blockers))
    lines.append("Score %.1f · leverage %d%s · %d min."
                 % (node.score, node.leverage,
                    " (%s)" % ", ".join(sorted(node.reach, key=_fm.sort_key))
                    if node.reach else "",
                    node.effort_minutes))
    found = node.get("evidence_found") or []
    if found:
        lines.append("")
        lines.append("Evidence on file: %s" % ", ".join(
            "`%s`" % (e.get("sha") or e.get("path") or "?") for e in found[:6]))
    else:
        lines.append("")
        lines.append("**No evidence recorded yet.** This item cannot be closed "
                     "until something can be clicked.")

    lines += ["", "## What's next", ""]
    nxt = whats_next(node)
    lines.append(nxt if nxt else
                 "**No handoff recorded.** Nobody has written down where this "
                 "was left, so the next session starts from the item body.")

    lines += ["", "## Already ruled out", ""]
    hits = ruled_out_for(node, entries)
    if hits:
        lines.append("Read these before proposing an approach:")
        lines.append("")
        for _n, title, first, overlap in hits:
            lines.append("- **%s** — _matched on %s_" % (title, ", ".join(overlap)))
            if first:
                lines.append("  %s" % first)
    else:
        lines.append("**Nothing in `wiki/ruled-out.md` matches this item's "
                     "keywords** (%s). That is not the same as nothing having "
                     "been ruled out — skim the register."
                     % (", ".join(sorted(str(k) for k in
                                         (node.get("keywords") or []))) or "none"))

    lines += ["", "## Decisions in force", ""]
    rulings = decisions_in_force(node, model)
    if rulings:
        for dec_id, ruling, title in rulings:
            lines.append("- **%s**%s — %s"
                         % (dec_id, " (%s)" % ruling if ruling else "", title))
    else:
        lines.append("**No ruling is recorded against this item.** It is "
                     "parented to nothing, which means nobody has decided how "
                     "it should go.")

    lines += ["", "---", "",
              "_Generated by `tools/brief.py` on every build. Never hand-edit: "
              "`build/` is rebuilt wholesale._"]
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("item", nargs="?")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--out")
    args = parser.parse_args(argv)

    root = _model.find_root()
    model = _model.Model.load(root)
    entries = parse_register(root)
    stamp = read_stamp(root)
    with open(os.path.join(root, "state", "repos.json"), "r",
              encoding="utf-8") as fh:
        repos_spec = {k: v for k, v in json.load(fh).items()
                      if not k.startswith("_")}

    if args.item:
        node = model.nodes.get(args.item.upper())
        if node is None:
            sys.stderr.write("no such item: %s\n" % args.item)
            return 2
        sys.stdout.write(render(node, model, entries, stamp, repos_spec, root))
        return 0

    out_dir = args.out or os.path.join(root, "build", "briefs")
    os.makedirs(out_dir, exist_ok=True)
    written = 0
    for node in model.nodes.values():
        if not (args.all or node.is_active):
            continue
        path = os.path.join(out_dir, "%s.md" % node.id)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(render(node, model, entries, stamp, repos_spec, root))
        written += 1
    print("wrote %d brief(s) to %s" % (written, os.path.relpath(out_dir, root)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
