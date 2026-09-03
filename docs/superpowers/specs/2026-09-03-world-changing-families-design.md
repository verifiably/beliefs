# The world-changing families: consolidate, move, and managed deletion

**Date:** 2026-09-03

**Status:** Review specification. Not banked. Promoted into `docs/designs/`
with the relocation cut's freeze.

**Scope:** The `consolidate-family` boundary of
[`../../plans/2026-08-29-implementation-roadmap.md`](../../plans/2026-08-29-implementation-roadmap.md),
with its `run-boundary-remainder` and `formal-model-remainder` ride-alongs.

**Prerequisite:** The family adapters of
[`../../designs/2026-08-19-family-adapters-design.md`](../../designs/2026-08-19-family-adapters-design.md),
whose §2.4 deferred exactly these three families "to their own cut with the
world index" and whose §5.3 requires this design to replace its concurrency
ruling.

## 1. Decision

Add three world-changing operations. `delete` joins `CorpusWriter` beside
`add`; `move` and `consolidate` live in a new module `beliefs.relocation`
that **composes** two `CorpusWriter`s and subclasses neither. Every mutation
remains an `atoms` effect executed by the certified engine under the per-root
operation lock, and every one of them mints a boundary act-report.

The boundary discharges across two freezes, in this order:

| freeze | operations | rows |
|---|---|---|
| the **relocation** cut | `move`, `consolidate` | W5, W16 (part), G3, D7, C3's move clause, R23's move and consolidate clauses, M3's replica arm, T2's per-kind arm |
| the **deletion** cut | `delete` | G2c, G8, C6, R5, S5's deletion half, R23's deletion clauses, W16's remainder, C1 (re-read), T8's delete clause (re-read); then R19, R22, M1, M3, M5 |

Cut numbers are claimed at freeze, not here (roadmap concurrency rule 1). The
relocation cut freezes first and takes the lower number; the deletion cut
names the relocation cut's acceptance runner as its prefix (rule 5).

## 2. What this replaces and what it amends

### 2.1 The create-only concurrency ruling lapses

Family adapters §5.3 argued that a target resolving under the lock cannot be
made missing "because no family deletes or moves it." That argument dies with
this design, and `corpus.py`'s `CorpusWriter` docstring already says so in
advance: *"A future deletion-capable family must re-own this question; neither
argument transfers to it."* §3.5 below is its replacement, and the docstring is
rewritten in the same change.

### 2.2 C1 is narrowed by dated amendment, not by a deletion refusal

Correction lifecycle C1 reads *"assert no API edits or deletes a target"*, and
cut 5 read it in full. A general `delete` contradicts the sentence as written.

The resolution is **not** to refuse deletion of retraction targets: that would
be a referential check, and §3.1 rejects those because S5's and R23's selected
arms require deleting a producing run and an ancestor that other records still
name. C1's claim is instead narrowed by a dated amendment in the
correction-lifecycle design:

> C1 is a claim about the **retraction family**: retraction is additive, and
> the retraction operation never edits, removes, or re-addresses its target.
> It is not a claim that no operation anywhere can remove a record.

Cut 5's reading of C1 stands as a reading of the pre-amendment text and is not
edited. The deletion cut **re-reads** C1 against the narrowed claim, which is
what keeps the row's closure resting on evidence that postdates the deletion
API rather than predating it.

### 2.3 T8 is re-read, and act-reports are undeletable

T8 is closed and its last clause is *"Attempt to edit, supersede, and delete a
report through every ordinary API; assert no such path exists."* A general
deletion API is a new ordinary API, so:

- `act-report` is an **excluded kind** for `delete` (§3.1), and
- the deletion cut re-reads T8's delete clause against `delete` itself.

This is a re-read, not a reopening: the row's claim is unchanged and still
holds; what changed is the set of APIs the word "every" quantifies over.

### 2.4 The act-report operation enum gains three kinds

`report.OPERATION_KINDS` is the closed enum
`("acquisition", "audit", "import", "re-check", "run-attempt")`, extended only
by amendment (act-report design §2). This design amends it to add
**`consolidate`**, **`move`**, and **`delete`**, and adds one entry type,
`RecordMutationEntry`, for their outcomes (§4).

