# Family adapters under the clean start

**Date:** 2026-08-19

**Status:** Implemented 2026-08-19; post-freeze feasibility corrections recorded
2026-08-19; conformance cut 5 discharged.

**Scope:** Plan B item 2 in
[`2026-08-03-redesign-adoption-ledger.md`](2026-08-03-redesign-adoption-ledger.md):
the supersede, retraction, and explicit-import families at Science's certified
composition root.

**Prerequisite:** The composition-root adapter in
[`2026-08-18-composition-root-adapter-design.md`](2026-08-18-composition-root-adapter-design.md).

## 1. Decision

Add the three mutation families as explicit `CorpusWriter` entry points. Every
entry point reads, refuses, plans, and executes while holding one process-global
operation lock for the resolved corpus root. Every filesystem mutation is an
`atoms` effect executed by the certified engine. No family reconstructs a
Science-side transaction, saved plan, or authentication layer.

The initial surface is deliberately narrow:

| Family | Entry point | Initial kind/scope | Mutation shape |
|---|---|---|---|
| supersede | `supersede(successor, of=...)` | propositions | create successor |
| revise | `revise(node)` | propositions | replace same `(uid, id)` |
| retraction | `retract(record)` | locally resolvable eligible targets | create retraction |
| import | `import_bundle(records, ...)` | one bundle into one local corpus | intent, payload transaction, report transaction |

`supersede` and `revise` are separate because the epistemic kernel draws a hard
line at semantic identity. A semantic change mints a successor. A permitted
prose-only change replaces the existing proposition without changing its
identity.

## 2. Recast rulings

### 2.1 The family list is closed for this item

This item implements supersede, retraction, and explicit import. It does not
adapt proto-science archive or cohort operations.

Archive is absent from the formal model's closed `Action` inventory. Relocation
itself is legal under W5 and the future move family. What has no model is the
old compound operation: relocation plus mutable status-driven visibility.
Computation reproducibility §7.3c is precedent for rejecting that mutable
status shape; it is not a prohibition on relocation. Reintroducing archive
requires a design of its own.

Cohort does not survive as a separate mutation family. Its useful grain is the
bundle, which the formal model's import row already carries. Reintroducing any
other cohort semantics also requires a separate design.

### 2.2 Gate-B and the old planner lapse with their boundary

The clean start has no save/apply boundary. Each public call constructs and
executes its plan before returning, so there is no saved artifact to re-derive
or authenticate. The engine's `intent_digest` is opaque to the engine and
discharges none of Gate-B authentication.

The adapter therefore does not reproduce the old planner, plan file, Gate-B
check, or authentication ceremony. Doing so would recreate the interim
transaction substrate that the engine design forbids. If a save/apply boundary
returns, it needs a new design with its own authenticity contract.

### 2.3 The hard cut has one remaining claim

The clean start carried no superseded execution dialects forward, so the
deletion half of the hard cut is already spent. This item completes only the
adoption half:

> Every Science **corpus mutation** flows through the certified engine.

Execution scratch and materialization writes are distinct surfaces and are not
covered by that sentence. Once this item is banked and implemented, the dated
`atoms` §12.2/§14 amendment may point to this design as the authority for the
current Science platform-support statement.

### 2.4 The world-changing families remain deferred

Consolidate, move/rename, and deletion remain deferred to their own cut with the
world index. G3 and D7 require that index. Those families also invalidate the
monotonic target-resolution argument used below, so they must reopen the
concurrency ruling rather than inheriting it.

## 3. Stored vocabulary

### 3.1 Authored proposition display prose

`display_statement` currently has no storage home: the proposition constructor
stores only the typed claim in the covered proposition facet. This design adds
one optional, uncovered facet:

```json
"display": {
  "display_statement": "authored prose"
}
```

The facet has exactly that one string field. It is absent when no display
statement is authored. It is never added to `COVERED_FACETS`; therefore it does
not participate in the proposition semantic hash. The proposition constructor
accepts the optional value, and the stored-node validator rejects malformed
display facets.

This is the only new proposition storage shape. No parallel gloss field or
compatibility spelling is introduced.

### 3.2 Supersession relation

The successor owns one outbound `supersedes` relation whose object is the
resolved predecessor's canonical live identifier. There is no stored
`superseded_by` back-pointer. Inbound lookup derives that direction.

The adapter, not the caller, authors this relation. A candidate successor that
already supplies a `supersedes` relation is ambiguous and refuses.

