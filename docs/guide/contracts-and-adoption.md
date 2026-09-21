---
title: Contracts and adoption
status: living
created: 2026-08-08
updated: 2026-09-21
sources:
  - ../designs/2026-08-03-normative-contract-design.md
  - ../designs/2026-08-03-redesign-adoption-ledger.md
  - ../designs/2026-08-05-review-disposition-and-conformance-cut-1.md
  - ../designs/2026-08-07-corpus-survey-and-vocabulary-admission-design.md
  - ../designs/2026-08-07-multi-corpus-typing-exercise.md
  - ../designs/2026-08-09-admission-ramp-design.md
  - ../designs/2026-08-09-conformance-cut-2.md
  - ../designs/2026-08-11-act-report-design.md
  - ../designs/2026-08-11-conformance-cut-3.md
  - ../designs/2026-08-17-conformance-cut-4.md
  - ../designs/2026-08-18-composition-root-adapter-design.md
  - ../designs/2026-08-19-conformance-cut-5.md
  - ../designs/2026-08-19-family-adapters-design.md
  - ../designs/2026-08-20-world-index-slice-2-design.md
  - ../designs/2026-08-20-conformance-cut-7.md
  - ../designs/2026-08-22-conformance-cut-8.md
  - ../designs/2026-08-23-conformance-cut-9.md
  - ../designs/2026-08-24-world-index-holdings-design.md
  - ../designs/2026-08-24-conformance-cut-10.md
  - ../designs/2026-08-26-world-index-intent-boundary-design.md
  - ../designs/2026-08-27-conformance-cut-11.md
  - ../designs/2026-08-29-conformance-cut-12.md
  - ../designs/2026-08-30-conformance-cut-13.md
  - ../designs/2026-08-30-run-confinement-design.md
  - ../designs/2026-08-29-successor-admission-design.md
  - ../designs/2026-09-03-world-changing-families-design.md
  - ../designs/2026-09-03-conformance-cut-16.md
  - ../designs/2026-09-04-write-permits-design.md
  - ../designs/2026-09-04-conformance-cut-18.md
  - ../designs/2026-09-05-conformance-cut-20.md
  - ../designs/2026-09-05-writer-session-design.md
  - ../designs/2026-09-05-conformance-cut-19.md
  - ../designs/2026-09-06-conformance-cut-21.md
  - ../designs/2026-09-08-biology-pack-design.md
  - ../designs/2026-09-08-conformance-cut-22.md
  - ../designs/2026-09-13-conformance-cut-27.md
  - ../designs/2026-09-14-conformance-cut-28.md
  - ../designs/2026-09-14-conformance-cut-29.md
  - ../designs/2026-09-15-conformance-cut-30.md
  - ../designs/2026-09-15-conformance-cut-31.md
  - ../designs/2026-09-16-conformance-cut-32.md
  - ../designs/2026-09-16-conformance-cut-33.md
  - ../designs/2026-09-19-conformance-cut-34.md
  - ../designs/2026-09-20-conformance-cut-35.md
  - ../designs/2026-09-21-conformance-cut-36.md
  - ../plans/2026-08-27-conformance-cut-11-results.md
  - ../plans/2026-08-29-conformance-cut-12-results.md
  - ../plans/2026-09-01-conformance-cut-13-results.md
  - ../plans/2026-09-04-conformance-cut-17-results.md
  - ../plans/2026-09-04-conformance-cut-18-results.md
  - ../plans/2026-09-05-conformance-cut-19-results.md
  - ../plans/2026-09-16-conformance-cut-32-results.md
  - ../plans/2026-09-16-conformance-cut-33-results.md
  - ../plans/2026-09-19-conformance-cut-34-results.md
  - ../plans/2026-09-20-conformance-cut-35-results.md
  - ../plans/2026-09-21-conformance-cut-36-results.md
---

# Contracts and adoption

## TL;DR

