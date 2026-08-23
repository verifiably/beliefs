# Log Verification and Anchoring (World-Index Slice 3) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the Science half of the tamper-evident mutation log — log-head records, the anchor act, head-artifact export, the four-outcome log evaluator behind audit and arrival boundaries, the world genesis↔mirror check, and the ordered-cuts predicate — discharging conformance cut 8.

**Architecture:** Two new modules in the `science/world/` package (`anchors.py` for the ruled record/artifact forms, `verify.py` for the evaluator, replay, and boundary cores), each act implemented as a private seam-injected core with a public wrapper in `science.root` — `science.root` already owns every atoms import and the `World` construction, and `science.world` never imports `science.root`. The atoms half goes first behind its own design gate in the atoms repository.

**Tech Stack:** Python 3.12, `uv` (frozen lockfile), pytest, ruff, pyright; the `atoms` engine as an editable path dependency.

**Spec:** `docs/superpowers/specs/2026-08-22-log-verification-design.md` (committed as a draft by Task 0; promoted to `docs/designs/` at banking). The frozen acceptance boundary is `docs/designs/2026-08-22-conformance-cut-8.md`.

## Global Constraints

- Gates for every Science task, run from `python/`: `uv run --frozen pytest` (no extra `-q` — `addopts` already sets it; count claims quote the summary line under `set -o pipefail`), `uv run --frozen ruff check`, and `uv run --frozen pyright` **project-wide** — the pyright gate passes iff the diagnostics are exactly the four known baseline diagnostics present at merge `83744e7`; any new diagnostic fails the gate.
- Stage only named paths. Never `git add -A`, never `git commit -a`.
- `atoms` is imported by `python/src/science/root.py` and nowhere else. `science/world/verify.py` and `science/world/anchors.py` receive engine capabilities only through the `LogSeam` callback bundle (Task 4); they never import `science.root`.
- The frozen cuts are never edited: cut 8 (`docs/designs/2026-08-22-conformance-cut-8.md`) after freeze commit `117f37e`, and cuts 5/6/7's runners and declarations, ever. Cut 8's status header alone changes at Task 12 (Discharged + results link).
- Durable acceptance artifacts live on the repository's own volume — never `/tmp`, `/dev/shm`, or the scratch volume.
- The execution rulings ledger is `docs/plans/2026-08-22-log-verification-ledger.md`, created and committed by Task 0, appended and **committed at every task boundary** — never left uncommitted in a removable worktree.
- Conventional commits; no AI-attribution trailers anywhere.
- The atoms repository is the local checkout Science's `atoms-core` editable path dependency resolves to; its work happens on its own branch there, merged `--no-ff` to its local `main` at Task 2's end. **One spec amendment rides Task 0** (recorded in the ledger): spec §8/§11's "merge-then-push" wording is clarified to what row 4 actually practices — the new head joins row 4's recorded **unpushed** disclosure, and pushing remains a prerequisite of any integration expecting a fresh checkout to build, exactly as for `read_chain`'s `2c077ed`. No push happens inside this plan.
- Domain strings are exactly `science.log-head.v1` and `science.head-artifact.v1`; nothing else new is minted.

---

### Task 0: Tracking setup

**Files:**
- Create: `docs/plans/2026-08-22-log-verification-ledger.md`
- Modify: `docs/superpowers/specs/2026-08-22-log-verification-design.md` (the push-wording clarification above, one sentence in §8 and §11)
- Commit (first tracking): the spec draft and this plan (`docs/superpowers/plans/2026-08-22-log-verification.md`) — both reviewed, both untracked until now

