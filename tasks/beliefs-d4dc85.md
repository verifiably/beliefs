---
id: beliefs-d4dc85
title: Adopt the ops act design's front door
status: done
priority: 2
size: s
complexity: low
process: direct
owner: chore/beliefs-d4dc85
created: 2026-09-28T10:27:58Z
updated: 2026-09-29T18:42:42Z
started: 2026-09-29T18:37:07Z
completed: 2026-09-29T18:42:42Z
depends: []
tags: [testing]
source: ops-a5a7ef
agent: claude-code/claude-opus-5-5
---

ops docs/specs/2026-09-28-test-ci-act-design.md §7.3. Copy templates/justfile's test-one, the docs-only pre-commit path and the CI-aware pre-push gate (ci_suite_refs, ci_remote, push_fast_cmd, hook-pre-push-fast) with both templates/githooks; set ci_suite_refs from what CI runs the full suite for and note it; AGENTS.md Gates line per templates/AGENTS.md. Its existing `hook-pre-commit-docs` is replaced by the template's classification (allowlist, not the `python/` `ts/` denylist).

## Notes

- 2026-09-29T18:37:07Z (chore/beliefs-d4dc85): started
  provenance: {"harness_session":"codex:01a0ee73-b5be-7b82-b996-1fe68e601881","harness_session_source":"CODEX_SESSION_ID"}
- 2026-09-29T18:37:07Z (chore/beliefs-d4dc85): claimed by Codex; process direct in .worktrees/beliefs-d4dc85; native session claim supplies liveness
- 2026-09-29T18:39:35Z (chore/beliefs-d4dc85): claimed by Codex, harness pid 3949212; CI push trigger covers only refs/heads/main on origin. Adopt fixed push fast set: parallel non-N2 Python plus full TS, since unbased vitest --changed misses clean-tree committed changes. Narrow docs_paths to AGENTS.md and tasks/*.md because README/docs are conformance inputs. Regression red: 5 failures in old classifiers/missing test-one.
- 2026-09-29T18:42:34Z (chore/beliefs-d4dc85): Review clear after fixing CI portability: contract test stubs host-budget (CI has no host tool) while production recipe retains it. Focused 11 tests pass; fast Python suite 5858 passed, 1 skipped; Vitest focused identity-v1 24 passed. N2 unchanged and not rerun for front-door adoption.
- 2026-09-29T18:42:42Z (chore/beliefs-d4dc85): done
  provenance: {"harness_session":"codex:01a0ee73-b5be-7b82-b996-1fe68e601881","harness_session_source":"CODEX_SESSION_ID"}
- 2026-09-29T18:42:42Z (chore/beliefs-d4dc85): Adopted recorded test-one, conservative docs allowlist and origin/main CI-aware push gate; 11 regression tests, fast suite, 155 TS tests and just check passed.
  provenance: {"harness_session":"codex:01a0ee73-b5be-7b82-b996-1fe68e601881","harness_session_source":"CODEX_SESSION_ID"}
