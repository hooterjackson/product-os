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

import glob
import json
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
        with open(os.path.join(ROOT, "tools", "audit.py"), encoding="utf-8") as fh:
            source = fh.read()
        self.assertIn("too broad to attribute anything", source)

    def test_group_d_is_built_from_reported_shas_not_from_claims(self):
        """The fix: a commit leaves group D only when a FINDING named it."""
        with open(os.path.join(ROOT, "tools", "audit.py"), encoding="utf-8") as fh:
            source = fh.read()
        self.assertIn("for sha in f.shas", source)
        self.assertIn("if c[0] not in reported", source)
        self.assertNotIn("if c[0] not in repo.claimed", source,
                         "group D is back to trusting the attribution scan")


class UnsatisfiableRulesAreNotSilence(unittest.TestCase):
    """`EL-001`'s evidence rule named only `docs/bom-checklist.md`, a checklist
    whose state "persists in your browser". Ticking it writes nothing to the
    repo, so the rule could never fire and the item could never close — while
    ranked #1 in the portfolio, with its parts photographed on the bench.

    The tool committed this even though CLAUDE.md already carried the rule,
    because "this glob matched nothing" and "this item is not done" were the
    same code path. A rule in the contract is not a rule in the machinery."""

    def test_the_three_verdicts_are_distinct(self):
        self.assertEqual(len({audit.SATISFIABLE, audit.NEVER_FIRED,
                              audit.UNSATISFIABLE}), 3)

    def test_a_path_absent_from_the_tree_is_unsatisfiable(self):
        repo = audit.Repo("fake", {"owner": "x"})
        repo.mode = "api"
        repo.tree = ["docs/04a-wire-the-zones.md", "docs/bom-checklist.md"]
        repo.files = {"aaaaaaa": ["docs/04a-wire-the-zones.md"]}
        self.assertEqual(audit.classify_rule(repo, "partitions*"),
                         audit.UNSATISFIABLE)
        self.assertEqual(audit.classify_rule(repo, "docs/*DECISION*"),
                         audit.UNSATISFIABLE)

    def test_a_real_but_untouched_path_is_never_fired_not_satisfiable(self):
        """The EL-001 shape: the file exists and is committed, but nothing a
        completion does would change it."""
        repo = audit.Repo("fake", {"owner": "x"})
        repo.mode = "api"
        repo.tree = ["docs/04a-wire-the-zones.md", "docs/bom-checklist.md"]
        repo.files = {"aaaaaaa": ["docs/04a-wire-the-zones.md"]}
        self.assertEqual(audit.classify_rule(repo, "docs/bom-checklist.md"),
                         audit.NEVER_FIRED)
        self.assertEqual(audit.classify_rule(repo, "docs/04a-wire-the-zones.md"),
                         audit.SATISFIABLE)

    def test_an_empty_commit_set_still_classifies(self):
        """A repo that produced no commits is a FACT to classify, not missing
        data. `if repo.files:` on an empty dict silently skipped this."""
        repo = audit.Repo("fake", {"owner": "x"})
        repo.mode = "api"
        repo.tree = ["CHANGELOG.md"]
        repo.files = {}
        self.assertEqual(audit.classify_rule(repo, "CHANGELOG.md"),
                         audit.NEVER_FIRED)

    def test_an_unreadable_tree_returns_none_rather_than_guessing(self):
        repo = audit.Repo("fake", {"owner": "x"})
        repo.mode = "api"
        repo.tree = []
        self.assertIsNone(audit.classify_rule(repo, "anything"))

    def test_the_finding_says_cannot_fire_not_merely_nothing_happened(self):
        with open(os.path.join(ROOT, "tools", "audit.py"), encoding="utf-8") as fh:
            source = fh.read()
        self.assertIn("cannot fire", source)
        self.assertIn("no path in %s matches", source)


