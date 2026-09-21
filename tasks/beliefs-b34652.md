---
id: beliefs-b34652
title: Deliver event-level L8 and the log remainder
status: doing
priority: 2
size: l
complexity: high
process: planned
owner: main
created: 2026-08-31T00:38:27Z
updated: 2026-09-21T11:54:08Z
started: 2026-09-21T09:32:07Z
depends: [beliefs-d248ba]
tags: [migration, world-read, log]
spec: docs/superpowers/specs/2026-09-21-event-level-l8-design.md
plan: docs/superpowers/plans/2026-09-21-event-level-l8.md
---

Outcome: Beliefs extends the world-read lane with the event-level relation required by L8 and closes the assigned L4 and L10 log remainder as relabels; L1's persistence arms are re-homed to persistence-cut (beliefs-3ea822).

Acceptance evidence: freeze cut 36 (docs/designs/2026-09-21-conformance-cut-36.md); build the event domain, the witness predicate and the witness-asymmetric relation (spec docs/superpowers/specs/2026-09-21-event-level-l8-design.md); discharge L8 in full and L4 and L10 as relabels on the certified volume; update the adoption ledger and roadmap, re-homing L1; pass the complete gates.

Sources: docs/plans/2026-08-29-implementation-roadmap.md event-level-l8 and log-remainder; docs/designs/2026-08-03-tamper-evident-log-design.md §7; docs/designs/2026-08-22-log-verification-design.md §7, §10.7.

## Notes

- 2026-09-12T16:26:55Z (main): Complexity high: Log design section 7 defines event order via presence/exclusion across ordered cuts, while root.epochs_ordered implements only the cut predicate. The event relation and its coverage, corruption, divergence and refusal semantics still need a concrete design and conformance selection.
- 2026-09-21T09:32:07Z (main): Process planned: the event-level relation's design and cut plan do not exist (log design §7 defines event order; root.epochs_ordered implements only the cut predicate). Slice design → cut plan → freeze, in .worktrees/event-level-l8 as the world-read lane's worktree (roadmap rule 4).
- 2026-09-21T09:32:08Z (main): started
  provenance: {"harness_session":"claude-code:51515f65-ae75-4a25-83a1-28526d417cd6","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-21T09:32:08Z (main): claimed by claude-code/opus, pid 3174647
- 2026-09-21T09:53:53Z (event-level-l8): Spec drafted for review: L8 in full (event domain, witness predicate W, witness-asymmetric relation), L4/L10 relabels, L1 re-homed to persistence-cut (beliefs-3ea822) and left partial; cut 36 claimed.
