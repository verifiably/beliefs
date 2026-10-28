# The normative contract, conformance oracles, and instrument certification — design (sub-problem 5b)

**Status:** Banked 2026-08-03. Second of the two sub-problem 5
clusters (adoption ledger §2), taken after 5a and the world-index packaging design
so the operation set and the rules store both exist before the document that
describes them freezes. The banking amendment set below was applied across
kernel, world, comp, 5a, and packaging in the banking commit.
**Amended 2026-08-05** by the formal model and claim calculus design: §4's exact
oracle inventory gains **M1–M13**.
**Inherits:** the ledger §2 constraints (tables frozen under current ids; `nodes`'
STANDARD transfers as form, not force); comp §3.1b (the rule-binding route, queued
to be decided once, here); comp limitation 4 and §11.4 (equivalence rules and
falsifiers are authored and uncertified); comp §7.3/§11.7 (code-lineage
independence); comp §7.3's open scope-derivation-rule versioning; packaging §7
(the held-rules store); 5a (retraction — this design adds an eligible target).
**Constraints:** G/S/W/R/C/X stay frozen — this design adds its own table (N) and,
where a banked statement must change, amends in place under the same identifier at
banking, never renumbering. The banking amendment set (applied in the banking
commit): comp's "no certification
kind" statements and every exhaustive kind accounting the tenth kind touches —
the kernel's kind inventory table, mapping totals, and count statements, the
kind-count phrasings in world and comp, world §3's in-world inventory, and a new
world §4.2 basis row for `instrument-certification` (§7.2); 5a's eligible-target
set, C10, and §9's relation-name question (§7.2, §7.7); packaging §7's
rules-store wording (§6); the exact-binding members — comp §4.2's recipe
inventory, §4.2a's projection rule, and §7.3c's evaluator-resolution sentence
(the binding recipe member, §6), R18, world §4.2's derived-evidence wording,
comp §4.4b's boundary-policy content (it names the scope-derivation rule,
§6), and the packaging receipts' rule-identity members (§6); and the
certification-enumeration receipt — X10's and X12's in-place amendments, X9's
third-receipt extension, packaging §5/§7's receipt inventories, and the
semantic certification-enumeration projection in world §5/W8a and packaging
§5.2 (§7.6), comp §7.3's `not-certified` derivation row (its trigger becomes
the per-shape required subject set, §7.6), and comp §7.3c's constructor
signature and audit consequence with R19's argument enumeration (the
required cut and epoch selection arguments; audit emits findings and mints
nothing, the superseding act being explicit — §7.6).

## 1. Why

