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
   beliefs, science, autonomy — and the name users say is the thing they
   open a session in.

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
the five layer names. `docs/guide/foundations.md`'s statement that views
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
Two more, **`publication`** and **`publication-binding`** (§6.2), join
them by a **versioned amendment of the coordination contract** that
sub-project 5 banks before any publish runs, since sub-project 1 mints
the contract first and a pinned contract can authorize only the kinds it
declares. They are distinct kinds, not one kind in two roles: a
`publication` is the **marker** minted in a published corpus (provenance,
selection, `supersedes`, attribution), and a `publication-binding` is the
source project's record binding a view and destination to what it has
published. Recipient admission requires a `publication`; a binding is
never admissible as one.
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
tips**, which is what repair needs, and has two admission rules, by how
the revision is minted:

- **The general rule, for revisions minted by the ordinary write path**
  — every revision of a view kind (`project`, `question`, `hypothesis`,
  `topic`, `theme`) or of an ordinary coordination kind (`task`,
  `decision`, `note`), which is one registered transaction under the
  root's per-root operation lock and carries no operation intent (the
  operation-kind set is closed and names none for these): every named
  predecessor must be a standing tip **at commit**, judged under that
  lock. A `project` revision changes its name or query, never its
  identity (§4.1 above), and is admitted by this same rule. Within one
  root the lock serializes revisions, so no sibling can arise there —
  the lock being in-process, that holds across processes only under the
  single-writer deployment obligation the ledger records for the
  composition root (row 4), the same dependence §7.1 names; siblings
  otherwise arise across corpora or replicas, and the tip rule below
  handles them.
- **The intent-position rule, for revisions minted inside a registered
  operation** — today exactly one, the `publication-binding` revision of
  a `publish` (§6.1 step 8), whose intent kind is the operation's own:
  every named predecessor must have been a standing tip at the position
  in the source root's log where the operation's intent was appended,
  which is a pure function of the chain prefix ending at that intent and
  provable by anyone holding the chain; a predecessor already superseded
  at that position refuses (`Refused(predecessor-not-standing)`). A
  predecessor superseded *between* intent and commit is therefore still
  valid, and the result is two standing tips — the sibling state below,
  not a violation of it. A future operation that mints revisions inherits
  this rule with its own intent kind, by amendment.

The current revision of an address is its **one standing tip**: the
single revision no other revision supersedes.
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
through that view's query. Two membership rules, one per tier, and they
must not be confused:

- **World facts belong to views by query, and may overlap.** A
  proposition, dataset, run or assessment carries no project field; it is
  in a project because the project's query selects it, so a boundary moves
  by editing a query, not by moving files. One proposition under two
  projects is ordinary, and W13's two-projects negative stays a negative,
  since the two projects share the entity and not an identity.
- **Views and coordination belong to projects by address.** A `question`,
  `hypothesis`, `task` or `decision` is `(project identity, local id)`
  (§4.1) and belongs to exactly that project. A second project that wants
  the same hypothesis does not share the record: it mints its own view
  record whose query is the same — sharing a view *definition* is reuse,
  not co-ownership (world §3) — and the two views select the same world
  facts.

So "one hypothesis under two projects" means two project-scoped view
records over one world query, never one project-scoped record under two
addresses.

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

**Constructing the corpus composes lifecycle commands that exist; no new
`atoms` primitive is needed.** The sequence is:

0. **Read the tips and append the intent under one lock, then write the
   request, before any side effect.** Under the source root's per-root
   operation lock, held across both actions so no binding revision can
   commit between them from this process — the lock is in-process
   (`OperationLock`), so across processes the guarantee rests on the
   single-writer deployment obligation the ledger records for the
   composition root (row 4), exactly as §7.1's exclusivity does; a second
   launcher on the same source root is that obligation's violation, and
   the retry's re-derivation from the chain prefix (below) is what turns
   an interleaved commit into a refusal rather than a wrong tip set:
   read the standing tips of the source project's
   `publication-binding` (below), then append the publish's
   `OperationIntent(kind = publish, event_token, actor)` to the source
   root's log, as every boundary operation already does (act-report §3).
   The frozen tips are thereby **exactly** the standing set at the
   intent's log position — the set §4.1's intent-position rule will judge
   — and, being a pure function of the chain prefix ending at that
   intent, they are recomputable by anyone: a retry re-derives them from
   the prefix and refuses a request whose cached tips disagree
   (`Refused(request-corrupt)`). Then a **publish request record** is
   written at the canonical, event-token-keyed path
   `<operations root>/publish/<event_token>/request.v1` — the operations
   root being a durable, launcher-owned directory outside every corpus
   that the actor cannot reach — by the **durable create-only write**
   defined below. It **freezes every identity-bearing input** of the
   publish, so a retry can never select differently: the **request
   identity** `(view address, view revision identity, destination)`; the
   **source epoch's packaging identity**, which every retry reopens
   explicitly with `open_epoch` rather than reading `current`; the
   **destination pins** (below); the **staging `world_id`**, derived
   deterministically as a domain-separated digest of `(publish,
   event_token)` so that no retry can mint a second one; and the
   canonical paths derived from the token — `…/<event_token>/staging`
   (staging root), `…/<event_token>/world` (staging world), and, for a
   remote destination, `…/<event_token>/export` (export root). The
   `corpus_id` is **not** in the request: `adopt_manifest` mints it
   itself and refuses a second manifest (`ManifestAlreadyPresent`), so
   the manifest is its durable record and a retry recovers it with
   `load_manifest(staging_root)` (step 1). Nothing about a publish is
   minted or placed anywhere
   else. Recovery therefore enumerates `<operations root>/publish/*/
   request.v1`, matches each to an unfulfilled `publish` intent by event
   token, and resumes that one; several crashed publishes cannot be
   confused. A request record is never rewritten, so nothing it freezes
   is ever minted twice for one token. **An intent with no request record
   is left `unfinished` and never resumed**: the intent carries only
   `(kind, event_token, actor)`, so the view, destination and request
   identity cannot be reconstructed from it — and since no side effect
   occurred, the honest rule is to begin a new attempt under a new token.

   **The destination pins.** A destination corpus carries exactly one
   `CorpusPins = (science_contract, domains)`, and a selection may span
   several source corpora. The pins are derived at step 0 from the
   manifests of every source corpus that contributes a selected record,
   at the frozen epoch: `science_contract` must be identical across them,
   and `domains` is their union, refused if any domain name is pinned to
   two values — `Refused(pins-disagree)` naming the corpora and the
   field. The destination also mints one record the sources did not
   select: the `publication` record, whose governing contract is the
   **coordination contract** of §4.1 — at the version that declares
   `publication`, the amendment §4.1 assigns to sub-project 5; an earlier
   version's pin authorizes nothing. That contract's pin is therefore
   required in the derived `domains`, taken from the source corpus that
   holds the publishing project's own records, and must agree with any
   other source that pins it — a destination whose pins do not authorize
   `publication` cannot be written, so this is checked at step 0 and not
   discovered at step 2. An **empty selection is refused**
   (`Refused(empty-selection)`): it has no contributing manifest to derive
   from, and a corpus holding only a `publication` record publishes
   nothing. The derived pins are frozen in the request; they are what
   step 1's `adopt_manifest` receives, and a retry never re-derives them.

   **The expected `publication` record is fixed at step 0, to the byte.**
   Its semantic payload is determined by what the request freezes:
   `published_from` from the world, the frozen epoch and the view
   revision; the selection list from that epoch; and `supersedes` from
   the **predecessor tips**, which are two projections of one reading and
   are frozen separately because they live in two identity domains. The
   standing tips of the source project's `publication-binding` for
   `(view address, destination)` (§6.2) are the set read under the lock
   above — every unsuperseded revision at the intent's position, several
   if siblings stand; none for a first publication.
   From them the request freezes **`binding_tips`**, the binding revision
   identities themselves, which step 8's binding revision supersedes; and
   **`marker_tips`**, the `(corpus_id, publication marker identity)` pair
   each of those revisions binds (§6.2's binding shape), which the
   marker's `supersedes` carries. Neither is ever derived from the other
   at retry time. Payload alone does not
   fix bytes: the record model assigns a random `uid` by default
   (`nodes` `Node.uid`), and Science's node factories leave it to that
   default. So the `publication` record is minted by a **deterministic
   factory** that takes the request and the matching intent and nothing
   else: its slug and its `uid` are domain-separated digests of
   `(publication, event_token)`, its facets are the frozen payload
   **plus the intent's `actor` and `event_token`** — the marker is a
   coordination record and therefore an attributed act (§4.1), so its
   attribution is in its closed shape, not implied by the log it happens
   to sit in — its relations are the selection, and it reads no clock and
   draws no randomness. Every byte of the expected record — and therefore
   its semantic identity, which later publications cite in `supersedes` —
   is then a function of the request record **and the matching intent**,
   never of the request alone; step 2 compares the marker it finds
   against exactly those bytes, and a recipient can recompute the slug
   and `uid` from the marker's own `event_token` and refuse a marker
   whose identity does not match its attribution. The factory is
   sub-project 5's, beside the contract amendment that declares the kind.

   **The durable create-only write.** The rules-store idempotency
   discipline runs under the world lock (log-verification design §3.1);
   the operations root and the artifact sibling (step 5) are outside
   every corpus and have no such boundary, so both use one mechanism
   defined here: write the bytes to a temporary name in the target
   directory, `fsync` it, publish it at the final name with a
   **create-only** link (`O_EXCL` semantics — fails if the name exists),
   and `fsync` the directory. Partial bytes therefore never appear at the
   final name. A retry that finds the final name compares bytes —
   identical is success, different is a collision and refuses — and
   discards any leftover temporary name.
1. Construct `WorldConfig(world_root = the staging world path from the
   request, world_id = the request's staging world id, corpus_roots =
   (staging_root,))` — the staging corpus must be
   the world's one configured carrier, because `_resolve_carrier`
   requires exactly one configured carrier for a `corpus_id` and
   admission alone configures none. Then, in this order, **reinvoking
   each operation on retry rather than testing for its result** — both
   initializers are exact-retry and converge on identical input, and
   their own predicates are what decide whether a prior attempt was this
   one: `init_corpus_root(staging_root)`; `adopt_manifest(profile = the
   request's pins)` on the staging corpus, which mints the `corpus_id`
   the first time and refuses `ManifestAlreadyPresent` after, whereupon
   `load_manifest(staging_root)` recovers the id and its pins are
   compared to the request's — a mismatch is a foreign write, refused;
   `init_world_root(config)`, converging on the deterministic `world_id`
   and raising `WorldIdMismatch` for any other; then `open_world(config)`,
   which refuses an uninitialized world (`WorldUninitialized`). Both roots
   are private; the actor cannot reach them. The staging world is
   throwaway; its only purpose is to make the staging corpus eligible for
   a head export.
2. **Populate, with the `publication` record as the completion mark.**
   Resolve the selection at the request's frozen epoch, and write the
   selected records into the staging corpus through `beliefs`' ordinary
   writer, each write its own registered transaction, in the selection's
   canonical order. Write the `publication` record **last**: it lists the
   full selection, so its presence is the durable mark that population
   finished, and a staging corpus without it is by definition incomplete.

   **Resumption is exact, and identity is not enough.** The writer's
   duplicate refusal (`RecordAlreadyMinted`) proves only a shared
   `(uid, id)`, not identical bytes, so a retry compares every record it
   finds present **byte for byte** with the frozen-epoch record it would
   have written. The only resumable state is a **true prefix**: the
   `publication` record absent, and the present records, taken in the
   selection's canonical order, equal to the first *n* records of the
   selection byte for byte — no holes, since writes are ordered, and no
   extras. A retry continues from record *n + 1*. Anything else — a
   hole, an extra record, a byte mismatch, or a `publication` record
   present that is not byte-equal to the expected record — is corruption
   or a foreign write: `Refused(staging-corrupt)` naming the record,
   reported, never resumed, and never a trip back to step 2; the staging
   root is then an operator's to discard.

   Population is **complete** iff the `publication` record is present
   **and byte-equal to the expected record fixed at step 0** — which
   entails its selection list, provenance and `supersedes` are the frozen
   ones — every identity that record lists is present and byte-equal to
   the frozen-epoch record, and the corpus holds no record outside that
   list plus the `publication` record itself. Checking the members named
   by whatever marker is found would let a marker that omits a member or
   carries other provenance pass; comparing the marker whole does not.
3. **Validate, then admit, then export.** Re-check completeness as
   defined in step 2 — a true prefix sends the retry back to step 2,
   and any other failure is `Refused(staging-corrupt)` — then
   `World.admit` the staging corpus into the staging world (a fresh
   adoption, not a replica) **under the original intent's actor**,
   reinvoked on every retry: `World.admit` succeeds only for the exact
   admission record it would mint, so a prior admission by this attempt
   converges and one with different provenance or actor refuses — the
   registry is never merely inspected for the `corpus_id`. Then
   `export_head_artifact(staging world, corpus(corpus_id))` — the
   existing act, which requires an admitted corpus on a configured carrier
   (log-verification design §3.2). It returns the canonical bytes of
   `(subject, genesis identity, head digest)` under
   `science.head-artifact.v1` and **stores nothing**.
4. **Name the export root.** Lifecycle commands take paths, so every
   publish has a local **export root**: for a local destination it *is*
   the destination directory; for a Git remote, a Zenodo deposit, or an
   inbox it is the request's `export` path, a durable, publisher-owned
   directory that step 7 later transports. The actor cannot reach it.
5. **Write the artifact to its canonical sibling locator** —
   `<export root parent>/<corpus_id>.head-artifact.v1`, outside the root
   so the corpus bytes are untouched — by the durable create-only write
   of step 0: an existing file with byte-identical content is success, a
   same-name file with different bytes refuses as a collision, and
   partial bytes never appear. The sibling **is** the durable external
   retention of the observer, and the staging root is **retained until
   step 9** so that any retry re-exports from it; the export is a pure
   function of the staged chain, so a re-export is byte-identical and the
   idempotent write converges.
6. `replicate_root` from the staging root to the export root — which
   publishes a claim-only reservation, stamps read-only before it exposes
   payload, and grants neither writability nor serviceability
   (root-lifecycle design §2–§4). Then `restore_root(export root,
   corpus(corpus_id), observers = {the artifact read back from its sibling
   locator})`, which inspects, captures the presented identity, evaluates
   against that explicit observer set, and admits the copy to read-only
   service on a `validated` verdict and nothing else. An empty observer
   set is `unresolvable`, which is why steps 3 and 5 are not optional.
   For a local destination **this is the reveal**.
7. **Transport, for a remote destination only.** Upload the export root
   and its sibling to the remote address, and verify the upload by
   reading the remote back — its listing and digests against the export
   root's. Transport is destination-specific: its unit of atomicity,
   partial states, and verification are sub-project 5's to specify per
   destination kind, and nothing here claims more than "verified complete
   or not complete." For a remote destination **this is the reveal**, and
   the recipient's own `restore_root` + `admit_arrival` (§6.3) is the
   admission.
8. **Commit the source binding, after the reveal and never before.** In
   the source root, mint **this attempt's revision** of the source
   project's `publication-binding` record (§6.2) — naming the revealed
   corpus, the frozen predecessor tips it supersedes, and the artifact's
   content identity, and minted by the same deterministic factory rule as
   the marker, so its identity is a function of the request and intent —
   **and** the publish's terminal act-report **in one registered
   transaction** (`run_transaction`), so neither can exist without the
   other. "Same operation" is not enough: a revision committed with the
   act-report still unpublished would leave the operation intent
   unmatched while a retry read "done". Written earlier, a crash before
   the reveal would bind an unrevealed corpus; written here, the binding
   can only name a corpus that has been revealed — locally by step 6,
   remotely by step 7. The revision supersedes the frozen
   **`binding_tips`** and nothing else, and the family admits it by
   §4.1's intent-position rule — the one that applies to revisions minted
   inside a registered operation, predecessors judged as of this
   operation's intent position, not its commit: if a concurrent attempt from the same
   frozen tips committed first, those tips were still standing when this
   attempt's intent was appended, so this attempt still commits, and the
   binding then has two standing tips — the sibling publications §6.2
   permits, refused at resolution by the tip rule until a revision
   supersedes both. An attempt whose intent was appended *after* a
   sibling superseded its tips is refused at step 8
   (`predecessor-not-standing`) and reports so — its terminal act-report
   records the refusal, which fulfills the intent (`closed`) without
   minting this attempt's binding revision; it cannot silently re-target,
   and the revealed corpus stands unbound, an operator's to discard. A retry never re-reads the binding to decide what to
   supersede.
9. Discard the staging corpus and the staging world.

**Done** means exactly: **this attempt's binding revision exists** in
the source root — looked up by its deterministic identity, never by
resolving a current binding, since revisions are immutable and a
concurrent sibling or a later repair may already have superseded it —
**and** the publish intent's completion reading is `closed` (act-report
§3.3). Whatever else the binding holds — a predecessor revision, no
revision at all (a first publication), or a sibling that committed first
from the same frozen tips — says nothing about this attempt; only the
existence of its own revision does. "Present" below means exactly that.
Either
alone is not done, and the reading's other two values are kept apart:
`unfinished` is an unmatched intent, `indeterminate` is a qualification
that did not resolve, and the design never collapses one into the other.

