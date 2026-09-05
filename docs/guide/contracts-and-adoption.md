---
title: Contracts and adoption
status: living
created: 2026-08-08
updated: 2026-09-05
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
  - ../designs/2026-09-05-writer-session-design.md
  - ../designs/2026-09-05-conformance-cut-19.md
  - ../plans/2026-08-27-conformance-cut-11-results.md
  - ../plans/2026-08-29-conformance-cut-12-results.md
  - ../plans/2026-09-01-conformance-cut-13-results.md
  - ../plans/2026-09-04-conformance-cut-17-results.md
  - ../plans/2026-09-04-conformance-cut-18-results.md
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
now holds 153 rows across thirteen frozen tables: the belief policy's P1–P9
banked the day the cut was drawn, the admission ramp appended G9 on 2026-08-09
while narrowing W3's dataset arm, the verified-holdings record design banked
H1–H4 on 2026-08-10, the act-report design banked T1–T8 on 2026-08-11, and
the coordination-and-view-kinds design banked W17–W18 on 2026-08-31. The
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

Eighteen conformance cuts have been frozen and discharged, each frozen before
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
S5, R23, R19, R22 and M3 remain partial on their named remainders; C1, T8, M11
and M13 are re-read.
The writer-session cut is frozen as cut 19 and not yet discharged: J1–J11,
the `J` table's every row, selected in full before implementation
(`../designs/2026-09-05-conformance-cut-19.md`).
The complete normative contract cut, its executable suite and N1–N10 are not
yet implemented. The
[adoption ledger's current-state summary](../designs/2026-08-03-redesign-adoption-ledger.md#current-state-2026-09-04)
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
- [Cut 13 discharge results, the newest results record](../plans/2026-09-01-conformance-cut-13-results.md)
