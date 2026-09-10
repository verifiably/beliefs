# World resolution, slice 2 — the coreference attestation and its balance

**Date:** 2026-09-10
**Status:** draft, awaiting review
**Boundary:** `world-resolution`, slice 2 of four (`beliefs-d248ba`), task `beliefs-113561`
**Lane:** `world-read`, worktree `.worktrees/world-resolution`
**Sources:** `../../designs/2026-08-08-world-address-ruling.md` (§3, §5–§5.5, §9),
`../../designs/2026-08-02-world-addressing-design.md` (§4.1, §4.2, §7 rows W4,
W8a, W15, W16),
`../../designs/2026-08-03-world-index-packaging-design.md` (the coreference
receipt, X10, X12),
`../../designs/2026-08-20-world-index-slice-2-design.md` (§7.4–§7.6, §8.2, §8.4),
`../../designs/2026-08-04-formal-model-and-claim-calculus-design.md` (§2.1 and
§3.2 rows for the kind and `attest-coreference`; M3),
`../../designs/2026-09-04-write-permits-design.md` (`KIND_ACTS`),
`../../designs/2026-09-05-writer-session-design.md` (§4.2 items 2–3),
`../../designs/2026-09-05-facet-contracts-design.md` (§6, the deferred kinds),
`2026-09-09-world-resolution-slice-1-design.md` (§1, §7)
**Measured against:** `main` at `4210834`

## 1. What this slice is

The world address ruling made different-basis coreference an attributed,
additive attestation with a derived balance and retired structural merge. The
kernel banked the shape and built everything downstream of the record: the
reduction rule and its four fixtures (`world/rules_v1/coreference.py`), the
captured value (`derive.CapturedCoreference`), the epoch member
`coreference-map.yaml` and its receipt, the permit entry, and the read side's
three edge states with the expansion refusal (`world/read.py`). What it never
built is the record. `contracts/science/CONTRACT.yaml` declares
`coreference-attestation: {}` with no domain and no facet; `stored.py` has no
builder and no reader; `CorpusWriter` has no seam; and `epoch._captured_records`
lifts no coreference facet, so every published coreference map is `{"pairs": []}`
and every build refuses a record that claims the kind with
`EnumeratedKindUngoverned`. The cut 7 results record names this: "two
enumerated kinds remain prose … every populated membership, reduction, and
omission-refutes arm waits on the kinds' own charters."

This slice builds the record and connects it. It promotes the kind from
deferred to governed, gives it a stored builder and facet reader, adds the one
write seam that mints it under the four endpoint refusals the ruling names,
lifts the facet at capture so the shipped reduction reduces real attestations,
and reads every populated arm the balance, receipt and edge-state rows carry.
The read side's balance branch does not change: over an established coverage a
pair the reduction never recorded is `inactive`, which is the ruling's "zero or
negative does not" activate, and omission is the receipt's finding, not the
reader's.

**Rows it closes or reads.** W15 in full; X12's coreference arms; W8a's
coreference omission-refutes and coverage arms; M3's coreference arm; W4 as
rewritten by the ruling (§9 there). W8b stays measured and not selected: its
build defect is repaired (`beliefs-fda0e5`), and selecting it is a decision for
a cut whose boundary is the build's uniqueness check, not this one's.

**Rows it does not touch.** W1, W2 and W5a were filed to this slice and are
**re-filed to a sibling slice** (§12): each rests on a source's address being
derived from its normalized external identifier, which the ruling upholds (§2
there) and the builder does not do — `stored.source_node` takes an authored
slug — so closing them is a source re-addressing design with its own
normalization rule and an identifier-correction rename, touching 78 call sites
across 18 test files and no line of coreference code. Slice 3 keeps the
snapshot, import, audit and diagnostic callers, R23's remaining clauses and the
X5 and W13 relabels; slice 4 keeps W7. The `instrument-certification` kind stays
deferred with `contract-cut`; every test that pins both deferrals together is
split so its pin survives.

## 2. Decisions

1. **The record carries no relations.** Its endpoints live in the facet only.
   `RelationAdjacency`, the world inbound index, `closure`, `producers` and
   every lineage walk therefore cannot observe an attestation, and only
   `read.expand_coreference` does — which is W15's closure arm ("only query
   expansion observes the edge") holding by construction rather than by a
   filter each walker must remember. A relation would also need a declared
   predicate whose `sources`/`targets` closure admits every world kind, which
   the contract's relation table has no precedent for.