### 3.3 Retraction record

Retraction remains a first-class immutable world kind. Its stored constructor
has one discriminated target arm:

- **node arm:** supplied target reference, its resolved local identifier, and
  the target's content identity;
- **route arm:** supplied dataset reference, its resolved local identifier and
  content identity, plus the named route identity from that dataset's stamped
  lineage basis.

The covered retraction facet also records the actor, event token, typed reason
code and rationale, non-empty grounds references, and optional successor
reference. The constructor derives the corresponding `retracts`, `grounded-in`,
and `succeeded-by` relations from those same arguments so that the facet and
graph cannot diverge. The whole retraction facet is semantic-hash covered.

The reason code comes from the closed correction-lifecycle vocabulary. The
constructor is the single storage boundary; raw records with an unknown target
arm, unknown reason, missing attribution, or no grounds are malformed.

## 4. Public write surface

> **Amended 2026-09-04 (write permits):** `CorpusWriter` binds one
> `Authority`; these methods take no actor and require the relevant family
> and emitted kinds before any effect. `import_bundle` attributes its intent
> to the bound actor while preserving imported actors as provenance.

All signatures below are methods on `CorpusWriter`. `Node` remains the public
stored-node value. The create and replace methods return the node that was
durably admitted; import returns its boundary-minted act-report.

### 4.1 `supersede`

```python
def supersede(self, successor: Node, *, of: str) -> Node: ...
```

The initial method accepts proposition predecessors and proposition successors
only. It:

1. resolves `of` in the local corpus;
2. requires a fresh successor `(uid, id)`;
3. requires the successor's proposition semantic identity to differ from the
   predecessor's;
4. constructs a copy carrying exactly one `supersedes` relation to the
   predecessor's canonical live identifier;
5. applies all ordinary `add` eligibility, basis, schema, and collision checks;
6. executes one create-only plan and returns the admitted successor.

The predecessor is byte-untouched. Its assessments continue to bind it, prior
references do not move, and no identifier is renamed. Equal semantic identity
refuses because that operation is a revision, not a supersession.

### 4.2 `revise`

```python
def revise(self, node: Node) -> Node: ...
```

This is the one new mutation shape: one `ReplaceOp` at the existing proposition
path with the same `(uid, id)`. Semantic-hash exclusion is necessary but not
sufficient permission. Retractions and act-reports are immutable, while specs,
verifications, and assessments retain their controlled constructors.

For propositions, the complete revision allowlist is:

- `title`;
- `body`;
- the optional `display.display_statement` value.

Every other field must equal the stored node: `uid`, `id`, `kind`, metadata,
relations, deprecated identifiers, the covered proposition facet, and every
other facet. The recomputed semantic digest must also remain unchanged. A
revision may add, change, or remove the display facet, provided its resulting
shape is valid.

A non-proposition refuses as immutable through this entry point. Any change
outside the allowlist refuses and directs the caller to `supersede`; the adapter
does not silently route between lifecycle operations.

The replacement plan takes its `expected_digest` from the pre-plan read of the
current file. A successful revision returns the replacement node and mints no
new identity.

### 4.3 `retract`

```python
def retract(self, record: Node) -> Node: ...
```

The caller supplies a retraction built by the controlled stored constructor.
The method is create-only. A counter-retraction is the same call targeting an
existing retraction; the model is a chain, never a toggled status.

Before planning, the adapter enforces all locally decidable C10 and C2
requirements:

- the discriminated target arm is valid and its target kind is eligible;
- a node-arm target resolves in this corpus;
- a route-arm dataset resolves in this corpus and the exact route exists in the
  dataset's stamped lineage basis;
- actor and event attribution are present;
- the reason belongs to the closed vocabulary and carries its rationale;
- at least one grounds reference is present;
- all ordinary `add` checks pass for the retraction record.

Target resolution is load-bearing: because an ordinary write cannot introduce
an edge to a missing vertex, and this slice neither deletes nor moves vertices,
it preserves the local DAG invariant. Cross-corpus node targets refuse until
the world index can resolve corpus identities. The target's bytes, address, and
resolution are never edited or deleted by this API.

### 4.4 `import_bundle`

```python
def import_bundle(
    self,
    records: Sequence[Node],
    *,
    actor: str,
    observer: str,
    instrument: str,
    opened_at: str,
    closed_at: str,
) -> ActReport: ...
```

