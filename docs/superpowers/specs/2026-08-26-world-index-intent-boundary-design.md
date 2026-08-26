# General intent qualification — design (world-index slice 6, the intent boundary)

**Date:** 2026-08-26
**Status:** draft — spec under review; conformance cut 11 freezes before any
implementation task, per §8 step 3. Promotion from `docs/superpowers/specs/`
to `docs/designs/` happens in the banking change, per the slice-5 precedent.
**Amended 2026-08-26**, closing the design review's five findings before any
cut draft: the captured-record evidence input (§3.1), the per-shape matching
requirements (§2.2), decode-gate semantics for unknown and malformed intent
payloads (§3.2), the concrete `LogReport` contract (§3.3), and the
`science.report.completion` re-base (§2.5). **Amended again 2026-08-26**
(second review round): pending-fulfillment semantics (§2.1), the domainless
discriminators and the assessment-run wire shape with its durable append
(§3.2), no-follow capture (§3.1), the corrected evidence constraint
(header), and pinned finding placement (§3.3). **Amended a third time
2026-08-26** (third review round): fd-anchored no-follow capture closing
the swap race (§3.1), the run boundary's persistence contract (§2.6), and
the durable run publication's `event_token` (§2.6). **Amended a fourth
time 2026-08-26** (fourth review round): the port's non-fulfilling
publication operation (§2.6 item 2a), the frozen `run-attempt` kind with
the run-shape discriminator and its arm (§2.6 item 4, §3.2), the
closure-to-stored encoder contract with tokenless-legacy scoping (§2.6
item 5), and `O_PATH` classification before any readable open (§3.1).
**Amended a fifth time 2026-08-26** (fifth review round): stored-run
identity is the closure address and the facet is its preimage projection
(§2.6 items 4–5), role-preserving relation projection with the production
dataset edge (§2.6 item 5), the `SHAPES` vocabulary reused verbatim
(§2.2, §2.6), the corrected leaf-symlink classification path (§3.1, §6),
and the executor's two-error contract preserved on `execute` (§2.6
item 2a). **Amended a sixth time 2026-08-26** (sixth review round): the
closure facet carries the projection as v1-canonical text — the
type-preserving wire the address already digests (§2.6 item 5); the
bare-address/typed-ref bridge with field-by-field assignment (§2.6
item 5); and the two accepted stored shapes — the `run` facet preserved
for every reader, the closure facet only on boundary-published runs
(§2.6 item 5). **Amended a seventh time 2026-08-26** (seventh review
round): the closure facet joins semantic-hash coverage (§2.6 item 5),
the production `run` facet frozen as exactly `{}` with both-ways decode
agreement (§2.6 item 5), and the frozen facet key, inner field, and
inverse parse rules (§2.6 item 5). **Amended an eighth time 2026-08-26**
(eighth review round): typed-closure reconstruction before any evidence
read — canonical syntax is not schema validation (§2.6 item 5); the
concrete `v1.decode` contract (§2.6 item 5); and the bounded record
capture ceiling (§3.1). **Amended a ninth time 2026-08-26** (ninth
review round): the typed projection view replaces impossible closure
reconstruction (§2.6 item 5); the ceiling becomes a shared
writer/reader invariant with the encoder's refusal (§3.1, §2.6); and
`CanonicalTextRefused` wraps every re-encoding `IdentityError` as an
`IdentityError` subclass (§2.6 item 5).
**Inherits:** `2026-08-03-tamper-evident-log-design.md` §6 as amended — the
qualification reduction this slice implements at its full stated width: the
matched / unresolvable / attempt-without-recorded-outcome precedence, the
assessment-run shape *(amended 2026-08-11, the act-report design §3 — the
widening to a `run-attempt` act-report)*, the holdings shape *(amended
2026-08-10, the verified-holdings record design §8)*, and the operation
shape *(amended 2026-08-11)*; `2026-08-11-act-report-design.md` §3 (the
operation intent, the completion discipline, T2's malformed-before-
qualification rule); `2026-08-24-world-index-holdings-design.md` §4.3 (the
holdings-shaped interior, written so this slice replaces its interior, not
its callers) and its deferral 5 (this slice's named territory);
`2026-08-22-log-verification-design.md` (the evaluator, the report that
states the qualification deferral, §10 item 1 — the owner row this slice
discharges; cut 8's frozen L7 row is this slice's arm inventory);
`2026-08-02-epistemic-kernel-design.md` §3.2 and §8.7 (G4 narrowed, the
recorded-history completeness table, the G-table's G4 row with its negative
half); adoption-ledger row 5 (the intent-boundary remainder named there).
**Constraints:** no `atoms` change — the intent API is unchanged;
`read_chain`/`inspect_chain` supply the chain the reducer walks, and the
captured-record surface §3.1 defines supplies the published bytes it
decodes — both Science-side captures over existing seams. Frozen cut
bodies stay frozen under their identifiers. Qualification is report-field
status, never the chain verdict (log §6). No compatibility alias for any
retired field. The rules-store dialect's constraints hold as built: pure
source, no science imports, binding by content digest.

## 1. Scope

**Built here (Science only):**

1. **The general qualification reduction** — one pure reducer implementing
   log §6's precedence, parameterized by a closed union of the three
   intent-union shapes (assessment-run, operation, holdings).
   With it, **the run boundary's persistence contract (§2.6)**: the
   boundary is in-memory end to end today, so both run entrypoints gain
   the destination binding, the append-before-any-member-act sequence,
   the port's non-fulfilling publication, the closure-to-stored encoder
   — identity `run:<closure address>`, the closure facet carrying the
   address's preimage as v1-canonical text beside the preserved `run`
   facet — and durable terminal publication with boundary-constructed
   `fulfills`.
2. **The captured-record evidence input** — the evaluator gains an explicit
   published-record surface, captured under the same hold that captures
   `disk`, because a registration exposes paths and opaque states only and
   the reducer must decode what a fulfilling registration published (§3.1).
3. **The verifier's lift** — `LogReport.intents_unevaluated` retires;
   evaluated qualification takes its place under the concrete contract §3.3
   states.
4. **The holdings interior replacement** — the installed holdings rule's
   qualification source is regenerated from the general reducer's holdings
   shape; new content digest, new pinned receipt, callers untouched.
5. **The `science.report.completion` re-base** — the act-report design §4
   reading keeps its designed vocabulary and its signature, and its
   predicate becomes the general reducer's shape predicates (§2.5), so no
   second precedence implementation survives this slice.
6. **G4's closure** — both halves of the kernel G-table row, read through
   the reduction.

**Closed here:** L7 from partial to its stated width — the guarantee
quantifies over all three intent kinds, exactly as cut 8's frozen row
states it; kernel §8.7's fourth recorded-mutation consequence (G4); the
"intent qualification is unevaluated" deferral stated in every report
(log-verification design §10 item 1); adoption-ledger row 5's
intent-boundary remainder.

**Not here, each staying with its named owner:**

1. **Event-level L8** — the presence/exclusion relation across captured
   corpus heads; the log-verification design's own successor work.
2. **The L13 preimage resolver** — waits on the named `atoms` blob-read
   seam; row 5's other named remainder.
3. **The URL retrieval boundary, acquisition orchestration, typed
   retrieval grants, recency as a successor projection rule** — the
   holdings design's deferrals 1–4, untouched.
4. **Out-of-band chronology** (G2a's negative) — stays open exactly as
   banked; nothing here strengthens it.
5. **The derived-answer negatives** — a discarded replay stops being
   consulted; neither §8.7 nor this slice claims to change how belief is
   computed from what remains.

## 2. The reduction module (`science/intents/`)

**2.1 One reducer, one precedence.** The module ships a single pure
function implementing log §6's reduction, and the three shapes are data to
it, never forks of it — the same no-second-taxonomy rule that put
`inspect_chain`'s validation core behind one shared implementation. The
precedence, verbatim from §6:

- any qualifying pointer → **matched**;
- no qualifier, but any pointer whose published record cannot be read →
  qualification **unresolvable** — decayed bytes are not evidence of no
  outcome, and **no** unmatched finding is emitted;
- only when every pointer fully resolves and none qualifies → the
  **attempt-without-recorded-outcome** finding, with each non-qualifying
  `fulfills` named in its own finding.

Two pointer-state rules complete the precedence, both the holdings
interior's as written, now general:

- **An unsettled fulfilling registration is an unresolvable pointer,
  regardless of any bytes captured at its published paths** — settlement
  is never inferred from disk state (log §6's rule for pending, applied
  inside qualification too). The report carries qualification on the
  pending exit like every other well-formed exit, so this rule is
  reachable, and copied-after-apply bytes on a copied root never read as
  a settled fulfillment.
- **A rolled-back registration is fully resolved and never qualifying** —
  it contributes nothing toward unresolvable, and an intent whose only
  pointers rolled back reads attempt-without-recorded-outcome.

Unresolved never collapses into either resolved state — the holdings
slice's rule, now general.

**2.2 The closed shape union.** Exactly three members, closed by
construction. Each shape contributes two pure functions:

- **decode**: entry payload → a validated intent of this shape, `None` for
  another domain, or a raised malformation for a payload that names this
  shape's domain and fails its schema — the holdings decoder's contract,
  now the union's.
- **qualifies**: a committed registration's published record × a decoded
  intent → qualifying or not, at the shape's stated width. The matching
  requirements are frozen text, restated here in full because each carries
  a cut-11 arm:
  - **assessment-run**: a `run` publication of shape `assessment` under
    the intent's `spec_identity` carrying the intent's `event_token` — a
    run under another spec, another token, a run of shape
    `dataset-production` (§2.6 item 4's discriminator), or a publication
    creating no run each
    fails qualification — or an act-report of kind `run-attempt` carrying
    the intent's `event_token`, for a post-intent attempt that minted no
    run. A pre-intent refusal publishes an *unfulfilling* report and
    fulfills nothing.
  - **operation**: for a non-run operation, an act-report of the intent's
    operation kind carrying the intent's `event_token` — a report carrying
    another operation's token, a report of the wrong kind, a run
    publication for a non-run operation, or a registration publishing no
    terminal record each fails qualification; for the production-run
    operation — wire kind `run-attempt`, the correspondence §2.6 item 2
    records — the minted `run` of shape `dataset-production` carrying
    the token or, when none is minted, that act-report; an
    assessment-shaped run never qualifies it.
  - **holdings**: a holdings observation for the intent's canonical
    location carrying the intent's `event_token` — a wrong-location
    observation, a wrong token, or a publication creating no observation
    each fails qualification; the interior as written today, relocated,
    not rewritten.

**2.3 Malformation stays the chain's.** A second committed registration
fulfilling one intent, a `fulfills` naming a missing or non-ancestor
intent — structure, classified before qualification ever runs (T2's rule).
The reducer never re-litigates what the chain already ruled malformed.

**2.4 The dialect constraint is a design input.** The shape functions are
pure and single-module so the rules-store concatenation can consume the
holdings shape unchanged (§4). Purity is not an implementation nicety
here; it is what makes one interior servable to every consumer.

**2.5 The third consumer: `science.report.completion`.** The act-report
design §4 reading already implements this precedence a second time —
`CLOSED` / `INDETERMINATE` / `UNFINISHED` over held records by pointer —
and its current predicate is looser than the frozen width (no
`spec_identity` comparison on a run closure). It is a designed, exported
surface, so it is re-based, not retired: its signature and vocabulary
stay, and its per-pointer judgment becomes a call into the shape
predicates §2.2 defines, with the vocabulary stated as a projection —
`CLOSED` is matched, `INDETERMINATE` is unresolvable (a pointer whose held
value is absent), `UNFINISHED` is every-pointer-resolved-none-qualifying.
The tightening to the frozen width is deliberate and cut-visible: the
wrong-spec run closure that reads `CLOSED` today reads `UNFINISHED` after
the re-base, and a cut-11 arm pins it. After this slice, the reducer's
shape predicates are the only implementation of qualification anywhere in
Science — the verifier, the holdings rule, and `completion` are callers.

**2.6 The run boundary's persistence contract.** The run boundary today
is in-memory end to end: `execute_assessment_run` and
`execute_production_run` receive no destination, and `_execute_run`
returns `RunMinted` carrying a `Registration` value that nothing appends
or publishes durably. The consumer rules banked with the act-report
design — freeze the observer-corpus root, append the intent before any
member act, construct `fulfills` for the closing terminal record — have
no mechanism without a destination, so this slice changes the boundary
contract, for **both** run shapes:

1. **Both entrypoints gain the destination binding** — the
   observer-corpus root's `OperationPort`, a required parameter, no
   defaulted in-memory mode: a run boundary without a destination is the
   pre-slice boundary, and it does not survive this slice.
2. **The sequence is fixed**: freeze the root; durably append the intent
   through the port — the assessment-run wire shape (§3.2) for an
   assessment run, the operation shape for a production run, whose
   operation kind **is frozen as `run-attempt`**: `OPERATION_KINDS` is
   closed and names no `dataset-production`, the built boundary already
   opens `OperationIntent("run-attempt", ...)`, and the log §6 phrase
   "a `dataset-production` operation" **denotes** this wire kind — the
   correspondence is recorded here so no fourth vocabulary entry is
   invented; only then any member act; then publish the closing terminal
   record — the run publication, or the act-report for a post-intent
   attempt that minted no run — through **the same port**, in a
   registration whose `fulfills` the boundary constructs from its own
   appended intent digest, never from a caller-supplied path.

   **2a. The port gains the non-fulfilling publication.** `OperationPort`
   is `append_intent` and `execute_fulfilling` today, so the unfulfilling
   report item 3 requires cannot be spelled through it. The port gains
   `execute(plan)` — a publication fulfilling nothing — implemented on
   the existing executor path, which already accepts `fulfills=None`,
   preserving the executor's **two-error contract as built**: a
   malformed plan refuses as `PlanRefusedError` before any write — the
   lexical validation the executor already runs — and a failure
   executing an encoder-validated plan surfaces as `ExecutionError`.
   Neither is silent, and neither converts into a fulfillment of
   anything.
3. **A pre-intent refusal publishes an unfulfilling report** through
   `execute` and fulfills nothing; a crash before the publication leaves
   no trace — the frozen negative, now constructible.
4. **The durable run publication is the closure itself, and its identity
   is the closure's address.** `RunClosure.address()` digests the
   complete `{recipe, result, occurrence}` projection under
   `science.run.v1`, the boundary's `Registration.pointer` already *is*
   that address, and assessments and production lineage
   (`StampedBasis.run`) already reference it — so the stored record must
   answer to it, not to a second identity. A facet hashing only a
   summary would let two different closures collide under one stored id;
   the projection is what makes the mapping injective. The qualification
   evidence — `shape`, the spec identity, `event_token` — is read from
   **within** the projection (the recipe's shape and spec, the
   occurrence's token); the one reader-facing duplicate is the preserved
   `run` facet's `spec` (item 5), checked for agreement on decode, and
   `shape` is the
   existing closed vocabulary `("assessment", "dataset-production")`
   verbatim — no persistence-only synonym. Both run shapes' intents can
   share one token space, so a token match alone never qualifies: the
   assessment-run predicate reads shape `assessment` plus the intent's
   `spec_identity` plus its token; the operation predicate's minted-run
   alternative reads shape `dataset-production` plus its token; a shape
   mismatch fails qualification (reason class `wrong-shape`, §3.3's
   list). The act-report codec already serializes its full record —
   kind and token included — and is unchanged.
5. **The closure-to-stored encoder is this slice's contract, not an
   incidental**: nothing in the tree bridges a minted `RunClosure` to a
   stored publication, and the one stored constructor takes
   caller-selected slug, title, spec, and relations. The boundary's
   encoder is fixed as:
   - **identity**: the record id is `run:<address>` where the address is
     `RunClosure.address()` — never caller-selected, never a second
     digest; the record lands at the run kind's declared layout path for
     that id. Decode **verifies** the identity: the address is
     recomputed from the captured closure facet, and a mismatch means
     the bytes are not the named publication — the pointer's record
     cannot be read, qualification `unresolvable`, §6's decayed-bytes
     rule;
   - **the bare-address/typed-ref bridge is explicit**: the bare closure
     address and the corpus ref `run:<address>` are two spellings with
     one injective bridge — prepend the kind, strip the kind — and each
     field's spelling is assigned, not inferred. **Bare closure
     identity**: `RunClosure.address()`, `Registration.pointer`,
     `StampedBasis.run`. **Typed corpus references**: the stored record
     id, an assessment facet's `run` field, the `PRODUCED_BY` relation
     target, every relation endpoint. Stored assessments already
     require `run` to be a resolvable corpus ref, and the published
     record is what makes that ref resolve;
   - **facet — two keys, two readers, both shapes accepted**: the
     existing `run` facet stays the readers' facet — `{"spec": <spec>}`
     for an assessment run, exactly as built, and **exactly `{}` for a
     production run**: no built production shape exists today
     (`stored.run_node` requires `spec` unconditionally), so the empty
     mapping is frozen here as the production shape — the facet key
     present, no `spec` key — and its construction is this slice's.
     `run_spec()` and every current reader keep working unchanged on
     old and new records alike (`facet.get("spec")` reads `None` on the
     production shape). Decode agreement runs **both ways**: an
     assessment-shaped closure requires the `run` facet's `spec` equal
     to its own; a production-shaped closure requires the `run` facet
     to carry **no** `spec` key. Beside it, a boundary-published run
     carries the **closure facet**, whose names are frozen: facet key
     **`run-closure`**, one inner field **`projection`**, holding the
     projection as its **v1-canonical text**. The canonical text is the
     type-preserving wire the address already digests: `Decimal` keeps
     its mandatory fractional part (`1` and `Decimal("1.0")` differ;
     `Decimal("0.5")` and `"0.5"` differ), floats are refused at the
     boundary, and `yaml.safe_dump` always represents a string — the
     projection's raw typed values would raise `RepresenterError` on
     `Decimal` or be lossily coerced. The **inverse codec is specified,
     not implied** — `v1` exports `encode` and `digest` only, and
     default JSON parsing would mint the floats the codec refuses — so
     `science.identity.v1` gains the exported inverse with a concrete
     contract: **`decode(data: bytes) -> object`**, joining `__all__`
     beside `encode` and `digest`. Its parse rules: UTF-8 decode, then
     `json.loads` with `parse_int=int`, `parse_float=Decimal`, and
     `parse_constant` refusing (`NaN`, `Infinity`, `-Infinity` never
     parse); validity is **canonical re-encoding equality** —
     `v1.encode` of the parsed value must equal the input
     byte-for-byte, which also refuses non-canonical ordering and
     collapsed duplicate keys. Every failure raises one new named
     refusal, **`CanonicalTextRefused`**, defined as an
     **`IdentityError` subclass** in `science.errors`: malformed
     UTF-8, malformed JSON, and a refused constant directly, and
     **every `IdentityError` the re-encoding itself raises** —
     `NullRefused` on a parsed `null`, `LoneSurrogate`, `KeyCollision`
     on NFC-colliding keys, and their siblings surface *before* any
     equality comparison and are **wrapped**, cause preserved, so a
     `decode` caller catches exactly one refusal type — with the
     failure class in its message; `decode` never returns a partial or
     coerced value. The address is the digest of exactly the input
     bytes under `science.run.v1`.

     **Canonical syntax is not schema validation — and the address
     preimage cannot rebuild the closure.** The projection stores
     `EnvironmentManifest.identity()`, a digest, where `Recipe`
     requires the manifest itself, so reconstruction through the
     constructors is impossible by design and is not claimed. Decode
     instead validates through a **typed projection view**: an
     exact-schema validator over the parsed mapping that mirrors the
     closure invariants at the projection's own level — the complete
     closed key set at every depth with nothing extra, `shape` in
     `SHAPES`, spec presence exactly per shape, input roles in the
     shape's closed role vocabulary, the result pairs' and occurrence
     fields' forms — yielding a frozen view. The view is validated,
     its recomputed address must equal the record id's, and shape,
     spec, and token are read **from the validated view**, never from
     the raw parsed mapping. A canonical object carrying only shape,
     spec, and token digests self-consistently without being a
     projection; the view's schema rejects it. Any view failure means
     the bytes are not the named publication: qualification
     `unresolvable`. The encoder constructs the node through the same
     construction-and-stamp path the stored constructors use;
     `stored.run_node` itself is unchanged for its existing callers;
   - **the closure facet enters semantic-hash coverage**:
     `COVERED_FACETS["run"]` gains `run-closure` beside the `run`
     facet — the dataset entry is the existing multi-facet precedent —
     so adding, removing, or editing a closure facet makes the stored
     semantic stamp stale and the read refuses, instead of the stamp
     staying valid over an uncovered mutation. Legacy records remain
     valid untouched: an absent facet does not enter the coverage
     projection, exactly as the dataset kind's optional facets behave
     today;
   - **legacy records are the absent-closure-facet shape**: an existing
     `stored.run_node` record has no closure facet — it stays readable
     through the `run` facet, resolves as a reference target, undergoes
     no address recomputation, and never qualifies. The tokenless-legacy
     scoping below is this rule; the legacy arm constructs its record
     with the **actual current `stored.run_node`**, not a new
     projection with fields removed;
   - **relations, role-preserving**: each `RecipeInput` projects to the
     predicate its own `role` names — `observes` and `reads` for an
     assessment recipe, `transforms` and `reads` for a production
     recipe, the two closed role vocabularies as built — targeting that
     input's dataset; collapsing every input to `reads` would destroy
     `observes` eligibility and `transforms` lineage. An assessment run
     emits no `produces`; a `dataset-production` run emits **exactly
     one** `produces` edge, to the dataset address `mint_dataset`
     derives from the result manifest's resource declarations — the
     declared outputs themselves are logical-name/digest pairs, not
     dataset references, and never become edges;
   - **plan**: the encoder emits the stored document bytes and the
     `WritePlan` the port executes; no second write path.

   **Legacy stored runs remain readable and never qualify.** The
   closure facet is scoped to boundary-published runs: a stored run
   without one decodes as what it is — a readable publication and a
   resolvable reference target that qualifies nothing — with no
   compatibility shim and no schema rejection of existing records. "No
   qualification pair predates this slice" scopes the *qualification*
   claim only; it was never a license to break the reading of existing
   records.

The kill-between-append-and-start, cross-root-publication, and
no-caller-supplied-`fulfills` arms all read this contract; they were
unconstructible against the in-memory boundary.

## 3. Verifier integration (`science/world/verify.py`)

**3.1 The captured-record evidence input.** A registration entry exposes
its surfaces as `(path, opaque state)` pairs — no bytes — and the
evaluator consults exactly what the caller supplies, searching for
nothing. Qualification must decode what a fulfilling registration
published, so `evaluate_log` gains one explicit input:

- `records: tuple[tuple[str, bytes], ...]` — the published-record
  surface, one `(path, payload)` pair per record file present, captured
  by `_assemble_evaluation_inputs` **under the same hold that captures
  `disk`**, over the published-record namespaces the shapes read (run
  publications, act-reports, `holdings-observation/`). Every evaluator
  caller — audit, arrival, restore — assembles and supplies it; there is
  no defaulted-empty overload, because an accidentally empty surface
  reading as universal unresolvable would be a silent fallback.
- **Capture never follows symlinks, closed by construction, not by
  ordering** — a pre-read `lstat` would leave the classic race: the leaf
  swapped for a symlink between check and read. The capture therefore
  never touches a path twice: it opens a descriptor on the root, descends
  **per component** with `O_DIRECTORY | O_NOFOLLOW` relative to the
  previous descriptor, and **classifies the leaf before any readable
  open exists**: the leaf is first opened `O_PATH | O_NOFOLLOW` — a
  descriptor that can be `fstat`ed but performs no device I/O and
  triggers no open side effect — and only a leaf whose `fstat` shows a
  regular file is then reopened readable **through that same
  descriptor** (the descriptor's own re-open route, no path
  re-traversal), so a fifo, device, or other non-regular leaf is never
  opened for reading at all. The certified tuple is Linux; the
  descriptor re-open route is available there. The two symlink
  positions classify differently and both withhold: a symlink at an
  **intermediate component** fails the `O_DIRECTORY | O_NOFOLLOW` step
  (`ELOOP`, or `ENOTDIR` for a non-directory), while a symlink **at the
  leaf** is opened *as itself* by `O_PATH | O_NOFOLLOW` — that flag
  pair opens the link, it does not error — and is rejected by the
  `fstat` classification showing a symlink, never followed and never
  reopened readable. Either way the payload is withheld and no bytes
  from outside the root ever enter the report; a failed open,
  classification, or read (permission, disappearance) likewise
  withholds the payload. None of these raises out of capture, and none
  is a chain verdict.
- **Capture is bounded, and the bound is a shared writer/reader
  invariant, not a reader-only trap**: the FIFO and device protections
  do not bound a regular file, and an unbounded read under the shared
  hold is a memory-exhaustion and hold-duration lever. The ceiling is
  frozen at **`RECORD_CEILING = 8 MiB` (2^23 bytes)**, one constant
  with two enforcement points. **Reader**: the capture reads
  **ceiling + 1** bytes from the descriptor; a read returning more
  withholds the payload (no partial capture, no truncation ever handed
  to a decoder), landing in the absent-from-`records` rule below.
  **Writer**: the §2.6 encoder refuses, **before any write**, a stored
  document whose encoded bytes exceed the same constant — closure
  members carry no size or cardinality ceiling of their own
  (parameters, inputs, trace), so without this check the official
  boundary could publish a record its own verifier automatically
  withholds. The refusal is a named error on the publication path; no
  partial record lands, and the already-appended intent then reads
  attempt-without-recorded-outcome — the truthful state for an attempt
  whose terminal record could not be published.
- A path a fulfilling registration's final surface names that is **absent
  from `records` — including absent because the no-follow rule withheld
  it — or present and undecodable** → that pointer is a pointer whose
  published record cannot be read: qualification **unresolvable**, no
  unmatched finding — §6's rule, now with its evidence path stated. Undecodable bytes here are a qualification state,
  never a refusal: this surface is captured live evidence, unlike
  `history`, which remains the caller-held historical copy input for L13
  classification, validated and refused on corruption exactly as today.
  The two inputs never mix: `records` answers "what does the chain's own
  root publish now", `history` answers "what did the caller retain".

**3.2 The decode gate — unknown and malformed intent payloads.** The
engine accepts arbitrary intent bytes, and only the holdings shape names
a domain on the wire. The other two are **domainless field shapes**, as
built: the operation payload is the canonical encoding of
`{kind, event_token, actor}` (the import boundary's append), and the
assessment-run payload **is fixed here** as the canonical encoding of the
record type's own fields, `{spec_identity, event_token, actor}` — no
durable append of it exists in the tree today; the boundary contract
that appends it, and publishes what fulfills it, is §2.6's. The
discriminators are exact and disjoint by construction:

- an object carrying `domain` naming `science.holdings-intent.v1` →
  the holdings shape's schema;
- an object with **exactly** the field set `{kind, event_token, actor}`
  and `kind` in the closed `OPERATION_KINDS` vocabulary → the operation
  shape's schema;
- an object with **exactly** the field set
  `{spec_identity, event_token, actor}` → the assessment-run shape's
  schema (`spec_identity` presence versus `kind` presence is what makes
  the two domainless shapes unconfusable);
- a discriminator match whose value then fails the shape's schema (a
  type violation, an empty required string) → status **`unrecognized`**,
  with one `intent-payload-malformed` finding (severity `error`, `ref`
  the intent digest) — a cooperative boundary wrote garbage under a
  claimed shape, which is louder than a foreign payload but still
  **never the chain verdict**: a rewritten payload on a tampered chain
  already broke linkage and answered `malformed` at structure, so what
  reaches this gate on a well-formed chain was written this way;
- everything else — bytes that are not canonical JSON, a non-object, an
  object fitting no discriminator (`{}`, a foreign `domain`, an unknown
  field set, an out-of-vocabulary `kind`) → status **`unrecognized`**,
  with one `intent-domain-unrecognized` finding (severity `warning`,
  `ref` the intent digest, `detail` the foreign domain,
  `domainless-unrecognized` for a parseable object fitting no shape, or
  `undecodable`); the reduction is not entered, and no fulfillment
  judgment is made or implied.

The gate is total: every `IntentEntryView` lands in exactly one bullet.

**3.3 The report contract.** `LogReport.intents_unevaluated` retires, and
the report gains exactly one field in its place:

```python
@sealed
@final
@dataclass(frozen=True, slots=True)
class IntentQualification:
    digest: str          # the intent entry's digest
    shape: Literal["assessment-run", "operation", "holdings"] | None
    status: Literal[
        "matched",
        "unresolvable",
        "attempt-without-recorded-outcome",
        "unrecognized",
    ]
    fulfilled_by: str | None  # the qualifying registration's digest
```

- `LogReport.qualification: tuple[IntentQualification, ...]` — one row
  per `IntentEntryView`, in chain order by entry position, always a
  total accounting of the inventory: no intent is silently dropped.
- `shape` is `None` exactly when `status` is `unrecognized`, and named
  otherwise. `fulfilled_by` is set exactly when `status` is `matched`,
  and `None` otherwise.
- `status` is `attempt-without-recorded-outcome` exactly when §6's
  finding of that name is emitted for that intent.
- Carriage keeps the inventory's rules: the field is populated even on a
  genesis-form `malformed` exit — a chain the engine linearized has an
  intent inventory whatever its genesis payload says — and empty on the
  `MalformedView` exit, where there are no entries to inventory.
- Finding codes, under the existing Science envelope
  (`Finding(severity, code, ref, detail, message)`):
  `intent-attempt-without-recorded-outcome` (severity `warning`, `ref`
  the intent digest); `intent-fulfillment-non-qualifying` (severity
  `warning`, `ref` the non-qualifying registration's digest, `detail`
  naming the intent digest and the reason class — wrong-purpose,
  wrong-spec, wrong-token, wrong-kind, wrong-shape, wrong-location,
  no-record); and §3.2's two gate codes.
- **Placement is pinned, not "existing discipline"** — the evaluator
  appends findings by phase and tests observe positions, so the rule is
  stated: qualification findings are appended **last**, after every
  finding the exit's own phase produced, on every exit that carries
  `qualification`. Within the block, intents in inventory (chain) order;
  per intent, the gate finding (§3.2), or the
  attempt-without-recorded-outcome finding followed by that intent's
  `intent-fulfillment-non-qualifying` findings in registration chain
  order. A `matched` or `unresolvable` intent emits no finding — the
  frozen text ties the non-qualifying findings to the attempt case, and
  unresolvable emits nothing by rule. Nothing about qualification
  reorders any other phase's findings.

Qualification remains **report-field status, never the chain verdict**:
no qualification state changes `outcome`, and no outcome suppresses
qualification's findings. Callers and tests naming the retired field
update in the same task; no alias, no deprecation shim.

## 4. The holdings interior replacement (`science/holdings/`)

The installed rule's qualification source (`qualify.py`, concatenated into
the `rules_v1` fixture) is regenerated from the general reducer's holdings
shape, so the rule and the verifier share one interior. The rule's
callers — the capture split, the active-set reducer, the three blocking
classes, the coverage projection, the adapter, the receipt *machinery* —
are untouched: holdings §4.3's contract, "replaces its interior, not its
callers," discharged as written. What changes is exactly:

1. the rule source's qualification section, now generated from the shared
   shape rather than hand-maintained beside it;
2. the rule's content digest, and therefore the pinned receipt — a new
   receipt is minted under the existing receipt discipline, and the old
   one remains what it always was, a value with a content identity;
3. nothing else. Blocking semantics, per-location precedence (§5.1's
   pinned capture precedence), and the reducer's fixture binding are
   byte-for-byte concerns of the regeneration, certified by arms that run
   the holdings qualification through both consumers and compare.

## 5. G4's closure

**The positive half.** A **recorded** failed replay attempt cannot be
silently orphaned. Through the reduction: an intent whose fulfillment
never qualifies — a kill between the durable intent append and execution
start, a wrong-purpose committed transaction, a publication creating no
run — reads **attempt-without-recorded-outcome** in every report over the
chain, and discarding the failed *fulfillment* while the intent survives
moves qualification, never erases the attempt. The kernel G-table row's
refusal arm — an unreferenced successor to a recorded failure — is read
where the boundary already refuses it.

**The negative half, pinning the limit.** Discard the failed attempt
*entirely* — no intent appended, nothing durable — and confirm the system
**cannot** detect it: crash, cancellation, and discarded failure are
indistinguishable by construction. The arm asserts the limit so no reader
over-reads G4, exactly as G8's negative pins its own. Detection stays
quantified over surviving observers throughout — destruction of a root
together with every anchor holding it is not detectable from nothing.

G4 closes at this slice's discharge; the G2a-ordering row is untouched.

## 6. Conformance cut 11

The cut document (`conformance-cut-11`, dated at drafting) freezes before
any implementation task. Its selection is drawn from frozen text, not written
fresh:

- **cut 8's L7 row** — the qualification arms at all three widths:
  no-pointers and all-resolved-non-qualifying; the mutated fulfillment
  family per shape (wrong purpose, wrong spec, wrong token, no record
  created; wrong location for holdings; wrong kind and wrong-operation
  token for operation); unresolvable published bytes with no unmatched
  finding; kill-between-append-and-start per shape; the
  root-other-than-the-intent's refusal; no caller-supplied `fulfills`
  path at the boundary; and the row's negative. The two chain-structural
  L7 units stay cut 8's — certified there, not re-read.
- **the kernel G-table G4 row** — both halves (§5).
- **the decode gate (§3.2)** — a foreign-domain intent reads
  `unrecognized` with its `intent-domain-unrecognized` finding and enters
  no reduction; a discriminator-matched schema-invalid payload reads
  `unrecognized` with `intent-payload-malformed`; a parseable object
  fitting no shape (`{}`) reads `unrecognized` with
  `domainless-unrecognized` detail; none moves the chain verdict, and
  every row appears in `qualification` — the total-accounting assertion.
- **the evidence path (§3.1)** — a fulfilling registration whose named
  record path is absent from the captured `records` surface, and one
  whose captured bytes do not decode, each read qualification
  `unresolvable` with no unmatched finding; a record path replaced by a
  **symlink out of the root** reads `unresolvable` with no bytes from
  outside the root anywhere in the report — and the arm runs the **swap
  race**, not only the static link: the leaf becomes a symlink between
  enumeration and read (constructed deterministically at the capture
  seam), and the fd-anchored capture classifies the opened `O_PATH`
  descriptor as a symlink and withholds the payload — never followed,
  never outside bytes; `history` remains L13's and is untouched by any
  of these.
- **the run boundary's persistence (§2.6)** — the published run's
  captured bytes round-trip: append, execute, publish, capture, decode,
  match — the projection's shape, token, and spec establish the
  qualifying pair, the recomputed address agrees with the record id,
  and the role-preserving relations and the production `produces` edge
  are read back exactly; the **closure-member mutation arm**: mutate
  any single member of the captured projection — a recipe field, a
  result pair, an occurrence field — and the recomputed address
  diverges from the id, the bytes are not the named publication, and
  qualification reads `unresolvable`, never a silent match; the
  **incomplete-closure arm**: a canonical, self-addressed object
  carrying only shape, spec, and token — a valid `science.run.v1`
  digest preimage that is not a projection — fails the typed projection
  view's schema and reads `unresolvable`, never a match on its matching
  fields; the
  **capture-ceiling arms, both sides of the shared invariant**: a
  tampered regular file at a record path exceeding `RECORD_CEILING` is
  withheld by the bounded read — qualification `unresolvable`, capture
  completes, and no ceiling-plus-one buffer is ever handed to a
  decoder — while the boundary-side arm drives the encoder past the
  same constant and asserts the pre-write refusal: the official
  boundary **cannot** publish a record its verifier would withhold,
  and the appended intent reads attempt-without-recorded-outcome; the
  **wrong-run-shape arm**: an assessment-shaped run
  carrying a production intent's token fails qualification with reason
  `wrong-shape`, and conversely; the **unfulfilling-publication arm**:
  a pre-intent refusal's report lands through `execute`, fulfills
  nothing, and `execute` keeps the executor's two-error contract — a
  malformed plan refuses as `PlanRefusedError` before any write, an
  execution failure surfaces as `ExecutionError`, neither a
  fulfillment; the **type-preserving wire arms**: a recipe parameter of
  `Decimal("0.5")` round-trips distinctly from `"0.5"`, and `1`
  distinctly from `Decimal("1.0")` — publish, capture, decode,
  recompute — with the address agreeing in each case and the four never
  colliding; the **coverage arm**: mutate the published record's
  `run-closure` facet in place and the semantic stamp is stale — the
  read refuses under the existing semantic-hash rule — while an
  untouched legacy record's stamp stays valid, absent facets never
  entering the projection; the **shape-agreement arms, both ways**: an
  assessment publication whose `run` facet `spec` disagrees with its
  closure's refuses decode, and a production publication whose `run`
  facet carries any `spec` key refuses decode — the frozen shapes are
  `{"spec": <spec>}` and exactly `{}`; the
  **reference-resolution arm**: an assessment referencing
  the published run and a `StampedBasis.run` carrying its bare address
  both resolve, through the stated bridge, to exactly the published
  record; the **legacy arm**: a record built by the *actual current*
  `stored.run_node` — not a stripped projection — reads through the
  `run` facet, resolves as a reference target, and never qualifies, with
  no schema rejection; the kill-between-append-and-start, cross-root,
  and pre-intent-refusal arms run against the durable boundary, per
  shape.
- **capture classification (§3.1)** — a non-regular leaf (a fifo) at a
  record path is classified through the `O_PATH` descriptor and never
  opened readable: capture completes without blocking, the payload is
  withheld, qualification reads `unresolvable`.
- **pending fulfillment (§2.1)** — an unsettled fulfilling registration
  with its published bytes present on disk reads qualification
  `unresolvable`, never `matched`: settlement is never inferred from
  disk state, asserted on the pending exit where qualification is
  carried.
- **the completion re-base (§2.5)** — the wrong-spec run closure that
  reads `CLOSED` today reads `UNFINISHED` after the re-base; and
  **consumer agreement at three sites**: the verifier, the regenerated
  holdings rule, and `completion` answer identically over the same
  evidence for every shape each consumer reads (§4 item 3, widened).
- **L7u1's partial remainder** — re-examined at the new width; selected
  if constructible, its partiality re-stated with the same reason if not.

Classification follows the any-unrun-arm rule: any arm not run keeps its
row partial, and no argument for why an arm shouldn't count earns a
"full." Discharge is on the certified volume, through the certified
acceptance-runner cadence, with pytest summary lines quoted in the
results record and the execution rulings ledger committed to a tracked
path before any worktree removal.

## 7. What this changes elsewhere (applied at banking)

- **Kernel §8.7** — the fourth recorded-mutation consequence closes; the
  status paragraph gains G4's dated closure with the negative's pin
  restated.
- **Adoption-ledger row 5** — the intent-boundary remainder discharges;
  the row's remainder text shrinks to event-level L8 and the L13
  preimage resolver.
- **Adoption-ledger design-track item 6** — same shrink.
- **Log-verification design §10 item 1** — closed with a dated note, the
  slice-3 precedent for items 2, 3 and 6.
- **`2026-08-22-log-verification-design.md` deferral texts and the
  holdings design's deferral 5** — dated closure notes; frozen cut bodies
  untouched.
- **README/guide live claims** — the stale-claim grep
  (`intent qualification|intents_unevaluated|G4`) runs at banking; live
  text saying qualification is unevaluated updates, frozen records stay.

## 8. Choreography (order of work)

1. This spec's review closes.
2. The conformance cut 11 document is drafted from the frozen sources §6
   names and reviewed by a second reader.
3. **Cut 11 freezes** — before any implementation task.
4. Implementation on `design/intent-boundary`, TDD throughout, the
   holdings slice's per-task review cadence: the reduction module, the
   verifier lift, the interior replacement, G4's arms — each task
   red-then-green with its review findings closed by amendment.
5. Certified discharge: the acceptance runner on the certified volume;
   results record and rulings ledger committed to tracked paths.
6. Banking: §7's changes, status header here, promotion to
   `docs/designs/`; the `--no-ff` merge is the human partner's act.

Any gap discovered mid-task between a frozen arm and built boundary
behavior (a refusal the boundary does not yet make, a record it does not
yet publish) upgrades scope by a dated amendment here before the task
proceeds — never a silent narrowing of the arm.
