---
id: beliefs-afbbff
title: "Deliver the writer session, session ledger, and corpus-write amendment"
status: doing
priority: 1
size: xl
owner: feat/writer-session
created: 2026-08-31T21:28:39Z
updated: 2026-09-05T10:04:18Z
depends: [beliefs-96a24a]
tags: [writer, sessions]
spec: docs/designs/2026-09-05-writer-session-design.md
---

Sub-project 2's beliefs half beyond permits (beliefs-96a24a): open_attended_session with fresh session identity and endpoint-set actor; WriterSession.scoped(required) returning an invocation-scoped writer; the session ledger (invocation-open/act/invocation-close with persisted refusal envelopes) at <operations root>/sessions/; every session-mediated ordinary corpus write as intent+fulfillment via a versioned act-report amendment adding the corpus-write operation kind; crash reconciliation (chains are truth, ledger is evidence). Contract: the science repo's docs/specs/2026-08-31-command-framework-design.md §§4-5 and its plan's Task 12 Consumes block.

## Notes

- 2026-09-04T21:40:11Z (main): write-permit exports live at beliefs merge commit da37650: RequiredCapabilities, KIND_ACTS, and PermitExceeded
- 2026-09-05T08:28:16Z (feat/writer-session): claimed by Claude Code (Fable 5.1), pid 3136796; brainstorming in .worktrees/writer-session
- 2026-09-05T09:17:36Z (feat/writer-session): design banked at docs/designs/2026-09-05-writer-session-design.md; cut 19 freezes after review; J1-J10; session lane touches corpus.py and report.py
- 2026-09-05T09:53:23Z (feat/writer-session): review 1 resolved: scoped(required, invocation_id) and open_attended_session(coordination=) are change requests to science Task 12; J11 added; reconciliation under the corpus lock via detached inspection
- 2026-09-05T10:04:18Z (feat/writer-session): review 2 resolved: PlanRefused(WriteRefused) from preflight; abandoned invocations stay open, fresh claims proceed; J2 bounded at submission; reconcile takes the whole ChainView incl. pending; adoption and a well-formed chain required at open
