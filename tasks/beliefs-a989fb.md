---
id: beliefs-a989fb
title: "Sharing door for the retired transition: World.retire under the scoped authority (science commons 1b)"
status: idea
priority: 2
reviewed: true
reviewed_at: 2026-10-24T09:57:06Z
created: 2026-10-23T01:56:42Z
updated: 2026-10-24T09:57:06Z
depends: [beliefs-c0d952]
parent: beliefs-182296
tags: [publication]
source: beliefs-f24fe9
agent: claude-code
---

The session doors design (2026-10-22 §2.4, §8) ledgers bound, fetched, admitted and mounted; retired is backed by World.retire and has no door, so record_sharing refuses it. Milestone 1b's retirement (science commons design §10) needs ScopedWriter.retire(corpus_id, *, evidence) ledgering retired with the status record as evidence.

Handoff: [ref:brief] records why this needs a design first: binding the pin without the existing doors' root/observer arguments, identifying the status record in the sharing evidence, and recovering when retirement commits but the ledger append fails. Wait on beliefs-c0d952; science keeps the dependency/keep/supersession policy.

## References

- brief (input, required, kind=brief): docs/notes/2026-10-24-publication-session-follow-ups-brief.md — scope evidence and disposition

## Notes

- 2026-10-24T09:57:06Z (main): scope: briefed; verified the missing retire door at 802286e; beliefs-c0d952 must settle evidence binding, status evidence and cross-actor retry after a ledger failure; dependency recorded; brief: docs/notes/2026-10-24-publication-session-follow-ups-brief.md
