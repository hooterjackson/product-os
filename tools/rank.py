#!/usr/bin/env python3
"""The ranked list. Derived on every run; never stored.

    python3 tools/rank.py                 the list
    python3 tools/rank.py --explain       the top item, and why
    python3 tools/rank.py --time 60       something that finishes in an hour
    python3 tools/rank.py --energy low    mechanical work only
    python3 tools/rank.py --gate none     what can start from this chair
    python3 tools/rank.py --show EL-004   the arithmetic for one item
"""

import argparse
import json
import sys

import _fm
import _model


def humanize_minutes(minutes):
    if minutes < 60:
        return "%d minutes" % minutes
    hours = minutes / 60.0
    if abs(hours - round(hours)) < 0.05:
        hours = int(round(hours))
        return "1 hour" if hours == 1 else "%d hours" % hours
    return "%.1f hours" % hours


def humanize_lead(days):
    return {
        0: "", 1: "a day", 7: "a week", 14: "two weeks",
        21: "three weeks", 30: "a month",
    }.get(days, "%d days" % days)


def humanize_money(amount):
    if amount is None or amount == 0:
        return ""
    if float(amount) == int(amount):
        return "$%d" % int(amount)
    return "$%.2f" % amount


def explain(node, model):
    """One deterministic sentence. No model involved -- see CLAUDE.md."""
    effort = humanize_minutes(node.effort_minutes)
    cost = humanize_money(node.get("cost_usd"))
    lead = node.get("lead_time_days") or 0
    projects = {model.nodes[n].project for n in node.reach if n in model.nodes}
    if node.leverage >= 3 and len(projects) >= 2:
        noun = "workstreams"
    else:
        noun = "item" if node.leverage == 1 else "items"

    parts = [effort]
    if cost:
        parts.append(cost)
    subject = " and ".join(parts)

    if node.leverage == 0:
        return "%s of work; nothing downstream is waiting." % effort.capitalize()

    sentence = "%s stand between you and unblocking %d %s" % (
        subject.capitalize(), node.leverage, noun)
    if lead:
        # Stated, never used as an argument. The lead-time term was removed
        # from the score on 2026-08-19; leaving persuasive language behind
        # would be the ranking arguing for something it no longer computes.
        sentence += " (it also carries %s of lead time, recorded but not " \
                    "ranked on)" % humanize_lead(lead)
    return sentence + "."


def arithmetic(node):
    """Show the working. The plan for this repo published a ranking claim with
    no operands twice; printing the arithmetic is the fix."""
    impact = node.get("impact") or 0
    confidence = node.get("confidence") or 0
    bucket = _model.effort_bucket(node.effort_minutes)
    base = (impact * confidence) / float(bucket)
    lift = 1.0 + _model.LEVERAGE_WEIGHT * node.leverage
    lead = node.get("lead_time_days") or 0
    rows = [
        "effort_bucket(%d min)  = %d" % (node.effort_minutes, bucket),
        "base = (%d x %d) / %d   = %.3f" % (impact, confidence, bucket, base),
        "leverage               = %d  %s" % (
            node.leverage,
            "(" + ", ".join(sorted(node.reach, key=_fm.sort_key)) + ")"
            if node.reach else "(nothing downstream)"),
        "lift = 1 + %.2f x %-2d   = %.3f" % (
            _model.LEVERAGE_WEIGHT, node.leverage, lift),
        "score = %.3f x %.3f     = %.2f" % (base, lift, node.score),
    ]
    if lead:
        rows.append("lead_time_days         = %d  (recorded, does NOT move the "
                    "order -- see _model.py)" % lead)
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--time", type=int, metavar="MIN",
                        help="only items that finish in MIN minutes")
    parser.add_argument("--energy", choices=["low", "medium", "high"])
    parser.add_argument("--gate", help="e.g. none, bench, printer")
    parser.add_argument("--machine")
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument("--all", action="store_true",
                        help="include blocked items")
    parser.add_argument("--explain", action="store_true",
                        help="the top item, with reasoning")
    parser.add_argument("--show", metavar="ID", help="the arithmetic for one item")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    model = _model.Model.load(_model.find_root())
    if model.errors:
        for err in model.errors:
            sys.stderr.write("warning: %s\n" % err)

    if args.show:
        node = model.nodes.get(args.show)
        if node is None:
            sys.stderr.write("no such item: %s\n" % args.show)
            return 2
        print("%s  %s" % (node.id, node.title))
        print()
        for line in arithmetic(node):
            print("  " + line)
        print()
        print("  " + explain(node, model))
        return 0

    ranked = model.ranked(
        time_limit=args.time, energy=args.energy, gate=args.gate,
        machine=args.machine, include_blocked=args.all,
    )

    if args.json:
        print(json.dumps([{
            "id": n.id, "title": n.title, "project": n.project,
            "score": round(n.score, 3), "leverage": n.leverage,
            "status": n.effective_status, "gate": n.get("gate"),
            "effort_minutes": n.effort_minutes,
            "lead_time_days": n.get("lead_time_days") or 0,
            "cost_usd": n.get("cost_usd"),
            "explanation": explain(n, model),
        } for n in ranked], indent=2))
        return 0

    if not ranked:
        print("Nothing is startable under those filters.")
        blocked = [n for n in model.nodes.values()
                   if n.is_active and n.effective_status == "blocked"]
        if blocked:
            print("%d item(s) are blocked. `--all` shows them." % len(blocked))
        return 0

    if args.explain:
        top = ranked[0]
        print("%s  %s" % (top.id, top.title))
        print("%s | %s | gate %s | %s" % (
            top.project, top.effective_status, top.get("gate") or "none",
            humanize_minutes(top.effort_minutes)))
        print()
        print("  " + explain(top, model))
        print()
        for line in arithmetic(top):
            print("  " + line)
        if top.get("pin"):
            print()
            print("  pinned to #%d by you; the math ranks it %d."
                  % (top.get("pin"),
                     1 + sorted(model.ranked(include_blocked=False),
                                key=lambda n: -n.score).index(top)))
        return 0

    width = max(len(n.id) for n in ranked)
    for index, node in enumerate(ranked[:args.limit], 1):
        flags = []
        if node.get("pin"):
            flags.append("pin%d" % node.get("pin"))
        if node.leverage:
            flags.append("unblocks %d" % node.leverage)
        if node.get("lead_time_days"):
            flags.append("%dd lead" % node.get("lead_time_days"))
        cost = humanize_money(node.get("cost_usd"))
        if cost:
            flags.append(cost)
        print("%2d. %-*s  %-6.1f %s" % (index, width, node.id, node.score,
                                        node.title))
        if flags:
            print("    %s  ·  %s" % (humanize_minutes(node.effort_minutes),
                                     "  ·  ".join(flags)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
