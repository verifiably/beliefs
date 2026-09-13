# Conformance cut 27 — snapshots, import, audit and diagnostics

**Status:** discharged 2026-09-13; frozen before implementation. Results: `../plans/2026-09-13-conformance-cut-27-results.md`.
**Frozen:** 2026-09-13, before implementation, on `design/world-resolution-slice-3`
**Design:** `../superpowers/specs/2026-09-13-world-resolution-slice-3-design.md`, reviewed three times 2026-09-13
**Numbered after** cut 26 (roadmap concurrency rule 1) and **serialized after** its discharge, which is in the branch ancestry (rule 5).

## 1. What this cut is

The following baseline describes the tree before implementation; cut 27 is now discharged, and the dated results record preserves the measured outcome.
Cut 7 built the one evaluator the world-addressing design names —
`world/read.py`'s `validate_receipt`: well-formedness from the document alone,
then availability, then the rebuild — and gave it one caller, the coreference
edge query. The design names three callers over that evaluator: an **explicit
import** that refuses what it can refute before any write, an **audit** that
evaluates stored pairs, reports every malformed pair as its own finding and
reduces a snapshot's state, and a **diagnostic query** that reports the same
result and writes nothing. None of the three exists on `main`. No act admits an
epoch carrier into `epochs/` other than publication; nothing reduces a
snapshot's receipts to `checked`, `contradicted` or `unchecked`; and the
"query" is a per-receipt function with no snapshot reduction.

The semantic audit has the mirror-image gap. `audit_corpus` is corpus-local and
reads the corpus root through the view's private handle; the three
recomputations it drives — verification, assessment, lineage basis — were
widened to the world view only for verification (cut 23, R19). And every
opener in the tree constructs a strict `nodes` corpus, so a damaged root — one
unparsable file, one misplaced file, one duplicated uid — is not judged but
refused, as `CorpusStateMalformed` naming the first fault. `nodes` 2.0 (landed
2026-09-12, `b0c37b8`) opens a corpus in *collecting* mode, excluding the
damaged, misplaced and colliding files and reporting each through `check()`;
the adoption ledger's row 3 records "audits over damaged corpora" as buildable
here and owned by no boundary until a cut selects it.

This slice builds the three callers, widens the audit to the world, makes the
audit judge a damaged corpus rather than refuse it, and closes the four
filed audit-finding questions from slices 1, 2 and 2b.

The selection rule is cut 5's: a clause is selected only when its source mutation and every named check run inside §2. A row with any unrun arm is partial.

> **2026-09-13 pre-implementation freeze correction:** the initial freeze
> named two planned focused-test files by obsolete names. The boundary below
> now names `test_world_import_epoch.py` and `test_world_audit.py`; no
> implementation had begun when this correction superseded the initial freeze.

## 2. The boundary

In scope:

- `docs/designs/2026-09-13-conformance-cut-27.md`: the frozen boundary, selection, accounting and obligations;
- `python/src/beliefs/errors.py`: `EpochImportRefused` and `CorpusDamaged`;
- `python/src/beliefs/world/read.py`: `_contract_fault`, `_standing` and `validate_receipt`;
- `python/src/beliefs/world/epoch.py`: `_carrier_epoch` and `_locked_retained_directories`;
- `python/src/beliefs/world/importing.py`: `import_epoch` and `EpochImportReport`;
- `python/src/beliefs/world/audit.py`: `SNAPSHOT_STATES`, `SnapshotVerdict`, `EpochAudit`, `audit_epochs` and `snapshot_state`;
- `python/src/beliefs/world/view.py`: report-mode `open_world_view`, `DamageReport`, `damaged`, `captured_records` and `captured_manifest`;
- `python/src/beliefs/corpus.py`: `_collecting_view`, `_CapturedCheckView` and the `corpus_check` split;
- `python/src/beliefs/audit.py`: `WORLD_AUDIT_CODES`, `WorldAudit`, `audit_world` and the world-level checks;
- `python/src/beliefs/world/registry.py`: the X5 and W13 relabel fixtures;
- `python/src/beliefs/world/__init__.py`: the new public exports;
- `python/tests/test_world_receipts.py`, `python/tests/test_world_import_epoch.py`, `python/tests/test_world_epoch_audit.py`, `python/tests/test_world_view.py` and `python/tests/test_world_audit.py`: focused behavior;
- `python/tests/acceptance/test_world_audit_acceptance.py`, `python/tests/acceptance/n2_arms_cut27.py` and `python/tests/acceptance/test_n2_cut27.py`: durable arms, declarations and guard;
- `python/tools/cut27_acceptance.py` and `python/tools/roadmap_status.py`: runner and accounting;
- the S9 ledger and navigation surfaces, dated guarantee notes, adoption ledger, roadmap, guide, README and cut 27 results record.

