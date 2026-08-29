# User and autonomy layers — design

**Date:** 2026-08-29
**Status:** approved in session 2026-08-29; not yet delivered
**Scope:** the division of the stack above the epistemic kernel into a daily
surface and an autonomy layer, the rename that makes the division nameable,
and the sub-projects that build it. It selects no cut scope and freezes no
guarantee row. Each sub-project in §8 gets its own spec, plan and
implementation cycle; this document is the architecture they share.

**Inherits:** the adoption ledger's §0 (clean start; records reproduced,
never migrated) and §5 (repository decomposition: split a distribution on an
observed second consumer or a different constraint regime, never a projected
one); the world-addressing design's §2–§3 and §6.1 (one world; a project is
a view plus local coordination; coordination addresses); the domain
extension boundary's §2, §5 and §9 (domain content never enters the
substrate; a vocabulary binding is exact or absent; where packs live); the
corpus survey's rule 2.6 (vocabulary admission); the act-report design's §3
and §6 (the operation intent; sub-problem 6 excluded); the implementation
roadmap and its lanes (`../../plans/2026-08-29-implementation-roadmap.md`).

## 1. Problem

The kernel is implemented through conformance cut 11 and its remaining
boundaries are ranked. Nothing above it exists: no command, no CLI entry
point, no agent surface, no project, no way to publish, no autonomous run.
The kernel's own designs name this gap — the agentic surface is "the
corpus's largest structural deferral" (kernel §10), and the guide warns that
"how would anyone use this day to day" lands in it.

The predecessor, `proto-science`, is what the layer above the kernel looked
like when it grew in one repository without a division of concerns:

- **Surface size without a contract.** 40 commands, 51 CLI groups, 253 leaf
  commands, 921 option declarations, ~50 entity kinds. Shared semantics —
  output format, report-then-apply, write class — were framework concepts
  with no framework contract, so every command re-decided them
  (`proto-science` `docs/audits/framework-surface/framework-findings.md`).
- **Context budget as an afterthought.** One read-only command emitted
  21 MB; write commands echoed every pre-existing audit failure on each
  write; the task file truncated to its oldest entries
  (`docs/plans/2026-07-24-agent-context-budget-program-design.md` there).
- **Single-project by default, federation bolted on.** Three separate
  cross-project mechanisms (peers, a global registry, a commons overlay);
  projects minted their own kinds (`multiple-myeloma` registered thirteen;
  `meta` was declared independently in three manifests); commons promotion
  was "aspirational more than actual" and left topic namespaces split.
- **Policy worked around in configuration.** Sixty-entry lint deny-lists,
  SHA-keyed validation suppressions, fields nothing read.
- **Autonomy was an envelope without a loop.** The envelope — a baseline
  captured outside the repository, a default-deny path gate that no project
  could override, `clean`/`quarantined`/`unwired` dispositions — was sound;
  the loop had one fixed actor, no queue, no scoring, and no iteration.

The kernel's designs already fix the knowledge-model half of this (one
world; projects as views; admission by agreement and a reader; exact
ontology bindings). What remains to design is the layer that people and
agents actually use, without reopening any of those doors.

## 2. Decisions

Recorded as rulings so they are not re-derived.

1. **Four layers, one repository and one distribution each.** `atoms`,
   `nodes`, `beliefs` (today's kernel repository, renamed), `science` (the
   daily surface, new), `autonomy` (the envelope and orchestrator, new).
   Dependencies run one way: `autonomy → science → beliefs → nodes/atoms`.
   Each consumer pins the layer below exactly, as the kernel pins `atoms`.
2. **`autonomy` is split from `science` on the conformance package's
   grounds — code-lineage independence.** The envelope must not share a
   package with the surface it constrains; `proto-science` stated the
   reason: "an override is a hole that will be widened under pressure by
   the very agents it constrains."
3. **The first end-to-end success criterion is interactive dogfood on
   mm30** (§8): a coding-agent session over a `beliefs` world holding a
   reproduced mm30 corpus, running a real analysis to a computed belief.
