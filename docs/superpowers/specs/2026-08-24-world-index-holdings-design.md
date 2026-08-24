# Verified holdings, store-side — design (world-index slice 5)

**Date:** 2026-08-24
**Status:** draft spec — promotes to
`docs/designs/2026-08-24-world-index-holdings-design.md` at banking. Nothing
here is implemented; no conformance arm is claimed. The conformance cut this
spec anticipates (cut 10) freezes after this spec's review and before any
implementation task.
**Inherits:** `2026-08-10-verified-holdings-record-design.md` whole — the
banked authority this slice implements; its §2 (the canonical facet and the
store-identity/lifecycle contract), §3 (the two act shapes, the dereference
boundary, the intent discipline), §4 (supersession, the three blocking
classes), §5 (the coverage projection, the adapter, the receipt), §6 (H1–H4),
§7 item 7 (the atoms bill this slice pays down);
`2026-08-23-world-index-root-lifecycle-design.md` (the fail-closed writer
state, store roots, serviceability, `restore_root` — the substrate built for
exactly these reads); `2026-08-03-tamper-evident-log-design.md` as amended
(the holdings intent in the intent union, the §6 qualification reduction's
holdings instantiation, `fulfills` construction, the §9 ownership split);
`2026-08-22-log-verification-design.md` (the evaluator and observer-set
discipline the restore gate already consumes); conformance cut 9's results
(`../../plans/2026-08-23-conformance-cut-9-results.md` §1.1 — the two
partial units L10u8 and L10u10 whose dereference clauses this slice closes);
the admission ramp §4/§6 and conformance cut 2 (the `admission_state` seam,
consumed unchanged); adoption-ledger rows 4 and 5.
**Constraints:** the frozen tables stay frozen under their identifiers; this
slice adds no table — H1–H4 exist, banked 2026-08-10, and become selectable.
No timestamp enters any derivation; `observed_at` is data. No new attester
class is privileged.

## 1. Scope

