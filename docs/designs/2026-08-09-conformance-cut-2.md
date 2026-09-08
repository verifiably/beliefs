# Conformance cut 2 — the belief seam, frozen prospectively

**Status.** Draft 2026-08-09, **frozen before any cut-2 implementation exists**,
on cut 1's discipline: a cut drawn after implementation is a list of what
happened to pass. Drawn over the **139-row** corpus — cut 1's frozen denominator
of **126 is untouched**, and nothing here amends a banked row. Selects **13 rows
in full and 11 in part**; §5 classifies the other 115 (six of them fully
exercised by cut 1 and one part-exercised), and §6 accounts for all 139. The
second reader cut 1's limitation 8 asked for has read this selection before the
freeze, and a third reading — the review before merge — followed it; §7 records
the fourteen findings and the two more, and what each moved — every arm a
finding moved, it moved **out**, the direction cut 1 predicted. The admission
ramp's three open questions are **boundary conditions on this cut, restated in
§2.1, and none of them is decided here.** The slice was built 2026-08-09; the
selection required no amendment, and S6(f)'s tie-break clause — structurally
unsabotageable under `science.belief.v1` in this suite — is recorded rather
than hidden (`python/tests/n2_arms_cut2.py`, S6). *Status append 2026-08-10:
the design §10 item 1 named as the most consequential open question landed —
`2026-08-10-verified-holdings-record-design.md`.*

---

> **Status amendment 2026-08-17.** `atoms` A8 landed; the live prerequisite
> descriptions below now name composition-root adoption alone. This changes no
> frozen selection. Original prerequisite text, preserved verbatim:
>
> **World persistence's prerequisites are not discharged.** The world-index build
> is X1–X12 with **X2 gated on `atoms` A8 and composition-root adoption**. A7's
> engine half landed 2026-08-14, but neither remaining prerequisite has; the `nodes`
> contract deltas (ledger artifact 3) block profile implementation and are not on
> `nodes` main; and the world layer's availability outcomes presuppose the index
> that carries them. A cut there today would be partial selections arranged
> around an absent substrate.
>
> | packaging | X1–X12 | 12 | world export; X2 additionally gated on `atoms` A8 and composition-root adoption |
> | tamper log | L1–L13 | 13 | `atoms` A8 and composition-root adoption |
>
> 3. **What cut 3 is.** §2 argues run capture and world persistence each fail a
>    prerequisite today; it does not rank them. The first is unblocked by
>    designing the holdings record; the second by `atoms` A8,
>    composition-root adoption, and the `nodes` deltas. A7's engine half landed
>    2026-08-14 without changing that stop-rule outcome. Whichever prerequisite
>    set lands first likely names the cut.

## 1. What this cut is drawn against

Cut 1 (`2026-08-05-review-disposition-and-conformance-cut-1.md` §5) froze over
126 rows and selected eleven — six whole, five at named assertion arms — against
a slice bounded at typed claim construction, canonical projection, identity,
decode and cross-language parity. The slice was built and merged 2026-08-07 and
required no amendment to the selection.

Three things changed the corpus after that freeze, and they are what a second
cut has to be drawn against:

1. **The belief policy banked** (`2026-08-05-belief-policy-design.md`), adding
   **P1–P9** — the eleventh table — and discharging the prerequisite cut 1's
   §5.5 stop rule placed ahead of any slice that computes belief. Its own
   limitation 7: *"P1–P9 are acceptance criteria for a later slice."*
2. **The world address ruling** (`2026-08-08-world-address-ruling.md`) closed
   docket §4.1, upheld basis-derived addressing, and added **W14–W16**.
3. **The admission ramp** (`2026-08-09-admission-ramp-design.md`) closed F2,
   appended **G9**, narrowed **W3**'s dataset arm, amended **R23** to the §6.2
   dataset basis projection, and ruled the three-state model — curation note,
   `declared`, `held` — with the state **derived, never stored**.