Two consequences cross into the acquisition lane and are named here rather
than discovered at merge:

- **T2** — *"Run each operation kind to success"* — now quantifies over eight
  kinds. Both cuts here select T2's per-kind arm for their own kinds; every
  other T2 arm stays with `act-report-remainder`, and T2 stays part.
- **T5** reserves outcome vocabularies per act kind and already names the
  managed-mutation, record-import and subject-evaluation entries.
  `RecordMutationEntry` is a fourth such entry on which `byte-locator-untested`
  must be unspellable. T5 belongs to `url-retrieval`; this design states the
  reservation and does not select the row.

## 3. The operations

### 3.1 `delete` — single root, on `CorpusWriter`

```python
def delete(self, ref: str, *, actor: str, observer: str, instrument: str) -> ActReport: ...
```

It resolves `ref` under the lock, removes exactly that record's file through
one engine effect, and mints a `delete` act-report.

**Inbound references do not prevent deletion.** `delete` performs no
referential check at all: it does not enumerate the records that name its
target, and the existence of such records — however many — is not a refusal
condition. Deletion is a storage operation, not an epistemic one. This is
forced by the rows: S5 and R23 select *delete the producing run*, *delete the ancestor*, and
*delete the divergent producer*, and then assert the basis entry goes
unresolved, `lineage-incomplete`, independence `not-certified`, and the belief
digest moves. A referential-integrity refusal would make every one of those
arms unrunnable. Withdrawing a record's epistemic force is what **retraction**
is for; `delete` is what removes bytes.

The corpus keeps **no tombstone**. S5's *"indistinguishable from one where that
run never existed"* and R23's §11.14 residue require exactly that.

**Excluded kinds**, refused as a closed list rather than by a general rule:

| kind | why |
|---|---|
| `act-report` | T8's *no ordinary API deletes a report* (§2.3) |
| coordination revision records | cut 14's revision family owns its own lifecycle |
| `holdings-observation` | owned exclusively by the holdings operations; the managed payload delete is `holdings.delete`, which records an `absent` observation rather than removing one |

