# Biology Pack (domain-boundary slice 2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the first packaged domain contract (`biology`), a corpus-local `mm30` contract that names the pack's sort across contracts, the consulted walk's sort-contract and pin-agreement rules, and the first derivation-side read of a domain facet — then freeze, implement and discharge conformance cut 22 and re-run the mm30 reproduction as the measurement.

**Architecture:** Three kernel changes, each behind its own tests: (1) a sort reference may be `<namespace>/<sort>`, deferred at parse and resolved at compile; (2) `consulted_contracts` reaches every claim's sort contracts and refuses a consulted namespace whose pin disagrees with the profile; (3) `gather` reads declared domain facets off held observed datasets into reader-minted `FacetRead` rows that feed both the consulted walk and a new closure member. Around them: the pack document and its packaged copy, the TypeScript mirror of the parse and compile refusals, the reproduction driver's corpus-local contract and held concept vocabulary, and the cut-22 guard, runner and records.

**Tech Stack:** Python 3.11 (`uv run --frozen`, pytest, ruff, pyright), TypeScript (vitest, biome), YAML contracts, the `tasks` CLI, git.

**Spec:** `docs/designs/2026-09-08-biology-pack-design.md` — every section reference below (§n) is to that document unless prefixed D (domain extension boundary design), F (facet contracts design), M (formal model design) or P (belief policy design).

## Global Constraints

