# Composition-root adapter design — the corpus-write adapter

**Date:** 2026-08-18
**Status:** Banked 2026-08-18 — the `nodes` seam amendment landed as
`abbf52b`, cut 4's §7 second reader discharged, and the banking commit froze
conformance cut 4 in the same change. **Implemented 2026-08-18** (`science`,
branch `feat/composition-root-adapter`): `science.root`, `science.corpus`,
`science.traversal` and `science.stored`, with cut 4's frozen selection
discharged against the certified engine on a certified volume — results in
`docs/plans/2026-08-18-conformance-cut-4-results.md`. **Review of 2026-08-18
closed both implementation deviations as amendments** — the `consumer_tag`
grammar (§3 step 6) and the derived parent-directory effects (§3 step 3), each
an engine constraint the original text did not survive; recorded the
stored-document mapping as normative surface (§5a); and added one
strengthening the review found (§5a: an unstamped governed kind is refused,
`semantic-hash-missing`), outside cut 4's frozen selection and counted in no
cut's accounting.
**Sources:** the `nodes` write-plan/executor seam design
(`~/d/nodes/docs/designs/2026-08-17-nodes-write-plan-executor-seam-design.md`,
frozen 2026-08-17, pre-normative); the `atoms` authority design §11–§12.2/§14
(`~/d/atoms/docs/plans/2026-07-23-recoverable-fs-effect-engine-design.md`), with
A8's physical certification (adoption ledger row 4); conformance cut 4
(`2026-08-17-conformance-cut-4.md`); the substrate consolidation design
§4.2.1/§4.3/§6.2/§7; the world-addressing design's write-boundary rule (its
§4.2 narrowing); the tamper-evident log design §2.1.

## 1. Scope

This is Plan B item 1: Science's composition root adopts the certified `atoms`
engine, and generic corpus writes flow through it. The design covers five
things and no more:

1. the **composition root** (`science.root`) — the only module that imports
   `atoms`: volume binding, the explicit root-registration act, the durable
   executor, and the root-taking executor factory;
2. the **durable executor** — the seam's `WritePlanExecutor`, compiling one
   `WritePlan` into one `TransactionSpec`;
3. the **write API** (`science.corpus`) — the sole holder of a mutable
   `Corpus`, exposing the add path with its write-boundary refusals;
4. the **read side** — a concrete read-only facade and the stored-corpus
   traversal adapters;
5. the **acceptance suite** discharging cut 4's frozen selection.

Python only: the engine is Python-only, and `nodes`' Python/TypeScript parity
is untouched — exactly the constraint authority §12.2 records. The design does
**not** cover the family adapters (supersede, archive, import/cohort — Plan B
item 2), anchor carriage and the L rows (the next persistence cut), the managed
holdings root, the world index, or any interim transaction layer (substrate §7
forbids one; no consumer adoption may redefine the engine protocol).

**Module topology is normative here, not cosmetic**, because S8's static check
quantifies over it. Two modules, layered: `science.root` closes over the engine
handles and constructs the write API; `science.corpus` constructs the mutable
`Corpus` and never sees an `atoms` type. The seam's own wiring sentence — a
composition root closes over its engine handles but lets the corpus supply the
root — is this shape.

## 2. Root layout and the init act

**Keying.** One corpus root = one engine project root, per authority §12.2: the
lock, chain, and metadata are keyed on the corpus, never on a "project" that
merely contributes to one. The registration chain lives where the engine puts
it (`<root>/.#~chain/`), covered by `nodes`' reserved-path contract — non-`*.md`
content is contractually untouched by `nodes`.

**Metadata root.** Caller-supplied per the engine, derived by one fixed rule:
the sibling `<corpus-root>.metadata/` (so `corpora/mm30` → `corpora/mm30.metadata`).
The rule normally places it on the corpus's volume, and the engine **proves**
same-volume placement and refuses otherwise — the guarantee is the engine's
probe, not the naming rule. The sibling sits outside the corpus root, keeping
the ledger's two cold-arrival cases legible: a corpus copied without its
sibling is a normal cold bootstrap; one copied with it is the restored-backup
classification case. The engine's sync exclusion is a best-effort ignore-marker
request — a synced metadata copy is untrusted, not impossible, and a failure to
set the marker weakens no single-host guarantee.

