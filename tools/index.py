#!/usr/bin/env python3
"""Bind AI chat transcripts to items. Metadata only, sharded by machine.

    python3 tools/index.py                 index this machine, write the shard
    python3 tools/index.py --dry-run       report, write nothing
    python3 tools/index.py --json

Writing an item ID into a chat is what links that conversation to that work,
permanently and for free. `CLAUDE.md` asks every session to do it. This is the
tool that collects the result.

## Metadata only, and it is enforced rather than intended

This repo may go public, and the corpus it reads is 405 GiB of unredacted
working conversation across every project on this machine. So:

- **Exactly one function sees message text: `scan_text()`. It returns an int.**
  It may also add to a caller-owned set, and can only add strings drawn from a
  closed vocabulary of KNOWN item IDs -- so nothing it touches can carry text
  out with it.
- Every shard record is checked against a **key allowlist** before it is
  written. `validate.py` re-checks it independently, so a record carrying a
  `message`, `content`, `text` or `body` key fails CI even if this file is
  changed to emit one.
- Paths are relativised to `~`. `validate.py`'s disclosure screen rejects
  `/Users/<name>/` anyway; this makes the shard portable as well as clean.

## Sharded by machine, never merged

Writes only `state/threads/by-machine/<machine>.json`. Machine-derived data
never enters item frontmatter: two machines indexing the same day would collide
on a shared file, and item files are hand-edited. One writer per file, always.

Neither Codex nor Claude Code records a hostname anywhere, so the machine
identity is stamped here from `state/machines/`.

## Reading 405 GiB in a second

The Codex corpus is 1,108 rollout files totalling 405 GiB. A naive full scan is
about forty minutes. Line 1 (median 19 KB) plus a 64 KiB tail seek is enough to
identify and date every one of them, and does the whole corpus in about a
second. Nothing here ever reads a rollout end to end.
"""

import argparse
import datetime
import glob
import hashlib
import io
import json
import os
import re
import shutil
import sys

import _fm
import _model
import new as new_mod

HOME = os.path.expanduser("~")
TAIL_BYTES = 64 * 1024
CODEX_SESSIONS = "~/.codex/sessions"
CODEX_INDEX = "~/.codex/session_index.jsonl"
CLAUDE_PROJECTS = "~/.claude/projects"

# The ONLY keys a shard thread record may carry. Anything not here is dropped
# before writing and is an error in validate.py.
THREAD_KEYS = {
    "key", "tool", "title", "started", "last_active", "branch",
    "prompts", "items", "cited_unknown", "files", "forks",
    "verdict", "verdict_reason",
}

# The machine-local half. NEVER tracked: `id` is a private conversation
# identifier, `command` embeds this machine's layout AND that id, and `path`
# carries the home directory dash-encoded as `-Users-<name>-`, which is
# precisely why the disclosure screen's `/Users/` pattern never saw it.
#
# Found live on the public remote: the tracked shard was 13.5 KB of exactly
# this. `R-076` split `manual.yaml` for the same reason and the same lesson did
# not reach here -- the redaction was applied to the GENERATED surface
# (`api/threads.json`) and the AUTHORED source was left alone. Fifth route.
LOCAL_KEYS = {"id", "command", "path", "cwd", "parent"}

# A non-reversible handle joining the two halves. Not the id, and useless for
# resuming -- it only says "these two records are the same chat".
def thread_key(ident):
    return hashlib.sha256((ident or "").encode("utf-8")).hexdigest()[:12]

# --- resume or restart ------------------------------------------------------
# The second question this tool exists to answer: which of these chats relates
# to the work, and do I resume it or start fresh.
#
# Resume only when the chat's model of reality is still the current one. If
# commits landed after its last message, that chat is provably behind and the
# brief is not -- reopening it means arguing with a model of a repo that no
# longer exists.
STALE_DAYS = 7
LONG_PROMPTS = 60

# Verified on this machine before being printed. `claude` is on PATH; the codex
# binary is NOT, it lives inside the ChatGPT app bundle, so its command is
# emitted with a full path or not at all. A resume command that fails is worse
# than a sentence that works.
CLAUDE_BIN = "claude"
CODEX_BIN = "/Applications/ChatGPT.app/Contents/Resources/codex"


