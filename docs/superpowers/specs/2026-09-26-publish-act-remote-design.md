# The publish act, remote — transport, the remote reveal, its orphans and divergent-publication

**Slice of:** `2026-08-29-user-and-autonomy-layer-design.md` §6.1 step 7, the
remote half of steps 4, 8 and 9, the recovery table's remote rows, §6.2's
orphans and §6.3's `divergent-publication`. This is the third and last of three
slices of sub-project 5's `beliefs` half.
**Boundary:** `publish`: the governed publication act
(`../../designs/2026-08-03-redesign-adoption-ledger.md`, Current state)
**Task:** `beliefs-3ce305`, child of the lane task `beliefs-1a5157`
**Lane:** `world-read`
**Cut:** 42, off the path (roadmap tier 1, off-path row 1)
**Status:** draft for user review, 2026-09-26

## 1. What this slice is

Cut 39 built the step-0 intent door and the step-8 binding door. Cut 40 built
the act between them for a local destination, whose reveal is `restore_root`'s
atomic grant. `publish` still refuses a remote destination
(`ValidationRefused("remote destinations arrive in cut 42")`).

A remote destination — a git remote, a Zenodo deposit, a commons inbox — adds
one step and changes what "revealed" means. Step 7 uploads the export root and
its head artifact, and an upload is not atomic: it can stop half-way, and a
completed upload can be fetched by a recipient before the publisher verifies
it. What was shared cannot be unshared (§6.2), so a remotely revealed marker
that never binds is an **orphan**, and the next publication of that view to
that destination must supersede it.

After this slice a caller holding the publication permit and a transport can
publish a view to a remote destination, resume an attempt that crashed at any
remote step, and a recipient holding several publications of one view to one
destination can tell whether one of them is current or whether they diverge.

A reading of the tree on 2026-09-26 found five things the remote act needs
and the kernel lacks:

1. **No transport seam.** Nothing in the kernel moves bytes to a remote, and
   §6.4 gives the hosting glue (a git layout, a Zenodo deposit) to `science`.
2. **No durable record that a remote reveal may have begun.** The orphan fold
   (`publication_doors.marker_tips_at`) reads orphans only from step 8's
   refusal reports, which carry `remotely_revealed`. Every pre-binding refusal
   is `PreBinding` and is skipped. A remote attempt that fails after its
   upload started but before step 8 would leave no trace the fold can read.
3. **Cut 39's Ruling 12.** An exception raised before any effect at step 8
   leaves the intent `unfinished`, so its remotely revealed marker is in no
   report and no later `marker_tips` names it. If a new attempt proceeds
   instead of resuming it, the stranded marker and every later marker diverge
   at every recipient that took the stranded one, with nothing able to repair
   it.
4. **No remote export root.** Cut 40's export root is
   `<destination>/<corpus_id>`, a local path. A URL is not one.
5. **No recipient reading of publications.** `admit_publication` admits one
   published corpus. Nothing reads the markers a recipient holds for one
   `(view, destination)` and applies §4.1's tip rule to them, so
   `divergent-publication` has no code.

## 2. Decisions

Each decision names what it rejects.

1. **Transport is an injected seam the kernel verifies.** The caller supplies
   a `Transport` (§3.1) with two operations: `push`, which uploads a named set
   of files, and `listing`, which reads the remote back as names and SHA-256
   digests. The kernel computes the local listing itself and decides
   "verified complete" by comparing the two. Real destinations are `science`'s
   adapters (§6.4). The kernel ships none, and its tests use a directory-backed
   fake.
   - **Rejected:** a seam that answers `verified` or `not verified` itself.
     The guarantee "the remote holds exactly these bytes" would then rest on
     each adapter's honesty, and no kernel test could exercise it.
   - **Also rejected:** a git or Zenodo adapter in the kernel, which is
     hosting glue by §6.4.

