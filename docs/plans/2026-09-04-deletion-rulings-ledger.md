# Deletion implementation rulings ledger

**Date:** 2026-09-04
**Scope:** implementation and discharge of
`../designs/2026-09-04-conformance-cut-17.md`.

This file preserves the rulings made while the deletion cut's plan was
executed. The frozen cut remains the authority for selection and accounting;
this ledger records how implementation ambiguities were resolved.

## R1 — The exclusion table has one home

`EXCLUDED_MUTATION_KINDS` lives in `corpus.py`; `relocation.py` imports it.

## R2 — A stored verification names its runs optionally

The verification facet gains an optional `derivation` member; a verification
without one is unchecked, never refused, so existing fixtures stay valid and
`verification-publication` later writes derived verifications carrying it.

## R3 — Scope is not recomputed

The stored projection carries no comparison report; the audit and the import
recompute verdict and assessment identity only (frozen §7).

## R4 — Evidence is explicit

`DerivationEvidence` is supplied by the caller; `NO_EVIDENCE` is an explicit
empty value, and an unresolvable derivation is an import **finding**, never a
silent pass.

## R5 — The semantic audit is its own module

`beliefs.audit` composes `corpus_check`; `world/verify.py` is untouched by
this cut, contrary to design §9's expectation, because the contradiction
findings are semantic recomputation and not log evaluation.

## R6 — Ω_valid is instrumentation-tested

Standing and belief evaluation are made to raise; the audit must still
classify.

## R7 — The cyclic pair is read for classification only

The raw pair is malformed by identity recomputation; the cut asserts its
classification and never its acyclicity (the banked limitation stands).

## R8 — `gather` locates the claim through the `assesses` edge

Never by decoding every proposition, so an unrelated claim is neither read
nor traced.

## R9 — The tasks CLI cannot attach a plan outside `docs/plans/`

The eleven task children carry the plan and step in prose bodies rather than
structured `plan:`/`step:` fields (feedback filed as tasks-1eb9d2).

## R10 — The Ω_valid skip set is the malformedness codes

`flagged` in the audit is narrowed to `semantic-hash-missing`,
`semantic-hash-stale`, `coordination-facet-malformed`, and
`derivation-malformed` — not every `corpus_check` finding. The spec's
Ω_valid is about malformed classification, not every finding a corpus check
can report.

## R11 — An unreadable neighbour leaves the derivation unchecked, never abort

A neighbour record that cannot be read (a stale or missing stamp on a
producing run, or on a verification's or assessment's named run) leaves the
audited record's derivation *unchecked* with a reason naming the neighbour.
`audit_corpus` never raises on a bad neighbour file; a `MalformedRecord`
raised from a record's own members becomes a `derivation-malformed` finding
instead of propagating.

## R12 — `check_assessment` compares only the comparable members

`outcome`, `interpretation_rule`, `estimate`, `uncertainty`, `estimand`, and
`applicability`, plus `spec` and a `run_ref`-normalized `run`. `proposition`
is excluded because the stored facet carries a corpus ref and the derivation
a claim target — different namespaces, not a disagreement.

## R13 — A verification with no derivation member imports unchecked, not refused

It imports with a `derivation-unchecked` finding like any other
unrecomputable member. The `derived` fixture used to exercise this is a
synthetic decodable closure, not a Snakemake run.

## R14 — `claim_from_stored` resolves the qualifier-body conflict by delegation, not duplication

It calls the module's own `_wire_parts(wire)` before delegating rather than
adding a second qualifier-body shape check — one implementation invoked
first satisfies both refusal-before-delegation and one-place-once.

## R15 — `gather` traces the `assesses` ref it actually read

Not the requested proposition. Non-`observes` declarations that cross
`run_value` are outside M1's traced set because no closure member declares
them — stated in the module's own docstring and carried into the results
record's "does not claim" section, not narrowed in code.

## R16 — S5's belief-rise arm is required and constructible

Observed datasets are minted at their content addresses so belief's
`certify` keys resolve against the snapshot's bases. The durable arm uses
the same construction.

## R17 — The family-adapters design's `import_bundle` signature listing is not edited

Frozen under cut 5; the widened `evidence` keyword introduced by this cut is
recorded here instead of editing that frozen listing.

## R18 — Two of the plan's minimum N2 sabotages were substituted

The intent-before-`_delete_locked` mutation is homed under G2c instead; G8's
arm flips the held verdict in `world/verify.py` instead. M13's arm binds
`decode_claim` as an import-time default rather than a `Claim._checked`
self-typing path. Every unit stays covered and all 20 arms are sound.

## R19 — A divergent `assesses` edge is a candidate finding, not admission refusal

Nothing refuses a divergent `assesses` edge at admission; M1 detects it. This
is banked as a candidate audit finding for a later cut, outside this cut's
frozen selection.
