# Root Lifecycle and the Store Substrate (World-Index Slice 4) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement world-index slice 4 — the fail-closed writer state, the
atoms lifecycle commands, store subjects through the verification surface,
`restore_root`, and the fork acts — discharging frozen conformance cut 9.

**Architecture:** An atoms design gate ships five root-kind-agnostic
obligations (three mutating lifecycle commands, one state query, one
migration); Science consumes them through `science.root`'s callback seam
(the only atoms importer), widens the slice-3 verification surface to store
subjects, and builds `restore_root` and the fork acts on top. Every claim
is certified as one of cut 9's 30 frozen declaration units.

**Tech Stack:** Python 3 (`uv run --frozen`), pytest, the certified `atoms`
engine (editable path dependency at the sibling checkout), the N2
declaration harness, `tools/cutN_acceptance.py` runners.

**Spec:** `docs/superpowers/specs/2026-08-23-world-index-root-lifecycle-design.md`
**Frozen cut:** `docs/designs/2026-08-23-conformance-cut-9.md` (frozen at
`0977bde`; the cut's §3 declarations are the acceptance criteria — read
both before any task).

## Global Constraints

- The frozen cut is not edited; only its status header may change, at
  discharge. Prior cuts' acceptance runners (`tools/cut7_acceptance.py`,
  `tools/cut8_acceptance.py`) must stay exit 0 after every task.
- `science.root` stays the only module importing `atoms`; the architecture
  test that asserts this must be extended, never weakened.
- Durable arms live on the repository's own volume — never `/tmp`, the
  scratch volume, or `/dev/shm`.
- Every count claim quotes pytest's own summary line under `pipefail` —
  never a collect-only count (addopts already sets `-q`; do not double it).
- Atoms is root-kind agnostic: it stores lifecycle state and opaque genesis
  bytes; Science owns `corpus`/`world`/`store` payload construction and
  validation. No Science vocabulary (verdicts, subjects) enters atoms.
