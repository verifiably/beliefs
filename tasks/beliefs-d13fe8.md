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
updated: 2026-09-20T10:53:59Z
started: 2026-09-20T01:29:45Z
depends: []
tags: [migration, acquisition, act-report]
spec: docs/superpowers/specs/2026-09-19-url-retrieval-design.md
plan: docs/superpowers/plans/2026-09-20-url-retrieval.md
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
- 2026-09-20T09:20:26Z (url-retrieval): resumed
  provenance: {"harness_session":"claude-code:6a1a6f7e-3a7e-43a0-bf2d-b496d4a671f1","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-20T09:25:54Z (url-retrieval): 2026-09-20: first review's six findings applied (spec §17): shared intent source and evidence key (BI-10), hop named by ordinal and category only, refused hop is retrieval-failed, faithful request target and Host, materialization refusal is a stop with AcquisitionOutcome.stop, incomplete body yields no finalized digest; 26 declaration units
- 2026-09-20T09:25:54Z (url-retrieval): parked (waiting on user, review): second review of the revised slice design; on approval, write the implementation plan (writing-plans) in .worktrees/url-retrieval, then freeze cut 35
  provenance: {"harness_session":"claude-code:6a1a6f7e-3a7e-43a0-bf2d-b496d4a671f1","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-20T09:31:58Z (url-retrieval): resumed
  provenance: {"harness_session":"claude-code:6a1a6f7e-3a7e-43a0-bf2d-b496d4a671f1","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-20T09:31:58Z (url-retrieval): 2026-09-20: second review's blocker applied — write wraps exactly the store_write call as StoreWriteRefused; acquire catches only that; intent, publication and session failures propagate; BI-11 added (27 units)
- 2026-09-20T09:31:58Z (url-retrieval): parked (waiting on user, review): third review of the slice design (decision 10, §6, BI-11); on approval, write the implementation plan (writing-plans) in .worktrees/url-retrieval, then freeze cut 35
  provenance: {"harness_session":"claude-code:6a1a6f7e-3a7e-43a0-bf2d-b496d4a671f1","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-20T09:37:06Z (url-retrieval): resumed
  provenance: {"harness_session":"claude-code:6a1a6f7e-3a7e-43a0-bf2d-b496d4a671f1","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-20T09:37:06Z (url-retrieval): 2026-09-20: third review's blocker applied — StoreWriteRefused only for applied==0 with a ProjectApprovalRefused, PreconditionRefused or PendingUnresolved cause (store_refusal); unexpected engine failures propagate; BI-11 negative and second sabotage arm; §5 corrected
- 2026-09-20T09:37:06Z (url-retrieval): parked (waiting on user, review): fourth review of the slice design (decision 10 cause set, BI-11); on approval, write the implementation plan (writing-plans) in .worktrees/url-retrieval, then freeze cut 35
  provenance: {"harness_session":"claude-code:6a1a6f7e-3a7e-43a0-bf2d-b496d4a671f1","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-20T09:39:54Z (url-retrieval): resumed
  provenance: {"harness_session":"claude-code:6a1a6f7e-3a7e-43a0-bf2d-b496d4a671f1","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-20T09:40:19Z (url-retrieval): 2026-09-20: design approved for implementation planning at 395b550 after four reviews; BI-11a fixture detail applied; next: implementation plan, then freeze cut 35
- 2026-09-20T10:11:16Z (url-retrieval): 2026-09-20: implementation plan drafted at docs/superpowers/plans/2026-09-20-url-retrieval.md (10 tasks, step children beliefs-4b4317..cb43c2); four planning corrections recorded in its self-review for spec §17 at Task 0
- 2026-09-20T10:11:16Z (url-retrieval): parked (waiting on user, review): review the implementation plan; on approval, execute Task 0 (freeze cut 35) onward in .worktrees/url-retrieval via subagent-driven development
  provenance: {"harness_session":"claude-code:6a1a6f7e-3a7e-43a0-bf2d-b496d4a671f1","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-20T10:37:01Z (url-retrieval): plan revised after review 1 (11 findings, all confirmed against the tree): close takes session then root via a hold and rebuilds the view; transport failures by fixed category, HTTPException classified, scratch cleaned; canonical trailing slash, IPv6 brackets, port 0 refused; bounded reads, finite timeout; look's scratch exclusion; dataset shape before the intent; survey as adapter only; in-process TLS server with a committed test cert; T4-a/BI-2/BI-1 corrected
- 2026-09-20T10:48:22Z (url-retrieval): plan revised after review 2 (4 findings, confirmed): server-supplied hops validated before urljoin/urlsplit under a sixth category 'malformed'; IPv6 brackets kept in the transmitted Host with an IP SAN on the test cert; dot-segment removal is RFC 3986 §5.2.4 verbatim (/a//. is /a//); look's scratch cleanup spans record construction
- 2026-09-20T10:53:59Z (url-retrieval): 2026-09-20: implementation plan approved at 69c0d64 after two reviews (15 findings applied, all confirmed against the tree); eighteen planning corrections (a)-(r) queued for spec §17 at Task 0; execution not started — paused at the user's request
- 2026-09-20T10:53:59Z (url-retrieval): parked (waiting on user, approval): execute Task 0 (freeze cut 35; record corrections (a)-(r) in spec §17) onward in .worktrees/url-retrieval via subagent-driven development, one foreground implementer per task
  provenance: {"harness_session":"claude-code:6a1a6f7e-3a7e-43a0-bf2d-b496d4a671f1","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
