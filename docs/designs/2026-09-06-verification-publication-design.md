# Verification publication — design (the `verification-publication` slice)

**Date:** 2026-09-06
**Status:** designed 2026-09-06; **conformance cut 21 to freeze** after review,
before implementation. Not yet implemented.
**Scope:** the `write-path` lane's open boundary — roadmap tier 1, on the path,
row 1 (`../plans/2026-08-29-implementation-roadmap.md`). Durable publication of
verification records: a derived verification written into a corpus through
the ordinary write path as a record carrying its whole basis, the comparison
report included; one spelling for the assessment's run member, so that a
verification derived from two runs over a stored assessment both admits over
the corpus and audits clean; admission evaluated over records read back;
scope recomputed by the audit and the import from a stored verification,
closing cut 18 §7's limitation and R19's last stored-verification remainder;
and, as a rider, a builder and reader for the stored `analysis-spec` kind, so
that the audit's frozen specs come from the corpus. Both verification shapes
publish. No store change, no `atoms` or `nodes` change, no new record kind, no
new act kind, no permit-table change.
**Inherits:** the computation-reproducibility design
(`2026-08-02-computation-reproducibility-design.md`) §7.3–§7.3c — scope is
derived, the basis is the ordered runs, the rule, the report by identity, the
scope rule, the scope and the verdict, the scope evidence is embedded in the
report, and derivation is validated at explicit import and under audit and at
no other moment; the run-confinement design
(`2026-08-30-run-confinement-design.md`) §7.2, whose `admission_record` this
design leaves untouched and whose §10 finding this design is; cut 18's
rulings R2 (the optional `derivation` member), R3 (scope not recomputed —
lifted here), R11 (an unreadable neighbour leaves a derivation unchecked) and
R12 (`check_assessment` compares only the comparable members)
(`../plans/2026-09-04-conformance-cut-18-results.md` §3); the writer-session
design (`2026-09-05-writer-session-design.md`) §4.2–§4.3 and §5, which own
the write path a publication travels; the write-permits design
(`2026-09-04-write-permits-design.md`) §3.2, whose permit table this design
does not amend; and the mm30 reproduction record
(`2026-09-05-mm30-reproduction.md`) §3 rows 6–10b and §6, which measured the
three defects §1 names.
**Out of scope:** the `verify` command and every surface (the `science`
repository's command framework); cross-corpus recomputation through the world
resolver (`world-resolution`, R19's other remainder); a stored carrier for
rule implementations (code is held, never stored); the assessment's
`proposition` member's two namespaces (§9); where the scope-derivation rule
is versioned (§14); the biology pack and the facet declarations the `domain`
lane owns (§11).

**Sources, read at design time:** `python/src/beliefs/verify.py`, `audit.py`,
`evaluation.py`, `admission.py`, `closure.py`, `record.py`, `stored.py`,
`runrecord.py`, `replay.py`, `spec.py`, `evidence.py`, `verification.py`,
`corpus.py` (`eligibility_refusal`, `_refuse`, `_refuse_family_kinds`,
`_validated_import_bundle`), `session/writer.py`, `intents/shapes.py`,
`permit.py`; `python/tools/reproduction/run.py`, `belief.py`, `rederive.py`,
`spec.py`, `close.py`; `python/tests/test_verify.py`, `test_audit.py`,
`test_import_derivation.py`, `acceptance/n2_arms_cut19.py`,
`acceptance/test_n2_cut19.py`, `tools/cut19_acceptance.py`; the sibling
lane's facet-contracts design of 2026-09-05, §4.2, §5.1, §5.2, §5.5 and §11
(read in `.worktrees/domain-boundary`; not on this branch).

---

## 1. Problem

The mm30 reproduction record walked from a registered world to the belief
evaluator's answer over one real proposition and stopped one step short of
the success criterion's `verify` step, for three reasons it measured
(`2026-09-05-mm30-reproduction.md` §3 rows 7–10b, §6):

1. **No stored record carries the comparison report** (row 10b,
   `comparison_report_stored` false). `build_verification` derives a
   `ComparisonReport` — both executions' conformance results, the two
   receipts, the rule bindings, the certification, the citation, the
   diagnostics — and digests it into the verification's basis, and then the
   only record written (`stored.verification_node`) keeps the assessment
   identity, the scope, the verdict, an optional `supersedes` and the two
   run refs. The report, the rule identity and the scope-rule identity are
   dropped on the floor. Scope and verdict *recompute* from the two stored
   closures and agree, but only with the in-process `FrozenSpec` and rule
   implementations; nothing is recovered from the corpus alone.
2. **Two spellings of one identity** (rows 6 and 8). `build_assessment` and
   `build_verification` digest the assessment basis with `run` as the bare
   closure address; `stored.assessment_node` stores `run:<address>` (the
   corpus ref `eligibility_refusal` resolves), and `stored.assessment_value`
   hands that typed ref back, so the stored record's identity differs from
   the derived one. `gather` selects verifications by the *stored* identity;
   the audit's `check_verification` accepts only the *derived* one. A
   verification naming the derived identity passed the audit and was refused
   at admission on a `clean-environment` pass; the belief was
   `NoBelief(no-eligible-assessment)` for that reason and no other.
3. **Scope is not recomputed** (cut 18 §7, ruling R3). Without the stored
   certification the audit and the import recompute the verdict and the
   assessment identity only, so a stored scope raised by hand from
   `same-environment` to `clean-environment` passes both. That is the
   fourth R19 limitation and the one this boundary was named for.

And one adjacent gap the record filed to whichever kernel lane next rewrites
`stored.py` or `verify.py` (§6 step 4, task `beliefs-91aac6`): `analysis-spec`
is a stored kind with a semantic domain and an import check, and no kernel
builder or reader — the reproduction hand-built its record and nothing
restores a `FrozenSpec` from it.

The ledger's row for this boundary (`2026-08-03-redesign-adoption-ledger.md`
Current state) states the deliverable: "a derived verification written into a
corpus through the operation port, with admission evaluated over records read
back … scope recomputation for a stored verification … a computed belief
re-derivable from the corpus alone."

## 2. Decisions

1. **One spelling rule.** A stored facet spells a reference to a record
   *typed*, as `kind:local`; a derived value spells an identity *bare*. A
   reader that hands a value to the derivation layer strips exactly the kind
   prefix and a resolver that reads a record adds it, through one helper pair
   in `stored` (§3). `AssessmentValue.run` is therefore the bare run address —
   the run's world identity — on both the derived and the stored side, and
   `(spec, run, proposition)` digests the same bytes wherever it is computed.
   The identity moves for every stored assessment; no corpus migrates (§3.3).
2. **The stored verification carries its whole basis.** The facet gains
   `rule`, `scope_rule`, `report` and a typed `supersedes`; the two runs stay
   under `derivation`. The report is the `ComparisonReport`'s canonical
   projection, embedded as a structured mapping — the same bytes its
   `identity()` digests — so the record is the report's preimage, as a run
   record is its closure's (§4.1). The node id is `verification:<identity>`,
   and a reader recomputes the identity from the members and refuses a node
   whose id disagrees (§4.2). The computation design's "embedded, not
   referenced" holds one level up: the report travels inside the verification.
3. **Absence of a report is not malformedness.** A verification carrying no
   `report` decodes as *absent* — the reader returns `None` — and is never
   refused for that: cut 18's ruling R2 stands, existing fixtures and the
   reproduction corpus's verification stay valid, and such a record is one the
   audit checks as far as it can (verdict and identity) and no further. A
   `report` that is present and malformed is refused, never repaired (M11).
4. **Publication is an ordinary `add`.** One total projection in `verify`
   turns a derived verification into a node; the caller adds it through the
   `CorpusWriter`, the `OperationWrites` facade or a `ScopedWriter`, so a
   session-mediated publication is one `corpus-write` intent and one
   fulfilling registration under the session actor (writer-session J1) and a
   library publication is a plain write. No new act kind; `KIND_ACTS`'s
   `verification` row stays `{corpus-write}`; the write-permits design's
   invitation to add `run` (§3.2 there) is declined (§12).
5. **Both shapes publish.** The projection is total over `RunVerification`:
   an `AssessmentVerification` publishes with its `verifies` edge and its
   `assessment` member; a `DatasetProductionVerification` publishes with no
   edge and no `assessment` member, and gates nothing (kernel §3.3). The
   projection refuses the cross: an assessment shape without an
   `assessment_ref`, or a production shape given one.
6. **Forgery is refused before the intent, as malformedness.** The write
   preflight gains one verification step, under the operation lock, after
   document validation and before the intent append, and in the import
   bundle's union view: for a node carrying a report, the identity
   recomputes to the id, the report's own identity equals the basis member,
   and the `verifies` target resolves to an assessment whose stored identity
   equals the `assessment` member. Each failure is a refusal and nothing is
   appended (§5.3). This is the reader's self-consistency, not derivation
   validation: reading still never validates, and the two validation moments
   stay explicit import and audit (computation §7.3c).
7. **The audit recomputes scope.** Over a stored verification with a report,
   `check_verification` recomputes both conformances, the receipts, the rule
   binding, the scope through the stored certification, the verdict, the
   report identity and the assessment identity, and reports every
   disagreement under the existing `verification-derivation-contradicted`
   code (§6). Over one without a report it keeps cut 18's verdict-and-identity
   path. The import inherits both through the same function.
8. **One derivation, two callers.** `build_verification` and
   `check_verification` share one private derivation helper in `verify`, so
   the audit recomputes through the constructor's own steps. The constructor's
   argument list stays closed (R19): the helper is private and takes closures
   and evidence, never a report.
9. **The report's construction authority stays in `verify`.** The reader
   restores a `ComparisonReport` through the same private mint the
   constructor uses, after recomputing the identity the record's basis names;
   no public constructor is added. `EmbeddedCitation` and
   `CodeLineageCertification` restore through their public dataclass
   constructors, which already validate.
10. **The analysis-spec rider.** `stored.analysis_spec_node(spec)` projects a
    `FrozenSpec` to a stamped node under `analysis-spec:<identity>`;
    `stored.analysis_spec_value(node)` restores it through a new restoring
    mint in `spec` that recomputes the identity and refuses a mismatch (§7).
    `audit.stored_specs(view)` collects them for `DerivationEvidence.specs`.
    Rule implementations stay in-process: code is held, not stored.
11. **The slice mints its own guarantee table**, `V1`–`V8` (§8), the way the
    writer session minted `J1`–`J11` before it was built: this boundary
    entered the ledger on cut 13 §2's named exclusion with no guarantee row,
    and a cut needs rows to select. R19's stored-verification limitation
    closes by V4; no row of another table is selected.
12. **Identity consequences are accepted, not migrated.** Assessment
    identities move (decision 1), so every belief input digest moves and every
    verification's `assessment` member over an existing corpus is stale. The
    reproduction corpus is re-run into a fresh directory, which the `domain`
    lane's decision 13 already schedules; the lane that merges second re-runs
    it (§11).

## 3. One spelling — the identity fix

### 3.1 The helper pair

`stored` gains two functions, the only place the kind prefix is added or
removed:

```python
def typed_ref(kind: str, local: str) -> str      # "run", "9700c4…" -> "run:9700c4…"
def local_id(kind: str, ref: str) -> str         # "run", "run:9700c4…" -> "9700c4…"
```

`typed_ref` refuses a `kind` outside `WORLD_KINDS` and an empty or
already-prefixed `local`; `local_id` refuses a `ref` that does not begin with
`f"{kind}:"` — both with `MalformedRecord`. Neither validates a closure
address: `runrecord.run_ref` and `bare_address` keep that job for the run
boundary, and `run_ref(address) == typed_ref("run", address)` by construction
(a test pins it). Hand-built fixtures whose runs are slugs (`run:r1`) remain
representable.

### 3.2 Where each spelling lives

| site | today | after |
|---|---|---|
| `record.AssessmentValue.run` | bare on the derived side, typed on the stored side | bare, both sides; the docstring says so |
| `stored.assessment_value` | `run=str(facet.get("run", ""))` | `run=local_id("run", facet["run"])`; a facet whose `run` is absent, not a string, or not `run:`-prefixed is `MalformedRecord` (M11) |
| `stored.assessment_node` | stores the caller's `run` | unchanged: the caller passes the typed ref, as today; the docstring names decision 1 |
| `admission.admit` | `run.ref != assessment.run` | `run.ref != typed_ref("run", assessment.run)` |
| `evaluation.gather` | `view.holds(a.run)`, `run_value(view, a.run)` | `ref = typed_ref("run", a.run)` for both; `runs` stays keyed by `a.run` and the trace row stays `("run", a.run)` — the value's spelling, matched by `declared_refs` |
| `audit._assessment_disagreements` | `stored_value.run != run_ref(derived.run)` | `stored_value.run != derived.run`; the docstring's normalization clause goes |
| `verify.build_verification`, `audit.check_verification` | digest `"run": original.address()` | unchanged — already bare |
| `corpus.eligibility_refusal` | reads the facet's typed ref directly | unchanged |

`RunValue.ref` stays typed: it is a record's address, read from the corpus,
and nothing digests it.

### 3.3 What moves

`AssessmentValue.identity()` over a stored assessment now equals the derived
identity, so:

- `gather`'s `ids` and `admit`'s `uid` agree with `admission_record`'s
  `assessment` member, and the reproduction's step 8 admits (V2).
- Every belief input digest over an existing corpus moves, because
  `assessment_facets` digests `(identity, facet_digest)` pairs. No stored
  digest is a claim any record carries, so nothing on disk is stale by that
  alone.
- Every existing verification's `assessment` member, if it was written from
  a stored identity, names an identity no assessment now carries. The
  reproduction corpus's verification was written from the *derived*
  identity and is unaffected; test fixtures that hard-code a stored identity
  are rewritten in the plan.

The failing test the roadmap names is written first, as the plan's first
task: over a corpus holding a dataset, a proposition, an assessment-shaped
run, its stored assessment and a replay, `build_verification` →
`publication_node` → `add`, then `gather` → `admit` is `Admitted` and
`audit_corpus` reports no contradiction. On `main` today the first assertion
fails with `not-admitted-verification-state`.

## 4. The stored verification

### 4.1 The facet

The `verification` facet, as `publication_node` writes it (all members
required in a published record; `assessment` and the `verifies` edge only for
the assessment shape):

```yaml
verification:
  assessment: <assessment identity, bare>          # assessment shape only
  scope: clean-environment
  verdict: passed
  supersedes: verification:<identity>              # optional, typed
  derivation:
    original: run:<address>                        # typed, as cut 18 R2 wrote it
    replayed: run:<address>
  rule: <equivalence-rule identity>
  scope_rule: <scope-derivation rule identity>     # from the original recipe's boundary policy
  report:                                          # ComparisonReport.projection()
    original_conformance: conforming
    replay_conformance: conforming
    receipts: [<receipt identity>, <receipt identity>]
    rule_bindings: [[<rule>, <implementation identity>]]
    diagnostics: []
    certification: {rationale: …, attribution: …}  # present iff relied on
    citation: {report_ref: …, index: 0, content: {…}}   # present iff supplied
```

`ComparisonReport.projection()` becomes public and is exactly the mapping
`identity()` digests today; `identity()` calls it. The facet is covered by the
semantic stamp already (`COVERED_FACETS["verification"]`), so a published
record's stamp covers the report. The record ceiling is unchanged and the
report is small; an embedded citation's `content` is bounded by the act
report it was cut from.

`stored.verification_node` keeps its signature and gains nothing: it remains
the hand-built shape (no `rule`, `scope_rule` or `report`), which is what
decision 3 preserves. `stored.verification_value` and
`stored.verification_derivation` are unchanged; `verification_value` still
reads `supersedes` as a ref, which now is one.

### 4.2 The id and the reader

`publication_node` mints `id = f"verification:{derived.identity()}"`. The
reader, in `verify`:

```python
@sealed @final @dataclass(frozen=True)
class StoredVerification:
    original: str            # bare run address
    replayed: str
    assessment: str | None   # bare identity; None for the production shape
    rule: str
    report: ComparisonReport
    scope_rule: str
    scope: str
    verdict: str
    supersedes: str | None   # bare verification identity
    def basis(self) -> dict[str, object]   # verify._basis over these members
    def identity(self) -> str              # v1.digest(RUN_VERIFICATION_DOMAIN, basis)

def decode_verification(node: Node) -> StoredVerification | None
```

`decode_verification` refuses a node whose kind is not `verification`. It
returns `None` when the facet carries no `report`. Otherwise every member is
required and typed exactly: `derivation` through `stored.verification_derivation`
(its `MalformedRecord` propagates), each run through `local_id("run", …)`;
`supersedes`, if present, through `local_id("verification", …)`; `report`
through `_restore_report`, which requires the projection's key set exactly
(`certification` and `citation` optional), restores `CodeLineageCertification`
and `EmbeddedCitation` through their constructors and the report through
`_mint_comparison_report`; `assessment` present iff the node carries a
`verifies` edge, and exactly one such edge. Then `identity()` is recomputed
and compared to `local_id("verification", node.id)`; a disagreement is
`MalformedRecord("… the recomputed identity is not the record id")`. Nothing
here reads another record: the reader is a pure function of the node, as
`decode_run_record` is.

`StoredVerification` is a distinct type from `AssessmentVerification` and
`DatasetProductionVerification` by design: those are minted only by the
constructor and R19 asserts no constructor accepts a report; this one is
minted only by the reader and carries the same basis. `admission_record` is
untouched and still takes the derived type; admission over the corpus reads
`stored.verification_value`, as it does today, and never needs the report.

### 4.3 No import cycle

`verify` imports `stored` for `typed_ref`/`local_id` and `verification_derivation`;
`stored` imports `verification`, `record`, `report`, never `verify`;
`audit` already imports `verify` (`_resolve_rule`); `corpus` imports `audit`
locally inside `_validated_import_bundle` and imports `verify` the same way,
locally inside the new preflight step (§5.3), for the reason the existing
comment gives — `audit` imports `corpus`. `spec` imports nothing new;
`stored` gains an import of `spec` for the rider (§7), and `spec` does not
import `stored`. A test asserts the module graph is acyclic, as
`test_facet_seams` does in the sibling lane.

## 5. Publication

### 5.1 The projection

```python
def publication_node(derived: RunVerification, *, assessment_ref: str | None = None) -> Node
```

Total over the two derived types; refuses anything else with
`MalformedRecord`. For an `AssessmentVerification`, `assessment_ref` is
required and must be `assessment:`-prefixed (`local_id` refuses otherwise);
the node carries `assessment=derived.assessment`, the facet of §4.1 and one
`Relation(source=id, predicate=VERIFIES, target=assessment_ref)`. For a
`DatasetProductionVerification`, `assessment_ref` must be `None` and the node
carries no edge and no `assessment` member. `title` is
`f"verification of {assessment_ref}"` or `"dataset-production verification"`;
prose is outside the stamp. The node is built through `stored._node`'s
public twin, `stored.governed_node(kind, local, title, facets, relations)`,
which stamps it — the one construction authority for the stamp
(`stamp_semantic_identity`) is unchanged. `publication_node` is pure: it
reads no view, holds no lock, and is checked by `decode_verification(node)`
round-tripping to a `StoredVerification` whose basis equals `derived.basis()`.

### 5.2 The write path

Nothing new. A library caller does `writer.add(publication_node(…))`; a
session caller does `scoped.add(…)`. The writer-session design's `_commit`
order holds unchanged: `require("corpus-write", ("verification",))`, prepare
(`_prepare_add` → `_refuse_family_kinds` → `_refuse`, now including §5.3),
port preflight (plan shape, reserved leaf, record ceiling), intent append
under the session actor, `execute_fulfilling`, reconstruct. Every refusal
precedes the intent. The registration is the fulfillment; no act-report is
minted. A session-published verification is byte-identical to a library
publication of the same node (writer-session J10).

### 5.3 The preflight refusal

`CorpusWriter._refuse` gains one call after `_refuse_invalid` and before the
stamp check, for `node.kind == "verification"` only:

```python
def _refuse_verification(self, node: Node, *, view: ReadView | _ImportView) -> None
```

Under the operation lock (it is inside `_refuse`, which `_commit`'s prepare
step and `_validated_import_bundle` both call under it), before any effect:

1. `decoded = decode_verification(node)` — a `MalformedRecord` propagates as
   the refusal, exactly as `verification_derivation`'s does in the audit
   ("refuse, never repair"). This is where a forged id, a forged report
   identity, a second `verifies` edge, or an `assessment` member on an
   edge-less node is caught.
2. If `decoded is None` — no report — return. A hand-built verification is
   admitted on today's terms (decision 3).
3. Otherwise the `verifies` target must resolve in `view` (the writer's view
   for `add`, the union for import) to a node of kind `assessment` whose
   `stored.assessment_value(...).identity()` equals `decoded.assessment`;
   else `VerificationTargetMismatch(WriteRefused)` naming the target and
   both identities. The production shape has no edge and skips this step.

No recomputation from the runs happens here: the runs need not resolve for a
publication to be accepted (a verification may be published into a corpus
that holds only the assessment), and derivation validation belongs to the
import and the audit alone. Effects: none; the chain head after a refusal
equals the head after settlement, and under a session no intent is appended
(J1's refusal clause, re-read here for the new refusal).

### 5.4 The import

`_validated_import_bundle` already runs `_refuse` over the union and then
`check_verification` per verification member, refusing on a contradiction
and adding `derivation-unchecked` findings otherwise. With §5.3 in `_refuse`
and §6 in `check_verification`, an imported verification with a report is
checked for self-consistency, its target, and — where both runs resolve in
the union — its full derivation, scope included, before any payload write.
R19's frozen "fabricated report … refused before any write" arm is now
reachable and is V5's import half. An import whose runs do not resolve
proceeds unchecked with its finding, as cut 18 rules.

## 6. The audit

`check_verification(view, node, *, evidence)` keeps its signature and its
early returns (no derivation member → unchecked; a run that does not resolve
or decode → unchecked with the reason; `RuleUnbound` → unchecked; mixed
shapes → unchecked). After resolving the rule it calls the shared derivation
helper (decision 8):

```python
def _derive(original, replayed, *, specs, held_rules, certification, citation) -> _Derived
# _Derived: rule, implementation_identity, report, scope, verdict, assessment (or None)
```

with `certification` and `citation` taken from the stored report when the
node decodes to a `StoredVerification`, else `None` (a report-less
verification derives with neither, as today). Then:

| compared | report-less (cut 18's path) | with a report |
|---|---|---|
| verdict | stored vs recomputed | same |
| assessment identity | stored vs recomputed (bare, both) | same |
| rule | — | `decoded.rule` vs the resolved rule |
| scope rule | — | `decoded.scope_rule` vs `original.recipe.boundary_policy.scope_rule` |
| scope | — | `decoded.scope` vs `derive_scope(original, replayed, certification=decoded.report.certification)` |
| report | — | `decoded.report.identity()` vs the recomputed report's identity |

Every disagreement is one clause of the `verification-derivation-contradicted`
finding's detail (`scope stored='clean-environment' recomputed='same-environment'`,
`report identity differs`, …); the outcome is `checked` with no contradiction
only when every compared member agrees. The recomputed report's certification
and citation are the stored ones — they are authored claims the constructor
embeds and cannot be derived from the runs (computation §7.3b) — so a report
whose *receipts*, *conformances*, *rule bindings* or *diagnostics* were
altered contradicts by identity, and a raised scope contradicts by
recomputation. A report whose certification was altered contradicts only if
the scope no longer derives (the `independent-implementation` row): the
design keeps the computation design's stated bound that a certification
found false is remedied by a superseding verification, never detected by
the audit.

`audit_corpus` is unchanged in signature and control flow: it still dispatches
on kind, still leaves a bad neighbour unchecked (R11), and still mints
nothing. `stored_specs(view) -> Mapping[str, FrozenSpec]` is added beside it:
it iterates `analysis-spec` records, restores each through
`stored.analysis_spec_value`, and returns them keyed by identity; a record
that fails to restore is skipped with no finding here — it is `corpus_check`'s
stamp finding and `_refuse`'s import refusal, by the same reasoning R11
gives — and the caller composes `DerivationEvidence(specs=stored_specs(view) | in_process, …)`
explicitly. Nothing reads specs ambiently.

## 7. The analysis-spec record

`spec` gains one restoring mint:

```python
def restore(facet: Mapping[str, object]) -> FrozenSpec
```

`facet` is `_facet_projection`'s mapping plus `identity`. `restore` requires
the key set exactly, decodes `input_roles` (with their optional `exclusion`),
`parameters` through the inverse of `_project_parameter_value` (so a `Decimal`
round-trips as a `Decimal`), `nondeterminism` through the three projections'
inverse, `rule_bindings` as pairs and `supersedes` as optional; recomputes
`v1.digest(SPEC_DOMAIN, projection-without-identity)` and refuses a
disagreement with the facet's `identity` (`MalformedRecord`); and mints
through `_mint_frozen_spec`, the private mint `freeze` and `revise` use.
`FrozenSpec`'s docstring widens from "minted by freeze or revise" to name
`restore`.

`stored.analysis_spec_node(spec: FrozenSpec) -> Node` writes the facet above
under `analysis-spec:<identity>` through `governed_node`, stamped, with no
relations (the `executes`/`targets` edges are the run's and the assessment's).
`stored.analysis_spec_value(node) -> FrozenSpec` requires the kind, reads the
facet, restores through `spec.restore`, and refuses a node whose id is not
`typed_ref("analysis-spec", spec.identity)`. The reproduction driver's
hand-built `spec_record` is replaced by the builder and its finding closes.

The `_refuse` preflight does not gain a spec step: the stamp already covers
the facet, the import's r20 check stands, and a facet whose identity
disagrees with its members is caught by `analysis_spec_value` wherever a
reader restores it. This is the same line §5.3 draws for the verification:
self-consistency at the reader, refused at write only where a write reads.

## 8. Guarantees

The `V` table. Rows are frozen; ids are never renumbered.

| # | Guarantee | Mutation test |
|---|---|---|
| **V1** | A published verification is recoverable from the corpus alone: `decode_verification` over the stored record restores a `StoredVerification` whose basis equals the derived value's member for member, whose report's identity equals the derived report's, and whose scope and verdict are *read*, not recomputed; `comparison_report_stored` is true in the reproduction's step 10b and scope and verdict read equal | Derive a verification over two published runs, publish it, reopen the corpus in a fresh process, decode, and assert `basis()` equality, report identity equality, `identity()` equal to the record id, and that the decode performed no run read (the runs deleted first). Run the reproduction driver's 10b and assert `comparison_report_stored` true, `scope_equal` and `verdict_equal` true, and the *corpus* input list naming the verification record alone for the report. **Negative:** the same record with its `report` member removed decodes as `None`, and 10b reports false |
| **V2** | One identity: the assessment identity a stored assessment reads back is the identity its run derives, so a verification derived over an original and a replayed run of a stored assessment both admits over the corpus and audits without contradiction; and `AssessmentValue.run` is the bare run address on both sides | The roadmap's failing test, first: publish a dataset, a proposition, an assessment-shaped run, its assessment and a replay; `build_verification` → `publication_node` → `add`; `gather` → `admit` is `Admitted`; `audit_corpus` has no `verification-derivation-contradicted` and no `assessment-derivation-contradicted`; `evaluate_over` answers a `Belief`. Assert `stored.assessment_value(node).run` has no `run:` prefix and equals `build_assessment(closure).run`; assert `run_ref(a) == typed_ref("run", a)`. **Negative:** an assessment facet whose `run` is bare or absent is `MalformedRecord` from `assessment_value`; `admit` with a `RunValue` whose ref is another run is `run-mismatch` |
| **V3** | Admission is evaluated over records read back: `gather` selects a stored verification by the stored assessment's identity, `admit` reads its scope and verdict from the record, and the belief moves with the record — deleted, it no longer admits; superseded, it is no longer active | Over V2's corpus assert `Belief`; `delete` the verification through the writer and assert `NoBelief(no-eligible-assessment)`; publish a second verification whose `supersedes` names the first and whose verdict is `failed`, and assert `invalidated` and `NoBelief`. Assert the belief input digest equals the one computed in a fresh process over the same corpus (10a). **Negative:** a verification published against a *different* assessment ref with the same identity is refused by V5, so the gathered set never contains it |
| **V4** | Scope is recomputed over a stored verification: the audit and the import recompute scope through the stored certification and the report by identity, and a stored member that disagrees — scope raised, verdict flipped, a receipt or conformance altered in the report, the rule or scope rule renamed — is `verification-derivation-contradicted` naming the member; a report-less verification is checked for verdict and identity only, as cut 18 rules; and `check_verification` reaches the same verdict whether the evidence's spec is in-process or restored from the corpus | Raw-write V2's published record with `scope: clean-environment` over a pair whose replay receipt does not qualify (or with the verdict flipped, a receipt identity changed, `original_conformance` changed, `rule` renamed, `scope_rule` renamed, each separately, stamp recomputed so the stamp check passes) and assert one finding per case with the member in `detail`; import each as a bundle member with both runs resolvable and assert `ImportRefused` before any file exists. Run the same audit with `evidence.specs` from `stored_specs(view)` alone and assert equal outcomes. **Negative:** the unaltered record audits `checked` with no contradiction; the same alterations on a report-less record are detected only where cut 18 detected them (verdict, identity) |
| **V5** | Forgery is refused before the intent and before any write: a verification whose id disagrees with its members, whose report identity disagrees with its basis, which carries an `assessment` member without a `verifies` edge or two edges, or whose `verifies` target resolves to no assessment or to one of another identity, is refused at `add` and at import with the chain head unchanged and no intent appended | Through a scoped writer over a registered root, `add` each forged node and assert the refusal type (`MalformedRecord` for the first three, `VerificationTargetMismatch` for the last two), the head equal to the head after settlement, no intent decoding to the invocation's token, no record file, and no `act` line; import the same as bundle members and assert `ImportRefused` with no file. **Negative:** the well-formed node is one intent and one fulfilling registration (J1), and a report-less hand-built node with an unresolvable target still adds, as today |
| **V6** | A verification without a report is not malformed: it adds, imports unchecked with `derivation-unchecked`, and audits on cut 18's terms; `stored.verification_node`, `verification_value` and `verification_derivation` are unchanged in signature and result | Add cut 18's fixture verifications (no derivation; derivation without report) through the writer and through import; assert acceptance, the `derivation-unchecked` finding on import, and `check_verification`'s outcome equal to cut 18's on the same fixtures. **Negative:** a `report` member that is present and malformed (a missing key, a receipts list of one, a non-string diagnostic) is `MalformedRecord`, at `add`, at import and in the audit |
| **V7** | The production shape publishes: a `DatasetProductionVerification` becomes a record with no `verifies` edge and no `assessment` member, decodes to a `StoredVerification` with `assessment` `None`, is never selected by `gather`, and admits nothing; `admission_record` still refuses it | Publish one over a dataset-production pair; assert the record's relations are empty, the facet has no `assessment`, `decode_verification` round-trips, `gather` over every proposition selects it never, and `admission_record` raises `NotAnAssessmentVerification`. **Negative:** `publication_node` refuses a production shape given an `assessment_ref` and an assessment shape given none |
| **V8** | The analysis-spec record round-trips: `analysis_spec_node` writes a stamped record under `analysis-spec:<identity>` and `analysis_spec_value` restores a `FrozenSpec` equal member for member and by identity; a facet whose identity disagrees with its members, or a node whose id disagrees with its identity, is `MalformedRecord`; `stored_specs` supplies the audit; and the reproduction's step 10b lists the rule implementations as its only in-process input | Freeze a spec with a `Decimal` parameter, a seeded nondeterminism and an exclusion; build, add, reopen, restore and assert equality of every member and `identity`; alter one member raw and assert `MalformedRecord`; rename the id and assert `MalformedRecord`; run the audit with `stored_specs(view)` only and assert V2's outcome. Run 10b and assert `in_process == ["interpretation and equivalence RuleImplementations"]`. **Negative:** `restore` of a facet with an extra key or a missing `identity` is `MalformedRecord`; the constructor's argument list is still closed (R19's arm re-run) |

## 9. Limitations

- **The `proposition` member keeps two namespaces.** The derived value carries
  the spec's `target` and the stored facet the proposition record's corpus
  ref; cut 18's ruling R12 excludes it from `check_assessment` for that
  reason, and the reproduction met it only because its spec's target *is* the
  corpus ref. This design does not unify them: the layer design's claim
  sub-project, which authors specs against typed claims, owns where a target
  is a claim identity. Until then the identity fix is exactly the run member.
- **Derivation validation stays corpus-local.** `check_verification` resolves
  the two runs in the view given; a run held only in another corpus leaves
  the verification unchecked with its reason. Cross-corpus recomputation is
  `world-resolution`'s (R19's other remainder).
