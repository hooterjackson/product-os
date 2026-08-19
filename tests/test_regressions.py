#!/usr/bin/env python3
"""Assertions for defects that have already happened here.

    python3 tests/test_regressions.py
    python3 tools/validate.py --tests      (runs this as part of the CI gate)

Not a suite. Every test below pins a bug that shipped in this repo and was
found by running the code and looking at the output — which is a detection
method that works exactly once per defect, by luck, and possibly after somebody
has acted on a wrong answer.

They share one shape: **the code returned a confident answer that was wrong,
and nothing about the answer looked wrong.** That is the class CLAUDE.md now
opens on, and it is why these four are worth more than coverage.
"""

import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import _fm          # noqa: E402
import _git         # noqa: E402
import apply as apply_mod   # noqa: E402
import audit        # noqa: E402


class CanonicalFormIsAFixedPoint(unittest.TestCase):
    """`render()` rstripped the body, but `split()` hands back the blank line
    after the closing fence — so every round trip grew one more. The first file
    `new.py` ever wrote would have failed validate.py's canonical check on
    sight, and the error message would have blamed the file, not the writer."""

    def test_idempotent(self):
        for body in ("hello\n\nworld", "", "\n\nleading blanks\n", "one line"):
            once = _fm.render({"id": "EL-001", "title": "x"}, body, "item")
            twice = _fm.canonicalize(once, "item")
            thrice = _fm.canonicalize(twice, "item")
            self.assertEqual(once, twice, "not a fixed point for %r" % body)
            self.assertEqual(twice, thrice)

    def test_exactly_one_blank_line_after_the_fence(self):
        text = _fm.render({"id": "EL-001"}, "body", "item")
        self.assertIn("}\n---\n\nbody\n", text)


class DatesAreUTC(unittest.TestCase):
    """`%cI` renders the committer's own offset; the GitHub API renders UTC.
    Same instant, different calendar day for anything committed in the evening
    west of Greenwich — and stale.py compares `[:10]` slices, so a document
    read from a clone came out one day older than the same document read
    through the API. The only number the detector publishes was silently off
    by one, in a direction that depended on which code path answered."""

    def test_git_date_format_is_utc_normalised(self):
        self.assertIn("format-local:", _git.DATE_FMT)
        self.assertTrue(_git.DATE_FMT.endswith("Z"),
                        "the format must pin a Z suffix, not a local offset")
        self.assertEqual(_git._UTC_ENV.get("TZ"), "UTC")

    def test_no_caller_still_uses_committer_local(self):
        """`%cI` is the trap. It may appear in prose explaining the bug; it
        must appear in no git format string."""
        for name in ("_git.py", "stale.py", "audit.py"):
            with open(os.path.join(ROOT, "tools", name), encoding="utf-8") as fh:
                for lineno, line in enumerate(fh, 1):
                    code = line.split("#", 1)[0]
                    self.assertNotIn("--format=%cI", code,
                                     "%s:%d asks git for a local-offset date"
                                     % (name, lineno))
                    self.assertNotIn("\\x1f%cI", code,
                                     "%s:%d asks git for a local-offset date"
                                     % (name, lineno))

    def test_utc_matches_a_known_commit(self):
        """b216f98 is 2026-07-21T02:03Z. Its committer offset puts it on the
        20th locally — the exact pair that produced the off-by-one."""
        clone = os.path.expanduser("~/Claude/engineered-lighting")
        if not os.path.isdir(clone):
            self.skipTest("no local clone to check against")
        out = _git._run(["git", "-C", clone, "log", "-1", _git.DATE_FMT,
                         "--format=%cd", "b216f98"])
        if not out:
            self.skipTest("commit not present locally")
        self.assertEqual(out[:10], "2026-07-21", "date drifted back to local time")


