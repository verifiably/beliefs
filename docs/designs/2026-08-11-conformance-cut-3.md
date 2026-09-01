# Conformance cut 3 — the run boundary, frozen prospectively

**Status.** Draft 2026-08-11, **frozen before any cut-3 implementation
exists**, on the discipline both prior cuts held: a cut drawn after
implementation is a list of what happened to pass. Drawn over the **151-row**
corpus — cut 1's frozen denominator of **126** and cut 2's of **139** are
untouched, and nothing here amends a banked row. Selects **15 rows in full
and 19 in part** after the pre-merge third reading's amendment and its
scoped re-reading (§7.1–§7.2) — the selection as first frozen read 17/17
and is preserved verbatim in **Appendix A**; §5 groups the 88 fully
deferred rows by unblocking subsystem, and §6 accounts for all 151. The
second reading ran before the freeze and §7 records its four findings;
the third reading returned four more (§7.1), three moving arms **out** —
the direction every prior cut's errors ran — and one correcting the
execution boundary itself; the re-reading over that amendment returned
four again (§7.2), catching the amendment's own mis-placement and moving
back out the two clauses it had over-selected; and the review's second
pass (§7.3) corrected two declarations and completed R2's deferral,
moving no row. The slice was built on branch cut-3 and merged 2026-08-12;
the selection required no amendment.

---

> **Status amendment 2026-08-17.** `atoms` A8 landed; the live prerequisite
> descriptions below now name composition-root adoption alone. This changes no
> frozen selection. Original prerequisite text, preserved verbatim:
>
> **World persistence still fails it.** `atoms` A7 landed 2026-08-14, but A8 and
> composition-root adoption have not; the `nodes` contract deltas are not on
> `nodes` main, and the world layer's availability outcomes presuppose the index
> that carries them. The stop-rule outcome is unchanged from cut 2; the `atoms`
> boundary has narrowed.
>
> | packaging | X1–X12 | 12 | world export; X2 additionally gated on `atoms` A8 and composition-root adoption |
> | tamper log | L1–L13 | 13 | `atoms` A8 and composition-root adoption; the intent/reduction **semantics** are built here as functions over values (§3), and every L row's check sits at the durable chain |
>
> 3. **What cut 4 is.** The persistence seam and world persistence are no
>    longer independent candidates: the holdings store, the tamper log, and
>    the world index all wait on `atoms` A8 and composition-root adoption, and the first cut that
>    crosses a persistence boundary will take several of §5's groups at
>    once. Whether that is one cut or two is not ruled here.

## 1. What this cut is drawn against

Cut 2 (`2026-08-09-conformance-cut-2.md`) froze over 139 rows at the belief
seam; its slice landed the same day and required no amendment to the
selection. Two designs banked since then are what a third cut has to be
drawn against:

1. **The verified-holdings record** (`2026-08-10-verified-holdings-record-design.md`)
   closed the ramp's §8 item 2 — where a verified observation is recorded —
   and added **H1–H4**, the twelfth table. Its own §6: the H arms *"are
   acceptance criteria for the conformance cut that builds the persistence
   seam"*; none is claimed exercised anywhere.
2. **The act-report design** (`2026-08-11-act-report-design.md`) closed the
   run boundary's completion and report seam — the boundary-minted terminal
   record of an opened operation or the pre-intent refusal record, the
   operation intent's three-valued completion reading, and the durable home
   of a look's non-report — and added **T1–T8**, the thirteenth table. Its
   §6 names the cut-3 run-capture seam as fully designed, and states that it
   makes the candidate *eligible, not selected*.

That takes the corpus to **151 rows across thirteen tables**, every one
under its banked identifier. The practice of both prior cuts is inherited
unchanged: the unit of selection is the **exact assertion arm**, no selected
arm may depend on a boundary §3 excludes, and the selection **adds no rows
and mints no oracles**.

## 2. The boundary decision — the stop rule points the other way

Cut 1's stop rule, preserved verbatim and inherited here as the selection
criterion:

> **Stop rule.** The slice stops at the **last fully designed seam**.

Cut 2's §2 measured run capture against this rule and failed it at the
admission ramp's own residue: where a verified observation is recorded was
undesigned, so a run-capture slice would either design the holdings record
implicitly or build a run boundary that could admit nothing. Both halves of
that failure have since closed — the holdings record on 2026-08-10, and its
own named residue, the run boundary's completion and report seam, on
2026-08-11. **Run capture now passes the stop rule.**

**World persistence still fails it.** `atoms` A7 landed 2026-08-14 and A8 landed
2026-08-17, but composition-root adoption has not; the `nodes` contract deltas are not on
`nodes` main, and the world layer's availability outcomes presuppose the index
that carries them. The stop-rule outcome is unchanged from cut 2; the `atoms`
boundary has narrowed.

So cut 3 is drawn at the run boundary. Nothing here rules what cut 4 is.

Two boundary conditions frame the drawing, and neither is decided here:

1. **The admission ramp's three open questions stand** exactly as cut 2
   restated them. The slice performs no probe, so no arm reads a validity
   window; the holdings record is now *designed* but its store is not built
   here, so the recording question moves from undesigned to unbuilt without
   any arm of this cut touching it; and the partly-pinned rule's empirical
   corroboration remains evidence-not-design.
2. **The holdings design's own assignment is honored.** Its §6 assigns
   H1–H4 to the cut that builds the persistence seam. This cut selects **no
   H arm**, including arms that would be mechanically runnable over supplied
   values — H2's walk, H3's receipt — because selecting them against the
   banked sentence would spend the rows' force on weakened forms before the
   seam they were written for exists. The same assignment keeps `G9`'s
   independence-sabotage arm deferred: corrupting the promotion predicate
   requires the persisted substrate the sabotage launders through, and R10
   and R5 becoming runnable is necessary but not sufficient.

