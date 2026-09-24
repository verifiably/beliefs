---
id: beliefs-75dc71
title: "Adopt host-budget: test-fast -n auto under host-budget run; test_n2 WORKERS from OPS_WORKERS; CI sets OPS_WORKERS"
status: todo
priority: 2
size: s
complexity: low
process: direct
created: 2026-09-24T19:38:55Z
updated: 2026-09-24T19:38:55Z
depends: []
tags: [testing]
source: ops-6d19bb
agent: claude-code/claude-opus-5-5
---

ops docs/specs/2026-09-24-host-budget-design.md, Consumers and CI. test_n2.py's WORKERS = 24 reads OPS_WORKERS and fails naming host-budget run or OPS_WORKERS=<n> when unset. test runs under host-budget run. ci.yml's Python job sets OPS_WORKERS: 4 (public repository, 4 vCPUs) in the same commit.
