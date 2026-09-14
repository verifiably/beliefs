# Task 4 report

## Implemented

- Added `decode.stored_claim_terms`, backed by one shared `_stored_wire` shape check used by `claim_from_stored`.
- Added `_binds_term` and `ReferencesTerm` denotation with validation before reading stored facets; malformed records raise `record-malformed`.
- Added decoder and world-selection coverage for argument terms, qualifier restrictions, exact stored comparison, malformed facets, and stale edits.

## TDD evidence

- RED: `uv run --frozen pytest tests/test_world_selection.py -k ReferencesTerm tests/test_claim_restore.py -k StoredClaimTerms` failed during collection because `beliefs.decode.stored_claim_terms` did not exist.
- GREEN: `uv run --frozen pytest tests/test_world_selection.py -k ReferencesTerm` — 10 passed, 18 deselected.
- GREEN: `uv run --frozen pytest tests/test_claim_restore.py` — 14 passed.

## Verification

- `uv run --frozen pytest tests/test_world_selection.py` — 28 passed.
- `uv run --frozen pytest tests/test_decode.py -k 'WireValueIsChecked or claim_from_stored'` — 7 passed, 62 deselected.
- `uv run --frozen ruff check .` — clean.
- `uv run --frozen pyright` — 0 errors, 0 warnings, 0 informations.

## Files changed

`python/src/beliefs/decode.py`, `python/src/beliefs/world/selection.py`, `python/tests/test_claim_restore.py`, `python/tests/test_world_selection.py`.

## Concerns

None.

## Review fix round 1

The review identified duplicate `_wire_parts` validation in `stored_claim_terms`. Removed the validation from `_stored_wire`; the terms reader validates once on its path, while `claim_from_stored` validates once before delegating to `decode_claim`.

- `uv run --frozen pytest tests/test_claim_restore.py` — 14 passed.
- `uv run --frozen pytest tests/test_world_selection.py` — 28 passed.
- `uv run --frozen pytest tests/test_decode.py -k 'WireValueIsChecked or claim_from_stored'` — 7 passed, 62 deselected.
- `uv run --frozen ruff check .` — clean.
