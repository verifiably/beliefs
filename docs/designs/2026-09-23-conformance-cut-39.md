# Conformance cut 39 — publication records

**Status:** discharged 2026-09-23 on the certified volume; results: ../plans/2026-09-23-conformance-cut-39-results.md
**Design:** `../superpowers/specs/2026-09-22-publication-records-design.md`, approved 2026-09-22 at `cb19908` after two user reviews; implementation not yet started.
**Plan:** `../superpowers/plans/2026-09-22-publication-records.md`.
**Numbered after** cut 38 under roadmap concurrency rule 1. No other worktree or branch held a cut numbered 39 or above at freeze; cut 38 is the highest discharged runner.

## 1. What this cut is

The layer design specifies `publish` to the step, and the step list leans on
records and evidence the kernel does not have: no shipped coordination
contract to amend, no evidence for the intent-position rule (the
coordination design's §11.6 withdrew cut 14's constructed-prefix arm and
handed the evidence shape to `publish`), no record shape for a marker or a
binding, no deterministic identity, and no `publish` operation kind or act
family. This cut reads the slice that supplies them.

The coordination contract ships as `v1` (the former test fixture, same
content identity) and `v2`, whose lineage succeeds v1 and which adds the two
kinds `publication` and `publication-binding` and the `composite`/`composes`
query amendment. Both kinds carry deterministic records — byte-functions of
the publish intent and named arguments, identity by the factory only, the
ordinary family doors refusing both — under the content rule of spec §3. The
`publish` operation kind opens only through its domain intent,
`science.publish-intent.v1`, which carries the pinned view, the destination,
the binding and marker tips, and one anchor per mounted root other than the
written one; `publish` is an act family admitted only through the closed
kernel requirement. The intent-position judgment decides presence at a
position from the chain's inventory at each root's bound: committed
registrations only, every inventoried file present, content-matched and
well-formed, removals and rewrites `history-violated`, and files the chain
does not account for classified by a chain re-read under the engine's
write-ahead order. Two internal doors — the step-0 intent and the step-8
binding commit — write the source root, with no public route.

W17 closes, its intent-position arm judged over the chain's inventory, and
Y1–Y4 open and close. The cut is **off the path**: the success criterion
publishes nothing.

## 2. The boundary

The surfaces on which a sabotage may land are:

