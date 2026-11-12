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
contracts/, domains/  the normative base contract; shipped domain packs and canonical registers (`general`)
tools/                vendored ops tools (tt, ops-check, ops-docs); never edited here
```

The kernel's main areas, under `python/src/beliefs/`:

| Area | Modules | Specified in |
|---|---|---|
| Contracts and profiles | `contract/`, `contracts/`, `domains/`, `profile.py`, `mount.py`, `facets.py` | [contracts.md](contracts.md) |
| Typed claims, identity and the shared encoding | `claim.py`, `estimand.py`, `resolution.py`, `decode.py`, `identity/`, `projection.py` | [records.md](records.md#identity) |
| Measurement values, records and read-side checks | `measurement.py`, `restriction.py`, `procedure.py`, `referent_mapping.py`, `proxy_model.py`, `classification_rule.py`, `aptness.py`, `dependencies.py`, `eligibility.py`, `comparability.py` | [records.md](records.md#measurement-records), [contracts.md](contracts.md#typed-restrictions) |
| The corpus and its writes | `root.py`, `corpus.py`, `stored.py`, `permit.py`, `session/` | [writes.md](writes.md) |
| Operations, acquisition and holdings | `intents/`, `report.py`, `acquisition.py`, `audit_operation.py`, `holdings/` | [writes.md](writes.md#operations) |
| Runs, datasets and replay | `spec.py`, `recipe.py`, `adapter.py`, `boundary.py`, `confinement.py`, `replay.py`, `verify.py`, `dataset.py` | [records.md](records.md#specs-runs-and-assessments) |
| Exposure events and reservation assignments | `reservation.py` (values, units, shared checks, view helpers), `stored.py` readers | [records.md](records.md#exposure-events-and-reservation-assignments) |
| Assessment and belief | `assess.py`, `admission.py`, `belief.py`, `policy.py`, `evaluation.py`, `composite.py` | [records.md](records.md#beliefs) |
| The world | `world/`, `relocation.py`, `audit.py` | [guide.md](guide.md#worlds-identity-and-change) |
| Views and coordination | `coordination.py`, `view_query.py`, `contract/coordination.py`, `contracts/coordination/` | [contracts.md](contracts.md#coordination-contract) |
| Publication | `publish.py`, `publication.py`, `publication_doors.py`, `transport.py` | [writes.md](writes.md#publication) |

`python/src/beliefs/contracts/science/` holds the packaged copy of
`contracts/science/CONTRACT.yaml`. `test_shipped_base.py` fails unless the pair is
byte-identical: edit the root file, then copy it. `python/src/beliefs/domains/` holds
the packaged copies of `domains/<namespace>/{DOMAIN.yaml,REGISTER.json}` (currently
`general`), verified byte-identical by `test_shipped_general.py` and
`python/tools/check_shipped_contracts.py`. The coordination contracts live only in the
package. The names `science.identity.v1`, `science.belief.v1` and `contract: science`
are rule and contract identities, not the package name, and stay as they are.

## Gates and focused runs

Every check and suite runs through the vendored timing wrapper `tools/tt`, which
records each run.

| Command | What it runs |
|---|---|
| `just test-one <args>` | A focused pytest selection, paths relative to `python/`: a file, `file::test`, or `-k "expr"` |
| `just --set one_cmd "cd ts && npx --no-install vitest run" test-one <filter> -t "<name>"` | A focused Vitest selection, filters relative to `ts/` |
| `just check-hygiene` | ops-check, `ops-docs check`, the document link and anchor check, the shipped-contract and register check, and `tasks check` |
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
module in its own `pytest` process, in sorted order, printing a summary table at the
end with each module's exit status and summary line and exiting 1 if any module
failed. It takes about 25 minutes. Each invocation works in a fresh directory under
the work root, removed afterwards, and registers a probe corpus there before the
first module. It errors and never skips:

| Exit | Meaning |
|---|---|
| 1 | At least one acceptance module failed; the summary table lists each module's exit status and summary line, followed by the failing set. |
| 2 | The probe was refused: the work root is not on a certified volume, or the host is off the certified configuration. The message gives the engine's words. |
| 3 | An old `SCIENCE_CUT<n>_ROOT` variable is set. The message names its replacement; unset it. |
| 4 | No acceptance modules were found. |
| 5 | An argument was given. The recipe takes none; narrowing would silently skip modules. |

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

Under base v3 the recreation cannot complete. The driver's contract layer
(`python/tools/reproduction/vocabulary.py`) compiles a profile from the shipped
biology pack and the v1 mm30 documents beside it; only the shared `general`
contract ships today, no biology pack ships yet, and base v3 refuses a v1 document,
so the first step that compiles that profile or types the claim fails. The documents
stay in place for the recreation that follows a biology v2 pack and an mm30 v2
contract.

New authors freeze an explicit `standing` with typed estimand and applicability,
including an evidence mode for each `SpecInput`. They hold the frozen normative
dependencies before publishing a spec or assessment. A model route names its
model procedure; calibrated-model also freezes its qualified empirical basis.
The belief step mints the verification, reopens the view and then evaluates the
claim. One assessed key returns its answer; multiple keys produce a
`multiple-assessed-propositions` finding and exit 2. Use `claim_view` to inspect
the answers and comparisons for every key instead of choosing one implicitly.

## The claim-identity parity fixture

`fixtures/claim-identity-v2.json` is the cross-language oracle for `π_claim` and
`I_claim` under `science.claim.v2`. `tests/test_parity_fixture.py` and `test_decode.py`'s
round trip read it, as does `ts/tests/parity.test.ts`, and no test writes it. It is generated by hand from
`fixtures/contracts/testing.yaml` and the base contract:

```
cd python && uv run --frozen python tools/generate_claim_identity_fixture.py
```

Regenerate it only when the claim grammar, the projection or the testing contract
changes, and review the diff: a test run never regenerates it. Its header pins the
claim domain, the identity encoding, the two contract paths and the compiled
profile identity; each row holds a claim's components as written, its projection,
its canonical bytes and its digest. The file is pure ASCII, with every non-ASCII
character escaped.

The vector covers, and `test_parity_fixture.py` asserts that it covers:

- both forms, every polarity tag (`inapt` reached both by a sign-inapt template and
  by the `null` form), every quantifier and every layer, each checked against the
  base contract rather than a hand-kept list;
- every binding kind on at least one referent: `release` (`entity`, `outcome`),
  `scheme` (`method`), `dataset` (`cohort`), `selection` (`event`), `run-output`
  (`product`) and `world-kind` (`procedure-spec`, through `within-model`);
- a `many` role with coefficients (`transforms`' `inputs`), one without
  (`correlates-with`'s `parties`), and an empty `min: 0` role (`facilitators`);
- `correlates-with` written in both member orders, as two rows with one digest;
- a `within-model` claim, the `promotes` bridge, and claim-side qualifiers,
  including two dimensions on one claim;
- a non-ASCII referent (`β-catenin`), a restriction spelled in NFD (`café` with a
  combining accent, composed only in the canonical bytes), and a supplementary-plane
  member beside a BMP member whose UTF-16 order is the reverse of their code-point
  order.

`fixtures/general-claim-identity-v2.json` is the companion frozen parity vector over
the shipped `domains/general/DOMAIN.yaml` contract and the synthetic consumer fixture
`fixtures/contracts/general-consumer.yaml`, verified by
`tests/test_general_integration.py` and `ts/tests/general.test.ts`. TypeScript reads
the source YAML documents directly (`parseBaseContract`, `parseDomainContract`,
`compileProfile`) and checks claim construction, symmetric `parties` ordering,
duplicate-after-NFC refusal, projections, canonical bytes and digests, while
compiled profile identities, package resource loaders, assumptions registers
and estimands remain Python-only. Contract content identity and additive succession
are shared, with `fixtures/contract-succession.json` checked by both languages.

Shipped domain resources keep the current `DOMAIN.yaml`/`REGISTER.json` pair and
preserve predecessors under `history/<contract-content-hex>/` in both canonical and
packaged directories. `beliefs.contract.shipped.load_domain_history` supplies the
same checked history to package loading and `check_shipped_contracts.py`; the latter
also enforces exact reachable inventory and byte equality. Tests use temporary
resource trees rather than replacing installed resources. General v2 preserves its
original v1 bytes in that archive; loading alone never changes a corpus pin.

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

1. Declare the kind in `contracts/science/CONTRACT.yaml`: its `role`, identity
   `domain`, required and covered facets, reader declarations and any relation
   signatures ([contracts.md](contracts.md#base-contract)). Keep
   `python/src/beliefs/contracts/science/CONTRACT.yaml` byte-identical.
2. Add its minting family to `KIND_ACTS` in `permit.py`; decide whether it is a
   coreference endpoint and an eligible retraction target. Retraction eligibility
   must agree with the contract's `retracts` signature.
3. Add a content-addressed builder in `stored.py` and a canonical, profile-free
   reader. Register whole-record readers in `_WHOLE_READERS` for `corpus_check`
   and `_refuse_facet_shapes` for ordinary and staging doors. Keep profile and
   held-dependency checks in the ordinary write door. A new write primitive or
   caller requires the closed write-entry inventories above to be reconciled.
4. Update every inventory pin in Python, TypeScript and acceptance tests. Regenerate
   the claim identity fixture, then run focused parity and declaration tests in
   both languages, affected behavior tests, the capability/permit/pin-recheck
   inventories and required hygiene/type checks under the execution policy.
5. Update [records.md](records.md#record-kinds), write-door documentation and the
   glossary with the behavior the code now admits. For the four measurement kinds,
   these steps cover the builders, readers, profile checks, staging guard and the
   eight eligible retraction targets; they add no write primitive or caller.

View and coordination kinds come from the coordination contract instead: add a
successor version under `python/src/beliefs/contracts/coordination/v<n>/`
([contracts.md](contracts.md#coordination-contract)), extend the versions
`shipped_coordination` accepts in `profile.py` (it lists them, `(1, 2, 3)`, and
names them in its error message; a new directory is never loaded until both
change), and add the kind to `KIND_ACTS` as above.

## Adding a domain contract

1. Write the document with `lineage: genesis`. Declare sorts with their bindings and
   identifier classes, templates with their roles, layers and forms (and an `edge`
   where composites need one), instantiations listing the sorts that fill each
   role, any bridges, and dimensions with their placement and `applies_to`; add
   `estimands` keyed `instantiation:<name>` or `bridge:<name>` where specs need
   them ([contracts.md](contracts.md#domain-contracts)).
   Measurement packs also declare quantity kinds, units, conversions,
   transformations, procedure and assumption kinds, measurement admissions and
   aspect sorts as needed. Declare applicability restriction forms explicitly.
   A calendar interval needs a named duration convention to resolve its unit
   when compared with another interval. A one-sided calendar restriction still
   narrows an unrestricted dimension.
   `fixtures/contracts/testing.yaml` uses every part of the grammar.
2. Load it with `load_domain_contract(path, base=shipped_base_contract(),
   predecessor=None)` and compile it with the base into a profile:
   `compile_profile(shipped_base_contract(), [contract])`.
3. Pin it in a new corpus's manifest: `adopt_manifest(profile=CorpusPins(...))`
   with the profile's base identity and activated contracts, then open writers
   with that profile.
4. To change the contract later, write a successor that names the old contract's
   identity, and retire identifiers instead of removing them
   ([contracts.md](contracts.md#succession-and-retirement)).

The package ships `general` under `domains/general/` and
`python/src/beliefs/domains/general/`: `shipped_domain_contract("general")` parses
the current v2 `DOMAIN.yaml` against its archived v1 predecessor and the shipped
base. `shipped_assumptions_register("general")` checks the register's `describes`,
complete eleven-entry coverage and immediate-predecessor `previous` link. The v1
files remain byte-identical in both copies' content-identity `history/` directory
([history layout](contracts.md#profiles)). Every other namespace refuses with `ProfileError`. Field packs keep sorts,
instantiations and bridges in their own namespace and activate `general` explicitly;
`python/tools/check_shipped_contracts.py` rejects non-`general` declarations in the
shared numerical and methodological tables across shipped and current reproduction
contract sources.

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
