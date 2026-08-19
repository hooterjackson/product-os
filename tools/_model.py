#!/usr/bin/env python3
"""Load the authored state and compute everything derived from it.

Nothing in here is ever written back to `state/`. Scores, leverage, effective
status and rank are computed on every run and live only in memory or `build/`.
That is the computed/decided boundary, and it is why there is no ordered list
anywhere in this repository.
"""

import glob
import graphlib
import os

import _fm

# --- scoring constants ------------------------------------------------------
# These are knobs, not truths. Changing one is a decision about how the system
# weighs your time, and should be recorded as such.

LEVERAGE_WEIGHT = 0.25
LEAD_DIVISOR = 7.0

# effort_minutes -> the 1-5 denominator. `effort` is derived, never authored:
# a human estimates minutes far more reliably than an abstract 1-5, and one
# source of truth removes a whole class of cross-machine drift.
EFFORT_BUCKETS = [(15, 1), (60, 2), (240, 3), (960, 4)]

ACTIVE_EXCLUDED = {"done", "dropped", "parked"}
OFFERABLE_GATES = {"none"}


def effort_bucket(minutes):
    for threshold, bucket in EFFORT_BUCKETS:
        if minutes <= threshold:
            return bucket
    return 5


def urgency(lead_time_days):
    """1 + lead/7.

    The spec divides lead time by effort as well, which counts effort twice --
    it is already the score's denominator. Two independent reviews flagged the
    resulting quadratic, and the proposed cap bound at 15.75 days, below this
    portfolio's normal case. Dropping the division removes the problem rather
    than clamping it.

    The trade, recorded honestly: the spec's version means "cheap action,
    expensive clock". This one means just "clock" -- a 40-hour long-lead task
    now gets the same multiplier as a 3-minute one.
    """
    return 1.0 + (lead_time_days or 0) / LEAD_DIVISOR


class Entity(object):
    def __init__(self, kind, path, fm, body):
        self.kind = kind
        self.path = path
        self.fm = fm
        self.body = body
        self.id = fm.get("id", "")
        self.title = fm.get("title", "")
        self.project = fm.get("project", "")
        self.status = fm.get("status", "next")
        # computed
        self.leverage = 0
        self.reach = frozenset()
        self.score = 0.0
        self.effective_status = self.status
        self.blockers = []

    def get(self, key, default=None):
        return self.fm.get(key, default)

    @property
    def is_active(self):
        return self.status not in ACTIVE_EXCLUDED

    @property
    def effort_minutes(self):
        return self.fm.get("effort_minutes") or 1

    def __repr__(self):
        return "<%s %s>" % (self.kind, self.id)