- `python/src/beliefs/contracts/coordination/v1/CONTRACT.yaml` (new),
  `python/src/beliefs/contracts/coordination/v2/CONTRACT.yaml` (new),
  `profile.py`, `coordination.py`, `permit.py`, `corpus.py`, `errors.py`,
  `report.py`, `stored.py`, `boundary.py`, `intents/shapes.py`,
  `intents/reduce.py`, `intents/publish.py` (new), `publication.py` (new),
  `publication_doors.py` (new), `root.py` (the moment seam),
  `world/epoch.py` (the capture's `stored.WORLD_KINDS` membership test,
  Y1-b's site);
- the test modules `python/tests/coordination_fixtures.py`,
  `test_coordination_contract.py`, `test_permit.py`,
  `test_coordination_write.py`, the act-report and intent-shape unit
  modules, `test_publish_intent.py`, `test_publication.py`,
  `test_standing_at.py`, `test_publication_doors.py`,
  `test_permit_boundary.py`, `test_permit_entry_points.py`,
  `test_publication_engine_order.py`, and
  `python/tests/acceptance/test_n2_cut17.py` (cut 17's live E4c re-targeted,
  its frozen `after` kept);
- `python/tests/acceptance/test_publication_records_acceptance.py`,
  `python/tests/n2_arms_cut39.py`,
  `python/tests/acceptance/n2_arms_cut39.py`,
  `python/tests/acceptance/test_n2_cut39.py`,
  `python/tools/cut39_acceptance.py`,
  `python/tests/test_recent_cut_acceptance.py`;
- this cut, the Y table's owner (`2026-09-22-publication-design.md`), the
  ledger, roadmap, guide, README and `python/tests/test_designs_corpus.py`.

Frozen declarations and cut bodies through cut 38 remain byte-exact.

## 3. Selection

Thirteen declaration units are selected and single-homed here, against five
rows. The quoted row text is byte-exact from
`2026-08-02-world-addressing-design.md` (W17) and
`2026-09-22-publication-design.md` (Y1–Y4) at freeze.

```markdown
| **W17** | A coordination address has one standing tip, or resolution refuses naming every tip (added 2026-08-31, coordination-and-view-kinds design) | **Genesis and immutability:** mint a coordination record's first revision and assert it names zero predecessors; edit it and assert a **new whole revision** superseding the first, with the predecessor set stored as **adapter-authored** `supersedes` relations — an author-written one refuses. Assert `add`, `revise`, `supersede` and `retract` all **refuse coordination kinds** — `note` included, whose unscoped predecessor-era use is retired by succession banked in cut 14 (its §9.2, cut 9's citation mechanism: the entire cut-5 surface stays byte-identical and is cited rather than run, its discharge standing as its frozen results record) — that `import_bundle` **refuses a bundle carrying a coordination kind, naming the member** (an imported revision would bypass every family judgment), and that the family door refuses world kinds — no other door, in any direction; assert the **pre-plan already-minted guard** holds at the new door, keyed on the per-revision stored identity, so a replayed genesis refuses rather than silently replacing. **The general rule:** under the written root's lock, supersede a predecessor and then attempt a revision naming it; assert `PredecessorNotStanding` judged **at commit** through the coordination resolver over its explicit corpus set. **Continuity before standing:** attempt a revision whose named predecessor is a standing tip of **another kind**, and one whose named predecessor is a standing tip of **another address**; assert both raise `PredecessorMismatch` — supersession never retargets what or where a record is, even across two standing tips. **The sibling state:** mint sibling successors of one tip in **two corpora**, resolve over a set containing both, and assert `Refused(divergent-view)` **naming every tip** — then reverse the corpus-set order and assert the identical refusal, pinning that no recency, arrival, or iteration order chooses. **Repair:** mint one revision superseding **all** named tips — the multi-predecessor arity's one job — and assert the address resolves again, with every sibling retained immutable and superseded. **The intent-position rule:** judge admission as a **pure function of a constructed chain prefix** ending at an operation intent: a predecessor already superseded at that position refuses; a predecessor superseded **between** intent and commit admits, and the result is **two standing tips** — the sibling state lawfully reached, repaired the same way. Its operational instance (`publish`'s `publication-binding`) is sub-project 5's cut. **Negative — zero tips is corruption:** raw-write a `supersedes` cycle and assert an **audit finding naming the cycle**, that resolution reports no tip, and that **no repair is offered** — no sanctioned door can produce the state. **Negative — a record that cannot state its address claims none:** raw-write a coordination node failing the dedicated `coordination_facet_malformed` validator (the one function the mint door, the audit and the resolver share); assert the audit emits a **malformed finding naming it**, that the resolver **excludes** it from tip computation so the address still resolves to its standing tip, and that nothing repairs or deletes it — vandalism cannot flip a tip, and exclusion is not repair. **Negative — a subordinate needs its project:** attempt a `(project identity, local id)` mint under a project identity with no resolvable record, and under one whose record is divergent; assert both refuse, the second naming the project's tips |
| **Y1** | version 2 declares `publication` and `publication-binding`; a version-1 pin authorizes neither; every ordinary door (`add`, `import_bundle`, `mint_coordination`, `revise_coordination`) refuses both; neither enters a world-index map or moves a `belief_input_digest` |
| **Y2** | both records are byte-functions of the intent and the named arguments; `marker_consistent` refuses a marker whose uid, address or id disagrees with its own `event_token`, view and destination |
| **Y3** | the publish intent decodes by its domain and qualifies only by a `publish` report with its token; a malformed payload under the domain, and a bare domainless `publish` triple, are audit findings; every other kind's intent is byte-unchanged |
| **Y4** | step 8 is all-or-nothing: a binding revision never exists without its success report, a refusal writes its report alone, and every `PositionRefused` reason refuses with no binding; a remotely revealed attempt refused for any reason is an orphan in the next intent's `marker_tips`, retired once a shared publish carrying it closes |
```

The unit table is spec §11.2's, the assertion column verbatim:

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

W17-p-e also holds a `rewritten` case (the spec's §16 planning note, user
review of the plan): a file at the address that no registration created,
then rewritten through the engine's `ReplaceOp` — a committed registration
whose own `initial` is already a file — refuses `history-violated`, never a
binding over it. The case is declared because `REPLACE_UNREGISTERED` is
`accepted` (§5).

### 3.2 Rows not read

W17's ordinary-family arms were closed by cut 14 and are not re-read; the
frozen cut-14 text's 'pure function of a constructed chain prefix' is
superseded by citation (coordination design §11.6 and this cut's W17-p
units), not edited.

## 4. Accounting

Task 0's two engine probes (§5) selected `REPLACE_UNREGISTERED = accepted`
and `ROLLBACK_MEANS = patched create effect`, which is the first row of the
plan's accounting table: **14 arms, 13 declaration units**, five rows; W17
closes and Y1–Y4 close; recent-cut row `(14, 13, 5)`; Task 7 passes 16;
188 of 220 → 193 of 220.

## 5. N2 and acceptance obligations

| arm | module | sabotage | check |
|---|---|---|---|
| W17-p-a | `publication_doors.py` | the guard trusts the intent's `binding_tips` instead of recomputing | W17-p-a |
| W17-p-b | `publication_doors.py` | the guard bounds the written root at its current tip, so the post-intent supersession refuses | W17-p-b |
| W17-p-c | `coordination.py` | the other roots' bound ignores the anchor and reads their current heads | W17-p-c |
| W17-p-d | `publication_doors.py` | the anchors ordered by mount path instead of `corpus_id` | W17-p-d |
| W17-p-e | `coordination.py` | the present set taken from the resolver's live read instead of the chain's inventory | W17-p-e |
| W17-p-e2 | `coordination.py` | `_creates` reduced to "any file post-state": a rewrite counts as a creation again, so the `rewritten` case admits the rewritten file as present instead of refusing `history-violated` | W17-p-e |
| W17-p-f | `coordination.py` | rolled-back registrations counted in the inventory's replay | W17-p-f |
| Y1-a | `corpus.py` | `revise_coordination`'s `KindNotMintedHere` check removed | Y1-a |
| Y1-b | `world/epoch.py` | the coordination exclusion dropped for `publication-binding` | Y1-b |
| Y2-a | `publication_doors.py` | the factory reads the clock for `at` | Y2-a |
| Y3-a | `intents/shapes.py` | the domain dispatch removed from `decode_intent` | Y3-a |
| Y4-a | `publication_doors.py` | the fallback plan written beside the success plan instead of in its place | Y4-a |
| Y4-b | `publication_doors.py` | the fold counts only `predecessor-not-standing` refusals as orphans | Y4-b |
| Y4-c | `publication_doors.py` | the fold skipping a publish intent whose report file is missing | Y4-c |

That makes **14 arms over 13 units** (W17-p-e homes two, W17-p-e and
W17-p-e2; every other unit one). Both directions are required: the check
passes on the real tree and fails under sabotage.

Task 0's probes (`python/tests/test_publication_engine_order.py`, on the
certified volume):

