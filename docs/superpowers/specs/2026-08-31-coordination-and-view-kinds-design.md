# Coordination and view kinds — design (the `coordination-addressing` slice)

**Date:** 2026-08-31
**Status:** designed; conformance cut 14 is specified in §9 and freezes with
this document's banking, before any of its code exists. Not implemented.
**Scope:** the tier-3 `coordination-addressing` answer, per the user and
autonomy layer design (`2026-08-29-user-and-autonomy-layer-design.md`) §4.1,
§4.2 and §8 item 1: the view query language `science.view-query.v1`; opaque
project identity minting and `(project identity, local id)` addressing with
the `project` record as the one exemption; the coordination revision family —
one-or-more predecessor tips, the at-commit and intent-position admission
rules, one standing tip or `Refused(divergent-view)`; the coordination
contract, compiled into `ProfileSpec` and versioned independently of the base
contract; guarantee rows **W17** and **W18**, banked into world-addressing §7;
the cut-14 selection of W11, W12, and W13's two-projects negative; and the
`foundations.md` extension. These records are never world facts and never
belief inputs.
**Inherits:** world-addressing
(`../../designs/2026-08-02-world-addressing-design.md`) §3 and §6.1 — the
tier table and the coordination-address rule this document implements without
amending, save the two added guarantee rows and §6.1's discharge note. The
user and autonomy layer design §4.1–§4.2 is the ruling this document
elaborates; where that document already decides a point, this one cites it
rather than restating the argument. The implementation roadmap
(`../../plans/2026-08-29-implementation-roadmap.md`) carries the boundary; the
answer moves it to the `mutation` lane at the next re-rank, per its tier-3
rule.
**Out of scope:** the query evaluator (the `world-read` lane's, where W7
lives); the `science` command surface and its writer endpoint (sub-project 2);
`publication` and `publication-binding`, which arrive by the versioned
contract amendment sub-project 5 banks; the derived work queue (sub-projects
4 and 7); any migration of predecessor tasks — the old corpus's `t068` is
heritage, not a requirement.

## 1. The question, and the answer

Cut 4 §5 deferred W11 and W12 because "whether coordination records are
minted through the corpus-write adapter at all is undetermined," and cut 6
§3.2 parked W13's two-projects negative beside them. The user and autonomy
layer design ruled the posture; this document makes the ruling buildable.

**The answer: yes, through the adapter, by a dedicated family door.** Views
(`project`, `question`, `hypothesis`, `topic`, `theme`) and coordination
records (`task`, `decision`, `note`) are minted through `CorpusWriter` like
every other record — that is what makes them governed: they carry provenance,
their transactions enter the log, and their bytes move the corpus-state
identity, so epochs capture them. But they are declared by a **coordination
contract** compiled into `ProfileSpec`, not added to the kernel's kinds; they
carry no world address and appear in no world-index map; and no route from
them to belief exists to be guarded (§6). The guide's sentence that views
"are not additional kernel kinds" stays true.

Two rulings made earlier bind everything below:

- **A view is a stored world query plus a label** — "a project-scoped name
  over a world query," never a container (user-layer §4.1). World facts
  belong to views by query and may overlap; views and coordination records
  belong to projects by address, and exactly one project each (user-layer
  §4.2).
- **The address forms are ruled by kind, never by author** (world §6.1).
  World entities take world addresses; coordination records take
  `(project identity, local id)`; each form used for the other's tier is
  refused — W11's whole content.

## 2. The view query language — `science.view-query.v1`

The opening design decision: small and closed, not a query engine.

### 2.1 Stored form

A query is literal data in the view record, under a versioned identifier,
canonically projected like every other stored value. The whole grammar:

```
query     := { version: "science.view-query.v1", clauses: [clause, ...] }
clause    := { all: [predicate, ...] }           # non-empty conjunction
predicate :=
    { kinds: [<world kind>, ...] }               # kind membership
  | { references-term: <term identifier> }       # claims binding that referent
  | { closure: { anchor: <world address>,
                 predicates: [<relation>, ...],
                 direction: out | in | both } }  # relation closure from one anchor
  | { addresses: [<world address>, ...] }        # explicit enumeration
```

A query denotes the union over its clauses of the intersection of its
predicates' denotations. There is no nesting, no negation, no variable, and
no reference to another view: every value is a literal. `clauses: []` is
legal and denotes the empty selection — a fresh project's honest state;
`publish` refuses `empty-selection` at its own boundary and needs no help
here. Sharing a view definition across projects is copying the query
content — reuse, never co-ownership (user-layer §4.2): two projects wanting
one hypothesis are two project-scoped records over one world query.

