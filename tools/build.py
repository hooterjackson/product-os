#!/usr/bin/env python3
"""Regenerate build/ from state/.

Everything written here is computed and git-ignored. Nothing in build/ is ever
read back as authority, and no generator may write outside it -- that is the
computed/decided boundary made physical rather than conventional.

    python3 tools/build.py
    python3 tools/build.py --check-determinism    build twice, diff
"""

import argparse
import filecmp
import json
import os
import shutil
import sys
import tempfile

import _fm
import _model
import brief as brief_mod
import rank as rank_mod


def write(out_dir, rel, text):
    path = os.path.join(out_dir, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def render_now(model):
    ranked = model.ranked()
    lines = ["# Now", ""]
    if not ranked:
        lines += ["Nothing is startable. Every active item is blocked or gated.", ""]
        return "\n".join(lines)
    top = ranked[0]
    lines += [
        "## %s · %s" % (top.id, top.title),
        "",
        "%s · %s · gate %s · %s" % (
            top.project, top.effective_status, top.get("gate") or "none",
            rank_mod.humanize_minutes(top.effort_minutes)),
        "",
        rank_mod.explain(top, model),
        "",
        "```",
    ]
    lines += ["  " + line for line in rank_mod.arithmetic(top)]
    lines += ["```", "", "## Then", ""]
    for index, node in enumerate(ranked[1:8], 2):
        lines.append("%d. **%s** %s — score %.1f" % (
            index, node.id, node.title, node.score))
    lines.append("")
    return "\n".join(lines)


def render_chain(model):
    """The dependency graph, as text. Cross-project edges are marked, because
    those are the ones invisible from inside any single repo."""
    nodes = model.nodes
    confirmed = model.edges(confirmed_only=True)
    inferred_all = model.edges(confirmed_only=False)

    lines = ["# Chain", "",
             "`->` confirmed edge · `~>` inferred, excluded from leverage · "
             "`*` crosses projects", ""]
    roots = [n for n in nodes.values()
             if n.is_active and not n.blockers and
             (confirmed.get(n.id) or inferred_all.get(n.id))]
    roots.sort(key=lambda n: (-n.leverage, _fm.sort_key(n.id)))

    seen = set()

    def walk(node_id, depth, prefix):
        node = nodes[node_id]
        marker = "  " * depth
        lines.append("%s%s%s  %s%s" % (
            marker, prefix, node.id, node.title,
            "" if node.effective_status != "blocked" else "  [blocked]"))
        if node_id in seen:
            return
        seen.add(node_id)
        children = sorted(confirmed.get(node_id, ()), key=_fm.sort_key)
        inferred = sorted(inferred_all.get(node_id, set()) - set(children),
                          key=_fm.sort_key)
        for child in children:
            star = "*" if nodes[child].project != node.project else ""
            walk(child, depth + 1, "-> " + star)
        for child in inferred:
            star = "*" if nodes[child].project != node.project else ""
            walk(child, depth + 1, "~> " + star)

    for root in roots:
        walk(root.id, 0, "")
        lines.append("")

    depth = max_depth(confirmed, {n for n, x in nodes.items() if x.is_active})
    lines += ["", "Deepest confirmed chain: %d hops." % depth]
    isolated = [n.id for n in nodes.values()
                if n.is_active and not n.blockers and not confirmed.get(n.id)
                and not inferred_all.get(n.id)]
    if isolated:
        lines += ["", "No dependencies: " + ", ".join(sorted(isolated, key=_fm.sort_key))]
    return "\n".join(lines) + "\n"


def max_depth(edges, active):
    memo = {}

    def depth(node_id, stack):
        if node_id in memo:
            return memo[node_id]
        if node_id in stack:
            return 0
        best = 0
        for child in edges.get(node_id, ()):
            if child in active:
                best = max(best, 1 + depth(child, stack | {node_id}))
        memo[node_id] = best
        return best

    return max([depth(n, frozenset()) for n in active] or [0])


def render_api(model):
    ranked = model.ranked()
    payload = {
        "generated_from": "state/",
        "item": None if not ranked else {
            "id": ranked[0].id, "title": ranked[0].title,
            "project": ranked[0].project,
            "explanation": rank_mod.explain(ranked[0], model),
        },
        "ranked": [{"id": n.id, "title": n.title, "score": round(n.score, 3),
                    "leverage": n.leverage, "project": n.project}
                   for n in ranked],
        "counts": {
            "items": len(model.items),
            "questions": len(model.questions),
            "decisions": len(model.decisions),
            "blocked": sum(1 for n in model.nodes.values()
                           if n.is_active and n.effective_status == "blocked"),
            "inbox": len(os.listdir(os.path.join(model.root, "state", "inbox")))
            if os.path.isdir(os.path.join(model.root, "state", "inbox")) else 0,
        },
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def build(root, out_dir):
    model = _model.Model.load(root)
    if model.errors:
        for err in model.errors:
            sys.stderr.write("warning: %s\n" % err)
    write(out_dir, "now.md", render_now(model))
    write(out_dir, "chain.md", render_chain(model))
    write(out_dir, "api/now.json", render_api(model))

    # Briefs are not a deferred phase. They are the per-item answer to "where
    # does this stand", and they are regenerated wholesale so they can never
    # drift from state/ the way a hand-maintained file does.
    entries = brief_mod.parse_register(model.root)
    stamp = brief_mod.read_stamp(model.root)
    with open(os.path.join(model.root, "state", "repos.json"), "r",
              encoding="utf-8") as fh:
        repos_spec = {k: v for k, v in json.load(fh).items()
                      if not k.startswith("_")}
    for node in model.nodes.values():
        if not node.is_active:
            continue
        write(out_dir, os.path.join("briefs", "%s.md" % node.id),
              brief_mod.render(node, model, entries, stamp, repos_spec,
                               model.root))
    return model


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=None)
    parser.add_argument("--check-determinism", action="store_true",
                        help="build twice into separate dirs and diff them")
    args = parser.parse_args(argv)

    root = _model.find_root()

    if args.check_determinism:
        # Byte-determinism on one runner is the mechanical proof that two
        # machines with identical state/ produce identical build/.
        first = tempfile.mkdtemp(prefix="po-a-")
        second = tempfile.mkdtemp(prefix="po-b-")
        try:
            build(root, first)
            build(root, second)
            match, mismatch, errors = filecmp.cmpfiles(
                first, second, _relpaths(first), shallow=False)
            if mismatch or errors:
                print("NOT deterministic: %s" % (mismatch + errors))
                return 1
            print("deterministic across %d file(s)" % len(match))
            return 0
        finally:
            shutil.rmtree(first, ignore_errors=True)
            shutil.rmtree(second, ignore_errors=True)

    out_dir = args.out or os.path.join(root, "build")
    build(root, out_dir)
    print("built %s" % os.path.relpath(out_dir, root))
    return 0


def _relpaths(base):
    out = []
    for dirpath, _dirs, files in os.walk(base):
        for name in files:
            out.append(os.path.relpath(os.path.join(dirpath, name), base))
    return sorted(out)


if __name__ == "__main__":
    sys.exit(main())
