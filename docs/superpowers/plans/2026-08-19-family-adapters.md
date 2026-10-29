# Family Adapters Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement Plan B item 2 — the supersede/revise, retraction, and explicit-import families on `CorpusWriter`, with conformance cut 5 frozen prospectively and discharged on the certified engine.

**Architecture:** Three new mutation families become entry points on the existing `CorpusWriter` (Approach A), each serialized end-to-end under a new process-global root-keyed operation lock and compiling into `nodes` `WritePlan`s executed by the certified `atoms` engine through `science.root`. Import is the one boundary operation: durable operation intent → one payload transaction → a separate act-report transaction carrying `fulfills`. Docs first: cut 5 freezes (with second reader) and the design banks **before** any implementation task runs.

**Tech Stack:** Python 3.12, `nodes-core` (WritePlan seam), `atoms-core` (certified engine, `append_intent`, `build_spec`), pytest, the repo's N2 arm harness.

**Spec:** `docs/superpowers/specs/2026-08-19-family-adapters-design.md` — Task 3 moves it to `docs/designs/2026-08-19-family-adapters-design.md`; from Task 5 on, read it there. Read it in full before any task; every task below argues from it.

## Global Constraints

- **Docs before code:** Tasks 1–4 (cut-5 authoring, second reader, banking, atoms amendment) MUST complete before Tasks 5+. Cut 5 is frozen prospectively; implementation against an unfrozen cut is the failure the freeze discipline exists to prevent.
- **No `atoms` import outside `science/root.py`** (architecture rule, tested by `test_capability_boundary.py`).
- **No mutable `Corpus` outside `science/corpus.py`** (S8, AST-checked).
- **Every corpus-domain refusal is a `WriteRefused` subclass; engine failures cross only as `PlanRefusedError`/`ExecutionError`** (spec §6).
- **Conventional commits; no AI-attribution trailers.**
- **The `revise` allowlist is exactly `title`, `body`, `display.display_statement` — for propositions only** (spec §4.2).
- **Import refusal after intent append publishes a refusal report that fulfills the intent, then raises** (spec §5.4/§6).
- **Portable tests run anywhere; durable arms run only under the cut-5 acceptance runner, which errors off the certified tuple and never skips. `python/tools/cut4_acceptance.py` is never edited** (spec §9).
- **Timestamps are caller-supplied strings; event tokens are `secrets.token_hex(16)`** (boundary.py precedent).
- Run tests from `python/`: `uv run pytest tests/<file> -q` (or plain `pytest` if the venv is active).
- **Commits stage explicitly.** Every commit step means `git add <each created or modified path>` then `git commit -m "..."` — never `-a`/`-A`, which misses untracked files and over-stages sibling work.
- **Family-owned kinds are reserved from `add`**: `CorpusWriter.add` refuses `retraction` (enters only through `retract`) and `act-report` (minted only by the boundary; stored only by import) — spec T1's no-construction-path claim, enforced at the one public mint.

---

### Task 1: Author conformance cut 5

**Files:**
- Create: `docs/designs/2026-08-19-conformance-cut-5.md`
- Read first: `docs/designs/2026-08-17-conformance-cut-4.md` (the form to follow), spec §8, `docs/designs/2026-08-03-correction-lifecycle-design.md` §7b (C-row texts), `docs/designs/2026-08-02-substrate-consolidation-design.md` (S2/S3/S4 row texts), `docs/designs/2026-08-02-epistemic-kernel-design.md` (G7, G2c, G8), `docs/designs/2026-08-04-formal-model-and-claim-calculus-design.md` (M3, M5), `docs/designs/2026-08-11-act-report-design.md` (T1, T2), `docs/designs/2026-08-11-conformance-cut-3.md` §4 (T-row splits as cut 3 left them).

**Interfaces:**
- Produces: the frozen selection every later task's tests discharge; the arm inventory Task 15's N2 declarations enumerate.

**Steps:**

**Historical drafting instruction:** The steps below preserve the prospective
selection before either post-freeze feasibility correction. Current execution
uses the corrected inventory stated after Task 2 and in Tasks 17 then 16.