Three debts, one document. First: the redesign now has six banked designs, six
guarantee tables, and no single answer to "what version is the system" — every
normative statement lives inside a design doc that also carries its rationale,
review history, and amendments, and drift between six part-authorities is
undetectable because none of them is *the* authority. Second: the estimator
doctrine — a check must be able to fail — is enforced everywhere except on the
instruments that do the checking. An equivalence rule that cannot fail makes every
verification over it a check that cannot fail; a falsifier that cannot fire makes
`falsification` a decoration; both are required fields today and certified nowhere
(comp limitation 4). Third: three queued rulings have no home — the rule-binding
route (comp §3.1b: held implementation *or* registry-plus-fixtures, "the same
decision for interpretation and equivalence rules, so it should be made once"),
the scope-derivation rule's versioning (comp §7.3), and code-lineage
independence's contract vocabulary (comp §11.7).

## 2. Framing rulings

1. **The contract is a distilled document, and it becomes the authority.** One
   versioned normative document — the STANDARD form, adopted for science's own
   reason (the estimator doctrine, not cross-language parity). It states kinds,
   identities, operations, boundary outcomes, rules, and the oracle tables,
   without rationale; each section cites its source design. Once the first
   contract version is cut, the design documents stop being normative and remain
   as rationale and history. **Drift between a design and the contract is a
   defect, resolved in the contract's favor.**
2. **The legacy checks get a disposition principle, not a disposition table.**
   The current validation suite (`science_tool/validate/checks`, 63 modules) is
   the old system's check authority. This design rules the principle (§8); the
   per-module disposition belongs to adoption and implementation plans.
3. **Certification degrades scope; it never blocks and it never merely
   decorates.** The banked pattern (code-lineage, exclusion certification)
   holds: an uncertified instrument refuses nothing at authoring or execution,
   and everything derived through it carries a capped, `not-certified` scope
   that admission rules read. Certification upgrades future derivations;
   absence is honest and visible.

## 3. The contract document

**Every cut is retained, immutable and content-addressed.** A contract cut is an
immutable artifact held at its content address; `docs/CONTRACT.md` in the science
repository is only the **operational rendering of the current cut**, never the
retained artifact, and publishing a new cut leaves every predecessor untouched at
its address. Contract node-hood stays open (§11); held addressability does not.

The **contract identity** is the `science.identity.v1` digest over the cut's
**exact canonical normative bytes**. No structured normative projection is
defined yet, so a byte-changing reorganization mints a successor even when
semantics are unchanged — the same deliberate false positive world §5 accepts
for relation document order, and the same trade: a closed, reproducible subject
is worth more than tolerance of cosmetic edits. A human-readable version label
is an alias for the identity, never the identity. Each cut names its
predecessor's identity, so succession is a recorded chain, not an inference
from labels. **The cut also names the executable oracle-case identities it
governs** (§5), putting the suite's code inside the identity's reach rather
than beside it.

Structure, fixed here; prose deferred to the first cut (an implementation act):

1. **Kinds and identities** — the kernel kind inventory, per-kind address bases,
   content and state identities, `science.identity.v1`.
2. **Operations and boundaries** — write boundary, import, audit, diagnostic
   query; `consolidate`, coreference attestation, supersession, retraction
   *(this read "merge" until 2026-08-08, when structural merge retired and split
   into the first two — `2026-08-08-world-address-ruling.md` §5)*; the outcome vocabularies
   (`validated | refuted | unresolvable | malformed | retracted`, admission
   states, snapshot states).
3. **Rules and instruments** — rule identity and binding (§6), the instrument
   inventory, certification (§7).
4. **The conformance suite** — the oracle tables (§5).
5. **Change policy** — what mints what (§4).

## 4. Versioning — what mints what

Four change classes, four different mints, none interchangeable:

| change | mints | retained |
|---|---|---|
| any change to a cut's canonical normative bytes — semantic or cosmetic (§3) | **successor contract identity** | every oracle human id (G1, R4, …); the predecessor cut, immutable at its address |
| rule behaviour change | **new rule identity** (`v2` disjoint from `v1`, comp §3.1b) | the rule's symbol lineage; a successor cut references the new identity |
| implementation change that conforms to the same fixtures | **new implementation content identity** only | the rule identity — the rule did not change |
| byte-identical republication of the operational rendering | nothing | the cut and its identity |

**Oracles freeze by `(contract identity, oracle id)`.** The human ids — G1,
G2a–G2c, G3–G8; S1–S8 with S1a; **W1–W16** with W5a and W8a–W8b (W14–W16 added
2026-08-08 by the world address ruling, §9 there); R1–R23; C1–C10;
X1–X12; **N1–N10** (this document's own table, §9); **L1–L13** (tamper-evident
log, banked 2026-08-03, omitted from this inventory at its banking and added
2026-08-04); **D1–D10** (domain extension boundary, banked 2026-08-04);
**M1–M13** (formal model and claim calculus, banked 2026-08-05); **P1–P9**
(belief policy, banked 2026-08-05); **H1–H4** (added 2026-08-10, the
verified-holdings record design §6 — the H table joins the suite on the same
rule that added N, L and D); **T1–T8** (added 2026-08-11, the act-report
design §5 — the T table joins on the same rule): the exact current inventory,
with no base G2 — are permanent names.

**P, not B.** The formal model uses `B` for the belief reading throughout M₀, so
an oracle table under that letter would recreate exactly the overloading that
document was written to remove. **P1–P9** covers the exact policy binding and its
refusal boundaries (P1, P2), the binding as a digest member (P3), the three
absence states and their distinguishability (P4), unequal weights being
unspellable under `science.belief.v1` (P5), v1 reading no magnitude-bearing facet
field (P6), belief as a computed view with an observationally inert cache (P7),
an `inconclusive` assessment being value-inert but digest-committed (P8), and the
unholding precedence that keeps R5's recomputation from being overruled by a
refusal (P9).

**M enters at banking, by that design's own standing obligation.** Both L and N
reached this inventory *late* — L was omitted at its banking and added a day
later, N only when D's banking noticed that §5 requires every oracle table in the
suite. The formal model recorded the obligation in its own header before its
first section was drafted, precisely so a third table would not repeat the
pattern. **M1–M13** covers claim typing and identity (M4, M5, M8, M9, M11, M13),
the vocabulary lifecycle and its single authored source (M6, M7), cross-language
projection parity (M10), untypeable spans (M12), `standing`'s termination over an
acyclic retraction graph (M3), run-input binding (M2), and declared-closure
containment at the instrumented resolver (M1, which states its own boundary as a
declared limit rather than claiming every undeclared read is detected).

**N is in the suite, and its self-reference is not a cycle.** §5 makes every
oracle table part of the conformance suite, §9 states N as a guarantee table,
and N2 guards the doctrine reflexively — so omitting N would make "exact current
inventory" false by this document's own rules. No identity cycle arises: a cut
contains N's **normative rows and executable case identities**, never the digest
that cut produces.
Extending a table appends; amending a row's meaning mints a successor contract
identity under the retained id, exactly as 5a amended G8 and the packaging design
amended W8a and W13; renumbering is unspellable. The estimator doctrine enters the
contract as **law, not preamble**: every oracle row must state a mutation that
makes it fail, and a row without one is malformed contract content.

**The scope-derivation rule versions as a rule** — its own fixture-bound rule
identity, resolved from the rules store like every other rule. Not versioned with
the belief policy (it derives scope, not belief) and not with
`science.identity.v1` (that versions canonicalization, not behaviour). This
closes comp §7.3's open question with the least machinery: the identity already
participates in every verification address; it now binds the way every rule
binds.

## 5. The conformance suite

The oracle tables **are** the conformance suite. Each row is an executable
obligation — the mutation test implemented, runnable, and failing when its
guarded invariant is sabotaged. An installation **conforms to contract identity
K** iff the suite at K passes against the installation's held implementations.
There is one implementation today, so conformance is presently a self-check —
the form is `nodes`' three-tier model reduced to one tier, kept because the
suite's reason here is not parity but the doctrine: the suite is where "this
system does what its contract says" becomes falsifiable. The suite is versioned
with the contract (a suite row is contract content); its executable form lives
with the implementation, and **each cut names its executable oracle-case
identities** (§3): a case whose content does not match the listed identity is
not the suite, so "the suite at K" is a determined set of bytes, not whatever
tests are checked out today.

## 6. Rule binding — one decision, both halves

Comp §3.1b left two routes open — a held content-addressed implementation, or a
normative registry entry with conformance fixtures. Ruled: **they are halves of
one binding, not alternatives.**

> A rule identity is `(symbol, fixture-set identity)` — the fixture set is the
> **normative half**: declared inputs and required outputs that define what the
> symbol *means*. A held implementation in the rules store (packaging §7) is the
> **operational half**: what runs here. An implementation that fails the fixtures
> **is not that rule**, whatever it is named; an implementation that passes is
> one of possibly several conforming implementations, each with its own content
> identity, none of them changing the rule identity.

*Amended 2026-10-28 (overlapping-publications design §4.5, cut 48):* a rule whose input is versioned carries the input version in its identity, `(symbol, fixture-set identity, input version)`; a rule with no declared version keeps the pair above, so no held identity moves.

The contract *is* the registry: its rule sections name each rule identity and its
fixture-set identity normatively. "Registry entry with fixtures" therefore stops
being an unbuilt artifact nobody maintains — it is contract content — and "held
implementation" stops being an alternative to it — it is rules-store membership,
proven against the contract's fixtures. This covers interpretation rules,
equivalence rules, and the scope-derivation rule in one decision, as comp asked.

**The exact binding enters every derivation.** Several conforming
implementations may be held at once, and finite fixtures cannot make them agree
beyond the fixtures — so *which one ran* is a fact every derived record must
carry, or the system reopens comp §3.1's installation-dependent-facet defect one
level down. Binding selection is **explicit**, and
`(rule identity, implementation content identity)` enters every derived result
and receipt that executed the rule: comparison reports, the epoch's
producer-snapshot, retraction-map, and certification-enumeration receipts
(§7.6), and assessment derivation evidence. A receipt validates
against **the implementation it names** — never "whatever implementation of this
rule is held today" — so installing a conforming B leaves every A-receipt
validating for as long as A stays held (N3).

**The binding freezes in the run's recipe, and the assessment basis stays the
triple.** A spec names rule identities only, so with two conforming
implementations held, a selection made at derivation time is made by a caller
who can already read what the rule will judge — the result manifest exists
before assessment derivation, both runs' artifacts before verification
construction — and observing-then-choosing is the evaluator-shopping route
comp §7.2/R8 closed for the rule identity itself. The same closure closes it
here: **binding resolution is a recipe member, and the selection source is the
freeze act.** Each rule identity has a named source — the spec names the
interpretation and equivalence rules (`dataset-content-equality/v1` for
`dataset-production` shape); the boundary policy (comp §4.4b) names the
scope-derivation rule. At recipe freeze each identity resolves to **exactly
one** held implementation content identity, or the freeze refuses: with one
conforming implementation held, resolution is determined; with several, the
freeze act **must name the implementation content identity explicitly** — a
pre-execution input, so nothing observable exists to shop — and a freeze that
names none while several are held, or names one that is un-held or fails the
fixtures, refuses. Ambiguity is never resolved by an installation default or
store order. The resolved pairs freeze into the recipe, which is complete
before execution (comp §4.2): the selection exists before any result it will
ever judge. Downstream assessment and verification constructors — and only
they — lack selection arguments: they **read** the binding from the original
run's frozen recipe — comp §7.3c's evaluator-not-an-argument rule, extended
to the implementation half — so post-observation selection is unspellable,
not refused. A replay reconstructs from the recipe and replays under the same
binding; a binding no longer held is `unresolvable`, never a silent rebind.

Freezing there is also what lets the assessment basis **remain**
`(spec, run, proposition)`: the recipe is inside the run address (comp
§4.2/R2), so the binding reaches the assessment identity through `run` and
the belief digest through kernel §5.1's keyed facets — "anything frozen into
a recipe is in G3's reach" already carries it. Two conforming implementations
that disagree beyond the fixtures are two recipes, two run identities, and
two assessments at two addresses — comp §3.1's worst-form failure closed
without touching comp §5.1's one-node-per-derivation argument, which holds
unchanged. At banking this amends comp §4.2's recipe inventory (the binding
member), §4.2a's projection rule (the boundary resolves bindings at freeze;
no caller-supplied path), §7.3c's evaluator-resolution sentence (identity
from the spec, implementation from the recipe), world §4.2's derived-evidence
wording and R18 (the comparison report states the binding it executed), and
the packaging receipts' rule-identity members to carry the pair.
Packaging §7's wording ("implementations content-addressed, each with the
fixtures that bind its identity") is clarified at banking: fixtures are
contract-normative content; the store holds implementations *and* fixture
content, and binding runs through the contract's fixture-set identity.