## 3. Step 1 — the boundaries the slice crosses

The slice is: **spec freezing and closure construction** — the analysis-spec
freeze with the nondeterminism contract enforced as a discriminated union,
recipe construction with role-partitioned inputs, identity canonicalization
consumed at run positions, and the refusal of every incomplete or
mis-shaped closure; **the execution boundary** — begin, execute, capture:
the operation intent opened before the act; execution through the
**minimal Snakemake adapter** — the fixtures supply a **held single-rule
workflow definition**; the boundary captures its identity as a **recipe**
member, renders only the engine configuration, environment, and argv
(computation §4.2b), and invokes the definition through the adapter as a
**real subprocess in a boundary-owned scratch root** over held fixture
inputs, the engine-native trace captured as the occurrence's *(amended
2026-08-11 across three passes — §7.1 corrected the frozen "one rendered
invocation per run, no engine" boundary, §7.2 the snapshot's member
placement, §7.3 the rendering surface: the boundary renders
configuration, never the definition; Appendix A preserves the frozen
text)* —
the code bundle and environment captured as held content, realized seeds
recorded per stream, and the result manifest constructed by the boundary
content-addressing every declared output on disk; **dataset
production, narrowly** — the output dataset's address as the §6.2 basis
projection over the manifest's content identities, the `produces` edge
emitted with the run, and prior bindings preserved; **replay and
verification-as-value** — re-execution of a recipe in a fresh scratch root,
equivalence evaluation, derived scope, and the verification constructed as
a value carrying its embedded report; and **completion and the report
layer** — the operation intent per opened operation, the three-valued
completion reading derived never stored, act-report construction reachable
only from the boundary, citable entry positions, and occurrence-bearing
report identity.

The intent and reduction semantics are the tamper-evident log's rules built
**as functions over values** — the same move cut 2 made building the ramp's
§6.2 projection while every W row stayed deferred: **every L row stays
deferred here**, and the semantics are exercised through T arms.

**A scratch root is staging, not confinement.** It is isolation by
location: the boundary creates it, renders into it, and hashes out of it,
and the subprocess may still read ambient host resources. Nothing in this
slice restricts what an execution can observe, so **R15 defers whole and
`clean-environment` is unreachable in every arm of this cut** — no receipt
this slice can produce qualifies, and every scope walk stops at the
branches genuine unconfined replays can derive.

> **Confinement landed 2026-09-01, conformance cut 13**
> (`2026-08-30-run-confinement-design.md`; results
> `../plans/2026-09-01-conformance-cut-13-results.md`). `boundary-policy/confined-v1`
> executes inside a fresh namespaced materialization of the digest-verified
> runtime closure, and `clean-environment` is reachable through its receipt.
> `boundary-policy/minimal-v1` is unchanged and remains the scratch root this
> paragraph describes.

It crosses **no** persistence boundary. Its **fixtures** perform no
network access and no IO outside the scratch roots and fixture inputs — a
property of what this cut's suite runs, which the **boundary does not
enforce**: an unconfined subprocess may read ambient host resources, and
only the confinement-capable boundary policy makes the stronger claim
checkable *(amended 2026-08-11, the third reading; Appendix A preserves
the frozen sentence)*. Three input-safety rules are the boundary's own
construction, not confinement: execution is by **direct argv with
`shell=False`**; engine **targets are separated from options**, an
option-like target rejected — `shell=False` prevents shell injection, not
option injection; and the entrypoint must resolve to a **regular file
inside the captured bundle** before anything runs. R17's selected
no-second-parameter-channel arm leans on all three. Stated exclusions,
each load-bearing:

- **No store of any kind.** Runs, intents, act-reports, and verifications
  are values; corpora exist as supplied node→corpus attributions with
  per-corpus pins, cut 2's fixture form. Every raw-write, explicit-import,
  and audit arm defers — T1's negative among them, which additionally waits
  on the tamper log and a valid anchored observer set.
- **No holdings store and no H arm** (§2 item 2).
- **No acquisition and no probe.** R10's refusal arm is selected; the
  acquisition path that records provenance is not built, and T7 defers
  whole — its publish-together claim is about store transactions this slice
  does not have.
- **The minimal adapter only.** The boundary wraps computation §6.4's one
  adapter at its smallest honest surface — fixture-held single-target,
  single-rule definitions, with Snakemake pinned in the frozen
  environment; every multi-rule, family, wildcard, definition-equality,
  and execution-coverage arm defers to the **full workflow surface**
  *(amended 2026-08-11, the third reading: this bullet read "No workflow
  engine", which was not a smaller execution boundary but a different
  one; Appendix A preserves it)*.
- **No confinement.** R15 defers whole, R13's import-resolution negative
  and R21's write-outside-root clause with it, to the
  **confinement-capable boundary policy** (computation §7.3a).
- **No rules store and no resolver** — P1's deferred arm is untouched.
- **No correction lifecycle and no retraction authoring.**
- **No world index and no authoring surface** — G5 and G7 stay at their
  boundaries.
- **Belief is consumed, never rebuilt.** Admission, the closure digest, and
  `science.belief.v1` are cut 2's built machinery; T4's inertness arms run
  against cut 2's already-admitted value fixtures, because no cut-3
  execution can reach admitted belief while `clean-environment` is
  unreachable.

## 4. Step 2 — the selection, arm by arm

Both prior cuts' rule is inherited unchanged: selection is over **exact
assertion arms**; a banked row may be partly selected and partly deferred;
no banked row is split; no selected arm may depend on an excluded boundary.
Each of the 151 rows is in exactly one of **five** states, cut 2's
definitions carried forward: **selected in full** means every arm no prior
cut exercised is selected here, and **selected in part** means this cut
selects at least one arm while at least one remains deferred — whatever any
prior cut did. Under that reading `R5` is selected for the first time (cut
2 said in as many words that its consequences exercised through `G9` were
*implication, not selection*), and `G9` moves from part-exercised to
selected in part because this cut adds an arm to it.

