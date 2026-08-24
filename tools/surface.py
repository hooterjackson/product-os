#!/usr/bin/env python3
"""The dashboard. One page, read-only, and its product is copyable prompts.

    python3 tools/surface.py            write public/index.html
    python3 tools/surface.py --out DIR

Named `surface`, not `site`, and the mechanism is worth stating correctly
because an earlier version of this docstring got it wrong.

`site` is a stdlib module CPython imports during interpreter startup. Measured,
three ways:

    sys.path.insert(0, "tools") at runtime   NO shadow -- by then `site` is
                                             already in sys.modules
    running a script from inside tools/      NO shadow, same reason
    PYTHONPATH=tools                         the real trigger

and the trigger has two outcomes, of which the quiet one is worse:

    the shadowing module RAISES         the interpreter dies at startup
    it imports cleanly                  it BOOTS, stdlib `site` is silently
                                        replaced, and site-packages is never
                                        set up

So the danger is not "every tool here shadows it" -- that claim was false --
and it is not only "the interpreter refuses to boot". It is that under
PYTHONPATH the failure can be completely silent, which is the shape this
repository exists to refuse. The plan said `site.py`; the interpreter wins,
and the design calls this file a surface anyway.

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
import urllib.parse

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
# `elsewhere` looked durable and is not: it is a COMPARISON with the reader's
# machine, not a fact about the task. One task carries
# `machine_affinity: work-laptop`, so the row read `needs the repo` on this
# laptop and `elsewhere` on a runner -- caught by the byte-identical test,
# which was itself blinding only the clone state and so missed it locally.
#
# So a published row states the FACT and makes no comparison at all:
#   no repo        the project has none
#   on <machine>   the task names one, verbatim
#   needs the repo neither -- run it where the repo is
def published_chip(node, verdict):
    if verdict["kind"] == _context.NO_REPO:
        return "no repo"
    affinity = node.get("machine_affinity")
    return ("on %s" % affinity) if affinity else "needs the repo"


def chip(node, verdict, volatile):
    return (CHIP[verdict["kind"]] if volatile
            else published_chip(node, verdict))


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


def copyable(command, label=None):
    """A command with a Copy button. He should not have to select a command out
    of a paragraph, and the way-back was a PARAGRAPH -- so command_block()'s
    `cd` line never reached it and he pasted the second line alone, twice,
    landing in his home directory both times."""
    return (
        '<div style="display:grid;gap:var(--sp-2)">'
        '<div style="display:flex;align-items:center;justify-content:'
        'space-between;gap:var(--sp-3)">'
        '<span style="%s">%s</span>'
        '<span role="button" tabindex="0" data-copy-block="" '
        'aria-label="Copy the command" style="flex:none;border:1px solid '
        'var(--el-line-2);padding:var(--sp-2) var(--sp-3);font:400 '
        'var(--fs-chrome)/1 var(--font-mono);letter-spacing:0.1em;'
        'text-transform:uppercase;color:var(--el-amber)">Copy'
        '<span data-copied-slot=""></span></span></div>'
        '<code style="font:400 var(--fs-meta)/1.6 var(--font-mono);'
        'color:var(--el-ink);background:var(--el-panel);border:1px solid '
        'var(--el-line);padding:var(--sp-3);display:block;white-space:pre-wrap;'
        'overflow-wrap:anywhere">%s</code></div>'
        % (MICRO, esc(label or "Command"), esc(command)))


def command_block(command, volatile, root=None):
    """Every command this page emits, with its working directory attached.

    Audited 2026-08-23: 34 of the 35 commands on the page said WHAT to run and
    never WHERE. Marcelo ran one from his home directory, on the right machine,
    and python answered `can't open file <home>/tools/index.py` -- the
    instruction was repo-relative and nothing on the page said so. (The literal
    path is not quoted here: the disclosure screen flagged it, correctly, the
    first time this docstring was written.)

    One emitter, always two lines. On a local build the first is the real path;
    on the published page it is `<your product-os clone>`, because a page
    served to every machine cannot name one -- the same rule the chip and the
    way-back already obey.
    """
    where = "<your product-os clone>"
    if volatile and root:
        try:
            with open(os.path.join(root, "state", "repos.json"),
                      encoding="utf-8") as fh:
                where = ((json.load(fh).get("product-os") or {}).get("local")
                         or where)
        except (OSError, ValueError):
            pass
    return ('<code style="font:400 var(--fs-meta)/1.6 var(--font-mono);'
            'color:var(--el-ink);display:block;white-space:pre-wrap;'
            'overflow-wrap:anywhere">cd %s\n%s</code>'
            % (esc(where), esc(command)))


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


def where_to_paste(node, verdict, volatile, repos):
    """The way in. An honest inert state names what you need, and never
    pretends to know where you are reading from."""
    kind = verdict["kind"]
    if volatile and kind == _context.LOCAL and verdict.get("command"):
        return field("Machine · this laptop",
                     '<code style="font:400 var(--fs-meta)/1.6 '
                     'var(--font-mono);color:var(--el-ink);border:1px solid '
                     'var(--el-line);padding:var(--sp-3);display:inline-block">'
                     '%s &amp;&amp; claude</code>' % esc(verdict["command"]))
    if volatile:
        return field("Machine · %s" % CHIP[kind], esc(verdict["reason"]), BODY)
    if kind == _context.NO_REPO:
        return field("Machine · no repo", esc(verdict["reason"]), BODY)
    affinity = node.get("machine_affinity")
    if affinity:
        return field(
            "Machine · on %s" % esc(affinity),
            "This task is bound to <code style=\"font-family:var(--font-mono)\">"
            "%s</code>. Whether that is the machine you are reading this on is "
            "not something a published page can know, so no command is offered."
            % esc(affinity), BODY)
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
    # PROJECT-MAJOR, and every count stated.
    #
    # This was a flat list of ids capped at `backlog()[:6]` — 6 of 27 open
    # items, with the other 21 unmentioned. A chat reading it believed it had
    # the whole picture and reconciled against a quarter of one. That is the
    # "no silent caps" rule broken inside the artifact the entire tool exists
    # to produce.
    #
    # The Backlog section directly above it is already project-major and reads
    # fine, so the prompt uses the same shape: phase, last worked, open count,
    # the top few, and the remainder said out loud.
    ordered = model.backlog()
    by_project = {}
    for node in ordered:
        by_project.setdefault(node.project, []).append(node)

    lines = ["You are updating Product OS.", "",
             "Read https://raw.githubusercontent.com/%s/main/public/llms.txt "
             "and follow it." % REPO, "",
             "WHAT IT BELIEVES RIGHT NOW — %d projects, %d open tasks. "
             "Everything below is as of the last audit."
             % (len(model.projects), len(ordered)), ""]

    for slug in sorted(model.projects):
        project = model.projects[slug]
        nodes = by_project.get(slug, [])
        handoff = _context.last_handoff(nodes) if nodes else None
        head = "%s — %s" % (slug, (project.get("phase") or "").strip()
                            or "no phase recorded")
        lines.append(head.rstrip(". ") + ".")
        notes = []
        if handoff:
            notes.append("Last worked %s" % short_date(handoff["date"]))
        if not (project.get("repos") or []):
            notes.append("no repository, so its status is my word only")
        if notes:
            # Not .capitalize() -- it lowercases the rest, which turned
            # "Last worked 19 Aug" into "19 aug".
            joined = "; ".join(notes)
            lines.append("  %s%s." % (joined[:1].upper(), joined[1:]))
        if not nodes:
            lines.append("  Nothing open.")
        else:
            top = nodes[:3]
            lines.append("  %d open%s:" % (len(nodes),
                                           ", top %d" % len(top)
                                           if len(nodes) > len(top) else ""))
            for node in top:
                lines.append("    %s  %s" % (node.id, node.title))
            if len(nodes) > len(top):
                # The bound, stated. A count that is not said is a cap.
                lines.append("    (%d more in this project not listed here — "
                             "ask if you need them)" % (len(nodes) - len(top)))
        lines.append("")

    if unconfirmed:
        lines.append("CLOSED BY A MACHINE, NEVER CONFIRMED BY ME — %d:"
                     % len(unconfirmed))
        for node in sorted(unconfirmed, key=lambda n: _fm.sort_key(n.id)):
            lines.append("  %s  %s" % (node.id, node.title))
        lines.append("")

    since = (stamp or {}).get("date") or "the beginning"
    lines += ["Tell me what actually happened since %s. Then hand back:" % since,
              "  1. status changes, each with the SHA or path that proves it",
              "  2. candidates you derived, each with its evidence",
              "  3. for each project I mentioned: one plain sentence on where "
              "it now stands,",
              "     in my words where I gave them, and a new `phase` line if "
              "it changed",
              "",
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
    body += where_to_paste(node, verdict, volatile, verdict["repos"])
    body += field("What happens next",
                  "The chat works in the repo the task names and writes a "
                  "handoff when it stops. Nothing here changes until the next "
                  "audit reads that.", BODY)
    body += close_it(node)
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
        % (esc(node.id), esc(node.title), copy_control(chip(node, verdict, volatile)),
           body))


def close_it(node):
    """Two exits, on every open task. There was none.

    The closures section handles what a MACHINE closed and he has not
    confirmed. Nothing handled the ordinary case: he did the work, or he
    decided not to. A backlog you can only add to is a list that grows.

    `done` and `won't do` are different acts and the system already treats them
    differently — `done` needs evidence you can click and that guard holds for
    him too, while dropping needs only a reason. So they are two links, not one
    with a toggle, and the form says which needs what.
    """
    def link(outcome, label, sub, accent):
        return (
            '<a href="%s" style="display:flex;align-items:center;'
            'justify-content:space-between;min-height:48px;border:1px solid %s;'
            'padding:0 var(--sp-4);font:400 var(--fs-chrome)/1 '
            'var(--font-mono);letter-spacing:0.12em;text-transform:uppercase;'
            'color:%s"><span>%s</span>'
            '<span style="color:var(--el-ink-3)">%s</span></a>'
            % (esc(issue_url("close.yml", "close",
                             "%s — %s" % (node.id, sub), task=node.id,
                             outcome=outcome)),
               accent, accent, label, sub))

    return field(
        "Close it",
        '<span style="%s;display:block;margin-bottom:var(--sp-3)">Done needs '
        'something you can click — a SHA, a path, a dated note. Dropping needs '
        'only a reason.</span>'
        '<span style="display:grid;gap:var(--sp-3)">%s%s</span>%s'
        % (BODY,
           link("Done - it shipped", "It is done", "done",
                "var(--el-amber)"),
           link("Won't do - dropping it", "Won't do", "drop",
                "var(--el-line-2)"),
           command_block('python3 tools/apply.py --evidence %s=<SHA> '
                         '--status %s=done \\\n    --said "your sentence"'
                         % (node.id, node.id), False)), BODY)


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


def issue_url(template, label, title, **fields):
    """A pre-filled GitHub issue. The page holds no token, so this is how a
    decision leaves it -- under his own sign-in, on any device."""
    query = {"template": template, "labels": label, "title": title}
    query.update({k: v for k, v in fields.items() if v})
    return "%s?%s" % (ISSUES, urllib.parse.urlencode(query))


def closure_row(node):
    """One closure, one judgement, and both ways out reachable from a phone.

    The row used to print `backlog.py --unconfirmed`. That LISTS the five and
    confirms nothing -- the discovery command offered as though it were the
    action, so the way out was a two-step presented as a one-step and the step
    it showed did nothing. The real command is what `backlog.py` itself prints
    at the foot of that listing, and the row knows its own id, so it is
    rendered here already parameterised.

    `--said` is not ceremony. `apply.py` routes on it: with his sentence a
    decided field APPLIES, without one it is only proposed. It is what makes
    this his decision rather than a rubber stamp on a machine's guess, and the
    audit keeps the sentence. So the form's one required field is that
    sentence, and the terminal form shows it too.
    """
    found = node.get("evidence_found") or []
    evidence = ", ".join(str(e.get("sha") or e.get("path")) for e in found[:3])
    claim = "%s — %s. Closed %s. Evidence: %s" % (
        node.id, node.title, node.get("completed") or "date unrecorded",
        evidence or "NONE recorded")

    def link(verdict, label, sub):
        return (
            '<a href="%s" style="display:flex;align-items:center;'
            'justify-content:space-between;min-height:48px;border:1px solid %s;'
            'padding:0 var(--sp-4);font:400 var(--fs-chrome)/1 '
            'var(--font-mono);letter-spacing:0.12em;text-transform:uppercase;'
            'color:%s"><span>%s</span>'
            '<span style="color:var(--el-ink-3)">%s</span></a>'
            % (esc(issue_url("confirm.yml", "confirm",
                             "%s — %s" % (node.id, sub), task=node.id,
                             verdict=verdict, evidence=claim)),
               "var(--el-amber)" if sub == "confirm" else "var(--el-line-2)",
               "var(--el-amber)" if sub == "confirm" else "var(--el-ink-2)",
               label, sub))

    ways = ('<div style="display:grid;gap:var(--sp-3);margin:0 0 var(--sp-4)">'
            '<span style="%s">Your way out — either one, from anywhere</span>'
            '%s%s</div>'
            % (MICRO,
               link("Confirm - it was finished", "It was right", "confirm"),
               link("Reopen - it was not", "It was not — reopen it", "reopen")))

    terminal = field(
        "Or from a terminal",
        command_block('python3 tools/apply.py --decided %s=status:done \\\n'
                      '    --said "your sentence here"' % node.id, False)
        + '<span style="%s;display:block;margin-top:var(--sp-2)">'
          'Same command with <code style="font-family:var(--font-mono)">'
          'status:next</code> reopens it. The sentence is required — without '
          'it the change is only proposed.</span>' % META, META)

    return (
        '<details style="border-top:1px solid var(--el-line)"><summary '
        'style="display:flex;gap:var(--sp-3);align-items:baseline;'
        'padding:var(--sp-4) 0;min-height:44px">'
        '<span style="font:400 var(--fs-chrome)/1.5 var(--font-mono);'
        'letter-spacing:0.06em;color:var(--el-ink-3);flex:none">%s</span>'
        '<span style="flex:1;font:400 var(--fs-body)/1.45 var(--font-sans);'
        'color:var(--el-ink)">%s</span></summary>'
        '<div style="padding:var(--sp-1) 0 var(--sp-5)">%s%s%s</div></details>'
        % (esc(node.id), esc(node.title),
           field("What it claims",
                 esc("Closed %s · evidence %s"
                     % (node.get("completed") or "?", evidence or "none")),
                 META),
           ways, terminal))


def closures(model):
    """A closure row is a disclosure. Closed, the ids. Open, what it claims and
    that row's own way out with its real id in it -- never a template."""
    rows = sorted([n for n in model.nodes.values()
                   if n.status == "done"
                   and n.get("closed_origin") != "his-word"],
                  key=lambda n: _fm.sort_key(n.id))
    if not rows:
        return ""
    return (
        '<section id="closures" style="%s"><div style="display:flex;'
        'align-items:baseline;gap:var(--sp-2);margin:0 0 var(--sp-4)">'
        '<span style="%s">Closed without you · %d</span></div>'
        '<p style="%s;margin:0 0 var(--sp-5);max-width:46ch">A machine decided '
        'these were finished. You have confirmed none of them. '
        '<strong>Each is its own call</strong> — five separate judgements, not '
        'one, because batching them would turn five decisions into one '
        'shrug.</p>%s</section>'
        % (SECTION, CHROME, len(rows), BODY,
           "".join(closure_row(n) for n in rows)))


