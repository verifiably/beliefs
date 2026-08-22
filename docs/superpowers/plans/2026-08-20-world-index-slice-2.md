# World Index Slice 2 Implementation Plan

**Status:** Executed. All 14 tasks are complete (plus an inserted Task 13.5 that restored
the project-wide Pyright gate) on branch `design/world-index-slice-2`, based on `f3a14bf` on
`main`; see the branch's close-out commit for the final documentation state. Conformance cut 7's 48 declarations are discharged on the certified tuple; the
results are recorded in `docs/plans/2026-08-20-conformance-cut-7-results.md`.

**Merged.** `design/world-index-slice-2` was merged into `main` on 2026-08-22 with `--no-ff`
(integration commit `83744e7`), preserving history as the constraint below requires; the branch
and its worktree are removed. The constraint itself outlives the merge.

> **Integration constraint — merge preserving history.** Cut 6's 22 arms all declare
> `module="world.py"`, and Task 3 moved that file to `world/registry.py`.
> `python/tests/acceptance/test_n2_cut6.py` was amended to audit cut 6's source mutations
> against the pre-move tree at commit **`4a7dc19`**, and Task 12 added a freeze guard
> pinning that amended file to **`c8c0b12`**. A squash merge, or a rebase that orphans
> `4a7dc19`, reds cut 6 permanently and cannot be repaired without editing a frozen cut.

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:executing-plans` to implement this plan task-by-task. Use
> `superpowers:test-driven-development` for every production task,
> `superpowers:verification-before-completion` before every completion claim, and
> `superpowers:requesting-code-review` at the review gates named below. Do not run
> tasks after a review gate until the reviewer closes it.

**Goal:** Complete ledger artifact 1 by publishing content-addressed world epochs with
four derived maps, a producer snapshot, four fixture-bound derivation receipts, coherent
corpus-state/head anchors, explicit rule holding, bound reads, and whole-epoch GC; expose
the one `atoms.read_chain` prerequisite first; and discharge frozen conformance cut 7.

**Architecture:** `atoms` exposes one recovery-disciplined projection of its already
validated chain. Science keeps that type behind `science.root` and injects one root-taking
chain-head callback into the engine-free `science.world` package. The existing slice-1
module first becomes a package without semantic change. The existing corpus operation
lock then gains writer/capture holder kinds; a build preflights under the world lock,
captures each corpus serially under that corpus's lock, derives immutable bytes with no
locks held, rechecks rule bindings, and publishes the epoch plus `current` in one existing
durable transaction. Reads validate a complete named carrier under the world lock and
return stamped, closed outcomes. GC deletes only complete non-current epochs and reports
the evidence path it severs.

**Tech Stack:** Python 3.11+, stdlib synchronization and hashing, PyYAML, `nodes-core`,
`atoms-core`, pytest, Ruff, Pyright, and the existing N2 sabotage/certified-acceptance
harness. Add no dependency.

**Spec:** `docs/designs/2026-08-20-world-index-slice-2-design.md`; frozen acceptance
authority: `docs/designs/2026-08-20-conformance-cut-7.md`. Read both completely before
execution. The cut is 7 full + 4 part rows, 38 selected + 10 labeled = 48 declaration
units.

## Global Constraints

- Execute Tasks 1 and 2 in the `atoms` repository and land them there before changing
  Science. `read_chain` gets its own approved design; do not treat this Science plan as
  authority to bypass the `atoms` review discipline.
- `ChainView.entries` is nonempty and in validated chain order;
  `entries[0][0] == genesis_digest`; `entries[0][1]` is the existing genesis entry;
  `entries[-1][0] == tip`. Promote the existing `Entry` union unchanged.
- `read_chain` composes `_recovery_lease` and `_registered_root`; it adds no validation,
  partial view, lease type, or consumer-visible lease.
- Science calls `read_chain` only through `science.root`, at the four frozen boundaries:
  covered-corpus capture, build-start world head, named-epoch open barrier, and
  current/open-or-delete barrier. Do not use it for genesis/mirror audit, explicit
  anchoring, fork construction, or replay.
- Task 3 is a pure `git mv` plus imports. It must be committed green before any slice-2
  Science behavior is added. Never recreate `python/src/science/world.py`.
- No `atoms` import outside `python/src/science/root.py`; retain and extend the existing
  capability-boundary test.
- Reuse `_RootState.lock` from `corpus.py`; do not add a second corpus lock. Cross-process
  exclusion remains a deployment obligation, not code in this slice.
- A build accepts an explicit coverage set and four exact rule bindings. It never means
  "all live" and never silently retries a drift or contention refusal.
- Enumeration is exactly once per covered corpus. A captured record of an enumerated but
  ungoverned stored kind raises `EnumeratedKindUngoverned`; an absent kind is an ordinary
  empty enumeration.
- Rules are trusted executable content admitted by an explicit install act. Verify their
  digests and fixtures before holding them. Do not pretend Python execution is a security
  sandbox and do not add a plugin framework or subprocess protocol.
- Pin the new identity domains exactly as the specification spells them:
  `science.fixture-set.v1`, `science.enumeration-rule.v1`,
  `science.derivation-receipt.v1`, `science.epoch.v1`,
  `science.producer-snapshot.v1`, `science.retraction-enumeration.v1`,
  `science.certification-inventory.v1`, and `science.coreference-map.v1`. Implement the
  four exact canonical subject projections pinned by specification §7.6; do not fold
  packaging, receipt, or corpus-state identity into belief.
- All YAML documents are deterministic and closed: duplicate keys, unknown keys,
  malformed values, missing members, and extra members refuse. Carrier validation and
  receipt validation remain separate so a structurally parseable but semantically
  unsound receipt yields outcome `malformed` instead of `EpochMalformed`.
- Publication is one world-root `WritePlan`: create-only epoch members plus create/replace
  of `epochs/current`. Exact rebuild is idempotent; no epoch member is replaced.
- Opening, following `current`, and deletion hold the one world lock from recovery barrier
  through carrier inspection. Private locked helpers must not reacquire the non-reentrant
  lock.
- The coreference query span is the registry's live-id set. Epoch coverage may be wider;
  insufficient containment and any non-`validated` receipt outcome are indeterminate.
  `EdgeIndeterminate` names every uncovered id and/or the exact receipt outcome.
- GC is explicit, whole-epoch, and non-current only. Do not add automatic retention,
  sequence numbers, tombstones, or an exact-retry claim.
- Portable tests make no durability claim. Certified arms go through
  `python/tools/cut7_acceptance.py` and error, never skip, off the certified tuple.
- Do not edit `python/tools/cut5_acceptance.py`, `python/tools/cut6_acceptance.py`,
  `python/tests/n2_arms_cut5.py`, `python/tests/n2_arms_cut6.py`, or their historical path
  spellings. The cut-7 runner may invoke the older runners as a prefix.
- Use conventional commits without attribution trailers. Stage only named paths; never
  use `git add -A` or `git commit -a`.
- `atoms` gates, from `python/`: `uv run --frozen pytest -q`,
  `uv run --frozen ruff check .`, `uv run --frozen pyright`.
- Science gates, from `python/`: `uv run --frozen pytest -q`,
  `uv run --frozen ruff check .`, `uv run --frozen pyright`.

---

### Task 1: Design and approve the public `atoms.read_chain` command

**Repository:** `atoms`, in a fresh feature worktree created according to that
repository's `AGENTS.md`.

**Files:**
- Create: `docs/plans/2026-08-20-public-chain-read-design.md`
- Inspect and amend only if the new public command makes a live status claim stale:
  `AGENTS.md`, `README.md`, `docs/deferred-obligation-ledger.md`,
  `python/tests/test_docs_status.py`

**Interfaces to freeze:**

```python
@dataclass(frozen=True)
class ChainView:
    genesis_digest: str
    entries: tuple[tuple[str, Entry], ...]
    tip: str


