---
title: Contracts and adoption
status: living
created: 2026-08-08
updated: 2026-09-26
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
  - ../designs/2026-09-21-conformance-cut-37.md
  - ../designs/2026-09-22-conformance-cut-38.md
  - ../designs/2026-09-22-publication-design.md
  - ../designs/2026-09-23-conformance-cut-39.md
  - ../designs/2026-09-24-conformance-cut-40.md
  - ../designs/2026-09-24-live-query-evaluation-design.md
  - ../designs/2026-09-25-conformance-cut-41.md
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
  - ../plans/2026-09-21-conformance-cut-37-results.md
  - ../plans/2026-09-22-conformance-cut-38-results.md
  - ../plans/2026-09-23-conformance-cut-39-results.md
  - ../plans/2026-09-24-conformance-cut-40-results.md
  - ../plans/2026-09-25-conformance-cut-41-results.md
  - ../plans/2026-09-02-conformance-cut-14-results.md
  - ../plans/2026-09-01-conformance-cut-15-results.md
---

# Contracts and adoption

## In brief

The designs make promises, and each promise has a permanent label — G1, W8a,
R12 — called a **guarantee row**. Work is built in small slices called
**conformance cuts**. Each cut is frozen before any of its code exists: it names
which rows the slice will satisfy, and states what it leaves out. Every check
the cut adds is paired with a deliberate break of the code, and the check must fail when that
break is applied; a check that cannot fail does not count. The
[adoption ledger](../designs/2026-08-03-redesign-adoption-ledger.md#current-state-2026-09-16),
not this guide, says what has landed.

- **Promises have permanent names.** Rows are never renumbered, so a test or a
  review can point at exactly the obligation it covers.
- **Scope is chosen before the code.** A cut cannot be widened afterwards to
  match what happened to get built.
- **Every check proves it can fail.** Each is armed with a sabotage that must
  turn it red.
- **Partial is the honest default.** If any selected part of a row is not
  exercised, the row stays partial.
- **Measurements inform; they do not certify.** Surveys of real corpora narrow
  what the next slice should claim, and never change implementation status.

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

[Conformance cut 1](../designs/2026-08-05-review-disposition-and-conformance-cut-1.md#5-conformance-cut-1--frozen-prospectively)
set the pattern. Frozen before implementation, it selected eleven of the 126
rows then banked — six wholly and five only at named assertion arms — and
classified every other row by the subsystem that would unblock it. Its stop rule
was the last fully designed seam: typed claim construction, projection,
identity, decode, and cross-language parity, with no persistence and no belief
computation. [Cut 2](../designs/2026-08-09-conformance-cut-2.md) drew the next
line at the belief seam and [cut 3](../designs/2026-08-11-conformance-cut-3.md)
at the run boundary, each frozen before any of its code existed and each read
adversarially by a second reviewer before the freeze. Every cut since has
followed the same discipline.

The row corpus grows as designs bank new tables; the repository README keeps
the current count, and the ledger the number closed.

### How a cut runs

1. **Freeze.** A cut document selects rows, whole or at named assertion arms,
   and states what it deliberately leaves out. It is frozen by a dated commit
   after review; later evidence that invalidates it is recorded beside it, never
   edited into it. A cut number is claimed at freeze, in freeze order, which is
   why cut 18 was frozen as 17 and renumbered.
2. **Arm.** The acceptance runner for the cut (`python/tools/cutN_acceptance.py`)
   pairs each selected unit with an exact sabotage mutation (runners exist
   from cut 4 onward). The N2 harness applies it to an isolated copy and
   classifies the arm sound, `vacuous`, `mixed`, `uncollected`, or `stale`.
3. **Discharge.** The suite runs on the certified kernel-and-volume tuple, where
   a missing capability is a failure rather than a skip. A **results record**
   under `../plans/` records the outcome; the ledger, the roadmap, and
   `test_recent_cut_acceptance.py` gain the cut in the same change.

Two constraints recur in every plan because missing them has cost fix rounds:
only `beliefs/root.py` may import `atoms`, and every discharged cut adds its row
to `test_recent_cut_acceptance.py`.

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
- [Writes, operations, and publication](writes-operations-and-publication.md)
  describes the doors whose guarantees the later cuts test.

## Current state

Forty-one conformance cuts have been frozen and discharged, each frozen before
its code existed and each from cut 4 onward discharged on the certified tuple.
Cut 42, the remote half of the publish act, is being designed and is not yet
frozen. The complete
normative contract cut, its executable suite, and N1–N10 are not yet
implemented; the roadmap schedules them after `publish`. The
[adoption ledger's current-state summary](../designs/2026-08-03-redesign-adoption-ledger.md#current-state-2026-09-16)
states the row count, what remains, and who owns it.

The contributor guide has no ledger artifact of its own. That is deliberate:
it documents the system, does not implement a system boundary, and no adoption
item waits on it.

### What each cut built

A map from a cut number to the boundary it built. The cut document holds the
exact selection; the results record under `../plans/` holds the evidence.

| Cut | What it built |
|---|---|
| [1](../designs/2026-08-05-review-disposition-and-conformance-cut-1.md) | Typed claim construction, projection, identity, decode, and Python/TypeScript parity |
| [2](../designs/2026-08-09-conformance-cut-2.md) | The belief seam: admission state, admission gate, belief-input digest, `science.belief.v1` |
| [3](../designs/2026-08-11-conformance-cut-3.md) | The run boundary: spec freezing, closure, minimal Snakemake execution, dataset production, replay, verification as a value, completion reading |
| [4](../designs/2026-08-17-conformance-cut-4.md) | The first persistence slice: the composition root over the certified `atoms` engine and the add-only write boundary |
| [5](../designs/2026-08-19-conformance-cut-5.md) | Family adapters: supersede, revise, retract, explicit import |
| [6](../designs/2026-08-20-conformance-cut-6.md) | The world registry |
| [7](../designs/2026-08-20-conformance-cut-7.md) | The epoch carrier |
| [8](../designs/2026-08-22-conformance-cut-8.md) | Mutation-log verification and anchoring |
| [9](../designs/2026-08-23-conformance-cut-9.md) | Root lifecycle and the store substrate |
| [10](../designs/2026-08-24-conformance-cut-10.md) | Verified holdings, store-side |
| [11](../designs/2026-08-27-conformance-cut-11.md) | General intent qualification and durable run publication |
| [12](../designs/2026-08-29-conformance-cut-12.md) | Successor admission (G4 at persistence width) |
| [13](../designs/2026-08-30-conformance-cut-13.md) | Run confinement: `clean-environment` becomes reachable |
| [14](../plans/2026-09-02-conformance-cut-14-results.md) | Coordination and view kinds |
| [15](../plans/2026-09-01-conformance-cut-15-results.md) | The full workflow surface (R2, R16, R20, R21) |
| [16](../designs/2026-09-03-conformance-cut-16.md) | Relocation: `move` and `consolidate` |
| [17](../plans/2026-09-04-conformance-cut-17-results.md) | Write permits at every write entry point (E1–E8) |
| [18](../designs/2026-09-04-conformance-cut-18.md) | Managed deletion |
| [19](../designs/2026-09-05-conformance-cut-19.md) | The writer session (J1–J11) |
| [20](../designs/2026-09-05-conformance-cut-20.md) | Facet contracts |
| [21](../designs/2026-09-06-conformance-cut-21.md) | Verification publication (V1–V8) |
| [22](../designs/2026-09-08-conformance-cut-22.md) | The biology pack and the domain-facet read (B1–B7, D6) |
| [23](../designs/2026-09-09-conformance-cut-23.md) | The world read view and cross-corpus traversal |
| [24](../designs/2026-09-10-conformance-cut-24.md) | Coreference attestation and its balance |
| [25](../designs/2026-09-10-conformance-cut-25.md) | Source addresses derived from normalized identifiers; identifier correction |
| [26](../designs/2026-09-12-conformance-cut-26.md) | D1's cross-repository negative |
| [27](../designs/2026-09-13-conformance-cut-27.md) | Epoch import, epoch audit and snapshot-state diagnostics, and the damaged-corpus world audit |
| [28](../designs/2026-09-14-conformance-cut-28.md) | View-query evaluation at an epoch (W7, W8b) |
| [29](../designs/2026-09-14-conformance-cut-29.md) | Dataset addresses derived from content identity |
| [30](../designs/2026-09-15-conformance-cut-30.md) | Reconciling divergent correction histories at `consolidate` |
| [31](../designs/2026-09-15-conformance-cut-31.md) | Estimand typing (Q1–Q10) |
| [32](../designs/2026-09-16-conformance-cut-32.md) | Composite claims (U1–U10) |
| [33](../designs/2026-09-16-conformance-cut-33.md) | Retraction standing reaches the belief evaluator (C3, C7) |
| [34](../designs/2026-09-19-conformance-cut-34.md) | Retraction of a producer's semantic snapshot (C8, C9) |
| [35](../designs/2026-09-20-conformance-cut-35.md) | URL retrieval and the `acquisition` operation |
| [36](../designs/2026-09-21-conformance-cut-36.md) | Event-level ordering across chains (L8) |
| [37](../designs/2026-09-21-conformance-cut-37.md) | Digest-matched classification of removed records (L13) |
| [38](../designs/2026-09-22-conformance-cut-38.md) | The `audit` and `re-check` operations (T2) |
| [39](../designs/2026-09-23-conformance-cut-39.md) | Publication records and the publish intent (W17, Y1–Y4) |
| [40](../designs/2026-09-24-conformance-cut-40.md) | The publish act for a local destination (Y5–Y10) |
| [41](../designs/2026-09-25-conformance-cut-41.md) | Live view-query evaluation (Z1–Z5) |

## Open edges

See [Contracts and adoption](open-questions.md#contracts-and-adoption) for
contract governance, the normative artifact's shape, certifying instruments that
already exist, relation endpoint enforcement, and the verified-holdings record's
residue. The act report's residue and the writer model are under
[Writes, operations, and publication](open-questions.md#writes-operations-and-publication).

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
- [The newest results record, cut 41](../plans/2026-09-25-conformance-cut-41-results.md); every other cut's record sits beside it under `docs/plans/`
