#!/usr/bin/env python3
"""Drain the GitHub issues the dashboard files into actual state.

    python3 tools/intake.py --check      show what is waiting, write nothing
    python3 tools/intake.py              apply it, and close each issue

The page holds no token, so every write leaves through a GitHub issue under
Marcelo's own sign-in. That half worked from the first day the forms existed.
**Nothing read them.** He attributed a chat from his phone, the issue opened
correctly, and the chat did not move -- a button that files a request into a
queue with no consumer, which is indistinguishable from a broken button and
worse than no button, because it looks like it worked.

## The forms are world-writable and the label is not a permission

This repo is public, so any GitHub user can open an issue and the template URL
applies the label for them. Issue text flows into task titles and captures that
end up in a kickoff prompt pasted into a chat with repo write access -- a path
from a stranger to a credentialed agent.

So: the issue BODY only, never comments, and only from an author who passes
BOTH `author_association == "OWNER"` AND `user.login == OWNER_LOGIN`. Either
alone is weaker than it looks -- association is a role that can be granted, and
a login match without it would accept a fork's issue. Comments are never read
at all, because a stranger commenting on his own issue is the same attack one
layer down.

Everything ingested is printed. A refusal is printed louder.

## Origin is preserved, not flattened

An issue is Marcelo speaking, so `confirm` and `close` route through
`apply.py --decided --said` and land stamped `on his word`. What the tool
inferred and what he said must never blur, and an intake tool is exactly where
they would.
"""

import argparse
import json
import os
import re
import subprocess
import sys

import _fm
import _model

REPO = "hooterjackson/product-os"
OWNER_LOGIN = "hooterjackson"
LABELS = ("attribute", "inbox", "task", "confirm", "close")


def gh(args):
    proc = subprocess.run(["gh"] + args, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)
    if proc.returncode != 0:
        return None, proc.stderr.decode().strip()
    return proc.stdout.decode(), None


def open_issues():
    """Every open issue carrying one of our labels.

    Returns (issues, error). An error is NEVER an empty list -- "I could not
    look" rendered as "nothing waiting" is the failure this repo keeps having,
    and here it would silently discard his phone's only write path.
    """
    out, err = gh(["api", "--paginate",
                   "repos/%s/issues?state=open&per_page=100" % REPO])
    if err is not None:
        return None, err
    try:
        rows = json.loads(out) if out.strip().startswith("[") else []
        if not out.strip().startswith("["):
            rows = [r for chunk in re.findall(r"\[.*?\]\s*(?=\[|$)", out,
                                              re.S)
                    for r in json.loads(chunk)]
    except ValueError as exc:
        return None, "unparseable response from gh: %s" % exc
    keep = []
    for row in rows:
        if row.get("pull_request"):
            continue
        labels = {l["name"] for l in row.get("labels") or []}
        if labels & set(LABELS):
            row["_label"] = sorted(labels & set(LABELS))[0]
            keep.append(row)
    return keep, None


def trusted(issue):
    """Both checks, not either. See the module docstring."""
    author = (issue.get("user") or {}).get("login")
    assoc = issue.get("author_association")
    if assoc != "OWNER":
        return False, "author_association is %r, not OWNER" % assoc
    if author != OWNER_LOGIN:
        return False, "author is %r, not %s" % (author, OWNER_LOGIN)
    return True, None


def fields(body):
    """GitHub renders an issue form as `### Label\\n\\n<value>\\n\\n`.

    Keyed by the rendered LABEL, not the field id -- the id never appears in
    the body, so a parser keyed on it silently returns nothing for every field.
    `_No response_` is GitHub's placeholder for an empty optional field and is
    read as absent rather than as that literal string.
    """
    out = {}
    for match in re.finditer(r"^### (.+?)\s*\n(.*?)(?=\n### |\Z)", body or "",
                             re.S | re.M):
        value = match.group(2).strip()
        if value and value != "_No response_":
            out[match.group(1).strip()] = value
    return out


# ------------------------------------------------------------------ handlers

def do_attribute(root, form, issue):
    key = form.get("Its handle")
    project = form.get("Which project")
    if not key or not project:
        return None, "missing handle or project"
    if not re.fullmatch(r"[0-9a-f]{12}", key):
        return None, "%r is not a chat handle" % key
    model = _model.Model.load(root)
    slug = "none" if project == "not one of my projects" else project
    if slug != "none" and slug not in model.projects:
        return None, "unknown project %r" % project
    path = os.path.join(root, "state", "threads", "attribution.yaml")
    with open(path, "r", encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    written, out = False, []
    for line in lines:
        if re.match(r"^%s\s*:" % re.escape(key), line):
            out.append("%s: %s" % (key, slug))
            written = True
        else:
            out.append(line)
    if not written:
        out.append("%s: %s" % (key, slug))
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out).rstrip() + "\n")
    return ("%s attributed to %s" % (key, slug)), None


