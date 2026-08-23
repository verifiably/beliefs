# World registry and corpus-state identity — authoritative slice

**Date:** 2026-08-20

**Status:** Implemented 2026-08-20; conformance cut 6 discharged
([results](../plans/2026-08-20-conformance-cut-6-results.md)). The dated
deferrals in §10 remain.

**Scope:** Slice 1 of the world-index implementation in
[`2026-08-03-redesign-adoption-ledger.md`](2026-08-03-redesign-adoption-ledger.md):
the world root, corpus manifest and fresh-adoption act, corpus-state identity,
authoritative registry, lifecycle status, and caller-supplied installation
configuration.

**Inherited authorities:**
[`2026-08-03-world-index-packaging-design.md`](2026-08-03-world-index-packaging-design.md),
world-addressing §5 and W13,
[`2026-08-03-tamper-evident-log-design.md`](2026-08-03-tamper-evident-log-design.md),
and the certified composition root in
[`2026-08-18-composition-root-adapter-design.md`](2026-08-18-composition-root-adapter-design.md).

## 1. Decision and boundary

Build the authoritative core of the world index as a second `atoms` engine
root. The root holds an append-only registry whose records establish corpus
admission and terminal lifecycle status. A root-local manifest gives each
adopted corpus its opaque identity and profile pins. Corpus-state identity is a
canonical digest over that manifest and the complete canonical contents of its
nodes.

The slice contains:

- a typed, caller-supplied `WorldConfig`, including a caller-minted `world_id`;
- explicit world-root initialization and opening;
- `world.yaml`, a readable mirror of the genesis `world_id`;
- closed loading and canonical projection of `corpus.yaml`;
- fresh corpus adoption and `corpus_id` minting;
- corpus-state identity;
- admission records for `fresh`, `replica-of`, and `fork-of` provenance;
- terminal `retired` and `departed` status records;
- computed `known`, `live`, and `present` status;
- registry and presence findings that this slice can establish; and
- certified durable writes with committed registration-entry evidence.

The slice does not contain epochs, the address/producers/retraction/coreference
maps, any of the four derivation receipts, the rules store, `current`,
staleness, garbage collection, anchored head members, or world-index builds.
It does not add the two unbuilt kernel kinds `coreference-attestation` and
`instrument-certification`. Slice 2 receives its own design and cut; its
brainstorm decides whether those kinds land there or continue to wait on their
owning designs.

The following dated rulings recast the banked packaging design for this slice.

### 1.1 The interim writer is never built

The packaging design's best-effort registry and epoch writer was conditional on
composition-root adoption not existing. That adoption landed on 2026-08-18 and
2026-08-19. Registry writes therefore use the certified engine from their first
commit. The registry-append half of packaging limitation 2 lapses unexercised;
X2's epoch-publication half remains gated on slice 2.

There is no compatibility path, best-effort fallback, or second persistence
implementation.

### 1.2 Reserved-path reliance is interim and explicit

`corpus.yaml` currently survives `nodes` traversal because the observed walk
selects `*.md`. That observation is sufficient to implement this slice, but it
is not a declared contract. The reservation of root-level non-node paths remains
part of the `nodes` contract-delta artifact in ledger row 3 and lands on that
repository's own clock.

Science neither copies the walker nor adds a filter that pretends to discharge
the missing contract.

### 1.3 Cut 6 covers only registry-side arms

Cut 6 selects the registry-side arms of X4, X5, and X6, the W13 arms made
executable by this slice, and the new durability and finding arms described in
§8. X7 and X5's build-side duplicate-carrier refusal are declared and deferred
to slice 2. Under the standing any-unrun-arm rule, their rows remain partial.

## 2. World root and composition-root wiring

### 2.1 Configuration is an external typed value

The public installation value is immutable and caller-supplied:

```python
@dataclass(frozen=True)
class WorldConfig:
    world_root: Path
    world_id: str
    corpus_roots: tuple[Path, ...]
```

`world_id` is exactly 128 bits rendered as 32 lowercase hexadecimal characters.
The caller mints it before initialization. `corpus_roots` is the installation's
current presence set, not registered world content. Paths are resolved before
root-state lookup; paths themselves enter no identity.

Configuration stays outside the world root and outside its registered surface.
It is operational input that must survive loss of the root, never an authority
copied into the root and then mistaken for independent evidence.