`atoms` stays ignorant of root kinds. **The local lifecycle steps are
exact-retry**, and the staging root's retention through step 8 is what
makes them so; transport is retried under its own semantics. A retry
starts from the request record (step 0), reads the intent's completion
reading, classifies the state it finds, and resumes there:

| state found | resume at |
|---|---|
| request present; any of step 1's operations not yet converged | step 1, reinvoking each — their own predicates decide |
| staging initialized; true prefix (marker absent, ordered present records equal the selection's first *n* byte for byte) | step 2, continuing from *n + 1* |
| staging initialized; not an exact prefix and not complete (extra record, byte mismatch, marker with a missing member) | not resumable — `Refused(staging-corrupt)`, reported; the staging root is an operator's to discard |
| population complete; admission not yet converged | step 3's `World.admit` under the original actor — its predicate decides, and a differing admission refuses |
| population complete and admitted; no sibling, no export root | step 3's export, then step 5 |
| sibling present, no reservation (crash after step 5) | step 6 |
| bare reservation at the export root | step 6 — **retry the exact same replication**, which adopts the retained claim and converges; a different request refuses |
| stamped copy, sibling missing | step 3's export from the retained staging root, step 5, then step 6's `restore_root` |
| stamped copy with sibling, unserviceable | step 6's `restore_root` |
| serviceable export root; remote destination not verified complete | step 7, under that destination's retry semantics |
| revealed; this attempt's binding revision absent — whatever other revisions exist: the predecessor's, none (a first publication), or a concurrent sibling's; intent `unfinished` | step 8 |
| revealed; this attempt's binding revision present; intent `unfinished` | not a resumable state — step 8 is all-or-nothing, so this attempt's revision beside an unmatched intent is a foreign write, refused and reported, never resumed |
| revealed; either binding state; intent `indeterminate` | **fail closed**: not done, not resumed, not relabeled. The qualification did not resolve (act-report §3.3), and neither a retry nor a person may turn that into `closed` by re-running; it is surfaced as an audit finding and the publish stays open until the qualification resolves |
| revealed; this attempt's binding revision **absent**; intent `closed` | **terminally refused**, not done and never resumed: `closed` means fulfilled, not successful, and a fulfillment without this attempt's revision is step 8's `predecessor-not-standing` refusal on record — the revealed corpus is unbound and an operator's to discard, and a new attempt begins under a new token |
| revealed; this attempt's binding revision present; intent `closed` | done |

No abandon operation exists, and cleanup of a reservation nobody will
retry is an explicit out-of-band operator action, never something a
publish does.

**Each attempt is an operation with its own act-report**, and that is an
amendment, not a given: the kernel's operation-kind set is closed at five
and contains no `publish` (act-report §3). Sub-project 5 carries the
**versioned act-report amendment** adding the `publish` operation kind
with its entry and outcome vocabulary — staging, head export, replication,
restore, and transport entries, each with its outcome — banked in the
act-report design before any publish runs. Without it there is no
act-report, and the claim would be false.

**The atomicity claim is exactly this wide.** For a local directory,
`restore_root`'s grant is the reveal, and a published corpus is a valid,
serviceable corpus or it is not serviceable. For a git remote, a Zenodo
deposit, or an inbox, the reveal is destination-specific and **not**
atomic — an upload can stop half-way — so the guarantee moves to the
consumer: a corpus is admitted (§6.3) only if `restore_root`'s validation
passes on the recipient's copy against the transported head artifact and
its `publication` **marker** — that kind, not a `publication-binding` —
is present, well-formed, and identity-consistent with its own
attribution, and anything less is refused whole, never adopted in part. Publishing to a remote is the local
sequence through step 6 followed by step 7's transport; the transport's
partial states are the publisher's to retry and the recipient's to refuse.

### 6.2 One operation, three destinations

A destination is a directory the user controls (private), a git remote or
Zenodo deposit whose content is the corpus (shared), or a community world's
inbox. **Every publish mints a fresh, immutable corpus** (§6.1); there is
no destination corpus that is advanced in place. The reason is
mechanical: a world adopts a corpus whole, and epoch capture enumerates
every stored record (`iter_stored`, no selection applied), so a shared
corpus that kept dropped records could never unpublish one. A fresh corpus
per revision contains exactly the current selection and nothing else.

Revisions are linked by their `publication` records. Each record carries
`supersedes`: **zero or more** `(corpus_id, publication record identity)`
pairs — none for the first publication of a view to a destination, one in
the ordinary case, several when a revision repairs a divergence by
superseding every tip; the pairs are **marker** identities, one identity
domain. The source project holds a `publication-binding` record — a
distinct coordination kind (§4.1) — whose revisions bind `(view address,
destination)` to `(corpus_id, publication marker identity, head artifact
content identity)` and carry their own `supersedes` of **binding
revision** identities, the other domain; a binding revision therefore
always identifies the marker it bound, which is how step 0 projects one
reading into both. History is derived by walking either chain, never
stored as a list that could disagree with it. A
record dropped from the selection is
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

Consuming a published corpus is two existing acts on the recipient's
side: `restore_root` on their copy with the transported head artifact as
the observer set, admitting it to read-only service; then `admit_arrival`
with `ReplicaOf` provenance and the same observers — cut 8's arrival act,
which verifies the traveled chain and returns the admission record beside
its verification report, and admission additionally requires the
corpus's `publication` marker (§6.1) — the marker kind specifically, a
`publication-binding` never qualifying. `World.admit` is not the entry
point: it refuses `ReplicaOf` outright, holding no verdict to report. Any world can adopt
any publication this way, and a community commons is a world whose
operator adopts many. Coreference between a local
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
| 1 | **Coordination and view kinds** — opaque project identity minting, `(project, local id)` addressing, the coordination revision family (one or more predecessor tips; the general at-commit rule under the root lock; the tip rule), W11, W12, W13's two-projects negative; the coordination contract in `beliefs`; the `foundations.md` extension | `beliefs` | none — it is the tier-3 answer and joins the `mutation` lane | now |
| 2 | **Command framework** — declaration schema, write classes, budgeted renderer, preamble, adapter generator with the Claude Code target, CLI and MCP over `beliefs` reads; the writer endpoint with its bound permit, endpoint-set actor and session ledger; the write permit on every `beliefs` write entry point | `science`, `beliefs` | 0 | now, against today's kernel reads |
| 3 | **Biology domain pack** — GO, HP, EFO, MONDO bindings; mm30's operator vocabulary | `beliefs/domains/biology` | the `domain-boundary` lane | with that lane |
| 4 | **The dogfood command set** — the dozen commands over a real world root; mm30 reproduced, not migrated, as the first corpus | `science` | 1, 2, 3; `run-confinement` and `workflow-surface` for a real assessment | after 2; grows as lanes land |
| 5 | **Publish** — the act and `publication` record in `beliefs`, composed over `init_corpus_root`, a staging world, `export_head_artifact`, `replicate_root` and `restore_root`; the versioned act-report amendment adding the `publish` operation kind and the versioned coordination-contract amendment declaring `publication` and `publication-binding`, with their deterministic record factories and the family's intent-position rule for operation-minted revisions; transports carrying the head artifact, admission-side refusal and dry run in `science` | `beliefs`, `science` | 1; the `world-read` lane (view queries resolve through it) | after that lane |
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
- **Retaining the head artifact as a holdings observation.** An
  observation carries a digest and a locator, the store reader returns
  path state rather than payload bytes, and the store write mints a fresh
  token per call — so it could neither rebuild the sibling on retry nor be
  exact-retry itself. The retained staging root and the idempotent sibling
  write do both.
- **A new `publish_root` lifecycle command in `atoms`.** Staging plus
  `replicate_root` plus `restore_root` already yields claim, stamp,
  validation and reveal; a new command would add a design gate and teach
  `atoms` a root kind for nothing.
- **A permit threaded by the caller.** Any code in the writer's process can
  mint one; only a process boundary with filesystem denial makes the tier a
  fact rather than a convention.
