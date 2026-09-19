# The mm30 reproduction — record

**Date:** 2026-09-05
**Status:** run 2026-09-05, complete. The path was walked to the belief
evaluator's answer and both halves of step 10 were measured. The lane's
commits carry the driver (`python/tools/reproduction/`, throwaway by
declaration), its unit tests (`python/tests/test_reproduction_driver.py`,
14 tests), this record, five findings filed as tasks through their owning
lanes, two `open-questions.md` entries, and the roadmap re-rank under the
method's second trigger. The corpus stays beside the main checkout: at
`.mm30-reproduction/` when this record was written, and since 2026-09-12
under `.work/reproduction/` (`f2d5a14`).
Re-run 2026-09-08 as biology slice 2's measurement; see §5 question 1 and §6.
Re-run 2026-09-15 under the estimand-typing design as cut 31's Q10, which
recreates the corpus rather than retyping it: the successor-contract corpus
is `.work/reproduction/mm30` and the prior state is kept at
`.work/reproduction/mm30.cut22`; see §10.
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

## 10. Addendum — estimand typing, 2026-09-15

Appended, not edited: §§1–9 record the 2026-09-05 run and its 2026-09-08
re-run and stay as written. This section records a third run, under the
estimand-typing design (`2026-09-12-estimand-typing-design.md`, §9, decision
10, row Q10), which does not retype the 2026-09-05 corpus but **recreates**
it: a fresh corpus under successor contracts at `.work/reproduction/mm30`,
with the prior corpus state moved aside — never deleted — to
`.work/reproduction/mm30.cut22`, because the transition arm reads it.

World `7aa0edfbdba76a32500d47ba253c43ce`, corpus
`b6472fcf82a1dca72b7ef0461dffa570`, store `fb144c9e05fb9c730566f25002ccb5ff`.

### 10.1 The successor contract and the three held lists

The `mm30` contract gains three corpus-local sorts and one `estimands:`
declaration, and declares
`lineage: {successor: 63566dd034da73bc…}` — the content identity of the
cut-22 document, which is committed beside it as
`python/tools/reproduction/mm30-cut22.yaml` (a byte copy) so that
`check_succession` runs against the real predecessor rather than an authored
stand-in. Q2's "adding a declaration is accepted" arm is therefore exercised
on the corpus that matters: the successor parses, and its identity is
`mm30:0e71608ea5395666a1b3d992c25e264b38250e3c07d20822c633f97e7fe3b71a`.

Each sort binds a held one-line-per-term list, exactly as the biology pack
§6.3 held the concept list. Written sorted, one canonical identifier per
line, newline-terminated, before anything adopts — the contract binds the
addresses, and `adopt` compiles the contract:

| sort | list | terms | content digest | dataset address |
|---|---|---|---|---|
| `concept` | `mm30-concepts.txt` | 285 | `sha256:c7e45f81f02effe2…` | `dataset:sha256:be3bf183a830c31d…` |
| `stage-level` | `mm30-stage-levels.txt` | 2 | `sha256:d77b182f993b076f…` | `dataset:sha256:85b5e3477d98ec01…` |
| `measure` | `mm30-measures.txt` | 1 | `sha256:31993609d906c316…` | `dataset:sha256:08027c2e5fdd6939…` |
| `identification` | `mm30-identifications.txt` | 4 | `sha256:559ea6c06d0beba2…` | `dataset:sha256:79e307100a52bc03…` |

The lists as written: `level:ndmm`, `level:pd`; `measure:rna-seq-tpm`;
`identification:interventional`, `identification:longitudinal`,
`identification:observational`, `identification:structural`. `none` is
deliberately absent: an estimand with no identification does not freeze.

**What the lists cost.** Three files, twelve authored terms, one new driver
step split in two (`lists prepare` before adoption, `lists mint` after) and
one existing step made three-phase. Nothing refused: every referent the
estimand names resolved `member` on the first call, and no term had to be
renamed to become canonical. The 285-member concept list holds
`concept:disease-stage` and holds no `ndmm` or `pd` member, which is why
the levels needed a sort of their own rather than reusing `concept`.

