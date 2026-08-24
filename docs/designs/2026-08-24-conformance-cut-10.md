# Conformance cut 10 — verified holdings, store-side

**Status:** Draft — freezes at the commit closing the second reader's
findings (§7), before any implementation task (spec §8 step 3, the
standing discipline). Every quoted row must be byte-exact against its
source table as of the freeze commit.

**Sources:** `2026-08-23-conformance-cut-9.md` (rule and practice
inheritances); the holdings specification
`docs/superpowers/specs/2026-08-24-world-index-holdings-design.md`
(cited as *spec*); the banked verified-holdings record design
`2026-08-10-verified-holdings-record-design.md` (cited as *holdings
design*), whose §6 **H table** is quoted verbatim below — this cut is
that table's first reading; the frozen **L10** row of
`2026-08-03-tamper-evident-log-design.md` §10, quoted verbatim below;
and the approved atoms-local design
`docs/2026-08-24-holdings-read-and-evidence-commands-design.md` (in the
atoms repository, approved at atoms `558817b`, implemented and merged —
the atoms remote `main` at `038513f`), cited as *atoms design* for the
certified seam.

## 1. What this cut is

Cut 10 is the frozen acceptance boundary for world-index slice 5: the
`holdings-observation` record kind under
`science.holdings-observation.v1` with the store locator; the two store
act shapes — the pure dereference under intent-before-read, and the
managed write, delete, and move recording only the engine's verified
post-state evidence; the holdings-scoped qualification reduction; the
mechanical coverage capture and the pure, fixture-bound active-set
reducer with its three blocking classes; the coverage projection's
receipt under `science.holdings-receipt.v1`; and the dataset-scoped
adapter into cut 2's `admission_state`.

The selection rule is cut 5's rule, unchanged: a clause is selected only
when its source mutation and every named check run entirely inside §2. A
row with any unrun arm is **partial** — never "full" on an argument for
why an arm should not count. The three practice inheritances stand:
labeled declarations (§3.3), single-homing, and verbatim row quotation,
byte-exact against the source tables as of this cut's freeze commit.

Cut 8's engine-interior principle applies: **the atoms read command's
boundary interior (lease and lock acquisition, descriptor-anchored
traversal, the errno classification) and the mutating commands'
commit-time final-surface verification are atoms-certified productions
(atoms design §8; the atoms suite at `038513f`); this cut certifies
Science's acts, records, reduction, projection, receipt, and adapter
over the results those productions return.** Every fabricated corpus
state used by reducer arms must decode through the stored surface, and
every fabricated chain must pass `inspect_chain` — or each presents
exactly its one intended defect — asserted at declaration time.

## 2. The boundary

**Mutation surface:** the Science modules this slice adds or amends —
`science/holdings/` (records, boundary, reduce, project, adapter), the
identity package's new domains (`science.holdings-observation.v1`,
`science.holdings-receipt.v1`), the stored codec/decode surfaces the
kind joins, and `science/errors.py`'s new names — plus, as **certified
engine**, the merged atoms seam at `038513f` (`read_path_state`, the
translation table and both invariant halves, and
`TransactionOutcome.final_states`) beside the standing commands: their
interiors are certified by the atoms suite and are not this cut's
mutation surface, exactly as for cuts 4–9.

**Checks:** pytest nodes under `python/tests/`, and the cut-10
acceptance run. Durable arms live on the repository's own volume, never
`/tmp`, the scratch volume, or `/dev/shm`. Count claims quote pytest's
own summary line under `pipefail`.

**The raw-write license:** sabotage and fixture construction may
raw-author observation documents, chain entry files, intents, store
payload, engine bookkeeping, and configuration. Detection claims
quantify over cooperative writes; the license is the sabotage
construction's, bounded by §1's well-formedness obligation.

## 3. The rows

### 3.1 Rows read, quoted verbatim, with dispositions

| **H1** | creation is reserved to acts, and to established outcomes | back-filling `found` from a listing or a source digest is unmintable / a hash outside the consistent-read boundary established nothing, and raw concurrent mutation stays out-of-band / `absent` comes only from a post-delete look, never a return code |

