# Estimand Typing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Type the estimand, applicability, estimate and uncertainty end to end — base-contract grammar, domain `estimands:` declarations, typed spec and assessment facets, boundary and audit checks, the consulted walk, the mm30 re-run — and discharge table Q at a conformance cut.

**Architecture:** The base contract gains `estimand_grammar` (three closed structural sets); a domain contract gains an `estimands:` table keyed by operator that names four sorts; `beliefs/estimand.py` builds an opaque `Estimand` against a typed `Claim` exactly as `claim.py` builds a `Claim` against a profile, and `decode.py` restores one from stored bytes; `spec.py`, `record.py`, `assess.py` and `stored.py` carry the typed members; `corpus.py` and `audit.py` check the spec's estimand against its target record; `consulted.py` reaches the estimand's contracts. The reproduction corpus is recreated under a successor `mm30` contract, never migrated.

**Tech Stack:** Python 3.11+ (`uv run --frozen` from `python/`), pytest, `nodes.core`, TypeScript/vitest under `ts/`, the N2 harness (`python/tests/test_n2.py`), `tasks`.

**Spec:** `docs/superpowers/specs/2026-09-12-estimand-typing-design.md` (cleared for planning 2026-09-12, review log §15).

## Global Constraints

- Work in the worktree `.worktrees/estimand-typing` (branch `design/estimand-typing`). Every path below is relative to the Beliefs repository root; paths shown to the user are prefixed with the worktree directory.
- **The lane opens first, and the cut freezes before its code exists.** Task 0 admits the lane under roadmap concurrency rule 6 (at most two kernel lanes while the success criterion is unmet; an off-path lane only when no on-path lane is startable) and freezes the cut document by dated commit. No later task starts until Task 0's freeze commit is in the branch. Every task rewrites a surface the lane owns; Tasks 6–9 additionally rewrite `decode.py`, `corpus.py`, `evaluation.py` and `stored.py` (spec §10.5), and the later merge resolves toward the earlier lane.
- Every Python command runs from `python/` as `uv run --frozen …`; `pytest` is bare (`addopts` carries `-q` and `--ignore=tests/acceptance`; an acceptance module runs only when named). Count claims quote the summary line.
- The shipped base contract is authored at `contracts/science/CONTRACT.yaml`; `python/src/beliefs/contracts/science/CONTRACT.yaml` is its byte-identical packaged copy, held equal by a test — edit the first, copy to the second.
- Frozen declarations and cut bodies through cut 26 stay byte-exact. No reader coerces a pre-grammar record (spec decision 10).
- Every closed set is declared in the contract and matched in code; every refusal names its position; `Estimand` has no public constructor (spec Q3).
- `science.belief.v1` reads nothing this plan adds; P1–P9 stay green at every commit.
- Conventional commits, no attribution trailers. `tasks check` before every commit; the pre-commit hook runs the gate. Every commit message names the Q row(s) it serves.

---

## File map

| File | Responsibility |
| --- | --- |
| `contracts/science/CONTRACT.yaml`, `python/src/beliefs/contracts/science/CONTRACT.yaml` | `estimand_grammar` (Task 1) |
| `python/src/beliefs/contract/base.py` | `EstimandGrammar`, parsed and refused (Task 1) |
| `python/src/beliefs/contract/domain.py` | `EstimandDecl`, `_parse_estimand_decl`, `DomainContract.estimands`, `_declarations()` entries (Task 2) |
| `fixtures/contracts/testing.yaml` | three fixture sorts and two `estimands:` entries, shared with TypeScript (Task 2) |
| `python/src/beliefs/profile.py` | `CompiledEstimandDecl`, `ProfileSpec.estimands`, `ProfileSpec.estimand()`, projection (Task 3) |
| `ts/src/contract.ts`, `ts/src/profile.ts` | the same declarations parsed and compiled, no payload validation (Tasks 1–3) |
| `python/src/beliefs/errors.py` | `EstimandError` family; `PreGrammarRecord` (Tasks 4, 6) |
| `python/src/beliefs/resolution.py` | `ReferentPosition.estimand()` (Task 4) |
| `python/src/beliefs/estimand.py` | values, `build_estimand`, `build_applicability`, projections, `commensurable`, `co_scoped` (Task 4) |
| `python/src/beliefs/decode.py` | `WireEstimand`, `decode_estimand`, `estimand_from_stored`, `applicability_from_stored` (Task 5) |
| `python/src/beliefs/spec.py` | typed `SpecDraft`/`FrozenSpec`, `ESTIMAND_GRAMMAR` member, `restore(..., profile=)`, `revise` (Task 6) |
| `python/src/beliefs/stored.py` | `analysis_spec_value(node, *, profile)`, typed `assessment_node`/`assessment_value` (Tasks 6, 7) |
| `python/src/beliefs/record.py`, `python/src/beliefs/assess.py` | typed `AssessmentValue`; constructor checks on rule output (Task 7) |
| `python/src/beliefs/corpus.py`, `python/src/beliefs/audit.py` | `_refuse_estimand_target_mismatch`, `check_spec_target`, pre-grammar codes (Task 8) |
| `python/src/beliefs/consulted.py`, `evaluation.py`, `belief.py`, `succession.py`, `replay.py` | the estimand walk; `profile` threaded to the readers (Task 9) |
| `python/tools/reproduction/*` | successor `mm30` contract, held lists, typed spec, recreated corpus, fresh-process restore (Task 10) |
| `python/tests/test_estimand_declarations.py`, `test_estimand.py`, `test_estimand_decode.py`; edits to `test_spec.py`, `test_assess.py`, `test_records.py`, `test_consulted.py`, `test_audit.py`, `fixtures_cut3.py` | unit coverage per task |
| `python/tests/acceptance/test_estimand_acceptance.py`, `python/tests/n2_arms_cut<N>.py`, `python/tests/acceptance/test_n2_cut<N>.py`, `python/tools/cut<N>_acceptance.py` | Q1–Q10 acceptance, the sabotage declaration, the guard, the runner (Task 11) |
| `docs/designs/…-conformance-cut-<N>.md`, `docs/plans/…-conformance-cut-<N>-results.md`, the amended designs, guide, glossary, ledger, roadmap | freeze, discharge, amendments (Tasks 11, 12) |

`<N>` is claimed at freeze (concurrency rule 1): the next unclaimed cut number across every worktree at that moment, chained after the highest-numbered discharged runner.

---

### Task 0: Open the lane and freeze the cut

**Files:**
- Create: `docs/designs/<date>-conformance-cut-<N>.md`
- Move: `docs/superpowers/specs/2026-09-12-estimand-typing-design.md` → `docs/designs/2026-09-12-estimand-typing-design.md` (`git mv`)
- Modify: `python/tests/test_designs_corpus.py` (`GUARANTEE_TABLES["Q"]`, `TABLE_OWNERS["Q"]`), the designs README row total and list

**Interfaces:**
- Produces: the cut number `<N>`, the freeze commit `CUT<N>_FREEZE_COMMIT` and the cut document's SHA-256, both pinned by Task 11's guard; the lane's admission recorded on `beliefs-59f846`.

- [ ] **Step 1: Admit the lane under rule 6**

Run `tasks prime --project beliefs` and read the roadmap's lane table. The lane opens only if fewer than two kernel lanes are open **and** no on-path lane is startable (the `world-read` head is either in flight or blocked). Record the reading in a task note — `tasks note beliefs-59f846 "lane admitted under rule 6: <open lanes>, <on-path state>"` — and `tasks start beliefs-59f846`. If the rule refuses, stop here: the plan waits, and nothing below starts.

- [ ] **Step 2: Claim the cut number**

Run `git worktree list` and `ls <each worktree>/docs/designs/*conformance-cut-*.md`; `<N>` is the next number unclaimed in any worktree (concurrency rule 1). Read the highest-numbered **discharged** runner in `python/tools/cut*_acceptance.py` for Task 11's `PREFIX_RUNNERS` (rule 5).

- [ ] **Step 3: Write and freeze the cut document**

Write `docs/designs/<date>-conformance-cut-<N>.md` on cut 26's shape: §1 what this cut is; §2 the boundary (the files this plan names); §3 selection — declaration units `Q1`–`Q10`, single-homed, every clause selected only when its source mutation and every named check run inside §2; §4 accounting; §5 N2 and acceptance obligations (the mechanisms of spec §10.3, one arm each — the `before` blocks are written in Task 11 against the tree that exists then, and the accounting freezes there); §6 second reader; §7 limitations (spec §13, restated). `git mv` the design spec into `docs/designs/`, register `"Q": [f"Q{i}" for i in range(1, 11)]` and its owner, update the README, and run `uv run --frozen pytest tests/test_designs_corpus.py` green. Commit: `docs(cut): freeze conformance cut <N>, estimand typing` — this is the dated freeze commit, made before any code below exists.

---

### Task 1: The base contract's `estimand_grammar` — Python, TypeScript, both copies

**Files:**
- Modify: `contracts/science/CONTRACT.yaml` (after the `claim_grammar:` block), copy to `python/src/beliefs/contracts/science/CONTRACT.yaml`
- Modify: `python/src/beliefs/contract/base.py:74-75` (field sets), the `ClaimGrammar` block, `parse_base_contract`
- Modify: `python/src/beliefs/profile.py` (`ProfileSpec.estimand_grammar`, `_projection`, `compile_profile`)
- Modify: `ts/src/contract.ts` (`BaseContract.estimandGrammar`, `parseBaseContract`), `ts/src/profile.ts` (`ProfileSpec.estimandGrammar`)
- Test: `python/tests/test_base_contract.py`, `ts/tests/declarations.test.ts`

**Interfaces:**
- Produces: `EstimandGrammar(version: int, contrast_kinds: tuple[str, ...], scales: tuple[str, ...], uncertainty_kinds: tuple[str, ...])` at `beliefs.contract.base`; `BaseContract.estimand_grammar`; `ProfileSpec.estimand_grammar`; the constant `ESTIMAND_GRAMMAR = "science.estimand.v1"` at `beliefs.contract.base`.

- [ ] **Step 1: Write the failing tests**

Append to `python/tests/test_base_contract.py`:

```python
class TestEstimandGrammar:
    def test_the_shipped_base_declares_the_three_closed_sets(self, base_contract):
        grammar = base_contract.estimand_grammar
        assert grammar.version == 1
        assert grammar.contrast_kinds == ("levels", "continuous")
        assert grammar.scales == ("additive", "multiplicative")
        assert grammar.uncertainty_kinds == ("interval", "standard-error")

    def test_a_base_contract_lacking_the_grammar_is_refused(self, base_contract_path):
        import yaml
        from beliefs.contract.base import parse_base_contract
        from beliefs.errors import MalformedContract

        document = yaml.safe_load(base_contract_path.read_text(encoding="utf-8"))
        del document["estimand_grammar"]
        with pytest.raises(MalformedContract, match="estimand_grammar"):
            parse_base_contract(document, source="<no-grammar>")

    def test_another_tag_encoding_is_refused(self, base_contract_path):
        import yaml
        from beliefs.contract.base import parse_base_contract
        from beliefs.errors import MalformedContract

        document = yaml.safe_load(base_contract_path.read_text(encoding="utf-8"))
        document["estimand_grammar"]["tag_encoding"] = "science.identity.v2"
        with pytest.raises(MalformedContract, match="tag_encoding"):
            parse_base_contract(document, source="<encoding>")

    def test_a_duplicate_tag_in_a_closed_set_is_refused(self, base_contract_path):
        import yaml
        from beliefs.contract.base import parse_base_contract
        from beliefs.errors import TagCollision

        document = yaml.safe_load(base_contract_path.read_text(encoding="utf-8"))
        document["estimand_grammar"]["scales"] = ["additive", "additive"]
        with pytest.raises(TagCollision):
            parse_base_contract(document, source="<dup>")

    def test_the_grammar_enters_the_compiled_identity(self, base_contract_path):
        import yaml
        from beliefs.contract.base import parse_base_contract
        from beliefs.profile import compile_profile

        document = yaml.safe_load(base_contract_path.read_text(encoding="utf-8"))
        before = compile_profile(parse_base_contract(document, source="<a>"), []).compiled_identity
        document["estimand_grammar"]["scales"] = ["additive", "multiplicative", "ordinal"]
        after = compile_profile(parse_base_contract(document, source="<b>"), []).compiled_identity
        assert before != after
```

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run --frozen pytest tests/test_base_contract.py -k EstimandGrammar`
Expected: 5 failed — `AttributeError: 'BaseContract' object has no attribute 'estimand_grammar'` and, for the refusal tests, no `MalformedContract` raised because the parser ignores… no: `_exact_fields` refuses the unknown key `estimand_grammar` on the shipped document, so `base_contract` fixture setup errors with `MalformedContract: unknown field`. Either way every test in the class is red.

- [ ] **Step 3: Declare the grammar in the contract**

In `contracts/science/CONTRACT.yaml`, after the `layers: [causal, structural, statistical, methodological]` line, add:

```yaml

# --- estimand grammar (estimand-typing design §3.1) ---------------------------
# Three closed *structural* sets: each member is defined by an operation the
# kernel performs — a `levels` contrast requires two bound levels, an
# `additive` scale compares by difference, an `interval` carries bounds and a
# level. Identification classes and measured quantities are vocabulary and are
# declared by domain contracts (§5), never here.
estimand_grammar:
  version: 1
  tag_encoding: science.identity.v1
  contrast_kinds: [levels, continuous]
  scales: [additive, multiplicative]
  uncertainty_kinds: [interval, standard-error]
```

Then `cp contracts/science/CONTRACT.yaml python/src/beliefs/contracts/science/CONTRACT.yaml`.

- [ ] **Step 4: Parse it in Python**

In `python/src/beliefs/contract/base.py`:

```python
_CONTRACT_FIELDS = frozenset({"contract", "version", "claim_grammar", "estimand_grammar", "kinds", "relations", "facets"})
_GRAMMAR_FIELDS = frozenset({"version", "tag_encoding", "quantifiers", "polarities", "sign_inapt_tag", "layers"})
_ESTIMAND_GRAMMAR_FIELDS = frozenset({"version", "tag_encoding", "contrast_kinds", "scales", "uncertainty_kinds"})
ESTIMAND_GRAMMAR = "science.estimand.v1"


@dataclass(frozen=True)
class EstimandGrammar:
    """The closed structural sets an estimand draws from (estimand-typing §3.1).

    Structural, not vocabulary: each tag names an operation the kernel performs
    on the value that carries it, which is what keeps these three sets out of
    the survey's admission rule the way quantifiers are kept out."""

    version: int
    contrast_kinds: tuple[str, ...]
    scales: tuple[str, ...]
    uncertainty_kinds: tuple[str, ...]

    def projection(self) -> dict[str, object]:
        return {
            "version": self.version,
            "contrast_kinds": sorted(self.contrast_kinds),
            "scales": sorted(self.scales),
            "uncertainty_kinds": sorted(self.uncertainty_kinds),
        }
```

Add `estimand_grammar: EstimandGrammar` to `BaseContract`'s fields (beside `claim_grammar`) and to `_parsed`'s keyword list. In `parse_base_contract`, after `claim_grammar = ClaimGrammar(...)`:

```python
    estimand_where = f"{source}: estimand_grammar"
    estimand = _mapping(root["estimand_grammar"], estimand_where)
    _exact_fields(estimand, _ESTIMAND_GRAMMAR_FIELDS, estimand_where)
    if estimand["tag_encoding"] != TAG_ENCODING:
        raise MalformedContract(
            f"{estimand_where}: tag_encoding is {estimand['tag_encoding']!r}; this implementation encodes tags only "
            f"under {TAG_ENCODING!r} (estimand-typing §3.1)."
        )
    estimand_grammar = EstimandGrammar(
        version=_positive_int(estimand["version"], f"{estimand_where}: version"),
        contrast_kinds=_closed_set(estimand["contrast_kinds"], f"{estimand_where}: contrast_kinds"),
        scales=_closed_set(estimand["scales"], f"{estimand_where}: scales"),
        uncertainty_kinds=_closed_set(estimand["uncertainty_kinds"], f"{estimand_where}: uncertainty_kinds"),
    )
```

and pass `estimand_grammar=estimand_grammar` to `BaseContract._parsed`. Export `EstimandGrammar` and `ESTIMAND_GRAMMAR` in `__all__`.

- [ ] **Step 5: Carry it on the profile**

In `python/src/beliefs/profile.py`: import `EstimandGrammar`; add `estimand_grammar: EstimandGrammar` to `ProfileSpec`'s fields after `claim_grammar`; pass `estimand_grammar=base.estimand_grammar` in `compile_profile`'s `_compiled(...)` call; give `_projection` a new keyword `estimand_grammar: EstimandGrammar` and emit `projection["estimand_grammar"] = estimand_grammar.projection()` right after the `claim_grammar` entry; pass it from both `ProfileSpec.projection()` and `compile_profile`.

- [ ] **Step 6: Run the tests**

Run: `uv run --frozen pytest tests/test_base_contract.py tests/test_profile.py tests/test_domain_contract.py`
Expected: all pass; the summary line reports 0 failed.

- [ ] **Step 7: TypeScript**

In `ts/src/contract.ts`: add `export interface EstimandGrammar { readonly version: number; readonly contrastKinds: readonly string[]; readonly scales: readonly string[]; readonly uncertaintyKinds: readonly string[]; }`; add `readonly estimandGrammar: EstimandGrammar` to `BaseContract` (frozen in the constructor like `claimGrammar`); in `parseBaseContract`, extend the top-level `exactFields` list with `"estimand_grammar"` and add after the claim-grammar block:

```ts
  const estimandDocument = mapping(document.estimand_grammar, `${source}.estimand_grammar`);
  exactFields(
    estimandDocument,
    ["version", "tag_encoding", "contrast_kinds", "scales", "uncertainty_kinds"],
    [],
    `${source}.estimand_grammar`,
  );
  if (estimandDocument.tag_encoding !== TAG_ENCODING) {
    throw new MalformedContract(
      `${source}.estimand_grammar.tag_encoding: this implementation carries ${TAG_ENCODING}, the contract names ${JSON.stringify(estimandDocument.tag_encoding)}`,
    );
  }
  const estimandGrammar: EstimandGrammar = {
    version: positiveInt(estimandDocument.version, `${source}.estimand_grammar.version`),
    contrastKinds: closedSet(estimandDocument.contrast_kinds, `${source}.estimand_grammar.contrast_kinds`),
    scales: closedSet(estimandDocument.scales, `${source}.estimand_grammar.scales`),
    uncertaintyKinds: closedSet(estimandDocument.uncertainty_kinds, `${source}.estimand_grammar.uncertainty_kinds`),
  };