4. **All daily-surface state is governed kernel content.** Views,
   coordination, session notes and autonomy trajectories are records in a
   corpus, minted through the same write adapter as everything else. The
   surface and the orchestrator own no store.
5. **Publishing mints a corpus.** Sharing a project is a kernel act that
   writes the view's selection into a fresh corpus at a destination;
   private, shared and community differ only in destination.
6. **The interactive surface is harness-neutral at source**, with generated
   adapters; the Claude Code adapter is first and the only one until a
   second harness is used.
7. **The kernel repository is renamed `beliefs`; the surface takes
   `science`.** The stack then reads as layer names — effects, graph,
   beliefs, science — and the name users say is the thing they open a
   session in.

## 3. Repositories and names

| layer | repository / import | distribution | owns |
|---|---|---|---|
| `atoms` | exists | exists | durable effects |
| `nodes` | exists | exists | entity/relation kernel |
| `beliefs` | the kernel repository, renamed | `verifiably-beliefs`, `@verifiably/beliefs` | the epistemic kernel, world, runs, log, holdings, correction, conformance cuts; `domains/` and `practices/`; coordination and view kinds; a thin kernel CLI |
| `science` | new | `verifiably-science` | commands and skills at source, generated adapters, MCP and CLI over `beliefs`, the derived work queue, publish glue |
| `autonomy` | new | `verifiably-autonomy` | envelope, orchestrator, behavioral profiles, `science.priority.v*` |

### 3.1 The rename

One commit in the kernel repository, made when the `science` repository is
created and **between lane merges** — never inside a lane's cut, since every
open lane would otherwise rebase across it.

Mechanical scope: the Python package `python/src/science` → `beliefs` and
every import; the TypeScript scope; `pyproject`/`package.json` names; the
README and the living guide; the repository name.

**Identifiers are not renamed.** `contracts/science/CONTRACT.yaml` carries
`contract: science` and the rule identities `science.identity.v1` and
`science.belief.v1` in its bytes; editing them re-identifies every claim
and is a contract succession under N1's rule. Those strings are the names
of rules, not of a repository, and they stay. The directory
`contracts/science/` stays with them, so the path the contract's own
documentation cites remains true.

**Banked designs are not edited.** They use "Science" as the system's name,
which now names the stack rather than the kernel repository. The adoption
ledger gains one dated ruling in §5 saying so; the guide's glossary gains
the four layer names.

### 3.2 What is not a repository

- **The commons** — a world that adopts published corpora (§6). Hosting
  helpers are a `science` module until a second consumer appears.
- **The meta-science corpus** — a corpus managed by the stack (ledger §5),
  and the first place successor priority functions are compared (§7.3).
- **Harness adapters** — generated output of `science`, committed there
  under `adapters/`, never edited.
- **Domain and practice packs** — directories under `beliefs/domains/` and
  `beliefs/practices/` (domain §9), promoted to distributions only on an
  observed second consumer.

## 4. The knowledge model at the user layer

The kernel owns what a thing is. The user layer adds nothing to identity or
belief; three rules follow.

### 4.1 Views and coordination are governed kinds minted in `beliefs`

World-addressing §3's tiers become contracts. **View** kinds — `project`,
`question`, `hypothesis`, `topic`, `theme` — are a stored, content-addressed
world query plus a label: "a project-scoped name over a world query," never
a container. **Coordination** kinds — `task`, `decision`, `note` — are
attributed acts addressed by `(project identity, local id)` per W11/W12. A
project's identity is opaque and minted the way a `corpus_id` is, so
renaming a project breaks no coordination reference (W12).

This is the roadmap's tier-3 `coordination-addressing` boundary, and this
design answers its question: coordination records **are** minted through the
corpus-write adapter, like every other record, so they carry provenance and
enter the log and epochs. The boundary moves to the roadmap's `mutation`
lane at the next re-rank. No kind is minted anywhere else — `science`
cannot declare one, and a kind a command wants is a request to `beliefs`.

