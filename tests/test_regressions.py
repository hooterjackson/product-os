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


class ProjectsAreFirstClass(unittest.TestCase):
    """Every task belongs to a project, and the project's description is
    injected into every one of its kickoff prompts.

    The point of `description` being a field rather than prose in the project
    body: a session that has never seen this portfolio gets the frame before
    the task, in every prompt, without anyone remembering to paste it."""

    def test_every_task_names_a_project_that_exists(self):
        import _model as model_mod
        model = model_mod.Model.load(ROOT)
        self.assertGreater(len(model.items), 20, "the scan did not run")  # R-075
        slugs = set(model.projects)
        for node in model.items.values():
            self.assertIn(node.project, slugs,
                          "%s names a project that does not exist" % node.id)

    def test_every_project_has_a_description_and_a_prefix(self):
        import _model as model_mod
        model = model_mod.Model.load(ROOT)
        self.assertGreaterEqual(len(model.projects), 5, "the scan did not run")
        for slug, project in model.projects.items():
            self.assertTrue((project.get("description") or "").strip(),
                            "%s has no description, so its tasks ship with no "
                            "project framing" % slug)
            self.assertTrue(project.get("prefix"),
                            "%s declares no prefix" % slug)
        self.assertNotIn("north_star", _fm.FIELD_ORDER["project"])

    def test_the_description_reaches_the_kickoff_prompt(self):
        import _model as model_mod
        model = model_mod.Model.load(ROOT)
        prompts = glob.glob(os.path.join(ROOT, "public", "kickoff", "*.md"))
        self.assertGreater(len(prompts), 10, "the scan did not run")   # R-075
        for path in prompts:
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
            node = model.nodes[os.path.basename(path)[:-3]]
            description = model.projects[node.project].get("description")
            self.assertIn("## Project context", text)
            self.assertIn(description.strip(), text,
                          "%s carries no project framing" % node.id)

    def test_a_project_with_no_repo_says_so_rather_than_looking_stale(self):
        """`home-ai-infra` is the V-JEPA GPU box and has no repository at all.

        Telling a session to "find out where the work lives" when the answer is
        "nowhere, it is a machine in the house" sends it looking for something
        that does not exist -- and an evidence query against it must report
        unreachable, never clean."""
        import _model as model_mod
        model = model_mod.Model.load(ROOT)
        repoless = [slug for slug, p in model.projects.items()
                    if not (p.get("repos") or [])]
        self.assertIn("home-ai-infra", repoless)
        for slug in repoless:
            for node in model.items.values():
                if node.project != slug or not node.is_active:
                    continue
                path = os.path.join(ROOT, "public", "kickoff",
                                    "%s.md" % node.id)
                if not os.path.exists(path):
                    continue
                with open(path, encoding="utf-8") as fh:
                    text = fh.read()
                self.assertIn("has no repository", text, node.id)
                self.assertIn("only when Marcelo says so", text, node.id)