Every other stored kind is deletable, retractions included — the log design's
5a witness (*"deleted retraction: committed creation, no committed removal,
absent record → refuted"*) is written for a retraction that can go missing.

**The managed/raw asymmetry is the point of the whole cut.** A managed deletion
is a committed removal transition in the chain; a raw `unlink` is not:

| | log verification | corpus read, admission, belief |
|---|---|---|
| managed `delete` | `validated`, with a `record-removed` warning finding, and `failing-verification-removed` at **error** severity where a held copy claiming that path carries a failing verdict | indistinguishable |
| raw `unlink` | **`refuted`** — the disk surface disagrees with the replayed head | indistinguishable |

Both halves already exist: `world/verify.py`'s `_removal_findings` and
`_classification` for the first, `replay`'s head disagreement for the second.
Neither is visible to belief, which is what kernel §8.7's bound means and what
G8's and C6's negatives assert.

### 3.2 `move` — two roots, destination-first

```python
def move(source: CorpusWriter, destination: CorpusWriter, ref: str, *,
         actor: str, observer: str, instrument: str) -> tuple[Node, ActReport, ActReport]: ...
```

Preconditions, in refusal order, all evaluated under both locks:

1. `ref` resolves in `source`;
2. `ref`'s kind is not an excluded kind (§3.1);
3. **contract agreement** at the destination (§5);
4. the destination holds no record at that canonical address — a move into a
   corpus already holding one is a `consolidate`, and refuses here.

Then: append an intent in each root, **create in the destination**, **delete
from the source**, publish a fulfilling `move` act-report in each root.

The order is load-bearing. `uid`, canonical address, `deprecated_ids` and every
inbound reference are untouched — addresses have been location-free since the
address ruling — so a move changes only location, both corpus-state identities
move, and `belief_input_digest` does not.

### 3.3 `consolidate` — the duplicate-location exit

```python
def consolidate(inputs: Sequence[tuple[CorpusWriter, str]], *, keep: tuple[CorpusWriter, str],
                rationale: str, actor: str, observer: str, instrument: str) -> tuple[Node, tuple[ActReport, ...]]: ...
```

Refusal order:

1. at least two inputs, at distinct `(root, ref)` positions;
2. every input resolves in its named corpus;
3. **every input is at one canonical address** — two different addresses is a
   coreference question and refuses here. One `uid` under two different
   addresses is world corruption (W8b); `consolidate` is *not offered* for it,
   and refuses on this precondition rather than on a corruption check;
4. `keep` is one of the inputs;
5. contract agreement at the surviving corpus (§5).

**Reconciliation rule.** The survivor is `keep`'s **whole authored record**,
carrying `keep`'s `uid`. Outgoing relations are **unioned** across inputs.
Lineage bases are **preserved**, unioned into the tagged basis — divergent
bases both survive as `conflict`, and no field-selection path chooses between
them. `deprecated_ids` are unioned from the inputs; **no live address is newly
deprecated**, because no address retires. No redirect is written, no inbound
reference is rewritten, no `coreference-attestation` is written, and no
coreference balance moves.

On `uid`: shared across inputs → preserved; distinct → `keep`'s survives, the
others cease to be live, and **no third is minted**. The choice of `keep` and
its `rationale` are the **recorded judgement** the address ruling's limitation
4 requires, carried in the `consolidate` act-report's entry (§4).

**Scope limit: two corpora, not one.** This design implements consolidation of
records held in **two readable corpora**. A single corpus holding two live
records at one canonical address is damaged in a way the ordinary indexed read
path is not built to open, and repairing it needs a lower-level recovery
scanner rather than a composition of two `CorpusWriter`s. That scanner is out
of scope and is stated as a limitation (§8), not claimed. W16's selected arms
are the two-corpora arms — *"Hold one canonical address in two corpora;
`consolidate`"* — so the selection is unaffected.

### 3.4 The lock-held mutation seam

`OperationLock` **is** reentrant per thread (`_writer_depth`, `_writer_owner`),
and its docstring says a writer may nest so that a `CorpusWriter` can keep its
end-to-end hold while its durable port takes the same root lock. So nesting is
safe, and `relocation.py` may hold both locks and call inward.

It nonetheless calls **internal lock-held operations**, not the public
`add`/`delete`, for a different reason: intent pairing. A public `delete`
mints its own intent and its own terminal report, and a move needs exactly one
paired intent and one fulfilling report **per root** for the whole operation.
The internal seam is the minimum that admits a caller-supplied intent:

- `_add_locked(node, intent)` — the create half, and
- `_delete_locked(ref, intent)` — the remove half,

each performing its own read, refusal, plan and execution, with the public
methods becoming thin wrappers that mint an intent and delegate.

**Lock discipline.** Acquire each **distinct resolved root path exactly once**,
in sorted order. Sorting makes two opposing relocations deadlock-free;
deduplicating on the resolved path is what makes a same-root consolidation
correct, and reentrancy makes an accidental second acquisition harmless rather
than load-bearing.

### 3.5 Legal crash prefixes

Neither operation is one transaction — `atoms` §12.2 keys an engine root on a
corpus root, so two corpora are two chains. Each operation's partial states are
enumerated and each is legal:

**`move`**

| durable point reached | observable state |
|---|---|
| destination intent only | unfinished operation in the destination, record still solely in the source |
| destination create | **duplicate location** — one canonical address in two corpora |
| source delete | move complete, reports outstanding |
| both reports | finished operation |

The one interesting prefix is world §5's `duplicate location`, whose designed
exit is `consolidate` — in this same design. A move therefore never loses a
record at any interruption point, which is the argument for the two operations
sharing a cut.

**`consolidate`**

| durable point reached | observable state |
|---|---|
| intents only | unfinished operations, inputs unchanged, still duplicate location |
| survivor written at `keep`'s position | still duplicate location, survivor now carrying the unioned relations and bases |
| non-surviving inputs deleted | consolidation complete, reports outstanding |
| all reports | finished operation |

Every prefix is either the pre-state or the duplicate-location state, so a
re-run of the same `consolidate` is the recovery. There is no compensation
transaction and no automatic resumption; the repair is an explicit second call.

## 4. Act reports and the recorded judgement

`RecordMutationEntry` carries `subject` (the affected ref) and an outcome
drawn from a vocabulary reserved to these kinds:

- `moved` — source corpus, destination corpus, ref;
- `consolidated` — the inputs, the kept position, the retired `uid`s, and the
  `rationale`; this entry **is** the recorded judgement;
- `removed` — the ref and the kind removed.

`byte-locator-untested` is unspellable on it (§2.4). No API accepts an
authored report; these are boundary-minted like every other.

## 5. Contract agreement at relocation

D7 rule 3 already reads **"Move and consolidate"** — this design implements
the rule, it does not extend it. A relocation into a receiving corpus is
refused unless, for the relocated node:

- the receiving corpus pins the **same** `science_contract`, regardless of
  which facets the node carries — a node with no domain facets at all is still
  governed by the base contract; and
- for **every namespace the node's facets use**, the receiving corpus's profile
  resolves to **exactly one** identity and that identity **equals** the source's.

A **missing** pin refuses. D7 rule 2 requires a namespace to resolve to exactly
one contract identity; a corpus that pins nothing for a used namespace does not
satisfy that, and "not different" is too weak a test.

This is what preserves W5: a permitted relocation never crosses a contract
boundary, so it never changes the consulted set, so `belief_input_digest` is
unchanged.

## 6. The two cuts

### 6.1 The relocation cut

| row | arms | reading |
|---|---|---|
| **W5** | move a `source` between corpora — `uid`, canonical address, `deprecated_ids`, every inbound reference and `belief_input_digest` unchanged; then move a **dataset in the producers map** and assert the digest still unchanged though the address map and both corpus-state identities moved, so re-deriving mints a new receipt naming the same snapshot | full |
| **W16** | one address; relations unioned; divergent lineage bases both preserved; no redirect, no inbound rewrite, no new `deprecated_ids`, no `coreference-attestation`, no balance moved; `uid` shared → preserved, distinct → one survives with no third minted; refusal on two different addresses; not offered for one `uid` under two addresses, refusing on the one-address precondition | part — its *conflict survives deleting either producing run* arm needs the deletion cut |
| **G3** | the negative alone: move an entity between corpora, digest unchanged — the member is the producer snapshot, not the index carrying it | closes G3 |
| **D7** | the W5-preservation producers-map move; the domain-facet move refusal; the base-`science_contract` refusal for a node with no domain facets; the same two refusals for cross-corpus `consolidate`; the missing-pin refusal | closes D7 |
| **C3** | the in-coverage corpus move: content identities unchanged → digest unchanged, receipt records the new states | move clause only; C3 stays part for `correction-remainder` |
| **R23** | *location is not evidence* and *the receipt is not a belief input* — both covered corpus-state identities change, the producers map does not, the digest is unchanged; the consolidate clauses over the tagged basis | part |
| **M3** | `consolidate` two equal-basis replicas of one retraction in two corpora while counter-retraction `R` targets it → succeeds, content identity unchanged, `R` neither rewritten nor re-minted | replica arm only |
| **T2** | one started operation, one intent, one terminal record, for the `move` and `consolidate` kinds | part |

R23's alias clause is read as amended: the alias was retired 2026-08-08, so the
arm is the move alone.

### 6.2 The deletion cut

| row | arms | reading |
|---|---|---|
| **G2c** | the §3.3 lifecycle-table walk re-run over durable records under the amended "active" (the standing-retraction clause), plus the raw-deletion negative | closes G2c |
| **G8** | raw-delete the failing verification → the assessment returns to admitted, undetected on read; the audit **refutes** it, while a managed deletion of the same record **validates** with its removal findings | closes G8 |
| **C6** | the same over verification retraction: raw deletion still restores admission undetectably | closes C6 |
| **R5** | negative (a): destroy the last held copy through `holdings.delete`'s managed act recording an `absent` observation → no longer held, eligibility fails, admission changes | closes R5 |
| **S5** | delete an ancestor named by a basis → `lineage-incomplete`, `not-certified`, digest moved, no belief rise; delete a divergent producer → certificate restored, belief may rise, indistinguishable from one where that run never existed (§7) | deletion half; cross-corpus reach stays with `world-resolution` |
| **R23** | delete the producing run and the ancestor — stored ref and `null` resolution recorded separately; a second surviving run does not repair the first basis; the §11.14 residue; the conflict surviving either deletion; the audit detecting the forged `single(A)` while `B`'s run stands, and its semantic contradiction finding disappearing once `B`'s run is deleted too (§7) | part |
| **W16** | its remaining arm from §6.1 | closes W16 |
| **C1** | re-read under §2.2's narrowing: retraction remains additive and its operation never edits, removes or re-addresses its target | re-read |
| **T8** | its delete clause, re-read against `delete`: no ordinary API deletes a report | re-read |
| **T2** | the `delete` kind's per-kind arm | part |

### 6.3 The ride-alongs

**R19 — part, and its cross-corpus arm defers now rather than at planning
time.** Selected: explicit-import derivation validation over complete closure
evidence, with refusal before any write; transition (b) end to end — import a
forged verification whose artifacts do not resolve, mount them, assert
admission is *still* unchanged until an audit runs, that the audit emits the
contradiction finding and **mints nothing**, that a separate constructor act
naming its own cut and epoch mints the superseding verification, and that
admission changes because of that node; negatives (d) and (e) with their
log-backed raw-write detection.

Deferred to `world-resolution`: *"the recomputation resolves across corpora
through the world resolver."* `world/read.py`'s `resolve_address` returns
`Resolved | NotPresent | Unknown` — an address's **location**, not the records
a semantic recomputation would need. There is nothing here to recompute from,
so R19 stays part.

**R22 — part.** Negative (c)'s explicit-import clause — import recomputes the
assessment facet from the run and refuses a mismatch — and its
caught-only-under-audit clause. The unresolvable-interpretation-rule refusal
stays with `contract-cut`.

**M1 — the instrumented resolver, which is construction and not only a test.**
`belief.Records` is constructed nowhere in the package today, so no
corpus→belief gathering layer exists to instrument. This cut builds one, and
the resolver's boundary is the **complete local belief-evaluation input
bundle**, not `Records` alone:

- the matched records — assessments, runs, verifications, propositions;
- the producer snapshot and its identity;
- the contracts and corpus pins consulted;
- the retraction enumeration and its coverage declaration; and
- the **read trace** itself, recorded at read time.

Selected: the containment assertion over a corpus exercising every closure
member, and the sabotage arm — one extra value read **through the resolver**,
nothing else changed, and the check must fail. M1's stated scope limitation is
preserved verbatim and not closed: a read that never crosses the resolver — a
module-level constant, an environment lookup, a cached global, a file opened
directly — is invisible and passes.

**M3 — part.** A raw-written cyclic configuration classified **malformed by
audit before any standing or belief evaluation**, with no reading invoked on
it; and the admission-order negative — no topological rank is stored, so
re-admitting the same records in a different order leaves every identity and
the belief digest unchanged. The coreference arm stays with
`world-resolution`; the concrete-cycle arms stay a banked limitation.

**M5 — full.** Its prior clauses re-run durably: restriction-only,
quantifier-only, and present-versus-absent qualification identity; the
qualifier-map sabotage; and the key-order negative.

## 7. Two audit claims, narrowed

Both of these are places where the obvious wording would overstate.

**S5's *"no test distinguishes"* is scoped to the epistemic readings** — the
corpus read, the lineage traversal, admission, and belief. It is **not** a
claim about log verification, which distinguishes a managed deletion perfectly
well: the committed removal transition is in the chain and `record-removed` is
in the findings. The row's claim is that belief retains no residue of a deleted
run, not that the deletion left no trace anywhere.

**R23's *"the audit reports nothing"* means the semantic contradiction finding
disappears.** After `B`'s producing run is deleted too, every surviving route
resolves and no record of `B` remains, so the forged `single(A)` is no longer
contradicted by anything. The **log** audit still reports the committed
removals through `_removal_findings`. The arm asserts the absence of the
contradiction finding, not the absence of all findings.

## 8. Limitations

- **L13 is not closed and must not be implied.** Removal classification matches
  a held copy by **claimed path**, never by bytes, so the copy claiming a path
  may be a different version than the transition removed. L13 stays tier 2
  behind the `atoms` blob-read seam.
- **Same-corpus duplicate location is not repaired.** `consolidate` handles two
  readable corpora; a single corpus holding two live records at one canonical
  address needs a recovery scanner this design does not build (§3.3).
- Ordered, deduplicated two-lock acquisition is **in-process only**.
  Cross-process single-writer operation remains a stated deployment obligation,
  detected loudly rather than prevented.
- An interrupted `move` is repaired by an explicit `consolidate`, and an
  interrupted `consolidate` by re-running it. There is no compensation
  transaction and no automatic resumption.
- `consolidate`'s `keep` selection is a recorded judgement, not a derivation
  (address ruling limitation 4).
- M1's resolver bound (formal model limitation 1) and M3's concrete-cycle arms
  (banked at cut 5) remain limitations, ranked nowhere.
- Rows still **part** after both cuts, with their owners: R23 (rules-store →
  `contract-cut`; snapshot, coverage, divergence → `world-resolution`), C3
  (coverage clauses → `correction-remainder`), S5 (cross-corpus reach →
  `world-resolution`), M3 (coreference arm → `world-resolution`), R19 and R22
  as §6.3 states, T2 (remaining arms → `act-report-remainder`).

## 9. Shared files, under roadmap concurrency rule 3

Rewritten by every lane, and named here: `python/src/beliefs/errors.py`,
`python/tests/test_designs_corpus.py`, the adoption ledger, the implementation
roadmap, and the guide index.

Named additionally by this lane:

| file | why | other claimant |
|---|---|---|
| `world/registry.py` | corpus-state identity moves on both sides of a relocation | the `world-read` lane, which reads it |
| `world/verify.py` | the deletion cut's semantic-audit arms | the `world-read` lane |
| `report.py` | the three new operation kinds and `RecordMutationEntry` | the `acquisition` lane, which owns T1/T2/T4 |
| `corpus.py`, `stored.py` | `delete`, the internal lock-held seam, the rewritten concurrency docstring | none |

The later merge resolves toward the earlier one.

## 10. Banking choreography

The banking change carries this design, promoted into `docs/designs/`, together
with the relocation cut's frozen document. In the same change: the ledger's
`consolidate-family` row note; the design-corpus guard's design count, README
count/table/date and `_COUNT_WORDS`; the dated C1 amendment in the
correction-lifecycle design (§2.2); and the dated operation-enum amendment in
the act-report design (§2.4).

Each cut's results record is a separate commit that rewrites the ledger's
`Current state` table and the roadmap, one at a time (concurrency rule 2). The
rulings ledger is committed to a tracked path before the worktree is removed.

## 11. Alternatives rejected

**Deletion that refuses on inbound references.** Rejected because it makes
S5's and R23's selected arms unrunnable — every one of them deletes a record
another record names, and then asserts what the dangling reference does.

**A corpus-visible tombstone.** Rejected because S5 and R23 assert the
resulting state is indistinguishable from one where the run never existed. The
chain's committed removal transition is the history.

**Refusing deletion of retraction targets to preserve C1's wording.** Rejected
as a referential check in disguise, and because C1's real claim is about the
retraction family, which the §2.2 amendment states directly.

**Source-first `move`.** Rejected because its crash prefix is a record present
in neither corpus — unrecoverable loss — where destination-first's crash prefix
is a duplicate location this design repairs.

**A world-level move record with a resumption seam.** Rejected for this cut: it
adds a new world kind and a resume-before-mint seam, and puts the operation on
`world/registry.py`, maximizing collision with the `world-read` lane. The
destination-first ordering already makes loss unreachable.

**`consolidate` and `move` as `CorpusWriter` methods.** Rejected because a
writer bound to one root cannot honestly own an operation over two, and
`corpus.py` is already the lane's largest file.

**Subclassing `CorpusWriter` for the two-root case.** Rejected on the house
rule: composition over inheritance. `relocation.py` holds two writers.
