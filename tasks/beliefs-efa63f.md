---
id: beliefs-efa63f
title: corpus._ROOT_STATES is a never-evicted process-global keyed by root path
status: done
priority: 2
size: m
owner: main
created: 2026-09-07T09:30:22Z
updated: 2026-09-12T12:50:57Z
started: 2026-09-12T12:23:01Z
completed: 2026-09-12T12:50:57Z
depends: []
tags: [testing]
---

corpus.py:559 holds _ROOT_STATES: dict[str, _RootState], a process-global map keyed by root path with no eviction. When pytest's retention policy deletes a passing test's numbered tmp_path and later hands the same literal path to another test, _root_state_for serves the stale _RootState instead of opening a fresh corpus.

This makes every path-keyed test fixture in the repo quietly order-dependent. Two fixtures now carry uuid-subdirectory workarounds to dodge it (tests/test_audit.py's writer fixture, and one in test_import_derivation.py), with the mechanism documented at the point of use.

Arguably fine for real corpora, which are not deleted and recreated at one path mid-process — but the failure mode is invisible and order-dependent, which is the expensive kind. Worth deciding whether the cache should be invalidated on root disappearance, keyed by something stabler, or left with the hazard documented once centrally instead of per-fixture.

Surfaced during the verification-publication slice; see docs/plans/2026-09-06-verification-publication-execution.md.

## Notes

- 2026-09-12T12:50:57Z (main): Decided 2026-09-12: the hazard is the test harness's, not production's. pytest's default retention keeps passing dirs; this machine's ~/.zshenv exports PYTEST_ADDOPTS=-o tmp_path_retention_policy=failed (tmpfs quota), which deletes them and lets make_numbered_dir hand the next test the same literal path. Production is inside OperationLock's stated single-writer-per-process envelope; keying by inode is unsound (ext4 reuses them) and a nodes root has no identity marker. Fix: corpus._forget_roots_under and world.registry._forget_worlds_under (documented as the harness's seam), a conftest autouse fixture evicting under each test's tmp_path at teardown, and the two uuid workarounds removed. Proven load-bearing: with eviction disabled, 6 of test_import_derivation's V4 cases fail; with it, 73 pass.
- 2026-09-12T12:50:57Z (main): central conftest eviction of per-root registry entries under tmp_path at teardown; per-fixture uuid workarounds removed; hazard and eviction covered in test_corpus_write and test_world_registry
