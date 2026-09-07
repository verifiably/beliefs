# Facet Contracts and the Compiled Kind Registry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first `domain-boundary` slice: facet, kind and relation declarations in the contracts, the compiled per-kind registry and payload validators, the empirical-observation payload contract with its bearer invariant and attestation binding, the shipped base profile with the pin recheck under the operation lock, guarded production publication, the consulted walk's facet arm, the practice loader, and the second `science.identity.v1` parity fixture — discharging D2, D4, D5, D8, D9, D10, G5 and F1–F8 at conformance cut 20.

**Architecture:** The base contract (`contracts/science/CONTRACT.yaml`) gains `kinds:`, `relations:` and `facets:`; domain contracts gain namespaced `facets:`. `compile_profile` turns these into `CompiledKind` and `CompiledFacet` tables on `ProfileSpec`, one `nodes` `Registry` and one payload validator per schema-shaped facet. `stored.py`'s per-kind tables become views over a profile compiled once from the package's own copy of the base contract (`shipped_base()`), so the read side needs no argument; the writer holds a compiled profile, rechecks pin agreement under the operation lock before every write, and runs one new preflight step (`_refuse_facets`) that validates kind and keys against the registry, validates payloads, and applies the acquisition-boundary validity predicate (`beliefs/acquisition.py`). The production-run boundary publishes through a guarded port method that evaluates the bearer invariant under the same lock.

**Tech Stack:** Python 3.11+ (`uv run --frozen`), `pydantic` v2 `nodes` documents, `pyyaml`, `pytest`; TypeScript with `vitest`, `yaml` v2, `biome`; the `nodes` package's `Registry`/`KindSpec`; `science.identity.v1` canonical encoding on both sides.

**Spec:** `docs/designs/2026-09-05-facet-contracts-design.md` (the design; every task cites its sections). Read it before any task. Companion sources the design inherits: `docs/designs/2026-08-04-domain-extension-boundary-design.md` §3–§8 and its D table; kernel `2026-08-02-epistemic-kernel-design.md` §4.1.

## Global Constraints

- From `python/`: `uv run --frozen pytest`, `uv run --frozen ruff check .`, `uv run --frozen pyright` must pass at every commit. From `ts/`: `npm test`, `npm run typecheck`, `npm run check` must pass at every commit. Run the Python suite with the project venv, never system python.
- Never edit `tasks/*.md` directly; use the `tasks` CLI. Run `tasks start <id>` before a task, `tasks done <id> "<result>"` in the commit that lands it.
- Conventional commits, no AI-attribution trailer or footer of any kind.
- Fail early, no silent fallbacks: every refusal is raised or reported, never skipped. Unknown keys are refused, never ignored (design §3.4, §3.7).
- Every new check must be able to fail (N2): each test asserts a refusal or a finding a sabotage would turn green.
- `ProfileSpec`, `BaseContract`, `DomainContract` stay parsed/compiled, never authored (the `_MINT` token pattern); do not add public constructors.
- The normative base contract stays at `contracts/science/CONTRACT.yaml`; the packaged copy is held byte-identical by a test (design §4.2).
- Do not create a real biology domain: fixture contracts live under `fixtures/contracts/` or `python/tests/` and are named as fixtures (design §3.2, D limitation 5).
- No `/home/keith` or `/mnt/ssd/Dropbox` paths in code or docs.
- The worktree is `.worktrees/domain-boundary` on `feat/domain-boundary`; run everything from it.

---

## File structure

**Created**

| path | responsibility |
|---|---|
| `python/src/beliefs/contract/document.py` | `load_document(path, *, source)`: YAML load that refuses duplicate mapping keys at every level (§3.7) |
| `python/src/beliefs/contract/facets.py` | `FieldDecl`, `FacetDecl`, `parse_facet_declarations`, the §3.4 grammar's parse-time closure, shared by base and domain parsers |
| `python/src/beliefs/contract/practice.py` | `Practice`, `parse_practice`, `load_practice` (§3.6) |
| `python/src/beliefs/facets.py` | `validate_payload(facet: CompiledFacet, payload) -> None` raising `FacetPayloadRefused` (§4.1) |
| `python/src/beliefs/acquisition.py` | the acquisition-boundary validity predicate and the bearer invariant (§2 items 1, 14; §5.2) |
| `python/src/beliefs/contracts/science/CONTRACT.yaml` | the packaged copy of the base contract (§4.2) |
| `python/tests/profiles.py` | test profiles compiled from real contracts: `BASE`, `WITH_BIOLOGY`, `WITH_BIOLOGY_OTHER`, `pins_for(profile)` |
| `python/tests/fixtures/biology-fixture.yaml` | a test-only domain contract in the `biology` namespace, two variants by description |
| `python/tests/test_document_loader.py`, `test_facet_declarations.py`, `test_practice.py`, `test_facet_validation.py`, `test_acquisition.py`, `test_facet_seams.py`, `test_dataset_revision.py`, `test_guarded_publication.py`, `test_profile_agreement.py`, `test_identity_parity_fixture.py`, `n2_arms_cut20.py` | tests, one module per task |
| `python/tests/acceptance/test_facet_acceptance.py`, `test_n2_cut20.py`, `n2_arms_cut20.py` (acceptance copy), `python/tools/cut20_acceptance.py` | the cut-20 discharge surface |
| `python/tools/generate_identity_fixture.py`, `fixtures/identity-v1.json` | the second parity fixture (§7.3) |
| `ts/tests/identity-fixture.test.ts`, `ts/tests/declarations.test.ts` | TypeScript halves |
| `docs/designs/2026-09-05-conformance-cut-20.md` | the frozen cut |

**Modified**

| path | change |
|---|---|
| `contracts/science/CONTRACT.yaml` | `kinds:`, `relations:`, `facets:` (§3.1, §3.2, §6) |
| `fixtures/contracts/testing.yaml` | two fixture facets (§3.2) |
| `python/src/beliefs/contract/base.py`, `domain.py`, `coordination.py`, `__init__.py` | declarations, duplicate-key loading, exports |
| `python/src/beliefs/profile.py` | `CompiledKind`, `CompiledFacet`, registry, validators, `shipped_base()`, projection, no `stored` import (§4) |
| `python/src/beliefs/stored.py` | tables become views over `shipped_base()`; coverage sorted by key (§4.2) |
| `python/src/beliefs/corpus.py` | writer `profile`, pin recheck, `_refuse_facets`, dataset `revise` arm, import producer index, `corpus_check(view, profile)`, `eligibility_refusal(view, node, profile)`, read-side pin check (§5) |
| `python/src/beliefs/root.py`, `runrecord.py`, `boundary.py` | `execute_fulfilling_guarded` and the production guard (§5.4) |
| `python/src/beliefs/relocation.py` | destination preflight keeps attestation (§5.2) |
| `python/src/beliefs/audit.py` | `audit_corpus(view, *, evidence, profile)` and the stopping rule (§5.5) |
| `python/src/beliefs/consulted.py`, `evaluation.py`, `belief.py` | `facets_read` (§5.6) |
| `python/src/beliefs/errors.py` | `FacetPayloadRefused`, `AcquisitionBoundaryRefused` (§5.7) |
| `python/pyproject.toml` | package data for the contract copy |
| `ts/src/contract.ts`, `profile.ts`, `index.ts`, `README.md` | declarations parse and compile; scope line (§7.2) |
| `python/tests/fixtures_cut6.py`, `coordination_fixtures.py`, `conftest.py`, every test and tool constructing `CorpusWriter` | real pins and profiles (Task 7) |
| `python/tools/reproduction/hold.py`, `vocabulary.py`, `close.py` | locator, bound actor, profile (§11) |
| the design documents and guide pages listed in design §11 | amendments |

---

### Task 0: Freeze conformance cut 20

**Files:**
- Create: `docs/designs/2026-09-05-conformance-cut-20.md`
- Modify: `README.md` (design table row and count), `docs/designs/2026-09-05-facet-contracts-design.md` (status line), `docs/guide/contracts-and-adoption.md` (sources list cites the cut)

**Interfaces:**
- Produces: the frozen selection every later task's tests are named against; the unit names in §3 of the cut are the test ids Task 15's `n2_arms_cut20.py` must use verbatim.

- [ ] **Step 1: Write the cut document**

Mirror `docs/designs/2026-09-04-conformance-cut-18.md`'s structure exactly (§1 What this cut is, §2 The boundary, §3 Selection with one fenced row quote per selected row, §4 Accounting, §5 N2 and acceptance obligations, §6 Second reader, §7 Limitations). Content:

- **§1**: cut 20 is the frozen acceptance boundary for the facet-contracts slice (design §10); frozen before implementation; numbered after cut 19 (concurrency rule 1); discharge serialized after cut 19's (rule 5); the selection rule is cut 5's.
- **§2 In scope**: the eleven bullets of design §2 items 1–12 restated as boundaries. **Out of scope**: design's out-of-scope header verbatim, plus D6's facet arm and D1's `nodes`-tree negative.
- **§3 Selection**, one subsection per row, each with the fenced row quote copied byte-exact from its owning table (D rows from `2026-08-04-domain-extension-boundary-design.md` §10, G5 from the kernel §5, F rows from the design §8), followed by **Selected:** and **Deferred:** paragraphs:
  - `D1 — part`: selected the installed-package arms (no `nodes` API takes a domain, contract or vocabulary argument, checked by signature inspection over `nodes.core.registry.Registry.register`, `KindSpec`, `ShapeSpec`; the registry receives opaque keys); deferred the "add a `nodes` code path" negative.
  - `D2 — closes`, `D4 — closes`, `D5 — closes`, `D8 — closes`, `D9 — closes`, `D10 — closes`, `G5 — closes`: every arm of the frozen row, each mapped to a Task 15 acceptance test name (`test_d2_interpretation_is_separable_from_identity_durably`, `test_d4_one_kindspec_per_kind_compiled_from_the_profile`, `test_d5_manifest_pin_projection_and_refusals`, `test_d8_contributions_compose_without_collision`, `test_d9_practices_carry_no_vocabulary`, `test_d10_facets_stay_facets`, `test_g5_no_divergence_kind_exists`).
  - `F1`–`F8 — closes`: the design §8 rows, mapped to `test_f1_payload_contract_enforced_at_every_entry`, `test_f2_bearer_invariant_over_resulting_state`, `test_f3_attestation_bound_and_preserved`, `test_f4_eligibility_reads_the_validity_predicate`, `test_f5_profile_agreement_rechecked_under_the_lock`, `test_f6_dataset_revision_changes_interpretation_and_prose_only`, `test_f7_retrieval_resolves_or_refuses`, `test_f8_every_builder_facet_is_declared`.
  - `parity-fixture-2 — closes`: the formal model §8 obligation, mapped to `test_identity_parity_fixture.py` and `ts/tests/identity-fixture.test.ts`.
  - **Boundary invariants**: no read entry point gains an argument (§7.1); `WORLD_RELATIONS` unchanged in membership (§3.1).
- **§4 Accounting**: 16 rows read: 15 full/closed (D2, D4, D5, D8, D9, D10, G5, F1–F8), 1 partial (D1); plus the parity-fixture unit and the boundary-invariant unit: **18 declaration units**.
- **§5 N2 and acceptance obligations**: the aggregate runner names `cut19_acceptance.py` as its prefix (present once main carries cut 19), then runs `test_facet_acceptance.py` and the cut-20 N2 audit; the sabotage list is design §10's, one arm per named check; capability refusal is an error, never a skip.
- **§7 Limitations**: design §9 verbatim.

- [ ] **Step 2: Add the README row, bump the count, cite the cut from the guide, update the design status**

README: after the facet-contracts row add `| \`2026-09-05-conformance-cut-20.md\` | the twentieth frozen conformance cut, selecting the facet-contracts slice: 15 rows full, 1 part, with 18 declaration units |`; change `Forty-nine documents` to `Fifty documents` and extend `_COUNT_WORDS` in `python/tests/test_designs_corpus.py` with `50: "Fifty",`. In `docs/guide/contracts-and-adoption.md`'s front-matter `sources:` list add `  - ../designs/2026-09-05-conformance-cut-20.md` and in its Current state paragraph add one sentence: "Cut 20, the facet-contracts slice, is frozen and not yet discharged." In the design's status line replace `Not yet frozen: conformance cut 20 freezes after the written review clears, numbered after the writer-session lane's cut 19.` with `**Conformance cut 20 frozen 2026-09-05** (\`2026-09-05-conformance-cut-20.md\`), before implementation.`

- [ ] **Step 3: Run the guard**

Run: `cd python && uv run --frozen pytest tests/test_designs_corpus.py`
Expected: `14 passed`

- [ ] **Step 4: Commit**

```bash
git add docs/designs/2026-09-05-conformance-cut-20.md README.md docs/guide/contracts-and-adoption.md docs/designs/2026-09-05-facet-contracts-design.md python/tests/test_designs_corpus.py
git commit -m "docs(domain): freeze conformance cut 20 on the facet-contracts slice"
```

Record the freeze commit's short hash; Task 15 pins it.

---

### Task 1: A document loader that refuses duplicate keys

**Files:**
- Create: `python/src/beliefs/contract/document.py`, `python/tests/test_document_loader.py`, `ts/tests/declarations.test.ts` (first case)
- Modify: `python/src/beliefs/contract/base.py:237-248` (`load_base_contract`), `domain.py` (`load_domain_contract`), `coordination.py` (`load_coordination_contract`)

**Interfaces:**
- Produces: `load_document(path: Path, *, source: str) -> object` raising `MalformedContract` on a duplicate key at any depth or on malformed YAML.

- [ ] **Step 1: Write the failing tests**

```python
# python/tests/test_document_loader.py
"""§3.7: a duplicate mapping key is refused at load, at every depth, never kept last."""

import pytest

from beliefs.contract.document import load_document
from beliefs.errors import MalformedContract


def test_a_top_level_duplicate_key_is_refused(tmp_path):
    path = tmp_path / "c.yaml"
    path.write_text("contract: a\ncontract: b\n")
    with pytest.raises(MalformedContract, match="duplicate key 'contract'"):
        load_document(path, source="<test>")


def test_a_nested_duplicate_key_is_refused(tmp_path):
    path = tmp_path / "c.yaml"
    path.write_text("facets:\n  x:\n    fields:\n      locator: {type: string, required: true}\n      locator: {type: string, required: true}\n")
    with pytest.raises(MalformedContract, match="duplicate key 'locator'"):
        load_document(path, source="<test>")


def test_a_well_formed_document_loads_as_plain_values(tmp_path):
    path = tmp_path / "c.yaml"
    path.write_text("a: 1\nb: [x, y]\nc: {d: true}\n")
    assert load_document(path, source="<test>") == {"a": 1, "b": ["x", "y"], "c": {"d": True}}


def test_a_non_string_mapping_key_is_refused_not_crashed(tmp_path):
    path = tmp_path / "c.yaml"
    path.write_text("? [a, b]\n: 1\n")
    with pytest.raises(MalformedContract, match="not a string"):
        load_document(path, source="<test>")


def test_malformed_yaml_is_refused_as_a_contract_error(tmp_path):
    path = tmp_path / "c.yaml"
    path.write_text("a: [\n")
    with pytest.raises(MalformedContract, match="not well-formed YAML"):
        load_document(path, source="<test>")
```

- [ ] **Step 2: Run them to verify they fail**

Run: `cd python && uv run --frozen pytest tests/test_document_loader.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'beliefs.contract.document'`

- [ ] **Step 3: Write the loader**

```python
# python/src/beliefs/contract/document.py
"""Contract documents are loaded through one loader that refuses a duplicate
mapping key at every depth (facet-contracts design §3.7).

PyYAML's `safe_load` keeps the *last* of two equal keys, so a duplicate facet,
field, kind or relation declaration would vanish before compilation reached
D8's collision check. The TypeScript side's `yaml` parser refuses duplicates by
default; this loader is the Python half of that agreement.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from yaml.constructor import ConstructorError

from beliefs.errors import MalformedContract

__all__ = ["load_document", "parse_document"]


class _UniqueKeyLoader(yaml.SafeLoader):
    # A SafeLoader subclass: it constructs exactly the tags SafeLoader does and
    # adds two checks. `yaml.load(..., Loader=_UniqueKeyLoader)` is therefore as
    # safe as `safe_load`, the same pattern `world/registry.py`'s manifest loader uses.
    def construct_mapping(self, node: yaml.MappingNode, deep: bool = False) -> dict[object, object]:
        seen: set[str] = set()
        for key_node, _value in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str):
                raise ConstructorError(
                    "while constructing a mapping", node.start_mark, f"mapping key {key!r} is not a string", key_node.start_mark
                )
            if key in seen:
                raise ConstructorError(
                    "while constructing a mapping", node.start_mark, f"duplicate key {key!r}", key_node.start_mark
                )
            seen.add(key)
        return super().construct_mapping(node, deep=deep)


def parse_document(text: str, *, source: str) -> object:
    """Parse YAML text, refusing duplicate keys and parser errors as `MalformedContract`."""
    try:
        return yaml.load(text, Loader=_UniqueKeyLoader)
    except ConstructorError as exc:
        problem = str(exc.problem or "")
        if "duplicate key" in problem or "is not a string" in problem:
            raise MalformedContract(f"{source}: {problem}; refused, never kept last (§3.7)") from exc
        raise MalformedContract(f"{source}: not well-formed YAML: {exc}") from exc
    except yaml.YAMLError as exc:
        raise MalformedContract(f"{source}: not well-formed YAML: {exc}") from exc


def load_document(path: Path, *, source: str) -> object:
    return parse_document(Path(path).read_text(encoding="utf-8"), source=source)
```

Then in `base.py` replace `load_base_contract`'s body with:

```python
def load_base_contract(path: Path) -> BaseContract:
    """Read and validate the base contract at ``path`` (duplicate keys refused, §3.7)."""
    from beliefs.contract.document import load_document

    return parse_base_contract(load_document(path, source=str(path)), source=str(path))
```

Do the same in `domain.py`'s `load_domain_contract` and `coordination.py`'s `load_coordination_contract` (keep their signatures; replace the `yaml.safe_load` call with `load_document(path, source=str(path))` and drop the local `yaml.YAMLError` handling, which the loader now owns). Remove the now-unused `import yaml` from any of the three modules where nothing else uses it.

- [ ] **Step 4: Write the TypeScript case**

```ts
// ts/tests/declarations.test.ts
import { describe, expect, it } from "vitest";
import { parseBaseContract } from "../src/contract.js";

describe("document load refuses duplicate keys (design §3.7)", () => {
  it("refuses a duplicate top-level key rather than keeping the last", () => {
    const text = "contract: science\ncontract: science\nversion: 1\nclaim_grammar: {}\n";
    expect(() => parseBaseContract(text, "<dup>")).toThrow(/unique/i);
  });
});
```

- [ ] **Step 5: Run both suites**

Run: `cd python && uv run --frozen pytest tests/test_document_loader.py tests/test_base_contract.py tests/test_domain_contract.py tests/test_coordination_contract.py -q`
Expected: all pass.
Run: `cd ts && npm test`
Expected: all pass (the new case included; `yaml` v2 throws "Map keys must be unique").

- [ ] **Step 6: Lint, typecheck, commit**

Run: `cd python && uv run --frozen ruff check . && uv run --frozen pyright`; `cd ts && npm run typecheck && npm run check`

```bash
git add python/src/beliefs/contract/document.py python/src/beliefs/contract/base.py python/src/beliefs/contract/domain.py python/src/beliefs/contract/coordination.py python/tests/test_document_loader.py ts/tests/declarations.test.ts
git commit -m "feat(contract): refuse duplicate mapping keys at document load"
```

---

### Task 2: Base contract declarations — `kinds:`, `relations:`, `facets:` — in Python and TypeScript

**Files:**
- Create: `python/src/beliefs/contract/facets.py`, `python/tests/test_facet_declarations.py`
- Modify: `contracts/science/CONTRACT.yaml`, `python/src/beliefs/contract/base.py`, `python/src/beliefs/contract/__init__.py`, `ts/src/contract.ts`, `ts/tests/declarations.test.ts`, `python/tests/test_base_contract.py`

**Interfaces:**
- Produces (Python): `FieldDecl(name, type, required, kinds, schemes)`, `FacetDecl(key, shape, fields, attaches_to, description)`, `KindDecl(name, domain, facets: Mapping[str, FacetUse])`, `FacetUse(required, covered)`, `RelationDecl(name, group, sources, targets)`; `BaseContract.kinds`, `.relations`, `.facets`; `parse_facet_declarations(value, *, where, namespace) -> dict[str, FacetDecl]`.
- Produces (TypeScript): `BaseContract.kinds`, `.relations`, `.facets` with the same shape; the same refusals.
- Consumed by Tasks 3, 5.

- [ ] **Step 1: Write the failing Python tests**

```python
# python/tests/test_facet_declarations.py
"""Design §3.1, §3.2, §3.4: the declaration grammar's closure, in the base contract."""

import copy

import pytest

from beliefs.contract import base
from beliefs.contract.facets import FacetDecl, FieldDecl, parse_facet_declarations
from beliefs.errors import MalformedContract


def parse(document):
    return base.parse_base_contract(document, source="<test>")


class TestTheShippedDeclarations:
    def test_the_thirteen_world_kinds_and_three_prose_kinds_are_declared(self, base_contract):
        assert {n for n, k in base_contract.kinds.items() if k.role == "prose"} == {"interpretation", "discussion", "story"}
        assert {n for n, k in base_contract.kinds.items() if k.role == "world"} == {
            "proposition", "source-assertion", "assessment", "analysis-spec", "run", "verification",
            "dataset", "source", "holdings-observation", "retraction", "instrument-certification",
            "coreference-attestation", "act-report",
        }

    def test_the_deferred_kinds_carry_no_domain_and_no_facets(self, base_contract):
        for name in ("instrument-certification", "coreference-attestation"):
            assert base_contract.kinds[name].domain is None
            assert base_contract.kinds[name].facets == {}
            assert base_contract.kinds[name].role == "world"

    def test_a_prose_kind_may_carry_display_only_and_no_domain(self, base_contract):
        assert dict(base_contract.kinds["discussion"].facets) == {"display": base_contract.kinds["proposition"].facets["display"]}
        assert base_contract.kinds["discussion"].domain is None

    def test_a_prose_kind_declaring_a_domain_or_another_facet_is_refused(self, base_contract_path):
        from beliefs.contract.document import load_document

        doc = load_document(base_contract_path, source="<t>")
        bad = copy.deepcopy(doc)
        bad["kinds"]["story"]["domain"] = "science.story.v1"
        with pytest.raises(MalformedContract, match="prose"):
            parse(bad)
        bad = copy.deepcopy(doc)
        bad["kinds"]["story"]["facets"]["dataset"] = {"required": False, "covered": False}
        with pytest.raises(MalformedContract, match="prose"):
            parse(bad)

    def test_a_domain_string_is_checked_and_null_facets_are_refused(self, base_contract_path):
        from beliefs.contract.document import load_document

        doc = load_document(base_contract_path, source="<t>")
        bad = copy.deepcopy(doc)
        bad["kinds"]["dataset"]["domain"] = "dataset-v1"
        with pytest.raises(MalformedContract, match="science.<kind>.v<n>"):
            parse(bad)
        bad = copy.deepcopy(doc)
        bad["facets"]["empirical-observation"]["description"] = 7
        with pytest.raises(MalformedContract, match="description"):
            parse(bad)
        bad = copy.deepcopy(doc)
        bad["facets"] = None
        with pytest.raises(MalformedContract, match="mapping"):
            parse(bad)

    def test_dataset_declares_its_four_facets(self, base_contract):
        facets = base_contract.kinds["dataset"].facets
        assert facets["dataset"].required and facets["dataset"].covered
        assert not facets["empirical-observation"].required and facets["empirical-observation"].covered
        assert not facets["lineage-basis"].required and facets["lineage-basis"].covered
        assert not facets["display"].required and not facets["display"].covered

    def test_relations_come_in_two_groups(self, base_contract):
        world = {name for name, decl in base_contract.relations.items() if decl.group == "world"}
        lifecycle = {name for name, decl in base_contract.relations.items() if decl.group == "lifecycle"}
        assert world == {
            "assesses", "observes", "reads", "transforms", "produces", "produced_by", "executes",
            "targets", "verifies", "member_of", "grounded-in",
        }
        assert lifecycle == {"supersedes", "retracts", "succeeded-by", "anchored_in"}

    def test_empirical_observation_is_the_one_schema_shaped_facet(self, base_contract):
        schema_shaped = [key for key, decl in base_contract.facets.items() if decl.shape == "schema"]
        assert schema_shaped == ["empirical-observation"]
        fields = base_contract.facets["empirical-observation"].fields
        assert fields["locator"] == FieldDecl("locator", "locator", True, (), ("accession", "url", "instrument"))
        assert fields["attested_by"] == FieldDecl("attested_by", "actor", True, (), ())
        assert fields["retrieval"] == FieldDecl("retrieval", "ref", False, ("act-report",), ())

    def test_every_facet_a_kind_names_is_declared(self, base_contract):
        for kind in base_contract.kinds.values():
            for key in kind.facets:
                assert key in base_contract.facets, f"{kind.name} names undeclared facet {key!r}"


class TestTheGrammarsClosure:
    @pytest.fixture()
    def document(self, base_contract_path):
        from beliefs.contract.document import load_document

        return load_document(base_contract_path, source="<test>")

    def _with_field(self, document, field):
        doc = copy.deepcopy(document)
        doc["facets"]["empirical-observation"]["fields"]["extra"] = field
        return doc

    def test_required_is_a_mandatory_boolean(self, document):
        with pytest.raises(MalformedContract, match="required"):
            parse(self._with_field(document, {"type": "string"}))
        with pytest.raises(MalformedContract, match="required"):
            parse(self._with_field(document, {"type": "string", "required": "yes"}))

    def test_kinds_only_with_ref_and_schemes_only_with_locator(self, document):
        with pytest.raises(MalformedContract, match="kinds"):
            parse(self._with_field(document, {"type": "string", "required": True, "kinds": ["dataset"]}))
        with pytest.raises(MalformedContract, match="kinds"):
            parse(self._with_field(document, {"type": "ref", "required": True}))
        with pytest.raises(MalformedContract, match="schemes"):
            parse(self._with_field(document, {"type": "ref", "required": True, "kinds": ["dataset"], "schemes": ["x"]}))
        with pytest.raises(MalformedContract, match="schemes"):
            parse(self._with_field(document, {"type": "locator", "required": True}))

    def test_kinds_and_schemes_are_non_empty_distinct_sets(self, document):
        with pytest.raises(MalformedContract, match="non-empty"):
            parse(self._with_field(document, {"type": "ref", "required": True, "kinds": []}))
        with pytest.raises(MalformedContract, match="duplicate"):
            parse(self._with_field(document, {"type": "locator", "required": True, "schemes": ["url", "url"]}))

    def test_an_unknown_type_and_an_unknown_field_key_are_refused(self, document):
        with pytest.raises(MalformedContract, match="type"):
            parse(self._with_field(document, {"type": "float", "required": True}))
        with pytest.raises(MalformedContract, match="unknown field"):
            parse(self._with_field(document, {"type": "string", "required": True, "default": "x"}))

    def test_a_field_name_must_be_an_identifier(self, document):
        doc = copy.deepcopy(document)
        doc["facets"]["empirical-observation"]["fields"]["Bad-Name"] = {"type": "string", "required": True}
        with pytest.raises(MalformedContract, match="identifier"):
            parse(doc)

    def test_a_kind_naming_an_undeclared_facet_is_refused(self, document):
        doc = copy.deepcopy(document)
        doc["kinds"]["dataset"]["facets"]["mystery"] = {"required": False, "covered": False}
        with pytest.raises(MalformedContract, match="mystery"):
            parse(doc)

    def test_a_shape_must_be_reader_or_schema_and_match_its_body(self, document):
        doc = copy.deepcopy(document)
        doc["facets"]["dataset"]["shape"] = "magic"
        with pytest.raises(MalformedContract, match="shape"):
            parse(doc)
        doc = copy.deepcopy(document)
        doc["facets"]["dataset"]["fields"] = {}
        with pytest.raises(MalformedContract, match="reader-shaped"):
            parse(doc)
        doc = copy.deepcopy(document)
        del doc["facets"]["empirical-observation"]["fields"]
        with pytest.raises(MalformedContract, match="schema-shaped"):
            parse(doc)

    def test_a_relation_must_name_a_group_and_declared_kinds(self, document):
        doc = copy.deepcopy(document)
        doc["relations"]["observes"]["group"] = "other"
        with pytest.raises(MalformedContract, match="group"):
            parse(doc)
        doc = copy.deepcopy(document)
        doc["relations"]["observes"]["targets"] = ["divergence"]
        with pytest.raises(MalformedContract, match="divergence"):
            parse(doc)

    def test_the_content_identity_covers_the_new_sections(self, document):
        before = parse(document).content_identity
        doc = copy.deepcopy(document)
        doc["facets"]["empirical-observation"]["fields"]["locator"]["schemes"].append("ftp")
        assert parse(doc).content_identity != before


def test_parse_facet_declarations_namespaces_domain_keys():
    declared = parse_facet_declarations(
        {"gene-axis": {"attaches_to": ["dataset"], "fields": {"axis": {"type": "string", "required": True}}}},
        where="<test>: facets",
        namespace="biology",
    )
    assert set(declared) == {"biology/gene-axis"}
    assert declared["biology/gene-axis"] == FacetDecl(
        key="biology/gene-axis",
        shape="schema",
        fields={"axis": FieldDecl("axis", "string", True, (), ())},
        attaches_to=("dataset",),
        description=None,
    )
```

