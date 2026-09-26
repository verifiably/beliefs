---
id: beliefs-a77bf9
title: Balance the fast scheduler
status: todo
priority: 0
size: m
complexity: mid
process: direct
created: 2026-09-26T16:07:37Z
updated: 2026-09-26T16:21:22Z
depends: []
parent: beliefs-9b248a
tags: [testing]
agent: codex
plan: docs/superpowers/plans/2026-09-26-test-suite-latency.md
step: "Task 1: Balance the fast scheduler"
---

Measure loadfile versus loadgroup and adopt the faster unchanged non-N2 fast-loop selection. N2 runs outside xdist in the later full-gate phase.
