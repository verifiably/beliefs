---
title: Science contributor guide
status: living
created: 2026-08-08
updated: 2026-09-03
sources:
  - ../designs/2026-08-08-contributor-guide-design.md
  - ../designs/2026-08-03-redesign-adoption-ledger.md
  - ../designs/2026-08-02-epistemic-kernel-design.md
---

# Science contributor guide

Science records scientific claims, the computations that assess them, and the
exact inputs needed to explain a belief. This guide is the short path into the
redesign. It explains the model by topic; the linked design documents and their
frozen guarantee identifiers remain authoritative.

## The system in six ideas

1. **A world holds immutable records.** Corpora contribute records to a world;
   content identity and explicit addresses keep references stable.
2. **A profile defines what records may mean.** The Science base contract and
   selected domain contracts compile into the runtime profile.
3. **A proposition is a typed claim.** Its operator, arguments, qualifiers,
   polarity, and layer determine semantic identity; prose does not.
4. **A run captures a complete execution.** Its predeclared spec, held inputs,
   code, environment, parameters, and outputs form a reproducible closure.
5. **A reproduced assessment may bear on belief.** Literature can orient and
   assert, but only eligible assessments of held observations enter empirical
   belief.
6. **History is additive.** Supersession, retraction, and mutation logs preserve
   prior records while changing what is active, standing, or demonstrably intact.

```text
held observations → run → assessment ──assesses──▶ typed proposition → belief
literature corpus → source assertion ────────────▶ typed proposition   (no belief edge)
contracts + corpus manifest → compiled profile ──governs every boundary above
```

## Read in this order

1. [Foundations](foundations.md) — the invariant, kernel, and ownership model.
2. [Claims and belief](claims-and-belief.md) — what propositions and belief
   values mean.
3. [Identity, world, and change](identity-world-and-change.md) — how records are
   named, found, corrected, and protected against silent removal.
4. [Computation and reproducibility](computation-and-reproducibility.md) — what a
   run captures and what replay proves.
5. [Contracts and adoption](contracts-and-adoption.md) — how the design becomes
   executable conformance work.

Use the [glossary](glossary.md) for quick definitions and the consolidated
[open questions](open-questions.md) for unresolved design edges.

## Status and authority

The guide deliberately does not copy a changing implementation tally. The
[adoption ledger's current-state summary](../designs/2026-08-03-redesign-adoption-ledger.md#current-state-2026-09-03)
is the sole authority for what is built and what remains to build, each
remainder with its named owner; the consolidated
[open questions](open-questions.md) page is the sole authority for what is
undecided. Each topic page below states only the facts specific to its topic
and links to those two for the rest. If this guide disagrees with a source
design, the source wins.

One boundary is worth knowing before you read further, because no page below
covers it. The redesign was cut into seven sub-problems. The *agentic surface*
now has an approved [user and autonomy layer design](../superpowers/specs/2026-08-29-user-and-autonomy-layer-design.md),
but its daily surface and autonomy sub-projects are not implemented. *Salvage*,
which asks how the predecessor's pipelines, notes, and results are re-situated
rather than migrated, still has no design. Everything the five topic pages
describe sits below those two, so a question that sounds like "but how would
anyone use this day to day" is usually landing in the gap rather than in
something the guide failed to explain.
([kernel §10](../designs/2026-08-02-epistemic-kernel-design.md#10-not-in-scope--the-remaining-six-sub-problems))

## Maintaining the guide

A commit that banks or amends a design, or changes implementation state in the
ledger, must update the affected guide pages and their `updated` dates in the
same commit. Use inline Markdown links rather than reference-style definitions
so `python/tools/check_guide.py` can inspect every local target.

A commit that adds a conformance-cut results record also re-ranks the
[implementation roadmap](../plans/2026-08-29-implementation-roadmap.md) in
the same change: the discharged boundary leaves both the ledger's `Current
state` table and the roadmap, any newly named remainder enters both, and the
roadmap's `Ranked at` line advances to the new cut.
`test_the_roadmap_and_ledger_name_the_same_boundaries` fails until both are
done.
