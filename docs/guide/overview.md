---
title: Overview
status: living
created: 2026-09-26
updated: 2026-09-26
sources:
  - ../designs/2026-08-02-epistemic-kernel-design.md
  - ../designs/2026-08-03-redesign-adoption-ledger.md
  - ../designs/2026-08-04-formal-model-and-claim-calculus-design.md
  - ../designs/2026-09-05-mm30-reproduction.md
  - ../superpowers/specs/2026-08-29-user-and-autonomy-layer-design.md
  - ../plans/2026-08-29-implementation-roadmap.md
---

# Overview

## In brief

Science is a system for keeping track of what we believe about the world, and
why. It records scientific claims, the data and analyses that bear on them, and
enough detail to run every analysis again. A belief is never typed in by hand:
it is calculated on request from analyses that were re-run, in a clean
environment, against data we actually have.

The five ideas to carry into the rest of the guide:

- **Belief is calculated, not stored.** Ask the same question of the same
  records and you get the same answer, together with a fingerprint of exactly
  what it was calculated from.
- **Only re-run analyses of data we hold can move a belief.** A paper is
  recorded as what someone wrote, not as a measurement, so it can guide work but
  never changes a belief by itself.
- **Nothing is overwritten.** A correction, a withdrawal, or a better version is
  a new record that points at the old one.
- **A claim has structure, not just wording.** Rephrasing a sentence does not
  change the claim; changing what it asserts makes a new one.
- **Bad input is refused, not repaired.** The system says "no" and why, rather
  than guessing what was meant.

## The problem it solves

A research notebook might say *"PHF19 rises as multiple myeloma progresses."*
That sentence cannot answer the questions a careful reader asks of it. Which data
showed it? Which analysis, with which settings? Would the analysis give the same
answer if run again tomorrow, on another machine? Has anyone since found a
problem with the data? Is *"PHF19 is associated with progression"* the same claim
or a different one?

Science's predecessor stored claims as prose and checked its policies after the
fact, so each of those answers depended on someone's memory. The redesign makes
each question answerable by construction: every claim has a precise form, every
analysis is captured completely enough to repeat, and every belief names the
exact inputs it was computed from.

## One claim, start to finish

