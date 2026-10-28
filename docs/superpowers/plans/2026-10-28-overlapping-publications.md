# Overlapping publications implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Tasks 2 to 6 share the world read view, the capture types and one conformance declaration, so inline execution is workable; a fresh reviewer checks the finished branch before integration either way.

**Goal:** Let a world hold one address in several live corpora when the copies have equal content, read it once everywhere, decide acceptance and attribution over the holder set, and fold correction standing once, while differing content, uid corruption and ambiguous provenance still refuse.

**Architecture:** The address map becomes multi-holder keyed by a content identity the kernel already computes; every world read labels a record by its least present holder and reads the holder set wherever the answer depends on it. Correction standing moves into a successor `retraction-enumeration` rule over a versioned rule input, with v1 untouched. Publish attributes a multi-holder record by own-holder, agreement, then the earliest origin in the held supersession order.

**Tech Stack:** Python 3.11+, pytest, the existing durable fixtures (two worlds, publish → adopt), the rules store, N2 and the acceptance runner. No dependency, permit, contract-release, world-config or TypeScript change.

**Spec:** `docs/superpowers/specs/2026-10-28-overlapping-publications-design.md`, accepted at `e14315c` (revision 10; the acceptance stamp is `5f28d5a`). Read the spec first; this plan cites it by section and repeats no ruling it already makes.

## Global Constraints

