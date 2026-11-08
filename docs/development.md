# Development

Type: guide; document types 1. This guide is for people and agents changing
beliefs: the layout and package map, the gates and focused test runs, the certified
host the real-engine tests need, the acceptance runner, the mm30 recreation, the two
architecture rules the tests hold closed, and how to add a record kind or a domain
contract. What the code must do is specified in [records.md](records.md),
[contracts.md](contracts.md) and [writes.md](writes.md); [guide.md](guide.md)
explains the model, and `AGENTS.md` carries the same gates in the form agents follow.

## Setting up

Clone `atoms`, `nodes` and `beliefs` side by side, as the README's Install section
shows: `python/pyproject.toml` takes both siblings from their checkouts. Then, from
the repository root:

```sh
just setup                            # npm ci for ts/; uv builds the Python env on first use
git config core.hooksPath .githooks   # once per clone
```

The Python side needs no install step: every Python command in the justfile runs
`uv run --frozen`, which builds the locked environment.

## Layout

```
python/src/beliefs/   the kernel, package `beliefs`
python/tests/         the test suite; tests/acceptance/ is run by `just test-acceptance`
python/tools/         fixture generators, the acceptance runner, the mm30 reproduction driver
ts/                   @verifiably/beliefs: the TypeScript mirror of the shared encoding
fixtures/             the parity corpus both test suites read and neither writes
contracts/, domains/  the normative base contract and biology pack
tools/                vendored ops tools (tt, ops-check, ops-docs); never edited here
```

The kernel's main areas, under `python/src/beliefs/`:

| Area | Modules | Specified in |
|---|---|---|
| Contracts and profiles | `contract/`, `contracts/`, `domains/`, `profile.py`, `mount.py`, `facets.py` | [contracts.md](contracts.md) |
| Typed claims, identity and the shared encoding | `claim.py`, `estimand.py`, `resolution.py`, `decode.py`, `identity/`, `projection.py` | [records.md](records.md#identity) |
| The corpus and its writes | `root.py`, `corpus.py`, `stored.py`, `permit.py`, `session/` | [writes.md](writes.md) |
| Operations, acquisition and holdings | `intents/`, `report.py`, `acquisition.py`, `audit_operation.py`, `holdings/` | [writes.md](writes.md#operations) |
| Runs, datasets and replay | `spec.py`, `recipe.py`, `adapter.py`, `boundary.py`, `confinement.py`, `replay.py`, `verify.py`, `dataset.py` | [records.md](records.md#specs-runs-and-assessments) |
| Exposure events and reservation assignments | `reservation.py` (values, units, shared checks, view helpers), `stored.py` readers | [records.md](records.md#exposure-events-and-reservation-assignments) |
| Assessment and belief | `assess.py`, `admission.py`, `belief.py`, `policy.py`, `evaluation.py`, `composite.py` | [records.md](records.md#beliefs) |
| The world | `world/`, `relocation.py`, `audit.py` | [guide.md](guide.md#worlds-identity-and-change) |
| Views and coordination | `coordination.py`, `view_query.py`, `contract/coordination.py`, `contracts/coordination/` | [contracts.md](contracts.md#coordination-contract) |
| Publication | `publish.py`, `publication.py`, `publication_doors.py`, `transport.py` | [writes.md](writes.md#publication) |

`python/src/beliefs/contracts/science/` and `python/src/beliefs/domains/biology/`
hold packaged copies of `contracts/science/CONTRACT.yaml` and
`domains/biology/DOMAIN.yaml`. `test_shipped_base.py` and `test_shipped_biology.py`
fail unless each pair is byte-identical: edit the root file, then copy it. The
coordination contracts live only in the package. The names `science.identity.v1`,
`science.belief.v1` and `contract: science` are rule and contract identities, not
the package name, and stay as they are.

## Gates and focused runs

Every check and suite runs through the vendored timing wrapper `tools/tt`, which
records each run.

| Command | What it runs |
|---|---|
| `just test-one <args>` | A focused pytest selection, paths relative to `python/`: a file, `file::test`, or `-k "expr"` |
| `just --set one_cmd "cd ts && npx --no-install vitest run" test-one <filter> -t "<name>"` | A focused Vitest selection, filters relative to `ts/` |
| `just check-hygiene` | ops-check, `ops-docs check`, the document link and anchor check, and `tasks check` |
| `just check-code` | ruff check, ruff format --check, pyright, tsc and biome |
| `just check` | `check-hygiene`, then `check-code` |
| `just test-fast` | All Python tests in parallel, plus the TypeScript tests Vitest selects as changed |
| `just test` | All Python tests, then the whole TypeScript suite |
| `just gate` | `check`, then `test` |
| `just test-full` | `test`, forced past the policy below |
| `just test-acceptance` | Every acceptance module on the certified host ([below](#acceptance-tests)) |

`.tt.toml` sets `automatic_broad = false`, so the broad targets it lists (`test`,
`test-fast`, `test-push`, `check-code`, `ci-python`, `ci-typescript`) are recorded
as skipped locally unless `TT_FORCE=1` is set. A skip is not a pass. `test-one`,
`test-full`, `test-acceptance`, `check-hygiene` and `setup` always run. Use
`just test-full` for deliberate suite evidence and `TT_FORCE=1 just gate` for the
whole gate.

The pre-commit hook runs hygiene and then `check-code`; a commit whose every staged
path matches the justfile's `docs_paths` runs hygiene only. The pre-push hook runs
hygiene, `check-code` and `just test-push` when every pushed ref goes to `origin`
and matches `ci_suite_refs`, and the full `just test` otherwise. CI
(`.github/workflows/ci.yml`) runs `just ci-python` on Python 3.11 and 3.13 and
`just ci-typescript` on Node 20 and 24 for every branch push, with `TT_FORCE=1`.

Two conventions the recipes depend on: `pytest` runs without an extra `-q`
(`addopts` already has one, and a second hides the summary line `tt` counts), and
`pyright` takes no path argument, because naming one narrows the check and hides
every diagnostic outside it.

## The certified host

`atoms` writes only on a host whose kernel and volume form a configuration it has
certified (see the [atoms README](https://github.com/verifiably/atoms#usage)).
Elsewhere every write fails with `CapabilityUnavailable`, and on a developer
machine that failure is a test failure, never a skip. CI cannot supply the
certified configuration, so it sets `VERIFIABLY_UNCERTIFIED_HOST=1`, which turns
only that exception into a skip whose message starts
`certified tuple unavailable on this host:`. A green CI run is therefore evidence
about the portable tests only. When a change touches the `root.py` boundary,
durability or publication persistence, run the affected tests with `just test-one`
on a certified host. When the reach is unclear, first run `TT_FORCE=1 just test-fast`
(about 90 seconds), which sweeps every capability-dependent test outside
`python/tests/acceptance/`; then `just test-acceptance` for the acceptance modules.

The work directories these tests use must sit on the certified volume, which a
tmpfs such as `/tmp` is not. They default to the ignored `.work/` directory beside
the main checkout, even when you run from a worktree:

- `BELIEFS_TEST_ROOT` (default `.work/tests`) holds the real-engine fixtures of the
  ordinary suite.
- `BELIEFS_ACCEPTANCE_ROOT` (default `.work/acceptance`) holds acceptance runs.

`test_project_root.py` refuses any unlisted directory at the top of the checkout, so
a new work directory goes under `.work/`. `atoms` also refuses a root reached
through a symbolic link (`ELOOP`): run from a checkout's canonical path.

## Acceptance tests

`python/tests/acceptance/` drives the real engine on a real volume and is excluded
from every other run (`addopts` ignores it). `just test-acceptance` runs it: each
module in its own `pytest` process, in order, stopping at the first module that
fails and returning its exit code. It takes about 25 minutes. Each invocation works
in a fresh directory under the work root, removed afterwards, and registers a probe
corpus there before the first module. It errors and never skips:

| Exit | Meaning |
|---|---|
| 2 | The probe was refused: the work root is not on a certified volume, or the host is off the certified configuration. The message gives the engine's words. |
| 3 | An old `SCIENCE_CUT<n>_ROOT` variable is set. The message names its replacement; unset it. |
| 4 | No acceptance modules were found. |
| 5 | An argument was given. The recipe takes none; narrowing would silently skip modules. |

Codes 2 to 5 have these meanings only before any module runs. Once the probe
passes, a non-zero exit is the failing module's own `pytest` exit code, and pytest
also uses 2 (interrupted, or a collection error) and 4 (a usage error); the
message printed above the exit tells the cases apart.

For a focused run of one module use `just test-one tests/acceptance/<module>.py`.

The ordinary suite refuses an old `SCIENCE_CUT<n>_ROOT` variable too, before any
test runs.

## Recreating the mm30 corpus

`just mm30-recreate WORK PREDECESSOR [CUT22] [CUT31]` recreates the mm30 reproduction
(the walk in [guide.md](guide.md#from-held-data-to-a-belief)) from the predecessor
mm30 project, whose root must carry a `science.yaml`. `WORK` must be an absolute,
canonical path that does not exist yet. `CUT22` and `CUT31` are the two archived
corpus states the transition steps read; they default to `mm30.cut22` and
`mm30.cut31` under `.work/reproduction/` beside the main checkout. The host needs
the certified volume and bubblewrap with unprivileged user namespaces, which the
first step checks.

The recipe runs each step of `python/tools/reproduction/` in its own process and
stops at the first non-zero exit. Some steps record a defect and still exit zero, so
the final `verdict` step, which reads what they recorded, decides whether the
corpus reproduced. The recipe also refuses to start, and fails at the end, if the
tracked Snakefile under `python/tools/reproduction/analysis/workflow/` differs from
`HEAD`. It deletes nothing and belongs to no gate.

## Two rules the tests hold closed

- **`root.py` is the one module that imports `atoms`.**
  `test_capability_boundary.py` (`TestTheCompositionRootIsTheOneAtomsImporter`)
  fails if any other module imports `atoms` or names an engine command. Behaviour
  that depends on engine types, such as classifying an engine exception, lives in
  `root.py` and reaches other modules through a seam callable it builds.
- **Every write entry point is inventoried.** A function that calls a write
  primitive must call `authority.require(...)` before its first effect, appear in
  `WRITE_ENTRY_POINTS` in `test_permit_boundary.py` with its act family, and have a
  `Case` in `test_permit_entry_points.py`'s `CASES`. The inventory is closed in both
  directions: an uninventoried caller and an inventoried function that no longer
  calls a primitive both fail, and the failure message names them.

## Adding a record kind

World kinds are declared by the base contract, so a new kind is a new base
contract. Every corpus pins the base it was made under, and a writer accepts only
the base the runtime ships, so existing corpora must be recreated under the new one.

1. Declare the kind in `contracts/science/CONTRACT.yaml`: its `role`, its identity
   `domain` if it is governed, its facets with `required` and `covered`, each new
   facet under `facets`, and any relations
   ([contracts.md](contracts.md#base-contract)). Copy the file to
   `python/src/beliefs/contracts/science/CONTRACT.yaml`.
2. Add the kind to `KIND_ACTS` in `permit.py` with the act families that may mint
   it (`test_permit.py` holds its keys equal to the world and coordination kinds),
   and decide whether it joins `stored.COREFERENCE_ENDPOINT_KINDS`.
3. Give it a way in. If `add` admits it, make the write boundary in `corpus.py`
   decode its facets; if it needs its own door, that door joins the write-entry
   inventory above.
4. Update the tests that pin the inventory and the profile's compiled identity
   (`test_shipped_base.py`, `test_profile.py`), run the TypeScript suite, which
   parses the same contract, and update [records.md](records.md#record-kinds).

View and coordination kinds come from the coordination contract instead: add a
successor version under `python/src/beliefs/contracts/coordination/v<n>/`
([contracts.md](contracts.md#coordination-contract)), extend the versions
`shipped_coordination` accepts in `profile.py` (it lists them, `(1, 2, 3)`, and
names them in its error message; a new directory is never loaded until both
change), and add the kind to `KIND_ACTS` as above.

## Adding a domain contract

1. Write the document with `lineage: genesis`. Name each operator's sorts, layers
   and dimensions, and add `estimands` and `edges` where specs and composites need
   them ([contracts.md](contracts.md#domain-contracts)).
2. Load it with `load_domain_contract(path, base=shipped_base_contract(),
   predecessor=None)` and compile it with the base into a profile:
   `compile_profile(shipped_base_contract(), [contract])`.
3. Pin it in a new corpus's manifest: `adopt_manifest(profile=CorpusPins(...))`
   with the profile's base identity and activated contracts, then open writers
   with that profile.
4. To change the contract later, write a successor that names the old contract's
   identity, and retire identifiers instead of removing them
   ([contracts.md](contracts.md#succession-and-retirement)).

To ship a pack with beliefs, put it at
`python/src/beliefs/domains/<namespace>/DOMAIN.yaml`, where
`shipped_domain_contract(namespace)` reads it as a genesis contract. The biology
pack also keeps a normative copy at `domains/biology/DOMAIN.yaml`, which must stay
byte-identical.

## When a check fails

- **`ops-docs check` reports drift in README.md or AGENTS.md.** Their generated
  regions come from `identity.toml` and `tools/family.toml`; run
  `python3 tools/ops-docs write`, never edit the regions by hand.
- **`CapabilityUnavailable` on a developer machine.** The host or the work root is
  off the certified configuration; see [The certified host](#the-certified-host).
- **`test_project_root.py` fails.** A run left a directory at the top of the
  checkout; move its default under `.work/`.
- **The permit inventory tests fail.** Their message names each uninventoried
  caller or stale entry; see [Two rules the tests hold closed](#two-rules-the-tests-hold-closed).
- **A shipped-copy test fails.** A root contract and its packaged copy differ; copy
  the root file over the packaged one.
