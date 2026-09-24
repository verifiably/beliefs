# The publish act, local — request, snapshot, staging, export, reveal, recovery and arrival

**Slice of:** `2026-08-29-user-and-autonomy-layer-design.md` §6.1 steps 0–6, 8
and 9, the recovery table's local rows, §6.3's marker-required arrival, and
§8 item 5. This is the second of three slices of sub-project 5's `beliefs`
half.
**Boundary:** `publish`: the governed publication act
(`../../designs/2026-08-03-redesign-adoption-ledger.md`, Current state)
**Task:** `beliefs-328507`, child of the lane task `beliefs-1a5157`
**Lane:** `world-read`, its head since cut 38 (roadmap §Lanes)
**Cut:** 40, off the path (roadmap tier 1, off-path row 1)
**Status:** draft, 2026-09-23

## 1. What this slice is

Cut 39 built the two points where a publish writes its source root: the
step-0 intent door (`_open_publication`) and the step-8 binding door
(`_bind_publication`). Both live in `beliefs/publication_doors.py` and have no
public route. This slice builds the act that runs between and around them,
for a **local destination**: a directory the publisher controls.

The act is a function a caller invokes. The caller is `science`'s
`publish` command, which arrives in `science`'s own design; here it is the
tests. After this slice, a caller holding the publication permit can publish
a view to a local directory. It can resume an attempt that crashed at any
local step, and a second world can admit the published corpus through a
door that requires its marker.

**Split, by the user's decision on 2026-09-23 (§2 decision 1).** Cut 41 takes
what a remote destination adds:
- the transport seam and step 7;
- the remote reveal and the orphans it creates, including cut 39's Ruling 12:
  a remotely revealed marker whose step-8 attempt raised before any effect
  leaves its intent unfinished rather than orphaned;
- the recovery table's remote rows;
- the recipient's `divergent-publication`.

A reading of the tree on 2026-09-23 found six things the act needs and the
kernel lacks:

1. **A retry cannot re-resolve the selection.** `evaluate_query` refuses
   `corpus-drifted` once a contributing corpus's state moves after the
   epoch (`world/selection.py`). `corpus_state_identity` digests every stored
   node (`world/registry.py`), and an epoch keeps no record bytes. Step 8's
   own binding revision and report move the written root's state, and so
   does any task minted there. A retry that re-resolved would be refused
   mid-population.
2. **No closure rule exists.** Nothing in the tree computes a record's
   publication closure, so neither `closure-incomplete` nor the composite
   amendment (layer design §6.1, the 2026-09-16 note) has code.
3. **No door can write a selected record into staging unchanged.**
   - `CorpusWriter.add` refuses a record that carries another actor
     (`_refuse_foreign_closure_actor`) and refuses both publication kinds.
   - `import_bundle` writes the whole bundle in one transaction and mints an
     act-report inside the corpus it writes. That report is a record outside
     the selection, and one transaction leaves no prefix to resume.
4. **No durable create-only write exists outside a root.** The operations
   root and the head artifact's sibling are outside every corpus. Layer
   design §6.1 step 0 defines the mechanism; no code implements it.
5. **The layer design's local export root is the destination directory
   itself.** A second publish of the same view to the same destination would
   then collide with the first. That is impossible under §6.2, where every
   publish mints a fresh corpus and a destination accumulates the chain of
   its revisions (§2 decision 4).
6. **No arrival door requires a marker.** `admit_arrival` serves every
   replica, cut 8's included, and none of those carries a marker.

## 2. Decisions

Each decision names what it rejects.

1. **Local first; remote is cut 41.** This slice closes the act end to end
   for the one destination whose reveal is atomic: `restore_root`'s grant.
   **Rejected:** one slice for every remaining §6.1 step. The records slice
   was 14 arms, and this remainder is larger. Remote transport's unit of
   atomicity and its orphans are a separate reasoning surface. **Also
   rejected:** splitting publisher from recipient. A local publish that no
   world can admit proves nothing about the marker it writes.