Out of scope:

- slice 4 (`beliefs-0e523a`): W7;
- W8 and W8b: retained and unselected, audited at slice 4's discharge; `beliefs-fda0e5`'s repair is on `main`; the view's duplicate-uid refusal is slice 1's invariant, never W8b conformance;
- R23's rules-store clauses and W8a's `instrument-certification` arm (`contract-cut`);
- the ledger's "manifest safety" item (unowned, spec §11 item 2);
- `audit_corpus`'s signature and every read-side function of `world/read.py` other than `validate_receipt`, `_contract_fault` and `_standing`.

## 3. Selection

### R23 — part, snapshot, explicit-import and cross-corpus-divergence clauses
A trimmed snapshot with its receipt untouched is refused at import as malformed at the subject check, and the internally consistent omission is refused as refuted after reconstruction; a carrier missing a receipt is refused; a receipt naming corpora rather than states or a bare version string is malformed at import and under audit; an all-malformed snapshot is `unchecked` with a finding per pair; a fabricated carrier raw-written into `epochs/` is read through without evaluation and reported under audit; a receipt over an absent corpus imports with a finding and is evaluated by a later audit; a moved corpus, and one of two moving, are `unresolvable`; `R2` in the other corpus claiming `D` from `B` yields `lineage-divergent`, `not-certified` and a moved digest. Selected: unit `R23`. **Deferred:** the rules-store clauses (`contract-cut`).

### W8a — part, import-boundary and audit arms
Well-formedness before availability: a receipt naming only `A` for `{A, B}` is malformed with `A` standing and the binding held; extra corpus, duplicate id and wrong subject refused; syntactically valid unheld identities are `unresolvable`; every malformedness decided with no corpus and no rule. A malformed receipt raw-written past the boundary is `malformed` under audit and query with a finding naming the pair, excluded from the reduction, and a validating receipt beside it makes the snapshot `checked`; the two roads to `unchecked` are distinguishable; mounting evaluates nothing; import, audit and query agree within one availability context and the same pair moves from `unresolvable` to `refuted`/`validated` after a mount and an audit; a resolvable-and-refuted receipt is refused before any write; the unheld-rule route evaluates after installation. Import refuses a write; audit and query write nothing, the audit distinguished by domain (spec decision 3, recorded by dated note on the row). Selected: unit `W8a`. **Deferred:** the `instrument-certification` omission-refutes arm (`contract-cut`).

### X5 — closes, relabel
The admission arm (cut 6) and the build arm (cut 7) are read in full; the "replica declaration excepted, minting no admission" clause is carried by `test_replica_restoration_recomputes_presence_without_admission`, with R34's supersession of cut 6's replica refusal half cited. One arm over existing code: two carriers collapsed to one refuse nothing. Selected: unit `X5`. **Deferred:** nothing.

### W13 — closes, relabel with two fixtures
Every clause read at cuts 6, 7, 9 and 14 is cited; the root-move fixture (move, rename, re-mount; `corpus_id`, coverage declaration and `belief_input_digest` unchanged) and the coordinated-forgery fixture (forged admission beside the retained one undetected; receipts `unresolvable` against the edited corpus and `validated` against the replica; indistinguishable from a declared fork) are new; the file-rename inertness clause is superseded by `nodes` 2.0 well-placedness and its replacement is S9's `path-mismatch` arm. Selected: unit `W13`. **Deferred:** nothing.

