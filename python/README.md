# beliefs — Python

The Python implementation, package `beliefs`. Substrate §11 puts the composition
root here, so this tree is the system; `../ts/` carries only the one shared encoding
(formal model limitation 9: **M10 is the only cross-implementation row**).

## Gates

From the repository root:

```
just check
just test
```

`check` is the vendored `tools/ops-check` and `tools/ops-docs check`, ruff check,
ruff format --check, pyright, biome, tsc, and `tasks check`; `test` runs parallel
Python tests outside N2, standalone N2, and the TypeScript suite. Both recipes run
through the vendored timing wrapper `tools/tt`, so the verdict is recorded. `test`
runs under ops' `host-budget run`, which sizes xdist and N2's own pool. The Python
commands they run, from this directory, are:

```
host-budget run -- sh -c 'uv run --frozen pytest -n auto --dist=loadgroup --ignore=tests/test_n2.py && uv run --frozen pytest tests/test_n2.py'
uv run --frozen ruff check .
uv run --frozen ruff format --check .
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
host-budget run -- uv run --frozen pytest -n auto --dist=loadgroup --ignore=tests/test_n2.py
```

Tests using module- or class-scoped fixtures share a file or class group;
other tests remain independently scheduled.

The whole-repository equivalent, which also runs the TypeScript tests vitest selects
from the working tree, is `just test-fast` from the root.

On the certified 16-worker host on 2026-09-26, three warm `test-fast` runs
passed 5,709 tests with one skip each in 86.94–87.42s by `tt` (87.17s
median). Two complete `test` runs each passed 5,709 non-N2 and 46 N2 tests
with one skip, plus 155 TypeScript tests, in 235.75s and 237.47s. Standalone
N2 took 148.54s and 150.75s. These timings use the per-capture path-walk
improvement; every artifact is still read and hashed on each capture.

With scoped fixture grouping on 2026-09-30, three warm `test-fast` runs
passed 5,888 tests with one skip in 76.158s, 83.055s, and 83.353s by `tt`
(83.055s median). The complete `test` gate passed 5,888 non-N2 tests,
46 N2 tests, and 155 TypeScript tests in 242.97s.

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

`src/beliefs/` is the whole kernel. The repository and package were renamed from
`science` on 2026-08-30
([adoption ledger §5](../docs/designs/2026-08-03-redesign-adoption-ledger.md#5-repository-and-package-decomposition-ruled-2026-08-04)).
`science.identity.v1`, `science.belief.v1` and `contract: science` kept their names:
they are rule and contract identities, not the package, and renaming them would be a
contract succession. Most modules' docstrings cite the design sections they
implement. The main areas (paths under `src/beliefs/`), with the guide page that
explains each:

| area | where | guide |
|---|---|---|
| contracts and profiles | `contract/`, `contracts/`, `domains/`, `profile.py`, `mount.py`, `facets.py` | [foundations](../docs/guide/foundations.md#contracts-compile-into-profiles) |
| typed claims and their identity, the encoding `../ts/` shares | `claim.py`, `estimand.py`, `resolution.py`, `decode.py`, `identity/` (`science.identity.v1`), `projection.py` (`π_claim`, `I_claim`) | [claims and belief](../docs/guide/claims-and-belief.md#structure-not-prose-determines-identity) |
| the corpus and its writes | `root.py` (the composition root, the one module that imports `atoms`), `corpus.py`, `stored.py`, `permit.py`, `session/` | [writes, operations, and publication](../docs/guide/writes-operations-and-publication.md) |
| operations, acquisition and holdings | `intents/`, `report.py`, `acquisition.py`, `audit_operation.py`, `holdings/` | [writes, operations, and publication](../docs/guide/writes-operations-and-publication.md) |
| runs, datasets and replay | `spec.py`, `recipe.py`, `adapter.py`, `boundary.py`, `confinement.py`, `replay.py`, `verify.py`, `dataset.py` | [computation and reproducibility](../docs/guide/computation-and-reproducibility.md) |
| assessment and belief | `assess.py`, `admission.py`, `belief.py`, `policy.py` (`science.belief.v1`), `evaluation.py`, `composite.py` | [claims and belief](../docs/guide/claims-and-belief.md) |
| the world | `world/`, `relocation.py`, `audit.py` | [identity, world, and change](../docs/guide/identity-world-and-change.md) |
| views and coordination | `coordination.py`, `view_query.py`, `contract/coordination.py`, `contracts/coordination/` | [foundations](../docs/guide/foundations.md#views-and-coordination-are-governed-not-kernel) |
| publication | `publish.py`, `publication.py`, `publication_doors.py`, `transport.py` | [writes, operations, and publication](../docs/guide/writes-operations-and-publication.md) |

`src/beliefs/contracts/science/` and `src/beliefs/domains/biology/` are packaged
copies of the normative files under the repository root's `contracts/` and
`domains/`, which `tests/test_shipped_base.py` and `tests/test_shipped_biology.py`
hold byte-identical: edit the root file and copy it. Only the coordination
contracts live solely in the package.

The [adoption ledger](../docs/designs/2026-08-03-redesign-adoption-ledger.md)'s
current-state section is the authority for what is built and what still waits on
another artifact; the per-cut results records under [`../docs/plans/`](../docs/plans/)
are the evidence.
