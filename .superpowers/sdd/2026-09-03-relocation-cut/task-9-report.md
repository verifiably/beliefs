# Task 9 report: consolidate and tagged-basis reconciliation

## Commit and files

- Commit: `feat(relocation): add consolidate, the duplicate-location exit`
- Modified: `python/src/beliefs/relocation.py`,
  `python/src/beliefs/stored.py`, and `python/src/beliefs/corpus.py`
- Modified tests: `python/tests/test_relocation.py`,
  `python/tests/test_relocation_rows.py`, and new `python/tests/test_stored.py`
- Modified through `tasks` CLI: `tasks/beliefs-676a2c.md`
- The frozen conformance cut and SDD ledger were not changed.

## RED

The required focused command was:

`cd python && uv run --frozen pytest tests/test_stored.py tests/test_relocation.py tests/test_relocation_rows.py -k "consolidate or union_lineage or m3"`

After correcting one test-only missing import, it failed `20 failed, 51
deselected in 0.75s`. Every failure was the expected missing
`stored.union_lineage_bases` or `relocation.consolidate` interface.

Two review-discovered cases received their own later RED cycles:

- Two same-address ungoverned `memo` records failed because unconditional
  restamping raised `MalformedRecord`: `1 failed, 48 deselected in 0.43s`.
- A duplicate relation triple with different authored attributes failed because
  the loser's relation replaced the survivor's: `1 failed, 21 deselected in
  0.45s`.

The missing-input and malformed-report preflight checks were requested after
the first GREEN and passed immediately against the already implemented
preflight order; they added coverage without requiring a production change.

## GREEN and gates

- Required focused selector: `20 passed, 51 deselected in 0.78s`.
- Ungoverned-kind fix: `1 passed, 48 deselected in 0.32s`.
- Survivor-relation fix: `1 passed, 21 deselected in 0.38s`.
- Final three focused modules: `75 passed in 3.38s`.
- Final full Python suite: `3180 passed in 934.94s (0:15:34)`.
- Ruff: `All checks passed!`.
- Pyright: `0 errors, 0 warnings, 0 informations`.
- `tasks check`: zero errors and zero warnings.
- No `CapabilityUnavailable` refusal or certified kernel/volume mismatch
  occurred.

## Behavior

`consolidate` resolves and validates both inputs under sorted root locks,
reconciles into the kept authored node, preflights both operation ports and the
replacement before either intent, and then performs the exact keep-intent,
other-intent, replace, delete, keep-report, other-report sequence. Both reports
share one event token and each root publishes its exact prebuilt report
operation.

Lineage routes are validated as tagged bases, deduplicated and sorted by their
canonical encoded mapping. Relations are deduplicated by their identifying
triple while preserving the kept record's authored representation. Existing
deprecated ids are unioned without adding a live id. Governed records are
restamped after reconciliation; ungoverned records remain unstamped.

The public tests cover both uid outcomes, all specified refusals and D7 cases,
the M3 retraction replica with an untouched counter-retraction, survivor
readability and idempotence, pre-intent deterministic refusal, and root-local
T2 report identity.

## Concerns

None. No redirect, inbound rewrite, coreference record, balance transfer,
third uid, N-way API, delete preflight helper, compatibility layer, or later
task behavior was added. The parent task remains open because managed deletion
is still outstanding.
