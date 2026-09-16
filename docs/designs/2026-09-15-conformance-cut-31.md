# Conformance cut 31 — estimand typing

**Status:** frozen 2026-09-15, before implementation, on `design/estimand-typing`. Q1–Q10 are open.
**Design:** `2026-09-12-estimand-typing-design.md`, reviewed in three spec passes and a plan review 2026-09-12 and worked against a second domain 2026-09-15 (§15, Appendix A there); moved into this directory at this freeze as table Q's owner.
**Plan:** `../superpowers/plans/2026-09-12-estimand-typing.md`, reviewed in two passes 2026-09-12.
**Numbered after** cut 30 (roadmap concurrency rule 1) and **serialized after** its discharge, which is in the branch ancestry (rule 5). The first lane opened off the dogfood path under rule 6, after cut 30 left tier 1 with no on-path boundary.

## 1. What this cut is

The baseline below describes `main` at `5127dcf` before implementation.

Four belief-bearing fields are prose: `estimand`, `applicability`, `estimate`
and `uncertainty` are `str` on the spec draft and the assessment value, the
stored reader coerces them and drops non-strings, and the interpretation rule
may return any string for the two it yields. Kernel limitation 5 and belief
policy §3.2 name the consequence — no estimand match is stateable, no weight
table has a key domain, and applicability cannot be compared — and the
predecessor's F11 records what a fixed statistical shape in the kernel costs
instead.

This cut types the **structure** an estimand has and leaves every vocabulary
that fills it to a domain contract. The base contract gains a kernel-owned,
closed `estimand_grammar` (`science.estimand.v1`); a domain contract gains a
succession-governed `estimands:` table declaring, per operator, the sorts its
levels, measures, identifications and conditioning members draw on; the
frozen spec carries a typed estimand built against the typed claim it answers
and a qualifier-map applicability over the operator's declared dimensions;
the rule returns decimal estimates and typed uncertainty on the spec's
declared scale and reference and nothing else; structural match is checked
at the write boundary, at import and under audit; and two predicates,
`commensurable` and `co_scoped`, are exposed from `beliefs.estimand` and
read by nothing in `science.belief.v1`. The transition is recreation, not
migration: a pre-grammar record is refused under a named reason and audited
under its own code, and the mm30 reproduction re-authors its spec in a
recreated corpus and re-derives its belief from disk in a fresh process.

The selection rule is cut 5's: a clause is selected only when its source
mutation and every named check run inside §2. A row with any unrun arm is
partial.

## 2. The boundary

In scope, as the plan's file map names them:

- `docs/designs/2026-09-15-conformance-cut-31.md`: the frozen boundary, selection, accounting and obligations; `docs/designs/2026-09-12-estimand-typing-design.md`: the design, moved here at this freeze;
- `contracts/science/CONTRACT.yaml` and `python/src/beliefs/contracts/science/CONTRACT.yaml`: `estimand_grammar`; `python/src/beliefs/contract/base.py`: `EstimandGrammar`, parsed and refused;
- `python/src/beliefs/contract/domain.py`: `EstimandDecl`, `_parse_estimand_decl`, `DomainContract.estimands`, the `estimand:<operator>` entries of `_declarations()`; `fixtures/contracts/testing.yaml`: three fixture sorts and two `estimands:` entries, shared with TypeScript;
- `python/src/beliefs/profile.py`: `CompiledEstimandDecl`, `ProfileSpec.estimands`, `ProfileSpec.estimand()`, the projection; `ts/src/contract.ts`, `ts/src/profile.ts`: the same declarations parsed and compiled, no payload validation;
- `python/src/beliefs/errors.py`: the `EstimandError` family and `PreGrammarRecord`; `python/src/beliefs/resolution.py`: `ReferentPosition.estimand()`;
- `python/src/beliefs/estimand.py`: the opaque values, `build_estimand`, `build_applicability`, the projections, `commensurable`, `co_scoped`;
- `python/src/beliefs/decode.py`: `WireEstimand`, `decode_estimand`, `estimand_from_stored`, `applicability_from_stored`;
- `python/src/beliefs/spec.py`: typed `SpecDraft` and `FrozenSpec`, the `ESTIMAND_GRAMMAR` member, `restore(..., profile=)`, `revise`; `python/src/beliefs/stored.py`: `analysis_spec_value(node, *, profile)`, typed `assessment_node` and `assessment_value`;
- `python/src/beliefs/record.py`, `python/src/beliefs/assess.py`: typed `AssessmentValue`; the constructor's checks on rule output;
- `python/src/beliefs/corpus.py`, `python/src/beliefs/audit.py`: `_refuse_estimand_target_mismatch`, `check_spec_target`, the pre-grammar codes;
- `python/src/beliefs/consulted.py`, `evaluation.py`, `belief.py`, `succession.py`, `replay.py`: the estimand walk; `profile` threaded to the readers;
- `python/tools/reproduction/*`: the successor `mm30` contract, its held lists, the typed spec, the recreated corpus, the fresh-process restore, and a dated addendum to `2026-09-05-mm30-reproduction.md`;
- `python/tests/test_estimand_declarations.py`, `test_estimand.py`, `test_estimand_decode.py`, and edits to `test_spec.py`, `test_assess.py`, `test_records.py`, `test_consulted.py`, `test_audit.py`, `fixtures_cut3.py`: unit coverage per task;
- `python/tests/acceptance/test_estimand_acceptance.py`, `python/tests/n2_arms_cut31.py` (and its `acceptance/` re-export shim), `python/tests/acceptance/test_n2_cut31.py`, `python/tools/cut31_acceptance.py`: acceptance, declaration, guard, runner;
- `python/tests/test_designs_corpus.py`: table Q registered at this freeze; `python/tools/roadmap_status.py`: the cut 31 accounting entry at discharge;
- the amended designs the plan's Task 12 enumerates (kernel §4.2.1 and limitation 5; computation §3.1, §3.1b, §5.1; formal model §7.1, §11; belief policy §3.2, §5, §9; review disposition §8 question 4; facet contracts §3.2; domain boundary D6), `domains/biology/DOMAIN.yaml` and the mm30 corpus-local contract by successor, the guide's claims page, glossary and open questions, the ledger's `Current state`, the roadmap, `README.md` and the cut 31 results record: discharge and navigation.

Shared under concurrency rule 3: `errors.py`, `test_designs_corpus.py`, the ledger, the roadmap and the guide index; beyond those `decode.py` (the `mutation` lane's surface), `corpus.py` and `evaluation.py` (the `world-read` lane's), and `stored.py`. The later merge resolves toward the earlier one.

Out of scope:

- ρO3's entailment half (formal model §6.7) and quantifier-directed gating (belief policy §5): P1–P9 are preserved verbatim, v1 reads no magnitude-bearing field, and no mismatch finding is emitted (design decision 2);
- the eleven K records and every higher-order claim (cut 1 §2.4): attenuation, model comparison and mediation refuse at the fragment (design §3.3);
- the weighted successor belief policy (S6 arm (h)): its key domain is supplied here and its design stays `weighted-belief`'s;
- the non-empirical route (kernel §11); `method` and `assumptions` stay prose or ref;
- TypeScript payload validation and spec hashing (F limitation 10, extended);
- cross-corpus spec targets (`world-resolution`'s read side): refused as `estimand-target-unresolvable`, never admitted unchecked;
- the natural-systems pack and its facet: Appendix A of the design is a worked example and asks for nothing; its API half (`beliefs-e48279`) is a unit test inside §2 and adds no row.

Frozen declarations and cut bodies through cut 30 remain byte-exact.

## 3. Selection

Ten rows are read, every clause selected, every row single-homed here. Each fenced row is byte-exact from the design's §8 table at the freeze commit.

### Q1 — closes

```markdown
| **Q1** | The estimand's structure is kernel-owned and closed | A base contract lacking `estimand_grammar` → **refused** at load; a domain contract declaring `estimand_grammar`, `contrast_kinds`, `scales` or `uncertainty_kinds` → **refused** at load; a `tag_encoding` other than `science.identity.v1` → refused; `build_estimand` with `kind`, `scale` or an uncertainty `kind` outside its set → **refused**. **Sabotage:** widen a closed set in the implementation without editing the contract and assert the shipped base-contract fixture **fails** |
```
### Q2 — closes

```markdown
| **Q2** | `estimands:` is domain-issued, operator-bound and succession-governed | An entry keyed by an operator the contract does not declare → refused at load; an unresolved sort → refused at compile with the missing namespace named; an arity-0 operator → refused; a `level_sorts` index outside `Fin(arity)` or duplicated → refused. **Succession:** a successor adding an entry for an operator that had none → **accepted**, with the operator's own `schema_projection()` byte-identical (M6 unamended); changing any of the four members → `SuccessionViolation`; dropping an entry → `SuccessionViolation`; retiring the operator → the entry survives as a tombstone. **Negative:** reorder `level_sorts` keys and assert the contract's content identity and the projection are **unchanged** |
```
### Q3 — closes

```markdown
| **Q3** | An estimand is unconstructible outside its claim's operator declaration, and refuses rather than flattens | Each refusal in §7.1, one fixture each, asserting the position named; a wrong-sorted level, contrasted quantity, measured quantity, identification and conditioning member each **refused**; a continuous contrast with no quantity, or with an increment of `0`, negative, or a `float` → **refused**; `not-member` refuses and `not-consulted` **mints** with a receipt, and the five outcomes stay distinct (D3 preserved). **Fragment:** three levels, two slots, a second measure, an attenuation pair → each refused with the fragment named, and assert **no flattened estimand** is reachable. **Opacity:** `Estimand` has no public field-wise constructor (M13's shape), and `claim` and `operator` are taken from the `Claim` handed in, never from the wire |
```
### Q4 — closes

```markdown
| **Q4** | `applicability` is a qualifier map over the target operator's dimensions, comparable and unread | An undeclared dimension, two restrictions on one dimension, an unbound restriction → refused; the empty map admitted; `applicability == claim.qualifiers` computed by canonical projection equality and **decidable in both directions**. **P6 preserved verbatim:** change only `applicability`, assert belief value unchanged and digest moved, and assert **no mismatch finding exists** to be emitted |
```
### Q5 — closes

```markdown
| **Q5** | Estimate and uncertainty are typed on the spec's scale, and the rule cannot move the reference | A rule yielding a `float`, a `str`, an interval with `low > estimate` or `high < estimate`, `level ∉ (0, 1)`, a negative standard error, or an estimate `≤ 0` under `multiplicative` → **no assessment**, an `AssessmentFinding` naming the violation, and never `inconclusive`; a rule output carrying `reference` or `scale` → the same. **Negative:** a rule yielding nothing but `outcome` mints as today, and `mm30-reproduction/outcome-file/v1`'s identity is **unchanged** |
```
### Q6 — closes

```markdown
| **Q6** | Structural match is checked at the write boundary and under audit; semantic match is not claimed | A spec whose estimand was built against a claim other than the one its target record carries → `ValidationRefused("estimand-target-mismatch")` — **including** a claim at the **same operator** with different arguments, or the same arguments under different qualifiers; a target the writer's view cannot resolve → `ValidationRefused("estimand-target-unresolvable")`; explicit import refuses the same; a raw-written mismatching spec is **not** refused on read and is caught **only** under audit with `spec-target-contradicted`. **The inconsistent stored pair:** raw-write a spec whose estimand carries the target's **correct** claim identity beside a **different** declared operator, with contrast, measure and control correctly typed under that operator and the spec digest recomputed; assert it decodes without refusal, that explicit import **refuses** it and audit **contradicts** it on the operator equality alone, and — **sabotage** — that comparing claim identities only lets it through. **Negative:** a measured quantity of the right sort that does not in fact operationalize the claim's argument is **admitted** — the check is structural, and the row asserts it does not pretend otherwise |
```
### Q7 — closes

```markdown
| **Q7** | Every member enters identity, and only members do | Change **only** `claim`, `contrast.slot`, `kind`, `baseline`, `comparison`, `contrast.quantity`, `increment`, `measure.quantity`, `measure.scale`, `reference`, `control.identification`, one `conditioning` member, or one `applicability` entry: the spec identity **moves** each time; reorder `conditioning` → **unchanged**; `increment` `1` against `1.0` → **unchanged** (identity v1's canonical decimal text). On the assessment: change only `estimate`, only `uncertainty`, only `estimand`, only `applicability` → the facet digest **moves**, the belief value is **unchanged** (P6's four arms, now per member); G3's keyed-facet arms unchanged. **Negative:** an editorial change to a consulted contract leaves `I_claim` unchanged (M8) |
```
### Q8 — closes

```markdown
| **Q8** | The estimand's contracts are consulted | Derive belief over an assessment whose estimand binds a measure sort declared in contract `X`; bump `X` touching no facet, no operator and no claim → `belief_input_digest` **moves**; bump an activated contract the estimand does not reach → **unchanged**; type an estimand under a sort pinned by no corpus → `ContractDisagreement`. **Sabotage:** drop the estimand walk from `consulted_contracts` and assert the first arm **fails** |
```
### Q9 — closes

```markdown
| **Q9** | Commensuration is total, decidable, and unread by v1 | For any two admitted estimands the predicate returns a boolean, never raises; equal except `control.identification` → **commensurable**; differing in any other member → **not**; `baseline`/`comparison` swapped → **not**; the same contrast and measure over two claims at one operator (PHF19 and EZH2) → **not**; per-unit against per-ten-units of one quantity → **not**. **The scope counterexample:** two specs on **one** claim with **identical** estimands and **different** typed applicability maps (`population ↦ ⟨generic, adults⟩` against `{}`) → `commensurable` is **true** and `co_scoped` is **false**; assert both predicates are exposed, both are total, and neither is read by v1's evaluator (**sabotage:** make `co_scoped` raise and assert every P row still passes). **Sabotage:** make the predicate raise and assert every P row still passes — v1 never calls it; **P5** still holds: no API path produces unequal weights |
```
### Q10 — closes

```markdown
| **Q10** | The reproduction recreates its corpus, re-authors its spec, and re-derives from disk | The driver recreates the reproduction corpus under the successor contracts (decision 10); the record's estimand builds with every referent resolving `member` against the held lists; the prose applicability's second clause is **refused** at retyping (§4), and the typed spec is minted by `freeze` with no `supersedes`; steps 4–10b re-run; the belief re-derives to the **same value** under a **different digest**; the consulted set is unchanged. **Then, in a fresh process** holding nothing in memory: restore the frozen spec through `analysis_spec_value` and the assessment through `assessment_value` from the corpus on disk, re-derive the assessment from its run and the belief from its closure, and assert both equal what the driver's process derived — the recovered-from-the-corpus-alone reading the reproduction record §5 question 3 required of verification. **The transition:** present the **prior** corpus state's prose spec and assessment to the same readers under the successor profile and assert `UnfreezableSpec("pre-grammar spec")` and `MalformedRecord("pre-grammar assessment")`, and that no reader returns a typed value for either; assert `audit_corpus` over that state under the successor profile reports `profile-mismatch: base` and nothing else — its pinned base contract predates the grammar and does not parse under the successor, so the existing profile-disagreement rule fires before any record is read and is preserved. The codes `spec-pre-grammar` and `assessment-pre-grammar` are exercised on a corpus **pinned to the successor** holding a raw-written pre-grammar record, and assert **not** `derivation-malformed` there. **Not asserted:** that the new spec's scope equals the prose spec's — the addendum records the authored judgment and no row certifies it. **Measured, not asserted** (§9) |
```

**Selected:** every clause of every row, including each row's **negative** and **sabotage** clauses, as the acceptance units of `test_estimand_acceptance.py` and the N2 arms of §5. Q10's reproduction re-run is executed by the driver against the corpus on the certified volume and read from its dated addendum; its **not asserted** clause — that the re-authored spec's scope equals the prose spec's — is written into the row as a limit the row closes carrying (M1's shape, roadmap Appendix C), and no check pretends otherwise.

**Deferred:** nothing.

### Boundary invariants

No P row's verdict changes: change only `estimand`, `applicability`, `estimate` or `uncertainty` on an assessment and the belief value is unchanged (Q4, Q7). M1–M13 are untouched; M6 governs the new declaration class without amendment, and an operator's own `schema_projection()` is byte-identical before and after an `estimands:` entry is added (Q2). Claim identities do not move (M8). `mm30-reproduction/outcome-file/v1`'s identity is unchanged (Q5). The mm30 reproduction's consulted set stays `{science, mm30, biology}` (Q8, design §5.4). No `n2_arms_cut*.py` body through cut 30 is edited.

## 4. Accounting

Ten guarantee rows enter the corpus and are read, **10 full/closed** at discharge. The frozen inventory is **10 declaration units** (`Q1`–`Q10`) expanding to **26 one-mutation sabotage arms**. At this freeze the global corpus moves to **206 rows** in **nineteen tables**, 153 closed and 53 open; at discharge it moves to **163 of 206 closed, 43 open**. `estimand-typing` enters the ledger's `Current state` table and the roadmap's boundary index at discharge and closes in the same results commit; `weighted-belief`'s *blocked on* becomes the successor belief-policy design over `commensurable` and `co_scoped`; `contract-cut` gains this lane as a dependency.

## 5. N2 and acceptance obligations

Every arm is a byte-exact sabotage on a line this cut writes, its `before` block copied from the tree that exists at Task 11 and audited by `arm_staleness` against the tree; the accounting freezes there (plan Task 11 Step 1, on cut 25's precedent for a dated supplement in §8 of this document). One arm per mechanism of design §10.3, homed by declaration unit:

- **Q1** (2): `Q1-a` drop the closed-set membership check (`estimand.py`, the scale, kind and uncertainty-kind sets); `Q1-b` admit an unknown grammar key (`base.py`, `_exact_fields` over `estimand_grammar`)
- **Q2** (3): `Q2-a` skip the operator-declared check on an `estimands:` key (`domain.py`); `Q2-b` skip the `Fin(arity)` check on `level_sorts` (`domain.py`); `Q2-c` drop `estimand:` entries from `_declarations()` (`domain.py`)
- **Q3** (7): `Q3-a` skip the level-sort presence check (`estimand.py`); `Q3-b` admit `not-member` (`estimand.py`, `_resolve_all`); `Q3-c` skip the duplicate-conditioning check (`estimand.py`, `Control.__post_init__`); `Q3-d` admit a float reference (`estimand.py`, `_finite`); `Q3-e` drop the sign check under `multiplicative` (`estimand.py`); `Q3-f` admit an increment of `0` (`estimand.py`, `ContinuousContrast.__post_init__`); `Q3-g` take `claim` from the wire instead of the `Claim` (`estimand.py`, `build_estimand`)
- **Q4** (1): `Q4-a` drop the dimension check in `build_applicability` (route around `Claim._checked`)
- **Q5** (3): `Q5-a` admit a string estimate (`assess.py`, `check_estimate`); `Q5-b` drop `low ≤ estimate ≤ high` (`estimand.py`, `check_uncertainty`); `Q5-c` drop the extra-key refusal on rule output (`assess.py`)
- **Q6** (3): `Q6-a` drop the operator equality from `_refuse_estimand_target_mismatch`, keeping the claim-identity one (`corpus.py`); `Q6-b` drop the claim-identity equality, keeping the operator one (`corpus.py`); `Q6-c` drop `check_spec_target` from the audit loop (`audit.py`)
- **Q7** (3): `Q7-a` drop `claim` from the estimand projection (`estimand.py`); `Q7-b` drop `increment` from the projection (`estimand.py`); `Q7-c` drop the `estimand_grammar` member from the spec projection (`spec.py`)
- **Q8** (1): `Q8-a` drop the estimand walk in `consulted_contracts` (`consulted.py`)
- **Q9** (1): `Q9-a` put `identification` into the commensuration key (`estimand.py`, `commensuration_key`)
- **Q10** (2): `Q10-a` coerce a string estimand to a typed one in `restore` (`spec.py`); `Q10-b` report a pre-grammar spec as `derivation-malformed` (`audit.py`)

Both directions for every arm: the check passes against the real tree (`baseline`) and fails under the sabotage (`audit`). Acceptance: `python/tests/acceptance/test_estimand_acceptance.py`, one test per row named `test_q<n>_<slug>`, composed from the unit constructions over a registered durable corpus; Q10 reads the addendum's recorded values and asserts the driver's `rederive` report keys (`spec_restored`, `assessment_restored`, `belief_equal`, `prior_pre_grammar`) all `True`. Runner: `python/tools/cut31_acceptance.py`, `PREFIX_RUNNERS = ("cut30_acceptance.py",)`, `PHASE_MODULES = ("test_estimand_acceptance.py", "test_n2_cut31.py")`. Guard: `python/tests/acceptance/test_n2_cut31.py` on `test_n2_cut26.py`'s shape, pinning this document's SHA-256, the freeze commit and the declaration's SHA-256.

## 6. Second reader

Verify each fenced row byte-exact against the design's §8 table at the freeze commit; audit every selected clause against §2; force any unrun clause to remain deferred and its row partial. Challenge especially:

- that the estimand is built against the typed `Claim` and never from the wire, so two claims at one operator have two keys and the target check sees the bound arguments (Q3, Q6, Q9);
- that Q6's inconsistent stored pair — the target's true claim identity beside a different operator — is refused at import and contradicted under audit on the operator equality alone, and that the sabotage keeping only the identity equality lets it through;
- that Q9's scope counterexample is `commensurable` and not `co_scoped`, and that making either predicate raise leaves every P row passing;
- that Q10 restores from disk in a fresh process, that the prior corpus state reports `profile-mismatch: base` and nothing else, and that the pre-grammar codes fire only on a successor-pinned corpus holding a raw-written pre-grammar record;
- that the mm30 reproduction's re-authored spec is minted by `freeze` with no `supersedes`, and that its addendum records the scope judgment as a judgment;
- that Appendix A's encoding, once `beliefs-e48279` runs it, needs no member the fragment lacks.

## 7. Limitations

Design §13, restated: semantic match is authored, not guaranteed (1); the target check is corpus-local (2); direction and increment are not normalized (3); identification is authored and corpus-local (4); the qualifier home for "conditional on" and quantitative restrictions stays open (5); attenuation, model comparison and mediation are refused (6); TypeScript validates no estimand payload (7); `restore` and `analysis_spec_value` change signature across four callers (8); sample selection outside a declared dimension is invisible to both predicates (9); the reproduction's typed spec is a new spec whose scope equality with the prose one is a judgment no row certifies (10); a pre-grammar record is refused, never read (11); the interval constraint reaches as far as containment (12).

## 8. Supplements — 2026-09-15

Two corrections found while executing the implementation's Task 10 (the mm30
reproduction re-run), recorded here on cut 25's precedent: §§1–7 above are the
frozen body and are **not** edited. This section is dated and outside the
freeze — the guard's `_frozen_body` slicing runs from `## 2. The boundary` to
this heading — so the pin of this document at freeze commit
`c2a2211c2d9a0889a59e7892dcb71f2008e20e46`, SHA-256
`3cd4409dd08d5b121d3f62bfaaa00e3d553335d6a54e7657471c70677854d93f`, is
unchanged by it and is not re-taken. Neither correction adds a declaration
unit, a row or an arm: the accounting of §4 and §5 stands.

### 8.1 Q10's spec half of the transition clause is unreachable over the prior corpus

§3's Q10 asks that the prior corpus state's prose spec and assessment be
presented to the successor readers and assert `UnfreezableSpec("pre-grammar
spec")` **and** `MalformedRecord("pre-grammar assessment")`. Measured against
the corpus the driver moved aside (`.work/reproduction/mm30.cut22`), the
assessment half fires exactly as written — `assessment_value` over
`assessment:316272987716ac4f` raises `PreGrammarAssessment` through
`ReadView.iter_stored`, the unvalidated route `audit_corpus` itself takes.

The spec half cannot fire at any level, and not for the reason the audit half
gives. The 2026-09-05 spec record **predates the projection form**: its
`analysis-spec` facet carries the frozen members directly and has no
`projection` key, so `analysis_spec_value` refuses on the facet's shape with
`MalformedRecord` and `restore`'s `estimand_grammar` check — the only place
`PreGrammarSpec` is raised — is never reached. That record is
pre-*projection*, not merely pre-grammar.

`prior_pre_grammar` is therefore **defined**, not asserted, as the conjunction
of three measurements, and the driver's report derives it from them
(`docs/designs/2026-09-05-mm30-reproduction.md` §10.7, §10.8):

1. the prior corpus's assessment record raises `PreGrammarAssessment`;
2. the prior corpus's analysis-spec record returns **no typed value**;
3. `audit_corpus` over the prior corpus state under the successor profile
   reports exactly `profile-mismatch: base` and nothing else.

The codes `spec-pre-grammar` and `assessment-pre-grammar` are exercised where
§3 already says they are — on a corpus **pinned to the successor** holding a
raw-written pre-grammar record — by `test_estimand_acceptance.py::test_q10_…`,
`test_audit.py::test_pre_grammar_records_audit_under_their_own_codes` and
`test_world_audit.py::test_a_pre_grammar_spec_and_assessment_audit_under_their_own_codes_and_the_audit_continues`.
Filed as a step-10 `design-gap` finding in the reproduction's own
`findings.jsonl`; no row is weakened and none is re-classified, because the
requirement the clause exists for — *no reader returns a typed value for
either* — holds in both halves.

### 8.2 Q10's "same value under a different digest" is measured one level down

§3's Q10 asks that the belief re-derive to the **same value** under a
**different digest**. The value is `NoBelief(no-directional-outcome)` — the
outcome is `inconclusive`, which is the scientific result — and **a `NoBelief`
carries no `belief_input_digest`**; only a `Belief` does. There is no old/new
digest pair at the belief, and this cut does not invent one.

The digest half is therefore measured at the two identities that do move over
the same data and the same run inputs
(`2026-09-05-mm30-reproduction.md` §10.6):

| | prior corpus state | recreated corpus |
|---|---|---|
| spec identity | `86aaa1a8a8edda82…` | `10e8bfce1aaad8a9…` |
| assessment identity (derived) | `316272987716ac4f…` | `618c6c584da64b62…` |

with the belief value equal — `NoBelief(no-directional-outcome)` on both the
driver's derivation and the fresh process's. The acceptance unit reads both
identities and the equal value from the driver's recorded state by name.

### 8.3 Cut 22's frozen `M8a` arm went vacuous, and its check's premise was restored additively — 2026-09-16

Found by the discharge chain, not by the unit suite. `[cut22 phase 3/3]`
reported

    M8a: drop the sort-contract collection under a belief: vacuous:
    test_domain_facet_read.py::test_m8_an_editorial_bump_of_a_foreign_sorts_contract_leaves_claim_identity_and_moves_the_digest
    passed with the sabotage applied

`M8a` sabotages the claim walk's `for sort in operator.arg_sorts:` in
`consulted.py`, and its check was built so that the `testing` contract is
reached **only** through slot 1's argument sort. Q8's estimand walk
(`029babe`) gave `testing` a second route: the fixture's assessments in
`python/tests/test_domain_facet_read.py` carry a typed estimand whose
`estimands:` declaration is `testing`'s, so dropping the claim route no longer
removes the contract from the consulted set. The arm is **not stale** — its
`before` still matches, and its assertion is still true. What became false is
the **premise of the check it names**.

The repair is additive and inside the doctrine: the frozen declaration
`python/tests/n2_arms_cut22.py` and the sabotaged source `consulted.py` are
**untouched**; the test now also measures the claim's own route in isolation —
`consulted_contracts` called with no `estimands` supplied, asserting `testing`
is reached there — and every original assertion survives unchanged. Under the
`M8a` mutation that added assertion fails, so the arm selects again;
`certified.log`'s cut 22 phase reports `7 passed`, as before.

**This is precedent, and is written down as one.** The frozen-guard doctrine
covers a frozen arm whose *site* moves (the live-matcher migration) and a
frozen arm whose *assertion* is contradicted (a reopening). It is silent on a
frozen arm whose *check goes vacuous* because a later cut supplied a second
route to the thing the check isolates. The ruling taken here: restore the
check's premise **additively**, in the later cut's own tree, editing neither
the frozen declaration nor the source the arm sabotages, and show the arm
selecting again in the certified transcript. `test_domain_facet_read.py` lies
outside §2's file map; it was first touched by this lane at `029babe` for the
same interaction on a sibling test, which is what keeps the repair inside this
cut's boundary. Isolation by fixture alone was not available: the only contract
in the fixture set carrying an `estimands:` entry is `testing`, and
`crossing.yaml` — which would have to gain one — is outside §2.

**Two readings the implementation took, recorded so the reader need not
re-derive them.** `Q10-a`'s `after` block widens `restore`'s pre-grammar gate
rather than coercing a prose estimand into a typed one: `restore` then refuses
the projection as `MalformedRecord` instead of `PreGrammarSpec`, and the
acceptance check asserts the refusal **by its own name**, which is decision
10's content. `Q5-a` likewise selects on the refusal's **name**: the record
constructor re-runs `check_estimate`, so dropping the call in `assess.py` still
yields an `AssessmentFinding`, and the row's clause is *"an `AssessmentFinding`
naming the violation"* — the acceptance check asserts the finding carries
`check_estimate`'s own words. Both are readings of the rows' wording, taken
after review.

**`CUT31_DECLARATION_SHA256` is a content pin only.** Cuts 26 and 30 pin their
declaration to a commit as well, which this cut cannot do at the freeze commit:
the declaration is written after it. The declaration's commit is `2977a83`, and
the next cut pins it by adding `python/tests/n2_arms_cut31.py: 2977a83` to its
`FROZEN_PRIOR_CUT_FILES`, which is the ordinary way this becomes
commit-pinned.
