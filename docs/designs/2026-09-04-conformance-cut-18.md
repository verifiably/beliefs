# Conformance cut 18 — managed deletion

**Status:** Frozen 2026-09-04 as cut 17; renumbered to cut 18 on 2026-09-04 (§8).
Discharged 2026-09-04
(`../plans/2026-09-04-conformance-cut-18-results.md`).

**Sources:** `2026-09-03-world-changing-families-design.md` §2.2, §2.3, §2.5,
§3.0, §3.1, §3.6, §6.2, §6.3 and §7, and the frozen G, C, R, S, W, T and M
rows quoted below.

## 1. What this cut is

Cut 18 is the frozen acceptance boundary for managed deletion and the
mutation lane's assigned ride-alongs: the ordinary-write `delete`, the
managed/raw asymmetry under log verification, the deletion clauses the
relocation cut deferred, the claim restore seam, the instrumented belief
resolver, explicit-import derivation validation, and the semantic audit
those rows read through. The selection was frozen before implementation.

The selection rule is cut 5's: a clause is selected only when its source
mutation and every named check run entirely inside §2. A row with any unrun
arm is partial. Prior evidence remains evidence but is not selected again.

## 2. The boundary

In scope:

- the public `delete` entry point on `CorpusWriter`: one engine effect under
  the root's lock, no intent, no act-report, no referential check, no
  tombstone (§3.1);
