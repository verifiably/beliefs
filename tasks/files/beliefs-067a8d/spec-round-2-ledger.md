# Spec round 2 rulings — beliefs-067a8d

Review: claude-code/claude-opus-5-5 on frozen e2927dd (spec-round-2-report.md). Controller: claude-code/claude-opus-5-5 (main session).
All 10 findings accepted and corrected in the next frozen revision; none deferred. Round-1 M5 scope widened by Minor 2.

- Ruling I-A: accept. Baseline runs as PYTEST_ADDOPTS=-rs just test and records both phases' SKIPPED lines as the skip-reason baseline. Why: hosted acceptance compares against it and -q/-rfE prints no reasons. Cost (if wrong): a slightly longer baseline log; no command-string change.
- Ruling I-B: accept. Post-activation checks from registered main: test-one ran, hook check-code/test-push skipped with null outcomes, forced-failure fixture via test-one, activation hosted run meets acceptance; each recorded on the task. Why: task body and shared Task 7 require it; ops pilot did it. Cost: none.
- Ruling I-C: accept. Step 4 writes state-independent guide text, pre-activation state where a state must be named; activation commit and rollback update every policy/covered-ref line. Why: repo rule on stale current-facing claims. Cost: none.
- Ruling M1: accept; cite ops design 469140a.
- Ruling M2: accept; hook_repo copies tools/tt for every routing case; only the warning case adds .tt.toml.
- Ruling M3: accept; coverage test uses GitHub glob semantics (refs/heads/* needs **).
- Ruling M4: accept; every subprocess in test_front_door.py key-by-key, TT_FORCE/GITHUB_ACTIONS absent unless set.
- Ruling M5: accept; hook short-circuit cases added; real recipes exercised with just --set marker children.
- Ruling M6: accept; contract test that broad_targets entries name justfile tt targets.
- Ruling M7: accept; hook-pre-push named as a fourth stopping route (0 runs in October).
