---
id: beliefs-0f5112
title: "Test latency over limit: test-fast 91.312 s against 90 s"
status: doing
priority: 0
size: m
complexity: high
process: planned
owner: main
created: 2026-11-01T10:00:12Z
updated: 2026-11-01T11:26:48Z
started: 2026-11-01T10:47:23Z
depends: []
tags: [test-latency, testing]
source: "tt-latency:titan:2026-11-01T10:00:05Z"
---

Filed by tt-latency on titan: the median of successful, uncontended, unwidened runs over the trailing window is over the limit in latency.toml (ops). The beliefs project is halted while this task is open: tasks start refuses new lower-priority work there. Each pair in a `breach:` note below is an obligation on the host it names. Fix the suite, then run `tt-latency verify <this id> --after <remedy timestamp>` on each host named; the task closes when verify exits 0, and the tasks done message carries its output.

Process: planned

## Notes

- 2026-11-01T10:00:12Z (add): created
- 2026-11-01T10:00:15Z (main): breach: titan window 2026-10-25T10:00:05Z..2026-11-01T10:00:05Z: test-fast median 91.312 s, limit 90 s, 11 runs on 3 days
- 2026-11-01T10:47:23Z (main): started
- 2026-11-01T10:53:04Z (main): Investigation and scope options (planned path, trial-arm: not enrolled; read-only in main checkout, no worktree created): (1) Origin: automated tt-latency filing on titan (source tt-latency:titan:2026-11-01T10:00:05Z, no harness_session stamp); recorded human policy intent is in ops-8bfa85 and docs/superpowers/specs/2026-10-31-test-execution-policy-design.md. (2) Breach and cost evidence: 11 uncontended, unwidened test-fast runs in 2026-10-25T10:00:05Z..2026-11-01T10:00:05Z sorted to 78.333, 78.600, 81.027, 84.281, 86.058, 91.312 (median), 93.702, 98.167, 100.508, 102.419, 820.807 s vs 90 s limit; since beliefs-ce9d05 closed 2026-10-18 at 68.671 s median on 6,119 tests, 284 non-N2 tests landed (6,119 -> 6,403 across cuts 47-48, session sharing/publish/retire doors with 17 shared(certified_work) and 15 published_source real-root setups, and route/CI checks) atop ~507 worker-seconds in Snakemake workflow modules (test_boundary.py 149.8 s, test_replay.py 98.0 s, test_cut15_workflows.py 87.0 s, test_verify.py 61.6 s, test_assess.py 52.9 s, test_run_persistence.py 36.2 s), with post-window uncontended 6,385-6,403-test runs at 99.46-103.73 s. (3) Premise collision with live beliefs-067a8d: beliefs-067a8d (doing on main, pushed d6dab00 at 10:45Z, watching hosted run 41298875513 in Task 8) plans in Task 9 to activate .tt.toml (automatic_broad = false, broad_targets including test-fast), note retirement on beliefs-0f5112, and lift its timing halt; once .tt.toml lands on main, tt-latency verify reports titan/test-fast as not applicable (exit 1, never 0, contradicting the body's verify-exits-0 closeout), and until Task 9 integrates, main may gain only tasks/*.md commits without invalidating beliefs-067a8d's activation packet. (4) Scope options: (A, recommended) keep beliefs-0f5112 to design and prove a real under-90-second test-fast reduction in .worktrees/0f5112-test-latency without touching main code while beliefs-067a8d finishes activation, closing on paired alternating TT_FORCE=1 just test-fast benchmark proof once policy-off retires the tt-latency obligation (or tt-latency verify if policy stays enabled), because TT_FORCE=1 just test-fast remains AGENTS.md's ~90 s local certified-tuple capability sweep and CI runs non-N2 on every push; (B) defer to beliefs-067a8d Task 9 and close/drop beliefs-0f5112 as policy-retired once .tt.toml lands (no runtime optimization pass now); (C) hold beliefs-067a8d Task 9, merge a test-fast fix on main under enabled policy, close via 3 post-merge tt-latency verify runs, and rebuild beliefs-067a8d's activation packet afterward.
- 2026-11-01T10:53:07Z (main): parked (waiting on user, decision): User chooses scope among options A/B/C in the diagnosis note; on Option A (recommended), agent resumes beliefs-0f5112, creates and hydrates .worktrees/0f5112-test-latency without touching main code while beliefs-067a8d finishes activation, profiles the 6,403-test suite, and lays out concrete optimization approaches. Retained items on titan: none created. Session processes (host-load --section session): none left running.
- 2026-11-01T11:26:45Z (main): Retired obligation: titan test-fast is now a disabled broad target under beliefs' landed policy (.tt.toml automatic_broad = false, broad_targets includes test-fast), activated by merge 01eb638191bd44fe9bd2a715fcc7d6853b07cc6e pushed to origin main at 2026-11-01T11:25:32Z (beliefs-067a8d). The titan/test-fast latency obligation is not applicable from that revision (not met, not performance-verified). Removed only this incident's timing halt tag; the task's remaining scope (the parked A/B/C choice) is unchanged and stays with its owner and the user.
