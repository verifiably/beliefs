---
title: Writes, operations, and publication
status: living
created: 2026-09-26
updated: 2026-09-26
sources:
  - ../designs/2026-09-04-write-permits-design.md
  - ../designs/2026-09-05-writer-session-design.md
  - ../designs/2026-09-09-session-routes-design.md
  - ../superpowers/specs/2026-09-24-session-selection-ledger-design.md
  - ../designs/2026-08-11-act-report-design.md
  - ../superpowers/specs/2026-09-22-act-report-remainder-design.md
  - ../designs/2026-09-03-world-changing-families-design.md
  - ../designs/2026-08-10-verified-holdings-record-design.md
  - ../designs/2026-08-24-world-index-holdings-design.md
  - ../superpowers/specs/2026-09-19-url-retrieval-design.md
  - ../designs/2026-09-20-conformance-cut-35.md
  - ../superpowers/specs/2026-08-29-user-and-autonomy-layer-design.md
  - ../designs/2026-09-22-publication-design.md
  - ../superpowers/specs/2026-09-22-publication-records-design.md
  - ../superpowers/specs/2026-09-23-publish-act-local-design.md
  - ../designs/2026-08-03-redesign-adoption-ledger.md
---

# Writes, operations, and publication

## In brief

Every change to a corpus goes through a small number of sanctioned doors. A
writer can only write what its **permit** allows, and who is writing comes from
how the writer was opened, never from the caller. Simple changes are single
writes. Anything with several steps — fetching data, auditing, moving a record,
publishing — is an **operation**: it announces itself in the log before it
starts and ends with exactly one record of what happened. **Publishing** copies
the records a saved query selects into a fresh, sealed corpus that someone else
can adopt whole.

- **No write without a permit.** The permit names which record kinds and which
  classes of act a writer may perform; anything else is refused before it
  touches the disk.
- **An operation opens with an intent and closes with one record.** Whether it
  finished is read from the log, never stored as a flag.
- **The record of an operation is inert.** An act report says what was done and
  what was found; it never feeds a belief.
- **A session keeps its own ledger.** An attended session writes down every step
  as it happens, so a retried command is recognised rather than repeated.
- **A publication is a new corpus, not an update.** Each publish mints a fresh,
  immutable corpus; later revisions point back to earlier ones.

## Why it matters

The epistemic rules on the other pages only hold if nothing can go around them.
A write path that trusted the caller's claim about who it is, or a multi-step
action that could half-finish silently, would let a record into the world
without the evidence the rules require. This page describes the doors every
write goes through and the evidence each one leaves behind.

## Key ideas

### Every write carries a bound authority

An **authority** is the frozen pair of a write permit and an actor. It is bound
once, where a writer is constructed — `open_corpus`, `open_world`, an operation
port, a holdings act context, a lifecycle act — and never supplied per call.
Every write entry point checks its requirement against that authority before any
effect and reads the actor from it, so no caller can name an actor of its own
(E1–E8, cut 17).

A **write permit** is two closed sets: the record kinds a holder may emit and the
**act families** it may perform — `corpus-write`, `run`, `holdings`, `registry`,
`epoch`, `lifecycle`, and `publish`. Going beyond it raises `PermitExceeded`
with nothing written. The daily surface, `science`, compiles each command's
declared requirement into a permit request and never holds a permit itself
([write-permits design](../designs/2026-09-04-write-permits-design.md)).

### Writer sessions: an attended session and its ledger

A **writer session** is how the daily surface writes. It opens over one corpus
root with a fresh session identity, which fixes the actor as `session:<id>`, and
keeps a **session ledger**: an append-then-fsync file whose every line is durable
before its call returns. Each command invocation first records a **claim**, so a
retried invocation is recognised and deduplicated instead of written twice. The
invocation then receives a **scoped writer** whose permit is exactly what that
command declared, not the session's ceiling. Reconciliation reads the ledger
against the corpus's chain to settle anything a crash left open (J1–J11, cut 19;
[writer-session design](../designs/2026-09-05-writer-session-design.md)).