class BroadGlobsAreReportedNeverAbsorbed(unittest.TestCase):
    """The tool's own stated failure mode, which occurred inside the tool.

    `EL-004` is done and its evidence rule is `docs/**`, so the attribution
    scan had it claiming all five Doc 4a commits. Group D then printed nothing
    for the site — which reads as "the seed covers the site" and actually meant
    "a broad rule on a finished item ate them". Indistinguishable from success,
    which is the one failure that ends trust in an audit."""

    def test_glob_star_does_not_cross_a_slash(self):
        matcher = audit.glob_re("docs/*.md")
        self.assertTrue(matcher.match("docs/06-message-contract.md"))
        self.assertFalse(matcher.match("docs/cad/renders/x.md"),
                         "`*` crossed a directory separator")

    def test_doublestar_does_cross(self):
        self.assertTrue(audit.glob_re("docs/**").match("docs/a/b/c.md"))

    def test_prefix_is_not_a_glob(self):
        """`captures/gimbal10/fixture/ring-*.md` reduced to its prefix claimed
        all 98 commits under that directory."""
        matcher = audit.glob_re("captures/gimbal10/fixture/ring-*.md")
        self.assertTrue(matcher.match("captures/gimbal10/fixture/ring-mirror.md"))
        self.assertFalse(matcher.match("captures/gimbal10/fixture/bench-session.md"))

    def test_a_broad_glob_produces_a_finding_rather_than_silence(self):
        self.assertLessEqual(audit.BROAD_GLOB_COMMITS, 20)
        source = open(os.path.join(ROOT, "tools", "audit.py"), encoding="utf-8").read()
        self.assertIn("too broad to attribute anything", source)

    def test_group_d_is_built_from_reported_shas_not_from_claims(self):
        """The fix: a commit leaves group D only when a FINDING named it."""
        source = open(os.path.join(ROOT, "tools", "audit.py"), encoding="utf-8").read()
        self.assertIn("for sha in f.shas", source)
        self.assertIn("if c[0] not in reported", source)
        self.assertNotIn("if c[0] not in repo.claimed", source,
                         "group D is back to trusting the attribution scan")


class ApplyRefusals(unittest.TestCase):
    """Three refusals that must not bend. Each is checked against a real seed
    item in a scratch copy of state/, not against a mock."""

    def setUp(self):
        self.applier = apply_mod.Applier(ROOT, dry_run=True)

    def test_human_authority_fields_are_proposed_not_written(self):
        for field, value in (("impact", 5), ("cost_usd", 35), ("gate", "bench"),
                             ("unblocks", ["GB-005"]), ("effort_minutes", 10)):
            applier = apply_mod.Applier(ROOT, dry_run=True)
            applier.set_field("EL-002", field, value)
            self.assertEqual(applier.applied, [],
                             "%s was written, not proposed" % field)
            self.assertEqual(len(applier.proposed), 1)
            self.assertEqual(applier.proposed[0][1], field)

    def test_parked_and_dropped_are_human_authority(self):
        for status in ("parked", "dropped"):
            applier = apply_mod.Applier(ROOT, dry_run=True)
            applier.set_status("GB-008", status)
            self.assertEqual(applier.applied, [])
            self.assertTrue(applier.proposed, "%s was applied" % status)

    def test_done_without_any_evidence_is_refused(self):
        applier = apply_mod.Applier(ROOT, dry_run=True)
        target = next(n.id for n in applier.model.items.values()
                      if n.status != "done" and not n.get("evidence_found"))
        applier.set_status(target, "done")
        self.assertEqual(applier.applied, [])
        self.assertTrue(any("REFUSED status=done" in why
                            for _, why in applier.refused))

    def test_done_on_evidence_discovered_in_the_same_breath_is_refused(self):
        """Without the pre-run snapshot, "no done without evidence" degrades
        into "no done without a path match" — which is precisely the inference
        the audit refuses to make."""
        applier = apply_mod.Applier(ROOT, dry_run=True)
        target = next(n.id for n in applier.model.items.values()
                      if n.status != "done" and not n.get("evidence_found"))
        applier.add_evidence(target, ["deadbee"])
        applier.set_status(target, "done")
        self.assertTrue(any("REFUSED status=done" in why
                            for _, why in applier.refused),
                        "closed on evidence found moments earlier")
        self.assertTrue(any("unread" in why for _, why in applier.refused))

    def test_agent_authority_still_works(self):
        """A guard that refuses everything is not a guard."""
        applier = apply_mod.Applier(ROOT, dry_run=True)
        applier.set_field("EL-002", "cognitive_load", "low")
        self.assertTrue(applier.applied)
        self.assertEqual(applier.proposed, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
