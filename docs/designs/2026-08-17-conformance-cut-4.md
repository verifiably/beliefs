# Conformance cut 4 — the first persistence slice

**Status:** Frozen 2026-08-18 — the composition-root adapter design banked
after §7's independent second reading. Discharged 2026-08-18 on the certified
volume (`../plans/2026-08-18-conformance-cut-4-results.md`).

**Sources:** the cut-4 scope spec
(`docs/superpowers/specs/2026-08-17-conformance-cut-4-scope-design.md`);
`2026-08-11-conformance-cut-3.md`; `2026-08-03-redesign-adoption-ledger.md`;
and, by description, the `atoms` authority design §14 and Plan B §12.2.

## 1. What this cut is drawn against

Cut 4 is drawn against the certified `atoms` engine adopted at Science's
composition root: the corpus-write adapter compiles a generic corpus write
into a `TransactionSpec` and submits it against the certified Linux volume
tuple, per the `atoms` authority design §14. Every other volume tuple fails
closed — there is no fallback path that writes durably outside the certified
binding.

The slice is **add-only**. Edits, moves, and deletions are not built here;
they are the family adapters' surface — supersede, archive, import/cohort —
which Plan B item 2 assigns to their own adapters in later cuts. What this
cut selects is bounded by the corpus-write adapter alone, Plan B item 1.

The cut froze when the composition-root adapter design banked on 2026-08-18,
after the `nodes` write-plan/executor seam amendment landed and §7's second
reader findings closed. The freeze block in §6 is now in force.

## 2. The boundary

In scope:

- durable minting of new corpus records through the write API's add path;
- refusal of every volume tuple outside the certified binding;
- compilation-correctness obligations at the Science boundary — `atoms`'
  physical certification is relied on, never re-run;
- stored-corpus traversal over the durable store.

Out of scope, each named with where it waits:

- **the family dialects** (supersede, archive, import/cohort) — wait for
  their own adapters, Plan B item 2;
- **the deletion surface** — removing a record is one of the edit-shaped
  writes §1 assigns to those same adapters, Plan B item 2's later cuts;
- **the managed holdings root** — the verified-holdings store's own
  management surface is not the corpus-write adapter's target, and waits on
  an adapter this slice does not build;
- **the world index** — waits on the `nodes` contract deltas, which are not
  on `nodes` main, and on the index those deltas carry being built, as cut 3
  stated it; its other condition there, composition-root adoption, is what
  this cut is drawn against (§5);
- **the audit** — no audit operation runs here, so every *caught only under
  audit* clause the cells below name waits on the reproducibility audit's
  own future slice;
- **retraction records** — subtracting standing without deleting a record is
  an edit-shaped write, outside this slice's add-only surface;
- **the rules store and resolver** — remain unbuilt, exactly as cut 2's P1
  deferral recorded;
- **the registry compile** — remains unbuilt, so the kind-existence check it
  would ground stays unbuilt with it;
- **the L rows and anchor carriage** — wait on the next persistence cut, as
  the closing paragraph below states.

Registration is an engine facility. The `atoms` executor appends a
registration entry inside every transaction this slice commits, and
`TransactionSpec` already carries `consumer_tag`, `intent_digest`, and
`fulfills` — the corpus-write adapter reserves nothing and adds no effect of
its own. No L row is selected here: anchor carriage and Science-side
verification — cut 3's intent/reduction semantics meeting the durable chain
— are the next persistence cut's work, and it selects the L rows then. Until
anchor acts exist, every transaction this cut commits is **chained but
unanchored**, and the unbounded unanchored tail is this cut's stated
limitation.

## 3. Step 1 — what the slice crosses

**The substrate.** The slice crosses the write API's add path made durable
and the stored-corpus traversal that reads back what that path minted: a
corpus record is minted through the add path, compiled into a
`TransactionSpec`, and committed against the certified volume tuple; the
world layer's closure then walks the committed store through `nodes`'
one-hop `outbound()` / `inbound()` operations — one algorithm over the
relation and lineage adjacency adapters, as the substrate consolidation
design §3 relocated it. Three consequences bound every S-row reading below,
and each is a boundary fact rather than a preference.

1. **A corpus root is durable; the crossing between two of them is not
   built.** Corpora exist and a record knows its own, but nothing resolves
   an address to the corpus holding it — that step is the world resolver,
   and the world addressing design's own capability table assigns it to the
   world layer, where a corpus-local walk "truncates at the corpus edge".
   The **world index** is out of scope, so every closure this cut runs is
   corpus-local, and every cross-corpus fixture defers with it.
2. **A raw filesystem write to a corpus path is available, and it is a
   fixture act rather than a slice operation.** The substrate consolidation
   design §4.2.1 defines such a write as an **untrusted import** by
   definition — a module bypassing `nodes` entirely — and with a durable
   store beneath it, a fixture constructs one without the write API,
   without an edit, and without touching any excluded subsystem. That is
   what makes S7's eligibility violation and S8's negative runnable here, and
   it is the one construction this cut's selected S rows use that the add path
   does not perform. S3's exact mutation remains deferred: its banked cell
   requires an edit followed by explicit import, not construction of a fresh
   raw file. A raw write is invisible to the
   engine-supplied chain in both directions: the chain records the
   transactions this slice commits, not the filesystem beneath them.
3. **The slice is add-only, so a store state a deletion would produce is
   reached only by minting it.** A basis entry naming an address no record
   carries is mintable, and an arm asserting the resulting *state* is
   selectable. An arm asserting the *transition* — a digest that moved
   because something was removed — is not, and it stays with the deletion
   surface.

