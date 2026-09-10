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

The initial full-file run hit `RunRefused: the planning launch exited 1` because Snakemake's source cache attempted to create a `TemporaryDirectory` under the default `~/.cache`, which is read-only here (`errno 30`). Setting `XDG_CACHE_HOME=/tmp/task8-xdg-cache` resolves the environment issue.

Final validation:

```text
XDG_CACHE_HOME=/tmp/task8-xdg-cache python3 tools/tt task8-replay-cache -- sh -c 'cd python && uv run --frozen pytest tests/test_replay.py -q'
52 passed in 152.817s
```

## Files changed

- `python/src/beliefs/replay.py`
- `python/tests/test_replay.py`
- `docs/plans/2026-09-09-session-routes.md`
- `tasks/beliefs-469af0.md`

## Self-review

The implementation changes only the requested union and two closure reads; no compatibility layer or unrelated cleanup was added.

## Concerns

Full replay validation passes with the cache directory override documented above; no implementation concern remains.
