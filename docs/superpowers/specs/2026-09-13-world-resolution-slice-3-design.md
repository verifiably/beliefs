# World resolution, slice 3 — snapshots, import, audit and diagnostics

**Date:** 2026-09-13
**Status:** draft, awaiting review
**Boundary:** `world-resolution`, slice 3 of four (`beliefs-d248ba`, task `beliefs-46847c`), carrying `packaging-remainder` with it
**Lane:** `world-read`, worktree `.worktrees/world-slice-3`
**Sources:** `../../designs/2026-08-02-world-addressing-design.md` (§5 "one evaluator, three callers", §5.1, §7 rows W8a, W13),
`../../designs/2026-08-02-computation-reproducibility-design.md` (§10 row R23),
`../../designs/2026-08-03-world-index-packaging-design.md` (§5.1, §5.4, §7, §9, §10 rows X1, X5),
`../../designs/2026-08-02-substrate-consolidation-design.md` (§6.2, the S table),
`../../designs/2026-08-03-redesign-adoption-ledger.md` (row 3 and its 2026-09-12 closure note),
`2026-09-09-world-resolution-slice-1-design.md` (§1, §3, §6, §9),
`2026-09-10-world-resolution-slice-2-design.md` (§13 item 3),
`2026-09-10-world-resolution-slice-2b-design.md` (§13 item 4),
`../../designs/2026-09-09-conformance-cut-23.md` (§2–§3)
**Measured against:** `main` at `355dd9e`

## 1. What this slice is

The world index's evidence of its own completeness is the derivation receipt.
Cut 7 built the one evaluator the world-addressing design names —
`world/read.py`'s `validate_receipt`: well-formedness from the document alone,
then availability, then the rebuild — and gave it one caller, the coreference
edge query. The design names three callers over that evaluator: an **explicit
import** that refuses what it can refute before any write, an **audit** that
evaluates stored pairs, reports every malformed pair as its own finding and
reduces a snapshot's state, and a **diagnostic query** that reports the same
result and writes nothing. None of the three exists on `main`. No act admits an
epoch carrier into `epochs/` other than publication; nothing reduces a
snapshot's receipts to `checked`, `contradicted` or `unchecked`; and the
"query" is a per-receipt function with no snapshot reduction.

The semantic audit has the mirror-image gap. `audit_corpus` is corpus-local and
reads the corpus root through the view's private handle; the three
recomputations it drives — verification, assessment, lineage basis — were
widened to the world view only for verification (cut 23, R19). And every
opener in the tree constructs a strict `nodes` corpus, so a damaged root — one
unparsable file, one misplaced file, one duplicated uid — is not judged but
refused, as `CorpusStateMalformed` naming the first fault. `nodes` 2.0 (landed
2026-09-12, `b0c37b8`) opens a corpus in *collecting* mode, excluding the
damaged, misplaced and colliding files and reporting each through `check()`;
the adoption ledger's row 3 records "audits over damaged corpora" as buildable
here and owned by no boundary until a cut selects it.

This slice builds the three callers, widens the audit to the world, makes the
audit judge a damaged corpus rather than refuse it, and closes the four
filed audit-finding questions from slices 1, 2 and 2b.

**Rows it closes or reads.** R23's snapshot, cross-corpus-divergence and
explicit-import clauses; W8a's import-boundary and audit arms; X5's relabel;
W13's remaining clauses; and one new row, S9 (§7), minted for the
damaged-corpus audit the ledger offered to this slice. With X5 full and W8a's
packaging arms read, the `packaging-remainder` boundary leaves the roadmap.

**Rows it does not touch**, each named to its owner: W7, view evaluation —
slice 4; W8 and W8b, retained unselected in `world-resolution` and audited at
slice 4's discharge (`beliefs-0e523a`), with `beliefs-fda0e5`'s build repair
already on `main` and the world view's own duplicate-uid refusal remaining a
slice 1 boundary invariant and never read as W8b conformance; R23's
rules-store clauses and W8a's `instrument-certification` omission-refutes arm
— `contract-cut`; the ledger's "manifest safety" item, which no audit caller
here reaches (§11).

## 2. Decisions

1. **The import unit is the epoch carrier.** A snapshot exists only inside an
   epoch beside its receipts, and the world-addressing arms speak of "a
   snapshot with a receipt" throughout; the eleven-member carrier is the one
   shape both take. `import_epoch` admits a carrier of *this* world into
   `epochs/` under its recomputed packaging identity, create-only. It touches
   neither `current` nor the registry: no pointer swap, and no log-head
   records, because a build's records assert an anchoring the build observed
   and an import observed nothing — the carrier's own `anchors.yaml` already
   states the triples, and the audit says which of them the registry
   corroborates (§4.3). *Rejected:* import as re-publication through
   `build_epoch`'s plan, which would swap `current` and mint `build`-origin
   registry records for an anchoring nobody here performed.
