#!/usr/bin/env python3
"""The exact glob set PROP-0003 proposes, and the measurement behind its 96%.

Kept beside the proposal so the number is reproducible rather than asserted:

    python3 state/proposals/PROP-0003-clusters.py

Not a tool. If PROP-0003 is accepted this becomes the item set and this file
can go; if it is rejected it is the record of what was offered.
"""
import os, sys, collections

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import audit, stale, _model  # noqa: E402

SINCE = "2026-07-05"

CANDIDATES = [
 # (id, repo, title, [globs])
 ("GB-015", "gimbal-bench", "Bench console UI: the operator-facing rebuild",
  ["tools/bench_ui/static/**"]),
 ("GB-016", "gimbal-bench", "Bench console server and serial bridge",
  ["tools/bench_ui/server.py", "tools/bench_ui/serial_bridge.py",
   "tools/bench_ui/commands.py", "tools/bench_ui/faults.py",
   "tools/bench_ui/fixtures.py", "tools/bench_ui/net_probe.py",
   "tools/bench_ui/stage_scopes.json", "tools/bench_ui/help_corpus.json"]),
 ("GB-017", "gimbal-bench", "Console contract, parser and lane tests",
  ["tools/bench_ui/test_*.py"]),
 ("GB-018", "gimbal-bench", "mega_gate: the seven-leg offline gate and its sweeps",
  ["tools/mega_gate.py", "tools/gate_baseline.json", "tests/test_mega_gate.py",
   "captures/gimbal10/mega/**"]),
 ("GB-019", "gimbal-bench", "gimbal-10 firmware: SAFE, stop and mute lanes",
  ["sketches/gimbal/gimbal.ino", "sketches/gimbal/gimbal_types.h"]),
 ("GB-020", "gimbal-bench", "Firmware state-model tests",
  ["tests/test_gimbal10_firmware.py", "tests/test_grouped_a4_firmware.py",
   "tests/test_motion_capture_firmware.py",
   "tests/test_group_motion_capture_firmware.py"]),
 ("GB-021", "gimbal-bench", "Motion campaign and capture tooling",
  ["tools/motion_*.py", "tools/group_motion_*.py", "tools/grouped_goto_model.py",
   "captures/gimbal10/motion/**", "tests/test_motion_*.py",
   "tests/test_group_motion_*.py"]),
 ("GB-022", "gimbal-bench", "Vision harness and camera qualification",
  ["tools/harness/**", "tools/cam_calibrate.py", "tools/vision_*.py",
   "tools/group_camera_trace.py", "tests/test_group_camera_trace.py",
   "tests/fixtures/poses/**"]),
 ("GB-023", "gimbal-bench", "Wire suite, bus evidence and anchor checking",
  ["tools/wire_suite.py", "tools/wire_evidence.py", "tools/check_anchors.py",
   "tools/can_*.py", "tools/test_wire_suite_offline.py",
   "tools/test_wire_evidence.py", "tests/test_capture_safety.py"]),
 ("GB-024", "gimbal-bench", "Planning prompts and design documents",
  ["docs/*PLAN*.md", "docs/*PROMPT*.md", "docs/GIMBAL10-DESIGN.md",
   "docs/*BRIEF*.md", "docs/*HANDOFF*.md", "docs/*ONBOARDING*.md",
   "docs/CODEX-*.md", "docs/SMOOTH-MOTION-*.md", "docs/AUTONOMOUS-*.md",
   "docs/FIXTURE-MASTERPLAN*.md", "docs/PHASEB-*.md", "docs/REACHABILITY-*.md",
   "docs/MEGAPLAN-*.md", "docs/GIMBAL10-*.md", "README.md",
   "UI-OVERHAUL-BRIEF.md", "VISION-HARNESS-BRIEF.md"]),
 ("GB-025", "gimbal-bench", "G-series offline release evidence",
  ["captures/gimbal10/g1/**", "captures/gimbal10/g2/**",
   "captures/gimbal10/g4/**", "captures/gimbal10/g5/**"]),
 ("GB-026", "gimbal-bench", "UI-overhaul milestone captures",
  ["captures/ui-overhaul/**"]),
 ("GB-027", "gimbal-bench", "Product-aim and group-product runtime",
  ["tools/group_product_*.py", "tools/product_camera_helper/**",
   "tools/bench_ui/product_aim_*.py", "tools/bench_ui/product_bootstrap.py",
   "tests/test_group_product_*.py", "tools/qualify_*.py",
   "tests/test_qualify_*.py"]),
 ("GB-028", "gimbal-bench", "Commissioning and probe scripts",
  ["tools/commission_*.py", "tools/*_probe.py", "tools/find_port.py",
   "tools/motor_session.py", "tools/set_accel.py", "tools/readdress.py",
   "tools/check_*.py", "tools/hold_capture.py", "tools/sweep_runner.py",
   "tools/source_tree_identity.py", "tests/test_source_tree_identity.py",
   "tests/test_repo_safety.py", "tools/fixture_geometry.py",
   "tools/test_commission_allowlist.py", "tools/test_fixture_geometry.py",
   "tools/arm_watch.py", "tools/write_pid.py", "tools/capture.py",
   "tools/bench_mcp.py", "tools/move_by.py", "tools/id_probe.py"]),
 ("SITE-004", "engineered-lighting-site", "Doc 4a: the connector-level companion",
  ["docs/04a-wire-the-zones.md", "docs/assets/photo-*.jpg"]),
 ("SITE-005", "engineered-lighting-site", "Site build, CI and end-to-end tests",
  ["mkdocs.yml", ".github/workflows/**", "tests/e2e/**", "requirements-*.txt",
   "docs/js/**", "docs/stylesheets/**", "docs/CNAME", "docs/.pages",
   ".gitignore"]),
 ("SITE-006", "engineered-lighting-site", "Doc 8, the index and site navigation",
  ["docs/08-build-the-fixture.md", "docs/index.md",
   "docs/00b-ai-native-workflow.md", "docs/01-how-we-got-here.md",
   "docs/05-teach-it-to-aim.md", "DESIGN.md", "site-build-brief.md"]),
 ("GB-029", "gimbal-bench", "Fixture bench-session and hardware captures",
  ["captures/gimbal10/fixture/**"]),
 ("SITE-008", "engineered-lighting-site", "BoM checklist and wiring diagram assets",
  ["docs/bom-checklist.md", "docs/assets/wiring-*.svg",
   "docs/assets/wiring-*.png", "docs/assets/*.svg",
   "docs/06-message-contract.md", "docs/07-building-the-software.md",
   "docs/04-full-fixture-bench.md", "PROJECT-STATE.md"]),
 ("SITE-007", "engineered-lighting-site", "Frame CAD, coupons and render checks",
  ["docs/cad/**", "ref/RMD-L-5005-S.md", "ref/step_dump.py",
   "ref/v7-adversarial-review.md", "tools/meshcheck.py", "tools/run_checks.py",
   "tools/solve_balance.py", "docs/03-build-the-gimbal.md",
   "docs/03a-wire-the-bench.md", "docs/03b-print-the-frame.md",
   "docs/03c-prove-the-bus.md", "GROUND-UP-BRIEF.md", "prompts/**"]),
]