def chat_row(row):
    """One chat. The title leads, the ids are a handle, and the way back is
    never a null.

    Every field here was already in the data and dropped in the render: the
    title, the verdict, the machine, the items. What rendered instead was the
    indexer's caveat -- four sentences across fifteen chats, each true of many
    and descriptive of none, saying what the INDEXER could not do rather than
    what the CHAT was about. The same failure the TL;DR had before it was
    rewritten, one section down.
    """
    verdict = (row.get("verdict") or "").upper()
    # Luminance, not hue. RESUME is worth returning to, so it is the brighter
    # of the two; no red, no green.
    tone = "var(--el-ink)" if verdict == "RESUME" else "var(--el-ink-3)"

    items = row.get("items") or []
    if items:
        shown = ", ".join(sorted(items, key=_fm.sort_key)[:3])
        touches = "touches %s%s" % (
            shown, ", +%d more" % (len(items) - 3) if len(items) > 3 else "")
    else:
        touches = "cites no task — it will not appear on any of them"

    if row.get("command"):
        way = ('<code style="font:400 var(--fs-meta)/1.6 var(--font-mono);'
               'color:var(--el-ink);display:block;white-space:pre-wrap;'
               'overflow-wrap:anywhere">%s</code>' % esc(row["command"]))
        # already absolute: `cd <path> && claude -r <id>` carries its own cd
    elif row.get("url"):
        way = '<a href="%s">%s</a>' % (esc(row["url"]), esc(row["url"]))
    elif row.get("instruction"):
        way = '<span style="%s;display:block;margin-bottom:var(--sp-3)">%s' \
              '</span>' % (BODY, esc(row["instruction"]))
        if row.get("instruction_command"):
            way += copyable(row["instruction_command"],
                            "On %s" % row["instruction_machine"])
    elif verdict == "RESTART":
        way = ('<span style="%s">Start a new chat. Its context is behind the '
               'repo, so there is nothing to return to — copy the task\'s '
               'kickoff prompt instead.</span>' % BODY)
    else:
        # Unrepresentable by construction: a resume with nowhere to go.
        way = ('<span style="%s">No way back was found when this index ran. '
               'Open it from the app\'s own session picker.</span>' % BODY)

    return (
        '<details style="border-top:1px solid var(--el-line)"><summary '
        'style="display:flex;gap:var(--sp-3);align-items:flex-start;'
        'padding:var(--sp-4) 0;min-height:44px">'
        '<span style="flex:1;display:grid;gap:var(--sp-1)">'
        '<span style="font:400 var(--fs-body-l)/1.4 var(--font-sans);'
        'color:var(--el-ink);text-wrap:pretty">%s</span>'
        '<span style="%s">%s · %s%s</span></span>'
        '<span style="flex:none;font:400 var(--fs-micro)/1 var(--font-mono);'
        'letter-spacing:0.1em;text-transform:uppercase;color:%s;'
        'border:1px solid var(--el-line);padding:var(--sp-2) var(--sp-3)">%s'
        '</span></summary>'
        '<div style="padding:var(--sp-1) 0 var(--sp-5)">%s%s%s</div></details>'
        % (esc(row.get("title") or "untitled"), META, esc(row.get("tool") or "chat"),
           esc(row.get("machine") or "unknown machine"),
           " · last active %s" % esc(short_date(row["last_active"]))
           if row.get("last_active") else "",
           tone, esc(verdict or "?"),
           field("What it touched", esc(touches), BODY_INK),
           field("The way back", way, BODY),
           field("Why this verdict", esc(row.get("reason") or "not recorded"),
                 META)))