**The run and report boundary.** Cut 3 built the run, verification,
assessment, and act-report constructors over held *values*: every record it
minted lived in a fixture's value set, and every claim it could make about
one was a claim about what the API constructs and what a digest over those
values reads. A durable store changes two things for those rows, and no
more. Records now **land** — a minted record occupies an address on disk, so
a corpus path exists to write beside through the fixture act that item 2
above defines, and a forged file can be placed at the address a genuine record
would occupy; that is the construction cut 3's raw-write clauses named and
could not build. And records now **reload** — what the add path committed is
read back by the stored-corpus traversal, so an assertion that a read *does
not* check something is at last an assertion about a read this cut runs.
What the boundary does not gain is every operation that is not the add path.
There is no explicit import here, so no write-time recomputation and no
refusal before writing; no audit, so no contradiction finding and no
superseding mint; no managed holdings root, so nothing is **mounted** and no
managed deletion runs — heldness itself stays exactly what cut 3 made it, a
value a fixture supplies, which is how cut 3's own selected R5 and G9 arms
made bytes unreachable here while a copy remained held; and, this cut's
transactions being chained but unanchored, no valid anchored observer set.
Where a T or R arm's subject is one of those, durability moves it no closer,
and the row defers by name below.

**The world layer.** Of the nineteen W rows, only **W3** runs without it. The
world-addressing design states its refusal — creating a `source` or
`dataset` without its basis — as the write boundary's own rule
(`2026-08-02-world-addressing-design.md:364`): a check over one record's own
fields, needing no resolution and no corpus beyond the one being written to.
Every other row's substantive claim is a world-scope one — collision,
coreference, and handle resolution across a world holding more than one
corpus, §1.1's own fixture being cross-project — or names an operation this
slice does not build: a move, a redirect, `consolidate`, a rename, or the
index and its derived maps. The eighteen remaining rows defer on the write
boundary and the index, unchanged from cut 3.

## 4. Step 2 — the selection, arm by arm

### 4.1 Selected in full

| row | what the slice must demonstrate |
|---|---|
| **S7** | eligibility enforced at **both** boundaries, both of which this slice builds. The write boundary (substrate consolidation design §6.2 item 1): the add path refuses to mint an inadmissible `assesses` edge. The profile-level corpus check (item 2): a file raw-written into the durable store carrying an `assesses` edge whose run has no `observes` input is reported `eligibility-unmet` by the check reading that store, under the Science-owned code namespace §6.2 fixes. The cross-node predicate spans assessment → run → `observes` → dataset → facet — kernel kinds and the `science` base profile's own `empirical-observation` facet, corrected there by the domain-extension boundary — so no clause of it reaches the excluded **registry compile**. The row's stated bound, that a raw write producing a *valid* node is intentionally unreported, is pinned by S8's negative construction — a raw write with the static check asserted silent — while the corpus check's own silence on a *valid* node remains §4.2.1's stated bound rather than an arm of either row |
| **S8** | the static claim over the code this cut wires: no module outside the write API constructs or receives a mutable `Corpus`, checked by AST — the capability boundary §4.2.1 chose precisely so that a new writer cannot escape by being undiscovered. The claim gains its first durable subject here, the composition root where the corpus-write adapter is the handle's one holder. **Negative:** write a corpus file with a raw filesystem call and assert S8 does **not** fire — the limit pinned, then read through §4.3's stale-hash check and §6.2's corpus check, subject to the recorded-history limitation the row carries. S7's corpus-check arm is selected here; S3's exact hand-edit-then-import mutation remains deferred |
| **W3** | a `source` created with **no accepted external identifier** (no DOI, PMID, ISBN or accession) and a `dataset` created with **no content identity** — the §1.1 DepMap case, a programme named with no release pinned — both **refused**, not silently coerced to a curation `note`: the world-addressing design's own rule (`2026-08-02-world-addressing-design.md:364`) puts the refusal **at the write boundary**, over the record being minted and nothing else. A curation note is authored instead as its own explicit add; supplying the basis afterward mints the world entity as a second, separate add — two mints, never an edit, so §3's add-only reading reaches both. **Negative:** no title-and-year fallback exists to be reached — the refusal has no derived-identity escape. **Negative — identity is not holding, the admission-ramp narrowing** (`2026-08-09-admission-ramp-design.md` §6.4): a `dataset` whose content identity is recorded and whose bytes are **not held anywhere** is **minted**, not refused — `declared`, addressable and referenceable; the add path performs no holding check, since `declared`/`held` is derived on read and never stored — cut 2's own arms over the same record, `G9`'s *derived, never stored* clause and `G2b`'s refusal of a `declared` input — so what this negative narrows is a write-time non-check. No clause of the row reaches the index, a move, `consolidate`, or a redirect: the check is entirely over one mint attempt's own fields |

### 4.2 Selected in part

