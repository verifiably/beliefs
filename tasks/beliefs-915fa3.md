---
id: beliefs-915fa3
title: The check and the audit take the profile; the stopping matrix
status: done
priority: 2
size: m
owner: feat/domain-boundary
created: 2026-09-05T23:36:55Z
updated: 2026-09-07T11:09:45Z
depends: [beliefs-91dfdc]
parent: beliefs-bc3aff
tags: [domain]
plan: docs/superpowers/plans/2026-09-05-facet-contracts.md
step: "Task 11: The check and the audit take the profile; the stopping matrix"
---

## Notes

- 2026-09-07T09:50:38Z (feat/domain-boundary): claimed by /root/task11, pid 205053
- 2026-09-07T10:04:25Z (feat/domain-boundary): Task11: implemented three-value shared pin comparison, profile-aware check/audit stopping matrix, unvalidated neighbours, caller migrations; focused suite and 82 durable caller tests pass. Guard-bypass checks and final gates in progress.
- 2026-09-07T10:25:09Z (feat/domain-boundary): Full gate 1:3796 passed,2 failed only on existing unreadable-manifest diagnostic wording. Restored wording without weakening tests; complete profile-agreement/check/audit/pin focus145 passed, Ruff/Pyright clean. Retrying full serial pytest with -x.
- 2026-09-07T10:42:25Z (feat/domain-boundary): Profile-aware check and audit implement the stopping matrix with unvalidated neighbours; 3798 Python tests and all static/TS gates pass.
- 2026-09-07T10:49:50Z (feat/domain-boundary): Review fix1: paired RED reproduces stray coordination hiding base supersession-target-missing; condition now respects coordination withholding while genuine coordination exemption remains.
- 2026-09-07T11:09:45Z (feat/domain-boundary): Review fix1 complete: base supersession finding survives stray coordination during pin mismatch; paired RED/GREEN and bypass,116 focused,22 durable,3800 full Python,static and TS gates pass.