The public composition-root calls are:

```python
def init_world_root(config: WorldConfig) -> None: ...
def open_world(config: WorldConfig) -> World: ...
```

### 2.2 Genesis and the readable mirror

`science.root` gains:

```python
WORLD_GENESIS_DOMAIN = "science.world-root.v1"
WORLD_CONSUMER_TAG = "science-world-write-v1"
```

The canonical genesis payload carries `WORLD_GENESIS_DOMAIN` and the supplied
`world_id`. Registration is explicit and idempotent on the same payload and
registered-root facts, exactly as corpus-root registration is today.

At this slice's freeze, the public engine had no chain-read API, so Science
could not read the genesis payload back during ordinary operation.

> **Dated recast 2026-08-20:** world-index slice 2 §2 now banks the prospective
> public `atoms.read_chain` contract. Its implementation remains a prerequisite
> to that slice. Genesis-to-mirror verification still waits on the
> configuration-mismatch audit's ownership decision; reader availability no
> longer owns that deferral.

Initialization writes a root-local `world.yaml` mirror with the closed shape:

```yaml
world_id: 0123456789abcdef0123456789abcdef
```

The sequence is:

1. resolve and validate the configured root and `world_id`;
2. register the world root with the engine and genesis payload;
3. if no mirror exists, commit one create-only engine transaction writing
   `world.yaml`, with that path in `registered_paths`;
4. if the exact mirror already exists, treat the call as an idempotent retry;
5. refuse an unloadable mirror or one carrying a different id.

This makes initialization retry-stable across the only exposed crash seam:
registration may commit before the mirror transaction, and the same
caller-held id completes the missing mirror on retry. The id is never minted
inside a return path where a crash could make it unreadable and unrecoverable.

Initialization already checks configuration against genesis: because the
configured `world_id` is inside the genesis payload, `register_root` returns the
existing digest only for the same id and registered surface and otherwise
raises `PreconditionRefused`. The readback deferral therefore applies only to
the ordinary `open_world` path, which cannot perform that registration check.

`open_world` requires the mirror and checks its id against `WorldConfig`. An
absent or malformed mirror raises `WorldUninitialized`; a well-formed different
id raises `WorldIdMismatch`. The genesis remains authoritative. On the open
path, agreement among configuration, genesis, and mirror is not checkable
through the current public engine surface and is therefore deferred, dated
2026-08-20, to the log design's chain verification. That design already owns
configuration-mismatch findings.

The mirror is neither a second authority nor an anchor. Slice 1's acceptance
can prove that its successful creation committed a registration entry naming
`world.yaml`; it cannot claim full replay or genesis/mirror refutation without
the deferred reader.

### 2.3 Layout

The effective layout after the corresponding members first arrive is:

```text
<world-root>/
  world.yaml
  registry/
  epochs/
  rules/
  .#~chain/
```

`.#~chain/` is the engine-owned reserved chain path. The banked packaging
design's `log/` spelling is stale and will be corrected when this design is
promoted. `registry/`, `epochs/`, and `rules/` are placement contracts, not an
empty scaffold: the engine creates parent directories as derived effects when
their first file is written. This slice writes no epoch or rule member, so it
does not pre-create either directory.

### 2.4 One durable seam, two root kinds

`science.root` remains the only Science module that imports `atoms`.
`science.world` defines values, parsing, reduction, and the `World` API without
an engine import. Every world-root mutation is one `WritePlan` executed through
the existing `WritePlan -> DurableExecutor` seam.

The existing executor is minimally parameterized by root kind: consumer tag,
intent domain, and the affected durable paths. The transaction's
`registered_paths` are derived from its write-plan paths. Consequently every
durable file introduced here—`world.yaml`, `corpus.yaml`, and each registry
record—appears in its transaction's committed registration entry. No parallel
world executor or transaction wrapper is introduced.

World state has its own per-resolved-root entry:

```python
@dataclass
class _WorldState:
    lock: threading.Lock
    registry: RegistryView
```

It is separate from corpus `_RootState`, which owns a `nodes.Corpus` and its
read facade. A `World` holds the immutable configuration and its `_WorldState`.
The registry cache is only a view; §5.5 requires a rescan under the lock before
every read and mutation.