| state | rows | n |
|---|---|---|
| **selected in full** — every previously unexercised arm | G2a, G4, M2, R1, R3, R6, R7, R8, R11, R14, R17, R18, T3, T6, T8 | **15** |
| **selected in part** — the arm split stated below | G9, N2, R2, R4, R5, R9, R10, R12, R13, R16, R19, R20, R21, R22, R23, T1, T2, T4, T5 | **19** |
| **fully exercised by prior cuts** | M4, M7, M9, M10, M11, M13 (cut 1); G1, G2b, G6, M6, M8, P2–P9 (cut 2) | 19 |
| **part-exercised by prior cuts, cut 3 adds nothing** | G2c, G3, G8, S5, S6, P1, D3, D6, D7, M5 | 10 |
| **fully deferred** — no arm in any cut | §5 | 88 |

### 4.1 Selected in full — 15 rows *(as amended, §7.1–§7.2; the frozen table read 17, with R5 and R9 here and R2 in §4.2 — R2 was restored by §7.1 and split again by §7.2)*

| row | what the slice must demonstrate |
|---|---|
| **G2a** | the boundary refuses to begin a run naming no frozen spec, and one naming a spec frozen mid-execution — refused, not downgraded; the negative: an out-of-band run with a spec frozen afterwards and attached is **undetectable**, pinning that G2a is about what the boundary will start |
| **G4** | an unreferenced successor to a recorded failed replay is refused; the negative: a discarded failed attempt is undetectable — activeness and reference here are over the slice's value state, the recorded-failure set the boundary holds |
| **M2** | substituting any run input with a differently-addressed dataset moves the assessment identity, every input, every time; an input no declared role partition covers is refused, not ignored — the three-hop binding path (role-partitioned `inputs` → R2 → assessment identity) pinned by test |
| **R1** | an incomplete closure is refused and no run value is minted; the curation note or source-assertion is authored as a separate explicit act before the member is supplied; no `unknown`- or `attested`-valued component is representable on a run in any position; a bare lockfile digest is refused as `environment_identity` |
| **R3** | two executions of one recipe are two runs — equal recipe identity, distinct addresses, both referenceable; they do not collapse; identical `started_at`, `actor`, and `host_realization` still yield distinct addresses, the minted `event_token` doing the separating |
| **R6** | an un-replayable run creates no verification and changes no assessment state; restoring availability changes nothing until a replay actually runs |
| **R7** | a `dataset-production` run with an `assesses` descendant is refused; an `assessment` run whose spec has no `target` is refused; zero `observes` inputs admit nothing at any quantity of `reads` |
| **R8** | editing the equivalence rule after a failing replay mints a new spec identity; the original run's closure still names the old spec; the successor references the superseded one; the failing verification **remains active** in the slice's value state |
| **R11** | a tolerance on a `dataset-production` replay is refused; a nondeterministic transform's replay yields all four — a different dataset entity, a `failed` verification under `dataset-content-equality/v1`, prior assessments still bound to the prior dataset, no belief moved; the dataset-production verification carries no `verifies → assessment` edge |
| **R14** | canonicalization exercised at run and closure positions: binary floats refused everywhere, all four §4.3 collisions walked, `NaN`/`Infinity` refused in every position, kind-domain separation, and the `v2`-never-equals-`v1` negative |
| **R17** | no path supplies `inputs`, `parameters`, or any part of the nondeterminism contract on an assessment run — including through `invocation`, which holds bindings, not values; seed shopping cannot occur at all, a changed root requiring a successor spec; the limit is pinned: a deleted or never-recorded attempt is undetectable, G4's boundary; a `dataset-production` recipe **is** authored directly, seed plan included |
| **R18** | two verifications over one run pair relying on different certifications have distinct addresses; the report carries the certification claim, both conformance results, the relied-on receipt identities, and the exact rule bindings **inline**; the verification basis names the report, not the evidence twice; deleting the external certification record from the value set leaves the verification unchanged and valid |
| **T3** | all three completion states built over value sets: an unmatched intent reads **unfinished**; an unreadable fulfillment pointer reads **indeterminate**, never collapsed into unfinished; a fulfilled intent reads **closed**; no status field is spellable on any record; removing a report from the held value set moves its operation **closed → indeterminate**, not unfinished |
| **T6** | permuting two entries moves the report identity — order is identity-bearing; an **(act-report ref, entry index)** citation resolves to exactly one entry; an out-of-range index is refused at the citing site; the R18 arm — deleting the cited report from the value set leaves the verification unchanged, its embedded content intact |
| **T8** | two operations with equal actors, timestamps, and entries but distinct `event_token`s have distinct identities; every facet member mutated in turn moves the identity; no ordinary API path edits, supersedes, or deletes a report |

### 4.2 Selected in part — the arm split, stated exactly

