---
id: beliefs-75dc71
title: "Adopt host-budget: test-fast -n auto under host-budget run; test_n2 WORKERS from OPS_WORKERS; CI sets OPS_WORKERS"
status: doing
priority: 2
size: s
complexity: low
process: direct
owner: main
created: 2026-09-24T19:38:55Z
updated: 2026-09-25T15:17:14Z
started: 2026-09-25T15:17:14Z
depends: []
tags: [testing]
source: ops-6d19bb
agent: claude-code/claude-opus-5-5
---

ops docs/specs/2026-09-24-host-budget-design.md, Consumers and CI. test_n2.py's WORKERS = 24 reads OPS_WORKERS and fails naming host-budget run or OPS_WORKERS=<n> when unset. test runs under host-budget run. ci.yml's Python job sets OPS_WORKERS: 4 (public repository, 4 vCPUs) in the same commit.

## Notes

- 2026-09-25T15:17:14Z (main): started
  provenance: {"harness_session":"claude-code:a80a2e70-e4ce-4a9b-887c-fc0b56920174","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
