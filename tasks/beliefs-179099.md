---
id: beliefs-179099
title: gather's per-ref absence branches are unreachable for world reads after decision 7
status: idea
priority: 2
created: 2026-09-19T18:52:20Z
updated: 2026-09-19T18:52:20Z
depends: []
tags: [conformance, world-read]
---

Slice 2 decision 7 makes an absent covered corpus answer absence for the whole world read before the per-ref walk runs, via the early producer-snapshot absence check and its if-absent short-circuit. The per-ref _absence_of branches in gather are therefore dead code for a world read; they remain live for a corpus-local read. Found reviewing test_world_view_acceptance.py's edit at cut 34 (results §3.2).