class Model(object):
    def __init__(self, root):
        self.root = root
        self.items = {}
        self.questions = {}
        self.decisions = {}
        self.projects = {}
        self.errors = []

    # -- loading ------------------------------------------------------------

    @classmethod
    def load(cls, root):
        model = cls(root)
        for path in sorted(glob.glob(os.path.join(
                root, "state", "projects", "*", "project.md"))):
            model._add(model.projects, "project", path, key="slug")
        for path in sorted(glob.glob(os.path.join(
                root, "state", "projects", "*", "items", "*.md"))):
            model._add(model.items, "item", path)
        for path in sorted(glob.glob(os.path.join(
                root, "state", "questions", "*.md"))):
            model._add(model.questions, "question", path)
        for pattern in (("state", "decisions", "*.md"),
                        ("state", "projects", "*", "decisions", "*.md")):
            for path in sorted(glob.glob(os.path.join(root, *pattern))):
                model._add(model.decisions, "decision", path)
        model.compute()
        return model

    def _add(self, target, kind, path, key="id"):
        try:
            fm, body = _fm.load(path)
        except _fm.FrontmatterError as exc:
            self.errors.append(str(exc))
            return
        entity = Entity(kind, path, fm, body)
        identifier = fm.get(key, "")
        if not identifier:
            self.errors.append("%s: missing '%s'" % (path, key))
            return
        if identifier in target:
            self.errors.append("%s: duplicate id %s (also %s)"
                               % (path, identifier, target[identifier].path))
            return
        target[identifier] = entity

    # -- graph --------------------------------------------------------------

    @property
    def nodes(self):
        merged = dict(self.items)
        merged.update(self.questions)
        return merged

    def edges(self, confirmed_only=True):
        """id -> set of ids it unblocks.

        Inferred edges are excluded from leverage and never force `blocked`.
        A wrong guessed edge should not be able to make real work invisible --
        that failure is expensive and silent, because you cannot tell
        "correctly blocked" from "wrongly blocked" without re-deriving the
        graph by hand, which is the labour this tool exists to remove.
        """
        out = {}
        nodes = self.nodes
        for node_id, node in nodes.items():
            targets = set(node.get("unblocks") or [])
            if not confirmed_only:
                targets |= set(node.get("unblocks_inferred") or [])
            # questions gate items; same edge direction for scoring purposes
            targets |= set(node.get("gates") or [])
            out[node_id] = {t for t in targets if t in nodes}
        return out

    def compute(self):
        nodes = self.nodes
        edges = self.edges(confirmed_only=True)

        # blockers: X is blocked by A when X is in A.unblocks (confirmed only)
        blockers = {node_id: [] for node_id in nodes}
        for source, targets in edges.items():
            for target in targets:
                blockers[target].append(source)

        for node_id, node in nodes.items():
            node.blockers = sorted(blockers[node_id], key=_fm.sort_key)
            unmet = [b for b in node.blockers if nodes[b].status != "done"]
            if node.status not in ACTIVE_EXCLUDED and unmet:
                node.effective_status = "blocked"
            else:
                node.effective_status = node.status

        # transitive leverage over the ACTIVE subgraph.
        #
        # Excluding done/dropped/parked matters twice over: reachability
        # through a finished node overstates what an item still gates (a lie
        # rank.py would then print in a sentence), and because `dropped` and
        # `parked` are human-authority, leverage stays a pure function of
        # human-authority fields -- which is what makes the authority
        # guarantee true rather than merely stated.
        active = {n for n, node in nodes.items() if node.is_active}
        sorter = graphlib.TopologicalSorter(
            {n: {s for s in edges if n in edges[s] and s in active}
             for n in active}
        )
        try:
            order = list(sorter.static_order())
        except graphlib.CycleError as exc:
            self.errors.append("dependency cycle: %s"
                               % " -> ".join(exc.args[1]))
            order = list(active)

        reach = {}
        for node_id in reversed(order):
            downstream = set()
            for target in edges.get(node_id, ()):
                if target in active:
                    downstream.add(target)
                    downstream |= reach.get(target, set())
            reach[node_id] = downstream

        for node_id, node in nodes.items():
            node.reach = frozenset(reach.get(node_id, ()))
            node.leverage = len(node.reach)
            node.score = self.score(node)

    def score(self, node):
        impact = node.get("impact") or 0
        confidence = node.get("confidence") or 0
        bucket = effort_bucket(node.effort_minutes)
        base = (impact * confidence) / float(bucket)
        lift = 1.0 + LEVERAGE_WEIGHT * node.leverage
        return base * lift * urgency(node.get("lead_time_days"))

    # -- ranking ------------------------------------------------------------

    def ranked(self, time_limit=None, energy=None, gate=None,
               machine=None, include_blocked=False):
        candidates = []
        for node in self.nodes.values():
            if not node.is_active:
                continue
            if not include_blocked and node.effective_status == "blocked":
                continue
            if gate is not None and (node.get("gate") or "none") != gate:
                continue
            if time_limit is not None and node.effort_minutes > time_limit:
                continue
            if energy is not None:
                load = node.get("cognitive_load") or "medium"
                if energy == "low" and load != "low":
                    continue
                if energy == "medium" and load == "high":
                    continue
            if machine is not None:
                affinity = node.get("machine_affinity")
                if affinity and affinity != machine:
                    continue
            candidates.append(node)

        # Total order, identical on any machine: score, then leverage, then
        # lead time, then the cheapest, then oldest, then id.
        candidates.sort(key=lambda n: (
            -round(n.score, 6), -n.leverage, -(n.get("lead_time_days") or 0),
            n.effort_minutes, n.get("created") or "", _fm.sort_key(n.id),
        ))

        pinned = [n for n in candidates if n.get("pin")]
        if pinned:
            rest = [n for n in candidates if not n.get("pin")]
            pinned.sort(key=lambda n: n.get("pin"))
            ordered = rest[:]
            for node in pinned:
                position = max(0, min(len(ordered), node.get("pin") - 1))
                ordered.insert(position, node)
            candidates = ordered
        return candidates


def find_root(start=None):
    path = os.path.abspath(start or os.path.dirname(os.path.abspath(__file__)))
    while True:
        if os.path.isdir(os.path.join(path, "state")) and \
           os.path.exists(os.path.join(path, "CLAUDE.md")):
            return path
        parent = os.path.dirname(path)
        if parent == path:
            raise SystemExit("not inside a product-os repo")
        path = parent