## 3. Corpus manifest

### 3.1 Value and closed loader

`science.world` defines the immutable value:

```python
@dataclass(frozen=True)
class CorpusManifest:
    manifest_version: Literal[2]
    corpus_id: str
    profile: CorpusPins
    forked_from: ForkedFrom | None = None

@dataclass(frozen=True)
class ForkedFrom:
    corpus_id: str
    corpus_state: str
```

The YAML form remains the banked shape:

```yaml
manifest_version: 2
corpus_id: 0123456789abcdef0123456789abcdef
profile:
  science_contract: science:<contract-identity>
  domains:
    biology: biology:<contract-identity>
forked_from:
  corpus_id: fedcba9876543210fedcba9876543210
  corpus_state: <science.corpus-state.v1 identity>
```

`profile` has the value shape already carried by `consulted.CorpusPins`: one
base `science_contract` and a namespace-to-contract `domains` mapping. The
manifest boundary performs the stronger authored-document checks: exact
mapping shapes, no `science` key in `domains`, canonical namespace and contract
identities, and agreement between each domain key and its contract namespace.

`corpus_id` and a fork parent's id are 32 lowercase hexadecimal characters.
`corpus_state` is a 64-character lowercase hexadecimal digest interpreted under
the corpus-state domain; the digest spelling does not itself encode its domain.
The loader accepts version 2 and no other version.

`load_manifest(corpus_root)` parses `corpus.yaml` without losing duplicate-key
information, then validates every mapping as closed. Unknown fields, duplicate
keys at any level, missing fields, extra provenance fields, wrong types,
malformed identities, invalid hex, or a wrong version raise
`ManifestMalformed`. A missing file raises `ManifestMissing`; absence and
damage remain distinct.

### 3.2 Canonical projection

`manifest_projection(manifest)` returns only the complete semantic value:

```text
manifest_version
corpus_id
profile(science_contract, domains mapping)
forked_from, when present(corpus_id, corpus_state)
```

It is encoder-ready and independent of YAML whitespace, quoting, comments, and
key order. Mapping order is canonicalized by `science.identity.v1`; absence of
`forked_from` remains distinct from a present value. No raw YAML bytes enter an
identity.

This projection is the single manifest representation used in corpus-state
identity and copied into admission records. There is no second admission-only
projection.

### 3.3 Fresh adoption

The only corpus-local manifest mutation in slice 1 is:

```python
def CorpusWriter.adopt_manifest(
    self, *, profile: CorpusPins
) -> CorpusManifest: ...
```

While holding the corpus root's existing operation lock, it:

1. validates the profile at the authored boundary;
2. refuses if `corpus.yaml` already exists;
3. mints 128 random bits as 32 lowercase hexadecimal characters;
4. constructs the version-2 manifest with no `forked_from`;
5. writes `corpus.yaml` create-only through the certified corpus executor, with
   the path in `registered_paths`; and
6. returns the committed manifest.

An existing manifest always raises `ManifestAlreadyPresent`; no ordinary API
re-mints. A retry after an uncertain result does not need a caller-minted id:
the committed manifest is readable, so `load_manifest` recovers the id. This is
different from genesis, whose payload has no public read path.

### 3.4 Fork construction is deliberately absent

The `forked_from` schema and `fork-of` admission arm remain in slice 1 and are
exercised with fixture-authored manifests. No `CorpusWriter.declare_fork`
method is built.

A filesystem copy includes the parent's `.#~chain/`. Replacing its manifest as
an ordinary corpus transaction would append a fork declaration to the parent's
chain, contradicting L10's rule that a fork begins a new genesis carrying the
parent genesis and head. The operation is irreversible once written and cannot
be repaired by later metadata.

The fork constructor is therefore deferred, dated 2026-08-20, until the engine
exposes head-read/root-fork capability. It will be a composition-root act that
creates a new root and genesis, not a mutation on an opened corpus. A replica
requires no manifest act and preserves the id and chain.

## 4. Corpus-state identity

The public function is:

```python
def corpus_state_identity(corpus_root: Path) -> str: ...
```

The outer domain is `science.corpus-state.v1`. Its projection is exactly:

```text
{
  "manifest": <complete manifest_projection>,
  "nodes": [
    {"uid": <uid>, "content_identity": <node content identity>},
    ... sorted by uid ...
  ]
}
```

