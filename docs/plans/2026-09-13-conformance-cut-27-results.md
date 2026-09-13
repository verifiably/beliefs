# Conformance cut 27 — results

**Cut:** `../designs/2026-09-13-conformance-cut-27.md`, corrected freeze
`a04fc6a87fcd6fa49090d2344076cfd2d560fe7b`; freeze document SHA-256
`7eb63bee70679bd4e79db7ed5fc41c3779eae3a4eac2a8a520cf63d2f9a3d4d1`
**Declaration:** `3674da8ab348fc3afdf0a5d7af09a141b9d665a3`; SHA-256
`564cd8fa93f5d0c22d374f90ba0b2bfbee3758504c977a5367cbd1930b15008f`
**Subject:** epoch import, epoch audit and query, and world audit over damaged corpora
**Discharged:** 2026-09-13, on `design/world-resolution-slice-3`
**Runner:** `python/tools/cut27_acceptance.py`

## 1. What ran

Task 10 ran the complete acceptance chain against the source now at `40c7dcb`:

```text
(cd python && uv run --frozen python tools/cut27_acceptance.py)
```

**Exit code 0.** Task 11 copied its transcript byte-for-byte; both copies have
SHA-256 `0b41d1e1123db4608f1f6c2e3d7bf801d9193ff368230d79297eac4a221959eb`.
The retained transcript is [`certified.log`](2026-09-13-conformance-cut-27-run/certified.log).
No capability waiver, skip or refusal occurred.

The prefix chain was cut 27 → cut 26 → cut 25 → cut 24 → cut 23 → cut 22 →
cut 21 → cut 20 → cut 19 → cut 18 → cut 17. Its **38 phase summaries
report 634 passed**:

| phase | module | summary |
|---|---|---|
| cut17 phase 1/19 | `test_n2_cut6.py` | 24 passed in 12.68s |
| cut17 phase 2/19 | `test_n2_cut7.py` | 42 passed in 47.58s |
| cut17 phase 3/19 | `test_n2_cut9.py` | 23 passed in 17.94s |
| cut17 phase 4/19 | `test_intent_boundary_acceptance.py` | 18 passed in 6.30s |
| cut17 phase 5/19 | `test_n2_cut11.py` | 17 passed in 30.03s |
| cut17 phase 6/19 | `test_successor_admission_acceptance.py` | 4 passed in 2.12s |
| cut17 phase 7/19 | `test_n2_cut12.py` | 16 passed in 14.16s |
| cut17 phase 8/19 | `test_confinement_acceptance.py` | 15 passed in 317.31s |
| cut17 phase 9/19 | `test_n2_cut13.py` | 16 passed in 131.07s |
| cut17 phase 10/19 | `test_coordination_acceptance.py` | 22 passed in 27.60s |
| cut17 phase 11/19 | `test_n2_cut14.py` | 7 passed in 15.54s |
| cut17 phase 12/19 | `test_cut15_lineage.py` | 5 passed in 83.27s |
| cut17 phase 13/19 | `test_n2_cut15.py` | 8 passed in 50.55s |
| cut17 phase 14/19 | `test_relocation_acceptance.py` | 16 passed in 72.10s |
| cut17 phase 15/19 | `test_n2_cut16.py` | 7 passed in 78.75s |
| cut17 phase 16/19 | `test_permit_acceptance.py` | 8 passed in 4.38s |
| cut17 phase 17/19 | `test_permit_boundary.py` | 18 passed in 2.70s |
| cut17 phase 18/19 | `test_permit_entry_points.py` | 110 passed in 27.15s |
| cut17 phase 19/19 | `test_n2_cut17.py` | 8 passed in 15.56s |
| cut18 phase 2/3 | `test_deletion_acceptance.py` | 16 passed in 54.27s |
| cut18 phase 3/3 | `test_n2_cut18.py` | 7 passed in 27.73s |
| cut19 phase 2/3 | `test_session_acceptance.py` | 31 passed in 31.42s |
| cut19 phase 3/3 | `test_n2_cut19.py` | 7 passed in 27.28s |
| cut20 phase 2/3 | `test_facet_acceptance.py` | 17 passed in 40.82s |
| cut20 phase 3/3 | `test_n2_cut20.py` | 5 passed in 35.39s |
| cut21 phase 2/3 | `test_verification_acceptance.py` | 4 passed in 7.15s |
| cut21 phase 3/3 | `test_n2_cut21.py` | 7 passed in 36.01s |
| cut22 phase 2/3 | `test_biology_acceptance.py` | 2 passed in 2.47s |
| cut22 phase 3/3 | `test_n2_cut22.py` | 7 passed in 4.31s |
| cut23 phase 2/3 | `test_world_view_acceptance.py` | 30 passed in 119.20s |
| cut23 phase 3/3 | `test_n2_cut23.py` | 7 passed in 43.03s |
| cut24 phase 2/3 | `test_coreference_acceptance.py` | 15 passed in 87.36s |
| cut24 phase 3/3 | `test_n2_cut24.py` | 7 passed in 23.81s |
| cut25 phase 2/3 | `test_source_address_acceptance.py` | 20 passed in 30.76s |
| cut25 phase 3/3 | `test_n2_cut25.py` | 8 passed in 8.37s |
| cut26 phase 2/2 | `test_n2_cut26.py` | 10 passed in 1.43s |
| cut27 phase 2/3 | `test_world_audit_acceptance.py` | 41 passed in 218.09s |
| cut27 phase 3/3 | `test_n2_cut27.py` | 9 passed in 51.77s |