- [ ] **Step 1: Write the cut document** following cut 4's structure: §1 what this cut is, §2 the in-scope boundary declaration (the three families, the lock registry, the display facet, the stored retraction/act-report kinds, the read-side evaluators, the acceptance runner — and the explicit out-list: world index, audit, holdings root, anchor acts, consolidate/move/deletion, rules store, registry compile), §3 the selection with **exact arm splits against each frozen row's full text**, §4 accounting, §5 N2 obligations, §6 the second-reader protocol, §7 limitations.
- [ ] **Step 2: The selection must contain exactly** (spec §8): S2, S4, G7, M5 for supersede/revise; S3 whole, T1's import arm, T2's persistence-deferred import arms, the six locally runnable M3 arms (termination over an admissible local state; cycle witness; bundle-only cycle; bundle-plus-local-context cycle; refusal with no payload write; ordinary-write target resolution in C10's termination role), and the corpus-local explicit-import clauses of R19, R20, R22, R23 for import; the corpus-local arms of C1–C10 plus the positive retraction arms of G2c and G8 for retraction. Quote each row's frozen text and mark every clause **selected / part / deferred** with the deferral's unblocker named. Per the standing classification rule: any unrun arm makes the row **part**, and there is no "full" on an argument for why an arm shouldn't count — the error always runs toward overstating coverage.
- [ ] **Step 3: Status header** says "Drafted 2026-08-19, awaiting second reader; NOT frozen." Nothing downstream may treat it as frozen yet.
- [ ] **Step 4: Commit** — `git add docs/designs/2026-08-19-conformance-cut-5.md && git commit -m "docs: draft conformance cut 5 for the family adapters"`.

---

### Task 2: Second reader over cut 5

**Files:**
- Modify: `docs/designs/2026-08-19-conformance-cut-5.md`

**Steps:**

- [ ] **Step 1: Dispatch a fresh reviewing agent** with ONLY: the banked row texts it names, the spec, and cut 5's §2 boundary declaration. Instruct it to attack **toward overstated coverage**: every selected clause must be checkable entirely inside §2's in-scope list; flag any clause that quietly reaches the world index, audit, holdings, anchor carriage, or a deferred family; flag any C-row arm whose text requires world standing rather than `standing_in_local_view`; check the R19/R20/R22/R23 splits against spec §8's narrowing rule (the validation promise narrows, the selection never expands).
- [ ] **Step 2: Close every finding in the document** — move overstated clauses to part/deferral, record the reader's run and dispositions in §6.
- [ ] **Step 3: Commit** — `git add docs/designs/2026-08-19-conformance-cut-5.md && git commit -m "docs(cut5): close the second reader's findings"`.

**First post-freeze correction (historical):** The original reader correctly demoted R23 but
missed that R19 and R22 require semantic evidence absent from the persisted
projections and `import_bundle(Sequence[Node])`. Task 15's later feasibility
audit narrowed both rows to deferred. The corrected inventory is **8 full + 10
part + 6 deferred = 24**, with **31** Selected declaration units.

**Second post-freeze correction:** Task 16's feasibility review deferred T2's
second-fulfillment classification because no durable-log consumer/classifier
exists, and deferred M3's bundle-only and bundle-plus-local concrete cycle arms
because controlled content-derived identities make those cycles unspellable.
T2 retains success, refusal, and intent-failure; M3 retains the direct abstract
witness, forced-verdict consumption, local-DAG termination, and ordinary
unresolved-target arms. Row accounting remains **8 full + 10 part + 6 deferred
= 24**; the current inventory is exactly **28** Selected declaration units.

---

### Task 3: Bank the design and freeze cut 5

**Files:**
- Create: `docs/designs/2026-08-19-family-adapters-design.md` (via `git mv` — see Step 1)
- Modify: `docs/designs/2026-08-19-conformance-cut-5.md` (status → frozen, dated), `docs/designs/2026-08-03-redesign-adoption-ledger.md` (row 4's Plan B note; order-of-work item 5; affected "waits on" cells), `README.md` (design count/table/date), `python/tests/test_designs_corpus.py` (`_COUNT_WORDS` — that is where the guard lives, **not** `check_guide.py`), `docs/guide/open-questions.md` (if it names item 2 as open)

**Steps:**

- [ ] **Step 1: Promote the spec by `git mv`** — `git mv docs/superpowers/specs/2026-08-19-family-adapters-design.md docs/designs/2026-08-19-family-adapters-design.md` — never by copy: the spec prohibits a permanent duplicate, and a moved file leaves no second authority behind. Update the moved file's status to "Banked 2026-08-19; implementation in progress on `design/family-adapters`", and correct its §9 "twenty-fifth design" sentence to the true count (26 — cut 5 lands beside it).
- [ ] **Step 2: Freeze cut 5** in the same change: status → "Frozen 2026-08-19, second reader discharged".
- [ ] **Step 3: Ledger updates**: §1 row 4 note (item 2 design banked; recast recorded), §3 item 5 (remaining Plan B surface = implementation of item 2, then the deferred consolidate/move/deletion cut), any "waits on" cells naming the family surface.
- [ ] **Step 4: Guard propagation**: the tree holds 24 design documents before this task; Task 1 added cut 5 and Step 1 adds the family design, so the count the guards must carry is **26** — verify against what `python/tests/test_designs_corpus.py` actually counts (its rule, not this plan's arithmetic, is the authority), extend `_COUNT_WORDS` with the entries the new count needs (`25: "Twenty-five"`, `26: "Twenty-six"` as applicable), update the README count/table/date, then run `uv run pytest tests/test_designs_corpus.py -q` and `uv run python tools/check_guide.py` from `python/` until both are clean.
- [ ] **Step 5: Commit** — `git add docs/designs/2026-08-19-family-adapters-design.md docs/designs/2026-08-19-conformance-cut-5.md docs/designs/2026-08-03-redesign-adoption-ledger.md docs/guide/open-questions.md README.md python/tests/test_designs_corpus.py && git commit -m "docs: bank the family-adapters design and freeze conformance cut 5"`.

---

### Task 4: The atoms amendment

**Files:**
- Modify: `<atoms checkout>/docs/plans/2026-07-23-recoverable-fs-effect-engine-design.md` §12.2 and §14 (a separate repo; its own commit there)

**Steps:**

- [ ] **Step 1: Add a dated amendment note** (do not rewrite the original sentences; append `*(amended 2026-08-19 …)*` markers in both sections): science's Plan B item 2 recast under the clean start per `science`'s `2026-08-19-family-adapters-design.md` — the family list is supersede, retraction, and explicit import; planner/Gate-B lapse with the save/apply boundary that no longer exists; dialect deletion discharged by the clean start; archive/cohort require their own designs; the hard cut's surviving claim is "every Science corpus mutation flows through the certified engine".
- [ ] **Step 2: Commit in the atoms checkout** — `git -C <atoms checkout> add docs/plans/2026-07-23-recoverable-fs-effect-engine-design.md && git -C <atoms checkout> commit -m "docs: record science's Plan B item 2 recast (2026-08-19)"`.

---

### Task 5: The display facet

**Files:**
- Modify: `python/src/science/stored.py`
- Test: `python/tests/test_stored.py` (or the existing stored-node test module — find it with `grep -rl proposition_node python/tests`)

**Interfaces:**
- Produces: `stored.DISPLAY_FACET = "display"`; `proposition_node(slug, *, title, claim, display_statement: str | None = None)`; `stored.display_statement(node) -> str | None`; `stored.display_facet_malformed(node) -> bool`.

**Steps:**

- [ ] **Step 1: Write the failing tests**

```python
def test_display_statement_stored_uncovered():
    node = stored.proposition_node("p1", title="t", claim={"op": "affects"},
                                   display_statement="In adults, X affects Y.")
    assert stored.display_statement(node) == "In adults, X affects Y."
    assert "display" not in stored.COVERED_FACETS["proposition"]
    # the stamp is identical with and without the display facet
    bare = stored.proposition_node("p1", title="t", claim={"op": "affects"})
    assert stored.stored_semantic_hash(node) == stored.stored_semantic_hash(bare)

def test_display_facet_shape_is_validated():
    node = stored.proposition_node("p1", title="t", claim={"op": "affects"})
    raw = node.model_copy(update={"facets": {**node.facets, "display": {"extra": 1}}})
    assert stored.display_facet_malformed(raw)
```

- [ ] **Step 2: Run to verify failure** — `uv run pytest tests -k display -q` → FAIL (no `display_statement` parameter).
- [ ] **Step 3: Implement**: `DISPLAY_FACET = "display"`; the facet is `{"display_statement": <str>}` exactly, absent when unauthored; `display_facet_malformed` is True when the facet exists and is not exactly that one-string-field shape. Never touch `COVERED_FACETS`. Wire it into the write boundary in the same task: `CorpusWriter._refuse` gains a check raising `ValidationRefused` on a malformed display facet, so ordinary `add` (and later `revise`) cannot admit one — a validator no write path consults is not a boundary. Test: `writer.add(<node with malformed display facet>)` raises `ValidationRefused`.
- [ ] **Step 4: Run to verify pass**, then run the full portable suite: `uv run pytest tests -q`.
- [ ] **Step 5: Commit** — `git add python/src/science/stored.py python/src/science/corpus.py python/tests/test_stored_display.py && git commit -m "feat(stored): give display_statement its uncovered facet home"`.

---

### Task 6: The root-keyed operation-lock registry

**Files:**
- Modify: `python/src/science/corpus.py`
- Test: `python/tests/test_corpus_write.py`

**Interfaces:**
- Produces: a private module-level registry `_root_state_for(root: Path, executor_factory) -> _RootState`, where `_RootState` holds `lock: threading.Lock`, `corpus: Corpus`, `view: ReadView`, and the `executor_factory` it was built with; `CorpusWriter` keeps `self._operation` (the shared lock) and reads `self._corpus`/`self._view` **through the shared state**, so two writers on one root share the lock *and* the live index — a lock over independently cached `Corpus` instances would serialize stale reads and still admit duplicate uids at different paths.

**Steps:**

- [ ] **Step 1: Write the failing tests** (beside the existing lock test in `test_corpus_write.py`, reusing its `Recorder`/barrier pattern):

```python
def test_two_writers_one_root_share_lock_and_state(tmp_path):
    Recorder.plans = []
    a = CorpusWriter(tmp_path, Recorder)
    b = CorpusWriter(tmp_path, Recorder)
    assert a._operation is b._operation
    minted = a.add(prop("p"))
    assert b.read_view.holds(minted.id)          # b sees a's mint without reconstruction
    other = CorpusWriter(tmp_path / "other", Recorder)
    assert other._operation is not a._operation

def test_second_writer_with_different_factory_refuses(tmp_path):
    CorpusWriter(tmp_path, Recorder)
    with pytest.raises(ScienceError):
        CorpusWriter(tmp_path, DefaultExecutor)

def test_open_corpus_twice_shares_state(tmp_path):
    # durable-factory identity is stable: repeated open_corpus on one root must
    # share state, never refuse (root.durable_executor_factory returns one
    # module-level callable, not a fresh closure per call). Construction alone
    # touches no engine, so this runs portably with no init_corpus_root.
    a = open_corpus(tmp_path)
    b = open_corpus(tmp_path)
    assert a._operation is b._operation
```

Also extend the existing deterministic concurrent-add test to drive its two adds through **two different writer instances** on the same root and assert the same serialization outcome (the second add observes the first's mint through the shared index and raises `RecordAlreadyMinted`/`CollisionRefused`; exactly one plan reaches the executor).

- [ ] **Step 2: Run to verify failure** — the two writers currently hold distinct locks and distinct `Corpus` instances.
- [ ] **Step 3: Implement**: a module-level `dict[str, _RootState]` guarded by one `threading.Lock`, keyed on `str(Path(root).resolve())`. First construction for a root builds the `Corpus` and stores the factory; a later construction with a **different** factory refuses loudly (a `ScienceError` — two executors for one root is a wiring bug, not a fallback case). Identity must be stable across `open_corpus` calls: `root.durable_executor_factory()` currently mints a fresh closure per call, so this task also makes it return one **module-level stable callable** (the backend/storage bindings are module constants; nothing needs a per-call closure). Test: two `open_corpus(tmp_path)` calls on one root succeed and share state — the durable factory's identity is the same object both times. Import's post-payload reconstruction (Task 15) replaces `corpus`/`view` **inside the shared state**, under the lock, so every writer sees the reconstruction.
- [ ] **Step 4: Run the full portable suite.**
- [ ] **Step 5: Commit** — `git add python/src/science/corpus.py python/tests/test_corpus_write.py && git commit -m "feat(corpus): one shared lock and one live index per corpus root"`.

---

### Task 7: `supersede`

**Files:**
- Modify: `python/src/science/errors.py`, `python/src/science/stored.py` (predicate constant), `python/src/science/corpus.py`
- Test: `python/tests/test_supersede.py` (new)

**Interfaces:**
- Consumes: Task 5's display facet (successors may carry one), Task 6's shared lock.
- Produces: `stored.SUPERSEDES = "supersedes"`; errors `SupersedeTargetMissing(WriteRefused)`, `SupersedeIdentityUnchanged(WriteRefused)`, `FamilyKindUnsupported(WriteRefused)`; `CorpusWriter.supersede(self, successor: Node, *, of: str) -> Node`.

**Steps:**

- [ ] **Step 1: Write the failing tests** (fixtures per `test_corpus_write.py`'s `writer`/`Recorder` pattern; propositions via `stored.proposition_node`):

```python
def prop(slug, claim_op="affects"):
    return stored.proposition_node(slug, title=slug, claim={"op": claim_op})

def test_supersede_mints_successor_and_edge(writer):
    old = writer.add(prop("in-adults"))
    new = writer.supersede(prop("in-all-humans", claim_op="causes"), of=old.id)
    assert any(r.predicate == "supersedes" and r.target == old.id for r in new.relations)
    # predecessor byte-untouched: the plan for the supersede is create-only
    assert all(isinstance(op, CreateOp) for op in Recorder.plans[-1])
    assert writer.read_view.get(old.id).facets == old.facets  # prior refs unmoved

def test_supersede_refuses_missing_predecessor(writer):
    with pytest.raises(SupersedeTargetMissing):
        writer.supersede(prop("s"), of="proposition:absent")

def test_supersede_refuses_equal_semantic_identity(writer):
    old = writer.add(prop("p"))
    with pytest.raises(SupersedeIdentityUnchanged):
        writer.supersede(prop("p-copy"), of=old.id)   # same claim → same identity

def test_supersede_refuses_caller_authored_edge(writer):
    old = writer.add(prop("p"))
    candidate = prop("q", claim_op="causes")
    candidate = candidate.model_copy(update={"relations": [
        Relation(source=candidate.id, predicate="supersedes", target=old.id)]})
    with pytest.raises(WriteRefused):
        writer.supersede(candidate, of=old.id)

def test_supersede_refuses_non_proposition(writer):
    src = writer.add(stored.source_node("s", title="s", identifiers={"doi": "10.1/x"}))
    with pytest.raises(WriteRefused):
        writer.supersede(prop("p2"), of=src.id)
```

- [ ] **Step 2: Run to verify failure** — `uv run pytest tests/test_supersede.py -q` → FAIL (`supersede` not defined).
- [ ] **Step 3: Implement** per spec §4.1's refusal order: under the lock — resolve `of` (else `SupersedeTargetMissing`); refuse a non-proposition predecessor or successor with a new `FamilyKindUnsupported(WriteRefused)`; refuse a fresh-pair violation via the existing `_refuse_already_minted`; refuse a caller-authored `supersedes` relation with `ValidationRefused` (spec §6: malformed shapes use the existing validation refusal); compare `stored.recompute_semantic_hash(successor)` against the predecessor's (equal → `SupersedeIdentityUnchanged`); construct the copy with the one adapter-authored `Relation(source=successor.id, predicate=stored.SUPERSEDES, target=<resolved live id>)` — no re-stamp: relations are outside the hash and the constructor's stamp is already correct; run `self._refuse(candidate)`; `return self._corpus.add(candidate)`.

  **Spec gap, close it here:** the banked design's §6 table has no name for supersede's kind refusal. Add one row — `FamilyKindUnsupported` | the family does not operate on this kind — to `docs/designs/2026-08-19-family-adapters-design.md` §6 in this task's commit, noted as a gap closure dated 2026-08-19, not a behavior change.
- [ ] **Step 4: Run to verify pass; run the full portable suite.**
- [ ] **Step 5: Commit** — `git add python/src/science/{corpus,stored,errors}.py docs/designs/2026-08-19-family-adapters-design.md python/tests/test_supersede.py && git commit -m "feat(corpus): supersede mints a successor and never touches the predecessor"`.

---

### Task 8: `revise`

**Files:**
- Modify: `python/src/science/errors.py`, `python/src/science/corpus.py`
- Test: `python/tests/test_revise.py` (new)

**Interfaces:**
- Consumes: Task 5's display facet; Task 7's `FamilyKindUnsupported`.
- Produces: errors `RevisionTargetMissing(WriteRefused)`, `ReviseKindImmutable(WriteRefused)`, `ReviseOutsideAllowlist(WriteRefused)`; `CorpusWriter.revise(self, node: Node) -> Node`.

**Steps:**

- [ ] **Step 1: Write the failing tests**

```python
def test_revise_prose_in_place_no_mint(writer):
    old = writer.add(stored.proposition_node("p", title="old", claim={"op": "affects"}))
    edited = old.model_copy(update={"title": "new title"})
    out = writer.revise(edited)
    assert (out.uid, out.id) == (old.uid, old.id)
    assert isinstance(Recorder.plans[-1][0], ReplaceOp)           # in-place
    got = writer.read_view.get(old.id)                            # G7 converse:
    assert stored.stored_semantic_hash(got) == stored.stored_semantic_hash(old)

def test_revise_display_statement_add_change_remove(writer): ...  # three calls, each passes

def test_revise_refuses_semantic_field_change(writer):
    old = writer.add(stored.proposition_node("p", title="t", claim={"op": "affects"}))
    edited = old.model_copy(update={"facets": {**old.facets,
        stored.PROPOSITION_FACET: {"op": "causes"}}})
    with pytest.raises(ReviseOutsideAllowlist):
        writer.revise(edited)

def test_revise_refuses_relation_change(writer): ...              # relations off-allowlist
def test_revise_refuses_missing_target(writer):                   # RevisionTargetMissing
    with pytest.raises(RevisionTargetMissing):
        writer.revise(stored.proposition_node("ghost", title="t", claim={"op": "affects"}))
def test_revise_refuses_non_proposition(writer):                  # ReviseKindImmutable
    src = writer.add(stored.source_node("s", title="s", identifiers={"doi": "10.1/x"}))
    with pytest.raises(ReviseKindImmutable):
        writer.revise(src.model_copy(update={"title": "x"}))
```

- [ ] **Step 2: Run to verify failure.**
- [ ] **Step 3: Implement** per spec §4.2: under the lock — the exact `(uid, id)` pair must exist (`RevisionTargetMissing`); kind must be `proposition` (`ReviseKindImmutable`); diff the candidate against the **stored** node: every field outside {`title`, `body`, the `display` facet} must be equal (`uid`, `id`, `kind`, metadata, relations, deprecated ids, every other facet including the covered one and the stamp) else `ReviseOutsideAllowlist`; validate the display facet shape if present (`ValidationRefused` on malformed); recompute the semantic digest and require it unchanged; then `return self._corpus.add(candidate)` — `nodes`' `add` selects `ReplaceOp` with `expected_digest` from its manifest for a matching live pair, which is the pre-plan-read digest spec §5.2 names. Do **not** route through `_refuse_already_minted`.
- [ ] **Step 4: Run to verify pass; full portable suite.**
- [ ] **Step 5: Commit** — `git add python/src/science/{corpus,errors}.py python/tests/test_revise.py && git commit -m "feat(corpus): revise replaces prose in place and mints nothing"`.

---

### Task 9: The stored retraction kind

**Files:**
- Modify: `python/src/science/stored.py`, `python/src/science/errors.py`
- Test: `python/tests/test_stored_retraction.py` (new)

**Interfaces:**
- Produces: `stored.RETRACTS = "retracts"`, `stored.GROUNDED_IN = "grounded-in"`, `stored.SUCCEEDED_BY = "succeeded-by"` — **hyphens, exactly**: the formal model's frozen vocabulary warns that an underscore spelling mints an unrelated predicate; `stored.RETRACTION_FACET = "retraction"`, `stored.RETRACTION_REASONS = ("authored-error", "corrupt-input", "defective-code", "environment-miscapture", "false-certification", "upstream-retraction", "wrong-route")`; frozen dataclasses `stored.NodeTarget(ref: str, resolved: str, content_identity: str)` and `stored.RouteTarget(dataset: str, resolved: str, content_identity: str, route_identity: str)`; constructor `stored.retraction_node(*, title, target: NodeTarget | RouteTarget, reason: str, rationale: str, grounds: Sequence[str], actor: str, event_token: str, successor: str | None = None) -> Node` — **no caller-selected slug**: the id is content-derived, `retraction:<the complete 64-hex v1.digest("science.retraction.v1", <the facet's identity mapping>)>` — the full digest, never a prefix: a truncated address is not the ruled content identity, so two retractions of one target by one actor for two reasons are two records and repetition never collides an address; `SEMANTIC_DOMAINS` and `COVERED_FACETS` gain `"retraction"` (`"science.retraction.v1"`, facet-covered).

**Steps:**

- [ ] **Step 1: Write the failing tests**

```python
def test_retraction_node_derives_relations_from_one_argument():
    node = stored.retraction_node(title="r",
        target=stored.NodeTarget("assessment:a1", "assessment:a1", "sha256:" + "ab"*32),
        reason="defective-code", rationale="why", grounds=("verification:v1",),
        actor="keith", event_token="tok")
    predicates = {(r.predicate, r.target) for r in node.relations}
    assert ("retracts", "assessment:a1") in predicates
    assert ("grounded-in", "verification:v1") in predicates
    assert not stored.semantic_hash_missing(node)      # governed and stamped
    facet = node.facets[stored.RETRACTION_FACET]
    assert facet["reason"] == "defective-code" and facet["event_token"] == "tok"

def test_retraction_id_is_content_derived():
    a = retraction(..., event_token="tok-1"); b = retraction(..., event_token="tok-1")
    assert a.id == b.id                                # same basis → same address
    c = retraction(..., event_token="tok-2")
    assert c.id != a.id                                # the token is in the basis

def test_retraction_reason_outside_closed_vocabulary_refuses():
    with pytest.raises(MalformedRecord): stored.retraction_node(..., reason="vibes", ...)

def test_retraction_empty_grounds_refuses():                       # MalformedRecord
def test_route_target_carries_route_identity():                     # facet round-trips it
def test_successor_derives_succeeded_by_relation():                 # optional arm, "succeeded-by"
```

- [ ] **Step 2: Run to verify failure.**
- [ ] **Step 3: Implement**: the facet carries the discriminated target (a `"target"` mapping with an `"arm"` key of `"node"` or `"route"` plus that arm's fields), `reason`, `rationale`, `grounds` (non-empty list), `actor`, `event_token`, optional `successor`. The constructor writes facet and relations from the same arguments (spec §3.3: they cannot diverge), **derives the slug from the facet's identity** (the complete `v1.digest("science.retraction.v1", facet_mapping)`, untruncated) so the address is content-derived, and stamps via `stamp_semantic_identity`; the whole retraction facet is covered — add `"retraction": (RETRACTION_FACET,)` to `COVERED_FACETS` and the domain to `SEMANTIC_DOMAINS`. Malformed inputs (unknown arm, unknown reason, missing attribution, no grounds, non-string rationale) raise `MalformedRecord` — the existing record vocabulary, per spec §6.
- [ ] **Step 4: Run to verify pass; full portable suite.**
- [ ] **Step 5: Commit** — `git add python/src/science/{stored,errors}.py python/tests/test_stored_retraction.py && git commit -m "feat(stored): the retraction kind, facet-covered, relations derived from one argument"`.

---

### Task 10: `retract`

**Files:**
- Modify: `python/src/science/errors.py`, `python/src/science/corpus.py`
- Test: `python/tests/test_retract.py` (new)

**Interfaces:**
- Consumes: Task 9's constructor and constants.
- Produces: errors `RetractionTargetIneligible(WriteRefused)`, `RetractionTargetUnresolvable(WriteRefused)`, `RetractionGroundsMissing(WriteRefused)`; `CorpusWriter.retract(self, record: Node) -> Node`; module constant `ELIGIBLE_RETRACTION_TARGET_KINDS = ("assessment", "retraction", "verification")` (the node-arm kinds this corpus stores; snapshots and instrument-certifications join when their stored kinds exist — the cut document says so).

**Steps:**

- [ ] **Step 1: Write the failing tests**

```python
def test_retract_is_create_only_and_target_untouched(writer):
    a = mint_eligible_assessment(writer)               # helper per test_corpus_write.py fixtures
    before = writer.read_view.get(a.id)
    out = writer.retract(retraction_for(a))
    assert all(isinstance(op, CreateOp) for op in Recorder.plans[-1])   # C1
    assert writer.read_view.get(a.id) == before                          # byte-identical, resolvable

def test_counter_retraction_targets_a_retraction(writer):               # chain, not toggle
def test_retract_refuses_unresolvable_target(writer):                   # RetractionTargetUnresolvable
def test_retract_refuses_ineligible_kind(writer):                       # a proposition target refuses
def test_retract_refuses_route_absent_from_stamped_basis(writer):       # RetractionTargetUnresolvable
def test_retract_refuses_missing_grounds(writer):                       # RetractionGroundsMissing

def test_add_reserves_family_owned_kinds(writer):
    # the bypass closure: a retraction handed to plain add refuses — retract is the one
    # entry that enforces C10/C2 — and an act-report kind refuses at add always
    with pytest.raises(WriteRefused): writer.add(valid_retraction)
    with pytest.raises(WriteRefused): writer.add(raw_act_report_shaped_node)
```

- [ ] **Step 2: Run to verify failure.**
- [ ] **Step 3: Implement** per spec §4.3's refusal order: under the lock — the record must be a well-formed stored retraction (kind, facet, stamp — `ValidationRefused`/`MalformedRecord` per existing vocabulary); target-arm and kind eligibility (`RetractionTargetIneligible`); node-arm target resolves in this corpus, route-arm dataset resolves and the named `route_identity` exists among `stored.basis_routes(dataset)`'s identities (`RetractionTargetUnresolvable`); grounds non-empty and each ground ref present as a string (`RetractionGroundsMissing` when empty); then the ordinary refusal set and the corpus add — `retract` calls the shared internals directly rather than the public `add`, because this task also adds the **family-kind reservation** to `add` itself: `_refuse_family_kinds` raises `WriteRefused` for kind `"retraction"` ("a retraction enters through retract") and `"act-report"` ("an act-report is minted by the boundary and stored by import") before every other add refusal, closing the bypass in which a caller-built retraction skips C10/C2 by using `add`. Resolution is the DAG-preservation rule; there is **no** graph scan here (spec §6 item 3).
- [ ] **Step 4: Run to verify pass; full portable suite.**
- [ ] **Step 5: Commit** — `git add python/src/science/{corpus,errors}.py python/tests/test_retract.py python/tests/test_corpus_write.py && git commit -m "feat(corpus): retract admits chained, additive retraction records"`.

---

### Task 11: Read side — supersession chase and local standing

**Files:**
- Modify: `python/src/science/corpus.py`, `python/src/science/errors.py`
- Test: `python/tests/test_local_standing.py` (new)

**Interfaces:**
- Produces: `superseded_by(view: ReadView, ref: str) -> tuple[str, ...]` (inbound `supersedes` sources, derived, unordered-then-sorted); `standing_in_local_view(view: ReadView, ref: str) -> bool`; error `RetractionCycleMalformed(ScienceError)`.

**Steps:**

- [ ] **Step 1: Write the failing tests**

```python
def test_superseded_by_is_derived_inbound(view_with_chain): ...
def test_standing_subtracted_by_one_standing_retraction(...):
    assert standing_in_local_view(view, target.id) is False
def test_counter_retraction_restores_iff_no_sibling_remains(...):      # C5's sibling rule
    # two retractions of one target; counter-retract one → still not standing;
    # counter-retract both → standing again
def test_raw_written_cycle_is_malformed_not_evaluated(tmp_path):
    # write two retraction files targeting each other behind the API, reload,
    with pytest.raises(RetractionCycleMalformed):
        standing_in_local_view(ReadView.opened_at(tmp_path), "retraction:r1")
```

- [ ] **Step 2: Run to verify failure.**
- [ ] **Step 3: Implement**: enumerate retraction ids via `iter_stored` (kind == "retraction") but **fetch each through `view.get`**, so an unstamped or stale retraction raises the facade's own `SemanticHashMissing`/`SemanticHashStale` — a malformed retraction must refuse the whole evaluation, never be skipped: silently ignoring one would let a corrupted stamp restore its target's apparent standing. A structurally malformed retraction facet likewise refuses (`MalformedRecord`). Only `corpus_check` (Task 12) converts these refusals into reported findings. Then build `target-ref → [retraction ids]` from node-arm facet targets resolved through the view; detect a cycle in the `target → retraction` orientation (iterative DFS) and raise `RetractionCycleMalformed` before any evaluation; otherwise evaluate the recursion (a retraction is standing unless a standing retraction targets it; the queried ref's standing is subtracted iff ≥1 standing retraction targets it). Route-arm targets do not subtract a node's standing (they name a route, not a record) — state that in the docstring, it is the cut's corpus-local narrowing. Update the cyclic raw-write test accordingly: its two raw-written retractions must be **self-consistently stamped** so the cycle — not a stale stamp — is what the evaluator refuses on.
- [ ] **Step 4: Run to verify pass; full portable suite.**
- [ ] **Step 5: Commit** — `git add python/src/science/{corpus,errors}.py python/tests/test_local_standing.py && git commit -m "feat(corpus): derived supersession chase and bounded local standing"`.

---

### Task 12: Corpus-check findings for the new raw-write shapes

**Files:**
- Modify: `python/src/science/corpus.py`
- Test: extend `python/tests/test_local_standing.py` and `python/tests/test_read_side.py` (the existing corpus-check tests)

**Interfaces:**
- Produces: new `Finding` codes emitted by `corpus_check`: `display-malformed`, `supersession-target-missing`, `retraction-target-invalid`, `retraction-cycle` (spec §7.3). Codes are Science-namespace strings; severity `"error"`; deterministic sort via the existing `sort_key`.

**Steps:**

- [ ] **Step 1: Write the failing tests** — one raw-write fixture per code, each writing bytes behind the API and asserting the finding appears in a **fresh** facade's `corpus_check` (the reconstruction rule in `corpus.py`'s module docstring): a malformed display facet; a `supersedes` relation to a ref the corpus does not hold; a stored retraction whose facet target arm is unknown or whose node target is unresolvable; the two-retraction cycle (which must be reported as `retraction-cycle`, not evaluated).
- [ ] **Step 2: Run to verify failure.**
- [ ] **Step 3: Implement** inside `corpus_check`'s single iteration pass, reusing Task 11's collection helpers; the cycle check runs once over the collected graph, reported (never raised) here.
- [ ] **Step 4: Run to verify pass; full portable suite.**
- [ ] **Step 5: Commit** — `git add python/src/science/corpus.py python/tests/test_local_standing.py python/tests/test_read_side.py && git commit -m "feat(corpus): report the family-era raw-write shapes"`.

---

### Task 13: The operation port — intent append and fulfilling execution

**Files:**
- Modify: `python/src/science/corpus.py` (protocol), `python/src/science/root.py` (implementation + wiring)
- Test: `python/tests/test_operation_port.py` (new, portable — fake port), plus one arm in the durable suite later (Task 17)

**Interfaces:**
- Produces, in `science.corpus`:

```python
class OperationPort(Protocol):
    def append_intent(self, payload: bytes) -> str: ...            # returns the 64-hex entry digest
    def execute_fulfilling(self, plan: WritePlan, fulfills: str) -> None: ...
```

  and `CorpusWriter.__init__(self, root, executor_factory, operation_port: OperationPort | None = None)`.
- Produces, in `science.root`: `class DurableOperationPort` — `append_intent` wraps `atoms.coordinator.commands.append_intent(backend, str(root), str(metadata_root), storage, payload)`; `execute_fulfilling` constructs a `DurableExecutor(root, ..., fulfills=fulfills)` and calls `execute(plan)`; `DurableExecutor.__init__` gains keyword `fulfills: str | None = None`, passed into `build_spec(fulfills=self._fulfills, ...)` — everything else in the compile is unchanged; `open_corpus` passes a `DurableOperationPort` for the root.

**Steps:**

- [ ] **Step 1: Write the failing tests** — portable: a `FakePort` records `append_intent` payloads and `execute_fulfilling(plan, fulfills)` pairs; assert `open_corpus`-independent construction still works with `operation_port=None`; assert `DurableExecutor(fulfills=...)` threads the value into the built spec (construct the executor with a stub `run_transaction`? No — instead unit-test the compile by monkeypatching `science.root.run_transaction` to capture the spec, then assert `spec.fulfills == "ab" * 32`).
- [ ] **Step 2: Run to verify failure.**
- [ ] **Step 3: Implement.** `science.corpus` must not import `atoms` (the protocol is structural); the engine failure mapping in `execute_fulfilling` is `DurableExecutor._submit`'s, inherited for free. `append_intent` failures map like §4's table: wrap engine exceptions as `ExecutionError(index=None, applied=0)` when raised before any mutation (`ProjectApprovalRefused`, `CapabilityUnavailable`, **and `PreconditionRefused`** — an unregistered root surfaces as a clean pre-mutation refusal here), `applied=None` otherwise — implement this inside `DurableOperationPort.append_intent` with the same `except` ladder as `_submit`.
- [ ] **Step 4: Run to verify pass; full portable suite.**
- [ ] **Step 5: Commit** — `git add python/src/science/{corpus,root}.py python/tests/test_operation_port.py && git commit -m "feat(root): the operation port — durable intents and fulfilling transactions"`.

---

### Task 14: The stored act-report kind

**Files:**
- Modify: `python/src/science/stored.py`
- Test: `python/tests/test_stored_retraction.py`'s sibling — `python/tests/test_stored_act_report.py` (new)

**Interfaces:**
- Consumes: `science.report.ActReport` (frozen boundary-minted value) and `report.ACT_REPORT_DOMAIN`.
- Produces: `stored.act_report_node(report: ActReport) -> Node` — kind `"act-report"`, **slug derived from `report.identity()`** (the complete digest, untruncated — the report's whole facet is its identity basis, so the address is content-derived; the event token alone is not the identity, and a prefix is not the identity either), title `f"{report.operation} report"`, one covered facet `"act-report"` carrying exactly the identity fields (`operation`, `event_token`, `actor`, `observer`, `instrument`, `opened_at`, `closed_at`, `entries` as `_entry_facet` rows); `SEMANTIC_DOMAINS["act-report"] = report.ACT_REPORT_DOMAIN`; `COVERED_FACETS["act-report"] = ("act-report",)`. Test the invariant: two mints of the same report value share an id; changing any identity field changes it.

**Steps:**

- [ ] **Step 1: Write the failing tests** — a boundary-minted report round-trips: `act_report_node(report)` is stamped, its facet reproduces `report.identity()`'s input mapping, and a foreign (raw-constructed) node of kind `act-report` with a stale stamp is caught by `semantic_hash_disagrees`. Mint a report for tests through `science.report._mint_report` is not public — use the boundary's public refusal path or expose a test fixture via `science.boundary`; follow whatever `test_boundary.py` already does to obtain an `ActReport` value.
- [ ] **Step 2: Run to verify failure.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run to verify pass; full portable suite.**
- [ ] **Step 5: Commit** — `git add python/src/science/stored.py python/tests/test_stored_act_report.py && git commit -m "feat(stored): act-report as a governed stored kind"`.

---

### Task 15: `import_bundle`

**Files:**
- Modify: `python/src/science/errors.py`, `python/src/science/corpus.py`
- Test: `python/tests/test_import_bundle.py` (new, portable with `FakePort` + `Recorder`)

**Interfaces:**
- Consumes: Task 13's port, Task 14's stored act-report, Task 9's retraction kind (bundle cycle checks), `science.report`'s `OperationIntent`, `RecordImportEntry`, `ImportedRecords`, `Registration`.
- Produces: errors `ImportRefused(WriteRefused)` (fields: `member: str | None`, `cycle_edges: tuple[tuple[str, str], ...]`, `report_ref: str | None`), `BundleMemberHeld(ImportRefused)`; `CorpusWriter.import_bundle(self, records: Sequence[Node], *, actor: str, observer: str, instrument: str, opened_at: str, closed_at: str) -> ActReport`.

**Post-freeze correction:** Implement only R20's grounded semantic import
check. R19 and R22 require run/result/comparison/rule evidence this API and the
stored projections do not carry; R23 remains deferred. Exact link and stamp
hygiene remains required import integrity, but does not proxy those rows.

**Steps:**

- [ ] **Step 1: Write the failing tests.** The fixture:

```python
class FakePort:
    intents: ClassVar[list[bytes]] = []
    fulfilling: ClassVar[list[tuple[list, str]]] = []
    intent_digest = "ab" * 32

    def append_intent(self, payload: bytes) -> str:
        FakePort.intents.append(payload)
        return FakePort.intent_digest

    def __init__(self, root):                      # applied so later reads see results
        self._inner = DefaultExecutor(root)

    def execute_fulfilling(self, plan, fulfills: str) -> None:
        FakePort.fulfilling.append((list(plan), fulfills))
        self._inner.execute(plan)

@pytest.fixture()
def writer_with_port(tmp_path):
    Recorder.plans, FakePort.intents, FakePort.fulfilling = [], [], []
    return CorpusWriter(tmp_path, Recorder, operation_port=FakePort(tmp_path))
```

```python
def test_import_admits_bundle_in_one_payload_plan(writer_with_port):
    reports = writer_with_port.import_bundle([prop("a"), prop("b")], actor="k",
        observer="corpus", instrument="test", opened_at="T0", closed_at="T1")
    # grain 1: exactly one intent appended, before any plan
    assert len(FakePort.intents) == 1
    # grain 2: one payload plan containing both creates
    payload_plans = [p for p in Recorder.plans if len(p) == 2]
    assert payload_plans and all(isinstance(op, CreateOp) for op in payload_plans[0])
    # grain 3: the report went through execute_fulfilling with the intent digest
    (plan, fulfills), = FakePort.fulfilling
    assert fulfills == FakePort.intent_digest
    assert writer_with_port.read_view.holds("proposition:a")

def test_member_held_refuses_whole_bundle_no_payload_write(writer_with_port):
    writer_with_port.add(prop("a"))
    with pytest.raises(BundleMemberHeld) as caught:
        writer_with_port.import_bundle([prop("a"), prop("b")], ...)
    assert not writer_with_port.read_view.holds("proposition:b")     # nothing admitted
    assert caught.value.report_ref is not None                        # refusal report published

def test_unresolved_foreign_input_admits_with_finding(writer_with_port):
    # report entries carry ImportedRecords(refs=..., findings=("unresolved: ...",))
def test_stale_stamp_member_refuses(writer_with_port):                # S3's banked mutation
def test_foreign_act_report_enters_inert(writer_with_port):           # T1's import arm

# The one selected R-row validator is a runnable check with a concrete forgery:
def test_contradictory_nondeterminism_contract_refused(writer_with_port):
    # R20's import half, per the frozen row: a bundle analysis-spec that combines the
    # stochastic-unseeded nondeterminism class with a bitwise equivalence rule — the
    # contradiction is internal to the spec record — refused, no write.
def test_refusal_before_intent_when_request_malformed(writer_with_port):
    # empty bundle: refuses before any intent is appended
    with pytest.raises(ImportRefused): writer_with_port.import_bundle([], ...)
    assert FakePort.intents == []
```

- [ ] **Step 2: Run to verify failure.**
- [ ] **Step 3: Implement** per spec §4.4/§6 order: under the lock —
  1. request validation (non-empty bundle, attribution strings) — refuses **before** the intent;
  2. mint `intent = OperationIntent("import", secrets.token_hex(16), actor)` and serialize **exactly its projection** — the banked act-report design fixes the operation-intent payload to operation kind, event token, and actor, nothing more (`observer`/`instrument` are act-report fields, not intent fields): `payload = v1.encode({"kind": intent.kind, "event_token": intent.event_token, "actor": intent.actor})`; `intent_digest = port.append_intent(payload)`; no port configured → `ImportRefused` before any act ("this corpus has no operation port; import is a boundary operation");
  3. whole-bundle validation over `records` + the local `ReadView` (spec §4.4's list): stored shape/stamp per member (stale → refuse), duplicate ids/uids/paths within the bundle, member held or colliding (`BundleMemberHeld`), the ordinary add refusals per member (basis, eligibility — evaluated over the union view so intra-bundle references resolve), retraction-graph acyclicity over bundle ∪ local (refusing with the offending edge set), R20's analysis-spec nondeterminism-class/equivalence-rule consistency check, and unresolvable foreign inputs collected as findings (not refusals);
  4. on refusal after the intent: build the refusal report (`RecordImportEntry(subject=<corpus root name>, outcome=ImportedRecords(refs=(), findings=(reason, ...)))`), publish it via `port.execute_fulfilling([CreateOp(...report node...)], intent_digest)`, reconstruct the corpus, set `report_ref` on the exception, raise;
  5. on pass: build the payload plan — one `CreateOp` per member, path from the store's own rule `self._corpus.store.path_for(node.id).relative_to(self._corpus.store.root).as_posix()`, content `node_to_markdown(node).encode("utf-8")` (import `node_to_markdown` from the same `nodes` module `nodes/core/corpus.py` imports it from) — execute through the shared state's `corpus.executor.execute(plan)`, then **reconstruct inside the shared root state** (Task 6): build a fresh `Corpus(self._root, executor_factory=<the state's stored factory>)`, replace the state's `corpus` and `view` under the held lock so every writer on this root sees the reconstruction (reconstruction from disk is the stated recovery posture);
  6. mint the closing report (entries: one `RecordImportEntry` with the admitted refs in canonical payload order and the findings), store it via `port.execute_fulfilling([CreateOp(<act_report_node bytes>)], intent_digest)`, reconstruct again, return the `ActReport`.
- [ ] **Step 4: Run to verify pass; full portable suite.**
- [ ] **Step 5: Commit** — `git add python/src/science/{corpus,errors}.py python/tests/test_import_bundle.py && git commit -m "feat(corpus): import_bundle — intent, one payload transaction, closing report"`.

---

### Task 17: The cut-5 acceptance suite and runner

**Files:**
- Create: `python/tests/acceptance/test_durable_families.py`, `python/tools/cut5_acceptance.py`
- Never modify: `python/tools/cut4_acceptance.py`
- Read first: `python/tests/acceptance/durable_fixture.py`, `conftest.py`, `tools/cut4_acceptance.py`.

**Steps:**

- [ ] **Step 1: Write the durable arms** against the certified tuple via the existing acceptance fixture: a durable supersede walked back out after facade reload; a durable revise whose replacement survives reload with unchanged stamp; a durable retract; one full `import_bundle` through `open_corpus` — real intent in the chain, payload transaction, report transaction with `fulfills` — asserting the report node reloads and the chain grew by **five** entries in the exact typed sequence: the intent entry, then the payload transaction's registration and settlement, then the report transaction's registration and settlement, with the report registration carrying `fulfills` equal to the intent entry's digest; the uncertified-tuple refusal for one family write (`/dev/shm`, errors if unavailable, per cut 4's pattern).
- [ ] **Step 2: Write `tools/cut5_acceptance.py`** by cut 4's shape (probe first, `PROBE_REFUSED = 2`, work dir `<repo>/.cut5-acceptance` / `SCIENCE_CUT5_ROOT`, per-run directories); it runs the cut-5 durable arms and may invoke cut 4's runner as a prefix without altering it.
- [ ] **Step 3: Run it on this host** — `uv run python -m tools.cut5_acceptance` — all durable arms green on the certified tuple. Record the full output.
- [ ] **Step 4: Commit** — `git add python/tests/acceptance/test_durable_families.py python/tools/cut5_acceptance.py && git commit -m "test(cut5): durable family arms and the acceptance runner"`.

---

### Task 16: N2 arms for cut 5

**Ordering:** Task 17 creates the durable acceptance nodes first. Task 16 then
declares and audits their N2 arms through the certified cut-5 runner.

**Files:**
- Create: `python/tests/n2_arms_cut5.py`, `python/tests/acceptance/test_n2_cut5.py`
- Read first: `python/tests/n2_arms.py` (the `Arm`/`Sabotage` types), `n2_arms_cut4.py`, `tests/test_n2_cut4.py`, and frozen cut 5 §5.

**Steps:**

- [ ] **Step 1: Declare all 28 cut-5 selected arms as data** — row, assertion, source mutation (a `Sabotage` against the real module text), and the exact tests that must fail. Durable arms name `acceptance/…` node ids exactly as `n2_arms_cut4.py` does. Every declaration must match a clause the twice-corrected frozen cut selects — no extra arms, no missing arms. R20 remains selected; R19, R22, and R23 have no cut-5 declaration. T2 has three declarations and M3 has four.
- [ ] **Step 2: Run `python/tests/acceptance/test_n2_cut5.py` through the certified runner** — `uv run python -m tools.cut5_acceptance -q` — and fix every `vacuous`/`stale`/`mixed`/`uncollected` verdict. The runner includes that acceptance module; the unsabotaged baseline must pass against the real package and certified tuple.
- [ ] **Step 3: Commit** — `git add python/tests/n2_arms_cut5.py python/tests/acceptance/test_n2_cut5.py && git commit -m "test(n2): declare cut 5's arms with their sabotages"`.

---

### Task 18: Results, ledger, and close-out

**Files:**
- Create: `docs/plans/2026-08-19-conformance-cut-5-results.md`
- Modify: `docs/designs/2026-08-19-conformance-cut-5.md` (discharge note), `docs/designs/2026-08-19-family-adapters-design.md` (status → implemented, dated), `docs/designs/2026-08-03-redesign-adoption-ledger.md` (row 4: item 2 implemented; the hard cut's adoption half's status), `docs/guide/` (grep for stale family-surface claims)

**Steps:**

- [ ] **Step 1: Write the results doc** per `2026-08-18-conformance-cut-4-results.md`'s form: what ran, where, counts, the acceptance output, any deviations (each closed as a dated design amendment or reverted — never silently).
- [ ] **Step 2: Status flips** in the same change; grep `docs/` for "add-only", "no edit surface", "Plan B item 2" claims that this landing makes stale and correct them (drift propagates outward).
- [ ] **Step 3: Run everything**: `uv run pytest tests -q` (portable), `uv run python -m tools.cut5_acceptance` (durable arms and `tests/acceptance/test_n2_cut5.py`), `uv run python tools/check_guide.py`. All green before the final commit.
- [ ] **Step 4: Commit** — `git add docs/plans/2026-08-19-conformance-cut-5-results.md docs/designs/2026-08-19-conformance-cut-5.md docs/designs/2026-08-19-family-adapters-design.md docs/designs/2026-08-03-redesign-adoption-ledger.md docs/guide && git commit -m "feat(corpus): land the family adapters; discharge conformance cut 5"`.
