# Repeatable reproduction and audit evidence

## Problem

The mm30 recreation should detect contract drift through a fresh execution with a
checked verdict. Goal: `beliefs-cde4d9`. The recipe and transition measurement have
landed; `beliefs-a49ab4` now asks for a repeat cadence. Establish what evidence must
survive each run before making repeated execution routine.

## Current behaviour and evidence

Checked against main at `c1418e7` on 2026-10-13.

- `just mm30-recreate` landed at `a819f23` (`beliefs-9e0b42`). It requires a
  fresh canonical work path, predecessor data and cut-22/cut-31 archives; it
  runs the driver steps and terminal verdict, checks the tracked Snakefile,
  and deletes nothing. It is outside the test gates.
- Reproduction record §25 reports one passing fresh run on 2026-09-30:
  53 s and about 423 MB. §25.3 does not establish a second agreeing run;
  §26 reads the existing fixture under cut 44, which is a different check.
- `reproduction.verdict` reads only `state.json` and `findings.jsonl`.
  Rechecking those saved assertions does not execute the current kernel.
  The earlier inventory below records absolute paths in retained state;
  verdict readability alone does not prove replay or diagnostic completeness.
- `beliefs-6f2c2b` owns the missing `composite_identity` pin. Its 2026-09-30
  note explicitly keeps `.work/reproduction/mm30-fresh-2026-09-30` for a
  read-only verdict check. That directory is excluded from future cleanup.
- `beliefs-0c1cc9` delivered the transition measurement. The audit evaluator
  remains read-only; retained operation reports are separate, shelved work.

## Constraints

Preserve frozen cuts, historical measurements, fixtures, predecessor data and
cut archives. The existing recipe's no-deletion contract remains intact.
Live capability evidence requires the certified host and volume. No live
recreation or retention experiment was performed by this scope pass.

The driver remains an exercise instrument under reproduction design §8.
Use existing task recurrence rather than introducing a scheduler. This project
has no declared shared-resource needs; a future quiet-host requirement would
need an explicit vocabulary entry before a task can carry that need.

## Alternatives

1. A recurring tracker task, with a fresh directory per run and retention
   defined from the artifact inventory. Current lean: this decouples the
   measurement from cut publication and uses existing tooling.
2. A fresh recreation at every cut discharge. This checks every transition,
   but adds host prerequisites and retained output to every discharge.
3. Keep the current manual cadence. It requires no new procedure, but leaves
   drift detection dependent on someone remembering to recreate the corpus.

## Unanswered questions

- Which artifacts are needed for diagnosis or replay beyond the two files
  read by the verdict, and which depend on their original paths?
  `beliefs-566bad` will trace their consumers and record an explicit table.
- Can future passing runs retain bounded evidence safely, while failures
  remain inspectable? The same research will recommend a retention boundary;
  it will not delete data or treat historical directories as disposable.
- What interval is justified once retention is known? Re-scope
  `beliefs-a49ab4` with the research recommendation before enabling recurrence.
  No cadence is installed by this brief.
- Which consumer needs persisted audit reports? Still the wake condition for
  the two shelved audit ideas; recurrence alone does not establish that need.

## Proposed decomposition

- `beliefs-566bad`: P3/s/mid/direct, inventory retention and path dependencies
  read-only, update this brief, and wake `beliefs-a49ab4` with an explicit
  `--no-reviewed` finding before merging its result.
- `beliefs-a49ab4`: briefed, remains an idea depending on `beliefs-566bad`.
  Preserve its original source material; re-scope once retention is settled.
- `beliefs-6f2c2b`: existing P3/xs/low/direct verdict-pin task, unchanged.
- `beliefs-0c1cc9`, `beliefs-b9c3ea`, `beliefs-9e0b42`: completed transition,
  invocation inventory and recreation recipe; do not duplicate them.
- `beliefs-b36632` and `beliefs-9d2b68`: remain shelved until a named consumer
  requires retained corpus or world audit reports.

### Recipe inventory (`beliefs-b9c3ea`, 2026-09-29)

The inventory below preserves the pre-implementation evidence. Its missing
recipe and override landed at `a819f23`; its composite-identity classification
was corrected by `beliefs-6f2c2b`'s finding, whose code change remains open.
The dated limitations describe that inventory pass, not the current recipe.

Traced at `5a6db10` by reading every module under `python/tools/reproduction/`,
`python/tests/test_reproduction_driver.py`, the two acceptance arms that read
the recorded state, the reproduction design's §4, §13 and §14, and the record's
§10, §11, §17, §22 and §23. The preserved work directories were listed and
their `state.json` and `findings.jsonl` read. No driver step, preflight or
confined run was executed, and nothing under `.work/reproduction/` was written.

#### The sequence

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
    uv run --frozen python -m reproduction.transition --archive <the cut-31 archive>
    <the verdict step, below>

This is the design's §13 and §14 order. Three written orders disagree with it:
the estimand-typing and composite-claims plans omit `analysis_inputs`, and
`beliefs-9e0b42`'s body predates `lists`, `compose` and `read`.
`analysis_inputs` is required in a fresh directory: `select_target` rewrites
`target.yaml` whole, and `spec.render_snakefile` reads `value_row`,
`group_separator` and `positive_level` from it.

The fixture's first pass on 2026-09-16 ran steps 1 to 12 in about 100 seconds
by its `findings.jsonl` timestamps (15:03:58Z to 15:05:34Z).

#### Inputs that must exist first

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

#### What an exit code does and does not prove

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

#### The minimal terminal verdict

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

#### Recommendation

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