Frozen guarantee identifiers become executable, mutation-tested obligations in
immutable contract cuts; adoption proceeds in dependency-ordered slices, and the
living ledger—not this guide—is the authority for what has actually landed.

## Why it matters

A large design can look complete while its strongest claims remain untested, or
a partial implementation can quietly redefine success around what was easiest
to build. Science counters both risks: guarantees keep stable names, every
conformance check must demonstrate how it fails, and each implementation slice
is selected prospectively at a fully designed boundary.

## Key ideas

### Designs explain; contract cuts will govern

The design corpus records rationale, alternatives, amendments, and declared
limits. The normative contract design specifies a smaller immutable artifact
containing kinds and identities, operations and outcomes, rule bindings,
conformance oracles, and change policy. Once the first normative contract cut
exists, drift is resolved in the contract's favor; earlier designs remain the
history explaining why the rule exists.

A contract identity hashes its exact canonical normative bytes. Any byte change
mints a successor that names its predecessor. A readable version is only an
alias. Frozen oracle identifiers—such as G3, W8a, R12, M10, and P4—are never
renumbered, so reviews and tests can point to the obligation more precisely than
to a mutable section number.

### Rules bind meaning to the code that ran

A rule identity is `(symbol, fixture-set identity)`: fixtures are the normative
definition of behavior. A held implementation that passes those fixtures is the
operational half. The exact pair of rule identity and implementation content
identity enters every derived result, because finite fixtures cannot guarantee
that two implementations agree on every unseen input.

Interpretation, equivalence, and scope-derivation instruments may also receive
an immutable certification. Certification recomputes witnesses showing that a
specific binding both conforms and reaches all required outcomes. Missing or
retracted certification does not block use; it caps downstream scope at
`not-certified`, making the limit visible to admission rules.

### Every oracle must be falsifiable

The guarantee tables are intended to become a conformance suite. Each oracle
row names a source mutation that should make its exact check fail. A check that
cannot fail, no longer reaches the mutated code, points to an uncollectable test,
or was already failing before mutation is malformed contract content—not a
successful guard.

The first implementation made this discipline executable with an N2 harness.
It applies each declared mutation to an isolated copy and distinguishes sound
arms from `vacuous`, `stale`, and `uncollected` ones. Ten of its first forty arms
were defective, demonstrating why a green ordinary suite alone is not enough.

### Adoption follows legal partial states

