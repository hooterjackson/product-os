#!/usr/bin/env python3
"""The dashboard. One page, read-only, and its product is copyable prompts.

    python3 tools/surface.py            write public/index.html
    python3 tools/surface.py --out DIR

Named `surface`, not `site`: `site` is a stdlib module that CPython imports
during interpreter startup, and every tool here does
`sys.path.insert(0, "tools")`. A module called `site.py` on that path shadows
it. The plan said `site.py`; the interpreter disagrees, and it wins.

Built to `Product OS Surfaces v2`. Four sections in this order -- TL;DR,
backlog, closures, chats -- because the daily action is what he opens the page
for and the rest is what it is answering about.

## Nothing here decides anything

The page holds no token and writes nothing. Every action leaves through a chat
(a copied prompt) or through GitHub (a pre-filled issue under his own sign-in).
`Order is the only rank`: DOM order is `state/backlog.md` order, and nothing on
the page can re-sort it, so nothing implies it could.

## The JS budget is two things

Copy, and the age renderer. Disclosure is `<details>`, closed by the element's
own default rather than by a state we set, so with JS off every panel still
opens and every prompt is still selectable.

## The copy payload IS the visible prompt

`<pre data-prompt>` holds the same text `kickoff.py` writes, and the control
reads its own row's node. One source, so what is copied and what is shown
cannot drift, and no fetch is needed to get it.

## A command renders only where it is true

`_context.reach()` returns four kinds and exactly one of them yields a command.
On top of that, a command renders only on a LOCAL build: `public/` is committed
and served to every machine, so `cd ~/Claude/product-os` there is wrong on
`formd-t1` and right nowhere the page can know about. That is the same rule
`R-076` already applies to chat URLs, extended to paths -- and it is enforced,
not promised: `E-PUBLIC-LOCAL-PATH` fails the build if one appears.
"""

import argparse
import html
import json
import os
import sys

import shutil

import _context
import _fm
import _model
import kickoff as kickoff_mod
import new as new_mod

REPO = "hooterjackson/product-os"
ISSUES = "https://github.com/%s/issues/new" % REPO

# --- the token vocabulary, referenced not redefined ------------------------
MICRO = ("font:400 var(--fs-micro)/1 var(--font-mono);letter-spacing:0.14em;"
         "text-transform:uppercase;color:var(--el-ink-3)")
CHROME = ("font:400 var(--fs-chrome)/1.4 var(--font-mono);letter-spacing:0.14em;"
          "text-transform:uppercase;color:var(--el-ink-3)")
META = "font:400 var(--fs-meta)/1.5 var(--font-mono);color:var(--el-ink-3)"
BODY = "font:400 var(--fs-body)/1.45 var(--font-sans);color:var(--el-ink-2)"
BODY_INK = ("font:400 var(--fs-body)/1.5 var(--font-sans);color:var(--el-ink);"
            "text-wrap:pretty")
SECTION = "padding:var(--sp-6) 0;border-top:1px solid var(--el-line)"
PRE = ("margin:0;font:400 var(--fs-meta)/1.6 var(--font-mono);color:var(--el-ink);"
       "background:var(--el-panel);border:1px solid var(--el-line);"
       "padding:var(--sp-4);white-space:pre-wrap;overflow-wrap:anywhere")

# The four kinds, as the chip says them on a LOCAL build. `local` is the only
# one that can yield a command.
CHIP = {_context.LOCAL: "this machine", _context.ELSEWHERE: "elsewhere",
        _context.NO_CLONE: "not cloned", _context.NO_REPO: "no repo"}