The clearest way in is to follow a single claim through the system. This is a
real run — the mm30 reproduction, repeated after each major change
([record §3 and §10](../designs/2026-09-05-mm30-reproduction.md#3-the-path)).

1. **State the claim precisely.** "Disease stage affects PHF19 expression,
   positively" becomes a **proposition**: the operator `affects`, the arguments
   `concept:disease-stage` and `protein:PHF19`, a causal claim layer, and
   positive polarity. The proposition's identity is computed from that
   structure, so rewording its display text changes nothing.
2. **Hold the data.** The expression matrix (GEO series GSE179929, 6,154,181
   bytes) is copied from a local file into a store and hashed. A **holdings observation** records
   that exactly these bytes were found there, and the **dataset** that names
   those bytes becomes *held*. A dataset that only names a file nobody has is
   *declared*: a real record, but one that cannot support a belief until an
   observation finds its bytes.
3. **Fix the plan before running.** An **analysis spec** freezes what is being
   estimated (PHF19 in progressive disease compared with newly diagnosed
   disease), how the numeric result is turned into a verdict, and what "the same
   result" means when the analysis is repeated.
4. **Run it in a sealed box.** A Snakemake workflow runs inside a confined
   sandbox that sees only the captured code, environment, and inputs, with no
   network. The **run** record captures all of that plus the outputs.
5. **Read off the verdict.** The frozen interpretation rule reads the output
   (a rank comparison, z = 1.16, p = 0.25) and yields an **assessment** of the
   proposition: `inconclusive`.
6. **Run it again, from scratch.** A second run in a fresh environment is
   compared with the first under the frozen rule. The **verification** says the
   two agree, and that the comparison reached *clean-environment* scope, the
   only scope strong enough to count. Only now is the assessment admitted.
7. **Ask what we believe.** The belief calculation gathers every admitted
   assessment of the proposition. Here the only one has no direction, so the
   answer is `NoBelief(no-directional-outcome)` — an honest "no evidence either
   way", never a fake zero. A `supported` or `refuted` result would have produced
   a **belief** value together with a digest naming every record and rule it
   consulted.

```text
proposition ◀──assesses── assessment ──derived from──▶ run ──observes──▶ held dataset
     ▲                        ▲                          │
     │                        │                          └── replayed and compared ──▶ verification
     │                   admitted only when that verification is a clean-environment pass
     │
 source assertion   (a paper's statement: recorded, never a route to belief)
```

A paper saying that PHF19 drives progression can be recorded too, as a
**source assertion** about the same proposition. It helps decide what to test.
It does not move the belief, because nothing in it can be re-run.

## The main ideas, grouped

Each term links to the page that explains it; the [glossary](glossary.md) has
one-line definitions.

| Question | Records and ideas | Explained in |
|---|---|---|
| What do we claim? | **proposition** (a typed claim), **composite** (a structure over claims, such as a causal diagram), **source assertion** (what a paper said) | [Claims and belief](claims-and-belief.md) |
| What data do we have? | **dataset**, **holdings observation**, *held* versus *declared* | [Foundations](foundations.md#the-epistemic-invariant) |
| What did we do? | **analysis spec**, **run**, **verification**, **assessment** | [Computation and reproducibility](computation-and-reproducibility.md) |
| What do we conclude? | **belief**, calculated on request under a named policy | [Claims and belief](claims-and-belief.md#a-belief-is-a-reproducible-view) |
| How do we change our minds? | **supersession** (a better version), **retraction** (a withdrawal), both additive | [Identity, world, and change](identity-world-and-change.md#correction-is-additive) |
| Where do records live? | **corpus** (one collection), **world** (every admitted corpus), **epoch** (a frozen index of the world) | [Identity, world, and change](identity-world-and-change.md) |
| What gives records meaning? | **contracts** (base and domain), compiled into a **profile** | [Foundations](foundations.md#contracts-compile-into-profiles) |
| How does anything get written? | **permits**, **writer sessions**, **operations** and their **act reports** | [Writes, operations, and publication](writes-operations-and-publication.md) |
| How is work organised and shared? | **views** (saved queries: project, question, hypothesis), **coordination records** (task, decision, note), **publication** | [Foundations](foundations.md#views-and-coordination-are-governed-not-kernel), [Writes, operations, and publication](writes-operations-and-publication.md#publishing-a-view) |
| How do we know the code does what the designs say? | **guarantee rows**, **conformance cuts**, sabotage-tested checks | [Contracts and adoption](contracts-and-adoption.md) |

## Principles that recur

The same few rules appear on every page. Knowing them makes most decisions in
the designs predictable.

- **Derived, not stored.** Belief, a record's standing after retractions,
  whether a dataset is held, human-readable labels, and whether an operation
  finished are all computed when asked. Nothing stores a "current status" that
  could fall out of date.
- **Refuse, don't repair.** A sanctioned action either produces a valid result
  or returns a refusal naming the problem. It never guesses, downgrades, or
  quietly fixes input. A write that bypasses the sanctioned path is caught later
  by audit, which reports and changes nothing.
- **History is additive.** Records are immutable. Change is expressed by new
  records, and a tamper-evident log makes some removals detectable.
- **Structure over prose.** What a record means is carried by typed fields.
  Prose is for people and never enters identity.
- **Every answer names its inputs.** A belief names its policy and the exact
  records it read; a world query names the epoch or the corpus states it
  captured. There is no implicit "latest".
- **Inert by default.** Adding a new kind of record, or a new domain vocabulary,
  cannot accidentally open a new route into belief. There is exactly one route —
  a verified assessment of a claim — and the set of routes is closed.

## The layers of the stack

"Science" names the whole stack. This repository, `beliefs`, is its middle layer.

| Layer | Repository | What it does | State |
|---|---|---|---|
| Filesystem effects | `atoms` | Crash-safe, atomic writes to disk, with a record made before each change | Built and certified on a pinned kernel and volume |
| Storage | `nodes` | Generic storage of records and relations, with no scientific meaning | Built |
| Epistemic kernel | `beliefs` (here) | Record kinds, identity, runs, verification, belief, the world index, correction, the log, and publication | Built through conformance cut 41; the remote half of publish is being designed as cut 42 |
| Daily surface | `science` | The commands people and coding agents use, over the CLI and MCP | The command framework and the belief-path commands are built; the coordination commands are partly built |
| Autonomy | `autonomy` | Running the daily surface unattended, inside a fixed envelope | Designed, not started |

The [user and autonomy layer design](../superpowers/specs/2026-08-29-user-and-autonomy-layer-design.md)
specifies the top two layers. Its success criterion is a coding-agent session in
which `next` ranks a proposition, `run` executes a real analysis under
confinement, `verify` reaches clean-environment scope, and `assess` admits the
result to a computed belief — every step a governed record.

## How the project is built

The system is specified before it is built, and built in small pieces whose
guarantees are tested in a way that proves the tests can fail.

1. A **design** explains a boundary and ends in a table of **guarantee rows**
   with permanent labels such as G1 or W8a.
2. A **conformance cut** is frozen before any code for it exists. It selects
   the rows one slice of work will satisfy.
3. Each selected check is paired with a deliberate **sabotage** of the code. The
   check must fail when the sabotage is applied; a check that cannot fail does
   not count.
4. A **results record** discharges the cut, and the
   [adoption ledger](../designs/2026-08-03-redesign-adoption-ledger.md#current-state-2026-09-16)
   and the [implementation roadmap](../plans/2026-08-29-implementation-roadmap.md)
   are updated in the same change.

The ledger is the only authority for what is built; the
[open questions](open-questions.md) page is the only list of what is undecided.

## Where to go next

Read the topic pages in this order. Each opens with a plain-language summary,
so you can skim the openings first and return for detail.

1. [Foundations](foundations.md) — the rule at the centre, the record kinds, and
   who owns what.
2. [Claims and belief](claims-and-belief.md) — how claims are typed and how a
   belief is calculated.
3. [Identity, world, and change](identity-world-and-change.md) — how records are
   named, found, corrected, and protected against silent removal.
4. [Computation and reproducibility](computation-and-reproducibility.md) — what a
   run captures and what re-running it proves.
5. [Writes, operations, and publication](writes-operations-and-publication.md) —
   who may write, how multi-step actions are recorded, and how a view is shared.
6. [Contracts and adoption](contracts-and-adoption.md) — how designs become tested
   code, and how work is ordered.
