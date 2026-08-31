---
id: beliefs-a7df71
title: Close L13 through a public preimage seam
status: todo
priority: 3
size: m
created: 2026-08-31T00:38:28Z
updated: 2026-08-31T00:38:28Z
depends: [atoms-38887b]
tags: [migration, cross-repo, log]
---

Outcome: Beliefs strengthens L13 from path evidence to held-copy byte matching through the narrow public Atoms preimage reader.

Acceptance evidence: Consume the reviewed seam delivered by `atoms-38887b`; design the Beliefs-side classification and refusal boundary; verify indexed preimage bytes under the correct lease and corruption semantics; discharge L13 with positive and negative evidence; update current status; and pass the complete gates.

Sources: `docs/plans/2026-08-29-implementation-roadmap.md` `l13-preimage`; `docs/designs/2026-08-03-tamper-evident-log-design.md`; and Atoms task `atoms-38887b`.

Uncertainty: Atoms has the internal verified reader but has not delivered the public seam, so the exact consumer interface remains pending there.