# What a PUBLISHED page may say. Two of the four kinds are facts about the
# reader's machine -- `local` and `not cloned` differ only in whether the repo
# happens to be on the box that ran `publish` -- and a committed page is read
# by machines it cannot see. Measured: index.html rendered `this machine` for
# product-os here and `not cloned` on CI, so `publish.py --check` could never
# pass on two machines at once.
#
# The other two ARE durable. `no repo` is a property of the project; `elsewhere`
# is a property of the task's own machine_affinity. Those keep their words.
#
# This is the same rule as the command and the chat url, one level up: a
# published surface may not speak about "here".
PUBLISHED_CHIP = {_context.LOCAL: "needs the repo",
                  _context.NO_CLONE: "needs the repo",
                  _context.ELSEWHERE: "elsewhere",
                  _context.NO_REPO: "no repo"}


def chip(verdict, volatile):
    return (CHIP if volatile else PUBLISHED_CHIP)[verdict["kind"]]


MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def short_date(iso):
    """`2026-08-19` -> `19 Aug`. The design's own answer to a measured
    overflow: at 375px the group summary carries the name, the date and the
    count on one line, and the ISO form pushes it to two. The year is dropped
    because a handoff older than a year is not what this line is for."""
    try:
        parts = [int(p) for p in str(iso).split("-")[:3]]
        return "%d %s" % (parts[2], MONTHS[parts[1] - 1])
    except (ValueError, IndexError):
        return str(iso)


def esc(text):
    return html.escape(str(text if text is not None else ""), quote=True)


def field(label, value, value_style=BODY_INK):
    return ('<div style="display:grid;gap:var(--sp-1);margin:0 0 var(--sp-4)">'
            '<span style="%s">%s</span><span style="%s">%s</span></div>'
            % (MICRO, esc(label), value_style, value))


def copy_control(sub):
    """The one control shape. Inside the <summary>, so a single tap writes the
    clipboard and opens the panel -- the reveal is the receipt."""
    return (
        '<span role="button" tabindex="0" aria-label="Copy the prompt" '
        'data-copy="" style="flex:none;display:flex;flex-direction:column;'
        'align-items:flex-end;gap:var(--sp-1);min-height:44px;min-width:82px;'
        'justify-content:center;border:1px solid var(--el-line-2);'
        'padding:var(--sp-2) var(--sp-3)">'
        '<span style="font:400 var(--fs-chrome)/1 var(--font-mono);'
        'letter-spacing:0.1em;text-transform:uppercase;color:var(--el-amber)">'
        'Copy<span data-copied-slot=""></span></span>'
        '<span style="font:400 var(--fs-micro)/1 var(--font-mono);'
        'letter-spacing:0.08em;text-transform:uppercase;color:var(--el-ink-3);'
        'white-space:nowrap">%s</span></span>' % esc(sub))


def where_to_paste(verdict, volatile, repos):
    """The way in. An honest inert state names what you need, and never
    pretends to know where you are reading from."""
    kind = verdict["kind"]
    if volatile and kind == _context.LOCAL and verdict.get("command"):
        return field("Machine · this laptop",
                     '<code style="font:400 var(--fs-meta)/1.6 '
                     'var(--font-mono);color:var(--el-ink);border:1px solid '
                     'var(--el-line);padding:var(--sp-3);display:inline-block">'
                     '%s &amp;&amp; claude</code>' % esc(verdict["command"]))
    if volatile or kind in (_context.ELSEWHERE, _context.NO_REPO):
        return field("Machine · %s" % chip(verdict, volatile),
                     esc(verdict["reason"]), BODY)
    return field(
        "Machine · needs the repo",
        "This task is worked in %s. Whether the machine you are reading this "
        "on has a clone is not something a published page can know, so no "
        "command is offered — run it where the repo is."
        % (", ".join("<code style=\"font-family:var(--font-mono)\">%s</code>"
                     % esc(r) for r in repos) or "the repo it names"),
        BODY)


# ------------------------------------------------------------------ sections

