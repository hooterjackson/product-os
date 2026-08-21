#!/usr/bin/env python3
"""The agent-facing surface: llms.txt, the JSON API, and kickoff prompts.

    python3 tools/publish.py            write public/ and build/
    python3 tools/publish.py --out DIR  write one target
    python3 tools/publish.py --check    regenerate and diff; exit 1 if stale

## Why this is committed and `build/` is not

`build/` is git-ignored on purpose -- computed values must never become
authoritative. That rule is right and it stays.

But this surface has one job: **Marcelo opens a chat on any computer, pastes two
lines, and that session picks up the current state.** A phone. The bench PC.
claude.ai. A machine he has never set up. No clone, no plugin, no install --
the plugin is a convenience for machines he deliberately sets up, and anything
that only works where the repo is cloned has missed the entire point.

Measured 2026-08-19: `build/` is git-ignored, product-os has no Pages site, and
`raw.githubusercontent.com` serves committed files with a 200. So a file in
`build/` is fetchable by nobody. `public/` is committed for exactly one reason:
it is the only way the paste works today.

The boundary is preserved by mechanism, not by promise. `publish.py --check`
regenerates and diffs, so `public/` cannot drift from `state/`, and nothing ever
reads `public/` back as authority.

## Keep llms.txt small

It gets pasted into context windows. Every line costs somebody real tokens on
every session, forever. Per-project files exist so a chat about firmware does
not drag the whole portfolio in with it.
"""

import argparse
import difflib
import json
import os
import shutil
import sys

import _fm
import _model
import actions as actions_mod
import _context
import kickoff as kickoff_mod
import surface as surface_mod

RAW = "https://raw.githubusercontent.com/hooterjackson/product-os/main/public"


def freshness_block(root, stamp):
    """Every endpoint says how fresh it is. A consumer must be able to tell
    whether it is reading something current without having to ask.

    There is deliberately no `generated` date. It moved every day, so every
    committed endpoint went stale at midnight with nothing in `state/` having
    changed -- `R-067`. `last_audit` is the date that answers the question a
    consumer is actually asking, and it only moves when an audit runs. The
    real generation record is the commit that carries the file.
    """
    block = {
        "source": "state/ in hooterjackson/product-os",
    }
    if stamp:
        block["last_audit"] = stamp.get("date")
        block["last_audit_window_since"] = stamp.get("window_since")
        block["unattributed_commits_at_last_audit"] = stamp.get("group_d")
    else:
        block["last_audit"] = None
        block["warning"] = ("no audit has ever run; nothing here has been "
                            "checked against the repos")
    return block


def item_json(node, model, position=None):
    """One task. No score, no leverage, no edges -- `DEC-202`.

    `position` is its 1-based place in `state/backlog.md`, or null if he has
    not ordered it yet. That is a fact about a file he wrote, not a computed
    rank, and the distinction is the whole point: a consumer that sorts on
    `position` is reading his judgement rather than re-deriving one.
    """
    return {
        "id": node.id,
        "title": node.title,
        "project": node.project,
        "status": node.status,
        "backlog_position": position,
        "lane": node.get("lane"),
        "gate": node.get("gate") or "none",
        "machine_affinity": node.get("machine_affinity"),
        "repos": node.get("repos") or [],
        "keywords": sorted(str(k) for k in (node.get("keywords") or [])),
        "evidence_found": [
            {"kind": e.get("kind"), "repo": e.get("repo"),
             "sha": e.get("sha"), "path": e.get("path")}
            for e in (node.get("evidence_found") or [])],
        "closed_origin": node.get("closed_origin"),
        "completed": node.get("completed"),
        "kickoff": ("%s/kickoff/%s.md" % (RAW, node.id)
                    if node.is_active else None),
    }