### S9 — closes
An unparsable, a misplaced, a uid-colliding and an id-colliding file each yield their construction finding, an audited remainder, `corpus-damaged`, no drift comparison and `CorpusDamaged` on every read of a mapped address; a foreign base pin is `corpus-damaged` with cause `base-pin`; the receipt evaluator answers `unresolvable`; the default open still refuses; no state identity is computed over a remainder. Selected: unit `S9`. **Deferred:** nothing.

### Boundary invariants
No refusal borrows `NotPresent` or `Unknown`; every object served is detached; the world lock is released before any corpus is touched; nothing but the import's eleven creates is written; a collecting corpus never reaches a writer or `_ROOT_STATES`.

## 4. Accounting

Five guarantee rows are read, **3 full/closed** (X5, W13, S9), 2 partial (R23, W8a), and **5 declaration units** carry them: `R23`, `W8a`, `X5`, `W13`, `S9`. W8 and W8b stay retained and unselected (§2); `packaging-remainder` closes with X5 and W8a's packaging arms.

## 5. N2 and acceptance obligations

1. The declaration inventory is exactly the five units `R23`, `W8a`, `X5`, `W13` and `S9`, each single-homed to the test that exercises it.
2. Every durable arm runs on the certified volume. Capability refusal is an error, never a skip or waiver.
3. The aggregate runner names `PREFIX_RUNNERS = ("cut26_acceptance.py",)` and `PHASE_MODULES = ("test_world_audit_acceptance.py", "test_n2_cut27.py")`.
4. The 27 declared arms cover every sabotage site: in `world/read.py` (availability evaluated before well-formedness; the coverage comparison narrowed to `coverage.yaml`; the member-subject comparison dropped; `_standing` raising on a damaged carrier), in `world/importing.py` (a refuted receipt admitted; `current` written; log-head records written; the source directory's name trusted; the world-membership check dropped), in `world/audit.py` (the reduction over the audited epoch alone; a malformed receipt folded into the reduction; a carrier that does not read skipped silently; `OSError` escaping the sweep; anchors corroborated against the epoch itself), in `world/view.py` (the strict open kept under `report`; a state identity computed over the remainder; a damaged address served; drift omitted; records captured under a foreign base pin), in `corpus.py` (`_record_findings` run over the live view), in `audit.py` (`CorpusDamaged` escaping the endpoint check; the endpoint resolved corpus-locally; the identifier check keyed on the selected identifier only; recomputation over damage reported as `derivation-malformed`), in `world/registry.py` (two carriers collapsed to one — X5), and in `world/registry.py` again (the corpus root's path digested into the state identity; the coverage declaration taken from the root's name — W13).
5. `test_n2_cut27.py` audits them by the cut-12 pattern with the staleness probe's baseline taken from the tree.
6. Prior declarations remain frozen and no check is reclaimed.
7. This document and its declaration inventory are pinned by digest before discharge.

## 6. Second reader

The design's three review passes on 2026-09-13 are its second reading: eleven first-review findings, four gaps and one correction in the second review, and two third-review issues were resolved.

## 7. Limitations

1. The collecting audit reports each construction fault and audits the remainder, but does not judge excluded-file contents or dangling records their absence creates.
2. The ledger's "manifest safety" item stays unowned and unselected.
3. W8 and W8b remain retained and unselected for slice 4's discharge.
4. A writer on a damaged root still fails at construction; the audit does not make it writable.
5. The world audit uses serial per-corpus coherent captures, not one simultaneous world state.
6. Anchor corroboration does not replay or verify a chain.
7. A cross-corpus uid collision involving a damaged corpus remains undecided until repair and re-audit.
8. A managed deletion since publication refuses the audit at that epoch; rebuild before auditing the new epoch.