- the excluded kinds common to every world-changing operation (§3.0);
- re-resolution by `retract` and `supersede` after a real `delete` (§3.6);
- log verification's reading of a managed deletion against a raw `unlink`
  (§3.1's asymmetry table), through the existing removal findings;
- the managed holdings deletion act as R5's last-held-copy transition;
- the corpus-local semantic audit: malformed classification first, then
  derivation recomputation for verifications and assessments and basis
  recomputation for datasets, over evidence the caller supplies; it writes
  nothing and mints nothing;
- explicit-import derivation validation over the same evidence, refusing a
  contradicted verification or assessment before any payload write;
- `decode.claim_from_stored`, the M13-conforming restore seam (§6.3); and
- `beliefs.evaluation`, the instrumented resolver and the only corpus-backed
  evaluation path (§6.3).

Out of scope:

- `move` and `consolidate` beyond producing the states this cut deletes from;
- cross-corpus record reads through the world resolver (R19's cross-corpus
  recomputation, S5's cross-corpus reach, M3's coreference arm);
- the rules store and the unresolvable-interpretation-rule refusal (R22);
- producer-snapshot, coverage and divergence clauses (R23);
- scope recomputation for a stored verification: the stored projection
  carries no comparison report, so only the verdict and the assessment
  identity are recomputed (limitation, §7);
- L13's preimage resolver: removal classification stays a path match; and
- the concrete-cycle constructions M3's banked limitation names.

## 3. Selection

### G2c — closes

```markdown
| **G2c** | An assessment is admitted only in the **admitted** verification state | Walk every row of the §3.3 lifecycle table; assert admission only for `clean-environment, passed` with no active `failed`. Assert a passing sibling does **not** clear an active failure |
```

- **Selected:** the kernel §3.3 lifecycle-table walk re-run over durable
  records — every row of the table, `active` read under the
  standing-retraction amendment — plus the raw-deletion negative: raw-delete a
  failing verification and assert the assessment returns to admitted,
  undetected on read.
- **Prior, not selected again:** cut 2's value-level walk and cut 5's
  positive retraction states.
- **Deferred:** none.

### G8 — closes

```markdown
| **G8** | A later failing verification forces recomputation and, **while recorded**, clears only by explicit resolution **or a standing retraction** (bounded — §3.3, amended by correction-lifecycle §7a) | Attach a failing verification to an admitted assessment; assert invalidation and recomputation of every touched proposition. Assert it is **not** cleared by recency or by a passing sibling, **and is cleared by a standing retraction** (correction-lifecycle C6). **Also assert the negative:** delete the failing verification and confirm the assessment returns to admitted — pinning that deletion is §3.2's undetectable-history limit, not a tamper-evidence claim |
```

- **Selected:** raw-delete the failing verification → admission restored,
  undetected on read; the log audit **refutes** the raw removal, while a
  managed `delete` of the same record **validates** with `record-removed`
  and, given the held copy, `failing-verification-removed` at error
  severity.
- **Prior, not selected again:** attaching the failure, recency and
  passing-sibling negatives, the standing-retraction clearing (cuts 2, 5).
- **Deferred:** none.

### C6 — closes

```markdown
| C6 | Verification retraction recomputes admission fail-closed under amended G8 (§7a) | retract a false failing verification → admitted iff a standing passing one remains; retract the passing one → unadmitted; a passing *sibling* still clears nothing. **Negative (unchanged):** raw deletion of a verification still restores admission undetectably — kernel §8.7's bound stands, §8 |
```

- **Selected:** the raw-deletion negative over verification retraction — raw
  deletion of a verification still restores admission undetectably on read.
- **Prior, not selected again:** cut 5's positive retraction states.
- **Deferred:** none.

### R5 — closes

```markdown
| **R5** | Belief does not depend on **artifact availability in this checkout** | Make the artifact bytes unreachable here **while a controlled copy remains held**; assert `belief_input_digest` **unchanged**, admission **unchanged**, replay eligibility *not available* — never `unverified`, never `failed`. **Negative (a) — holding, not reach:** destroy the **last held copy** of an `observes` input and assert the input is no longer held, eligibility fails, and admission **changes**. **Negative (b) — computability, not belief:** remove the **corpus holding the records** and assert **`not-available`**, not an unchanged belief, which would be a recomputation from absent inputs |
```

- **Selected:** negative (a) — destroy the last held copy of an `observes`
  input through `holdings.delete`, the managed act recording an `absent`
  observation; assert the input is no longer held, eligibility fails, and
  admission changes.
- **Prior, not selected again:** the digest, admission and eligibility
  thirds (cuts 2, 3), negative (b).
- **Deferred:** none.

### S5 — part

```markdown
| **S5** | Incomplete lineage never certifies independence, and the deletion guarantee is scoped | Science | delete an **ancestor named by a basis**; assert `lineage-incomplete`, `not-certified`, changed `belief_input_digest`, and no belief increase. **Negative:** delete a **divergent producer** (step 3) and assert the certificate is **restored**, belief **can** increase, and the state is indistinguishable from one where that run never existed — the absolute form of this row was written before step 3 existed |
```

- **Selected:** the deletion half — delete an ancestor named by a basis →
  `lineage-incomplete`, `not-certified`, `belief_input_digest` moved, no
  belief rise; delete a divergent producer → certificate restored, belief may
  rise, and the epistemic readings (corpus read, lineage traversal,
  admission, belief) are indistinguishable from a corpus in which that run
  never existed (§7's scoping: log verification is *not* one of those
  readings).
- **Prior, not selected again:** cut 4's corpus-local walk.
- **Deferred:** cross-corpus reach → `world-resolution`.

### R23 — part

```markdown
| **R23** | A produced dataset, its ancestry and its durable basis are minted by the boundary (§5.2) | Assert the output dataset's address is the **dataset basis projection over the output manifest's content identities** — deduplicated, sorted, digested (admission ramp §6.2; *amended 2026-08-09, this read "the single output entry's content identity", which a uniform projection cannot return for a one-entry manifest without a cardinality special case inside an identity function*) — and that the run's **`produces`** edge is emitted with the run; attempt to attach `produces` naming a dataset the manifest did **not** emit, and assert the ordinary API offers no such path. Assert **no `produced_by` edge exists in either direction of the API** — the retired representation must not be reachable. **Negative (a) — no nominal handle in identity:** emit byte-identical output under two different **logical names** and assert **one** dataset address results — pinning that the address is not the manifest digest, which carries the name. Assert `derived_from` **resolves as a view** over `produces ∘ transforms`, is **not stored**, and is **not read by independence** — which walks the stamped basis — and that no authored ancestry list is accepted. **Negative (b) — the independence multiplier:** construct two runs sharing an upstream dataset and omit it from one's ancestry in a build that permits authoring; assert the omission **would** make the two assessments read as independent under kernel §4.2.1's disjoint-closure rule, then assert the derived form makes it unspellable. **Negative (c) — omission survives derivation:** classify a shared **empirical** input as auxiliary `reads` **without certification**; assert the closure is **incomplete** and independence is **`not-certified`**, never assumed — pinning that deriving the edge did not make the classification honest. Assert a **certified** exclusion does remove the input from the closure, that the certification is **inline on the `reads` entry** with a rationale and attribution, and that adding or withdrawing it **mints a different recipe** — then assert it mints **no run**, and that the original run is unchanged, until that recipe is **executed**. **Then assert both limits:** a *false* certification still omits the edge and still inflates belief — the guarantee is attribution, not truth; and after a corrected re-execution, assert the **original run and its false certification are still active belief inputs**, with no API path that retires either, pinning §11.13 rather than letting attribution be read as correction. **Replay cardinality:** replay a `dataset-production` run successfully and assert **one dataset address with two `produces` edges from two runs**; assert the lineage view composes over both, and that **no existing dataset node was mutated** to record either — including that the pre-existing dataset's **lineage basis is unchanged** and still names the first run. **Deletion, which the view alone cannot see:** stamp the basis, then **delete the producing run**; assert the dataset does **not** read as a root, that the unresolved basis entry emits **`lineage-incomplete`**, that independence over it is **`not-certified`**, and that kernel §5.1's belief digest **moves** — asserting the stored ref and its `null` resolution are recorded **separately**, since recording either alone loses the deletion. Assert the same for a deleted **ancestor**. Assert a *second* surviving run producing the same address by another route does **not** repair the first basis. **Negative (e) — divergence, not union and not silence:** have `R1` mint `D` from `A`, stamping the basis, then have `R2` produce byte-identical `D` from `B`. Assert independence over `D` becomes **`not-certified`** with a **`lineage-divergent`** finding — not silently unioned into ancestry, which the single basis cannot make durable, and not silently ignored, which would certify `D` independent of `B`-derived evidence while a derivation from `B` demonstrably exists. Assert kernel §5.1's belief digest **moves** when `R2` is added, pinning that the snapshot covers the **producer set** and not only the basis. **Coverage (§11.15):** enumerate producers from a **producer snapshot** whose coverage omits `R2`'s corpus and assert the digest **differs** from the full-coverage one even though every *present* corpus is identical; then make `R2`'s corpus absent **within** coverage and assert `not-present` rather than a silent undiverged reading. **Negative — location is not evidence:** move a dataset between corpora and edit an alias, and assert the belief digest is **unchanged** (world W5) — pinning that the member is the snapshot and not the whole index. **Derivation, not just hashing:** delete `R2`'s entry from a valid snapshot, leave its coverage and receipt intact, and hand it to **explicit import**; assert it is **refused** because rebuilding from the receipt's corpus states does not reproduce the map, that a snapshot carrying **no receipt** is refused as unrecomputable and that a receipt naming corpora rather than **exact states**, or naming a bare version string rather than a fixture-bound rule identity, evaluates to **`malformed`** — refused at import, and returned as `malformed` rather than `unresolvable` by an **audit** that meets one raw-written, since no arriving corpus or rule could ever make it checkable (world §5, W8a). Assert a snapshot whose receipts are **all malformed** is **`unchecked`**, never `contradicted`, with a malformed finding per pair. Assert a fabricated snapshot written straight into place is caught **only under audit** — never on read, which would violate R5. Assert the third case is **not** a refusal: a receipt naming exact states whose **corpora are absent here** imports with a **finding**, writes no validation state, and is checked by a later audit (world §5) — "cannot be checked here" is `not-present`, not `unknown`. Assert a receipt whose covered corpus has **moved to a new state** is likewise **unresolvable** rather than refuted, so a snapshot's completeness evidence is checkable only while the receipt is **`resolvable`** — **each** covered corpus at its own recorded state (world §5, limitation 10). **Two corpora:** make one of two covered corpora move while the other stands still, and assert the receipt is **unresolvable** — one corpus cannot satisfy the other's entry. **The rule is a receipt member too:** mutate the receipt's `producer_snapshot_rule_identity` and assert the **receipt identity moves** while the snapshot's semantic identity and the belief digest do **not**; then install a newer enumeration rule beside the old and assert the receipt **still validates**, stop holding the old rule and assert **`unresolvable`** rather than refuted, and assert a rule whose implementation fails its fixtures **is not that rule** (world W8a). **Negative — the receipt is not a belief input:** move a dataset between two covered corpora, so **both** corpus-state identities in the receipt change while the producers map does not; assert the belief digest is **unchanged**, pinning that exact states sit outside the semantic identity and that the completeness mechanism did not smuggle location back in. **Then assert the residue (§11.14):** delete `R2` and assert certification is **restored** and the resulting state is **indistinguishable** from one where `R2` never existed — no retained prior digest, since belief is a computed view; assert specifically that **no** test can distinguish them, rather than asserting a difference the design cannot deliver. **Merge and the tagged basis (world §4.3):** assert a boundary-minted basis is always **`single`**, and that the **only** transition to `conflict` is a merge of records whose routes differ. Merge two records at one content address with different routes; assert the survivor carries `conflict([both], sorted)`, that no field-selection path chooses between them and **no ordinary API removes a route**, that the dataset is `lineage-divergent` with independence `not-certified`, and — unlike the deletion case — that the conflict **survives** deleting either producing run. Assert merging two `conflict`s **unions** their routes. Assert the traversal over a `conflict` resolves **every** route's refs and certifies nothing, and that divergence is decided on the **tag** before any comparison — no `transforms`-versus-basis comparison is attempted against a set. **Valid state:** assert `conflict` with **fewer than two distinct routes is unconstructible**, so a conflict that never occurred cannot be spelled and there is one representation per fact. **Lifecycle:** assert **no** API resolves a conflict — none retires a route, chooses between two, or records one as wrong — so the state is permanent under this design (§11.13's missing correction lifecycle, reached from another direction). **Then assert two limits, which are not one limit:** a raw filesystem edit *can* drop a route or forge a `single`, and the API guarantee does not reach the filesystem (§11.11) — with `B`'s producing run still present, assert an **audit detects** the forged `single(A)`, since recomputation still has `B` to contradict it. **Then delete `B`'s producing run as well** and assert the audit reports **nothing**: every surviving route resolves and no record of `B` remains. Assert specifically that **no test distinguishes** that corpus from one in which the conflict never arose, rather than asserting a detection the design cannot deliver — the composite of §11.11 and §11.14, where R23 previously claimed a route's removal was always caught while the row above it said no path removes one. **Negative (f) — the replay case is not divergent:** replay `R1`'s recipe; assert the second producer's `transforms` set **equals** the basis, that **no** divergence is reported, and that independence stays certified — pinning that the divergence rule does not fire on the case §5.3 is built to reach. **Negative (g) — self-edges:** run an identity transform that transforms and produces one content identity; assert the run is **valid**, that **no** `D derived_from D` edge appears in the view, that the closure is **not** reported as cyclic, and that the run is **not** divergent — then assert a genuine two-node cycle **is** reported. **Negative (h):** assert an input's role is fixed in the recipe before execution, so reclassifying it mints a **different recipe**, and a different run only on execution; and assert a raw-written lineage basis is caught only under audit, as in R22 |
```

- **Selected:** the deletion clauses — delete the producing run and the
  ancestor, stored ref and `null` resolution recorded separately, a second
  surviving run does not repair the first basis; the §11.14 residue after
  deleting `R2`; the conflict surviving deletion of either producing run;
  the audit detecting the forged `single(A)` while `B`'s run stands, and
  its contradiction finding disappearing once `B`'s run is deleted too
  (§7: the **semantic** contradiction finding disappears; the log audit
  still reports the committed removals).
- **Prior, not selected again:** cuts 3, 15, 16.
- **Deferred:** producer-snapshot, coverage, cross-corpus divergence,
  explicit-import and rules-store clauses.

### W16 — closes

```markdown
| **W16** | `consolidate` repairs storage and asserts nothing about identity (added 2026-08-08) | Hold **one canonical address** in two corpora; `consolidate`; assert **one canonical address**, outgoing relations **unioned**, **no redirect written**, **no inbound reference rewritten**, and **no `deprecated_ids` entry created** — no address retired, so nothing needs one. **`uid`, both cases** *(added 2026-08-09: equal basis gives an equal address, and does **not** give an equal `uid`)*: with inputs **sharing** a `uid` — a stamped corpus that was copied — assert it is **preserved**; with inputs carrying **distinct** `uid`s — independent authoring of the same source from the same DOI, which is the ordinary case — assert **one input `uid` survives**, the other ceases to be live, and **no third is minted**. **Divergent lineage survives consolidation:** consolidate two dataset records at one content address carrying **different lineage bases**; assert **both** survive, that no field-selection path offers a choice between them, that the dataset is `lineage-divergent` with independence over it `not-certified`, and that the conflict **still stands after deleting either producing run** — the W4 arm, re-homed. **Negative:** attempt `consolidate` on two records at **different** canonical addresses and assert **refusal** — that is a coreference question and `consolidate` must not answer it. **Negative, which is W8b's first arm:** one `uid` under two **different** canonical addresses is **corruption**; assert `consolidate` is not offered, and that it refuses on its **one-address precondition** rather than on a corruption check. **Negative:** assert `consolidate` writes no `coreference-attestation` and moves no balance |
```

- **Selected:** its remaining arm — the divergent-lineage conflict still
  stands after deleting either producing run.
- **Prior, not selected again:** cut 16's whole selection.
- **Deferred:** none.

### C1 — re-read

```markdown
| C1 | Retraction is additive: the target is byte-identical and still resolvable after | retract; assert target bytes, address, and resolution unchanged; assert no API edits or deletes a target |
```

- **Selected:** under §2.2's narrowing, retraction remains additive and its
  operation never edits, removes or re-addresses its target — asserted
  while a deletion API exists, so the reading postdates it.
- **Prior, not selected again:** cut 5's pre-amendment reading.
- **Deferred:** none.

### T8 — re-read

```markdown
| **T8** | Report identity preserves occurrence, and reports are retained evidence | Run two operations with equal actors, timestamps and entries but distinct operation `event_token`s; assert **distinct identities**. Mutate each facet member in turn; assert the identity moves every time. Attempt to edit, supersede, and delete a report through every ordinary API; assert no such path exists |
```

- **Selected:** the edit/supersede/delete clause against `delete` — no
  ordinary API deletes a report, `delete` refuses an act-report subject, and
  `delete` mints no report of its own.
- **Prior, not selected again:** cut 16's re-read against the relocation
  operations.
- **Deferred:** none.

### M13 — re-read

```markdown
| **M13** | **`Claim` is opaque, and the only route to one is the validated constructor** | Assert `Claim` cannot be built from ambient data: no public field-wise constructor, no cast or coercion from `WireClaim`, no dict/object-literal path. Assert **no function downstream of the boundary accepts a `WireClaim`** — the wire type is confined to the decode module. **Sabotage:** export a raw constructor, or widen one downstream signature from `Claim` to `WireClaim`, and assert the check fails. **Scope, stated because the first draft overreached:** profile-dependent validity — sign-aptness, arity, argument sorts, permitted dimensions, admissible layers — is **runtime** and belongs to **M11**. Operators arrive through `ProfileSpec`, and no Python or TypeScript implementation can vary a constructor's static signature by a runtime value without a code-generation layer this design does not propose. What survives statically is the consequence that actually matters: the check happens **once**, at one place, and downstream code needs no defensive revalidation. **Extended 2026-08-06, twice, on building it:** the guarantee is *"a value of this type was checked"*, and it is a **chain** — assert that `π_claim` refuses a claim its validated constructor did not mint, that the constructor refuses a profile the compiler did not return, and that the compiler refuses a contract no parser produced, each by an unforgeable brand rather than by shape. **Sabotage each link separately, and each link's brand against a prototype-only forgery**, since a plain object literal fails `instanceof` too and a test built only from one cannot tell the two checks apart — that vacuous test was written three times here. Assert also that everything a profile or contract holds is immutable **to the leaves**: rewriting one argument sort inside a compiled operator re-types an operator that is otherwise entirely real. **And assert what no brand can reach:** that two *genuine* artifacts which were never typed against one another are refused where they meet — a domain contract parsed under one base contract and compiled under another, which needs no forgery and passes every provenance check there is. This last obligation is **scoped, not universal**: it falls on an artifact whose validity is conditional on a particular upstream artifact *and* which can later be recombined independently, and it is discharged by verifying a recorded dependency **or** by revalidating the relation |
```

- **Selected:** §2.5's opacity arms against `claim_from_stored` — no
  `WireClaim` in or out of its signature; delegation to `decode_claim` with
  the own-typing-path sabotage; the brand chain intact through the new
  route.
- **Prior, not selected again:** cut 1's closure.
- **Deferred:** none.

### M11 — re-read

```markdown
| **M11** | **`decodeClaim` is a function of its arguments, and refuses rather than repairs** | Same `⟨WireClaim, ProfileSpec, ResolutionSnapshot⟩` decoded twice, in different processes and different checkouts → **identical** result. Then each ill-formed input in turn — a sign on a sign-inapt operator, wrong arity, an undeclared dimension, an inadmissible layer, a missing required contract — → **`Refused`**, with **nothing minted** in every case. **Sabotage:** make availability ambient rather than a parameter and assert two holders now decode the same bytes differently. **Negative:** a raw-written malformed claim is an **audit finding**, not a silent accept and not a decode failure — the boundary was bypassed, not defeated |
```

- **Selected:** §2.5's decode arms against `claim_from_stored` —
  determinism across processes and checkouts; availability as a parameter
  with the ambient sabotage; refusal before delegation on a wrong kind and
  on a missing, extra or malformed facet field, with nothing minted.
- **Prior, not selected again:** cut 1's closure; the raw-written negative is
  not re-run.
- **Deferred:** none.

### R19 — part

```markdown
| **R19** | Verification derivation is validated at explicit import and under audit, and neither mounting nor a raw write is an epistemic event (§7.3c) | Assert the constructor's arguments are **ordered run refs, an optional certification, and the explicitly selected contract identity and epoch (5b §7.6), and nothing else**: attempt to pass a comparison report, a conformance result, a boundary receipt, an **equivalence-rule evaluator**, or an **implementation selection** and assert no such parameter exists. Assert the evaluator's **identity** is resolved from the **original run's frozen spec** and its **implementation** from the run's frozen `rule_bindings` (5b §6), and that a **mixed-shape** pair is refused. **Explicit import, inputs resolvable:** hand a `verification` with a fabricated report, a chosen `scope` and `verdict`, and an address computed to agree with them to the **import operation** — the untrusted-import case substrate §4.2 says passes stale-hash and corpus checks — and assert the import is **refused before any write**, and that no file exists afterwards. Assert an import whose inputs do **not** resolve **proceeds** and emits an **import finding**, and that **no validation state is written onto the verification** in either case — the record is immutable and gains no `validated` field. Assert the recomputation resolves **across corpora** through the world resolver, and that a verification whose runs live in a different corpus is **not** refused for that reason alone. Do the same for an `analysis-spec` whose `stochastic-unseeded` contract accompanies a bitwise `equivalence_rule`. **Both transitions, which is the point of this row:** **(a) genuine, available → unavailable** — record a `passed` verification under a declared **tolerance**, make its artifacts unreachable here while they remain **held elsewhere**, and assert it is **not refused**, admission is **unchanged**, and no `inconclusive` is recorded; **(b) forged, unavailable → available** — import a self-consistent forged verification whose artifacts do **not** resolve (so it enters unvalidated and admits), then **mount them**, and assert admission is **still unchanged** until an **audit** runs, that the audit emits the contradiction finding and **mints nothing** (amended 2026-08-03, 5b §7.6), that a separate explicit constructor act naming its own cut and epoch mints the **superseding verification** carrying the correct derivation, and that admission changes **because of that node**, never as a side effect of the mount or of the audit alone. Assert reading the record at any point in either transition validates nothing. **Negative (c) — availability is not an epistemic result:** assert an unvalidated verification is neither certified sound nor treated as non-admitting; where its inputs cannot be resolved anywhere in the world, assert belief is **not computable**, never a silently unchanged or lowered value. **Negative (d) — the import boundary is an operation, not a directory:** write the same forged verification straight into a corpus path with a raw filesystem call, bypassing the import operation entirely; assert it is **not** refused, that **reloading the corpus does not validate it** at any point, and that it is caught **only** when an audit runs — pinning that "validate on import" is a claim about Science's operations and never about files appearing on disk. **Negative (e):** assert a raw-written *run* whose internal hashes agree is **still** not detected, and that an unaudited self-consistent verification is **not** distinguishable from a genuine one — both are substrate §4.3's limitation and need §9's log; this test must not be read as closing either *(Amended 2026-08-11, the act-report design §4: the constructor's closed list gains one member — the optional report-position citation. Every other extra argument is still refused, deleting the cited report invalidates nothing, and the audit arm is unchanged: the evaluator mints nothing, its finding recorded as an entry in the boundary wrapper's inert act-report.)* |
```

- **Selected:** explicit-import derivation validation over complete closure
  evidence, refusing before any payload write; transition (b) end to end —
  import a forged verification whose runs do not resolve (enters unvalidated
  and admits), then mount the runs, admission still unchanged until the
  audit runs, the audit emits the contradiction finding and mints nothing, a
  separate constructor act naming its own contract identity and epoch mints
  the superseding verification, and admission changes because of that node;
  negatives (d) and (e) with log-backed raw-write detection.
- **Prior, not selected again:** cut 3's constructor clauses, cut 4's
  transition (a) and read-side negatives.
- **Deferred:** cross-corpus recomputation → `world-resolution`; scope
  recomputation (§2, §7).

### R22 — part

```markdown
| **R22** | The assessment facet is derived from the run through the ordinary API (§3.1b, §5.1, kernel §4.2.1) | Assert the assessment constructor takes **only a run ref** — attempt to pass `outcome`, `estimate`, `uncertainty`, `estimand`, `applicability` or `interpretation_rule` and assert **no such parameter exists**. Run an analysis whose result the frozen `interpretation_rule` maps to **`refuted`**, and assert no API path produces an assessment carrying `supported`; assert the derived `outcome` changes only when the **result** or the **rule** changes. Assert `estimand` and `applicability` are **copied by the constructor** from the frozen spec, and that `proposition` comes from the spec's `target`. **Evaluator failure (§3.1b):** make the rule's evaluator fail — unreadable output, unparseable payload, missing rule implementation — and assert **no assessment is produced** and a finding is recorded; assert `inconclusive` is **not** produced, since it is a scientific outcome and machinery failure is not one. **Negative (a):** assert narrowing `applicability` after seeing the result requires a **successor spec and a new run**. **Negative (b) — no revisions, but the values are still hashed:** assert there is **no edit** that changes a facet and leaves the same assessment, and that the world basis `(spec, run, proposition)` is the constructor's own argument set. Then assert **G3 digests keyed facets** — sorted `(assessment identity, facet digest)` pairs — with **both** halves tested, since two consecutive revisions each dropped one: raw-write an assessment at the correct address carrying `supported` where the derivation yields `refuted` and assert the **belief digest differs** from the correct state's (which hashing identities alone would have missed); then **exchange the facets of two assessments** on one proposition, over different runs and different lineages, and assert the belief digest **differs** (which hashing a bag of facet digests alone would have missed, the multiset being unchanged). Assert the second state can aggregate to a different belief, so the digest is not merely being pedantic. Assert this is **change detection, not truth detection**. **Reach:** execute one recipe, then execute a second differing **only** by an inline exclusion certification (§5.2), so the two assessments carry **byte-identical facet values**; assert the belief digest differs. Assert that editing the certification alone changes **no** belief digest, because it mints a recipe and no run. **Rule binding (§3.1b):** assert a spec naming an `interpretation_rule` that resolves to neither a held implementation nor a registry entry with fixtures is **refused**, and that an implementation failing its fixtures **is not that rule**. **Negative (c) — the API is not the world:** hand-write an assessment file with a fabricated facet straight into a corpus path; assert it is **not** refused and **not** detected on read, that **explicit import** recomputes the facet from the run and **refuses** a mismatch, and that a raw-written one is caught **only under audit** — the §7.3c limitation, unchanged, and read-time validation would violate R5 |
```

- **Selected:** negative (c)'s explicit-import clause — import recomputes
  the assessment facet from the run and refuses a mismatch — and its
  caught-only-under-audit clause.
- **Prior, not selected again:** cuts 3 and 4.
- **Deferred:** the unresolvable-interpretation-rule refusal →
  `contract-cut`.

### M1 — closes

```markdown
| **M1** | **Every read that crosses the instrumented resolver is inside the declared closure** | Instrument the resolver so each value read through it is recorded at read time; assert the recorded read-set is contained in the declared closure, for a corpus exercising every closure member. **Sabotage:** add a code path that reads one value outside the closure **through the resolver** — a facet, a contract, a producer set — changing nothing else, and assert the check **fails**. **Scope, and it is a real one (DL):** the row is bounded by the resolver. A read that never crosses it — a module-level constant, an environment lookup, a cached global, a file opened directly — is invisible and passes, so M1 does **not** assert that every undeclared read is detected (limitation 1). Strengthening it to that claim requires an exhaustive capability or sandbox boundary, which this design does not propose. **Why the bounded row is still worth having:** G3's own text records four closure members that "were live holes in earlier revisions," each found by a reviewer noticing. M1 converts the ordinary case from noticing to checking, and names precisely the case it leaves to noticing |
```

- **Selected:** the containment assertion over a corpus exercising every
  closure member, on the `Belief` arm; and the sabotage — one extra value
  read through `gather`, a run or verification of a different proposition,
  nothing else changed, and the check fails while the digest is unchanged.
  The stated scope limitation is preserved verbatim (Appendix C's resolver
  bound).
- **Prior, not selected again:** none.
- **Deferred:** none.

### M3 — part

```markdown
| **M3** | **`standing` terminates, because the retraction graph is a DAG** | **Termination itself, on valid states:** evaluate `standing` over retraction chains of increasing depth, including counter-retractions and several standing retractions of one target, and assert termination and a stable value. Without this arm a looping implementation passes while its validator is perfectly correct. **The validator, exercised directly** — the only arm that can certify the check exists: hand it an abstract two-cycle and assert a **cycle-specific** result carrying a **witness** (the offending edge set), not a generic failure. Case-split the cycle across the boundary that matters — both records in the **bundle**, and one record in the bundle closing a cycle through the **resolved world context** — and assert import invokes the validator on the **union**, never on the bundle alone. **That import consumes the result:** force a cycle verdict for an otherwise entirely valid bundle and assert the import **refuses with no write**; an importer that calls the validator and ignores its witness must fail this arm. **Ordinary writes:** attempt a retraction whose target does not already resolve and assert refusal (C10), which is what makes a write incapable of closing a cycle. **Merge's two arms, restated onto its successors 2026-08-08 (`2026-08-08-world-address-ruling.md` §5; ρA10):** the distinct-basis arm becomes **unspellable rather than refused** — assert **no operation exists** that merges two distinct-basis retractions, which is stronger than the refusal this arm banked, and assert instead that a `coreference-attestation` over them leaves both retraction records **byte-unchanged** and closes **no cycle** (**W15**). The equal-basis arm keeps its shape under its new name: `consolidate` two **equal-basis** replicas of one retraction held in two corpora **while a counter-retraction `R` already targets it**, and assert it **succeeds**, that the retraction's content identity is **unchanged**, and that `R` is **not rewritten and not re-minted** — now true by construction, since `consolidate` requires one canonical address and performs no inbound rewrite (**W16**). World §4.3's `duplicate location` state has no other resolution. **Raw writes:** a cyclic configuration is classified **malformed by audit before any standing or belief evaluation** — assert no reading is invoked on it (§3.3, `Ω_valid`). **Explicitly not the test:** refusing a hand-written cyclic *pair* certifies nothing. Each retraction's content-derived address already includes its target identity, so such a pair fails **identity recomputation** on its own, and a generic "import refused" passes whether or not any acyclicity validation exists. That fixture is circular evidence, and an earlier draft of this row used it. **Negative:** no topological rank is stored anywhere; re-evaluate the same state after admitting records in a different order and assert every identity and `belief_input_digest` is unchanged |
```

- **Selected:** a raw-written cyclic configuration classified malformed by
  the audit before any standing or belief evaluation, with no reading
  invoked on it; and the admission-order negative — no topological rank is
  stored, and re-admitting the same records in a different order leaves
  every identity and the belief digest unchanged.
- **Prior, not selected again:** cuts 5 and 16.
- **Deferred:** the coreference arm → `world-resolution`; the concrete-cycle
  arms stay a banked limitation.

### M5 — closes

```markdown
| **M5** | **Qualification participates in claim identity** | Two claims differing **only** in a restriction identifier → different `I_claim`; differing **only** in quantifier tag → different; one carrying a dimension the other omits → different. Then the founding case end to end: mint kernel §4.1's *"in adults"* claim, assess it, "edit" to *"in all humans"*, and assert a **new** identity, the prior assessment still bound to the old one, and a `supersedes` link. **Sabotage:** drop the qualifier map from `π_claim` and assert the founding case **collapses to one identity** — the row's whole point. **Negative:** re-serialize the qualifier map with keys in a different order and assert the identity is **unchanged** |
```

- **Selected:** its prior clauses re-run durably — restriction-only,
  quantifier-only, and present-versus-absent qualification identity; the
  qualifier-map sabotage; the key-order negative — over records minted into
  a registered root.
- **Prior, not selected again:** cuts 1 and 5.
- **Deferred:** none.

### Boundary invariants

- **Selected:** after a real `delete` removes a previously resolved target,
  `retract` and `supersede` each re-resolve under the lock immediately
  before plan construction and refuse `RelocationTargetMissing`. One
  declaration unit, both entry points exercised, the absence produced by
  `delete` and not by a filesystem call.
- **Prior, not selected again:** cut 16's moved-away arm.
- **Deferred:** none.

## 4. Accounting

Sixteen guarantee rows are read: **7 full/closed** (G2c, G8, C6, R5, W16,
M1, M5), **5 partial** (S5, R23, R19, R22, M3), and **4 closed-row re-reads**
(C1, T8, M11, M13). The boundary-invariant declaration adds no row. The N2
inventory therefore has **17 declaration units**: one grouped unit for each
row selection and one for the boundary invariant. A grouped unit may expand
into lettered sabotage arms, but it is counted once here and may not be
silently split or merged after the freeze.

`delete` contributes no T2 arm: it opens no operation and mints no terminal
record (§3.1).

## 5. N2 and acceptance obligations

1. The declaration inventory names exactly the 17 frozen units in §4, each
   single-homed to the test that exercises it. Lettered sabotage arms
   normalize back to those units.
2. Every selected behavior runs portably and again through the certified
   engine on the certified kernel and volume tuple. Capability refusal is an
   error, never a skip or waiver.
3. The aggregate runner names `cut17_acceptance.py` as its prefix, then runs
   the deletion acceptance module and the cut-18 N2 audit.
4. G8's asymmetry runs through `audit_log` over a real chain: the raw arm
   must read `refuted` and the managed arm `validated` with both removal
   findings. A test that asserts only the corpus read does not satisfy the
   cell.
5. The audit's Ω_valid ordering is asserted by instrumentation: standing and
   belief evaluation are made to raise, and the audit must still classify.
6. The cut document and declaration inventory are pinned by digest before
   discharge. No implementation discovery rewrites this frozen body; any
   deviation is dated in the results record.

## 6. Second reader

The second-reader charge is to verify every fenced row byte-exact against its
source table at the freeze commit; audit every selected clause against §2;
and force any unrun clause to remain deferred and its row partial.

The reader challenges especially:

- S5's *indistinguishable* claim is asserted over the epistemic readings only
  and never over log verification (§7);
- R23's *audit reports nothing* is asserted as the absence of the semantic
  contradiction finding, not the absence of all findings (§7);
- `delete` mints nothing: the arms assert no intent appended and no report
  minted, and the operation enum carries no `delete` kind;
- the deleted-target fixture is produced by a real `delete`;
- M1's sabotage reads an **unrelated** run or verification through `gather`
  and the digest is unchanged while the check fails;
- `claim_from_stored` refuses **before** delegating and never repairs.

## 7. Limitations

- **L13 is not closed.** Removal classification matches a held copy by
  claimed path, never by bytes.
- **Scope is not recomputed.** A stored verification carries no comparison
  report, so the audit and the import recompute the verdict and the
  assessment identity only; scope recomputation waits on
  `verification-publication`.
- **The audit is corpus-local**, over a `ReadView` and caller-supplied
  evidence; nothing here resolves across corpora.
- **M1's resolver bound** and **M3's concrete-cycle arms** remain
  limitations, ranked nowhere.
- **No interrupted operation is ever completed** (design §8); `delete` is one
  transaction and has no prefix set.

## 8. Renumbering amendment — 2026-09-04

This cut was frozen as **cut 17** at `2071be0`. The write-permits lane froze
its own cut 17 earlier the same day (`c2f87b3`, renumbered at `398491d`) and
merged first. The roadmap's concurrency rule 1 claims a number **at freeze, in
freeze order**, so the earlier freeze keeps 17 and this cut is **cut 18**.
Rule 5 then makes this cut's aggregate runner name the highest-numbered
runner below it, `cut17_acceptance.py`, as its prefix.

The renumbering is a rename, not a re-reading. §§2–7 are byte-identical to the
freeze at `2071be0` under exactly four substitutions:

| from | to |
|---|---|
| `cut 17` | `cut 18` |
| `Cut 17` | `Cut 18` |
| `cut-17` | `cut-18` |
| `cut16_acceptance` | `cut17_acceptance` |

Nothing else moves: the boundary, the row selections and their quoted rows,
the 17 declaration units, the 20 sabotage arms, and the accounting — 7
full/closed, 5 partial, 4 closed-row re-reads — are the frozen ones.
`tests/acceptance/test_n2_cut18.py` pins both commits: current §§2–7 must equal
the renumbering commit's byte-exact **and** equal the freeze commit's under
those four substitutions.

One implementation change rides with the renumbering, dated here and in the
write-permits design's §15: `CorpusWriter.delete` now requires the
`corpus-write` permit on the resolved record's kind before any other refusal,
and is inventoried as a write entry point. It is a check added before an
effect; no selected behavior, arm or check changes.