- the engine appends a registration before its create effect runs — the
  write-ahead order §6's re-read classification relies on;
- `ROLLBACK_MEANS = "patched create effect"`: patching the engine's
  create-file effect to raise after registration leaves the registration and
  a `committed=False` settlement in the chain and no file, so W17-p-f is
  declared;
- `RETRY_AFTER_ROLLBACK = "same intent"`: after a rolled-back fulfilling
  execution through `execute_fulfilling_guarded`, a retry under the same
  intent is admitted and commits, leaving two fulfilling registrations, the
  first rolled back and the second committed;
- `REPLACE_UNREGISTERED = "accepted"`: the engine commits a `ReplaceOp` over
  a file its chain never registered, as a registration whose own `initial`
  is already a file, so W17-p-e's `rewritten` case and arm W17-p-e2 are
  declared;
- the read-only detached inspector reads a live registered root well-formed,
  with the same entries as the registered inspector.

The runner uses `PREFIX_RUNNERS = ("cut38_acceptance.py",)` and carries
`PHASE_MODULES = ("test_publication_records_acceptance.py", "test_n2_cut39.py")`.

## 6. Second reader

Check that W17-p-a's second writer commits its supersession between the
step-0 tip read and `append_intent` (a port wrapper, not a thread) and that
the refusal comes from the guard's recomputation; that W17-p-c's anchor is
the one the intent carries, read back from the chain; that W17-p-e's
refusals are raised by the inventory, not by the resolver's live read; that
Y2-a's clock advances on every read; that Y4-a counts
`execute_fulfilling_guarded` calls on a wrapper over the durable port.

## 7. Limitations

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
   spec §6), rather than trusting files no registration covers.
6. **The judgment reads every inventoried revision's bytes** at the address
   in every mounted root, and every publish report for the
   `(view, destination)`; it is exact and not cheap.
