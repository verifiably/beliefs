# Task 6 report: durable routes on the acceptance rig

## Requirements implemented

- Added the durable holdings route acceptance test through the scoped writer and
  `beliefs.holdings.boundary.write`.
- Added the durable run publication route acceptance test through the operation
  port and `beliefs.runrecord.publication_plan`.
- Both tests compare the invocation act's persisted record identifiers and
  registration digest against the detached chain, then require clean session
  reconciliation.
- Marked Task 6 steps complete in `docs/plans/2026-09-09-session-routes.md`.

## Tests

- Focused: `RUFF_CACHE_DIR=/tmp/beliefs-ruff-cache tools/tt task6-focused -- sh -c 'cd python && uv run --frozen pytest tests/acceptance/test_session_acceptance.py -q -k "holdings_route or run_route or through_the"'`
  - Result: 2 passed.
- Repository gate: `RUFF_CACHE_DIR=/tmp/beliefs-ruff-cache just check`
  - Result: passed; 0 errors, 0 warnings from `tasks check`.

## Files changed

- `python/tests/acceptance/test_session_acceptance.py`
- `docs/plans/2026-09-09-session-routes.md`
- `tasks/beliefs-440c98.md`

## Self-review

The tests use the production acceptance rig and exact capability declarations
from the task brief. The holdings assertion parses the persisted node to prove
the boundary-minted UID survives to disk; the run assertion proves the closure
address is used in the persisted run ID. No unrelated code was changed.

## Concerns

None.