That takes the corpus to 139 rows across eleven frozen tables, every one under
its banked identifier. This cut extends cut 1's practice unchanged: the unit of
selection is the **exact assertion arm**, no selected arm may depend on a
boundary §3 excludes, and the selection **adds no rows and mints no oracles** —
a slice that graded itself is what prospective freezing exists to prevent.

## 2. The boundary decision — three candidates, one designed seam

Cut 1's stop rule, preserved verbatim where it was frozen and inherited here as
the selection criterion:

> **Stop rule.** The slice stops at the **last fully designed seam**.

The guide's open-questions page names the candidates for the next expansion:
run capture, world persistence, or belief. Measured against the tree, only one
of the three has a fully designed seam today.

**Run capture fails the stop rule, at the admission ramp's own residue.** Every
run input is a held dataset (computation §4.7); `G2b` consumes heldness; `R10`
routes a URL-valued input to acquisition; and the ramp's §6.6 rules that an
acquisition **ends by recording the digest of what it retrieved**. Where that
verified observation is recorded — the record `G9` promotes from — is the
ramp's §8 item 2, and it is **undesigned**. A run-capture slice would either
design the holdings record implicitly, which is scope creep past the seam, or
build a run boundary that cannot admit anything, which exercises no R row's
positive arm.

**World persistence's prerequisites are not discharged.** The world-index build
is X1–X12 with **X2 gated on composition-root adoption**. A7's engine half
landed 2026-08-14 and A8 landed 2026-08-17. Composition-root adoption remains;
the `nodes`
contract deltas (ledger artifact 3) block profile implementation and are not on
`nodes` main; and the world layer's availability outcomes presuppose the index
that carries them. A cut there today would be partial selections arranged
around an absent substrate.

**The belief seam is designed end to end, and both post-cut-1 designs name
their rows as acceptance criteria for exactly this slice.** Kernel §4.2.1
designs aggregation with its counterexamples worked; the belief policy supplies
every scalar it is parameterized by and the exact binding that pins them; G3's
closure table enumerates every input the evaluator reads; the admission ramp
supplies the heldness semantics that `G2b` and `P9` consume. The one input
whose *recording* is undesigned — the verified holding — enters the slice the
way cut 1's M11 already ruled availability enters a decode: **as an explicit
argument, never ambient**. Taking an argument is not designing its store, and
§2.1 pins the difference.

So cut 2 is drawn at the belief seam. Nothing here rules what cut 3 is.

### 2.1 The admission ramp's three open questions, as boundary conditions

The ramp closed F2 and left three questions open
(`2026-08-09-admission-ramp-design.md` §8). Each bounds this cut, none is
decided by it, and each stays exactly as open the day the slice lands.

1. **Where verified holdings are recorded** (§8 item 2). The slice derives a
   dataset's state **per query** from byte observations **supplied as
   arguments**, and stores nothing — `G9`'s *derived, never stored* arm is
   selected, and `R5` and `G9` still bound the eventual record from either side
   (not a property of this checkout; not authorable). Unselectable in
   consequence: any arm that needs a **persisted** holdings record — its
   location, its re-check, what makes an entry stale. And the boundary of what
   the slice settles is stated as sharply as what it builds: **an argument's
   type is not a storage design.** The evaluator's availability context says
   what a verified observation *is*; where one is kept, and how a caller comes
   to hold a current set of them, is the undesigned middle the ramp named. The
   §6.5 middle row — 24 of 47 measured records whose state no measurement can
   determine — is exactly as undetermined after this slice as before it.
2. **How long a probe's evidence of retrievability lasts** (§8 item 1). No
   selected arm reads an observation's timestamp — not for the value, not for
   admission. A supplied observation's currency is the **caller's assertion**,
   and the slice performs no probe and no acquisition. An arm that would need a
   validity window cannot be selected until that question is ruled.
3. **The partly-pinned dataset** (§8 item 3). §6.2's all-or-nothing rule is
   implemented **as ruled**. The fixtures will construct partly-pinned datasets
   — the first instances anywhere, since the measured corpus pins all or none —
   and a passing fixture **exercises the ruled boundary without corroborating
   the ruling**: the rule stands on argument, the corpus is silent on its
   strictest edge, and the ramp's §6.2 paragraph remains where a future
   argument starts.