def resume_command(thread):
    tool = thread.get("tool")
    ident = thread.get("id")
    if not ident:
        return None
    if tool == "claude-code":
        # The RESOLVED path, not the bare name. `codex` is already addressed by
        # full path because it is not on PATH, and `claude` was left as a bare
        # word on the assumption that it always is. It is not: it lives in
        # ~/.local/bin, which this repo's tools inherit and an interactive zsh
        # here does not. The command verified fine when the index was BUILT --
        # a different process, a different PATH -- and then printed into a
        # shell that answered `zsh: command not found: claude`.
        #
        # Verifying in one environment and running in another is the same shape
        # as verifying on one machine and reading on another. Store what will
        # actually run.
        resolved = shutil.which(CLAUDE_BIN)
        if not resolved:
            return None
        cwd = thread.get("cwd")
        return "cd %s && %s -r %s" % (cwd or "~", tilde(resolved), ident)
    if tool == "codex":
        if not os.path.exists(CODEX_BIN):
            return None
        return "%s resume %s" % (CODEX_BIN, ident)
    return None


def verdict_for(thread, today, latest_commit, repo_for_cwd):
    """RESUME, RESTART, and a reason that states ABSOLUTE facts.

    The reason is FROZEN INTO THE SHARD and the shard is committed and
    published, so anything relative in it rots silently. Measured 2026-08-21:
    `public/` carried 40 occurrences of "0 day(s) old" -- true on the 19th, two
    days wrong by then -- and 67 of "this machine", which names whichever box
    ran the indexer, across 32 files.

    Both are the same rule the generator already obeys, arriving in STORED
    DATA where a published-surface check cannot reach: **a committed string may
    not carry a relative age or point at "here".**

    And the failure shape is why it needed a rule rather than a fix.
    `publish.py --check` regenerates from the frozen shard, gets the identical
    string back, and stays green -- so unlike `R-061`, which broke loudly the
    moment it was committed, this rots for as long as nobody re-runs the
    indexer.

    So: no ages, no deixis. The date the chat was last active, and what has
    landed since. The reader computes the rest, exactly as `data-audit-date`
    already lets the browser do.
    """
    last = (thread.get("last_active") or "")[:10]
    if not last:
        return "restart", "no last-activity timestamp — cannot tell how stale it is"

    try:
        age = (today - datetime.date.fromisoformat(last)).days
    except ValueError:
        return "restart", "unparseable last-activity date %r" % last

    repo = repo_for_cwd.get(thread.get("cwd"))
    landed = None
    if repo and latest_commit.get(repo):
        landed = latest_commit[repo][:10] > last

    if landed:
        return ("restart",
                "last active %s; %s has commits after that, so its model of "
                "the repo is provably behind and the brief is not"
                % (last, repo))
    if age > STALE_DAYS:
        return ("restart",
                "last active %s, more than %d days before this index ran"
                % (last, STALE_DAYS))
    if (thread.get("prompts") or 0) > LONG_PROMPTS:
        return ("restart",
                "%d prompts — long enough that its early context is noise"
                % thread["prompts"])
    if landed is None:
        return ("resume",
                "last active %s; could NOT check whether work landed in its "
                "repo — resume, but re-read the brief first" % last)
    return ("resume",
            "last active %s, and nothing has landed in %s since"
            % (last, repo or "its repo"))

# Keys that must never appear, at any depth, in a shard.
FORBIDDEN_KEY = re.compile(r"(?i)message|content|text|body|prompt_text|summary")


def tilde(path):
    return "~" + path[len(HOME):] if path.startswith(HOME) else path


def known_ids(root):
    """id -> the date it was created.

    The date is load-bearing, not decoration. An ID is unique only WITHIN a
    seed generation: this repo's first seed was rebuilt, and IDs were reused
    for unrelated work. A transcript from 2026-08-15 citing `Q-004` was citing
    the old Q-004, next to `EL-040` and `EL-042`, which do not exist now. Today
    `Q-004` is "where do 300 liveness taps a second come from". Binding them
    would be a confident, plausible, wrong attachment -- the shape this
    portfolio keeps getting burned by.
    """
    model = _model.Model.load(root)
    out = {}
    for node in list(model.nodes.values()) + list(model.decisions.values()):
        out[node.id] = node.get("created") or ""
    return out