The returned report records the canonical payload order and every import
finding. The input already carries the admitted records, so no second result or
workflow type is introduced. `actor`, `observer`, and `instrument` are the
act-report's required attribution triple (act-report design §2.2, the
holdings-observation vocabulary): all three are required, and `instrument`
names the tool performing the import. `opened_at` and `closed_at` are the
required operation timestamps. All five metadata fields are explicit,
non-empty strings; the adapter supplies no clock fallback.

One call imports one non-empty bundle into one corpus. The boundary freezes the
observer-corpus root, mints operation metadata, and performs three durable
grains:

1. append one operation intent through the engine intent API before any act;
2. validate and publish the complete payload in one engine transaction;
3. publish the boundary-minted act-report, whose `fulfills` names that intent,
   in a separate engine transaction.

"One bundle, one transaction" refers to the payload. The intent and report are
the surrounding tamper-evident operation record, not payload members.

#### Whole-bundle validation

Validation runs over the complete bundle plus the resolved local corpus view
before any payload write. It checks:

- stored-node shape, eligibility, identity basis, and destination paths;
- duplicate identifiers or paths within the bundle;
- any destination member already held, or any identifier/path collision with
  the local corpus;
- every locally recomputable derivation identity;
- semantic stamps, including stale-stamp refusal;
- the locally decidable R20 import clause;
- the retraction graph formed by the bundle union the local context, including
  a topological order and a cycle witness when none exists;
- structural validity of imported act-reports.

If one member is already held or collides, the whole payload refuses; import is
not an idempotent partial-admission API. Any other member failure also refuses
the complete payload with no payload write. A cycle refusal names the offending
edge set.

An input that cannot be resolved in the current local context is admitted with
an import finding where the formal import rule permits unresolved foreign
input. It is not silently treated as verified. An imported foreign act-report
is structurally validated, unauthenticated, attributed, and inert. Import does
not convert it into local authentication evidence or execute the act it
describes.

The adapter builds one payload plan directly. It does not call `add` once per
member, because that would destroy bundle atomicity.

A post-freeze feasibility audit narrowed the earlier validation promise. R19
and R22 semantic recomputation require complete run closures, results,
comparison evidence, frozen specifications, and callable rule implementations;
neither the persisted run/verification/assessment projections nor
`import_bundle(Sequence[Node])` carries those inputs. They are therefore
deferred, as R23 already was. Exact link, identity, and stamp checks remain
import-integrity checks, but are not substitutes for those semantic rules.

A second post-freeze feasibility review narrowed the conformance selection,
not this import boundary. T2's second-fulfillment classification is deferred
until a durable-log consumer exists: the port and engine treat `fulfills` as
opaque and append both registrations, and a test-local count is not a
classifier. M3's bundle-only and bundle-plus-local concrete cycle arms are also
deferred: controlled retraction identities hash their targets, making cyclic
pairs unspellable without circular fixed-point identities, while raw forged
pairs fail controlled-shape validation and are the frozen row's forbidden
non-test.

## 5. Serialization and races

### 5.1 One in-process writer per resolved root

The implementation adds one process-global, root-keyed registry of operation
locks. The key is the resolved corpus-root path. Every `CorpusWriter` for that
root receives the same lock; different roots may proceed independently.

Every family call holds the lock continuously across its read, validation,
refusal, plan construction, and execution. Existing writer entry points use the
same registry. This closes the composition-root design's hole in which two
writer instances in one process could each own a different lock.

Cross-process exclusion remains a deployment obligation with loud startup or
configuration detection. This item does not invent a filesystem lease.

### 5.2 Revision preconditions

There are two possible digest-race observations, and the public mapping remains
the composition-root mapping:

- if the adapter observes a mismatch while building the replacement plan, it
  refuses with that operation index and `applied=0`;
- if the engine observes the mismatch after compilation, its
  `PreconditionRefused` becomes `ExecutionError(index=None, applied=0)`.

Both are clean refusals and neither can clobber the raced file. The design does
not promise the same index for both layers.

### 5.3 Create-only target predicates

*(Amended 2026-09-03, `2026-09-03-world-changing-families-design.md` §3.6: the
monotonicity argument below is retired. Consolidate and move now exist, so a
target that resolved under the lock **can** be made missing. Its replacement:
`retract` and `supersede` re-resolve their target under the lock immediately
before plan construction and refuse if it no longer resolves; each distinct
resolved root is locked exactly once, in sorted order; and the surviving hazard
is crash, whose prefixes that design enumerates.)*

