# Root Lifecycle and the Store Substrate (World-Index Slice 4) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement world-index slice 4 — the fail-closed writer state, the
atoms lifecycle commands, store subjects through the verification surface,
`restore_root`, and the fork acts — discharging frozen conformance cut 9.

**Architecture:** An atoms design gate ships five root-kind-agnostic
obligations (three mutating lifecycle commands, one state query, one
migration) plus the fork's source-snapshot binding; Science consumes them
through `science.root`'s callback seam (the only atoms importer), widens
the slice-3 verification surface to store subjects, and builds
`restore_root` and the fork acts on top. Every claim is certified as one of
cut 9's 30 frozen declaration units.

**Tech Stack:** Python 3 (`uv run --frozen`, cwd `python/`), pytest, the
certified `atoms` engine (editable path dependency at the sibling
checkout `~/d/atoms`; imported as `atoms.*`, confined to
`science/root.py`), the N2 declaration harness
(`tests/acceptance/n2_arms_cut8.py` + `tests/acceptance/test_n2_cut8.py`
are the pattern), `tools/cutN_acceptance.py` runners.

**Spec:** `docs/superpowers/specs/2026-08-23-world-index-root-lifecycle-design.md`
**Frozen cut:** `docs/designs/2026-08-23-conformance-cut-9.md` (frozen at
`0977bde`; the cut's §3 declarations are the acceptance criteria — read
both before any task).

## Global Constraints

- The frozen cut is not edited; only its status header may change, at
  discharge. `uv run --frozen python tools/cut7_acceptance.py` (which
  chains cuts 5–6) must stay exit 0 after every Science task.
  **Cut 8's runner is a current-tree prefix only through Task 3:** Task
  4 removes the store refusal cut 8's declarations sabotage against and
  assert, so from Task 4 on those declarations fail **by design** — a
  ledger ruling records it there, and cut 8's discharge stands as its
  frozen results record
  (`docs/plans/2026-08-22-conformance-cut-8-results.md`), not as a
  current-tree invariant. Cut 9 runs against the successor tree with no
  current-tree cut-8 prefix (Task 10).
- `science/root.py` stays the only module importing `atoms`;
  `tests/test_capability_boundary.py` enforces this and its
  `test_the_composition_root_names_every_engine_command` node must be
  extended with every new engine command name, never weakened.
- Durable arms live on the repository's own volume — never `/tmp`, the
  scratch volume, or `/dev/shm`. Reuse
  `tests/acceptance/durable_fixture.py`.
- Every count claim quotes pytest's own summary line under `pipefail` —
  never a collect-only count (addopts already sets `-q`; do not double
  it, and never `| tail` without `set -o pipefail`).
- Atoms is root-kind agnostic: it stores lifecycle state and opaque
  genesis bytes; Science owns `corpus`/`world`/`store` payload
  construction and validation. No Science vocabulary (verdicts, subjects)
  enters atoms.
- The Science gate block, run from `python/` after every green step
  (addopts already supplies `-q` and `--ignore=tests/acceptance`;
  acceptance files run only by explicit node id):
  `uv run --frozen pytest && uv run --frozen ruff check . && uv run --frozen pyright`