def id_pattern(ids):
    """Anchored to the LIVE prefix set, and every hit must be a KNOWN id.

    The spec's `\\b[A-Z]{2,4}-\\d{3,}\\b` matched `AES-256` and `SHA-256` 916
    times on the real corpus -- 100% false positives -- and missed `Q-007`
    entirely because its prefix is one letter. Two independent narrowings:
    the prefix alternation, and membership in the closed set below.

    The alternation is derived from `state/projects/*/project.md` now rather
    than hardcoded, so a project created inline is scanned for from its first
    commit instead of being silently invisible.
    """
    return _fm.mention_re()


# --- the one function allowed to see message text ---------------------------

def scan_text(text, known, found, unknown):
    """Count nothing; find item IDs. Returns an INT.

    This is the only function in this file that receives raw conversation text.
    It returns an integer, and the only other effect it may have is inserting
    into `found` / `unknown` -- and every string it inserts is matched by
    `_fm.mention_re()` and then checked against `known`, so the sets can never
    accumulate anything but item IDs this repo already defines.

    Nothing else in this module may take a text argument.
    """
    hits = 0
    for match in _fm.mention_re().findall(text):
        hits += 1
        if match in known:
            found.add(match)
        else:
            unknown.add(match)
    return hits


# --- Codex ------------------------------------------------------------------

def read_head_and_tail(path):
    """Line 1 plus the last TAIL_BYTES, without reading the middle."""
    with open(path, "rb") as fh:
        first = fh.readline()
        size = os.fstat(fh.fileno()).st_size
        if size > TAIL_BYTES:
            fh.seek(-TAIL_BYTES, io.SEEK_END)
            tail = fh.read()
        else:
            fh.seek(len(first))
            tail = fh.read()
    return first, tail, size


def codex_titles():
    """session_index.jsonl is TITLES ONLY.

    Its `updated_at` lagged real last activity by 9 and 11 days on this corpus,
    so it is read for `thread_name` and nothing else. A date that is wrong by
    a week and a half is worse than no date.
    """
    path = os.path.expanduser(CODEX_INDEX)
    titles = {}
    if not os.path.exists(path):
        return titles
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if row.get("id"):
                titles[row["id"]] = row.get("thread_name")
    return titles


def index_codex(root, known, stats):
    titles = codex_titles()
    base = os.path.expanduser(CODEX_SESSIONS)
    threads = {}
    if not os.path.isdir(base):
        stats["codex_missing"] = True
        return []

    for path in sorted(glob.glob(os.path.join(base, "*", "*", "*",
                                              "rollout-*.jsonl"))):
        stats["codex_files"] += 1
        try:
            first, tail, size = read_head_and_tail(path)
        except OSError:
            stats["unreadable"] += 1
            continue
        try:
            head = json.loads(first)
        except ValueError:
            stats["malformed"] += 1
            continue

        payload = head.get("payload") or {}
        session_id = payload.get("session_id") or head.get("id")
        if not session_id:
            stats["no_session_id"] += 1
            continue

        # `source` is POLYMORPHIC: a str on roots, an object on subagents.
        # Exactly 7 of 1108 are roots. A strict parser breaks on this.
        is_root = isinstance(payload.get("source"), str)

        # DEDUPE ON session_id, NOT filename -- 681 files share one root.
        thread = threads.setdefault(session_id, {
            "id": session_id, "tool": "codex",
            "title": titles.get(session_id),
            "started": payload.get("timestamp") or head.get("timestamp"),
            "last_active": None, "cwd": None, "branch": None,
            "prompts": 0, "items": set(), "cited_unknown": set(),
            "path": tilde(path), "files": 0, "forks": 0, "parent": None,
        })
        thread["files"] += 1
        if is_root:
            thread["title"] = thread["title"] or payload.get("instructions_name")
            cwd = payload.get("cwd")
            if cwd:
                thread["cwd"] = tilde(cwd)
        if payload.get("parent_thread_id") or payload.get("forked_from_id"):
            thread["forks"] += 1
            thread["parent"] = thread["parent"] or payload.get("parent_thread_id")

        last = None
        for raw in tail.split(b"\n"):
            if not raw.strip():
                continue
            try:
                row = json.loads(raw)
            except ValueError:
                continue        # a partial first line from the seek; expected
            ts = row.get("timestamp")
            if ts:
                last = ts
            thread["prompts"] += scan_text(
                raw.decode("utf-8", "replace"), known,
                thread["items"], thread["cited_unknown"]) and 0 or 0
        if last and (thread["last_active"] or "") < last:
            thread["last_active"] = last

    stats["codex_threads"] = len(threads)
    return list(threads.values())


