---
id: beliefs-86b150
title: "Open the audit and re-check operation kinds: T2's remainder"
status: todo
priority: 3
size: m
complexity: mid
created: 2026-09-20T15:17:59Z
updated: 2026-09-22T02:25:32Z
depends: []
tags: [migration, act-report]
agent: "claude-code/claude-opus-5[1m]"
---

act-report-remainder after cut 35: T2 reads every built operation kind; audit and re-check have no boundary that opens an intent and mints a report (act-report design §4's wrapper). Surface: audit.py, world/audit.py, holdings/boundary.py — the world-read lane's column. Off the path.

## Notes

- 2026-09-22T02:25:32Z (design/l13-preimage): Shared-surface note (l13-preimage spec §8): cut 37 rewrites world/verify.py (the policy pass, _audit_log, LogSeam) and root.py (_read_preimage, _LOG_SEAM); a later act-report-remainder merge resolves toward it.
