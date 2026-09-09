# The mm30 reproduction — record

**Date:** 2026-09-05
**Status:** run 2026-09-05, complete. The path was walked to the belief
evaluator's answer and both halves of step 10 were measured. The lane's
commits carry the driver (`python/tools/reproduction/`, throwaway by
declaration), its unit tests (`python/tests/test_reproduction_driver.py`,
14 tests), this record, five findings filed as tasks through their owning
lanes, two `open-questions.md` entries, and the roadmap re-rank under the
method's second trigger. The corpus stays at `.mm30-reproduction/` beside
the main checkout.
Re-run 2026-09-08 as biology slice 2's measurement; see §5 question 1 and §6.
**Scope:** one real mm30 proposition pushed through the `beliefs` kernel as a
library, from a registered world to the belief evaluator's answer, under the
design `../superpowers/specs/2026-09-05-mm30-reproduction-design.md` and its
plan `../superpowers/plans/2026-09-05-mm30-reproduction.md`. A measurement: it
produces this record, findings, and a re-rank. It produces no cut, no row, no
new kind, no vocabulary admission, and no code under `python/src/beliefs/`.

## 1. Preflight

Step 0 (`reproduction.preflight`), run 2026-09-05:

    ok: certified volume at <checkout>/.mm30-reproduction; confinement available; predecessor at <predecessor>

The work directory is `.mm30-reproduction/` beside the **main** checkout, not
beside the lane's worktree: a worktree under `.worktrees/` is removed when the
lane closes, and the corpus is the deliverable's second half (design §8 item
2). It is gitignored. The probe world, corpus and store roots were initialized
under it and removed; `host_prerequisites()` returned `None`; the predecessor
root carries a `science.yaml`.

## 2. Target

**`proposition:concept-disease-stage-affects-protein-phf19`** — `concept:disease-stage`
`affects` `protein:PHF19`, `claim_layer: causal_effect`, `polarity: positive`,
`identification_strength: longitudinal` — over **`dataset:gse179929`**, the
Misund 2022 paired RNA-seq TPM matrix (`GSE179929_gene_tpm.txt.gz`, 6,154,181
bytes under the predecessor's `data/supp/orig/misund2022/`). Selected
2026-09-05 by `reproduction.select_target` from 275 candidate
(proposition, dataset) pairs; the four it beat are in `target.yaml`.

**The join.** The plan's join read a proposition's `datasets` and `related`
fields and an evidence line's `related`; in the predecessor none of those
names a dataset, and the join was empty. The predecessor's evidence lines
name the datasets they analyzed in `dataset_usage` (role `analyzed`), and
that field is the join. This is the evidence line's own field, not a
relaxation of the design's §3 criteria; none of *small*, *locally held*,
*empirical* or *structured* was relaxed. Two facts about "locally held":
42 dataset records resolve on disk, but 22 of them resolve to absolute paths
outside the predecessor (`/data/proj/mm30/...`, `/data/raw/...`); the ranking
prefers a dataset under the predecessor's own `data/` (§3's wording), and the
chosen one is.

**What the predecessor computed.** Evidence lines `-ev2` (task t240) and
`-ev3` (task t258) rest on this dataset. t240
(`interpretation:0084-t240-misund-phf19-trajectory`) computed the per-patient
`log2((latest_tpm + 1) / (first_tpm + 1))` of PHF19 between the first (NDMM)
and latest (PD) paired sample, then a Spearman correlation of that change
against the proliferative-index change from Misund's Supplementary Table S10
(a second file, `.xlsx`). t258 correlated the same PHF19 change with ssGSEA
pathway trajectories from Table S9. Lines `-ev0` (t166, four other GEO
series) and `-ev1` (t055, MMRF) do not use this dataset.