- **A false certification is not detected.** The audit recomputes scope
  *through* the stored certification. The computation design's remedy — a
  superseding verification — is unchanged.
- **The rule implementations are in-process.** 10b's last in-process input
  is code. A stored carrier for rule implementations is not proposed.
- **The stamp covers a published record's report; a report-less record's
  stamp covers what it carries.** Nothing here re-stamps existing records.
- **Belief input digests move** for every corpus (decision 12). Nothing on
  disk names one, so nothing goes stale, but a caller comparing a digest
  computed before this slice to one computed after sees a difference that is
  this slice's, not the corpus's.

## 10. Conformance cut 21

The `domain` lane froze cut 20 on its branch on 2026-09-05
(`.worktrees/domain-boundary`, its cut 20 document); a number
is claimed at freeze in freeze order (roadmap rule 1), so this cut takes 21
and names `cut20_acceptance.py` as its prefix runner. By rule 5 it discharges
after cut 20 does, on the merged tree; implementation and the portable suite
do not wait.

### 10.1 Selection

Every row of §8 in full: V1–V8. Eight rows, eight selected units. R19 is
re-read, not selected: its stored-verification limitation (cut 18 §7,
roadmap Appendix C) closes by V4, and the cut's results record says so; its
cross-corpus arm stays with `world-resolution`. J1 and J10 are re-read by V5:
the new refusal is one more refusal that precedes the intent, and a
published verification is one more record indistinguishable from a library
write. No row of another table is selected.

