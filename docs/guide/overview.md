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
  - ../designs/2026-09-12-composite-claims-design.md
  - ../designs/2026-09-12-estimand-typing-design.md
---

# Overview

## In brief

verifiably is an effort to improve our understanding of the world by building
it up from small, reproducible data analyses. Each analysis is a building block:
a precise question asked of real data, recorded completely enough that anyone
can run it again and get the same answer. Blocks are combined to map what is
known about a topic, to see whether the same pattern appears across independent
experiments, and to find where more work would teach us the most. Throughout,
the data lead: a claim gains weight only from analyses of data we actually have,
never because a paper, a person, or an AI said so.

- **Understanding is built from analyses, not assertions.** Each block is one
  analysis of one dataset, small enough to check.
- **Confidence comes from agreement across experiments.** One careful analysis
  can still mislead. The same pattern in several independent datasets, perhaps
  measured in different ways, is much harder to explain away.
- **Unverified claims are kept out.** A paper is recorded as what someone wrote,
  not as fact, and categories or labels invented by a person or an AI never
  become part of what a record means.
- **Every block can be traced and repeated.** Which data, which code, which
  settings, and what came out are all on the record, and nothing is quietly
  overwritten.
- **People and agents work on the same ground.** The same records, commands,
  and rules serve a researcher at a terminal and an agent running unattended.

## What it is for

The building blocks are useful in four ways:

- **Mapping the landscape** around a topic, system, question, or hypothesis:
  what has been analysed, on which data, with what result.
- **Aggregating analyses** into a sturdier picture than any single one gives,
  and from there towards more complex questions — a form of meta-analysis in
  which every contributing analysis can itself be checked.
- **Finding gaps**: where understanding is thin, where results disagree, and so
  where additional effort is most likely to pay off.
- **Giving humans and agents a common substrate** to work on, with the same
  guarantees whoever does the work.

## Why build from reproducible blocks

Even an unbiased analysis of one experiment can reach the wrong conclusion: a
quirk of one cohort, a batch effect, or plain chance. What earns plausibility is
seeing the same pattern emerge again and again, across experiments and across
kinds of data. For that agreement to mean anything, three things must hold for
every block:

- **We know exactly what it rests on**: the precise data, code, and settings.
- **It gives the same answer when run again from scratch**, so the result is a
  property of the data and the method, not of one machine on one day.
- **It is independent of the blocks it agrees with.** Two analyses of the same
  dataset are one observation, not two, and must be counted once.

Most of the machinery in this guide exists to make those three properties
checkable rather than assumed.

## What is kept out

The system is built to stop unverified material from quietly becoming part of
what we believe.

- **Literature as a source of truth.** A paper's statement is recorded as a
  *source assertion*: useful for deciding what to look at, never evidence by
  itself, because nothing in it can be re-run.
- **Subjective categories and labels.** Genes, diseases, and cell lines are
  named by the identifiers of established ontologies, not by names someone
  chose. Human-readable labels are computed for display and never stored or used
  to identify anything. A term enters the shared vocabulary only when separately
  built collections agree on it and some rule actually uses it. When two records
  might name the same thing, that is recorded as an attributed, graded claim,
  never an automatic merge.
- **Results nobody can repeat.** An analysis counts only after it has been run a
  second time from scratch and matched.
- **Quiet revisions.** Records are never edited in place. A changed analysis is
  a new version, and the earlier one and its results stay visible.
- **Double counting.** Analyses that share data are recognised as dependent and
  counted once.

## One building block, start to finish

