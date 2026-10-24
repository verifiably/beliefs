---
id: beliefs-5aad8c
title: Consolidate work roots under a single .work/ instead of the project root
status: todo
priority: 3
size: m
complexity: mid
process: direct
created: 2026-09-07T09:48:53Z
updated: 2026-10-24T11:23:52Z
depends: [beliefs-1b6534]
tags: [testing]
---

Why: Keep the project root readable by putting current acceptance and lifecycle-test scratch under .work/ on the certified volume. Reproduction already moved there at f2d5a14. This task finishes the current defaults; it does not repair historical acceptance commands.

Established at main 2437c71 (2026-10-24):
- Cut 32 through the newest runner, cut 46, already default to MAIN_CHECKOUT / ".work" / "acceptance" / "cutN".
- The newest chain runs cut46 -> ... -> cut17. Cut 17 has no prefix runners and supplies its explicit nineteen-module inventory, beginning with cut 6. The remaining live runner defaults outside .work/ are cuts 17–31 (fifteen), not the original seventeen-runner inventory.
- python/tests/acceptance/conftest.py still defaults SCIENCE_CUT4_ROOT to .cut4-acceptance. python/tests/conftest.py::certified_work still falls back to .lifecycle-wrappers-test; python/tests/test_n2.py::test_an_empty_cut10_root_uses_the_main_checkout_fallback asserts that path.
- python/tests/test_project_root.py names five older roots: .cut4-acceptance, .cut29-acceptance, .cut30-acceptance, .cut31-acceptance and .lifecycle-wrappers-test. All five directories still exist; their contents and retention have not been assessed.
- beliefs-1b6534 was dropped with user approval on 2026-10-24. 8b7fbc3 restored cut 5 as cited-not-run evidence; c153ac2 and the frozen-guard doctrine establish older runner signatures as historical. Do not revive cut 5 or require cuts 4–16's historical commands to run. The resolved dependency is retained as provenance.
- Certification belongs to the volume tuple in Atoms, not to a directory spelling. The old device-number observation in the capture below is historical, not a current certification check. Use MAIN_CHECKOUT on the certified volume, preserving explicit SCIENCE_CUT*_ROOT overrides.

Done:
- Move only current defaults: live runners cut17_acceptance.py through cut31_acceptance.py to .work/acceptance/cutN, the shared acceptance fixture to .work/acceptance/cut4, and certified_work's lifecycle fallback under .work/. Keep override precedence, empty-value behavior, prefix-root forwarding, cleanup and accounting unchanged.
- Update the fallback assertion and current-facing instructions that describe those defaults. Do not rewrite frozen conformance bodies, historical results, cited-not-run surfaces or old runner defaults merely to make every textual path match. Apply the doctrine to any affected live pins, with its dated citation amendment; never re-pin cited evidence.
- Add focused checks for changed defaults and existing environment overrides through the documented test front door. Reuse test_recent_cut_acceptance.py, test_checkout.py, the lifecycle fallback test and the project-root guard; establish runner behavior without re-running historical chains. Run the focused checks and just test-fast; run capability-dependent checks only on a certified tuple and report the exact mismatch otherwise.
- Before retiring any existing scratch directory, inventory its contents and references and retain needed evidence. Never delete an unassessed corpus or log. Shrink LEGACY_WORK_ROOTS only when the corresponding directory is actually retired; retain old ignore entries while existing roots or preserved evidence need them. Directory retention and any runtime verification limits must be stated in the completion report.

Where to look: [ref:doctrine] distinguishes live machinery from cited evidence; [ref:readiness] records the approved cut-5 disposition. Start with python/tools/cut46_acceptance.py -> cut17_acceptance.py, python/tools/acceptance_runner.py, python/tools/checkout.py, both conftest.py files, python/tests/test_n2.py, python/tests/test_recent_cut_acceptance.py, python/tests/test_project_root.py and .gitignore.

Process: direct; m/mid. The destination, scope boundary and verification are established; bounded pin/retention checks remain. Priority stays 3.

## Original capture (historical; superseded where established above)

Thirteen git-ignored work-root directories sit at the project root (.cut4/5/6/7/8/9/19-acceptance, .cut14-merge-cache, .lifecycle-wrappers-test, .mm30-reproduction, .mm30-reproduction-cut21), against five genuine hidden dirs (.git, .worktrees, .claude, .agents, .codex). They drown the real ones.