### 4.2 A project is a view, and a user has one world

A user's collection is one world root with N corpora. "Which project am I
in" is a selected `project` record, and every command reads the world
through that view's query. Records carry no project field; a question
belongs to a project because the project's query selects it, so a boundary
moves by editing a query, not by moving files. Overlap is free — one
hypothesis under two projects — and W13's two-projects negative stays a
negative, since the two projects share the entity and not an identity.

### 4.3 Vocabulary and ontology posture is the banked one

A field enters the base profile only by rule 2.6 — agreement and exercise
across separately evolved corpora, and a reader. A field that fails 2.6 and
that a domain reader wants goes to a domain pack under `beliefs/domains/`,
the only place a vocabulary can be bound. Ontology terms are `term`
referents under the ontology's own identifier with an exact release
binding (domain §5). The mm30 dogfood needs the biology pack — GO, HP, EFO
and MONDO bindings and mm30's operator vocabulary from the typing exercise —
and that pack is the `domain-boundary` lane's first.

The predecessor's escape hatches — project-local manifests, configuration
deny-lists, keyed suppressions, inert fields — do not exist here. A record
that will not type is typing work; a check that fires is a finding, never
a suppression entry.

### 4.4 The work queue is derived, never stored

"What next" is a query over the world through the current view — unassessed
propositions with holdings in hand, stale verifications, open tasks —
computed at read time. Nothing persists a ranking; a persisted ranking is
the predecessor's `graph add` written and wiped by the next build. What is
persisted is a *choice*: a coordination record saying which candidate was
taken and why (§7.2).

## 5. The daily surface — `science`

### 5.1 A command is a declaration and a body

Each command carries a declaration — name, one-line purpose, inputs, the
kernel reads it performs, its **write class**, and its **output budget** —
and a harness-neutral prompt body that includes one shared preamble. Write
classes are closed: `read-only`, `coordination` (mints coordination kinds
only), `mints:<kinds>` (named kernel kinds), `publishes`. The declaration
is the framework contract the predecessor lacked: format, report-then-apply
and write class are decided once, in the schema, and a command that does
not fit the schema does not ship.

The dogfood set is deliberately small — on the order of a dozen: `status`,
`next`, `project`, `question`, `hypothesis`, `claim`, `dataset`, `run`,
`verify`, `assess`, `task`, `decide`, `publish`. A new command names the
world query or the act it exists for, or it is not a command.

### 5.2 Every write is a kernel act; the surface owns no files

A command reads the world through the current view, or requests an act
from `beliefs` and receives a record or `Refused(reason)`. The surface
renders both. It never repairs, retries with altered inputs, or writes
around a refusal. This is the entire guardrail story on the interactive
path, and it is the one autonomy inherits (§7): there is no second write
path to gate.

### 5.3 Output budget is enforced by the renderer

Every result passes through one budgeted renderer: a declared cap in bytes,
deterministic truncation with a visible marker and a paging handle back
into the world, and the write-audit rule — a write returns its own record
and nothing else. The predecessor's 21 MB read and its audit echo were
untestable habits; the renderer makes each a test.

### 5.4 One source, generated adapters

`science/commands/` and `science/skills/` are the source. `science adapters
build` emits the Claude Code plugin — commands, skills, manifest — under
`adapters/claude-code/`, committed as a generated tree and never edited.
Other harnesses are further targets, added when used. The same declarations
drive the MCP tool list and the CLI, so the three surfaces cannot drift.

### 5.5 Testing

Each command has a fixture world and a reader test that must be able to
fail, in N2's harness shape — the assertion, a source mutation that
falsifies it, and the test that catches it. The renderer has budget tests
including the write-audit rule. Adapter generation is checked by diffing
the committed tree against a fresh build.

## 6. Publish and the commons

### 6.1 `publish` is a kernel act

