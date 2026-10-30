---
id: beliefs-1dfd8c
title: Publish lifecycle inspection exception types at the root boundary
status: todo
priority: 2
size: s
complexity: low
process: direct
created: 2026-10-30T22:54:35Z
updated: 2026-10-30T22:54:35Z
depends: []
tags: []
source: sci-300dab plan review round 2
agent: codex
origin: agent
---

The public read_lifecycle_state API can raise AtomsError subclasses, but AtomsError, MetadataStoreInvalid, CapabilityUnavailable and PreconditionRefused are only internal imports in beliefs.root and absent from __all__. Publish these four names at the root boundary with a contract test so consumers can normalize inspection refusals without importing atoms directly. Science will temporarily import them through beliefs.root with a comment citing this task; no change to exception behavior or lifecycle admission is requested. Acceptance: the four names are explicit supported exports, importable from beliefs.root, and existing exception semantics remain intact.

## Notes

- 2026-10-30T22:54:35Z (add): created
  provenance: {"harness_session":"codex:01a18e58-0cdf-75c2-bf7d-f4ac22417069","harness_session_source":"CODEX_THREAD_ID","origin":"agent"}
