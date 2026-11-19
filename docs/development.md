# Development

Type: guide; document types 1. This guide is for people and agents changing
beliefs: the layout and package map, the gates and focused test runs, the certified
host the real-engine tests need, the acceptance runner, the mm30 recreation, the two
architecture rules the tests hold closed, and how to add a record kind or a domain
contract. What the code must do is specified in [records.md](records.md),
[contracts.md](contracts.md) and [writes.md](writes.md); [guide.md](guide.md)
explains the model, and `AGENTS.md` carries the same gates in the form agents follow.

## Setting up

Clone `atoms`, `nodes`, `refs` and `beliefs` side by side. The Python dev group
includes `verifiably-refs` and RDFLib; refs is an editable sibling source, so every
Python development environment (including hygiene) needs it. Run `just registry-sync`
in refs to hydrate its generated registry before running beliefs commands. Then,
from the repository root:

```sh
just setup                            # checks refs hydration; installs ts/ dependencies
git config core.hooksPath .githooks   # once per clone
```

The Python side needs no install step: every Python command in the justfile runs
`uv run --frozen`, which builds the locked environment. In a worktree, setup links
the main checkout's refs sibling beside the physical worktree if the sibling is
absent. It never replaces an existing sibling or modifies its registry. A missing
or stale registry is an explicit error; inspect the selected refs checkout before
hydrating it. Use separate clean sibling checkouts when reproducible admission
requires revisions different from the shared development checkouts.

Python CI checks out refs at `c098faf964b097ef0016fc9e8aa69f3292c655f3`, hydrates
its registry and records its revision alongside atoms and nodes. The beliefs
maintainer or assigned implementer changes that SHA only in a reviewed change
requiring a refs API, fix or registry update: verify publication, record the old
and new revisions and registry fingerprints, and run affected tests and CI.
Atoms and nodes retain their default-branch CI policy. The uv lockfile pins package
versions; editable sibling revisions are established separately by Git.

## Offline external-source admission