`publish(view, destination)` in `beliefs`: resolve the view's query at the
current epoch; mint a fresh corpus at the destination — own `corpus_id`,
manifest, genesis; write the selected records with their identities
unchanged; stamp the manifest `published_from = (source corpus_id, source
epoch identity, view record identity)`. A selected record whose closure
names an unselected one — an assessment whose run closure names a dataset
outside the selection — makes the publish `Refused(closure-incomplete)`
with the missing identities listed; the user widens the view or drops the
record. A published corpus is a valid corpus or it does not exist.

### 6.2 One operation, three destinations

A destination is a directory the user controls (private), a git remote or
Zenodo deposit whose content is the corpus (shared), or a community world's
inbox. Republishing a view is a second `publish` from a later epoch to the
same destination: the destination corpus advances by explicit import
through the mutation log, never by overwrite, so a recipient's replica sees
an ordinary history.

### 6.3 A commons is a world

Consuming a published corpus is `World.admit` of a replica — cut 8's
arrival act — so any world can adopt any publication, and a community
commons is a world whose operator adopts many. Coreference between a local
record and an adopted one is the existing graded `coreference-attestation`.
Nothing promotes, overlays, or rewrites; the predecessor's peers, registry
and overlay collapse into adopt, attest, query.

### 6.4 What `science` adds

Hosting glue only: laying a corpus out as a git repository or Zenodo
deposit; discovering published corpora through a manifest index a community
world publishes as an ordinary epoch artifact; and a `publish` command with
a dry run that shows the selection and closure before the act.

### 6.5 The reciprocal gap, named

A recipient who reproduces a published assessment produces a verification
in their own corpus; returning it to the publisher is the publisher
adopting the recipient's publication. Symmetric, and unbuilt until a second
installation exists — the log design's observer-distribution question.

## 7. Autonomy — `autonomy`

A seam-level statement; the loop and the priority function get their own
spec after the interactive dogfood exists (§8, item 7).

### 7.1 The envelope, not overridable by construction

A run is opened by capturing the world head and the belief basis to a
baseline outside any corpus the actor can write. Every act inside the run
carries the run identity as its operation intent (act-report §3). The run
closes by re-reading the basis and classifying `clean`, `quarantined`, or
`unwired`; `unwired` — "a guard that cannot see must not report clean" — is
the disposition whenever the baseline, the log evaluator, or the intent
chain is unavailable.

The predecessor's path gate is replaced by something stronger. The actor
has only `science`'s commands, so what it can write is exactly the write
classes those commands declare, and an envelope **tier** is a set of
permitted write classes: `report-only` ⊂ `coordination` ⊂ `mints` ⊂
`publishes`, with `publishes` never granted unattended. A tier is a
constant in `autonomy`; no project, profile, or command can widen one.

### 7.2 The loop is a sampler over the derived queue

Each iteration reads the queue through the run's view (§4.4), scores the
candidates, samples one, runs its command under the envelope, and records
the choice and its outcome as coordination records — so the trajectory is
in the world. A **behavioral profile** is a declared, content-identified
parameterization: tier, budget (iterations, tokens, wall time), the scoring
function's identity and weights, sampling temperature, stop rules. A run is
attributable to a profile identity the way a belief is to a policy binding.

### 7.3 The priority function is versioned like a belief policy

`science.priority.v1` scores a candidate by expected information gain
under feasibility: widely asserted but unassessed propositions with
holdings in hand rank highest; assessed and stable ones lowest; disputed
ones with a runnable closure between. It reads only kernel-derived
quantities — admission state, holdings, divergence, verification
staleness — and is one function behind one identity, because it is the
piece that improves with measurement. Its first version is simple by
intent; the meta-science corpus is where successors are compared.

### 7.4 The seam: commands as tools, nothing else

`autonomy` has no private kernel access. An orchestrator that needs a
capability the surface lacks asks for a command, which then exists for
people too. Kill switch and liveness are `autonomy`'s: a run holds a lease;
a dead orchestrator leaves its run `unwired`; the audit-liveness half of
kernel sub-problem 6 — audits actually running on a cadence — is a standing
profile, not special code.

