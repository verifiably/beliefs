# Conformance cut 6 — the world registry

**Status:** Frozen 2026-08-20; second reader discharged 2026-08-20 (§6.1),
its five findings and two pre-freeze record corrections closed before freeze.
Discharged 2026-08-20; [results](../plans/2026-08-20-conformance-cut-6-results.md).

**Sources:** `2026-08-19-conformance-cut-5.md`; the world-registry
specification `2026-08-20-world-registry-design.md` §8; and the frozen X and W
rows quoted below.

## 1. What this cut is

Cut 6 is the frozen acceptance boundary for the authoritative world-registry
slice: the world root, the corpus manifest and fresh-adoption act, corpus-state
identity, admission, terminal lifecycle status, and computed presence. It
selects obligations before their implementation.

The selection rule is cut 5's rule, unchanged: a clause is selected only when
its source mutation and every named check run entirely inside §2. A row is
**full** only when cut 6 runs every arm in its frozen cell; one unrun arm makes
it **part**, even when a prior cut exercised that arm or an argument says it
should not count. A row with no cut-6 arm is **deferred**. Prior-cut evidence
remains evidence, but it is not silently relabelled as cut-6 selection.

One structural inheritance from cut 4: a behavior this slice adds that no
frozen cell names is carried as a **labeled declaration outside the frozen
selection** (§3.3), on the `semantic-hash-missing` precedent. A labeled
declaration is sabotaged and run like a selected arm; it discharges no frozen
row and inflates no row accounting.

## 2. The boundary

In scope:

- the caller-supplied `WorldConfig` value, including the caller-minted
  `world_id` and the configured presence set;
- `init_world_root` and `open_world`, the world genesis payload, and the
  root-local `world.yaml` mirror;
- closed loading and canonical projection of `corpus.yaml`, and the
  fresh-adoption act minting `corpus_id`;
- `corpus_state_identity` over the complete manifest projection plus sorted
  `(uid, node content identity)` pairs;
- admission records for `fresh`, `replica-of`, and `fork-of` provenance —
  `fork-of` exercised against fixture-authored manifests only;
- terminal `retired` and `departed` status records, computed `known`, `live`,
  and `present`, and presence resolution over the configured roots;
- the whole-read registry validation refusal, the `duplicate-carrier` finding,
  and the `manifest-malformed` corpus-check strengthening;
- committed registration-entry evidence for the durable writes this slice
  introduces, decoded from the engine-owned chain as acceptance evidence; and
- a cut-6 acceptance runner over the certified engine tuple. Portable tests
  remain portable; a selected durable arm errors rather than skips when that
  tuple is unavailable or fails.

Out of scope:

- **epochs and builds**: the address/producers/retraction/coreference maps,
  every derivation receipt, coverage declarations, `current`, staleness, and
  GC;
- the **rules store**, anchored head members, and any `atoms` chain-read API
  (none existed at cut-6 freeze);
- **full chain replay or refutation** and **genesis-to-mirror agreement** —
  the deferred log reader's claims; committed registration-entry evidence is
  the whole durable claim here;
- the **fork constructor** and every copy-time fork act;
- the global **audit** and every clause whose detector is audit-only;
- **cross-process locking** — single-writer deployment remains the stated
  obligation; and
- the `nodes` **reserved-path contract** — `corpus.yaml`'s survival of the
  observed `*.md` walk is relied on and not certified.

> **Dated recast 2026-08-20:** world-index slice 2 §2 now banks the prospective
> public `atoms.read_chain` contract. The command remains outside this frozen
> cut and is not backported. Genesis-to-mirror verification remains deferred
> on audit ownership, not on the ability to specify a reader.

Raw filesystem writes may construct negative fixtures; they are not registry
operations and do not make the build, the audit, or deletion part of the
slice.

## 3. The selection, against the frozen rows

The code blocks preserve each source row verbatim. **Selected** bullets are
the complete arm inventory that the N2 declarations must enumerate; every
**deferred** bullet names its unblocker.

### 3.1 The registry rows

#### X4 — full

```markdown
| X4 | The registry is append-only through every API | assert no API mutates or deletes a registry record; attempt a purge → unspellable. **Negative (limitation 1):** raw deletion of an admission record is undetected until §9 lands |
```

- **Selected:** assert no `World` API mutates or deletes a registry record and
  that no purge, replace, or delete operation is spellable through the public
  surface.
