# The mm30 reproduction — design

**Date:** 2026-09-05
**Status:** approved in session 2026-09-05 (the course-correction session);
**run 2026-09-05** — the record is `../../designs/2026-09-05-mm30-reproduction.md`
and its commit re-ranked the roadmap. This document is a measurement design in the typing exercise's
shape (`../../designs/2026-08-07-corpus-survey-and-vocabulary-admission-design.md`),
not a slice design: it selects no cut scope, freezes no guarantee row, and
its deliverable is a dated record, not code that ships.
**Scope:** reaching the first computed belief over a real record through the
`beliefs` kernel *as a library*, before the daily surface exists — one
proposition of the predecessor's mm30 corpus, reproduced under this system,
with one held dataset, one run under confinement, one verification and one
admitted assessment — and writing down, before the run, what is expected to
refuse, so that every refusal is classified as a design gap, corpus work, or
a defect rather than worked around.

**Inherits:** the adoption ledger's §0 (records are reproduced, never
migrated; `proto-science` is heritage and not a dependency) and §3's
standing prerequisite ("a second corpus … has to be authored"); the user and
autonomy layer design's decision 3 and §8 success criterion
(`2026-08-29-user-and-autonomy-layer-design.md`); the roadmap design's §4.0
as amended 2026-09-05 (`2026-08-29-implementation-roadmap-design.md`), under
which this lane's findings move boundaries on or off the path; the review
disposition record's §5.5 discipline of predicting in writing before the run;
and the typing exercise's rule that the exercise mints no kind and admits no
vocabulary field (`../../designs/2026-08-07-multi-corpus-typing-exercise.md`).

## 1. Problem

The kernel is implemented through conformance cut 18. Between 2026-08-07 and
2026-09-04 eighteen cuts closed 93 of 161 guarantee rows, and in that time no
real record touched the system. The last measurement over a real corpus was
the typing exercise of 2026-08-07, which ran `build_claim` over the
predecessor's propositions and persisted nothing, because no persistence
boundary existed yet. Every boundary the success criterion needs now exists in
some form — the composition root and write families (cuts 4–5), the world
registry and holdings (cuts 6–10), run confinement with `clean-environment`
reachable (cut 13), the workflow surface (cut 15), belief under
`science.belief.v1` (cut 2) — and each has been exercised only by fixtures its
own designers wrote.

