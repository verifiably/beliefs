---
id: beliefs-a555d6
title: ruff format is not in the gate; 11 reproduction-lane files drift from it
status: todo
priority: 3
size: m
complexity: high
process: planned
created: 2026-09-10T22:01:42Z
updated: 2026-10-09T15:44:40Z
depends: []
tags: [hygiene]
---

Why: the gate runs ruff check but not ruff format, so formatting drifts silently. On 2026-10-09 (main cb354e1), 347 of 566 Python files under python/ would be reformatted: 70 src, 180 tests, 79 tests/acceptance, 18 tools. Line length is 120, from [tool.ruff] in python/pyproject.toml. Decision 2026-10-09 (user): option (c), reformat once and enforce. Rejected: (a) keep format out of the gate, and (b) a ratchet with an exclude list of the drifted files.

Done:
- python/pyproject.toml excludes, for formatting only ([tool.ruff.format] exclude), every file a freeze pin names. On 2026-10-09 frozen_guards.pins_in over the 43 guard modules found 942 pins on 57 distinct targets, 53 of them under python/ (9 content-pinned, 48 commit-pinned), such as the n2_arms_cutN declaration modules. Derive the list from frozen_guards, not by hand. Add a test asserting the exclude list equals the pinned python/ targets, so a new freeze cannot drift from it.
  The exclude is temporary: beliefs-ea5ec7 makes pins hold up to formatting, then removes it and formats those files.
- One isolated commit runs ruff format over everything else. Its hash goes in .git-blame-ignore-revs.
- Every N2 arm whose before-text the reformat moves is restored, without editing any frozen declaration:
  - live guards re-target through their _LIVE_SABOTAGES (or RETARGETED_ROWS);
  - portable arms through test_n2.py's portable override;
  - cited-not-run guards get their moved pin recorded in cited_not_run.py.
  A scratch-copy measurement of declared arms found 63 of the 1149 that apply today would break (cut 46: 7, cut 19: 5, cuts 11/14/28/31/35: 4 each, cuts 9/10/16/38: 3 each, ...). Re-measure over audited arms with arm_staleness after the reformat, since that is the authority.
- py_check_cmd in the justfile gains `uv run --frozen ruff format --check .`, and so does ci-python if it does not go through py_check_cmd. Update the AGENTS.md gate line to match.

Constraints:
- Frozen guard doctrine (docs/superpowers/specs/2026-09-07-frozen-guard-doctrine-design.md).
- Memories: live guards end with zero stale arms; cited guards are recorded, never chained or run.
- A repo-wide reformat conflicts with every open branch. Land it while no other kernel lane has unmerged work: on 2026-10-09 only main existed.
- The re-target commits and the reformat commit land together, so no commit on main has stale live arms.

Verification:
- ruff format --check passes.
- test_arm_staleness and frozen-pin checks are green.
- The audits of the re-targeted live arms score sound: run each affected live guard's N2 phase through host-budget, or the newest cut runner's chain if that is the cheaper whole-set check.
- Finish with just gate on the certified host.

## Notes

- 2026-09-16T10:03:27Z (main): 2026-09-16 doc review: 'ruff format --check .' from python/ now reports 273 files would be reformatted, 159 already formatted — the drift is repo-wide, not 11 reproduction-lane files. Scoping this means deciding format's place in the gate over the whole tree, and the one reformat commit would touch frozen-cut test modules, which is a supersession by citation, not an edit.
- 2026-10-09T14:39:36Z (main): scope: question; measured 347/566 files drifted and 63 of 1149 applying N2 arms broken by an src reformat; options and recommendation (keep format out, record why) under Open questions
- 2026-10-09T15:27:47Z (main): scope: scoped; user chose (c) reformat once and enforce; added frozen-pin evidence (53 pinned python/ targets to exclude); rewrote body; todo P3/m/high/planned
- 2026-10-09T15:44:39Z (main): follow-up beliefs-ea5ec7 filed: freeze pins hold modulo formatting (AST + comments; 31/31 reformatted pinned files pass), which retires this task's format exclude
