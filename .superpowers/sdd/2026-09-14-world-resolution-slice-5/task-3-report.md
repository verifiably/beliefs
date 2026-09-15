# Task 3 report: derived dataset builder and caller migration

## Changes

- `stored.dataset_node` is keyword-only, requires resources, derives its id from the shared dataset declaration projection, and refuses declarations without a content identity.
- `dataset_declaration` and the builder share `_declaration_of`; stored malformed-resource messages retain the node-id prefix.
- Every ordinary Python test, acceptance fixture, and reproduction-tool caller now supplies resources and uses a derived ref where it names a built dataset. Deliberately absent refs and raw invalid-record boundary tests retain their original meaning. The forbidden positional-call TypeError test remains positional.
- The cut 20 F8 live guard has a dated adapter for the moved builder return. Frozen cut declarations and the cited-not-run cut 5 guard are unchanged.

## TDD evidence

RED:

```text
cd python && uv run --frozen pytest tests/test_stored.py -k TheDatasetBuilder
4 failed: the first three reached the old required `slug`; the positional-call arm showed the old builder still accepted it.
```

GREEN:

```text
cd python && uv run --frozen pytest tests/test_stored.py -k TheDatasetBuilder
4 passed

cd python && uv run --frozen pytest tests/test_stored.py tests/test_reproduction_driver.py
54 passed
```

The first broad migration inventory was retained at `/tmp/beliefs-task3-test-fast.log`:

```text
60 failed, 4525 passed, 10 errors in 173.43s
```

After fixture repair, `/tmp/task3-test-fast-final.log` reported:

```text
2 failed, 4593 passed in 172.12s
```

Both failures identified the same newly displaced live guard row, `test_n2_cut20.py::F8[5] in stored.py (0 matches)`. After adding the authorized live adapter, focused evidence was:

```text
F8 baseline: resolved
F8 audit: sound
uv run --frozen pytest tests/test_arm_staleness.py tests/test_frozen_guards.py
14 passed
```

## Final verification

The final serial portable suite was run after sourcing `certified-env.sh`; its complete output is retained at `/tmp/task3-portable-final.log`.

```text
4636 passed in 1229.24s (0:20:29)
```

```text
uv run --frozen ruff check .
All checks passed

uv run --frozen pyright
0 errors, 0 warnings, 0 informations

tasks check
0 errors, 0 warnings
```

Frozen-file and call-site audits found no modified `n2_arms_cut*.py`, cut documents, or `acceptance/test_n2_cut5.py`; no non-frozen builder caller lacks `resources`, and the only positional call is the required TypeError test.

## Concerns

None within Task 3. Task 4 still owns the separate cut 7 X9 live sabotage adapter.