2. **Grounds is one exact string, compared byte for byte.** The ruling's
   deduplication key reads `grounds`, and §5.2 there refuses to decide when two
   rationales are the same rationale. The captured value and all four rule
   fixtures already hold `grounds` as one text; this slice keeps that shape and
   states the comparison: no Unicode normalization, no trimming, no case fold.
   Two grounds that differ in one byte are two units, deliberately.
3. **Endpoints resolve through a view the caller supplies.** The retract
   precedent resolves its target in the writer's own corpus. An attestation's
   whole purpose is often a pair held in two corpora, so the seam takes
   `view: ReadView | WorldReadView`, defaulting to the writer's own view, and
   the world view resolves at its stamp. The seam never opens a world view
   itself: opening one takes every covered corpus's capture hold, and the
   writer already holds its own corpus's operation lock, so an open from
   inside the seam would refuse itself with `BuildContended`.
4. **The four endpoint refusals are one error class with a closed reason.**
   `CoreferenceEndpointRefused(WriteRefused)` carries `reason` in
   `("self-pair", "kind-mismatch", "unresolved", "inadmissible-kind")` and the
   offending endpoint. W15 asks for four distinguishable refusals; a closed
   reason set is distinguishable and keeps `errors.py` from growing four
   classes that differ only in name. `inadmissible-kind` is the curation-note
   refusal in this kernel: a record with no basis is refused at mint (W3), so
   the only stored belief-inert records are the prose kinds and the
   coordination kinds, and neither is a world entity a semantic reference may
   name.
5. **An attestation is a retraction's peer under every lifecycle operation.**
   It is not added to `EXCLUDED_MUTATION_KINDS`: `move` carries it, `consolidate`
   repairs two equal-basis replicas of it, `delete` removes it under the
   deletion audit, exactly as a retraction. Deleting an attestation moves the
   next build's balance, as deleting a retraction moves standing; the deletion
   design already reads that as a managed write with an audit trail, and this
   slice adds no second rule. It is **not** added to
   `ELIGIBLE_RETRACTION_TARGET_KINDS`: the ruling records that retracting an
   individual attestation is a trigger, not a mechanism, and a negative
   attestation offsets.
6. **Actor is bound, weight is unit.** The facet's `actor` must equal the
   writer authority's actor (`ActorMismatch`, the retract precedent), so the
   record's attribution is the session's and not a claim. No attester class is
   privileged: the seam reads nothing about the actor but its string.
7. **The capture lifts the validated facet.** `_captured_records` validates
   every `coreference-attestation` node's facet through the stored reader and
   passes `derive.CapturedCoreference`. `ENUMERATED_SOURCE_KINDS` is not
   edited: its refusal is computed against `stored.SEMANTIC_DOMAINS`, and the
   contract change lifts it.

## 3. The kind

### 3.1 Contract

`contracts/science/CONTRACT.yaml` and its byte-identical packaged copy change
in two places:

```yaml
kinds:
  coreference-attestation:
    domain: science.coreference-attestation.v1
    facets: { coreference-attestation: { required: true, covered: true } }
facets:
  coreference-attestation: { shape: reader, reader: stored.coreference_attestation_value }
```

`WORLD_KINDS` keeps its order and membership. `SEMANTIC_DOMAINS` gains the
kind; `COVERED_FACETS` gains `("coreference-attestation",)` for it. The
contract's `content_identity` and the profile's `compiled_identity` move,
as every contract edit moves them; no test pins either as a literal.

### 3.2 The facet

```
coreference-attestation
  endpoints     [left, right]   two distinct typed refs, stored sorted, left < right
  stance        1 | -1
  actor         non-empty text, the minting authority's actor
  grounds       non-empty text, exact
  event_token   non-empty text, minted per act
```

Exactly these five keys. The identity is `v1.digest("science.coreference-attestation.v1", facet)`
and the address is `coreference-attestation:<digest>`; the semantic-identity
stamp is the ordinary `_node` stamp. Two attestations differing only in
`event_token` are two records at two addresses, and the reduction counts them
once (§5).

### 3.3 `stored.py`

- `COREFERENCE_ATTESTATION_FACET = "coreference-attestation"`.
- `CoreferenceAttestation` frozen dataclass: `endpoints: tuple[str, str]`,
  `stance: int`, `actor: str`, `grounds: str`, `event_token: str`.
