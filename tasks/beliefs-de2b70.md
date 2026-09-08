---
id: beliefs-de2b70
title: Ship the biology pack
status: done
priority: 2
size: s
owner: feat/domain-boundary-slice2
created: 2026-09-08T11:32:19Z
updated: 2026-09-08T23:03:14Z
depends: []
parent: beliefs-1ce152
tags: [domain]
plan: docs/superpowers/plans/2026-09-08-biology-pack.md
step: "Task 9: Ship the biology pack"
---

## Notes

- 2026-09-08T22:55:59Z (feat/domain-boundary-slice2): claimed by task9, pid 2
- 2026-09-08T22:57:38Z (feat/domain-boundary-slice2): RED ImportError on shipped_domain_contract; GREEN 5 biology tests + 5 shipped-base tests passed; pyright clean
- 2026-09-08T22:58:00Z (feat/domain-boundary-slice2): Ship biology pack with cached packaged contract loader and parity tests
- 2026-09-08T23:03:14Z (feat/domain-boundary-slice2): Round1 fix: shipped_domain_contract now validates namespace via contract.domain._name; added biology/../biology and dotted-name refusals; focused 12 tests, ruff, pyright clean
