# Publication records — the coordination amendment, the publish intent, and the intent-position rule

**Slice of:** `2026-08-29-user-and-autonomy-layer-design.md` §4.1, §6.1 steps 0
and 8, §6.2 and §8 item 5 — sub-project 5's `beliefs` half, first of two slices
**Boundary:** `publish` — W17's publication-binding intent-position arm, and the
governed publication records (`../../designs/2026-08-03-redesign-adoption-ledger.md`,
Current state)
**Task:** `beliefs-1a5157` (lane task); this slice's child is filed with the spec
**Lane:** `world-read`, its head since cut 38 (roadmap §Lanes)
**Cut:** 39, off the path (roadmap tier 1, off-path row 1)
**Status:** approved 2026-09-22 after two user reviews; plan next

## 1. What this slice is

The layer design specifies `publish` to the step (§6.1 steps 0–9 and the
recovery table), and the step list leans on six things the kernel does not
have. A read of the tree on 2026-09-22 found:

1. **No shipped coordination contract.** The eight coordination kinds are
   compiled from a test fixture (`python/tests/coordination_fixtures.py`
   `COORDINATION_DOCUMENT`); the package ships only the base contract and the
   biology domain. §4.1's "versioned amendment of the coordination contract"
   has nothing to amend, and no corpus pins a coordination contract today
   (mm30's manifest pins the base, `biology` and `mm30`).
2. **No evidence for the intent-position rule.** The coordination design's
   §11.6 withdrew cut 14's constructed-prefix arm: an intent entry carries
   only its payload, the operation intent is closed at `(kind, event_token,
   actor)`, transaction entries carry path-state fingerprints, and a
   multi-corpus resolver reads chains other than the source's. It handed the
   evidence shape to `publish`. W17 has stayed partial on this arm since.
3. **No record shape for a marker or a binding.** `coordination_revision`
   admits only same-address `supersedes` relations, so §6.1's "relations are
   the selection" and §6.2's cross-corpus marker `supersedes` pairs cannot be
   stored as relations.
4. **No deterministic identity.** Every coordination id and uid is
   `secrets.token_hex(16)` (`corpus.py` `mint_coordination`,
   `revise_coordination`), and `nodes` defaults `Node.uid` to `uuid4`.
5. **No `publish` operation kind or act family.** `OPERATION_KINDS` is closed
   at eight; `permit.py`'s `ACT_FAMILIES` notes that `publish` "arrives by
   sub-project 5's amendment".
6. **A frozen-epoch retry cannot re-resolve the selection.**
   `evaluate_query` refuses `corpus-drifted` once a contributing corpus moves
   after the epoch, and an epoch keeps no record bytes, so one `task` minted
   in the project's corpus would strand a publish mid-population.

Items 1–5 are records and evidence; item 6 belongs to the act that
populates a staging corpus. This slice takes 1–5 and builds §6.1's step 0
**intent** and step 8 **binding commit** — the two points where the source
root is written — as internal doors with no public route. The second slice
(cut 40, planned after this one discharges) builds the act between them:
the request record and the durable create-only write, the selection snapshot
that answers item 6, the step-0 refusals that precede the intent
(`pins-disagree`, `empty-selection`, `closure-incomplete` with its composite
amendment) and the retry's `request-corrupt`, staging, head export,
replication, restore, the transport seam, the recovery table,
marker-required arrival, and the recipient's `divergent-publication`.

It closes **W17 in full** (unless W17-p-f's rollback cannot be produced durably, §11.2) and opens and closes the publication-record rows
Y1–Y4 (§10). It is **off the path**: the success criterion publishes
nothing. It amends one oracle before `contract-cut` freezes — the coordination
contract, which §4.1 and the coordination design §5.1 assign to this
sub-project — and rides beliefs-c80d8c's `composite`/`composes` query
amendment in the same version, as the coordination design §5.1's 2026-09-16
note assigns.

## 2. Decisions

Each decision names what it rejects.

1. **Two slices, split at the source-root writes.** This slice owns every
   record and every write to the source root; the next owns every write
   outside it. **Rejected:** one slice for the whole of §6.1. It would be the
   largest slice in the corpus, and the writer-session design (939 lines,
   five review rounds) is the recorded cost of that shape. **Also rejected:**
   splitting by step number (0–3, then 4–9): steps 0 and 8 share the
   evidence, and splitting them apart puts the W17 arm's two halves in two
   cuts.

2. **Ship the coordination contract as two versions.** Version 1 is the
   fixture document byte for byte, moved to
   `beliefs/contracts/coordination/v1/CONTRACT.yaml`; version 2 is its
   successor at `…/v2/CONTRACT.yaml`, `lineage: {successor: <v1 identity>}`,
   adding the `publication` and `publication-binding` kinds (§3) and
   `composite` and `composes` to the query vocabulary.
   `shipped_coordination()` returns version 2; `shipped_coordination(1)` returns
   version 1, which the fixture module then loads rather than spelling. **Rejected:**
   shipping one version 1 that already declares ten kinds. No corpus pins
   coordination today, so nothing would break; but W18's "an earlier
   version's pin authorizes nothing an amendment added" is then an arm about
   fixtures only, and §4.1's banked text names a versioned amendment.

3. **The intent binds its evidence.** The publish intent is a domain-tagged
   payload, `science.publish-intent.v1` (§5), after the holdings intent's
   precedent (`intents/holdings.py`). Besides `(kind, event_token, actor)` it
   carries the request identity, the frozen `binding_tips` and `marker_tips`,
   and one **anchor** `(corpus_id, genesis digest, head digest)` for every
   mounted root other than the written root, captured under the written
   root's lock before the append. **Rejected:** widening `OperationIntent`.
   Its closed shape is decoded in three places and read by every audit;
   a domain tag leaves every other kind's intent byte-unchanged. **Also
   rejected:** confining binding revisions to the written root, so that the
   source chain alone proves standing. It is simpler, but a project that
   moves corpora (coordination design §6.3) would lose its binding history
   and its next publish would be a first publication.

4. **Standing at a position is a record's registration moment.** A
   coordination revision is create-only at a path derived from its id
   (`CorpusWriter._relative_path`), and the registration that created it
   carries that path's final `FileState` with the content hash of its bytes.
   So "revision *r* existed at position *p*" is a fact about the chain plus
   *r*'s own bytes: some committed registration moved *r*'s path from absent
   to a file whose content hash is *r*'s, and its moment (cut 36's
   `world/events.moment`) is at or before *p*. §11.6's fingerprint objection
   holds for mutable paths and not for create-only records; its multi-corpus
   objection is what decision 3's anchors answer. The comparison of an engine
   `FileState` against bytes is engine-typed, so it lives in `root.py` behind
   the log seam (§6). **Rejected:** caching the tip set in the intent and
   trusting it. That is the caller-asserted stand-in §11.6 refused to build.

5. **Marker and binding carry their cross-record fields as facet fields.**
   The marker's selection, its `published_from` and its cross-corpus
   `supersedes` pairs, and the binding's bound `(corpus_id, marker, artifact)`,
   are declared fields of the kind (§3), validated by a closed per-kind rule
   beside `_validated_coordination_content`. The binding's own `supersedes`
   of binding revisions stays a relation, since it is same-address and the
   family's tip rule reads it. **Rejected:** widening `coordination_revision`
   to admit other relation predicates. Every coordination kind would then
   admit them, and the relation-signature inventory (`stored.py`) would need
   a coordination-to-world edge that nothing but the marker wants.

6. **Deterministic identity by a factory, not by a parameter on the family
   doors.** `beliefs/publication.py` mints both records from the decoded
   intent and nothing else; `mint_coordination` and `revise_coordination`
   refuse both kinds with a new `KindNotMintedHere` (`errors.py`), and every
   other ordinary door already refuses them once they join
   `COORDINATION_KINDS`, since `EXCLUDED_MUTATION_KINDS` and
   `_refuse_family_kinds` are built from it. **Rejected:** a `uid=` parameter
   on `revise_coordination`. It would let any caller mint a revision whose
   identity claims a publish that never happened.

7. **A `publish` act family.** `ACT_FAMILIES` and the `ActFamily` literal
   gain `publish`; `KIND_ACTS` maps `publication` and `publication-binding`
   to `{"publish"}` alone. `RequiredCapabilities.coordination()` keeps its
   permit to the eight ordinary kinds (it is built from `_COORDINATION_KINDS`
   today, so the two new kinds are excluded from it explicitly), and
   `RequiredCapabilities.publishes()`, which raises today, returns the
   `publish` family over `publication-binding` together with `corpus-write`
   over `act-report` — the intent door needs the second because
   `_append_operation_intent` requires it.

   `publish` is **not command-reachable** (`COMMAND_REACHABLE_FAMILIES` is
   unchanged): `science`'s write classes reach it by `science`'s own design.
   Since `RequiredCapabilities.__post_init__` refuses any family outside that
   set, the requirement's admissible families and command-route validation
   are separated by one closed exception, not by widening the set:
   `permit.py` gains `KERNEL_REQUIREMENTS`, a frozenset holding exactly the
   one publication permit above, and `__post_init__` admits a permit whose
   families are command-reachable **or** that equals a member of
   `KERNEL_REQUIREMENTS`, and refuses everything else as today. So
   `publishes()` constructs, and every ordinary declaration route that names
   `publish` still refuses — `for_kinds(["publication-binding"], …)`, whose
   permit is `{publication-binding}` over `{publish}` and not the kernel
   one; a direct `RequiredCapabilities(WritePermit(…, {"publish"}))`; and the
   kernel permit widened by one kind. `test_permit.py`'s invariant that every
   declaration requirement is command-reachable excludes exactly
   `KERNEL_REQUIREMENTS`.

   **Rejected:** minting both kinds under `corpus-write`. A session permitted
   to write tasks could then mint a binding. **Also rejected:** adding
   `publish` to `COMMAND_REACHABLE_FAMILIES`. Every command declaration could
   then name it. **And:** having the doors call `authority.require` without a
   `RequiredCapabilities`. It would work, but `publishes()` exists to be the
   requirement the second slice's act and `science`'s eventual route both
   cite, and it would go on raising a false reason (`publish is not an act
   family`).

8. **The act-report amendment banks only what this slice emits.** `publish`
   joins `OPERATION_KINDS`, with one entry kind, `publication-binding`, and
   its outcomes (§7). The lifecycle entries (staging, export, replication,
   restore, transport) arrive with the code that emits them, by the second
   slice's amendment. **Rejected:** banking the whole §6.1 vocabulary now.
   Those entries' fields depend on the request record and the recovery
   table's states, which the second slice designs.

9. **The destination is a closed union.** `local` carries an absolute,
   normalized POSIX directory path; `remote` carries a URL under cut 35's
   canonicalization profile (`holdings` `url` locator). Its canonical `v1`
   encoding is what the addresses and the request identity digest.
   **Rejected:** an opaque string. Two spellings of one directory would be
   two bindings, and two sibling histories for one destination.

10. **`publish` opens only through its domain intent.** Adding `publish` to
    `OPERATION_KINDS` would otherwise make `OperationIntent("publish", …)`
    constructible and let the domainless `{kind, event_token, actor}`
    branch of `decode_intent` decode a bare publish triple. Both refuse
    `publish` explicitly: the constructor raises `MalformedRecord`, and the
    domainless branch decodes a `publish` triple as `malformed`, so an
    evidence-free publish intent is an audit finding, never an operation.
    **Rejected:** a separate kind set for domain intents. The report's
    `operation` field and `stored.act_report_facet` read `OPERATION_KINDS`,
    and one closed set is what T1's report shape names.

11. **`predecessor-not-standing` detects a broken single-writer
    obligation.** In one process, step 0 reads the tips and appends the
    intent under one lock, so the tips it freezes are standing at the
    intent's position by construction, and the binding door's recomputation
    finds them standing. The recomputation still runs, because the lock is
    in-process (`OperationLock`): a second process writing the same root
    — the violation of the obligation the ledger records for the
    composition root (row 4), which the layer design §6.1 step 0 names —
    can commit a supersession between the tip read and the append, and the
    recomputation is what turns that into a refusal rather than a binding
    over a superseded tip. The acceptance arm injects exactly that second
    writer (§11.2). **Rejected:** calling the outcome an ordinary race. Under
    the obligation it cannot occur, and a design that claims otherwise would
    have an arm with no reachable path.

## 3. The coordination contract, version 2 — `beliefs/contracts/coordination/`

Version 2 is version 1 plus:

- `query_vocabulary.kinds` gains `composite`; `query_vocabulary.relations`
  gains `composes` (the coordination design §5.1 note of 2026-09-16);
- `kinds.publication`: `fields: [name, body, author, at, event_token,
  published_from, destination, selection, supersedes_markers]`,
  `query_versions: []`;
- `kinds.publication-binding`: `fields: [name, body, author, at,
  event_token, view, destination, corpus_id, marker, artifact]`,
  `query_versions: []`.

`check_coordination_succession` already admits added kinds and query
vocabulary. The hard-coded kind lists move with the contract:
`coordination.COORDINATION_KINDS` and `permit._COORDINATION_KINDS` gain the
two kinds (the test that holds `KIND_ACTS`' key set to `stored.WORLD_KINDS ∪
COORDINATION_KINDS` keeps them honest); `EXCLUDED_MUTATION_KINDS` and
`_refuse_family_kinds` need no edit, being built from `COORDINATION_KINDS`.
`_validated_coordination_content` gains a closed rule per kind:

| field | `publication` | `publication-binding` |
|---|---|---|
| `name`, `body` | the literal strings `publication`, `""` | `publication-binding`, `""` |
| `event_token` | 32 lowercase hex | 32 lowercase hex |
| `published_from` | `{world_id, epoch, view, view_revision}`: 32-hex, 64-hex, canonical `coord:` address, 32-hex | — |
| `selection` | non-empty list of record ids, strictly ascending | — |
| `supersedes_markers` | list of `[corpus_id, marker uid]`, strictly ascending, possibly empty | — |
| `view` | — | canonical `coord:` address, unpinned |
| `destination` | the decision 9 union, canonical | the decision 9 union, canonical |
| `corpus_id`, `marker` | — | 32-hex each |
| `artifact` | — | 64-hex head-artifact content identity |

A marker carries **no relations**; a binding carries exactly its
`supersedes` relations to `binding_tips`. Neither is a belief input: both
are coordination role, excluded from world-index maps and
`belief_input_digest` by `WORLD_KINDS` membership, cut 14's existing rule,
which the acceptance module reads once for each (Y1).

## 4. The records and their factory — `beliefs/publication.py`

```python
@dataclass(frozen=True)
class Destination:          # decision 9
    type: Literal["local", "remote"]
    locator: str

def binding_address(view: CoordinationAddress, destination: Destination) -> CoordinationAddress
def marker_address(view: CoordinationAddress, destination: Destination) -> CoordinationAddress
def marker_record(intent: PublishIntent, *, world_id, epoch, view_revision, selection) -> Node
def binding_record(intent: PublishIntent, *, corpus_id, marker, artifact) -> Node
def marker_consistent(node: Node) -> bool
```

- **Two addresses per `(view, destination)`.** Both are `(view.project,
  local)`; the binding's local is `digest("science.publication-binding-address.v1",
  [view.project, view.local, destination])[:32]` and the marker's is the same
  under `science.publication-address.v1`. The resolver gathers revisions by
  address alone (`CoordinationResolver._at_address`) and the coordination
  design §4.3 fixes an address's kind at genesis, so sharing one address
  would let a marker held in a mounted destination corpus become a binding
  tip. Every publish of one view to one destination shares each address, so
  step 0 finds the tips without a lookup table, and a first publication is
  simply a revision with no predecessors.
- **Identities.** A record's uid is `digest(<domain>, event_token)[:32]`
  with `science.publication.v1` for the marker and
  `science.publication-binding.v1` for the binding; the id follows
  `coordination_revision`'s form from the address and the uid.
- **Content.** `author` is the intent's actor and `at` the intent's `at`
  (§5): the factory reads no clock and draws no randomness, so every byte
  is a function of the intent and the named arguments. `marker_record`'s
  `supersedes_markers` is the intent's `marker_tips`; `binding_record`'s
  relations are the intent's `binding_tips`.
- **`marker_consistent`** recomputes the uid, the address and the id from
  the marker's own `event_token`, `published_from.view` and `destination`,
  and answers `False` on any difference. The check is self-contained: a
  recipient holds the marker, not the publisher's destination — its copy
  sits wherever its own `restore_root` put it — so the marker carries the
  canonical destination it was published to, and a marker whose carried
  destination disagrees with its address fails. Arrival calls
  it in the second slice; here it is a pure function with a unit table
  (Y2).

## 5. The publish intent — `beliefs/intents/publish.py`

```text
{ "domain": "science.publish-intent.v1",
  "kind": "publish", "event_token": <32-hex>, "actor": <actor>, "at": <RFC3339>,
  "view": <coord address, pinned to the resolved revision>,
  "destination": <decision 9, canonical>,
  "binding_tips": [<32-hex>, …],                  strictly ascending
  "marker_tips":  [[<corpus_id>, <marker uid>], …], strictly ascending
  "anchors": [{"corpus_id", "genesis", "head"}, …] ascending by corpus_id,
                                                  every mount but the written root }
```

`PublishIntent` is its sealed value; `decode_publish_intent` is the one
decoder and `shapes.decode_intent` dispatches to it on the domain, beside
the holdings branch. A malformed payload under the domain decodes as
`malformed` for audit, exactly as a malformed holdings intent does.
`DecodedIntent.shape` gains `publish`, and `shapes.mismatch` gains a
`PublishIntent` branch ahead of the holdings fall-through (which today
answers any non-`OperationIntent` value's `ReportEvidence` with
`wrong-purpose`): it qualifies by a `ReportEvidence` whose operation is
`publish` and whose token matches, `wrong-kind` and `wrong-token`
otherwise. `completion` itself is unchanged.

The written root is identified by the chain the intent sits in, so it needs
no anchor: its position is the intent entry itself. The `view` is pinned so
that the request identity names the view revision (§6.1 step 0), and the
`at` is read once, here, from the clock the composition root supplies.

## 6. The intent-position judgment — `coordination.py` and the log seam

```python
def standing_at(
    resolver: CoordinationResolver, address: CoordinationAddress, *,
    written: Path, position: str, anchors: Sequence[Anchor], moments: MomentSeam,
) -> tuple[CoordinationRevision, ...] | PositionRefused
```

For each mounted root the judgment takes a **bound**: the written root's
bound is the index of the entry `position` (the intent's digest); every
other root's bound is `events.place(view, anchor)`'s head.

**The chain, not the directory, says which revisions exist.** A first
reading that decided presence per file found on disk had a hole: if B
superseded A before the bound and B's file later vanished or went
malformed, the resolver would omit B and declare A standing. So the
judgment starts from the chain. For each root *R* and the address, the
seam's `inventory(R, address, bound)` replays *R*'s committed registrations
up to the bound and returns every path under the address's path prefix —
`{kind}/{project}.{local}.` followed by a 32-hex uid and `.md`, which is
`nodes`' `path_for_node_id` over the coordination id form — whose state
after the last committed registration touching it is a `FileState`, with
that state as the expected content. Pending and rolled-back registrations
move nothing, so a write in flight in an unlocked root, an unrecovered
crash, and a rolled-back step-8 attempt followed by its retry are all read
correctly by construction. The judgment then reads each inventoried path's
current bytes and requires, per revision:

| check | refusal |
|---|---|
| the file exists | `revision-missing` |
| the seam's `matches(expected, bytes)` — the `FileState` content hash is engine-typed | `revision-mismatch` |
| the bytes decode as a coordination revision at the address, of the address's kind | `revision-malformed` |

The **present revisions are exactly the inventory**, and `standing_at`
returns `standing_tips` over them — the family's one tip rule, unchanged,
over a chain-derived set. A committed registration before the bound that
moves an address path from a `FileState` to `ABSENT` or to another
`FileState` is a removal or rewrite of an immutable record, which no door
performs: `history-violated`, rather than a silently shrunken inventory.

**A file the chain does not account for.** Files at the address outside the
inventory are classified, never ignored silently. After listing them the
judgment re-reads *R*'s chain: a listed file created by a registration that
is pending, rolled back, or committed after the bound is not present and
not a refusal; a listed file no registration in the re-read creates is
`unregistered-revision`. The re-read is what makes this exact: the engine
admits a registration before its effects run (`atoms`
`coordinator/commands.py` `run_transaction`, write-ahead), so a file seen
on disk has its registration in any later read of the chain, and a write
that becomes visible during the listing and then rolls back is classified
by its rolled-back registration, not by the file's presence. The plan's
Task 0 pins the write-ahead order with a test before anything relies on it.

`MomentSeam` — `inventory`, `matches`, and the re-read classification —
lives in `root.py` beside the log seam, reached by its consumers as
callables, so `root.py` stays the one `atoms` importer.

The remaining refusals, all values:

| `PositionRefused` reason | when |
|---|---|
| `mounts-changed` | the resolver's mounted corpus ids differ from the written root plus the anchors' |
| `anchor-unplaced` | `place` answers `None`: another genesis, or a head no longer in the chain |
| `chain-absent` | a mounted root has no chain (`AbsentView`) |
| `chain-malformed` | a mounted root's chain is not well-formed |

A root whose files predate its genesis — `init_corpus_root` registers an
empty baseline even over a populated directory — answers
`unregistered-revision` for every pre-existing revision at the address and
refuses. No publishing root is created that way; the refusal is the honest
reading if one is.

**Step 0, the intent door** — `_open_publication(writer, resolver, *, view,
destination, clock)`, under the written root's `writer._operation`, after
`authority.require` for `RequiredCapabilities.publishes()`: resolve `view`
to its one tip (`divergent-view` refuses); capture every other mount's
anchor from its current head — those roots are not locked and may advance,
which is why the anchor, not the live read, bounds them; compute
`binding_tips` by `standing_at` with the written root bounded at its
current tip, and `marker_tips` (below); build the `PublishIntent`; append it
through `_append_operation_intent`'s port, extended to take a pre-encoded
payload. In one process the lock admits no entry between the tip read and
the append, so the frozen tips equal `standing_at` recomputed at the
intent's own position; across processes that holds only under the
single-writer obligation (decision 11), which is why the binding door
recomputes.

**`marker_tips`** is one projection read at the position: the markers the
present `binding_tips` revisions bind, plus the **standing orphans**. An
orphan is the `(corpus_id, marker)` pair of a publish attempt at this
`(view, destination)` whose marker was **remotely revealed** and never
bound: every `publish` refusal report whose outcome carries
`remotely_revealed: true` (§7), whatever its refusal reason. An orphan is
**retired** once any publish whose marker was shared — a `Bound` report, or
a refusal carrying `remotely_revealed: true` — fulfils an intent whose
`marker_tips` names the pair: that attempt's marker is a byte-function of its
intent (§4), so it supersedes exactly those pairs, and it has reached some
recipient. A locally revealed refusal's marker was never shared and neither
creates nor retires an orphan (layer design §6.1 step 8). Markers live in
destination corpora, which the resolver need not mount, so everything is
read where the source holds it, and by the same chain-first rule: in
**every mounted root, within its bound**, the publish intents for this
`(view, destination)` are decoded from the chain, each one's committed
fulfilling registration names the report path it created, and that report's
bytes are read and matched against the registration exactly as a revision's
are — a missing, mismatched or malformed report refuses with the same three
reasons, so a lost refusal report can never silently drop an orphan. A
project that moved corpora keeps its earlier publish reports in the root it
moved from. Orphans are derived, never stored.

**Step 8, the binding door** — `_bind_publication(writer, resolver, intent,
*, corpus_id, marker, artifact, remotely_revealed)`, through
`execute_fulfilling_guarded`. The guard recomputes, at the intent's
position, both `standing_at` for the binding address and the whole
`marker_tips` projection, and

- a `PositionRefused` → the refusal report alone, outcome
  `evidence-refused` with the reason;
- a recomputed binding-tip set that does not contain every `binding_tips`
  member → the refusal report alone, outcome `predecessor-not-standing`;
- a recomputed binding-tip set or `marker_tips` unequal to the intent's
  otherwise → `evidence-refused`, `tips-disagree`: the intent froze a
  reading its own position does not yield;
- otherwise → the binding revision and the success report in one fulfilling
  transaction, outcome `bound`.

Every refusal carries `corpus_id`, `marker` and `remotely_revealed`, so a
remotely revealed attempt refused for any reason is an orphan the next
publish supersedes. A predecessor superseded *after* the intent's position
is still present and standing at it, so the attempt commits and two tips
stand — the lawful sibling state of the coordination design §4.3. The
at-commit general rule is not applied to this kind: the binding door is its
only door. The second slice calls both doors; this slice's tests call them
directly.

## 7. The act-report amendment

`OPERATION_KINDS` gains `publish` (nine kinds; decision 10 keeps it out of
the domainless intent). One entry kind, `publication-binding`, in the stored
form every entry takes, `{kind, subject, outcome}`: `subject` is the binding
address's canonical `coord:` string, and the operation's `event_token` is
the report's own, not repeated. Three outcomes:

| outcome | fields |
|---|---|
| `bound` | `binding` (the revision uid), `corpus_id`, `marker` |
| `predecessor-not-standing` | `corpus_id`, `marker`, `remotely_revealed`, `tips` (the recomputed set, ascending) |
| `evidence-refused` | `corpus_id`, `marker`, `remotely_revealed`, `reason`: one of §6's nine, or `tips-disagree` |

They join `_ALLOWED_OUTCOMES`, `_ENTRY_KINDS`, `_OUTCOME_TYPES`, the stored
mirror `stored._REPORT_ENTRY_OUTCOMES` (which gains validators for a boolean
and for a list of hex strings) and `act_report_facet`'s kind check. A
`publish` report carries exactly one such entry in this slice. The
act-report design gains an "Amended 2026-09-22 (publication records, cut
39)" note in §2 and §6 item 3.

## 8. What does not change

Every existing kind's intent bytes, and `completion`; `standing_tips`; the
general at-commit rule and both ordinary family doors for the eight existing
kinds; `World.admit`, `admit_arrival`, and every lifecycle function in
`root.py`; the base contract and both `CONTRACT.yaml` copies; the TypeScript
parity artifact; the reproduction driver. No stored record of an existing
kind changes a byte. `OperationIntent` and the domainless decoder branch
change only by decision 10's refusal of `publish`.

## 9. Shared files, under roadmap concurrency rule 3

Rewritten by every lane: `errors.py`, the ledger, the roadmap,
`docs/guide/open-questions.md`, `python/tests/test_designs_corpus.py`.
Named beyond those: `coordination.py`, `corpus.py`, `permit.py`,
`profile.py` (the shipped-coordination loader), `report.py`, `stored.py`,
`intents/shapes.py`, `root.py` (the moment seam),
`python/tests/coordination_fixtures.py`, `test_permit.py`,
`test_permit_boundary.py` and `test_permit_entry_points.py`. No other kernel lane is open.

## 10. Guarantee rows

The ledger gains a **Y table** (publication), rows Y1–Y4 here; the second
slice appends its own. W17's intent-position arm is rewritten to this
design's evidence (decision 4) — the frozen cut-14 text's "pure function of
a constructed chain prefix" is superseded by citation, not edited.

| row | guarantee |
|---|---|
| **W17-p** | the binding revision's predecessors are judged at the intent's position by §6: a tip superseded before the position (reachable only by a second writer, decision 11) → `predecessor-not-standing`, report alone; superseded between intent and commit → commits, two tips; the present revisions are the chain's inventory at each root's bound — a revision past its anchor, or unsettled, is absent from it, and an inventoried revision whose file is missing, mismatched or malformed refuses; the resolver's mount order does not move the anchors or the tips |
| **Y1** | version 2 declares `publication` and `publication-binding`; a version-1 pin authorizes neither; every ordinary door (`add`, `import_bundle`, `mint_coordination`, `revise_coordination`) refuses both; neither enters a world-index map or moves a `belief_input_digest` |
| **Y2** | both records are byte-functions of the intent and the named arguments; `marker_consistent` refuses a marker whose uid, address or id disagrees with its own `event_token`, view and destination |
| **Y3** | the publish intent decodes by its domain and qualifies only by a `publish` report with its token; a malformed payload under the domain, and a bare domainless `publish` triple, are audit findings; every other kind's intent is byte-unchanged |
| **Y4** | step 8 is all-or-nothing: a binding revision never exists without its success report, a refusal writes its report alone, and every `PositionRefused` reason refuses with no binding; a remotely revealed attempt refused for any reason is an orphan in the next intent's `marker_tips`, retired once a shared publish carrying it closes |

## 11. Testing and the cut

### 11.1 Unit — portable

- the contract: both versions load; v2's succession check passes against
  v1; the v1 identity equals the former fixture's; `compile_profile` over
  v2 activates the two kinds; `composite`/`composes` are spellable in a v2
  view query and refused under v1;
- the content rules: each field of §3's table accepted and each malformed
  form refused, one row per field;
- the factory: byte-equality under one intent, identity recomputation,
  `marker_consistent`'s refusal table, the two addresses distinct for one
  `(view, destination)`, and one address for two spellings of one local
  directory;
- the intent: round-trip, strict ordering, every malformed field, dispatch
  in `decode_intent`, a domainless `publish` triple decoding `malformed`,
  `OperationIntent("publish", …)` refused, `mismatch` against wrong-kind and
  wrong-token reports;
- permits: `coordination()` excludes both kinds; `publishes()` constructs
  and names exactly the `publish` family over `publication-binding` and
  `corpus-write` over `act-report`, and `scoped_authority` binds it; each
  ordinary route naming `publish` refuses with `a requirement names only
  command-reachable families` — `for_kinds(["publication-binding"], …)`,
  direct construction over `{publish}`, and the kernel permit plus one
  kind; `KERNEL_REQUIREMENTS` holds exactly one permit;
- `standing_at` over a fake `MomentSeam`: the inventory's replay (create,
  pending, rolled back, retry after rollback, removal → `history-violated`),
  each refusal, the anchored-past exclusion, the between-intent-and-commit
  sibling, and the orphan fold with and without retirement, local and
  remote reveals.

### 11.2 Acceptance — `test_publication_records_acceptance.py` (new)

On the certified tuple, over two mounted roots whose path order is the
reverse of their `corpus_id` order, one arm per declaration unit, each
ending `_durably`. The plan's Task 0 freezes the unit list; this spec fixes
the rows and the arms each must hold:

| unit | row | assertion |
|---|---|---|
| W17-p-a | W17 | a port wrapper standing in for a second writer commits a supersession of the tip between step 0's tip read and its `append_intent`: the binding door refuses `predecessor-not-standing`, report alone, `completion` closed, no binding |
| W17-p-b | W17 | the same supersession committed after the intent: the binding commits; `resolve` answers `divergent-view` naming both tips; one repair revision restores one tip |
| W17-p-c | W17 | a revision written in the other root after its anchor is not present at the position; the same revision before the anchor is |
| W17-p-d | W17 | two resolvers over the same roots in both mount orders freeze the same `binding_tips`, `marker_tips` and anchors, and the anchors are in `corpus_id` order |
| W17-p-e | W17 | B supersedes A before the intent; B's file is then deleted → `revision-missing`, and overwritten with other bytes → `revision-mismatch` — never a binding over A; a raw-written revision at the address with no registration → `unregistered-revision` |
| W17-p-f | W17 | a transaction in the other root that fails and rolls back after its registration: its file, if left, is classified by the rolled-back registration — not present, no refusal — and a retry that commits is present once, not ambiguous. The plan's Task 0 establishes a durable way to make the engine register and then roll back a transaction (an effect-time precondition failure, for one); if the engine offers none short of `persistence-cut`'s kill-at-stage harness, this arm is declared unrun and W17 is reported **partial**, not closed |
| Y1-a | Y1 | a v1-pinned root refuses both kinds; a v2-pinned root's ordinary doors refuse both |
| Y1-b | Y1 | a binding and a marker leave the world-index maps and a belief answer's `belief_input_digest` unchanged |
| Y2-a | Y2 | under a fake clock that advances on every read, the binding the door commits is byte-equal to `binding_record` called on the intent decoded back from the chain |
| Y3-a | Y3 | the audit reads a publish intent with its report as fulfilled, without as unfinished, and a malformed domain payload as a finding |
| Y4-a | Y4 | a refusing guard's fallback and a success each submit exactly one fulfilling execution (the counting port of cut 38's T2-h), and the refusal leaves no binding revision on disk |
| Y4-b | Y4 | a remotely revealed `evidence-refused` attempt's pair appears in the next intent's `marker_tips`; once that publish binds, the intent after it does not carry the pair; a locally revealed refusal's pair never appears |
| Y4-c | Y4 | a remotely revealed refusal report's file deleted → the next intent door refuses `revision-missing` rather than dropping the orphan |

### 11.3 N2 sabotages — `n2_arms_cut39.py`

One sabotage per unit, each chosen so the unit's check sees it:

| unit | sabotage |
|---|---|
| W17-p-a | the guard trusts the intent's `binding_tips` instead of recomputing |
| W17-p-b | the guard bounds the written root at its current tip, so the post-intent supersession refuses |
| W17-p-c | the other roots' bound ignores the anchor and reads their current heads |
| W17-p-d | the anchors ordered by mount path instead of `corpus_id` |
| W17-p-e | the present set taken from the resolver's live read instead of the chain's inventory |
| W17-p-f | rolled-back registrations counted in the inventory's replay |
| Y1-a | `revise_coordination`'s `KindNotMintedHere` check removed |
| Y1-b | the coordination exclusion dropped for `publication-binding` |
| Y2-a | the factory reads the clock for `at` |
| Y3-a | the domain dispatch removed from `decode_intent` |
| Y4-a | the fallback plan written beside the success plan instead of in its place |
| Y4-b | the fold counts only `predecessor-not-standing` refusals as orphans |
| Y4-c | the fold skipping a publish intent whose report file is missing |

The plan fixes the declared accounting (13 arms, 13 units, 5 rows as drafted
here: W17, Y1–Y4).

### 11.4 The cut

`docs/designs/<freeze date>-conformance-cut-39.md`, dated by the commit that
freezes it after review; `tools/cut39_acceptance.py` with
`PREFIX_RUNNERS = ("cut38_acceptance.py",)` and `PHASE_MODULES =
("test_publication_records_acceptance.py", "test_n2_cut39.py")`; the
`test_recent_cut_acceptance.py` row with the declared arm, unit and
guarantee-row counts and the guarantee-rows-exercised line; the results
record. `root.py` stays the one `atoms` importer: the `FileState`
comparison is the moment seam's, reached through a seam callable.
`_bind_publication` calls `execute_fulfilling_guarded`, an inventoried write
primitive, so it joins `WRITE_ENTRY_POINTS` under the `publish` family and
gains a `Case` in `test_permit_entry_points.py`'s `CASES`; the intent door
writes only through `_append_operation_intent`, already inventoried.

## 12. Documentation amendments

- Coordination design: a note beside §11.6 recording that the evidence
  shape landed here, that W17-p replaces the constructed-prefix arm, and
  that `predecessor-not-standing` is reachable only across processes
  (decision 11).
- Layer design §6.1, notes at the sentences they qualify:
  - step 0: the tips are frozen by `standing_at` at the intent's position
    with anchors (decision 3), not "from the chain prefix" alone; and the
    intent now carries the view, destination and tips, so "the view,
    destination and request identity cannot be reconstructed from it" is
    narrowed to what it still lacks — the pins, the epoch and the staging
    identities — and an intent with no request record is still never
    resumed;
  - the marker's "relations are the selection" and its `supersedes` become
    facet fields (decision 5), and the marker and binding hold separate
    addresses (§4);
  - step 8: every refusal carries the orphan fields, and an orphan is
    retired by a shared publish's intent (§6);
  - §4.1's two-rule text cites this slice.
- Act-report design §2 and §6 item 3: the `publish` kind and its one entry.
- Ledger: the Y table (Y1–Y4 open, then closed at the results record); W17
  closes; `publish` stays in Current state with the second slice's
  remainder.
- Roadmap: re-ranked at cut 39; `publish` stays off-path row 1, its
  remainder named.
- `docs/guide/foundations.md` where it states the intent-position rule.

## 13. Task linkage

`beliefs-1a5157` stays the lane task. This slice is its child
`beliefs-d7d7d1`, carrying `--spec publication-records`; the plan's
`### Task N:` headings become that child's children. The second slice is
`beliefs-328507`, planned, depending on this one. beliefs-c80d8c (the
`composite`/`composes` query amendment) closes with this slice's results
record.

## 14. Limitations

1. **Neither door has a public route.** Nothing but tests calls them until
   the second slice's act does; a session cannot publish.
2. **No marker is written anywhere.** The factory is tested; minting one in
   a staging corpus is the second slice's step 2.
3. **The moment seam reads whole chains.** Placement cost is linear in
   chain length per mounted root per judgment; no index is built.
4. **Anchors bind only mounted roots.** A binding revision or publish report
   held in a root the resolver does not mount is invisible to the judgment,
   exactly as it is to the at-commit rule today.
5. **A root populated before its genesis refuses** (`unregistered-revision`,
   §6), rather than trusting files no registration covers.
6. **The judgment reads every inventoried revision's bytes** at the address
   in every mounted root, and every publish report for the
   `(view, destination)`; it is exact and not cheap.

## 15. Open questions this slice files

None new. The request record, the selection snapshot, and orphan semantics
for transports are the second slice's by decision 1.

## 16. Review log

- 2026-09-22 — drafted.
- 2026-09-22 — first review, twelve findings, all taken: the moment seam
  answers four values, so an unsettled write in an unlocked root is not
  present rather than a refusal, and two committed registrations refuse as
  a value (§6); every step-8 refusal carries the orphan fields and an orphan
  is retired by any shared publish's intent (§6, §7); the marker holds its
  own address (§4); `predecessor-not-standing` is stated as the detection of
  a broken single-writer obligation, with an injected second writer as its
  arm (decision 11, §11.2); every unit has a sabotage its check sees
  (§11.3); `publish` opens only through its domain intent and `mismatch`
  gains its branch (decision 10, §5); the permit gaps are closed (decision
  7); `_bind_publication` joins `WRITE_ENTRY_POINTS` (§11.4); `marker_tips`
  is recomputed by the guard; the fold reads every mounted root, and
  `chain-absent` joins the refusals (§6); the entry takes the stored
  `{kind, subject, outcome}` form (§7); the second slice's remaining step-0
  refusals and the layer design's stale sentences are named (§1, §12).
- 2026-09-22 — user review, four findings. Two were already taken at the
  first review (the marker's own address; orphan fields on every refusal).
  Two are new and taken: presence is now the chain's inventory at each
  root's bound, with every inventoried revision's bytes required present
  and matching, removals refused as `history-violated`, and files the chain
  does not account for classified by a chain re-read under the engine's
  write-ahead order — so a vanished or corrupted superseding revision
  refuses instead of resurrecting its predecessor (§6, W17-p-e, W17-p-f);
  the orphan fold reads publish reports by the same rule (§6, Y4-c); and
  the marker carries its canonical destination, so `marker_consistent`
  needs nothing a recipient cannot hold (§3, §4).
- 2026-09-22 — user re-review: the four findings resolved; one more, taken:
  `RequiredCapabilities.__post_init__` refuses non-command-reachable
  families, so `publishes()` could not construct. A closed
  `KERNEL_REQUIREMENTS` exception admits exactly the publication permit
  while every ordinary route naming `publish` still refuses, with unit
  checks for both outcomes (decision 7, §11.1).