- Reuse `.worktrees/918fd2-overlapping-publications`, branch `design/918fd2-overlapping-publications`. The worktree is hydrated (`just setup` ran at creation); the full `just test` baseline has **not** run yet and is Task 1's first step. Show the user paths prefixed with this worktree directory. Do not touch main's existing `python/uv.lock` edit.
- **`root.py` is the one `atoms` importer** (`test_capability_boundary.py`, `TestTheCompositionRootIsTheOneAtomsImporter`). A classification over engine cause types, a predicate over engine exceptions, or any other engine-typed behaviour lives in `root.py` and reaches its boundary through a seam callable (cut 35's `StoreActSeam.store_refusal`, `b065711`), never as an import in the boundary module. Every new caller of a write primitive joins `WRITE_ENTRY_POINTS` in `test_permit_boundary.py` and gains a `Case` in `test_permit_entry_points.py`'s `CASES`; the inventory is closed in both directions.
- **Every discharged cut adds its row to `test_recent_cut_acceptance.py`**: the runner import, its `(runner, cut, accounting)` parametrization entry with the declared-arm, declaration-unit and guarantee-row counts, and the cut's guarantee-rows-exercised line. Cuts 33, 34 and 35 landed theirs at `f4c2cef`, `c77b2aa` and after cut 35's final review; the plan's runner task owns the row.
- Task 7 owns the proposed `(cut48, 48, (32, 32, 5))` row. Recheck branches and worktrees before Task 1 freezes cut 48; if occupied, amend this plan and every dependent name before freezing. Never silently reuse a number.
- Content identity is `v1.digest("science.node-content.v1", <nodes canonical projection>)`, the member `corpus_state_identity` computes, exposed as `beliefs.world.registry.content_identity(node)` and computed nowhere else (spec §4.1). Equality is exact.
- The derivation order is uid-corruption, then per-address content grouping, then deprecated keys (spec §4.2), and `_derived_members` derives the address map before running any rule (spec §4.5).
- `address-map.yaml` entries are closed on `{address, content, holders, uid}`; the legacy `{address, corpus_id, uid}` is admitted as a second closed shape, never mixed (spec §4.3). Only the new shape is written.
- The capture stays per corpus; `CapturedRecord.projection()` and the v1 rule input are byte-identical to today's; v1 rule documents, fixtures and identities do not move (spec §4.5). `retraction_v2` takes `science.rule-input.v2`; `rule.yaml` admits `{symbol}` and `{symbol, input: science.rule-input.v2}` only; the fixture-schema check runs at install and at resolution, never in `_locked_stored_rule` or removal.
- Every world answer that depends on which holder (acceptance, attribution, audit filing, absence naming, `contributing`) reads the holder set; `corpus_of` is a label, the least present holder (spec §5.2, §5.4). Nothing picks content by corpus order.
- Attribution: own holder wins; else every replica claim must agree; else the unique claim every other claimed marker supersedes, read from captured markers only when that rule is reached; else `attribution-ambiguous` carrying the claims, nothing written (spec §7). v2 names only holders of carried records.
- Freeze the cut document before product edits. Preserve prior frozen documents, canonical declarations and their tests' assertions; live mutation retargets go in the owning guard with a recorded reason and a proved kill; obligation changes (`TestTheSplit` and the two split acceptance tests) are rewritten with a ledger disposition, not retargeted.
- `just test-one` is the test front door; `just test-fast` precedes implementation commits; portable and acceptance modules run separately. Durable fixtures and the successor runner use the certified volume through `checkout.MAIN_CHECKOUT`. Report exact capability refusal; never turn it into a skip. No live corpus is a fixture.
- New test subprocesses receive an environment built key by key (temporary `HOME`, required `PATH`, explicit variables, fake credentials); git reads use `GIT_CONFIG_NOSYSTEM=1` and a temporary `GIT_CONFIG_GLOBAL`.
- Record lifecycle, review and retained-item evidence with `tasks`. No push or live-world mutation is authorized. Science's side (spec §8) is a filed science task, never an edit from this worktree.

## Review Focus

1. A legacy epoch (singular entries) opened after the cut beside a rebuilt one: Task 2 pins that both open, `resolve_address` answers both, and a document mixing shapes refuses.
2. Three holders where two agree and one differs after the epoch: Task 3 pins `ResolutionRefused` naming all three, never a served copy.
3. A dataset's route identity equal to a retraction's address, retracted by route, in one corpus: Task 4 pins no edge in v2, in `retraction_standing` and in `gather`.
4. A recipient holding P1 and P7 with P3 retired: Task 5 pins `attribution-ambiguous` carrying both claims (the §10 item 3 state), and Task 6 pins that the chain-retention fixture (P3 kept) resolves to P1.
5. A policy that rejects a counter under one holder and accepts it under another, over a v1-bound epoch: Task 4 pins that the two recorded resolutions refuse explicitly in the filtered check, not by sort order.

## File map and declaration

All paths are repository-relative; user-facing paths add the worktree prefix.

| Files | Responsibility |
|---|---|
| `docs/designs/2026-10-28-conformance-cut-48.md` (new); W, G, Y, J tables; normative contract §6; slice 2 §4.1/§7.2/§8.3; mount-citations and belief-acceptance specs (dated notes); designs README, adoption ledger, roadmap, README; `python/tools/roadmap_status.py` | Freeze and later discharge the cut (Tasks 1, 7) |
| `python/src/beliefs/world/registry.py`, `world/derive.py`, `world/epoch.py` (`_captured_records`, `_check_addresses`), `world/read.py` (`_address_map`), `world/live.py` (`_address_map`) | Content identity, `AddressEntry`, the two epoch shapes (Task 2) |
| `python/src/beliefs/world/view.py`, `world/read.py` (`Location`, `resolve_address`), `world/live.py` (`_LiveCapture`), `world/selection.py`, `audit.py`, `corpus.py` (`_absence_of`, coreference endpoint) | Holder states and the served surface (Task 3) |
| `python/src/beliefs/world/rules.py`, `world/rules_v1/retraction_v2.py` (new) and fixtures, `world/derive.py` (`CapturedRetraction.arm`, `rule_input(version)`), `world/epoch.py` (`_BuildDraft.run`, `_derived_members`), `world/read.py` (`validate_receipt`, `_snapshot_standing`, `reported_receipt`), `corpus.py` (`snapshot_standing`), `evaluation.py` (`_check_filtered_world_standing`), `root.py` docstring | Correction standing: the v2 rule, the versioned input, the merged folds (Task 4) |
| `python/src/beliefs/evaluation.py` (gather's loops), `publish.py` (`_selected_attributions`), `corpus.py` (`MountCitations`), `errors.py` | Acceptance union, attribution over holders, J17 (Task 5) |
| `python/tests/acceptance/test_overlapping_publications_acceptance.py` (new) | The 1b fixture end to end on the certified tuple (Task 6) |
| `python/tests/n2_arms_cut48.py` (new), acceptance shim and `test_n2_cut48.py` (new), `python/tools/cut48_acceptance.py` (new), `test_recent_cut_acceptance.py`; retargets in `test_n2_cut23.py`, `n2_arms_cut28.py`/`test_n2_cut28.py`, `n2_arms_cut41.py`, `n2_arms_cut44.py`, `n2_arms_cut45.py`, `n2_arms_cut46.py`, `test_n2_cut7.py` | Mutation proof, historical pins, runner accounting (Task 7) |
| `docs/plans/2026-10-28-conformance-cut-48-results.md` (new) | Results, review dispositions and limits (Task 7) |

**32 units, 32 arms, 5 rows exercised**: W19, W20, G14 and Y19 newly closed, J17 reclosed under its amendment; W8b, J20, G10, G12, Y5 and Y17 are reclosed by retargets and carry no new unit. The exact check is `test_<unit lowercased, hyphen to underscore>_<suffix>` in the module the unit's task names. Parameter cases stay within one unit; durable tests add evidence, not units.

| Unit | Suffix / decisive behavior | Independent mutation responsibility |
|---|---|---|
| W19-a | `equal_content_reads_once`: two and three corpora map one entry with sorted holders, either capture order | Refuse every multi-claim address |
| W19-b | `differing_content_refuses`: shared uid with differing content, and distinct uids, refuse `duplicate-location` naming every claim | Group claims by uid instead of content |
| W19-c | `corruption_outranks`: one uid at two addresses refuses `uid-corruption` before any duplicate, both orders | Check addresses before uids |
| W19-d | `deprecated_key_entry`: one entry through two holders; a key colliding with a live or differing record refuses typed `ResolutionRefused`, both orders, same and cross corpus | Keep the first claimant of a deprecated key |
| W19-e | `epoch_shapes`: the new shape is written; the legacy shape reads as singleton holders with `content=None`; a mixed document refuses `EpochMalformed` | Read a legacy entry as the new shape |
| W19-f | `discovery_once`: a retraction held twice is discovered once | Collect discovery refs as a list |
| W19-g | `live_map_holders`: `evaluate_live_query` carries content and holders into the map; Z5-a/b/c behaviour unchanged | Drop content from the live capture |
| W20-a | `view_serves_once`: `get`, `resolve`, `inbound` (one edge per relation) and `Location.holders` over equal-content holders | Build inbound edges per holder |
| W20-b | `holders_disagree_refuses`: a captured copy that differs after the epoch refuses `ResolutionRefused` naming every holder, never `NotPresent` | Serve the least holder without comparing |
| W20-c | `absence_over_holders`: `NotPresent` only when every holder is absent; `Resolved` with one present; `_require_located` lists every absent holder; `Unresolved.corpus_id` is the least | Mark not-present when any holder is absent |
| W20-d | `owners_check_narrowed`: a map-established shared uid opens; an unmapped shared uid still refuses with the existing text | Drop the owners check for mapped uids too |
| W20-e | `damaged_holder_rule`: served when every captured copy equals the mapped `content`; refuses `CorpusDamaged` naming the damaged corpus for a legacy entry or a differing copy | Skip the damaged holder without the content comparison |
| W20-f | `resolve_address_holders`: per-holder uid rule, unreadable-holder skip against `content`, disagreement refuses, `holders=readable` | Resolve through the first carrier only |
| W20-g | `contributing_union`: `contributing` names every captured holder of a selected record; disagreeing pins refuse `pins-disagree` | Keep the last holder per record in `_denoted` |
| W20-h | `mapped_view_and_absence`: `_mapped_view` sees the record under each holder; `_absence_of` and the coreference endpoint name the least holder only when all are absent | Filter `_mapped_view` by `holder == corpus_id` |
| W20-i | `audit_files_per_holder`: a finding is filed under every captured holder; `_CapturedCitations._holder` reads the first readable holder and is unreadable only when none is | File under the canonical holder only |
| G14-a | `union_over_holders`: rejected under one holder, accepted under another: read once, counts, attributed to the accepting holder, rejected pair in `excluded` | Stop at the first holder's decision |
| G14-b | `rejected_everywhere_inert`: rejected under every holder: inert, every pair reported | Accept when any holder is undecided |
| G14-c | `predicate_per_holder`: asked once per captured holder per record, decisions cached per pair | Ask only the canonical holder |
| G14-d | `filtered_graphs`: R and C in *A*, R in *B*, policy rejects C: R upheld, fidelity passes with C's rejection reported; C accepted: R overturned; both hold R and C, C accepted through *B* only: R overturned | Fold the filtered graph per corpus |
| G14-e | `snapshot_merged_fold`: both hold snapshot-arm R and counter C, C accepted through *B* only: not retracted; one history chain `((C, upheld), (R, overturned))`; both holder orders | Union per-corpus `retracted` sets |
| G14-f | `merge_self_check`: through `validate_receipt` and `reported_receipt` directly, two copies of one uid with differing content, with differing addresses, and one id under two uids, both orders: `unresolvable` with the conflict's finding, never `retracted` | Collapse by uid without the classification |
| G14-g | `filtered_fidelity_one_comparison`: one comparison against gather's fold; two recorded resolutions for one ref refuse explicitly; the affected set is rejected retractions and what they counter | Keep the last recorded resolution per ref |
| G14-h | `v2_rule_binding`: `rule.yaml` shapes, identities, `input_version` dispatch at build, validation and fixture run; a v2 bundle with a fixture lacking `arm` refuses at install and, raw-written, at resolution; an intact nonconformant pair is removable | Hand a v2 rule the v1 input |
| G14-i | `v2_fold_world`: v2-bound build over R,C/R publishes one `(R, overturned)` either order, `validate_receipt` validates, `gather` agrees; v1-bound publishes both pairs; R,C,D/R,C says `upheld`; the moved counter is overturned; the colliding route adds no edge | Run the rules before the address map |
| Y19-a | `own_wins`: an own holder beside a carried copy yields no entry; the authenticity limit is unchanged | Prefer the carried claim over own |
| Y19-b | `carriers_agree`: two carriers with one triple forward it | Refuse any two carriers |
| Y19-c | `earliest_origin`: P1/P3; re-adopted own P2 beside them; a third party holding P2 and P3; sibling tips over P1; P7 → P3 → P1 read through P3's marker only when rule 3.3 is reached | Order holders' markers instead of claimed markers |
| Y19-d | `ambiguous_refuses`: unrelated origins, and a chain with its intermediate unheld, refuse `attribution-ambiguous` carrying the claims, nothing written | Pick the lowest claim on disagreement |
| Y19-e | `order_independent`: publish → adopt → republish with the recipient's roots and admissions reordered yields equal frozen tuples and `published_from.attributions`; retries use the frozen tuple | Sort claims by holder registration order |
| Y19-f | `v2_narrowing`: v2 names only holders of carried records; an own-made record needs no source | Name every replica holder under v2 |
| J17-c | `citation_equal_content`: two session corpora holding equal content resolve once with every mount's contract checked; differing content refuses naming every holder | Return the first holder's view without comparing |

Each arm must fail at its named assertion, not a collection, syntax or unrelated guard error; a check that drives a build or a publish wraps it so the failure lands in the named assertion. The v2 rule's own fold is normative in its fixtures and pinned by the equivalence test, never by a sabotage of rule bytes (a changed implementation is a different identity, which the store refuses to bind). Task 7 fixes the exact before/after anchors against the finished implementation without weakening these obligations.

### Task 1: Freeze conformance cut 48

**Files:** new cut document; `docs/designs/2026-08-02-world-addressing-design.md` (W8b note, W19, W20), `docs/designs/2026-08-02-epistemic-kernel-design.md` and `docs/designs/2026-08-04-formal-model-and-claim-calculus-design.md` (G10/G12 notes, G14, Y19 copy), `docs/designs/2026-09-22-publication-design.md` (Y5/Y17 notes, Y19), `docs/designs/2026-09-05-writer-session-design.md` (J17/J20 notes), `docs/designs/2026-08-03-normative-contract-design.md` §6 and `docs/designs/2026-08-20-world-index-slice-2-design.md` §4.1/§7.2/§8.3 (dated notes), `docs/superpowers/specs/2026-10-01-mount-citations-design.md` decision 4 and `2026-10-02-belief-acceptance-design.md` §5.1 (dated notes), `docs/designs/README.md`, the adoption ledger, the roadmap, `README.md`, `python/tools/roadmap_status.py`.

**Interfaces:** Consumes spec `e14315c` and this reviewed plan. Produces the frozen cut-48 obligations, the 32 unit names, four new rows and six amendments by citation; no product behaviour.

- [ ] At execution Setup, refresh the task claim (`tasks start beliefs-918fd2` in the worktree) and the trial arm, inspect worktree status and installed hooks, and run the full `just test` baseline before any code change, in the foreground with a timeout that covers it. Record the command, passed/failed/skipped counts and capability limits on the task.
- [ ] Inspect `git for-each-ref`, `git worktree list` and the cut documents in every worktree; confirm 48 is unused. Confirm W19, W20, G14 and Y19 are unused in their tables (W18, G13 and Y18 are the last used at the baseline).
- [ ] Write `docs/designs/2026-10-28-conformance-cut-48.md` in cut 47's seven-section form: what the cut is (spec §1 to §3 in one paragraph), the boundary (every file in the file map; `root.py` touched only for a docstring), the selection (this declaration table verbatim, the refusal orders of spec §4.2, §5.1, §7 and the two epoch shapes), the accounting (**32 arms, 32 units, 5 rows**: 4 newly closed, J17 reclosed; the recent-runner entry `(32, 32, 5)` and the line `guarantee rows exercised: 5 (4 newly closed: W19, W20, G14, Y19; J17 amendment reclosed)`), the N2 obligations with `PREFIX_RUNNERS = ("cut47_acceptance.py",)` and `PHASE_MODULES = ("test_overlapping_publications_acceptance.py", "test_n2_cut48.py")`, the second-reader list (spec Review Focus above plus §10's limitations), and the limitations (spec §10 items 1 to 8, the science task, and that no live corpus changes).
- [ ] Append W19 and W20 to the W table, G14 to the G table and its formal-model copy, and Y19 to the Y table and its copy, each row's obligation and decisive checks copied from spec §9. Add dated notes on W8b, J17, J20, G10, G12, Y5 and Y17 as spec §9 words them, on the normative contract §6 and slice 2 §4.1 (the v2 identity formula), slice 2 §7.2 (multi-holder map) and §8.3 (holder-set resolution), mount-citations decision 4 and belief-acceptance §5.1. Leave every frozen cut body untouched.
- [ ] In `roadmap_status.py` register the new rows and set `REOPENED` for W8b, J17, J20, G10, G12, Y5 and Y17 to `("conformance-cut-48 §3", 48)`. Run `cd python && uv run --frozen python tools/roadmap_status.py` and carry its totals into the ledger's `Current state`, the roadmap (reopen `world-read`; name the rule-3 shared surfaces), the designs README row and `README.md`. Do not claim discharge.
- [ ] Run `just test-one tests/test_designs_corpus.py tests/test_check_guide.py tests/test_world_rules.py`, then `just test-fast` and `tasks check`. Commit `docs(cut): freeze conformance cut 48 (overlapping publications)`; record the commit and the document's SHA-256 on the task.

### Task 2: Content identity and the multi-holder address map

**Files:** `python/src/beliefs/world/registry.py:758-779`, `world/derive.py:177-313,402-465`, `world/epoch.py:752-756,1170-1240`, `world/read.py:762-775`, `world/live.py:251-276`; tests `test_world_derive.py::TestAddressMap`, `test_world_epoch.py`, `test_world_read.py`, `test_live_selection.py`.

**Interfaces:** Produces `registry.content_identity(node: Node) -> str`; `derive.AddressEntry(uid: str, content: str | None, holders: tuple[str, ...])` (frozen; `holders` sorted and non-empty, refused otherwise); `derive.CapturedRecord.content: str` (required keyword, after the existing fields; `projection()` unchanged); `derive.address_map(capture) -> Mapping[str, AddressEntry]`; `derive.address_map_projection(mapping) -> dict` writing `{address, content, holders, uid}` entries sorted by address; `read._address_map(published) -> Mapping[str, AddressEntry]` admitting both shapes; `epoch._check_addresses` admitting exactly the two closed key sets, never mixed. Consumes nothing from later tasks.

- [ ] Write W19-a/b/c/d/e/f in `test_world_derive.py` (extend `TestAddressMap`; the `record` and `corpus` helpers gain `content=`), with W19-e's epoch half in `test_world_epoch.py` (build, read back, a hand-written legacy document, a mixed document) and its reader half in `test_world_read.py`. Pin these assertions:

  ```python
  assert mapping["dataset:one"] == derive.AddressEntry("uid-dataset:one", DIGEST, ("corpus-a", "corpus-b"))
  assert caught.value.finding.code == "duplicate-location"            # differing content, shared uid
  assert caught.value.finding.code == "uid-corruption"                # before any duplicate
  assert isinstance(caught.value, ResolutionRefused) and "dataset:one" in str(caught.value)  # W19-d
  assert sorted(entry) == ["address", "content", "holders", "uid"]    # written shape
  assert read._address_map(legacy)["dataset:one"] == derive.AddressEntry("uid", None, ("corpus-a",))
  with pytest.raises(EpochMalformed): epoch._check_addresses(mixed)
  ```

  Replace `test_a_deprecated_entry_may_not_shadow_a_live_address`'s `ValueError` expectation with `ResolutionRefused` (beliefs-354eae's ruling), keeping the same-corpus fixture and adding the cross-corpus and reversed-order cases.