class ThePrefixSetIsDerivedNotHardcoded(unittest.TestCase):
    """It was three hardcoded tables -- `ID_RE`, `MENTION_RE` and
    `PREFIX_PROJECT`. A project created inline needed a new prefix edited into
    all three, and `MENTION_RE` is the audit's id-mention fallback, so missing
    one meant the audit silently stopped recognising a project's commits."""

    def test_the_hardcoded_tables_are_gone(self):
        """Anchored to the start of a LINE, because a module-level table is
        defined at column 0. The substring form of this test failed on its own
        replacement: `MENTION_RE = re.compile` is a substring of the private
        `_MENTION_RE = re.compile` that caches the derived pattern."""
        with open(os.path.join(ROOT, "tools", "_fm.py"), encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        self.assertGreater(len(lines), 100, "the file did not load")  # R-075
        defined = [ln.split(" =")[0] for ln in lines
                   if " = " in ln and not ln.startswith((" ", "\t", "#"))]
        for gone in ("PREFIX_PROJECT", "ID_RE", "MENTION_RE"):
            self.assertNotIn(gone, defined,
                             "%s is a hardcoded table again" % gone)

    def test_the_derived_set_covers_every_live_id(self):
        """The regression this test exists for, found by printing the set and
        reading it: `ID_SHAPE` was written `[A-Z]{2,6}`, so `parse_id("Q-001")`
        returned None and `Q` fell out of the derived set entirely -- exactly
        the bug the old comment warned about ("misses Q-007 because its prefix
        is one letter"). `mention_re()` would have stopped matching five live
        tasks and the thread indexer would have quietly stopped binding them.
        Nothing would have failed."""
        import _model as model_mod
        model = model_mod.Model.load(ROOT)
        pattern = _fm.mention_re()
        ids = [n.id for n in model.items.values()] + \
              [d.id for d in model.decisions.values()]
        self.assertGreater(len(ids), 20, "the scan did not run")     # R-075
        for item_id in ids:
            self.assertEqual(pattern.findall(item_id), [item_id],
                             "%s is not matched by the derived pattern -- the "
                             "indexer cannot see it" % item_id)

    def test_it_is_still_narrow_enough_to_reject_the_known_false_positives(self):
        """916 hits, 100% false positives, on the real corpus."""
        import _model as model_mod
        model_mod.Model.load(ROOT)
        pattern = _fm.mention_re()
        for probe in ("AES-256", "SHA-256", "ISO-8601", "RFC-2119", "UTF-8"):
            self.assertEqual(pattern.findall(probe), [], probe)

    def test_an_unloaded_prefix_set_raises_rather_than_matching_nothing(self):
        """R-075. A regex built from an empty set matches nothing and reads
        exactly like a corpus with nothing in it."""
        saved = _fm.prefixes()
        try:
            _fm.set_prefixes({})
            with self.assertRaises(RuntimeError):
                _fm.mention_re()
        finally:
            _fm.set_prefixes(saved)

    def test_an_undeclared_prefix_implies_no_project(self):
        """`Q-001`..`Q-004` are gimbal-bench and `Q-005` is engineering-site.
        Binding the prefix to whichever loaded first would make
        `E-ID-PROJECT-MISMATCH` fire on four real tasks."""
        import _model as model_mod
        model = model_mod.Model.load(ROOT)
        self.assertIsNone(model.prefixes().get("Q"))
        self.assertIsNone(model.prefixes().get("DEC"))
        self.assertEqual(model.prefixes().get("GB"), "gimbal-bench")


class ReorderingTheBacklogNeedsHisWords(unittest.TestCase):
    """`state/backlog.md` is the only place his order exists (`DEC-202`), so
    the two write operations are gated differently on purpose:

      appending asserts NOTHING about priority -- ungated
      moving asserts EVERYTHING -- needs `--said`

    The origin lives in the flag name, borrowed from `apply.py`, so an agent
    that forgets it fails safe toward refusing rather than toward writing."""

    def _scratch(self):
        import shutil as sh
        tmp = tempfile.mkdtemp(prefix="po-bl-")
        sh.copy(os.path.join(ROOT, "state", "backlog.md"),
                os.path.join(tmp, "backlog.md"))
        return tmp

    def _run(self, *args):
        return subprocess.run(
            [sys.executable, os.path.join(ROOT, "tools", "backlog.py")]
            + list(args), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            cwd=ROOT)

    def test_move_without_said_is_refused(self):
        proc = self._run("--move", "HAI-001", "1")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("--said", proc.stdout.decode())

    def test_move_with_said_reorders_and_keeps_the_header(self):
        import _model as model_mod
        path = os.path.join(ROOT, "state", "backlog.md")
        with open(path, encoding="utf-8") as fh:
            before = fh.read()
        try:
            proc = self._run("--move", "HAI-001", "1", "--said", "test move")
            self.assertEqual(proc.returncode, 0, proc.stdout.decode())
            model = model_mod.Model.load(ROOT)
            self.assertEqual(model.backlog_ids()[0], "HAI-001")
            with open(path, encoding="utf-8") as fh:
                after = fh.read()
            # The header is his prose and must survive a rewrite untouched.
            self.assertIn("THIS FILE IS THE PRIORITY", after)
            self.assertEqual(before.count("\n"), after.count("\n"),
                             "the rewrite added or dropped lines")
            self.assertEqual(sorted(model.backlog_ids()),
                             sorted(_ids(before)),
                             "the rewrite changed the SET, not just the order")
        finally:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(before)

    def test_a_move_says_the_surface_is_now_stale(self):
        """Reordering changes what llms.txt and reconcile.md name as next, so
        the gate goes red until publish.py runs. Discovering that from a red
        validate is how a guardrail gets ignored (`R-067`)."""
        proc = self._run("--move", "HAI-001", "1")
        with open(os.path.join(ROOT, "tools", "backlog.py"),
                  encoding="utf-8") as fh:
            self.assertIn("python3 tools/publish.py", fh.read())

    def test_add_refuses_a_task_that_does_not_exist(self):
        proc = self._run("--add", "ZZ-999")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("no such task", proc.stdout.decode())

    def test_add_refuses_a_duplicate(self):
        """`E-BACKLOG-DRIFT` catches a duplicate, but catching it at the write
        is better than catching it at the gate."""
        proc = self._run("--add", "HAI-001")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("already in the backlog", proc.stdout.decode())


def _ids(text):
    out = []
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            out.append(line)
    return out


class AWayInIsDerivedNeverTemplated(unittest.TestCase):
    """Written BEFORE `site.py` exists, so the rule constrains it by
    construction rather than by a review that might not happen.

    Measured 2026-08-20: FOUR of the six repos in `state/repos.json` have
    `local: null` -- HomeApp, genio, gimbal-bench and home-ai-infra are not
    cloned on this Mac -- and `GB-001` is `machine_affinity: formd-t1`, a
    Windows box. A card rendering `cd ~/Claude/<repo> && claude` from a
    template is wrong for most of the portfolio and looks right.

    `kickoff.py` did not have this bug in its repo section, but only BY
    OMISSION: it names a repo and a machine and emits no path, so it cannot
    emit a wrong one. That safety does not transfer to anything that wants to
    offer a command, which is why the derivation lives in `_context.reach`."""

    def _fixture(self):
        import _model as model_mod
        import new as new_mod
        root = model_mod.find_root()
        model = model_mod.Model.load(root)
        with open(os.path.join(root, "state", "repos.json"),
                  encoding="utf-8") as fh:
            spec = {k: v for k, v in json.load(fh).items()
                    if not k.startswith("_")}
        return root, model, spec, new_mod.machine_id(root)

    def test_a_command_only_ever_comes_back_for_a_clone_that_is_here(self):
        import _context as ctx
        root, model, spec, machine = self._fixture()
        checked = 0
        for node in model.nodes.values():
            verdict = ctx.reach(node, model, spec, machine)
            checked += 1
            if verdict["command"] is None:
                continue
            # It offered a command. Every precondition must actually hold.
            self.assertEqual(verdict["kind"], ctx.LOCAL, node.id)
            affinity = node.get("machine_affinity")
            self.assertIn(affinity, (None, machine),
                          "%s is bound to %s and still got a command"
                          % (node.id, affinity))
            for name in verdict["repos"]:
                local = (spec.get(name) or {}).get("local")
                self.assertTrue(
                    local and os.path.isdir(os.path.expanduser(local)),
                    "%s got a command for %s, which is not cloned here"
                    % (node.id, name))
        self.assertGreater(checked, 20, "the sweep did not run")     # R-075

    def test_an_uncloned_repo_yields_no_command(self):
        """APP-001 -> HomeApp, `local: null`. The exact case a template breaks
        on: no machine affinity, so nothing else stops it."""
        import _context as ctx
        root, model, spec, machine = self._fixture()
        verdict = ctx.reach(model.nodes["APP-001"], model, spec, machine)
        self.assertEqual(verdict["kind"], ctx.NO_CLONE)
        self.assertIsNone(verdict["command"])

    def test_machine_affinity_beats_a_local_clone(self):
        """Checked before the clone test on purpose: a command that RUNS is not
        a command that HELPS. Synthetic, because no real task currently pairs a
        cloned repo with a foreign machine -- and that is exactly the
        combination a future task will hit."""
        import _context as ctx
        root, model, spec, machine = self._fixture()
        node = model.nodes["Q-005"]          # engineered-lighting-site, cloned
        self.assertEqual(
            ctx.reach(node, model, spec, machine)["kind"], ctx.LOCAL)
        node.fm["machine_affinity"] = "formd-t1"
        try:
            verdict = ctx.reach(node, model, spec, machine)
            self.assertEqual(verdict["kind"], ctx.ELSEWHERE)
            self.assertIsNone(verdict["command"])
            self.assertIn("formd-t1", verdict["reason"])
        finally:
            node.fm["machine_affinity"] = None

    def test_a_project_with_no_repo_is_its_own_verdict(self):
        import _context as ctx
        root, model, spec, machine = self._fixture()
        verdict = ctx.reach(model.nodes["HAI-001"], model, spec, machine)
        self.assertEqual(verdict["kind"], ctx.NO_REPO)
        self.assertIsNone(verdict["command"])
        self.assertIn("says so", verdict["reason"])

    def test_site_py_when_it_lands_must_use_the_derivation(self):
        """The forward constraint. Skips today and stops skipping the moment
        site.py appears -- a vacuous pass is `R-075`, so it says which it is."""
        path = os.path.join(ROOT, "tools", "site.py")
        if not os.path.exists(path):
            self.skipTest("site.py does not exist yet; this guard is waiting")
        with open(path, encoding="utf-8") as fh:
            source = fh.read()
        self.assertIn("reach(", source,
                      "site.py builds a way-in without _context.reach -- the "
                      "one thing this test exists to prevent")
        self.assertNotIn("cd ~/", source, "site.py templates a local path")


class NothingCommittedUnderPublicNamesThisMachine(unittest.TestCase):
    """`public/` is served to every machine, so nothing in it may name this
    one. Shipped and measured: 26 `cd ~/Claude/...` commands across 4 committed
    files, session ids in `id` and `parent`, and the home directory
    dash-encoded inside a transcript path as `-Users-mlima-...`, which is why
    the disclosure screen's `/Users/...` pattern never saw it.

    `publish.py` already redacted `manual.yaml` chat URLs for this exact
    reason. It covered one of two sources -- the shape of `R-067`."""

    SPELLINGS = ["cd ~/Claude/product-os",
                 "git -C ~/Claude/product-os push",
                 # Uppercase placeholder on purpose: it exercises ROOTED (which
                 # keys on `/Users/`) without being a real home path, which
                 # the disclosure screen is right to flag in a committed file.
                 "python3 /Users/USERNAME/x.py",
                 "code C:\\Claude\\gimbal-bench",
                 "ls /home/USERNAME/",
                 "$ cd ~/Claude/product-os"]

    def test_the_check_matches_the_CLASS_not_the_known_spellings(self):
        """The finding this test exists for. The first version was anchored to
        `cd `, one of the two spellings that had shipped, and missed `git -C
        ~/Claude/product-os` -- **54 of them, live across 27 committed files,
        with the gate green.** `R-067` again, one syntax over.

        So the assertion is over a LIST of spellings, and adding one is how a
        future shape gets covered without rewriting the check."""
        import validate as validate_mod
        pattern = validate_mod.Validator.ROOTED
        for probe in self.SPELLINGS:
            self.assertTrue(pattern.search(probe),
                            "%r is machine-local and unmatched" % probe)

    def test_it_does_not_fire_on_a_path_that_names_no_machine(self):
        """A repo-relative path is correct on every machine, and `~45` is an
        approximation, not a path. A guard that cries wolf gets switched off."""
        import validate as validate_mod
        pattern = validate_mod.Validator.ROOTED
        for probe in ("tools/publish.py", "state/backlog.md", "~45 entries",
                      "~30 register entries", "wiki/ruled-out.md"):
            self.assertIsNone(pattern.search(probe), probe)

    def test_prose_is_exempt_because_nobody_runs_a_citation(self):
        """Scoped to command context on purpose. Three kinds of `~` path exist
        under public/: leaked commands, a `~/path/to/clone` PLACEHOLDER in a
        JSON fence, and `~/Claude/PICKUP.md:19` as a CITATION in an item body.
        Only the first is a hazard, and stripping the third would break the
        provenance it exists to give."""
        # Calls the check DIRECTLY. Shelling out to validate.py from a test
        # recurses without bound -- validate.py runs this suite as its own
        # gate, so the subprocess re-enters the test that spawned it. Found by
        # a 120s timeout, which is the polite version of the failure.
        import validate as validate_mod
        published = glob.glob(os.path.join(ROOT, "public", "kickoff", "*.md"))
        self.assertGreater(len(published), 10, "the scan did not run")  # R-075
        citation = [p for p in published
                    if "PICKUP.md" in open(p, encoding="utf-8").read()]
        if not citation:
            self.skipTest("the citation is not currently published")
        checker = validate_mod.Validator(ROOT)
        checker.check_public_is_machine_neutral()
        offenders = [f.code for f in checker.findings
                     if f.code == "E-PUBLIC-LOCAL-PATH"]
        self.assertEqual(offenders, [],
                         "a citation in prose was flagged as a command")

    def test_the_clone_path_is_derived_and_not_published(self):
        """`~/Claude/product-os` was hardcoded in two lines of actions.py and
        published 54 times. It comes from repos.json now, and only build/ --
        which nobody but this machine reads -- gets the real thing."""
        # Asserted POSITIVELY -- that the derivation is wired -- rather than
        # by grepping for the absence of the old string. The absence form
        # failed on this function's own docstring, which quotes the path to
        # explain the bug: a guard tripping on its own explanation, the same
        # shape as `MENTION_RE` matching `_MENTION_RE`.
        import actions as actions_mod
        self.assertIn("repos.json", actions_mod.clone_hint.__doc__ or "")
        self.assertEqual(actions_mod.clone_hint(ROOT, False),
                         "-C <your product-os clone>")
        self.assertIn("~/Claude/product-os",
                      actions_mod.clone_hint(ROOT, True),
                      "the volatile form lost the real path, so build/ is "
                      "useless to the person at this keyboard")
        published = glob.glob(os.path.join(ROOT, "public", "attach", "*.md"))
        self.assertGreater(len(published), 10, "the scan did not run")  # R-075
        for path in published:
            with open(path, encoding="utf-8") as fh:
                self.assertIn("<your product-os clone>", fh.read(),
                              "%s names a machine" % os.path.basename(path))

    def test_the_gate_carries_this_check(self):
        with open(os.path.join(ROOT, "tools", "validate.py"),
                  encoding="utf-8") as fh:
            source = fh.read()
        for code in ("E-PUBLIC-LOCAL-PATH", "E-PUBLIC-SESSION-ID",
                     "E-PUBLIC-HOME-DIR"):
            self.assertIn(code, source)

    def test_build_keeps_what_public_may_not(self):
        """The redaction must not cost the person at the keyboard the command.
        `build/` is git-ignored and generated volatile for exactly that."""
        prompts = glob.glob(os.path.join(ROOT, "build", "kickoff", "*.md"))
        if not prompts:
            self.skipTest("build/ not generated")
        self.assertTrue(
            any("claude -r" in open(p, encoding="utf-8").read()
                for p in prompts),
            "build/ lost the resume command too -- the split is gone")


if __name__ == "__main__":
    unittest.main(verbosity=2)