**The init act.** A corpus becomes durable only through the explicit
composition-root operation:

```python
def init_corpus_root(corpus_root: Path) -> None
```

It creates the corpus directory if absent, refuses a non-directory, and calls
the engine's `register_root` with:

- `genesis_payload` — the canonical bytes (`science.identity.v1` encoding) of
  the constant `{"domain": "science.corpus-root.v1"}`. The payload deliberately
  carries **no corpus identity**: corpus manifests and `corpus_id` minting are
  ledger artifact 2, unbuilt. When identity arrives it binds through a later
  chain entry, never by rewriting genesis.
- `registered_surface = ()` — no manifest exists to baseline, and the
  corpus-write adapter reserves nothing.

`register_root` is idempotent on a matching payload and surface and refuses a
mismatch, so the act is re-runnable and the payload permanent. Every write
against an unregistered root refuses — the engine's registered-root check,
surfaced through §4's mapping. Lazy registration on first write is rejected:
the genesis act is attributable and its timing is a recorded decision, not an
accident of whichever write came first.

**Volume binding.** The composition root passes the engine's production
storage profile through unchanged. Science holds no tuple data, no allowlist,
no override: admitting a new tuple is an `atoms` certification amendment, and
cut 4's "every other tuple fails closed" obligation is exercised as the
engine's refusal — relied on, never re-implemented.

## 3. The durable executor

The factory `science.root` supplies to the write API is
`(root: Path) -> DurableExecutor`, closing over the backend and storage
profile and deriving the metadata root by §2's rule. The corpus supplies the
root; the root is never pre-bound where the corpus cannot verify it.
`execute(plan)` builds exactly one `TransactionSpec` per plan and submits it
via the engine's `run_transaction`; all-or-nothing is the engine's property,
never re-implemented.