The session also carries ledgered routes for runs and holdings
([session routes](../designs/2026-09-09-session-routes-design.md)) and records
which project the user has selected, pinned to the project revision it resolved
([session selection](../superpowers/specs/2026-09-24-session-selection-ledger-design.md)).

### Ordinary writes and operations

An **ordinary write** — `add`, `supersede`, `revise`, `retract`, `delete`, and
the coordination mint and revision — is one registered transaction under the
root's lock. It needs no further ceremony because the log's registration already
records it.

An **operation** is an action with several member acts. It follows one shape:

1. append an **operation intent** to the log — kind, a fresh event token, and the
   actor — before any member act runs;
2. perform the member acts;
3. close through exactly **one terminal record**: the `run` if one was minted,
   otherwise an **act report**.

Two kinds vary the shape: `corpus-write` is closed by its own committed
registration and writes no report, and `publish` opens through its own domain
intent, `science.publish-intent.v1`, rather than a plain operation intent.

The intent blocks nothing. It exists so completion can be read back: an
operation is *unfinished* (its intent is unmatched), *indeterminate* (the log
cannot yet say), or *closed*. That reading is derived per root and never stored
([act-report design](../designs/2026-08-11-act-report-design.md)).

An **act report** is inert by type. Each entry records one member act's
subject, its explicit instrument inputs, and its outcome in that act's own
vocabulary, and can be cited as *(report, entry index)*. A look that found
nothing is recorded here too, so "we checked and it was absent" is evidence
rather than silence.

### The nine operation kinds

| Kind | What it does | Closes through |
|---|---|---|
| `corpus-write` | A session's ordinary write, recorded as an operation | the write's own committed registration (no report, by design) |
| `run-attempt` | Executes a run request | the `run`, or an act report when no run was minted |
| `import` | Explicitly imports records from another corpus, validating every derivation first | an act report |
| `move` | Moves one record to another root, destination first | an act report in each root |
| `consolidate` | Folds a duplicate copy of a record into the kept one, reconciling their correction histories | an act report in each root |
| `acquisition` | Fetches resources by URL, hashes them, optionally stores them, and mints the dataset when every look matches | an act report, in the same transaction as the dataset |
| `audit` | Runs the read-only corpus audit and publishes its findings | an act report, one entry per finding |
| `re-check` | Looks again at held locations and records fresh holdings observations | an act report, one entry per location |
| `publish` | Publishes a view to a destination (below) | the publication binding and an act report |

`move` and `consolidate` are specified by the
[world-changing families design](../designs/2026-09-03-world-changing-families-design.md),
`audit` and `re-check` by the
[act-report remainder](../superpowers/specs/2026-09-22-act-report-remainder-design.md),
and `acquisition` by the
[URL-retrieval design](../superpowers/specs/2026-09-19-url-retrieval-design.md).
`delete` is deliberately an ordinary write, not an operation.

### Acquiring data

Data becomes held through a **holdings observation**: an act dereferences one
location, hashes what it finds, and records `found` with the digest (or, for a
store location, `absent`). An observation is never expired by age; a later
observation supersedes it
([holdings design](../designs/2026-08-10-verified-holdings-record-design.md)).

The `acquisition` operation does this for URLs. For each resource it performs a
**look** — a network fetch under a recorded discipline of timeout, byte ceiling,
redirect bound, and a pinned connection to the validated address — and,
optionally, stores the bytes in the session's store. When every look found
what was expected, it mints the dataset and its closing report in one
transaction; otherwise the report closes the operation alone. The dataset's
empirical-observation
facet names that report, so the evidence of how the data arrived travels with it
([cut 35](../designs/2026-09-20-conformance-cut-35.md)).

### Publishing a view

