# The world-changing families: consolidate, move, and managed deletion

**Date:** 2026-09-03

**Status:** Banked 2026-09-03. Relocation cut frozen as conformance cut 16; the deletion cut is not yet frozen.

**Scope:** The `consolidate-family` boundary of
[`../plans/2026-08-29-implementation-roadmap.md`](../plans/2026-08-29-implementation-roadmap.md),
with its `run-boundary-remainder` and `formal-model-remainder` ride-alongs.

**Prerequisite:** The family adapters of
[`2026-08-19-family-adapters-design.md`](2026-08-19-family-adapters-design.md),
whose §2.4 deferred exactly these three families "to their own cut with the
world index" and whose §5.3 requires this design to replace its concurrency
ruling.

## 1. Decision

Add three world-changing operations. `delete` joins `CorpusWriter` beside
`add`; `move` and `consolidate` live in a new module `beliefs.relocation`
that **composes** two `CorpusWriter`s and subclasses neither. Every mutation
remains an `atoms` effect executed by the certified engine under the per-root
operation lock.

`move` and `consolidate` are **boundary operations**: each mints an intent and
a fulfilling act-report in each root it touches. `delete` is an **ordinary
write**, like `add` — no intent, no report, one engine effect (§3.1 gives the
reason, and it is the whole point of the deletion cut).

The boundary discharges across two freezes, in this order:

| freeze | operations | rows |
|---|---|---|
| the **relocation** cut | `move`, `consolidate` | W5, W16 (part), G3, D7, C3's move clause, R23's move and consolidate clauses, M3's replica arm, T2's per-kind arms, T8 (re-read) |
| the **deletion** cut | `delete` | G2c, G8, C6, R5, S5's deletion half, R23's deletion clauses, W16's remainder, C1, T8, M11, M13 (re-reads); then R19, R22, M1, M3, M5 |

Cut numbers are claimed at freeze, not here (roadmap concurrency rule 1). The
relocation cut freezes first and takes the lower number; the deletion cut
names the relocation cut's acceptance runner as its prefix (rule 5).

## 2. What this replaces and what it amends

### 2.1 The create-only concurrency ruling lapses

Family adapters §5.3 argued that a target resolving under the lock cannot be
made missing "because no family deletes or moves it." That argument dies with
this design, and `corpus.py`'s `CorpusWriter` docstring already says so in
advance: *"A future deletion-capable family must re-own this question; neither
argument transfers to it."* **§3.6 is its replacement**, carried into the
family-adapters design as a dated amendment at banking (§10), with the
docstring rewritten in the same change.

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

### 2.3 T8 is re-read twice, and act-reports are excluded from all three operations

T8 is closed and its last clause is *"Attempt to edit, supersede, and delete a
report through every ordinary API; assert no such path exists."* All three
operations are new ordinary APIs, and two of them can remove a record from a
corpus: `delete` directly, `move` and `consolidate` as the second half of their
own effects. So `act-report` is an **excluded kind for every one of them**
(§3.0), and T8's clause is re-read twice:

- in the **relocation** cut, against `move` and `consolidate`; and
- in the **deletion** cut, against `delete`.

This is a re-read, not a reopening: the row's claim is unchanged and still
holds; what changed is the set of APIs the word "every" quantifies over.

### 2.4 Four closed act-report grammars are amended

The act-report design closes several vocabularies "extended only by amendment"
(its §2, §2.1, §2.2). This design amends four of them, and §10 carries all four
as one dated amendment:

1. **The operation enum.** `report.OPERATION_KINDS` —
   `("acquisition", "audit", "import", "re-check", "run-attempt")` — gains
   **`consolidate`** and **`move`**, and *not* `delete`, which mints no report
   at all (§3.1).
2. **The act-kind enum.** §2.1's closed list — `pure-look` |
   `managed-mutation` | `declaration-pin` | `subject-evaluation` |
   `record-import` | `run-attempt` — gains **`record-mutation`**, the entry kind
   `RecordMutationEntry` carries.
3. **The subject grammar.** §2.1 admits a canonical location, a record ref, a
   spec identity, or a recipe identity. A `record-mutation` entry's subject is a
   **record ref together with the corpus it is read from or written to** — a
   bare ref cannot name a side of a two-root operation.
4. **The outcome vocabulary.** §2.2 gives each act kind its own; `record-mutation`
   gets `moved` and `consolidated` (§4), and nothing is borrowed from another
   kind.

A fifth clause is widened rather than extended: §2.1's operation model knows
only single-root operations, and §3.5 needs a **composite root-local
operation** — one `event_token`, one `opened_at`/`closed_at`, one intent and one
terminal report **per touched root**. The amendment states that model and T2's
scope under it.

Two consequences cross into the acquisition lane and are named here rather
than discovered at merge:

- **T2** — *"Run each operation kind to success"* — now quantifies over seven
  kinds. The relocation cut selects T2's per-kind arm for `move` and
  `consolidate`, read **root-locally** (§3.5). Every other T2 arm stays with
  `act-report-remainder`, and T2 stays part.
