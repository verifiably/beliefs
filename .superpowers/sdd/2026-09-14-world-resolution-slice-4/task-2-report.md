# Task 2 report

## Implemented

- Added `SelectionRefused` with closed reasons, sorted unique references, and corpus IDs.
- Added `stored_query` to validate view revision records and parse their stored coordination query.
- Added `WorldReadView._mapped_records`, preserving corpus order and retained node identity.
- Added the specified tests and completed task tracking through `tasks`.

## TDD evidence

- RED: `cd python && uv run --frozen pytest tests/test_view_query.py tests/test_world_view.py -k "stored_query or selection_refused or mapped_records"` failed during collection with the expected missing `SelectionRefused` import.
- GREEN: the same focused command passed: `6 passed, 78 deselected`.

## Verification

- `cd python && uv run --frozen pytest tests/test_view_query.py tests/test_world_view.py tests/test_arm_staleness.py tests/test_frozen_guards.py` — `98 passed`.
- `cd python && uv run --frozen ruff check .` — passed.
- `cd python && uv run --frozen pyright` — `0 errors, 0 warnings, 0 informations`.
- `tasks check` — zero errors and warnings.

## Files changed

`python/src/beliefs/errors.py`, `python/src/beliefs/view_query.py`, `python/src/beliefs/world/view.py`, `python/tests/test_view_query.py`, `python/tests/test_world_view.py`, task records, and this report.

## Self-review

The implementation is limited to the three requested interfaces and their tests. The private accessor yields the same retained objects while `iter_stored` continues to provide copies.

## Concerns

None.
