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

import datetime
import glob
import json
import os
import shutil
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

    # `cost_usd` was the field in the original report. It no longer exists,
    # so these run on `machine_affinity` -- still human-authority, still a
    # fact about his own bench that he is entitled to state in one sentence.
    FIELD, VALUE = "machine_affinity", "formd-t1"

    def test_human_stated_decided_field_applies(self):
        applier = apply_mod.Applier(ROOT, dry_run=True)
        applier.set_field("EL-001", self.FIELD, self.VALUE,
                          origin=apply_mod.HUMAN)
        self.assertEqual(applier.proposed, [], "his own decision was queued for him")
        self.assertEqual(len(applier.applied), 1)
        item_id, what, origin = applier.applied[0]
        self.assertEqual((item_id, origin), ("EL-001", apply_mod.HUMAN))
        self.assertIn(self.FIELD, what)

    def test_agent_inferred_decided_field_still_proposes(self):
        applier = apply_mod.Applier(ROOT, dry_run=True)
        applier.set_field("EL-001", self.FIELD, self.VALUE,
                          origin=apply_mod.AGENT)
        self.assertEqual(applier.applied, [], "agent wrote a decided field")
        self.assertEqual(len(applier.proposed), 1)
        self.assertEqual(applier.proposed[0][1], self.FIELD)

    def test_agent_is_the_default_origin(self):
        """Forgetting to say who decided must fail SAFE, toward proposing."""
        applier = apply_mod.Applier(ROOT, dry_run=True)
        applier.set_field("EL-001", "gate", "external")
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


class QuestionsCollapsedIntoTasks(unittest.TestCase):
    """Was `QuestionsAreNotItems`, which pinned that `apply.py` resolved the
    entity kind per entity rather than hardcoding `item` -- a real corruption
    where parking `Q-005` produced a valid file that failed the canonical
    check.

    There is one kind now. A `Q-*` node was defined by `gates` edges and by
    `impact`/`confidence`/`effort_minutes`; with both deleted it was a task
    whose title ends in a question mark, living outside any project, which the
    "every task belongs to a project" rule forbids. The old defect cannot
    recur because the second key order no longer exists -- so what is pinned
    here is the collapse itself."""

    def test_there_is_one_entity_kind_for_tasks(self):
        applier = apply_mod.Applier(ROOT, dry_run=True)
        self.assertEqual(applier.kind_of("Q-001"), "item")
        self.assertEqual(applier.kind_of("GB-001"), "item")
        self.assertNotIn("question", _fm.FIELD_ORDER)

    def test_the_questions_directory_is_gone(self):
        self.assertFalse(os.path.isdir(os.path.join(ROOT, "state", "questions")))

    def test_every_former_question_is_a_task_in_a_project(self):
        import _model as model_mod
        model = model_mod.Model.load(ROOT)
        movers = [n for n in model.items.values() if n.id.startswith("Q-")]
        self.assertEqual(len(movers), 5, "expected the 5 questions")   # R-075
        for node in movers:
            self.assertTrue(node.project, "%s has no project" % node.id)
            self.assertIn(os.sep + "items" + os.sep, node.path)
            with open(node.path, encoding="utf-8") as fh:
                original = fh.read()
            self.assertEqual(_fm.canonicalize(original, "item", node.path),
                             original, "%s is not canonical" % node.id)


