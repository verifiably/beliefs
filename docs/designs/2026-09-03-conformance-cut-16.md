# Conformance cut 16 — relocation

**Status:** Frozen 2026-09-03. Discharged 2026-09-04
(`../plans/2026-09-03-conformance-cut-16-results.md`).

**Sources:** `2026-09-03-world-changing-families-design.md` §6.1 and
the frozen W, G, D, C, R, M, and T rows quoted below.

## 1. What this cut is

Cut 16 is the frozen acceptance boundary for the two-root relocation slice:
`move`, `consolidate`, their root-local intents and act-reports, contract
agreement, target re-resolution after a move, and sorted deduplicated lock
acquisition. The selection was frozen before implementation.

The selection rule is cut 5's: a clause is selected only when its source
mutation and every named check run entirely inside §2. A row with any unrun arm
is partial. Prior evidence remains evidence but is not selected again.

## 2. The boundary

In scope:

- the public `move` and `consolidate` entry points over two corpus roots;
- one shared event token and one intent and terminal report per touched root;
- destination-first move, two-record consolidation, the tagged lineage-basis
  union, contract agreement, and every relocation refusal named in §3;
- re-resolution by `retract` and `supersede` after a real move; and
- sorted, deduplicated acquisition of the distinct resolved root locks.

Out of scope:

- `delete` and every deletion arm;
- the audit;
- cross-corpus record reads through the world resolver;
- the rules store;
- `world-resolution`'s snapshot, coverage, and divergence clauses;
- the M1 resolver; and
- the claim restore seam.

## 3. Selection

### W5 — full

```markdown
| **W5** | Moving an entity between corpora changes only its location | Move a `source` from one corpus to another; assert its **`uid` unchanged**, its **canonical address unchanged**, no entry added to `deprecated_ids`, every inbound reference unchanged, and `belief_input_digest` unchanged. Then move a **dataset** that appears in the producers map, and assert `belief_input_digest` is **still** unchanged even though the address map and **both corpus-state identities** moved, so that re-deriving now mints a **new receipt** naming the same snapshot — this row is what two successive revisions of §5's snapshot identity violated, once through the address map and once through exact coverage states, so it is asserted against a member of the producer enumeration and not only against an unrelated `source` |
```

- **Selected:** the whole row: move a `source` with identity, address,
  deprecated ids, inbound references, and belief digest unchanged; then move a
  dataset in the producers map with the digest and snapshot unchanged, both
  corpus-state identities moved, and a new receipt naming that snapshot.
- **Prior, not selected again:** none.
- **Deferred:** none.

### W16 — part

```markdown
| **W16** | `consolidate` repairs storage and asserts nothing about identity (added 2026-08-08) | Hold **one canonical address** in two corpora; `consolidate`; assert **one canonical address**, outgoing relations **unioned**, **no redirect written**, **no inbound reference rewritten**, and **no `deprecated_ids` entry created** — no address retired, so nothing needs one. **`uid`, both cases** *(added 2026-08-09: equal basis gives an equal address, and does **not** give an equal `uid`)*: with inputs **sharing** a `uid` — a stamped corpus that was copied — assert it is **preserved**; with inputs carrying **distinct** `uid`s — independent authoring of the same source from the same DOI, which is the ordinary case — assert **one input `uid` survives**, the other ceases to be live, and **no third is minted**. **Divergent lineage survives consolidation:** consolidate two dataset records at one content address carrying **different lineage bases**; assert **both** survive, that no field-selection path offers a choice between them, that the dataset is `lineage-divergent` with independence over it `not-certified`, and that the conflict **still stands after deleting either producing run** — the W4 arm, re-homed. **Negative:** attempt `consolidate` on two records at **different** canonical addresses and assert **refusal** — that is a coreference question and `consolidate` must not answer it. **Negative, which is W8b's first arm:** one `uid` under two **different** canonical addresses is **corruption**; assert `consolidate` is not offered, and that it refuses on its **one-address precondition** rather than on a corruption check. **Negative:** assert `consolidate` writes no `coreference-attestation` and moves no balance |
```

- **Selected:** consolidate one address across two corpora; union relations and
  divergent lineage bases; write no redirect, inbound rewrite, new deprecated
  id, coreference attestation, or balance change; preserve a shared uid or keep
  one distinct uid without minting a third; refuse different addresses,
  including one uid under two addresses, on the one-address precondition.