## 7. Instrument certification

### 7.1 The form — certification by recomputable witness over a specific binding

> An **instrument certification** is a recorded, recomputable demonstration that
> a specific binding — rule identity **plus** implementation content identity —
> both *conforms* and *can fire*. Its content: the **contract identity it
> certifies under**; the **discriminated subject** — `equivalence`,
> `interpretation`, or `scope-derivation` over a rule binding, or
> `falsification` over `(spec identity, interpretation binding)` (§7.4) — with
> the rule identity, which **contains** the fixture-set identity (§6, one
> spelling only), and the implementation content identity; and the witness
> evaluations. Never an
> attestation. The subject is discriminant-exact at consumption (§7.6): a
> certification satisfies only the requirement its arm names.

**Certification is exact-K.** A certification speaks only for the contract cut
it names: a consumer deriving under any other cut finds no standing
certification, however close the cuts are. If a successor cut strengthens
witness coverage without touching the rule or its fixtures, nothing old silently
qualifies — recertification under the new cut is required, and its record is a
different record. Global recertification on a contract bump is the accepted
initial cost; a narrower certification-policy identity splits out only if that
cost becomes measured pain.

**One fixture execution, two assertions.** Certification reuses the binding run
rather than minting a second witness infrastructure:

- **binding** — every normative fixture produced its required output (the
  implementation is the rule);
- **certification** — the required *outcomes were actually reached*: the
  fixtures include witnesses on which the instrument is **required to fire**,
  and it did.

**The certification binds rule + implementation.** A witness run against
implementation A certifies nothing about implementation B sharing the symbol:
scope derivation consulting a binding B with no standing certification finds it
uncertified, whatever A's record says (N5).