- **Selected:** raw-delete an admission record and assert the loss is
  undetected — subsequent registry reads and status computations succeed with
  no finding — pinning packaging limitation 1 as built rather than leaving it
  prose. This selects the negative as an undetectability assertion, on cut 5's
  S3 precedent; it claims no detection.

#### X5 — part

```markdown
| X5 | Duplicate `corpus_id` is refused at admission and detected at build | admit a known id → refused (replica declaration excepted, minting no admission); raw-place two corpora with one id, build → refused, reported |
```

- **Selected:** admit a corpus whose `corpus_id` an existing admission already
  makes known and assert `CorpusIdKnown` refusal with no file written — the
  mutation parameterized over provenance, as the frozen cell's own exception
  clause invites: a differing `fresh` admission refuses, and a
  `replica-of(parent)` admission naming an already-admitted id refuses
  identically, pinning the specification's uniform refusal as a tested fact.
  Two narrowings are recorded rather than argued away: the frozen **replica
  exception** is narrowed by interpretation — replicating an admitted corpus
  requires no registry act at all, so the excepted act's "minting no
  admission" runs as X6's selected replica-presence arm, and `replica-of`
  provenance describes only a first arrival — and the frozen **unconditional
  refusal** is narrowed by the specification's idempotent exact-retry
  exception, carried as §3.3's admission idempotency labeled unit.
- **Deferred:** the raw-placed duplicate detected at **build** waits on slice
  2's epoch build. The `duplicate-carrier` finding (§3.3) is its local
  precursor, not its discharge.

#### X6 — full

```markdown
| X6 | Status is monotone and terminal states are terminal | emit `retired`, attempt any act returning the corpus to live → unspellable; make an admitted, live corpus unreachable, then restore a replica carrying its id → `present` recomputes true with **no new admission record**; assert every status is invariant under record arrival order |
```

- **Selected:** emit `retired` and assert no act returns the corpus to live:
  re-admission refuses on the known id, and no un-retire or status-clearing
  API is spellable. The refusal of a differing post-terminal status act is
  spec-added behavior and is declared exactly once, as §3.3's status
  idempotency labeled unit, not here.
- **Selected:** make an admitted, live corpus unreachable from the configured
  presence set, then restore a byte-copy replica carrying its id at a
  configured root; assert `present` recomputes true with no new admission
  record and an unchanged registry.
- **Selected:** materialize one record set under different arrival orders and
  assert every computed status is identical — content-named files carry no
  order, and no reduction consults one.

#### X7 — deferred

```markdown
| X7 | Admission is the cross-root commit point | build a coverage naming a manifest-bearing but unadmitted corpus → refused; admit it → same build proceeds |
```

- **Deferred:** both arms are build-side and wait on slice 2's epoch build and
  its cut.

### 3.2 W13 — the identity row

