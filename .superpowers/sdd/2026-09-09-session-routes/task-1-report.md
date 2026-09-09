# Task 1 report: public store identity reader

## Requirements implemented

- Renamed the detached private reader to public `beliefs.root.store_identity` and exported it.
- Preserved both internal callers (`init_store_root` and `fork_store`) through the public name.
- Returned `None` for missing, empty, malformed-chain, or no-genesis roots; malformed non-store genesis payloads raise `CorpusRootRefused`.
- Updated the store-root test module description and added five behavioral tests.

## TDD evidence

RED:

```text
python3 tools/tt beliefs-task1-red -- sh -c 'cd python && uv run --frozen pytest tests/test_store_root.py -q -k TestStoreIdentity'
ImportError: cannot import name 'store_identity' from 'beliefs.root'
```

The failure occurred during collection because the requested public symbol did not yet exist.

GREEN:

```text
python3 tools/tt beliefs-task1-green -- sh -c 'cd python && uv run --frozen pytest tests/test_store_root.py -q -k TestStoreIdentity'
.....                                                                    [100%]

python3 tools/tt beliefs-task1-file -- sh -c 'cd python && uv run --frozen pytest tests/test_store_root.py -q'
.............                                                            [100%]
```

## Final verification

```text
RUFF_CACHE_DIR=/tmp/beliefs-ruff-cache just check
All checks passed!
0 errors, 0 warnings, 0 informations
Checked 15 files in 33ms. No fixes applied.
{"errors":[],"warnings":[]}
```

The first unqualified `just check` attempt was blocked by the environment's read-only `/home/keith/.cache/ruff`; rerunning with a writable `RUFF_CACHE_DIR` passed.

## Files changed

- `python/src/beliefs/root.py`
- `python/tests/test_store_root.py`
- `docs/plans/2026-09-09-session-routes.md`
- `tasks/beliefs-2d9a55.md` (CLI task records)

## Self-review

The public function has the specified type and detached read semantics, explicitly handles missing roots, and has no remaining private-name references in the module. The diff is limited to the requested seam, tests, plan checkboxes, task record, and this report.

## Concerns

No substantive concerns. Ruff requires a writable cache override in this environment.