- [ ] **Step 2: Run them to verify they fail**

Run: `cd python && uv run --frozen pytest tests/test_facet_declarations.py -q`
Expected: FAIL (`ModuleNotFoundError: beliefs.contract.facets`).

- [ ] **Step 3: Add the sections to the shipped contract**

Append to `contracts/science/CONTRACT.yaml` (after `layers: [causal, structural, statistical, methodological]`):

```yaml

# --- kinds, relations and facets (facet-contracts design §3) -----------------
#
# The kernel's per-kind inventory, transcribed from what `stored.py` carried in
# code until this contract declared it (D4). A governed kind names its semantic
# domain and its facets; the stamp facet `semantic-identity` is implicit on
# every governed kind. The two deferred kinds are declared without a domain.

kinds:
  proposition:
    domain: science.proposition.v1
    facets:
      proposition: { required: true,  covered: true }
      display:     { required: false, covered: false }
  source-assertion:
    domain: science.source-assertion.v1
    facets:
      source-assertion: { required: true, covered: true }
  assessment:
    domain: science.assessment.v1
    facets:
      assessment: { required: true, covered: true }
  analysis-spec:
    domain: science.analysis-spec.v1
    facets:
      analysis-spec: { required: true, covered: true }
  run:
    domain: science.run.v1
    facets:
      run:         { required: true,  covered: true }
      run-closure: { required: false, covered: true }
  verification:
    domain: science.verification.v1
    facets:
      verification: { required: true, covered: true }
  dataset:
    domain: science.dataset.v1
    facets:
      dataset:               { required: true,  covered: true }
      empirical-observation: { required: false, covered: true }
      lineage-basis:         { required: false, covered: true }
      display:               { required: false, covered: false }
  source:
    domain: science.source.v1
    facets:
      source: { required: true, covered: true }
  holdings-observation:
    domain: science.holdings-observation.v1
    facets:
      holdings-observation: { required: true, covered: true }
  retraction:
    domain: science.retraction.v1
    facets:
      retraction: { required: true, covered: true }
  act-report:
    domain: science.act-report.v1
    facets:
      act-report: { required: true, covered: true }
  instrument-certification: {}
  coreference-attestation: {}
  # Kernel §4.4's belief-inert notes: hand-authored, undomained, unstamped,
  # never in a closure. Declared so the closed registry admits them (design
  # §3.1 as amended 2026-09-05). `WORLD_KINDS` excludes them by role.
  interpretation: { role: prose, facets: { display: { required: false, covered: false } } }
  discussion:     { role: prose, facets: { display: { required: false, covered: false } } }
  story:          { role: prose, facets: { display: { required: false, covered: false } } }

# Kernel §4.1's closed relation vocabulary. `world` is the queryable group
# `WORLD_RELATIONS` derives from; `lifecycle` relations are minted by adapters
# and are not query vocabulary. Endpoints are compiled, not yet enforced at
# write (design §9 item 2).
relations:
  assesses:     { group: world, sources: [assessment], targets: [proposition] }
  observes:     { group: world, sources: [run], targets: [dataset] }
  reads:        { group: world, sources: [run], targets: [dataset] }
  transforms:   { group: world, sources: [run], targets: [dataset] }
  produces:     { group: world, sources: [run], targets: [dataset] }
  produced_by:  { group: world, sources: [assessment], targets: [run] }
  executes:     { group: world, sources: [run], targets: [analysis-spec] }
  targets:      { group: world, sources: [analysis-spec], targets: [proposition] }
  verifies:     { group: world, sources: [verification], targets: [assessment] }
  member_of:    { group: world, sources: [source], targets: [dataset] }
  grounded-in:  { group: world, sources: [retraction], targets: [retraction, verification, source] }
  supersedes:   { group: lifecycle, sources: [proposition], targets: [proposition] }
  retracts:     { group: lifecycle, sources: [retraction], targets: [assessment, dataset, verification, source, run] }
  succeeded-by: { group: lifecycle, sources: [retraction], targets: [retraction] }
  anchored_in:  { group: lifecycle, sources: [source-assertion], targets: [source] }

# Two shapes (§3.2). `reader` names the kernel reader that decodes the payload
# and declares nothing about its strictness; `schema` carries `fields:` under
# the §3.4 grammar and is validated at every write seam.
facets:
  proposition:          { shape: reader, reader: decode.claim_from_stored }
  display:              { shape: reader, reader: stored.display_facet_malformed }
  source-assertion:     { shape: reader, reader: stored.source_assertion_value }
  assessment:           { shape: reader, reader: stored.assessment_value }
  analysis-spec:        { shape: reader, reader: stored.analysis_spec_value }
  run:                  { shape: reader, reader: stored.run_spec }
  run-closure:          { shape: reader, reader: runrecord.projection_of }
  verification:         { shape: reader, reader: stored.verification_value }
  dataset:              { shape: reader, reader: stored.dataset_declaration }
  lineage-basis:        { shape: reader, reader: stored.lineage_basis }
  source:               { shape: reader, reader: stored.external_identifiers }
  holdings-observation: { shape: reader, reader: stored.holdings_observation_value }
  retraction:           { shape: reader, reader: corpus.CorpusWriter._validated_retraction }
  act-report:           { shape: reader, reader: stored.act_report_facet }
  empirical-observation:
    shape: schema
    description: The declared acquisition boundary (design §6). `locator` names the most upstream form outside the held boundary; `attested_by` is bound to the writer's actor at mint; `retrieval` is the boundary-minted acquisition report when one exists.
    fields:
      locator:     { type: locator, required: true,  schemes: [accession, url, instrument] }
      attested_by: { type: actor,   required: true }
      retrieval:   { type: ref,     required: false, kinds: [act-report] }
```

The `reader:` value is documentation (a dotted name a reviewer can find); the parser checks it is a non-empty string and nothing more. Check the exact semantic-domain strings against `stored.SEMANTIC_DOMAINS` and `report_values.ACT_REPORT_DOMAIN` / `HOLDINGS_OBSERVATION_DOMAIN` before committing: run `cd python && uv run --frozen python -c "from beliefs import stored; print(stored.SEMANTIC_DOMAINS)"` and copy the two module-defined values verbatim into the YAML. `retracts`' targets: copy the kinds `stored.RETRACTION_REASONS`' owning design lists as retractable (assessment, dataset, verification, source, run); if `grep -n "def _resolve_retraction_target" -A30 python/src/beliefs/corpus.py` shows a narrower set, use that set.

- [ ] **Step 4: Write the shared facet grammar parser**

```python
# python/src/beliefs/contract/facets.py
"""Facet declarations — the §3.4 grammar's parse-time closure.

Shared by the base and domain parsers: an unnamespaced base facet and a
namespaced domain facet are the same declaration with a different key. What
is checked here is *structure*; resolution of `kinds` against the compiled
inventory happens at compile (`profile.compile_profile`), and a payload's
validity is `beliefs.facets.validate_payload`'s.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from beliefs.errors import MalformedContract

__all__ = ["FIELD_TYPES", "FacetDecl", "FieldDecl", "parse_facet_declarations"]

FIELD_TYPES = ("string", "integer", "boolean", "ref", "locator", "actor")
_FIELD_NAME = re.compile(r"[a-z][a-z0-9_]*")
_KEY = re.compile(r"[a-z][a-z0-9-]*")
_FIELD_KEYS = frozenset({"type", "required", "kinds", "schemes"})


@dataclass(frozen=True)
class FieldDecl:
    name: str
    type: str
    required: bool
    kinds: tuple[str, ...]
    schemes: tuple[str, ...]

    def projection(self) -> dict[str, object]:
        projection: dict[str, object] = {"type": self.type, "required": self.required}
        if self.type == "ref":
            projection["kinds"] = sorted(self.kinds)
        if self.type == "locator":
            projection["schemes"] = sorted(self.schemes)
        return projection


@dataclass(frozen=True)
class FacetDecl:
    key: str
    shape: str  # "reader" | "schema"
    fields: Mapping[str, FieldDecl]
    attaches_to: tuple[str, ...]
    description: str | None

    def projection(self) -> dict[str, object]:
        """The behavioural projection: shape, fields, attaches_to; never the description (§3.5)."""
        return {
            "shape": self.shape,
            "fields": {name: field.projection() for name, field in sorted(self.fields.items())},
            "attaches_to": sorted(self.attaches_to),
        }


def _mapping(value: object, where: str) -> dict[str, object]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise MalformedContract(f"{where}: expected a mapping with string keys")
    return value  # type: ignore[return-value]


def _names(value: object, where: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise MalformedContract(f"{where}: expected a non-empty list")
    names: list[str] = []
    for entry in value:
        if not isinstance(entry, str) or not _KEY.fullmatch(entry):
            raise MalformedContract(f"{where}: {entry!r} is not an identifier")
        if entry in names:
            raise MalformedContract(f"{where}: duplicate {entry!r}")
        names.append(entry)
    return tuple(names)


def parse_field(name: str, value: object, where: str) -> FieldDecl:
    if not _FIELD_NAME.fullmatch(name):
        raise MalformedContract(f"{where}: {name!r} is not a field identifier; expected `[a-z][a-z0-9_]*`")
    body = _mapping(value, where)
    unknown = sorted(set(body) - _FIELD_KEYS)
    if unknown:
        raise MalformedContract(f"{where}: unknown field key(s) {', '.join(unknown)}; refused, never ignored")
    field_type = body.get("type")
    if field_type not in FIELD_TYPES:
        raise MalformedContract(f"{where}: type {field_type!r} is not one of {', '.join(FIELD_TYPES)}")
    if "required" not in body or not isinstance(body["required"], bool):
        raise MalformedContract(f"{where}: required is a mandatory boolean")
    if ("kinds" in body) != (field_type == "ref"):
        raise MalformedContract(f"{where}: kinds is required for type ref and refused for every other type")
    if ("schemes" in body) != (field_type == "locator"):
        raise MalformedContract(f"{where}: schemes is required for type locator and refused for every other type")
    kinds = _names(body["kinds"], f"{where}: kinds") if field_type == "ref" else ()
    schemes = _names(body["schemes"], f"{where}: schemes") if field_type == "locator" else ()
    return FieldDecl(name=name, type=field_type, required=body["required"], kinds=kinds, schemes=schemes)


def parse_facet_declarations(value: object, *, where: str, namespace: str | None) -> dict[str, FacetDecl]:
    """Parse a `facets:` mapping. `namespace=None` for the base contract (unnamespaced
    keys, either shape); a domain namespace prefixes every key and requires
    `attaches_to` and the schema shape."""
    declarations: dict[str, FacetDecl] = {}
    for local, body_value in _mapping(value, where).items():
        if not _KEY.fullmatch(local):
            raise MalformedContract(f"{where}: {local!r} is not a facet identifier")
        facet_where = f"{where}.{local}"
        body = _mapping(body_value, facet_where)
        key = local if namespace is None else f"{namespace}/{local}"
        description = body.get("description")
        if "description" in body and not isinstance(description, str):
            raise MalformedContract(f"{facet_where}: description is a string, never null")
        if namespace is None:
            shape = body.get("shape")
            if shape not in ("reader", "schema"):
                raise MalformedContract(f"{facet_where}: shape is `reader` or `schema`, found {shape!r}")
            permitted = {"shape", "description", "reader"} if shape == "reader" else {"shape", "description", "fields"}
            unknown = sorted(set(body) - permitted)
            if unknown:
                raise MalformedContract(f"{facet_where}: unknown key(s) {', '.join(unknown)} for a {shape}-shaped facet")
            if shape == "reader":
                if not isinstance(body.get("reader"), str) or not body["reader"]:
                    raise MalformedContract(f"{facet_where}: a reader-shaped facet names its reader")
                declarations[key] = FacetDecl(key, "reader", {}, (), description)
                continue
            if "fields" not in body:
                raise MalformedContract(f"{facet_where}: a schema-shaped facet declares fields")
            attaches_to: tuple[str, ...] = ()
        else:
            unknown = sorted(set(body) - {"attaches_to", "fields", "description"})
            if unknown:
                raise MalformedContract(f"{facet_where}: unknown key(s) {', '.join(unknown)}")
            if "attaches_to" not in body or "fields" not in body:
                raise MalformedContract(f"{facet_where}: a domain facet declares attaches_to and fields")
            attaches_to = _names(body["attaches_to"], f"{facet_where}: attaches_to")
        fields = {
            name: parse_field(name, field_value, f"{facet_where}.fields.{name}")
            for name, field_value in _mapping(body["fields"], f"{facet_where}.fields").items()
        }
        declarations[key] = FacetDecl(key, "schema", MappingProxyType(fields), attaches_to, description)
    return declarations
```

- [ ] **Step 5: Extend the base contract parser**

In `python/src/beliefs/contract/base.py`:

```python
# after _GRAMMAR_FIELDS
_CONTRACT_FIELDS = frozenset({"contract", "version", "claim_grammar", "kinds", "relations", "facets"})
_RELATION_GROUPS = ("world", "lifecycle")


@dataclass(frozen=True)
class FacetUse:
    required: bool
    covered: bool


@dataclass(frozen=True)
class KindDecl:
    name: str
    role: str  # "world" | "prose"
    domain: str | None
    facets: Mapping[str, FacetUse]

    def projection(self) -> dict[str, object]:
        # No null anywhere: `science.identity.v1` refuses it. An undomained kind
        # carries no `domain` key; its role says what it is.
        projection: dict[str, object] = {
            "role": self.role,
            "facets": {
                key: {"required": use.required, "covered": use.covered} for key, use in sorted(self.facets.items())
            },
        }
        if self.domain is not None:
            projection["domain"] = self.domain
        return projection


@dataclass(frozen=True)
class RelationDecl:
    name: str
    group: str
    sources: tuple[str, ...]
    targets: tuple[str, ...]

    def projection(self) -> dict[str, object]:
        return {"group": self.group, "sources": sorted(self.sources), "targets": sorted(self.targets)}
```

Add three fields to `BaseContract` (after `claim_grammar: ClaimGrammar`): `kinds: Mapping[str, KindDecl]`, `relations: Mapping[str, RelationDecl]`, `facets: Mapping[str, FacetDecl]` (import `FacetDecl, parse_facet_declarations` from `beliefs.contract.facets`). In `parse_base_contract`, after `claim_grammar = ClaimGrammar(...)` and before `return`, add:

```python
    facets = parse_facet_declarations(root["facets"], where=f"{source}: facets", namespace=None)

    kinds: dict[str, KindDecl] = {}
    for name, body_value in _mapping(root["kinds"], f"{source}: kinds").items():
        where = f"{source}: kinds.{name}"
        body = _mapping(body_value, where)
        _exact_fields_or_empty(body, frozenset({"domain", "facets", "role"}), where)
        role = body.get("role", "world")
        if role not in ("world", "prose"):
            raise MalformedContract(f"{where}: role is `world` or `prose`, found {role!r}")
        domain = body.get("domain")
        if role == "prose":
            if domain is not None or set(body.get("facets", {})) - {"display"}:
                raise MalformedContract(f"{where}: a prose kind carries no domain and no facet but display")
        elif body and (not isinstance(domain, str) or not v1_domain_ok(domain)):
            raise MalformedContract(f"{where}: a governed kind names a `science.<kind>.v<n>` domain")
        uses: dict[str, FacetUse] = {}
        for key, use_value in _mapping(body.get("facets", {}), f"{where}.facets").items():
            if key not in facets:
                raise MalformedContract(f"{where}.facets: {key!r} is not a facet this contract declares")
            use = _mapping(use_value, f"{where}.facets.{key}")
            _exact_fields(use, frozenset({"required", "covered"}), f"{where}.facets.{key}")
            if not isinstance(use["required"], bool) or not isinstance(use["covered"], bool):
                raise MalformedContract(f"{where}.facets.{key}: required and covered are booleans")
            uses[key] = FacetUse(required=use["required"], covered=use["covered"])
        kinds[name] = KindDecl(name=name, role=role, domain=domain if role == "world" and body else None, facets=MappingProxyType(uses))

    relations: dict[str, RelationDecl] = {}
    for name, body_value in _mapping(root["relations"], f"{source}: relations").items():
        where = f"{source}: relations.{name}"
        body = _mapping(body_value, where)
        _exact_fields(body, frozenset({"group", "sources", "targets"}), where)
        if body["group"] not in _RELATION_GROUPS:
            raise MalformedContract(f"{where}: group is one of {', '.join(_RELATION_GROUPS)}, found {body['group']!r}")
        sources = _closed_set(body["sources"], f"{where}: sources")
        targets = _closed_set(body["targets"], f"{where}: targets")
        for kind in (*sources, *targets):
            if kind not in kinds:
                raise MalformedContract(f"{where}: {kind!r} is not a kind this contract declares")
        relations[name] = RelationDecl(name=name, group=body["group"], sources=sources, targets=targets)
```

(`from types import MappingProxyType`; `FacetDecl.fields` is wrapped the same way in `contract/facets.py`: `fields=MappingProxyType(fields)`.) With two helpers beside `_exact_fields`:

```python
def _exact_fields_or_empty(mapping: dict[str, object], permitted: frozenset[str], where: str) -> None:
    """A deferred kind is `{}`; a governed kind carries exactly `domain` and `facets`."""
    if not mapping:
        return
    _exact_fields(mapping, permitted, where)


def v1_domain_ok(domain: str) -> bool:
    try:
        v1.check_domain(domain)
    except Exception:  # noqa: BLE001 - any refusal means "not a domain"
        return False
    return True
```

and pass `kinds=kinds, relations=relations, facets=facets` to `BaseContract._parsed`. Note `_closed_set` already refuses an empty list and duplicates, and `_mapping` is the local helper already defined in `base.py`. Export `FacetDecl`, `FieldDecl`, `FacetUse`, `KindDecl`, `RelationDecl` from `beliefs/contract/__init__.py`.

- [ ] **Step 6: Extend the TypeScript base parser**

In `ts/src/contract.ts` add exported interfaces and parse them with the same refusals:

```ts
export type FieldType = "string" | "integer" | "boolean" | "ref" | "locator" | "actor";
export interface FieldDecl {
  readonly name: string;
  readonly type: FieldType;
  readonly required: boolean;
  readonly kinds: readonly string[];
  readonly schemes: readonly string[];
}
export interface FacetDecl {
  readonly key: string;
  readonly shape: "reader" | "schema";
  readonly fields: DeclarationTable<FieldDecl>;
  readonly attachesTo: readonly string[];
}
export interface FacetUse {
  readonly required: boolean;
  readonly covered: boolean;
}
export interface KindDecl {
  readonly name: string;
  readonly role: "world" | "prose";
  readonly domain: string | null;
  readonly facets: DeclarationTable<FacetUse>;
}

const SEMANTIC_DOMAIN = /^science\.[a-z][a-z0-9-]*(\.[a-z][a-z0-9-]*)*\.v[1-9][0-9]*$/;
export interface RelationDecl {
  readonly name: string;
  readonly group: "world" | "lifecycle";
  readonly sources: readonly string[];
  readonly targets: readonly string[];
}

const FIELD_TYPES: readonly FieldType[] = ["string", "integer", "boolean", "ref", "locator", "actor"];
const FIELD_NAME = /^[a-z][a-z0-9_]*$/;

function parseField(name: string, value: unknown, where: string): FieldDecl {
  if (!FIELD_NAME.test(name)) throw new MalformedContract(`${where}: ${JSON.stringify(name)} is not a field identifier`);
  const body = mapping(value, where);
  exactFields(body, ["type", "required"], ["kinds", "schemes"], where);
  const type = body.type;
  if (typeof type !== "string" || !(FIELD_TYPES as readonly string[]).includes(type)) {
    throw new MalformedContract(`${where}: type ${JSON.stringify(type)} is not one of ${FIELD_TYPES.join(", ")}`);
  }
  if (typeof body.required !== "boolean") throw new MalformedContract(`${where}: required is a mandatory boolean`);
  if (("kinds" in body) !== (type === "ref")) {
    throw new MalformedContract(`${where}: kinds is required for type ref and refused for every other type`);
  }
  if (("schemes" in body) !== (type === "locator")) {
    throw new MalformedContract(`${where}: schemes is required for type locator and refused for every other type`);
  }
  return Object.freeze({
    name,
    type: type as FieldType,
    required: body.required,
    kinds: type === "ref" ? closedSet(body.kinds, `${where}.kinds`) : [],
    schemes: type === "locator" ? closedSet(body.schemes, `${where}.schemes`) : [],
  });
}

export function parseFacetDeclarations(value: unknown, where: string, namespace: string | null): DeclarationTable<FacetDecl> {
  const table: Record<string, FacetDecl> = Object.create(null);
  for (const [local, bodyValue] of Object.entries(mapping(value, where))) {
    const facetWhere = `${where}.${local}`;
    const body = mapping(bodyValue, facetWhere);
    const key = namespace === null ? tag(local, facetWhere) : `${namespace}/${tag(local, facetWhere)}`;
    if ("description" in body && typeof body.description !== "string") {
      throw new MalformedContract(`${facetWhere}: description is a string, never null`);
    }
    let shape: "reader" | "schema";
    let attachesTo: readonly string[] = [];
    if (namespace === null) {
      if (body.shape !== "reader" && body.shape !== "schema") {
        throw new MalformedContract(`${facetWhere}: shape is reader or schema`);
      }
      shape = body.shape;
      if (shape === "reader") {
        exactFields(body, ["shape", "reader"], ["description"], facetWhere);
        if (typeof body.reader !== "string" || body.reader === "") {
          throw new MalformedContract(`${facetWhere}: a reader-shaped facet names its reader`);
        }
        table[key] = Object.freeze({ key, shape, fields: Object.freeze(Object.create(null)), attachesTo: [] });
        continue;
      }
      exactFields(body, ["shape", "fields"], ["description"], facetWhere);
    } else {
      exactFields(body, ["attaches_to", "fields"], ["description"], facetWhere);
      shape = "schema";
      attachesTo = closedSet(body.attaches_to, `${facetWhere}.attaches_to`);
    }
    const fields: Record<string, FieldDecl> = Object.create(null);
    for (const [name, fieldValue] of Object.entries(mapping(body.fields, `${facetWhere}.fields`))) {
      fields[name] = parseField(name, fieldValue, `${facetWhere}.fields.${name}`);
    }
    table[key] = Object.freeze({ key, shape, fields: Object.freeze(fields), attachesTo });
  }
  return Object.freeze(table);
}
```