2. **The selection is snapshotted at step 0, and population reads only the
   snapshot.** Step 0 evaluates the view's query at the epoch the caller
   names. It then writes the selected records' canonical bytes to
   `<operations root>/publish/<event_token>/selection.v1` using the durable
   create-only write (§4.4). The request freezes the snapshot's digest. Every
   later step, on every retry, reads the records from the snapshot and never
   from a corpus. This is the answer to item 1.
   - **Rejected:** re-resolving at retry. It strands at the first drift.
   - **Also rejected:** populating the staging corpus at step 0, which would
     make staging the snapshot. That is a side effect before the intent, it
     holds the lock across one transaction per record, and it would put the
     request after staging (layer design §6.1 step 0: "before any side
     effect").
   - **And rejected:** carrying the bytes inside the request. The request
     would grow with the selection, and every retry's decode of the small
     frozen inputs would pay for it.

3. **The act uses the caller's current epoch and never builds one.** Step 0
   opens `current_epoch(world)` and evaluates the view against it. A caller
   whose corpora moved since that epoch is refused (`corpus-drifted`, from
   `evaluate_query`) and builds a fresh epoch first. The selection is
   evaluated **before** the written root's lock is taken, since the epoch is
   immutable and the snapshot comes from the view's captured records. So step
   0 never holds a corpus lock and the world lock together.
   - **Rejected:** building an epoch inside the act. That nests the world's
     epoch build inside a corpus act, and it makes what a publish selects
     depend on an epoch the caller never saw, which rules out `science`'s dry
     run (layer design §6.4).

4. **A local destination is a container, and each publication lands at
   `<destination>/<corpus_id>`.** The head artifact's sibling is
   `<destination>/<corpus_id>.head-artifact.v1`, exactly layer design §6.1
   step 5's `<export root parent>/<corpus_id>.head-artifact.v1`. Successive
   publications of one view to one destination accumulate side by side,
   linked by their markers' `supersedes_markers`.
   - **Rejected:** export root = destination directory, the layer design's
     step-4 wording. It admits one publication per destination, ever.
   - A layer-design note records the correction (§14).

5. **Staging is written through two kernel-internal writer doors.**
   `_stage_record` writes one snapshot record, and `_stage_marker` writes the
   factory's marker. Each is a registered transaction on the staging writer,
   with no intent and no report, like `add`. Each is validated against the
   staging pins, and neither refuses a foreign actor: a published record's
   actor is its provenance, as it is in an import.
   - **Rejected:** `add` and `import_bundle`, for item 3's reasons.
   - **Also rejected:** a public `stage` door. Nothing but the act writes a
     staging corpus.

6. **One permit covers the whole act.** `RequiredCapabilities.publishes()`,
   cut 39's one member of `KERNEL_REQUIREMENTS`, widens to what the act does:
   - `publish` over `publication-binding` and `publication`;
   - `corpus-write` over `act-report` and every world kind;
   - `lifecycle`.

   The caller's authority stages, exports and reveals, because the caller is
   the one permitted to publish.
   - **Rejected:** a staging authority the act derives from the caller's
     actor. That is an authority wider than the caller holds, minted by the
     kernel on the caller's behalf.
   - `publish` stays out of `COMMAND_REACHABLE_FAMILIES`.

7. **One terminal report per attempt, with the lifecycle entries in step
   order.** The report fulfils the intent, and an operation has one report.
   It carries a `publication-staging` entry, a `publication-export` entry, a
   `publication-reveal` entry and cut 39's `publication-binding` entry, each
   with its outcome.
   - A terminal refusal **before** step 8 writes the entries reached so far,
     ending with the refusing one, as the report alone in its own fulfilling
     transaction. That report is `staging-corrupt` or `request-corrupt`.
   - **Rejected:** one report per step. The report is what fulfils the
     intent, and an intent is fulfilled once.
   - **Also rejected:** one entry kind whose outcomes are the steps. That
     loses the per-boundary outcome typing that every other kind keeps (T1).

8. **Resumption is by reinvocation, and the recovery table's rows become
   acceptance arms.** `resume_publish(token)` re-runs the step sequence.
   Every lifecycle operation it calls is exact-retry, and its own predicate
   decides whether an earlier attempt was this one (layer design §6.1 step
   1). The classifier inspects only what no predicate answers:
   - population's prefix state;
   - the sibling's presence;
   - the export root's lifecycle state;
   - the intent's completion reading and this attempt's binding revision.

   **Rejected:** a separate code path per table row. Its branches would
   duplicate the predicates they stand in front of.

9. **Resuming requires the intent's actor.** `resume_publish` refuses with
   `ValidationRefused` unless `authority.actor` equals the intent's `actor`,
   and writes nothing. The staging admission runs under the original actor
   (layer design §6.1 step 3), and the report's observer is the intent's
   actor (cut 39).
   - **Rejected:** a terminal refusal on an actor mismatch. That would let
     the wrong session close someone else's publish.

10. **Arrival of a publication is its own door.**
    `admit_publication(world, root, observers)` checks the marker first and
    then calls `admit_arrival` with `ReplicaOf(corpus_id)`. It refuses before
    `admit_arrival` writes anything.
    - **Rejected:** amending `admit_arrival` for every replica. Cut 8's
      replicas carry no marker, and requiring one there would refuse every
      plain replica.

## 3. The act's surface — `beliefs/publish.py` (new)

```python
def publish(
    writer: CorpusWriter,              # the written root: the project's corpus
    resolver: CoordinationResolver,    # its mounts
    world: World,                      # the source world, opened by the caller
    *,
    view: CoordinationAddress,         # unpinned
    destination: Destination,          # type "local" in this slice
    operations_root: Path,
    clock: Callable[[], str],
    seam: MomentSeam,
    port: OperationPort | None = None,
) -> PublishOutcome

def resume_publish(
    writer, resolver, *, event_token: str, operations_root: Path, clock, seam, port=None,
) -> PublishOutcome

def pending_publishes(writer, *, operations_root: Path) -> tuple[str, ...]
```

`PublishOutcome` is a closed union:

| outcome | when |
|---|---|
| `Published(event_token, corpus_id, marker, binding, artifact)` | done (§9) |
| `PublishRefused(event_token, report)` | a terminal refusal on record: step 8's two refusals, or §7's four pre-binding refusals |
| `Unresolved(event_token, reason)` | §9's fail-closed rows, with nothing written |

A refusal before the intent is `PublicationRefused`, raised as an exception
(cut 39's `WriteRefused`) with the new reasons in §4.1. The attempt has no
token yet, so nothing is on record.

`publish` authorizes against `RequiredCapabilities.publishes()` first and
refuses a `remote` destination with `ValidationRefused("remote destinations
arrive in cut 41")`. It then runs step 0 (§4), then steps 1–6, 8 and 9. A
fresh `publish` and a `resume_publish` share one sequence from step 1 on.
`pending_publishes` lists every request under the operations root whose
intent's completion reading is `unfinished`, in ascending token order.

**Operations root.** It is caller-supplied, absolute and normalized, an
existing directory outside every mounted corpus root and outside the world
root. If not, `publish` refuses before any other work with
`PublicationRefused("operations-root-unusable")`. The kernel cannot check
that the actor cannot reach it; that remains the launcher's obligation, like
the single-writer obligation (roadmap row 4). The certified volume applies to
the staging roots, which are `atoms` roots under it (§5), so the operations
root lives on the certified volume in every test.

## 4. Step 0 — selection, refusals, intent, snapshot, request

### 4.1 Before the lock: select and refuse

In order, with nothing written by any refusal:

1. Resolve `view` to its one tip through `resolver`. Refuses
   `view-unresolved` or `divergent-view`, as cut 39's door does. Pin the
   address to the tip's uid, giving `pinned_view`, and read its query with
   `view_query.stored_query`.
2. Open `current_epoch(world)` and `open_world_view(world, epoch)`, then run
   `evaluate_query`. Its `SelectionRefused` propagates unchanged:
   `corpus-drifted`, `corpus-damaged`, `address-unknown` and
   `address-not-present`.
3. `selection.complete` false → `PublicationRefused("selection-incomplete",
   corpus_ids=…)`. A selection that cannot see a covered corpus cannot say
   what it omits.
4. `selection.selected` empty → `empty-selection`.
5. **Closure.** A selected record's publication closure is the set of targets
   of its world-group relations (`stored.WORLD_RELATIONS`). Kernel §4.1 stores
   every role-typed input as a relation, and the facet copies are written from
   the same argument (`stored.py`'s module note), so the relations are the
   whole reference set. A composite's `composes` edges are world relations,
   so the 2026-09-16 amendment needs no rule of its own. Any target outside
   `selection.selected` → `closure-incomplete` with the missing ids ascending.
6. **Pins.** Read each contributing corpus's `captured_manifest` at the epoch.
   - `science_contract` must be identical across them, and `domains` is
     their union. Otherwise `pins-disagree`, naming the corpora and the field.
   - The written root's own manifest must pin the coordination contract at a
     version that declares `publication` (v2 or later, by
     `shipped_coordination`'s lineage). That pin joins the derived `domains`
     and must agree with any contributing corpus that pins it. Otherwise
     `coordination-unpinned` or `pins-disagree`.
7. **Destination.** `destination.locator` must be an existing directory, not
   inside the operations root, any mounted corpus root or the world root.
   Otherwise `destination-unusable`.
8. Build the snapshot bytes in memory from the view's retained records, in
   `selection.selected` order (§4.3).

### 4.2 Under the lock: tips and intent

`_open_publication` gains one keyword, `expected_view: CoordinationAddress`
(pinned). Inside the lock it resolves the view again. If the tip differs from
`expected_view`, it refuses `PublicationRefused("view-revised")` and appends
nothing. The view was revised between the evaluation and the lock, and
freezing the new revision would pair it with the old revision's selection.
Everything else in the door is unchanged: tips, `marker_tips`, anchors, the
intent's append. The one lock of layer design §6.1 step 0 still covers the tip
read and the append. The selection sits outside it by decision 3, and the pin
comparison is what makes that sound.

### 4.3 The snapshot — `selection.v1`

```text
{ "domain": "science.publish-selection.v1",
  "event_token": <32-hex>,
  "records": [ { "id": <world record id>, "text": <the record's canonical markdown> }, … ] }
```

- Records are strictly ascending by id and equal `selection.selected`.
- `text` is `nodes`' canonical rendering of the retained record, which is
  byte for byte what the ordinary writer writes.
- The file is `v1.encode` of the value, and its identity is
  `v1.digest("science.publish-selection.v1", value)`.
- Step 0 checks every record's content identity against the view's capture
  before writing. The check holds by construction and is asserted, not
  trusted.

### 4.4 The durable create-only write — `beliefs/durable.py` (new)

`write_create_only(path, data) -> Literal["created", "present"]`:
1. Write the bytes to `path.parent / f".{path.name}.{token_hex(8)}.tmp"`,
   opened `O_CREAT | O_EXCL | O_WRONLY`, then `fsync` it.
2. `os.link` it to `path`. The link fails if the name exists.
3. `unlink` the temporary and `fsync` the directory.

On `FileExistsError` it reads `path`: identical bytes answer `"present"`, and
different bytes raise `CreateOnlyCollision(path)`. Any leftover
`.{path.name}.*.tmp` in the directory is removed first. This is layer design
§6.1 step 0's mechanism, used by the snapshot, the request and the sibling
(§6). It is plain POSIX, not an `atoms` root. `root.py` stays the one `atoms`
importer.

### 4.5 After the lock: snapshot, then request

Once the intent is appended, the act writes `selection.v1` and then
`request.v1`, both to `<operations root>/publish/<event_token>/`, both by
§4.4.

```text
{ "domain": "science.publish-request.v1",
  "event_token": <32-hex>,
  "view": <pinned coord address>, "destination": <canonical>,
  "epoch": <64-hex packaging identity>, "world_id": <32-hex source world>,
  "pins": { "science_contract": …, "domains": {…} },
  "selection": <64-hex snapshot identity>,
  "staging_world_id": <32-hex digest("science.publish-staging-world.v1", event_token)[:32]> }
```

- The request identity is `(view, destination)` plus the pinned revision the
  view names, as layer design §6.1 step 0 defines it.
- The paths are not stored. `staging`, `world` and the snapshot are canonical
  functions of the operations root and the token, and a request that named
  its own paths could name others.
- **Order matters.** If the process crashes after the intent and before the
  request, the intent is left unfinished with no request, and it is never
  resumed (layer design §6.1 step 0, unchanged). A snapshot with no request
  is residue for the operator. A request's presence implies its snapshot was
  durably written, since the snapshot was written first.

**`request-corrupt`.** A retry decodes the request and the snapshot. Each of
these is a terminal `request-corrupt` refusal (§7): a request that fails to
decode; a token, view or destination that disagrees with the intent's; a
missing snapshot; a snapshot whose identity differs from `request.selection`;
or a snapshot whose records fail to decode. The layer design's "cached tips
disagree" case cannot arise: since cut 39 the tips are in the intent, and the
binding door recomputes them.

## 5. Steps 1–3 — staging, populate, admit, export

**Step 1.** Build `WorldConfig(world_root = <op>/world, world_id =
request.staging_world_id, corpus_roots = (<op>/staging,))`, where `<op>` is
`<operations root>/publish/<token>`. Then reinvoke each step in order:
- `init_corpus_root(staging)`;
- the staging writer's `adopt_manifest(profile = request.pins)`. On
  `ManifestAlreadyPresent` it runs `load_manifest(staging)` and compares the
  pins, and a mismatch refuses `staging-corrupt` (a foreign write);
- `init_world_root(config)`;
- `open_world(config)`.

**Step 2, population.** Classify the staging corpus against the snapshot and
the expected marker. The expected marker is
`marker_record(intent, world_id = request.world_id, epoch = request.epoch,
selection = the snapshot's ids)`, cut 39's factory, whose bytes are a
function of the intent and those arguments.

| state | action |
|---|---|
| true prefix: marker absent, and the present records, in snapshot order, byte-equal the snapshot's first *n* | write *n + 1* … through `_stage_record`, then the marker through `_stage_marker` |
| complete: every snapshot record present and byte-equal, the marker present and byte-equal to the expected marker, nothing else | go to step 3 |
| anything else: a hole, an extra record, a byte mismatch, or a marker that is unequal or present early | `staging-corrupt` naming the first offending record id, terminal (§7) |

`_stage_record(writer, text)` and `_stage_marker(writer, node)` sit on
`CorpusWriter` beside `add`:
- each runs under `writer._operation` and requires its permit;
- each runs `_require_pins_agree` and `validated_node`;
- each refuses a record the staging pins do not authorize;
- each writes one registered transaction through the writer's own
  `_corpus.add`.

`_stage_marker` also requires `publication.publication_content_malformed` to
answer `None` and `marker_consistent` to answer `True`.

**Step 3.** Re-check completeness, since a true prefix goes back to step 2.
Then reinvoke `World.admit(staging, provenance = a fresh adoption)` on the
staging world opened under the intent's actor (§2 decision 9). Its predicate
converges on a prior admission by this attempt and refuses any other. Then
run `export_head_artifact(staging world, CorpusSubject(corpus_id))`, which
stores nothing.

## 6. Steps 4–6 — the local reveal

- **Export root:** `<destination>/<corpus_id>` (§2 decision 4).
- **Step 5, the sibling.** `write_create_only(<destination>/<corpus_id>.head-artifact.v1,
  artifact)`. A collision, a sibling of the same name with other bytes, is
  `export-collision`, terminal (§7).
- **Step 6.**
  1. `replicate_root(staging, export root)` returns the retained operation
     id, and an exact retry adopts the claim.
  2. If `read_lifecycle_state(export root)` is not `READ_ONLY_SERVICEABLE`,
     run `restore_root(export root, CorpusSubject(corpus_id),
     ObserverSet((ArtifactCarrier.from_bytes(<the sibling read back>),)))`.
  3. A verdict other than `validated` leaves the root unserviceable, and the
     act reports `reveal-refused` with the verdict, terminal (§7).

  A serviceable export root is the local reveal. The staging root is
  retained until step 9, so any retry can re-export from it (layer design
  §6.1 step 5).

## 7. Step 8 and the terminal refusals

**Step 8.** Call `_bind_publication(writer, resolver, opened, corpus_id,
marker = the marker uid, artifact = digest of the sibling's bytes,
remotely_revealed = False, …)`. It gains one keyword, `lifecycle: tuple[Entry,
…]`: the `publication-staging`, `publication-export` and `publication-reveal`
entries, which its report carries ahead of the binding entry, in both the
success plan and the fallback. `opened` is rebuilt on retry from the intent
decoded out of the chain and its digest, which is cut 39's `OpenedPublication`.

**The pre-binding refusal door.** `_refuse_publication(writer, opened,
entries)` writes the report alone through `execute_fulfilling`, with the
intent's actor as observer and `PUBLISH_INSTRUMENT` as instrument. It serves
`request-corrupt`, `staging-corrupt`, `export-collision` and
`reveal-refused`. None of them reached a reveal, so none carries orphan
fields, and none ever enters `marker_tips` (a locally revealed attempt never
does, cut 39 §6).

**The act-report amendment.** Four entry kinds join `_ENTRY_KINDS`,
`_ALLOWED_OUTCOMES`, `_OUTCOME_TYPES` and the stored mirror
`stored._REPORT_ENTRY_OUTCOMES`. Each uses the stored `{kind, subject,
outcome}` form, and `subject` is the binding address's `coord:` string, as in
cut 39.

| entry kind | outcome | fields |
|---|---|---|
| `publication-request` | `request-corrupt` | `reason`: `undecodable`, `intent-disagrees`, `snapshot-missing`, `snapshot-mismatch`, `snapshot-undecodable` |
| `publication-staging` | `staged` | `corpus_id`, `records` (count) |
| | `staging-corrupt` | `corpus_id` or `null`, `record` or `null`, `reason`: `pins-foreign`, `hole`, `extra`, `bytes`, `marker` |
| `publication-export` | `exported` | `corpus_id`, `artifact` |
| | `export-collision` | `corpus_id`, `sibling` (the sibling's file name) |
| `publication-reveal` | `revealed` | `corpus_id` |
| | `reveal-refused` | `corpus_id`, `verdict` |

**Report shape.** A `publish` report carries these entries in order: request
(present only as a refusal), staging, export, reveal, binding. The entries
stop at the first refusal. Cut 39's "exactly one entry" becomes this
sequence. The act-report design gains an "Amended 2026-09-23 (publish act,
cut 40)" note in §2 and §6 item 3.

## 8. Step 9 and done

**Done** is layer design §6.1's definition, unchanged: this attempt's binding
revision exists, looked up by `binding_record`'s deterministic identity, and
the intent's completion reading is `closed`.

**Step 9** runs only when done. It removes `<op>/staging`, `<op>/world` and
their metadata siblings with `shutil.rmtree` and keeps `request.v1` and
`selection.v1`: those two are the attempt's durable residue, and
`pending_publishes` skips any request whose intent is `closed`. If a crash
interrupts the discard, the retry sees done and repeats the discard. After a
terminal refusal, staging is kept for the operator (layer design §6.1).

## 9. Recovery — the local rows

`resume_publish` reads the intent's completion reading first:

| state found | outcome |
|---|---|
| intent `unfinished`, no request | `Unresolved("no-request")`, nothing written; never resumed |
| intent `indeterminate` | `Unresolved("indeterminate")`: fail closed, not resumed, not relabelled |
| intent `closed`, this attempt's binding present | `Published`; step 9 if staging remains |
| intent `closed`, binding absent | `PublishRefused` with the report on record; never resumed |
| intent `unfinished`, binding present | `Unresolved("binding-without-report")`: a foreign write, since step 8 is all-or-nothing |
| intent `unfinished`, request present, binding absent | step 1, by reinvocation (§2 decision 8) |

From step 1 on, the layer design's local rows are reached, not dispatched:

| layer-design row | how it is reached |
|---|---|
| step 1 not converged | each initializer's own predicate |
| true prefix | §5's classification → step 2 from *n + 1* |
| not a prefix, not complete | `staging-corrupt`, reported |
| complete, admission not converged | `World.admit` reinvoked |
| admitted, no sibling | export and step 5 |
| sibling, no reservation | step 6's `replicate_root` |
| bare reservation | `replicate_root`'s exact retry adopts it |
| stamped copy, sibling missing | export (pure) and step 5 again, then `restore_root` |
| stamped, sibling present, unserviceable | `restore_root` |
| revealed, binding absent, `unfinished` | step 8 |

The remote row (a serviceable export root whose remote copy is not verified)
belongs to cut 41.

## 10. Arrival — `beliefs/publication_arrival.py` (new)

```python
def admit_publication(world: World, root: Path, observers: ObserverSet) -> tuple[AdmissionRecord, LogReport]
```

It opens the arriving root read-only (`ReadView.opened_at`) and refuses with
`ArrivalRefused(reason)`, before any write, when any of the following fails:

| check | reason |
|---|---|
| exactly one record of kind `publication` | `marker-absent`, `marker-duplicated` |
| `publication_content_malformed(marker)` is `None` | `marker-malformed` |
| `marker_consistent(marker)` | `marker-inconsistent` |
| the root's other records are exactly `marker.selection` | `selection-mismatch`, naming the first difference |
| no record of kind `publication-binding` | `binding-present` |

It then calls `admit_arrival(world, root, ReplicaOf(load_manifest(root).corpus_id),
observers)`, whose chain verification binds the files the checks read. A
root that is read-only and serviceable does not change between the checks
and the call. Anything less is refused whole (layer design §6.1 "the
atomicity claim"). `ArrivalRefused` is a new `WriteRefused` in `errors.py`.

## 11. What does not change

- the intent's bytes and `PublishIntent`;
- `standing_at`, `marker_tips_at` and the cut-39 refusal table;
- both records' factories;
- every lifecycle function in `root.py`;
- `admit_arrival` and `World.admit`;
- `evaluate_query`;
- every other operation kind's report;
- the TypeScript parity artifact;
- the reproduction driver.

`_open_publication` changes only by `expected_view` (§4.2), and
`_bind_publication` only by `lifecycle` (§7). No stored record of an existing
kind changes a byte.

## 12. Shared files, under roadmap concurrency rule 3

- **Rewritten by every lane:** `errors.py`, the ledger, the roadmap,
  `docs/guide/open-questions.md`, `python/tests/test_designs_corpus.py`.
- **Named beyond those:** `publication_doors.py`, `corpus.py` (the two
  staging doors), `permit.py`, `report.py`, `stored.py`, `boundary.py` (the
  report minting), `test_permit.py`, `test_permit_boundary.py`,
  `test_permit_entry_points.py`.
- **New:** `publish.py`, `durable.py`, `publication_arrival.py`.

No other kernel lane is open.

## 13. Guarantee rows

The Y table (`../../designs/2026-09-22-publication-design.md`) gains Y5–Y10:

| row | guarantee |
|---|---|
| **Y5** | every step-0 refusal — `view-revised`, `selection-incomplete`, `empty-selection`, `closure-incomplete` (a composite's missing member included), `pins-disagree`, `coordination-unpinned`, `destination-unusable`, `operations-root-unusable`, and `evaluate_query`'s own — writes nothing: no intent, no file under the operations root |
| **Y6** | a retry never selects differently: population reads only the snapshot the request's digest names, written create-only before the request; a corpus that drifts after step 0 does not strand the retry; a request or snapshot that disagrees with its intent is `request-corrupt`, reported, terminal |
| **Y7** | staging resumes only from a true prefix; a hole, an extra, a byte mismatch or an unequal marker is `staging-corrupt`, reported, terminal; population is complete iff the marker is byte-equal to the factory's |
| **Y8** | the local reveal is `restore_root`'s grant on `<destination>/<corpus_id>` against the create-only sibling; a colliding sibling or a non-`validated` verdict is reported and binds nothing; a second publication to the same destination lands beside the first |
| **Y9** | a crash after any local step resumes exactly to one binding and one report; done iff this attempt's binding exists and the intent is `closed`; `indeterminate` and binding-without-report fail closed with nothing written; the terminal report carries the lifecycle entries in step order |
| **Y10** | a published corpus is admitted in a second world only through `admit_publication`, which refuses before any write a root with no marker, two markers, a malformed or inconsistent marker, a binding, or records other than the marker's selection |

## 14. Testing and the cut

### 14.1 Unit — portable

- **`durable.py`:** created, present, collision, a leftover temporary
  removed, and the name never showing partial bytes (a fault injected before
  the link).
- **The snapshot and request codecs:** round-trip, strict ordering, every
  malformed field, and the identity recomputation.
- **The closure rule:** a table over each world relation, a composite
  missing a member, and a selection whose closure is complete.
- **Pins derivation:** agreement, `science_contract` disagreement, a domain
  pinned to two values, no coordination v2 pin, and a v1 coordination pin.
- **The population classifier:** each row of §5's table, from records built
  by the factory.
- **The report:** each new entry kind and outcome round-trips through the
  typed and stored forms, and the ordered-sequence rule refuses an
  out-of-order or post-refusal entry.
- **Permits:** `publishes()` names exactly decision 6's families and kinds,
  and every ordinary route naming `publish` still refuses.
- **`admit_publication`:** each refusal reason over a hand-built root.

### 14.2 Acceptance — `test_publish_act_acceptance.py` (new)

These run on the certified tuple, over a source world with two contributing
corpora and a written root pinning coordination v2. Every arm ends
`_durably`. Crashes are injected at step boundaries through a fault seam on
the act, which raises and discards in-memory state; a fresh `resume_publish`
then reads only disk. A kill at an engine stage is `persistence-cut`'s (§16).

| unit | row | assertion |
|---|---|---|
| Y5-a | Y5 | each pre-intent refusal leaves the chain's tip and the operations root byte-unchanged |
| Y5-b | Y5 | a view revised between evaluation and lock refuses `view-revised`; nothing is appended |
| Y6-a | Y6 | a crash after the request; a task minted in the written root, so the world drifts; `resume_publish` publishes the step-0 selection byte for byte |
| Y6-b | Y6 | the snapshot rewritten with other bytes → `request-corrupt` report, closed, no binding |
| Y7-a | Y7 | a crash after *k* staged records → resume writes *k + 1* … once each (the counting port) |
| Y7-b | Y7 | an extra record raw-written into staging → `staging-corrupt` naming it, report alone, staging retained |
| Y8-a | Y8 | a published root is read-only-serviceable at `<destination>/<corpus_id>` with the sibling beside it; a second publish of the same view lands beside it, and its marker supersedes the first's |
| Y8-b | Y8 | a pre-existing sibling with other bytes → `export-collision`, no binding |
| Y9-a | Y9 | for each step boundary 1–6 and 8, crash then resume → `Published`, exactly one binding revision and one report, the report's entries in step order |
| Y9-b | Y9 | a binding revision raw-written beside an unfinished intent → `Unresolved("binding-without-report")`, nothing written |
| Y9-c | Y9 | an intent with no request → `Unresolved("no-request")`; `pending_publishes` omits it |
| Y9-d | Y9 | done then a crash inside step 9 → resume discards staging and answers `Published` |
| Y10-a | Y10 | a second world admits the published root through `admit_publication`, and its epoch sees the selection |
| Y10-b | Y10 | a root built through the staging doors with one record beyond its marker's selection, exported, replicated and restored against its own artifact, so its chain verifies → `admit_publication` refuses `selection-mismatch`, and the recipient's registry is unchanged |

### 14.3 N2 sabotages — `n2_arms_cut40.py`

| unit | sabotage |
|---|---|
| Y5-a | the closure check skips `composes` |
| Y5-b | `_open_publication` ignores `expected_view` |
| Y6-a | resume re-evaluates the query instead of reading the snapshot |
| Y6-b | the retry skips the snapshot's identity check |
| Y7-a | the classifier restarts population from record 1 |
| Y7-b | the classifier ignores records outside the snapshot |
| Y8-a | the export root is the destination directory itself |
| Y8-b | the sibling write overwrites instead of creating |
| Y9-a | step 8's report omits the lifecycle entries |
| Y9-b | the classifier treats binding-present-unfinished as done |
| Y9-c | `pending_publishes` lists requestless intents |
| Y9-d | done is decided by resolving the current binding instead of this attempt's identity |
| Y10-a | `admit_publication` skips `marker_consistent` |
| Y10-b | the selection-equality check compares ids only against the marker, not the root's contents |

The plan fixes the declared accounting (14 arms, 14 units, 6 rows as drafted
here: Y5–Y10). A unit whose check does not see its sabotage is rehomed at
Task 0, never dropped.

### 14.4 The cut

The cut document is `docs/designs/<freeze date>-conformance-cut-40.md`, dated
by the commit that freezes it after review. `tools/cut40_acceptance.py` sets
`PREFIX_RUNNERS = ("cut39_acceptance.py",)` and `PHASE_MODULES =
("test_publish_act_acceptance.py", "test_n2_cut40.py")`. The cut also needs
the `test_recent_cut_acceptance.py` row with its declared arm, unit and
guarantee-row counts and its guarantee-rows-exercised line, and the results
record.

`root.py` stays the one `atoms` importer, and `publish.py` reaches the
lifecycle through `root.py`'s wrappers. `_stage_record`, `_stage_marker` and
`_refuse_publication` are new callers of write primitives. They join
`WRITE_ENTRY_POINTS` under the `publish` family and gain `Case`s in
`test_permit_entry_points.py`'s `CASES`.

## 15. Documentation amendments

- **Layer design §6.1**, notes at the sentences they qualify:
  - step 0's selection is evaluated before the lock against the caller's
    current epoch and snapshotted, and the lock covers tips and intent with a
    pin re-check (decisions 2–3);
  - step 4's local export root is `<destination>/<corpus_id>`, not the
    destination itself (decision 4);
  - the recovery table's `request-corrupt` is re-stated for the snapshot
    (§4.5).
- **Act-report design** §2 and §6 item 3: the four entry kinds and the
  report's ordered sequence.
- **Ledger:** Y5–Y10 open, then closed at the results record. `publish` stays
  in Current state with cut 41's remainder.
- **Roadmap:** re-ranked at cut 40, with `publish`'s remainder named as cut
  41.

## 16. Limitations

1. **Crashes are exceptions at step boundaries.** They are not kills at
   engine stages or power cuts, which belong to `persistence-cut`
   (`beliefs-3ea822`). The arms prove the classifier and the reinvocation
   order, not the engine's own crash atomicity, which its cuts own.
2. **The durable create-only write rests on the host's POSIX `fsync` and
   `link`.** It is not an `atoms` root, and the kernel does not check the
   operations root's volume against the allowlist.
3. **Step 9 removes staging with `rmtree`,** outside any `atoms` operation.
   The roots are private and throwaway.
4. **`publish` has no public route.** `science` reaches it by its own design.
5. **Remote destinations are refused until cut 41.**

## 17. Task linkage

`beliefs-328507` carries `--spec publish-act-local`, and the plan's
`### Task N:` headings become its children. Cut 41 is filed as a sibling
under `beliefs-1a5157`, depending on `beliefs-328507`: remote transport,
orphans and Ruling 12, and the recipient's `divergent-publication`.

## 18. Review log

- 2026-09-23: drafted. The user chose the local-first split before drafting.