- **Prior, not selected again:** none.
- **Deferred:** the conflict-survives-deleting-either-producing-run arm belongs
  to the deletion cut. That one unrun arm keeps W16 partial.

### G3 — closes

```markdown
| **G3** | **Whenever a belief is produced**, that belief state names its **complete transitive input closure** (below), as one digest (arm restriction added 2026-08-05 — formal model ρA8) | Recompute from the named closure alone; assert identity. Then mutate **each** closure member in turn — including ones the old G3 omitted — and assert the digest changes every time. **Structure, not only content:** a member that is a *set* must be tested for what the set's own structure carries — **permute** the keyed facets across assessments and assert the digest changes, and **delete** a producing run so a lineage basis entry stops resolving and assert the same. **Reads, not descriptions:** **add** a second producing run to a dataset already in the closure, changing nothing else, and assert the digest changes — the divergence test reads the producer set, so the producer set is a closure member. **Scope, not only contents:** enumerate the producer sets from a snapshot covering **fewer corpora**, with every present corpus identical, and assert the digest changes — an enumeration is bounded by what it consulted. **Negative — location is not evidence:** move an entity between corpora; assert the digest is **unchanged** (world W5), pinning that the member is the **producer snapshot** and not the world index that carries it. *(The alias arm was deleted 2026-08-08 with the alias itself — labels are rendered, never stored, so there is nothing to edit. Not replaced: location already tests OInv here, G7 tests display invariance, and an authority-release bump is **not** a substitute, since a consulted release may legitimately move the digest under D6.)* All four were live holes in earlier revisions, and none is reached by mutating a member's value |
```

- **Selected:** the negative: move an entity between corpora and assert the
  belief digest is unchanged because the closure member is the producer
  snapshot, not the carrying world index.
- **Prior, not selected again:** recomputation, mutation of every closure
  member, keyed-facet permutation, missing basis resolution, producer-set
  addition, and coverage-width evidence from earlier cuts.
- **Deferred:** none. This selected negative closes G3.

### D7 — closes

```markdown
| D7 | Contract agreement holds across a derivation, and W5 survives unamended | **W5 preservation:** move a dataset that appears in the producers map between two corpora pinning the **same** contract identities and assert `belief_input_digest` is **unchanged** even though both corpus-state identities moved — the row two prior snapshot-identity revisions violated; **agreement:** construct a closure spanning corpora pinning **different** identities for one namespace and assert the derivation is **refused**, never merged, never resolved by recency; **move refusal:** attempt to move a node whose facets use `biology/` into a corpus pinning a different `biology` identity and assert the **write boundary refuses**, so the belief-moving case is unreachable by relocation rather than tolerated; **the base-contract arms:** construct a closure spanning corpora that agree on every domain namespace but pin **different `science_contract`s** and assert the derivation is **refused** even though no base-profile facet is read; and attempt to move a Science node carrying **no domain facets whatsoever** into a corpus pinning a different `science_contract` and assert the move is **refused** — base-contract agreement is not conditional on facet content |
```

- **Selected:** W5 preservation for the producers-map move; refusal when a
  domain facet crosses contract identities; refusal for a facetless Science
  node crossing base-contract identities; the same domain and base-contract
  refusals for consolidation; and refusal on a missing required pin. Both
  refusal classes are exercised through each public entry point, `move` and
  `consolidate`; a helper-only check does not satisfy this cell.
- **Prior, not selected again:** derivation refusal for a closure spanning
  corpora with disagreeing domain or base-contract identities.
- **Deferred:** none. This selection closes D7.

### C3 — part

```markdown
| C3 | The digest covers the retraction enumeration — refs, resolutions, and coverage declaration; never exact corpus states | retract an in-closure, in-coverage input → digest moves; input outside the closure → unchanged; **standing retraction in an uncovered corpus → digest unchanged, and the coverage declaration is itself a digest member — the bound is visible, not silent**; **in-coverage corpus move (content identities unchanged) → digest unchanged, receipt records the new states** |
```

- **Selected:** move an in-coverage corpus with content identities unchanged;
  the belief digest stays unchanged and the receipt records the new corpus
  states.
- **Prior, not selected again:** the corpus-local in-closure and
  outside-the-closure retraction arms.
