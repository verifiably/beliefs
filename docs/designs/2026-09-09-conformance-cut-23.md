# Conformance cut 23 — the world read view and cross-corpus traversal

**Status:** discharged 2026-09-09; frozen before implementation. Results: `../plans/2026-09-09-conformance-cut-23-results.md`.
**Frozen:** 2026-09-09, before implementation, on `design/world-resolution`
**Design:** `../superpowers/specs/2026-09-09-world-resolution-slice-1-design.md`, reviewed 2026-09-09
**Numbered after** cut 22 (roadmap concurrency rule 1) and **serialized after** its discharge, which landed on `main` at `197f517` (rule 5).

## 1. What this cut is

The following baseline describes the tree before implementation. Cut 23 is
now discharged: seven rows close and R23 gains its coverage clause. The dated
results record preserves the measured outcome; §§2–7 remain frozen.

The world's read side exists at the epoch tier and stops there. Slice 2 of the
world index landed `world/read.py`: an address resolves through a published
epoch to `Resolved`, `NotPresent` or `Unknown`, a coreference edge answers
`active`, `inactive` or `indeterminate`, and every answer carries a
`BoundStamp`. Nothing below that tier can use it. `resolution.py` declares
`not-present` unreachable; `corpus.py` says in its docstring that traversal
truncates at the corpus edge; `lineage_snapshot` skips a dataset the corpus does
not hold without a word; `belief.py` banks `unavailable-corpus-absent` as a
reason it never returns. The mm30 reproduction record measured that a single
corpus needs none of this and that the dogfood needs all of it the day a second
corpus enters.

This slice connects the two tiers. It adds one concrete read handle over a
world, captured at an explicit publication, that the kernel's existing walks,
snapshot builders and evaluators accept beside the corpus `ReadView`; and it
makes the three absence distinctions the code has banked producible.

The selection rule is cut 5's: a clause is selected only when its source
mutation and every named check run inside §2. A row with any unrun arm is
partial.

## 2. The boundary

In scope:

- `docs/designs/2026-09-09-conformance-cut-23.md`: the frozen boundary,
  selection, accounting and obligations;
- `python/src/beliefs/errors.py`: `RecordNotPresent`;
- `python/src/beliefs/corpus.py`: `validated_node`, the widened adjacencies,
  `superseded_by`, `_producer_ids`, `lineage_snapshot`, `_producers_of` and
  `run_value`;
- `python/src/beliefs/world/view.py`: `DriftReport`, `WorldReadView` and
  `open_world_view`;
- `python/src/beliefs/world/__init__.py`: the three world-view re-exports;
- `python/src/beliefs/lineage.py`: `Absence`, `Producer.absent`,
  `LineageSnapshot.not_present`, `Certification.absent`, the `"incomplete"`
  divergence state and their projections;
- `python/src/beliefs/resolution.py`: `_BoundVocabulary.state`,
  `_BoundVocabulary.absent`, `build_snapshot(not_present=)` and the reachable
  `NOT_PRESENT` result;
- `python/src/beliefs/consulted.py` and `python/src/beliefs/belief.py`:
  tuple-valued `node_corpus` and the existing `NoBelief.detail`;
- `python/src/beliefs/evaluation.py`: widened `gather` and `evaluate_over`,
  attribution at the read, the facet-set comparison,
  `unavailable-corpus-absent` and `EvaluationInputs.absent`;
- `python/src/beliefs/audit.py`: widened `check_verification`;
- `python/tests/test_world_view.py`, `python/tests/test_lineage.py`,
  `python/tests/test_resolution_snapshot.py`, `python/tests/test_evaluation.py`,
  `python/tests/test_audit.py` and `python/tests/test_corpus_traversal.py`: the
  view and unit arms;
- `python/tests/acceptance/test_world_view_acceptance.py`,
  `python/tests/acceptance/n2_arms_cut23.py` and
  `python/tests/acceptance/test_n2_cut23.py`: the durable arms, declarations and
  guard;
- `python/tools/cut23_acceptance.py`: the aggregate runner;
- `docs/plans/2026-09-XX-conformance-cut-23-results.md`, the adoption ledger,
  roadmap and guide index: discharge records.

Out of scope:

- slice 2: the `coreference-attestation` kind, X12, W15, W8a's coreference
  arms, M3's coreference arm, W4, W1, W2 and W5a;
- slice 3: the import, audit and diagnostic callers; R23's snapshot,
  divergence and explicit-import clauses; X5 and W13;
- slice 4: W7;
- `ReadView` itself.

## 3. Selection

### D3 — closes
`not-present` produced over the world index; the five-way non-collapse with every member reachable; every pair of overlapping availability inputs refused. Selected: unit `D3`. **Deferred:** nothing.