- Conventional commits; no AI-attribution trailers. After every task:
  append the execution ledger (rulings + the task's head commit) and
  commit it with the task.

---

### Task 0: Tracking setup

**Files:**
- Create: `docs/plans/2026-08-23-root-lifecycle-ledger.md`

**Interfaces:**
- Produces: the execution ledger every later task appends to — a tracked,
  durable path (slice 2 lost R1–R15 to an untracked one; never relocate
  it).

- [ ] **Step 1:** Write the ledger skeleton: title ("Root lifecycle —
  execution ledger, world-index slice 4"), the plan/spec/cut paths with
  the freeze hash `0977bde`, an empty `## Rulings` section (rulings
  numbered R1…, written at task boundaries, never rewritten after the
  fact), and a `## Heads` section for the atoms and Science head commits
  per task.
- [ ] **Step 2:** Commit (the plan is already committed; this adds only
  the ledger):
  `git add docs/plans/2026-08-23-root-lifecycle-ledger.md && git commit -m "docs(plans): root-lifecycle execution ledger"`

### Task 1: Atoms root-lifecycle design (atoms repository — design gate)

**Files:**
- Create (in `~/d/atoms`): `docs/2026-08-23-root-lifecycle-commands-design.md`
  on branch `design/root-lifecycle` in a fresh atoms worktree.
- Modify (after the review): **this plan's Tasks 2–7**, amended with the
  reviewed design's exact contracts wherever they name a callback,
  command, error, or token.

**Interfaces:**
- Produces: the reviewed atoms design Task 2 implements and Tasks 3–8
  consume through `science.root` — including the durable carrier for the
  grant and binding, the migration command's name, every signature, the
  retry/operation-identity token, and the fork's source-snapshot binding.

- [ ] **Step 1:** In the atoms checkout, create the worktree:
  `cd ~/d/atoms && git worktree add .worktrees/root-lifecycle -b design/root-lifecycle`
- [ ] **Step 2:** Write the design document covering exactly spec §2–§4,
  with these contracts pinned verbatim from the spec:
  - **The fail-closed writer state** (spec §2): writability a granted
    state in host bookkeeping; the coordinator refuses every mutation on
    a root not granted writability; a metadata-less tree cold-bootstraps
    read-only and unserviceable. Grantors: `register_root` **only for its
    own recorded local initialization operation** (recorded before
    genesis; the matching retry — and only it — completes a
    crash-interrupted grant; the bare matching-existing-genesis arm never
    grants), and `fork_root` after its genesis is durable.
  - **The root/host binding** (spec §2): the grant record carries a
    binding to the host's stable machine identity and the root's
    canonical path, validated before any grant is honored; mismatch
    reports `binding-mismatched` and conveys no grant; moving or renaming
    a writable root invalidates its grant, no writable rebind exists.
    **The binding's durable carrier is this design's to choose** — the
    requirement is frozen, the representation is not.
  - **The migration** (spec §2): a version-bound, operator-authorized
    transition recording the grant with a fresh binding; never
    auto-upgrades a metadata-less or restored copy; provenance is
    attested, not proven. This design names the command.
  - **`replicate_root`** (spec §4): source-lease-coherent copy;
    destination bookkeeping first, read-only stamp durable before any
    tree byte is exposable; grants neither writability nor
    serviceability; no-clobber with a durable operation identity;
    exact-retry.
  - **`fork_root(…, genesis_payload, surface_paths, dest_overrides)`**
    (spec §4): opaque genesis bytes; `dest_overrides` applied before
    baseline capture, genesis, and grant, interpreted never; baseline
    captured over `surface_paths`; new chain, genesis durable before the
    grant; retry splits at the grant — pre-grant proves
    genesis/baseline/tree, post-grant recognizes the operation identity
    and returns success.
  - **The fork's source-snapshot binding** (cut 9 W13 u2's requirement,
    resolved here): the caller derives its opaque genesis and override
    bytes from source facts, so the command must bind them to the **exact
    source snapshot it copies** — e.g. an expected-source-head
    precondition verified under the source lease, refusing with a
    distinct source-moved error when the source advanced between the
    caller's derivation and the hold; and an interrupted fork's retry
    must **reuse the original child identity, never re-mint** — the
    operation record carries (or verifies byte-identity of) the original
    `genesis_payload` and `dest_overrides`, so a retry that resupplies
    different bytes refuses rather than forking twice. The exact
    mechanism and error names are this design's to choose; the two
    requirements are frozen.
  - **`grant_read_serviceability`** (spec §4): structural rechecks only
    (non-writable; unserviceable, or already read-only serviceable →
    success without another write); no verdict channel; atoms spells no
    `restore_root`; out-of-band outside Science's restore orchestration.
    **The cold-root admission path:** spec §4's "currently unserviceable"
    includes the metadata-less root — the grant **creates** matching
    read-only-serviceable bookkeeping (with a fresh binding) for a
    validated cold root, since a metadata-less copy is exactly what
    restore admits (spec §7.2, cut 9 L10 u9); it refuses a writable root
    and a binding-mismatched one (a mismatched carrier is discarded by
    the operator, never overwritten by the grant).
  - **`read_lifecycle_state`** (spec §4): the closed five-value union —
    writable / read-only serviceable / read-only unserviceable /
    metadata-less / binding-mismatched — binding validated as part of the
    reading.
- [ ] **Step 3:** Commit the design on the branch.
- [ ] **Step 4: STOP.** Hand the design to the human partner for the
  atoms-side review. Do not proceed until the review closes; fold its
  findings into the design first.
- [ ] **Step 5: Amend every downstream contract the reviewed API
  touches** — Task 2's exact file paths, the bookkeeping schema
  transition, the migration command's name, every public signature, the
  operation-identity token type, and the source-moved and retry-mismatch
  error names; **and** Tasks 3, 5, 6, and 7 wherever they name a callback,
  command, error, or token the review renamed or reshaped. Replace every
  bracketed deferred item; do not start Task 2 before this amendment is
  committed.
- [ ] **Step 6:** Commit the amendment:
  `git add docs/superpowers/plans/2026-08-23-root-lifecycle.md docs/plans/2026-08-23-root-lifecycle-ledger.md && git commit -m "docs(plans): pin Task 2 to the reviewed atoms lifecycle design"`
  — recording the review's rulings in the ledger in the same commit.

### Task 2: Atoms implementation — lifecycle commands, state query, migration

**Contract-deferred:** the bracketed items below are finalized by Task 1
step 5's plan amendment; the red/green structure and obligations are fixed
now.

**Files (in the atoms worktree):**
- Create: `[the lifecycle module the reviewed design names]`,
  `python/tests/test_lifecycle_commands.py`
- Modify: `python/src/atoms/coordinator/commands.py` (`register_root`'s
  initialization operation and grant; the writability gate on
  `append_intent` and `run_transaction`), the coordinator exports.

**Interfaces:**
- Produces (consumed by Science via `science.root` callbacks):
  `replicate_root`, `fork_root`, `grant_read_serviceability`,
  `read_lifecycle_state`, `[the migration command]`, the five-value
  lifecycle-state union type, and `[the source-moved and retry-mismatch
  error names]` — signatures exactly as the Task 1 amendment pins them.

- [ ] **Step 1: Write the failing lifecycle-state tests** in
  `python/tests/test_lifecycle_commands.py`:

  - `test_fresh_register_root_reads_writable`
  - `test_interrupted_registration_matching_retry_grants` (fabricated:
    recorded operation, durable genesis, no grant)
  - `test_bare_reregistration_over_an_existing_genesis_never_grants`
  - `test_metadata_less_tree_reads_metadata_less`
  - `test_host_delta_reads_binding_mismatched`
  - `test_path_delta_reads_binding_mismatched`

  each state read back through `read_lifecycle_state`.
- [ ] **Step 2:** Run: `uv run --frozen pytest tests/test_lifecycle_commands.py -v`
  (from the atoms worktree's `python/`). Expected: every test FAILS at
  import (`ImportError: cannot import name 'read_lifecycle_state'`).
  Implement the writer state, binding, and query. Run again: PASS.
- [ ] **Step 3: Write the failing command tests**, same file:

  - `test_replicate_copies_chain_and_payload_byte_identical`
  - `test_replica_reads_read_only_unserviceable`
  - `test_replicate_refuses_an_existing_destination` (no-clobber)
  - `test_replicate_interrupted_before_stamp_is_metadata_less` and
    `test_replicate_interrupted_after_stamp_is_read_only_unserviceable`
    (fabricated windows); `test_replicate_retry_converges`
  - `test_fork_applies_overrides_before_baseline` (baseline = destination
    surface after overrides)
  - `test_fork_appends_a_new_chain_with_the_supplied_genesis_bytes`
  - `test_fork_refuses_a_moved_source` (the bound snapshot no longer
    matches under the lease)
  - `test_fork_interrupted_before_grant_is_read_only`;
    `test_fork_pregrant_retry_completes_with_identical_inputs`;
    `test_fork_pregrant_retry_refuses_different_bytes`;
    `test_fork_postgrant_retry_returns_success_after_legitimate_writes`
  - `test_grant_refuses_a_writable_root`;
    `test_grant_refuses_a_binding_mismatched_root`;
    `test_grant_creates_bookkeeping_for_a_metadata_less_root` (the
    cold-root admission path: after it, `read_lifecycle_state` is
    read-only serviceable with a fresh binding);
    `test_grant_is_idempotent_on_read_only_serviceable` (no second write)
  - `test_migration_authorized_success_grants_with_a_fresh_binding`
    (fabricated pre-lifecycle vintage);
    `test_migration_refuses_a_metadata_less_root`;
    `test_migration_refuses_a_binding_mismatch`
- [ ] **Step 4:** Run: `uv run --frozen pytest tests/test_lifecycle_commands.py -v`.
  Expected: FAIL for want of each command. Implement. Run again: PASS.
- [ ] **Step 5:** Run the full atoms suite and gates from the atoms
  `python/`: `uv run --frozen pytest && uv run --frozen ruff check . && uv run --frozen pyright`
  (no explicit `-q` — if the atoms addopts already sets it, doubling
  hides the count)
  — quote the pytest summary line in the ledger.
- [ ] **Step 6:** Commit on the branch; merge `--no-ff` to local atoms
  `main`; **push atoms `main`** (spec §8 step 5 makes the push part of
  the gate). Record the pushed head hash in the Science ledger's
  `## Heads`.

### Task 3: Science store construction and the widened projection

**Files:**
- Create: `python/tests/test_store_root.py`
- Modify: `python/src/science/root.py` (`init_store_root`,
  `_store_genesis_payload`, the five new atoms callbacks),
  `python/src/science/world/verify.py` (`RootKind` gains `"store"`;
  `registered_surface_paths` gains the `"store"` arm — **the one
  projection function, no second walker**),
  `python/tests/test_capability_boundary.py`
  (`test_the_composition_root_names_every_engine_command` gains the five
  new command names)

**Interfaces:**
- Consumes: Task 2's commands, via new `root.py` callbacks on the
  `chain_head_reader`/`_capture` pattern; `verify.registered_surface_paths`.
- Produces: `init_store_root(store_root: Path) -> str` (the minted
  32-lowercase-hex `store_id`; refuses a populated payload root with
  `CorpusRootRefused`, the established init refusal; exact-retry — a
  re-run over an interrupted init returns the **original** id);
  `registered_surface_paths(root, "store")` (every non-bookkeeping
  root-relative entry, symlinks not followed);
  `_store_genesis_payload(store_id: str, forked_from: tuple[str, str] | None) -> bytes`
  under the store genesis domain.

- [ ] **Step 1: Write the failing tests** in `tests/test_store_root.py`:

  - `test_init_store_root_mints_a_fresh_opaque_id` — two inits in two
    directories mint distinct 32-lowercase-hex ids; renaming the root
    directory changes nothing the genesis carries.
  - `test_init_store_root_refuses_a_populated_payload_root` — a root
    holding one payload file refuses `CorpusRootRefused`; nothing is
    registered (no chain leaf appears).
  - `test_interrupted_init_retry_returns_the_original_store_id` —
    fabricate the interrupt per Task 2's pattern (durable genesis, no
    grant); a re-run of `init_store_root` completes the grant and
    returns the id decoded from the existing genesis, never a re-mint.
  - `test_store_genesis_payload_round_trips` — payload with and without
    `forked_from` decodes to its inputs; a malformed `forked_from` (wrong
    shape, non-hex digest) is refused at decode. (The fork-form versus
    empty-baseline distinction is Task 7's, with the fork acts.)
  - `test_cold_existing_store_root_refuses_reinitialization` — a
    metadata-less copy of an initialized store (genesis present, no
    bookkeeping) refuses `CorpusRootRefused`: a copied store is restored
    or forked, never re-initialized into writability.
  - `test_store_surface_excludes_bookkeeping` —
    `registered_surface_paths(root, "store")` excludes the chain leaf
    and engine metadata; every other root-relative entry is included.
  - `test_store_surface_does_not_follow_symlinks` — a symlink is an
    entry, never traversed.
- [ ] **Step 2:** Run: `uv run --frozen pytest tests/test_store_root.py -v`.
  Expected: FAIL, `ImportError: cannot import name 'init_store_root' from 'science.root'`.
- [ ] **Step 3: Implement**, following `_world_genesis_payload` and
  `init_world_root` as the pattern (directory handling and refusal
  included). Sketch:

  ```python
  STORE_GENESIS_DOMAIN = "science.store-root.v1"

  def _store_genesis_payload(store_id: str, forked_from: tuple[str, str] | None) -> bytes:
      doc: dict[str, object] = {"domain": STORE_GENESIS_DOMAIN, "store_id": store_id}
      if forked_from is not None:
          doc["forked_from"] = {"genesis": forked_from[0], "head": forked_from[1]}
      return v1.encode(doc)

  def init_store_root(store_root: Path) -> str:
      if store_root.exists() and not store_root.is_dir():
          raise CorpusRootRefused(f"{str(store_root)!r} exists and is not a directory, so it cannot be a store root")
      store_root.mkdir(parents=True, exist_ok=True)
      existing = _read_existing_store_genesis(store_root)
      if existing is not None:
          # Let register_root recognize its own durable initialization
          # operation; Science never reads or interprets that bookkeeping.
          # The matching retry grants, a completed init stays writable, and a
          # bare copied genesis remains metadata-less.
          register_root(_PRODUCTION_BACKEND, str(store_root), str(metadata_root_for(store_root)),
                        PRODUCTION_STORAGE, _store_genesis_payload(existing, None), ())
          if read_lifecycle_state(store_root) == "writable":
              return existing
          raise CorpusRootRefused(
              f"{str(store_root)!r} carries a store genesis this host did not "
              "initialize; a copied store is restored or forked, never re-initialized")
      populated = registered_surface_paths(store_root, "store")
      if populated:
          raise CorpusRootRefused(f"{str(store_root)!r} holds payload {populated[0]!r}; a store initializes empty")
      store_id = secrets.token_hex(16)
      register_root(_PRODUCTION_BACKEND, str(store_root), str(metadata_root_for(store_root)),
                    PRODUCTION_STORAGE, _store_genesis_payload(store_id, None), ())
      return store_id
  ```

  The `"store"` arm of `registered_surface_paths` is the whole-namespace
  projection: every root-relative entry minus the chain leaf and engine
  metadata, `entry.is_symlink()` checked before any `is_dir()` traversal.
  Extend the boundary test's engine-command list with the five new names.
- [ ] **Step 4:** Run to PASS, then the gate block. Commit:
  `feat(root): store roots and the canonical store projection`. Append
  and commit the ledger.

### Task 4: Store subjects through the verification surface

**Files:**
- Create: `python/tests/test_store_subjects.py`
- Modify: `python/src/science/world/verify.py` (delete
  `_refuse_store_subject` and both call sites — the `evaluate_log` path
  and `_audit_log` path; widen `_subject_hold` and the audit target
  rule), `python/src/science/errors.py` (delete `StoreSubjectUnsupported`
  and every import of it), `python/src/science/root.py` (`anchor_heads`
  store widening, `export_head_artifact` store arm, `audit_log` store
  path), and the existing store-refusal assertions in
  `python/tests/test_world_log_codecs.py`,
  `python/tests/test_world_log_audit.py`, and
  `python/tests/test_world_log_evaluator.py` — each updated to the new
  store behavior, never deleted without a replacement assertion.

**Interfaces:**
- Consumes: Task 3's projection and genesis codec.
- Produces:
  `anchor_heads(world, corpus_ids, *, store_roots: tuple[tuple[str, Path], ...] = (), actor)`
  — each pair `(store_id, root)`, the genesis verified to carry that
  `store_id` **before head acceptance or registry mutation**;
  `export_head_artifact(world, subject, *, store_root: Path | None = None)`
  under the same resolution contract; `audit_log` accepting a
  `StoreSubject` with a supplied root.

- [ ] **Step 1: Write the failing tests** in `tests/test_store_subjects.py`:

  - `test_anchor_heads_mints_a_store_subject_record` — anchor an
    initialized store; the registry holds a `LogHeadRecord` with the
    store subject and the live genesis/head digests.
  - `test_anchor_refuses_a_store_id_genesis_mismatch_before_registry_mutation`
    — a supplied root whose genesis carries another id refuses; the
    registry bytes are unchanged after the refusal.
  - `test_export_head_artifact_round_trips_a_store_head` — the returned
    bytes decode under `science.head-artifact.v1` with the store subject.
  - `test_store_audit_validated` / `test_store_audit_refuted_on_truncation`
    (valid-prefix truncation behind the store-subject registry anchor) /
    `test_store_audit_refuted_on_chain_removal_under_registry_anchor`
    (delete the chain outright, the store-subject record in the observer
    set — cut 9 L4 u1, the anchor bound by `store_id`) /
    `test_store_audit_malformed_on_interior_damage` /
    `test_store_audit_unresolvable_on_empty_observers` — the four
    verdicts over fabricated store states.
  - `test_store_audit_holds_one_boundary_across_inspect_capture_evaluate`
    — the hold spans the three (assert via the lock-probe pattern
    `test_capability_boundary.py::test_the_check_would_see_a_second_holder`
    uses).
  - `test_store_subject_unsupported_is_deleted` — the class is gone from
    its defining module (`assert not hasattr(science.errors, "StoreSubjectUnsupported")`)
    **and** the helper is gone from the source
    (`"_refuse_store_subject" not in Path(verify.__file__).read_text()`,
    the capability-boundary tests' source-scan pattern) — not a mere
    not-raised.
- [ ] **Step 2:** Run: `uv run --frozen pytest tests/test_store_subjects.py -v`.
  Expected: FAIL — `TypeError: anchor_heads() got an unexpected keyword argument 'store_roots'`
  and `StoreSubjectUnsupported` raised where verdicts are expected.
- [ ] **Step 3: Implement** — the widening only: codecs already carry
  stores; touch acts, wrappers, and the reachable evaluator path, and
  update the three existing test files' store-refusal assertions to the
  new behavior. The genesis check decodes the supplied root's genesis
  payload and compares `store_id` before any registry transaction is
  planned.
- [ ] **Step 4:** Run to PASS; gate block; then
  `uv run --frozen python tools/cut7_acceptance.py` (still exit 0).
  **Ledger ruling, written now:** cut 8's store-refusal declarations
  (its label 6 and the refusal assertions its arms exercise) fail on the
  current tree from this task on, **by design** — the refusal they
  certify is the shape-only state this slice removes; cut 8's discharge
  stands as its frozen results record, and cut 9's store units are the
  successor certification. Commit:
  `feat(world): store subjects through anchor, export, and audit`. Append
  and commit the ledger.

### Task 5: Lifecycle wrappers and gate precedence

**Files:**
- Create: `python/tests/test_lifecycle_wrappers.py`
- Modify: `python/src/science/root.py` (thin wrappers: `replicate_root`,
  `read_lifecycle_state`, the migration passthrough)

**Interfaces:**
- Consumes: Task 2's commands.
- Produces: `science.root.replicate_root(source_root, dest_root)`
  (appends nothing — a replica's chain arrives unchanged);
  `science.root.read_lifecycle_state(root) -> LifecycleState` (the atoms
  union re-exported); the operator-authorized migration passthrough,
  refusals included.

- [ ] **Step 1: Write the failing tests** in
  `tests/test_lifecycle_wrappers.py`:

  - `test_completed_replica_reads_read_only_unserviceable` — replicate an
    initialized store; `read_lifecycle_state(dest)` is read-only
    unserviceable (cut 9 L10 u3/u4's residues).
  - `test_replica_chain_is_byte_identical` — the chain leaf's files
    compare equal, byte for byte.
  - `test_metadata_less_copy_refuses_mutation_at_the_writability_gate` —
    `shutil.copytree` a **corpus** root without its metadata; a
    cooperative registered-surface mutation refuses at the writability
    gate while `audit_log` over the copy still reads `unresolvable` with
    the pending entry named (cut 9 L2 u1; the fixture asserts the copy
    genuinely carries a pending entry and no metadata).
  - `test_writable_pending_root_still_refuses_pending_unresolved` — a
    live root with a fabricated unresolved pending entry and a real grant
    refuses `PendingUnresolved` (label 11's contrast half; the fixture
    asserts the grant through `read_lifecycle_state`).
  - `test_migration_refuses_metadata_less_and_mismatched` — the
    passthrough's two structural refusals.
  - `test_metadata_less_store_copy_reads_metadata_less_and_refuses_mutation`
    — the store half of the cold bootstrap (cut 9 L10 u8's structural
    residue; the holdings-read clauses stay deferred by the cut).
  - `test_lifecycle_union_is_closed_at_five` — the re-exported state type
    has exactly the five declared members (cut 9 label 6's closure).
  - `test_binding_delta_reads_binding_mismatched` — a fabricated
    single-delta binding edit (host, then path) reads `binding-mismatched`
    through the Science wrapper, never the state the bytes claim.
  - `test_migration_authorized_success_reads_writable` — the passthrough
    over a fabricated pre-lifecycle vintage grants; the root reads
    writable with a fresh binding.
  - `test_replicate_refuses_an_existing_destination` — the wrapper's
    no-clobber refusal, observed from Science.
- [ ] **Step 2:** Run: `uv run --frozen pytest tests/test_lifecycle_wrappers.py -v`.
  Expected: FAIL at import of the wrappers.
- [ ] **Step 3: Implement** the wrappers (each a `root.py` function
  converting paths and re-raising the atoms errors through the existing
  `LogEvidenceRefused` conversion pattern where one applies). Run to
  PASS; gate block. Commit:
  `feat(root): lifecycle wrappers and the writability-gate precedence`.
  Append and commit the ledger.

### Task 6: `restore_root`

**Files:**
- Create: `python/tests/test_restore_root.py`
- Modify: `python/src/science/root.py` (`restore_root`, the wrapper),
  `python/src/science/world/verify.py` (factor the evaluation-input
  assembly out of `_audit_log` into a shared helper —
  `_assemble_evaluation_inputs(root, subject, …) -> (view, disk, presented, absent)`
  — called by `_audit_log` unchanged in behavior and by the new restore
  core; the helper is the exact boundary, and no third assembly exists)

**Interfaces:**
- Consumes: Tasks 2–5 (query, grant, evaluator store path).
- Produces:
  `restore_root(dest_root: Path, subject: CorpusSubject | StoreSubject, observers) -> LogReport`
  — the existing report type, unwrapped (**no new report type**);
  admission is observed through `read_lifecycle_state(dest_root)`, never
  through the return value; a world subject is unspellable by type.

- [ ] **Step 1: Write the failing tests** in `tests/test_restore_root.py`,
  one per spec §7.2 step:

  - `test_malformed_copy_returns_malformed_and_stays_unserviceable` — a
    copied store with interior chain damage returns
    `LogReport(outcome="malformed")` and the root reads read-only
    unserviceable — never a pre-evaluation exception.
  - `test_validated_store_copy_admits_read_only_serviceable` — replicate,
    restore with the store-subject registry record as observer →
    `outcome == "validated"` and `read_lifecycle_state(dest)` is
    read-only serviceable.
  - `test_re_restore_is_idempotent` — a second restore returns
    `validated` again and the state is unchanged.
  - `test_validated_with_store_subject_mismatch_does_not_admit` — the
    fixture raw-authors an exported head artifact naming the presented
    chain's genesis and head digests under the **selected, different**
    `store_id` (the raw-write license); evaluation over that observer
    set returns `outcome == "validated"` — asserted, so replay
    refutation cannot discharge the test vacuously — and the root stays
    unserviceable: subject agreement is a separate lifecycle
    precondition.
  - `test_validated_with_corpus_manifest_mismatch_does_not_admit` — the
    corpus fixture rewrites `corpus.yaml` to another `corpus_id`
    **cooperatively, through the logged mutation path**, so the rewrite
    is in history and replay validates (the slice-3 §1.2 case: "a
    cooperatively logged `corpus.yaml` identity rewrite replays
    consistently, so replay alone is not the guard"); then replicate and
    restore selecting the original subject — `outcome == "validated"`
    asserted, and no admission.
  - `test_empty_observer_set_unresolvable_replay_not_reached` — cut 9
    L10 u11; the report's `observer_bound` is empty and the root
    unserviceable.
  - `test_incomplete_copy_never_validates` — omit one payload file the
    chain's surface names (never chain damage — the cut §6 obligation);
    the verdict is preserved (refuted/malformed/unresolvable, asserted
    `!= "validated"`), root unserviceable (L10 u10).
  - `test_two_copies_both_admit_read_only` — two metadata-less copies of
    one `store_id`, both restored → both read-only serviceable, a
    cooperative write on either refused (L10 u9; the fixture asserts
    both were metadata-less first).
  - `test_restore_never_grants_writability` — after every admission
    above, no root reads writable.
  - `test_restore_holds_one_boundary_across_evaluate_and_grant` — the
    lock-probe pattern again: a second holder is refused for the whole
    span.
  - The divergence triple (cut 9 L10 u12):
    `test_divergent_copies_assembled_in_one_root_are_sibling_malformed`;
    `test_both_divergent_heads_in_one_observer_set_refute`;
    `test_divergent_copies_verified_separately_each_validate` — the last
    asserting the pinned surviving-observer negative as the claim.
- [ ] **Step 2:** Run: `uv run --frozen pytest tests/test_restore_root.py -v`.
  Expected: FAIL, `ImportError: cannot import name 'restore_root'`.
- [ ] **Step 3: Implement.** The evaluation assembly is `audit_log`'s
  own, reused — `restore_root` mirrors how `audit_log` builds the
  `ChainView`, disk capture, `PresentedIdentity`, and `absent_state`
  arguments, then adds the gate and grant. Sketch (all under one held
  destination boundary; `evaluate_log`'s real signature is
  `evaluate_log(subject, view, observers, disk, presented, absent_state, history=None)`):

  ```python
  def restore_root(dest_root: Path, subject: CorpusSubject | StoreSubject, observers) -> LogReport:
      with _restore_boundary(dest_root):
          view, disk, presented, absent = _assemble_evaluation_inputs(dest_root, subject)
          # ^ the same assembly audit_log performs today, factored so both call it;
          #   inspection mode by lifecycle state, malformed views flowing into evaluate_log
          report = evaluate_log(subject, view, observers, disk, presented, absent)
          if report.outcome == "validated" and _subject_agrees(subject, presented, dest_root):
              _grant_read_serviceability_callback(dest_root)
          return report
  ```

  `_subject_agrees` implements spec §7.2 step 4: store — the presented
  genesis's `store_id` equals the subject's; corpus — the presented
  manifest's `corpus_id` equals the subject's, the genesis form-validated
  only.
- [ ] **Step 4:** Run to PASS; gate block. Commit:
  `feat(root): restore_root under one held boundary`. Append and commit
  the ledger.

### Task 7: The fork acts

**Files:**
- Create: `python/tests/test_fork_acts.py`
- Modify: `python/src/science/root.py` (`fork_corpus`, `fork_store`, the
  fork genesis payloads), `python/src/science/world/verify.py`
  (genesis-form validation: fork forms carry `forked_from` and a
  non-empty baseline; non-fork forms still require empty)

**Interfaces:**
- Consumes: Task 2's `fork_root` with its source-snapshot binding and
  retry contract (names per the Task 1 amendment); Task 3's projection
  and codecs; `registry.CorpusManifest`.
- Produces: `fork_corpus(source_root, dest_root) -> CorpusManifest` — the
  **existing** manifest type, act-authored, carrying the fresh
  `corpus_id` and `forked_from = (parent corpus_id, parent corpus-state
  identity)`; `fork_store(source_root, dest_root) -> str` (the new
  `store_id`). Fork genesis payloads carry `forked_from = (parent genesis
  digest, parent head digest)`; the manifest travels as a
  `dest_overrides` entry, installed before the grant.

- [ ] **Step 1: Write the failing tests** in `tests/test_fork_acts.py`:

  - `test_fork_corpus_mints_a_fresh_id_independent_of_path_and_name` —
    W13 u1; two forks of one parent mint distinct ids.
  - `test_fork_manifest_is_complete_before_writability` — the destination
    `corpus.yaml` parses as a full `CorpusManifest` the moment the root
    reads writable.
  - `test_fork_genesis_carries_parent_digests_and_nonempty_baseline` —
    L10 u1: the fork genesis's `forked_from` equals the parent's genesis
    and head digests at the bound snapshot, and its baseline equals the
    destination surface after overrides.
  - `test_nonfork_genesis_still_requires_empty_baseline` — genesis-form
    validation refuses a non-empty baseline on a non-fork form.
  - `test_source_moved_between_derivation_and_fork_refuses` — mutate the
    parent after deriving the fork facts; the act refuses with the
    source-moved error and mints nothing.
  - `test_fork_retry_reuses_the_original_child_identity` — interrupt
    between genesis and grant (fabricated per Task 2's pattern); the
    retry completes with the **same** `corpus_id`; a retry resupplying
    different bytes refuses.
  - `test_l6_anchored_baseline_deletion_refutes` — fork, anchor the fork,
    delete one baseline-covered pre-log member (the only delta — cut §6),
    audit → `refuted`; the fixture asserts the member is in the fork
    genesis's baseline and in no post-genesis entry (L6 u1).
  - `test_l6_anchor_free_rewrite_is_unresolvable` — consistent rewrite of
    genesis, baseline, and chain omitting the member, no surviving
    anchor → `unresolvable`, asserted never `validated` and never
    `refuted`; the fixture asserts byte-difference and full omission
    (L6 u2).
  - `test_parent_anchor_never_compared_in_fork_subject_evaluation` — L10
    u2: a parent anchor in a fork-subject observer set contributes to no
    genesis or ancestry judgment (assert it is filtered from
    `observer_bound`).
  - `test_two_fork_geneses_same_child_subject_refute` — L4 u2: replace an
    anchored fork's chain with a self-consistent chain under a different
    fork genesis, same child subject, original anchor supplied →
    `refuted`; the fixture asserts same subject, differing geneses.
- [ ] **Step 2:** Run: `uv run --frozen pytest tests/test_fork_acts.py -v`.
  Expected: FAIL, `ImportError: cannot import name 'fork_corpus'`.
- [ ] **Step 3: Implement.** `fork_corpus` branches on the destination
  **before any mint** — the retry path first, so an interrupted fork
  never re-mints:

  1. **Resume branch:** the destination carries `fork_root`'s recorded
     fork operation (probed through the mechanism the Task 1 amendment
     names — the operation record carries the original `genesis_payload`
     and `dest_overrides`, so atoms completes the fork from its own
     record). Call the resume entry point; then read the child manifest
     **from the destination** (it was installed by the recorded
     overrides) and return it — the same `corpus_id`, never a fresh one.
  2. **Fresh branch:** the destination is absent. Read the parent's
     manifest and chain head, compute the corpus-state identity, mint
     the child id, author the `CorpusManifest`, build the fork genesis
     payload, then call `fork_root` with the snapshot binding — a
     source-moved refusal propagates untranslated.
  3. Anything else at the destination (a foreign root, a completed fork)
     — `fork_root`'s no-clobber and operation-identity refusals
     propagate; `fork_corpus` adds no third disposition.

  Extend genesis-form validation for both fork forms. Run to PASS.
- [ ] **Step 4:** Gate block; then
  `uv run --frozen python tools/cut7_acceptance.py` (still exit 0;
  cut 8's store-refusal residue is Task 4's standing ruling). Commit:
  `feat(root): fork acts, fork geneses, and the L6 lift in code`. Append
  and commit the ledger.

### Task 8: Fork-of admission and `admit_arrival`'s inspection modes

**Files:**
- Create: `python/tests/test_arrival_modes.py`
- Modify: `python/src/science/root.py` (`admit_arrival` mode selection).
  **No registry change:** `World.admit` already loads the destination
  manifest and validates `ForkOf`; fork admission needs an integration
  test, not new registry code.

**Interfaces:**
- Consumes: Task 5's `read_lifecycle_state`, Task 7's act-authored
  `CorpusManifest`.
- Produces: `admit_arrival` branching over the five-value union; the
  fork-admission integration path proven end-to-end.

- [ ] **Step 1: Write the failing tests** in `tests/test_arrival_modes.py`:

  - `test_fork_product_admits_through_the_fork_of_path` — integration:
    `fork_corpus`'s destination admits through `World.admit` with no
    fixture-authored manifest anywhere in the flow.
  - `test_arrival_registered_mode_on_serviceable` — a restored
    (read-only serviceable) corpus copy arrives under registered
    inspection.
  - `test_arrival_detached_on_unserviceable_metadata_less_and_mismatched`
    — the three detached states, one fixture each.
  - `test_arrival_refuses_a_writable_root` — the root is granted through
    `register_root`'s own path, never fabricated bookkeeping (cut §6);
    a `ReplicaOf` arrival over it refuses.
  - `test_restored_arrival_requires_restore_first` — an unrestored copy
    arrives detached; after `restore_root`, registered.
  - `test_store_subject_unspellable_at_arrival` — the arrival act's
    signature still cannot name a store (label 8's corpus-only negative).
- [ ] **Step 2:** Run: `uv run --frozen pytest tests/test_arrival_modes.py -v`.
  Expected: the mode tests FAIL (arrival is unconditionally detached
  today); the fork-admission test FAILS only if Task 7 mis-authored the
  manifest — a passing first run there is acceptable and recorded.
- [ ] **Step 3: Implement** the mode selection in `admit_arrival`
  (branch on `read_lifecycle_state`; writable → a typed refusal). Run to
  PASS; gate block; then
  `uv run --frozen python tools/cut7_acceptance.py` (still exit 0). Commit:
  `feat(world): act-minted fork admission and lifecycle-aware arrival`.
  Append and commit the ledger.

### Task 9: The 30 N2 declarations

**Files:**
- Create: `python/tests/acceptance/n2_arms_cut9.py` (the declarations as
  data), `python/tests/acceptance/test_n2_cut9.py` (the audit and
  obligations) — mirroring `n2_arms_cut8.py` + `test_n2_cut8.py` exactly
  in structure.

**Interfaces:**
- Consumes: every prior task's test nodes (declare, cite, never
  re-implement).
- Produces: `CUT9_ARMS`, the 30 declaration units cut 9 §3 freezes — L2
  u1; L4 u1–u2; L6 u1–u2; L10 u1–u12; W13 u1–u2; labels 1–11 — each
  naming its check nodes in Tasks 2–8's test files, plus
  `ATOMS_CITATIONS_BY_UNIT: dict[str, tuple[str, ...]]`, a parallel
  metadata map whose values are fully qualified atoms pytest nodes and
  which never enters `Arm.checks`; plus
  `test_the_declared_units_are_unique_and_number_thirty` pinning the
  count.

- [ ] **Step 1:** Declare all 30 units as data, unit-for-unit against the
  frozen cut's §3.1 dispositions and §3.3 labels, each carrying its §5
  declaration-time obligations (chain fabrications pass `inspect_chain`;
  bookkeeping fabrications read back through `read_lifecycle_state`; the
  L6, L4, L10 u9, migration-vintage, single-binding-delta, and L2 u1
  fixture assertions of §5 items 2–8) and the three §6 freeze obligations
  as declaration-time checks. Atoms-certified interiors are declared as
  citations to the atoms suite, per the cut's §1 principle. The
  unit-to-node mapping. **Check nodes live under Science's `tests/`
  only** — the harness resolves every check there and applies sabotage
  beneath `src/science`, so an atoms test can never be a check node.
  Where a unit's producing half is atoms-certified, the declaration
  carries an **atoms citation** as metadata beside its local check —
  named in the "atoms citation" column, resolved by the harness against
  nothing (it is recorded provenance, not a collected node). Implement
  that metadata as the exported parallel map
  `ATOMS_CITATIONS_BY_UNIT`; its keys are exactly `L10u4`, `L10u5`,
  `L10u7`, and `D1`–`D6`, and every value is one fully qualified node
  beneath atoms' `tests/test_lifecycle_commands.py`. Add
  `test_atoms_citations_are_metadata_not_checks`: assert the exact key
  set, assert every value has the form
  `tests/test_lifecycle_commands.py::test_*`, and assert no citation
  occurs in any `Arm.checks`. The audit never passes this map to
  `baseline` or `audit`. `t_` abbreviates Science's `tests/`; the atoms
  column shows the exact stored node ids.

  | unit | check node(s) (Science `tests/`) | atoms citation (metadata) |
  |---|---|---|
  | L2 u1 | `t_lifecycle_wrappers::test_metadata_less_copy_refuses_mutation_at_the_writability_gate`, `::test_writable_pending_root_still_refuses_pending_unresolved` | — |
  | L4 u1 | `t_store_subjects::test_store_audit_refuted_on_chain_removal_under_registry_anchor` | — |
  | L4 u2 | `t_fork_acts::test_two_fork_geneses_same_child_subject_refute` | — |
  | L6 u1 | `t_fork_acts::test_l6_anchored_baseline_deletion_refutes` | — |
  | L6 u2 | `t_fork_acts::test_l6_anchor_free_rewrite_is_unresolvable` | — |
  | L10 u1 | `t_fork_acts::test_fork_genesis_carries_parent_digests_and_nonempty_baseline` | — |
  | L10 u2 | `t_fork_acts::test_parent_anchor_never_compared_in_fork_subject_evaluation` | — |
  | L10 u3 | `t_lifecycle_wrappers::test_completed_replica_reads_read_only_unserviceable`, `::test_replica_chain_is_byte_identical` | — |
  | L10 u4 | `t_lifecycle_wrappers::test_completed_replica_reads_read_only_unserviceable` | `tests/test_lifecycle_commands.py::test_replicate_interrupted_after_stamp_is_read_only_unserviceable` (the order) |
  | L10 u5 | `t_lifecycle_wrappers::test_metadata_less_store_copy_reads_metadata_less_and_refuses_mutation` (the Science-observable residue of the window) | `tests/test_lifecycle_commands.py::test_replicate_interrupted_before_stamp_is_metadata_less` |
  | L10 u6 | `t_lifecycle_wrappers::test_metadata_less_copy_refuses_mutation_at_the_writability_gate`, `::test_metadata_less_store_copy_reads_metadata_less_and_refuses_mutation` | — |
  | L10 u7 | `t_fork_acts::test_fork_retry_reuses_the_original_child_identity` | `tests/test_lifecycle_commands.py::test_fork_interrupted_before_grant_is_read_only` (the order) |
  | L10 u8 | `t_lifecycle_wrappers::test_metadata_less_store_copy_reads_metadata_less_and_refuses_mutation` (holdings-read clauses deferred, stated in the declaration) | — |
  | L10 u9 | `t_restore_root::test_two_copies_both_admit_read_only` | — |
  | L10 u10 | `t_restore_root::test_incomplete_copy_never_validates` | — |
  | L10 u11 | `t_restore_root::test_empty_observer_set_unresolvable_replay_not_reached` | — |
  | L10 u12 | `t_restore_root::test_divergent_copies_assembled_in_one_root_are_sibling_malformed`, `::test_both_divergent_heads_in_one_observer_set_refute`, `::test_divergent_copies_verified_separately_each_validate` | — |
  | W13 u1 | `t_fork_acts::test_fork_corpus_mints_a_fresh_id_independent_of_path_and_name` | — |
  | W13 u2 | `t_fork_acts::test_fork_manifest_is_complete_before_writability`, `::test_source_moved_between_derivation_and_fork_refuses` | — |
  | label 1 | `t_store_root::test_interrupted_init_retry_returns_the_original_store_id`, `::test_cold_existing_store_root_refuses_reinitialization` | `tests/test_lifecycle_commands.py::test_interrupted_registration_matching_retry_grants`, `tests/test_lifecycle_commands.py::test_bare_reregistration_over_an_existing_genesis_never_grants` |
  | label 2 | `t_lifecycle_wrappers::test_binding_delta_reads_binding_mismatched` (host and path deltas; the moved-root consequence is the path delta) | `tests/test_lifecycle_commands.py::test_host_delta_reads_binding_mismatched`, `tests/test_lifecycle_commands.py::test_path_delta_reads_binding_mismatched` |
  | label 3 | `t_lifecycle_wrappers::test_migration_authorized_success_reads_writable`, `::test_migration_refuses_metadata_less_and_mismatched` | `tests/test_lifecycle_commands.py::test_migration_authorized_success_grants_with_a_fresh_binding` |
  | label 4 | `t_lifecycle_wrappers::test_replicate_refuses_an_existing_destination`, `t_fork_acts::test_fork_retry_reuses_the_original_child_identity` | `tests/test_lifecycle_commands.py::test_fork_pregrant_retry_completes_with_identical_inputs`, `tests/test_lifecycle_commands.py::test_fork_pregrant_retry_refuses_different_bytes`, `tests/test_lifecycle_commands.py::test_fork_postgrant_retry_returns_success_after_legitimate_writes` |
  | label 5 | `t_restore_root::test_validated_store_copy_admits_read_only_serviceable` (the cold-root creation path), `::test_re_restore_is_idempotent`, `::test_restore_never_grants_writability`; the out-of-band pinning is the declaration's stated negative | `tests/test_lifecycle_commands.py::test_grant_refuses_a_writable_root`, `tests/test_lifecycle_commands.py::test_grant_creates_bookkeeping_for_a_metadata_less_root`, `tests/test_lifecycle_commands.py::test_grant_is_idempotent_on_read_only_serviceable` |
  | label 6 | `t_lifecycle_wrappers::test_lifecycle_union_is_closed_at_five`, `::test_binding_delta_reads_binding_mismatched` | `tests/test_lifecycle_commands.py::test_metadata_less_tree_reads_metadata_less` |
  | label 7 | `t_restore_root::test_malformed_copy_returns_malformed_and_stays_unserviceable`, `::test_validated_with_store_subject_mismatch_does_not_admit`, `::test_validated_with_corpus_manifest_mismatch_does_not_admit`, `::test_restore_never_grants_writability`, `::test_restore_holds_one_boundary_across_evaluate_and_grant` | — |
  | label 8 | `t_arrival_modes::test_fork_product_admits_through_the_fork_of_path`, `::test_arrival_registered_mode_on_serviceable`, `::test_arrival_detached_on_unserviceable_metadata_less_and_mismatched`, `::test_arrival_refuses_a_writable_root`, `::test_restored_arrival_requires_restore_first`, `::test_store_subject_unspellable_at_arrival` | — |
  | label 9 | `t_store_subjects::test_anchor_refuses_a_store_id_genesis_mismatch_before_registry_mutation`, `::test_export_head_artifact_round_trips_a_store_head`, `::test_store_audit_holds_one_boundary_across_inspect_capture_evaluate` | — |
  | label 10 | `t_store_root::test_init_store_root_refuses_a_populated_payload_root`, `::test_store_genesis_payload_round_trips`, `::test_store_surface_excludes_bookkeeping`, `::test_store_surface_does_not_follow_symlinks`, `t_fork_acts::test_nonfork_genesis_still_requires_empty_baseline` | — |
  | label 11 | `t_lifecycle_wrappers::test_metadata_less_copy_refuses_mutation_at_the_writability_gate`, `::test_writable_pending_root_still_refuses_pending_unresolved` (cited from L2 u1, single-homed there) | — |
- [ ] **Step 2:** Run the audit:
  `uv run --frozen pytest tests/acceptance/test_n2_cut9.py -v`. Every one
  of the 30 arms resolves `sound`; fix any `vacuous`/`uncollected`/`stale`
  as harness or declaration defects, never by weakening a check.
- [ ] **Step 3:** Gate block; quote the summary line. Commit:
  `test(cut9): declare the 30 frozen arms`. Append and commit the ledger.

### Task 10: Certified acceptance

**Files:**
- Create: `python/tools/cut9_acceptance.py`

**Interfaces:**
- Consumes: Task 9's declarations; `tools/cut7_acceptance.py` unedited.
- Produces: the certified acceptance runner. Its **sole prior-cut
  current-tree prefix is `tools/cut7_acceptance.py`** (which already
  chains cuts 5–6). **Cut 8 is cited, not run:** Task 4's ruling made its
  store-refusal declarations deliberately stale on the successor tree,
  so its discharge stands as the frozen results record
  (`docs/plans/2026-08-22-conformance-cut-8-results.md`) and cut 9's
  store units are the successor certification — the runner's docstring
  states this ruling and its ledger number exactly as cut 8's docstring
  states its own chaining authority.

- [ ] **Step 1:** Implement the runner mirroring `tools/cut8_acceptance.py`
  structurally (the certified-tuple probe first, erroring never
  skipping; phase 1 = `tools/cut7_acceptance.py` unedited; phase 2 =
  `tests/acceptance/test_n2_cut9.py`; the closing line naming the
  declared unit count 30 = `len(CUT9_ARMS)`, pinned separately by
  `test_the_declared_units_are_unique_and_number_thirty`; the docstring
  carrying the cut-8 citation ruling above).
- [ ] **Step 2:** Run on the certified volume:
  `uv run --frozen python tools/cut9_acceptance.py`. Expected: exit 0,
  each phase's counts quoted verbatim, the closing line naming 30.
- [ ] **Step 3:** Full gate block; quote the summary line. Commit:
  `test(cut9): certified acceptance runner`. Append and commit the
  ledger.

### Task 11: Results record, banking, and close-out

**Files:**
- Create: `docs/plans/2026-08-23-conformance-cut-9-results.md`
- Modify: the spec (promote to
  `docs/designs/2026-08-23-world-index-root-lifecycle-design.md`), the
  adoption ledger (rows 2, 4, 5),
  `docs/designs/2026-08-22-log-verification-design.md` (limitations 2, 3,
  6), `docs/designs/2026-08-03-world-index-packaging-design.md`
  (limitation 5), the guide pages and README the stale-claim grep flags,
  cut 9's status header (discharge note only)

**Interfaces:**
- Consumes: everything; this task is spec §8 step 7 executed exactly.

- [ ] **Step 1: Write the results record** on the cut-8 pattern: the
  discharge statement, the certified tuple, per-row dispositions (1 full
  + 4 partial, 19 + 11 = 30), the evidence commands with their quoted
  summary lines (each run after the last tree edit), the integration
  state (branch, base, unmerged — the `--no-ff` merge is the human
  partner's act), and the amendment enumeration.
- [ ] **Step 2: Apply the banking amendment set:** promote the spec;
  correct adoption-ledger row 4 (the five commands as landed, pushed
  atoms head named), row 2 (fork construction closes), row 5 (remainder
  shrinks to intent qualification, event-level L8, and L13's preimage
  resolver); close or narrow log-verification limitations 2, 3, 6;
  narrow packaging limitation 5 (act-minted forks' `forked_from`
  act-derived); record the cut-8 successor ruling in the results record's
  amendment enumeration (its store-refusal declarations deliberately
  stale, discharge standing as the frozen record, cut 9 the successor —
  Task 4's ledger ruling cited by number); run the stale-claim grep
  (`rg -n "fork construction remains|store subjects are shape-only|row 4's|wait on row 4" docs/ README.md`)
  and correct what it finds.
- [ ] **Step 3:** Re-run `uv run --frozen python tools/cut9_acceptance.py`
  and the full gate block after the last edit; quote the lines in the
  results record. Finalize the execution ledger (rulings complete, heads
  recorded). Commit:
  `docs(log): bank the root-lifecycle slice and discharge cut 9`.
- [ ] **Step 4: STOP.** The `--no-ff` merge of
  `design/world-index-root-lifecycle` to `main` is the human partner's
  act, inheriting the prior cuts' reachability constraints plus cut 9's
  freeze pin `0977bde`.
