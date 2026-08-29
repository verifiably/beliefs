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

The kernel is implemented through conformance cut 12 and its remaining
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

1. **Five layers, one repository and one distribution each.** `atoms`,
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
the four layer names. `docs/guide/foundations.md`'s statement that views
and coordination "are not additional kernel kinds" remains true under §4.1
and is extended, with sub-project 1, to say where they live: corpus
records under a coordination contract, coordination-scoped, belief-inert.

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

World-addressing §3's tiers become a contract. **View** kinds — `project`,
`question`, `hypothesis`, `topic`, `theme` — are a stored world query plus a
label: "a project-scoped name over a world query," never a container.
**Coordination** kinds — `task`, `decision`, `note` — are attributed acts.
Neither tier is a world fact (world §3: "the world contains what is true or
done… not what is planned or organised"), so neither carries a world
address. Both are stored in a corpus and minted through the corpus-write
adapter like every other record — that is what makes them governed: they
carry provenance and enter the log and epochs — but they are declared by a
**coordination contract** compiled into `ProfileSpec`, not added to the
kernel's kinds, and they are never belief inputs. The guide's sentence that
views "are not additional kernel kinds" stays true.

**Identity is coordination-scoped, and a project's is opaque.** The
`project` record is the root of its own address space and the one
exemption from the qualified form: its address **is** its opaque durable
identity, minted the way a `corpus_id` is — fresh and act-authored at
creation — and carried by the record itself. It is never written into a
corpus manifest, because several projects may share a corpus and a project
may change which corpus holds it (world §6, which rejects coupling the two
identities). Every **other** view and coordination record is addressed by
`(project identity, local id)` per world §6.1 and W11 — never by a world
address, and never by a hash of its content. A project's name and query,
and every subordinate record's content, are content.

Editing a view's query or label mints a new **revision** — an immutable
record superseding the previous one under the same address — through a
**coordination revision family** that sub-project 1 designs. The existing
`supersede` is not reused: it operates on propositions only and takes
exactly one predecessor (`CorpusWriter.supersede`), and revisions need
neither restriction. The new family takes **one or more predecessor
tips**, which is what repair needs. The current revision of an address is
its **one standing tip**: the single revision no other revision supersedes.
Two corpora or replicas can mint sibling successors, so resolution
requires exactly one tip and otherwise returns `Refused(divergent-view)`
naming every tip; it never chooses by recency, arrival, or iteration
order, and the divergence is repaired by minting one revision that
supersedes all of them. W12 holds because a coordination reference binds
the project identity and the local id, both of which survive every rename
and every re-query; a reference to a view reads the current tip unless it
names a revision explicitly.

This is the roadmap's tier-3 `coordination-addressing` boundary, and the
above answers its question. The boundary moves to the roadmap's `mutation`
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

**Write classes are enforced by the kernel writer, not by the declaration.**
A declaration is metadata; a body could invoke a broader writer than it
declares. So every `beliefs` write entry point — `CorpusWriter.add`, the
family adapters, the run boundary, `publish` — takes a **write permit**: a
closed set of permitted kinds and act families, checked against the kind or
act actually emitted, with anything outside it `Refused(permit-exceeded)`
before any effect. A command's declared write class is additionally
checked against the session's permit before the body runs, so a mismatch
is a refusal at declaration time and, if the body lies, again at the act.
The interactive path runs under a full permit through the same mechanism,
so the permit is exercised every day and not only unattended.

**The permit is bound inside the writer endpoint, and no request carries
one.** A **launcher** — the interactive launcher a person starts, or
`autonomy` for a run — opens a `beliefs` **writer session**: it starts the
writer endpoint (the MCP server, or the CLI's service process) with the
permit and a fresh session identity fixed at launch. Requests to the
endpoint name a command and its inputs and nothing else; the endpoint
supplies the permit, and it sets every intent's `actor` itself from the
session — `actor` is a caller-supplied string in the kernel's intent
(act-report §3), so the endpoint is where it stops being caller-supplied.
`science` never sees, threads, or constructs a permit.

**The boundary is mechanical or the run is `unwired`.** "The actor imports
no writer" is an arrangement, not a boundary. The enforced boundary is:
the actor process — the agent harness running the command bodies — is
spawned by the launcher in a sandbox that **denies filesystem access to
every corpus root, the world root, and the baseline**, and is handed one
**private endpoint handle** (a launcher-owned socket plus a per-session
token that exists only in the actor's environment). A process that can
reach the corpora on disk can write around any endpoint, which is why the
denial is the boundary and the handle is only the channel. The endpoint
keeps a **session ledger** outside every corpus — each log entry it
appended, by corpus and entry digest — which is the evidence §7.1's
closing check compares against the chains. If the launcher cannot
establish the sandbox on this platform, an unattended run is `unwired`
from the moment it opens; it never runs on the arrangement alone. The
interactive path uses the same endpoint and ledger under a full permit;
its sandbox is a person's choice, because it is attended. Using `science`
as an in-process library gets a full permit by construction and is not an
autonomy configuration.

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
unchanged; and mint one immutable **`publication` record** in the new
corpus carrying `published_from = (world_id, the epoch's packaging
identity, the view's address, the view revision's identity)` and the full
selection it publishes. The corpus manifest is not touched: manifests are
a closed version that is never reminted (registry design §4), so
provenance lives in records, where it can be succeeded. A view's query
runs over the whole world, so a publication may draw from several source
corpora; which ones is carried by the cited epoch's coverage, and no single
source `corpus_id` is named. A selected record whose closure names an
unselected one — an assessment whose run closure names a dataset outside
the selection — makes the publish `Refused(closure-incomplete)` with the
missing identities listed; the user widens the view or drops the record.

**Constructing the corpus needs a primitive the root lifecycle does not
have.** `replicate_root` copies one root and stamps read-only before it
exposes payload; `fork_root` copies one source tree and ends in a
writability grant (root-lifecycle design §2–§4). Neither builds a corpus
from a selection over several roots. Sub-project 5 therefore specifies
**`publish_root`**, a populated-root publication command behind `atoms`'
own design gate, in the lifecycle's existing shape: a claim-only,
surface-excluded reservation at the destination directory; payload, chain
and genesis written durably under it from the selection; then the
read-only lifecycle stamp as the single step that makes the directory
serviceable, granting no writability. A retry finds a stamped corpus or an
unstamped reservation and resumes or abandons at the same split the fork
uses; it never guesses. Each attempt is its own operation with its own
act-report.

**The atomicity claim is exactly this wide.** For a local directory,
`publish_root`'s stamp is the reveal, and a published corpus is a valid
corpus or it does not exist. For a git remote, a Zenodo deposit, or an
inbox, the reveal is destination-specific and **not** atomic — an upload
can stop half-way — so the guarantee moves to the consumer: a corpus is
admitted (§6.3) only if its validation passes and its `publication` record
is present and well-formed, and anything less is refused whole, never
adopted in part. Publishing to a remote is `publish_root` locally followed
by a transport, and the transport's partial states are the recipient's to
refuse.

### 6.2 One operation, three destinations

A destination is a directory the user controls (private), a git remote or
Zenodo deposit whose content is the corpus (shared), or a community world's
inbox. **Every publish mints a fresh, immutable corpus** (§6.1); there is
no destination corpus that is advanced in place. The reason is
mechanical: a world adopts a corpus whole, and epoch capture enumerates
every stored record (`iter_stored`, no selection applied), so a shared
corpus that kept dropped records could never unpublish one. A fresh corpus
per revision contains exactly the current selection and nothing else.

Revisions are linked by their `publication` records: the new corpus's
record names `supersedes = (predecessor corpus_id, predecessor publication
record identity)`, and the source project holds a `publication`
coordination record binding `(view address, destination)` to the ordered
list of published corpus ids. A record dropped from the selection is
**neither retracted nor deleted** — retraction is legal only for the
readable inputs (correction lifecycle §4), which sources, datasets,
propositions and coordination records are not — it is simply absent from
the new corpus. What was already shared cannot be unshared: a recipient
who adopted the predecessor keeps it, and the successor's `supersedes` is
what lets them retire the predecessor through their registry's lifecycle
status. Two publishers racing on one view produce two corpora naming the
same predecessor; the recipient's tip rule (§4.1) refuses that as
`divergent-publication` until one revision supersedes both.

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

A run is opened by capturing the world head, every writable corpus's log
head, and the belief basis to a baseline outside any corpus the actor can
write. The run closes by re-reading the heads and the basis and classifying
`clean`, `quarantined`, or `unwired`; `unwired` — "a guard that cannot see
must not report clean" — is the disposition whenever the baseline, the log
evaluator, or a chain is unavailable.

**Membership is by chain interval, and the intent contract is unchanged.**
The kernel's `OperationIntent` is closed over `(kind, event_token, actor)`
with a closed operation-kind set (act-report §3), and this design does not
reinterpret or extend it: a run's member acts are exactly the log entries
between the opening heads and the closing heads of the corpora the run may
write, and every intent in that interval must carry the run's actor
identity — an entry in the interval under another actor is a `quarantined`
finding. Two conditions make the interval mean what it claims:

- **Every run mints a fresh actor identity.** The actor of a run is a
  run-unique identity, not the person or profile behind it, so an
  interactive write by the same person during the run carries a different
  actor and cannot pass the actor test.
- **The run's writer session is exclusive over its corpora.** Opening a
  run opens one `beliefs` writer session (§5.2) holding every corpus the
  run may write for the run's duration; no second session — interactive or
  another run — can be opened on those corpora until the run closes, and a
  write attempted around it is refused at the endpoint. Exclusivity is
  enforced by §5.2's boundary, not assumed: the actor cannot reach the
  corpora on disk, so its only writes are the session's, and the closing
  check compares the chain interval against the session ledger entry by
  entry — an entry in the interval the ledger did not append is a foreign
  write and the run is `quarantined`, whatever actor string it carries.
  Cross-process writers other than the actor (a person's editor, another
  launcher) are still bounded only by the single-writer deployment
  obligation the ledger records for the composition root (row 4); the
  ledger comparison is what turns a violation of it into a `quarantined`
  finding rather than a silent member.

Nothing can write inside the interval without being a member, which is
stronger than a per-act stamp. If concurrent runs on one corpus are ever
wanted, the remedy is a versioned additive parent-run member on the
intent, banked as an act-report design amendment; it is not taken now.

The predecessor's path gate is replaced by the write permit (§5.2). An
envelope **tier** is a permit: `report-only` ⊂ `coordination` ⊂ `mints` ⊂
`publishes`, with `publishes` never granted unattended. A tier is a
constant in `autonomy`, minted into the permit when the run opens; the
kernel writer enforces it at every act, so no project, profile, command, or
body can widen one.

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
| 1 | **Coordination and view kinds** — opaque project identity minting, `(project, local id)` addressing, the coordination revision family (one or more predecessor tips, the tip rule), W11, W12, W13's two-projects negative; the coordination contract in `beliefs`; the `foundations.md` extension | `beliefs` | none — it is the tier-3 answer and joins the `mutation` lane | now |
| 2 | **Command framework** — declaration schema, write classes, budgeted renderer, preamble, adapter generator with the Claude Code target, CLI and MCP over `beliefs` reads; the writer endpoint with its bound permit, endpoint-set actor and session ledger; the write permit on every `beliefs` write entry point | `science`, `beliefs` | 0 | now, against today's kernel reads |
| 3 | **Biology domain pack** — GO, HP, EFO, MONDO bindings; mm30's operator vocabulary | `beliefs/domains/biology` | the `domain-boundary` lane | with that lane |
| 4 | **The dogfood command set** — the dozen commands over a real world root; mm30 reproduced, not migrated, as the first corpus | `science` | 1, 2, 3; `run-confinement` and `workflow-surface` for a real assessment | after 2; grows as lanes land |
| 5 | **Publish** — `publish_root` behind `atoms`' design gate; the act and `publication` record in `beliefs`; transports, admission-side refusal and dry run in `science` | `atoms`, `beliefs`, `science` | 1; the `world-read` lane (view queries resolve through it) | after that lane |
| 6 | **Envelope** — the actor sandbox and private endpoint handle, baseline with log heads, tiers as permits, ledger-checked interval membership, dispositions, lease | `autonomy` | 2 | after 2 |
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
- **A shared destination corpus advanced by import.** A world adopts a
  corpus whole and epoch capture enumerates every stored record, so a
  dropped record could never be unpublished; and the destination would need
  a writer of its own, which is what the fresh-corpus model avoids.
- **Reusing the proposition `supersede` family for revisions.** It is
  proposition-only with one predecessor; repairing a divergent view needs
  a successor of several tips.
- **A permit threaded by the caller.** Any code in the writer's process can
  mint one; only a process boundary with filesystem denial makes the tier a
  fact rather than a convention.
