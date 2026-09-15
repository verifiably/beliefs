# Conformance cut 29 — dataset addresses derived from the content identity

**Status:** frozen 2026-09-14; not yet discharged.
**Frozen:** 2026-09-14, before implementation, on `design/world-resolution-slice-5`
**Design:** `../superpowers/specs/2026-09-14-world-resolution-slice-5-design.md`, approved 2026-09-14 after one review (§12 there)
**Numbered after** cut 28 (roadmap concurrency rule 1) and **serialized after** its discharge, which is in the branch ancestry (rule 5).

## 1. What this cut is

The baseline below describes `main` at `fb1dac1` before implementation.

A dataset's address is ruled (admission ramp §6.2) and computed
(`dataset.dataset_address`), and seven kernel modules read it from a stored
declaration — the belief-input closure, the observed-facet ledger, produced
dataset minting, run-input admission. What has never existed is the check:
`stored.dataset_node(slug, ...)` mints `dataset:<slug>` from an authored
handle, and the write boundary refuses a dataset with *no* content identity
(W3, cut 4) while never comparing the id it has with the address its
declaration derives. Slice 2b closed the same gap for `source` at cut 25 and
filed this half.

This cut removes the slug from the dataset builder, adds
`stored.dataset_address_of`, holds every admitted dataset to its derived
address at the write boundary (`DatasetAddressDisagreement`) and at both
inputs of `consolidate`, and migrates the test corpus to derived addresses.
The address form is unchanged: `dataset:sha256:<fold>` as ruled. No seam,
history or redirect set is built: a re-held dataset is a new entity (world
design §4.4).

The selection rule is cut 5's: a clause is selected only when its source mutation and every named check run inside §2. A row with any unrun arm is partial.

## 2. The boundary

In scope:

- `docs/designs/2026-09-14-conformance-cut-29.md`: the frozen boundary, selection, accounting and obligations;
- `python/src/beliefs/errors.py`: `DatasetAddressDisagreement`;
- `python/src/beliefs/stored.py`: `dataset_node` without its slug, `dataset_address_of`;
- `python/src/beliefs/corpus.py`: `_refuse_dataset_basis`'s second clause;
- `python/src/beliefs/relocation.py`: `consolidate`'s dataset input validation;
- `python/tools/reproduction/hold.py` and `concepts.py`: the slug argument removed;
- `python/tests/dataset_fixtures.py` and the test corpus's `dataset_node` sites, closure fixtures and `dataset:` literals: the §8.2 migration of the design;
- `python/tests/acceptance/test_n2_cut7.py`: the dated live adapter for the X9 interposed write;
- `python/tests/acceptance/test_dataset_address_acceptance.py`, `python/tests/acceptance/n2_arms_cut29.py` and `python/tests/acceptance/test_n2_cut29.py`: durable arms, declarations and guard;
- `python/tests/test_designs_corpus.py`: the design-count guard;
- `python/tools/cut29_acceptance.py` and `python/tools/roadmap_status.py`: runner and accounting;
- `docs/designs/2026-08-02-world-addressing-design.md`: a dated note on the §4.2 dataset row;
- `docs/superpowers/specs/2026-09-10-world-resolution-slice-2b-design.md`: a dated §12 note;
- `docs/designs/2026-08-03-redesign-adoption-ledger.md`, `docs/plans/2026-08-29-implementation-roadmap.md`, `docs/guide/identity-world-and-change.md`, `docs/guide/glossary.md`, `docs/guide/contracts-and-adoption.md`, `docs/guide/foundations.md`, `README.md` and the cut 29 results record: discharge and navigation.

Out of scope:

- `dataset.py`: the fold is the ruling and is not touched;
- a `corpus_check` or world-audit finding for a handle-addressed dataset in a corpus written outside the boundary (design §11 item 1);
- `beliefs-24b42b`, divergent correction-history reconciliation: the lane's next boundary, not a prerequisite;
- the seven modules that already compute the address from a declaration (`closure.py`, `evaluation.py`, `facet_read.py`, `production.py`, `admission.py`, `belief.py`, `corpus.py`'s readers): read and not rewritten;
- the mm30 reproduction record: its records already sit at derived addresses; no new measurement.

## 3. Selection

### W2 — closed at cut 25, re-read on its dataset arm
Two writers in two corpora build a dataset from one declaration under different titles and observation attesters and mint one address; resource order, repetition and names give the same address and one changed digest gives a different one; the world's producers map and a run's `observes` closure name the derived address; a declaration under an unaccepted algorithm refuses `BasisMissing` at the builder and again at the boundary for a hand-built record; `dataset_address_of` reads the stored declaration and agrees with the fold. Selected: unit `W2`. **Deferred:** nothing.

### W3 — closed at cut 4, re-read on its builder arm
`dataset_node` with an empty or unpinned declaration refuses `BasisMissing` before any write; a declared-not-held dataset is minted (the narrowed arm, unchanged); the boundary's own refusal of a hand-built unpinned record still runs and still fails when its guard is removed. Selected: unit `W3`. **Deferred:** nothing.

### W8 — part, the address-conflict conflict on datasets
A hand-built dataset at a handle address refuses `DatasetAddressDisagreement` on `add`, on `import_bundle` naming the member, and on `move` into a governed destination; the same bytes at the derived address are admitted; `consolidate` of two records at one derived address gives one address and no redirect; `consolidate` of a valid survivor with a raw record at the same id carrying different digests refuses `DatasetAddressDisagreement` naming `other` before anything is written, the invalid record is still present in its corpus afterwards, and swapping `keep` names `keep`. Selected: unit `W8`. **Deferred:** the ambiguous-search-term conflict, which needs the pinned authority snapshot (ledger artifact 11) and is W9's arm restated (`authority-labels`) — unchanged from cut 28.

### Boundary invariants
The fold (`dataset.py`) is byte-unchanged; the first clause of `_refuse_dataset_basis` and its two call lines are byte-unchanged; no referrer is rewritten; no address is retired; `revise` still preserves the `dataset` facet; the mm30 corpus's recorded dataset addresses are what the builder now derives.

## 4. Accounting

Three guarantee rows are read, **0 full/closed** newly (W2 and W3 are re-read on dataset arms and keep their closed status; W8 stays partial on its ambiguous-search-term conflict), and **3 declaration units** carry them: `W2`, `W3`, `W8`. `world-resolution` then retains one filed follow-up, `beliefs-24b42b`.

## 5. N2 and acceptance obligations

1. The declaration inventory is exactly the three units `W2`, `W3` and `W8`, each single-homed to the test that exercises it.
2. Every durable arm runs on the certified volume. Capability refusal is an error, never a skip or waiver.
3. The aggregate runner names `PREFIX_RUNNERS = ("cut28_acceptance.py",)` and `PHASE_MODULES = ("test_dataset_address_acceptance.py", "test_n2_cut29.py")`.
4. The 6 declared arms cover every sabotage site: in `stored.py` (the builder deriving the id from the title instead of the declaration; the builder minting through a `None` address; `dataset_address_of` answering `node.id` instead of the stored declaration), in `corpus.py` (the id/derived-address agreement dropped on `add`; the import loop skipping datasets), and in `relocation.py` (`consolidate` validating the survivor only).
5. `test_n2_cut29.py` audits them by the cut-28 pattern with the staleness probe's baseline taken from the tree; cut 7's guard carries a dated live adapter for the X9 interposed write and every other live matcher still applies exactly once.
6. Prior declarations remain frozen and no check is reclaimed.
7. This document and its declaration inventory are pinned by digest before discharge.

The sites in item 4 count three in `stored.py`, two in `corpus.py` and one in `relocation.py`: **6 arms**.

## 6. Second reader

The spec's one review pass on 2026-09-14 resolved two findings (§12 there): consolidation now validates both inputs, and the boundary's existing `BasisMissing` checks migrate to hand-built records so the builder's refusal cannot satisfy them. The user approved the spec and the freeze on 2026-09-14.

## 7. Limitations

1. Boundary-only: a corpus written outside the write boundary can hold a dataset at a handle address unreported (design §11 item 1).
2. One record per byte set: a second observer of the same bytes edits through `revise` (design §11 item 2).
3. The accepted-algorithm set is still `{"sha256"}` (design §11 item 3).
4. W8's search-term conflict is unrun and stays with `authority-labels`.