| row | arms **in** cut 4 | arms **deferred**, and on what |
|---|---|---|
| **S1** | the relation fixture minted through the add path into one durable corpus root and walked back out of it: chain, diamond, cycle, unrelated predicate, deprecated ref, dangling target, and the **undirected relation** reached from its stored source but not its stored target — the whole of it corpus-local traversal over `nodes`' one-hop operations, which is the traversal this cut's boundary names; membership-traversal agreement and the non-reinterpretation of `directed` are asserted over that store. **Negative:** `nodes` exposes **no** transitive operation — a static reading of that package's surface, depending on nothing this cut builds | the **chain crossing corpora**, with its assertion of the full closure rather than truncation at the corpus edge. Reaching a target the holding corpus does not carry requires resolving an address to the corpus holding it, and that is the **world index**; run corpus-locally the fixture cannot be built at all, and a truncation indistinguishable from the dangling-target case already selected would assert nothing |
| **S1a** | the lineage fixture over the same durable root, walked as a **facet** rather than as relations: chain, diamond, cycle, a `single` basis, a `conflict` basis yielding **every** route and certifying nothing, and the unresolvable **ancestor** told apart from the unresolvable **producing run** — the distinction the relation adapter cannot express. Both unresolvable cases are constructed by *minting* a basis entry naming an address no record carries, never by deleting one, so §3's add-only reading reaches them; the `conflict` tag is likewise written into the store rather than produced, the boundary minting only `single`. **Negatives:** the lineage adapter accepts **no** predicate and **no** direction argument; and one algorithm serves both adapters, so cycle-safety and start-exclusion are certified once — assertable because S1's adapter arms are selected in this same cut | the **cross-corpus chain**, deferred with S1's and for the same reason — a basis whose ancestor lives in another corpus is resolvable only through the **world index** |
| **S5** | the walk that *produces* the lineage snapshot from a store, in its corpus-local form: the basis walked transitively out of a durable corpus root under the substrate consolidation design §5's procedure — the inspected set is `{observed root} ∪ closure`, the root included because the traversal is start-excluding (step 1); a `conflict` tag short-circuits to `lineage-divergent` on the tag alone, before resolution or comparison (step 2); and a minted basis entry that does not resolve — absent ancestor or absent producing run alike, including an unresolvable entry with an empty closure — yields `lineage-incomplete` and no certificate (step 2b). Cut 2 deferred exactly this piece on "**S1a's and the write API's** territory"; this cut supplies both — the add path mints the basis durably, and S1a's walk runs over the store — so what cut 2 could not run is what this cut adds | the walk's **cross-corpus** reach, with S1's and S1a's, on the **world index**; the banked construction — *delete* an ancestor named by a basis and assert the `belief_input_digest` **changed** and belief did not rise — which is a transition across the **deletion surface** Plan B item 2 assigns to the family adapters, leaving both halves where cut 2 left them, over supplied snapshots; and the negative's *"indistinguishable from one where that run never existed"* clause, which needs the same **deletion surface** and is in any case a claim about what a store retains after a removal, not about the walk this cut adds |
| **R19** | **Availability transition (a)**, the genuine one — record a `passed` verification under a declared **tolerance** through the constructor cut 3 selected, mint it durably into a corpus root, then make its artifacts unreachable here while they remain **held elsewhere**, and assert it is **not refused**, that admission is **unchanged**, and that no `inconclusive` is recorded; with it, the *reading the record validates nothing* sentence in its (a) half. Heldness is no stronger here than in cut 3 — it stays a value a fixture supplies, exactly as cut 3's selected R5 and G9 arms had it, so no clause reaches the **managed holdings root**, which owns the mount and the managed deletion and neither of which (a) performs. What the store adds is the whole of what cut 3 was missing: the verification is a record that *lands* and is *reloaded*, so "not refused" and "validates nothing" are assertions about a read this cut runs rather than about a value set, and admission is recomputed over the reloaded store. The bound is built and the arm is failable on it: this cut's traversal already reports an unresolvable reference as `lineage-incomplete` (S5), so a build that let unavailability reach admission — the `inconclusive` R5 forbids, or a refusal on reload — fails this arm. **Negatives (d)/(e), read-side clauses only:** raw-write a self-consistent forged verification and assert it is not refused and reload does not validate it; raw-write a self-consistent run and assert it is not detected; and assert an unaudited self-consistent verification is indistinguishable on read from a genuine one. These are the same durable read-path bound R22(c) selects, not claims that the excluded detectors ran | the **refusal before writing**, which is the explicit import's result and not the add path's: the import operation is the import **family dialect**, Plan B item 2's surface, and the recomputation it refuses on traverses verification → runs → spec and results, all world-identified, which the computation design's own world-addressing consumer table assigns to the composed resolver — the **world index**, out of scope, and §3's corpus-local reading with it. **Transition (b)** is not (a)'s mirror and does not follow it in: it imports a forged verification, then **mounts** the artifacts, then wants an **audit** to emit the contradiction finding and a separate constructor act to mint the superseding verification — the **family dialects**, the **managed holdings root** for the mount, and the **audit** for everything the transition is *for*, since the admission change it asserts happens because of the audit's superseding node. Negative (c) asks whether inputs resolve *anywhere in the world* — the **world index**. Negatives (d)/(e)'s *caught only under audit* clauses remain with the **audit**, and (e)'s log-backed detection remains with **anchor carriage and Science-side verification** |
| **R22** | negative (b)'s **raw-write** half, which cut 3 deferred on the store and the store now supplies: mint an assessment through the add path into a durable corpus root and take the belief digest over the reloaded store; then raw-write a second file **placed at the address a genuine record would occupy** — the basis is `(spec, run, proposition)`, so the forgery sits exactly where the derived assessment sits — carrying `supported` where the derivation from the same run yields `refuted`, self-consistent in its own stored hash so §4.3's stale-hash check has nothing to say about it, and assert the belief digest **differs** from the correct state's — the half a digest keyed on assessment identities alone would have missed, and the first cut in which the forged state can be built at all, an address on disk being what "at the correct address" needs. The rule binding stays **supplied** by fixture, exactly as cut 3's selected arms had it, so no clause of this reaches the excluded **rules store**; the closure is corpus-local, the producer snapshot an argument to the digest rather than a stored selection. **Negative (c)'s corpus-path clause**, its companion and its point: the same hand-written file with its fabricated facet is **not refused** and **not reported** on read — not by the stale-hash check and not by the corpus check. S7's corpus-check arm is selected here; S3's exact hand-edit-then-import mutation remains deferred, but this self-consistent file is silent under both checks. Read with the raw-write half it is R22's own punchline made durable: the digest moved and the reader said nothing, which is change detection and not truth detection | the *unresolvable interpretation rule is refused* clause, unchanged from cut 3 — resolution against a held implementation or a registry entry is the **rules store and resolver**, still excluded exactly as P1's deferred arm records, and the in-slice form (*"no binding supplied → refuse"*) is still the different, weaker claim cut 3 named; negative (c)'s **explicit-import** clause — that import recomputes the facet from the run and refuses a mismatch — which is the import **family dialect**'s operation, Plan B item 2's surface and not the add path this slice builds, so the recomputation has nowhere to happen and no refusal to produce; and negative (c)'s *caught only under audit* clause — the **audit** — which stays where cut 3 left it and is what keeps the two selected halves a statement of the §7.3c limitation rather than a closing of it |
| **G9** | the *minted as a world entity* clause, the one piece of the row both prior cuts deferred on the world boundary: a `dataset` carrying a content identity and **no bytes** is minted through the add path into a durable corpus root and is a **world entity** there — addressable, referenceable from a second record minted into the same corpus, and resolved as a reference by this cut's traversal — while it still reads **`declared`** and `G2b` still refuses it as an assessment input, those two being cut 2's own arms over the same record. Cut 2 named the blocker exactly: *"entity standing is **W3**'s property, referenceability included, and needs the world boundary W3 waits on"* — and **W3 is selected in full in this cut** (§4.1), where the add path performs no holding check and `declared`/`held` stays a state derived on read. This is a named blocker discharged by name, not a re-reading of the clause | the **independence sabotage** — *install the declared path exists as the promotion predicate; assert G9 fails while G2b, R5 and R10 all pass* — unchanged from cut 3 and for cut 3's reason (§2 item 2 there): the sabotage launders through a **persisted** heldness substrate, and heldness in this slice is still a value a fixture supplies, exactly as §3's run-and-report reading has it. It waits on the **managed holdings root**, beside R5's own negative (a) |
| **R23** | the **`derived_from` view**, which cut 3 deferred among the clauses blocked by *the store* and which the store now supplies: a run is minted through the add path into a durable corpus root with its `produces` edge and its role-partitioned inputs, and `derived_from` **resolves as a view** over `produces ∘ transforms` walked out of that store — **stored nowhere**, no such edge present in the corpus and no ordinary API accepting an authored ancestry list — and **not read by independence**, which walks the **stamped basis**: with a basis and a composition made to disagree, by the §3 item 2 fixture write rather than by any deletion, independence follows the basis, which is the structure S5's selected walk produces from this same store. Corpus-local throughout and add-only, and failable in both directions — a build that stores the view fails it, and a build that certifies independence off the view fails it | every **deletion** arm — delete the producing run, the ancestor, or the second producer, and assert what the digest and the certificate do — which asserts a **transition**, and §3's third consequence keeps a transition outside an add-only slice even where the resulting state is mintable, that minted state being S5's selected arm and not this row's assertion; negatives **(e)**–**(g)** with every divergence, coverage, receipt, snapshot, merge and conflict arm, each of which reads the **producer snapshot** over a declared coverage or enumerates producers across corpora — the **world index**, unchanged from cut 3, the snapshot staying an argument to the digest here exactly as R22's selected half has it; the **independence multiplier and the omission arms**, which cut 3 deferred together and which stay together here — the multiplier's construction runs *"in a build that permits authoring"*, which minting durably does not make this cut, and negative (c)'s omission half classifies a shared **empirical** input as uncertified auxiliary `reads` and then asserts the closure is **incomplete** with independence **`not-certified`**, a reading over the producer set and its coverage and so the **world index** again, carrying with it the two limits that are not one limit: that a *false* certification still omits the edge and still inflates belief, and that after a corrected re-execution the original run and its false certification are **still active belief inputs** with no API path retiring either, which is the correction lifecycle's **retraction records**; and negative (h)'s raw-written basis, caught *"only under audit"* by its own text — the **audit** |
| **N2** | the doctrine over **cut 4's selected arms**, as cut 1, cut 2 and cut 3 each applied it over their own: every arm this document selects is declared as data with its row, its assertion, its source mutation, and its exact named checks, and the harness audits each for `vacuous`, `stale`, `mixed`, `uncollected`, and the class-node collapse, reporting malformed contract content rather than passing it. The doctrine is already load-bearing inside this cut's own reading — it is what refuses **S4**'s vacuous form and what excludes **G5** below — so declaring this cut's arms is not a new obligation but the one the reading has been discharging in prose | the doctrine over the rows **no cut selects**, exactly as all three prior cuts left it |

