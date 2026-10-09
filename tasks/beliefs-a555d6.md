---
id: beliefs-a555d6
title: ruff format is not in the gate; 11 reproduction-lane files drift from it
status: doing
priority: 3
size: m
complexity: high
process: planned
owner: chore/ruff-format-gate
created: 2026-09-10T22:01:42Z
updated: 2026-10-09T19:50:59Z
started: 2026-10-09T17:01:36Z
depends: []
tags: [hygiene]
spec: docs/superpowers/specs/2026-10-09-ruff-format-gate-design.md
plan: docs/superpowers/plans/2026-10-09-ruff-format-gate.md
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
- 2026-10-09T17:01:36Z (main): started
  provenance: {"harness_session":"claude-code:0bad1686-0d62-4fbe-b728-4897c6863fa5","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-09T17:08:57Z (chore/ruff-format-gate): pilot 2026-10-09 (worktree, discarded): exclude = 52 existing pinned python/ targets + cut 4's unpinned cited surface (guard, declaration, runner) = 56 files; ruff format touches 314 others; pins all hold; 70 audited arms stale across 27 live guards, 3 newly stale cited arms (cut 10); 5 displaced suppression comments (2 noqa, 3 type: ignore); test-fast otherwise green; all 70 re-targets derive mechanically with exact equivalence (format(sabotaged pre-format) == re-targeted arm applied to formatted)
- 2026-10-09T17:11:04Z (chore/ruff-format-gate): correction to the pilot note: the protected set is 55 existing files (52 pinned + cut 4's 3); the pilot's 56 included the removed n2_arms_cut25.py. 28 live guards affected, not 27.
- 2026-10-09T17:11:04Z (chore/ruff-format-gate): parked (waiting on user, review): user reviews docs/superpowers/specs/2026-10-09-ruff-format-gate-design.md (commit 4f1addf in .worktrees/ruff-format-gate); on approval the agent writes the implementation plan
  provenance: {"harness_session":"claude-code:0bad1686-0d62-4fbe-b728-4897c6863fa5","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-09T17:16:28Z (chore/ruff-format-gate): review: spec round 1 — verdict: revise; findings: P1 1; reviewer: codex
- 2026-10-09T17:16:28Z (chore/ruff-format-gate): spec review P1: protected-set discovery misses scalar FROZEN_DECLARATION/CUT46_DECLARATION_SHA256. The focused cut-46 byte-identity check passes today; ruff 0.16.1 stdin formatting changes n2_arms_cut46.py sha256 from da3e36e19ecf87d3da17da009350bf0c82fcc29315323057f64e9c781cf6dc04 to cbce4b91e9e1a0ab29384322a765981c4b9b16c6dbfa890658a4d5dc52a889a8. Protect scalar declaration targets too (56 existing protected files today), correct section 3.3, and add portable coverage so future newest-cut declarations cannot escape the exclude.
- 2026-10-09T17:17:11Z (chore/ruff-format-gate): resumed
  provenance: {"harness_session":"claude-code:0bad1686-0d62-4fbe-b728-4897c6863fa5","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-09T17:17:11Z (chore/ruff-format-gate): review: spec round 1 — verdict: revise; findings: P1 1; reviewer: unknown (pasted by user)
- 2026-10-09T17:25:52Z (chore/ruff-format-gate): spec round 1 P1 fixed: protected set gains each guard's FROZEN_DECLARATION (scalar CUTN_DECLARATION_SHA256/COMMIT pins, cuts 26-46); only n2_arms_cut46.py was not already table-pinned, so 56 files. Pilot with 56 excluded: 289/290 live-guard static tests pass, the 1 failure an audit test failing on the stale arms; verification gains that static run as the scalar-pin backstop.
- 2026-10-09T17:26:22Z (chore/ruff-format-gate): parked (waiting on user, review): user reviews revised spec docs/superpowers/specs/2026-10-09-ruff-format-gate-design.md (round 2) in .worktrees/ruff-format-gate; on approval the agent writes the plan
  provenance: {"harness_session":"claude-code:0bad1686-0d62-4fbe-b728-4897c6863fa5","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-09T17:32:52Z (chore/ruff-format-gate): review: spec round 2 — verdict: revise; findings: P2 1; reviewer: codex
- 2026-10-09T17:32:52Z (chore/ruff-format-gate): spec round 2: independently confirmed 21 scalar declaration targets and 56 protected existing files; the round-1 P1 is resolved. P2: section 5 replaces the one-guard mutation pilot with static tests that explicitly exclude mutation audits and live checks. Keep the static pin backstop and restore a bounded mutation pilot through baseline, sabotage application, check execution, and soundness verdict before the roughly hour-long chain, as required by the extended-run pilot rule. The plan should run focused guard tests through just test-one rather than the direct pytest command shown.
- 2026-10-09T17:34:24Z (chore/ruff-format-gate): resumed
  provenance: {"harness_session":"claude-code:0bad1686-0d62-4fbe-b728-4897c6863fa5","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-09T17:34:24Z (chore/ruff-format-gate): spec round 2 P2 fixed: section 5 keeps the static pin backstop (now via just test-one) and adds a mutation pilot, the whole cut-46 guard via just test-one (36 arms, 7 re-targeted; 13 passed in 15 s pre-reformat), before the chain
- 2026-10-09T17:42:06Z (chore/ruff-format-gate): resumed
  provenance: {"harness_session":"claude-code:0bad1686-0d62-4fbe-b728-4897c6863fa5","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-09T17:42:06Z (chore/ruff-format-gate): plan written: docs/superpowers/plans/2026-10-09-ruff-format-gate.md, 6 steps; dry run of its tool and tests: 9/9 tests pass, derive on a scratch reformat gives 70 derived, 0 refused
- 2026-10-09T17:42:44Z (chore/ruff-format-gate): parked (waiting on user, review): user reviews docs/superpowers/plans/2026-10-09-ruff-format-gate.md and picks the execution method; then the agent executes Task 1 in .worktrees/ruff-format-gate
  provenance: {"harness_session":"claude-code:0bad1686-0d62-4fbe-b728-4897c6863fa5","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-09T17:53:09Z (chore/ruff-format-gate): review: plan round 1 — verdict: revise; findings: P2 2; reviewer: codex
- 2026-10-09T17:53:09Z (chore/ruff-format-gate): plan review: nine proposed tool cases passed in a temporary probe through just test-one. P2: Tasks 3/4 use space-separated PROTECTED/MODS scalars; default zsh passes each as one path, so the protected-file diff can falsely pass and static guard collection fails (two-module collect-only reproduction exits 4). Use arrays with quoted expansion or explicitly execute those snippets under Bash. P2: Task 6 closes the parent before its own step child beliefs-3b1bb8 is complete; tasks done refuses open descendants. Finish and close the step children, including Task 6, before parent closure, with the final-review/merge order explicit.
- 2026-10-09T17:56:36Z (chore/ruff-format-gate): resumed
  provenance: {"harness_session":"claude-code:0bad1686-0d62-4fbe-b728-4897c6863fa5","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-09T17:56:36Z (chore/ruff-format-gate): plan round 1 fixed: path lists go one-per-line through a file and xargs (proved under zsh: 56 protected paths, clean tree passes, a touched cut-46 declaration is caught; 39 guard modules split into separate args); children close with their tasks, Task 3's in a record-only commit after the pure reformat; Task 6 orders verification note, final review, land, child done, parent done
- 2026-10-09T17:57:09Z (chore/ruff-format-gate): parked (waiting on user, review): user reviews the revised plan docs/superpowers/plans/2026-10-09-ruff-format-gate.md (round 2) and picks the execution method; then the agent executes Task 1 in .worktrees/ruff-format-gate
  provenance: {"harness_session":"claude-code:0bad1686-0d62-4fbe-b728-4897c6863fa5","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-09T17:58:58Z (chore/ruff-format-gate): review: plan round 2 — verdict: accept; findings: none; reviewer: codex
- 2026-10-09T17:58:58Z (chore/ruff-format-gate): resumed
  provenance: {"harness_session":"codex:01a121a7-aedd-7b71-942e-be84b87b9ce4","harness_session_source":"CODEX_THREAD_ID"}
- 2026-10-09T17:58:58Z (chore/ruff-format-gate): execution: inline in .worktrees/ruff-format-gate by codex; fresh whole-branch reviewer at the end; no push
- 2026-10-09T18:11:14Z (chore/ruff-format-gate): reformat commit REFORMAT=03d91bd4ced210e8935f3101da1dc59fe1eef7b3, BASE=f87cb460b5279a744a76c0d0c521190d30b7d715; 313 files; 56 protected paths unchanged; declarations/pins identical including post-commit comparison; fast red only in 3 staleness tests; four suppression comments moved
- 2026-10-09T18:26:47Z (chore/ruff-format-gate): re-targets: 70 derived, 0 refused, verify 0 problems; static guard tests 287 passed; cut-46 mutation pilot 13 passed in 15.52 s; cut 10 records 3 stale arms; occupied-anchor widening preserves cut-46 uniqueness without weakening its gate
- 2026-10-09T18:31:41Z (chore/ruff-format-gate): full acceptance chain starting from a6c3123, after 287 static tests and cut-46 pilot 13/13 sound passed; certified-host waiver unset; tracked Codex exec session, 2-hour shell timeout
- 2026-10-09T18:39:14Z (chore/ruff-format-gate): chain progress: cut 6/7/9/11/12 guards passed; tracked acceptance session still running through cut 17's inventory; no failure observed
- 2026-10-09T19:03:54Z (chore/ruff-format-gate): chain progress: cut 27 and world-selection acceptance passed; cut 28 mutation audit running in tracked session 47983; no failure observed
- 2026-10-09T19:26:16Z (chore/ruff-format-gate): chain progress: cut 40/41 passed; cut 42 remote-publication acceptance running in tracked session 47983; no failure observed
- 2026-10-09T19:34:30Z (chore/ruff-format-gate): full acceptance chain passed: all 39 live guards; evidence in .work/ruff-format-gate/cut46-chain.log; starting just gate with skip reporting, certified-host waiver unset
- 2026-10-09T19:40:31Z (chore/ruff-format-gate): verification: cut-46 chain passed (76 pytest phases, 1172 tests, 3654.45 s pytest); just gate passed (6093 portable Python, 46 N2, 155 TypeScript; 1 causal-only fixture skip with other-layer coverage elsewhere), capability waiver unset
- 2026-10-09T19:43:11Z (chore/ruff-format-gate): main advanced only at c99da06 (new task record); merged into the branch and proved all non-task files byte-identical to verified 8f91ef6; retaining reformat 03d91bd and all chain/gate evidence
- 2026-10-09T19:50:58Z (chore/ruff-format-gate): review: impl round 1 — verdict: accept; findings: none; reviewer: codex
- 2026-10-09T19:50:58Z (chore/ruff-format-gate): fresh whole-branch review accepted: 313 formatting ASTs identical; all 56 protected files unchanged; 70 exact sabotage rows across 28 guards; recorded originals match base; current verify 70/0; no declined judgments or deferred findings