### 10.2 Where the arms live

**Portable suite** (no host prerequisite): `test_verify.py` — V1's
round-trip, V7, the closed-constructor re-run, `projection()`; `test_stored.py`
— the helper pair, `assessment_value`'s strictness, `analysis_spec_node`/`_value`;
`test_spec.py` — `restore`; `test_audit.py` — V4's contradictions over an
in-memory corpus, `stored_specs`; `test_import_derivation.py` — V4's and
V5's import halves; `test_evaluation.py` / `test_admission.py` — V2's
spelling, V3's selection; `test_operation_writes.py` — V5's refusals through
`OperationWrites` with the test port.

**Durable suite**, on the certified volume beside the checkout:
`acceptance/test_verification_acceptance.py` — V1, V2, V3 and V5 through
`open_attended_session` over a registered, adopted root with the real
`DurableOperationPort`, runs published by the run boundary; V8's 10b arm and
V1's 10b arm through the reproduction driver over a fresh
`.mm30-reproduction/` directory.

### 10.3 N2

`acceptance/n2_arms_cut21.py` declares one lettered arm per selected unit
with its sabotage in `verify.py` (drop `report` from the projection; skip
the identity recomputation in `decode_verification`; accept a projection with
a missing key; write `assessment` for the production shape; compute the
assessment digest over the typed ref), `stored.py` (return the typed ref from
`assessment_value`; strip nothing in `local_id`; skip the identity check in
`analysis_spec_value`), `admission.py` (compare `run.ref` to the bare
address), `evaluation.py` (resolve `a.run` untyped), `audit.py` (skip the
scope comparison; skip the report comparison; take `certification=None` for a
decoded report; compare `stored_value.run` through `run_ref` again),
`corpus.py` (call `_refuse_verification` after `append_intent`; return before
the target check; resolve the target in `self._view` instead of `view` for
import), `spec.py` (skip `restore`'s identity check; project a `Decimal` as a
string). `test_n2_cut21.py` audits them by the cut-12 pattern, with the
staleness probe's baseline taken from the tree, and `tools/cut21_acceptance.py`
runs `PREFIX_RUNNERS = ("cut20_acceptance.py",)` then its phase modules.

