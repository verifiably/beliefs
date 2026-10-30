---
id: beliefs-e12aaa
title: Diagnose the intermittent test_verify environment-manifest mismatch
status: todo
priority: 2
size: s
complexity: mid
process: direct
created: 2026-10-29T12:52:09Z
updated: 2026-10-30T13:36:05Z
depends: []
tags: [tests]
agent: claude-code/claude-opus-5-5
origin: agent
---

Question: Which exact EnvironmentManifest entries differ between recording and the pre-execution check in the two reported test_verify failures, and is the difference caused by test isolation, mutable captured files, or another mechanism? Worker load is an observed context, not a diagnosed cause.

Where to start: python/tests/test_verify.py::test_r11_a_nondeterministic_transform_yields_all_four and ::test_a_data_dependent_replay_over_different_inputs_is_conforming; their fixtures_cut3.py memory_production/memory_assessment/memory_replay helpers and fixtures_cut15.py:data_dependent_pair; python/src/beliefs/adapter.py:capture_closure, _walk_closure, capture_environment, require_executing_environment; python/src/beliefs/boundary.py:_execute_run. At e7c3464, require_executing_environment compares the entire manifest with a fresh closure capture just before run_engine. That establishes the refusal seam, not the cause. The filing session is claude-code:a586de0e-bccf-4067-9940-3b6ecc9e67a2, filing call/result at transcript lines 412-413; baseline revision 064f351.

Bound: Diagnose these two failures in an isolated, hydrated worktree. First run the protected focused route with both named tests (just test-one tests/test_verify.py -k 'r11_a_nondeterministic_transform_yields_all_four or a_data_dependent_replay_over_different_inputs_is_conforming'); then capture the smallest manifest difference with narrowly scoped instrumentation and controlled repetitions. Respect the invoking checkout's validated test policy. Do not rerun the full suite repeatedly to fish for a failure, serialize the suite, suppress the refusal, or weaken environment identity. Record the commands, worker settings and attempt count; a passing retry alone does not diagnose it. Any fixture subprocess uses an explicit minimal environment and test-owned HOME; evidence contains no host credentials. If the cause proves to be an external dependency, do the required upstream issue/PR/branch/changelog search before reproducing or patching that dependency. This task records a diagnosis and recommendation; implementation needs a separately scoped follow-up if warranted.

Expected result: Record the field-level difference, a minimal reproducer and causal explanation, and the smallest justified remedy plus its regression-test location. If a bounded attempt cannot reproduce the issue, record the actual negative evidence and what next evidence is needed; do not call it fixed. Correctness evidence must distinguish a legitimate environment change from nondeterministic capture. Keep the original baseline failure and later passing runs separate. Do not conflate this refusal with beliefs-631101's replay recipe-identity check timing or beliefs-067a8d's test-policy adoption.

Ideas it wakes: None; this is the original idea promoted to a bounded diagnosis task. Record the result on beliefs-e12aaa and scope any justified fix without inventing a waiting parent.

Original observed evidence (preserved):
Observed 2026-10-29 in the full just test baseline at 064f351 (.worktrees/a989fb-retire-door, non-N2 phase, 6333 passed): test_verify.py::test_r11_a_nondeterministic_transform_yields_all_four and ::test_a_data_dependent_replay_over_different_inputs_is_conforming got RunRefused('the recorded environment is not the executing environment ...') instead of RunMinted. Both pass under just test-one in isolation (2 passed, 24.9 s), and the next just test-fast passed them. The refusal points at an environment fingerprint that differs between recording and execution when many workers run at once; the cause is not diagnosed. A flaky refusal in the non-N2 phase stops just test before N2 and TypeScript run.

## Notes

- 2026-10-29T12:52:09Z (add): created
  provenance: {"harness_session":"claude-code:a586de0e-bccf-4067-9940-3b6ecc9e67a2","harness_session_source":"CLAUDE_CODE_SESSION_ID","origin":"agent"}
