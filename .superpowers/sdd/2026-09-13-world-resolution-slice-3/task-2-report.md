# Task 2 report — evaluator

## Changes

- Widened `_contract_fault` to compare each receipt's corpus set with the
  published epoch coverage before availability is consulted.
- Added subject-member identity checks for producer and coreference subjects,
  plus coverage checks for producer, retraction enumeration, and certification
  inventory subjects.
- Changed `_standing` to use the lock-only `_operation_lock_for` lookup, keep
  strict reads inside the capture hold, and convert `CorpusStateMalformed` into
  an `unresolvable` detail.
- Added five receipt regression arms covering narrowed coverage, three-way
  coverage disagreement, member identity disagreement, consistent omission,
  and a damaged carrier.
- Re-targeted the two moved live cut-7 arm anchors by index in
  `acceptance/test_n2_cut7.py`; frozen declarations were not edited.

## TDD evidence

RED command:

```text
cd python && uv run --frozen pytest tests/test_world_receipts.py -k "narrower or agree or member_subject or consistent_omission or damaged_carrier"
```

Observed: 4 failed, 2 passed, 14 deselected. The three ordering arms reached
binding availability before the new checks, and the damaged carrier raised
`CorpusStateMalformed`; the consistent omission already refuted.

GREEN command:

```text
cd python && uv run --frozen pytest tests/test_world_receipts.py -k "narrower or agree or member_subject or consistent_omission or damaged_carrier"
```

Observed: 6 passed, 14 deselected.

## Verification

```text
cd python && uv run --frozen pytest tests/test_world_receipts.py tests/test_world_read.py tests/test_arm_staleness.py tests/test_frozen_guards.py
45 passed in 14.72s

cd python && uv run --frozen ruff check .
All checks passed!

cd python && uv run --frozen pyright
0 errors, 0 warnings, 0 informations

cd <repo> && tasks check
errors: [], warnings: []
```

## Concerns and deviations

The brief's `_standing` signature allowed either retaining or dropping the
unused `world` parameter; it was dropped and its sole caller updated. The
brief's stale-arm instruction referred to `cited_not_run`, but cut 7 is a live
guard in this tree; the required live-guard mechanism was used instead, with
two indexed re-targets. No frozen document or declaration was changed.

Commit: this task's implementation commit (reported with the final handoff).
