# Conformance cut 32 — composite claims

**Status:** frozen 2026-09-16, before implementation, on `design/composite-claim`; U1–U10 are open.
**Design:** `2026-09-12-composite-claims-design.md`, reviewed in three spec passes 2026-09-12 and re-read against `main` at `8aa5903` on 2026-09-16 (§15 there); moved into this directory at this freeze as table U's owner.
**Plan:** `../superpowers/plans/2026-09-12-composite-claims.md`, reviewed in three passes 2026-09-13 and re-read 2026-09-16.
**Numbered after** cut 31 (roadmap concurrency rule 1) and **serialized after** its discharge, which is in the branch ancestry (rule 5). The second lane opened off the dogfood path under rule 6, after cut 31 closed `estimand-typing` and left tier 1 without an on-path boundary.

## 1. What this cut is

The baseline below describes `main` at `8aa5903` before implementation.

Nothing in `beliefs` represents the structure a causal analysis is drawn
against. An edge of a causal DAG is already a first-class object — a typed
claim `affects(X, Y)` on the causal layer with a proposition, a semantic
identity, assessments and a computed belief — but the structure has no
record: which referents form the node set, which claims are its edges, and
the assertion that makes a DAG a model rather than a list, that no other
direct edge holds among those nodes. Kernel §11 left `inquiry`,
`patch-definition` and `structural-chain` unplaced for exactly this reason,
and kernel §4.4 carries them as its one *open, unplaced deliberately* row.

This cut adds the **`composite`** world kind. The base contract gains a
kernel-owned, closed `composite_grammar` (`science.composite.v1`, one shape,
`dag`), the kind, a `composes` signature `composite → proposition`, and a
declared `same_kind` rule on `supersedes`, which widens to the new kind; a
domain contract gains a succession-governed `edges:` table naming, per
operator, which slot is the cause and which the effect. A composite declares
an explicit, closed node set of `(sort, term)` pairs and members that are
propositions named by claim identity; each member is read as a signed
directed edge under the domain declaration, a cycle refuses, and the
absence of an edge between declared nodes is the composite's assertion.
It is belief-inert by construction: `assesses` keeps its one target kind,
the belief input closure never mentions it, and its reading is a pure
function over its members' beliefs and their admitted assessments'
identification terms, obtained through the evaluator's own traced wrapper
and stored nowhere. `structural-chain` dissolves with no successor,
`patch-definition` splits into a composite and a view query, and `inquiry`
decomposes into records that exist. The transition is recreation, not
migration: the mm30 reproduction composes the `h1-prognosis` fragment in a
recreated corpus and reads it in a fresh process, twice.

The selection rule is cut 5's: a clause is selected only when its source
mutation and every named check run inside §2. A row with any unrun arm is
partial.

## 2. The boundary

In scope, as the plan's file map names them:

