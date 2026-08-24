#!/usr/bin/env python3
"""Is the site people actually read the site this repo actually contains?

    python3 tools/deployed.py            what is live, and how far behind

Every other gate in this repo answers a question about the working tree.
`validate.py` reads state, `publish.py --check` compares `public/` against a
fresh generation, the suite runs offline. **All three were green while the
published site was two commits stale**, because none of them can see the one
thing that matters to a reader: what is being served.

The failure that motivated this was silent in the loudest possible way. Adding
an `intake` job to `pages.yml` made `deploy` skip -- a skip propagates
transitively through `needs`, and `deploy` named only `gate`, so it inherited
a skip from a job two links up. The run finished with three green jobs and
reported SUCCESS. Nothing anywhere said the site had stopped updating.

**A pipeline that stops while still reporting success is worse than one that
breaks**, and this repo already has the general rule for it: a mechanical
signal is not the primary source. A green workflow run is a signal about the
workflow. The primary source is the deployment.

Exit 0 in sync, 1 behind, 2 could not look -- and 2 is never 0. "I could not
reach GitHub" rendered as "the site is current" is the same defect one layer
out.
"""

import argparse
import json
import subprocess
import sys

REPO = "hooterjackson/product-os"


def gh(args):
    proc = subprocess.run(["gh"] + args, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)
    if proc.returncode != 0:
        return None, proc.stderr.decode().strip() or "gh failed"
    return proc.stdout.decode(), None


def live_sha():
    """The commit behind the newest github-pages deployment."""
    out, err = gh(["api", "repos/%s/deployments?environment=github-pages"
                   "&per_page=1" % REPO])
    if err is not None:
        return None, err
    try:
        rows = json.loads(out)
    except ValueError as exc:
        return None, "unparseable response: %s" % exc
    if not rows:
        return None, "no github-pages deployment exists yet"
    return rows[0].get("sha"), None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", default="origin/main",
                        help="what the site SHOULD be serving")
    args = parser.parse_args(argv)

    # `git fetch` first, always. A tracking ref that has not been fetched
    # answers a question about last week -- measured at 54 commits stale.
    fetch = subprocess.run(["git", "fetch", "--quiet", "origin", "main"],
                           stderr=subprocess.PIPE)
    if fetch.returncode != 0:
        sys.stderr.write("could not fetch: %s\nThat is not the same as being "
                         "in sync.\n" % fetch.stderr.decode().strip())
        return 2

    sha, err = live_sha()
    if err is not None:
        sys.stderr.write("could not read the deployment: %s\n"
                         "That is not the same as being in sync.\n" % err)
        return 2

    want = subprocess.run(["git", "rev-parse", args.ref],
                          stdout=subprocess.PIPE).stdout.decode().strip()
    if sha == want:
        print("live: %s — in sync with %s" % (sha[:8], args.ref))
        return 0

    behind = subprocess.run(
        ["git", "rev-list", "--count", "%s..%s" % (sha, args.ref)],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    count = behind.stdout.decode().strip() or "?"
    print("live: %s\nwant: %s (%s)\nthe published site is %s commit(s) behind"
          % (sha[:8], want[:8], args.ref, count))
    print("\nA workflow run reporting success is a fact about the workflow, "
          "not about what is being served.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
