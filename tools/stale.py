#!/usr/bin/env python3
"""Find published documents that a later ruling has contradicted.

The one detector in this slice. It exists because without it the seed's
headline finding would be a screenshot of a signal -- true on the day it was
typed and quietly wrong afterwards -- and product-os would become the ninth
hand-maintained state file in a portfolio that already has eight.

The rule is arithmetic, not judgement: a decision has a `decided` date and a
list of documents it propagates to. If the document's last commit predates the
ruling, the document is stale and the ruling wins.

    python3 tools/stale.py
    python3 tools/stale.py --json
"""

import argparse
import json
import os
import subprocess
import sys

import _git
import _model


def load_repos(root):
    path = os.path.join(root, "state", "repos.json")
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return {k: v for k, v in data.items() if not k.startswith("_")}


def gh_last_commit(owner, repo, path, ref):
    """Last commit date for a path, via the API. Used for repos not cloned here."""
    args = ["gh", "api",
            "repos/%s/%s/commits?path=%s&sha=%s&per_page=1" % (owner, repo, path, ref),
            "--jq", ".[0].commit.committer.date"]
    try:
        proc = subprocess.run(args, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, timeout=45)
    except (OSError, subprocess.TimeoutExpired):
        return _git.UNREACHABLE
    if proc.returncode != 0:
        return _git.UNREACHABLE
    out = proc.stdout.decode("utf-8", "replace").strip()
    return out or None


def doc_date(repos, repo_name, doc_path, reached, unreachable):
    spec = repos.get(repo_name)
    if spec is None:
        unreachable.add("%s (not configured)" % repo_name)
        return _git.UNREACHABLE
    local = spec.get("local")
    if local:
        local = os.path.expanduser(local)
        if os.path.isdir(local):
            # fetch first, always -- a stale tracking ref answers 0 and lies
            result = _git.last_commit_date(local, doc_path)
            if result is not _git.UNREACHABLE:
                reached.add(repo_name)
                return result
    owner = spec.get("owner")
    if owner:
        result = gh_last_commit(owner, repo_name, doc_path,
                                spec.get("default_branch") or "HEAD")
        if result is not _git.UNREACHABLE:
            reached.add(repo_name)
            return result
    unreachable.add(repo_name)
    return _git.UNREACHABLE


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = _model.find_root()
    repos = load_repos(root)
    model = _model.Model.load(root)

    reached, unreachable = set(), set()
    findings, skipped = [], []

    for decision in sorted(model.decisions.values(), key=lambda d: d.id):
        decided = decision.get("decided")
        targets = decision.get("propagates_to") or []
        if not decided or not targets:
            continue
        for target in targets:
            repo_name = target.get("repo")
            doc_path = target.get("path")
            last = doc_date(repos, repo_name, doc_path, reached, unreachable)
            if last is _git.UNREACHABLE:
                skipped.append((decision.id, repo_name, doc_path))
                continue
            if last is None:
                continue
            if last[:10] < decided[:10]:
                findings.append({
                    "decision": decision.id,
                    "ruling": decision.get("title"),
                    "decided": decided[:10],
                    "repo": repo_name,
                    "doc": doc_path,
                    "doc_last_edited": last[:10],
                    "days_stale": _days_between(last[:10], decided[:10]),
                    "claim": target.get("claim"),
                })

    findings.sort(key=lambda f: -f["days_stale"])

    if args.json:
        print(json.dumps({
            "findings": findings,
            "coverage": {"reached": sorted(reached),
                         "unreachable": sorted(unreachable),
                         "skipped": skipped},
        }, indent=2))
        return 0

    if findings:
        print("Published documents contradicted by a later ruling:\n")
        for f in findings:
            print("  %s  %s" % (f["repo"], f["doc"]))
            print("    last edited %s, but %s ruled %s (%d days stale)"
                  % (f["doc_last_edited"], f["decision"], f["decided"],
                     f["days_stale"]))
            if f["claim"]:
                print("    the doc still claims: %s" % f["claim"])
            print()
    else:
        print("No published document is behind a ruling.\n")

    # Always printed. A system that says "no changes" when it means
    # "I couldn't look" is worse than no system at all.
    print("Coverage: reached %s%s" % (
        ", ".join(sorted(reached)) or "nothing",
        "" if not unreachable else
        " · unreachable: " + ", ".join(sorted(unreachable))))
    if skipped:
        print("%d ruling/doc pair(s) could not be checked." % len(skipped))
    return 0


def _days_between(earlier, later):
    import datetime
    fmt = "%Y-%m-%d"
    a = datetime.datetime.strptime(earlier, fmt)
    b = datetime.datetime.strptime(later, fmt)
    return (b - a).days


if __name__ == "__main__":
    sys.exit(main())