The typing exercise is the precedent for why that matters. It was predicted
to confirm two figures and instead withdrew one claim outright ("no
constructor can" reach the 27 title-stated records), found 25 records that
refuse on argument sort, and found that no corpus other than mm30 has a claim
vocabulary at all. None of that was visible from the fixtures. The same kind
of finding is waiting behind the persistence, run and belief seams, and the
cheapest way to get it is to push one real proposition through them.

The user and autonomy layer design schedules this as sub-project 4, after
the command framework, the biology pack and the writer session. Its success
criterion is the right one. Its position is not: the first belief does not
need a command, and every week the surface is built against fixtures is a
week the errors compound.

## 2. Decision

**Run the reproduction now, through the kernel as a library, as a lane
beside the two on-path kernel lanes.** It is a measurement: it produces a
dated record, findings, and design amendments filed through the lane that
owns each surface. It produces no cut, no row, no new kind, no vocabulary
admission, and no code under `python/src/beliefs/`.

Three rules from the inheriting documents bind it and are restated so they
are not re-derived:

1. **Reproduce, never migrate.** No record is copied from the predecessor's
   `multiple-myeloma` project. Its propositions are re-authored as typed
   claims through `build_claim`; its datasets are re-held by content
   identity; its analysis is re-run. The predecessor is read for what to
   reproduce and for nothing else.
2. **A refusal is a finding.** The reproduction never repairs, retries with
   altered inputs, or writes around a `Refused`. Each refusal is classified
   (§7) and the run continues only past refusals classified as corpus work
   the reproduction itself can do.
3. **The stop rule inverts.** Cut 1's §5.5 stopped at the last fully
   designed seam and computed no belief. This exercise stops at *nothing
   short of the belief evaluator's answer* unless a refusal it cannot
   classify as corpus work stands in the way; then it stops there, records
   the boundary, and that boundary is on the path.
4. **Three answers are terminal, and none licenses a second attempt.** The
   target, its frozen spec and its interpretation rule are fixed at step 4
   and are not changed afterwards to obtain a belief. `Belief` closes the
   measurement. So does `NoBelief(reason)` when the reason is one the record
   can attribute: `no-directional-outcome` means the frozen interpretation
   rule read the run as `inconclusive`, which is a scientific result and is
   recorded as one; `no-eligible-assessment` is terminal only once the
   admission refusal's reason and step 7's derived scope have been read and
   classified under §7, because a scope short of `clean-environment` has
   more than one cause. `derive_scope` (`replay.py`) returns
   `same-environment` when the recipes agree and the replay's receipt fails
   to qualify — missing capabilities or no fresh instance — and that is the
   host's, recorded as a host finding. It returns `not-certified` when
   either closure is non-conforming or the recipes disagree, and that is an
   authoring error in the spec, recipe or workflow, or a defect, and is never
   attributed to the host. `Refused(reason)` is a §7 finding. A `NoBelief`
   of either kind is a *complete* run of the path, and steps 9 and 10 still
   run over whatever it left on disk.

## 3. What is reproduced

The predecessor's mm30 project — `cancer-types/multiple-myeloma` under the
cancer collection — holds 334 propositions, 307 of them structured
(`subject`, `predicate`, `object`; 224 under `affects`), 274 dataset records,
six workflow definitions with a Snakemake entry point under `workflows/`,
and about 16 GB of held data under `data/`, including per-accession GEO
expression matrices under `data/geo/`.

**The target is one proposition, chosen by the exercise under four
criteria**, recorded in the results with the alternatives it beat:

- **structured** — among the 307, so it types today under mm30's operator
  vocabulary from the typing exercise, with no grammar work;
- **empirical** — `claim_layer` is an empirical layer, and its evidence in
  the predecessor is a within-dataset association the predecessor computed
  itself, not a literature assertion;
- **locally held** — the dataset it rests on is a file already under
  `data/`, so no acquisition from outside the system is needed
  (`url-retrieval` stays off the path);
- **small** — one dataset, one association score, expressible as a
  single-rule or two-rule Snakemake workflow whose closure the confinement
  boundary can materialize in minutes.

A within-dataset gene-level association against a clinical covariate in one
GEO accession is the expected shape. If no proposition meets all four, the
exercise relaxes *small* first and *locally held* last, and records which.

## 4. The path

Each step names the kernel seam it crosses. Steps are taken in order; the
record states where each stopped.

| # | step | seam | governed record it should leave |
|---|---|---|---|
| 1 | Register a world root and adopt one fresh corpus on the certified volume beside the checkout | `root` and the world registry (cuts 6, 9) | the corpus manifest and its registry entry |
| 2 | Type the target proposition and the handful of propositions its analysis plan names, under the biology vocabulary the typing exercise compiled, and mint them under a full `Authority` | `build_claim`, `CorpusWriter.add` (cuts 1, 4, 17) | `proposition` records with typed claims |
| 3 | Hold the dataset: observe the local file's bytes and locator, mint the dataset record carrying the `empirical-observation` facet | the holdings boundary's local arm (cut 10), `stored.is_empirical_observation` | a `dataset` record and a `holdings-observation` |
| 4 | Freeze the analysis spec and its recipe: the Snakemake definition snapshot, the held input by address, the declared output | spec freezing and closure construction (cuts 3, 15) | the frozen spec and its closure |
| 5 | Execute the run under the confined boundary policy on this host | `execute_assessment_run` under confinement (cut 13) | the run record, its launch attestations, the act-report |
| 6 | Derive the assessment: the frozen spec's interpretation rule, through its bound `RuleImplementation`, over the run's result; an `AssessmentFinding` is machinery failure and a §7 finding, never an outcome; persist the derived value | `build_assessment` (cut 3) | an `assessment` record with its `assesses` edge to the target |
| 7 | Verify: replay, compare, derive scope | `build_verification`, `derive_scope` (cuts 3, 13) | a derived `AssessmentVerification`; whether `clean-environment` is reached on this host |
| 8 | Admit and compute belief under `science.belief.v1` | `admission_record`, `belief.evaluate` (cuts 2, 13) | `Belief`, `NoBelief(reason)` or `Refused(reason)`, under §2 rule 4 |
| 9 | Close the corpus: `corpus_check`, the corpus-local semantic audit, log verification | `audit`, `world/verify` (cuts 8, 18) | zero findings, or each finding classified |
| 10a | Re-derive the belief: from the corpus on disk alone, in a fresh process, recompute step 8's answer | `evaluation.gather` over stored records | equal, or the reason it cannot be |
| 10b | Reconstruct the verification evidence: from the corpus on disk alone, recover step 7's comparison report and recompute its scope | whatever is stored | recovered, or the member that is missing |

Step 10 is where the success criterion's phrase "every step a governed
record" is measured, and its two halves are measured separately because they
can disagree: `evaluation.gather` reads a stored verification's assessment,
scope and verdict through `stored.verification_value` and needs no comparison
report, so 10a can pass while 10b fails. The roadmap decision on
`verification-publication` rests on 10b (§6, question 3).

## 5. Predictions, written before the run

On the discipline the disposition record and the typing exercise set: a
prediction that fails is a finding about the predictor, and a prediction
confirmed for a different reason is recorded as such.

- **P1 — authoring dominates.** Typing the target and its plan's
  propositions is the largest cost of the exercise, larger than the run. No
  more than ten propositions need typing for one belief. This is the
  measurement behind the layer design's `claim` command and behind the
  ledger's "has to be authored" prerequisite.
- **P2 — the facet is stamped, not checked.** Step 3 succeeds by writing an
  `empirical-observation` facet with whatever payload the author chooses,
  because `is_empirical_observation` reads presence only. Nothing refuses
  a dataset that is not an observation. This is expected to be the first
  finding filed, to the `domain` lane, which owns facet compilation.
- **P3 — the local hold works unchanged.** A holdings observation over a
  local file under the cut-10 local arm needs no amendment.
- **P4 — the run reaches the boundary; the scope is measured, not
  predicted.** The confined launch runs the analysis or refuses at the
  platform probe; it does not fail in between. Which scope `derive_scope`
  reaches is what step 7 measures. A scope short of `clean-environment` is
  recorded, not repaired, and is classified by §2 rule 4 — `same-environment`
  to the host, `not-certified` to authoring or defect.
- **P5 — the belief re-derives; the verification evidence does not.** Step
  10a passes: the stored projection carries assessment, scope and verdict,
  which is all the evaluator reads. Step 10b fails: step 7's
  `AssessmentVerification` is in-memory, only its `admission_record`
  projection is written, and no stored record carries the comparison report
  or lets scope be recomputed (cut 18 §7). 10b is what puts
  `verification-publication` on the path, where the 2026-09-05 re-rank
  provisionally placed it; 10a passing is not evidence against it.
- **P7 — the assessment derives without a finding.** Step 6 returns an
  `AssessmentValue`, not an `AssessmentFinding`, on the first run: the
  interpretation rule is authored for this target and the run's result is
  the shape it expects. A finding here is a defect in the rule's authoring
  or the recipe's result manifest, classified under §7.
- **P6 — at least one banked design is amended.** Not which. The typing
  exercise amended the kernel design and withdrew a ledger claim; a run
  through five more seams is not expected to amend nothing.

## 6. Questions this exercise answers

Three questions the re-rank of 2026-09-05 could only provisionally answer,
each named in the roadmap's tier-1 placements:

1. **How much of the biology pack does the first belief need?** The typing
   exercise left two vocabularies under `python/tools/vocabularies/`,
   `mm30-modal-sorted.yaml` and `mm30-unsorted.yaml`, and both bind only the
   placeholder `mm30-entities` namespace at release `2026-08-07`; neither
   exercises a GO, HP, EFO or MONDO binding, so typing under either measures
   nothing about the pack. The exercise names which vocabulary it types
   under, and answers this question only if it adds explicit bindings for
   the target's own terms under a named ontology release and records
   whether a `member` verdict needed an exact release pin or `not-consulted`
   sufficed to mint. If it types under the placeholder alone, the pack
   requirement is reported as **unmeasured**, and what is measured is the
   floor: the operator vocabulary and referent set the pack must at least
   reproduce.
2. **Does a single-corpus dogfood need world resolution?** Whether any step
   of §4 resolves an address across corpora or returns a resolution state
   the registry alone cannot give. If none does, `world-resolution` stays
   last on the path and the dogfood's `next` can be built over one corpus.
3. **Is a stored verification required by the success criterion?** Step
   10b's outcome, never 10a's. If 10b fails as predicted,
   `verification-publication` is on the path and its slice design is drawn
   next in the `write-path` lane; it moves off the path at the next re-rank
   only if the comparison report and scope are recoverable from the corpus
   alone, whatever 10a says.

And one the roadmap carries as a question with no row: **where a typed claim
is authored** for a corpus that has none. The record states what authoring
cost, what `build_claim` refused and why, and what a `claim` command must do
and must refuse — the input to the layer design's sub-project 4, measured
rather than designed from the fixtures.

## 7. Findings discipline

Every refusal, and every place the exercise wanted a seam that did not exist,
is one finding with one classification:

| class | meaning | where it goes |
|---|---|---|
| **design gap** | a banked design does not say what happens here, or says something the kernel cannot do | a dated amendment to the owning design, filed through the lane that owns the surface (roadmap concurrency rule 6); or an `open-questions.md` entry when it is a question rather than an omission |
| **corpus work** | the kernel is right and the input is not yet in the shape it requires — an untyped claim, an unpinned release, an unheld file | done by the exercise if it is the exercise's own work; otherwise recorded as the authoring cost P1 measures |
| **defect** | the kernel does not do what its design and its cut say it does | a failing test first, in the owning lane; the reproduction does not patch the kernel |

A finding never becomes a suppression, a configuration entry, a fixture
edit that makes it pass, or a second write path. The predecessor's escape
hatches (layer design §4.3) do not exist here, and this exercise is the
first place that rule meets real input.

## 8. Deliverables

1. **The record**, `docs/designs/<date>-mm30-reproduction.md`, in the typing
   exercise's shape: the target and the alternatives it beat; each step of
   §4 with where it stopped and what it left on disk; each prediction of §5
   with its outcome and, where confirmed for a different reason, that
   reason; the answers to §6; and every finding of §7 with its class and
   where it was filed.
2. **The corpus**, on the certified volume beside the checkout, left in the
   state the record describes, with its world root and log — the first
   corpus this system produced, and the seed of the dogfood's world.
3. **The scripts**, under `python/tools/reproduction/`, that drive §4 —
   throwaway by declaration: they are the exercise's instrument, not a
   surface, and sub-project 4's commands are written from what they show
   rather than by promoting them.
4. **The amendments and questions** of §7, each in its owning document.
5. **A re-rank.** The record's commit re-ranks the roadmap under the
   method's second trigger, moving boundaries on or off the path by §6's
   answers.

## 9. What this exercise is not

- **Not the dogfood.** No command, no session, no agent. The layer design's
  sub-project 4 remains the success criterion; this is its library-level
  precursor, and the commands wrap what this shows works.
- **Not a cut.** It freezes nothing, selects no arm, and its scripts carry
  no N2 table. What it proves is reachability of the belief evaluator's
  answer over one real record, which no fixture proves and no cut has
  claimed.
- **Not a migration.** Nothing under the predecessor's `entities/`,
  `knowledge/` or `results/` is copied. If reproducing the target's analysis
  needs the predecessor's code, the code is re-held as a run input by
  content identity like any other, never imported.
- **Not a vocabulary exercise.** It admits no field to the base profile and
  mints no relation kind; a field the target needs and the profile lacks is
  a finding for the `domain` lane under rule 2.6, not an admission.
- **Not the second corpus.** The ledger's prerequisite — a second corpus
  exercising the claim calculus — stands. This is the first, reproduced.

## 10. Lane discipline

The lane holds `.worktrees/mm30` and touches no kernel surface; its own
files are the scripts of §8 item 3 and the record. The corpus lives on the
certified volume beside the checkout, never under `/tmp`, `/dev/shm` or the
scratch volume, because a corpus written anywhere else fails the durability
allowlist and would prove nothing about the certified path. A finding for a
kernel surface is filed as §7 says and is not edited into the kernel from
this worktree. The lane closes with the record's commit and the re-rank it
carries.

## 11. Alternatives rejected

- **Wait for the surface.** The layer design's order; rejected because the
  first belief needs no command, and the error-finding value of real input is
  highest before the surface is built against fixtures.
- **Run it as conformance cut 19.** A cut needs rows to select and a frozen
  scope; this exercise's scope is "until a belief or an unclassifiable
  refusal", which is not freezable, and cut 19 is the writer session's.
- **Reproduce a whole analysis first** — the meta-analysis across thirty
  datasets that gives mm30 its name. Days of compute behind the first
  refusal; the seams are the same at one dataset.
- **Migrate the predecessor's records and see what breaks.** Ruled out by
  ledger §0; a migrated record is the provenance-weak assertion the kernel
  exists to exclude, and the breakage would measure the migration, not the
  system.
- **Author the claims in the surface's future `claim` command shape.** That
  shape is what this exercise measures; designing it first inverts the
  dependency.

## 12. Verification

The record is the deliverable and is verified the way the typing exercise's
was: every figure in it is reproducible from the scripts and the corpus on
disk; every prediction is stated in this document before the run and
answered in the record; the corpus passes `corpus_check` and the semantic
audit with every finding classified; and both halves of step 10 are run in
a fresh process over the on-disk corpus alone and reported separately. The `test_designs_corpus.py` guards run
unchanged, since no cut, row or ledger state changes until the re-rank.