For each node, Science first obtains `nodes`' public, versioned canonical JSON
text for the `STANDARD.md` §11.1 projection—the complete canonical node
projection, including relations and facets. The `nodes` API owns that text and
pins its cross-language serialization, including JSON number spelling; it may
also expose the parsed projection as a convenience, but Science consumes the
text. `nodes` does not mint a digest.

Science parses the text with `json.loads`, using `parse_int=Decimal` and
`parse_float=Decimal`, so every JSON number takes its digits from the canonical
serialization and no binary float is materialized. It then applies this
uniform, recursive JSON-value lift before calling
`v1.digest("science.node-content.v1", lifted)`:

```text
null       -> ["null"]
boolean b  -> ["boolean", b]
number n   -> ["number", Decimal(n)]
string s   -> ["string", s]
array xs   -> ["array", [lift(x) for x in xs]]
object m   -> ["object", {key: lift(value) for key, value in m}]
```

Tagging every JSON type makes the lift injective: an authored object that
resembles one tag remains an `object` value and cannot collide with that tag.
Non-standard constants and non-JSON values refuse. `Decimal(str(value))` is
permitted only if a separately documented value-shaped fallback is ever
adopted; that fallback must pin CPython's shortest-representation dependence in
a unit test and is not part of the selected text API.

The lift re-encodes the projection under Science's identity contract; it does
not re-canonicalize `nodes` semantics. In particular, list order is preserved,
so relation reordering still moves identity. Science deliberately owns the
digest and its `science.node-content.v1` domain, and the corpus identity digests
the resulting node identities rather than inlining node projections. Corpus
members are sorted by `uid`, never path or traversal order.

The consequences are intentional:

- changing node content, facets, or relations moves the state;
- adding, removing, or retargeting a relation moves the state;
- reordering relations moves the state because §11.1 preserves document order;
- renaming a node file without changing its `uid` or projected content does not
  move the state;
- reformatting `corpus.yaml` or reordering its mappings does not move the state;
- changing any manifest fact semantically does move the state;
- other non-node files, mtimes, filesystem paths, and git state are excluded.

A corpus with no manifest has no corpus-state identity and raises
`ManifestMissing`. A malformed manifest raises `ManifestMalformed`. A node that
cannot be parsed or projected, JSON text that cannot be parsed or lifted, an
NFC collision between projection keys refused by `v1.encode`, or a
duplicate/colliding `uid` that prevents the sorted member set from being formed,
raises `CorpusStateMalformed` with the original parse, projection, lift,
`KeyCollision`, or corpus collision error chained as `__cause__`.

The required `nodes` §11.1 projection is confirmed absent from its public API as
of 2026-08-20; it exists only in test support. Ledger row 3 therefore receives a
`nodes` API task, ordered before Science consumes it, to ship the versioned
canonical projection text in the owning repository and pin it in both language
implementations. Science does not copy the test helper, invent a local
approximation, or ask `nodes` to own the Science digest.

## 5. Authoritative registry

### 5.1 Record shapes and content names

The registry has two immutable, closed value kinds. Their identity domains are:

```text
science.world-admission.v1
science.world-status.v1
```

An admission record contains:

```text
record_kind: admission
corpus_id
manifest: <complete manifest_projection at admission>
provenance:
  fresh
  | replica-of(parent corpus_id)
  | fork-of(parent corpus_id, parent corpus_state)
actor
```

A status record contains:

```text
record_kind: status
corpus_id
status: retired | departed
actor
```

The record digest is `science.identity.v1` over the corresponding domain and
complete record projection. Each event is serialized as one closed YAML file at
`registry/<digest>.yaml`; the stem is exactly its digest. No timestamp,
sequence, or arrival-order field is added, because no reduction may depend on
one.

Validity is projection-level, not byte-level. Different YAML formatting that
parses to the same closed projection has the same valid content name; the raw
serialization bytes are not the record identity.

Loading a registry file parses and validates the closed value, recomputes its
domain-selected digest, and compares it with the filename. An unknown file,
directory, unknown field, duplicate key, malformed value, wrong kind, or wrong
content name raises `RegistryMalformed`. One bad member refuses the complete
view; it is never skipped.

### 5.2 Admission

The public call is:

```python
def World.admit(
    self,
    corpus_root: Path,
    *,
    provenance: AdmissionProvenance,
    actor: str,
) -> AdmissionRecord: ...
```

All three provenance arms are authored values. Their manifest checks are:

- `fresh` requires no `forked_from`;
- `replica-of(parent)` requires no `forked_from` and names the same retained
  `corpus_id`; and
- `fork-of(parent, corpus_state)` requires `forked_from` to match both values
  exactly.

The refusal order is normative:

1. while holding the world lock, rescan and validate the complete registry;
2. load the target manifest;
3. validate the authored provenance against it;
4. construct the complete admission record, recompute its content name, and
   return idempotent success if that exact file already exists;
5. refuse if any admission already makes the `corpus_id` known;
6. for `fork-of`, refuse if the parent id is not already admitted;
7. append the record create-only in one certified world-root transaction.

The exact-file check must precede known-id refusal: an exact retry is necessarily
a known id and is success, not `CorpusIdKnown`.

Known ids are refused uniformly. A replica already admitted to this world needs
no new act; changing configured presence is sufficient. `replica-of` describes
the first arrival of that retained id to a world that has never admitted it. It
is not an exception that permits a second admission.

> **Amended 2026-08-23** (the log-verification design §6.2; execution ruling
> R34). `World.admit` now refuses a `ReplicaOf` provenance outright with
> **`ReplicaAdmissionRequiresVerification`**, *before* the world lock and
> *before* any known-id consideration — a replica's chain traveled, admitting it
> is the one admission that asks a question about evidence, and a bare `admit`
> inspects nothing and so has no answer to report. The refusal order above is
> therefore what runs **after** that check, and the two paragraphs above
> describe the **verified** route: `science.root.admit_arrival`, which loads the
> arriving root's manifest under that root's own lock, verifies the traveled
> chain against `Corpus(parent_corpus_id)`, and commits through the very
> admission core the numbered order states. On the bare-admit path a replica
> never reaches the known-id check at all. `Fresh` and `ForkOf` are unchanged.
>
> **Cut 6's X5 replica clause is superseded by this, not satisfied.** Its arm
> `test_known_id_refuses_fresh_and_replica_provenance` asserts that a *known id*
> refuses both provenances; both refusals and the arm's green result survive,
> and no frozen cut-6 file was edited, but the replica half no longer
> demonstrates the row's claim, because the refusal it now observes is the
> replica refusal rather than the known-id one. There is no way to preserve the
> claim on that path. Recorded in the cut-8 results record
> (`../plans/2026-08-22-conformance-cut-8-results.md`, §7.2) rather than left
> for a harness that cannot see it.

A legitimate fork retains the parent's admission and declares the parent in its
manifest. `fork-of` therefore raises `ForkParentUnknown` when that parent is not
known. This is also the registry fact W13 uses to distinguish a declared fork
from coordinated identity mimicry.

### 5.3 Terminal status events

The public calls are:

```python
def World.retire(self, corpus_id: str, *, actor: str) -> StatusRecord: ...
def World.depart(self, corpus_id: str, *, actor: str) -> StatusRecord: ...
```

Each call rescans, validates the target id, constructs its record, and returns
idempotent success if that exact content-named file already exists. An unknown
id raises `StatusTargetUnknown`. If any terminal record already exists for the
id, every genuinely different later act raises `StatusTerminal`, including a
second terminal status or the same status under a different actor.

The reduction remains robust to raw record arrival: if two well-formed terminal
records exist, `live` is false regardless of their order. The API's early
refusal prevents producing that state; it does not make the order-free reader
depend on the refusal having been obeyed.

Every successful append is one create-only engine transaction, serialized by
the world lock, with its registry path in `registered_paths`. There is no purge,
replace, or delete API.

### 5.4 Computed status and presence

Registry status is a reduction over the complete record set:

```text
known := at least one admission exists for corpus_id
live  := known and no terminal status record exists
```

Presence is computed from the current `WorldConfig`, independently of registry
arrival order. Repeated configuration entries resolving to the same root count
as one carrier:

```text
present := exactly one configured corpus root carries a loadable manifest
           whose corpus_id is the target
```

