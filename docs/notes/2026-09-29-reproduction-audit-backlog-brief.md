# Repeatable reproduction and audit evidence

## Problem

The mm30 driver should reproduce its recorded measurements with explicit inputs and
a checkable verdict. Goal: `beliefs-cde4d9`. Restore the missing cut-31 transition
check first; establish a recipe's prerequisites before implementing it. Retained
audit reports need a concrete consumer before changing the measured artifact.

## Current behaviour and evidence

Inspected main at `b5225b2` on 2026-09-29; no recreation was run in this pass.

- `python/tools/reproduction/rederive.py::prior_state` reads the cut-22 archive.
  `cut31_corpus_state` appears only in `state.py` documentation within the driver;
  no committed test reads it. The reproduction record §11.5 and cut-32 results
  §3.3 describe the missing measurement: exactly `profile-mismatch: base`, zero
  records read. `audit_corpus` still returns early on that base mismatch.
- `justfile` has no reproduction recipe. `world.main` refuses an existing world;
  `paths.PRIOR` requires a sibling cut-22 archive. Later steps include `compose`
  and `read` followed by a separate `read --again` process. `close`, `rederive`
  and `read` can record a defect and still return zero, so a successful shell
  loop alone would not prove the measurement passed.
- `close.py` calls the bare evaluator. `audit_operation.py::audit`, introduced
  at `12a17b6`, appends an intent and publishes a report under the root lock.
  Cut-38 design decisions 2 and 12 deliberately limit that operation to one
  corpus and preserve the reproduction's read-only close step.
- `audit.py::audit_world` already returns a bound result with findings grouped
  by corpus. Persisting that result is the unresolved extension. Relocation
  (`634a3e9`) leaves the reproduction fixture in place and creates a separate
  research world; it is not part of recreating the fixture.

## Constraints

Preserve frozen cuts, archived predecessor corpora and historical measurements.
The adoption ledger and roadmap remain the status and delivery authorities.
Use the certified host for live capability-dependent measurements; do not infer
those results from unit tests. Driver scripts remain exercise instruments under
reproduction design §8. A small recipe is the intended ceiling.

Read-only evaluators gain no writes. A retained audit changes corpus and chain
state. A world report requires choosing root-local reports under a shared token
or corpus-qualified entries, with the corresponding act-report amendment.
No existing open research task found in this checkout owns the recipe inventory.

## Alternatives

1. Restore the transition check and inventory a minimal recipe with an explicit
   final verdict. This is the current lean: it addresses observed repeatability gaps.
2. Continue using the documented manual sequence. It avoids new orchestration,
   but leaves order and final assertions to each operator.
3. Expand reproduction to retain audit reports and design world report storage.
   Defer until a named consumer needs those artifacts; the existing evaluator
   already supplies read-only findings.

## Unanswered questions

- What inputs, invocation order and final assertions make the current driver
  reproducible by one recipe? The agent executing `beliefs-b9c3ea` answers.
- Is the preserved cut-31 archive available and readable on the execution host?
  The implementer of `beliefs-0c1cc9` verifies it and reports missing input
  explicitly; its availability was not tested during this pass.
- Which consumer needs reports retained in the corpus or across a world?
  A future reproduction requirement or multi-corpus consumer supplies the wake
  condition. This pass found no such requirement in the inspected sources.

## Proposed decomposition

- `beliefs-0c1cc9`: scoped, P3/s/mid/direct; implement the repeatable transition
  measurement with explicit missing-input and wrong-verdict failures.
- `beliefs-b9c3ea`: P3/s/mid/direct research; inventory current recreation inputs,
  invocations and verdict. Completion updates this brief and writes a finding
  note on `beliefs-9e0b42` in the same commit.
- `beliefs-9e0b42`: briefed; remains an idea until that inventory settles scope.
- `beliefs-b36632`: shelved until a reproduction measurement requires retained
  audit reports and accepts their mutation of the measured artifact.
- `beliefs-9d2b68`: shelved until a named consumer needs persisted world audit
  reports beyond the current read-only result.

The detached-runner exit-code idea `beliefs-7be4f1` was inspected but left
untouched: it concerns conformance process supervision, outside this cluster.