| row | arms **in** cut 3 | arms **deferred**, and on what |
|---|---|---|
| **T5** | the type-union unspellability refusals: `byte-locator-untested` unspellable on managed-mutation, record-import, and subject-evaluation entries | the *locator entry whose request began* refusal and the *preflight refusal versus deliberate post-stop skip* distinction — began-ness is not an entry field, and both are behaviors of the **acquisition** operation this slice does not run; the *no entry outcome constructs an observation* negative — vacuous here, where no observation-minting machinery exists — with the **persistence seam** |
| **G9** | the **replay-eligibility third** of R5's answer: making bytes unreachable here while a controlled copy remains held leaves the digest and admission halves unchanged — cut 2's arms — and now reads replay eligibility *not available*, the third the run boundary supplies | unchanged from cut 2: the *minted as a world entity* clause (**W3**'s property, the world boundary) and the **independence sabotage**, which stays with the **persistence seam** on the holdings design's own assignment (§2 item 2) |
| **T1** | the ordinary-API and type claim: no construction path authors an act-report — direct authoring and every API taking report fields as input are absent; the constructor is reachable only from the boundary | the **import** arm — structurally-validated, unauthenticated, attributed, inert entry of another observer's report is a store operation — and the **raw-write negative**, which needs the tamper log and a valid anchored observer set |
| **T2** | the shape refusals: a dataset-production attempt opens the **operation intent**, and the assessment-run intent is unspellable without a `spec_identity`; negative (b): a complete non-conforming execution mints a **run**, never an act-report; the pre-intent refusal: a missing-spec run request refuses **before** any intent, and a surviving boundary publishes an *unfulfilling* act-report that fulfills nothing | **one started operation, one intent, one terminal record** — qualification, the second-registration-malformed rule, and the no-act-before-intent ordering are claims about committed registrations in a root, deferred with **persistence**; the crash-leaves-no-trace clause with them, there being no durable trace here to interrogate |
| **T4** | adding and removing reports leaves the belief digest, admission, and eligibility byte-unchanged — run against **cut 2's already-admitted value fixtures** (§3), the only admitted belief this cut can reach | the **coverage projection** clause and the *unfinished operation blocks nothing* arm — the holdings design's §5 projection, unbuilt with H — and the observation-deletion negative, whose record-layer consequences are the holdings record's |
| **R2** | every §4.2 closure member mutated in turn moves the run address — the workflow-definition snapshot among them, as a **recipe** member; the negative over the components the minimal surface can vary: two executions of one recipe have **equal recipe identities** despite differing realized seeds and event tokens | the negative's **trace and job-ID** components — the minimal one-rule fixture provides no differing-job-ID state, and equal recipes on this surface can produce equal raw traces (equal job IDs, rule names, wildcards, inputs, and outputs), so no mutation guarantees a differing per-execution trace observation — the **full workflow surface** *(amended 2026-08-11 across three passes: the frozen cut split this row, §7.1 restored it to full, §7.2 and §7.3 split it again component by component; Appendix A preserves the frozen cell)* |
| **R5** | bytes unreachable here while a controlled copy remains held: `belief_input_digest` unchanged, admission unchanged, replay eligibility **not available** — never `unverified`, never `failed`; negative (b): removing the corpus attribution holding the records yields **`not-available`**, never an unchanged belief | negative (a) — destroying the **last held copy** is enacted only by a managed deletion recording an `absent` observation (holdings §3), and raw deletion deliberately leaves heldness unchanged until audit, so over supplied observations the destruction is a fixture edit — the **persistence seam** *(amended 2026-08-11, the third reading; the frozen cut selected the row in full — Appendix A preserves its cell)* |
| **R9** | an unreadable output, a missing output, and a reader error each yield `inconclusive` | the *admission does not follow* conjunct — with `clean-environment` unreachable, admission never follows a verdict here, the same defect §7 item 3 removed from R16 — the **confinement-capable boundary policy** *(amended 2026-08-11, the third reading; the frozen cut selected the row in full — Appendix A preserves its cell)* |
| **R4** | the derived-scope walk over the branches genuine unconfined replays can produce: `not-certified`, `same-environment`, `independent-implementation`; no authored `scope`; negatives (a)–(c): a hostname change stays `same-environment` — no receipt, so a machine name buys nothing; a comment change is `not-certified`, never `independent-implementation`; different `spec_identity` is `not-certified` | the **`clean-environment`** row of the walk and negative (d) — both need a qualifying confinement receipt, the **confinement-capable boundary policy** |
| **R10** | a URL- or accession-valued input is refused as a run input; no fallback synthesizes a dataset entity from the URL | *"the acquisition path records dataset provenance instead"* — there is no acquisition here |
| **R12** | the boundary refuses a run naming no frozen spec identity; the negative: freeze a spec after an out-of-band execution, attach it, and the ordering is undetectable — content addressing is not pre-registration | the **boundary-mediated strengthening** — an intent entry as a removal-detectable witness — which is conditional on the **tamper log** |
| **R13** | modifying an untracked file inside `code_roots` changes `code_identity`; modifying a tracked-but-uncommitted file does the same — the capture is real | the negative — a local import resolving outside the bundle and held environment is refused — which is an observation about what execution can reach, the **confinement-capable boundary policy** |
| **R16** | a complete closure whose realized seeds violate its seed plan mints a run, is **non-conforming**, and derives `not-certified`; no equivalence rule can read an occurrence — the evaluator's signature is `(result, result)` and admits no job-set argument | the *"nothing is admitted"* conjunct — failable only against a pair with **qualifying receipts**, which needs the confinement boundary, since with `clean-environment` unreachable admission never follows scope here and the conjunct passes under its own mutation — the **confinement-capable boundary policy**; the trace-membership and target-satisfaction clauses *(amended 2026-08-11 twice: §7.1 selected both on the minimal adapter's arrival; the §7.2 re-reading moved both back out — a single-rule execution **is** its derived trace by construction, and an unsatisfied single target is a missing declared output that R21's selected arm refuses upstream, so neither clause can fail here)* — and every family, definition-equality, multi-stream, and execution-coverage arm — the **full workflow surface** |
| **R19** | the constructor's closed list: ordered run refs, an optional certification, the explicitly selected contract identity and epoch, and the optional report-position citation — nothing else, each extra argument refused; the evaluator's identity resolves from the original run's frozen spec and its implementation from the frozen `rule_bindings`; a mixed-shape pair is refused | explicit import with its refusal-before-write, both availability transitions, the audit and its contradiction finding, and negatives (c)–(e) — the **store**, the **world resolver**, and the **audit** |
| **R20** | the union's type refusals: `deterministic` with a plan, `stochastic-unseeded` with a plan, and `seeded` without one are unspellable; a multi-root plan with no total stream mapping is refused; `stochastic-unseeded` with a rationale **is** freezable; negative (a)'s freeze-time half — unseeded beside a bitwise rule caught at freeze; negative (b) — a two-stream, two-root plan cannot record seeds keyed by job alone; negative (d)'s spellability half — the frozen spec names logical streams only, no workflow rule or process name spellable | negative (a)'s **import** half (the import boundary); negative (c) — per-family obligations are workflow claims — and negative (d)'s two-decomposition comparison, both the **full workflow surface** |
| **R21** | the manifest is constructed by the boundary and there is no supplied-manifest path; a missing declared output, duplicate logical name, undeclared entry, or digest mismatch mints **no run**; intermediates are excluded and a replay with different scratch files yields an equal manifest; negative (a): a scheduling-only option leaves the recipe identity unchanged; negative (b)'s refusals: absolute and root-escaping output paths are refused; negative (c): one recipe under two differently-mounted scratch roots yields equal recipe identities, each mapping only in its receipt; negative (e): a complete closure disobeyed is a non-conforming run, an incompletable closure is a refusal | the two-target arm and negative (d) — the **full workflow surface**; negative (b)'s *write outside the root fails closed* and negative (c)'s `clean-environment` reachability — the **confinement-capable boundary policy** |
| **R22** | the assessment constructor takes only a run ref — every named facet parameter is absent; the derived `outcome` moves only with the result or the rule; `estimand` and `applicability` copy from the frozen spec; a failing rule evaluator produces no assessment and records a finding, never `inconclusive`; negative (a): narrowing `applicability` needs a successor spec and a new run; negative (b)'s **facet-exchange** half: exchanging the facets of two assessments moves the belief digest, composing with cut 2's keyed-facet digest; the **reach** arm: an inline exclusion certification differing between two recipes yields byte-identical facets and a differing digest, and editing the certification alone mints a recipe and moves nothing; an implementation failing its fixtures is not that rule, checked over **supplied** implementations and their fixtures | the *unresolvable interpretation rule is refused* clause — resolution against a held implementation or a registry entry is the **rules store and resolver**, excluded exactly as P1's deferred arm records, and the in-slice form ("no binding supplied → refuse") is a different, weaker claim; negative (b)'s **raw-write** half and negative (c) — corpus paths, explicit import, and the audit — the **store** |
| **R23** | the fifth crossing, exactly: the output dataset's address is the §6.2 basis projection over the manifest's content identities; the `produces` edge is emitted with the run and no path attaches one naming an output absent from the manifest; no `produced_by` edge is reachable in either direction; negative (a): byte-identical output under two logical names yields **one** address; **replay cardinality**: one address, two `produces` edges from two runs, no existing node mutated and the prior lineage basis unchanged; the certified-exclusion mechanics: inline on the `reads` entry with rationale and attribution, adding or withdrawing it mints a different recipe and no run until executed; negative (h)'s first half: reclassifying an input's role mints a different recipe | the `derived_from` view, the independence-multiplier and omission arms, every deletion, divergence, coverage, receipt, snapshot, merge, and conflict arm, negatives (e)–(g), and the raw-written-basis audit — the **store**, the **world index**, and the **audit** |
| **N2** | the doctrine over **cut 3's selected arms**: every arm declared as data with its row, assertion, source mutation, and exact named checks; the harness audits for `vacuous`, `stale`, `mixed`, `uncollected`, and the class-node collapse, reporting malformed contract content rather than passing it | the doctrine over the rows no cut selects, exactly as both prior cuts left it |

### 4.3 Standing from prior cuts

**M4, M7, M9, M10, M11, M13** (cut 1) and **G1, G2b, G6, M6, M8, P2–P9**
(cut 2, completing M6 and M8 jointly with cut 1) are fully exercised;
nothing remains. Ten rows are part-exercised with remainders this cut does
not touch, each still waiting where its prior cut left it: **G2c** and
**G8** on the correction lifecycle's retraction records; **G3** on world
persistence (the corpus-move negative); **S5** on the write API's snapshot
walk; **S6** on the first successor policy admitting unequal weights;
**P1** on the rules store; **D3** on the world index; **D6** on the
compiled registry; **D7** on the write boundary and the index; and **M5**
on persistence — cut 2 supplied belief, this cut supplies runs, and the
founding case's mint-and-edit walk still needs the store, so its blocker
remains half-discharged and it gains no arm here.

## 5. Step 3 — fully deferred rows, grouped by unblocking subsystem

88 of 151 rows have no arm in any cut. Grouping is by the subsystem that
unblocks them, re-read against this slice's boundary; cut 2's groups carry
forward except where this cut's boundary moves a row, and each move is
stated.

| group | rows | n | unblocked by |
|---|---|---|---|
| the persistence seam | H1–H4, **T7** | 5 | the holdings store and the transactional root — the holdings design's own assignment (§2 item 2); T7's publish-together claim is about store transactions |
| world addressing | W1–W16, W5a, W8a, W8b | 19 | the write boundary and the index, unchanged from cut 2 |
| substrate write & traversal | S1, S1a, S2, S3, S4, S7, S8 | 7 | the write API and the stored-corpus traversal, unchanged |
| kernel, at other boundaries | G5, G7 | 2 | the authoring surface and kind registry; the mint path — unchanged |
| packaging | X1–X12 | 12 | world export; X2 additionally gated on composition-root adoption |
| tamper log | L1–L13 | 13 | composition-root adoption; the intent/reduction **semantics** are built here as functions over values (§3), and every L row's check sits at the durable chain |
| correction lifecycle | C1–C10 | 10 | retraction records, unchanged |
| normative contract — contract cut | N1, N3 | 2 | the first contract cut |
| normative contract — certification | N4–N9 | 6 | instrument certification and parity machinery |
| normative contract — legacy adoption | N10 | 1 | the adoption gate |
| domain boundary | D1, D2, D4, D5, D8, D9, D10 | 7 | facets, manifests, and the registry compile |
| formal model | M1, M3, M12 | 3 | M1 the instrumented resolver; M3 retraction graphs and consolidation; M12 the extraction path. **M2 leaves this group** — its arms are the run-input binding path, which this slice builds (§4.1) |
| confinement | R15 | 1 | the **confinement-capable boundary policy** — a scratch root is staging, not confinement (§3) |

## 6. Accounting, freeze, and amendment discipline

**15 selected in full + 19 in part + 19 fully exercised by prior cuts + 10
part-exercised with remainders deferred + 88 fully deferred = 151** *(as
amended; the frozen accounting read 17 + 17, §7.1's read 16 + 18, and the
§7.2 re-reading settled 15 + 19 — the total intact at every step)*. Every
banked row is classified into exactly one state. As in both prior cuts,
**no count of arms is offered as a denominator**: the banked rows do not
enumerate their arms formally, and the splits in §4.2 are this document's
reading of each row's test cell.

> **Freeze.** This cut is frozen on the date in the status header, before
> any cut-3 implementation exists. **Results are recorded separately**,
> never by editing the selection. If the cut must change, the original
> selection is **preserved verbatim** alongside the amendment, with the
> reason stated.

The slice's acceptance criteria are the selected arms as frozen — it adds
no guarantee table of its own.

## 7. The second reader

Cut 1's limitation 8 asked for a second reader on cut 2 and got one; every
classification error found in cuts 1 and 2 moved toward overstating
coverage, so the reading is now standing practice. It ran **before this
freeze**: a reader with no stake in the draft was given the banked row
texts and §3's boundary declaration — not this document's rationale — and
instructed to attack the selection in the known failure direction, moving
arms **out**.

It returned four findings; every arm a finding moved, it moved out.

1. **T5 was over-selected as whole.** The slice's only honest entry
   producer is the run-attempt operation, so every locator entry in a T5
   test is fixture-constructed. The *"request began"* refusal is not a
   type refusal at all — began-ness is no entry field, and only an
   acquisition operation begins locator requests — and the *preflight
   refusal versus post-stop skip* distinction is likewise the acquisition
   operation's behavior: a fixture entry carrying a test-invented
   began-state certifies the fixture. The *no entry outcome constructs an
   observation* negative is vacuous here, where no observation-minting
   machinery exists to fail it. T5 moved to selected in part, keeping only
   the type-union unspellability refusals.
2. **R2's negative leaned on the excluded engine.** *"Despite differing
   traces, job ids and realized seeds"* — the engine-native trace is an
   occurrence member only an engine observes, so two single-subprocess
   executions have no traces or job ids to differ, and the in-slice
   negative collapses to realized seeds and event tokens: a weaker
   assertion wearing the banked arm's name. R2 moved to selected in part,
   the trace and job-id halves deferred to the Snakemake adapter.
3. **R16's "nothing is admitted" conjunct could not fail.** The banked arm
   runs over a pair with *qualifying receipts* — the confinement boundary
   — and with `clean-environment` unreachable, admission never follows
   scope in this slice: under the arm's own mutation the conjunct still
   passes. Struck from the in-cell; the admission-blocking force of seed
   non-conformance defers with the confinement-capable boundary policy.
4. **R22's unresolvable-rule clause sat on the rules store.** The banked
   refusal resolves against a held implementation *or a registry entry
   with fixtures* — the resolver §3 excludes, exactly as cut 2's P1 cell
   ruled — and the in-slice form, "no binding supplied → refuse," is a
   different, weaker claim. The clause moved out; the fixtures check
   survives only over supplied implementations.

The reading verified the accounting before and after the moves: 151 rows,
each in exactly one state, the full/part split shifting 19/15 → 17/17
with the total intact.

### 7.1 The third reading — the pre-merge review, and what it amended

The review before merge ran against the frozen 17/17 selection and
returned four findings. Per §6's freeze rule each is recorded as an
**amendment**: every amended site carries a note naming its change,
**Appendix A preserves the frozen text verbatim**, and this section
carries the reasons.

1. **The engine-free subprocess was not the banked execution boundary.**
   Every run occurrence carries the engine-native trace as a closure
   member (computation §4.2), and §6.4's ruling wraps the engine rather
   than substituting a Science-owned runner — so "no workflow engine" was
   not a smaller execution boundary but a **different** one, and every
   genuine execution arm would have run against machinery the banked rows
   do not describe. Amended: §3's execution crossing wraps the **minimal
   Snakemake adapter** — boundary-rendered single-target, single-rule
   definitions executed through the engine, the definition snapshot and
   trace captured as occurrence members — and the workflow deferral
   target is renamed from "the Snakemake adapter" to the **full workflow
   surface**, since the adapter now exists at its minimal surface and an
   unblocking event that has occurred cannot honestly name a deferral.
   **R2 returns to selected in full** — its traces and job ids now exist
   to differ — and **R16's in-cell gains** the two things single-run
   job-set conformance actually asserts, trace membership and target
   satisfaction. This is the one finding in three readings whose
   correction moved coverage **up**, and it moved because the boundary
   was wrong, not because an arm was re-read: the second reading's R2
   finding was a correct reading of a mis-drawn boundary.
2. **R5's last-copy negative needed the managed-deletion path.**
   "Destroy the last held copy" is enacted by a managed deletion
   recording an `absent` observation (holdings §3); raw deletion
   deliberately leaves heldness unchanged until audit, and over supplied
   observations the destruction is a fixture edit. Negative (a) defers to
   the persistence seam; **R5 moves to selected in part**.
3. **R9's admission conjunct could not fail** — the defect §7 item 3
   removed from R16, in a second row: with `clean-environment`
   unreachable, admission never follows a verdict here, so *"admission
   does not follow"* survives a verdict mutation. The three
   `inconclusive` verdict checks stand; the admission consequence defers
   with the confinement-capable boundary policy; **R9 moves to selected
   in part**.
4. **§3's IO and network claims contradicted the unconfined-process
   ruling.** A subprocess that may read ambient host resources cannot be
   claimed to perform no IO outside scratch roots. The claim is now that
   the **fixtures** perform neither and the **boundary does not enforce
   it**, and two input-safety rules are pinned as boundary construction,
   not confinement: direct-argv execution with `shell=False`, and
   bundle-relative entrypoint validation.

The amended accounting: **16 + 18 + 19 + 10 + 88 = 151**, every row in
exactly one state.

### 7.2 The re-reading over the amendment

A scoped re-reading ran over the amended cells — the restored R2, the
widened R16, the R5 and R9 splits, and §3's amended execution crossing —
with the same instruction and the rationale withheld. It returned four
findings: three moved arms out, and one corrected the amendment's own
text.

1. **§7.1's amendment mis-placed the definition snapshot.** The banked
   member table puts `workflow_definition_identity` in the **recipe** —
   computation §6.2 rules it "declared, pre-execution — recipe member" —
   and only the engine-native trace is the occurrence's. The amendment's
   first form declared both as occurrence members, the inverse of the
   mis-placement the computation design's own scar text records. Corrected
   at §3 — a correction to the crossing declaration, not a selection move.
2. **R16's trace-membership clause cannot fail on the minimal surface.**
   A single-rule execution **is** its engine-derived trace by
   construction; the only exercisable form is a hand-built occurrence
   naming a phantom job key, a fixture no boundary emits, certifying the
   evaluator rather than the execution property the banked clause names.
   Moved back out to the full workflow surface, where the frozen cut had
   it.
3. **R16's target-satisfaction clause is pre-empted by R21's selected
   manifest arm.** On the minimal surface an unsatisfied single target is
   a missing declared output, and R21 rules that state mints **no run at
   all** — so no minted run bearing the state ever reaches the
   conformance check, and the clause passes under any mutation. The state
   the banked clause guards needs a target distinct from the declared
   outputs — a multi-node DAG. Moved back out with the trace clause.
4. **R2's job-id component has no producible difference.** Engine-native
   job ids are DAG-assigned and deterministic, so two executions of one
   single-rule definition carry equal job ids and no mutation produces
   the differing state. R2 moved to selected in part, its surviving
   negative running over realized seeds, event tokens, and per-execution
   trace observations.

Explicit passes, recorded because their absence would read as unchecked:
every other selected arm is exercisable on single-rule definitions; no
deferred cell or §5 group names an unblocking event that has occurred;
R5's and R9's retained arms are failable; and no selected arm assumes
enforcement the boundary does not provide. The re-read accounting: **15 +
19 + 19 + 10 + 88 = 151**, every row in exactly one state.

### 7.3 The review's second pass

The pre-merge review read the amended document again and returned four
findings. None moved a row; the accounting stands at 15 + 19.

1. **R2's trace component followed its job-ID component out.** On the
   one-rule surface equal recipes can produce equal raw traces — equal
   job IDs, rule names, wildcards, inputs, and outputs — and the document
   named no mutation guaranteeing a differing per-execution trace
   observation. §7.2's rationale claimed broadly that "job ids are
   DAG-assigned and deterministic"; the claim recorded now is only what
   is established — **this minimal fixture provides no differing-job-ID
   state**, the engine exposing job ids as internal DAG assignments, not
   a stability contract. R2's negative retains realized seeds and event
   tokens.
2. **The boundary must not render the workflow definition.** The banked
   contract makes the definition a declared input, and the boundary's
   rendering surface is exactly engine configuration, environment, and
   argv (computation §4.2b) — "renders a workflow definition" risked a
   Science-owned Snakefile generator, the substitution §6.4 refuses from
   the other side. §3 now reads: the fixtures supply a held single-rule
   definition; the boundary captures its identity, renders
   configuration, environment, and argv, and invokes it through the
   adapter.
3. **The preservation claim was made good.** The amendment notes quoted
   fragments and summaries where §6's rule requires the frozen text
   itself; R5's and R9's frozen cells were not preserved at all. Appendix
   A now carries the frozen passages verbatim, and every amended site
   points to it.
4. **The argv rule was completed.** `shell=False` prevents shell
   injection, not option injection: engine targets are now separated
   from options with option-like targets rejected, and the entrypoint
   must resolve to a regular file inside the captured bundle — all three
   rules necessary for R17's selected no-second-parameter-channel arm.

## 8. What this changes elsewhere

Applied in the same change as this document. Nothing amends a banked row;
every entry is navigational.

| site | change |
|---|---|
| README | design count **twenty-one → twenty-two**; the table gains this document; the status section records that a third cut is drawn at the run boundary |
| guide `contracts-and-adoption.md` | the cuts paragraph gains cut 3: what it selects, and that seven of the twelve rows banked after cut 2 — T1–T6 and T8 — gain their first arms while H1–H4 and T7 wait on the persistence seam; this document joins `sources` |
| guide `open-questions.md` | the third-cut entry is replaced: cut 3 is drawn, taking run capture; what remains open is what §5 defers — the persistence seam, world persistence, and the subsystems behind them; this document joins `sources` |
| corpus guards | no new rows and no new tables; `_COUNT_WORDS` gains `22: "Twenty-two"`, and the design-document glob discovers the file itself |

## 9. Limitations

1. **The arm splits are a reading, not a property of the rows** — both
   prior cuts' limitation, inherited whole.
2. **Several banked arms are exercised in stated weaker slice-forms** —
   T3's value-set deletion, G4's and R8's activeness over value state,
   T8's ordinary-API-only immutability — with
   their full force explicitly re-owed at the persistence seam. A reader
   tallying "arms exercised" without §4's caveats would over-count what
   this slice demonstrates.
3. **No execution in this cut can reach `clean-environment`**, so no cut-3
   execution reaches admitted belief, and T4's inertness arms lean on cut
   2's fixtures (§3). The scope walk this cut certifies is genuinely
   partial, and the confinement-capable boundary policy owns the rest.
4. **Real subprocess execution puts host variability inside the suite.**
   Fixture recipes must be deterministic by construction, and a flake here
   is an operational defect, not an epistemic one — but the suite's first
   nondeterministic failure will arrive through this cut, and triage
   discipline is part of the slice's cost.
5. **R16's selected arms assert seed-plan conformance and the evaluator's
   signature and nothing more.** Trace membership, target satisfaction,
   families, multi-stream obligations, and execution coverage all wait on
   the full workflow surface, and a green R16 here demonstrates none of
   them.
6. **The second reading is one model-instructed pass, not adjudication** —
   cut 2's limitation 4, inherited unchanged.
7. **This cut is drawn the same day two of its tables banked.** Cut 2 was
   drawn against designs banked days earlier; T1–T8 froze hours before
   this selection read them. The compensating control is the same one the
   corpus always uses — the second reading and the merge review — but a
   misreading of an hours-old row has had fewer eyes than any prior cut's
   inputs.

## 10. Open questions

1. **The admission ramp's three questions stand unchanged**, one changed
   in kind: where verified holdings are recorded is now **designed and
   unbuilt** — the persistence seam is the corpus's most consequential
   unbuilt subsystem, blocking H whole, T1's negative, T2's ordering arms,
   T7, M5's remainder, and the independence sabotage (§2).
2. **Split or carry the compound rows.** Nineteen arm-splits in this cut
   as amended, eleven in cut 2, five in cut 1. The F11 trade stands docketed and
   undecided, and recurs at every cut until someone pays one of its two
   costs.
3. **What cut 4 is.** The persistence seam and world persistence are no
   longer independent candidates: the holdings store, the tamper log, and
   the world index all wait on composition-root adoption, and the first cut that
   crosses a persistence boundary will take several of §5's groups at
   once. Whether that is one cut or two is not ruled here.

## Appendix A — the frozen text, preserved verbatim

§6's freeze rule requires the original selection preserved verbatim
alongside any amendment. The notes at each amended site name the change;
this appendix is the preservation. Every passage below is byte-verbatim
from the freeze, wrapping included.

**The frozen state table's selection rows (17/17):**

```
| **selected in full** — every previously unexercised arm | G2a, G4, M2, R1, R3, R5, R6, R7, R8, R9, R11, R14, R17, R18, T3, T6, T8 | **17** |
| **selected in part** — the arm split stated below | G9, N2, R2, R4, R10, R12, R13, R16, R19, R20, R21, R22, R23, T1, T2, T4, T5 | **17** |
```

**§3's execution crossing, as frozen** (amended by §7.1, §7.2, and §7.3;
the final line continues into the unamended dataset-production crossing):

