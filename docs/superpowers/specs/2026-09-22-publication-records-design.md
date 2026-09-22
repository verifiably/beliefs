# Publication records — the coordination amendment, the publish intent, and the intent-position rule

**Slice of:** `2026-08-29-user-and-autonomy-layer-design.md` §4.1, §6.1 steps 0
and 8, §6.2 and §8 item 5 — sub-project 5's `beliefs` half, first of two slices
**Boundary:** `publish` — W17's publication-binding intent-position arm, and the
governed publication records (`../../designs/2026-08-03-redesign-adoption-ledger.md`,
Current state)
**Task:** `beliefs-1a5157` (lane task); this slice's child is filed with the spec
**Lane:** `world-read`, its head since cut 38 (roadmap §Lanes)
**Cut:** 39, off the path (roadmap tier 1, off-path row 1)
**Status:** draft, 2026-09-22

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
that answers item 6, staging, head export, replication, restore, the
transport seam, the recovery table, and marker-required arrival.

It closes **W17 in full** and opens and closes the publication-record rows
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
   intent and nothing else; the ordinary `mint_coordination` and
   `revise_coordination` refuse both kinds (`KindNotMintedHere`, the
   `EXCLUDED_MUTATION_KINDS` pattern). **Rejected:** an `uid=` parameter on
   `revise_coordination`. It would let any caller mint a revision whose
   identity claims a publish that never happened.

7. **A `publish` act family.** `ACT_FAMILIES` gains `publish`; `KIND_ACTS`
   maps `publication` and `publication-binding` to `{"publish"}` alone, and
   the step-0 and step-8 doors require it. It is not command-reachable
   (`COMMAND_REACHABLE_FAMILIES` is unchanged): `science`'s write classes
   reach it by `science`'s own design. **Rejected:** minting both kinds under
   `corpus-write`. A session permitted to write tasks could then mint a
   binding.

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
   encoding is what the binding address and the request identity digest.
   **Rejected:** an opaque string. Two spellings of one directory would be
   two bindings, and two sibling histories for one destination.

## 3. The coordination contract, version 2 — `beliefs/contracts/coordination/`

Version 2 is version 1 plus:

- `query_vocabulary.kinds` gains `composite`; `query_vocabulary.relations`
  gains `composes` (the coordination design §5.1 note of 2026-09-16);
- `kinds.publication`: `fields: [name, body, author, at, event_token,
  published_from, selection, supersedes_markers]`, `query_versions: []`;
- `kinds.publication-binding`: `fields: [name, body, author, at,
  event_token, view, destination, corpus_id, marker, artifact]`,
  `query_versions: []`.