def write(target, rel, text):
    path = os.path.join(target, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def dump(obj):
    return json.dumps(obj, indent=2, sort_keys=True) + "\n"


# ------------------------------------------------------------------ llms.txt

def root_llms(model, stamp, ordered):
    top = ordered[0] if ordered else None
    unconfirmed = [n for n in model.nodes.values()
                   if n.status == "done" and n.get("closed_origin") != "his-word"]
    lines = [
        "# product-os — read this, then start",
        "",
        "Marcelo's priority and context plane for a portfolio of software",
        "projects run through AI chats. You are probably here because he pasted",
        "two lines. Follow the bootstrap in order.",
        "",
        "**BASE** = `%s`" % RAW,
        "All paths below are relative to it.",
        "",
        "## 1 · Bootstrap, in this order",
        "",
        "1. This file. You are done with it after step 4.",
        "2. `BASE/api/now.json` — his backlog IN HIS ORDER, and how fresh it is.",
        "3. Pick the top item, or the one he names.",
        "   Fetch `BASE/api/items/<ID>.json`.",
        "4. Fetch `BASE/kickoff/<ID>.md` — a paste-ready prompt with what is",
        "   known, what is ALREADY RULED OUT, which repo to work in, and the",
        "   rules. That prompt is the product; everything else is a way of",
        "   reaching it.",
        "",
        "Then work. If a step 404s, say so; do not guess the shape.",
        "",
        "## 2 · Rules of engagement",
        "",
        "- **CITE THE ITEM ID IN YOUR FIRST MESSAGE.** `GB-001`, `POS-009`.",
        "  Writing it into the chat is what links this conversation to that work,",
        "  permanently and for free. It costs one token. Nothing else recovers it.",
        "- **Work in the repo the item names, not in product-os.** This repo",
        "  tracks; it does not host. `repos` on the item says where.",
        "- **Nothing is done without evidence** — a commit SHA, a file path, or a",
        "  dated note. If you cannot produce one, it is not done. Say so.",
        "- **Say \"I couldn't look\", never \"no changes.\"** An empty result and an",
        "  unreachable repo are different facts and must never render alike.",
        "- **Do not write his fields.** `impact`, `confidence`, `effort_minutes`,",
        "  `cost_usd`, `unblocks`, `pin`, `gate`, `project`, `parked`/`dropped`",
        "  and the `evidence` rule are his. Propose instead.",
        "",
        "## 3 · The order is his, and it is not negotiable by you",
        "",
        "**`state/backlog.md` is a file Marcelo wrote. Top is next.** There is no",
        "score, no leverage and no dependency graph — they were removed on",
        "2026-08-20 because 9 of 17 adjacent pairs sat inside the 10% band this",
        "repo's own rules say to escalate on (`DEC-202`).",
        "",
        "So do not re-derive an order, do not weigh two tasks against each other,",
        "and do not reorder the file. If you think he has the order wrong, **say",
        "so once with the reason, then work on what he put at the top.** Once.",
        "Not as a preamble to doing it anyway.",
        "",
    ]
    if top:
        lines += ["## 4 · Right now", "",
                  "`%s` — %s" % (top.id, top.title),
                  "%s · gate %s%s"
                  % (top.project, top.get("gate") or "none",
                     " · machine %s" % top.get("machine_affinity")
                     if top.get("machine_affinity") else ""),
                  ""]
    else:
        lines += ["## 4 · Right now", "",
                  "**The backlog is empty.** That is a real state, not an error:",
                  "he authors every task, and the system never creates one. There",
                  "is nothing to start until he adds something.",
                  ""]
    if stamp:
        lines += ["_Last audited %s. %s commits were unattributed then._"
                  % (stamp.get("date"), stamp.get("group_d")), ""]
    else:
        lines += ["_No audit has ever run. Nothing here has been checked "
                  "against the repos._", ""]
    if unconfirmed:
        lines += ["_%d item(s) are marked done on a machine's judgement, "
                  "unconfirmed by him: %s._"
                  % (len(unconfirmed),
                     ", ".join(sorted((n.id for n in unconfirmed),
                                      key=_fm.sort_key))), ""]

    lines += ["## 5 · The five actions — the destination is part of the artifact",
              "",
              "Three destinations and they are NOT interchangeable. Pasting a",
              "\"link yourself to GB-001\" prompt into a fresh chat fails",
              "confusingly.",
              "",
              "| Action | Fetch | Paste into |",
              "|---|---|---|",
              "| Start a task | `BASE/kickoff/<ID>.md` | a **new** chat |",
              "| Tell it what changed | `BASE/reconcile.md` | a **new** chat |",
              "| Link a web chat | `BASE/attach/<ID>.md` | **that** chat |",
              "| Connect a repo | `BASE/connect-repo.md` | an existing chat |",
              "| Capture a thought | `BASE/capture.md` | anywhere |",
              "",
              "## 6 · Endpoints", ""]
    for rel, what in [
            ("api/index.json", "every endpoint, with freshness"),
            ("api/now.json", "the backlog, in his order"),
            ("api/items/<ID>.json", "one item"),
            ("api/projects/<slug>.json", "one project and its items"),
            ("api/threads.json", "indexed chats, with resume-or-restart"),
            ("api/unconfirmed.json", "closed by a machine, not confirmed"),
            ("kickoff/<ID>.md", "START A TASK — paste into a NEW chat"),
            ("reconcile.md", "TELL IT WHAT CHANGED — paste into a NEW chat"),
            ("attach/<ID>.md", "LINK A WEB CHAT — paste into THAT chat"),
            ("connect-repo.md", "ADD A REPO — paste into an existing chat"),
            ("capture.md", "CAPTURE A THOUGHT — type anywhere"),
            ("projects/<slug>/llms.txt", "this file, scoped to one project")]:
        lines.append("- `BASE/%s` — %s" % (rel, what))
    lines += ["",
              "Projects: " + ", ".join(sorted(model.projects)) + ".",
              ""]
    return "\n".join(lines)


def project_llms(slug, project, model, stamp, ordered):
    mine = [n for n in ordered if n.project == slug]
    lines = [
        "# product-os — %s" % slug,
        "",
        (project.get("description") or "").strip(),
        "",
        "Scoped to this project so a chat about it does not drag the whole",
        "portfolio into context.",
        "",
        "**BASE** = `%s` — paths below are relative." % RAW,
        "",
        "## Bootstrap",
        "",
        "1. `BASE/api/projects/%s.json` — this project's items." % slug,
        "2. `BASE/api/items/<ID>.json`, then `BASE/kickoff/<ID>.md`.",
        "3. The whole portfolio, if you need it: `BASE/llms.txt`.",
        "",
        "## Rules",
        "",
        "- **Cite the item ID in your first message.** That is the link.",
        "- Work in %s, not in product-os."
        % (", ".join("`%s`" % r for r in (project.get("repos") or []))
           or "the repo the item names"),
        "- Nothing is done without evidence. Say \"I couldn't look\", never",
        "  \"no changes\".",
        "- The order is his. Do not re-derive one. Disagree once, with a",
        "  reason, then work on what he put at the top.",
        "",
    ]
    if not project.get("may_rule"):
        lines += ["**This project may not issue rulings.** Every item here is",
                  "parented to a ruling in `%s`."
                  % (project.get("decision_authority") or "the authority repo"),
                  ""]
    lines += ["## Open here", ""]
    if mine:
        for node in mine[:8]:
            lines.append("- `%s` %s%s"
                         % (node.id, node.title,
                            " · gate %s" % node.get("gate")
                            if (node.get("gate") or "none") != "none" else ""))
    else:
        lines.append("Nothing from this project is in the backlog right now.")
    lines += [""]
    if stamp:
        lines += ["_Last audited %s._" % stamp.get("date"), ""]
    else:
        lines += ["_No audit has ever run._", ""]
    return "\n".join(lines)


# ---------------------------------------------------------------- the surface

def generate(root, model, target, volatile=False):
    stamp = _context.read_stamp(root)
    entries = _context.parse_register(root)
    with open(os.path.join(root, "state", "repos.json"), "r",
              encoding="utf-8") as fh:
        repos_spec = {k: v for k, v in json.load(fh).items()
                      if not k.startswith("_")}
    ordered = model.backlog()
    position = {n.id: i for i, n in enumerate(ordered, 1)}
    fresh = freshness_block(root, stamp)

    # A chat URL is a private conversation identifier and this repo is PUBLIC
    # (DEC-201). The url no longer lives in a tracked file at all -- presence
    # is committed to `manual.yaml`, the url to the gitignored
    # `manual.local.yaml`. This redaction stays anyway, because publish runs on
    # the machine that HAS the urls: without it the loaded url would be written
    # straight back out into `public/`. Belt and braces, and the braces are the
    # part that was missing when this class shipped three times.
    manual = kickoff_mod.load_manual(root)
    redacted = kickoff_mod.redact_manual(manual)

    write(target, "llms.txt", root_llms(model, stamp, ordered))
    for slug, project in sorted(model.projects.items()):
        write(target, os.path.join("projects", slug, "llms.txt"),
              project_llms(slug, project, model, stamp, ordered))

    # --- the five actions. Everything this tool does is one of these.
    kickoff_mod.generate(root, model, target, volatile,
                         manual=redacted if not volatile else manual)
    surface_mod.generate(root, model, target, volatile)
    actions_mod.generate(root, model, target, stamp, ordered, volatile)

    # --- api
    write(target, os.path.join("api", "now.json"), dump({
        "freshness": fresh,
        "item": None if not ordered else {
            "id": ordered[0].id, "title": ordered[0].title,
            "project": ordered[0].project,
        },
        "backlog": [item_json(n, model, position.get(n.id)) for n in ordered],
        "unlisted": [item_json(n, model) for n in model.unlisted()],
        "counts": {
            "items": len(model.items),
            "active": sum(1 for n in model.items.values() if n.is_active),
            "parked": sum(1 for n in model.items.values()
                          if n.status == "parked"),
            "done": sum(1 for n in model.items.values() if n.status == "done"),
            "decisions": len(model.decisions),
            "blocked": sum(1 for n in model.nodes.values()
                           if n.status == "blocked"),
            "backlog": len(ordered),
            "unlisted": len(model.unlisted()),
        },
    }))

    for node in model.nodes.values():
        write(target, os.path.join("api", "items", "%s.json" % node.id),
              dump({"freshness": fresh,
                    "item": item_json(node, model, position.get(node.id))}))

    for slug, project in sorted(model.projects.items()):
        mine = [n for n in model.nodes.values() if n.project == slug]
        write(target, os.path.join("api", "projects", "%s.json" % slug),
              dump({
                  "freshness": fresh,
                  "project": {
                      "slug": slug, "name": project.get("name"),
                      "description": project.get("description"),
                      "phase": project.get("phase"),
                      "repos": project.get("repos") or [],
                      "may_rule": project.get("may_rule"),
                      "decision_authority": project.get("decision_authority"),
                  },
                  "items": [item_json(n, model, position.get(n.id)) for n in
                            sorted(mine, key=lambda n: (
                                position.get(n.id, 10 ** 6),
                                _fm.sort_key(n.id)))],
              }))

    # Four fields in a thread shard are machine-local and must not be
    # republished. `command` and `cwd` name THIS machine's layout, which is
    # wrong everywhere else -- formd-t1 is Windows. `id` is a private
    # conversation identifier, the same class publish.py already redacts out of
    # `manual.yaml` (R-062). And `path` embeds the home directory in
    # dash-encoded form, `-Users-mlima-Claude-product-os`, which is precisely
    # why the disclosure screen's `/Users/...` pattern never saw it.
    #
    # Measured 2026-08-20: 26 such commands across 4 committed files on a
    # public repo. The redaction existed and covered one of two sources.
    #
    # What survives is what a remote consumer can actually use: that a thread
    # exists, which tasks it cites, its verdict and the reason. You cannot
    # resume from another machine anyway -- `build/` keeps the whole thing for
    # the person at the keyboard who can.
    # `parent` is a session id too -- a forked thread names the one it came
    # from. Redacting `id` and leaving `parent` publishes the same class of
    # identifier through the sibling field, which is this bug's whole shape.
    MACHINE_LOCAL = ("command", "id", "parent", "path", "cwd")

    shard_dir = os.path.join(root, "state", "threads", "by-machine")
    shards = {}
    if os.path.isdir(shard_dir):
        for name in sorted(os.listdir(shard_dir)):
            if not name.endswith(".json"):
                continue
            with open(os.path.join(shard_dir, name), "r",
                      encoding="utf-8") as fh:
                shard = json.load(fh)
            if not volatile:
                shard = dict(shard)
                shard["threads"] = [
                    {k: v for k, v in thread.items() if k not in MACHINE_LOCAL}
                    for thread in shard.get("threads") or []]
                shard["redacted"] = list(MACHINE_LOCAL)
            shards[name[:-5]] = shard
    write(target, os.path.join("api", "threads.json"),
          dump({"freshness": fresh, "by_machine": shards,
                "manual_urls": {k: v for k, v in sorted(redacted.items())},
                "return_paths": {
                    node.id: kickoff_mod.redact(
                        kickoff_mod.threads_for(root, node.id, redacted),
                        volatile)
                    for node in sorted(model.nodes.values(),
                                       key=lambda n: _fm.sort_key(n.id))
                    if kickoff_mod.threads_for(root, node.id, manual)},
                "note": ("A RESUME verdict with no way back is a dead end. "
                         "Web chats have no CLI, so a pointer is written by "
                         "hand -- split: %s %s"
                         % (_context.POINTER_RULE_PUBLIC,
                            _context.POINTER_RULE_LOCAL))}))

    unconfirmed = [n for n in model.nodes.values()
                   if n.status == "done" and n.get("closed_origin") != "his-word"]
    write(target, os.path.join("api", "unconfirmed.json"), dump({
        "freshness": fresh,
        "note": ("Items a machine marked done. Marcelo has confirmed none of "
                 "these. Confirming one is a sentence: "
                 "apply.py --decided <ID>=status:done --said \"...\""),
        "items": [item_json(n, model, position.get(n.id)) for n in
                  sorted(unconfirmed, key=lambda n: _fm.sort_key(n.id))],
    }))

    write(target, os.path.join("api", "index.json"), dump({
        "freshness": fresh,
        "base": RAW,
        "endpoints": sorted(advertised(model)),
    }))


def advertised(model):
    """Every path this surface promises. Used by the CI link check."""
    paths = ["index.html", "assets/tokens.css", "assets/product-os-theme.css",
             "llms.txt", "api/index.json", "api/now.json",
             "api/threads.json", "api/unconfirmed.json",
             "reconcile.md", "connect-repo.md", "capture.md"]
    for slug in model.projects:
        paths.append("projects/%s/llms.txt" % slug)
        paths.append("api/projects/%s.json" % slug)
    for node_id in model.nodes:
        paths.append("api/items/%s.json" % node_id)
    for node_id, node in model.nodes.items():
        if node.is_active:
            paths.append("kickoff/%s.md" % node_id)
            paths.append("attach/%s.md" % node_id)
    return paths


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    root = _model.find_root()
    model = _model.Model.load(root)

    if args.check:
        import tempfile
        tmp = tempfile.mkdtemp(prefix="po-pub-")
        try:
            generate(root, model, tmp)
            live = os.path.join(root, "public")
            drift = []
            for base, _dirs, files in os.walk(tmp):
                for name in files:
                    rel = os.path.relpath(os.path.join(base, name), tmp)
                    a = os.path.join(tmp, rel)
                    b = os.path.join(live, rel)
                    if not os.path.exists(b):
                        drift.append("missing: %s" % rel)
                        continue
                    with open(a, encoding="utf-8") as fa, \
                            open(b, encoding="utf-8") as fb:
                        if fa.read() != fb.read():
                            drift.append("stale: %s" % rel)
            for base, _dirs, files in os.walk(live):
                for name in files:
                    rel = os.path.relpath(os.path.join(base, name), live)
                    if not os.path.exists(os.path.join(tmp, rel)):
                        drift.append("orphan: %s" % rel)
            for line in drift[:20]:
                print(line)
            if drift:
                print("%d file(s) out of sync; run `python3 tools/publish.py`"
                      % len(drift))
                return 1
            print("public/ is in sync with state/")
            return 0
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    # `public/` is committed and served to every machine, so it is generated
    # DURABLE: no ages, no machine-local paths, no session ids. `build/` is
    # git-ignored and only ever read by the person sitting at this keyboard,
    # so it is generated VOLATILE and keeps the live command and the live age.
    #
    # That split was documented in `_context.freshness` and was not actually
    # true -- main() generated both targets with volatile=False, so build/ was
    # as redacted as public/. A promise in a docstring that the code does not
    # keep is worth less than no promise.
    build_dir = os.path.join(root, "build")
    targets = [args.out] if args.out else [os.path.join(root, "public"),
                                           build_dir]
    for target in targets:
        # wholesale: an orphan endpoint that llms.txt no longer advertises is
        # still fetchable, and still answers with something stale.
        for sub in ("api", "assets", "briefs", "projects", "kickoff",
                    "attach"):
            shutil.rmtree(os.path.join(target, sub), ignore_errors=True)
        generate(root, model, target, volatile=(target == build_dir))
        print("wrote %s" % os.path.relpath(target, root))
    return 0


if __name__ == "__main__":
    sys.exit(main())