def chats(root, manual):
    """One row per CHAT, newest first -- not one per (task, chat) pair.

    Item-major rendering turned 15 chats into 52 rows, because a thread citing
    fifty tasks rendered fifty times, and made the row's primary label an item
    id rather than the chat's own name.
    """
    rows = kickoff_mod.all_threads(root, manual, volatile=False)
    out = ['<section style="%s"><div style="display:flex;align-items:baseline;'
           'gap:var(--sp-2);margin:0 0 var(--sp-4)"><span style="%s">Chats · %d'
           '</span></div>' % (SECTION, CHROME, len(rows))]
    if not rows:
        out.append('<p style="%s;margin:0;max-width:46ch">None indexed. '
                   'Starting fresh is correct — nothing has been bound to a '
                   'chat yet, which is a cold start and not a fault.</p>' % BODY)
    else:
        resume = sum(1 for r in rows if (r.get("verdict") or "") == "resume")
        out.append('<p style="%s;margin:0 0 var(--sp-4);max-width:46ch">%d '
                   'worth returning to, %d better restarted. Every chat here '
                   'was indexed from a transcript on the machine that ran '
                   'it.</p>' % (BODY, resume, len(rows) - resume))
        out += [chat_row(r) for r in rows]
    out.append("</section>")
    return "".join(out)


