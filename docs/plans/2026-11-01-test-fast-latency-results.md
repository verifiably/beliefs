# `test-fast` latency results

**Task:** `beliefs-0f5112`; steps `beliefs-ef55af`, `beliefs-da58e8`, `beliefs-202076`, `beliefs-501cb2`, `beliefs-516396`.
**Status:** implemented, benchmark-verified and branch-reviewed (two rounds, accepted).
**Design:** [approved design](../superpowers/specs/2026-11-01-test-fast-latency-design.md).
**Plan:** [approved inline plan](../superpowers/plans/2026-11-01-test-fast-latency.md).
**Workspace:** `.worktrees/0f5112-test-latency`; logs and snapshots in persistent task storage `$WORK_ROOT/beliefs/beliefs-0f5112`.

## Changes

Part 1 removes redundant test-machinery work; Part 2 removes per-walk churn
from the closure walker. Nothing is cached across closure walks.

- **1C, `test_capability_boundary.py` (`4f6c6e1`).** `parsed(path)` still
  reads the file's current bytes on every call and delegates to
  `@functools.lru_cache(maxsize=256) _parsed_bytes(raw, filename)`, so a
  sabotage that edits a file on `PYTHONPATH` misses the cache. The two scan
  tests compute each module's name set once instead of once per vocabulary
  name. The cache holds at most 256 trees (the package's 116 modules, about
  63 MiB) and only in the worker that runs this module.
- **1A, `test_session_sharing_doors.py` (`7c48364`, `3038992`).** A
  `try / finally` helper `certified_work_dir()` in `conftest.py` now backs
  `certified_work`, the new `certified_module_work`, and
  `certified_work_factory`; it forgets corpus and world registry entries under
  the directory and removes it however the body ends. A module-scoped
  `exported_publication` builds the source world and its two local
  publications once and yields only the metadata-less export and facts read
  from it. Each of the 38 capability-dependent items copies the export into
  its own certified directory and opens its own recipient session.
- **1B, `test_session_publish_door.py` (`7c48364`).** A module-scoped
  `readonly_source` serves the 8 items that write no byte of the source
  world, each through `scoped_source(readonly_source, tmp_path)`, which
  rebinds the operations root and destination into the test's own
  directory. Teardown asserts every file under the source base is unchanged
  byte for byte. The 14 mutating items keep a per-test `certified_work`.
- **2, `beliefs.adapter._Closure` (`5de55eb`).** String-prefix root matching
  replaces `os.path.commonpath`/`relpath`; parents are resolved through a
  per-walk string-keyed `realpath` table and entries are inspected with one
  `os.lstat`; `add_tree` walks with `os.scandir`, entering no symlinked
  directory and pruning only the two known predicates' monotone directory
  names (`site-packages`, `__pycache__`, `.git`); `add_records` filters and
  joins `RECORD` text directly; and every regular file is hashed through one
  helper that keeps the 20-byte header of a loadable ELF, which `elves()`
  then classifies without reopening the file. One deliberate behaviour
  change: an unreadable subdirectory now propagates `OSError` (and so
  `ClosureUnsupported` from `capture_closure()`) where `Path.rglob` skipped it.
  `RAW_WRITE_ALLOWLIST["adapter.py"]` stays `{"copy2"}` and all five
  `Sabotage.before` anchors (`K7a`, `K7b`, `K7c`, `R13`, `R17`) stay unique.

## Correctness evidence

- **RED to GREEN.** Seven new tests. Observed RED: the AST cache test
  (`NameError: _parsed_bytes`), `certified_work_factory` (fixture not found),
  `scoped_source` (`NameError`), `elves()` reopening a hashed file, and the
  `add_tree` scan control (no `os.scandir` call under `Path.rglob`). The
  `add_records` and root-matching tests pin baseline behaviour and passed
  before and after the change.
- **Focused runs (`just test-one`).** Baseline over the seven target modules:
  634 passed. After Task 3: closure, adapter, confinement, staleness and
  boundary modules 575 passed; `tests/acceptance/test_n2_cut13.py` 16 passed
  (live `K7a`/`K7b`/`K7c` kills); session doors, publish door and fixture
  grouping 67 passed; acceptance callers
  (`test_owned_replica_publication_acceptance.py`, `test_n2_cut47.py`) 24
  passed; `test_capability_boundary.py` with `acceptance/test_durable_corpus.py`
  470 passed.
- **Uncertified-host partition.** With `VERIFIABLY_UNCERTIFIED_HOST=1` and a
  tmpfs `SCIENCE_CUT10_ROOT`, the two session-door modules gave
  `6 passed, 60 skipped`, every skip reason starting
  `certified tuple unavailable on this host:`, and the base directory was
  empty afterwards.
- **Python 3.11.** The six affected modules under CPython 3.11.15 in a
  temporary project environment: 633 passed.
- **Closure parity.** Baseline (`240a989`'s `adapter.py`, executed as a
  standalone module) and candidate `capture_closure()` ran back to back over
  the same filesystem. Their serialized manifests, rendered rows, loader,
  interpreter, loader map, loader ELFs and plan are byte-identical: SHA-256
  `18b10edf7811ec9b46ea2501c3d268ca216b3744f484cf92c760277073525e65`, 8,476
  rows, 75 loader-map entries, 27 loader ELFs, 5 rendered rows. Over five
  alternating warm walks a single `capture_closure()` took a median 1.566 s
  (baseline) and 0.623 s (candidate).
