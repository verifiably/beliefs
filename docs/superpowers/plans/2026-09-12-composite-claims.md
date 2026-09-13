# Composite Claims Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the `composite` world kind end to end — base-contract grammar, kind and relation, the domain `edges:` declaration, the opaque value and its constructor, the write boundary, the audit, the derived reading over the traced evaluator, the mm30 re-run — and discharge table U at a conformance cut.

**Architecture:** The base contract gains `composite_grammar`, a `composite` kind, a `composes` relation and a `same_kind` rule on `supersedes`; a domain contract gains an `edges:` table keyed by operator naming the cause and effect slots; `beliefs/composite.py` builds an opaque `Composite` from proposition refs under a `ResolutionSnapshot`, classifies members into signed edges, refuses cycles, and reads a composite through the evaluator's own wrapper; `corpus.py` re-derives every check on the shared refusal path and `audit.py` under audit; `belief.py` and `evaluation.py` are factored so the admitted set is computed once and traced out. The reproduction corpus is recreated under successor `mm30` and `biology` contracts, never migrated.

**Tech Stack:** Python 3.11+ (`uv run --frozen` from `python/`), pytest, `nodes.core`, TypeScript/vitest under `ts/`, the N2 harness (`python/tests/test_n2.py`), `tasks`.

**Spec:** `docs/superpowers/specs/2026-09-12-composite-claims-design.md` (cleared for planning 2026-09-12 after three reviews, review log §15).

## Global Constraints

- **Baseline is `main` after the `estimand-typing` lane merges** (spec decision 12). Interfaces consumed from that lane — `stored.analysis_spec_value(node, *, profile)`, `Estimand.control.identification`, the `estimands:` declaration beside which `edges:` sits, the recreated reproduction corpus and its step order — are named exactly as the estimand plan (`docs/superpowers/plans/2026-09-12-estimand-typing.md`, on `design/estimand-typing` until it merges) produces them. Task 0 refuses to open the lane before that merge.
- Work in the worktree `.worktrees/composite-claim` (branch `design/composite-claim`), rebased onto `main` at Task 0. Every path below is relative to the Beliefs repository root; paths shown to the user are prefixed with the worktree directory.
- Frozen declarations and cut bodies stay byte-exact. No reader coerces or repairs a stored record; every refusal names a stable code (spec §3.4, §4.2, §4.3).
- Every closed set is declared in the contract and matched in code; `Composite`, `CompositeReading` and `BaseContract` have no public constructor; `ResolutionSnapshot` is a required argument everywhere membership is resolved and has no default.
- `science.belief.v1` reads nothing this plan adds; the evaluator's answers are unchanged for every input (P1–P9 green at every commit; the factoring in Task 6 is asserted by equality with the pre-factoring answers over `test_belief.py`'s scenarios).
- Both implementations parse the same base and domain documents; TypeScript validates no composite payload (spec limitation 11).
- Conventional commits, no attribution trailers. `tasks check` before every commit; the pre-commit hook runs the gate. Every commit message names the U row(s) it serves.

---

## File map

| File | Responsibility |
| --- | --- |
| `contracts/science/CONTRACT.yaml`, `python/src/beliefs/contracts/science/CONTRACT.yaml` | `composite_grammar`, the `composite` kind, `composes`, `supersedes` with `same_kind`, the `composite` facet (Task 1) |
| `python/src/beliefs/contract/base.py` | `CompositeGrammar`, `RelationDecl.same_kind`, `COMPOSITE_GRAMMAR` (Task 1) |
| `python/src/beliefs/contract/domain.py` | `EdgeDecl`, `_parse_edge`, `DomainContract.edges`, `_declarations()` entries `edge:<op>` (Task 2) |
| `fixtures/contracts/testing.yaml` | one `edges:` row, shared with TypeScript (Task 2) |
| `python/src/beliefs/profile.py` | `ProfileSpec.composite_grammar`, `CompiledEdge`, `ProfileSpec.edges`, projection (Tasks 1, 2) |
| `ts/src/contract.ts`, `ts/src/profile.ts` | the same declarations parsed and compiled, no payload validation (Tasks 1, 2) |
| `python/src/beliefs/errors.py` | `CompositeError` (Task 3) |
| `python/src/beliefs/resolution.py` | `ReferentPosition.node()` (Task 3) |
| `python/src/beliefs/composite.py` | `CompositeNode`, `Edge`, `CompositeFacet`, `Composite`, `CompositeReceipt`, `build_composite`, `classify`, `composite_identity`; `read_composite` and its value types (Tasks 3, 6) |
| `python/src/beliefs/stored.py` | `COMPOSITE_FACET`, `COMPOSES`, `composite_value`, `composite_node` (Task 3) |
| `python/src/beliefs/permit.py` | `KIND_ACTS["composite"]` (Task 1) |
| `python/src/beliefs/corpus.py` | `_refuse_composite`, `_refuse_supersedes_same_kind`, `supersede` widened (Task 4) |
| `python/src/beliefs/audit.py` | `check_composite`, `check_supersedes_kinds`, the loop arms (Task 5) |
| `python/src/beliefs/belief.py`, `python/src/beliefs/evaluation.py` | `Admission`, `admitted`, `evaluate_traced`, `evaluate_over_traced`; `evaluate` and `evaluate_over` as first projections (Task 6) |
| `python/tools/reproduction/*` | successor `mm30` and `biology` contracts with `edges:`, `compose.py`, `read.py`, the recreated corpus, the addendum (Task 7) |
| `python/tests/test_composite.py`, `test_composite_boundary.py`, `test_composite_reading.py`; edits to `test_base_contract.py`, `test_domain_contract.py`, `test_facet_declarations.py`, `test_coordination.py`, `test_permit.py`, `test_audit.py`, `test_belief.py`, `test_evaluation.py`; `ts/tests/declarations.test.ts` | unit coverage per task |
| `python/tests/acceptance/test_composite_acceptance.py`, `python/tests/n2_arms_cut<N>.py`, `python/tests/acceptance/n2_arms_cut<N>.py`, `python/tests/acceptance/test_n2_cut<N>.py`, `python/tools/cut<N>_acceptance.py` | U1–U10 acceptance, the sabotage declaration, the guard, the runner (Task 8) |
| `docs/designs/…-conformance-cut-<N>.md`, `docs/plans/…-conformance-cut-<N>-results.md`, the amended designs, guide, glossary, ledger, roadmap | freeze, discharge, amendments (Tasks 0, 8, 9) |

`<N>` is claimed at freeze (concurrency rule 1): the next unclaimed cut number across every worktree at that moment, chained after the highest-numbered discharged runner.

**One correction to the spec, found while planning and recorded in its review log.** Spec §3.1 said the same-kind rule is enforced "beside the signature check each relation instance already passes". No such check exists: `RelationDecl` (sources, targets) is parsed and compiled and read by nothing on the write path — `_refuse` validates documents, facets, bearers and eligibility, never a relation instance's endpoint kinds. The same-kind rule is therefore a **new** check on the shared path (Task 4), and the absence of a general endpoint-kind check is filed as spec limitation 17, not closed here.

---

### Task 0: Open the lane and freeze the cut

**Files:**
- Create: `docs/designs/<date>-conformance-cut-<N>.md`
- Move: `docs/superpowers/specs/2026-09-12-composite-claims-design.md` → `docs/designs/2026-09-12-composite-claims-design.md` (`git mv`)
- Modify: `python/tests/test_designs_corpus.py` (`GUARANTEE_TABLES["U"]`, `TABLE_OWNERS["U"]`), the designs README row total and list

**Interfaces:**
- Produces: the cut number `<N>`, the freeze commit `CUT<N>_FREEZE_COMMIT` and the cut document's SHA-256, both pinned by Task 8's guard; the lane's admission recorded on `beliefs-4bcf88`.

- [ ] **Step 1: Confirm the baseline**

Run `git -C <main checkout> log --oneline -1 -- docs/designs/2026-09-12-estimand-typing-design.md`. The lane opens only if that design has merged into `main` (the file exists under `docs/designs/` on `main`). If it has not, stop: nothing below starts. Then `git rebase main` in this worktree and `just setup`.

- [ ] **Step 2: Admit the lane under rule 6**

Run `tasks prime --project beliefs` and read the roadmap's lane table. The lane opens only if fewer than two kernel lanes are open **and** no on-path lane is startable (the `world-read` head is either in flight or blocked). Record the reading in a task note — `tasks note beliefs-4bcf88 "lane admitted under rule 6: <open lanes>, <on-path state>"` — and `tasks start beliefs-4bcf88`. If the rule refuses, stop here.

- [ ] **Step 3: Claim the cut number**

Run `git worktree list` and `ls <each worktree>/docs/designs/*conformance-cut-*.md`; `<N>` is the next number unclaimed in any worktree (concurrency rule 1). Read the highest-numbered **discharged** runner in `python/tools/cut*_acceptance.py` for Task 8's `PREFIX_RUNNERS` (rule 5).

- [ ] **Step 4: Write and freeze the cut document**

