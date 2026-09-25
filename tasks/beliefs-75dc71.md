---
id: beliefs-75dc71
title: "Adopt host-budget: test-fast -n auto under host-budget run; test_n2 WORKERS from OPS_WORKERS; CI sets OPS_WORKERS"
status: done
priority: 2
size: s
complexity: low
process: direct
owner: main
created: 2026-09-24T19:38:55Z
updated: 2026-09-25T15:32:01Z
started: 2026-09-25T15:17:14Z
completed: 2026-09-25T15:32:01Z
depends: []
tags: [testing]
source: ops-6d19bb
model: claude-opus-5-5
agent: claude-code/claude-opus-5-5
---

ops docs/specs/2026-09-24-host-budget-design.md, Consumers and CI. test_n2.py's WORKERS = 24 reads OPS_WORKERS and fails naming host-budget run or OPS_WORKERS=<n> when unset. test runs under host-budget run. ci.yml's Python job sets OPS_WORKERS: 4 (public repository, 4 vCPUs) in the same commit.

## Notes

- 2026-09-25T15:17:14Z (main): started
  provenance: {"harness_session":"claude-code:a80a2e70-e4ce-4a9b-887c-fc0b56920174","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-25T15:32:01Z (beliefs-75dc71): done
  provenance: {"harness_session":"claude-code:a80a2e70-e4ce-4a9b-887c-fc0b56920174","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-25T15:32:01Z (beliefs-75dc71): test and test-fast (and the pre-push hook) run under host-budget run; test-fast uses -n auto; test_n2 sizes its pool from OPS_WORKERS with the nested-pools share, refusing when unset; ci.yml's Python job sets OPS_WORKERS=4
  provenance: {"harness_session":"claude-code:a80a2e70-e4ce-4a9b-887c-fc0b56920174","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