### 4.3 Standing from prior cuts

Three registers, and every row named below sits in exactly one of them: the
rows **fully exercised**, where nothing remains anywhere; the rows
**part-exercised** whose remainder this cut does not touch, each with the
place it waits; and the rows this reading **reached and deferred whole**,
which are counted in §5 with their groups and are recorded here only because
a reader of §5's table alone would not learn that they were read.

**Fully exercised — 34 rows.** No single prior list holds them. **M4, M7,
M9, M10, M11, M13** (cut 1) and **G1, G2b, G6, M6, M8, P2–P9** (cut 2,
completing M6 and M8 jointly with cut 1) are cut 3's own nineteen. To them
this cut adds cut 3's fifteen selected in full — **G2a, G4, M2, R1, R3, R6,
R7, R8, R11, R14, R17, R18, T3, T6, T8** — whose slice landed 2026-08-12 and
whose last arms were completed 2026-08-13, the selection requiring no
amendment. Nineteen plus fifteen is the **34** this cut inherits with nothing
outstanding.

**Part-exercised, and this cut adds nothing — 23 rows.** Each was read
against this slice's boundary in the sweep §5 opens with, and each still
waits where a prior cut left it.

- **R2**'s trace and job-ID components; **R16**'s trace-membership,
  target-satisfaction, family, definition-equality, multi-stream and
  execution-coverage arms; **R20**'s two-decomposition comparison and its
  per-family negative; **R21**'s two-target arm and its negative (d) — the
  **full workflow surface**.
