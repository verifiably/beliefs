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

## Fast local loop

Start with the zero-dependency deterministic loop:

```
uv run --frozen pytest --ignore=tests/test_n2.py
```

On the measured multicore host, run the same loop in parallel:

```
uv run --frozen pytest -n 8 --dist=loadfile --ignore=tests/test_n2.py
```

Use a test file or node id (`tests/test_module.py::test_name`) for the narrowest
deterministic run, `-k` for a name expression, `--lf` to rerun failures, or
`--ff` to run failures first. Adjust `-n` to the machine; `8` is the measured
value on a 16-core/32-thread host.

N2 runs each declared contract check in its own subprocess and is intentionally
excluded only from ordinary iteration. The serial `uv run --frozen pytest` above
remains the required CI, conformance, and completion gate. For an exploratory
parallel full run, remove `--ignore`; `--dist=loadfile` keeps all N2 tests on one
xdist worker so their internal 24 workers are not multiplied.

On 2026-09-04 with fresh writable caches, the serial gate ran 3,216 tests in
868.15s; serial without N2 ran 3,178 in 703.03s; parallel with N2 ran 3,216 in
223.34s; and the command above ran 3,178 in 164.25s. These are single
end-to-end samples; N2's earlier three-run range of 147.37–229.02s corroborates
the serial delta but shows the absolute-time variance. An initial
`uv run --with pytest-xdist` trial was invalid because its overlay interpreter
sat outside the captured runtime closure; the pinned development dependency
keeps workers inside the project environment.

## What is here

| module | what it owns | authority |
|---|---|---|
| `science.identity.v1` | the canonical value contract — injective, domain-separated per kind | computation §4.3 |

Cuts 1–7 have landed their selected slices; cut 7's world-index epoch carrier
merged into `main` on 2026-08-22 preserving history
([results](../docs/plans/2026-08-20-conformance-cut-7-results.md)). The
[`adoption ledger`](../docs/designs/2026-08-03-redesign-adoption-ledger.md) is the
authority for what is built and what still waits on another artifact.
