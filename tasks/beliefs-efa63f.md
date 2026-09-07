---
id: beliefs-efa63f
title: corpus._ROOT_STATES is a never-evicted process-global keyed by root path
status: todo
priority: 2
size: m
created: 2026-09-07T09:30:22Z
updated: 2026-09-07T09:30:22Z
depends: []
tags: [testing]
---

corpus.py:559 holds _ROOT_STATES: dict[str, _RootState], a process-global map keyed by root path with no eviction. When pytest's retention policy deletes a passing test's numbered tmp_path and later hands the same literal path to another test, _root_state_for serves the stale _RootState instead of opening a fresh corpus.

This makes every path-keyed test fixture in the repo quietly order-dependent. Two fixtures now carry uuid-subdirectory workarounds to dodge it (tests/test_audit.py's writer fixture, and one in test_import_derivation.py), with the mechanism documented at the point of use.

Arguably fine for real corpora, which are not deleted and recreated at one path mid-process — but the failure mode is invisible and order-dependent, which is the expensive kind. Worth deciding whether the cache should be invalidated on root disappearance, keyed by something stabler, or left with the hazard documented once centrally instead of per-fixture.

Surfaced during the verification-publication slice; see docs/plans/2026-09-06-verification-publication-execution.md.
