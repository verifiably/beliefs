---
id: beliefs-3eb090
title: Fix facet-contract final integration review findings
status: done
priority: 1
size: m
owner: feat/domain-boundary
created: 2026-09-07T15:48:33Z
updated: 2026-09-07T16:43:45Z
depends: []
parent: beliefs-bc3aff
tags: [facet-contracts]
---

Resolve I1-I4 and M1/M2/M4 from final integration review; rerun serial gates and certified cut20 aggregate without changing frozen evidence.

## Notes

- 2026-09-07T15:48:41Z (feat/domain-boundary): claimed by final_fix, controller pid 205053
- 2026-09-07T15:58:57Z (feat/domain-boundary): I1-I4 portable RED/GREEN plus durable ordinary/session pending-recovery RED/GREEN; M1 exact loss-check bypass fails, M2 AST identical, M4 current narrative corrected. Static gate passed with zero task warnings.
- 2026-09-07T16:43:45Z (feat/domain-boundary): Final stable gates passed: 4048 Python, 137 TS, complete cut20 aggregate (17 durable + 5 final checks, 27 session prerequisite checks), just check zero errors/warnings; UV_NO_SYNC=1 authorized for external metadata-only rename, runtime hashes unchanged.
- 2026-09-07T16:43:45Z (feat/domain-boundary): Closed I1-I4 and M1/M2/M4 with focused regressions, full serial gates and certified cut20 replay on stable runtime inputs.
