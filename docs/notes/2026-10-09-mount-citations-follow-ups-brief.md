# Cut 44 mount-citations follow-ups

## Problem

Cut 44 (mount citations, `beliefs-9ce6e4`) left five follow-ups from its reviews:
`beliefs-d69102`, `beliefs-54e7b8`, `beliefs-4a2998`, `beliefs-cb2a39` and
`beliefs-e02ef3`. They concern two things:

- whether a multi-corpus world read and audit stay correct at the corners;
- whether the costs the lane added stay affordable at mm30 scale.

The second-project milestone reads belief over a world view at an epoch. One of
these corners (`beliefs-d69102`) refuses a legitimate read of that kind.

## Current behaviour and evidence

Read on main at `e319c50`, 2026-10-09. None of the files involved has changed
since cut 44 in a way that touches these findings. No suites were run.

- **`beliefs-d69102`.** `consulted_contracts`
  (`python/src/beliefs/consulted.py`) takes its corpora only from closure nodes
  that `node_corpus` attributes. Over a world view, `gather`
  (`python/src/beliefs/evaluation.py`) attributes only assessments, runs and
  datasets. That is mount-citations decision 10, and the design's §13 notes it
  under J20. A corpus that holds only the proposition therefore contributes no
  pins. A claim namespace only that corpus pins would refuse
  `ContractDisagreement` ("consulted but pinned by no corpus"). This is a
  static reading: no test builds that shape.
- **`beliefs-54e7b8`.** In `audit_world` (`python/src/beliefs/audit.py`), the
  `scope in ("base", "malformed")` exclusion runs `continue` before the
  construction damage report's findings and `corpus-damaged` are appended. A
  corpus that fails construction and also pins a non-shipped base reports
  `profile-mismatch` only.
- **`beliefs-4a2998`.** `CorpusWriter._validate_import_bundle`
  (`python/src/beliefs/corpus.py`) calls `self._refuse(...)` once per bundle
  member. Each call opens its own `_citing()` scope, so every read mount is
  opened and indexed N times per bundle. `_citing` already nests: the
  outermost scope wins.
- **`beliefs-cb2a39`.** `gather`'s observed-facet loop skips an `observes`
  target the view does not hold. Cut 44 re-targeted cut 22's B4b to J21-a's
  mutation, so no N2 arm now mutates this filter. The ordinary suite still
  covers it:
  `test_world_view.py::test_an_absent_input_corpus_is_the_banked_reason`
  evaluates the J20 split with the observed dataset's corpus absent and
  asserts `unavailable-corpus-absent`.
- **`beliefs-e02ef3`.** `audit_world` runs `_record_findings` twice per
  eligible corpus. Every citing write under read mounts opens a fresh
  `ReadView` of each mount (spec §10, limitation 1). Neither cost has been
  measured.

## Constraints

- Frozen cut bodies are never edited. Fixes in `audit.py`, `corpus.py` and
  `evaluation.py` keep pinned sabotage strings byte-exact, and
  `test_arm_staleness` stays at zero stale.
- A change to mount-citations decision 10's attribution, or to the
  reproducibility context, is a contract change and needs its own cut.
- The mount view cache that `beliefs-e02ef3` might call for needs a cheap
  state witness. `beliefs-655c10` asks for the same witness for coordination
  drift, so a decision there serves both.
- `beliefs-918fd2` (overlapping publications) will change `gather`'s
  attribution and its acceptance predicate. That makes it the natural cut to
  take any arm on `gather`.

## Alternatives

For `beliefs-d69102`, the one open decision:

1. **Pass the proposition's corpus to `consulted_contracts` separately (lean).**
   Use the world view's `corpus_of`. `node_corpus` keeps its meaning (where
   the evidence lives), and only the pins needed for the claim are added.
2. **Attribute the proposition in `node_corpus`.** This amends decision 10. It
   changes the attribution every world-read context records, and through it
   the derivation's reproducibility context.
3. **Bank it as a limitation.** Only acceptable if no real world can produce
   the shape. A working corpus that never pins a domain its mounted
   proposition uses can.

The other four are ruled here:

- `beliefs-54e7b8`: report the construction damage before the exclusion. The
  base-pin classification says "no record was read", which is false once
  construction has read records.
- `beliefs-4a2998`: one citation scope per bundle.
- `beliefs-e02ef3`: measure before choosing a remedy.
- `beliefs-cb2a39`: rides along with the next cut that touches `gather`.

## Unanswered questions

- Does the `beliefs-d69102` shape actually refuse? Does option 1 or option 2
  change the identity of any existing world-read derivation? Answered by
  `beliefs-c6e2e4`.
- Is either cost in `beliefs-e02ef3` material at mm30 scale? Answered by that
  task's measurement.

## Proposed decomposition

Goal `beliefs-7e341d` holds all five.

- `beliefs-c6e2e4` (research): reproduce the proposition-only namespace
  refusal and compare options 1 and 2 against the context identity.
  `beliefs-d69102` waits on it.
- `beliefs-54e7b8`, `beliefs-4a2998` and `beliefs-e02ef3` are scoped `todo`
  as direct work.
- `beliefs-cb2a39` is shelved until the next cut that touches `gather` plans
  its arms.