def tldr(root, model, stamp, volatile):
    """What did I do, and what did a machine do without me."""
    unconfirmed = [n for n in model.nodes.values()
                   if n.status == "done" and n.get("closed_origin") != "his-word"]
    latest = _context.latest_audit(root)
    head = ('<div style="display:flex;align-items:baseline;gap:var(--sp-2);'
            'margin:0 0 var(--sp-4)"><span style="%s">TL;DR</span>' % CHROME)
    if stamp and stamp.get("date"):
        head += ('<span style="font:400 var(--fs-micro)/1 var(--font-mono);'
                 'letter-spacing:0.1em;text-transform:uppercase;'
                 'color:var(--el-ink-3)">audit · <span data-audit-date="%s">%s'
                 '</span></span>' % (esc(stamp["date"]), esc(stamp["date"])))
    head += "</div>"

    body = []
    if latest:
        body.append('<div style="display:grid;gap:var(--sp-1)">'
                    '<span style="%s">What happened</span>'
                    '<span style="%s">%s</span></div>'
                    % (MICRO, BODY_INK, esc(latest)))
    else:
        body.append('<p style="font:400 var(--fs-body-l)/1.5 var(--font-sans);'
                    'color:var(--el-ink);margin:0 0 var(--sp-5);max-width:38ch;'
                    'text-wrap:pretty">No audit has written a summary yet. The '
                    'audit writes this part, so it stays empty until one does.'
                    '</p>')
    if unconfirmed:
        ids = ", ".join(sorted((n.id for n in unconfirmed), key=_fm.sort_key))
        body.append(
            '<div style="display:grid;gap:var(--sp-1);margin-top:var(--sp-4)">'
            '<span style="%s">What a machine did without you</span>'
            '<span style="%s">Closed %d task%s, unconfirmed. '
            '<a href="#closures" style="display:inline-block;'
            'padding:var(--sp-4) var(--sp-2);margin:calc(var(--sp-4) * -1) '
            'calc(var(--sp-2) * -1)">Below</a>.</span></div>'
            % (MICRO, BODY_INK, len(unconfirmed),
               "" if len(unconfirmed) == 1 else "s"))
    body.append(daily_action(root, model, stamp, unconfirmed, volatile))
    return '<section style="%s">%s%s</section>' % (SECTION, head, "".join(body))


def daily_action(root, model, stamp, unconfirmed, volatile):
    """An action sits at the foot of the thing it acts on -- the TL;DR it
    rewrites -- one tap from landing, and NOT as a section, which would put it
    in the reading order competing with the audit's own output."""
    lines = ["You are updating Product OS.", "",
             "Read https://raw.githubusercontent.com/%s/main/public/llms.txt "
             "and follow it." % REPO, "", "What it believes right now:"]
    for node in model.backlog()[:6]:
        lines.append("  %s %s" % (node.id, node.title))
    for node in sorted(unconfirmed, key=lambda n: _fm.sort_key(n.id)):
        lines.append("  %s closed by a machine, unconfirmed" % node.id)
    for slug, project in sorted(model.projects.items()):
        if not (project.get("repos") or []):
            lines.append("  %s has no repository — its status is my word only"
                         % slug)
    since = (stamp or {}).get("date") or "the beginning"
    lines += ["", "Tell me what actually happened since %s. Then hand back:" % since,
              "  1. status changes, each with the SHA or path that proves it",
              "  2. candidates you derived, each with its evidence",
              "  3. a rewritten TL;DR — five things, under 1 KB", "",
              "Anything you cannot prove, say so and leave it open. "
              "Do not close a task I have not confirmed."]
    prompt = "\n".join(lines)

    inner = field("What this does",
                  "Hands a new chat everything this page believes, including "
                  "what it could not prove, and asks what actually happened. "
                  "Everything below this line is as of the last audit until "
                  "you run it.", BODY)
    inner += ('<div style="display:grid;gap:var(--sp-1);margin:0 0 var(--sp-4)">'
              '<span style="%s">The prompt</span><pre data-prompt="" style="%s">'
              '%s</pre></div>' % (MICRO, PRE, esc(prompt)))
    inner += field("Where to paste it",
                   "Any chat window, including this phone. The prompt carries "
                   "no path — it reads the repo over the web, so nothing needs "
                   "to be cloned.", BODY)
    inner += field("What happens next",
                   "It answers with status changes, derived candidates and a "
                   "new TL;DR. From a chat you carry the answer back; from the "
                   "Mac it writes them itself. Either way this page shows them "
                   "the next time it is built.", BODY)
    return (
        '<details style="margin-top:var(--sp-5)"><summary data-copy="" '
        'style="display:flex;align-items:center;justify-content:space-between;'
        'gap:var(--sp-3);min-height:48px;border:1px solid var(--el-amber);'
        'padding:0 var(--sp-4);font:400 var(--fs-chrome)/1 var(--font-mono);'
        'letter-spacing:0.12em;text-transform:uppercase;color:var(--el-amber)">'
        '<span>Tell it what changed<span data-copied-slot=""></span></span>'
        '<span style="color:var(--el-ink-3)">any chat</span></summary>'
        '<div style="padding:var(--sp-4) 0 var(--sp-1)">%s</div></details>'
        % inner)