# -------------------------------------------------------------------- render

SCRIPT = """
// The whole JS budget: copy, and the age renderer. Disclosure is <details>.
document.addEventListener('click', function (ev) {
  // Copy THIS block: the command sitting next to the button. Distinct from
  // [data-copy], which copies the row's whole prompt.
  var block = ev.target.closest('[data-copy-block]');
  if (block) {
    var code = block.closest('div').parentNode.querySelector('code');
    if (code) {
      navigator.clipboard.writeText(code.textContent).then(function () {
        var slot = block.querySelector('[data-copied-slot]');
        if (!slot) return;
        slot.textContent = ' \u00b7 copied';
        setTimeout(function () { slot.textContent = ''; }, 2000);
      });
    }
    return;
  }
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
  var el = ev.target.closest('[data-copy], [data-copy-block]');
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
    icon = favicon(root)
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
        ('<link rel="icon" type="%s" href="assets/%s">' % (icon[1], icon[0]))
        if icon else "",
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
        closures(model),
        chats(root, manual),
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

# The favicon is OPTIONAL and discovered, not assumed. If the source file is
# not there the page links nothing and the assets directory holds nothing --
# which is the state the site is in today, and is honest rather than a dangling
# <link> to a 404.
#
# It is SOURCE in tools/assets/ and copied out like the stylesheets, for the
# reason a hand-placed file cannot survive here: `publish.py --check` reports
# anything the generator did not produce as `orphan:` and the next publish
# deletes it.
FAVICONS = ("favicon.svg", "favicon.png", "favicon.ico")
FAVICON_TYPE = {".svg": "image/svg+xml", ".png": "image/png",
                ".ico": "image/x-icon"}


def favicon(root):
    """(filename, mime) for the first favicon source present, or None."""
    for name in FAVICONS:
        if os.path.exists(os.path.join(root, "tools", "assets", name)):
            return name, FAVICON_TYPE[os.path.splitext(name)[1]]
    return None


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
    icon = favicon(root)
    if icon:
        shutil.copyfile(os.path.join(root, "tools", "assets", icon[0]),
                        os.path.join(out, icon[0]))
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
