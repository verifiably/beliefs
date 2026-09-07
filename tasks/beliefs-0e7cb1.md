---
id: beliefs-0e7cb1
title: "Python CI cannot meet the certified tuple: decide what CI runs"
status: todo
priority: 1
size: s
created: 2026-09-07T14:32:04Z
updated: 2026-09-07T14:39:23Z
depends: []
tags: [testing]
---

The first full CI run (34129604930, 2026-09-07) came back 3556 passed, 183 failed in 22m23s on both 3.11 and 3.13. Every failure is one cause: atoms.core.errors.CapabilityUnavailable, 'ext4 feature masks unresolvable: the kernel does not support EXT4_IOC_GET_TUNE_SB_PARAM', from atoms/python/src/atoms/fs/volume.py:303. A stock GitHub runner has no certified ext4 kernel and volume tuple, so those tests cannot pass there.

Concentrated in tests/test_permit_entry_points.py, test_holdings_boundary.py, test_succession.py, test_restore_root.py and test_fork_acts.py.

This is a policy question, not a configuration one. AGENTS.md says CapabilityUnavailable is a fail-closed result, not a waiver, and that the suite runs on the certified tuple 'or report the exact mismatch'. Options:

1. TypeScript-only CI, with the Python suite staying local behind the pre-push gate, documented as requiring the certified tuple. Honest, cheap, and loses remote coverage of 3556 passing tests.
2. Run the Python suite in CI and report the mismatch rather than waive it: a job that expects the capability-dependent set to be unavailable and fails only on anything else. Uses the 'or report' branch of the rule, and needs a way to name that set that does not become a silent skip list.
3. A self-hosted runner on the certified host. Full fidelity, real operational cost.

Until this is decided CI is red on main, which trains people to ignore it. TypeScript is green on both Node versions and is not implicated.

## Notes

- 2026-09-07T14:39:23Z (main): Marking by hand is not viable: the 183 failures are subsets of 14 files, not whole modules — test_succession 43 of 49, test_permit_entry_points 29 of 96, test_operation_port 10 of 32, test_session_reconcile 1 of 19, and only test_holdings_windows fails entirely (5 of 5). So a module-level pytestmark cannot express it; it would take 183 per-test annotations across 14 files, which is exactly the skip list that rots.
