# Live View-Query Evaluation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `evaluate_live_query(world, query) -> LiveSelection`, which denotes a view query over every admitted corpus's current state with no epoch, stamped by the states it captured, and discharge its five guarantees as conformance cut 41.

**Architecture:** `world/selection.py`'s denotation is lifted into a private core, `_denoted(view, query)`, typed over a private protocol that `WorldReadView` and a new private live capture both satisfy. `evaluate_query` keeps its entry checks and calls the core. A new `world/live.py` resolves coverage from the registry, captures each present corpus inside its own operation-lock hold, derives the address map with publish's `derive.address_map`, runs the core, and returns a `LiveSelection` carrying a `CaptureStamp`. `corpus.py` gains one structural protocol so `RelationAdjacency` accepts the live capture, and `WorldReadView` gains one private method.

**Tech Stack:** Python 3.11+ under `uv`, pytest, the `nodes` records, the certified `atoms` engine behind `root.py` (reached here only through the acceptance fixtures), the acceptance harness under `python/tests/acceptance/`, and the N2 audit.

**Spec:** `docs/designs/2026-09-24-live-query-evaluation-design.md`, approved 2026-09-24 at `d67359e` after two user reviews, amended 2026-09-25 at this plan's review (cut 41, prefix cut 40; Z2-b observes enumeration). Task 0 moved it there from `docs/superpowers/specs/` as table Z's owner (the cut 31 and cut 32 precedent for a new table); every later task reads it there. Read it first; every task cites its decisions (§2) and sections.

## Global Constraints