- [ ] Run `just test-one tests/test_world_derive.py tests/test_world_epoch.py tests/test_world_read.py`; require failures for the absent behaviour, not fixture errors.
- [ ] Extract `content_identity(node)` from `corpus_state_identity` and call it there. Add `content` to `CapturedRecord` and supply it in `epoch._captured_records` and `live._address_map`. Rewrite `derive.address_map` in spec §4.2's order and `address_map_projection` for the new shape; make `_check_addresses` and `read._address_map` admit both shapes. Keep every message the existing tests pin.
- [ ] Add W19-g to `test_live_selection.py`: the live map carries holders and content; the existing Z5 cases still pass. Run the four modules through `just test-one`; then every other module that constructs `CapturedRecord` or reads `address-map.yaml` (`grep -rn "CapturedRecord(\|address-map" python/tests`), fixing fixtures only.
- [ ] `just test-fast`, `tasks check`, commit `feat(world): multi-holder address map keyed by content identity`.

### Task 3: Holder states and the served world surface

**Files:** `python/src/beliefs/world/view.py` (whole module), `world/read.py:646-760`, `world/live.py:103-150`, `world/selection.py:184-256`, `audit.py:627-660,799,881`, `corpus.py:1443-1450,3060-3078`; tests `test_world_view.py`, `test_world_read.py`, `test_live_selection.py`, `test_world_selection.py` (or the module holding `evaluate_query` tests), `test_world_audit.py` (or the module holding `audit_world` tests), the cut 7 live checks in `acceptance/test_n2_cut7.py:472,478` and `test_world_read.py:135,139` that construct `Location` positionally.