Then in `parseBaseContract`: change `exactFields(document, ["contract", "version", "claim_grammar"], [], source)` to require `kinds`, `relations`, `facets` too; parse `facets` with `parseFacetDeclarations(document.facets, \`${source}.facets\`, null)` (the `mapping` helper already refuses `null`, matching Python); parse `kinds` (each entry `{}` → `role: "world", domain: null, facets: {}`; otherwise exact fields `domain`, `facets`, `role` (optional, `world` default, else `prose`); a `world` kind's `domain` must match `SEMANTIC_DOMAIN` — the same syntax Python's `v1.check_domain` enforces — refusing with a message containing `science.<kind>.v<n>`; a `prose` kind refuses a `domain` and any facet but `display`; every facet key present in the facets table; `required`/`covered` booleans); parse `relations` (exact fields `group`, `sources`, `targets`; group in `world`/`lifecycle`; every endpoint a declared kind). Add `kinds`, `relations`, `facets` readonly members to `BaseContract` (frozen tables), thread them through the constructor `parts`, and export the new types from `ts/src/index.ts`. Refusal messages must contain the same key words the Python tests match on (`required`, `kinds`, `schemes`, `shape`, `group`).

- [ ] **Step 7: Add the TypeScript cases**

Append to `ts/tests/declarations.test.ts`:

```ts
import { readFileSync } from "node:fs";
const REPO_ROOT = new URL("../../", import.meta.url);
const SHIPPED = readFileSync(new URL("contracts/science/CONTRACT.yaml", REPO_ROOT), "utf-8");

describe("the base contract's declarations (design §3.1–§3.4)", () => {
  const base = parseBaseContract(SHIPPED, "contracts/science/CONTRACT.yaml");
  it("declares the thirteen world kinds with the deferred two undomained", () => {
    expect(Object.keys(base.kinds)).toHaveLength(13);
    expect(base.kinds["instrument-certification"].domain).toBeNull();
    expect(base.kinds["coreference-attestation"].facets).toEqual({});
  });
  it("declares empirical-observation as the one schema-shaped facet", () => {
    const schema = Object.values(base.facets).filter((f) => f.shape === "schema").map((f) => f.key);
    expect(schema).toEqual(["empirical-observation"]);
    expect(base.facets["empirical-observation"].fields.locator.schemes).toEqual(["accession", "url", "instrument"]);
  });
  it("refuses kinds on a non-ref field and schemes on a non-locator field", () => {
    const bad = SHIPPED.replace("attested_by: { type: actor,   required: true }", "attested_by: { type: actor, required: true, kinds: [x] }");
    expect(() => parseBaseContract(bad, "<bad>")).toThrow(/kinds/);
  });
  it("refuses a relation outside the two groups", () => {
    const bad = SHIPPED.replace("observes:     { group: world,", "observes:     { group: other,");
    expect(() => parseBaseContract(bad, "<bad>")).toThrow(/group/);
  });
  it("checks the semantic-domain syntax, a description's type, and refuses null facets — the same three refusals Python makes", () => {
    expect(() => parseBaseContract(SHIPPED.replace("domain: science.dataset.v1", "domain: dataset-v1"), "<bad>")).toThrow(/science\.<kind>\.v<n>/);
    expect(() => parseBaseContract(SHIPPED.replace("    description: The declared acquisition boundary", "    description: 7\n    x-ignored: The declared acquisition boundary"), "<bad>")).toThrow(/description|unknown/);
    expect(() => parseBaseContract(`${SHIPPED.split("\nfacets:")[0]}\nfacets: null\n`, "<bad>")).toThrow(/mapping/);
  });
  it("declares the three prose kinds with display only", () => {
    const base = parseBaseContract(SHIPPED, "contracts/science/CONTRACT.yaml");
    expect(base.kinds.discussion.role).toBe("prose");
    expect(Object.keys(base.kinds.discussion.facets)).toEqual(["display"]);
  });
});
```

(The `replace` strings must match the YAML exactly as written in Step 3; keep the spacing identical.)

- [ ] **Step 8: Update the existing base-contract tests and run everything**

`python/tests/test_base_contract.py` may have a test asserting `_CONTRACT_FIELDS` or an "unknown field refused" case using a field name that is now legal; adjust only those assertions. Run:

`cd python && uv run --frozen pytest tests/test_facet_declarations.py tests/test_base_contract.py tests/test_domain_contract.py tests/test_profile.py tests/test_parity_fixture.py -q` → all pass (the compiled identity and the claim fixture are unchanged because the projection does not yet carry the new sections).

`cd ts && npm test && npm run typecheck && npm run check` → pass.

Then the full Python suite: `cd python && uv run --frozen pytest` → pass; `uv run --frozen ruff check . && uv run --frozen pyright` → clean.

- [ ] **Step 9: Commit**

```bash
git add contracts/science/CONTRACT.yaml python/src/beliefs/contract python/tests/test_facet_declarations.py python/tests/test_base_contract.py ts/src/contract.ts ts/src/index.ts ts/tests/declarations.test.ts
git commit -m "feat(contract): declare kinds, relations and facets in the base contract, both languages"
```

---

### Task 3: Domain contract `facets:`, and the refusals of `kinds:` and `relations:`

**Files:**
- Modify: `python/src/beliefs/contract/domain.py`, `fixtures/contracts/testing.yaml`, `python/tests/test_domain_contract.py`, `ts/src/contract.ts`, `ts/tests/declarations.test.ts`