- **Full.** Selected (3 units): **(u1)** the back-fill arm — a `found`
  minted from a directory listing's declared digests, or a managed
  write's observation minted from the **payload's** digest rather than
  the engine's verified final row, is unconstructible through the
  boundary, and the sabotaged construction that mints one fails exactly
  the declared checks; **(u2)** the outside-boundary arm — a digest taken
  through the detached capture path (no lease) instead of
  `read_path_state` established nothing: the boundary's act refuses to
  mint from it, with raw concurrent mutation staying §4's out-of-band
  bound, asserted as the claim, not tested as detection; **(u3)** the
  return-code arm — a deletion's `absent` is minted only from the
  transaction's verified final `AbsentState` row, never from the
  command's success alone, and a sabotage that mints it from the return
  fails the declared checks.

| **H2** | supersession is by explicit reference, per location, over a checked DAG, and a contested, incommensurable, or unsettled location is blocked | active-ness is walked per location over a checked DAG, never ordered by `observed_at` / disagreeing heads block the location rather than any outcome winning / acyclicity is validated on every walk / an unmatched or qualification-unresolved mutating intent leaves its location unsettled, blocking as itself / every agreeing head stays active under coalescence / an algorithm-mixed `found` pair blocks as `incommensurable`, forced into neither box |

- **Full.** Selected (6 units), one per sabotage arm: **(u1)** a reducer
  ordering by `observed_at` — two records at one location, neither
  superseding the other, with adversarial timestamps — changes no
  active-set membership; the sabotaged timestamp-ordering reducer fails
  the declared checks; **(u2)** disagreeing heads (`found` beside
  `absent`) block the location — the existential held-rule never counts
  the `found`; **(u3)** a crafted cycle in one location's `supersedes`
  refuses the **whole projection**, never hangs and never drops the
  location; **(u4)** an unmatched mutating intent — and separately a
  qualification-unresolved one (an unsettled registration in the
  captured chain) — leaves its location unsettled and blocked, distinct
  reasons carried, until a later fulfilled re-check intent lifts it; a
  reducer that ignores the carried intents, or collapses unresolved into
  either resolved state, fails the declared checks; **(u5)** two
  agreeing `found` heads with different `expected` values both stay
  active — coalescence selects no winner, and the dropped-head sabotage
  fails the expectation-join check that head alone feeds; **(u6)** a
  `found(sha256:…)` beside a `found(sha512:…)` blocks as
  `incommensurable`, forced into neither agreement nor conflict.

| **H3** | the derivation refuses an undeclared coverage, and its receipt is checkable | "whatever is checked out" is not a coverage — enumeration is by declared stable identity / a receipt the bound rule over the named inputs does not reproduce is `refuted`, an absent input `unresolvable`, corpora-not-states is `malformed` / log chain heads are coherently captured, committed inputs, never read ambiently |

- **Full.** Selected (3 units): **(u1)** a projection with no declared
  coverage refuses, and a declared corpus that cannot be produced
  refuses the **whole** projection — never a silent shrink to what is
  present; **(u2)** receipt validation is re-running: a reproduced
  reduction reads `validated` byte-for-byte on both output digests, a
  wrong reduction `refuted`, an unresolvable corpus state, chain head,
  or implementation `unresolvable` (never reported as refutation), and a
  receipt naming corpora-not-states or a bare version string
  `malformed`; a signing sabotage — half the coverage enumerated, or an
  unbound implementation run — fails the declared checks; **(u3)** the
  per-corpus chain heads are captured coherently with the corpus states
  and committed into the receipt's identity: re-running under a chain
  that gained an unmatched intent flips no verdict of a receipt whose
  named heads still resolve — the same states under **different** heads
  are a different receipt, not a different answer to the same one.

| **H4** | no silent act, and no laundered non-answer | an act records every outcome it established or fails, never a transient report and a dropped record / an inconclusive attempt reports through its own channel and never mints `absent` / a mutating act runs inside its intent–fulfillment ordering or fails |