**Interfaces:** Produces `read.Location(corpus_id: str, uid: str, holders: tuple[str, ...])` (required, sorted, non-empty); `WorldReadView.holders_of(ref) -> tuple[str, ...]`, `WorldReadView.captured() -> tuple[str, ...]`, `WorldReadView._mapped_holders() -> Iterator[tuple[tuple[str, ...], Node]]`; the same three on `live._LiveCapture`; `corpus_of` unchanged in signature (least captured holder, least recorded for `NotPresent`); `_mapped_records()` once per captured holder; `iter_stored()` once per record ordered by `(canonical holder, uid)`. Consumes Task 2's `AddressEntry`.

- [ ] Write W20-a/b/c/d/e/f/g/h/i, each in the module that tests the surface it names (W20-c and W20-g in the selection tests; W20-i in the audit tests; the rest in `test_world_view.py` and `test_world_read.py`), over a three-corpus fixture where one record is held in two corpora with equal content and a third copy can be made to differ or be damaged. Pin:

  ```python
  assert view.locate(ADDR) == Resolved(Location("corpus-a", UID, ("corpus-a", "corpus-b")), stamp)
  assert view.corpus_of(ADDR) == "corpus-a" and view.holders_of(ADDR) == ("corpus-a", "corpus-b")
  assert len(view.inbound(TARGET)) == 1
  with pytest.raises(ResolutionRefused) as caught: open_world_view(world, published)   # W20-b
  assert "corpus-a" in str(caught.value) and "corpus-b" in str(caught.value)
  assert type(view.locate(ADDR)) is NotPresent                                        # both absent
  assert refused.value.corpus_ids == ["corpus-a", "corpus-b"]                          # _require_located
  assert selection.contributing == ("corpus-a", "corpus-b")
  assert [c for c, _ in view._mapped_records() if _.uid == UID] == ["corpus-a", "corpus-b"]
  assert sum(1 for n in view.iter_stored() if n.uid == UID) == 1
  ```

  W20-d keeps `test_one_uid_under_two_corpora_refuses_at_open_durably`'s unmapped case and adds the mapped case that opens. W20-e covers served, legacy-refused and differing-refused, asserting `CorpusDamaged.corpus_id` is the damaged corpus. W20-f uses `resolve_address` with one unreadable carrier and the `content` match.
