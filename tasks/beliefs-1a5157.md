---
id: beliefs-1a5157
title: Implement the Beliefs publish act and governed records
status: todo
priority: 2
size: xl
created: 2026-08-31T00:38:28Z
updated: 2026-08-31T00:38:28Z
depends: [beliefs-acc2e9, beliefs-b34652]
tags: [migration, publication, coordination]
---

Outcome: Beliefs publishes an immutable selected view through a recoverable governed act, with publication marker and binding revisions, exact retry, terminal reporting, and recipient admission refusal.

Acceptance evidence: After coordination/view delivery and the world-read lane, bank the coordination-contract and act-report amendments; implement request fixation, staging, exact-prefix recovery, head export, replication, restore, reveal, atomic source binding/report, orphan repair semantics, and marker-required arrival; test every recovery-table state and destination refusal; and pass the complete gates before any real publish runs.

Sources: `docs/superpowers/specs/2026-08-29-user-and-autonomy-layer-design.md` §§4.1 and 6 and §8 item 5; `docs/designs/2026-08-11-act-report-design.md`; and the root-lifecycle and log-verification designs.

Uncertainty: Destination-specific remote transport remains for Science, while this task owns only the Beliefs act and records. The prerequisite coordination and world-read outcomes are unfinished.