**Interfaces:**
- Produces: a committed spec (so Task 12's `git mv` has a tracked source) and a committed ledger skeleton (so no ruling ever lives only in a removable worktree).

- [ ] **Step 1:** Write the ledger skeleton: title, the plan/spec/cut paths, an empty `## Rulings` section, and a `## Heads` section for the atoms/science commit hashes this execution produces.
- [ ] **Step 2:** Apply the spec's push-wording clarification (§8: "the merge joins row 4's recorded unpushed disclosure; pushing remains a prerequisite of any fresh-checkout integration"; §11 step 4 the same), and record the amendment as ruling R1 in the ledger.
- [ ] **Step 3:** Commit all three: `git add docs/superpowers/specs/2026-08-22-log-verification-design.md docs/superpowers/plans/2026-08-22-log-verification.md docs/plans/2026-08-22-log-verification-ledger.md && git commit -m "docs(log): commit the slice-3 spec, plan, and execution ledger"`.

### Task 1: Atoms chain-inspection design (atoms repository — design gate)

**Files:**
- Create (atoms repo): `docs/plans/2026-08-22-chain-inspection-design.md` — atoms keeps its design corpus under `docs/plans/`, the public-chain-read design's convention

**Interfaces:**
- Produces: the reviewed contract Task 2 implements. No code.

- [ ] **Step 1:** In the atoms checkout, create a worktree `.worktrees/chain-inspection` on branch `design/chain-inspection`.
- [ ] **Step 2:** Write the design document covering exactly the four obligations of spec §2/§8, with these contracts pinned verbatim:
  - **Registered mode:** `inspect_chain(backend, project_root, metadata_root, storage) -> ChainInspection` — pinned order: project lock → structural inspection → malformed **returns** / well-formed runs recovery → inspect again.
  - **Detached mode:** `inspect_chain_detached(backend, project_root) -> ChainInspection` — read-only scan, **no metadata root and no storage profile in the signature** (an arriving root has neither), no recovery, pending honestly unresolved.
  - `ChainInspection = WellFormedChain(genesis_digest, entries, tip, pending) | MalformedChain(defect) | AbsentChain()`; `pending` is a tuple of `(txid, entry_digest)` pairs; `defect` is **one deterministic first defect** in the validator's fixed traversal order, from the fourteen-entry taxonomy of spec §2.1; the staging leaf is engine bookkeeping, never a foreign-leaf defect.
  - One typed validation core shared by both `inspect_chain` modes and the raising paths, so the defect taxonomy cannot fork. **Three defect classes are certified through the typed core only** (an injected entry map), never a fabricated directory, because each needs a digest fixed point or forward reference no content-named fixture can honestly construct: a **cycle**; an **orphan history** (a disconnected component with valid internal linkage — its other spellings land in missing-predecessor or non-genesis-root defects); and a **`fulfills` naming an existing non-ancestor** (in a linear chain every existing earlier entry is an ancestor, and a later digest depends on the referencing entry). The remaining twelve taxonomy entries retain directory cases — the `fulfills` entry through its missing and non-intent variants.
  - `capture_states(backend, root, paths)` returning `tuple[tuple[str, PathState], ...]` — exactly the spec §2.2 signature, nothing more.
  - The shared post-recovery pending gate: `register_root`'s existing-chain arm, `append_intent`, and `run_transaction` refuse with a new `PendingUnresolved` while an unsettled registration survives recovery.
- [ ] **Step 3:** Commit the design on the branch.
- [ ] **Step 4: STOP.** Hand the design to the human partner for the atoms-side review. Do not start Task 2 until the review closes; fold its findings first. Record the review's rulings in the Science-side ledger and commit it.

### Task 2: Atoms implementation — inspection core, capture, pending gate

**Files:**
- Create (atoms repo): `python/src/atoms/chain/inspect.py`, `python/tests/test_chain_inspect.py`, `python/tests/test_pending_gate.py`, `python/tests/test_capture_states.py`
- Modify (atoms repo): `python/src/atoms/coordinator/commands.py`, `python/src/atoms/chain/read.py`; create `python/src/atoms/chain/errors.py` (`PendingUnresolved`)

**Interfaces:**
- Consumes: Task 1's reviewed contracts.
- Produces (for Task 4's callbacks): `inspect_chain(backend, project_root, metadata_root, storage)`, `inspect_chain_detached(backend, project_root)`, `capture_states(backend, root, paths)`, `PendingUnresolved` — importable from `atoms.coordinator.commands` / `atoms.chain.inspect` / `atoms.chain.errors`.

- [ ] **Step 1: Write the failing structural tests** in `test_chain_inspect.py`: **twelve taxonomy entries retain directory cases — fourteen concrete fabrications** once zero/multiple genesis and the two fabricable `fulfills` variants are split (foreign leaf; name/bytes mismatch; undecodable entry; zero genesis; multiple genesis; missing predecessor; sibling branch; settlement without ancestor registration; settlement txid mismatch; duplicate settlement; duplicate registration per txid; `fulfills` missing; `fulfills` non-intent; duplicate committed fulfillment), each fabricating the defective chain directory and asserting `MalformedChain` with exactly that first defect; the three **core-only** classes (cycle; orphan history; `fulfills` naming an existing non-ancestor) against the typed core with injected entry maps; at least one **multi-defect chain** asserting the deterministic first defect by traversal order; well-formed, absent, pending-listing, and staging-leaf cases in both modes; the detached call on a root with no metadata directory at all; the registered-order probe (malformed chain: recovery entry point not invoked).
- [ ] **Step 2:** Run them: every one fails for want of `atoms.chain.inspect`.
- [ ] **Step 3: Implement the typed core** in `chain/inspect.py` (a collecting traversal parameterized to return-first-defect or raise), refactor `validate_chain` onto it, and add both `inspect_chain` modes to `commands.py`. Run Step 1's tests to green.
- [ ] **Step 4: Write the failing capture and gate tests**: `capture_states` round-trips all four state classes (absence, file content, directory, symlink target — plus mode on each present class) against fabricated disk state, and returns exactly the named paths; the pending gate fabricates an unsettled registration on a metadata-less root and asserts all three commands refuse `PendingUnresolved`, and that a settled chain does not refuse.
- [ ] **Step 5:** Run them; fail. Implement `capture_states` and the gate. Run to green.
- [ ] **Step 6:** Run the full atoms suite and its ruff/pyright gates; quote the summary line.
- [ ] **Step 7:** Commit on the branch; merge `--no-ff` to local atoms `main`. Record the new head hash in the Science ledger's `## Heads` (it joins row 4's unpushed disclosure at Task 12) and commit the ledger.

### Task 3: Science codecs — log-head record and head artifact

**Files:**
- Create: `python/src/science/world/anchors.py`, `python/tests/test_world_log_codecs.py`
- Modify: `python/src/science/world/registry.py` (record loader learns `record_kind: log-head`; **`RegistryView` gains `log_heads: tuple[LogHeadRecord, ...]`** — parsed records are carried, never discarded), `python/src/science/world/__init__.py` (re-exports)

**Interfaces:**
- Produces:
  - `CorpusSubject(corpus_id: str)`, `WorldSubject(world_id: str)`, `StoreSubject(store_id: str)`; `Subject = CorpusSubject | WorldSubject | StoreSubject`.
  - `LogHeadRecord(subject: CorpusSubject | StoreSubject, genesis: str, head: str, origin: BuildOrigin | AnchorActOrigin)` with `BuildOrigin(packaging_identity: str)`, `AnchorActOrigin(actor: str)`; `log_head_projection(record) -> dict`, `log_head_digest(record) -> str` under `science.log-head.v1`; YAML encode/decode behind `record_kind: log-head`.
  - `HeadArtifact(subject: Subject, genesis: str, head: str)`; `head_artifact_bytes(artifact) -> bytes`, `decode_head_artifact(data: bytes) -> HeadArtifact` under `science.head-artifact.v1`.
  - `RegistryView.log_heads` populated by the registry scan.

- [ ] **Step 1:** Write failing tests: encode/decode byte-stability for both codecs; digest stability against a pinned projection; store-arm round-trip in both codecs; world subject rejected by the record codec; malformed inputs refuse `ValueError`; a registry scan over a fixture root carrying one log-head record yields it in `RegistryView.log_heads` alongside admissions and statuses.
- [ ] **Step 2:** Run; fail. Implement, following `registry.py`'s grammar helpers (`_closed_mapping`, `_require_lower_hex`, the `record_kind` discriminant).
- [ ] **Step 3:** Run tests, then the three gates. Commit: `feat(world): log-head record and head-artifact codecs`. Append the ledger and commit it.

### Task 4: The seam — `logmodel`, `LogSeam`, root wrappers, presented identity, lock-only lookup

**Files:**
- Create: `python/src/science/world/logmodel.py` (Science-typed chain views — stdlib imports only)
- Modify: `python/src/science/world/verify.py` (create the module with the seam types), `python/src/science/root.py` (callbacks, view conversion, seam construction), `python/src/science/corpus.py` (`_operation_lock_for`), `python/src/science/world/registry.py` (the lock-only world lookup over `_WORLD_STATES`), `python/src/science/errors.py` (`LogEvidenceRefused` is defined here, in this task — the seam adapters raise it)
- Test: `python/tests/test_capability_boundary.py` (additions), `python/tests/test_corpus_write.py` (lock-lookup addition), `python/tests/test_world_log_codecs.py` (view-conversion additions)

**Interfaces:**
- Consumes: Task 2's atoms commands.
- Produces, in `logmodel.py` — the legal non-importing discrimination mechanism: **`science.root` converts every atoms inspection result into Science-owned view types before it crosses the seam**, and the state fingerprints inside are carried as **opaque values compared only by equality** (never re-encoded — L12's one-vocabulary rule is kept precisely because Science never constructs or interprets a state, it passes atoms's own objects through). **Two atoms forms, one opaque value:** chain entries carry `PathStateJSON`, while capture returns `PathState` — so root **decodes entry states with atoms's `state_from_json`** during view conversion, and capture states pass through unchanged; both sides of every replay comparison are then `PathState` values:
  - `ChainView = WellFormedView(genesis: GenesisEntryView, entries: tuple[EntryView, ...], tip: str, pending: tuple[tuple[str, str], ...]) | MalformedView(defect: DefectView) | AbsentView()`.
  - `EntryView = GenesisEntryView(digest: str, payload: bytes, baseline: tuple[tuple[str, object], ...]) | RegisteredEntryView(digest: str, txid: str, initial: tuple[tuple[str, object], ...], final: tuple[tuple[str, object], ...], fulfills: str | None) | SettledEntryView(digest: str, txid: str, registration: str, committed: bool) | IntentEntryView(digest: str, payload: bytes)` — the `object`-typed members are the atoms `PathState` values, opaque.
  - `DefectView(kind: DefectKind, subject: str | None, detail: str)` with `DefectKind = Literal["foreign-leaf", "name-mismatch", "undecodable-entry", "genesis-count", "missing-predecessor", "sibling-branch", "cycle", "orphan-history", "settlement-unregistered", "settlement-txid-mismatch", "duplicate-settlement", "duplicate-registration", "fulfills-invalid", "duplicate-fulfillment"]` — one member per taxonomy entry (the three `fulfills` reference variants share `fulfills-invalid`; zero and multiple genesis share `genesis-count`). The mapping is closed: `subject` is the offending chain-directory leaf name for `foreign-leaf`/`name-mismatch`/`undecodable-entry`, the entry digest whose linkage offends for `missing-predecessor` (the referencing entry), `sibling-branch` (the predecessor with two successors), `cycle` (one member of the offending cycle, deterministic under the pinned traversal), `orphan-history` (**the lowest unvisited digest**), the settlement digest for the three settlement defects, the second registration digest for `duplicate-registration`, **the second committed settlement digest** for `duplicate-fulfillment` (the defect exists only at the second committed settlement, per the atoms design's timing), the registration digest carrying the bad `fulfills` for `fulfills-invalid`, and `None` for `genesis-count`; `detail` is the atoms defect message verbatim.
  - `ChainHead(genesis_digest: str, genesis_payload: bytes, tip: str)` — the validated head read, **genesis payload included** so a world export can bind its subject to the configured/genesis `world_id`.
- Produces, in `verify.py`:
  - `LogSeam(inspect_registered: Callable[[Path], ChainView], inspect_detached: Callable[[Path], ChainView], capture: Callable[[Path, tuple[str, ...]], tuple[tuple[str, object], ...]], read_head: Callable[[Path], ChainHead], absent_state: object, world_lock: Callable[[Path], AbstractContextManager[None]], corpus_lock: Callable[[Path], OperationLock])` — a frozen dataclass; `absent_state` is the atoms `ABSENT` singleton passed through opaquely (replay's union-compare default); the seam's adapters **translate exactly three engine escapes** — `ChainStateInvalid` from a chain-vs-record contradiction, `TransactionHalted`, and capture's `PreconditionRefused` — into `LogEvidenceRefused(phase, engine_error, detail)` (spec §6.4; defined in `python/src/science/errors.py`), preserving `__cause__`; it produces no `LogReport`, is not `ArrivalRefused`, and sits outside every precedence; `ProtocolError` and setup errors pass through untranslated. `world_lock` yields holding the world root's lock, resolved through a new **lock-only world lookup backed by `_WORLD_STATES`** (`world/registry.py:174` — the corpus `_ROOT_STATES` and world `_WORLD_STATES` registries are separate, so `_operation_lock_for` cannot serve here), so audit locks a world it never opened and an opened `World` shares the identical lock object. **Every act core in Tasks 5–9 takes `seam: LogSeam`**, and `science.root` is the only constructor of a production seam.
  - `PresentedIdentity = PresentedManifest(corpus_id: str) | PresentedWorldIds(configured: str, mirrored: str | None)` — the typed identity input the evaluator's subject-mismatch findings compare against; state fingerprints alone cannot say what a manifest claims.
- Produces, elsewhere: `science.corpus._operation_lock_for(root: Path) -> OperationLock` — same registry as `_root_state_for`, no `Corpus` construction, usable over damaged node bytes; `science.root._log_seam() -> LogSeam` (private), consumed by the Task 5–9 public wrappers.

- [ ] **Step 1:** Write failing tests: the architecture assertion extends to the new atoms names (atoms imports only in `root.py`; `logmodel.py` imports stdlib only; `verify.py`/`anchors.py` import neither `atoms` nor `science.root` — assert over module `import` statements); the root-side conversion maps each atoms inspection variant to its view (well-formed, each defect kind, absent), with the **`is`-level assertion on a capture value** (pass-through unchanged) and an **equality assertion between a decoded entry state and the capture of the same disk state** (the `state_from_json` conversion meets capture in one comparable value); detached inspect over a fabricated metadata-less root returns rather than raises; the `TransactionHalted` adapter arm — a registered inspect whose engine escape is `TransactionHalted` surfaces as `LogEvidenceRefused(phase="inspect", engine_error="TransactionHalted")` with `__cause__` the engine exception (Tasks 8 and 9 cover the `ChainStateInvalid` and `PreconditionRefused` arms in context); `read_head` carries the genesis payload; `_operation_lock_for` returns the identical lock object `_root_state_for` later yields, and works on a root with an unparseable node file; the world lock-only lookup returns the identical lock object an opened `World` holds.
- [ ] **Step 2:** Run; fail. Implement `logmodel.py`, the conversion and callbacks in `root.py`, and the lock split.
- [ ] **Step 3:** Run tests and gates. Commit: `feat(root): the log seam, chain views, and the lock-only lookup`. Append and commit the ledger.

### Task 5: The anchor act, export, and build-origin records

**Files:**
- Modify: `python/src/science/world/anchors.py` (act cores), `python/src/science/root.py` (public wrappers `anchor_heads`, `export_head_artifact`), `python/src/science/world/epoch.py` (publication plan gains build-origin log-head `CreateOp`s), `python/src/science/errors.py` (the existing central errors module — no world/errors.py exists; `AnchorSubjectUnknown`, `AnchorTargetUnresolvable`)
- Test: `python/tests/test_world_anchor_act.py`

**Interfaces:**
- Consumes: Tasks 3–4.
- Produces:
  - `science.root.anchor_heads(world: World, corpus_ids: frozenset[str], *, actor: str) -> tuple[LogHeadRecord, ...]` (wrapping `anchors._anchor_heads(world, corpus_ids, actor=..., seam=...)`) — under the world lock; unknown id → `AnchorSubjectUnknown`; zero/multiple carriers → `AnchorTargetUnresolvable`; byte-identical existing record → skipped success, no transaction; same-name different bytes → collision refusal; terminal corpora anchorable.
  - `science.root.export_head_artifact(world: World, subject: CorpusSubject | WorldSubject) -> bytes` — **under the world lock, plus the corpus operation lock for a corpus subject** (both asserted by test); world-subject agreement with configuration and genesis or refusal; corpus subject under the exactly-one-carrier rule; no actor; no write.
  - Epoch publication writes `BuildOrigin` log-head records for every covered corpus.

- [ ] **Step 1:** Write failing tests: every refusal; the idempotency pair; export round-trip against the live tip; `World(W2)` refused over a W1 world; **the lock assertions** — export of a corpus subject holds both the world lock and that corpus's operation lock across the tip read (probe locks via `_operation_lock_for` and the world lock's holder state); publication leaves build-origin records beside the epoch.
- [ ] **Step 2:** Run; fail. Implement cores in `anchors.py`, wrappers in `root.py`.
- [ ] **Step 3:** Run tests and gates; run `uv run --frozen python tools/cut7_acceptance.py` (which chains cuts 5, 6, 7) to prove no frozen surface moved. Commit: `feat(world): anchor act, head export, and build-origin records`. Append and commit the ledger.

### Task 6: Projection, replay, and the policy pass

**Files:**
- Modify: `python/src/science/world/verify.py`
- Test: `python/tests/test_world_log_replay.py`

**Interfaces:**
- Consumes: Task 4's seam (`capture`, `absent_state`) and `logmodel` views — entry states already decoded to opaque `PathState` values by root's conversion, comparable by equality with capture output.
- Produces:
  - `registered_surface_paths(root: Path, kind: Literal["corpus", "world"]) -> tuple[str, ...]` — corpus: claimed node-layout paths plus `corpus.yaml`, excluding `.nodes-index`, the reserved log path, and engine bookkeeping; world: the registry/epoch/rules grammars plus `world.yaml`; no-follow enumeration.
  - `validate_history(history: Mapping[str, bytes]) -> None` — keys exactly `sha256:<64 lowercase hex>`; malformed key or key/bytes disagreement refuses `ValueError`. (Defined here; **called at evaluator entry by Task 7**, so corrupt history refuses even when evaluation stops before replay.)
  - `replay(view: WellFormedView, disk: tuple[tuple[str, object], ...], absent_state: object, history: Mapping[str, bytes] | None) -> ReplayResult` with `ReplayResult(refuted: bool, disagreements: tuple[str, ...], findings: tuple[Finding, ...])` — committed registrations only; initial-fingerprint check each step by opaque equality; union-compare over replay-known and disk-discovered claimed paths with unknown-replay-state as `absent_state`; removal findings for every committed removal of a claimed record path; failing-verification classification only where `history` resolves, the finding naming the matched digest.

- [ ] **Step 1:** Write failing tests: projection contents on fixture corpus and world roots (symlink not followed; `.nodes-index` excluded); replay validates a fabricated committed history against its matching disk; raw-delete refutes; raw-create refutes; rolled-back creation's absence does not refute; removal finding with and without `history`; classification digest named when history resolves; `validate_history` refusals (bad key form; bytes not hashing to key).
- [ ] **Step 2:** Run; fail. Implement.
- [ ] **Step 3:** Run tests and gates. Commit: `feat(world): registered-surface replay and the removal policy pass`. Append and commit the ledger.

### Task 7: The evaluator

**Files:**
- Modify: `python/src/science/world/verify.py`, `python/src/science/errors.py` (`StoreSubjectUnsupported`, `ObserverCarrierInvalid`)
- Test: `python/tests/test_world_log_evaluator.py`

**Interfaces:**
- Consumes: Tasks 3–6.
- Produces:
  - **Authority-derived carrier factories** — carriers are constructible only through factories that retain their validation evidence, and **provenance is never a parameter**: each factory fixes it from the authority it reads. `RegistryCarrier.from_record(record: LogHeadRecord)` (grammar-checked on entry); `EpochCarrier.from_named_local(epoch_root: Path)` — reads the eleven members from the world root's own epoch directory, revalidates the packaging identity, and fixes provenance `named-local` internally; `EpochCarrier.from_export(members: Mapping[str, bytes], packaging_identity: str)` — takes the **complete member mapping** (packaging identity covers all eleven members, so one `bytes` value could never revalidate it), revalidates, and fixes provenance `supplied-export` internally; `ArtifactCarrier.from_bytes(data: bytes)` (codec-validated, canonical bytes retained). Every factory refuses `ObserverCarrierInvalid` on failure; direct dataclass construction is unspellable outside the module (module-private `__init__` guard). The factories fix the **discriminator** — no parameter exists to mislabel — but a factory name cannot prove external custody: a caller could still read local epoch members and hand them to `from_export`, so `supplied-export` remains **caller-attested custody evidence under the deferred holder protocol** (spec §10.9), stated as such in the report's observer bound.
  - `ObserverSet(carriers: tuple[RegistryCarrier | EpochCarrier | ArtifactCarrier, ...])`.
  - `evaluate_log(subject: Subject, view: ChainView, observers: ObserverSet, disk: tuple[tuple[str, object], ...], presented: PresentedIdentity | None, absent_state: object, history: Mapping[str, bytes] | None = None) -> LogReport` with `LogReport(outcome: Literal["validated","refuted","unresolvable","malformed"], anchored_through: str | None, unanchored_tail: tuple[str, ...], pending: tuple[tuple[str, str], ...], intents_unevaluated: tuple[str, ...], observer_bound: tuple[str, ...], findings: tuple[Finding, ...])`.
  - Behavior: `validate_history` at entry, before anything; `StoreSubject` → `StoreSubjectUnsupported`; then precedence exactly spec §4.2 — structure (genesis-form validation: payload form per subject kind, empty baseline; a valid world genesis naming a different id is a subject-mismatch finding against `presented`, never malformed) → anchors (subject filter first; world subject accepts only supplied-export epochs and artifacts; absent → refuted-removal; genesis mismatch → refuted-replacement; unreachable/incomparable → refuted; empty `S`-bound set → unresolvable) → pending → replay. Subject-mismatch findings compare `presented` against `S` and the genesis; they never filter anchors.

- [ ] **Step 1: Write the failing precedence tests**, one per exit in order: malformed stops at step 1 with the defect named; genesis-form malformation (wrong payload form; non-empty baseline); the world-id-different subject-mismatch split; absent-chain refutation against a surviving anchor; genesis-mismatch replacement (world subject); ancestry unreachability; incomparable pair; empty-set unresolvable with bound recorded; pending unresolvable with replay not reached (probe: replay not invoked); replay refutation pass-through; the validated exit with tail extent.
- [ ] **Step 2: Write the failing carrier tests**: each factory's refusal on invalid input; the packaging-identity revalidation (edit one member byte after construction inputs → `ObserverCarrierInvalid`); direct construction unspellable; the L11 eligibility square (in-root vs supplied epoch × corpus vs world subject).
- [ ] **Step 3: Write the failing history-early-exit test**: corrupt `history` plus a malformed chain → the act refuses on history **before** any outcome is produced.
- [ ] **Step 4:** Run; fail. Implement carriers, then `evaluate_log`. Run to green.
- [ ] **Step 5:** Run gates. Commit: `feat(world): the four-outcome log evaluator`. Append and commit the ledger.

### Task 8: Audit and the ordered-cuts predicate

**Files:**
- Modify: `python/src/science/world/verify.py` (cores), `python/src/science/root.py` (public wrappers `audit_log`, `epochs_ordered`)
- Test: `python/tests/test_world_log_audit.py`

**Interfaces:**
- Consumes: Tasks 4–7.
- Produces:
  - `science.root.audit_log(config: WorldConfig, subject: Subject, target_root: Path, observers: ObserverSet, *, actor: str, history=None) -> LogReport` — wraps `verify._audit_log(..., seam=...)`; target root must be configured, never associated by manifest; corpus audit under `seam.corpus_lock(target_root)`, world audit under the world lock, across inspection and capture; constructed from `config` directly (no `open_world`), so it runs on worlds `open_world` refuses; writes nothing.
  - `science.root.epochs_ordered(config: WorldConfig, e1: str, e2: str) -> Literal["ordered", "unordered"]` — ordered iff e2's build-start world head descends by ancestry from e1's settled committed publication entry; missing or rolled-back publication → unordered.

- [ ] **Step 1:** Write failing tests: audit over a corpus with damaged node bytes (lock obtainable, verdict returned); audit of a world whose configured id disagrees with genesis (callable; subject-mismatch finding in the report); an unconfigured target root refused; `epochs_ordered` over two sequentially built epochs → ordered; over a fabricated rolled-back publication → unordered, asserted by entry class (cut §6's freeze obligation); the no-sequence-numbers architecture assertion; and the `LogEvidenceRefused` translation at audit — a fabricated chain-vs-record contradiction (empty chain beside a live record fixture) refuses with phase `inspect` and `__cause__` preserved, producing no report.
- [ ] **Step 2:** Run; fail. Implement cores and wrappers.
- [ ] **Step 3:** Run tests and gates. Commit: `feat(world): the audit act and the ordered-cuts predicate`. Append and commit the ledger.

### Task 9: Arrival and the open-world agreement check

**Files:**
- Modify: `python/src/science/world/registry.py` (`World.admit` refuses `ReplicaOf`; the shared admission core split), `python/src/science/root.py` (`open_world` at root.py:636 gains the genesis/configuration/mirror agreement check; public wrapper `admit_arrival`), `python/src/science/world/verify.py` (`_admit_arrival` core), `python/src/science/errors.py` (`ReplicaAdmissionRequiresVerification`, `ArrivalRefused`, `SubjectMismatch`)
- Test: `python/tests/test_world_arrival.py`

**Interfaces:**
- Consumes: Tasks 4, 7.
- Produces:
  - `World.admit(..., provenance=ReplicaOf(...))` → raises `ReplicaAdmissionRequiresVerification`.
  - `science.root.admit_arrival(world: World, corpus_root: Path, provenance: ReplicaOf, observers: ObserverSet, *, actor: str, history=None) -> tuple[AdmissionRecord, LogReport]` — manifest loaded internally under the arriving root's lock (via `seam.corpus_lock`); `S = CorpusSubject(provenance.parent_corpus_id)`; detached inspection; cause ranking `malformed > refuted > pending > chainless` derived from report fields (`ArrivalRefused` carries the complete report and the closed cause); `AbsentView` + empty observers → `chainless`; empty observers admissible only for a `WellFormedView` with empty pending; `SubjectMismatch` checked after report causes and before the admission transaction; committed through the shared admission core so `AdmissionRecord` identity is byte-identical to a fixture admission of the same inputs.
  - `open_world` refuses `WorldIdMismatch` when genesis payload, configuration, and `world.yaml` disagree.

- [ ] **Step 1:** Write failing tests: each cause in rank order, plus the ranking case (a chain both pending and mismatched refuses `pending`); the chainless refusal; the unanchored admissible arrival (bound recorded in the returned report; admission identity byte-identical to fixture); bare `admit` refusal; the L10 arrival-identity case (fresh manifest over the parent's chain → `SubjectMismatch`); `open_world` refusing a mirror edit while `audit_log` still runs on the same world; and the `LogEvidenceRefused` translation at arrival — a device node planted at a modeled path refuses with phase `capture`, `__cause__` preserved, no report and no admission.
- [ ] **Step 2:** Run; fail. Implement.
- [ ] **Step 3:** Run tests and gates; rerun `tools/cut7_acceptance.py` (admission surface moved). Commit: `feat(world): verified arrival and the open-world agreement check`. Append and commit the ledger.

### Task 10: The 53 N2 declarations

**Files:**
- Create: `python/tests/acceptance/n2_arms_cut8.py`, `python/tests/acceptance/test_n2_cut8.py`

**Interfaces:**
- Consumes: every check node in the table below. Tasks 3–9 create them; where a table-named node is missing, this task adds it **to the file the table names** — that is this task's license, and its only one.
- Produces: the declared-arms data (53 units) and the audit harness, cut-7 pattern: `vacuous`, `uncollected`, `stale` reported as malformed contract content.

- [ ] **Step 1:** Declare all 53 units as data with these exact check nodes:

| unit | check node |
|---|---|
| L1u1 | `test_capability_boundary.py::test_no_cooperative_mutation_path_skips_registration` |
| L2u1 | `test_world_log_replay.py::test_rolled_back_creation_absence_is_not_refuted` |
| L2u2 | `test_world_log_replay.py::test_committed_creation_raw_deleted_is_refuted` |
| L2u3 | `test_world_log_evaluator.py::test_duplicate_settlement_is_malformed_at_step_one` |
| L2u4 | `test_world_log_evaluator.py::test_copied_root_pending_is_unresolvable_in_both_variants` |
| L2u5 | `test_world_arrival.py::test_pending_root_refuses_further_mutation_via_the_gate` |
| L3u1 | `test_world_log_evaluator.py::test_valid_prefix_truncation_refutes_naming_the_unreachable_head` |
| L3u2 | `test_world_log_evaluator.py::test_interior_damage_is_malformed` |
| L3u3 | `test_world_log_evaluator.py::test_sibling_branch_is_malformed` |
| L3u4 | `test_world_log_evaluator.py::test_orphan_entry_is_malformed` |
| L4u1 | `test_world_log_evaluator.py::test_chain_deletion_refutes_against_a_registry_anchor` |
| L4u2 | `test_world_log_evaluator.py::test_two_anchored_corpora_refute_exactly_the_chainless_one` |
| L4u3 | `test_world_log_evaluator.py::test_manifest_remint_reports_mismatch_and_replay_refutes` |
| L4u4 | `test_world_log_audit.py::test_edited_world_configuration_mismatch_and_refusal` |
| L4u5 | `test_world_log_evaluator.py::test_same_genesis_alternative_chain_refutes_by_ancestry` |
| L4u6 | `test_world_log_audit.py::test_exported_w1_head_refutes_rewritten_world` |
| L4u7 | `test_world_log_evaluator.py::test_deletion_plus_remint_refutes_as_removal_under_selected_subject` |
| L5u1 | `test_world_log_replay.py::test_consistent_tail_rewrite_beyond_anchor_validates` |
| L5u2 | `test_world_log_replay.py::test_unanchored_tail_extent_covers_the_rewrite` |
| L7u1 | `test_world_log_evaluator.py::test_fulfills_naming_missing_or_nonancestor_intent_is_malformed` |
| L7u2 | `test_world_log_evaluator.py::test_duplicate_committed_fulfillment_is_malformed` |
| L8u1 | `test_world_log_audit.py::test_epochs_ordered_by_descent_and_unordered_without_settled_publication` |
| L8u2 | `test_world_log_audit.py::test_epoch_sequence_numbers_are_read_by_nothing` |
| L9u1 | `test_world_log_evaluator.py::test_old_anchor_never_validates_past_a_missing_newer_head` |
| L9u2 | `test_world_log_evaluator.py::test_incomparable_anchored_heads_refute` |
| L9u3 | `test_world_log_evaluator.py::test_empty_observer_set_is_unresolvable_with_bound_recorded` |
| L9u4 | `test_world_log_evaluator.py::test_anchored_through_and_observer_set_are_report_fields` |
| L9u5 | `test_world_log_evaluator.py::test_malformed_structure_stops_before_anchor_judgment` |
| L10u1 | `test_world_arrival.py::test_fresh_manifest_over_parent_chain_refuses_subject_mismatch` |
| L11u1 | `test_world_log_evaluator.py::test_in_root_epoch_ineligible_for_world_subject_but_eligible_for_corpus` |
| L11u2 | `test_world_log_codecs.py::test_world_subject_registry_record_is_unconstructible` |
| L11u3 | `test_world_log_audit.py::test_coordinated_truncation_without_exported_holder_is_undetected` |
| L11u4 | `test_world_log_audit.py::test_coordinated_truncation_with_one_exported_epoch_refutes` |
| L12u1 | `test_world_log_replay.py::test_all_four_state_classes_round_trip` |
| L12u2 | `test_capability_boundary.py::test_science_fingerprints_only_through_the_capture_command` |
| L12u3 | `test_world_log_replay.py::test_log_appends_are_not_recursively_registered` |
| L12u4 | `test_world_log_evaluator.py::test_raw_log_edit_within_anchored_prefix_is_malformed_or_refuted` |
| L12u5 | `test_world_log_evaluator.py::test_valid_raw_append_beyond_anchor_passes_as_the_residue` |
| L13u1 | `test_world_log_replay.py::test_cooperative_verification_removal_is_in_timeline_with_finding` |
| L13u2 | `test_world_log_replay.py::test_failing_classification_resolves_through_history_naming_digest` |
| L13u3 | `test_world_log_replay.py::test_without_history_deletion_detected_classification_absent` |
| L13u4 | `test_world_arrival.py::test_retirement_appends_status_and_deletes_nothing` |
| L13u5 | `test_world_log_codecs.py::test_no_entry_class_records_preimage_gc` |
| D1 | `test_world_log_evaluator.py::test_genesis_form_malformation_and_world_id_mismatch_split` |
| D2 | `test_world_arrival.py::test_arrival_cause_ranking_from_report_fields` |
| D3 | `test_world_arrival.py::test_bare_admit_refusal_and_shared_core_identity` |
| D4 | `test_world_arrival.py::test_refusal_ordering_report_causes_then_mismatch_then_admission` |
| D5 | `test_world_log_audit.py::test_mirror_branch_refuses_open_world_and_audit_stays_callable` |
| D6 | `test_world_log_codecs.py::test_store_subject_shape_only_across_codecs_and_evaluator` |
| D7 | `test_world_anchor_act.py::test_export_binds_subject_and_takes_no_actor` |
| D8 | `test_world_anchor_act.py::test_anchor_act_refusals_idempotency_and_terminal_corpora` |
| D9 | `test_world_log_replay.py::test_history_validation_refusals_and_digest_named_findings` |
| D10 | `test_world_log_audit.py::test_one_evaluator_one_inspection_contract` |

- [ ] **Step 2: Implement the harness** with cut-8 §5's declaration-time obligations 1–6 plus both §6 freeze obligations as declaration-time assertions: fabrication well-formedness (every fabricated chain inspects well-formed unless the arm's declared defect class is the point, then exactly that one defect); L2u1's entry-class and path-absence assertion; L5u1's byte-difference-beyond-anchor assertion; L4u2's two-distinct-roots assertion; L11u3's all-three-carriers-truncated assertion; L12u1's all-four-classes assertion; L4u3's no-other-delta assertion; L8u1's entry-class assertion. (§5's obligation 7 — summary-line accounting — is Task 12's, where the counts are claimed.)
- [ ] **Step 3:** Run the audit over a copy of the package; every one of the 53 arms resolves `sound`. Fix any `vacuous`/`uncollected`/`stale` as harness or Task 3–9 defects, never by editing the frozen cut.
- [ ] **Step 4:** Run all gates; quote the summary line. Commit: `test(cut8): declare the 53 frozen arms`. Append and commit the ledger.

### Task 11: Certified acceptance

**Files:**
- Create: `python/tools/cut8_acceptance.py`
- Modify: `.gitignore` (add the cut-8 run directory, closing the cut-7 results' noted gap for interrupted runs)

**Interfaces:**
- Consumes: Task 10's harness.
- Produces: the runner — **`cut7_acceptance.py` as the sole prior-cut prefix** (it already chains cuts 5, 6, 7; invoking 5 or 6 again would run them twice), then the cut-8 N2 audit; exit 0 only on all green; run directories on the repository volume, removed in `finally`.

- [ ] **Step 1:** Implement the runner mirroring `tools/cut7_acceptance.py`'s structure (same exit-code discipline; the `PROBE_REFUSED` docstring corrected per cut-7 results §8 — do not claim distinctness from pytest's own exit code 2).
- [ ] **Step 2:** Run it: exit 0, with the four counts (39 / 23 / 42 / 53) quoted from its output.
- [ ] **Step 3:** Run the full suite and gates; quote the summary line. Commit: `test(cut8): certified acceptance runner`. Append and commit the ledger.

### Task 12: Results record, banking, and close-out

**Files:**
- Create: `docs/plans/2026-08-22-conformance-cut-8-results.md`
- Modify: `docs/designs/2026-08-03-tamper-evident-log-design.md` (§1.2/§1.3 amendments, dated); `docs/designs/2026-08-20-world-registry-design.md` (the admission-algorithm section, ~:490–508: `World.admit` now refuses `ReplicaOf` outright with `ReplicaAdmissionRequiresVerification`, before the lock and before the known-id refusal, so "known ids are refused uniformly … `replica-of` describes the first arrival" no longer describes the bare-admit path — replica arrival is `admit_arrival`'s, and cut 6's X5 replica clause is superseded per ledger R34); `docs/designs/2026-08-03-redesign-adoption-ledger.md` (rows 4 and 5); `docs/designs/2026-08-22-conformance-cut-8.md` **status header only**; `docs/designs/2026-08-02-epistemic-kernel-design.md` (the §8.7 status line); `README.md`; `docs/guide/contracts-and-adoption.md`, `docs/guide/identity-world-and-change.md`, `docs/guide/foundations.md`, `docs/guide/open-questions.md` (citations, stale-claim corrections, `updated:` stamps to the landing date); promote the spec via `git mv docs/superpowers/specs/2026-08-22-log-verification-design.md docs/designs/2026-08-22-log-verification-design.md` (tracked since Task 0; `git mv` stages both halves — do not `git add` the moved-away path).
- Finalize: `docs/plans/2026-08-22-log-verification-ledger.md`.

**Interfaces:**
- Consumes: everything above, green.

- [ ] **Step 1: Write the results record** on the cut-6/7 pattern: the discharge statement, the certified tuple, per-row dispositions (5 full, 7 partial, L6 unread with §3.2's justification restated, L10's arrival arm), known limitations honestly recorded, and corrections to banked text if any surfaced during execution. Leave the evidence block empty until Step 4 — evidence recorded before the tree stops moving is not evidence of the final tree.
- [ ] **Step 2: Apply the banking amendment set** from the spec's header: the log design's §3/§5/§6 genesis-subject clauses and affected L4/L10 arm mechanisms (§1.2), its L6 constructibility note (§1.3); ledger row 5 (carriage **and** verification landed; the remainder named: intent qualification/G4, the preimage resolver, event-level L8, L10's row-4 arms); ledger row 4 (the three new atoms APIs; the new unpushed atoms head from the Task 2 ledger entry, disclosed exactly as `2c077ed` was); the kernel §8.7 status line (three of the four recorded-mutation consequences closed at discharge — G8, semantic identity, 5a — with G4 waiting on the intent boundary and chronology boundary-mediated as banked); the spec promotion via `git mv`. **Amend the slice-3 spec itself before promoting it**, from the ledger's execution rulings: **§5.3** — the held-copy match is by path, not digest, because the seam exposes no state→digest accessor (R16), stated as a second reason L13 is partial and disclosed in the results record; **§7** — `epochs_ordered` takes a `WorldConfig`, not a `World`, since the predicate must answer where `open_world` refuses (R33). A promoted design document must not bank a claim the code contradicts.
- [ ] **Step 3: Sweep for propagated stale claims** — `rg -n "L1–L13 await|anchor act|verification remain|not yet buildable|unanchored registry" README.md docs/guide/ docs/designs/2026-08-03-redesign-adoption-ledger.md` — and correct every hit that the landing makes false; move the touched guides' `updated:` stamps to the landing date.
- [ ] **Step 4: Collect the evidence, now that the tree is final.** Each under `set -o pipefail`: the full suite (`uv run --frozen pytest` — paste the actual `N passed` summary line), `tools/cut8_acceptance.py` (exit 0; record the counts **as the runner prints them and say what each is**: cut 5 `39 passed`, cut 6 `23 passed`, cut 7 N2 `42 passed`, and cut 8's phase — whose pytest line is `76 passed`, covering the 53-arm sabotage audit plus the inventory, obligation, freeze and guard checks. **53 is the declared-unit count** (`len(CUT8_ARMS)`, pinned by the inventory test), not a pytest total; the results record must not present it as one), the corpus guard's summary line, and `tools/check_guide.py` recorded as **exit 0** (it emits no `N passed` line). Paste all four into the results record's evidence block — this is cut-8 §5's obligation 7, homed here.
- [ ] **Step 5:** Finalize the ledger (complete rulings list, final heads) and commit it **before any cleanup**. Commit the banking change. The branch is ready for the `--no-ff` merge — the merge itself is the human partner's act, as before.