## 3. Step 1 — the boundaries the slice crosses

The slice is: the **derived admission state** — curation note, `declared`,
`held` — computed from a dataset declaration and a supplied set of byte
observations (ramp §6.1, §6.2, `G9`), including the §6.2 dataset basis
projection; the **admission gate for assessments** over constructed records —
role-typed run inputs, held-state inputs, and the kernel §3.3 verification
lifecycle as values; the **belief input closure digest** (`G3`, kernel §5.1);
and **`science.belief.v1` end to end** under an exact `PolicyBinding` (belief
policy §2–§4). Propositions are cut 1's typed claims; their construction and
identity are already built and are consumed here, not rebuilt.

**Two closure members are computed, not supplied, and the distinction is
load-bearing.** The **consulted-contract set** is computed by the domain
boundary's §8 membership walk — the base contract unconditionally, each other
contract only if the derivation actually read something it declares — resolved
against supplied corpus pins; and **independence certification** is computed
from the supplied lineage snapshot. The remaining members — records, facets,
verification values, the retraction enumeration, the producer-snapshot
identity, the policy binding — are supplied. The second reader's first finding
is why this sentence exists: a digest over a *supplied* consulted set cannot
fail when a contract that should have entered it was withheld, and an arm that
cannot fail is malformed under N2. Every D6, M6 and M8 arm below is selected
**on this sentence**.

It crosses exactly four boundaries:

1. **state derivation** — declaration + observations → curation note /
   `declared` / `held`, including the §6.2 dataset basis projection;
2. **admission** — where a constructed assessment meets eligibility: role-typed
   inputs, heldness, verification state;
3. **closure digestion** — where the supplied members, the computed consulted
   set and the computed certification meet `science.identity.v1` and become one
   `belief_input_digest`;
4. **evaluation** — where a closure and an exact binding meet the evaluator and
   yield `Belief | NoBelief(reason) | Refused(reason)`.

It crosses **no** persistence boundary and performs **no** IO beyond its own
fixtures. Stated exclusions, each load-bearing:

- **No holdings store** (§2.1 item 1). Observations are arguments.
- **No runs.** Run and spec identities are opaque supplied values; the
  execution boundary — begin, capture, replay — is not built, so `G2a`'s
  refusals and every R row stay out. A run-shaped **value** with role-typed
  inputs is a fixture, not the boundary.
- **No world index.** The producer-snapshot identity is a required argument
  (kernel §5.1), supplied, never derived; no map is built and no address is
  resolved through one.
- **No rules store and no resolver.** The `PolicyBinding` arrives resolved;
  5b §6's deterministic resolution is not built, which is why P1's resolver
  negative is deferred (§4.2).
- **Verification is consumed, never produced.** Verification nodes are values
  walked through the §3.3 lifecycle; no replay produces one.
- **No retraction authoring.** The retraction enumeration is a supplied closure
  member; the correction lifecycle's operations are not built.
- **No network, no probe, no acquisition** (§2.1 item 2).

## 4. Step 2 — the selection, arm by arm

Cut 1's rule is inherited unchanged: selection is over **exact assertion
arms**; a banked row may be partly selected and partly deferred; no banked row
is split; no selected arm may depend on an excluded boundary. Because cut 1's
own selection stands, each of the 139 rows is in exactly one of **five**
states. **"Selected in full" here means every arm not already exercised under
cut 1** — a deliberate redefinition over cut 1's three states, stated so
limitation 7's ambiguity does not return through it: under cut 1's reading, M6
and M8 are partly-selected rows whose remainder this cut completes.

| state | rows | n |
|---|---|---|
| **selected in full** — every arm not already exercised under cut 1 | G1, G2b, G6, P2–P9, M6, M8 | **13** |
| **selected in part** — the arm split stated below | G2c, G3, G8, G9, S5, S6, P1, D3, D6, D7, N2 | **11** |
| **fully exercised by cut 1** — nothing remains to select | M4, M7, M9, M10, M11, M13 | 6 |
| **part-exercised by cut 1, remainder still deferred** — cut 2 adds nothing | M5 | 1 |
| **fully deferred** — no arm in either cut | §5 | 108 |