Cut 27's final inventory is:

```text
declared arms: 27 (= 5 declaration units; 5 guarantee rows)
```

Against the implementation at `40c7dcb`, from the repository root through
the vendored `tools/tt` recipes:

- `just check` exited **0** in 23.669s: Ruff passed; Pyright reported zero
  errors, warnings and information diagnostics; TypeScript typecheck and Biome
  passed; and `tasks check` reported zero errors and warnings. Transcript:
  [`check.log`](2026-09-13-conformance-cut-27-run/check.log).
- `just test` exited **0**: **4,557 Python tests passed in 1,102.83s
  (0:18:22)** and **142 TypeScript tests passed across 7 files**. Transcript:
  [`test.log`](2026-09-13-conformance-cut-27-run/test.log).

## 2. Accounting and disposition

Cut 27 reads five guarantee rows: **3 full/closed** (X5, W13 and S9) and
**2 partial** (R23 and W8a). Five declaration units carry 27 arms. Minting S9
moves the corpus from 195 to **196 rows**; closing X5, W13 and S9 moves the
closed count from 148 to **151**, leaving **45 open**. The generated accounting
reports exactly `Closed 151 of 196; open 45.`

- **X5 closes.** Its admission and build arms are read together and the row is
  relabelled full.
- **W13 closes.** Its prior clauses and the two cut 27 fixtures are read
  together and the row is relabelled full.
- **S9 closes.** All seven damaged-corpus arms are selected and read.
- **R23 remains partial** only on its rules-store clauses under `contract-cut`.
- **W8a remains partial** only on its `instrument-certification` arm under
  `contract-cut`. W8 and W8b remain retained and unselected.

With X5 closed and W8a's packaging arms read, `packaging-remainder` closes and
leaves the open-boundary set.

## 3. Corrections and deviations from the frozen cut

The frozen cut's §§2–7 and the canonical declaration did not change. The
following measured corrections were required or clarified during implementation:

- **2026-09-13 — R23 omission fixtures.** The literal omitted-producer carrier
  is caught one gate earlier as `malformed-receipt` by the subject check. The
  reconstruction clause is read by the internally consistent fixture, which
  recomputes the subject and is refused as `refuted-receipt`.
- **2026-09-13 — R23 divergence arm (e).** The one-held-`D` fixture passed on
  the existing slice 1 implementation: it reported `lineage-divergent` and
  `not-certified`, and adding R2 moved `belief_input_digest`. No slice 1
  production fix was required.
- **2026-09-13 — W13 clause reading.** Root relocation preserves `corpus_id`,
  coverage and `belief_input_digest`; a coordinated manifest/admission forgery
  remains undetected and reads like a declared fork; replica restore preserves
  the declaration. The old file-rename inertness clause is superseded by
  `nodes` 2.0 well-placedness and S9's `path-mismatch` arm.
- **2026-09-13 — live permit inventory.** The first complete chain stopped at
  cut 17 phase 18 because `import_epoch` had entered the closed write-entry
  inventory without its exhaustive live permit case: **1 failed, 107 passed**.
  Adding that one established case corrected the live guard; the successful
  chain then reported **110 passed** for the phase. No frozen declaration changed.
- **2026-09-13 — check exit capture.** `just check` completed every stage, but
  the surrounding shell tried to assign zsh's reserved `status` variable while
  reporting its exit. The command was not rerun: `tools/tt`'s recorded entry for
  target `check` at revision `40c7dcb` directly reports exit 0, and the retained
  log contains every successful stage.

