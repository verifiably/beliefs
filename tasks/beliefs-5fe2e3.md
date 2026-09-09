---
id: beliefs-5fe2e3
title: Expose the run and holdings routes on the invocation-scoped writer
status: todo
priority: 1
size: m
created: 2026-09-09T12:43:20Z
updated: 2026-09-09T12:43:20Z
depends: []
tags: [command-framework, dogfood]
---

Belief-path design (science docs/specs/2026-09-09-belief-path-commands-design.md §6.2): ScopedWriter exposes seven corpus-write methods only. The run boundary takes an OperationPort and the holdings boundary an ActContext, both binding an Authority the surface may neither see nor thread (command-framework §4.2), so a command routed run or holdings obtains a requirement and a scoped writer and no way to act. Required: the scoped writer exposes both routes under the invocation's scoped authority (an operation port for execute_assessment_run and replay; a holdings act context over a store root the session is opened with) and records their commits as act lines the way add does. open_attended_session takes the store root.