### 2.2 Semantics

Denotational, over the world at a named epoch. Each predicate denotes a
subset of the epoch's world records:

- `kinds` — the records of those kinds;
- `references-term` — the propositions whose typed claim binds the named
  referent, resolved exactly as claim referents already resolve;
- `closure` — the records reached from the anchor by the named relation
  predicates in the stated direction, transitively, at the epoch;
- `addresses` — exactly the named records.

Evaluation is therefore a pure function of `(query, epoch)`, which is what
`publish`'s request-freezing requires and what makes two installations
agree. One rule is pinned now, though the evaluator is the `world-read`
lane's to build: **an anchor or enumerated address that does not resolve at
the evaluation epoch makes evaluation refuse naming it — never denote the
empty set.** Reading a failure to look as a finding of absence is
`fb-2026-07-27-010`'s error, and W8a's split applies verbatim: whether a
query is *well-formed* is a property of the record; whether its addresses
*resolve* is a property of the epoch and the checkout.

### 2.3 Admission at mint

A view revision carrying a query refuses (`ValidationRefused` lineage,
§4.6) unless: the query parses against the grammar; its `version` is one
the pinned coordination contract declares; every `kinds` value is a world
kind the contract's vocabulary names; and every clause is a non-empty
conjunction. Mint-time admission checks **form and vocabulary only**. It
never checks that an anchor resolves: the record is immutable while the
world moves, and a query whose anchor has not yet been minted — or whose
corpus is elsewhere — is a well-formed query that today evaluates to a
refusal, not a malformed record.

### 2.4 Closure, and how the language grows

At any pinned coordination-contract version the language is closed: the
contract declares which `science.view-query` version(s) a view kind's query
field may carry, and the predicate vocabulary is fixed by that version. New
predicates mean `science.view-query.v2`, arriving only by contract
amendment — the same road sub-project 5's amendment already travels for new
kinds. Nothing dispatches on unknown predicate keys; an unknown key is
malformed at version 1, forever.

### 2.5 Named limitation — no joins, deliberately

Version 1 cannot express "records related to whatever another clause
selected": no closure-over-selection, no join. "The assessments of my
term-selected propositions" is not writable; the author widens with
explicit `kinds`, `closure` or `addresses` predicates instead. This pinches
exactly at `publish`, whose `closure-incomplete` refusal pushes selections
toward computation closures — and sub-project 5 already banks a
coordination-contract amendment, which is where a closure-over-selection
form can arrive as a v2 predicate if the pinch is real. Nothing is built
for it now.

## 3. Identity and addressing

### 3.1 Minting

Creating a project mints its identity the way `adopt_manifest` mints a
`corpus_id`: `secrets.token_hex(16)` — 32 lowercase hex characters,
act-authored at creation, opaque, validated by shape everywhere it is read,
never re-derivable from name, path, corpus, or content. The identity is
carried by the project record itself and is **never written into a corpus
manifest**: several projects may share a corpus, and a project may change
which corpus holds it (world §6 rejects coupling the two identities).

Every other view and coordination record mints an opaque 32-lowercase-hex
**local id** the same way, at genesis. Fresh-mint collisions across
replicas of one project are thereby impossible; only sibling *revisions*
remain, and §4 owns those.

### 3.2 The address forms

```
coord:<project-identity>              # the project record — the exemption
coord:<project-identity>/<local-id>   # every other view/coordination record
```

The `project` record is the root of its own address space and the one
exemption from the qualified form: its address **is** its identity. The
`coord:` scheme is disjoint from the world-address form by construction, so
W11's refusal is syntactic and mechanical — a `coord:` reference where a
world entity is required, or a world address where a coordination record is
required, refuses **by kind before any lookup**, and no author choice can
blur the tiers.

### 3.3 Names are content

A project's name, a task's `t12`-style handle, a hypothesis's slug: all are
record content — rendered, searched, and superseded like any content, and
**never consulted by lookup**. This is W14's discipline extended verbatim
to the coordination tier: the only stored values participating in reference
resolution are the two identity halves. W12 follows by construction —
renaming a project is an ordinary project revision (§4), new name, same
identity, and every `(project identity, local id)` reference is untouched;
the old name survives only in superseded revisions' content. Handles may
collide freely — across projects, and even within one (a rename can reuse
a handle) — because nothing resolves through them.

### 3.4 References store the full qualified form