`check_coordination_succession` already admits added kinds and query
vocabulary. The hard-coded kind lists move with the contract:
`coordination.COORDINATION_KINDS` and `permit._COORDINATION_KINDS` gain the
two kinds (the test that holds `KIND_ACTS`' key set to `stored.WORLD_KINDS ∪
COORDINATION_KINDS` keeps them honest), and `corpus.EXCLUDED_MUTATION_KINDS`
and `_refuse_family_kinds` refuse them on every ordinary door.
`_validated_coordination_content` gains a closed rule per kind:

| field | `publication` | `publication-binding` |
|---|---|---|
| `name`, `body` | the literal strings `publication`, `""` | `publication-binding`, `""` |
| `event_token` | 32 lowercase hex | 32 lowercase hex |
| `published_from` | `{world_id, epoch, view, view_revision}`: 32-hex, 64-hex, canonical `coord:` address, 32-hex | — |
| `selection` | non-empty list of record ids, strictly ascending | — |
| `supersedes_markers` | list of `[corpus_id, marker uid]`, strictly ascending, possibly empty | — |
| `view` | — | canonical `coord:` address, unpinned |
| `destination` | — | the §2 decision 9 union, canonical |
| `corpus_id`, `marker` | — | 32-hex each |
| `artifact` | — | 64-hex head-artifact content identity |

A marker carries **no relations**; a binding carries exactly its
`supersedes` relations to `binding_tips`. Neither is a belief input: both
are coordination role, excluded from world-index maps and
`belief_input_digest` by cut 14's existing rule, which the acceptance module
reads once for each (Y1).

## 4. The records and their factory — `beliefs/publication.py`

```python
@dataclass(frozen=True)
class Destination:          # decision 9
    type: Literal["local", "remote"]
    locator: str

def binding_address(view: CoordinationAddress, destination: Destination) -> CoordinationAddress
def marker_record(intent: PublishIntent, *, world_id, epoch, view_revision, selection) -> Node
def binding_record(intent: PublishIntent, *, corpus_id, marker, artifact) -> Node
def marker_consistent(node: Node) -> bool
```

- **The binding address** is `(view.project, local)` with `local =
  digest("science.publication-binding-address.v1", [view.project,
  view.local, destination])[:32]`. Every publish of one view to one
  destination shares it, so step 0 finds the tips without a lookup table, and
  the first publication is simply a revision with no predecessors.
- **Identities.** A record's uid is `digest(<domain>, event_token)[:32]`
  with `science.publication.v1` for the marker and
  `science.publication-binding.v1` for the binding; the id follows
  `coordination_revision`'s form from the address and the uid. The marker's
  address is the binding address, so one address carries both kinds'
  histories, which the continuity rule (coordination design §4.3) keeps
  apart by kind.
- **Content.** `author` is the intent's actor and `at` the intent's `at`
  (§5): the factory reads no clock and draws no randomness, so every byte
  is a function of the intent and the named arguments. `marker_record`'s
  `supersedes_markers` is the intent's `marker_tips`; `binding_record`'s
  relations are the intent's `binding_tips`.
- **`marker_consistent`** recomputes the uid, the id and the address from
  the marker's own `event_token`, `published_from.view` and the destination
  its caller supplies, and answers `False` on any difference. Arrival calls
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
`shapes.mismatch` qualifies it by a `ReportEvidence` whose operation is
`publish` and whose token matches: `completion` needs no new branch, only
the domain dispatch and `publish` in `OPERATION_KINDS`.

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
bound is the position of the entry `position` (the intent's digest); every
other root's bound is `events.place(view, anchor)`'s head. A revision at
`address` held in root *R* is **present at the position** iff
`moments.created(R, relative_path, bytes)` names a registration whose
`moment` is at or before *R*'s bound. `standing_at` returns
`standing_tips` over the present revisions — the family's one tip rule,
unchanged, over a filtered set.

`MomentSeam.created` lives in `root.py` beside the log seam: it reads the
root's well-formed chain and returns the moment of the committed
registration whose `initial` holds the path `ABSENT` and whose `final`
holds a `FileState` with the bytes' content hash, or `None`. Two such
registrations cannot exist for a create-only path in a well-formed chain;
if they do, the seam raises rather than choosing.

It refuses, as a value, when the evidence does not bind:

| `PositionRefused` reason | when |
|---|---|
| `mounts-changed` | the resolver's mounted corpus ids differ from the written root plus the anchors' |
| `anchor-unplaced` | `place` answers `None`: another genesis, or a head no longer in the chain |
| `chain-malformed` | a mounted root's chain is not well-formed |
| `unregistered-revision` | a revision is held in a root whose chain has no creating registration for it at any position — a raw write, never admitted as present |

**Step 0, the intent door** — `_open_publication(writer, resolver, *, view,
destination, clock)`, under the written root's `writer._operation`:
resolve `view` to its one tip (`divergent-view` refuses); capture every other
mount's anchor from its current head — those roots are not locked and may
advance, which is why the anchor, not the live read, bounds them; compute `binding_tips` by
`standing_at` with the written root bounded at its current tip, and
`marker_tips` as the markers those tips bind plus the standing orphans
(below); build the `PublishIntent`; append it through
`_append_operation_intent`'s port, extended to take a pre-encoded payload.
The written root's lock admits no entry between its tip and the append, and
the other roots are bounded by their anchors, so the frozen tips are exactly
`standing_at` recomputed at the intent's own position — which is what the
binding door checks.

**Standing orphans** are the `(corpus_id, marker)` pairs of every `publish`
refusal report at this binding address whose outcome is
`predecessor-not-standing` with `remotely_revealed: true` (§7), present at
the position by the same registration-moment rule, minus every pair named in
the `marker_tips` of an intent that some present `Bound` report at the
address fulfills. Markers live in destination corpora, which the source's
resolver need not mount, so retirement is read where the source holds it:
a bound publish's marker is a byte-function of its intent (§4), so it
supersedes exactly that intent's `marker_tips`. Orphans are derived, never
stored.

**Step 8, the binding door** — `_bind_publication(writer, resolver, intent,
*, corpus_id, marker, artifact, remotely_revealed)`, through
`execute_fulfilling_guarded`: the guard recomputes `standing_at` for the
binding address at the intent's position, and

- a `PositionRefused` → the refusal report alone, outcome
  `evidence-refused` with the reason;
- a recomputed tip set that does not contain every `binding_tips` member →
  the refusal report alone, outcome `predecessor-not-standing`, carrying
  `corpus_id`, `marker` and `remotely_revealed`;
- a recomputed set unequal to `binding_tips` otherwise → `evidence-refused`,
  `tips-disagree`: the intent froze a set its own position does not yield;
- otherwise → the binding revision and the success report in one fulfilling
  transaction, outcome `bound`.

A predecessor superseded *after* the intent's position is still present and
standing at it, so the attempt commits and two tips stand — the lawful
sibling state of the coordination design §4.3. The at-commit general rule is
not applied to this kind: the binding door is its only door. The second
slice calls both doors; this slice's tests call them directly.

## 7. The act-report amendment

`OPERATION_KINDS` gains `publish` (nine kinds). One entry kind,
`PublicationBindingEntry(address, event_token, outcome)`, with three outcomes:

| outcome | fields |
|---|---|
| `Bound` | `binding` (the revision uid), `corpus_id`, `marker` |
| `PredecessorNotStanding` | `corpus_id`, `marker`, `remotely_revealed: bool`, `tips` (the recomputed set) |
| `EvidenceRefused` | `reason`: one of §6's four, or `tips-disagree` |

They join `_ALLOWED_OUTCOMES`, `_ENTRY_KINDS`, `_OUTCOME_TYPES`, the stored
mirror `stored._REPORT_ENTRY_OUTCOMES` and `act_report_facet`'s kind check.
A `publish` report carries exactly one such entry in this slice. The act-report
design gains an "Amended 2026-09-22 (publication records, cut 39)" note in
§2 and §6 item 3.

## 8. What does not change

`OperationIntent`, its decoder branch, and every other kind's intent bytes;
`standing_tips`; the general at-commit rule and both ordinary family doors
for the eight existing kinds; `World.admit`, `admit_arrival`, and every
lifecycle function in `root.py`; the base contract and both `CONTRACT.yaml`
copies; the TypeScript parity artifact; the reproduction driver. No stored
record of an existing kind changes a byte.

## 9. Shared files, under roadmap concurrency rule 3

Rewritten by every lane: `errors.py`, the ledger, the roadmap,
`docs/guide/open-questions.md`, `python/tests/test_designs_corpus.py`.
Named beyond those: `coordination.py`, `corpus.py`, `permit.py`,
`profile.py` (the shipped-coordination loader), `report.py`, `stored.py`,
`intents/shapes.py`, `root.py` (the moment seam), and
`python/tests/coordination_fixtures.py`. No other kernel lane is open.

## 10. Guarantee rows

The ledger gains a **Y table** (publication), rows Y1–Y4 here; the second
slice appends its own. W17's intent-position arm is rewritten to this
design's evidence (decision 4) — the frozen cut-14 text's "pure function of
a constructed chain prefix" is superseded by citation, not edited.

| row | guarantee |
|---|---|
| **W17-p** | the binding revision's predecessors are judged at the intent's position by §6: superseded before the position → `predecessor-not-standing`, report alone; superseded between intent and commit → commits, two tips; a revision past its root's anchor is not present; swapping the resolver's mount order changes nothing |
| **Y1** | version 2 declares `publication` and `publication-binding`; a version-1 pin authorizes neither; every ordinary door (`add`, `import_bundle`, `mint_coordination`, `revise_coordination`) refuses both; neither enters a world-index map or moves a `belief_input_digest` |
| **Y2** | both records are byte-functions of the intent and the named arguments: two mints from one intent are byte-equal; `marker_consistent` refuses a marker whose uid, id or address disagrees with its own `event_token`, view and destination |
| **Y3** | the publish intent decodes by its domain, qualifies only by a `publish` report with its token, and a malformed payload under the domain is an audit finding; every other kind's intent is byte-unchanged |
| **Y4** | step 8 is all-or-nothing: a binding revision never exists without its success report, a refusal writes its report alone, and every `PositionRefused` reason refuses with no binding; standing orphans enter the next intent's `marker_tips` and leave it once a publish carrying them binds |

## 11. Testing and the cut

### 11.1 Unit — portable

- the contract: both versions load; v2's succession check passes against
  v1; the v1 identity equals the former fixture's; `compile_profile` over
  v2 activates the two kinds; `composite`/`composes` are spellable in a v2
  view query and refused under v1;
- the content rules: each field of §3's table accepted and each malformed
  form refused, one row per field;
- the factory: byte-equality under one intent, identity recomputation,
  `marker_consistent`'s refusal table, `binding_address` over two spellings
  of one local directory;
- the intent: round-trip, strict ordering, every malformed field, dispatch
  in `decode_intent`, `mismatch` against wrong-kind and wrong-token reports;
- `standing_at` over a fake `MomentSeam`: the four refusals, the
  anchored-past exclusion, the between-intent-and-commit sibling, and the
  orphan fold.

### 11.2 Acceptance — `test_publication_records_acceptance.py` (new)

On the certified tuple, over two mounted roots, one arm per declaration
unit, each ending `_durably`. The plan's Task 0 freezes the unit list;
this spec fixes the rows and the arms each must hold:

| unit | row | assertion |
|---|---|---|
| W17-p-a | W17 | a tip superseded in the written root before the intent → `predecessor-not-standing`, report alone, `completion` closed, no binding |
| W17-p-b | W17 | the same supersession committed after the intent → binding commits; `resolve` answers `divergent-view` naming both tips; one repair revision restores one tip |
| W17-p-c | W17 | a revision written in the *other* root after its anchor is not present at the position; the same revision before the anchor is |
| W17-p-d | W17 | the mount order swapped yields the same `binding_tips`, `marker_tips` and anchors |
| Y1-a | Y1 | a v1-pinned root refuses both kinds; a v2-pinned root's ordinary doors refuse both |
| Y1-b | Y1 | a binding and a marker leave the world-index maps and a belief answer's `belief_input_digest` unchanged |
| Y2-a | Y2 | the binding the door commits is byte-equal to `binding_record` called on the intent decoded back from the chain, and to a second such call |
| Y3-a | Y3 | the audit reads a publish intent with its report as fulfilled, without as unfinished, and a malformed domain payload as a finding |
| Y4-a | Y4 | a refusing guard's fallback and a success each submit exactly one fulfilling execution (the counting port of cut 38's T2-h) |
| Y4-b | Y4 | a remotely revealed refusal's pair appears in the next intent's `marker_tips`; once that publish binds, the intent after it does not carry the pair |
| Y4-c | Y4 | a raw-written binding revision with no creating registration → `unregistered-revision`, no binding |

### 11.3 N2 sabotages — `n2_arms_cut39.py`

At least one sabotage per unit: the position bound replaced by the root's
current tip (W17-p-a, -c); the guard reading at commit instead of at the
position (W17-p-b); the anchors sorted by root path (W17-p-d); a door's
kind refusal removed (Y1-a); the coordination exclusion dropped for one kind
(Y1-b); the clock read in the factory (Y2-a); the domain dispatch removed
(Y3-a); the fallback written beside the plan (Y4-a); the orphan fold's
retirement removed (Y4-b); the seam answering "present" for a missing
registration (Y4-c). The plan fixes the declared accounting.

### 11.4 The cut

`docs/designs/<freeze date>-conformance-cut-39.md`, dated by the commit that freezes it after review;
`tools/cut39_acceptance.py` with `PREFIX_RUNNERS = ("cut38_acceptance.py",)`
and `PHASE_MODULES = ("test_publication_records_acceptance.py",
"test_n2_cut39.py")`; the `test_recent_cut_acceptance.py` row with the
declared arm, unit and guarantee-row counts and the guarantee-rows-exercised
line; the results record. `root.py` stays the one `atoms` importer: the
`FileState` comparison is the moment seam's, reached through a seam
callable. The intent door writes only through `_append_operation_intent`
and the binding door only through the port's fulfilling execution; if the
plan finds either calling a write primitive directly, it joins
`WRITE_ENTRY_POINTS` and gains a `Case` in `test_permit_entry_points.py`.

## 12. Documentation amendments

- Coordination design: a note beside §11.6 recording that the evidence
  shape landed here, and that W17-p replaces the constructed-prefix arm.
- Layer design §6.1 step 0: a note that the tips are frozen by `standing_at`
  at the intent's position with anchors (decision 3), not "from the chain
  prefix" alone; §4.1's two-rule text cites this slice.
- Act-report design §2 and §6 item 3: the `publish` kind and its one entry.
- Ledger: the Y table (Y1–Y4 open, then closed at the results record); W17
  closes; `publish` stays in Current state with the second slice's
  remainder.
- Roadmap: re-ranked at cut 39; `publish` stays off-path row 1, its
  remainder named.
- `docs/guide/foundations.md` where it states the intent-position rule.

## 13. Task linkage

`beliefs-1a5157` stays the lane task. This slice files a child carrying
`--spec publication-records`, and the plan's `### Task N:` headings become
that child's children. The second slice is filed as a planned sibling
depending on this one. beliefs-c80d8c (the `composite`/`composes` query
amendment) closes with this slice's results record.

## 14. Limitations

1. **Neither door has a public route.** Nothing but tests calls them until
   the second slice's act does; a session cannot publish.
2. **No marker is written anywhere.** The factory is tested; minting one in
   a staging corpus is the second slice's step 2.
3. **The moment seam reads whole chains.** Placement cost is linear in
   chain length per mounted root per judgment; no index is built.
4. **Anchors bind only mounted roots.** A binding revision held in a root the
   resolver does not mount is invisible to the judgment, exactly as it is to
   the at-commit rule today.

## 15. Open questions this slice files

None new. The request record, the selection snapshot, and orphan semantics
for transports are the second slice's by decision 1.

## 16. Review log

- 2026-09-22 — drafted.