- `coreference_attestation_value(node) -> CoreferenceAttestation`: the facet
  reader the contract names. Refuses with `MalformedRecord` a facet whose key
  set is not exactly the five, endpoints that are not a two-element list of
  non-empty text, endpoints not in sorted order, a self-pair, a stance outside
  `{1, -1}` or not an `int` (`True` is refused: `type(stance) is int`), and any
  empty text. It does not resolve endpoints — a reader has no view.
- `coreference_attestation_node(*, title, endpoints, stance, actor, grounds, event_token) -> Node`:
  sorts the pair, validates as the reader does, requires `actor` through
  `require_actor`, digests, and builds through `_node` with no relations.

## 4. The write seam

### 4.1 `CorpusWriter.attest_coreference`

```
def attest_coreference(self, record: Node, *, view: ReadView | WorldReadView | None = None) -> Node
```

In order, under `self._operation` (the settling hold, as `retract`):

1. `self._authority.require("corpus-write", ("coreference-attestation",))`
   before the hold, as every entry point.
2. `_require_pins_agree()`.
3. `_refuse_family_kinds(record, admitted_kind="coreference-attestation")`.
   `_refuse_family_kinds` gains the clause
   `node.kind == "coreference-attestation" and admitted_kind != "coreference-attestation"
   → WriteRefused("a coreference attestation enters through attest_coreference")`,
   so `add` and `import_bundle`'s ordinary path refuse it as they refuse a
   retraction.
4. The facet's `actor` must equal `self._authority.actor`, else
   `ActorMismatch`, checked on the raw facet before shape validation so an
   attribution forgery is named as such.
5. Shape: `stored.coreference_attestation_value(record)`; `MalformedRecord`
   becomes `ValidationRefused("… refused by coreference shape validation: …")`.
   The record must equal `coreference_attestation_node` rebuilt from its own
   facet, byte for byte, else `MalformedRecord` — the controlled-shape check
   `_validated_retraction` performs.
6. Endpoints, over `view or self._view`, each endpoint in sorted order and
   the first failure refusing:
   - **inadmissible-kind:** the ref's kind prefix (`ref.partition(":")[0]`)
     is not in `stored.WORLD_KINDS`. Prose and coordination kinds refuse here
     before any lookup.
   - **self-pair:** left equals right after the builder's sort — reachable
     only through a raw record, since the builder refuses it, and kept as a
     seam refusal so the seam does not trust its input.
   - **unresolved:** `view.resolve(ref)` is `None` or differs from `ref`.
     Over a world view the message names `locate(ref)`'s answer: `Unknown`, or
     `NotPresent` with its corpus id, since an endpoint the world knows but
     cannot read now is still an endpoint that does not resolve now. An
     endpoint that resolves through `deprecated_ids` to a different live
     address refuses: the attestation names exact canonical addresses, and a
     retired one is not that.
   - **kind-mismatch:** `view.get(left).kind != view.get(right).kind`. The
     resolved records' kinds decide, not the prefixes; a prefix disagreeing
     with its record's kind is corruption and `view.get`'s validation refuses
     it first.
7. `self._refuse(record, document_validated=True)`: minted-already, basis,
   eligibility, facets, governed stamp, rendering, collision.
8. `self._corpus.add(record)`.

No endpoint is read again after step 6 and none is written: an attestation
changes no existing record (formal model §3.2, `attest-coreference`). The
seam mints no act-report and opens no intent of its own beyond the ordinary
corpus-write intent `_fulfilling` records, as `retract` does.

### 4.2 The session

`OperationWrites.attest_coreference(record, *, view=None) -> OperationCommit`
and `ScopedWriter.attest_coreference(record, *, view=None) -> Node` are added
on the `retract` pattern: the session lock, then the raw root lock, currency,
`perform`, and the `act` line recording the minted `(uid, id)`. Reconciliation
is generic over the intent digest and learns nothing new. The writer-session
design's "seven operation seams" (§4.2 items 2–3) becomes eight by dated
amendment in the same change, with the static-inventory sentence of §4.4
there corrected in place; the world-changing families design's "own the seven
write methods" is amended the same way.

### 4.3 Errors

`CoreferenceEndpointRefused(WriteRefused)` with members `endpoint: str`,
`reason: str` (closed to the four above) and, for `unresolved` over a world
view, `corpus_id: str | None`. It is exported beside the retraction refusals.

## 5. The build and the receipts

`epoch._captured_records` adds, after the retraction facets:

```
attestations = {node.id: stored.coreference_attestation_value(node)
                for node in nodes if node.kind == "coreference-attestation"}
```