### 4.1 Selected in full — 13 rows

Two of the thirteen, **M6** and **M8**, are completions: cut 1 selected most of
their arms and deferred exactly the belief-dependent remainder, which is what
this slice builds. Selecting the remainder makes each row jointly covered by
the two cuts; nothing cut 1 exercised is re-litigated.

| row | what the slice must demonstrate |
|---|---|
| **G1** | a source-assertion with every field maximal moves no belief output byte — the **value** half failable by widening the admission gate to read `asserts` edges, the **digest** half failable only because closure membership is computed (§3); an `assesses` edge from a source-assertion is refused **in the typed constructor** — the closed relation signatures of kernel §4.1, M13-style — since the slice has no other authoring surface to refuse at |
| **G2b** | an assessment whose run names an input that is not `held` — `declared`, or a curation note, under the supplied observations — is refused; so is one whose input carries no digest |
| **G6** | a run value whose only inputs are `reads` — a literature corpus and an ontology — admits no assessment regardless of quantity or QA state |
| **P2–P9** | the belief policy's table minus P1's resolver negative (§4.2) — the fixture-failure refusal that installation cannot repair, the digest membership of the binding, the three distinguishable absences, unspellable unequal weights, no magnitude-bearing read, the computed view, the digest-committed value-inert `inconclusive`, and unholding precedence with recomputation from survivors. **P7's slice form is stated now rather than discovered later**: *no belief record, no current-belief selector* is a static assertion over the built code plus the behavioral arms — no prior-value or prior-digest parameter, byte-identical recomputation, observationally inert cache — and *"the same committed projection"* is here the same **supplied** projection. Its full force is re-asserted at the persistence boundary, where a mint path could exist to refuse |
| **M6** | the arm cut 1 deferred: on an **additive** successor contract, consulted belief digests **move** — now assertable because the digest exists and its consulted set is computed (§3) |
| **M8** | the arms cut 1 deferred: the `belief_input_digest` half of the editorial-bump arm; the negative arm's digest half (activated-but-unconsulted); and the *"absent from the consulted set"* clause, which needed exactly the consulted-set computation §3 names as a crossing |

### 4.2 Selected in part — the arm split, stated exactly