The superseded argument, preserved: supersede and retract are create-only.
Within cut 5's slice, a target that resolved under the lock cannot be made
missing by another supported mutation, because no family deletes or moves it.

### 5.4 Import crash states

The intent/report pair records rather than conceals partial operation history:

| Durable point reached | Observable state |
|---|---|
| intent only | unfinished operation, no payload |
| intent and refusal report | finished operation, refused, no payload |
| intent and payload | unfinished operation, imported records present |
| intent, payload, report | finished operation |

The refusal report **fulfills** the intent — a refused import is a finished
operation that admitted nothing, which is a different state from T2's
unfulfilling report that fulfills nothing.

There is no compensation transaction. There is also no recovery resumption in
this slice. Retrying creates a new operation with a new intent and cannot close
the old one. Explicit recovery correlation—adopting an open intent and minting
the report that fulfills it—is deferred to the log-consumer cut.

## 6. Failure surface

Family validation uses Science `WriteRefused` subclasses. Engine failures retain
the two public names and mappings from the composition-root adapter.

| Refusal | Meaning |
|---|---|
| `SupersedeTargetMissing` | predecessor does not resolve locally |
| `SupersedeIdentityUnchanged` | successor has the predecessor's semantic identity |
| `FamilyKindUnsupported` | the family does not operate on this kind *(gap closure 2026-08-19)* |
| `RevisionTargetMissing` | `(uid, id)` does not identify an existing local proposition |
| `ReviseKindImmutable` | this kind has no revision path |
| `ReviseOutsideAllowlist` | at least one changed field is not revision-permitted |
| `RetractionTargetIneligible` | target arm or target kind is not permitted |
| `RetractionTargetUnresolvable` | required local target, dataset, or route does not resolve |
| `RetractionGroundsMissing` | no grounds reference is present |
| `ImportRefused` | whole-bundle refusal with structured member or cycle detail |
| `BundleMemberHeld` | specialized import refusal for an existing member/collision |

Malformed attribution, reason, display, or stored-node shapes use the existing
validation refusal rather than a new exception per field.

Refusal order is part of each entry point's contract:

1. `supersede`: resolve predecessor; check both kinds and successor freshness;
   reject a caller-authored supersession edge; compare semantic identity; run
   ordinary stored/add checks; plan; execute.
2. `revise`: resolve the exact `(uid, id)`; check kind; compare every field to
   the allowlist and recompute the semantic digest; plan with the observed file
   digest; execute.
3. `retract`: validate the stored retraction, attribution, reason, and grounds;
   check target-arm and target-kind eligibility; resolve the local node or
   dataset route; run ordinary add checks; plan; execute. Resolution itself is
   the ordinary-write DAG-preservation rule; there is no redundant graph scan.
4. `import_bundle`: validate only the request fields needed to select the root
   and mint an intent; append the intent; validate the whole bundle and local
   context; plan and execute the payload; mint and publish the report.

An import refusal after intent append attempts to publish a closing report
before raising `ImportRefused`; the exception carries that report's reference.
If report publication fails, the open intent is the honest durable state from
§5.4. Once any family reaches execution, `PlanRefusedError` and
`ExecutionError` cross unchanged under item 1's table. No adapter catches one
public failure and retries it as another lifecycle operation.

## 7. Read side and corpus checking

### 7.1 Supersession

`superseded_by` is a derived inbound query over the stored `supersedes` edge.
The chase reuses `ReadView`'s relation adjacency and closure machinery; it does
not add a stored back-pointer or a second graph index.

### 7.2 Local standing

The new evaluator is named `standing_in_local_view`. It computes standing from
the retraction records visible in one corpus, including C5's sibling rule and
counter-retraction chains. The name is part of the contract: this is not
authoritative world standing.

Before evaluating standing, the local retraction graph must be acyclic. A cycle
found in raw corpus bytes is classified as malformed rather than assigned an
arbitrary standing value.

World-spanning standing waits on the retraction map, corpus identities, and the
world index. The local evaluator must not later be widened behind the same name.

### 7.3 Corpus findings

The corpus checker gains findings for raw-write shapes made meaningful by this
slice: malformed display facets, invalid supersession targets, invalid local
retraction target arms, missing local targets/routes, and local retraction
cycles. These are corpus-local integrity findings, not the world-level audit
promised by the correction lifecycle.

## 8. Prospective conformance cut 5

Cut 5 is frozen before implementation, using the same row-text, exact-arm, N2,
and second-reader discipline as cuts 1–4. The second reader attacks especially
for overstated coverage.

