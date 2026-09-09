---
id: beliefs-5fe2e3
title: Expose the run and holdings routes on the invocation-scoped writer
status: todo
priority: 1
size: m
created: 2026-09-09T12:43:20Z
updated: 2026-09-09T14:08:33Z
depends: []
tags: [command-framework, dogfood]
---

Belief-path design (science docs/specs/2026-09-09-belief-path-commands-design.md §6.2): ScopedWriter exposes seven corpus-write methods only. The run boundary takes an OperationPort and the holdings boundary an ActContext, both binding an Authority the surface may neither see nor thread (command-framework §4.2), so a command routed run or holdings obtains a requirement and a scoped writer and no way to act. Required: the scoped writer exposes both routes under the invocation's scoped authority (an operation port for execute_assessment_run and replay; a holdings act context over a store root the session is opened with) and records their commits as act lines the way add does. open_attended_session takes the store root.

## Notes

- 2026-09-09T13:23:42Z (main): Names the science plan (docs/plans/2026-09-09-belief-path-commands.md) assumes: open_attended_session(..., store_root: Path | None = None); ScopedWriter.operation_port() -> OperationPort under the scoped authority with commits recorded as act lines; ScopedWriter.holdings_context(*, instrument: str) -> ActContext over the session's store root, observer = session actor, published observations recorded as act lines; ScopedWriter.store_id -> str; ScopedWriter.actor; and beliefs.replay.replay accepting a RunClosure as well as a RunMinted (it reads only the closure). Also needed: a public way to read a store root's id.
- 2026-09-09T14:08:33Z (main): Also assumed by the science plan: beliefs.root.store_identity(store_root) -> str | None, the public form of _read_existing_store_genesis (detached inspection).