```

and pass `estimandGrammar` into `new BaseContract(MINT, {...})`. In `ts/src/profile.ts` add `readonly estimandGrammar: EstimandGrammar` to `ProfileSpec`, assigned from `base.estimandGrammar` in `compileProfile`. Every test string in `ts/tests/*.test.ts` that builds a base contract inline (`const BASE = \`…\``) gains the same five-line `estimand_grammar:` block after `layers:`.

Append to `ts/tests/declarations.test.ts` inside the base-contract `describe`:

```ts
  it("declares the estimand grammar's three closed sets (estimand-typing §3.1)", () => {
    expect(base.estimandGrammar.contrastKinds).toEqual(["levels", "continuous"]);
    expect(base.estimandGrammar.scales).toEqual(["additive", "multiplicative"]);
    expect(base.estimandGrammar.uncertaintyKinds).toEqual(["interval", "standard-error"]);
  });
  it("refuses a base contract without the estimand grammar", () => {
    const missing = SHIPPED.replace(/estimand_grammar:[\s\S]*?uncertainty_kinds: \[interval, standard-error\]\n/, "");
    expect(() => parseBaseContract(missing, "<missing>")).toThrow(/estimand_grammar/);
  });
```

Run: `cd ts && npm test`
Expected: all vitest suites pass.

- [ ] **Step 8: Commit**

```bash
git add contracts/science/CONTRACT.yaml python/src/beliefs/contracts/science/CONTRACT.yaml python/src/beliefs/contract/base.py python/src/beliefs/profile.py ts/src/contract.ts ts/src/profile.ts python/tests/test_base_contract.py ts/tests
git commit -m "feat(contract): declare the estimand grammar in the base contract (Q1)"
```

---

### Task 2: A domain contract's `estimands:` table — Python, the fixture, TypeScript

**Files:**
- Modify: `python/src/beliefs/contract/domain.py:59-63` (field sets), the declaration classes, `parse_domain_contract`, `DomainContract` fields and `_declarations()`
- Modify: `fixtures/contracts/testing.yaml`
- Modify: `ts/src/contract.ts` (`EstimandDecl`, `DomainContract.estimands`, `parseDomainContract`)
- Test: `python/tests/test_estimand_declarations.py` (new), `ts/tests/contract-scope.test.ts`

**Interfaces:**
- Produces: `EstimandDecl(operator: str, level_sorts: Mapping[str, str], measure_sort: str, identification_sort: str, conditioning_sort: str)` with `schema_projection()`; `DomainContract.estimands: Mapping[str, EstimandDecl]` keyed by the operator's local name; the `_declarations()` key `estimand:<operator>`.

- [ ] **Step 1: Extend the shared fixture**

In `fixtures/contracts/testing.yaml`, add three sorts under `sorts:`:

```yaml
  measure:
    vocabulary: { namespace: EX, release: "2026-01-01" }
  identification:
    vocabulary: { namespace: EX, release: "2026-01-01" }
  level:
    vocabulary: { namespace: EX, release: "2026-01-01" }
```

and, after `operators:`, a new top-level table:

```yaml
# Estimand declarations (estimand-typing design §5.1): which sorts fill the
# kernel's estimand structure at each operator. `subtype-of` and `measured-by`
# deliberately declare none, so a spec targeting a claim at them refuses.
estimands:
  affects:
    level_sorts: { "0": level }
    measure_sort: measure
    identification_sort: identification
    conditioning_sort: entity
  correlates-with:
    level_sorts: {}
    measure_sort: measure
    identification_sort: identification
    conditioning_sort: entity
```

- [ ] **Step 2: Write the failing tests**

Create `python/tests/test_estimand_declarations.py`:

```python
"""The `estimands:` declaration class (estimand-typing design §5, Q2)."""

import copy

import pytest

from beliefs.contract import domain
from beliefs.errors import MalformedContract, SuccessionViolation


@pytest.fixture()
def parse(base_contract):
    def _parse(document, source="<test>", predecessor=None):
        return domain.parse_domain_contract(document, source=source, base=base_contract, predecessor=predecessor)

    return _parse


def test_the_fixture_declares_two_estimands(parse, testing_document):
    contract = parse(testing_document)
    assert set(contract.estimands) == {"affects", "correlates-with"}
    decl = contract.estimands["affects"]
    assert decl.level_sorts == {"0": "level"}
    assert (decl.measure_sort, decl.identification_sort, decl.conditioning_sort) == ("measure", "identification", "entity")


def test_a_key_naming_an_undeclared_operator_is_refused(parse, testing_document):
    document = copy.deepcopy(testing_document)
    document["estimands"]["regulates"] = document["estimands"]["affects"]
    with pytest.raises(MalformedContract, match="regulates"):
        parse(document)


def test_a_level_sort_index_outside_the_arity_is_refused(parse, testing_document):
    document = copy.deepcopy(testing_document)
    document["estimands"]["affects"]["level_sorts"] = {"2": "level"}
    with pytest.raises(MalformedContract, match="Fin"):
        parse(document)


def test_a_non_decimal_level_sort_key_is_refused(parse, testing_document):
    document = copy.deepcopy(testing_document)
    document["estimands"]["affects"]["level_sorts"] = {"first": "level"}
    with pytest.raises(MalformedContract, match="slot index"):
        parse(document)


def test_an_arity_zero_operator_admits_no_declaration(parse, testing_document):
    document = copy.deepcopy(testing_document)
    document["operators"]["holds"] = {"arity": 0, "arg_sorts": [], "sign_apt": False, "layers": ["structural"], "dimensions": []}
    document["estimands"]["holds"] = {"level_sorts": {}, "measure_sort": "measure", "identification_sort": "identification", "conditioning_sort": "entity"}
    with pytest.raises(MalformedContract, match="arity 0"):
        parse(document)


def test_an_unknown_field_is_refused(parse, testing_document):
    document = copy.deepcopy(testing_document)
    document["estimands"]["affects"]["retired"] = True
    with pytest.raises(MalformedContract, match="unknown field"):
        parse(document)


def test_an_undeclared_sort_is_refused_at_parse(parse, testing_document):
    document = copy.deepcopy(testing_document)
    document["estimands"]["affects"]["measure_sort"] = "assay"
    with pytest.raises(MalformedContract, match="assay"):
        parse(document)


def test_the_projection_sorts_level_sort_keys(parse, testing_document):
    document = copy.deepcopy(testing_document)
    document["operators"]["affects"]["arity"] = 2
    document["estimands"]["affects"]["level_sorts"] = {"1": "level", "0": "level"}
    reordered = copy.deepcopy(document)
    reordered["estimands"]["affects"]["level_sorts"] = {"0": "level", "1": "level"}
    assert parse(document).estimands["affects"].schema_projection() == parse(reordered).estimands["affects"].schema_projection()
    assert parse(document).content_identity == parse(reordered).content_identity


class TestSuccession:
    def _successor(self, document, predecessor):
        successor = copy.deepcopy(document)
        successor["lineage"] = {"successor": predecessor.content_identity}
        return successor

    def test_adding_a_declaration_for_an_existing_operator_is_accepted(self, parse, testing_document):
        prior_document = copy.deepcopy(testing_document)
        del prior_document["estimands"]["correlates-with"]
        prior = parse(prior_document)
        successor = self._successor(testing_document, prior)
        contract = parse(successor, predecessor=prior)
        assert "correlates-with" in contract.estimands
        assert contract.operators["correlates-with"].schema_projection() == prior.operators["correlates-with"].schema_projection()

    @pytest.mark.parametrize("member,value", [
        ("level_sorts", {}),
        ("measure_sort", "entity"),
        ("identification_sort", "entity"),
        ("conditioning_sort", "outcome"),
    ])
    def test_changing_any_member_is_a_redefinition(self, parse, testing_document, member, value):
        prior = parse(testing_document)
        successor = self._successor(testing_document, prior)
        successor["estimands"]["affects"][member] = value
        with pytest.raises(SuccessionViolation, match="estimand:affects"):
            parse(successor, predecessor=prior)

    def test_dropping_a_declaration_is_refused(self, parse, testing_document):
        prior = parse(testing_document)
        successor = self._successor(testing_document, prior)
        del successor["estimands"]["affects"]
        with pytest.raises(SuccessionViolation, match="estimand:affects"):
            parse(successor, predecessor=prior)

    def test_retiring_the_operator_keeps_the_declaration_as_a_tombstone(self, parse, testing_document):
        prior = parse(testing_document)
        successor = self._successor(testing_document, prior)
        successor["operators"]["affects"]["retired"] = True
        contract = parse(successor, predecessor=prior)
        assert "affects" in contract.estimands
```

- [ ] **Step 3: Run them to verify they fail**

Run: `uv run --frozen pytest tests/test_estimand_declarations.py`
Expected: every test fails at `parse(...)` with `MalformedContract: … unknown field(s) estimands`.

- [ ] **Step 4: Parse the table in Python**

In `python/src/beliefs/contract/domain.py`:

```python
_CONTRACT_FIELDS = frozenset({"contract", "version", "lineage", "sorts", "dimensions", "operators"})
_CONTRACT_OPTIONAL = frozenset({"description", "facets", "estimands"})
_ESTIMAND_FIELDS = frozenset({"level_sorts", "measure_sort", "identification_sort", "conditioning_sort"})
_SLOT_INDEX = re.compile(r"^(0|[1-9][0-9]*)$")


@dataclass(frozen=True)
class EstimandDecl:
    """Which sorts fill the kernel's estimand structure at one operator
    (estimand-typing §5.1). A claim-vocabulary declaration under §8.3's four
    succession rules; keyed by the operator it belongs to, and carrying no
    `retired` of its own — retiring the operator retires it."""

    operator: str
    level_sorts: Mapping[str, str]
    """Slot index, spelled as decimal text, → sort. A slot absent here admits
    only a `continuous` contrast."""
    measure_sort: str
    identification_sort: str
    conditioning_sort: str

    def schema_projection(self) -> dict[str, object]:
        return {
            "level_sorts": {slot: self.level_sorts[slot] for slot in sorted(self.level_sorts, key=int)},
            "measure_sort": self.measure_sort,
            "identification_sort": self.identification_sort,
            "conditioning_sort": self.conditioning_sort,
        }


def _parse_estimand_decl(
    name: str, value: object, where: str, *, operators: Mapping[str, OperatorDecl], resolve: Callable[[object, str], str]
) -> EstimandDecl:
    body = _mapping(value, where)
    _fields(body, _ESTIMAND_FIELDS, frozenset({"description"}), where)
    if name not in operators:
        raise MalformedContract(
            f"{where}: {name!r} is not an operator this contract declares. An estimand declaration lives with its "
            "operator (estimand-typing §5.1)."
        )
    arity = operators[name].arity
    if arity == 0:
        raise MalformedContract(f"{where}: {name!r} has arity 0 and admits no estimand — a contrast needs a slot to name")
    raw_levels = _mapping(body["level_sorts"], f"{where}: level_sorts")
    level_sorts: dict[str, str] = {}
    for key, sort in raw_levels.items():
        if not _SLOT_INDEX.fullmatch(key):
            raise MalformedContract(f"{where}: level_sorts key {key!r} is not a slot index spelled as decimal text")
        if int(key) >= arity:
            raise MalformedContract(f"{where}: level_sorts names slot {key}, outside Fin({arity})")
        level_sorts[key] = resolve(sort, f"{where}: level_sorts[{key}]")
    return EstimandDecl(
        operator=name,
        level_sorts=MappingProxyType(level_sorts),
        measure_sort=resolve(body["measure_sort"], f"{where}: measure_sort"),
        identification_sort=resolve(body["identification_sort"], f"{where}: identification_sort"),
        conditioning_sort=resolve(body["conditioning_sort"], f"{where}: conditioning_sort"),
    )
```

(`import re`, `from collections.abc import Callable, Mapping`, `from types import MappingProxyType` as needed.) In `parse_domain_contract`, replace `_fields(root, _CONTRACT_FIELDS, frozenset({"description", "facets"}), source)` with `_fields(root, _CONTRACT_FIELDS, _CONTRACT_OPTIONAL, source)`, and after the operators loop:

```python
    def resolve(value: object, where: str) -> str:
        return _sort_reference(value, where, namespace=namespace, base_name=base.name, sorts=sorts)

    estimands: dict[str, EstimandDecl] = {}
    for name, body in _declarations(root.get("estimands", {}), f"{source}: estimands").items():
        estimands[name] = _parse_estimand_decl(name, body, f"{source}: estimands.{name}", operators=operators, resolve=resolve)
```

Add `estimands: Mapping[str, EstimandDecl]` to `DomainContract`'s fields and to `_parsed` (`("estimands", MappingProxyType(dict(estimands)))`), pass `estimands=estimands` from the parser, and extend `_declarations()`:

```python
            *((f"estimand:{name}", decl) for name, decl in self.estimands.items()),
```

`retired_identifiers()` filters on `decl.retired`; give `EstimandDecl` a read-only property `retired` returning `False` so the existing comprehension needs no branch — the tombstone comes from the operator, not the declaration. Export `EstimandDecl`.

- [ ] **Step 5: Run the tests**

Run: `uv run --frozen pytest tests/test_estimand_declarations.py tests/test_domain_contract.py tests/test_claim.py tests/test_decode.py`
Expected: all pass; the fixture's added sorts change no existing assertion (the parity vector in `fixtures/claim-identity-v1.json` is built from claims, not sorts — if `tests/test_identity_fixture.py` or `ts/tests/parity.test.ts` fails, the fixture's coverage assertion names what moved; re-run after Step 7).

- [ ] **Step 6: TypeScript**

In `ts/src/contract.ts`: `export interface EstimandDecl { readonly operator: string; readonly levelSorts: Readonly<Record<string, string>>; readonly measureSort: string; readonly identificationSort: string; readonly conditioningSort: string; }`; `readonly estimands: DeclarationTable<EstimandDecl>` on `DomainContract` (constructor parts and assignment); in `parseDomainContract`, add `"estimands"` to the optional field list and, after the operators table is built:

```ts
  const estimandEntries: [string, EstimandDecl][] = [];
  for (const [name, body] of Object.entries(declarations(document.estimands, `${source}.estimands`))) {
    const where = `${source}.estimands.${name}`;
    const decl = mapping(body, where);
    exactFields(decl, ["level_sorts", "measure_sort", "identification_sort", "conditioning_sort"], ["description"], where);
    const operator = operators[name];
    if (operator === undefined) throw new MalformedContract(`${where}: ${JSON.stringify(name)} is not a declared operator`);
    if (operator.arity === 0) throw new MalformedContract(`${where}: ${JSON.stringify(name)} has arity 0 and admits no estimand`);
    const levelSorts: Record<string, string> = Object.create(null);
    for (const [slot, sort] of Object.entries(mapping(decl.level_sorts, `${where}.level_sorts`))) {
      if (!/^(0|[1-9][0-9]*)$/.test(slot)) throw new MalformedContract(`${where}.level_sorts: ${JSON.stringify(slot)} is not a slot index`);
      if (Number(slot) >= operator.arity) throw new MalformedContract(`${where}.level_sorts: slot ${slot} is outside Fin(${operator.arity})`);
      levelSorts[slot] = sortReference(sort, `${where}.level_sorts[${slot}]`, namespace, base.name, sorts);
    }
    estimandEntries.push([
      name,
      Object.freeze({
        operator: name,
        levelSorts: Object.freeze(levelSorts),
        measureSort: sortReference(decl.measure_sort, `${where}.measure_sort`, namespace, base.name, sorts),
        identificationSort: sortReference(decl.identification_sort, `${where}.identification_sort`, namespace, base.name, sorts),
        conditioningSort: sortReference(decl.conditioning_sort, `${where}.conditioning_sort`, namespace, base.name, sorts),
      }),
    ]);
  }
  const estimands = frozenTable(estimandEntries);
```

Append to `ts/tests/contract-scope.test.ts` (its `DOMAIN` string gains `estimands:` for `subtype-of`? no — `subtype-of` has arity 2 there, so add a sort `measure` and an entry keyed `subtype-of`; then):

```ts
  it("refuses an estimand declaration keyed by an undeclared operator", () => {
    const bad = WITH_ESTIMAND.replace("estimands:\n  subtype-of:", "estimands:\n  affects:");
    expect(() => parseDomainContract(bad, "<domain>", base)).toThrow(/not a declared operator/);
  });
  it("refuses a level_sorts slot outside the arity", () => {
    const bad = WITH_ESTIMAND.replace('level_sorts: { "0": entity }', 'level_sorts: { "5": entity }');
    expect(() => parseDomainContract(bad, "<domain>", base)).toThrow(/Fin\(2\)/);
  });
```

where `WITH_ESTIMAND` is `DOMAIN` plus a `measure` sort and:

```yaml
estimands:
  subtype-of:
    level_sorts: { "0": entity }
    measure_sort: measure
    identification_sort: entity
    conditioning_sort: entity
```

Run: `cd ts && npm test`
Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add python/src/beliefs/contract/domain.py fixtures/contracts/testing.yaml ts/src/contract.ts python/tests/test_estimand_declarations.py ts/tests/contract-scope.test.ts
git commit -m "feat(contract): parse and succession-govern estimands declarations (Q2)"
```

---

### Task 3: Compile `estimands:` into the profile — Python and TypeScript

**Files:**
- Modify: `python/src/beliefs/profile.py` (`CompiledEstimandDecl`, `ProfileSpec.estimands`, `ProfileSpec.estimand()`, `_projection`, `compile_profile`)
- Modify: `ts/src/profile.ts`
- Test: `python/tests/test_estimand_declarations.py` (append), `python/tests/test_profile.py`

**Interfaces:**
- Produces: `CompiledEstimandDecl(operator: str, level_sorts: Mapping[str, str], measure_sort: str, identification_sort: str, conditioning_sort: str, contract: str)` with every sort a **term identifier**; `ProfileSpec.estimands: Mapping[str, CompiledEstimandDecl]` keyed by operator term; `ProfileSpec.estimand(term) -> CompiledEstimandDecl` refusing with `ProfileError` when the operator declares none.

- [ ] **Step 1: Write the failing tests**

Append to `python/tests/test_estimand_declarations.py`:

```python
class TestCompile:
    @pytest.fixture()
    def profile(self, base_contract, testing_document):
        from beliefs.profile import compile_profile

        testing = domain.parse_domain_contract(testing_document, source="<test>", base=base_contract, predecessor=None)
        return compile_profile(base_contract, [testing])

    def test_sorts_compile_to_term_identifiers(self, profile):
        decl = profile.estimand("testing/affects")
        assert decl.level_sorts == {"0": "testing/level"}
        assert decl.measure_sort == "testing/measure"
        assert decl.identification_sort == "testing/identification"
        assert decl.conditioning_sort == "testing/entity"
        assert decl.contract == "testing"

    def test_an_operator_without_a_declaration_refuses(self, profile):
        from beliefs.errors import ProfileError

        with pytest.raises(ProfileError, match="declares no estimand"):
            profile.estimand("testing/subtype-of")

    def test_the_declaration_enters_the_compiled_identity(self, base_contract, testing_document):
        from beliefs.profile import compile_profile

        changed = copy.deepcopy(testing_document)
        changed["estimands"]["affects"]["conditioning_sort"] = "outcome"
        one = compile_profile(base_contract, [domain.parse_domain_contract(testing_document, source="<a>", base=base_contract, predecessor=None)])
        two = compile_profile(base_contract, [domain.parse_domain_contract(changed, source="<b>", base=base_contract, predecessor=None)])
        assert one.compiled_identity != two.compiled_identity

    def test_a_cross_contract_sort_resolves_or_refuses_by_namespace(self, base_contract, testing_document):
        from beliefs.profile import compile_profile

        document = copy.deepcopy(testing_document)
        document["estimands"]["affects"]["measure_sort"] = "biology/assay"
        contract = domain.parse_domain_contract(document, source="<x>", base=base_contract, predecessor=None)
        with pytest.raises(MalformedContract, match="namespace 'biology'"):
            compile_profile(base_contract, [contract])
```

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run --frozen pytest tests/test_estimand_declarations.py -k TestCompile`
Expected: 4 failed — `AttributeError: 'ProfileSpec' object has no attribute 'estimand'` (and the cross-contract case passes parse but compiles without refusing).

- [ ] **Step 3: Compile**

In `python/src/beliefs/profile.py`, import `EstimandDecl`, add:

```python
@dataclass(frozen=True)
class CompiledEstimandDecl:
    """An `estimands:` entry with every sort resolved to a term identifier
    (estimand-typing §5.2)."""

    operator: str
    level_sorts: Mapping[str, str]
    measure_sort: str
    identification_sort: str
    conditioning_sort: str
    contract: str

    def schema_projection(self) -> dict[str, object]:
        return {
            "level_sorts": {slot: self.level_sorts[slot] for slot in sorted(self.level_sorts, key=int)},
            "measure_sort": self.measure_sort,
            "identification_sort": self.identification_sort,
            "conditioning_sort": self.conditioning_sort,
        }


def _compile_estimand(
    contract: DomainContract, decl: EstimandDecl, sorts: Mapping[str, CompiledSort]
) -> CompiledEstimandDecl:
    where = f"estimands.{decl.operator}"
    return CompiledEstimandDecl(
        operator=contract.term(decl.operator),
        level_sorts=MappingProxyType(
            {slot: _resolve_sort(contract, sort, sorts, where=f"{where}: level_sorts[{slot}]") for slot, sort in decl.level_sorts.items()}
        ),
        measure_sort=_resolve_sort(contract, decl.measure_sort, sorts, where=f"{where}: measure_sort"),
        identification_sort=_resolve_sort(contract, decl.identification_sort, sorts, where=f"{where}: identification_sort"),
        conditioning_sort=_resolve_sort(contract, decl.conditioning_sort, sorts, where=f"{where}: conditioning_sort"),
        contract=contract.namespace,
    )
```

Add `estimands: Mapping[str, CompiledEstimandDecl]` to `ProfileSpec` after `operators`; in `compile_profile`, declare `estimands: dict[str, CompiledEstimandDecl] = {}` beside `operators` and, inside the second `for namespace in sorted(seen)` loop after the operators loop:

```python
        for name, decl in contract.estimands.items():
            estimands[contract.term(name)] = _compile_estimand(contract, decl, sorts)
```

pass `estimands=MappingProxyType(dict(estimands))` to `_compiled`, give `_projection` an `estimands: Mapping[str, CompiledEstimandDecl]` keyword and emit `"estimands": {term: decl.schema_projection() for term, decl in estimands.items()}` after `"operators"`, and add the accessor:

```python
    def estimand(self, term: str) -> CompiledEstimandDecl:
        """The estimand declaration for an operator, or refuse. An operator with
        no declaration admits no typed estimand, so a spec targeting a claim at
        it refuses at construction (estimand-typing §7.1)."""
        self.operator(term)
        try:
            return self.estimands[term]
        except KeyError:
            raise ProfileError(
                f"operator {term!r} declares no estimand; its contract's `estimands:` table has no entry for it "
                "(estimand-typing §5.1), so no spec can target a claim at it."
            ) from None
```

Export `CompiledEstimandDecl`.

- [ ] **Step 4: Run the tests**

Run: `uv run --frozen pytest tests/test_estimand_declarations.py tests/test_profile.py tests/test_profile_agreement.py tests/test_consulted.py`
Expected: all pass.

- [ ] **Step 5: TypeScript**

In `ts/src/profile.ts`: `export interface CompiledEstimandDecl { readonly operator: string; readonly levelSorts: Readonly<Record<string, string>>; readonly measureSort: string; readonly identificationSort: string; readonly conditioningSort: string; }`; `readonly estimands: ResolutionTable<CompiledEstimandDecl>` on `ProfileSpec`; in `compileProfile`'s second domain loop, after operators:

```ts
    for (const [name, declaration] of Object.entries(contract.estimands)) {
      const levelSorts: Record<string, string> = Object.create(null);
      for (const [slot, sort] of Object.entries(declaration.levelSorts)) {
        levelSorts[slot] = resolveSort(contract, sort, `estimands.${name}: level_sorts[${slot}]`);
      }
      estimands[term(contract.namespace, name)] = Object.freeze({
        operator: term(contract.namespace, name),
        levelSorts: Object.freeze(levelSorts),
        measureSort: resolveSort(contract, declaration.measureSort, `estimands.${name}: measure_sort`),
        identificationSort: resolveSort(contract, declaration.identificationSort, `estimands.${name}: identification_sort`),
        conditioningSort: resolveSort(contract, declaration.conditioningSort, `estimands.${name}: conditioning_sort`),
      });
    }
```

Append to `ts/tests/contract-scope.test.ts`:

```ts
  it("compiles an estimand declaration's sorts to term identifiers", () => {
    const profile = compileProfile(base, [parseDomainContract(WITH_ESTIMAND, "<domain>", base)]);
    expect(profile.estimands["testing/subtype-of"].measureSort).toBe("testing/measure");
    expect(profile.estimands["testing/subtype-of"].levelSorts).toEqual({ "0": "testing/entity" });
  });
```

Run: `cd ts && npm test`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add python/src/beliefs/profile.py ts/src/profile.ts python/tests/test_estimand_declarations.py ts/tests/contract-scope.test.ts
git commit -m "feat(profile): compile estimand declarations into the profile (Q2)"
```

---

### Task 4: `beliefs/estimand.py` — the opaque value, its constructor, projections and predicates

**Files:**
- Create: `python/src/beliefs/estimand.py`
- Modify: `python/src/beliefs/errors.py` (after `InadmissibleLayer`), `python/src/beliefs/resolution.py:92-118` (`ReferentPosition.estimand`)
- Test: `python/tests/test_estimand.py` (new)

**Interfaces:**
- Consumes: `ProfileSpec.estimand(term)` (Task 3), `ProfileSpec.estimand_grammar` (Task 1), `Claim`, `Referent`, `Qualifier` from `beliefs.claim`, `ResolutionSnapshot`, `_emit_receipt`, `ReferentPosition` from `beliefs.resolution`.
- Produces, all in `beliefs.estimand`: sealed values `LevelsContrast(slot: int, baseline: Referent, comparison: Referent)`, `ContinuousContrast(slot: int, quantity: Referent, increment: Decimal)`, `Measure(quantity: Referent, scale: str)`, `Control(identification: Referent, conditioning: tuple[Referent, ...])`, `Interval(low: Decimal, high: Decimal, level: Decimal)`, `StandardError(value: Decimal)`; the opaque `Estimand(claim: str, operator: str, contrast, measure, reference: Decimal, control)`; `build_estimand(profile, claim, *, contrast, measure, reference, control, snapshot) -> tuple[Estimand, BindingCheckReceipt]`; `build_applicability(profile, claim, qualifiers, *, snapshot) -> tuple[Mapping[str, Qualifier], BindingCheckReceipt]`; `estimand_projection(e) -> dict`, `applicability_projection(q) -> dict`, `uncertainty_projection(u) -> dict`; `commensuration_key(e) -> dict`, `commensurable(a, b) -> bool`, `co_scoped(a, b) -> bool`; `check_estimate(estimate, scale)`, `check_uncertainty(uncertainty, estimate, scale)` raising `UncertaintyRefused`. `ESTIMAND_ERRORS`, the tuple of every refusal class.
- Errors in `beliefs.errors`: `EstimandError(ScienceError)` and its subclasses `ContrastRefused`, `MeasureRefused`, `ReferenceRefused`, `ControlRefused`, `UncertaintyRefused`, `EstimandSortMismatch`, `EstimandFragmentRefused`, `UntypedEstimandMember`.

- [ ] **Step 1: Write the failing tests**

Create `python/tests/test_estimand.py`:

```python
"""Q3 (construction refuses rather than flattens), Q7's projection arms, Q9 (commensuration and scope)."""

from decimal import Decimal

import pytest

from beliefs.claim import Qualifier, Referent, build_claim
from beliefs.contract import domain
from beliefs.errors import (
    ContrastRefused,
    ControlRefused,
    EstimandFragmentRefused,
    EstimandSortMismatch,
    MeasureRefused,
    ProfileError,
    ReferenceRefused,
    UnboundReferent,
    UncertaintyRefused,
)
from beliefs.estimand import (
    ContinuousContrast,
    Control,
    Estimand,
    Interval,
    LevelsContrast,
    Measure,
    StandardError,
    applicability_projection,
    build_applicability,
    build_estimand,
    check_estimate,
    check_uncertainty,
    co_scoped,
    commensurable,
    estimand_projection,
)
from beliefs.profile import compile_profile
from beliefs.resolution import TermOutcome, build_snapshot

E, O, L, M, I = "testing/entity", "testing/outcome", "testing/level", "testing/measure", "testing/identification"


@pytest.fixture()
def profile(base_contract, testing_document):
    testing = domain.parse_domain_contract(testing_document, source="<test>", base=base_contract, predecessor=None)
    return compile_profile(base_contract, [testing])


@pytest.fixture()
def claim(profile):
    return build_claim(profile, operator="testing/affects", args=(Referent(E, "EX:gene-x"), Referent(O, "EX:pheno-y")), layer="causal", polarity="positive")


@pytest.fixture()
def other_claim(profile):
    return build_claim(profile, operator="testing/affects", args=(Referent(E, "EX:gene-z"), Referent(O, "EX:pheno-y")), layer="causal", polarity="positive")


@pytest.fixture()
def unconsulted():
    return build_snapshot(readable={})


def parts(**overrides):
    fields = {
        "contrast": LevelsContrast(slot=0, baseline=Referent(L, "EX:ndmm"), comparison=Referent(L, "EX:pd")),
        "measure": Measure(quantity=Referent(M, "EX:tpm"), scale="additive"),
        "reference": Decimal("0"),
        "control": Control(identification=Referent(I, "EX:observational"), conditioning=()),
    }
    fields.update(overrides)
    return fields


def build(profile, claim, snapshot, **overrides):
    estimand, _receipt = build_estimand(profile, claim, snapshot=snapshot, **parts(**overrides))
    return estimand


def test_a_levels_estimand_builds_and_names_its_claim(profile, claim, unconsulted):
    from beliefs.projection import claim_identity

    estimand, receipt = build_estimand(profile, claim, snapshot=unconsulted, **parts())
    assert estimand.claim == claim_identity(claim) and estimand.operator == "testing/affects"
    assert set(receipt.outcomes) == {"estimand:contrast.baseline", "estimand:contrast.comparison", "estimand:measure.quantity", "estimand:control.identification"}
    assert all(outcome is TermOutcome.NOT_CONSULTED for outcome in receipt.outcomes.values())


def test_a_continuous_estimand_carries_quantity_and_increment(profile, claim, unconsulted):
    estimand = build(profile, claim, unconsulted, contrast=ContinuousContrast(slot=0, quantity=Referent(M, "EX:log2-tpm"), increment=Decimal("1")))
    assert estimand_projection(estimand)["contrast"] == {"slot": 0, "kind": "continuous", "quantity": {"sort": M, "term": "EX:log2-tpm"}, "increment": Decimal("1")}


def test_estimand_has_no_public_constructor():
    with pytest.raises(Exception):
        Estimand(claim="c", operator="o", contrast=None, measure=None, reference=Decimal("0"), control=None)  # type: ignore[call-arg]


# Every invalid value is built **inside** the assertion: the sealed values refuse
# at construction, so a parametrization that constructed them at collection time
# would fail before `pytest.raises` ran.
@pytest.mark.parametrize("make,error,position", [
    (lambda: {"contrast": LevelsContrast(slot=2, baseline=Referent(L, "EX:a"), comparison=Referent(L, "EX:b"))}, ContrastRefused, "slot 2"),
    (lambda: {"contrast": LevelsContrast(slot=True, baseline=Referent(L, "EX:a"), comparison=Referent(L, "EX:b"))}, ContrastRefused, "integer"),
    (lambda: {"contrast": ContinuousContrast(slot=0.5, quantity=Referent(M, "EX:q"), increment=Decimal("1"))}, ContrastRefused, "integer"),  # type: ignore[arg-type]
    (lambda: {"contrast": LevelsContrast(slot=1, baseline=Referent(L, "EX:a"), comparison=Referent(L, "EX:b"))}, ContrastRefused, "no level sort"),
    (lambda: {"contrast": LevelsContrast(slot=0, baseline=Referent(L, "EX:a"), comparison=Referent(L, "EX:a"))}, ContrastRefused, "distinct"),
    (lambda: {"contrast": LevelsContrast(slot=0, baseline=Referent(E, "EX:a"), comparison=Referent(L, "EX:b"))}, EstimandSortMismatch, "contrast.baseline"),
    (lambda: {"contrast": ContinuousContrast(slot=0, quantity=Referent(M, "EX:q"), increment=Decimal("0"))}, ContrastRefused, "increment"),
    (lambda: {"contrast": ContinuousContrast(slot=0, quantity=Referent(M, "EX:q"), increment=Decimal("-1"))}, ContrastRefused, "increment"),
    (lambda: {"contrast": ContinuousContrast(slot=0, quantity=Referent(E, "EX:q"), increment=Decimal("1"))}, EstimandSortMismatch, "contrast.quantity"),
    (lambda: {"measure": Measure(quantity=Referent(E, "EX:tpm"), scale="additive")}, EstimandSortMismatch, "measure.quantity"),
    (lambda: {"measure": Measure(quantity=Referent(M, "EX:tpm"), scale="ordinal")}, MeasureRefused, "scale"),
    (lambda: {"measure": Measure(quantity=Referent(M, "EX:hr"), scale="multiplicative"), "reference": Decimal("0")}, ReferenceRefused, "multiplicative"),
    (lambda: {"reference": Decimal("NaN")}, ReferenceRefused, "finite"),
    (lambda: {"control": Control(identification=Referent(E, "EX:obs"), conditioning=())}, EstimandSortMismatch, "control.identification"),
    (lambda: {"control": Control(identification=Referent(I, "EX:obs"), conditioning=(Referent(O, "EX:c"),))}, EstimandSortMismatch, "control.conditioning[0]"),
    (lambda: {"control": Control(identification=Referent(I, "EX:obs"), conditioning=(Referent(E, "EX:c"), Referent(E, "EX:c")))}, ControlRefused, "duplicate"),
])
def test_each_refusal_names_its_position(profile, claim, unconsulted, make, error, position):
    with pytest.raises(error, match=position):
        build(profile, claim, unconsulted, **make())


def test_a_float_reference_is_refused_before_the_digest(profile, claim, unconsulted):
    with pytest.raises(ReferenceRefused, match="Decimal"):
        build(profile, claim, unconsulted, reference=0.0)  # type: ignore[arg-type]


def test_an_operator_without_a_declaration_refuses(profile, unconsulted):
    structural = build_claim(profile, operator="testing/subtype-of", args=(Referent(E, "EX:a"), Referent(E, "EX:b")), layer="structural")
    with pytest.raises(ProfileError, match="declares no estimand"):
        build(profile, structural, unconsulted)


def test_not_member_refuses_and_not_consulted_mints(profile, claim, unconsulted):
    binding = profile.sorts[L].vocabulary
    readable = build_snapshot(readable={binding: ["EX:ndmm", "EX:pd"]})
    estimand, receipt = build_estimand(profile, claim, snapshot=readable, **parts())
    assert receipt.outcomes["estimand:contrast.baseline"] is TermOutcome.MEMBER
    with pytest.raises(UnboundReferent, match="estimand:contrast.comparison"):
        build(profile, claim, readable, contrast=LevelsContrast(slot=0, baseline=Referent(L, "EX:ndmm"), comparison=Referent(L, "EX:mgus")))
    assert estimand_projection(build(profile, claim, unconsulted)) == estimand_projection(estimand)


def test_the_fragment_refuses_a_second_measure_or_reference(profile, claim, unconsulted):
    with pytest.raises(EstimandFragmentRefused, match="one measure"):
        build_estimand(profile, claim, snapshot=unconsulted, **parts(), measures=(parts()["measure"], parts()["measure"]))  # type: ignore[arg-type]


class TestProjection:
    def test_conditioning_order_is_inert(self, profile, claim, unconsulted):
        a = build(profile, claim, unconsulted, control=Control(identification=Referent(I, "EX:obs"), conditioning=(Referent(E, "EX:c1"), Referent(E, "EX:c2"))))
        b = build(profile, claim, unconsulted, control=Control(identification=Referent(I, "EX:obs"), conditioning=(Referent(E, "EX:c2"), Referent(E, "EX:c1"))))
        assert estimand_projection(a) == estimand_projection(b)

    def test_swapped_levels_are_two_estimands(self, profile, claim, unconsulted):
        a = build(profile, claim, unconsulted)
        b = build(profile, claim, unconsulted, contrast=LevelsContrast(slot=0, baseline=Referent(L, "EX:pd"), comparison=Referent(L, "EX:ndmm")))
        assert estimand_projection(a) != estimand_projection(b)

    @pytest.mark.parametrize("override", [
        {"measure": Measure(quantity=Referent(M, "EX:other"), scale="additive")},
        {"measure": Measure(quantity=Referent(M, "EX:tpm"), scale="multiplicative"), "reference": Decimal("1")},
        {"reference": Decimal("0.5")},
        {"control": Control(identification=Referent(I, "EX:longitudinal"), conditioning=())},
        {"control": Control(identification=Referent(I, "EX:observational"), conditioning=(Referent(E, "EX:c"),))},
    ])
    def test_each_member_moves_the_projection(self, profile, claim, unconsulted, override):
        assert estimand_projection(build(profile, claim, unconsulted)) != estimand_projection(build(profile, claim, unconsulted, **override))


class TestPredicates:
    def test_identification_alone_is_outside_the_key(self, profile, claim, unconsulted):
        a = build(profile, claim, unconsulted)
        b = build(profile, claim, unconsulted, control=Control(identification=Referent(I, "EX:longitudinal"), conditioning=()))
        assert commensurable(a, b)

    def test_two_claims_at_one_operator_are_two_keys(self, profile, claim, other_claim, unconsulted):
        assert not commensurable(build(profile, claim, unconsulted), build(profile, other_claim, unconsulted))

    def test_swapped_levels_and_different_increments_are_not_commensurable(self, profile, claim, unconsulted):
        a = build(profile, claim, unconsulted)
        b = build(profile, claim, unconsulted, contrast=LevelsContrast(slot=0, baseline=Referent(L, "EX:pd"), comparison=Referent(L, "EX:ndmm")))
        assert not commensurable(a, b)
        c1 = build(profile, claim, unconsulted, contrast=ContinuousContrast(slot=0, quantity=Referent(M, "EX:q"), increment=Decimal("1")))
        c10 = build(profile, claim, unconsulted, contrast=ContinuousContrast(slot=0, quantity=Referent(M, "EX:q"), increment=Decimal("10")))
        assert not commensurable(c1, c10)

    def test_the_scope_counterexample(self, profile, claim, unconsulted):
        adults, _ = build_applicability(profile, claim, {"testing/population": Qualifier("generic", Referent("testing/cohort", "EX:adults"))}, snapshot=unconsulted)
        everyone, _ = build_applicability(profile, claim, {}, snapshot=unconsulted)
        a, b = build(profile, claim, unconsulted), build(profile, claim, unconsulted)
        assert commensurable(a, b) and not co_scoped(adults, everyone)
        assert applicability_projection(everyone) == {}

    def test_applicability_refuses_an_undeclared_dimension_and_a_wrong_sort(self, profile, claim, unconsulted):
        from beliefs.errors import RestrictionSortMismatch, UndeclaredDimension

        with pytest.raises(UndeclaredDimension):
            build_applicability(profile, claim, {"testing/regime": Qualifier("generic", Referent(E, "EX:x"))}, snapshot=unconsulted)
        with pytest.raises(RestrictionSortMismatch):
            build_applicability(profile, claim, {"testing/population": Qualifier("generic", Referent(E, "EX:x"))}, snapshot=unconsulted)


class TestEstimateAndUncertainty:
    def test_a_multiplicative_estimate_must_be_positive(self):
        check_estimate(Decimal("1.2"), "multiplicative")
        with pytest.raises(UncertaintyRefused, match="multiplicative"):
            check_estimate(Decimal("0"), "multiplicative")

    @pytest.mark.parametrize("uncertainty,scale", [
        (Interval(Decimal("0.5"), Decimal("0.3"), Decimal("0.95")), "additive"),
        (Interval(Decimal("-1"), Decimal("1"), Decimal("1")), "additive"),
        (Interval(Decimal("0"), Decimal("2"), Decimal("0.95")), "multiplicative"),
        (StandardError(Decimal("-0.1")), "additive"),
    ])
    def test_ill_formed_uncertainty_is_refused(self, uncertainty, scale):
        with pytest.raises(UncertaintyRefused):
            check_uncertainty(uncertainty, Decimal("0.4") if scale == "additive" else Decimal("1.1"), scale)

    def test_well_formed_uncertainty_passes(self):
        check_uncertainty(Interval(Decimal("0.1"), Decimal("0.7"), Decimal("0.95")), Decimal("0.4"), "additive")
        check_uncertainty(StandardError(Decimal("0.2")), Decimal("1.1"), "multiplicative")
```

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run --frozen pytest tests/test_estimand.py`
Expected: collection error — `ModuleNotFoundError: No module named 'beliefs.estimand'`.

- [ ] **Step 3: The errors and the position**

Append to `python/src/beliefs/errors.py` after `InadmissibleLayer`:

```python
class EstimandError(ScienceError):
    """An estimand, or a part of one, that is not admissible (estimand-typing §7.1).
    Subclasses stay distinct for M11's reason: each ill-formed input refuses in
    turn, and one class would let a check cover for another's absence."""


class UntypedEstimandMember(EstimandError):
    """A member that is not the sealed value the position requires."""


class ContrastRefused(EstimandError):
    """A slot outside `Fin(arity)`, a `levels` contrast on a slot with no level sort,
    two equal levels, a continuous increment that is not a finite `Decimal > 0`."""


class MeasureRefused(EstimandError):
    """A scale outside the grammar's closed set."""


class ReferenceRefused(EstimandError):
    """A reference that is not a finite `Decimal`, or `≤ 0` under `multiplicative`."""


class ControlRefused(EstimandError):
    """A duplicate conditioning member."""


class UncertaintyRefused(EstimandError):
    """An estimate or uncertainty the spec's scale and reference do not admit
    (estimand-typing §6): a float, an interval excluding its estimate, a level
    outside (0, 1), a negative standard error, a non-positive multiplicative
    estimate. Raised by the constructor's checks; `build_assessment` records it
    as a finding, never an assessment."""


class EstimandSortMismatch(EstimandError):
    """A referent whose sort is not the one the operator's declaration names
    for its position — a term with no slot to occupy, as `ArgumentSortMismatch`."""


class EstimandFragmentRefused(EstimandError):
    """Anything richer than the inhabited fragment (estimand-typing §3.3):
    refused with the fragment named, never flattened."""
```

In `python/src/beliefs/resolution.py`, add to `ReferentPosition`:

```python
    @classmethod
    def estimand(cls, part: str) -> ReferentPosition:
        """`estimand:contrast.baseline`, `estimand:measure.quantity`,
        `estimand:control.conditioning[3]` — the estimand's positions, in the
        receipt's one vocabulary (estimand-typing §7.1)."""
        return cls(kind="estimand", key=part)
```

- [ ] **Step 4: The module**

Create `python/src/beliefs/estimand.py`:

```python
"""The typed estimand (estimand-typing design §3, §7.1, §7.3).

`Estimand` is opaque and reachable only through `build_estimand`, which types
it against the **claim** it answers: the claim's operator fixes every sort
through the operator's `estimands:` declaration, and the claim's identity
enters the value so the estimand says which proposition it answers. Every
referent is resolved under D3's five outcomes; only `not-member` refuses.
Nothing here is read by `science.belief.v1`.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from types import MappingProxyType
from typing import final

from beliefs.claim import Claim, Qualifier, Referent
from beliefs.errors import (
    ContrastRefused,
    ControlRefused,
    EstimandError,
    EstimandFragmentRefused,
    EstimandSortMismatch,
    MeasureRefused,
    ReferenceRefused,
    UnboundReferent,
    UncertaintyRefused,
    UntypedEstimandMember,
)
from beliefs.profile import CompiledEstimandDecl, ProfileSpec
from beliefs.projection import claim_identity
from beliefs.resolution import BindingCheckReceipt, ReferentPosition, ResolutionSnapshot, TermOutcome, _emit_receipt
from beliefs.sealed import sealed

__all__ = [
    "ESTIMAND_ERRORS",
    "ContinuousContrast",
    "Control",
    "Estimand",
    "Interval",
    "LevelsContrast",
    "Measure",
    "StandardError",
    "applicability_projection",
    "build_applicability",
    "build_estimand",
    "check_estimate",
    "check_uncertainty",
    "co_scoped",
    "commensurable",
    "commensuration_key",
    "estimand_projection",
    "uncertainty_projection",
]

ESTIMAND_ERRORS = (EstimandError, UnboundReferent)


def _finite(value: object, where: str, error: type[EstimandError]) -> Decimal:
    if type(value) is not Decimal:
        raise error(f"{where}: expected a Decimal, found {type(value).__name__} — binary floats are refused at the boundary")
    if not value.is_finite():
        raise error(f"{where}: {value} is not finite")
    return value


def _require_slot(value: object) -> None:
    """An integer, never a bool and never a float: the decoder already refuses
    these on the wire, and the shared constructor refuses them for every route."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ContrastRefused(f"contrast.slot is an integer slot index, found {value!r}")


@sealed
@final
@dataclass(frozen=True)
class LevelsContrast:
    slot: int
    baseline: Referent
    comparison: Referent

    def __post_init__(self) -> None:
        _require_slot(self.slot)
        for name in ("baseline", "comparison"):
            if not isinstance(getattr(self, name), Referent):
                raise UntypedEstimandMember(f"contrast.{name} holds {type(getattr(self, name)).__name__}, not a Referent")


@sealed
@final
@dataclass(frozen=True)
class ContinuousContrast:
    slot: int
    quantity: Referent
    increment: Decimal

    def __post_init__(self) -> None:
        _require_slot(self.slot)
        if not isinstance(self.quantity, Referent):
            raise UntypedEstimandMember(f"contrast.quantity holds {type(self.quantity).__name__}, not a Referent")
        if _finite(self.increment, "contrast.increment", ContrastRefused) <= 0:
            raise ContrastRefused(f"contrast.increment must be > 0, found {self.increment}")


@sealed
@final
@dataclass(frozen=True)
class Measure:
    quantity: Referent
    scale: str

    def __post_init__(self) -> None:
        if not isinstance(self.quantity, Referent):
            raise UntypedEstimandMember(f"measure.quantity holds {type(self.quantity).__name__}, not a Referent")


@sealed
@final
@dataclass(frozen=True)
class Control:
    identification: Referent
    conditioning: tuple[Referent, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.identification, Referent):
            raise UntypedEstimandMember("control.identification is not a Referent")
        if not all(isinstance(member, Referent) for member in self.conditioning):
            raise UntypedEstimandMember("control.conditioning holds a non-Referent")
        keyed = sorted(self.conditioning, key=lambda r: (r.sort, r.term))
        for earlier, later in zip(keyed, keyed[1:], strict=False):
            if earlier == later:
                raise ControlRefused(f"control.conditioning: duplicate member {later.term!r}")
        object.__setattr__(self, "conditioning", tuple(keyed))


@sealed
@final
@dataclass(frozen=True)
class Interval:
    low: Decimal
    high: Decimal
    level: Decimal


@sealed
@final
@dataclass(frozen=True)
class StandardError:
    value: Decimal


@sealed
@final
@dataclass(frozen=True, init=False)
class Estimand:
    """Opaque: the only route in is `build_estimand` (M13's shape, one artifact over)."""

    claim: str
    operator: str
    contrast: LevelsContrast | ContinuousContrast
    measure: Measure
    reference: Decimal
    control: Control

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise EstimandError("Estimand is validated at construction — use build_estimand(profile, claim, ...)")

    @classmethod
    def _checked(
        cls,
        profile: ProfileSpec,
        *,
        claim: str,
        operator: str,
        contrast: LevelsContrast | ContinuousContrast,
        measure: Measure,
        reference: Decimal,
        control: Control,
    ) -> Estimand:
        declaration: CompiledEstimandDecl = profile.estimand(operator)
        arity = profile.operator(operator).arity
        grammar = profile.estimand_grammar
        if not isinstance(contrast, (LevelsContrast, ContinuousContrast)):
            raise UntypedEstimandMember(f"contrast holds {type(contrast).__name__}")
        if not (0 <= contrast.slot < arity):
            raise ContrastRefused(f"contrast: slot {contrast.slot} is outside Fin({arity}) for {operator!r}")
        if isinstance(contrast, LevelsContrast):
            level_sort = declaration.level_sorts.get(str(contrast.slot))
            if level_sort is None:
                raise ContrastRefused(f"contrast: slot {contrast.slot} of {operator!r} declares no level sort; only a continuous contrast is admitted there")
            for name in ("baseline", "comparison"):
                _require_sort(getattr(contrast, name), level_sort, f"contrast.{name}")
            if contrast.baseline.term == contrast.comparison.term:
                raise ContrastRefused("contrast: baseline and comparison must be distinct levels")
        else:
            _require_sort(contrast.quantity, declaration.measure_sort, "contrast.quantity")
        if not isinstance(measure, Measure):
            raise UntypedEstimandMember(f"measure holds {type(measure).__name__}")
        _require_sort(measure.quantity, declaration.measure_sort, "measure.quantity")
        if measure.scale not in grammar.scales:
            raise MeasureRefused(f"measure.scale {measure.scale!r} is outside the kernel's closed set {list(grammar.scales)}")
        reference = _finite(reference, "reference", ReferenceRefused)
        if measure.scale == "multiplicative" and reference <= 0:
            raise ReferenceRefused(f"reference must be > 0 under a multiplicative scale, found {reference}")
        if not isinstance(control, Control):
            raise UntypedEstimandMember(f"control holds {type(control).__name__}")
        _require_sort(control.identification, declaration.identification_sort, "control.identification")
        for index, member in enumerate(control.conditioning):
            _require_sort(member, declaration.conditioning_sort, f"control.conditioning[{index}]")
        estimand = object.__new__(cls)
        for name, value in (("claim", claim), ("operator", operator), ("contrast", contrast), ("measure", measure), ("reference", reference), ("control", control)):
            object.__setattr__(estimand, name, value)
        return estimand


def _require_sort(referent: Referent, sort: str, where: str) -> None:
    if referent.sort != sort:
        raise EstimandSortMismatch(
            f"{where} is declared {sort!r}; {referent.term!r} is of sort {referent.sort!r} — a term with no slot to occupy"
        )


def _referent_positions(estimand: Estimand) -> dict[str, Referent]:
    positions: dict[str, Referent] = {}
    if isinstance(estimand.contrast, LevelsContrast):
        positions["contrast.baseline"] = estimand.contrast.baseline
        positions["contrast.comparison"] = estimand.contrast.comparison
    else:
        positions["contrast.quantity"] = estimand.contrast.quantity
    positions["measure.quantity"] = estimand.measure.quantity
    positions["control.identification"] = estimand.control.identification
    for index, member in enumerate(estimand.control.conditioning):
        positions[f"control.conditioning[{index}]"] = member
    return positions


def _resolve_all(profile: ProfileSpec, snapshot: ResolutionSnapshot, positions: Mapping[str, Referent]) -> dict[str, TermOutcome]:
    outcomes = {label: snapshot.resolve(profile.sorts[referent.sort].vocabulary, referent.term) for label, referent in positions.items()}
    refused = sorted(label for label, outcome in outcomes.items() if outcome.refuses)
    if refused:
        raise UnboundReferent(
            f"{', '.join(refused)}: the term is not in the vocabulary its sort binds, and the vocabulary was read. Nothing was minted."
        )
    return outcomes


def build_estimand(
    profile: ProfileSpec,
    claim: Claim,
    *,
    contrast: LevelsContrast | ContinuousContrast,
    measure: Measure,
    reference: Decimal,
    control: Control,
    snapshot: ResolutionSnapshot,
    **richer: object,
) -> tuple[Estimand, BindingCheckReceipt]:
    """Type an estimand against the claim it answers, resolve its referents, or refuse.

    `**richer` exists to be refused: a second measure, a second reference, a
    multi-arm contrast handed in under any keyword is outside the inhabited
    fragment (§3.3), and the refusal names it rather than flattening it."""
    if richer:
        raise EstimandFragmentRefused(
            f"the inhabited fragment admits one contrast on one slot, one measure, one reference, one identification and "
            f"one flat conditioning set; {sorted(richer)} is outside it and is refused, not flattened (estimand-typing §3.3)"
        )
    if not isinstance(claim, Claim):
        raise UntypedEstimandMember(f"an estimand is built against a Claim, found {type(claim).__name__}")
    if not isinstance(snapshot, ResolutionSnapshot):
        raise UntypedEstimandMember("snapshot is not a ResolutionSnapshot — availability is a parameter, never ambient")
    identity = claim_identity(claim)
    estimand = Estimand._checked(profile, claim=identity, operator=claim.operator, contrast=contrast, measure=measure, reference=reference, control=control)
    outcomes = _resolve_all(profile, snapshot, {ReferentPosition.estimand(part).label(): r for part, r in _referent_positions(estimand).items()})
    return estimand, _emit_receipt(identity, snapshot, outcomes)


def build_applicability(
    profile: ProfileSpec, claim: Claim, qualifiers: Mapping[str, Qualifier], *, snapshot: ResolutionSnapshot
) -> tuple[Mapping[str, Qualifier], BindingCheckReceipt]:
    """The claim grammar's flat fragment over the target operator's dimensions
    (§4): every check `Claim._checked` performs on a qualifier, performed here on
    the applicability map, then each restriction resolved."""
    if not isinstance(claim, Claim):
        raise UntypedEstimandMember(f"applicability is built against a Claim, found {type(claim).__name__}")
    polarity = None if claim.polarity == profile.claim_grammar.sign_inapt_tag else claim.polarity
    checked = Claim._checked(profile, operator=claim.operator, args=claim.args, qualifiers=qualifiers, polarity=polarity, layer=claim.layer)
    outcomes = _resolve_all(
        profile, snapshot, {ReferentPosition.restriction(d).label(): q.restriction for d, q in checked.qualifiers.items()}
    )
    return MappingProxyType(dict(checked.qualifiers)), _emit_receipt(claim_identity(claim), snapshot, outcomes)


def _referent(referent: Referent) -> dict[str, str]:
    return {"sort": referent.sort, "term": referent.term}


def estimand_projection(estimand: Estimand) -> dict[str, object]:
    """The canonical projection (§3.2): `claim`, `operator`, the contrast by kind,
    `measure`, `reference`, `control` with conditioning sorted. Decimals stay
    `Decimal`; identity v1 renders them canonically at encode."""
    contrast: dict[str, object] = {"slot": estimand.contrast.slot}
    if isinstance(estimand.contrast, LevelsContrast):
        contrast |= {"kind": "levels", "baseline": _referent(estimand.contrast.baseline), "comparison": _referent(estimand.contrast.comparison)}
    else:
        contrast |= {"kind": "continuous", "quantity": _referent(estimand.contrast.quantity), "increment": estimand.contrast.increment}
    return {
        "claim": estimand.claim,
        "operator": estimand.operator,
        "contrast": contrast,
        "measure": {"quantity": _referent(estimand.measure.quantity), "scale": estimand.measure.scale},
        "reference": estimand.reference,
        "control": {
            "identification": _referent(estimand.control.identification),
            "conditioning": [_referent(member) for member in estimand.control.conditioning],
        },
    }


def applicability_projection(qualifiers: Mapping[str, Qualifier]) -> dict[str, object]:
    return {
        dimension: {"quantifier": q.quantifier, "restriction": _referent(q.restriction)}
        for dimension, q in sorted(qualifiers.items())
    }


def uncertainty_projection(uncertainty: Interval | StandardError) -> dict[str, object]:
    if isinstance(uncertainty, Interval):
        return {"kind": "interval", "low": uncertainty.low, "high": uncertainty.high, "level": uncertainty.level}
    return {"kind": "standard-error", "value": uncertainty.value}


def commensuration_key(estimand: Estimand) -> dict[str, object]:
    """§7.3: the projection with `control.identification` removed — the design
    key a weight table reads is the one member outside the key."""
    projection = estimand_projection(estimand)
    control = dict(projection["control"])  # type: ignore[arg-type]
    del control["identification"]
    projection["control"] = control
    return projection


def commensurable(a: Estimand, b: Estimand) -> bool:
    return commensuration_key(a) == commensuration_key(b)


def co_scoped(a: Mapping[str, Qualifier], b: Mapping[str, Qualifier]) -> bool:
    """Canonical map equality over two applicability maps (M5's). Outside the
    estimand and outside `commensurable`; a successor policy reads both."""
    return applicability_projection(a) == applicability_projection(b)


def check_estimate(estimate: Decimal, scale: str) -> Decimal:
    estimate = _finite(estimate, "estimate", UncertaintyRefused)
    if scale == "multiplicative" and estimate <= 0:
        raise UncertaintyRefused(f"estimate must be > 0 under a multiplicative scale, found {estimate}")
    return estimate


def check_uncertainty(uncertainty: Interval | StandardError, estimate: Decimal, scale: str) -> None:
    """§6's one meaning per kind: a two-sided central interval at `level` around
    the estimate on its own scale; a standard error on the scale's additive form."""
    if isinstance(uncertainty, Interval):
        low, high, level = (_finite(getattr(uncertainty, n), f"uncertainty.{n}", UncertaintyRefused) for n in ("low", "high", "level"))
        if not (low <= estimate <= high):
            raise UncertaintyRefused(f"uncertainty: the interval [{low}, {high}] excludes the estimate {estimate}")
        if not (0 < level < 1):
            raise UncertaintyRefused(f"uncertainty.level must lie in (0, 1), found {level}")
        if scale == "multiplicative" and low <= 0:
            raise UncertaintyRefused(f"uncertainty.low must be > 0 under a multiplicative scale, found {low}")
        return
    if isinstance(uncertainty, StandardError):
        if _finite(uncertainty.value, "uncertainty.value", UncertaintyRefused) < 0:
            raise UncertaintyRefused(f"a standard error is non-negative, found {uncertainty.value}")
        return
    raise UncertaintyRefused(f"uncertainty holds {type(uncertainty).__name__}, not Interval or StandardError")
```

- [ ] **Step 5: Run the tests**

Run: `uv run --frozen pytest tests/test_estimand.py tests/test_claim.py tests/test_decode.py`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add python/src/beliefs/estimand.py python/src/beliefs/errors.py python/src/beliefs/resolution.py python/tests/test_estimand.py
git commit -m "feat(estimand): build a typed estimand against its claim; commensurable and co_scoped (Q3, Q9)"
```

---

### Task 5: The decoder — `WireEstimand`, `decode_estimand`, `estimand_from_stored`, `applicability_from_stored`

**Files:**
- Modify: `python/src/beliefs/decode.py`
- Test: `python/tests/test_estimand_decode.py` (new)

**Interfaces:**
- Consumes: Task 4's values and `Estimand._checked`; `ProfileSpec.estimand()`.
- Produces: `WireEstimand(claim: str, operator: str, contrast: Mapping, measure: Mapping, reference: object, control: Mapping)`; `decode_estimand(wire, *, profile, snapshot) -> tuple[Estimand, BindingCheckReceipt]`; `estimand_from_stored(projection: Mapping, *, profile) -> Estimand` (no snapshot — restoration, like `claim_from_stored`'s posture on retirement, but with **no resolution at all**: a stored spec is typed against declarations, and membership was the freeze's check); `applicability_from_stored(projection: Mapping, *, profile, operator) -> Mapping[str, Qualifier]`; every ill-formed input refuses with `MalformedWireClaim`'s sibling `MalformedWireEstimand` (add to `errors.py` under `DecodeError`).

- [ ] **Step 1: Write the failing tests**

Create `python/tests/test_estimand_decode.py`:

```python
"""Round trips and refusals at the decode boundary (M11's shape, one artifact over)."""

from decimal import Decimal

import pytest
from test_estimand import E, I, L, M, O, build, parts  # noqa: F401 — fixtures re-exported by name

from beliefs.claim import Qualifier, Referent, build_claim
from beliefs.contract import domain
from beliefs.decode import WireEstimand, applicability_from_stored, decode_estimand, estimand_from_stored
from beliefs.errors import ContrastRefused, EstimandSortMismatch, MalformedWireEstimand
from beliefs.estimand import applicability_projection, build_applicability, estimand_projection
from beliefs.identity import v1
from beliefs.profile import compile_profile
from beliefs.resolution import build_snapshot


@pytest.fixture()
def profile(base_contract, testing_document):
    testing = domain.parse_domain_contract(testing_document, source="<test>", base=base_contract, predecessor=None)
    return compile_profile(base_contract, [testing])


@pytest.fixture()
def claim(profile):
    return build_claim(profile, operator="testing/affects", args=(Referent(E, "EX:gene-x"), Referent(O, "EX:pheno-y")), layer="causal", polarity="positive")


def test_a_projection_round_trips_through_canonical_text(profile, claim):
    estimand = build(profile, claim, build_snapshot(readable={}))
    projection = estimand_projection(estimand)
    restored = estimand_from_stored(v1.decode(v1.encode(projection)), profile=profile)
    assert estimand_projection(restored) == projection
    assert restored.reference == Decimal("0") and type(restored.reference) is Decimal


def test_decode_types_a_wire_value_and_resolves_it(profile, claim):
    from beliefs.projection import claim_identity

    wire = WireEstimand(
        claim=claim_identity(claim), operator="testing/affects",
        contrast={"slot": 0, "kind": "levels", "baseline": "EX:ndmm", "comparison": "EX:pd"},
        measure={"quantity": "EX:tpm", "scale": "additive"}, reference=Decimal("0"),
        control={"identification": "EX:observational", "conditioning": []},
    )
    estimand, receipt = decode_estimand(wire, profile=profile, snapshot=build_snapshot(readable={}))
    assert estimand_projection(estimand) == estimand_projection(build(profile, claim, build_snapshot(readable={})))
    assert "estimand:measure.quantity" in receipt.outcomes


@pytest.mark.parametrize("mutate,error", [
    (lambda p: p.pop("reference"), MalformedWireEstimand),
    (lambda p: p.__setitem__("extra", 1), MalformedWireEstimand),
    (lambda p: p["contrast"].__setitem__("kind", "levels-and-continuous"), MalformedWireEstimand),
    (lambda p: p["contrast"].__setitem__("slot", "0"), MalformedWireEstimand),
    (lambda p: p["contrast"].__setitem__("baseline", {"sort": E, "term": "EX:ndmm"}), EstimandSortMismatch),
    (lambda p: p["measure"].__setitem__("quantity", {"sort": 7, "term": "EX:tpm"}), MalformedWireEstimand),
    (lambda p: p["measure"].__setitem__("quantity", {"sort": "", "term": "EX:tpm"}), MalformedWireEstimand),
    (lambda p: p["measure"].__setitem__("quantity", {"term": "EX:tpm"}), MalformedWireEstimand),
    (lambda p: p["contrast"].__setitem__("comparison", {"sort": L, "term": "EX:ndmm"}), ContrastRefused),
    (lambda p: p.__setitem__("reference", "zero"), MalformedWireEstimand),
    (lambda p: p["control"].__setitem__("conditioning", "none"), MalformedWireEstimand),
])
def test_ill_formed_stored_projections_refuse_never_repair(profile, claim, mutate, error):
    projection = estimand_projection(build(profile, claim, build_snapshot(readable={})))
    mutate(projection)
    with pytest.raises(error):
        estimand_from_stored(projection, profile=profile)


def test_applicability_round_trips_and_refuses_an_undeclared_dimension(profile, claim):
    from beliefs.errors import UndeclaredDimension

    adults, _ = build_applicability(profile, claim, {"testing/population": Qualifier("generic", Referent("testing/cohort", "EX:adults"))}, snapshot=build_snapshot(readable={}))
    projection = applicability_projection(adults)
    restored = applicability_from_stored(v1.decode(v1.encode(projection)), profile=profile, operator="testing/affects")
    assert applicability_projection(restored) == projection
    with pytest.raises(UndeclaredDimension):
        applicability_from_stored({"testing/regime": projection["testing/population"]}, profile=profile, operator="testing/affects")
```

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run --frozen pytest tests/test_estimand_decode.py`
Expected: `ImportError: cannot import name 'WireEstimand' from 'beliefs.decode'`.

- [ ] **Step 3: Implement**

In `python/src/beliefs/errors.py`, after `MalformedWireClaim`:

```python
class MalformedWireEstimand(DecodeError):
    """A wire estimand that does not have the shape a wire estimand has at all —
    a missing or extra member, a non-integer slot, a non-Decimal reference, a
    kind outside the grammar — refused before anything is typed."""
```

In `python/src/beliefs/decode.py`, add to `__all__` and append:

```python
from decimal import Decimal

from beliefs.errors import MalformedWireEstimand
from beliefs.estimand import ContinuousContrast, Control, Estimand, LevelsContrast, Measure

_WIRE_ESTIMAND_KEYS = frozenset({"claim", "operator", "contrast", "measure", "reference", "control"})


@dataclass(frozen=True)
class WireEstimand:
    """An estimand as it arrives — identifiers, tags and decimals, nothing typed.
    Freely constructible for `WireClaim`'s reason; every field is checked below."""

    claim: str
    operator: str
    contrast: Mapping[str, object]
    measure: Mapping[str, object]
    reference: object
    control: Mapping[str, object]


def _wire_referent(value: object, where: str, *, declared: str) -> Referent:
    """A referent on the wire, in one of two forms and never a blend of them.

    The **bare-term** form (the decode route) carries a term only; its sort is
    the declaration's. The **stored** form (`{sort, term}`, the projection's)
    carries an explicit sort that must be a non-empty string — it is passed
    through unchanged, and `Estimand._checked` then refuses it if it is not the
    declared sort. Nothing here substitutes the declaration's sort for a stored
    one that is missing, empty or not a string: that would repair a malformed
    record on the way in, which is the one thing a decoder must not do."""
    if isinstance(value, Mapping):
        if set(value) != {"sort", "term"}:
            raise MalformedWireEstimand(f"{where}: a stored referent is exactly {{sort, term}}")
        return Referent(sort=_require_text(value["sort"], f"{where}.sort"), term=_require_text(value["term"], f"{where}.term"))
    return Referent(sort=declared, term=_require_text(value, where))


def _decimal(value: object, where: str) -> Decimal:
    if type(value) is not Decimal:
        raise MalformedWireEstimand(f"{where}: expected a Decimal, found {type(value).__name__}")
    return value


def _slot(value: object, where: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise MalformedWireEstimand(f"{where}: slot is an integer, found {value!r}")
    return value


def _typed_estimand(wire: WireEstimand, profile: ProfileSpec) -> Estimand:
    if not isinstance(wire, WireEstimand):
        raise MalformedWireEstimand(f"decode_estimand takes a WireEstimand, found {type(wire).__name__}")
    claim = _require_text(wire.claim, "claim")
    operator = _require_text(wire.operator, "operator")
    declaration = profile.estimand(operator)
    contrast_body, measure_body, control_body = (
        _mapping_body(getattr(wire, name), name) for name in ("contrast", "measure", "control")
    )
    kind = _require_text(contrast_body.get("kind"), "contrast.kind")
    if kind not in profile.estimand_grammar.contrast_kinds:
        raise MalformedWireEstimand(f"contrast.kind {kind!r} is outside {list(profile.estimand_grammar.contrast_kinds)}")
    slot = _slot(contrast_body.get("slot"), "contrast.slot")
    if kind == "levels":
        _exact_keys(contrast_body, {"slot", "kind", "baseline", "comparison"}, "contrast")
        level_sort = declaration.level_sorts.get(str(slot), "")
        contrast: LevelsContrast | ContinuousContrast = LevelsContrast(
            slot=slot,
            baseline=_wire_referent(contrast_body["baseline"], "contrast.baseline", declared=level_sort),
            comparison=_wire_referent(contrast_body["comparison"], "contrast.comparison", declared=level_sort),
        )
    else:
        _exact_keys(contrast_body, {"slot", "kind", "quantity", "increment"}, "contrast")
        contrast = ContinuousContrast(
            slot=slot,
            quantity=_wire_referent(contrast_body["quantity"], "contrast.quantity", declared=declaration.measure_sort),
            increment=_decimal(contrast_body["increment"], "contrast.increment"),
        )
    _exact_keys(measure_body, {"quantity", "scale"}, "measure")
    measure = Measure(
        quantity=_wire_referent(measure_body["quantity"], "measure.quantity", declared=declaration.measure_sort),
        scale=_require_text(measure_body["scale"], "measure.scale"),
    )
    _exact_keys(control_body, {"identification", "conditioning"}, "control")
    conditioning = control_body["conditioning"]
    if isinstance(conditioning, (str, bytes)) or not isinstance(conditioning, Sequence):
        raise MalformedWireEstimand("control.conditioning is a sequence of referents")
    control = Control(
        identification=_wire_referent(control_body["identification"], "control.identification", declared=declaration.identification_sort),
        conditioning=tuple(
            _wire_referent(member, f"control.conditioning[{i}]", declared=declaration.conditioning_sort)
            for i, member in enumerate(conditioning)
        ),
    )
    return Estimand._checked(
        profile, claim=claim, operator=operator, contrast=contrast, measure=measure,
        reference=_decimal(wire.reference, "reference"), control=control,
    )


def _mapping_body(value: object, where: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise MalformedWireEstimand(f"{where}: expected a mapping, found {type(value).__name__}")
    for key in value:
        _require_text(key, f"{where}: a member name")
    return value


def _exact_keys(body: Mapping[str, object], keys: set[str], where: str) -> None:
    if set(body) != keys:
        raise MalformedWireEstimand(f"{where}: members are exactly {sorted(keys)}, found {sorted(body)}; refused, never repaired")


def decode_estimand(
    wire: WireEstimand, *, profile: ProfileSpec, snapshot: ResolutionSnapshot
) -> tuple[Estimand, BindingCheckReceipt]:
    """Type and resolve a wire estimand, or refuse — `decode_claim`'s discipline."""
    from beliefs.estimand import _referent_positions, _resolve_all

    if not isinstance(snapshot, ResolutionSnapshot):
        raise MalformedWireEstimand("snapshot is not a ResolutionSnapshot")
    estimand = _typed_estimand(wire, profile)
    outcomes = _resolve_all(profile, snapshot, {ReferentPosition.estimand(p).label(): r for p, r in _referent_positions(estimand).items()})
    return estimand, _emit_receipt(estimand.claim, snapshot, outcomes)


def estimand_from_stored(projection: Mapping[str, object], *, profile: ProfileSpec) -> Estimand:
    """Restore a typed estimand from a stored spec's projection member. Typed
    against the declarations, resolved against nothing: restoration is not
    authoring, and the freeze already performed the membership check."""
    if not isinstance(projection, Mapping) or set(projection) != _WIRE_ESTIMAND_KEYS:
        raise MalformedWireEstimand(f"a stored estimand carries exactly {sorted(_WIRE_ESTIMAND_KEYS)}")
    wire = WireEstimand(**{key: projection[key] for key in _WIRE_ESTIMAND_KEYS})  # type: ignore[arg-type]
    return _typed_estimand(wire, profile)


def applicability_from_stored(projection: Mapping[str, object], *, profile: ProfileSpec, operator: str) -> Mapping[str, Qualifier]:
    """Restore an applicability map: the same checks a claim's qualifiers get."""
    from types import MappingProxyType

    if not isinstance(projection, Mapping):
        raise MalformedWireEstimand("a stored applicability is a mapping")
    qualifiers: dict[str, Qualifier] = {}
    for dimension, body in projection.items():
        where = f"applicability[{dimension!r}]"
        declared = profile.dimensions.get(_require_text(dimension, "a dimension"))
        if declared is None:
            raise UndeclaredDimension(f"no dimension {dimension!r} in this profile")
        if not isinstance(body, Mapping) or set(body) != {"quantifier", "restriction"}:
            raise MalformedWireEstimand(f"{where}: exactly quantifier and restriction")
        qualifiers[dimension] = Qualifier(
            quantifier=_require_text(body["quantifier"], f"{where}.quantifier"),
            restriction=_wire_referent(body["restriction"], f"{where}.restriction", declared=declared.restriction_sort),
        )
    declaration = profile.operator(operator)
    permitted = set(declaration.dimensions)
    for dimension, qualifier in qualifiers.items():
        if dimension not in permitted:
            raise UndeclaredDimension(f"{operator!r} does not permit dimension {dimension!r}")
        if qualifier.quantifier not in profile.claim_grammar.quantifiers:
            raise UnknownQuantifier(f"quantifier {qualifier.quantifier!r} is outside the kernel's closed set")
        if qualifier.restriction.sort != profile.dimensions[dimension].restriction_sort:
            raise RestrictionSortMismatch(f"{dimension!r} restricts to {profile.dimensions[dimension].restriction_sort!r}")
    return MappingProxyType(qualifiers)
```

(`UnknownQuantifier`, `RestrictionSortMismatch` imported from `beliefs.errors`.)

- [ ] **Step 4: Run the tests**

Run: `uv run --frozen pytest tests/test_estimand_decode.py tests/test_estimand.py tests/test_decode.py`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add python/src/beliefs/decode.py python/src/beliefs/errors.py python/tests/test_estimand_decode.py
git commit -m "feat(decode): decode and restore typed estimands and applicability maps (Q3)"
```

---

### Task 6: The typed spec — `SpecDraft`, `FrozenSpec`, the grammar member, `restore(..., profile=)`, the readers

**Files:**
- Modify: `python/src/beliefs/spec.py` (`SpecDraft`, `FrozenSpec`, `_facet_projection`, `_FROZEN_MEMBERS`, `_TEXT_MEMBERS`, `restore`, `revise`)
- Modify: `python/src/beliefs/errors.py` (`PreGrammarSpec(UnfreezableSpec)`, `PreGrammarAssessment(MalformedRecord)`)
- Modify: `python/src/beliefs/stored.py:1034-1045` (`analysis_spec_value(node, *, profile)`)
- Modify callers: `python/src/beliefs/corpus.py:2703`, `python/src/beliefs/audit.py:260,275` (`check_analysis_spec(node, *, profile)`, `stored_specs(view, *, profile)`), `python/tools/reproduction/rederive.py:67`, `python/tools/reproduction/close.py:28`
- Modify: `python/tests/fixtures_cut3.py` (typed draft), `python/tests/test_spec.py`
- Test: `python/tests/test_spec.py`

**Interfaces:**
- Consumes: `Estimand`, `estimand_projection`, `applicability_projection` (Task 4); `estimand_from_stored`, `applicability_from_stored` (Task 5); `ESTIMAND_GRAMMAR` (Task 1).
- Produces: `SpecDraft.estimand: Estimand`, `SpecDraft.applicability: Mapping[str, Qualifier]` (same on `FrozenSpec`); the projection member `estimand_grammar: "science.estimand.v1"`; `restore(identity, projection, *, profile)`; `stored.analysis_spec_value(node, *, profile)`; `audit.stored_specs(view, *, profile)`; `audit.check_analysis_spec(node, *, profile)`; `fixtures_cut3.TESTING_PROFILE`, `TESTING_CLAIM`, `typed_estimand()`, `typed_applicability()`.

- [ ] **Step 1: Give the fixtures a typed draft**

In `python/tests/fixtures_cut3.py`, near `spec_rules`:

```python
from decimal import Decimal
from pathlib import Path

from beliefs.claim import Referent, build_claim
from beliefs.contract import parse_domain_contract
from beliefs.contract.document import load_document
from beliefs.estimand import Control, LevelsContrast, Measure, build_applicability, build_estimand
from beliefs.profile import compile_profile, shipped_base_contract
from beliefs.resolution import build_snapshot

_TESTING = Path(__file__).resolve().parents[2] / "fixtures" / "contracts" / "testing.yaml"
TESTING_PROFILE = compile_profile(
    shipped_base_contract(),
    [parse_domain_contract(load_document(_TESTING, source=str(_TESTING)), source=str(_TESTING), base=shipped_base_contract(), predecessor=None)],
)
TESTING_CLAIM = build_claim(
    TESTING_PROFILE,
    operator="testing/affects",
    args=(Referent("testing/entity", "EX:gene-x"), Referent("testing/outcome", "EX:pheno-y")),
    layer="causal",
    polarity="positive",
)
UNCONSULTED = build_snapshot(readable={})


def typed_estimand(**overrides):
    fields = {
        "contrast": LevelsContrast(slot=0, baseline=Referent("testing/level", "EX:ndmm"), comparison=Referent("testing/level", "EX:pd")),
        "measure": Measure(quantity=Referent("testing/measure", "EX:tpm"), scale="additive"),
        "reference": Decimal("0"),
        "control": Control(identification=Referent("testing/identification", "EX:observational"), conditioning=()),
    }
    fields.update(overrides)
    estimand, _receipt = build_estimand(TESTING_PROFILE, TESTING_CLAIM, snapshot=UNCONSULTED, **fields)
    return estimand


def typed_applicability(qualifiers=None):
    applicability, _receipt = build_applicability(TESTING_PROFILE, TESTING_CLAIM, qualifiers or {}, snapshot=UNCONSULTED)
    return applicability
```

and in `spec_draft`, replace `"estimand": "the effect of x on y"` with `"estimand": typed_estimand()` and `"applicability": "the sampled population"` with `"applicability": typed_applicability()`.

- [ ] **Step 2: Write the failing tests**

Append to `python/tests/test_spec.py`:

```python
# --- estimand typing: the typed members, the grammar member, restoration (Q7, Q10) ---


def test_the_projection_carries_the_grammar_and_typed_members():
    from beliefs.contract.base import ESTIMAND_GRAMMAR
    from beliefs.estimand import applicability_projection, estimand_projection
    from beliefs.spec import frozen_projection

    spec = freeze(draft(), held_rules=held_rules())
    projection = frozen_projection(spec)
    assert projection["estimand_grammar"] == ESTIMAND_GRAMMAR
    assert projection["estimand"] == estimand_projection(spec.estimand)
    assert projection["applicability"] == applicability_projection(spec.applicability)


def test_a_string_estimand_is_refused_at_the_draft():
    with pytest.raises(MalformedSpec, match="Estimand"):
        draft(estimand="the effect of x on y")


@pytest.mark.parametrize("override", [
    {"contrast": __import__("beliefs.estimand", fromlist=["LevelsContrast"]).LevelsContrast(
        slot=0,
        baseline=__import__("beliefs.claim", fromlist=["Referent"]).Referent("testing/level", "EX:pd"),
        comparison=__import__("beliefs.claim", fromlist=["Referent"]).Referent("testing/level", "EX:ndmm"),
    )},
    {"reference": Decimal("0.5")},
])
def test_each_estimand_member_moves_the_spec_identity(override):
    from fixtures_cut3 import typed_estimand

    assert freeze(draft(), held_rules=held_rules()).identity != freeze(draft(estimand=typed_estimand(**override)), held_rules=held_rules()).identity


def test_applicability_moves_the_spec_identity():
    from fixtures_cut3 import typed_applicability

    from beliefs.claim import Qualifier, Referent

    adults = typed_applicability({"testing/population": Qualifier("generic", Referent("testing/cohort", "EX:adults"))})
    assert freeze(draft(), held_rules=held_rules()).identity != freeze(draft(applicability=adults), held_rules=held_rules()).identity


def test_restore_round_trips_the_typed_members():
    from fixtures_cut3 import TESTING_PROFILE

    from beliefs.spec import frozen_projection, restore

    spec = freeze(draft(), held_rules=held_rules())
    restored = restore(spec.identity, v1.encode(frozen_projection(spec)), profile=TESTING_PROFILE)
    assert restored.estimand == spec.estimand and dict(restored.applicability) == dict(spec.applicability)
    assert restored.identity == spec.identity


def test_a_pre_grammar_projection_is_refused_by_name():
    from fixtures_cut3 import TESTING_PROFILE

    from beliefs.errors import PreGrammarSpec, UnfreezableSpec
    from beliefs.spec import frozen_projection, restore

    spec = freeze(draft(), held_rules=held_rules())
    projection = frozen_projection(spec)
    del projection["estimand_grammar"]
    projection["estimand"] = "the effect of x on y"
    projection["applicability"] = "the sampled population"
    identity = v1.digest(SPEC_DOMAIN, projection)
    with pytest.raises(PreGrammarSpec, match="pre-grammar spec") as caught:
        restore(identity, v1.encode(projection), profile=TESTING_PROFILE)
    assert isinstance(caught.value, UnfreezableSpec)


def test_another_grammar_identity_is_malformed_not_pre_grammar():
    from fixtures_cut3 import TESTING_PROFILE

    from beliefs.spec import frozen_projection, restore

    spec = freeze(draft(), held_rules=held_rules())
    projection = frozen_projection(spec)
    projection["estimand_grammar"] = "science.estimand.v2"
    with pytest.raises(MalformedRecord, match="estimand_grammar"):
        restore(v1.digest(SPEC_DOMAIN, projection), v1.encode(projection), profile=TESTING_PROFILE)


def test_a_malformed_typed_member_restores_as_a_record_error():
    from fixtures_cut3 import TESTING_PROFILE

    from beliefs.errors import RecordError
    from beliefs.spec import frozen_projection, restore

    spec = freeze(draft(), held_rules=held_rules())
    projection = frozen_projection(spec)
    projection["estimand"]["measure"]["quantity"] = {"sort": "", "term": "EX:tpm"}
    with pytest.raises(RecordError, match="do not restore"):
        restore(v1.digest(SPEC_DOMAIN, projection), v1.encode(projection), profile=TESTING_PROFILE)


def test_revise_copies_the_typed_members():
    from fixtures_cut3 import typed_estimand

    original = freeze(draft(), held_rules=held_rules())
    successor = revise(original, edits={"estimand": typed_estimand(reference=Decimal("1"))}, held_rules=held_rules(), recorded_failures=frozenset())
    assert successor.supersedes == original.identity and successor.estimand.reference == Decimal("1")
    assert dict(successor.applicability) == dict(original.applicability)
```

- [ ] **Step 3: Run them to verify they fail**

Run: `uv run --frozen pytest tests/test_spec.py`
Expected: the new tests fail (`KeyError: 'estimand_grammar'`, `TypeError` on `restore`'s unexpected `profile`, a `str` draft accepted); the pre-existing tests fail at collection of `fixtures_cut3` only if Step 1 was skipped.

- [ ] **Step 4: Implement**

`python/src/beliefs/errors.py`, after `UnfreezableSpec`:

```python
class PreGrammarSpec(UnfreezableSpec):
    """A stored spec projection with no `estimand_grammar` member: frozen
    before `science.estimand.v1`. Refused by name, never coerced; a corpus
    holding one was not recreated (estimand-typing decision 10)."""


class PreGrammarAssessment(MalformedRecord):
    """A stored assessment facet whose estimand is prose: minted before
    `science.estimand.v1`. Refused by name, never coerced (decision 10)."""
```

`python/src/beliefs/spec.py`:

```python
from beliefs.claim import Qualifier
from beliefs.contract.base import ESTIMAND_GRAMMAR
from beliefs.decode import applicability_from_stored, estimand_from_stored
from beliefs.errors import PreGrammarSpec
from beliefs.estimand import Estimand, applicability_projection, estimand_projection
from beliefs.profile import ProfileSpec
```

In `SpecDraft` and `FrozenSpec`, change `estimand: str` to `estimand: Estimand` and `applicability: str` to `applicability: Mapping[str, Qualifier]`; add to `SpecDraft.__post_init__`:

```python
        if type(self.estimand) is not Estimand:
            raise MalformedSpec(f"estimand is a typed Estimand built by build_estimand, found {type(self.estimand).__name__}")
        if not isinstance(self.applicability, Mapping) or not all(isinstance(q, Qualifier) for q in self.applicability.values()):
            raise MalformedSpec("applicability is a mapping of dimension → Qualifier built by build_applicability")
        object.__setattr__(self, "applicability", MappingProxyType(dict(self.applicability)))
```

In `_facet_projection`, replace the two string entries and add the grammar:

```python
        "estimand_grammar": ESTIMAND_GRAMMAR,
        "estimand": estimand_projection(draft.estimand),
        ...
        "applicability": applicability_projection(draft.applicability),
```

```python
_FROZEN_MEMBERS = frozenset({
    "target", "estimand_grammar", "estimand", "method", "assumptions", "falsification", "input_roles", "applicability",
    "interpretation_rule", "equivalence_rule", "parameters", "nondeterminism", "rule_bindings",
})
_TEXT_MEMBERS = ("target", "method", "assumptions", "falsification", "interpretation_rule", "equivalence_rule")
```

`restore` becomes `def restore(identity: str, projection: bytes, *, profile: ProfileSpec) -> FrozenSpec:` and, right after `mapping = v1.decode(projection)` succeeds and before the members check:

```python
    if isinstance(mapping, dict) and "estimand_grammar" not in mapping:
        raise PreGrammarSpec(
            f"{where}: pre-grammar spec — frozen before {ESTIMAND_GRAMMAR}, its estimand and applicability are prose. "
            "Refused, never coerced: a corpus holding one was not recreated (estimand-typing decision 10)."
        )
```

then after the digest check:

```python
    if mapping["estimand_grammar"] != ESTIMAND_GRAMMAR:
        raise MalformedRecord(f"{where}: estimand_grammar is {mapping['estimand_grammar']!r}, not {ESTIMAND_GRAMMAR!r}")
    try:
        estimand = estimand_from_stored(mapping["estimand"], profile=profile)
        applicability = applicability_from_stored(mapping["applicability"], profile=profile, operator=estimand.operator)
    except (DecodeError, EstimandError, ClaimError, ProfileError) as refused:
        # Translated here, not propagated: the audit and `stored_specs` catch
        # `RecordError`, and a decode-family error escaping a stored reader would
        # abort an audit instead of becoming its finding.
        raise MalformedRecord(f"{where}: the typed members do not restore: {refused}") from refused
```

(import `DecodeError`, `EstimandError`, `ClaimError`, `ProfileError` from `beliefs.errors`) and pass `estimand=estimand, applicability=applicability` to `_mint_frozen_spec` (the `**text` no longer carries them). `revise` casts `estimand` to `Estimand` and `applicability` to `Mapping[str, Qualifier]` from `edits`/`original` exactly as the other members.

`python/src/beliefs/stored.py`: `def analysis_spec_value(node: Node, *, profile: ProfileSpec) -> FrozenSpec:` calling `restore(facet["identity"], facet["projection"].encode("utf-8"), profile=profile)` (import `ProfileSpec` under `TYPE_CHECKING` if `stored` must stay import-light; `restore` is already imported).

Callers: `corpus._refuse_r20_contradiction` becomes an instance method reading `self._profile` and passes `profile=self._profile`; `audit.check_analysis_spec(node, *, profile)` and `audit.stored_specs(view, *, profile)` pass it through, `audit_corpus` supplies its own `profile`; `close.evidence_for(view)` becomes `evidence_for(view, profile)` called with `vocabulary.profile()`; `rederive.py:67` passes `profile=profile()`.

- [ ] **Step 5: Run the tests**

Run: `uv run --frozen pytest tests/test_spec.py tests/test_assess.py tests/test_audit.py tests/test_reproduction_driver.py tests/test_verification_publication.py tests/test_succession*.py`
Expected: `test_spec.py` green; `test_assess.py`, `test_audit.py` and `test_verification_publication.py` will show failures that Task 7 owns (they build `AssessmentValue` with string members) — record the count in the commit body and proceed; nothing else regresses.

- [ ] **Step 6: Commit**

```bash
git add python/src/beliefs/spec.py python/src/beliefs/errors.py python/src/beliefs/stored.py python/src/beliefs/corpus.py python/src/beliefs/audit.py python/tools/reproduction/rederive.py python/tools/reproduction/close.py python/tests/fixtures_cut3.py python/tests/test_spec.py
git commit -m "feat(spec): type the estimand and applicability members; refuse pre-grammar specs by name (Q7, Q10)"
```

---

### Task 7: The typed assessment — `AssessmentValue`, the constructor's checks, the stored record

**Files:**
- Modify: `python/src/beliefs/record.py:84-115` (`AssessmentValue`)
- Modify: `python/src/beliefs/assess.py:70-95` (`build_assessment`)
- Modify: `python/src/beliefs/stored.py` (`assessment_node`, `assessment_value(node, *, profile)`, new `assessment_identity(node)`), `python/src/beliefs/succession.py:231`, `python/src/beliefs/corpus.py:2946`, `python/src/beliefs/evaluation.py:221`
- Modify: `python/tests/test_records.py`, `python/tests/test_assess.py`, `python/tests/fixtures_cut3.py:288-310` (`interp`, `result_sensitive`), `python/tests/test_audit.py`, `python/tests/test_verification_publication.py`, `python/tests/succession_fixtures.py`, `python/tests/verification_fixtures.py` (every `AssessmentValue(...)` and `assessment_node(...)` site gains `estimand=typed_estimand(), applicability=typed_applicability()`)
- Test: `python/tests/test_records.py`, `python/tests/test_assess.py`

**Interfaces:**
- Produces: `AssessmentValue(spec, run, proposition, outcome, interpretation_rule, estimand: Estimand, applicability: Mapping[str, Qualifier], estimate: Decimal | None = None, uncertainty: Interval | StandardError | None = None)`; `stored.assessment_node(slug, *, title, spec, run, proposition, outcome, interpretation_rule, estimand, applicability, estimate=None, uncertainty=None)` writing a `typed` member of canonical text; `stored.assessment_value(node, *, profile)`; `stored.AssessmentRef(spec, run, proposition)` with `identity()`, and `stored.assessment_reference(node) -> AssessmentRef` reading only those three members.

- [ ] **Step 1: Write the failing tests**

In `python/tests/test_records.py`, rewrite the parametrized optional-field test:

```python
    def test_each_typed_member_moves_the_facet_digest(self):
        from decimal import Decimal

        from fixtures_cut3 import typed_applicability, typed_estimand

        from beliefs.claim import Qualifier, Referent
        from beliefs.estimand import Interval, StandardError

        base = assessment()
        assert base.facet_digest() != assessment(estimate=Decimal("0.4")).facet_digest()
        assert assessment(estimate=Decimal("0.4")).facet_digest() != assessment(estimate=Decimal("0.4"), uncertainty=Interval(Decimal("0.1"), Decimal("0.7"), Decimal("0.95"))).facet_digest()
        assert assessment(estimate=Decimal("0.4"), uncertainty=StandardError(Decimal("0.1"))).facet_digest() != assessment(estimate=Decimal("0.4")).facet_digest()
        assert base.facet_digest() != assessment(estimand=typed_estimand(reference=Decimal("1"))).facet_digest()
        adults = typed_applicability({"testing/population": Qualifier("generic", Referent("testing/cohort", "EX:adults"))})
        assert base.facet_digest() != assessment(applicability=adults).facet_digest()

    def test_a_string_member_is_refused(self):
        with pytest.raises(MalformedRecord):
            assessment(estimate="0.4")
        with pytest.raises(MalformedRecord):
            assessment(estimand="the effect of x on y")

    def test_the_numerical_invariants_hold_at_construction(self):
        from decimal import Decimal

        from beliefs.estimand import Interval, StandardError

        with pytest.raises(MalformedRecord, match="non-negative"):
            assessment(estimate=Decimal("0.4"), uncertainty=StandardError(Decimal("-0.1")))
        with pytest.raises(MalformedRecord, match="excludes"):
            assessment(estimate=Decimal("0.4"), uncertainty=Interval(Decimal("0.5"), Decimal("0.7"), Decimal("0.95")))
        with pytest.raises(MalformedRecord, match="no estimate"):
            assessment(uncertainty=StandardError(Decimal("0.1")))
```

(`assessment()`'s default fields gain `estimand=typed_estimand()` and `applicability=typed_applicability()`.)

Append to `python/tests/test_assess.py`:

```python
# --- Q5: estimate and uncertainty are typed on the spec's scale ---


def _rule(output):
    return {"impl-interp-1": RuleImplementation(identity="impl-interp-1", evaluate=lambda manifest: output, fixtures=())}


@pytest.mark.parametrize("output,reason", [
    ({"outcome": "supported", "estimate": 0.4}, "Decimal"),
    ({"outcome": "supported", "estimate": "0.4"}, "Decimal"),
    ({"outcome": "supported", "estimate": Decimal("0.4"), "uncertainty": {"kind": "interval", "low": Decimal("0.5"), "high": Decimal("0.7"), "level": Decimal("0.95")}}, "excludes the estimate"),
    ({"outcome": "supported", "estimate": Decimal("0.4"), "uncertainty": {"kind": "interval", "low": Decimal("0.1"), "high": Decimal("0.7"), "level": Decimal("1")}}, "level"),
    ({"outcome": "supported", "estimate": Decimal("0.4"), "uncertainty": {"kind": "standard-error", "value": Decimal("-0.1")}}, "non-negative"),
    ({"outcome": "supported", "estimate": Decimal("0.4"), "reference": Decimal("0")}, "reference"),
    ({"outcome": "supported", "scale": "additive"}, "scale"),
    ({"outcome": "supported", "uncertainty": {"kind": "standard-error", "value": Decimal("0.1")}}, "estimate"),
])
def test_an_ill_typed_rule_output_is_a_finding_never_inconclusive(minted, output, reason):
    derived = build_assessment(minted.run, specs={minted.run.recipe.spec_identity: minted.spec}, implementations=_rule(output))
    assert isinstance(derived, AssessmentFinding) and reason in derived.reason
    assert "inconclusive" not in derived.reason


def test_a_well_typed_output_mints_typed_members(minted):
    output = {"outcome": "supported", "estimate": Decimal("0.4"), "uncertainty": {"kind": "interval", "low": Decimal("0.1"), "high": Decimal("0.7"), "level": Decimal("0.95")}}
    derived = build_assessment(minted.run, specs={minted.run.recipe.spec_identity: minted.spec}, implementations=_rule(output))
    assert isinstance(derived, AssessmentValue)
    assert derived.estimate == Decimal("0.4") and derived.uncertainty.level == Decimal("0.95")
    assert derived.estimand == minted.spec.estimand and dict(derived.applicability) == dict(minted.spec.applicability)


def test_a_multiplicative_estimate_must_be_positive(minted):
    from fixtures_cut3 import typed_estimand
    from beliefs.estimand import Measure
    from beliefs.claim import Referent

    spec = freeze(spec_draft(estimand=typed_estimand(measure=Measure(Referent("testing/measure", "EX:hr"), "multiplicative"), reference=Decimal("1"))), held_rules=spec_rules())
    run = run_assessment_under(spec)  # the module's helper that executes a closure under a given frozen spec
    derived = build_assessment(run, specs={spec.identity: spec}, implementations=_rule({"outcome": "supported", "estimate": Decimal("0")}))
    assert isinstance(derived, AssessmentFinding) and "multiplicative" in derived.reason
```

(`run_assessment_under` is the existing module pattern for minting a run under a spec — `memory_assessment` with the spec supplied; if `test_assess.py` has no such helper, add one beside `minted` that calls `run_assessment(tmp_path_factory.mktemp("mult"), spec=spec)` and returns `outcome.run`.)

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run --frozen pytest tests/test_records.py tests/test_assess.py`
Expected: red — string members accepted, `estimand` an unexpected keyword on `assessment_node`, float estimates minted.

- [ ] **Step 3: Implement the value**

`python/src/beliefs/record.py`:

```python
from decimal import Decimal

from beliefs.claim import Qualifier
from beliefs.errors import UncertaintyRefused
from beliefs.estimand import (
    Estimand,
    Interval,
    StandardError,
    applicability_projection,
    check_estimate,
    check_uncertainty,
    estimand_projection,
    uncertainty_projection,
)


@sealed
@final
@dataclass(frozen=True)
class AssessmentValue:
    spec: str
    run: str
    proposition: str
    outcome: str
    interpretation_rule: str
    estimand: Estimand
    applicability: Mapping[str, Qualifier]
    estimate: Decimal | None = None
    uncertainty: Interval | StandardError | None = None

    def __post_init__(self) -> None:
        if self.outcome not in OUTCOMES:
            raise MalformedRecord(f"outcome {self.outcome!r} is outside the closed set {OUTCOMES}")
        if type(self.estimand) is not Estimand:
            raise MalformedRecord(f"estimand is a typed Estimand, found {type(self.estimand).__name__}")
        if not isinstance(self.applicability, Mapping) or not all(isinstance(q, Qualifier) for q in self.applicability.values()):
            raise MalformedRecord("applicability is a mapping of dimension → Qualifier")
        if self.estimate is not None and type(self.estimate) is not Decimal:
            raise MalformedRecord(f"estimate is a Decimal or absent, found {type(self.estimate).__name__}")
        if self.uncertainty is not None and not isinstance(self.uncertainty, (Interval, StandardError)):
            raise MalformedRecord(f"uncertainty is an Interval, a StandardError or absent, found {type(self.uncertainty).__name__}")
        # The numerical invariants (estimand-typing §6) hold at **every**
        # construction — the constructor's, the stored reader's, a test's — so a
        # stored record cannot carry a negative standard error or an interval
        # that excludes its estimate any more than a derived one can.
        try:
            if self.estimate is not None:
                check_estimate(self.estimate, self.estimand.measure.scale)
            if self.uncertainty is not None:
                if self.estimate is None:
                    raise UncertaintyRefused("an uncertainty with no estimate to be uncertain about")
                check_uncertainty(self.uncertainty, self.estimate, self.estimand.measure.scale)
        except UncertaintyRefused as refused:
            raise MalformedRecord(str(refused)) from refused
        object.__setattr__(self, "applicability", MappingProxyType(dict(self.applicability)))

    def identity(self) -> str:
        return v1.digest(ASSESSMENT_DOMAIN, {"spec": self.spec, "run": self.run, "proposition": self.proposition})

    def typed_projection(self) -> dict[str, object]:
        """The typed members, as one canonical mapping: what the stored record
        carries as text and what the facet digest covers. Absent optionals are
        omitted, never null."""
        typed: dict[str, object] = {
            "estimand": estimand_projection(self.estimand),
            "applicability": applicability_projection(self.applicability),
        }
        if self.estimate is not None:
            typed["estimate"] = self.estimate
        if self.uncertainty is not None:
            typed["uncertainty"] = uncertainty_projection(self.uncertainty)
        return typed

    def facet_digest(self) -> str:
        return v1.digest(
            ASSESSMENT_FACET_DOMAIN,
            {"proposition": self.proposition, "outcome": self.outcome, "interpretation_rule": self.interpretation_rule, **self.typed_projection()},
        )
```

- [ ] **Step 4: Implement the constructor's checks**

In `python/src/beliefs/assess.py`, replace the block from `raw = implementation.evaluate(run.result)` through `return AssessmentValue(...)`:

```python
        raw = implementation.evaluate(run.result)
        if not isinstance(raw, Mapping):
            raise TypeError("the interpretation rule returned no facet mapping")
        derived = cast(Mapping[str, object], raw)
        extra = sorted(set(derived) - {"outcome", "estimate", "uncertainty"})
        if extra:
            raise TypeError(
                f"the interpretation rule returned {extra}; a rule yields outcome, estimate and uncertainty only — "
                "the reference and scale are the spec's, and a rule restating them is a rule that lies (estimand-typing §6)"
            )
        outcome = derived.get("outcome")
        if type(outcome) is not str:
            raise TypeError("the interpretation rule returned no string outcome")
        scale = spec.estimand.measure.scale
        estimate = derived.get("estimate")
        if estimate is not None:
            estimate = check_estimate(cast(Decimal, estimate), scale)
        uncertainty = _typed_uncertainty(derived.get("uncertainty"))
        if uncertainty is not None:
            if estimate is None:
                raise TypeError("the interpretation rule returned an uncertainty with no estimate to be uncertain about")
            check_uncertainty(uncertainty, estimate, scale)
        return AssessmentValue(
            spec=spec.identity,
            run=run_address,
            proposition=spec.target,
            outcome=outcome,
            interpretation_rule=spec.interpretation_rule,
            estimand=spec.estimand,
            applicability=spec.applicability,
            estimate=estimate,
            uncertainty=uncertainty,
        )
```

and add the helper:

```python
def _typed_uncertainty(value: object) -> Interval | StandardError | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise UncertaintyRefused(f"uncertainty is a mapping with a kind, found {type(value).__name__}")
    kind = value.get("kind")
    if kind == "interval" and set(value) == {"kind", "low", "high", "level"}:
        return Interval(low=cast(Decimal, value["low"]), high=cast(Decimal, value["high"]), level=cast(Decimal, value["level"]))
    if kind == "standard-error" and set(value) == {"kind", "value"}:
        return StandardError(value=cast(Decimal, value["value"]))
    raise UncertaintyRefused(f"uncertainty kind {kind!r} with members {sorted(value)} is neither interval nor standard-error")
```

(imports: `from decimal import Decimal`; `from beliefs.estimand import Interval, StandardError, check_estimate, check_uncertainty`; `from beliefs.errors import UncertaintyRefused`. The enclosing `except Exception` already turns every raise into `AssessmentFinding(reason="evaluation-failed: …")`.)

- [ ] **Step 5: Implement the stored record**

`python/src/beliefs/stored.py`:

```python
def assessment_node(
    slug: str,
    *,
    title: str,
    spec: str,
    run: str,
    proposition: str,
    outcome: str,
    interpretation_rule: str,
    estimand: Estimand,
    applicability: Mapping[str, Qualifier],
    estimate: Decimal | None = None,
    uncertainty: Interval | StandardError | None = None,
) -> Node:
    value = AssessmentValue(
        spec=spec, run=local_id("run", run), proposition=proposition, outcome=outcome,
        interpretation_rule=interpretation_rule, estimand=estimand, applicability=applicability,
        estimate=estimate, uncertainty=uncertainty,
    )
    node_id = f"assessment:{slug}"
    facet: dict[str, Any] = {
        "spec": spec, "run": run, "proposition": proposition, "outcome": outcome,
        "interpretation_rule": interpretation_rule,
        "typed": v1.encode(value.typed_projection()).decode("utf-8"),
    }
    relations = [Relation(source=node_id, predicate=ASSESSES, target=proposition), Relation(source=node_id, predicate=PRODUCED_BY, target=run)]
    return _node("assessment", slug, title, {ASSESSMENT_FACET: facet}, relations)


_ASSESSMENT_FACET_KEYS = frozenset({"spec", "run", "proposition", "outcome", "interpretation_rule", "typed"})


@sealed
@final
@dataclass(frozen=True)
class AssessmentRef:
    """The three world-identity members of a stored assessment and nothing
    typed: what the successor-admission reader (`spec`, `identity()`) and the
    retraction target resolver (`identity()`) read. Malformed evidence still
    refuses — a missing facet or a non-string member is `MalformedRecord`."""

    spec: str
    run: str
    proposition: str

    def identity(self) -> str:
        return v1.digest(ASSESSMENT_DOMAIN, {"spec": self.spec, "run": self.run, "proposition": self.proposition})


def assessment_reference(node: Node) -> AssessmentRef:
    facet = _facet(node, ASSESSMENT_FACET)
    if facet is None:
        raise MalformedRecord(f"{node.id}: an assessment carries an {ASSESSMENT_FACET!r} facet")
    for member in ("spec", "run", "proposition"):
        if type(facet.get(member)) is not str or not facet[member]:
            raise MalformedRecord(f"{node.id}: assessment member {member!r} is a non-empty string")
    return AssessmentRef(spec=facet["spec"], run=local_id("run", facet["run"]), proposition=facet["proposition"])


def assessment_value(node: Node, *, profile: ProfileSpec) -> AssessmentValue:
    facet = _facet(node, ASSESSMENT_FACET)
    if facet is None:
        raise MalformedRecord(f"{node.id}: an assessment carries an {ASSESSMENT_FACET!r} facet")
    if "typed" not in facet and isinstance(facet.get("estimand"), str | type(None)):
        raise PreGrammarAssessment(
            f"{node.id}: pre-grammar assessment — minted before science.estimand.v1 with prose members. "
            "Refused, never coerced (estimand-typing decision 10)."
        )
    if set(facet) != _ASSESSMENT_FACET_KEYS or any(type(facet[k]) is not str for k in _ASSESSMENT_FACET_KEYS):
        raise MalformedRecord(f"{node.id}: an assessment facet is exactly {sorted(_ASSESSMENT_FACET_KEYS)}, every member text")
    try:
        typed = v1.decode(facet["typed"].encode("utf-8"))
    except CanonicalTextRefused as refused:
        raise MalformedRecord(f"{node.id}: the typed member is not canonical text: {refused}") from refused
    if not isinstance(typed, dict) or not {"estimand", "applicability"} <= set(typed) <= {"estimand", "applicability", "estimate", "uncertainty"}:
        raise MalformedRecord(f"{node.id}: the typed member carries estimand, applicability, and optionally estimate and uncertainty")
    try:
        estimand = estimand_from_stored(typed["estimand"], profile=profile)
        applicability = applicability_from_stored(typed["applicability"], profile=profile, operator=estimand.operator)
    except (DecodeError, EstimandError, ClaimError, ProfileError) as refused:
        raise MalformedRecord(f"{node.id}: the typed members do not restore: {refused}") from refused
    uncertainty = None
    if "uncertainty" in typed:
        body = typed["uncertainty"]
        if not isinstance(body, dict):
            raise MalformedRecord(f"{node.id}: uncertainty is a mapping")
        kind = body.get("kind")
        if kind == "interval" and set(body) == {"kind", "low", "high", "level"}:
            uncertainty = Interval(low=body["low"], high=body["high"], level=body["level"])
        elif kind == "standard-error" and set(body) == {"kind", "value"}:
            uncertainty = StandardError(value=body["value"])
        else:
            raise MalformedRecord(f"{node.id}: uncertainty kind {kind!r} is neither interval nor standard-error")
    return AssessmentValue(
        spec=facet["spec"], run=local_id("run", facet["run"]), proposition=facet["proposition"], outcome=facet["outcome"],
        interpretation_rule=facet["interpretation_rule"], estimand=estimand, applicability=applicability,
        estimate=typed.get("estimate"), uncertainty=uncertainty,
    )
```

(`AssessmentValue.__post_init__` refuses a non-`Decimal` `estimate` decoded from text and runs `check_estimate` and `check_uncertainty` against the estimand's scale, so the reader coerces nothing and admits no value the constructor would have refused. Add to `test_records.py`'s stored-reader coverage: a raw facet whose `typed` member carries `{"kind": "standard-error", "value": -0.1}` reads as `MalformedRecord`, never as a value.) Point `succession._typed` at `stored.assessment_reference(node)` — its return type becomes `dict[str, AssessmentRef]`, and `_recorded_failures`' reads of `target.identity()` and `target.spec` are unchanged — and `corpus.py:2946` at `stored.assessment_reference(target).identity()`; give `evaluation.py:221` `profile=profile`. Run `uv run --frozen pytest tests/test_successor_admission.py tests/acceptance/test_successor_admission_acceptance.py` and confirm the arm that admits a successor over an **active failed verification** still passes: it is the path that reads both members. Update `fixtures_cut3.interp` and `result_sensitive` to return `Decimal("0.4")` and `{"kind": "standard-error", "value": Decimal("0.1")}`.

- [ ] **Step 6: Run the tests**

Run: `uv run --frozen pytest tests/test_records.py tests/test_assess.py tests/test_audit.py tests/test_verification_publication.py tests/test_evaluation.py tests/test_belief.py tests/test_succession*.py tests/test_replay.py`
Expected: all pass; P5 and P6 (in `test_belief.py`) unchanged and green.

- [ ] **Step 7: Commit**

```bash
git add python/src/beliefs/record.py python/src/beliefs/assess.py python/src/beliefs/stored.py python/src/beliefs/succession.py python/src/beliefs/corpus.py python/src/beliefs/evaluation.py python/tests
git commit -m "feat(assess): type estimate and uncertainty on the spec's scale; strict stored assessment reader (Q5, Q7)"
```

---

### Task 8: The boundary and the audit — target match, pre-grammar codes

**Files:**
- Modify: `python/src/beliefs/corpus.py` (`_refuse`, new `_refuse_estimand_target_mismatch`)
- Modify: `python/src/beliefs/audit.py` (`check_spec_target`, `check_analysis_spec`, `stored_specs`, `audit_corpus`, the pre-grammar codes)
- Test: `python/tests/test_audit.py`, `python/tests/test_corpus_write.py`

**Interfaces:**
- Produces: `ValidationRefused("estimand-target-mismatch: …")`, `ValidationRefused("estimand-target-unresolvable: …")` at write and import; audit findings `spec-target-contradicted`, `spec-pre-grammar`, `assessment-pre-grammar`; `audit.check_spec_target(view, node, *, profile) -> DerivationOutcome`.

- [ ] **Step 1: Write the failing tests**

Append to `python/tests/test_corpus_write.py` (using its existing `writer` fixture over `profiles.BASE`-style profiles — this test needs the testing profile, so build a writer over `fixtures_cut3.TESTING_PROFILE` with the module's `_writer`/`corpora` helper and `pins_for(TESTING_PROFILE)`):

```python
class TestEstimandTargetMatch:
    def _proposition(self, writer, claim):
        from beliefs.projection import project_claim

        return writer.add(stored.proposition_node("p", title="p", claim=project_claim(claim)))

    def test_a_spec_answering_its_target_is_admitted(self, typed_writer):
        from fixtures_cut3 import TESTING_CLAIM, spec_draft, spec_rules

        target = self._proposition(typed_writer, TESTING_CLAIM)
        spec = freeze(spec_draft(target=target.id), held_rules=spec_rules())
        assert typed_writer.add(stored.analysis_spec_node(spec)).id == f"analysis-spec:{spec.identity}"

    def test_a_spec_built_against_another_claim_at_the_same_operator_is_refused(self, typed_writer):
        from fixtures_cut3 import TESTING_PROFILE, spec_draft, spec_rules
        from beliefs.claim import Referent, build_claim

        other = build_claim(TESTING_PROFILE, operator="testing/affects", args=(Referent("testing/entity", "EX:gene-z"), Referent("testing/outcome", "EX:pheno-y")), layer="causal", polarity="positive")
        target = self._proposition(typed_writer, other)
        spec = freeze(spec_draft(target=target.id), held_rules=spec_rules())  # estimand built against TESTING_CLAIM
        with pytest.raises(ValidationRefused, match="estimand-target-mismatch"):
            typed_writer.add(stored.analysis_spec_node(spec))

    def test_an_unresolvable_target_is_refused(self, typed_writer):
        from fixtures_cut3 import spec_draft, spec_rules

        spec = freeze(spec_draft(target="proposition:elsewhere"), held_rules=spec_rules())
        with pytest.raises(ValidationRefused, match="estimand-target-unresolvable"):
            typed_writer.add(stored.analysis_spec_node(spec))

    def test_the_inconsistent_stored_pair_is_caught_by_operator_equality(self, typed_writer):
        """Q6's stored-pair arm: the target's true claim hash beside another operator."""
        from fixtures_cut3 import TESTING_CLAIM, TESTING_PROFILE, UNCONSULTED, spec_draft, spec_rules
        from beliefs.claim import Referent, build_claim
        from beliefs.estimand import Control, LevelsContrast, Measure, build_estimand
        from beliefs.identity import v1
        from beliefs.projection import claim_identity
        from beliefs.spec import SPEC_DOMAIN, frozen_projection

        target = self._proposition(typed_writer, TESTING_CLAIM)
        correlates = build_claim(TESTING_PROFILE, operator="testing/correlates-with", args=(Referent("testing/entity", "EX:gene-x"), Referent("testing/outcome", "EX:pheno-y")), layer="statistical", polarity="positive")
        foreign, _ = build_estimand(
            TESTING_PROFILE, correlates, snapshot=UNCONSULTED,
            contrast=LevelsContrast(0, Referent("testing/level", "EX:a"), Referent("testing/level", "EX:b")),
            measure=Measure(Referent("testing/measure", "EX:tpm"), "additive"), reference=Decimal("0"),
            control=Control(Referent("testing/identification", "EX:observational"), ()),
        )  # note: correlates-with declares level_sorts {} — build with a continuous contrast instead if this refuses
        spec = freeze(spec_draft(target=target.id, estimand=foreign), held_rules=spec_rules())
        projection = frozen_projection(spec)
        projection["estimand"]["claim"] = claim_identity(TESTING_CLAIM)  # the target's true hash, another operator
        text = v1.encode(projection)
        identity = v1.digest(SPEC_DOMAIN, projection)
        node = stored._node("analysis-spec", identity, "forged", {stored.ANALYSIS_SPEC_FACET: {"identity": identity, "projection": text.decode()}}, ())
        with pytest.raises(ValidationRefused, match="estimand-target-mismatch.*operator"):
            typed_writer.add(node)
```

Append to `python/tests/test_audit.py`:

```python
def test_a_raw_written_mismatching_spec_is_caught_only_under_audit(writer):
    from fixtures_cut3 import TESTING_PROFILE, spec_draft, spec_rules

    target = writer.add(stored.proposition_node("p-other", title="other", claim=project_claim(OTHER_CLAIM)))
    spec = freeze(spec_draft(target=target.id), held_rules=spec_rules())
    node = stored.analysis_spec_node(spec)
    raw_write(writer.root, node)
    assert reopen(writer.root).get(node.id).id == node.id  # not refused on read
    findings = audit_corpus(reopen(writer.root), evidence=NO_EVIDENCE, profile=TESTING_PROFILE)
    assert [f.code for f in findings if f.ref == node.id] == ["spec-target-contradicted"]


def test_pre_grammar_records_audit_under_their_own_codes(writer):
    from fixtures_cut3 import TESTING_PROFILE

    spec_node = stored._node("analysis-spec", "old", "old", {stored.ANALYSIS_SPEC_FACET: {"identity": "old", "projection": v1.encode({"target": "proposition:p", "estimand": "prose", "method": "m", "assumptions": "a", "falsification": "f", "input_roles": [], "applicability": "prose", "interpretation_rule": "r", "equivalence_rule": "e", "parameters": {}, "nondeterminism": {"variant": "deterministic"}, "rule_bindings": []}).decode()}}, ())
    assessment_node = stored._node("assessment", "old", "old", {stored.ASSESSMENT_FACET: {"spec": "old", "run": "run:x", "proposition": "proposition:p", "outcome": "supported", "interpretation_rule": "r", "estimand": "prose"}}, ())
    raw_write(writer.root, stored.stamp_semantic_identity(spec_node))
    raw_write(writer.root, stored.stamp_semantic_identity(assessment_node))
    codes = {f.ref: f.code for f in audit_corpus(reopen(writer.root), evidence=NO_EVIDENCE, profile=TESTING_PROFILE)}
    assert codes[spec_node.id] == "spec-pre-grammar" and codes[assessment_node.id] == "assessment-pre-grammar"
    assert "derivation-malformed" not in codes.values()
```

(`OTHER_CLAIM` and `project_claim` defined at module top from `fixtures_cut3`/`beliefs.projection`; the `writer` fixture is rebuilt over `TESTING_PROFILE` for these two tests.)

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run --frozen pytest tests/test_corpus_write.py -k EstimandTargetMatch tests/test_audit.py -k "mismatching_spec or pre_grammar"`
Expected: the mismatching spec is admitted (no refusal), the raw-written spec audits clean, the pre-grammar records audit as `derivation-malformed`.

- [ ] **Step 3: The boundary**

In `python/src/beliefs/corpus.py`, inside `_refuse` after `self._refuse_r20_contradiction(node)`:

```python
        if node.kind == "analysis-spec":
            self._refuse_estimand_target_mismatch(node, view=self._view if view is None else view)
```

and the method:

```python
    def _refuse_estimand_target_mismatch(self, record: Node, *, view: ReadView | _ImportView) -> None:
        """Estimand-typing §7.2: the spec's estimand names the claim its target
        record carries — both the identity and the operator, since a stored
        estimand carries the two as independent members with no preimage."""
        from beliefs.decode import claim_from_stored
        from beliefs.projection import claim_identity
        from beliefs.resolution import build_snapshot

        spec = stored.analysis_spec_value(record, profile=self._profile)
        if not view.holds(spec.target):
            raise ValidationRefused(
                f"{record.id}: estimand-target-unresolvable: target {spec.target!r} does not resolve in this corpus; "
                "a cross-corpus target is world-resolution's read (estimand-typing §13)"
            )
        target = view.get(spec.target)
        if target.kind != "proposition":
            raise ValidationRefused(f"{record.id}: estimand-target-unresolvable: {spec.target!r} is not a proposition")
        # Identities only: the boundary consults no vocabulary, so every binding is not-consulted and nothing refuses here.
        claim, _receipt = claim_from_stored(target, profile=self._profile, snapshot=build_snapshot(readable={}))
        if spec.estimand.claim != claim_identity(claim):
            raise ValidationRefused(
                f"{record.id}: estimand-target-mismatch: the estimand answers claim {spec.estimand.claim[:12]}…, "
                f"the target record carries {claim_identity(claim)[:12]}…"
            )
        if spec.estimand.operator != claim.operator:
            raise ValidationRefused(
                f"{record.id}: estimand-target-mismatch: the estimand's operator {spec.estimand.operator!r} is not the "
                f"target's {claim.operator!r} — a stored pair with the true hash and another operator"
            )
```

- [ ] **Step 4: The audit**

In `python/src/beliefs/audit.py`:

```python
def check_spec_target(view: ReadView | _ImportView | WorldReadView, node: Node, *, profile: ProfileSpec) -> DerivationOutcome:
    """The boundary's estimand-target comparison, over a stored record (§7.2)."""
    from beliefs.decode import claim_from_stored
    from beliefs.projection import claim_identity
    from beliefs.resolution import build_snapshot

    spec = stored.analysis_spec_value(node, profile=profile)
    if not view.holds(spec.target):
        return _unchecked(f"{spec.target} does not resolve here")
    target = view.get(spec.target)
    if target.kind != "proposition":
        return _unchecked(f"{spec.target} is not a proposition")
    claim, _receipt = claim_from_stored(target, profile=profile, snapshot=build_snapshot(readable={}))
    disagreements = []
    if spec.estimand.claim != claim_identity(claim):
        disagreements.append("claim")
    if spec.estimand.operator != claim.operator:
        disagreements.append("operator")
    if not disagreements:
        return DerivationOutcome(checked=True, reason="", contradiction=None)
    return DerivationOutcome(
        checked=True, reason="",
        contradiction=Finding(severity="error", code="spec-target-contradicted", ref=node.id, detail=",".join(disagreements),
                              message=f"{node.id}: the spec's estimand does not answer the claim its target carries"),
    )


def check_analysis_spec(node: Node, *, profile: ProfileSpec) -> DerivationOutcome:
    stored.analysis_spec_value(node, profile=profile)
    return DerivationOutcome(checked=True, reason="", contradiction=None)
```

In `audit_corpus`'s loop, the `analysis-spec` branch becomes `outcome = check_spec_target(view, node, profile=profile)` (which restores first, so `check_analysis_spec`'s refusal is reached through it), and the `except RecordError` handler gains, **before** the generic finding:

```python
        except PreGrammarSpec as refused:
            findings.append(Finding(severity="error", code="spec-pre-grammar", ref=node.id, detail=str(refused), message=f"{node.id}: pre-grammar spec; the corpus was not recreated (decision 10)"))
            continue
        except PreGrammarAssessment as refused:
            findings.append(Finding(severity="error", code="assessment-pre-grammar", ref=node.id, detail=str(refused), message=f"{node.id}: pre-grammar assessment; the corpus was not recreated (decision 10)"))
            continue
```

`stored_specs` gets the same `PreGrammarSpec` branch with the `spec-pre-grammar` code. Import the two errors.

- [ ] **Step 5: Run the tests**

Run: `uv run --frozen pytest tests/test_corpus_write.py tests/test_audit.py tests/test_facet_seams.py tests/test_relocation*.py`
Expected: all pass, including the existing R22 negative (c) arm, which still sees a raw-written fabricated **assessment** caught only under audit.

- [ ] **Step 6: Commit**

```bash
git add python/src/beliefs/corpus.py python/src/beliefs/audit.py python/tests/test_corpus_write.py python/tests/test_audit.py
git commit -m "feat(boundary): require the spec's estimand to name its target's claim and operator; pre-grammar audit codes (Q6, Q10)"
```

---

### Task 9: The consulted walk reaches the estimand's contracts

**Files:**
- Modify: `python/src/beliefs/consulted.py:45-100`
- Modify: `python/src/beliefs/evaluation.py:307-314`, `python/src/beliefs/belief.py:255-262` (pass `estimands=`)
- Create: `python/tests/fixtures/measures-fixture.yaml` — namespace `measures`, `lineage: genesis`, one sort `assay` bound to `{namespace: EX, release: "2026-01-01"}`, no dimensions, no operators, no facets; a contract **no claim can reach**, since it declares no operator
- Test: `python/tests/test_consulted.py`, `python/tests/test_belief.py`

**Interfaces:**
- Produces: `consulted_contracts(..., estimands: Mapping[str, Estimand] = MappingProxyType({}))` keyed by assessment identity; a consulted set that includes the declaring contract of every estimand's `estimands:` entry and of each of its four sorts.

- [ ] **Step 1: Write the failing tests**

Append to `python/tests/test_consulted.py`:

```python
@pytest.fixture()
def measured(base_contract, testing_document):
    """`testing` whose `affects` estimand measures in `measures/assay`, compiled
    beside the `measures` fixture: a contract reached through the estimand and
    through nothing else, so the arm below cannot pass on the claim walk."""
    import copy
    from pathlib import Path

    from beliefs.contract.document import load_document

    fixture = Path(__file__).resolve().parent / "fixtures" / "measures-fixture.yaml"
    measures = domain.parse_domain_contract(load_document(fixture, source=str(fixture)), source=str(fixture), base=base_contract, predecessor=None)
    document = copy.deepcopy(testing_document)
    document["estimands"]["affects"]["measure_sort"] = "measures/assay"
    testing = domain.parse_domain_contract(document, source="<measured>", base=base_contract, predecessor=None)
    return compile_profile(base_contract, [testing, measures])


def test_an_estimand_reaches_a_contract_no_claim_reaches(measured, claim):
    from fixtures_cut3 import UNCONSULTED
    from beliefs.claim import Referent
    from beliefs.estimand import Control, LevelsContrast, Measure, build_estimand

    claim = build_claim(profile=measured, operator="testing/affects", args=claim.args, qualifiers={}, polarity="positive", layer="causal")
    estimand, _ = build_estimand(
        measured, claim, snapshot=UNCONSULTED,
        contrast=LevelsContrast(0, Referent("testing/level", "EX:a"), Referent("testing/level", "EX:b")),
        measure=Measure(Referent("measures/assay", "EX:m"), "additive"), reference=Decimal("0"),
        control=Control(Referent("testing/identification", "EX:obs"), ()),
    )
    pins = pins_for(measured)
    claim_only = consulted_contracts(claims={"p": claim}, profile=measured, node_corpus={}, pins={"c1": pins}, closure_nodes=())
    with_estimand = consulted_contracts(claims={"p": claim}, estimands={"a1": estimand}, profile=measured, node_corpus={}, pins={"c1": pins}, closure_nodes=())
    assert "measures" not in dict(claim_only) and dict(with_estimand)["measures"] == pins.domains["measures"]


def test_an_estimand_under_an_unpinned_namespace_refuses(profile, pins, claim):
    # A cross-contract measure sort pinned by no corpus is `ContractDisagreement`, as an operator's sort would be.
    ...  # build a profile whose testing contract's measure_sort is `biology/measure`, pin only `testing`, assert ContractDisagreement
```

Replace the `...` with the concrete construction: parse a `testing_document` copy whose `estimands.affects.measure_sort` is `biology/gene` alongside `profiles.biology("fixture")` compiled together, build the estimand, then call `consulted_contracts` with pins carrying `testing` but not `biology` and assert `ContractDisagreement` matching `'biology' is consulted but pinned by no corpus`.

In `python/tests/test_belief.py`, add the Q8 arm beside the existing D6 claim-schema arm, over the `measured` profile above: derive a belief over one assessment whose estimand's measure quantity binds `measures/assay`; recompile with the `measures` fixture's `description` changed (editorial: its content identity moves, no projection does) and re-pin it; assert `belief_input_digest` **moves**; then change the description of a third activated fixture contract that neither the claim nor the estimand reaches and assert the digest is **unchanged**. Because `measures` declares no operator, the claim walk cannot reach it, so deleting the estimand walk in `consulted_contracts` makes the first assertion fail — which is exactly the sabotage Task 11 declares for this arm, and the plan's own check that the arm is not vacuous.

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run --frozen pytest tests/test_consulted.py tests/test_belief.py -k "estimand"`
Expected: `TypeError: consulted_contracts() got an unexpected keyword argument 'estimands'`.

- [ ] **Step 3: Implement**

`python/src/beliefs/consulted.py`: add the parameter `estimands: Mapping[str, Estimand] = MappingProxyType({})` after `claims`, import `Estimand`, and after the claims loop:

```python
    # An assessment reaches its contract through the estimand's declaration and
    # its four sorts (estimand-typing §5.4, D6's third trigger). Keyed by
    # assessment identity so the walk is over what the derivation read.
    for estimand in estimands.values():
        declaration = profile.estimand(estimand.operator)
        read.add(declaration.contract)
        for sort in (declaration.measure_sort, declaration.identification_sort, declaration.conditioning_sort, *declaration.level_sorts.values()):
            read.add(profile.sorts[sort].contract)
```

`evaluation.py`: pass `estimands={a.identity(): a.estimand for a in matched}`; `belief.py`: the same over `matched`.

- [ ] **Step 4: Run, then commit**

Run: `uv run --frozen pytest tests/test_consulted.py tests/test_belief.py tests/test_evaluation.py tests/test_world_view*.py`
Expected: all pass.

```bash
git add python/src/beliefs/consulted.py python/src/beliefs/evaluation.py python/src/beliefs/belief.py python/tests/test_consulted.py python/tests/test_belief.py
git commit -m "feat(consulted): reach an estimand's contracts in the consulted walk (Q8)"
```

---

### Task 10: The reproduction — successor `mm30` contract, held lists, recreated corpus, fresh-process restore

**Files:**
- Modify: `python/tools/reproduction/mm30.yaml` (three sorts, `estimands:`, `lineage: {successor: <cut-22 identity>}`)
- Create: `python/tools/reproduction/lists.py` (step 1c: hold the three term lists)
- Modify: `python/tools/reproduction/vocabulary.py` (`{{LEVELS}}`, `{{MEASURES}}`, `{{IDENTIFICATIONS}}` tokens; `snapshot()` reads four bindings), `spec.py` (`draft()` typed), `run.py:110-125` (typed `assessment_node`), `rederive.py` (`profile=`; the fresh-process restore of spec and assessment), `close.py` (`evidence_for(view, profile)`), `state.py` (new keys)
- Modify: `docs/designs/2026-09-05-mm30-reproduction.md` (a dated addendum, §10)
- Test: `python/tests/test_reproduction_driver.py`

**Interfaces:**
- Consumes: everything above.
- Produces: `lists.hold_list(name, terms) -> (address, ref)`; `spec.draft()` returning a typed `SpecDraft`; the recreated corpus at `.work/reproduction/mm30/` under the successor contracts; `state.json` keys `levels_address`, `measures_address`, `identifications_address`, `spec_prose_identity` (the cut-22 spec's `86aaa1a8…`, cited as text).

- [ ] **Step 1: The successor contract**

In `python/tools/reproduction/mm30.yaml`, under `contract:` set `lineage: {successor: "<the cut-22 mm30 content identity, read from the prior corpus's manifest pin>"}` — read it with `uv run --frozen python -c "from reproduction import vocabulary; print(vocabulary.contract().content_identity)"` **before** editing, and paste the value; add sorts

```yaml
    stage-level: {vocabulary: "dataset:{{LEVELS}}"}
    measure: {vocabulary: "dataset:{{MEASURES}}"}
    identification: {vocabulary: "dataset:{{IDENTIFICATIONS}}"}
```

and

```yaml
  estimands:
    affects-concept-molecular-entity:
      level_sorts: { "0": stage-level }
      measure_sort: measure
      identification_sort: identification
      conditioning_sort: concept
```

The predecessor contract must be supplied to `parse_domain_contract`: `vocabulary.contract()` gains `predecessor=` loaded from `python/tools/reproduction/mm30-cut22.yaml`, a byte copy of the cut-22 document committed beside it (with its `{{CONCEPTS}}` token resolved from `state.json`), so `check_succession` runs against the real predecessor and Q2's "adding a declaration is accepted" arm is exercised on the corpus that matters.

- [ ] **Step 2: Hold the three lists**

Create `python/tools/reproduction/lists.py` on the pattern of `concepts.py`, in **two entry points**, because `world.adopt()` compiles the contract and the contract binds every list's address: `LISTS = {"levels": ("mm30-stage-levels.txt", ["level:ndmm", "level:pd"]), "measures": ("mm30-measures.txt", ["measure:rna-seq-tpm"]), "identifications": ("mm30-identifications.txt", ["identification:interventional", "identification:longitudinal", "identification:observational", "identification:structural"])}`. `prepare()` writes each list sorted, one canonical identifier per line, newline-terminated, to `paths.WORK`, computes its digest and dataset address as `concepts.py` does, and saves `<name>_address` and `<name>_file` to `state.json` — **before** anything adopts. `concepts.main()` is split the same way: its address computation and `state.save(concepts_address=…)` move ahead of `world.adopt()`, which now compiles with all four addresses present. `mint()` then holds each list's bytes through `holdings.boundary.write` and mints its dataset record with `stored.dataset_node`, saving `<name>_ref`. `vocabulary._document` replaces the three tokens as it replaces `{{CONCEPTS}}` and refuses when any address is absent. `snapshot()` builds one snapshot over all four bindings: `build_snapshot(readable={concept_binding: concepts, level_binding: levels, measure_binding: measures, identification_binding: identifications})`.

- [ ] **Step 3: The typed draft**

In `python/tools/reproduction/spec.py`, `draft()` becomes:

```python
def draft() -> SpecDraft:
    from beliefs.claim import Referent
    from beliefs.estimand import Control, LevelsContrast, Measure, build_applicability, build_estimand
    from reproduction import type_target, vocabulary

    st = state.load()
    target = yaml.safe_load(paths.TARGET.read_text())
    profile, plan = vocabulary.profile(), vocabulary.plan()
    claim = type_target.typed(target, profile, plan)
    snapshot = vocabulary.snapshot()
    estimand, _ = build_estimand(
        profile, claim, snapshot=snapshot,
        contrast=LevelsContrast(slot=0, baseline=Referent("mm30/stage-level", "level:ndmm"), comparison=Referent("mm30/stage-level", f"level:{target['positive_level'].lower()}")),
        measure=Measure(quantity=Referent("mm30/measure", "measure:rna-seq-tpm"), scale="additive"),
        reference=Decimal("0"),
        control=Control(identification=Referent("mm30/identification", "identification:observational"), conditioning=()),
    )
    applicability, _ = build_applicability(profile, claim, {}, snapshot=snapshot)
    return SpecDraft(
        target=st["proposition_ref"],
        estimand=estimand,
        method=(
            "two-group rank comparison (Mann-Whitney U, normal approximation), standard library; "
            "a sample whose value is not finite is malformed input and the run refuses (assoc.py's own rule)"
        ),
        assumptions="independent samples; the stage is a two-level factor carried by each sample id",
        falsification="no difference at alpha 0.05, or a difference opposite the proposition's polarity",
        input_roles=(SpecInput(role="observes", dataset=st["dataset_address"]),),
        applicability=applicability,
        interpretation_rule=INTERPRETATION_RULE,
        equivalence_rule=EQUIVALENCE_RULE,
        parameters={"alpha": Decimal("0.05")},
        nondeterminism=Deterministic(),
    )
```

The prose applicability's second clause is **refused** at retyping per spec §4 and moves into `method`, as shown; the driver records the relocation with `findings.record(4, "corpus-work", "prose applicability clause 'whose ids carry a stage token and whose value is finite' refused at retyping (no declared dimension); re-authored in `method` as estimator behaviour — the estimator refuses a non-finite value as malformed input, it does not exclude the sample — an authored judgment (design §4, §9)")`. Changing `assoc.py` to exclude instead would be a separate behavioural change and is not made. `run.py` step 6 passes `estimand=derived.estimand, applicability=derived.applicability, estimate=derived.estimate, uncertainty=derived.uncertainty` to `stored.assessment_node`.

- [ ] **Step 4: Recreate, re-run, restore in a fresh process**

Move the prior corpus aside (`mv .work/reproduction/mm30 .work/reproduction/mm30.cut22` — it is the prior corpus state Q10's transition arm reads) and run the driver's steps in order: `world`, `select_target`, `lists prepare` (addresses only), `concepts` (addresses, then adoption, then the held list and record), `lists mint`, `type_target`, `hold`, `spec`, `run`, `belief` (publishes the verification and saves the baseline `rederive` reads), then `rederive` and `close`. The order is written into `docs/superpowers/specs/2026-09-05-mm30-reproduction-design.md`'s step table as a dated amendment, since `lists` is a new step and `belief` was implicit. `rederive.py` gains, in its fresh process: `stored.analysis_spec_value(view.get(st["spec_ref"]), profile=profile())` and `stored.assessment_value(view.get(st["assessment_ref"]), profile=profile())`, re-derives the assessment through `build_assessment` and the belief through `belief.evaluate_here`, and writes `spec_restored`, `assessment_restored`, `belief_equal` into its report. It then opens the **prior** corpus at `mm30.cut22` read-only (`ReadView.opened_at`) and records, under the successor profile: `analysis_spec_value` raises `PreGrammarSpec`, `assessment_value` raises `PreGrammarAssessment`, and `audit_corpus` returns exactly one finding, `profile-mismatch` with detail `base`, and reads no record — the prior corpus pins the cut-22 base contract, which predates the grammar and does not parse under the successor, so the existing profile-disagreement rule fires first and is preserved. The two pre-grammar audit codes are Task 8's, exercised on a corpus **pinned to the successor** that holds a raw-written pre-grammar record; the addendum cites that test by name rather than claiming the prior corpus reaches them. Q10's transition arm, measured.

- [ ] **Step 5: The addendum**

Append `## 10. Addendum — estimand typing, <date>` to `docs/designs/2026-09-05-mm30-reproduction.md`: the three held lists (digests, counts), the typed estimand as spelled, the refused clause and its relocation **as a judgment**, the prose spec's identity `86aaa1a8…` cited as text with no successor edge, the new spec identity, the belief value (equal) and digest (different), the consulted set (`{science, mm30, biology}`), the fresh-process restoration results, and the pre-grammar refusals over the prior corpus. Add a unit test in `test_reproduction_driver.py` that `lists.hold_list` writes sorted, newline-terminated canonical identifiers and refuses a non-canonical one.

- [ ] **Step 6: Commit**

```bash
git add python/tools/reproduction docs/designs/2026-09-05-mm30-reproduction.md python/tests/test_reproduction_driver.py
git commit -m "feat(reproduction): recreate the mm30 corpus under the successor contract with a typed spec (Q10)"
```

---

### Task 11: Acceptance, the N2 declaration, the cut, the guard and the runner

**Files:**
- Create: `python/tests/acceptance/test_estimand_acceptance.py`, `python/tests/n2_arms_cut<N>.py`, `python/tests/acceptance/n2_arms_cut<N>.py` (re-export shim), `python/tests/acceptance/test_n2_cut<N>.py`, `python/tools/cut<N>_acceptance.py`, `docs/designs/<date>-conformance-cut-<N>.md`
- Modify: `python/tests/test_designs_corpus.py` (`GUARANTEE_TABLES["Q"]`, `TABLE_OWNERS["Q"]`), the designs README row total

- [ ] **Step 1: The frozen cut is Task 0's**

The cut document, the `Q` table registration and the freeze commit already exist (Task 0). Nothing in the frozen document is edited; a correction found while writing the arms is a dated supplement in the cut document's §8, on cut 25's precedent.

- [ ] **Step 2: The acceptance module**

`python/tests/acceptance/test_estimand_acceptance.py`: one test per Q row, each named `test_q<n>_<slug>`, composed from the unit tests' constructions over a registered durable corpus (the `corpora` fixture pattern of `test_facet_acceptance.py`), and for Q10 reading the addendum's recorded values and asserting the driver's `rederive` report keys (`spec_restored`, `assessment_restored`, `belief_equal`, `prior_pre_grammar`) are all `True`.

- [ ] **Step 3: The declaration file**

`python/tests/n2_arms_cut<N>.py`, one `Arm` per sabotage in spec §10.3, `before` blocks copied verbatim from the tree at freeze, each `checks=` naming the acceptance test it must fail. The twenty-one arms, by mechanism: drop the closed-set membership check (`estimand.py`, `if measure.scale not in grammar.scales`); admit an unknown grammar key (`base.py`, `_exact_fields(estimand, …)`); skip the operator-declared check (`domain.py`, `if name not in operators`); skip the `Fin(arity)` check (`domain.py`); skip the level-sort presence check (`estimand.py`, `if level_sort is None`); admit `not-member` (`estimand.py`, `_resolve_all`'s `refused`); skip duplicate conditioning (`estimand.py`, `Control.__post_init__`); admit a float reference (`estimand.py`, `_finite`'s `type(value) is not Decimal`); drop the sign check under `multiplicative` (`estimand.py`); drop the dimension check in `build_applicability` (route around `Claim._checked`); admit a string estimate (`assess.py`, `check_estimate`); drop `low ≤ estimate ≤ high` (`estimand.py`, `check_uncertainty`); drop the extra-key refusal on rule output (`assess.py`, `extra`); drop the operator equality from `_refuse_estimand_target_mismatch`; drop the claim-identity equality from it; drop `check_spec_target` from the audit loop; drop the estimand walk in `consulted_contracts`; put `identification` into the commensuration key (`commensuration_key`, the `del`); drop `claim` from the projection; drop `increment` from the projection; admit an increment of `0` (`ContinuousContrast.__post_init__`); take `claim` from the wire instead of the `Claim` (`build_estimand`); drop `estimand:` entries from `_declarations()`; drop the `estimand_grammar` member from the spec projection; coerce a string estimand in `restore`; report a pre-grammar spec as `derivation-malformed`.

- [ ] **Step 4: The guard and the runner**

`python/tests/acceptance/test_n2_cut<N>.py` on `test_n2_cut26.py`'s shape: `FROZEN_CUT`, `CUT<N>_FREEZE_COMMIT`, `CUT<N>_FROZEN_SHA256`, `CUT<N>_DECLARATION_SHA256`, `FROZEN_PRIOR_CUT_FILES` extended with cut 26's declaration and its commit, `PRIOR_ARMS` extended with `CUT26_ARMS`, the accounting test (arms, units, rows), the freeze pins, and the audit over every arm with the staleness baseline taken from the tree. `python/tools/cut<N>_acceptance.py` on `cut26_acceptance.py`'s shape with `PREFIX_RUNNERS = ("cut26_acceptance.py",)` — or the highest-numbered discharged runner at freeze — and `PHASE_MODULES = ("test_estimand_acceptance.py", "test_n2_cut<N>.py")`.

- [ ] **Step 5: Freeze, discharge, commit**

Freeze by dated commit after review clears (`docs(cut): freeze conformance cut <N>`), pin the commit and hashes in the guard, then discharge on the certified volume: `uv run --frozen python tools/cut<N>_acceptance.py`, then `just hook-pre-push`. Record both summary lines.

---

### Task 12: Amendments, the results record, the ledger and the roadmap

**Files:**
- Modify: `docs/designs/2026-08-02-epistemic-kernel-design.md` §4.2.1 (the facet table's four rows now typed; limitation 5 amended to name the structural match and the surviving semantic residue); `docs/designs/2026-08-02-computation-reproducibility-design.md` §3.1 (the `estimand` and `applicability` rows), §3.1b (the rule's output types), §5.1 (the constructor copies typed members); `docs/designs/2026-08-04-formal-model-and-claim-calculus-design.md` §7.1 (the `estimands:` declaration class; D6's third trigger), §11 (ρO3's estimand half answered, the entailment half unchanged); `docs/designs/2026-08-05-belief-policy-design.md` §3.2 and §5 (the blocker named is now supplied; v1 still reads none of it), §9 questions 2 and 3; `docs/designs/2026-08-05-review-disposition-and-conformance-cut-1.md` §8 question 4; `docs/designs/2026-09-05-facet-contracts-design.md` §3.2 (the `assessment` and `analysis-spec` reader rows: strict, `profile`-taking); `docs/designs/2026-08-04-domain-extension-boundary-design.md` D6 row (the estimand-schema arm); `docs/guide/claims-and-belief.md`, `docs/guide/computation-and-reproducibility.md`, `docs/guide/glossary.md` (Estimand, Applicability, Estimate, Uncertainty, Commensurable, Co-scoped, Pre-grammar record); `docs/guide/open-questions.md` (Entailment and estimand match: the estimand half closed by citation, the entailment half open; Weighted belief: blocked on the successor-policy design over the commensuration and scope keys); `docs/designs/2026-08-03-redesign-adoption-ledger.md` `Current state` (a new `estimand-typing` row, then its closure at discharge); `docs/plans/2026-08-29-implementation-roadmap.md` (boundary index, tier 1 off the path, lane table, Appendix A/B); `docs/plans/<date>-conformance-cut-<N>-results.md`
- Every amendment is a dated block in place, never an edit of frozen prose; each names this design by path.

- [ ] **Step 1: Results record**

On cut 26's results shape: what ran (both summary lines, the arms' verdicts, the baseline), accounting and disposition (Q1–Q10 closed; the global row total moves from 195 to 205 and the closed count by 10), corrections and deviations from the frozen cut, remaining boundary (none for Q; `weighted-belief` re-blocked).

- [ ] **Step 2: Ledger and roadmap**

Add the `estimand-typing` row to the ledger table and the roadmap's boundary index, tier 1 off the path, lane `estimand-typing`, then mark it closed in the same results commit; rewrite the roadmap whole (it carries no dated corrections); `weighted-belief`'s *blocked on* becomes "the successor belief-policy design over `commensurable` and `co_scoped` (`beliefs-638318`)"; `contract-cut` (`beliefs-eacbe2`) gains `beliefs-59f846` as a dependency via `tasks dep`. Run `uv run --frozen pytest tests/test_designs_corpus.py tests/test_check_guide.py` and `uv run --frozen python tools/roadmap_status.py` green.

- [ ] **Step 3: Tasks and commit**

`tasks done` each step child as its commit lands; `tasks done beliefs-59f846 "<what landed>"` in the results commit; `tasks check` clean.

```bash
git add docs python/tests/test_designs_corpus.py
git commit -m "docs(cut): discharge conformance cut <N>; close estimand-typing and amend the banked designs"
```

---

## Self-review

**Spec coverage.** §11's lane admission and the freeze-before-code rule → Task 0; §3.1 grammar → Task 1; §3.2 type and projection → Tasks 4, 5; §3.3 fragment refusals → Task 4 (`**richer`, the per-member refusals); §4 applicability and the relocation rule → Tasks 4, 5, 10; §5.1–5.3 declaration, compile, succession → Tasks 2, 3; §5.4 consulted walk → Task 9; §6 estimate and uncertainty meanings and checks → Tasks 4, 7; §7.1 construction → Task 4; §7.2 boundary, decode, `restore(profile)`, pre-grammar → Tasks 5, 6, 8; §7.3 `commensurable`, `co_scoped` → Task 4; §8 Q1–Q10 → Tasks 1–10 unit, Task 11 acceptance; §9 identity and the reproduction → Tasks 6, 7, 10; §10 testing and the cut → Task 11; §11 roadmap → Task 12; §12/§13 nothing to build; decision 10's transition → Tasks 6, 7, 8, 10.

**Placeholder scan.** `<N>` and `<date>` are claimed at freeze by concurrency rule 1 and are not placeholders. Task 9's second consulted test and Task 11's acceptance module are described by construction rather than pasted because they compose the unit tests' code verbatim; the arms list names every sabotage site. Task 7's `run_assessment_under` names the helper to add if absent, with its construction.

**Type consistency.** `build_estimand(profile, claim, *, contrast, measure, reference, control, snapshot)` (Task 4) is what Tasks 6, 7, 8, 9, 10 call; `estimand_from_stored(projection, *, profile)` and `applicability_from_stored(projection, *, profile, operator)` (Task 5) are what `restore` (Task 6) and `assessment_value` (Task 7) call; `restore(identity, projection, *, profile)` and `analysis_spec_value(node, *, profile)` (Task 6) are what Tasks 8 and 10 call; `assessment_reference(node) -> AssessmentRef` (Task 7) is what `succession._typed` and `corpus.py:2946` call, and `AssessmentRef` keeps `spec` and `identity()` for `_recorded_failures`; `consulted_contracts(..., estimands=)` (Task 9) is what `evaluation.py` and `belief.py` call; `PreGrammarSpec` / `PreGrammarAssessment` (Task 6) are what Task 8's audit branches and Task 10's transition arm catch.