Proposal: one hidden root, e.g.
  .work/acceptance/cut21/        was .cut21-acceptance/
  .work/reproduction/mm30-cut21/ was .mm30-reproduction-cut21/
  .work/merge-cache/cut14/       was .cut14-merge-cache/
One .gitignore line (.work/), and it absorbs the non-cut variants a bare ./acceptance/ would not. Prefer hidden over a visible ./cuts or ./acceptance: these are ignored scratch, and a visible root entry is more intrusive to someone browsing the repo, not less.

DURABILITY IS NOT AN OBSTACLE. The allowlist is a volume certification held in atoms, not a path rule — root.py:271: 'Science holds no tuple data, no allowlist and no override: admitting a new volume configuration is an atoms certification amendment.' A subdirectory is the same device (verified: repo root, .cut19-acceptance and .worktrees all report device 66306), so the certification is untouched.

Scope: 17 runners each carry one line, DEFAULT_WORK = PYTHON_ROOT.parent / '.cutN-acceptance'; plus python/tests/acceptance/conftest.py's SCIENCE_CUT4_ROOT default; plus tools/reproduction's mm30 default; plus .gitignore. SCIENCE_CUT*_ROOT already overrides, so hosts are unaffected.

ADOPT FORWARD, NEVER MIGRATE THE FROZEN RECORDS. Of 25 docs naming these paths, 11 are conformance results records (cuts 7-19). Those state the work root a past run actually used; rewriting them would make them assert something false about the past, which the repo's own rule forbids (invalidated frozen evidence is pinned and cited, never edited). Leave every results record alone. Old .gitignore lines can be pruned once nothing cites them.

Verification is the hard part, not the edit: proving a runner still works means re-running its chain, and most chains cannot run today (cut 20 absent; cut 5 carries 15 pre-existing failures, beliefs-1b6534). Do this when a chain can be exercised, not blind.

## References

- doctrine (input, required, kind=decision): docs/superpowers/specs/2026-09-07-frozen-guard-doctrine-design.md — live machinery and preserved historical surfaces
- readiness (context, kind=brief): docs/notes/2026-10-24-conformance-readiness-brief.md — approved historical cut-5 disposition

## Notes

- 2026-09-12T16:26:55Z (main): Complexity mid: The destination convention, runner defaults, environment overrides and same-volume constraint are established, and .work is already ignored. Remaining judgment is validating the historical runner chains and separating current defaults from frozen run records.
- 2026-09-16T10:03:27Z (main): 2026-09-16 doc review: the reproduction half landed at f2d5a14 (2026-09-12) — .work/ is gitignored and the mm30 corpora live under .work/reproduction/ (mm30, mm30.cut22, mm30-cut21, cut20-*). What remains is the acceptance half: every cutN_acceptance.py DEFAULT_WORK and tests/acceptance/conftest.py's SCIENCE_CUT4_ROOT default still point at .cutN-acceptance (root today: .cut4, .cut29, .cut30, .cut31-acceptance, .lifecycle-wrappers-test). The body's 'cut 20 absent' is also dated: cut 20's results record exists (2026-09-07) and the live certified chain cut31→…→cut17 ran green at cut 31, so that chain is exercisable for verification; cut 5 remains off the live chain (beliefs-1b6534).
- 2026-09-16T10:22:47Z (chore/docs-guards): 2026-09-16: beliefs-8d0497's guard (python/tests/test_project_root.py) pins the five legacy roots by name in LEGACY_WORK_ROOTS; retiring the runner defaults under .work/acceptance/ shrinks that set, and a cut 32 runner defaulting to .cut32-acceptance trips it — set DEFAULT_WORK under .work/ from the next runner on.
- 2026-10-24T11:23:52Z (main): scope: rescoped; at main 2437c71, reproduction and cut32–46 defaults already use .work/, cut46 chains only to cut17, and cut5 repair was deliberately dropped under 8b7fbc3/c153ac2; narrowed to fifteen live runner defaults plus acceptance/lifecycle fixtures, their checks and assessed root retention; preserved the complete capture, priority 3 and resolved dependency; m/mid/direct because destination, historical boundary and verification are established
