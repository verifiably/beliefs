# Task 6 report

## Implementation

Added `python/tests/acceptance/test_dataset_address_acceptance.py` with the 10 specified durable acceptance cases covering W2, W3, and W8. The W8 raw-write move and consolidate cases clear the in-process corpus registry before reopening with `open_corpus`, so the fresh writer observes raw filesystem records as required by the fixture contract.

## Commands and outputs

```text
source .superpowers/sdd/2026-09-14-world-resolution-slice-5/certified-env.sh
cd python && uv run --frozen pytest tests/acceptance/test_dataset_address_acceptance.py
10 passed in 8.05s

(cd python && uv run --frozen ruff check . && uv run --frozen pyright)
All checks passed!
0 errors, 0 warnings, 0 informations

tasks check
{"errors":[],"warnings":[]}
```

## Self-review

- All requested function names and fixtures are present.
- The W8 move reopens alpha after `raw_write(alpha, bad)` before `relocation.move`.
- The W8 consolidate cases reopen beta after the raw write and assert both declaration orders preserve the filesystem snapshot on refusal.
- Removed the unused `digest_for` import and replaced the snapshot lambda with a named function for lint cleanliness.
- Pyright requires a narrow inline ignore for the dynamically typed epoch document projection.

## Final status

DONE. No production files changed.