and passes
`coreference=derive.CapturedCoreference(a.endpoints, a.stance, a.actor, a.grounds, a.event_token)`
for those nodes. A malformed facet raises `MalformedRecord` out of the
capture, as a malformed retraction facet does today: the capture is discarded,
never narrowed. Everything downstream is unchanged and now populated: the
shipped `reduce_coreference` sums stance over distinct
`(endpoints, stance, actor, grounds)` per sorted pair, `derive.coreference_map`
checks `left < right`, `count >= 1` and `abs(balance) <= count`, the member is
written, and the coreference receipt names the rule binding and corpus states.
`validate_receipt(world, published, "coreference-reduction")` rebuilds over the
named states and compares the projection byte for byte; an omitted in-coverage
attestation or a wrong balance is `refuted`, an absent named state or an
un-held rule is `unresolvable`, a bare version string is `malformed`.

The coverage bound is the build's, not the seam's: an attestation in a corpus
outside `coverage` is outside the pair's published balance, and the coverage
declaration states the bound. Nothing about the belief input digest changes:
the coreference map carries no semantic identity and is not a member of
`belief_input_identity`, so two epochs differing only in their coreference map
carry one digest.

## 6. The read side

No branch of `coreference_edge` or `expand_coreference` changes. What changes
is that the reduction they read is now populated, and the tests that bound a
sibling rule reducing `produces` edges into pairs — the `COREFERENCE_ANCHOR`
scaffold in `test_world_read.py` — are replaced by real attestations. The
three states stay: `active` for balance > 0 over an established coverage,
`inactive` for balance ≤ 0 or a pair never recorded, `indeterminate` when a
live corpus is outside the epoch's coverage or the receipt is anything but
`validated`; expansion over an indeterminate edge raises `EdgeIndeterminate`
naming the missing coverage and the receipt outcome.

One consequence the row text can be misread on, stated here so the arm is
exact: an attestation in a corpus that is **inside coverage but unmounted**
still contributes to the **published balance**, because the map is the
reduction and not pointers. The **edge answer** over that world is
`indeterminate` with `receipt_outcome == "unresolvable"`, because the receipt
cannot be rebuilt against a corpus that is not standing at its named state.
Both are asserted; the arm's claim is that the map holds `1` and no reader
recomputes `2` from the mounted corpora alone, not that the edge is active.

## 7. Lifecycle

- `move` and `delete` accept the kind as they accept a retraction.
- `consolidate` accepts two equal-basis replicas at one address; two
  attestations at different addresses refuse there as "a coreference
  question", which the relocation rows already assert.
- `consolidate` writes no attestation and moves no balance (W16's negative,
  already asserted in `test_relocation_rows.py` and the relocation
  acceptance module); those assertions now run against a governed kind
  rather than an unmintable one, and are re-run in this cut's suite.
- An attestation is not a retraction target and not a belief read kind
  (`evaluation.READ_KINDS` is unchanged).

## 8. Measured rather than built

**W4 as rewritten:** "assert no operation retires an address on coreference
grounds." After an attestation over `{A, B}`: both records are byte-identical
to their pre-attestation bytes, both addresses resolve live, neither carries
a new `deprecated_ids` entry, and the world address map records both as
live. The operation inventory — `add`, `retract`, `supersede`, `revise`,
`delete`, `move`, `consolidate`, `attest_coreference`, the coordination
mints — contains no member that writes a `deprecated_ids` entry on any input;
`consolidate` unions the two inputs' existing entries and creates none. The
arm asserts that inventory by name, so a future rename family that does retire
an address must amend it and cannot slip in under W4's negative.

**M3's coreference arm:** attest coreference between two distinct-basis
retractions `R1` (in A) and `R2` (in B). Assert both retraction records are
byte-unchanged, `standing` over each target is unchanged, the retraction
graph the writer and the audit compute has no edge between them, and
`expand_coreference` over the active edge is the only structure that
associates them. No operation exists that merges them: the arm asserts the
inventory above has no `merge` member.

## 9. Refusals

