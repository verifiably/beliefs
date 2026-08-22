# science — Python

The Python implementation. Substrate §11 puts the composition root here, so this
tree is the system; `../ts/` carries only the one shared encoding (formal model
limitation 9: **M10 is the only cross-implementation row**).

## Gates

```
uv run --frozen pytest -q
uv run --frozen ruff check .
uv run --frozen pyright
```

`pyright` takes no path argument. Naming one narrows the check to that subtree
and hides every diagnostic outside it — which is how `tests/` drifted once
already after the
[test-typing cleanup](../docs/superpowers/plans/2026-08-17-python-tests-pyright.md)
landed. The gate is the whole project or it is not the gate.

## What is here

| module | what it owns | authority |
|---|---|---|
| `science.identity.v1` | the canonical value contract — injective, domain-separated per kind | computation §4.3 |

Cuts 1–7 have landed their selected slices; cut 7's world-index epoch carrier
merged into `main` on 2026-08-22 preserving history
([results](../docs/plans/2026-08-20-conformance-cut-7-results.md)). The
[`adoption ledger`](../docs/designs/2026-08-03-redesign-adoption-ledger.md) is the
authority for what is built and what still waits on another artifact.