- **R4**, **R9**, **R13**, and the confinement clauses of **R16** and
  **R21** — the **confinement-capable boundary policy**. A durable store is
  not a confined one, and `clean-environment` is no more reachable here than
  in cut 3. (Three rows appear in two bullets each, their remainders
  splitting across two boundaries; each is one row in one state.)
- **R5** and **T4** — the **managed holdings root**. R5's negative (a)
  destroys the last held copy, which only a managed deletion recording an
  `absent` observation enacts; T4's coverage projection, its
  unfinished-operation arm, and its observation-deletion negative are the
  holdings record's. Heldness stays what §3 makes it, a value a fixture
  supplies.
- **R10** and **T5** — the **acquisition** operation. R10's remainder is
  *"the acquisition path records dataset provenance instead"*, and T5's
  began-ness and preflight-versus-post-stop distinctions are that operation's
  behaviours; T5's *no entry outcome constructs an observation* negative
  additionally needs the **managed holdings root**, where cut 3 `:248` put it
  under the persistence seam — a durable corpus mints records, not byte
  observations, so the negative stays as vacuous here as it was there.
- **R12** and **T2** — **anchor carriage and Science-side verification**.
  R12 wants the intent entry as a *removal-detectable* witness, which an
  unanchored tail does not give; T2's qualification, second-registration and
  ordering claims are readings of committed registrations, and this slice's
  operation surface is the corpus-write adapter alone, so no boundary
  operation appends an intent to a root here. T2's crash-leaves-no-trace
  clause travels with them: crash atomicity is the certified engine's
  property, relied on and never re-run.
- **R20**'s negative (a) import half — the **import family dialect**, Plan B
  item 2's surface.
- **T1** — the **import family dialect**, the **audit**, and **anchor
  carriage**, as the paragraph below sets out.
- **G2c** and **G8** — **retraction records**. The clause correction-lifecycle
  §7a added to *"active"*, and G8's *cleared by a standing retraction*, are
  both C6, and subtracting standing without deleting a record is an
  edit-shaped write this slice excludes (§2).
- **G3**, **D7** — the **move surface and the world index** together. Both
  rows' remainders are moves: G3's *move an entity between corpora; assert
  the digest is unchanged* (kernel `:960`) and D7's W5-preservation arm with
  its two move refusals (cut 2 `:253`). This cut builds neither half, so
  neither row gains an arm.
- **S6** — the **first successor policy admitting unequal weights**. Arm (h)
  is recorded and not run by its own amended text, and is not assertable
  against `science.belief.v1`; the trigger is a future artifact, not a
  subsystem, and durability is not it.
- **P1** — the **rules store and resolver**, named out of scope in §2.
- **D3** — the **world index**. `not-present` is *world address indexed,
  corpus absent*, and the remainder of the five-way non-collapsing assertion
  needs it produced.
- **D6** — the **registry compile**. The domain-facet arm needs a derivation
  that reads a namespaced facet, and no derivation this slice runs reads one.
- **M5** — the **supersede family's adapter**. The founding case is one
  scenario carried whole — mint, assess, edit, a new identity with the prior
  assessment still bound and a `supersedes` link, the enumeration reading as
  the formal model banks it (`:3136`) and as cut 2 restated it
  (`:259`–`:261`), placed where cut 3 `:280` left it. This cut
  supplies the mint and not the edit, and half a scenario runs none of it.

**The outright exclusions, stated against this cut's own candidate list.**
Five rows the scope reading named as candidates or near-candidates are
excluded here on the record, and each is counted where this paragraph says.
**G3** — the corpus-move negative, world persistence, kernel `:960` — counts
among the 23 above. **G5** — the kind registry is where *"no such kind
exists"* becomes checkable (cut 2 `:283`), and the registry compile is out of
scope, so the refusal would be vacuous under N2's sabotage doctrine — counts
in §5's kernel group. **G7** — the walk is a semantic edit, kernel `:964` —
counts in §5's kernel group. **M5** — the mint-and-edit walk is one scenario,
carried whole, cut 3 `:280` — counts among the 23 above. **D7** — both
remaining arms are moves needing the write boundary *and* the index, cut 2
`:253` — counts among the 23 above.

