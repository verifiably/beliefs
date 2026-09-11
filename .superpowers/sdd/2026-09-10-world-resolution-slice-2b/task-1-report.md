# Task 1 report

## Changes

- Added `beliefs.source` normalization for DOI, PMID, ISBN, and accession identifiers.
- Added `IdentifierMalformed` with the closed refusal reasons.
- Added precedence, basis projection, and `science.source-address.v1` digest derivation.
- Made `stored.ACCEPTED_EXTERNAL_IDENTIFIERS` re-export `source.SCHEMES`.
- Added focused source-address tests.

## Evidence

- `uv run --frozen pytest tests/test_source_address.py` — `53 passed`.
- `uv run --frozen ruff check .` — `All checks passed!`.
- `uv run --frozen pyright` — `0 errors, 0 warnings, 0 informations`.

## Concerns

None.

## Commits

`feat(source): normalize identifiers and derive source addresses` (implementation commit)