# --- Claude Code ------------------------------------------------------------

def claude_files():
    base = os.path.expanduser(CLAUDE_PROJECTS)
    for path in sorted(glob.glob(os.path.join(base, "*", "**", "*.jsonl"),
                                 recursive=True)):
        rel = os.path.relpath(path, base)
        # isSidechain transcripts carry the PARENT's sessionId and would
        # double-count it; workflow journals are a different schema entirely.
        if os.sep + "subagents" + os.sep in os.sep + rel:
            continue
        if rel.endswith(os.sep + "journal.jsonl") or "workflows" in rel.split(os.sep):
            continue
        yield path


def index_claude(root, known, stats, exclude_cwd):
    threads = []
    for path in claude_files():
        stats["claude_files"] += 1
        rows = []
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rows.append(json.loads(line))
                    except ValueError:
                        stats["malformed"] += 1
        except OSError:
            stats["unreadable"] += 1
            continue
        if not rows:
            continue
        if any(r.get("isSidechain") for r in rows):
            stats["claude_sidechain_skipped"] += 1
            continue

        # There is NO session_meta record. Line 1 is a queue-operation, which
        # carries neither cwd nor branch. Scan FORWARD to the first real
        # user/assistant record for them.
        cwd = branch = session_id = None
        for row in rows:
            if row.get("type") in ("user", "assistant"):
                cwd = cwd or row.get("cwd")
                branch = branch or row.get("gitBranch")
                session_id = session_id or row.get("sessionId")
                if cwd and session_id:
                    break
        session_id = session_id or os.path.splitext(os.path.basename(path))[0]

        # `timestamp` is ABSENT on ai-title, custom-title, last-prompt and mode
        # records, and those are frequently LAST. Taking the final line yields
        # None. Scan BACKWARD for the last record that actually has one.
        last_active = None
        for row in reversed(rows):
            if row.get("timestamp"):
                last_active = row["timestamp"]
                break
        started = next((r["timestamp"] for r in rows if r.get("timestamp")), None)

        title = None
        for row in rows:
            title = row.get("customTitle") or title
        if not title:
            for row in rows:
                title = row.get("aiTitle") or title
        if not title:
            for row in rows:
                if row.get("slug"):
                    title = row["slug"]
                    break

        items, unknown = set(), set()
        prompts = 0
        for row in rows:
            if row.get("type") == "user" and not row.get("isMeta"):
                message = row.get("message") or {}
                body = message.get("content")
                blocks = body if isinstance(body, list) else []
                # A tool_result is the harness talking, not him.
                if not any(isinstance(b, dict) and b.get("type") == "tool_result"
                           for b in blocks):
                    prompts += 1
            scan_text(json.dumps(row, ensure_ascii=False), known, items, unknown)

        rel_cwd = tilde(cwd) if cwd else None
        # This repo's own planning transcripts cite every ID constantly --
        # EL-001 alone appears 664 times -- because they are transcripts ABOUT
        # the tracker. Binding all of it would attach ~2,000 self-references on
        # day one and drown every real signal.
        #
        # But dropping these transcripts wholesale is too blunt: POS-001..005
        # were genuinely WORKED in them, and that is exactly the link this
        # indexer exists to make. So the rule is narrower than "exclude":
        # inside this repo's own sessions, keep only items belonging to this
        # repo's own project. Discussion is dropped; work is kept.
        if rel_cwd and exclude_cwd and rel_cwd == exclude_cwd:
            stats["self_scoped"] += 1
            items = {i for i in items if i.startswith("POS-")}
            # Same reason for the unknown list: these sessions DESIGNED the ID
            # scheme, so they discuss EL-1001, EL-2999 and other illustrations
            # that were never meant to exist. Reporting them as "cited but not
            # defined" would bury the one finding that matters -- a real
            # transcript citing a real ID from a discarded seed generation.
            unknown = set()

        threads.append({
            "id": session_id, "tool": "claude-code", "title": title,
            "started": started, "last_active": last_active,
            "cwd": rel_cwd, "branch": branch, "prompts": prompts,
            "items": items, "cited_unknown": unknown,
            "path": tilde(path), "files": 1, "forks": 0, "parent": None,
        })
    stats["claude_threads"] = len(threads)
    return threads