**Three substrate rows the reading reached and deferred whole.** They have no
arm in any cut, so they are counted **once, in §5's substrate write &
traversal group**, and not among the 23 above; the reading is recorded here
because §5's group row states an unblocker and not a cell.
**S2** — *a semantic edit through the write API mints a new proposition* —
is pure edit in its banked cell
(`2026-08-02-substrate-consolidation-design.md:550`: edit scope via API,
assert a new node, a `supersedes` edge, and prior refs unmoved): every
clause of it is the supersede dialect's surface, so it gains no arm and
defers whole to the **supersede family's** cut. **S3** — *a stale semantic
hash is rejected on import* — requires the banked source mutation
*hand-edit fields only* followed by refusal at explicit import; constructing
a fresh stale file would substitute a different mutation and fail N2's exact
source-mutation rule. It defers whole to the **import/cohort family's** cut.
**S4** — *`nodes.rename` is
never used for a semantic change* — asserts that no rename path is
reachable **from the semantic-change branch** (`:552`), and this slice
builds no such branch; asserting unreachability from a branch that does not
exist is not a weaker form of the row but a vacuous one, which N2's
sabotage doctrine refuses. It defers whole with S2, to the same cut.

One boundary row the store was read against and did not move. **T1** —
*only the boundary mints an act-report* — has two arms outstanding and the
durable store reaches neither. The **import** arm asserts what another
observer's report becomes when it *enters*: structurally validated, not
operation-authenticated, attributed, and inert, with nothing derivable to
recompute and no validation state written. Entering is the explicit
import's doing, and the act-report design §3.1 makes an explicit import a
boundary **operation** — a frozen observer-corpus root, one operation intent
appended before any act, products publishing per act, and an act-report
closing it — which is the import **family dialect**'s surface, Plan B item
2's work and not this slice's. The add path cannot stand in for it, and the
clause that forecloses it is the one cut 3 selected: *the constructor is
reachable only from the boundary*. There is no path by which a fixture
constructs another observer's report to hand the add path in the first
place, so the arm has no add-path form at all — not a weaker one. The
**raw-write negative** names its own blockers in its own text — a
self-consistent report
undetected on read, detected by an audit *only* with the tamper log
implemented and a valid anchored observer set — which are the **audit** and
the **L rows and anchor carriage**, both excluded here, every transaction
this cut commits being chained but unanchored. T1 stays selected in part,
exactly where cut 3 left it, and is counted among the 23 above — the one row
of them whose reading is given here at length rather than in a line.

## 5. Step 3 — fully deferred rows, grouped by unblocking subsystem

Every row this cut does not fully exercise was **re-read against this slice's
boundary**, cell by cell — its owning table's text and its latest arm split
both — and none is carried here unread: 82 of 151 rows have no arm in any
cut, and each of the 82 has a reading behind the group row it sits in.
Grouping is by the subsystem that unblocks the row. Cut 3's groups carry
forward, and every move this cut's boundary forces is stated inline — both
the rows that **leave** a group because this cut selected them, and the
unblockers that had to be **restated** because the thing cut 3 named as
missing is built here. An unblocking event that has occurred cannot honestly
name a deferral, which is cut 3's own rule from its third reading.