| condition | answer |
|---|---|
| a `coreference-attestation` through `add` or an import bundle | `WriteRefused`, "enters through attest_coreference" |
| the facet's actor is not the authority's | `ActorMismatch` |
| a malformed facet | `ValidationRefused` wrapping `MalformedRecord` |
| a record not byte-equal to its controlled rebuild | `MalformedRecord` |
| an endpoint whose kind prefix is prose or coordination | `CoreferenceEndpointRefused("inadmissible-kind")` |
| left equals right | `CoreferenceEndpointRefused("self-pair")` |
| an endpoint that does not resolve exactly: unknown, not present, or resolving only through a retired address | `CoreferenceEndpointRefused("unresolved")`, naming the corpus when the view is a world view and the answer is `NotPresent` |
| endpoints of two kinds | `CoreferenceEndpointRefused("kind-mismatch")` |
| an authority without `corpus-write` over the kind | the permit's refusal, before the hold |
| a malformed attestation facet at capture | `MalformedRecord` out of the build; nothing published |
| a stance outside ±1 at the builder | `MalformedRecord` |

No refusal here is a balance answer, and no balance answer is a refusal: the
seam refuses records, the receipt refutes maps, and the edge reads
`indeterminate`.

## 10. Testing and the cut

**Unit** (`tests/test_coreference_attestation.py`, new): the builder and
reader over every malformed shape; the seam's refusal order; the actor bind;
endpoint resolution over a corpus view and over a world view, including
`NotPresent` and a retired address; `add` and import refusing the kind; the
capture lift; a balance sequence through the shipped rule over real
attestations; `consolidate` over two replicas.

**Acceptance** (`tests/acceptance/test_coreference_acceptance.py`, new, over
`work_directory` with slice 1's `durable_world` fixture shape), one durable arm
per row clause:

- **W15 endpoints:** the four refusals, each over a real pair in one corpus,
  plus the not-present and retired-address cases over a world view.
- **W15 balance:** `+1` from actor `human-a` and `+1` from actor `agent-b`
  over one pair → balance 2, `active`; swap which actor posts which → the
  published map is byte-identical. A `-1` → balance 1, still `active`, three
  records present. A second `-1` from a third actor → balance 0, `inactive`,
  four records present.
- **W15 duplicates:** over a fresh pair at 0, the same
  `(endpoints, stance, actor, grounds)` ten times under ten tokens → ten
  records at ten addresses; after the first the balance is 1 and
  `distinct_key_count` 1; after all ten both are unchanged. Then the same
  actor with different grounds → balance 2, count 2.
- **W15 closure:** with an active edge between `A` and `B`, a retraction
  targeting `A` still stores `A`'s exact address; `π_claim`, every
  `belief_input_digest` over closures naming `A`, and every content identity
  in both corpora are byte-unchanged before and after the attestation;
  `inbound(A)`, `inbound(B)`, `closure` and `producers` return exactly what
  they returned before.
- **W15 coverage:** A holds `+2` on a pair, B holds the only `-1`. Epoch over
  `{A, B}` → balance 1, `active`. Epoch over `{A}` → balance 2, and the
  coverage declaration differs. Query the `{A, B}` world naming the `{A}`
  epoch → `indeterminate` with `missing_coverage == (B,)`, and
  `expand_coreference` raises naming B. Assert that no call shape names no
  epoch: `coreference_edge` and `expand_coreference` require one and there is
  no `current` overload. Then, over the `{A, B}` epoch: un-hold the rule →
  `indeterminate`/`unresolvable`; repackage with the balance altered and the
  receipt's subject recomputed → `indeterminate`/`refuted`; raw-write a
  receipt with a bare version string → `indeterminate`/`malformed`. All three
  refuse expansion.
- **W15 absent is not empty:** as §6 states it: B unmounted after the
  `{A, B}` publication → the map's pair still reads 1; the edge is
  `indeterminate`/`unresolvable`; remounting B restores `active`.
- **W15 cycle:** as §8's M3 arm.
- **X12 membership:** an attestation in A with A covered → inside the
  balance; the same attestation with A outside coverage → outside it, the
  coverage declaration stating the bound.
- **X12 / W8a omission-refutes:** publish over `{A, B}` with attestations in
  both; repackage into an internally consistent epoch omitting one pair
  member's contribution (balance and count reduced, subject identity
  recomputed) → `validate_receipt` is `refuted`; the producer, retraction and
  certification receipts stay `validated`.
- **X12 wrong balance:** leave every attestation in place, publish a wrong
  balance for one pair with a consistent subject → `refuted`; the covered
  edges read `indeterminate`; `belief_input_digest` over a closure in A is
  identical between the genuine and the refuted epochs.