def task_row(node, model, entries, stamp, repos_spec, root, manual, machine,
             volatile):
    """Seven parts, in the reading order the prompt itself uses."""
    verdict = _context.reach(node, model, repos_spec, machine)
    prompt = kickoff_mod.render(node, model, entries, stamp, repos_spec, root,
                                manual, volatile)
    ruled = _context.ruled_out_for(node, entries)

    body = field("What this does",
                 "Hands a chat this task, what has already been ruled out for "
                 "it, and how stale that knowledge is.", BODY)

    if ruled:
        rows = "".join(
            '<div style="display:grid;gap:var(--sp-1);padding:var(--sp-3) 0;'
            'border-top:1px solid var(--el-line)">'
            '<span style="font:400 var(--fs-meta)/1.4 var(--font-mono);'
            'color:var(--el-ink)">%s</span>'
            '<span style="font:400 var(--fs-label)/1.5 var(--font-sans);'
            'color:var(--el-ink-3)">%s</span></div>'
            % (esc(title), esc(_context_clip(first)))
            for _n, title, first, _o in ruled)
        body += ('<div style="display:grid;gap:var(--sp-1);margin:0 0 '
                 'var(--sp-4)"><span style="%s">Already ruled out · %d</span>'
                 '<div style="display:grid;gap:0">%s</div></div>'
                 % (MICRO, len(ruled), rows))
    else:
        body += field("Already ruled out",
                      "Nothing matches this task's keywords. That is not the "
                      "same as nothing having been ruled out — this section is "
                      "empty, not clear.", BODY)

    body += ('<div style="display:grid;gap:var(--sp-1);margin:0 0 var(--sp-4)">'
             '<span style="%s">The prompt</span><span style="%s">%s</span>'
             '<pre data-prompt="" style="%s">%s</pre></div>'
             % (MICRO, META,
                esc(_context.freshness(root, node, stamp, repos_spec, False)),
                PRE, esc(prompt)))
    body += where_to_paste(verdict, volatile, verdict["repos"])
    body += field("What happens next",
                  "The chat works in the repo the task names and writes a "
                  "handoff when it stops. Nothing here changes until the next "
                  "audit reads that.", BODY)
    body += field("Tied to", esc("%s · %s" % (node.project, node.id)), META)

    return (
        '<details style="border-top:1px solid var(--el-line)"><summary '
        'style="display:flex;gap:var(--sp-3);align-items:flex-start;'
        'padding:var(--sp-4) 0;min-height:44px">'
        '<span style="font:400 var(--fs-chrome)/1.5 var(--font-mono);'
        'letter-spacing:0.06em;color:var(--el-ink-3);flex:none;'
        'padding-top:var(--sp-1)">%s</span>'
        '<span style="flex:1;font:400 var(--fs-body-l)/1.45 var(--font-sans);'
        'color:var(--el-ink);text-wrap:pretty">%s</span>%s</summary>'
        '<div style="padding:var(--sp-1) 0 var(--sp-6)">%s</div></details>'
        % (esc(node.id), esc(node.title), copy_control(chip(verdict, volatile)),
           body))


