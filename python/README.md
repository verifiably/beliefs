# science — Python

The Python implementation. Substrate §11 puts the composition root here, so this
tree is the system; `../ts/` carries only the one shared encoding (formal model
limitation 9: **M10 is the only cross-implementation row**).

## Gates

From the repository root:

```
just check
just test
```

`check` is ruff, pyright, biome, tsc, and `tasks check`; `test` runs parallel
Python tests outside N2, standalone N2, and the TypeScript suite. Both recipes run
through the vendored timing wrapper `tools/tt`, so the verdict is recorded. `test`
runs under ops' `host-budget run`, which sizes xdist and N2's own pool. The Python
commands it runs are:

```
host-budget run -- sh -c 'uv run --frozen pytest -n auto --dist=worksteal --ignore=tests/test_n2.py && uv run --frozen pytest tests/test_n2.py'
uv run --frozen ruff check .
uv run --frozen pyright
```

`pytest` is bare rather than `-q`: this project's `addopts` already carries `-q`, so a
second one is `-qq`, which drops the summary line the wrapper counts tests from.

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

On a multicore host, run the same loop in parallel under ops' `host-budget run`, which
sets `-n auto`'s worker count from the host's CPU budget:

```
host-budget run -- uv run --frozen pytest -n auto --dist=worksteal --ignore=tests/test_n2.py
```

The whole-repository equivalent, which also runs the TypeScript tests vitest selects
from the working tree, is `just test-fast` from the root.

On the certified 16-worker host on 2026-09-26, three warm `test-fast` runs
passed 5,709 tests with one skip each in 86.94–87.42s by `tt` (87.17s
median). Two complete `test` runs each passed 5,709 non-N2 and 46 N2 tests
with one skip, plus 155 TypeScript tests, in 235.75s and 237.47s. Standalone
N2 took 148.54s and 150.75s. These timings use the per-capture path-walk
improvement; every artifact is still read and hashed on each capture.

Use a test file or node id (`tests/test_module.py::test_name`) for the narrowest
deterministic run, `-k` for a name expression, `--lf` to rerun failures, or
`--ff` to run failures first. The measurements below used `-n 8` on a
16-core/32-thread host; `host-budget show` prints what `-n auto` gets now.

N2 runs each declared contract check in its own subprocess and is excluded only
from ordinary iteration and the parallel first phase. The full gate's second
pytest invocation runs it outside xdist so its session-scoped findings fixture is
built once and its pool receives the full `OPS_WORKERS` allowance. Running N2
under xdist with 16 workers would give that pool only one worker under the
host-budget share rule. Without `OPS_WORKERS` N2 refuses to run: use
`host-budget run`, or set `OPS_WORKERS=<n>` for one module run by hand. A
single-process `uv run --frozen pytest` remains available for diagnosis.

On 2026-09-04 with fresh writable caches, the serial gate ran 3,216 tests in
868.15s; serial without N2 ran 3,178 in 703.03s; parallel with N2 ran 3,216 in
223.34s; and the then-current fast command ran 3,178 in 164.25s. These are
single end-to-end samples from before N2's nested-pool share rule; the old
parallel-full result does not predict a current N2-in-xdist run. N2's earlier
three-run range of 147.37–229.02s shows the absolute-time variance. An initial
`uv run --with pytest-xdist` trial was invalid because its overlay interpreter
sat outside the captured runtime closure; the pinned development dependency
keeps workers inside the project environment.

On 2026-09-12 (beliefs-f253a1, step 3) the then-current parallel command ran
4,438 tests in 171.46s, and the serial gate's median over the baseline week's
24 recorded runs was 1066.0s. That historical 4,438-test profile found 97
pipeline call sites across 17 files; the current 5,700-plus-test attribution and
two-phase gate measurements are in the
[latency design](../docs/superpowers/specs/2026-09-26-test-suite-latency-design.md).

## What is here

| module | what it owns | authority |
|---|---|---|
| `science.identity.v1` | the canonical value contract — injective, domain-separated per kind | computation §4.3 |

Cuts 1–7 have landed their selected slices; cut 7's world-index epoch carrier
merged into `main` on 2026-08-22 preserving history
([results](../docs/plans/2026-08-20-conformance-cut-7-results.md)). The
[`adoption ledger`](../docs/designs/2026-08-03-redesign-adoption-ledger.md) is the
authority for what is built and what still waits on another artifact.
