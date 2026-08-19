#!/usr/bin/env python3
"""Create a capture, an item, or a question.

    python3 tools/new.py capture "zigbee thing weird at high brightness"
    python3 tools/new.py item --project robotic-spotlight --title "..."
    python3 tools/new.py question --title "..."

Capture takes no options beyond the text on purpose. There is no project flag,
no priority flag, nothing to ask about. If capture ever asks a question,
capture is broken -- triage does all of that later, in batch.
"""

import argparse
import datetime
import hashlib
import os
import re
import sys

import _fm
import _model


def today():
    return datetime.date.today().isoformat()


def slugify(text, limit=48):
    slug = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return slug[:limit].rstrip("-") or "untitled"


def machine_id(root):
    """Resolve this machine: $PRODUCT_OS_MACHINE, then hostname lookup."""
    env = os.environ.get("PRODUCT_OS_MACHINE")
    if env:
        return env
    import socket
    hostname = socket.gethostname().split(".")[0]
    directory = os.path.join(root, "state", "machines")
    if os.path.isdir(directory):
        import json
        for name in sorted(os.listdir(directory)):
            if not name.endswith(".json"):
                continue
            with open(os.path.join(directory, name), "r", encoding="utf-8") as fh:
                try:
                    spec = json.load(fh)
                except ValueError:
                    continue
            if spec.get("hostname", "").lower() == hostname.lower():
                return spec.get("id") or name[:-5]
    return hostname


def next_id(root, prefix):
    """max+1 within this machine's stripe.

    One machine is registered, so this is plain max+1 today. Striping
    (work-laptop 001-999, second machine 1001-1999) becomes necessary the day a
    second machine registers, and migrating then means renaming files that do
    not exist yet.
    """
    highest = 0
    for base, _dirs, files in os.walk(os.path.join(root, "state")):
        for name in files:
            match = re.match(r"^(%s)-(\d{3,})-" % prefix, name)
            if match:
                highest = max(highest, int(match.group(2)))
    return "%s-%03d" % (prefix, highest + 1)


def cmd_capture(root, args):
    text = " ".join(args.text).strip()
    if not text:
        sys.stderr.write("nothing to capture\n")
        return 2
    stamp = datetime.datetime.now(datetime.timezone.utc)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:6]
    machine = machine_id(root)
    name = "%s-%s-%s.md" % (stamp.strftime("%Y%m%dT%H%M"), machine, digest)
    path = os.path.join(root, "state", "inbox", name)
    fm = {
        "captured": stamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "machine": machine,
        "source": os.environ.get("PRODUCT_OS_SOURCE", "cli"),
        "cwd": os.environ.get("PRODUCT_OS_CWD") or _tilde(os.getcwd()),
    }
    _fm.write(path, fm, text, "capture")
    print(os.path.relpath(path, root))
    return 0


def _tilde(path):
    home = os.path.expanduser("~")
    return "~" + path[len(home):] if path.startswith(home) else path


def cmd_item(root, args):
    prefix = None
    for key, project in _fm.PREFIX_PROJECT.items():
        if project == args.project:
            prefix = key
            break
    if prefix is None:
        sys.stderr.write("unknown project: %s\n" % args.project)
        return 2
    item_id = next_id(root, prefix)
    fm = {
        "id": item_id,
        "title": args.title,
        "project": args.project,
        "status": "next",
        "lane": args.lane,
        "gate": args.gate,
        "machine_affinity": args.machine,
        "impact": args.impact,
        "confidence": args.confidence,
        "effort_minutes": args.minutes,
        "cognitive_load": args.load,
        "lead_time_days": args.lead,
        "cost_usd": args.cost,
        "unblocks": [],
        "keywords": [k.strip() for k in (args.keywords or "").split(",") if k.strip()],
        "evidence": [],
        "created": today(),
        "updated": today(),
    }
    path = os.path.join(root, "state", "projects", args.project, "items",
                        "%s-%s.md" % (item_id, slugify(args.title)))
    body = args.body or "<!-- Why this matters. Then ## Acceptance, then ## Handoffs. -->\n"
    _fm.write(path, fm, body, "item")
    print(os.path.relpath(path, root))
    return 0


def cmd_question(root, args):
    question_id = next_id(root, "Q")
    fm = {
        "id": question_id,
        "title": args.title,
        "project": args.project,
        # "next", not "open": questions share the item status vocabulary because
        # they share the ranking pipeline. A second vocabulary would fail
        # validate.py's enum check on the first question ever created.
        "status": "next",
        "gates": [],
        "impact": args.impact,
        "confidence": args.confidence,
        "effort_minutes": args.minutes,
        "cognitive_load": args.load,
        "lead_time_days": 0,
        "keywords": [k.strip() for k in (args.keywords or "").split(",") if k.strip()],
        "evidence": [],
        "created": today(),
        "updated": today(),
    }
    path = os.path.join(root, "state", "questions",
                        "%s-%s.md" % (question_id, slugify(args.title)))
    _fm.write(path, fm, args.body or "", "question")
    print(os.path.relpath(path, root))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    cap = sub.add_parser("capture")
    cap.add_argument("text", nargs="+")

    item = sub.add_parser("item")
    item.add_argument("--project", required=True)
    item.add_argument("--title", required=True)
    item.add_argument("--lane", default="infra")
    item.add_argument("--gate", default="none")
    item.add_argument("--machine", default=None)
    item.add_argument("--impact", type=int, default=3)
    item.add_argument("--confidence", type=int, default=3)
    item.add_argument("--minutes", type=int, default=60)
    item.add_argument("--load", default="medium")
    item.add_argument("--lead", type=int, default=0)
    item.add_argument("--cost", type=float, default=None)
    item.add_argument("--keywords", default="")
    item.add_argument("--body", default=None)

    question = sub.add_parser("question")
    question.add_argument("--title", required=True)
    question.add_argument("--project", default=None)
    question.add_argument("--impact", type=int, default=3)
    question.add_argument("--confidence", type=int, default=3)
    question.add_argument("--minutes", type=int, default=60)
    question.add_argument("--load", default="medium")
    question.add_argument("--keywords", default="")
    question.add_argument("--body", default=None)

    args = parser.parse_args(argv)
    root = _model.find_root()
    return {"capture": cmd_capture, "item": cmd_item,
            "question": cmd_question}[args.cmd](root, args)


if __name__ == "__main__":
    sys.exit(main())