- [ ] Run the modules through `just test-one`; require failures at the new assertions.
- [ ] Implement spec §5.0 to §5.4 in `open_world_view` (holder classification; per-holder carrier check; holder agreement by `content_identity`; damaged-holder rule in `_refuse_damaged`; owners check keyed against the entry's `holders`; `held`, `_mapped_view`, `inbound` from the distinct-record enumeration), the served methods, `resolve_address`, `_LiveCapture`, `_denoted`'s `held`/`contributing`, `_classify`/`_require_located`, the audit loops and `_CapturedCitations._holder`, `_absence_of` and the coreference endpoint refusal. Update the positional `Location` constructions in tests.
- [ ] Run the touched modules, then `just test-one tests/acceptance/test_n2_cut23.py -k each_arm_targets` and the same for cuts 28, 41 and 7 to list the anchors Task 7 retargets (W10g, W8/W8b-a..d, Z5-a/b/c, cut 7's `Location`). Record them on the task.
- [ ] `just test-fast`, `tasks check`, commit `feat(world): serve multi-holder records once and read the holder set where it matters`.

### Task 4: Correction standing: the v2 rule, the versioned input and the merged folds

**Files:** `python/src/beliefs/world/rules.py:83-100,111-135,160-235,257-300,338-420,435-460`, `world/rules_v1/retraction_v2.py` (new) and `world/rules_v1/fixtures/retraction_v2.*.yaml` (new: `basic`, `differing-graphs`, `counter-chain`, `route-arm`, `snapshot-arm`, `colliding-route`, `deprecated-target`, `empty`), `world/derive.py:177-194,282-313,384-400`, `world/epoch.py:956-1003,1170-1240,1414-1452`, `world/read.py:222-345,346-411`, `corpus.py:1206-1300`, `evaluation.py:272-320`, `root.py` (the "four v1" docstring), `python/tests/test_world_build.py:73,222`, `test_world_receipts.py:105`, `acceptance/test_n2_cut7.py:217-250`; tests `test_world_rules.py`, `test_world_derive.py`, `test_world_standing.py`, `test_standing_read.py`, `test_snapshot_retraction.py`, `test_acceptance.py`.

**Interfaces:** Produces `rules.RuleBundle(symbol, fixtures, implementation, input_version: str | None = None)`; `rules.RULE_INPUT_V2 = "science.rule-input.v2"`; `rules.rule_document_bytes(symbol, input_version)` and `rules.parse_rule_document(content) -> tuple[str, str | None]`; `rules.rule_identity(symbol, fixtures, input_version)` (two-member list for `None`, three-member for v2); `rules._HeldRule.input_version`; `rules.RuleNonconformant` raised by `_HeldRule.invoke` around a rule raise, naming the pair; `derive.CapturedRetraction(target, resolution, arm: str)`; `derive.Capture.rule_input(version: str | None = None) -> dict`; `epoch._BuildDraft.run(kind)` handing `rule_input(held.input_version)`; `read._snapshot_standing(...) -> tuple[ReceiptOutcome, Finding | None] | None`; `corpus.snapshot_standing` over a merged view with its self-check; test helpers `install_bindings(world, *, retraction: str = "v2")`, `hold_shipped(world, *, retraction: str = "v2")`, `shipped_bindings(world, *, retraction: str = "v2")` and `SYMBOL_KINDS` keyed per version. Consumes Tasks 2 and 3.

- [ ] Write G14-d/e/f/g/h/i. G14-h in `test_world_rules.py` (documents, identities, dispatch, the install refusal `RuleNonconformant` for a fixture lacking `arm`, resolution refusal for the same raw-written, and `remove_rule_binding` succeeding on an intact nonconformant pair); G14-i and G14-d in `test_world_standing.py` (rewrite `TestTheSplit::test_a_counter_retraction_moved_away_refuses_the_disagreement` into the v2 obligation and keep a v1-bound twin asserting today's refusal); G14-e and G14-f in `test_snapshot_retraction.py` and `test_standing_read.py`; G14-g in `test_acceptance.py` beside the G12 cases. Add the equivalence test `test_v2_fold_equals_retraction_standing_over_every_fixture` in `test_world_derive.py`. Pin:

  ```python
  assert parse_rule_document(b"symbol: enumerate_retractions\n") == ("enumerate_retractions", None)
  assert rule_identity("s", fixtures, None) == v1.digest(RULE_DOMAIN, ["s", fixture_set_identity(fixtures)])
  assert dict(enumeration.found)[first.id] == "overturned"          # v2-bound split
  assert dict(v1_enumeration.found).get(first.id) is None             # two pairs under v1: use list, assert both present
  assert outcome.outcome == "unresolvable" and finding.code == "duplicate-location"   # G14-f, both orders
  assert standing.history[SUBJECT] == (("retraction:c", "upheld"), ("retraction:r", "overturned"))
  with pytest.raises(RetractionResolutionDisagreement): ...           # two recorded resolutions, filtered path
  ```
- [ ] Run the modules through `just test-one`; require failures at the new assertions. Confirm `test_every_shipped_fixture_carries_a_captured_view` and `test_four_bundles_ship_with_fixtures_and_distinct_identities` fail only on counts and the v2 key set.
- [ ] Implement the rules-store half: `input_version` on `RuleBundle` (last, default `None`), the two document shapes, the identity formula, `_HeldRule.input_version`, the fixture-schema check in `install_rule_binding` (before identities) and `_locked_resolve_rule_binding` (beside `_run_fixtures`), the raise wrap in `invoke`, `_SHIPPED` with `("retraction_v2", "enumerate_retractions_v2")`, the five-bundle docstrings and count pins. `_locked_stored_rule` and `remove_rule_binding` untouched.
- [ ] Implement the capture half: `CapturedRetraction.arm` from the validated facet, `rule_input(version)` adding `arm` to each retraction member for v2 only, `_BuildDraft.run` and `validate_receipt` dispatching by the held version, `_derived_members` deriving the address map first.
- [ ] Write `retraction_v2.py` (pure; the arm-aware edge rule and acyclic postorder reimplemented; a deterministic plain raise for an id under two uids and for a cycle) and its eight fixtures, each showing per-corpus resolutions that disagree where the case has them and the one world resolution emitted; both input orders for `differing-graphs`.
- [ ] Implement the fold half: `snapshot_standing` over a merged view with spec §4.5's self-check (between holders only; the three refusals; `Finding("error", "deprecated-key-collision", …)` for the third), record-level acceptance before the fold, one history chain; `read._snapshot_standing` returning outcome and finding; `validate_receipt` reporting `unresolvable`; `reported_receipt` returning the finding; `_check_filtered_world_standing` as one comparison with the explicit two-resolutions refusal.
- [ ] Give the three binding helpers an explicit retraction version (default v2) and make `SYMBOL_KINDS` per version; the v1-bound twin tests use `retraction="v1"`.
- [ ] Run every touched module through `just test-one`, then `just test-one tests/acceptance/test_n2_cut45.py -k each_arm_targets` and cuts 34 and 7 to list the anchors Task 7 retargets. `just test-fast`, `tasks check`, commit `feat(world): fold correction standing once in a versioned retraction-enumeration rule`.

### Task 5: Acceptance over holders, attribution over holders, J17

**Files:** `python/src/beliefs/evaluation.py:392-470,468-560`, `publish.py:251-316`, `corpus.py:719-792`, `errors.py` (no new class; `attribution-ambiguous` is a `PublicationRefused` reason); tests `test_acceptance.py`, `test_publication_attribution.py`, `test_owned_replica_publication.py` (fixtures only), `test_mount_citations.py`.

**Interfaces:** `gather` iterates `_mapped_holders()` and asks `counts(h, address)` for every captured holder; `node_corpus` lists accepting holders; `_selected_attributions(read, registry, selected, pin, *, own_corpora)` keeps its signature and implements spec §7's four rules, reading non-selected undeclared `ReplicaOf` holders' markers through `read.captured()` only when rule 3.3 is reached; `PublicationRefused("attribution-ambiguous", refs=(address,), corpus_ids=holders, field=<claims rendered as "corpus:marker" joined by ",">)`; `MountCitations._one` compares `content_identity` across holders. Consumes Tasks 2 to 4.

- [ ] Write G14-a/b/c in `test_acceptance.py` over the multi-holder world fixture (extend the existing acceptance world helpers with a second holder of one assessment, one verification and one retraction); Y19-a/b/c/d/e/f in `test_publication_attribution.py` using `capture_fixture`/`wrapper_fixture`/`pin`/`Prepared` with captures that hold one address in several corpora and markers whose `supersedes_markers` form the P1/P3, P2/P3, sibling and P7→P3→P1 shapes; J17-c in `test_mount_citations.py`. Pin:

  ```python
  assert inputs.node_corpus[identity] == ("corpus-b",)                 # accepting holder only
  assert ("corpus-a", ADDR) in context.excluded and identity in ids     # G14-a
  assert attributions == ()                                             # Y19-a, own wins
  assert attributions == ((ADDR, P1_CORPUS, P1_MARKER),)                # Y19-c, every shape
  assert (caught.value.reason, caught.value.refs, caught.value.corpus_ids) == ("attribution-ambiguous", (ADDR,), HOLDERS)
  assert first.attributions == reordered.attributions                   # Y19-e
  assert caught.value.reason == "attribution-contract-unpinned" and caught.value.corpus_ids == (CARRIED_HOLDER,)  # Y19-f
  assert citations.holder(ADDR) is own_view                             # J17-c equal; differing → AddressMapConflict naming both
  ```
- [ ] Run the three modules through `just test-one`; require failures at the new assertions.
- [ ] Implement gather's per-record loops (assessments, runs, observed datasets, verifications, retractions) over `_mapped_holders()`, the attribution tuple, and the retraction acceptance union; `_selected_attributions`' four rules with lazy marker reading and the own-holder, agreement and least-element steps; `MountCitations._one`'s content comparison with `_refuse_contract_mismatch` over every read-mount holder.
- [ ] Run the modules, then `just test-one tests/acceptance/test_n2_cut44.py -k each_arm_targets` and cuts 45 and 46 to list the anchors Task 7 retargets (J17a/b, G10-d/f, G12-a/b/c/e, Y17 arms). `just test-fast`, `tasks check`, commit `feat(belief,publish): decide acceptance and attribution over the holder set`.

### Task 6: The 1b fixture on the certified tuple

**Files:** `python/tests/acceptance/test_overlapping_publications_acceptance.py` (new), reusing `test_publication_attribution_acceptance.py`'s `source`, `world_at`, `build`, `context_at`, `saved_marker`, `resume` and `unavailable` helpers and `test_owned_replica_publication_acceptance.py`'s replica arrival fixture.

**Interfaces:** Durable evidence only; adds no unit. Produces the fixture later science work can copy: two worlds *A* and *B*, `A` publishes P1, `B` adopts and publishes P2 carrying *A*'s records, `A` adopts P2 (the overlap), builds an epoch, publishes P3, `B` adopts P3 keeping P1.

- [ ] Write six functions: `test_overlap_epoch_reads_once` (after *A* adopts P2: build succeeds, the shared addresses map two holders, `evaluate_query`, `evaluate_live_query` and `resolve_address` serve them once, `gather` under `accept = [B]` counts *A*'s assessment through the write root and lists the P2 copy as excluded); `test_republish_attributes_own_and_earliest_origin` (P3 carries no entry for *A*'s records; *B*'s republish after adopting P3 with P1 kept attributes to P1; the same with roots reordered gives equal tuples); `test_chain_gap_refuses_and_retention_resolves` (P7 with P3 retired refuses `attribution-ambiguous` carrying both claims; with P3 kept resolves to P1); `test_differing_copy_refuses_and_consolidate_is_the_exit` (revise *A*'s copy in place: build refuses `duplicate-location`; the retained epoch's view refuses `ResolutionRefused`); `test_counter_after_publishing_folds_once` (*A* counters R after P1: v2-bound build publishes one pair, receipt validates, `gather` agrees); `test_receipt_path_merge_refusals` (G14-f's three cases through `reported_receipt` directly). Assert exact refusal reasons, no operations-root writes on refusal, and byte-identical markers' `published_from.attributions` across the reordered runs.
- [ ] Run `just test-one tests/acceptance/test_overlapping_publications_acceptance.py` on the certified tuple; record counts and the tuple. A capability refusal is reported verbatim and stops the task.
- [ ] `just test-fast`, `tasks check`, commit `test(acceptance): the 1b overlap fixture end to end`.

### Task 7: Prove the cut and discharge it

**Files:** `python/tests/n2_arms_cut48.py` (new), `acceptance/n2_arms_cut48.py` shim and `acceptance/test_n2_cut48.py` (new), `python/tools/cut48_acceptance.py` (new), `test_recent_cut_acceptance.py`; the live guards Tasks 3 to 5 listed; roadmap accounting, current docs and the new results record.

**Interfaces:** `CUT48_ARMS`, `DECLARATION_UNITS`, `UNIT_CHECKS`, `CO_CITED = ()`, `unit_of(row: str) -> str`; `cut48_acceptance.declared_accounting() -> (32, 32, 5)`; runner `main(argv: list[str]) -> int` chaining cut 47 before the new durable and N2 modules.

- [ ] Materialize the 32-unit table into `n2_arms_cut48.py`; each mutation targets one unique source span, keeps the module importable, and fails its named check against a passing baseline. Pin the completed declaration's content digest in the guard and commit them together.
- [ ] Retarget every live arm Tasks 3 to 5 listed (cut 23 W10g; cut 28 W8 and W8b-a..d; cut 41 Z5-a/b/c re-read; cut 44 J17a/b; cut 45 G10-d/f, G12-a/b/c/d/e/g/h/i/l; cut 46 Y17 arms over `_selected_attributions`; cut 34 BI-4/BI-8 re-read; cut 7's `Location` checks) in their owning guards with a recorded reason and a proved kill; rewrite the three obligation-changing tests with a ledger disposition. Run `just test-one tests/test_arm_staleness.py tests/test_frozen_guards.py` to find anything missed.
- [ ] Add the shim and guard on cut 47's pattern with `frozen_guards.content_pin_holds`/`commit_pin_holds`; pin Task 1's freeze commit and the cut document's §§2–7. Verify the 32/32 inventory, unique checks, unique spans, AST parse after sabotage, passing baselines and sound kills, with the isolated git environment.
- [ ] Add `test_cut48_pilot`: `baseline` and `audit` for W20-b alone, asserting `resolved`/`sound`; run it and one durable case before the chain.
- [ ] Add `cut48_acceptance.py` with `DEFAULT_WORK = MAIN_CHECKOUT / ".work" / "acceptance" / "cut48"` and the frozen prefix and phase tuples; add the `(cut48, 48, (32, 32, 5))` row, id and `assert "guarantee rows exercised: 5 (4 newly closed: W19, W20, G14, Y19; J17 amendment reclosed)" in output` to `test_recent_cut_acceptance.py`; `just test-one tests/test_recent_cut_acceptance.py -k cut48`.
- [ ] Commit the declaration, guard and runner after `just test-fast` and `tasks check`, then run the complete chain: `just --set one_cmd "cd python && uv run --frozen python tools/cut48_acceptance.py" test-one -q`, harness-tracked, with command, counts, exit status and log retained under the task's `$WORK_ROOT/beliefs/beliefs-918fd2/` directory with a retained-item note. On refusal or failure, read the completed output before retrying.
- [ ] Only after a clean chain: write `docs/plans/2026-10-28-conformance-cut-48-results.md`, add `ACCOUNTING[48]` naming the results §2 with the four new rows and J17, remove the seven `REOPENED` entries, regenerate totals, and update README, ledger, roadmap (close `world-read` again), spec and plan status. Re-run the documentation tests and `just check`.
- [ ] File the science consumer task (`tasks add --project sci`, sourced to beliefs-918fd2, origin agent) carrying spec §8 verbatim: the `Carrier` content check, the three-item adopt checklist, `mount_holding`/`cited`, `explain` wording, pins, the in-place change refusal, chain retention, `show`'s marker naming, and the `SYMBOL_FIELDS` replacement; make sci-4a3543 and sci-9104fb depend on it. Note the ruling's completion on beliefs-81367e and beliefs-c800ef.
- [ ] Request the final whole-branch read-only review under the executing skill; note it before acting; fix or rule on Critical and Important findings in the prescribed corrective rounds with a fresh scoped re-review; minors go to the ledger as deferred. Close children on the branch, account for retained evidence, run `tt-report`, then close beliefs-918fd2 and beliefs-354eae with the cut, leave beliefs-c800ef for the user's call (the rule has landed), and integrate locally only when review and checks pass. No push.

## Self-review

Spec coverage: §4.1–§4.4 → Task 2; §5.0–§5.4 → Task 3; §4.5 → Task 4 (with Review Focus 3 and 5); §6 → Task 5 (G14-a/b/c) and Task 4 (correction records); §7 → Task 5 and Task 6 (Review Focus 4); §8 → Task 7's filed science task; §9 → Tasks 1 and 7; §10 → Task 1's cut limitations and Task 6's refusal cases; §11 → the Global Constraints and every task's test front door; §12's on-approval notes were done before this plan. Review Focus 1 and 2 are pinned in Tasks 2 and 3. Types: `AddressEntry`, `Location.holders`, `holders_of`, `captured()`, `_mapped_holders()`, `input_version`, `rule_input(version)` are named once and reused by name. Proportion: the plan decides files, names, orders and tests and leaves bodies to the implementer; the only algorithm spelled out is where the spec fixes it.