- **Deferred:** uncovered-corpus behavior and coverage declarations remain with
  `correction-remainder`. C3 stays partial.

### R23 — part

```markdown
| **R23** | A produced dataset, its ancestry and its durable basis are minted by the boundary (§5.2) | Assert the output dataset's address is the **dataset basis projection over the output manifest's content identities** — deduplicated, sorted, digested (admission ramp §6.2; *amended 2026-08-09, this read "the single output entry's content identity", which a uniform projection cannot return for a one-entry manifest without a cardinality special case inside an identity function*) — and that the run's **`produces`** edge is emitted with the run; attempt to attach `produces` naming a dataset the manifest did **not** emit, and assert the ordinary API offers no such path. Assert **no `produced_by` edge exists in either direction of the API** — the retired representation must not be reachable. **Negative (a) — no nominal handle in identity:** emit byte-identical output under two different **logical names** and assert **one** dataset address results — pinning that the address is not the manifest digest, which carries the name. Assert `derived_from` **resolves as a view** over `produces ∘ transforms`, is **not stored**, and is **not read by independence** — which walks the stamped basis — and that no authored ancestry list is accepted. **Negative (b) — the independence multiplier:** construct two runs sharing an upstream dataset and omit it from one's ancestry in a build that permits authoring; assert the omission **would** make the two assessments read as independent under kernel §4.2.1's disjoint-closure rule, then assert the derived form makes it unspellable. **Negative (c) — omission survives derivation:** classify a shared **empirical** input as auxiliary `reads` **without certification**; assert the closure is **incomplete** and independence is **`not-certified`**, never assumed — pinning that deriving the edge did not make the classification honest. Assert a **certified** exclusion does remove the input from the closure, that the certification is **inline on the `reads` entry** with a rationale and attribution, and that adding or withdrawing it **mints a different recipe** — then assert it mints **no run**, and that the original run is unchanged, until that recipe is **executed**. **Then assert both limits:** a *false* certification still omits the edge and still inflates belief — the guarantee is attribution, not truth; and after a corrected re-execution, assert the **original run and its false certification are still active belief inputs**, with no API path that retires either, pinning §11.13 rather than letting attribution be read as correction. **Replay cardinality:** replay a `dataset-production` run successfully and assert **one dataset address with two `produces` edges from two runs**; assert the lineage view composes over both, and that **no existing dataset node was mutated** to record either — including that the pre-existing dataset's **lineage basis is unchanged** and still names the first run. **Deletion, which the view alone cannot see:** stamp the basis, then **delete the producing run**; assert the dataset does **not** read as a root, that the unresolved basis entry emits **`lineage-incomplete`**, that independence over it is **`not-certified`**, and that kernel §5.1's belief digest **moves** — asserting the stored ref and its `null` resolution are recorded **separately**, since recording either alone loses the deletion. Assert the same for a deleted **ancestor**. Assert a *second* surviving run producing the same address by another route does **not** repair the first basis. **Negative (e) — divergence, not union and not silence:** have `R1` mint `D` from `A`, stamping the basis, then have `R2` produce byte-identical `D` from `B`. Assert independence over `D` becomes **`not-certified`** with a **`lineage-divergent`** finding — not silently unioned into ancestry, which the single basis cannot make durable, and not silently ignored, which would certify `D` independent of `B`-derived evidence while a derivation from `B` demonstrably exists. Assert kernel §5.1's belief digest **moves** when `R2` is added, pinning that the snapshot covers the **producer set** and not only the basis. **Coverage (§11.15):** enumerate producers from a **producer snapshot** whose coverage omits `R2`'s corpus and assert the digest **differs** from the full-coverage one even though every *present* corpus is identical; then make `R2`'s corpus absent **within** coverage and assert `not-present` rather than a silent undiverged reading. **Negative — location is not evidence:** move a dataset between corpora and edit an alias, and assert the belief digest is **unchanged** (world W5) — pinning that the member is the snapshot and not the whole index. **Derivation, not just hashing:** delete `R2`'s entry from a valid snapshot, leave its coverage and receipt intact, and hand it to **explicit import**; assert it is **refused** because rebuilding from the receipt's corpus states does not reproduce the map, that a snapshot carrying **no receipt** is refused as unrecomputable and that a receipt naming corpora rather than **exact states**, or naming a bare version string rather than a fixture-bound rule identity, evaluates to **`malformed`** — refused at import, and returned as `malformed` rather than `unresolvable` by an **audit** that meets one raw-written, since no arriving corpus or rule could ever make it checkable (world §5, W8a). Assert a snapshot whose receipts are **all malformed** is **`unchecked`**, never `contradicted`, with a malformed finding per pair. Assert a fabricated snapshot written straight into place is caught **only under audit** — never on read, which would violate R5. Assert the third case is **not** a refusal: a receipt naming exact states whose **corpora are absent here** imports with a **finding**, writes no validation state, and is checked by a later audit (world §5) — "cannot be checked here" is `not-present`, not `unknown`. Assert a receipt whose covered corpus has **moved to a new state** is likewise **unresolvable** rather than refuted, so a snapshot's completeness evidence is checkable only while the receipt is **`resolvable`** — **each** covered corpus at its own recorded state (world §5, limitation 10). **Two corpora:** make one of two covered corpora move while the other stands still, and assert the receipt is **unresolvable** — one corpus cannot satisfy the other's entry. **The rule is a receipt member too:** mutate the receipt's `producer_snapshot_rule_identity` and assert the **receipt identity moves** while the snapshot's semantic identity and the belief digest do **not**; then install a newer enumeration rule beside the old and assert the receipt **still validates**, stop holding the old rule and assert **`unresolvable`** rather than refuted, and assert a rule whose implementation fails its fixtures **is not that rule** (world W8a). **Negative — the receipt is not a belief input:** move a dataset between two covered corpora, so **both** corpus-state identities in the receipt change while the producers map does not; assert the belief digest is **unchanged**, pinning that exact states sit outside the semantic identity and that the completeness mechanism did not smuggle location back in. **Then assert the residue (§11.14):** delete `R2` and assert certification is **restored** and the resulting state is **indistinguishable** from one where `R2` never existed — no retained prior digest, since belief is a computed view; assert specifically that **no** test can distinguish them, rather than asserting a difference the design cannot deliver. **Merge and the tagged basis (world §4.3):** assert a boundary-minted basis is always **`single`**, and that the **only** transition to `conflict` is a merge of records whose routes differ. Merge two records at one content address with different routes; assert the survivor carries `conflict([both], sorted)`, that no field-selection path chooses between them and **no ordinary API removes a route**, that the dataset is `lineage-divergent` with independence `not-certified`, and — unlike the deletion case — that the conflict **survives** deleting either producing run. Assert merging two `conflict`s **unions** their routes. Assert the traversal over a `conflict` resolves **every** route's refs and certifies nothing, and that divergence is decided on the **tag** before any comparison — no `transforms`-versus-basis comparison is attempted against a set. **Valid state:** assert `conflict` with **fewer than two distinct routes is unconstructible**, so a conflict that never occurred cannot be spelled and there is one representation per fact. **Lifecycle:** assert **no** API resolves a conflict — none retires a route, chooses between two, or records one as wrong — so the state is permanent under this design (§11.13's missing correction lifecycle, reached from another direction). **Then assert two limits, which are not one limit:** a raw filesystem edit *can* drop a route or forge a `single`, and the API guarantee does not reach the filesystem (§11.11) — with `B`'s producing run still present, assert an **audit detects** the forged `single(A)`, since recomputation still has `B` to contradict it. **Then delete `B`'s producing run as well** and assert the audit reports **nothing**: every surviving route resolves and no record of `B` remains. Assert specifically that **no test distinguishes** that corpus from one in which the conflict never arose, rather than asserting a detection the design cannot deliver — the composite of §11.11 and §11.14, where R23 previously claimed a route's removal was always caught while the row above it said no path removes one. **Negative (f) — the replay case is not divergent:** replay `R1`'s recipe; assert the second producer's `transforms` set **equals** the basis, that **no** divergence is reported, and that independence stays certified — pinning that the divergence rule does not fire on the case §5.3 is built to reach. **Negative (g) — self-edges:** run an identity transform that transforms and produces one content identity; assert the run is **valid**, that **no** `D derived_from D` edge appears in the view, that the closure is **not** reported as cyclic, and that the run is **not** divergent — then assert a genuine two-node cycle **is** reported. **Negative (h):** assert an input's role is fixed in the recipe before execution, so reclassifying it mints a **different recipe**, and a different run only on execution; and assert a raw-written lineage basis is caught only under audit, as in R22 |
```