## 11. What changes elsewhere

- **The `domain` lane** (its facet-contracts design of 2026-09-05, in its
  worktree) rewrites three surfaces this design touches; the later merge
  resolves toward the earlier (roadmap rule 3), and this section names the
  resolution for each:
  - `corpus.py`: that lane inserts `_refuse_facets` in `_refuse` after
    document validation; `_refuse_verification` lands after it and before the
    stamp check. Its `CorpusWriter(profile=)` keyword and the port's profile
    recheck do not touch this design's calls.
  - `audit.py`: that lane widens `audit_corpus(view, *, evidence, profile)`
    and `eligibility_refusal(view, node, profile)`; this design changes
    `check_verification`'s body and adds `stored_specs`, neither of which
    takes the profile. V4's arms assert under an agreeing profile.
  - `stored.py`: that lane declares the `verification` facet `shape: reader`
    with readers `verification_value` and `verification_derivation`, and the
    `analysis-spec` facet with reader `stored.analysis_spec_value`. After
    both merge, the `verification` declaration names `verify.decode_verification`
    as a third reader (so `_refuse_facets` accepts the new members) and the
    `analysis-spec` reader is the one §7 builds. That is one line in the base
    contract's `facets:` and one row in that design's reader table, made by
    whichever lane merges second.
  - The reproduction corpus: both lanes re-run the driver into a fresh
    directory (their decision 13, this design's decision 12); the second
    merge re-runs it once.
- **Computation design** §7.3b–§7.3c: a dated note that the stored record
  carries the report's projection and that scope recomputation lands here;
  §13's first open question (a publishable belief-input snapshot) unchanged.
- **Run-confinement design** §10: the roadmap finding "verification
  publication crosses the persistence seam" is closed by citation.
- **Cut 18** results §3 ruling R3 and §4's "scope is not recomputed": a dated
  note citing V4.
- **Ledger** Current state: the `verification-publication` row moves to "its
  slice design written 2026-09-06, cut 21 to freeze"; at discharge the row
  leaves and R19's remainder is restated as the cross-corpus arm only.
- **Roadmap**: at discharge, tier 1 row 1 leaves, `write-path`'s next boundary
  is none until `world-resolution` opens, Appendix A gains the `V` table and
  Appendix C drops R19's row.
- **Guide**: `computation-and-reproducibility.md` "Current state" drops
  "durable verification publication" from the owned-elsewhere list and cites
  this design; `glossary.md` gains "Published verification"; `open-questions.md`
  gains §14's entry.
- **README**: the designs count and date range; the `V` table in the row
  total (180 rows in fifteen frozen tables); the design's row in the table.
- **`python/tests/test_designs_corpus.py`** and **`tools/roadmap_status.py`**:
  the `V` table registered, this document as its owner, the prefix
  character classes widened.
- **The reproduction driver**: `belief.py` step 8 publishes through
  `publication_node`; `rederive.py` step 10b reads the report and relabels
  its inputs; `spec.py` uses `analysis_spec_node`; `close.py` passes
  `stored_specs(view)` into its evidence.
- **Tasks**: `beliefs-754995` carries this design; `beliefs-f860f1`,
  `beliefs-ae9b18` and `beliefs-91aac6` close at discharge.

## 12. Alternatives rejected

- **A separate `comparison-report` kind, referenced by identity.** Two
  records per verification, a new kind in the base contract colliding with
  the `domain` lane's kind declarations, and a report deletable apart from
  its verification. The computation design already makes the report an
  embedded, content-identified member; embedding it in the record keeps one
  record the preimage of one identity.
- **The typed ref everywhere** (digest `run:<address>`). Bakes a corpus
  spelling into a world identity and makes the in-memory derivation add a
  prefix it has no reason to know. Rejected for the bare address, the run's
  world identity.
- **Normalizing at digest time** (`identity()` strips a prefix if present).
  Two spellings admitted into one value type and the difference hidden inside
  the digest. Rejected: one spelling, made explicit at the reader.
- **A `verify` boundary operation minting the record through the port**, the
  way the run boundary mints a run (the write-permits design's invitation).
  A verification is derived from records the corpus already holds; it needs
  no execution, no act-report and no boundary receipt, and `add` already
  gives it the intent, the registration and the session actor. Adding `run`
  to `KIND_ACTS["verification"]` would open a second route for the same
  record.
- **Recomputing the derivation at `add`.** The computation design fixes the
  two validation moments; a third would make a corpus that holds only the
  assessment refuse a valid publication, and would make `add` read runs.
- **Restoring a derived type from the record** (minting an
  `AssessmentVerification` in the reader). A second constructor accepting a
  report, which R19 forbids by arm. `StoredVerification` is a distinct type
  with the same basis.
- **Storing rule implementations.** Code is held, never stored; the
  reproduction's own reading of 10b already labels them in-process.
- **Leaving the analysis-spec rider to the `domain` lane.** That lane
  declares the facet and names a reader it does not build; the task names
  this lane as an admissible owner and the audit's evidence is this lane's.

## 13. Verification

Before freeze, the design is checked against the tree as follows: the
sources listed above are re-read at the named lines; the failing test of §3.3
is written on this branch and shown to fail on `main`'s code for the stated
reason; `test_designs_corpus.py` passes with the `V` table registered; and
the module graph of §4.3 is drawn from the imports as they are. After
implementation, every V row's mutation test is an executable check named in
`n2_arms_cut21.py`, the durable suite runs on the certified volume through
`cut21_acceptance.py` after cut 20 merges, and the reproduction driver's 10b
is the acceptance oracle for V1 and V8.

## 14. Open questions this design files

- **Where the scope-derivation rule is versioned** — already filed
  (`../guide/open-questions.md#computation-and-reproducibility`); this
  design stores `scope_rule` as the original recipe's boundary policy names
  it and adds one sentence there: a stored verification now carries the
  identity, so a versioning decision changes what new records write, never
  what stored ones mean.
- **The assessment's `proposition` spelling** (§9) — filed as a new entry
  under claims and belief, owned by the layer design's claim sub-project.