The [adoption ledger](../designs/2026-08-03-redesign-adoption-ledger.md#3-order-of-work)
orders work by actual dependencies. Designs can bank before their dependencies
are implemented; an implementation slice may cross only the boundaries it can
exercise and must leave the rest explicitly deferred. The clean-start ruling
also forbids mechanical predecessor migration and compatibility machinery:
records are reproduced through the new typed boundaries.

Conformance cut 1 was frozen before implementation. It selected eleven of 126
then-banked guarantee rows—six wholly and five only at named assertion arms—and
classified the other 115 by the subsystem that would unblock them. The corpus
has since grown to 216 rows across twenty frozen tables (the README keeps the
count): the belief policy's P1–P9 banked the day the cut was drawn, the admission ramp appended G9 on 2026-08-09
while narrowing W3's dataset arm, the verified-holdings record design banked
H1–H4 on 2026-08-10, the act-report design banked T1–T8 on 2026-08-11, the coordination-and-view-kinds design banked W17–W18 on 2026-08-31, and
later designs banked their tables through Q (estimand typing, cut 31) and U
(composite claims, cut 32). The
cut's stop rule was the last fully designed seam: typed claim construction,
projection, identity, decode, and cross-language parity, with no persistence
boundary and no belief computation.

[Conformance cut 2](../designs/2026-08-09-conformance-cut-2.md) was frozen
2026-08-09 on the same discipline, before its slice was built, and gives the
ten post-cut-1 rows their owner. The selection required no amendment after
the freeze. It is drawn at the belief seam — the derived
admission state, the assessment admission gate, the belief input closure digest,
and `science.belief.v1` under an exact binding — selecting 13 rows in full and
11 at named assertion arms, and classifying the remaining 108 deferred rows by the
subsystem that unblocks them. The admission ramp's three open questions are its
stated boundary conditions: verified-holdings observations enter as supplied
arguments precisely because where they are recorded had not yet been
designed at the freeze (designed 2026-08-10, the verified-holdings record
design; the frozen selection is unchanged), no arm reads an observation's
timestamp, and the partly-pinned fixtures exercise a ruled boundary without
corroborating the ruling. A second reader reviewed the
selection adversarially before the freeze, and every arm its findings moved,
they moved out.

[Conformance cut 3](../designs/2026-08-11-conformance-cut-3.md) was frozen
2026-08-11 at the run boundary, again before any of its implementation
existed. It selects 15 rows in full and 19 at named assertion arms — spec
freezing and closure construction, the execution boundary through a minimal
Snakemake adapter, dataset production, replay and verification-as-value, and
the completion and report layer. Of the twelve rows banked after cut 2, seven
— T1–T6 and T8 — gain their first arms, while H1–H4 and T7 wait on the
persistence seam: the holdings design's own assignment. The selection was
amended across three adversarial readings before merge, with the frozen text
preserved verbatim, and a scratch root is staging by location, not
confinement — no arm of this cut reaches `clean-environment`. The selection
required no amendment after the freeze.

### Measurements constrain the next slice

The eight-corpus survey and three-corpus typing exercise are measurements, not
conformance oracles. They showed that fitted vocabulary can type mm30's 307
structured propositions, but only one surveyed corpus meaningfully exercises
the calculus; no surveyed record exercises qualifiers. They also prevented
readerless or unexercised vocabulary from entering the base profile.

Measurements therefore narrow claims and reveal prerequisites. They do not
change implementation status, expand a frozen cut after the fact, or turn a
fitted result into independent validation.

## How it connects

- [Foundations](foundations.md) defines the ownership and transition boundaries
  to which contracts give executable form.
- [Claims and belief](claims-and-belief.md) explains M1–M13, P1–P9, and the
  corpus measurements summarized here.
- [Identity, world, and change](identity-world-and-change.md) supplies immutable
  contract succession, standing, epochs, and audit inputs.
- [Computation and reproducibility](computation-and-reproducibility.md) uses
  exact rule bindings and instrument certification in runs and verifications.

## Current state

Cut 23 discharges the world read view and cross-corpus traversal: D3, S1,
S1a, S5, W6, W10 and R19 close; R23 gains its coverage clause and stays partial.
W8b is measured and not selected. Its build defect is repaired by
`beliefs-fda0e5`; the conformance row awaits a future selection.
The [results record](../plans/2026-09-09-conformance-cut-23-results.md) preserves
the certified chain and repository gates; it makes no new mm30 measurement.

Thirty-two conformance cuts have been frozen and discharged, each frozen before
its code existed and each from cut 4 onward discharged on the certified tuple
with a results record under `../plans/`. The cut discipline is what this page
owns: a cut selects rows, the acceptance runner arms each selected unit with
an exact sabotage mutation, and a discharge is a results record, never a
re-reading of the frozen text. Cut 13 closed the run boundary's confinement
arms — R15, R4, R9 and R13 in full, R16 and R21 at their confinement arms —
so a real verification can reach `clean-environment`
(`../designs/2026-08-30-run-confinement-design.md`). Cut 15 closes R2, R16,
R20, and R21 across the full workflow surface and reads R23's local
basis/composition disagreement without reopening replay cardinality. The
relocation cut is discharged as cut 16: W5 reads in full, G3 and D7 close,
W16, C3, R23, M3 and T2 remain partial on their named remainders, and T8 is
re-read against `move` and `consolidate`. The write-permits cut is discharged
as cut 17: E1–E8 close, every write entry point requires its permit before any
effect, and no caller supplies an actor. The deletion cut is discharged as
cut 18 — frozen the same day as cut 17 and numbered after it, because a number
is claimed at freeze in freeze order: G2c, G8, C6, R5, W16, M1 and M5 close;
S5, R23, R19, R22 and M3 were partial at that cut; S5 and R19 close at cut 23.
C1, T8, M11 and M13 were re-read.
The writer-session cut is discharged as cut 19: J1–J11 close — the `J` table's
every row, selected in full before implementation and read in full afterwards
(`../designs/2026-09-05-conformance-cut-19.md`).
The facet-contracts slice is discharged as cut 20: 15 rows read full/closed,
D1 was partial on its cross-repository arm, and D6's domain-facet reader arm
then traveled with biology slice 2
(`../plans/2026-09-07-conformance-cut-20-results.md`).
The verification-publication cut is discharged as cut 21 (V1–V8 full/closed),
and the biology-pack slice is discharged as cut 22 (B1–B7 and D6 full/closed;
D1 still partial then)
(`../plans/2026-09-08-conformance-cut-22-results.md`).
Cut 26 closes D1's cross-repository negative through namespace-renaming
invariance and two `nodes`-package sabotages
(`../designs/2026-09-12-conformance-cut-26.md`;
`../plans/2026-09-12-conformance-cut-26-results.md`).
Cut 27 discharges world resolution slice 3 — R23's snapshot, import and
divergence clauses, W8a's packaging arms, the X5 and W13 relabels and the new
row S9 (`../plans/2026-09-13-conformance-cut-27-results.md`).
Cut 28 discharges world resolution slice 4 — W7's view evaluation and the W8/W8b conflicts over existing code (`../designs/2026-09-14-conformance-cut-28.md`; `../plans/2026-09-14-conformance-cut-28-results.md`).
Cut 29 discharges world resolution slice 5 — dataset ids derived from the content identity and held at the write boundary and both inputs of `consolidate` (`../designs/2026-09-14-conformance-cut-29.md`; `../plans/2026-09-14-conformance-cut-29-results.md`).
Cut 30 discharges world resolution slice 6 — divergent correction histories reconcile at `consolidate` by absorption (`../designs/2026-09-15-conformance-cut-30.md`; `../plans/2026-09-15-conformance-cut-30-results.md`).
Cut 31 is discharged: estimand typing, the first off-path lane after the world-read path closed, reading Q1–Q10 in full over 26 sabotage arms — the estimand, its applicability, and the estimate and uncertainty the rule yields are typed, and a pre-grammar record is refused under its own name (`../designs/2026-09-15-conformance-cut-31.md`; design `../designs/2026-09-12-estimand-typing-design.md`; results `../plans/2026-09-16-conformance-cut-31-results.md`).
Cut 32 discharges composite claims, the second off-path lane under rule 6, reading U1–U10 in full over 26 sabotage arms — the `composite` kind records the structure a set of claims is drawn against, its reading is derived through the traced evaluator and stored nowhere, and it is inert to belief (`../designs/2026-09-16-conformance-cut-32.md`; design `../designs/2026-09-12-composite-claims-design.md`; results `../plans/2026-09-16-conformance-cut-32-results.md`).
Cut 33 discharges correction-remainder slice 1: standing reaches the evaluator,
C7 and C3 close, and C10's audit arm is read over 11 declaration units.
Cut 34 discharges correction-remainder slice 2 and closes the boundary: the
retraction target gains a third arm, the semantic snapshot, read live from
the corpora its own coverage names and reported or refused at import, audit,
diagnostic query, and the world read; C8 and C9 close over 17 declaration
units, and the mutation lane has no further open boundary
(`../designs/2026-09-19-conformance-cut-34.md`;
`../plans/2026-09-19-conformance-cut-34-results.md`).
Cut 35 discharges URL retrieval and closes the boundary: the `url` locator
under the banked canonicalization profile, the network discipline as the
kernel's URL dereference boundary behind an injectable transport seam, and
the `acquisition` operation — one intent, per resource a URL look and an
optional managed materialization, one act-report published in the same
registered transaction as the dataset it mints. H4, G9, R10, T5, T1 and T4
close over 27 declaration units and eleven boundary invariants; T2 stays
partial on the `audit` and `re-check` operation kinds and T7 on its
cross-root case
(`../designs/2026-09-20-conformance-cut-35.md`;
`../plans/2026-09-20-conformance-cut-35-results.md`).
Cut 36 discharges event-level L8 and closes the boundary: an event is
`(corpus_id, entry_digest)` with at most one moment, a cut speaks about a
chain only with a placeable anchor under the live genesis, and the relation
is witness-asymmetric over ordered cuts — the double witness answers
`unordered`. L8 closes over 16 declaration units and three boundary
invariants; L4 and L10 close as relabels citing cuts 8, 9 and 10; L1 stays
partial on its persistence arms, re-homed to `persistence-cut`. The corpus
now has **186 of 216 rows closed, 30 open**
(`../designs/2026-09-21-conformance-cut-36.md`;
`../plans/2026-09-21-conformance-cut-36-results.md`).
The complete normative contract cut, its executable suite and N1–N10 are not
yet implemented. The
[adoption ledger's current-state summary](../designs/2026-08-03-redesign-adoption-ledger.md#current-state-2026-09-16)
states what is built and which remaining boundaries have named owners; the cut
documents and results records in the references below are the evidence.

The contributor guide has no ledger artifact of its own. That is deliberate:
it documents the system, does not implement a system boundary, and no adoption
item waits on it.

## Open edges

See [Contracts and adoption](open-questions.md#contracts-and-adoption) for
contract governance, the normative artifact's shape, certifying instruments that
already exist, and the residues the verified-holdings record and the act-report
design deliberately left open. The writer model sits with the other authority
questions under
[Identity, world, and change](open-questions.md#identity-world-and-change).

## References

- [Normative contract guarantees N1–N10](../designs/2026-08-03-normative-contract-design.md#9-guarantees)
- [Contract versioning and frozen oracle identifiers](../designs/2026-08-03-normative-contract-design.md#4-versioning--what-mints-what)
- [Adoption order and landed artifacts](../designs/2026-08-03-redesign-adoption-ledger.md#3-order-of-work)
- [Prospectively frozen conformance cut 1](../designs/2026-08-05-review-disposition-and-conformance-cut-1.md#5-conformance-cut-1--frozen-prospectively)
- [Conformance cut 2 and its boundary conditions](../designs/2026-08-09-conformance-cut-2.md#21-the-admission-ramps-three-open-questions-as-boundary-conditions)
- [Vocabulary admission decision](../designs/2026-08-07-corpus-survey-and-vocabulary-admission-design.md#4-ruling-admission-by-agreement-and-exercise)
- [Typing exercise results and limits](../designs/2026-08-07-multi-corpus-typing-exercise.md#3-results)
- [Conformance cut 4 — the first persistence slice](../designs/2026-08-17-conformance-cut-4.md)
- [Composition-root adapter design](../designs/2026-08-18-composition-root-adapter-design.md)
- [Conformance cut 5 — the family adapters](../designs/2026-08-19-conformance-cut-5.md)
- [Family adapters design](../designs/2026-08-19-family-adapters-design.md)
- [Cut 12 discharge results](../plans/2026-08-29-conformance-cut-12-results.md)
- [Cut 34 discharge results](../plans/2026-09-19-conformance-cut-34-results.md)
- [Cut 35 discharge results](../plans/2026-09-20-conformance-cut-35-results.md)
- [Cut 36 discharge results, the newest results record](../plans/2026-09-21-conformance-cut-36-results.md)