No matching carrier yields `present = False`. Exactly one yields `True`. More
than one yields `False` together with a distinct error-severity
`duplicate-carrier` finding naming the id and resolved carrier roots; it is not
silently collapsed into ordinary absence. Slice 2's X5 build arm will turn that
finding into build refusal.

`known`, `live`, and `present` are independent facts. A retired corpus may
remain present; a live corpus may be absent; restoring one replica of an
admitted live corpus changes only `present` and appends no admission.

A malformed configured manifest refuses presence resolution rather than being
treated as a non-match: without loading it, the reader cannot establish which
id that root carries. A configured root with no manifest is an unadopted legal
partial state and counts as a non-carrier; `ManifestMissing` does not poison
presence queries for other ids.

### 5.5 Read and lock discipline

The public read surface is:

```python
def World.registry(self) -> RegistryView: ...
def World.status(self, corpus_id: str) -> CorpusStatus: ...
```

`RegistryView` is immutable and exposes the validated admission and status
values. `CorpusStatus` carries `known`, `live`, `present`, and any presence
findings. Neither exposes a mutable `nodes.Corpus` or engine capability.

Both calls acquire the world root's lock and rescan every registry member from
disk before returning. Every mutation does the same rescan while holding that
same lock before it checks preconditions or writes. A cached view may avoid
reduction work only after that rescan; it never authorizes a mutation and never
serves a stale status.

This is an in-process serialization guarantee, matching the corpus writer's
current boundary. Cross-process single-writer operation remains the existing
deployment obligation; this slice does not invent another lock protocol.

## 6. Failure surface

The following fine-grained errors join `science.errors`, following the existing
explicit-refusal discipline:

| Error | Boundary |
|---|---|
| `ManifestMalformed` | present manifest cannot be parsed, projected, or validated |
| `ManifestAlreadyPresent` | fresh adoption finds any existing manifest |
| `ManifestMissing` | a manifest-required operation finds no manifest |
| `WorldIdMismatch` | configured id differs from the valid mirror |
| `WorldUninitialized` | world mirror is absent or malformed |
| `ProvenanceMismatch` | admission provenance contradicts the manifest |
| `ForkParentUnknown` | a fork admission names no admitted parent |
| `CorpusIdKnown` | a non-idempotent admission reuses a known id |
| `StatusTargetUnknown` | status act names no admitted id |
| `StatusTerminal` | a differing act follows a terminal status |
| `RegistryMalformed` | any registry member or content name is invalid |
| `CorpusStateMalformed` | a node cannot participate in state identity |

`CorpusStateMalformed` always chains the underlying node parse, projection,
JSON parse/lift, `KeyCollision`, or corpus collision error. Manifest absence
and damage retain their own errors rather than being wrapped as corpus-state
failures.

Admission follows §5.2's pinned order. Status follows the analogous order:
rescan and establish a known target, compute the candidate and accept an exact
retry, refuse any other act after terminality, then append. No API silently
normalizes malformed authored input or falls through to a less specific error.

## 7. Findings and corpus checking

World reads report `duplicate-carrier` as described in §5.4. It is a finding,
not an exception, because status can still report the other monotone facts and
the duplicate is exactly the raw-write escape whose build consequence belongs
to slice 2.

`corpus_check` gains one explicitly selected cut-6 strengthening:

```text
severity: error
code: manifest-malformed
ref: corpus.yaml
```

It is emitted when `corpus.yaml` exists but `load_manifest` refuses it. This is
parallel to cut 5's `display-malformed`: a damaged authored file surfaces in the
corpus's own audit rather than only when a world tries to load it.

An absent manifest produces no corpus finding. Unadopted corpora remain a legal
partial state, even though manifest-dependent operations such as state-identity
computation and admission refuse them. The strengthening is a named cut row,
not an implementation side effect.

Malformed or misnamed registry files are different: `World.registry()` and
`World.status()` refuse the entire read with `RegistryMalformed`. Skipping one
would compute authority from an invented subset.

## 8. Prospective conformance cut 6

Cut 6 is authored and frozen before implementation, using the row-text,
exact-arm, second-reader, and N2 sabotage discipline of cuts 1–5. Its selection
is prospective until the cut document records exact declarations.

### 8.1 Selected arms

- **X4, API arms:** every registry API is append-only; purge, replacement, and
  deletion are unspellable. Limitation 1's raw-deletion negative is declared,
  not selected as detected.
