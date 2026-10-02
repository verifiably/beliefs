# Publication attribution — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Freeze a selected adopted record's origin inside the publication
snapshot, forward earlier origins unchanged, and discharge the release and
pre-intent amendments in the successor cut.

**Architecture:** Extend `published_from` and the existing snapshot codec.
One preparation helper reads a registry snapshot and the already-held corpus
captures, validates holders in deterministic order, and returns an immutable
origin tuple. The existing marker reconstruction and recovery paths consume
that tuple; one private pure predicate enforces the v2/v3 release pairing at
pinned boundaries. No provenance graph, new recovery state or re-pin act.

**Tech Stack:** Python 3.11+, frozen dataclasses, the existing coordination
contract loader, `science.identity.v1`, pytest, N2 and the certified acceptance
runner. No new dependency.

**Spec:** `docs/superpowers/specs/2026-10-02-publication-attribution-design.md`,
revised and author-approved at `dcc8a53` after round 1's P1/P2 decisions, under
the review's fix-then-plan disposition. Read both artifacts before execution.

**Status:** approved 2026-10-02 after plan round 1; native execution started.
Native execution continues the method used for acceptance; no task worker or
review agent is dispatched while writing this plan.

## Global Constraints

- Reuse `.worktrees/publication-attribution`, branch `feat/publication-attribution`,
  locked on WORK_ROOT storage. It is stacked on acceptance discharge `d466f5f`;
  main's independent `abb4f1c` changes vendored tooling only. `just setup` passed.
  Run tools from the canonical worktree path (`pwd -P`) to avoid pytest ELOOP
  through the `.worktrees` symlink. User-facing paths include the worktree prefix.
- Proposed successor is **cut 46**, following cut 45. Recheck all branches and
  worktrees in Task 0 before freezing; an occupied number requires a plan
  amendment. Freeze obligations before changing product code.
