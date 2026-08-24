#!/usr/bin/env python3
"""The labels the write path keys on. Declared here, verified against GitHub.

    python3 tools/labels.py --check     exit 1 if one is missing
    python3 tools/labels.py --create    create the missing ones

## Why this exists

`intake.py` drains issues BY LABEL. An issue template that declares a label the
repository does not have is accepted by GitHub, renders a perfect form, and
files the issue **with no label at all** -- silently. Measured 2026-08-21: the
capture form rendered correctly, title pre-filled, one field, right
placeholder, and the sidebar read "Labels — No labels", because neither
`inbox` nor `task` existed.

That is a link to a form that IS there, keyed on something that ISN'T. The
whole write path would have looked healthy and drained nothing.

## Why it is not a unit test

Whether a label exists is a fact about the REMOTE, and the offline suite cannot
know it. A test that shells out and skips when there is no network reports
clean by not running, which is `R-075`. So the shape is checked offline -- the
templates may only declare labels named here -- and the remote fact is checked
in the Pages workflow, where there is always a token.
"""

import argparse
import json
import os
import re
import subprocess
import sys

REPO = "hooterjackson/product-os"

# name -> (colour, description). The description is the contract, so a future
# reader knows what drains it.
REQUIRED = {
    "inbox": ("D4C5A9", "A raw capture. Not a task until he adopts it."),
    "task": ("E2A24C", "Something he decided is worth doing. Drains to the "
                       "bottom of state/backlog.md."),
    "adopt": ("9C937F", "Adopt an audit recommendation into the backlog."),
    "dismiss": ("7D765F", "Dismiss a recommendation. It must not come back."),
    "confirm": ("D6E5F4", "Confirm a closure a machine made without him."),
    "close": ("9C937F", "Close an open task — shipped, or decided against."),
}

TEMPLATE_DIR = os.path.join(".github", "ISSUE_TEMPLATE")


def declared(root):
    """Every label named by an issue template, by file."""
    out = {}
    directory = os.path.join(root, TEMPLATE_DIR)
    if not os.path.isdir(directory):
        return out
    for name in sorted(os.listdir(directory)):
        if not name.endswith((".yml", ".yaml")) or name == "config.yml":
            continue
        with open(os.path.join(directory, name), encoding="utf-8") as fh:
            body = fh.read()
        block = re.search(r"^labels:\s*\n((?:\s*-\s*\S+\n)+)", body, re.M)
        if block:
            out[name] = [ln.strip("- \n") for ln in
                         block.group(1).splitlines() if ln.strip()]
    return out


def remote():
    proc = subprocess.run(
        ["gh", "api", "--paginate", "repos/%s/labels" % REPO],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        return None
    try:
        return {row["name"] for row in json.loads(proc.stdout.decode())}
    except ValueError:
        return None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--create", action="store_true")
    args = parser.parse_args(argv)

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    have = remote()
    if have is None:
        # Never "clean" -- an unreachable remote is a fact we could not check.
        sys.stderr.write("could not reach GitHub to list labels. That is not "
                         "the same as the labels being present.\n")
        return 2

    used = {label for labels in declared(root).values() for label in labels}
    unknown = sorted(used - set(REQUIRED))
    if unknown:
        sys.stderr.write("a template declares %s, which this file does not "
                         "know about\n" % ", ".join(unknown))
        return 1

    missing = sorted(used - have)
    if args.create:
        for name in missing:
            colour, about = REQUIRED[name]
            subprocess.run(["gh", "api", "-X", "POST",
                            "repos/%s/labels" % REPO,
                            "-f", "name=%s" % name,
                            "-f", "color=%s" % colour,
                            "-f", "description=%s" % about],
                           stdout=subprocess.DEVNULL)
            print("created %s" % name)
        missing = sorted(used - (remote() or set()))

    if missing:
        sys.stderr.write(
            "MISSING on %s: %s\n"
            "GitHub accepts a template that names a label the repo does not "
            "have, renders a perfect form, and files with NO label. The write "
            "path would look healthy and drain nothing.\n"
            "  python3 tools/labels.py --create\n" % (REPO, ", ".join(missing)))
        return 1
    print("%d label(s) declared, all present on %s" % (len(used), REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
