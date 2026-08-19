#!/usr/bin/env python3
"""The agent-facing surface: llms.txt, the JSON API, and paste-able briefs.

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
import datetime
import difflib
import json
import os
import shutil
import sys

import _fm
import _model
import brief as brief_mod
import kickoff as kickoff_mod

RAW = "https://raw.githubusercontent.com/hooterjackson/product-os/main/public"


def freshness_block(root, stamp):
    """Every endpoint says how fresh it is. A consumer must be able to tell
    whether it is reading something current without having to ask."""
    block = {
        "generated": datetime.date.today().isoformat(),
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


def item_json(node, model):
    return {
        "id": node.id,
        "title": node.title,
        "project": node.project,
        "status": node.effective_status,
        "authored_status": node.status,
        "lane": node.get("lane"),
        "gate": node.get("gate") or "none",
        "machine_affinity": node.get("machine_affinity"),
        "score": round(node.score, 3),
        "leverage": node.leverage,
        "unblocks": sorted(node.get("unblocks") or [], key=_fm.sort_key),
        "reach": sorted(node.reach, key=_fm.sort_key),
        "blocked_by": sorted(node.blockers, key=_fm.sort_key),
        "effort_minutes": node.effort_minutes,
        "cognitive_load": node.get("cognitive_load"),
        "repos": node.get("repos") or [],
        "keywords": sorted(str(k) for k in (node.get("keywords") or [])),
        "evidence_found": [
            {"kind": e.get("kind"), "repo": e.get("repo"),
             "sha": e.get("sha"), "path": e.get("path")}
            for e in (node.get("evidence_found") or [])],
        "closed_origin": node.get("closed_origin"),
        "completed": node.get("completed"),
        "brief": "%s/briefs/%s.md" % (RAW, node.id),
    }


def write(target, rel, text):
    path = os.path.join(target, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def dump(obj):
    return json.dumps(obj, indent=2, sort_keys=True) + "\n"


# ------------------------------------------------------------------ llms.txt

def root_llms(model, stamp, ranked):
    top = ranked[0] if ranked else None
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
        "2. `BASE/api/now.json` — the ranked list, and how fresh it is.",
        "3. Pick the top item, or the one he names.",
        "   Fetch `BASE/api/items/<ID>.json`.",
        "4. Fetch `BASE/kickoff/<ID>.md` — a paste-ready prompt with what is",
        "   known, what is ALREADY RULED OUT, which repo to work in, and the",
        "   rules. `BASE/briefs/<ID>.md` is the same content without the",
        "   framing, if you only want the state.",
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
        "## 3 · You may disagree with the ranking",
        "",
        "**The score is a label, not a verdict.** It is one arithmetic reading of",
        "guesses he has not reviewed. If what he tells you about his situation —",
        "his time, his energy, where he is sitting, what he actually cares about",
        "today — points somewhere else, **say so once with the reason, then do",
        "what he says.** Once. Not as a preamble to doing it anyway.",
        "",
        "The list is a conversation starter, not a contract.",
        "",
    ]
    if top:
        lines += ["## 4 · Right now", "",
                  "`%s` — %s" % (top.id, top.title),
                  "score %.1f · leverage %d · %d min · gate %s%s"
                  % (top.score, top.leverage, top.effort_minutes,
                     top.get("gate") or "none",
                     " · machine %s" % top.get("machine_affinity")
                     if top.get("machine_affinity") else ""),
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

    lines += ["## 5 · Endpoints", ""]
    for rel, what in [
            ("api/index.json", "every endpoint, with freshness"),
            ("api/now.json", "the ranked list"),
            ("api/items/<ID>.json", "one item"),
            ("api/projects/<slug>.json", "one project and its items"),
            ("api/graph.json", "the dependency graph"),
            ("api/threads.json", "indexed chats, with resume-or-restart"),
            ("api/unconfirmed.json", "closed by a machine, not confirmed"),
            ("kickoff/<ID>.md", "PASTE THIS to start work on an item"),
            ("briefs/<ID>.md", "the paste-able brief"),
            ("projects/<slug>/llms.txt", "this file, scoped to one project")]:
        lines.append("- `BASE/%s` — %s" % (rel, what))
    lines += ["",
              "Projects: " + ", ".join(sorted(model.projects)) + ".",
              ""]
    return "\n".join(lines)


def project_llms(slug, project, model, stamp, ranked):
    mine = [n for n in ranked if n.project == slug]
    lines = [
        "# product-os — %s" % slug,
        "",
        (project.get("north_star") or "").strip(),
        "",
        "Scoped to this project so a chat about it does not drag the whole",
        "portfolio into context.",
        "",
        "**BASE** = `%s` — paths below are relative." % RAW,
        "",
        "## Bootstrap",
        "",
        "1. `BASE/api/projects/%s.json` — this project's items." % slug,
        "2. `BASE/api/items/<ID>.json`, then `BASE/briefs/<ID>.md`.",
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
        "- The score is a label, not a verdict. Disagree once, with a reason,",
        "  then do what he says.",
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
            lines.append("- `%s` %s — score %.1f%s"
                         % (node.id, node.title, node.score,
                            ", gate %s" % node.get("gate")
                            if (node.get("gate") or "none") != "none" else ""))
    else:
        lines.append("Nothing is startable in this project right now.")
    lines += [""]
    if stamp:
        lines += ["_Last audited %s._" % stamp.get("date"), ""]
    else:
        lines += ["_No audit has ever run._", ""]
    return "\n".join(lines)


# ---------------------------------------------------------------- the surface

def generate(root, model, target, volatile=False):
    stamp = brief_mod.read_stamp(root)
    entries = brief_mod.parse_register(root)
    with open(os.path.join(root, "state", "repos.json"), "r",
              encoding="utf-8") as fh:
        repos_spec = {k: v for k, v in json.load(fh).items()
                      if not k.startswith("_")}
    ranked = model.ranked()
    fresh = freshness_block(root, stamp)

    write(target, "llms.txt", root_llms(model, stamp, ranked))
    for slug, project in sorted(model.projects.items()):
        write(target, os.path.join("projects", slug, "llms.txt"),
              project_llms(slug, project, model, stamp, ranked))

    # --- briefs: self-contained, paste-able, no link required to make sense
    for node in model.nodes.values():
        write(target, os.path.join("briefs", "%s.md" % node.id),
              brief_mod.render(node, model, entries, stamp, repos_spec, root,
                               volatile))

    # --- kickoff prompts: the artifact he actually pastes
    kickoff_mod.generate(root, model, target, volatile)

    # --- api
    write(target, os.path.join("api", "now.json"), dump({
        "freshness": fresh,
        "item": None if not ranked else {
            "id": ranked[0].id, "title": ranked[0].title,
            "project": ranked[0].project,
        },
        "ranked": [item_json(n, model) for n in ranked],
        "counts": {
            "items": len(model.items),
            "active": sum(1 for n in model.items.values() if n.is_active),
            "parked": sum(1 for n in model.items.values()
                          if n.status == "parked"),
            "done": sum(1 for n in model.items.values() if n.status == "done"),
            "questions": len(model.questions),
            "decisions": len(model.decisions),
            "blocked": sum(1 for n in model.nodes.values()
                           if n.is_active and n.effective_status == "blocked"),
        },
    }))

    for node in model.nodes.values():
        write(target, os.path.join("api", "items", "%s.json" % node.id),
              dump({"freshness": fresh, "item": item_json(node, model)}))

    for slug, project in sorted(model.projects.items()):
        mine = [n for n in model.nodes.values() if n.project == slug]
        write(target, os.path.join("api", "projects", "%s.json" % slug),
              dump({
                  "freshness": fresh,
                  "project": {
                      "slug": slug, "name": project.get("name"),
                      "north_star": project.get("north_star"),
                      "phase": project.get("phase"),
                      "repos": project.get("repos") or [],
                      "may_rule": project.get("may_rule"),
                      "decision_authority": project.get("decision_authority"),
                  },
                  "items": [item_json(n, model) for n in
                            sorted(mine, key=lambda n: -n.score)],
              }))

    confirmed = model.edges(confirmed_only=True)
    inferred = model.edges(confirmed_only=False)
    write(target, os.path.join("api", "graph.json"), dump({
        "freshness": fresh,
        "nodes": [{"id": n.id, "title": n.title, "project": n.project,
                   "status": n.effective_status, "leverage": n.leverage}
                  for n in sorted(model.nodes.values(),
                                  key=lambda n: _fm.sort_key(n.id))],
        "edges": sorted(
            [{"from": a, "to": b, "kind": "confirmed"}
             for a, targets in confirmed.items() for b in targets] +
            [{"from": a, "to": b, "kind": "inferred"}
             for a, targets in inferred.items() for b in targets
             if b not in confirmed.get(a, set())],
            key=lambda e: (e["from"], e["to"])),
    }))

    shard_dir = os.path.join(root, "state", "threads", "by-machine")
    shards = {}
    if os.path.isdir(shard_dir):
        for name in sorted(os.listdir(shard_dir)):
            if name.endswith(".json"):
                with open(os.path.join(shard_dir, name), "r",
                          encoding="utf-8") as fh:
                    shards[name[:-5]] = json.load(fh)
    manual = kickoff_mod.load_manual(root)
    write(target, os.path.join("api", "threads.json"),
          dump({"freshness": fresh, "by_machine": shards,
                "manual_urls": {k: sorted(v) for k, v in sorted(manual.items())},
                "return_paths": {
                    node.id: kickoff_mod.threads_for(root, node.id, manual)
                    for node in sorted(model.nodes.values(),
                                       key=lambda n: _fm.sort_key(n.id))
                    if kickoff_mod.threads_for(root, node.id, manual)},
                "note": ("A RESUME verdict with no way back is a dead end. "
                         "Web chats have no CLI, so their URLs live in "
                         "state/threads/manual.yaml -- paste one in once.")}))

    unconfirmed = [n for n in model.nodes.values()
                   if n.status == "done" and n.get("closed_origin") != "his-word"]
    write(target, os.path.join("api", "unconfirmed.json"), dump({
        "freshness": fresh,
        "note": ("Items a machine marked done. Marcelo has confirmed none of "
                 "these. Confirming one is a sentence: "
                 "apply.py --decided <ID>=status:done --said \"...\""),
        "items": [item_json(n, model) for n in
                  sorted(unconfirmed, key=lambda n: _fm.sort_key(n.id))],
    }))

    write(target, os.path.join("api", "index.json"), dump({
        "freshness": fresh,
        "base": RAW,
        "endpoints": sorted(advertised(model)),
    }))


def advertised(model):
    """Every path this surface promises. Used by the CI link check."""
    paths = ["llms.txt", "api/index.json", "api/now.json", "api/graph.json",
             "api/threads.json", "api/unconfirmed.json"]
    for slug in model.projects:
        paths.append("projects/%s/llms.txt" % slug)
        paths.append("api/projects/%s.json" % slug)
    for node_id in model.nodes:
        paths.append("api/items/%s.json" % node_id)
        paths.append("briefs/%s.md" % node_id)
    for node_id, node in model.nodes.items():
        if node.is_active:
            paths.append("kickoff/%s.md" % node_id)
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

    targets = [args.out] if args.out else [os.path.join(root, "public"),
                                           os.path.join(root, "build")]
    for target in targets:
        # wholesale: an orphan endpoint that llms.txt no longer advertises is
        # still fetchable, and still answers with something stale.
        for sub in ("api", "briefs", "projects", "kickoff"):
            shutil.rmtree(os.path.join(target, sub), ignore_errors=True)
        generate(root, model, target)
        print("wrote %s" % os.path.relpath(target, root))
    return 0


if __name__ == "__main__":
    sys.exit(main())