class AuthorityGuardFiresAtTheAgentNotTheOwner(unittest.TestCase):
    """The guard exists to stop the AGENT silently reprioritising. It was
    briefly stopping the owner from deciding his own project:

        $ apply.py --field EL-001=cost_usd:486 --said "the tape is the Valent X"
        proposed  EL-001  cost_usd — human-authority. Proposed, not written.

    He stated a fact about his own build and the tool filed a proposal for him
    to approve later. Two guards had been conflated — one about *who decided*,
    one about *whether it is provable* — and only the first may yield to him."""

    def live_item_without_evidence(self, applier):
        return next(n.id for n in applier.model.items.values()
                    if n.status != "done" and not n.get("evidence_found"))

    def test_human_stated_decided_field_applies(self):
        applier = apply_mod.Applier(ROOT, dry_run=True)
        applier.set_field("EL-001", "cost_usd", 486, origin=apply_mod.HUMAN)
        self.assertEqual(applier.proposed, [], "his own decision was queued for him")
        self.assertEqual(len(applier.applied), 1)
        item_id, what, origin = applier.applied[0]
        self.assertEqual((item_id, origin), ("EL-001", apply_mod.HUMAN))
        self.assertIn("cost_usd", what)

    def test_agent_inferred_decided_field_still_proposes(self):
        applier = apply_mod.Applier(ROOT, dry_run=True)
        applier.set_field("EL-001", "cost_usd", 486, origin=apply_mod.AGENT)
        self.assertEqual(applier.applied, [], "agent wrote a decided field")
        self.assertEqual(len(applier.proposed), 1)
        self.assertEqual(applier.proposed[0][1], "cost_usd")

    def test_agent_is_the_default_origin(self):
        """Forgetting to say who decided must fail SAFE, toward proposing."""
        applier = apply_mod.Applier(ROOT, dry_run=True)
        applier.set_field("EL-001", "impact", 5)
        self.assertEqual(applier.applied, [])
        self.assertTrue(applier.proposed)

    def test_done_without_evidence_is_refused_even_when_he_says_it(self):
        """TRUTH guard, not an authority guard. He cannot make an unevidenced
        completion evidenced by asserting it."""
        applier = apply_mod.Applier(ROOT, dry_run=True)
        target = self.live_item_without_evidence(applier)
        applier.set_status(target, "done", origin=apply_mod.HUMAN)
        self.assertEqual(applier.applied, [], "his word overrode a truth guard")
        self.assertTrue(any("REFUSED status=done" in why
                            for _, why in applier.refused))

    def test_he_can_park_but_the_agent_cannot(self):
        for origin, applies in ((apply_mod.HUMAN, True), (apply_mod.AGENT, False)):
            applier = apply_mod.Applier(ROOT, dry_run=True)
            applier.set_status("GB-008", "parked", origin=origin)
            self.assertEqual(bool(applier.applied), applies,
                             "parked/%s behaved wrongly" % origin)

    def test_agent_authority_field_applies_unremarked_at_either_origin(self):
        for origin in (apply_mod.AGENT, apply_mod.HUMAN):
            applier = apply_mod.Applier(ROOT, dry_run=True)
            applier.set_field("EL-002", "cognitive_load", "low", origin=origin)
            self.assertEqual(applier.proposed, [])
            self.assertEqual(len(applier.applied), 1)

    def test_decided_requires_his_words_on_the_record(self):
        """--decided asserts he said something. Without --said the assertion is
        unattributed, and an unattributed human decision is indistinguishable
        from an agent writing whatever it likes."""
        proc = subprocess.run(
            [sys.executable, os.path.join(ROOT, "tools", "apply.py"),
             "--dry-run", "--decided", "EL-001=cost_usd:486"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(proc.returncode, 2)
        self.assertIn(b"--said", proc.stderr)

    def test_origin_is_recorded_in_the_audit_entry(self):
        applier = apply_mod.Applier(ROOT, dry_run=True)
        applier.set_field("EL-001", "cost_usd", 486, origin=apply_mod.HUMAN)
        _path, text = applier.record("the tape is the Valent X", None, None)
        self.assertIn("on his word", text)


class CoverageNumbersMustNotSilentlyCap(unittest.TestCase):
    """Group D — the number that says "I recognised nothing here" — was
    silently truncated at the API's 100-commit page. gimbal-bench had 245
    commits in the window and the audit reported exactly 100 as the answer.
    Two different figures (108 and 156) were quoted on the same day, both
    truncated, neither labelled with its window. A capped coverage number is
    worse than none, because it looks precise."""

    def test_pagination_exists(self):
        with open(os.path.join(ROOT, "tools", "audit.py"), encoding="utf-8") as fh:
            source = fh.read()
        self.assertIn("page=%d", source, "commit query is not paginated")
        self.assertIn("if len(data) < 100:", source,
                      "no short-page stop condition, so it cannot know it is done")

    def test_a_page_cap_is_declared_and_reported(self):
        self.assertGreaterEqual(audit.MAX_COMMIT_PAGES, 10)
        with open(os.path.join(ROOT, "tools", "audit.py"), encoding="utf-8") as fh:
            source = fh.read()
        self.assertIn("truncated", source)
        self.assertIn("FLOOR", source, "truncation must be announced, not implied")

    def test_group_d_heading_carries_its_window(self):
        """A coverage figure without its window drifts between reports."""
        with open(os.path.join(ROOT, "tools", "audit.py"), encoding="utf-8") as fh:
            source = fh.read()
        self.assertIn('(%d since %s)', source)


class ThreadIndexIsMetadataOnly(unittest.TestCase):
    """The shard is derived from 405 GiB of unredacted working conversation and
    this repo may go public. Two independent gates, and the CI one must not
    share a constant with the writer."""

    def test_the_two_allowlists_are_independent_copies(self):
        import index as index_mod
        import validate as validate_mod
        self.assertEqual(index_mod.THREAD_KEYS, validate_mod.SHARD_THREAD_KEYS)
        with open(os.path.join(ROOT, "tools", "validate.py"), encoding="utf-8") as fh:
            source = fh.read()
        self.assertNotIn("import index", source,
                         "validate.py must not import the tool it is checking")

    def test_forbidden_keys_are_rejected_by_both(self):
        import index as index_mod
        import validate as validate_mod
        for key in ("message", "content", "text", "body", "Summary", "excerpt"):
            self.assertNotIn(key, index_mod.THREAD_KEYS)
            self.assertTrue(validate_mod.FORBIDDEN_SHARD_KEY.search(key),
                            "%r would pass the CI gate" % key)

    def test_clean_drops_anything_off_the_allowlist(self):
        import index as index_mod
        out = index_mod.clean({"id": "x", "tool": "codex",
                               "message": "secret", "content": "secret"})
        self.assertEqual(set(out), {"id", "tool"})

    def test_paths_are_relativised_to_home(self):
        import index as index_mod
        self.assertTrue(index_mod.tilde(os.path.expanduser("~/x")).startswith("~/"))

    def test_written_shard_carries_only_allowlisted_keys(self):
        path = os.path.join(ROOT, "state", "threads", "by-machine")
        shards = glob.glob(os.path.join(path, "*.json"))
        if not shards:
            self.skipTest("no shard written yet")
        import validate as validate_mod
        for shard_path in shards:
            with open(shard_path, encoding="utf-8") as fh:
                shard = json.load(fh)
            for thread in shard.get("threads") or []:
                extra = set(thread) - validate_mod.SHARD_THREAD_KEYS
                self.assertEqual(extra, set(), "%s leaked %s" % (shard_path, extra))


class ItemIdsAreUniqueOnlyWithinASeedGeneration(unittest.TestCase):
    """A transcript from 2026-08-15 cited `Q-004` beside `EL-040` and `EL-042`,
    IDs from a seed that was later discarded. Today's `Q-004` is an unrelated
    question. The indexer bound them, confidently and wrongly — a conversation
    cannot cite an item that did not exist when it happened."""

    def test_a_citation_predating_the_item_is_not_bound(self):
        import index as index_mod
        thread = {"last_active": "2026-08-15T10:00:00Z", "items": {"Q-004"}}
        kept, stale = index_mod.gate_by_age(thread, {"Q-004": "2026-08-19"})
        self.assertEqual(kept, set())
        self.assertEqual(stale, {"Q-004"})

    def test_a_citation_after_the_item_exists_is_bound(self):
        import index as index_mod
        thread = {"last_active": "2026-08-19T22:00:00Z", "items": {"POS-001"}}
        kept, stale = index_mod.gate_by_age(thread, {"POS-001": "2026-08-19"})
        self.assertEqual(kept, {"POS-001"})
        self.assertEqual(stale, set())

    def test_a_collision_is_reported_not_dropped_silently(self):
        with open(os.path.join(ROOT, "tools", "index.py"), encoding="utf-8") as fh:
            source = fh.read()
        self.assertIn("generation_collisions", source)


class QuestionsAreNotItems(unittest.TestCase):
    """apply.py wrote every entity with kind="item". `_fm` orders a question's
    keys differently, so parking Q-005 produced a valid file that failed the
    canonical check -- a corruption introduced by the tool whose job is to keep
    state consistent."""

    def test_kind_is_resolved_per_entity(self):
        applier = apply_mod.Applier(ROOT, dry_run=True)
        self.assertEqual(applier.kind_of("Q-001"), "question")
        self.assertEqual(applier.kind_of("GB-001"), "item")

    def test_no_hardcoded_item_kind_remains(self):
        with open(os.path.join(ROOT, "tools", "apply.py"), encoding="utf-8") as fh:
            source = fh.read()
        self.assertNotIn('body, "item")', source,
                         "a write still hardcodes kind=item")

    def test_every_question_file_is_canonical(self):
        import _fm as fm_mod
        for path in glob.glob(os.path.join(ROOT, "state", "questions", "*.md")):
            with open(path, encoding="utf-8") as fh:
                original = fh.read()
            self.assertEqual(fm_mod.canonicalize(original, "question", path),
                             original, "%s is not canonical" % path)


class BriefsAlwaysCarryFreshness(unittest.TestCase):
    """A brief without a freshness stamp reads as current. That is the same
    shape as PROJECT-STATE.md listing two prompts as pending that had already
    shipped -- so the stamp prints even when the answer is "I don't know"."""

    def test_stamp_has_an_honest_form_when_no_audit_has_run(self):
        import brief as brief_mod
        node = type("N", (), {"get": lambda self, k, d=None: None})()
        line = brief_mod.freshness(ROOT, node, None, {})
        self.assertIn("no audit has ever run", line)

    def test_unreachable_repos_are_named_not_assumed_unchanged(self):
        import brief as brief_mod
        node = type("N", (), {"get": lambda self, k, d=None:
                              ["gimbal-bench"] if k == "repos" else None})()
        line = brief_mod.freshness(ROOT, node, {"date": "2026-08-19",
                                                "heads": {}}, {})
        self.assertIn("could not check", line)

    def test_every_generated_brief_has_a_stamp(self):
        briefs = glob.glob(os.path.join(ROOT, "build", "briefs", "*.md"))
        if not briefs:
            self.skipTest("no briefs built yet")
        for path in briefs:
            with open(path, encoding="utf-8") as fh:
                self.assertIn("**Freshness:**", fh.read(),
                              "%s has no freshness stamp" % path)


class ResumeCommandsAreVerifiedBeforePrinting(unittest.TestCase):
    """A resume command that fails is worse than a sentence that works. The
    codex binary is not on PATH -- it lives inside ChatGPT.app -- so a bare
    `codex resume` would have been printed and would not have run."""

    def test_no_command_is_emitted_for_a_restart(self):
        import json as json_mod
        shard = os.path.join(ROOT, "state", "threads", "by-machine")
        for path in glob.glob(os.path.join(shard, "*.json")):
            with open(path, encoding="utf-8") as fh:
                data = json_mod.load(fh)
            for thread in data.get("threads") or []:
                if thread.get("verdict") == "restart":
                    self.assertIsNone(thread.get("command"),
                                      "a restart carries a resume command")

    def test_every_thread_carries_a_verdict_and_a_reason(self):
        import json as json_mod
        shard = os.path.join(ROOT, "state", "threads", "by-machine")
        files = glob.glob(os.path.join(shard, "*.json"))
        if not files:
            self.skipTest("no shard")
        for path in files:
            with open(path, encoding="utf-8") as fh:
                data = json_mod.load(fh)
            for thread in data.get("threads") or []:
                self.assertIn(thread.get("verdict"), ("resume", "restart"))
                self.assertTrue(thread.get("verdict_reason"))

    def test_codex_is_addressed_by_full_path_since_it_is_not_on_path(self):
        import index as index_mod
        self.assertTrue(index_mod.CODEX_BIN.startswith("/"),
                        "codex must be a full path; it is not on PATH")


class LeadTimeNoLongerMovesTheOrder(unittest.TestCase):
    """Measured before removal: 2 of 30 items carried any lead_time_days and
    both were purchases. The term was inert on 28 items and tripled the score
    on the two that no longer matter."""

    def test_score_ignores_lead_time(self):
        import _model as model_mod
        model = model_mod.Model.load(ROOT)
        node = next(iter(model.items.values()))
        before = model.score(node)
        original = node.fm.get("lead_time_days")
        node.fm["lead_time_days"] = 999
        try:
            self.assertEqual(model.score(node), before,
                             "lead_time_days still moves the score")
        finally:
            node.fm["lead_time_days"] = original

    def test_urgency_is_gone(self):
        import _model as model_mod
        self.assertFalse(hasattr(model_mod, "urgency"))
        self.assertFalse(hasattr(model_mod, "LEAD_DIVISOR"))


class TheDoneGuardIsASpeedBumpNotAWall(unittest.TestCase):
    """Closing POS-003 walked through the guard in two commands: write
    evidence_found (agent authority), then close. "Before the run" is a process
    boundary, not readership. The guard still stops the common case; what it
    cannot stop is the actor that authors both sides. The durable guarantee is
    the origin stamp, so that must never be droppable."""

    def test_the_limitation_is_recorded_where_it_will_be_read(self):
        with open(os.path.join(ROOT, "wiki", "ruled-out.md"), encoding="utf-8") as fh:
            register = fh.read()
        self.assertIn("R-059", register)
        self.assertIn("process boundary, not readership", register)

    def test_an_inferred_close_is_stamped_as_inferred(self):
        applier = apply_mod.Applier(ROOT, dry_run=True)
        target = next((n.id for n in applier.model.items.values()
                       if n.get("evidence_found") and n.status != "done"), None)
        if target is None:
            self.skipTest("no item with prior evidence still open")
        applier.set_status(target, "done", origin=apply_mod.AGENT)
        self.assertTrue(applier.applied)
        self.assertEqual(applier.applied[0][2], apply_mod.AGENT)

    def test_the_record_distinguishes_his_word_from_inference(self):
        applier = apply_mod.Applier(ROOT, dry_run=True)
        applier.set_field("EL-002", "cognitive_load", "low",
                          origin=apply_mod.AGENT)
        _p, text = applier.record("x", None, None)
        self.assertIn("_(inferred)_", text)


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
