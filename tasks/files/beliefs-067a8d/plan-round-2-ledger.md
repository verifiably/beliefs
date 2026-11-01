# Plan round 2 rulings — beliefs-067a8d

Review: claude-code/claude-opus-5-5 on frozen ab1f9a6 (plan-round-2-report.md). Controller: claude-code/claude-opus-5-5 (main session).
All 7 findings accepted and corrected in the next frozen plan revision; none deferred. The reviewer judged Ruling I1's reading of spec step 7 faithful and the sequence executable.

- Ruling I-A: accept. Global Constraints now say no .tt.toml reaches the registered main checkout before Task 9 Step 1, the branch carries the unintegrated activation commit from Task 8 Step 5 and the worktree runs policy-off from then; "Tasks 2 to 8 Step 4"; the activation commit is Task 8 Step 5's; that step cites Ruling I1. Why: constraints given to workers and reviewers must not contradict a step. Cost: none.
- Ruling I-B: accept. Every packet lists `git log --oneline origin/main..<sha>` and `git diff --stat origin/main <sha>`; Task 7 Step 5 rechecks the range before pushing; Task 9 Step 1 requires `git diff --name-only <published-merge-sha> HEAD` to list only tasks/*.md, else a new packet. Why: a push publishes every unpushed commit (main is 7 ahead today, including the ops-check v16 vendoring), and other lanes may merge meanwhile. Cost: a new packet round if another lane lands between approvals.
- Ruling M-1: accept; park text names the refspec push.
- Ruling M-2: accept; refusal resets the unpushed activation commit, changes rebuild it with a new packet.
- Ruling M-3: accept; `tasks start beliefs-067a8d` in the main checkout right after the merge.
- Ruling M-4: accept; Task 8 Step 5 refreshes the state-line list with git grep and edits the union.
- Ruling M-5: accept; activation push rows identified by target triple and rev equal to the pushed merge SHA.