## 8. Sub-projects and order

Each row is its own spec → plan → implementation cycle. Order is by
dependency; rows run beside the roadmap's kernel lanes where the last
column says so.

| # | sub-project | repository | depends on | starts |
|---|---|---|---|---|
| 0 | **Rename and seed** — `science` → `beliefs`; ledger §5 ruling; glossary; create `science` and `autonomy` with a README pointing here | kernel, new | nothing | now, between lane merges |
| 1 | **Coordination and view kinds** — project identity minting, `(project, local id)` addressing, the view-query record, W11, W12, W13's two-projects negative; a coordination contract in `beliefs` | `beliefs` | none — it is the tier-3 answer and joins the `mutation` lane | now |
| 2 | **Command framework** — declaration schema, write classes, budgeted renderer, preamble, adapter generator with the Claude Code target, CLI and MCP over `beliefs` reads | `science` | 0 | now, against today's kernel reads |
| 3 | **Biology domain pack** — GO, HP, EFO, MONDO bindings; mm30's operator vocabulary | `beliefs/domains/biology` | the `domain-boundary` lane | with that lane |
| 4 | **The dogfood command set** — the dozen commands over a real world root; mm30 reproduced, not migrated, as the first corpus | `science` | 1, 2, 3; `run-confinement` and `workflow-surface` for a real assessment | after 2; grows as lanes land |
| 5 | **Publish** — the act in `beliefs`; hosting glue and dry run in `science` | both | 1; the `world-read` lane (view queries resolve through it) | after that lane |
| 6 | **Envelope** — baseline, tiers as write-class sets, dispositions, lease | `autonomy` | 2 | after 2 |
| 7 | **Loop and `science.priority.v1`** — its own spec | `autonomy` | 4, 6 | last |

**Success criterion** — item 4 complete: a coding-agent session over a
`beliefs` world holding a reproduced mm30 corpus, where `next` ranks a
proposition, `run` executes a real Snakemake analysis under confinement,
`verify` reaches `clean-environment`, and `assess` admits the result to a
computed belief — every step a governed record.

**What this adds to the ledger.** Nothing new: items 1 and 3 already carry
ids (`coordination-addressing`, `domain-boundary`). Item 1's answer moves
`coordination-addressing` from tier 3 to the `mutation` lane at the next
re-rank, and the coordination-record bullet leaves `open-questions.md` in
the same commit.

## 9. Verification posture shared by the three repositories

- Every check must be able to fail — N2's harness shape for readers,
  renderers, and generators alike.
- No generated artifact in a source tree; generated trees are committed and
  diffed, never edited.
- No per-project suppression surface: a firing check is a finding.
- An `unwired` disposition anywhere a guard cannot see — in the interactive
  path as much as the autonomous one.

## 10. Alternatives rejected

- **One workbench repository with module boundaries.** Cheapest to start,
  and ledger §5's default; rejected because the envelope would share a
  package with the surface it constrains, and because the predecessor's
  integration hub is exactly what one such repository becomes.
- **Five or six repositories by concern** (prompts, adapters, commons host,
  coordination pack each apart). Every change becomes a multi-repository
  version dance before any piece has a second consumer.
- **The surface keeping its own store** for tasks, views and notes. Fast,
  but sharing a project would ship two stores and views would be
  unattested; and the split variant (views governed, coordination local)
  makes trajectories invisible to the world.
- **A read-only export bundle as the sharing unit.** Recreates the
  predecessor's overlay asymmetry: recipients can read but not build on it.
- **A replica of the whole corpus as the sharing unit.** No selection;
  everything private travels.
- **Claude Code only.** Fastest for the dogfood, but the predecessor
  reached generated adapters by accident and paid for the retrofit.
- **Keeping `science` for the kernel and naming the surface something
  else.** Would reproduce the predecessor's `science_tool` / `science_model`
  confusion, with the name people say attached to the layer they never
  touch.
- **Renaming the rule identities with the repository.** A contract
  succession that re-identifies every claim, for no gain.