- **Partial.** Selected (3 units), each in its **store instantiation**;
  the remote half of the row's vocabulary defers with the URL slice,
  named in §8: **(u1)** an act that established a finding publishes it
  or **fails loudly** — a publication failure after an established
  outcome raises, and the sabotage that reports transiently and drops
  the record fails the declared checks; **(u2)** an inconclusive store
  attempt — an unserviceable or metadata-less root, a preflight refusal,
  a boundary-unobtainable read, an established-neither observation —
  reports through the act's channel under the ramp vocabulary mapped
  from the command's structured phase (`byte-locator-untested` /
  `retrieval-failed`), **mints nothing**, and never supersedes the
  standing observation; the laundering sabotage (a refusal recorded as
  `absent`) fails the declared checks; **(u3)** a managed mutation runs
  inside its intent–fulfillment ordering or fails: the mutate-first
  sabotage (skip the intent, mutate, publish) fails the declared checks,
  and a crash between intent and mutation reads
  attempt-without-recorded-outcome — the unsettled state H2 u4 blocks
  on, cited never re-declared.

| L10 | A fork is a new chain; a replica is the same chain | fork act → fresh genesis carrying `(parent genesis, parent head)` and its own baseline; assert parent and fork anchors are never compared; replica/restore → same genesis, chain carried unchanged, comparability intact; a copy presenting the parent genesis under a fresh `corpus_id` manifest without a fork-genesis → its chain refuses to verify under the new identity (genesis names the parent `corpus_id`); the **store instantiation** (the verified-holdings record design §2) — replica act → same genesis, chain carried unchanged, a claim-only destination directory published first as reserved, surface-excluded no-clobber bookkeeping, with no payload, chain, override, lifecycle stamp or grant, or serviceability before the read-only stamp; kill inside that window → the interrupted copy is metadata-less, hence read-only, never a writable twin; cooperative mutation of an existing root **not granted writability** → refused, with recorded root creation the sole pre-grant write exception and the fork act the only writable exit; fork act → the new `store(store_id, forked_from)` genesis durable **before** the writability grant; kill between them → still a read-only replica; **copy any store tree without its engine metadata — replica or original alike — and cold-bootstrap it → read-only and unresolvable for holdings reads**, every mutation refused, the stamp's loss failing closed, never open; **restore two metadata-less copies of one `store_id` on two hosts → both enter service read-only**, a write on either refused — the sole writable exit is a fork under a new `store_id`, so two cooperative writers of one store stay unconstructible; **an interrupted copy carrying genesis and chain with payload files missing → the restore act's verification under a store-anchored observer set never returns `validated`**, the verdict is preserved — refuted, malformed, or unresolvable, never coerced to an admission — the root stays unserviceable and its dereferences mint nothing, in particular never an `absent` for a path the copy failed to carry; **a restore presented with an empty store-anchored observer set → unresolvable, replay not reached** (the verifier's L9 bound), the root unserviceable; raw-written copies of one `store_id` with branches assembled in one root → sibling-malformed (L3); both divergent heads supplied as anchors in one observer set → refuted (L9); the same two copies verified **separately** after their last common anchored head → each validates, the divergent tails L5's unanchored residue — the pinned surviving-observer negative *(amended 2026-08-10, the verified-holdings record design §8)*; *(amended 2026-08-23, the log-verification design §1.2/§6.2 — mechanism, not verdict: the copy presenting the parent genesis under a fresh `corpus_id` manifest **cannot** be caught by a genesis-payload comparison, since a corpus genesis names no `corpus_id`. The arrival act is the mechanism instead — `admit_arrival` selects `S = Corpus(provenance.parent_corpus_id)`, because the chain a replica carries is its parent's, and the fresh manifest then refuses `SubjectMismatch`: its chain refuses to verify under the new identity, exactly the frozen claim. This is the one arm of this row conformance cut 8 reads; every fork, replica-construction, restore and store arm still waits on ledger row 4)* |

- **Partial (this cut reads 2 units; cut 9's twelve and cut 8's one
  stand certified there, cited never re-declared).** Selected: **(u1)**
  the cold-bootstrap dereference clause, the successor of cut 9's L10u8
  remainder — a metadata-less store root is **unresolvable for holdings
  reads**: every dereference of it is an inconclusive attempt reported
  as such, **minting nothing**, never an `absent` for a path the copy
  merely failed to carry — the boundary's mapping of the read command's
  lifecycle refusal, exercised through the acts; **(u2)** the
  interrupted-copy dereference clause, the successor of cut 9's L10u10
  remainder — an unserviceable root that never validated has
  dereferences that **mint nothing**, in particular never an `absent`
  for an uncopied payload path. With these two units, the row's
  clause-by-clause coverage across cuts 8–10 has no named remainder;
  the row label stays partial because this cut reads exactly two of its
  clauses.

### 3.2 Rows not read

Every other row of every table stands at its prior cut's certification;
this cut reads exactly the rows its slice's mutations move. **L7 is
deliberately not read**: the holdings-shape qualification is declared as
labeled behavior (§3.3 label 9), and L7's general reduction, G4's
closure, and the boundary-side arms remain the intent-boundary slice's —
a cross-cut listing must not read this cut as L7's closure. No expected
row fails construction.

### 3.3 Labeled declarations

Twelve labeled declarations carry the spec's minted obligations outside
the frozen rows, declared as data beside the selected arms:

1. **The read-command consumption and the phase mapping** — the boundary
   maps the atoms read command's structured result and nothing else:
   `PathObserved(FileState)` → `found` from the content hash,
   `PathObserved(AbsentState)` → `absent`, a final symlink or directory
   → established-neither, `ReadNotAttempted` → `byte-locator-untested`,
   `ReadUnestablished` → `retrieval-failed`; a non-routine engine
   **raise** aborts the act — no report, no observation, the durable
   unmatched intent marking an intent-bearing attempt — and exception
   types are never classified into the report vocabulary (spec §2.1,
   §4.1). The command's interior is the atoms design's certified
   production, cited.
2. **The post-state evidence rule** — a managed mutation's observation
   records only the transaction's returned `final_states` rows (the
   commit-verified final surface); a refused or failed transaction mints
   nothing; the committed-but-unobserved window is unconstructible in
   the engine, cited never re-proven (spec §2.2).
3. **The locator union ships store-only** — `store(store_id,
   relative_path)` with the 32-hex identity and the refuse-never-
   normalize path grammar; constructing a `url` locator refuses with the
   named deferral error — the refusal is this label's declared behavior,
   not silence (spec §3).
4. **Construction canonicalization** — algorithm-qualified digests in
   canonical spelling with exact width where known; `expected` sharing
   its `found`'s algorithm or refused; `observed_at` in the one
   canonical UTC encoding; every violation refused at construction,
   never repaired (spec §3).
5. **Per-location supersession by construction** — the constructor
   validates every supplied predecessor record names the same canonical
   location and encodes the deduplicated reference sequence sorted by
   canonical reference bytes; a cross-location predecessor refuses
   (spec §3).
6. **The identity domain** — `science.holdings-observation.v1` over the
   whole facet, every field participating; two acts with identical
   findings mint two records because each bears its own `event_token`,
   distinctness never the clock's (spec §3).
7. **The stored surface** — a governed world-record kind with semantic
   stamping, joining the stored codec/decode surfaces; authored only
   through the acts boundary; a member of **no epoch map** — the
   coverage projection is its read surface this slice (spec §3).
8. **The holdings intent and its fulfillment** — the intent payload
   (canonical location, act kind, boundary-minted `event_token`, actor)
   appended in the observer's corpus before any store-dereferencing act
   reads or mutates; `fulfills` constructed by the boundary from its own
   intent, never caller-selected; and the publishing transaction
   **registers the observation's stored path**, so the chain's
   registration rows carry the row qualification reads (spec §4).
9. **Qualification is the pinned three-step precedence, holdings-shape
   only** — matched, then unresolved (a final file row at a
   holdings-observation path with no captured record deriving to it),
   then non-qualifying; a rolled-back registration is resolved and
   non-qualifying with its rows unconsulted; a registration with no
   settlement entry is unresolved as itself; **the general L7 reduction
   and G4 are explicitly not claimed** (spec §4.3, §5.1).
10. **The move choreography** — two intents appended one at a time, two
    registrations, and the three crash windows read exactly: between the
    appends, one location unsettled and the other intent-less and
    unmutated; after both appends before the mutation, both unsettled;
    between the publications, one settled and one unsettled (spec §4.2).
11. **Mechanical capture under the closed schema** — the coverage
    projection carries every stored record's uid and §11.1 canonical
    projection (no kind filter, no storage bytes) and the validated
    chain whole with settlement entries; a record that cannot be read or
    generically decoded refuses the **whole capture**; the value's field
    names, orders, and variant tags are the spec's closed schema, one
    capture one byte form (spec §5.1) — the constructions H3's arms
    stand on, declared once here.
12. **The receipt facet** — `science.holdings-receipt.v1`, closed
    members: `kind` (`holdings-reduction`), `coverage` (sorted
    corpus-id/state/chain-head triples), the rules-store binding pair,
    and the two outputs' canonical-encoding digests — identity digesting
    **every member**, and the reducer installed and resolved through the
    rules store's fixture-bound admission (spec §5.2).

## 4. Accounting

Five rows read: **3 full** (H1, H2, H3) **+ 2 partial** (H4, L10).
Selected units by row: H1 3, H2 6, H3 3, H4 3, L10 2 — **17 selected +
12 labeled = 29 declaration units**.

## 5. N2 obligations

Beyond the standing N2 harness discipline, the declarations carry these
check-time obligations:

1. **Fabrication well-formedness** (§1): every fabricated corpus state
   decodes through the stored surface, and every fabricated chain passes
   `inspect_chain` — or each presents exactly its one intended defect —
   asserted at declaration time.
2. **H2 u1** asserts its two records genuinely fail to reference each
   other and that only their timestamps differ between the paired
   constructions — an identity delta would make the ordering claim
   vacuous.
3. **H2 u4's unsettled constructions** produce their intents through the
   boundary's own append path (a genuinely crashed or abandoned act),
   never by raw-authoring chain entries; the unresolved variant's
   unsettled registration is a chain state `inspect_chain` accepts.
4. **H3 u3** asserts the two captures differ only in the one corpus's
   chain head — same corpus states — before asserting distinct receipt
   identities.
5. **H4 u2** asserts the standing observation's identity is unchanged
   across the inconclusive attempt — "left standing" is a comparison,
   not an absence of code.
6. **L10 u1/u2** assert their roots' lifecycle states (metadata-less;
   read-only unserviceable post-failed-restore) through
   `read_lifecycle_state` before any dereference is attempted.