**Interfaces:**
- Produces: `DomainContract.facets: Mapping[str, FacetDecl]` (keys `<namespace>/<name>`); `DomainContract.claim_vocabulary()` unchanged (facets are not claim vocabulary; succession rules do not reach them — D §12's facet-versioning question stays open and is not decided here).

- [ ] **Step 1: Write the failing tests**

Append to `python/tests/test_domain_contract.py`:

```python
class TestDomainFacets:
    def test_the_testing_contract_declares_two_namespaced_facets(self, parse, testing_document):
        contract = parse(testing_document)
        assert set(contract.facets) == {"testing/axis", "testing/annotation"}
        assert contract.facets["testing/axis"].attaches_to == ("dataset",)
        assert contract.facets["testing/annotation"].attaches_to == ("dataset", "proposition")

    def test_a_domain_declaring_kinds_or_relations_is_refused(self, parse, testing_document):
        for section in ("kinds", "relations"):
            doc = copy.deepcopy(testing_document)
            doc[section] = {}
            with pytest.raises(MalformedContract, match=f"a domain contract declares no {section}"):
                parse(doc)

    def test_a_domain_facet_requires_attaches_to_and_fields(self, parse, testing_document):
        doc = copy.deepcopy(testing_document)
        del doc["facets"]["axis"]["attaches_to"]
        with pytest.raises(MalformedContract, match="attaches_to"):
            parse(doc)

    def test_a_domain_facet_may_not_declare_a_shape(self, parse, testing_document):
        doc = copy.deepcopy(testing_document)
        doc["facets"]["axis"]["shape"] = "schema"
        with pytest.raises(MalformedContract, match="unknown key"):
            parse(doc)

    def test_facets_enter_the_content_identity(self, parse, testing_document):
        before = parse(testing_document).content_identity
        doc = copy.deepcopy(testing_document)
        doc["facets"]["axis"]["fields"]["axis"]["required"] = False
        assert parse(doc).content_identity != before

    def test_a_contract_without_facets_still_loads(self, parse, testing_document):
        doc = copy.deepcopy(testing_document)
        del doc["facets"]
        assert parse(doc).facets == {}
```

- [ ] **Step 2: Run to verify failure**

Run: `cd python && uv run --frozen pytest tests/test_domain_contract.py -q -k DomainFacets`
Expected: FAIL (`AttributeError: facets` / KeyError on the fixture).

- [ ] **Step 3: Add the fixture facets**

Append to `fixtures/contracts/testing.yaml`:

```yaml

# Two fixture facets (facet-contracts design §3.2). They exist to exercise the
# namespaced grammar, D2's asymmetry, D8's composition and F8's registry check.
# Neither means anything: `annotation` attaches to two kinds only so that a
# kind-scoped `attaches_to` is tested at all.
facets:
  axis:
    attaches_to: [dataset]
    fields:
      axis:       { type: string, required: true }
      vocabulary: { type: ref,    required: false, kinds: [dataset] }
  annotation:
    attaches_to: [dataset, proposition]
    fields:
      note:  { type: string,  required: true }
      count: { type: integer, required: false }
      final: { type: boolean, required: false }
```

- [ ] **Step 4: Extend the domain parser**

In `domain.py`: add `facets: Mapping[str, FacetDecl]` to `DomainContract` and `_parsed`; in `parse_domain_contract` change `_fields(root, _CONTRACT_FIELDS, frozenset({"description"}), source)` to permit `facets` as optional, and **before** that call add:

```python
    for section in ("kinds", "relations"):
        if section in root:
            raise MalformedContract(
                f"{source}: a domain contract declares no {section}; a kernel kind or relation signature is the "
                "base contract's, and a domain contributes facets to kinds that already exist (D §3.3, D8) — refused"
            )
```

and after the operators loop:

```python
    facets = parse_facet_declarations(root.get("facets", {}), where=f"{source}: facets", namespace=namespace)
```

passing `facets=facets` to `_parsed`. Import `FacetDecl, parse_facet_declarations` from `beliefs.contract.facets`.

- [ ] **Step 5: TypeScript**

In `parseDomainContract`: refuse `kinds` and `relations` before `exactFields` with `MalformedContract(\`${source}: a domain contract declares no ${section}; refused\`)`; permit `facets` as optional; parse with `parseFacetDeclarations("facets" in document ? document.facets : {}, \`${source}.facets\`, namespace)` so an explicit `null` is refused by `mapping` exactly as Python's `_mapping(None)` refuses it; add `readonly facets: DeclarationTable<FacetDecl>` to `DomainContract`. Append to `ts/tests/declarations.test.ts`:

```ts
describe("a domain contract's facets (design §3.3)", () => {
  const TESTING = readFileSync(new URL("fixtures/contracts/testing.yaml", REPO_ROOT), "utf-8");
  const base = parseBaseContract(SHIPPED, "contracts/science/CONTRACT.yaml");
  it("namespaces facet keys and carries attaches_to", () => {
    const domain = parseDomainContract(TESTING, "fixtures/contracts/testing.yaml", base);
    expect(Object.keys(domain.facets).sort()).toEqual(["testing/annotation", "testing/axis"]);
    expect(domain.facets["testing/axis"].attachesTo).toEqual(["dataset"]);
  });
  it("refuses kinds and relations in a domain contract", () => {
    expect(() => parseDomainContract(`${TESTING}\nkinds: {}\n`, "<bad>", base)).toThrow(/declares no kinds/);
    expect(() => parseDomainContract(`${TESTING}\nrelations: {}\n`, "<bad>", base)).toThrow(/declares no relations/);
  });
});
```

- [ ] **Step 6: Run, lint, commit**

`cd python && uv run --frozen pytest tests/test_domain_contract.py tests/test_profile.py tests/test_parity_fixture.py -q` → pass (the testing contract's content identity moves; `fixtures/claim-identity-v1.json` pins `profile_compiled_identity`, which does **not** move yet because facets are not in the projection until Task 5 — if `test_parity_fixture.py` fails on a content-identity assertion, that assertion is over the compiled identity only; confirm before touching the fixture). `cd ts && npm test && npm run typecheck && npm run check` → pass. Full Python gates → pass.

```bash
git add fixtures/contracts/testing.yaml python/src/beliefs/contract/domain.py python/tests/test_domain_contract.py ts/src/contract.ts ts/tests/declarations.test.ts
git commit -m "feat(contract): namespaced facet declarations in domain contracts; kinds and relations refused"
```

---

### Task 4: The practice loader

**Files:**
- Create: `python/src/beliefs/contract/practice.py`, `python/tests/test_practice.py`
- Modify: `python/src/beliefs/contract/__init__.py`

**Interfaces:**
- Produces: `Practice(name, version, description, guidance: tuple[str, ...])`; `parse_practice(document, *, source) -> Practice`; `load_practice(path) -> Practice`. `compile_profile` takes no practice (D9 by construction).

- [ ] **Step 1: Write the failing tests**

```python
# python/tests/test_practice.py
"""D9: a practice carries procedure and no vocabulary (design §3.6)."""

import inspect

import pytest

from beliefs.contract.practice import Practice, parse_practice
from beliefs.errors import MalformedContract
from beliefs.profile import compile_profile

GOOD = {"practice": "causal-modeling", "version": 1, "description": "How we do it", "guidance": ["docs/practices/causal.md"]}


def test_a_practice_parses_to_its_four_fields():
    assert parse_practice(GOOD, source="<t>") == Practice("causal-modeling", 1, "How we do it", ("docs/practices/causal.md",))


@pytest.mark.parametrize("section", ["vocabulary", "sorts", "dimensions", "operators", "facets", "kinds"])
def test_a_practice_declaring_vocabulary_or_schema_is_refused(section):
    with pytest.raises(MalformedContract, match=f"{section}.*practice"):
        parse_practice({**GOOD, section: {}}, source="<t>")


def test_unknown_keys_and_a_missing_field_are_refused():
    with pytest.raises(MalformedContract, match="unknown"):
        parse_practice({**GOOD, "skills": []}, source="<t>")
    with pytest.raises(MalformedContract, match="missing"):
        parse_practice({k: v for k, v in GOOD.items() if k != "guidance"}, source="<t>")


def test_compile_profile_accepts_no_practice():
    assert "practice" not in inspect.signature(compile_profile).parameters
```

- [ ] **Step 2: Run to verify failure** — `cd python && uv run --frozen pytest tests/test_practice.py -q` → ModuleNotFoundError.

- [ ] **Step 3: Write the loader**

```python
# python/src/beliefs/contract/practice.py
"""`PRACTICE.yaml` — procedure without vocabulary (D §3.5, design §3.6).

A practice is refused the moment it tries to bind a vocabulary or declare a
schema: the distinguishing test is mechanical, and a practice that acquires a
binding was a domain. Nothing consumes a practice at compile, which is what
makes D9's "contributes nothing to the registry" true by construction rather
than by check.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from beliefs.errors import MalformedContract

__all__ = ["Practice", "load_practice", "parse_practice"]

_FIELDS = frozenset({"practice", "version", "description", "guidance"})
_REFUSED = ("vocabulary", "sorts", "dimensions", "operators", "facets", "kinds", "relations")


@dataclass(frozen=True)
class Practice:
    name: str
    version: int
    description: str
    guidance: tuple[str, ...]


def parse_practice(document: object, *, source: str) -> Practice:
    if not isinstance(document, dict):
        raise MalformedContract(f"{source}: a practice is a mapping")
    for section in _REFUSED:
        if section in document:
            raise MalformedContract(
                f"{source}: {section} is not a practice's to declare; a practice carries procedure only (D §3.5)"
            )
    unknown = sorted(set(document) - _FIELDS)
    if unknown:
        raise MalformedContract(f"{source}: unknown field(s) {', '.join(unknown)}")
    missing = sorted(_FIELDS - set(document))
    if missing:
        raise MalformedContract(f"{source}: missing field(s) {', '.join(missing)}")
    name, version, description, guidance = (document[k] for k in ("practice", "version", "description", "guidance"))
    if not isinstance(name, str) or not name:
        raise MalformedContract(f"{source}: practice is a non-empty string")
    if isinstance(version, bool) or not isinstance(version, int) or version < 1:
        raise MalformedContract(f"{source}: version is a positive integer")
    if not isinstance(description, str):
        raise MalformedContract(f"{source}: description is a string")
    if not isinstance(guidance, list) or not all(isinstance(entry, str) and entry for entry in guidance):
        raise MalformedContract(f"{source}: guidance is a list of paths")
    return Practice(name, version, description, tuple(guidance))


def load_practice(path: Path) -> Practice:
    from beliefs.contract.document import load_document

    return parse_practice(load_document(path, source=str(path)), source=str(path))
```

Export `Practice`, `parse_practice`, `load_practice` from `beliefs/contract/__init__.py`.

- [ ] **Step 4: Run, lint, commit**

`cd python && uv run --frozen pytest tests/test_practice.py -q && uv run --frozen ruff check . && uv run --frozen pyright`

```bash
git add python/src/beliefs/contract/practice.py python/src/beliefs/contract/__init__.py python/tests/test_practice.py
git commit -m "feat(contract): the practice loader refuses vocabulary and schema"
```

---
### Task 5: The compile — compiled kinds and facets, a private registry, the validators, the projection

**Files:**
- Create: `python/src/beliefs/facets.py`, `python/tests/test_facet_validation.py`
- Modify: `python/src/beliefs/profile.py`, `python/tests/test_profile.py`, `fixtures/claim-identity-v1.json` (regenerated), `ts/src/profile.ts`, `ts/tests/declarations.test.ts`

**Interfaces:**
- Produces (Python): `CompiledKind(name, role, domain, facets: Mapping[str, FacetUse], covered: tuple[str, ...], contract)`; `CompiledFacet(key, shape, attaches_to: frozenset[str], fields: Mapping[str, FieldDecl], contract)`; `ProfileSpec.kinds`, `.facets`, `.relations` (all read-only, nested mappings included); `ProfileSpec.facets_of(kind)`; `ProfileSpec.validate_document(node) -> None` raising `nodes.core.errors.UnknownKindError | FacetError`; `ProfileSpec.document_violations(node) -> tuple[Violation, ...]`; **no public registry**; `validate_payload(facet, payload, *, where) -> None` raising `FacetPayloadRefused`.
- Consumed by Tasks 6–11.

- [ ] **Step 1: Write the failing tests**

```python
# python/tests/test_facet_validation.py
"""§3.4's grammar at validation time, and §4.1's compiled products — immutable, one registry, private."""

import copy
from dataclasses import FrozenInstanceError

import pytest
from nodes.core.errors import FacetError, UnknownKindError
from nodes.core.node import Node
from nodes.core.registry import Registry

import beliefs.profile as profile_module
from beliefs.contract import domain, parse_base_contract
from beliefs.contract.base import FacetUse
from beliefs.contract.document import load_document
from beliefs.errors import FacetPayloadRefused, ProfileError
from beliefs.facets import validate_payload
from beliefs.profile import compile_profile


@pytest.fixture()
def testing(base_contract, testing_document):
    return domain.parse_domain_contract(testing_document, source="<t>", base=base_contract, predecessor=None)


@pytest.fixture()
def profile(base_contract, testing):
    return compile_profile(base_contract, [testing])


def reparse(document, source="<t>"):
    return parse_base_contract(document, source=source)


class TestCompiledProducts:
    def test_kinds_and_facets_are_compiled(self, profile):
        assert profile.kinds["dataset"].covered == ("dataset", "empirical-observation", "lineage-basis")
        assert profile.kinds["dataset"].role == "world"
        assert profile.kinds["instrument-certification"].domain is None
        assert profile.kinds["discussion"].role == "prose" and profile.kinds["discussion"].domain is None
        assert profile.facets["empirical-observation"].shape == "schema"
        assert profile.facets["testing/axis"].attaches_to == frozenset({"dataset"})

    def test_nothing_compiled_is_mutable(self, profile):
        with pytest.raises(TypeError):
            profile.kinds["x"] = None  # type: ignore[index]
        with pytest.raises(TypeError):
            profile.kinds["dataset"].facets["x"] = FacetUse(True, True)  # type: ignore[index]
        with pytest.raises((TypeError, AttributeError)):
            profile.facets["empirical-observation"].fields.pop("locator")  # type: ignore[attr-defined]
        with pytest.raises(AttributeError):
            profile.kinds["dataset"].facets["dataset"].required = False  # type: ignore[misc]
        assert "registry" not in dir(profile)  # no public registry, no public route to `register`
        with pytest.raises(FrozenInstanceError):
            profile._registry = Registry()  # type: ignore[misc]  # the private slot is frozen with the rest

    def test_facets_of_a_kind_include_attached_domain_facets(self, profile):
        assert set(profile.facets_of("dataset")) == {
            "dataset", "empirical-observation", "lineage-basis", "display", "testing/axis", "testing/annotation"
        }
        assert set(profile.facets_of("run")) == {"run", "run-closure"}
        assert set(profile.facets_of("discussion")) == {"display"}

    def test_one_kindspec_per_kind_registered_once_and_validation_is_exposed_without_the_registry(
        self, base_contract, testing, monkeypatch
    ):
        calls: list[str] = []
        original = Registry.register

        def counting(self, spec):
            calls.append(spec.name)
            return original(self, spec)

        monkeypatch.setattr(Registry, "register", counting)
        compiled = compile_profile(base_contract, [testing])
        assert sorted(calls) == sorted(compiled.kinds) and len(calls) == len(set(calls))
        compiled.validate_document(Node(id="dataset:x", kind="dataset", title="x", facets={"dataset": {"resources": []}}))
        with pytest.raises(FacetError, match="unexpected"):
            compiled.validate_document(Node(id="dataset:y", kind="dataset", title="y", facets={"dataset": {}, "biology/gene-axis": {}}))
        with pytest.raises(UnknownKindError):
            compiled.validate_document(Node(id="divergence:z", kind="divergence", title="z", facets={}))
        codes = [v.code for v in compiled.document_violations(Node(id="dataset:w", kind="dataset", title="w", facets={}))]
        assert codes == ["facet-missing"]

    def test_a_domain_facet_attaching_to_an_undeclared_or_prose_kind_refuses_the_compile(self, base_contract, testing_document):
        for kind in ("divergence", "discussion"):
            doc = copy.deepcopy(testing_document)
            doc["facets"]["axis"]["attaches_to"] = [kind]
            contract = domain.parse_domain_contract(doc, source="<t>", base=base_contract, predecessor=None)
            with pytest.raises(ProfileError, match=kind):
                compile_profile(base_contract, [contract])

    def test_a_ref_field_naming_an_undeclared_kind_refuses_the_compile(self, base_contract, testing_document):
        doc = copy.deepcopy(testing_document)
        doc["facets"]["axis"]["fields"]["vocabulary"]["kinds"] = ["ontology"]
        contract = domain.parse_domain_contract(doc, source="<t>", base=base_contract, predecessor=None)
        with pytest.raises(ProfileError, match="ontology"):
            compile_profile(base_contract, [contract])

    def test_every_profile_has_an_identity_and_undomained_kinds_encode_without_null(self, base_contract):
        compiled = compile_profile(base_contract, [])
        assert len(compiled.compiled_identity) == 64
        projection = compiled.projection()["kinds"]["instrument-certification"]
        assert "domain" not in projection and projection["role"] == "world"

    def test_the_compiled_identity_moves_on_every_behavioural_declaration(self, base_contract, testing_document):
        base_identity = compile_profile(base_contract, []).compiled_identity
        contract = domain.parse_domain_contract(testing_document, source="<t>", base=base_contract, predecessor=None)
        with_facets = compile_profile(base_contract, [contract]).compiled_identity
        assert with_facets != base_identity
        doc = copy.deepcopy(testing_document)
        doc["facets"]["axis"]["attaches_to"] = ["dataset", "proposition"]
        moved = domain.parse_domain_contract(doc, source="<t>", base=base_contract, predecessor=None)
        assert compile_profile(base_contract, [moved]).compiled_identity != with_facets
        doc = copy.deepcopy(testing_document)
        doc["facets"]["axis"]["description"] = "editorial"
        editorial = domain.parse_domain_contract(doc, source="<t>", base=base_contract, predecessor=None)
        assert compile_profile(base_contract, [editorial]).compiled_identity == with_facets

    def test_reordering_declarations_moves_neither_identity_nor_coverage(self, base_contract_path):
        doc = load_document(base_contract_path, source="<t>")
        reordered = copy.deepcopy(doc)
        reordered["kinds"] = dict(reversed(list(doc["kinds"].items())))
        reordered["kinds"]["dataset"]["facets"] = dict(reversed(list(doc["kinds"]["dataset"]["facets"].items())))
        reordered["facets"] = dict(reversed(list(doc["facets"].items())))
        reordered["relations"] = dict(reversed(list(doc["relations"].items())))
        a = compile_profile(reparse(doc, "<a>"), [])
        b = compile_profile(reparse(reordered, "<b>"), [])
        assert a.compiled_identity == b.compiled_identity
        assert a.kinds["dataset"].covered == b.kinds["dataset"].covered

    def test_moving_a_relation_between_groups_moves_the_compiled_identity(self, base_contract_path):
        doc = load_document(base_contract_path, source="<t>")
        moved = copy.deepcopy(doc)
        moved["relations"]["grounded-in"]["group"] = "lifecycle"
        assert compile_profile(reparse(doc, "<a>"), []).compiled_identity != compile_profile(reparse(moved, "<b>"), []).compiled_identity


class TestPayloadValidation:
    def facet(self, profile):
        return profile.facets["empirical-observation"]

    def test_a_valid_declaration_validates(self, profile):
        validate_payload(self.facet(profile), {"locator": "accession:GSE179929", "attested_by": "keith"}, where="d")

    @pytest.mark.parametrize(
        "payload, reason",
        [
            ({"boundary": "acquisition", "source": "x", "asserted_by": "y"}, "unknown key"),
            ({"attested_by": "keith"}, "missing required field 'locator'"),
            ({"locator": "ftp:x", "attested_by": "keith"}, "scheme 'ftp'"),
            ({"locator": "accession:", "attested_by": "keith"}, "empty"),
            ({"locator": 7, "attested_by": "keith"}, "locator"),
            ({"locator": "url:x", "attested_by": ""}, "attested_by"),
            ({"locator": "url:x", "attested_by": "k", "retrieval": "dataset:z"}, "kind 'dataset'"),
            ({"locator": "url:x", "attested_by": "k", "retrieval": "act-report:"}, "empty"),
            ({"locator": "url:x", "attested_by": "k", "retrieval": None}, "null"),
            ({"locator": "url:x", "attested_by": {"name": "k"}}, "nested"),
        ],
    )
    def test_every_malformation_is_refused_with_its_reason(self, profile, payload, reason):
        with pytest.raises(FacetPayloadRefused, match=reason):
            validate_payload(self.facet(profile), payload, where="d")

    def test_integer_and_boolean_keep_their_types(self, profile):
        annotation = profile.facets["testing/annotation"]
        validate_payload(annotation, {"note": "n", "count": 3, "final": False}, where="d")
        with pytest.raises(FacetPayloadRefused, match="integer"):
            validate_payload(annotation, {"note": "n", "count": True}, where="d")
        with pytest.raises(FacetPayloadRefused, match="boolean"):
            validate_payload(annotation, {"note": "n", "final": 1}, where="d")

    def test_a_reader_shaped_facet_validates_nothing_here(self, profile):
        validate_payload(profile.facets["dataset"], {"anything": "goes"}, where="d")


def test_profile_imports_nothing_from_stored():
    assert "stored" not in profile_module.__dict__
```

- [ ] **Step 2: Run to verify failure** — `cd python && uv run --frozen pytest tests/test_facet_validation.py -q` → ModuleNotFoundError / AttributeError.

- [ ] **Step 3: Add the error**

In `python/src/beliefs/errors.py`, directly after `class ValidationRefused(WriteRefused)`:

```python
class FacetPayloadRefused(ValidationRefused):
    """A schema-shaped facet's payload is outside its declared grammar (facet-contracts
    design §3.4, §5.7): an unknown key, a missing required field, a null, a nested
    value, a wrong type, an unknown scheme or kind, an empty remainder. Refused at
    every write seam and reported by the check as `facet-payload-malformed`."""
```

- [ ] **Step 4: Write the validator**

```python
# python/src/beliefs/facets.py
"""Payload validation for schema-shaped facets (facet-contracts design §3.4, §4.1).

Shape only: a `ref` is checked for its kind prefix and a non-empty local, never
for resolution, which is the writer's seam rule (§5.2); an `actor` is checked
non-empty, never for identity, which is the writer's binding rule (§5.3).
"""

from __future__ import annotations

from collections.abc import Mapping

from beliefs.errors import FacetPayloadRefused
from beliefs.profile import CompiledFacet

__all__ = ["validate_payload"]


def _refuse(where: str, key: str, reason: str) -> FacetPayloadRefused:
    return FacetPayloadRefused(f"{where}: facet {key!r} payload malformed: {reason}")


def validate_payload(facet: CompiledFacet, payload: object, *, where: str) -> None:
    if facet.shape != "schema":
        return
    if not isinstance(payload, Mapping):
        raise _refuse(where, facet.key, "a facet payload is a mapping")
    unknown = sorted(set(payload) - set(facet.fields))
    if unknown:
        raise _refuse(where, facet.key, f"unknown key(s) {', '.join(map(repr, unknown))}; refused, never ignored")
    for name, field in facet.fields.items():
        if name not in payload:
            if field.required:
                raise _refuse(where, facet.key, f"missing required field {name!r}")
            continue
        value = payload[name]
        if value is None:
            raise _refuse(where, facet.key, f"{name!r} is null; a field is present or absent, never null")
        if isinstance(value, (Mapping, list, tuple)):
            raise _refuse(where, facet.key, f"{name!r} is nested; the grammar admits no nesting")
        if field.type == "integer":
            if isinstance(value, bool) or not isinstance(value, int):
                raise _refuse(where, facet.key, f"{name!r} must be an integer")
            continue
        if field.type == "boolean":
            if not isinstance(value, bool):
                raise _refuse(where, facet.key, f"{name!r} must be a boolean")
            continue
        if not isinstance(value, str) or not value:
            raise _refuse(where, facet.key, f"{name!r} must be a non-empty string ({field.type})")
        if field.type in ("string", "actor"):
            continue
        prefix, separator, rest = value.partition(":")
        if separator != ":" or not rest:
            what = "kind" if field.type == "ref" else "scheme"
            raise _refuse(where, facet.key, f"{name!r} must be `<{what}>:<rest>` with a non-empty remainder")
        if field.type == "ref" and prefix not in field.kinds:
            raise _refuse(where, facet.key, f"{name!r} names kind {prefix!r}; declared kinds are {', '.join(field.kinds)}")
        if field.type == "locator" and prefix not in field.schemes:
            raise _refuse(where, facet.key, f"{name!r} uses scheme {prefix!r}; declared schemes are {', '.join(field.schemes)}")
```

- [ ] **Step 5: Extend `profile.py`**

Add, after `CompiledOperator` (imports: `from nodes.core.registry import KindSpec, Registry, Violation`; `from nodes.core.node import Node`; `from beliefs.contract.base import FacetUse, RelationDecl`; `from beliefs.contract.facets import FieldDecl`):

```python
@dataclass(frozen=True)
class CompiledKind:
    name: str
    role: str  # "world" | "prose" — coordination kinds carry "coordination"
    domain: str | None
    facets: Mapping[str, FacetUse]
    covered: tuple[str, ...]
    """The covered facets **sorted by key by code point** — coverage order is never
    the authored order, so one contract identity yields one stamp (§4.2)."""
    contract: str

    def projection(self) -> dict[str, object]:
        # No null anywhere: `science.identity.v1` refuses it. An undomained kind
        # simply carries no `domain` key; its role says what it is.
        projection: dict[str, object] = {
            "role": self.role,
            "facets": {k: {"required": u.required, "covered": u.covered} for k, u in sorted(self.facets.items())},
        }
        if self.domain is not None:
            projection["domain"] = self.domain
        return projection


@dataclass(frozen=True)
class CompiledFacet:
    key: str
    shape: str
    attaches_to: frozenset[str]
    fields: Mapping[str, FieldDecl]
    contract: str

    def projection(self) -> dict[str, object]:
        return {
            "shape": self.shape,
            "fields": {name: field.projection() for name, field in sorted(self.fields.items())},
            "attaches_to": sorted(self.attaches_to),
        }
```

`ProfileSpec` gains `kinds: Mapping[str, CompiledKind]`, `facets: Mapping[str, CompiledFacet]`, `relations: Mapping[str, RelationDecl]` and a private `_registry: Registry` (built in `compile_profile`, never returned), plus:

```python
    def facets_of(self, kind: str) -> Mapping[str, CompiledFacet]:
        """Every facet the kind may carry: its own declared facets and every domain
        facet attaching to it."""
        if kind not in self.kinds:
            raise ProfileError(f"kind {kind!r} is not in the compiled inventory")
        own = {key: self.facets[key] for key in self.kinds[kind].facets}
        attached = {key: f for key, f in self.facets.items() if kind in f.attaches_to}
        return MappingProxyType({**own, **attached})

    def validate_document(self, node: Node) -> None:
        """Kind registered and facet keys declared (G5, D4), raising `nodes`' own
        `UnknownKindError` / `FacetError`. The registry stays private: exposing it
        would let a caller register or mutate a kind without moving a pin."""
        object.__getattribute__(self, "_registry").validate(node)

    def document_violations(self, node: Node) -> tuple[Violation, ...]:
        return tuple(object.__getattribute__(self, "_registry").check(node))
```

In `compile_profile`:

- Replace the `stored`-based coordination check with `set(coordination.query_kinds) - {n for n, k in base.kinds.items() if k.role == "world"}` and `set(coordination.query_relations) - {n for n, r in base.relations.items() if r.group == "world"}`; delete `from beliefs import stored`.
- Build `kinds`: for each `base.kinds` entry `CompiledKind(name, decl.role, decl.domain, MappingProxyType(dict(decl.facets)), tuple(sorted(k for k, u in decl.facets.items() if u.covered)), "science")`; for each coordination kind `CompiledKind(name, "coordination", None, MappingProxyType({"coordination": FacetUse(True, False)}), (), "coordination")`.
- Build `facets`: base facets with `contract="science"`, `attaches_to=frozenset()`, `fields=MappingProxyType(dict(decl.fields))`; then for each activated domain (sorted namespaces) each facet: `DuplicateContribution` if the key is already present; `ProfileError(f"{key}: attaches_to names {kind!r}, not a world kind")` for any kind whose compiled role is not `"world"` (prose and coordination kinds carry no domain facets; an undeclared kind is refused by the same test); `ProfileError(f"{key}: field {name!r} names kind {k!r}, not in the compiled inventory")` for any `ref` field's kind absent from `kinds`; the same `ref` resolution over base schema facets.
- Build the registry once: for each compiled kind `Registry.register(KindSpec(name=name, required_facets={required keys}, optional_facets={optional keys} | {domain facets attaching} | ({"semantic-identity"} if domain is not None else set())))`. Pydantic `KindSpec` instances are held only by the private registry; nothing hands them out.
- Pass `kinds=MappingProxyType(dict(kinds))`, `facets=MappingProxyType(dict(facets))`, `relations=MappingProxyType(dict(base.relations))`, `_registry=registry`.
- In `_projection`, add `"kinds"`, `"relations"`, `"facets"` entries keyed by name (each value the declaration's `projection()`); `projection()` passes `self.kinds`, `self.relations`, `self.facets`.

In `base.py` (Task 2's `KindDecl`), make the parsed `facets` mapping a `MappingProxyType` and give `KindDecl.projection()` the same no-null shape (`role`, conditional `domain`, `facets`). `FacetDecl.fields` likewise wrapped at parse.

- [ ] **Step 6: TypeScript compile carries the tables**

In `ts/src/profile.ts` add `readonly kinds: DeclarationTable<KindDecl>; readonly relations: DeclarationTable<RelationDecl>; readonly facets: DeclarationTable<FacetDecl>;` to `ProfileSpec` and in `compileProfile` build `facets` from `base.facets` then each domain's, throwing `ProfileError` on a duplicate key, on an `attachesTo` kind whose role is not `world`, and on a `ref` field whose kind is absent from `base.kinds`. Append to `ts/tests/declarations.test.ts`:

```ts
describe("compileProfile enforces the declaration constraints (design §7.2)", () => {
  const base = parseBaseContract(SHIPPED, "contracts/science/CONTRACT.yaml");
  const TESTING = readFileSync(new URL("fixtures/contracts/testing.yaml", REPO_ROOT), "utf-8");
  it("carries kinds, relations and facets", () => {
    const profile = compileProfile(base, [parseDomainContract(TESTING, "<t>", base)]);
    expect(Object.keys(profile.kinds).length).toBeGreaterThanOrEqual(16);
    expect(profile.facets["testing/axis"].attachesTo).toEqual(["dataset"]);
  });
  it("refuses a domain facet attaching to an undeclared or prose kind", () => {
    for (const kind of ["divergence", "discussion"]) {
      const bad = TESTING.replace("attaches_to: [dataset]\n    fields:\n      axis:", `attaches_to: [${kind}]\n    fields:\n      axis:`);
      expect(() => compileProfile(base, [parseDomainContract(bad, "<bad>", base)])).toThrow(new RegExp(kind));
    }
  });
});
```

- [ ] **Step 7: Regenerate the claim fixture and re-pin the compiled identity**

Run `cd python && uv run --frozen python tools/generate_claim_identity_fixture.py` and `git diff fixtures/claim-identity-v1.json`: the only changed value must be `profile_compiled_identity`. If any row's `canonical_bytes` or `digest` changed, stop — the projection touched `π_claim`, which it must not. Update `test_profile.py::test_no_coordination_contract_preserves_the_pre_cut_compiled_identity`'s pinned hex to the value printed by `uv run --frozen python -c "from beliefs.contract import load_base_contract; from beliefs.profile import compile_profile; print(compile_profile(load_base_contract('../contracts/science/CONTRACT.yaml'), []).compiled_identity)"` and rename it `..._preserves_the_cut_20_compiled_identity`.

- [ ] **Step 8: Run everything, lint, commit**

`cd python && uv run --frozen pytest && uv run --frozen ruff check . && uv run --frozen pyright`; `cd ts && npm test && npm run typecheck && npm run check`.

```bash
git add python/src/beliefs/facets.py python/src/beliefs/profile.py python/src/beliefs/contract/base.py python/src/beliefs/errors.py python/tests/test_facet_validation.py python/tests/test_profile.py fixtures/claim-identity-v1.json ts/src/profile.ts ts/tests/declarations.test.ts
git commit -m "feat(profile): compile kinds, facets and relations; a private registry registered once; payload validators"
```

---

### Task 6: The shipped base profile and `stored.py`'s views

**Files:**
- Create: `python/src/beliefs/contracts/science/CONTRACT.yaml` (a byte-identical copy), `python/tests/test_shipped_base.py`
- Modify: `python/src/beliefs/profile.py` (`shipped_base`, `shipped_base_contract`), `python/src/beliefs/stored.py:160-232`, `python/tests/test_stored.py`

**Interfaces:**
- Produces: `profile.shipped_base_contract() -> BaseContract` and `profile.shipped_base() -> ProfileSpec`, both `functools.cache`d; `stored.WORLD_KINDS`, `WORLD_RELATIONS`, `SEMANTIC_DOMAINS`, `COVERED_FACETS` unchanged in name, type and membership, derived; `stored.PROSE_KINDS`.

- [ ] **Step 1: Write the failing tests**

```python
# python/tests/test_shipped_base.py
"""§4.2: one shipped base, byte-identical to the normative file, and stored.py's tables as views over it."""

from importlib import resources

from beliefs import stored
from beliefs.profile import shipped_base, shipped_base_contract


def test_the_packaged_copy_is_byte_identical_to_the_normative_file(base_contract_path):
    packaged = resources.files("beliefs").joinpath("contracts/science/CONTRACT.yaml").read_bytes()
    assert packaged == base_contract_path.read_bytes()


def test_the_shipped_base_is_compiled_once():
    assert shipped_base() is shipped_base()
    assert shipped_base().base_contract_identity == shipped_base_contract().content_identity


def test_stored_tables_are_views_over_the_shipped_base():
    world = {n: k for n, k in shipped_base().kinds.items() if k.role == "world"}
    assert stored.WORLD_KINDS == tuple(world)
    assert stored.PROSE_KINDS == tuple(n for n, k in shipped_base().kinds.items() if k.role == "prose")
    assert stored.SEMANTIC_DOMAINS == {n: k.domain for n, k in world.items() if k.domain is not None}
    assert stored.COVERED_FACETS == {n: k.covered for n, k in world.items() if k.domain is not None}
    assert stored.WORLD_RELATIONS == tuple(n for n, r in shipped_base().relations.items() if r.group == "world")


def test_membership_is_exactly_what_it_was_before_this_slice():
    assert set(stored.WORLD_KINDS) == {
        "proposition", "source-assertion", "assessment", "analysis-spec", "run", "verification", "dataset",
        "source", "holdings-observation", "retraction", "instrument-certification", "coreference-attestation",
        "act-report",
    }
    assert set(stored.PROSE_KINDS) == {"interpretation", "discussion", "story"}
    assert set(stored.WORLD_RELATIONS) == {
        "assesses", "observes", "reads", "transforms", "produces", "produced_by", "executes", "targets",
        "verifies", "member_of", "grounded-in",
    }
    assert stored.COVERED_FACETS["dataset"] == ("dataset", "empirical-observation", "lineage-basis")
    assert stored.COVERED_FACETS["run"] == ("run", "run-closure")
    assert "instrument-certification" not in stored.SEMANTIC_DOMAINS
    assert "discussion" not in stored.SEMANTIC_DOMAINS


def test_the_import_graph_is_acyclic():
    import importlib
    import sys

    for name in [m for m in list(sys.modules) if m.startswith("beliefs")]:
        del sys.modules[name]
    importlib.import_module("beliefs.stored")
```

- [ ] **Step 2: Run to verify failure** — `cd python && uv run --frozen pytest tests/test_shipped_base.py -q` → fails on `shipped_base` import.

- [ ] **Step 3: Ship the copy and the accessor**

`mkdir -p python/src/beliefs/contracts/science && cp contracts/science/CONTRACT.yaml python/src/beliefs/contracts/science/CONTRACT.yaml`. Hatchling packages every file under `src/beliefs`. In `profile.py`:

```python
from functools import cache
from importlib import resources


@cache
def shipped_base_contract() -> BaseContract:
    """The base contract this implementation carries, parsed from package data.
    A corpus pinning another base identity is refused, never reinterpreted
    (§4.2) — the same shape as `TAG_ENCODING`."""
    from beliefs.contract.base import parse_base_contract
    from beliefs.contract.document import parse_document

    source = "beliefs/contracts/science/CONTRACT.yaml"
    text = resources.files("beliefs").joinpath("contracts/science/CONTRACT.yaml").read_text(encoding="utf-8")
    return parse_base_contract(parse_document(text, source=source), source=source)


@cache
def shipped_base() -> ProfileSpec:
    return compile_profile(shipped_base_contract(), [])
```

Add both to `__all__`.

- [ ] **Step 4: Derive `stored.py`'s tables**

Replace the literal `WORLD_KINDS`, `WORLD_RELATIONS`, `SEMANTIC_DOMAINS` and `COVERED_FACETS` definitions with:

```python
from types import MappingProxyType

from beliefs.profile import shipped_base

_SHIPPED = shipped_base()
_WORLD = {name: kind for name, kind in _SHIPPED.kinds.items() if kind.role == "world"}

WORLD_KINDS: tuple[str, ...] = tuple(_WORLD)
"""The kernel's world kinds, in the base contract's authored order (facet-contracts §4.2)."""

PROSE_KINDS: tuple[str, ...] = tuple(name for name, kind in _SHIPPED.kinds.items() if kind.role == "prose")
"""Kernel §4.4's belief-inert notes: hand-authored, undomained, unstamped, never in a closure."""

WORLD_RELATIONS: tuple[str, ...] = tuple(name for name, decl in _SHIPPED.relations.items() if decl.group == "world")
"""The `world` relation group only; lifecycle relations are adapter-minted (§3.1)."""

SEMANTIC_DOMAINS: Mapping[str, str] = MappingProxyType(
    {name: kind.domain for name, kind in _WORLD.items() if kind.domain is not None}
)

COVERED_FACETS: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {name: kind.covered for name, kind in _WORLD.items() if kind.domain is not None}
)
"""Which facets the semantic hash governs, per kind, sorted by key (§4.2)."""
```

The authored order of `kinds:` in `CONTRACT.yaml` must equal the old `WORLD_KINDS` tuple order for the world kinds (Task 2 wrote it in that order; the prose kinds follow). Update the module docstring's "named in code" sentence to "declared by the base contract and compiled (facet-contracts design §4.2)". Add `PROSE_KINDS` to `__all__`.

- [ ] **Step 5: Run, lint, commit**

`cd python && uv run --frozen pytest && uv run --frozen ruff check . && uv run --frozen pyright`

```bash
git add python/src/beliefs/contracts python/src/beliefs/profile.py python/src/beliefs/stored.py python/tests/test_shipped_base.py
git commit -m "feat(profile): the shipped base profile; stored.py's per-kind tables become views over it"
```

---

### Task 7: The writer and the port hold a profile — real pins, the recheck under every lock, registry and payload validation, provenance mode

**Files:**
- Create: `python/tests/profiles.py`, `python/tests/fixtures/biology-fixture.yaml`, `python/tests/test_profile_agreement.py`, `python/tests/test_pin_recheck_inventory.py`
- Modify: `python/src/beliefs/corpus.py`, `python/src/beliefs/root.py` (`DurableOperationPort`, `open_corpus`), `python/src/beliefs/runrecord.py` (`OperationPort` protocol gains `profile`), `python/src/beliefs/relocation.py`, `python/tests/fixtures_cut6.py`, `python/tests/coordination_fixtures.py`, `python/tests/test_corpus_write.py` (`OperationRecorder`), every test/tool constructing `CorpusWriter`, a port, or calling `open_corpus`; every test fixture writing an `empirical_observation` payload or a `memo` node

**Interfaces:**
- Produces: `CorpusWriter(root, executor_factory, *, authority, profile: ProfileSpec, operation_port=None, coordination_resolver=None)`; `DurableOperationPort(root, *, backend, storage, metadata_root, authority, profile)`; `OperationPort.profile`; `open_corpus(root, *, authority, profile, coordination_resolver=None)`; module-level `require_pins_agree(root: Path, profile: ProfileSpec) -> None`; `CorpusWriter._refuse(node, *, document_validated=False, view=None, provenance=False)`, `_preflight_add_locked(node, *, provenance=False)`, `_add_locked(node, *, provenance=False)`, `_preflight_replace_locked(node, *, provenance=False)`, `_replace_locked(node, *, provenance=False)`; `_refuse_facets(node, *, view=None, provenance=False)` steps 1–2 here (3–5 in Task 8, which reads `provenance` as "do not bind the actor"); test helpers `profiles.BASE`, `WITH_BIOLOGY`, `WITH_BIOLOGY_OTHER`, `pins_for`.

- [ ] **Step 1: Write the fixture domain contract and the profiles module**

```yaml
# python/tests/fixtures/biology-fixture.yaml
# A TEST FIXTURE in the `biology` namespace, not a domain. The relocation and
# world tests pin a `biology` contract identity and need two distinct ones for
# their pin-disagreement arms; `profiles.py` parses this document twice with
# different descriptions. Shipping `domains/biology/DOMAIN.yaml` is the second
# slice's design act (D limitation 5), and nothing here binds a real vocabulary.
contract: biology
version: 1
lineage: genesis
description: fixture
sorts:
  gene:
    vocabulary: { namespace: EX, release: "2026-01-01" }
dimensions: {}
operators:
  affects:
    arity: 2
    arg_sorts: [gene, gene]
    sign_apt: true
    layers: [causal]
    dimensions: []
facets:
  gene-axis:
    attaches_to: [dataset]
    fields:
      axis: { type: string, required: true }
```

```python
# python/tests/profiles.py
"""Compiled profiles the tests write under, from real contracts (facet-contracts §5.1).

Every manifest pins the shipped base; a writer refuses a profile whose base
identity is not the shipped one. The `biology` fixture exists twice so the
relocation tests can pin two disagreeing identities for one namespace.
"""

from __future__ import annotations

from pathlib import Path

from beliefs.consulted import CorpusPins
from beliefs.contract import parse_domain_contract
from beliefs.contract.document import load_document
from beliefs.profile import ProfileSpec, compile_profile, shipped_base, shipped_base_contract

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "biology-fixture.yaml"


def biology(description: str):
    document = load_document(FIXTURE, source=str(FIXTURE))
    assert isinstance(document, dict)
    document["description"] = description
    return parse_domain_contract(document, source=f"{FIXTURE}#{description}", base=shipped_base_contract(), predecessor=None)


BASE: ProfileSpec = shipped_base()
WITH_BIOLOGY: ProfileSpec = compile_profile(shipped_base_contract(), [biology("fixture")])
WITH_BIOLOGY_OTHER: ProfileSpec = compile_profile(shipped_base_contract(), [biology("fixture, second variant")])


def pins_for(profile: ProfileSpec) -> CorpusPins:
    return CorpusPins(
        science_contract="science:" + profile.base_contract_identity,
        domains={ns: f"{ns}:{identity}" for ns, identity in profile.activated_contracts.items()},
    )
```

Rewrite `python/tests/fixtures_cut6.py`:

```python
from profiles import WITH_BIOLOGY, WITH_BIOLOGY_OTHER, pins_for

PINS = pins_for(WITH_BIOLOGY)
OTHER_PINS = pins_for(WITH_BIOLOGY_OTHER)
SCIENCE_ID = PINS.science_contract
BIOLOGY_ID = PINS.domains["biology"]
OTHER_BIOLOGY_ID = OTHER_PINS.domains["biology"]


def manifest_document(corpus_id: str = "1" * 32) -> str:
    return (
        "manifest_version: 2\n"
        f"corpus_id: {corpus_id}\n"
        "profile:\n"
        f"  science_contract: {SCIENCE_ID}\n"
        "  domains:\n"
        f"    biology: {BIOLOGY_ID}\n"
    )
```

Every test that builds a second, disagreeing biology identity by hand (`grep -rn '"biology:" +\|biology:.*\* 64' python/tests`) switches to `OTHER_BIOLOGY_ID` / `OTHER_PINS` and builds that writer with `WITH_BIOLOGY_OTHER`.

- [ ] **Step 2: Write the failing tests**

```python
# python/tests/test_profile_agreement.py
"""§5.1 and F5: writer and port hold a profile; every write path rechecks the pins under its lock."""

import pytest
from authority import FULL
from nodes.core.node import Node
from nodes.core.write_plan import DefaultExecutor
from profiles import BASE, WITH_BIOLOGY, WITH_BIOLOGY_OTHER, pins_for
from test_corpus_write import OperationRecorder

from beliefs import stored
from beliefs.corpus import CorpusWriter, ReadView
from beliefs.errors import ContractMismatch, FacetPayloadRefused, ValidationRefused
from nodes.core.corpus import Corpus

PINNED = [{"name": "m", "digest": "sha256:" + "1" * 64}]
IMPORT = {"observer": "o", "instrument": "i", "opened_at": "2026-09-05T00:00:00Z", "closed_at": "2026-09-05T00:00:01Z"}


def _writer(root, profile=BASE):
    port = OperationRecorder(root, authority=FULL, profile=profile)
    writer = CorpusWriter(root, DefaultExecutor, authority=FULL, profile=profile, operation_port=port)
    writer.adopt_manifest(profile=pins_for(profile))
    return writer, port


def _rewrite_biology_pin(root):
    text = (root / "corpus.yaml").read_text()
    (root / "corpus.yaml").write_text(text.replace(pins_for(WITH_BIOLOGY).domains["biology"], pins_for(WITH_BIOLOGY_OTHER).domains["biology"]))


def test_a_writer_requires_a_compiled_profile_and_a_port_agreeing_with_it(tmp_path):
    with pytest.raises(TypeError):
        CorpusWriter(tmp_path, DefaultExecutor, authority=FULL)  # type: ignore[call-arg]
    port = OperationRecorder(tmp_path, authority=FULL, profile=WITH_BIOLOGY)
    with pytest.raises(ValueError, match="profile"):
        CorpusWriter(tmp_path, DefaultExecutor, authority=FULL, profile=BASE, operation_port=port)
    assert WITH_BIOLOGY.compiled_identity == WITH_BIOLOGY_OTHER.compiled_identity  # description-only variants
    with pytest.raises(ValueError, match="profile"):
        CorpusWriter(tmp_path, DefaultExecutor, authority=FULL, profile=WITH_BIOLOGY_OTHER, operation_port=port)


def test_adopt_manifest_writes_only_the_held_profiles_pins(tmp_path):
    writer = CorpusWriter(tmp_path, DefaultExecutor, authority=FULL, profile=BASE)
    with pytest.raises(ContractMismatch):
        writer.adopt_manifest(profile=pins_for(WITH_BIOLOGY))


@pytest.mark.parametrize("path", ["add", "delete", "revise", "import", "intent", "port-execute", "port-fulfilling"])
def test_every_write_path_rechecks_the_pins_after_a_manifest_change(tmp_path, path):
    writer, port = _writer(tmp_path, WITH_BIOLOGY)
    p = writer.add(stored.proposition_node("p", title="p", claim={"operator": "affects"}))
    before = sorted(str(x.relative_to(tmp_path)) for x in tmp_path.rglob("*") if x.is_file())
    _rewrite_biology_pin(tmp_path)
    q = stored.proposition_node("q", title="q", claim={"operator": "affects"})
    with pytest.raises(ContractMismatch, match="manifest pins"):
        if path == "add":
            writer.add(q)
        elif path == "delete":
            writer.delete(p.id)
        elif path == "revise":
            writer.revise(p.model_copy(update={"title": "renamed"}))
        elif path == "import":
            writer.import_bundle([q], **IMPORT)
        elif path == "intent":
            port.append_intent(b"intent")
        elif path == "port-execute":
            port.execute(())
        else:
            port.execute_fulfilling((), "ab" * 32)
    after = sorted(str(x.relative_to(tmp_path)) for x in tmp_path.rglob("*") if x.is_file())
    assert before == after and port.intents == [] and port.executed == [] and port.fulfilling == []


def test_relocation_rechecks_at_the_destination(tmp_path):
    from fixtures_cut6 import PINS  # noqa: F401 - the relocation fixtures adopt biology pins
    from test_relocation import _writer as relocation_writer

    from beliefs import relocation

    source = relocation_writer(tmp_path / "s", domains=PINS.domains)
    destination = relocation_writer(tmp_path / "d", domains=PINS.domains)
    node = source.add(stored.proposition_node("p", title="p", claim={"operator": "affects"}))
    _rewrite_biology_pin(tmp_path / "d")
    with pytest.raises(ContractMismatch):
        relocation.move((source, node.id), destination, observer="o", instrument="i", opened_at="2026-09-05T00:00:00Z", closed_at="2026-09-05T00:00:01Z")
    assert source.read_view.holds(node.id) and not destination.read_view.holds(node.id)


def test_a_validated_read_refuses_a_corpus_pinning_another_base_but_iteration_does_not(tmp_path):
    writer, _ = _writer(tmp_path)
    node = writer.add(stored.proposition_node("p", title="p", claim={"operator": "affects"}))
    text = (tmp_path / "corpus.yaml").read_text()
    (tmp_path / "corpus.yaml").write_text(text.replace(pins_for(BASE).science_contract, "science:" + "f" * 64))
    view = ReadView(Corpus(tmp_path))  # construction never checks
    assert [n.id for n in view.iter_stored()] == [node.id]
    with pytest.raises(ContractMismatch, match="science_contract"):
        view.get(node.id)


def test_an_unknown_kind_and_an_undeclared_facet_key_are_refused_at_add(tmp_path):
    writer, _ = _writer(tmp_path)
    with pytest.raises(ValidationRefused, match="kind-unknown"):
        writer.add(Node(id="divergence:d", kind="divergence", title="d", facets={}))
    node = stored.proposition_node("p", title="p", claim={"operator": "affects"})
    node.facets["biology/gene-axis"] = {"axis": "rows"}
    with pytest.raises(ValidationRefused, match="facet-unexpected"):
        writer.add(stored.stamp_semantic_identity(node))


def test_a_prose_kind_is_admitted_with_display_only(tmp_path):
    writer, _ = _writer(tmp_path)
    writer.add(Node(id="discussion:d", kind="discussion", title="d", facets={"display": {"display_statement": "x"}}))
    with pytest.raises(ValidationRefused, match="facet-unexpected"):
        writer.add(Node(id="discussion:e", kind="discussion", title="e", facets={"dataset": {}}))


def test_a_malformed_schema_facet_is_refused_at_add(tmp_path):
    writer, _ = _writer(tmp_path)
    node = stored.dataset_node(
        "d", title="d", resources=PINNED,
        empirical_observation={"boundary": "acquisition", "source": "dataset:gse", "asserted_by": "driver"},
    )
    with pytest.raises(FacetPayloadRefused, match="unknown key"):
        writer.add(node)
```

```python
# python/tests/test_pin_recheck_inventory.py
"""F5's static arm: every function in corpus.py and relocation.py that reaches a
corpus effect calls `_require_pins_agree` (or the module-level `require_pins_agree`)
earlier in its own body, and every port method that writes calls it under its lock."""

import ast
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src" / "beliefs"
EFFECTS = {"add", "execute", "_execute", "_execute_fulfilling"}  # `self._corpus.add`, `executor.execute`, port internals


def _effect_calls(fn: ast.FunctionDef) -> list[ast.Call]:
    return [
        node for node in ast.walk(fn)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in EFFECTS
        and not (isinstance(node.func.value, ast.Name) and node.func.value.id in {"findings", "calls", "seen_ids", "seen_uids", "seen_paths", "read"})
    ]


def _rechecks(fn: ast.FunctionDef) -> bool:
    return any(
        isinstance(node, ast.Call) and isinstance(node.func, (ast.Attribute, ast.Name))
        and (getattr(node.func, "attr", None) or getattr(node.func, "id", None)) in {"_require_pins_agree", "require_pins_agree"}
        for node in ast.walk(fn)
    )


def test_every_effecting_function_rechecks_the_pins():
    offenders = []
    for module in ("corpus.py", "relocation.py", "root.py"):
        tree = ast.parse((SRC / module).read_text(encoding="utf-8"))
        for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
            if fn.name in {"require_pins_agree", "_require_pins_agree", "adopt_manifest", "_reconstruct"}:
                continue
            if _effect_calls(fn) and not _rechecks(fn):
                offenders.append(f"{module}:{fn.name}")
    assert offenders == [], "effects without a pin recheck: " + ", ".join(offenders)
```

(Run the inventory once against the finished code and tune the exclusion set in `_effect_calls` to the read-only `.add` calls on sets and lists it names; a new exclusion needs a comment saying what it is. `adopt_manifest` is excluded because it writes the pins it then agrees with.)

- [ ] **Step 3: Run to verify failure** — `cd python && uv run --frozen pytest tests/test_profile_agreement.py tests/test_pin_recheck_inventory.py -q` → TypeErrors and the inventory's offender list.

- [ ] **Step 4: The port and the writer**

`runrecord.py`'s `OperationPort` protocol gains `@property def profile(self) -> ProfileSpec: ...`. `DurableOperationPort.__init__` gains `profile: ProfileSpec` (keyword, required), stores `self._profile`, exposes `profile`, and every one of `append_intent`, `execute`, `execute_fulfilling` (and Task 10's guarded form) calls `require_pins_agree(self.root, self._profile)` as the first statement inside its `with _operation_lock_for(self.root):`. `OperationRecorder` in `test_corpus_write.py` gains `profile=BASE` and the same first-statement call in each method (it has no lock; call it first). `open_corpus` gains `profile` and passes it to both.

In `corpus.py`:

1. Module-level:

```python
def require_pins_agree(root: Path, profile: ProfileSpec) -> None:
    """§5.1: under the operation lock, before any effect. A manifest, when
    present, pins exactly this profile's base and activated contracts. A
    manifest that cannot be loaded is a mismatch: the writer cannot know what
    it would be agreeing with."""
    manifest_path = Path(root) / "corpus.yaml"
    if not manifest_path.exists():
        return
    from beliefs.world import load_manifest

    try:
        pins = load_manifest(Path(root)).profile
    except ManifestMalformed as caught:
        raise ContractMismatch(f"{manifest_path}: manifest pins cannot be read: {caught}") from caught
    expected = CorpusPins(
        "science:" + profile.base_contract_identity,
        {ns: f"{ns}:{identity}" for ns, identity in profile.activated_contracts.items()},
    )
    if pins != expected:
        raise ContractMismatch(
            f"{manifest_path}: manifest pins do not match the profile "
            f"(manifest {pins.science_contract[:20]}…, {sorted(pins.domains)}; "
            f"profile {expected.science_contract[:20]}…, {sorted(expected.domains)})"
        )
```

2. `CorpusWriter.__init__` gains `profile: ProfileSpec` (keyword-only, required, after `authority`): refuse a non-`ProfileSpec` (`TypeError`), a base identity other than `shipped_base().base_contract_identity` (`ContractMismatch`), an `operation_port` whose profile differs in **any** of `base_contract_identity`, `dict(activated_contracts)` or `compiled_identity` (`ValueError("the operation port holds another profile than this writer")`) — the two biology fixtures share a compiled identity and differ only in their activated pins, which is exactly the disagreement a compiled-identity comparison would miss, and a mounted coordination profile for this root whose `activated_contracts` differ (`ContractMismatch`). `self._profile = profile`; `@property def profile`. `_require_pins_agree(self)` calls `require_pins_agree(self._corpus.store.root, self._profile)`.

3. Place `self._require_pins_agree()` as the **first statement after the lock is taken** in every lock-held method or helper that reaches an effect: `add`, `delete`, `revise`, `supersede`, `retract`, `import_bundle`, the coordination write methods, `_add_locked`, `_replace_locked`, `_delete_locked`, `_publish_operation_report`, `_append_operation_intent`; in `relocation.py`, at the top of `move` and `consolidate` bodies once both locks are held (both writers). `adopt_manifest` instead compares the requested pins with `pins_for`-shaped expected pins of the held profile and refuses `ContractMismatch("adopt_manifest writes only the held profile's pins")`. The static inventory test holds the set closed.

4. `ReadView.get`: before `_validated`, call `self._require_base_pin()`:

```python
    def _require_base_pin(self) -> None:
        """§7.1: a validated read judges nothing under a base the corpus does not
        pin. Construction never checks (the check would refuse the audit that
        reports the mismatch, §5.5); iteration never checks."""
        path = self._corpus.store.root / "corpus.yaml"
        try:
            stamp = (path.stat().st_mtime_ns, path.stat().st_size)
        except FileNotFoundError:
            return
        if stamp == self._base_pin_stamp:
            return
        from beliefs.world import load_manifest

        pinned = load_manifest(self._corpus.store.root).profile.science_contract
        shipped = "science:" + shipped_base().base_contract_identity
        if pinned != shipped:
            raise ContractMismatch(f"{path}: science_contract {pinned[:20]}… is not the shipped base {shipped[:20]}…; refused, never reinterpreted")
        self._base_pin_stamp = stamp
```

(`self._base_pin_stamp = None` in `__init__`; a malformed manifest raises `ManifestMalformed` here, which is the right refusal for a validated read.)

5. `_refuse_facets`, steps 1–2:

```python
    def _refuse_facets(self, node: Node, *, view: ReadView | _ImportView | None = None, provenance: bool = False) -> None:
        """§5.2: registry validation, then payload validation. Steps 3–5 arrive
        with `beliefs.acquisition` (Task 8); `provenance=True` means the record
        arrived from elsewhere and its attestation is kept as written."""
        try:
            self._profile.validate_document(node)
        except UnknownKindError as caught:
            raise ValidationRefused(f"{node.id}: kind-unknown: {caught}") from caught
        except FacetError as caught:
            code = "facet-missing" if "missing" in str(caught) else "facet-unexpected"
            raise ValidationRefused(f"{node.id}: {code}: {caught}") from caught
        for key, payload in node.facets.items():
            facet = self._profile.facets.get(key)
            if facet is not None:
                validate_payload(facet, payload, where=node.id)
```

Thread `provenance` through `_refuse(node, *, document_validated=False, view=None, provenance=False)` → `self._refuse_facets(node, view=view, provenance=provenance)` placed after `_refuse_invalid` and before `_refuse_governed_stamp`; `_preflight_add_locked(node, *, provenance=False)` and `_add_locked(node, *, provenance=False)` pass it to `_refuse`; `_preflight_replace_locked(node, *, provenance=False)` and `_replace_locked(node, *, provenance=False)` likewise. `import_bundle` calls `self._refuse(record, document_validated=True, view=import_view, provenance=True)`; `relocation.py` passes `provenance=True` at its four call sites (`_preflight_add_locked`, `_add_locked`, `_preflight_replace_locked`, `_replace_locked`).

- [ ] **Step 4b: The holdings act path**

Holdings acts reach the corpus chain through `StoreActSeam.append_intent` and `publish_fulfilling`, whose root implementations (`_store_append_intent`, `_store_publish_fulfilling`) hold neither a profile nor the operation lock. Three changes:

- `holdings/seam.py`: `StoreActSeam` gains `corpus_lock: Callable[[Path], ContextManager[None]]`; `root.py`'s `_HOLDINGS_SEAM` supplies `_world_lock`-style `_operation_lock_for` (the same object the writer and the port take, so a holdings act and a corpus write contend for one lock); the tests' seam fixture supplies a no-op context manager.
- `holdings/boundary.py`: `ActContext` gains `profile: ProfileSpec` (required; `__post_init__` refuses a non-`ProfileSpec`). `_append` becomes

```python
def _append(ctx: ActContext, location: StoreLocator, kind: str) -> tuple[str, str]:
    ctx.authority.require("holdings", ("holdings-observation",))
    token = secrets.token_hex(16)
    with ctx.seam.corpus_lock(ctx.observer_root):
        require_pins_agree(ctx.observer_root, ctx.profile)
        intent = ctx.seam.append_intent(
            ctx.observer_root, intent_payload(location=location, act_kind=kind, event_token=token, actor=ctx.actor)
        )
    return token, intent
```

  and every publication goes through one guarded helper — `_publish` **and** `write`, which today publishes through its own `ctx.seam.publish_fulfilling` call:

```python
def _publish_record(ctx: ActContext, record: HoldingsObservation, intent: str) -> PublishedObservation:
    """The one publication route for a holdings observation: pins rechecked under
    the corpus lock, then the record published fulfilling its intent."""
    node = stored.holdings_observation_node(record)
    plan = (CreateOp(f"holdings-observation/{record.identity()}.md", node_to_markdown(node).encode("utf-8")),)
    with ctx.seam.corpus_lock(ctx.observer_root):
        require_pins_agree(ctx.observer_root, ctx.profile)
        ctx.seam.publish_fulfilling(ctx.observer_root, plan, intent)
    return PublishedObservation(record)
```

  `_publish` builds its record as now and returns `_publish_record(ctx, record, intent)`; `write` builds its record exactly as now — `expected=expected` preserved — and returns `_publish_record(ctx, record, intent)` in place of its inline `publish_fulfilling` call. After the change `grep -n "publish_fulfilling" holdings/boundary.py` shows exactly one call, inside `_publish_record`; the static inventory holds that. `recheck`'s inline `append_intent` call moves into `_append`. `require_pins_agree` is imported from `beliefs.corpus` inside the functions (the boundary already imports from `root` lazily for the same cycle reason).
- The static inventory (`test_pin_recheck_inventory.py`) adds `holdings/boundary.py` to its modules and `append_intent`, `publish_fulfilling` to `EFFECTS`.

Every `ActContext(...)` construction (`grep -rn "ActContext(" python/tests python/tools`) gains `profile=` (tests: `BASE` or the corpus's profile; the reproduction driver: `profile()`). Add to `test_profile_agreement.py`:

```python
def test_a_holdings_act_rechecks_before_its_intent_and_before_its_publication(tmp_path, holdings_context):
    """`holdings_context(root, profile)` is the fixture the holdings tests build their ActContext with; find it
    by `grep -n "ActContext(" python/tests/test_holdings_capture.py` and give it a `profile` parameter."""
    from beliefs.holdings.boundary import write
    from beliefs.holdings.records import StoreLocator

    writer, _ = _writer(tmp_path / "corpus", WITH_BIOLOGY)
    ctx = holdings_context(tmp_path, WITH_BIOLOGY)
    _rewrite_biology_pin(tmp_path / "corpus")
    with pytest.raises(ContractMismatch):
        write(ctx, StoreLocator(ctx_store_id(ctx), "f.txt"), b"bytes")
    assert not any((tmp_path / "corpus").rglob("holdings-observation/*"))
```

(`ctx_store_id` reads the store genesis through `ctx.seam.store_genesis` as `_bind` does; write it as a two-line helper beside the test.) The refusal before the intent leaves the chain untouched. The after-intent arm injects the change **before the publication lock is taken** — a rewrite inside `publish_fulfilling` would run after the recheck and prove nothing — by wrapping the seam's `store_write` so the manifest is rewritten as the store write returns:

```python
def test_a_manifest_change_after_the_intent_leaves_it_unfulfilled(tmp_path, holdings_context):
    from dataclasses import replace

    from beliefs.holdings.boundary import write
    from beliefs.holdings.records import StoreLocator

    _writer(tmp_path / "corpus", WITH_BIOLOGY)
    ctx = holdings_context(tmp_path, WITH_BIOLOGY)
    inner = ctx.seam.store_write

    def store_write_then_rewrite(store_root, relative_path, content):
        outcome = inner(store_root, relative_path, content)
        _rewrite_biology_pin(tmp_path / "corpus")  # between the intent and the publication lock
        return outcome

    ctx = replace(ctx, seam=replace(ctx.seam, store_write=store_write_then_rewrite))
    with pytest.raises(ContractMismatch):
        write(ctx, StoreLocator(ctx_store_id(ctx), "f.txt"), b"bytes")
    assert len(ctx.seam.intents) == 1 and ctx.seam.published == []  # the intent stands unfulfilled
    assert not any((tmp_path / "corpus").rglob("holdings-observation/*"))
```

(`ctx.seam.intents` and `.published` are the recording lists the tests' seam fixture keeps; if it names them differently, use its names. Both `ActContext` and `StoreActSeam` are frozen dataclasses, so `dataclasses.replace` builds the wrapped copies.) The same arm runs durably in Task 15 over `holdings_seam()` with the store write wrapped the same way.

- [ ] **Step 5: Migrate the fixtures the new refusals reach, in this commit**

- Every `empirical_observation={"boundary": ...}` in `python/tests` and `python/tests/acceptance` (`grep -rn 'empirical_observation={"boundary"'`) becomes `empirical_observation={"locator": "instrument:fixture", "attested_by": ACTOR}` where `ACTOR` is the writing authority's actor (`authority.ACTOR` under `FULL`; the durable fixture's actor under acceptance). Records that are imported rather than added may keep any attester.
- Every `memo` node (`grep -rln 'kind="memo"\|memo(' python/tests`) becomes the declared prose kind `discussion`: `kind="discussion"`, ids `discussion:<slug>`, and any `memo(` helper renamed `discussion(`. The `nodes` store path derives from the kind, so no other change follows.
- `coordination_fixtures.py` compiles its profile with `compile_profile(shipped_base_contract(), [], coordination=...)` and pins with `pins_for`.

- [ ] **Step 6: Thread the profile through every construction site**

`grep -rn "CorpusWriter(\|open_corpus(\|DurableOperationPort(\|OperationRecorder(" python/tests python/tools python/src --include='*.py'`. The rule: a writer whose corpus adopts `PINS` uses `profile=WITH_BIOLOGY`; one built to disagree uses `WITH_BIOLOGY_OTHER`; every other writer uses `BASE`; a writer over a coordination-mounted root uses that mount's profile; the port a writer takes is built with the same profile. `test_relocation._writer(root, *, domains=None, operation_port=True, authority=FULL)` derives the profile from `domains` (`BIOLOGY_ID` → `WITH_BIOLOGY`, `OTHER_BIOLOGY_ID` → `WITH_BIOLOGY_OTHER`, else `BASE`) and adopts `pins_for(profile)`; drop its `science=` parameter. `python/tools/reproduction/world.py::open_writer` passes `profile=profile()` from `reproduction.vocabulary`, whose `base()` returns `shipped_base_contract()`. Then `cd python && uv run --frozen pytest -x -q 2>&1 | tail -20` until green.

- [ ] **Step 7: Run everything, lint, commit**

`cd python && uv run --frozen pytest && uv run --frozen ruff check . && uv run --frozen pyright`

```bash
git add -A python/src python/tests python/tools
git commit -m "feat(corpus): writer and port hold a compiled profile, recheck pins under every lock, and validate kinds, keys and payloads"
```

---

### Task 8: The acquisition-boundary validity predicate, the bearer invariant, attestation and retrieval

**Files:**
- Create: `python/src/beliefs/acquisition.py`, `python/tests/test_acquisition.py`, `python/tests/test_facet_seams.py`
- Modify: `python/src/beliefs/corpus.py` (`_refuse_facets` steps 3–5, `ReadView.producers`, `_ImportView.producers`, `eligibility_refusal`), `python/src/beliefs/errors.py`, `python/tests/test_read_side.py`, `python/tests/conftest.py`

**Interfaces:**
- Produces: `ReadView.producers(dataset_id, *, aliases=()) -> tuple[str, ...]` and `_ImportView.producers(...)`, both over the **resulting** index (existing relations, arriving records, deprecated-id aliases, dangling edges included); `acquisition.validity_refusal(view, node, profile) -> str | None`; `acquisition.bearer_refusal(view, node) -> str | None`; `AcquisitionBoundaryRefused(WriteRefused)`; `eligibility_refusal(view, node, profile)`.

- [ ] **Step 1: Write the failing unit tests**

```python
# python/tests/test_acquisition.py
"""§2 items 1 and 14: the predicate and the invariant, over an in-memory view."""

from nodes.core.relations import Relation
from profiles import BASE

from beliefs import stored
from beliefs.acquisition import bearer_refusal, validity_refusal

from test_read_side import seed  # the module's raw-write seeding helper (Task 11 gives it manifest arguments)

PINNED = [{"name": "m", "digest": "sha256:" + "1" * 64}]
GOOD = {"locator": "accession:GSE1", "attested_by": "test-actor"}


def acquired(slug="d", **facet):
    return stored.dataset_node(slug, title=slug, resources=PINNED, empirical_observation={**GOOD, **facet})


def test_a_valid_declaration_on_an_unproduced_dataset_passes(tmp_path):
    node = acquired()
    assert validity_refusal(seed(tmp_path, node), node, BASE) is None


def test_absence_and_invalidity_are_distinct_reasons(tmp_path):
    plain = stored.dataset_node("p", title="p", resources=PINNED)
    assert validity_refusal(seed(tmp_path, plain), plain, BASE) == "no-empirical-observation-facet"
    bad = stored.dataset_node("b", title="b", resources=PINNED, empirical_observation={"boundary": "x"})
    assert str(validity_refusal(seed(tmp_path / "b", bad), bad, BASE)).startswith("facet-payload-malformed:")


def test_a_lineage_basis_disqualifies_even_with_a_valid_facet(tmp_path):
    node = stored.dataset_node("d", title="d", resources=PINNED, empirical_observation=GOOD, basis={"tag": "single", "routes": []})
    assert validity_refusal(seed(tmp_path, node), node, BASE) == "facet-bearer-produced: the dataset carries a lineage basis"


def test_a_producer_disqualifies(tmp_path):
    node = acquired()
    run = stored.run_node("r", title="r", spec="analysis-spec:s", produces=[node.id])
    assert validity_refusal(seed(tmp_path, node, run), node, BASE) == f"facet-bearer-produced: produced by {run.id}"


def test_a_dangling_producer_edge_counts_before_the_dataset_exists(tmp_path):
    run = stored.run_node("r", title="r", spec="analysis-spec:s", produces=["dataset:d"])
    view = seed(tmp_path, run)
    assert view.producers("dataset:d") == (run.id,)
    assert bearer_refusal(view, acquired()) == f"dataset:d: carries the empirical-observation facet and is produced by {run.id}"


def test_an_alias_reaches_the_producer(tmp_path):
    node = acquired()
    node.deprecated_ids = ["dataset:old"]
    run = stored.run_node("r", title="r", spec="analysis-spec:s", produces=["dataset:old"])
    view = seed(tmp_path, stored.stamp_semantic_identity(node), run)
    assert view.producers(node.id, aliases=("dataset:old",)) == (run.id,)


def test_an_unresolved_retrieval_disqualifies(tmp_path):
    node = acquired(retrieval="act-report:" + "0" * 64)
    assert validity_refusal(seed(tmp_path, node), node, BASE) == "facet-retrieval-unresolved: act-report:" + "0" * 64


def test_the_bearer_invariant_reads_the_edge_whatever_its_carrier(tmp_path):
    node = acquired()
    view = seed(tmp_path, node)
    source = stored.source_node("s", title="s", identifiers={"doi": "10.1/x"})
    source.relations.append(Relation(source=source.id, predicate="produces", target=node.id))
    assert bearer_refusal(view, source) == f"{source.id}: produces {node.id}, which carries the empirical-observation facet"


def test_a_new_dataset_producing_itself_is_refused_by_id_and_by_alias(tmp_path):
    view = seed(tmp_path)  # an empty corpus: nothing resolves, so only the candidate can answer
    for target in ("dataset:d", "dataset:old"):
        node = acquired()
        node.deprecated_ids = ["dataset:old"]
        node.relations.append(Relation(source=node.id, predicate="produces", target=target))
        assert bearer_refusal(view, node) == "dataset:d: carries the empirical-observation facet and produces itself"
```

- [ ] **Step 2: Write the failing seam tests**

```python
# python/tests/test_facet_seams.py
"""F1–F3, F7 at the write seams: add, import, relocation. Revision is Task 9's."""

import pytest
from authority import ACTOR, FULL
from nodes.core.relations import Relation
from nodes.core.write_plan import DefaultExecutor
from profiles import BASE, pins_for
from test_corpus_write import OperationRecorder

from beliefs import stored
from beliefs.corpus import CorpusWriter
from beliefs.errors import AcquisitionBoundaryRefused, ActorMismatch, FacetPayloadRefused, ImportRefused
from beliefs.permit import Authority, WritePermit

PINNED = [{"name": "m", "digest": "sha256:" + "1" * 64}]
ALICE = Authority(WritePermit.full(), "alice")
IMPORT = {"observer": "o", "instrument": "i", "opened_at": "2026-09-05T00:00:00Z", "closed_at": "2026-09-05T00:00:01Z"}


def writer(root, authority=FULL):
    port = OperationRecorder(root, authority=authority, profile=BASE)
    w = CorpusWriter(root, DefaultExecutor, authority=authority, profile=BASE, operation_port=port)
    if not (root / "corpus.yaml").exists():
        w.adopt_manifest(profile=pins_for(BASE))
    return w


def acquired(slug, attester, **extra):
    return stored.dataset_node(slug, title=slug, resources=PINNED, empirical_observation={"locator": "url:x", "attested_by": attester, **extra})


def producing(slug, target):
    return stored.run_node(slug, title=slug, spec="analysis-spec:s", produces=[target])


class TestF1:
    def test_the_reproductions_authored_payload_is_refused(self, tmp_path):
        node = stored.dataset_node("d", title="d", resources=PINNED, empirical_observation={"boundary": "acquisition", "source": "dataset:gse", "asserted_by": "driver"})
        with pytest.raises(FacetPayloadRefused, match="unknown key"):
            writer(tmp_path).add(node)

    def test_import_wraps_the_refusal_naming_the_member(self, tmp_path):
        node = stored.dataset_node("d", title="d", resources=PINNED, empirical_observation={"locator": "ftp:x", "attested_by": "k"})
        with pytest.raises(ImportRefused) as caught:
            writer(tmp_path).import_bundle([node], **IMPORT)
        assert caught.value.member == node.id
        assert isinstance(caught.value.__cause__, FacetPayloadRefused)


class TestF2:
    def test_facet_dataset_then_producing_run_refuses_the_run(self, tmp_path):
        w = writer(tmp_path)
        d = w.add(acquired("d", ACTOR))
        with pytest.raises(AcquisitionBoundaryRefused, match="carries the empirical-observation facet"):
            w.add(producing("r", d.id))

    def test_producing_run_then_facet_dataset_refuses_the_dataset(self, tmp_path):
        w = writer(tmp_path)
        w.add(producing("r", "dataset:d"))
        with pytest.raises(AcquisitionBoundaryRefused, match="is produced by run:r"):
            w.add(acquired("d", ACTOR))

    def test_a_non_run_carrier_of_produces_is_refused_on_the_edge(self, tmp_path):
        w = writer(tmp_path)
        d = w.add(acquired("d", ACTOR))
        source = stored.source_node("s", title="s", identifiers={"doi": "10.1/x"})
        source.relations.append(Relation(source=source.id, predicate="produces", target=d.id))
        with pytest.raises(AcquisitionBoundaryRefused):
            w.add(stored.stamp_semantic_identity(source))

    @pytest.mark.parametrize("order", ["dataset-first", "run-first"])
    def test_a_bundle_holding_both_is_refused_in_either_order(self, tmp_path, order):
        d, r = acquired("d", "importer"), producing("r", "dataset:d")
        members = [d, r] if order == "dataset-first" else [r, d]
        with pytest.raises(ImportRefused) as caught:
            writer(tmp_path).import_bundle(members, **IMPORT)
        assert isinstance(caught.value.__cause__, AcquisitionBoundaryRefused)
        assert not (tmp_path / "dataset").exists() and not (tmp_path / "run").exists()


class TestF3:
    def test_add_binds_the_attester_to_the_authority(self, tmp_path):
        with pytest.raises(ActorMismatch):
            writer(tmp_path, ALICE).add(acquired("d", "bob"))
        writer(tmp_path, ALICE).add(acquired("e", "alice"))

    def test_import_keeps_a_foreign_attester(self, tmp_path):
        w = writer(tmp_path, ALICE)
        w.import_bundle([acquired("d", "carol")], **IMPORT)
        assert w.read_view.get("dataset:d").facets["empirical-observation"]["attested_by"] == "carol"

    def test_relocation_keeps_a_foreign_attester(self, tmp_path):
        from test_relocation import _writer as relocation_writer

        from beliefs import relocation

        source = relocation_writer(tmp_path / "s")
        destination = relocation_writer(tmp_path / "d")
        source.import_bundle([acquired("d", "carol")], **IMPORT)
        relocation.move((source, "dataset:d"), destination, **IMPORT)
        assert destination.read_view.get("dataset:d").facets["empirical-observation"]["attested_by"] == "carol"


class TestF7:
    def test_present_and_unresolved_is_refused(self, tmp_path):
        with pytest.raises(FacetPayloadRefused, match="retrieval-unresolved"):
            writer(tmp_path).add(acquired("d", ACTOR, retrieval="act-report:" + "0" * 64))

    def test_resolving_to_a_non_acquisition_report_is_refused(self, tmp_path):
        w = writer(tmp_path)
        report = w.import_bundle([stored.source_node("s", title="s", identifiers={"doi": "10.1/x"})], **IMPORT)
        with pytest.raises(FacetPayloadRefused, match="not an acquisition"):
            w.add(acquired("d", ACTOR, retrieval=f"act-report:{report.identity()}"))

    def test_resolving_to_an_imported_acquisition_report_is_accepted(self, tmp_path, acquisition_report):
        w = writer(tmp_path)
        node = stored.act_report_node(acquisition_report)
        w.import_bundle([node], **IMPORT)
        w.add(acquired("d", ACTOR, retrieval=node.id))
```

`acquisition_report` is a `conftest.py` fixture: read `python/src/beliefs/report.py`'s `ActReport` and `fixtures_cut3.report`; build one with `operation="acquisition"` and the smallest entries tuple the act-report codec accepts for that operation (copy `fixtures_cut3.report`'s call and change only `operation`; if the codec requires an operation-specific entry, use the entry type `report.py` defines for acquisition).

- [ ] **Step 3: Run both to verify failure** — `cd python && uv run --frozen pytest tests/test_acquisition.py tests/test_facet_seams.py -q` → ModuleNotFoundError.

- [ ] **Step 4: Write `acquisition.py`**

```python
# python/src/beliefs/acquisition.py
"""The acquisition-boundary validity predicate and the bearer invariant
(facet-contracts design §2 items 1 and 14, §5.2).

One function decides whether a dataset's empirical-observation facet stands:
present, payload valid, no producer, no lineage basis, and `retrieval`
resolving to an acquisition report when present. Actor binding is a write
rule and is not here. The write seams, `corpus_check` and `eligibility_refusal`
all call it, so no seam can read a weaker predicate than another.
"""

from __future__ import annotations

from typing import Protocol

from nodes.core.node import Node

from beliefs import stored
from beliefs.errors import FacetPayloadRefused
from beliefs.facets import validate_payload
from beliefs.profile import ProfileSpec

__all__ = ["ProducerView", "bearer_refusal", "validity_refusal"]


class ProducerView(Protocol):
    def holds(self, ref: str) -> bool: ...
    def get(self, ref: str) -> Node: ...
    def resolve(self, ref: str) -> str | None: ...
    def producers(self, dataset: str, *, aliases: tuple[str, ...] = ()) -> tuple[str, ...]: ...


def validity_refusal(view: ProducerView, node: Node, profile: ProfileSpec) -> str | None:
    """`None` when `node` carries a valid acquisition-boundary declaration."""
    payload = node.facets.get(stored.EMPIRICAL_OBSERVATION_FACET)
    if payload is None:
        return "no-empirical-observation-facet"
    try:
        validate_payload(profile.facets[stored.EMPIRICAL_OBSERVATION_FACET], payload, where=node.id)
    except FacetPayloadRefused as refused:
        return f"facet-payload-malformed: {refused}"
    if stored.lineage_basis(node) is not None:
        return "facet-bearer-produced: the dataset carries a lineage basis"
    producers = view.producers(node.id, aliases=tuple(node.deprecated_ids))
    if producers:
        return f"facet-bearer-produced: produced by {', '.join(producers)}"
    retrieval = payload.get("retrieval")
    if retrieval is not None:
        if not view.holds(retrieval):
            return f"facet-retrieval-unresolved: {retrieval}"
        facet = view.get(retrieval).facets.get("act-report")
        if not isinstance(facet, dict) or facet.get("operation") != "acquisition":
            return f"facet-retrieval-unresolved: {retrieval} is not an acquisition report"
    return None


def bearer_refusal(view: ProducerView, node: Node) -> str | None:
    """The resulting-state invariant for one proposed write, either half, keyed
    on the `produces` edge whatever its carrier's kind. The **candidate is part
    of the resulting state**: a facet-bearing dataset whose own `produces`
    names itself (by id, alias, or a target that resolves to it) is refused
    before the view is consulted at all."""
    own_names = {node.id, *node.deprecated_ids}
    bears = node.kind == "dataset" and stored.EMPIRICAL_OBSERVATION_FACET in node.facets
    for relation in node.relations:
        if relation.predicate != stored.PRODUCES:
            continue
        if bears and (relation.target in own_names or view.resolve(relation.target) == node.id):
            return f"{node.id}: carries the empirical-observation facet and produces itself"
        target = view.resolve(relation.target)
        if target is not None and stored.EMPIRICAL_OBSERVATION_FACET in view.get(target).facets:
            return f"{node.id}: produces {target}, which carries the empirical-observation facet"
    if bears:
        if stored.lineage_basis(node) is not None:
            return f"{node.id}: carries the empirical-observation facet and a lineage basis"
        producers = view.producers(node.id, aliases=tuple(node.deprecated_ids))
        if producers:
            return f"{node.id}: carries the empirical-observation facet and is produced by {', '.join(producers)}"
    return None
```

Add to `errors.py` after `EligibilityUnmet`:

```python
class AcquisitionBoundaryRefused(WriteRefused):
    """The bearer invariant (facet-contracts §2 item 1): a dataset may not carry
    the empirical-observation facet and a producer. Refused on whichever half
    arrives second, whatever the carrier's kind."""
```

- [ ] **Step 5: Producer lookups over the resulting index**

`ReadView.inbound` requires the target to resolve, so it cannot serve a dataset being written for the first time or a dangling edge. Both views scan relations instead:

```python
    def producers(self, dataset: str, *, aliases: tuple[str, ...] = ()) -> tuple[str, ...]:
        """Ids of every stored record holding a `produces` edge that names `dataset`
        — by its id, by an alias, or by a target that resolves to it. Dangling
        edges count: a run written before its dataset is still a producer."""
        names = {dataset, *aliases}
        found: set[str] = set()
        for node in self.iter_stored():
            for relation in node.relations:
                if relation.predicate != stored.PRODUCES:
                    continue
                if relation.target in names or self.resolve(relation.target) == dataset:
                    found.add(node.id)
        return tuple(sorted(found))
```

`_ImportView.producers` runs the same scan over `self._local.iter_stored()` followed by `self._records.values()`, resolving through `self._index` (the union index `import_bundle` already builds) — `self.resolve(relation.target)`.

- [ ] **Step 6: Steps 3–5 of `_refuse_facets`, eligibility, and the fixtures**

Extend `_refuse_facets(self, node, *, view=None, provenance=False)` after step 2:

```python
        reading = self._view if view is None else view
        reason = bearer_refusal(reading, node)
        if reason is not None:
            raise AcquisitionBoundaryRefused(reason)
        payload = node.facets.get(stored.EMPIRICAL_OBSERVATION_FACET)
        if isinstance(payload, dict):
            if not provenance and payload.get("attested_by") != self._authority.actor:
                raise ActorMismatch(
                    f"{node.id}: the declaration names attester {payload.get('attested_by')!r}, not the bound "
                    f"{self._authority.actor!r}"
                )
            retrieval = payload.get("retrieval")
            if retrieval is not None:
                if not reading.holds(retrieval):
                    raise FacetPayloadRefused(f"{node.id}: retrieval-unresolved: {retrieval} resolves to no record")
                facet = reading.get(retrieval).facets.get("act-report")
                if not isinstance(facet, dict) or facet.get("operation") != "acquisition":
                    raise FacetPayloadRefused(f"{node.id}: retrieval-unresolved: {retrieval} is not an acquisition report")
```

`provenance` is already threaded through import and relocation (Task 7), so import keeps a foreign attester and relocation keeps it while enforcing everything else at the destination. Change `eligibility_refusal(view, node)` to `eligibility_refusal(view, node, profile)` and replace its loop:

```python
    reasons: list[str] = []
    for dataset_ref in observed:
        if not view.holds(dataset_ref):
            reasons.append(f"{dataset_ref}: unresolved")
            continue
        reason = validity_refusal(view, view.get(dataset_ref), profile)
        if reason is None:
            return None
        reasons.append(f"{dataset_ref}: {reason}")
    return f"no observes input of {run_ref!r} carries a valid empirical-observation facet ({'; '.join(reasons)})"
```

`_refuse_ineligible` passes `self._profile`; `corpus_check`'s call passes `shipped_base()` until Task 11 threads the caller's profile (one-line comment `# Task 11 threads the caller's profile`). Update `test_read_side.py::test_an_observes_input_without_the_empirical_observation_facet_is_reported` to assert the detail names `no-empirical-observation-facet`, and add `test_an_observes_input_with_an_invalid_facet_is_reported_distinctly` asserting `facet-payload-malformed` in the detail.

- [ ] **Step 7: Run, lint, commit**

`cd python && uv run --frozen pytest && uv run --frozen ruff check . && uv run --frozen pyright`

```bash
git add python/src/beliefs/acquisition.py python/src/beliefs/corpus.py python/src/beliefs/errors.py python/tests
git commit -m "feat(corpus): the acquisition-boundary predicate, the bearer invariant over the resulting index, attestation binding and retrieval resolution"
```

---

### Task 9: The dataset revision arm

**Files:**
- Create: `python/tests/test_dataset_revision.py`
- Modify: `python/src/beliefs/corpus.py` (`revise`)

**Interfaces:**
- Produces: `CorpusWriter.revise(node)` resolving the current record first, requiring the permit on the **current kind**, dispatching propositions to today's prose arm and datasets to `_revise_dataset_locked`; the accepted dataset revision is **restamped by the writer** (the supplied stamp is ignored).

- [ ] **Step 1: Write the failing tests**

```python
# python/tests/test_dataset_revision.py
"""F6 and F3's revision cases (design §5.3)."""

import pytest
from authority import lacking
from nodes.core.relations import Relation
from nodes.core.write_plan import DefaultExecutor
from profiles import WITH_BIOLOGY, pins_for
from test_corpus_write import OperationRecorder

from beliefs import stored
from beliefs.corpus import CorpusWriter
from beliefs.errors import ActorMismatch, PermitExceeded, ReviseOutsideAllowlist, RevisionTargetMissing
from beliefs.permit import Authority, WritePermit

PINNED = [{"name": "m", "digest": "sha256:" + "1" * 64}]
ALICE = Authority(WritePermit.full(), "alice")
BOB = Authority(WritePermit.full(), "bob")
DATASET_ONLY = lacking(kinds=("proposition",), actor="alice")  # every kind but proposition


def writer(root, authority):
    port = OperationRecorder(root, authority=authority, profile=WITH_BIOLOGY)
    w = CorpusWriter(root, DefaultExecutor, authority=authority, profile=WITH_BIOLOGY, operation_port=port)
    if not (root / "corpus.yaml").exists():
        w.adopt_manifest(profile=pins_for(WITH_BIOLOGY))
    return w


def revised(node, **facets):
    candidate = node.model_copy(deep=True)
    for key, value in facets.items():
        if value is None:
            candidate.facets.pop(key, None)
        else:
            candidate.facets[key] = value
    return candidate  # deliberately NOT restamped: the writer restamps (§5.3)


@pytest.fixture()
def minted(tmp_path):
    w = writer(tmp_path, ALICE)
    node = w.add(stored.dataset_node("d", title="d", resources=PINNED, empirical_observation={"locator": "url:x", "attested_by": "alice"}))
    return w, node


def test_dataset_only_authority_may_revise_a_dataset_and_the_writer_restamps(tmp_path):
    w = writer(tmp_path, ALICE)
    node = w.add(stored.dataset_node("d", title="d", resources=PINNED, empirical_observation={"locator": "url:x", "attested_by": "alice"}))
    narrow = writer(tmp_path, DATASET_ONLY)
    candidate = revised(node, **{"empirical-observation": {"locator": "url:y", "attested_by": "alice"}})
    del candidate.facets[stored.SEMANTIC_IDENTITY_FACET]  # an unstamped edit is accepted and restamped
    stored_node = narrow.revise(candidate)
    assert stored_node.facets["empirical-observation"]["locator"] == "url:y"
    assert not stored.semantic_hash_disagrees(narrow.read_view.get(node.id))
    proposition = w.add(stored.proposition_node("p", title="p", claim={"operator": "affects"}))
    with pytest.raises(PermitExceeded):
        narrow.revise(proposition.model_copy(update={"title": "renamed"}))


def test_alice_revises_her_own_locator_keeping_herself(minted):
    w, node = minted
    w.revise(revised(node, **{"empirical-observation": {"locator": "url:y", "attested_by": "alice"}}))
    assert w.read_view.get(node.id).facets["empirical-observation"]["locator"] == "url:y"


def test_bob_revising_the_locator_must_name_himself(minted, tmp_path):
    _, node = minted
    bob = writer(tmp_path, BOB)
    with pytest.raises(ActorMismatch):
        bob.revise(revised(node, **{"empirical-observation": {"locator": "url:y", "attested_by": "alice"}}))
    bob.revise(revised(node, **{"empirical-observation": {"locator": "url:y", "attested_by": "bob"}}))


def test_an_unchanged_declaration_keeps_its_attester(minted, tmp_path):
    _, node = minted
    bob = writer(tmp_path, BOB)
    with pytest.raises(ActorMismatch):
        bob.revise(revised(node, **{"empirical-observation": {"locator": "url:x", "attested_by": "bob"}}))
    bob.revise(revised(node, **{"biology/gene-axis": {"axis": "rows"}}))  # a domain facet, the declaration untouched


def test_removing_the_facet_is_refused_and_removing_a_domain_facet_is_not(minted):
    w, node = minted
    with_axis = w.revise(revised(node, **{"biology/gene-axis": {"axis": "rows"}}))
    w.revise(revised(with_axis, **{"biology/gene-axis": None}))
    with pytest.raises(ReviseOutsideAllowlist, match="empirical-observation"):
        w.revise(revised(node, **{"empirical-observation": None}))


@pytest.mark.parametrize(
    "field, refusal",
    [("id", RevisionTargetMissing), ("uid", RevisionTargetMissing), ("relations", ReviseOutsideAllowlist),
     ("deprecated_ids", ReviseOutsideAllowlist), ("metadata", ReviseOutsideAllowlist),
     ("dataset", ReviseOutsideAllowlist), ("lineage-basis", ReviseOutsideAllowlist)],
)
def test_every_preserved_field_is_refused_when_moved(minted, field, refusal):
    w, node = minted
    candidate = node.model_copy(deep=True)
    if field == "id":
        candidate.id = "dataset:other"
    elif field == "uid":
        candidate.uid = "0" * 32
    elif field == "relations":
        candidate.relations.append(Relation(source=node.id, predicate="reads", target="dataset:z"))
    elif field == "deprecated_ids":
        candidate.deprecated_ids = ["dataset:old"]
    elif field == "metadata":
        candidate.metadata = candidate.metadata.model_copy(update={"version": candidate.metadata.version + 1})
    elif field == "dataset":
        candidate.facets["dataset"] = {"resources": [{"name": "n", "digest": "sha256:" + "2" * 64}]}
    else:
        candidate.facets["lineage-basis"] = {"tag": "single", "routes": []}
    with pytest.raises(refusal):
        w.revise(candidate)
    assert w.read_view.get(node.id).facets == node.facets


def test_adding_the_facet_to_an_unmarked_dataset_mints_the_declaration(tmp_path):
    w = writer(tmp_path, ALICE)
    plain = w.add(stored.dataset_node("p", title="p", resources=PINNED))
    with pytest.raises(ActorMismatch):
        w.revise(revised(plain, **{"empirical-observation": {"locator": "url:x", "attested_by": "bob"}}))
    w.revise(revised(plain, **{"empirical-observation": {"locator": "url:x", "attested_by": "alice"}}))
    assert stored.dataset_declaration(w.read_view.get(plain.id)) == stored.dataset_declaration(plain)


def test_a_malformed_payload_in_a_revision_is_refused_as_a_payload_fault(minted):
    from beliefs.errors import FacetPayloadRefused

    w, node = minted
    with pytest.raises(FacetPayloadRefused, match="null"):
        w.revise(revised(node, **{"empirical-observation": {"locator": None, "attested_by": "alice"}}))


def test_display_and_prose_may_change(minted):
    w, node = minted
    candidate = node.model_copy(deep=True, update={"title": "new title"})
    candidate.facets["display"] = {"display_statement": "shown"}
    w.revise(candidate)
    assert w.read_view.get(node.id).title == "new title"
```

(Confirm `Node` has a `metadata` field in the installed `nodes` — `grep -n "metadata" /path/to/nodes/core/node.py`; if it does not, drop that parametrization row and say so in the commit.)

- [ ] **Step 2: Run to verify failure** — `cd python && uv run --frozen pytest tests/test_dataset_revision.py -q` → `ReviseKindImmutable` / `PermitExceeded` on the wrong kind.

- [ ] **Step 3: Restructure `revise` and add the arm**

Replace `revise`'s opening so that the permit is required on the current record's kind after it resolves under the lock:

```python
    def revise(self, node: Node) -> Node:
        """Replace a proposition after changing display prose alone, or a dataset
        within §5.3's interpretation-and-prose boundary."""
        with self._operation:
            self._require_pins_agree()
            existing = self._corpus.index.by_uid.get(node.uid)
            if existing is None or existing.id != node.id:
                raise RevisionTargetMissing(f"{node.id}: exact uid and id do not identify a local node")
            current = self._view.get(node.id)
            self._authority.require("corpus-write", (current.kind,))
            if current.kind == "dataset" and node.kind == "dataset":
                return self._revise_dataset_locked(node, current)
            if current.kind != "proposition" or node.kind != "proposition":
                raise ReviseKindImmutable("revise operates on propositions and datasets only")
            ... # the existing proposition body from `self._refuse_family_kinds(node)` onward, unchanged
```

and:

```python
    _DATASET_REVISION_FACETS = frozenset({stored.EMPIRICAL_OBSERVATION_FACET, stored.DISPLAY_FACET})

    def _revise_dataset_locked(self, node: Node, current: Node) -> Node:
        """§5.3's exact boundary. Everything outside title, body, display, the
        empirical-observation declaration and namespaced domain facets must be
        byte-identical; the stamp is the writer's to recompute."""
        candidate_fields = node.model_dump()
        current_fields = current.model_dump()
        for fields in (candidate_fields, current_fields):
            fields.pop("title")
            fields.pop("body")
            facets = fields["facets"]
            fields["facets"] = {
                key: value for key, value in facets.items()
                if key not in self._DATASET_REVISION_FACETS and key != stored.SEMANTIC_IDENTITY_FACET and "/" not in key
            }
        if candidate_fields != current_fields:
            moved = sorted(k for k in set(candidate_fields) | set(current_fields) if candidate_fields.get(k) != current_fields.get(k))
            raise ReviseOutsideAllowlist(f"{node.id}: a dataset revision preserves {', '.join(moved)}")
        before = current.facets.get(stored.EMPIRICAL_OBSERVATION_FACET)
        after = node.facets.get(stored.EMPIRICAL_OBSERVATION_FACET)
        if before is not None and after is None:
            raise ReviseOutsideAllowlist(
                f"{node.id}: removing {stored.EMPIRICAL_OBSERVATION_FACET!r} withdraws standing; that is a "
                "record-level act the correction lifecycle has not designed (facet-contracts §2 item 3)"
            )
        for key, payload in node.facets.items():  # F1 before F3: a malformed payload is refused as such,
            facet = self._profile.facets.get(key)  # never as an attestation fault or an unencodable stamp
            if facet is not None:
                validate_payload(facet, payload, where=node.id)
        if after is not None:
            strip = lambda payload: {k: v for k, v in payload.items() if k != "attested_by"}  # noqa: E731
            declaration_changed = before is None or strip(before) != strip(after)
            expected = self._authority.actor if declaration_changed else before["attested_by"]  # type: ignore[index]
            if after.get("attested_by") != expected:
                raise ActorMismatch(
                    f"{node.id}: a {'changed' if declaration_changed else 'unchanged'} declaration names attester "
                    f"{after.get('attested_by')!r}, expected {expected!r}"
                )
        if stored.display_facet_malformed(node):
            raise ValidationRefused(f"{node.id}: refused by document validation: malformed display facet")
        restamped = stored.stamp_semantic_identity(node.model_copy(deep=True))
        self._refuse_invalid(restamped)
        self._refuse_facets(restamped, provenance=True)  # attestation was judged above against the stored declaration
        self._refuse_governed_stamp(restamped)
        self._refuse_rendering(restamped)
        return self._corpus.add(restamped)
```

(`current_fields`/`candidate_fields` include `metadata`, `relations`, `deprecated_ids`, `uid`, `kind` and every non-allowlisted facet, so any of them moving is caught by one comparison; `id`/`uid` changes fail earlier as `RevisionTargetMissing`.)

- [ ] **Step 4: Run, lint, commit**

`cd python && uv run --frozen pytest && uv run --frozen ruff check . && uv run --frozen pyright`

```bash
git add python/src/beliefs/corpus.py python/tests/test_dataset_revision.py
git commit -m "feat(corpus): revise gains the dataset interpretation-correction arm, permit on the actual kind, writer-restamped"
```

---

### Task 10: Guarded production publication

**Files:**
- Create: `python/tests/test_guarded_publication.py`
- Modify: `python/src/beliefs/runrecord.py:89-98` (the `OperationPort` protocol), `python/src/beliefs/root.py` (`DurableOperationPort`), `python/src/beliefs/boundary.py:892-965` (`execute_production_run`, `acquisition_guard`), `python/tests/test_corpus_write.py` (`OperationRecorder`)

**Interfaces:**
- Produces: `OperationPort.execute_fulfilling_guarded(plan, fulfills, *, guard: Callable[[ReadView], str | None], fallback: Callable[[str], WritePlan]) -> str | None` — under the lock: `require_pins_agree(root, self.profile)` (raises `ContractMismatch`, nothing executed), then `guard(view)`; `None` → `plan` executed, `None` returned; a reason → `fallback(reason)` executed and the reason returned. `boundary.acquisition_guard(run: RunClosure) -> Callable[[ReadView], str | None]`.

- [ ] **Step 1: Write the failing tests**

```python
# python/tests/test_guarded_publication.py
"""§5.4: the production boundary's bearer check shares the publication lock."""

import pytest
from authority import ACTOR, FULL
from closure_fixtures import make_closure
from nodes.core.write_plan import DefaultExecutor
from profiles import BASE, pins_for
from test_corpus_write import OperationRecorder

from beliefs import stored
from beliefs.corpus import CorpusWriter
from beliefs.errors import ContractMismatch
from beliefs.runrecord import publication_plan


def corpus(tmp_path):
    port = OperationRecorder(tmp_path, authority=FULL, profile=BASE)
    w = CorpusWriter(tmp_path, DefaultExecutor, authority=FULL, profile=BASE, operation_port=port)
    w.adopt_manifest(profile=pins_for(BASE))
    return w, port


def test_the_guard_runs_under_the_lock_and_selects_the_plan(tmp_path):
    _, port = corpus(tmp_path)
    _, _, plan = publication_plan(make_closure(shape="dataset-production"))
    reason = port.execute_fulfilling_guarded(plan, "ab" * 32, guard=lambda view: None, fallback=lambda r: ())
    assert reason is None and port.fulfilling[-1][0] == list(plan)


def test_a_reason_publishes_the_fallback_and_returns_it(tmp_path):
    _, port = corpus(tmp_path)
    _, _, plan = publication_plan(make_closure(shape="dataset-production"))
    marker = [("fallback", ())]
    reason = port.execute_fulfilling_guarded(plan, "ab" * 32, guard=lambda view: "acquisition-boundary", fallback=lambda r: marker)
    assert reason == "acquisition-boundary" and port.fulfilling[-1][0] == marker


def test_a_pin_mismatch_under_the_lock_publishes_neither_plan(tmp_path):
    _, port = corpus(tmp_path)
    text = (tmp_path / "corpus.yaml").read_text()
    (tmp_path / "corpus.yaml").write_text(text.replace(pins_for(BASE).science_contract, "science:" + "f" * 64))
    _, _, plan = publication_plan(make_closure(shape="dataset-production"))
    with pytest.raises(ContractMismatch):
        port.execute_fulfilling_guarded(plan, "ab" * 32, guard=lambda v: None, fallback=lambda r: ())
    assert not port.fulfilling


def test_the_acquisition_guard_reads_the_produced_address(tmp_path):
    """The guard the production boundary installs (§5.4). The boundary path itself
    runs durably in Task 15's acceptance module through `fixtures_cut15`'s
    production helper."""
    from beliefs.boundary import acquisition_guard
    from beliefs.production import mint_dataset

    w, _ = corpus(tmp_path)
    closure = make_closure(shape="dataset-production")
    address = mint_dataset(closure, existing_bases={}).address
    assert acquisition_guard(closure)(w.read_view) is None
    w.add(stored.dataset_node(
        address.removeprefix("dataset:"),
        title="bearer",
        resources=[{"name": name, "digest": digest} for name, digest in closure.result.outputs],
        empirical_observation={"locator": "url:x", "attested_by": ACTOR},
    ))
    assert acquisition_guard(closure)(w.read_view) == "acquisition-boundary"
```

- [ ] **Step 2: Run to verify failure** — `cd python && uv run --frozen pytest tests/test_guarded_publication.py -q` → `AttributeError: execute_fulfilling_guarded`.

- [ ] **Step 3: The port**

In `runrecord.py`'s `OperationPort` protocol add:

```python
    def execute_fulfilling_guarded(
        self,
        plan: WritePlan,
        fulfills: str,
        *,
        guard: Callable[[ReadView], str | None],
        fallback: Callable[[str], WritePlan],
    ) -> str | None: ...
```

(`from collections.abc import Callable`; `ReadView` under `TYPE_CHECKING`.) In `DurableOperationPort`:

```python
    def execute_fulfilling_guarded(self, plan, fulfills, *, guard, fallback):
        from beliefs.corpus import ReadView, require_pins_agree

        with _operation_lock_for(self.root):
            require_pins_agree(self.root, self._profile)  # raises before either plan
            reason = guard(ReadView.opened_at(self.root))
            self._execute_fulfilling(plan if reason is None else fallback(reason), fulfills)
            return reason
```

`OperationRecorder` gets the same method (record into `fulfilling`, call `require_pins_agree(self.root, self.profile)` first, return the reason).

- [ ] **Step 4: The boundary**

In `execute_production_run`, replace

```python
    if type(result) is RunMinted:
        _, _, plan = publication_plan(result.run)
        port.execute_fulfilling(plan, fulfills)
```

with

```python
    if type(result) is RunMinted:
        _, _, plan = publication_plan(result.run)

        def _fallback(reason: str) -> WritePlan:
            return _report_plan(_refused(reason, "absent", actor, observer, started_at, intent).report)

        reason = port.execute_fulfilling_guarded(plan, fulfills, guard=acquisition_guard(result.run), fallback=_fallback)
        if reason is not None:
            result = _refused(reason, "absent", actor, observer, started_at, intent)
```

and add beside `_report_plan`:

```python
def acquisition_guard(run: RunClosure) -> Callable[[ReadView], str | None]:
    """§5.4: under the publication lock, the produced address must not resolve to
    a facet-bearing dataset. The reason string is the refusal's."""

    def guard(view: ReadView) -> str | None:
        produced = mint_dataset(run, existing_bases={}).address
        resolved = view.resolve(produced)
        if resolved is not None and stored.EMPIRICAL_OBSERVATION_FACET in view.get(resolved).facets:
            return "acquisition-boundary"
        return None

    return guard
```

(`from beliefs.production import mint_dataset`; `ReadView` under `TYPE_CHECKING`.) The assessment boundary's publication and every refusal report keep using `execute_fulfilling`/`execute`, which Task 7 made recheck the pins under their own lock; the pin-mismatch-after-intent case (unfulfilled intent, `ContractMismatch` raised) is F5's second arm and is asserted in `test_profile_agreement.py`'s `port-fulfilling` case and durably in Task 15.

- [ ] **Step 5: Run, lint, commit**

`cd python && uv run --frozen pytest && uv run --frozen ruff check . && uv run --frozen pyright`

```bash
git add python/src/beliefs/runrecord.py python/src/beliefs/root.py python/src/beliefs/boundary.py python/tests/test_guarded_publication.py python/tests/test_corpus_write.py
git commit -m "feat(boundary): guarded production publication under the operation lock"
```

---

### Task 11: The check and the audit take the profile; the stopping matrix

**Files:**
- Modify: `python/src/beliefs/corpus.py` (`corpus_check`, `profile_mismatch`, `_CheckView`), `python/src/beliefs/audit.py` (`audit_corpus`), `python/tests/test_read_side.py` (`seed`, new cases), `python/tests/test_audit.py`, `python/tools/reproduction/close.py`

**Interfaces:**
- Produces: `corpus_check(view, profile) -> tuple[Finding, ...]`; `audit_corpus(view, *, evidence, profile)`; `profile_mismatch(root, profile) -> tuple[MismatchScope, str]` with `MismatchScope = Literal["none", "domains", "base", "malformed"]`; finding codes `profile-mismatch`, `kind-unknown`, `facet-unexpected`, `facet-missing`, `facet-payload-malformed`, `facet-bearer-produced`, `facet-retrieval-unresolved`; the check reads neighbours **unvalidated** through a `_CheckView` adapter so a stale neighbour is a finding elsewhere, never a raise here.

**The stopping matrix**, implemented literally:

| scope | reported | withheld |
|---|---|---|
| `none` | everything | nothing |
| `domains` | `manifest-malformed`; stamp findings; `kind-unknown` for non-coordination kinds; `facet-missing`/`facet-unexpected` for unnamespaced keys on non-coordination kinds; `empirical-observation` payload validity; bearer; retrieval; eligibility; retraction and lineage findings | every judgment on a namespaced key; **every judgment on a coordination kind** (their kind and `coordination` facet are unnamespaced, so they are withheld by kind membership in `profile.coordination_kinds`) when `coordination` is among the disagreeing pins, else nothing coordination-shaped |
| `base` | `profile-mismatch`, `manifest-malformed` | everything else, stamps included; the audit performs no recomputation |
| `malformed` | `manifest-malformed`, `profile-mismatch` (detail `malformed`) | as `base` |

- [ ] **Step 1: Write the failing tests**

Give `test_read_side.py`'s `seed(tmp_path, *nodes)` two keyword parameters, `pins=None` (default `pins_for(BASE)`) and `science_contract=None` (override), write the manifest with `manifest_bytes` after the raw writes, and return `ReadView(Corpus(root))`. Then append to `TestTheCorpusCheck`:

```python
    def test_the_check_takes_the_profile_and_reports_facet_findings(self, tmp_path):
        bad = stored.dataset_node("b", title="b", resources=PINNED, empirical_observation={"boundary": "x"})
        assert [(f.code, f.ref) for f in corpus_check(seed(tmp_path, bad), BASE)] == [("facet-payload-malformed", bad.id)]

    def test_a_raw_written_bearer_conflict_is_reported_once(self, tmp_path):
        d = observed_dataset()
        r = stored.run_node("r", title="r", spec="analysis-spec:s", produces=[d.id])
        findings = [(f.code, f.ref) for f in corpus_check(seed(tmp_path, d, r), BASE)]
        assert findings.count(("facet-bearer-produced", d.id)) == 1

    def test_an_unknown_kind_and_an_undeclared_key_are_reported(self, tmp_path):
        from nodes.core.node import Node
        stray = Node(id="divergence:x", kind="divergence", title="x", facets={})
        keyed = stored.proposition_node("p", title="p", claim={"operator": "affects"})
        keyed.facets["biology/gene-axis"] = {}
        codes = {(f.code, f.ref) for f in corpus_check(seed(tmp_path, stray, stored.stamp_semantic_identity(keyed)), BASE)}
        assert ("kind-unknown", "divergence:x") in codes and ("facet-unexpected", keyed.id) in codes

    def test_a_stale_neighbour_is_a_finding_not_a_raise(self, tmp_path):
        d = observed_dataset()
        r = stored.run_node("r", title="r", spec="analysis-spec:s", produces=[d.id])
        r.facets["run"]["spec"] = "analysis-spec:tampered"  # stamp now disagrees
        findings = corpus_check(seed(tmp_path, d, r), BASE)
        codes = {(f.code, f.ref) for f in findings}
        assert ("semantic-hash-stale", r.id) in codes and ("facet-bearer-produced", d.id) in codes

    def test_a_domain_only_mismatch_withholds_namespaced_judgments_and_keeps_base_ones(self, tmp_path):
        from profiles import WITH_BIOLOGY
        bad = stored.dataset_node("b", title="b", resources=PINNED, empirical_observation={"boundary": "x"})
        bad.facets["biology/gene-axis"] = {"axis": "rows"}
        findings = corpus_check(seed(tmp_path, stored.stamp_semantic_identity(bad), pins=pins_for(WITH_BIOLOGY)), BASE)
        codes = [f.code for f in findings]
        assert codes.count("profile-mismatch") == 1 and "facet-payload-malformed" in codes and "facet-unexpected" not in codes

    def test_a_coordination_pin_disagreement_withholds_only_what_needs_the_contract(self, tmp_path):
        from coordination_fixtures import coordination_profile  # the profile compiled with the coordination contract
        from nodes.core.node import Node
        pins = pins_for(coordination_profile())
        malformed_task = Node(id="task:t", kind="task", title="t", facets={"coordination": {"nonsense": True}})
        facetless_task = Node(id="task:u", kind="task", title="u", facets={})
        findings = corpus_check(seed(tmp_path, malformed_task, facetless_task, pins=pins), BASE)
        assert [f.code for f in findings] == ["profile-mismatch"]  # both withheld by kind, facet or no facet
        raw = stored.dataset_node("b", title="b", resources=PINNED, empirical_observation={"boundary": "x"})
        raw.facets["coordination"] = {"nonsense": True}
        del raw.facets[stored.SEMANTIC_IDENTITY_FACET]
        findings = corpus_check(seed(tmp_path / "second", raw, pins=pins), BASE)
        codes = {f.code for f in findings}
        assert codes == {"profile-mismatch", "semantic-hash-missing", "facet-unexpected", "facet-payload-malformed"}

    def test_a_base_mismatch_withholds_everything_but_the_mismatch(self, tmp_path):
        node = observed_dataset()
        del node.facets[stored.SEMANTIC_IDENTITY_FACET]
        assert [f.code for f in corpus_check(seed(tmp_path, node, science_contract="science:" + "f" * 64), BASE)] == ["profile-mismatch"]

    def test_a_malformed_manifest_is_two_findings_and_no_judgment(self, tmp_path):
        node = observed_dataset()
        del node.facets[stored.SEMANTIC_IDENTITY_FACET]
        view = seed(tmp_path, node)
        (tmp_path / "corpus.yaml").write_text("manifest_version: 3\n")
        assert sorted(f.code for f in corpus_check(view, BASE)) == ["manifest-malformed", "profile-mismatch"]

    def test_eligibility_keeps_the_existential_rule(self, tmp_path):
        good = observed_dataset()
        bad = stored.dataset_node("b", title="b", resources=PINNED, empirical_observation={"boundary": "x"})
        view = seed(
            tmp_path, good, bad,
            stored.run_node("r1", title="r1", spec="analysis-spec:s1", observes=[good.id, bad.id]),
            stored.assessment_node("a1", title="a1", spec="analysis-spec:s1", run="run:r1", proposition="proposition:p1", outcome="supported", interpretation_rule="rule:threshold"),
            stored.proposition_node("p1", title="p1", claim={"operator": "affects"}),
        )
        codes = [f.code for f in corpus_check(view, BASE)]
        assert "eligibility-unmet" not in codes and codes == ["facet-payload-malformed"]
```

(`coordination_fixtures.coordination_profile` may be named differently; use whatever that module exposes that returns the compiled profile with the coordination contract.) Append to `test_audit.py`:

```python
def test_the_audit_stops_on_a_base_mismatch_without_recomputing(writer):
    from nodes.core.corpus import Corpus
    from beliefs.corpus import ReadView
    text = (writer.root / "corpus.yaml").read_text()
    (writer.root / "corpus.yaml").write_text(text.replace(pins_for(BASE).science_contract, "science:" + "f" * 64))
    assert [f.code for f in audit_corpus(ReadView(Corpus(writer.root)), evidence=NO_EVIDENCE, profile=BASE)] == ["profile-mismatch"]
```

- [ ] **Step 2: Run to verify failure** — `cd python && uv run --frozen pytest tests/test_read_side.py tests/test_audit.py -q -k "profile or mismatch or bearer or unknown or existential or neighbour or malformed_manifest"` → TypeErrors on the new signature.

- [ ] **Step 3: Implement**

In `corpus.py`:

```python
MismatchScope = Literal["none", "domains", "base", "malformed"]


def profile_mismatch(root: Path, profile: ProfileSpec) -> tuple[MismatchScope, str, frozenset[str]]:
    """§5.5: what the manifest's pins disagree with, a message, and the disagreeing
    domain namespaces. A manifest that cannot be read is `malformed`: nothing can
    be judged against pins nobody can state."""
    manifest_path = Path(root) / "corpus.yaml"
    if not manifest_path.exists():
        return "none", "", frozenset()
    from beliefs.world import load_manifest

    try:
        pins = load_manifest(root).profile
    except ManifestMalformed as caught:
        return "malformed", str(caught), frozenset()
    if pins.science_contract != "science:" + profile.base_contract_identity:
        return "base", f"manifest pins {pins.science_contract[:20]}…, profile carries science:{profile.base_contract_identity[:12]}…", frozenset()
    expected = {ns: f"{ns}:{identity}" for ns, identity in profile.activated_contracts.items()}
    disagreeing = frozenset(ns for ns in set(pins.domains) | set(expected) if pins.domains.get(ns) != expected.get(ns))
    if disagreeing:
        return "domains", f"manifest domains disagree on {sorted(disagreeing)}", disagreeing
    return "none", "", frozenset()


class _CheckView:
    """The check's own read: every record unvalidated, so a stale neighbour is
    reported where it stands and never raises here (§5.5)."""

    def __init__(self, view: ReadView) -> None:
        self._view = view
        self._by_id = {node.id: node for node in view.iter_stored()}

    def resolve(self, ref: str) -> str | None:
        return self._view.resolve(ref)

    def holds(self, ref: str) -> bool:
        return self.resolve(ref) is not None

    def get(self, ref: str) -> Node:
        resolved = self.resolve(ref)
        return self._by_id[resolved if resolved is not None else ref]

    def producers(self, dataset: str, *, aliases: tuple[str, ...] = ()) -> tuple[str, ...]:
        names = {dataset, *aliases}
        return tuple(sorted(
            node.id for node in self._by_id.values()
            for relation in node.relations
            if relation.predicate == stored.PRODUCES and (relation.target in names or self.resolve(relation.target) == dataset)
        ))
```

`corpus_check(view: ReadView, profile: ProfileSpec)`:

1. Keep the existing `manifest-malformed` block. Then `scope, detail, disagreeing = profile_mismatch(root, profile)`; when `scope != "none"` append `Finding(severity="error", code="profile-mismatch", ref="corpus.yaml", detail=scope, message=detail)`.
2. When `scope in ("base", "malformed")`: return the findings so far.
3. Otherwise run the existing loop with a `_CheckView` (`check = _CheckView(view)`) and two flags: `judge_namespaced = scope == "none"`, `withhold_coordination = "coordination" in disagreeing`. What the coordination contract alone can judge is decided by the **shipped base inventory**, never by the supplied profile's `coordination_kinds` (empty exactly when the profile lacks the contract the manifest pins) and never by the presence of the facet: a node whose kind is in `shipped_base().kinds` (world or prose) keeps **every base judgment** — stamps, base-facet payloads, the bearer invariant, retrieval, eligibility, and `facet-unexpected` for a `coordination` facet the base declares on no such kind; a node whose kind is **outside** that inventory is one only the coordination contract can judge, so when `withhold_coordination` the loop `continue`s on it as its first statement — before today's `coordination_facet_malformed` check and before anything else — and the post-loop supersession-graph checks over `coordination_revisions` are skipped entirely. A coordination record that has lost its facet is therefore withheld by its kind, and a dataset that gained one is judged by the base. Then, per remaining node, after the stamp checks:

```python
        for violation in profile.document_violations(node):
            if violation.code == "unknown-kind":
                findings.append(Finding(severity="error", code="kind-unknown", ref=node.id, detail=node.kind, message=violation.message))
            elif violation.code in ("facet-missing", "facet-unexpected"):
                if "/" in violation.detail and not judge_namespaced:
                    continue
                findings.append(Finding(severity="error", code=violation.code, ref=node.id, detail=violation.detail, message=violation.message))
        for key, payload in node.facets.items():
            facet = profile.facets.get(key)
            if facet is None or ("/" in key and not judge_namespaced):
                continue
            try:
                validate_payload(facet, payload, where=node.id)
            except FacetPayloadRefused as refused:
                findings.append(Finding(severity="error", code="facet-payload-malformed", ref=node.id, detail=key, message=str(refused)))
        if node.kind == "dataset" and stored.EMPIRICAL_OBSERVATION_FACET in node.facets:
            reason = validity_refusal(check, node, profile)
            if reason is not None and not reason.startswith("facet-payload-malformed"):
                bearer_or_retrieval.add((reason.split(":", 1)[0], node.id, reason))
        for relation in node.relations:
            if relation.predicate == stored.PRODUCES:
                target = check.resolve(relation.target)
                if target is not None and stored.EMPIRICAL_OBSERVATION_FACET in check.get(target).facets:
                    bearer_or_retrieval.add(("facet-bearer-produced", target, f"produced by {node.id}"))
```

with `bearer_or_retrieval: set[tuple[str, str, str]]` collected across the loop and emitted once per `(code, ref)` after it (one finding per dataset, the details joined), which is what makes the raw-written pair report once. Replace the eligibility call with `eligibility_refusal(check, node, profile)` and drop Task 8's placeholder. Add `facet-payload-malformed` to `MALFORMEDNESS_CODES` (a malformed declaration must not feed a derivation); `facet-bearer-produced` and `facet-retrieval-unresolved` stay out.

`audit_corpus(view, *, evidence, profile)`: `findings = list(corpus_check(view, profile))`; if any finding has `code == "profile-mismatch"` and `detail in ("base", "malformed")`, return `tuple(findings)` at once. Update `close.py` to pass `profile()` to both.

- [ ] **Step 4: Run, lint, commit**

`cd python && uv run --frozen pytest && uv run --frozen ruff check . && uv run --frozen pyright`

```bash
git add python/src/beliefs/corpus.py python/src/beliefs/audit.py python/tests/test_read_side.py python/tests/test_audit.py python/tools/reproduction/close.py
git commit -m "feat(corpus): the check and the audit judge under the caller's profile with the stopping matrix, reading neighbours unvalidated"
```

---
### Task 12: The consulted walk's facet arm

**Files:**
- Modify: `python/src/beliefs/consulted.py`, `python/src/beliefs/evaluation.py:206`, `python/src/beliefs/belief.py:219`, `python/tests/test_consulted.py` (create if absent)

**Interfaces:**
- Produces: `consulted_contracts(*, claims, profile, node_corpus, pins, closure_nodes, facets_read: Mapping[str, tuple[str, ...]] = MappingProxyType({}))` — per closure node, the namespaced facet keys a derivation read; the declaring namespace of each enters `consulted` exactly as an operator's does.

- [ ] **Step 1: Write the failing tests**

```python
# python/tests/test_consulted.py (append or create)
"""§5.6: a facet a derivation read brings its declaring contract in; a facet merely present does not."""

from profiles import WITH_BIOLOGY, pins_for

from beliefs.consulted import CorpusPins, consulted_contracts


def _pins():
    p = pins_for(WITH_BIOLOGY)
    return {"c": CorpusPins(p.science_contract, dict(p.domains))}


def test_a_read_domain_facet_enters_the_consulted_set():
    consulted = dict(consulted_contracts(
        claims={}, profile=WITH_BIOLOGY, node_corpus={"dataset:d": "c"}, pins=_pins(),
        closure_nodes=("dataset:d",), facets_read={"dataset:d": ("biology/gene-axis",)},
    ))
    assert set(consulted) == {"science", "biology"}


def test_an_unread_activated_domain_stays_out():
    consulted = dict(consulted_contracts(
        claims={}, profile=WITH_BIOLOGY, node_corpus={"dataset:d": "c"}, pins=_pins(),
        closure_nodes=("dataset:d",), facets_read={},
    ))
    assert set(consulted) == {"science"}


def test_an_unnamespaced_facet_read_adds_nothing_beyond_the_base():
    consulted = dict(consulted_contracts(
        claims={}, profile=WITH_BIOLOGY, node_corpus={"dataset:d": "c"}, pins=_pins(),
        closure_nodes=("dataset:d",), facets_read={"dataset:d": ("empirical-observation",)},
    ))
    assert set(consulted) == {"science"}
```

- [ ] **Step 2: Run to verify failure** — `cd python && uv run --frozen pytest tests/test_consulted.py -q` → TypeError on `facets_read`.

- [ ] **Step 3: Implement**

In `consulted_contracts`, add the parameter and, after the claim loop:

```python
    for node, keys in facets_read.items():
        if node not in closure_nodes:
            raise MalformedRecord(f"{node} is reported read but is not a closure node; a read ledger names closure members only")
        for key in keys:
            namespace, separator, _ = key.partition("/")
            if separator:
                read.add(namespace)
```

Pass `facets_read={}` explicitly at both call sites (`evaluation.py`, `belief.py`) with the comment `# §5.6: no derivation reads a domain facet yet; the read ledger arrives with the first reader (slice 2)`.

- [ ] **Step 4: Run, lint, commit**

```bash
git add python/src/beliefs/consulted.py python/src/beliefs/evaluation.py python/src/beliefs/belief.py python/tests/test_consulted.py
git commit -m "feat(consulted): the facet arm of the consulted walk, keyed on facets read"
```

---

### Task 13: The second parity fixture — `science.identity.v1` values

**Files:**
- Create: `python/tools/generate_identity_fixture.py`, `fixtures/identity-v1.json`, `python/tests/test_identity_parity_fixture.py`, `ts/tests/identity-fixture.test.ts`

**Interfaces:**
- Produces: the frozen fixture with rows `{name, covers, domain, value: <tagged component>, canonical_bytes, digest}` for successful rows and `{name, covers, domain, value, refusal: <name>}` for refusal rows. Tagged components: `{"t": "str", "v": "..."}`, `{"t": "bool", "v": true}`, `{"t": "int", "v": "12"}`, `{"t": "decimal", "v": "0.0"}`, `{"t": "float", "v": "0.1"}`, `{"t": "list", "v": [...]}`, `{"t": "obj", "v": {key: component}}`, `{"t": "null"}`.

- [ ] **Step 1: Write the generator**

```python
# python/tools/generate_identity_fixture.py
"""Generate the values-level parity fixture for `science.identity.v1` (facet-contracts §7.3).
**Run by hand, never by tests:** `uv run python tools/generate_identity_fixture.py`.

Every row carries a **tagged** component tree, because JSON numbers cannot say
whether they meant an integer, a decimal or a binary float; the reader rebuilds
`int`/`Decimal`/`float` (Python) and `bigint`/`Decimal`/`number` (TypeScript).
Successful rows pin canonical bytes **and** digest; refusal rows pin the refusal.
The file is pure ASCII so an editor cannot normalize the decomposed row away.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from beliefs.errors import BinaryFloatRefused, LoneSurrogate, NullRefused
from beliefs.identity import v1

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT = REPO_ROOT / "fixtures" / "identity-v1.json"
DOMAIN = "science.parity-fixture.v1"


def tagged(value: object) -> object:
    if value is None:
        return {"t": "null"}
    if isinstance(value, bool):
        return {"t": "bool", "v": value}
    if isinstance(value, int):
        return {"t": "int", "v": str(value)}
    if isinstance(value, Decimal):
        return {"t": "decimal", "v": str(value)}
    if isinstance(value, float):
        return {"t": "float", "v": repr(value)}
    if isinstance(value, str):
        return {"t": "str", "v": value}
    if isinstance(value, list):
        return {"t": "list", "v": [tagged(v) for v in value]}
    if isinstance(value, dict):
        return {"t": "obj", "v": {k: tagged(v) for k, v in value.items()}}
    raise TypeError(type(value).__name__)


@dataclass(frozen=True)
class Row:
    name: str
    covers: str
    value: object
    refusal: type[Exception] | None = None


ESCAPES = "".join(chr(c) for c in range(0x00, 0x20)) + '"\\'

VECTOR = [
    Row("integer", "an integer never contains a point", 12),
    Row("integer-zero", "one spelling of integer zero", 0),
    Row("negative-integer", "sign preserved", -7),
    Row("big-integer", "beyond 2^53, so a JavaScript number cannot carry it", 9007199254740993),
    Row("decimal-zero", "one spelling of decimal zero, folding -0", Decimal("-0.0")),
    Row("decimal-retains-fraction", "a decimal always retains a fractional part", Decimal("3")),
    Row("decimal-strips-trailing-zeros", "trailing zeros stripped", Decimal("1.2300")),
    Row("decimal-no-exponent", "never exponent notation", Decimal("1E+6")),
    Row("decimal-small", "small magnitudes spelled positionally", Decimal("1E-7")),
    Row("boolean-and-integer-distinct", "true is not 1", [True, 1]),
    Row("escape-table", "every C0 control, the quote and the backslash", ESCAPES),
    Row("non-ascii-unescaped", "non-ASCII is never escaped", "éβ\U0001F600"),
    Row("nfc-at-encode", "decomposed input, NFC-composed canonical output", "café"),
    Row("astral-key-order", "an astral key sorts after a high BMP key by code point", {"\U00010000": 1, "￿": 2}),
    Row("plain-key-order", "keys sort by code point", {"b": 1, "a": 2, "B": 3}),
    Row("namespaced-facet-key", "D4's parity arm: a namespaced facet key round-trips", {"facets": {"biology/gene-axis": {"axis": "rows"}}}),
    Row("nested", "arrays and objects nest", {"a": [1, {"b": [Decimal("2.5"), "c"]}]}),
    Row("binary-float-refused", "binary floats are refused at the boundary", 0.1, BinaryFloatRefused),
    Row("null-refused", "null is refused, not pruned", {"a": None}, NullRefused),
    Row("lone-surrogate-refused", "an unpaired surrogate has no UTF-8 encoding", "\ud800", LoneSurrogate),
]


def main() -> None:
    rows = []
    for row in VECTOR:
        entry: dict[str, object] = {"name": row.name, "covers": row.covers, "domain": DOMAIN, "value": tagged(row.value)}
        if row.refusal is None:
            entry["canonical_bytes"] = v1.encode(row.value).decode("utf-8")
            entry["digest"] = v1.digest(DOMAIN, row.value)
        else:
            entry["refusal"] = row.refusal.__name__
            try:
                v1.encode(row.value)
            except row.refusal:
                pass
            else:
                raise SystemExit(f"{row.name}: expected {row.refusal.__name__}, got an encoding")
        rows.append(entry)
    OUTPUT.write_text(
        json.dumps({"fixture": "identity-v1", "identity_contract": "science.identity.v1", "note": "A conformance oracle, frozen. Regenerate deliberately with tools/generate_identity_fixture.py and review the diff.", "vector": rows}, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
```

If `v1.encode` refuses any "successful" row above for a reason the encoder documents (read `identity/v1.py` before running), move that row to the refusal side with the encoder's own exception; do not weaken the encoder. Run `cd python && uv run --frozen python tools/generate_identity_fixture.py`, then open `fixtures/identity-v1.json` and check by eye that `decimal-zero` encodes as `0.0`, `integer-zero` as `0`, and `nfc-at-encode`'s bytes carry `é` while its value carries `é`.

- [ ] **Step 2: The Python reader test**

```python
# python/tests/test_identity_parity_fixture.py
"""The second parity fixture, Python half: components → encode → digest, bytes and digest both compared."""

import json
from decimal import Decimal
from pathlib import Path

import pytest

from beliefs import errors
from beliefs.identity import v1

FIXTURE = json.loads((Path(__file__).resolve().parents[2] / "fixtures" / "identity-v1.json").read_text(encoding="utf-8"))


def rebuild(component):
    tag = component["t"]
    if tag == "null":
        return None
    if tag == "bool":
        return component["v"]
    if tag == "int":
        return int(component["v"])
    if tag == "decimal":
        return Decimal(component["v"])
    if tag == "float":
        return float(component["v"])
    if tag == "str":
        return component["v"]
    if tag == "list":
        return [rebuild(v) for v in component["v"]]
    if tag == "obj":
        return {k: rebuild(v) for k, v in component["v"].items()}
    raise AssertionError(tag)


def test_the_fixture_is_about_this_encoding():
    assert FIXTURE["identity_contract"] == "science.identity.v1"
    assert {row["name"] for row in FIXTURE["vector"]} >= {"decimal-zero", "integer-zero", "escape-table", "astral-key-order", "namespaced-facet-key", "binary-float-refused"}


@pytest.mark.parametrize("row", [r for r in FIXTURE["vector"] if "refusal" not in r], ids=lambda r: r["name"])
def test_bytes_and_digest_agree(row):
    value = rebuild(row["value"])
    assert v1.encode(value).decode("utf-8") == row["canonical_bytes"]
    assert v1.digest(row["domain"], value) == row["digest"]


@pytest.mark.parametrize("row", [r for r in FIXTURE["vector"] if "refusal" in r], ids=lambda r: r["name"])
def test_refusals_agree(row):
    with pytest.raises(getattr(errors, row["refusal"])):
        v1.encode(rebuild(row["value"]))
```

- [ ] **Step 3: The TypeScript reader test**

```ts
// ts/tests/identity-fixture.test.ts
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import * as errors from "../src/errors.js";
import { Decimal, digest, encode } from "../src/identity/v1.js";

const REPO_ROOT = new URL("../../", import.meta.url);
type Component =
  | { t: "null" } | { t: "bool"; v: boolean } | { t: "int"; v: string } | { t: "decimal"; v: string }
  | { t: "float"; v: string } | { t: "str"; v: string } | { t: "list"; v: Component[] } | { t: "obj"; v: Record<string, Component> };
interface Row { name: string; covers: string; domain: string; value: Component; canonical_bytes?: string; digest?: string; refusal?: string }
const fixture = JSON.parse(readFileSync(new URL("fixtures/identity-v1.json", REPO_ROOT), "utf-8")) as { vector: Row[] };

function rebuild(c: Component): unknown {
  switch (c.t) {
    case "null": return null;
    case "bool": return c.v;
    case "int": return BigInt(c.v);
    case "decimal": return new Decimal(c.v);
    case "float": return Number(c.v);
    case "str": return c.v;
    case "list": return c.v.map(rebuild);
    case "obj": return Object.fromEntries(Object.entries(c.v).map(([k, v]) => [k, rebuild(v)]));
  }
}

describe("science.identity.v1 parity fixture", () => {
  for (const row of fixture.vector.filter((r) => r.refusal === undefined)) {
    it(`${row.name}: bytes and digest agree`, () => {
      const value = rebuild(row.value);
      expect(new TextDecoder().decode(encode(value))).toBe(row.canonical_bytes);
      expect(digest(row.domain, value)).toBe(row.digest);
    });
  }
  for (const row of fixture.vector.filter((r) => r.refusal !== undefined)) {
    it(`${row.name}: refused as ${row.refusal}`, () => {
      const refusal = (errors as Record<string, unknown>)[row.refusal as string] as new () => Error;
      expect(refusal, `TypeScript has no ${row.refusal}`).toBeDefined();
      expect(() => encode(rebuild(row.value))).toThrow(refusal);
    });
  }
});
```

If a refusal class name differs between languages (Python `BinaryFloatRefused` is TypeScript `BinaryFloatRefused`; check the others against `ts/src/errors.ts`), add a small name map in the test rather than renaming an error class. A decoded `\ud800` cannot be represented by JSON.parse in JavaScript as a lone surrogate string in the same way Python does; if the lone-surrogate row cannot be rebuilt in TypeScript, keep it in the fixture as Python-only with `"languages": ["python"]` on the row and skip it here — state that in the row's `covers`.

- [ ] **Step 4: Run both suites, lint, commit**

`cd python && uv run --frozen pytest tests/test_identity_parity_fixture.py -q && uv run --frozen ruff check . && uv run --frozen pyright`; `cd ts && npm test && npm run typecheck && npm run check`.

```bash
git add python/tools/generate_identity_fixture.py fixtures/identity-v1.json python/tests/test_identity_parity_fixture.py ts/tests/identity-fixture.test.ts
git commit -m "feat(parity): the second science.identity.v1 fixture, typed components compared on bytes and digest"
```

---

### Task 14: The reproduction driver under the new contract

**Files:**
- Modify: `python/tools/reproduction/hold.py`, `python/tools/reproduction/vocabulary.py`, `python/tests/test_reproduction_driver.py`

**Interfaces:**
- Consumes: `shipped_base_contract()`, `open_corpus(..., profile=)` (Task 7), the `empirical-observation` schema (Task 2).

- [ ] **Step 1: Write the failing test**

Append to `python/tests/test_reproduction_driver.py`:

```python
def test_the_hold_step_declares_a_locator_and_the_bound_actor():
    from reproduction.authority import ACTOR
    from reproduction.hold import dataset_record

    node, _ = dataset_record(name="f.gz", digest="sha256:" + "c" * 64, title="dataset:gse179929", accession="GSE179929")
    assert node.facets["empirical-observation"] == {"locator": "accession:GSE179929", "attested_by": ACTOR}
```

- [ ] **Step 2: Run to verify failure** — `cd python && PYTHONPATH=tools uv run --frozen pytest tests/test_reproduction_driver.py -q -k locator` → TypeError (`accession`).

- [ ] **Step 3: Amend the driver**

In `hold.py`, change `dataset_record(*, name, digest, title, facet)` to `dataset_record(*, name, digest, title, accession)` writing `empirical_observation={"locator": f"accession:{accession}", "attested_by": AUTHORITY.actor}`; in `main` call it with `accession=target["dataset_id"].split(":", 1)[1].upper()` and replace the P2 comment and the `findings.record(3, "design-gap", ...)` line with `findings.record(3, "closed", "empirical-observation payload validated under the facet-contracts design §6; the authored placeholder is refused (F1)")` — check `findings.record`'s accepted classes in `reproduction/findings.py` and use the one for a closed finding, adding it if the driver has none. In `vocabulary.py`, `base()` returns `shipped_base_contract()` (delete the `BASE` path constant). `world.py::open_writer` passes `profile=profile()`.

- [ ] **Step 4: Run, lint, commit**

`cd python && PYTHONPATH=tools uv run --frozen pytest tests/test_reproduction_driver.py -q && uv run --frozen ruff check . && uv run --frozen pyright`

```bash
git add python/tools/reproduction python/tests/test_reproduction_driver.py
git commit -m "chore(reproduction): the hold step declares an accession locator under the bound actor"
```

A fresh reproduction run (design §13's last line) is performed at discharge, not here: `rm -rf` of the old `.mm30-reproduction/` is the user's call, since the record cites its corpus.

---

### Task 15: The cut-20 discharge surface — durable acceptance, the N2 arms, the runner

**Files:**
- Create: `python/tests/acceptance/test_facet_acceptance.py`, `python/tests/acceptance/n2_arms_cut20.py`, `python/tests/acceptance/test_n2_cut20.py`, `python/tools/cut20_acceptance.py`
- Modify: `python/tests/acceptance/durable_fixture.py` (profile-aware `open_corpus`)

**Interfaces:**
- Consumes: every name Tasks 1–14 produced; the cut document's test names (Task 0).
- Produces: `CUT20_ARMS`, `DECLARATION_UNITS`, `unit_of`, `CO_CITED` in the arms module, in cut 18's shape.

- [ ] **Step 1: The durable acceptance module**

Write `test_facet_acceptance.py` with one test per cut-§3 unit, each re-running the corresponding unit test's construction over an `open_corpus` writer on the certified tuple (`durable_fixture.py` provides the root, authority and now `profile=BASE`), asserting the same refusal or finding and, where the row says so, the chain and store unchanged: compare `{p.relative_to(root): sha256(p.read_bytes()).hexdigest() for p in root.rglob("*") if p.is_file()}` before and after (contents, not paths), and the chain head through the durable fixture's log read (`durable_fixture.py` exposes the `read_chain`-backed head the deletion acceptance uses; reuse that helper by name). Names, verbatim from the cut: `test_d2_interpretation_is_separable_from_identity_durably`, `test_d4_one_kindspec_per_kind_compiled_from_the_profile`, `test_d5_manifest_pin_projection_and_refusals`, `test_d8_contributions_compose_without_collision`, `test_d9_practices_carry_no_vocabulary`, `test_d10_facets_stay_facets`, `test_g5_no_divergence_kind_exists`, `test_f1_payload_contract_enforced_at_every_entry`, `test_f2_bearer_invariant_over_resulting_state`, `test_f3_attestation_bound_and_preserved`, `test_f4_eligibility_reads_the_validity_predicate`, `test_f5_profile_agreement_rechecked_under_the_lock`, `test_f6_dataset_revision_changes_interpretation_and_prose_only`, `test_f7_retrieval_resolves_or_refuses`, `test_f8_every_builder_facet_is_declared`, `test_d1_installed_nodes_takes_no_domain_argument`, `test_boundary_no_read_entry_point_gained_an_argument`. For D4 assert `Registry.register` was called exactly once per compiled kind during `compile_profile` (the monkeypatched counting spy from `test_facet_validation.py`, over `shipped_base_contract()` and the durable fixture's coordination contract), that `validate_document` admits every world, prose and coordination kind and refuses `divergence`, and — the "no second authored per-kind artifact" arm — a static scan that `python/src/beliefs/stored.py` contains no literal `WORLD_KINDS = (` tuple (`"WORLD_KINDS: tuple[str, ...] = tuple(" in source`). For D10 inspect `CorpusWriter`'s public methods by signature: none takes a parameter named `facet` or `facet_key`, and `retract`/`supersede` take records/refs only. For D1 use `inspect.signature` over `Registry.register`, `KindSpec`, `ShapeSpec` in the installed `nodes` package: no parameter named `domain`, `contract` or `vocabulary`. For F8 iterate every `stored.*_node` builder with a minimal valid argument set (copy the argument sets from `test_stored.py`) plus the writer's coordination node and `profile.validate_document` each.

- [ ] **Step 2: The arms**

`n2_arms_cut20.py` (both copies identical, as cut 18 keeps them): one `Arm` per sabotage in design §10, each with `module`, an exact `before`/`after` from the final source, and `checks` naming the acceptance test. The nine sabotages: the validator accepting unknown keys (`facets.py`: delete the `unknown` refusal); the producer read dropped (`acquisition.py`: `producers = ()`); the attestation comparison skipped (`corpus.py`: `if not provenance and payload.get("attested_by") != self._authority.actor` → `if False`); the pin recheck skipped under the lock (`corpus.py`: `_require_pins_agree` returns immediately); validity replaced by presence (`corpus.py` eligibility loop: `reason = validity_refusal(...)` → `reason = None if stored.EMPIRICAL_OBSERVATION_FACET in view.get(dataset_ref).facets else "absent"`); a builder writing an undeclared key (`stored.py`: `dataset_node` adds `facets["provenance"] = {}`); the digest comparison (`identity/v1.py`'s `digest` hashing the canonical bytes without the domain prefix — bytes unchanged, every digest wrong — with the check `test_identity_parity_fixture.py::test_bytes_and_digest_agree`, which fails only through its digest assertion); the domain parser **accepting** `kinds:` and `relations:` (`domain.py`: Task 3 places the explicit refusal loop immediately above the `_fields(root, _CONTRACT_FIELDS, frozenset({"description", "facets"}), source)` call, so one contiguous sabotage deletes the loop *and* widens the optional set to `frozenset({"description", "facets", "kinds", "relations"})` — the mutant then parses a domain contract carrying `kinds:` and ignores it, and the check `test_domain_contract.py::TestDomainFacets::test_a_domain_declaring_kinds_or_relations_is_refused` fails because nothing refuses); a domain facet attaching to an undeclared kind accepted at compile (`profile.py`: delete that `ProfileError`); `WORLD_RELATIONS` widened (`stored.py`: drop the `group == "world"` filter); the duplicate-key loader replaced (`document.py`: `Loader=yaml.SafeLoader`); coverage in authored order (`profile.py`: `tuple(k for ...)` without `sorted`). `DECLARATION_UNITS` is the 18-tuple of cut §4.

- [ ] **Step 3: The runner and the freeze pin**

`tools/cut20_acceptance.py`: copy `cut18_acceptance.py`, rename 18→20, `PREFIX_RUNNERS = ("cut19_acceptance.py",)`, `PHASE_MODULES = ("test_facet_acceptance.py", "test_n2_cut20.py")`, the env range `range(4, 21)`. `test_n2_cut20.py`: copy `test_n2_cut18.py`'s structure; `FROZEN_CUT = .../2026-09-05-conformance-cut-20.md`; `CUT20_FREEZE_COMMIT` = Task 0's short hash; `CUT20_FROZEN_SHA256` = `sha256sum docs/designs/2026-09-05-conformance-cut-20.md` at that commit (`git show <hash>:docs/designs/2026-09-05-conformance-cut-20.md | sha256sum`); no renumbering substitutions.

- [ ] **Step 4: Run portably where possible, then commit**

`cd python && uv run --frozen pytest tests/acceptance/test_facet_acceptance.py -q` — on a machine without the certified tuple this errors with `CapabilityUnavailable`, which is the expected fail-closed result, not a skip; report it as such. The N2 audit and the runner are discharged on the certified tuple after main carries cut 19 (`git merge main` into the lane first; resolve toward main on the shared files roadmap rule 3 names).

```bash
git add python/tests/acceptance python/tools/cut20_acceptance.py
git commit -m "test(cut20): the durable acceptance module, the N2 arms and the aggregate runner"
```

---

### Task 16: Documentation amendments, the guide, the ledger row, and the task close

**Files:**
- Modify: `docs/designs/2026-08-02-epistemic-kernel-design.md` (§4.1, limitation 8, §11), `2026-08-02-computation-reproducibility-design.md` (§13), `2026-08-04-domain-extension-boundary-design.md` (§3.4, §6, §12), `2026-08-18-composition-root-adapter-design.md` (§5), `2026-08-19-family-adapters-design.md` (revise), `2026-09-04-write-permits-design.md` (limitation 2), `docs/guide/foundations.md`, `glossary.md`, `open-questions.md`, `contracts-and-adoption.md`, `python/src/beliefs/stored.py` (docstring), `ts/README.md`, `docs/designs/2026-08-03-redesign-adoption-ledger.md` (current-state row for `domain-boundary`), `docs/plans/2026-08-29-implementation-roadmap.md` (row 3 split, lane status)

Each amendment is a **dated note appended in place**, never an edit of frozen text, in the style the corpus already uses (`> **Amended 2026-09-05** (facet-contracts design §N). …`). Contents, one per file:

- Kernel §4.1: what "declared acquisition boundary" means (design §6, three sentences) and the bearer invariant; limitation 8 narrowed to the locator's truth and the observation's nature; §11's empirical-observation bullet struck through with `**CLOSED 2026-09-05** by the facet-contracts design §6` and a new bullet for lineage-inherited standing (design §14).
- Computation §13 first bullet: closed by citation.
- D §3.4: "the payload schema travels with it — now literally, as the base contract's `facets:` entry"; §6: kinds, relations and facets compiled (inventory widened again); §12: parity for domains answered (parse-only TypeScript, Python validation); distribution still open.
- Adapter §5: coverage is contract-declared, never stored per node; the per-node defence unchanged.
- Family-adapters: `revise` gains the dataset arm (design §5.3).
- Write-permits limitation 2: closed by ruling, domains mint no kinds, `KIND_ACTS` unchanged.
- Guide: `foundations.md` "Contracts compile into profiles" gains two sentences on facet declarations and the shipped base; `glossary.md`'s Facet entry cites the design; `open-questions.md` foundations: the empirical-observation bullet marked closed with the citation, a new bullet for lineage-inherited standing, and under contracts-and-adoption a bullet for relation endpoint enforcement; `contracts-and-adoption.md` current state: one sentence on cut 20's freeze status (Task 0 wrote it; update to "discharged" only at discharge).
- `stored.py` docstring: "declared by the base contract and compiled" replaces "named in code".
- `ts/README.md`: one line — "It parses `kinds`, `relations` and `facets` declarations with the same structural refusals and validates no facet payload; validation is Python-primary, sited with compilation (facet-contracts §7.2)."
- Ledger current-state `domain-boundary` row: "slice 1, the facet-contracts design dated 2026-09-05, frozen as cut 20"; roadmap row 3: split into slice 1 (this design) and slice 2 (the biology pack), lane status `open (.worktrees/domain-boundary)`.

- [ ] **Step 1: Make the amendments**, then run the guard: `cd python && uv run --frozen pytest tests/test_designs_corpus.py -q` and the guide checker `uv run --frozen python tools/check_guide.py`.

- [ ] **Step 2: Close the finding task and note the goal**

```bash
tasks done beliefs-d245a9 "decided and enforced: locator + attested_by + reserved retrieval, validated at every seam (facet-contracts design §6, F1)"
tasks note beliefs-bc3aff "slice 1 (facet contracts, cut 20) implemented on feat/domain-boundary; slice 2 (biology pack) next"
tasks check
```

- [ ] **Step 3: Commit**

```bash
git add docs python/src/beliefs/stored.py ts/README.md tasks
git commit -m "docs(domain): amend the designs and guide for the facet-contracts slice; close the payload-contract finding"
```

Then the full gates one last time from both `python/` and `ts/`, and `git log --oneline main..HEAD` as the lane's record for the results document, which is written at discharge.
