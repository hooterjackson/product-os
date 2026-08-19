#!/usr/bin/env python3
"""Read-only git access that refuses to lie about what landed.

This module exists because of one measurement:

    $ cd ~/Claude/engineered-lighting
    $ git rev-list --count HEAD..origin/main
    0
    $ gh api repos/.../compare/90ff98d...main --jq .ahead_by
    54

The local tracking ref had not been fetched since July. `git log` answered
confidently and wrongly, and it would have answered wrongly in the same
direction for every consumer: the audit would find no new commits, a brief
would stamp itself "current", and a resume recommendation would say "nothing
landed since this thread."

So: fetch first, and if the fetch fails, return UNREACHABLE. Never silently
fall back to the local ref -- a wrong answer delivered confidently is worse
than no answer, and this whole system is a bet on being trustworthy about state.
"""

import os
import subprocess

UNREACHABLE = "unreachable"

# Every date this module returns is UTC.
#
# `%cI` renders the committer's OWN recorded offset, while the GitHub API
# renders UTC. Same instant, different calendar day for anything committed in
# the evening west of Greenwich -- and `stale.py` compares `[:10]` slices, so a
# doc read from a local clone came out one day older than the same doc read
# through the API. A staleness figure that depends on which code path answered
# is exactly the kind of quiet disagreement this system exists to remove.
DATE_FMT = "--date=format-local:%Y-%m-%dT%H:%M:%SZ"
_UTC_ENV = dict(os.environ, TZ="UTC")

_fetched = set()


def _run(args, cwd=None, timeout=60):
    try:
        proc = subprocess.run(
            args, cwd=cwd, timeout=timeout, env=_UTC_ENV,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout.decode("utf-8", "replace").strip()


def is_repo(path):
    return _run(["git", "-C", path, "rev-parse", "--git-dir"]) is not None


def remotes(path):
    """Configured remote names. Empty means there is nothing to be stale FROM."""
    out = _run(["git", "-C", path, "remote"])
    return [r for r in (out or "").split() if r]


def fetch(path, remote="origin"):
    """Fetch once per process per repo. Returns True on success."""
    key = (path, remote)
    if key in _fetched:
        return True
    if not is_repo(path):
        return False
    ok = _run(["git", "-C", path, "fetch", "--quiet", "--no-tags", remote]) is not None
    if ok:
        _fetched.add(key)
    return ok


def default_branch(path, remote="origin"):
    """Resolve the remote's default branch. Do not assume 'main'.

    gimbal-bench's default branch is 'master'; assuming 'main' fails silently
    against it, which is the worst possible failure for an evidence query.
    """
    head = _run(["git", "-C", path, "symbolic-ref",
                 "refs/remotes/%s/HEAD" % remote])
    if head:
        return head.rsplit("/", 1)[-1]
    for candidate in ("main", "master"):
        if _run(["git", "-C", path, "rev-parse", "--verify",
                 "%s/%s" % (remote, candidate)]):
            return candidate
    return None


def fetch_then_query(path, args, remote="origin"):
    """Run a read-only git query, but only after a successful fetch.

    Returns the command's stdout, or UNREACHABLE. Callers MUST handle
    UNREACHABLE explicitly and must never treat it as an empty result.
    """
    if not fetch(path, remote):
        return UNREACHABLE
    out = _run(["git", "-C", path] + list(args))
    return UNREACHABLE if out is None else out


def commits_since(path, since_iso, ref=None, remote="origin"):
    """Commits on the remote's default branch since an ISO timestamp.

    Returns a list of (sha, iso_date, subject), or UNREACHABLE.
    """
    if not fetch(path, remote):
        return UNREACHABLE
    if ref is None:
        branch = default_branch(path, remote)
        if branch is None:
            return UNREACHABLE
        ref = "%s/%s" % (remote, branch)
    out = _run(["git", "-C", path, "log", ref, "--no-merges", DATE_FMT,
                "--since=%s" % since_iso, "--format=%h\x1f%cd\x1f%s"])
    if out is None:
        return UNREACHABLE
    rows = []
    for line in out.splitlines():
        parts = line.split("\x1f")
        if len(parts) == 3:
            rows.append(tuple(parts))
    return rows


def last_commit_date(path, file_path, remote="origin"):
    """ISO date of the last commit touching a path, on the remote's default
    branch. Returns UNREACHABLE rather than guessing from local state."""
    if not fetch(path, remote):
        return UNREACHABLE
    branch = default_branch(path, remote)
    if branch is None:
        return UNREACHABLE
    out = _run(["git", "-C", path, "log", "-1", DATE_FMT, "--format=%cd",
                "%s/%s" % (remote, branch), "--", file_path])
    if out is None:
        return UNREACHABLE
    return out or None


def behind_count(path, remote="origin"):
    """How many commits the local HEAD is behind the fetched remote.

    Deliberately fetches first. Without that this returns 0 on a stale clone,
    which is the exact bug this module was written for.
    """
    if not fetch(path, remote):
        return UNREACHABLE
    branch = default_branch(path, remote)
    if branch is None:
        return UNREACHABLE
    out = _run(["git", "-C", path, "rev-list", "--count",
                "HEAD..%s/%s" % (remote, branch)])
    if out is None:
        return UNREACHABLE
    try:
        return int(out)
    except ValueError:
        return UNREACHABLE