```
the operation intent opened before the act, one rendered invocation per run
executed as a **real subprocess in a boundary-owned scratch root** over held
fixture inputs, the code bundle and environment captured as held content,
realized seeds recorded per stream, and the result manifest constructed by
the boundary content-addressing every declared output on disk; **dataset
```

**§3's IO sentence, as frozen** (amended by §7.1 item 4):

```
It crosses **no** persistence boundary and performs **no** IO outside its
scratch roots and fixture inputs. Stated exclusions, each load-bearing:
```

**§3's acquisition and engine bullets, as frozen** (amended by §7.1):

```
- **No acquisition, no network, no probe.** R10's refusal arm is selected;
  the acquisition path that records provenance is not built, and T7 defers
  whole — its publish-together claim is about store transactions this slice
  does not have.
- **No workflow engine.** The boundary renders single invocations; every
  trace, family, definition-equality, and target-enumeration arm defers to
  the **Snakemake adapter** (computation §6.4's one adapter).
```

**§4.1's R5 and R9 cells, as frozen** (moved to §4.2 by §7.1):

```
| **R5** | bytes unreachable here while a controlled copy remains held: `belief_input_digest` unchanged, admission unchanged, replay eligibility **not available** — never `unverified`, never `failed`; destroying the last held copy of an `observes` input fails eligibility and **changes** admission; removing the corpus attribution holding the records yields **`not-available`**, never an unchanged belief |
| **R9** | an unreadable output, a missing output, and a reader error each yield `inconclusive`, and admission does not follow |
```

**§4.2's R2 cell, as frozen** (restored to full by §7.1, split again by
§7.2 and §7.3):

```
| **R2** | every §4.2 closure member mutated in turn moves the run address; the negative's in-slice half: two executions of one recipe have **equal recipe identities** despite differing realized seeds and event tokens | the negative's **trace and job-id** halves — the engine-native execution trace is an occurrence member only an engine observes, so two single-subprocess executions have no traces or job ids to differ — the **Snakemake adapter** |
```

**§4.2's R16 cell, as frozen** (its trace and target clauses selected by
§7.1 and moved back out by §7.2):

```
| **R16** | a complete closure whose realized seeds violate its seed plan mints a run, is **non-conforming**, and derives `not-certified`; no equivalence rule can read an occurrence — the evaluator's signature is `(result, result)` and admits no job-set argument | the *"nothing is admitted"* conjunct — failable only against a pair with **qualifying receipts**, which needs the confinement boundary, since with `clean-environment` unreachable admission never follows scope here and the conjunct passes under its own mutation — the **confinement-capable boundary policy**; every trace-membership, target-satisfaction, family, definition-equality, multi-stream, and execution-coverage arm — the **Snakemake adapter** |
```