A **view** is a saved query over the world, such as a project or a question.
`publish(view, destination)` shares what a view selects
([layer design §6](../superpowers/specs/2026-08-29-user-and-autonomy-layer-design.md#6-publish-and-the-commons);
[publication rows Y1–Y10](../designs/2026-09-22-publication-design.md)):

1. **Select and check, writing nothing.** The query is evaluated at the caller's
   current epoch. The publish is refused before any write if the selection is
   empty or incomplete, or if a selected record depends on one left out — an
   assessment whose run used an unselected dataset, or a composite without all
   its member propositions (`closure-incomplete`).
2. **Record the plan.** The publish intent is appended under the root's lock.
   Afterwards a selection snapshot and a request are written create-only under
   the operations root, so a retry always publishes exactly the same selection.
3. **Stage, export, reveal.** The selected records are copied unchanged into a
   private staging corpus with a **`publication`** marker record carrying the
   provenance — which world, epoch, view, and view revision it came from. The
   corpus is exported and revealed at `<destination>/<corpus_id>`.
4. **Bind.** The source project gains a **`publication-binding`** revision
   linking the view and destination to the new corpus, and one act report
   records every step in order.

Every publish mints a **fresh, immutable corpus**; a destination accumulates the
chain of revisions, each marker naming the one it supersedes. Dropping a record
from a view does not unpublish it from copies already shared. A recipient admits
a published corpus only through `admit_publication`, which refuses anything
without exactly one consistent marker. A crashed publish resumes by
reinvocation (`resume_publish`), and `pending_publishes` lists unfinished ones.

The two publication kinds are coordination records, not kernel kinds: they never
enter a world-index map or a belief's inputs.

## How it connects

- [Foundations](foundations.md) states the refusal/audit boundary these doors
  enforce and introduces views and coordination records.
- [Identity, world, and change](identity-world-and-change.md) supplies the
  mutation log that intents and registrations are appended to, and the two ways a
  view is read — at an epoch or live.
- [Computation and reproducibility](computation-and-reproducibility.md) explains
  the run that closes a `run-attempt`.
- [Contracts and adoption](contracts-and-adoption.md) lists the cuts that built
  each door.

## Current state

- **Built:** write permits on every write entry point (cut 17); the writer
  session and its ledger (cut 19), its routes, and session selection; `move` and
  `consolidate` (cut 16); managed deletion (cut 18); URL acquisition (cut 35);
  `audit` and `re-check` (cut 38); the publication records and publish intent
  (cut 39); the publish act for a local destination and marker-required
  arrival (cut 40).
- **Being designed:** publishing to a remote destination — the transport seam,
  the remote reveal and its orphans, and the recipient's
  `divergent-publication` refusal — as conformance cut 42, not yet frozen.
- **Not built:** cross-root publication of a dataset's provenance reference and
  its acquiring report (T7's cross-root case).

The [adoption ledger's current-state summary](../designs/2026-08-03-redesign-adoption-ledger.md#current-state-2026-09-16)
is the authority for what remains and who owns it.

## Open edges

See [Writes, operations, and publication](open-questions.md#writes-operations-and-publication)
for the act report's residue (cross-root publication, compaction, a world-scope
audit) and the question of who *may* write.

## References

- [Write permits and E1–E8](../designs/2026-09-04-write-permits-design.md#7-guarantees)
- [Writer session and J1–J11](../designs/2026-09-05-writer-session-design.md#7-guarantees)
- [Act reports, operation intents and T1–T8](../designs/2026-08-11-act-report-design.md)
- [What the act-report design left open](../designs/2026-08-11-act-report-design.md#6-what-this-unblocks-and-what-stays-open)
- [The publication table, Y1–Y10](../designs/2026-09-22-publication-design.md)
- [The publish act, local destination](../superpowers/specs/2026-09-23-publish-act-local-design.md)
- [Publish and the commons](../superpowers/specs/2026-08-29-user-and-autonomy-layer-design.md#6-publish-and-the-commons)