- **Baseline is `main` at `a79fb5a`**, merged into the branch at `ce8e46e` before Task 0 (the design forked at `f3a02fe`; the merge brought `beliefs-3ce305`'s cut-42 title and the task-note history). Work in `.worktrees/live-query` (branch `design/live-query`, locked "on WORK_ROOT storage"). Paths below are relative to the repository root; paths shown to the user carry the `.worktrees/live-query/` prefix. The main checkout is `~/d/beliefs`.
- **The fast loop.** From the worktree root: `SCIENCE_CUT13_ROOT=$(readlink -f ~/d/beliefs)/.lifecycle-wrappers-test just test-fast` (`beliefs-ad68df`). For one module: `cd python && SCIENCE_CUT13_ROOT=$(readlink -f ~/d/beliefs)/.lifecycle-wrappers-test uv run --frozen pytest tests/<module> -q`. About 216 `CapabilityUnavailable` failures mean the export is missing, not a bug.
- **Acceptance and N2 run from the worktree, under overrides onto the main checkout's certified volume — not after a fast-forward.** The worktree sits on WORK_ROOT storage, which the durability allowlist refuses, and acceptance fixtures whose roots are repo-relative fail there. Before any acceptance or N2 run:

  ```bash
  cd ~/d/beliefs/.worktrees/live-query/python && cd "$(pwd -P)"
  for n in $(seq 4 41); do export SCIENCE_CUT${n}_ROOT=$(readlink -f ~/d/beliefs)/.work/acceptance/cut$n; done
  export SCIENCE_CUT13_ROOT=$(readlink -f ~/d/beliefs)/.lifecycle-wrappers-test
  ```

  `SCIENCE_CUT4_ROOT` is acceptance's `work_directory`. Run pytest from the canonical path (`cd "$(pwd -P)"`): `ELOOP` from `open_root` means the `.worktrees` symlink is in the cwd. The cut runner resolves its own default work under the main checkout (`MAIN_CHECKOUT` in `cut40_acceptance.py`).
- AGENTS.md, Cut plans, verbatim: **`root.py` is the one `atoms` importer** (`test_capability_boundary.py`,
  `TestTheCompositionRootIsTheOneAtomsImporter`). A classification over engine
  cause types, a predicate over engine exceptions, or any other engine-typed
  behaviour lives in `root.py` and reaches its boundary through a seam callable
  (cut 35's `StoreActSeam.store_refusal`, `b065711`), never as an import in the
  boundary module. Every new caller of a write primitive joins
  `WRITE_ENTRY_POINTS` in `test_permit_boundary.py` and gains a `Case` in
  `test_permit_entry_points.py`'s `CASES`; the inventory is closed in both
  directions.
  - For this lane: `world/live.py` imports nothing of `atoms`, and it calls no write primitive, so `WRITE_ENTRY_POINTS` and `CASES` do not change. Tasks 1 and 3 run `test_capability_boundary.py`, `test_permit_boundary.py` and `test_permit_entry_points.py` green to prove both.
- AGENTS.md, Cut plans, verbatim: **Every discharged cut adds its row to `test_recent_cut_acceptance.py`**: the
  runner import, its `(runner, cut, accounting)` parametrization entry with the
  declared-arm, declaration-unit and guarantee-row counts, and the cut's
  guarantee-rows-exercised line. Cuts 33, 34 and 35 landed theirs at `f4c2cef`,
  `c77b2aa` and after cut 35's final review; the plan's runner task owns the row. Here that is Task 5, Step 4, with `(cut41, 41, (12, 12, 5))`.
- **The declared accounting is 12 arms, 12 declaration units, 5 rows (Z1–Z5).** Every later mention reads the frozen cut document's §4.
- **Frozen declarations and cut bodies stay byte-exact.** Cut 28's live arms pin these `world/selection.py` spellings, and each must occur **exactly once** after Task 1:
  - `if view.damaged():` (W7-a), `if moved:` (W7-b), `    if type(view) is not WorldReadView:` (W7-o);
  - `    if unknown:\n        raise SelectionRefused("address-unknown", refs=unknown)` (W7-c);
  - the four-line `raise SelectionRefused(\n            "address-not-present", …)` block (W7-d);
  - `            members = denoted if members is None else members & denoted\n        selected |= members or set()` (W7-e);
  - `        return set(reach.reached)` (W7-f) and `        reach = closure(live, _QueryAdjacency(view, predicate.predicates, predicate.direction))` (W7-g);
  - `_InboundAdjacency.steps`' nine-line `if edge.source_uid is None:` block (W7-h);
  - `"unresolved": [step.projection() for step in self.unresolved],` (W7-i) and `"absent": list(self.absent),` (W7-j), both in `Selection.projection`;
  - `    for address in selected:\n        validated_node(held[address][1])` (W7-k);
  - `_binds_term`'s first two lines (W7-l), `    return term in args or term in restrictions` (W7-m), and `        raise SelectionRefused("record-malformed", refs=[node.id]) from None` (W7-n).

  Cuts 23 and 27 pin `world/view.py`'s `locate`, `get`, `inbound` and `open_world_view` lines, and cut 4 pins `RelationAdjacency(self._view, stored.TRANSFORMS, "outbound")` in `corpus.py`. Task 1 adds beside them and edits none of them. Tasks 1 and 3 end with `tests/test_arm_staleness.py`. A stale prior arm means an edit moved a pinned line: restore its spelling and put the new code beside it. Never edit a prior declaration.
- **Decisions the code must honour verbatim** (spec §2):
  1. one function, `evaluate_live_query(world, query) -> LiveSelection`, and no public live view;
  2. `LiveSelection` and `CaptureStamp(world_id, coverage)` are their own sealed types; the projection is versioned `science.live-selection.v1` and carries `capture` where `Selection` carries `epoch`; `Unresolved` is shared;
  3. coverage is the registry's admitted, non-terminal set (`registry._live_corpus_ids`); an unreadable manifest or a duplicate carrier refuses `ResolutionRefused` with `open_world_view`'s messages; absent corpora are listed;
  4. an address in an absent corpus is `unknown`; `address-not-present` is never raised on this path;
  5. each present corpus is captured inside its own `capture()` hold, serially, in sorted order; a moved state raises `CaptureDrift`, with no retry;
  6. the address map is `derive.address_map` over the captured world-kind records (`stored.WORLD_KINDS`);
  7. `AddressMapConflict` propagates unchanged (`uid-corruption` before `duplicate-location`); the scoped W8b check runs only after the map succeeds and only over uids a record outside the map holds;
  8. damage (`CorpusStateMalformed`, `ContractMismatch`) is collected and refuses `corpus-damaged` naming every damaged corpus; `corpus-drifted` is never raised here;
  9. the denotation is shared, not copied;
  10. cut 41 is the focused cut, and cut 28 stays as it is.
- **The lane.** The boundary id is `live-query`, its own lane, opened off the dogfood path under roadmap rule 6. Its shared surface is `world/selection.py` and `world/live.py`. Under rule 3 it names two files the `world-read` lane (`publish`, planned cut 42) also lists: `world/view.py`, which gains one private method and one type alias, and `corpus.py`, which gains one protocol and one annotation. The later merge resolves toward the earlier one. The lane amends no contract oracle, so `contract-cut` gains no dependency.
- **Detached runs go through the reaping wrapper** (Processes rule). Launch the cut runner and the gate with `setsid nohup ~/d/beliefs/.work/acceptance/detached.sh <log> <cmd…> > /dev/null 2>&1 &`, after `test -x` on the wrapper. An end-of-turn report that leaves one running names its process group (`cat <log>.pid`) and the stop command (`kill -TERM -- "-$(cat <log>.pid)"`), after `host-load --section session`.
- **Commits:**
  - Use conventional commits, with no attribution trailers.
  - Run `tasks check` before every commit.
  - Use `just test-fast` while working. Never run the full suite after every edit (AGENTS.md).
  - Run every `pytest` from `python/` with `uv run --frozen`.
  - Make no TypeScript changes, and leave both `CONTRACT.yaml` copies unchanged.

## Review Focus

These are the inputs a person meets that the spec's tests do not pin. Each names the test that pins it and the task that owns it.

1. **A query naming a retired address of a live record.** The live address map carries every `deprecated_ids` entry, exactly as publish's does, so the retired address resolves to the live record rather than refusing `address-unknown`. Pinned by `test_a_retired_address_resolves_to_its_live_record` in Task 3.
2. **A world with nothing admitted.** The evaluation returns an empty, complete selection with an empty coverage, and never refuses. Pinned by `test_a_world_with_nothing_admitted_selects_nothing_and_is_complete` in Task 3.
3. **An admitted corpus holding only coordination records**, as a fresh working corpus does before its first world record. It is captured and stamped, and it contributes nothing. Pinned by `test_a_corpus_holding_only_coordination_records_is_captured_and_contributes_nothing` in Task 3.
4. **A configured root whose manifest cannot be read.** It refuses `ResolutionRefused` with `open_world_view`'s message, never reading as an absence. Pinned by `test_a_configured_root_with_an_unreadable_manifest_refuses` in Task 3.
5. **Repeated evaluation.** Two evaluations over an unchanged world answer the same identity, and a write moves only the written corpus's stamp entry. Pinned by `test_an_unchanged_world_answers_identically_and_a_write_moves_only_its_corpus` in Task 3.

---

## File map

| File | Responsibility |
| --- | --- |
| `docs/designs/2026-09-24-live-query-evaluation-design.md` (moved from `docs/superpowers/specs/`) | the design, owner of table Z (Task 0); status and planning notes |
| `docs/designs/<freeze date>-conformance-cut-41.md` (new), `README.md`, `docs/guide/contracts-and-adoption.md`, `python/tests/test_designs_corpus.py` | freeze and totals (Task 0) |
| `python/src/beliefs/corpus.py` | `RelationView` protocol; `RelationAdjacency` typed over it (Task 1) |
| `python/src/beliefs/world/view.py` | `LocatedState`; `WorldReadView._located_state` (Task 1) |
| `python/src/beliefs/world/selection.py` | `_QueryableView`, `_Denotation`, `_denoted`; helpers typed over the protocol (Task 1) |
| `python/tests/test_world_selection.py` | `TestLocatedState` (Task 1) |
| `python/src/beliefs/world/live.py` (new) | `CaptureStamp`, `LiveSelection` (Task 2); `evaluate_live_query` and its private capture (Task 3) |
| `python/tests/test_live_selection.py` (new) | portable tests (Tasks 2 and 3) |
| `python/tests/acceptance/test_live_selection_acceptance.py` (new) | the twelve units and the module's other tests (Task 4) |
| `python/tests/n2_arms_cut41.py`, `python/tests/acceptance/n2_arms_cut41.py`, `python/tests/acceptance/test_n2_cut41.py`, `python/tools/cut41_acceptance.py` (new); `python/tests/test_recent_cut_acceptance.py` | declaration, guard, runner, recent-cut row (Task 5) |
| `docs/designs/2026-09-05-mm30-reproduction.md` | the next addendum (Task 6) |
| `docs/plans/<date>-conformance-cut-41-results.md` (new), `docs/designs/2026-08-31-coordination-and-view-kinds-design.md`, the ledger, the roadmap, `python/tools/roadmap_status.py` | discharge (Task 8) |

---

### Task 0: Freeze cut 41, bank Z1–Z5, audit the arms on paper

A cut is frozen before its code exists (roadmap, Concurrency rules), so the twelve arms cannot be executed at the freeze. This task audits each arm against its unit on paper instead. The executable audit is Task 5 Step 5, and an arm that fails it there is rehomed in a dated §8 supplement to the cut document, never dropped.

**Files:**
- Create: `docs/designs/<freeze date>-conformance-cut-41.md`
- Move: `docs/superpowers/specs/2026-09-24-live-query-evaluation-design.md` → `docs/designs/2026-09-24-live-query-evaluation-design.md`
- Modify: `python/tests/test_designs_corpus.py`, `README.md`, `docs/guide/contracts-and-adoption.md`, this plan (its **Spec** line), tasks through the CLI
- Modify (Step 1's relabel of the remote slice to planned cut 42): `docs/designs/2026-08-03-redesign-adoption-ledger.md`, `docs/plans/2026-08-29-implementation-roadmap.md`, `docs/guide/open-questions.md`, `docs/designs/2026-09-22-publication-design.md`, `python/src/beliefs/publish.py`

**Interfaces:**
- Produces: the frozen cut body and its digest (Task 5 pins them); the prefix decision (`PREFIX_RUNNERS`) that Task 5 writes.

- [ ] **Step 1: Recheck the number, claim cut 41, and relabel the remote slice**

The user decided on 2026-09-25: this cut is **cut 41**, and `PREFIX_RUNNERS = ("cut40_acceptance.py",)`, since cut 40's is the highest-numbered runner (rule 5). Cut 40 is discharged, so the discharge waits on nothing. The remote publish slice (`beliefs-3ce305`), which prose had reserved as cut 41, becomes **planned cut 42**. The decision stands only while no cut-41 document exists, so recheck that at the freeze:

```bash
cd ~/d/beliefs
for b in $(git for-each-ref --format='%(refname:short)' refs/heads); do git ls-tree -r --name-only "$b" docs/designs | grep -E "conformance-cut-4[1-9]" | sed "s|^|$b: |"; done; echo scan done
ls docs/plans | grep -E "conformance-cut-4[1-9]-results"; ls python/tools | grep -E "cut4[1-9]_acceptance"; git worktree list
```

Expected: `scan done` and nothing else from the three listings, so no branch holds a cut-41-or-later document, results record or runner. If anything else is listed, stop: `tasks note beliefs-cc0aea` the scan output, and `tasks park beliefs-cc0aea "cut 41 was claimed before this freeze; the number and prefix need a new decision" --waiting-on user --reason decision`.

Then relabel remote publish's **current** references to planned cut 42, in this freeze commit. Rule 1 claims the number at the freeze, so the claim and the relabel land together. The exact edits:
- `docs/designs/2026-08-03-redesign-adoption-ledger.md`: the `Updated 2026-09-24` paragraph, the **Y5–Y10 close** bullet, the `publish` row of the open-boundary table, the paragraph after that table, and the `publish remains open …` sentence: each "cut 41" that names the remote slice → "cut 42".
- `docs/plans/2026-08-29-implementation-roadmap.md`: the `world-read` head sentence, the lane table's `world-read` row ("its third, the remote slice (cut 41), is next"), the boundary index's `publish` row, the off-path tier table's row 1, and "Cut 41's remote slice appends its own rows" → cut 42.
- `README.md` ("stays open with cut 41's remote slice"), `docs/guide/contracts-and-adoption.md` (same phrase), `docs/guide/open-questions.md` ("work for cut 41"), `docs/designs/2026-09-22-publication-design.md` ("the remote slice, cut 41,") → cut 42.
- `python/src/beliefs/publish.py`: `ValidationRefused("remote destinations arrive in cut 41")` → `"… in cut 42"`. No test or arm pins the text (`git grep -n "arrive in cut" -- python/tests` finds nothing); rerun `git grep` to confirm first.
- `tasks edit beliefs-3ce305 --title "The publish act, remote: transport seam, remote reveal and orphans, divergent-publication (cut 42)"`, plus `tasks note beliefs-3ce305 "renumbered cut 41 → 42 on <date>: live view-query evaluation froze as cut 41 (beliefs-cc0aea), by the user's decision of 2026-09-25"`. The title was changed on `main` on 2026-09-25, when the user decided: confirm it reads so and skip the edit.

Historical text stays byte-exact: cut 40's frozen document and results record, the publish-act-local spec and plan, the dated amendments in the user-and-autonomy layer design, and task notes. Each of those records what was true when it was written. Afterwards, `git grep -n "cut 41" -- README.md docs/designs/2026-08-03-redesign-adoption-ledger.md docs/plans/2026-08-29-implementation-roadmap.md docs/guide docs/designs/2026-09-22-publication-design.md python/src` should list only lines about this cut.

- [ ] **Step 2: Audit every arm on paper.** For each row, confirm against the Task 3 code and the Task 4 test that the check observes what the sabotage changes. If a row does not hold, change the unit's test (never the frozen text) before Step 5, and record why in the spec's planning notes.

| unit | the check asserts | the sabotage | why the check sees it |
| --- | --- | --- | --- |
| Z1-a | both corpora's datasets selected; coverage is exactly both | the capture loop skips the last covered corpus | one dataset, one contributing corpus and one coverage pair go missing |
| Z1-b | the retired corpus's dataset is never selected and never stamped | the terminal filter is dropped | the retired carrier is present, so it would be captured and its dataset selected |
| Z1-c | `absent == (b,)` and `complete` is false | absent corpora are dropped from `absent` | `absent` becomes `()` and `complete` true |
| Z1-d | a never-published world evaluates; a corpus admitted after the epoch is covered | coverage is filtered by the current epoch | `current_epoch` raises `EpochUnknown` on the first call; on the second, B is filtered out |
| Z2-a | a state moving inside the hold raises `CaptureDrift` | the before/after comparison is dropped | the evaluation returns instead of raising |
| Z2-b | every state read, open, and record yielded by `iter_stored` for the carrier sees holder `"capture"` (read as the iterator is consumed); a held writer lock refuses `BuildContended` | the hold is bypassed, the comparison kept | the holder is `None` at every call and every yield, and no `BuildContended` is raised |
| Z3-a | the stamp names the first corpus's in-hold state; the late record is unselected | the stamp re-reads state after all captures | the re-read sees the late record's state, which differs from the in-hold one |
| Z4-a | a malformed corpus refuses `corpus-damaged` naming it | a construction failure omits the corpus | a selection returns without the corpus |
| Z4-b | a foreign base pin refuses `corpus-damaged` naming it | the base-pin check is skipped | the corpus is read as healthy and a selection returns |
| Z5-a | a shared-uid duplicate location raises `AddressMapConflict("duplicate-location")` | an every-record uid check runs before the map | the shared uid trips it, so `ResolutionRefused` is raised instead |
| Z5-b | uid corruption raises `AddressMapConflict("uid-corruption")` over a duplicate location | one record is kept per uid before the map | both conflicts vanish, and the evaluation returns |
| Z5-c | a uid a coordination record shares with a world record refuses `ResolutionRefused` | the scoped check is dropped | the evaluation returns |

- [ ] **Step 3: Move the design and bank Z1–Z5**

```bash
cd ~/d/beliefs/.worktrees/live-query
git mv docs/superpowers/specs/2026-09-24-live-query-evaluation-design.md docs/designs/2026-09-24-live-query-evaluation-design.md
tasks edit beliefs-cc0aea --spec docs/designs/2026-09-24-live-query-evaluation-design.md
```

In the moved design:
- bold the five row ids in §6.3's row table (`| **Z1** |` … `| **Z5** |`), the form every banked table uses;
- set its Status line to `**Status:** approved 2026-09-24 after two user reviews, amended 2026-09-25; frozen as conformance cut 41 on <date>; implementation not yet started. **Task:** \`beliefs-cc0aea\`.`;
- append `## 8. Planning notes`, holding exactly these bullets:

```markdown
- 2026-09-24 — at planning (plan `../superpowers/plans/2026-09-24-live-query-evaluation.md`):
  - **Table Z's owner is this design**, moved into `docs/designs/` at the
    freeze as estimand typing (cut 31) and composite claims (cut 32) were for
    their new tables.
  - **`LocatedState`** (`Literal["resolved", "not-present", "unknown"]`) lives
    in `world/view.py`, beside `WorldReadView._located_state`, because
    `selection.py` already imports `view.py` and the reverse would cycle.
  - **`RelationAdjacency` is typed over a structural `RelationView` protocol**
    in `corpus.py` (`get`, `resolve`, `inbound`, `live_id`), which `ReadView`,
    `WorldReadView` and the live capture all satisfy. Nothing it reads changes.
  - **The live capture is private** (`live._LiveCapture`); `_denoted` returns a
    private `_Denotation(selected, contributing, unresolved)`.
  - **The damage and conflict refusals keep their exception types**:
    `SelectionRefused("corpus-damaged")`, `AddressMapConflict`,
    `ResolutionRefused`, `CaptureDrift`, and `BuildContended` from `capture()`.
    No new error class is added.
  - **`live.py` repeats `open_world_view`'s coverage block, capture loop, W8b
    message and inbound-edge construction instead of sharing them.** The
    repeated `view.py` lines are pinned by live arms (cut 23's W10d, W10e and
    W10g; cut 27's S9-a), and cut 41's arms need single-site targets in
    `live.py`. The two identical `except` branches in `_capture` and the
    per-corpus filter in `_address_map` stay separate for the same reason:
    Z4-a and Z5-b each need one site. A later de-duplication re-targets those
    arms through the guards' `_LIVE_SABOTAGES`, and is out of this cut.
  - **`evaluate_live_query` checks `type(world) is registry.World` and
    `isinstance(query, ViewQuery)`**, as `evaluate_query` does; "a parsed
    `ViewQuery`" (§3.1) is read as an instance.
  - **Z1-d's and Z3-a's sabotages are stated as implemented** in §6.3: Z1-d
    filters the registry's coverage by the current epoch's coverage, and Z3-a
    re-reads each covered corpus's state when the stamp is built.
  - **The twelve arms were audited on paper at the freeze** (plan Task 0 Step
    2); the executable audit is plan Task 5, and an arm that fails it is
    rehomed in a dated §8 supplement to the cut document.
```

In `python/tests/test_designs_corpus.py`:
- add `"Z": tuple(f"Z{n}" for n in range(1, 6)),` as the last `GUARANTEE_TABLES` entry, and `"Z": "2026-09-24-live-query-evaluation-design.md",` as the last `TABLE_OWNERS` entry;
- add `Z` to the letter class in `_ROW`, `_ROW_RANGE` and `_PROSE_LABEL` (`[GSWRCXNLDMPHTEFJVBQUYZ]` in each);
- extend `table_words` with `22: "twenty-two"`;
- extend `_COUNT_WORDS` with `79: "Seventy-nine"` and `80: "Eighty"`.

Totals: compute rather than assume, since another design may land first:

```bash
cd python && uv run --frozen python -c "
import importlib.util, pathlib
s = importlib.util.spec_from_file_location('c', 'tests/test_designs_corpus.py'); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
print(sum(map(len, m.GUARANTEE_TABLES.values())), 'rows', len(m.GUARANTEE_TABLES), 'tables', len(m.design_documents()), 'designs')"
```
Expected today: `231 rows 22 tables 79 designs` (80 after Step 4). Update:
- `README.md`: "**231 rows** across **twenty-two frozen tables**", the design-count word ("Eighty documents"), its "through <newest design date>", and two design-table rows: the moved design (`the live attention read: a view query denoted over every admitted corpus's current state, stamped by its capture; table Z`) and the cut document (Step 4);
- `docs/guide/contracts-and-adoption.md`: its rows-and-tables sentence and totals line, and the frozen-not-discharged cut paragraph, on cut 40's shape. That paragraph cites both new filenames (the moved design and the cut document): `test_the_guide_cites_every_design` requires every design to be cited on a guide page.

- [ ] **Step 4: Write the cut document.** Read `sed -n 1,190p docs/designs/2026-09-24-conformance-cut-40.md` first and keep its headings exactly (`## 1. What this cut is` … `## 7. Limitations`): the guard slices §§2–7 from `## 2. The boundary` to the first `\n## 8.`. Header:

```markdown
# Conformance cut 41 — live view-query evaluation

**Status:** frozen <date>, before implementation; Z1–Z5 are open
**Design:** `2026-09-24-live-query-evaluation-design.md`, approved 2026-09-24 at `d67359e` after two user reviews, amended 2026-09-25 at the plan review; implementation not yet started.
**Plan:** `../superpowers/plans/2026-09-24-live-query-evaluation.md`.
**Numbered** under roadmap concurrency rules 1 and 5: cut 41 by the user's decision of 2026-09-25, prefixing cut 40; the remote publish slice (`beliefs-3ce305`) is relabelled planned cut 42 in this commit. <Step 1's scan result>.
```

Sections:
- **§1:** design §1 condensed; the `live-query` lane opened off the path under rule 6; the rule-3 overlaps (`world/view.py`, `corpus.py`); no oracle amended, so `contract-cut` gains no dependency.
- **§2, the boundary:** every file in this plan's file map from Task 1 to Task 5, then "Frozen declarations and cut bodies through cut 40 remain byte-exact; cut 28's W7 arms keep applying exactly once."
- **§3, selection:** the five Z rows copied from the design's §6.3, then its §6.2 unit table (twelve rows, Z1-a to Z5-c).
- **§4, accounting:** "**12 arms, 12 declaration units**, five rows; Z1–Z5 open and close; recent-cut row `(12, 12, 5)`; `<closed>` of 231 → `<closed + 5>` of 231". Take `<closed>` from `cd python && uv run --frozen python tools/roadmap_status.py | tail -1`.
- **§5, N2 and acceptance obligations:** the sabotage table from Task 5 Step 1, `PREFIX_RUNNERS` as Step 1 decided (write the tuple literally), and `PHASE_MODULES = ("test_live_selection_acceptance.py", "test_n2_cut41.py")`.
- **§6, second reader:** check that Z2-b observes the holder at every state read, every open, and every record `iter_stored` yields for the carrier, not just one, and that the enumeration check reads the holder during consumption, not at generator creation; that Z3-a's write lands after the first corpus's hold is released and before the evaluation returns; that Z5-a's duplicate shares its uid; and that no arm touches `world/selection.py`.
- **§7, limitations:** coherence is per corpus, with no cross-corpus snapshot (decision 5); an absent corpus's addresses are unknown to a live read (decision 4); a live selection is attention, never belief input (§5's amendment).

- [ ] **Step 5: Verify and commit the freeze**

```bash
cd python && uv run --frozen pytest tests/test_designs_corpus.py tests/test_check_guide.py -q
```
Expected: pass. If the cross-reference guard flags a science filename the moved design cites (`2026-09-24-coordination-command-set-design.md`), add it to `EXTERNAL_DOCUMENTS` with a comment naming the science repository, as the `nodes` entries do.

Point this plan's **Spec** line at `docs/designs/2026-09-24-live-query-evaluation-design.md`, then:

```bash
cd .. && tasks note beliefs-cc0aea "Cut 41 frozen: <case>; accounting 12/12/5; prefix <runner>."
tasks done beliefs-09a5c4 "cut 41 frozen; Z1–Z5 banked; arms audited on paper"
tasks check && git add docs README.md python/tests/test_designs_corpus.py python/src/beliefs/publish.py tasks
git commit -m "docs(cut): freeze conformance cut 41, live view-query evaluation; bank Z1–Z5"
git rev-parse HEAD; sha256sum docs/designs/*-conformance-cut-41.md
```
Record the hash as `CUT41_FREEZE_COMMIT` and the digest as `CUT41_FROZEN_SHA256`, both for Task 5.

The plan's step children, filed with the plan, each depending on its predecessor:
- Task 0 `beliefs-09a5c4`, Task 1 `beliefs-462b32`, Task 2 `beliefs-bfe541` (low), Task 3 `beliefs-efe56e`;
- Task 4 `beliefs-b5adc3` (high), Task 5 `beliefs-05590f`, Task 6 `beliefs-a4f6a5` (low), Task 7 `beliefs-63500c`, Task 8 `beliefs-23f3d1`.

`tasks start` each child before its task, and `tasks done` it in that task's commit. Every `<Task N's id>` in this plan is its id from this list. Task 0's own commit carries `tasks done beliefs-09a5c4`.

---

### Task 1: The shared denotation core

**Files:**
- Modify: `python/src/beliefs/corpus.py` (beside `RelationAdjacency`, line ~856), `python/src/beliefs/world/view.py`, `python/src/beliefs/world/selection.py`
- Test: `python/tests/test_world_selection.py`

**Interfaces:**
- Produces:
  - `beliefs.corpus.RelationView` (Protocol: `get(ref) -> Node`, `resolve(ref) -> str | None`, `inbound(ref) -> list[ResolvedEdge]`, `live_id(uid) -> str`);
  - `beliefs.world.view.LocatedState = Literal["resolved", "not-present", "unknown"]`;
  - `WorldReadView._located_state(ref: str) -> LocatedState`;
  - `beliefs.world.selection._QueryableView` (Protocol: `_located_state`, `corpus_of`, `resolve`, `get`, `inbound`, `live_id`, `_mapped_records`);
  - `beliefs.world.selection._Denotation(selected: tuple[str, ...], contributing: tuple[str, ...], unresolved: tuple[Unresolved, ...])`;
  - `beliefs.world.selection._denoted(view: _QueryableView, query: ViewQuery) -> _Denotation`.

- [ ] **Step 1: Write the failing test.** Append to `python/tests/test_world_selection.py`:

```python
class TestLocatedState:
    """The evaluator reads `locate` as three states (live-query design decision 9)."""

    def test_the_three_states_follow_locate(self, tmp_path):
        world, roots, published, _topic = topic_world(tmp_path, [{"kinds": ["dataset"]}])
        view = open_world_view(world, published)
        assert view._located_state(dataset_ref("d-b")) == "resolved"
        assert view._located_state("dataset:never") == "unknown"
        make_absent(roots, BETA)
        assert open_world_view(world, published)._located_state(dataset_ref("d-b")) == "not-present"

```

- [ ] **Step 2: Run it to see it fail**

Run: `cd python && SCIENCE_CUT13_ROOT=$(readlink -f ~/d/beliefs)/.lifecycle-wrappers-test uv run --frozen pytest tests/test_world_selection.py::TestLocatedState -q`
Expected: FAIL — `AttributeError: 'WorldReadView' object has no attribute '_located_state'`.

- [ ] **Step 3: `corpus.py`.** Directly above `class RelationAdjacency:` add:

```python
class RelationView(Protocol):
    """What a relation adjacency reads of a view. `ReadView`, `WorldReadView`
    and the live capture behind `world.live` all satisfy it structurally."""

    def get(self, ref: str) -> Node: ...

    def resolve(self, ref: str) -> str | None: ...

    def inbound(self, ref: str) -> list[ResolvedEdge]: ...

    def live_id(self, uid: str) -> str: ...
```

and change only `RelationAdjacency.__init__`'s annotation:

```python
    def __init__(self, view: RelationView, predicate: str, direction: str) -> None:
```

(`Protocol`, `Node` and `ResolvedEdge` are already imported in `corpus.py`.)

- [ ] **Step 4: `world/view.py`.** After `_MINT = object()` add:

```python
LocatedState = Literal["resolved", "not-present", "unknown"]
"""`locate`'s answer as the three states the query evaluator reads (live-query design decision 9)."""
```

and in `WorldReadView`, directly after `locate`:

```python
    def _located_state(self, ref: str) -> LocatedState:
        """`locate`'s answer as the evaluator's three states; damage refuses
        exactly as `locate` refuses it."""
        located = self.locate(ref)
        if type(located) is Unknown:
            return "unknown"
        if type(located) is NotPresent:
            return "not-present"
        return "resolved"
```

- [ ] **Step 5: `world/selection.py`.** Make exactly these edits and nothing else.

Imports: replace the `collections.abc`, `dataclasses`, `typing`, `nodes`, `read` and `view` import lines with

```python
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from typing import Literal, Protocol, final

from nodes.core.node import Node
from nodes.core.structural_index import ResolvedEdge
```

and

```python
from beliefs.world.read import BoundStamp
from beliefs.world.view import LocatedState, WorldReadView
```

(`NotPresent` and `Unknown` are no longer used here.)

After the `Held = …` alias and its docstring, add:

```python
class _QueryableView(Protocol):
    """What the denotation reads of a capture: a `WorldReadView` at an epoch,
    or `live._LiveCapture` over the current state (live-query design
    decision 9). Both satisfy it structurally; neither names it."""

    def _located_state(self, ref: str) -> LocatedState: ...

    def corpus_of(self, ref: str) -> str | None: ...

    def resolve(self, ref: str) -> str | None: ...

    def get(self, ref: str) -> Node: ...

    def inbound(self, ref: str) -> list[ResolvedEdge]: ...

    def live_id(self, uid: str) -> str: ...

    def _mapped_records(self) -> Iterator[tuple[str, Node]]: ...
```

Change the two adjacency constructors' annotations only:

```python
    def __init__(self, view: _QueryableView, predicate: str) -> None:
```

```python
    def __init__(self, view: _QueryableView, predicates: tuple[str, ...], direction: str) -> None:
```

Replace `_classify` whole:

```python
def _classify(view: _QueryableView, entry: RelationEntry) -> Unresolved:
    state = view._located_state(entry.target)
    if state == "not-present":
        corpus_id = view.corpus_of(entry.target)
        assert corpus_id is not None
        return Unresolved(entry.source, entry.predicate, entry.target, "not-present", corpus_id)
    assert state == "unknown", entry
    return Unresolved(entry.source, entry.predicate, entry.target, "unknown", None)
```

In `evaluate_query`, keep every line through the drift refusal, then replace everything from `    _require_located(view, query.addresses())` to the end of the function with:

```python
    denoted = _denoted(view, query)
    return Selection(
        stamp=view.stamp,
        query=query,
        selected=denoted.selected,
        contributing=denoted.contributing,
        absent=view.absent(),
        unresolved=denoted.unresolved,
    )


@final
@dataclass(frozen=True)
class _Denotation:
    """The part of an answer the capture determines and the stamp does not."""

    selected: tuple[str, ...]
    contributing: tuple[str, ...]
    unresolved: tuple[Unresolved, ...]


def _denoted(view: _QueryableView, query: ViewQuery) -> _Denotation:
    """The one denotation both entry points run (§3.2): every named address
    located first, then each clause the intersection of its predicates and
    the answer the union of its clauses."""
    _require_located(view, query.addresses())

    held: dict[str, tuple[str, Node]] = {node.id: (corpus_id, node) for corpus_id, node in view._mapped_records()}
    unresolved: dict[tuple[str, str, str], Unresolved] = {}
    selected: set[str] = set()
    for clause in query.clauses:
        members: set[str] | None = None
        for predicate in clause.predicates:
            denoted = _denote(view, predicate, held, unresolved)
            members = denoted if members is None else members & denoted
        selected |= members or set()

    for address in selected:
        validated_node(held[address][1])
    contributing = sorted({held[address][0] for address in selected})
    return _Denotation(
        selected=tuple(sorted(selected)),
        contributing=tuple(contributing),
        unresolved=tuple(sorted(unresolved.values(), key=lambda step: step.sort_key)),
    )
```

In `_require_located`, change the annotation to `view: _QueryableView` and replace only the loop body:

```python
    for address in addresses:
        state = view._located_state(address)
        if state == "unknown":
            unknown.append(address)
        elif state == "not-present":
            corpus_id = view.corpus_of(address)
            assert corpus_id is not None
            not_present.append((address, corpus_id))
```

In `_denote`, change only the annotation to `view: _QueryableView`.

- [ ] **Step 6: Run the tests**

```bash
cd python && export SCIENCE_CUT13_ROOT=$(readlink -f ~/d/beliefs)/.lifecycle-wrappers-test
uv run --frozen pytest tests/test_world_selection.py tests/test_world_view.py tests/test_arm_staleness.py tests/test_capability_boundary.py tests/test_permit_boundary.py tests/test_permit_entry_points.py -q
uv run --frozen ruff check src tests && uv run --frozen pyright
```
Expected: all pass, and pyright reports 0 errors. Then run slice 4's acceptance under Global Constraints' exports: `uv run --frozen pytest tests/acceptance/test_world_selection_acceptance.py -q`, expecting it to pass unmodified.

- [ ] **Step 7: Commit**

```bash
tasks done <Task 1's id> "shared denotation core; W7 spellings each once"
tasks check && git add python/src/beliefs/corpus.py python/src/beliefs/world/view.py python/src/beliefs/world/selection.py python/tests/test_world_selection.py tasks
git commit -m "refactor(world): one denotation core over a private view protocol"
```

---

### Task 2: `CaptureStamp` and `LiveSelection`

**Files:**
- Create: `python/src/beliefs/world/live.py`, `python/tests/test_live_selection.py`

**Interfaces:**
- Consumes: `beliefs.world.selection.Unresolved`, `beliefs.view_query.ViewQuery`, `beliefs.identity.v1`, `registry._require_lower_hex`.
- Produces: `LIVE_SELECTION_VERSION = "science.live-selection.v1"`; `CaptureStamp(world_id: str, coverage: tuple[tuple[str, str], ...])`; `LiveSelection(stamp, query, selected, contributing, absent, unresolved)` with `complete`, `projection()`, `identity()`.

- [ ] **Step 1: Write the failing tests.** Create `python/tests/test_live_selection.py`:

```python
"""Live view-query evaluation (live-query design §6.1 and the plan's Review Focus)."""

from __future__ import annotations

import pytest
from dataset_fixtures import dataset_ref
from test_world_build import ALPHA, BETA
from test_world_selection import query

from beliefs.identity import v1
from beliefs.world.live import LIVE_SELECTION_VERSION, CaptureStamp, LiveSelection
from beliefs.world.read import BoundStamp
from beliefs.world.selection import Selection, Unresolved

WORLD = "f" * 32
STATE = "a" * 64
DATASETS = query([{"kinds": ["dataset"]}])


def sample(**overrides) -> LiveSelection:
    fields: dict[str, object] = {
        "stamp": CaptureStamp(WORLD, ((ALPHA, STATE),)),
        "query": DATASETS,
        "selected": (dataset_ref("d-a"),),
        "contributing": (ALPHA,),
        "absent": (),
        "unresolved": (),
    }
    fields.update(overrides)
    return LiveSelection(**fields)  # type: ignore[arg-type]


class TestTypes:
    def test_a_capture_stamp_is_one_world_and_sorted_distinct_states(self):
        assert CaptureStamp(WORLD, ()).coverage == ()
        with pytest.raises(ValueError):
            CaptureStamp("not-a-world", ())
        with pytest.raises(ValueError):
            CaptureStamp(WORLD, (("b" * 32, STATE), ("a" * 32, STATE)))
        with pytest.raises(ValueError):
            CaptureStamp(WORLD, (("a" * 32, STATE), ("a" * 32, STATE)))
        with pytest.raises(ValueError):
            CaptureStamp(WORLD, (("a" * 32, "not-a-state"),))
        with pytest.raises(TypeError):
            CaptureStamp(WORLD, [("a" * 32, STATE)])  # type: ignore[arg-type]

    def test_a_live_selection_is_neither_a_selection_nor_bound(self):
        live = sample()
        assert not isinstance(live, Selection) and not isinstance(live.stamp, BoundStamp)
        projection = live.projection()
        assert set(projection) == {"version", "capture", "query", "selected", "contributing", "absent", "unresolved"}
        assert projection["version"] == LIVE_SELECTION_VERSION == "science.live-selection.v1"
        assert projection["capture"] == {"world": WORLD, "coverage": [[ALPHA, STATE]]}
        assert live.identity() == v1.digest(LIVE_SELECTION_VERSION, projection)
        assert sample(stamp=CaptureStamp(WORLD, ((ALPHA, "b" * 64),))).identity() != live.identity()

    def test_complete_follows_the_selection_rule(self):
        assert sample().complete
        assert not sample(absent=(BETA,)).complete
        assert not sample(unresolved=(Unresolved("run:r", "produces", "dataset:x", "not-present", BETA),)).complete
        assert sample(unresolved=(Unresolved("run:r", "produces", "dataset:x", "unknown", None),)).complete
```

- [ ] **Step 2: Run to see them fail**

Run: `cd python && uv run --frozen pytest tests/test_live_selection.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'beliefs.world.live'`.

- [ ] **Step 3: Create `python/src/beliefs/world/live.py`** with the types; Task 3 adds the rest of the module below them:

```python
"""Live view-query evaluation for attention reads.

Live-query design (`docs/designs/2026-09-24-live-query-evaluation-design.md`).
`evaluate_live_query` denotes a `ViewQuery` over every corpus the world admits
with no terminal status, each captured inside its own operation-lock hold, and
returns a `LiveSelection` stamped with the states it captured. It reads no
epoch, builds none and writes nothing. The denotation is `selection._denoted`,
the one `evaluate_query` runs, so the two paths differ only in what they
capture and how they stamp it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final

from beliefs.identity import v1
from beliefs.sealed import sealed
from beliefs.view_query import ViewQuery
from beliefs.world import registry
from beliefs.world.selection import Unresolved

__all__ = ["LIVE_SELECTION_VERSION", "CaptureStamp", "LiveSelection"]

LIVE_SELECTION_VERSION = "science.live-selection.v1"


@sealed
@final
@dataclass(frozen=True)
class CaptureStamp:
    """What a live answer is bound to: one world and the per-corpus states its
    capture read (decision 2). There is no packaging identity and there will
    not be one: a live selection names bytes it read, never a publication."""

    world_id: str
    coverage: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        registry._require_lower_hex(self.world_id, 32, "world_id")
        if type(self.coverage) is not tuple or any(type(pair) is not tuple or len(pair) != 2 for pair in self.coverage):
            raise TypeError("coverage must be an exact tuple of (corpus_id, corpus_state) pairs")
        for _, state in self.coverage:
            registry._require_lower_hex(state, 64, "corpus_state")
        ids = [corpus_id for corpus_id, _ in self.coverage]
        if ids != sorted(set(ids)):
            raise ValueError("coverage names each corpus once, in sorted order")


@sealed
@final
@dataclass(frozen=True)
class LiveSelection:
    """What a query denotes over one live capture (§3). It is not a
    `Selection`, so nothing typed for an epoch-bound answer accepts it."""

    stamp: CaptureStamp
    query: ViewQuery
    selected: tuple[str, ...]
    contributing: tuple[str, ...]
    absent: tuple[str, ...]
    unresolved: tuple[Unresolved, ...]

    @property
    def complete(self) -> bool:
        return not self.absent and all(step.state != "not-present" for step in self.unresolved)

    def projection(self) -> dict[str, object]:
        return {
            "version": LIVE_SELECTION_VERSION,
            "capture": {
                "world": self.stamp.world_id,
                "coverage": [[corpus_id, state] for corpus_id, state in self.stamp.coverage],
            },
            "query": self.query.projection(),
            "selected": list(self.selected),
            "contributing": list(self.contributing),
            "absent": list(self.absent),
            "unresolved": [step.projection() for step in self.unresolved],
        }

    def identity(self) -> str:
        return v1.digest(LIVE_SELECTION_VERSION, self.projection())
```

- [ ] **Step 4: Run them to pass**

Run: `cd python && uv run --frozen pytest tests/test_live_selection.py -q && uv run --frozen ruff check src tests && uv run --frozen pyright`
Expected: 3 passed, 0 errors.

- [ ] **Step 5: Commit**

```bash
tasks done <Task 2's id> "CaptureStamp and LiveSelection"
tasks check && git add python/src/beliefs/world/live.py python/tests/test_live_selection.py tasks
git commit -m "feat(world): the live selection and its capture stamp"
```

---

### Task 3: `evaluate_live_query`

**Files:**
- Modify: `python/src/beliefs/world/live.py`
- Test: `python/tests/test_live_selection.py`

**Interfaces:**
- Consumes: Task 1's `_denoted`, `_Denotation`, `LocatedState`, `RelationView`; Task 2's types; `registry._locked_barrier`, `_scan_registry`, `_live_corpus_ids`, `_reduce_status`, `_carrier_roots`, `corpus_state_identity`; `corpus._operation_lock_for`, `ReadView.opened_at`, `ReadView._require_base_pin`; `derive.Capture`, `CapturedCorpus`, `CapturedRecord`, `address_map`.
- Produces: `evaluate_live_query(world: registry.World, query: ViewQuery) -> LiveSelection`. Task 5's arms target the exact spellings below, so write them character for character.

- [ ] **Step 1: Write the failing tests.** Add to the imports of `python/tests/test_live_selection.py`, merging each line into the module's existing import from the same module and keeping the groups sorted (ruff's I001 is on):

```python
from coordination_fixtures import raw_coordination_node
from dataset_fixtures import pinned
from fixtures_cut4 import raw_write
from test_world_receipts import corpora, world_over
from test_world_selection import PROJECT

from beliefs import stored
from beliefs.errors import ResolutionRefused
from beliefs.world import registry
from beliefs.world.live import evaluate_live_query
```

and append:

```python
def datasets(*slugs):
    return tuple(stored.dataset_node(title=slug, resources=pinned(slug)) for slug in slugs)


def two_corpora(tmp_path, alpha=(), beta=()):
    roots = corpora(tmp_path, {ALPHA: (*datasets("d-a"), *alpha), BETA: (*datasets("d-b"), *beta)})
    return world_over(tmp_path, roots), roots


class TestEvaluation:
    def test_types_refuse(self, tmp_path):
        world, _roots = two_corpora(tmp_path)
        with pytest.raises(TypeError):
            evaluate_live_query(object(), DATASETS)  # type: ignore[arg-type]
        with pytest.raises(TypeError):
            evaluate_live_query(world, {"version": "science.view-query.v1", "clauses": []})  # type: ignore[arg-type]

    def test_a_never_published_world_selects_from_every_admitted_corpus(self, tmp_path):
        world, roots = two_corpora(tmp_path)
        live = evaluate_live_query(world, DATASETS)
        assert live.selected == tuple(sorted((dataset_ref("d-a"), dataset_ref("d-b"))))
        assert live.contributing == tuple(sorted((ALPHA, BETA))) and live.complete
        assert live.stamp.world_id == WORLD
        assert dict(live.stamp.coverage) == {c: registry.corpus_state_identity(r) for c, r in roots.items()}

    def test_a_retired_address_resolves_to_its_live_record(self, tmp_path):
        retired = datasets("d-old")[0].id
        (renamed,) = datasets("d-new")
        renamed.deprecated_ids = [retired]
        world, _roots = two_corpora(tmp_path, alpha=(renamed,))
        assert evaluate_live_query(world, query([{"addresses": [retired]}])).selected == (renamed.id,)

    def test_a_world_with_nothing_admitted_selects_nothing_and_is_complete(self, tmp_path):
        live = evaluate_live_query(world_over(tmp_path, {}), DATASETS)
        assert (live.selected, live.stamp.coverage, live.absent, live.complete) == ((), (), (), True)

    def test_a_corpus_holding_only_coordination_records_is_captured_and_contributes_nothing(self, tmp_path):
        roots = corpora(tmp_path, {ALPHA: (raw_coordination_node("project", PROJECT, "4" * 32),), BETA: datasets("d-b")})
        live = evaluate_live_query(world_over(tmp_path, roots), DATASETS)
        assert live.selected == (dataset_ref("d-b"),) and live.contributing == (BETA,)
        assert set(dict(live.stamp.coverage)) == {ALPHA, BETA}

    def test_a_configured_root_with_an_unreadable_manifest_refuses(self, tmp_path):
        roots = corpora(tmp_path, {ALPHA: datasets("d-a")})
        broken = tmp_path / "broken"
        broken.mkdir()
        (broken / "corpus.yaml").write_text("not: [a manifest\n", encoding="utf-8")
        world = world_over(tmp_path, roots, also_configured=(broken,))
        with pytest.raises(ResolutionRefused, match="cannot read"):
            evaluate_live_query(world, DATASETS)

    def test_an_unchanged_world_answers_identically_and_a_write_moves_only_its_corpus(self, tmp_path):
        world, roots = two_corpora(tmp_path)
        first = evaluate_live_query(world, DATASETS)
        assert evaluate_live_query(world, DATASETS).identity() == first.identity()
        (late,) = datasets("d-late")
        raw_write(roots[ALPHA], late)
        moved = evaluate_live_query(world, DATASETS)
        assert late.id in moved.selected
        assert dict(moved.stamp.coverage)[ALPHA] != dict(first.stamp.coverage)[ALPHA]
        assert dict(moved.stamp.coverage)[BETA] == dict(first.stamp.coverage)[BETA]
```

- [ ] **Step 2: Run to see them fail**

Run: `cd python && uv run --frozen pytest tests/test_live_selection.py::TestEvaluation -q`
Expected: FAIL — `ImportError: cannot import name 'evaluate_live_query'`.

- [ ] **Step 3: Implement.** In `live.py`, replace the import block and `__all__` with:

```python
from __future__ import annotations

from collections.abc import Iterator, Mapping
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import final

from nodes.core.errors import RefError
from nodes.core.node import Node
from nodes.core.structural_index import ResolvedEdge

from beliefs import stored
from beliefs.corpus import ReadView, _operation_lock_for, validated_node
from beliefs.errors import (
    CaptureDrift,
    ContractMismatch,
    CorpusStateMalformed,
    ManifestMalformed,
    ResolutionRefused,
    SelectionRefused,
)
from beliefs.identity import v1
from beliefs.sealed import sealed
from beliefs.view_query import ViewQuery
from beliefs.world import derive, registry
from beliefs.world.selection import Unresolved, _denoted
from beliefs.world.view import LocatedState

__all__ = ["LIVE_SELECTION_VERSION", "CaptureStamp", "LiveSelection", "evaluate_live_query"]
```

and append after `LiveSelection`:

```python
@final
class _LiveCapture:
    """The capture `_denoted` reads on the live path (decision 9): publish's
    address map over the captured world records, those records by corpus and
    uid, and the inbound edges between them. It records no absent corpus's
    addresses (decision 4), so it never answers `not-present`."""

    def __init__(
        self,
        recorded: Mapping[str, tuple[str, str]],
        held: Mapping[str, Mapping[str, Node]],
        inbound: Mapping[tuple[str, str], tuple[ResolvedEdge, ...]],
    ) -> None:
        self._recorded = recorded
        self._held = held
        self._inbound = inbound

    def _located_state(self, ref: str) -> LocatedState:
        return "resolved" if ref in self._recorded else "unknown"

    def corpus_of(self, ref: str) -> str | None:
        entry = self._recorded.get(ref)
        return None if entry is None else entry[0]

    def resolve(self, ref: str) -> str | None:
        entry = self._recorded.get(ref)
        return None if entry is None else self._held[entry[0]][entry[1]].id

    def get(self, ref: str) -> Node:
        entry = self._recorded.get(ref)
        if entry is None:
            raise RefError(f"no node resolves ref {ref!r}")
        return validated_node(self._held[entry[0]][entry[1]]).model_copy(deep=True)

    def inbound(self, ref: str) -> list[ResolvedEdge]:
        entry = self._recorded.get(ref)
        if entry is None:
            return []
        return [
            ResolvedEdge(relation=deepcopy(edge.relation), source_uid=edge.source_uid, target_uid=edge.target_uid)
            for edge in self._inbound.get(entry, ())
        ]

    def live_id(self, uid: str) -> str:
        for records in self._held.values():
            if (node := records.get(uid)) is not None:
                return node.id
        raise KeyError(uid)

    def _mapped_records(self) -> Iterator[tuple[str, Node]]:
        for corpus_id in sorted(self._held):
            for uid in sorted(self._held[corpus_id]):
                yield corpus_id, self._held[corpus_id][uid]


def evaluate_live_query(world: registry.World, query: ViewQuery) -> LiveSelection:
    """Denote `query` over every admitted corpus's current state (§3), or refuse."""
    if type(world) is not registry.World:
        raise TypeError(f"evaluate_live_query takes a registry.World, not {type(world).__name__}")
    if not isinstance(query, ViewQuery):
        raise TypeError(f"evaluate_live_query takes a parsed ViewQuery, not {type(query).__name__}")
    carriers, absent = _coverage(world)
    captured, states, damaged = _capture(carriers)
    if damaged:
        raise SelectionRefused("corpus-damaged", refs=damaged)
    recorded = _address_map(captured, states)
    _require_unmapped_uids_unique(captured)
    held = {
        corpus_id: {node.uid: node for node in records if node.kind in stored.WORLD_KINDS}
        for corpus_id, records in captured.items()
    }
    denoted = _denoted(_LiveCapture(recorded, held, _inbound(recorded, held)), query)
    return LiveSelection(
        stamp=CaptureStamp(world.config.world_id, tuple(sorted(states.items()))),
        query=query,
        selected=denoted.selected,
        contributing=denoted.contributing,
        absent=absent,
        unresolved=denoted.unresolved,
    )


def _coverage(world: registry.World) -> tuple[dict[str, Path], tuple[str, ...]]:
    """Decision 3: the registry's live admitted set, read under the world
    barrier and released before any capture, each corpus present or absent as
    `open_world_view` resolves it. No epoch is read."""
    carriers: dict[str, Path] = {}
    absent: list[str] = []
    with registry._locked_barrier(world) as world_root:
        world._state.registry = registry._scan_registry(world_root)
        covered = registry._live_corpus_ids(world._state.registry)
        for corpus_id in covered:
            try:
                status = registry._reduce_status(world.config, world._state.registry, corpus_id)
            except ManifestMalformed as caught:
                raise ResolutionRefused(
                    f"{corpus_id}: a configured root claims a manifest this world cannot read, so it can say "
                    f"neither that the corpus is here nor that it is absent: {caught}"
                ) from caught
            if any(finding.code == "duplicate-carrier" for finding in status.findings):
                raise ResolutionRefused(
                    f"{corpus_id}: more than one configured carrier claims this corpus, so which bytes "
                    "answer is a configuration question rather than a resolution"
                )
            if status.present:
                carriers[corpus_id] = registry._carrier_roots(world.config, corpus_id)[0]
            else:
                absent.append(corpus_id)
    return carriers, tuple(absent)


def _capture(carriers: Mapping[str, Path]) -> tuple[dict[str, tuple[Node, ...]], dict[str, str], list[str]]:
    """Decisions 5 and 8: one hold per present corpus, serial, in sorted
    order. Both state reads and the one enumeration happen inside the hold; a
    moved state discards the whole evaluation, and damage is collected so the
    refusal names every damaged corpus."""
    captured: dict[str, tuple[Node, ...]] = {}
    states: dict[str, str] = {}
    damaged: list[str] = []
    for corpus_id in sorted(carriers):
        carrier = carriers[corpus_id]
        with _operation_lock_for(carrier).capture():
            try:
                before = registry.corpus_state_identity(carrier)
                view = ReadView.opened_at(carrier)
                view._require_base_pin()
            except CorpusStateMalformed:
                damaged.append(corpus_id)
                continue
            except ContractMismatch:
                damaged.append(corpus_id)
                continue
            records = tuple(view.iter_stored())
            after = registry.corpus_state_identity(carrier)
            if before != after:
                raise CaptureDrift(
                    f"{corpus_id}: {carrier}: the corpus state moved inside the capture hold "
                    f"({before} -> {after}); the whole live evaluation is discarded and nothing is returned"
                )
        captured[corpus_id] = records
        states[corpus_id] = before
    return captured, states, damaged


def _address_map(
    captured: Mapping[str, tuple[Node, ...]], states: Mapping[str, str]
) -> Mapping[str, tuple[str, str]]:
    """Decisions 6 and 7: publish's own `derive.address_map` over the captured
    world-kind records, so its `AddressMapConflict` — `uid-corruption` before
    `duplicate-location` — reaches the caller unchanged."""
    located = [
        (corpus_id, node) for corpus_id in sorted(captured) for node in captured[corpus_id] if node.kind in stored.WORLD_KINDS
    ]
    return derive.address_map(
        derive.Capture(
            tuple(
                derive.CapturedCorpus(
                    corpus_id,
                    states[corpus_id],
                    tuple(
                        derive.CapturedRecord(
                            address=node.id, uid=node.uid, kind=node.kind, deprecated_ids=tuple(node.deprecated_ids)
                        )
                        for owner, node in located
                        if owner == corpus_id
                    ),
                )
                for corpus_id in sorted(captured)
            )
        )
    )


def _require_unmapped_uids_unique(captured: Mapping[str, tuple[Node, ...]]) -> None:
    """Decision 7's scoped W8b check, run only after the map succeeded: a uid
    held in two corpora where a holder is a record the map excludes."""
    holders: dict[str, list[tuple[str, Node]]] = {}
    for corpus_id in sorted(captured):
        for node in captured[corpus_id]:
            holders.setdefault(node.uid, []).append((corpus_id, node))
    for uid in sorted(holders):
        corpora = sorted({corpus_id for corpus_id, _ in holders[uid]})
        if len(corpora) > 1 and any(node.kind not in stored.WORLD_KINDS for _, node in holders[uid]):
            raise ResolutionRefused(
                f"uid {uid!r} is held by both {corpora[0]} and {corpora[1]}; world uid uniqueness is enforced "
                "and its violation is corruption, not a record with two homes (W8b, the view's half)"
            )


def _inbound(
    recorded: Mapping[str, tuple[str, str]], held: Mapping[str, Mapping[str, Node]]
) -> dict[tuple[str, str], tuple[ResolvedEdge, ...]]:
    """Inbound edges between held records, constructed as `open_world_view` constructs them."""
    inbound: dict[tuple[str, str], list[ResolvedEdge]] = {}
    for records in held.values():
        for node in records.values():
            for relation in node.relations:
                if (target := recorded.get(relation.target)) is not None:
                    source = recorded.get(relation.source)
                    if source is None:
                        continue
                    source_uid = source[1] if source[1] in held.get(source[0], {}) else None
                    inbound.setdefault(target, []).append(
                        ResolvedEdge(relation=relation, source_uid=source_uid, target_uid=target[1])
                    )
    return {key: tuple(edges) for key, edges in inbound.items()}
```

If `ruff format` would rewrap a line Task 5 targets, keep this plan's spelling and do not run the formatter over `live.py` (`ruff check` is the gate; the repository does not gate on `ruff format`).

- [ ] **Step 4: Check the arm targets occur once**

```bash
cd python && uv run --frozen python - <<'EOF'
from pathlib import Path
source = Path("src/beliefs/world/live.py").read_text(encoding="utf-8")
targets = [
    "    for corpus_id in sorted(carriers):",
    "        covered = registry._live_corpus_ids(world._state.registry)",
    "            else:\n                absent.append(corpus_id)",
    "    carriers, absent = _coverage(world)\n",
    "            if before != after:",
    "        with _operation_lock_for(carrier).capture():",
    "        stamp=CaptureStamp(world.config.world_id, tuple(sorted(states.items()))),",
    "            except CorpusStateMalformed:\n                damaged.append(corpus_id)\n                continue",
    "                view._require_base_pin()\n",
    "    recorded = _address_map(captured, states)\n    _require_unmapped_uids_unique(captured)\n",
    "    located = [\n        (corpus_id, node) for corpus_id in sorted(captured) for node in captured[corpus_id] if node.kind in stored.WORLD_KINDS\n    ]",
    "    _require_unmapped_uids_unique(captured)\n",
]
for target in targets:
    assert source.count(target) == 1, (source.count(target), target)
print("all twelve targets occur once")
EOF
```
Expected: `all twelve targets occur once`.

- [ ] **Step 5: Run the tests**

```bash
cd python && export SCIENCE_CUT13_ROOT=$(readlink -f ~/d/beliefs)/.lifecycle-wrappers-test
uv run --frozen pytest tests/test_live_selection.py tests/test_world_selection.py tests/test_arm_staleness.py tests/test_capability_boundary.py tests/test_permit_boundary.py tests/test_permit_entry_points.py -q
uv run --frozen ruff check src tests && uv run --frozen pyright
```
Expected: all pass, 0 errors.

- [ ] **Step 6: Commit**

```bash
tasks done <Task 3's id> "evaluate_live_query: registry coverage, per-corpus holds, publish's map, the shared core"
tasks check && git add python/src/beliefs/world/live.py python/tests/test_live_selection.py tasks
git commit -m "feat(world): evaluate a view query live over every admitted corpus"
```

---

### Task 4: The acceptance module — `test_live_selection_acceptance.py`

**Files:**
- Create: `python/tests/acceptance/test_live_selection_acceptance.py`

**Interfaces:**
- Consumes: Task 3's `evaluate_live_query`; fixtures `durable_world` (`test_world_view_acceptance.py`), `work_directory` (acceptance `conftest.py`), `topic_nodes`, `query`, `PROJECT` (`test_world_selection.py`), `damage` (`test_world_view.py`), `hold_shipped` (`test_world_receipts.py`), `raw_write` (`fixtures_cut4.py`).
- Produces: the twelve unit functions Task 5's `UNIT_CHECKS` names, spelled exactly as below.

- [ ] **Step 1: Write the module.** Every assertion is the spec §6.2 row it names.

```python
"""Cut 41: live view-query evaluation over certified durable roots (live-query design §6.2)."""

from __future__ import annotations

import shutil
from pathlib import Path
from tempfile import mkdtemp

import pytest
from authority import FULL
from coordination_fixtures import coordination_profile, raw_coordination_node
from dataset_fixtures import dataset_ref, pinned
from fixtures_cut4 import raw_write
from test_evaluation import GENE
from test_world_receipts import hold_shipped
from test_world_selection import PROJECT, query, topic_nodes
from test_world_view import damage
from test_world_view_acceptance import durable_world  # noqa: F401

# ruff: noqa: F811 - imported pytest fixtures are injected below.
from beliefs import stored
from beliefs.corpus import ReadView, _operation_lock_for
from beliefs.errors import AddressMapConflict, BuildContended, CaptureDrift, ResolutionRefused, SelectionRefused
from beliefs.root import init_world_root, metadata_root_for, open_world
from beliefs.world import Fresh, WorldConfig, epoch, registry
from beliefs.world.live import evaluate_live_query
from beliefs.world.registry import load_manifest
from beliefs.world.selection import evaluate_query
from beliefs.world.view import open_world_view

COORDINATION = coordination_profile(None)
DATASETS = query([{"kinds": ["dataset"]}])


def datasets(*slugs):
    return tuple(stored.dataset_node(title=slug, resources=pinned(slug)) for slug in slugs)


def topic_records():
    """Slice 4's topic records without its coordination project: ALPHA d_a, r_a; BETA d_b, r_b, p_b."""
    alpha, beta = topic_nodes()
    return tuple(node for node in alpha if node.kind != "project"), beta


@pytest.fixture()
def scratch(work_directory):
    path = Path(mkdtemp(prefix="cut41-", dir=work_directory))
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


@pytest.fixture()
def live_world(durable_world, scratch):
    """Two admitted durable corpora and a world that has never published.

    `records` replaces the topic records; `gamma` adds a third configured,
    admitted corpus; `admit_beta=False` leaves BETA configured but unadmitted;
    `also_configured` adds roots the world sees and never admits."""

    def make(*, records=None, alpha_raw=(), beta_raw=(), gamma=None, admit_beta=True, also_configured=()):
        alpha_nodes, beta_nodes = topic_records() if records is None else records
        a, alpha, left = durable_world.corpus(COORDINATION)
        b, beta, right = durable_world.corpus(COORDINATION)
        for writer, nodes in ((left, alpha_nodes), (right, beta_nodes)):
            for node in nodes:
                writer.add(node)
        for node in alpha_raw:
            raw_write(alpha, node)
        for node in beta_raw:
            raw_write(beta, node)
        roots = {a: alpha, b: beta}
        if gamma is not None:
            g, gamma_root, third = durable_world.corpus(COORDINATION)
            for node in gamma:
                third.add(node)
            roots[g] = gamma_root
        config = WorldConfig(scratch / f"live-world-{a[:8]}", "e" * 32, (*roots.values(), *also_configured))
        init_world_root(config, authority=FULL)
        world = open_world(config, authority=FULL)
        for corpus_id, root in roots.items():
            if corpus_id != b or admit_beta:
                world.admit(root, provenance=Fresh())
        return world, roots, a, b

    return make


def tree(root: Path) -> dict[str, bytes]:
    return {str(path.relative_to(root)): path.read_bytes() for path in sorted(root.rglob("*")) if path.is_file()}


# --- Z1: coverage is the world's live admitted set ------------------------------------------------


def test_z1_a_every_present_admitted_corpus_is_captured_and_stamped_durably(live_world):
    world, roots, a, b = live_world()
    live = evaluate_live_query(world, DATASETS)
    assert live.selected == tuple(sorted((dataset_ref("d-a"), dataset_ref("d-b"))))
    assert live.contributing == tuple(sorted((a, b)))
    assert live.stamp.coverage == tuple(sorted((c, registry.corpus_state_identity(r)) for c, r in roots.items()))
    assert live.absent == () and live.complete


def test_z1_b_a_terminal_corpus_is_never_covered_durably(live_world):
    world, roots, a, b = live_world(gamma=datasets("d-g"))
    (g,) = set(roots) - {a, b}
    world.retire(g)
    live = evaluate_live_query(world, DATASETS)
    assert dataset_ref("d-g") not in live.selected
    assert set(dict(live.stamp.coverage)) == {a, b}
    assert g not in live.contributing and g not in live.absent


def test_z1_c_an_absent_corpus_is_listed_and_its_addresses_are_unknown_durably(live_world):
    world, roots, a, b = live_world()
    (roots[b] / "corpus.yaml").unlink()
    live = evaluate_live_query(world, DATASETS)
    assert live.absent == (b,) and not live.complete
    assert live.selected == (dataset_ref("d-a"),) and set(dict(live.stamp.coverage)) == {a}
    with pytest.raises(SelectionRefused) as refused:
        evaluate_live_query(world, query([{"addresses": [dataset_ref("d-b")]}]))
    assert refused.value.reason == "address-unknown" and refused.value.refs == (dataset_ref("d-b"),)


def test_z1_d_coverage_is_the_registry_not_an_epoch_durably(live_world):
    world, roots, a, b = live_world(records=(datasets("d-a"), datasets("d-b")), admit_beta=False)
    never_published = evaluate_live_query(world, DATASETS)
    assert never_published.selected == (dataset_ref("d-a"),)
    epoch.build_epoch(world, coverage=frozenset({a}), bindings=hold_shipped(world))
    world.admit(roots[b], provenance=Fresh())
    live = evaluate_live_query(world, DATASETS)
    assert live.selected == tuple(sorted((dataset_ref("d-a"), dataset_ref("d-b"))))
    assert set(dict(live.stamp.coverage)) == {a, b}


# --- Z2: each corpus is captured inside its own hold -----------------------------------------------


def test_z2_a_a_state_moving_inside_the_hold_discards_the_evaluation_durably(live_world, monkeypatch):
    world, roots, a, b = live_world()
    first = min(a, b)
    original = registry.corpus_state_identity
    calls = {"n": 0}

    def moving(root):
        calls["n"] += 1
        if calls["n"] == 2:  # the first corpus's second read, inside its hold
            raw_write(roots[first], datasets("d-late")[0])
        return original(root)

    monkeypatch.setattr(registry, "corpus_state_identity", moving)
    with pytest.raises(CaptureDrift):
        evaluate_live_query(world, DATASETS)


def test_z2_b_state_reads_and_enumeration_run_inside_the_corpus_hold_durably(live_world, monkeypatch):
    world, roots, a, b = live_world()
    carriers = {root.resolve() for root in roots.values()}
    seen: list[tuple[str, Path, object]] = []
    original_state = registry.corpus_state_identity
    original_open = ReadView.opened_at.__func__
    original_iter = ReadView.iter_stored

    def state(root):
        seen.append(("state", Path(root).resolve(), _operation_lock_for(root)._holder))
        return original_state(root)

    def opened(cls, root):
        seen.append(("open", Path(root).resolve(), _operation_lock_for(root)._holder))
        return original_open(cls, root)

    def enumerated(self):
        # `iter_stored` reads the store lazily, so the holder is read at each record
        # as the evaluation consumes it, not when the iterator is made: a
        # generator created inside the hold and drained after it must fail here.
        root = self._corpus.store.root
        for node in original_iter(self):
            seen.append(("enumerate", Path(root).resolve(), _operation_lock_for(root)._holder))
            yield node

    monkeypatch.setattr(registry, "corpus_state_identity", state)
    monkeypatch.setattr(ReadView, "opened_at", classmethod(opened))
    monkeypatch.setattr(ReadView, "iter_stored", enumerated)
    evaluate_live_query(world, DATASETS)
    monkeypatch.undo()

    calls = [call for call in seen if call[1] in carriers]
    # every carrier holds records, so each is seen stating, opening and enumerating
    assert {carrier: {kind for kind, path, _ in calls if path == carrier} for carrier in carriers} == {
        carrier: {"state", "open", "enumerate"} for carrier in carriers
    }
    assert all(holder == "capture" for _, _, holder in calls), calls
    with _operation_lock_for(roots[a]):
        with pytest.raises(BuildContended):
            evaluate_live_query(world, DATASETS)


# --- Z3: the stamp names what was denoted ------------------------------------------------------------


def test_z3_a_the_stamp_names_the_states_the_selection_was_denoted_over_durably(live_world, monkeypatch):
    world, roots, a, b = live_world()
    first, second = sorted((a, b))
    (late,) = datasets("d-late")
    original = registry.corpus_state_identity
    in_hold: dict[str, str] = {}

    def recording(root):
        resolved = Path(root).resolve()
        if resolved == roots[second].resolve() and "written" not in in_hold:
            in_hold["written"] = "yes"  # the first corpus's hold is released; the evaluation has not returned
            raw_write(roots[first], late)
        value = original(root)
        if resolved == roots[first].resolve():
            in_hold.setdefault(first, value)
        return value

    monkeypatch.setattr(registry, "corpus_state_identity", recording)
    live = evaluate_live_query(world, DATASETS)
    monkeypatch.undo()
    assert late.id not in live.selected
    assert dict(live.stamp.coverage)[first] == in_hold[first]
    assert registry.corpus_state_identity(roots[first]) != in_hold[first]


# --- Z4: damage refuses and is never omitted -----------------------------------------------------------


def test_z4_a_a_malformed_corpus_refuses_and_is_never_omitted_durably(live_world):
    world, roots, a, b = live_world()
    damage(roots[b], "parse-error")
    with pytest.raises(SelectionRefused) as refused:
        evaluate_live_query(world, DATASETS)
    assert refused.value.reason == "corpus-damaged" and refused.value.refs == (b,)


def test_z4_b_a_disagreeing_base_pin_refuses_durably(live_world):
    world, roots, a, b = live_world()
    manifest = roots[b] / "corpus.yaml"
    science = load_manifest(roots[b]).profile.science_contract
    text = manifest.read_text(encoding="utf-8")
    assert f"science_contract: {science}" in text
    manifest.write_text(
        text.replace(f"science_contract: {science}", "science_contract: science:" + "0" * 64), encoding="utf-8"
    )
    with pytest.raises(SelectionRefused) as refused:
        evaluate_live_query(world, DATASETS)
    assert refused.value.reason == "corpus-damaged" and refused.value.refs == (b,)


# --- Z5: conflicts keep publish's classification -------------------------------------------------------


def test_z5_a_a_shared_uid_duplicate_location_is_publishs_conflict_durably(live_world):
    world, roots, a, b = live_world()
    copy = ReadView.opened_at(roots[a]).get(dataset_ref("d-a"))  # same address, same uid
    raw_write(roots[b], copy)
    with pytest.raises(AddressMapConflict) as refused:
        evaluate_live_query(world, DATASETS)
    assert refused.value.finding.code == "duplicate-location" and refused.value.finding.ref == copy.id


def test_z5_b_uid_corruption_outranks_duplicate_location_durably(live_world):
    world, roots, a, b = live_world()
    read = ReadView.opened_at(roots[a])
    run = read.get("run:r-a")
    twin = run.model_copy(deep=True)
    twin.id = "run:r-a-twin"  # same uid, another canonical address
    raw_write(roots[b], twin)
    raw_write(roots[b], read.get(dataset_ref("d-a")))  # and a duplicate location beside it
    with pytest.raises(AddressMapConflict) as refused:
        evaluate_live_query(world, DATASETS)
    assert refused.value.finding.code == "uid-corruption" and refused.value.finding.ref == run.uid


def test_z5_c_a_uid_shared_with_a_record_outside_the_map_refuses_after_the_map_durably(live_world):
    world, roots, a, b = live_world()
    shared = ReadView.opened_at(roots[b]).get("run:r-b").uid
    raw_write(roots[a], raw_coordination_node("project", PROJECT, shared))
    with pytest.raises(ResolutionRefused, match="W8b"):
        evaluate_live_query(world, DATASETS)


# --- the module's other tests (spec §6.2) --------------------------------------------------------------


def test_live_after_a_write_selects_what_the_old_epoch_refuses_durably(live_world):
    world, roots, a, b = live_world(records=(datasets("d-a"), datasets("d-b")))
    published = epoch.build_epoch(world, coverage=frozenset({a, b}), bindings=hold_shipped(world))
    (late,) = datasets("d-late")
    raw_write(roots[a], late)
    with pytest.raises(SelectionRefused) as refused:
        evaluate_query(open_world_view(world, published), DATASETS)
    assert refused.value.reason == "corpus-drifted"
    live = evaluate_live_query(world, DATASETS)
    assert late.id in live.selected
    assert dict(live.stamp.coverage)[a] == registry.corpus_state_identity(roots[a])


AGREEMENT_QUERIES = (
    # Slice 4's acceptance queries over its default topic records
    # (`test_world_selection_acceptance.py`), then two of this plan's own.
    query([{"kinds": ["dataset"]}]),
    query([{"closure": {"anchor": "run:r-a", "predicates": ["produces"], "direction": "out"}}]),
    query([{"references-term": GENE}]),
    query([{"references-term": GENE.upper()}]),
    query([{"references-term": GENE.lower()}]),
    query([{"addresses": [dataset_ref("d-a")]}], [{"references-term": GENE}]),
    query([{"addresses": [dataset_ref("d-b")]}]),
    query([{"closure": {"anchor": dataset_ref("d-b"), "predicates": ["produces"], "direction": "in"}}]),
    query([{"closure": {"anchor": dataset_ref("d-a"), "predicates": ["produces"], "direction": "in"}}]),
    query([{"kinds": ["dataset"]}, {"addresses": [dataset_ref("d-b")]}], [{"kinds": ["run"]}]),
    query([{"kinds": ["dataset", "run"]}]),
    query(
        [{"closure": {"anchor": dataset_ref("d-b"), "predicates": ["produces"], "direction": "both"}}],
        [{"kinds": ["proposition"]}],
    ),
)


def test_live_and_epoch_agree_over_identical_coverage_every_corpus_present_and_equal_states_durably(live_world):
    world, roots, a, b = live_world()
    published = epoch.build_epoch(world, coverage=frozenset({a, b}), bindings=hold_shipped(world))
    live_set = {a, b}
    assert {corpus_id for corpus_id, _ in published.coverage} == live_set  # identical coverage
    assert all(root.joinpath("corpus.yaml").exists() for root in roots.values())  # every corpus present
    assert dict(published.coverage) == {c: registry.corpus_state_identity(r) for c, r in roots.items()}  # equal states
    view = open_world_view(world, published)
    for each in AGREEMENT_QUERIES:
        bound, live = evaluate_query(view, each), evaluate_live_query(world, each)
        assert (live.selected, live.contributing, live.absent, live.unresolved) == (
            bound.selected,
            bound.contributing,
            bound.absent,
            bound.unresolved,
        ), each.projection()
        live_projection, bound_projection = live.projection(), bound.projection()
        assert set(live_projection) - set(bound_projection) == {"capture"}
        assert set(bound_projection) - set(live_projection) == {"epoch"}
        assert {k: v for k, v in live_projection.items() if k not in ("version", "capture")} == {
            k: v for k, v in bound_projection.items() if k not in ("version", "epoch")
        }


def test_equal_states_alone_do_not_make_the_two_agree_durably(live_world):
    world, roots, a, b = live_world(records=(datasets("d-a"), datasets("d-b")), admit_beta=False)
    published = epoch.build_epoch(world, coverage=frozenset({a}), bindings=hold_shipped(world))
    world.admit(roots[b], provenance=Fresh())
    assert dict(published.coverage)[a] == registry.corpus_state_identity(roots[a])
    bound = evaluate_query(open_world_view(world, published), DATASETS)
    live = evaluate_live_query(world, DATASETS)
    assert dataset_ref("d-b") in live.selected and dataset_ref("d-b") not in bound.selected


def test_damage_names_every_damaged_corpus_durably(live_world):
    world, roots, a, b = live_world()
    damage(roots[a], "parse-error")
    damage(roots[b], "parse-error")
    with pytest.raises(SelectionRefused) as refused:
        evaluate_live_query(world, DATASETS)
    assert refused.value.reason == "corpus-damaged" and refused.value.refs == tuple(sorted((a, b)))


def test_coordination_records_are_never_selected_durably(live_world):
    project = raw_coordination_node("project", PROJECT, "4" * 32)
    world, roots, a, b = live_world(alpha_raw=(project,))
    every = evaluate_live_query(world, query([{"kinds": sorted(stored.WORLD_KINDS)}]))
    assert project.id not in every.selected
    world_records = {node.id for records in topic_records() for node in records}
    assert set(every.selected) == world_records


def test_two_carriers_of_one_corpus_refuse_durably(live_world, scratch):
    twin = scratch / "twin-carrier"
    twin.mkdir()
    world, roots, a, b = live_world(also_configured=(twin,))
    shutil.copyfile(roots[a] / "corpus.yaml", twin / "corpus.yaml")
    with pytest.raises(ResolutionRefused, match="more than one configured carrier"):
        evaluate_live_query(world, DATASETS)


def test_an_evaluation_writes_nothing_durably(live_world):
    world, roots, a, b = live_world()
    watched = [world.config.world_root, *roots.values(), *(metadata_root_for(root) for root in roots.values())]
    before = {str(path): tree(path) for path in watched}
    states = {c: registry.corpus_state_identity(r) for c, r in roots.items()}
    evaluate_live_query(world, DATASETS)
    assert {str(path): tree(path) for path in watched} == before
    assert {c: registry.corpus_state_identity(r) for c, r in roots.items()} == states
```

- [ ] **Step 2: Run the module** under Global Constraints' acceptance exports:

```bash
uv run --frozen pytest tests/acceptance/test_live_selection_acceptance.py -q
uv run --frozen ruff check tests/acceptance/test_live_selection_acceptance.py
```

The repository's ruff (and the pre-commit hook) refuse the module as written above: nine unused unpacked names (RUF059) and one nested `with` (SIM117, in Z2-b's `BuildContended` check). Prefix each unused unpacked name with `_` and merge the two `with` statements into one; neither change touches an assertion. Then extend `test_coordination_records_are_never_selected_durably` with spec §6.2's other half, that the address map holds no coordination address: capture the covered carriers with `live._capture(roots)` and assert `project.id` is not a key of `live._address_map(captured, states)` (import the module as `from beliefs.world import live as live_module`, since `live` names a selection elsewhere in the file).
Expected: 19 passed. If a fixture fails for a reason the plan did not foresee (a durable writer refusing a topic record, a manifest serialized without the `science_contract: ` spelling Z4-b asserts), fix the fixture, never the assertion the row names, and note the fix for the results record's §3.

- [ ] **Step 3: Commit**

```bash
tasks done <Task 4's id> "acceptance: twelve Z units and the module's seven other tests"
tasks check && git add python/tests/acceptance/test_live_selection_acceptance.py tasks
git commit -m "test(cut41): the live selection acceptance module — Z1–Z5"
```

---

### Task 5: Declarations, guard, runner, the recent-cut row; run the cut

**Files:**
- Create: `python/tests/n2_arms_cut41.py`, `python/tests/acceptance/n2_arms_cut41.py`, `python/tests/acceptance/test_n2_cut41.py`, `python/tools/cut41_acceptance.py`
- Modify: `python/tests/test_recent_cut_acceptance.py`

**Interfaces:**
- Consumes: Task 0's freeze commit, digest and prefix decision; Task 4's test names; Task 3's spellings.
- Produces: `CUT41_ARMS` (12), `DECLARATION_UNITS` (12), `UNIT_CHECKS`, `unit_of`, `CO_CITED = ()`; the runner's `main`, `PREFIX_RUNNERS`, `PHASE_MODULES`.

- [ ] **Step 1: The declaration.** Create `python/tests/n2_arms_cut41.py`:

```python
"""Frozen cut-41 declaration: twelve units, twelve sabotage arms, one each."""

from n2_arms import Arm, Sabotage

DECLARATION_UNITS = (
    "Z1-a",
    "Z1-b",
    "Z1-c",
    "Z1-d",
    "Z2-a",
    "Z2-b",
    "Z3-a",
    "Z4-a",
    "Z4-b",
    "Z5-a",
    "Z5-b",
    "Z5-c",
)
_MODULE = "acceptance/test_live_selection_acceptance.py"
UNIT_CHECKS = {
    "Z1-a": f"{_MODULE}::test_z1_a_every_present_admitted_corpus_is_captured_and_stamped_durably",
    "Z1-b": f"{_MODULE}::test_z1_b_a_terminal_corpus_is_never_covered_durably",
    "Z1-c": f"{_MODULE}::test_z1_c_an_absent_corpus_is_listed_and_its_addresses_are_unknown_durably",
    "Z1-d": f"{_MODULE}::test_z1_d_coverage_is_the_registry_not_an_epoch_durably",
    "Z2-a": f"{_MODULE}::test_z2_a_a_state_moving_inside_the_hold_discards_the_evaluation_durably",
    "Z2-b": f"{_MODULE}::test_z2_b_state_reads_and_enumeration_run_inside_the_corpus_hold_durably",
    "Z3-a": f"{_MODULE}::test_z3_a_the_stamp_names_the_states_the_selection_was_denoted_over_durably",
    "Z4-a": f"{_MODULE}::test_z4_a_a_malformed_corpus_refuses_and_is_never_omitted_durably",
    "Z4-b": f"{_MODULE}::test_z4_b_a_disagreeing_base_pin_refuses_durably",
    "Z5-a": f"{_MODULE}::test_z5_a_a_shared_uid_duplicate_location_is_publishs_conflict_durably",
    "Z5-b": f"{_MODULE}::test_z5_b_uid_corruption_outranks_duplicate_location_durably",
    "Z5-c": f"{_MODULE}::test_z5_c_a_uid_shared_with_a_record_outside_the_map_refuses_after_the_map_durably",
}
CO_CITED = ()

_LIVE = "world/live.py"


def unit_of(row: str) -> str:
    """Every arm homes its own unit; no row shares one."""
    if row not in DECLARATION_UNITS:
        raise ValueError(f"{row!r} is not a cut-41 row")
    return row


def _arm(row, assertion, before, after):
    return Arm(
        row=row,
        asserts=assertion,
        sabotage=Sabotage(module=_LIVE, before=before, after=after),
        checks=(UNIT_CHECKS[unit_of(row)],),
    )


CUT41_ARMS = (
    _arm(
        "Z1-a",
        "Every present admitted corpus is captured and stamped, so skipping the last covered corpus loses its records and its coverage pair.",
        "    for corpus_id in sorted(carriers):",
        "    for corpus_id in sorted(carriers)[:-1]:",
    ),
    _arm(
        "Z1-b",
        "Coverage is the registry's live set, so a retired corpus whose carrier is still configured is never captured.",
        "        covered = registry._live_corpus_ids(world._state.registry)",
        "        covered = tuple(sorted({record.corpus_id for record in world._state.registry.admissions}))",
    ),
    _arm(
        "Z1-c",
        "An admitted corpus with no present carrier is listed in `absent`, so the selection is incomplete.",
        "            else:\n                absent.append(corpus_id)",
        "            else:\n                pass",
    ),
    _arm(
        "Z1-d",
        "Coverage never comes from an epoch: a never-published world evaluates, and a corpus admitted after the epoch is covered.",
        "    carriers, absent = _coverage(world)\n",
        "    from beliefs.world.read import current_epoch\n\n"
        "    carriers, absent = _coverage(world)\n"
        "    carriers = {corpus_id: root for corpus_id, root in carriers.items() if corpus_id in dict(current_epoch(world).coverage)}\n",
    ),
    _arm(
        "Z2-a",
        "A state that moves inside a corpus's capture hold raises `CaptureDrift` and returns nothing.",
        "            if before != after:",
        "            if False:",
    ),
    _arm(
        "Z2-b",
        "Both state reads and the enumeration run inside the corpus's own capture hold, which refuses a held writer lock.",
        "        with _operation_lock_for(carrier).capture():",
        '        with __import__("contextlib").nullcontext():',
    ),
    _arm(
        "Z3-a",
        "The stamp carries the states read inside each hold, never a state re-read after the captures.",
        "        stamp=CaptureStamp(world.config.world_id, tuple(sorted(states.items()))),",
        "        stamp=CaptureStamp(world.config.world_id, tuple(sorted((corpus_id, registry.corpus_state_identity(carriers[corpus_id])) for corpus_id in states))),",
    ),
    _arm(
        "Z4-a",
        "A present corpus whose construction fails is collected as damage and refuses the evaluation, never silently omitted.",
        "            except CorpusStateMalformed:\n                damaged.append(corpus_id)\n                continue",
        "            except CorpusStateMalformed:\n                continue",
    ),
    _arm(
        "Z4-b",
        "A present corpus whose base pin disagrees refuses the evaluation as damage.",
        "                view._require_base_pin()\n",
        "                pass\n",
    ),
    _arm(
        "Z5-a",
        "World-record conflicts are publish's: the scoped uid check runs only after the address map, so a shared-uid duplicate location is `duplicate-location`.",
        "    recorded = _address_map(captured, states)\n    _require_unmapped_uids_unique(captured)\n",
        "    _uids = [node.uid for records in captured.values() for node in records]\n"
        "    if len(_uids) != len(set(_uids)):\n"
        '        raise ResolutionRefused("a uid is held twice")\n'
        "    recorded = _address_map(captured, states)\n",
    ),
    _arm(
        "Z5-b",
        "Every captured world record reaches the address map, so uid corruption is refused before any duplicate location.",
        "    located = [\n"
        "        (corpus_id, node) for corpus_id in sorted(captured) for node in captured[corpus_id] if node.kind in stored.WORLD_KINDS\n"
        "    ]",
        "    located = list({\n"
        "        node.uid: (corpus_id, node) for corpus_id in sorted(captured) for node in captured[corpus_id] if node.kind in stored.WORLD_KINDS\n"
        "    }.values())",
    ),
    _arm(
        "Z5-c",
        "A uid a record outside the map shares with another corpus refuses `ResolutionRefused` (W8b, the view's half).",
        "    _require_unmapped_uids_unique(captured)\n",
        "    pass\n",
    ),
)
```

The acceptance shim `python/tests/acceptance/n2_arms_cut41.py` is cut 40's shim with every `40` replaced by `41`.

- [ ] **Step 2: The guard.** Copy `python/tests/acceptance/test_n2_cut40.py` to `python/tests/acceptance/test_n2_cut41.py`, then:
- import `CUT40_ARMS` from `n2_arms_cut40` and add it to `PRIOR_ARMS`;
- add `"python/tests/n2_arms_cut40.py": "<sha>"` to `FROZEN_PRIOR_CUT_FILES` (`git log -1 --format=%h -- python/tests/n2_arms_cut40.py`);
- set `FROZEN_CUT` to the cut-41 document, and `CUT41_FREEZE_COMMIT` and `CUT41_FROZEN_SHA256` from Task 0 Step 5;
- set `FROZEN_DECLARATION = "python/tests/n2_arms_cut41.py"`, recompute `CUT41_DECLARATION_SHA256` with `sha256sum python/tests/n2_arms_cut41.py`, and rename every `CUT40_*` constant to `CUT41_*` except the `CUT40_ARMS` import the previous bullet adds to `PRIOR_ARMS`;
- make the inventory test assert the twelve units in Step 1's order and `(FROZEN_ARMS, FROZEN_UNITS) == (12, 12)`;
- point `test_every_acceptance_test_the_arms_name_exists` at `test_live_selection_acceptance.py`;
- make the freeze test assert `"**12 arms, 12 declaration units**" in " ".join(current.split())` and the prefix tuple (`'("cut40_acceptance.py",)' in current`);
- replace the row-parser negatives with `("", "Z1", "Z1-e", "Z2-c", "Z3-b", "Z4-c", "Z5-d", "Z6-a", "Y5-a", "W7-a")`, each raising `is not a cut-41 row`.

- [ ] **Step 3: The runner.** Create `python/tools/cut41_acceptance.py`:

```python
"""Run cut 41 after the highest-numbered prior runner on the certified durable tuple."""

from __future__ import annotations

import sys
from pathlib import Path

from acceptance_runner import run_acceptance

PYTHON_ROOT = Path(__file__).resolve().parents[1]
TOOLS = PYTHON_ROOT / "tools"
ACCEPTANCE = PYTHON_ROOT / "tests" / "acceptance"
REPO_ROOT = PYTHON_ROOT.parent
# Beside the main checkout, as cut 40's runner resolves it: a lane worktree
# under `.worktrees/` sits on storage the durability allowlist refuses.
MAIN_CHECKOUT = REPO_ROOT.parents[1] if REPO_ROOT.parent.name == ".worktrees" else REPO_ROOT
DEFAULT_WORK = MAIN_CHECKOUT / ".work" / "acceptance" / "cut41"

# Roadmap rule 5: the highest-numbered acceptance runner at freeze (the cut document's §5).
PREFIX_RUNNERS = ("cut40_acceptance.py",)
PHASE_MODULES = ("test_live_selection_acceptance.py", "test_n2_cut41.py")


def declared_accounting() -> tuple[int, int, int]:
    """Arms, declaration units and exercised guarantee rows from the frozen declaration."""
    for directory in (PYTHON_ROOT / "tests", ACCEPTANCE):
        path = str(directory)
        if path not in sys.path:
            sys.path.insert(0, path)
    from n2_arms_cut41 import CUT41_ARMS, DECLARATION_UNITS  # pyright: ignore[reportMissingImports]

    rows = {unit.partition("-")[0] for unit in DECLARATION_UNITS}
    assert rows == {"Z1", "Z2", "Z3", "Z4", "Z5"}
    arms, units = len(CUT41_ARMS), len(DECLARATION_UNITS)
    assert (arms, units) == (12, 12)
    return arms, units, len(rows)


def main(argv: list[str]) -> int:
    result = run_acceptance(
        cut=41,
        python_root=PYTHON_ROOT,
        default_work=DEFAULT_WORK,
        prefix_runners=PREFIX_RUNNERS,
        phase_modules=PHASE_MODULES,
        declared_accounting=declared_accounting,
        argv=argv,
    )

    if result == 0:
        print("guarantee rows exercised: 5 (5 newly closed: Z1, Z2, Z3, Z4, Z5)", flush=True)
    return result


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
```

`PREFIX_RUNNERS` is the tuple Task 0 Step 1 fixed. Write exactly the tuple the frozen cut document's §5 names, never a runner chosen at Task 5.

- [ ] **Step 4: The recent-cut row.** In `python/tests/test_recent_cut_acceptance.py`, add `import cut41_acceptance as cut41` after the cut-40 import, `(cut41, 41, (12, 12, 5)),` after cut 40's entry, `"cut41"` after `"cut40"` in `ids`, and after the cut-40 branch:

```python
    if cut == 41:
        assert "guarantee rows exercised: 5 (5 newly closed: Z1, Z2, Z3, Z4, Z5)" in output
```

- [ ] **Step 5: Guard green, then the cut, detached.** The prefix, cut 40, is discharged, so rule 5 adds no wait. Rerun Task 0 Step 1's scan against `main` first. If a document numbered 42 or above has frozen since and is undischarged, rule 5 does not reorder this cut, which is lower-numbered. If anything numbered 41 other than this cut appears, stop and `tasks park <Task 5's id> "cut 41 contested at discharge" --waiting-on user --reason decision`.

```bash
cd python && uv run --frozen pytest tests/test_recent_cut_acceptance.py tests/test_arm_staleness.py tests/test_frozen_guards.py -q
cd ~/d/beliefs/.worktrees/live-query/python && cd "$(pwd -P)"
export SCIENCE_MM30_ROOT=$(readlink -f ~/d/beliefs)/.work/reproduction/mm30
for n in $(seq 4 41); do export SCIENCE_CUT${n}_ROOT=$(readlink -f ~/d/beliefs)/.work/acceptance/cut$n; done
test -x ~/d/beliefs/.work/acceptance/detached.sh
setsid nohup ~/d/beliefs/.work/acceptance/detached.sh ~/d/beliefs/.work/acceptance/cut41-runner.log uv run --frozen python tools/cut41_acceptance.py > /dev/null 2>&1 &
sleep 2; echo "runner process group $(cat ~/d/beliefs/.work/acceptance/cut41-runner.log.pid)"
```
If the turn ends before the wrapper does, report that process group and the stop command, `kill -TERM -- "-$(cat ~/d/beliefs/.work/acceptance/cut41-runner.log.pid)"`.

Read the log at exit. Expected tail:
- three `[cut41 phase n/3]` lines;
- `declared arms: 12 (= 12 declaration units; 5 guarantee rows)`;
- the rows-exercised line;
- exit 0, with every arm `sound` and every check `resolved`.

A `stale` verdict means a `before` no longer matches: fix the source's spelling back to Task 3's, never the frozen declaration. An arm that is not `sound` (its check passes under its sabotage) is rehomed, never dropped: append a dated `## 8. Supplement` to the cut document naming the arm, the reshaped sabotage or check and why, update the declaration and `CUT41_DECLARATION_SHA256` to match, and rerun. §§2–7 stay byte-exact.

- [ ] **Step 6: Commit**

```bash
tasks done <Task 5's id> "N2 declaration, guard, runner, recent-cut row; the cut ran sound"
tasks check && git add python/tests/n2_arms_cut41.py python/tests/acceptance/n2_arms_cut41.py python/tests/acceptance/test_n2_cut41.py python/tools/cut41_acceptance.py python/tests/test_recent_cut_acceptance.py tasks
git commit -m "test(cut41): N2 declaration, guard, runner and the recent-cut row — Z1–Z5"
```

---

### Task 6: The reproduction re-run

**Files:**
- Modify: `docs/designs/2026-09-05-mm30-reproduction.md` (append the next addendum section)

- [ ] **Step 1: Run.**
  1. `export SCIENCE_MM30_ROOT=$(readlink -f ~/d/beliefs)/.work/reproduction/mm30`, then `test -f "$SCIENCE_MM30_ROOT/state.json"` and copy that file to the scratchpad.
  2. From `python/`, run `PYTHONPATH=tools uv run --frozen python -m reproduction.preflight`, which must say `ok`. On a host-load refusal, `tasks park <Task 6's id> "rerun reproduction.preflight then reproduction.rederive" --reason quiet --waiting-on user --minutes 5`.
  3. Run `PYTHONPATH=tools uv run --frozen python -m reproduction.rederive`.
  4. `grep -n 'evaluate_query\|selection\|live' python/tools/reproduction/*.py` shows what the driver reaches. Expected: nothing of this slice.

- [ ] **Step 2: Append the addendum** on §19's shape (`sed -n '/^## 19\./,$p' docs/designs/2026-09-05-mm30-reproduction.md`), numbered after the last section present, titled `Addendum — live view-query evaluation, <date>`:
- what changed: `evaluate_live_query` and the shared denotation core, neither reached by the driver;
- what the re-run reached: the same `NoBelief` payload, `rederived_equal: true`, and `state.json` byte-identical (the diff and both SHA-256s);
- what it does not claim: mm30's driver evaluates no view query.

```bash
cd python && uv run --frozen pytest tests/test_reproduction_driver.py tests/test_designs_corpus.py -q
cd .. && tasks done <Task 6's id> "reproduction re-run: nothing moves"
tasks check && git add docs/designs/2026-09-05-mm30-reproduction.md tasks
git commit -m "docs(reproduction): re-run under live view-query evaluation; nothing moves"
```

---

### Task 7: Whole-branch review and the gate

- [ ] **Step 1: Review.** Run `superpowers:requesting-code-review` over `git diff main...HEAD`, against this plan's Global Constraints and the cut document's §5 and §6. Land each fix as its own commit, and list each for the results record's §3. A fix that moves a Task 3 spelling reruns Task 5 Step 5.

- [ ] **Step 2: The gate, detached**

```bash
cd ~/d/beliefs/.worktrees/live-query && cd "$(pwd -P)"
export SCIENCE_MM30_ROOT=$(readlink -f ~/d/beliefs)/.work/reproduction/mm30
for n in $(seq 4 41); do export SCIENCE_CUT${n}_ROOT=$(readlink -f ~/d/beliefs)/.work/acceptance/cut$n; done
export SCIENCE_CUT13_ROOT=$(readlink -f ~/d/beliefs)/.lifecycle-wrappers-test
setsid nohup ~/d/beliefs/.work/acceptance/detached.sh ~/d/beliefs/.work/acceptance/cut41-gate.log just gate > /dev/null 2>&1 &
sleep 2; echo "gate process group $(cat ~/d/beliefs/.work/acceptance/cut41-gate.log.pid)"
```
Read the log at exit. Expected: the pytest summary line with zero failures, and the TypeScript suite green.

- [ ] **Step 3: Record**

```bash
tasks done <Task 7's id> "whole-branch review landed; gate green"
tasks check && git add tasks && git commit -m "chore(tasks): cut 41 review and gate"
```

---

### Task 8: The results record, the re-rank, the amendments; close and merge

**Files:**
- Create: `docs/plans/<date>-conformance-cut-41-results.md`
- Modify: the cut document (`**Status:**`), the design (`**Status:**`), `docs/designs/2026-08-31-coordination-and-view-kinds-design.md` (§6.2), the ledger, the roadmap, `python/tools/roadmap_status.py`, `docs/guide/contracts-and-adoption.md`, `README.md`, tasks

- [ ] **Step 1: The results record**, on cut 40's shape (`docs/plans/2026-09-24-conformance-cut-40-results.md`):
- **§1, what ran:** the runner's summary lines verbatim, and the per-unit table.
- **§2, accounting:** 12 arms, 12 units, 5 rows; Z1–Z5 closed; the corpus total (`roadmap_status.py`'s last line after Step 2).
- **§3, evidence:** the design's planning notes (§8) and any deviation from this plan; Task 4's fixture fixes; Task 7's review fixes; the inventories unchanged (no new write entry point, no `atoms` import); the stale-arm probe clean, with cut 28's W7 spellings each once.
- **§4, the reproduction:** Task 6's addendum.
- **§5, `## Remaining boundary`:** what stays open elsewhere, named by row (the guard reads its labels and requires each in the ledger's Current state): L1 under `persistence-cut`, T7 under `cross-root-publication`, and `publish`'s remote slice with the rows it appends.
- **§6, main integration:** filled at merge.
- **§7, execution rulings:** the Task 0 Step 1 case.

- [ ] **Step 2: `roadmap_status.py`.** Add `41: ("conformance-cut-41-results §2", "Z1, Z2, Z3, Z4, Z5", ""),` after the highest existing entry, then regenerate Appendix A with `cd python && uv run --frozen python tools/roadmap_status.py`.

- [ ] **Step 3: Ledger and roadmap.** Follow cut 31's discharge commit (`git show 61a6f95 -- docs/designs/2026-08-03-redesign-adoption-ledger.md docs/plans/2026-08-29-implementation-roadmap.md`): `live-query` enters and closes in this commit, so neither table carries an open row for it.
  - **Ledger `Current state`:** an `**Updated <date>**` paragraph and a built bullet, "**Live attention reads** — `evaluate_live_query` denotes a view query over every admitted corpus's current state, captured corpus by corpus inside each hold and stamped by those states, never an epoch; Z1–Z5 close (cut 41)"; "Implemented through conformance cut 41"; the totals. The boundary table is unchanged.
  - **Roadmap:** `**Ranked at:** cut 41` (under rule 2, if a higher-numbered results record already landed, rebase and re-rank against it); a `**Cut 41 (<date>) discharges live view-query evaluation and closes the boundary**` paragraph on cut 31's shape, recording that `live-query` entered and closed at this record, that it was opened off the path under rule 6, and that it re-ranks nothing on the path; the boundary index's opening sentence extended to name `live-query` beside `estimand-typing` and `composite-claims`; the accounting paragraph; Appendix A pasted; Appendix B unchanged, since no row stays open.

- [ ] **Step 4: Amendments.**
  - `docs/designs/2026-08-31-coordination-and-view-kinds-design.md` §6.2: after the two regimes, the design's §5 paragraph verbatim, dated to the discharge (`> *Amended <date> (\`beliefs-cc0aea\`, conformance cut 41).* A third regime, attention reads: …`).
  - The design's Status: `discharged at conformance cut 41 on <date>; results: \`../plans/<date>-conformance-cut-41-results.md\``.
  - The cut document's Status: `discharged <date> on the certified volume; results: …`.
  - README: "through **cut 41**", its cut-41 row's wording, and "The latest discharged boundary is cut 41"; the guide's cut-41 line as discharged.

- [ ] **Step 5: Close in the results record's commit**

```bash
cd python && uv run --frozen pytest tests/test_designs_corpus.py tests/test_check_guide.py -q && cd ..
tasks done <Task 8's id> "results record, re-rank at cut 41, amendments"
tasks done beliefs-cc0aea "cut 41 discharged: Z1–Z5 — evaluate_live_query over every admitted corpus, stamped by its capture"
tasks check && git add docs python/tools/roadmap_status.py README.md tasks
git commit -m "docs(cut41): results record, re-rank at cut 41, Z1–Z5 closed"
```

- [ ] **Step 6: Merge and tell science**

```bash
cd ~/d/beliefs && git merge --no-ff design/live-query -m "merge: live view-query evaluation — conformance cut 41"
tasks note sci-f95f8b "beliefs-cc0aea landed (cut 41): beliefs.world.live.evaluate_live_query(world, query) -> LiveSelection; render complete, absent and stamp (CaptureStamp: world_id, coverage)."
```
Fill the results record's §6 in a `docs(cut41): record merged-main verification` commit. Then run `tt-report` (ops) to harvest the worktree's timing log, check that no host pointer resolves into the worktree (`readlink -f ~/bin/* ~/.local/bin/* 2>/dev/null | grep live-query` prints nothing), and remove it: `git worktree unlock .worktrees/live-query && git worktree remove .worktrees/live-query && git branch -d design/live-query`.

---

## Self-review

**Spec coverage.**

| Spec section | Where it is built |
|---|---|
| §1 | the file map; Task 0's cut document §1 |
| §2 decision 1 | Task 3 (`evaluate_live_query`; `_LiveCapture` private) |
| §2 decision 2 | Task 2 |
| §2 decision 3 | Task 3's `_coverage`; Z1-a–Z1-d; Review Focus 4 |
| §2 decision 4 | `_LiveCapture._located_state`; Z1-c |
| §2 decision 5 | Task 3's `_capture`; Z2-a, Z2-b |
| §2 decision 6 | Task 3's `_address_map`; the coordination-records test; Review Focus 1 |
| §2 decision 7 | Task 3's `_address_map` and `_require_unmapped_uids_unique`; Z5-a–Z5-c |
| §2 decision 8 | Task 3's `_capture`; Z4-a, Z4-b, and the two-damaged test |
| §2 decision 9 | Task 1 |
| §2 decision 10 | Tasks 0 and 5 |
| §3, API and the seven-step order | Tasks 2 and 3; the stamp from in-hold states is Z3-a |
| §4 | Task 1 Step 6 and Task 5 Step 5 (slice 4 and cut 28 unmodified) |
| §5 | Task 8 Step 4 |
| §6.1 | Task 2 |
| §6.2 | Task 4 (twelve units and seven other tests) |
| §6.3 | Tasks 0 (bank and paper audit) and 5 (declaration) |
| §6.4 | Tasks 0 (numbering, cut document) and 5 (runner, recent-cut row), and Task 8 (results record) |
| §6.5 | Tasks 1, 3 and 5 (`test_arm_staleness.py`, slice 4's acceptance) |
| §7 | Task 8 Steps 3 and 6 |

**Placeholders.** Four places defer a spelling to the tree by instruction, each with the command that settles it: the freeze hash and digests (Task 0 Step 5 → Task 5 Step 2), the prior declaration pins (Task 5 Step 2's `git log`), the corpus totals (Task 0 Step 3's script and `roadmap_status.py`), and the reproduction section number (Task 6 Step 2). Task 0 Step 1 rechecks the number at the freeze and stops on any conflict.

**Type consistency.**
- `CaptureStamp(world_id: str, coverage: tuple[tuple[str, str], ...])`; `LiveSelection(stamp, query, selected, contributing, absent, unresolved)` with `complete`, `projection()`, `identity()`; `LIVE_SELECTION_VERSION`.
- `evaluate_live_query(world: registry.World, query: ViewQuery) -> LiveSelection`.
- `_denoted(view: _QueryableView, query: ViewQuery) -> _Denotation(selected, contributing, unresolved)`; `LocatedState`; `WorldReadView._located_state(ref)`; `RelationView`.
- Private helpers in `live.py`: `_coverage(world) -> (carriers, absent)`, `_capture(carriers) -> (captured, states, damaged)`, `_address_map(captured, states)`, `_require_unmapped_uids_unique(captured)`, `_inbound(recorded, held)`, `_LiveCapture(recorded, held, inbound)`. Task 5's twelve `before` strings are copied from Task 3's code and checked by Task 3 Step 4.

**Review Focus.** All five lines have their test in Task 3.

## Plan review log

- 2026-09-24 — drafted. Resolved at planning and recorded for the design's §8 (Task 0 Step 3): table Z's owner is the moved design; `LocatedState` lives in `view.py`; `RelationAdjacency` is typed over `RelationView`; no new error class; the arms audited on paper at the freeze, since a cut is frozen before its code exists, with the executable audit and any rehoming at Task 5. Cut numbering follows rules 1 and 5 by Task 0 Step 1's three cases; the unfrozen-cut-41 case is the user's decision.
- 2026-09-25 — user review: freeze as **cut 41** with prefix cut 40, and relabel the remote publish slice's current references to planned cut 42 at the freeze, keeping historical cut bodies byte-exact (Task 0 Step 1, which rechecks the number first). Z2-b also wraps `ReadView.iter_stored`, reading the holder at each record as the evaluation consumes it, because enumeration reads the store separately from the open. The accounting stays 12/12/5.