The measured declaration count is exactly the frozen count of 27 arms; there
is no arm-count deviation.

### 2026-09-13 — post-discharge review correction

The final review found that an ill-formed textual receipt subject entered the
snapshot groups as an ordinary unchecked identity. The shared grouping boundary
now uses the existing identity validator: missing or ill-formed subjects yield
only their receipt finding, while a well-formed subject on an otherwise malformed
receipt still enters the unchecked group. Five invalid-subject cases failed
before the fix; those cases, the absent-subject case and the existing named
all-malformed case then passed (**7 passed**).

A new durable world-audit test retains a validating receipt beside a genuinely
refuted own receipt for the same subject. The own `receipt-refuted` finding
remains and `snapshot-contradicted` is absent. Replacing the retained-set decision
with a local-only decision made that assertion fail; the production decision
was restored. The private verification fixture now returns its full tuple to
all callers. The guide's stale open-callers claim and five ledger anchors, the
freeze-document hash label above, the evaluator docstring and the broader world
task's remaining-work body were corrected.

The focused verification below covers this later correction. The **4,557 Python
and 142 TypeScript** results in §1 remain historical evidence for `40c7dcb`;
they do not cover this source fix. The original transcripts, including the
Pyright version-update notice, are unchanged; that notice is not an analysis
warning or a branch defect. No dependency, frozen §§2–7, declaration or hash pin
changed. Source-site and freeze guards required no retargeting.

From `python/`:

```sh
uv run --frozen pytest -n 8 --dist=loadfile tests/test_world_epoch_audit.py tests/test_world_receipts.py tests/test_world_audit.py tests/test_world_view.py tests/acceptance/test_world_audit_acceptance.py
uv run --frozen pytest tests/test_arm_staleness.py tests/test_frozen_guards.py tests/test_designs_corpus.py tests/acceptance/test_n2_cut27.py -k 'not every_live_check and not every_arm_fails'
```

The first command reported **161 passed in 220.67s (0:03:40)**.
The second command reported **35 passed, 2 deselected**; its two exclusions are
the already retained full cut-27 mutation run and its baseline, not source-site
or frozen-evidence checks. The later integrated full-gate result is recorded in §6.


## 4. Reproduction measurement

This cut performs **no new mm30 reproduction run**. The previous single-corpus
measurement remains [cut 22 results §4](2026-09-08-conformance-cut-22-results.md#4-reproduction-measurement)
and the [mm30 record](../designs/2026-09-05-mm30-reproduction.md): 307 of 334
claims typed, 27 `no-claim-recorded`, and equal original/rederived
`NoBelief(no-directional-outcome)` answers. Those answers carry no
`belief_input_digest`; no new mm30 digest comparison or isolated causal claim
is made here.

## 5. Remaining boundary

`world-resolution` retains **W7, W8 and W8b**, all unselected, plus the filed
dataset-addressing (`beliefs-48214e`) and divergent correction-history
(`beliefs-24b42b`) follow-ups. Slice 4 (`beliefs-0e523a`) owns the next view
evaluation and the W8/W8b discharge audit.

`contract-cut` retains **R23** only on its rules-store clauses and **W8a** only
on its `instrument-certification` arm. The ledger's manifest-safety item remains
unowned and unselected.

## 6. Main integration

Merged `design/world-resolution-slice-3` into `main` with `--no-ff` on
2026-09-13 at `645dc8f999c32e10007893955004c64b07a1f7e7`, after the final
whole-branch review and scoped approval of correction commit
`a8f78a81e95cc901c218600edef299712f1bc9f5`.

`just gate` on that merged revision exited **0**: Ruff, Pyright, TypeScript
typecheck, Biome and task checks passed; the serial Python suite reported
**4,563 passed in 1,125.76s**, and TypeScript reported **142 passed** across
seven files. Task validation reported zero errors and warnings. The exact
output is retained in [main-gate.log](2026-09-13-conformance-cut-27-run/main-gate.log).
This run covers the corrected source, including the subject-grouping regression
and validated-versus-refuted retained-receipt composition check. The earlier
transcripts in §1 remain unchanged.

The tracked Task 2 verification note is preserved with the other evidence as
[receipt-contract-implementation.md](2026-09-13-conformance-cut-27-run/receipt-contract-implementation.md)
when clearing the temporary implementation workspace.
