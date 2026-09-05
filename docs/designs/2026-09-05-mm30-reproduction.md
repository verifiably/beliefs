# The mm30 reproduction — record

**Date:** 2026-09-05
**Status:** in progress. Started 2026-09-05 on the lane
`measure/mm30-reproduction`. The commit carries the driver
(`python/tools/reproduction/`, throwaway by declaration) and its unit tests
(`python/tests/test_reproduction_driver.py`).
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
| 2 | type the target and mint the proposition | pending | |
| 3 | hold the dataset | pending | |
| 4 | freeze the analysis spec and its recipe | pending | |
| 5 | execute the run under confinement | pending | |
| 6 | derive the assessment | pending | |
| 7 | verify: replay, compare, derive scope | pending | |
| 8 | admit and compute belief under `science.belief.v1` | pending | |
| 9 | close the corpus: `corpus_check`, semantic audit, log verification | pending | |
| 10a | re-derive the belief from the corpus in a fresh process | pending | |
| 10b | reconstruct the verification evidence from the corpus | pending | |

## 4. Predictions

Copied verbatim from the design's §5 before any step past preflight ran.
Each is marked `confirmed`, `confirmed for another reason: …`, or `refuted`,
citing `state.json` or `findings.jsonl`.

- **P1 — authoring dominates.** Typing the target and its plan's
  propositions is the largest cost of the exercise, larger than the run. No
  more than ten propositions need typing for one belief. This is the
  measurement behind the layer design's `claim` command and behind the
  ledger's "has to be authored" prerequisite.
  **Outcome:** pending.
- **P2 — the facet is stamped, not checked.** Step 3 succeeds by writing an
  `empirical-observation` facet with whatever payload the author chooses,
  because `is_empirical_observation` reads presence only. Nothing refuses
  a dataset that is not an observation. This is expected to be the first
  finding filed, to the `domain` lane, which owns facet compilation.
  **Outcome:** pending.
- **P3 — the local hold works unchanged.** A holdings observation over a
  local file under the cut-10 local arm needs no amendment.
  **Outcome:** pending.
- **P4 — the run reaches the boundary; the scope is measured, not
  predicted.** The confined launch runs the analysis or refuses at the
  platform probe; it does not fail in between. Which scope `derive_scope`
  reaches is what step 7 measures. A scope short of `clean-environment` is
  recorded, not repaired, and is classified by §2 rule 4 — `same-environment`
  to the host, `not-certified` to authoring or defect.
  **Outcome:** pending.
- **P5 — the belief re-derives; the verification evidence does not.** Step
  10a passes: the stored projection carries assessment, scope and verdict,
  which is all the evaluator reads. Step 10b fails: step 7's
  `AssessmentVerification` is in-memory, only its `admission_record`
  projection is written, and no stored record carries the comparison report
  or lets scope be recomputed (cut 18 §7). 10b is what puts
  `verification-publication` on the path, where the 2026-09-05 re-rank
  provisionally placed it; 10a passing is not evidence against it.
  **Outcome:** pending.
- **P7 — the assessment derives without a finding.** Step 6 returns an
  `AssessmentValue`, not an `AssessmentFinding`, on the first run: the
  interpretation rule is authored for this target and the run's result is
  the shape it expects. A finding here is a defect in the rule's authoring
  or the recipe's result manifest, classified under §7.
  **Outcome:** pending.
- **P6 — at least one banked design is amended.** Not which. The typing
  exercise amended the kernel design and withdrew a ledger claim; a run
  through five more seams is not expected to amend nothing.
  **Outcome:** pending.

## 5. Questions

The design's §6, answered from the run:

1. **How much of the biology pack does the first belief need?** Pending.
2. **Does a single-corpus dogfood need world resolution?** Pending.
3. **Is a stored verification required by the success criterion?** Pending
   (answered from step 10b, never 10a).

And the one carried with no row: **where a typed claim is authored** for a
corpus that has none. Pending.

## 6. Findings

Every refusal and every seam the exercise wanted that did not exist, one
line each, under the design's §7 classes. The driver's own mistakes are not
here; they are in §8.

| step | class | reason | filed |
|---|---|---|---|
| — | — | none yet | — |

## 7. Authoring cost

Pending (Task 5 records the wall time from opening the predecessor record
through the vocabulary edits to the mint).

## 8. Driver corrections

Mistakes fixed in the driver during the run, kept apart from §6 so a reader
can tell instrument from kernel.

- none yet.
