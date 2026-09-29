# Repeatable reproduction and audit evidence

## Problem

The mm30 driver should reproduce its recorded measurements with explicit inputs and
a checkable verdict. Goal: `beliefs-cde4d9`. Restore the missing cut-31 transition
check first; establish a recipe's prerequisites before implementing it. Retained
audit reports need a concrete consumer before changing the measured artifact.

## Current behaviour and evidence

Inspected main at `b5225b2` on 2026-09-29; no recreation was run in this pass.

- `python/tools/reproduction/rederive.py::prior_state` reads the cut-22 archive.
  `cut31_corpus_state` appears only in `state.py` documentation within the driver;
  no committed test reads it. The reproduction record §11.5 and cut-32 results
  §3.3 describe the missing measurement: exactly `profile-mismatch: base`, zero
  records read. `audit_corpus` still returns early on that base mismatch.
- `justfile` has no reproduction recipe. `world.main` refuses an existing world;
  `paths.PRIOR` requires a sibling cut-22 archive. Later steps include `compose`
  and `read` followed by a separate `read --again` process. `close`, `rederive`
  and `read` can record a defect and still return zero, so a successful shell
  loop alone would not prove the measurement passed.
- `close.py` calls the bare evaluator. `audit_operation.py::audit`, introduced
  at `12a17b6`, appends an intent and publishes a report under the root lock.
  Cut-38 design decisions 2 and 12 deliberately limit that operation to one
  corpus and preserve the reproduction's read-only close step.
- `audit.py::audit_world` already returns a bound result with findings grouped
  by corpus. Persisting that result is the unresolved extension. Relocation
  (`634a3e9`) leaves the reproduction fixture in place and creates a separate
  research world; it is not part of recreating the fixture.

## Constraints

Preserve frozen cuts, archived predecessor corpora and historical measurements.
The adoption ledger and roadmap remain the status and delivery authorities.
Use the certified host for live capability-dependent measurements; do not infer
those results from unit tests. Driver scripts remain exercise instruments under
reproduction design §8. A small recipe is the intended ceiling.

Read-only evaluators gain no writes. A retained audit changes corpus and chain
state. A world report requires choosing root-local reports under a shared token
or corpus-qualified entries, with the corresponding act-report amendment.
No existing open research task found in this checkout owns the recipe inventory.

## Alternatives

1. Restore the transition check and inventory a minimal recipe with an explicit
   final verdict. This is the current lean: it addresses observed repeatability gaps.
2. Continue using the documented manual sequence. It avoids new orchestration,
   but leaves order and final assertions to each operator.
3. Expand reproduction to retain audit reports and design world report storage.
   Defer until a named consumer needs those artifacts; the existing evaluator
   already supplies read-only findings.

## Unanswered questions

- What inputs, invocation order and final assertions make the current driver
  reproducible by one recipe? Answered by `beliefs-b9c3ea`; see "Recipe
  inventory" below.
- Is the preserved cut-31 archive available and readable on the execution host?
  The implementer of `beliefs-0c1cc9` verifies it and reports missing input
  explicitly; its availability was not tested during this pass.
- Which consumer needs reports retained in the corpus or across a world?
  A future reproduction requirement or multi-corpus consumer supplies the wake
  condition. This pass found no such requirement in the inspected sources.

## Proposed decomposition

- `beliefs-0c1cc9`: scoped, P3/s/mid/direct; implement the repeatable transition
  measurement with explicit missing-input and wrong-verdict failures.
- `beliefs-b9c3ea`: P3/s/mid/direct research; inventory current recreation inputs,
  invocations and verdict. Completion updates this brief and writes a finding
  note on `beliefs-9e0b42` in the same commit.
- `beliefs-9e0b42`: briefed; the inventory below settles its scope as a recipe
  plus a verdict step and a prior-archive override. It stays an idea until scoped.
- `beliefs-b36632`: shelved until a reproduction measurement requires retained
  audit reports and accepts their mutation of the measured artifact.
- `beliefs-9d2b68`: shelved until a named consumer needs persisted world audit
  reports beyond the current read-only result.

The detached-runner exit-code idea `beliefs-7be4f1` was inspected but left
untouched: it concerns conformance process supervision, outside this cluster.

## Recipe inventory (`beliefs-b9c3ea`, 2026-09-29)

Traced at `5a6db10` by reading every module under `python/tools/reproduction/`,
`python/tests/test_reproduction_driver.py`, the two acceptance arms that read
the recorded state, the reproduction design's §4, §13 and §14, and the record's
§10, §11, §17, §22 and §23. The preserved work directories were listed and
their `state.json` and `findings.jsonl` read. No driver step, preflight or
confined run was executed, and nothing under `.work/reproduction/` was written.