A stored reference to a view or coordination record is always the full
`coord:` address — there is no relative form, no "current project"
shorthand, and no default scope in storage; brevity is the renderer's job.
A `task` names blockers in a `depends` field of `coord:` addresses,
including addresses under another project's identity — the `t018`/`t043`
case world §6.1 exists to keep expressible. A reference resolves to the
address's current standing tip (§4.4) unless it names a revision identity
explicitly, in which case it reads that immutable revision.

### 3.5 `addressing.py`, discharged

World §6.1 kept the predecessor's `<project>:<artifact>` grammar alive on
paper, "corrected to bind project identity rather than the project name."
No such module exists in this repository — the grammar survives only in
design prose — so there is nothing to correct in place. This document
defines the `coord:` form fresh, and the §6.1 clause is discharged by
supersession: a note added beside it records that this design replaces the
corrected-survival plan. The `beliefs-tasks` records under `tasks/` are the
repository's own process tooling, not this design's records, and are
untouched.

## 4. The coordination revision family

### 4.1 Every record is a revision

A record's first revision — **genesis** — mints its address (the project's
identity, or a subordinate's local id) and names **zero** predecessors.
Every subsequent edit mints a new immutable revision naming **one or more**
predecessor tips. Nothing at this tier is edited in place, retracted, or
deleted; supersession is the only change, and a revision is a whole record,
never a patch. Timestamps and authorship ride the revision as content
(§5.2) and participate in **no** derivation: no tip choice, no ordering, no
expiry reads a clock.

### 4.2 A new door, not `supersede` reused

`CorpusWriter` gains a family entry point pair — genesis-mint and revise —
for coordination-tier kinds only. The existing `supersede` is not reused:
it is proposition-only and single-predecessor by signature, and revisions
need neither restriction. The predecessor set is stored as adapter-authored
`supersedes` relations on the successor; an author-written `supersedes`
relation refuses, exactly as it does today. Conversely `add`, `revise`,
`supersede` and `retract` all **refuse coordination kinds**, the way
`_refuse_family_kinds` already refuses `act-report`, `retraction` and
`holdings-observation`: these kinds have their own door, and no ordinary
path can mint or mutate them.

Two mechanical inheritances from the substrate, stated so they are built
rather than discovered: the door carries the **pre-plan already-minted
guard** (`Corpus.add` silently turns a create into a replace when a `uid`
already stands in the index, which is exactly what `_refuse_already_minted`
exists to prevent); and a revision commit is a **single-record
transaction** — one revision, one commit — since the batched-plan path is
`import_bundle`'s alone and the family does not need it.

### 4.3 Two admission rules, by how the revision is minted

- **The general rule — the ordinary write path, all eight kinds, project
  revisions included.** One transaction under the root's per-root operation
  lock, carrying **no** operation intent: `OPERATION_KINDS` stays closed
  and names nothing for these. Every named predecessor must be a standing
  tip **at commit**, judged under that lock over the root's read view;
  otherwise `Refused(predecessor-not-standing)`. Within one root the lock
  serializes revisions, so no sibling can arise there — the lock being
  in-process, that holds across processes only under the single-writer
  deployment obligation the ledger records for the composition root (its
  row 4); siblings otherwise arise across corpora or replicas, and §4.4
  handles them.
- **The intent-position rule — revisions minted inside a registered
  operation.** Every named predecessor must have been a standing tip **at
  the position in the source root's log where the operation's intent was
  appended** — a pure function of the chain prefix ending at that intent,
  provable by anyone holding the chain; a predecessor already superseded at
  that position refuses (`Refused(predecessor-not-standing)`). A
  predecessor superseded *between* intent and commit is still valid, and
  the result is two standing tips — the sibling state of §4.4, lawfully
  reached, not a violation. This document defines the rule; its only
  instance today is the `publication-binding` revision of a `publish`,
  which sub-project 5 lands with its own intent kind, and a future
  operation that mints revisions inherits the rule by amendment.

### 4.4 One standing tip, or refuse

The current revision of an address is its **one standing tip**: the single
revision of that address that no other revision supersedes. Resolution
gathers every revision of the address across the checkout's mounted
corpora — **live**, never epoch-bound (§6.2) — and:

- exactly one tip: that revision is the current record;
- two or more tips — minted across corpora or replicas, or lawfully by the
  intent-position rule: `Refused(divergent-view)` **naming every tip**.
  Resolution never chooses by recency, arrival, mount order, or iteration
  order, and swapping the order in which corpora are read changes nothing;