- **X5, admission arm:** admitting a known id refuses, with exact retry handled
  separately as idempotent success. The build-side duplicate-id refusal is
  declared and deferred to slice 2.
- **X6, full row:** monotone order-free status, terminal-state refusals, and
  replica presence becoming true again with no new admission.
- **W13, slice-1 arms:** fresh opaque minting; no ordinary re-mint API; node
  content and relation changes moving corpus state; file rename, non-manifest
  non-node-file reformat, manifest reformat, mtime, and git changes leaving it
  fixed; semantic manifest changes moving it; and
  malformed/unknown/duplicate manifest inputs refusing.
- **Idempotency arms:** exact admission retry, exact terminal-status retry, and
  world initialization retry across registration/mirror separation.
- **Durable arms:** `world.yaml`, `corpus.yaml`, and registry append on the
  certified volume, each with committed registration-entry evidence naming its
  durable path.
- **Corpus-check strengthening:** a present malformed manifest emits
  `manifest-malformed`; absence does not.

The durability claim is intentionally limited to committed registration-entry
evidence. Tests may decode the engine-owned chain as acceptance evidence, as
the existing durable-family tests do. Full replay/refutation and
genesis-to-mirror agreement remain the deferred log reader's claim. *(Amended
2026-08-23: that reader is no longer deferred. World-index slice 3
(`2026-08-22-log-verification-design.md`) built the registered-surface
projection and replay, the four-outcome evaluator, and the genesis↔mirror
agreement check — `open_world` now refuses a mismatch and the world audit
reports it — discharging conformance cut 8. **Cut 6's own durability claim is
unchanged and is not restated by that landing**; what changes is that the
claim's stated successor exists.)*

### 8.2 Declared deferrals and classification

X7 is declared and deferred because no epoch build exists to test admission as
the build commit point. X5's build-side duplicate-carrier refusal is declared
and deferred for the same reason. Cut 6 is therefore partial under the
any-unrun-arm rule.

The fork-constructor arm of W13 is also declared but not claimed by fixture-only
admission coverage. It waits on the head-read/root-fork capability in §3.4.

No X2 epoch arm, map, receipt, current-pointer, staleness, GC, anchor-member, or
kernel-kind arm enters this cut.

### 8.3 Test and runner shape

Cut 5 remains historical evidence and its runner is never edited. Cut 6 gets
all three corresponding surfaces:

```text
python/tests/n2_arms_cut6.py
python/tests/acceptance/test_n2_cut6.py
python/tools/cut6_acceptance.py
```

N2 sabotages every selected declaration so no arm can pass vacuously. On the
certified tuple, a selected durable arm runs and errors cannot become skips.
Portable tests remain portable.

## 9. Banking and implementation choreography

The sequence is fixed:

1. review this specification;
2. author the cut-6 selection document with exact row text and declarations;
3. run a second-reader review aimed at overstated coverage and record its
   disposition;
4. promote this specification with `git mv` into `docs/designs/`, freeze cut 6,
   and bank both authorities in one change;
5. update the design corpus from 26 to 28 in that banking change — the
   promotion adds two members, this design and the cut document: extend
   `_COUNT_WORDS` with 27 and 28, update the README count sentence/table/date
   range, and make no unrelated corpus-guard edits;
6. implement and release the public, versioned `nodes` §11.1 canonical JSON
   text API in its owning repository first, with cross-language serialization
   parity;
7. implement the Science slice;
8. add `n2_arms_cut6.py`, the cut-6 acceptance test, and the new acceptance
   runner, leaving cut 5 untouched;
9. run portable and certified acceptance, then write the cut-6 results record;
10. close out the ledger and propagated user-facing claims in the same landing
    change.

The ledger close-out is precise rather than binary:

- artifact 1 records that the authoritative slice landed while epochs and the
  rest of the world-index build remain outstanding;
- artifact 2 becomes **partially landed**: fresh adoption and minting complete;
  fork construction and build-time uniqueness outstanding; and
- artifact 3 records the shipped §11.1 canonical-text API task without claiming
  the separate reserved-path work unless it also landed independently.

After correcting those status claims, grep the guide and other user-facing docs
for propagated statements that still say manifests, corpus ids, or the entire
world index are wholly unbuilt. A merge is the moment the design status becomes
stale, so the promoted design's header and checkboxes are corrected in that same
change.

