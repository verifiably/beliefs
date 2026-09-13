# World resolution slice 3 — implementation plan

**Status:** implementation in progress since 2026-09-13.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the three receipt-evaluator callers the world-addressing design names — an explicit epoch import, an epoch audit with a snapshot-state query — widen the semantic audit to the world so it judges a damaged corpus instead of refusing it, and discharge R23's snapshot/import/divergence clauses, W8a's packaging arms, the X5 and W13 relabels and the new row S9 as conformance cut 27.

**Architecture:** The evaluator (`world/read.py`'s `validate_receipt`) gains the coverage-agreement and subject checks and answers `unresolvable` for a carrier it cannot read. A new `world/importing.py` admits an epoch carrier of this world create-only after evaluating every receipt; a new `world/audit.py` sweeps every retained epoch, reduces snapshot states over the retained set and corroborates anchors against the registry; both write nothing but the import's eleven members. `open_world_view` gains `on_damage="report"`, which re-opens a damaged carrier in `nodes` collecting mode inside the same capture hold and refuses every read of its addresses with `CorpusDamaged`; `audit.audit_world` judges the capture corpus by corpus and across corpora. The cut is frozen first and discharged through its own runner after cut 26's.

**Tech Stack:** Python 3.13 via `uv run --frozen`, pytest with `pytest-xdist`, pydantic v2 `Node` models from `nodes` 0.2.0 (collecting-mode `Corpus`), the `atoms` durable engine on the certified volume for acceptance, PyYAML for fixtures; ruff and pyright as the gate.

**Spec:** `docs/superpowers/specs/2026-09-13-world-resolution-slice-3-design.md` (reviewed three times, approved 2026-09-13 at `72cb8dc`). Every task cites its section; read the spec first — the plan argues from it.

## Global Constraints

- Work on branch `design/world-resolution-slice-3` in `.worktrees/world-slice-3`; every path below is relative to the repository root, and every path you show the user is prefixed `.worktrees/world-slice-3/`. Conventional commits; no AI-attribution trailer; no `/home/<user>` or absolute Dropbox paths in code or docs.
- Run every Python command from `python/` with `uv run --frozen …`; system python lacks `beliefs`. Never pass `-q` to pytest (addopts already sets it, and `-qq` drops the summary line); read the final `N passed` line before claiming a count.
- Fast loop: `uv run --frozen pytest -n 8 --dist=loadfile --ignore=tests/test_n2.py`. Before each commit: `uv run --frozen ruff check . && uv run --frozen pyright` (pyright takes no path argument). The pre-commit hook runs `just check` when `python/` is staged and `just hook-pre-commit-docs` otherwise; `ts/node_modules` exists (`just setup` ran).
- Tracker: `tasks start <id>` before a task's first step, `tasks note <id> "<what landed>"` and `tasks done <id> "<result>"` at its last, `tasks check` before every commit. Never edit `tasks/*.md` directly. The parent is `beliefs-46847c`; the step ids are listed in the **Task ids** section below.
- Lock discipline (spec decision 8): a reader that must judge a damaged root takes `_operation_lock_for(root).capture()`, never `_root_state_for`; the strict attempt runs inside the hold; the report-mode catch set is exactly `CorpusStateMalformed` and `ContractMismatch`; `CaptureDrift` always propagates.
- No refusal may borrow `NotPresent` or `Unknown` (spec §6): `CorpusDamaged` is raised, never returned, and a damaged corpus never enters `absent()`, `not_present` or the resolution snapshot's third state.
- Nothing writes but the import's eleven `CreateOp`s: `import_epoch` never swaps `current` and never writes a log-head record; `audit_epochs`, `snapshot_state`, `audit_world` write nothing (spec decisions 1, 3).
- Frozen files (`n2_arms_cut*.py`, cut documents, declaration tables of cuts ≤ 26) are never edited. A task that displaces a line a frozen cited-not-run guard matches records the arm in `python/tests/cited_not_run.py`'s `stale_arms`; a live guard gets a dated re-target. `uv run --frozen pytest tests/test_arm_staleness.py tests/test_frozen_guards.py` passes after Tasks 2, 5, 6.
- N2 rows are `<unit>-<letter>` (`R23-a`, `S9-c`); cut 27's `unit_of` parses exactly that. Every durable arm runs on the certified volume; a capability refusal is an error, never a skip.
- Shared surfaces this lane rewrites (roadmap rule 3): `errors.py`, `corpus.py`, `audit.py`, `world/view.py`, `world/read.py`, `world/epoch.py`, `world/__init__.py`, `python/tests/test_designs_corpus.py`, `README.md`, the ledger, the roadmap, the guide, the world-addressing, substrate and formal-model designs (dated notes only), the adoption ledger.
- The cut is frozen before implementation (Task 1) and its §§2–7 are byte-exact from the freeze commit onward; §1 stays editable. The number is 27 unless a sibling worktree has claimed it first — Task 1 checks every worktree.

## Task ids

Created 2026-09-13 against this plan; each task's first step names its id.

- Task 1: `beliefs-310b74`
- Task 2: `beliefs-be3c58`
- Task 3: `beliefs-32c2bc`
- Task 4: `beliefs-25e47f`
- Task 5: `beliefs-7b10fb`
- Task 6: `beliefs-48c9a1`
- Task 7: `beliefs-85fed2`
- Task 8: `beliefs-da09df`
- Task 9: `beliefs-d52159`
- Task 10: `beliefs-22d401`
- Task 11: `beliefs-1f5bc3`

---

## File structure

| path | responsibility |
|---|---|
| `docs/designs/2026-09-13-conformance-cut-27.md` | the frozen cut: boundary, selection, accounting, obligations |
| `docs/designs/2026-08-02-substrate-consolidation-design.md` §10, `docs/designs/2026-08-04-formal-model-and-claim-calculus-design.md` (inherit line, S table), `python/tests/test_designs_corpus.py` (`GUARANTEE_TABLES["S"]`), `README.md` (row total, design list) | the minted row S9 |
| `python/src/beliefs/errors.py` | `EpochImportRefused`, `CorpusDamaged` |
| `python/src/beliefs/world/read.py` | `_contract_fault(kind, member, receipt, published)`: coverage agreement and member-subject checks; `_standing` via the lock-only lookup, `unresolvable` on damage |
| `python/src/beliefs/world/epoch.py` | `_carrier_epoch(members, packaging_identity)` factored out of `_locked_open_epoch`; `_locked_retained_directories(world_root)` |
| `python/src/beliefs/world/importing.py` (new) | `import_epoch`, `EpochImportReport` |
| `python/src/beliefs/world/audit.py` (new) | `SNAPSHOT_STATES`, `SnapshotVerdict`, `EpochAudit`, `audit_epochs`, `snapshot_state`, anchor corroboration |
| `python/src/beliefs/world/view.py` | `on_damage`, `DamageReport`, `damaged()`, `captured_records()`, `captured_manifest()`, `CorpusDamaged` on every read of a damaged address |
| `python/src/beliefs/corpus.py` | `_collecting_view(root)`, `_CapturedCheckView`, `corpus_check` split into `_manifest_findings` and `_record_findings` |
| `python/src/beliefs/audit.py` | `WORLD_AUDIT_CODES`, `WorldAudit`, `audit_world`; `check_assessment`, `check_lineage_basis`, `stored_specs` widened |
| `python/src/beliefs/world/__init__.py` | re-exports of the new modules and names |
| `python/tests/test_world_receipts.py` | Task 2's evaluator arms |
| `python/tests/test_world_import_epoch.py` (new) | Task 3 |
| `python/tests/test_world_epoch_audit.py` (new) | Task 4 |
| `python/tests/test_world_view.py` | Task 5's report-mode arms |
| `python/tests/test_world_audit.py` (new) | Tasks 6 and 7 |
| `python/tests/test_world_relabels.py` (new) | Task 8: W13 fixtures, X5 relabel citations, R23 (e) |
| `python/tests/acceptance/test_world_audit_acceptance.py` (new), `python/tests/acceptance/n2_arms_cut27.py` (new, canonical), `python/tests/acceptance/test_n2_cut27.py` (new) | durable arms, declarations, guard |
| `python/tools/cut27_acceptance.py` (new), `python/tools/roadmap_status.py` | the runner and cut 27's accounting row |
| `docs/designs/2026-08-02-world-addressing-design.md` (W8a, W13 cells), `docs/designs/2026-08-03-redesign-adoption-ledger.md` (row 3 note, Current state), `docs/guide/identity-world-and-change.md`, `docs/guide/contracts-and-adoption.md` | dated notes |
| `docs/plans/<date>-conformance-cut-27-results.md`, ledger, roadmap, README | discharge |

---
### Task 1: Freeze conformance cut 27 and mint S9

**Files:**
- Create: `docs/designs/2026-09-13-conformance-cut-27.md`
- Modify: `docs/designs/2026-08-02-substrate-consolidation-design.md:556` (after S8's row), `docs/designs/2026-08-04-formal-model-and-claim-calculus-design.md:16` and `:933` (after S8), `python/tests/test_designs_corpus.py:38` (the `S` tuple), `README.md:96` (design list) and `:147` (row total), `docs/guide/contracts-and-adoption.md` (sources list)

**Interfaces:**
- Produces: the five declaration units `R23`, `W8a`, `X5`, `W13`, `S9` cited verbatim by Task 9's `DECLARATION_UNITS`; the literals `PREFIX_RUNNERS = ("cut26_acceptance.py",)` and `PHASE_MODULES = ("test_world_audit_acceptance.py", "test_n2_cut27.py")` cited by Task 10; the freeze sha and sha256 cited by Task 9's guard; the row id `S9` every later task's tests name.

- [ ] **Step 0: `tasks start beliefs-310b74`**

The eleven step tasks already exist under `beliefs-46847c` (the **Task ids** section); they were created against this plan on 2026-09-13. Do not add them again.

- [ ] **Step 1: Confirm the number is free**

```bash
for wt in $(git worktree list --porcelain | awk '/^worktree /{print $2}'); do ls "$wt/docs/designs" | grep -c "conformance-cut-27"; done
git log --all --oneline -- 'docs/designs/*cut-27*' | head -3
```
Expected: every count is `0` and the log is empty. If not, use the next free number everywhere below and in every later task.

- [ ] **Step 2: Mint S9**

In `docs/designs/2026-08-02-substrate-consolidation-design.md`, after S8's row (line 556) add one row:

```markdown
| **S9** | An audit judges a damaged corpus rather than refusing it — construction faults are findings, the remainder is audited, and no state identity is claimed *(added 2026-09-13, world resolution slice 3 §7)* | Science | damage a covered corpus one way at a time — an unparsable file, a misplaced file, two files sharing a `uid`, two files claiming one id — and assert the world audit reports the matching construction finding (`parse-error`, `path-mismatch`, `uid-collision`, `id-collision`), audits the remainder, records `corpus-damaged`, makes no drift comparison, and that every read of a mapped address in that corpus refuses with `CorpusDamaged`; assert the receipt evaluator answers `unresolvable` for a receipt naming it. **Negative:** the default open still refuses with `CorpusStateMalformed`; a state identity is never computed over a collected remainder |
```

In `docs/designs/2026-08-04-formal-model-and-claim-calculus-design.md` line 16 change `substrate consolidation (S1–S8)` to `substrate consolidation (S1–S9, S9 added 2026-09-13)`, and after the S8 row (line 933) add:

```markdown
| S9 | an audit judges a damaged corpus: construction faults are findings, the remainder is audited, no state identity is claimed | RF† + PC† |
```

In `python/tests/test_designs_corpus.py` line 38 change `"S": ("S1", "S1a", "S2", "S3", "S4", "S5", "S6", "S7", "S8"),` to `"S": ("S1", "S1a", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9"),`. In `README.md` line 147 change `**195 rows**` to `**196 rows**`.

- [ ] **Step 3: Write the cut document**

Follow `docs/designs/2026-09-10-conformance-cut-24.md` section for section. Header:

```markdown
# Conformance cut 27 — snapshots, import, audit and diagnostics

**Status:** frozen 2026-09-13 before implementation.
**Frozen:** 2026-09-13, before implementation, on `design/world-resolution-slice-3`
**Design:** `../superpowers/specs/2026-09-13-world-resolution-slice-3-design.md`, reviewed three times 2026-09-13
**Numbered after** cut 26 (roadmap concurrency rule 1) and **serialized after** its discharge, which is in the branch ancestry (rule 5).
```

`## 1. What this cut is` — spec §1's first three paragraphs, then cut 5's selection-rule sentence: "The selection rule is cut 5's: a clause is selected only when its source mutation and every named check run inside §2. A row with any unrun arm is partial."

`## 2. The boundary` — `In scope:` bullets at file-and-symbol granularity from this plan's file-structure table; `Out of scope:` bullets: slice 4 (`beliefs-0e523a`: W7); W8 and W8b (retained, unselected; audited at slice 4's discharge; `beliefs-fda0e5`'s repair is on `main`; the view's duplicate-uid refusal is slice 1's invariant, never W8b conformance); R23's rules-store clauses and W8a's `instrument-certification` arm (`contract-cut`); the ledger's "manifest safety" item (unowned, spec §11 item 2); `audit_corpus`'s signature and every read-side function of `world/read.py` other than `validate_receipt`, `_contract_fault` and `_standing`.

`## 3. Selection` — one subsection per row:

```markdown
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
```

`## 4. Accounting` — exactly:

```markdown
Five guarantee rows are read, **3 full/closed** (X5, W13, S9), 2 partial (R23, W8a), and **5 declaration units** carry them: `R23`, `W8a`, `X5`, `W13`, `S9`. W8 and W8b stay retained and unselected (§2); `packaging-remainder` closes with X5 and W8a's packaging arms.
```

`## 5. N2 and acceptance obligations` — numbered as cut 24's: (1) the inventory is exactly the five units, single-homed; (2) every durable arm runs on the certified volume, refusal is an error and never a skip; (3) the runner, quoting `PREFIX_RUNNERS = ("cut26_acceptance.py",)` and `PHASE_MODULES = ("test_world_audit_acceptance.py", "test_n2_cut27.py")`; (4) the 27 declared arms cover every sabotage site: in `world/read.py` (availability evaluated before well-formedness; the coverage comparison narrowed to `coverage.yaml`; the member-subject comparison dropped; `_standing` raising on a damaged carrier), in `world/importing.py` (a refuted receipt admitted; `current` written; log-head records written; the source directory's name trusted; the world-membership check dropped), in `world/audit.py` (the reduction over the audited epoch alone; a malformed receipt folded into the reduction; a carrier that does not read skipped silently; `OSError` escaping the sweep; anchors corroborated against the epoch itself), in `world/view.py` (the strict open kept under `report`; a state identity computed over the remainder; a damaged address served; drift omitted; records captured under a foreign base pin), in `corpus.py` (`_record_findings` run over the live view), in `audit.py` (`CorpusDamaged` escaping the endpoint check; the endpoint resolved corpus-locally; the identifier check keyed on the selected identifier only; recomputation over damage reported as `derivation-malformed`), in `world/registry.py` (two carriers collapsed to one — X5), and in `world/registry.py` again (the corpus root's path digested into the state identity; the coverage declaration taken from the root's name — W13); (5) `test_n2_cut27.py` audits them by the cut-12 pattern with the staleness probe's baseline taken from the tree; (6) prior declarations frozen, no check reclaimed; (7) this document and its declaration inventory pinned by digest before discharge.

`## 6. Second reader` — the spec's three review passes on 2026-09-13 (§12 there): eleven findings, then four gaps and one correction, then two issues. `## 7. Limitations` — spec §11's eight items, one line each.

- [ ] **Step 4: Add the document to the README list and the guide's sources**

In `README.md` add a row after line 96 in the same format: `| \`2026-09-13-conformance-cut-27.md\` | the frozen slice 3 cut: epoch import, epoch audit and query, the world audit over a capture and damaged corpora, X5 and W13 relabels, S9 |`. Bump the stated count of designs by one (the sentence `test_the_readme_states_how_many_designs_there_are` reads; extend `_COUNT_WORDS` in `python/tests/test_designs_corpus.py` if the next number word is missing). In `docs/guide/contracts-and-adoption.md`'s front-matter `sources:` list add `- ../designs/2026-09-13-conformance-cut-27.md`.

- [ ] **Step 5: Run the design-corpus guards**

Run: `cd python && uv run --frozen pytest tests/test_designs_corpus.py -p no:cacheprovider`
Expected: every test passes, including `test_the_readme_states_the_corpus_row_total` at 196.

- [ ] **Step 6: Commit the freeze and pin it**

```bash
git add docs README.md python/tests/test_designs_corpus.py tasks
git commit -m "docs(cut27): freeze conformance cut 27 and mint S9"
git rev-parse HEAD
sha256sum docs/designs/2026-09-13-conformance-cut-27.md
tasks note beliefs-46847c "cut 27 frozen at <sha>, sha256 <digest>"
tasks done <task-1-id> "cut 27 frozen at <sha>; S9 minted"
```
Task 9 pins both values.

---
### Task 2: The evaluator — coverage agreement and the damaged carrier

**Files:**
- Modify: `python/src/beliefs/world/read.py:88-90` (imports), `:360-429` (`_contract_fault`), `:270-320` (the `_contract_fault` call and the `_standing` call in `validate_receipt`), `:432-467` (`_standing`)
- Test: `python/tests/test_world_receipts.py`

**Interfaces:**
- Consumes: `epoch.Epoch.coverage` (sorted `(corpus_id, corpus_state)` pairs), `epoch.Epoch.documents`, `epoch._ReceiptCarrier.document`, `derive.subject_identity`, `read._thawed`, `read._SUBJECT_MEMBERS`, `read._SUBJECT_KEYS`, `corpus._operation_lock_for`, `registry.corpus_state_identity`, `epoch._captured_records`.
- Produces: `_contract_fault(kind, member, receipt, published) -> str | None` (spec decision 9) and `_standing(world, corpus_id, corpus_state, carrier) -> derive.CapturedCorpus | str` — a string is the `unresolvable` detail. Task 3 evaluates through `validate_receipt` unchanged in signature; Task 4 and Task 9 rely on `unresolvable` for a damaged carrier.

- [ ] **Step 1: `tasks start <task-2-id>`, then write the failing evaluator tests**

Append to `python/tests/test_world_receipts.py`, inside `class TestReceiptOutcomes` (the class every arm above lives in):

```python
    def _refuse_availability(self, monkeypatch):
        """Every availability read refuses, so a `malformed` verdict proves the
        order and not only the outcome (spec decision 9)."""
        def refuse(*_args, **_kwargs):
            raise AssertionError("availability consulted before well-formedness")

        monkeypatch.setattr(registry, "corpus_state_identity", refuse)
        monkeypatch.setattr(registry, "_carrier_roots", refuse)
        monkeypatch.setattr(rules, "_locked_resolve_rule_binding", refuse)

    def test_a_receipt_naming_a_narrower_corpus_set_is_malformed_before_availability(self, tmp_path, monkeypatch):
        world, _bindings, _roots, published = published_world(tmp_path, (ALPHA, BETA))
        receipt = document(published, "producer-receipt.yaml")
        receipt["corpus_states"] = [state for state in receipt["corpus_states"] if state["corpus_id"] == ALPHA]
        narrowed = repackage(world, published, {"producer-receipt.yaml": receipt})

        self._refuse_availability(monkeypatch)
        outcome = read.validate_receipt(world, narrowed, "producer")
        assert outcome.outcome == "malformed"
        assert "not the coverage" in outcome.detail

    def test_every_coverage_declaration_must_agree(self, tmp_path, monkeypatch):
        """Snapshot {A, B}; epoch coverage and receipt {A}; subject digest untouched.
        A two-way check passes this carrier — the spec's probe (decision 9)."""
        world, _bindings, _roots, published = published_world(tmp_path, (ALPHA, BETA))
        receipt = document(published, "producer-receipt.yaml")
        receipt["corpus_states"] = [state for state in receipt["corpus_states"] if state["corpus_id"] == ALPHA]
        coverage = document(published, "coverage.yaml")
        coverage["coverage"] = [entry for entry in coverage["coverage"] if entry["corpus_id"] == ALPHA]
        anchors = document(published, "anchors.yaml")
        anchors["corpora"] = [entry for entry in anchors["corpora"] if entry["subject"] == ALPHA]
        skewed = repackage(
            world, published,
            {"producer-receipt.yaml": receipt, "coverage.yaml": coverage, "anchors.yaml": anchors},
        )

        self._refuse_availability(monkeypatch)
        outcome = read.validate_receipt(world, skewed, "producer")
        assert outcome.outcome == "malformed"
        assert "subject declares coverage" in outcome.detail

    def test_a_member_subject_disagreeing_with_its_receipt_is_malformed(self, tmp_path, monkeypatch):
        """R23's literal omission fixture: the snapshot trimmed, the receipt untouched."""
        world, _bindings, _roots, published = published_world(tmp_path, (ALPHA, BETA))
        snapshot = document(published, "producer-snapshot.yaml")
        assert snapshot["producers"], "the sample corpus carries a producer to omit"
        snapshot["producers"] = snapshot["producers"][1:]
        trimmed = repackage(world, published, {"producer-snapshot.yaml": snapshot})

        self._refuse_availability(monkeypatch)
        outcome = read.validate_receipt(world, trimmed, "producer")
        assert outcome.outcome == "malformed"
        assert "producer-snapshot.yaml has identity" in outcome.detail

    def test_the_consistent_omission_is_refuted_at_rebuild(self, tmp_path):
        """R23's reconstruction clause: subject recomputed over the trimmed snapshot."""
        world, _bindings, _roots, published = published_world(tmp_path, (ALPHA, BETA))
        snapshot = document(published, "producer-snapshot.yaml")
        snapshot["producers"] = snapshot["producers"][1:]
        receipt = document(published, "producer-receipt.yaml")
        receipt["subject"] = derive.subject_identity("producer", snapshot)
        omitted = repackage(world, published, {"producer-snapshot.yaml": snapshot, "producer-receipt.yaml": receipt})

        assert read.validate_receipt(world, omitted, "producer").outcome == "refuted"

    def test_a_damaged_carrier_is_unresolvable_rather_than_an_exception(self, tmp_path):
        """Spec decisions 7–8: the hold is the lock-only lookup, the strict attempt
        runs inside it, and `CorpusStateMalformed` becomes an outcome."""
        world, _bindings, roots, published = published_world(tmp_path, (ALPHA, BETA))
        (roots[BETA] / "verification").mkdir(exist_ok=True)
        (roots[BETA] / "verification" / "bad.md").write_text("---\nnot: [a valid record\n---\n", encoding="utf-8")

        outcome = read.validate_receipt(world, published, "producer")
        assert outcome.outcome == "unresolvable"
        assert "cannot be read" in outcome.detail and BETA in outcome.detail
        assert read.validate_receipt(world, published, "coreference-reduction").outcome == "unresolvable"
```

`derive` and `rules` are already imported at the module head (`from beliefs.world import derive, epoch, read, registry, rules`).

- [ ] **Step 2: Run them to verify they fail**

Run: `cd python && uv run --frozen pytest tests/test_world_receipts.py -k "narrower or agree or member_subject or consistent_omission or damaged_carrier"`
Expected: 5 failed — the first three pass availability (`AssertionError: availability consulted`), the fourth returns `validated` or `malformed` depending on the digest, the fifth raises out of `_root_state_for`.

- [ ] **Step 3: Widen `_contract_fault`**

In `python/src/beliefs/world/read.py`, change the signature at line 360 to `def _contract_fault(kind: str, member: str, receipt: epoch._ReceiptCarrier, published: epoch.Epoch) -> str | None:` and, after the existing `if len(set(covered)) != len(covered): return "corpus_states names one corpus twice"` block and before the `key = _SUBJECT_KEYS.get(kind)` block, insert:

```python
    declared = sorted(corpus_id for corpus_id, _state in published.coverage)
    if covered != declared:
        return (
            f"corpus_states names {covered}, not the coverage {declared} this epoch declares; a receipt over a "
            "narrower or wider corpus set is unsound before any corpus is consulted (world §5, well_formed)"
        )
    subject_member = _SUBJECT_MEMBERS.get(kind)
    if subject_member is not None:
        try:
            member_identity = derive.subject_identity(
                kind, _thawed(cast(Mapping[object, object], published.documents[subject_member]))
            )
        except Exception as caught:  # noqa: BLE001 — any refusal here is the same finding
            return f"{subject_member} is not a projection this subject's identity can be taken over: {caught}"
        if member_identity != receipt.subject_identity:
            return (
                f"{subject_member} has identity {member_identity}, not the {receipt.subject_identity} "
                "this receipt names as its subject"
            )
    subject_coverage = _subject_coverage(kind, receipt, published)
    if subject_coverage is not None and subject_coverage != declared:
        return (
            f"the {kind} subject declares coverage {subject_coverage}, not the {declared} this epoch and "
            "receipt declare; the three declarations must agree before availability (world §5)"
        )
```

and add the helper after `_contract_fault`:

```python
def _subject_coverage(kind: str, receipt: epoch._ReceiptCarrier, published: epoch.Epoch) -> list[str] | None:
    """The coverage the subject itself declares, sorted, or `None` for the one
    kind that declares none (the coreference map). A declaration that is not a
    list of text is returned as an impossible marker so the caller reports it."""
    if kind == "producer":
        source: object = published.documents["producer-snapshot.yaml"].get("coverage")
    elif kind == "retraction-enumeration":
        carried = receipt.document.get("enumeration")
        source = carried.get("coverage") if isinstance(carried, Mapping) else None
    elif kind == "certification-enumeration":
        carried = receipt.document.get("inventory")
        source = carried.get("coverage") if isinstance(carried, Mapping) else None
    else:
        return None
    if not isinstance(source, (list, tuple)) or not all(type(member) is str for member in source):
        return ["<not a coverage declaration>"]
    return sorted(source)
```

Update the one call site in `validate_receipt`: `fault = _contract_fault(kind, member, receipt, published)`.

- [ ] **Step 4: `_standing` through the lock-only lookup**

Replace `_standing`'s body (keep the docstring, add one paragraph: "A carrier that cannot be read cannot stand at any named state: `unresolvable`, decided inside the same hold, on the unreadable-manifest precedent above. The hold is the lock-only lookup, because `_root_state_for` constructs a strict corpus before the hold and would raise on exactly the damaged root."):

```python
def _standing(world: registry.World, corpus_id: str, corpus_state: str, carrier: Path) -> derive.CapturedCorpus | str:
    with _operation_lock_for(carrier).capture():
        try:
            before = registry.corpus_state_identity(carrier)
            if before != corpus_state:
                return f"this corpus no longer stands at the state {corpus_state} the receipt named"
            records = epoch._captured_records(carrier)
            after = registry.corpus_state_identity(carrier)
        except CorpusStateMalformed as caught:
            return f"this corpus cannot be read, so the named state {corpus_state} cannot be reached: {caught}"
    if before != after:
        raise CaptureDrift(
            f"{corpus_id}: {carrier}: the corpus state moved inside a validation hold "
            f"({before} -> {after}); no rebuild is reported from a corpus that did not hold still"
        )
    return derive.CapturedCorpus(corpus_id, before, records)
```

Change the import at line 90 to `from beliefs.corpus import ReadView, _operation_lock_for` (drop `_root_state_for` if nothing else in the module uses it — ruff says), add `CorpusStateMalformed` to the `beliefs.errors` import, and in `validate_receipt` replace

```python
        standing = _standing(world, corpus_id, corpus_state, carriers[0])
        if standing is None:
            return derive.ReceiptOutcome(
                kind,
                "unresolvable",
                f"{corpus_id}: {carriers[0]}: this corpus no longer stands at the state "
                f"{corpus_state} the receipt named",
            )
        captured.append(standing)
```

with

```python
        standing = _standing(world, corpus_id, corpus_state, carriers[0])
        if isinstance(standing, str):
            return derive.ReceiptOutcome(kind, "unresolvable", f"{corpus_id}: {carriers[0]}: {standing}")
        captured.append(standing)
```

`world` is now unused inside `_standing`; keep the parameter (the signature is cited by tests) and consume it with `del world` on the first line, or drop it and update the one call — either is fine; pick the drop.

- [ ] **Step 5: Run the receipt suite and the frozen guards**

Run: `cd python && uv run --frozen pytest tests/test_world_receipts.py tests/test_world_read.py tests/test_arm_staleness.py tests/test_frozen_guards.py`
Expected: all pass. If `test_arm_staleness.py` reports a cut 7 arm whose `before` no longer matches (`_standing`'s old body or `_contract_fault`'s signature line), record it in `python/tests/cited_not_run.py`'s `stale_arms` with today's date and the reason, and rerun.

- [ ] **Step 6: Lint, typecheck, commit**

```bash
cd python && uv run --frozen ruff check . && uv run --frozen pyright
cd .. && tasks note <task-2-id> "evaluator: three-way coverage agreement and member-subject checks are malformed; a damaged carrier is unresolvable through the lock-only hold"
tasks done <task-2-id> "evaluator widened (spec decisions 7-9)"
git add python/src/beliefs/world/read.py python/tests tasks
git commit -m "feat(world): receipt well-formedness inspects the snapshot and a damaged carrier is unresolvable"
```

---
### Task 3: The epoch import act

**Files:**
- Create: `python/src/beliefs/world/importing.py`, `python/tests/test_world_import_epoch.py`
- Modify: `python/src/beliefs/errors.py` (after `EpochUnknown`, line 122), `python/src/beliefs/world/epoch.py:615-664` (`_locked_open_epoch` → `_carrier_epoch`), `python/src/beliefs/world/__init__.py` (re-exports and `__all__`)

**Interfaces:**
- Consumes: `epoch._carrier_members`, `epoch.packaging_identity_of`, `epoch.EPOCH_MEMBERS`, `epoch.RECEIPT_KINDS`, `epoch._emptied`, `epoch._locked_open_epoch`, `registry._locked_barrier`, `World.authority.require`, `World._executor_factory`, `read.validate_receipt` (Task 2), `corpus.Finding`.
- Produces: `epoch._carrier_epoch(members: Mapping[str, bytes], packaging_identity: str) -> Epoch`; `importing.import_epoch(world, source: Path) -> EpochImportReport`; `EpochImportReport(packaging_identity, outcomes, findings, written)`; `errors.EpochImportRefused(reason, message, *, outcomes=())` with `reason` in `("malformed-carrier", "foreign-world", "malformed-receipt", "refuted-receipt")`. Task 4 reuses `_carrier_epoch` indirectly through the loader; Task 9's arms import through `import_epoch`.

- [ ] **Step 1: `tasks start <task-3-id>`, then write the failing tests**

Create `python/tests/test_world_import_epoch.py`:

```python
"""Explicit import of an epoch carrier (slice 3 design §3)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from authority import FULL
from nodes.core.write_plan import DefaultExecutor
from test_world_build import ALPHA, BETA, ChainHeads
from test_world_receipts import document, hold_shipped, published_world, sample_corpora, world_over

from beliefs.errors import EpochImportRefused, EpochUnknown, PermitExceeded
from beliefs.permit import READ_ONLY
from beliefs.world import derive, epoch, read, registry
from beliefs.world.importing import import_epoch


def exported(published: epoch.Epoch, into: Path, changes: dict[str, object] | None = None) -> Path:
    """A carrier copy outside any world root, edited member by member."""
    members = dict(published.members)
    for member, edited in (changes or {}).items():
        members[member] = yaml.safe_dump(edited, sort_keys=True, allow_unicode=True).encode("utf-8")
    into.mkdir(parents=True)
    for member, content in members.items():
        (into / member).write_bytes(content)
    return into


def replica_world(tmp_path: Path, roots: dict[str, Path], *, hold: bool = True) -> registry.World:
    """A second world of the same id over the same corpora, publishing nothing."""
    world = world_over(tmp_path, roots, name="replica")
    if hold:
        hold_shipped(world)
    return world


def epochs_of(world: registry.World) -> set[str]:
    base = world.config.world_root / "epochs"
    return {entry.name for entry in base.iterdir()} if base.exists() else set()


def test_a_validated_carrier_is_admitted_without_a_pointer_or_a_log_head_record(tmp_path):
    world, _bindings, roots, published = published_world(tmp_path, (ALPHA, BETA))
    replica = replica_world(tmp_path, roots)
    source = exported(published, tmp_path / "export")

    report = import_epoch(replica, source)

    assert report.written is True
    assert report.packaging_identity == published.packaging_identity
    assert {kind: outcome.outcome for kind, outcome in report.outcomes.items()} == dict.fromkeys(
        epoch.RECEIPT_KINDS.values(), "validated"
    )
    assert report.findings == ()
    assert read.open_epoch(replica, published.packaging_identity).members == published.members
    with pytest.raises(EpochUnknown):
        read.current_epoch(replica)
    assert registry._scan_registry(replica.config.world_root).log_heads == ()
    assert epochs_of(replica) == {published.packaging_identity}


def test_a_second_import_of_the_same_carrier_writes_nothing(tmp_path):
    _world, _bindings, roots, published = published_world(tmp_path, (ALPHA, BETA))
    replica = replica_world(tmp_path, roots)
    source = exported(published, tmp_path / "export")
    import_epoch(replica, source)
    before = {p: p.stat().st_mtime_ns for p in (replica.config.world_root / "epochs").rglob("*")}

    report = import_epoch(replica, source)

    assert report.written is False
    assert {p: p.stat().st_mtime_ns for p in (replica.config.world_root / "epochs").rglob("*")} == before


def test_a_carrier_missing_a_member_is_refused_as_malformed_with_nothing_written(tmp_path):
    _world, _bindings, roots, published = published_world(tmp_path, (ALPHA, BETA))
    replica = replica_world(tmp_path, roots)
    source = exported(published, tmp_path / "export")
    (source / "producer-receipt.yaml").unlink()

    with pytest.raises(EpochImportRefused) as refused:
        import_epoch(replica, source)
    assert refused.value.reason == "malformed-carrier"
    assert epochs_of(replica) == set()


def test_a_carrier_of_another_world_is_refused(tmp_path):
    _world, _bindings, roots, published = published_world(tmp_path, (ALPHA, BETA))
    other = world_over(tmp_path, roots, name="other", world_id="e" * 32)
    hold_shipped(other)
    source = exported(published, tmp_path / "export")

    with pytest.raises(EpochImportRefused) as refused:
        import_epoch(other, source)
    assert refused.value.reason == "foreign-world"
    assert epochs_of(other) == set()


def test_a_malformed_receipt_refuses_before_any_write_and_names_every_kind(tmp_path):
    _world, _bindings, roots, published = published_world(tmp_path, (ALPHA, BETA))
    replica = replica_world(tmp_path, roots)
    receipt = document(published, "producer-receipt.yaml")
    receipt["corpus_states"] = receipt["corpus_states"][:1]
    source = exported(published, tmp_path / "export", {"producer-receipt.yaml": receipt})

    with pytest.raises(EpochImportRefused) as refused:
        import_epoch(replica, source)
    assert refused.value.reason == "malformed-receipt"
    assert [outcome.kind for outcome in refused.value.outcomes] == ["producer"]
    assert epochs_of(replica) == set()


def test_a_refuted_receipt_refuses_before_any_write(tmp_path):
    _world, _bindings, roots, published = published_world(tmp_path, (ALPHA, BETA))
    replica = replica_world(tmp_path, roots)
    snapshot = document(published, "producer-snapshot.yaml")
    snapshot["producers"] = snapshot["producers"][1:]
    receipt = document(published, "producer-receipt.yaml")
    receipt["subject"] = derive.subject_identity("producer", snapshot)
    source = exported(
        published, tmp_path / "export", {"producer-snapshot.yaml": snapshot, "producer-receipt.yaml": receipt}
    )

    with pytest.raises(EpochImportRefused) as refused:
        import_epoch(replica, source)
    assert refused.value.reason == "refuted-receipt"
    assert epochs_of(replica) == set()


def test_an_unresolvable_receipt_is_admitted_with_a_finding_and_no_stored_verdict(tmp_path):
    _world, _bindings, roots, published = published_world(tmp_path, (ALPHA, BETA))
    only_alpha = replica_world(tmp_path, {ALPHA: roots[ALPHA]})
    source = exported(published, tmp_path / "export")

    report = import_epoch(only_alpha, source)

    assert report.written is True
    assert all(outcome.outcome == "unresolvable" for outcome in report.outcomes.values())
    assert [finding.code for finding in report.findings] == ["receipt-unresolvable"] * 4
    carrier = only_alpha.config.world_root / "epochs" / published.packaging_identity
    assert {p.name for p in carrier.iterdir()} == set(epoch.EPOCH_MEMBERS)


def test_the_permit_is_required_before_the_carrier_is_read(tmp_path):
    _world, _bindings, roots, published = published_world(tmp_path, (ALPHA, BETA))
    reader = registry.World(
        registry.WorldConfig(tmp_path / "reader", "f" * 32, tuple(roots.values())),
        DefaultExecutor,
        chain_head=ChainHeads(),
        corpus_executor_factory=DefaultExecutor,
        authority=READ_ONLY,
    )
    source = exported(published, tmp_path / "export")
    (source / "coverage.yaml").unlink()  # unreadable, but the permit refuses first

    with pytest.raises(PermitExceeded):
        import_epoch(reader, source)
```

If `beliefs.permit` spells the read-only authority differently, use the name `root.open_world_read` imports (grep `READ_ONLY` in `python/src/beliefs/root.py`).

- [ ] **Step 2: Run them to verify they fail**

Run: `cd python && uv run --frozen pytest tests/test_world_import_epoch.py`
Expected: collection error — `beliefs.world.importing` does not exist.

- [ ] **Step 3: The error class**

In `python/src/beliefs/errors.py`, after `EpochUnknown` (line 122):

```python
class EpochImportRefused(ScienceError):
    """An epoch carrier was not admitted into `epochs/` (slice 3 design §3).

    One class with a closed reason set rather than four, because a caller's
    response is the same — the carrier is not admitted — and the reason is
    what it reports. `outcomes` carries the offending receipt outcomes for the
    two receipt reasons and is empty otherwise.
    """

    def __init__(
        self,
        reason: Literal["malformed-carrier", "foreign-world", "malformed-receipt", "refuted-receipt"],
        message: str,
        *,
        outcomes: tuple["ReceiptOutcome", ...] = (),
    ) -> None:
        super().__init__(message)
        self.reason = reason
        self.outcomes = outcomes
```

and under the existing `if TYPE_CHECKING:` block add `from beliefs.world.derive import ReceiptOutcome`.

- [ ] **Step 4: Factor `_carrier_epoch` out of the loader**

In `python/src/beliefs/world/epoch.py`, replace lines 640–663 of `_locked_open_epoch` (from `members = _carrier_members(directory)` to the `return Epoch(...)`) with:

```python
    members = _carrier_members(directory)
    recomputed = packaging_identity_of(members)
    if recomputed != packaging_identity:
        raise EpochMalformed(
            f"{directory}: the members recompute the packaging identity {recomputed}, "
            "so this directory does not hold the epoch its name claims"
        )
    return _carrier_epoch(members, packaging_identity)
```

and add, directly after `_locked_open_epoch`:

```python
def _carrier_epoch(members: Mapping[str, bytes], packaging_identity: str) -> Epoch:
    """One carrier's eleven members, parsed into an `Epoch` value.

    Shared by the locked loader and the explicit import: the loader has
    already checked the directory's name against the recomputed identity, and
    the import computes the identity from the bytes and claims nothing else.
    Every parse failure is `EpochMalformed`, as the loader raises it.
    """
    documents: dict[str, Mapping[object, object]] = {}
    receipts: dict[str, _ReceiptCarrier] = {}
    for member, content in members.items():
        if member in RECEIPT_KINDS:
            receipts[member] = _parse_receipt(packaging_identity, member, content)
            documents[member] = receipts[member].document
        else:
            documents[member] = _parse_member(packaging_identity, member, content)
    return Epoch(
        packaging_identity,
        members,
        documents,
        receipts,
        _covered_states(documents["coverage.yaml"]),
        _corpus_anchors(documents["anchors.yaml"]),
        _anchor(cast(Mapping[object, object], documents["anchors.yaml"]["world"])),
    )
```

Run `uv run --frozen pytest tests/test_world_epoch.py` — every carrier arm still passes (the identity check now precedes parsing; both refuse `EpochMalformed`).

- [ ] **Step 5: The import module**

Create `python/src/beliefs/world/importing.py`:

```python
"""Explicit import of an epoch carrier (slice 3 design §3).

The one effectful caller of the receipt evaluator beside publication. It
admits a carrier of *this* world into ``epochs/`` under its recomputed
packaging identity, create-only, after every receipt has been evaluated: a
``malformed`` or ``refuted`` receipt refuses with nothing written, an
``unresolvable`` one admits the carrier with a finding, and no verdict is
stored anywhere. It touches neither ``current`` nor the registry — a build's
log-head records assert an anchoring the build observed, and an import
observed nothing.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import cast

from nodes.core.write_plan import CreateOp

from beliefs.corpus import Finding
from beliefs.errors import EpochImportRefused, EpochMalformed
from beliefs.world import derive, epoch, read, registry

__all__ = ["EpochImportReport", "import_epoch"]


@dataclass(frozen=True)
class EpochImportReport:
    """What one import decided: every receipt's outcome, the findings an
    admitted-but-unchecked receipt leaves, and whether bytes were written."""

    packaging_identity: str
    outcomes: Mapping[derive.ReceiptKind, derive.ReceiptOutcome]
    findings: tuple[Finding, ...]
    written: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "outcomes", MappingProxyType(dict(self.outcomes)))


def import_epoch(world: registry.World, source: Path) -> EpochImportReport:
    """Admit the carrier at `source` into this world's ``epochs/``, or refuse.

    Order: the permit; the carrier's bytes, read once and parsed as the
    loader parses them, with the packaging identity recomputed and the
    directory's name never consulted; world membership; every receipt through
    `validate_receipt`, all four before the decision so the report names
    every fault; then one hold of the world lock for the retained-set check
    and the plan of eleven creates. Evaluation runs outside the lock, as
    derivation does in `build_epoch`.
    """
    world.authority.require("epoch")
    try:
        members = epoch._carrier_members(Path(source))
        packaging_identity = epoch.packaging_identity_of(members)
        carrier = epoch._carrier_epoch(members, packaging_identity)
    except (EpochMalformed, OSError) as caught:
        raise EpochImportRefused("malformed-carrier", f"{source}: the carrier does not read: {caught}") from caught
    if carrier.world_anchor.subject != world.config.world_id:
        raise EpochImportRefused(
            "foreign-world",
            f"{packaging_identity}: epoch belongs to world {carrier.world_anchor.subject}, not {world.config.world_id}",
        )
    kinds = cast(tuple[derive.ReceiptKind, ...], tuple(epoch.RECEIPT_KINDS.values()))
    outcomes = {kind: read.validate_receipt(world, carrier, kind) for kind in kinds}
    for reason, outcome in (("malformed-receipt", "malformed"), ("refuted-receipt", "refuted")):
        offending = tuple(verdict for verdict in outcomes.values() if verdict.outcome == outcome)
        if offending:
            raise EpochImportRefused(
                cast("str", reason),  # pyright: the literal set is the class's
                f"{packaging_identity}: {len(offending)} receipt(s) {outcome}: "
                + "; ".join(f"{verdict.kind}: {verdict.detail}" for verdict in offending),
                outcomes=offending,
            )
    findings = tuple(
        Finding(
            severity="warning",
            code="receipt-unresolvable",
            ref=packaging_identity,
            detail=f"{verdict.kind}: {verdict.detail}",
            message=f"{packaging_identity}: the {verdict.kind} receipt cannot be checked here and enters unchecked",
        )
        for verdict in outcomes.values()
        if verdict.outcome == "unresolvable"
    )
    with registry._locked_barrier(world) as world_root:
        directory = world_root / "epochs" / packaging_identity
        if directory.is_symlink() or (directory.exists() and not (directory.is_dir() and epoch._emptied(directory))):
            retained = epoch._locked_open_epoch(world_root, packaging_identity)
            assert dict(retained.members) == dict(members)  # the loader recomputes the identity, so this holds
            written = False
        else:
            world._executor_factory(world_root).execute(
                [CreateOp(f"epochs/{packaging_identity}/{member}", members[member]) for member in epoch.EPOCH_MEMBERS]
            )
            written = True
    return EpochImportReport(packaging_identity, outcomes, findings, written)
```

If pyright rejects the `cast("str", reason)` on the literal parameter, type `reason` in the loop tuple as `Literal[...]` pairs instead; either way no `# type: ignore`.

In `python/src/beliefs/world/__init__.py` add, after the `view` import line, `from beliefs.world.importing import EpochImportReport, import_epoch`, and add `"EpochImportReport"` and `"import_epoch"` to `__all__` in sorted position. Run `uv run --frozen pytest tests/test_world_build.py::test_each_world_module_imports_first_without_a_cycle` — it parametrizes over the package's modules; add `"importing"` to its module list if the list is literal.

- [ ] **Step 6: Run, lint, commit**

Run: `cd python && uv run --frozen pytest tests/test_world_import_epoch.py tests/test_world_epoch.py tests/test_world_receipts.py`
Expected: all pass.

```bash
uv run --frozen ruff check . && uv run --frozen pyright
cd .. && tasks note <task-3-id> "import_epoch: create-only, no pointer, no log-head records; malformed/refuted refuse before any write; unresolvable admits with a finding"
tasks done <task-3-id> "epoch import act (spec §3)"
git add python/src/beliefs tasks python/tests/test_world_import_epoch.py
git commit -m "feat(world): explicit import of an epoch carrier through the receipt evaluator"
```

---
### Task 4: The epoch audit and the snapshot-state query

**Files:**
- Create: `python/src/beliefs/world/audit.py`, `python/tests/test_world_epoch_audit.py`
- Modify: `python/src/beliefs/world/epoch.py` (add `_locked_retained_directories` after `_retained_identities_locked`, line 1770), `python/src/beliefs/world/__init__.py`

**Interfaces:**
- Consumes: `registry._locked_barrier`, `registry._scan_registry` (→ `RegistryView.log_heads`), `epoch._locked_open_epoch`, `epoch._emptied`, `epoch._PACKAGING_IDENTITY`, `epoch.CURRENT_POINTER`, `epoch.Epoch.anchors` (`_Anchor(subject, genesis_digest, head_digest)`), `epoch.Epoch.receipts[member].subject_identity`, `read.validate_receipt`, `read._member_for`, `anchors.CorpusSubject`, `corpus.Finding`.
- Produces: `epoch._locked_retained_directories(world_root) -> tuple[tuple[str, str | None], ...]` (name, refusal-or-None); `audit.SNAPSHOT_STATES`, `audit.SnapshotVerdict(kind, subject_identity, state, receipts, unreadable)`, `audit.EpochAudit(receipts, snapshots, findings)`, `audit.audit_epochs(world) -> EpochAudit`, `audit.snapshot_state(world, kind, subject_identity) -> SnapshotVerdict`. Task 7 calls `audit_epochs`-shaped receipt findings for the audited epoch; Task 9's arms name all of these.

- [ ] **Step 1: `tasks start <task-4-id>`, then write the failing tests**

Create `python/tests/test_world_epoch_audit.py`:

```python
"""The epoch audit and the snapshot-state query (slice 3 design §4)."""

from __future__ import annotations

from pathlib import Path

import pytest
from test_world_build import ALPHA, BETA
from test_world_import_epoch import exported, replica_world
from test_world_receipts import document, hold_shipped, publish, published_world, repackage

from beliefs.errors import EpochMalformed
from beliefs.world import derive, epoch, registry
from beliefs.world.audit import EpochAudit, SnapshotVerdict, audit_epochs, snapshot_state

KINDS = tuple(epoch.RECEIPT_KINDS.values())


def codes(findings) -> list[str]:
    return sorted(finding.code for finding in findings)


def inventory(world: registry.World) -> dict[str, bytes]:
    return {str(p.relative_to(world.config.world_root)): p.read_bytes() for p in world.config.world_root.rglob("*") if p.is_file()}


def test_a_published_world_audits_clean(tmp_path):
    world, _bindings, _roots, published = published_world(tmp_path, (ALPHA, BETA))

    audit = audit_epochs(world)

    assert isinstance(audit, EpochAudit)
    assert [(name, kind, outcome.outcome) for name, kind, outcome in audit.receipts] == [
        (published.packaging_identity, kind, "validated") for kind in KINDS
    ]
    assert [(verdict.kind, verdict.state, verdict.unreadable) for verdict in audit.snapshots] == [
        (kind, "checked", ()) for kind in sorted(KINDS)
    ]
    assert audit.findings == ()


def test_a_malformed_receipt_is_reported_and_excluded_from_the_reduction(tmp_path):
    """W8a: raw-written past the boundary, `malformed` under audit and under the
    query, a finding naming the pair, and a validating receipt beside it keeps
    the snapshot `checked` with the finding still emitted."""
    world, _bindings, _roots, published = published_world(tmp_path, (ALPHA, BETA))
    receipt = document(published, "producer-receipt.yaml")
    receipt["rule_identity"] = "v1"  # a bare version string, not an identity
    forged = repackage(world, published, {"producer-receipt.yaml": receipt})

    audit = audit_epochs(world)

    assert [(n, o.outcome) for n, k, o in audit.receipts if k == "producer"] == sorted(
        [(published.packaging_identity, "validated"), (forged.packaging_identity, "malformed")]
    )
    producer = next(v for v in audit.snapshots if v.kind == "producer")
    assert producer.state == "checked"
    assert [(f.code, f.ref) for f in audit.findings] == [("receipt-malformed", forged.packaging_identity)]
    subject = published.receipts["producer-receipt.yaml"].subject_identity
    assert subject is not None
    assert snapshot_state(world, "producer", subject).state == "checked"


def test_the_two_roads_to_unchecked_are_distinguishable(tmp_path):
    _world, _bindings, roots, published = published_world(tmp_path, (ALPHA, BETA))
    receipt = document(published, "producer-receipt.yaml")
    receipt["rule_identity"] = "v1"
    all_malformed = replica_world(tmp_path, roots)
    exported(published, all_malformed.config.world_root / "epochs" / "0" * 64, {"producer-receipt.yaml": receipt})
    merely_absent = replica_world(tmp_path / "absent", {ALPHA: roots[ALPHA]})
    exported(published, merely_absent.config.world_root / "epochs" / published.packaging_identity)

    forged = audit_epochs(all_malformed)
    absent = audit_epochs(merely_absent)

    # The raw-written carrier's name is not its identity, so it is a malformed carrier — spec §4.2.
    assert codes(forged.findings) == ["epoch-malformed"]
    assert absent.snapshots and all(v.state == "unchecked" for v in absent.snapshots)
    assert set(codes(absent.findings)) == {"anchor-uncorroborated", "receipt-unresolvable"}
    assert codes(absent.findings).count("receipt-unresolvable") == 4
    assert "receipt-malformed" not in codes(absent.findings)


def test_an_all_malformed_snapshot_is_unchecked_with_a_finding_per_pair(tmp_path):
    _world, _bindings, roots, published = published_world(tmp_path, (ALPHA, BETA))
    receipt = document(published, "producer-receipt.yaml")
    receipt["rule_identity"] = "v1"
    replica = replica_world(tmp_path, roots)
    members = dict(published.members)
    import yaml

    members["producer-receipt.yaml"] = yaml.safe_dump(receipt, sort_keys=True, allow_unicode=True).encode("utf-8")
    identity = epoch.packaging_identity_of(members)
    directory = replica.config.world_root / "epochs" / identity
    directory.mkdir(parents=True)
    for member, content in members.items():
        (directory / member).write_bytes(content)

    audit = audit_epochs(replica)

    producer = next(v for v in audit.snapshots if v.kind == "producer" and identity in dict(v.receipts))
    assert producer.state == "unchecked"
    assert ("receipt-malformed", identity) in [(f.code, f.ref) for f in audit.findings]


def test_an_unreadable_carrier_is_a_finding_and_the_next_carrier_is_still_evaluated(tmp_path, monkeypatch):
    world, _bindings, _roots, published = published_world(tmp_path, (ALPHA, BETA))
    receipt = document(published, "producer-receipt.yaml")
    receipt["rule_identity"] = "v1"
    second = repackage(world, published, {"producer-receipt.yaml": receipt})
    (world.config.world_root / "epochs" / "not-an-identity").mkdir()
    (world.config.world_root / "epochs" / "not-an-identity" / "x").write_text("x")
    original_members = epoch._carrier_members

    def unreadable(directory: Path):
        if directory.name == published.packaging_identity:
            raise PermissionError(f"{directory}: read refused")
        return original_members(directory)

    monkeypatch.setattr(epoch, "_carrier_members", unreadable)
    original_emptied = epoch._emptied

    def unlistable(directory: Path):
        if directory.name == second.packaging_identity:
            raise PermissionError(f"{directory}: listing refused")  # the walk's own read, before the loader
        return original_emptied(directory)

    monkeypatch.setattr(epoch, "_emptied", unlistable)
    third = repackage(world, published, {"producer-receipt.yaml": {**receipt, "rule_identity": "v2"}})  # distinct bytes, so a third carrier

    audit = audit_epochs(world)

    assert [f.ref for f in audit.findings if f.code == "epoch-malformed"] == sorted(
        ["not-an-identity", published.packaging_identity, second.packaging_identity]
    )
    assert {n for n, _k, _o in audit.receipts} == {third.packaging_identity}
    subject = published.receipts["producer-receipt.yaml"].subject_identity
    assert subject is not None
    verdict = snapshot_state(world, "producer", subject)
    assert isinstance(verdict, SnapshotVerdict)
    assert published.packaging_identity in " ".join(verdict.unreadable)


def test_a_consistent_omission_is_contradicted_under_its_own_subject(tmp_path):
    world, _bindings, _roots, published = published_world(tmp_path, (ALPHA, BETA))
    snapshot = document(published, "producer-snapshot.yaml")
    snapshot["producers"] = snapshot["producers"][1:]
    receipt = document(published, "producer-receipt.yaml")
    receipt["subject"] = derive.subject_identity("producer", snapshot)
    omitted = repackage(world, published, {"producer-snapshot.yaml": snapshot, "producer-receipt.yaml": receipt})

    audit = audit_epochs(world)

    states = {v.subject_identity: v.state for v in audit.snapshots if v.kind == "producer"}
    assert states[receipt["subject"]] == "contradicted"
    assert states[published.receipts["producer-receipt.yaml"].subject_identity] == "checked"
    assert ("snapshot-contradicted", receipt["subject"]) in [(f.code, f.ref) for f in audit.findings]
    assert ("receipt-refuted", omitted.packaging_identity) in [(f.code, f.ref) for f in audit.findings]


def test_an_imported_carriers_anchors_are_uncorroborated_until_a_build_records_the_same_heads(tmp_path):
    from beliefs.world.importing import import_epoch

    _world, _bindings, roots, published = published_world(tmp_path, (ALPHA, BETA))
    replica = replica_world(tmp_path, roots)
    import_epoch(replica, exported(published, tmp_path / "export"))

    before = audit_epochs(replica)
    assert sorted(f.detail for f in before.findings if f.code == "anchor-uncorroborated") == sorted([ALPHA, BETA])

    publish(replica, (ALPHA, BETA), hold_shipped(replica))  # same roots, so the stand-in heads agree
    after = audit_epochs(replica)
    assert "anchor-uncorroborated" not in codes(after.findings)


def test_the_audit_and_the_query_write_nothing(tmp_path):
    world, _bindings, _roots, published = published_world(tmp_path, (ALPHA, BETA))
    before = inventory(world)
    subject = published.receipts["producer-receipt.yaml"].subject_identity
    assert subject is not None

    audit_epochs(world)
    snapshot_state(world, "producer", subject)

    assert inventory(world) == before


def test_a_symlinked_epochs_directory_still_refuses(tmp_path):
    world, _bindings, _roots, _published = published_world(tmp_path, (ALPHA, BETA))
    base = world.config.world_root / "epochs"
    real = base.rename(tmp_path / "moved-epochs")
    base.symlink_to(real)

    with pytest.raises(EpochMalformed):
        audit_epochs(world)
```

`test_an_all_malformed_snapshot_is_unchecked_with_a_finding_per_pair` dumps its edited receipt inline because it needs the carrier written under its *recomputed* identity (so the loader opens it) with a malformed receipt inside; move `import yaml` to the module head.

- [ ] **Step 2: Run them to verify they fail**

Run: `cd python && uv run --frozen pytest tests/test_world_epoch_audit.py`
Expected: collection error — `beliefs.world.audit` does not exist.

- [ ] **Step 3: The name-only walk**

In `python/src/beliefs/world/epoch.py`, after `_retained_identities_locked` (line 1770):

```python
def _locked_retained_directories(world_root: Path) -> tuple[tuple[str, str | None], ...]:
    """Every entry beneath ``epochs/`` an audit must account for, by name.

    The caller holds the world lock. Unlike `_retained_receipt_bindings_locked`,
    this reads no carrier: an audit that refused on the first damaged carrier
    could not report it (slice 3 design decision 4). Each pair is a directory
    name and `None` for an entry the loader may open, or the refusal the walk
    itself can state — a symlink, a file, a name that is not a packaging
    identity. `current` and emptied directories (§9's nonsemantic residue) are
    skipped. The ``epochs/`` directory itself being a symlink or not a
    directory still raises `EpochMalformed`: that is the world, not a carrier.
    """
    base = Path(world_root) / "epochs"
    if base.is_symlink():
        raise EpochMalformed(f"{base}: the epochs directory is a symbolic link")
    if not base.exists():
        return ()
    if not base.is_dir():
        raise EpochMalformed(f"{base}: the epochs directory is not a directory")
    entries: list[tuple[str, str | None]] = []
    for entry in sorted(base.iterdir()):
        if entry.name == CURRENT_POINTER:
            continue
        try:
            if entry.is_symlink() or not entry.is_dir() or not _PACKAGING_IDENTITY.fullmatch(entry.name):
                entries.append((entry.name, f"{entry}: nothing but epoch carriers and {CURRENT_POINTER!r} lives here"))
                continue
            if _emptied(entry):
                continue
        except OSError as caught:  # an entry the process cannot stat or list is unjudged, not a stop
            entries.append((entry.name, f"{entry}: cannot be read: {caught}"))
            continue
        entries.append((entry.name, None))
    return tuple(entries)
```

- [ ] **Step 4: The audit module**

Create `python/src/beliefs/world/audit.py`:

```python
"""The epoch audit and the snapshot-state query (slice 3 design §4).

Both share the receipt evaluator with the import and write nothing. The
audit sweeps every retained epoch; the query answers one subject. A
snapshot's state reduces over every well-formed receipt naming it across the
retained set: `checked` if any validated, else `contradicted` if any refuted,
else `unchecked`. A malformed receipt is reported and never reduced, so the
two roads to `unchecked` stay apart.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal, cast

from beliefs.corpus import Finding
from beliefs.errors import EpochMalformed
from beliefs.world import anchors, derive, epoch, read, registry

__all__ = ["SNAPSHOT_STATES", "EpochAudit", "SnapshotVerdict", "audit_epochs", "snapshot_state"]

SNAPSHOT_STATES: tuple[str, ...] = ("checked", "contradicted", "unchecked")
SnapshotState = Literal["checked", "contradicted", "unchecked"]
_KINDS = cast(tuple[derive.ReceiptKind, ...], tuple(epoch.RECEIPT_KINDS.values()))


@dataclass(frozen=True)
class SnapshotVerdict:
    kind: derive.ReceiptKind
    subject_identity: str
    state: SnapshotState
    receipts: tuple[tuple[str, derive.ReceiptOutcome], ...]
    unreadable: tuple[str, ...]


@dataclass(frozen=True)
class EpochAudit:
    receipts: tuple[tuple[str, derive.ReceiptKind, derive.ReceiptOutcome], ...]
    snapshots: tuple[SnapshotVerdict, ...]
    findings: tuple[Finding, ...]


def _reduce(outcomes: list[derive.ReceiptOutcome]) -> SnapshotState:
    well_formed = [outcome for outcome in outcomes if outcome.outcome != "malformed"]
    if any(outcome.outcome == "validated" for outcome in well_formed):
        return "checked"
    if any(outcome.outcome == "refuted" for outcome in well_formed):
        return "contradicted"
    return "unchecked"


def _retained(world: registry.World) -> tuple[Mapping[str, epoch.Epoch], tuple[tuple[str, str], ...], registry.RegistryView]:
    """Under one hold: every retained carrier the loader opens, the ones it
    cannot (name, refusal), and the registry scan. Released before any corpus
    is touched, as `validate_receipt` releases it."""
    opened: dict[str, epoch.Epoch] = {}
    unreadable: list[tuple[str, str]] = []
    with registry._locked_barrier(world) as world_root:
        view = registry._scan_registry(world_root)
        for name, refusal in epoch._locked_retained_directories(world_root):
            if refusal is not None:
                unreadable.append((name, refusal))
                continue
            try:
                opened[name] = epoch._locked_open_epoch(world_root, name)
            except (EpochMalformed, OSError) as caught:
                unreadable.append((name, str(caught)))
    return opened, tuple(unreadable), view


def _receipt_finding(name: str, outcome: derive.ReceiptOutcome) -> Finding | None:
    if outcome.outcome == "malformed":
        return Finding("error", "receipt-malformed", name, f"{outcome.kind}: {outcome.detail}", f"{name}: the {outcome.kind} receipt violates its contract: {outcome.detail}")
    if outcome.outcome == "refuted":
        return Finding("error", "receipt-refuted", name, f"{outcome.kind}: {outcome.detail}", f"{name}: the {outcome.kind} receipt is refuted by reconstruction; a rebuild (build_epoch) publishes the correction: {outcome.detail}")
    if outcome.outcome == "unresolvable":
        return Finding("warning", "receipt-unresolvable", name, f"{outcome.kind}: {outcome.detail}", f"{name}: the {outcome.kind} receipt cannot be checked in this checkout: {outcome.detail}")
    return None


def _anchor_findings(opened: Mapping[str, epoch.Epoch], view: registry.RegistryView) -> list[Finding]:
    recorded = {(record.subject, record.genesis, record.head) for record in view.log_heads}
    findings: list[Finding] = []
    for name in sorted(opened):
        for anchor in opened[name].anchors:
            if (anchors.CorpusSubject(anchor.subject), anchor.genesis_digest, anchor.head_digest) not in recorded:
                findings.append(Finding("warning", "anchor-uncorroborated", name, anchor.subject, f"{name}: no registry log-head record carries the heads this epoch anchors {anchor.subject} at"))
    return findings


def _verdicts(
    opened: Mapping[str, epoch.Epoch],
    outcomes: list[tuple[str, derive.ReceiptKind, derive.ReceiptOutcome]],
    unreadable: tuple[str, ...],
) -> tuple[SnapshotVerdict, ...]:
    groups: dict[tuple[derive.ReceiptKind, str], list[tuple[str, derive.ReceiptOutcome]]] = {}
    for name, kind, outcome in outcomes:
        subject = opened[name].receipts[read._member_for(kind)].subject_identity
        if subject is None:
            continue  # names no subject; reported by receipt-malformed alone
        groups.setdefault((kind, subject), []).append((name, outcome))
    return tuple(
        SnapshotVerdict(kind, subject, _reduce([o for _n, o in members]), tuple(sorted(members, key=lambda pair: pair[0])), unreadable)
        for (kind, subject), members in sorted(groups.items())
    )


def audit_epochs(world: registry.World) -> EpochAudit:
    """Every retained pair evaluated, every snapshot reduced, every anchor
    checked against the registry; writes nothing."""
    opened, unreadable, view = _retained(world)
    findings: list[Finding] = [
        Finding("error", "epoch-malformed", name, refusal, f"{name}: this retained carrier does not read: {refusal}")
        for name, refusal in unreadable
    ]
    outcomes: list[tuple[str, derive.ReceiptKind, derive.ReceiptOutcome]] = []
    for name in sorted(opened):
        for kind in _KINDS:
            outcome = read.validate_receipt(world, opened[name], kind)
            outcomes.append((name, kind, outcome))
            finding = _receipt_finding(name, outcome)
            if finding is not None:
                findings.append(finding)
    findings.extend(_anchor_findings(opened, view))
    snapshots = _verdicts(opened, outcomes, tuple(name for name, _r in unreadable))
    for verdict in snapshots:
        if verdict.state == "contradicted":
            findings.append(Finding("error", "snapshot-contradicted", verdict.subject_identity, verdict.kind, f"{verdict.subject_identity}: no receipt naming this {verdict.kind} subject validates and at least one is refuted"))
    return EpochAudit(tuple(outcomes), snapshots, tuple(sorted(findings, key=lambda f: f.sort_key)))


def snapshot_state(world: registry.World, kind: derive.ReceiptKind, subject_identity: str) -> SnapshotVerdict:
    """One subject's state over the retained set; writes nothing."""
    opened, unreadable, _view = _retained(world)
    member = read._member_for(kind)
    members = [
        (name, read.validate_receipt(world, opened[name], kind))
        for name in sorted(opened)
        if opened[name].receipts[member].subject_identity == subject_identity
    ]
    return SnapshotVerdict(kind, subject_identity, _reduce([o for _n, o in members]), tuple(members), tuple(name for name, _r in unreadable))
```

In `python/src/beliefs/world/__init__.py` add `from beliefs.world.audit import SNAPSHOT_STATES, EpochAudit, SnapshotVerdict, audit_epochs, snapshot_state` and the five names to `__all__`; add `"audit"` to the cycle test's module list if literal. `anchors` must be imported in `beliefs.world` before `audit` — it is (line 21).

- [ ] **Step 5: Run, lint, commit**

Run: `cd python && uv run --frozen pytest tests/test_world_epoch_audit.py tests/test_world_import_epoch.py tests/test_world_receipts.py tests/test_world_epoch.py`
Expected: all pass. Tighten the loose assertion noted in step 1.

```bash
uv run --frozen ruff check . && uv run --frozen pyright
cd .. && tasks note <task-4-id> "audit_epochs/snapshot_state: name-only walk, malformed excluded from the reduction, unreadable carriers are findings, anchors corroborated against registry log-head records"
tasks done <task-4-id> "epoch audit and snapshot-state query (spec §4)"
git add python/src/beliefs tasks python/tests/test_world_epoch_audit.py
git commit -m "feat(world): the epoch audit and the snapshot-state query over the retained set"
```

---
### Task 5: Report mode on the world view

**Files:**
- Modify: `python/src/beliefs/errors.py` (after `RecordNotPresent`, line 416), `python/src/beliefs/corpus.py` (add `_collecting_view` after `_root_state_for`, line 742), `python/src/beliefs/world/view.py` (whole open path and the class)
- Test: `python/tests/test_world_view.py`

**Interfaces:**
- Consumes: `corpus._operation_lock_for`, `registry.corpus_state_identity`, `registry.load_manifest`, `ReadView.opened_at`, `ReadView._require_base_pin`, `nodes.core.corpus.Corpus(root, mode="collecting")`, `Corpus.check()`, `Corpus.all()`, `errors.CorpusStateMalformed`, `errors.ContractMismatch`.
- Produces: `errors.CorpusDamaged(ref, corpus_id, stamp)`; `corpus.CONSTRUCTION_CODES`; `corpus._collecting_view(root) -> tuple[tuple[Node, ...], tuple[Finding, ...]]`; `view.DamageReport(corpus_id, carrier, cause, findings)`; `open_world_view(world, published, *, on_damage="refuse")`; `WorldReadView.damaged()`, `.captured_records(corpus_id)`, `.captured_manifest(corpus_id)`; `CorpusDamaged` from `locate`, `resolve`, `holds`, `get`, `inbound`, `corpus_view` on a damaged address. Task 6 builds `audit_world` on these.

- [ ] **Step 1: `tasks start <task-5-id>`, then write the failing tests**

Append to `python/tests/test_world_view.py`:

```python
def damage(root: Path, kind: str) -> None:
    """One damage per S9 clause, each producing exactly its named finding under
    `nodes` 2.0 collecting mode. The two collisions write a *well-placed* twin
    through `raw_write` (its own mapped path), so placement is not the fault:
    `uid-collision` is a different live id sharing the uid; `id-collision` is
    a different live id and uid whose `deprecated_ids` claims the original's
    live id (review finding 4)."""
    from nodes.core.frontmatter import node_from_markdown

    stored_files = sorted(root.rglob("*.md"))
    if kind == "parse-error":
        (root / "verification").mkdir(exist_ok=True)
        (root / "verification" / "bad.md").write_text("---\nnot: [a valid record\n---\n", encoding="utf-8")
        return
    if kind == "path-mismatch":
        source = stored_files[0]
        source.rename(source.with_name("moved-" + source.name))
        return
    original = node_from_markdown(stored_files[0].read_text(encoding="utf-8"))
    twin = original.model_copy(deep=True)
    kind_prefix, _, slug = original.id.partition(":")
    twin.id = f"{kind_prefix}:{slug}-twin"
    if kind == "uid-collision":
        pass  # same uid, different live id, its own mapped path
    elif kind == "id-collision":
        twin.uid = f"twin-{original.uid}"
        twin.deprecated_ids = [original.id]  # claims the original's live id
    else:
        raise ValueError(kind)
    raw_write(root, twin)


class TestReportMode:
    @pytest.mark.parametrize("kind", ["parse-error", "path-mismatch", "uid-collision", "id-collision"])
    def test_a_damaged_carrier_is_reported_and_never_served(self, tmp_path, kind):
        from beliefs.errors import CorpusDamaged, CorpusStateMalformed

        world, roots, published = two_corpus_world(tmp_path)
        damage(roots[BETA], kind)

        with pytest.raises(CorpusStateMalformed):
            open_world_view(world, published)
        view = open_world_view(world, published, on_damage="report")

        (report,) = view.damaged()
        assert report.corpus_id == BETA and report.cause == "construction"
        assert kind in {finding.code for finding in report.findings}
        assert view.absent() == () and all(d.corpus_id != BETA for d in view.drift())
        address = address_in(published, BETA)
        for read_it in (view.locate, view.resolve, view.holds, view.get, view.inbound, view.corpus_view):
            with pytest.raises(CorpusDamaged):
                read_it(address)
        assert view.corpus_of(address) == BETA
        assert all(node.id != address for node in view.iter_stored())
        assert view.captured_records(BETA) and view.captured_manifest(BETA).corpus_id == BETA
        # An undamaged corpus is served exactly as before.
        assert view.get(address_in(published, ALPHA)).id == address_in(published, ALPHA)

    def test_a_foreign_base_pin_is_damage_with_no_records(self, tmp_path):
        from fixtures_cut6 import manifest_document
        from beliefs.errors import ContractMismatch, CorpusDamaged

        world, roots, published = two_corpus_world(tmp_path)
        manifest = manifest_document(BETA).replace(f"science_contract: {pins_for(BASE).science_contract}", "science_contract: science:" + "0" * 64)
        (roots[BETA] / "corpus.yaml").write_text(manifest, encoding="utf-8")

        with pytest.raises(ContractMismatch):
            open_world_view(world, published)
        view = open_world_view(world, published, on_damage="report")

        (report,) = view.damaged()
        assert report.cause == "base-pin" and report.findings == ()
        assert view.captured_records(BETA) == ()
        assert view.captured_manifest(BETA).profile.science_contract == "science:" + "0" * 64
        with pytest.raises(CorpusDamaged):
            view.get(address_in(published, BETA))

    def test_a_damaged_corpus_skips_the_map_and_owner_checks(self, tmp_path):
        """The excluded file may be a mapped record; that is `corpus-damaged`'s
        to report, never corruption at open (spec §5.2)."""
        world, roots, published = two_corpus_world(tmp_path)
        damage(roots[BETA], "uid-collision")  # excludes a mapped record and its twin
        view = open_world_view(world, published, on_damage="report")
        assert view.damaged()[0].corpus_id == BETA

    def test_the_hold_is_the_lock_only_lookup(self, tmp_path, monkeypatch):
        """`_root_state_for` constructs a strict corpus before the hold; report
        mode must never call it on the audited carrier (spec decision 8)."""
        from beliefs.world import view as view_module

        world, roots, published = two_corpus_world(tmp_path)
        damage(roots[BETA], "parse-error")

        def refuse(*_a, **_k):
            raise AssertionError("_root_state_for called under report mode")

        monkeypatch.setattr(view_module, "_root_state_for", refuse)
        view = open_world_view(world, published, on_damage="report")
        assert view.damaged()[0].corpus_id == BETA

    def test_drift_moving_inside_the_hold_still_raises(self, tmp_path, monkeypatch):
        world, roots, published = two_corpus_world(tmp_path)
        from beliefs.world import registry as registry_module

        calls = {"n": 0}
        original = registry_module.corpus_state_identity

        def moving(root):
            calls["n"] += 1
            if calls["n"] == 2:
                raw_write(roots[ALPHA], stored.dataset_node("late", title="late"))
            return original(root)

        monkeypatch.setattr(registry_module, "corpus_state_identity", moving)
        with pytest.raises(CaptureDrift):
            open_world_view(world, published, on_damage="report")
```

`manifest_document(BETA)` writes the cut-6 pins; the replacement swaps the science pin for a syntactically valid unknown identity, which `_require_base_pin` refuses. If `fixtures_cut6.manifest_document` no longer produces the two-corpus fixture's exact manifest, build the string from `registry.manifest_bytes(registry.CorpusManifest(2, BETA, replace(PINS, science_contract=...)))` instead. The last test imports `CaptureDrift` from `beliefs.errors` at the module head.

- [ ] **Step 2: Run them to verify they fail**

Run: `cd python && uv run --frozen pytest tests/test_world_view.py -k ReportMode`
Expected: every test fails — `open_world_view() got an unexpected keyword argument 'on_damage'`.

- [ ] **Step 3: `CorpusDamaged` and `_collecting_view`**

In `python/src/beliefs/errors.py` after `RecordNotPresent`:

```python
class CorpusDamaged(ScienceError):
    """A recorded address's corpus is present but could not be read whole, and
    the view was opened to report that rather than refuse (slice 3 design
    §5.2). A refusal, never an absence: nothing that raises this enters
    `absent()` or any not-present structure."""

    def __init__(self, ref: str, corpus_id: str, stamp: "BoundStamp") -> None:
        self.ref = ref
        self.corpus_id = corpus_id
        self.stamp = stamp
        super().__init__(
            f"{ref}: recorded in {corpus_id}, a present corpus this view could not read whole "
            f"(publication {stamp.packaging_identity[:12]}…); the record is unjudged, not absent"
        )
```

In `python/src/beliefs/corpus.py` after `_root_state_for`:

```python
CONSTRUCTION_CODES = frozenset({"parse-error", "path-mismatch", "uid-collision", "id-collision"})
"""`nodes` 2.0's collecting-mode construction findings, adopted under this
namespace verbatim (slice 3 design §5.5)."""


def _collecting_view(root: Path) -> tuple[tuple[Node, ...], tuple[Finding, ...]]:
    """A damaged root read in `nodes` collecting mode: detached copies of the
    admitted remainder (`Corpus.all()`, never the store) and the construction
    findings re-minted as sealed `Finding`s, selected by code because
    `check()` sorts by ref. The handle is dropped here; it never enters
    `_ROOT_STATES` and no `ReadView` is built over it (S8)."""
    handle = Corpus(Path(root).resolve(), mode="collecting")
    findings = tuple(
        Finding(severity=f.severity, code=f.code, ref=f.ref, detail=f.detail, message=f.message)
        for f in handle.check()
        if f.code in CONSTRUCTION_CODES
    )
    return tuple(node.model_copy(deep=True) for node in handle.all()), tuple(sorted(findings, key=lambda f: f.sort_key))
```

Add `"CONSTRUCTION_CODES"` to `corpus.__all__`.

- [ ] **Step 4: Report mode in `world/view.py`**

Add after `DriftReport`:

```python
@final
@dataclass(frozen=True)
class DamageReport:
    corpus_id: str
    carrier: Path
    cause: Literal["construction", "base-pin"]
    findings: tuple[Finding, ...]
```

(`Literal` from `typing`, `Finding` from `beliefs.corpus`.) Add three private fields to `WorldReadView` — `_damaged: tuple[DamageReport, ...]`, `_captured: Mapping[str, tuple[Node, ...]]`, `_manifests: Mapping[str, CorpusManifest]` — thread them through `_opened`, and add the methods:

```python
    def damaged(self) -> tuple[DamageReport, ...]:
        return self._damaged

    def captured_records(self, corpus_id: str) -> tuple[Node, ...]:
        return tuple(node.model_copy(deep=True) for node in self._captured[corpus_id])

    def captured_manifest(self, corpus_id: str) -> CorpusManifest:
        return self._manifests[corpus_id]

    def _refuse_damaged(self, ref: str) -> None:
        entry = self._recorded.get(ref)
        if entry is not None and entry[0] in self._damaged_ids:
            raise CorpusDamaged(ref, entry[0], self._stamp)
```

with `_damaged_ids: frozenset[str]` set in `_opened`. Call `self._refuse_damaged(ref)` as the first line of `locate`, `resolve`, `get` (before `_located`), `inbound` and `corpus_view`; `holds` goes through `resolve`.

Change `open_world_view`'s signature to `def open_world_view(world: registry.World, published: epoch.Epoch, *, on_damage: Literal["refuse", "report"] = "refuse") -> WorldReadView:` and replace the capture loop (from `captured: dict[str, dict[str, Node]] = {}` through `live[corpus_id] = view`) with:

```python
    captured: dict[str, dict[str, Node]] = {}
    states: dict[str, str] = {}
    live: dict[str, ReadView] = {}
    manifests: dict[str, registry.CorpusManifest] = {}
    all_captured: dict[str, tuple[Node, ...]] = {}
    damaged: list[DamageReport] = []
    for corpus_id in sorted(carriers):
        carrier = carriers[corpus_id]
        with _operation_lock_for(carrier).capture():
            manifests[corpus_id] = registry.load_manifest(carrier)
            try:
                before = registry.corpus_state_identity(carrier)
                view = ReadView.opened_at(carrier)
                view._require_base_pin()
            except CorpusStateMalformed as caught:
                if on_damage == "refuse":
                    raise
                remainder, findings = _collecting_view(carrier)
                damaged.append(DamageReport(corpus_id, carrier, "construction", findings))
                all_captured[corpus_id] = remainder
                continue
            except ContractMismatch:
                if on_damage == "refuse":
                    raise
                damaged.append(DamageReport(corpus_id, carrier, "base-pin", ()))
                all_captured[corpus_id] = ()
                continue
            records = tuple(view.iter_stored())
            after = registry.corpus_state_identity(carrier)
            if before != after:
                raise CaptureDrift(
                    f"{corpus_id}: {carrier}: the corpus state moved inside the capture hold "
                    f"({before} -> {after}); the whole open is discarded and nothing is served"
                )
        captured[corpus_id] = {node.uid: node for node in records}
        all_captured[corpus_id] = records
        states[corpus_id] = before
        live[corpus_id] = view
    damaged_ids = frozenset(report.corpus_id for report in damaged)
```

The map check (`for address, (corpus_id, uid) in recorded.items():`) and the owner map already iterate `captured` only, so a damaged corpus — never entered in `captured` — skips both (spec §5.2). The drift loop likewise. Replace the import line with `from beliefs.corpus import Finding, ReadView, _collecting_view, _operation_lock_for, _producer_ids, validated_node` (keep `_root_state_for` only if the `refuse` path still needs it — it does not: the lock-only lookup hands out the same lock object) and add `ContractMismatch, CorpusDamaged, CorpusStateMalformed` to the `beliefs.errors` import. Pass `damaged=tuple(damaged)`, `captured=all_captured`, `manifests=manifests`, `damaged_ids=damaged_ids` to `_opened`. Extend `__all__` with `"DamageReport"` and re-export it from `beliefs.world`.

`load_manifest` runs inside the hold once; its `ManifestMalformed` cannot reach here (step 1 refused the carrier), and `CorpusStateMalformed` from `corpus_state_identity` already wraps a manifest fault.

- [ ] **Step 5: Run the view suites and the frozen guards**

Run: `cd python && uv run --frozen pytest tests/test_world_view.py tests/acceptance/test_world_view_acceptance.py tests/test_evaluation.py tests/test_audit.py tests/test_arm_staleness.py tests/test_frozen_guards.py`
Expected: all pass. A cut 23 arm whose `before` matched the old `state = _root_state_for(carrier, ...)` line in `view.py` is now stale: record it in `python/tests/cited_not_run.py`'s `stale_arms` with the date and "the hold moved to the lock-only lookup (slice 3 decision 8)", or re-target it if cut 23's guard is live (`test_n2_cut23.py` — check for a `_LIVE_SABOTAGES` table).

- [ ] **Step 6: Lint, commit**

```bash
uv run --frozen ruff check . && uv run --frozen pyright
cd .. && tasks note <task-5-id> "on_damage=report: collecting remainder and construction findings inside the same hold via the lock-only lookup; base-pin damage; CorpusDamaged on every read of a damaged address; map and owner checks skip damaged corpora"
tasks done <task-5-id> "report mode on the world view (spec §5.2)"
git add python/src/beliefs python/tests tasks
git commit -m "feat(world): report-mode world view over damaged carriers"
```

---
### Task 6: The per-corpus checks over a capture and `audit_world`

**Files:**
- Modify: `python/src/beliefs/corpus.py:645-668` (`_CheckView`; add `_CapturedCheckView` after it), `:1194-1394` (`corpus_check` → `_record_findings`), `:1487-1509` (`profile_mismatch` → `_pins_mismatch`, `_manifest_findings`), `python/src/beliefs/audit.py` (imports, `__all__`, `WORLD_AUDIT_CODES`, `WorldAudit`, `audit_world`; widen `check_assessment`, `check_lineage_basis`, `stored_specs`)
- Create: `python/tests/test_world_audit.py`

**Interfaces:**
- Consumes: Task 5's `open_world_view(..., on_damage="report")`, `DamageReport`, `captured_records`, `captured_manifest`, `damaged()`, `drift()`, `absent()`, `CorpusDamaged`; `registry.CorpusManifest`, `CorpusPins`; `shipped_base`.
- Produces: `corpus._CapturedCheckView(records)`; `corpus._pins_mismatch(pins, profile) -> tuple[MismatchScope, str, frozenset[str]]`; `corpus._manifest_findings(manifest, profile) -> tuple[tuple[Finding, ...], MismatchScope, frozenset[str]]`; `corpus._record_findings(check, profile, scope, disagreeing) -> list[Finding]`; `audit.WORLD_AUDIT_CODES`; `audit.WorldAudit(stamp, corpora, world)`; `audit.audit_world(world, published, *, evidence, profile) -> WorldAudit`. Task 7 extends `audit_world`'s `world` findings; Task 9's arms name all of these.

- [ ] **Step 1: `tasks start <task-6-id>`, then write the failing tests**

Create `python/tests/test_world_audit.py`:

```python
"""The world audit over a capture (slice 3 design §5)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fixtures_cut4 import raw_write
from profiles import BASE
from test_profile_agreement import foreign_profile  # noqa: F401 — pytest fixture
from test_world_build import ALPHA, BETA
from test_world_view import address_in, damage, make_absent, two_corpus_world

from beliefs import stored
from beliefs.audit import NO_EVIDENCE, WORLD_AUDIT_CODES, WorldAudit, audit_corpus, audit_world
from beliefs.corpus import ReadView
from beliefs.errors import CorpusDamaged


def codes(findings) -> list[tuple[str, str]]:
    return sorted((f.code, f.detail) for f in findings)


def stale(slug: str):
    node = stored.dataset_node(slug, title=f"dataset {slug}")
    node.facets["semantic-identity"]["hash"] = "0" * 64  # a stale stamp, raw-written
    return node


def inventory(*roots: Path) -> dict[str, bytes]:
    return {str(p): p.read_bytes() for root in roots for p in root.rglob("*") if p.is_file()}


def test_a_clean_world_audits_clean(tmp_path):
    world, _roots, published = two_corpus_world(tmp_path)

    audit = audit_world(world, published, evidence=NO_EVIDENCE, profile=BASE)

    assert isinstance(audit, WorldAudit) and audit.stamp.packaging_identity == published.packaging_identity
    assert dict(audit.corpora) == {ALPHA: (), BETA: ()}
    assert audit.world == ()


def test_a_raw_written_record_is_drift_and_judged_and_skipped_by_recomputation(tmp_path):
    world, roots, published = two_corpus_world(tmp_path)
    late = stale("late")
    raw_write(roots[ALPHA], late)

    audit = audit_world(world, published, evidence=NO_EVIDENCE, profile=BASE)

    assert codes(audit.corpora[ALPHA]) == [("drift", f"unmapped:{late.uid}"), ("semantic-hash-stale", "mismatch")]
    local = audit_corpus(ReadView.opened_at(roots[ALPHA]), evidence=NO_EVIDENCE, profile=BASE)
    assert [f for f in local if f.code == "semantic-hash-stale"] == [f for f in audit.corpora[ALPHA] if f.code == "semantic-hash-stale"]
    assert not any(f.code.endswith("-contradicted") or f.code == "derivation-malformed" for f in audit.corpora[ALPHA])


def test_a_post_publication_edit_is_state_drift(tmp_path):
    world, roots, published = two_corpus_world(tmp_path)
    (roots[BETA] / "corpus.yaml").write_bytes((roots[BETA] / "corpus.yaml").read_bytes() + b"\n")

    audit = audit_world(world, published, evidence=NO_EVIDENCE, profile=BASE)

    assert codes(audit.corpora[BETA]) == [] or codes(audit.corpora[BETA]) == [("drift", "state")]
    # A whitespace-only manifest edit does not move the state (W13); edit a node instead:
    raw_write(roots[BETA], stale("moved"))
    audit = audit_world(world, published, evidence=NO_EVIDENCE, profile=BASE)
    assert ("drift", "state") in codes(audit.corpora[BETA])


def test_an_absent_corpus_is_reported(tmp_path):
    world, roots, published = two_corpus_world(tmp_path)
    make_absent(roots, BETA)

    audit = audit_world(world, published, evidence=NO_EVIDENCE, profile=BASE)

    assert codes(audit.corpora[BETA]) == [("corpus-absent", "")]


@pytest.mark.parametrize("kind", ["parse-error", "path-mismatch", "uid-collision", "id-collision"])
def test_a_damaged_corpus_is_judged_on_its_remainder_and_never_compared(tmp_path, kind):
    world, roots, published = two_corpus_world(tmp_path)
    raw_write(roots[BETA], stale("remainder"))
    damage(roots[BETA], kind)

    audit = audit_world(world, published, evidence=NO_EVIDENCE, profile=BASE)

    found = codes(audit.corpora[BETA])
    assert any(code == kind for code, _ in found)
    assert ("semantic-hash-stale", "mismatch") in found
    assert any(code == "corpus-damaged" and detail.startswith("construction:") for code, detail in found)
    assert not any(code == "drift" for code, _ in found)
    assert audit.corpora[ALPHA] == ()


def test_a_foreign_base_pin_is_reported_from_the_manifest_alone(tmp_path):
    from dataclasses import replace

    from fixtures_cut6 import PINS

    from beliefs.world import registry

    world, roots, published = two_corpus_world(tmp_path)
    pins = replace(PINS, science_contract="science:" + "0" * 64)
    (roots[BETA] / "corpus.yaml").write_bytes(registry.manifest_bytes(registry.CorpusManifest(2, BETA, pins)))

    audit = audit_world(world, published, evidence=NO_EVIDENCE, profile=BASE)

    assert codes(audit.corpora[BETA]) == [("corpus-damaged", "base-pin"), ("profile-mismatch", "base")]


def test_a_recomputation_reaching_a_damaged_corpus_is_unreachable(tmp_path):
    """A verification in ALPHA whose two runs sit in BETA — cut 23's R19
    fixture (`verification_fixtures.self_consistent_forgery`, see
    `test_world_view.py`'s R19 test) — with BETA damaged."""
    from test_world_view import cross_corpus_verification_world  # the R19 fixture factory; add it if it is inline

    world, roots, published, verification = cross_corpus_verification_world(tmp_path)
    damage(roots[BETA], "parse-error")

    audit = audit_world(world, published, evidence=NO_EVIDENCE, profile=BASE)

    assert ("derivation-unreachable", BETA) in codes(audit.corpora[ALPHA])
    assert all(f.ref == verification.id for f in audit.corpora[ALPHA] if f.code == "derivation-unreachable")


def test_the_audit_writes_nothing_and_every_code_is_declared(tmp_path):
    world, roots, published = two_corpus_world(tmp_path)
    damage(roots[BETA], "parse-error")
    before = inventory(world.config.world_root, *roots.values())

    audit = audit_world(world, published, evidence=NO_EVIDENCE, profile=BASE)

    assert inventory(world.config.world_root, *roots.values()) == before
    for f in [*audit.world, *(f for fs in audit.corpora.values() for f in fs)]:
        assert f.code in WORLD_AUDIT_CODES or f.code in {"semantic-hash-stale", "profile-mismatch"}


def test_a_foreign_profile_stops_every_recomputation(tmp_path, monkeypatch, foreign_profile):
    """Scope `base` from the supplied profile, not the manifest: the view opens
    (the manifest pins the shipped base), and `audit_corpus`'s early return
    must hold per corpus — nothing is recomputed (review finding 1)."""
    from beliefs import audit as audit_module

    world, _roots, published = two_corpus_world(tmp_path)
    assert foreign_profile.base_contract_identity != BASE.base_contract_identity

    def never(*_a, **_k):
        raise AssertionError("a recomputation ran under a base mismatch")

    monkeypatch.setattr(audit_module, "_recompute", never)
    audit = audit_world(world, published, evidence=NO_EVIDENCE, profile=foreign_profile)

    assert codes(audit.corpora[ALPHA]) == [("profile-mismatch", "base")] == codes(audit.corpora[BETA])


def test_corpus_damaged_never_escapes(tmp_path):
    world, roots, published = two_corpus_world(tmp_path)
    damage(roots[BETA], "id-collision")
    try:
        audit_world(world, published, evidence=NO_EVIDENCE, profile=BASE)
    except CorpusDamaged:  # pragma: no cover - the assertion
        pytest.fail("CorpusDamaged escaped audit_world")
```

If `test_world_view.py`'s R19 fixture is inline in its test, extract it there as `cross_corpus_verification_world(tmp_path) -> (world, roots, published, verification_node)` in the same commit; the test body is unchanged.

- [ ] **Step 2: Run them to verify they fail**

Run: `cd python && uv run --frozen pytest tests/test_world_audit.py`
Expected: import error — `audit_world` does not exist.

- [ ] **Step 3: Split `corpus_check` without changing it**

In `python/src/beliefs/corpus.py`:

1. After `_CheckView` add:

```python
class _CapturedCheckView:
    """`_CheckView`'s shape over one corpus's captured records — mapped and
    drift alike — resolving live and deprecated ids over that set and nothing
    else, so "does not resolve locally" means the capture (slice 3 §5.3)."""

    def __init__(self, records: Sequence[Node]) -> None:
        self._by_id = {node.id: node for node in records}
        self._live: dict[str, str] = {}
        for node in records:
            self._live[node.id] = node.id
            for deprecated in node.deprecated_ids:
                self._live.setdefault(deprecated, node.id)

    def resolve(self, ref: str) -> str | None:
        return self._live.get(ref)

    def holds(self, ref: str) -> bool:
        return self.resolve(ref) is not None

    def get(self, ref: str) -> Node:
        resolved = self.resolve(ref)
        return self._by_id[resolved if resolved is not None else ref]

    def iter_stored(self) -> Iterator[Node]:
        yield from self._by_id.values()

    def producers(self, dataset: str, *, aliases: tuple[str, ...] = ()) -> tuple[str, ...]:
        return _producer_ids(self, dataset, aliases=aliases)
```

and widen `_producer_ids`, `eligibility_refusal` and `validity_refusal`'s `ProducerView` protocol annotations to admit it (`_CheckView | _CapturedCheckView` wherever `_CheckView` is named).

2. Replace `profile_mismatch`'s body from `from beliefs.world import load_manifest` onward with a call: load the manifest as today, catching the two errors into `("malformed", str(caught), frozenset())`, then `return _pins_mismatch(load_manifest(Path(root)).profile, profile)`; move the pin comparison into:

```python
def _pins_mismatch(pins: CorpusPins, profile: ProfileSpec) -> tuple[MismatchScope, str, frozenset[str]]:
    if pins.science_contract != "science:" + profile.base_contract_identity:
        return "base", f"manifest pins {pins.science_contract[:20]}…, profile carries science:{profile.base_contract_identity[:12]}…", frozenset()
    expected = {ns: f"{ns}:{identity}" for ns, identity in profile.activated_contracts.items()}
    disagreeing = frozenset(ns for ns in set(pins.domains) | set(expected) if pins.domains.get(ns) != expected.get(ns))
    if disagreeing:
        return "domains", f"manifest domains disagree on {sorted(disagreeing)}", disagreeing
    return "none", "", frozenset()


def _manifest_findings(manifest: CorpusManifest, profile: ProfileSpec) -> tuple[tuple[Finding, ...], MismatchScope, frozenset[str]]:
    """The manifest half of `corpus_check` over a parsed manifest (the world
    audit's captured one): the base check first, as `profile_mismatch` orders it."""
    if profile.base_contract_identity != shipped_base().base_contract_identity:
        return (Finding("error", "profile-mismatch", "corpus.yaml", "base", "the supplied profile requires a different base than this runtime ships"),), "base", frozenset()
    scope, detail, disagreeing = _pins_mismatch(manifest.profile, profile)
    findings = (Finding("error", "profile-mismatch", "corpus.yaml", scope, detail),) if scope != "none" else ()
    return findings, scope, disagreeing
```

(`CorpusManifest` is already a `TYPE_CHECKING` import; `CorpusPins` is imported from `beliefs.consulted`.)

3. In `corpus_check`, cut everything from `check = _CheckView(view)` to just before `return tuple(sorted(findings, ...))` into `_record_findings(check, profile, scope, disagreeing) -> list[Finding]` — the body is moved verbatim with three substitutions: `view.holds(relation.target)` → `check.holds(relation.target)`, `view.resolve(target["ref"])` → `check.resolve(target["ref"])`, and it returns its `findings` list instead of appending to the outer one. `corpus_check` becomes: the manifest block as today, `findings.extend(_record_findings(_CheckView(view), profile, scope, disagreeing))`, the sorted return. Run `uv run --frozen pytest tests/test_corpus_check.py tests/test_audit.py tests/test_facet_seams.py` (or whichever modules name `corpus_check`; grep) — every existing finding is byte-identical.

- [ ] **Step 4: `audit_world`**

In `python/src/beliefs/audit.py`: widen `check_assessment`'s and `stored_specs`'s `view` to `ReadView | _ImportView | WorldReadView` and `check_lineage_basis`'s to `ReadView | WorldReadView` (bodies unchanged); import `CorpusDamaged` from `beliefs.errors`, `_CapturedCheckView, _manifest_findings, _record_findings` from `beliefs.corpus`, `BoundStamp` under `TYPE_CHECKING` from `beliefs.world.read`, `Mapping` and `dataclass`; add:

```python
WORLD_AUDIT_CODES = frozenset(
    {
        "epoch-malformed", "receipt-malformed", "receipt-refuted", "receipt-unresolvable",
        "snapshot-contradicted", "anchor-uncorroborated",
        "parse-error", "path-mismatch", "uid-collision", "id-collision",
        "corpus-damaged", "corpus-absent", "drift", "derivation-unreachable",
        "attestation-endpoint-unknown", "attestation-endpoint-unreachable", "source-identifier-shared",
    }
)
"""Slice 3 design §5.5's closed set, beside `MALFORMEDNESS_CODES`."""


@dataclass(frozen=True)
class WorldAudit:
    stamp: BoundStamp
    corpora: Mapping[str, tuple[Finding, ...]]
    world: tuple[Finding, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "corpora", MappingProxyType(dict(self.corpora)))


def _recompute(view: WorldReadView, node: Node, evidence: DerivationEvidence) -> DerivationOutcome | None:
    if node.kind == "verification":
        return check_verification(view, node, evidence=evidence)
    if node.kind == "assessment":
        return check_assessment(view, node, evidence=evidence)
    if node.kind == "dataset":
        return check_lineage_basis(view, node)
    if node.kind == "analysis-spec":
        return check_analysis_spec(node)
    return None


def audit_world(world: World, published: Epoch, *, evidence: DerivationEvidence, profile: ProfileSpec) -> WorldAudit:
    """Judge the capture at `published`, corpus by corpus and across corpora
    (slice 3 design §5). Reports and never raises; writes nothing."""
    from beliefs.world.view import open_world_view

    view = open_world_view(world, published, on_damage="report")
    damaged = {report.corpus_id: report for report in view.damaged()}
    drift = {report.corpus_id: report for report in view.drift()}
    corpora: dict[str, list[Finding]] = {}
    malformed: dict[str, set[str]] = {}
    excluded: set[str] = set()  # corpora no recomputation may touch: base/malformed scope
    for corpus_id, _state in published.coverage:
        findings = corpora.setdefault(corpus_id, [])
        if corpus_id in view.absent():
            findings.append(Finding("warning", "corpus-absent", corpus_id, "", f"{corpus_id}: a covered corpus with no carrier here"))
            continue
        manifest_findings, scope, disagreeing = _manifest_findings(view.captured_manifest(corpus_id), profile)
        findings.extend(manifest_findings)
        report = damaged.get(corpus_id)
        if report is not None and report.cause == "base-pin":
            findings.append(Finding("error", "corpus-damaged", corpus_id, "base-pin", f"{corpus_id}: the manifest pins a base this runtime does not ship; no record was read and nothing was recomputed"))
            continue
        if scope in ("base", "malformed"):
            excluded.add(corpus_id)  # `audit_corpus`'s early return, per corpus: nothing below judges it
            continue
        findings.extend(_record_findings(_CapturedCheckView(view.captured_records(corpus_id)), profile, scope, disagreeing))
        malformed[corpus_id] = {finding.ref for finding in findings if finding.code in MALFORMEDNESS_CODES}
        if report is not None:
            findings.extend(report.findings)
            excluded = len({finding.ref for finding in report.findings})
            findings.append(Finding("error", "corpus-damaged", corpus_id, f"construction:{excluded}", f"{corpus_id}: {excluded} file(s) failed construction; the remainder was audited, nothing was recomputed and no drift comparison was made"))
            continue
        moved = drift.get(corpus_id)
        if moved is not None:
            if moved.published_state != moved.captured_state:
                findings.append(Finding("warning", "drift", corpus_id, "state", f"{corpus_id}: the carrier stands at {moved.captured_state[:12]}…, not the {moved.published_state[:12]}… this epoch recorded; rebuild to publish over it"))
            for uid in moved.unmapped:
                findings.append(Finding("warning", "drift", corpus_id, f"unmapped:{uid}", f"{corpus_id}: uid {uid!r} is held but the epoch never mapped it; rebuild to publish it"))
    for node in view.iter_stored():
        corpus_id = view.corpus_of(node.id)
        assert corpus_id is not None  # iter_stored yields mapped records only
        if corpus_id in excluded or node.id in malformed.get(corpus_id, set()):
            continue
        try:
            outcome = _recompute(view, node, evidence)
        except CorpusDamaged as unreachable:
            corpora[corpus_id].append(Finding("warning", "derivation-unreachable", node.id, unreachable.corpus_id, f"{node.id}: its recomputation reaches {unreachable.corpus_id}, which this audit could not read whole"))
            continue
        except RecordError as refused:
            corpora[corpus_id].append(Finding("error", "derivation-malformed", node.id, str(refused), f"{node.id}: the members a derivation recomputation reads are malformed"))
            continue
        if outcome is not None and outcome.contradiction is not None:
            corpora[corpus_id].append(outcome.contradiction)
    world_findings: list[Finding] = []  # Task 7: `_world_findings(world, view, published, malformed, excluded)`
    return WorldAudit(
        view.stamp,
        {corpus_id: tuple(sorted(findings, key=lambda f: f.sort_key)) for corpus_id, findings in corpora.items()},
        tuple(sorted(world_findings, key=lambda f: f.sort_key)),
    )
```

`World` and `Epoch` are `TYPE_CHECKING` imports from `beliefs.world.registry` and `beliefs.world.epoch`; `Node` is already imported. Add `"WORLD_AUDIT_CODES"`, `"WorldAudit"`, `"audit_world"` to `__all__`.

- [ ] **Step 5: Run, lint, commit**

Run: `cd python && uv run --frozen pytest tests/test_world_audit.py tests/test_audit.py tests/test_world_view.py tests/test_arm_staleness.py tests/test_frozen_guards.py` and then the fast loop.
Expected: all pass. A frozen arm matching a moved `corpus_check` line (cuts 3, 5, 14 name lines in it) is recorded in `cited_not_run.py`'s `stale_arms` or re-targeted, per the global constraint.

```bash
uv run --frozen ruff check . && uv run --frozen pyright
cd .. && tasks note <task-6-id> "audit_world: per-corpus checks over the capture through _CapturedCheckView, damaged/absent/drift findings, recomputations over mapped records with derivation-unreachable"
tasks done <task-6-id> "world audit over a capture (spec §5.1-5.3)"
git add python/src/beliefs python/tests tasks
git commit -m "feat(audit): the world audit judges the capture corpus by corpus and across corpora"
```

---
### Task 7: The world-level findings

**Files:**
- Modify: `python/src/beliefs/audit.py` (`audit_world`'s `world_findings`; add `_world_findings`)
- Test: `python/tests/test_world_audit.py`

**Interfaces:**
- Consumes: `stored.coreference_attestation_value`, `stored.COREFERENCE_ATTESTATION_FACET`, `stored._source_identifiers`, `source.normalized_identifiers`, `errors.IdentifierMalformed`, `read.Unknown`, `CorpusDamaged`, Task 4's `audit_epochs`-shaped receipt findings (`_receipt_finding`, `_verdicts`) — import `beliefs.world.audit` inside the function.
- Produces: `audit_world(...).world` carrying `attestation-endpoint-unknown`, `attestation-endpoint-unreachable`, `source-identifier-shared`, and the audited epoch's `receipt-*` / `snapshot-contradicted` findings (spec §5.4).

- [ ] **Step 1: `tasks start <task-7-id>`, then write the failing tests**

Append to `python/tests/test_world_audit.py`:

```python
def attestation(left: str, right: str):
    return stored.coreference_attestation_node(
        title="coreference attestation", endpoints=(left, right), stance=1, actor="alice", grounds="same work", event_token="event-1"
    )


def test_an_attestation_over_a_deleted_endpoint_is_unknown_and_one_over_an_absent_endpoint_is_not(tmp_path):
    from test_world_receipts import corpora, hold_shipped, publish, world_over
    from test_world_build import sample_nodes, slug_for

    coverage = (ALPHA, BETA)
    alpha_nodes = sample_nodes(slug_for(ALPHA, coverage))
    beta_nodes = sample_nodes(slug_for(BETA, coverage))
    gone = stored.proposition_node("gone", title="gone", claim={"operator": "affects"})
    kept = beta_nodes[0]
    over_gone = attestation(*sorted((gone.id, alpha_nodes[0].id)))  # its endpoint will be deleted: unknown after a rebuild
    over_beta = attestation(*sorted((alpha_nodes[1].id, kept.id)))  # its endpoint sits in BETA: not-present when BETA is absent
    roots = corpora(tmp_path, {ALPHA: (*alpha_nodes, gone, over_gone, over_beta), BETA: beta_nodes})
    world = world_over(tmp_path, roots)
    bindings = hold_shipped(world)
    publish(world, coverage, bindings)
    # Delete the endpoint through the managed door, then rebuild so the deletion is published.
    from authority import FULL
    from beliefs.root import open_corpus

    open_corpus(roots[ALPHA], authority=FULL, profile=BASE).delete(gone.id)
    rebuilt = publish(world, coverage, bindings)

    audit = audit_world(world, rebuilt, evidence=NO_EVIDENCE, profile=BASE)
    assert codes(audit.world) == [("attestation-endpoint-unknown", gone.id)]

    make_absent(roots, BETA)
    absent = audit_world(world, rebuilt, evidence=NO_EVIDENCE, profile=BASE)
    # The deleted endpoint stays unknown; the BETA endpoint is not-present and yields nothing (review finding 8).
    assert codes(f for f in absent.world if f.code.startswith("attestation-endpoint")) == [
        ("attestation-endpoint-unknown", gone.id)
    ]
    assert not any(f.ref == over_beta.id for f in absent.world)
    receipt_findings = [f for f in absent.world if f.code == "receipt-unresolvable"]
    assert len(receipt_findings) == 4
    assert {f.detail.partition(":")[0] for f in receipt_findings} == {
        "producer", "retraction-enumeration", "certification-enumeration", "coreference-reduction"
    }


def test_a_healthy_attestation_naming_a_damaged_endpoint_reports_and_the_audit_completes(tmp_path):
    from test_world_receipts import corpora, hold_shipped, publish, world_over
    from test_world_build import sample_nodes, slug_for

    coverage = (ALPHA, BETA)
    alpha_nodes = sample_nodes(slug_for(ALPHA, coverage))
    beta_nodes = sample_nodes(slug_for(BETA, coverage))
    pair = sorted((alpha_nodes[0].id, beta_nodes[0].id))
    roots = corpora(tmp_path, {ALPHA: (*alpha_nodes, attestation(*pair)), BETA: beta_nodes})
    world = world_over(tmp_path, roots)
    published = publish(world, coverage, hold_shipped(world))
    damage(roots[BETA], "parse-error")

    audit = audit_world(world, published, evidence=NO_EVIDENCE, profile=BASE)

    assert ("attestation-endpoint-unreachable", beta_nodes[0].id) in codes(audit.world)
    # Repair the same corpus in place — remove the unparsable file — and audit the same epoch (review finding 8).
    (roots[BETA] / "verification" / "bad.md").unlink()
    repaired = audit_world(world, published, evidence=NO_EVIDENCE, profile=BASE)
    assert not any(f.code.startswith("attestation-endpoint") for f in repaired.world)
    assert repaired.corpora[BETA] == ()


def test_two_sources_sharing_a_secondary_identifier_are_reported(tmp_path):
    from test_world_receipts import corpora, hold_shipped, publish, world_over

    doi_first = stored.source_node(title="paper", identifiers={"doi": "10.1234/abc", "pmid": "42"})
    pmid_only = stored.source_node(title="paper again", identifiers={"pmid": "42"})
    unrelated = stored.source_node(title="other", identifiers={"pmid": "43"})
    assert doi_first.id != pmid_only.id  # precedence makes them two addresses (slice 2b §6.4)
    roots = corpora(tmp_path, {ALPHA: (doi_first, unrelated), BETA: (pmid_only,)})
    world = world_over(tmp_path, roots)
    published = publish(world, (ALPHA, BETA), hold_shipped(world))

    audit = audit_world(world, published, evidence=NO_EVIDENCE, profile=BASE)

    assert codes(audit.world) == [("source-identifier-shared", "pmid:42")]
    (finding,) = audit.world
    assert finding.ref == min(doi_first.id, pmid_only.id) and finding.severity == "warning"


def test_the_audited_epochs_receipts_are_reported_on_the_world(tmp_path):
    from test_world_receipts import document, repackage

    world, _roots, published = two_corpus_world(tmp_path)
    receipt = document(published, "producer-receipt.yaml")
    receipt["rule_identity"] = "v1"
    forged = repackage(world, published, {"producer-receipt.yaml": receipt})

    audit = audit_world(world, forged, evidence=NO_EVIDENCE, profile=BASE)

    assert ("receipt-malformed", "producer: " ) in [(f.code, f.detail[: len("producer: ")]) for f in audit.world]
    assert audit_world(world, published, evidence=NO_EVIDENCE, profile=BASE).world == ()
```

`open_corpus(root, authority=FULL, profile=BASE)` is how `test_world_view_acceptance.py`'s fixture obtains a writer; if the unit fixtures' roots were built with the plain `Corpus` (they were, through `corpus_at`), open them with the same `DefaultExecutor` the world was built with — `test_deletion_rows.py` shows the `CorpusWriter` call for a plain root (grep `.delete(`). The deletion must go through the write API, never a raw unlink, so the rebuilt epoch maps nothing for `gone`.

- [ ] **Step 2: Run them to verify they fail**

Run: `cd python && uv run --frozen pytest tests/test_world_audit.py -k "attestation or secondary or audited_epochs"`
Expected: 4 failed — `audit.world` is empty.

- [ ] **Step 3: `_world_findings`**

In `python/src/beliefs/audit.py` add, and call it in `audit_world` as `world_findings = _world_findings(world, view, published, malformed, excluded)`:

```python
def _world_findings(
    world: World,
    view: WorldReadView,
    published: Epoch,
    malformed: Mapping[str, set[str]],
    excluded: set[str],
) -> list[Finding]:
    """Ω_valid first, here too: a record the per-corpus check classified
    malformed, or a corpus excluded under a base mismatch, is never decoded
    again (review finding 2)."""
    from beliefs import source as source_basis
    from beliefs.errors import IdentifierMalformed
    from beliefs.world import audit as epoch_audit
    from beliefs.world.read import Unknown, validate_receipt

    findings: list[Finding] = []
    identifiers: dict[tuple[str, str], list[str]] = {}
    for node in view.iter_stored():
        corpus_id = view.corpus_of(node.id)
        if corpus_id in excluded or node.id in malformed.get(corpus_id or "", set()):
            continue
        if node.kind == "coreference-attestation":
            try:
                endpoints = stored.coreference_attestation_value(node).endpoints
            except MalformedRecord:
                continue  # classified by the per-record check under its own ref
            for endpoint in endpoints:
                try:
                    located = view.locate(endpoint)
                except CorpusDamaged:
                    findings.append(Finding("warning", "attestation-endpoint-unreachable", node.id, endpoint, f"{node.id}: endpoint {endpoint} sits in a corpus this audit could not read whole"))
                    continue
                if type(located) is Unknown:
                    findings.append(Finding("warning", "attestation-endpoint-unknown", node.id, endpoint, f"{node.id}: endpoint {endpoint} is an address this epoch never observed; the attestation names nothing the world holds or held"))
        elif node.kind == "source":
            try:
                normalized = source_basis.normalized_identifiers(dict(stored._source_identifiers(node)))
            except IdentifierMalformed:
                continue  # the per-record check's finding, already reported
            for scheme, value in normalized.items():
                identifiers.setdefault((scheme, value), []).append(node.id)
    for (scheme, value), holders in sorted(identifiers.items()):
        distinct = sorted(set(holders))
        if len(distinct) > 1:
            findings.append(Finding("warning", "source-identifier-shared", distinct[0], f"{scheme}:{value}", f"{distinct[0]}: shares {scheme}:{value} with {', '.join(distinct[1:])}; precedence made these two addresses and they may be one work"))
    opened = {published.packaging_identity: published}
    outcomes = []
    for kind in epoch_audit._KINDS:
        outcome = validate_receipt(world, published, kind)
        outcomes.append((published.packaging_identity, kind, outcome))
        finding = epoch_audit._receipt_finding(published.packaging_identity, outcome)
        if finding is not None:
            findings.append(finding)
    for verdict in epoch_audit._verdicts(opened, outcomes, ()):
        state = epoch_audit.snapshot_state(world, verdict.kind, verdict.subject_identity).state
        if state == "contradicted":
            findings.append(Finding("error", "snapshot-contradicted", verdict.subject_identity, verdict.kind, f"{verdict.subject_identity}: no receipt naming this {verdict.kind} subject validates and at least one is refuted"))
    return findings
```

`validate_receipt` is imported inside the function (the audit module imports `corpus`, and `world.read` imports `corpus`; a function-local import keeps the order). The verdict for the audited epoch is reduced over the **retained set** through `snapshot_state`, as spec §5.4 requires; the local `_verdicts` call only enumerates the subjects.

Add one more test to `python/tests/test_world_audit.py`:

```python
def test_a_malformed_attestation_is_a_per_record_finding_and_the_audit_completes(tmp_path):
    from test_world_receipts import hold_shipped, publish

    from beliefs.world.view import open_world_view

    world, roots, published = two_corpus_world(tmp_path)
    broken = attestation(address_in(published, ALPHA), address_in(published, BETA))
    raw_write(roots[ALPHA], broken)
    published = publish(world, (ALPHA, BETA), hold_shipped(world))

    # Corrupt an already mapped record; its id and uid stay fixed.
    broken.facets[stored.COREFERENCE_ATTESTATION_FACET]["endpoints"] = [address_in(published, ALPHA)]
    raw_write(roots[ALPHA], broken)
    assert broken.id in {node.id for node in open_world_view(world, published).iter_stored()}

    audit = audit_world(world, published, evidence=NO_EVIDENCE, profile=BASE)

    assert any(f.ref == broken.id and f.code == "semantic-hash-stale" for f in audit.corpora[ALPHA])
    assert not any(f.ref == broken.id for f in audit.world)
```

The raw record's stamp no longer covers its edited facet, so `semantic-hash-stale`
is the finding the per-record check reports. Its address was published before the
edit, so the world-level loop encounters it and must honor that classification.

- [ ] **Step 4: Run, lint, commit**

Run: `cd python && uv run --frozen pytest tests/test_world_audit.py tests/test_world_epoch_audit.py`
Expected: all pass.

```bash
uv run --frozen ruff check . && uv run --frozen pyright
cd .. && tasks note <task-7-id> "world findings: attestation endpoints unknown/unreachable, shared secondary identifiers, the audited epoch's receipts reduced over the retained set"
tasks done <task-7-id> "world-level findings (spec §5.4)"
git add python/src/beliefs/audit.py python/tests/test_world_audit.py tasks
git commit -m "feat(audit): world-level findings for attestation endpoints, shared identifiers and the audited epoch's receipts"
```

---

### Task 8: Relabel fixtures — X5, W13 and R23's divergence

**Files:**
- Create: `python/tests/test_world_relabels.py`

**Interfaces:**
- Consumes: `test_world_receipts` helpers, `test_world_view.chain_nodes`, `registry` (`WorldConfig`, `manifest_bytes`, `CorpusManifest`, `admission_digest`, `_scan_registry`), `epoch.build_epoch`, `derive.belief_input_identity`, `read.validate_receipt`, `lineage_snapshot`, `certify`, `divergence_state`, `snapshot_projection`, `closure.belief_input_digest` (the digest the R23 arm compares; grep `belief_input_digest` in `python/src/beliefs/closure.py` for the exact call).
- Produces: the unit tests Task 9's `UNIT_CHECKS` name for `X5`, `W13` and `R23`'s divergence arm.

- [ ] **Step 1: `tasks start <task-8-id>`, then write the tests (they should pass on the tree — every one is a measured or relabel arm)**

Create `python/tests/test_world_relabels.py`:

```python
"""Relabel arms and the measured R23 divergence arm (slice 3 design §7)."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml
from nodes.core.write_plan import DefaultExecutor
from test_world_build import ALPHA, BETA, ChainHeads, sample_nodes, slug_for
from test_world_receipts import corpora, hold_shipped, publish, world_over
from test_world_view import chain_nodes

from beliefs import stored
from beliefs.corpus import lineage_snapshot
from beliefs.errors import CoverageUnresolvable
from beliefs.lineage import certify, divergence_state, snapshot_projection
from beliefs.world import derive, epoch, read, registry
from beliefs.world.view import open_world_view


from test_relocation_rows import _belief_digest  # kernel §5.1's digest, from a belief evaluated over the epoch's producer snapshot


class TestW13:
    def test_moving_renaming_and_remounting_a_root_changes_no_identity(self, tmp_path):
        coverage = (ALPHA, BETA)
        roots = corpora(tmp_path, {c: sample_nodes(slug_for(c, coverage)) for c in coverage})
        world = world_over(tmp_path, roots)
        bindings = hold_shipped(world)
        first = publish(world, coverage, bindings)
        before = (first.coverage, first.documents["producer-snapshot.yaml"], _belief_digest(first))

        for relocation in ("moved", "renamed-differently", "cloned"):
            target = tmp_path / relocation
            if relocation == "cloned":
                shutil.copytree(roots[BETA], target)
                shutil.rmtree(roots[BETA])  # the clone is mounted *instead*: two live carriers are X5's refusal
            else:
                roots[BETA].rename(target)
            roots[BETA] = target
            world = registry.World(
                registry.WorldConfig(world.config.world_root, world.config.world_id, tuple(roots.values())),
                DefaultExecutor, chain_head=ChainHeads(), corpus_executor_factory=DefaultExecutor, authority=world.authority,
            )
            again = publish(world, coverage, bindings)
            assert registry.load_manifest(target).corpus_id == BETA
            assert (again.coverage, again.documents["producer-snapshot.yaml"], _belief_digest(again)) == before

    def test_a_coordinated_forgery_is_undetected_and_reads_as_a_fork(self, tmp_path):
        from fixtures_cut6 import PINS

        coverage = (ALPHA, BETA)
        roots = corpora(tmp_path, {c: sample_nodes(slug_for(c, coverage)) for c in coverage})
        world = world_over(tmp_path, roots)
        bindings = hold_shipped(world)
        published = publish(world, coverage, bindings)
        replica = tmp_path / "replica"
        shutil.copytree(roots[BETA], replica)  # a pre-edit replica, unmounted for now

        forged_id = "d" * 32
        (roots[BETA] / "corpus.yaml").write_bytes(registry.manifest_bytes(registry.CorpusManifest(2, forged_id, PINS)))
        admission = registry.AdmissionRecord(registry.CorpusManifest(2, forged_id, PINS), registry.Fresh(), "forger")
        record_dir = world.config.world_root / "registry"
        (record_dir / f"{registry.admission_digest(admission)}.yaml").write_bytes(
            yaml.safe_dump(registry.admission_projection(admission), sort_keys=True).encode("utf-8")
        )

        forged = publish(world, (ALPHA, forged_id), bindings)  # proceeds: nothing detects the coordinated act
        assert forged_id in dict(forged.coverage)
        assert read.validate_receipt(world, published, "producer").outcome == "unresolvable"  # states moved with the id

        roots[BETA] = replica
        world = registry.World(
            registry.WorldConfig(world.config.world_root, world.config.world_id, (roots[ALPHA], replica, tmp_path / "moved-forged")),
            DefaultExecutor, chain_head=ChainHeads(), corpus_executor_factory=DefaultExecutor, authority=world.authority,
        )
        assert read.validate_receipt(world, published, "producer").outcome == "validated"  # the replica validates
        scan = registry._scan_registry(world.config.world_root)
        assert {a.manifest.corpus_id for a in scan.admissions} == {ALPHA, BETA, forged_id}  # two admissions, as a fork's registry reads
        assert not any(a.manifest.forked_from for a in scan.admissions if a.manifest.corpus_id == forged_id)  # and no assertion ties them

    def test_raw_deleting_an_admission_evades_nothing(self, tmp_path):
        """Cut 6 read the undetected half; the build's refusal is the other half."""
        coverage = (ALPHA, BETA)
        roots = corpora(tmp_path, {c: sample_nodes(slug_for(c, coverage)) for c in coverage})
        world = world_over(tmp_path, roots)
        bindings = hold_shipped(world)
        for record in (world.config.world_root / "registry").iterdir():
            if BETA in record.read_text(encoding="utf-8"):
                record.unlink()
        with pytest.raises(CoverageUnresolvable):
            publish(world, coverage, bindings)


class TestX5:
    def test_two_carriers_of_one_id_refuse_the_build_and_offer_no_repair(self, tmp_path):
        """The build arm (cut 7) re-read as X5's whole: refusal, reported, no merge."""
        coverage = (ALPHA,)
        roots = corpora(tmp_path, {ALPHA: sample_nodes("one")})
        twin = tmp_path / "twin"
        shutil.copytree(roots[ALPHA], twin)
        world = world_over(tmp_path, roots, also_configured=(twin,))
        bindings = hold_shipped(world)
        with pytest.raises(CoverageUnresolvable) as refused:
            publish(world, coverage, bindings)
        assert "duplicate" in str(refused.value)
        assert not hasattr(world, "merge") and not hasattr(world, "consolidate")


class TestR23Divergence:
    def test_a_run_in_the_other_corpus_claiming_the_dataset_diverges_and_moves_the_digest(self, tmp_path):
        """Negative (e), cross-corpus: R2 in BETA claims D (held once, in ALPHA)
        from B by edges alone — no second D record (spec §7)."""
        d0, r1, d1, _r2, _d2 = chain_nodes()
        b = stored.dataset_node("b", title="b")
        r2 = stored.run_node("r2x", title="r2x", spec="s", transforms=[b.id], produces=[d1.id])
        coverage = (ALPHA, BETA)
        roots = corpora(tmp_path, {ALPHA: (d0, r1, d1), BETA: (b, r2)})
        world = world_over(tmp_path, roots)
        bindings = hold_shipped(world)
        published = publish(world, coverage, bindings)
        view = open_world_view(world, published)

        snapshot = lineage_snapshot(view, [d1.id])
        assert divergence_state(snapshot, d1.id) == "divergent"
        certification = certify(snapshot, (d1.id,), (d0.id,))
        assert certification.state == "not-certified" and "lineage-divergent" in certification.findings
        with_r2 = snapshot_projection(snapshot)

        shutil.rmtree(roots[BETA]); (roots[BETA]).mkdir()
        roots_without = corpora(tmp_path / "without", {ALPHA: (d0, r1, d1), BETA: (b,)})
        world_without = world_over(tmp_path / "without", roots_without)
        published_without = publish(world_without, coverage, hold_shipped(world_without))
        without_r2 = snapshot_projection(lineage_snapshot(open_world_view(world_without, published_without), [d1.id]))
        assert with_r2 != without_r2  # the lineage member moves with the producer set
        assert _belief_digest(published) != _belief_digest(published_without)  # and so does kernel §5.1's digest: the snapshot covers the producer set
```

- [ ] **Step 2: Run them; measure rather than fix**

Run: `cd python && uv run --frozen pytest tests/test_world_relabels.py`
Expected: every test passes on the tree. Both rows assert kernel §5.1's `belief_input_digest` itself, through `test_relocation_rows._belief_digest` (a belief evaluated over the epoch's producer snapshot identity), never a proxy — a projection comparison would still pass if belief stopped incorporating the input (review finding 7). If the R23 arm **fails**, stop: the fix is to slice 1's code and is recorded in the results record under "corrections" (spec §7) — file `tasks note beliefs-46847c` with the failure before changing anything. If the coordinated-forgery arm's registry write is refused by the registry loader's content-name check, write the record with the exact `registry` codec (`admission_digest` names the file; `admission_projection` is its content) — the two calls above are those.

- [ ] **Step 3: Lint, commit**

```bash
uv run --frozen ruff check . && uv run --frozen pyright
cd .. && tasks note <task-8-id> "relabel fixtures pass on the tree: root move/rename/clone, coordinated forgery, raw-deleted admission, duplicate carriers; R23 (e) cross-corpus divergence measured"
tasks done <task-8-id> "X5, W13 and R23 divergence arms (spec §7)"
git add python/tests/test_world_relabels.py tasks
git commit -m "test(world): relabel arms for X5 and W13 and the measured cross-corpus divergence"
```

---
### Task 9: Durable arms, N2 declarations and the guard

**Files:**
- Create: `python/tests/acceptance/test_world_audit_acceptance.py`, `python/tests/acceptance/n2_arms_cut27.py` (canonical), `python/tests/acceptance/test_n2_cut27.py`

**Interfaces:**
- Consumes: `test_world_view_acceptance.durable_world` (the certified-volume two-corpus fixture; import it and `chain`), Tasks 2–8's public names, `n2_arms.Arm`/`Sabotage`, `test_n2.audit`/`baseline`, cut 26's guard as the template.
- Produces: `DECLARATION_UNITS = ("R23", "W8a", "X5", "W13", "S9")`, `CUT27_ARMS` (27 arms), `UNIT_CHECKS`, `unit_of`; the durable tests Task 10's runner names; the pins `CUT27_FREEZE_COMMIT`, `CUT27_FROZEN_SHA256`, `CUT27_DECLARATION_SHA256`.

- [ ] **Step 1: `tasks start <task-9-id>`, then write the durable arms**

Create `python/tests/acceptance/test_world_audit_acceptance.py`. It re-exercises, on the certified volume and through `beliefs.root`'s durable executors, one test per spec §8 bullet, each ending in `_durably`. Build each from the unit test of the same name in Tasks 2–8 by replacing `two_corpus_world`/`published_world` with `durable_world(alpha_nodes, beta_nodes)` (its fifth return is the two corpus ids; use them instead of `ALPHA`/`BETA`) and `repackage`/`exported` with copies written under `work_directory`. The required functions, one per bullet, with the assertion each carries:

| test | asserts |
|---|---|
| `test_the_literal_omission_is_malformed_and_the_consistent_one_refuted_durably` | Task 2's two omission arms through `import_epoch` into a replica world on the certified volume: `EpochImportRefused.reason` is `malformed-receipt` then `refuted-receipt`, nothing written either time |
| `test_every_coverage_declaration_must_agree_durably` | Task 2's three-way fixture: `malformed-receipt` with `A` standing and the binding held, availability reads stubbed to fail |
| `test_a_missing_receipt_a_corpus_state_and_a_bare_version_are_refused_durably` | `malformed-carrier`; `malformed-receipt` for a `corpus_states` entry naming a corpus id as its state and for `rule_identity: v1`, each decided with the replica holding no rule and mounting no corpus |
| `test_an_unresolvable_receipt_imports_with_a_finding_and_a_later_audit_evaluates_it_durably` | import into a replica missing corpus B: `receipt-unresolvable` ×4, `written`; mount B (reconfigure the replica over both roots, admit B) and `audit_epochs` reports `validated` ×4 |
| `test_a_moved_corpus_and_one_of_two_moving_are_unresolvable_durably` | a managed write to B after publication; `validate_receipt` → `unresolvable` naming B; A untouched |
| `test_a_fabricated_carrier_is_read_through_and_caught_only_under_audit_durably` | raw-write a carrier with a forged receipt into `epochs/`; `open_epoch` and `resolve_address` succeed with `validate_receipt` monkeypatched to raise; `audit_epochs` reports `receipt-malformed` |
| `test_an_all_malformed_snapshot_is_unchecked_with_a_finding_per_pair_durably` | Task 4's arm |
| `test_the_two_roads_to_unchecked_are_distinguishable_durably` | Task 4's arm |
| `test_a_validating_receipt_beside_a_malformed_one_is_checked_durably` | Task 4's arm, with `snapshot_state` agreeing with `audit_epochs` |
| `test_mounting_evaluates_nothing_and_the_three_callers_agree_durably` | `validate_receipt` monkeypatched to raise while `open_world`, `admit` and a rebuild run; then unpatched, `import_epoch`'s outcomes, `audit_epochs`'s and `snapshot_state`'s are equal for one carrier |
| `test_the_same_pair_moves_from_unresolvable_to_refuted_after_mount_and_audit_durably` | Task 3's unresolvable import with a consistent omission; mount B; `audit_epochs` → `refuted` |
| `test_the_unheld_rule_route_evaluates_after_installation_durably` | replica holds no rules: import with 4 findings; `hold_shipped`; audit → `validated` |
| `test_import_refuses_a_write_and_audit_and_query_write_nothing_durably` | byte inventories of the world root before/after each call |
| `test_an_unreadable_carrier_is_a_finding_and_the_next_carrier_is_still_evaluated_durably` | Task 4's arm |
| `test_a_built_epochs_anchors_are_corroborated_and_an_imported_ones_are_not_durably` | Task 4's arm |
| `test_a_damaged_carrier_is_reported_and_never_served_durably` | parametrized over the four S9 damages: Task 5's arm plus `audit_world`'s `corpus-damaged`, plus `validate_receipt` → `unresolvable` |
| `test_a_foreign_base_pin_is_base_pin_damage_durably` | Task 5's and Task 6's base-pin arms |
| `test_the_default_open_still_refuses_and_no_state_identity_is_taken_over_a_remainder_durably` | `CorpusStateMalformed` under `refuse`; with `registry.corpus_state_identity` monkeypatched to record its arguments, report mode calls it once on the damaged carrier (the strict attempt) and never again |
| `test_drift_absence_and_unreachable_recomputation_are_findings_durably` | Task 6's drift, absent and `derivation-unreachable` arms |
| `test_attestation_endpoints_and_shared_identifiers_are_findings_durably` | Task 7's three arms |
| `test_the_world_audit_reproduces_every_per_record_finding_durably` | a stale-stamped raw record: `audit_world`'s finding equals `audit_corpus`'s over the live root |
| `test_the_evaluator_answers_unresolvable_for_a_damaged_carrier_and_the_edge_is_indeterminate_durably` | Task 2's arm plus `read.coreference_edge(...).state == "indeterminate"` |
| `test_root_move_rename_and_clone_change_no_identity_durably` | Task 8's W13 root-move arm, asserting `_belief_digest` equality across every relocation |
| `test_a_coordinated_forgery_is_undetected_and_reads_as_a_fork_durably` | Task 8's arm |
| `test_two_carriers_of_one_id_refuse_the_build_durably` | Task 8's X5 arm |
| `test_a_cross_corpus_producer_diverges_and_moves_the_digest_durably` | Task 8's R23 arm, asserting `_belief_digest` inequality with and without `R2` |
| `test_open_refusals_never_become_absence_durably` | over a report-mode view: `CorpusDamaged` from every read of a damaged address, and `absent()`, `not_present` and the resolution snapshot's `not_present` input are empty for it |

Run: `cd python && uv run --frozen pytest tests/acceptance/test_world_audit_acceptance.py`
Expected: all pass on the certified volume (the `work_directory` fixture refuses elsewhere).

- [ ] **Step 2: The declaration module**

Create `python/tests/acceptance/n2_arms_cut27.py` on `n2_arms_cut24.py`'s shape (canonical in `tests/acceptance/`, imported by the guard directly — no `tests/` shim, since every arm is durable). Header:

```python
"""Cut 27 canonical declaration: R23, W8a, X5, W13 and S9 over the slice 3 seams."""

from n2_arms import Arm, Sabotage

DECLARATION_UNITS = ("R23", "W8a", "X5", "W13", "S9")

_A = "acceptance/test_world_audit_acceptance.py"

UNIT_CHECKS = {
    "R23": f"{_A}::test_the_literal_omission_is_malformed_and_the_consistent_one_refuted_durably",
    "W8a": f"{_A}::test_every_coverage_declaration_must_agree_durably",
    "X5": f"{_A}::test_two_carriers_of_one_id_refuse_the_build_durably",
    "W13": f"{_A}::test_root_move_rename_and_clone_change_no_identity_durably",
    "S9": f"{_A}::test_a_damaged_carrier_is_reported_and_never_served_durably",
}

CO_CITED = ()


def unit_of(row: str) -> str:
    """Rows are `<unit>` or `<unit>-<letter>`."""
    unit, hyphen, suffix = row.partition("-")
    if unit not in DECLARATION_UNITS or (hyphen and not (len(suffix) == 1 and suffix.islower())):
        raise ValueError(f"{row!r} is not a cut-27 row")
    return unit
```

Then `CUT27_ARMS`, 27 `Arm(...)` entries, each with a `Sabotage(module=..., before=<the exact source line(s) as landed>, after=<the mutation>)` and `checks=(<the durable test that fails under it>,)`. The mutations, by row (the `before` text is copied verbatim from the landed code at this point, which is why this module is written last):

- `W8a-a` `world/read.py`: move the `fault = _contract_fault(...)` call below the rule-binding resolution → `test_every_coverage_declaration_must_agree_durably`.
- `W8a-b` `world/read.py`: `if subject_coverage is not None and subject_coverage != declared:` → `if False:` (the receipt is compared with `coverage.yaml` only, the two-way check the third review refuted) → same check.
- `W8a-c` `world/read.py`: `if member_identity != receipt.subject_identity:` → `if False:` → `test_the_literal_omission_is_malformed_and_the_consistent_one_refuted_durably`.
- `W8a-d` `world/audit.py`: `_reduce`'s classification admits malformed evidence — `if any(outcome.outcome == "refuted" for outcome in well_formed):` → `if any(outcome.outcome in ("refuted", "malformed") for outcome in outcomes):` — so an all-malformed snapshot reads `contradicted` (dropping the `well_formed` filter alone changes nothing, since the two predicates name only `validated` and `refuted`; review finding 6) → `test_an_all_malformed_snapshot_is_unchecked_with_a_finding_per_pair_durably`.
- `W8a-e` `world/audit.py`: `unreadable.append((name, str(caught)))` → `continue` (skip silently) → `test_an_unreadable_carrier_is_a_finding_and_the_next_carrier_is_still_evaluated_durably`.
- `W8a-f` `world/read.py`: `except CorpusStateMalformed as caught:` → `except CoverageUnknown as caught:` (a class never raised there) → `test_the_evaluator_answers_unresolvable_for_a_damaged_carrier_and_the_edge_is_indeterminate_durably`.
- `W8a-g` `world/audit.py`: `except (EpochMalformed, OSError) as caught:` → `except EpochMalformed as caught:` → the unreadable-carrier test.
- `W8a-h` `world/audit.py`: `recorded = {... for record in view.log_heads}` → `recorded = {(anchors.CorpusSubject(a.subject), a.genesis_digest, a.head_digest) for e in opened.values() for a in e.anchors}` → `test_a_built_epochs_anchors_are_corroborated_and_an_imported_ones_are_not_durably`.
- `W8a-i` `world/importing.py`: append `CreateOp(f"epochs/{epoch.CURRENT_POINTER}", epoch._current_pointer_bytes(packaging_identity))` to the plan → `test_a_validated_carrier_...` durable counterpart (`test_import_refuses_a_write_and_audit_and_query_write_nothing_durably`).
- `W8a-j` `world/importing.py`: extend the plan with `epoch._locked_log_head_records(world_root, packaging_identity, members)` → the anchors test.
- `W8a-k` `world/importing.py`: `packaging_identity = epoch.packaging_identity_of(members)` → `packaging_identity = Path(source).name` → `test_a_missing_receipt_a_corpus_state_and_a_bare_version_are_refused_durably` (the export directory is named `export`, so the carrier is refused as malformed by the loader's name check instead of being admitted — choose a test whose export directory is named by the identity and asserts admission, e.g. the unresolvable-import test).
- `W8a-l` `world/importing.py`: `if carrier.world_anchor.subject != world.config.world_id:` → `if False:` → a durable foreign-world import test (add `test_a_carrier_of_another_world_is_refused_durably` to the acceptance module).
- `R23-a` `world/importing.py`: the refuted loop tuple loses `("refuted-receipt", "refuted")` → `test_the_literal_omission_is_malformed_and_the_consistent_one_refuted_durably`.
- `R23-b` `world/audit.py` `snapshot_state`: `for name in sorted(opened)` → `for name in sorted(opened)[-1:]` (the audited epoch alone) → `test_a_validating_receipt_beside_a_malformed_one_is_checked_durably`.
- `R23-c` `audit.py`: drop the `for uid in moved.unmapped:` findings → `test_drift_absence_and_unreachable_recomputation_are_findings_durably`.
- `R23-d` `audit.py`: `located = view.locate(endpoint)` → `located = Unknown(view.stamp) if view.resolve(endpoint) is None else located` shape (resolve corpus-locally: use `_located` on the holding corpus's live view) → `test_attestation_endpoints_and_shared_identifiers_are_findings_durably`.
- `R23-e` `audit.py`: `for scheme, value in normalized.items():` → `for scheme, value in [source_basis.basis(normalized)]:` (selected identifier only) → same test.
- `S9-a` `world/view.py`: `if on_damage == "refuse": raise` → `raise` unconditionally under `CorpusStateMalformed` → `test_a_damaged_carrier_is_reported_and_never_served_durably`.
- `S9-b` `world/view.py`: after `remainder, findings = _collecting_view(carrier)` add `states[corpus_id] = registry.corpus_state_identity(carrier)` guarded so it does not raise (e.g. `states[corpus_id] = "0" * 64`) and add the corpus to `captured` → `test_the_default_open_still_refuses_and_no_state_identity_is_taken_over_a_remainder_durably`.
- `S9-c` `world/view.py`: `_refuse_damaged` body → `return` → the damaged-carrier test.
- `S9-d` `corpus.py`/`audit.py`: `_CapturedCheckView(view.captured_records(corpus_id))` → `_CheckView(view.corpus_view(<a live address>))`-shaped live read; simplest mutant: `_record_findings(_CapturedCheckView(view.captured_records(corpus_id)), ...)` → `_record_findings(_CapturedCheckView(tuple(ReadView.opened_at(damaged_or_live_root).iter_stored())), ...)` → `test_the_world_audit_reproduces_every_per_record_finding_durably` with a post-capture raw write between open and audit (add that write to the test).
- `S9-e` `world/view.py`: `except ContractMismatch:` branch → capture records anyway (`view = ReadView(Corpus(carrier)); records = tuple(view.iter_stored())` path) → `test_a_foreign_base_pin_is_base_pin_damage_durably`.
- `S9-f` `audit.py`: `except CorpusDamaged:` in `_world_findings` → `except CoverageUnknown:` → `test_attestation_endpoints_and_shared_identifiers_are_findings_durably`.
- `S9-g` `audit.py`: `except CorpusDamaged as unreachable:` in the recomputation loop → `except CoverageUnknown as unreachable:` → the unreachable-recomputation test (`derivation-malformed` would be reported instead, or the exception escapes).
- `X5-a` `world/registry.py`: in `_carrier_roots`, `carriers.append(root)` → `if not carriers: carriers.append(root)` (two carriers collapse to one) → `test_two_carriers_of_one_id_refuse_the_build_durably`.
- `W13-a` `world/registry.py`: `corpus_state_identity`'s projection gains `"root": str(corpus_root)` → `test_root_move_rename_and_clone_change_no_identity_durably`.
- `W13-b` `world/epoch.py`: `_declared_coverage` (or the preflight's coverage projection) substitutes `Path(carrier).name` for the manifest's `corpus_id` → same test.

Every `before` must occur exactly once in its module — run `test_each_sabotage_names_one_real_source_site` (step 3) until it does. Twenty-seven arms; if a mutation cannot be made to fail exactly one durable test, add the durable test that isolates it rather than dropping the arm, and record the count in Task 11.

- [ ] **Step 3: The guard**

Create `python/tests/acceptance/test_n2_cut27.py` from `test_n2_cut26.py`: import `CUT27_ARMS, CO_CITED, DECLARATION_UNITS, unit_of` from `n2_arms_cut27`; add `from n2_arms_cut26 import CUT26_ARMS` to the prior imports and `*CUT26_ARMS` to `PRIOR_ARMS`; `FROZEN_CUT = REPO_ROOT / "docs" / "designs" / "2026-09-13-conformance-cut-27.md"`; `FROZEN_DECLARATION = "python/tests/acceptance/n2_arms_cut27.py"`. **Two commits are pinned, not one** (review finding 5): `CUT27_FREEZE_COMMIT` and `CUT27_FROZEN_SHA256` are Task 1's freeze commit and the cut document's digest there; `CUT27_DECLARATION_COMMIT` and `CUT27_DECLARATION_SHA256` are the commit step 4 makes and the declaration's digest there — the declaration did not exist at the freeze. `test_the_freeze_commit_and_sections_two_through_seven_are_pinned` reads the cut document from `CUT27_FREEZE_COMMIT` as cut 26's does; `test_the_declaration_is_byte_exact_against_the_freeze` becomes:

```python
def test_the_declaration_is_byte_exact_against_its_own_commit() -> None:
    """The arms the guard audits are the arms that were declared: the canonical
    table's bytes at HEAD equal its bytes at the declaring commit, which is
    an ancestor of HEAD and a descendant of the freeze."""
    for commit in (CUT27_FREEZE_COMMIT, CUT27_DECLARATION_COMMIT):
        assert subprocess.run(["git", "-C", str(REPO_ROOT), "merge-base", "--is-ancestor", commit, "HEAD"], check=False).returncode == 0, commit
    assert subprocess.run(["git", "-C", str(REPO_ROOT), "merge-base", "--is-ancestor", CUT27_FREEZE_COMMIT, CUT27_DECLARATION_COMMIT], check=False).returncode == 0
    current = (REPO_ROOT / FROZEN_DECLARATION).read_bytes()
    assert sha256(current).hexdigest() == CUT27_DECLARATION_SHA256
    assert current.decode("utf-8") == _show(CUT27_DECLARATION_COMMIT, FROZEN_DECLARATION)
``` `FROZEN_PRIOR_CUT_FILES` gains `"python/tests/n2_arms_cut26.py": "<the short sha that added it — git log --follow>"`. The inventory test asserts `DECLARATION_UNITS == ("R23", "W8a", "X5", "W13", "S9")`, 27 rows, and `unit_of` over every row. The pinned-sections test greps `"**5 declaration units**"`, `"Five guarantee rows are read, **3 full/closed** (X5, W13, S9)"` and `'("cut26_acceptance.py",)'`. The `nodes`-gate test is dropped (no `nodes` arm). The baseline/audit fixtures are unchanged; every arm's `sabotage.package` is `"beliefs"`.

- [ ] **Step 4: Pin the declaration, run the guard, commit**

```bash
git add python/tests/acceptance/n2_arms_cut27.py python/tests/acceptance/test_world_audit_acceptance.py
git commit -m "test(cut27): durable arms and the N2 declaration"
git rev-parse HEAD                                    # → CUT27_DECLARATION_COMMIT
sha256sum python/tests/acceptance/n2_arms_cut27.py    # → CUT27_DECLARATION_SHA256
```

Fill both into `test_n2_cut27.py`, then:

Run: `cd python && uv run --frozen pytest tests/acceptance/test_n2_cut27.py`
Expected: every guard test passes — including `test_every_arm_fails_under_its_own_sabotage` (27 sound findings) and the freeze pin.

```bash
uv run --frozen ruff check . && uv run --frozen pyright
cd .. && tasks note <task-9-id> "27 durable arms on the certified volume; n2_arms_cut27 declared and pinned; guard green"
tasks done <task-9-id> "cut 27 arms, declarations and guard"
git add python/tests tasks
git commit -m "test(cut27): the freeze guard and pins"
```

---
### Task 10: The runner, the status row and the dated notes

**Files:**
- Create: `python/tools/cut27_acceptance.py`
- Modify: `python/tools/roadmap_status.py:56` (add cut 27's row), `docs/designs/2026-08-02-world-addressing-design.md:1513` (W8a's cell, appended note) and `:1519` (W13's cell, appended note), `docs/designs/2026-08-03-redesign-adoption-ledger.md:279` (row 3's note, appended sentence), `docs/guide/identity-world-and-change.md:171-176`, `docs/guide/contracts-and-adoption.md:224-227`

- [ ] **Step 1: `tasks start <task-10-id>`, then write the runner**

Copy `python/tools/cut26_acceptance.py` to `cut27_acceptance.py` and change: the docstring to `"""Run cut 27 after cut 26 on the certified durable tuple."""`; `DEFAULT_WORK = PYTHON_ROOT.parent / ".cut27-acceptance"`; `PREFIX_RUNNERS = ("cut26_acceptance.py",)`; `PHASE_MODULES = ("test_world_audit_acceptance.py", "test_n2_cut27.py")`; the import to `from n2_arms_cut27 import CUT27_ARMS, DECLARATION_UNITS, unit_of` and the return to count `CUT27_ARMS`; `cut=27`. `declared_accounting` already puts `tests/acceptance` on `sys.path`, which is where the canonical module lives.

- [ ] **Step 2: The status tool's row**

In `python/tools/roadmap_status.py` after line 56 (`25: (...)`) add, in the tuple shape of the rows above it (source, closed rows, partial rows):

```python
    27: ("conformance-cut-27-results §2", "X5, W13, S9", "R23, W8a"),
```

If cut 26 has no row there, check how `test_designs_corpus.py` derives Appendix A from this table before adding one for 26 — only 27 is this task's.

- [ ] **Step 3: The row notes, the ledger note and the guide**

Each a dated addition; no existing words are removed.

- `2026-08-02-world-addressing-design.md:1513`, at the end of W8a's cell, after cut 24's note: ` **Read 2026-09-13 (cut 27, slice 3 design decision 3):** the audit publishes no correction; the correction is the explicit rebuild (`build_epoch`) its finding advises, and the audit's effect is its report. The arm's effectful/read-only split is read as import (refuses a write) versus audit and query (write nothing), the audit distinguished by domain — every retained pair — not by effect.`
- `2026-08-02-world-addressing-design.md:1519`, at the end of W13's cell: ` **Read 2026-09-13 (cut 27, slice 3 design §7):** the file-rename inertness clause ("rename a node's file without changing its uid or content identity … unchanged") is superseded by `nodes` 2.0 well-placedness — a moved node file is a placement fault the strict open refuses and the collecting audit reports as `path-mismatch` (S9). "Re-clone it and mount it at a second path" is read as mounting the clone instead; a second live carrier is this row's own uniqueness clause. Cut 6's replica-refusal half of X5 is superseded per the log-verification ledger's R34.`
- `2026-08-03-redesign-adoption-ledger.md:279`, appended to row 3's note: ` Audits over damaged corpora were selected by cut 27 (2026-09-13) as row S9 of the substrate design; manifest safety remains unowned.`
- `docs/guide/identity-world-and-change.md:171-176`: after the cut 25 sentence add "Cut 27 adds the explicit epoch import, the epoch audit with its snapshot-state query, and a world audit that judges the capture corpus by corpus and reports a damaged corpus rather than refusing it; view evaluation remains open." Add `- ../designs/2026-09-13-conformance-cut-27.md` to the page's `sources:` list.
- `docs/guide/contracts-and-adoption.md:224-227`: after the cut 26 sentence add "Cut 27 discharges world resolution slice 3 — R23's snapshot, import and divergence clauses, W8a's packaging arms, the X5 and W13 relabels and the new row S9 (`../designs/2026-09-13-conformance-cut-27.md`; `../plans/<date>-conformance-cut-27-results.md`)." — the results path is filled in Task 11.

- [ ] **Step 4: Run the guard sweeps and the whole runner**

Run: `cd python && uv run --frozen pytest tests/test_frozen_guards.py tests/test_arm_staleness.py tests/test_designs_corpus.py -p no:cacheprovider`
Expected: PASS.

Run: `cd python && uv run --frozen python tools/cut27_acceptance.py 2>&1 | tee ../.cut27-acceptance/run.log | tail -30`
Expected: exit 0; the prefix chain through cut 26 green; both phases green; the final line `declared arms: 27 (= 5 declaration units; 5 guarantee rows)`.

- [ ] **Step 5: Commit**

```bash
cd .. && tasks note <task-10-id> "runner cut27_acceptance.py green over the cut 26 prefix; roadmap_status row; W8a and W13 notes; ledger row 3 note; guide"
tasks done <task-10-id> "the cut 27 runner and the dated notes"
git add python/tools docs tasks
git commit -m "test(cut27): the acceptance runner, and the dated notes on W8a, W13 and the ledger"
```

---

### Task 11: Discharge

**Files:**
- Create: `docs/plans/<date>-conformance-cut-27-results.md` and `docs/plans/<date>-conformance-cut-27-run/{certified.log,check.log,test.log}` — the date is the day the gate runs; every `2026-09-XX` below is that date
- Modify: `docs/designs/2026-08-03-redesign-adoption-ledger.md` (`Updated`, the `Current state` heading date, the `world-resolution` row: R23's snapshot/divergence/import clauses and W13 leave it, W7/W8/W8b remain; the `packaging-remainder` row is **removed** — X5 is full and W8a's packaging arms are read, so the boundary leaves the open set as `domain-boundary` did at cut 26), `docs/plans/2026-08-29-implementation-roadmap.md` (whole rewrite per its header rule: `**Ranked at:** cut 27`, Appendix A regenerated by `python/tools/roadmap_status.py`, Appendix B rows narrowed — W8a keeps only its `instrument-certification` arm under `contract-cut`, R23 keeps only its rules-store clauses, X5 and W13 leave, S9 appears nowhere open — the tier-1 and ride-along tables drop `packaging-remainder`), `docs/designs/2026-09-13-conformance-cut-27.md` (`Status:` and §1's first sentence only), `docs/superpowers/specs/2026-09-13-world-resolution-slice-3-design.md` (`Status:` → discharged at cut 27, dated), this plan (`Status:`), `README.md` (the "latest discharged boundary" sentence → cut 27), `docs/guide/contracts-and-adoption.md` (the results path)

- [ ] **Step 1: `tasks start <task-11-id>`, then run the repository gates and retain the transcripts**

From the repository root:

```bash
mkdir -p docs/plans/2026-09-XX-conformance-cut-27-run
(cd python && uv run --frozen python tools/cut27_acceptance.py) > docs/plans/2026-09-XX-conformance-cut-27-run/certified.log 2>&1; echo "exit $?"
just check > docs/plans/2026-09-XX-conformance-cut-27-run/check.log 2>&1; echo "exit $?"
just test  > docs/plans/2026-09-XX-conformance-cut-27-run/test.log  2>&1; echo "exit $?"
grep -E "^[0-9]+ passed" docs/plans/2026-09-XX-conformance-cut-27-run/test.log
```
Expected: three `exit 0`; the pytest summary line and the vitest summary line name their counts. Claim the counts only from those lines.

- [ ] **Step 2: Write the results record**

Sections as cut 26's: `## 1. What ran` (the exact commands, exit codes, the prefix chain, per-phase counts, the `declared arms:` line, the transcript links); `## 2. Accounting and disposition` (X5, W13 and S9 close; R23 part on its rules-store clauses; W8a part on its `instrument-certification` arm; W8 and W8b retained, unselected; `packaging-remainder` closes; the global row count moves to 196 and the closed count by three); `## 3. Corrections and deviations from the frozen cut` (dated bullets: R23's literal omission fixture is now caught at the subject check and the reconstruction clause is read through the consistent fixture; the R23 (e) arm's measured result and any slice 1 fix it forced; the W13 clause readings of Task 10's note; any arm count other than 27); `## 4. Reproduction measurement` (no new mm30 run; cite cut 22's); `## 5. Remaining boundary` (`world-resolution` retains W7, W8, W8b and the filed dataset/history follow-ups; `contract-cut` retains R23's rules-store clauses and W8a's `instrument-certification` arm; manifest safety unowned); `## 6. Main integration` after the merge.

- [ ] **Step 3: Regenerate the roadmap's Appendix A and rewrite the ledger's Current state**

Run: `cd python && uv run --frozen python tools/roadmap_status.py` and paste its table; rewrite the roadmap whole per its header rule; update the ledger's `world-resolution` row, remove `packaging-remainder`, and update the summary; run `uv run --frozen pytest tests/test_designs_corpus.py -p no:cacheprovider` until green — `test_the_roadmap_and_ledger_name_the_same_boundaries` and `test_the_ledger_summary_names_the_newest_remaining_boundary` bind these documents to the record.

- [ ] **Step 4: Close the tasks and commit**

```bash
tasks done <task-11-id> "cut 27 discharged; results record docs/plans/2026-09-XX-conformance-cut-27-results.md"
tasks note beliefs-0e523a "from slice 3: W8 and W8b remain retained and unselected; audit both labels at slice 4's discharge (slice 3 design §11 item 3)"
tasks done beliefs-46847c "slice 3 discharged at cut 27: epoch import, epoch audit and query, world audit over damaged corpora; R23/W8a part, X5/W13/S9 closed; packaging-remainder closes"
tasks check
git add -A docs python/tests python/tools tasks README.md
git commit -m "docs(cut27): discharge conformance cut 27 and re-rank the roadmap"
```

Then merge `design/world-resolution-slice-3` into `main` with `--no-ff`, run `just gate` on `main`, record §6 of the results record, and remove the worktree per the roadmap's lane rules. `beliefs-d248ba` stays open: slice 4 and the two filed follow-ups remain.

---

## Review log

**2026-09-13, first review (user's reviewer), eight findings, all resolved.**
(1) A base-scope profile mismatch recorded an empty malformed set and the
recomputation loop read that as permission — `audit_world` now tracks an
`excluded` corpus set and skips it, with a test that patches `_recompute` to
raise (Task 6). (2) `_world_findings` decoded every attestation outside any
handler and without the Ω_valid classification — it takes `malformed` and
`excluded`, skips classified records and catches `MalformedRecord` (Task 7).
(3) `_locked_retained_directories` called `_emptied` before any catch, so an
unlistable carrier directory escaped — per-entry `OSError` is a finding; the
`epochs/` directory itself still refuses (Task 4). (4) Both collision fixtures
produced `path-mismatch` — `damage()` writes well-placed twins through
`raw_write`: a shared uid under a different live id, and a different uid whose
`deprecated_ids` claims the original's live id (Task 5). (5) The guard pinned
the declaration to the freeze commit, where it did not exist — two commits are
pinned, the declaration's own being a descendant of the freeze (Task 9). (6)
`W8a-d` removed a filter the two predicates never consulted — the mutant now
admits malformed evidence as `contradicted` (Task 9). (7) W13 and R23 compared
projections and identities — both assert `belief_input_digest` through
`test_relocation_rows._belief_digest`, unit and durable (Tasks 8, 9). (8) The
endpoint tests' negatives were wrong — the deleted endpoint stays unknown when
another corpus goes absent, and the repair happens in place on the same corpus
and epoch (Task 7).

**2026-09-13, second review, three fixture corrections.** The foreign-profile
test reuses the compiled `foreign_profile` fixture without changing the runtime's
shipped base, so it exercises the excluded-corpus branch rather than base-pin
damage (Task 6). The malformed attestation is published while valid, then
raw-edited with its mapped id and uid retained; the test asserts that the world
iteration reaches it and that the audit reports its stale stamp (Task 7). The
absent-endpoint test checks endpoint findings separately from the four required
receipt-unresolvable warnings (Task 7). The shared attestation helper supplies
the constructor's required title.