```markdown
| **W13** | A corpus identity is minted, opaque and stable; its state identity is over content (§5) | Move a corpus's root directory, rename it, re-clone it and mount it at a second path; assert `corpus_id` is **unchanged** in every case, and that the coverage declaration naming it — and therefore `belief_input_digest` — is unchanged with it. Assert `corpus_id` is **not** derived from the path, directory name, remote URL or project name: change each and assert no effect; and assert **no ordinary API re-mints** it for an existing corpus. **Negative — amended 2026-08-03 (packaging §4): the immutability is the API's; manifest-only re-minting is detected, coordinated forgery is not.** Raw-edit the manifest's `corpus_id`, regenerate the snapshot and receipt consistently, and assert the next index build **refuses** — the presented id has no admission record while the registry still names the original (packaging X7). Then perform the **coordinated** act: raw-forge an admission for the new id while **retaining** the old id's admission — as a legitimate fork's registry would read — and assert **nothing detects it**: every state identity is self-consistent and the registry is well-formed. Under that retained-admission variant, assert the case that *looks* like a detection is not one: keep an **older replica** still resolving the pre-edit states, and assert every receipt naming them is **unresolvable against the edited corpus** (its states all moved with the id), that resolving them against the replica validates **the replica**, that **no assertion ties the new id to the old**, and that the resulting pair is **indistinguishable from a declared fork**. **Separately**, raw-delete an admission record alone and assert both halves: nothing detects the loss, **and** it evades nothing — the re-minted id is still unadmitted and the build still refuses (packaging X7). Assert no finding is emitted for any undetected case — G4/G8/S3's undetectable-history limit, one partial detection deep, needing §9's log for the rest. **Uniqueness:** place two corpora carrying one `corpus_id` in one world and assert the index build reports **corruption** and offers **no merge** — the W8b handling, not the duplicate-location one. **Replica vs fork:** restore a corpus from a backup and mount it in place of the original; assert the id is **retained** and every coverage declaration naming it still resolves. Then copy a corpus as a **fork**; assert a fresh id is minted, that the declaration is **authored** rather than inferred from the bytes, and that an undeclared fork is caught **only** when both corpora are live in one world. **State identity is content, not filesystem:** change a node's content and assert the corpus-state identity moves; **add, remove and retarget a `produces` relation** and assert it moves each time, **while the run's world address and every semantic identity stand still** — the case a subset-based content identity would have missed and the producers map is derived from. Then reformat a non-node file **other than the manifest**, rename a node's **file** without changing its `uid` or content identity, and touch every mtime, and assert the state identity is **unchanged**. **Amended 2026-08-04 (domain-extension-boundary §7): the manifest splits three ways** — reformat `corpus.yaml` (whitespace, key order, quoting) or reorder its `domains` mapping and assert the state identity is **unchanged**, since the member is a canonical projection of the parsed manifest; change any manifest field **semantically** — a pinned `science_contract` or domain contract identity, `corpus_id`, fork provenance — and assert it **moves**; and assert an unknown field, a duplicate `domains` key, or a malformed contract identity is **refused at load** rather than digested. Assert the identity is computed over `nodes`' **canonical JSON projection** (`STANDARD.md` §11.1) including `relations` and `facets`, and that **reordering a node's relations does move it** — the deliberate false positive, since cross-language equality is defined over document order. **Negative — not git:** compute the state identity for a corpus that is **not a repository** and assert it exists; then, in one that is, modify an **untracked** node file and assert the state identity **moves** while `HEAD` does not, and commit with no content change and assert it does **not** move. **Negative — a project identity is not a corpus identity:** point two projects at one corpus and assert one `corpus_id`; repoint a project to another corpus and assert **no** corpus identity changed |
```

W13 is **part**. Selected:

- **Selected:** adopt a fresh manifest, then move the corpus's root directory,
  rename it, and mount a re-clone at a second path; assert `corpus_id` is
  unchanged in every case and derives from neither path nor directory name.
  The remote-URL and project-name clauses have no local analog in this slice
  and are recorded as narrowed, not claimed.
- **Selected:** assert no ordinary API re-mints an existing corpus's id: fresh
  adoption over any existing manifest refuses.
- **Selected:** change a node's content and assert the corpus-state identity
  moves; add, remove, and retarget a `produces` relation and assert it moves
  each time while every semantic identity stands still. The world-address
  clause waits on the world resolver and is recorded as narrowed.
- **Selected:** reorder a node's relations and assert the state identity moves
  — the deliberate document-order positive, computed over `nodes`' canonical
  §11.1 projection including `relations` and `facets`.
- **Selected:** rename a node's file without changing its `uid` or projected
  content, reformat a non-node file other than the manifest, reformat
  `corpus.yaml` (whitespace, key order, quoting), reorder its `domains`
  mapping, and touch every mtime; assert the state identity is unchanged in
  each case.

  *(2026-09-12:)* the file-rename arm is superseded by `nodes` 2.0's
  well-placedness (its STANDARD §4.1): a node file at a path other than its
  id's mapped path is a member strict construction refuses, so the move is a
  placement fault reported as `CorpusStateMalformed`, not an inert change
  (`test_a_misplaced_node_file_is_a_malformed_state`). The other inert arms
  stand as discharged.
- **Selected:** change a manifest field semantically — a pinned contract
  identity, `corpus_id`, fork provenance — and assert the state identity
  moves.
- **Selected:** present a manifest with an unknown field, a duplicate
  `domains` key, and a malformed contract identity in turn; assert each is
  refused at load and never digested.
- **Selected:** compute the state identity for a corpus that is not a git
  repository and assert it exists; in one that is, modify an untracked node
  file and assert the identity moves while `HEAD` does not, then commit with
  no content change and assert it does not move.

Deferred, each with its unblocker:

- **Deferred:** the coverage-declaration and `belief_input_digest` invariance
  clauses wait on the **world index and belief wiring**.
- **Deferred:** manifest-only re-mint detection, the coordinated forgery and
  its older-replica variant, the evades-nothing half of lone admission
  deletion, and the two-corpora uniqueness corruption all wait on slice 2's
  **epoch build** (and, for the receipt clauses, its receipts). The local
  undetectability of raw admission deletion is X4's selected negative.
