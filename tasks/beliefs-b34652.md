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
updated: 2026-09-21T09:32:08Z
started: 2026-09-21T09:32:07Z
depends: [beliefs-d248ba]
tags: [migration, world-read, log]
---

Outcome: Beliefs extends the world-read lane with the event-level relation required by L8 and closes the assigned L1, L4, and L10 log remainder.

Acceptance evidence: After world resolution lands, freeze and implement the event-level successor to ordered cuts; add positive, divergence, corruption, and relabel evidence; discharge L8 and the ride-along rows; update the adoption ledger and roadmap; and pass the complete gates.

Sources: `docs/plans/2026-08-29-implementation-roadmap.md` `event-level-l8` and `log-remainder`; `docs/designs/2026-08-03-tamper-evident-log-design.md`; and `docs/designs/2026-08-22-log-verification-design.md`.

Uncertainty: The ordered-cuts predicate exists, but the event-level relation's design and cut plan do not.

## Notes

- 2026-09-12T16:26:55Z (main): Complexity high: Log design section 7 defines event order via presence/exclusion across ordered cuts, while root.epochs_ordered implements only the cut predicate. The event relation and its coverage, corruption, divergence and refusal semantics still need a concrete design and conformance selection.
- 2026-09-21T09:32:07Z (main): Process planned: the event-level relation's design and cut plan do not exist (log design §7 defines event order; root.epochs_ordered implements only the cut predicate). Slice design → cut plan → freeze, in .worktrees/event-level-l8 as the world-read lane's worktree (roadmap rule 4).
- 2026-09-21T09:32:08Z (main): started
  provenance: {"harness_session":"claude-code:51515f65-ae75-4a25-83a1-28526d417cd6","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-21T09:32:08Z (main): claimed by claude-code/opus, pid 3174647