def do_inbox(root, form, issue):
    text = form.get("What you were about to forget")
    if not text:
        return None, "empty capture"
    env = dict(os.environ, PRODUCT_OS_SOURCE="github-issue")
    proc = subprocess.run(
        [sys.executable, os.path.join(root, "tools", "new.py"), "capture",
         text], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    if proc.returncode != 0:
        return None, proc.stderr.decode().strip()
    return "captured %s" % proc.stdout.decode().strip(), None


def do_task(root, form, issue):
    project = form.get("Project")
    title = (issue.get("title") or "").strip()
    if not title:
        return None, "the issue title is the task, and it is empty"
    if project == "new project":
        return None, ("asks for a NEW project. Creating one is yours, and it "
                      "needs a prefix nothing else uses — do it in a chat")
    model = _model.Model.load(root)
    if project not in model.projects:
        return None, "unknown project %r" % project
    args = [sys.executable, os.path.join(root, "tools", "new.py"), "item",
            "--project", project, "--title", title]
    if form.get("Anything else"):
        args += ["--body", form["Anything else"] + "\n"]
    proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        return None, proc.stderr.decode().strip()
    return "created %s" % proc.stdout.decode().strip(), None


def _apply(root, argv):
    proc = subprocess.run(
        [sys.executable, os.path.join(root, "tools", "apply.py")] + argv,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        return None, (proc.stderr.decode().strip()
                      or proc.stdout.decode().strip())
    return proc.stdout.decode().strip(), None


def do_confirm(root, form, issue):
    task = (form.get("Task") or "").strip().upper()
    verdict = form.get("Was it right?") or ""
    said = form.get("In your words") or issue.get("title") or ""
    if not _fm.parse_id(task):
        return None, "%r is not a task id" % task
    if verdict.lower().startswith("confirm"):
        out, err = _apply(root, ["--decided", '%s=closed_origin:"his-word"'
                                 % task, "--said", said])
        return (out and "%s confirmed closed on your word" % task), err
    out, err = _apply(root, ["--status", "%s=next" % task,
                             "--decided", '%s=closed_origin:null' % task,
                             "--said", said])
    return (out and "%s reopened" % task), err


def do_close(root, form, issue):
    task = (form.get("Task") or "").strip().upper()
    outcome = form.get("What happened") or ""
    evidence = form.get("What proves it") or ""
    said = form.get("In your words") or issue.get("title") or ""
    if not _fm.parse_id(task):
        return None, "%r is not a task id" % task
    if outcome.lower().startswith("won"):
        out, err = _apply(root, ["--decided", '%s=status:"dropped"' % task,
                                 "--said", said])
        return (out and "%s dropped" % task), err
    if not evidence:
        # The truth guard, and it does not bend for him either.
        return None, ("done with no evidence. A commit sha, a file path or a "
                      "dated note — without one it is not done")
    out, err = _apply(root, ["--evidence", "%s=%s" % (task, evidence),
                             "--status", "%s=done" % task,
                             "--decided", '%s=closed_origin:"his-word"' % task,
                             "--said", said])
    return (out and "%s closed on your word, evidence %s" % (task, evidence)), err


HANDLERS = {"attribute": do_attribute, "inbox": do_inbox, "task": do_task,
            "confirm": do_confirm, "close": do_close}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="show what is waiting, write nothing")
    args = parser.parse_args(argv)
    root = _model.find_root()

    issues, err = open_issues()
    if err is not None:
        sys.stderr.write("could not reach GitHub: %s\n"
                         "That is NOT the same as nothing waiting.\n" % err)
        return 2
    if not issues:
        print("nothing waiting on %s" % REPO)
        return 0

    applied, refused = 0, 0
    for issue in sorted(issues, key=lambda r: r["number"]):
        number, label = issue["number"], issue["_label"]
        head = "#%d [%s] %s" % (number, label, issue.get("title") or "")
        ok, why = trusted(issue)
        if not ok:
            print("%s\n  REFUSED — %s" % (head, why))
            refused += 1
            continue
        form = fields(issue.get("body"))
        print("%s\n  by %s (OWNER)" % (head, issue["user"]["login"]))
        for key, value in form.items():
            print("    %s: %s" % (key, value.replace("\n", " ")[:90]))
        if args.check:
            continue
        result, why = HANDLERS[label](root, form, issue)
        if why:
            print("  REFUSED — %s" % why)
            refused += 1
            continue
        print("  %s" % result)
        applied += 1
        gh(["issue", "close", str(number), "--repo", REPO, "--comment",
            "Applied: %s\n\nDrained by `tools/intake.py`." % result])

    print("\n%d applied, %d refused, %d issue(s) seen"
          % (applied, refused, len(issues)))
    if not args.check and applied:
        print("Now: python3 tools/publish.py && git add -A && git commit")
    return 1 if refused else 0


if __name__ == "__main__":
    sys.exit(main())