- **Deferred:** the replica-restore-with-resolving-declarations clause's
  declaration half waits on **coverage declarations**; its presence half is
  X6's selected replica arm. The fork copy act waits on the **fork
  constructor**; the undeclared-fork-caught-when-live clause waits on the
  **build**.
- **Deferred:** the two-projects negative waits on a **project/coordination
  surface**, which no slice has built.

### 3.3 Labeled declarations outside the frozen selection

Eight declarations, on cut 4's `semantic-hash-missing` precedent, each
sabotaged like a selected arm. Seven are named by the world-registry
specification §8.1's idempotency, durable-evidence, and corpus-check bullets;
the `duplicate-carrier` declaration's authority is instead the specification's
normative §5.4 and §7 — §8.1's bullet list does not name it:

- **Labeled (idempotency, admission):** repeat an admission with identical
  content; assert idempotent success returning the committed record, no second
  file, and no refusal.
- **Labeled (idempotency, status):** repeat a terminal status act with
  identical content; assert idempotent success; then attempt a differing act
  after terminality — the other terminal status, and the same status under a
  different actor — and assert `StatusTerminal` refusal.
- **Labeled (idempotency, initialization):** interrupt `init_world_root`
  between genesis registration and the mirror transaction; assert a re-run
  with the same `WorldConfig` completes the mirror idempotently, a full
  re-run is a no-op, and a re-run whose `world_id` differs from the
  registered genesis payload is refused by the engine's own precondition.
- **Labeled (durable evidence, mirror):** on the certified tuple, assert
  init's mirror transaction commits a registration entry naming `world.yaml`.
- **Labeled (durable evidence, manifest):** on the certified tuple, assert the
  adoption act's transaction commits a registration entry naming
  `corpus.yaml`.
- **Labeled (durable evidence, registry):** on the certified tuple, assert
  each admission and status append commits a registration entry naming its
  `registry/` path.
- **Labeled (presence, duplicate carrier):** configure two roots carrying one
  `corpus_id`; assert `present` is false together with an error-severity
  `duplicate-carrier` finding naming the id and both resolved roots — never
  ordinary absence (specification §5.4). Slice 2's X5 build arm turns this
  finding into refusal.
- **Labeled (corpus check, manifest):** a present `corpus.yaml` that
  `load_manifest` refuses emits the `manifest-malformed` corpus-check finding;
  an absent manifest emits none — unadopted corpora remain a legal state.

## 4. Accounting

Cut 6 reads 5 frozen rows: **2 full + 2 part + 1 deferred = 5**.

| state | rows | n |
|---|---|---:|
| full | X4, X6 | 2 |
| part | X5, W13 | 2 |
| deferred | X7 | 1 |

The 8 labeled declarations in §3.3 sit outside this row accounting and
discharge no frozen row.

This is row accounting, not a denominator of prose arms. Each **Selected** and
**Labeled** bullet in §3 is one declaration unit for N2: **14 selected + 8
labeled = 22** declaration units. No row outside these 5 is read by cut 6, and
no prior-cut arm is counted as new selection.

## 5. N2 and acceptance obligations

The implementation plan's N2 task owns cut 6's declarations. It must declare
every §3 **Selected** and **Labeled** bullet, and only those 22 units, as data
with:

- its frozen row id (or `labeled:` name and specification citation) and
  assertion;
- the exact source mutation, against real module text;
- every exact test or acceptance node that must fail under that mutation; and
- a verdict from the standing harness for `vacuous`, `stale`, `mixed`,
  `uncollected`, and class-node collapse.

The unsabotaged baseline must pass. A selected durable arm runs through the
cut-6 acceptance runner on the certified tuple; errors on that tuple are
errors, never skips. Portable arms remain in the portable suite. The cut-6
runner may invoke cut 5 as a prefix, but neither
`python/tools/cut5_acceptance.py` nor cut 5's meaning is edited.

The three surfaces are `python/tests/n2_arms_cut6.py`,
`python/tests/acceptance/test_n2_cut6.py`, and
`python/tools/cut6_acceptance.py`.

N2 is prospective at freeze: the cut fixes the declaration inventory and
claims no declaration, sabotage, or test exists.

## 6. The second reader

The independent reader receives only the frozen rows quoted in §3, the
world-registry specification, and §2's boundary; they are not asked to
preserve this draft's rationale. The review attacks in the historically common
direction, toward overstated coverage.

The reader must:

1. check every selected clause and its exact source mutation against §2;
2. demote any clause that reaches the epoch build, receipts, coverage
   declarations, the audit, the log reader, the fork constructor, world
   resolution, or the `nodes` reserved-path contract;
3. check that W13's recorded narrowings (remote URL, project name, world
   address, coverage declarations) narrow rather than silently claim, and
   that no clause substitutes local presence for world resolution;
4. judge the two flagged selections: X4's raw-deletion undetectability
   negative — the specification's §8.1 wording ("declared, not selected as
   detected") admits both the cut-5 S3 precedent of selecting an
   undetectability assertion and a prose-only declaration — and the labeled
   `duplicate-carrier` arm, which specification §5.4 makes normative but
   §8.1's bullet list does not name; and
5. rederive §4's row accounting and the 22-unit declaration inventory
   independently.

### 6.1 Run and dispositions

The independent reading ran on 2026-08-20 with only §3's quoted frozen rows,
the world-registry specification, and §2's boundary declaration. It required
no demotions and rederived the accounting independently at **2 full + 2 part
+ 1 deferred = 5** rows and **14 selected + 8 labeled = 22** declaration
units, agreeing with §4. It found five overstatements of record rather than
of coverage, all closed before freeze:

1. **X6 spec-added clause:** the differing-post-terminal-act refusal is
   `StatusTerminal`, spec-added behavior that does not "return the corpus to
   live," and it appeared both inside X6's first selected bullet and as a
   labeled unit. **Disposition:** removed from the frozen selection; declared
   exactly once, as the status idempotency labeled unit. X6 remains full — no
   frozen arm was removed.
2. **X5 replica exception discharged by argument:** the frozen exception
   clause was dissolved by prose rather than run or recorded. **Disposition:**
   the selected mutation is parameterized to also admit `replica-of` naming
   an already-admitted id and assert identical refusal, and both narrowings —
   the exception by interpretation (its runnable content being X6's replica
   arm) and the unconditional refusal by the exact-retry exception — are now
   recorded in the bullet.
3. **§3.3 provenance claim:** the preamble cited specification §8 for all
   eight labeled declarations; the `duplicate-carrier` arm is named only by
   the normative §5.4 and §7. **Disposition:** citation corrected; the arm's
   selection judged sound rather than scope expansion.
4. **Unstated `nodes` §11.1 prerequisite:** five W13 units are unrunnable
   before the `nodes` public projection lands, and only the specification
   recorded the ordering. **Disposition:** carried as limitation 4 with the
   choreography's ordering.
5. **X5 narrowing unflagged:** the frozen unconditional refusal was silently
   restricted to differing content. **Disposition:** folded into item 2's
   re-word.

Both flagged selections were judged sound: X4's raw-deletion negative as a
runnable undetectability assertion (claiming no detection, on cut 5's S3
precedent — with the note that its N2 sabotage must be checked against
vacuous passing at declaration time), and the labeled `duplicate-carrier`
arm with its citation corrected. The reading completed before banking; at
freeze, implementation remains prospective.

## 7. Limitations

1. **Local is not world.** Presence, uniqueness, and every identity claim stop
   at the configured roots of one installation. No arm resolves across worlds
   or certifies coverage.
2. **The registry is chained but unanchored.** Committed registration-entry
   evidence shows a write was logged; nothing here refutes truncation, record
   deletion, or chain removal. X4's negative asserts exactly that bound.
3. **Genesis is unread.** The mirror is the only readable `world_id`; genesis
   and mirror agreement waits on the log design's chain reader.
4. **Five W13 units wait on the `nodes` §11.1 projection.** Every
   corpus-state-identity arm requires `nodes`' public §11.1 projection API,
   confirmed absent from that repository's public surface as of 2026-08-20.
   The specification's choreography (§9 step 6) orders that release before
   the Science slice, so the arms are runnable at discharge time; if that
   ordering slips, these units error rather than run, with this limitation as
   the recorded reason.
5. **No fork exists.** `fork-of` admission is exercised against
   fixture-authored manifests; no supported operation constructs a fork.
6. **In-process serialization only.** The world lock serializes cooperating
   writers in one process; cross-process single-writer deployment remains an
   obligation, not a guarantee.
7. **Discharge is bounded.** The 22 declaration units are what cut 6 can
   discharge; deferred clauses and prior-cut evidence are not relabelled as
   cut-6 results.
8. **Arm boundaries remain a reading.** The frozen cells are prose. That is
   why the independent reading is a precondition of freeze and why any
   uncertainty is classified toward part or deferral.
