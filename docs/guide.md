# Guide

Type: guide; document types 1. This guide explains the beliefs model in plain
language for anyone who uses it, whether through `science` or as a Python library:
the six ideas the kernel rests on, claims and belief, runs and reproducibility,
worlds and change, and writes as a user meets them. It ends with one walk from held
data to a belief and a map of where each contract is specified. The contracts
themselves are in [records.md](records.md), [contracts.md](contracts.md) and
[writes.md](writes.md); [development.md](development.md) is for people changing
beliefs, and [glossary.md](glossary.md) defines the terms.

## Where beliefs sits

beliefs is the epistemic kernel of verifiably. It sits on
[nodes](https://github.com/verifiably/nodes), which stores records and relations,
and [atoms](https://github.com/verifiably/atoms), which applies each change to disk
completely or not at all. Above it, [science](https://github.com/verifiably/science)
is the command line and MCP server people and agents use day to day, and
[autonomy](https://github.com/verifiably/autonomy) runs those commands unattended.
Neither layer owns a record kind: everything they keep is a record written through
beliefs. If you want to do an analysis, start with `science`. Read on to understand
what its commands record and why. The
[verifiably overview](https://github.com/verifiably/docs/blob/main/overview.md)
gives the wider picture.

## The kernel in six ideas

1. **A corpus holds records that are not edited in place.** Each record has an
   identity computed from what it means. A change of meaning is a new record;
   `revise` covers only prose and a few named facets
   ([records.md](records.md#propositions-and-claims)).
2. **A profile defines what records may mean.** The Science base contract and the
   domain contracts a corpus activates compile into one profile, and every write
   is checked against it.
3. **A proposition is a typed claim.** Its operator, arguments, qualifiers,
   polarity and layer are its identity. Its wording is not.
4. **A run captures a complete execution.** The frozen plan, the held inputs, the
   code, the environment, the parameters and the outputs are all on the record.
5. **Only a reproduced assessment of held data bears on belief.** A paper's
   statement is recorded as a source assertion and never counts as evidence.
6. **History is additive.** Supersession and retraction are new records. Every
   change made through beliefs, a deletion included, is entered in the root's
   log, where audit can find it.

```text
held dataset ◀──observes── run ◀──produced_by── assessment ──assesses──▶ proposition ──▶ belief
source ◀──anchored_in── source assertion          (no route to belief)
contracts + corpus manifest ──▶ compiled profile, which checks every write above
```

## Claims and belief

A claim is a small structure, not a sentence. The **operator** (for example
*affects*) fixes how many arguments the claim takes and of what sort, which
qualifiers it allows, whether it has a direction, and which layers (causal,
statistical and so on) it may sit in. Two people who word the same claim
differently are recording one claim. A change to what is claimed is a new
proposition that supersedes the old one, so assessments of the old claim stay
attached to exactly what they assessed. The rules are in
[records.md](records.md#propositions-and-claims).

An **assessment** is the result of one run of a frozen analysis against one
proposition: `supported`, `refuted` or `inconclusive`, together with the typed
estimand and estimate. It counts toward belief only when its run observes held
data, every input of the run is held, and a verification that passed in a clean
environment admits it.

A **belief** is calculated when you ask for it, never stored. You name the policy
exactly (`PolicyBinding`). The shipped policy, `science.belief.v1`, returns a signed
count over the largest set of directional assessments that are certified independent
of one another, so two analyses of the same data count once; contrary independent
assessments pull the count toward zero but never past it. "No evidence" is its own
answer (`NoBelief`), never a zero. See [records.md](records.md#beliefs).

## Runs and reproducibility

An **analysis spec** freezes the plan before anything runs: the target proposition,
the estimand, the method, the input roles, the interpretation rule that turns
outputs into an outcome, and the equivalence rule that says what "the same result"
means. The run cannot override any of it.

A **run** records the recipe, the outputs and the facts of one execution. Its
inputs have roles: `observes` names held data and is the only role that can make an
assessment count; `reads` (literature, configuration, ontologies) never can. A
confined run sees only its captured code, environment and data, with no network.
Confinement needs bubblewrap and unprivileged user namespaces on the host.

To count, an analysis is run a second time and the two runs are compared under the
frozen rule. The **verification** records the comparison, its verdict and its scope.
The scope is derived from the evidence, never chosen: only a `passed` verification
at `clean-environment` scope admits an assessment. A dataset-production run records
how a dataset was made; its verification establishes that the dataset reproduces
but admits no assessment. See [records.md](records.md#specs-runs-and-assessments)
and [records.md](records.md#verifications).

## Worlds, identity and change

A **corpus** is one directory of records under a manifest that pins its contracts.
A **world** is every corpus its registry admits. A project is a view over part of
the world, not a separate collection.

Answers name what they read. A cross-corpus read through `open_world_view` is bound
to one published **epoch**, an immutable index over named corpus states, and a query
evaluated over it refuses once a covered corpus has moved past that epoch.
`evaluate_live_query` reads every live corpus the registry admits as it is now and
stamps its answer with the states it captured, for work queues and other reads that
cannot wait for an epoch.

Identity, address, name and location are separate. A record's identity is a digest
of its meaning-bearing fields; datasets and sources are addressed by their content
or external identifier; titles and file locations never enter identity. See
[records.md](records.md#identity).

Change is additive. **Supersession** links a replacement to what it replaces.
**Retraction** withdraws a record's standing without touching it, and standing is
computed from the retractions that target it. Each root keeps a hash-linked log of
its changes; `audit_log` checks that log against copies of its head held elsewhere,
so a truncation or rewrite is detectable while one such copy survives.

## Writes and publication

Every write is made by a writer bound to an **authority**: a write permit, which
names the record kinds and the classes of act allowed, and an actor. The actor
comes from how the writer was opened, never from the call. A write outside the
permit is refused before anything touches the disk. See
[writes.md](writes.md#authority-and-permits).

A simple change is one write, applied completely or not at all. Anything with
several steps (acquiring data, auditing, moving records, publishing) is an
**operation**: it writes an intent to the root's log first and closes with one
record of what was done, usually an act report, and whether it finished is read from
the log. `science` writes through a
**writer session**, whose ledger records every step so a retried command is
recognised rather than repeated. See [writes.md](writes.md#writer-sessions) and
[writes.md](writes.md#operations).

**Publishing** copies the records a saved view selects into a new corpus that
another world can admit whole. Each publish makes a new corpus; nothing is
updated in place. See [writes.md](writes.md#publication).

A refusal names its reason and leaves no effect. On a host whose kernel and volume
are not a configuration `atoms` certifies, every write fails with
`CapabilityUnavailable` as its cause. See [writes.md](writes.md#failure).

## From held data to a belief

This is the mm30 reproduction, condensed: one real multiple-myeloma claim recreated
through the kernel as a library. The driver is `python/tools/reproduction/`, one
module per step, and [development.md](development.md#recreating-the-mm30-corpus)
says how to run it.

1. **Open the roots.** `init_world_root`, `init_corpus_root` and `init_store_root`
   register a world, a corpus and a byte store under one `Authority`. The profile
   compiles the base contract, the shipped biology pack and the reproduction's own
   mm30 contract, and `adopt_manifest` pins all three in the corpus manifest.
2. **Type the claim.** `build_claim` types *disease stage affects PHF19*: the mm30
   contract's operator `affects-concept-molecular-entity`, a concept and a
   biology molecular entity as its arguments, layer causal, polarity positive.
   `project_claim` gives the stored form, and
   `writer.add(stored.proposition_node(...))` mints the proposition.
3. **Hold the data.** The holdings boundary's `write` copies the GEO series
   GSE179929 expression matrix (6,154,181 bytes) into the store and records a
   holdings observation of its digest. The dataset record is minted at its content
   address with an `empirical-observation` facet, and reads as held.
4. **Freeze the plan.** `freeze` turns a `SpecDraft` into a `FrozenSpec`: a typed
   estimand (PHF19 expression in progressive against newly diagnosed disease), a
   two-group rank comparison, the dataset as an `observes` input, and the
   interpretation and equivalence rules bound to their held implementations.
   `stored.analysis_spec_node` builds the record.
5. **Run it confined.** `execute_assessment_run` runs the Snakemake workflow in a
   sandbox. The outputs are `z = 1.16`, `p = 0.25`, `n = 51`, and the
   interpretation rule reads them as `inconclusive`. `build_assessment` derives the
   assessment from the run, and `stored.assessment_node` with `add` stores it.
6. **Reproduce it.** `replay` runs the analysis again from scratch, `derive_scope`
   finds `clean-environment`, and `build_verification` compares the two runs:
   `passed`. `publication_node` builds the verification record and `add` stores it.
7. **Ask for the belief.** `evaluate_over`, given the proposition, the profile and
   an exact `PolicyBinding` for `science.belief.v1`, gathers the admitted assessment
   and answers `NoBelief(no-directional-outcome)`: the one admitted assessment points
   neither way. A fresh process re-derives the same answer from the records on
   disk.

That answer is the scientific result, not a failure: the data in hand do not
separate the two stages. Another admitted, independent assessment that points one
way would move the answer.

## Where each contract is specified

| Topic | Reference |
|---|---|
| Corpus manifest and record kinds | [records.md](records.md#corpus), [records.md](records.md#record-kinds) |
| Relations and their enforced signatures | [records.md](records.md#relations) |
| Identity encoding and content addresses | [records.md](records.md#identity) |
| Claim typing | [records.md](records.md#propositions-and-claims) |
| Specs, runs, assessments, verifications | [records.md](records.md#specs-runs-and-assessments), [records.md](records.md#verifications) |
| Datasets, holdings and sources | [records.md](records.md#datasets-sources-and-holdings) |
| Belief answers | [records.md](records.md#beliefs) |
| The TypeScript mirror and parity fixtures | [records.md](records.md#encoding-and-parity) |
| Contract documents and profiles | [contracts.md](contracts.md#documents), [contracts.md](contracts.md#profiles) |
| Domain contracts and succession | [contracts.md](contracts.md#domain-contracts), [contracts.md](contracts.md#succession-and-retirement) |
| Permits, ordinary writes and sessions | [writes.md](writes.md#authority-and-permits), [writes.md](writes.md#an-ordinary-write), [writes.md](writes.md#writer-sessions) |
| Operations, publication and failures | [writes.md](writes.md#operations), [writes.md](writes.md#publication), [writes.md](writes.md#failure) |
