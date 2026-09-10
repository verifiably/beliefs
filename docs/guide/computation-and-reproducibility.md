---
title: Computation and reproducibility
status: living
created: 2026-08-08
updated: 2026-09-09
sources:
  - ../designs/2026-08-02-epistemic-kernel-design.md
  - ../designs/2026-08-02-world-addressing-design.md
  - ../designs/2026-08-02-computation-reproducibility-design.md
  - ../designs/2026-08-03-normative-contract-design.md
  - ../designs/2026-08-03-tamper-evident-log-design.md
  - ../designs/2026-08-03-redesign-adoption-ledger.md
  - ../designs/2026-08-11-act-report-design.md
  - ../designs/2026-08-11-conformance-cut-3.md
  - ../designs/2026-08-26-world-index-intent-boundary-design.md
  - ../designs/2026-08-27-conformance-cut-11.md
  - ../designs/2026-08-29-successor-admission-design.md
  - ../designs/2026-08-30-conformance-cut-13.md
  - ../designs/2026-08-30-run-confinement-design.md
  - ../designs/2026-09-06-verification-publication-design.md
---

# Computation and reproducibility

## TL;DR

A run is an immutable, complete execution closure; reproduction compares two
runs under a frozen equivalence rule, and only a passing clean-environment
verification can admit an assessment to empirical belief.

## Why it matters

A command, lockfile, output checksum, or claim that code “runs again” is not
enough to reproduce a scientific computation. The redesign records what was
planned, the exact executable closure, what happened, and how two occurrences
were compared. It also separates the ability to attempt a replay from a
successful verification and from the later epistemic use of its result.

## Key ideas

### The analysis spec freezes the scientific plan

An assessment run begins from an immutable analysis spec that names the target
proposition, estimand, interpretation rule, inputs, parameter contract,
nondeterminism contract, and equivalence rule. Those fields are projected into
the run recipe and cannot be overridden at execution time.

Freezing a spec before execution is preregistration only when chronology is
independently observable. A content hash proves content identity, not when the
content existed. A boundary-mediated `intent` entry and an external anchor can
strengthen that chronology, within the mutation log's observer limits.

### A run has three complete parts

| Part | Records |
|---|---|
| Execution recipe | Run shape; spec identity where applicable; code bundle, environment artifact manifest, and workflow identities; structural invocation; role-partitioned inputs; parameters; nondeterminism, boundary, and rule bindings. |
| Result | A boundary-built manifest of the declared output bytes. |
| Occurrence | A random event token, actor/time/host facts, execution trace, realized seeds, and boundary receipt. |

If one part is missing, the object is not a run. Recipe identity answers
“same declared computation”; occurrence identity distinguishes two executions
of that recipe.

### Capture includes the executable closure

The code bundle includes the actual tracked and untracked files used by the
execution, and execution is confined to that captured closure. The environment
is a manifest of held artifacts, not merely a dependency name or lockfile.
Inputs are content-addressed and role-typed; outputs are admitted from the
boundary's observed manifest rather than trusted from an authored declaration.

These constraints are meant to fail early. An uncaptured dependency,
unavailable input, recipe/spec mismatch, or output outside the declared boundary
refuses run construction instead of producing a lower-quality run.

### One run kind has two shapes

An **assessment run** is bound to an analysis spec, observes empirical inputs,
and may produce one assessment through the assessment constructor. The
assessment copies its target, estimand, and interpretation from the frozen
spec; an authored assessment record is invalid.

A **dataset-production run** transforms inputs and produces one dataset. It has
no proposition, analysis spec, or assessment, and its v1 equivalence rule is
bitwise content equality. This captures lineage without turning every data
preparation step into evidence about a proposition.

### Workflows are imported, not redrawn

The workflow definition is itself a held artifact. Science imports a minimal
normalized DAG from executable workflow content and binds invocation to named
steps. The initial design needs one normalized schema and one Snakemake adapter,
not a general plugin framework. A diagram or manually transcribed DAG is useful
documentation but not execution authority.

### Replay, verification, and belief are different decisions

- **Replay eligibility** asks whether this environment holds enough closure to
  attempt the recipe.
- **Verification** records the comparison of two completed runs under the
  equivalence rule frozen in the spec.