def _context_clip(text, limit=190):
    text = " ".join((text or "").split())
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0].rstrip(" ,;:—-") + " …"


def backlog(root, model, entries, stamp, repos_spec, manual, machine, volatile):
    """Grouped by project, because the project is the unit: closed, a project is
    its name and how long since it moved; open, it is what it is, where it is,
    and its tasks. A project with no open tasks still has somewhere to speak."""
    ordered = model.backlog()
    out = ['<section style="%s"><div style="display:flex;align-items:baseline;'
           'gap:var(--sp-2);margin:0 0 var(--sp-1)"><span style="%s">Backlog'
           '</span></div>' % (SECTION, CHROME)]
    if not ordered:
        out.append('<p style="font:400 var(--fs-body-l)/1.5 var(--font-sans);'
                   'color:var(--el-ink);margin:var(--sp-5) 0 0;max-width:38ch;'
                   'text-wrap:pretty">Nothing in the backlog. You author every '
                   'task here — the system never invents one — so this stays '
                   'empty until you add something.</p>')
    else:
        # ONE card per project, not one per contiguous run. His order is a
        # global list and it interleaves projects freely, so grouping on
        # "the project changed" rendered gimbal-bench three times and
        # product-os twice -- six projects as nine cards, which is not a unit.
        #
        # Nothing is lost: a project takes its position from its
        # highest-ranked task, so the project holding his #1 is still first,
        # and inside a card the tasks keep his order.
        groups, seen = [], {}
        for node in ordered:
            if node.project not in seen:
                seen[node.project] = len(groups)
                groups.append((node.project, []))
            groups[seen[node.project]][1].append(node)
        # EVERY project renders, including the ones with nothing open. A
        # project used to be a label on a task list, so a project with no open
        # tasks had nowhere to say anything and simply vanished -- and two of
        # the six are in that state while still holding closures a machine
        # made. A card that disappears when idle cannot tell you it is idle.
        for slug in sorted(model.projects):
            if slug not in seen:
                groups.append((slug, []))
        out.append('<div style="display:grid;gap:0;margin-top:var(--sp-5)">')
        for slug, nodes in groups:
            out.append(project_group(slug, nodes, model, entries, stamp,
                                     repos_spec, root, manual, machine,
                                     volatile))
        out.append("</div>")
    out.append(add_controls(model))
    out.append("</section>")
    return "".join(out)