- Conventional commits; no AI-attribution trailers. After every task:
  append the execution ledger (rulings + the task's head commit) and commit
  it with the task.
- Gates per Science task: the project's test suite plus its ruff/pyright
  gates, run as the existing tasks run them (see `python/README.md`).

---

### Task 0: Tracking setup

**Files:**
- Create: `docs/plans/2026-08-23-root-lifecycle-ledger.md`
- Modify: none

**Interfaces:**
- Produces: the execution ledger every later task appends to — a tracked,
  durable path (slice 2 lost R1–R15 to an untracked one; never relocate it).

- [ ] **Step 1:** Write the ledger skeleton: title ("Root lifecycle —
  execution ledger, world-index slice 4"), the plan/spec/cut paths with the
  freeze hash `0977bde`, an empty `## Rulings` section (rulings numbered
  R1…, written at task boundaries, never rewritten after the fact), and a
  `## Heads` section for the atoms and Science head commits per task.
- [ ] **Step 2:** Commit: `git add docs/plans/2026-08-23-root-lifecycle-ledger.md docs/superpowers/plans/2026-08-23-root-lifecycle.md && git commit -m "docs(plans): root-lifecycle implementation plan and execution ledger"`.

### Task 1: Atoms root-lifecycle design (atoms repository — design gate)

**Files:**
- Create (in `~/d/atoms`): `docs/2026-08-23-root-lifecycle-commands-design.md`
  on branch `design/root-lifecycle` in a fresh atoms worktree.

**Interfaces:**
- Produces: the reviewed atoms design the Task 2 implementation follows and
  Tasks 3–8 consume through `science.root`.

- [ ] **Step 1:** In the atoms checkout, create worktree
  `.worktrees/root-lifecycle` on branch `design/root-lifecycle`.
- [ ] **Step 2:** Write the design document covering exactly spec §2–§4,
  with these contracts pinned verbatim from the spec:
  - **The fail-closed writer state** (spec §2): writability a granted state
    in host bookkeeping; the coordinator refuses every mutation on a root
    not granted writability; a metadata-less tree cold-bootstraps read-only
    and unserviceable. Grantors: `register_root` **only for its own
    recorded local initialization operation** (recorded before genesis; the
    matching retry — and only it — completes a crash-interrupted grant; the
    bare matching-existing-genesis arm never grants), and `fork_root` after
    its genesis is durable.
  - **The root/host binding** (spec §2): the grant record carries a binding
    to the host's stable machine identity and the root's canonical path,
    validated before any grant is honored; mismatch reports
    `binding-mismatched` and conveys no grant; moving or renaming a
    writable root invalidates its grant, no writable rebind exists. **The
    binding's exact carrier is this design's to choose** — the requirement
    is frozen, the representation is not.
  - **The migration** (spec §2): a version-bound, operator-authorized
    transition recording the grant with a fresh binding; never
    auto-upgrades a metadata-less or restored copy; provenance is attested,
    not proven.
  - **`replicate_root`** (spec §4): source-lease-coherent copy; destination
    bookkeeping first, read-only stamp durable before any tree byte is
    exposable; grants neither writability nor serviceability; no-clobber
    with a durable operation identity; exact-retry.
  - **`fork_root(…, genesis_payload, surface_paths, dest_overrides)`**
    (spec §4): opaque genesis bytes; `dest_overrides` applied before
    baseline capture, genesis, and grant, interpreted never; baseline
    captured over `surface_paths` (the existing registration baseline
    machinery); new chain, genesis durable before the grant; retry splits
    at the grant — pre-grant proves genesis/baseline/tree, post-grant
    recognizes the operation identity and returns success.
  - **`grant_read_serviceability`** (spec §4): structural rechecks only
    (non-writable; unserviceable, or already read-only serviceable →
    success without another write); no verdict channel; atoms spells no
    `restore_root`; out-of-band outside Science's restore orchestration.
  - **`read_lifecycle_state`** (spec §4): the closed five-value union —
    writable / read-only serviceable / read-only unserviceable /
    metadata-less / binding-mismatched — binding validated as part of the
    reading.
- [ ] **Step 3:** Commit the design on the branch.
- [ ] **Step 4: STOP.** Hand the design to the human partner for the
  atoms-side review. Do not start Task 2 until the review closes; fold its
  findings into the design first. Record the review's rulings in the
  Science ledger.

### Task 2: Atoms implementation — lifecycle commands, state query, migration

**Files (in the atoms worktree):**
- Create: `python/src/atoms/coordinator/lifecycle.py`,
  `python/tests/test_lifecycle_commands.py`
- Modify: `python/src/atoms/coordinator/commands.py` (`register_root`'s
  initialization operation and grant; the writability gate on
  `append_intent`/`run_transaction`), `python/src/atoms/coordinator/__init__.py`
  (exports)

**Interfaces:**
- Produces (consumed by Science via `science.root` callbacks): the five
  public names as the reviewed Task 1 design finalizes them —
  `replicate_root`, `fork_root`, `grant_read_serviceability`,
  `read_lifecycle_state`, and the migration command — plus the five-value
  lifecycle-state union type.

- [ ] **Step 1: Write the failing lifecycle-state tests**: fresh
  `register_root` → writable; interrupted-registration fabrication
  (recorded operation, durable genesis, no grant) → matching retry grants,
  bare re-registration never grants; metadata-less tree → metadata-less;
  binding delta (host, then path, one at a time) → binding-mismatched;
  each state read back through `read_lifecycle_state`.
- [ ] **Step 2:** Run them; every one fails for want of the lifecycle
  module. Implement the writer state, binding, and query. Run to green.
- [ ] **Step 3: Write the failing command tests**: `replicate_root`
  (chain and payload byte-identical, dest read-only unserviceable,
  no-clobber refusal, interrupted-copy fabrications in both windows,
  exact-retry); `fork_root` (overrides applied before baseline; baseline =
  destination surface after overrides; new chain with the supplied genesis;
  kill-between fabrication → read-only, pre-grant retry completes,
  post-grant retry returns success after a legitimate write changed the
  tree); `grant_read_serviceability` (structural refusals: writable root,
  metadata-less root; idempotent success); migration (authorized success on
  a fabricated pre-lifecycle vintage → writable with fresh binding;
  refusals: metadata-less, binding-mismatched).
- [ ] **Step 4:** Run; fail. Implement the three commands and the
  migration. Run to green.
- [ ] **Step 5:** Run the full atoms suite and its ruff/pyright gates;
  quote the summary line.
- [ ] **Step 6:** Commit on the branch; merge `--no-ff` to local atoms
  `main`; **push atoms `main`** (spec §8 step 5 makes the push part of the
  gate, not a trailing disclosure). Record the pushed head hash in the
  Science ledger's `## Heads`.

### Task 3: Science store construction and the widened projection

**Files:**
- Create: `python/tests/test_store_root.py`
- Modify: `python/src/science/root.py` (`init_store_root`, the store
  genesis payload, the atoms lifecycle callbacks),
  `python/src/science/world/verify.py` (`RootKind` gains `"store"`,
  `registered_surface_paths` gains the store projection)

**Interfaces:**
- Consumes: Task 2's commands through new `science.root` callbacks.
- Produces: `init_store_root(store_root: Path) -> str` (the minted
  32-lowercase-hex `store_id`; refuses a populated payload root);
  `store_surface_paths(store_root: Path) -> tuple[str, ...]` — the
  canonical projection: every non-bookkeeping root-relative entry, symlinks
  not followed; the `science.store-root.v1` genesis payload codec
  (`store_id`, optional `forked_from`).

- [ ] **Step 1:** Write failing tests: `init_store_root` mints a fresh
  opaque id, registers an empty surface, leaves the root writable
  (`read_lifecycle_state` via the callback); a populated payload root
  refuses; the genesis payload round-trips and a `forked_from`-absent
  non-fork form is enforced; the store projection excludes the chain leaf
  and engine bookkeeping, includes everything else root-relative, and does
  not follow symlinks; the architecture test still holds (atoms imported
  only in `root.py`).
- [ ] **Step 2:** Run; fail. Implement, following `_world_genesis_payload`
  and `init_world_root` as the pattern.
- [ ] **Step 3:** Run tests and gates. Commit:
  `feat(root): store roots and the canonical store projection`. Append and
  commit the ledger.

### Task 4: Store subjects through the verification surface

**Files:**
- Create: `python/tests/test_store_subjects.py`
- Modify: `python/src/science/world/verify.py` (remove
  `_refuse_store_subject` and both call sites; widen `_subject_hold` and
  the audit target rule), `python/src/science/root.py` (`anchor_heads`
  store widening, `export_head_artifact` store arm, `audit_log` store
  path)

**Interfaces:**
- Consumes: Task 3's projection and genesis codec.
- Produces: `anchor_heads(world, corpus_ids, *, store_roots: tuple[tuple[str, Path], ...] = (), actor)` —
  each pair `(store_id, root)`, the genesis verified to carry that
  `store_id` **before head acceptance or registry mutation**;
  `export_head_artifact(world, subject, *, store_root: Path | None = None)`
  under the same resolution contract; `audit_log` accepting a
  `StoreSubject` with a supplied root, one hold across inspection, surface
  capture, and evaluation.

- [ ] **Step 1:** Write failing tests: anchor a store and find its
  store-subject log-head record in the registry; genesis/`store_id`
  mismatch refuses before any registry mutation (registry byte-identical
  after the refusal); export round-trips a store head under
  `science.head-artifact.v1`; a store audit returns each of the four
  verdicts over fabricated states (validated; truncation → refuted against
  the store anchor — cut 9 L4 u1's mechanism; interior damage → malformed;
  empty observer set → unresolvable); the store audit holds one boundary
  across inspection, surface capture, and evaluation (assert the hold
  spans the three, cut 9 label 9's claim); `StoreSubjectUnsupported` is
  deleted, not merely unraised.
- [ ] **Step 2:** Run; fail. Implement — the widening only: codecs already
  carry stores; touch acts, wrappers, and the reachable evaluator path.
- [ ] **Step 3:** Run tests and gates; run `tools/cut8_acceptance.py`
  (the evaluator surface moved). Commit:
  `feat(world): store subjects through anchor, export, and audit`. Append
  and commit the ledger.

### Task 5: Lifecycle wrappers and gate precedence

**Files:**
- Create: `python/tests/test_lifecycle_wrappers.py`
- Modify: `python/src/science/root.py` (thin wrappers: `replicate_root`,
  `read_lifecycle_state`, migration passthrough)

**Interfaces:**
- Consumes: Task 2's commands.
- Produces: `science.root.replicate_root(source_root, dest_root)` (appends
  nothing — a replica's chain arrives unchanged);
  `science.root.read_lifecycle_state(root) -> LifecycleState`; the
  operator-authorized migration passthrough, refusals included.

- [ ] **Step 1:** Write failing tests: a completed replica reads read-only
  unserviceable and its chain is byte-identical (cut 9 L10 u3/u4's
  residues); a metadata-less copy of a **corpus** root refuses cooperative
  registered-surface mutation at the writability gate while its chain
  evaluation still reads `unresolvable at step 3` — and a **writable**
  live root carrying an unresolved pending entry still refuses
  `PendingUnresolved` (cut 9 L2 u1 + label 11: the precedence claim,
  vacuous unless the construction carries the pending entry and, for the
  contrast, a real grant).
- [ ] **Step 2:** Run; fail. Implement the wrappers.
- [ ] **Step 3:** Run tests and gates. Commit:
  `feat(root): lifecycle wrappers and the writability-gate precedence`.
  Append and commit the ledger.

### Task 6: `restore_root`

**Files:**
- Create: `python/tests/test_restore_root.py`
- Modify: `python/src/science/root.py` (`restore_root`),
  `python/src/science/world/verify.py` (any shared subject-binding helper)

**Interfaces:**
- Consumes: Tasks 2–5 (query, grant, evaluator store path).
- Produces: `restore_root(dest_root, subject, observers) -> RestoreOutcome`
  where `RestoreOutcome` is a frozen dataclass `(report: LogReport,
  admitted: bool)`; `subject: CorpusSubject | StoreSubject` (a world
  subject is unspellable by type); `observers` the evaluator's observer
  set.

- [ ] **Step 1:** Write failing tests, one per spec §7.2 step: a
  malformed copied chain reaches `evaluate_log` and returns `malformed`
  (`admitted=False`, root unserviceable — never a pre-evaluation
  exception); a validated store copy admits to read-only serviceable
  exactly once (idempotent re-restore); a validated report with a subject
  mismatch (genesis carries another `store_id`; for a corpus, manifest
  carries another `corpus_id` while the genesis passes form validation)
  does **not** admit; empty observer set → `unresolvable`, replay not
  reached, unserviceable (L10 u11); an interrupted copy missing payload
  files the chain's surface names → never `validated`, verdict preserved
  (L10 u10 — constructed by omission, never chain damage, the cut §6
  freeze obligation); two metadata-less copies of one `store_id` restored
  into service → both read-only, writes refused (L10 u9); restore never
  grants writability; the whole act runs under one held destination
  boundary (assert the lock is held across the evaluate→grant seam).
- [ ] **Step 2:** Run; fail. Implement.
- [ ] **Step 3:** Run tests and gates. Commit:
  `feat(root): restore_root under one held boundary`. Append and commit
  the ledger.

### Task 7: The fork acts

**Files:**
- Create: `python/tests/test_fork_acts.py`
- Modify: `python/src/science/root.py` (`fork_corpus`, `fork_store`, the
  fork genesis payloads), `python/src/science/world/verify.py`
  (genesis-form validation: fork forms carry `forked_from` and a non-empty
  baseline; non-fork forms still require empty)

**Interfaces:**
- Consumes: Task 2's `fork_root`; Task 3's projection and codecs.
- Produces: `fork_corpus(source_root, dest_root) -> ForkOutcome` (frozen
  dataclass: `corpus_id`, the authored manifest mapping);
  `fork_store(source_root, dest_root) -> str` (the new `store_id`). Fork
  genesis payloads carry `forked_from = (parent genesis digest, parent
  head digest)`; the corpus child manifest carries `forked_from = (parent
  corpus_id, parent corpus-state identity)`, act-derived, installed via
  `dest_overrides` before the grant.

- [ ] **Step 1:** Write failing tests: `fork_corpus` mints a fresh opaque
  id independent of path and name, with no re-mint API (W13 u1/u2); the
  child manifest is present and complete before the destination is
  writable; the fork genesis carries the parent's genesis and head digests
  and its own non-empty baseline equal to the destination surface after
  overrides (L10 u1; cut 9 label 10); genesis-form validation accepts the
  fork forms and still refuses a non-empty baseline on a non-fork genesis;
  the L6 pair over a forked root — anchor the fork, delete a
  baseline-covered pre-log member → refuted at replay, with the
  declaration-time assertion that the member is baseline-covered and
  pre-log; the anchor-free consistent rewrite omitting it → unresolvable,
  never validated, never refuted (L6 u1/u2, the cut §6 only-delta
  obligation); a parent anchor in a fork-subject observer set participates
  in no genesis or ancestry judgment (L10 u2); two same-child-subject
  chains under different fork geneses, original anchor supplied → refuted
  (L4 u2).
- [ ] **Step 2:** Run; fail. Implement.
- [ ] **Step 3:** Run tests and gates; rerun `tools/cut8_acceptance.py`
  (genesis-form validation moved). Commit:
  `feat(root): fork acts, fork geneses, and the L6 lift in code`. Append
  and commit the ledger.

### Task 8: Fork-of admission and `admit_arrival`'s inspection modes

**Files:**
- Create: `python/tests/test_arrival_modes.py`
- Modify: `python/src/science/world/registry.py` (fork-of admission over
  act-minted manifests), `python/src/science/root.py` (`admit_arrival`
  mode selection)

**Interfaces:**
- Consumes: Task 5's `read_lifecycle_state`, Task 7's `ForkOutcome`.
- Produces: `World.admit` accepting the act-minted fork manifest
  (fixture-authored fork manifests removed from the production path);
  `admit_arrival` branching over the five-value union.

- [ ] **Step 1:** Write failing tests: a `fork_corpus` product admits
  through `World.admit`'s fork-of path with no fixture manifest; arrival
  mode per state — read-only serviceable → registered inspection;
  read-only unserviceable, metadata-less, binding-mismatched → detached;
  **writable → refused** (constructed through `register_root`'s own path,
  never fabricated bookkeeping — the cut §6 obligation); a restored corpus
  arrival admits registered-mode only after `restore_root`; a store
  subject remains unspellable at the arrival act (cut 9 label 8).
- [ ] **Step 2:** Run; fail. Implement.
- [ ] **Step 3:** Run tests and gates; rerun `tools/cut8_acceptance.py`
  (the admission surface moved). Commit:
  `feat(world): act-minted fork admission and lifecycle-aware arrival`.
  Append and commit the ledger.

### Task 9: The 30 N2 declarations

**Files:**
- Create: `python/tests/test_cut9_declarations.py` (declarations as data +
  the harness), reusing the cut-8 harness pattern in
  `python/tests/test_cut8_declarations.py`

**Interfaces:**
- Consumes: every prior task's surface.
- Produces: the 30 declaration units cut 9 §3 freezes — L2 u1; L4 u1–u2;
  L6 u1–u2; L10 u1–u12; W13 u1–u2; labels 1–11 — each naming its check
  nodes in Tasks 3–8's test files (declare, cite, never re-implement).

- [ ] **Step 1:** Declare all 30 units as data, unit-for-unit against the
  frozen cut's §3.1 dispositions and §3.3 labels, each carrying its §5
  declaration-time obligations (fabrication well-formedness via
  `inspect_chain` for chains and `read_lifecycle_state` agreement for
  bookkeeping; L6 u1's baseline-covered-and-pre-log assertion; L6 u2's
  byte-difference and omission assertions; L4 u2's same-subject
  differing-genesis assertion; L10 u9's both-metadata-less assertion; the
  migration-vintage and single-binding-delta assertions; L2 u1's
  pending-entry-and-no-metadata plus granted-contrast assertions) and the
  three §6 freeze obligations as declaration-time checks.
- [ ] **Step 2:** Run the audit over a copy of the package; every one of
  the 30 arms resolves `sound`. Fix any `vacuous`/`uncollected`/`stale` as
  harness or declaration defects, never by weakening a check.
- [ ] **Step 3:** Run all gates; quote the summary line. Commit:
  `test(cut9): declare the 30 frozen arms`. Append and commit the ledger.

### Task 10: Certified acceptance

**Files:**
- Create: `tools/cut9_acceptance.py`

**Interfaces:**
- Consumes: Task 9's declarations; the prior runners.
- Produces: the certified acceptance runner chaining cuts 5–9.

- [ ] **Step 1:** Implement the runner mirroring `tools/cut8_acceptance.py`
  (same exit-code discipline and certified-tuple checks; it chains the
  prior cuts' runners, then runs cut 9's declarations).
- [ ] **Step 2:** Run it on the certified volume: exit 0, each cut's count
  quoted from its own output, cut 9 reporting 30.
- [ ] **Step 3:** Run the full suite and gates; quote the summary line.
  Commit: `test(cut9): certified acceptance runner`. Append and commit the
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
  discharge statement, the certified tuple, per-row dispositions (1 full +
  4 partial, 19 + 11 = 30), the evidence commands with their quoted
  summary lines (each run after the last tree edit), the integration
  state (branch, base, unmerged — the `--no-ff` merge is the human
  partner's act), and the amendment enumeration.
- [ ] **Step 2: Apply the banking amendment set:** promote the spec;
  correct adoption-ledger row 4 (the five commands as landed, pushed
  atoms head named), row 2 (fork construction closes), row 5 (remainder
  shrinks to intent qualification, event-level L8, and L13's preimage
  resolver); close or narrow log-verification limitations 2, 3, 6; narrow
  packaging limitation 5 (act-minted forks' `forked_from` act-derived);
  run the stale-claim grep over the user-facing docs and correct what it
  finds.
- [ ] **Step 3:** Re-run `tools/cut9_acceptance.py` and the full suite
  after the last edit; quote the lines in the results record. Finalize the
  execution ledger (rulings complete, heads recorded). Commit:
  `docs(log): bank the root-lifecycle slice and discharge cut 9`.
- [ ] **Step 4: STOP.** The `--no-ff` merge of
  `design/world-index-root-lifecycle` to `main` is the human partner's
  act, inheriting the prior cuts' reachability constraints plus cut 9's
  freeze pin `0977bde`.
