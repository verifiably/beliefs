---
id: beliefs-a7df71
title: Close L13 through a public preimage seam
status: todo
priority: 3
size: m
complexity: high
created: 2026-08-31T00:38:28Z
updated: 2026-09-12T16:26:55Z
depends: [atoms-38887b]
tags: [migration, cross-repo, log]
---

Outcome: Beliefs strengthens L13 from path evidence to held-copy byte matching through the narrow public Atoms preimage reader.

Acceptance evidence: Consume the reviewed seam delivered by `atoms-38887b`; design the Beliefs-side classification and refusal boundary; verify indexed preimage bytes under the correct lease and corruption semantics; discharge L13 with positive and negative evidence; update current status; and pass the complete gates.

Sources: `docs/plans/2026-08-29-implementation-roadmap.md` `l13-preimage`; `docs/designs/2026-08-03-tamper-evident-log-design.md`; and Atoms task `atoms-38887b`.

Uncertainty: Atoms has the internal verified reader but has not delivered the public seam, so the exact consumer interface remains pending there.

## Notes

- 2026-09-11T14:34:29Z (main): Consumer scope for atoms-38887b: engine-produced replicas carry the project tree/chain but no local transaction records or preimage blobs; metadata is minted fresh and writable roots cannot be demoted. Read surviving preimages from the reachable writable source root, or classify from supplied held-copy history bytes; this task owns source-root selection and matching to the inspected chain. Transporting history into replicas is outside the approved Atoms seam.
- 2026-09-12T16:26:55Z (main): Complexity high: atoms-38887b has delivered the writable-source read_preimage contract; the original missing-seam uncertainty is resolved. Beliefs still owns source-root selection, matching held history to the inspected chain and classification/refusal semantics, including replicas without local transaction/preimage history.
