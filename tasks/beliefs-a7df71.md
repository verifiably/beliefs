---
id: beliefs-a7df71
title: Close L13 through a public preimage seam
status: done
priority: 3
size: m
complexity: high
process: planned
owner: design/l13-preimage
created: 2026-08-31T00:38:28Z
updated: 2026-09-22T09:18:31Z
started: 2026-09-22T00:12:25Z
completed: 2026-09-22T09:18:31Z
depends: [atoms-38887b]
tags: [migration, cross-repo, log]
spec: docs/superpowers/specs/2026-09-21-l13-preimage-design.md
plan: docs/superpowers/plans/2026-09-21-l13-preimage.md
---

Outcome: Beliefs strengthens L13 from path evidence to held-copy byte matching through the narrow public Atoms preimage reader.

Acceptance evidence: Consume the writable-source `read_preimage` seam `atoms-38887b` delivered on 2026-09-11; design the Beliefs-side classification and refusal boundary; verify indexed preimage bytes under the correct lease and corruption semantics; discharge L13 with positive and negative evidence; update current status; and pass the complete gates.

Sources: `docs/plans/2026-08-29-implementation-roadmap.md` `l13-preimage`; `docs/designs/2026-08-03-tamper-evident-log-design.md`; and Atoms task `atoms-38887b`.

Uncertainty: The Atoms seam is delivered and writable-only, so nothing outside this task must land first; the roadmap ranks it tier 1 off the path (row 4, after event-level L8). What is undesigned is the Beliefs side: source-root selection, matching held history to the inspected chain, and the classification and refusal semantics — including replicas that carry no local transaction or preimage history.

## Notes

- 2026-09-11T14:34:29Z (main): Consumer scope for atoms-38887b: engine-produced replicas carry the project tree/chain but no local transaction records or preimage blobs; metadata is minted fresh and writable roots cannot be demoted. Read surviving preimages from the reachable writable source root, or classify from supplied held-copy history bytes; this task owns source-root selection and matching to the inspected chain. Transporting history into replicas is outside the approved Atoms seam.
- 2026-09-12T16:26:55Z (main): Complexity high: atoms-38887b has delivered the writable-source read_preimage contract; the original missing-seam uncertainty is resolved. Beliefs still owns source-root selection, matching held history to the inspected chain and classification/refusal semantics, including replicas without local transaction/preimage history.
- 2026-09-16T10:02:59Z (main): 2026-09-16 doc review: atoms-38887b closed 2026-09-11, so the prerequisite is met; roadmap moved l13-preimage to tier 1 off the path (row 4) and the ledger row names the landed seam. Body's uncertainty rewritten to match; the 2026-09-11 consumer-scope note stands.
- 2026-09-22T00:12:10Z (main): process planned: the Beliefs-side classification boundary (source-root selection, held-copy matching, refusal semantics for history-less replicas) is undesigned; slice design then plan before the cut. Opened as roadmap tier-1 off-path row 1 after cut 36; lane cross-repo, worktree .worktrees/l13-preimage
- 2026-09-22T00:12:25Z (design/l13-preimage): started
  provenance: {"harness_session":"claude-code:d086e462-1230-46b7-9dda-e4f7bef8146f","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-22T00:12:25Z (design/l13-preimage): claimed by claude-code/claude-opus-5[1m], pid 1533210, session d086e462-1230-46b7-9dda-e4f7bef8146f; next: brainstorm the l13-preimage slice design
- 2026-09-22T00:28:39Z (design/l13-preimage): parked (waiting on user, review): review docs/superpowers/specs/2026-09-21-l13-preimage-design.md; on approval, writing-plans for cut 37 in .worktrees/l13-preimage
  provenance: {"harness_session":"claude-code:d086e462-1230-46b7-9dda-e4f7bef8146f","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-22T00:43:02Z (design/l13-preimage): resumed
  provenance: {"harness_session":"claude-code:d086e462-1230-46b7-9dda-e4f7bef8146f","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-22T01:25:44Z (design/l13-preimage): parked (waiting on user, review): review docs/superpowers/plans/2026-09-21-l13-preimage.md (cut 37, 8 tasks); on approval, execute via subagent-driven-development in .worktrees/l13-preimage starting at Task 0 (beliefs-e20786)
  provenance: {"harness_session":"claude-code:d086e462-1230-46b7-9dda-e4f7bef8146f","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-22T01:47:18Z (design/l13-preimage): parked (waiting on user, review): plan review round 1 applied (5/5); on approval, execute via subagent-driven-development from Task 0 (beliefs-e20786) in .worktrees/l13-preimage
  provenance: {"harness_session":"claude-code:d086e462-1230-46b7-9dda-e4f7bef8146f","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-22T02:20:52Z (design/l13-preimage): resumed
  provenance: {"harness_session":"codex:01a0c6e5-2757-7613-baea-904797ce0e78","harness_session_source":"CODEX_SESSION_ID"}
- 2026-09-22T02:25:32Z (design/l13-preimage): Cut 37 frozen (docs/designs/2026-09-21-conformance-cut-37.md): 11 units, 15 arms; chains cut 36; cut 8's L13u1–u3 recorded stale at Task 1.
- 2026-09-22T06:16:47Z (design/l13-preimage): parked (waiting on user, approval): choose integration for the reviewed, gate-green design/l13-preimage branch
  provenance: {"harness_session":"codex:01a0c6e5-2757-7613-baea-904797ce0e78","harness_session_source":"CODEX_SESSION_ID"}
- 2026-09-22T09:18:30Z (design/l13-preimage): resumed
  provenance: {"harness_session":"codex:01a0c6e5-2757-7613-baea-904797ce0e78","harness_session_source":"CODEX_SESSION_ID"}
- 2026-09-22T09:18:31Z (design/l13-preimage): done
  provenance: {"harness_session":"codex:01a0c6e5-2757-7613-baea-904797ce0e78","harness_session_source":"CODEX_SESSION_ID"}
- 2026-09-22T09:18:31Z (design/l13-preimage): cut 37 discharged: L13 in full — digest-matched classification over held copies and surviving preimages, absence stated, corruption refused
  provenance: {"harness_session":"codex:01a0c6e5-2757-7613-baea-904797ce0e78","harness_session_source":"CODEX_SESSION_ID"}