### S1 — closes
The relation chain crossing corpora returns its full closure through the world inbound index; the dangling-target case stays distinguishable. Selected: unit `S1`. **Deferred:** nothing.

### S1a — closes
The lineage chain crossing corpora, walked as a facet, returns its full closure. Selected: unit `S1a`. **Deferred:** nothing.

### S5 — closes
Cross-corpus reach: an absent ancestor or producing run in a covered corpus is `lineage-incomplete` naming the corpus, `not-certified`, and moves the belief input digest through the lineage projection. Selected: unit `S5`. **Deferred:** nothing.

### W6 — closes, read over slice 2's code
Three states, never collapsed; removing a corpus does not convert its ids to `unknown`. Selected: unit `W6`. **Deferred:** nothing.

### W8b — not selected, measured
Probed 2026-09-09 on `197f517` before the freeze: `epoch.build_epoch` **published** an epoch over two records at different addresses sharing one `uid`, and refused one address held in two corpora with a bare `ValueError` from `derive.address_map` rather than the `duplicate-location` finding the row promises. Neither half of the row can be read closed on this tree, and repairing the build is a change to slice 2's code outside this cut's boundary. **Not selected.** The measurement is filed as a task in this lane (`beliefs-fda0e5`, Task 1 step 5) and the row stays part in the roadmap. What this cut does hold is the view's own half: a `uid` held under two corpora refuses at open as corruption (§5 item 4, boundary invariants).

### W10 — closes
Cross-corpus edges are ordinary at the world layer and dangling at the corpus layer. Selected: unit `W10`. **Deferred:** nothing.

### R19 — closes
Cross-corpus recomputation: `check_verification` over the world view reports a well-formed forgery whose runs sit in the other corpus as `verification-derivation-contradicted`, and a malformed record raises. Selected: unit `R19`. **Deferred:** nothing.

### R23 — part, coverage clause
Absence within coverage reads `not-present` and digests differently from absence outside it. Selected: unit `R23`. **Deferred:** the snapshot, cross-corpus-divergence and explicit-import clauses (slice 3) and the rules-store clauses (`contract-cut`).

### Boundary invariants
The view captures, never rereads; every object served is detached; the world lock is released before any capture; only `NotPresent` enters an absence structure; every projection member is identity-encodable.

## 4. Accounting

Eight guarantee rows are read, **7 full/closed** (D3, S1, S1a, S5, W6, W10, R19), 1 partial (R23), and **8 declaration units** carry them: `D3`, `S1`, `S1a`, `S5`, `W6`, `W10`, `R19`, `R23`. W8b is measured and not selected (§3).

## 5. N2 and acceptance obligations

1. The declaration inventory is exactly the eight units `D3`, `S1`, `S1a`,
   `S5`, `W6`, `W10`, `R19` and `R23`, each single-homed to the test that
   exercises it. Lettered sabotage arms normalize back to those units.
2. Every durable arm runs on the certified volume. Capability refusal is an
   error, never a skip or waiver.
3. The aggregate runner names `PREFIX_RUNNERS = ("cut22_acceptance.py",)` and
   `PHASE_MODULES = ("test_world_view_acceptance.py", "test_n2_cut23.py")`.
4. The 25 declared arms cover every sabotage site: in `world/view.py`
   (map-first resolution replaced by a carrier scan; the absent set read as
   unknown; `get` served from the live carrier; drift sources filed in the
   inbound index; targets resolved through the local index; the retained node
   returned), in `corpus.py` (the published-producers union dropped;
   `not_present` filtered by the inspected set), in `lineage.py` (the divergence
   comparison made over an absent producer; `not_present` omitted from the
   projection), in `resolution.py` (one overlap pair unrefused), in
   `evaluation.py` (attribution after the fact through `corpus_of`; the world
   view passed to `read_observed_facets`; the facet comparison made on
   identities), in `world/read.py` (`not status.present` answered `Unknown`),
   in `audit.py` (the verdict disagreement never recorded), and in
   `world/view.py` again (a `uid` held under two corpora admitted at open).
5. `test_n2_cut23.py` audits those arms by the cut-12 pattern, with the
   staleness probe's baseline taken from the tree.
6. Prior declarations remain frozen and no check is reclaimed.
7. This cut document and its declaration inventory are pinned by digest before
   discharge. No implementation discovery rewrites §§2–7; any deviation is
   dated in the results record.

## 6. Second reader

The design's three review passes on 2026-09-09 are its second reading: six
initial findings and five second-review findings were resolved, then the third
pass corrected two acceptance details and found no remaining architectural
issue.

## 7. Limitations

1. Each corpus is captured coherently, but the serial captures are not one
   simultaneous world state.
2. The absent set reaches the belief input digest through the lineage member
   only; a corpus no inspected lineage touches does not move that digest.
