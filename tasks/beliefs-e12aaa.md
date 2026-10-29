---
id: beliefs-e12aaa
title: test_verify snakemake runs refuse 'recorded environment is not the executing environment' under xdist load
status: idea
priority: 2
created: 2026-10-29T12:52:09Z
updated: 2026-10-29T12:52:09Z
depends: []
tags: [tests]
agent: claude-code/claude-opus-5-5
origin: agent
---

Observed 2026-10-29 in the full just test baseline at 064f351 (.worktrees/a989fb-retire-door, non-N2 phase, 6333 passed): test_verify.py::test_r11_a_nondeterministic_transform_yields_all_four and ::test_a_data_dependent_replay_over_different_inputs_is_conforming got RunRefused('the recorded environment is not the executing environment ...') instead of RunMinted. Both pass under just test-one in isolation (2 passed, 24.9 s), and the next just test-fast passed them. The refusal points at an environment fingerprint that differs between recording and execution when many workers run at once; the cause is not diagnosed. A flaky refusal in the non-N2 phase stops just test before N2 and TypeScript run.

## Notes

- 2026-10-29T12:52:09Z (add): created
  provenance: {"harness_session":"claude-code:a586de0e-bccf-4067-9940-3b6ecc9e67a2","harness_session_source":"CLAUDE_CODE_SESSION_ID","origin":"agent"}