- **Checks.** `just check-hygiene` and `TT_FORCE=1 just check-code` pass.
- **Review correction (`0a61785`).** A `RECORD` entry holding a NUL byte made
  the new path reads raise a raw `ValueError` where `Path.is_file()` had read
  it as absent; `add_records` now refuses it as `MalformedClosure` with the
  baseline's message (RED `ValueError`, GREEN after). Focused modules 576
  passed, `test_n2_cut13.py` 16 passed, and closure parity stayed exact
  (SHA-256 `9554e5deabb508e9d9b4cca5169b9df3e3be12dd4460bee07a89032b38fcdb86`;
  the digest moved because the closure hashes `adapter.py` itself).

## Alternating performance proof

Recorded `tt` wall seconds of `TT_FORCE=1 just test-fast`, in B1, C1, B2,
C2, B3, C3 order, all from a clean tree with an observed 16-worker grant.
Baseline `240a989` passed 6,403 with one skip on every run; the candidate
passed 6,410 with one skip; affected TypeScript selected no files and exited 0.
The host was shared with other sessions throughout: one-minute load read
between 20.8 and 26.4 on 32 CPUs before and after every run except the start
of B1 (9.2, five-minute 21.1). That one shift could only have favoured the
baseline, and B1 matches B3 within a second, so no pair was repeated.

| Pair | Baseline (s) | Candidate (s) | Baseline minus candidate (s) |
| --- | ---: | ---: | ---: |
| 1 | 105.379 | 75.142 | 30.237 |
| 2 | 112.190 | 70.223 | 41.967 |
| 3 | 104.401 | 77.273 | 27.128 |

- Median candidate: **75.142 s**, at or under 90 s.
- Every paired difference is positive.
- Median difference 30.237 s exceeds the noise bound 7.789 s (the larger of
  the baseline range 7.789 s and the candidate range 7.050 s).

Verdict: **keep**. The unprofiled pilot before the sweep recorded 77.062 s.

## Worker-time attribution

`--durations=0` totals of setup, call and teardown across 16 workers.
Baseline is the diagnostic at `240a989`; candidate is one pass after the
sweep (pytest 77.35 s, load 17.9 to 23.8). Per-module figures under shared
load move by a few seconds either way; the totals and the targeted modules
are the evidence.

| Module | Baseline (s) | Candidate (s) | Change (s) |
| --- | ---: | ---: | ---: |
| `tests/test_boundary.py` | 181.76 | 126.49 | -55.27 |
| `tests/test_session_sharing_doors.py` | 175.41 | 20.26 | -155.15 |
| `tests/test_replay.py` | 122.54 | 88.54 | -34.00 |
| `tests/test_cut15_workflows.py` | 105.84 | 86.58 | -19.26 |
| `tests/test_session_publish_door.py` | 80.77 | 67.77 | -13.00 |
| `tests/test_verify.py` | 70.36 | 48.85 | -21.51 |
| `tests/test_assess.py` | 65.49 | 43.86 | -21.63 |
| `tests/test_run_persistence.py` | 44.62 | 34.74 | -9.88 |
| `tests/test_capability_boundary.py` | 30.78 | 7.73 | -23.05 |
| **Total** | **1,381.43** | **1,101.58** | **-279.85** |

Each part has a real reduction: 1A -155 s, 1B -13 s, 1C -23 s, and Part 2
about -161 s across the six workflow modules that capture closures.

## Full suite

`just test-full` passed every phase: non-N2 Python 6,410 passed and 1
skipped, standalone N2 46 passed, TypeScript 155 passed (`execution: ran`,
`execution_reason: forced`). It recorded **395.447 s**, over the 300 s
`test` limit. The run was contended: one-minute load rose from 20.9 to 47.9
as other sessions ran their own suites, the non-N2 phase took 102 s against
75 s in the sweep, and the N2 phase, which this change does not touch, took
289 s. Earlier unforced `test` runs on this host ranged from 241 to 381 s.
Under policy-off `test` is a disabled broad target with no latency
obligation; this run is correctness evidence, not a timing sample.

## Policy-off and hosted CI

`.tt.toml` (`automatic_broad = false`, `test-fast` among its broad targets)
was activated on `main` at `01eb638191bd44fe9bd2a715fcc7d6853b07cc6e`
(`beliefs-067a8d`), which retired this incident's `tt-latency` obligation for
`test-fast`. `tt-latency verify` therefore reports it as not applicable and
never exits 0; this record and the task's notes are the closeout evidence.
The branch merges into `main` locally without a push, so hosted GitHub
Actions CI (Python 3.11 and 3.13, Node 20 and 24) has not run on it and runs
on the next push the user approves.

## Review

A fresh whole-branch review (round 1) accepted the branch with five Minor
findings; the executor re-graded one (the NUL-byte refusal above) to
Important and fixed it, and a fresh scoped re-review (round 2) accepted the
fix with three Minor findings. Deferred minors, recorded on the task:

- `add_tree`'s pruned directory names are written beside the two predicates
  they mirror; a later narrowing of a predicate would keep pruning silently.
- `session_doors_fixture.metadata_less_copy` has no remaining caller.
- `exported_publication` has no teardown byte check on its shared export.
- No test changes a symlink between two `capture_closure()` calls; the
  guarantee holds because each walk builds a new `_Closure`.
- The foreign-endian ELF case in the `elves()` test is rejected by its data
  encoding alone, not by its byte-swapped machine field.
- Under a non-UTF-8 filesystem encoding an unencodable `RECORD` entry would
  still raise `UnicodeEncodeError` rather than `MalformedClosure`.
- The NUL-byte test matches part of the message and calls the entry
  "unencodable".