The clearest way to meet the machinery is to follow one block through it. This
is a real run — the mm30 reproduction, repeated after each major change
([record §3 and §10](../designs/2026-09-05-mm30-reproduction.md#3-the-path)).
Terms in **bold** are the record types the rest of the guide explains.

1. **Write the question down precisely.** "Does disease stage raise PHF19
   expression in multiple myeloma?" is recorded as a **proposition** with
   explicit parts rather than as a sentence: the relationship (*affects*; the
   guide calls this the *operator*), the two things it relates (disease stage,
   and the protein PHF19), the direction asserted (*raises* rather than
   *lowers*; the *polarity*), and what kind of claim it is (a cause-and-effect
   claim rather than, say, a mere association; the *claim layer*). Because those
   parts are the claim's identity, rewording the sentence changes nothing.
2. **Get the data in hand.** The expression matrix (GEO series GSE179929,
   6,154,181 bytes) is copied from a local file into a store and fingerprinted
   by its hash. A **holdings observation** records that exactly these bytes were
   found there, and the **dataset** naming them becomes *held*. A dataset that
   only names a file nobody has is *declared*: a real record, but one that
   cannot support anything until an observation finds its bytes.
3. **Describe the analysis.** An **analysis spec** records which comparison is
   made (PHF19 in progressive disease against newly diagnosed disease), how the
   output is read as a verdict, and what counts as "the same result" when the
   analysis is repeated. It is recorded before the run, so the run can be checked
   against a fixed description. It is not a promise that cannot change: if the
   data show the analysis should be different, you record a new version. A new
   version cannot quietly drop an earlier attempt whose repeat failed on the
   record, so what was tried stays visible.
4. **Run it in a sealed box.** A Snakemake workflow runs inside a sandbox that
   sees only the captured code, software, and data, with no network. The **run**
   record keeps all of that and the outputs.
5. **Read off the result.** The spec's rule reads the output (a rank comparison,
   z = 1.16, p = 0.25) and records an **assessment** of the proposition:
   `inconclusive`.
6. **Check that it reproduces.** The analysis is run again from scratch in a
   fresh environment and the two runs are compared. This second run is a check,
   not a second piece of evidence: it must give the same result. The
   **verification** records that it did, in a clean environment — the only
   setting strong enough to let the assessment count.
7. **See what it adds up to.** Every checked, independent assessment of the
   proposition is combined into a **belief**. Here there is one, and it points
   neither way, so the answer is `NoBelief(no-directional-outcome)` — an honest
   "no evidence either way", never a fake zero. As blocks from other datasets
   accumulate, each checked and independent one adds its direction, and the
   answer always comes with a fingerprint of every record and rule it used.

```text
proposition ◀──assesses── assessment ──derived from──▶ run ──observes──▶ held dataset
     ▲                        ▲                          │
     │                        │                          └── run again and compared ──▶ verification
     │                   counts only when that verification is a clean-environment match
     │
 source assertion   (a paper's statement: recorded, never evidence by itself)
```

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

## Where the design is heading

The kernel today supports the path above well, and it is deliberately only part
of the goal. Three directions matter for reading the rest of the guide:

- **Weighing evidence, not just counting it.** Version 1 of the belief
  calculation gives every checked, independent assessment one vote. The
  quantities it would need to weigh them — what was estimated, on what scale,
  with what uncertainty — are already recorded as typed values. The weighting
  policy itself is the next design
  ([open question](open-questions.md#claims-and-belief)).
- **Comparing models.** A **composite** records a structure over several claims,
  such as a causal diagram, and reads each member's belief. That lets the
  evidence for one structure be set beside another's; how plausibility should be
  assigned across competing models is still open.
- **Starting from observation.** Today's path begins with a stated claim and an
  analysis written for it. The intended complement begins with the data:
  characterize datasets of different types from several angles using simple,
  well-grounded methods — statistical, information-theoretic, unbiased
  detectors — with as few human or AI decisions as possible in the early steps,
  and then weigh one model or several by what is seen. This is a direction, not
  yet a design ([open question](open-questions.md#foundations)).

Finding gaps is served above the kernel: the daily surface derives a work queue
from the records, and the autonomy layer's priority function will choose what
to work on next.

## The layers of the stack

The ecosystem is called **verifiably**. It has five layers, each its own
repository; this one, `beliefs`, is the middle. The earlier, single-repository
system was called Science, and the banked designs still use "Science" for the
whole stack; in this guide `science` names only the daily-surface layer.

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
