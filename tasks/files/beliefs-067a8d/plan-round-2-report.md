# Plan round 2 review — beliefs-067a8d

Reviewer: claude-code/claude-opus-5-5 (fresh read-only Claude Code subagent dispatched by the controller).
Revision reviewed: beliefs ab1f9a6:docs/superpowers/plans/2026-11-01-test-execution-policy.md (scoped re-review of the diff from 224c799), spec content 68fa37f.
Verdict: revise. Critical 0, Important 2, Minor 5.

## Ruling I1 assessment

Faithful: yes. Spec step 7 requires both "the exact activation commit" in the packet and committing only after approval; what it guards is that policy-off never takes effect in the registered checkout before approval and that the approver sees exactly what lands. Building A on the design branch and integrating after approval keeps both: tools/tt read_policy reads only the invoking Git top level, so a worktree .tt.toml never reaches main-checkout runs, and main carries no .tt.toml until Task 9 Step 1's merge.

Executable as traced: after Task 7's merge the branch ends at D, A's parent is D, merge-base(main, A) is D, main gains only tasks/*.md between merges, so Task 9's --no-ff merge brings A's diff alone with no conflict. A's commit in the worktree runs the worktree's hooks (relative core.hooksPath), full hook-pre-commit, worktree .tt.toml makes hygiene run and check-code skipped, hence Task 8 Step 5's focused checks plus TT_FORCE=1 just check-code. The Task 9 merge in main runs no gate (no pre-merge-commit hook); acceptable since A's tree was checked. The refspec push `git push origin <sha>:refs/heads/main` gives a stdin line with four fields and valid oids, routes on the remote ref, $1 is origin, ci_suite_refs is refs/heads/* after merge, so hook-pre-push-fast; main holds .tt.toml, so hygiene runs and check-code and test-push skip, as Task 9 Step 2 expects. Task 7's publication push routes fast with policy enabled.

## Round-1 findings

I1 partly (gaps I-A, I-B, M-1); I2 yes; I3 yes; M1-M5 yes; M6 yes ("who asked for its two revisions" relies on session context; the record holds only "relayed by user"); M7 yes (grep at ab1f9a6 finds only lines inside Task 5/6 scope); M8 yes (test_failure_stops_later_steps still fails at RED via its FAIL_STEP=uv arm); M9 yes.

## Important

I-A. Global Constraints contradict Task 8 Step 5: "No .tt.toml enters the tree before Task 9", "ci_suite_refs stays refs/heads/main until the Task 9 activation commit" and "Policy is absent (enabled) through Tasks 2 to 8", while Task 8 Step 5 now writes .tt.toml, sets refs/heads/* and commits in Task 8. An executor, worker or reviewer given these constraints hits a contradiction, and the user reading the activation packet's plan would believe no policy-off file exists before Task 9; from Task 8 Step 5 the worktree itself runs policy-off. Fix: "No .tt.toml reaches the registered main checkout before Task 9 Step 1; the design branch carries the unintegrated activation commit from Task 8 Step 5, and the worktree runs under policy-off from then on"; "Tasks 2 to 8 Step 4"; "the activation commit (Task 8 Step 5)"; Task 8 Step 5 cites Ruling I1.

I-B. Approval does not bound everything the push publishes. Pushing M publishes origin/main..M. Today main is 7 commits ahead of origin/main, including 405f249 chore(tools): vendor ops-check version 16, which no packet names. Two other locked lanes exist (918fd2-overlapping-publications, ce9d05-test-latency); if either merges into local main between Task 7 and Task 9 the activation push publishes it under an approval claiming only tasks/*.md other content. Task 9 Step 1 checks only diff(main_prev, merge) == diff(A), never main_prev against the last approved push; another lane could add a current-state line A does not update. Fix: each packet lists `git log --oneline origin/main..<sha>` and `git diff --stat origin/main <sha>`; before Task 7 Step 5's push confirm origin/main..<merge-sha> matches the packet; Task 9 Step 1 requires `git diff --name-only <published-merge-sha> HEAD` to list only tasks/*.md before merging, else stop, rebuild A and re-present.

## Minor

M-1. Task 7 Step 4's park text says approval covers "git push origin main of the named commit"; say `git push origin <merge-sha>:refs/heads/main`.
M-2. No path if activation is refused or revised: on refusal reset the worktree to the pre-activation tip (A unpushed, unmerged) and note it; on requested changes rebuild A and present a new packet with the new SHA.
M-3. The task claim does not move to the main checkout after the merge (owner is the branch); run `tasks start beliefs-067a8d` in the main checkout right after the merge. Failure unverified (claim-guard may warn or refuse).
M-4. The state-line list covers only Tasks 5 and 6; Task 3 comments and Task 7 corrective rounds may add lines. In Task 8 Step 5 refresh it against the integrated tree with `git grep -n "refs/heads/main\|origin/main\|policy enabled"` over AGENTS.md, justfile, python/README.md and .githooks, and edit the union.
M-5. Task 9 Step 2's skipped rows are ambiguous with Task 8 Step 5's pre-commit row; identify the activation push's rows by hook-pre-push-fast, check-code, test-push with rev equal to the pushed merge SHA.

## Checked and fine

Pre-push routing reads f[2]/f[1]/f[3], a SHA source keeps the line valid, $1 is origin; read_policy reads only the invoking top level; protected targets include check-hygiene; hosted refusal before any row; owner_of and rev from the cwd checkout; relative hooksPath in linked worktrees; merges trigger no pre-commit gate; activation pre-commit skips check-code as the spec anticipates; test-push skipped at the merge push; Vitest probe matches test-one and ts/package.json (vitest 4, no config); conftest skip prefix matches conftest.py:56; M3 sibling path arithmetic; nodes Checkout precedent; Task numbering consistent; no other changes in the diff.