**What this reproduces.** The within-dataset association the proposition
states — PHF19 expression against disease stage — over the one held file:
the PHF19 row (`ENSG00000119403`; the file is keyed by unversioned Ensembl
ids, and the predecessor's annotables crosswalk maps it to PHF19) compared
between the two stage levels the sample ids carry as their last
`_`-separated token, `NDMM` (17 samples) and `PD` (34 samples), by a
two-group rank comparison. `positive_level: PD`: the proposition's positive
polarity predicts the higher PHF19 in progressive disease. The predecessor's
own statistic (paired log2FC correlated with a Table S10 covariate) needs a
second file and `.xlsx` parsing, so it is not what runs; the two-group stage
association over the same file is the standard-library, one-file expression
of the proposition, and the record says so rather than taking the next
alternative (both alternatives over this dataset are abstract concepts —
`ratchet-strength`, `fitness-selection` — with no column in the file).

**The vocabulary.** The proposition is typed under the exercise's own copy
of the typing exercise's *unsorted* vocabulary
(`python/tools/reproduction/mm30-reproduction.yaml`, one sort `term`), not
the modal-sorted one the plan named: the target's kind pair is
concept→protein, and `mm30-modal-sorted.yaml` assigns `affects` the slots
`[concept, concept]` by its stated modal rule, refusing the 10
concept→protein `affects` records by construction. Both vocabularies
predate the selection, so choosing between them is not fitting one to the
target; the modal-sorted refusal is measured at step 2 as a pure
`build_claim` call (no mint) and recorded. Every binding is the placeholder
`mm30-entities` at release `2026-08-07`; the resolution snapshot declares
nothing readable, so question 1 is answered unmeasured (§5).

**The file's shape.** The matrix is wide: 58,050 gene rows × 51 sample
columns, gzipped. The plan assumed a long table with a `value_column` and a
`group_column`; the analysis (Task 7) reads the wide shape instead, taking
`value_row` and deriving the group from the sample id, and opens the gzip
directly rather than through a decompression rule. `target.yaml` carries
`held_file`, `value_row`, `group_separator` and `positive_level`.

## 3. The path

| # | step | outcome | left on disk |
|---|---|---|---|
| 1 | register a world root and adopt one fresh corpus | ran 2026-09-05: world `9ea5394560c2a36acdd4e502e02141c7`, corpus `6d25948b9d8bf0120b096ab470241742` admitted `Fresh`, status `known, live, present`, no findings; store `6750e2f29ff9f74fb8724fc6caad5ff1` | `world/` (registry, `world.yaml`), `corpus/corpus.yaml` (manifest pinning the science contract and the `mm30-reproduction` domain), `store/`, and the three `.metadata` roots |
| 2 | type the target and mint the proposition | ran 2026-09-05: `build_claim` typed the target under the unsorted vocabulary on the first call; claim identity `5e702bc43fdf51d3…`; minted `proposition:concept-disease-stage-affects-protein-phf19` under the full `Authority`. The pure measurement under the modal-sorted vocabulary refused: `ArgumentSortMismatch: slot 1 of 'mm30/affects' is declared 'mm30/concept'; 'protein:PHF19' is of sort 'mm30/protein'` (§6) | `corpus/proposition/…` — one `proposition` record carrying the claim projection and a display statement |
| 3 | hold the dataset | ran 2026-09-05: the holdings boundary's local arm wrote 6,154,181 bytes to the store under `gse179929/GSE179929_gene_tpm.txt.gz`, digest `sha256:c74ea661…`, and published the observation; the dataset record was minted under its content address `dataset:sha256:a6bf229e…` with an authored `empirical-observation` facet; `admission_state` over the stored declaration and the observation read `Held` | `store/gse179929/…`, `corpus/holdings-observation/8ef93a89…` (outcome `Found`), `corpus/dataset/sha256__a6bf229e…` |
| 4 | freeze the analysis spec and its recipe | ran 2026-09-05: the Snakefile was rendered with the held basename, the PHF19 row, the `_` separator and `PD`; `freeze` bound the interpretation rule `mm30-reproduction/outcome-file/v1` and the equivalence rule `content-identity-equality/v1` to their held implementations; spec identity `86aaa1a8a8edda82…`, target the proposition's corpus ref; the hand-built `analysis-spec` record was accepted by the writer once stamped | `corpus/analysis-spec/86aaa1a8…`; the rendered `analysis/workflow/Snakefile` in the driver (committed, since its digest enters the definition snapshot). **From here the target, spec and rule are fixed** |
| 5 | execute the run under confinement | ran 2026-09-05 (2 min 36 s for steps 5–7 together, including the venv snapshot's materialization): the confined planning launch and the execution launch both exited 0; the analysis wrote `stats.tsv` (`z = 1.159`, `p = 0.246`, `n = 51`) and `outcome.txt` = `inconclusive`; run minted as `run:9700c41d…` with the receipt's capabilities `closure-confined-filesystem`, `from-bundle`, `network-denied` and an instance attestation | `corpus/run/9700c41d…` (the closure projection with both launch attestations inside it), the port's registration chain under `corpus/.#~chain/`, the environment snapshot and both run scratches under `scratch/` |
| 6 | derive the assessment | ran 2026-09-05: `build_assessment` returned an `AssessmentValue` with outcome `inconclusive` on the first call (P7); minted `assessment:316272987716ac4f`. The derived identity `31627298…` and the stored record's identity `d9e338a7…` differ (§6) | `corpus/assessment/316272987716ac4f.md` |
| 7 | verify: replay, compare, derive scope | ran 2026-09-05: the replay minted `run:edf73817…`; the two result manifests agree (same `stats.tsv` and `outcome.txt` digests); `derive_scope` = **`clean-environment`** on this host, so no scope finding; `build_verification` derived an `AssessmentVerification` with verdict `passed` | `corpus/run/edf73817…`; the verification is in memory until step 8 |
| 8 | admit and compute belief under `science.belief.v1` | ran 2026-09-05: `build_verification` re-derived from the two stored closures agreed with step 7 (`clean-environment`, `passed`); `admission_record` named the **derived** assessment identity `31627298…`, kept unaltered; minted `verification:…`. `gather` matched one assessment and its run. `admit` refused: `not-admitted-verification-state: kernel 3.3 admits only clean-environment passes` — the gathered assessment carries the stored identity `d9e338a7…`, so no verification names it. `evaluate_over` answered `{"kind": "NoBelief", "reason": "no-eligible-assessment", "detail": ""}`. Terminal under §2 rule 4: the admission reason and the scope (`clean-environment`, `passed`) were read together, and the class is **design-gap** (the identity bridge, §6), not host. Supplied members: `producer_snapshot_identity` = `no-epoch-published` (no epoch was built), the retraction enumeration is empty with coverage this corpus; the holdings reduction rule was not applied (one observation, no history) | `corpus/verification/…` naming the derived identity, the corpus ref of the assessment, scope, verdict and the two-run derivation |
| 9 | close the corpus: `corpus_check`, semantic audit, log verification | ran 2026-09-05: `corpus_check` **0 findings**; `audit_corpus` over the in-process spec and rule implementations **0 findings** (the stored verification's derivation recomputed and agreed, since it names the derived identity); `audit_log` measured under two observer shapes, both read-only: with the **empty observer set** (the exercise anchored nothing) the outcome is `unresolvable`, 22 chain entries unanchored, 3 intents qualified, one `unanchored` finding — the exercise's own omission, not the kernel's; with **one registry carrier built from the chain head as read now** (the record an anchor act would leave) the outcome is `validated`, anchored through `f64d23b2…`, 0 unanchored, 0 findings. Zero kernel findings is the expected outcome and is stated as such | nothing written; `state.log_verdict` carries both reports |
| 10a | re-derive the belief from the corpus in a fresh process | ran 2026-09-05 in a new interpreter: `evaluate_over` over the corpus on disk answered `NoBelief(no-eligible-assessment)`, **equal** to step 8's payload (`state.rederived_equal` = true). Inputs, labelled: *corpus* — the assessment, both runs, the dataset, the verification, the claim and the holdings observation; *supplied* — `producer_snapshot_identity` (`no-epoch-published`) and the empty retraction enumeration; *in-process* — the compiled profile, the empty resolution snapshot and the policy binding. **Measured 2026-09-08:** the fresh-process answer was `NoBelief(no-directional-outcome)`, again equal to step 8. Neither `NoBelief` carries a `belief_input_digest`, and the 2026-09-05 artifacts record no input digest, so there are no honest old/new digests to quote. The closure projection now includes `observed_facets` (biology pack design §5.4), while this re-run also changed the typed claim/operator and consulted contracts; this run did not isolate any one change as the cause of a reconstructed closure-digest difference. | nothing written |
| 10b | reconstruct the verification evidence from the corpus | ran 2026-09-05: `comparison_report_stored` **false** — no stored record carries step 7's comparison report; the verification names its two-run derivation, both closures decode from their stored projections, `derive_scope` recomputes `clean-environment` (equal) and `build_verification` recomputes `passed` (equal); the `analysis-spec` record is present and its identity matches the in-process spec; `check_verification` reports checked, no contradiction. Inputs, labelled: *corpus* — the verification record, the two run publications, the spec record's identity; *in-process* — the `FrozenSpec` and both rule implementations, because no kernel reader restores either from a record. Recovered by recomputation, not read | nothing written; `state.evidence_reconstruction` |

## 4. Predictions

Copied verbatim from the design's §5 before any step past preflight ran.
Each is marked `confirmed`, `confirmed for another reason: …`, or `refuted`,
citing `state.json` or `findings.jsonl`.

- **P1 — authoring dominates.** Typing the target and its plan's
  propositions is the largest cost of the exercise, larger than the run. No
  more than ten propositions need typing for one belief. This is the
  measurement behind the layer design's `claim` command and behind the
  ledger's "has to be authored" prerequisite.
  **Outcome:** confirmed, narrowly, and for a weaker reason than predicted.
  Authoring (§7: about 4.5 minutes from opening the predecessor's records to
  the mint) exceeded the run (steps 5–7 together, 2 min 36 s), but only
  because the claim vocabulary already existed: choosing between the two
  the typing exercise authored took seconds, and `build_claim` plus the mint
  took 0.1 s (`state.typing_seconds`). One proposition was typed, not ten:
  this target's analysis plan names no other proposition, so the "no more
  than ten" bound holds trivially. Had the vocabulary not existed, the
  typing exercise's cost (a day, 2026-08-07) would have dominated
  everything else here by two orders of magnitude.
- **P2 — the facet is stamped, not checked.** Step 3 succeeds by writing an
  `empirical-observation` facet with whatever payload the author chooses,
  because `is_empirical_observation` reads presence only. Nothing refuses
  a dataset that is not an observation. This is expected to be the first
  finding filed, to the `domain` lane, which owns facet compilation.
  **Outcome:** confirmed. The facet `{"boundary": "acquisition", "source":
  "dataset:gse179929", "asserted_by": "mm30-reproduction"}` was authored by
  the driver and accepted unread; `is_empirical_observation` reads presence
  only (`stored.py`). It was the second finding filed (`findings.jsonl`, step
  3), not the first: step 2's modal-sorted measurement preceded it.
- **P3 — the local hold works unchanged.** A holdings observation over a
  local file under the cut-10 local arm needs no amendment.
  **Outcome:** confirmed. `holdings.boundary.write` under `holdings_seam()`
  with the expected digest published a `Found` observation on the first
  call; `state.holdings_observation_ref` resolves in the read view.
- **P4 — the run reaches the boundary; the scope is measured, not
  predicted.** The confined launch runs the analysis or refuses at the
  platform probe; it does not fail in between. Which scope `derive_scope`
  reaches is what step 7 measures. A scope short of `clean-environment` is
  recorded, not repaired, and is classified by §2 rule 4 — `same-environment`
  to the host, `not-certified` to authoring or defect.
  **Outcome:** confirmed. The launch ran the analysis; nothing failed
  between the platform probe and the result. The measured scope is
  `clean-environment` (`state.verification_scope`), the best row, so rule 4's
  classification was not needed.
- **P5 — the belief re-derives; the verification evidence does not.** Step
  10a passes: the stored projection carries assessment, scope and verdict,
  which is all the evaluator reads. Step 10b fails: step 7's
  `AssessmentVerification` is in-memory, only its `admission_record`
  projection is written, and no stored record carries the comparison report
  or lets scope be recomputed (cut 18 §7). 10b is what puts
  `verification-publication` on the path, where the 2026-09-05 re-rank
  provisionally placed it; 10a passing is not evidence against it.
  **Outcome:** confirmed for another reason in part. 10a passed as
  predicted, and for the predicted reason. 10b: no stored record carries the
  comparison report, as predicted — but scope **can** be recomputed from the
  corpus, because the stored verification names its two-run derivation
  (cut 18's `derivation` member) and both closures decode; what the
  recomputation needs beyond the corpus is the in-process `FrozenSpec` and
  the rule implementations, since no reader restores them from the
  `analysis-spec` record. The prediction's "or lets scope be recomputed" is
  refuted; the rest stands (`state.evidence_reconstruction`).
- **P7 — the assessment derives without a finding.** Step 6 returns an
  `AssessmentValue`, not an `AssessmentFinding`, on the first run: the
  interpretation rule is authored for this target and the run's result is
  the shape it expects. A finding here is a defect in the rule's authoring
  or the recipe's result manifest, classified under §7.
  **Outcome:** confirmed. `build_assessment` returned an `AssessmentValue`
  (`state.assessment_outcome` = `inconclusive`) on the first run.
- **P6 — at least one banked design is amended.** Not which. The typing
  exercise amended the kernel design and withdrew a ledger claim; a run
  through five more seams is not expected to amend nothing.
  **Outcome:** confirmed as obligations, not yet as text. Five design-gap
  findings (§6) are filed as amendment obligations through their owning
  lanes; no banked design's text changes in this lane's commits, because
  roadmap concurrency rule 6 forbids editing a kernel surface's design from
  the reproduction worktree. The amendments themselves are the owning
  lanes' next commits.

## 5. Questions

The design's §6, answered from the run:

1. **How much of the biology pack does the first belief need?**
   **Unmeasured.** The proposition was typed under the unsorted vocabulary
   (§2), whose one sort binds the placeholder `mm30-entities` namespace at
   release `2026-08-07`; the resolution snapshot declared nothing readable,
   every binding was `not-consulted`, and `not-consulted` sufficed to mint
   and to gather (D3 refuses only `not-member`). No GO, HP, EFO or MONDO
   binding was exercised. What is measured is the **floor** the pack must at
   least reproduce: one operator, `affects`, with a concept→protein argument
   pair; two referents, `concept:disease-stage` and `protein:PHF19`; the
   `causal` layer and `positive` polarity. And one constraint on the pack's
   sort discipline: the modal-sorted vocabulary refuses this pair
   (`ArgumentSortMismatch`, §3 row 2), and it refuses the ten concept→protein
   `affects` records of mm30 by the same rule, so a pack whose `affects`
   is `[concept, concept]` cannot type this target.

   **Measured 2026-09-08 (biology pack design §6.4).** The target typed under
   `mm30/affects-concept-molecular-entity`: slot 0, `concept:disease-stage`,
   resolved `member` against the held list of 285 concept identifiers; slot 1,
   `protein:PHF19`, resolved `not-consulted`. The new claim identity is
   `780ace5964c8ab8315607ee9ed084b4acf6bf0f3f20f82bbbd41c11408cddb1c`,
   replacing `5e702bc43fdf51d3ef957b773b1f4cd5935ec958b39a8203738181cd23b702a7`
   because the claim now names the pack's sorted
   operator instead of `mm30-reproduction/affects`. Across all 334 proposition
   records, 307 typed and 27 had the sole refusal class `no-claim-recorded`.
2. **Does a single-corpus dogfood need world resolution?** **No.** No step
   of the path resolved an address across corpora or returned a resolution
   state the registry alone could not give: step 1 used the registry
   (admit, status); steps 2–9 used the one corpus's writer and read view;
   step 10a's `evaluate_over` gathered through the corpus-local instrumented
   resolver with the corpus id as the whole retraction coverage. `next` over
   one corpus can be built without world resolution; the dogfood proper
   needs it only when a second corpus enters. `world-resolution` stays last
   on the path.
3. **Is a stored verification required by the success criterion?** **Yes.**
   Step 10b (never 10a): `comparison_report_stored` is false. The stored
   verification names its two-run derivation and both closures decode, so
   scope and verdict *recompute* and agree — but only with the in-process
   `FrozenSpec` and rule implementations, which no reader restores from a
   record. Nothing is *recovered* from the corpus alone. `verification-
   publication` stays on the path; its slice design is drawn next in the
   `write-path` lane. 10a passing (the belief re-derives equal) is not
   evidence against it, as the design said.

And the one carried with no row: **where a typed claim is authored** for a
corpus that has none.
- *What it cost:* §7 — reading the predecessor's records dominated; the
  typing itself was one `build_claim` call.
- *What `build_claim` refused and why:* nothing, under the chosen vocabulary.
  Under the modal-sorted one, `ArgumentSortMismatch`: "slot 1 of
  `mm30/affects` is declared `mm30/concept`; `protein:PHF19` is of sort
  `mm30/protein` … a term with no slot to occupy" — the sort discipline,
  not the operator, the layer or the polarity.
- *What a `claim` command must do:* take a predicate, a subject and an
  object with kind prefixes, a layer and a polarity; resolve the local
  names through one **named** domain contract's `term`, exactly as
  `type_corpus_claims.py` and `vocabulary.plan()` do; build the claim; mint
  the proposition under the session's writer with the claim projection and
  a display statement kept out of the identity.
- *What it must refuse:* a kind prefix that maps to no sort; a sort the
  operator's slot does not admit; an unknown layer or polarity; and —
  this record's own lesson — choosing a vocabulary silently: the contract
  the claim is typed under must be named by the caller or the corpus
  manifest, never picked to make the claim type.

## 6. Findings

Every refusal and every seam the exercise wanted that did not exist, one
line each, under the design's §7 classes. The driver's own mistakes are not
here; they are in §8.

| step | class | reason | filed |
|---|---|---|---|
| 10b | design-gap | no stored record carries the verification's comparison report; scope and verdict recover only by recomputation over both stored closures with the in-process spec and rule implementations (P5) | write-path lane: `beliefs-f860f1` under `beliefs-754995` (verification publication) |
| 9 | corpus-work | `audit_log` under the empty observer set: `unanchored: corpus:6d25948b…` — the exercise performed no anchor act (`anchor_heads`), so nothing anchors its chain; measured as `validated` under a head carrier instead | this record; no lane |
| 8 | design-gap | a `clean-environment` pass was refused at admission (`not-admitted-verification-state`): the verification names the derived identity `31627298…`, the gathered assessment carries the stored identity `d9e338a7…`, and only the former satisfies the audit's recomputation. The belief answer is `NoBelief(no-eligible-assessment)` for this reason and no other | write-path lane: `beliefs-ae9b18`, the same task as step 6's |
| 6 | design-gap | the derived `AssessmentValue` spells `run` as the bare closure address and the stored record as `run:<address>` (which `eligibility_refusal` requires so the run resolves); `assessment.identity()` = `31627298…` and `stored.assessment_value(node).identity()` = `d9e338a7…`. No single identity satisfies both admission over the corpus (which matches the stored one) and the audit's recomputation (which digests the bare address). Unpredicted by §5 | write-path lane: `beliefs-ae9b18` under `beliefs-754995` (one spelling for the run member), with the failing test named |
| 4 | design-gap | `build_assessment` hands the interpretation rule a `ResultManifest` of output digests, not output bytes; the verdict is routed through a canonical outcome file (`outputs/outcome.txt`, exactly one of three lines) whose digest the rule maps. Unpredicted by the design's §5 | `open-questions.md`, computation section (where an interpretation rule reads content); no lane owns it yet |
| 4 | design-gap | `analysis-spec` is a stored kind (`stored.py`'s kinds table, semantic domain `science.analysis-spec.v1`, the r20 check on import) with no kernel builder and no reader; the record was hand-built and stamped through `stamp_semantic_identity`, and nothing restores a `FrozenSpec` from it (step 10b) | `beliefs-91aac6` (a stored `analysis-spec` builder and reader), lands through the next lane that rewrites `stored.py` |
| 3 | design-gap | the `empirical-observation` facet is presence-only: `is_empirical_observation` read the driver's authored payload unchecked (P2) | domain lane: `beliefs-d245a9` (facet payload contract, kernel §11) |
| 2 | corpus-work | under `mm30-modal-sorted`, `build_claim` on the target: `ArgumentSortMismatch` — slot 1 of `mm30/affects` is declared `mm30/concept`; `protein:PHF19` is of sort `mm30/protein` (a term with no slot to occupy, not a rejected value). The exercise's own corpus work: it types under the unsorted vocabulary (§2) | this record, §2 and §5 (the fourth question) |
| 1 | closed | held 285 concept identifiers as `sha256:c7e45f81f02effe2cdded3261257fb1a45af1ca87c988e45b0d1706abd7e981e`; dataset `dataset:sha256:be3bf183a830c31d4f8acf46a309e01bd0476580d2d6db4079af3e3c7bd738d8`; the line format is the tool's (biology pack design §6.3) | unfiled |
| 2 | corpus-work | under `mm30-modal-sorted`, `build_claim` on the target: `ArgumentSortMismatch` — slot 1 of `mm30/affects` is declared `mm30/concept`; `protein:PHF19` is of sort `mm30/protein`. Inside the model these are different types, so this is not a rejected value but a term with no slot to occupy. | record §2 / §5 (the fourth question); the exercise types under the unsorted vocabulary |
| 2 | closed | slot 0 `concept:disease-stage` resolved `member` against the held concept list; slot 1 is `biology/molecular-entity`, `not-consulted` (biology pack design §6.4) | unfiled |
| 3 | closed | `biology/gene-axis {axis: rows, namespace: HGNC}` validated at write by cut 20's seam | unfiled |
| 4 | design-gap | `build_assessment` hands the interpretation rule a `ResultManifest` of digests, not output bytes; the verdict is routed through a canonical outcome file whose digest the rule maps | computation design (where an interpretation rule reads content) |
| 8 | closed | biology unpinned: namespace `biology` is consulted but pinned by no corpus in `['2ea32f637fcdea58a6d96c505bc50a44']`; unresolvable, not merely disputed | unfiled |
| 8 | closed | consulted contracts `biology:24bcec4370cfcff3077414798c02525814d4aeaaf84430ab378838df7345d53b`, `mm30:63566dd034da73bcd6c346a5d9ad61fe46dc67cc58b77f82bad367dea61211eb`, and `science:cf7b0779a5ebee19e6f521b910b8bdf7720ebbc96b8624ec55152839280a8f25`; observed facet `dataset:sha256:a6bf229ef0abd8e11f0b7f017cbdb6977395e23d83fb122fcf141f723ba1e448`, `biology/gene-axis`, digest `94638a01c6b6251d8ba59d20e35e5875bd47c3a04ad0c2c927ddea43a77b8d0b` | unfiled |
| 9 | corpus-work | `audit_log[no-observer]`: `unanchored: corpus:2ea32f637fcdea58a6d96c505bc50a44` | the exercise performed no anchor act; measured under the head carrier instead |

## 7. Authoring cost

Preliminary; completed at the end. Wall clock, local, 2026-09-05: the
predecessor's proposition and evidence-line records were first opened at
15:38 (the selection driver's first successful run); the vocabulary was
chosen (not edited — both candidates predate the exercise, authored
2026-08-07 by the typing exercise) at 15:41; the proposition was minted at
15:42:38. **About four and a half minutes of authoring for one proposition**,
of which `build_claim` and the mint took under a second (`typing_seconds` in
`state.json`). Reading what the predecessor computed (two interpretation
records, one workflow rule, the file's header) took most of it. One
proposition was typed, not ten: the analysis plan for this target names no
other proposition. Against it, steps 5–7 (the confined run, the assessment,
the replay and the verification) took 2 min 36 s of wall time, most of it
materializing the environment snapshot once; the whole path from preflight
to step 10b took about 25 minutes including the driver's own writing.
Authoring beat the run, but only because the vocabulary was already
authored (P1).

## 8. Driver corrections

Mistakes fixed in the driver during the run, kept apart from §6 so a reader
can tell instrument from kernel.

- **Step 9, log audit classification.** The first run of `reproduction.close`
  filed the empty-observer-set `unanchored` line as a design-gap. It is the
  exercise's own omission (no anchor act was performed), so the driver was
  corrected to file it as corpus-work, the mis-filed line was removed from
  `findings.jsonl`, and the step was re-run. `close` writes nothing, so the
  re-run changed no record.
- **Step 3 onward, the analysis's input shape.** The plan's analysis read a
  long table (`value_column`, `group_column`); the held file is a wide gzipped
  matrix (§2). The analysis, the template's placeholders and `target.yaml`'s
  keys were written to the wide shape before the spec was frozen, so no run
  or recipe was affected.
- **The work directory.** The plan put it beside the worktree; a worktree
  under `.worktrees/` is removed when the lane closes, so `paths.py` resolves
  it beside the main checkout when the driver runs from a linked worktree.

## 9. What this run does not claim

- **No cut, no row.** Nothing was frozen or selected; no guarantee row's
  status changes on this record. The measurements are reachability facts
  about one path over one record.
- **One proposition, one dataset, one host.** `concept:disease-stage affects
  protein:PHF19` over GSE179929 on the host `titan`, whose bubblewrap
  reached `clean-environment`. Another host, another target or a paired
  analysis may reach a different row of `derive_scope` or a different
  outcome; the `inconclusive` here is a two-group unpaired comparison at
  alpha 0.05, not the predecessor's paired trajectory statistic (§2).
- **The belief is `NoBelief`, for a kernel reason.** The evaluator answered
  `no-eligible-assessment` because of the assessment identity's two
  spellings (§6, steps 6 and 8), not because of the data. Had admission
  succeeded, the frozen rule's `inconclusive` would have given
  `NoBelief(no-directional-outcome)`, the scientific result; this run never
  reached that branch, and does not claim it.
- **Supplied, not derived.** The producer snapshot identity
  (`no-epoch-published`) and the retraction enumeration (empty, coverage
  this corpus) were supplied to `SuppliedContext`; no epoch was built and
  no retraction search ran.
- **The holdings reduction rule was bypassed.** Step 8 read every `Found`
  holdings observation directly; supersession and coverage were not
  applied, since there is one observation and no history.
- **In-process spec and rules.** Steps 8, 9, 10a and 10b used the
  `FrozenSpec`, the interpretation rule and the equivalence rule from the
  driver's process, because no kernel reader restores them from a record
  (§6, step 4). The stored `analysis-spec` record's identity was checked to
  agree; that is the whole of what the corpus contributed there.
- **Question 1 is unmeasured** (§5): no ontology binding was consulted.
- **No act-report for the fulfilled runs.** A successful confined run's
  publication plan writes the run record only; the registration chain holds
  the settled intents. Whether a fulfilled operation should also leave an
  act-report record is the act-report design's reading, not this record's.
- **No anchor act.** The corpus's own log is unanchored; `validated` was
  measured under a carrier built from the head as read (§3 row 9).
- **The driver is not a surface.** Its scripts are the instrument, written
  to the bridges this kernel has today; sub-project 4's commands are
  written from what they show, not by promoting them.