| row | arms **in** cut 2 | arms **deferred**, and on what |
|---|---|---|
| **G2c** | every row of the kernel §3.3 lifecycle table walked over verification values: admission only in `clean-environment, passed` with no active `failed`; a passing sibling does not clear an active failure — with **"active" exercised as *not superseded* only** | the standing-retraction clause that correction-lifecycle §7a added to "active" — the **C group**, beside G8's deferred arm. A walk that exercised the pre-amendment lifecycle while claiming the amended one is exactly the over-count this table exists to prevent |
| **S6** | the kernel §4.2.1 dependency graph, arms (a)–(g): multiplicity 2 on `A={x}, B={x,y}, C={y}`; contestation without selection; addition of a certified-independent-of-nothing assessment; the clique; non-amplification with a moving digest; the double-contest tie; both clamps | arm **(h)** — **recorded, not run**: its own amended text makes it *"a named acceptance condition binding the first successor policy that admits unequal weights"*, not assertable against `science.belief.v1`; what binds v1 today is P5, which is selected. Unblocked by that successor policy — the one deferral in this cut whose trigger is a future artifact rather than a subsystem |
| **G3** | recomputation from the named closure is byte-identical; each closure member mutated in turn moves the digest; the keyed-facet **permutation**; the producing-run deletion — stored ref intact, resolution `null`, the pair kernel §5.1 itself defines as how a deletion reaches the digest; the **second producer** addition; the **narrower-coverage** snapshot | the negative *"move an entity between corpora; assert the digest is unchanged"* — the slice has no corpora and no location input, so the arm **cannot fail** here, and N2 refuses an arm that cannot fail. It waits on **world persistence**, where a move exists to perform |
| **G8** | a failing verification value attached to an admitted assessment invalidates, where invalidation's slice form is stated: the derived admission state flips, and any belief computed thereafter differs — belief is a computed view, so *"forces recomputation"* can mean nothing stronger here; not cleared by recency; not cleared by a passing sibling; the negative — deleting the failing verification value returns the assessment to admitted — whose one in-slice sabotage is **statefulness**, a cross-call memory the N2 table must name, since the banked arm's real target, §3.2's undetectable-history limit in a store, re-arises at persistence | *"cleared by a standing retraction"* (C6) — needs the **correction lifecycle's** retraction records |
| **G9** | declaration does not promote — a dataset whose declaration clears the basis test takes its address under the **§6.2 projection**, reads `declared`, and `G2b` refuses it; **no API accepts an authored `held`**, and the state is derived, never stored; presence does not promote — mismatching bytes leave it `declared` with the mismatch reported as a mismatch; a proper subset does not promote, in both directions over a three-resource declaration; location is not the discriminator — matching bytes outside the repository read `held`, and making them unreachable here while a controlled copy remains held leaves the **digest and admission halves** of R5's answer unchanged; absence in a declared coverage is not `unheld`; the row says nothing about losing heldness | the *"minted as a world entity"* clause — entity standing is **W3's** property, referenceability included, and needs the world boundary W3 waits on; the **replay-eligibility third** of R5's answer — the run boundary; and the **independence sabotage** — *"assert G9 fails while G2b, R5 and R10 all pass"* — which requires all three named rows to exist as runnable checks, and R10 and R5's replay arm sit at the run boundary. Running it against G2b alone would be a weaker assertion wearing the banked arm's name |
| **S5** | independence certification **computed from the supplied snapshot**: an unresolved basis entry yields `lineage-incomplete` and `not-certified`, the `belief_input_digest` changes, and belief cannot rise; the negative's certification half — with the **divergent producer** absent from the snapshot, the certificate is restored and belief **can** rise | the walk that *produces* the snapshot from a store — substrate §5's procedure over the world resolver, which is **S1a's and the write API's** territory; and the negative's *"indistinguishable from one where that run never existed"* clause, a **store** property (nothing surviving holds a reference) that over supplied snapshots collapses to purity of the certifier — a different claim than the row makes |
| **P1** | the evaluator accepts only an exact `PolicyBinding`: supply nothing → refusal; supply the rule identity alone → refusal | the negative's **resolver half** — *"assert 5b §6's deterministic resolution … is unaffected"* — observes a resolver, and the slice builds **no rules store and no resolution** (§3). Adding one to save the arm would be the enlargement this cut's whole discipline refuses |
| **D3** | one further arm joins cut 1's selection: a dataset identified whose bytes are not held here → **`not-available`**, never reported as `not-present` — the holding half of the outcome pair, now derivable from the admission state. With it, one **named clause of the five-way arm**: `not-available` is never reported as `not-member` — selectable because `not-member` production landed in cut 1, and attributed to the five-way arm rather than folded into the not-available arm, which does not contain it | `not-present` (world address indexed, corpus absent) and the remainder of the five-way non-collapsing assertion, which requires producing it — still on the **world index** |
| **D6** | the claim-schema arm — bump the contract declaring `affects`, no facet touched, digest moves — running on **cut 1's claim-schema compilation**, not D4's; activate an unrelated domain and bump it, digest unchanged, where **"activated" is a supplied pin set** — the arm certifies the consulted-membership rule, not activation, whose carrier (the corpus manifest) is deferred with D5; the base-contract arm at the eligibility hinge; the unconditional arm — a closure reading no base-profile facet still moves when a kernel kind is reinterpreted; the negative, instantiated over the base contract, a kernel kind and a relation signature **only** | the domain-**facet** arm — *"derive belief over an assessment reading `biology/gene-axis`"* — needs a derivation that reads a namespaced facet, and no derivation in this slice reads one; it waits on the **compiled registry** (D4's subsystem), and the negative's domain-facet instantiation travels with it |
| **D7** | the two closure-agreement refusals: a closure spanning corpora pinning different identities for one namespace is **refused**, never merged, never resolved by recency; and different `science_contract`s refuse even when no base-profile facet is read — corpora existing in-slice as supplied node→corpus attributions plus per-corpus pins, so what is certified is **§8.1's agreement rule and not its resolution rule**, whose *"manifest of the corpus holding the node"* needs the index | the W5-preservation arm (a producers-map move) and both **move refusals** — the **write boundary** and the index |
| **N2** | the same doctrine cut 1 applied to its own arms, extended over **cut 2's selected arms**: every arm declared as data with its row, assertion, source mutation and exact named checks; the harness audits each for `vacuous`, `stale`, **`mixed`**, `uncollected` and the class-node collapse — mixed restored to the list by the second reading, being the defect three real cut-1 arms actually had — and reports malformed contract content rather than passing it | the doctrine over the rows **neither cut selects**, exactly as cut 1 left it |

### 4.3 Standing from cut 1

**M4, M7, M9, M10, M11, M13** were fully selected by cut 1 and are fully
exercised; nothing remains. **M5**'s cut-1 arms stand, and its remainder — the
founding case end to end: mint, assess, edit, a new identity with the prior
assessment still bound and a `supersedes` link — stays deferred. Cut 1 recorded
its blocker as *"persistence + belief"*; this slice supplies belief and **not**
persistence, and half a blocker unblocks nothing. Recording that M5 gains no
arm here is the point of the five-state accounting: a reader of cut 2 alone
would otherwise read "belief built" as M5 reachable.

## 5. Step 3 — fully deferred rows, grouped by unblocking subsystem

108 of 139 rows have no arm in either cut. Grouping is by the subsystem that
unblocks them, re-read against this slice's boundary; where the reading
disagrees with cut 1's §5.3 grouping, the row sits here under the corrected
group and the disagreement is stated rather than edited into the frozen text.
The same correction runs the other way: cut 1 grouped **S5 and S6** under *"the
write API"*, and every arm of S6(a)–(g) and most of S5's are assertions about
certification and aggregation — this slice's interior — which is why they
appear in §4 and not here.

| group | rows | n | unblocked by |
|---|---|---|---|
| runs & the execution boundary | R1–R23, **G2a**, **G4** | 25 | the run boundary. G2a and G4 sat in cut 1's *"kernel & belief"* group; both are assertions about what the boundary will begin and what a recorded replay failure forces, and no belief evaluator reaches either. R5 and R10's *consequences* are asserted inside P9's and G9's selected arms — and implication is not selection |
| world addressing | W1–W16, W5a, W8a, W8b | 19 | the world index. The §6.2 projection **function** is built and exercised through G9's arms, but every W row's check sits at the write boundary or the index, so none is selected — the same line cut 1 drew between M8's clause and D4's rows |
| substrate write & traversal | S1, S1a, S2, S3, S4, S7, S8 | 7 | the write API and the world layer's stored-corpus traversal — where S5's deferred walk half also waits |
| kernel, at other boundaries | **G5**, **G7** | 2 | G5 — the authoring surface and kind registry, where *"no such kind exists"* is a checkable claim; G7 — the mint path. Both sat in cut 1's kernel-and-belief group; neither unblocks on the evaluator |
| packaging | X1–X12 | 12 | world export; X2 additionally gated on composition-root adoption |
| tamper log | L1–L13 | 13 | composition-root adoption |
| correction lifecycle | C1–C10 | 10 | retraction records — where G8's deferred arm and G2c's retraction-clause of "active" also wait |
| normative contract — contract cut | N1, N3 | 2 | the first contract cut |
| normative contract — certification | N4–N9 | 6 | instrument certification and parity machinery |
| normative contract — legacy adoption | N10 | 1 | the adoption gate |
| domain boundary | D1, D2, D4, D5, D8, D9, D10 | 7 | facets, manifests, and the registry compile |
| formal model | M1, M2, M3, M12 | 4 | resolver, runs, retraction graphs, and the extraction path |

## 6. Accounting, freeze, and amendment discipline

**13 selected in full + 11 in part + 6 fully exercised by cut 1 + 1
part-exercised with its remainder deferred + 108 fully deferred = 139.** Every
banked row is classified into exactly one state. As in cut 1, **no count of
arms is offered as a denominator**: the banked rows do not enumerate their arms
formally, and the splits in §4.2 are this document's reading of each row's test
cell.

> **Freeze.** This cut is frozen on the date in the status header, before any
> cut-2 implementation exists. **Results are recorded separately**, never by
> editing the selection. If the cut must change, the original selection is
> **preserved verbatim** alongside the amendment, with the reason stated.

The slice's acceptance criteria are the selected arms as frozen — it adds no
guarantee table of its own.

## 7. The second reader

Cut 1's limitation 8 found that every selection error ran toward a larger cut
and was caught by review rather than by the method, and asked for *"a second
reader on cut 2."* That reading happened **before this freeze**: a reader with
no stake in the draft was given the banked row texts and §3's boundary
declaration — not this document's rationale — and instructed to attack the
selection in the direction cut 1's errors ran, moving arms **out**.

It returned fourteen findings, and every arm a finding moved, it moved out.
The load-bearing ones, recorded because the pattern is the finding:

1. **The draft's boundary said the closure digest ran "over explicitly
   supplied members," which would have made every digest-membership arm
   unfailable** — D6 entire, M6's and M8's completions, and G1's digest half
   all certify a *membership rule*, and a digest over a supplied set passes
   whatever the caller withholds. The boundary now names the consulted-set
   computation and independence certification as **computed** crossings (§3),
   which is what those arms are selected on.
2. **S5 was over-selected as whole.** Its deletion arm *produces* a changed
   snapshot by walking a store, and its negative's indistinguishability clause
   is a store property; both moved out, and S5 moved to partly selected.
3. **P1's resolver negative observes a resolver the slice does not build.**
   Moved out; P1 moved to partly selected rather than quietly narrowed.
4. **Two of G9's clauses leaned on excluded boundaries** — *minted as a world
   entity* is W3's property, and one third of R5's answer is replay
   eligibility. Both weakened explicitly in §4.2, and the independence-sabotage
   deferral's rationale corrected: it rests on the arm's three-check form, not
   on R5 lacking executable checks, which was half false as drafted.
5. **The draft's N2 audit list had dropped `mixed`** — the defect three real
   cut-1 arms actually had. Restored.

The remaining findings pinned slice-forms that are now stated at their sites:
G1's refusal living in the typed constructor, G2c's supersession-only "active",
G8's invalidation and statefulness sabotage, P7's static form, D3's clause
re-attribution to the five-way arm, D6's activation-as-pin-set, and D7
certifying agreement but not resolution. The accounting was verified correct
as drafted and again after the recategorizations.

**A third reading — the review before merge — moved two more rows the same
way.** G2c and S6 were classified as selected in full while each carried an
unexercised aspect: the standing-retraction clause of "active", and arm (h).
Both moved to partly selected, and §10's phrasing of the partly-pinned question
was corrected from *standing* — which the ramp ruled — to the empirical
corroboration that is what actually remains open, a conflation the guide had
carried too. Three readings, one direction: every classification error found in
this document ran toward overstating coverage.

**The reader is not an independent human.** It is a separately-instructed
reading with the draft's rationale withheld, which removes anchoring on this
document's arguments and removes nothing else. The corpus's own rule is that
reliability is measured, never assumed by category; this section states what
the reading was so a later reader can weigh it, and limitation 4 carries the
residue.

## 8. What this changes elsewhere

Applied in the same change as this document. Nothing amends a banked row;
every entry is navigational.

| site | change |
|---|---|
| README | design count **eighteen → nineteen**; the table gains this document; the status section stops describing cut 1's edge as the built system's only frozen selection |
| guide `contracts-and-adoption.md` | the cut-1 paragraph gains cut 2: what it selects, and that the ten rows banked after cut 1 now have an owner; this document joins `sources` |
| guide `open-questions.md` | the *next conformance expansion* entry is replaced: cut 2 is drawn, and what remains open is what §5 defers — run capture, world persistence, and the subsystems behind them |

## 9. Limitations

1. **The arm splits are a reading, not a property of the rows** — cut 1's
   limitation 7, inherited whole. A different reader could draw a boundary one
   clause earlier and change which half of G3 or D6 is selectable.
2. **This cut is more than twice cut 1's size, and cut 1's errors all ran
   toward larger cuts.** The size has a cause — an entire table and most of a
   second had their unblocking event occur at once — but a cause is not a
   defense. The second reading ran against the known failure direction and
   found the draft had over-selected in exactly that direction, three times
   (§7); what it cannot establish is that it found the last instance — and it
   had not: §7's third reading found two more.
3. **The F11 pattern recurred, and the trade is now live.** Cut 1 worked around
   five compound rows by selecting arms and recorded that splitting them —
   paying a successor contract identity — *"is the cheaper fix only if the
   pattern recurs at cut 2."* It recurred: eleven rows are arm-split here, two
   of them (G3, G9) among the corpus's largest cells. The split-versus-carry
   decision is docketed by open question 2 below, not decided by this cut.
4. **The second reading is one model-instructed pass, not adjudication.** It
   was run adversarially and blind to the rationale, and it remains a single
   reading whose own errors would land in the same direction as the author's.
5. **Fixtures at the partly-pinned edge exercise a ruling the corpus cannot
   corroborate** (§2.1 item 3). A green suite there is evidence the boundary is
   implemented as ruled, and no evidence the ruling is right.
6. **Several banked arms are exercised here in stated weaker slice-forms** —
   G8's invalidation, P7's static half, S5's certification half — with their
   full force explicitly re-owed at the persistence boundary. A reader tallying
   "arms exercised" without §4's caveats would over-count what this slice
   demonstrates.

## 10. Open questions

1. **The admission ramp's three questions stand unchanged** — where verified
   holdings are recorded, how long probe evidence lasts, and the partly-pinned
   rule's **empirical corroboration**: the standing itself is ruled — a
   curation note, on argument alone — and what remains open is evidence at the
   edge the ruling is strictest about. §2.1 states what each makes
   unselectable; this cut
   decides none of them, and the first is now the corpus's most consequential
   open design: it blocks the run boundary (§2), the G9 independence arm
   (§4.2), and the ramp's own 24 undetermined records.
2. **Split or carry the compound rows.** Eleven arm-splits in this cut, five in
   cut 1. A split is an amendment minting a successor contract identity (F11);
   carrying the interpretive boundary is free until the next cut re-reads it
   differently. One of the two costs is paid once and the other on every cut.
3. **What cut 3 is.** §2 argues run capture and world persistence each fail a
   prerequisite today; it does not rank them. The first is unblocked by
   designing the holdings record; the second by composition-root adoption and
   the `nodes` deltas. A7's engine half landed 2026-08-14 and A8 landed
   2026-08-17; the stop-rule outcome remains unchanged. Whichever prerequisite
   set lands first likely names the cut.

> **Amended 2026-09-08 (biology pack design §5.3a, §10).** The consulted walk
> now reaches every claim's sort and dimension contracts and refuses a
> consulted namespace whose pin disagrees with the profile. Cut 2's D6 arm
> "consulting every pinned namespace" is re-pointed at the landed lines of
> `consulted.py` in `n2_arms_cut2.py` (fix the arm, never the source); its two
> checks and `test_closure.py`'s two D6 checks keep their names and their
> assertions and bump a compiled profile rather than a pin string. Commit:
> the one that lands this amendment.
>
> The same amendment re-points G1's closed-signature sabotage from the former
> final `binding` parameter to the new final `observed_facets` parameter. The
> sabotage and check are unchanged in meaning; only their live source anchor
> moved. Commit: the one that lands this amendment.
