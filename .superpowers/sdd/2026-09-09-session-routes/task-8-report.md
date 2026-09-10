# Task 8 implementation report

## Implemented

- Updated `replay` to accept `RunMinted | RunClosure` and select the closure once.
- Added forwarding-equivalence coverage proving direct closure and minted replay pass identical boundary arguments.
- Updated the source plan checklist and completed `beliefs-469af0` through the tasks CLI.

## TDD evidence

RED:

```text
python3 tools/tt task8-red -- sh -c 'cd python && uv run --frozen pytest tests/test_replay.py -q -k over_a_closure'
1 failed: AttributeError: 'RunClosure' object has no attribute 'run'
```

GREEN:

```text
python3 tools/tt task8-green2 -- sh -c 'cd python && uv run --frozen pytest tests/test_replay.py -q -k over_a_closure'
1 passed
```

Additional verification:

```text
RUFF_CACHE_DIR=/tmp/beliefs-ruff-cache just check
All checks passed; tasks check reported 0 errors and 0 warnings.
```

The full `tests/test_replay.py` run is currently blocked by fixture execution failures in the existing assessment/production setup (`RunRefused: the planning launch exited 1`), yielding 7 failures and 19 setup errors.

## Files changed

- `python/src/beliefs/replay.py`
- `python/tests/test_replay.py`
- `docs/plans/2026-09-09-session-routes.md`
- `tasks/beliefs-469af0.md`

## Self-review

The implementation changes only the requested union and two closure reads; no compatibility layer or unrelated cleanup was added.

## Concerns

The full replay file needs a certified or otherwise functioning fixture execution environment before its pre-existing boundary-dependent tests can run.
