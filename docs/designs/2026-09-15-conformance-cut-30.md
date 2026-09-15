# Conformance cut 30 — reconciling divergent correction histories at `consolidate`

**Status:** discharged 2026-09-15; results: ../plans/2026-09-15-conformance-cut-30-results.md
**Frozen:** 2026-09-15, before implementation, on `design/world-resolution-slice-6`
**Design:** `../superpowers/specs/2026-09-15-world-resolution-slice-6-design.md`, approved 2026-09-15 after two reviews (§11 there)
**Numbered after** cut 29 (roadmap concurrency rule 1) and **serialized after** its discharge, which is in the branch ancestry (rule 5).

## 1. What this cut is

The baseline below describes `main` at `6f08418` before implementation.

Slice 2b gave a `source` record a linear, attributed correction history and
made `consolidate` refuse two replicas whose histories differ
(`HistoryDisagreement`, 2b §7): a chain cannot hold two branches, and keeping
the survivor's chain would drop the addresses the other replica held. The
refusal has no operator escape — any further correction widens the
difference — and the families design's recovery contract ("re-run
`consolidate`") could not be met for a `source` once histories diverged.

This cut adds one entry kind to the same facet — a *consolidation entry*,
`from == to`, carrying `absorbed`: the other replica's unheld events as a
nested chain — and a pure reconciliation (`stored.reconcile_correction_histories`)
that fast-forwards a prefix, absorbs a divergent tail, and is the identity over
its own result, so an interrupted run re-runs to completion. One token is one
event: it may recur across chains only as the same entry. Identifier maps that
differ still refuse, naming the schemes; the rationale is validated before
reconciliation on every path.

The selection rule is cut 5's: a clause is selected only when its source mutation and every named check run inside §2. A row with any unrun arm is partial.

## 2. The boundary

In scope:

- `docs/designs/2026-09-15-conformance-cut-30.md`: the frozen boundary, selection, accounting and obligations;
- `python/src/beliefs/stored.py`: `IdentifierCorrection.absorbed`, the recursive reader, `held_source_addresses` over absorbed chains, `reconcile_correction_histories`;
- `python/src/beliefs/relocation.py`: `consolidate`'s rationale validation, early intent, reconciliation call; `_reconcile`'s `correction_entries`;
- `python/src/beliefs/errors.py` and `corpus.py`: docstrings only;
- `python/tests/test_source_address.py`, `python/tests/test_identifier_correction.py`: the unit obligations of design §7.1;
- `python/tests/acceptance/test_source_address_acceptance.py`: the lifecycle absorb and the interruption re-run (design §7.2);
- `python/tests/acceptance/test_n2_cut25.py`: the dated `W5a-m` live re-target; `test_n2_cut26.py`–`test_n2_cut29.py`: the second re-targeted row in their prior-declaration checks; `python/tests/arm_staleness.py`: `re_targeted_rows` reads a guard's `RETARGETED_ROWS`;
- `python/tests/acceptance/n2_arms_cut30.py`, `python/tests/acceptance/test_n2_cut30.py`, `python/tools/cut30_acceptance.py`: declaration, guard, runner;
- `python/tools/roadmap_status.py`: the cut 30 accounting entry;
- `docs/superpowers/specs/2026-09-10-world-resolution-slice-2b-design.md` (§7, §12 item 2) and `docs/designs/2026-08-02-world-addressing-design.md` (W5a's consolidation clause): dated notes;
- `docs/designs/2026-08-03-redesign-adoption-ledger.md`, `docs/plans/2026-08-29-implementation-roadmap.md`, `docs/guide/identity-world-and-change.md`, `docs/guide/contracts-and-adoption.md`, `docs/guide/glossary.md`, `README.md` and the cut 30 results record: discharge and navigation.

Out of scope:

- identifier-map merging: `consolidate` refuses differing maps (design decision 1);
- releasing a blocked address (2b §13 item 1);
- `report.py`: `Consolidated` is unchanged (design decision 7);
- `correct_identifier`'s append rule and every other mutation family: unchanged;
- the mm30 reproduction record: no source is consolidated there; no new measurement.

## 3. Selection

No guarantee row is read. `W5a` closed at cut 25 and stays closed; its consolidation arm (`W5a-m`, "consolidation refuses divergent correction histories") is retired by design decision 5 and re-targeted live to its successor, `W5a-p` here (design §7.5). `W8` stays partial on its ambiguous-search-term conflict (cut 28, unchanged); its map-conflict arm (`W8-b`) is untouched.

### Boundary invariants
The `W8-b` anchor `            if keep_map != other_map:` and the `W5a-l` / `W5a-k` anchors `        if frm == to:` and `    if list(node.deprecated_ids) != expected:` are byte-unchanged; no `n2_arms_cut*.py` body is edited; no referrer is rewritten; no address is released; `move`, `delete`, `supersede`, `revise` are unchanged for `source`.

## 4. Accounting

Zero guarantee rows are read, **0 full/closed** newly, and **1 declaration unit** carries the arms: `W5a`, re-read on its reconciliation arms. `world-resolution` then retains no filed follow-up and leaves the ledger's `Current state` table and the roadmap's boundary index at discharge.

## 5. N2 and acceptance obligations

Declared in `python/tests/acceptance/n2_arms_cut30.py` (design §7.3): `W5a-p` (divergent histories absorbed, not dropped), `W5a-q` (the absorbed chain is validated), `W5a-r` (held addresses reach into absorbed chains), `W5a-s` (one token is one event across chains), `W5a-t` (a consolidation entry changes nothing), `W5a-u` (the entry carries the operation's token), `W5a-v` (a prefix fast-forwards without an entry), `W5a-x` (an already-held event is not absorbed again), `W5a-y` (conflicting reuse refuses before any intent), `W5a-z` (the rationale is validated before reconciliation on every path). Each is a byte-exact sabotage on a line this cut writes, audited by `arm_staleness` against the tree. Acceptance: design §7.2. Runner: `python/tools/cut30_acceptance.py`, `PREFIX_RUNNERS = ("cut29_acceptance.py",)`, phase modules `test_source_address_acceptance.py` and `test_n2_cut30.py`.

## 6. Discharge

On the certified volume beside the checkout, `just check`, `just test` and the runner all exit 0; the results record `../plans/2026-09-15-conformance-cut-30-results.md` retains the transcripts and digests; the branch merges `--no-ff`.

## 7. Limitations

Design §10: reconciliation is by `keep`; conflicting token reuse refuses with no seam to repair it; a blocked address is still not released; map merge is not offered; the absorbed fork point is provenance, not a clause.