**Recorded means recomputed.** The certification constructor accepts bindings
and witness *refs* — never caller-supplied outcomes; no such parameter exists
(N4). Import and audit re-execute the witness evaluations, with the standard
outcome pattern: `validated` when re-execution reproduces the recorded
evaluations, `refuted` when it does not, `unresolvable` when a witness, fixture,
or implementation is no longer held, `malformed` for structural defects, and
`retracted` under a standing 5a retraction. **Recomputation detects
disagreement, not authorship.** A certification whose typed-in outcomes disagree
with re-execution is refuted; one whose typed-in outcomes happen to agree is
indistinguishable from a genuine record and validates at audit — at which point
the audit's own re-execution has supplied the demonstration, so what the forgery
misrepresented is provenance, never the demonstrated fact. The raw-write route
is R19's bound, unchanged; the API route stays closed because the constructor
has no outcome parameter to lie through (N4 pins all three).

### 7.2 The carrier — a tenth kernel kind

`instrument-certification` is a new immutable kernel kind, a **world kind** with
a content-derived address over the content above — no event token, following the
`verification` precedent: the record is a derived demonstration, so identical
content is identical identity, re-deriving an unchanged certification is
idempotent, and a retracted certification re-minted byte-identical is *still
retracted* (the standing retraction targets the address), which is exactly
right — nothing changed, so nothing is re-established; a wrongful retraction is
answered by counter-retraction, not by re-minting. The contract identity in the
basis completes the picture: under one cut, a byte-identical re-mint stays
retracted; under a successor cut the certification is a **different record**,
so recertification-after-amendment is a new act, never a toggle.

Two banked statements amend narrowly at banking: comp §7.3b's "no
`certification` kind exists to point at" and the inline-certification ruling's
"the kernel's kinds … include no certification" become "no *code-lineage* certification kind exists —
code-lineage remains an inline authored claim (§7.5); executable-instrument
certification is the `instrument-certification` kind." 5a's eligible-target set
(§4) and C10 gain the new kind in the `node` arm: a certification is a readable
input (scope derivation reads its standing), so it is retraction-eligible by
5a's own test.

### 7.3 Witness coverage — per instrument

