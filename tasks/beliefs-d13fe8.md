---
id: beliefs-d13fe8
title: Deliver URL acquisition and act-report coverage
status: doing
priority: 2
size: l
complexity: high
process: planned
owner: url-retrieval
created: 2026-08-31T00:38:27Z
updated: 2026-09-20T01:49:37Z
started: 2026-09-20T01:29:45Z
depends: []
tags: [migration, acquisition, act-report]
spec: docs/superpowers/specs/2026-09-19-url-retrieval-design.md
---

Outcome: Beliefs acquires datasets through canonical URL locators under the banked network discipline and closes the act-report remainder with the new acquisition operation surface.

Acceptance evidence: Design and freeze the acquisition cut; implement canonicalization, network and redirect policy, provenance, refusal reporting, and same-root behavior; cover H4, G9, R10, T5, T7's same-root case and T1/T2/T4 with deterministic tests; update current status; and pass the complete gates.

Sources: `docs/plans/2026-08-29-implementation-roadmap.md` `url-retrieval` and `act-report-remainder`; `docs/designs/2026-08-10-verified-holdings-record-design.md`; and `docs/designs/2026-08-11-act-report-design.md`.

Uncertainty: Canonicalization and network discipline are banked, but the concrete retrieval cut and supported transport behavior are not planned.

## Notes

- 2026-09-12T16:26:55Z (main): Complexity high: Holdings sections 2-3 bank URL canonicalization and network discipline, and act-report section 4 fixes same-root provenance/report publication. The concrete acquisition cut must still compose redirect/address validation, bounded retrieval, refusals and atomic publication; no transport implementation plan settles those interactions.
- 2026-09-15T16:26:47Z (main): 2026-09-15: natural-systems v2 is a real consumer once its Dryad pilot sample is drawn (ns-006fda; framing §4: the survey corpus is random acquisition from repositories). A second corpus is the measurement the roadmap says may re-rank tier 1; until the pilot runs, url-retrieval stays off-path row 2 in breadth order.
- 2026-09-20T01:29:35Z (main): 2026-09-19: process planned — holdings §2–§3 bank canonicalization and network discipline but no transport plan settles how redirect/address validation, bounded retrieval, refusals and atomic publication compose; the lane opens as off-path row 1 after cut 34 (rule 6: no on-path lane, none open), carrying act-report-remainder (T1, T2, T4) as the ride-along; slice design → freeze cut 35 → plan → implement, in .worktrees/url-retrieval
- 2026-09-20T01:29:45Z (url-retrieval): started
  provenance: {"harness_session":"claude-code:6a1a6f7e-3a7e-43a0-bf2d-b496d4a671f1","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-20T01:29:45Z (url-retrieval): claimed by claude-code/claude-fable-5-1, pid 3578147, worktree .worktrees/url-retrieval (branch url-retrieval)
- 2026-09-20T01:49:37Z (url-retrieval): 2026-09-19: slice design drafted at 53bfd7a-amended (docs/superpowers/specs/2026-09-19-url-retrieval-design.md), 16 decisions, 25 declaration units for cut 35; two scope findings: T2 stays partial on the unbuilt audit and re-check operation kinds (decision 12), and the URL look appends a re-check holdings intent for its registration (decision 2, a dated note on holdings §3)
- 2026-09-20T01:49:37Z (url-retrieval): parked (waiting on user, review): review the slice design; on approval, write the implementation plan (writing-plans) in .worktrees/url-retrieval, then freeze cut 35
  provenance: {"harness_session":"claude-code:6a1a6f7e-3a7e-43a0-bf2d-b496d4a671f1","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