- **Selected:** the two move clauses: location is not evidence, and the receipt
  is not a belief input. The retired alias phrase is not exercised; this is the
  move alone, as amended by the world-address ruling.
- **Selected:** the non-deletion, non-audit consolidate clauses over the tagged
  basis: boundary-minted bases start `single`; consolidation is the only
  ordinary transition to a sorted `conflict`; differing and already-conflict
  routes union without field selection; traversal resolves every route and
  decides divergence from the tag; a conflict with fewer than two distinct
  routes is unconstructible; and no ordinary API resolves the conflict.
- **Prior, not selected again:** the dataset-production, replay-cardinality,
  derived-lineage, exclusion, and local basis/composition evidence already
  selected by prior cuts.
- **Deferred:** the deletion, audit, producer-snapshot, coverage,
  cross-corpus-divergence, explicit-import, and rules-store clauses. R23 stays
  partial.

### M3 — part

```markdown
| **M3** | **`standing` terminates, because the retraction graph is a DAG** | **Termination itself, on valid states:** evaluate `standing` over retraction chains of increasing depth, including counter-retractions and several standing retractions of one target, and assert termination and a stable value. Without this arm a looping implementation passes while its validator is perfectly correct. **The validator, exercised directly** — the only arm that can certify the check exists: hand it an abstract two-cycle and assert a **cycle-specific** result carrying a **witness** (the offending edge set), not a generic failure. Case-split the cycle across the boundary that matters — both records in the **bundle**, and one record in the bundle closing a cycle through the **resolved world context** — and assert import invokes the validator on the **union**, never on the bundle alone. **That import consumes the result:** force a cycle verdict for an otherwise entirely valid bundle and assert the import **refuses with no write**; an importer that calls the validator and ignores its witness must fail this arm. **Ordinary writes:** attempt a retraction whose target does not already resolve and assert refusal (C10), which is what makes a write incapable of closing a cycle. **Merge's two arms, restated onto its successors 2026-08-08 (`2026-08-08-world-address-ruling.md` §5; ρA10):** the distinct-basis arm becomes **unspellable rather than refused** — assert **no operation exists** that merges two distinct-basis retractions, which is stronger than the refusal this arm banked, and assert instead that a `coreference-attestation` over them leaves both retraction records **byte-unchanged** and closes **no cycle** (**W15**). The equal-basis arm keeps its shape under its new name: `consolidate` two **equal-basis** replicas of one retraction held in two corpora **while a counter-retraction `R` already targets it**, and assert it **succeeds**, that the retraction's content identity is **unchanged**, and that `R` is **not rewritten and not re-minted** — now true by construction, since `consolidate` requires one canonical address and performs no inbound rewrite (**W16**). World §4.3's `duplicate location` state has no other resolution. **Raw writes:** a cyclic configuration is classified **malformed by audit before any standing or belief evaluation** — assert no reading is invoked on it (§3.3, `Ω_valid`). **Explicitly not the test:** refusing a hand-written cyclic *pair* certifies nothing. Each retraction's content-derived address already includes its target identity, so such a pair fails **identity recomputation** on its own, and a generic "import refused" passes whether or not any acyclicity validation exists. That fixture is circular evidence, and an earlier draft of this row used it. **Negative:** no topological rank is stored anywhere; re-evaluate the same state after admitting records in a different order and assert every identity and `belief_input_digest` is unchanged |
```