- zero tips with revisions present: a `supersedes` cycle, constructible
  only by raw write. An audit finding names the cycle; nothing repairs it
  silently, and no sanctioned door can produce it.

**Repair is one ordinary revision superseding all named tips** — the
general rule, multi-predecessor arity doing the one job it exists for.
After repair the address resolves again; the sibling revisions remain,
immutable and superseded.

### 4.5 A subordinate needs its project

Minting any `(project identity, local id)` record — genesis or revision —
requires the project record to resolve to one standing tip over the same
scope resolution uses. A project that is missing refuses; a project that is
divergent refuses with `Refused(divergent-view)` naming its tips, so the
author repairs the project first. No record is minted into an address space
that cannot currently be resolved.

### 4.6 Refusal shapes

Mint-time refusals are `WriteRefused` subclasses, one narrow class per
decidable condition, on the existing pattern: `PredecessorNotStanding`,
`CoordinationKindUnsupported` (wrong door, both directions),
`ProjectNotResolvable`, and the §2.3 admission refusals under the
`ValidationRefused` lineage. Read-time divergence is value-shaped like
`belief.Refused` — but with a **closed code set** validated in
`__post_init__` (the `NoBelief` pattern) and a structured `tips` field
carrying every tip's revision identity (the `ImportRefused.cycle_edges`
precedent), because a caller must enumerate the tips to author the repair.
The same value shape carries the intent-position judgment's refusal, which
is a verdict about a chain position rather than a failed write. The codes
are closed at two: `divergent-view` (resolution),
`predecessor-not-standing` (the intent-position judgment; the general
rule's mint-time counterpart is the `PredecessorNotStanding` exception).

## 5. The coordination contract

### 5.1 A new contract type

Not a domain contract, though it rides the same machinery where that
machinery fits. Domain contracts declare vocabulary — sorts, operators,
dimensions; the coordination contract declares **kinds**: which view and
coordination kinds exist, each kind's closed field set, which
`science.view-query` version(s) a view kind's query may carry, which kind
is the address-space root (`project`, the exemption), and that all its
kinds are members of §4's revision family. Version 1 declares exactly the
eight kinds of §1; `publication` and `publication-binding` arrive by the
versioned amendment sub-project 5 banks, and an earlier version's pin
authorizes nothing an amendment added.

It has its own parser with a closed field set; a hand-built contract
object refuses at compile, on the `UnparsedContract` pattern; an unknown
field, a duplicate kind, or a malformed declaration refuses at parse.

### 5.2 Record shapes, version 1

Every kind carries: `name` (the label; content, §3.3), `body` (prose),
`author` (the attributed actor — coordination records are attributed acts;
the `science` writer endpoint binds it to the session actor when
sub-project 2 lands), and `at` (an RFC3339 timestamp; content only, §4.1).
View kinds add `query` (§2). `task` adds `status` — a closed vocabulary,
`open | done | dropped` — and `depends`, a list of `coord:` addresses
(§3.4). `note` adds `about`, an optional list of world addresses naming
what the note comments on — the "project commentary on a world entity" of
world §3, and the one sanctioned place a coordination record references the
world tier; the reference is inert, like everything here. No other kind
carries a cross-tier reference field, and no field anywhere at this tier is
consulted by lookup.

### 5.3 Independently versioned, by the existing succession mechanism

The contract carries `version` and `predecessor` lineage and passes the
succession check domain contracts already pass — genesis has no
predecessor, a successor names its predecessor's content identity, and a
mismatch refuses. The base contract deliberately has no lineage; the
coordination contract does not touch it and does not wait for it. Amending
the coordination contract mints a successor content identity and moves no
base-contract pin.

### 5.4 Pinned like a domain, under a reserved namespace

The pin rides the corpus manifest's `domains` mapping as
`coordination:<64-hex>` — exactly what the user-layer design's publish §6.1
already assumes when it derives destination pins. `coordination` joins
`science` as a reserved namespace no domain contract may claim, enforced
where that ban already lives (manifest parse and pin validation).

### 5.5 Compilation and authorization

`compile_profile` accepts the coordination contract alongside the base and
domains; `ProfileSpec` carries the compiled kind specs and folds the
contract identity into `compiled_identity` and `activated_contracts`. The
family door (§4.2) authorizes a mint **only** for a kind the pinned
contract version declares: a corpus pinning no coordination contract mints
no coordination records, and a kind an amendment added is unauthorized
under every earlier pin. "A pinned contract can authorize only the kinds it
declares" is thereby mechanical, not policed.

### 5.6 Structurally inert to belief

The contract declares no operators, no sorts, no dimensions. The consulted
set — which admits a domain only when a claim operator's declaring
namespace was read — can therefore never name it, and no coordination pin
ever perturbs `belief_input_digest`. "Never belief inputs" holds by
construction; §6 states the other half.

## 6. Storage and the world boundary

### 6.1 Governed means: in a corpus, through the adapter, in the log and epochs

A coordination record is an ordinary node in whichever corpus root it was
written to. It carries provenance and attribution, its transaction enters
the corpus log, and its bytes move the corpus-state identity like any
content, so epochs capture it. That is the whole sense of "governed," and
all of it.

### 6.2 Never a world fact

No coordination record has a world address, and none appears in any
world-index map — address, producers, retraction, coreference — which stay
derivations over world entities only. Two resolution regimes follow, kept
visibly apart:

- **World reads are epoch-bound.** A view's *query* evaluates at a named
  epoch (§2.2), because its answer is a belief-adjacent selection over the
  packaged world.
- **Coordination resolution is live.** The *record* — which revision of the
  view or task is current — resolves over the checkout's mounted corpora
  with no epoch named (§4.4): coordination is not belief input, and no
  packaging step mediates seeing your own task edit.

Belief exclusion is double: no coordination kind declares a belief-bearing
edge (inertness is the default — foundations' closed routes), and §5.6 made
the contract invisible to the consulted set. View queries select **world
records only**: the `kinds` vocabulary is world kinds (§2.3), so a view can
never select a task, and the derived work queue — which does read open
tasks — is queue derivation over coordination records directly
(user-layer §4.4), not a view query, and stays sub-projects 4 and 7's.

### 6.3 Moving and sharing corpora

Several projects share a corpus freely. A project moves to another corpus
by minting its next revision there — cross-corpus supersession is ordinary,
since tip resolution is world-wide — and nothing else moves: subordinate
records may remain in the old corpus, their addresses name no corpus, and
no reference anywhere is rewritten. This is what W13's two-projects
negative pins: two projects pointed at one corpus see one `corpus_id`;
repointing a project moves no corpus identity; project identity and corpus
identity never touch.

## 7. Guarantees

W11, W12 and W13's two-projects negative stand as world-addressing §7 froze
them; this design adds two rows there — the W15/W16 precedent, extension
under existing identifiers, frozen text preserved — because the inherited
rows say nothing about tips or authorization:

- **W17 — the coordination revision family.** One standing tip or a refusal
  naming every tip; both admission rules; repair; the cycle finding; the
  subordinate-needs-project refusal; no other door. The full arm text is in
  world-addressing §7.
- **W18 — contract-governed minting, world-inert.** Authorization by the
  pinned coordination-contract version; query admission's
  malformed/unresolvable split at the mint boundary; no index-map
  membership and no `belief_input_digest` movement; the reserved-namespace
  refusal. Full arm text in world-addressing §7.

The roadmap's boundary index and appendix B carry the new rows under
`coordination-addressing`, and appendix A's generated table regenerates over
the extended inventory.

## 8. Limitations

1. **The v1 query language has no joins** (§2.5). The growth path is a v2
   predicate by contract amendment, on `publish`'s evidence of need.
2. **Cross-process tip admission rests on the single-writer obligation.**
   The at-commit judgment is exact only under the per-root lock; two
   writer processes on one root are that obligation's violation, exactly
   as §7.1's exclusivity and the publish sequence already depend on it.
   Cut 14 does not race processes to prove it.
3. **Divergence is detected at resolution, not at mint.** Two replicas
   mint siblings without error — correctly, since neither can see the
   other — and the refusal surfaces when a checkout mounts both. There is
   no background reconciliation; repair is authored.
4. **Resolution scope is the checkout.** A tip standing in an unmounted
   corpus is invisible, and no finding says so — the checkout answers for
   what it mounts, as world reads already do. Mounting later may turn one
   tip into two; that is §4.4's refusal doing its job late, not wrongly.
5. **The intent-position rule runs no operational instance here.** Its
   only operation is `publish` (sub-project 5); cut 14 exercises the rule
   as a pure function of a constructed chain prefix (§9).
6. **Handles are unreserved.** Nothing prevents two live records of one
   project sharing a display handle; lookup never reads one, and the
   surface may warn, but no invariant exists to enforce.

## 9. Conformance cut 14

Cut 13 is claimed by the banked run-confinement design (its §9) and does
not renumber; this cut takes 14 regardless of freeze order, so no banked
document moves. Frozen with this document's banking, before any code
exists.

### 9.1 Selection

| row | arms in cut 14 | banked |
|---|---|---|
| **W11** | a qualified `coord:` reference where a world entity is required → refused by kind; a world address where a coordination reference is required → refused by kind; both before any lookup, off the address form alone | **closes** |
| **W12** | rename a project by ordinary revision; every stored `(project identity, local id)` reference resolves unchanged; resolution consults no name, handle, or label — the old name survives only in superseded revisions' content | **closes** |
| **W13** | the two-projects negative only: point two projects at one corpus → one `corpus_id`; repoint one project to another corpus → no corpus identity changed | remains **part** — every other arm is `world-resolution`'s |
| **W17** | genesis arity zero; every edit a new whole revision; `add`/`revise`/`supersede`/`retract` refuse coordination kinds (no other door), and the family door refuses world kinds; the pre-plan already-minted guard holds at the new door; general rule: a named predecessor superseded before commit → `predecessor-not-standing` under the lock; siblings minted in two corpora → `Refused(divergent-view)` naming every tip, and swapping mount order changes nothing; one repair revision superseding all tips restores resolution, with the siblings retained immutable; the intent-position rule judged as a pure function of a constructed chain prefix, including the superseded-between-intent-and-commit case that lawfully yields two tips; a raw-written `supersedes` cycle → audit finding naming the cycle, zero tips, no repair; a subordinate mint under a missing or divergent project → refused | **closes** — the rule's operational instance (`publish`) is sub-project 5's, banked unrun in §9.3 |
| **W18** | a kind the pinned coordination-contract version does not declare → refused (no pin, no mints; an earlier version authorizes nothing an amendment added); an ill-formed or out-of-vocabulary query → refused at mint, while a well-formed query whose anchor does not resolve is **accepted** — the malformed/unresolvable split at the mint boundary; coordination mints appear in no world-index map and move no `belief_input_digest`; a domain contract claiming the `coordination` namespace → refused | **closes** |

### 9.2 Where the arms live

**Portable suite** (no host prerequisite): the `science.view-query.v1`
grammar — parse, canonical projection, every §2.3 admission refusal, and
the accepted unresolvable-anchor case; `coord:` address-form validation and
both W11 refusal directions; the coordination-contract parser, succession
check, reserved-namespace refusal, and `compile_profile` over base +
domains + coordination, including `compiled_identity` movement; the
intent-position judgment over constructed chain prefixes; the
`Refused` value's closed code set and structured `tips` field.

**Durable suite**, on the certified volume beside the checkout (the
composition-root pattern every corpus-write cut since 4 uses): the family
door end to end — genesis, revision, the at-commit refusal under the lock,
wrong-door refusals both directions, the already-minted guard; two-corpus
sibling minting and `divergent-view` with mount-order swap; repair;
the raw-written cycle audit finding; the subordinate-needs-project
refusals; W12's rename walk; W13's two-projects negative; W18's index-map
absence and `belief_input_digest` stability, asserted over a packaged
epoch.

**N2**: `n2_arms_cut14.py` declares every selected arm with its sabotage in
the family door, the tip resolver, the query parser, the contract
compiler, or the manifest pin validation; `test_n2_cut14.py` and
`tools/cut14_acceptance.py` follow the cut-12 pattern, with
`PREFIX_RUNNERS` naming the newest discharged prefix chain as it stands at
discharge time.

### 9.3 Limitations, banked as unrun by design

- Cross-process interleavings of the per-root lock: the single-writer
  obligation (§8.2), recorded, not raced.
- The intent-position rule's operational instance: `publish`'s
  `publication-binding` revision, sub-project 5's cut, against its own
  contract amendment.
- View-query evaluation over a live world: W7, the `world-read` lane's.
- Replica divergence is simulated as two corpora in one checkout; no test
  synchronizes real replicas.

## 10. What this banking changes elsewhere

In the same commit as this document: world-addressing §7 gains W17 and W18
and §6.1 gains the discharge note (§3.5); the roadmap's boundary index and
appendix B carry the new rows and appendix A regenerates; the guarantee-row
inventory and the README's and guide's row totals move from 151 to 153; the
open-questions coordination-records bullet leaves, per user-layer §8; and
`foundations.md` gains its governed-tiers subsection with this document in
its sources. The boundary itself moves to the `mutation` lane at the next
re-rank, not in this commit, per the roadmap's tier-3 rule.