- **`root.py` is the one `atoms` importer** (`test_capability_boundary.py`,
  `TestTheCompositionRootIsTheOneAtomsImporter`). A classification over engine
  cause types, a predicate over engine exceptions, or any other engine-typed
  behaviour lives in `root.py` and reaches its boundary through a seam callable
  (cut 35's `StoreActSeam.store_refusal`, `b065711`), never as an import in the
  boundary module. Every new caller of a write primitive joins
  `WRITE_ENTRY_POINTS` in `test_permit_boundary.py` and gains a `Case` in
  `test_permit_entry_points.py`'s `CASES`; the inventory is closed in both
  directions.
  This slice adds no write primitive. Task 6 checks both inventories.
- **Every discharged cut adds its row to `test_recent_cut_acceptance.py`**: the
  runner import, its `(runner, cut, accounting)` parametrization entry with the
  declared-arm, declaration-unit and guarantee-row counts, and the cut's
  guarantee-rows-exercised line. Cuts 33, 34 and 35 landed theirs at `f4c2cef`,
  `c77b2aa` and after cut 35's final review; the plan's runner task owns the row.
  Task 6 owns `(cut46, 46, (36, 36, 3))` and its Y5/Y17/Y18 line.
- **Accounting:** 36 arms, 36 declaration units, three exercised guarantee
  rows: three Y5 units, sixteen Y17 units and seventeen Y18 units. Y17/Y18
  are new; Y5 is reopened for this amendment, not newly banked. No co-citation
  or reuse of an earlier check node id.
- Preserve `marker_uid`, `marker_address` and the `marker_consistent` function
  body. Attribution changes snapshot commitment and exported content, never
  marker uid/address/id. Preserve `SELECTION_DOMAIN`, `selection.v1`, old
  snapshot bytes, request/transport schemas and in-flight v2 recovery.
- Ship v3 explicitly; `shipped_coordination()` stays v2. Existing manifests
  remain immutable. New v3 write roots are the Science 1a deployment requirement;
  markerless replicas cannot be published. No migration or origin invention.
- V2's new carried-selection refusal follows existing selection, closure,
  derived-pin and staging-profile checks, and all admission checks. V2 carrying
  v3 refuses earlier with `pins-disagree` on `coordination`. Every new publish
  performs one preparation registry scan, including v2 own-only; retries do none.
  Retirement/departure retains the admission and does not make it unregistered.
- V3 ignores only source coordination pins during destination derivation;
  science-contract and non-coordination disagreements remain refusals. Source
  markers are read under their own captured pins. Preserve exact v2 derivation.
- Forward only explicit earlier entries. A legacy unattributed v2 B yields B's
  own marker origin even if B previously carried A; historical missing provenance
  is unreconstructable. Attribution is a claim, not proof of authorship.
- Preserve all frozen cut bodies and canonical arm declarations. One known live
  retarget is cut 40's **Y6-a**, whose snapshot-probe call gains `attributions`.
  Retarget its sabotage in `acceptance/test_n2_cut40.py`, keeping its check and
  assertion. Any other staleness needs a named disposition before continuing.
- Tests use `just test-one`; implementation commits use `just test-fast` first.
  Portable and acceptance modules run in separate invocations, since combining
  their roots can shadow `conftest`. `test-fast` ignores `tests/acceptance`;
  explicitly named `test-one` acceptance paths still collect. Use `tasks` for
  every task mutation, including `trial-arm` after every start; require clean
  `tasks check`, and report warnings. Preserve native execution after plan approval.
- Run durable checks on the certified tuple using the main checkout's
  `.work/acceptance/cut46` and existing `checkout.MAIN_CHECKOUT` resolution.
  Missing capability is refusal, not a skip. Before the full successor chain,
  finish the bounded pilot in Task 7 through its verdict. Use harness-tracked
  foreground sessions, no detached jobs or host-pointer changes.
- Commit specs, plans and task evidence in this branch. No push, PR, integration
  or Science configuration write is authorized here. The N2 preflight pilot task
  `beliefs-aa9f88` remains after this publication slice.

## Review Focus

1. **Restored personal corpus with no marker:** reads remain possible, but new
   publication refuses before intent. Task 3 pins the refusal; Task 5 exercises
   real restore and public `admit_arrival`, rather than faking adoption.
2. **Holder retires between capture and preparation:** its retained admission
   still supplies origins. Tasks 3/4 test the second-scan boundary and no added
   live-status check; Task 5 exercises an actual retirement.
3. **Origin address changes through an alias:** output keys are the selected
   canonical ids, with no unselected source entries. Tasks 3/5 cover canonical
   selection and mixed holders; no semantic-identity rekeying is allowed.
4. **Saved snapshot has a valid origin but the wrong release:** Task 2 pins
   exact codec distinctions, and Task 4 tests `_load` with coherent request
   digests so identity refusal cannot mask the pin/format guard.
5. **Remote retry has only its mark and export:** Tasks 4/5 prove origins survive
   without saved selection/request or source-world access; altered export content
   still fails its existing identity/content checks before any push.

## File map

Paths below are repository-relative; add the worktree prefix when showing them
to the user. Existing modules keep their responsibilities.

| Files | Responsibility / task |
|---|---|
| `docs/designs/2026-10-02-conformance-cut-46.md` (new), publication guarantee table, formal coverage map, `test_designs_corpus.py`, `tools/roadmap_status.py` | Freeze Y5 amendment and Y17/Y18; account reopening (0) |
| `python/tests/fixtures/publication-v2-marker.md`, `publication-v2-selection.v1` (new) | Pre-change canonical bytes captured before implementation (0) |
| `contracts/coordination/v3/CONTRACT.yaml` (new), `profile.py`, `publication.py`, `corpus.py`, `publication_arrival.py` under `python/src/beliefs/` | Release, content and pinned guards (1) |
| `python/src/beliefs/publish_request.py` | Snapshot codec and release-specific destination pins (2) |
| `python/src/beliefs/publish.py` | Preparation, frozen reconstruction and request/export guards (3/4) |
| `python/tests/test_publication_attribution.py` (new); existing publication, request, arrival, coordination and publish tests | Portable declaration checks and focused regressions (1–4) |
| `python/tests/acceptance/test_publication_attribution_acceptance.py` (new) | Ten durable end-to-end functions (5) |
| `python/tests/n2_arms_cut46.py`, acceptance shim/guard, `python/tools/cut46_acceptance.py` (new), `test_recent_cut_acceptance.py` | Declaration, mutation audit, successor and inventory (6) |
| `python/tests/acceptance/test_n2_cut40.py` | Y6-a live sabotage retarget (4) |
| README, guide, adoption ledger, roadmap, spec/plan status, task records, `docs/plans/2026-10-02-conformance-cut-46-results.md` (new) | Current-facing status, release limitations and discharge evidence (0/7) |

## Declared checks

Each unit below has exactly one portable check named
`test_publication_attribution.py::test_<lowercase unit with underscore>_<suffix>`.
Parameter cases belong to that one unit. For example Y5-c maps to
`test_y5_c_v3_destination_pins`. Durable functions in Task 5 are additional
evidence; their ten functions do not enlarge the declaration-unit count.

| Unit | Suffix and decisive assertion | Mutation responsibility |
|---|---|---|
| Y5-c | `v3_destination_pins`: v2/v3 source coordination pins are replaced by writer v3; other domains are unioned | Keep source coordination in v3 union |
| Y5-d | `v3_disagreement`: base and non-coordination mismatch refuse with exact field/corpus ids | Suppress a v3 world-domain disagreement |
| Y5-e | `v2_pin_precedence`: source v3 plus writer v2 refuses coordination disagreement before preparation scan/intent | Apply v3 derivation relaxation to v2 |
| Y17-a | `local_holdings`: Fresh/ForkOf yield None under v2 and empty tuple under v3 | Emit an origin for a non-replica |
| Y17-b | `first_carry`: each selected world kind gets holder and own marker uid | Omit replica own-origin fallback |
| Y17-c | `forwarded_origin`: earlier tuple is copied exactly | Replace earlier origin with current holder |
| Y17-d | `selection_scope`: no unselected source attribution escapes | Return entire source attribution map |
| Y17-e | `distinct_holders`: canonical selected keys and per-holder origins, ascending | Reuse one source marker for another holder |
| Y17-f | `v2_refusal`: exact unpinned reason and all selected replica ids ascending | Permit v2 replica selection |
| Y17-g | `before_intent`: v2 refusal runs before `_open_publication` and leaves ops/written state unchanged | Bypass preparation for a v2 destination |
| Y17-h | `markerless_replica`: marker-absent refuses, not an own-only classification | Treat markerless ReplicaOf as Fresh |
| Y17-i | `missing_holder`: v2/v3 missing admission reports first holder and ascending refs | Default unknown admission to Fresh |
| Y17-j | `invalid_source_order`: reverse input order still reports ascending first invalid holder | Iterate source captures in registry/input order |
| Y17-k | `admission_before_layout`: missing admission wins before an earlier holder's invalid marker is inspected | Validate layouts during admission discovery |
| Y17-l | `held_capture`: preparation uses held records/manifests once per replica, never reopens a root | Reopen source through ReadView |
| Y17-m | `local_frozen_marker`: reconstruction forwards frozen local origins, with source access trapped | Drop frozen origins for local reconstruction |
| Y17-n | `remote_frozen_marker`: reconstruction forwards frozen remote origins; mark-only recovery uses export | Drop frozen origins for remote reconstruction |
| Y17-o | `registry_boundary`: once-per-new-publish scan, retained retired admission, scan error before intent | Reject an admission with terminal status |
| Y17-p | `legacy_source`: unattributed v2 B falls back to B; explicit v3 B forwards A | Guess absent upstream provenance |
| Y18-a | `closed_shapes`: exactly old/new nested maps; old marker bytes remain exact | Accept unknown nested keys |
| Y18-b | `member_types`: malformed containers/triples/mixed members return malformed or factory/codec refusal | Coerce malformed attribution members |
| Y18-c | `strict_order`: duplicate and descending keys refuse, including valid-empty distinction | Remove strict ascending check |
| Y18-d | `selected_addresses`: invalid world ids and unselected keys refuse | Omit selected-key membership check |
| Y18-e | `identity_split`: same intent/different origins keep uid/address/id, change content and remain consistent | Include origins in marker uid |
| Y18-f | `snapshot_formats`: old bytes and new bytes round-trip exactly; missing/empty remain distinct | Decode absent entries as empty tuple |
| Y18-g | `snapshot_commitment`: origin-only change moves snapshot identity | Omit origins from snapshot projection |
| Y18-h | `snapshot_tamper`: origin edit reports mismatch, malformed entry reports undecodable | Bypass snapshot identity check |
| Y18-i | `snapshot_pin`: coherent request/snapshot with wrong pairing reports snapshot-pin-disagrees before stage | Omit request pin/format guard |
| Y18-j | `staged_release`: shape-valid but unauthorized marker refuses the staged write | Skip stage release predicate |
| Y18-k | `audit_release`: matching profile/manifest plus wrong marker shape yields coordination-facet-malformed | Skip profile-aware audit predicate |
| Y18-l | `arrival_release`: unauthorized marker refuses marker-malformed before admission | Skip arrival release predicate |
| Y18-m | `tip_release`: unauthorized held marker refuses with its corpus id | Skip tip release predicate |
| Y18-n | `source_release`: unauthorized captured marker reports attribution-source-invalid/marker-malformed | Skip source release predicate |
| Y18-o | `remote_release`: validated-export marker must agree with export manifest pin | Skip remote marker release predicate |
| Y18-p | `v3_succession`: v3 names v2 predecessor and retains every outer kind field | Parse v3 against v1 instead of v2 |
| Y18-q | `explicit_activation`: shipped default remains v2; fresh v3 root works, existing manifest cannot be re-adopted | Change shipped default to v3 |

## Task 0: Freeze the successor and amended publication guarantees

**Files:** new cut document; `docs/designs/2026-09-22-publication-design.md`,
`2026-08-04-formal-model-and-claim-calculus-design.md`; `python/tests/test_designs_corpus.py`,
`python/tools/roadmap_status.py`; current-facing README/guide/ledger/roadmap.
**Consumes:** approved spec and plan, verified cut-45 accounting.
**Produces:** immutable cut-46 obligations, Y17/Y18 banked open, Y5 reopened,
and Tasks 0–7 recorded under `beliefs-f50596`.

- [ ] Run `tasks prime`/`tasks ready` here; recheck `git for-each-ref`,
  `git worktree list` and tracked/uncommitted cut documents in each worktree.
  Current evidence: cut 45 highest, Y16 highest publication id, 224/251 closed.
  Require no competing freeze before choosing 46.
- [ ] Before changing the factory or codec, save two pre-change byte fixtures
  in `python/tests/fixtures/` and commit them with the freeze. Run this script
  with the worktree's installed Python from `python/`; it is fixture generation,
  not a direct test-runner invocation:

  ```python
  import sys
  from pathlib import Path
  sys.path.insert(0, str(Path("tests").resolve()))
  from test_publish_intent import intent
  from nodes.core.frontmatter import node_to_markdown
  from beliefs import stored
  from beliefs.publication import marker_record
  from beliefs.publish_request import Snapshot, encode_snapshot
  node = stored.run_node("a", title="a", spec="s", produces=[])
  marker = marker_record(intent(), world_id="a" * 32, epoch="b" * 64, selection=(node.id,))
  assert "attributions" not in marker.facets[stored.COORDINATION_FACET]["published_from"]
  fixture = Path("tests/fixtures")
  (fixture / "publication-v2-marker.md").write_bytes(node_to_markdown(marker).encode("utf-8"))
  (fixture / "publication-v2-selection.v1").write_bytes(
      encode_snapshot(Snapshot("e" * 32, ((node.id, node_to_markdown(node)),))))
  ```

  Record both SHA-256 values. Y18-a/f compare exact bytes against these committed
  fixtures after implementation; never regenerate expected bytes from new code.
- [ ] Append Y17/Y18 with spec §8's exact guarantees. Amend Y5's current-facing
  description with v2 carried-selection refusal, holder/source failures and
  v3 writer-derived coordination. Preserve the historical v2 guarantee as a
  release-specific obligation and all frozen cut-40 wording.
- [ ] Add Y17/Y18 to `GUARANTEE_TABLES["Y"]`; add their classification rows in
  formal coverage §5 (Y17: RF† + CS; Y18: CS + OInv). Set
  `REOPENED["Y5"] = ("conformance-cut-46 §3", 46)` in the existing roadmap tool.
  Derive totals with `cd python && uv run --frozen python tools/roadmap_status.py`:
  freeze is **223/253**, with Y5 reopened and two new rows; discharge is
  **226/253**, absent intervening verified accounting changes.
- [ ] Write the frozen cut using cut 45's seven headings: What this cut is;
  The boundary; Selection; Accounting; N2 and acceptance obligations; Second
  reader; Limitations. Include this full 36-unit table, source/refusal order,
  release guards, the explicit v2 amendment/new-root prerequisite, and
  `PREFIX_RUNNERS = ("cut45_acceptance.py",)` with
  `PHASE_MODULES = ("test_publication_attribution_acceptance.py", "test_n2_cut46.py")`.
- [ ] Update README/design count, guide citation, adoption ledger and roadmap
  together; reopen `world-read` for this slice without erasing historical
  dogfood or cut evidence. Register Tasks 0–7 through `tasks add --parent
  beliefs-f50596 --plan publication-attribution --step '<exact Task heading>'`,
  direct process, sequential dependencies. After starting each, run trial-arm.
- [ ] Run `just test-one tests/test_designs_corpus.py tests/test_check_guide.py`,
  `just test-fast`, `tasks check`; commit
  `docs(cut): freeze publication attribution obligations for cut 46`.
  Record the freeze commit and document SHA-256 in task notes. Do not edit the
  frozen body afterward without an explicit disposition.

## Task 1: Ship v3 content and enforce it at pinned boundaries

**Files:** coordination v3 resource; `profile.py`, `publication.py`, `corpus.py`,
`publication_arrival.py`; new portable test module, existing coordination,
publication and arrival tests. `coordination.py::tips_at` stays shape-only.
**Consumes:** frozen marker/release rules.
**Produces:** `marker_record(..., attributions: tuple[tuple[str,str,str],...] | None = None)`;
private `_attributions_malformed(value: object, selection: tuple[str,...]) -> bool`
over the list wire shape; `_marker_release_malformed(node: Node, coordination_pin: str | None) -> bool`
after shape validation. Neither helper performs I/O.

- [ ] RED: add Y18-a/b/c/d/e/p/q. Reuse `test_publish_intent.intent`,
  `coordination_profile`, `raw_add` and `test_publication` field cases. Pin
  old factory output using the pre-change canonical text, not an expected value
  generated by the new implementation. Include exact None/empty distinction:

  ```python
  old = marker_record(intent(), world_id="a" * 32, epoch="b" * 64,
                      selection=("run:a",))
  carried = marker_record(intent(), world_id="a" * 32, epoch="b" * 64,
      selection=("run:a",), attributions=(("run:a", "c" * 32, "d" * 32),))
  assert old.id == carried.id and old.uid == carried.uid
  assert marker_consistent(old) and marker_consistent(carried)
  assert node_to_markdown(old) != node_to_markdown(carried)
  assert "attributions" not in old.facets[stored.COORDINATION_FACET]["published_from"]
  assert shipped_coordination() is shipped_coordination(2)
  v3 = shipped_coordination(3)
  assert v3.predecessor == shipped_coordination(2).content_identity
  assert v3.schema_projection() == shipped_coordination(2).schema_projection()
  ```

- [ ] Run `just test-one tests/test_publication_attribution.py -k 'y18_a or
  y18_b or y18_c or y18_d or y18_e or y18_p or y18_q'`; require assertion/API
  failures from absent behavior, not collection errors.
- [ ] Copy the v2 contract resource into v3, change version/lineage/description,
  preserve all kind fields and query vocabulary. Obtain lineage from the actual
  v2 content identity. Extend loader exact versions to `(1, 2, 3)`; predecessor
  is `_shipped_coordination(version - 1)` when version > 1. Keep default 2.
  Extend the fixture helper's shipped-version branch to `version in (2, 3)`.
- [ ] Implement the wire validator in `publication.py`: exact list, exact
  three-member lists of exact strings, world address, selection membership,
  two hex32 ids, then strictly ascending unique addresses. Exact empty is valid.
  At the factory/snapshot tuple boundary require exact outer/inner tuples
  before converting to wire lists. Check selection validity before nested
  membership checks. Accept exactly the three-key/four-key `published_from`
  shapes; do not alter binding rules or `marker_consistent`'s body.

  ```python
  def _marker_release_malformed(node, coordination_pin):
      from beliefs.profile import shipped_coordination
      carried = "attributions" in node.facets[stored.COORDINATION_FACET]["published_from"]
      expected = "coordination:" + shipped_coordination(3 if carried else 2).content_identity
      return coordination_pin != expected
  ```

- [ ] RED: add Y18-j/k/l/m with v2 + entries, v3 + missing entries, and
  missing/unsupported pin cases. For audit, keep supplied profile and manifest
  matching so `profile-mismatch` does not mask content validation. For arrival,
  replace only `publication_arrival.admit_arrival` with a call recorder and
  assert it stays empty. Tip cases assert reason and exact corpus id.
- [ ] Pass the held coordination pin into corpus's private audit wrapper from
  `_record_findings`' profile. Keep mismatch/withheld-domain behavior intact.
  In `_stage_marker`, test release after the existing shape/consistency guard
  and before the write. Arrival/tip reuse `require_publication_layout` unchanged,
  then find its single marker and test release from that root's manifest.
  Arrival maps to marker-malformed; tip wraps the same reason. Pure factory,
  `marker_consistent`, layout and `coordination.tips_at` remain shape-only.
- [ ] Run `just test-one tests/test_publication_attribution.py tests/test_publication.py
  tests/test_publication_arrival.py tests/test_coordination_contract.py
  tests/test_guarded_publication.py`; then fast/task checks. Commit
  `feat(publication): authorize attribution content under coordination v3`.

## Task 2: Bind origins into the existing snapshot and destination pins

**Files:** `publish_request.py`, portable attribution tests, `test_publish_request.py`.
**Consumes:** Task 1's content validator and shipped v3 identity.
**Produces:** `Snapshot(event_token, records, attributions=None)` with the exact
optional tuple type; old/new closed decoder shapes; `derive_pins`' v3 branch.

- [ ] RED: add Y18-f/g and Y5-c/d. Use the existing `_run`/PINNED request
  fixtures to form actual canonical record texts. Cover None and (), unknown
  keys, duplicate/mixed entries, byte-exact old/new round trips and valid
  origin-only identity changes. Include this complete identity check:

  ```python
  records = (("run:a", node_to_markdown(stored.run_node("a", title="a", spec="s", produces=[]))),)
  old = Snapshot("e" * 32, records)
  empty = Snapshot("e" * 32, records, ())
  a = Snapshot("e" * 32, records, (("run:a", "a" * 32, "b" * 32),))
  b = Snapshot("e" * 32, records, (("run:a", "c" * 32, "b" * 32),))
  assert "attributions" not in old.projection()
  assert empty.projection()["attributions"] == []
  assert old.identity() != empty.identity() and a.identity() != b.identity()
  for value in (old, empty, a, b):
      assert decode_snapshot(encode_snapshot(value)) == value
      assert encode_snapshot(decode_snapshot(encode_snapshot(value))) == encode_snapshot(value)
  ```

- [ ] Run `just test-one tests/test_publication_attribution.py -k 'y5_c or
  y5_d or y18_f or y18_g'`; confirm the intended red.
- [ ] Add the frozen optional tuple to Snapshot; use Task 1's validator after
  exact tuple checks. Add the projection key only when non-None. Decoder accepts
  only the old/new field sets, validates exact lists before tuple conversion,
  then retains canonical re-encoding. Preserve domains/file names.
- [ ] Add v3 to `PUBLISHING_COORDINATION`. Determine writer coordination first
  for dispatch, but preserve existing error precedence: base disagreement first,
  contributing non-coordination/domain disagreements next, unsupported writer
  pin afterward. In the v3 branch alone skip source namespace coordination:

  ```python
  if coordination == V3_PIN and namespace == "coordination":
      continue
  if domains.setdefault(namespace, pin) != pin:
      raise PublicationRefused("pins-disagree", corpus_ids=corpus_ids, field=namespace)
  ```

  Define `V3_PIN` from the shipped content identity in this module, not a literal
  hash. Retain the existing writer coordination installation/disagreement check.
  Y5-c includes two differently coordinated sources, a source-only world domain,
  and a writer-only non-coordination domain that still is not automatically unioned.
  Y5-d parameterizes base, contributing biology and another namespace disagreement.
- [ ] Run `just test-one tests/test_publish_request.py tests/test_publication_attribution.py`.
  Keep every original v2 pin-refusal assertion; do not relax its case table.
  Run fast/task checks, commit
  `feat(publication): commit carried origins in selection snapshots`.

## Task 3: Derive origins from immutable admissions and held captures

**Files:** `publish.py`, portable attribution tests.
**Consumes:** Task 1's layout/release checks and Task 2's supported pins.
**Produces:** private `_selected_attributions(read: WorldReadView, registry: RegistryView,
selected: tuple[str,...], coordination_pin: str)`
returning `tuple[tuple[str,str,str],...] | None`; this helper reads captures only,
performs no registry scan, opens no root/intent and writes nothing.

- [ ] Build one small structural fixture for this helper in the portable test
  module. Its Node contents are deliberately layout-only, not durable minting
  evidence. Use real marker factories, manifests and AdmissionRecord values:

  ```python
  def capture_fixture(holdings, *, source_version=2, carried=None):
      profile = coordination_profile(None, version=source_version)
      manifests, captures, owners, admissions = {}, {}, {}, []
      for cid, (provenance, refs) in holdings.items():
          manifests[cid] = CorpusManifest(2, cid, pins_for(profile))
          records = tuple(Node(id=ref, uid=ref.split(":", 1)[1], kind=ref.split(":", 1)[0],
                               title=ref, body="", facets={}, relations=[]) for ref in refs)
          entries = None if source_version == 2 else (carried or {}).get(cid, ())
          marker = marker_record(intent(event_token=cid), world_id="d" * 32,
              epoch="f" * 64, selection=tuple(sorted(refs)), attributions=entries)
          captures[cid] = (*records, marker)
          owners.update(dict.fromkeys(refs, cid))
          admissions.append(AdmissionRecord(manifests[cid], provenance, "actor"))
      read = SimpleNamespace(corpus_of=owners.get, captured_manifest=manifests.__getitem__,
                             captured_records=captures.__getitem__)
      return read, RegistryView(tuple(admissions)), captures
  ```

  Import exact value types from `beliefs.world.registry`; add the test's get/resolve
  adapters only where the wrapper fixture below needs them. No product protocol
  or fixture-framework expansion is needed.
- [ ] RED: add Y17-a/b/c/d/e/f/h/i/j/k/l/p and Y18-n. Y17-b parameterizes
  `sorted(stored.WORLD_KINDS)` with valid `kind:a` ids. Y17-a covers real `Fresh`
  and `ForkOf` value forms. Y17-j removes the lower holder's marker and adds a
  second marker to the higher holder, supplies registry entries high-first,
  and asserts lower holder/marker-absent. Y17-k combines an earlier invalid layout
  with a later missing admission; the missing admission must win without any
  layout read. Y18-n uses shape-valid v3 metadata under a captured v2 pin.

  ```python
  cid = "b" * 32
  read, registry, captures = capture_fixture({cid: (ReplicaOf(cid), ("run:a",))})
  assert _selected_attributions(read, registry, ("run:a",), V3_PIN) == (
      ("run:a", cid, marker_uid(cid)),)
  captures[cid] = tuple(n for n in captures[cid] if n.kind != MARKER_KIND)
  with pytest.raises(PublicationRefused) as caught:
      _selected_attributions(read, registry, ("run:a",), V3_PIN)
  assert (caught.value.reason, caught.value.corpus_ids, caught.value.refs, caught.value.field) == (
      "attribution-source-invalid", (cid,), ("run:a",), "marker-absent")
  ```

- [ ] Run `just test-one tests/test_publication_attribution.py -k 'y17 or y18_n'`
  selecting only the Task 3 functions already written. Add later-task checks
  when their seams exist; never commit future failing tests.
- [ ] Implement two passes over grouped selected holders: first discover every
  admission in ascending cid order and refuse missing information with exact
  holder/refs; then dispatch v2 refusal or validate v3 replica captures in that
  order. Fresh/ForkOf contribute nothing. Keep terminal status out of the
  admission lookup. Require layout and captured-pin release, translating only
  `PublicationArrivalRefused` to source-invalid; existing capture errors propagate.

  ```python
  grouped = {}
  for ref in selected:
      holder = read.corpus_of(ref)
      assert holder is not None  # complete canonical world selection
      grouped.setdefault(holder, []).append(ref)
  admissions = {record.corpus_id: record for record in registry.admissions}
  for holder in sorted(grouped):
      if holder not in admissions:
          raise PublicationRefused("attribution-holder-unregistered",
              corpus_ids=(holder,), refs=tuple(sorted(grouped[holder])))
  replicas = tuple(holder for holder in sorted(grouped)
                   if type(admissions[holder].provenance) is ReplicaOf)
  if coordination_pin == "coordination:" + shipped_coordination(2).content_identity:
      if replicas:
          raise PublicationRefused("attribution-contract-unpinned", corpus_ids=replicas)
      return None
  sources = {}
  for holder in replicas:
      records = read.captured_records(holder)
      manifest = read.captured_manifest(holder)
      try:
          require_publication_layout(records)
          (marker,) = (node for node in records if node.kind == MARKER_KIND)
          if _marker_release_malformed(marker, manifest.profile.domains.get("coordination")):
              raise PublicationArrivalRefused("marker-malformed")
      except PublicationArrivalRefused as refused:
          raise PublicationRefused("attribution-source-invalid",
              corpus_ids=(holder,), refs=tuple(sorted(grouped[holder])), field=refused.reason) from refused
      earlier = marker.facets[stored.COORDINATION_FACET]["published_from"].get("attributions", [])
      sources[holder] = (marker.uid, {row[0]: tuple(row) for row in earlier})
  result = []
  for ref in sorted(selected):
      holder = read.corpus_of(ref)
      if holder in sources:
          uid, earlier = sources[holder]
          result.append(earlier.get(ref, (ref, holder, uid)))
  return tuple(result)
  ```

  The helper's caller supplies only a supported destination pin after derive_pins;
  add the necessary typed local mappings/casts while keeping this two-pass order.
- [ ] Cache one validated marker/map per replica holder, then emit selected ids
  ascending, using existing entry or `(ref, holder, marker.uid)`. Never follow
  upstream entries, read live roots, or include an unselected source entry.
  Return None for v2 own-only; return a tuple for every v3 path, even empty.
- [ ] Run all new portable tests currently present plus existing publication
  tests; fast/task checks; commit
  `feat(publication): select origins from held replica publications`.

## Task 4: Wire preparation and freeze into both recovery paths

**Files:** `publish.py`, portable attribution tests, `test_publish.py`,
`acceptance/test_n2_cut40.py` for its live Y6-a override.
**Consumes:** helper from Task 3, snapshot tuple from Task 2.
**Produces:** one pre-intent registry scan; tuple passed to probe, saved Snapshot
and `_expected_marker`; `_load` pin-format guard; remote export release guard.

- [ ] RED: add Y5-e, Y17-g/m/n/o and Y18-h/i/o. Build a narrow wrapper fixture
  around real `publish` and real `derive_pins`: use an actual project node from
  `raw_coordination_node`, a resolver with mounted()/resolve(), temporary ops
  and destination directories, and the held-capture adapters from Task 3.
  Patch only `current_epoch`, `open_world_view`, `evaluate_query` and the written
  manifest load to supply already-completed selection/capture. Keep selection,
  pins and actual preparation code in the act. `world.registry` counts scans;
  `_open_publication` is a recorder that fails if reached in a refusal case.
  Assert unchanged ops tree and zero intent calls for every new refusal.
- [ ] Y5-e supplies writer v2/source v3 and traps registry(): expect
  `pins-disagree`/coordination before that scan. Y17-g supplies two v2 replicas:
  expect unpinned with both ids ascending, one scan, no intent. Y17-o supplies
  retained admission plus `StatusRecord(cid, "retired", "actor")`; origin is
  unchanged. Its second case makes only preparation registry() raise an existing
  `RegistryMalformed` sentinel, which must propagate before intent. Missing-holder
  cases run under both v2 and v3, including a Fresh-only selected record.
- [ ] Wire the act without moving earlier checks:

  ```python
  attributions = _selected_attributions(
      read, world.registry(), selection.selected, pins.domains["coordination"])
  records = tuple((address, node_to_markdown(read.get(address))) for address in selection.selected)
  _require_snapshot_records(read, records, attributions=attributions)
  # The existing _open_publication call stays immediately after complete probing.
  # Once its real token exists:
  snapshot = Snapshot(token, records, attributions)
  ```

  Extend `_require_snapshot_records(read, records, *, attributions=None)` to
  construct the probe Snapshot with entries, retaining the reparse-to-capture
  comparison. `_expected_marker` passes `a.snapshot.attributions` to the factory.
  Y17-m/n build an attempt with local/remote destination and a frozen origin tuple;
  assert exact reconstructed tuple and trap all registry/source read functions.
- [ ] `_load` keeps intent agreement and snapshot identity checks first, then
  validates request coordination pin and snapshot None/tuple pairing. Return
  `RequestCorrupt("snapshot-pin-disagrees")` for unsupported/missing/mismatched
  pin. Y18-i creates each request with the **matching snapshot identity** before
  changing its pin, so the new guard is reached. Y18-h changes only saved origins
  for mismatch, and a malformed member for undecodable. Verify old v2 recovery.
- [ ] `_marker_agrees` retains node parse, content, consistency, uid and count
  checks, then applies release from the already-validated export manifest.
  Its signature stays unchanged; do not compare against missing frozen files or
  inspect a source world. Y18-o supplies a canonical marker file and export
  manifest, exercising the actual predicate after the existing marker checks.
  Full artifact identity behavior is Task 5's durable evidence.
- [ ] Add a new live `_LIVE_SABOTAGES["Y6-a"]` override (cut 40 has no table yet), applying `replace` to the tuple returned by `frozen_guards.live_guards` that staleness audits. Add this override to cut 40's guard using the
  extended probe call. Its after-text still reselects canonical texts **after**
  intent, preserving attributions and the existing Y6-a check/assertion. Use
  `dataclasses.replace` on the imported frozen arm, like cut 33. Do not edit
  `python/tests/n2_arms_cut40.py` or an old cut body. Confirm exactly one anchor
  match and parseable mutation with `just test-one tests/test_arm_staleness.py`.
- [ ] Run `just test-one tests/test_publication_attribution.py tests/test_publish.py
  tests/test_publish_request.py tests/test_publication_arrival.py`, then fast/task
  checks; commit `feat(publication): freeze origins before intent and reuse them on retry`.

## Task 5: Prove first carry, forwarding and retries on real registered roots

**Files:** new `acceptance/test_publication_attribution_acceptance.py`.
**Consumes:** working publish/recovery APIs and existing durable fixtures.
**Produces:** exactly these ten durable test functions; parameter cases do not
change that function inventory.

| Function | Evidence |
|---|---|
| `test_first_carry_durably` | Real A v2 publish → export/copy/restore → B admit_publication → epoch → B v3 publish; all selected replica-held records name A |
| `test_forwarding_without_origin_durably` | B v3 carries A and authors a distinct record; C holds B only, forwards A and attributes B's own record to B |
| `test_two_carriers_and_selection_durably` | Disjoint A/D publications, selected subsets and a query using a deprecated ref; canonical ids and distinct origins, no extra entries |
| `test_markerless_replica_durably` | Replicate/restore an unpublished corpus, admit_arrival with verified ReplicaOf; read succeeds, v2/v3 publication refuses before intent |
| `test_retirement_after_capture_durably` | Retire after open_world_view returns its capture; retained admission supplies identical origin; actual state drift remains refused |
| `test_local_retry_frozen_durably` | Crash after partial population; remove/make source unavailable and trap origin preparation; resume writes exact originally frozen marker and one binding |
| `test_remote_retry_export_only_durably` | Crash after remote mark; remove request/selection/source access, retain mark/export; resume forwards exact origins without lookup, one binding/report |
| `test_new_roots_and_arrival_releases_durably` | New explicit v3 root succeeds; existing v2 manifest cannot be replaced; restored v3 publication admits under own pin |
| `test_snapshot_and_staged_marker_tamper_durably` | Saved origin edit refuses request-corrupt; staged same-identity marker with wrong origins refuses staging-corrupt |
| `test_remote_export_origin_tamper_durably` | Origin edit after mark fails export evaluation/identity before transport; no push or binding |

- [ ] Reuse cut 40's `source`, `corpus`, `Clock`, `crash`, `token_of_last_intent`,
  chain/report helpers and cleanup; reuse `DirectoryTransport`, cut 42's
  `recipient_copy` pattern, ObserverSet/ArtifactCarrier and root lifecycle acts.
  Do not repoint shared launchers or fabricate an accepted ReplicaOf registry row.
  Introduce a local helper for new explicit v3 writers: initialize root, compile
  v3 profile, adopt first manifest, mount resolver, mint project selecting the
  actual world records, bind exactly `RequiredCapabilities.publishes()` for
  publish/resume. Setup runs under FULL; every act under its exact permit.
- [ ] The A/B/C sequence avoids overlap: B adopts A beside a distinct write corpus;
  C holds only B's publication and its own distinct write corpus. A/D subsets
  retain relation closure. Build the epoch after all setup records/admissions
  are final. Use `hold_shipped` for the four existing derivation-rule bindings;
  v3 is the packaged coordination resource activated by the writer profile,
  not an additional `DerivationBindings` member. Never mint honest source
  markers with raw writes in these flows.
- [ ] In the two-carrier flow, first try a new publish from an existing v2 writer
  with both valid v2 carriers selected: assert attribution-contract-unpinned,
  sorted carrier ids, unchanged intent-chain tip and ops tree. Then use a new
  v3 writer for the positive case. This proves the shipped-v2 amendment on
  honest publication sources as well as the portable refusal-order checks.
- [ ] For portable release regressions, keep the v2/v3 paired profiles capable
  of storing markers. Missing/unsupported-pin predicate cases are additional
  shape-valid inputs; a later unknown-kind or profile-mismatch refusal is not
  evidence that a specific release guard ran. Assert its reason/finding and
  no-write behavior, with a call recorder where needed.
- [ ] Write first-carry and forwarding assertions before their runs. Read the
  published marker through `ReadView` and compare the complete list, not just
  count or helper-call observations:

  ```python
  facet = marker.facets[stored.COORDINATION_FACET]
  actual = facet["published_from"]["attributions"]
  expected = [[ref, a_corpus_id, a_marker_uid] for ref in sorted(carried_ids)]
  assert actual == expected
  ```

- [ ] Crash local population by wrapping `CorpusWriter._stage_record` after the
  first successful staged write; allow setup to finish before patching it.
  Discard in-memory writers and restore the method before resume. Read the saved
  snapshot before deleting source access, and retain its complete marker bytes
  as the expected result. For remote, use `crash(monkeypatch, "_mark")` after
  mark creation; resume with a fresh writer. Remove only request/selection
  in that case, leaving all existing reveal/export artifacts required by recovery.
- [ ] For retirement, wrap the imported `act.open_world_view`: call original,
  retire via setup world, then return the held view. Do not mutate corpus state
  in this case. In a separate parameter case actually write a record before
  capture and expect `SelectionRefused("corpus-drifted")`; unchanged unmapped
  coordination markers remain selectable. Assert preparation observed retired via `world.status(holder)` after the patched open. Markerless replicas use real
  `admit_arrival` into a fresh world that does not already hold that corpus id.
- [ ] Label malformed/tamper fixtures separately. Permission changes for damaged
  records follow existing `writable` helpers; restore/remove all roots and
  `metadata_root_for` in finally blocks. Registry/source traps apply after initial
  preparation only. Preserve old frozen snapshot byte fixtures and old retries.
- [ ] Run `just test-one tests/acceptance/test_publication_attribution_acceptance.py`
  explicitly from canonical cwd on the certified work root. Expect all ten
  functions (and any documented parameters) collected and green. Portable/fast
  checks run separately. Commit
  `test(publication): prove durable origin forwarding and recovery`.

## Task 6: Declare mutations, guard the freeze and add the successor runner

**Files:** new portable canonical `n2_arms_cut46.py`, acceptance shim/guard,
`tools/cut46_acceptance.py`; `test_recent_cut_acceptance.py`.
**Consumes:** frozen Task 0 checks and actual implementation seams.
**Produces:** exact `(36,36,3)` accounting and predecessor chain, all 36 arms
sound against their own named checks, immutable declaration pin.

- [ ] Write `DECLARATION_UNITS`, `UNIT_CHECKS`, `CO_CITED=()` and `unit_of`
  directly from this table. Each arm's assertion is the frozen obligation; its
  exact before/after texts target the responsible branch shown. Record the
  concrete unique replacement once that branch exists. No synthesized sabotage
  generator, unrelated exception insertion, collection failure or silently
  weakened assertion counts as a kill. Y17-m and Y17-n remove forwarding only
  for their respective local/remote destination, using distinct context anchors.
- [ ] Add the acceptance shim that re-exports the canonical table via the existing
  cut-45 pattern. Copy cut 45's guard structure for inventory, unique/parseable
  sabotage, normal baseline, findings, freeze body/commit, declaration SHA,
  unchanged prior declarations and no reclaimed check. Its PRIOR_ARMS includes
  canonical cut 45; live overrides apply only in their owning guards.
- [ ] Before pinning the declaration hash, run the complete new audit through
  `just test-one tests/acceptance/test_n2_cut46.py`. Every baseline must pass and
  all 36 findings must be sound. A vacuous or malformed arm blocks declaration
  finalization; fix its discriminating assertion or source-target mismatch with
  a task disposition, then rerun the affected check. Pin the accepted canonical
  declaration and Task 0 freeze hashes in the guard.
- [ ] Copy the small cut-45 runner: change cut/default work/prefix/phases, use
  `run_acceptance` and `MAIN_CHECKOUT`, and return the exact accounting below.
  Add the recent-runner import, parametrization/ids entry and output assertion:

  ```python
  rows = {unit.partition("-")[0] for unit in DECLARATION_UNITS}
  assert rows == {"Y5", "Y17", "Y18"}
  assert (len(CUT46_ARMS), len(DECLARATION_UNITS)) == (36, 36)
  return 36, 36, 3
  # successful runner output:
  # guarantee rows exercised: 3 (2 newly closed: Y17, Y18; Y5 amendment reclosed)
  ```

- [ ] Run `just test-one tests/test_recent_cut_acceptance.py tests/test_arm_staleness.py
  tests/test_capability_boundary.py tests/test_permit_boundary.py
  tests/test_permit_entry_points.py`, then the new guard in its separate acceptance
  invocation. Run fast/task checks; commit
  `test(conformance): declare publication attribution cut 46`.
  Record declaration and implementation-source hashes before the successor run.

## Task 7: Pilot, successor evidence, review and discharge

**Files:** new results record; README, guide, ledger, roadmap/tool accounting;
spec/plan status and task records. Frozen bodies stay unchanged.
**Consumes:** clean implementation, all 36 sound arms, ten durable functions.
**Produces:** certified results, fresh whole-branch implementation review, Y5
amendment and Y17/Y18 discharged, task closed with evidence in the same commit.

- [ ] Run the bounded pilot first: first carry, forwarding, local and remote
  retry, plus a baseline and mutation verdict for Y5-c, Y17-c and Y18-i. Use
  explicit `just test-one` node ids for durable cases. To select three arms
  without the full findings fixture, add a pilot check parameterized over those
  exact rows, calling the existing `baseline`/`audit` functions through the same
  test recipe; assert each audit result is sound. This pilot is not another
  declaration unit or a replacement for the complete guard.

  ```python
  @pytest.mark.parametrize("row", ("Y5-c", "Y17-c", "Y18-i"))
  def test_pilot_arm(row, tmp_path):
      (arm,) = (arm for arm in CUT46_ARMS if arm.row == row)
      assert baseline(arm).verdict == "resolved"
      assert audit(arm, tmp_path / row).verdict == "sound"
  ```
- [ ] Inspect pilot results through their final verdicts. If refused/aborted,
  analyze completed portions before changing environment or retrying. Record
  exact kernel, filesystem/volume options and work-root resolution. A capability
  mismatch blocks discharge; report it, never turn it into a skip.
- [ ] Run the full successor in a harness-tracked foreground session:

  ```bash
  just --set one_cmd 'cd python && uv run --frozen python tools/cut46_acceptance.py' test-one -q
  ```

  Preserve its whole output in main `.work/acceptance/cut46-runner.log`, actual
  exit status, phase/test counts, durations and source hashes. The prefix is the
  highest predecessor, cut 45, not merely the publication cuts. A review-requested
  code repair invalidates affected evidence and requires its rerun.
- [ ] After passing local implementation checks, use native execution's required
  fresh whole-branch reviewer. Supply the approved spec/plan, the actual base and
  reviewed head, and verification evidence; reviewers do not inherit assertions
  that final discharge already happened. Record every review round using the
  required tasks-note shape before acting. Fix critical/important findings,
  explicitly dispose of any minor ones, and verify affected behavior.
- [ ] Create results with source/review ranges, canonical work/tuple, every new
  arm verdict, all durable function outcomes, predecessor-chain result, Y5 release
  amendment/new-root prerequisite, legacy limitations, attribution as claim, and
  remaining boundaries. Preserve review/rerun rulings and any deferred findings.
  Claim success only from observed completed command output.
- [ ] Add cut 46 to `ACCOUNTING` as full Y5/Y17/Y18 and remove Y5's REOPENED entry
  only at successful discharge. Regenerate totals (expected 226/253, open 27).
  Update current-facing publication design, contracts/adoption guide, README,
  ledger, roadmap and spec/plan status together. Keep old v1/v2 release docs and
  frozen evidence exact; record the new amendment adjacent to current-facing
  claims, not by rewriting historical cut bodies.
- [ ] Run focused document guards and recent-runner checks, `just check`,
  `just test-fast`, `tasks check`; resolve errors and non-environmental warnings.
  Close all completed children and parent via CLI with the precise outcome, then
  commit `docs(cut): record publication attribution discharge` including task
  closure. Check clean status, record final commit, and run `host-load --section
  session`; reap only processes this task launched. Retain the worktree for review.
- [ ] Only after this slice is closed, select the authorized bounded preflight
  pilot `beliefs-aa9f88` using its own task process and trial arm. No integration
  or external writes are inferred from completion.

## Plan self-review and handoff

Spec §§1–4 map to Tasks 0/1; §5 to Tasks 3/4/5; §§6–7 to Tasks 2/4/5;
§8 to the 36-unit matrix and Tasks 5–7; §9 to the constraints and discharge
documentation. All five Review Focus cases have owning tests. The pinned-boundary
inventory explicitly includes stage, audit, arrival, tip, source and remote;
shape-only `coordination.tips_at`, layout, factory and consistency are deliberate.

The user accepted this plan on 2026-10-02; the author approves the revised spec
and plan. Task 0 starts with the cut-number recheck. Review notes are included
in Tasks 4/5; product implementation follows the freeze.