- **T5** reserves outcome vocabularies per act kind and already names the
  managed-mutation, record-import and subject-evaluation entries.
  `record-mutation` is a fourth such kind on which `byte-locator-untested`
  must be unspellable. T5 belongs to `url-retrieval`; this design states the
  reservation and does not select the row.

### 2.5 M11 and M13 are re-read for the claim restore seam

`decode.claim_from_stored` (§6.3) is a **new public route to a `Claim`** and a
new deserialization entry point. M11 and M13 are both closed, and both were
closed against a surface that had exactly one such route. Adding a second
without re-reading them would rest their closure on evidence that predates it —
the same error §2.3 corrects for T8. The deletion cut therefore re-reads both,
with these arms:

**M13 — opacity and the confined wire type.**

- `claim_from_stored`'s signature neither accepts nor returns a `WireClaim`: it
  takes a `Node` and returns `(Claim, BindingCheckReceipt)`. The wire value is
  constructed and consumed **within** `decode.py`.
- It **delegates to `decode_claim`** rather than typing the claim itself.
  Sabotage: give the helper its own typing path and assert the check fails —
  otherwise "one place, once" has quietly become two places.
- The brand chain M13's 2026-08-06 extension requires is unbroken through the
  new route: the returned `Claim` is one the validated constructor minted, so
  `π_claim` accepts it, and a `Claim` reaching `π_claim` by this route rather
  than by `decode_claim` directly is not distinguishable from one that did.

**M11 — a function of its arguments, refusing rather than repairing.**

- Determinism across the new route: the same `⟨Node, ProfileSpec,
  ResolutionSnapshot⟩` restored twice, in different processes and different
  checkouts, yields an identical result.
- Availability stays a **parameter**. Sabotage: let `claim_from_stored` build
  or default its own `ResolutionSnapshot` and assert two holders now restore
  the same bytes differently.
- **Refusal before delegation, never repair and never a crash.** Each
  ill-formed input in turn — a node of the wrong kind, a proposition facet with
  a missing field, an extra field, or a malformed one — is **refused with
  nothing minted**, and refused *by the helper before it delegates*, rather
  than repaired into a well-formed wire value or allowed to raise an unrelated
  `KeyError`/`AttributeError` on the way into `decode_claim`. This is the arm
  that matters most: a restore helper is exactly the place where "be liberal in
  what you accept" would silently defeat M11's whole claim.
- M11's negative is unchanged and not re-run here: a raw-written malformed
  claim remains an audit finding, the boundary bypassed rather than defeated.

## 3. The operations

### 3.0 Excluded kinds, common to all three

No world-changing operation accepts a record of these kinds, as an input, a
move subject, or a consolidation input:

| kind | why |
|---|---|
| `act-report` | T8's *no ordinary API edits, supersedes or deletes a report* (§2.3) |
| coordination revision records | cut 14's revision family owns its own lifecycle |
| `holdings-observation` | owned exclusively by the holdings operations; the managed payload delete is `holdings.delete`, which records an `absent` observation rather than removing one |

