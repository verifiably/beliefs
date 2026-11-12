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
   domain contracts a corpus explicitly activates (such as the shipped `general`
   contract and a field contract) compile into one profile, and every write is
   checked against it.
3. **A proposition is a typed claim.** Its operator, the referents in its named
   roles, its qualifiers, form, polarity and layer are its identity. Its wording
   is not.
4. **A run captures a complete execution.** The frozen plan, the held inputs, the
   code, the environment, the parameters and the outputs are all on the record.
5. **Only an admitted assessment bears on belief.** Empirical, model and
   calibrated-model assessments have separate standing requirements and counting
   keys. A paper's statement is recorded as a source assertion and has no direct
   counting route.
6. **History is additive.** Supersession and retraction are new records. Every
   change made through beliefs, a deletion included, is entered in the root's
   log, where audit can find it.

```text
held dataset ◀──observes── run ◀──produced_by── assessment ──assesses──▶ proposition ──▶ belief
source ◀──anchored_in── source assertion          (no route to belief)
contracts + corpus manifest ──▶ compiled profile, which checks every write above
```

## Claims and belief

The kernel makes representational choices shared by every field: its claim
forms, layers, measurement structure and rules for counting evidence. The
[kernel commitments register](contracts.md#kernel-commitments-layer-0-register)
states what those choices preserve, their limits and their identity costs.
Activated contracts supply shared and field-specific vocabulary; their immutable
[assumptions registers](records.md#assumptions-registers) state what each
declaration collapses and licenses. The analysis spec names the register revisions
it relies on. Recording an assumption does not establish that it is appropriate.

A claim is a small structure, not a sentence. The **operator** (for example
`general/covaries-with`) names the roles the claim fills (such as *parties*), each
with one referent or a set of members; its instantiations say which sorts may
fill each role. The operator also fixes whether the claim has a direction,
whether it may be stated as a null (absent) effect, and which layers (causal,
statistical and so on) it may sit in; the qualifiers it allows are the
dimensions that name it. Two people who word the same claim
differently are recording one claim. A change to what is claimed is a new
proposition that supersedes the old one, so assessments of the old claim stay
attached to exactly what they assessed. The rules are in
[records.md](records.md#propositions-and-claims).

An **assessment** is the result of one run of a frozen analysis against one
proposition: `supported`, `refuted` or `inconclusive`, together with the typed
assessed target and optional named estimates. It counts toward belief only when
its run and inputs are held, its verification state admits it, and its frozen
dependencies remain eligible. Empirical assessments additionally require observed
data with empirical standing; model assessments name a held model procedure, and
calibrated-model assessments also depend on eligible calibrations. These routes
keep separate assessed-proposition keys; reproducing a model does not turn its
result into empirical corroboration. See the
[standing rules](records.md#declared-standing-at-write-boundaries).

A **belief** is calculated when you ask for it, never stored. You name the policy
exactly (`PolicyBinding`). The shipped policy, `science.belief.v1`, returns a signed
count over the largest set of directional assessments that are certified independent
of one another, so two analyses of the same data count once; contrary independent
assessments pull the count toward zero but never past it. "No evidence" is its own
answer (`NoBelief`), never a zero. See [records.md](records.md#beliefs).

## Runs and reproducibility

Measurement records describe what was measured and how: a procedure's complete
observables, a mapping between bearer sorts, a proxy model with its validity and
basis, or a classification rule. Domain contracts supply their measurement
vocabulary. Read-side helpers check binding aptness, dependency eligibility and
coordinate conversion, with separate exact comparison and rendered estimate
paths. Estimand authoring uses these measurements and aptness checks and freezes
its normative record dependencies into the spec and assessment. See
[measurement records](records.md#measurement-records) and
[coordinate convertibility](records.md#coordinate-convertibility).
Whole-target comparison first checks that variables correspond, then applies
conversion, observable, procedure, control, scope and standing checks. Its read-only
synthesis verdict carries any additional assumptions; it does not pool results.
See [assessed-target comparison](records.md#assessed-target-comparison).

An **analysis spec** freezes the plan before anything runs: the target proposition,
the estimand, the method, the input roles, the interpretation rule that turns
outputs into an outcome, and the equivalence rule that says what "the same result"
means. Each input declares its evidence mode; the spec also fixes standing, an
optional model and the estimator procedure bound to its interpretation rule. The run cannot override any of it.

A **run** records the recipe, the outputs and the facts of one execution. Its
inputs have roles: `observes` with mode `observation` can confer empirical
standing; `reads` (literature, configuration, ontologies) never does. The write
boundary separately validates declared model and calibrated-model routes,
including the held model procedure and current calibration evidence. A
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
recognised rather than repeated. A launched run opens a **run session** instead, under a
ceiling limited to corpus writes, runs and holdings, and one that refuses tree writes.
Its runs are confined only, and stage in scratch the kernel chooses and checks
before every launch.
See [writes.md](writes.md#writer-sessions) and
[writes.md](writes.md#operations).

**Publishing** copies the records a saved view selects into a new corpus that
another world can admit whole. Each publish makes a new corpus; nothing is
updated in place. See [writes.md](writes.md#publication).

A refusal names its reason and leaves no effect. On a host whose kernel and volume
are not a configuration `atoms` certifies, every write fails with
`CapabilityUnavailable` as its cause. See [writes.md](writes.md#failure).

## From held data to a belief

The PHF19 route is an **engineering demonstration** of one gene-level RNA
comparison through the kernel. It preserves the source cohort's paired inputs
while using the existing unpaired computation: independence, assay validity and
biological reuse remain unestablished. A verified replay establishes the tested
computation and recovery, not those scientific assumptions.

The driver is `python/tools/reproduction/phf19.py`;
[development.md](development.md#recreating-the-mm30-corpus) gives the command and
required pinned inputs. It creates a new question and target; the old
`protein:PHF19` causal proposition remains provenance. The five legacy contract
wrappers retain their exact bytes. The full legacy composite/cut route refuses
explicitly and remains owned by beliefs-6f039b.

1. **Check the sources.** An explicit declaration selects the original proposition,
   matrix and crosswalk, HGNC 2025-09-05 and human Ensembl 115/GRCh38.p14. All six
   byte pins, unique approved correspondence and source-row occurrence must agree.
   The later mapping establishes no historical annotation release or assay validity.
2. **Open and hold.** The base plus `general`, `biology` and corpus-local `mm30`
   profile is activated explicitly. A fresh world, corpus and store hold original
   sources, compressed references, the complete HGNC ID list and its derivation,
   mapping members, provenance and local lists. Ensembl membership is unconsulted;
   inspecting one annotation is not a full membership lookup.
3. **Type the question.** Shared `general/covaries-with` relates exactly the selected
   HGNC gene and disease-stage factor, polar/positive/statistical. Canonical party
   order does not select the measured response; the exact gene member does. The
   driver enforces this selected pair and the exact label rule, beyond the broader
   kernel admission of same-sort pairs or another rule with the same class sort.
4. **Freeze.** Public builders produce the RNA observable, the PD-versus-NDMM
   probability-of-superiority estimand, cohort applicability and dependency closure.
   The held assay has explicit unknown validation and a frozen
   `general/procedure-validity` assumption. It is conditional, never validation
   evidence. Canonical general/biology/mm30 registers and implementation digests
   remain recoverable with the target.
5. **Run and reproduce.** A work-local bundle runs confined and replays. The covered
   stats artifact exports `effect = U_PD / (n_PD * n_NDMM)`, with half-weighted ties,
   beside z/p/n diagnostics. The normal approximation has no tie correction or
   computed interval. Interpretation retains alpha .05 and uses the covered outcome
   file; a point estimate is not invented from output digests.
6. **Read the result.** Verification, admission, corpus audit and a separate fresh
   process must agree with stored spec/assessment/belief recovery. A separate
   terminal verdict detects a missing obligation or a step recording a defect
   despite exit zero. It assumes no fixed scientific result and no old cuts.

For several assessed targets, use `evaluation.claim_view` for one answer per key
and pairwise conversion/synthesis verdicts. The `evaluate_over` convenience refuses
multiple keys; it forwards the exact answer for one key. Neither aggregation nor a
successful demonstration certifies independence or biological interpretation.

## Where each contract is specified

| Topic | Reference |
|---|---|
| Corpus manifest and record kinds | [records.md](records.md#corpus), [records.md](records.md#record-kinds) |
| Relations and their enforced signatures | [records.md](records.md#relations) |
| Identity encoding and content addresses | [records.md](records.md#identity) |
| Claim typing | [records.md](records.md#propositions-and-claims) |
| Specs, runs, assessments, verifications | [records.md](records.md#specs-runs-and-assessments), [records.md](records.md#verifications) |
| Measurement records, aptness and coordinate conversion | [records.md](records.md#measurement-records), [records.md](records.md#coordinate-convertibility) |
| Datasets, holdings and sources | [records.md](records.md#datasets-sources-and-holdings) |
| Belief answers | [records.md](records.md#beliefs) |
| The TypeScript mirror and parity fixtures | [records.md](records.md#encoding-and-parity) |
| Contract documents and profiles | [contracts.md](contracts.md#documents), [contracts.md](contracts.md#profiles) |
| Domain contracts and succession | [contracts.md](contracts.md#domain-contracts), [contracts.md](contracts.md#succession-and-retirement) |
| Permits, ordinary writes and sessions | [writes.md](writes.md#authority-and-permits), [writes.md](writes.md#an-ordinary-write), [writes.md](writes.md#writer-sessions) |
| Operations, publication and failures | [writes.md](writes.md#operations), [writes.md](writes.md#publication), [writes.md](writes.md#failure) |