The prospective selection is:

- **supersede/revise:** S2, S4, G7, and M5;
- **import:** S3 whole; T1's import arm; T2's success, refusal, and
  intent-append-failure arms; M3's local-DAG termination, direct abstract
  witness, forced-verdict consumption, and ordinary unresolved-target arms;
  and R20's corpus-local explicit-import clause;
- **retraction:** the corpus-local arms of C1–C10, plus the positive retraction
  arms of G2c and G8.

The cut document owns the exact split against each frozen row's full text. Any
clause reaching the world index, global retraction audit, corpus identity map,
or verified holdings remains deferred by name.

For M3, the locally runnable selection includes termination over an admissible
local state, a direct abstract cycle witness, forced-verdict refusal with no
payload write, and ordinary-write target resolution in C10's termination role.
The two concrete import-cycle arms, cross-corpus arms, and audit arms remain
deferred.

R20 selects only the contradiction check the local importer can execute. The
original second reader correctly deferred R23 but missed that R19 and R22 also
need semantic evidence absent from the stored projections and import API. A
later implementation-feasibility audit therefore deferred R19 and R22 as a
post-freeze correction. Stale-stamp and exact-link checks remain required
import-integrity behavior; they do not discharge R19 or R22.

The second post-freeze feasibility review deferred one T2 declaration and two
M3 declarations for the reasons above. T2 and M3 remain part rows, so row-state
accounting stays **8 full + 10 part + 6 deferred = 24**; the current N2
inventory is exactly **28** Selected declaration units.

N2 extends over every newly selected arm. On the certified tuple, a selected
arm must run durably; errors on that tuple must never become skips. Portable
tests remain portable.

## 9. Acceptance and banking choreography

Cut 4 remains historical evidence. `python/tools/cut4_acceptance.py` and its
invocation are not edited. Cut 5 receives its own acceptance runner for the new
durable arms; it may invoke cut 4 as a prefix but may not alter cut 4's runner or
meaning.

After this written specification is reviewed, the banking change must contain
the approved family-adapter design and the frozen cut-5 document together. It
also updates:

- the adoption ledger's Plan B row 4 note, order-of-work item 5, and every
  affected `waits on` cell;
- the design-corpus guard for a twenty-sixth design, including the README
  count/table/date and `_COUNT_WORDS`;
- the dated `atoms` §12.2/§14 amendment that cites this design as the recast
  authority.

There must be one banked authority, not a permanent duplicate. At banking, this
review specification is promoted into `docs/designs/` and its status is updated
in the same change as the cut freeze.

Implementation planning begins only after review of this written document. The
implementation order is supersede/revise first, retraction second, and import
last.

## 10. Explicit limitations

- Retraction targets are corpus-local until the world index exists.
- Import's resolved world context is the local corpus.
- `standing_in_local_view` is non-authoritative and corpus-local.
- The retraction model is chained but remains unanchored globally.
- The create-only concurrency proof must be replaced when consolidate,
  move/rename, or deletion lands.
- The inherited recorded-history bound is unchanged.
- Cross-process one-planner enforcement remains a deployment obligation.
- An import stranded after payload commit has no recovery resumption in this
  slice; recovery correlation belongs to the log-consumer cut.
- Execution scratch and materialization writes are outside the hard-cut claim.
- Archive and any cohort semantics beyond import bundles require their own
  designs.

## 11. Alternatives rejected

**One `edit` entry point that routes implicitly.** Rejected because equal versus
changed semantic identity is a lifecycle choice with different identity and
reference consequences. Silent routing would obscure caller intent.

**Revision of every semantically uncovered field.** Rejected because hash
coverage is an identity rule, not a lifecycle permission list. The explicit
per-kind allowlist keeps immutable and controlled-constructor kinds immutable.

**A stored supersession back-pointer.** Rejected because the successor's one
outbound edge already answers the inbound query and avoids two-record atomicity.

**Per-writer locks.** Rejected because multiple writers can open the same root in
one process. The smallest correct lock scope is the resolved root.

**Per-member import calls.** Rejected because they cannot provide whole-bundle
validation or all-or-nothing payload admission.

**Closing an old intent on retry.** Rejected for this slice because safe intent
adoption needs explicit recovery correlation. A fresh retry is honestly a new
operation.

**Rebuilding Gate-B around `intent_digest`.** Rejected because the digest is
opaque and there is no saved plan boundary to authenticate.
