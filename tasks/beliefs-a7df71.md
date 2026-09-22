---
id: beliefs-a7df71
title: Close L13 through a public preimage seam
status: doing
priority: 3
size: m
complexity: high
process: planned
owner: design/l13-preimage
created: 2026-08-31T00:38:28Z
updated: 2026-09-22T00:28:31Z
started: 2026-09-22T00:12:25Z
depends: [atoms-38887b]
tags: [migration, cross-repo, log]
spec: docs/superpowers/specs/2026-09-21-l13-preimage-design.md
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