# --- shard ------------------------------------------------------------------

# Words, not syntax. E-PUBLIC-SESSION-ID, E-PUBLIC-HOME-DIR and
# E-PUBLIC-LOCAL-PATH are all structural -- uuids, usernames, paths -- and none
# of them can see a sentence that is merely no longer true.
FROZEN_CLAIM = re.compile(
    r"(?i)\bthis machine\b|\bday\(s\) old\b|\b\d+\s+days?\s+(?:old|stale|ago)\b"
    r"|\btoday\b|\byesterday\b|\bright now\b")


def frozen_claim(text):
    """The offending phrase, or None. A reason is frozen into a committed file,
    so it may not carry a relative age or point at "here"."""
    found = FROZEN_CLAIM.search(text or "")
    return found.group(0) if found else None


def split_thread(thread):
    """(tracked, local). Two records, one chat, joined by a non-reversible key."""
    ident = thread.get("id") or ""
    thread = dict(thread, key=thread_key(ident))
    tracked = {k: v for k, v in thread.items() if k in THREAD_KEYS}
    local = {k: v for k, v in thread.items() if k in LOCAL_KEYS}
    local["key"] = tracked["key"]
    return tracked, local


# `clean()` runs inside build() and used to strip to THREAD_KEYS, which now
# excludes the local half -- so the split in main() found nothing left to
# write. It keeps BOTH sets here and main() separates them, which is also the
# only place that knows which file each half goes to.
ALLOWED_ON_BUILD = THREAD_KEYS | LOCAL_KEYS


def clean(thread):
    """Enforce the allowlist at the point of writing, not by convention."""
    out = {}
    for key, value in thread.items():
        if key not in ALLOWED_ON_BUILD:
            continue
        if FORBIDDEN_KEY.search(key):
            continue
        if isinstance(value, set):
            value = sorted(value, key=_fm.sort_key if value and
                           all(_fm.parse_id(v) for v in value) else str)
        out[key] = value
    return out


def gate_by_age(thread, created_by):
    """Drop citations that predate the item they name.

    A conversation cannot cite an item that did not exist when it happened.
    Anything caught here is an ID reused across seed generations, and it is
    reported rather than dropped silently -- a collision is a finding.
    """
    when = (thread.get("last_active") or thread.get("started") or "")[:10]
    if not when:
        return set(), set()
    kept, stale = set(), set()
    for item_id in thread.get("items") or ():
        created = (created_by.get(item_id) or "")[:10]
        if created and when < created:
            stale.add(item_id)
        else:
            kept.add(item_id)
    return kept, stale


