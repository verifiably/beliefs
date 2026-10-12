---
id: beliefs-7a56ef
title: "Run sessions for the autonomy envelope: ceiling constructor, cross-process corpus claim, seal, after-tip read, ledgered store writes"
status: todo
priority: 2
size: l
complexity: high
process: planned
created: 2026-10-12T12:10:22Z
updated: 2026-10-12T15:59:09Z
depends: []
tags: []
source: autonomy-250f4d
agent: claude-code/claude-opus-5-5
---

The kernel slice the autonomy envelope (sub-project 6) needs; design it here and freeze it in a conformance cut. Source: autonomy docs/specs/2026-10-12-envelope-design.md (branch envelope-design until merged), §4 and §12.

- open_run_session(..., ceiling: WritePermit): a public run-session constructor, the permit deserialized from the launcher's file and recorded in session-open.
- A cross-process claim on each written chain (corpus and store root), taken by every session constructor before session-open, held for the session's life, released on process death; a second session on a claimed chain is refused (row E15). Host-local.
- WriterSession.seal(): a flag checked in _require_current under the session lock, so no act starts after the seal; scoped acts drain, route acts are cut at their next phase (row E16).
- A detached read of the entries after a tip (no recovery appends), for science's log.
- An act line for every store-chain registration a holdings act appends (store_write, store_move, store_delete): entry resolved by txid read-back inside the same lock hold, intent = the holdings intent (move-source for a move), records empty. Without it every holdings run quarantines.
- reconcile's act matching by digest across written chains, not by the corpus field, so store-root acts verify.
- The belief-policy and contract identities the basis reads; the confinement denied-set extension (envelope's denied set, except the kernel's own <ops>/scratch/<invocation> staging).
- Note: SettledEntryView does not record whether recovery appended a settlement; the envelope no longer needs it.

## Notes

- 2026-10-12T15:59:09Z (main): the envelope spec is merged on autonomy main: docs/specs/2026-10-12-envelope-design.md (§4 lists this slice's asks, §12 its rows)
