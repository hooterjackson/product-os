#!/usr/bin/env python3
"""Shared context helpers: the register, the audit stamp, freshness, handoffs.

Not an artifact. This module was `brief.py`, which generated a second per-item
document alongside the kickoff prompt -- and `kickoff.py`'s output turned out to
be a superset of it except for two sections, both of which now live there
(`R-071`). Two surfaces rendering the same content is how they drift apart, and
drift inside an excerpt is `R-065`.

What survived the brief is everything that was actually load-bearing:

    parse_register      wiki/ruled-out.md -> (title, keywords, first paragraph)
    ruled_out_for       the keyword match that decides which entries a task meets
    read_stamp          the audit stamp
    freshness           one honest line, always -- see its own docstring
    whats_next          the last handoff's Next line, or a stated absence
    decisions_in_force  the rulings a task is parented to
"""

import datetime
import json
import os
import re

import _fm
import _git

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

    `volatile=False` means "this line is about to be COMMITTED", and drops
    every quantity that is a property of this machine at this moment rather
    than of the audit:

        the "+N commits since the audit" delta   -- moves with local HEAD
        the "(2 days ago)" age                   -- moves with the calendar
        "could not check X offline"              -- moves with what is cloned here

    All three make a committed copy wrong without anything in `state/`
    changing. The delta was measured at `+9` before a commit and `+10` after,
    which is `R-061`.

    `R-067` is the same defect four lines further down, left behind by that
    fix: the age. Measured 2026-08-20 -- `publish.py --check` reported **121
    files out of sync on a clean tree**, the whole difference being
    `(today)` -> `(1 day ago)`. `validate.py` was therefore red every day but
    the audit's, which trains a reader to regenerate-and-commit or to stop
    looking. **A guardrail that is red by default is off.**

    So the published surface carries only the DURABLE half: when the last
    audit ran and what it found. That does not move between audits, and it is
    identical on every machine. The live delta stays in `build/`, for the
    person at the keyboard who can act on it -- and, from Phase 2, in
    `index.html`, where a `data-audit-date` attribute lets the browser render
    the age without the bytes ever changing.
    """
    if not stamp:
        return ("(no audit has ever run — freshness unknown. "
                "`python3 tools/audit.py` sets this.)")
    when = stamp.get("date", "?")
    found = ("" if stamp.get("group_d") is None
             else " · %d commits unattributed then" % stamp["group_d"])

    if not volatile:
        return "last audit %s%s" % (when, found)

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

    line = ("last audit %s (%s)%s" % (when, age, found) if age
            else "last audit %s%s" % (when, found))
    if moved:
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


# --- where the work happens, and how to get there ---------------------------
#
# `site.py` will want to offer a way in -- the terminal is one of the three
# paste destinations and a Copy button is the product. That is the moment this
# becomes dangerous, because a card that renders `cd ~/Claude/gimbal-bench`
# from a template is wrong on this machine and looks right.
#
# Measured 2026-08-20: FOUR of the six repos in `state/repos.json` have
# `local: null` -- HomeApp, genio, gimbal-bench and home-ai-infra are not
# cloned on this Mac. `GB-001` is `machine_affinity: formd-t1`, a Windows box.
# A templated `cd ~/Claude/<repo> && claude` is wrong for most of the
# portfolio.
#
# `kickoff.py` does not have this bug, but it is worth being precise about WHY:
# it is right BY OMISSION, not by derivation. It names a repo and a machine and
# emits no path at all, so it cannot emit a wrong one. Its single `$` command
# comes from the thread indexer, where `resume_command()` already returns None
# when the binary is absent. That safety does not transfer to something that
# wants to offer a command.
#
# So the rule is enforced here, once, by construction: a command comes back
# ONLY when the repo is cloned on this machine AND the task is not bound
# elsewhere. Every other case returns a command of None and says why.

NO_REPO = "no-repo"          # the project has no repository at all
ELSEWHERE = "elsewhere"      # bound to another machine
NO_CLONE = "no-clone"        # repo exists, not cloned here
LOCAL = "local"              # cloned here, and this is the right machine


def reach(node, model, repos_spec, machine):
    """How to get to this task's work FROM THIS MACHINE.

    Returns {kind, command, repos, machine, reason}. `command` is None in
    every case but `LOCAL`, and callers must render it rather than build their
    own -- that is the whole point of this function existing.
    """
    project = model.projects.get(node.project)
    repos = list(node.get("repos") or [])
    if not repos and project:
        repos = list(project.get("repos") or [])

    def out(kind, reason, command=None):
        return {"kind": kind, "command": command, "repos": repos,
                "machine": node.get("machine_affinity"), "reason": reason}

    if not repos:
        return out(NO_REPO,
                   "%s has no repository. Nothing here can be verified from "
                   "commits, so its status changes only when Marcelo says so."
                   % (node.project or "this project"))

    affinity = node.get("machine_affinity")
    if affinity and affinity != machine:
        # Checked BEFORE the clone test on purpose. Even a cloned repo is the
        # wrong answer when the work is bound to another machine -- the bench
        # is not this laptop, and a command that runs is not a command that
        # helps.
        return out(ELSEWHERE,
                   "This is %s work. The honest answer is \"resume on %s\", "
                   "not a plan that cannot be executed from here."
                   % (affinity, affinity))

    missing = []
    paths = []
    for name in repos:
        local = (repos_spec.get(name) or {}).get("local")
        expanded = os.path.expanduser(local) if local else None
        if expanded and os.path.isdir(expanded):
            paths.append(local)
        else:
            missing.append(name)
    if missing:
        return out(NO_CLONE,
                   "%s %s not cloned on %s. Clone it, or work on a machine "
                   "that has it — there is no command to give you from here."
                   % (", ".join("`%s`" % m for m in missing),
                      "is" if len(missing) == 1 else "are", machine))

    return out(LOCAL,
               "Cloned here. product-os TRACKS the work; it does not host it.",
               command="cd %s" % paths[0])