| group | rows | n | unblocked by |
|---|---|---|---|
| the persistence seam | H1–H4, **T7** | 5 | the **managed holdings root**. *Restated:* cut 3 read this group as waiting on *"the holdings store and the transactional root"* — the transactional root is built here, so the deferral names the store alone. Every H arm is an act against that store: creation reserved to acts and to established outcomes, supersession per location over a checked DAG, the declared-coverage receipt, the no-silent-act rule. T7's publish-together claim additionally needs the **acquisition** operation, its subject being *a successful acquisition*, over a store transaction this cut does build |
| world addressing | W1, W2, W4–W16, W5a, W8a, W8b | 18 | the write boundary and the index, unchanged from cut 3. *Leaves:* **W3**, selected in full (§4.1) — its refusal is the write boundary's own rule over one mint attempt's fields. The group phrase is the group's; where a member's own blockers are narrower they are its own — **W11**, for one, waits on the world resolver and the project/coordination surface, and whether coordination records are minted through the corpus-write adapter at all is underdetermined here, which is why it defers rather than gaining a vacuous arm |
| substrate write & traversal | S2, S3, S4 | 3 | the **supersede family's adapter** for S2/S4 and the **import/cohort family's adapter** for S3. *Restated:* cut 3 read this group as waiting on *"the write API and the stored-corpus traversal"*, and this cut builds both — what remains is the family surface: semantic edit for S2/S4, and S3's exact hand-edit-then-import mutation (§4.3). *Leaves:* **S7**, **S8** in full and **S1**, **S1a** in part. **S5** is selected in part at §4.2 and counted there; it was never a member of this group — cut 3 carried it in the part-exercised list, and only cut 2 said that its deferred *walk* half waited where this group waits |
| kernel, at other boundaries | G5, G7 | 2 | G5 — the **registry compile**, where *"no such kind exists"* becomes a checkable claim, so the refusal would be vacuous while it is unbuilt; G7 — the **supersede family's adapter**. *Restated:* cut 3 named *"the mint path"* for G7, and the mint path is what this cut builds — G7's walk is a semantic **edit**, in its positive form and in both prose forms of its converse, so the honest deferral is the edit surface |
| packaging | X1–X12 | 12 | **world export** — the epoch, its four derived maps, and its receipts. *Restated:* cut 3 carried a second condition on X2, composition-root adoption, which this cut is drawn against and which is therefore discharged; X2's remaining claim is publication over an epoch, and its recovery half is the certified engine's property, relied on here and never re-run. X9's anchored head members additionally need **anchor carriage**, X10's bindings the **rules store**, and X12's map **retraction records** |
| tamper log | L1–L13 | 13 | **anchor carriage and Science-side verification — the next persistence cut; the chain itself is engine-supplied at every commit**. Every row's check sits at the durable chain and asks of it what this slice does not build: settlement gating an absence test, truncation refuted behind an anchored head, chain removal refuted against a surviving anchor, the unanchored tail's extent as a reported bound, the genesis baseline load-bearing *once anchored*, intent claims read off entries, anchor evaluation total over an observer set. L8's cross-chain order and L11's export eligibility additionally need the **world index** and **world export**, and L13's cooperative removal the **deletion surface** |
| correction lifecycle | C1–C10 | 10 | **retraction records**, unchanged — and named again in §2 for this slice's own reason: a retraction subtracts standing **without** deleting a record, which is an edit-shaped write outside an add-only surface. C3's and C9's coverage clauses additionally need the **world index**, C7's route retirement the merge and conflict surface, C8's import refusal the **import family dialect** with the **audit** and its *mounting the corpus writes nothing* negative the **managed holdings root**, and C10's *raw-write each refused case and assert the audit reports it* clause the **audit** |
| normative contract — contract cut | N1, N3 | 2 | the **first contract cut**, unchanged. N3's resolution clauses — an implementation failing one fixture *is not that rule*, an un-held implementation reading `unresolvable` — additionally need the **rules store and resolver**, out of scope here exactly as P1's deferred arm records |
| normative contract — certification | N4–N9 | 6 | **instrument certification and parity machinery**, unchanged. N4's and N7's raw-write clauses additionally need the **audit**; N7's epochs and coverage the **world index**; N7's and N8's retraction grounds **retraction records** |
| normative contract — legacy adoption | N10 | 1 | the **adoption gate**, unchanged — the subject is the legacy suite's disposition classes, which no persistence boundary supplies |
| domain boundary | D1, D2, D4, D5, D8, D9, D10 | 7 | **facets, manifests, and the registry compile**, unchanged. D1's check is a static reading of the `nodes` tree and **durability gives it no new subject** — unlike S8, whose static claim gains the composition root this cut wires, D1's subject is a package this cut does not touch, and its negative is a compile-time refusal besides; D5's projection needs the **corpus manifest** and identities to pin; D2's facet addition and D10's promotion trigger are edit-shaped besides, and wait on the **supersede family's adapter** with **retraction records** |
| formal model | M1, M3, M12 | 3 | M1 the instrumented resolver; M3 retraction graphs and consolidation — **retraction records**; M12 the extraction path. Unchanged; **M2** left this group at cut 3 |
| confinement | R15 | 1 | the **confinement-capable boundary policy**, unchanged — a durable store is not a confined one, and every arm of the row is about what an execution may reach |

## 6. Accounting, freeze, and amendment discipline

**3 selected in full + 8 in part + 34 fully exercised by prior cuts + 23
part-exercised with untouched remainders + 83 fully deferred = 151.** Every
banked row is classified into exactly one state. As in all three prior cuts,
**no count of arms is offered as a denominator**: the banked rows do not
enumerate their arms formally, and the splits in §4.2 are this document's
reading of each row's test cell.

The identity is checked by hand, and there is no other way to check it. A
cell legitimately names other rows in bold — **N2**'s cell bolds **S4** and
**G5**, neither of which it selects, the doctrine being what refuses the one
and excludes the other — so any pattern that read bold row ids out of §4
would score a citation as a placement. §5's *Leaves:* clauses are the
stronger case: they bold the ids of rows that left a group, **W3** in world
addressing and **S7**, **S8**, **S1**, **S1a** in substrate write &
traversal, and every one of those is counted in §4 — so the same pattern run
over §5 would count each of them a second time. §5's group rows carry
ranges rather than members besides, so `X1–X12` and `W4–W16` must be
expanded before there is anything to count. The check was therefore made by
writing out all 151 ids on paper: the three of §4.1 (**S7**, **S8**,
**W3**); the eight of §4.2 (**S1**, **S1a**, **S5**, **R19**, **R22**,
**G9**, **R23**, **N2**); the 34 and the 23 that
§4.3 enumerates by name; and each of §5's thirteen groups expanded to its
members, 5 + 18 + 3 + 2 + 12 + 13 + 10 + 2 + 6 + 1 + 7 + 3 + 1 = 83. Every
one of the corpus's 151 rows appears once and once only.

Four sets of placements are the ones a re-reading should attack first,
because each is *read* in one section and *counted* in another, which is
exactly the shape a double count takes. **S2**, **S3**, and **S4** are read in §4.3 and counted in §5's
substrate write & traversal group, never among the 23. **G5** and **G7** are
named in §4.3's exclusion paragraph and counted in §5's kernel group.
**G3**, **M5** and **D7** are named in that same paragraph and counted among
the 23, their remainders being prior-cut standing rather than fresh whole
deferrals. And **S5** is counted in §4.2, having never been a member of §5's
substrate group — §5's own row says so, because cut 2's phrasing invites the
opposite reading.

> **Freeze — in force 2026-08-18.** The composition-root adapter design banked
> after §7's second-reader findings closed, and the status header carries that
> date. From this freeze onward the discipline is cut 3's, unchanged.
> **Results are recorded
> separately**, never by editing the selection. If the cut must change, the
> original selection is **preserved verbatim** alongside the amendment, with
> the reason stated.