def build(root, machine):
    known = known_ids(root)
    stats = {k: 0 for k in ("codex_files", "claude_files", "malformed",
                            "unreadable", "no_session_id", "self_excluded",
                            "claude_sidechain_skipped", "codex_threads",
                            "claude_threads", "generation_collisions",
                            "self_scoped")}
    self_cwd = tilde(root)
    threads = index_codex(root, known, stats) + \
        index_claude(root, known, stats, self_cwd)
    for thread in threads:
        kept, stale = gate_by_age(thread, known)
        if stale:
            stats["generation_collisions"] += len(stale)
            thread.setdefault("cited_unknown", set()).update(stale)
        thread["items"] = kept
    # --- resume or restart, per thread
    stamp_path = os.path.join(root, "build", "audit-stamp.json")
    latest_commit = {}
    if os.path.exists(stamp_path):
        try:
            with open(stamp_path, "r", encoding="utf-8") as fh:
                latest_commit = json.load(fh).get("latest_commit") or {}
        except ValueError:
            pass
    repo_for_cwd = {}
    try:
        with open(os.path.join(root, "state", "repos.json"), "r",
                  encoding="utf-8") as fh:
            for name, spec in json.load(fh).items():
                if name.startswith("_") or not isinstance(spec, dict):
                    continue
                if spec.get("local"):
                    repo_for_cwd[tilde(os.path.expanduser(spec["local"]))] = name
    except (OSError, ValueError):
        pass
    today = datetime.date.today()
    for thread in threads:
        verdict, reason = verdict_for(thread, today, latest_commit, repo_for_cwd)
        thread["verdict"] = verdict
        thread["verdict_reason"] = reason
        thread["command"] = resume_command(thread) if verdict == "resume" else None
        if verdict == "resume" and not thread["command"]:
            thread["verdict_reason"] += (
                " · no verified way back was found when this index ran — open "
                "it from the app's own session picker")
    for thread in threads:
        offence = frozen_claim(thread.get("verdict_reason") or "")
        if offence:
            raise SystemExit(
                "refusing to write the shard: a verdict reason says %r.\n"
                "This string is committed and published, so a relative age "
                "rots silently and \"this machine\" names whichever box ran "
                "the indexer. State the date; let the reader compute the rest."
                % offence)
    threads = [clean(t) for t in threads]
    threads.sort(key=lambda t: (t.get("last_active") or "", t.get("id") or ""),
                 reverse=True)

    bound = [t for t in threads if t.get("items")]
    unknown = sorted({u for t in threads for u in (t.get("cited_unknown") or [])})
    shard = {
        "machine": machine,
        "generated": datetime.date.today().isoformat(),
        "tool_counts": {
            "codex": stats["codex_threads"],
            "claude-code": stats["claude_threads"],
        },
        "coverage": {
            "codex_files_read": stats["codex_files"],
            "claude_files_read": stats["claude_files"],
            "malformed_lines_skipped": stats["malformed"],
            "unreadable_files": stats["unreadable"],
            "sidechains_excluded": stats["claude_sidechain_skipped"],
            "self_transcripts_scoped_to_own_project": stats["self_scoped"],
            "threads_bound_to_items": len(bound),
            "cited_but_unknown_ids": unknown,
            "generation_collisions": stats["generation_collisions"],
        },
        "threads": threads,
    }
    return shard, stats, bound