- **Epistemic admission** asks whether a passing verification has the required
  scope to make an assessment eligible for belief.

Verification scope is derived from evidence, not selected by the author:
`same-environment`, `clean-environment`, `independent-implementation`, or
`not-certified`. Clean-environment scope requires equal recipes plus qualifying
fresh-environment and confinement receipts for both runs. Independent
implementation is valuable corroboration of a result but is not a second
observation and does not create another assessment.

The immutable verification record names the ordered run pair, equivalence-rule
identity, comparison report, scope derivation, scope, and verdict. Only
`clean-environment` plus `passed` can admit an assessment under the kernel.
Dataset-production verification establishes reproducibility of a derived
dataset but gates no belief-bearing assessment.

## How it connects

- [Foundations](foundations.md) supplies held artifacts, role-typed relations,
  immutable records, and the closed assessment route.
- [Claims and belief](claims-and-belief.md) consumes admitted assessments and
  never treats replay or verification as an evidence weight.
- [Identity, world, and change](identity-world-and-change.md) distinguishes
  recipe identity from occurrence identity and supplies mutation-log anchors.
- [Contracts and adoption](contracts-and-adoption.md) maps the R1–R23 guarantees
  to the adoption ledger and executable conformance surface.

## Current state

The run boundary is implemented: analysis-spec freezing and closure
construction, content-addressed workflow definitions, semantic wildcard job
keys, planning-derived job and target sets, per-family seed obligations,
multi-rule and multi-target execution, dataset production, replay,
verification-as-value, and the act-report layer's completion reading, running
as real subprocess executions over held fixtures.
Runs publish durably with their closure preimage and typed identity bridge, and
general intent qualification reads every boundary operation through one
three-shape reducer. `admit_spec_successor` now composes that qualification with
active, coherent failing-verification evidence under one hold, closing G4 at
persistence width. Assessment admission is gated on the verification reading
rather than on a claim that code ran.

**The boundary is confined, and `clean-environment` is reachable** (cut 13,
[run confinement](../designs/2026-08-30-run-confinement-design.md)). A run
under `boundary-policy/confined-v1` executes inside a fresh namespaced
materialization of a digest-verified runtime closure, observed by the
boundary from its own `/proc` before the engine starts; the receipt names the
capabilities the launch actually observed. `derive_scope` reaches
`clean-environment` only through a qualifying pair of such receipts —
`boundary-policy/minimal-v1`'s scratch root stays `same-environment` at best.
Cut 15 composes separate planning and execution launch attestations and closes
R2, R16, R20, and R21; `qualifies()` reads the execution launch. Verification
publication is implemented and discharged at cut 21
([design](../designs/2026-09-06-verification-publication-design.md),
[results](../plans/2026-09-06-conformance-cut-21-results.md)): a published
verification carries its comparison report, so the audit and the import
recompute its scope from the corpus rather than from an in-memory value. What is not built here is owned
elsewhere — the mutation log's event-level order (L8); and the
preimage-backed classification of a removed verification (L13) — and listed
with those owners in the
[adoption ledger's current-state summary](../designs/2026-08-03-redesign-adoption-ledger.md#current-state-2026-09-10).

## Open edges

See [Computation and reproducibility](open-questions.md#computation-and-reproducibility)
for the unresolved questions about artifact lifetime, multi-product workflows,
publishing a belief-input snapshot, and where the scope-derivation rule is
versioned.

## References

- [Run closure and guarantees R1–R23](../designs/2026-08-02-computation-reproducibility-design.md#10-guarantees-and-how-each-is-tested)
- [Normative rule binding](../designs/2026-08-03-normative-contract-design.md#6-rule-binding--one-decision-both-halves)
- [Kernel reproduction gate and G5](../designs/2026-08-02-epistemic-kernel-design.md#3-reproduction-is-an-eligibility-gate-not-a-ceiling)
- [World identity bases for runs](../designs/2026-08-02-world-addressing-design.md#42-the-basis-ruled-per-kind)
- [Mutation registration and intent entries](../designs/2026-08-03-tamper-evident-log-design.md#3-the-chain)
- [Scope derivation and the admission join, confined](../designs/2026-08-30-run-confinement-design.md#7-scope-derivation-and-the-admission-join-replaypy-verifypy)
