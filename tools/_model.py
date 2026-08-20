#!/usr/bin/env python3
"""Load the authored state. Compute almost nothing.

This module used to derive an order: `impact x confidence / effort_bucket`,
lifted by transitive reachability through a dependency graph, recomputed on
every run so that no ordered list existed anywhere. That was the repository's
founding claim and it is reversed -- `DEC-202`, `R-068`, `R-069`.

**Measured before removing it.** Across the 18 offerable nodes, 9 of the 17
adjacent pairs sat within 10% of each other -- the exact band `CLAUDE.md` says
to *escalate* on. Eighteen items produced ten distinct scores, the largest tie
was four items, and `pin` (the human override, described in the plan as moving
"from exception to ordinary use") had never been set on a single item. The
graph was 12 edges over 41 nodes, 10 of them inside one repo, from a phase plan
Marcelo wrote by hand before this tool existed.

So the order is authored: `state/backlog.md`, one id per line, top is next.
Nothing here computes it, and no agent writes it.
"""

import glob
import os

import _fm

BACKLOG = "state/backlog.md"

# `dropped` and `parked` are scope decisions with taste in them; `done` is
# finished. None of the three can be picked up, so none belongs in the backlog.
ACTIVE_EXCLUDED = {"done", "dropped", "parked"}


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

    def get(self, key, default=None):
        return self.fm.get(key, default)

    @property
    def is_active(self):
        return self.status not in ACTIVE_EXCLUDED

    def __repr__(self):
        return "<%s %s>" % (self.kind, self.id)


class Model(object):
    def __init__(self, root):
        self.root = root
        self.items = {}
        self.decisions = {}
        self.projects = {}
        self.errors = []

    @classmethod
    def load(cls, root):
        model = cls(root)
        for path in sorted(glob.glob(os.path.join(
                root, "state", "projects", "*", "project.md"))):
            model._add(model.projects, "project", path, key="slug")
        for path in sorted(glob.glob(os.path.join(
                root, "state", "projects", "*", "items", "*.md"))):
            model._add(model.items, "item", path)
        for pattern in (("state", "decisions", "*.md"),
                        ("state", "projects", "*", "decisions", "*.md")):
            for path in sorted(glob.glob(os.path.join(root, *pattern))):
                model._add(model.decisions, "decision", path)
        _fm.set_prefixes(model.prefixes())
        return model

    def prefixes(self):
        """prefix -> project slug, derived rather than hardcoded.

        Three sources, and the third is the one that matters:

          1. `prefix` on each `project.md`. The declared set.
          2. `_fm.RESERVED_PREFIXES` -- `DEC` only; a ruling is portfolio-wide.
          3. **Prefixes actually in use on disk.** `Q-001`..`Q-005` are the
             live case: they were the `question` kind, which was collapsed,
             and no project declares `Q`. Their ids are stable on purpose --
             renaming them would break every transcript citation and re-create
             `R-057`, where an id reused across seed generations bound a real
             conversation to the wrong work. So a prefix that exists is
             legitimate whether or not a project claims it, and the guard
             against typos is `E-ID-PREFIX-UNKNOWN` in validate.py, which
             checks against this same set.
        """
        out = dict(_fm.RESERVED_PREFIXES)
        for slug, project in self.projects.items():
            prefix = project.get("prefix")
            if prefix:
                out[prefix] = slug
        for node in list(self.items.values()) + list(self.decisions.values()):
            parsed = _fm.parse_id(node.id)
            if parsed and parsed[0] not in out:
                # None, NOT the project this one happens to sit in. `Q-001`..
                # `Q-004` are gimbal-bench and `Q-005` is engineering-site, so
                # binding the prefix to whichever loaded first would have made
                # `E-ID-PROJECT-MISMATCH` fire on four real tasks. An
                # undeclared prefix implies no project, which is the truth.
                out[parsed[0]] = None
        return out

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

    @property
    def nodes(self):
        """Every task. Questions used to be a second kind here; with the graph
        and the score inputs gone, a question was a task whose title ends in a
        question mark, living outside any project -- which the "every task
        belongs to a project" rule forbids. They are ordinary tasks now."""
        return dict(self.items)

    # -- the authored order --------------------------------------------------

    def backlog_ids(self):
        """`state/backlog.md`, in file order. Ids only; resolution is separate
        so `validate.py` can report a dangling id as a dangling id."""
        path = os.path.join(self.root, BACKLOG)
        out = []
        if not os.path.exists(path):
            return out
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.split("#", 1)[0].strip()
                if line:
                    out.append(line)
        return out

    def backlog(self):
        """The tasks he has ordered, top first. Unknown ids are skipped here
        and reported by `validate.py`'s `E-BACKLOG-DRIFT` -- rendering must not
        be the thing that tells you the file is wrong."""
        nodes = self.nodes
        return [nodes[i] for i in self.backlog_ids() if i in nodes]

    def unlisted(self):
        """Active tasks the backlog does not mention. Not an error on its own:
        a task created since the last reorder is unlisted and fine. It is
        `validate.py`'s job to decide, and the dashboard's job to show them
        rather than let them be invisible."""
        listed = set(self.backlog_ids())
        return [n for n in sorted(self.nodes.values(),
                                  key=lambda n: _fm.sort_key(n.id))
                if n.is_active and n.id not in listed]


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