### The sequence

From `python/`, each line its own process, stopping at the first non-zero exit:

    export PYTHONPATH=tools
    export SCIENCE_MM30_ROOT=<canonical main checkout>/.work/reproduction/<fresh name>
    export MM30_PREDECESSOR=<canonical predecessor root>
    uv run --frozen python -m reproduction.preflight
    uv run --frozen python -m reproduction.world
    uv run --frozen python -m reproduction.select_target
    uv run --frozen python -m reproduction.analysis_inputs
    uv run --frozen python -m reproduction.lists prepare
    uv run --frozen python -m reproduction.concepts
    uv run --frozen python -m reproduction.lists mint
    uv run --frozen python -m reproduction.type_target
    uv run --frozen python -m reproduction.hold
    uv run --frozen python -m reproduction.spec
    uv run --frozen python -m reproduction.run
    uv run --frozen python -m reproduction.belief
    uv run --frozen python -m reproduction.rederive
    uv run --frozen python -m reproduction.close
    uv run --frozen python -m reproduction.compose
    uv run --frozen python -m reproduction.read
    uv run --frozen python -m reproduction.read --again
    <the cut-31 transition step, owned by beliefs-0c1cc9>
    <the verdict step, below>

This is the design's §13 and §14 order. Three written orders disagree with it:
the estimand-typing and composite-claims plans omit `analysis_inputs`, and
`beliefs-9e0b42`'s body predates `lists`, `compose` and `read`.
`analysis_inputs` is required in a fresh directory: `select_target` rewrites
`target.yaml` whole, and `spec.render_snakefile` reads `value_row`,
`group_separator` and `positive_level` from it.

The fixture's first pass on 2026-09-16 ran steps 1 to 12 in about 100 seconds
by its `findings.jsonl` timestamps (15:03:58Z to 15:05:34Z).

### Inputs that must exist first

| input | where | state on this host, 2026-09-29 |
|---|---|---|
| a fresh work directory | `SCIENCE_MM30_ROOT`, on the certified volume beside the main checkout, spelled canonically (record §16: a symlinked spelling refuses the preflight) | to be chosen per run; `world` refuses an existing `world/` |
| the predecessor corpus | `MM30_PREDECESSOR`; the driver's default under the home directory does not exist under this account (record §17) | present; 285 concept records, equal to the held list's count |
| the held dataset | `data/supp/orig/misund2022/GSE179929_gene_tpm.txt.gz` under the predecessor | present; 6,154,181 bytes, `sha256:c74ea661…`, equal to the recorded digest |
| the cut-22 archive | `<SCIENCE_MM30_ROOT>.cut22/` holding `corpus/corpus.yaml` and `state.json` with `spec_ref`, `assessment_ref` and `spec_identity` | present only as `mm30.cut22`, the fixture's sibling; a fresh directory has no such sibling |
| the cut-31 archive | `.work/reproduction/mm30.cut31/`, read by the transition step | present; not opened in this pass |
| the project venv, `bwrap` and the certified volume | `just setup`; `preflight` checks the last two | not run in this pass, so unverified today |

The cut-22 archive is the one input a recipe cannot supply as the driver
stands. `paths.PRIOR` is fixed to the work directory's name plus `.cut22`, and
`rederive.prior_state` raises `RuntimeError` when it is absent, after 10a and
10b have already been saved. Two routes: an environment override for
`paths.PRIOR` beside the two the module already reads, or a symbolic link at
the sibling path. `ReadView.opened_at` builds a plain read handle and does not
pass through `open_root`, so the link probably reads; that was not run and is
unverified. The override is the recommendation: it is explicit, and it fails
loudly on a missing archive exactly as today.

Recorded state is bound to absolute paths. `held_file` and the four
`*_file` keys are absolute, and `mm30.cut31/state.json` names
`mm30/mm30-concepts.txt`, inside its successor's directory. An archive is
therefore readable through `ReadView` but is not a directory the snapshot
steps can run in after it moves.

### What an exit code does and does not prove