- **W8a coverage:** B holds attestations and nothing else. Epochs over
  `{A, B}` and `{A}` differ in the coreference map and the coverage
  declaration, and carry identical producer snapshots and identical
  `belief_input_digest` over the same closure — the fixture holds every run
  and dataset in A so the producers map cannot be what differs.
- **W4:** as §8.
- **Lifecycle:** `move` an attestation from A to B → the next epoch's balance
  is unchanged; `delete` it → the next epoch's balance moves and the deletion
  audit names the deletion; `consolidate` two replicas → one address, no
  balance change (each replica was one unit); `add` refuses the kind.

**N2 sabotages**, one per mechanism, declared in
`tests/acceptance/n2_arms_cut24.py` and audited by
`tests/acceptance/test_n2_cut24.py` on the cut 12 pattern with the staleness
baseline taken from the tree: the kind-prefix admissibility check (accept a
prose prefix), the self-pair check (drop it), exact resolution (accept a
deprecated-id resolution), the kind comparison (compare prefixes instead of
records), the actor bind (skip it), the family-kind clause (let `add` mint
it), the controlled-shape rebuild (skip it), the capture lift (pass
`coreference=None`), the dedup key (add the event token to it), the coverage
bound (reduce over every configured corpus), the receipt rebuild (compare
membership and not balances), the digest boundary (add the coreference map to
`belief_input_identity`'s members), the no-relations invariant (attach a
relation to each endpoint), and the inventory arm (register a `merge` name).

**The cut.** This design freezes as **conformance cut 24**, numbered after
cut 23 and serialized after its discharge (`main` at `6eb0b93`). The runner
`python/tools/cut24_acceptance.py` names `PREFIX_RUNNERS = ("cut23_acceptance.py",)`
and `PHASE_MODULES = ("test_coreference_acceptance.py", "test_n2_cut24.py")`.
Declaration units: `W15`, `X12`, `W8a`, `M3`, `W4`, each single-homed. W15,
W4 and the coreference arms of X12, W8a and M3 close; X12 and W8a stay part
on their `instrument-certification` arms (`contract-cut`) and W8a on its
import and audit arms (`packaging-remainder`); M3 stays part on its
concrete-cycle limitation.

## 11. Shared files, under roadmap concurrency rule 3

`errors.py`, `corpus.py`, `stored.py`, `permit.py` (docstring only),
`world/epoch.py`, `session/writer.py`, `contracts/science/CONTRACT.yaml` and
its packaged copy, `python/tests/test_designs_corpus.py`, the adoption
ledger, the roadmap, the guide index and `docs/guide/identity-world-and-change.md`.
Tests that pin the deferral and are split or amended: `test_facet_declarations.py`,
`test_base_contract.py`, `test_world_build.py` (four tests),
`test_world_read.py` (the sibling-rule scaffold), `test_world_receipts.py`
(the empty-reduction docstring), `ts/tests/declarations.test.ts` (the
`facets toEqual({})` line). Designs amended by dated note: the writer-session
design (§4.2, §4.4), the world-changing families design (the write-method
count), the facet-contracts design (§6: one deferred kind remains), the
world-index slice 2 design (limitations: one enumerated kind remains prose).
No frozen guarantee row is edited.

## 12. Task linkage

`beliefs-113561` carries this spec; the implementation plan's tasks become its
children. W1, W2 and W5a are re-filed as a new sibling under `beliefs-d248ba`,
`beliefs-b7994b` **"World resolution slice 2b: source addresses derived from
the normalized identifier"**, depending on this slice's discharge, carrying
the finding in §1 and the 78-site measurement; the roadmap's W-row
classification names it at this cut's re-rank.
The task body for `beliefs-113561` is corrected by note to say the three rows
moved.

## 13. Open questions this design files

1. **Whether a coreference balance belongs in any audit** stays open in
   `open-questions.md`; the world-scale audit is slice 3's, and this slice
   surfaces no balance in any finding.
2. **Attester reliability** stays open; this slice records `actor` and weighs
   nothing.
3. **Endpoint identity at attestation time.** The record names addresses, not
   content identities. A later revision of an endpoint's display facet or a
   §4.4 rename of it leaves the attestation naming the same entity through
   the same or a redirected address; a `delete` of an endpoint leaves an
   attestation whose endpoint no longer resolves, which the next capture
   still reduces (the reduction does not resolve) and which no reader
   refuses. Whether the world-scale audit should report an attestation over a
   deleted endpoint is filed to slice 3 beside its drift question.

## 14. Review log

*(empty until the first review pass)*
