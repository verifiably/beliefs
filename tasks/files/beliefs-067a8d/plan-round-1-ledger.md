# Plan round 1 rulings — beliefs-067a8d

Review: claude-code/claude-opus-5-5 on frozen 224c799 (plan-round-1-report.md). Controller: claude-code/claude-opus-5-5 (main session).
All 12 findings accepted and corrected in the next frozen plan revision; none deferred.

- Ruling I1: accept. Global constraint: task commands run in the worktree until Task 7's merge and in the main checkout after it; every push names its approved commit by refspec `<sha>:refs/heads/main`. The publication packet names the merge SHA and states that later tasks/*.md commits stay local. The activation commit is built and focus-checked on the branch before the activation packet (Task 8 Step 5), the packet names that SHA and the --no-ff merge it authorizes, and Task 9 only integrates, pushes and verifies. Why: approval must cover the exact pushed commit, and spec step 7 asks for the exact activation commit in the packet. This reads spec step 7's "commit .tt.toml after approval" as integrating the commit into the registered main checkout after approval; the branch commit lives in the worktree's own Git top level and changes no registered policy. Cost (if wrong): the activation commit exists on the branch before approval and would have to be reverted if approval is refused.
- Ruling I2: accept. The Vitest probe runs through `just --set one_cmd "cd ts && npx --no-install vitest run" test-one --root <dir> --globals …` with import-free globals test files. Why: the front door records runs and the scratch files cannot resolve the vitest package. Cost: none.
- Ruling I3: accept. Global constraint: suite and focused runs start from the physical worktree path (`cd "$(pwd -P)"`). Why: the .worktrees symlink spelling causes ELOOP failures in atoms' open_root. Cost: none.
- Ruling M1: accept; hygiene-stops arm runs with no policy and asserts exactly one hook row with exit 7.
- Ruling M2: accept; nested case asserts only the outer row, ran with nonzero exit.
- Ruling M3: accept; inventory fixture copies the live manifest; Checkout root is tmp/"checkout".
- Ruling M4: accept; tests construct Checkout(tmp_path) directly, no shared fixture import.
- Ruling M5: accept; baseline expectation about 6,300+ non-N2 passed.
- Ruling M6: accept; status line records round 5 as relayed by the user, who asked for its two revisions before planning, and claims no approval beyond the record.
- Ruling M7: accept; Task 6 rewrites the .githooks/pre-commit header state-independently and notes every state line it and Task 5 write; the activation commit edits exactly those.
- Ruling M8: accept; Task 3 RED names the cases that pin existing tt v9 behaviour; enabled-hook rows worded per hook.
- Ruling M9: accept; fixture skip uses runtime pytest.skip with the conftest prefix; keepalive test installs capture_hook_recipe().