Implementation planning starts only after this specification and cut 6 are
reviewed and banked. The first implementation task is the cross-repository
`nodes` projection prerequisite; Science does not begin by working around it.

## 10. Explicit limitations and dated deferrals

- **Fork construction — 2026-08-20:** waits on public head-read/root-fork
  capability and lands as a composition-root act (§3.4).
- **X7 and X5 build arm — 2026-08-20:** wait on slice 2's epoch build and its
  cut (§8.2).
- **Genesis/mirror verification — 2026-08-20:** waits on the log design's public
  chain reader and configuration-mismatch audit (§2.2).
- **Public `nodes` §11.1 canonical text — confirmed missing 2026-08-20:** lands
  with cross-language parity in `nodes` before Science consumes it (§4).
- **Registry deletion detection:** the registry is chained but unanchored; raw
  deletion remains packaging limitation 1 until the log consumer lands.
- **Cross-process writers:** in-process locks serialize cooperating Science
  writers; single-writer deployment across processes remains an obligation.
- **Reserved manifest path:** observed `*.md` traversal suffices temporarily;
  the declared reservation remains ledger artifact 3 (§1.2).
- **All derived world-index behavior:** epochs, maps, receipts, rules, current,
  staleness, GC, and anchored members remain slice 2.

> **Dated amendment 2026-08-21.** Slice 2 has landed and conformance cut 7 is
> discharged (`2026-08-20-world-index-slice-2-design.md`; results at
> `../plans/2026-08-20-conformance-cut-7-results.md`), so the two deferrals above
> that named it are answered: X5's build-side duplicate-carrier refusal is
> implemented — a coverage naming two carriers with one `corpus_id` refuses
> `CoverageUnresolvable` at preflight, with the `duplicate-carrier` finding still
> emitted — and X7 is discharged in full, along with epochs, the four maps and
> receipts, the rules store, `current`, bounded reads, GC, and anchored members.
> The slice-1 boundary statements above are unchanged: they describe what slice 1
> contains, and that is still what it contains. Slice 2 **merged into `main` on
> 2026-08-22 preserving history**; fork construction, genesis/mirror
> verification, registry deletion detection, cross-process writers, and the
> reserved manifest path are untouched by it.

No `atoms` amendment is required for slice 1. The mirror ruling removes the
runtime genesis-read consumer, and the fork deferral removes the runtime
head-read consumer. The acceptance suite may inspect committed chain evidence;
production code may not import a private chain reader to erase the deferral.

## 11. Alternatives rejected

**Mint `world_id` inside initialization and return it.** Rejected because a
crash after genesis commit but before return strands the only authoritative id
behind an unreadable public engine surface. Caller minting makes retry input
stable.

**Treat `world.yaml` as authority.** Rejected because genesis already owns root
identity. The mirror solves current readback only; the log verifier later checks
agreement.

**Wait for chain read before building any registry.** Rejected because the
mirror removes the only slice-1 runtime need for it, while committed
registration evidence already covers the durable write claims selected here.

**Build the packaging design's interim writer.** Rejected because the certified
composition root exists. A second durability path would add code only to delete
it and would exercise a lapsed limitation instead of the target architecture.

**Pre-create the complete world layout.** Rejected because empty directories
carry no contract and the engine already creates derived parents for the first
real member.

**Declare a fork by replacing the copied manifest.** Rejected because the copy
still carries the parent's chain. A fork is new genesis, not a corpus edit.

**Copy `nodes`' test-only canonicalizer into Science.** Rejected because two
implementations of §11.1 can drift while producing plausible identities. The
owning repository must expose the projection it specifies.

**Trust the cached registry view.** Rejected because raw arrival between reads
would make status and uniqueness depend on process history. Rescanning under
the existing root lock is the smallest correct authority boundary.

**Permit repeated terminal acts because reduction is monotone.** Rejected
because reader tolerance of raw disorder is not permission for an authored API
to produce meaningless duplicate lifecycle acts. Exact retry succeeds;
different post-terminal intent refuses.

**Treat duplicate carriers as ordinary absence.** Rejected because absence and
corruption are different facts. The finding preserves that distinction until
slice 2's build gives it its authoritative refusal point.