- Work on the lane worktree `.worktrees/domain-boundary`, branch `feat/domain-boundary-slice2`. Run Python commands from `python/` with `uv run --frozen`; the system interpreter lacks `beliefs`.
- Conventional commits; no AI-attribution trailer or footer.
- The pre-commit hook runs `ops-check`, `ruff check`, `pyright`, `tsc --noEmit`, `biome check` and `tasks check`; a commit that fails any of them is not a commit.
- Every refusal message is prefix-stable: the text before the first `:` is what tests match on.
- Sabotage sites in Task 11's arm table must match the source lines written in Tasks 2–9 **byte for byte**; when a task's code changes a line the table cites, the table is the thing that moves ("fix the arm, never the source").
- Frozen guard modules (`tests/acceptance/test_n2_cut*.py`, the `n2_arms_cut*.py` tables cut 21's `FROZEN_PRIOR_CUT_FILES` pins) are never edited. `n2_arms_cut2.py` is **live and unpinned** (nothing in `FROZEN_PRIOR_CUT_FILES` names it), so its D6 arm is re-pointed at the landed source in Task 4, with a dated amendment to the cut-2 document.
- The shipped pack file is `domains/biology/DOMAIN.yaml`, the name D §11 limitation 5 and `fixtures/contracts/testing.yaml` already use; Task 1 corrects the design's `CONTRACT.yaml` spelling.
- The HGNC release string is `"2026-07-01"`: the most recent HGNC quarterly archive date (the first of January, April, July, October) on or before the design date 2026-09-08 (§3.2). It is unconsulted in this slice; no bytes depend on it.
- Task identifiers: parent `beliefs-1ce152`; this plan's children are created in Task 1 step 6.

---

### Task 1: Correct the design's two details, freeze cut 22, attach the plan

**Files:**
- Modify: `docs/designs/2026-09-08-biology-pack-design.md` (§5.3a, §6.1, §10)
- Create: `docs/designs/2026-09-08-conformance-cut-22.md`
- Modify: `tasks/beliefs-1ce152.md` via the `tasks` CLI only

**Interfaces:**
- Produces: the frozen cut document whose §§2–7 Task 11's guard pins by commit and digest; `CUT22_FREEZE_COMMIT` is the short SHA of step 5's commit.

- [ ] **Step 1: Correct the pack file name in the design**

In `docs/designs/2026-09-08-biology-pack-design.md` replace every `CONTRACT.yaml` that refers to the biology pack (§6.1: the normative path and the packaged path; §7 row B6; decision 8) with `DOMAIN.yaml`, and add to §6.1 after "The normative file is `domains/biology/DOMAIN.yaml` at the repository root":

```markdown
The file name is `DOMAIN.yaml`, not the base's `CONTRACT.yaml`: D §11
limitation 5 and `fixtures/contracts/testing.yaml` both name
`domains/biology/DOMAIN.yaml` as the design act this slice performs, and a
domain document is not a base contract.
```

The base contract's own `contracts/science/CONTRACT.yaml` mentions stay as they are.

- [ ] **Step 2: Correct the cut-2 standing in §5.3a and §10**

Replace the last paragraph of §5.3a with:

```markdown
The consequence for existing evidence is stated in §10: tests that pin a
synthetic identity such as `sci-1` under a real profile no longer describe
a well-formed derivation and are rewritten to derive pins from the profile.
Cut 2's guard is **live** — `test_n2.py` audits `n2_arms_cut2.py` in the
portable suite and no later cut pins that table by commit — so its D6 arm
whose sabotage site this slice edits is re-pointed at the landed source
under the frozen-guard doctrine's "fix the arm, never the source", and the
cut-2 document takes a dated citation amendment. Nothing frozen is edited.
```

Replace the "Existing evidence under §5.3a" bullet in §10 with:

```markdown
- **Existing evidence under §5.3a and §4.4.** `test_consulted.py`,
  `test_closure.py`, `test_belief.py`, `test_evaluation.py` and
  `verification_fixtures.py` build `CorpusPins` with strings such as
  `sci-1` and `testing-1` under a real profile; every one is rewritten to
  `profiles.pins_for(<the profile in use>)`, and the two cut-2 D6 checks
  that bump a pin string alone (`test_the_base_contract_arm_at_the_eligibility_hinge`,
  `test_an_activated_but_unconsulted_bump_is_absent`) bump a **compiled
  profile** instead, keeping their names and their assertions. The cut-2
  D6 arm whose sabotage `before` text names the walk's three lines is
  re-pointed at the landed lines in `n2_arms_cut2.py`, which is live and
  unpinned; `2026-08-09-conformance-cut-2.md` gains a dated amendment
  naming the commit. No frozen guard is edited.
```

- [ ] **Step 3: Write the cut-22 freeze document**

Create `docs/designs/2026-09-08-conformance-cut-22.md`:

```markdown
# Conformance cut 22 — the biology pack, the cross-contract slot, the domain-facet read

**Frozen:** 2026-09-08, before implementation, on `feat/domain-boundary-slice2`.
**Design:** `2026-09-08-biology-pack-design.md`, reviewed 2026-09-08 (three findings, all in the design's status header).
**Numbered after** cut 21 (concurrency rule 1) and **serialized after** cut 21's discharge, which landed on `main` at `03471da` on 2026-09-08 (rule 5).

## 1. What this cut is

Cut 22 is the frozen acceptance boundary for the `domain` lane's second
slice: a sort reference that crosses contracts, resolved at compile or
refused with the missing namespace named; the consulted walk reaching every
claim's sort and dimension contracts and refusing a consulted namespace
whose pin disagrees with the validating profile; the first derivation-side
domain-facet read, minted by the reader, validated, ledgered and digested,
never weighed; and the first packaged domain contract. The selection was
frozen after the design's written review cleared.

The selection rule is cut 5's: a clause is selected only when its source
mutation and every named check run entirely inside §2. A row with any unrun
arm is partial. The `B` table is new, so every B row is selected in full.

## 2. The boundary

In scope:

- `contract/domain.py`: `_sort_reference` and the two parse-time refusals
  (own namespace, base namespace); `OperatorDecl.arg_sorts` and
  `DimensionDecl.restriction_sort` carrying a reference as written;
- `profile.py`: the two-pass compile, `_resolve_sort`, the unresolved-
  reference refusal, `shipped_domain_contract`;
- `consulted.py`: the sort- and dimension-contract collection, the
  `science` and per-namespace pin agreement, `facets_read` derived from
  `FacetRead` rows over closure nodes that include observed addresses;
- `facet_read.py`: `FacetRead`, its minting classmethod, `read_observed_facets`
  over a `ReadView` and a target ref;
- `belief.py`: `Records.observed_facets`, the closure-node widening, the
  `ContractMismatch` → `Refused("profile-pin-mismatch")` mapping;
- `evaluation.py`: `gather`'s observed-dataset read, `EvaluationInputs.observed_facets`,
  `evaluate_over`'s mapping of `ContractMismatch`, `FacetPayloadRefused`
  and `FacetUndeclared` to `Refused`;
- `closure.py`: the `observed_facets` member, always present;
- `stored.dataset_node`'s `domain_facets` parameter;
- `domains/biology/DOMAIN.yaml` and its packaged copy;
- `ts/src/contract.ts` and `ts/src/profile.ts`: the same two forms and three refusals;
- the reproduction driver's steps 1b, 2, 3 and 8 over a fresh work directory.

Out of scope:

- the GO, HP, EFO and MONDO bindings (design §9 item 1);
- a kernel-side vocabulary dataset reader (§12);
- any verdict effect of a domain payload (P §open question 4);
- D1's `nodes` negative (cross-repository; deferred with its reason);
- distribution beyond the package (D §12);
- unresolved `observes` addresses (`world-resolution`; §9 item 10).

## 3. Selection

### B1 — closes

A slot sort resolves or refuses, at the right stage. Selected: a bare name
undeclared → refused at parse; `mm30/concept` inside `mm30` → refused at
parse; `science/x` → refused at parse; `testing/entity` compiled with
`testing` → resolves to that term; compiled without it → refused at compile
naming `testing`; `restriction_sort` takes both forms identically.
**Deferred:** none.

### B2 — closes

The consulted walk reaches every sort's contract, and facet namespaces are
collected on their own. Selected: a claim at `crossing/affects-local-entity`,
whose only route to `testing` is slot 1's argument sort (the operator
declares no dimension), consults `{science, crossing, testing}`; a
same-contract operator's set is unchanged from cut 2; a corpus pinning the
operator's contract only → `ContractDisagreement` naming the sort's
namespace; the isolated case consults `biology` through the ledger alone.
**Deferred:** none.

### B3 — closes

`FacetRead` is minted by the corpus reader only, over a dataset it fetched
from a corpus view, with the address derived from that dataset's own
declaration. Selected: no public field-wise constructor; the reader refuses
anything but a `ReadView`; there is no route that takes an in-memory node or
a caller-supplied address. **Deferred:** none.

### B4 — closes

Every read is validated, and only held datasets are read. Selected: a
declared facet failing its schema → `Refused("facet-payload-refused…")`; an
undeclared namespaced key → `Refused("facet-undeclared…")`; through `gather`
with an observed dataset node absent from the view → no run input, no
`FacetRead`, no `observes` entry, nothing refuses. **Deferred:** none.

### B5 — closes

Observed facets enter the digest through the one carrier. Selected: payload
byte change, every other member fixed → digest moves; the member is present
and empty when nothing was read; the rows the closure digests are the rows
the walk consumed. **Deferred:** none.

### B6 — closes

The pack ships byte-identical, and TypeScript refuses what Python refuses.
Selected: packaged copy equals `domains/biology/DOMAIN.yaml`; the pack
compiles with the shipped base and declares the floor; the TypeScript
parser refuses own-namespace and `science` references and an unresolved
reference at compile (vitest, run by the acceptance module).
**Deferred:** none.

### B7 — closes

A consulted namespace's pin agrees with the profile. Selected: pins built
from the profile → the walk proceeds; `science` pinned to another identity →
`Refused("profile-pin-mismatch: science")`; a consulted domain pinned to
another revision → refused naming it; an unconsulted domain pinned to
anything → not compared; `evaluate_over` refuses before `evaluate` runs.
**Deferred:** none.

### D6 — closes

The facet arm and the negative's domain-facet instantiation, on the design's
two cases (§5.6): the isolated case (a claim at `testing/affects` over a run
observing a held dataset carrying `biology/gene-axis`; a biology bump moves
the digest, an unrelated activated domain's bump does not, with payload and
assessment bytes fixed) and the dogfood shape (a claim whose slot sort is
biology's, reaching `biology` by both routes), the latter also durable
through `CorpusWriter.add` on the certified tuple. Cut 2's claim-schema,
base-contract, unconditional and negative arms stand and are cited.
**Deferred:** none.

### M8 — arm added, closes

Over a claim at `crossing/affects-local-entity` with no domain facet in the
closure, an editorial `testing` bump leaves `I_claim` unchanged and moves
`belief_input_digest` — reached through slot 1's foreign sort and nothing
else, so dropping the walk's sort-contract collection fails the check.
**Deferred:** none.

### M6 — re-read, not counted

A successor rewriting a namespaced slot is a changed `arg_sorts` and is
refused; the existing succession tests run unchanged plus one over a
namespaced slot. Cited, not counted.

### D1 — part, unchanged

Cut 20's selection stands; the "add a `nodes` code path" negative is
deferred again: it runs in another repository's suite.

### Boundary invariants

No verdict changes. No claim identity changes for a same-contract claim. No
contract identity changes for a document that names no foreign sort.

## 4. Accounting

Nine guarantee rows are read, **9 full/closed** (B1–B7, D6, M8), 1 partial
(D1, unchanged), 1 re-read not counted (M6). The N2 inventory therefore has
**9 declaration units**, one grouped unit per closed row. A grouped unit may
expand into lettered sabotage arms, but it is counted once here and may not
be silently split or merged after the freeze.

## 5. N2 and acceptance obligations

1. The declaration inventory names exactly the 9 frozen units in §4, each
   single-homed to the test that exercises it. Lettered sabotage arms
   normalize back to those units.
2. Every selected behavior marked durable in §3 runs through the certified
   engine on the certified kernel and volume tuple, on the volume beside
   the checkout; its portable arms run beside it. Capability refusal is an
   error, never a skip or waiver.
3. The aggregate runner `tools/cut22_acceptance.py` names
   `cut21_acceptance.py` as its prefix (`PREFIX_RUNNERS =
   ("cut21_acceptance.py",)`), then runs the biology acceptance module and
   the cut-22 N2 audit.
4. `acceptance/n2_arms_cut22.py` declares the sabotage arms: in
   `contract/domain.py` (the own-namespace refusal dropped), in `profile.py`
   (the resolver namespacing a namespaced name; the unresolved-reference
   refusal dropped; the shipped pack read from the base's path), in
   `consulted.py` (the sort-contract collection dropped — cited once by B2
   over the walk and once by M8 over a belief; the facet-namespace
   collection dropped; the `science` agreement dropped; the domain agreement
   dropped), in `facet_read.py` (a field-wise constructor; the corpus-view
   check dropped; re-validation skipped), in `evaluation.py` (an unheld
   observed dataset fetched), in `belief.py` (the ledger taken from nowhere,
   cited by a check that derives a belief; observed addresses dropped from
   the closure nodes), in `closure.py` (the `observed_facets` member
   emptied). `test_n2_cut22.py` audits them by the cut-12 pattern, with the
   staleness probe's baseline taken from the tree.
5. B5's byte-change test changes one payload byte on the observed dataset
   and nothing else; a test that also re-mints the run or the assessment
   exercises nothing. B5's one-carrier half is proved by a check that
   derives a belief, so the walk inside `evaluate` is what the sabotage
   reaches; and `gather`'s consulted set must equal `evaluate`'s over the
   same corpus, asserted by a check of its own.
6. The isolated case's claim schema must not reach `biology`: its operator
   is `testing/affects` and both slots are `testing` sorts. A case whose
   claim reaches `biology` through a sort is the dogfood shape, not the
   proof.
7. The cut document and declaration inventory are pinned by digest before
   discharge. No implementation discovery rewrites this frozen body; any
   deviation is dated in the results record.

## 6. Second reader

The written review of 2026-09-08 (three findings) is the second reading of
the design; this freeze carries its consequences: B7 and the isolated case
exist because of it, and B4's absent-dataset arm replaces a claim the tree
falsified.

## 7. Limitations

1. B6's TypeScript half runs as vitest checks in the acceptance module, not
   as sabotage arms: the N2 harness mutates the Python package only.
2. The reproduction re-run is the measurement, not an arm; its findings are
   filed to the reproduction record.
3. M6 is re-read, not re-counted.
4. The durable D6 arm is the dogfood shape only; the isolated case is
   portable.
```

- [ ] **Step 4: Run the checks that guard documents**

Run from `python/`: `uv run --frozen pytest tests/test_frozen_guards.py -q` and from the repo root: `tasks check --pretty`. Both must pass (the freeze document is not yet pinned by any guard).

- [ ] **Step 5: Commit the freeze**

```bash
git add docs/designs/2026-09-08-biology-pack-design.md docs/designs/2026-09-08-conformance-cut-22.md
git commit -m "docs(domain): freeze conformance cut 22 and correct the pack file name"
git log -1 --format=%h   # record this as CUT22_FREEZE_COMMIT for Task 11
```

- [ ] **Step 6: Confirm the plan's tasks are filed**

The plan was attached to `beliefs-1ce152` and one child filed per `### Task N:` heading when the plan was written. From the repo root:

```bash
tasks tree beliefs-1ce152 --pretty   # thirteen children, one per task heading
tasks check --pretty                 # no heading without a task, no task without a heading
```

Before starting any task below, `tasks start <its id>`; `tasks done <its id> "<what landed>"` goes in the same commit as its code.

---

### Task 2: Parse a cross-contract sort reference

**Files:**
- Modify: `python/src/beliefs/contract/domain.py` (`_parse_operator` ~line 370, the body parser's `dimensions` and `operators` loops ~lines 495–525)
- Test: `python/tests/test_domain_contract.py`

**Interfaces:**
- Produces: `OperatorDecl.arg_sorts` and `DimensionDecl.restriction_sort` may hold `"<namespace>/<name>"` as written; `_sort_reference(value, where, *, namespace, base_name, sorts) -> str`.
- Consumes: nothing new.

- [ ] **Step 1: Write the failing tests**

Append to `python/tests/test_domain_contract.py`:

```python
class TestSortReferences:
    """Design §4.1–§4.2 (biology pack): a bare name is this contract's; a
    namespaced name is another contract's and is deferred to compile."""

    def test_a_namespaced_reference_is_deferred_to_compile(self, parse, testing_document):
        crossing = copy.deepcopy(testing_document)
        crossing["operators"]["affects"]["arg_sorts"] = ["entity", "other/thing"]
        crossing["dimensions"]["population"]["restriction_sort"] = "other/cohort"
        contract = parse(crossing)
        assert contract.operators["affects"].arg_sorts == ("entity", "other/thing")
        assert contract.dimensions["population"].restriction_sort == "other/cohort"
        # As written, in the schema projection too (§4.5).
        assert contract.operators["affects"].schema_projection()["arg_sorts"] == ["entity", "other/thing"]

    def test_a_bare_undeclared_name_is_still_refused(self, parse, testing_document):
        broken = copy.deepcopy(testing_document)
        broken["operators"]["affects"]["arg_sorts"] = ["entity", "thing"]
        with pytest.raises(MalformedContract, match="not a sort this contract declares"):
            parse(broken)

    def test_own_namespace_is_refused(self, parse, testing_document):
        broken = copy.deepcopy(testing_document)
        broken["operators"]["affects"]["arg_sorts"] = ["entity", "testing/outcome"]
        with pytest.raises(MalformedContract, match="own namespace"):
            parse(broken)

    def test_the_base_namespace_is_refused(self, parse, testing_document):
        broken = copy.deepcopy(testing_document)
        broken["dimensions"]["population"]["restriction_sort"] = "science/cohort"
        with pytest.raises(MalformedContract, match="declares no claim vocabulary"):
            parse(broken)

    def test_a_malformed_reference_is_refused(self, parse, testing_document):
        for bad in ("Other/thing", "other/", "/thing", "a/b/c"):
            broken = copy.deepcopy(testing_document)
            broken["operators"]["affects"]["arg_sorts"] = ["entity", bad]
            with pytest.raises(MalformedContract):
                parse(broken)
```

- [ ] **Step 2: Run them to verify they fail**

Run: `cd python && uv run --frozen pytest tests/test_domain_contract.py::TestSortReferences -q`
Expected: 4 failures (the bare-name test passes already), the first with `not a sort this contract declares` for `other/thing`.

- [ ] **Step 3: Implement the reference rule**

In `python/src/beliefs/contract/domain.py`, add after `_no_duplicates`:

```python
def _sort_reference(
    value: object, where: str, *, namespace: str, base_name: str, sorts: Mapping[str, SortDecl]
) -> str:
    """§4.1 (biology pack): a bare name is a sort this contract declares; a
    `<namespace>/<name>` is another compiled contract's sort, deferred to
    compile. Two spellings are refused here: the contract's own namespace,
    because a local sort has exactly one spelling, and the base's, because
    the base declares no claim vocabulary (§7.1)."""
    if not isinstance(value, str) or not value:
        raise MalformedContract(f"{where}: {value!r} is not a sort reference")
    if "/" not in value:
        _name(value, where)
        if value not in sorts:
            raise MalformedContract(f"{where}: {value!r} is not a sort this contract declares")
        return value
    foreign, _, local = value.partition("/")
    _name(foreign, f"{where}: namespace")
    _name(local, f"{where}: sort")
    if foreign == namespace:
        raise MalformedContract(
            f"{where}: {value!r} names this contract's own namespace; a local sort is spelled by its local "
            f"name {local!r} and nothing else"
        )
    if foreign == base_name:
        raise MalformedContract(
            f"{where}: {value!r} names the base contract, which declares no claim vocabulary (§7.1); "
            "a slot sort is a domain's"
        )
    return value
```

Change `_parse_operator` so `arg_sorts` are taken as raw strings — replace

```python
    arg_sorts = tuple(_name(item, f"{where}: arg_sorts[{i}]") for i, item in enumerate(raw_sorts))
```

with

```python
    arg_sorts = tuple(
        item if isinstance(item, str) else _name(item, f"{where}: arg_sorts[{i}]") for i, item in enumerate(raw_sorts)
    )
```

In the body parser, replace the dimension check

```python
        restriction_sort = _name(decl["restriction_sort"], f"{where}: restriction_sort")
        if restriction_sort not in sorts:
            raise MalformedContract(
                f"{where}: restriction_sort {restriction_sort!r} is not a sort this contract declares"
            )
```

with

```python
        restriction_sort = _sort_reference(
            decl["restriction_sort"], f"{where}: restriction_sort", namespace=namespace, base_name=base.name, sorts=sorts
        )
```

and the operator slot check

```python
        for slot, sort in enumerate(operator.arg_sorts):
            if sort not in sorts:
                raise MalformedContract(f"{where}: arg_sorts[{slot}] {sort!r} is not a sort this contract declares")
```

with

```python
        for slot, sort in enumerate(operator.arg_sorts):
            _sort_reference(sort, f"{where}: arg_sorts[{slot}]", namespace=namespace, base_name=base.name, sorts=sorts)
```

Add `from collections.abc import Mapping` to the imports if it is not already there.

- [ ] **Step 4: Run the module's tests**

Run: `cd python && uv run --frozen pytest tests/test_domain_contract.py -q`
Expected: all pass, including `TestSortReferences` (5 tests).

- [ ] **Step 5: Commit**

```bash
git add python/src/beliefs/contract/domain.py python/tests/test_domain_contract.py
git commit -m "feat(contract): accept a namespaced sort reference at parse, deferred to compile"
```

---

### Task 3: Resolve sort references at compile

**Files:**
- Create: `fixtures/contracts/crossing.yaml`
- Modify: `python/src/beliefs/profile.py` (`compile_profile` ~lines 530–550, `_compile_operator` ~line 656)
- Test: `python/tests/test_profile.py`

**Interfaces:**
- Produces: `_resolve_sort(contract, name, sorts, *, where) -> str`; `_compile_operator(contract, operator, sorts)`; a `MalformedContract` at compile whose message starts `<contract>: <where> names sort '<term>', but no contract for namespace '<ns>' is compiled`.
- Consumes: Task 2's reference form.

- [ ] **Step 1: Add the crossing fixture**

Create `fixtures/contracts/crossing.yaml`:

```yaml
# A synthetic domain contract that names another contract's sorts (biology
# pack design §4). Owned by neither implementation: both parsers read it, and
# both compiles must resolve `testing/entity` when `testing` is compiled
# beside it and refuse when it is not.
contract: crossing
version: 1
lineage: genesis

sorts:
  local:
    vocabulary: { namespace: EX, release: "2026-01-01" }

dimensions:
  scope:
    restriction_sort: testing/cohort

operators:
  # Its only route to `testing` is slot 1's argument sort: no dimension, so
  # a walk that stops collecting sort contracts loses `testing` here (B2a).
  affects-local-entity:
    arity: 2
    arg_sorts: [local, testing/entity]
    sign_apt: true
    layers: [causal]
    dimensions: []
  # The dimension's restriction sort crosses too, on an operator whose slots
  # do not, so the restriction-sort route is exercised on its own (B1).
  scoped-local-local:
    arity: 2
    arg_sorts: [local, local]
    sign_apt: true
    layers: [causal]
    dimensions: [scope]
  same-local-local:
    arity: 2
    arg_sorts: [local, local]
    sign_apt: false
    layers: [structural]
    dimensions: []
```

- [ ] **Step 2: Write the failing tests**

Append to `python/tests/test_profile.py` (the module already has `base_contract`, `testing` and `parse` fixtures; add a `crossing_document` fixture reading the new file with `yaml.safe_load`):

```python
@pytest.fixture()
def crossing_document():
    import yaml

    path = Path(__file__).resolve().parents[2] / "fixtures" / "contracts" / "crossing.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


class TestCrossContractSlots:
    """Biology pack design §4.3: a namespaced reference resolves against the
    sorts of every contract in the compile, or refuses naming the namespace."""

    def test_a_foreign_sort_resolves_when_its_contract_is_compiled(self, base_contract, testing, crossing_document):
        crossing = domain.parse_domain_contract(crossing_document, source="<crossing>", base=base_contract, predecessor=None)
        profile = compile_profile(base_contract, [crossing, testing])
        operator = profile.operator("crossing/affects-local-entity")
        assert operator.arg_sorts == ("crossing/local", "testing/entity")
        assert operator.contract == "crossing" and operator.dimensions == ()
        assert profile.dimensions["crossing/scope"].restriction_sort == "testing/cohort"
        assert profile.operator("crossing/scoped-local-local").dimensions == ("crossing/scope",)
        assert profile.sorts["testing/entity"].contract == "testing"

    def test_the_resolver_namespaces_a_bare_name_once(self, base_contract, testing, crossing_document):
        crossing = domain.parse_domain_contract(crossing_document, source="<crossing>", base=base_contract, predecessor=None)
        profile = compile_profile(base_contract, [crossing, testing])
        assert profile.operator("crossing/same-local-local").arg_sorts == ("crossing/local", "crossing/local")

    def test_an_unresolved_reference_refuses_naming_the_namespace(self, base_contract, crossing_document):
        crossing = domain.parse_domain_contract(crossing_document, source="<crossing>", base=base_contract, predecessor=None)
        with pytest.raises(MalformedContract, match="no contract for namespace 'testing' is compiled"):
            compile_profile(base_contract, [crossing])

    def test_compile_order_is_inert(self, base_contract, testing, crossing_document):
        crossing = domain.parse_domain_contract(crossing_document, source="<crossing>", base=base_contract, predecessor=None)
        one = compile_profile(base_contract, [crossing, testing])
        other = compile_profile(base_contract, [testing, crossing])
        assert one.operator("crossing/affects-local-entity") == other.operator("crossing/affects-local-entity")
        assert one.activated_contracts == other.activated_contracts
```

Add `from beliefs.errors import MalformedContract` and `from beliefs.contract import domain` to the test module's imports if absent.

- [ ] **Step 3: Run them to verify they fail**

Run: `cd python && uv run --frozen pytest tests/test_profile.py::TestCrossContractSlots -q`
Expected: 4 failures; the first raises `KeyError`/`ProfileError` on `testing/entity` inside `_compile_operator`.

- [ ] **Step 4: Implement the two-pass compile**

In `python/src/beliefs/profile.py`, add near `_compile_operator`:

```python
def _resolve_sort(contract: DomainContract, name: str, sorts: Mapping[str, CompiledSort], *, where: str) -> str:
    """Biology pack §4.3: a bare name is namespaced once; a namespaced name
    passes through; either must name a compiled sort, or the compile refuses
    with the missing namespace named."""
    term = name if "/" in name else contract.term(name)
    if term not in sorts:
        namespace = term.partition("/")[0]
        raise MalformedContract(
            f"{contract.namespace}: {where} names sort {term!r}, but no contract for namespace {namespace!r} is "
            "compiled into this profile. A cross-contract slot resolves at compile or refuses; nothing here can "
            "stand behind a sort no compiled contract declares."
        )
    return term


def _compile_operator(contract: DomainContract, operator: OperatorDecl, sorts: Mapping[str, CompiledSort]) -> CompiledOperator:
    return CompiledOperator(
        term=contract.term(operator.name),
        arity=operator.arity,
        arg_sorts=tuple(
            _resolve_sort(contract, sort, sorts, where=f"operators.{operator.name}: arg_sorts[{slot}]")
            for slot, sort in enumerate(operator.arg_sorts)
        ),
        sign_apt=operator.sign_apt,
        layers=operator.layers,
        dimensions=tuple(contract.term(dimension) for dimension in operator.dimensions),
        retired=operator.retired,
        contract=contract.namespace,
    )
```

Replace the single loop in `compile_profile` that fills `sorts`, `dimensions` and `operators` with two passes:

```python
    # Pass one: every contract's sorts, so a reference across contracts has
    # something to resolve against regardless of compile order.
    for namespace in sorted(seen):
        contract = seen[namespace]
        for name, decl in contract.sorts.items():
            sorts[contract.term(name)] = CompiledSort(
                term=contract.term(name), vocabulary=decl.vocabulary, retired=decl.retired, contract=namespace
            )
    # Pass two: dimensions and operators, resolved against the complete map.
    for namespace in sorted(seen):
        contract = seen[namespace]
        for name, dimension in contract.dimensions.items():
            dimensions[contract.term(name)] = CompiledDimension(
                term=contract.term(name),
                restriction_sort=_resolve_sort(
                    contract, dimension.restriction_sort, sorts, where=f"dimensions.{name}: restriction_sort"
                ),
                retired=dimension.retired,
                contract=namespace,
            )
        for name, operator in contract.operators.items():
            operators[contract.term(name)] = _compile_operator(contract, operator, sorts)
```

Import `MalformedContract` from `beliefs.errors` in `profile.py`.

- [ ] **Step 5: Run the profile and claim tests**

Run: `cd python && uv run --frozen pytest tests/test_profile.py tests/test_claim.py tests/test_domain_contract.py -q`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add fixtures/contracts/crossing.yaml python/src/beliefs/profile.py python/tests/test_profile.py
git commit -m "feat(profile): resolve a cross-contract sort reference at compile or refuse naming the namespace"
```

---

### Task 4: The consulted walk reaches sort contracts and checks pin agreement

**Files:**
- Modify: `python/src/beliefs/consulted.py` (`consulted_contracts`)
- Modify: `python/src/beliefs/belief.py` (`evaluate`, the `consulted_contracts` call ~line 220)
- Modify: `python/src/beliefs/evaluation.py` (`evaluate_over`)
- Modify: `python/tests/test_consulted.py`, `python/tests/test_closure.py`, `python/tests/test_belief.py`, `python/tests/test_evaluation.py`, `python/tests/verification_fixtures.py` (synthetic pins → `pins_for`)
- Modify: `python/tests/n2_arms_cut2.py` (the D6 arm's `before`/`after`)
- Modify: `docs/designs/2026-08-09-conformance-cut-2.md` (dated amendment)

**Interfaces:**
- Produces: `consulted_contracts(...)` raising `ContractMismatch` on a consulted namespace whose pin disagrees with `profile`; `evaluate` and `evaluate_over` returning `Refused("profile-pin-mismatch: ...")`.
- Consumes: `CompiledOperator.arg_sorts` term identifiers (Task 3), `ProfileSpec.sorts`, `.dimensions`, `.base_contract_identity`, `.activated_contracts`.

- [ ] **Step 1: Write the failing walk tests**

In `python/tests/test_consulted.py`, change the module-level helpers so pins come from the profile:

```python
from profiles import pins_for

@pytest.fixture()
def pins(profile):
    def _pins(**overrides: str) -> CorpusPins:
        real = pins_for(profile)
        return CorpusPins(
            science_contract=overrides.get("science", real.science_contract),
            domains={**real.domains, **{k: v for k, v in overrides.items() if k != "science"}},
        )
    return _pins
```

and rewrite every existing call `pins()` / `pins("t-v1")` / `pins(science="base-1")` to `pins()` / `pins(testing="t-v1")` / `pins(science="base-1")`; replace `BASE` uses with `pins_for(profile).science_contract`. The existing assertions keep their meaning: `test_a_claim_reaches_its_contract_through_the_operator` asserts `("testing", pins_for(profile).domains["testing"]) in consulted`.

Then add:

```python
class TestSlotSorts:
    @pytest.fixture()
    def crossing_profile(self, base_contract, testing_document):
        import yaml

        path = Path(__file__).resolve().parents[2] / "fixtures" / "contracts" / "crossing.yaml"
        crossing = domain.parse_domain_contract(
            yaml.safe_load(path.read_text(encoding="utf-8")), source="<crossing>", base=base_contract, predecessor=None
        )
        testing = domain.parse_domain_contract(testing_document, source="<test>", base=base_contract, predecessor=None)
        return compile_profile(base_contract, [crossing, testing])

    def test_a_claim_reaches_its_slot_sorts_contracts(self, crossing_profile):
        """`affects-local-entity` declares no dimension, so `testing` is
        reached through slot 1's argument sort or not at all."""
        from beliefs.projection import claim_identity

        assert crossing_profile.operator("crossing/affects-local-entity").dimensions == ()
        claim = build_claim(
            profile=crossing_profile,
            operator="crossing/affects-local-entity",
            args=(Referent(sort="crossing/local", term="EX:l"), Referent(sort="testing/entity", term="EX:gene-x")),
            qualifiers={},
            polarity="positive",
            layer="causal",
        )
        uid = claim_identity(claim)
        pins = pins_for(crossing_profile)
        consulted = dict(
            consulted_contracts(
                claims={uid: claim},
                profile=crossing_profile,
                node_corpus={uid: "c1"},
                pins={"c1": CorpusPins(pins.science_contract, dict(pins.domains))},
                closure_nodes=(uid,),
            )
        )
        assert set(consulted) == {"science", "crossing", "testing"}

    def test_a_corpus_pinning_the_operators_contract_only_refuses(self, crossing_profile):
        from beliefs.projection import claim_identity

        claim = build_claim(
            profile=crossing_profile,
            operator="crossing/affects-local-entity",
            args=(Referent(sort="crossing/local", term="EX:l"), Referent(sort="testing/entity", term="EX:gene-x")),
            qualifiers={},
            polarity="positive",
            layer="causal",
        )
        uid = claim_identity(claim)
        pins = pins_for(crossing_profile)
        without_testing = CorpusPins(pins.science_contract, {"crossing": pins.domains["crossing"]})
        with pytest.raises(ContractDisagreement, match="'testing' is consulted but pinned by no corpus"):
            consulted_contracts(
                claims={uid: claim},
                profile=crossing_profile,
                node_corpus={uid: "c1"},
                pins={"c1": without_testing},
                closure_nodes=(uid,),
            )


class TestPinAgreement:
    """Biology pack §5.3a (B7): a consulted namespace's pin must equal the
    validating profile's identity; an unconsulted pin is not compared."""

    def test_the_base_pin_must_agree_with_the_profile(self, profile, pins):
        with pytest.raises(ContractMismatch, match="profile-pin-mismatch: science"):
            consulted_contracts(
                claims={}, profile=profile, node_corpus={}, pins={"c1": pins(science="science:" + "0" * 64)}, closure_nodes=()
            )

    def test_a_consulted_namespace_pinned_to_another_identity_refuses(self, profile, claim, pins):
        from beliefs.projection import claim_identity

        uid = claim_identity(claim)
        with pytest.raises(ContractMismatch, match="profile-pin-mismatch: testing"):
            consulted_contracts(
                claims={uid: claim},
                profile=profile,
                node_corpus={uid: "c1"},
                pins={"c1": pins(testing="testing:" + "1" * 64)},
                closure_nodes=(uid,),
            )

    def test_an_unconsulted_pin_is_not_compared(self, profile, pins):
        consulted = consulted_contracts(
            claims={}, profile=profile, node_corpus={}, pins={"c1": pins(unrelated="unrelated:" + "2" * 64)}, closure_nodes=()
        )
        assert dict(consulted) == {"science": pins_for(profile).science_contract}
```

Add `ContractMismatch` to the `beliefs.errors` import and `from pathlib import Path` at the top.

- [ ] **Step 2: Run them to verify they fail**

Run: `cd python && uv run --frozen pytest tests/test_consulted.py -q`
Expected: `TestSlotSorts::test_a_claim_reaches_its_slot_sorts_contracts` fails (`testing` missing), the two `TestPinAgreement` refusal tests fail (no exception).

- [ ] **Step 3: Implement the walk**

In `python/src/beliefs/consulted.py` replace the body from `consulted: dict[str, str] = {BASE_NAMESPACE: base_identities.pop()}` to the end of the function with:

```python
    base_identity = base_identities.pop()
    if base_identity != "science:" + profile.base_contract_identity:
        raise ContractMismatch(
            f"profile-pin-mismatch: science is pinned {base_identity[:20]}… but the profile carries "
            f"science:{profile.base_contract_identity[:12]}…; a derivation validates and digests under one identity, "
            "never two (biology pack §5.3a)"
        )
    consulted: dict[str, str] = {BASE_NAMESPACE: base_identity}

    # Each domain contract only if actually read. A claim reaches its
    # contract through the operator, and through every sort and dimension the
    # operator declares (D §8, ρA6); a facet read reaches its namespace.
    read: set[str] = set()
    for claim in claims.values():
        operator = profile.operator(claim.operator)
        read.add(operator.contract)
        for sort in operator.arg_sorts:
            read.add(profile.sorts[sort].contract)
        for dimension in operator.dimensions:
            declared = profile.dimensions[dimension]
            read.add(declared.contract)
            read.add(profile.sorts[declared.restriction_sort].contract)
    for node, keys in facets_read.items():
        if node not in closure_nodes:
            raise MalformedRecord(
                f"{node} is reported read but is not a closure node; a read ledger names closure members only"
            )
        for key in keys:
            namespace, separator, _ = key.partition("/")
            if separator:
                read.add(namespace)
    for namespace in sorted(read):
        identities = {pins[corpus].domains[namespace] for corpus in corpora if namespace in pins[corpus].domains}
        if not identities:
            raise ContractDisagreement(
                f"namespace {namespace!r} is consulted but pinned by no corpus in {corpora}; "
                "unresolvable, not merely disputed"
            )
        if len(identities) != 1:
            raise ContractDisagreement(
                f"namespace {namespace!r} resolves to {sorted(identities)} across corpora {corpora}; "
                "one derivation, one identity per namespace (D §8.1)"
            )
        identity = identities.pop()
        expected = profile.activated_contracts.get(namespace)
        if identity != f"{namespace}:{expected}":
            raise ContractMismatch(
                f"profile-pin-mismatch: {namespace} is pinned {identity[:20]}… but the profile carries "
                f"{namespace}:{str(expected)[:12]}…; a derivation validates and digests under one identity, "
                "never two (biology pack §5.3a)"
            )
        consulted[namespace] = identity
    return tuple(sorted(consulted.items()))
```

Import `ContractMismatch` from `beliefs.errors`. The sabotage sites Task 11 cites are the lines `        for sort in operator.arg_sorts:\n            read.add(profile.sorts[sort].contract)\n`, `            if separator:\n                read.add(namespace)\n`, `    if base_identity != "science:" + profile.base_contract_identity:\n` and `        if identity != f"{namespace}:{expected}":\n` — keep them exactly so.

- [ ] **Step 4: Map the refusal in `evaluate` and `evaluate_over`**

In `python/src/beliefs/belief.py`, `evaluate`, change the walk's exception handling to:

```python
    except ContractDisagreement as exc:
        return Refused(f"consulted-contracts-disagree: {exc}")
    except ContractMismatch as exc:
        return Refused(str(exc))  # already prefixed `profile-pin-mismatch: <namespace>` by the walk
```

In `python/src/beliefs/evaluation.py`, `evaluate_over`, wrap `gather` the same way:

```python
    try:
        inputs = gather(view, proposition, context=context, profile=profile, resolution=resolution, binding=binding)
    except ContractDisagreement as exc:
        return Refused(f"consulted-contracts-disagree: {exc}")
    except ContractMismatch as exc:
        return Refused(str(exc))
```

Import `ContractMismatch` in both modules.

- [ ] **Step 5: Rewrite synthetic pins in the other test modules**

Every `CorpusPins(science_contract="sci-1", ...)`, `"science-id-1"`, `"science-contract-id-1"` and the like under a real profile becomes `pins_for(<profile>)`:

- `python/tests/test_belief.py` `scenario()`: `pins={"c1": pins_for(PROFILE)}` (import `from profiles import pins_for`). The `test_w18j...` test adds `coordination` to `pins_for(PROFILE)`'s domains exactly as it does now.
- `python/tests/test_evaluation.py` `_fixture`: `pins={"c1": pins_for(PROFILE)}`.
- `python/tests/verification_fixtures.py` `evaluation_kwargs`: `pins={"c1": pins_for(PROFILE)}`.
- `python/tests/test_closure.py`: the two cut-2 D6 checks keep their names and assertions but bump a **compiled profile**:

```python
def _bumped(base_contract, testing_document, description: str):
    document = copy.deepcopy(testing_document)
    document["description"] = description
    testing = domain.parse_domain_contract(document, source="<test>", base=base_contract, predecessor=None)
    return compile_profile(base_contract, [testing])


def test_an_activated_but_unconsulted_bump_is_absent(base_contract, testing_document):
    # M8 negative half + D6: an extra pinned-but-unread namespace is bumped;
    # the walk output — and hence the digest — is unchanged.
    profile = _bumped(base_contract, testing_document, "v1")
    real = pins_for(profile)
    pins_v1 = CorpusPins(science_contract=real.science_contract, domains={**real.domains, "unrelated": "unrelated:" + "1" * 64})
    pins_v2 = CorpusPins(science_contract=real.science_contract, domains={**real.domains, "unrelated": "unrelated:" + "2" * 64})
    consulted_v1 = consulted_contracts(claims={}, profile=profile, node_corpus={}, pins={"c1": pins_v1}, closure_nodes=())
    consulted_v2 = consulted_contracts(claims={}, profile=profile, node_corpus={}, pins={"c1": pins_v2}, closure_nodes=())
    assert consulted_v1 == consulted_v2
    assert all(namespace != "unrelated" for namespace, _ in consulted_v1)
    kwargs = closure_kwargs()
    kwargs["consulted"] = consulted_v1
    baseline = build_closure(**kwargs).digest()
    kwargs["consulted"] = consulted_v2
    assert build_closure(**kwargs).digest() == baseline


def test_the_base_contract_arm_at_the_eligibility_hinge(base_contract, testing_document, base_contract_path):
    # D6: bump the *base* contract editorially and pin the bumped profile;
    # the digest moves even though this closure reads no base-profile facet.
    # The base parser takes exact top-level fields, so the editorial edit
    # goes on a facet's `description`, which `contract/facets.py` accepts.
    import yaml
    from beliefs.contract.base import parse_base_contract

    document = yaml.safe_load(base_contract_path.read_text(encoding="utf-8"))
    document["facets"]["empirical-observation"]["description"] = "bumped for the eligibility-hinge arm"
    bumped_base = parse_base_contract(document, source="<bumped base>")
    testing_v1 = domain.parse_domain_contract(testing_document, source="<test>", base=base_contract, predecessor=None)
    testing_v2 = domain.parse_domain_contract(testing_document, source="<test>", base=bumped_base, predecessor=None)
    profile_v1 = compile_profile(base_contract, [testing_v1])
    profile_v2 = compile_profile(bumped_base, [testing_v2])
    consulted_v1 = consulted_contracts(claims={}, profile=profile_v1, node_corpus={}, pins={"c1": pins_for(profile_v1)}, closure_nodes=())
    consulted_v2 = consulted_contracts(claims={}, profile=profile_v2, node_corpus={}, pins={"c1": pins_for(profile_v2)}, closure_nodes=())
    kwargs = closure_kwargs()
    kwargs["consulted"] = consulted_v1
    baseline = build_closure(**kwargs).digest()
    kwargs["consulted"] = consulted_v2
    assert build_closure(**kwargs).digest() != baseline
```

Any other `CorpusPins(...)` with a literal identity in these five files gets the same treatment.

- [ ] **Step 6: Re-point cut 2's D6 arm**

In `python/tests/n2_arms_cut2.py`, the first `_D6` arm's `Sabotage.before` becomes the landed lines and the `after` keeps its meaning:

```python
        sabotage=Sabotage(
            module="consulted.py",
            before=(
                "    read: set[str] = set()\n"
                "    for claim in claims.values():\n"
                "        operator = profile.operator(claim.operator)\n"
                "        read.add(operator.contract)"
            ),
            after=(
                "    read: set[str] = set()\n"
                "    for corpus in corpora:\n"
                "        read.update(pins[corpus].domains)\n"
                "    for claim in claims.values():\n"
                "        operator = profile.operator(claim.operator)\n"
                "        read.add(operator.contract)"
            ),
        ),
```

Append to `docs/designs/2026-08-09-conformance-cut-2.md`, after §10:

```markdown
> **Amended 2026-09-08 (biology pack design §5.3a, §10).** The consulted walk
> now reaches every claim's sort and dimension contracts and refuses a
> consulted namespace whose pin disagrees with the profile. Cut 2's D6 arm
> "consulting every pinned namespace" is re-pointed at the landed lines of
> `consulted.py` in `n2_arms_cut2.py` (fix the arm, never the source); its two
> checks and `test_closure.py`'s two D6 checks keep their names and their
> assertions and bump a compiled profile rather than a pin string. Commit:
> the one that lands this amendment.
```

- [ ] **Step 7: Run the portable suite**

Run: `cd python && uv run --frozen pytest -q 2>&1 | tail -3`
Expected: the summary line reports all passed (the count is above 4057) and `test_n2.py`'s cut-2 audit reports the D6 arm `sound`, not `stale`.

- [ ] **Step 8: Commit**

```bash
git add python/src/beliefs/consulted.py python/src/beliefs/belief.py python/src/beliefs/evaluation.py python/tests/test_consulted.py python/tests/test_closure.py python/tests/test_belief.py python/tests/test_evaluation.py python/tests/verification_fixtures.py python/tests/n2_arms_cut2.py docs/designs/2026-08-09-conformance-cut-2.md
git commit -m "feat(consulted): reach every slot sort's contract and refuse a pin that disagrees with the profile"
```

---

### Task 5: FacetRead and the domain-facet reader

**Files:**
- Create: `python/src/beliefs/facet_read.py`
- Modify: `python/src/beliefs/errors.py` (add `FacetUndeclared` beside `FacetPayloadRefused`)
- Modify: `python/src/beliefs/stored.py` (`dataset_node` gains `domain_facets`)
- Test: `python/tests/test_facet_read.py`

**Interfaces:**
- Produces: `FacetRead(address: str, key: str, payload_digest: str)` sealed, final, frozen, `init=False`, with `projection() -> list[str]` and a private `_minted(mint, *, address, key, payload_digest)`; `read_observed_facets(profile: ProfileSpec, view: ReadView, target: str) -> tuple[FacetRead, ...]` sorted by key, which **fetches** `target` from the corpus view and derives the address from the fetched dataset's declaration — there is no parameter for a node or an address; `FACET_READ_DOMAIN = "science.facet-read.v1"`; `FacetUndeclared(ScienceError)`; `stored.dataset_node(..., domain_facets: Mapping[str, Mapping[str, Any]] | None = None)`.
- Consumes: `facets.validate_payload`, `beliefs.identity.v1.digest` (bare hex), `ProfileSpec.facets`, `corpus.ReadView` (`corpus.py` imports neither `belief`, `closure` nor `evaluation`, so the import is cycle-free).

- [ ] **Step 1: Write the failing tests**

Create `python/tests/test_facet_read.py`:

```python
"""B3 and B4 (biology pack design §5.1–§5.2, §5.5): the corpus reader is the
only route to a `FacetRead`, the address is the fetched dataset's own, and
every read is validated. Every row here seeds a corpus by raw write and reads
it back through a fresh `ReadView`, because that is the only door."""

from __future__ import annotations

import pytest
from fixtures_cut4 import raw_write, reopen
from profiles import WITH_BIOLOGY

from beliefs import stored
from beliefs.dataset import dataset_address
from beliefs.errors import FacetPayloadRefused, FacetUndeclared, MalformedRecord
from beliefs.facet_read import FacetRead, read_observed_facets

RESOURCES = [{"name": "r-a", "digest": "sha256:" + "a" * 64}]


def _corpus(tmp_path, **domain_facets):
    node = stored.dataset_node("d-a", title="d-a", resources=RESOURCES, domain_facets=domain_facets)
    raw_write(tmp_path, node)
    return reopen(tmp_path), dataset_address(stored.dataset_declaration(node))


def test_facet_read_has_no_field_wise_constructor():
    with pytest.raises(MalformedRecord, match="minted by the reader"):
        FacetRead("dataset:sha256:" + "a" * 64, "biology/gene-axis", "0" * 64)  # type: ignore[call-arg]
    with pytest.raises(MalformedRecord):
        FacetRead(address="dataset:sha256:" + "a" * 64, key="biology/gene-axis", payload_digest="0" * 64)  # type: ignore[call-arg]


def test_the_reader_refuses_anything_but_a_corpus_view():
    """The public bypass B3 closes: an in-memory node, or any object shaped
    like a view, mints nothing."""
    node = stored.dataset_node("d-a", title="d-a", resources=RESOURCES, domain_facets={"biology/gene-axis": {"axis": "rows"}})

    class Shaped:
        def holds(self, ref: str) -> bool:
            return True

        def get(self, ref: str):
            return node

    with pytest.raises(MalformedRecord, match="corpus ReadView"):
        read_observed_facets(WITH_BIOLOGY, Shaped(), "dataset:d-a")  # type: ignore[arg-type]
    with pytest.raises(MalformedRecord, match="corpus ReadView"):
        read_observed_facets(WITH_BIOLOGY, node, "dataset:d-a")  # type: ignore[arg-type]


def test_the_reader_mints_one_row_per_declared_domain_facet(tmp_path):
    view, address = _corpus(tmp_path, **{"biology/gene-axis": {"axis": "rows"}})
    rows = read_observed_facets(WITH_BIOLOGY, view, "dataset:d-a")
    assert len(rows) == 1
    assert rows[0].address == address and rows[0].key == "biology/gene-axis"
    assert len(rows[0].payload_digest) == 64 and int(rows[0].payload_digest, 16) >= 0  # v1.digest: bare hex
    assert rows[0].projection() == [address, "biology/gene-axis", rows[0].payload_digest]


def test_the_address_is_the_fetched_datasets_own(tmp_path):
    """No caller supplies it: the address is derived from the declaration the
    corpus holds, so a row can never name a dataset other than the one read."""
    view, address = _corpus(tmp_path, **{"biology/gene-axis": {"axis": "rows"}})
    (row,) = read_observed_facets(WITH_BIOLOGY, view, "dataset:d-a")
    assert row.address == address == dataset_address(stored.dataset_declaration(view.get("dataset:d-a")))


def test_the_digest_follows_the_payload_bytes(tmp_path):
    one, _ = _corpus(tmp_path / "one", **{"biology/gene-axis": {"axis": "rows"}})
    other, _ = _corpus(tmp_path / "other", **{"biology/gene-axis": {"axis": "columns"}})
    assert read_observed_facets(WITH_BIOLOGY, one, "dataset:d-a")[0].payload_digest != read_observed_facets(WITH_BIOLOGY, other, "dataset:d-a")[0].payload_digest


def test_base_facets_are_not_this_readers(tmp_path):
    node = stored.dataset_node(
        "d-a", title="d-a", resources=RESOURCES,
        empirical_observation={"locator": "instrument:fixture", "attested_by": "actor:fixture"},
    )
    raw_write(tmp_path, node)
    assert read_observed_facets(WITH_BIOLOGY, reopen(tmp_path), "dataset:d-a") == ()


def test_an_unheld_target_is_malformed(tmp_path):
    view, _ = _corpus(tmp_path)
    with pytest.raises(MalformedRecord, match="not held"):
        read_observed_facets(WITH_BIOLOGY, view, "dataset:d-missing")


def test_a_malformed_payload_refuses_the_derivation(tmp_path):
    view, _ = _corpus(tmp_path, **{"biology/gene-axis": {}})
    with pytest.raises(FacetPayloadRefused, match="missing required field 'axis'"):
        read_observed_facets(WITH_BIOLOGY, view, "dataset:d-a")


def test_an_undeclared_namespaced_key_refuses(tmp_path):
    view, _ = _corpus(tmp_path, **{"other/thing": {"x": "y"}})
    with pytest.raises(FacetUndeclared, match="facet-undeclared: 'other/thing'"):
        read_observed_facets(WITH_BIOLOGY, view, "dataset:d-a")


def test_dataset_node_refuses_an_unnamespaced_domain_facet():
    with pytest.raises(MalformedRecord, match="namespaced"):
        stored.dataset_node("d-a", title="d-a", resources=[], domain_facets={"display": {"display_statement": "x"}})
```

- [ ] **Step 2: Run them to verify they fail**

Run: `cd python && uv run --frozen pytest tests/test_facet_read.py -q`
Expected: collection error, `No module named 'beliefs.facet_read'`.

- [ ] **Step 3: Add the error class and the `domain_facets` parameter**

In `python/src/beliefs/errors.py`, after `FacetPayloadRefused`:

```python
class FacetUndeclared(ScienceError):
    """A namespaced facet key on a record that the profile in force does not
    declare (biology pack §5.5): the profile the derivation runs under is
    stale against the corpus. Prefix `facet-undeclared:`."""
```

In `python/src/beliefs/stored.py`, extend `dataset_node`:

```python
def dataset_node(
    slug: str,
    *,
    title: str,
    resources: Sequence[Mapping[str, Any]] = (),
    empirical_observation: Mapping[str, Any] | None = None,
    basis: Mapping[str, Any] | None = None,
    domain_facets: Mapping[str, Mapping[str, Any]] | None = None,
) -> Node:
    facets: dict[str, Any] = {DATASET_FACET: {"resources": [dict(resource) for resource in resources]}}
    if empirical_observation is not None:
        facets[EMPIRICAL_OBSERVATION_FACET] = dict(empirical_observation)
    if basis is not None:
        facets[LINEAGE_BASIS_FACET] = dict(basis)
    for key, payload in (domain_facets or {}).items():
        if "/" not in key:
            raise MalformedRecord(
                f"{key!r} is not a namespaced facet key; a domain facet is `<namespace>/<name>` (F §3.3), and a base "
                "facet has its own parameter"
            )
        facets[key] = dict(payload)
    return _node("dataset", slug, title, facets, ())
```

- [ ] **Step 4: Write the reader module**

Create `python/src/beliefs/facet_read.py`:

```python
"""The first derivation-side read of a domain facet (biology pack design §5).

`FacetRead` is what a derivation knows about one facet it read off one
observed dataset: the dataset's address, the facet key, and the payload's
digest. It has no field-wise constructor, and the one reader below takes a
**corpus view and a target ref** — never a node, never an address — fetches
the dataset and derives the address from what it fetched. So a row is a
receipt for a read that happened against a corpus, and the ledger the
consulted walk consumes can never be authored by a caller: the property
F §5.6 asked for, made a property of the type and of its only constructor's
arguments.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final

from beliefs import stored
from beliefs.corpus import ReadView
from beliefs.dataset import dataset_address
from beliefs.errors import FacetUndeclared, MalformedRecord
from beliefs.facets import validate_payload
from beliefs.identity import v1
from beliefs.profile import ProfileSpec
from beliefs.sealed import sealed

__all__ = ["FACET_READ_DOMAIN", "FacetRead", "read_observed_facets"]

FACET_READ_DOMAIN = "science.facet-read.v1"

_MINT = object()


@sealed
@final
@dataclass(frozen=True, init=False)
class FacetRead:
    address: str
    key: str
    payload_digest: str

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise MalformedRecord(
            "FacetRead is minted by the reader — use read_observed_facets(profile, view, target). A field-wise "
            "constructor would let a caller author the read ledger the consulted walk digests (F §5.6)."
        )

    @classmethod
    def _minted(cls, mint: object, *, address: str, key: str, payload_digest: str) -> FacetRead:
        if mint is not _MINT:
            raise MalformedRecord("FacetRead._minted is the reader's, not a public constructor")
        row = object.__new__(cls)
        object.__setattr__(row, "address", address)
        object.__setattr__(row, "key", key)
        object.__setattr__(row, "payload_digest", payload_digest)
        return row

    def projection(self) -> list[str]:
        return [self.address, self.key, self.payload_digest]


def read_observed_facets(profile: ProfileSpec, view: ReadView, target: str) -> tuple[FacetRead, ...]:
    """Fetch `target` from the corpus view and mint one row per namespaced
    facet on it that `profile` declares for `dataset`, re-validated against
    the compiled schema, sorted by key. The address is derived from the
    fetched declaration, never supplied. Base facets are not this reader's. A
    key the profile does not declare, or a payload the schema refuses,
    refuses the derivation rather than dropping the read; an unheld target is
    malformed, because the caller (`gather`) has already filtered to held
    inputs and a miss here is a caller error, not a corpus state."""
    if not isinstance(view, ReadView):
        raise MalformedRecord(
            f"the domain-facet reader reads through a corpus ReadView, not a {type(view).__name__}; a row is a "
            "receipt for a read against a corpus, and nothing else can mint one (B3)"
        )
    if not view.holds(target):
        raise MalformedRecord(f"{target} is not held by this corpus; the reader is called over held observed inputs only")
    node = view.get(target)
    if node.kind != "dataset":
        raise MalformedRecord(f"{node.id}: the domain-facet reader reads observed datasets, not {node.kind!r}")
    address = dataset_address(stored.dataset_declaration(node))
    if address is None:
        raise MalformedRecord(f"{node.id}: an observed dataset with no content address has nothing to ledger against")
    rows: list[FacetRead] = []
    for key in sorted(node.facets):
        namespace, separator, _ = key.partition("/")
        if not separator:
            continue
        facet = profile.facets.get(key)
        if facet is None or "dataset" not in facet.attaches_to:
            raise FacetUndeclared(
                f"facet-undeclared: {key!r} on {node.id} is not a dataset facet the profile in force declares; the "
                "profile is stale against the corpus, and a read under it would digest a meaning nobody declared"
            )
        payload = node.facets[key]
        validate_payload(facet, payload, where=node.id)
        rows.append(
            FacetRead._minted(_MINT, address=address, key=key, payload_digest=v1.digest(FACET_READ_DOMAIN, payload))
        )
    return tuple(rows)
```

`from beliefs.identity import v1` is the import `contract/domain.py` and `record.py` already use; `v1.digest` returns the bare 64-character hex digest, no `sha256:` prefix. The lines `    if not isinstance(view, ReadView):\n` and `        validate_payload(facet, payload, where=node.id)\n` are Task 11 sabotage sites.

- [ ] **Step 5: Run the tests**

Run: `cd python && uv run --frozen pytest tests/test_facet_read.py tests/test_stored.py -q`
Expected: all pass. Then `uv run --frozen pyright` from `python/`: 0 errors.

- [ ] **Step 6: Commit**

```bash
git add python/src/beliefs/facet_read.py python/src/beliefs/errors.py python/src/beliefs/stored.py python/tests/test_facet_read.py
git commit -m "feat(facet-read): mint reader-only FacetRead rows from declared domain facets"
```

---

### Task 6: Thread the read through Records, the closure, gather and evaluate

**Files:**
- Modify: `python/src/beliefs/belief.py` (`Records`, `evaluate`)
- Modify: `python/src/beliefs/closure.py` (`build_closure`)
- Modify: `python/src/beliefs/evaluation.py` (`EvaluationInputs`, `gather`, `evaluate_over`)
- Modify: `python/tests/test_closure.py` (`closure_kwargs` gains `observed_facets=()`), `python/tests/test_belief.py` (every `Records(...)` unchanged — the new field defaults)
- Test: `python/tests/test_domain_facet_read.py` (created here; extended in Task 7), `python/tests/domain_facet_fixtures.py`

**Interfaces:**
- Produces: `Records.observed_facets: tuple[FacetRead, ...] = ()` (sorted, typed in `__post_init__`); `build_closure(..., observed_facets: tuple[FacetRead, ...])` and the projection member `"observed_facets"`; `EvaluationInputs.observed_facets`; `gather` reading held observed datasets **and** handing its rows and observed addresses to its own `consulted_contracts` call, so `gather`'s consulted set and `evaluate`'s are one set; `evaluate_over` mapping `FacetPayloadRefused` → `Refused("facet-payload-refused: …")` and `FacetUndeclared` → `Refused(str(exc))`.
- Consumes: Task 5's `FacetRead`, `read_observed_facets`; Task 4's walk.

- [ ] **Step 1: Write the shared seeding helper**

Create `python/tests/domain_facet_fixtures.py`:

```python
"""One corpus shape for the domain-facet rows (biology pack design §5.6):
a proposition at `testing/affects`, two assessments over two runs, each run
observing its own held dataset, `d-a` carrying `biology/gene-axis`. Seeded
by raw write (portable) or through an open `CorpusWriter` (durable)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from authority import ACTOR
from fixtures_cut4 import raw_write, reopen
from nodes.core.node import Node
from profiles import biology, pins_for
from test_evaluation import CLAIM_FACET, EX, GENE, OTHER_GENE, PHENO, _observations, _resources

from beliefs import stored
from beliefs.belief import Availability, SuppliedContext
from beliefs.closure import RetractionEnumeration
from beliefs.contract import domain
from beliefs.corpus import CorpusWriter, ReadView, lineage_snapshot
from beliefs.policy import BELIEF_V1, BELIEF_V1_FIXTURES, BELIEF_V1_RULE, PolicyBinding
from beliefs.profile import ProfileSpec, compile_profile, shipped_base_contract
from beliefs.resolution import build_snapshot

PROPOSITION_REF = "proposition:p"
REPO_ROOT = Path(__file__).resolve().parents[2]


def _fixture_document(name: str) -> dict:
    import yaml

    return yaml.safe_load((REPO_ROOT / "fixtures" / "contracts" / f"{name}.yaml").read_text(encoding="utf-8"))


def testing_contract(description: str | None = None):
    document = _fixture_document("testing")
    if description is not None:
        document["description"] = description
    return domain.parse_domain_contract(document, source="<test>", base=shipped_base_contract(), predecessor=None)


def crossing_contract():
    return domain.parse_domain_contract(_fixture_document("crossing"), source="<crossing>", base=shipped_base_contract(), predecessor=None)


def unrelated_contract(description: str):
    document = _fixture_document("testing")
    document["contract"] = "unrelated"
    document["description"] = description
    return domain.parse_domain_contract(document, source="<unrelated>", base=shipped_base_contract(), predecessor=None)


def profile_with(
    biology_description: str = "fixture",
    *,
    unrelated: str | None = None,
    testing_description: str | None = None,
    crossing: bool = False,
) -> ProfileSpec:
    contracts = [testing_contract(testing_description), biology(biology_description)]
    if unrelated is not None:
        contracts.append(unrelated_contract(unrelated))
    if crossing:
        contracts.append(crossing_contract())
    return compile_profile(shipped_base_contract(), contracts)


CROSSING_CLAIM: dict[str, Any] = {
    "operator": "crossing/affects-local-entity",
    "args": [OTHER_GENE, GENE],
    "qualifiers": {},
    "polarity": "positive",
    "layer": "causal",
}
"""A claim whose only route to `testing` is slot 1's foreign sort: the
operator declares no dimension. Both terms are members of the `EX`
vocabulary every fixture sort binds, so the snapshot in `kwargs_for`
resolves them."""


def seed(
    corpus: Path | CorpusWriter,
    *,
    axis: str | None = "rows",
    observes_missing: bool = False,
    claim: dict[str, Any] | None = None,
    proposition: str = PROPOSITION_REF,
) -> ReadView:
    """`axis=None` seeds `d-a` without the facet; `observes_missing` makes
    `run-a` observe a dataset that is never written; `claim` replaces the
    proposition's claim facet; `proposition` is what the assessments name
    (pass a ref the corpus does not hold for the claimless shape)."""
    domain_facets: dict[str, Any] = {"biology/gene-axis": {"axis": axis}} if axis is not None else {}
    nodes: list[Node] = [stored.proposition_node("p", title="p", claim=claim or CLAIM_FACET)]
    nodes.append(
        stored.dataset_node(
            "d-a", title="d-a", resources=_resources("a"),
            empirical_observation={"locator": "instrument:fixture", "attested_by": ACTOR},
            domain_facets=domain_facets,
        )
    )
    nodes.append(
        stored.dataset_node(
            "d-b", title="d-b", resources=_resources("b"),
            empirical_observation={"locator": "instrument:fixture", "attested_by": ACTOR},
        )
    )
    nodes.append(
        stored.run_node("run-a", title="run-a", spec="spec-a", observes=["dataset:d-missing" if observes_missing else "dataset:d-a"])
    )
    nodes.append(stored.run_node("run-b", title="run-b", spec="spec-b", observes=["dataset:d-b"]))
    assessments = [
        stored.assessment_node("a-1", title="a-1", spec="spec-a", run="run:run-a", proposition=proposition, outcome="supported", interpretation_rule="rule-1"),
        stored.assessment_node("a-2", title="a-2", spec="spec-b", run="run:run-b", proposition=proposition, outcome="supported", interpretation_rule="rule-1"),
    ]
    nodes.extend(assessments)
    for index, node in enumerate(assessments, start=1):
        value = stored.assessment_value(node)
        nodes.append(
            stored.verification_node(f"v-{index}", title=f"v-{index}", assessment=value.identity(), assessment_ref=node.id, scope="clean-environment", verdict="passed")
        )
    if isinstance(corpus, CorpusWriter):
        for node in nodes:
            corpus.add(node)
        return corpus.read_view
    corpus.mkdir(parents=True, exist_ok=True)
    for node in nodes:
        raw_write(corpus, node)
    return reopen(corpus)


def kwargs_for(view: ReadView, profile: ProfileSpec) -> dict[str, Any]:
    identities = {stored.assessment_value(n).identity() for n in view.iter_stored() if n.kind == "assessment"}
    return {
        "availability": Availability(
            observations=_observations("a", "b"),
            implementations={BELIEF_V1.identity: BELIEF_V1},
            fixtures={BELIEF_V1_RULE: BELIEF_V1_FIXTURES},
        ),
        "context": SuppliedContext(
            snapshot=lineage_snapshot(view, ("dataset:d-a", "dataset:d-b")),
            producer_snapshot_identity="producer-snapshot-1",
            retractions=RetractionEnumeration(found=(), coverage=("c1",)),
            node_corpus={identity: "c1" for identity in identities},
            pins={"c1": pins_for(profile)},
        ),
        "profile": profile,
        "resolution": build_snapshot(readable={EX: [GENE, PHENO, OTHER_GENE]}),
        "binding": PolicyBinding(rule=BELIEF_V1_RULE, implementation=BELIEF_V1.identity),
    }
```

`_observations` and `_resources` are module-level helpers in `test_evaluation.py`; importing them across test modules is how `test_verification_acceptance.py` already shares `CLAIM_FACET`, and neither pyright's basic mode nor the ruff rule set flags it.

- [ ] **Step 2: Write the failing tests**

Create `python/tests/test_domain_facet_read.py`:

```python
"""B4's absent-dataset arm and B5 (biology pack design §5.1, §5.4, §5.5)."""

from __future__ import annotations

import pytest
from domain_facet_fixtures import PROPOSITION_REF, kwargs_for, profile_with, seed

from beliefs.belief import Belief, Refused
from beliefs.evaluation import evaluate_over, gather


def _gathered(kwargs):
    return {k: v for k, v in kwargs.items() if k != "availability"}


def test_gather_reads_the_declared_facet_off_the_held_observed_dataset(tmp_path):
    profile = profile_with()
    view = seed(tmp_path)
    inputs = gather(view, PROPOSITION_REF, **_gathered(kwargs_for(view, profile)))
    assert [row.key for row in inputs.observed_facets] == ["biology/gene-axis"]
    # Consulted identities carry the namespace prefix; `activated_contracts` values do not.
    assert ("biology", "biology:" + profile.activated_contracts["biology"]) in [tuple(pair) for pair in inputs.consulted]
    assert ("dataset", inputs.observed_facets[0].address) in inputs.read_trace


def test_gather_and_evaluate_agree_on_the_consulted_set(tmp_path):
    """One walk, two callers: the closure `gather` builds and the one
    `evaluate` builds over `gather`'s records must digest identically, so a
    ledger `gather` read but did not pass to its own walk cannot hide."""
    profile = profile_with()
    view = seed(tmp_path)
    kwargs = kwargs_for(view, profile)
    inputs = gather(view, PROPOSITION_REF, **_gathered(kwargs))
    belief = evaluate_over(view, PROPOSITION_REF, **kwargs)
    assert isinstance(belief, Belief)
    assert inputs.closure().digest() == belief.belief_input_digest
    assert "biology" in dict(tuple(pair) for pair in inputs.consulted)


def test_an_absent_observed_dataset_is_absent_from_gather(tmp_path):
    profile = profile_with()
    view = seed(tmp_path, observes_missing=True)
    inputs = gather(view, PROPOSITION_REF, **_gathered(kwargs_for(view, profile)))
    assert inputs.observed_facets == ()
    assert all(entry.role != "observes" for entry in inputs.runs["run-a"].inputs)
    assert len(inputs.closure().projection["observes"]) == 1  # run-b's dataset only
    assert ("dataset", "dataset:d-missing") not in inputs.read_trace
    result = evaluate_over(view, PROPOSITION_REF, **kwargs_for(view, profile))
    assert not isinstance(result, Refused)


def test_the_member_is_present_and_empty_when_nothing_was_read(tmp_path):
    profile = profile_with()
    view = seed(tmp_path, axis=None)
    inputs = gather(view, PROPOSITION_REF, **_gathered(kwargs_for(view, profile)))
    assert inputs.closure().projection["observed_facets"] == []
    assert "biology" not in dict(tuple(pair) for pair in inputs.consulted)


def test_a_payload_byte_change_moves_the_digest(tmp_path):
    profile = profile_with()
    rows = evaluate_over(seed(tmp_path / "rows", axis="rows"), PROPOSITION_REF, **kwargs_for(seed(tmp_path / "rows2", axis="rows"), profile))
    columns = evaluate_over(seed(tmp_path / "cols", axis="columns"), PROPOSITION_REF, **kwargs_for(seed(tmp_path / "cols2", axis="columns"), profile))
    assert isinstance(rows, Belief) and isinstance(columns, Belief)
    assert rows.value == columns.value
    assert rows.belief_input_digest != columns.belief_input_digest


def test_a_malformed_payload_refuses_the_derivation_through_evaluate_over(tmp_path):
    profile = profile_with()
    view = seed(tmp_path, axis="")  # the schema wants a non-empty string
    result = evaluate_over(view, PROPOSITION_REF, **kwargs_for(view, profile))
    assert isinstance(result, Refused) and result.reason.startswith("facet-payload-refused:")


def test_evaluate_over_refuses_a_pin_mismatch_before_evaluate_runs(tmp_path):
    from dataclasses import replace

    from beliefs.consulted import CorpusPins

    profile = profile_with()
    view = seed(tmp_path)
    kwargs = kwargs_for(view, profile)
    pin = kwargs["context"].pins["c1"]
    wrong = CorpusPins(science_contract=pin.science_contract, domains={**pin.domains, "biology": "biology:" + "9" * 64})
    result = evaluate_over(view, PROPOSITION_REF, **{**kwargs, "context": replace(kwargs["context"], pins={"c1": wrong})})
    assert isinstance(result, Refused) and result.reason.startswith("profile-pin-mismatch: biology")
```

`Refused` is a frozen dataclass with one field, `reason`.

- [ ] **Step 3: Run them to verify they fail**

Run: `cd python && uv run --frozen pytest tests/test_domain_facet_read.py -q`
Expected: `AttributeError: 'EvaluationInputs' object has no attribute 'observed_facets'` and friends.

- [ ] **Step 4: Records and the closure member**

In `python/src/beliefs/belief.py`:

```python
from beliefs.facet_read import FacetRead
...
class Records:
    ...
    verifications: tuple[Verification, ...]
    observed_facets: tuple[FacetRead, ...] = ()
    """§5.3 (biology pack): the reader's rows, sorted, the one carrier of the
    read ledger and of the closure's `observed_facets` member."""

    def __post_init__(self) -> None:
        object.__setattr__(self, "claims", MappingProxyType(dict(self.claims)))
        object.__setattr__(self, "runs", MappingProxyType(dict(self.runs)))
        for row in self.observed_facets:
            if not isinstance(row, FacetRead):
                raise MalformedRecord(f"observed_facets carries a {type(row).__name__}, not a FacetRead; only the reader mints one")
        if list(self.observed_facets) != sorted(self.observed_facets, key=FacetRead.projection):
            raise MalformedRecord("observed_facets is sorted by (address, key, digest); an unsorted carrier is not the reader's")
```

In `evaluate`, replace the closure-node and walk block with:

```python
    matched = tuple(a for a in records.assessments if a.proposition == proposition)
    observed = tuple(
        sorted(
            {
                address
                for a in matched
                for entry in records.runs[a.run].inputs
                if entry.role == "observes" and (address := dataset_address(entry.dataset)) is not None
            }
        )
    )
    closure_nodes = tuple(a.identity() for a in matched) + observed
    ledger: dict[str, list[str]] = {}
    for row in records.observed_facets:
        ledger.setdefault(row.address, []).append(row.key)
    read_claims = {proposition: records.claims[proposition]} if proposition in records.claims else {}
    try:
        consulted = consulted_contracts(
            claims=read_claims,
            profile=profile,
            node_corpus=context.node_corpus,
            pins=context.pins,
            closure_nodes=closure_nodes,
            facets_read={address: tuple(keys) for address, keys in ledger.items()},
        )
    except ContractDisagreement as exc:
        return Refused(f"consulted-contracts-disagree: {exc}")
    except ContractMismatch as exc:
        return Refused(str(exc))
```

(`dataset_address` is imported from `beliefs.dataset`; `records.runs[a.run]` is how the closure already indexes runs.) Pass `observed_facets=records.observed_facets` to `build_closure`.

In `python/src/beliefs/closure.py`, add the parameter and member:

```python
from beliefs.facet_read import FacetRead
...
def build_closure(
    *,
    proposition: str,
    assessments: tuple[AssessmentValue, ...],
    runs: Mapping[str, RunValue],
    verifications: tuple[Verification, ...],
    snapshot: LineageSnapshot,
    producer_snapshot_identity: str,
    retractions: RetractionEnumeration,
    consulted: tuple[tuple[str, str], ...],
    binding: tuple[str, str],
    observed_facets: tuple[FacetRead, ...],
) -> Closure:
    ...
    projection: dict[str, object] = {
        ...
        "consulted": [list(pair) for pair in consulted],
        "observed_facets": [row.projection() for row in observed_facets],
    }
```

Update the docstring: `observed_facets` — supplied, the reader's rows, always present (§5.4). Check `closure.py` does not import `belief.py` (it does not); `facet_read.py` imports `profile`, which imports neither, so no cycle.

- [ ] **Step 5: gather and EvaluationInputs**

In `python/src/beliefs/evaluation.py`:

```python
from beliefs.errors import ContractDisagreement, ContractMismatch, FacetPayloadRefused, FacetUndeclared
from beliefs.facet_read import FacetRead, read_observed_facets
...
class EvaluationInputs:
    ...
    read_trace: tuple[ReadRef, ...]
    observed_facets: tuple[FacetRead, ...]

    def closure(self) -> Closure:
        return build_closure(..., binding=self.binding, observed_facets=self.observed_facets)

    def records(self) -> Records:
        return Records(
            claims=...,
            assessments=self.assessments,
            runs=self.runs,
            source_assertions=(),
            verifications=self.verifications,
            observed_facets=self.observed_facets,
        )
```

In `gather`, replace the runs loop with:

```python
    runs: dict[str, RunValue] = {}
    observed: dict[tuple[str, str, str], FacetRead] = {}
    for a in matched:
        ref = stored.typed_ref("run", a.run)
        if a.run in runs or not view.holds(ref):
            continue
        run_node = view.get(ref)
        runs[a.run] = run_value(view, ref)
        trace.append(("run", a.run))
        for target in stored.inputs_of(run_node, stored.OBSERVES):
            if not view.holds(target):
                continue
            address = dataset_address(stored.dataset_declaration(view.get(target)))
            if address is None:
                continue
            trace.append(("dataset", address))
            for row in read_observed_facets(profile, view, target):
                observed[(row.address, row.key, row.payload_digest)] = row
    rows = tuple(observed[key] for key in sorted(observed))
```

Then **wire the rows and the observed addresses into `gather`'s own walk**. The existing call

```python
    consulted = consulted_contracts(
        claims={proposition: claim} if claim is not None else {},
        profile=profile,
        node_corpus=context.node_corpus,
        pins=context.pins,
        closure_nodes=tuple(sorted(ids)),
        # §5.6: no derivation reads a domain facet yet; the read ledger arrives with the first reader (slice 2)
        facets_read={},
    )
```

becomes

```python
    ledger: dict[str, list[str]] = {}
    for row in rows:
        ledger.setdefault(row.address, []).append(row.key)
    observed_addresses = tuple(sorted({row.address for row in rows} | {ref for kind, ref in trace if kind == "dataset"}))
    consulted = consulted_contracts(
        claims={proposition: claim} if claim is not None else {},
        profile=profile,
        node_corpus=context.node_corpus,
        pins=context.pins,
        closure_nodes=tuple(sorted(ids)) + observed_addresses,
        facets_read={address: tuple(keys) for address, keys in ledger.items()},
    )
```

and `EvaluationInputs(..., observed_facets=rows)`. `evaluate` rebuilds the same ledger from `Records.observed_facets` and the same closure nodes from the run inputs, so the two walks see one input; `test_gather_and_evaluate_agree_on_the_consulted_set` holds them to it. The line pair `            if not view.holds(target):\n                continue\n` is a Task 11 sabotage site; keep it exactly.

In `evaluate_over`, widen the `gather` guard:

```python
    except ContractDisagreement as exc:
        return Refused(f"consulted-contracts-disagree: {exc}")
    except ContractMismatch as exc:
        return Refused(str(exc))
    except FacetPayloadRefused as exc:
        return Refused(f"facet-payload-refused: {exc}")
    except FacetUndeclared as exc:
        return Refused(str(exc))
```

Update `closure_kwargs()` in `python/tests/test_closure.py` to include `"observed_facets": ()`.

- [ ] **Step 6: Run the suite**

Run: `cd python && uv run --frozen pytest -q 2>&1 | tail -3 && uv run --frozen pyright && uv run --frozen ruff check .`
Expected: all pass; `test_domain_facet_read.py`'s six tests pass; 0 pyright errors.

- [ ] **Step 7: Commit**

```bash
git add python/src/beliefs/belief.py python/src/beliefs/closure.py python/src/beliefs/evaluation.py python/tests/domain_facet_fixtures.py python/tests/test_domain_facet_read.py python/tests/test_closure.py
git commit -m "feat(evaluation): read declared domain facets off observed datasets into the ledger and the closure"
```

---

### Task 7: D6's two cases and the M8 arm

**Files:**
- Modify: `python/tests/test_domain_facet_read.py`
- Modify: `python/tests/test_domain_contract.py` (M6 over a namespaced slot)

**Interfaces:**
- Consumes: `domain_facet_fixtures.profile_with`, `seed`, `kwargs_for`; `profiles.biology`.
- Produces: the check names Task 11's arms cite.

- [ ] **Step 1: Write the isolated case**

Append to `python/tests/test_domain_facet_read.py`:

```python
# --- D6's facet arm, the isolated case (design §5.6) ------------------------


def _belief(view, profile):
    result = evaluate_over(view, PROPOSITION_REF, **kwargs_for(view, profile))
    assert isinstance(result, Belief), result
    return result


def test_isolated_case_biology_enters_through_the_ledger_alone(tmp_path):
    """The claim is at `testing/affects` over `testing` sorts; nothing in its
    schema reaches `biology`. With the facet read, biology is consulted; with
    the facet absent, it is not."""
    profile = profile_with()
    with_facet = gather(seed(tmp_path / "with"), PROPOSITION_REF, **_gathered(kwargs_for(seed(tmp_path / "with2"), profile)))
    without = gather(seed(tmp_path / "without", axis=None), PROPOSITION_REF, **_gathered(kwargs_for(seed(tmp_path / "without2", axis=None), profile)))
    assert with_facet.claim is not None and with_facet.claim.operator == "testing/affects"
    assert "biology" in dict(tuple(p) for p in with_facet.consulted)
    assert "biology" not in dict(tuple(p) for p in without.consulted)


def test_isolated_case_a_biology_bump_moves_the_digest(tmp_path):
    view = seed(tmp_path)
    before = _belief(view, profile_with("fixture"))
    after = _belief(view, profile_with("fixture, bumped"))
    assert before.value == after.value
    assert before.belief_input_digest != after.belief_input_digest


def test_isolated_case_an_unrelated_bump_leaves_it(tmp_path):
    view = seed(tmp_path)
    before = _belief(view, profile_with("fixture", unrelated="v1"))
    after = _belief(view, profile_with("fixture", unrelated="v2"))
    assert before.belief_input_digest == after.belief_input_digest


def test_isolated_case_holds_with_no_claim_record(tmp_path):
    """A proposition with no claim consults only the base — plus biology
    through the facet. The assessments name a proposition the corpus does not
    hold, as `test_evaluation.claimless_fixture` does."""
    absent = "proposition:never-stored"
    profile = profile_with()
    view = seed(tmp_path, proposition=absent)
    inputs = gather(view, absent, **_gathered(kwargs_for(view, profile)))
    assert inputs.claim is None
    assert set(dict(tuple(p) for p in inputs.consulted)) == {"science", "biology"}
```

- [ ] **Step 2: Write the dogfood shape and the M8 arm**

Append:

```python
# --- the dogfood shape: biology by both routes (design §5.6) ----------------


def test_dogfood_shape_reaches_biology_by_both_routes(tmp_path):
    """A claim at `biology/affects` (the fixture's operator) whose sorts are
    biology's, over the same facet-bearing dataset: dropping either route
    leaves biology consulted, which is why this case is the measurement and
    the isolated case is the proof."""
    from test_evaluation import GENE, OTHER_GENE

    profile = profile_with()
    biology_claim = {"operator": "biology/affects", "args": [GENE, OTHER_GENE], "qualifiers": {}, "polarity": "positive", "layer": "causal"}
    view = seed(tmp_path, claim=biology_claim)
    inputs = gather(view, PROPOSITION_REF, **_gathered(kwargs_for(view, profile)))
    assert inputs.claim is not None and inputs.claim.operator == "biology/affects"
    assert "biology" in dict(tuple(p) for p in inputs.consulted)
    assert [row.key for row in inputs.observed_facets] == ["biology/gene-axis"]


# --- M8's added arm (design §7) --------------------------------------------


def test_m8_an_editorial_bump_of_a_foreign_sorts_contract_leaves_claim_identity_and_moves_the_digest(tmp_path):
    """The claim is at `crossing/affects-local-entity`, no domain facet is in
    the closure (`axis=None`), and the bumped contract is `testing`, reached
    through slot 1's sort and nothing else. Dropping the walk's sort-contract
    collection leaves `testing` unconsulted and this test fails (M8a)."""
    from domain_facet_fixtures import CROSSING_CLAIM
    from beliefs.projection import claim_identity

    view = seed(tmp_path, axis=None, claim=CROSSING_CLAIM)
    before = profile_with(crossing=True)
    after = profile_with(crossing=True, testing_description="editorial")
    one = evaluate_over(view, PROPOSITION_REF, **kwargs_for(view, before))
    two = evaluate_over(view, PROPOSITION_REF, **kwargs_for(view, after))
    assert isinstance(one, Belief) and isinstance(two, Belief)
    inputs_one = gather(view, PROPOSITION_REF, **_gathered(kwargs_for(view, before)))
    inputs_two = gather(view, PROPOSITION_REF, **_gathered(kwargs_for(view, after)))
    assert inputs_one.observed_facets == () and inputs_one.claim is not None and inputs_two.claim is not None
    assert claim_identity(inputs_one.claim) == claim_identity(inputs_two.claim)
    assert "testing" in dict(tuple(p) for p in inputs_one.consulted)
    assert one.value == two.value and one.belief_input_digest != two.belief_input_digest
```

The `claim=` keyword is the one `seed` gained in Task 6; the biology fixture's `gene` sort binds the same `EX` vocabulary as `testing`'s, so the snapshot in `kwargs_for` resolves both terms.

- [ ] **Step 3: M6 over a namespaced slot**

Append to `python/tests/test_domain_contract.py`'s `TestSuccession` class (the redefinition refusal is `SuccessionViolation`, with the text the class's existing tests match):

```python
    def test_a_successor_rewriting_a_namespaced_slot_is_refused(self, parse, testing_document, genesis):
        operators = copy.deepcopy(testing_document["operators"])
        operators["affects"]["arg_sorts"] = ["entity", "other/outcome"]
        document = TestSuccession.successor_document(testing_document, genesis, operators=operators)
        with pytest.raises(SuccessionViolation, match="different canonical schema projection"):
            parse(document, predecessor=genesis)
```

- [ ] **Step 4: Run and commit**

Run: `cd python && uv run --frozen pytest tests/test_domain_facet_read.py tests/test_domain_contract.py -q`
Expected: all pass.

```bash
git add python/tests/test_domain_facet_read.py python/tests/test_domain_contract.py python/tests/domain_facet_fixtures.py
git commit -m "test(domain): prove D6's facet arm on the isolated case and the dogfood shape; add M8's sort-contract arm"
```

---

### Task 8: Mirror the slot rule in TypeScript

**Files:**
- Modify: `ts/src/contract.ts` (`parseDomainContract`: the dimension and operator sort checks ~lines 495–530)
- Modify: `ts/src/profile.ts` (`compileProfile` ~lines 170–192)
- Test: `ts/tests/contract-scope.test.ts`

**Interfaces:**
- Produces: `sortReference(value, where, namespace, baseName, sorts)` in `contract.ts`; `resolveSort(contract, name, sorts)` in `profile.ts`; the same refusal texts as Python, prefix for prefix.

- [ ] **Step 1: Write the failing tests**

Append to `ts/tests/contract-scope.test.ts` (it already defines `BASE`, `DOMAIN` and `base`):

```ts
describe("a cross-contract sort reference (biology pack design §4)", () => {
  const crossing = `
contract: crossing
version: 1
lineage: genesis
sorts:
  local:
    vocabulary: { namespace: EX, release: "2026-01-01" }
dimensions: {}
operators:
  affects-local-entity:
    arity: 2
    arg_sorts: [local, testing/entity]
    sign_apt: true
    layers: [causal]
    dimensions: []
`;
  it("defers a namespaced reference to compile and resolves it there", () => {
    const contract = parseDomainContract(crossing, "<crossing>", base);
    expect(contract.operators["affects-local-entity"].argSorts).toEqual(["local", "testing/entity"]);
    const testing = parseDomainContract(DOMAIN, "<domain>", base);
    const profile = compileProfile(base, [contract, testing]);
    expect(profile.operators["crossing/affects-local-entity"].argSorts).toEqual(["crossing/local", "testing/entity"]);
  });
  it("refuses an unresolved reference at compile, naming the namespace", () => {
    const contract = parseDomainContract(crossing, "<crossing>", base);
    expect(() => compileProfile(base, [contract])).toThrow(MalformedContract);
    expect(() => compileProfile(base, [contract])).toThrow(/no contract for namespace "testing" is compiled/);
  });
  it("refuses the contract's own namespace and the base's at parse", () => {
    const own = crossing.replace("testing/entity", "crossing/local");
    expect(() => parseDomainContract(own, "<crossing>", base)).toThrow(/own namespace/);
    const sci = crossing.replace("testing/entity", "science/local");
    expect(() => parseDomainContract(sci, "<crossing>", base)).toThrow(/declares no claim vocabulary/);
  });
  it("still refuses a bare undeclared name", () => {
    const bare = crossing.replace("testing/entity", "entity");
    expect(() => parseDomainContract(bare, "<crossing>", base)).toThrow(/not a declared sort/);
  });
});
```

- [ ] **Step 2: Run to verify they fail**

Run: `cd ts && npx vitest run tests/contract-scope.test.ts`
Expected: the first test fails on `"testing/entity" is not a declared sort`.

- [ ] **Step 3: Implement the parse half**

In `ts/src/contract.ts`, add near `tag`:

```ts
function sortReference(
  value: unknown,
  where: string,
  namespace: string,
  baseName: string,
  sorts: DeclarationTable<SortDecl>,
): string {
  if (typeof value !== "string" || value.length === 0) {
    throw new MalformedContract(`${where}: ${JSON.stringify(value)} is not a sort reference`);
  }
  if (!value.includes("/")) {
    tag(value, where);
    if (!(value in sorts)) throw new MalformedContract(`${where}: ${JSON.stringify(value)} is not a declared sort`);
    return value;
  }
  const [foreign, local, ...rest] = value.split("/");
  if (rest.length > 0 || !NAME.test(foreign) || !NAME.test(local)) {
    throw new MalformedContract(`${where}: ${JSON.stringify(value)} is not a sort reference`);
  }
  if (foreign === namespace) {
    throw new MalformedContract(
      `${where}: ${JSON.stringify(value)} names this contract's own namespace; a local sort is spelled by its local name ${JSON.stringify(local)} and nothing else`,
    );
  }
  if (foreign === baseName) {
    throw new MalformedContract(
      `${where}: ${JSON.stringify(value)} names the base contract, which declares no claim vocabulary (§7.1); a slot sort is a domain's`,
    );
  }
  return value;
}
```

Replace the dimension check with `const restrictionSort = sortReference(dimensionBody.restriction_sort, \`${where}.restriction_sort\`, namespace, base.name, sorts);` and the operator slot loop with `const argSorts = operatorBody.arg_sorts.map((entry, index) => sortReference(entry, \`${where}.arg_sorts[${index}]\`, namespace, base.name, sorts));` (delete the `for (const sort of argSorts)` refusal loop that follows). `base.name` is the `readonly name: string` on `BaseContract`.

- [ ] **Step 4: Implement the compile half**

In `ts/src/profile.ts`, replace the per-contract loop's sort collection with two passes:

```ts
  const sortOwners: Record<string, string> = Object.create(null);
  for (const contract of domains) {
    // ... the existing provenance, base and namespace checks stay above ...
    for (const name of Object.keys(contract.sorts)) {
      sorts.push(term(contract.namespace, name));
      sortOwners[term(contract.namespace, name)] = contract.namespace;
    }
  }
  const resolveSort = (contract: DomainContract, name: string, where: string): string => {
    const resolved = name.includes("/") ? name : term(contract.namespace, name);
    if (!(resolved in sortOwners)) {
      const namespace = resolved.split("/")[0];
      throw new MalformedContract(
        `${contract.namespace}: ${where} names sort ${JSON.stringify(resolved)}, but no contract for namespace ${JSON.stringify(namespace)} is compiled into this profile`,
      );
    }
    return resolved;
  };
  for (const contract of domains) {
    for (const [name, declaration] of Object.entries(contract.dimensions)) {
      dimensions[term(contract.namespace, name)] = Object.freeze({
        term: term(contract.namespace, name),
        restrictionSort: resolveSort(contract, declaration.restrictionSort, `dimensions.${name}: restriction_sort`),
      });
    }
    for (const [name, declaration] of Object.entries(contract.operators)) {
      operators[term(contract.namespace, name)] = Object.freeze({
        term: term(contract.namespace, name),
        arity: declaration.arity,
        argSorts: Object.freeze(declaration.argSorts.map((sort, slot) => resolveSort(contract, sort, `operators.${name}: arg_sorts[${slot}]`))),
        signApt: declaration.signApt,
        layers: Object.freeze([...declaration.layers]),
        dimensions: Object.freeze(declaration.dimensions.map((dimension) => term(contract.namespace, dimension))),
      });
    }
  }
```

Keep the facet loop where it is in the first pass. Import `MalformedContract` from `./errors.js` in `profile.ts`.

- [ ] **Step 5: Run the TypeScript gates**

Run: `cd ts && npm run typecheck && npm run check && npx vitest run`
Expected: all pass, including the parity fixture test (a same-contract profile compiles to the same terms as before).

- [ ] **Step 6: Commit**

```bash
git add ts/src/contract.ts ts/src/profile.ts ts/tests/contract-scope.test.ts
git commit -m "feat(ts): mirror the cross-contract sort reference and its refusals"
```

---

### Task 9: Ship the biology pack

**Files:**
- Create: `domains/biology/DOMAIN.yaml`
- Create: `python/src/beliefs/domains/biology/DOMAIN.yaml` (byte-identical copy)
- Modify: `python/src/beliefs/profile.py` (`shipped_domain_contract`)
- Test: `python/tests/test_shipped_biology.py`

**Interfaces:**
- Produces: `shipped_domain_contract(namespace: str) -> DomainContract`, cached, parsing `beliefs/domains/<namespace>/DOMAIN.yaml` against `shipped_base_contract()`; `ProfileError` for a namespace the package does not ship.

- [ ] **Step 1: Write the failing tests**

Create `python/tests/test_shipped_biology.py`:

```python
"""B6 (biology pack design §3.2, §6.1): the first packaged domain contract."""

from importlib import resources

import pytest

from beliefs.errors import ProfileError
from beliefs.profile import compile_profile, shipped_base_contract, shipped_domain_contract


def test_the_packaged_copy_is_byte_identical_to_the_normative_file(fixtures_dir):
    normative = fixtures_dir.parent / "domains" / "biology" / "DOMAIN.yaml"
    packaged = resources.files("beliefs").joinpath("domains/biology/DOMAIN.yaml").read_bytes()
    assert packaged == normative.read_bytes()


def test_the_shipped_pack_declares_the_floor():
    pack = shipped_domain_contract("biology")
    assert pack.namespace == "biology"
    assert set(pack.sorts) == {"molecular-entity"}
    binding = pack.sorts["molecular-entity"].vocabulary
    assert (binding.namespace, binding.release) == ("HGNC", "2026-07-01")
    assert set(pack.operators) == {
        "affects-molecular-entity-molecular-entity",
        "associates-with-molecular-entity-molecular-entity",
        "regulates-molecular-entity-molecular-entity",
    }
    assert set(pack.facets) == {"biology/gene-axis"}
    assert set(pack.facets["biology/gene-axis"].fields) == {"axis", "namespace"}


def test_the_shipped_pack_compiles_with_the_shipped_base():
    profile = compile_profile(shipped_base_contract(), [shipped_domain_contract("biology")])
    operator = profile.operator("biology/affects-molecular-entity-molecular-entity")
    assert operator.arg_sorts == ("biology/molecular-entity", "biology/molecular-entity")
    assert "dataset" in profile.facets["biology/gene-axis"].attaches_to


def test_the_pack_is_parsed_once():
    assert shipped_domain_contract("biology") is shipped_domain_contract("biology")


def test_an_unshipped_namespace_is_refused():
    with pytest.raises(ProfileError, match="ships no domain contract"):
        shipped_domain_contract("chemistry")
```

- [ ] **Step 2: Run to verify they fail**

Run: `cd python && uv run --frozen pytest tests/test_shipped_biology.py -q`
Expected: `ImportError: cannot import name 'shipped_domain_contract'`.

- [ ] **Step 3: Write the pack**

Create `domains/biology/DOMAIN.yaml`:

```yaml
# The biology domain contract — the first domain the package ships
# (biology pack design §3.2). It declares what is biology's regardless of
# corpus: one sort bound to HGNC at an exact release, the three
# protein→protein relations mm30 recorded, and the gene-axis facet a
# tabular dataset carries when one axis holds molecular entities.
#
# The HGNC release is the most recent quarterly archive date on or before
# the design date (2026-09-08). No release is held in this slice, so the
# sort resolves `not-consulted`; succession makes this binding the sort's
# for the life of the identifier (design §12).
#
# Operators with a corpus-local sort live in the corpus's own contract and
# name `biology/molecular-entity` in their protein slot (design §3.3, §4).
contract: biology
version: 1
lineage: genesis

sorts:
  molecular-entity:
    vocabulary: { namespace: HGNC, release: "2026-07-01" }

dimensions: {}

operators:
  affects-molecular-entity-molecular-entity:
    arity: 2
    arg_sorts: [molecular-entity, molecular-entity]
    sign_apt: true
    layers: [causal, structural, statistical]
    dimensions: []
  associates-with-molecular-entity-molecular-entity:
    arity: 2
    arg_sorts: [molecular-entity, molecular-entity]
    sign_apt: true
    layers: [statistical, causal]
    dimensions: []
  regulates-molecular-entity-molecular-entity:
    arity: 2
    arg_sorts: [molecular-entity, molecular-entity]
    sign_apt: true
    layers: [causal]
    dimensions: []

facets:
  gene-axis:
    attaches_to: [dataset]
    fields:
      axis: { type: string, required: true }
      namespace: { type: string, required: true }
```

Copy it: `cp domains/biology/DOMAIN.yaml python/src/beliefs/domains/biology/DOMAIN.yaml` (create the directory; hatch packages `src/beliefs` wholesale, so the data file ships without a manifest entry — the base copy under `contracts/science/` proves that).

- [ ] **Step 4: Add `shipped_domain_contract`**

In `python/src/beliefs/profile.py`, after `shipped_base_contract`:

```python
@cache
def shipped_domain_contract(namespace: str) -> DomainContract:
    """Parse a domain contract carried by this package, against the shipped
    base (biology pack §6.1). Distribution beyond the package stays open."""
    from beliefs.contract.document import parse_document
    from beliefs.contract.domain import parse_domain_contract

    source = f"beliefs/domains/{namespace}/DOMAIN.yaml"
    resource = resources.files("beliefs").joinpath(f"domains/{namespace}/DOMAIN.yaml")
    if not resource.is_file():
        raise ProfileError(f"this package ships no domain contract for namespace {namespace!r}")
    text = resource.read_text(encoding="utf-8")
    return parse_domain_contract(
        parse_document(text, source=source), source=source, base=shipped_base_contract(), predecessor=None
    )
```

Add `"shipped_domain_contract"` to `__all__`. The line `    resource = resources.files("beliefs").joinpath(f"domains/{namespace}/DOMAIN.yaml")` is a Task 11 sabotage site.

- [ ] **Step 5: Run and commit**

Run: `cd python && uv run --frozen pytest tests/test_shipped_biology.py tests/test_shipped_base.py -q && uv run --frozen pyright`
Expected: all pass.

```bash
git add domains/biology/DOMAIN.yaml python/src/beliefs/domains/biology/DOMAIN.yaml python/src/beliefs/profile.py python/tests/test_shipped_biology.py
git commit -m "feat(domain): ship the biology pack — molecular-entity, gene-axis, three protein relations"
```

---

### Task 10: The reproduction's corpus-local contract and held concept vocabulary

**Files:**
- Create: `python/tools/reproduction/mm30.yaml`
- Create: `python/tools/reproduction/concepts.py` (step 1b)
- Modify: `python/tools/reproduction/vocabulary.py`, `type_target.py`, `hold.py`, `belief.py`, `world.py`
- Modify: `python/tools/type_corpus_claims.py` (row-shaped plan)
- Test: `python/tests/test_reproduction_driver.py`

**Interfaces:**
- Produces: `vocabulary.profile()` compiling base + biology pack + `mm30`; `vocabulary.plan()` returning `{"operators": {(predicate, subject_kind, object_kind): term}, "sorts": {...}, "layers": {...}, "polarities": {...}}`; `vocabulary.pins()` pinning both domains; `vocabulary.snapshot()` reading the held concept list; `state` keys `concepts_address`, `concepts_ref`.
- Consumes: Tasks 3, 5, 9.

- [ ] **Step 1: Write the driver tests**

Append to `python/tests/test_reproduction_driver.py`:

```python
def test_the_row_plan_maps_a_predicate_and_kind_pair(tmp_path, monkeypatch):
    from reproduction import vocabulary

    monkeypatch.setattr(vocabulary.state, "load", lambda: {"concepts_address": "dataset:sha256:" + "c" * 64})
    plan = vocabulary.plan()
    assert plan["operators"][("affects", "concept", "protein")] == "mm30/affects-concept-molecular-entity"
    assert plan["operators"][("affects", "protein", "protein")] == "biology/affects-molecular-entity-molecular-entity"
    assert plan["sorts"] == {"concept": "mm30/concept", "protein": "biology/molecular-entity"}
    assert len(plan["operators"]) == 17


def test_the_mm30_contract_binds_concept_to_the_held_list(monkeypatch):
    from reproduction import vocabulary

    monkeypatch.setattr(vocabulary.state, "load", lambda: {"concepts_address": "dataset:sha256:" + "c" * 64})
    vocabulary._document.cache_clear()
    contract = vocabulary.contract()
    assert contract.sorts["concept"].vocabulary.dataset_identity == "sha256:" + "c" * 64
    assert contract.operators["affects-concept-molecular-entity"].arg_sorts == ("concept", "biology/molecular-entity")


def test_concept_lines_are_canonical_sorted_and_terminated(tmp_path):
    from reproduction.concepts import concept_lines

    root = tmp_path / "entities" / "concepts"
    root.mkdir(parents=True)
    (root / "b.md").write_text("---\nid: concept:b-thing\nkind: concept\n---\n")
    (root / "a.md").write_text("---\nid: concept:a-thing\nkind: concept\n---\n")
    assert concept_lines(tmp_path) == b"concept:a-thing\nconcept:b-thing\n"


def test_a_non_canonical_concept_id_refuses(tmp_path):
    from reproduction.concepts import concept_lines

    root = tmp_path / "entities" / "concepts"
    root.mkdir(parents=True)
    # NFD, not NFC: `e` + combining acute. The predicate is about normalization,
    # not about spaces or case (`not_a_canonical_identifier` in identifiers.py).
    (root / "x.md").write_text("---\nid: 'concept:café-thing'\nkind: concept\n---\n", encoding="utf-8")
    with pytest.raises(ValueError, match="canonical"):
        concept_lines(tmp_path)
```

- [ ] **Step 2: Run to verify they fail**

Run: `cd python && uv run --frozen pytest tests/test_reproduction_driver.py -q`
Expected: 4 failures (`mm30.yaml` missing; no `reproduction.concepts`).

- [ ] **Step 3: Write `mm30.yaml`**

Create `python/tools/reproduction/mm30.yaml` (the `{{CONCEPTS}}` token is replaced by `vocabulary.py` with the held list's address from `state.json`; the document is refused unless that state exists):

```yaml
# mm30's corpus-local claim vocabulary (biology pack design §3.3, §3.5).
#
# What is one corpus's: the `concept` sort, bound to mm30's own concept
# list held as a dataset by content identity, and every operator with a
# concept slot — fourteen of the seventeen predicate-by-shape pairs the
# corpus recorded. The six mixed shapes name `biology/molecular-entity`
# under the cross-contract slot rule (§4). The three protein→protein
# shapes live in the biology pack.
#
# Names follow one rule: <predicate>-<subject sort>-<object sort>. Layers
# and sign-aptness per predicate are the typing exercise's, read off the
# corpus, not chosen (`tools/vocabularies/mm30-modal-sorted.yaml`).
contract:
  contract: mm30
  version: 1
  lineage: genesis

  sorts:
    concept:
      vocabulary: dataset:{{CONCEPTS}}

  dimensions: {}

  operators:
    affects-concept-concept:
      { arity: 2, arg_sorts: [concept, concept], sign_apt: true, layers: [causal, structural, statistical], dimensions: [] }
    affects-concept-molecular-entity:
      { arity: 2, arg_sorts: [concept, biology/molecular-entity], sign_apt: true, layers: [causal, structural, statistical], dimensions: [] }
    affects-molecular-entity-concept:
      { arity: 2, arg_sorts: [biology/molecular-entity, concept], sign_apt: true, layers: [causal, structural, statistical], dimensions: [] }
    associates-with-concept-concept:
      { arity: 2, arg_sorts: [concept, concept], sign_apt: true, layers: [statistical, causal], dimensions: [] }
    associates-with-molecular-entity-concept:
      { arity: 2, arg_sorts: [biology/molecular-entity, concept], sign_apt: true, layers: [statistical, causal], dimensions: [] }
    binds-concept-concept:
      { arity: 2, arg_sorts: [concept, concept], sign_apt: false, layers: [causal], dimensions: [] }
    induces-state-concept-concept:
      { arity: 2, arg_sorts: [concept, concept], sign_apt: false, layers: [causal], dimensions: [] }
    is-proxy-for-concept-concept:
      { arity: 2, arg_sorts: [concept, concept], sign_apt: false, layers: [causal, structural], dimensions: [] }
    part-of-molecular-entity-concept:
      { arity: 2, arg_sorts: [biology/molecular-entity, concept], sign_apt: false, layers: [structural], dimensions: [] }
    part-of-concept-concept:
      { arity: 2, arg_sorts: [concept, concept], sign_apt: false, layers: [structural], dimensions: [] }
    regulates-concept-molecular-entity:
      { arity: 2, arg_sorts: [concept, biology/molecular-entity], sign_apt: true, layers: [causal], dimensions: [] }
    regulates-concept-concept:
      { arity: 2, arg_sorts: [concept, concept], sign_apt: true, layers: [causal], dimensions: [] }
    regulates-molecular-entity-concept:
      { arity: 2, arg_sorts: [biology/molecular-entity, concept], sign_apt: true, layers: [causal], dimensions: [] }
    subtype-of-concept-concept:
      { arity: 2, arg_sorts: [concept, concept], sign_apt: false, layers: [structural], dimensions: [] }

plan:
  # One row per predicate-by-kind-pair the corpus recorded (design §3.1);
  # a pair with no row is refused by the tools, never typed under a nearest row.
  operators:
    - { predicate: affects,         subject: concept, object: concept, operator: affects-concept-concept }
    - { predicate: affects,         subject: concept, object: protein, operator: affects-concept-molecular-entity }
    - { predicate: affects,         subject: protein, object: concept, operator: affects-molecular-entity-concept }
    - { predicate: affects,         subject: protein, object: protein, operator: biology/affects-molecular-entity-molecular-entity }
    - { predicate: associates_with, subject: concept, object: concept, operator: associates-with-concept-concept }
    - { predicate: associates_with, subject: protein, object: protein, operator: biology/associates-with-molecular-entity-molecular-entity }
    - { predicate: associates_with, subject: protein, object: concept, operator: associates-with-molecular-entity-concept }
    - { predicate: binds,           subject: concept, object: concept, operator: binds-concept-concept }
    - { predicate: induces_state,   subject: concept, object: concept, operator: induces-state-concept-concept }
    - { predicate: is_proxy_for,    subject: concept, object: concept, operator: is-proxy-for-concept-concept }
    - { predicate: part_of,         subject: protein, object: concept, operator: part-of-molecular-entity-concept }
    - { predicate: part_of,         subject: concept, object: concept, operator: part-of-concept-concept }
    - { predicate: regulates,       subject: concept, object: protein, operator: regulates-concept-molecular-entity }
    - { predicate: regulates,       subject: concept, object: concept, operator: regulates-concept-concept }
    - { predicate: regulates,       subject: protein, object: protein, operator: biology/regulates-molecular-entity-molecular-entity }
    - { predicate: regulates,       subject: protein, object: concept, operator: regulates-molecular-entity-concept }
    - { predicate: subtype_of,      subject: concept, object: concept, operator: subtype-of-concept-concept }
  sorts:
    concept: concept
    protein: biology/molecular-entity
  layers:
    causal_effect: causal
    structural_claim: structural
    empirical_regularity: statistical
  polarities:
    positive: positive
    negative: negative
    unsigned: unsigned
    not_applicable: null
```

- [ ] **Step 4: Rewrite `vocabulary.py`**

Replace `python/tools/reproduction/vocabulary.py` with:

```python
"""Task 3: the profile the reproduction types under — the shipped base, the
biology pack and mm30's corpus-local contract (biology pack design §6.2).

`mm30.yaml` binds its `concept` sort to the held concept list (step 1b,
`concepts.py`), whose address lives in `state.json`; the document is refused
until that step has run. The modal-sorted exercise plan stays exposed for
the step-2 measurement it has always served.
"""

from __future__ import annotations

from functools import cache
from pathlib import Path

import yaml

from beliefs.consulted import CorpusPins
from beliefs.contract.domain import DomainContract, VocabularyBinding, parse_domain_contract
from beliefs.profile import ProfileSpec, compile_profile, shipped_base_contract, shipped_domain_contract
from beliefs.resolution import ResolutionSnapshot, build_snapshot
from reproduction import paths, state

DOCUMENT = Path(__file__).with_name("mm30.yaml")
MODAL_SORTED = paths.REPO / "python" / "tools" / "vocabularies" / "mm30-modal-sorted.yaml"
CONCEPTS_TOKEN = "{{CONCEPTS}}"


@cache
def _document(path: Path = DOCUMENT) -> dict:
    text = path.read_text()
    if CONCEPTS_TOKEN in text:
        st = state.load()
        if "concepts_address" not in st:
            raise RuntimeError("mm30.yaml binds `concept` to the held concept list; run concepts.py (step 1b) first")
        text = text.replace(CONCEPTS_TOKEN, st["concepts_address"].removeprefix("dataset:"))
    return yaml.safe_load(text)


@cache
def base():
    return shipped_base_contract()


@cache
def biology() -> DomainContract:
    return shipped_domain_contract("biology")


@cache
def contract(path: Path = DOCUMENT) -> DomainContract:
    return parse_domain_contract(_document(path)["contract"], source=f"{path}: contract", base=base(), predecessor=None)


@cache
def profile(path: Path = DOCUMENT) -> ProfileSpec:
    if path == DOCUMENT:
        return compile_profile(base(), [biology(), contract(path)])
    return compile_profile(base(), [contract(path)])


def _term(domain: DomainContract, name: str) -> str:
    return name if "/" in name else domain.term(name)


def plan(path: Path = DOCUMENT) -> dict:
    """Rows keyed by (predicate, subject kind, object kind) → operator term; a
    namespaced operator or sort passes through, a local one is namespaced once."""
    raw = _document(path)["plan"]
    domain = contract(path)
    operators = raw.get("operators") or {}
    if isinstance(operators, dict):  # the exercise plans' predicate-only shape
        rows = {(predicate, None, None): _term(domain, name) for predicate, name in operators.items()}
    else:
        rows = {(row["predicate"], row["subject"], row["object"]): _term(domain, row["operator"]) for row in operators}
    return {
        "operators": rows,
        "sorts": {k: _term(domain, v) for k, v in (raw.get("sorts") or {}).items()},
        "layers": dict(raw.get("layers") or {}),
        "polarities": dict(raw.get("polarities") or {}),
    }


def operator_for(plan_: dict, predicate: str, subject_kind: str, object_kind: str) -> str:
    rows = plan_["operators"]
    if (predicate, subject_kind, object_kind) in rows:
        return rows[(predicate, subject_kind, object_kind)]
    if (predicate, None, None) in rows:
        return rows[(predicate, None, None)]
    raise KeyError(f"no plan row for {predicate} {subject_kind}→{object_kind}; a shape with no row is refused, never nearest-typed")


def pins() -> CorpusPins:
    p = profile()
    return CorpusPins(
        science_contract=f"science:{p.base_contract_identity}",
        domains={ns: f"{ns}:{identity}" for ns, identity in p.activated_contracts.items()},
    )


def concept_binding() -> VocabularyBinding:
    return contract().sorts["concept"].vocabulary


def snapshot() -> ResolutionSnapshot:
    """The held concept list is read back and supplied as readable; HGNC is
    not held and stays `not-consulted` (design §6.3, §9 item 2).

    The copy beside `state.json` is an instrument, not the vocabulary: before
    a single member is asserted, its bytes are hashed and compared to the
    resource digest the **minted dataset record** declares — read from the
    corpus, not from state — and a mismatch refuses. Editing the copy cannot
    change membership while the contract names the original."""
    from hashlib import sha256

    from beliefs import stored
    from reproduction import world

    st = state.load()
    content = Path(st["concepts_file"]).read_bytes()
    declared = stored.dataset_declaration(world.open_writer().read_view.get(st["concepts_ref"]))
    (resource,) = declared.resources
    if "sha256:" + sha256(content).hexdigest() != resource.digest:
        raise RuntimeError(
            f"{st['concepts_file']} does not hash to the held vocabulary's declared digest {resource.digest}; "
            "membership is measured against the dataset the contract binds, never against an edited copy"
        )
    return build_snapshot(readable={concept_binding(): content.decode("utf-8").splitlines()})
```

- [ ] **Step 5: Write `concepts.py` (step 1b)**

Create `python/tools/reproduction/concepts.py`:

```python
"""Step 1b: hold mm30's concept vocabulary as a dataset (biology pack design §6.3).

The 285 canonical concept identifiers under the predecessor's
`entities/concepts/` become one UTF-8 text resource, one identifier per
line, sorted by code point, newline-terminated; it is held in the store
under its digest and minted as a dataset record whose content address the
`mm30` contract's `concept` sort binds. The kernel defines no vocabulary
file format; this line format is the tool's, and the record says so.
"""

from __future__ import annotations

import sys
from hashlib import sha256
from pathlib import Path

import yaml

from beliefs import stored
from beliefs.dataset import DatasetDeclaration, ResourceDeclaration, dataset_address
from beliefs.holdings.boundary import ActContext, write
from beliefs.holdings.records import StoreLocator
from beliefs.identifiers import not_a_canonical_identifier
from beliefs.root import holdings_seam
from reproduction import findings, paths, state, world
from reproduction.authority import AUTHORITY

OBSERVER = "mm30-reproduction-observer"
INSTRUMENT = "mm30-reproduction/concepts.v1"
RESOURCE = "mm30-concepts.txt"


def concept_lines(predecessor: Path) -> bytes:
    ids: list[str] = []
    for path in sorted((predecessor / "entities" / "concepts").glob("*.md")):
        text = path.read_text(errors="replace")
        block = text.split("---", 2)
        front = yaml.safe_load(block[1]) if len(block) >= 3 else None
        if not isinstance(front, dict) or front.get("kind") != "concept" or not isinstance(front.get("id"), str):
            raise ValueError(f"{path}: not a concept record with an id")
        problem = not_a_canonical_identifier(front["id"])
        if problem is not None:
            raise ValueError(f"{path}: {front['id']!r} is not a canonical identifier: {problem}")
        ids.append(front["id"])
    return "".join(identifier + "\n" for identifier in sorted(ids)).encode("utf-8")


def main() -> int:
    """Order matters, and it is the address that makes it work. The manifest
    pins `mm30`, whose `concept` sort binds the concept list's address; the
    address is a pure function of the resource digest, so it is known before
    any write. Compute it, save it, adopt the manifest under the full pins,
    then hold the bytes and mint the record under the full profile."""
    content = concept_lines(paths.PREDECESSOR)
    digest = "sha256:" + sha256(content).hexdigest()
    address = dataset_address(DatasetDeclaration(resources=(ResourceDeclaration(name=RESOURCE, digest=digest),)))
    assert address is not None
    # The snapshot reads the bytes back without the store's read seam; a copy
    # beside state.json is the reproduction's own instrument, stated as such.
    held_copy = paths.WORK / RESOURCE
    held_copy.write_bytes(content)
    state.save(concepts_address=address, concepts_file=str(held_copy), concepts_count=content.count(b"\n"))
    from reproduction import vocabulary  # after the state it needs exists

    vocabulary._document.cache_clear()
    world.adopt()  # the manifest, pinned to base + biology + mm30
    st = state.load()
    ctx = ActContext(paths.CORPUS_ROOT, paths.STORE_ROOT, OBSERVER, INSTRUMENT, AUTHORITY, holdings_seam(), profile=vocabulary.profile())
    write(ctx, StoreLocator(st["store_id"], f"mm30-concepts/{RESOURCE}"), content, expected=digest)
    node = stored.dataset_node(
        address.removeprefix("dataset:"), title="mm30 concept vocabulary", resources=[{"name": RESOURCE, "digest": digest}]
    )
    minted = world.open_writer().add(node)
    state.save(concepts_ref=minted.id)
    findings.record(1, "closed", f"held {content.count(b'\\n')} concept identifiers as {digest}; dataset {minted.id}; the line format is the tool's (design §6.3)")
    print(f"held {content.count(b'\\n')} concepts as {digest}; dataset {minted.id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

In `world.py`, split step 1 so adoption follows step 1b: `main` keeps `state.save(world_id=...)`, `init_world_root`, `init_corpus_root` and `init_store_root`, saves `store_id`, and returns; the adoption moves into

```python
def adopt() -> None:
    manifest = open_writer().adopt_manifest(profile=pins())
    open_world().admit(paths.CORPUS_ROOT, provenance=Fresh())
    state.save(corpus_id=manifest.corpus_id)
    print(f"corpus {manifest.corpus_id} status {open_world().status(manifest.corpus_id)}")
```

`open_writer()` before adoption is what `adopt_manifest` is called on today, so the call order inside `adopt()` is step 1's existing order. `hold.py`'s `ActContext` already passes `profile=profile()`; `concepts.py` passes the same.

- [ ] **Step 6: Update `type_target.py`, `hold.py`, `belief.py`**

`type_target.py`: resolve the operator by shape and keep the modal measurement:

```python
def typed(target: dict, profile, plan: dict):
    subject_kind = target["subject"].partition(":")[0]
    object_kind = target["object"].partition(":")[0]
    return build_claim(
        profile,
        operator=vocabulary.operator_for(plan, target["predicate"], subject_kind, object_kind),
        args=(referent(target["subject"], plan), referent(target["object"], plan)),
        layer=plan["layers"][target["claim_layer"]],
        polarity=plan["polarities"][target["polarity"]],
    )
```

After the mint, record the two measured resolutions:

```python
    snapshot = vocabulary.snapshot()
    concept = snapshot.resolve(vocabulary.concept_binding(), target["subject"])  # a TermOutcome
    findings.record(2, "closed", f"slot 0 {target['subject']} resolved {concept.value} against the held concept list; slot 1 is biology/molecular-entity, not-consulted (design §6.4)")
```

`ResolutionSnapshot.resolve(binding, term)` returns the `TermOutcome` enum; `.value` is the outcome's wire name (`member`).

`hold.py`: stamp the facet on the dataset record:

```python
    node = stored.dataset_node(
        address.removeprefix("dataset:"),
        title=title,
        resources=[{"name": name, "digest": digest}],
        empirical_observation={"locator": f"accession:{accession}", "attested_by": AUTHORITY.actor},
        domain_facets={"biology/gene-axis": {"axis": "rows", "namespace": "HGNC"}},
    )
```

and record `findings.record(3, "closed", "biology/gene-axis {axis: rows, namespace: HGNC} validated at write by cut 20's seam")`.

`belief.py`: before `evaluate_here`, the pins negative (design §6.5):

```python
def pins_negative(view: ReadView) -> None:
    """Design §6.5: with `biology` unpinned, the walk refuses naming it."""
    from beliefs.consulted import consulted_contracts
    from beliefs.errors import ContractDisagreement

    st = state.load()
    full = world.open_writer().manifest_pins()
    without = CorpusPins(science_contract=full.science_contract, domains={"mm30": full.domains["mm30"]})
    inputs = gather(view, st["proposition_ref"], context=context(view), profile=vocabulary.profile(), resolution=vocabulary.snapshot(), binding=BINDING)
    try:
        consulted_contracts(
            claims={st["proposition_ref"]: inputs.claim} if inputs.claim is not None else {},
            profile=vocabulary.profile(),
            node_corpus=context(view).node_corpus,
            pins={st["corpus_id"]: without},
            closure_nodes=tuple(a.identity() for a in inputs.assessments),
        )
    except ContractDisagreement as refused:
        findings.record(8, "closed", f"biology unpinned: {refused}")
        return
    findings.record(8, "defect", "the walk consulted biology through slot 1's sort without a pin for it")
```

Call it from `main` before the evaluation, importing `CorpusPins`. After `evaluate_here`, record the consulted set and the `observed_facets` rows from `gather(...)` in `findings` (step 8, class `closed`).

- [ ] **Step 7: Row-shaped plans in `type_corpus_claims.py`**

In `run`, accept both plan shapes:

```python
    raw_operators = plan.get("operators") or {}
    if isinstance(raw_operators, dict):
        rows = {(predicate, None, None): _term(contract, name) for predicate, name in raw_operators.items()}
    else:
        rows = {(r["predicate"], r["subject"], r["object"]): _term(contract, r["operator"]) for r in raw_operators}
    resolved = {"operators": rows, "sorts": {k: _term(contract, v) for k, v in (plan.get("sorts") or {}).items()}, ...}
```

with `def _term(contract, name): return name if "/" in name else contract.term(name)`, and in `type_record` replace `plan["operators"].get(predicate)` with a lookup by `(predicate, sort_of(subject), sort_of(obj))` falling back to `(predicate, None, None)`, reporting `unmapped-shape` with `f"{predicate} {sort_of(subject)}→{sort_of(obj)}"` when neither exists. `run` must compile **every** contract the plan document names: add an optional top-level `also:` list in the plan document (`also: [biology]`) that `run` resolves through `shipped_domain_contract`, so the `mm30.yaml` file can be typed over the corpus with `uv run python tools/type_corpus_claims.py tools/reproduction/mm30.yaml <corpus>` after `concepts.py` has produced the state the token needs — the tool reads the token the same way `vocabulary._document` does (import and reuse it).

- [ ] **Step 8: Run the driver tests and the gates**

Run: `cd python && uv run --frozen pytest tests/test_reproduction_driver.py -q && uv run --frozen ruff check . && uv run --frozen pyright`
Expected: all pass, 0 errors.

- [ ] **Step 9: Commit**

```bash
git add python/tools/reproduction python/tools/type_corpus_claims.py python/tests/test_reproduction_driver.py
git commit -m "feat(reproduction): mm30's corpus-local contract over its held concept vocabulary, shape-keyed plan rows"
```

---

### Task 11: Cut 22's guard, acceptance module and runner

**Files:**
- Create: `python/tests/acceptance/n2_arms_cut22.py`
- Create: `python/tests/acceptance/test_n2_cut22.py`
- Create: `python/tests/acceptance/test_biology_acceptance.py`
- Create: `python/tools/cut22_acceptance.py`
- Modify: `python/tests/frozen_guards.py` (register the new guard as live, following how `test_n2_cut21.py` was registered)

**Interfaces:**
- Consumes: every check name in Tasks 2–10; `CUT22_FREEZE_COMMIT` from Task 1 step 5.

- [ ] **Step 1: Write the arm table**

Create `python/tests/acceptance/n2_arms_cut22.py`:

```python
"""Cut 22's nine frozen declaration units and their source sabotages
(docs/designs/2026-09-08-conformance-cut-22.md §3, §5 item 4), one arm per
frozen sabotage."""

from __future__ import annotations

from n2_arms import Arm, Sabotage

_DOMAIN, _PROFILE, _CONSULTED, _READ, _EVAL, _BELIEF, _CLOSURE = (
    "contract/domain.py", "profile.py", "consulted.py", "facet_read.py", "evaluation.py", "belief.py", "closure.py",
)
_TDC, _TP, _TC, _TFR, _TDF, _TSB = (
    "test_domain_contract.py", "test_profile.py", "test_consulted.py", "test_facet_read.py",
    "test_domain_facet_read.py", "test_shipped_biology.py",
)

DECLARATION_UNITS = ("B1", "B2", "B3", "B4", "B5", "B6", "B7", "D6", "M8")
CO_CITED: tuple[str, ...] = ()


def unit_of(row: str) -> str:
    return row.rstrip("abcdefghijklmnopqrstuvwxyz")


CUT22_ARMS = (
    Arm("B1a", "drop the own-namespace refusal",
        Sabotage(_DOMAIN, "    if foreign == namespace:\n", "    if False and foreign == namespace:\n"),
        (f"{_TDC}::TestSortReferences::test_own_namespace_is_refused",)),
    Arm("B1b", "namespace a namespaced name again",
        Sabotage(_PROFILE, '    term = name if "/" in name else contract.term(name)\n', "    term = contract.term(name)\n"),
        (f"{_TP}::TestCrossContractSlots::test_a_foreign_sort_resolves_when_its_contract_is_compiled",)),
    Arm("B1c", "drop the unresolved-reference refusal",
        Sabotage(_PROFILE, "    if term not in sorts:\n        namespace = term.partition(\"/\")[0]\n", "    if False:\n        namespace = term.partition(\"/\")[0]\n"),
        (f"{_TP}::TestCrossContractSlots::test_an_unresolved_reference_refuses_naming_the_namespace",)),
    Arm("B2a", "add the operator's contract alone",
        Sabotage(_CONSULTED, "        for sort in operator.arg_sorts:\n            read.add(profile.sorts[sort].contract)\n", "        for sort in ():\n            read.add(profile.sorts[sort].contract)\n"),
        (f"{_TC}::TestSlotSorts::test_a_claim_reaches_its_slot_sorts_contracts",)),
    # The crossing operator declares no dimension, so with argument sorts
    # dropped `testing` is not reached by any other route (§5 item 4).
    Arm("B2b", "stop collecting facet namespaces",
        Sabotage(_CONSULTED, "            if separator:\n                read.add(namespace)\n", "            if separator:\n                pass\n"),
        (f"{_TDF}::test_isolated_case_biology_enters_through_the_ledger_alone",)),
    Arm("B3a", "a field-wise constructor",
        Sabotage(_READ, "        raise MalformedRecord(\n            \"FacetRead is minted by the reader", "        return None  # sabotage: a field-wise constructor\n        raise MalformedRecord(\n            \"FacetRead is minted by the reader"),
        (f"{_TFR}::test_facet_read_has_no_field_wise_constructor",)),
    Arm("B3b", "mint over anything shaped like a view",
        Sabotage(_READ, "    if not isinstance(view, ReadView):\n", "    if False:\n"),
        (f"{_TFR}::test_the_reader_refuses_anything_but_a_corpus_view",)),
    Arm("B4a", "skip re-validation",
        Sabotage(_READ, "        validate_payload(facet, payload, where=node.id)\n", "        pass\n"),
        (f"{_TFR}::test_a_malformed_payload_refuses_the_derivation",)),
    Arm("B4b", "fetch an unheld observed dataset",
        Sabotage(_EVAL, "            if not view.holds(target):\n                continue\n", "            if not view.holds(target):\n                raise RuntimeError(f\"{target} is observed but not held\")\n"),
        (f"{_TDF}::test_an_absent_observed_dataset_is_absent_from_gather",)),
    Arm("B5a", "empty the observed_facets member",
        Sabotage(_CLOSURE, '        "observed_facets": [row.projection() for row in observed_facets],\n', '        "observed_facets": [],\n'),
        (f"{_TDF}::test_a_payload_byte_change_moves_the_digest",)),
    # B5b mutates `evaluate`, so its check must derive a belief: the isolated
    # bump test goes through `evaluate_over` → `evaluate`, whose walk then
    # lacks biology and whose digest no longer moves under the biology bump.
    Arm("B5b", "take the ledger from nowhere",
        Sabotage(_BELIEF, "    for row in records.observed_facets:\n        ledger.setdefault(row.address, []).append(row.key)\n", "    for row in ():\n        ledger.setdefault(row.address, []).append(row.key)\n"),
        (f"{_TDF}::test_isolated_case_a_biology_bump_moves_the_digest", f"{_TDF}::test_gather_and_evaluate_agree_on_the_consulted_set")),
    Arm("B6a", "read the shipped pack from the base's path",
        Sabotage(_PROFILE, '    resource = resources.files("beliefs").joinpath(f"domains/{namespace}/DOMAIN.yaml")\n', '    resource = resources.files("beliefs").joinpath("contracts/science/CONTRACT.yaml")\n'),
        (f"{_TSB}::test_the_shipped_pack_declares_the_floor",)),
    Arm("B7a", "drop the science agreement",
        Sabotage(_CONSULTED, '    if base_identity != "science:" + profile.base_contract_identity:\n', "    if False:\n"),
        (f"{_TC}::TestPinAgreement::test_the_base_pin_must_agree_with_the_profile",)),
    Arm("B7b", "drop the domain agreement",
        Sabotage(_CONSULTED, '        if identity != f"{namespace}:{expected}":\n', "        if False:\n"),
        (f"{_TC}::TestPinAgreement::test_a_consulted_namespace_pinned_to_another_identity_refuses",)),
    Arm("D6a", "drop observed addresses from the closure nodes",
        Sabotage(_BELIEF, "    closure_nodes = tuple(a.identity() for a in matched) + observed\n", "    closure_nodes = tuple(a.identity() for a in matched)\n"),
        (f"{_TDF}::test_isolated_case_a_biology_bump_moves_the_digest",)),
    # M8a shares B2a's site on purpose: the row promises movement *through a
    # foreign sort's contract*, so the sabotage that severs that route is the
    # one whose absence this check must feel.
    Arm("M8a", "drop the sort-contract collection under a belief",
        Sabotage(_CONSULTED, "        for sort in operator.arg_sorts:\n            read.add(profile.sorts[sort].contract)\n", "        for sort in ():\n            read.add(profile.sorts[sort].contract)\n"),
        (f"{_TDF}::test_m8_an_editorial_bump_of_a_foreign_sorts_contract_leaves_claim_identity_and_moves_the_digest",)),
)
```

B4b's `after` raises `RuntimeError` on purpose: `evaluation.py` imports no `MalformedRecord`, and an arm whose `after` fails to import scores `uncollected`, not `sound`.

- [ ] **Step 2: Write the audit module**

Create `python/tests/acceptance/test_n2_cut22.py` by copying `test_n2_cut21.py` and changing: the docstring to cut 22; the imports to add `from n2_arms_cut21 import CUT21_ARMS` and `from n2_arms_cut22 import CO_CITED, CUT22_ARMS, DECLARATION_UNITS, unit_of`; `FROZEN_CUT` to `docs/designs/2026-09-08-conformance-cut-22.md`; `CUT22_FREEZE_COMMIT` to Task 1 step 5's short SHA; `CUT22_FROZEN_SHA256` to `sha256` of `git show <commit>:docs/designs/2026-09-08-conformance-cut-22.md`; `FROZEN_PRIOR_CUT_FILES` to cut 21's table plus `"python/tests/acceptance/n2_arms_cut21.py": "<the commit at which cut 21's table last moved, from git log -1 --format=%h -- python/tests/acceptance/n2_arms_cut21.py>"`; `PRIOR_ARMS` to include `*CUT21_ARMS`; the inventory test to:

```python
def test_the_inventory_is_exactly_the_nine_frozen_units() -> None:
    assert DECLARATION_UNITS == ("B1", "B2", "B3", "B4", "B5", "B6", "B7", "D6", "M8")
    assert {unit_of(arm.row) for arm in CUT22_ARMS} == set(DECLARATION_UNITS)
    assert len(CUT22_ARMS) == 16
```

and the freeze assertions to `assert "**9 declaration units**" in current`, `assert "Nine guarantee rows are read, **9 full/closed** (B1–B7, D6, M8), 1 partial" in current`, `assert '("cut21_acceptance.py",)' in current`. `_frozen_body` slices from `## 2. The boundary` to the first `\n## 8.` or end of file, as cut 21's does.

- [ ] **Step 3: Write the acceptance module**

Create `python/tests/acceptance/test_biology_acceptance.py`:

```python
"""Cut 22's durable arm: the dogfood shape of D6's facet arm through
`CorpusWriter.add` on the certified engine and volume
(`docs/designs/2026-09-08-conformance-cut-22.md` §3, D6), plus B6's
TypeScript half run as vitest."""

from __future__ import annotations

import subprocess
from dataclasses import replace
from pathlib import Path

import pytest
from authority import FULL
from domain_facet_fixtures import PROPOSITION_REF, kwargs_for, profile_with, seed
from profiles import pins_for
from test_session_acceptance import adopted

from beliefs.belief import Belief, Refused
from beliefs.errors import ContractMismatch
from beliefs.evaluation import evaluate_over, gather
from beliefs.root import open_corpus

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_d6_the_facet_read_is_consulted_over_bytes_the_engine_committed(work_directory):
    """The dogfood shape, durable: the facet-bearing dataset goes through
    `CorpusWriter.add` (cut 20's seam validates the payload), belief derives
    with `biology` consulted, and both pin-agreement seams refuse a bumped
    profile — the writer's own recheck at open, and B7 at the walk. The digest
    movement under a bump is the portable arm's (Task 7)."""
    profile = profile_with()
    root = adopted(work_directory, "corpus", pins=pins_for(profile), profile=profile)
    writer = open_corpus(root, authority=FULL, profile=profile)
    view = seed(writer, axis="rows")
    result = evaluate_over(view, PROPOSITION_REF, **kwargs_for(view, profile))
    assert isinstance(result, Belief)
    reopened = open_corpus(root, authority=FULL, profile=profile).read_view
    gathered = {k: v for k, v in kwargs_for(reopened, profile).items() if k != "availability"}
    assert "biology" in dict(tuple(pair) for pair in gather(reopened, PROPOSITION_REF, **gathered).consulted)
    bumped = profile_with("fixture, bumped")
    with pytest.raises(ContractMismatch):
        open_corpus(root, authority=FULL, profile=bumped)
    # B7 at the walk: the bumped profile validates, but the pins stay the
    # manifest's — `kwargs_for(…, bumped)` would build agreeing pins and B7
    # would rightly accept that pair, so the original pins are put back.
    original_pins = kwargs_for(reopened, profile)["context"].pins
    mismatched = kwargs_for(reopened, bumped)
    mismatched["context"] = replace(mismatched["context"], pins=original_pins)
    refused = evaluate_over(reopened, PROPOSITION_REF, **mismatched)
    assert isinstance(refused, Refused) and refused.reason.startswith("profile-pin-mismatch: biology")


def test_b6_typescript_refuses_what_python_refuses():
    completed = subprocess.run(
        ["npx", "vitest", "run", "tests/contract-scope.test.ts"], cwd=REPO_ROOT / "ts", check=False, capture_output=True, text=True
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
```

`adopted(work_directory, name, pins=PINS, profile=WITH_BIOLOGY)` already takes both keywords; the manifest it writes pins exactly the profile the test opens under, which B7 and the writer's own recheck both require.

- [ ] **Step 4: Write the runner**

Create `python/tools/cut22_acceptance.py` by copying `cut21_acceptance.py` and changing every `21` to `22` and `20` to `21` in names and messages, `PHASE_MODULES = ("test_biology_acceptance.py", "test_n2_cut22.py")`, `declared_accounting` to import `n2_arms_cut22`, and the `SCIENCE_CUT{n}_ROOT` range to `range(4, 23)`.

- [ ] **Step 5: Register the guard**

In `python/tests/frozen_guards.py`, add the new module where cut 21's is listed (the live inventory the newest runner defines). Run:

```bash
cd python && uv run --frozen pytest tests/test_frozen_guards.py -q
```

Expected: pass (every guard live or declared; every live pin holds).

- [ ] **Step 6: Run the audit portably first, then the certified runner**

```bash
cd python && uv run --frozen pytest tests/acceptance/test_n2_cut22.py -q -x
```

Expected: every arm `sound`; the freeze pin test passes. Then:

```bash
cd python && uv run --frozen python tools/cut22_acceptance.py
```

Expected: exit 0 and the printed `declared arms: 16 (= 9 declaration units; 9 guarantee rows)`. A `CapabilityUnavailable` refusal means the tuple needs recertification (`atoms-recertify.timer`), not a regression; wait for it and re-run.

- [ ] **Step 7: Commit**

```bash
git add python/tests/acceptance/n2_arms_cut22.py python/tests/acceptance/test_n2_cut22.py python/tests/acceptance/test_biology_acceptance.py python/tools/cut22_acceptance.py python/tests/frozen_guards.py python/tests/test_session_acceptance.py
git commit -m "test(cut22): guard, acceptance module and runner for the biology pack cut"
```

---

### Task 12: Re-run the reproduction and amend its record

**Files:**
- Modify: `docs/designs/2026-09-05-mm30-reproduction.md` (§5 question 1, §6, §3 row annotations)
- Create: the run's findings under `.work/reproduction/mm30-slice2/` (untracked; its `findings.jsonl` and `state.json` are copied into `docs/plans/2026-09-08-mm30-reproduction-slice2-run/` as the durable ledger)

- [ ] **Step 1: Run the driver over a fresh work directory**

```bash
cd python
# Beside the main checkout, on the repository's volume: the first worktree
# `git worktree list` prints is the main checkout (paths.py's CHECKOUT rule).
export SCIENCE_MM30_ROOT="$(git worktree list --porcelain | head -1 | cut -d' ' -f2)/.work/reproduction/mm30-slice2"
uv run --frozen python tools/reproduction/world.py
uv run --frozen python tools/reproduction/concepts.py
uv run --frozen python tools/reproduction/select_target.py   # if the target file is not reused; otherwise copy target.yaml from the first run
uv run --frozen python tools/reproduction/type_target.py
uv run --frozen python tools/reproduction/hold.py
uv run --frozen python tools/reproduction/spec.py
uv run --frozen python tools/reproduction/run.py
uv run --frozen python tools/reproduction/belief.py
uv run --frozen python tools/reproduction/close.py
uv run --frozen python tools/reproduction/rederive.py
uv run --frozen python tools/type_corpus_claims.py tools/reproduction/mm30.yaml "$HOME/d/cancer/cancer-types/multiple-myeloma" > "$SCIENCE_MM30_ROOT/typing-all-307.md"
```

Read `paths.py` for the exact `SCIENCE_MM30_ROOT` semantics; the directory must be on the repository's volume, not `/tmp`. Every refusal is a finding filed through the owning lane; do not work around one.

- [ ] **Step 2: Copy the ledger into the tree**

```bash
mkdir -p docs/plans/2026-09-08-mm30-reproduction-slice2-run
cp "$SCIENCE_MM30_ROOT"/findings.jsonl "$SCIENCE_MM30_ROOT"/state.json "$SCIENCE_MM30_ROOT"/typing-all-307.md docs/plans/2026-09-08-mm30-reproduction-slice2-run/
```

- [ ] **Step 3: Amend the record**

In `docs/designs/2026-09-05-mm30-reproduction.md`:

- §5 question 1: append a dated paragraph beginning `**Measured 2026-09-08 (biology pack design §6.4).**` stating the operator the target typed under, slot 0's `member` outcome against the held concept list of N identifiers, slot 1's `not-consulted`, the new claim identity and why it differs, and the full-corpus typing yield from `typing-all-307.md` (typed count, and each refusal class with its count).
- §6: one row per finding in `findings.jsonl` from this run, in the table's existing columns.
- §3 row 10a: a note that the re-derive's digest differs from the 2026-09-05 record because the closure gained `observed_facets` (design §5.4), with both digests quoted.
- The status header: `Re-run 2026-09-08 as biology slice 2's measurement; see §5 question 1 and §6.`

- [ ] **Step 4: Commit**

```bash
git add docs/designs/2026-09-05-mm30-reproduction.md docs/plans/2026-09-08-mm30-reproduction-slice2-run
git commit -m "docs(reproduction): re-run mm30 under the biology pack and mm30 contract; record the measurement"
```

---

### Task 13: Discharge cut 22 and sweep the documents

**Files:**
- Create: `docs/plans/2026-09-08-conformance-cut-22-results.md`
- Modify: `docs/designs/2026-09-08-biology-pack-design.md` (status header), `docs/plans/2026-08-29-implementation-roadmap.md`, `docs/superpowers/specs/2026-08-29-user-and-autonomy-layer-design.md`, `docs/designs/2026-08-04-domain-extension-boundary-design.md` (§12), `docs/designs/2026-09-05-facet-contracts-design.md` (§5.6, §9, §14), `python/tests/fixtures/biology-fixture.yaml` (its header comment), `tasks/*` via the CLI

- [ ] **Step 1: Write the results record**

Create `docs/plans/2026-09-08-conformance-cut-22-results.md` on cut 21's pattern: the header (cut, freeze commit and digest, subject, discharged date and branch, runner), §1 what ran (the runner command, exit code, the accounting line, the chain), §2 rows (B1–B7, D6, M8 closed; M6 re-read; D1 partial unchanged), §3 deviations dated (any branch Task 11 step 3 took; anything the freeze body did not foresee), §4 the reproduction's measurement by citation of Task 12's record.

- [ ] **Step 2: Correct every claim the discharge falsifies**

- Design status header: replace `Not implemented.` with `Implemented on the domain lane; conformance cut 22 frozen <date> at <commit> and discharged <date> (docs/plans/2026-09-08-conformance-cut-22-results.md).`
- Roadmap: the `domain-boundary` row and the D6/D1 rows as the design's §10 states; the row-count line (closed rows +9, i.e. B1–B7, D6, M8 — count what the roadmap counts and keep its arithmetic honest).
- Layer design sub-project 3: amendment note per §10.
- D §12: the two notes per §10.
- F §5.6, §9 items 3 and 6, §14: answered-by-citation notes per §10.
- `biology-fixture.yaml` header: `Shipping domains/biology/DOMAIN.yaml` is done at cut 22; the fixture stays a fixture.
- Grep the user-facing docs (`docs/guide` or wherever the computation page lives — `grep -rl "cut 21" docs | grep -v designs | grep -v plans`) for "slice 2 remains open", "D6 … deferred", "biology pack" and correct each.

- [ ] **Step 3: Close the tasks and run every gate**

```bash
tasks done <each child id> "<what landed>"   # thirteen children; done in the same commit as their code where the plan was followed
tasks note beliefs-1ce152 "Slice 2 implemented and cut 22 discharged; see docs/plans/2026-09-08-conformance-cut-22-results.md"
tasks check --pretty
cd python && uv run --frozen pytest -q 2>&1 | tail -3 && uv run --frozen ruff check . && uv run --frozen pyright
cd ../ts && npm run typecheck && npm run check && npx vitest run
```

Expected: every gate clean; the pytest summary line shows the count.

- [ ] **Step 4: Commit and hand off**

```bash
git add -A docs tasks python/tests/fixtures/biology-fixture.yaml
git commit -m "docs(domain): discharge conformance cut 22 and correct the claims it falsifies"
```

Then follow `superpowers:finishing-a-development-branch`: the lane merges to `main` after the results record is committed, the worktree is removed only after the ledger under `docs/plans/2026-09-08-mm30-reproduction-slice2-run/` is on the branch, and `beliefs-1ce152` is marked done in the merge's own commit or the one before it.