- **Selected:** consolidate two equal-basis replicas of one retraction in two
  corpora while a counter-retraction targets it; consolidation succeeds,
  content identity is unchanged, and the counter-retraction is neither
  rewritten nor re-minted.
- **Prior, not selected again:** local DAG termination, direct abstract witness,
  forced-verdict consumption, and ordinary unresolved-target refusal from cut
  5.
- **Deferred:** the coreference, raw-write audit, admission-order, and concrete
  cyclic-construction arms. M3 stays partial.

### T2 — part

```markdown
| **T2** | One started operation, one intent, one terminal record — and no act precedes the intent | Run each operation kind to success; assert exactly one qualifying fulfillment: the `run` where one is minted, the act-report otherwise. **Positive:** a post-intent attempt that mints no run closes through **exactly one** qualifying act-report. Attempt a second fulfilling registration on one intent → **malformed**, the log's rule as built. Make root selection fail, then the intent append fail; assert in each case **no act began** — no request issued, no lease taken, **no record minted** (an `event_token` generated in memory and carried by no intent and no record is not a mint). **Negative (a):** a missing-spec run request refuses **pre-intent**; assert a surviving boundary publishes an *unfulfilling* act-report, that it fulfills nothing, and that a crash there leaves no trace. **Negative (b):** a complete non-conforming execution mints a **run**, never an act-report. **Negative (c):** a dataset-production attempt opens the **operation intent** — assert the assessment-run intent cannot be spelled without a `spec_identity` |
```