**The build follows path timelines, not independent operations.** A path may
occur more than once in one plan, and the engine validates a continuous
timeline per path (`build_timelines`: each occurrence's pre-state must equal
the previous occurrence's post-state). So the build:

1. **Plan validation** — an unknown operation kind, a lexically escaping path
   (absolute, or `..` after lexical normalization), or a reserved-namespace
   path (`.nodes-index/`, the engine's own leaves) raises `PlanRefusedError`
   before any read. These are the lexically decidable malformedness checks;
   authoritative resolution is the engine's (§4).
2. **Pre-state reads, first occurrence only** — for each path, the first
   replace/delete occurrence reads the file once: bytes hashed, mode and
   byte length from `stat`. Every later occurrence of the same path derives
   its pre-state from the previous occurrence's post-state. Each op's
   `expected_digest` is cross-checked against the state that op will actually
   see — the disk read for a first occurrence, the derived state after — with
   the `sha256:` prefix added when building `FileState`s and stripped when
   comparing. Alongside the digest, **every operation's implicit existence
   precondition is checked against the state it will actually see**: a later
   create on a path whose derived state is present, or a later replace or
   delete on a path whose derived state is `ABSENT`, is unsatisfiable by
   construction. Any mismatch, absence, or unsatisfiable precondition refuses
   before any effect (`ExecutionError`, that op's index, `applied=0`) — a
   create's pre-state is always `ABSENT` and cannot be derived, so without
   this check a create-after-present plan would fall through to the engine's
   timeline validation and surface mislabeled as an adapter bug.
   First-occurrence creates read nothing; `CreateFileNoClobber` enforces
   absence engine-side.
3. **Effects** — the seam §6 mapping: `CreateOp → CreateFileNoClobber`,
   `ReplaceOp → ReplaceFile`, `DeleteOp → DeletePath`, with deterministic
   position-derived effect ids (`op-<index>`). Created and replacement
   **post**-states carry the adapter's constant file mode `0o644`; every
   **pre**-state carries its observed mode and byte length. `MoveNoClobber`
   stays deliberately unused — rename is never a pure move.
   *(Amended 2026-08-18, implementation review.)* The engine refuses a create
   whose parent directory neither exists nor is created by the same
   transaction, so the adapter additionally **derives `CreateDirectory`
   effects** for each missing parent a created file needs, ordered before the
   file and carrying the second adapter constant, directory mode `0o755`
   (`dir-<index>-<depth>` effect ids); the surfaces gain the corresponding
   directory states. The alternative — an out-of-transaction `mkdir` — would
   put a corpus mutation outside both all-or-nothing and the chain's
   transaction record, and pre-creating kind directories at init fails
   because the kind set is open. The intent digest is unaffected: it is
   taken over the op list, not the effects, and stays derivable from the
   plan alone. Cut 4 §2's frozen *"reserves nothing and adds no effect of
   its own"* is **not** contradicted: that sentence sits in the registration
   paragraph and claims the adapter adds no registration machinery and
   reserves no paths, both still true — the wrong text was this step's
   verbatim three-effect mapping, which is what this amendment corrects.
4. **Surfaces** — `initial_surface` from each touched path's first pre-state,
   `final_surface` from its last post-state (`ABSENT` ↔ `FileState`).
5. **Intent** — derivable from the plan alone. The projection is the ordered
   list of discriminated op shapes, omitting inapplicable fields (the
   identity encoding refuses `null`):
   `{"op": "create", "path": …, "content_sha256": …}`,
   `{"op": "replace", "path": …, "expected_digest": …, "content_sha256": …}`,
   `{"op": "delete", "path": …, "expected_digest": …}`. Then
   `intent_digest = "sha256:" + digest("science.corpus-write-intent.v1", projection)`
   — the prefix is mandatory for the spec's format check.
6. **Assembly** — the adapter calls the engine's `build_spec` and never
   constructs a `TransactionSpec` directly: `build_spec` supplies
   `schema_version` from the engine's `SCHEMA_VERSION` constant and imposes
   canonical ordering, so the adapter cannot ship a stale version literal.
   Its constants: `consumer_tag = "science-corpus-write-v1"` *(amended
   2026-08-18, implementation review: the engine's identifier grammar is
   `[A-Za-z0-9_-]{1,64}` because the tag becomes a scratch-leaf path
   component, so the originally specified dotted `science.corpus-write.v1`
   was never submittable; the intent **domain** in step 5 stays dotted —
   Science identity domains and engine identifiers are different namespaces
   with different grammars)*, `dependencies=()`, `fulfills=None`,
   `registered_paths=()` — the adapter reserves nothing and adds no
   registration effect. The engine's automatic
   registration-chain append happens inside every transaction regardless;
   per cut 4, every transaction this slice commits is **chained but
   unanchored**.
7. **Payloads** — an in-memory `PayloadSource` over the plan's own content
   bytes, keyed by digest.

The complete `TransactionOutcome` (txid, outcome, registration digest,
settlement) is **discarded**: the seam returns `None`, nothing in this slice
consumes it, and anchor carriage — the next persistence cut — reads
registration digests from the chain itself, not from executor state. An empty
plan applies vacuously: no transaction, no chain entry, matching what
`DefaultExecutor` does with nothing to apply.

## 4. The failure and refusal surface

The seam permits exactly two public error names. This design requires one
narrow seam amendment before it banks — legal under the seam's own rule, since
no landed consumer exercises these parts; `nodes`-side review records it in the
seam's §8 log:

1. **Error shape** — `ExecutionError(index: int | None, applied: int | None)`.
   `index=None` means the failure is not attributable to an operation;
   `applied=None` means **restoration is unproved** — the adapter cannot prove
   the corpus is at its pre-plan state. `applied=None` is used for any such
   failure, not merely a caught halt.
2. **§4 halt carve-out** — the seam's "refusal or a crash leaves both disk and
   in-memory state at their pre-plan state" gains the halt case: on
   `TransactionHalted`, memory is pre-plan (`execute` never returned) but disk
   is **halted/unattributable, evidence preserved**. A halt does not resolve
   on the next lease by itself: it persists until the frozen diagnostic's
   operator action is performed, after which a later lease resumes recovery —
   or re-raises the halt.
3. **§3 malformed-plan clause** — narrowed to lexically decidable
   malformedness for `PlanRefusedError`; a durable executor surfaces
   resolution-time refusals as `ExecutionError(index=None, applied=0)`.
   `ProjectApprovalRefused` is deliberately **not** mapped to
   `PlanRefusedError`: it covers casefold roots, root-identity collisions,
   path and name limits, mount crossings, missing ancestors, lookup aliases,
   scratch collisions, and recovery-evidence mismatch — root and deployment
   failures, not only resolved escape. Preserving the original clause would
   require a new structured engine refusal reason; classifying by exception
   type or message would misclassify deployment failures as plan
   malformedness.

The complete mapping:

| failure | raised | fields |
|---|---|---|
| lexical/reserved/op-kind malformedness | `PlanRefusedError` | before any read |
| pre-state mismatch, absence, or unsatisfiable precondition at build | `ExecutionError` | that op's `index`, `applied=0` |
| `ProjectApprovalRefused` (rooted proof; before any mutation) | `ExecutionError` | `index=None`, `applied=0` |
| `SpecValidationError` (adapter-built spec fails compile, before project context — an adapter bug) | `ExecutionError` | `index=None`, `applied=0` |
| `PreconditionRefused` (clean refusal — restoration proven by the engine's own contract), `CapabilityUnavailable` (at preparation, before mutation) | `ExecutionError` | `index=None`, `applied=0` |
| `MetadataStoreInvalid`, `ChainStateInvalid` — stop-and-preserve, bypassing rollback | `ExecutionError` | `index=None`, `applied=None` |
| `TransactionHalted`, `ProtocolError`, any unrecognized engine failure — restoration unproved | `ExecutionError` | `index=None`, `applied=None` |

`applied=0` is licensed only where the engine's own contract proves
pre-mutation state: `ProjectApprovalRefused` and `CapabilityUnavailable` are
raised before any project mutation, `SpecValidationError` before any project
context, and `PreconditionRefused` refuses cleanly — once mutation may have
begun it returns only after proven restoration, unprovable restoration
becoming a halt. Everything else is `applied=None` unless the adapter
independently knows the failure preceded mutation (a store error raised
before `run_transaction` was entered). The default for the unrecognized is
conservative, never optimistic.

The engine exception is always chained as `__cause__`. Cause inspection is
diagnostic, never a public discrimination API: callers branch on the seam's
two names and the two optional fields, nothing else. Crash attribution is the
seam's §4 as amended: disk and memory both pre-plan, or the plan fully applied
and committed (recovered under the engine's next lease), or halted as above;
the corpus updates in-memory state only after `execute` returns. Recovery is
engine-owned and runs inside the lease `run_transaction` acquires — the
adapter never invokes or reimplements it.

## 5. The write API's add path

`science.corpus` is the sole constructor and holder of a mutable `Corpus`,
built by the root with the corpus root path and the executor factory. Its
public surface in this slice is **add alone**:

```python
def add(self, node: Node) -> Node      # returns the minted node, as nodes mints it
```

The input is a constructed `nodes` document (Science's record constructors
from cuts 1–3 produce its content); payloads are serialized document bytes
from the kernel's serializer — the executor stays pure file mechanics.

**Every corpus-domain refusal this package raises is a `ScienceError`;
execution-layer failures cross the boundary as the seam's two names.** The
split is deliberate: what the write API decides (basis, eligibility,
collisions, the add-only guard) refuses in Science's vocabulary, and what the
executor layer decides (plan validity, engine refusal, halt) surfaces as
`PlanRefusedError`/`ExecutionError` per §4 — a third vocabulary wrapping the
seam's two names would add a layer with no added discrimination. The add
path's refusal types, in refusal order, all subclasses of a new
`WriteRefused(ScienceError)`:

1. `RecordAlreadyMinted` — the add-only guard: an existing `(uid, id)` pair
   refuses **before plan construction**, so no plan this slice's public
   surface emits can contain a `ReplaceOp` or `DeleteOp`. The seam's
   replace-selecting `add` stays unexercised rather than accidentally
   exposed; the edit surface is Plan B item 2's.
2. `BasisMissing` — W3 as narrowed: a `source` with no accepted external
   identifier (no DOI, PMID, ISBN or accession) or a `dataset` with no
   content identity refuses, never coerces to a `note`. The curation note is
   its own explicit add; supplying the basis later is a second, separate mint
   — two mints, never an edit. No title-and-year fallback exists to reach.
   The add path performs **no holding check**: `declared`/`held` is derived
   on read and never stored (the W3/G9 negative).
3. `EligibilityUnmet` — S7's write boundary: an inadmissible `assesses` edge
   (its run lacking an `observes` input) refuses. The cross-node predicate
   reads through the same corpus's read view (§6).
4. `ValidationRefused` — `nodes`' registry/document validation failures,
   wrapped with the `nodes` exception as `__cause__`. (The kind-existence
   check G5 grounds on the registry **compile** stays unbuilt with it; this
   is `nodes`' existing per-document validation, not that check.)
5. `CollisionRefused` — `assert_addable`'s corpus-side refusals (a uid held
   by another id, an identity claim held by another uid), wrapped. Per the
   seam, these never reach an executor; per Science's error contract,
   `nodes.CollisionError` never escapes raw.

A write against an unregistered root surfaces as §4's
`ExecutionError(index=None, applied=0)` with the engine's registration
refusal as cause — init is an explicit act, not a fallback the add performs.

**Why pre-plan reads are safe in this slice, recorded — two arguments, not
one.** The refusals above read corpus state before the engine lease exists.
The **monotone** predicates are safe under concurrent adds: another admitted
add cannot invalidate an already-satisfied W3 or S7 predicate (nothing
removes a basis or an `observes` edge). The **collision** predicates are
not: two planners can each pass `assert_addable` for the same uid under
different ids, plan creates at two different paths, and both no-clobber
effects succeed — a duplicate uid on disk that no engine precondition can
express, and identity-claim collisions race identically. `CreateFileNoClobber`
backstops only the same-path (same-id) race. The ruling is therefore a
**single-planner restriction**: the write API serializes each add end-to-end
— read, refuse, plan, execute — under a per-corpus-root operation lock, which
the composition root enforces in-process by construction (one mutable
`Corpus`, one holder). Cross-process, single-planner-per-root is a **stated
deployment obligation**, and its violation is detected loudly rather than
prevented: strict construction refuses the duplicate uid with
`CollisionError` — the same loud-refusal posture the seam chose for rename's
duplicate-uid window. Deletion-capable family adapters **must re-own this
concurrency question**; neither argument transfers.

## 5a. The stored-document mapping *(added 2026-08-18, implementation review)*

The design as banked said the record constructors from cuts 1–3 produce a
document's content and left unstated how a Science value sits in a `nodes`
document. That gap is normative surface — two readers disagreeing about which
facet carries a run's spec is a corpus with two meanings — and `science.stored`
is its one home. The review records its contract here:

- **Facet keys are unnamespaced**: they belong to the `science` base profile,
  not a domain contract (domain-extension boundary §3.4), with
  `empirical-observation` the facet the eligibility predicate turns on.
- **Relation predicates are kernel §4.1's closed signatures**, and role-typed
  inputs are stored as relations, not facet payload. Where a ref is
  deliberately carried twice — an assessment's edges beside its facet's
  digest fields — the builders write both from one argument, so nothing the
  boundary mints can disagree with itself; a raw write that makes them
  disagree is an untrusted import under the stated bound.
- **Semantic-hash coverage is code, not stored data** (`COVERED_FACETS`,
  per-kind): a stored coverage list is data an untrusted writer could
  shorten, which is a hash certifying whatever it was pointed at. The
  projection records which covered facets are present, so adding a governed
  facet without restamping is a disagreement, not a silent extension. Prose
  (`title`, body, `display_statement`) is outside every entry, hand-editable
  by rule.
- **A governed kind must carry a stamp; a prose kind never has to** — the
  review's one strengthening. `SEMANTIC_DOMAINS` partitions the corpus; the
  boundary mints every governed record stamped, so an unstamped stored
  record of a governed kind is statically detectable and is refused on the
  facade's read path (`SemanticHashMissing`) and reported by the corpus
  check (`semantic-hash-missing`). This narrows nothing in the
  recorded-history bound — fields and stamp moved together stay undetectable
  — and breaks no frozen negative: S3's negative and R22(c) both construct
  *stamped* self-consistent forgeries. It is outside cut 4's frozen
  selection, declared as a labeled post-freeze arm in the N2 table and
  counted in no cut's accounting.

## 6. The read side and S8's capability boundary

**A concrete facade, not a protocol.** `Corpus` structurally satisfies any
read-only `Protocol` despite carrying mutation methods, so a protocol is not a
capability boundary. `science.corpus` exposes a concrete `ReadView` holding
its `Corpus` privately and exposing exactly the read surface: `get`, one-hop
`outbound`/`inbound`, and member iteration for the corpus check. Every module
outside `science.corpus` receives a `ReadView`; no mutable `Corpus` is
constructed or received anywhere else. That is S8's claim, checkable by AST,
and the suite's static arm asserts exactly it. The `atoms`-import confinement
(`science.root` only) is enforced beside it as architecture, **not** as an S8
arm — S8's row is about the mutable corpus handle.

**Stale-hash validation lives on the facade's node-read path.** Every fetch —
`get` and every node a traversal resolves — recomputes the semantic hash from
the stored fields and refuses a disagreement (`semantic-hash-stale`), which is
S3's read-side check, and refuses an unstamped governed kind
(`semantic-hash-missing`, §5a's strengthening). This design supplies the behavior, but cut 4 does not
select S3: its exact banked mutation is an edit followed by explicit import,
and that family surface remains deferred. The §6.2 profile-level corpus check
(`eligibility-unmet`, over the store) reads through the same facade's
iteration. Because a live `Corpus` indexes at construction and a raw
filesystem write is invisible to it, **every raw-write fixture reconstructs a
fresh facade** before asserting read behavior — reconstruction from disk is
the recovery posture the seam names, and the read this cut actually runs.

**Traversal.** The stored-corpus relation and lineage adjacency adapters
implement the same adapter protocols cuts 1–3's one algorithm consumes, now
reading through the `ReadView`. Corpus-local throughout; a walk truncates at
the corpus edge, which is the world layer's documented property and not this
design's to change. S1a's facet-walked lineage, S5's snapshot-producing walk,
and R23's `derived_from`-as-view all run over this surface.

## 7. The acceptance suite

The suite discharges cut 4's frozen selection — S7, S8, W3 in full; the
selected arms of S1, S1a, S5, R19(a), R19(d), R19(e), R22, G9, R23 — under N2's harness
extended over this cut's arms: every arm declared as data (row, assertion,
source mutation, exact failing tests), audited for `vacuous`, `stale`,
`mixed`, `uncollected`, and the class-node collapse, **and carrying the
unsabotaged baseline verdict — every named check resolves and passes against
the real package** — before any result counts.

Three fixture acts do the construction work:

- the **raw filesystem write** — §4.2.1's untrusted import, a fixture act and
  not a slice operation: S7's corpus-check half, S8's negative, R19(d)/(e)'s
  read-side nondetection, R22's at-the-address forgery, and R23's
  basis/composition disagreement;
- the **durable mint** through the add path on the certified tuple, walked
  back out through §6's read surface after reload;
- the **uncertified-tuple refusal** — a write attempted on an existing
  writable tmpfs (`/dev/shm`), asserting the engine's fail-closed refusal
  surfaces as §4's mapping. The fixture **errors if `/dev/shm` is
  unavailable** rather than requiring a privileged mount.

**The certified acceptance command is separate from portable tests.** A
dedicated cut-4 acceptance command runs the durable arms and **errors off the
certified tuple — never skips** — so an environment where durability cannot be
exercised cannot report green. Ordinary unit tests (plan building, refusal
ordering, intent encoding, facade behavior against `DefaultExecutor` or a
fake executor) remain runnable anywhere and **cannot claim cut-4 discharge**.

**The single-planner lock has its own runnable check**, portable, since §5
makes it load-bearing: a deterministic concurrent-add test drives two adds of
the same uid under different ids from two threads against a fake executor
whose `execute` blocks on a barrier, and asserts the operation lock
serializes them end-to-end — the second add observes the first's mint and
raises `CollisionRefused`, and exactly one plan reaches the executor. A lock
covering only `execute` (not the reads and planning before it) fails this
test, which is the sabotage that makes it an arm rather than a smoke test.

## 8. Dependencies, gates, and banking choreography

**Dependencies.** The distributions are already named: `science` gains
`nodes-core` and `atoms-core` as real pyproject dependencies. Local
`[tool.uv.sources]` entries **override their source** with the sibling
checkouts for now; publication removes those overrides and adds the required
released-version bounds. Nothing else changes at publication time.

**Implementation gate.** Code waits on two things this design names and does
not own:

1. the `nodes` seam implementation — ledger row 3's deltas: the `WritePlan`
   types, `Corpus(root, executor_factory=...)`, `DefaultExecutor`, and the
   two error names;
2. the §4 seam amendment, recorded in the seam's §8 amendments log by
   `nodes`-side review **before** any part is consumer-exercised.

**Banking choreography.** Steps 1–3 banked this design on 2026-08-18; step 4
immediately follows in `nodes`:

1. the seam amendment landed in `nodes` as `abbf52b`;
2. cut 4's §7 second reader ran — given the banked row texts and cut 4 §2's
   boundary declaration only, instructed to attack toward overstated
   coverage, with the recorded freeze-reader notes as the checklist: the
   R19(d)/(e)-vs-R22(c) discriminator, G9's dependence on W3, S5's
   walk-as-arm reading, the R16/R20/R21 double-listed bullets, and the parked
   §7 demotion-trigger-list asymmetry;
3. its findings closed, this design banked, and the **same change** flipped cut 4's
   status header to frozen with the date, updates the adoption ledger (row 3's
   exercise note; row 4 — the design is banked, and **adoption remains the
   implementation**, so no production-durability claim moves at banking;
   order-of-work item 5), updates `docs/guide/open-questions.md`, and carries
   the guard propagation a twenty-fourth design forces (README count, table
   and date; guide citation; the `24: "Twenty-four"` `_COUNT_WORDS` entry);
4. the `nodes` exercise map records the **create path** as consumer-exercised
   by this design, activating Science's sign-off right over amendments to it.

**Non-goals restated:** no family adapters, no anchor acts, no holdings root,
no world index, no interim transaction layer, no runtime executor choice.

## Limitations

1. **The recorded-history bound is inherited, not narrowed.** A raw write
   producing a self-consistent record passes the stale-hash check and the
   corpus check — §4.2.1's stated bound, pinned here by S8 and the selected
   R19/R22 negatives; S3's exact import arm remains deferred.
   The chain records the transactions this slice commits, not the filesystem
   beneath them.
2. **Chained but unanchored.** Every transaction registers in the engine's
   chain; no anchor act exists, so the unanchored tail grows without bound and
   its extent is unreported — cut 4's limitation 1, carried here because this
   design is the surface that commits those transactions.
3. **The metadata store is host-local and its absence is normal.** A corpus
   arriving without its sibling cold-bootstraps; one arriving with a foreign
   sibling is a restored-backup classification case. A synced metadata copy is
   untrusted, not impossible.
4. **The pre-plan read argument is scoped to add-only under a single
   planner.** §5's monotonicity rationale covers W3 and S7 alone; the
   collision predicates rest on the single-planner restriction, whose
   cross-process half is a deployment obligation with loud detection
   (`CollisionError` at strict construction), not prevention. Neither
   argument transfers to deletion-capable adapters; Plan B item 2 re-owns
   the question.
5. **The seam amendment is a prerequisite, not an assumption.** If `nodes`
   review rejects or reshapes §4's amendment, this design does not bank as
   written; the affected sections return to review rather than being worked
   around adapter-side.
6. **Transaction execution is engine-serialized; planning is not.** The
   engine's project lock serializes execution per root under the lease, but
   the safety of pre-plan reads depends on §5's single-planner restriction —
   in-process by the operation lock, cross-process as a deployment
   obligation. Nothing here adds cross-root coordination: multi-corpus
   operations remain consumer-composed sequences of per-root transactions,
   per the engine's one-transaction, one-root rule.

> **Amended 2026-09-07** (facet-contracts design §5). Semantic-hash coverage is
> contract-declared and compiled, never stored per node. The existing per-node
> defence remains: the projection records which covered facets are present, so
> an untrusted payload cannot shorten its own coverage.