**Whether `observational` is the honest class.** Recorded as an open
judgment, not a certification. The predecessor's evidence lines carry
`identification_strength: longitudinal`, and the held file *is* paired: 51
samples over patients with a first (NDMM) and a latest (PD) sample. The
analysis this spec freezes does **not** pair them — it is a two-group
unpaired rank comparison over the stage token (§2) — so the identification
the *estimand* claims is the one the *estimator* supports, which is
`observational`, not `longitudinal`. Recording `longitudinal` would claim of
this estimand a design its run never used. Both terms are on the list, and a
future paired analysis over the same corpus can select the other.

### 10.2 The typed estimand, as spelled

    claim:      780ace5964c8ab8315607ee9ed084b4acf6bf0f3f20f82bbbd41c11408cddb1c
    operator:   mm30/affects-concept-molecular-entity
    contrast:   {slot: 0, kind: levels,
                 baseline:   {sort: mm30/stage-level,     term: level:ndmm},
                 comparison: {sort: mm30/stage-level,     term: level:pd}}
    measure:    {quantity: {sort: mm30/measure,           term: measure:rna-seq-tpm},
                 scale: additive}
    reference:  0
    control:    {identification: {sort: mm30/identification,
                                  term: identification:observational},
                 conditioning: []}
    applicability: {}

The claim identity is the pack-typed `780ace59…` of the 2026-09-08 re-run,
unchanged by this run (M8: claim identities do not move).

### 10.3 The refused clause, and where it went — a judgment

The 2026-09-05 spec's applicability was prose: *"samples of dataset:gse179929
whose ids carry a stage token and whose value is finite"*. Two clauses, and
neither survives retyping as applicability:

- *"samples of `dataset:gse179929`"* restates the run's one `observes`
  input and is **dropped** under estimand-typing §4.
- *"whose ids carry a stage token and whose value is finite"* is
  **refused**: `mm30/affects-concept-molecular-entity` declares no dimension
  it could be typed along, and §4 gives it no other home.

It was re-authored into `method`, which now reads:

> two-group rank comparison (Mann-Whitney U, normal approximation), standard
> library; a sample whose value is not finite is malformed input and the run
> refuses (assoc.py's own rule)

**This is an authored judgment and is recorded as one.** The judgment is
that the refused clause described *estimator behaviour*, not scope: the
analysis does not exclude a non-finite sample, it refuses the whole run as
malformed input, which is what `assoc.py` has always done and what the
driver's own unit tests pin. Changing `assoc.py` to exclude instead would be
a behavioural change and was **not** made. The new spec **is not certified
equal in scope to the prose spec**, and nothing here claims it is; its scope
is what its typed fields say, and its typed applicability is `{}`. Filed as
a step-4 `corpus-work` finding in `findings.jsonl`.

### 10.4 The prose spec, cited as text

The 2026-09-05 spec's identity is
**`86aaa1a8a8edda8217a1d6f5f6ae28c89fae7362176a214f9fd9fdf95e3f2b1d`**. It is
cited here as text and nothing else. It was not restored, not revised and not
superseded: the new spec carries `supersedes: None`, and no record in the new
corpus names it. It survives only in the prior corpus state, which is why that
state is kept. This is the treatment the biology pack's re-run gave the
replaced claim identity.

The re-authored spec, frozen by `freeze` in the recreated corpus, is
**`10e8bfce1aaad8a937a79bfba7cf523ac42b4240ec8b15e20e5b5f450d234714`**.

### 10.5 What the re-run reached

| step | outcome |
|---|---|
| 1b/1c | four lists held; corpus adopted with all four addresses bound |
| 2 | `build_claim` typed the target on the first call; claim `780ace59…`. The modal-sorted measurement refused as in §3, unchanged |
| 3 | the same 6,154,181 bytes, the same digest `sha256:c74ea661…`, the same dataset address `dataset:sha256:a6bf229e…` |
| 4 | typed `freeze`; spec `10e8bfce…`; `supersedes` absent |
| 5 | confined run `run:b37849ab…`, exit 0, `stats.tsv` and `outcome.txt` = `inconclusive` |
| 6 | `build_assessment` → `AssessmentValue`, outcome `inconclusive`, `assessment:618c6c584da64b62`. **The two spellings of the assessment identity now agree**: stored and derived are both `618c6c584da64b62…`, so §6's identity-bridge finding does not recur |
| 7 | replay `run:73a8e7a2…`; `derive_scope` = `clean-environment`; verdict `passed` |
| 8 | `admit` returned **`Admitted`** (2026-09-05 refused here); `evaluate_over` answered `NoBelief(no-directional-outcome)` |
| 9 | `corpus_check` **0 findings**; `audit_corpus` **0 findings**; `audit_log` as in §3 row 9 — `unresolvable` under the empty observer set (the exercise still anchors nothing), `validated` under the head carrier |
| 10a | the fresh process answered `NoBelief(no-directional-outcome)`, **equal** |
| 10b | `comparison_report_stored` is now **true** (it was false in 2026-09-05; the verification-publication lane landed since); scope, verdict and report identity all recompute equal; `check_verification` checked, no contradiction |

**The consulted set is `{science, mm30, biology}`** — unchanged from the
2026-09-08 re-run, as estimand-typing §5.4 predicted: the estimand's
declaration and its four sorts are all `mm30`'s, and `biology` was already
reached through slot 1's sort.

    science: db7d2ebb252af89567dd7b56cc6bd8d4a563d03ab15d70698bff2f58ff32d557
    mm30:    0e71608ea5395666a1b3d992c25e264b38250e3c07d20822c633f97e7fe3b71a
    biology: 24bcec4370cfcff3077414798c02525814d4aeaaf84430ab378838df7345d53b

The negative still holds: with `biology` unpinned the walk refuses, now with
the assessment's typed estimand supplied to it as well as the claim —
*"namespace 'biology' is consulted but pinned by no corpus"*.

### 10.6 The belief: same value, and where the digest moved

The answer is **`NoBelief(no-directional-outcome)`**, the same value the
2026-09-08 re-run reached (§3 row 10a) and the same value the fresh process
re-derives. The outcome is `inconclusive`, so the evaluator has no direction
to believe in; that is the scientific result, not a machinery failure.

**The digest half of Q10 cannot be quoted at the belief, and this section
says so rather than inventing it.** A `NoBelief` carries no
`belief_input_digest` — only a `Belief` does — so there is no old/new pair
here. The digest movement estimand typing predicts is visible one level
down, over the same data and the same run inputs:

| | prior corpus state | recreated corpus |
|---|---|---|
| spec identity | `86aaa1a8a8edda82…` | `10e8bfce1aaad8a9…` |
| assessment identity (derived) | `316272987716ac4f…` | `618c6c584da64b62…` |
| assessment facet digest | *refused: `PreGrammarAssessment`* (§10.8) | `ddcb5b68dfbf27dc…` |

### 10.7 The fresh-process restoration (Q10's own arm)

Run in a new interpreter holding nothing from the driver's process except the
two rule implementations, which no kernel reader restores from a record. All
four hold:

| key | value |
|---|---|
| `spec_restored` | **true** — `analysis_spec_value(..., profile=…)` returned `10e8bfce…` |
| `assessment_restored` | **true** — `assessment_value(..., profile=…)` returned `618c6c58…` |
| `assessment_equal` | **true** — `build_assessment` over the stored run and the restored spec re-derived `618c6c58…` |
| `belief_equal` | **true** — `evaluate_over` re-derived `NoBelief(no-directional-outcome)` |
| `prior_pre_grammar` | **true** — §10.8's three measurements, below |

`prior_pre_grammar` is the fourth key conformance cut 31 §5 names, and it
travels inside the same `fresh_process_restoration` mapping as the others so
that all of them are read by name from one place. It is **true** exactly when
all three of these hold, and it is derived from them, never asserted:

1. the prior corpus's assessment record refuses with `PreGrammarAssessment`;
2. the prior corpus's analysis-spec record returns **no typed value**;
3. `audit_corpus` over the prior corpus state under the successor profile
   reports exactly one finding, `profile-mismatch` with detail `base`.

This is the "recovered from the corpus alone" reading §5 question 3 asked of
verification, now had for the spec and the assessment too.

### 10.8 The prior corpus state under the successor profile

`.work/reproduction/mm30.cut22` was opened **read-only** under the successor
profile. `audit_corpus` returned **exactly one finding,
`profile-mismatch: base`, and read no record**: that corpus pins
`science:1b029b61dcbf…`, which predates the estimand grammar and does not
parse under the successor, so the existing profile-disagreement rule fires
first and is preserved.

**What the two record readers answered, measured rather than assumed.**
Each stored node was fetched through `iter_stored`, which yields store nodes
unvalidated — the route `audit_corpus` itself takes — and handed directly to
its reader under the successor profile. (`ReadView.get` is the wrong route
here: it validates the base pin and refuses this whole corpus with
`ContractMismatch` before any record is reached, which measures the manifest,
not the record.) The two halves answer differently, and the difference is the
finding:

- **The assessment half fires as Q10 asks.** `assessment_value` over
  `assessment:316272987716ac4f` raises

      PreGrammarAssessment: assessment:316272987716ac4f: pre-grammar
      assessment — minted before science.estimand.v1 with prose members.
      Refused, never coerced (estimand-typing decision 10).

- **The spec half cannot fire at any level**, and not for the reason the
  audit half gives. `analysis_spec_value` over `analysis-spec:86aaa1a8…`
  raises

      MalformedRecord: analysis-spec:86aaa1a8…: an analysis-spec facet is
      exactly {identity, projection}

  The 2026-09-05 spec record **predates the projection form**: its facet
  carries the frozen members directly and has no `projection` key at all, so
  the reader refuses on the facet's shape and `restore`'s `estimand_grammar`
  check — the only place `PreGrammarSpec` is raised — is never reached. That
  record is pre-*projection*, not merely pre-grammar. No typed value comes
  back, which is the transition's real requirement, but `PreGrammarSpec`
  cannot be produced over this corpus by any route.

Filed as a step-10 `design-gap` finding against the estimand-typing design
(Q10's transition arm, §9): the arm's assertion that *both* readers raise
their pre-grammar refusals over this corpus holds for the assessment and is
unreachable for the spec.

The code `assessment-pre-grammar` is reachable over this corpus's assessment
record; `spec-pre-grammar` is not, and neither is reached through
`audit_corpus`, which returns at `profile-mismatch: base` before reading a
record. Both codes are exercised where they can be — on a corpus **pinned to
the successor** holding a raw-written pre-grammar record — by
`python/tests/test_audit.py::test_pre_grammar_records_audit_under_their_own_codes`
and
`python/tests/test_world_audit.py::test_a_pre_grammar_spec_and_assessment_audit_under_their_own_codes_and_the_audit_continues`.
This addendum cites those tests by name rather than claiming the prior corpus
reaches them.

### 10.9 What this addendum does not claim

- **Not scope equality.** §10.3's relocation is an author's judgment. No row
  certifies that the re-authored spec's scope equals the prose spec's, and
  Q10 does not.
- **Not a belief digest comparison.** §10.6: no `NoBelief` carries one.
- **Not a migration.** Nothing was retyped, revised or superseded. The prior
  corpus state is kept as evidence, not as lineage.

## 11. Addendum — composite claims, 2026-09-16

Appended, not edited: §§1–10 record the 2026-09-05 run, its 2026-09-08 re-run
and the 2026-09-15 recreation under estimand typing, and stay as written.
This section records a fourth run, under the composite-claims design
(`2026-09-12-composite-claims-design.md`, §9), which again **recreates** the
corpus rather than migrating it (decision 11): the base contract gained
`composite_grammar` and the `mm30` contract gained an `edges:` table, so the
cut-31 corpus state was moved aside — never deleted — to
`.work/reproduction/mm30.cut31`, and the driver's steps were run in order from
`preflight` through `close`, then the two new steps `compose` (11) and `read`
(12). `.work/reproduction/mm30.cut22` is untouched: `rederive`'s 10c still
reads it.

The run was driven from a lane worktree, so both of the driver's root
variables were supplied rather than defaulted: `SCIENCE_MM30_ROOT` named the
work root — the main checkout's `.work/reproduction/mm30` — because
`paths.CHECKOUT` resolves a `.worktrees/` checkout through its real path under
the work-root volume and would otherwise have looked beside the worktree, and
`MM30_PREDECESSOR` named the predecessor corpus root, whose declared default
does not exist on this host. `preflight` refused once, on the predecessor,
before the second variable was set; that refusal is a path binding on this
host and not a finding about the volume, confinement or the corpus, and the
re-run certified all three.

World `bc234bbfbbad12fb2915801de4a27301`, corpus
`8b5d0c802677ee445e2b9d91ebf5d6a7`, store `05b6c1225e710bb1559f36e8333f3f29`.

### 11.1 The successor contracts

    base (science):  52a4399342235225fbf23526050cf64ff0436d9b72bc54e30fc0c2cb7193b220
    mm30 successor:  4af7c4212d482ae60f429526ff5a8a6d4c335f70351a2687cd2062ffdedf437c
    mm30 predecessor (the cut-31 document): 0e71608ea5395666a1b3d992c25e264b38250e3c07d20822c633f97e7fe3b71a
    biology (shipped, unchanged): 24bcec4370cfcff3077414798c02525814d4aeaaf84430ab378838df7345d53b

The `mm30` document declares `lineage: {successor: 0e71608e…}` — the content
identity of the cut-31 document, committed beside it as
`python/tools/reproduction/mm30-cut31.yaml` (a byte copy), exactly as
`mm30-cut22.yaml` was committed for the previous succession. `version` stays
`1`, as the estimand lane left it. `vocabulary.contract()` now walks the whole
chain, document by document: cut 22 → cut 31 → current, each predecessor
parsed rather than trusted by shape.

What the successor adds is one table, seven rows, over the operators whose
direction is not in doubt:

| edge | cause | effect |
|---|---|---|
| `affects-concept-concept` | 0 | 1 |
| `affects-concept-molecular-entity` | 0 | 1 |
| `affects-molecular-entity-concept` | 0 | 1 |
| `regulates-concept-concept` | 0 | 1 |
| `regulates-concept-molecular-entity` | 0 | 1 |
| `regulates-molecular-entity-concept` | 0 | 1 |
| `induces-state-concept-concept` | 0 | 1 |

`associates-with-*` gets no row (a symmetric statistical relation is not an
arrow), `binds-*` gets none (symmetric), and `is-proxy-for-*` gets none —
§11.5 below. The shipped `biology` pack gains **no** row and was not edited:
`shipped_domain_contract` parses it with no predecessor and `check_succession`
refuses a successor lineage without one, so a shipped pack has no succession
route at this design (limitation 18). Both of the fragment's operators are
`mm30`'s, so the fragment needs none.

**The consulted set is `{science, mm30, biology}`** — unchanged in membership
from §10.5, as the composite-claims design predicted: the composite is read
under the same profile, and no namespace enters through the `edges:` table.
Two of the three identities moved, because two of the three contracts changed
shape; `biology`'s did not.

### 11.2 What the re-run reached

Recreated, so every identity derived from the run is new; every identity
derived from the authored inputs is the one §10 recorded.

| step | outcome |
|---|---|
| 1b/1c | the same four lists, byte for byte: 285 concepts `dataset:sha256:be3bf183…`, 2 levels `dataset:sha256:85b5e347…`, 1 measure `dataset:sha256:08027c2e…`, 4 identifications `dataset:sha256:79e30710…` |
| 2 | claim `780ace5964c8ab83…`, **unchanged** (M8: claim identities do not move). The modal-sorted measurement refused as in §3 |
| 3 | the same 6,154,181 bytes, digest `sha256:c74ea661…`, address `dataset:sha256:a6bf229e…` |
| 4 | spec `10e8bfce1aaad8a9…`, **unchanged** |
| 5 | confined run `run:8b1a2401…`, exit 0, outcome `inconclusive` |
| 6 | `assessment:27bd9753ffa77bf6`; stored and derived identities agree. **Moved** from §10's `618c6c58…`: the assessment derives from the run closure, and this is a new run |
| 7 | replay `run:616f2685…`; `derive_scope` = `clean-environment`; verdict `passed`; verification `verification:353bd069…` |
| 8 | `admit` → **`Admitted`**; `evaluate_over` → `NoBelief(no-directional-outcome)` |
| 9 | `corpus_check` **0 findings**; `audit_corpus` **0 findings** — the audit's composite rules (U7, U9) find nothing to report over a well-formed composite; `audit_log` as before (`unresolvable` under the empty observer set, `validated` under the head carrier) |
| 10a | the fresh process answered `NoBelief(no-directional-outcome)`, **equal** |
| 10b | `comparison_report_stored` true; scope, verdict and report identity recompute equal |
| 10c | all five keys of `fresh_process_restoration` true, `prior_pre_grammar` included |
| 11 | `compose`: the spine minted, the fragment composed — §11.3 |
| 12 | `read` / `read --again`: the two encodings **byte-equal** — §11.4 |

### 11.3 Step 11 — the spine and the fragment

The spine proposition, minted with no evidence and none claimed:

    ref:      proposition:protein-phf19-affects-concept-overall-survival
    claim:    376450b154a29a9be60913f629012614e8ca378d1bcea8b9fece12044cc7950e
    operator: mm30/affects-molecular-entity-concept
    args:     (biology/molecular-entity, protein:PHF19),
              (mm30/concept,            concept:overall-survival)
    layer:    causal
    polarity: negative

The polarity is **negative**, as the inquiry states it — higher PHF19
expression, shorter overall survival. The composite-claims design §9 calls
this proposition "positive" in one clause; that clause is a drafting slip
against its own two neighbours (the fragment's title `PHF19 ⊣ overall
survival` and the spine's display statement), and what was minted and measured
is recorded here rather than adjusted to it. The design is frozen at
conformance cut 32 and is not edited.

The composite, built by `build_composite` over the reproduction's own
snapshot and minted as `composite:h1-prognosis-fragment`:

    identity: ef546cde73edf91b310bd49ff61cd7ace95add2c3d0ffb6e20701fb17b63df32
    shape:    dag
    nodes:    (biology/molecular-entity, protein:PHF19)
              (mm30/concept,             concept:disease-stage)
              (mm30/concept,             concept:overall-survival)
    edges:    concept:disease-stage → protein:PHF19            positive
              protein:PHF19        → concept:overall-survival  negative

The nodes are sorted by `(sort, term)`, which is why PHF19 is `node:0`:
`biology` sorts before `mm30`. The node receipt, measured:

| node | term | outcome |
|---|---|---|
| `node:0` | `protein:PHF19` (`biology/molecular-entity`) | `not-consulted` |
| `node:1` | `concept:disease-stage` (`mm30/concept`) | `member` |
| `node:2` | `concept:overall-survival` (`mm30/concept`) | `member` |

`not-consulted` is the honest answer and not a gap: the reproduction's
snapshot is built over the four held lists this corpus binds and reads no HGNC
release, so the vocabulary that would decide PHF19's membership was never
opened. A check not performed is not a finding (composite-claims design §4.1).
The two concepts resolved `member` against the held 285-term concept list on
the first call, `concept:overall-survival` included — the term the design read
out of `entities/concepts/` on 2026-09-12 is in the recreated corpus's list.

### 11.4 Step 12 — the reading, twice, in fresh processes

`read_composite` was handed the same four arguments the `belief` step handed
the evaluator — the policy binding `science.belief.v1`, the supplied context,
the availability built from the corpus's own held observations, and the
resolution snapshot over the four lists — plus the compiled profile. Standing:
`active`, no successors.

| member | edge | belief | identification |
|---|---|---|---|
| `780ace59…` (`proposition:concept-disease-stage-affects-protein-phf19`) | `disease-stage → PHF19`, positive | `NoBelief("no-directional-outcome")` | `{identification:observational}` |
| `376450b1…` (`proposition:protein-phf19-affects-concept-overall-survival`) | `PHF19 → overall-survival`, negative | `NoBelief("no-eligible-assessment")` | `()` |

Both rows are what the design predicted. The target's row carries the answer
the `belief` step computed over this same corpus (§11.2 row 8), reached
through the traced evaluator rather than re-derived by the reading, and its
identification column is read from the same traced admission — the estimand's
`identification:observational`, §10.1's recorded judgment, now visible as a
column of the composite. The spine's row is `no-eligible-assessment` because
nothing assesses it: the claim was minted with no evidence, and the reading
says so in the row rather than leaving the member out.

The reading was taken in one process, encoded through `identity.v1` to
`reading-1.json`, and taken again in a second process to `reading-2.json`.
The two byte strings are **equal** (`state.reading_equal` true): the reading
is a function of the persisted records and its five arguments, and holds
nothing from the process that wrote them.

### 11.5 The cut-31 corpus state under the successor profile

`.work/reproduction/mm30.cut31` was opened **read-only** under the successor
profile. `audit_corpus` returned **exactly one finding,
`profile-mismatch: base`, and read no record**: that corpus pins
`science:db7d2ebb252af895…`, the estimand lane's base contract, which has no
`composite_grammar` and does not parse under the successor. The
profile-disagreement rule returns before `iter_stored` is reached, so no
record of that corpus was read at all — the same shape §10.8 measured for the
cut-22 state, and decision 11's transition arm, measured rather than assumed.

The route is `rederive.prior_state`'s, pointed at this corpus instead:
`ReadView.opened_at(.work/reproduction/mm30.cut31/corpus)`, then
`audit_corpus(view, evidence=<the two held rule implementations>,
profile=vocabulary.profile())`. Nothing was written to that corpus; the
measurement is saved as `state.cut31_corpus_state` in the recreated one.

### 11.6 The fragment is the inquiry's spine, not its DAG — an author's judgment

Recorded as a judgment, not a certification. The `h1-prognosis` inquiry names
more than these three nodes: gain(1q), EZH2, PRC2 retargeting, a proliferation
score, and the proxies that stand between the measured quantities and the ones
the hypothesis is about. **None of them is minted here.** The corpus holds no
proposition for them and this lane does not author claims it has no evidence
for; the one claim it did author, the spine, is minted precisely so that the
reading can report `no-eligible-assessment` over it and the fragment can carry
a real arrow that nothing supports.

The proxies are the sharper half. `is-proxy-for` gets **no** `edges:` row, so
a proxy relation cannot be a member of a `dag` at this grammar version — it is
not a causal arrow between the nodes, it is a statement about representation,
and typing it as `affects` to get it into the composite would be exactly the
coercion this kernel exists to refuse. This is the **first exercise of spec
limitation 5**, and it is recorded as a limitation reached, not a defect: the
composite says what it can say about this inquiry, and the inquiry's
representation edges wait for a grammar version that types them.

## 12. Addendum — standing reaches the evaluator, 2026-09-17

Re-run under correction-remainder slice 1
(`../superpowers/specs/2026-09-16-correction-remainder-slice-1-design.md`;
cut 33). No contract succeeded, so the corpus was neither recreated nor moved
aside: `.work/reproduction/mm30` is the cut-32 state, read in place, and
`mm30.cut22` / `mm30.cut31` are untouched.

### 12.1 What changed in the driver

Step 8 and step 10a no longer supply a retraction enumeration.
`SuppliedContext` has no such member: `gather` derives it from the corpus under
the manifest's corpus id as coverage. The standing fold resolves every stored
retraction; `EvaluationInputs` and the closure carry only the input-scoped
subset and its counter chain under that full coverage (slice 1 decisions 1,
3, and 10). The producer-snapshot identity stays supplied
(`no-epoch-published`; no epoch is built here) and is the one member of the
context this exercise still declares rather than reads.

### 12.2 What the re-run reached

`reproduction.rederive`, 2026-09-17, in a fresh process:
`rederived_belief` =
`{"detail":"","kind":"NoBelief","reason":"no-directional-outcome"}`,
equal to the recorded step-8 answer (`rederived_equal: true`). The corpus holds
no retraction, so both the full fold and the input-scoped enumeration are
`found=()`, `coverage=(8b5d0c802677ee445e2b9d91ebf5d6a7,)` — byte for byte
the declaration the driver used to supply, now computed. The answer is a
`NoBelief` and carries no `belief_input_digest`, so the slice's projection
change (`retired` and `identity` on every lineage basis) moves no pinned digest
here; it is measured by `test_lineage.py` and the cut's C7 arms, not by this
corpus.

### 12.3 What this addendum does not claim

That a retraction in the mm30 corpus would subtract: none exists, and minting
one is the dogfood's work, not the reproduction's. That the answer would
survive an epoch: none is built. The transition measured is the driver's
supplied member becoming a derived one with the same value.

## 13. Addendum — the snapshot target, 2026-09-19

Re-run under correction-remainder slice 2
(`../superpowers/specs/2026-09-19-correction-remainder-slice-2-design.md`;
cut 34), from the worktree `design/correction-remainder`, at head `24f901c`.
No contract succeeded, so nothing under `.work/reproduction/mm30` was
recreated or moved aside: the corpus is read in place, exactly as at §12.
`MM30_PREDECESSOR` had to be set explicitly to
`/mnt/ssd/Dropbox/proto/projects/cancer/cancer-types/multiple-myeloma` — the
declared default (`~/d/cancer/cancer-types/multiple-myeloma`) resolves one
path segment short of it on this host and `preflight` refused once on the
predecessor before the export, the same shape §11 recorded for
`SCIENCE_MM30_ROOT`.

### 13.1 What changed in the kernel this slice

The slice adds one retraction target arm, `snapshot`, and its live standing:
resolution at the write boundary through the world's retained epochs
(BI-1, BI-2), a fold of a subject's live standing and validated history
(BI-4, BI-7, BI-8), refusal of a retracted producer snapshot at import and
its report by the audits (C8, BI-3, BI-6, BI-8), and the evaluator's mismatch
check consulting that standing (C9). None of this is reached by the mm30
driver: `context()` still supplies `producer_snapshot_identity` as the
literal `"no-epoch-published"` (`python/tools/reproduction/belief.py`,
unchanged this slice — no epoch is built here, so no snapshot is ever bound),
and the scope loop's snapshot key is never populated because there is no
bound snapshot to key on. The one new arm is exercised by the acceptance
module alone — `python/tests/acceptance/test_snapshot_retraction_acceptance.py`,
`n2_arms_cut34.py`, `test_n2_cut34.py`, and `cut34_acceptance.py` — not by
this corpus.

### 13.2 What the re-run reached

`reproduction.rederive`, 2026-09-19, in a fresh process: `rederived_belief` =
`{"detail":"","kind":"NoBelief","reason":"no-directional-outcome"}`, equal to
the recorded step-8 answer (`rederived_equal: true`) — the same payload §12.2
quoted, unchanged by this slice. The corpus holds no retraction of any arm,
so the derived enumeration is still `found=()`,
`coverage=(8b5d0c802677ee445e2b9d91ebf5d6a7,)`. `state.json` was rewritten
with byte-identical content (`assessment_identity_derived`,
`assessment_identity_stored`, `claim_identity`, `composite_identity`,
`corpus_check_findings`, `audit_findings` all equal to the pre-run values);
only `findings.jsonl` gained the run's own log lines. No pinned digest moved:
decision 11 holds, and this re-run is the transition it predicted — a slice
that adds a new retraction arm and its standing without touching any
derivation rule or implementation identity the mm30 corpus's answer depends
on.

### 13.3 What this addendum does not claim

That a snapshot-arm retraction exists in the mm30 corpus, or that one is
minted here: none does and none is. Minting one is the dogfood's work, not
the reproduction's, exactly as §12.3 held for the other arm. That the
snapshot arm's live standing is read anywhere in this run: no epoch is ever
built by this driver, so no producer snapshot is ever bound and
`_snapshot_standing` is never called on this corpus's behalf. The transition
this addendum measures is that the kernel gained an arm and a standing fold
while the reproduction's one supplied member — the literal
`producer_snapshot_identity` — and its answer stayed exactly where §12 left
them.