- **Selected:** successful `move` and `consolidate`, each read root-locally:
  one started operation, one intent, and one qualifying terminal act-report in
  each touched root, with no act preceding its root's intent.
- **Prior, not selected again:** the import and existing operation-family
  evidence.
- **Deferred:** every other operation kind, root-selection, second-fulfillment,
  missing-spec, and non-conforming-execution clause assigned elsewhere. T2
  stays partial.

### T8 — re-read

```markdown
| **T8** | Report identity preserves occurrence, and reports are retained evidence | Run two operations with equal actors, timestamps and entries but distinct operation `event_token`s; assert **distinct identities**. Mutate each facet member in turn; assert the identity moves every time. Attempt to edit, supersede, and delete a report through every ordinary API; assert no such path exists |
```

- **Selected:** re-read the ordinary-API prohibition against both `move` and
  `consolidate`; neither accepts an act-report as a subject or input.
- **Prior, not selected again:** occurrence identity, facet mutation, and the
  prohibition over every ordinary API that existed before this cut.
- **Deferred:** none. This is a re-read of a closed row, not a reopening.

### Boundary invariants

- **Selected:** after a real `move` removes a previously resolved target from
  its corpus, `retract` and `supersede` each re-resolve under the lock
  immediately before plan construction and refuse. This is one declaration
  unit with both entry points exercised.
- **Selected:** root acquisition deduplicates by resolved path before sorting;
  a same-root pair acquires its one distinct lock exactly once and refuses as a
  same-root relocation.
- **Prior, not selected again:** none.
- **Deferred:** the equivalent re-resolution refusal after a real `delete`
  belongs to the deletion cut.

## 4. Accounting

Nine guarantee rows are read: **3 full/closed** (W5, G3, D7), **5 partial**
(W16, C3, R23, M3, T2), and **1 closed-row re-read** (T8). The two
boundary-invariant declarations add no row. The N2 inventory therefore has
**11 declaration units**: one grouped unit for each row selection and one for
each boundary invariant. A grouped unit may expand into lettered sabotage arms,
but it is counted once here and may not be silently split or merged after the
freeze.

No deletion arm is selected. W16's deletion arm remains explicitly deferred.

## 5. N2 and acceptance obligations

1. The declaration inventory names exactly the 11 frozen units in §4, each
   single-homed to the test that exercises it. Lettered sabotage arms normalize
   back to those units.
2. Every selected behavior runs portably and again through the certified engine
   on the certified kernel and volume tuple. Capability refusal is an error,
   never a skip or waiver.
3. The aggregate runner names `cut15_acceptance.py` as its prefix, then runs
   the relocation acceptance module and the cut-16 N2 audit.
4. D7's disagreement and missing-pin paths run through the public `move` and
   `consolidate` operations. Deleting either public call to the predicate must
   fail the declared arm.
5. T2 is asserted root-locally, with one shared event token and timestamps
   across both roots; it does not collapse a two-root operation into one global
   intent or one global report.
6. The cut document and declaration inventory are pinned by digest before
   discharge. No implementation discovery rewrites this frozen body; any
   deviation is dated in the results record.

## 6. Second reader

The second-reader charge is to verify every fenced row byte-exact against its
source table at the freeze commit; audit every selected clause against §2; and
force any unrun clause to remain deferred and its row partial.

The reader challenges especially:

- W16 and R23 do not borrow their deletion or audit clauses;
- D7's refusals fail when either public operation stops calling the predicate;
- the moved-away target fixture is produced by a real `move`, not by direct
  filesystem deletion or a helper-only predicate test;
- same-root acquisition observes one resolved lock acquisition, not two
  reentrant acquisitions; and
- T2's root-local reading preserves two intents and two terminal reports under
  one operation token.

## 7. Limitations

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