def read_chain(backend, project_root, metadata_root, storage) -> ChainView: ...
```

- [ ] **Step 1: Create and verify the isolated worktree.** From the real `atoms`
  checkout, read `AGENTS.md`, confirm the source tree is clean, create a branch such as
  `design/public-chain-read` under that repository's `.worktrees/`, and confirm the new
  worktree resolves to the shared git common directory. Do not nest it inside the Science
  worktree.

- [ ] **Step 2: Perform the required seam review before drafting.** Read the authority
  design's recovery-lease and chain sections, the A5b/A7a/A7b designs,
  `docs/deferred-obligation-ledger.md`, `coordinator/lease.py`,
  `coordinator/recover.py`, `coordinator/commands.py`, and `chain/read.py`. Record why the
  command admits no new deferred shape: it returns only `_registered_root`'s complete
  `ValidatedChain` after recovery and exposes no capability or lease.

- [ ] **Step 3: Draft the command design.** Pin the public dataclass, the unchanged public
  `Entry` union, all four `ChainView` invariants, the existing-error behavior, command
  choreography (`_recovery_lease` then `_registered_root`), descriptor/lease lifetime,
  recovery-survivor semantics, refusal of an invalid or unregistered root, and the exact
  tests and documentation impact. State explicitly that there is no second reader,
  validation pass, partial mode, or mutable operation.

- [ ] **Step 4: Self-review the design against the tree.** Trace every proposed name to an
  existing symbol. Verify that `_registered_root` proves nonempty entries and a non-`None`
  tip, that `Entry` is the existing union rather than a copy, and that `ChainStateInvalid`
  remains the invalid-chain refusal. Grep the repository for public-command inventories
  and stale "three commands" claims. Run the docs/status tests named by `AGENTS.md`.

- [ ] **Step 5: Hand the design to the owner and stop.** Do not implement the command until
  the owner and the independent `atoms` reviewer close findings and approve/freeze the
  design. Apply review corrections in the `atoms` worktree, rerun the docs gates, then
  commit only the reviewed design/status paths:

```bash
git add docs/plans/2026-08-20-public-chain-read-design.md AGENTS.md README.md docs/deferred-obligation-ledger.md python/tests/test_docs_status.py
git commit -m "docs(coordinator): design public chain read"
```

Omit unchanged paths from `git add`.

---

### Task 2: Implement `atoms.read_chain` from existing validated-chain internals

**Repository:** the approved `atoms` feature worktree from Task 1.

**Files:**
- Modify: `python/src/atoms/coordinator/commands.py`
- Modify: `python/tests/test_coordinator_commands.py`
- Modify: `python/tests/test_coordinator_architecture.py`
- Modify: `python/tests/test_packaging.py`
- Modify: the approved Task-1 design/status files only where landing makes their status
  claims stale

**Public surface:** `Entry`, `ChainView`, and `read_chain` from
`atoms.coordinator.commands`; no package-wide convenience re-export unless the approved
`atoms` design explicitly requires one.

- [ ] **Step 1: Write failing public-surface and happy-path tests.** Register a root,
  append at least one entry, call `read_chain`, and assert the returned tuple is nonempty,
  ordered, genesis-first, and tip-last. Assert `Entry` is the existing union imported from
  `atoms.chain.model`, not a duplicate type. Run:

```bash
uv run --frozen pytest tests/test_coordinator_commands.py tests/test_packaging.py -q
```

Expect import/attribute failures for `ChainView`, `Entry`, and `read_chain`.

- [ ] **Step 2: Write failing recovery and refusal tests.** Reuse the coordinator test
  helpers to leave a recoverable survivor, then assert `read_chain` completes recovery and
  returns the recovered complete chain. Corrupt a chain and assert the existing
  `ChainStateInvalid`; use an unregistered root and assert the existing precondition
  refusal. Assert no view is returned on either failure and the lease/descriptors are
  released before the caller receives a successful value.

- [ ] **Step 3: Implement the minimal projection.** Import and publicly export the existing
  `Entry`; add the frozen `ChainView`; then add one command body that acquires
  `_recovery_lease`, enters `_registered_root`, copies `ValidatedChain.entries`, and
  returns its genesis digest and validated tip. Rely on `_registered_root` for validation;
  do not call the chain validator again or catch/translate `ChainStateInvalid`.

- [ ] **Step 4: Pin the architecture.** Extend the architecture test to prove the new
  command uses the same lease/registered-root seam and exposes neither the lease nor a
  backend descriptor. Extend the packaging test to pin only the approved public names.

- [ ] **Step 5: Run focused and full gates.** From `atoms/python`:

```bash
uv run --frozen pytest tests/test_coordinator_commands.py tests/test_coordinator_architecture.py tests/test_packaging.py -q
uv run --frozen pytest -q
uv run --frozen ruff check .
uv run --frozen pyright
```

- [ ] **Step 6: Correct landing status and commit.** Update the approved design's status
  and grep user-facing docs for any claim invalidated by a fourth command. Stage only the
  implementation, tests, and actually changed docs:

```bash
git add python/src/atoms/coordinator/commands.py python/tests/test_coordinator_commands.py python/tests/test_coordinator_architecture.py python/tests/test_packaging.py docs/plans/2026-08-20-public-chain-read-design.md
git commit -m "feat(coordinator): expose validated chain reads"
```

- [ ] **Step 7: Obtain `atoms` code review and land it.** Request independent review
  against the approved design. Close findings, rerun the full gates, and integrate the
  `atoms` branch before changing Science's dependency lock or source checkout. Record the
  landed commit in this plan's execution notes; do not duplicate the command in Science.

---

### Task 3: Promote `science.world` from a module to a package, unchanged

**Repository:** Science slice-2 worktree.

**Files:**
- Move: `python/src/science/world.py` -> `python/src/science/world/registry.py`
- Create: `python/src/science/world/__init__.py`
- Modify: `python/tests/test_world_registry.py`
- Modify: `python/tests/test_corpus_state.py`
- Modify only if required by import resolution: `python/src/science/root.py`,
  `python/src/science/corpus.py`

**Invariant:** every current public `from science.world import ...` continues to work;
slice-1 behavior and bytes do not change.

- [ ] **Step 1: Record the clean baseline.** Confirm the Science worktree is clean and run:

```bash
uv run --frozen pytest -q
uv run --frozen ruff check .
uv run --frozen pyright
```

- [ ] **Step 2: Perform the plain move.** Use `git mv`; create `world/__init__.py` that
  re-exports exactly the old module's public surface and the existing private seam names
  consumed by `root.py`, `corpus.py`, and tests. Tests that monkeypatch implementation
  globals import `science.world.registry` explicitly. Do not rename, reformat, or split
  any slice-1 definition in this task.

- [ ] **Step 3: Prove the import and semantic surface is unchanged.** Run the world,
  corpus-state, root, capability-boundary, and cut-6 tests, then the full Science gates.
  Inspect `git diff --find-renames`; the registry implementation must show as a move plus
  only necessary import changes.

- [ ] **Step 4: Commit the green move alone.** Stage only the move, new facade, and import
  fixes:

```bash
git add python/src/science/world/registry.py python/src/science/world/__init__.py python/src/science/root.py python/src/science/corpus.py python/tests/test_world_registry.py python/tests/test_corpus_state.py
git commit -m "refactor(world): promote world module to package"
```

Omit unchanged paths. Do not combine Task 4 with this commit.

---

### Task 4: Replace the corpus lock with `OperationLock`

**Files:**
- Modify: `python/src/science/corpus.py`
- Modify: `python/src/science/errors.py`
- Create: `python/tests/test_operation_lock.py`
- Modify: `python/tests/test_corpus_write.py`

**Interfaces:**
- `OperationLock.__enter__` / `__exit__`: writer-kind acquisition, preserving
  `with self._operation:`.
- `OperationLock.capture()`: context manager for the build's nonblocking capture hold.
- Errors: `BuildContended`, `BuildHold`.

- [ ] **Step 1: Write the failing lock-state tests.** Cover free writer, writer-behind-
  writer queueing, capture refusing immediately behind either holder, writer refusing on
  arrival during capture, and writer refusing after it queued behind a writer but a
  capture generation began and ended before it could acquire. Use events/barriers with
  bounded joins; no sleeps as synchronization.

- [ ] **Step 2: Write the failing corpus integration test.** Hold the root state's capture
  context, invoke a real `CorpusWriter` operation from another thread, and assert
  `BuildHold` with no committed write. Confirm ordinary cooperating writers still
  serialize and succeed.

- [ ] **Step 3: Implement the smallest condition-based lock.** Back `OperationLock` with
  one `threading.Condition`, one holder kind, and one monotonically increasing capture
  generation. A writer snapshots the generation before any wait and refuses if it ever
  sees capture or wakes after the generation changed. Capture never waits. Replace only
  `_RootState.lock` construction and annotation; keep `CorpusWriter` call sites in their
  current context-manager shape.

- [ ] **Step 4: Run focused and full gates.** Run the new lock test, all corpus tests, then
  the full Science gates. Repeat the concurrency-focused test enough times to expose a
  missed wakeup, but do not add timing retries to production.

- [ ] **Step 5: Commit.**

```bash
git add python/src/science/corpus.py python/src/science/errors.py python/tests/test_operation_lock.py python/tests/test_corpus_write.py
git commit -m "feat(world): add coherent capture locking"
```

---

### Task 5: Add the self-verifying rules store and shipped v1 bindings

**Files:**
- Create: `python/src/science/world/rules.py`
- Create: `python/src/science/world/rules_v1/producer.py`
- Create: `python/src/science/world/rules_v1/retraction.py`
- Create: `python/src/science/world/rules_v1/certification.py`
- Create: `python/src/science/world/rules_v1/coreference.py`
- Create: `python/src/science/world/rules_v1/fixtures/*.yaml`
- Modify: `python/src/science/world/__init__.py`
- Modify: `python/src/science/root.py`
- Modify: `python/src/science/errors.py`
- Create: `python/tests/test_world_rules.py`
- Modify if package-data discovery requires it: `python/pyproject.toml`

**Interfaces:**

```python
@dataclass(frozen=True)
class RuleBinding:
    rule_identity: str
    implementation_identity: str


@dataclass(frozen=True)
class RuleBundle:
    symbol: str
    fixtures: tuple[tuple[str, bytes], ...]
    implementation: bytes


def shipped_rule_bundles() -> tuple[RuleBundle, ...]: ...
def install_rule_binding(world: World, bundle: RuleBundle) -> RuleBinding: ...
def install_shipped_world_rules(world: World) -> tuple[RuleBinding, ...]: ...
```

Private `resolve_rule_binding` returns the verified callable and exact source bytes for
build/receipt use. Errors: `RuleCollision`, `RuleNonconformant`, `RuleNotHeld`.

- [ ] **Step 1: Write failing identity and closed-loader tests.** Pin fixture-set identity
  as `science.fixture-set.v1` over sorted `(relative member name, SHA-256 content digest)`
  pairs and rule identity as `science.enumeration-rule.v1` over `(symbol,
  fixture-set identity)`. Assert member order does not move either identity, while symbol,
  fixture name, fixture bytes, or implementation bytes move the appropriate identity.
  Assert `rule.yaml` accepts exactly `symbol` and rejects duplicates/unknowns.

- [ ] **Step 2: Write failing install tests.** Install a conforming bundle and assert one
  transaction creates `rule.yaml`, every fixture, and the selected implementation beneath
  the content-addressed paths. Assert `init_world_root` alone holds no rule. Assert an
  exact byte-identical reinstall succeeds without a second mutation; any differing
  existing member raises `RuleCollision`; a wrong or raising implementation raises
  `RuleNonconformant` before a write plan is submitted.

- [ ] **Step 3: Implement deterministic resource loading and identities.** Use
  `importlib.resources` for the four package-owned bundles, `hashlib.sha256` for member and
  implementation content digests, and `science.identity.v1` for the two domain-separated
  identities. Keep fixture names relative and sorted. Do not add a registry, entry-point
  dependency, or installed-default selector.

- [ ] **Step 4: Implement held resolution.** Read `rule.yaml`, fixtures, and the exact
  implementation under the world lock; recompute every identity against the directory
  and file names; load the stored symbol from the selected implementation bytes; and run
  every stored fixture with exact equality. Any failed identity/fixture check means the
  pair is not held. The source loader is an explicit trusted-code admission boundary, not
  a sandbox; expose no ambient world/corpus object to the rule ABI.

- [ ] **Step 5: Implement explicit composition-root installation.** `open_world` injects
  the durable executor and chain callback but installs nothing.
  `root.install_shipped_world_rules(world)` iterates `shipped_rule_bundles()` and calls
  `install_rule_binding`; it runs only when the application explicitly invokes the act.
  Do not hide it inside initialization or opening.

- [ ] **Step 6: Run focused and full gates, then commit.** Include a packaging test that
  installs rules from a built wheel or installed package so fixture/source resources are
  not accidentally source-tree-only.

```bash
git add python/src/science/world/rules.py python/src/science/world/rules_v1 python/src/science/world/__init__.py python/src/science/root.py python/src/science/errors.py python/tests/test_world_rules.py python/pyproject.toml
git commit -m "feat(world): add fixture-bound rule storage"
```

Omit `python/pyproject.toml` if Hatch already includes the resources without a change.

---

### Task 6: Add explicit binding removal and its sever report

**Files:**
- Modify: `python/src/science/world/rules.py`
- Create: `python/src/science/world/epoch.py`
- Modify: `python/src/science/world/__init__.py`
- Modify: `python/src/science/errors.py`
- Modify: `python/tests/test_world_rules.py`

**Interface:**

```python
def remove_rule_binding(world: World, binding: RuleBinding) -> RuleRemovalReport: ...
```

`RuleRemovalReport` contains the exact removed binding and the sorted receipt identities
in retained epochs that name it. Error: `RuleBindingUnknown`.

- [ ] **Step 1: Write failing removal tests.** Assert unknown exact pairs refuse; removing
  one of several implementations deletes only that implementation; removing the final
  implementation also deletes `rule.yaml` and every fixture; empty directories are
  ignored. Assert the report names every retained receipt that loses this world's exact
  resolution path and no receipt using a sibling implementation. Because epoch
  publication is not implemented until Task 9, construct these retained-epoch inputs as
  fixture-authored closed eleven-member carriers under the cut's raw-write license; do
  not add an interim publisher.

- [ ] **Step 2: Implement one delete plan.** Under the world lock, resolve the exact held
  binding, scan retained closed epoch carriers for receipt bindings needed by the report,
  and submit one `WritePlan` of `DeleteOp`s. Put the frozen eleven-member inventory and a
  single private `_retained_receipt_bindings_locked` scanner in `epoch.py`; Tasks 8–11
  extend that same module and do not create another epoch scanner. Do not remove
  successors, individual fixtures, or epochs as a side effect. Do not add tombstones or
  automatic cleanup.

- [ ] **Step 3: Run focused and full gates, then commit.**

```bash
git add python/src/science/world/rules.py python/src/science/world/epoch.py python/src/science/world/__init__.py python/src/science/errors.py python/tests/test_world_rules.py
git commit -m "feat(world): remove exact rule bindings explicitly"
```

---

### Task 7: Implement the pure derivations, snapshot, and receipt projections

**Files:**
- Create: `python/src/science/world/derive.py`
- Modify: `python/src/science/world/rules_v1/*.py`
- Modify: `python/src/science/world/rules_v1/fixtures/*.yaml`
- Modify: `python/src/science/world/__init__.py`
- Create: `python/tests/test_world_derive.py`

**Pure values:** captured corpus records; address, producers, retraction-discovery, and
coreference projections; producer snapshot; retraction enumeration; certification
inventory; `DerivationReceipt`; and receipt outcome
`validated | refuted | unresolvable | malformed`.

**Identity interfaces:** each subject value exposes the exact specification-§7.6
projection and an identity computed with its pinned domain:
`science.producer-snapshot.v1`, `science.retraction-enumeration.v1`,
`science.certification-inventory.v1`, or `science.coreference-map.v1`.

- [ ] **Step 1: Write failing producer/address tests.** From immutable captured records,
  assert every live address and every `deprecated_ids` value maps to `(corpus_id, uid)`;
  every `produces` edge contributes its run address under the dataset address; values and
  keys are sorted deterministically; and moving an unchanged entity between two covered
  corpora changes location/state receipts but not the producer snapshot identity when the
  producers map and stable coverage are unchanged.

- [ ] **Step 2: Write failing retraction/certification/coreference tests.** Generalize the
  existing `standing_in_local_view` record reading to enumerate every retraction and group
  several event-token records under one target. Pin the location-free,
  resolution-free, by-kind certification inventory. Pin coreference deduplication by its
  ruled distinct key, sorted endpoint pairs, balance, and distinct-key count; duplicate
  submissions do not add weight. Keep edge state out of the member.

- [ ] **Step 3: Write failing subject-identity and receipt tests.** Pin all four exact
  specification-§7.6 projections and domains, including sorting and list shapes, before
  testing the one receipt family under `science.derivation-receipt.v1`. Assert all four
  receipts carry the same sorted `(corpus_id, corpus_state_identity)` tuple and exact rule
  binding; the retraction enumeration and certification inventory live in their receipts;
  and the coreference receipt has no semantic identity/belief-input field.

- [ ] **Step 4: Implement one captured-record model and four pure reducers.** Reuse
  existing stored-node projections and retraction parsing. Each shipped implementation
  receives only immutable projection values and returns deterministic projection values.
  Do not create per-map corpus scans, a mutable index object, or a generic derivation
  framework.

- [ ] **Step 5: Make all shipped fixtures normative and conforming.** Include fixtures
  that would fail for omission, wrong sorting, duplicate coreference weighting,
  deprecated-address loss, and retraction target loss. Test that each packaged bundle
  installs and independently evaluates to the same expected bytes.

- [ ] **Step 6: Run focused and full gates, then commit.**

```bash
git add python/src/science/world/derive.py python/src/science/world/rules_v1 python/src/science/world/__init__.py python/tests/test_world_derive.py
git commit -m "feat(world): derive epoch projections and receipts"
```

---

### Task 8: Implement coherent preflight and corpus capture

**Files:**
- Modify: `python/src/science/world/epoch.py`
- Modify: `python/src/science/world/registry.py`
- Modify: `python/src/science/world/rules.py`
- Modify: `python/src/science/world/__init__.py`
- Modify: `python/src/science/root.py`
- Modify: `python/src/science/errors.py`
- Create: `python/tests/test_world_build.py`
- Modify: `python/tests/test_capability_boundary.py`

**Boundary:** `World` receives one callback
`Callable[[Path], tuple[str, str]]`, returning `(genesis_digest, tip)`. `root.py`
implements it with `atoms.read_chain`; no `ChainView` crosses into `science.world`.

**Errors:** `CoverageUnknown`, `CoverageNotLive`, `CoverageUnresolvable`,
`CaptureDrift`, `EnumeratedKindUngoverned`, `RuleNotHeld`.

- [ ] **Step 1: Write failing root-boundary tests.** Assert `root.py` calls
  `read_chain` with the existing backend, target root, `metadata_root_for(root)`, and
  storage profile, then returns only genesis/tip. Extend the capability test to prove no
  world-package module imports `atoms`.

- [ ] **Step 2: Write failing preflight tests.** With an explicitly declared coverage,
  assert the world recovery/head callback runs under the world lock before registry or
  rule inspection. Exercise unadmitted, non-live, absent-carrier, duplicate-carrier, and
  unheld-binding refusals in the frozen order. Assert preflight pins a sorted
  `corpus_id -> carrier root` mapping and never substitutes all live ids.

- [ ] **Step 3: Write failing coherent-capture tests.** Assert sorted serial capture;
  chain head and both state computations occur inside the same corpus capture hold; every
  stored node is enumerated once and feeds all four rules; only immutable captured values
  leave the hold. Mutate raw corpus content during enumeration and assert `CaptureDrift`,
  complete discard, no retry, and no publication call.

- [ ] **Step 4: Write the ungoverned-kind boundary tests.** A stored
  `coreference-attestation` or `instrument-certification` record raises
  `EnumeratedKindUngoverned` before any derivation consumes it. A corpus with no records of
  either kind captures normally and produces empty corresponding enumerations. Do not add
  either kind to `stored.SEMANTIC_DOMAINS` in this slice.

- [ ] **Step 5: Implement preflight and capture as private epoch helpers.** Under the
  world lock: recover/read the world chain, scan/reduce registry, resolve unique covered
  carriers, and verify four exact bindings. Then release the world lock and, for each
  sorted id, enter `_root_state_for(...).lock.capture()`, call the injected chain callback,
  compute state, enumerate once into captured projections, and recompute state. Return a
  frozen build draft containing only captured values, anchors, coverage/states, build-start
  world head, and resolved exact rule bytes.

- [ ] **Step 6: Add the pre-publication binding recheck helper.** It reacquires the world
  lock, checks the same four exact bindings, and raises `RuleNotHeld` if removal won. It
  performs no corpus read and is called by publication in Task 9.

- [ ] **Step 7: Complete this task's cut-7 check nodes.** Before this task's commit, every
  Task-12 check node naming `test_world_build.py` exists and passes, including the ABA
  undetectability, rebuild-identity, map-edit-discard, and publication-recheck nodes.

- [ ] **Step 8: Run focused and full gates, then commit.**

```bash
git add python/src/science/world/epoch.py python/src/science/world/registry.py python/src/science/world/rules.py python/src/science/world/__init__.py python/src/science/root.py python/src/science/errors.py python/tests/test_world_build.py python/tests/test_capability_boundary.py
git commit -m "feat(world): capture coherent epoch inputs"
```

---

### Task 9: Publish, open, and select immutable epochs

**Files:**
- Modify: `python/src/science/world/epoch.py`
- Create: `python/src/science/world/read.py`
- Modify: `python/src/science/world/__init__.py`
- Modify: `python/src/science/root.py`
- Modify: `python/src/science/errors.py`
- Create: `python/tests/test_world_epoch.py`
- Modify: `python/tests/test_world_build.py`

**Interfaces:**

```python
def build_epoch(
    world: World,
    *,
    coverage: frozenset[str],
    bindings: DerivationBindings,
) -> Epoch: ...


def open_epoch(world: World, packaging_identity: str) -> Epoch: ...
def current_epoch(world: World) -> Epoch: ...
```

`DerivationBindings` names producer, retraction, certification, and coreference exact
bindings. `Epoch` is immutable and carries its packaging identity plus parsed members.
Errors: `EpochMalformed`, `EpochUnknown`.

- [ ] **Step 1: Write failing deterministic-carrier tests.** Pin the exact eleven member
  names, closed YAML bytes, sorted anchors `(subject, genesis_digest, head_digest)`, sorted
  coverage/state pairs, and packaging identity under `science.epoch.v1` over sorted
  `(member name, SHA-256 member content digest)` pairs. Assert the retraction and
  certification subjects appear only inside receipts.

- [ ] **Step 2: Write failing publication tests.** First publication submits one plan of
  eleven member `CreateOp`s plus a `CreateOp` for `epochs/current`; later publication uses
  member creates plus `ReplaceOp`. Remove a rule after capture but before publication and
  assert `RuleNotHeld` with no epoch plan. Assert corpora may move after capture without a
  freshness refusal.

- [ ] **Step 3: Write failing exact-rebuild tests.** An identical existing epoch requires
  only the pointer swap; a pointer already naming it is success. A same-name incomplete,
  malformed, extra-member, or byte-different carrier raises `EpochMalformed`; no member is
  overwritten.

- [ ] **Step 4: Implement deterministic encoding and one publication plan.** Keep carrier
  dataclasses and the private locked epoch loader in `epoch.py`; expose open/read wrappers
  from `read.py`. Derive all bytes before reacquiring the world lock, recheck bindings,
  inspect any same-name carrier, then submit exactly one plan. Use the existing executor's
  `CreateOp`/`ReplaceOp`; add no staging writer or sequence file.

- [ ] **Step 5: Write failing locked-open tests.** For `open_epoch`, assert the world lock
  is acquired before the recovery callback and held through every carrier read. For
  `current_epoch`, assert one lock acquisition, recovery before reading `current`, and use
  of the private locked loader without re-entry. Interleave publication/deletion setup and
  prove no reader observes a partial in-process transaction.

- [ ] **Step 6: Implement opening in two validation layers.** The carrier layer validates
  exact members, closed YAML, member digests, and packaging identity, translating failures
  to `EpochMalformed` with causes. It parses receipt carrier shapes permissively enough to
  hand structurally representable content to the semantic receipt validator; do not turn a
  receipt outcome `malformed` into carrier failure.

- [ ] **Step 7: Complete this task's cut-7 check nodes.** Before this task's commit, every
  Task-12 check node naming `test_world_epoch.py` exists and passes, including both X1
  nodes, retained named-epoch opening, and exact rebuild.

- [ ] **Step 8: Run focused and full gates, then commit.**

```bash
git add python/src/science/world/epoch.py python/src/science/world/read.py python/src/science/world/__init__.py python/src/science/root.py python/src/science/errors.py python/tests/test_world_epoch.py python/tests/test_world_build.py
git commit -m "feat(world): publish and open immutable epochs"
```

---

### Task 10: Validate receipts and expose bound address/coreference reads

**Files:**
- Modify: `python/src/science/world/derive.py`
- Modify: `python/src/science/world/read.py`
- Modify: `python/src/science/world/registry.py`
- Modify: `python/src/science/world/__init__.py`
- Modify: `python/src/science/errors.py`
- Create: `python/tests/test_world_receipts.py`
- Create: `python/tests/test_world_read.py`

**Interfaces:**

```python
def validate_receipt(world: World, epoch: Epoch, kind: ReceiptKind) -> ReceiptOutcome: ...
def resolve_address(world: World, epoch: Epoch, address: str) -> Resolved | NotPresent | Unknown: ...
def coreference_edge(world: World, epoch: Epoch, left: str, right: str) -> EdgeAnswer: ...
def expand_coreference(world: World, epoch: Epoch, endpoint: str) -> tuple[str, ...]: ...
```

Every result carries `BoundStamp(packaging_identity, coverage)`. `EdgeAnswer.state` is
`active | inactive | indeterminate`. Errors: `ResolutionRefused`, `EdgeIndeterminate`.

- [ ] **Step 1: Write failing receipt-outcome tests.** For all four receipt kinds, assert a
  rebuild with the named binding and exact currently available corpus states validates;
  an omitted source or wrong reduction refutes; an absent state or removed binding is
  unresolvable; and a structurally unsound receipt contract is malformed. Assert all four
  state maps are identical within one epoch and no evaluator consults an installed default.

- [ ] **Step 2: Write failing resolution-union tests.** Recorded live and deprecated
  addresses resolve to `(corpus_id, uid)` when the singular carrier produces the uid;
  absent carrier returns `NotPresent`; address outside observed coverage returns `Unknown`.
  Duplicate carriers, malformed present manifests, or a present carrier missing the mapped
  uid raise `ResolutionRefused`, never `NotPresent`.

- [ ] **Step 3: Write failing stamp/staleness tests.** Every resolution and edge answer
  names the explicit epoch packaging identity and complete coverage. Move corpus state
  after publication and assert the answer remains honestly bound to the old epoch without
  a recency claim. Prove no belief API accepts `current_epoch`; existing belief input stays
  an explicit producer-snapshot identity.

- [ ] **Step 4: Write failing edge-state and expansion tests.** Reduce active/inactive from
  balance only when the receipt validates and epoch coverage contains every registry-live
  id. Wider epoch coverage is accepted. For missing live ids and each of `refuted`,
  `unresolvable`, and `malformed`, inspection returns `indeterminate`; expansion raises
  `EdgeIndeterminate` carrying the sorted uncovered ids and/or exact receipt outcome.

- [ ] **Step 5: Implement receipt validation and reads.** Reuse the registry's locked scan
  and presence rules; resolve current states only after receipt well-formedness; run the
  exact held implementation; compare canonical subject projections byte-for-byte. Keep
  the public result unions as small frozen dataclasses, not a generic result framework.

- [ ] **Step 6: Complete this task's cut-7 check nodes.** Before this task's commit, every
  Task-12 check node naming `test_world_receipts.py` or `test_world_read.py` exists and
  passes, including well-formedness-before-availability, two-world agreement,
  per-corpus/per-rule quantification, and belief invariance.

- [ ] **Step 7: Run focused and full gates, then commit.**

```bash
git add python/src/science/world/derive.py python/src/science/world/read.py python/src/science/world/registry.py python/src/science/world/__init__.py python/src/science/errors.py python/tests/test_world_receipts.py python/tests/test_world_read.py
git commit -m "feat(world): expose bound epoch reads"
```

---

### Task 11: Add explicit whole-epoch garbage collection

**Files:**
- Modify: `python/src/science/world/epoch.py`
- Modify: `python/src/science/world/__init__.py`
- Modify: `python/src/science/errors.py`
- Create: `python/tests/test_world_gc.py`

**Interface:**

```python
def delete_epoch(world: World, packaging_identity: str, *, actor: str) -> EpochDeletionReport: ...
```

The report names the actor, producer-snapshot identity, four receipt identities, and
whether each identity is still carried by another retained epoch. Errors: `EpochUnknown`,
`EpochCurrent`.

- [ ] **Step 1: Write failing refusal-order tests.** Under the world lock, assert recovery
  runs before reading `current`; deleting current raises `EpochCurrent`; unknown identity
  raises `EpochUnknown`; malformed current/target/other retained carriers refuse through
  the established carrier rules. No delete plan is submitted on refusal.

- [ ] **Step 2: Write failing whole-epoch/report tests.** Assert one plan contains one
  `DeleteOp` for each of the eleven target members and nothing else. The report identifies
  snapshot and receipt identities uniquely carried by the target versus still carried by
  another epoch. Assert no individual-member or automatic deletion API exists.

- [ ] **Step 3: Implement deletion with the private locked loader.** Acquire the world
  lock once, run the injected recovery barrier, read/validate `current`, open the target
  and required other retained epochs without lock re-entry, compute the report, and submit
  one delete plan. Ignore empty directories. A repeated post-commit call is
  `EpochUnknown`; add no tombstone.

- [ ] **Step 4: Run focused and full gates, then commit.**

```bash
git add python/src/science/world/epoch.py python/src/science/world/__init__.py python/src/science/errors.py python/tests/test_world_gc.py
git commit -m "feat(world): delete complete epochs explicitly"
```

---

### Task 12: Declare all 48 cut-7 N2 units

**Files:**
- Create: `python/tests/n2_arms_cut7.py`
- Create: `python/tests/acceptance/test_n2_cut7.py`
- Modify only if the shared harness needs a cut-neutral capability already required by the
  frozen cut: `python/tests/test_n2.py`

**Inventory:** selected units by row: X1 2, X2 2, X3 2, X5 1, X7 2, X8 2,
X9 6, X10 4, X11 2, X12 5, W8a 10 = 38. Labeled units: lock capture
generation; rule install; rule removal; rule self-verification; build publication
recheck; publication exact rebuild; read resolution refusals; read edge-query span;
capture ungoverned kind; durable world transactions = 10.

**Exact check-node inventory:**

> **Annotation added at close-out — do not transcribe this table literally.** Every
> function named below exists verbatim in the landed tree, but **31 of the 45 pre-existing
> ones are methods on a class**, and `pytest file.py::method` exits 4 — which the N2
> harness scores `uncollected`, not `sound`. Declared as spelled here, 31 arms would look
> like declarations and assert nothing. Cut 1 already spells node ids with the class
> segment between the file and the function, and the landed `python/tests/n2_arms_cut7.py`
> does too: `test_world_epoch.py::TestOpening::test_open_epoch_refuses_raw_member_edit`,
> not `test_world_epoch.py::test_open_epoch_refuses_raw_member_edit`. The file and function
> names are the frozen ones; only the resolvable class segment is added. No unit is
> renumbered or re-homed — reducing the landed declarations back to `file::function`
> reproduces this table set-identically.

| row/unit | check node |
|---|---|
| X1 no member mutation API | `test_world_epoch.py::test_public_surface_has_no_individual_epoch_member_mutation` |
| X1 raw member edit | `test_world_epoch.py::test_open_epoch_refuses_raw_member_edit` |
| X2 observable interruption | `acceptance/test_n2_cut7.py::test_recovery_barrier_never_selects_partial_epoch` |
| X2 publication evidence | `acceptance/test_n2_cut7.py::test_publication_registration_names_epoch_and_current` |
| X3 explicit belief input | `test_world_read.py::test_belief_has_no_current_epoch_input` |
| X3 retained named epochs | `test_world_epoch.py::test_retained_epochs_open_by_packaging_identity` |
| X5 duplicate carrier at build | `test_world_build.py::test_build_refuses_duplicate_carrier_coverage` |
| X7 unadmitted refusal | `test_world_build.py::test_build_refuses_unadmitted_manifest_carrier` |
| X7 admission permits build | `test_world_build.py::test_admission_allows_same_build_preflight` |
| X8 complete stamps | `test_world_read.py::test_every_epoch_answer_carries_complete_bound_stamp` |
| X8 no stampless constructor | `test_world_read.py::test_bound_answer_types_have_no_stampless_constructor` |
| X9 writer during capture | `test_world_build.py::test_api_write_refuses_during_capture` |
| X9 build behind writer | `test_world_build.py::test_capture_refuses_active_writer_without_waiting` |
| X9 raw drift | `test_world_build.py::test_capture_drift_discards_without_publication` |
| X9 identical receipt states | `test_world_build.py::test_four_receipts_share_identical_corpus_states` |
| X9 head/state coherence | `test_world_build.py::test_chain_head_and_state_are_captured_in_one_hold` |
| X9 ABA limit | `test_world_build.py::test_raw_aba_during_capture_is_undetectable` |
| X10 removed bindings | `test_world_receipts.py::test_removed_binding_makes_every_receipt_kind_unresolvable` |
| X10 successor beside named pair | `test_world_receipts.py::test_receipt_uses_named_binding_beside_successor` |
| X10 malformed bare version | `test_world_receipts.py::test_bare_version_receipt_is_malformed_without_availability` |
| X10 coreference consequence | `test_world_read.py::test_coreference_nonvalidated_outcomes_are_indeterminate` |
| X11 current refusal | `test_world_gc.py::test_delete_current_epoch_refuses` |
| X11 sever report | `test_world_gc.py::test_delete_noncurrent_epoch_reports_severed_identities` |
| X12 bounded retraction map | `test_world_derive.py::test_retraction_map_is_bounded_by_coverage` |
| X12 retraction omission | `test_world_receipts.py::test_retraction_omission_refutes_repackaged_epoch` |
| X12 moved named state | `test_world_receipts.py::test_moved_corpus_state_makes_receipt_unresolvable` |
| X12 empty coreference reduction | `test_world_receipts.py::test_nonzero_coreference_balance_refutes_empty_coverage` |
| X12 refuted coreference consequence | `test_world_read.py::test_refuted_coreference_is_nonbelief_indeterminate` |
| W8a rebuild identity | `test_world_build.py::test_delete_and_rebuild_reconstructs_all_four_maps` |
| W8a map edits discarded | `test_world_build.py::test_rebuild_discards_all_map_only_edits` |
| W8a producer coverage | `test_world_derive.py::test_narrower_producer_coverage_moves_snapshot_and_belief` |
| W8a receipt beside identity | `test_world_receipts.py::test_receipt_changes_when_location_states_move_but_snapshot_does_not` |
| W8a rule succession | `test_world_receipts.py::test_rule_successor_mints_receipt_and_snapshot_only_on_subject_change` |
| W8a well-formedness first | `test_world_receipts.py::test_receipt_well_formedness_precedes_availability` |
| W8a conformance/agreement | `test_world_receipts.py::test_rule_conformance_and_two_worlds_agree_within_availability` |
| W8a per-conjunct quantifier | `test_world_receipts.py::test_receipt_resolution_quantifies_each_corpus_and_rule` |
| W8a belief invariance | `test_world_read.py::test_belief_is_invariant_to_availability_and_requires_snapshot` |
| W8a absent is not empty | `test_world_read.py::test_inside_coverage_absence_is_not_outside_coverage_unknown` |
| labeled lock generation | `test_operation_lock.py::test_writer_waiting_across_capture_generation_refuses` |
| labeled rule install | `test_world_rules.py::test_rule_install_is_idempotent_and_refuses_collision_or_nonconformance` |
| labeled rule removal | `test_world_rules.py::test_rule_removal_is_exact_and_reports_severed_receipts` |
| labeled rule self-verification | `test_world_rules.py::test_held_rule_recomputes_stored_symbol_and_fixtures` |
| labeled publication recheck | `test_world_build.py::test_removed_rule_before_publication_refuses` |
| labeled exact rebuild | `test_world_epoch.py::test_exact_epoch_rebuild_swaps_only_current` |
| labeled resolution refusals | `test_world_read.py::test_resolution_refuses_every_carrier_ambiguity` |
| labeled edge span | `test_world_read.py::test_edge_indeterminate_names_missing_span_and_receipt_outcome` |
| labeled ungoverned kind | `test_world_build.py::test_build_refuses_ungoverned_enumerated_record` |
| labeled durable world acts | `acceptance/test_n2_cut7.py::test_world_transactions_register_every_path` |

- [ ] **Step 1: Write the failing declaration-accounting test.** Parse the frozen cut's
  explicit unit ids into `CUT7_ARMS`; assert 7 full + 4 part row states, 38 selected,
  10 labeled, and 48 total. Assert every arm has one source mutation and one exact check
  node, and no cut-5/cut-6 declaration is re-homed or edited.

- [ ] **Step 2: Declare X1/X2/X3/X5/X7/X8.** Pin carrier tamper/open refusal, observable
  transaction stages only, explicit snapshot input/belief boundary, build-time carrier
  uniqueness, bound stale reads, and current-pointer operational-only behavior exactly as
  frozen. X2 must state that intra-transaction stages belong to engine-certified recovery
  and are not Science-observable.

- [ ] **Step 3: Declare all six X9 arms with a nonvacuous relocation sabotage.** The
  relocated-head mutation must move the sole head-capture call outside the capture hold
  **and interpose a real corpus write between state capture and relocated head capture**.
  Add a declaration-time test that removes the interposed write and demonstrates the
  check would pass vacuously, then restores it and observes the mismatch/refusal. Also pin
  writer-during-capture, writer-held contention, raw drift, identical four-receipt states,
  and empty-enumeration coherent publication.

- [ ] **Step 4: Declare X10/X11/X12.** Cover all four receipt outcomes and coreference
  indeterminacy consequences, identity-class separation, retraction/certification/coref
  completeness selections, and the frozen deferred coreference omission arm without
  promoting it. A malformed receipt must remain an outcome, not carrier refusal.

- [ ] **Step 5: Declare all ten W8a selected units.** The rebuild fixture must have
  populated address, producers, and retraction maps; only coreference is kind-empty. The
  agreement arm must construct **two distinct world roots**, each resolving the same
  binding from its own rules store over the same corpora, rather than evaluate twice in
  one root. Preserve the outside-coverage `Unknown` contrast and §11.15 limitation.

- [ ] **Step 6: Declare the ten labeled units.** Use exact implementation sites and tests
  already created in Tasks 4–11. The ungoverned-kind arm names both deferred prose kinds
  but asserts a refusal only when such a record exists. The durable-world arm points to
  committed registration-entry evidence, not portable write-plan shape alone.

- [ ] **Step 7: Run declaration validation.** Run the cut-7 N2 test, the standing harness,
  and all prior N2 tests. Grep the frozen cut's `Selected` and `Labeled` bullets and account
  for every one exactly once in the declaration file. Run Ruff and Pyright on the new
  files.

- [ ] **Step 8: Commit declarations separately.**

```bash
git add python/tests/n2_arms_cut7.py python/tests/acceptance/test_n2_cut7.py python/tests/test_n2.py
git commit -m "test(n2): declare conformance cut 7"
```

Omit the shared harness if unchanged.

---

### Task 13: Add cut-7 portable acceptance and certified runner

**Files:**
- Modify: `python/tests/acceptance/test_n2_cut7.py`
- Create: `python/tools/cut7_acceptance.py`
- Modify: `python/pyproject.toml` only if the new runner needs an installed script entry

**Runner:** invokes cut-5 and cut-6 runners/tests as an unchanged prefix, then cut-7 N2,
portable acceptance, and certified durable arms. It refuses off the certified tuple.

- [ ] **Step 1: Write portable end-to-end acceptance.** In temporary world/corpus roots,
  explicitly install shipped rules, admit coverage, publish an epoch, open it by identity
  and through current, validate all four receipts, exercise `Resolved`/`NotPresent`/
  `Unknown`, exercise active/inactive/indeterminate edge behavior available in this slice,
  remove a binding with a sever report, and delete a non-current epoch with a sever report.
  Make no crash-durability assertion here.

- [ ] **Step 2: Write certified durable arms.** On the certified tuple, prove committed
  registration-entry evidence for rule installation/removal, epoch publication with the
  anchored tuple, pointer replacement, and whole-epoch deletion. Reuse `atoms` recovery
  and the existing cut harness; do not certify `read_chain` again in Science or add a
  replay reader.

- [ ] **Step 3: Implement the runner.** Follow the cut-6 runner's CLI/error style. Execute
  cut 5 and cut 6 unchanged as prefix, then the cut-7 declaration, portable acceptance,
  and durable tests. An uncertified storage tuple is an error with a clear diagnostic,
  never a skip or portable substitute.

- [ ] **Step 4: Run portable gates.** From `science/python`:

```bash
uv run --frozen pytest tests/acceptance/test_n2_cut7.py -q
uv run --frozen pytest -q
uv run --frozen ruff check .
uv run --frozen pyright
```

- [ ] **Step 5: Run certified acceptance.** On the certified host/tuple:

```bash
uv run --frozen python tools/cut7_acceptance.py
```

Capture the exact command, tuple, counts, and terminal result for Task 14. Do not claim
cut discharge from portable green alone.

- [ ] **Step 6: Commit the acceptance surface.**

```bash
git add python/tests/acceptance/test_n2_cut7.py python/tools/cut7_acceptance.py python/pyproject.toml
git commit -m "test(acceptance): certify world epoch publication"
```

Omit `python/pyproject.toml` if unchanged.

---

### Task 14: Record cut-7 results and close the ledger claims

**Files:**
- Create: `docs/plans/2026-08-20-conformance-cut-7-results.md`
- Modify: `docs/superpowers/plans/2026-08-20-world-index-slice-2.md`
- Modify: `docs/designs/2026-08-20-world-index-slice-2-design.md`
- Modify: `docs/designs/2026-08-03-redesign-adoption-ledger.md`
- Modify user-facing README/guide files only where landing makes an existing claim stale

- [ ] **Step 1: Re-derive acceptance accounting.** From the frozen cut and declaration
  module, independently recount 7 full + 4 part rows and 38 selected + 10 labeled = 48
  units. Record each portable and certified command, the certified tuple, pass counts,
  and commit identities. Never infer durability from the portable suite.

- [ ] **Step 2: Write the results record.** Record that artifact 1 is complete; row 2's
  build-time uniqueness half is closed while the fork constructor remains deferred; row 4
  now has the public chain reader; row 5 has an anchor carrier while log verification,
  explicit anchor act, and replay remain deferred. Preserve the dated genesis/mirror,
  Plan-B fork, cross-process locking, GC tombstone, sequence-number, epoch-sweep, and
  pinned-authority limitations.

- [ ] **Step 3: Correct status at the landing boundary.** Change this plan and the slice-2
  design from planned/approved to implemented only after the implementation commits are
  ancestors of the integration commit and certified acceptance passed. Grep the README,
  guides, ledger, slice-1 design, and cut-6 text for propagated stale claims; amend only
  claims made stale by this implementation.

- [ ] **Step 4: Run documentation and full gates.** Run the docs/status tests, full
  portable Science gates, and `git diff --check`. Verify the cut-5 and cut-6 files are
  byte-identical to their pre-slice-2 versions.

- [ ] **Step 5: Commit close-out separately.**

```bash
git add docs/plans/2026-08-20-conformance-cut-7-results.md docs/superpowers/plans/2026-08-20-world-index-slice-2.md docs/designs/2026-08-20-world-index-slice-2-design.md docs/designs/2026-08-03-redesign-adoption-ledger.md
git commit -m "docs(world): record cut 7 discharge"
```

Add only genuinely changed README/guide paths to that explicit list.

---

## Final Verification and Handoff

- [ ] Confirm the `atoms` implementation commit is landed and Science resolves that exact
  source/dependency revision.
- [ ] Confirm the pure package-promotion commit is independently green and contains no
  slice-2 semantic change.
- [ ] Run the complete Science portable suite, Ruff, and Pyright from a clean worktree.
- [ ] Run `python/tools/cut7_acceptance.py` on the certified tuple and retain its exact
  output in the results record.
- [ ] Recount the frozen cut: 7 full + 4 part, 38 selected + 10 labeled, 48 total.
- [ ] Verify X9's relocated-head arm contains a real interposed corpus write and its
  declaration-time nonvacuousness check.
- [ ] Verify W8a's agreement arm uses two distinct world roots and two independently
  resolving stores.
- [ ] Verify `coreference-attestation` and `instrument-certification` remain deferred
  stored kinds and production capture refuses records claiming either.
- [ ] Verify no `atoms` import escaped `science.root`, no `world.py` compatibility file
  exists, and cut-5/cut-6 runners/declarations are unchanged.
- [ ] Request final code review against the approved slice-2 design, frozen cut 7, and this
  plan; close findings and rerun affected gates before integration.