The slice's acceptance criteria are the selected arms as frozen. This cut
adds no guarantee table of its own, and the acceptance suite that discharges
the selected arms belongs to the composition-root adapter design, not to this
document.

## 7. The second reader

A second reader ran before this cut froze. Cut 1's limitation 8 set the
precedent — a cut
drawn by its author against rows that author also reads is not
self-checking — and every arm-level classification error found in cuts 1, 2
and 3 ran the same way, toward overstating coverage. The one recorded
exception is not an arm error: cut 3's §7.1 finding 1 calls itself *"the one
finding in three readings whose correction moved coverage **up**"*, and it
moved because the execution boundary had been mis-drawn, not because an arm
was re-read. Cut 3 accordingly ran its reading before its freeze, and of the
four findings it returned, every arm a finding moved, it moved **out**. The
reader here is given the banked row texts and §2's boundary declaration, not
this document's rationale, and was instructed to attack the draft in that known
direction. Three things are theirs to check. **The arm splits of §4.1 and
§4.2, against the Selection rule**: an arm is selectable only where its check
runs entirely inside §2's in-scope list, so a clause reaching an edit, a move,
a deletion, the family dialects (including explicit import/cohort), the world
index, the registry compile, the managed holdings root, the audit, retraction
records, the rules store, or anchor carriage moves its row out of full into
part, or out of part into whole deferral. **The accounting of §6**,
re-derived independently by the hand method described there rather than read
off its sum — the check that cannot be mechanized is the one most likely to
have been fudged, and the arithmetic being right proves only that the
placements agree with each other. **The group moves of §5**: each *Leaves:*
and each *Restated:* claim, since a restatement naming as missing a subsystem
this cut in fact builds is the same overstatement wearing a deferral's
   clothes, and an unblocking event that has occurred cannot honestly name a
   deferral.

It returned four findings, all closed before freeze:

1. **S3 was over-selected in full.** Its banked mutation is *hand-edit fields
   only* followed by refusal at explicit import. A freshly constructed stale
   file is a different source mutation, so the raw-write fixture did not
   satisfy N2. S3 moved to whole deferral under the import/cohort family.
2. **R19(d)/(e) were under-selected relative to R22(c).** Their read-side
   clauses independently assert that raw-written, self-consistent records are
   not refused or validated on reload. Those clauses moved into §4.2; their
   audit and log-backed detection clauses remain deferred.
3. **S5's walk stood, but its deletion-equivalence wording did not.** The
   selected fixture is now only a minted unresolved basis entry. Every
   deletion transition and digest consequence remains deferred.
4. **The demotion-trigger list omitted two §2 exclusions.** The selection rule
   above now names the family dialects, including explicit import/cohort, and
   the audit alongside the other blockers.

The reader found no error in G9's dependence on W3 or in the R16/R20/R21
double-listed remainder bullets. It independently re-derived the corrected
accounting: **3 + 8 + 34 + 23 + 83 = 151**, every row in exactly one state.

## Limitations

1. **The unbounded unanchored tail.** Every transaction this cut commits is
   **chained but unanchored**. The `atoms` executor appends a registration
   entry inside each one, so chain entries exist from the first commit and
   there is no window without them; what does not exist is an anchor act
   publishing a head against which truncation or chain removal could be
   refuted. The tail therefore grows without bound for as long as this slice
   is the whole persistence surface, and its extent is not a reported
   quantity here either — the row that would report it is an L row, and no L
   row is selected. Anchor carriage and Science-side verification are the
   next persistence cut's work; the tail is the price of drawing this cut
   first.
2. **Add-only: no edit, move, or deletion obligation is exercised.** The
   corpus-write adapter mints, and nothing in this slice supersedes,
   renames, moves an entity between corpora, retracts standing, or removes a
   record. Where an add-only construction reaches the *state* a deletion
   would produce — S1a's basis entry naming an address no record carries,
   S5's observed root with an empty closure — the arm is selected and the
   construction is named; every arm asserting the *transition* stays
   deferred, by §3's third consequence. A reader tallying rows exercised
   should read that as the whole edit-shaped half of the corpus's
   obligations having no first arm yet, in this cut or any prior one.
3. **The selection is prospective implementation work, not a shipped
   durability claim.** The composition-root adapter design is banked and this
   cut is frozen, but the adapter and suite remain unbuilt. The cells commit
   what implementation must demonstrate; they do not say it already does.
4. **Durability claims rest on the certified tuple's binding, not on
   re-running the physical exerciser.** `atoms`' certification of the Linux
   volume tuple is relied on by construction: this cut asserts compilation
   correctness at the Science boundary and that every other tuple fails
   closed, and it asserts nothing whatever about crash atomicity, fsync
   ordering, or rename semantics beneath that boundary — §4.3 defers T2's
   crash clause on exactly this ground. If the certified binding is wrong,
   or a deployment runs a tuple the binding does not cover, no arm selected
   here fails; the whole of that risk is carried by the certification and
   its adoption-ledger row, not by this cut's suite.
5. **The arm splits are a reading, not a property of the rows** — all three
   prior cuts' limitation, inherited whole. The banked cells are prose, and
   a different reader could draw a boundary one clause earlier and change
   which half of S5, R19 or R23 is selectable. That is why §6 offers no arm
   count as a denominator, and why §7's reading is a precondition of the
   freeze rather than a courtesy after it.