def ways_back(root, machine):
    """What the dashboard cannot print, printed here.

    The page says a resume command exists and names the machine holding it;
    it cannot print the command itself, because `public/` is served to every
    machine and the command embeds this one's paths and a session id. So the
    page points at this, and this is the step that actually hands it over --
    rather than at `index.py` with no arguments, which REBUILDS the index and
    prints nothing you can paste.
    """
    path = os.path.join(root, "state", "threads", "by-machine",
                        "%s.local.json" % machine)
    if not os.path.exists(path):
        sys.stderr.write(
            "no local thread file on %s yet.\n"
            "  cd %s && python3 tools/index.py\n"
            "builds it, then re-run this.\n" % (machine, tilde(root)))
        return 1
    with open(path, "r", encoding="utf-8") as fh:
        local = {row["key"]: row for row in json.load(fh).get("threads") or []}
    shard_path = os.path.join(root, "state", "threads", "by-machine",
                              "%s.json" % machine)
    with open(shard_path, "r", encoding="utf-8") as fh:
        threads = json.load(fh).get("threads") or []

    shown = 0
    header = False
    for thread in sorted(threads, key=lambda t: t.get("last_active") or "",
                         reverse=True):
        row = local.get(thread.get("key")) or {}
        if thread.get("verdict") != "resume":
            continue
        if not header:
            # It printed a bare list of titles and commands and never said what
            # to do with them. "How do I hop back into one" was not answerable
            # from the output.
            print("Paste one of these into a terminal. It reopens that chat "
                  "where it left off,")
            print("with its whole history — you are not starting over.\n")
            header = True
        shown += 1
        command = row.get("command")
        # Re-verified HERE, not trusted from the index. The binary that existed
        # when the shard was written may not exist now, and may not be on the
        # PATH of the shell reading this -- which is exactly how a command that
        # passed its check at build time printed `command not found`.
        if command:
            binary = command.split("&&")[-1].strip().split()[0]
            expanded = os.path.expanduser(binary)
            if not (os.path.exists(expanded) or shutil.which(binary)):
                command = None
                stale = binary
        print("%s" % (thread.get("title") or thread.get("key")))
        if command:
            print("  %s" % command)
        elif row.get("command"):
            print("  the recorded command names %s, which does not resolve "
                  "here any more." % stale)
            print("  Re-run `python3 tools/index.py` in this shell to rebuild "
                  "it, or open the chat from the app's session picker.")
        else:
            print("  no verified command — open it from the app's own session "
                  "picker")
        print()
    if not shown:
        print("Nothing is worth resuming on %s. Every indexed chat here reads "
              "RESTART — start a new one and copy the task's kickoff prompt "
              "from the dashboard instead." % machine)
    else:
        print("%d chat(s) worth returning to. The rest read RESTART: their "
              "model of the repo is behind, so a fresh chat with the task's "
              "kickoff prompt beats reopening them." % shown)
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--ways-back", action="store_true",
                        help="print the resume command for each indexed chat")
    args = parser.parse_args(argv)

    if args.ways_back:
        return ways_back(_model.find_root(), new_mod.machine_id(_model.find_root()))

    root = _model.find_root()
    machine = new_mod.machine_id(root)
    shard, stats, bound = build(root, machine)

    out_dir = os.path.join(root, "state", "threads", "by-machine")
    out_path = os.path.join(out_dir, "%s.json" % machine)
    local_path = os.path.join(out_dir, "%s.local.json" % machine)

    # SPLIT on write. The tracked half is metadata; the local half holds the
    # session id, the resume command and this machine's paths, and is
    # git-ignored. See LOCAL_KEYS.
    local_rows = []
    tracked_rows = []
    for thread in shard["threads"]:
        tracked, local = split_thread(thread)
        tracked_rows.append(tracked)
        if any(local.get(k) for k in LOCAL_KEYS):
            local_rows.append(local)
    shard["threads"] = tracked_rows

    if not args.dry_run:
        os.makedirs(out_dir, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(shard, fh, indent=2, sort_keys=True)
            fh.write("\n")
        with open(local_path, "w", encoding="utf-8") as fh:
            json.dump({"machine": machine, "threads": local_rows}, fh,
                      indent=2, sort_keys=True)
            fh.write("\n")

    if args.json:
        print(json.dumps(shard, indent=2, sort_keys=True))
        return 0

    cov = shard["coverage"]
    print("machine %s" % machine)
    print("  codex        %4d threads from %d files"
          % (shard["tool_counts"]["codex"], cov["codex_files_read"]))
    print("  claude-code  %4d threads from %d files"
          % (shard["tool_counts"]["claude-code"], cov["claude_files_read"]))
    print()
    print("  bound to an item: %d thread(s)" % cov["threads_bound_to_items"])
    for thread in bound[:12]:
        print("    %-10s %-34s %s"
              % (thread["tool"], (thread.get("title") or thread["id"])[:34],
                 ", ".join(thread["items"])))
    if not bound:
        print("    none. Zero found is zero found, not a failure.")
    if cov["cited_but_unknown_ids"]:
        print()
        print("  cited but not defined here: %s"
              % ", ".join(cov["cited_but_unknown_ids"]))
        print("    A finding, not an error -- either a typo or an item that "
              "was never written.")
    print()
    print("Resume or restart")
    for thread in shard["threads"][:10]:
        mark = "RESUME " if thread["verdict"] == "resume" else "restart"
        print("  %s %-9s %s" % (mark, thread["tool"],
                                (thread.get("title") or thread["id"])[:44]))
        print("           %s" % thread["verdict_reason"])
        if thread.get("command"):
            print("           $ %s" % thread["command"])
    print()
    print("Coverage: read %d codex + %d claude files · skipped %d malformed "
          "line(s), %d unreadable file(s) · excluded %d sidechain · %d own-repo "
          "session(s) scoped to POS-* only"
          % (cov["codex_files_read"], cov["claude_files_read"],
             cov["malformed_lines_skipped"], cov["unreadable_files"],
             cov["sidechains_excluded"],
             cov["self_transcripts_scoped_to_own_project"]))
    print("%s %s" % ("would write" if args.dry_run else "wrote",
                     os.path.relpath(out_path, root)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