def project_group(slug, nodes, model, entries, stamp, repos_spec, root, manual,
                  machine, volatile):
    project = model.projects.get(slug)
    name = slug
    open_n = len(nodes)
    handoff = _context.last_handoff(nodes)
    inner = []
    if project:
        if (project.get("description") or "").strip():
            inner.append(field("What it is", esc(project.get("description"))))
        if (project.get("phase") or "").strip():
            inner.append(field("Where it is", esc(project.get("phase"))))
        if not (project.get("repos") or []):
            inner.append(field(
                "No repository",
                "Nothing here can be verified from commits, so its status "
                "changes only when you say so. Not stale — unauditable.", BODY))
    inner.append(field(
        "Last session",
        esc(handoff["said"]) if handoff else
        "A handoff has not been written yet. Absent is not the same as "
        "nothing happened.",
        BODY_INK if handoff else BODY))
    if nodes:
        rows = "".join(task_row(n, model, entries, stamp, repos_spec, root,
                                manual, machine, volatile) for n in nodes)
        inner.append('<div style="display:grid;gap:0;margin-top:var(--sp-2)">'
                     '<span style="%s;padding-bottom:var(--sp-2)">%d open</span>'
                     '%s</div>' % (MICRO, open_n, rows))
    else:
        closed = sorted([n.id for n in model.nodes.values()
                         if n.project == slug and n.status == "done"
                         and n.get("closed_origin") != "his-word"],
                        key=_fm.sort_key)
        parked = sum(1 for n in model.nodes.values()
                     if n.project == slug and n.status == "parked")
        said = "Nothing open."
        if closed:
            said += (" A machine closed %s here without you — "
                     "<a href=\"#closures\">below</a>." % ", ".join(closed))
        if parked:
            said += " %d set aside." % parked
        if not closed and not parked:
            said += " Not idle by accident — there is simply nothing here."
        inner.append(field("Nothing open", said, BODY_INK))
    return (
        '<details style="border-top:1px solid var(--el-line)"><summary '
        'style="display:flex;gap:var(--sp-3);align-items:baseline;'
        'padding:var(--sp-4) 0;min-height:44px">'
        '<span style="flex:1;font:400 var(--fs-body-l)/1.4 var(--font-mono);'
        'letter-spacing:0.02em;color:var(--el-ink)">%s</span>'
        '<span style="font:400 var(--fs-meta)/1.4 var(--font-mono);'
        'color:var(--el-ink-3);text-align:right">%s%s</span></summary>'
        '<div style="display:grid;gap:var(--sp-4);padding:0 0 var(--sp-6)">%s'
        '</div></details>'
        % (esc(name),
           ("last worked %s · " % esc(short_date(handoff["date"])))
           if handoff else "",
           ("%d open" % open_n) if open_n else "nothing open",
           "".join(inner)))


def add_controls(model):
    """Two controls, two silhouettes, because they are the boundary of the
    authority model. Adding a task is a DECISION -- a full-width square control
    with an amber border, this page's shape for a deliberate act. Capture is
    not: it asks nothing and lands in the inbox, outside the backlog, becoming a
    task only if he adopts one. Provenance changes shape, not colour."""
    return (
        '<div style="margin-top:var(--sp-6);display:grid;gap:var(--sp-3)">'
        '<a href="%s?labels=task&amp;template=task.yml" style="display:flex;'
        'align-items:center;justify-content:space-between;min-height:48px;'
        'border:1px solid var(--el-amber);padding:0 var(--sp-4);font:400 '
        'var(--fs-chrome)/1 var(--font-mono);letter-spacing:0.12em;'
        'text-transform:uppercase;color:var(--el-amber)">'
        '<span>Add a task</span><span style="color:var(--el-ink-3)">backlog'
        '</span></a>'
        '<div><a href="%s?labels=inbox&amp;template=capture.yml" style="display:inline-flex;'
        'align-items:center;gap:var(--sp-2);min-height:44px;border:1px solid '
        'var(--el-line-2);border-radius:var(--r-pill);padding:0 var(--sp-4);'
        'font:400 var(--fs-chrome)/1 var(--font-mono);letter-spacing:0.1em;'
        'text-transform:uppercase;color:var(--el-ink-2)">'
        '<span>Don\'t let me forget this</span>'
        '<span style="color:var(--el-ink-3)">inbox</span></a></div>'
        '<span style="font:400 var(--fs-label)/1.5 var(--font-sans);'
        'color:var(--el-ink-3);max-width:44ch">It asks nothing, because every '
        'question is a reason not to bother next time.</span></div>'
        % (ISSUES, ISSUES))