`python/tools/admit_external_source.py` validates a separate candidate from a clean
committed mechanism checkout. It is a developer command, outside the installed
runtime. The shipped inventory includes the SI Brochure time vocabulary and its
[provisional register and admission receipt](contracts.md#source-ownership-admission).
Acquisition, semantic approval and production admission require separate authority.

Prepare a dedicated clean sibling layout containing beliefs, refs, atoms and nodes,
then run the frozen Python sync in beliefs. The refs sibling must be the reviewed
revision, with its generated registry hydrated. The command verifies the actual
import roots and Git revisions; `--refs-root` asserts that installed checkout and
does not alter Python's import path. Every Git revision cited in a public receipt
must be published and retrievable; verify this in the private run sheet. Python CI
must be green at the accepted mechanism commit before freezing the run sheet.

Create a separate linked beliefs worktree at exactly the mechanism checkout's
HEAD. Prepare its domain/register pairs, package copies, inventory and inventory
pin together, leaving the index empty. From the clean mechanism checkout:

```sh
uv run --frozen --project python python -I python/tools/admit_external_source.py \
  --candidate CANDIDATE --manifest MANIFEST --bindings BINDINGS \
  --refs-root REFS --refs-commit FULL_SHA --output NEW_RECEIPT
```

Manifest version 1 has exactly `version`, `source_id`, `namespace`,
`contract_identity`, `documents`, `resources`, `units` and
`semantic_review_sha256`. Documents match the ordered candidate normative pins;
resources has `ucum` and `qudt` pins of the same four-field form described in
[contracts.md](contracts.md#source-ownership-admission). Every qualified unit id
appears once with a bare case-sensitive `ucum` code and an exact full
`http://qudt.org/vocab/unit/` IRI or explicit null `qudt`. The semantic review
covers source provenance, permission, mapping meaning and any absence rationale;
its content digest binds the review without publishing its text.

Bindings version 1 has exactly `version` and `files`. The latter maps every required
`sha256:<digest>` to its explicitly resolved absolute regular-file path, including
the semantic review document. Resolve ancestor symlinks deliberately and record the
result privately; the command refuses implicit path resolution, leaf symlinks,
nonregular files, missing/extra bindings and mismatched bytes. It hashes and parses
the same read bytes. UCUM uses a supplied nonempty essence table with the declared
release. QUDT uses held Turtle only and requires the exact IRI as a subject typed
`http://qudt.org/schema/qudt/Unit`; imports and locators are never fetched.

The command validates the full candidate and historical continuity, verifies clean
code/configuration and rechecks frozen inputs before publishing. Only the two
literal checker pin values may change. Other permitted admission changes are the
inventory, added digest-named receipts, canonical/package SI Brochure pairs and
history, deletion of the synthetic series-time fixture, its Python/TypeScript
callers, and the two contracts/development reference documents. Other code,
dependency and configuration changes require a new reviewed mechanism.

A successful run writes deterministic public receipt metadata outside the candidate.
It does not write semantic approval or modify the candidate. Refusal exits 1 without
a receipt; invalid CLI usage exits 2. Existing output is never overwritten. Private
write staging and exclusive publication prevent partial success output.

Install the receipt at its digest-named repository path, update `RECEIPT_SHA256`,
finish the fixture/doc changes, and stage the complete admission. Before committing,
run this distinct check-only form from the clean mechanism:

```sh
uv run --frozen --project python python -I python/tools/admit_external_source.py \
  --check-staged CANDIDATE --receipt CANDIDATE_RECEIPT
```

It verifies the index, receipt and pin-only checker difference without held payloads
or candidate code execution. It writes nothing and refuses unstaged changes. Commit
all admission artifacts together; ordinary pre-commit hygiene then checks the
installed metadata. Receipt provenance identifies the clean mechanism commit, never
the future admission commit. A coordinated pin edit remains an independent review
obligation, not cryptographic proof of honest validation.

## Layout

```
python/src/beliefs/   the kernel, package `beliefs`
python/tests/         the test suite; tests/acceptance/ is run by `just test-acceptance`
python/tools/         fixture generators, the acceptance runner, the mm30 reproduction driver
ts/                   @verifiably/beliefs: the TypeScript mirror of the shared encoding
fixtures/             the parity corpus both test suites read and neither writes
contracts/, domains/  the normative base contract; shipped domain packs and canonical registers (`general`, `biology`)
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
`general` and `biology`), verified byte-identical by `test_shipped_general.py` and
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
Python jobs use `ubuntu-24.04`, whose loader-listing format the closure checker
supports; TypeScript jobs use `ubuntu-latest`. Ubuntu 26.04 loader support is not
established by these CI results.

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

`just mm30-phf19 WORK PREDECESSOR HGNC ENSEMBL [DECLARATION]` executes the selected
PHF19 gene-RNA **engineering demonstration** described in
[guide.md](guide.md#from-held-data-to-a-belief). The default declaration is
`python/tools/reproduction/phf19-inputs.json`; direct module invocation requires
`--declaration`. It selects the original proposition explicitly and never ranks
new candidates. PREDECESSOR must carry `science.yaml` and the four declared sources.
HGNC and ENSEMBL name the acquired complete HGNC 2025-09-05 TSV and compressed human
Ensembl 115/GRCh38.p14 GTF. The declaration pins all six inputs by SHA-256. The
small committed references under `fixtures/phf19/` are labelled synthetic and
cannot masquerade as the pinned real releases.

WORK must be a fresh absolute canonical path strictly below an explicitly supplied
host-local `WORK_ROOT`, outside this checkout, on the certified volume. There is no
`.work/` fallback, acquisition or host-configuration change. A storage path can be
off the certified tuple even on the same host; the kernel reports the exact
`CapabilityUnavailable` mismatch. Choose a certified local root through an explicit
environment override for that invocation. Real execution requires its own
applicable authority; implementation tests confer none.

Each run holds about 121.1 MB (115.5 MiB) of exact reference bytes, plus the complete
HGNC member list, derivation and ordinary store overhead. It holds the GTF compressed.
The source holdings and mapping are explicitly rechecked through dataset and
holdings records plus actual byte hashes; digest-only procedure parameters are
not kernel dependency edges. Readback uses run-held copies, independent of the
acquisition directory. It recomputes full HGNC membership and the selected mapping.

The workflow uses a local copy under WORK/bundle/analysis and preserves the tracked
Snakefile. `phf19-report.json` records the exported effect and terminal obligations;
a fresh process reconstructs stored spec, assessment, comparison and belief. To
repeat readback, from `python/` run `PYTHONPATH=tools uv run --frozen python -m
reproduction.phf19 --readback WORK` with the same WORK_ROOT. Missing closure, changed
bundle/parser, mismatched pins, a step defect or differing recovery fails the
command. It creates no composite or legacy cut output.

PHF19 readback checks the current head's pins. To reconstruct a historical
profile from a checkout that can parse the full chain, select the exact mm30
pair. Use the digest after `mm30:` in the original corpus manifest. The example
uses the Python API from `python/` with `PYTHONPATH=tools`.

```python
from beliefs.mount import compile_mount_profile
from reproduction import vocabulary

selected = vocabulary.revision(content_identity=mm30_digest)
profile = compile_mount_profile(corpus_root, available=(selected.contract,))
register = selected.register
```

Here `corpus_root` is a `Path` to the corpus with the original manifest.
The manifest must pin the shipped base and the original peer contracts must
be available. If the original base or peers are unavailable, or the head requires grammar
unavailable under the original base, recover from the original source revision
with its pinned peers.

The result is an unpaired computational demonstration over paired source inputs.
It does not certify independence, upstream assay validation or biological reuse.
The assay's unknown validation remains an explicit frozen assumption. A full real
recreation is separately owned by beliefs-dcce70, with renewed pre-mint inventory
and a smallest end-to-end pilot before any extended run; beliefs-9cbde6 owns its
independence assessment.

`just mm30-recreate WORK PREDECESSOR HGNC ENSEMBL` runs one fresh PHF19
demonstration under `WORK/phf19` and records the refusal of the historical causal
composite in `WORK/heritage-report.json`. It uses the packaged declaration and
additionally checks the pinned survival proposition and prognostic narrative
under `PREDECESSOR/entities/propositions/`. Both texts are retained under
`WORK/evidence/`. The HGNC and Ensembl arguments must be the release files.
Supplying historical cut directories in those positions fails before WORK is
created.

A successful exit requires the verified PHF19 report and fresh-process recovery.
The heritage report gives the two grounds for refusal, the source pins, and the
stored corpus and claim identities. The first proposed edge needs a causal
stage effect on protein, while the stored target measures a statistical
gene-RNA contrast. The second needs a causal effect on overall survival, while
the pinned source records an observational association with patient survival
and the narrative describes prognostic information. To repeat ordinary PHF19
readback after recreation, pass `WORK/phf19` to `--readback`. Treat files from a failed or interrupted command as diagnostic. An interruption
before the final directory sync can leave an unacknowledged report. Every retry
requires a fresh WORK.

## Working with series evidence

Series payloads are finite canonical JSON, supplied through exact local store
locations. A caller selects and authorizes the stores and locations; neither a
corpus reader nor a URL holdings observation discovers or acquires them.
For example, with a compiled `profile`, explicit `records`, one authorized
`store_root` / `store_id`, and a complete `selected_locations` map:

```python
from beliefs.root import open_series_store
from beliefs.series.evidence import SeriesEvidence
from beliefs.series.reader import read_series

with open_series_store(store_root, store_id=store_id) as store_read:
    evidence = SeriesEvidence(
        stores={store_id: store_read}, locations=selected_locations
    )
    checked = read_series(
        series_ref, profile=profile, records=records, evidence=evidence
    )
```

Keep the store contexts open while using their readers. Locations cover every
reachable descriptor, table, origin, anchor and predecessor; tree locations also
require their manifest. Use the same explicit evidence argument at estimand
build/freeze and supply `series_evidence`, `profile`, `records` to execution,
replay and new verification. Every stage rechecks, rather than reusing `checked`.
The [boundary table](records.md#series-bindings) documents records-only portability
and the different unchecked/inconclusive/contradicted outcomes.

Elapsed axes and event lags require the activated declarations at the exact
[base time roles](contracts.md#base-contract), including defining-source identity
and licensed exact units. The base map alone activates no SI vocabulary. The
canonical `domains/si-brochure/DOMAIN.yaml` supplies the admitted vocabulary for
these tests through the Python time accessor and TypeScript parity reader. The
former unmapped synthetic series-time fixture is removed. All six register entries
remain provisional; passing interface tests does not establish empirical standing.
TypeScript covers contract parsing/compilation parity; it has no series target
reader.

Base v5 uses estimand grammar `science.estimand.v4`. A v4-pinned corpus refuses
validated reads; no compatibility reader or automatic migration is provided.
Retain its bytes and select an explicit recreation/migration procedure before
using v5 against it. A pin edit is not recreation. Assessment identity and facet
tags remain `science.assessment.v2` and `science.assessment-facet.v2`; embedded
target/spec bytes and keys change, while coarse claim identity can remain stable.
The series reader accepts v2 table/view/origins/anchors and v1 clock maps only;
stored v3-tagged specs and pre-v2 series objects refuse by name. Event preparation
checks have focused portable and certified workflow coverage in `tests/series/`;
`tests/acceptance/test_event_preparation_acceptance.py` exercises the durable
mapped-event roundtrip. A generation build runs the forced full code check and
`test-push` on a clean commit before its acceptance pilot and full certified sweep.
Those deliberate checks do not change the local automatic-broad policy.

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
`fixtures/scope-relations.json` is the shared scope-relation vector: declaration
schema, local qualification, parse and compile refusals, and graph consistency
cases, read by `tests/test_scope_declarations.py`, `tests/test_scope_graph.py` and
`ts/tests/scope-relations.test.ts`. TypeScript compiles and validates scope-relation
tables but implements no scope comparison.

`fixtures/candidate-contracts.json` pins the content identities of the unshipped
candidate documents under `fixtures/contracts/candidates/` and of the successor
that tests derive from the shipped `general` document plus
`fragments/general-event-locked.yaml`. `tests/test_candidate_contracts.py`,
`tests/case_comparisons/test_candidates.py` and `ts/tests/candidate-contracts.test.ts` read it. The candidates are test fixtures:
they have no inventory row, no packaged copy and no source-ownership verdict.
A `general` revision moves the derived identity; recompute the row, or retire the
fragment when its rows ship.

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

1. Write the document with `lineage: genesis` and a canonical `defining_source.id`. Declare sorts with their bindings and
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
([history layout](contracts.md#profiles)). The biology version-1 genesis and twelve-entry canonical register ship at the
corresponding `domains/biology/` paths with identical packaged copies. Its generic
loaders use the same checks; unknown namespaces refuse with `ProfileError`. Field packs keep sorts,
instantiations and bridges in their own namespace and activate `general` explicitly;
`python/tools/check_shipped_contracts.py` verifies source ownership across all
shipped histories, the full standalone PHF19 chain and other reproduction contracts. Before admission, add the
canonical pair and exact hashes to `contracts/source-ownership/INVENTORY.json` and
update the checker's `SOURCE_INVENTORY_SHA256` in the same reviewed change. Compare
all existing reservations and historical pins; a coordinated pin edit does not
prove continuity. New lineages need a distinct justified source owner, and future
successors retain the canonical id. The original four metadata-free revisions
are exact byte-pinned exceptions, not a namespace-wide exemption.

The contract/register pair supplies authored definitions and their justified-use
limits; semantic consistency and known equivalent meanings require review. The
inventory is repository-only; the offline admission command supports the SI Brochure
lineage with held evidence, human semantic review and a pinned success receipt. It
does not add a runtime inventory or acquire publisher data.
Unshipped candidates retain joint ownership review outside this checker.

To revise the standalone PHF19 pair, work under `python/tools/reproduction/`.
Move the exact previous `mm30-phf19.yaml` and `mm30-phf19-register.json` bytes to
`mm30-phf19-history/<previous-contract-content-identity>/DOMAIN.yaml` and
`mm30-phf19-history/<previous-contract-content-identity>/REGISTER.json`.
Install the successor at the two head paths with an increased version,
`lineage: {successor: <previous-contract-content-identity>}` and
`defining_source.id` set to `urn:beliefs:definitions:phf19-stage-contrast-admissions`.
Its register describes the successor, covers its declarations and names the
immediate prior register identity in `previous`. Keep every earlier pair and
retained tombstone. Formatting and register prose in adopted files are
part of their exact-byte pins.

Relocate the previous inventory row's two paths and append the new authored
pair's row. Update `SOURCE_INVENTORY_SHA256` in the same reviewed change.
Compare both revisions of the inventory for reservation, alias, owner, adoption
and historical-pin continuity. Run `just check-hygiene` against the resulting tree.

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


### Domain re-pin checks

Run `just test-one tests/acceptance/test_corpus_repin.py` on the certified tuple
for manifest replacement and recovery evidence. Its fault backend delegates to
the real engine and interrupts both old-visible and target-visible transactions;
portable doubles do not establish those guarantees. Start with the module's
`test_repin_real_engine_journey` case when checking a new host setup. The focused
manifest, permit, capability and pin-recheck inventory tests cover the write
boundary, while world-view, consulted-contract and register tests cover readers.