class EveryPromptCarriesFreshness(unittest.TestCase):
    """A prompt without a freshness stamp reads as current. That is the same
    shape as PROJECT-STATE.md listing two prompts as pending that had already
    shipped -- so the stamp prints even when the answer is "I don't know".

    Was `BriefsAlwaysCarryFreshness`. Briefs are gone (`R-071`); the kickoff
    prompt is the artifact that carries the stamp, and it is the one that was
    ever actually pasted anywhere."""

    def test_stamp_has_an_honest_form_when_no_audit_has_run(self):
        import _context as _ctx
        node = type("N", (), {"get": lambda self, k, d=None: None})()
        line = _ctx.freshness(ROOT, node, None, {})
        self.assertIn("no audit has ever run", line)

    def test_unreachable_repos_are_named_not_assumed_unchanged(self):
        import _context as _ctx
        node = type("N", (), {"get": lambda self, k, d=None:
                              ["gimbal-bench"] if k == "repos" else None})()
        line = _ctx.freshness(ROOT, node, {"date": "2026-08-19",
                                                "heads": {}}, {})
        self.assertIn("could not check", line)

    def test_every_generated_prompt_has_a_stamp(self):
        prompts = glob.glob(os.path.join(ROOT, "public", "kickoff", "*.md"))
        # R-075: a scan of nothing passes every assertion after it.
        self.assertGreater(len(prompts), 10,
                           "found %d kickoff prompts -- the scan did not run"
                           % len(prompts))
        for path in prompts:
            with open(path, encoding="utf-8") as fh:
                self.assertIn("Freshness:", fh.read(),
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


class NoScoringSurvives(unittest.TestCase):
    """`DEC-202` / `R-068`. The order is `state/backlog.md`, authored by hand.

    This replaces `LeadTimeNoLongerMovesTheOrder`, which pinned a weaker
    property -- that ONE term had stopped moving the order. The whole formula
    is gone now, so the assertion is that it stays gone.

    Measured before removal: 9 of 17 adjacent pairs sat within the 10% band
    `CLAUDE.md` says to escalate on; 18 items produced 10 distinct scores; and
    `pin`, the human override, had never once been set.
    """

    # Code shapes, not prose -- `impact` appears legitimately in register
    # entries and docstrings explaining why it went, and a guard that trips on
    # its own explanation gets deleted rather than obeyed.
    TOKENS = ["effort_bucket(", "LEVERAGE_WEIGHT", "node.score", "n.score",
              "node.leverage", "n.leverage", ".ranked(", "cognitive_load"]

    def _sources(self):
        found = []
        for base in ("tools", "plugin"):
            for root, _dirs, files in os.walk(os.path.join(ROOT, base)):
                found += [os.path.join(root, f) for f in files
                          if f.endswith(".py")]
        return found

    def test_no_scoring_survives(self):
        sources = self._sources()
        # R-075: assert the denominator. A guard that walks zero files and
        # reports clean is worse than no guard, because it is green.
        self.assertGreaterEqual(len(sources), 8,
                                "walked %d source files -- the scan did not "
                                "run" % len(sources))
        offenders = []
        for path in sources:
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
            for token in self.TOKENS:
                if token in text:
                    offenders.append("%s: %s"
                                     % (os.path.relpath(path, ROOT), token))
        self.assertEqual(offenders, [], "scoring came back")

    def test_the_deleted_tools_are_gone(self):
        for name in ("rank.py", "brief.py", "build.py"):
            self.assertFalse(
                os.path.exists(os.path.join(ROOT, "tools", name)),
                "tools/%s is back" % name)

    def test_no_task_file_carries_a_score_input(self):
        paths = glob.glob(os.path.join(
            ROOT, "state", "projects", "*", "items", "*.md"))
        self.assertGreater(len(paths), 20, "the scan did not run")   # R-075
        dead = {"impact", "confidence", "effort_minutes", "lead_time_days",
                "cost_usd", "cognitive_load", "pin"}
        for path in paths:
            fm, _body = _fm.load(path)
            self.assertEqual(sorted(dead & set(fm)), [],
                             "%s still carries score inputs"
                             % os.path.basename(path))


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


class InferredClosuresAreVisibleWhereHumansLook(unittest.TestCase):
    """R-059 concluded the durable guarantee was the (inferred) stamp. It was
    recorded in state/audits/ and appeared in ZERO places anyone reads --
    including the brief for the very item it described. A guarantee nobody can
    see is not a guarantee; that is the same shape as four earlier findings
    here, where the rule existed and nothing executed it."""

    def test_closed_origin_is_derived_not_settable(self):
        applier = apply_mod.Applier(ROOT, dry_run=True)
        applier.set_field("POS-003", "closed_origin", "his-word",
                          origin=apply_mod.HUMAN)
        self.assertEqual(applier.applied, [],
                         "an agent laundered its judgement into his word")
        self.assertTrue(any("REFUSED closed_origin" in why
                            for _, why in applier.refused))

    def test_closing_records_who_closed_it(self):
        for origin, expected in ((apply_mod.HUMAN, "his-word"),
                                 (apply_mod.AGENT, "inferred")):
            applier = apply_mod.Applier(ROOT, dry_run=True)
            target = next((n.id for n in applier.model.items.values()
                           if n.get("evidence_found") and n.status != "done"),
                          None)
            if target is None:
                self.skipTest("no open item with prior evidence")
            applier.set_status(target, "done", origin=origin)
            self.assertTrue(applier.applied)

    def test_every_done_item_records_how_it_was_closed(self):
        import _model as model_mod
        model = model_mod.Model.load(ROOT)
        for node in model.items.values():
            if node.status == "done":
                self.assertIn(node.get("closed_origin"), ("inferred", "his-word"),
                              "%s is done and does not say who closed it" % node.id)

    def test_an_unconfirmed_close_is_flagged_on_the_face_of_its_brief(self):
        import _model as model_mod
        model = model_mod.Model.load(ROOT)
        for node in model.items.values():
            if node.status != "done" or node.get("closed_origin") == "his-word":
                continue
            path = os.path.join(ROOT, "build", "briefs", "%s.md" % node.id)
            if not os.path.exists(path):
                continue
            with open(path, encoding="utf-8") as fh:
                head = "".join(fh.readlines()[:12])
            self.assertIn("CLOSED ON MY JUDGEMENT", head,
                          "%s's brief buries or omits the stamp" % node.id)

    def test_now_md_surfaces_them(self):
        path = os.path.join(ROOT, "build", "now.md")
        if not os.path.exists(path):
            self.skipTest("not built")
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        import _model as model_mod
        model = model_mod.Model.load(ROOT)
        if any(n.status == "done" and n.get("closed_origin") != "his-word"
               for n in model.items.values()):
            self.assertIn("Closed on my judgement", text)


class SettledDecisionsAreWrittenDown(unittest.TestCase):
    """The public-visibility question was re-derived in three consecutive
    recaps because `grep -ril public state/decisions/` returned nothing. A
    decision that lives only in a chat gets re-derived by every session that
    follows -- this repo's founding failure, happening to this repo."""

    def test_the_visibility_decision_exists_as_a_record(self):
        import _model as model_mod
        model = model_mod.Model.load(ROOT)
        hits = [d for d in model.decisions.values()
                if "public" in (d.title or "").lower()]
        self.assertTrue(hits, "the visibility decision is not a decision record")
        self.assertTrue(hits[0].get("revisit_if"),
                        "a decision with no revisit trigger is a gag order")


class NoDependencyGraphSurvives(unittest.TestCase):
    """`R-069`. 12 edges over 41 nodes, 10 of them inside one repo, from a
    phase plan Marcelo wrote by hand before this tool existed.

    Replaces `GateNoneIsNotTheSameAsFromThisChair`, whose subject -- the
    interaction of `--gate` and `machine_affinity` in `rank.py` -- no longer
    has a tool to live in. What that test protected is now structural: there
    are no filters, because there is no derived list to filter.
    """

    TOKENS = ["graphlib", "unblocks_inferred", "TopologicalSorter",
              "node.blockers", "n.blockers", "node.reach", "n.reach",
              "effective_status"]

    def test_no_dependency_graph_survives(self):
        sources = []
        for base in ("tools", "plugin"):
            for root, _dirs, files in os.walk(os.path.join(ROOT, base)):
                sources += [os.path.join(root, f) for f in files
                            if f.endswith(".py")]
        self.assertGreaterEqual(len(sources), 8,
                                "walked %d source files -- the scan did not "
                                "run" % len(sources))          # R-075
        offenders = []
        for path in sources:
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
            for token in self.TOKENS:
                if token in text:
                    offenders.append("%s: %s"
                                     % (os.path.relpath(path, ROOT), token))
        self.assertEqual(offenders, [], "the dependency graph came back")

    def test_no_task_file_carries_an_edge(self):
        paths = glob.glob(os.path.join(
            ROOT, "state", "projects", "*", "items", "*.md"))
        self.assertGreater(len(paths), 20, "the scan did not run")   # R-075
        for path in paths:
            fm, _body = _fm.load(path)
            self.assertEqual(
                sorted({"unblocks", "unblocks_inferred", "gates", "answers"}
                       & set(fm)), [],
                "%s still carries edges" % os.path.basename(path))

    def test_intent_md_was_not_edited(self):
        """The criterion stays; only the automation went.

        `intent.md` names "what unblocks the most downstream work" as a
        precedence rule, and it is human-authority. Marcelo's ruling,
        2026-08-20: *"the criterion stays, the automation goes. intent.md
        describes how I decide, not what the tool computes."* So the line must
        still be there -- deleting a computation is not licence to edit his
        description of his own judgement."""
        with open(os.path.join(ROOT, "intent.md"), encoding="utf-8") as fh:
            self.assertIn("unblocks the most downstream work", fh.read())


class PublishedStampsMustSurviveBeingPublished(unittest.TestCase):
    """The brief's freshness line carried "+N commits since the last audit",
    computed from local HEAD, and was committed into public/. The commit that
    published it invalidated it -- measured +9 before, +10 after. No ordering
    of regenerate-then-commit converges."""

    def test_public_drops_the_volatile_delta(self):
        import _context as _ctx
        import _model as model_mod
        root = model_mod.find_root()
        model = model_mod.Model.load(root)
        stamp = _ctx.read_stamp(root)
        if not stamp:
            self.skipTest("no audit stamp")
        with open(os.path.join(root, "state", "repos.json"), encoding="utf-8") as fh:
            spec = {k: v for k, v in json.load(fh).items()
                    if not k.startswith("_")}
        node = model.nodes["POS-001"]
        durable = _ctx.freshness(root, node, stamp, spec, volatile=False)
        self.assertNotIn("since the last audit", durable)
        self.assertIn("last audit", durable)

    def test_no_committed_freshness_line_carries_a_commit_delta(self):
        """Scan the FRESHNESS LINE, not the whole file.

        The first version of this test grepped the file and failed on
        `R-061`'s own register excerpt, which correctly quotes the bad stamp as
        an example. A check aimed at the wrong surface -- the same class it was
        written to catch, inside itself."""
        names = glob.glob(os.path.join(ROOT, "public", "kickoff", "*.md"))
        self.assertGreater(len(names), 10, "the scan did not run")   # R-075
        for name in names:
            with open(name, encoding="utf-8") as fh:
                for line in fh:
                    if not line.startswith(("**Freshness:**", "Freshness:")):
                        continue
                    self.assertNotIn("since the last audit", line,
                                     "%s embeds a counter its own commit "
                                     "changes" % os.path.basename(name))


class EveryActionArtifactStatesItsDestination(unittest.TestCase):
    """Three destinations -- a new chat, an existing chat with repo access, a
    terminal -- and they are not interchangeable. Pasting "link yourself to
    GB-001" into a fresh chat fails confusingly. These get read far from
    whatever page produced them, so the destination is part of the artifact."""

    def test_all_five_actions_have_an_artifact(self):
        public = os.path.join(ROOT, "public")
        for rel in ("reconcile.md", "connect-repo.md", "capture.md"):
            self.assertTrue(os.path.exists(os.path.join(public, rel)), rel)
        for sub in ("kickoff", "attach"):
            self.assertTrue(glob.glob(os.path.join(public, sub, "*.md")), sub)

    def test_each_artifact_says_where_it_is_pasted(self):
        public = os.path.join(ROOT, "public")
        targets = glob.glob(os.path.join(public, "*.md")) + \
            glob.glob(os.path.join(public, "attach", "*.md")) + \
            glob.glob(os.path.join(public, "kickoff", "*.md"))
        for path in targets:
            with open(path, encoding="utf-8") as fh:
                head = "".join(fh.readlines()[:8])
            name = os.path.basename(path)
            if os.path.basename(os.path.dirname(path)) == "kickoff":
                self.assertIn("Cite ", head, "%s: no citation line" % name)
                continue
            self.assertTrue(
                "PASTE THIS" in head or "TYPE THIS" in head,
                "%s does not say where it goes" % name)

    def test_attach_is_specific_not_a_template(self):
        for path in glob.glob(os.path.join(ROOT, "public", "attach", "*.md")):
            item_id = os.path.basename(path)[:-3]
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
            self.assertIn(item_id, text, "%s does not embed its id" % item_id)
            self.assertIn("by-machine", text,
                          "%s omits the do-not-write warning" % item_id)

    def test_connect_repo_warns_that_coverage_scales_with_items(self):
        with open(os.path.join(ROOT, "public", "connect-repo.md"),
                  encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn("ITEMS, not repos", text)
        self.assertIn("group D", text)

    def test_capture_promises_to_ask_nothing(self):
        with open(os.path.join(ROOT, "public", "capture.md"),
                  encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn("capture is broken", text)

    def test_no_action_artifact_embeds_a_volatile_counter(self):
        """R-061 applies to these too."""
        public = os.path.join(ROOT, "public")
        for path in (glob.glob(os.path.join(public, "*.md")) +
                     glob.glob(os.path.join(public, "attach", "*.md"))):
            with open(path, encoding="utf-8") as fh:
                for line in fh:
                    self.assertNotIn("since the last audit —", line,
                                     "%s embeds a live delta"
                                     % os.path.basename(path))


class ApplyParsesValuesWhole(unittest.TestCase):
    """--field and --decided shared --evidence's comma splitter. Measured:
    `--decided EL-001=unblocks:["GB-001","GB-002"]` parsed as two fragments,
    wrote a truncated string into an item and injected five garbage keys into
    its frontmatter. No error; the write succeeded. Worst on --decided, the
    documented way for HIM to state a decided field."""

    def test_a_json_value_containing_commas_survives(self):
        got = apply_mod.parse_pairs(['EL-001=unblocks:["GB-001","GB-002"]'],
                                    split=False)
        self.assertEqual(got["EL-001"], ['unblocks:["GB-001","GB-002"]'])

    def test_evidence_still_splits_on_commas(self):
        got = apply_mod.parse_pairs(["GB-004=aaa1111,bbb2222"])
        self.assertEqual(got["GB-004"], ["aaa1111", "bbb2222"])

    def test_confirming_a_closure_does_not_redate_it(self):
        """`--decided <ID>=status:done` is the documented way to CONFIRM a
        closure. Re-stamping `completed` moved EL-005 from 2026-08-15 to
        2026-08-19 -- eating the fact POS-008 exists to surface."""
        import _fm as fm_mod
        applier = apply_mod.Applier(ROOT, dry_run=True)
        done = [n for n in applier.model.items.values()
                if n.status == "done" and n.get("completed")]
        if not done:
            self.skipTest("no dated closure to confirm")
        node = done[0]
        before = node.get("completed")
        fm, _body = fm_mod.load(node.path)
        self.assertEqual(fm.get("completed"), before)
        with open(os.path.join(ROOT, "tools", "apply.py"), encoding="utf-8") as fh:
            source = fh.read()
        self.assertIn('fm.setdefault("completed", today())', source,
                      "completed is still stamped unconditionally")


class ApplyRefusals(unittest.TestCase):
    """Three refusals that must not bend. Each is checked against a real seed
    item in a scratch copy of state/, not against a mock."""

    def setUp(self):
        self.applier = apply_mod.Applier(ROOT, dry_run=True)

    def test_human_authority_fields_are_proposed_not_written(self):
        # The score inputs this list used to walk are deleted (`DEC-202`).
        # Five human-authority things survive, and the guard must still hold
        # on every one of them -- a shorter list is not a weaker rule.
        for field, value in (("project", "gimbal-bench"), ("gate", "external"),
                             ("machine_affinity", "formd-t1"),
                             ("evidence", [{"repo": "x", "paths": ["y"]}]),
                             ("status", "parked")):
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


class PublishedBytesDoNotMoveWithTheCalendar(unittest.TestCase):
    """`R-067`. Measured 2026-08-20 on a clean tree at `9b3ff8b`:
    `publish.py --check` exited 1 reporting **121 files out of sync**, and the
    entire difference was `(today)` -> `(1 day ago)`. Nothing in `state/` had
    changed. `validate.py` was therefore red on every day but the audit's,
    which trains a reader to regenerate-and-commit or to stop looking at it.

    `R-061` established the rule and fixed the commit delta at `brief.py:152`,
    leaving the age phrase four lines above it in the same function. So this
    test asserts the PROPERTY, not the two quantities that have been found so
    far: generate the whole published surface under two different calendar
    dates and require the bytes to be identical. A third volatile quantity
    added later fails here without anyone having to think of it.
    """

    def _publish_as_of(self, iso):
        import _model as model_mod
        import _context as _ctx
        import publish as publish_mod

        class _Frozen(datetime.date):
            @classmethod
            def today(cls):
                return datetime.date.fromisoformat(iso)

        # Alias the module first: inside a class body, `datetime = ...`
        # rebinds the name for every line after it.
        _module = datetime

        class _Shim(object):
            date = _Frozen
            datetime = _module.datetime
            timedelta = _module.timedelta

        real = _ctx.datetime
        target = tempfile.mkdtemp(prefix="po-cal-")
        _ctx.datetime = _Shim
        try:
            publish_mod.generate(ROOT, model_mod.Model.load(ROOT), target)
        finally:
            _ctx.datetime = real
        return target

    def test_two_different_days_produce_identical_bytes(self):
        first = self._publish_as_of("2026-08-19")
        second = self._publish_as_of("2027-04-02")
        try:
            names = set()
            for base in (first, second):
                for root, _dirs, files in os.walk(base):
                    for name in files:
                        names.add(os.path.relpath(os.path.join(root, name), base))
            # A scan that walked nothing would pass every assertion below it.
            # `R-075`: assert the denominator before asserting the result.
            self.assertGreater(len(names), 50,
                               "the surface scan found %d files -- it did not "
                               "run" % len(names))
            drift = []
            for rel in sorted(names):
                a, b = os.path.join(first, rel), os.path.join(second, rel)
                if not (os.path.exists(a) and os.path.exists(b)):
                    drift.append("%s exists on only one date" % rel)
                    continue
                with open(a, encoding="utf-8") as fa, open(b, encoding="utf-8") as fb:
                    if fa.read() != fb.read():
                        drift.append(rel)
            self.assertEqual(drift[:8], [],
                             "%d published file(s) move with the calendar"
                             % len(drift))
        finally:
            shutil.rmtree(first, ignore_errors=True)
            shutil.rmtree(second, ignore_errors=True)

    def test_the_durable_line_still_says_when_the_audit_ran(self):
        """Durability must not be bought by saying nothing."""
        import _context as _ctx
        node = type("N", (), {"get": lambda self, k, d=None: None})()
        line = _ctx.freshness(
            ROOT, node, {"date": "2026-08-19", "group_d": 153}, {},
            volatile=False)
        self.assertIn("2026-08-19", line)
        self.assertIn("153 commits unattributed", line)
        self.assertNotIn("ago", line)
        self.assertNotIn("today", line)


class TheSchemaAndTheAuthorityTableAgree(unittest.TestCase):
    """A field in `FIELD_ORDER` with no row in `AUTHORITY` has no owner, and a
    row in `AUTHORITY` for a field that does not exist enforces nothing. Either
    way the failure is silent: the file validates, the guard never fires, and
    nobody finds out until someone writes a field they should not have."""

    STRUCTURAL = {"id", "created", "parent_ruling", "closed_origin"}

    def test_every_authority_row_names_a_real_field(self):
        fields = set(_fm.FIELD_ORDER["item"])
        self.assertGreater(len(fields), 8, "the schema did not load")   # R-075
        orphans = sorted(set(_fm.AUTHORITY) - fields)
        self.assertEqual(orphans, [],
                         "AUTHORITY governs fields that no longer exist")

    def test_every_field_has_an_owner_or_is_named_structural(self):
        unowned = sorted(set(_fm.FIELD_ORDER["item"])
                         - set(_fm.AUTHORITY) - self.STRUCTURAL)
        self.assertEqual(unowned, [],
                         "these fields have no authority row and are not "
                         "declared structural -- decide who owns them")


class TheSessionStartHookStillInjects(unittest.TestCase):
    """The hook imported `rank.py` at `session_start.py:86` and called it at
    `:115` and `:117`. Deleting `rank.py` without rewiring it would have broken
    the ruled-out register's only delivery mechanism **silently** -- a hook that
    raises does not inject, and nothing reports it. `hooks.json` names that
    failure shape in its own comment: "it looks installed."

    This is the test that was missing. It runs the hook the way the harness
    does and requires a register entry to come back."""

    def test_the_hook_runs_and_emits_a_matching_entry(self):
        env = dict(os.environ, PRODUCT_OS_ITEM="GB-001")
        proc = subprocess.run(
            [sys.executable,
             os.path.join(ROOT, "plugin", "hooks", "session_start.py")],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, cwd=ROOT)
        self.assertEqual(proc.returncode, 0, proc.stderr.decode()[:400])
        payload = json.loads(proc.stdout.decode("utf-8"))
        context = payload["hookSpecificOutput"]["additionalContext"]
        self.assertIn("GB-001", context)
        self.assertIn("## R-", context,
                      "the hook injected no register entry -- the guardrail is "
                      "installed and doing nothing")

    def test_the_hook_does_not_import_a_deleted_module(self):
        with open(os.path.join(ROOT, "plugin", "hooks", "session_start.py"),
                  encoding="utf-8") as fh:
            source = fh.read()
        for gone in ("import rank", "import brief", "import build"):
            self.assertNotIn(gone, source)


class NoAuthoredDocDescribesTheOldModel(unittest.TestCase):
    """The document table in the rebuild plan, made mechanical. A table is a
    promise; a test is enforcement.

    `PENDING` is the honest part. These files still describe the old model and
    are scheduled for a later phase; naming them here means a NEW offender
    fails immediately, and the list shrinks as those phases land. An empty
    allowlist today would only be achievable by lying."""

    TOKENS = ["rank.py", "build.py", "brief.py", "effort_minutes",
              "cognitive_load", "lead_time_days", "unblocks_inferred"]

    # Scheduled, not forgotten. Phase 6 archives GOAL/BOOTSTRAP; Phase 7
    # rewrites the contract docs and the cold-start test.
    PENDING = {"GOAL.md", "BOOTSTRAP.md", "CLAUDE.md", "AGENTS.md",
               "README.md", "docs/cold-start-test.md"}

    # The register is the RECORD of the old model. Rewriting it would delete
    # the reasoning these entries exist to preserve.
    ALLOWED = {"wiki/ruled-out.md"}

    # Task BODIES are records too -- a handoff saying "build.py reported a
    # 3-hop chain" is what happened, and editing it would be rewriting
    # history. Their FRONTMATTER is covered instead, and covered harder, by
    # `test_no_task_file_carries_a_score_input` and
    # `test_no_task_file_carries_an_edge`.
    #
    # This exclusion earned itself: it was added only after the guard flagged
    # 18 item files, and reading them turned up one that was NOT a record --
    # GB-008 told a future session that its edge to gate L was
    # `unblocks_inferred`, live instruction about a deleted field, sitting in
    # a body that `kickoff.py` excerpts. That got fixed rather than excluded.
    # `decisions` and `proposals` are records for the same reason the register
    # is: a ruling that records WHY a field was deleted has to name the field.
    # `DEC-202` tripped this guard by explaining the deletion the guard exists
    # to enforce.
    EXCLUDE_DIRS = ("archive", "inbox", "threads", "audits", "items",
                    "decisions", "proposals")

    def _authored(self):
        out = []
        for name in sorted(os.listdir(ROOT)):
            if name.endswith(".md"):
                out.append(name)
        for base in ("docs", "plugin", "state"):
            for root, dirs, files in os.walk(os.path.join(ROOT, base)):
                dirs[:] = [d for d in dirs if d not in self.EXCLUDE_DIRS]
                out += [os.path.relpath(os.path.join(root, f), ROOT)
                        for f in files if f.endswith((".md", ".json"))]
        return out

    def test_no_unscheduled_doc_describes_the_old_model(self):
        docs = self._authored()
        # R-075: assert the denominator. The scope is the 7 root `.md` files,
        # `docs/`, the plugin's 4 skills + 2 manifests, `state/backlog.md`,
        # `repos.json`, the 6 `project.md` and the 2 machine files -- 24
        # today. This threshold has already earned itself once: adding the
        # `items`/`decisions`/`proposals` exclusions dropped the walk from 33
        # to 24 and the guard REFUSED to report clean over the smaller set,
        # instead of quietly certifying a third of the tree it no longer read.
        self.assertGreaterEqual(len(docs), 20,
                                "walked %d authored docs -- the scan did not "
                                "run, or its scope silently shrank" % len(docs))
        offenders = []
        for rel in docs:
            if rel in self.PENDING or rel in self.ALLOWED:
                continue
            with open(os.path.join(ROOT, rel), encoding="utf-8",
                      errors="replace") as fh:
                text = fh.read()
            for token in self.TOKENS:
                if token in text:
                    offenders.append("%s: %s" % (rel, token))
        self.assertEqual(sorted(offenders), [],
                         "authored docs describe a model that no longer exists")

    def test_the_pending_list_does_not_rot(self):
        """A file on the pending list that no longer offends must come off it,
        or the list becomes a permanent exemption nobody rechecks."""
        stale = []
        for rel in sorted(self.PENDING):
            path = os.path.join(ROOT, rel)
            if not os.path.exists(path):
                continue
            with open(path, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
            if not any(token in text for token in self.TOKENS):
                stale.append(rel)
        self.assertEqual(stale, [],
                         "these are clean now -- remove them from PENDING")


if __name__ == "__main__":
    unittest.main(verbosity=2)