def main():
    root = _model.find_root()
    _f, unattributed, _c, _m = audit.audit(root, SINCE)
    specs = stale.load_repos(root)
    repos = {}
    for name in unattributed:
        r = audit.Repo(name, specs.get(name)); r.open()
        r.commits = audit.commits(r, SINCE)
        audit.load_files(r, SINCE, progress=False)
        repos[name] = r

    before = sum(len(v) for v in unattributed.values())
    covered_by = collections.Counter()
    covered = set()
    for item_id, repo_name, _title, globs in CANDIDATES:
        r = repos.get(repo_name)
        if not r:
            continue
        matchers = [audit.glob_re(g) for g in globs]
        for sha, _d, _s in unattributed[repo_name]:
            paths = r.files.get(sha, [])
            if any(m.match(p) for m in matchers for p in paths):
                covered_by[item_id] += 1
                covered.add((repo_name, sha))

    print("group D before: %d" % before)
    print("covered by the proposed set: %d" % len(covered))
    print("remaining: %d" % (before - len(covered)))
    print("coverage: %.0f%%\n" % (100.0 * len(covered) / before))
    for item_id, repo_name, title, _g in CANDIDATES:
        n = covered_by[item_id]
        flag = "  <-- TOO BROAD" if n > audit.BROAD_GLOB_COMMITS else ""
        print("  %-9s %3d  %s%s" % (item_id, n, title[:46], flag))

    print("\n--- NOT covered ---")
    rest = collections.Counter()
    for name, rows in unattributed.items():
        for sha, d, subj in rows:
            if (name, sha) in covered:
                continue
            rest[(name, subj[:60])] += 1
    for (name, subj), _n in rest.most_common(25):
        print("  %-26s %s" % (name, subj))
    print("  ... %d uncovered total" % (before - len(covered)))


main()