def closures(model, machine):
    """A closure row is a disclosure. Closed, the IDs. Open, the title, the date
    and that row's own way out with its real ID in it -- never a template."""
    rows = sorted([n for n in model.nodes.values()
                   if n.status == "done"
                   and n.get("closed_origin") != "his-word"],
                  key=lambda n: _fm.sort_key(n.id))
    if not rows:
        return ""
    out = ['<section id="closures" style="%s"><div style="display:flex;'
           'align-items:baseline;gap:var(--sp-2);margin:0 0 var(--sp-4)">'
           '<span style="%s">Closed without you · %d</span></div>'
           % (SECTION, CHROME, len(rows))]
    out.append('<p style="%s;margin:0 0 var(--sp-4);max-width:46ch">A machine '
               'decided these were finished. You have confirmed none of them.'
               '</p>' % BODY)
    for node in rows:
        found = node.get("evidence_found") or []
        evidence = ", ".join(str(e.get("sha") or e.get("path"))
                             for e in found[:3]) or "none recorded"
        out.append(
            '<details style="border-top:1px solid var(--el-line)"><summary '
            'style="display:flex;gap:var(--sp-3);align-items:baseline;'
            'padding:var(--sp-4) 0;min-height:44px">'
            '<span style="font:400 var(--fs-chrome)/1.5 var(--font-mono);'
            'letter-spacing:0.06em;color:var(--el-ink-3);flex:none">%s</span>'
            '<span style="flex:1;font:400 var(--fs-body)/1.45 '
            'var(--font-sans);color:var(--el-ink)">%s</span></summary>'
            '<div style="padding:var(--sp-1) 0 var(--sp-5)">%s%s</div>'
            '</details>'
            % (esc(node.id), esc(node.title),
               field("Closed", esc("%s · evidence %s"
                                   % (node.get("completed") or "?", evidence)),
                     META),
               field("Your way out",
                     'Confirm it was right, or reopen it. From a terminal on '
                     '<code style="font-family:var(--font-mono)">%s</code>: '
                     '<code style="font-family:var(--font-mono);'
                     'font-size:var(--fs-meta)">tools/backlog.py --unconfirmed'
                     '</code>' % esc(machine), BODY)))
    out.append("</section>")
    return "".join(out)


def chats(root, model, manual, machine):
    """Which task, which machine, resume-or-restart with its reason, and the way
    back. Empty on day one and it must SAY so -- every indexed thread binds to a
    task the cutover archives, so `none indexed` is the true answer, not a bug."""
    out = ['<section style="%s"><div style="display:flex;align-items:baseline;'
           'gap:var(--sp-2);margin:0 0 var(--sp-4)"><span style="%s">Chats'
           '</span></div>' % (SECTION, CHROME)]
    any_row = False
    for node in model.backlog():
        rows = kickoff_mod.redact(
            kickoff_mod.threads_for(root, node.id, manual), volatile=False)
        for row in rows:
            any_row = True
            way = row.get("reason") or ""
            out.append(
                '<div style="display:grid;gap:var(--sp-1);padding:var(--sp-3) '
                '0;border-top:1px solid var(--el-line)">'
                '<span style="%s">%s · %s · %s</span>'
                '<span style="%s">%s</span></div>'
                % (META, esc(node.id), esc(row.get("tool") or "chat"),
                   esc(row.get("machine") or "—"), BODY, esc(way)))
    if not any_row:
        out.append('<p style="%s;margin:0;max-width:46ch">None indexed. '
                   'Starting fresh is correct — nothing here has been bound to '
                   'a chat yet, which is a cold start and not a fault.</p>'
                   % BODY)
    out.append("</section>")
    return "".join(out)


# -------------------------------------------------------------------- render

