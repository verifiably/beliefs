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

Pending (Task 2).

## 3. The path

| # | step | outcome | left on disk |
|---|---|---|---|
| 1 | register a world root and adopt one fresh corpus | pending | |
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