2. **Import refuses what it can refute now, admits what it cannot check, and
   stores no verdict.** Carrier structure first, then world membership, then
   every receipt through the one evaluator, in that order, before any write:
   a `malformed` or `refuted` receipt refuses the import with nothing written;
   an `unresolvable` receipt admits the carrier with a finding; `validated`
   admits it silently. No outcome is written anywhere — a later audit
   re-evaluates in its own availability context (world §5, "mount, then
   audit"). *Rejected:* refusing `unresolvable` too, which would make a
   receipt over a corpus not yet mounted here unimportable and leave R23's
   "cannot be checked here is `not-present`, not `unknown`" clause with no
   route to `contradicted`.
3. **The audit and the diagnostic query share the evaluator and write
   nothing; the correction is a rebuild.** World §5 calls the audit an
   effectful boundary "where a correction is published". The landed log audit
   (`_audit_log`, cut 8) writes nothing, and the epoch audit follows it: its
   effect is its report, and the correction a refuted receipt calls for is
   `build_epoch`, an explicit act the finding advises and never performs — an
   audit that rebuilt on its own would be a publication nobody asked for. The
   audit is distinguished from the query by **domain**, not effect: the audit
   sweeps every retained epoch, every pair and every covered corpus; the
   query answers one pair or one snapshot. W8a's "only the first two are
   effectful" arm is read as import refusing a write and audit and query
   writing nothing, recorded by dated note on the row (§8, precedent cut 24's
   note on the same row). *Rejected:* an audit report record written into the
   world root, which would make the audit a writer on exactly the surface it
   judges.
4. **A snapshot's state reduces over every retained receipt naming it.** Several
   receipts may name one snapshot (world §5) and they live in different
   epochs, so the reduction's domain is the retained set of this world, never
   one carrier. Over the **well-formed** receipts naming a subject identity:
   `checked` if any is `validated`; else `contradicted` if any is `refuted`;
   else `unchecked`. A `malformed` receipt is excluded from the reduction and
   reported as its own finding, so the two roads to `unchecked` stay apart.
   A retained carrier the world cannot read is a finding (`epoch-malformed`),
   not a refusal of the audit: X1's arm says a raw-edited member is "reported
   at audit", and an audit that refused on the first damaged carrier could not
   report it. *Rejected:* `delete_epoch`'s rule that a damaged carrier
   elsewhere refuses the act — right for a deletion, whose sever report must be
   complete, wrong for the act whose job is to say what is damaged.
5. **The world audit judges the capture, and a damaged carrier is reported,
   never served.** `audit_world` opens the world view at an explicit epoch in
   a mode that reports damage instead of refusing it: a present carrier whose
   strict construction fails is re-opened in collecting mode *inside the same
   capture hold*; its construction findings are recorded; its collected
   remainder receives the per-record structural checks and **no
   recomputation**; it gets **no state identity**, no drift comparison and no
   place in the served world — an address the map records for it **refuses**
   with `CorpusDamaged`, because a refusal must never read as absence (slice 1
   §6) and a record the audit cannot trust must never answer a read. Every
   other corpus is judged over its captured records, manifest included, so the
   per-corpus checks and the cross-corpus recomputations are one view.
   *Rejected:* a fourth `locate` answer for damage, which every slice 4
   consumer would then have to handle for a state only the audit ever opens.
6. **Drift, damage, absence, unknown attestation endpoints and shared
   secondary identifiers are audit findings with codes; belief reads none of
   them.** This answers slice 1's Q2, slice 2's item 3 and slice 2b's item 4
   (§5.4). Slice 1's Q1 — whether the absent set is a digest member of its
   own — is answered **no**: belief is invariant to availability (W8a's arm
   `test_belief_is_invariant_to_availability_and_requires_snapshot`), absence
   reaches belief as the `unavailable-corpus-absent` answer and reaches the
   digest through the lineage member exactly where it changed what was read;
   an absent corpus no inspected lineage touches changed nothing the belief
   consulted, and a digest that moved anyway would make the belief input a
   function of the checkout.
7. **The evaluator answers `unresolvable` for a carrier it cannot read.** On
   `main`, `_standing` constructs a strict corpus and a damaged carrier makes
   `validate_receipt` raise a `nodes` construction error instead of returning
   an outcome — so a coreference edge query over a damaged corpus raises where
   world §8.4 says it answers `indeterminate`. A carrier that cannot be read
   cannot stand at the named state: `unresolvable`, with a detail naming the
   fault, on the precedent of the unreadable manifest the same function
   already handles. Malformedness stays a property of the *receipt*; a
   damaged *corpus* is a property of the checkout, and the audit tells the
   two apart by also emitting the damage findings (§5.3).

## 3. The import act

### 3.1 Module and surface

New module `beliefs/world/importing.py`, re-exported through `beliefs.world`:

```
import_epoch(world: registry.World, source: Path) -> EpochImportReport

@dataclass(frozen=True)
class EpochImportReport:
    packaging_identity: str
    outcomes: Mapping[ReceiptKind, ReceiptOutcome]   # all four, always
    findings: tuple[Finding, ...]                     # receipt-unresolvable, per kind
    written: bool                                    # False for a byte-identical retained epoch
```

`EpochImportRefused(ScienceError)` is new in `errors.py`, carrying
`reason: Literal["malformed-carrier", "foreign-world", "malformed-receipt",
"refuted-receipt"]` and, for the receipt reasons, the offending
`ReceiptOutcome`s. It is one class with a closed reason set rather than four,
because a caller's response is the same — the carrier is not admitted — and
the reason is what it reports.

### 3.2 Order of operations

`import_epoch` requires the `epoch` permit, as `build_epoch` and `delete_epoch`
do, then:

1. **Read the carrier once.** `epoch._carrier_members(source)` reads the eleven
   members; a member set other than `EPOCH_MEMBERS`, a symlink, or an
   unreadable file is `EpochImportRefused("malformed-carrier")`. Every member
   is parsed as `_locked_open_epoch` parses it — the closed documents, the
   receipt carriers, the coverage and anchors — and the packaging identity is
   **recomputed** over the bytes. The source directory's name is never
   consulted: a supplied copy may sit anywhere and claims nothing.
2. **World membership.** The anchors member's world subject must be this
   world's id; otherwise `EpochImportRefused("foreign-world")`, the same check
   `open_world_view` makes.
3. **Every receipt, through the one evaluator.** An in-memory `Epoch` value is
   handed to `validate_receipt` for each of the four kinds. The evaluator's
   own order holds: well-formedness from the document alone, then the rule
   binding under one brief hold of the world lock, then each corpus under its
   own capture hold, then the rebuild. Any `malformed` outcome refuses with
   `"malformed-receipt"`; else any `refuted` refuses with `"refuted-receipt"`;
   each `unresolvable` outcome becomes a `receipt-unresolvable` finding. All
   four outcomes are evaluated before the decision, so the report names every
   fault and not the first.
4. **One hold, one plan.** Under `registry._locked_barrier`: if a carrier of
   the recomputed identity is retained and byte-identical, nothing is written
   (`written=False`) — publication's own rule for an exact rebuild; a retained
   carrier that differs cannot exist, since its members would recompute a
   different name, and `_locked_open_epoch` refuses it as `EpochMalformed`,
   which propagates. Otherwise eleven `CreateOp`s, and nothing else, execute
   through the world's executor factory. An emptied directory left by a
   deletion is created back into, as publication does.

Evaluation runs **outside** the world lock, as derivation does in
`build_epoch`; the hold covers only the retained-set check and the plan. A
corpus that moves between step 3 and step 4 changes what a later audit says
and nothing the import stored, because the import stored no verdict.

### 3.3 What an imported epoch is not

It is not `current`, until an operator publishes over it or points at it —
which no act here does. It is not anchored by the registry: no `build`-origin
log-head record names it, and §4.3's `anchor-uncorroborated` finding is how an
audit says so. It is not a belief input by arrival: belief names an explicit
epoch, and the import returned its identity for exactly that.

## 4. The epoch audit and the diagnostic query

### 4.1 Module and surface

New module `beliefs/world/audit.py`, re-exported through `beliefs.world`:

```
SNAPSHOT_STATES = ("checked", "contradicted", "unchecked")

audit_epochs(world: registry.World) -> EpochAudit
snapshot_state(world: registry.World, kind: ReceiptKind, subject_identity: str) -> SnapshotVerdict
# validate_receipt(world, published, kind) is the per-receipt query, unchanged in signature

@dataclass(frozen=True)
class SnapshotVerdict:
    kind: ReceiptKind
    subject_identity: str
    state: Literal["checked", "contradicted", "unchecked"]
    receipts: tuple[tuple[str, ReceiptOutcome], ...]   # (packaging_identity, outcome), sorted
    unreadable: tuple[str, ...]                        # retained carriers that did not open

@dataclass(frozen=True)
class EpochAudit:
    receipts: tuple[tuple[str, ReceiptKind, ReceiptOutcome], ...]   # every retained pair
    snapshots: tuple[SnapshotVerdict, ...]                          # every (kind, subject) named
    findings: tuple[Finding, ...]
```

Both functions write nothing and take no permit: they are reads. `Finding` is
`beliefs.corpus.Finding`, as every audit here reports.

### 4.2 The reduction

`audit_epochs`, under one hold of the world lock, crosses the recovery barrier
and lists the retained identities; each carrier is opened with
`_locked_open_epoch`. A carrier that refuses with `EpochMalformed` is recorded
as an `epoch-malformed` finding (`ref` the directory name, `detail` the
refusal) and contributes no receipt; the hold is released before any corpus is
touched, exactly as `validate_receipt` does. Every receipt of every opened
epoch is then evaluated. Findings: `receipt-malformed` (error; `ref` the
packaging identity, `detail` the kind and the contract fault),
`receipt-refuted` (error, with the evaluator's detail, and a message advising
a rebuild), `receipt-unresolvable` (warning: a property of this checkout).

The snapshot verdicts are computed over the outcomes just taken, grouped by
`(kind, subject_identity)` across all opened epochs, by decision 4's rule. A
subject reduced to `contradicted` also yields a `snapshot-contradicted`
finding (error; `ref` the subject identity, `detail` the kind), because the
state is the answer a reader of the receipt table wants and the finding is
the answer a reader of the findings list wants, and neither list should have
to be joined against the other.

`snapshot_state` is the same computation restricted to one subject: it opens
every retained epoch, evaluates only the receipts of that kind whose subject
identity matches, and reduces. A retained carrier that does not open is named
in `unreadable` rather than raised, for the same reason the sweep reports it:
the caller asked what this world's evidence says, and "one carrier could not
be read" is part of the answer. Two calls in one availability context return the
same verdict as one sweep, since they share the function.

### 4.3 Anchor corroboration

For every opened epoch and every corpus triple in its anchors member, the
audit checks the registry (already scanned under the hold) for a log-head
record carrying the same `(subject, genesis_digest, head_digest)` triple, of
any origin. A triple no record carries yields `anchor-uncorroborated`
(warning; `ref` the packaging identity, `detail` the corpus subject). A built
epoch always has one — publication writes the record in the same plan as the
members, or finds an identical one already there; an imported epoch has one
only if some build or anchor act here observed the same heads. This is the
audit's one statement about provenance, and it is the whole of it: nothing
here verifies a chain, and an observer set is still named explicitly by the
caller of the log audit (`verify.py` §4.1).

## 5. The world audit

### 5.1 Surface

In `beliefs/audit.py`:

```
audit_world(world: registry.World, published: epoch.Epoch, *,
            evidence: DerivationEvidence, profile: ProfileSpec) -> WorldAudit

@dataclass(frozen=True)
class WorldAudit:
    stamp: BoundStamp
    corpora: Mapping[str, tuple[Finding, ...]]   # every covered corpus id, absent and damaged included
    world: tuple[Finding, ...]                   # cross-corpus findings
```

`audit_corpus(view: ReadView, ...)` keeps its signature and its contract —
one corpus, live, findings keyed by that corpus's refs — and is not widened:
its `ref` namespace is one corpus's, and a flat tuple over a world would
force every consumer to guess which corpus a `corpus.yaml` finding meant.
What is widened is what it calls: `check_assessment`, `check_lineage_basis`
and `stored_specs` gain `WorldReadView` in their annotations, and their bodies
do not change — each reaches the view through `resolve`, `get`, `inbound` and
`iter_stored`, which the world view answers across corpora, and
`check_lineage_basis` already walks through the widened `_producers_of`.

### 5.2 Opening in report mode

`open_world_view` gains a keyword `on_damage: Literal["refuse", "report"] =
"refuse"`. Under `"refuse"` nothing changes. Under `"report"`, step 2 of
slice 1 §3.2 becomes: inside the corpus's capture hold, attempt the strict
open; if `Corpus` construction raises — `nodes`' parse, placement or collision
error, or any other exception construction raises — re-open in collecting mode
under the same hold, take the construction findings from `check()` (the
`parse-error`, `path-mismatch`, `uid-collision` and `id-collision` entries,
which lead the list), enumerate the collected remainder, and record the
corpus as **damaged** with those findings and that remainder. No state
identity is computed for it — an identity over a subset would claim a content
the corpus does not have — and no drift comparison is made.

The view gains:

```
damaged() -> tuple[DamageReport, ...]          # DamageReport(corpus_id, carrier, findings)
captured_records(corpus_id) -> tuple[Node, ...]   # detached copies; mapped and drift alike
captured_manifest(corpus_id) -> CorpusManifest    # read inside the hold
```

and one new refusal, `CorpusDamaged(ref, corpus_id, stamp)` in `errors.py`,
raised by `locate`, `resolve`, `holds`, `get`, `inbound` and `corpus_view`
for an address the map records under a damaged corpus. `iter_stored` yields
nothing from a damaged corpus; `absent()` and `drift()` exclude it; the
inbound index files no edge from its records and files edges *to* its mapped
addresses (the map records them), which `inbound` then refuses to answer for.
`corpus_of` answers from the map, as it does for an absent corpus.
`captured_records` and `captured_manifest` serve the audit's per-corpus
checks; for a damaged corpus the records are the collected remainder and the
manifest is what the hold read. Only the audit opens in report mode, and a
consumer that opens in report mode and reads a damaged address gets a refusal
and never a record.

A collecting-mode corpus never enters `_ROOT_STATES` and is never wrapped in
a `ReadView` a writer could reach: a private `_collecting_view(root)` in
`corpus.py` builds the `ReadView` over a fresh collecting `Corpus` for the
duration of the hold and returns it with the construction findings; the
facade's B3 rule is satisfied — the corpus is the exact `nodes` class — and
S8's is too, since the handle is created and dropped inside the view's open.

### 5.3 What the audit judges, per corpus

`corpus_check` is split, without changing its signature or its findings, into
two functions it now calls: `_manifest_findings(root_manifest, profile)` —
the `manifest-malformed` and `profile-mismatch` findings, over a *parsed
manifest* rather than a root path — and `_record_findings(records, profile,
scope, disagreeing)` — the per-record stamp, facet, coordination and
eligibility findings over any record iterable. `corpus_check` reads its
manifest from the root and its records from the live view, as today.

`audit_world` opens the view in report mode and, for every covered corpus in
sorted order:

- **absent:** one `corpus-absent` finding (warning; `ref` the corpus id);
- **damaged:** the construction findings, then `_record_findings` over the
  collected remainder with `_manifest_findings` over the captured manifest,
  then one `corpus-damaged` finding (error; `detail` the count of excluded
  files) stating that no recomputation and no drift comparison was made;
- **present and whole:** `_manifest_findings` over the captured manifest,
  `_record_findings` over `captured_records` — mapped and drift records alike,
  because a record raw-written into a carrier after publication is exactly
  what an audit exists to catch — then `drift` findings (warning) from the
  view's `DriftReport`: one with `detail="state"` when the captured state
  differs from the epoch's coverage pair, and one per unmapped uid with
  `detail="unmapped:<uid>"`, each with a message advising a rebuild.

Then, over the world view, the recomputations: for every **mapped** record
of every whole corpus, `check_verification`, `check_assessment`,
`check_lineage_basis` or `check_analysis_spec` by kind, under `audit_corpus`'s
existing catch — a `RecordError` is `derivation-malformed` — plus a new catch:
a `CorpusDamaged` or `RecordNotPresent` raised from inside a recomputation is
`derivation-unreachable` (warning; `detail` the corpus id), because the audit
could not judge, which is not a contradiction and not a malformed record.
Findings from recomputations are filed under the corpus that holds the
record; the lineage-basis check over the world view is where R23's
cross-corpus divergence surfaces at audit (§7).

### 5.4 The world-level findings

Over the view, in `WorldAudit.world`:

- `attestation-endpoint-unknown` (warning; `ref` the attestation's address,
  `detail` the endpoint): a `coreference-attestation` whose endpoint the
  epoch's map never observed — `locate` answers `Unknown`. A `NotPresent`
  endpoint is not this finding: it is held elsewhere and the reduction
  still covers it. This is slice 2's item 3: a deleted endpoint leaves an
  attestation naming an address no live or retired entry carries.
- `source-identifier-shared` (warning; `ref` the lower of the two addresses,
  `detail` `<scheme>:<normalized value>` of the shared identifier): two
  `source` records at different addresses whose normalized identifier sets
  intersect. Slice 2b's item 4: precedence makes such a pair two addresses,
  and the finding is the CI-decidable statement that they may be one work.
  It asserts nothing; an attestation or a correction is the operator's.
- `receipt-*` and `snapshot-contradicted` for the audited epoch's own four
  receipts, evaluated through §4's reduction over the retained set, so a
  reader of one world audit sees the standing of the epoch it was bound to.

### 5.5 Codes

The new codes form a closed set, `WORLD_AUDIT_CODES`, beside
`MALFORMEDNESS_CODES`:

| code | severity | layer | ref / detail |
|---|---|---|---|
| `epoch-malformed` | error | epoch | carrier name / refusal |
| `receipt-malformed` | error | epoch | packaging identity / kind: fault |
| `receipt-refuted` | error | epoch | packaging identity / kind: evaluator detail |
| `receipt-unresolvable` | warning | epoch | packaging identity / kind: evaluator detail |
| `snapshot-contradicted` | error | epoch | subject identity / kind |
| `anchor-uncorroborated` | warning | epoch | packaging identity / corpus subject |
| `parse-error`, `path-mismatch`, `uid-collision`, `id-collision` | error | corpus | `nodes`' own ref and detail, adopted verbatim |
| `corpus-damaged` | error | corpus | corpus id / excluded-file count |
| `corpus-absent` | warning | corpus | corpus id / — |
| `drift` | warning | corpus | corpus id / `state` or `unmapped:<uid>` |
| `derivation-unreachable` | warning | corpus | record address / corpus id |
| `attestation-endpoint-unknown` | warning | world | attestation address / endpoint |
| `source-identifier-shared` | warning | world | lower address / scheme:value |

`nodes`' four construction codes are adopted under Science's namespace without
renaming: they name per-file facts Science did not define and could only
restate, and a rename would break the one join a reader has between the audit
and `nodes`' own `check()`.

## 6. Refusals

| condition | answer |
|---|---|
| a carrier with a member set other than the eleven, a symlink member, or an unreadable member | `EpochImportRefused("malformed-carrier")`, nothing written |
| a carrier whose world anchor names another world | `EpochImportRefused("foreign-world")`, nothing written |
| any receipt `malformed` | `EpochImportRefused("malformed-receipt")` naming every such kind, nothing written, availability never consulted for that kind |
| any receipt `refuted` (and none malformed) | `EpochImportRefused("refuted-receipt")` naming every such kind, nothing written |
| a receipt `unresolvable` | admitted, `receipt-unresolvable` finding on the report |
| a retained carrier of the same identity, byte-identical | admitted, `written=False` |
| a retained carrier of the same identity that does not read | `EpochMalformed`, propagated from the locked loader |
| the caller lacks the `epoch` permit | the authority's refusal, before the carrier is read |
| a retained carrier that does not read, under audit | `epoch-malformed` finding; the sweep continues |
| a covered carrier whose strict open fails, under `on_damage="refuse"` | `CorpusStateMalformed` at open, as on `main` |
| the same, under `on_damage="report"` | a `DamageReport`; its addresses refuse with `CorpusDamaged` on every read |
| a covered carrier the receipt evaluator cannot read | `unresolvable`, never an exception |
| a collecting-mode corpus reaching a writer or `_ROOT_STATES` | unconstructible: the handle never leaves `open_world_view` |
| a read through a report-mode view of a damaged address | `CorpusDamaged` — a refusal, never `NotPresent`, never `Unknown` |

No refusal here may borrow `NotPresent` or `Unknown`, and nothing that refuses
enters `absent()`, `not_present` or the resolution snapshot's third state.

## 7. What this slice measures rather than builds

**R23's cross-corpus divergence, negative (e).** With `R1` minting `D` from
`A` in corpus X and `R2` producing byte-identical `D` from `B` in corpus Y,
the world view's `_producers_of` already unions both runs through the world
inbound index and `divergence_state` compares each producer's `transforms`
against the `single` route. The arm is expected to pass on the tree:
`lineage-divergent`, `not-certified`, and a belief digest that moves when
`R2` is added. It is declared as a measured arm; if it fails, the fix is a
change to slice 1's code and is recorded as such in the results record.

**X5 — relabel to full.** The admission arm ran at cut 6, the build arm at
cut 7, and neither relabelled (cut 7's own X5 entry). The "replica declaration
excepted, minting no admission" clause is carried by
`test_replica_restoration_recomputes_presence_without_admission`; the R34
ruling (log-verification ledger) that cut 6's replica *refusal* half was
superseded by `ReplicaAdmissionRequiresVerification` is cited in the relabel
note and does not weaken the row, whose claim is that a known id mints no
second admission. No new arm.

**W13 — relabel to full, with two new fixtures and one superseded clause.**
Read on `main`: no-re-mint, every state-identity clause, the manifest's
three-way split, the not-git negative (cut 6); the fork copy act (cut 9,
`W13u1`/`W13u2`); the two-projects negative (cut 14); manifest-only re-mint
refused at build (cut 7, `test_build_refuses_unadmitted_manifest_carrier`);
uniqueness as corruption with no merge offered (cut 7's duplicate-carrier
refusal, read as the row's "W8b handling, not the duplicate-location one":
`CoverageUnresolvable` with the `duplicate-carrier` finding and no repair act);
replica restore (cut 6, `test_replica_restoration_recomputes_presence_without_admission`);
raw-deleted admission undetected (cut 6, `test_raw_admission_deletion_is_undetected`).
New arms: the **root-move fixture** — move, rename and re-mount a covered
corpus's root, updating `WorldConfig`, rebuild, and assert `corpus_id`, the
coverage declaration and `belief_input_digest` unchanged; "re-clone it and
mount it at a second path" is read as mounting the clone *instead*, since a
second live carrier is the row's own uniqueness clause; and the **coordinated
forgery fixture** — raw-edit the manifest's id, raw-forge an admission for the
new id beside the retained old one, assert the build proceeds and no finding
is emitted; mount a pre-edit replica under the old id and assert every receipt
naming the old states is `unresolvable` against the edited corpus and
`validated` against the replica; assert the registry reads as a declared
fork's would. The **file-rename inertness clause** is superseded, as the
adoption ledger's 2026-09-12 note records: under `nodes` 2.0 a renamed node
file is a placement fault, the strict open refuses and the collecting audit
reports `path-mismatch` — its replacement arm is S9's, cited from W13's
relabel note rather than rerun.

**S9 — the new row.** The substrate design's S table gains, by dated
amendment, `S9`: *An audit judges a damaged corpus rather than refusing it —
construction faults are findings, the remainder is audited, and no state
identity is claimed.* Mutation test: damage a covered corpus one way at a time
— an unparsable file, a misplaced file, two files sharing a `uid`, two files
claiming one id — and assert the world audit reports the matching
construction finding, audits the remainder, records `corpus-damaged`, makes
no drift comparison, and that every read of a mapped address in that corpus
refuses with `CorpusDamaged`; assert the receipt evaluator answers
`unresolvable` for a receipt naming it. **Negative:** the default open still
refuses with `CorpusStateMalformed`; a state identity is never computed over a
collected remainder. The formal model's coverage map and
`test_designs_corpus.py`'s `S` table gain the id.

## 8. Testing and the cut

**Fixtures.** The two-corpus world of `test_world_build.py` (`admitted_world`,
`publish`) and cut 23's chain fixture on the certified volume. The
`repackage` helper of `test_world_receipts.py` is promoted to a shared test
module, and gains a variant that writes the repackaged carrier to a directory
*outside* the world root, for import. Damage is produced by raw-writing a
carrier after publication; absence by dropping a root from `WorldConfig`;
drift by writing to a carrier after publication — never by deleting records
the epoch mapped, which the view refuses as corruption.

**Arms**, grouped by row.

- *R23 explicit import and snapshot:* the trimmed producer snapshot (one entry
  deleted, coverage and receipt intact, repackaged) is refused at import
  because the rebuild disagrees; a carrier missing a receipt member is refused
  as malformed; a receipt naming a corpus rather than a state, and one naming
  a bare version string, are refused as `malformed-receipt` with no corpus
  present and no rule held; a receipt over a corpus absent here imports with
  a `receipt-unresolvable` finding, no verdict is stored, and a later audit
  after mounting that corpus evaluates it; a receipt whose corpus has moved
  is `unresolvable`, and with two corpora one moving is `unresolvable`; a
  fabricated carrier raw-written into `epochs/` is opened and read through
  (`open_epoch`, `resolve_address`) with the evaluator patched to fail —
  proving no read evaluates — and the audit then reports it; an all-malformed
  snapshot is `unchecked` with a `receipt-malformed` finding per pair, never
  `contradicted`.
- *R23 cross-corpus divergence:* §7's measured arm.
- *W8a import-boundary:* the well-formedness-before-availability set — a
  receipt naming only `A` of `{A, B}` with `A` standing is refused as
  malformed and never `validated`; extra corpus, duplicate id, wrong subject
  identity each refused; syntactically valid identities not held here are
  `unresolvable`, not malformed; every malformedness decided with no corpus
  present and no rule held.
- *W8a audit and query:* a malformed receipt raw-written past the boundary
  evaluates `malformed` under audit and under `snapshot_state`, with a
  finding naming the pair; the reduction excludes it (`unchecked`, not
  `contradicted`); a validating receipt beside it makes the snapshot
  `checked` with the malformed finding still emitted; an all-malformed
  snapshot and a merely-absent one both read `unchecked` and only the first
  carries malformed findings; mounting a corpus (admission, `open_world`)
  evaluates nothing, asserted with the evaluator patched to fail; import,
  audit and query in one availability context agree; the same pair is
  `unresolvable` before a corpus arrives and `refuted`/`validated` after
  mount and audit; a resolvable-and-refuted receipt is refused at import
  with no file afterwards; the unheld-rule route — import with a finding,
  install the rule, audit — evaluates.
- *W8a effect:* import refuses a write; audit and query write nothing —
  asserted over the world root's byte inventory before and after.
- *Anchor corroboration:* a built epoch's anchors are corroborated; an
  imported carrier's are not, and are, once an anchor act records the same
  heads.
- *X5 and W13:* §7's relabel notes and the two new W13 fixtures.
- *S9:* §7's mutation test, one damage kind per arm.
- *Audit findings:* drift (`state`, `unmapped`) after a post-publication
  write; `corpus-absent`; an attestation whose endpoint was deleted before a
  rebuild reports `attestation-endpoint-unknown` at the new epoch and a
  `NotPresent` endpoint does not; two source records sharing a secondary
  identifier under different selected schemes report `source-identifier-shared`
  and two sharing nothing do not; a recomputation whose closure crosses into a
  damaged corpus is `derivation-unreachable`; every per-record finding of
  `corpus_check` reproduces over a captured record, mapped or drift, through
  the world audit, and `audit_corpus` over one corpus is byte-for-byte what it
  was.
- *The evaluator over damage:* `validate_receipt` answers `unresolvable` for
  a damaged carrier and the coreference edge over it is `indeterminate`.
- *Refusals:* each row of §6.

**N2 sabotages**, one per mechanism: the well-formedness gate (evaluate
availability first); the refuted gate (admit a refuted receipt); the pointer
(write `current` on import); the registry (write log-head records on import);
the identity (trust the source directory's name); world membership (skip it);
the reduction domain (reduce over the audited epoch alone); malformed
exclusion (fold a malformed receipt into the reduction); the damaged-carrier
finding (skip a carrier that does not read); corroboration (check the epoch's
anchors against itself); the evaluator's standing (raise on a damaged
carrier); the audit's open (open strict); the state identity (compute one over
the collected remainder); damaged addresses (serve them); drift (omit it); the
capture (run `_record_findings` over the live view); the endpoint check
(resolve corpus-locally instead of through the map); the identifier check (key
on the selected identifier only); recomputation over damage (report
`derivation-malformed` instead of `derivation-unreachable`).

**The cut.** This design freezes as **cut 27** under the lane rules — the
number is free on every branch and worktree on 2026-09-13 — with
`PREFIX_RUNNERS = ("cut26_acceptance.py",)` and `PHASE_MODULES =
("test_world_audit_acceptance.py", "test_n2_cut27.py")`. Declaration units:
`R23`, `W8a`, `X5`, `W13`, `S9`. Expected accounting: X5 and W13 full by
relabel, S9 closes, R23 and W8a part — R23 on its rules-store clauses and W8a
on its `instrument-certification` arm, both `contract-cut`'s. Every durable
arm runs on the certified volume; the staleness probe's baseline is the
tree's output, never an empty list. The results record adds the dated notes
of §2.3 and §7 to the W8a and W13 rows, the S9 row to the substrate design and the
formal model, and retires `packaging-remainder` from the roadmap and ledger.

## 9. Shared files, under roadmap concurrency rule 3

Rewritten by this slice: `errors.py` (`EpochImportRefused`, `CorpusDamaged`),
`corpus.py` (`corpus_check`'s split, `_collecting_view`), `audit.py`
(`audit_world`, `WorldAudit`, `WORLD_AUDIT_CODES`, three widened annotations),
`world/view.py` (`on_damage`, `DamageReport`, `damaged`, `captured_records`,
`captured_manifest`), `world/read.py` (`_standing`), `world/__init__.py` and
`root.py` (re-exports), `python/tests/test_designs_corpus.py` (the `S` table),
the ledger, the roadmap and the guide index. New: `world/importing.py`,
`world/audit.py`. Dated notes: the world-addressing design (W8a, W13), the
substrate design and the formal model (S9), the adoption ledger (row 3's
"audits over damaged corpora" selected here). Slice 4 touches `world/view.py`
and `audit.py` after this slice merges; no other open lane names these files.

## 10. Task linkage

`beliefs-46847c` carries this spec (`tasks edit --spec`); the implementation
plan's tasks become its children. Slice 4 (`beliefs-0e523a`) stays a sibling
under `beliefs-d248ba` and inherits the W8/W8b audit obligation named in §1.

## 11. Limitations and open questions

1. **The excluded files are unjudged.** The collecting audit reports *that* a
   file failed construction and *which* fault, and audits the remainder; it
   says nothing about what the excluded file would have held or which records
   its absence leaves dangling. That is `nodes`' well-placedness bound,
   inherited.
2. **A malformed `nodes` index cache refuses both modes.** `Corpus` loads
   `.nodes/snapshot.py.json` before construction mode applies; a damaged cache
   is a bare `ValueError` in either mode and the audit reports the carrier as
   damaged with that detail. Making the cache recoverable is `nodes`' own.
3. **"Manifest safety" stays unowned.** The ledger's other row-3 item names
   the reserved-path contract's guarantee that a root-level non-node file is
   not a walk hazard; no caller widened here reads it, and `corpus_check`'s
   `manifest-malformed` finding is already what a broken manifest yields. It
   is recorded as unselected, not as done.
4. **W8 and W8b are retained, unselected.** Slice 4 audits both labels at its
   discharge. The world view's duplicate-uid refusal at open is slice 1's
   boundary invariant and is not read here as W8b's build half.
5. **A writer on a damaged root still fails at construction.** `_root_state_for`
   caches one strict corpus per root; every write act on a damaged root
   refuses before its own logic runs. The audit can now say why; nothing here
   makes the root writable.
6. **Serial captures.** Slice 1's limitation 1 carries: the world audit's
   cross-corpus recomputations are over a sequence of per-corpus coherent
   captures, not one simultaneous world state.
7. **Corroboration is not verification.** `anchor-uncorroborated` says whether
   the registry saw the heads an epoch names; it does not replay a chain, and
   an epoch named as an observer carrier is still the caller's choice.

## 12. Review log

*(none yet)*