SCRIPT = """
// The whole JS budget: copy, and the age renderer. Disclosure is <details>.
document.addEventListener('click', function (ev) {
  var el = ev.target.closest('[data-copy]');
  if (!el) return;
  var row = el.closest('details');
  var pre = row && row.querySelector('[data-prompt]');
  if (!pre) return;
  navigator.clipboard.writeText(pre.textContent).then(function () {
    var slot = el.querySelector('[data-copied-slot]');
    if (!slot) return;
    slot.textContent = ' \\u00b7 copied';
    setTimeout(function () { slot.textContent = ''; }, 2000);
  });
});
document.addEventListener('keydown', function (ev) {
  if (ev.key !== 'Enter' && ev.key !== ' ') return;
  var el = ev.target.closest('[data-copy]');
  if (el) { ev.preventDefault(); el.click(); }
});
// The bytes carry the date; the browser renders the age. publish --check
// therefore passes on two consecutive days -- R-067.
[].forEach.call(document.querySelectorAll('[data-audit-date]'), function (n) {
  var then = new Date(n.getAttribute('data-audit-date') + 'T00:00:00Z');
  var days = Math.floor((Date.now() - then.getTime()) / 86400000);
  if (isNaN(days) || days < 0) return;
  n.textContent = days === 0 ? 'today'
    : days === 1 ? 'yesterday' : days + ' days ago';
});
"""


def render(root, model, volatile=False):
    stamp = _context.read_stamp(root)
    entries = _context.parse_register(root)
    with open(os.path.join(root, "state", "repos.json"), encoding="utf-8") as fh:
        repos_spec = {k: v for k, v in json.load(fh).items()
                      if not k.startswith("_")}
    manual = kickoff_mod.load_manual(root)
    if not volatile:
        # R-076, fourth route. This page embeds whole kickoff prompts, and a
        # prompt built from the unredacted map carries the chat url straight
        # into a committed index.html. publish.py redacts before calling
        # kickoff; nothing was redacting before calling this.
        manual = kickoff_mod.redact_manual(manual)
    machine = new_mod.machine_id(root)

    parts = [
        '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        "<title>Product OS</title>",
        '<link rel="stylesheet" href="assets/tokens.css">',
        '<link rel="stylesheet" href="assets/product-os-theme.css">',
        "</head><body>",
        '<div style="padding:var(--sp-6) var(--sp-5) var(--sp-16);'
        'max-width:760px;margin:0 auto">',
        '<div style="display:flex;align-items:center;gap:var(--sp-3);'
        'margin:0 0 var(--sp-6)"><span style="font:400 var(--fs-micro)/1 '
        'var(--font-mono);letter-spacing:0.14em;text-transform:uppercase;'
        'color:var(--el-ink-2);border:1px solid var(--el-line);'
        'border-radius:var(--r-pill);padding:var(--sp-2) var(--sp-3)">'
        'Product OS</span></div>',
        tldr(root, model, stamp, volatile),
        backlog(root, model, entries, stamp, repos_spec, manual, machine,
                volatile),
        closures(model, machine),
        chats(root, model, manual, machine),
        '<p style="%s;margin:var(--sp-8) 0 0">This page reads. It never writes '
        '— every action leaves through a chat or a GitHub issue under your own '
        'sign-in, and it holds no token.</p>' % META,
        "</div><script>%s</script></body></html>" % SCRIPT,
    ]
    return "".join(parts) + "\n"


# The stylesheets are SOURCE in tools/assets/ and are COPIED out by this
# generator. They must not be hand-placed under public/: `publish.py --check`
# walks the target and reports anything the generator did not produce as
# `orphan:`, so a hand-placed file turns the gate red and the next publish
# deletes it. The same rule applies to a Pages CNAME -- if one is ever needed,
# it is emitted here, never dropped in by hand.
ASSETS = ("tokens.css", "product-os-theme.css")


def generate(root, model, target, volatile=False):
    path = os.path.join(target, "index.html")
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(render(root, model, volatile))
    out = os.path.join(target, "assets")
    os.makedirs(out, exist_ok=True)
    for name in ASSETS:
        shutil.copyfile(os.path.join(root, "tools", "assets", name),
                        os.path.join(out, name))
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out")
    args = parser.parse_args(argv)
    root = _model.find_root()
    model = _model.Model.load(root)
    target = args.out or os.path.join(root, "public")
    print("wrote %s" % os.path.relpath(generate(root, model, target), root))
    return 0


if __name__ == "__main__":
    sys.exit(main())