| step | non-zero exit | recorded, exit still zero |
|---|---|---|
| `preflight`, `world`, `select_target`, `analysis_inputs`, `type_target` | every refusal (2) | nothing |
| `hold` | bad `held_file`; held bytes not reading as `Held` (2) | nothing |
| `run` | run refused, `AssessmentFinding`, replay refused (2) | a stored and derived identity that differ; a scope class other than `none` |
| `belief` | gather mismatch (2) | `admission_record` naming another identity (`defect`); the unpinned-biology negative failing (`defect`); admission refused; the evaluator refusing |
| `rederive` | none by return; a missing cut-22 archive raises | a verification contradiction (`defect`); any false restoration key (`defect`); an unequal re-derived belief |
| `close` | none | every `corpus_check` and `audit_corpus` finding |
| `compose` | `build_composite` refused (2) | a node receipt other than the expected one (`defect`) |
| `read --again` | none | two readings that differ (`defect`) |

A loop that stops at the first non-zero exit can therefore finish with a
corpus that failed its own checks. Five steps carry the measurement in
`state.json` and `findings.jsonl` alone.

### The minimal terminal verdict

One read-only step over the fresh directory's `state.json` and
`findings.jsonl`, exiting non-zero and naming each failed line. Everything
below is invariant across runs; run, assessment, verification and composite
record identities move with each confined run and are compared only with each
other.

- Authored identities equal the record's: `target`
  `proposition:concept-disease-stage-affects-protein-phf19`; `dataset`
  `dataset:gse179929`; `held_digest` `sha256:c74ea661…`; `dataset_address`
  `dataset:sha256:a6bf229e…`; `concepts_count` 285 with `concepts_address`
  `dataset:sha256:be3bf183…`; the three list addresses (`85b5e347…`,
  `08027c2e…`, `79e30710…`); `claim_identity` `780ace59…`; `spec_identity`
  `10e8bfce…`. The full values are in the fixture's `state.json`.
- The run: `assessment_outcome` `inconclusive`; `assessment_identity_stored`
  equals `assessment_identity_derived`; `verification_scope`
  `clean-environment`; `verification_verdict` `passed`; `scope_class` `none`;
  `admission` `Admitted`.
- The belief: `belief_answer` is `NoBelief` with reason
  `no-directional-outcome`; `rederived_equal` true.
- 10b: `comparison_report_stored`, `scope_equal`, `verdict_equal`,
  `report_identity_equal` and `spec_restored_identity_matches_run` all true;
  `audit_check.checked` true with no contradiction.
- 10c: all five `fresh_process_restoration` keys true;
  `prior_corpus_state.audit` equal to `["profile-mismatch: base"]`.
- Close: `corpus_check_findings` and `audit_findings` both 0; `log_verdict`
  `unresolvable` under `no-observer` and `validated` under `head-carrier`.
- Composite: no `composite_refusal`; `composite_receipt` equal to
  `{node:0: not-consulted, node:1: member, node:2: member}`; `reading_equal`
  true; `reading_rows` as acceptance arm U10 reads them.
- Transition: `cut31_corpus_state` as `beliefs-0c1cc9`'s step writes it.
- Findings: no line of class `defect` or `host`, and the lines outside
  `closed` are exactly the five the fixture's first pass left: step 2
  `corpus-work` (the modal-sorted refusal), step 4 `design-gap` and
  `corpus-work`, step 9 `corpus-work` (the unanchored chain under the empty
  observer set) and step 10 `design-gap` (Q10's spec half). Any other line
  fails the verdict.
- The tree: `spec` rewrites the tracked
  `python/tools/reproduction/analysis/workflow/Snakefile`; the committed file
  equals a render from the recorded inputs today, so `git diff --quiet` on
  that path after the run is part of the verdict.

Acceptance arms Q10 (`test_estimand_acceptance.py`) and U10
(`test_composite_acceptance.py`) already assert much of this, over the
fixture. They cannot be the recipe's verdict: Q10 pins the fixture's
run-derived `assessment_identity_derived`, which a fresh run moves, and both
are frozen cut modules.

### Recommendation

A recipe alone does not suffice. It needs two small additions to the driver,
both inside the design's "small recipe" ceiling and neither a runner
framework: a verdict step as above, and the prior-archive override. With
those and `beliefs-0c1cc9`'s transition step, a `just` recipe taking the work
directory and the predecessor root can report truthfully. `findings.jsonl` is
append-only and each `rederive` re-run adds two step-10 lines (the fixture
holds twelve pairs), so the verdict is defined over a fresh directory, not
over the fixture. Relocation (`relocate.py`) stays a separate operation and
is not part of the recipe.

Not established in this pass: that `preflight` passes on this host today,
that a recreation under the current contracts yields the recorded authored
identities (the in-place reads through record §22 show the fixture still
opens under the current profile, which is weaker), and that a linked prior
archive reads.