**Built here (atoms, behind its own design gate — choreography §8):** the
coordinator **dereference-and-hash read command** and the **post-state
evidence return** on `run_transaction` (§2.2 — the establishment already
lives in the engine's commit verification; the ledger's "mutator
post-state capture" clause is discharged by returning it) —
adoption-ledger row 4's named holdings remainder, and nothing else of
row 4.

**Built here (Science, `science/holdings/`):** the `holdings-observation`
record kind under `science.holdings-observation.v1` with the **store locator
only**; the two store act shapes (pure dereference; managed write, delete,
and move) under the intent discipline; the **holdings-scoped** qualification
reduction; the active-set reducer with the three blocking classes; the
coverage projection with its derivation receipt; and the dataset-scoped
adapter into cut 2's `admission_state`.

**Closed here:** cut 9's two partial units — L10u8 and L10u10's
*unresolvable-for-holdings-reads* and *dereference-minting* clauses — and
adoption-ledger row 4's holdings-prerequisite remainder.

**Not here, each a named deferral:**

1. **The `url` locator arm and the whole URL retrieval boundary** (holdings
   design §2's url canonicalization profile, §3's network discipline).
   Constructing a `url` locator refuses with a named error; no
   canonicalization code ships untested by any act. The deferral is declared
   in cut 10's labeled set.
2. **Acquisition orchestration** — the act-report design reads act termini;
   no acquisition-level state is built here.
3. **Typed retrieval grants** (holdings design §7 item 8).
4. **Recency as a successor projection rule** (§7 item 1) — the reducer this
   slice ships is the rule such a successor would replace, which is why its
   binding is fixture-bound and receipt-pinned.
5. **The intent-boundary slice's territory**: L7's general reduction, G4's
   closure, and every boundary-side arm. This slice instantiates
   qualification for the holdings shape only (§4 below).
6. **Event-level L8 and the L13 preimage resolver** — row 5's other named
   owners, untouched.
7. **Whether the derivation receipt joins the belief-input closure** (§7
   item 3) — stays with the persistence-cut ruling; this slice only keeps
   the receipt a value with a content identity, ready either way.

## 2. The atoms seam (row 4's remainder)

Both commands are designed in an **atoms-local design document behind that
repository's own gate**, approved before implementation, merged into the
atoms `main` and **pushed before this slice's discharge** — the
lifecycle-commands precedent, and the same disclosure rule: the results
record quotes the pushed head. The exact signatures are that design's to
finalize; the contract Science consumes is:

**2.1 The read command — dereference-and-hash under the private lease.**
Over `(backend, project_root, metadata_root, storage, relative_path)`,
answer `found(<algorithm>:<lowercase hex>)` or `absent`.

- **Lifecycle-honoring:** a writable root reads under the recovery lease; a
  read-only *serviceable* root reads quiescently under the held lock — the
  `read_chain` non-writable arm's discipline, including its incomplete-
  operation and live-transaction refusals. Metadata-less, read-only
  unserviceable, binding-mismatched, and exact-v2 roots **refuse**. That
  refusal is the mechanism behind L10u8/u10's closure: an unadmitted copy's
  dereference is an inconclusive attempt at the Science boundary, minting
  nothing — in particular never an `absent` for a path the copy failed to
  carry.
- **Path preflight, then descriptor-anchored traversal:** the relative path
  is validated under the existing project-relative grammar (refuse, never
  normalize), and the read then **reuses the engine's guarded capture
  traversal** — components resolved child-by-child from the root
  descriptor, never re-walked from a path string — so no post-preflight
  ancestor swap by a raw writer can redirect the read (a string re-walk
  would be a check/use race the preflight alone cannot close). A path whose
  ancestor is a file or a symlink reads **`absent`**, exactly as the
  capture model already answers for the registered surface. A final entry
  observed as a symlink or a directory **refuses as established-neither** —
  never followed, never hashed, never `absent`: a symlink's target bytes
  live at a different canonical location, and hashing through one would
  attest bytes the location does not name.
- **Refusals are structured and phase-bearing.** The command's refusal
  carries which phase refused: **no read attempted** (lifecycle refusal,
  path-preflight refusal, boundary unobtainable) versus **read attempted
  and established neither** (an I/O failure mid-read, a final non-regular
  entry). Science maps the first to `byte-locator-untested` and the second
  to `retrieval-failed` (§4.1) — from the structured refusal, never
  inferred from an exception type or message, which is not a stable
  contract.
- **The boundary is the claim:** dereference start through hash completion
  under the one lease, so `found` digests a stable cooperative state and
  `absent` is a completed enumeration answer. Cooperative-write bound, no
  further — a raw writer holds no lease (§4's out-of-band bound, inherited).
- **A5b preserved:** the command acts on the consumer's behalf; no `Lease`
  is returned.
- The digest is algorithm-qualified in the canonical spelling; sha256 is the
  algorithm shipped, and the accepted set stays the profile's residue.

**2.2 Post-state evidence from `run_transaction`.** *Corrected at the
atoms design gate (2026-08-24): the first draft specified an opt-in
per-effect capture, believing establishment was new work. Reading the
engine found it already built, stronger than asked:* the spec compiler's
coverage phase requires the transaction's **final surface to name every
path an effect mutates** with its timeline's last post-state, and commit
verification **observes every final-surface path on disk under the held
lease** — content hash streamed from a pinned descriptor — and **refuses
commit on any mismatch**. A committed registration's final rows are
therefore already verified reopen-and-hash evidence, carried durably in
the chain entry. The atoms delta is a **return channel**:
`TransactionOutcome` gains `final_states`, the committed registration's
final `(path, PathState)` rows, typed.

The evidence mapping stands as first drafted, now read from those rows:

| act | evidence in `final_states` |
|---|---|
| write | the destination's final `FileState` — its content hash observed on disk, **never the source stream's digest** (H1, first arm) |
| delete | the path's final `AbsentState` — established by the commit observation, never inferred from the return (H1, third arm) |
| move | the **dual-location result**: the source's `AbsentState` and the destination's `FileState`, both rows from the one transaction |

Consequences, replacing the first draft's pinned semantics:

- **No selection parameter.** Every mutated path is present; the consumer
  ignores rows it does not need, and there is nothing to opt into or get
  wrong. `CreateDirectory` needs no special case — its row is a
  `DirectoryState` no holdings act reads.
- **Establishment precedes commit.** The observation happens at commit
  verification, under the lease, before release — and a mutation whose
  observed post-state does not match **never commits** (`EffectMismatch`).
  The first draft's committed-but-uncaptured disposition is deleted as
  unconstructible: there is no committed transaction whose post-state went
  unobserved. A refused or failed transaction raises, no observation is
  minted, the intent stays unmatched, the location reads unsettled, and a
  later re-check repairs it (§4).
- **One authority, two access paths.** `final_states` decodes the same
  rows the registration entry carries; a consumer can re-derive them via
  `read_chain`, and the return is a convenience, never a second source.

Atoms returns evidence, never observations; the two-intent move
orchestration over the dual result is the Science boundary's (§4 below).
Store payload mutations flow as ordinary registered transactions against
the store root, so the writability gate, the pending gate, and `fulfills`
admission apply unchanged — the return is additive, and no existing atoms
contract moves.

## 3. The record kind (`science/holdings/records.py`)

The banked §2 facet, made executable. Construction enforces every
constraint; a violated one refuses (`MalformedRecord` family), never
repairs.

- **Fields:** `kind`, `location`, `outcome`, `expected`, `observer`,
  `instrument`, `event_token`, `observed_at`, `supersedes`, exactly as
  banked. `observed_at` in the one canonical `YYYY-MM-DDTHH:MM:SSZ`
  encoding, recorded as data, read by nothing.
- **Digest canonicalization:** `<algorithm>:<lowercase hex>`, lowercase
  algorithm identifier, exact width where the algorithm is known (64 for
  sha256); unqualified and non-canonical spellings refused. The record stays
  **algorithm-generic**: an unknown algorithm's width is unenforceable and
  the accepted set is the profile's, not this record's.
- **`expected`:** optional; with a `found` outcome it must share the found
  digest's algorithm or construction refuses (the same-algorithm rule that
  makes every derivation-time mismatch commensurable).
- **The locator union ships with one arm:** `store(store_id, relative_path)`
  — the 32-hex opaque store identity, the path validated under the atoms
  project-relative grammar, **refuse-never-normalize**, so the canonical
  form is the accepted spelling and equality is byte equality. A `url`
  construction refuses with a named deferral error; the refusal is a
  declared arm of cut 10's labeled set, not silence.
- **Per-location supersession by construction:** the constructor takes the
  predecessor **records** being superseded — the acts have them in hand,
  having resolved the heads they replace — validates every one names the
  same canonical location, and encodes only their references, deduplicated
  and sorted by canonical reference bytes. The record layer resolves nothing
  ambiently.
- **Identity:** the facet's content identity under
  **`science.holdings-observation.v1`** through `science.identity.v1`'s
  `v1.digest`, every field participating — the minted `event_token` is what
  keeps two identical findings distinct (never the clock).
- **Stored representation:** a governed world-record kind in the observer's
  corpus, joining the existing stored codec/decode surface with
  semantic-hash stamping like every other kind. Authored **only** through
  the acts boundary — G9 extended: no API accepts an authored observation
  (H1's territory). It joins **no epoch map**: the coverage projection, not
  the world index, is its read surface this slice.

## 4. The acts boundary (`science/holdings/boundary.py`)

The orchestration across the two roots — the store root read or mutated, the
observer's corpus root carrying intent and observation. It consumes the
atoms intent API **as built**; no log machinery changes.

**4.1 The pure dereference (audit / re-check).**

1. **Intent before read:** append a holdings intent in the observer's
   corpus root — payload: canonical location, act kind (`re-check`),
   boundary-minted `event_token`, actor. Chain position, never a clock, is
   what orders the look after any damaged attempt.
2. Resolve the store identity to the supplied root; the genesis must carry
   the `store_id` (`StoreIdMismatch` otherwise); then the atoms read command
   answers under §2.1's boundary.
3. **A refusal is an inconclusive attempt:** unserviceable, metadata-less,
   binding-mismatched, preflight-refused, boundary-unobtainable — reported
   in the ramp's vocabulary, **mapped from the read command's structured
   refusal phase (§2.1)**: no-read-attempted → `byte-locator-untested`,
   attempted-and-established-neither → `retrieval-failed` — never inferred
   from an exception type or message. **Nothing minted**, the prior
   observation left standing. The unmatched re-check intent reads as a look
   that never became a finding — the act's failure, not the record's;
   nothing unsettled (the act-kind distinction, H4).
4. **An established finding publishes or the act fails:** the observation is
   constructed superseding the standing heads **the caller resolved and
   supplied** (the repair act replaces every head it was shown), and
   published by a registered, committed transaction whose `fulfills` the
   boundary constructs **from its own intent** — no caller-selected
   `fulfills`. Established-but-unrecordable fails loudly; no transient
   report with a dropped record (H4, first arm).

**4.2 The managed mutations (write / delete / move).**

1. **One intent per canonical location, appended before mutating** — the
   move appends two, each with its own minted token; one intent cannot name
   two locations.
2. The store-root transaction runs through atoms; §2.2's returned
   `final_states` rows are the **only** evidence the observation records.
3. Each observation publishes by its own registered transaction fulfilling
   its own intent — the move's **two registrations**, so the crash cases
   split per location. The intents append one at a time (the atoms intent
   API's single append, unchanged), so the windows are: a crash **between
   the two appends** leaves one intent unmatched — its location unsettled —
   while the other location carries no intent and saw no mutation, so there
   is nothing to mark and nothing changed; a crash **after both appends and
   before the mutation** leaves both intents unmatched and both locations
   unsettled; a crash **between the publications** leaves one location
   settled by its observation and the other unsettled. Per-location
   blocking needs nothing new for any of the three.

**4.3 The holdings-scoped qualification reduction.** A **qualifying
fulfillment** of a holdings intent is a committed registration whose
published record is a holdings observation for the intent's canonical
location carrying the intent's `event_token`. A non-qualifying pointer never
matches; qualification lands unresolved **only** where §5.1's pinned
precedence says the captured coverage cannot answer — a missing record at a
holdings-observation file row, or an unsettled registration — and
**unresolved blocks as itself, never collapsed** into either resolved state. This is the log §6
reduction instantiated for the holdings shape only; L7's general reduction,
G4's closure, and the boundary-side arms remain the intent-boundary slice's,
and this slice's reduction is written so that slice replaces its interior,
not its callers.

## 5. Reducer, projection, adapter, receipt

**5.1 Capture, then the pure reducer — the split the rules-store ABI
forces, drawn where the binding demands.** The rules store's ABI is
deliberately small: an installed rule receives **one immutable projection
value and returns one projection value** — no world, corpus, path, or
executor is reachable from it. But the banked authority binds
**enumeration into the fixture-bound reducer** (§5 there: "steps 1 and 2
whole"), and a capture that *selected* holdings material would escape that
binding — a buggy selective capture could omit evidence, sign the output
digests, and later validate against the same unbound selection, H3's
second arm reopened one layer down. So the line is drawn at **mechanism
versus judgment**: capture is a mechanical transporter with no
holdings-specific choice in it, and every act of selection, decoding,
association, and classification is the rule's.

**The capture orchestration (`science/holdings/project.py`, impure,
mechanical).** Under cut 7's coherent-capture machinery, per covered
corpus — named by stable identity; a corpus whose state or validated chain
cannot be produced **refuses the whole projection** — capture, coherently
with that corpus's state:

- **every stored record's canonical node projection**, no kind filter —
  the node's stable uid and its §11.1 canonical text (`to_canonical_json`,
  the same per-node projection the corpus-state identity digests); and
- **the validated chain whole**, genesis first, in chain order — each
  entry's digest and its own fields verbatim, the settlement entries
  included, so the rule can **require** commitment rather than assume it.

**Raw storage bytes are deliberately not carried.** The corpus-state
identity digests canonical node content, so two lexically different
documents can share one state identity — a rule handed storage bytes could
distinguish inputs the receipt names as identical, and "the receipt's
inputs determine the value" would be false. The canonical projection is
exactly what the state identity binds.

**A record that cannot be read or generically decoded to its canonical
projection refuses the whole capture.** This is the same condition under
which the corpus-state identity itself is unmintable
(`CorpusStateMalformed`), so a state a receipt can name always has a
capturable projection. No unreadable variant exists in the schema, and no
platform error text enters it — refusal diagnostics live outside the
projection.

**The coverage projection is a closed schema, not "a value":**

```
CoverageProjection
  corpora: one entry per covered corpus, sorted by corpus_id bytes
    corpus_id:    str — the manifest's opaque id
    corpus_state: str — the corpus-state identity
    chain_head:   str — the 64-hex head digest of the captured chain
    records: sorted by uid bytes
      uid:        str — the node's stable uid
      canonical:  str — the node's §11.1 canonical projection text
    chain: chain order, genesis first
      digest:     str — the entry's 64-hex digest
      entry:      genesis(payload, baseline)
                  | intent(payload)
                  | registered(txid, intent_digest, consumer_tag,
                               fulfills?, initial, final)
                  | settled(txid, registration,
                            outcome: committed | rolled-back)
```

The field names, member order, and variant tags above are the schema; the
fixture serialization encodes payload `bytes` as lowercase hex and an
absent `fulfills` by omission. One capture, one byte form — the exact
value the receipt's inputs determine, and the exact value supplied to the
rule's fixtures.

**The active-set reducer (`science/holdings/reduce.py`, pure,
fixture-bound)** — the rule a recency successor would one day replace: the
function from one coverage projection to the pair (active set, blocked
set). The **whole of banked §5 steps 1–2 runs inside it**: decode the
stored documents and **select** the holdings observations; parse the
intent payloads and select the holdings intents; **associate** each intent
with the registrations whose `fulfills` names it; **qualify** — a
qualifying fulfillment is a **committed** registration (its settled
entry's outcome read from the carried chain, never assumed) whose
published record is a holdings observation for the intent's canonical
location carrying its `event_token`, the record found by deriving each
carried record's stored path **inside the rule** — the layout's
deterministic id→path derivation over the record's own canonical
projection, no path carried — and matching it against the registration's
final path-state rows; then the walk, coalescing, blocking, and
cycle-refusal below.

- **Qualification is a pinned three-step precedence**, applied per intent
  over its registrations' final path-state rows — matched, then
  unresolved, then non-qualifying, the first step that answers winning:
  1. **matched** — some committed registration has a final **file** row
     whose path derives from a captured record that is a holdings
     observation for the intent's canonical location carrying its
     `event_token`;
  2. otherwise **unresolved — as itself** — some committed registration
     has a final **file** row at a path in the holdings-observation
     layout (the layout's kind-first derivation makes this decidable from
     the path alone) with **no captured record deriving to it**: the
     publication may have existed and be gone from this state, which
     proves nothing either way and blocks rather than settles (H2's
     fourth arm keeps its soft-collapse sabotage);
  3. otherwise **non-qualifying**, contributing to **unmatched** — a
     final absent, directory, or symlink row published no record, and a
     final file outside the holdings-observation layout could never be
     the required observation: each fully resolved, never unresolved.
- **Settlement gates the rows.** A **rolled-back** registration is fully
  resolved and non-qualifying — its settlement answered, and its rows are
  not consulted. A registration with **no settlement entry** in the
  captured chain is **unresolved as itself**: the transaction's outcome is
  unestablished, which is exactly the proves-nothing state, never a
  resolved one.
- Per-location `supersedes` DAG walk from heads; acyclicity **checked on
  every walk** (ρA9's discipline) — a presented cycle refuses the whole
  projection; a dangling predecessor outside coverage is a head with an
  unseen tail, not an error.
- Classification: agreeing heads coalesce in classification only, **every
  head retained**; disagreeing outcomes → `contested`; an algorithm-mixed
  `found` pair → `incommensurable`; an unmatched-or-unresolved **mutating**
  intent with no later fulfilled re-check intent in that corpus's chain →
  `unsettled`. One location can carry several reasons at once.
- **Outputs:** the active set and the blocked set, sharing the one member
  shape — the head join projection: head reference, canonical location,
  outcome, `expected`, and every reached predecessor's reference, outcome,
  and `expected`, deduplicated by reference — under the banked §4 canonical
  encoding at every level (active set by head reference bytes; blocked
  entries by location bytes; reasons as fixed enum forms, deduplicated and
  sorted; projections by head reference bytes; history rows deduplicated
  then sorted). One reduction, one byte form under the receipt.

**5.2 The receipt.** Cut 7's receipt identity formula digests exactly
`{kind, subject, corpus_states, rule_identity, implementation_identity}` —
it has **no chain-heads member**, so reusing it would let two reductions
under different heads (and therefore different unsettled sets) share one
receipt identity: H3's third arm defeated at the identity layer. The
holdings receipt is therefore its **own closed facet under a new domain,
`science.holdings-receipt.v1`** — deliberately not a member of the epoch
carrier, which it never joins — with the closed member set:

- `kind` — `holdings-reduction`;
- `coverage` — the deduplicated triples (corpus id, corpus-state identity,
  chain head), sorted by corpus-id bytes;
- `rule_identity` and `implementation_identity` — the rules-store binding
  pair, exactly as cut 7 defines them;
- `active_set_digest` and `blocked_set_digest` — sha256 over each output's
  canonical byte encoding.

Identity digests **every member** (the holdings-observation facet's own
discipline). A receipt naming corpora rather than states, or a bare version
string, is `malformed`. Validation is re-running: resolve the binding,
re-capture the named states under the named heads, re-reduce — `validated`
when both output digests reproduce byte-for-byte, `refuted` when not,
`unresolvable` when a named corpus state, chain head, or implementation
cannot be resolved here (a computability state, never epistemic),
`malformed` when it could never be checked. The receipt's claim **ends at
the reducer's outputs**; the adapter sits outside the binding, exactly as
banked and for the banked reason.

**5.3 The dataset-scoped adapter (`science/holdings/adapter.py`).** Inputs:
the dataset declarations plus the reducer's two receipt-committed outputs —
never a re-enumeration beside the receipt. The three joins — by outcome, by
expectation, by history (read from the carried join projections) — every
comparison a whole algorithm-qualified digest under one algorithm, the
history join gated by the same commensurability. Then the blocked-entry
pass: the same three joins over each blocked entry's projections, and a hit
**refuses that dataset's answer** — blocked evidence never enters a tuple
and never silently vanishes from one; every other dataset proceeds, so one
crashed act at an unclaimed locator blocks nothing but itself. Output is
cut 2's `ByteObservation` tuples into `admission_state`, **unchanged** —
`dataset.py` does not move.

## 6. Conformance cut 10

Drafted and **frozen after this spec's review and before any implementation
task**, on the standing discipline: the freeze decides the selection
finally; any unrun arm is partial; the error always runs toward overstating
coverage, so classification is conservative.

**Candidate selection (the cut's draft decides):** H1–H4's store-reachable
arms — H1's three arms (listing/source-digest back-fill unmintable;
outside-boundary hash established nothing; `absent` only from a post-delete
look); H2's six (no timestamp ordering; disagreement blocks; checked
acyclicity; unsettled blocking with unresolved-as-itself; every agreeing
head retained; incommensurable); H3's three (declared coverage refused
absent; receipt re-run vocabulary; chain heads committed, never ambient);
H4's three (no silent act; no laundered non-answer; intent ordering or
failure) — plus L10u8/u10's dereference clauses as the successor
certification of cut 9's two partial units, and the fulfills/qualification
behavior **as the holdings-shape instantiation only**, declared so a
cross-cut listing cannot read it as L7's closure.

**Labeled deferrals:** the `url` arm (construction refusal is the labeled
behavior), acquisition orchestration, recency, typed grants, the general L7
reduction and G4.

**Evidence discipline, as established:** count claims quote pytest's own
summary line under `pipefail`, never a doubled `-q`, never a collect-only
count; the certified tuple, with the work directory on the repository's own
volume; the cut-10 acceptance runner chains the prior cuts as prefixes or
pins on the cut-9 pattern; the corpus guard and `check_guide.py` run as
evidence items — this slice moves the H table and the holdings design from
designed to landed, exactly the rot those guards watch.

## 7. What this changes elsewhere (applied at banking)

- **Adoption-ledger row 4:** the holdings-prerequisite clause closes — the
  read command and the post-state evidence return landed (the capture
  clause discharged as §2.2 records: established at commit verification,
  returned on the outcome), the pushed atoms head named. Row 4 stays the
  single authority for atoms implementation state.
- **Adoption-ledger row 5:** the remainder re-states as exactly intent
  qualification (G4), event-level L8, and the L13 preimage resolver — the
  holdings arms landed.
- **Cut 9's results record is not edited** (frozen); the live docs that
  carry its two partial units as open — the guide's current-state pages —
  gain the closure with dated markers.
- **`foundations.md`:** the current-state paragraph gains the holdings
  slice; the held section's derived-heldness sentence gains the landed
  pointer.
- **`contracts-and-adoption.md`:** cuts through 10; the open remainder drops
  the holdings arms.
- **README:** the design table gains cut 10 and this document's promoted
  row; the spelled-out design count and date range move under the corpus
  guard's machinery.
- **The stale-claim grep** (`holdings slice|unresolvable for holdings
  reads|row 4's|dereference-minting`) runs over `docs/` and `README.md`;
  frozen records stay untouched, per the freeze discipline.

## 8. Choreography (order of work)

1. This spec reviewed; findings closed by amendment commits.
2. **Atoms design gate:** the atoms-local design document for §2's two
   commands, drafted in the atoms repository, reviewed and approved there
   before implementation — then implemented, reviewed, merged into atoms
   `main`, and **pushed**.
3. **Cut 10 drafted and frozen** (own commit pinning the freeze), after the
   spec settles and before Science implementation.
4. Implementation plan written (`docs/superpowers/plans/`), reviewed, then
   executed task-by-task on the branch `design/holdings` (worktree
   `.worktrees/holdings`), with the **execution ledger at a tracked path**
   under `docs/plans/`, appended and committed at every task boundary —
   never worktree-only.
5. Science implementation order: records → stored codec/decode → boundary
   (intents, acts, qualification) → reducer → projection/receipt → adapter
   → the N2 declaration module and the cut-10 acceptance runner.
6. Discharge on the certified tuple; results record at
   `docs/plans/2026-08-24-conformance-cut-10-results.md`; banking applies
   §7's amendment set and promotes this spec; the `--no-ff` merge is the
   human partner's act, inheriting every prior reachability constraint plus
   cut 10's freeze pin.