- `docs/designs/2026-09-16-conformance-cut-32.md`: the frozen boundary, selection, accounting and obligations; `docs/designs/2026-09-12-composite-claims-design.md`: the design, moved here at this freeze;
- `contracts/science/CONTRACT.yaml` and `python/src/beliefs/contracts/science/CONTRACT.yaml`: `composite_grammar`, the `composite` kind, `composes`, `supersedes` with `same_kind`, the `composite` facet; `python/src/beliefs/contract/base.py`: `CompositeGrammar`, `RelationDecl.same_kind`, `COMPOSITE_GRAMMAR`;
- `python/src/beliefs/contract/domain.py`: `EdgeDecl`, `_parse_edge`, `DomainContract.edges`, the `edge:<operator>` entries of `_declarations()`; `fixtures/contracts/testing.yaml` and `python/tests/fixtures/biology-fixture.yaml`: one `edges:` row each, the fixture's `estimands:` row and sorts; `fixtures/claim-identity-v1.json`: regenerated as the compiled identity moves;
- `python/src/beliefs/profile.py`: `ProfileSpec.composite_grammar`, `CompiledEdge`, `ProfileSpec.edges`, the projection; `ts/src/contract.ts`, `ts/src/profile.ts`: the same declarations parsed and compiled, no payload validation;
- `python/src/beliefs/errors.py`: `CompositeError`; `python/src/beliefs/resolution.py`: `ReferentPosition.node()`; `python/src/beliefs/permit.py`: `KIND_ACTS["composite"]`;
- `python/src/beliefs/composite.py`: `CompositeNode`, `Edge`, `CompositeFacet`, `Composite`, `CompositeReceipt`, `build_composite`, `classify`, `composite_identity`, `restore_members`, `read_composite` and its value types; `python/src/beliefs/stored.py`: `COMPOSITE_FACET`, `COMPOSES`, `composite_value`, `composite_node`;
- `python/src/beliefs/corpus.py`: `_refuse_composite`, `_refuse_supersedes_same_kind`, `_refuse_assesses_target_kind`, `supersede` widened to the two kinds with its permit line; `python/src/beliefs/audit.py`: `check_composite`, `check_supersedes_kinds`, both per-kind dispatches (`audit_corpus`'s loop and `_recompute`), the code registries;
- `python/src/beliefs/belief.py`, `python/src/beliefs/evaluation.py`: `Admission` (`NotReached` | `Reached`), `admitted`, `evaluate_traced`, `evaluate_over_traced`; `evaluate` and `evaluate_over` restated as their first projections;
- `python/tools/reproduction/*`: the successor `mm30` contract with `edges:` and its cut-31 predecessor frozen beside it (`mm30-cut31.yaml`, the chain in `vocabulary.py`), `compose.py`, `read.py`, the recreated corpus on the certified volume beside the main checkout, and a dated addendum (§11) to `2026-09-05-mm30-reproduction.md`;
- `python/tests/test_composite.py`, `test_composite_boundary.py`, `test_composite_reading.py`, and edits to `test_base_contract.py`, `test_domain_contract.py`, `test_facet_declarations.py`, `test_coordination.py`, `test_permit.py`, `test_permit_entry_points.py`, `test_profile.py`, `test_audit.py`, `test_belief.py`, `test_evaluation.py`, `test_reproduction_driver.py`; `ts/tests/declarations.test.ts`: unit coverage per task;
- `python/tests/acceptance/test_composite_acceptance.py`, `python/tests/n2_arms_cut32.py` (and its `acceptance/` re-export shim), `python/tests/acceptance/test_n2_cut32.py`, `python/tools/cut32_acceptance.py`: acceptance, declaration, guard, runner;
- `python/tests/test_designs_corpus.py`: table U registered at this freeze; `python/tools/roadmap_status.py`: the cut 32 accounting entry at discharge;
- the amended designs the plan's Task 9 enumerates (kernel §4.1, §4.3, §4.4 and §11; formal model §2.1, §2.2 and §8.2; coordination-and-view-kinds §5.1, a dated note on both literal lists; the user and autonomy layer spec §6.1), the guide's foundations, claims-and-belief, glossary and open-questions pages, the ledger's `Current state`, the roadmap, `README.md` and the cut 32 results record: discharge and navigation.

Shared under concurrency rule 3: `errors.py`, `test_designs_corpus.py`, the ledger, the roadmap and the guide index; beyond those `corpus.py`, `audit.py`, `evaluation.py` and `belief.py` (the `world-read` and `mutation` lanes' surfaces) and `stored.py`. No other kernel lane is open at this freeze; the later merge resolves toward the earlier one.

Out of scope:

- the coordination-contract amendment that adds `composite` to version 1's literal `kinds` list and `composes` to its `relations` list (design §5, limitation 12): sub-project 5's road; `closure` from a composite anchor and a `kinds: [composite]` view predicate both wait on it, and a view names a composite's members by `addresses` until then;
- `publish` and its closure rule (design §5): unbuilt; the sentence "a composite's closure is its members" lands in the user and autonomy layer spec, not in code;
- `search` and the non-empirical route (kernel §11); the eleven K records and every higher-order claim (cut 1 §2.4); the weighted successor belief policy;
- the shipped `biology` pack's `edges:` row (limitation 18): a shipped pack has no succession route, and the fragment needs no biology operator;
- a general relation endpoint-kind check on the write path (limitation 17): the existing `open-questions.md` entry, extended at discharge, not built;
- TypeScript payload validation for composites (limitation 11); a boundary check that reads through `world-resolution`'s read side (limitation 2); qualifier heterogeneity among members (limitation 3); a summary or ladder over the reading's rows (limitation 7).

Frozen declarations and cut bodies through cut 31 remain byte-exact.

## 3. Selection

Ten rows are read, every clause selected, every row single-homed here. Each fenced row is byte-exact from the design's §8 table at the freeze commit.

### U1 — closes

```markdown
| **U1** | The base contract declares `composite_grammar` and the `composite` kind; an unknown shape, a missing grammar, or a `composes` signature outside `composite → proposition` refuses at parse in both implementations | Python and TypeScript parse the shipped contract and refuse each mutation; the world-kind count is fourteen in both |
```
### U2 — closes

```markdown
| **U2** | A domain `edges:` row names an own-namespace operator with `causal` among its layers and two distinct in-range slots; compile keys it by namespaced operator; succession never redefines a row | parse and compile refusals; a successor contract redefining `edge:<op>` refuses under §8.3's rule |
```
### U3 — closes

```markdown
| **U3** | *Form and classification, at construction and at `add` alike:* refuse, with the named code, a member whose operator is undeclared, whose layer is not `causal`, whose argument is outside the node set, a cycle — including one through a negative-polarity member — a duplicate node or member, and an empty node set; admit a composite with nodes and no members, and a negative-polarity member as a signed edge. *Vocabulary, at construction and at reading only:* `build_composite` refuses an isolated node that a consulted vocabulary excludes (`composite-node-not-member`) and the reading refuses the same stored record under the same snapshot, while `add` admits it, checking form only (§4.2); under a snapshot that did not consult the vocabulary both admit it with `not-consulted` in the receipt | one fixture per row of §3.4's table, each asserted at construction and at `add`; the isolated-node fixture asserted at construction, at `add`, and at reading, under an excluding and an unconsulted snapshot |
```
### U4 — closes

```markdown
| **U4** | Minting, superseding and deleting a composite leaves every proposition's belief input digest byte-identical, and `assesses` cannot target one | digest before and after each family operation; a hand-built assessment naming a composite refuses at the signature |
```
### U5 — closes

```markdown
| **U5** | Identity is content identity over the covered facet: authoring order does not move it; a node with no member does; display prose does not | three pairs of records, hashed |
```
### U6 — closes

```markdown
| **U6** | The boundary requires each `composes` target to resolve to a proposition whose semantic identity equals the facet's member at that position; a mismatch, a non-proposition and an unresolvable ref each refuse with their code | a stored composite with a swapped member, a dataset member, and a member ref that resolves nowhere |
```
### U7 — closes

```markdown
| **U7** | The audit reports an unresolvable member, a mismatched member, a relation-set mismatch, and a composite that no longer classifies, as contradictions, not malformedness, and reads the record again in later arms | delete a member and audit; raw-edit a member's claim and audit; retire the `edges:` row by successor and audit |
```
### U8 — closes

```markdown
| **U8** | The reading is a pure function of its named arguments — record, view at the epoch, supplied context, availability, resolution snapshot, binding, profile: two processes agree byte for byte under equal arguments; every row's `belief` **equals** `evaluate_over`'s answer for that member under the same arguments — so withholding the policy implementation reads `NoBelief("unavailable-policy-unheld")`, withholding a dataset observation reads the evaluator's own `NoBelief`, and a member whose inputs sit in an absent corpus reads `NoBelief("unavailable-corpus-absent")` — with the identification column drawn from the same traced admission — two admitted `inconclusive` assessments read `NoBelief("no-directional-outcome")` with both identification terms present, and an answer given before admission reads `not-reached`, never `{}`; a member with no admitted assessment reads `NoBelief` and `{}`; a superseded member reads its successors and a belief; an unresolvable member refuses the reading; a memberless composite reads no rows and a node receipt, with `not-consulted` for a node under an unconsulted vocabulary | the reproduction's composite read twice from persisted records (§9); a fixture composite with an assessed, an unassessed and a superseded member, read under full availability and under each withholding, each row compared with `evaluate_over` called directly; a two-inconclusive fixture; a one-admitted-one-refused fixture pinning the admitted set apart from the digest's keyed facets; a memberless two-node composite under an unconsulted snapshot |
```
### U9 — closes

```markdown
| **U9** | `supersede` admits a same-kind composite successor, authors the relation, and refuses a cross-kind pair and an identity-unchanged successor; a `supersedes` instance with endpoints of different kinds refuses on the shared path for `add` and for `import_bundle` (`ImportRefused`, the member named), and a raw-written one audits as `supersedes-cross-kind`; both parsers refuse `same_kind` on a relation whose sources and targets differ | the three family calls; an import bundle carrying `composite ──supersedes──▶ proposition` and its reverse; a raw-written pair audited; a mutated contract parsed in Python and TypeScript |
```
### U10 — closes

```markdown
| **U10** | The reproduction composes the `h1-prognosis` fragment from the recreated corpus and reads it in a fresh process: the assessed member carries the evaluator's own answer for it — over the recreated corpus a `NoBelief("no-directional-outcome")` from an `inconclusive` outcome, with identification `{observational}`; measured, not asserted — and the unassessed one `NoBelief("no-eligible-assessment")` and `{}`, from persisted records, twice, byte-identical | §9's addendum, from persisted records |
```

**Selected:** every clause of every row, as the acceptance units of `test_composite_acceptance.py` and the N2 arms of §5; U8 and U10 are held against persisted records in a fresh process, twice. U10's reproduction step is executed by the driver against the corpus on the certified volume and read from its dated addendum; its **measured, not asserted** clause — the target member's answer, `NoBelief("no-directional-outcome")` over the recreated corpus — is written into the row as what the record measured, and no check pretends the reproduction computed a directional belief. If the driver's `compose` step refuses (a node `not-member` under the reproduction's snapshot, plan Task 8's `test_u10` skip), the arm is unrun and the row partial, reported as such.

**Deferred:** nothing.

### Boundary invariants

No P row's verdict changes: minting, superseding and deleting a composite leaves every proposition's belief input digest byte-identical (U4), and `evaluate` equals the first projection of `evaluate_traced` over every scenario in `test_belief.py`. `assesses` keeps its one target kind (U4). `WORLD_KINDS` gains exactly one kind, fourteen in both implementations (U1). M1–M13 are untouched; M6 governs `edges:` without amendment, and an operator's own `schema_projection()` is byte-identical before and after an `edges:` row is added. Claim identities do not move (M8). No `n2_arms_cut*.py` body through cut 31 is edited; a live guard whose pinned `before` line this lane moves is re-targeted in that guard, never silenced.

## 4. Accounting

Ten guarantee rows enter the corpus and are read, **10 full/closed** at discharge. The frozen inventory is **10 declaration units** (`U1`–`U10`) expanding to **26 one-mutation sabotage arms** (plan Task 8 Step 3; the `before` blocks are copied from the tree that exists then, and the accounting freezes there). At this freeze the global corpus moves to **216 rows** in **twenty tables**, 163 closed and 53 open; at discharge it moves to **173 of 216 closed, 43 open**. `composite-claims` enters the ledger's `Current state` table and the roadmap's boundary index at discharge and closes in the same results commit; `contract-cut` (`beliefs-eacbe2`) gains this lane as a dependency at the lane's opening; kernel §4.4's open row empties and the kernel counts fourteen kinds.

## 5. N2 and acceptance obligations

Every arm is a byte-exact sabotage on a line this cut writes, its `before` block copied from the tree that exists at Task 8 and audited by `arm_staleness` against the tree; the accounting freezes there (plan Task 8 Step 1, on cut 25's precedent for a dated supplement in §8 of this document). One arm per mechanism of design §10.3 and of the plan's Tasks 3–6, homed by declaration unit:

- **U1** (1): `U1-a` make `composite_grammar` optional in the base parser (`contract/base.py`)
- **U2** (2): `U2-a` drop the `"causal" not in operator.layers` refusal (`contract/domain.py`, `_parse_edge`); `U2-b` drop the `edge:` group from `_declarations()` (`contract/domain.py`)
- **U3** (4): `U3-a` drop the `layer != "causal"` refusal (`composite.py`, `classify`); `U3-b` skip the `negative`-polarity member's edge (`composite.py`, `classify`); `U3-c` compute `refused` over `outcome.performed` instead of `outcome.refuses`, admitting `not-member` (`composite.py`, `build_composite`); `U3-d` drop the empty-set refusal (`composite.py`, `_canonical_nodes`)
- **U4** (4): `U4-a` let the closure projection reach the composites naming a proposition (`closure.py`); `U4-b` add `composite` to `assesses`' targets (both `CONTRACT.yaml` copies); `U4-c` make `target.kind != "proposition"` `False` (`corpus.py`, `_refuse_assesses_target_kind`); `U4-d` turn the `except RefError` arm into `continue` (`corpus.py`, `_refuse_assesses_target_kind`)
- **U5** (1): `U5-a` omit `nodes` from the identity projection (`composite.py`, `composite_identity`)
- **U6** (2): `U6-a` replace the `restore_members` call with a form-only pass, skipping step 3 (`corpus.py`, `_refuse_composite`); `U6-b` drop the `len(composes) != len(facet.members)` check (`corpus.py`, `_refuse_composite`)
- **U7** (2): `U7-a` drop the `composite` arm from the audit loop (`audit.py`, `audit_corpus`); `U7-b` map `composite-member-unresolvable` to `composite-malformed` (`audit.py`, `check_composite`)
- **U8** (7): `U8-a` yield a `NoBelief("no-eligible-assessment")` row for an unresolvable member instead of refusing (`composite.py`, `read_composite`); `U8-b` default an empty identification set to `observational` (`composite.py`, `read_composite`); `U8-c` build `availability` from the view instead of taking it (`composite.py`, `read_composite`); `U8-d` replace `evaluate_over_traced` with `gather` + `evaluate_traced`, skipping the absent-corpus arm (`composite.py`, `read_composite`); `U8-e` call `admission.admit` per gathered assessment instead of reading the traced set (`composite.py`, `read_composite`); `U8-f` return `NotReached()` on every `NoBelief` (`belief.py`, `evaluate_traced`); `U8-g` call `belief.admitted` a second time over the gathered records (`composite.py`, `read_composite`)
- **U9** (3): `U9-a` move `_refuse_supersedes_same_kind` under `if not document_validated:` (`corpus.py`, `_refuse`); `U9-b` drop the `same_kind and set(sources) != set(targets)` refusal (`contract/base.py`); `U9-c` make `target.kind != node.kind` `False` (`audit.py`, `check_supersedes_kinds`)

Both directions for every arm: the check passes against the real tree (`baseline`) and fails under the sabotage (`audit`). Acceptance: `python/tests/acceptance/test_composite_acceptance.py`, one test per row named `test_u<n>_<slug>`, composed from the unit constructions over a registered durable corpus; U8 compares every row with `evaluate_over` called directly under the same arguments and reads the durable corpus from two subprocesses; U10 reads the reproduction's recorded state (`reading_equal`, the node receipt, the two signed rows). Runner: `python/tools/cut32_acceptance.py`, `PREFIX_RUNNERS = ("cut31_acceptance.py",)`, `PHASE_MODULES = ("test_composite_acceptance.py", "test_n2_cut32.py")`, its default work root under the main checkout's `.work/acceptance/`. Guard: `python/tests/acceptance/test_n2_cut32.py` on `test_n2_cut31.py`'s shape, pinning this document's SHA-256, the freeze commit and the declaration's SHA-256.

## 6. Second reader

Verify each fenced row byte-exact against the design's §8 table at the freeze commit; audit every selected clause against §2; force any unrun clause to remain deferred and its row partial. Challenge especially:

- that polarity is the edge's sign and never its presence, so a cycle through a negative-polarity member refuses (U3) and the signed-cycle fixture cannot be satisfied by dropping the member;
- that the boundary checks form only and never vocabulary membership, while the constructor and the reading resolve nodes under the snapshot their caller names (U3's two halves), and that `add` admits the isolated node `build_composite` refuses;
- that U4's otherwise-eligible assessment — an observing run over a held, attested dataset — is refused at `add` and at `import_bundle` on its `assesses` target's kind, and that the eligibility predicate alone would admit it;
- that every U8 row equals `evaluate_over`'s answer under the same arguments, that the identification column is drawn from the one traced admission and never a second `admit` or `admitted` call, and that two admitted `inconclusive` assessments read `NoBelief("no-directional-outcome")` with both terms present while an answer given before admission reads `not-reached`, never `{}`;
- that the same-kind rule sits on the shared refusal path outside the `document_validated` shortcut, so an import bundle carrying `composite ──supersedes──▶ proposition` refuses in either direction (U9);
- that `check_composite` runs in both audit dispatches and that its four codes and `supersedes-cross-kind` are contradictions, never malformedness, read again by later arms (U7);
- that U10 reads persisted records in a fresh process and records the evaluator's answer as measured — `NoBelief("no-directional-outcome")` from an inconclusive outcome — rather than a belief the reproduction never computed.

## 7. Limitations

Design §13, restated: membership asserts directness only relative to the node set, and a member's belief is about the claim as stated (1); members are corpus-local at the boundary, and neither this boundary nor the estimand target check reads through `world-resolution`'s read side, closed at cut 30 (2); qualifier heterogeneity among members is not checked (3); cycles refuse (4); structural-layer members refuse by layer and `is-proxy-for` refuses as undeclared (5); latent nodes carry no marker (6); no summary, no ladder (7); faithfulness and the Markov condition are unstated (8); no relation between composites (9); a depth-bounded neighbourhood and an exclusion list are not expressible in `science.view-query.v1` (10); TypeScript validates no composite payload (11); `closure` from a composite anchor and a `kinds: [composite]` predicate both wait on the coordination-contract amendment (12); the identification column depends on estimand typing, discharged at cut 31 (13); an explicit absence claim is unrepresentable (14); node membership is resolved at construction and at reading, never at the boundary (15); the identification column follows admission as it is, retraction filtering deferred with the C group (16); relation endpoint kinds are not enforced at the write boundary, the existing open question extended rather than a check built (17); a shipped domain pack has no succession route, so the `biology` pack gains no `edges:` row here (18).

## 8. Supplements — 2026-09-16

Three corrections found while writing the N2 arms (plan Task 8 Step 3),
recorded here on cut 25's precedent: §§1–7 above are the frozen body and are
**not** edited. This section is dated and outside the freeze — the guard's
`_frozen_body` slicing runs from `## 2. The boundary` to this heading — so the
pin of this document at freeze commit
`ff03b00f7f6297f3277da4ab40e1dbfc0b9a39e0`, SHA-256
`598222cbac1ac04e43e503b05287524dc6a3049b760063721482dc844ca43ac2`, is
unchanged by it and is not re-taken. None of the three adds, removes or moves
a declaration unit, a row or an arm: §4's **10 declaration units** and **26
one-mutation sabotage arms** and §5's homing stand exactly as frozen. Each
correction names a different module or site for one arm's mutation, and each
was measured, not argued: the arm as §5 spells it was written, run, and scored
by the harness before it was moved.

§5 homes no arm on **U10**, and the guard says so by name
(`test_n2_cut32.py`'s `UNAUDITED_UNIT`) rather than passing silently on the
absence: U10's row is read from the mm30 reproduction's recorded state in a
fresh process, and a source mutation that moved it would be a mutation of a
driver that has already run.

### 8.1 U4-a's mutation lands in `evaluation.py`, not `closure.py`

§5 spells U4-a as *"let the closure projection reach the composites naming a
proposition (`closure.py`)"*. No mutation of `closure.py` can do that.
`build_closure` is a pure function of the arguments it is handed —
`assessments`, `runs`, `verifications`, the supplied lineage snapshot, the
producer-snapshot identity, the retraction enumeration, the consulted pairs,
the binding and the observed-facet rows — and it holds **no read view**. It
therefore cannot see a composite at all, and every mutation available inside
it moves the digest identically before and after a composite is minted, which
is exactly the comparison U4 makes. An arm written there scores `vacuous`.

The one function that resolves a proposition's belief inputs *from a corpus*
is `evaluation.gather`, so U4-a is homed there. Its `before` is `gather`'s

```python
    absent.extend(context.snapshot.not_present.items())
```

and its `after` extends the same list with the composites whose `composes`
edges name the proposition under evaluation. The property falsified is the
one U4 states — a composite naming a proposition is inert to that
proposition's belief — and the check that fails is `test_u4_belief_inert`,
which reads the digest through `evaluate_over` before and after minting,
superseding and deleting a composite naming `proposition:ab`. The mechanism
count is unchanged: one arm, homed on U4.

### 8.2 U1-a's site inside `contract/base.py`

§5 spells U1-a as *"make `composite_grammar` optional in the base parser
(`contract/base.py`)"*, and the plan's table gives the shape
`root.get("composite_grammar", {...})`. Written exactly there, the arm scores
`vacuous`, and the measurement says why: `parse_base_contract` calls
`_exact_fields(root, _CONTRACT_FIELDS, source)` before it reads any grammar,
and `_CONTRACT_FIELDS` carries `composite_grammar`, so a document without the
key is refused by the field check and the `root[...]` read is never reached.
`root.get(...)` alone does not make the grammar optional; it makes an
unreachable line defensive.

The arm is therefore homed on the same module and the same mechanism at the
site where optionality is actually decided:

```python
    _exact_fields(root, _CONTRACT_FIELDS, source)
```

becomes a `root.setdefault("composite_grammar", {"version": 1, "shapes":
["dag"]})` ahead of that call. That is *"`composite_grammar` made optional"*
in one mutation, and `test_u1_grammar_kind_and_relations` — which parses the
packaged contract with the grammar deleted and requires the refusal — fails
under it.

### 8.3 U8-a's sabotage drops the unresolvable member rather than reading it

§5 spells U8-a as *"yield a `NoBelief("no-eligible-assessment")` row for an
unresolvable member instead of refusing"*. A row cannot be minted for a member
that does not resolve without also inventing its `claim` and its `role`:
`MemberRow` carries both, `classify` produces the role only for members whose
claims restored, and a mutation that forged either would be sabotaging the
row's construction rather than the refusal. The arm is written as the other
half of the same disjunction — `read_composite` filters the unresolvable refs
out of the facet and the ref tuple before `restore_members`, so the reading
returns the resolvable rows and **does not refuse**. The asserted property is
unchanged (*"an unresolvable member refuses the reading"*), the check is
unchanged (`test_u8_reading_equals_the_wrapper`, whose last arm requires
`CompositeError("composite-member-unresolvable")` after a member is deleted),
and the arm scores `sound`.

### 8.4 Where U3's "at construction and at `add` alike" rows land at the boundary — 2026-09-16

Task 8's review asked for the three pure-form rows of §3's **U3** — a duplicate
node, a duplicate member, and an empty node set — to be asserted at `add` as
well as at construction. They are, and the measurement is worth recording,
because the code they carry at `add` is not the code they carry at
construction.

§4.2's step 1 is the **facet decode**: the boundary reads the stored composite
facet before it re-derives anything from it. `CompositeFacet.__post_init__` is
that decode, and those three defects are defects *of the facet*, not of any
classification over it — a facet whose nodes repeat, whose members repeat, or
whose node set is empty is not a composite facet at all. So the boundary
refuses each of them with the decode's own code, `MalformedRecord`, and no
`composite-*` code is reached:

| row | at construction (`build_composite`) | at `add` (`_refuse_composite`, step 1) |
|---|---|---|
| duplicate node | `composite-duplicate` | `MalformedRecord`, "sorted by (sort, term) and distinct" |
| duplicate member | `composite-duplicate` | `MalformedRecord`, "sorted and distinct" |
| empty node set | `composite-nodes-empty` | `MalformedRecord`, "at least one node" |
| member outside the node set | `composite-member-outside-nodes` | `composite-member-outside-nodes` |
| undeclared operator | `composite-member-undeclared` | `composite-member-undeclared` |
| non-causal layer | `composite-member-layer` | `composite-member-layer` |
| cycle, negative member included | `composite-cyclic` | `composite-cyclic` |
| unknown shape | `composite-shape` | `composite-shape` |

That is §4.2's rule rather than a gap in it: the constructor takes nodes and
members as arguments and can name which one repeated, while the boundary takes
a stored record and must first decide whether what it holds is a facet. Both
refuse, neither admits, and `test_u3_form_classification_and_vocabulary_arms`
asserts both columns — the class and the part of the message that names the
defect on the right, the code on the left. No unit, row or arm moves.

### 8.5 U4-b mutates the packaged contract copy only — 2026-09-16

§5 spells U4-b as *"add `composite` to `assesses`' targets (both `CONTRACT.yaml`
copies)"*. An N2 arm is one byte-exact mutation of one module inside **one**
package tree: `test_n2.py`'s harness copies `python/src/beliefs` and mutates
the copy, so the repo-root `contracts/science/CONTRACT.yaml` is not reachable
from an arm at all, and a second arm for it would be a second arm.

The arm therefore names `contracts/science/CONTRACT.yaml` under the package,
and `test_u1_grammar_kind_and_relations` and `test_u4_belief_inert` read the
**packaged** contract through `importlib.resources` — the copy the sabotage
moves — rather than the repo-root copy that `tests/conftest.py`'s
`base_contract` fixture loads. The two copies are held byte-equal by the
existing parity machinery, so the row's claim is unweakened: the declaration
the kernel actually parses is the one the arm moves and the one the check
reads. One arm, homed on U4, as §5 counts it.
