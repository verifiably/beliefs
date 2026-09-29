---
id: beliefs-179099
title: gather's per-ref absence branches are unreachable for world reads after decision 7
status: shelved
priority: 2
created: 2026-09-19T18:52:20Z
updated: 2026-09-29T22:50:05Z
depends: []
parent: beliefs-0c50ed
tags: [conformance, world-read]
---

Slice 2 decision 7 makes an absent covered corpus answer absence for the whole world read before the per-ref walk runs, via the early producer-snapshot absence check and its if-absent short-circuit. The per-ref _absence_of branches in gather are therefore dead code for a world read; they remain live for a corpus-local read. Found reviewing test_world_view_acceptance.py's edit at cut 34 (results §3.2).

## Scoping correction (2026-09-29)

The original blanket claim is incorrect. gather records producer-snapshot absence, then still walks the retraction enumeration before its if-absent return. Its early per-ref and target checks collect diagnostics; test_world_standing.py::TestAbsence::test_a_found_retraction_in_an_absent_corpus_is_the_absence_answer asserts (retraction.id, corpus) and passed in this review. The later run/input/proposition absence branches occur after the return and appear redundant for an absent covered world corpus. They are not live for corpus-local reads: corpus._absence_of returns None unless the view is WorldReadView. Preserve the original report above as provenance; do not delete all checks from it. No runtime defect or measured benefit establishes a cleanup task. Handoff: docs/notes/2026-09-29-retraction-standing-backlog-brief.md.

## Notes

- 2026-09-29T22:50:05Z (main): shelved: A measured gather refactor or maintenance issue needs the later absence branches simplified; preserve the early retraction/target diagnostics and prove each removed branch unreachable.
- 2026-09-29T22:50:05Z (main): scope: shelved; corrected the blanket dead-code premise: early world checks remain live, while local _absence_of returns None; brief: docs/notes/2026-09-29-retraction-standing-backlog-brief.md