| instrument | certification requires | and as conformance (error path) |
|---|---|---|
| **equivalence rule** | one witness pair it judges `passed`, one it judges `failed` — both directions, so a constant-equal rule and a constant-unequal rule both fail certification | `inconclusive` on unreadable artifacts stays a fixture obligation, not a witness |
| **interpretation rule** | witness manifests reaching each declared outcome: `supported`, `refuted`, `inconclusive` | evaluator failure produces **no assessment** (comp §3.1's asymmetry) — a fixture obligation |
| **falsification** (spec-scoped, §7.4) | the spec-declared witness manifest reaching `refuted` under the certification's named interpretation binding | — |
| **scope-derivation rule** | witnesses exercising **every derivation row**: `same-environment`, `clean-environment`, `independent-implementation`, and `not-certified`, including the fail-closed degradations | — |

The independence witness deserves its own sentence: it proves the derivation
**handles an authored lineage claim correctly** — certified claim present →
`independent-implementation`; absent or retracted → degraded — and proves
nothing about whether any such claim is *true* (that is §7.5's bound, unchanged).

### 7.4 Falsification certification is spec-specific, and mints no second evaluator

`falsification` is normative spec content; only `interpretation_rule` has an
executable signature (comp §3.1, §3.1b). Certifying that a spec's falsifier
could fire therefore runs through the machinery that already exists: the
falsification declaration names **at least one held witness manifest**, and the
certification demonstrates that the spec's interpretation rule — under the
implementation binding the certification names (§7.1) — produces **`refuted`**
from it. The certification record carries the spec
identity (§7.1); no falsification evaluator, signature, or second execution
path is created (N9). The two spec fields stay semantically distinct — the
falsifier says *what would refute*; the certification demonstrates the spec's
instrument *can say so*.

### 7.5 Code-lineage independence stays authored

A code-lineage claim is about how code came to be written — not an executable
that fires — so there is nothing to demonstrate and the witness form does not
apply. It remains an inline authored claim with grounds, **embedded in the
comparison report per comp §7.3b — deliberately not independently addressable,
so a 5a retraction cannot target it directly**. Withdrawal keeps the form comp
promised: retract or supersede the **verification that embeds the false
claim**, with the claim as ground; the embedded evidence falls with its
carrier. This design gives it contract vocabulary and otherwise changes
nothing.

### 7.6 Degradation and retraction semantics

**Standing is discovered from explicit inputs, never an implicit current view.**
A consumer derives under an **explicitly selected contract identity and an
explicitly selected epoch** — the epoch is a required argument exactly as the
snapshot identity is for belief (packaging §5.3), and a derivation naming
neither is unspellable. Standing is discovered by **enumerating the selected
epoch** for `instrument-certification` records matching a required subject
under that cut — no fifth index map is needed; the enumeration runs over the
epoch's address map by kind — joined through the retraction map for standing.
Matching a subject **reads the certification's content**, so a ref whose
covered corpus is absent resolves `not-present` (packaging §5.4) and cannot
be inspected: it stays in the evidence as a **known unresolved ref**,
satisfies no required subject — fail-closed, the scope caps — and keeps the
report distinct from one where no certification existed (N7). The
consumer records the discovery evidence in its own derived record (the
comparison report, per R18's one-digest-over-evidence rule) as a **semantic
enumeration projection built around a receipt-covered core**. The core names
**one** identity the epoch's receipt also names: the
**certification-inventory projection** — the epoch-wide by-kind enumeration
as sorted certification refs under the coverage declaration, **location-free**
(no per-ref corpus assignment) and **resolution-free** (resolution is
consumption-time state and lives only in the surrounding evidence) — exactly
the certification-enumeration receipt's subject, created at build time before
any verification or subject set exists. **The retraction axis deliberately
stays out of the core.** The report digests only the per-input recursive
closures below — 5a's specificity rule: a retraction moves only the
computations whose closure contains its target, so an unrelated retraction
elsewhere in coverage must not move the report (N8) — while the epoch-wide
retraction projection remains the retraction-map receipt's subject, reached
at audit through the epoch and never digested by the report. Around the core
sits the verification-specific evidence: the selected cut, the coverage
declaration (the stable `corpus_id`s), and the refs matching required
subjects, each with its **consumption-time resolution** (`not-present`
above), its **recursive retraction closure** — the found retraction refs and
their resolutions, and recursively the retractions targeting *those*,
sibling-aware and well-founded exactly as 5a's standing recursion computes it
(5a §6, C5), with the coverage each level's join ran under — and the standing
that closure yields. Report and receipt never claim one identity for two
different projections: the receipt covers the epoch-wide core, the report
adds cut, filter, resolution, and standing around it, and the audit joins on
the core identity (below). Every link in the additive chain is digest-covered, so
restored standing stays distinguishable from never-wrong — never-retracted,
retracted, and counter-retracted embed three different evidence sets and mint
three verification addresses while the first and third derive the same
scope — and so does a move **inside** the chain that moves no standing: with
siblings R1 and R2 both retracting a certification, counter-retracting R1
leaves it non-standing under R2, yet the closure gained a link and the report
identity moves — 5a's third-digest rule, holding at the consumer at every
depth (N8). **The epoch's packaging identity stays out of the derived
identity.** It is the operational selection input — required, exactly as
above — but moving a certification node between two covered corpora re-mints
the epoch — the address map's `(corpus, uid)` entry, both corpus states, the
receipt, and the packaging identity all move — while the certification's
address, standing, and the coverage are unchanged, and W5 forbids a derived
record from moving with it (packaging §5.2's semantic/packaging split, reused
at the consumer). The exact corpus states and the enumeration-rule binding
are receipt material, carried by the epoch's certification-enumeration
receipt (below), never digest members.

**The constructor gains the selection arguments, and recomputation needs no
pointer back to the epoch.** Comp §7.3c's one-constructor rule admits ordered
run refs and the optional code-lineage certification and "nothing else" —
R19's enumeration — so requiring an explicit cut and epoch amends that
signature at banking: the two selection arguments join the admitted list, and
R19's "nothing else" is restated over the extended enumeration. They are
**creation-time selection devices only**: import and audit recompute the
standings from the embedded closure's refs and resolutions and the scope from
the recomputed standings — the semantic projection is self-contained for
that — but completeness is receipt-proven on **both axes**, located by
content rather than by pointer. Whether the enumeration missed a
certification is the certification-enumeration receipt's build-time claim;
whether the embedded closures missed an applicable retraction is the
retraction-map receipt's — recomputing standing from the embedded closure
alone would trust the forger's closure. The auditor joins the
certification-enumeration receipt on the core identity the report names and
reaches the retraction axis **through the epoch** — and that join is
**multi-valued by design**: the same inventory can be the core of several
retained epochs whose retraction maps differ (build, retract, rebuild), and
the report deliberately records no epoch (W5) and no exact states (5a §6),
so no discriminator exists that could pick one capture without digesting
what those rules forbid. Audit is therefore **existential over retained
captures — and existential evidence works only positively**. A **qualifying
capture** is one retained epoch holding a **validating**
certification-enumeration receipt for the report's core identity *and* a
**validating** sibling retraction-map receipt from the same coherent states
(X9): the witness is never assembled across epochs, and a refuted or
unresolvable receipt supplies no witness (N7's crossed-receipt case).
**Audit evaluates in a fixed order, so no report has two outcomes.** First,
the **capture-free recomputation**: standings that do not follow from the
report's own embedded closures, or a scope that does not follow from the
standings, **refute** with no epoch consulted. Second, the **core
reduction** (below): **contradicted** → refuted; **unchecked** →
`unresolvable` (a doctored core identity matching no retained receipt lands
here, never validated); **checked** → the third step. Third, the
**existential capture evaluation**: the report **validates** when its
embedded closures agree with a qualifying capture's relevant map entries —
the finding naming **every agreeing qualifying epoch**, in sorted identity
order, never store or filesystem order, and no epoch that merely qualifies
without agreeing — and is **`unresolvable`** when no qualifying capture
agrees: retained epochs are not a complete history (whole-epoch GC,
packaging §9), so a missing or disagreeing witness is missing evidence,
never disagreement of record, and no superseding verification is ever
minted over an honest historical record. **Capture comparison never
refutes** — refutation comes only from the report's own recomputation or a
contradicted core (N7).

**Detection and correction split.** Comp §7.3c has audit mint a superseding
verification wherever recomputation contradicts a stored one — an act this
design's refutation branches cannot perform: the constructor requires an
explicit cut and epoch (above), the refuted report retains the cut but not
the epoch — never the complete selection pair — and in
the contradicted-core case no usable epoch need exist at all. Audit
therefore **emits the refutation finding and mints nothing**; the
superseding verification is a separate, explicit constructor act, supplied
with its own cut and epoch selection like any other derivation (N7).
*(Amended 2026-08-11, the act-report design §4: the evaluator is unchanged
and still mints nothing — the finding's durable home is an entry in the
boundary wrapper's inert act-report, published under the wrapper's own
operation intent.)* At banking this amends comp §7.3c's audit consequence
and R19 alongside the signature amendment already queued. This bound is
exact, not loose: a closure that omits a
retraction agrees only with captures **predating** it, and such a record is
byte-identical to an honest derivation over that earlier retained epoch —
the record tells no lie, and "derived from the newer epoch" is a claim that
exists only outside it. What stays undetected is provenance, never
disagreement — N4's bound, at the consumer — and freshness is the
prospective-upgrade discipline above plus 5a limitation 6's temporal bound,
never a record property (limitation 7). **Reduction over several receipts is world §5's rule,
unchanged**: one validating receipt makes the core **checked** — a refuting
sibling cannot condemn what another receipt validates, so a forged refuting
receipt cannot poison a valid core; **contradicted** only when none validate
and one refutes, which refutes the report's derivation; none resolvable —
malformed, un-held, or absent alike — leaves it **unchecked** →
`unresolvable`, the ordinary evidence-decay outcome, never a silent pass.
The reduction grades each receipt; the existential witness above is
stricter — it additionally requires the two validating receipts to share one
epoch, so a checked core lends nothing to another epoch's map.

**The consumption rule is per-shape, and the reduction is all-of.** A
verification shape determines its **required subject set**, every member
resolved from the original run's frozen recipe (§6): for `assessment` shape —
`equivalence` over the spec's equivalence binding, `interpretation` over the
spec's interpretation binding, `falsification` over `(the spec, that
interpretation binding)`, and `scope-derivation` over the boundary policy's
binding; for `dataset-production` shape — `equivalence` over the
`dataset-content-equality/v1` binding and `scope-derivation` likewise, there
being no spec. The cap is the verification's derived **scope** — the value
comp §7.3 already derives; no other tag exists — and it caps at
`not-certified` unless **every** required subject has a standing
certification under the selected cut. A subject match is
**discriminant-exact**: a `falsification` certification satisfies only the
named spec's falsification requirement — never a generic `interpretation`
requirement over the same binding, and never another spec's — and an
`interpretation` certification never satisfies `falsification`. Wrong purpose
and wrong spec are type mismatches, not near-misses (N7). At banking, comp
§7.3's `not-certified` derivation row amends: its trigger becomes this
required subject set, with the code-lineage claim's role in
`independent-implementation` unchanged (§7.5). "No standing certification" is therefore always a
statement relative to a named cut and an enumerated coverage — never "not
found under whatever was current" — 5a's discovery discipline, reused at the
consumer.

**The scan's completeness is receipt-covered, never assumed.** The enumeration
runs over the epoch's address map, and packaging gives derivation receipts to
the producer snapshot and the retraction map only — so an epoch whose build
omitted an in-coverage certification from its address map is internally
consistent, and the scan's "none found" would be honest and wrong with
nothing to refute it: neither the packaging identity nor X12 reaches the
address map. At banking the epoch gains a **certification-enumeration
receipt** on the retraction-receipt contract (packaging §7), member for
member — the projection identity of the by-kind certification enumeration in
its **location-free, resolution-free form** (sorted refs under the coverage;
the report's core submember, above), the exact corpus-state identity per
covered corpus, and a fixture-bound enumeration-rule identity, with the
address-map sourcing and per-ref corpus assignment as receipt material — and
X12 amends in
place to cover both receipted projections: omit an in-coverage certification
and repackage → rebuilding with the named rule against corpora at the named
states **refutes** the epoch. The receipt's reach is exactly its projection:
omitting an ordinary source or run from the address map is outside it, and
the address map at large stays receipt-uncovered as before. X9's
identical-states assertion and X10's held-store resolution row extend to the
third receipt under this name, and packaging §5's epoch inventory and §7's
receipt inventory gain it; world §5/W8a and packaging §5.2's semantic-member
wording gain the certification-enumeration projection as a semantic member
beside the map and snapshot identities. Still no fifth map: the receipt
covers the projection the scan already reads.

**Uncertified degrades, prospectively.** A required subject with no standing
certification → the derived scope caps at `not-certified`; nothing refuses. A certification
arriving later upgrades **future** derivations (over an epoch that carries it)
only — existing records embed the evidence they derived from and do not
revalue.

**A standing record qualifies; disqualification is an act.** "Standing" is
5a's meaning — not targeted by a standing retraction — and consumption checks
nothing else: reading never validates (comp §7.3c's rule), so a consumer
neither re-executes witnesses nor consults a stored evaluation state, and no
such state exists — §7.1's outcomes are evaluation outcomes at import and
audit, never fields on the record. The recomputation moments are unchanged:
import refuses a disagreeing certification before the write, and an audit
that refutes one emits a finding — the record **still qualifies until
retracted**, with the finding as the natural ground (`false-certification`).
Refutation observed is not standing subtracted; the subtraction is an
attributed 5a act, and only it changes consumption (N4, N7).

**Retraction is existential subtraction, not transitive invalidation.**
Retracting a certification removes **that record's** standing; a future
derivation caps only when **no standing certification remains** for a
required subject, so one of two sibling demonstrations retracted leaves the
subject satisfied (N8). Nor is the retracted world evidence-identical to one
where the certification never existed: the semantic projection retains the
found ref and the retraction that subtracted its standing, so the derived
record's embedded evidence differs — 5a's digest-is-the-memory shape, at the
consumer.
Retraction also does **not** silently retract the verifications already
derived in reliance on the certification — each embedded its discovery
evidence in its comparison report and stands until *its own* 5a retraction,
for which the certification's withdrawal is the natural ground
(`upstream-retraction`). One subtraction, one record, every consequence an
attributed act — 5a's chain discipline, upstream.

### 7.7 The 5a relation names are adopted

5a §9 left `retracts`, `grounded-in`, and `succeeded-by` provisional pending
this design's vocabulary. **Adopted as-is** into the contract's normative
relation vocabulary at the first cut: each already carries exactly one meaning
under 5a's banked semantics, and a rename would buy nothing but a migration.
5a §9's open question closes at banking.

## 8. The legacy checks — disposition principle

Every module in `science_tool/validate/checks` is classified, in the adoption
and implementation plans, into **exactly one** of:

1. **oracle** — its invariant is (or becomes, by table extension) an oracle
   row; the module retires in favor of the conformance suite;
2. **profile tooling** — curation and editorial checking outside the contract's
   scope, kept or rewritten as project-level tooling with no normative claim;
3. **retired with its subsystem** — it checked a structure the redesign
   removes.

An unclassified check is a **shadow authority** — a normative claim living
outside the contract — and the adoption plans treat one as a defect, not a
leftover. This design deliberately rules the principle and not the table
(ruling 2, §2).

## 9. Guarantees

New table, prefix **N**. Each row is certified by mutation, per the doctrine —
which table N now also guards reflexively (N2).

| # | guarantee | mutation test |
|---|---|---|
| N1 | Contract succession retains every id | amend an oracle's meaning → successor contract identity, human id retained, predecessor identity named; attempt a renumbering → unspellable; byte-identical republication → identity unchanged — **the only no-mint case**; a byte-changing, semantics-preserving reorganization → successor identity (§3) |
| N2 | Every oracle row can fail | sabotage a guarded invariant → its suite row fails; construct a row whose check passes under sabotage → the row itself is reported as malformed contract content — the doctrine as executable law |
| N3 | The fixture set is the normative half of every rule identity, and derivations name their exact binding | present an implementation failing one fixture → it is not that rule (resolution refuses); swap in a conforming implementation B → new implementation identity, same rule identity; **every receipt naming A still validates against A while A is held, and never revalidates against B**; change fixture semantics → new rule identity, `v2` disjoint. **Selection at freeze, refusal on ambiguity:** freeze a recipe with two conforming implementations held and no explicit selection → refused; freeze naming an un-held or fixture-failing implementation → refused. **Post-observation selection:** attempt to pass an implementation selection to the assessment or verification constructor → no such parameter exists; install B after a run's recipe froze → every derivation over that run still executes and records A, read from the recipe; un-hold A → `unresolvable`, never a silent rebind to B; two recipes differing only in the binding member → two run identities, and their assessments occupy two addresses |
| N4 | Certification is recomputable, and recomputation detects disagreement, not authorship | assert the constructor accepts bindings and witness refs only — no outcome parameter exists; import a certification whose typed-in outcomes **disagree** with re-execution → **refuted before any write**; **negative:** raw-write a self-consistent certification whose typed outcomes agree with re-execution → indistinguishable until audit, and the audit **validates** it — the re-execution supplies the demonstration and the lie was provenance only (R19's bound, not closed here); make a witness un-held → `unresolvable`, never `validated`; an audit refutation changes no consumption by itself — the remedy is a 5a retraction grounded in the finding (N7) |
| N5 | Certification binds contract, rule, **and** implementation | certify binding (rule, A) under contract K1; derive scope through implementation B of the same rule → uncertified, degraded; through A under K1 → certified; **through A under successor K2 → uncertified — the certification names K1 and speaks for no other cut**; assert the certification identity covers the subject discriminant, the contract identity, and both content identities; mutate **each subject member independently** — discriminant, rule identity, implementation identity, and the falsification arm's spec identity — → a different certification address every time (a fixture change is a rule-identity change, §6, so it is covered there and has **no second spelling** to mutate); two specs sharing one interpretation binding → two falsification certifications at two addresses, never one |
| N6 | Witness coverage is total per instrument | equivalence: a constant-equal rule and a constant-unequal rule each fail certification (one direction missing each way); interpretation: a rule that cannot reach `refuted` fails; falsification: a spec whose declared witness does not reach `refuted` under the certification's named interpretation binding fails, and a certification whose named binding's rule identity differs from the spec's `interpretation_rule` → **malformed**; scope-derivation: a certification missing any derivation row, including `not-certified` and the fail-closed degradations, fails |
| N7 | Uncertified degrades and never blocks, and standing is discovered from explicit inputs | freeze a spec naming an uncertified rule → minted, not refused; verify under an explicitly selected cut and epoch → derived scope `not-certified`, with the semantic discovery evidence (cut, coverage, found refs with resolutions and standings) embedded; certify every required subject, rebuild the epoch, verify again → upgraded scope on the **new** verification, the old one byte-unchanged; **all-of, per subject:** with every required subject certified, remove or retract each one's certification in turn → scope caps at `not-certified` every time; a certification an audit has refuted but no one has retracted → **still satisfies** its subject — reading never validates, and the finding grounds the retraction that changes consumption (§7.6); un-hold one of a standing certification's witnesses (N4's `unresolvable` route) → it **still satisfies** its subject — consumption consults no evaluation outcome, refuted or unresolvable alike, and only a retraction changes it; substitute a `falsification` certification naming a **different spec** → no match; substitute an `interpretation` certification where `falsification` is required over the same binding → no match — wrong spec and wrong purpose are type mismatches; move an `instrument-certification` node between two covered corpora and rebuild the epoch → the address map's `(corpus, uid)`, corpus states, receipt, and packaging identity all move, and a re-derivation embeds byte-identical evidence — the packaging identity never enters the derived record (W5, packaging §5.2). **Negative:** a derivation naming no cut or no epoch → unspellable — no implicit current; a standing certification in a corpus outside the selected epoch's coverage → not found, and the embedded coverage declaration states the bound; an in-coverage certification whose corpus is absent → a known unresolved ref in the evidence (`not-present`, packaging §5.4), satisfying no subject — the scope caps **and** the report identity differs from the no-certification case, never collapsing into "never existed"; omit an in-coverage certification from an epoch's address map and repackage → the certification-enumeration receipt refutes the epoch (X12, §7.6) — the scan's "none found" is only as strong as a receipt-valid epoch; raw-write a report whose standings do not follow from its own embedded closures → **refused** at import, **refuted** at audit — the capture-free recomputation, no epoch consulted; a report whose **checked** core has no agreeing qualifying capture → `unresolvable`, **never refuted**, and no superseding verification is minted — GC the only matching epoch and an honest historical report degrades to `unresolvable`, not refuted; **fixed order:** one refuting core receipt and no validator → **refuted** at the core-reduction step, the capture evaluation never reached — the same report is never both refuted and unresolvable; **crossed receipts:** E1 holds a validating core receipt but **no validating map receipt** (its map receipts, however many, are all refuted or unresolvable), and E2 holds a validating map receipt agreeing with the report's closures but **no validating core receipt** → no qualifying capture in either epoch, and only a cross-epoch splice of E1's core with E2's map could validate → `unresolvable` — the witness is a same-epoch validating pair, quantified over **all** of each epoch's receipts, several per artifact being ordinary; audit refutes a report → the finding is emitted and **nothing is minted** — the superseding verification is a separate explicit constructor act naming its own cut and epoch (§7.6); a report omitting a retraction that some retained **earlier** capture also lacks → validates against that capture, the finding naming every **agreeing** qualifying epoch in sorted identity order and no merely-qualifying one — byte-identical to an honest derivation over the earlier epoch, provenance being N4's bound (limitation 7); name a doctored core identity no retained receipt matches → `unresolvable`, never validated; one validating and one refuting receipt for the core → **checked** — world §5's reduction unchanged: a refuting sibling cannot condemn what another receipt validates; none validating, one refuting → contradicted, the derivation refuted; only malformed or un-held receipts → unchecked, `unresolvable` |
| N8 | Certification retraction is prospective, not transitive | retract the **sole standing** certification for a required subject → a new verification over the same binding derives scope capped at `not-certified`; **sibling case:** with two standing certifications for one subject, retract one → the other still satisfies the subject and a new verification's scope is uncapped; retract both → capped; **third-digest:** derive at never-retracted, at retracted, and at counter-retracted → three distinct comparison-report identities, with the first and third deriving the same scope — restored standing is never evidence-identical to never-wrong (5a §6, §7.6); **sibling counter-retraction:** with R1 and R2 both retracting the sole certification, counter-retract R1 → the subject stays unsatisfied and the scope stays capped, yet the report identity **moves** — the recursive closure gained a link, and every link is digest-covered; **specificity negative:** retract a node unrelated to every required subject elsewhere in coverage, rebuild the epoch, re-derive → the report is **byte-unchanged** — a retraction moves only computations whose closure contains its target (5a), and the retraction axis is not digested epoch-wide (§7.6); every existing verification is byte-unchanged and stands until its own retraction; assert the certification withdrawal serves as a 5a ground for those |
| N9 | Falsification certification reuses the interpretation evaluator | assert no falsification evaluator, signature, or execution path exists to call; a falsification certification whose witness manifest is absent from the spec's declaration → malformed; the demonstration runs the certification's named interpretation binding and nothing else |
| N10 | No legacy check survives unclassified | at adoption: every module in the legacy suite appears in exactly one disposition class; introduce an unclassified module → the adoption gate reports a defect |

## 10. Limitations

1. **Finite witnesses prove reachability, not correctness.** Certification
   rejects constant instruments and proves the declared outcomes reachable; it
   does not prove an instrument correct, adequate to its domain, or complete
   over it. A subtly wrong equivalence rule with reachable outcomes certifies.
2. **Witness quality is authored.** A trivially easy witness satisfies N6; what
   makes a witness *demanding* is review-surface work, not a gate.
3. **Code-lineage independence remains an authored claim** (comp §7.3,
   unchanged). Its form is attestation with grounds, embedded in the comparison
   report and **not independently retractable** — withdrawal retracts or
   supersedes the verification that embeds it (§7.5) — the one B-form survivor,
   kept because there is nothing executable to demonstrate.
4. **Distillation fidelity is human-checked.** The contract restates the
   designs; drift is defined as a defect in the contract's favor (§2), but its
   detection is review, not recomputation.
5. **One implementation makes conformance a self-check.** The suite becomes a
   cross-implementation instrument only if a second implementation ever exists;
   until then its force is the doctrine, not parity — stated so the STANDARD
   form is not read as claiming STANDARD's force.
6. **Certification evidence decays like every receipt.** Un-hold a witness,
   fixture, or implementation and re-execution is `unresolvable` — the world
   §5/W8a evidence-decay bound, inherited unchanged.
7. **Certification-discovery audit is existential over retained captures.**
   The comparison report deliberately names no epoch and no exact states
   (W5; 5a §6), so audit proves its evidence consistent with **some**
   retained coherent capture, never with a particular one: a report omitting
   a later retraction is indistinguishable from an honest derivation over
   the retained epoch that preceded it. What is lost is provenance, never
   disagreement — the closure still determines standing and restored stays
   distinguishable from never-wrong — and freshness is governed by explicit
   epoch selection and prospective upgrade (§7.6), not by the record.
   Whole-epoch GC (packaging §9) can sever the only capture a report
   validates against — then `unresolvable`, the ordinary evidence-decay
   outcome.

## 11. Open questions

- **Whether the contract cut becomes a world node.** Cuts are already held,
  immutable, content-addressed artifacts (§3) — addressability is settled. What
  stays open is only world-record status: a kind, a §4.2 basis row, and a reason
  for something to read cuts through the resolver rather than the store.
  Deferred until such a reader exists.
- **The first cut.** Distilling the banked designs into `CONTRACT.md` v1 is
  implementation-plan work, as is the executable suite's layout. *(Corrected
  2026-08-08: this read "the six designs" — the corpus as it stood at this
  document's banking.
  The cut's scope is whatever the ledger's artifact-7 row inventories —
  thirteen tables and 151 rows as of 2026-08-11, D, M, P, H and T having
  arrived since, and the kernel table now running **G1–G9** after the
  admission ramp appended G9.
  The scope is a live number, so the cut names it by reference and not by
  count.)*
  **Not to be confused with `contracts/science/CONTRACT.yaml`**, which exists:
  that is the *base profile* contract — the kernel-owned claim grammar the formal
  model §8 sites — and this cut is the *normative conformance* contract. Two
  artifacts, two jobs, and the shared word is the only thing they share.
- **Existing instruments certify by succession, or not at all.** A frozen spec
  cannot acquire the witness reference its falsification declaration lacks —
  "retroactive certification" of an immutable identity is unspellable (§7.4).
  The adoption choice is the successor-minting cadence: a sweep, mint on next
  authored use, or never; an existing spec's instruments certify only through
  the successor spec that declares witnesses.
