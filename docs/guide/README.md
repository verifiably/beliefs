---
title: verifiably contributor guide
status: living
created: 2026-08-08
updated: 2026-09-26
sources:
  - ../designs/2026-08-08-contributor-guide-design.md
  - ../designs/2026-08-03-redesign-adoption-ledger.md
  - ../designs/2026-08-02-epistemic-kernel-design.md
---

# verifiably contributor guide

verifiably aims to improve our understanding of the world by building it up from
small, reproducible data analyses, letting the data lead and keeping unverified
claims out. This repository, `beliefs`, is its kernel: it records claims, the
analyses that assess them, and the exact inputs behind every conclusion. This
guide is the short path into the system:
it explains the model by topic, in plain language first, and links to the design
documents whenever detail matters. The designs, and the frozen guarantee labels
in them, remain authoritative.

**New here? Start with the [overview](overview.md).** It introduces the big
picture, follows one real claim from data to belief, and names every concept the
topic pages build on.

## The kernel in six ideas

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

0. [Overview](overview.md) — the big picture, a worked example, and the key
   concepts.
1. [Foundations](foundations.md) — the invariant, the record kinds, and the
   ownership model.
2. [Claims and belief](claims-and-belief.md) — what propositions and belief
   values mean.
3. [Identity, world, and change](identity-world-and-change.md) — how records are
   named, found, corrected, and protected against silent removal.
4. [Computation and reproducibility](computation-and-reproducibility.md) — what a
   run captures and what replay proves.
5. [Writes, operations, and publication](writes-operations-and-publication.md) —
   permits, sessions, operations and their reports, and publishing a view.
6. [Contracts and adoption](contracts-and-adoption.md) — how the design becomes
   tested code, and how work is ordered.

Every topic page opens with **In brief**: a plain-language summary and its key
takeaways. Skimming those six openings is a fair ten-minute tour.

Use the [glossary](glossary.md) for quick definitions and the consolidated
[open questions](open-questions.md) for unresolved design edges.

## Status and authority

The guide deliberately does not copy a changing implementation tally. The
[adoption ledger's current-state summary](../designs/2026-08-03-redesign-adoption-ledger.md#current-state-2026-09-16)
is the sole authority for what is built and what remains to build, each
remainder with its named owner; the consolidated
[open questions](open-questions.md) page is the sole authority for what is
undecided. Each topic page states only the facts specific to its topic and links
to those two for the rest. If this guide disagrees with a source design, the
source wins.

One boundary is worth knowing before you read further. The kernel design
divided the redesign into seven sub-problems
([kernel §10](../designs/2026-08-02-epistemic-kernel-design.md#10-not-in-scope--the-remaining-six-sub-problems)).
Two sit mostly outside this repository:

- The **agentic surface** has an approved
  [user and autonomy layer design](../superpowers/specs/2026-08-29-user-and-autonomy-layer-design.md).
  Its `beliefs` parts — views and coordination records, the writer session, and
  local publication — are built here. Its daily surface lives in the `science`
  repository, where the command framework and the belief-path commands are built
  and the coordination commands are partly built. The `autonomy` layer is not
  started.
- **Salvage** — how the predecessor's pipelines, notes, and results are
  re-situated rather than migrated — has no design. The mm30 reproduction
  recreates one corpus through the ordinary typed path, which is the posture a
  salvage design would start from.

A question that sounds like "but how would anyone use this day to day" is
usually landing in the first of those, not in something the topic pages failed
to explain.

## Maintaining the guide

A commit that banks or amends a design, or changes implementation state in the
ledger, must update the affected guide pages and their `updated` dates in the
same commit. Use inline Markdown links rather than reference-style definitions
so `python/tools/check_guide.py` can inspect every local target and anchor.
Keep each page's **In brief** opening true: when a change alters what a newcomer
should take away, change the opening, not only the detail below it.

A commit that adds a conformance-cut results record also re-ranks the
[implementation roadmap](../plans/2026-08-29-implementation-roadmap.md) in
the same change: the discharged boundary leaves both the ledger's `Current
state` table and the roadmap, any newly named remainder enters both, and the
roadmap's `Ranked at` line advances to the new cut.
`test_the_roadmap_and_ledger_name_the_same_boundaries` fails until both are
done. An amendment to the roadmap's method re-ranks the same way without a
new cut: `Ranked at` stays at the newest record and the roadmap's `Method`
line names the amendment (its design §6, amended 2026-09-05). The same commit
adds the cut's row to the table in
[Contracts and adoption](contracts-and-adoption.md#what-each-cut-built).

The roadmap's [Boundary index](../plans/2026-08-29-implementation-roadmap.md#boundary-index)
maps each remaining boundary to its high-level task. At discharge, update that
task's current body and affected dependencies as well as the docs; keep dated
notes as history. `tasks ready` lists eligible work, while the roadmap retains
lane priority and sequencing authority.