7. **Count claims** in the results record quote pytest's summary line
   under `pipefail`, never a collect-only count.

## 6. Freeze obligations

Three, named before the plan exists: **H1 u2's outside-boundary digest**
must be taken through the detached capture path over an undamaged store
— never by chain or payload damage — so the established-nothing claim is
the boundary's, not corruption's; **H2 u3's cycle** must be constructed
by raw-authoring records whose `supersedes` references close a loop
while each record remains individually well-formed under the stored
codec — the refusal must be the walk's acyclicity check, not a decode
failure; and **the L10 units' dereferences** must run through the acts
boundary (the act reporting, minting nothing), never by calling the
atoms read command directly — the claim is Science's mapping, and the
command's own refusal is the atoms design's certified territory.

## 7. Second reader

The charge, unchanged from cut 9 §7: verify every quoted row byte-exact
against its source table; audit each selection against §2's boundary;
check single-homing across rows and labeled declarations; test each
partiality against the any-unrun-arm rule; verify the §4 accounting by
independent recount; and read §3.2 adversarially. Findings and their
dispositions are recorded here before freeze.

## 8. Limitations

1. **No persistence-cut harness** (fourth cut running): kill-at-stage
   and durability-order interiors defer to the atoms certification; this
   cut reads returned results and resulting states.
2. **The URL arm defers whole**: the `url` locator's canonicalization,
   the network retrieval boundary, and H4's remote instantiation — a
   remote look never answering *nothing is there* — wait on the URL
   slice; label 3's construction refusal is the declared boundary.
3. **Acquisition orchestration defers** with the act-report design's
   reading of act termini; no acquisition-level state is read here.
4. **The intent-boundary territory is untouched**: L7's general
   reduction, G4's closure, and the boundary-side arms — label 9
   declares the holdings-shape instantiation only.
5. **Recency and typed grants defer** as the holdings design's §7 items
   1 and 8; the reducer this cut certifies is the rule a recency
   successor would replace, its binding receipt-pinned for exactly that
   day.
6. **Whether the derivation receipt joins the belief-input closure is
   not decided here** — this cut keeps the receipt a value with a
   content identity, ready either way (holdings design §5, §7 item 3).
7. **The cut inherits the spec's rulings as dated**; a future design
   moving any extends by a successor cut, never by editing this one.