Write `docs/designs/<date>-conformance-cut-<N>.md` on cut 26's shape: §1 what this cut is; §2 the boundary (the files this plan names); §3 selection — declaration units `U1`–`U10`, single-homed, every clause selected only when its source mutation and every named check run inside §2; §4 accounting; §5 N2 and acceptance obligations (the mechanisms of spec §10.3, one arm each — the `before` blocks are written in Task 8 against the tree that exists then, and the accounting freezes there); §6 second reader; §7 limitations (spec §13, restated, with limitation 17 added). `git mv` the design spec into `docs/designs/`, register `"U": tuple(f"U{n}" for n in range(1, 11))` and `TABLE_OWNERS["U"] = "2026-09-12-composite-claims-design.md"`, update the README's design table and its "frozen tables" count (the guide's `contracts-and-adoption.md` sentence too), and run `uv run --frozen pytest tests/test_designs_corpus.py` green. Commit: `docs(cut): freeze conformance cut <N>, composite claims` — the dated freeze commit, made before any code below exists.

---

### Task 1: The base contract — grammar, kind, relations, both implementations

**Files:**
- Modify: `contracts/science/CONTRACT.yaml`, copy to `python/src/beliefs/contracts/science/CONTRACT.yaml`
- Modify: `python/src/beliefs/contract/base.py:74-75` (field sets), the `ClaimGrammar` block, `RelationDecl`, `BaseContract`, `parse_base_contract`
- Modify: `python/src/beliefs/profile.py` (`ProfileSpec.composite_grammar`, `_projection`, `compile_profile`)
- Modify: `python/src/beliefs/permit.py:52` (`KIND_ACTS`)
- Modify: `ts/src/contract.ts` (`CompositeGrammar`, `RelationDecl.sameKind`, `parseBaseContract`), `ts/src/profile.ts` (`ProfileSpec.compositeGrammar`, the projection)
- Test: `python/tests/test_base_contract.py`, `python/tests/test_facet_declarations.py:18`, `python/tests/test_coordination.py:63`, `python/tests/test_permit.py`, `ts/tests/declarations.test.ts:19`

**Interfaces:**
- Produces: `CompositeGrammar(version: int, shapes: tuple[str, ...])` and `COMPOSITE_GRAMMAR = "science.composite.v1"` at `beliefs.contract.base`; `RelationDecl.same_kind: bool`; `BaseContract.composite_grammar`; `ProfileSpec.composite_grammar`; `stored.WORLD_KINDS` ending in `"composite"` (derived from the document's authored order); `stored.SEMANTIC_DOMAINS["composite"] == "science.composite.v1"`; `stored.COVERED_FACETS["composite"] == ("composite",)`; `KIND_ACTS["composite"] == frozenset({"corpus-write"})`.

- [ ] **Step 1: Write the failing tests**

Append to `python/tests/test_base_contract.py`:

```python
class TestCompositeGrammarAndKind:
    def test_the_shipped_base_declares_the_grammar_and_the_kind(self, base_contract):
        assert base_contract.composite_grammar.version == 1
        assert base_contract.composite_grammar.shapes == ("dag",)
        kind = base_contract.kinds["composite"]
        assert kind.role == "world" and kind.domain == "science.composite.v1"
        assert kind.facets["composite"].required and kind.facets["composite"].covered
        assert not kind.facets["display"].covered

    def test_the_two_relations(self, base_contract):
        composes = base_contract.relations["composes"]
        assert (composes.group, composes.sources, composes.targets) == ("world", ("composite",), ("proposition",))
        assert composes.same_kind is False
        supersedes = base_contract.relations["supersedes"]
        assert set(supersedes.sources) == set(supersedes.targets) == {"proposition", "composite"}
        assert supersedes.same_kind is True
        assert base_contract.relations["assesses"].targets == ("proposition",)

    def test_a_base_contract_lacking_the_grammar_is_refused(self, document):
        del document["composite_grammar"]
        with pytest.raises(MalformedContract, match="composite_grammar"):
            parse(document)

    def test_an_unknown_grammar_field_is_refused(self, document):
        document["composite_grammar"]["directed"] = True
        with pytest.raises(MalformedContract, match="directed"):
            parse(document)

    def test_a_duplicate_shape_is_refused(self, document):
        document["composite_grammar"]["shapes"] = ["dag", "dag"]
        with pytest.raises(TagCollision):
            parse(document)

    def test_same_kind_on_unequal_endpoint_sets_is_refused(self, document):
        document["relations"]["composes"]["same_kind"] = True
        with pytest.raises(MalformedContract, match="same_kind"):
            parse(document)

    def test_same_kind_must_be_a_boolean(self, document):
        document["relations"]["supersedes"]["same_kind"] = "yes"
        with pytest.raises(MalformedContract, match="same_kind"):
            parse(document)

    def test_an_unsupported_shape_is_refused(self, document):
        document["composite_grammar"]["shapes"] = ["dag", "pag"]
        with pytest.raises(MalformedContract, match="pag"):
            parse(document)

    def test_the_grammar_and_the_rule_enter_the_identities(self, document):
        from beliefs.profile import compile_profile

        before = parse(copy.deepcopy(document))
        document["composite_grammar"]["version"] = 2
        after = parse(document)
        assert before.content_identity != after.content_identity
        assert compile_profile(before, []).compiled_identity != compile_profile(after, []).compiled_identity
        assert compile_profile(before, []).composite_grammar == before.composite_grammar
```

In `python/tests/test_facet_declarations.py:18` rename the test to `test_the_fourteen_world_kinds_and_three_prose_kinds_are_declared` and add `"composite"` to the world set. In `python/tests/test_coordination.py:63` rename to `test_the_world_inventory_is_exactly_the_fourteen_banked_kinds` and append `"composite"` as the last element (the document declares it after `act-report`). In `python/tests/test_permit.py` add:

```python
def test_a_composite_is_minted_by_corpus_write_alone():
    assert KIND_ACTS["composite"] == frozenset({"corpus-write"})
```

In `ts/tests/declarations.test.ts` change the count test to `"declares fourteen world kinds and three prose kinds"` with `toHaveLength(14)` and add:

```ts
  it("declares the composite grammar and the same-kind rule on supersedes", () => {
    expect(base.compositeGrammar).toEqual({ version: 1, shapes: ["dag"] });
    expect(base.relations.supersedes.sameKind).toBe(true);
    expect(base.relations.composes.sameKind).toBe(false);
    expect(base.relations.composes.targets).toEqual(["proposition"]);
  });
  it("refuses same_kind where sources and targets differ", () => {
    const line = "composes: { group: world, sources: [composite], targets: [proposition] }";
    expect(SHIPPED).toContain(line); // the mutation must land, or the assertion below asserts nothing
    const bad = SHIPPED.replace(line, "composes: { group: world, sources: [composite], targets: [proposition], same_kind: true }");
    expect(() => parseBaseContract(bad, "<bad>")).toThrow(/same_kind/);
  });
  it("refuses an unsupported shape", () => {
    const line = "  shapes: [dag]\n";
    expect(SHIPPED).toContain(line);
    expect(() => parseBaseContract(SHIPPED.replace(line, "  shapes: [dag, pag]\n"), "<bad>")).toThrow(/pag/);
  });
  it("refuses a base contract without the composite grammar", () => {
    const block = "composite_grammar:\n  version: 1\n  shapes: [dag]\n";
    expect(SHIPPED).toContain(block);
    expect(() => parseBaseContract(SHIPPED.replace(block, ""), "<bad>")).toThrow(/composite_grammar/);
  });
```

- [ ] **Step 2: Run the tests to verify they fail**

Run from `python/`: `uv run --frozen pytest tests/test_base_contract.py tests/test_facet_declarations.py tests/test_coordination.py tests/test_permit.py -q` — expected: failures on `composite_grammar` (`KeyError`/`AttributeError`) and on the kind sets. From `ts/`: `npx vitest run tests/declarations.test.ts` — expected: three failures.

- [ ] **Step 3: The contract document**

In `contracts/science/CONTRACT.yaml`, after the `claim_grammar:` block and before `kinds:`, add:

```yaml
# --- composite grammar (composite-claims design §3.1) ------------------------
# A shape is a thing the kernel does — for `dag`, derive directed edges from the
# members' claims and refuse a cycle — so the set is kernel-owned and closed.
composite_grammar:
  version: 1
  shapes: [dag]
```

In `kinds:`, after `act-report:` add:

```yaml
  composite:
    domain: science.composite.v1
    facets:
      composite: { required: true, covered: true }
      display: { required: false, covered: false }
```

In `relations:`, add after `grounded-in:` and replace the `supersedes:` line:

```yaml
  composes: { group: world, sources: [composite], targets: [proposition] }
  supersedes: { group: lifecycle, sources: [proposition, composite], targets: [proposition, composite], same_kind: true }
```

In `facets:`, beside the other reader-shaped entries, add:

```yaml
  composite: { shape: reader, reader: stored.composite_value }
```

Copy the file byte-for-byte to `python/src/beliefs/contracts/science/CONTRACT.yaml` (`cp contracts/science/CONTRACT.yaml python/src/beliefs/contracts/science/CONTRACT.yaml`; `test_base_contract.py`'s existing shipped-copy test holds them equal).

- [ ] **Step 4: Python parsing**

In `python/src/beliefs/contract/base.py`:

```python
_CONTRACT_FIELDS = _CONTRACT_FIELDS | {"composite_grammar"}  # the baseline's set already carries `estimand_grammar`; extend it, never restate it
_COMPOSITE_GRAMMAR_FIELDS = frozenset({"version", "shapes"})
SUPPORTED_SHAPES = ("dag",)
"""The shapes this implementation derives (design §3.4). A contract naming a
shape outside this set is refused at parse: a profile carrying `pag` would
otherwise run `dag` classification under another shape's name."""
_RELATION_FIELDS = frozenset({"group", "sources", "targets"})
_RELATION_OPTIONAL = frozenset({"same_kind"})
_RELATION_GROUPS = ("world", "lifecycle")

COMPOSITE_GRAMMAR = "science.composite.v1"
"""The tag a stored composite facet carries under `grammar` (design §3.2)."""


@dataclass(frozen=True)
class CompositeGrammar:
    """The closed set of shapes a composite may take (design §3.1). A shape is
    a derivation the kernel performs, never a domain's declaration."""

    version: int
    shapes: tuple[str, ...]

    def projection(self) -> dict[str, object]:
        return {"version": self.version, "shapes": list(self.shapes)}
```

Extend `RelationDecl`:

```python
@dataclass(frozen=True)
class RelationDecl:
    name: str
    group: str
    sources: tuple[str, ...]
    targets: tuple[str, ...]
    same_kind: bool = False
    """An instance's endpoints must be records of one kind (design §3.1).
    Admissible only where `sources` and `targets` are equal sets, so the rule
    can never name a pair the signature already forbids."""

    def projection(self) -> dict[str, object]:
        return {
            "group": self.group,
            "sources": sorted(self.sources),
            "targets": sorted(self.targets),
            "same_kind": self.same_kind,
        }
```

Add `composite_grammar: CompositeGrammar` to `BaseContract` after `claim_grammar`. In `parse_base_contract`, after `claim_grammar = ClaimGrammar(...)`:

```python
    composite_where = f"{source}: composite_grammar"
    composite = _mapping(root["composite_grammar"], composite_where)
    _exact_fields(composite, _COMPOSITE_GRAMMAR_FIELDS, composite_where)
    composite_grammar = CompositeGrammar(
        version=_positive_int(composite["version"], f"{composite_where}: version"),
        shapes=_closed_set(composite["shapes"], f"{composite_where}: shapes"),
    )
    if not composite_grammar.shapes:
        raise MalformedContract(f"{composite_where}: shapes must be non-empty; a grammar with no shape admits no composite")
    unsupported = sorted(set(composite_grammar.shapes) - set(SUPPORTED_SHAPES))
    if unsupported:
        raise MalformedContract(
            f"{composite_where}: shapes {unsupported} are not shapes this implementation derives ({SUPPORTED_SHAPES}); "
            "a later grammar version arrives with its classification, never ahead of it"
        )
```

(`_closed_set` already raises `TagCollision` on a duplicate and refuses a non-list.) Replace the relation loop's body:

```python
        body = _mapping(body_value, where)
        _exact_fields({k: v for k, v in body.items() if k not in _RELATION_OPTIONAL}, _RELATION_FIELDS, where)
        if body["group"] not in _RELATION_GROUPS:
            raise MalformedContract(f"{where}: group is one of {', '.join(_RELATION_GROUPS)}, found {body['group']!r}")
        sources = _closed_set(body["sources"], f"{where}: sources")
        targets = _closed_set(body["targets"], f"{where}: targets")
        for kind in (*sources, *targets):
            if kind not in kinds:
                raise MalformedContract(f"{where}: {kind!r} is not a kind this contract declares")
        same_kind = body.get("same_kind", False)
        if not isinstance(same_kind, bool):
            raise MalformedContract(f"{where}: same_kind is a boolean, found {same_kind!r}")
        if same_kind and set(sources) != set(targets):
            raise MalformedContract(
                f"{where}: same_kind requires sources and targets to be equal sets; "
                f"{sorted(set(sources) ^ set(targets))} appear on one side only"
            )
        relations[relation_name] = RelationDecl(relation_name, body["group"], sources, targets, same_kind)
```

Pass `composite_grammar=composite_grammar` to `BaseContract._parsed`. Export `COMPOSITE_GRAMMAR` and `CompositeGrammar` from `beliefs/contract/__init__.py` beside `ClaimGrammar` if that module re-exports the grammar (check `grep -n ClaimGrammar python/src/beliefs/contract/__init__.py`; mirror whatever it does).

- [ ] **Step 5: The profile and the permit**

In `python/src/beliefs/profile.py`: add `composite_grammar: CompositeGrammar` to `ProfileSpec` after `claim_grammar`; import `CompositeGrammar` from `beliefs.contract.base`; in `compile_profile`'s `_compiled(...)` call pass `composite_grammar=base.composite_grammar` and in the `_projection(...)` call pass `composite_grammar=base.composite_grammar`; extend `_projection`'s signature with `composite_grammar: CompositeGrammar` (keyword-only, beside `kinds`) and add `"composite_grammar": composite_grammar.projection()` to the dict it returns. In `python/src/beliefs/permit.py` add `"composite": _CORPUS_WRITE,` after `"act-report"`.

- [ ] **Step 6: TypeScript parity**

In `ts/src/contract.ts`: add

```ts
export interface CompositeGrammar {
  readonly version: number;
  readonly shapes: readonly string[];
}
const SUPPORTED_SHAPES: readonly string[] = ["dag"];
```

add `readonly compositeGrammar: CompositeGrammar;` to `BaseContract` and `readonly sameKind: boolean;` to `RelationDecl`; in `parseBaseContract` add `"composite_grammar"` to the required list of the top-level `exactFields(document, [...])` call **beside the `"estimand_grammar"` entry the baseline already carries** (never restate the list), and after the claim grammar parse add:

```ts
  const compositeDocument = mapping(document.composite_grammar, `${source}.composite_grammar`);
  exactFields(compositeDocument, ["version", "shapes"], [], `${source}.composite_grammar`);
  const shapes = closedSet(compositeDocument.shapes, `${source}.composite_grammar.shapes`);
  if (shapes.length === 0) throw new MalformedContract(`${source}.composite_grammar.shapes: must be non-empty`);
  for (const shape of shapes) {
    if (!SUPPORTED_SHAPES.includes(shape))
      throw new MalformedContract(`${source}.composite_grammar.shapes: ${JSON.stringify(shape)} is not a shape this implementation derives`);
  }
  const compositeGrammar: CompositeGrammar = Object.freeze({
    version: positiveInt(compositeDocument.version, `${source}.composite_grammar.version`),
    shapes: Object.freeze(shapes),
  });
```

In the relation loop, `exactFields(body, ["group", "sources", "targets"], ["same_kind"], where)`; parse `same_kind` as `body.same_kind === undefined ? false : body.same_kind`, refusing a non-boolean (`${where}.same_kind: is a boolean`) and refusing `true` where the sorted sources and targets differ (`${where}.same_kind: requires sources and targets to be equal sets`); carry `sameKind` on the frozen decl. Return `compositeGrammar` on the contract. In `ts/src/profile.ts`, carry `compositeGrammar` on `ProfileSpec` (`compositeGrammar: base.compositeGrammar` in `compileProfile`'s constructor call). The TypeScript profile computes no compiled identity, so nothing else changes there.

- [ ] **Step 7: Run the tests to verify they pass**

`uv run --frozen pytest tests/test_base_contract.py tests/test_facet_declarations.py tests/test_coordination.py tests/test_permit.py tests/test_coreference_attestation.py tests/test_profile.py -q` green (the coreference test holds endpoint kinds equal to `WORLD_KINDS - {…}`, which now includes `composite` without an edit). From `ts/`: `npm test` green. Then the full `just test`. If `python/tests/test_parity_fixture.py` or `ts/tests/identity-fixture.test.ts` pins the base contract's content identity (read both headers), regenerate the fixture with `uv run --frozen python tools/generate_identity_fixture.py` and commit it here.

- [ ] **Step 8: Commit**

```bash
git add contracts python/src/beliefs/contracts python/src/beliefs/contract/base.py python/src/beliefs/profile.py python/src/beliefs/permit.py python/tests ts
git commit -m "feat(contract): declare composite_grammar, the composite kind, composes and same-kind supersedes (U1)"
```

---
### Task 2: A domain contract's `edges:` table — Python, the fixture, the profile, TypeScript

**Files:**
- Modify: `python/src/beliefs/contract/domain.py:59-63` (field sets), the declaration classes, `DomainContract` (`edges`, `_parsed`, `_declarations`), `parse_domain_contract`
- Modify: `fixtures/contracts/testing.yaml` (one `edges:` row)
- Modify: `python/tests/fixtures/biology-fixture.yaml` (one `edges:` row for `affects`, so the test writers' `WITH_BIOLOGY` profile can compose; three sorts and one `estimands:` row, so Tasks 4 and 6 can type an assessment under it)
- Modify: `python/src/beliefs/profile.py` (`CompiledEdge`, `ProfileSpec.edges`, `compile_profile`, `_projection`)
- Modify: `ts/src/contract.ts` (`EdgeDecl`, `DomainContract.edges`, `parseDomainContract`), `ts/src/profile.ts` (`ProfileSpec.edges`)
- Test: `python/tests/test_domain_contract.py`, `python/tests/test_profile.py`, `ts/tests/declarations.test.ts`

**Interfaces:**
- Consumes: `CompositeGrammar` (Task 1) — nothing here reads it; `edges:` is independent of shape.
- Produces: `EdgeDecl(operator: str, cause: int, effect: int, retired: bool = False)` with `schema_projection()`; `DomainContract.edges: Mapping[str, EdgeDecl]` keyed by local operator name; `_declarations()` entries `edge:<operator>`; `CompiledEdge(operator: str, cause: int, effect: int, retired: bool, contract: str)`; `ProfileSpec.edges: Mapping[str, CompiledEdge]` keyed by **namespaced** operator term.

- [ ] **Step 1: Write the failing tests**

Append to `python/tests/test_domain_contract.py`:

```python
class TestEdges:
    def test_the_fixture_declares_one_edge(self, parse, testing_document):
        contract = parse(testing_document)
        assert set(contract.edges) == {"affects"}
        assert (contract.edges["affects"].cause, contract.edges["affects"].effect) == (0, 1)
        assert ("edge:affects", contract.edges["affects"]) in contract._declarations()
        assert contract.claim_vocabulary()["edge:affects"] == {"cause": 0, "effect": 1}

    def test_a_contract_without_edges_is_a_contract_with_no_edges(self, parse, testing_document):
        del testing_document["edges"]
        assert parse(testing_document).edges == {}

    def test_an_edge_for_an_operator_the_contract_does_not_declare_is_refused(self, parse, testing_document):
        testing_document["edges"]["regulates"] = {"cause": 0, "effect": 1}
        with pytest.raises(MalformedContract, match="regulates"):
            parse(testing_document)

    def test_an_edge_for_another_namespace_is_refused(self, parse, testing_document):
        testing_document["edges"]["biology/affects-molecular-entity-molecular-entity"] = {"cause": 0, "effect": 1}
        with pytest.raises(MalformedContract, match="own"):
            parse(testing_document)

    def test_an_edge_on_an_operator_without_the_causal_layer_is_refused(self, parse, testing_document):
        testing_document["edges"]["correlates-with"] = {"cause": 0, "effect": 1}
        with pytest.raises(MalformedContract, match="causal"):
            parse(testing_document)

    @pytest.mark.parametrize("body", [{"cause": 0, "effect": 0}, {"cause": 0, "effect": 2}, {"cause": -1, "effect": 1}, {"cause": True, "effect": 1}, {"cause": 0}, {"cause": 0, "effect": 1, "sign": "+"}])
    def test_a_malformed_slot_pair_is_refused(self, parse, testing_document, body):
        testing_document["edges"]["affects"] = body
        with pytest.raises(MalformedContract):
            parse(testing_document)

    def test_succession_never_redefines_an_edge(self, parse, testing_document, genesis):
        successor = copy.deepcopy(testing_document)
        successor["lineage"] = {"successor": genesis.content_identity}
        successor["edges"]["affects"] = {"cause": 1, "effect": 0}
        with pytest.raises(SuccessionViolation, match="edge:affects"):
            parse(successor, predecessor=genesis)

    def test_succession_refuses_dropping_an_edge(self, parse, testing_document, genesis):
        successor = copy.deepcopy(testing_document)
        successor["lineage"] = {"successor": genesis.content_identity}
        del successor["edges"]
        with pytest.raises(SuccessionViolation, match="edge:affects"):
            parse(successor, predecessor=genesis)

    def test_retiring_an_edge_is_permitted_and_tombstoned(self, parse, testing_document, genesis):
        successor = copy.deepcopy(testing_document)
        successor["lineage"] = {"successor": genesis.content_identity}
        successor["edges"]["affects"]["retired"] = True
        contract = parse(successor, predecessor=genesis)
        assert "edge:affects" in contract.retired_identifiers()
```

(`genesis` is the fixture the existing succession tests use at `test_domain_contract.py:273`; reuse it.) Append to `python/tests/test_profile.py`:

```python
def test_edges_compile_under_the_namespaced_operator(base_contract, testing_document):
    from beliefs.contract import parse_domain_contract
    from beliefs.profile import compile_profile

    testing = parse_domain_contract(testing_document, source="<t>", base=base_contract, predecessor=None)
    profile = compile_profile(base_contract, [testing])
    edge = profile.edges["testing/affects"]
    assert (edge.operator, edge.cause, edge.effect, edge.retired, edge.contract) == ("testing/affects", 0, 1, False, "testing")
    assert "testing/correlates-with" not in profile.edges


def test_edges_enter_the_compiled_identity(base_contract, testing_document):
    import copy

    from beliefs.contract import parse_domain_contract
    from beliefs.profile import compile_profile

    with_edge = parse_domain_contract(copy.deepcopy(testing_document), source="<t>", base=base_contract, predecessor=None)
    del testing_document["edges"]
    without = parse_domain_contract(testing_document, source="<t>", base=base_contract, predecessor=None)
    assert compile_profile(base_contract, [with_edge]).compiled_identity != compile_profile(base_contract, [without]).compiled_identity
```

In `ts/tests/declarations.test.ts`, in the domain-facets describe block, add:

```ts
  it("parses the edges table and refuses an undeclared or non-causal operator", () => {
    const domain = parseDomainContract(TESTING, "fixtures/contracts/testing.yaml", base);
    expect(domain.edges.affects).toEqual({ operator: "affects", cause: 0, effect: 1 });
    expect(() => parseDomainContract(TESTING.replace("edges:\n  affects:", "edges:\n  regulates:"), "<bad>", base)).toThrow(/regulates/);
    expect(() => parseDomainContract(TESTING.replace("edges:\n  affects:", "edges:\n  correlates-with:"), "<bad>", base)).toThrow(/causal/);
    expect(() => parseDomainContract(TESTING.replace("{ cause: 0, effect: 1 }", "{ cause: 0, effect: 0 }"), "<bad>", base)).toThrow(/distinct/);
    const profile = compileProfile(base, [domain]);
    expect(profile.edges["testing/affects"]).toEqual({ operator: "testing/affects", cause: 0, effect: 1 });
  });
```

- [ ] **Step 2: The fixtures**

Append to `fixtures/contracts/testing.yaml` after the `operators:` block and before `facets:`:

```yaml
# One edge-forming operator (composite-claims design §3.3): `affects` at the
# causal layer, cause in slot 0, effect in slot 1. `correlates-with` has no row
# on purpose — a statistical operator forms no edge in a `dag`.
edges:
  affects: { cause: 0, effect: 1 }
```

Append to `python/tests/fixtures/biology-fixture.yaml` after its `operators:` block: `edges:\n  affects: { cause: 0, effect: 1 }`. In the same file add three sorts beside `gene`, each `vocabulary: { namespace: EX, release: "2026-01-01" }` — `level`, `measure`, `identification` — and an `estimands:` table with one row for `affects`, spelled exactly as the estimand lane's `fixtures/contracts/testing.yaml` spells its `affects` row (the same keys — `level_sorts` keyed by slot, `measure_sort`, `identification_sort`, and `conditioning_sort` if that fixture carries it — with the three new sorts in place of its). Tasks 4 and 6 type assessments under `WITH_BIOLOGY` with them. `profiles.py` parses the document twice with different descriptions; both variants gain the rows. Run `uv run --frozen pytest tests/test_relocation.py tests/test_world_view_acceptance.py -q`; if either pins the fixture contract's identity, update the pin here.

- [ ] **Step 3: Run the tests to verify they fail**

`uv run --frozen pytest tests/test_domain_contract.py -k Edges tests/test_profile.py -q` — expected: `MalformedContract: unknown field(s) edges` from every test that parses the fixture. `npx vitest run tests/declarations.test.ts` — expected: `edges` unknown field.

- [ ] **Step 4: Python parsing**

In `python/src/beliefs/contract/domain.py`:

```python
_EDGE_FIELDS = frozenset({"cause", "effect"})
_EDGE_OPTIONAL = frozenset({"description", "retired"})


@dataclass(frozen=True)
class EdgeDecl:
    """Which slot of an operator is the cause and which the effect
    (composite-claims design §3.3). The kernel does not assume slot 0 is the
    cause — `binds(A, B)` is symmetric — so the direction is the owner's
    declaration, and an operator with no row forms no edge."""

    operator: str
    cause: int
    effect: int
    retired: bool = False

    def schema_projection(self) -> dict[str, object]:
        return {"cause": self.cause, "effect": self.effect}


def _slot(value: object, arity: int, where: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value < arity:
        raise MalformedContract(f"{where}: a slot is an integer in Fin({arity}), found {value!r}")
    return value


def _parse_edge(name: str, value: object, where: str, operators: Mapping[str, OperatorDecl]) -> EdgeDecl:
    body = _mapping(value, where)
    _fields(body, _EDGE_FIELDS, _EDGE_OPTIONAL, where)
    if "/" in name:
        raise MalformedContract(
            f"{where}: {name!r} names another namespace; a direction is part of what an operator means and only "
            "its own contract may declare it (design §3.3)"
        )
    operator = operators.get(name)
    if operator is None:
        raise MalformedContract(f"{where}: {name!r} is not an operator this contract declares")
    if "causal" not in operator.layers:
        raise MalformedContract(f"{where}: {name!r} admits no causal layer, so it forms no edge")
    cause = _slot(body["cause"], operator.arity, f"{where}: cause")
    effect = _slot(body["effect"], operator.arity, f"{where}: effect")
    if cause == effect:
        raise MalformedContract(f"{where}: cause and effect must be distinct slots, both are {cause}")
    return EdgeDecl(operator=name, cause=cause, effect=effect, retired=_bool(body.get("retired", False), f"{where}: retired"))
```

`DomainContract` gains `edges: Mapping[str, EdgeDecl]` after `operators`; `_parsed` takes `edges: dict[str, EdgeDecl]` and sets it with `MappingProxyType(dict(edges))`; `_declarations()` returns one more group, `*((f"edge:{name}", decl) for name, decl in self.edges.items())`, and its return annotation widens to include `EdgeDecl`. In `parse_domain_contract`, add `"edges"` to the optional set of the existing `_fields(root, _CONTRACT_FIELDS, frozenset({...}), source)` call — the baseline's set already holds `"description"`, `"facets"` and `"estimands"`; extend it, never restate it — and after the operators loop:

```python
    edges: dict[str, EdgeDecl] = {}
    for name, body in _declarations(root.get("edges", {}), f"{source}: edges").items():
        edges[name] = _parse_edge(name, body, f"{source}: edges.{name}", operators)
```

(`_declarations` refuses a non-mapping and a non-name key; the `/` case is unreachable through it and stays in `_parse_edge` for the hand-built path.) Pass `edges=edges` to `_parsed`. `check_succession` needs no change: `claim_vocabulary()` and `retired_identifiers()` read `_declarations()`. Export `EdgeDecl` from `beliefs/contract/__init__.py` beside `OperatorDecl`.

- [ ] **Step 5: The profile**

In `python/src/beliefs/profile.py` add beside `CompiledOperator`:

```python
@dataclass(frozen=True)
class CompiledEdge:
    operator: str
    cause: int
    effect: int
    retired: bool
    contract: str

    def schema_projection(self) -> dict[str, object]:
        return {"cause": self.cause, "effect": self.effect}
```

`ProfileSpec` gains `edges: Mapping[str, CompiledEdge]` after `operators`. In `compile_profile`, after the operators loop inside `for namespace in sorted(seen):`:

```python
        for name, edge in contract.edges.items():
            edges[contract.term(name)] = CompiledEdge(
                operator=contract.term(name), cause=edge.cause, effect=edge.effect, retired=edge.retired, contract=namespace
            )
```

with `edges: dict[str, CompiledEdge] = {}` declared beside `operators`; pass `edges=MappingProxyType(dict(edges))` to `_compiled` and `edges=edges` to `_projection`, whose signature gains `edges: Mapping[str, CompiledEdge]` (keyword-only) and whose dict gains `"edges": {term: edge.schema_projection() for term, edge in sorted(edges.items())}`.

- [ ] **Step 6: TypeScript parity**

In `ts/src/contract.ts` add `export interface EdgeDecl { readonly operator: string; readonly cause: number; readonly effect: number; }`, `readonly edges: DeclarationTable<EdgeDecl>` on `DomainContract`, `"edges"` appended to `parseDomainContract`'s existing optional field list (beside the baseline's `"estimands"`), and after the operators table is built:

```ts
  const edgeEntries: [string, EdgeDecl][] = [];
  for (const [name, body] of Object.entries(declarations("edges" in document ? document.edges : {}, `${source}.edges`))) {
    const where = `${source}.edges.${name}`;
    const edgeBody = mapping(body, where);
    exactFields(edgeBody, ["cause", "effect"], ["description", "retired"], where);
    refuseRetired(edgeBody, where);
    const operator = operators[name];
    if (operator === undefined) throw new MalformedContract(`${where}: ${JSON.stringify(name)} is not an operator this contract declares`);
    if (!operator.layers.includes("causal")) throw new MalformedContract(`${where}: ${JSON.stringify(name)} admits no causal layer`);
    const slot = (value: unknown, label: string): number => {
      if (typeof value !== "number" || !Number.isInteger(value) || value < 0 || value >= operator.arity)
        throw new MalformedContract(`${where}.${label}: a slot is an integer in Fin(${operator.arity})`);
      return value;
    };
    const cause = slot(edgeBody.cause, "cause");
    const effect = slot(edgeBody.effect, "effect");
    if (cause === effect) throw new MalformedContract(`${where}: cause and effect must be distinct slots`);
    edgeEntries.push([name, Object.freeze({ operator: name, cause, effect })]);
  }
  const edges = frozenTable(edgeEntries);
```

(`operators` here is whatever local the existing loop builds its table from — read the surrounding code and use that name.) Carry `edges` on the returned contract. In `ts/src/profile.ts`, `ProfileSpec.edges: ResolutionTable<CompiledEdge>` with `CompiledEdge { operator; cause; effect }` keyed by `term(contract.namespace, name)`, built in the same loop that compiles operators. The TypeScript profile computes no compiled identity, so nothing else changes there.

- [ ] **Step 7: Run the tests to verify they pass**

`uv run --frozen pytest tests/test_domain_contract.py tests/test_profile.py tests/test_profile_agreement.py tests/test_parity_fixture.py -q` green; `npm test` green; then `just test` — the existing parity fixture over the testing contract now carries `edges`, so if `test_parity_fixture.py` or `ts/tests/identity-fixture.test.ts` pins a projection of the *domain contract* or the *profile* it is regenerated with `uv run --frozen python tools/generate_identity_fixture.py` (read its header first; commit the regenerated fixture in this task).

- [ ] **Step 8: Commit**

```bash
git add python/src/beliefs/contract python/src/beliefs/profile.py fixtures python/tests ts
git commit -m "feat(contract): declare edges per operator in a domain contract and compile them (U2)"
```

---

### Task 3: `beliefs/composite.py` — the values, the constructor, classification, identity, the stored shape

**Files:**
- Create: `python/src/beliefs/composite.py`
- Modify: `python/src/beliefs/errors.py` (`CompositeError`), `python/src/beliefs/resolution.py` (`ReferentPosition.node`), `python/src/beliefs/stored.py` (`COMPOSITE_FACET`, `COMPOSES`, `composite_value`, `composite_node`, `__all__`)
- Test: `python/tests/test_composite.py`

**Interfaces:**
- Consumes: `ProfileSpec.composite_grammar`, `ProfileSpec.edges` (Tasks 1, 2); `claim_from_stored(node, *, profile, snapshot)` and `claim_identity(claim)` (existing); `ReadView.get`.
- Produces, at `beliefs.composite`:
  - `CompositeNode(sort: str, term: str)` — frozen, sealed; both identifiers checked as `Referent` checks its fields.
  - `Edge(cause: CompositeNode, effect: CompositeNode, sign: str, member: str)` — `sign` is the member claim's polarity tag as stored (`positive`, `negative`, `unsigned`, or the base's `inapt` tag).
  - `CompositeFacet(grammar: str, shape: str, nodes: tuple[CompositeNode, ...], members: tuple[str, ...])` — the stored shape; `projection()`; `nodes` sorted by `(sort, term)`, `members` sorted, both distinct, `nodes` non-empty, else `MalformedRecord`.
  - `Composite` — opaque; fields `facet: CompositeFacet`, `refs: tuple[str, ...]` (member corpus refs in facet order), `edges: tuple[Edge, ...]`, `slug: str`; no public constructor; `identity` property.
  - `CompositeReceipt(identity: str, snapshot_identity: str, outcomes: Mapping[str, TermOutcome])` keyed `node:<index>`.
  - `build_composite(profile, view, *, shape, nodes, members, snapshot, slug) -> tuple[Composite, CompositeReceipt]`.
  - `classify(profile, facet, claims: Mapping[str, Claim]) -> tuple[Edge, ...]` — pure; `claims` keyed by member identity; the one classification the constructor, the boundary and the audit all call.
  - `composite_identity(facet) -> str` — `v1.digest("science.composite.v1", {"kind": "composite", "present": ["composite"], "facets": {"composite": facet.projection()}})`, which is exactly `stored.recompute_semantic_hash` over the node `composite_node` writes, so the stamp and this identity agree by construction (asserted in Step 1).
  - `EMPTY_SNAPSHOT = build_snapshot()` — the consult-nothing snapshot the boundary and the audit restore member claims under (spec §4.2 step 1: form only).
  - `CompositeError(ScienceError)` with `.code`; codes: `composite-shape`, `composite-nodes-empty`, `composite-duplicate`, `composite-node-not-member`, `composite-member-kind`, `composite-member-unresolvable`, `composite-member-unrestorable`, `composite-member-undeclared`, `composite-member-layer`, `composite-member-outside-nodes`, `composite-cyclic`.
  - `stored.COMPOSITE_FACET = "composite"`, `stored.COMPOSES = "composes"`, `stored.composite_value(node) -> CompositeFacet` (form only; raises `MalformedRecord`), `stored.composite_node(value: Composite, *, title: str) -> Node` (refuses anything but a `Composite`).
- **A note on "claim identity".** The facet stores `claim_identity(claim)` — `I_claim` under `CLAIM_DOMAIN` — for each member. A proposition record's `semantic-identity` stamp is `recompute_semantic_hash(node)`, a digest over `{kind, present, facets}` under `science.proposition.v1`: a different digest over the same information. The spec's "semantic identity" of a member (§3.2, §4.2 step 3) is `I_claim`, and the boundary compares `claim_identity(claim_from_stored(record, …))` to the facet, never the stamp. Task 9 records this as a wording amendment to spec §3.2.

- [ ] **Step 1: Write the failing tests**

Create `python/tests/test_composite.py`:

```python
"""`beliefs.composite` — construction, classification, identity, the stored shape (design §3–§5, U3, U5)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fixtures_cut4 import raw_write, reopen
from nodes.core.node import Node

from beliefs import composite, stored
from beliefs.claim import Referent, build_claim
from beliefs.composite import CompositeNode, CompositeError, build_composite
from beliefs.contract import parse_base_contract, parse_domain_contract
from beliefs.contract.domain import VocabularyBinding
from beliefs.errors import MalformedRecord
from beliefs.profile import compile_profile
from beliefs.projection import claim_identity, project_claim
from beliefs.resolution import TermOutcome, build_snapshot

REPO = Path(__file__).resolve().parents[2]
BASE = parse_base_contract(__import__("yaml").safe_load((REPO / "contracts/science/CONTRACT.yaml").read_text()), source="<base>")
TESTING = parse_domain_contract(__import__("yaml").safe_load((REPO / "fixtures/contracts/testing.yaml").read_text()), source="<t>", base=BASE, predecessor=None)
PROFILE = compile_profile(BASE, [TESTING])
EX = VocabularyBinding(namespace="EX", release="2026-01-01", dataset_identity=None)

ENTITY, OUTCOME = "testing/entity", "testing/outcome"
A, B, C = CompositeNode(ENTITY, "EX:a"), CompositeNode(ENTITY, "EX:b"), CompositeNode(OUTCOME, "EX:y")
CONSULTED = build_snapshot(readable={EX: ["EX:a", "EX:b", "EX:y", "EX:isolated"]})
EXCLUDING = build_snapshot(readable={EX: ["EX:a", "EX:b", "EX:y"]})
UNCONSULTED = build_snapshot()


def _claim(operator: str, cause: str, effect: str, *, polarity: str | None = "positive", layer: str = "causal"):
    sorts = PROFILE.operator(operator).arg_sorts
    return build_claim(PROFILE, operator=operator, args=(Referent(sorts[0], cause), Referent(sorts[1], effect)), layer=layer, polarity=polarity)


def _proposition(slug: str, claim) -> Node:
    return stored.proposition_node(slug, title=slug, claim=project_claim(claim))


def _corpus(tmp_path: Path, *nodes: Node):
    root = tmp_path / "corpus"
    root.mkdir()
    for node in nodes:
        raw_write(root, node)
    return reopen(root)


AB = _claim("testing/affects", "EX:a", "EX:y")            # a → y, positive
NEG = _claim("testing/affects", "EX:b", "EX:y", polarity="negative")


class TestConstruction:
    def test_a_dag_of_two_edges_builds_and_reports_signs(self, tmp_path):
        view = _corpus(tmp_path, _proposition("ab", AB), _proposition("neg", NEG))
        value, receipt = build_composite(PROFILE, view, shape="dag", nodes=[A, B, C], members=["proposition:ab", "proposition:neg"], snapshot=CONSULTED, slug="two")
        assert value.facet.nodes == (A, B, C)  # sorted by (sort, term): entity before outcome
        assert value.facet.members == tuple(sorted([claim_identity(AB), claim_identity(NEG)]))
        assert {(e.cause, e.effect, e.sign) for e in value.edges} == {(A, C, "positive"), (B, C, "negative")}
        assert receipt.identity == value.identity
        assert receipt.outcomes == {"node:0": TermOutcome.MEMBER, "node:1": TermOutcome.MEMBER, "node:2": TermOutcome.MEMBER}

    def test_authoring_order_does_not_move_identity_but_an_isolated_node_does(self, tmp_path):
        view = _corpus(tmp_path, _proposition("ab", AB), _proposition("neg", NEG))
        one, _ = build_composite(PROFILE, view, shape="dag", nodes=[C, B, A], members=["proposition:neg", "proposition:ab"], snapshot=CONSULTED, slug="one")
        two, _ = build_composite(PROFILE, view, shape="dag", nodes=[A, B, C], members=["proposition:ab", "proposition:neg"], snapshot=CONSULTED, slug="two")
        three, _ = build_composite(PROFILE, view, shape="dag", nodes=[A, B, C, CompositeNode(ENTITY, "EX:isolated")], members=["proposition:ab", "proposition:neg"], snapshot=CONSULTED, slug="three")
        assert one.identity == two.identity != three.identity

    def test_nodes_and_no_members_is_legal(self, tmp_path):
        value, receipt = build_composite(PROFILE, _corpus(tmp_path), shape="dag", nodes=[A, B], members=[], snapshot=CONSULTED, slug="empty")
        assert value.edges == () and value.facet.members == ()
        assert set(receipt.outcomes) == {"node:0", "node:1"}

    @pytest.mark.parametrize(
        ("nodes", "members", "code"),
        [
            ([], [], "composite-nodes-empty"),
            ([A, A], [], "composite-duplicate"),
            ([A, C], ["proposition:ab", "proposition:ab"], "composite-duplicate"),
            ([A], ["proposition:ab"], "composite-member-outside-nodes"),
            ([A, C], ["proposition:missing"], "composite-member-unresolvable"),
        ],
    )
    def test_form_refusals(self, tmp_path, nodes, members, code):
        view = _corpus(tmp_path, _proposition("ab", AB))
        with pytest.raises(CompositeError) as caught:
            build_composite(PROFILE, view, shape="dag", nodes=nodes, members=members, snapshot=CONSULTED, slug="x")
        assert caught.value.code == code

    def test_an_unknown_shape_refuses(self, tmp_path):
        with pytest.raises(CompositeError) as caught:
            build_composite(PROFILE, _corpus(tmp_path), shape="pag", nodes=[A], members=[], snapshot=CONSULTED, slug="x")
        assert caught.value.code == "composite-shape"

    def test_a_member_that_is_not_a_proposition_refuses(self, tmp_path):
        dataset = stored.dataset_node("d", title="d", resources=[{"name": "m", "digest": "sha256:" + "1" * 64}])
        with pytest.raises(CompositeError) as caught:
            build_composite(PROFILE, _corpus(tmp_path, dataset), shape="dag", nodes=[A, C], members=[dataset.id], snapshot=CONSULTED, slug="x")
        assert caught.value.code == "composite-member-kind"

    def test_an_undeclared_operator_and_a_non_causal_layer_refuse(self, tmp_path):
        stat = _claim("testing/correlates-with", "EX:a", "EX:y", layer="statistical")
        structural = _claim("testing/subtype-of", "EX:a", "EX:b", polarity=None, layer="structural")
        view = _corpus(tmp_path, _proposition("stat", stat), _proposition("sub", structural))
        with pytest.raises(CompositeError) as caught:
            build_composite(PROFILE, view, shape="dag", nodes=[A, C], members=["proposition:stat"], snapshot=CONSULTED, slug="x")
        assert caught.value.code == "composite-member-undeclared"
        with pytest.raises(CompositeError) as caught:
            build_composite(PROFILE, view, shape="dag", nodes=[A, B], members=["proposition:sub"], snapshot=CONSULTED, slug="x")
        assert caught.value.code == "composite-member-undeclared"  # subtype-of has no edges: row; the layer check never runs

    def test_a_causal_operator_member_at_another_layer_refuses_on_layer(self, tmp_path):
        # `affects` declares an edge, but this claim asserts it at the statistical layer.
        member = _claim("testing/affects", "EX:a", "EX:y", layer="statistical") if "statistical" in PROFILE.operator("testing/affects").layers else None
        if member is None:
            pytest.skip("the fixture's affects admits causal only; the layer arm is exercised by the biology fixture in test_composite_boundary")
        view = _corpus(tmp_path, _proposition("m", member))
        with pytest.raises(CompositeError) as caught:
            build_composite(PROFILE, view, shape="dag", nodes=[A, C], members=["proposition:m"], snapshot=CONSULTED, slug="x")
        assert caught.value.code == "composite-member-layer"

    def test_a_cycle_through_a_negative_edge_refuses(self, tmp_path):
        # entity → outcome only exists under `affects`; a cycle needs an entity-sorted effect, so use `regulates`-shaped
        # claims from the biology fixture: see test_composite_boundary. Here: a two-node cycle over the testing
        # fixture is unconstructible (arg sorts differ), which is itself the assertion.
        pytest.skip("cycle detection is exercised in test_composite_boundary under the biology fixture (gene → gene)")

    def test_an_isolated_node_with_an_undeclared_sort_refuses_in_shared_classification(self, tmp_path):
        from beliefs.composite import CompositeFacet, classify
        from beliefs.contract.base import COMPOSITE_GRAMMAR

        facet = CompositeFacet(grammar=COMPOSITE_GRAMMAR, shape="dag", nodes=(CompositeNode("nowhere/sort", "EX:z"),), members=())
        with pytest.raises(CompositeError) as caught:
            classify(PROFILE, facet, {})
        assert caught.value.code == "composite-node-sort"

    def test_a_retired_edge_declaration_refuses(self, tmp_path):
        import copy

        import yaml

        document = yaml.safe_load((REPO / "fixtures/contracts/testing.yaml").read_text())
        successor = copy.deepcopy(document)
        successor["lineage"] = {"successor": TESTING.content_identity}
        successor["edges"]["affects"]["retired"] = True
        retired = compile_profile(BASE, [parse_domain_contract(successor, source="<r>", base=BASE, predecessor=TESTING)])
        view = _corpus(tmp_path, _proposition("ab", AB))
        with pytest.raises(CompositeError) as caught:
            build_composite(retired, view, shape="dag", nodes=[A, C], members=["proposition:ab"], snapshot=CONSULTED, slug="x")
        assert caught.value.code == "composite-member-retired"

    def test_a_member_whose_stored_claim_fails_typing_is_unrestorable_not_an_escape(self, tmp_path):
        node = _proposition("bad", AB)
        node.facets[stored.PROPOSITION_FACET]["layer"] = "methodological"  # affects admits causal only
        stored.stamp_semantic_identity(node)
        view = _corpus(tmp_path, node)
        with pytest.raises(CompositeError) as caught:
            build_composite(PROFILE, view, shape="dag", nodes=[A, C], members=["proposition:bad"], snapshot=CONSULTED, slug="x")
        assert caught.value.code == "composite-member-unrestorable"

    def test_an_isolated_node_a_consulted_vocabulary_excludes_refuses(self, tmp_path):
        view = _corpus(tmp_path, _proposition("ab", AB))
        with pytest.raises(CompositeError) as caught:
            build_composite(PROFILE, view, shape="dag", nodes=[A, C, CompositeNode(ENTITY, "EX:isolated")], members=["proposition:ab"], snapshot=EXCLUDING, slug="x")
        assert caught.value.code == "composite-node-not-member"
        assert "EX:isolated" in str(caught.value)

    def test_an_isolated_node_under_an_unconsulted_vocabulary_is_admitted_and_recorded(self, tmp_path):
        view = _corpus(tmp_path, _proposition("ab", AB))
        value, receipt = build_composite(PROFILE, view, shape="dag", nodes=[A, C, CompositeNode(ENTITY, "EX:isolated")], members=["proposition:ab"], snapshot=UNCONSULTED, slug="x")
        assert receipt.outcomes["node:1"] == TermOutcome.NOT_CONSULTED  # (entity, EX:isolated) sorts after (entity, EX:a)
        assert receipt.snapshot_identity == UNCONSULTED.identity
        assert len(value.facet.nodes) == 3

    def test_a_snapshot_is_required(self, tmp_path):
        with pytest.raises(TypeError):
            build_composite(PROFILE, _corpus(tmp_path), shape="dag", nodes=[A], members=[], slug="x")  # type: ignore[call-arg]

    def test_the_value_has_no_public_constructor(self):
        with pytest.raises(CompositeError):
            composite.Composite()  # type: ignore[call-arg]


class TestStoredShape:
    def test_composite_node_writes_the_facet_and_one_composes_edge_per_member(self, tmp_path):
        view = _corpus(tmp_path, _proposition("ab", AB), _proposition("neg", NEG))
        value, _ = build_composite(PROFILE, view, shape="dag", nodes=[A, B, C], members=["proposition:neg", "proposition:ab"], snapshot=CONSULTED, slug="two")
        node = stored.composite_node(value, title="two")
        assert node.id == "composite:two" and node.kind == "composite"
        facet = stored.composite_value(node)
        assert facet == value.facet
        assert [r.predicate for r in node.relations] == [stored.COMPOSES, stored.COMPOSES]
        assert [r.target for r in node.relations] == list(value.refs)  # facet order, i.e. sorted by member identity
        assert stored.stored_semantic_hash(node) == value.identity == composite.composite_identity(value.facet)

    def test_composite_node_refuses_a_hand_built_value(self):
        with pytest.raises(MalformedRecord):
            stored.composite_node(object(), title="x")  # type: ignore[arg-type]

    @pytest.mark.parametrize(
        "mutate",
        [
            lambda f: f.__setitem__("grammar", "science.composite.v2"),
            lambda f: f.__setitem__("shape", 1),
            lambda f: f.__setitem__("nodes", []),
            lambda f: f.__setitem__("nodes", [{"sort": ENTITY, "term": "EX:a"}, {"sort": ENTITY, "term": "EX:a"}]),
            lambda f: f.__setitem__("nodes", [{"sort": OUTCOME, "term": "EX:y"}, {"sort": ENTITY, "term": "EX:a"}]),  # unsorted
            lambda f: f.__setitem__("members", ["b", "a"]),
            lambda f: f.__setitem__("members", ["a", 7]),
            lambda f: f.__setitem__("extra", 1),
            lambda f: f.pop("members"),
        ],
    )
    def test_composite_value_refuses_a_malformed_facet(self, tmp_path, mutate):
        view = _corpus(tmp_path, _proposition("ab", AB))
        value, _ = build_composite(PROFILE, view, shape="dag", nodes=[A, C], members=["proposition:ab"], snapshot=CONSULTED, slug="x")
        node = stored.composite_node(value, title="x")
        mutate(node.facets[stored.COMPOSITE_FACET])
        with pytest.raises(MalformedRecord):
            stored.composite_value(node)
```

- [ ] **Step 2: Run the tests to verify they fail**

`uv run --frozen pytest tests/test_composite.py -q` — expected: `ImportError: cannot import name 'composite'`.

- [ ] **Step 3: Errors and the referent position**

In `python/src/beliefs/errors.py`, after `SignatureRefused`:

```python
class CompositeError(RecordError):
    """A composite refused at construction, at the boundary or at reading
    (composite-claims design §3.4, §4). `code` is the stable name the design
    tables carry; the message names the position."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
```

In `python/src/beliefs/resolution.py`, on `ReferentPosition`:

```python
    @classmethod
    def node(cls, index: int) -> ReferentPosition:
        """A composite's node, by position in its sorted node set (design §4.1)."""
        return cls(kind="node", key=str(index))
```

and widen the `kind` docstring to `argument`, `restriction` or `node`.

- [ ] **Step 4: The module**

Create `python/src/beliefs/composite.py`:

```python
"""Composite claims (composite-claims design §3–§5): a declared node set over
propositions whose typed claims form the directed edges of one shape.

The value is built, never authored; its members are corpus refs resolved
through a read view; its nodes are resolved through a `ResolutionSnapshot`
that is a required argument, for the reason `decode_claim`'s is. `classify`
is the one classification the constructor, the write boundary and the audit
share, so the three cannot disagree about what a member contributes.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import final

from nodes.core.errors import RefError
from nodes.core.node import Node

from beliefs.claim import Claim, _require_referent_identifier
from beliefs.contract.base import COMPOSITE_GRAMMAR
from beliefs.decode import claim_from_stored
from beliefs.errors import ClaimError, CompositeError, DecodeError, MalformedRecord, ProfileError
from beliefs.identity import v1
from beliefs.profile import ProfileSpec
from beliefs.projection import claim_identity
from beliefs.resolution import ReferentPosition, ResolutionSnapshot, TermOutcome, build_snapshot
from beliefs.sealed import sealed

COMPOSITE_DOMAIN = "science.composite.v1"
EMPTY_SNAPSHOT = build_snapshot()
"""The consult-nothing snapshot. The boundary and the audit restore member
claims under it (design §4.2 step 1): every referent resolves
`not-consulted`, nothing refuses, and membership is left to the constructor
and the reading, which take a caller's snapshot."""

_MINT = object()


@sealed
@final
@dataclass(frozen=True)
class CompositeNode:
    sort: str
    term: str

    def __post_init__(self) -> None:
        _require_referent_identifier(self.sort, "a node's sort")
        _require_referent_identifier(self.term, "a node's term")

    def projection(self) -> dict[str, str]:
        return {"sort": self.sort, "term": self.term}


@sealed
@final
@dataclass(frozen=True)
class Edge:
    cause: CompositeNode
    effect: CompositeNode
    sign: str
    member: str


@sealed
@final
@dataclass(frozen=True)
class CompositeFacet:
    grammar: str
    shape: str
    nodes: tuple[CompositeNode, ...]
    members: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.grammar != COMPOSITE_GRAMMAR:
            raise MalformedRecord(f"a composite facet carries grammar {COMPOSITE_GRAMMAR!r}, found {self.grammar!r}")
        if type(self.shape) is not str or not self.shape:
            raise MalformedRecord("a composite's shape is a non-empty tag")
        if type(self.nodes) is not tuple or any(type(n) is not CompositeNode for n in self.nodes):
            raise MalformedRecord("a composite's nodes are CompositeNode values")
        if not self.nodes:
            raise MalformedRecord("a composite declares at least one node")
        if type(self.members) is not tuple or any(type(m) is not str or not m for m in self.members):
            raise MalformedRecord("a composite's members are non-empty claim-identity strings")
        # Types first, order second: sorting a list holding a non-string raises
        # TypeError, which is not a refusal anything downstream translates.
        keys = [(n.sort, n.term) for n in self.nodes]
        if keys != sorted(keys) or len(set(keys)) != len(keys):
            raise MalformedRecord("a composite's nodes are sorted by (sort, term) and distinct; refused, never tidied")
        if list(self.members) != sorted(self.members) or len(set(self.members)) != len(self.members):
            raise MalformedRecord("a composite's members are sorted and distinct; refused, never tidied")

    def projection(self) -> dict[str, object]:
        return {
            "grammar": self.grammar,
            "shape": self.shape,
            "nodes": [n.projection() for n in self.nodes],
            "members": list(self.members),
        }


def composite_identity(facet: CompositeFacet) -> str:
    """The content identity, taken over exactly what `stored.semantic_projection`
    digests for the node `composite_node` writes, so the stamp agrees."""
    return v1.digest(COMPOSITE_DOMAIN, {"kind": "composite", "present": ["composite"], "facets": {"composite": facet.projection()}})


@sealed
@final
@dataclass(frozen=True, init=False)
class Composite:
    facet: CompositeFacet
    refs: tuple[str, ...]
    edges: tuple[Edge, ...]
    slug: str

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise CompositeError("composite-unbuilt", "Composite is built, never authored — use build_composite(...)")

    @classmethod
    def _checked(cls, token: object, **fields: object) -> Composite:
        if token is not _MINT:
            raise CompositeError("composite-unbuilt", "Composite._checked is build_composite's own route")
        value = object.__new__(cls)
        for name, field in fields.items():
            object.__setattr__(value, name, field)
        return value

    @property
    def identity(self) -> str:
        return composite_identity(self.facet)


@dataclass(frozen=True)
class CompositeReceipt:
    identity: str
    snapshot_identity: str
    outcomes: Mapping[str, TermOutcome]

    def __post_init__(self) -> None:
        object.__setattr__(self, "outcomes", MappingProxyType(dict(self.outcomes)))


def _canonical_nodes(nodes: Iterable[object]) -> tuple[CompositeNode, ...]:
    listed = list(nodes)
    for node in listed:
        if type(node) is not CompositeNode:
            raise CompositeError("composite-node", f"{node!r} is not a CompositeNode")
    if not listed:
        raise CompositeError("composite-nodes-empty", "a composite over no nodes asserts nothing")
    keys = [(n.sort, n.term) for n in listed]
    if len(set(keys)) != len(keys):
        dup = next(k for k in keys if keys.count(k) > 1)
        raise CompositeError("composite-duplicate", f"node {dup} appears twice")
    return tuple(sorted(listed, key=lambda n: (n.sort, n.term)))


def require_node_sorts(profile: ProfileSpec, nodes: Sequence[CompositeNode]) -> None:
    """Every node's sort is one the profile declares — isolated nodes included,
    since no member's claim ever names them and nothing else would look."""
    for index, node in enumerate(nodes):
        if node.sort not in profile.sorts:
            raise CompositeError("composite-node-sort", f"node {index}: {node.sort!r} is not a sort this profile declares")


def classify(profile: ProfileSpec, facet: CompositeFacet, claims: Mapping[str, Claim]) -> tuple[Edge, ...]:
    """§3.4's table for `shape: dag`. `claims` is keyed by member identity and
    must cover every member; a missing key is the caller's defect. The whole
    node-set contract is checked here, because this is the one function the
    constructor, the boundary and the audit share."""
    if facet.shape not in profile.composite_grammar.shapes:
        raise CompositeError("composite-shape", f"{facet.shape!r} is not a shape the base contract declares ({profile.composite_grammar.shapes})")
    require_node_sorts(profile, facet.nodes)
    declared = {(n.sort, n.term): n for n in facet.nodes}
    edges: list[Edge] = []
    for member in facet.members:
        claim = claims[member]
        edge = profile.edges.get(claim.operator)
        if edge is None:
            raise CompositeError("composite-member-undeclared", f"member {member}: operator {claim.operator!r} declares no edge")
        if edge.retired:
            raise CompositeError("composite-member-retired", f"member {member}: the edge declaration for {claim.operator!r} is retired; a retired row types history and admits no new structure (§7.3a)")
        if claim.layer != "causal":
            raise CompositeError("composite-member-layer", f"member {member}: layer {claim.layer!r} forms no edge in a dag; the inhabited fragment is the causal layer")
        # Every argument must be a declared node, not only the two the edge
        # reads: a ternary operator's third slot is part of the claim the
        # composite asserts over these nodes.
        for slot, referent in enumerate(claim.args):
            if (referent.sort, referent.term) not in declared:
                raise CompositeError("composite-member-outside-nodes", f"member {member}: argument {slot} ({referent.sort}, {referent.term}) is not a declared node")
        cause, effect = (declared[(claim.args[slot].sort, claim.args[slot].term)] for slot in (edge.cause, edge.effect))
        edges.append(Edge(cause=cause, effect=effect, sign=claim.polarity, member=member))
    _refuse_cycle(facet.nodes, edges)
    return tuple(edges)


def _refuse_cycle(nodes: Sequence[CompositeNode], edges: Sequence[Edge]) -> None:
    """Every member is an arrow, whatever its sign (§3.4); a cycle through a
    negative edge is a cycle. Depth-first, reporting the first cycle found."""
    out: dict[CompositeNode, list[CompositeNode]] = {n: [] for n in nodes}
    for edge in edges:
        out[edge.cause].append(edge.effect)
    state: dict[CompositeNode, int] = {}
    stack: list[CompositeNode] = []

    def visit(node: CompositeNode) -> None:
        state[node] = 1
        stack.append(node)
        for nxt in out[node]:
            if state.get(nxt) == 1:
                cycle = stack[stack.index(nxt):] + [nxt]
                raise CompositeError("composite-cyclic", "cycle " + " -> ".join(f"({n.sort}, {n.term})" for n in cycle))
            if nxt not in state:
                visit(nxt)
        stack.pop()
        state[node] = 2

    for node in nodes:
        if node not in state:
            visit(node)


def restore_members(view: object, facet_members: Sequence[str], refs: Sequence[str], *, profile: ProfileSpec, snapshot: ResolutionSnapshot) -> dict[str, Claim]:
    """Resolve each member ref to a proposition and restore its claim; refuse a
    non-proposition, an unresolvable ref, or an unrestorable claim. Shared by
    the boundary and the audit (`EMPTY_SNAPSHOT`) and by the reading."""
    claims: dict[str, Claim] = {}
    for member, ref in zip(facet_members, refs, strict=True):
        try:
            node = view.get(ref)  # type: ignore[attr-defined]
        except RefError as caught:
            raise CompositeError("composite-member-unresolvable", f"member {ref} does not resolve in this corpus") from caught
        if node.kind != "proposition":
            raise CompositeError("composite-member-kind", f"member {ref} is a {node.kind!r}, not a proposition")
        try:
            claim, _ = claim_from_stored(node, profile=profile, snapshot=snapshot)
        except (DecodeError, ClaimError, ProfileError) as caught:
            # `claim_from_stored` raises all three families: a malformed wire
            # claim, a claim that fails typing (`InadmissibleLayer`, an arity or
            # sort mismatch), an operator no contract declares. None is a
            # `RecordError`, so each is translated here or it escapes the audit.
            raise CompositeError("composite-member-unrestorable", f"member {ref}: {caught}") from caught
        if claim_identity(claim) != member:
            raise CompositeError("composite-member-mismatch", f"member {ref} carries claim {claim_identity(claim)}, the facet names {member}")
        claims[member] = claim
    return claims


def build_composite(
    profile: ProfileSpec,
    view: object,
    *,
    shape: str,
    nodes: Iterable[CompositeNode],
    members: Iterable[str],
    snapshot: ResolutionSnapshot,
    slug: str,
) -> tuple[Composite, CompositeReceipt]:
    if not isinstance(profile, ProfileSpec):
        raise CompositeError("composite-profile", f"profile is a {type(profile).__name__}, not a compiled ProfileSpec")
    if not isinstance(snapshot, ResolutionSnapshot):
        raise CompositeError("composite-snapshot", f"snapshot is a {type(snapshot).__name__}, not a ResolutionSnapshot — use build_snapshot(...); availability is a parameter, never ambient")
    if type(slug) is not str or not slug:
        raise CompositeError("composite-slug", "a composite's local id is a non-empty string")
    canonical_nodes = _canonical_nodes(nodes)
    if shape not in profile.composite_grammar.shapes:
        raise CompositeError("composite-shape", f"{shape!r} is not a shape the base contract declares ({profile.composite_grammar.shapes})")

    refs = list(members)
    if len(set(refs)) != len(refs):
        raise CompositeError("composite-duplicate", "a member ref appears twice")
    # Resolve first under the caller's snapshot: a member whose own referents
    # the snapshot excludes cannot be classified, and says so.
    by_ref: dict[str, Claim] = {}
    for ref in refs:
        try:
            node = view.get(ref)  # type: ignore[attr-defined]
        except RefError as caught:
            raise CompositeError("composite-member-unresolvable", f"member {ref} does not resolve in this corpus") from caught
        if node.kind != "proposition":
            raise CompositeError("composite-member-kind", f"member {ref} is a {node.kind!r}, not a proposition")
        try:
            claim, _ = claim_from_stored(node, profile=profile, snapshot=snapshot)
        except (DecodeError, ClaimError, ProfileError) as caught:
            raise CompositeError("composite-member-unrestorable", f"member {ref}: {caught}") from caught
        by_ref[ref] = claim
    identities = {ref: claim_identity(claim) for ref, claim in by_ref.items()}
    if len(set(identities.values())) != len(identities):
        raise CompositeError("composite-duplicate", "two member refs carry one claim identity")
    ordered_refs = tuple(sorted(refs, key=identities.__getitem__))
    facet = CompositeFacet(
        grammar=COMPOSITE_GRAMMAR,
        shape=shape,
        nodes=canonical_nodes,
        members=tuple(identities[ref] for ref in ordered_refs),
    )

    require_node_sorts(profile, canonical_nodes)
    outcomes: dict[str, TermOutcome] = {}
    for index, node in enumerate(canonical_nodes):
        outcomes[ReferentPosition.node(index).label()] = snapshot.resolve(profile.sorts[node.sort].vocabulary, node.term)
    refused = [label for label, outcome in outcomes.items() if outcome.refuses]
    if refused:
        named = ", ".join(f"{label} ({canonical_nodes[int(label.partition(':')[2])].term})" for label in refused)
        raise CompositeError("composite-node-not-member", f"{named}: the term is not in the vocabulary its sort binds, and the vocabulary was read")

    edges = classify(profile, facet, {identities[ref]: claim for ref, claim in by_ref.items()})
    value = Composite._checked(_MINT, facet=facet, refs=ordered_refs, edges=edges, slug=slug)
    return value, CompositeReceipt(identity=value.identity, snapshot_identity=snapshot.identity, outcomes=outcomes)
```

(`_require_referent_identifier` is `claim.py`'s existing checker; import it by name or lift it to a public `require_identifier` in the same commit — do the latter if `claim.py`'s `__all__` is strict.) `beliefs.sealed` is the existing `@sealed` decorator module (`grep -rn "^def sealed" python/src/beliefs`); use whatever `claim.py` imports.

- [ ] **Step 5: The stored shape**

In `python/src/beliefs/stored.py`, add the constants beside `ASSESSMENT_FACET` / the relation names, and the reader and writer beside `coreference_attestation_value`/`_node`:

```python
COMPOSITE_FACET = "composite"
COMPOSES = "composes"
```

```python
def composite_value(node: Node) -> "CompositeFacet":
    """The facet reader the base contract names for the kind — form only
    (composite-claims design §4.2 step 1): grammar tag, shape tag, canonical
    nodes, canonical members. Membership of a node's term in its vocabulary
    is never read here."""
    from beliefs.composite import CompositeFacet, CompositeNode
    from beliefs.errors import ClaimError

    facet = _facet(node, COMPOSITE_FACET)
    if facet is None:
        raise MalformedRecord(f"{node.id}: a composite carries a {COMPOSITE_FACET!r} facet")
    if set(facet) != {"grammar", "shape", "nodes", "members"}:
        raise MalformedRecord(f"{node.id}: composite facet keys are grammar, shape, nodes, members; found {sorted(facet)}")
    raw_nodes, raw_members = facet["nodes"], facet["members"]
    if not isinstance(raw_nodes, list) or not isinstance(raw_members, list):
        raise MalformedRecord(f"{node.id}: nodes and members are lists")
    nodes = []
    for entry in raw_nodes:
        if not isinstance(entry, dict) or set(entry) != {"sort", "term"} or not all(isinstance(entry[k], str) for k in entry):
            raise MalformedRecord(f"{node.id}: a node is {{sort, term}} of strings")
        try:
            nodes.append(CompositeNode(entry["sort"], entry["term"]))
        except ClaimError as caught:  # the identifier checks are `Referent`'s, a ClaimError family
            raise MalformedRecord(f"{node.id}: {caught}") from caught
    try:
        return CompositeFacet(grammar=facet["grammar"], shape=facet["shape"], nodes=tuple(nodes), members=tuple(raw_members))
    except MalformedRecord as caught:
        raise MalformedRecord(f"{node.id}: {caught}") from caught


def composite_node(value: "Composite", *, title: str) -> Node:
    from beliefs.composite import Composite

    if type(value) is not Composite:
        raise MalformedRecord("composite_node writes a built Composite and nothing else")
    node_id = f"composite:{value.slug}"
    relations = [Relation(source=node_id, predicate=COMPOSES, target=ref) for ref in value.refs]
    return _node("composite", value.slug, title, {COMPOSITE_FACET: value.facet.projection()}, relations)
```

Add both names and both constants to `__all__`. The import is local to avoid a cycle (`composite.py` imports `decode`, which imports nothing from `stored`; `stored` must not import `composite` at module load).

- [ ] **Step 6: Run the tests to verify they pass**

`uv run --frozen pytest tests/test_composite.py -q` green (two tests skip by design and are covered in Task 4). `uv run --frozen pyright` from `python/` clean.

- [ ] **Step 7: Commit**

```bash
git add python/src/beliefs/composite.py python/src/beliefs/errors.py python/src/beliefs/resolution.py python/src/beliefs/stored.py python/tests/test_composite.py
git commit -m "feat(composite): build, classify and store a composite over propositions under a resolution snapshot (U3, U5)"
```

---
### Task 4: The write boundary — `_refuse_composite`, the same-kind rule, `supersede` widened

**Files:**
- Modify: `python/src/beliefs/corpus.py` (`_refuse` at 2861, `supersede` at 2382, two new refusal helpers)
- Test: `python/tests/test_composite_boundary.py`

**Interfaces:**
- Consumes: `composite.classify`, `composite.restore_members`, `composite.EMPTY_SNAPSHOT`, `stored.composite_value`, `stored.COMPOSES` (Task 3); `KIND_ACTS["composite"]` (Task 1).
- Produces: every `CorpusWriter` route in — `add`, `supersede`, `import_bundle`, `move`'s destination half through `_add_locked` — refusing a malformed composite with its `CompositeError` code, refusing any record carrying a `supersedes` edge to a record of another kind with `SignatureRefused("<id>: supersedes-cross-kind: …")`, and refusing an assessment whose `assesses` edge resolves to anything but a proposition with `SignatureRefused("<id>: assesses-target-kind: …")` — the guard U4 needs, since `eligibility_refusal` reads the run and the observed dataset and never the target's kind (found in review: an otherwise eligible assessment naming `composite:x` passes it); `supersede(successor, of=)` admitting a same-kind `composite` pair.

- [ ] **Step 1: Write the failing tests**

Create `python/tests/test_composite_boundary.py`:

```python
"""The composite write boundary (design §4.2, U3, U6, U9)."""

from __future__ import annotations

from decimal import Decimal

import pytest
from authority import ACTOR, FULL
from fixtures_cut4 import raw_write, reopen
from nodes.core.node import Node
from nodes.core.relations import Relation
from nodes.core.write_plan import DefaultExecutor
from profiles import WITH_BIOLOGY, pins_for
from test_corpus_write import OperationRecorder

from beliefs import stored
from beliefs.claim import Referent, build_claim
from beliefs.composite import CompositeNode, CompositeError, build_composite
from beliefs.contract.domain import VocabularyBinding
from beliefs.corpus import CorpusWriter, superseded_by
from beliefs.errors import FamilyKindUnsupported, ImportRefused, SignatureRefused, SupersedeIdentityUnchanged
from beliefs.estimand import Control, LevelsContrast, Measure, build_estimand
from beliefs.projection import claim_identity, project_claim
from beliefs.resolution import build_snapshot

GENE = "biology/gene"
AFFECTS = "biology/affects"
EX = VocabularyBinding(namespace="EX", release="2026-01-01", dataset_identity=None)
# Every biology-fixture sort binds `EX/2026-01-01`, so one binding carries the nodes and the estimand's terms.
SNAPSHOT = build_snapshot(readable={EX: ["EX:a", "EX:b", "EX:c", "EX:lo", "EX:hi", "EX:expr", "EX:observational"]})
A, B, C = (CompositeNode(GENE, f"EX:{t}") for t in "abc")
IMPORT = {"observer": "o", "instrument": "i", "opened_at": "2026-09-12T00:00:00Z", "closed_at": "2026-09-12T00:00:01Z"}


def _estimand(claim):
    """A typed estimand for a biology-fixture `affects` claim, under the profile that stores and restores it —
    the fixture's `estimands:` row for `affects` (Task 2) names `biology/level`, `biology/measure`, `biology/identification`."""
    estimand, _ = build_estimand(
        WITH_BIOLOGY, claim, snapshot=SNAPSHOT,
        contrast=LevelsContrast(slot=0, baseline=Referent("biology/level", "EX:lo"), comparison=Referent("biology/level", "EX:hi")),
        measure=Measure(quantity=Referent("biology/measure", "EX:expr"), scale="additive"),
        reference=Decimal("0"),
        control=Control(identification=Referent("biology/identification", "EX:observational"), conditioning=()),
    )
    return estimand


def _writer(root):
    port = OperationRecorder(root, authority=FULL, profile=WITH_BIOLOGY)
    writer = CorpusWriter(root, DefaultExecutor, authority=FULL, profile=WITH_BIOLOGY, operation_port=port)
    writer.adopt_manifest(profile=pins_for(WITH_BIOLOGY))
    return writer


def _claim(cause: str, effect: str, polarity: str = "positive"):
    return build_claim(WITH_BIOLOGY, operator=AFFECTS, args=(Referent(GENE, cause), Referent(GENE, effect)), layer="causal", polarity=polarity)


def _proposition(writer, slug: str, claim) -> Node:
    return writer.add(stored.proposition_node(slug, title=slug, claim=project_claim(claim)))


@pytest.fixture()
def writer(tmp_path):
    w = _writer(tmp_path / "corpus")
    _proposition(w, "ab", _claim("EX:a", "EX:b"))
    _proposition(w, "bc", _claim("EX:b", "EX:c", polarity="negative"))
    _proposition(w, "ca", _claim("EX:c", "EX:a"))
    return w


def _build(writer, members, nodes=(A, B, C), slug="g"):
    value, _ = build_composite(WITH_BIOLOGY, writer.read_view, shape="dag", nodes=list(nodes), members=list(members), snapshot=SNAPSHOT, slug=slug)
    return value


def test_add_admits_a_signed_chain_and_the_reading_view_resolves_its_members(writer):
    minted = writer.add(stored.composite_node(_build(writer, ["proposition:ab", "proposition:bc"]), title="a→b⊣c"))
    node = writer.read_view.get(minted.id)
    assert {r.target for r in node.relations} == {"proposition:ab", "proposition:bc"}
    assert {e.sign for e in _build(writer, ["proposition:ab", "proposition:bc"]).edges} == {"positive", "negative"}


def test_a_cycle_through_the_negative_edge_refuses_at_construction_and_at_add(writer):
    with pytest.raises(CompositeError) as caught:
        _build(writer, ["proposition:ab", "proposition:bc", "proposition:ca"])
    assert caught.value.code == "composite-cyclic" and "EX:b" in str(caught.value)
    # Hand-assemble the same record behind the constructor and push it through `add`.
    acyclic = stored.composite_node(_build(writer, ["proposition:ab", "proposition:bc"]), title="x")
    facet = acyclic.facets[stored.COMPOSITE_FACET]
    ca = claim_identity(_claim("EX:c", "EX:a"))
    facet["members"] = sorted([*facet["members"], ca])
    refs = {claim_identity(_claim("EX:a", "EX:b")): "proposition:ab", claim_identity(_claim("EX:b", "EX:c", "negative")): "proposition:bc", ca: "proposition:ca"}
    acyclic.relations = [Relation(source=acyclic.id, predicate=stored.COMPOSES, target=refs[m]) for m in facet["members"]]
    stored.stamp_semantic_identity(acyclic)
    with pytest.raises(CompositeError) as caught:
        writer.add(acyclic)
    assert caught.value.code == "composite-cyclic"


def test_add_checks_form_and_never_vocabulary(writer):
    excluding = build_snapshot(readable={EX: ["EX:a", "EX:b"]})
    with pytest.raises(CompositeError) as caught:
        build_composite(WITH_BIOLOGY, writer.read_view, shape="dag", nodes=[A, B, C], members=["proposition:ab"], snapshot=excluding, slug="iso")
    assert caught.value.code == "composite-node-not-member"
    value, _ = build_composite(WITH_BIOLOGY, writer.read_view, shape="dag", nodes=[A, B, C], members=["proposition:ab"], snapshot=build_snapshot(), slug="iso")
    minted = writer.add(stored.composite_node(value, title="iso"))  # the boundary holds no snapshot (§4.2 step 1)
    assert writer.read_view.get(minted.id).kind == "composite"


@pytest.mark.parametrize(
    ("mutate", "code"),
    [
        (lambda n: n.relations.pop(), "composite-relations-mismatch"),
        (lambda n: n.relations.__setitem__(0, Relation(source=n.id, predicate=stored.COMPOSES, target="proposition:bc")), "composite-member-mismatch"),
        (lambda n: n.relations.__setitem__(0, Relation(source=n.id, predicate=stored.COMPOSES, target="proposition:missing")), "composite-member-unresolvable"),
        (lambda n: n.relations.append(Relation(source=n.id, predicate=stored.COMPOSES, target="proposition:bc")), "composite-relations-mismatch"),
        (lambda n: n.facets[stored.COMPOSITE_FACET].__setitem__("shape", "pag"), "composite-shape"),
    ],
)
def test_the_boundary_re_derives_every_check_from_the_stored_record(writer, mutate, code):
    node = stored.composite_node(_build(writer, ["proposition:ab"]), title="x")
    mutate(node)
    stored.stamp_semantic_identity(node)
    with pytest.raises(CompositeError) as caught:
        writer.add(node)
    assert caught.value.code == code


def test_a_dataset_member_refuses_with_its_code(writer):
    dataset = writer.add(stored.dataset_node("d", title="d", resources=[{"name": "m", "digest": "sha256:" + "1" * 64}]))
    node = stored.composite_node(_build(writer, ["proposition:ab"]), title="x")
    node.relations[0] = Relation(source=node.id, predicate=stored.COMPOSES, target=dataset.id)
    stored.stamp_semantic_identity(node)
    with pytest.raises(CompositeError) as caught:
        writer.add(node)
    assert caught.value.code == "composite-member-kind"


class TestSupersession:
    def test_a_same_kind_successor_is_admitted_and_the_relation_is_authored_by_the_adapter(self, writer):
        first = writer.add(stored.composite_node(_build(writer, ["proposition:ab"], slug="v1"), title="v1"))
        second = writer.supersede(stored.composite_node(_build(writer, ["proposition:ab", "proposition:bc"], slug="v2"), title="v2"), of=first.id)
        assert superseded_by(writer.read_view, first.id) == (second.id,)
        assert any(r.predicate == stored.SUPERSEDES and r.target == first.id for r in writer.read_view.get(second.id).relations)

    def test_an_identity_unchanged_successor_refuses(self, writer):
        first = writer.add(stored.composite_node(_build(writer, ["proposition:ab"], slug="v1"), title="v1"))
        with pytest.raises(SupersedeIdentityUnchanged):
            writer.supersede(stored.composite_node(_build(writer, ["proposition:ab"], slug="v2"), title="v2"), of=first.id)

    def test_supersede_refuses_a_cross_kind_pair_before_the_shared_check(self, writer):
        first = writer.add(stored.composite_node(_build(writer, ["proposition:ab"], slug="v1"), title="v1"))
        with pytest.raises(FamilyKindUnsupported):
            writer.supersede(stored.proposition_node("p2", title="p2", claim=project_claim(_claim("EX:a", "EX:c"))), of=first.id)

    @pytest.mark.parametrize("direction", ["composite-over-proposition", "proposition-over-composite"])
    def test_add_and_import_refuse_a_cross_kind_supersedes_edge_on_the_shared_path(self, writer, tmp_path, direction):
        first = writer.add(stored.composite_node(_build(writer, ["proposition:ab"], slug="v1"), title="v1"))
        if direction == "composite-over-proposition":
            record = stored.composite_node(_build(writer, ["proposition:bc"], slug="v2"), title="v2")
            target = "proposition:ab"
        else:
            record = stored.proposition_node("p2", title="p2", claim=project_claim(_claim("EX:a", "EX:c")))
            target = first.id
        record.relations.append(Relation(source=record.id, predicate=stored.SUPERSEDES, target=target))
        stored.stamp_semantic_identity(record)
        with pytest.raises(SignatureRefused, match="supersedes-cross-kind"):
            writer.add(record)
        other = _writer(tmp_path / "other")
        members = tuple(n for n in writer.read_view.iter_stored() if n.kind in {"proposition", "composite"}) + (record,)
        with pytest.raises(ImportRefused, match="supersedes-cross-kind") as caught:
            other.import_bundle(members, **IMPORT)
        assert caught.value.member == record.id

    def _typed_assessment(self, writer, slug: str, target: str):
        """Otherwise valid evidence: an attested, held-shaped dataset, an observing run, and an assessment typed
        under the fixture profile (the estimand lane's constructor requires `estimand` and `applicability`)."""
        from test_evaluation import _resources

        if not writer.read_view.holds("dataset:d-a"):
            writer.add(stored.dataset_node("d-a", title="d-a", resources=_resources("a"), empirical_observation={"locator": "instrument:fixture", "attested_by": ACTOR}))
        run = writer.add(stored.run_node(f"run-{slug}", title=slug, spec=f"spec-{slug}", observes=["dataset:d-a"]))
        return stored.assessment_node(
            slug, title=slug, spec=f"spec-{slug}", run=run.id, proposition=target, outcome="supported", interpretation_rule="rule-1",
            estimand=_estimand(_claim("EX:a", "EX:b")), applicability={},
        )

    def test_an_assessment_targeting_a_composite_is_refused_by_kind_at_add_and_at_import(self, writer, tmp_path):
        composite = writer.add(stored.composite_node(_build(writer, ["proposition:ab"], slug="v1"), title="v1"))
        assessment = self._typed_assessment(writer, "a-x", composite.id)
        # The typed constructor admits it; only the target's kind is wrong.
        assert stored.assessment_value(assessment, profile=writer.profile).proposition == composite.id
        with pytest.raises(SignatureRefused, match="assesses-target-kind"):
            writer.add(assessment)
        other = _writer(tmp_path / "other")
        members = tuple(n for n in writer.read_view.iter_stored() if n.kind in {"proposition", "composite", "dataset", "run"}) + (assessment,)
        with pytest.raises(ImportRefused, match="assesses-target-kind"):
            other.import_bundle(members, **IMPORT)

    def test_an_assessment_whose_target_resolves_nowhere_is_refused_at_add_and_at_import(self, writer, tmp_path):
        assessment = self._typed_assessment(writer, "a-y", "composite:future")
        with pytest.raises(SignatureRefused, match="assesses-target-unresolvable"):
            writer.add(assessment)
        other = _writer(tmp_path / "other")
        members = tuple(n for n in writer.read_view.iter_stored() if n.kind in {"proposition", "dataset", "run"}) + (assessment,)
        with pytest.raises(ImportRefused, match="assesses-target-unresolvable"):
            other.import_bundle(members, **IMPORT)
        # And a target arriving in the same bundle resolves through the union view. The bundle is rebuilt
        # after `ok` exists, so it carries `run:run-a-z` too — eligibility refuses an assessment whose run
        # is in neither the destination nor the bundle.
        ok = self._typed_assessment(writer, "a-z", "proposition:ab")
        bundle = tuple(n for n in writer.read_view.iter_stored() if n.kind in {"proposition", "dataset", "run"}) + (ok,)
        other.import_bundle(bundle, **IMPORT)
        assert other.read_view.holds("assessment:a-z") and other.read_view.holds("run:run-a-z")

    def test_a_same_kind_supersedes_edge_imports(self, writer, tmp_path):
        first = writer.add(stored.composite_node(_build(writer, ["proposition:ab"], slug="v1"), title="v1"))
        second = writer.supersede(stored.composite_node(_build(writer, ["proposition:ab", "proposition:bc"], slug="v2"), title="v2"), of=first.id)
        other = _writer(tmp_path / "other")
        members = tuple(n for n in writer.read_view.iter_stored() if n.kind in {"proposition", "composite"})
        other.import_bundle(members, **IMPORT)
        assert superseded_by(other.read_view, first.id) == (second.id,)
```

(`ImportRefused.member` is the attribute the existing import path sets via `member=record.id`; confirm the attribute name in `errors.py` and adjust the assertion to it.)

- [ ] **Step 2: Run the tests to verify they fail**

`uv run --frozen pytest tests/test_composite_boundary.py -q` — expected: `FamilyKindUnsupported: supersede operates on propositions only`, admitted cross-kind edges, and admitted malformed composites (the boundary does not yet know the kind).

- [ ] **Step 3: The refusal helpers**

In `python/src/beliefs/corpus.py`, add two methods beside `_refuse_verification` and wire them into `_refuse`:

```python
    def _refuse_composite(self, node: Node, *, view: ReadView | _ImportView) -> None:
        """Design §4.2, steps 1–4, re-derived from the stored record: form,
        the relation set, member resolution and identity, classification.
        No vocabulary membership is read — the boundary holds no snapshot."""
        from beliefs import composite as composite_module

        facet = stored.composite_value(node)  # step 1: form (MalformedRecord)
        if facet.shape not in self._profile.composite_grammar.shapes:
            raise CompositeError("composite-shape", f"{node.id}: {facet.shape!r} is not a shape the base contract declares")
        composes = [relation for relation in node.relations if relation.predicate == stored.COMPOSES]
        if len(composes) != len(facet.members) or any(relation.source != node.id for relation in composes):
            raise CompositeError(
                "composite-relations-mismatch",
                f"{node.id}: the facet names {len(facet.members)} member(s) and the record carries {len(composes)} composes edge(s)",
            )
        refs = tuple(relation.target for relation in composes)
        claims = composite_module.restore_members(
            view, facet.members, refs, profile=self._profile, snapshot=composite_module.EMPTY_SNAPSHOT
        )  # steps 2–3
        composite_module.classify(self._profile, facet, claims)  # step 4

    def _refuse_assesses_target_kind(self, node: Node, *, view: ReadView | _ImportView) -> None:
        """`assesses` targets a proposition and nothing else (kernel §4.1, U4).
        The eligibility predicate reads the run and its observed dataset and
        never the target's kind, so without this an otherwise eligible
        assessment could name a composite and enter the pool `gather` matches."""
        if node.kind != "assessment":
            return
        for relation in node.relations:
            if relation.predicate != stored.ASSESSES:
                continue
            try:
                target = view.get(relation.target)
            except RefError as caught:
                # Not the eligibility predicate's to refuse: it reads the run and
                # its observed datasets and never the target. An edge to a ref
                # that resolves nowhere would let a later `composite:future`
                # establish the forbidden edge by arriving second.
                raise SignatureRefused(
                    f"{node.id}: assesses-target-unresolvable: {relation.target} resolves to no record in this corpus"
                ) from caught
            if target.kind != "proposition":
                raise SignatureRefused(
                    f"{node.id}: assesses-target-kind: an assessment assesses a proposition, not a {target.kind!r} ({relation.target})"
                )

    def _refuse_supersedes_same_kind(self, node: Node, *, view: ReadView | _ImportView) -> None:
        """Design §3.1's `same_kind` rule, on the shared path every route takes
        and outside the `document_validated` shortcut: a `supersedes` edge whose
        target is a record of another kind is a signature violation, whoever
        authored it."""
        rule = self._profile.relations.get(stored.SUPERSEDES)
        if rule is None or not rule.same_kind:
            return
        for relation in node.relations:
            if relation.predicate != stored.SUPERSEDES:
                continue
            try:
                target = view.get(relation.target)
            except RefError:
                continue  # an unresolvable predecessor is the family's refusal (RelocationTargetMissing), not this rule's
            if target.kind != node.kind:
                raise SignatureRefused(
                    f"{node.id}: supersedes-cross-kind: a {node.kind!r} names a {target.kind!r} predecessor "
                    f"({relation.target}); supersedes is same-kind succession (kernel §4.1, composite-claims §3.1)"
                )
```

In `_refuse`, after the `if node.kind == "analysis-spec":` line and **before** `_refuse_governed_stamp`, add:

```python
        reading = self._view if view is None else view
        self._refuse_supersedes_same_kind(node, view=reading)
        self._refuse_assesses_target_kind(node, view=reading)
        if node.kind == "composite":
            self._refuse_composite(node, view=reading)
```

Import `CompositeError` and `SignatureRefused` from `beliefs.errors` at the top of `corpus.py`. All three new refusals run for every record regardless of `document_validated`; `ImportRefused(str(caught), member=record.id)` wraps them through the existing `except ScienceError` in `_validate_import_bundle`. Under the import's union view an assessment and its target may arrive in one bundle: `_ImportView.get` resolves bundle members, so a target in the same bundle resolves and an absent one refuses. Run the whole suite after this step: any existing test that minted an assessment through `add` before its target existed now refuses, and the fix is to mint the target first — the edge was always kernel §4.1's `Assessment ──assesses──▶ Proposition`.

- [ ] **Step 4: `supersede` widened**

In `supersede` (corpus.py:2382), replace the kind check:

```python
            if predecessor.kind != successor.kind or successor.kind not in ("proposition", "composite"):
                raise FamilyKindUnsupported(
                    f"supersede operates on a proposition or a composite and its same-kind successor; "
                    f"found {predecessor.kind!r} → {successor.kind!r}"
                )
```

and change the docstring's first line to "Mint a proposition or composite successor without touching its predecessor." The permit line `self._authority.require("corpus-write", ("proposition",))` becomes `self._authority.require("corpus-write", (successor.kind,))` — the successor's own kind, judged before the lock, which for a proposition is unchanged. Check `test_permit_entry_points.py` for a pin on `supersede`'s required kind and update its expectation to name the successor's kind.

- [ ] **Step 5: Run the tests to verify they pass**

`uv run --frozen pytest tests/test_composite_boundary.py tests/test_corpus_write.py tests/test_permit_entry_points.py tests/test_relocation.py -q` green; then `just test`.

- [ ] **Step 6: Commit**

```bash
git add python/src/beliefs/corpus.py python/tests/test_composite_boundary.py python/tests/test_permit_entry_points.py
git commit -m "feat(corpus): refuse a malformed composite, a cross-kind supersedes edge and a non-proposition assesses target on the shared write path; supersede composites (U3, U4, U6, U9)"
```

---

### Task 5: The audit — `check_composite`, `check_supersedes_kinds`

**Files:**
- Modify: `python/src/beliefs/audit.py` (two functions, the loop, `__all__`)
- Test: `python/tests/test_audit.py`

**Interfaces:**
- Consumes: `composite.restore_members`, `composite.classify`, `composite.EMPTY_SNAPSHOT`, `stored.composite_value` (Task 3).
- Produces: `check_composite(view, node, *, profile) -> DerivationOutcome`; `check_supersedes_kinds(view, node, *, profile) -> Finding | None`; `audit_corpus` reporting `composite-member-unresolvable`, `composite-member-mismatch`, `composite-relations-mismatch`, `composite-malformed` and `supersedes-cross-kind` as contradictions (severity `error`), each record still read by later arms.

- [ ] **Step 1: Write the failing tests**

Append to `python/tests/test_audit.py`:

```python
# --- U7: composites and cross-kind succession under audit -------------------
from test_composite_boundary import A, B, C, SNAPSHOT, _build, _claim, _proposition
from test_composite_boundary import _writer as _composite_writer

from beliefs.audit import check_composite, check_supersedes_kinds
from beliefs.composite import CompositeNode


def _composite_corpus(tmp_path):
    w = _composite_writer(tmp_path / "corpus")
    _proposition(w, "ab", _claim("EX:a", "EX:b"))
    _proposition(w, "bc", _claim("EX:b", "EX:c", polarity="negative"))
    minted = w.add(stored.composite_node(_build(w, ["proposition:ab", "proposition:bc"]), title="g"))
    return w, minted


def _codes(writer):
    return sorted((f.code, f.ref) for f in audit_corpus(reopen(writer.root), evidence=NO_EVIDENCE, profile=writer.profile))


def test_a_well_formed_composite_audits_clean(tmp_path):
    writer, _ = _composite_corpus(tmp_path)
    assert _codes(writer) == []


def test_a_deleted_member_is_an_unresolvable_contradiction_and_the_record_stays_read(tmp_path):
    writer, minted = _composite_corpus(tmp_path)
    writer.delete("proposition:bc")
    codes = _codes(writer)
    assert ("composite-member-unresolvable", minted.id) in codes
    assert not any(code in audit.MALFORMEDNESS_CODES for code, _ in codes)


def test_a_raw_edited_member_claim_is_a_mismatch(tmp_path):
    writer, minted = _composite_corpus(tmp_path)
    node = writer.read_view.get("proposition:bc")
    node.facets[stored.PROPOSITION_FACET]["polarity"] = "positive"
    stored.stamp_semantic_identity(node)
    raw_write(writer.root, node)
    assert ("composite-member-mismatch", minted.id) in _codes(writer)


def test_a_relation_set_that_disagrees_with_the_facet_is_reported(tmp_path):
    writer, minted = _composite_corpus(tmp_path)
    node = writer.read_view.get(minted.id)
    node.relations.pop()
    raw_write(writer.root, node)  # the stamp covers the facet, not the relations, so the record is well formed
    assert ("composite-relations-mismatch", minted.id) in _codes(writer)


def test_a_composite_that_no_longer_classifies_is_malformed_not_silently_kept(tmp_path):
    writer, minted = _composite_corpus(tmp_path)
    node = writer.read_view.get(minted.id)
    node.facets[stored.COMPOSITE_FACET]["nodes"] = [{"sort": "biology/gene", "term": "EX:a"}, {"sort": "biology/gene", "term": "EX:b"}]  # drops c
    stored.stamp_semantic_identity(node)
    raw_write(writer.root, node)
    findings = {f.code: f for f in audit_corpus(reopen(writer.root), evidence=NO_EVIDENCE, profile=writer.profile)}
    assert "composite-malformed" in findings and "composite-member-outside-nodes" in findings["composite-malformed"].detail


def test_a_raw_written_cross_kind_supersedes_edge_is_reported_on_any_record(tmp_path):
    writer, minted = _composite_corpus(tmp_path)
    node = writer.read_view.get("proposition:ab")
    node.relations.append(Relation(source=node.id, predicate=stored.SUPERSEDES, target=minted.id))
    raw_write(writer.root, node)
    assert ("supersedes-cross-kind", "proposition:ab") in _codes(writer)
    assert check_supersedes_kinds(reopen(writer.root), reopen(writer.root).get("proposition:ab"), profile=writer.profile) is not None


def test_a_successor_that_retires_the_edge_row_makes_the_composite_malformed(tmp_path):
    import copy

    from beliefs.contract import parse_domain_contract
    from beliefs.contract.document import load_document
    from beliefs.profile import compile_profile, shipped_base_contract
    from profiles import FIXTURE, biology

    writer, minted = _composite_corpus(tmp_path)
    document = load_document(FIXTURE, source=str(FIXTURE))
    successor = copy.deepcopy(document)
    successor["description"] = "fixture"
    successor["lineage"] = {"successor": biology("fixture").content_identity}
    successor["edges"]["affects"]["retired"] = True
    retired = compile_profile(shipped_base_contract(), [parse_domain_contract(successor, source="<r>", base=shipped_base_contract(), predecessor=biology("fixture"))])
    # `check_composite` directly: the corpus pins the predecessor, and this arm is about classification under the successor, not about pins.
    outcome = check_composite(reopen(writer.root), reopen(writer.root).get(minted.id), profile=retired)
    assert outcome.contradiction is not None and outcome.contradiction.code == "composite-malformed"
    assert "composite-member-retired" in outcome.contradiction.detail


def test_check_composite_reads_form_only_and_never_a_snapshot(tmp_path):
    writer, minted = _composite_corpus(tmp_path)
    outcome = check_composite(reopen(writer.root), reopen(writer.root).get(minted.id), profile=writer.profile)
    assert outcome.checked and outcome.contradiction is None
```

(`Relation` is already imported in `test_audit.py`'s header via `nodes.core.relations`; add it if not.)

- [ ] **Step 2: Run the tests to verify they fail**

`uv run --frozen pytest tests/test_audit.py -k "composite or cross_kind" -q` — expected: `ImportError` on `check_composite`.

- [ ] **Step 3: The arms**

In `python/src/beliefs/audit.py`:

```python
def check_composite(view: ReadView | _ImportView | WorldReadView, node: Node, *, profile: ProfileSpec) -> DerivationOutcome:
    """Design §4.3: the boundary's four steps over the stored record, reported
    rather than raised. Form only — the audit holds no snapshot."""
    from beliefs import composite as composite_module
    from beliefs.errors import CompositeError

    def contradiction(code: str, detail: str) -> DerivationOutcome:
        return DerivationOutcome(
            checked=True,
            reason="",
            contradiction=Finding(severity="error", code=code, ref=node.id, detail=detail, message=f"{node.id}: {detail}"),
        )

    facet = stored.composite_value(node)  # MalformedRecord → derivation-malformed, by the loop's catch
    composes = [r for r in node.relations if r.predicate == stored.COMPOSES]
    if len(composes) != len(facet.members) or any(r.source != node.id for r in composes):
        return contradiction("composite-relations-mismatch", f"facet names {len(facet.members)} member(s), record carries {len(composes)} composes edge(s)")
    try:
        claims = composite_module.restore_members(
            view, facet.members, tuple(r.target for r in composes), profile=profile, snapshot=composite_module.EMPTY_SNAPSHOT
        )
        composite_module.classify(profile, facet, claims)
    except CompositeError as refused:
        if refused.code in ("composite-member-unresolvable", "composite-member-mismatch"):
            return contradiction(refused.code, str(refused))
        return contradiction("composite-malformed", str(refused))
    return DerivationOutcome(checked=True, reason="", contradiction=None)


def check_supersedes_kinds(view: ReadView | _ImportView | WorldReadView, node: Node, *, profile: ProfileSpec) -> Finding | None:
    """Design §3.1's `same_kind` rule, under audit: a raw-written edge the
    shared path would have refused."""
    from nodes.core.errors import RefError

    rule = profile.relations.get(stored.SUPERSEDES)
    if rule is None or not rule.same_kind:
        return None
    for relation in node.relations:
        if relation.predicate != stored.SUPERSEDES:
            continue
        try:
            target = view.get(relation.target)
        except RefError:
            continue  # resolution is the supersession arm's finding, not this one's
        if target.kind != node.kind:
            detail = f"a {node.kind!r} names a {target.kind!r} predecessor ({relation.target})"
            return Finding(severity="error", code="supersedes-cross-kind", ref=node.id, detail=detail, message=f"{node.id}: {detail}")
    return None
```

In `audit_corpus`'s loop, before the `try:` block's kind dispatch, add:

```python
        cross = check_supersedes_kinds(view, node, profile=profile)
        if cross is not None:
            findings.append(cross)
```

and add the arm `elif node.kind == "composite": outcome = check_composite(view, node, profile=profile)` after the `analysis-spec` arm. Add both names to `__all__`.

- [ ] **Step 4: Run the tests to verify they pass**

`uv run --frozen pytest tests/test_audit.py -q` green; `uv run --frozen pyright` clean.

- [ ] **Step 5: Commit**

```bash
git add python/src/beliefs/audit.py python/tests/test_audit.py
git commit -m "feat(audit): report a dangling, mismatched or unclassifiable composite and a cross-kind supersedes edge (U7, U9)"
```

---

### Task 6: The reading — the traced evaluator and `read_composite`

**Files:**
- Modify: `python/src/beliefs/belief.py` (`Admission`, `admitted`, `evaluate_traced`; `evaluate` as first projection), `python/src/beliefs/evaluation.py` (`evaluate_over_traced`; `evaluate_over` as first projection), `python/src/beliefs/composite.py` (`Resolution`, `MemberRow`, `CompositeReading`, `read_composite`)
- Test: `python/tests/test_belief.py`, `python/tests/test_evaluation.py`, `python/tests/test_composite_reading.py`

**Interfaces:**
- Consumes: `evaluation.gather`, `belief.evaluate`, `admission.admit`, `verification.lifecycle_state`, `corpus.superseded_by` (existing); the estimand lane's `AssessmentValue.estimand: Estimand` with `estimand.control.identification: Referent` (estimand plan Task 7); Task 4's `_estimand` helper and `SNAPSHOT` (typed under the biology fixture's `estimands:` row from Task 2).
- Produces, at `beliefs.belief`: `NotReached` and `Reached(admitted: frozenset[str])` (sealed, frozen; `Admission = NotReached | Reached`); `admitted(distinct, *, runs, observations, verifications) -> tuple[tuple[AssessmentValue, ...], tuple[AssessmentValue, ...]]` (eligible, unheld-only — step 5's partition, called exactly once by the evaluator); `evaluate_traced(**same kwargs as evaluate) -> tuple[Belief | NoBelief | Refused, Admission]`; `evaluate(...)` unchanged in signature and answer, defined as `evaluate_traced(...)[0]`. At `beliefs.evaluation`: `evaluate_over_traced(view, proposition, *, availability, context, profile, resolution, binding) -> tuple[answer, Admission]`; `evaluate_over(...) = evaluate_over_traced(...)[0]`. At `beliefs.composite`: `Resolution(state: str, successors: tuple[str, ...])` with `state ∈ {"active", "superseded"}`; `MemberRow(member, ref, role: Edge, claim: Claim, resolution: Resolution, belief, identification: tuple[str, ...] | NotReached)`; `CompositeReading(ref, identity, shape, nodes: tuple[CompositeNode, ...], standing: Resolution, node_outcomes: Mapping[str, TermOutcome], rows: tuple[MemberRow, ...])` with `projection() -> dict` (canonically encodable; the evaluator answer projected as `answers.payload` in the reproduction driver does — `{"kind": "Belief", "value", "belief_input_digest", "policy_binding"}` and its two siblings); `read_composite(view, ref, *, context, availability, resolution, binding, profile) -> CompositeReading`.

- [ ] **Step 1: Write the failing tests**

Append to `python/tests/test_belief.py`:

```python
# --- the traced evaluator (composite-claims design §6.2) ---------------------
from beliefs.belief import NotReached, Reached, evaluate_traced


def test_evaluate_is_the_first_projection_of_evaluate_traced():
    for overrides in ({}, {"binding": None}, {"availability": scenario()["availability"].__class__(observations={}, implementations={}, fixtures={})}):
        kwargs = scenario(**overrides)
        answer, _ = evaluate_traced(**kwargs)
        assert evaluate(**kwargs) == answer


def test_admission_is_reached_with_identities_on_a_belief_and_on_a_directionless_no_belief():
    answer, admission = evaluate_traced(**scenario())
    assert isinstance(answer, Belief) and isinstance(admission, Reached)
    assert admission.admitted == {a.identity() for a in scenario()["records"].assessments}
    answer, admission = evaluate_traced(**scenario(records=_fifty_inconclusive_records()))
    assert answer == NoBelief("no-directional-outcome")
    assert isinstance(admission, Reached) and len(admission.admitted) == 50


def test_admission_is_not_reached_when_the_answer_precedes_the_gate():
    unheld = scenario()["availability"]
    without_policy = Availability(observations=unheld.observations, implementations={}, fixtures=unheld.fixtures)
    answer, admission = evaluate_traced(**scenario(availability=without_policy))
    assert answer == NoBelief("unavailable-policy-unheld") and admission == NotReached()
    answer, admission = evaluate_traced(**scenario(binding=None))
    assert isinstance(answer, Refused) and admission == NotReached()
    # The identity-contradiction arm sits inside step 5, before the gate, and keeps its existing answer.
    base = scenario()
    twin = _assessment("spec-a", "run-a", outcome="refuted")  # same (spec, run, proposition) as a1, different facet
    records = Records(claims=base["records"].claims, assessments=(*base["records"].assessments, twin), runs=base["records"].runs, source_assertions=(), verifications=base["records"].verifications)
    answer, admission = evaluate_traced(**scenario(records=records))
    assert isinstance(answer, Refused) and answer.reason.startswith("assessment-identity-contradicted") and admission == NotReached()
    assert evaluate(**scenario(records=records)) == answer


def test_the_admitted_set_is_not_the_digest_keyed_set():
    kwargs = scenario()
    a1, a2 = kwargs["records"].assessments
    held_only_a = Availability(observations=_held(DATASET_A), implementations=kwargs["availability"].implementations, fixtures=kwargs["availability"].fixtures)
    answer, admission = evaluate_traced(**scenario(availability=held_only_a))
    assert isinstance(admission, Reached) and admission.admitted == {a1.identity()}
    assert {a.identity() for a in kwargs["records"].assessments} == {a1.identity(), a2.identity()}  # the closure keys both


def test_admission_runs_exactly_once_in_the_evaluator(monkeypatch):
    from beliefs import belief as belief_module

    original = belief_module.admitted
    calls = []

    def trap(*args, **kwargs):
        calls.append(1)
        if len(calls) > 1:
            raise AssertionError("belief.admitted was called a second time")
        return original(*args, **kwargs)

    monkeypatch.setattr(belief_module, "admitted", trap)
    evaluate_traced(**scenario())
    assert calls == [1]
```

(`NotReached` is a frozen dataclass with no fields: equal by value, never compared by identity.) Append to `python/tests/test_evaluation.py`:

```python
def test_evaluate_over_is_the_first_projection_of_evaluate_over_traced(corpus_fixture, claimless_fixture):
    from beliefs.belief import Reached
    from beliefs.evaluation import evaluate_over_traced

    for fixture in (corpus_fixture, claimless_fixture):
        answer, admission = evaluate_over_traced(fixture.view, fixture.proposition, **fixture.kwargs)
        assert evaluate_over(fixture.view, fixture.proposition, **fixture.kwargs) == answer
        if isinstance(answer, Belief):
            assert isinstance(admission, Reached) and admission.admitted == {a.identity() for a in fixture.assessments}
```

Create `python/tests/test_composite_reading.py`:

```python
"""`read_composite` (design §6, U8): rows equal the wrapper's answers; the node receipt sits on the reading."""

from __future__ import annotations

import pytest
from profiles import pins_for
from test_composite_boundary import GENE, SNAPSHOT, A, _build, _claim, _estimand, _proposition, _writer
from test_evaluation import _observations  # the held byte observations helper, keyed by dataset address

from beliefs import stored
from beliefs.belief import Availability, Belief, NoBelief, NotReached, SuppliedContext
from beliefs.closure import RetractionEnumeration
from beliefs.composite import CompositeNode, CompositeError, build_composite, read_composite
from beliefs.corpus import lineage_snapshot
from beliefs.evaluation import evaluate_over
from beliefs.identity import v1
from beliefs.policy import BELIEF_V1, BELIEF_V1_FIXTURES, BELIEF_V1_RULE, PolicyBinding
from beliefs.projection import project_claim
from beliefs.resolution import TermOutcome, build_snapshot

BINDING = PolicyBinding(rule=BELIEF_V1_RULE, implementation=BELIEF_V1.identity)


@pytest.fixture()
def corpus(tmp_path):
    """Three propositions over an acyclic graph a→b, b⊣c, a→c: `ab` assessed once
    (supported, verified, held), `bc` unassessed, `ac` (unsigned) superseded by `ac2` (positive)."""
    w = _writer(tmp_path / "corpus")
    ab = _proposition(w, "ab", _claim("EX:a", "EX:b"))
    _proposition(w, "bc", _claim("EX:b", "EX:c", polarity="negative"))
    ac = _proposition(w, "ac", _claim("EX:a", "EX:c", polarity="unsigned"))
    ac2 = w.supersede(stored.proposition_node("ac2", title="ac2", claim=project_claim(_claim("EX:a", "EX:c"))), of=ac.id)
    # One admitted assessment of `ab`: an observing run over a held dataset, a passed clean-environment verification,
    # typed under the profile that restores it (Step 4).
    from test_evaluation import seed_assessed_proposition

    dataset_address = seed_assessed_proposition(w, ab.id, slug="a-ab", estimand=_estimand(_claim("EX:a", "EX:b")), applicability={})
    return w, dataset_address, ac.id, ac2.id


def _inputs(w, dataset_address, *, hold=True, with_policy=True):
    view = w.read_view
    context = SuppliedContext(
        snapshot=lineage_snapshot(view, (dataset_address,)),
        producer_snapshot_identity="producer-snapshot-1",
        retractions=RetractionEnumeration(found=(), coverage=("c1",)),
        node_corpus={},
        pins={"c1": pins_for(w.profile)},
    )
    availability = Availability(
        observations=_observations("a") if hold else {},
        implementations={BELIEF_V1.identity: BELIEF_V1} if with_policy else {},
        fixtures={BELIEF_V1_RULE: BELIEF_V1_FIXTURES},
    )
    return {"context": context, "availability": availability, "resolution": SNAPSHOT, "binding": BINDING, "profile": w.profile}


def test_rows_equal_the_wrapper_answers_and_columns_share_one_admission(corpus):
    w, dataset_address, ac, ac2 = corpus
    minted = w.add(stored.composite_node(_build(w, ["proposition:ab", "proposition:bc", ac]), title="g"))
    reading = read_composite(w.read_view, minted.id, **_inputs(w, dataset_address))
    assert reading.identity == stored.stored_semantic_hash(w.read_view.get(minted.id))
    by_ref = {row.ref: row for row in reading.rows}
    for ref, row in by_ref.items():
        assert row.belief == evaluate_over(w.read_view, ref, **_inputs(w, dataset_address))
    assert isinstance(by_ref["proposition:ab"].belief, Belief) and by_ref["proposition:ab"].identification == ("EX:observational",)
    assert by_ref["proposition:bc"].belief == NoBelief("no-eligible-assessment") and by_ref["proposition:bc"].identification == ()
    assert by_ref[ac].resolution.state == "superseded" and by_ref[ac].resolution.successors == (ac2,)
    assert {row.role.sign for row in reading.rows} == {"positive", "negative", "unsigned"}
    assert set(reading.node_outcomes) == {"node:0", "node:1", "node:2"} and reading.standing.state == "active"


def test_withholding_follows_the_evaluator(corpus):
    w, dataset_address, _, _ = corpus
    minted = w.add(stored.composite_node(_build(w, ["proposition:ab"]), title="g"))
    unheld = read_composite(w.read_view, minted.id, **_inputs(w, dataset_address, hold=False)).rows[0]
    assert unheld.belief == evaluate_over(w.read_view, "proposition:ab", **_inputs(w, dataset_address, hold=False))
    assert isinstance(unheld.belief, NoBelief) and unheld.identification == ()
    no_policy = read_composite(w.read_view, minted.id, **_inputs(w, dataset_address, with_policy=False)).rows[0]
    assert no_policy.belief == NoBelief("unavailable-policy-unheld") and no_policy.identification == NotReached()


def test_two_inconclusive_admitted_assessments_keep_their_terms(corpus):
    w, dataset_address, *_ = corpus
    from test_evaluation import seed_assessed_proposition

    bc = _estimand(_claim("EX:b", "EX:c", polarity="negative"))
    seed_assessed_proposition(w, "proposition:bc", slug="i-1", outcome="inconclusive", estimand=bc, applicability={})
    seed_assessed_proposition(w, "proposition:bc", slug="i-2", outcome="inconclusive", estimand=bc, applicability={})
    minted = w.add(stored.composite_node(_build(w, ["proposition:bc"]), title="g"))
    row = read_composite(w.read_view, minted.id, **_inputs(w, dataset_address)).rows[0]
    assert row.belief == NoBelief("no-directional-outcome")
    assert row.identification == ("EX:observational",)


def test_the_reading_admits_each_member_once_and_never_calls_admit_itself(corpus, monkeypatch):
    """Two traps, because the two declared mutations differ: a second
    `belief.admitted` call over the gathered records, and a direct
    `admission.admit` call per gathered assessment. `admit` is counted through
    the module `belief.admitted` resolves it from, so a `read_composite` that
    imported it itself would still be counted — `admit` has one home."""
    from beliefs import admission as admission_module
    from beliefs import belief as belief_module

    admitted_calls, admit_calls = [], []
    original_admitted, original_admit = belief_module.admitted, belief_module.admit

    def trap_admitted(*args, **kwargs):
        admitted_calls.append(1)
        return original_admitted(*args, **kwargs)

    def trap_admit(*args, **kwargs):
        admit_calls.append(1)
        return original_admit(*args, **kwargs)

    monkeypatch.setattr(belief_module, "admitted", trap_admitted)
    monkeypatch.setattr(belief_module, "admit", trap_admit)
    monkeypatch.setattr(admission_module, "admit", trap_admit)
    w, dataset_address, *_ = corpus
    minted = w.add(stored.composite_node(_build(w, ["proposition:ab", "proposition:bc"]), title="g"))
    read_composite(w.read_view, minted.id, **_inputs(w, dataset_address))
    assert admitted_calls == [1, 1]  # one per member, from the evaluator
    assert admit_calls == [1]  # `ab` has one distinct assessment; `bc` has none — nothing outside the evaluator called it


def test_an_unresolvable_member_refuses_the_reading(corpus):
    w, dataset_address, *_ = corpus
    minted = w.add(stored.composite_node(_build(w, ["proposition:ab", "proposition:bc"]), title="g"))
    w.delete("proposition:bc")
    with pytest.raises(CompositeError) as caught:
        read_composite(w.read_view, minted.id, **_inputs(w, dataset_address))
    assert caught.value.code == "composite-member-unresolvable"


def test_a_memberless_composite_reads_no_rows_and_a_node_receipt(corpus):
    w, dataset_address, *_ = corpus
    value, _ = build_composite(w.profile, w.read_view, shape="dag", nodes=[A, CompositeNode(GENE, "EX:z")], members=[], snapshot=build_snapshot(), slug="m")
    minted = w.add(stored.composite_node(value, title="m"))
    unconsulted = {**_inputs(w, dataset_address), "resolution": build_snapshot()}
    reading = read_composite(w.read_view, minted.id, **unconsulted)
    assert reading.rows == ()
    assert reading.node_outcomes == {"node:0": TermOutcome.NOT_CONSULTED, "node:1": TermOutcome.NOT_CONSULTED}
    assert v1.encode(reading.projection())  # canonically encodable


def test_the_reading_refuses_a_node_the_consulted_vocabulary_excludes(corpus):
    w, dataset_address, *_ = corpus
    value, _ = build_composite(w.profile, w.read_view, shape="dag", nodes=[A, CompositeNode(GENE, "EX:z")], members=[], snapshot=build_snapshot(), slug="m")
    minted = w.add(stored.composite_node(value, title="m"))
    with pytest.raises(CompositeError) as caught:
        read_composite(w.read_view, minted.id, **_inputs(w, dataset_address))  # SNAPSHOT consults EX and lacks z
    assert caught.value.code == "composite-node-not-member" and "node:1" in str(caught.value)


def test_a_superseded_composite_reports_its_successor(corpus):
    w, dataset_address, *_ = corpus
    first = w.add(stored.composite_node(_build(w, ["proposition:ab"], slug="v1"), title="v1"))
    second = w.supersede(stored.composite_node(_build(w, ["proposition:ab", "proposition:bc"], slug="v2"), title="v2"), of=first.id)
    reading = read_composite(w.read_view, first.id, **_inputs(w, dataset_address))
    assert reading.standing.state == "superseded" and reading.standing.successors == (second.id,)
```

The memberless receipt is exercised under an unconsulted snapshot; under the consulting `SNAPSHOT`, which lacks `EX:z`, the reading refuses exactly as the constructor does (U3's vocabulary arm). Only the boundary and the audit check form alone.

- [ ] **Step 2: Run the tests to verify they fail**

`uv run --frozen pytest tests/test_belief.py tests/test_evaluation.py tests/test_composite_reading.py -q` — expected: `ImportError` on `evaluate_traced`, `evaluate_over_traced`, `read_composite`, `seed_assessed_proposition`.

- [ ] **Step 3: Factor the evaluator**

In `python/src/beliefs/belief.py`, add after `Refused`:

```python
@sealed
@final
@dataclass(frozen=True)
class NotReached:
    """The answer was given before step 5: admission never ran, and no set —
    not even the empty one — describes what it would have found."""


@sealed
@final
@dataclass(frozen=True)
class Reached:
    """Step 5 ran; `admitted` is what it admitted, possibly nothing."""

    admitted: frozenset[str]


Admission = NotReached | Reached


def admitted(
    distinct: Sequence[AssessmentValue],
    *,
    runs: Mapping[str, RunValue],
    observations: Mapping[str, tuple[ByteObservation, ...]],
    verifications: tuple[Verification, ...],
) -> tuple[tuple[AssessmentValue, ...], tuple[AssessmentValue, ...]]:
    """Step 5's gate, once: `(eligible, unheld_only)` over the identity-collapsed pool."""
    eligible: list[AssessmentValue] = []
    unheld_only: list[AssessmentValue] = []
    for a in distinct:
        admission = admit(a, runs[a.run], observations, verifications)
        if isinstance(admission, Admitted):
            eligible.append(a)
        elif isinstance(admission, AdmissionRefused) and admission.reason.startswith("input-not-held"):
            own_verifications = tuple(v for v in verifications if v.assessment == a.identity())
            if lifecycle_state(own_verifications) == ADMITTED:
                unheld_only.append(a)
    return tuple(eligible), tuple(unheld_only)
```

Rename the existing `evaluate` to `evaluate_traced` with return type `tuple[Belief | NoBelief | Refused, Admission]`; every `return X` before the `admitted` call becomes `return X, NotReached()` — that is the four steps 1–4 arms **and** the `assessment-identity-contradicted` `Refused` inside step 5's identity-collapse loop, which precedes the gate (a `return` left bare there makes the first-projection wrapper index a `Refused`, `TypeError`); the admission loop that follows the collapse is replaced by

```python
    eligible, unheld_only = admitted(distinct, runs=records.runs, observations=availability.observations, verifications=records.verifications)
    reached = Reached(frozenset(a.identity() for a in eligible))
```

(one plain module-level call, which resolves through the module globals at call time, so `monkeypatch.setattr(belief_module, "admitted", trap)` is seen). Every `return` from step 6 onward becomes `return X, reached`. Then add:

```python
def evaluate(
    *,
    proposition: str,
    records: Records,
    availability: Availability,
    context: SuppliedContext,
    binding: object,
    profile: ProfileSpec,
) -> Belief | NoBelief | Refused:
    """Belief-policy §4's evaluation order, exactly, top to bottom — the first
    projection of `evaluate_traced`, so the answer cannot differ from it."""
    return evaluate_traced(
        proposition=proposition, records=records, availability=availability, context=context, binding=binding, profile=profile
    )[0]
```

Add `NotReached`, `Reached`, `admitted`, `evaluate_traced` to `__all__`. `ByteObservation` is imported from `beliefs.dataset`; `Sequence` from `collections.abc`.

In `python/src/beliefs/evaluation.py`, rename `evaluate_over` to `evaluate_over_traced` returning `tuple[Belief | NoBelief | Refused, Admission]`: the binding guard returns `(Refused(...), NotReached())`, each gather-exception arm returns `(Refused(...), NotReached())`, the absent-corpus arm `(NoBelief("unavailable-corpus-absent", detail=...), NotReached())`, and the final call becomes `return evaluate_traced(...)`. Then:

```python
def evaluate_over(
    view: ReadView | WorldReadView,
    proposition: str,
    *,
    availability: Availability,
    context: SuppliedContext,
    profile: ProfileSpec,
    resolution: ResolutionSnapshot,
    binding: object,
) -> Belief | NoBelief | Refused:
    """`evaluate`'s step-1 guard first, then `gather`, then `evaluate` — the
    first projection of `evaluate_over_traced`."""
    return evaluate_over_traced(
        view, proposition, availability=availability, context=context, profile=profile, resolution=resolution, binding=binding
    )[0]
```

Import `Admission`, `NotReached`, `evaluate_traced` from `beliefs.belief`; add `evaluate_over_traced` to `__all__`.

- [ ] **Step 4: The seeding helper**

In `python/tests/test_evaluation.py`, beside `_seed`, add a helper the reading tests share:

```python
def seed_assessed_proposition(writer, proposition_ref: str, *, slug: str, outcome: str = "supported", **typed) -> str:
    """Mint one admissible assessment of `proposition_ref` through the writer:
    dataset `d-a` (address `_address("a")`, resources `_resources("a")`), an
    observing run, the assessment, and a passed clean-environment
    verification. Returns the dataset address. `typed` carries the estimand
    lane's `estimand=` and `applicability=` values."""
    address = _address("a")
    if not writer.read_view.holds("dataset:d-a"):
        writer.add(stored.dataset_node("d-a", title="d-a", resources=_resources("a"), empirical_observation=EMPIRICAL))
    run = writer.add(stored.run_node(f"run-{slug}", title=slug, spec=f"spec-{slug}", observes=["dataset:d-a"]))
    assessment = writer.add(stored.assessment_node(slug, title=slug, spec=f"spec-{slug}", run=run.id, proposition=proposition_ref, outcome=outcome, interpretation_rule="rule-1", **typed))
    value = stored.assessment_value(writer.read_view.get(assessment.id), profile=writer.profile)
    writer.add(stored.verification_node(f"v-{slug}", title=slug, assessment=value.identity(), assessment_ref=assessment.id, scope="clean-environment", verdict="passed"))
    return address
```

`EMPIRICAL` is whatever `_seed` already passes as the dataset's `empirical-observation` facet (read `_seed`'s dataset node construction and reuse its exact keyword and value; the writer's boundary requires `attested_by` to equal the writer's actor, `authority.ACTOR`). `stored.run_node`'s keyword for an observing input is whatever `_seed` uses (`observes=`); copy it.

- [ ] **Step 5: The reading**

Append to `python/src/beliefs/composite.py`:

```python
@sealed
@final
@dataclass(frozen=True)
class Resolution:
    state: str
    successors: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.state not in ("active", "superseded"):
            raise MalformedRecord(f"resolution state {self.state!r} is not active or superseded")

    def projection(self) -> dict[str, object]:
        return {"state": self.state, "successors": list(self.successors)}


@sealed
@final
@dataclass(frozen=True)
class MemberRow:
    member: str
    ref: str
    role: Edge
    claim: Claim
    resolution: Resolution
    belief: Belief | NoBelief | Refused
    identification: tuple[str, ...] | NotReached

    def projection(self) -> dict[str, object]:
        return {
            "member": self.member,
            "ref": self.ref,
            "role": {"cause": self.role.cause.projection(), "effect": self.role.effect.projection(), "sign": self.role.sign},
            "claim": project_claim(self.claim),
            "resolution": self.resolution.projection(),
            "belief": _answer_projection(self.belief),
            "identification": "not-reached" if isinstance(self.identification, NotReached) else list(self.identification),
        }


@sealed
@final
@dataclass(frozen=True)
class CompositeReading:
    ref: str
    identity: str
    shape: str
    nodes: tuple[CompositeNode, ...]
    standing: Resolution
    node_outcomes: Mapping[str, TermOutcome]
    rows: tuple[MemberRow, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "node_outcomes", MappingProxyType(dict(self.node_outcomes)))

    def projection(self) -> dict[str, object]:
        return {
            "ref": self.ref,
            "identity": self.identity,
            "shape": self.shape,
            "nodes": [n.projection() for n in self.nodes],
            "standing": self.standing.projection(),
            "node_outcomes": {label: outcome.value for label, outcome in self.node_outcomes.items()},
            "rows": [row.projection() for row in self.rows],
        }


def _answer_projection(answer: Belief | NoBelief | Refused) -> dict[str, object]:
    if isinstance(answer, Belief):
        return {"kind": "Belief", "value": answer.value, "belief_input_digest": answer.belief_input_digest, "policy_binding": [answer.policy_binding.rule, answer.policy_binding.implementation]}
    if isinstance(answer, NoBelief):
        return {"kind": "NoBelief", "reason": answer.reason, "detail": answer.detail}
    return {"kind": "Refused", "reason": answer.reason}


def _resolution(view: object, ref: str) -> Resolution:
    successors = superseded_by(view, ref)  # type: ignore[arg-type]
    return Resolution("superseded", successors) if successors else Resolution("active", ())


def read_composite(
    view: object,
    ref: str,
    *,
    context: SuppliedContext,
    availability: Availability,
    resolution: ResolutionSnapshot,
    binding: PolicyBinding,
    profile: ProfileSpec,
) -> CompositeReading:
    """Design §6: a pure function of exactly these arguments. Each row's
    belief is `evaluate_over_traced`'s answer for the member, and the
    identification column is read from the same traced admission."""
    if not isinstance(resolution, ResolutionSnapshot):
        raise CompositeError("composite-snapshot", "read_composite takes a ResolutionSnapshot; availability is a parameter, never ambient")
    node = view.get(ref)  # type: ignore[attr-defined]
    if node.kind != "composite":
        raise CompositeError("composite-kind", f"{ref} is a {node.kind!r}, not a composite")
    facet = stored_composite_value(node)
    composes = [r for r in node.relations if r.predicate == COMPOSES]
    if len(composes) != len(facet.members):
        raise CompositeError("composite-relations-mismatch", f"{ref}: the facet and the relation set disagree")
    refs = tuple(r.target for r in composes)
    claims = restore_members(view, facet.members, refs, profile=profile, snapshot=resolution)
    edges = {edge.member: edge for edge in classify(profile, facet, claims)}

    outcomes: dict[str, TermOutcome] = {}
    for index, n in enumerate(facet.nodes):
        outcomes[ReferentPosition.node(index).label()] = resolution.resolve(profile.sorts[n.sort].vocabulary, n.term)
    refused = [label for label, outcome in outcomes.items() if outcome.refuses]
    if refused:
        # U3: construction and reading refuse alike under an excluding snapshot;
        # only the boundary and the audit, which hold no snapshot, check form alone.
        raise CompositeError("composite-node-not-member", f"{ref}: {', '.join(refused)}: the term is not in the vocabulary its sort binds, and the vocabulary was read")

    rows: list[MemberRow] = []
    for member, member_ref in zip(facet.members, refs, strict=True):
        answer, admission = evaluate_over_traced(
            view, member_ref, availability=availability, context=context, profile=profile, resolution=resolution, binding=binding
        )
        if isinstance(admission, NotReached):
            identification: tuple[str, ...] | NotReached = admission
        else:
            terms = set()
            for stored_node in view.iter_stored():  # type: ignore[attr-defined]
                if stored_node.kind != "assessment":
                    continue
                value = assessment_value(stored_node, profile=profile)
                if value.identity() in admission.admitted:
                    terms.add(value.estimand.control.identification.term)
            identification = tuple(sorted(terms))
        rows.append(
            MemberRow(
                member=member,
                ref=member_ref,
                role=edges[member],
                claim=claims[member],
                resolution=_resolution(view, member_ref),
                belief=answer,
                identification=identification,
            )
        )
    return CompositeReading(
        ref=ref,
        identity=composite_identity(facet),
        shape=facet.shape,
        nodes=facet.nodes,
        standing=_resolution(view, ref),
        node_outcomes=outcomes,
        rows=tuple(rows),
    )
```

with these imports added at the top of `composite.py` (`corpus` and `evaluation` import `stored` and `decode`, not `composite`, so no cycle): `from beliefs.belief import Availability, Belief, NoBelief, NotReached, Refused, SuppliedContext`, `from beliefs.corpus import superseded_by`, `from beliefs.evaluation import evaluate_over_traced`, `from beliefs.policy import PolicyBinding`, `from beliefs.projection import project_claim`, `from beliefs.stored import COMPOSES, assessment_value, composite_value as stored_composite_value`. If importing `beliefs.corpus` at module load creates a cycle through `stored` (Task 3 made `stored.composite_value` import `composite` lazily, so it should not), move the `corpus`/`evaluation` imports inside `read_composite`.

`restore_members` refuses `not-member` on a member's own referents under the reading's snapshot with `composite-member-unrestorable` — that is the rule the spec's §6.3 names for a member that cannot be classified; a node's outcome, by contrast, is reported and never refuses here.

- [ ] **Step 6: Run the tests to verify they pass**

`uv run --frozen pytest tests/test_belief.py tests/test_evaluation.py tests/test_composite_reading.py tests/test_closure.py -q` green; then `just test` (P1–P9 through `test_belief.py` and the acceptance suite unchanged).

- [ ] **Step 7: Commit**

```bash
git add python/src/beliefs/belief.py python/src/beliefs/evaluation.py python/src/beliefs/composite.py python/tests/test_belief.py python/tests/test_evaluation.py python/tests/test_composite_reading.py
git commit -m "feat(composite): read a composite through the traced evaluator, one admission per member (U8)"
```

---
### Task 7: The reproduction — successor contracts with `edges:`, the composed spine, the reading in a fresh process

**Files:**
- Modify: `python/tools/reproduction/mm30.yaml` (`edges:`, `lineage: {successor: <the estimand lane's mm30 identity>}`, `version` + 1), `domains/biology/DOMAIN.yaml` (`edges:`, `lineage: {successor: <the estimand lane's biology identity>}`, `version` + 1) and its copy under `python/src/beliefs/domains/biology/DOMAIN.yaml` if the package ships one (`ls python/src/beliefs/domains`)
- Create: `python/tools/reproduction/compose.py` (step 11), `python/tools/reproduction/read.py` (step 12)
- Modify: `python/tools/reproduction/state.py` (no code change; new keys documented in its docstring), `docs/designs/2026-09-05-mm30-reproduction.md` (a dated addendum, §11), `docs/superpowers/specs/2026-09-05-mm30-reproduction-design.md` (the step table gains rows 11 and 12 as a dated amendment)
- Test: `python/tests/test_reproduction_driver.py`

**Interfaces:**
- Consumes: everything above; the estimand lane's recreated-corpus sequence (`world`, `select_target`, `lists prepare`, `concepts`, `lists mint`, `type_target`, `hold`, `spec`, `run`, `belief`, `rederive`, `close`) and its `vocabulary.snapshot()`, `belief.context`, `belief.availability`, `belief.BINDING`.
- Produces: `compose.main()` minting the spine proposition and the composite and saving `spine_ref`, `composite_ref`, `composite_identity`, `composite_receipt` (the node outcomes, as `{label: tag}`); `read.main(argv)` writing `paths.WORK / "reading-1.json"` on the first run and, with `--again`, `reading-2.json` and `state.reading_equal`; the addendum.

- [ ] **Step 1: The successor contracts**

Read the two predecessor identities **before** editing: `uv run --frozen python -c "from reproduction import vocabulary; print(vocabulary.contract().content_identity, vocabulary.biology().content_identity)"` (run from `python/` with `PYTHONPATH=tools`, as the driver's other steps are run — see the reproduction record §3 for the exact invocation). In `python/tools/reproduction/mm30.yaml` under `contract:` set `lineage: {successor: "<mm30 identity>"}`, bump `version`, and add after `estimands:`:

```yaml
  edges:
    affects-concept-concept:            { cause: 0, effect: 1 }
    affects-concept-molecular-entity:   { cause: 0, effect: 1 }
    affects-molecular-entity-concept:   { cause: 0, effect: 1 }
    regulates-concept-concept:          { cause: 0, effect: 1 }
    regulates-concept-molecular-entity: { cause: 0, effect: 1 }
    regulates-molecular-entity-concept: { cause: 0, effect: 1 }
    induces-state-concept-concept:      { cause: 0, effect: 1 }
```

In `domains/biology/DOMAIN.yaml` set `lineage: {successor: "<biology identity>"}`, bump `version`, and add:

```yaml
edges:
  affects-molecular-entity-molecular-entity:   { cause: 0, effect: 1 }
  regulates-molecular-entity-molecular-entity: { cause: 0, effect: 1 }
```

`associates-with-*` and `binds-*` get no row (spec §3.3). `shipped_domain_contract("biology")` loads the document with its predecessor per the biology pack design's succession rule — follow whatever the estimand lane did for its own successor (its plan Task 10 Step 1) so the predecessor chain is checked, not skipped. Run `uv run --frozen pytest tests/test_domain_boundary.py tests/test_biology_pack.py -q` (or whichever module pins the shipped biology identity) and update the pinned identity in the same commit.

- [ ] **Step 2: `compose.py`**

```python
"""Step 11: mint the h1-prognosis spine and compose the fragment (composite-claims design §9)."""

from __future__ import annotations

import sys

from beliefs import stored
from beliefs.claim import Referent, build_claim
from beliefs.composite import CompositeError, CompositeNode, build_composite
from beliefs.projection import project_claim
from reproduction import findings, state, vocabulary, world

SPINE_SLUG = "protein-phf19-affects-concept-overall-survival"
COMPOSITE_SLUG = "h1-prognosis-fragment"


def main() -> int:
    st = state.load()
    profile = vocabulary.profile()
    writer = world.open_writer()
    spine_claim = build_claim(
        profile,
        operator="mm30/affects-molecular-entity-concept",
        args=(Referent("biology/molecular-entity", "protein:PHF19"), Referent("mm30/concept", "concept:overall-survival")),
        layer="causal",
        polarity="negative",
    )
    spine = writer.add(
        stored.proposition_node(
            SPINE_SLUG,
            title="PHF19 expression affects overall survival (negatively)",
            claim=project_claim(spine_claim),
            display_statement="Higher PHF19 expression predicts shorter overall survival — inquiry 0001-prognosis's spine, minted here with no evidence.",
        )
    )
    nodes = [
        CompositeNode("mm30/concept", "concept:disease-stage"),
        CompositeNode("biology/molecular-entity", "protein:PHF19"),
        CompositeNode("mm30/concept", "concept:overall-survival"),
    ]
    try:
        value, receipt = build_composite(
            profile, writer.read_view, shape="dag", nodes=nodes, members=[st["proposition_ref"], spine.id],
            snapshot=vocabulary.snapshot(), slug=COMPOSITE_SLUG,
        )
    except CompositeError as refused:
        findings.record(11, "design-gap" if refused.code == "composite-node-not-member" else "defect", f"build_composite refused: {refused}", filed="composite-claims design §9")
        state.save(spine_ref=spine.id, composite_refusal=f"{refused.code}: {refused}")
        print(f"REFUSED: {refused}")
        return 2
    minted = writer.add(stored.composite_node(value, title="h1-prognosis fragment: disease stage → PHF19 ⊣ overall survival"))
    state.save(
        spine_ref=spine.id,
        composite_ref=minted.id,
        composite_identity=value.identity,
        composite_receipt={label: outcome.value for label, outcome in receipt.outcomes.items()},
    )
    outcomes = state.load()["composite_receipt"]
    # The reproduction's snapshot consults concepts, levels, measures and identifications and leaves
    # `biology/molecular-entity` unconsulted, so PHF19 — node:0, since "biology" sorts before "mm30" —
    # resolves `not-consulted`, and the two concepts `member` (design §4.1: a check not performed is not a finding).
    expected = {"node:0": "not-consulted", "node:1": "member", "node:2": "member"}
    findings.record(11, "closed" if outcomes == expected else "defect", f"composed {minted.id} ({value.identity[:16]}…) over {len(value.edges)} edges; node outcomes {outcomes} (expected {expected})")
    print(f"composed {minted.id}; edges {[(e.cause.term, e.effect.term, e.sign) for e in value.edges]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

The concept list holds `overall-survival` (measured 2026-09-12 against `entities/concepts/` in the predecessor, the same directory `concepts.concept_lines` reads). If the term nonetheless resolves `not-member` under the reproduction's snapshot, the refusal is the addendum's first finding, `read.py` is not run, and U10 is discharged **unrun** (any unrun arm is partial; the cut's results record says so).

- [ ] **Step 3: `read.py`**

```python
"""Step 12: read the composite, in a fresh process, twice (composite-claims design §6, §9; U8, U10)."""

from __future__ import annotations

import json
import sys

from beliefs.belief import NotReached
from beliefs.composite import read_composite
from beliefs.identity import v1
from reproduction import belief, findings, paths, state, vocabulary, world


def main(argv: list[str]) -> int:
    st = state.load()
    again = "--again" in argv
    view = world.open_writer().read_view
    reading = read_composite(
        view,
        st["composite_ref"],
        context=belief.context(view),
        availability=belief.availability(view),
        resolution=vocabulary.snapshot(),
        binding=belief.BINDING,
        profile=vocabulary.profile(),
    )
    encoded = v1.encode(reading.projection())
    out = paths.WORK / ("reading-2.json" if again else "reading-1.json")
    out.write_bytes(encoded)
    rows = {
        row.ref: (
            row.role.sign,
            row.belief.__class__.__name__,
            "not-reached" if isinstance(row.identification, NotReached) else list(row.identification),
        )
        for row in reading.rows
    }
    if again:
        equal = (paths.WORK / "reading-1.json").read_bytes() == encoded
        state.save(reading_equal=equal, reading_rows=rows)
        findings.record(12, "closed" if equal else "defect", f"second-process reading {'equal' if equal else 'DIFFERS'}; rows {rows}")
    else:
        state.save(reading_rows=rows)
    print(json.dumps({"standing": reading.standing.projection(), "nodes": dict(reading.projection()["node_outcomes"]), "rows": rows}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

- [ ] **Step 4: Recreate, run, read twice**

Move the estimand lane's corpus aside (`mv <CHECKOUT>/.work/reproduction/mm30 <CHECKOUT>/.work/reproduction/mm30.estimand` — the base contract changed, decision 11) and run the driver's steps in order: `world`, `select_target`, `lists prepare`, `concepts`, `lists mint`, `type_target`, `hold`, `spec`, `run`, `belief`, `rederive`, `close`, then `compose`, then `read` and `read --again`, each `read` in its own process. Then open the moved-aside corpus read-only and record that `audit_corpus` returns exactly one finding, `profile-mismatch` with detail `base` (it pins the estimand lane's base contract, which lacks `composite_grammar`), and reads no record — decision 11's transition arm, measured. Write rows 11 and 12 into the reproduction design's step table as a dated amendment.

- [ ] **Step 5: The addendum and the unit test**

Append `## 11. Addendum — composite claims, <date>` to `docs/designs/2026-09-05-mm30-reproduction.md`: the two successor contract identities; the spine proposition's identity and its claim as spelled; the composite's identity, its three nodes and two signed edges; the node receipt — `node:0` (PHF19, `biology/molecular-entity`) `not-consulted` because the reproduction's snapshot binds no HGNC release, `node:1` and `node:2` (the two concepts) `member`; the reading's rows — the target member `edge(disease-stage → PHF19, positive)` with the `belief` step's answer and identification `{identification:observational}`, the spine member `edge(PHF19 → overall-survival, negative)` with `NoBelief("no-eligible-assessment")` and `()`; the two encodings' equality; the moved-aside corpus's `profile-mismatch: base`; and the author's judgment that the fragment is the inquiry's spine and not its DAG — the proxies (`is-proxy-for`) and the other nodes are not minted, the first exercise of spec limitation 5. Add to `python/tests/test_reproduction_driver.py`:

```python
def test_the_reading_projection_round_trips_through_identity_v1(tmp_path):
    from beliefs.composite import CompositeNode, CompositeReading, Resolution
    from beliefs.identity import v1
    from beliefs.resolution import TermOutcome

    reading = CompositeReading(
        ref="composite:x", identity="a" * 64, shape="dag",
        nodes=(CompositeNode("mm30/concept", "concept:a"),),
        standing=Resolution("active", ()),
        node_outcomes={"node:0": TermOutcome.NOT_CONSULTED},
        rows=(),
    )
    assert v1.encode(reading.projection()) == v1.encode(json.loads(v1.encode(reading.projection())))
```

(`import json` at the top.)

- [ ] **Step 6: Commit**

```bash
git add python/tools/reproduction domains/biology python/src/beliefs/domains docs/designs/2026-09-05-mm30-reproduction.md docs/superpowers/specs/2026-09-05-mm30-reproduction-design.md python/tests
git commit -m "feat(reproduction): compose the h1-prognosis spine under successor contracts and read it twice (U10)"
```

---

### Task 8: Acceptance, the N2 declaration, the guard and the runner

**Files:**
- Create: `python/tests/acceptance/test_composite_acceptance.py`, `python/tests/n2_arms_cut<N>.py`, `python/tests/acceptance/n2_arms_cut<N>.py` (the re-export shim on cut 26's shape), `python/tests/acceptance/test_n2_cut<N>.py`, `python/tools/cut<N>_acceptance.py`

**Interfaces:**
- Consumes: the frozen cut document and `<N>` (Task 0); every module above.
- Produces: U1–U10 discharged on the certified volume; the guard pinning the freeze commit, the cut document's SHA-256 and the declaration's SHA-256.

- [ ] **Step 1: The frozen cut is Task 0's**

Nothing in the frozen document is edited; a correction found while writing the arms is a dated supplement in the cut document's §8, on cut 25's precedent.

- [ ] **Step 2: The acceptance module**

`python/tests/acceptance/test_composite_acceptance.py`: one test per U row, `test_u<n>_<slug>`, composed from the unit tests' constructions over a registered durable corpus (the `durable_root` fixture and `open_corpus(durable_root, authority=FULL, profile=WITH_BIOLOGY)` pattern of `test_permit_acceptance.py`), with the reproduction-backed rows reading the addendum's recorded state:

- `test_u1_grammar_kind_and_relations` — the shipped contract's declarations in Python and, via `subprocess.run(["npx", "vitest", "run", "tests/declarations.test.ts"], cwd=ts)`, in TypeScript.
- `test_u2_edges_declared_and_never_redefined` — `test_domain_contract.TestEdges` over the durable corpus's pinned profile.
- `test_u3_form_classification_and_vocabulary_arms` — the two halves: `add` refuses each form/classification row; `add` admits the vocabulary-excluded isolated node that `build_composite` and `read_composite` refuse/report.
- `test_u4_belief_inert` — read the belief input digest of `proposition:ab` through `evaluate_over` before and after minting, superseding and deleting a composite naming it; byte-identical each time; an assessment with otherwise valid evidence — an observing run over a held, attested dataset — whose `assesses` target is the composite is refused at `add` and at `import_bundle` with `SignatureRefused("…assesses-target-kind…")`, and one whose target resolves nowhere with `…assesses-target-unresolvable…` (Task 4's guard; the eligibility predicate alone admits both, so a `composite:future` could otherwise establish the edge by arriving second).
- `test_u5_identity` — the three pairs of `test_composite.py`.
- `test_u6_boundary_resolution_and_identity` — the swapped member, the dataset member, the unresolvable ref, through `add` and through `import_bundle`.
- `test_u7_audit_codes` — the four codes plus `supersedes-cross-kind`, each still read by later arms.
- `test_u8_reading_equals_the_wrapper` — every row compared with `evaluate_over`; the withholding arms; the two-inconclusive fixture; the one-admitted-one-refused fixture; the memberless composite; the unresolvable member; and two `subprocess` readings of the durable corpus compared byte for byte.
- `test_u9_supersession` — the three family calls, the import arms in both directions, the audited raw pair, the parser mutation in both implementations.
- `test_u10_reproduction` — reads `<CHECKOUT>/.work/reproduction/mm30/state.json` and asserts `reading_equal is True`, `composite_receipt == {"node:0": "not-consulted", "node:1": "member", "node:2": "member"}` (PHF19's sort is unconsulted under the reproduction's snapshot; the two concepts are members), and `reading_rows` names the two refs with signs `positive` and `negative`; skipped with the addendum's recorded refusal named when `composite_refusal` is present (an unrun arm, reported as such).

- [ ] **Step 3: The declaration file**

`python/tests/n2_arms_cut<N>.py`, one `Arm` per sabotage in spec §10.3 plus the mechanisms named in Tasks 3–6, `before` blocks copied verbatim from the tree at freeze, each `checks=` naming the acceptance test it must fail. The arms, by mechanism:

| row | sabotage (module, what changes) | must fail |
|---|---|---|
| U4-a | `closure.py`: the projection gains the composites naming the proposition | `test_u4_belief_inert` (digest moves on mint) |
| U4-b | `contracts/science/CONTRACT.yaml` (both copies): `assesses` targets gain `composite` | `test_u1_…`, `test_u4_…` |
| U4-c | `corpus.py` `_refuse_assesses_target_kind`: `target.kind != "proposition"` becomes `False` | `test_u4_…` (the otherwise-eligible assessment is admitted) |
| U4-d | `corpus.py` `_refuse_assesses_target_kind`: the `except RefError` arm becomes `continue` | `test_u4_…` (the `composite:future` assessment is admitted) |
| U3-a | `composite.py` `classify`: the `layer != "causal"` refusal dropped | `test_u3_…` (the `associates-with`/statistical fixture) |
| U3-b | `composite.py` `classify`: `Edge(... sign=claim.polarity ...)` skipped for `negative` (member dropped from `edges`) | `test_u3_…` (the signed-cycle fixture) |
| U3-c | `composite.py` `build_composite`: `refused` computed over `outcome.performed` instead of `outcome.refuses` (admits `not-member`) | `test_u3_…` (the excluding-snapshot fixture) |
| U3-d | `composite.py` `_canonical_nodes`: the empty-set refusal dropped | `test_u3_…` |
| U5-a | `composite.py` `composite_identity`: `nodes` omitted from the projection | `test_u5_identity` |
| U6-a | `corpus.py` `_refuse_composite`: `restore_members` call replaced by a form-only pass (step 3 skipped) | `test_u6_…` (the swapped member is admitted) |
| U6-b | `corpus.py` `_refuse_composite`: the `len(composes) != len(facet.members)` check dropped | `test_u6_…` |
| U7-a | `audit.py` `audit_corpus`: the `composite` arm dropped | `test_u7_audit_codes` |
| U7-b | `audit.py` `check_composite`: `composite-member-unresolvable` mapped to `composite-malformed` | `test_u7_audit_codes` |
| U8-a | `composite.py` `read_composite`: an unresolvable member yields a row with `NoBelief("no-eligible-assessment")` instead of refusing | `test_u8_…` |
| U8-b | `composite.py` `read_composite`: `identification = ("identification:observational",)` when the set is empty | `test_u8_…` (the `{}` arm) |
| U8-c | `composite.py` `read_composite`: `availability` replaced by one built from `view` (every stored holdings observation) | `test_u8_…` (the withholding arms) |
| U8-d | `composite.py` `read_composite`: `evaluate_over_traced` replaced by `gather` + `evaluate_traced` (the absent-corpus arm skipped) | `test_u8_…` (the absent-corpus row) |
| U8-e | `composite.py` `read_composite`: the identification column calls `admission.admit` per gathered assessment instead of reading `admission.admitted` | `test_u8_…` (the `admit`-count trap) |
| U8-g | `composite.py` `read_composite`: the identification column calls `belief.admitted` a second time over the gathered records | `test_u8_…` (the `admitted`-count trap) |
| U8-f | `belief.py` `evaluate_traced`: every `NoBelief` return carries `NotReached()` | `test_u8_…` (the two-inconclusive fixture) |
| U9-a | `corpus.py` `_refuse`: `_refuse_supersedes_same_kind` moved under `if not document_validated:` | `test_u9_supersession` (the import arm) |
| U9-b | `contract/base.py`: the `same_kind and set(sources) != set(targets)` refusal dropped | `test_u9_supersession` (the parser arm) |
| U9-c | `audit.py` `check_supersedes_kinds`: `target.kind != node.kind` becomes `False` | `test_u9_supersession` (the audited raw pair) |
| U2-a | `contract/domain.py` `_parse_edge`: the `"causal" not in operator.layers` refusal dropped | `test_u2_…` |
| U2-b | `contract/domain.py` `_declarations`: the `edge:` group dropped | `test_u2_…` (succession redefines) |
| U1-a | `contract/base.py`: `composite_grammar` made optional (`root.get("composite_grammar", {...})`) | `test_u1_…` |

Every `before` must occur exactly once in its module (the harness reports staleness otherwise), so each is copied from the tree at freeze, never paraphrased.

- [ ] **Step 4: The guard and the runner**

`python/tests/acceptance/test_n2_cut<N>.py` on `test_n2_cut26.py`'s shape: `FROZEN_CUT`, `CUT<N>_FREEZE_COMMIT`, `CUT<N>_FROZEN_SHA256`, `FROZEN_DECLARATION`, `CUT<N>_DECLARATION_SHA256`, `FROZEN_PRIOR_CUT_FILES` extended with every declaration frozen since cut 26 (cut 26's own and the estimand lane's, with their commits), `PRIOR_ARMS` extended likewise, the accounting test, the freeze pins, and the audit over every arm with the staleness baseline taken from the tree (never `stale: []`). `python/tools/cut<N>_acceptance.py` on `cut26_acceptance.py`'s shape with `PREFIX_RUNNERS = ("<highest discharged runner at freeze>",)` and `PHASE_MODULES = ("test_composite_acceptance.py", "test_n2_cut<N>.py")`.

- [ ] **Step 5: Freeze, discharge, commit**

Pin the commit and hashes in the guard, then discharge on the certified volume: `uv run --frozen python tools/cut<N>_acceptance.py`, then `just hook-pre-push`. Record both summary lines.

```bash
git add python/tests/acceptance python/tests/n2_arms_cut<N>.py python/tools/cut<N>_acceptance.py
git commit -m "test(cut): discharge conformance cut <N>, composite claims U1–U10"
```

---

### Task 9: Amendments, the results record, the ledger and the roadmap

**Files:**
- Modify: `docs/designs/2026-09-12-composite-claims-design.md` (the *Status* header); `docs/designs/2026-08-02-epistemic-kernel-design.md` §4.1 (the `composes` signature; `supersedes` same-kind over two kinds), §4.3 (a `composite` paragraph beside Views), §4.4 (the open row loses three entries; the kernel counts fourteen since <date>), §11 (the first bullet closed by citation); `docs/designs/2026-08-04-formal-model-and-claim-calculus-design.md` §2.1 (a fourteenth `Rec` row: construction built, identity content over the covered facet, lifecycle `supersedes` same-kind, reads its members, affects nothing, inert under display prose and the `composes` targets' resolution state, banked U1–U10), §2.2 (the `composes` signature row and `supersedes`' widened signature), §8.2 (the amendment record); `docs/designs/2026-08-31-coordination-and-view-kinds-design.md` §5.1 (a dated note: `composes` is not in version 1's literal relation list; the amendment is sub-project 5's road); `docs/superpowers/specs/2026-08-29-user-and-autonomy-layer-design.md` §6.1 ("a composite's closure is its members"); `docs/guide/foundations.md` (the kinds table: a fourteenth row under *Epistemic*; the "not additional kernel kinds" sentence keeps views out and says composites are in), `docs/guide/claims-and-belief.md` (a short *Composites* section: what one asserts, how it is read, that it is never a belief input), `docs/guide/glossary.md` (Composite, Edge, Node receipt, Same-kind succession), `docs/guide/open-questions.md` (*Kernel-adjacent structures* closed by citation for `inquiry`, `patch-definition`, `structural-chain`; `search` stays; a new entry for relation endpoint kinds at the write boundary, limitation 17); `docs/designs/2026-08-03-redesign-adoption-ledger.md` `Current state` (a `composite-claims` row, then its closure at discharge); `docs/plans/2026-08-29-implementation-roadmap.md` (boundary index row `composite-claims | U1–U10 | 1, off the path | beliefs-4bcf88`; the off-path table; the lane table's `mutation`-adjacent surfaces note; Appendix A/B); `docs/plans/<date>-conformance-cut-<N>-results.md`
- Every amendment is a dated block in place, never an edit of frozen prose; each names this design by path.

- [ ] **Step 1: The spec's status**

The two corrections found while planning (§3.1's non-existent signature check; §3.2's `I_claim` wording) and limitation 17 are already recorded in the design's §13 and §15 by the planning commit. Here only the header's *Status* changes, to frozen at the cut, with the freeze commit named.

- [ ] **Step 2: Results record**

On cut 26's results shape: what ran (both summary lines, the arms' verdicts, the baseline), accounting and disposition (U1–U10 closed, or U10 unrun with the addendum's refusal named; the global row total moves by 10), corrections and deviations from the frozen cut, remaining boundary (the coordination-contract relation-list amendment, sub-project 5's).

- [ ] **Step 3: Ledger, roadmap, tasks**

Add the `composite-claims` row to the ledger table and the roadmap's boundary index, tier 1 off the path, lane `composite-claims`, then mark it closed in the same results commit; rewrite the roadmap whole (it carries no dated corrections); `tasks dep beliefs-eacbe2 --on beliefs-4bcf88`. Run `uv run --frozen pytest tests/test_designs_corpus.py tests/test_check_guide.py` and `uv run --frozen python tools/roadmap_status.py` green. `tasks done` each step child as its commit lands; `tasks done beliefs-4bcf88 "<what landed>"` in the results commit; `tasks check` clean.

```bash
git add docs python/tests/test_designs_corpus.py tasks
git commit -m "docs(cut): discharge conformance cut <N>; close composite-claims and amend the banked designs"
```

---

## Self-review

**Spec coverage.** §3.1 → Task 1; §3.2 → Task 3 (`CompositeFacet`, `composite_value`); §3.3 → Task 2; §3.4 → Task 3 (`classify`, `_refuse_cycle`) and Task 4's re-derivation; §4.1 → Task 3 (`build_composite`, the receipt, `not-member` refusal, isolated nodes); §4.2 → Task 4; §4.3 → Task 5; §5 identity → Task 3 (`composite_identity` = the stamp), lifecycle → Task 4 (`supersede`), index/views → no code (the adjacency is predicate-generic; the coordination-contract amendment is sub-project 5's, named in Task 9), publication → Task 9's user-layer amendment (the `publish` code is sub-project 5's), no belief input → U4 in Task 8; §6.1 → Task 6 (`read_composite`, the wrapper, `projection`); §6.2 → Task 6 (`admitted`, `evaluate_traced`, `evaluate_over_traced`, the column from `AssessmentValue.estimand`); §6.3 → Task 6 (`composite-member-unresolvable`, `Resolution`); §7 → Task 9 (amendments; no code, by design); §8 → Task 8; §9 → Task 7; §10 → Tasks 0, 8; §11 → Tasks 0, 9; §13 limitations 1–16 → restated in the cut document (Task 0) with 17 added (Task 9).

**Placeholder scan.** Every code step carries its code; the one deliberately non-literal item is `<N>`, claimed at freeze by rule. The reproduction's `not-member` contingency is a measured outcome with a named disposition, not a fallback.

**Type consistency.** `CompositeNode(sort, term)` everywhere; `Edge.sign` is the polarity tag string in Tasks 3, 6, 7; `build_composite(profile, view, *, shape, nodes, members, snapshot, slug) -> (Composite, CompositeReceipt)` in Tasks 3, 4, 6, 7; `restore_members(view, facet_members, refs, *, profile, snapshot)` in Tasks 3, 4, 5, 6; `classify(profile, facet, claims)` in Tasks 3, 4, 5, 6; `Admission = NotReached | Reached(admitted)` in Task 6's three modules and Task 8's arms; `read_composite(view, ref, *, context, availability, resolution, binding, profile)` in Tasks 6, 7, 8; `RelationDecl.same_kind` in Tasks 1, 4, 5; `ProfileSpec.edges[<namespaced operator>].cause/.effect` in Tasks 2, 3.

**Two things the plan leaves to the tree at execution.** The estimand lane's fixture names (`typed_estimand`, `typed_applicability`, `TESTING_PROFILE`) and its `AssessmentValue.estimand` member are consumed as that plan defines them; if the merged lane spells them otherwise, Task 6 follows the tree and records the difference in a task note. The TypeScript identity fixture's regeneration command is read from the fixture's own header.
