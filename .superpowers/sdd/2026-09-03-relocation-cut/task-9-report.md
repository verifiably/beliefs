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

## Review fix round 1/5

Two Important findings were reproduced before production changes:

- A loser's deprecated id colliding with an unrelated record in the kept root
  raised `CollisionRefused` only after both intents.
- Two canonically equal single routes with different key order and NFC spelling
  retained different raw operands depending on argument order.

The combined RED summary was `2 failed, 53 deselected in 0.42s`; after the
fixes the same selector passed `2 passed, 53 deselected in 0.35s`.

`_preflight_replace_locked` now ends with `_refuse_collision`. The substrate
index permits the existing same `(uid, id)` replacement and refuses claims
owned by another uid, so the check is safe and keeps deterministic replacement
collisions ahead of both intents. The banked design §3.4 and the current plan's
verified-interface row and Task 4 instructions were corrected narrowly; the
frozen cut was untouched.

Lineage route union now deduplicates canonical bytes, sorts them, decodes each
retained route, and explicitly refuses a non-object decode. The result no
longer preserves an arbitrary raw operand and is independent of input order
for insertion-order and NFC-equivalent mappings.

Final review-fix evidence:

- Three Task 9 focused modules: `77 passed in 3.42s`.
- Full Python suite: `3182 passed in 943.87s (0:15:43)`.
- Ruff: `All checks passed!`.
- Pyright: `0 errors, 0 warnings, 0 informations`.
- `tasks check`: zero errors and zero warnings.
- No `CapabilityUnavailable` refusal or certified kernel/volume mismatch
  occurred.