2. **A remote reveal begins when transport begins, and a durable mark records
   it before the first byte leaves.** After step 6 validates the export root,
   the act writes `<op>/transport.v1` by the durable create-only write (cut
   40's `durable.py`). It names the corpus, the marker, the artifact identity
   and the record count (§4.2). From then on the attempt is treated as
   possibly shared.
   - **Rejected:** "revealed" meaning "verified complete". A crash after a
     complete upload and before verification leaves a fetchable marker, and a
     reading that waited for verification would drop it.
   - **Also rejected:** a mark written after `push` returns. A crash inside
     `push` would leave a possibly shared marker with no mark.

3. **The orphan rule is asymmetric: a possibly shared marker creates an
   orphan, and only a certainly shared marker retires one.** An attempt whose
   transport began but was not verified is recorded as an orphan (§2 decision
   4). It does **not** retire the orphans its own intent's `marker_tips` named.
   Only a verified upload, followed by a step-8 report, retires them, which is
   cut 39's rule unchanged.
   - Suppose unverified markers retired orphans. Orphan O stands, attempt T
     names O in its `marker_tips`, and T's upload fails at the first byte. T
     would then retire O from the fold. The next marker N would supersede T,
     which no recipient holds, and not O. A recipient holding O and N would
     report `divergent-publication` for ever.
   - **Rejected:** one symmetric "remotely revealed" flag for both directions.
     It is safe in one direction only.

4. **A transport the seam abandons, or a listing that disagrees, is a terminal
   refusal carrying the orphan.** A new lifecycle entry,
   `publication-transport`, has the outcomes `transported` and
   `transport-incomplete`. The latter carries `corpus_id`, `marker` and a
   `reason` (`abandoned` or `listing-mismatch`). Its report fulfils the intent
   alone, through cut 40's `_refuse_publication`. The fold reads it as an
   orphan that retires nothing (decision 3), so the next publication
   supersedes it.
   - An exception from `push` or `listing` is not an outcome: it propagates
     and leaves the intent `unfinished`, to be resumed. The seam's contract is
     that raising means "try again" and abandoning means "this attempt's
     upload is over".
   - **Rejected:** retrying for ever. Without a terminal outcome, a
     permanently broken remote holds its `(view, destination)` blocked under
     decision 6 with no way to close it, since §6.1 defines no abandon
     operation.

5. **After the mark, a retry resumes at step 7 from the mark alone.** It does
   not decode the request or the snapshot again, reclassify staging, re-export
   or restore. Those steps' results are already fixed in the validated export
   root and in the mark. The step-8 report's lifecycle entries are rebuilt from
   the mark.
   - **Rejected:** re-running steps 1–6 on every retry, as the local act does.
     A pre-binding refusal found after the mark (`staging-corrupt` over a
     staging root damaged after the reveal) would be `PreBinding`, which
     carries no orphan, and a possibly shared marker would be dropped.
   - Before resuming from it, the act checks the mark against its intent and
     against the retained export root and sibling (§4.2). A mark that fails
     to decode, or disagrees with either, answers
     `PublishUnresolved("transport-mark-corrupt")` and writes nothing: fail
     closed, like `indeterminate`. Nothing the mark names reaches a binding
     unchecked.

6. **Ruling 12 is closed at step 0.** A publish refuses
   `PublicationRefused("publish-unfinished", tokens=…)` before its intent,
   writing nothing, while the written chain holds an `unfinished` publish
   intent for the same `(view, destination)` whose transport mark exists under
   the operations root. The operator resumes the named attempt, which then
   binds or closes as an orphan, and the next publish supersedes it.
   - An `unfinished` attempt with no mark never uploaded anything, so it does
     not block. That covers a requestless intent and a crash anywhere before
     the mark. If it is resumed after a later publish has bound, it still
     binds: step 8 judges tips at its own intent position, where the later
     binding does not exist yet (cut 39's intent-position rule). The two
     bindings are lawful siblings. A recipient holding both markers reads
     `divergent-publication` until the next publish, whose binding tips are
     both siblings, supersedes both markers.
   - **Rejected:** folding the stranded attempt's marker into the new
     intent's `marker_tips`. The mark is outside the chain, and step 8's guard
     recomputes `marker_tips` from the chain alone (cut 39 §6), so the
     recomputation would disagree (`tips-disagree`).
   - **Also rejected:** refusing on any unfinished attempt that has a request,
     the task note's leading candidate. It blocks a destination behind attempts
     that never shared anything, some of which may never resume.
   - **And rejected:** closing a requestless intent with a report. Cut 40
     freezes `no-request` as writing nothing (Y9-c).

7. **A remote export root is `<op>/export/<corpus_id>`.** The container
   `<op>/export` stands where a local destination's directory does, so steps 4
   to 6 are cut 40's code with the container swapped. The sibling is
   `<op>/export/<corpus_id>.head-artifact.v1`. The layer design's
   `…/<event_token>/export` becomes a container rather than the root itself,
   for cut 40's reason: the root is named by its `corpus_id`.

8. **Step 9 keeps the remote export root.** It removes staging and the
   staging world as cut 40 does. It keeps the request, the snapshot, the mark
   and the read-only serviceable export root. Removing a serviceable root is a
   lifecycle act the kernel has no primitive for. Reservation cleanup is
   out-of-band operator work (§6.1), and this cleanup is too.
   - **Rejected:** `rmtree` of the export root, which would reach under a
     read-only-serviceable `atoms` root with no engine operation.

9. **The recipient reads publications with the family's one tip rule.**
   `publication_tip(read, view, destination)` collects the markers at
   `marker_address(view, destination)` across the world view's captured
   records. It removes every pair some present marker's `supersedes_markers`
   names, and answers `CurrentPublication(corpus_id, marker)` for one
   survivor, `DivergentPublication(tips)` for several, and `None` when no
   marker is held. A missing intermediate — a recipient holding A and C, where
   C supersedes B and B supersedes A — leaves A standing and reads as
   divergent. That fails closed: the recipient cannot see B's supersession
   without B.
   - **Rejected:** transitive supersession across absent markers. Nothing a
     recipient holds says that A is behind C.
   - Retiring a superseded corpus through the recipient's registry lifecycle
     (§6.2) is a recipient's act, not this reading, and it is not built here
     (§13).

10. **The recipient's intake is the two existing acts.** A recipient takes a
    raw copy of the transported files (without the `.metadata` sibling, so the
    root reads `METADATA_LESS`), runs `restore_root` against the transported
    head artifact, then `admit_publication`. The file layout and the download
    are `science`'s glue. No new kernel door is added.
    - **Rejected:** a `receive_publication` door that downloads. It would pull
      a transport into the recipient's kernel.

## 3. Surface

### 3.1 The transport seam — `beliefs/transport.py` (new)

```python
class Transport(Protocol):
    def push(self, destination: Destination, files: Mapping[str, Path]) -> TransportAbandoned | None: ...
    def listing(self, destination: Destination, corpus_id: str) -> Mapping[str, str]: ...

@dataclass(frozen=True)
class TransportAbandoned:
    detail: str

def transport_files(container: Path, corpus_id: str) -> dict[str, Path]
def local_listing(files: Mapping[str, Path]) -> dict[str, str]
```

- **Names.** `transport_files` maps a logical name to a local path.
  - Every regular file under `<container>/<corpus_id>` is named
    `<corpus_id>/<posix path relative to the root>`.
  - The sibling is named `<corpus_id>.head-artifact.v1`.
  - A symlink or any other non-regular entry under the root refuses
    `MalformedRecord` before the mark. The plan's Task 0 pins that a validated
    export root holds only directories and regular files.
- **`push`** uploads every named file. It is reinvoked on every retry and must
  be idempotent: it converges on the same remote content. It returns
  `TransportAbandoned` when this attempt's upload will never complete, and
  raises for anything transient.
- **`listing`** enumerates the publication's whole namespace at the remote:
  every file it holds whose name is `<corpus_id>.head-artifact.v1` or begins
  with `<corpus_id>/`, each mapped to the SHA-256 hex of its remote bytes. It
  names what the remote holds, not what the act asked for, so an extra file is
  visible. It may raise.
- **Verified complete** means `listing(destination, corpus_id) ==
  local_listing(files)`, computed by the act. Anything else is
  `listing-mismatch`: a missing name, an extra name, or a differing digest.
- **The namespace is the seam's to keep.** A destination kind lays the names
  out as it likes (a git tree, a deposit's file list), but it must enumerate
  exactly the files under them. An adapter that cannot enumerate its remote
  cannot implement `listing`, and cannot publish.
- The seam takes no authority. It reaches only the remote. The act holds the
  permit (§3.2).

### 3.2 The act — `beliefs/publish.py`

`publish` and `resume_publish` gain one keyword, `transport: Transport | None
= None`. The rules:

- A remote destination with `transport=None` refuses
  `ValidationRefused("a remote destination needs a transport")`, as does a
  local destination given a transport. Both run after the permit and before
  anything else, and write nothing.
- The `ValidationRefused("remote destinations arrive in cut 42")` is removed.
- `resume_publish` applies the same rule to the intent's destination.

`PublishOutcome` is unchanged in shape:
- `PublishRefused.outcome` may now be `transport-incomplete`;
- `PublishUnresolved.reason` gains `transport-mark-corrupt`.

`RequiredCapabilities.publishes()` is unchanged. A read of what the remote act
calls found no new family: the mark is a `durable.py` write, and transport
goes through the seam. `pending_publishes` is unchanged.

## 4. The remote act

### 4.1 Step 0

Cut 40's order, with two differences:

1. **The destination checks.** A remote destination's locator is already a
   canonical URL (`Destination.__post_init__`, `url_locator`). It is not
   resolved on the filesystem, and `destination-unusable` does not apply. The
   operations-root checks apply unchanged: `require_usable` checks only the
   operations root for a remote destination and returns the destination as
   given.
2. **`publish-unfinished`**, after the operations-root check and before the
   view is resolved:
   - `publication_doors.unfinished_attempts(writer, view, destination, seam)`
     lists every publish intent on the written chain whose `view` (unpinned)
     and `destination` match and which has no committed fulfilling
     registration. It reads chain entries only, not reports.
   - Each listed token whose `<operations root>/publish/<token>/transport.v1`
     exists is blocking.
   - Any blocking token refuses `PublicationRefused("publish-unfinished",
     tokens=<ascending>)`.
   - A local destination can hold no mark, so the check never blocks one.

The check runs before the lock. Take two attempts in one process: A writes its
mark between B's check and B's intent. A is in flight, not stranded, and
closes as bound or as an orphan by the rules below. If A later strands, every
publish after B refuses until A is resumed. The race window is repaired by the
next publish, not left permanent (§16 item 3).

### 4.2 The transport mark — `transport.v1`

```text
{ "domain": "science.publish-transport.v1",
  "event_token": <32-hex>,
  "destination": <canonical, remote>,
  "corpus_id": <32-hex>, "marker": <32-hex marker uid>,
  "artifact": <64-hex head-artifact content identity>,
  "records": <count of selected records> }
```

- It is `v1.encode`d and written by `write_create_only` to `<op>/transport.v1`
  after step 6's `validated` verdict and before `push` is first called.
- An exact retry finds identical bytes (`present`). Other bytes are
  `CreateOnlyCollision`, which propagates and writes nothing, so the attempt
  stays `unfinished`, blocks step 0, and is the operator's.
- **Decoded strictly.** Every field is present, and there are no others. The
  token and destination equal the intent's. The marker equals
  `marker_uid(token)`. The destination's type is `remote`.
- **Checked against the export before a resume uses it.** Let `export` be
  `<op>/export/<corpus_id>` and `sibling` be
  `<op>/export/<corpus_id>.head-artifact.v1`. All of the following must hold:
  1. `read_serviceable(export)`, and `load_manifest(export).corpus_id` equals
     the mark's `corpus_id`;
  2. `sha256(sibling bytes)` equals the mark's `artifact`, and the sibling
     decodes as a `science.head-artifact.v1` whose subject is
     `CorpusSubject(corpus_id)` and whose genesis and head equal
     `chain_head_reader()(export)`;
  3. the export root holds exactly one record of kind `publication`, its uid
     is the mark's `marker`, and its `selection` has `records` entries.

  Any failure, including a failing decode, is `transport-mark-corrupt`. On a
  fresh run the act builds the mark from exactly these values after step 6, so
  the checks hold by construction there. A resume asserts them, because the
  mark and the files it names are outside every chain.

### 4.3 Step 7

`_transport(a, mark) -> Transported | TransportIncomplete`:

1. `files = transport_files(<op>/export, mark.corpus_id)`, then
   `expected = local_listing(files)`;
2. `transport.push(destination, files)`, where `TransportAbandoned(detail)`
   gives `TransportIncomplete(corpus_id, marker, "abandoned")`;
3. `listing = transport.listing(destination, mark.corpus_id)`, where
   `listing != expected` gives `TransportIncomplete(corpus_id, marker,
   "listing-mismatch")`;
4. otherwise `Transported(corpus_id, listing_identity)`, where
   `listing_identity = v1.digest("science.publish-transport-listing.v1",
   expected)`.

An incomplete transport writes the report alone through `_refuse_publication`.
Its entries are staging, export, reveal and transport, the last refusing, and
the result is `PublishRefused(token, "transport-incomplete")`.

### 4.4 Step 8 and step 9

`_bind` passes `remotely_revealed=True` for a remote destination. Its lifecycle
is staging, export, reveal and transport, every entry succeeding. A step-8
refusal is therefore an orphan by cut 39's rule, and a verified one that
retires what its intent named (decision 3). Step 9 is cut 40's `_discard`:
the export root, the mark, the request and the snapshot stay (decision 8).

### 4.5 The sequence

A fresh remote `publish` runs:
1. step 0 (§4.1);
2. steps 1–6 into `<op>/export` (decision 7);
3. the mark (§4.2);
4. step 7 (§4.3);
5. step 8;
6. step 9.

`resume_publish`, after cut 40's completion-reading branches (`indeterminate`,
`closed`, `binding-without-report`), reads `<op>/transport.v1`.
- If it is present, the attempt decodes it (`transport-mark-corrupt` on
  failure) and runs steps 7, 8 and 9 from it (decision 5).
- If it is absent, cut 40's request path runs, and for a remote destination
  that path reaches the mark itself.

## 5. The report and the fold

### 5.1 The act-report amendment

One entry kind joins `_ENTRY_KINDS`, `_ALLOWED_OUTCOMES`, `_OUTCOME_TYPES`,
`_LIFECYCLE_OUTCOMES`, `_LIFECYCLE_ENTRY_TYPES` and the stored mirror
`stored._REPORT_ENTRY_OUTCOMES`, in cut 40's `{kind, subject, outcome}` form:

| entry kind | outcome | fields |
|---|---|---|
| `publication-transport` | `transported` | `corpus_id`, `listing` (64-hex) |
| | `transport-incomplete` | `corpus_id`, `marker`, `reason`: `abandoned` or `listing-mismatch` |

`_refuse_publication`'s docstring claim that a pre-binding refusal "carries no
orphan fields" becomes: only `transport-incomplete` carries them.

`publish_sequence_error` admits one more lifecycle, and nothing else:

- **The lifecycle.** A lifecycle is either staging, export and reveal (local),
  or staging, export, reveal and transport (remote).
- **A binding** follows a whole lifecycle whose entries all succeed, or it
  stands alone (cut 39's bare door).
- **A pre-binding refusal** is a prefix of either lifecycle whose last entry
  refuses, or a request refusal alone.
- **Unchanged.** Every sequence cut 40 admits is still admitted, and the
  sequences it refuses are still refused.

### 5.2 The fold

`_reports_at` gains two rules, both in `publication_doors.py`:

1. **The transport entry must match the destination.** A report whose entries
   include `publication-transport`, fulfilling an intent whose destination is
   `local`, refuses `revision-malformed`. The reverse is not required: cut
   39's bare door writes a lone binding entry for either destination type.
2. **`PreBinding` gains `orphan: tuple[str, str] | None`.** It is
   `(corpus_id, marker)` when the last entry is `transport-incomplete`, and
   `None` otherwise.

`marker_tips_at` then treats a `PreBinding` whose `orphan` is set as an
orphan, and never as a retirement:

```text
PreBinding, orphan None       → skipped (cut 40)
PreBinding, orphan set        → orphans.add(orphan)          # retires nothing (decision 3)
refusal, remotely_revealed    → orphans.add(pair); retired ∪= intent.marker_tips   (cut 39)
bound                         → retired ∪= intent.marker_tips                       (cut 39)
```

`attempt_reading` is unchanged. A `transport-incomplete` report is `closed`,
and its outcome is the last entry's type.

`unfinished_attempts(writer, view, destination, seam) -> tuple[str, ...]` is
new. It walks the written chain's intent entries as `_reports_at` does, keeps
the publish intents for `(view, destination)` with no committed fulfilling
registration, and returns their tokens in ascending order.

## 6. Recovery — the remote rows

Before these rows, `resume_publish` runs cut 40's completion-reading branches
unchanged: `indeterminate`, `closed`, `binding-without-report`.

| state found | outcome |
|---|---|
| `unfinished`, no mark, request present | cut 40's request path; steps 1–6 into `<op>/export`, then the mark and step 7 |
| `unfinished`, no mark, no request | `PublishUnresolved("no-request")` (cut 40, unchanged) |
| `unfinished`, mark undecodable, or disagreeing with the intent, the export root or the sibling (§4.2) | `PublishUnresolved("transport-mark-corrupt")`, nothing written |
| `unfinished`, mark present | step 7 by reinvocation: `push` again, then `listing`, then step 8 |
| `closed` by `transport-incomplete` | `PublishRefused(token, "transport-incomplete")`, never resumed |

These are the layer design's remote row ("serviceable export root; remote
destination not verified complete → step 7"), which splits into the mark's
presence and its absence. The row "revealed; binding absent; `unfinished` →
step 8" is reached through step 7's reinvocation. Re-verifying a completed
upload costs one `listing`, and a verified state is never stored.

## 7. The recipient

### 7.1 `publication_tip` — `beliefs/publication_arrival.py`

```python
def publication_tip(read: WorldView, view: CoordinationAddress, destination: Destination
                    ) -> CurrentPublication | DivergentPublication | None
```

The reading, over the view's captured records:

1. **Collect** the records of kind `publication` whose address is
   `marker_address(view.unpinned(), destination)`. They are taken from every
   covered, present corpus's captured records.
2. **Refuse any corpus whose layout arrival would refuse.** Every covered
   corpus holding at least one marker at the address is checked by
   `publication_layout_refusal(records)`. This is the check `admit_publication`
   runs before any write, moved into one shared function in
   `publication_arrival.py`; `admit_publication` calls it and keeps its
   reasons and order unchanged. Over one corpus's captured records it refuses:
   - no `publication` record (`marker-absent`) or several
     (`marker-duplicated`);
   - a marker failing `not publication_content_malformed`
     (`marker-malformed`) or `marker_consistent` (`marker-inconsistent`);
   - any `publication-binding` record (`binding-present`);
   - records other than exactly the marker's `selection`
     (`selection-mismatch`, the first difference).

   The reading raises `PublicationReadingRefused(reason, corpus_id, refs)` with
   the same reason. Across corpora, two markers with one uid →
   `marker-duplicated`. A world can hold a corpus admitted by another route,
   so the reading applies arrival's rule itself instead of trusting that
   every holder arrived through the door.
3. **Take the tips.**
   - `present` is the set of `(holding corpus_id, marker uid)` pairs;
   - `superseded` is the union of every present marker's
     `supersedes_markers`;
   - `tips = present − superseded`.
4. **Answer.**
   - One tip → `CurrentPublication(corpus_id, marker)`.
   - Several tips → `DivergentPublication(tips)`, ascending. This is §6.1's
     `divergent-publication`, and it is a value, not an exception, because a
     divergence is a lawful sibling state.
   - No marker → `None`.
   - `present` non-empty with no tip is impossible by construction. A marker's
     uid digests a random token, so no marker can name one minted after it. It
     refuses `supersession-cycle` rather than answering `None`.

`PublicationReadingRefused` is a new `WriteRefused` sibling in `errors.py`, a
read refusal like `SelectionRefused`.

The plan's Task 0 pins that `WorldView.captured_records` holds coordination
kinds. `epoch.py` filters its derived index by `WORLD_KINDS`, and the capture
must not be filtered the same way.

### 7.2 Intake

The acceptance arms model a recipient in three steps (decision 10):
1. materialize the fake remote's files into a fresh directory;
2. `restore_root(copy, CorpusSubject(corpus_id), ObserverSet((ArtifactCarrier.from_bytes(<the transported sibling>),)))`;
3. `admit_publication`.

A copy with any named file missing never validates (`test_restore_root.py`'s
incomplete-copy case), so a partial upload is refused whole at the recipient.

## 8. What does not change

- The intent's bytes and `PublishIntent`.
- Both record factories and `marker_consistent`.
- `standing_at` and `_bind_publication`'s guard.
- `_open_publication`. The Ruling 12 check sits before it, not inside it.
- Every lifecycle function in `root.py`, and `durable.py`.
- The local act's behaviour, every cut 40 refusal and outcome included.
- `admit_publication`'s behaviour: its checks move into
  `publication_layout_refusal` with the same reasons in the same order, and
  cut 40's Y10 arms read it unchanged. `admit_arrival` and `World.admit` are
  untouched.
- `evaluate_query`, the TypeScript parity artifact and the reproduction
  driver.

No stored record of an existing kind changes a byte, and every report cut 39
or 40 wrote still folds to the same value. The one exception is a
`PreBinding` that gains `orphan=None`, which is not stored.

## 9. Shared files, under roadmap concurrency rule 3

- **Rewritten by every lane:** `errors.py`, the ledger, the roadmap,
  `docs/guide/open-questions.md`, `python/tests/test_designs_corpus.py`.
- **Named beyond those:** `publish.py`, `publish_request.py`
  (`require_usable` gains the remote branch of §4.1),
  `publication_doors.py`, `publication_arrival.py`, `report.py`, `stored.py`.
  `boundary._mint_publish_refusal` needs no edit: it defers to
  `publish_sequence_error`.
- **New:** `transport.py`, `tests/transport_fake.py`.

No other kernel lane is open.

## 10. Guarantee rows

The Y table (`../../designs/2026-09-22-publication-design.md`) gains Y11–Y16:

| row | guarantee |
|---|---|
| **Y11** | a remote reveal is verified by the act, not the seam: the remote's enumeration of the publication's whole namespace must equal the local listing of every export-root file and the sibling, by name and SHA-256; a missing, extra or altered file is `transport-incomplete` (`listing-mismatch`), reported, terminal; a remote destination without a transport, or a local one with one, refuses before anything is written |
| **Y12** | the transport mark is written create-only after the export root validates and before the first `push`; once it exists a retry resumes at step 7 from the mark and never re-runs steps 1–6; a mark that fails to decode, or disagrees with its intent, the export root's manifest and chain, the sibling's identity or the export's marker, fails closed with nothing written |
| **Y13** | a transport the seam abandons, or whose listing disagrees, closes the attempt with a report carrying `(corpus_id, marker)`; the fold reads it as a standing orphan that retires nothing, so the next publication's marker supersedes it and every orphan its intent named |
| **Y14** | a publish refuses `publish-unfinished` before its intent, writing nothing, while an `unfinished` attempt for the same `(view, destination)` has a transport mark; an unfinished attempt without a mark never blocks; once the blocking attempt is resumed to a close, the publish proceeds and its marker supersedes the resumed one |
| **Y15** | a crash at any remote step resumes to exactly one binding and one report whose entries run staging, export, reveal, transport, binding; a remote step-8 refusal carries `remotely_revealed: true` and is an orphan; step 9 keeps the export root, the mark, the request and the snapshot |
| **Y16** | a recipient admits a remote publication from a raw copy through `restore_root` against the transported artifact and `admit_publication`, and a copy missing any file never validates; `publication_tip` refuses a corpus whose layout `admit_publication` would refuse, answers the one standing marker, `divergent-publication` for sibling markers, and the one tip again once a marker superseding both arrives |

## 11. Testing and the cut

### 11.1 Unit — portable

- **`transport.py`:** naming covers every regular file and the sibling; a
  symlink under the root refuses; `local_listing` digests the bytes; the
  listing identity is a function of the listing alone.
- **The mark codec:** round-trip; every missing, extra or malformed field;
  token, destination and marker disagreement with an intent; a `local`
  destination refused.
- **The report:** both transport outcomes round-trip through the typed and
  stored forms. `publish_sequence_error` admits the remote lifecycle and its
  prefixes, refuses transport before reveal, a transport after a refusal, and
  a binding after `transport-incomplete`. Every cut-40 sequence is still
  admitted.
- **The fold:**
  - `_reports_at` refuses a transport entry under a local intent;
  - `PreBinding.orphan` is set only by `transport-incomplete`;
  - `marker_tips_at` adds that orphan and retires nothing (a table over the
    four rows of §5.2's rule);
  - `unfinished_attempts` lists only unfulfilled intents for the pair.
- **`publication_tip`:** none, one, two siblings, an orphan with a
  successor, a gap (A and C held, B absent), a duplicated uid across corpora,
  and the cycle refusal from a hand-built pair. Also, one hand-built corpus per
  `publication_layout_refusal` reason — two distinct markers in one corpus,
  one record beyond the selection, a binding present, a malformed and an
  inconsistent marker — each refused by the reading as by
  `admit_publication`.
- **The transport's listing:** an extra remote file under `<corpus_id>/`, and
  an extra sibling-like name, are each `listing-mismatch`.
- **The mark's export checks:** each of §4.2's three checks failing alone is
  `transport-mark-corrupt`.
- **The seam guards:** remote without a transport, local with one, and
  `resume_publish` under each.

### 11.2 Acceptance — `test_publish_remote_acceptance.py` (new)

The arms run on the certified tuple, over cut 40's fixture: a source world with
two contributing corpora, and a written root pinning coordination v2, built
under setup authority. The publishing and resuming writers bind exactly
`publishes()`.

**The fake transport.** `tests/transport_fake.py`'s `DirectoryTransport` maps
`https://remote.test/<name>` to a directory on the certified volume and stores
each name as a file. Its fault knobs:
- raise on the *k*th `push` call;
- drop a named file after a push;
- alter a named file's bytes;
- abandon.

It is a test double and never ships.

Crashes are injected by monkeypatching the act's named step functions, cut 40's
plus `_mark`, `_push` and `_verify`. Every arm ends `_durably`.

| unit | row | assertion |
|---|---|---|
| Y11-a | Y11 | two cases, each on a fresh attempt: the fake alters one export-root file's bytes after `push`, and the fake adds an extra file under `<corpus_id>/` after `push`; each → `transport-incomplete` (`listing-mismatch`), closed, no binding, the report's entries staging, export, reveal, transport |
| Y12-a | Y12 | a crash inside `_push` after one file is uploaded leaves `transport.v1` on disk, and a second publish of the view refuses `publish-unfinished` naming the token |
| Y12-b | Y12 | after the mark, an extra record raw-written into staging, then a crash in `_verify`; `resume_publish` answers `Published` with staging untouched by the resume (no `_stage_record` call, no `staging-corrupt`) |
| Y12-c | Y12 | two cases, each on a fresh attempt crashed in `_push`: the mark rewritten with another `corpus_id`, and the mark rewritten with another `artifact`; each resume → `PublishUnresolved("transport-mark-corrupt")`, the chain tip and the operations root byte-unchanged |
| Y13-a | Y13 | the fake abandons → `PublishRefused("transport-incomplete")`; a second publish binds, and its marker's `supersedes_markers` holds the abandoned attempt's pair |
| Y13-b | Y13 | attempt O abandons, which makes O a standing orphan; attempt T, whose intent's `marker_tips` names O, then abandons too; publish N then binds, and N's `supersedes_markers` holds both O and T |
| Y14-a | Y14 | the Ruling 12 case: `_bind` monkeypatched to raise before any effect after a verified transport → intent `unfinished`; a new publish refuses `publish-unfinished` with nothing written; `resume_publish` → `Published`; the new publish then binds and supersedes it |
| Y14-b | Y14 | an attempt crashed in `_initialize` (a request, no mark) does not block a second publish, which binds |
| Y15-a | Y15 | for each remote boundary — `_mark`, `_push`, `_verify`, `_bind` — crash then resume → `Published`, one binding revision, one report whose entries are staging, export, reveal, transport, binding; step 9 leaves the export root serviceable and the mark in place |
| Y15-b | Y15 | the one reachable `predecessor-not-standing`, cut 39's W17-p-a race driven through the act: A's `port` wrapper runs a whole remote publish B inside `append_intent`, after A's tip read and before A's intent. A transports, then its step 8 refuses `predecessor-not-standing` with `remotely_revealed: true`, and the next publish's `marker_tips` names A's pair |
| Y16-a | Y16 | a recipient materializes the fake remote, restores against the transported artifact, admits through `admit_publication`, and `publication_tip` answers `CurrentPublication`; the same copy missing one file restores to a non-`validated` verdict and `admit_publication` refuses |
| Y16-b | Y16 | sibling bindings: attempt A crashed in `_initialize`, publish B bound, then A resumed and bound at its own intent position. A recipient holding A and B reads `DivergentPublication` naming both; after the next publication C, whose binding tips are both, arrives → `CurrentPublication(C)` |

### 11.3 N2 sabotages — `n2_arms_cut42.py`

| unit | sabotage |
|---|---|
| Y11-a | the comparison checks only the names the act uploaded against their digests, so a digest change is caught but the extra file is not (the fake's listing restricted to the uploaded names) |
| Y12-a | the mark is written after `push` returns instead of before it |
| Y12-b | a resume with a mark re-runs the request path instead of starting at step 7 |
| Y12-c | the resume checks the mark against its intent only, not against the export root and the sibling |
| Y13-a | `_reports_at` yields `PreBinding(orphan=None)` for `transport-incomplete` |
| Y13-b | a `PreBinding` orphan also retires its intent's `marker_tips` |
| Y14-a | the `publish-unfinished` check is skipped |
| Y14-b | the check blocks on any unfinished attempt, marked or not |
| Y15-a | step 8's report omits the transport entry |
| Y15-b | the act passes `remotely_revealed=False` for a remote destination |
| Y16-a | `transport_files` omits the root's chain files, so the transport still verifies against its own listing but the recipient's copy cannot validate |
| Y16-b | `publication_tip` returns the lowest tip instead of `DivergentPublication` |

The plan fixes the declared accounting: 12 arms, 12 units and 6 rows as drafted
here (Y11–Y16). A unit whose check does not see its sabotage is rehomed at
Task 0, never dropped.

### 11.4 The cut

The cut document is `docs/designs/<freeze date>-conformance-cut-42.md`, dated
by the commit that freezes it after review. `tools/cut42_acceptance.py` uses
`MAIN_CHECKOUT` from `checkout.py` and sets:
- `PREFIX_RUNNERS = ("cut41_acceptance.py",)`;
- `PHASE_MODULES = ("test_publish_remote_acceptance.py", "test_n2_cut42.py")`.

The cut also adds its `test_recent_cut_acceptance.py` row (the runner import,
the `(runner, cut, accounting)` entry with 12 arms, 12 units and 6 guarantee
rows, and the guarantee-rows-exercised line) and the results record.

- **`root.py` stays the one `atoms` importer.** `transport.py` imports nothing
  of `atoms`, and it walks the export root with the standard library, as cut
  40's population reads staging files.
- **No new write primitive.** `_refuse_publication` and `_bind_publication`
  are existing entries in `WRITE_ENTRY_POINTS`, and the mark is a
  `durable.py` write outside every root. If planning finds a new caller of a
  write primitive, it joins `WRITE_ENTRY_POINTS` and gains a `Case` in
  `test_permit_entry_points.py`.

## 12. Documentation amendments

- **Layer design §6.1**, notes at the sentences they qualify:
  - step 4's remote export root is `<op>/export/<corpus_id>` (decision 7);
  - step 7 has a seam that the act verifies, a mark before the first byte, and
    a terminal `transport-incomplete` (decisions 1, 2 and 4);
  - step 8's orphans include a `transport-incomplete` refusal, and the
    asymmetry holds (decision 3);
  - the recovery table's remote row splits on the mark (§6);
  - step 0 refuses `publish-unfinished` (decision 6);
  - step 9 keeps the remote export root (decision 8).
- **§6.3:** `publication_tip` and `divergent-publication` (§7).
- **Act-report design** §2 and §6 item 3: the transport entry and the remote
  lifecycle.
- **Publication-records design** §6: an amendment note on the fold's
  `PreBinding` orphan and `unfinished_attempts`.
- **Cut 39 results §3.3:** Ruling 12 closed, cited by a note (the frozen
  body is not edited).
- **Ledger:** Y11–Y16 open, then closed at the results record. `publish`
  leaves Current state when the lane goal `beliefs-1a5157` closes.
- **Roadmap:** re-ranked at cut 42 with `publish` discharged. The next
  off-path row is `contract-cut`.

## 13. What this slice does not settle

These are recorded in `docs/guide/open-questions.md` and are not built:

1. **A recipient retiring a superseded corpus** through its registry
   lifecycle (§6.2). The reading says which marker is current, but nothing
   acts on it.
2. **A recipient's missing intermediate.** Decision 9 fails closed. Acquiring
   the gap is `science`'s discovery glue (§6.4).

## 14. Limitations

1. **Crashes are exceptions at step boundaries.** They are not kills inside
   `push`, which are `persistence-cut`'s along with engine-stage kills. Y12-a
   models a partial upload by the fake's own fault, not by a kill.
2. **The operations root is one per written root.** Step 0's
   `publish-unfinished` check and every resume read marks under the
   operations root the caller supplies. An attempt run under another
   operations root is invisible to them. This is the launcher's obligation,
   like the single-writer obligation (roadmap row 4), and the kernel cannot
   check it.
3. **In-process concurrent attempts can race the check** (§4.1). The window
   is repaired by the next publish, never left permanent.
4. **A remote's own retention is not the kernel's.** Verification reads the
   remote once. A remote that later loses or alters the files is caught by
   each recipient's `restore_root`, not by the publisher.
5. **Transport is reinvoked whole.** `push` re-sends every file on a retry.
   Resuming a partial upload is the seam's optimization, not the act's.

## 15. Task linkage

`beliefs-3ce305` carries `--spec publish-act-remote`, and the plan's
`### Task N:` headings become its children. When cut 42 discharges,
`beliefs-1a5157` reaches closeout.

## 16. Review log

- 2026-09-26: drafted. Decisions 2–6 answer cut 39's Ruling 12, which the
  task note's leading candidate (refusing on any unfinished attempt with a
  request) addressed only in part. The draft blocks only on a transport mark,
  adds a terminal `transport-incomplete` so that a broken remote cannot block
  a destination for ever, and makes the orphan rule asymmetric.
- 2026-09-26: user review, four findings, all taken after checking them
  against the code:
  - **The orphan scenario was unreachable.** Y15-b had B bind after A's
    intent. Step 8 judges tips at A's intent position, where B does not
    exist, so A binds as a sibling. Y15-b now drives cut 39's W17-p-a race
    through the act: a port wrapper commits B between A's tip read and its
    append, the one reachable `predecessor-not-standing`. Y13-b's orphan is an
    abandoned transport. Y16-b's divergence is two sibling bindings.
    Decision 6's claim about a late resume now says it binds as a sibling,
    repaired by the next publish.
  - **The mark was checked against its intent only.** A rewritten `corpus_id`
    or `artifact` could reach a binding. §4.2 now checks the mark against the
    export root's manifest and chain head, the sibling's identity, and the
    export's marker before any resume uses it. Y12-c covers both fields.
  - **`listing` took the uploaded names, so an extra remote file was
    invisible.** It now enumerates the publication's whole remote namespace,
    and Y11-a adds an extra-file case.
  - **The tip reading checked single markers only.** It now applies
    `admit_publication`'s corpus-level layout rule, moved into one shared
    `publication_layout_refusal`, to every corpus holding a marker at the
    address.