Every other stored kind is in scope, retractions included — the log design's
5a witness (*"deleted retraction: committed creation, no committed removal,
absent record → refuted"*) is written for a retraction that can go missing.

### 3.1 `delete` — an ordinary write, and it mints nothing

```python
def delete(self, ref: str) -> None: ...
```

It resolves `ref` under the lock, refuses an excluded kind, and removes exactly
that record's file through one engine effect.

**It mints no intent and no act-report.** This is forced by the guarantee the
deletion cut exists to read. An act-report is a **live corpus node**: it is
visible through `ReadView` and it participates in `corpus_state_identity`. A
`delete` that minted one would leave a record behind that a raw `unlink` does
not, and managed and raw deletion would be trivially distinguishable on an
ordinary corpus read — destroying G8's and C6's negatives, S5's *"no test
distinguishes"*, and this design's own claim that the committed removal
transition is the entire history. `delete` therefore mirrors `add`, which mints
no intent and no report either, and the operation enum gains no `delete` kind.

**Inbound references do not prevent deletion.** `delete` performs no
referential check at all: it does not enumerate the records that name its
target, and the existence of such records — however many — is not a refusal
condition. Deletion is a storage operation, not an epistemic one. This is
forced by the rows: S5 and R23 select *delete the producing run*, *delete the
ancestor*, and *delete the divergent producer*, and then assert the basis entry
goes unresolved, `lineage-incomplete`, independence `not-certified`, and the
belief digest moves. A referential-integrity refusal would make every one of
those arms unrunnable. Withdrawing a record's epistemic force is what
**retraction** is for; `delete` is what removes bytes.

The corpus keeps **no tombstone**. S5's *"indistinguishable from one where that
run never existed"* and R23's §11.14 residue require exactly that.

**The managed/raw asymmetry is the point of the whole cut.**

| | log verification | corpus read, admission, belief |
|---|---|---|
| managed `delete` | `validated`, with a `record-removed` warning finding, and `failing-verification-removed` at **error** severity where a held copy claiming that path carries a failing verdict | indistinguishable |
| raw `unlink` | **`refuted`** — the disk surface disagrees with the replayed head | indistinguishable |

Both halves already exist: `world/verify.py`'s `_removal_findings` and
`_classification` for the first, `replay`'s head disagreement for the second.
Neither is visible to belief, which is what kernel §8.7's bound means.

### 3.2 `move` — two roots, destination-first

```python
def move(source: CorpusWriter, destination: CorpusWriter, ref: str, *,
         actor: str, observer: str, instrument: str,
         opened_at: str, closed_at: str) -> tuple[Node, ActReport, ActReport]: ...
```

`opened_at` and `closed_at` are caller-supplied for the operation as a whole and
passed **identically to both roots**: the operation opened once and closed once,
and the two reports describe one operation from two sides. Both reports are
returned, destination first.

Preconditions, in refusal order, all evaluated under both locks:

1. the two roots resolve to **distinct** paths;
2. `ref` resolves in `source`;
3. `ref`'s kind is not excluded (§3.0);
4. **contract agreement** at the destination (§5);
5. the destination holds no record at that canonical address — a move into a
   corpus already holding one is a `consolidate`, and refuses here.

Here “holds at that canonical address” means exact canonical resolution:
`destination.read_view.resolve(node.id) == node.id`. A different record claiming
`node.id` only as a deprecated alias is not a duplicate location, nor is a
different canonical record with the same `uid`; the destination's ordinary
add preflight classifies either identity claim as `CollisionRefused`. That
no-write preflight runs before either intent, while `_add_locked` repeats the
same checks at the destination data step.

Then the sequence of §3.5. `uid`, canonical address, `deprecated_ids` and every
inbound reference are untouched — addresses have been location-free since the
address ruling — so a move changes only location, both corpus-state identities
move, and `belief_input_digest` does not.

### 3.3 `consolidate` — the duplicate-location exit, exactly two records

```python
def consolidate(keep: tuple[CorpusWriter, str], other: tuple[CorpusWriter, str], *,
                rationale: str, actor: str, observer: str, instrument: str,
                opened_at: str, closed_at: str) -> tuple[Node, ActReport, ActReport]: ...
```

Exactly two records in two **distinct resolved roots**. The API is not N-way
and takes no sequence: this design's scope is two readable corpora (below), and
an arbitrary-arity signature would advertise crash states §3.5 does not
enumerate.

Refusal order:

1. the two roots resolve to **distinct** paths — a same-root pair refuses (see
   the scope limit below);
2. both inputs resolve in their named corpora;
3. **neither input is an excluded kind** (§3.0) — without this, two replicated
   act-reports at one address could be consolidated, removing one of them
   through an ordinary API and violating T8;
4. **both inputs are at one canonical address** — two different addresses is a
   coreference question and refuses here. One `uid` under two different
   addresses is world corruption (W8b); `consolidate` is *not offered* for it,
   and refuses on this precondition rather than on a corruption check;
5. contract agreement at `keep`'s corpus (§5).

**Reconciliation rule.** The survivor is `keep`'s **whole authored record**,
carrying `keep`'s `uid`, rewritten in place at `keep`'s existing `(uid, id)`.
Outgoing relations are **unioned** across both inputs. Lineage bases are
**preserved**, unioned into the tagged basis — divergent bases both survive as
`conflict`, and no field-selection path chooses between them. `deprecated_ids`
are unioned from the inputs; **no live address is newly deprecated**, because
no address retires. No redirect is written, no inbound reference is rewritten,
no `coreference-attestation` is written, and no coreference balance moves.

The union is order-independent and idempotent, which is what makes re-running a
`consolidate` safe over the prefixes in which both inputs still resolve — steps
1 through 4 of §3.5, and no further.

On `uid`: shared across the inputs → preserved; distinct → `keep`'s survives,
the other ceases to be live, and **no third is minted**. The choice of `keep`
and its `rationale` are the **recorded judgement** the address ruling's
limitation 4 requires, carried in the `consolidated` entry (§4).

**Scope limit: two corpora, not one.** A single corpus holding two live records
at one canonical address is damaged in a way the ordinary indexed read path is
not built to open, and repairing it needs a lower-level recovery scanner rather
than a composition of two `CorpusWriter`s. That scanner is out of scope, the
same-root pair refuses at precondition 1, and the gap is stated as a limitation
(§8) rather than claimed. W16's selected arms are the two-corpora arms — *"Hold
one canonical address in two corpora; `consolidate`"* — so the selection is
unaffected.

### 3.4 The lock-held mutation seam

`OperationLock` **is** reentrant per thread (`_writer_depth`, `_writer_owner`),
and its docstring says a writer may nest so that a `CorpusWriter` can keep its
end-to-end hold while its durable port takes the same root lock. So nesting is
safe, and `relocation.py` may hold both locks and call inward.

It nonetheless calls **internal lock-held operations**, not the public methods,
because a relocation needs exactly one intent and one fulfilling report per
root for the operation as a whole, and the public methods own their own:

| seam | used by | shape |
|---|---|---|
| `_add_locked(node)` | `move`'s destination half | the create path, with `_refuse_already_minted` intact |
| `_delete_locked(ref)` | `move`'s source half, `consolidate`'s non-surviving half | the remove path; builds `DeleteOp(path, expected_digest)` |
| `_replace_locked(node)` | `consolidate`'s survivor | replacement at an existing `(uid, id)`; the digest precondition is the substrate's |

**No data seam receives an intent digest.** Each executes through the
operation port's ordinary `execute`, which fulfills nothing; only the report
transaction calls `execute_fulfilling`. This is not a convenience: the digest's
sole use is registering a fulfillment, so handing it to a data transaction
would register that transaction as the operation's first fulfillment and leave
the report as a forbidden second — the exact state T2's *"attempt a second
fulfilling registration on one intent"* arm refuses. It is also what makes
§3.5's tables true: both operations are still **unfinished** after their data
transactions, and publication is what closes them.

`_replace_locked` is a **distinct path and not a relaxation of `add`**.
`_refuse_already_minted` deliberately refuses a create at an existing
`(uid, id)`, and `revise` reaches replacement only through its display-only
allowlist; neither is weakened.

**Replacement collision preflight is safe and required** *(corrected
2026-09-04, on inspecting `Index.assert_addable`)*. The index explicitly
permits the existing same `(uid, id)` pair and refuses only an identity claim
owned by another uid. `_replace_locked` therefore runs `_refuse_collision`
after rendering, in `_refuse` order; `_refuse_already_minted` is the sole
ordinary admission check it omits. `consolidate` calls that same no-write
replacement preflight before either intent, so a deprecated id contributed by
the other input cannot strand two intents when it collides in the kept root.

**The digest precondition is the substrate's, not a Science-layer parameter**
*(corrected 2026-09-03, on inspecting the write API)*. `Corpus.add` selects
`ReplaceOp` for an existing `(uid, id)` and takes its `expected_digest` from
the pre-plan read of the current file — `revise` reaches replacement exactly
this way, and no Science-layer caller supplies a digest anywhere in the
package. `_replace_locked(node)` therefore takes no digest argument; the race
refuses through family-adapters §5.2's existing two-observation mapping, which
is unchanged. `_delete_locked` does need one, because `DeleteOp(path,
expected_digest)` is constructed directly: it is the bare 64-character
`member_content_digest` of the record's rendered bytes as read under the lock,
never a `sha256:`-prefixed identity.

**The seams admit the kind they are relocating** *(added 2026-09-03, on tracing
M3's replica arm)*. `_refuse_family_kinds` refuses a `retraction` unless its
`admitted_kind` argument names one — that is the guard keeping retractions
entering through `retract`. A relocation neither mints nor authors a record: it
carries an existing one, whose kind was already admitted when it was minted. So
both seams pass `admitted_kind=node.kind`, without which M3's arm —
`consolidate` over two equal-basis retraction replicas — is unreachable. This
opens nothing else: the guard's refusals for coordination kinds,
`holdings-observation` and `act-report` consult no `admitted_kind` and stay
absolute, agreeing with §3.0's excluded list.

**Lock discipline.** Acquire each **distinct resolved root path exactly once**,
in sorted order. Sorting makes two opposing relocations deadlock-free;
deduplicating on the resolved path is the rule, and reentrancy makes an
accidental second acquisition harmless rather than load-bearing.

### 3.5 The cross-root protocol and every durable prefix

Neither operation is one transaction — `atoms` §12.2 keys an engine root on a
corpus root, so two corpora are two chains and two operation ports.

**One operation, one event token, two root-local intents and reports.** The
operation opens once, and its single token is carried in **both** root-local
intents and **both** reports. This is what makes the two halves uniquely
correlated: `(source corpus, destination corpus, ref)` does not distinguish two
identical relocations run in succession, and a token does. It leaves T8 intact —
that row separates two *operations* with distinct tokens, and the two reports of
one operation still carry different entries and so different identities (act
report §2.3).

**T2 is read root-locally**: each root sees exactly one intent and exactly one
terminal record fulfilling it. That is the only reading under which a two-root
operation satisfies a row written for one, and it is a genuine widening of the
banked act-report design, which knows only single-root operations. §10 carries
the dated amendment defining a **composite root-local operation** — one token,
one `opened_at`/`closed_at`, one report per touched root — and T2's scope under
it.

**`move`**, in order:

| # | step | state if interrupted after it |
|---|---|---|
| 1 | acquire both locks, sorted; validate every precondition | unchanged |
| 2 | append intent in the **destination** | destination operation unfinished; record solely in the source |
| 3 | append intent in the **source** | both operations unfinished; record solely in the source |
| 4 | destination data transaction — create | **duplicate location**; both unfinished |
| 5 | source data transaction — delete | move complete; both unfinished |
| 6 | destination report transaction, fulfilling | move complete; destination finished, source unfinished |
| 7 | source report transaction, fulfilling | finished |

**`consolidate`**, in order:

| # | step | state if interrupted after it |
|---|---|---|
| 1 | acquire both locks, sorted; validate every precondition | unchanged — still duplicate location |
| 2 | append intent in `keep`'s root | keep's operation unfinished; still duplicate location |
| 3 | append intent in the other root | both unfinished; still duplicate location |
| 4 | `keep` data transaction — `_replace_locked` the survivor | survivor carries the union; still duplicate location |
| 5 | other-root data transaction — delete the non-surviving input | consolidation complete; both unfinished |
| 6 | `keep` report transaction, fulfilling | complete; keep finished, other unfinished |
| 7 | other-root report transaction, fulfilling | finished |

Intents are appended in a fixed order — destination then source; `keep` then
other — so the prefix set is deterministic and the tables above are exhaustive.

Every `move` prefix is either the pre-state, the duplicate-location state, or a
complete move with reports outstanding: **a move loses nothing at any
interruption point**, which is the argument for the two operations sharing a
cut.

**Recovery per operation, per prefix.** The two operations do not share a
partition, because `move`'s own precondition 5 refuses once its destination
create has landed:

| interrupted after | state | data recovery |
|---|---|---|
| `move` steps 2–3 | record solely in the source | re-run `move` |
| `move` step 4 | **duplicate location** | call `consolidate` — `move` itself now refuses at precondition 5, which is correct: the state is no longer a move's pre-state, it is the state `consolidate` exists for |
| `move` steps 5–6 | data final | none needed; nothing to repair |
| `consolidate` steps 2–4 | still duplicate location | re-run `consolidate`; §3.3's idempotent union is what makes a re-run over an already-unioned survivor safe |
| `consolidate` steps 5–6 | data final | none needed; nothing to repair |

**Every recovery above repairs data only. None of them closes the interrupted
operation** *(stated 2026-09-03, on tracing the token)*. A re-run mints a
**fresh `event_token`** and is therefore a new operation with new intents; it
cannot adopt the interrupted operation's intents, and nothing else does either.
So any interruption at or after step 2 — the first intent append — leaves one or
two intents permanently unmatched, reading **unfinished** under T3, *whether or
not the data was subsequently repaired*.

That is the residue, and it is exactly the disposition family-adapters §5.4 gave
a stranded import: *"Retrying creates a new operation with a new intent and
cannot close the old one."* Recovery correlation — adopting an open intent and
minting the report that fulfills it — remains the log-consumer cut's, and this
design adds no compensation transaction and no resumption seam. A cut arm that
asserted a re-run "recovered the operation" would be false; the arms assert
repaired data **and** a stranded original intent, together.

### 3.6 The replacement concurrency ruling

This is what family-adapters §5.3 is amended to, and it is declared and tested
in both cuts rather than argued:

1. **Create-only targets are no longer monotone, so they are re-read.**
   `retract` and `supersede` re-resolve their target **under the lock,
   immediately before plan construction**, and refuse if it no longer resolves.
   They may not rely on a resolution taken earlier in the call, and they may not
   infer from "no family removes it" that it is still there. The relocation cut
   declares the arm for a target moved away; the deletion cut declares it for a
   target deleted. Local absence does not reveal whether the target never
   existed or was removed, so this final under-lock missing-target check uses
   `RelocationTargetMissing` for either history.
2. **Each distinct resolved root is locked exactly once, in sorted order.** Two
   opposing relocations therefore cannot deadlock, and a two-root operation
   holds both locks across its whole read-refuse-plan-execute sequence.
3. **The surviving hazard is crash, not concurrency, and its states are
   enumerated.** §3.5's tables are the complete prefix set for each operation;
   no other partial state is reachable, because every step is one engine
   transaction under both locks.
4. **Cross-process exclusion is unchanged.** It remains a stated deployment
   obligation, detected loudly rather than prevented.

## 4. Act reports and the recorded judgement

`RecordMutationEntry` carries `subject` (the affected ref) and an outcome drawn
from a vocabulary reserved to the two relocation kinds:

- `moved` — source corpus, destination corpus, ref;
- `consolidated` — both inputs, the kept position, **`retired_uids`**, and the
  `rationale`; this entry **is** the recorded judgement.

`retired_uids` is a **sequence, empty in the shared-`uid` arm** *(corrected
2026-09-03)*. §3.3 has two `uid` cases and only one retires anything: where the
inputs share a `uid` it is preserved and nothing is retired, and where they
differ exactly one ceases to be live. A mandatory single `retired_uid` could not
state the first case truthfully, and a sentinel empty string would be a silent
fallback standing in for a fact. An empty sequence says what happened.

There is no `removed` outcome, because `delete` mints no report (§3.1).
`byte-locator-untested` is unspellable on the entry (§2.4). No API accepts an
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
| **T2** | one started operation, one intent, one terminal record, **root-locally**, for the `move` and `consolidate` kinds | part |
| **T8** | its edit/supersede/delete clause re-read against `move` and `consolidate`: neither accepts an act-report as a subject or an input | re-read |

Boundary-invariant arms declared beside the rows: §3.6's re-resolution refusal
for a `supersede` and a `retract` whose target was moved away, and the sorted
dedup acquisition over a same-root pair.

R23's alias clause is read as amended: the alias was retired 2026-08-08, so the
arm is the move alone.

### 6.2 The deletion cut

| row | arms | reading |
|---|---|---|
| **G2c** | the kernel §3.3 lifecycle-table walk re-run over durable records under the amended "active" (the standing-retraction clause), plus the raw-deletion negative | closes G2c |
| **G8** | raw-delete the failing verification → the assessment returns to admitted, undetected on read; the audit **refutes** it, while a managed deletion of the same record **validates** with its removal findings | closes G8 |
| **C6** | the same over verification retraction: raw deletion still restores admission undetectably | closes C6 |
| **R5** | negative (a): destroy the last held copy through `holdings.delete`'s managed act recording an `absent` observation → no longer held, eligibility fails, admission changes | closes R5 |
| **S5** | delete an ancestor named by a basis → `lineage-incomplete`, `not-certified`, digest moved, no belief rise; delete a divergent producer → certificate restored, belief may rise, indistinguishable from one where that run never existed (§7) | deletion half; cross-corpus reach stays with `world-resolution` |
| **R23** | delete the producing run and the ancestor — stored ref and `null` resolution recorded separately; a second surviving run does not repair the first basis; the §11.14 residue; the conflict surviving either deletion; the audit detecting the forged `single(A)` while `B`'s run stands, and its semantic contradiction finding disappearing once `B`'s run is deleted too (§7) | part |
| **W16** | its remaining arm from §6.1 | closes W16 |
| **C1** | re-read under §2.2's narrowing: retraction remains additive and its operation never edits, removes or re-addresses its target | re-read |
| **T8** | its clause re-read against `delete`: no ordinary API deletes a report — and `delete` mints no report of its own, so it adds no report to delete | re-read |
| **M13** | §2.5's opacity arms against `claim_from_stored`: no `WireClaim` in or out, delegation to `decode_claim` with the sabotage, and the brand chain intact through the new route | re-read |
| **M11** | §2.5's decode arms against `claim_from_stored`: determinism across processes and checkouts, availability as a parameter with the ambient sabotage, and refusal before delegation on wrong kind and on missing, extra or malformed facet fields | re-read |

`delete` contributes **no** T2 arm: it opens no operation and mints no terminal
record (§3.1). The §3.6 re-resolution arm is declared here for a deleted target.

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

**M1 — the instrumented resolver, specified as a seam.** `belief.Records` is
constructed nowhere in the package today, so no corpus→belief gathering layer
exists to instrument. This cut adds one small module, `beliefs.evaluation`,
with this surface:

```python
ReadRef: TypeAlias = tuple[str, str]   # (member kind, ref); kinds below

@dataclass(frozen=True)
class EvaluationInputs:
    """`build_closure`'s argument set, plus what was read to obtain it."""

    # build_closure's nine keyword arguments, verbatim and in its order
    proposition: str
    assessments: tuple[AssessmentValue, ...]
    runs: Mapping[str, RunValue]
    verifications: tuple[Verification, ...]
    snapshot: LineageSnapshot
    producer_snapshot_identity: str
    retractions: RetractionEnumeration
    consulted: tuple[tuple[str, str], ...]
    binding: tuple[str, str]               # the PolicyBinding projected, as evaluate projects it

    # gathered, and not closure arguments
    claim: Claim | None                    # the one `claims` entry, keyed by `proposition`
    read_trace: tuple[ReadRef, ...]        # recorded at the moment of each read

    def closure(self) -> Closure: ...      # build_closure over the nine fields above
    def declared_refs(self) -> frozenset[ReadRef]: ...
    def records(self) -> belief.Records: ...

def gather(view: ReadView, proposition: str, *,
           context: belief.SuppliedContext, profile: ProfileSpec,
           resolution: ResolutionSnapshot, binding: PolicyBinding) -> EvaluationInputs: ...

def evaluate_over(view: ReadView, proposition: str, *,
                  availability: belief.Availability, context: belief.SuppliedContext,
                  profile: ProfileSpec, resolution: ResolutionSnapshot,
                  binding: object) -> Belief | NoBelief | Refused: ...
```

**`evaluate_over` guards the binding before it reads anything.** Its `binding`
is typed `object` and its **first** statement is `evaluate`'s step-1 check: a
value that is not a `PolicyBinding` returns `Refused("binding-not-exact: …")`
immediately. Without that guard the wrapper would open the corpus, or crash
projecting `.rule` off a `None` or a string, before `evaluate` ever got to
refuse — turning a clean refusal into reads and an exception. `gather` keeps the
narrow `PolicyBinding` type because the guard has already run by the time it is
called.

**`profile` and a real `PolicyBinding` are both required, and neither is
optional.** `consulted` is not derivable from `context` alone:
`consulted_contracts` takes `claims`, `profile`, `node_corpus`, `pins` and
`closure_nodes`, so `gather` must receive the `ProfileSpec`. And `evaluate`
refuses a binding that is not a `PolicyBinding` before anything else runs, so
passing a bare tuple would make every `evaluate_over` call refuse. The seam
therefore carries `PolicyBinding` and **projects it to `(rule, implementation)`
only for `build_closure`**, which is exactly what `evaluate` does at its step 9.

**`claim` is retained because dropping it would move the digest.** `evaluate`
reads at most one `claims` entry, keyed by `proposition`, and hands it to
`consulted_contracts`; a proposition with **no** claim record consults only the
base contract. So an absent claim is not a neutral default — it yields a
different `consulted`, and `consulted` is a digested closure member. The claim
is opaque and cannot be rebuilt from its identity, so `records()` populates
`Records.claims` from this field — `{proposition: claim}` when present, `{}`
when not — and passes `source_assertions=()`, which G1 makes safe: they are
never read below and move no output byte.

**Restoring that `Claim` needs a new seam inside `decode.py`, and this design
adds it.** `ReadView` returns a stored `Node`, not a `Claim`; the only
public route to a `Claim` is `decode_claim`, which takes a `WireClaim` — and
M13's second clause is that **no function downstream of the boundary accepts a
`WireClaim`**, the wire type being confined to the decode module. So `gather`
may not assemble one, and it may not decode by any other path either. The
conforming route is one added function, in `decode.py`, beside `decode_claim`
and sharing its body:

```python
def claim_from_stored(node: Node, *, profile: ProfileSpec,
                      snapshot: ResolutionSnapshot) -> tuple[Claim, BindingCheckReceipt]: ...
```

It builds the `WireClaim` from the node's covered proposition facet **inside the
module** and delegates to `decode_claim`, so the wire type still never leaves.
`gather` therefore takes a `ResolutionSnapshot`: the decode design makes
availability a parameter on purpose (§7.2 — *"a decoder that supplied its own
would decide by ambient state, and two holders would read the same bytes
differently"*), so the seam receives one and never builds one.

**This widens the public `Claim`-producing surface, so M11 and M13 are re-read
(§2.5).** It is not enough to assert the helper was written carefully: both rows
were closed against evidence that predates it.

The three genuinely supplied members — `snapshot`, `producer_snapshot_identity`
and `retractions` — pass through from `context` unchanged.

`evaluate_over` is the call-site change that makes the seam load-bearing rather
than merely present: it composes `gather` with `belief.evaluate`, passing
`inputs.records()`, and is **the only corpus-backed evaluation path in the
package**. `belief.evaluate` keeps its signature unchanged.

The first nine fields are **exactly** `closure.build_closure`'s keyword
arguments, in its order, so `closure()` is a call over the same typed values and
not a re-parse of anything. `closure.py` is not modified.

`gather` is **the resolver**: it is the only path by which a belief evaluation
obtains a value from a corpus, and it appends to `read_trace` at the moment of
each read.

**`gather` filters at read time, and this is not an optimization.**
`belief.Records` is deliberately an *unfiltered pool* — its own docstring
requires that an unrelated claim present in it move neither the value nor the
digest — so a resolver that read a pool and let `build_closure` filter
afterwards would record reads that the digest legitimately omits, and M1 would
fail on correct code. `gather` therefore resolves the matched assessments for
`proposition` **first**, and then reads exactly and only what they reach: their
runs, the verifications naming them, their `observes` datasets, and the single
`claims` entry keyed by `proposition`. The `Records` it returns is already
proposition-scoped, so `evaluate`'s own filtering is a no-op over it — itself
an assertable property.

**The membership key is `ReadRef`, and both sides derive it from the same typed
values.** `Closure.projection` is an encoder-ready mapping built for digesting,
not for set comparison, so containment is *not* computed against it.
`declared_refs()` derives the pair set from the nine fields directly, over a
closed kind vocabulary:

**It mirrors `build_closure`'s filtering exactly, member for member.** Let
`ours` be the matched assessments — those whose `proposition` equals
`proposition` — and `ids` their identities, the same two lines `build_closure`
opens with:

| kind | refs | mirrors |
|---|---|---|
| `assessment` | each identity in `ids` | `assessment_facets` |
| `proposition` | `{a.proposition for a in ours}` — the one `claims` key read, when `ours` is non-empty | `propositions` |
| `run` | `{a.run for a in ours}` — **not** every key of `runs` | the runs `observes` walks |
| `verification` | `{v.ref for v in verifications if v.assessment in ids}` — **not** every verification | `verifications` |
| `dataset` | the non-`None` `observes` addresses of those runs' inputs | `observes` |
| `retraction` | each ref in `retractions.found` | `retractions` |
| `contract` | each identity in `consulted` | `consulted` |
| `producer-snapshot` | `producer_snapshot_identity` | `producer_snapshot` |

The two bolded exclusions are the whole point. Declaring every key of `runs`
or every verification would admit a read of an **unrelated** run or
verification — one that `build_closure` filters out and the digest therefore
omits — and M1 would pass on exactly the code it exists to catch. `snapshot`'s
named addresses are likewise absent: the snapshot is supplied rather than read
through `gather`, so declaring its datasets would open the same hole.

Containment is then `read_trace ⊆ declared_refs()` as sets, and M1's assertion
is that inclusion. A read of a value in no row above is a read of something the
closure does not declare, which is precisely the failure the row is for.

**Containment is asserted on the `Belief` arm only, and the closure is never
widened to legitimize a read.** G3 makes the closure exist *whenever a belief is
produced*; `NoBelief` and `Refused` commit no input closure, so on those arms
there is nothing for a read to be contained in, and asserting containment would
mean inventing a closure this design does not have. Scoping the claim rather
than widening the declaration is the whole discipline: an earlier draft declared
`proposition` unconditionally so that a claim read would pass when no assessment
matched, which would have let a genuinely out-of-closure read through — the
exact failure M1 guards. On the `Belief` arm the question does not arise:
`evaluate` reaches step 8 only with at least one directional eligible
assessment, so `ours` is non-empty, `propositions` is non-empty, and the claim
read is declared by the closure itself.

`read_trace` records values **handed out**, not lookups attempted: a key that
resolves to nothing yields no value and traces nothing, so a proposition
carrying no claim record needs no declaration for the attempt.

Selected: the containment assertion over a corpus exercising every closure
member, and the sabotage arm — one extra value read **through `gather`**,
nothing else changed, and the check must fail. The sabotage is run in the shape
that would slip past a loose `declared_refs()`: the corpus holds a run and a
verification belonging to a **different** proposition, `gather` is made to read
one of them, and the check must fail even though the pool legitimately contains
both and the digest is unchanged. M1's stated scope limitation is
preserved verbatim and not closed: a read that never crosses `gather` — a
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
- **Same-corpus duplicate location is not repaired.** `consolidate` refuses a
  same-root pair; a single corpus holding two live records at one canonical
  address needs a recovery scanner this design does not build (§3.3).
- **`consolidate` is two-way only.** Three replicas at one address are
  consolidated by two successive calls, and no single call spans them.
- Ordered, deduplicated two-lock acquisition is **in-process only**.
  Cross-process single-writer operation remains a stated deployment obligation,
  detected loudly rather than prevented.
- **No interrupted operation is ever completed; only its data is repaired.**
  §3.5's recovery table is per operation and per prefix — a `move` interrupted
  at its destination create is repaired by `consolidate`, not by re-running
  `move`, which now refuses. But every one of those recoveries mints a fresh
  `event_token` and is a **new** operation, so an interruption at or after the
  first intent append strands one or two intents permanently, reading
  `unfinished` under T3, whether or not the data was repaired. There is no
  compensation transaction and no resumption seam; recovery correlation remains
  the log-consumer cut's, as family-adapters §5.4 left it for a stranded import.
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
| `report.py` | the two new operation kinds and `RecordMutationEntry` | the `acquisition` lane, which owns T1/T2/T4 |
| `corpus.py`, `stored.py` | `delete`, the three lock-held seams, the rewritten concurrency docstring | none |
| `decode.py` | `claim_from_stored`, the M13-conforming restore seam (§6.3) | none |

The later merge resolves toward the earlier one.

## 10. Banking choreography

The banking change carries this design, promoted into `docs/designs/`, together
with the relocation cut's frozen document. In the same change:

- the ledger's `consolidate-family` row note;
- the design-corpus guard's design count, README count/table/date and
  `_COUNT_WORDS`;
- the dated **C1 amendment** in the correction-lifecycle design (§2.2);
- the dated **§5.3 amendment** in the family-adapters design, replacing the
  create-only monotonicity ruling with §3.6 and citing this design (§2.1); and
- the dated **act-report amendment** (§2.4), carrying all five clauses in one
  change: the operation enum, the act-kind enum, the `record-mutation` subject
  grammar, its outcome vocabulary, and the composite root-local operation model
  with T2's scope under it.

Each cut's results record is a separate commit that rewrites the ledger's
`Current state` table and the roadmap, one at a time (concurrency rule 2). The
rulings ledger is committed to a tracked path before the worktree is removed.

## 11. Alternatives rejected

**A `delete` that mints an act-report.** Rejected because an act-report is a
live corpus node inside `corpus_state_identity`, so the report itself would
distinguish a managed deletion from a raw one on an ordinary corpus read —
contradicting the exact guarantee the deletion cut exists to establish.

**Deletion that refuses on inbound references.** Rejected because it makes
S5's and R23's selected arms unrunnable — every one of them deletes a record
another record names, and then asserts what the dangling reference does.

**A corpus-visible tombstone.** Rejected because S5 and R23 assert the
resulting state is indistinguishable from one where the run never existed. The
chain's committed removal transition is the history.

**Refusing deletion of retraction targets to preserve C1's wording.** Rejected
as a referential check in disguise, and because C1's real claim is about the
retraction family, which the §2.2 amendment states directly.

**An N-way `consolidate`.** Rejected because the scope is two readable corpora,
and an arbitrary-arity signature advertises multi-delete crash states §3.5 does
not enumerate. Three replicas take two calls.

**Relaxing `_refuse_already_minted` so `add` can write the survivor.** Rejected
because the create-path guard is what keeps ordinary `add` from silently
replacing a minted record. `_replace_locked` is a separate path with its own
expected-digest precondition.

**Distinct event tokens per root, correlated by the entry's corpora and ref.**
Rejected because that triple cannot distinguish two identical relocations run
in succession, so the two halves of one operation would not be uniquely
pairable. One operation carries one token in both root-local intents and both
reports (§3.5).

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
