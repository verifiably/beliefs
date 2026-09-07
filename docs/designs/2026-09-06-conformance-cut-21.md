# Conformance cut 21 — verification publication

**Status:** Frozen 2026-09-06, before implementation.

**Sources:** `2026-09-06-verification-publication-design.md` §2–§9, in
particular §3 (one spelling), §4 (the stored verification and its reader),
§5 (publication and the preflight refusal), §6 (the audit), §7 (the
analysis-spec record) and §8 (the `V` table), and the frozen `V` rows quoted
below.

## 1. What this cut is

Cut 21 is the frozen acceptance boundary for verification publication: a
derived verification published as an ordinary `add` carrying its whole basis
with the comparison report embedded under an id that is its identity, one
spelling for the assessment's run member, admission evaluated over records
read back, scope recomputed by the audit and the import from a stored
verification, forgery refused before the intent, and the stored
`analysis-spec` builder and reader. The selection was frozen before
implementation, after two review rounds of the design (its §2 items 13–18
and the two pre-freeze corrections: restamped raw-write fixtures and the
failing identity test written first).

The selection rule is cut 5's: a clause is selected only when its source
mutation and every named check run entirely inside §2. A row with any unrun
arm is partial. The `V` table is new, so no prior evidence exists and every
row is selected in full.

## 2. The boundary

In scope:

- `stored.typed_ref` and `stored.local_id`, the one place a kind prefix is
  added or removed; `AssessmentValue.run` as the bare run address on both
  sides; `stored.assessment_value`'s refusal of an untyped run member; the
  resolvers in `admission.admit`, `evaluation.gather`, `audit.check_assessment`
  and the comparison in `audit._assessment_disagreements`;
- the `verification` facet's `rule`, `scope_rule`, `report` and typed
  `supersedes` members, `ComparisonReport.projection()`,
  `verify.StoredVerification`, `verify.decode_verification` and its
  recomputed-identity refusal, and the report-less `None`;
- `verify.publication_node`, total over both shapes, and `stored.governed_node`;
- `CorpusWriter._refuse`'s verification step — decode, then the `verifies`
  target's resolved identity — and its analysis-spec step, under the
  operation lock, before the intent, in `add` and in the import union;
- `audit.check_verification`'s scope, rule, scope-rule and report
  comparisons through the shared derivation helper, the report-less path
  unchanged; `audit.check_analysis_spec`; `audit.stored_specs` and its two
  halves;
- `spec.restore`, `stored.analysis_spec_node`, `stored.analysis_spec_value`,
  and `_refuse_r20_contradiction` reading the restored spec;
- publication through `CorpusWriter.add`, `OperationWrites.add` and
  `ScopedWriter.add` — one `corpus-write` intent and one fulfilling
  registration, no new act kind;
- the reproduction driver's steps 4, 8 and 10b over a fresh corpus.

Out of scope:

- the `verify` command and every surface (`science`);
- cross-corpus recomputation through the world resolver (`world-resolution`);
- a stored carrier for rule implementations;
- the assessment's `proposition` member's two namespaces (design §9);
- where the scope-derivation rule is versioned (design §14);
- the facet declarations, the compiled registry and the profile arguments the
  `domain` lane's cut 20 owns; after both merge, the base contract names
  `decode_verification` beside the verification facet's readers (design §11).

## 3. Selection

### V1 — closes

```markdown
| **V1** | A published verification is recoverable from the corpus alone: `decode_verification` over the stored record restores a `StoredVerification` whose basis equals the derived value's member for member, whose report's identity equals the derived report's, and whose scope and verdict are *read*, not recomputed; `comparison_report_stored` is true in the reproduction's step 10b and scope and verdict read equal | Derive a verification over two published runs, publish it, reopen the corpus in a fresh process, decode, and assert `basis()` equality, report identity equality, `identity()` equal to the record id, and that the decode performed no run read (the runs deleted first). Run the reproduction driver's 10b and assert `comparison_report_stored` true, `scope_equal` and `verdict_equal` true, and the *corpus* input list naming the verification record alone for the report. **Negative:** the same record with its `report` member removed decodes as `None`, and 10b reports false |
```

- **Selected:** the row in full — every arm of its mutation test, including
  the **Negative** — run through the certified engine on the certified volume, with the portable arms beside it: `acceptance/test_verification_acceptance.py`: the fresh-process decode over a session-published verification with the runs deleted first, and the reproduction driver's step 10b over a fresh `.mm30-reproduction/` directory; `test_verify.py` for the in-memory round trip and the report-less `None`.
- **Prior, not selected again:** none. The `V` table is new at this cut.
- **Deferred:** none.

### V2 — closes

```markdown
| **V2** | One identity: the assessment identity a stored assessment reads back is the identity its run derives, so a verification derived over an original and a replayed run of a stored assessment both admits over the corpus and audits without contradiction; and `AssessmentValue.run` is the bare run address on both sides | The roadmap's failing test, written before the freeze at `tests/test_verification_identity.py` and failing on this tree at its first assertion (§13): publish a dataset, a proposition, an assessment-shaped run, its assessment and a replay; `build_verification` → `publication_node` → `add`; `gather` → `admit` is `Admitted`; `audit_corpus` has no `verification-derivation-contradicted` and no `assessment-derivation-contradicted`; `evaluate_over` answers a `Belief`. Assert `stored.assessment_value(node).run` has no `run:` prefix and equals `build_assessment(closure).run`; assert `run_ref(a) == typed_ref("run", a)`. Raw-alter a stored assessment's `outcome` with the semantic stamp recomputed (an unstamped edit is `semantic-hash-stale`, which the audit skips as malformed) and assert `assessment-derivation-contradicted` at audit and `ImportRefused` as a bundle member — the lookup resolves through the typed ref (decision 13). **Negative:** an assessment facet whose `run` is bare or absent is `MalformedRecord` from `assessment_value`; `admit` with a `RunValue` whose ref is another run is `run-mismatch` |
```

- **Selected:** the row in full — every arm of its mutation test, including
  the **Negative** — run through the certified engine on the certified volume, with the portable arms beside it: `tests/test_verification_identity.py` (written before the freeze, failing on the freeze tree at its first assertion) widened to `gather` → `admit` → `evaluate_over` over `publication_node`; `acceptance/test_verification_acceptance.py` through an attended session; `test_stored.py` and `test_admission.py` for the helper pair, `assessment_value`'s strictness and `run-mismatch`; `test_audit.py` and `test_import_derivation.py` for the restamped contradicted assessment.
- **Prior, not selected again:** none. The `V` table is new at this cut.
- **Deferred:** none.

### V3 — closes

```markdown
| **V3** | Admission is evaluated over records read back: `gather` selects a stored verification by the stored assessment's identity, `admit` reads its scope and verdict from the record, and the belief moves with the record — deleted, it no longer admits; superseded, it is no longer active | Over V2's corpus assert `Belief`; `delete` the verification through the writer and assert `NoBelief(no-eligible-assessment)`; publish a second verification whose `supersedes` names the first and whose verdict is `failed`, and assert `invalidated` and `NoBelief`. Assert the belief input digest equals the one computed in a fresh process over the same corpus (10a). **Negative:** a verification whose `assessment` member names another proposition's assessment is never gathered for this one; and a second assessment record carrying the same identity under another slug is an equally valid `verifies` target — a verification published against either twin admits the identity (decision 17) |
```

- **Selected:** the row in full — every arm of its mutation test, including
  the **Negative** — run through the certified engine on the certified volume, with the portable arms beside it: `acceptance/test_verification_acceptance.py`: the belief over the session-published record, the `delete`, the superseding failed verification, and the fresh-process digest equality; `test_evaluation.py` for the other-proposition and twin-target negatives.
- **Prior, not selected again:** none. The `V` table is new at this cut.
- **Deferred:** none.

### V4 — closes

```markdown
| **V4** | Scope is recomputed over a stored verification: the audit and the import recompute scope through the stored certification and the report by identity, and a stored member that disagrees — scope raised, verdict flipped, a receipt or conformance altered in the report, the rule or scope rule renamed — is `verification-derivation-contradicted` naming the member; a report-less verification is checked for verdict and identity only, as cut 18 rules; and `check_verification` reaches the same verdict whether the evidence's spec is in-process or restored from the corpus | Raw-write V2's published record with `scope: clean-environment` over a pair whose replay receipt does not qualify (or with the verdict flipped, a receipt identity changed, `original_conformance` changed, `rule` renamed, `scope_rule` renamed, each separately), with the verification id, the `verifies` relation's source and the stamp all recomputed from the altered members so the record is self-consistent and decodes (decision 16), and assert one finding per case with the member in `detail`; import each as a bundle member with both runs resolvable and assert `ImportRefused` before any file exists. Run the same audit with `evidence.specs` from `stored_specs(view)` alone and assert equal outcomes. **Negative:** the unaltered record audits `checked` with no contradiction; the same alterations on a report-less record are detected only where cut 18 detected them (verdict, identity) |
```

- **Selected:** the row in full — every arm of its mutation test, including
  the **Negative** — run portably; no host prerequisite: `test_audit.py` over an in-memory corpus for each self-consistent forgery and the report-less comparison; `test_import_derivation.py` for the import refusals before any file; `test_audit.py` again for the stored-specs-only evidence.
- **Prior, not selected again:** none. The `V` table is new at this cut.
- **Deferred:** none.

### V5 — closes

```markdown
| **V5** | Forgery is refused before the intent and before any write: a verification whose id disagrees with its members (a member altered under the old id included), whose report identity disagrees with its basis, which carries an `assessment` member without a `verifies` edge or two edges, or whose `verifies` target resolves to no assessment or to one of another identity, is refused at `add` and at import with the chain head unchanged and no intent appended | Through a scoped writer over a registered root, `add` each forged node and assert the refusal type (`MalformedRecord` for the first three, `VerificationTargetMismatch` for the last two), the head equal to the head after settlement, no intent decoding to the invocation's token, no record file, and no `act` line; import the same as bundle members and assert `ImportRefused` with no file. **Negative:** the well-formed node is one intent and one fulfilling registration (J1), and a report-less hand-built node with an unresolvable target still adds, as today |
```

- **Selected:** the row in full — every arm of its mutation test, including
  the **Negative** — run through the certified engine on the certified volume, with the portable arms beside it: `acceptance/test_verification_acceptance.py`: each forgery through a scoped writer with the head, intent, file and `act`-line assertions, and the well-formed publication's one intent and one registration; `test_operation_writes.py` for the same refusals over the in-memory executor; `test_import_derivation.py` for the bundle-member refusals.
- **Prior, not selected again:** none. The `V` table is new at this cut.
- **Deferred:** none.

### V6 — closes

```markdown
| **V6** | A verification without a report is not malformed: it adds; it imports on cut 18's terms — checked for verdict and assessment identity when its derivation names runs that resolve and the evidence binds the rule, refused on a contradiction, and `derivation-unchecked` only when it names no derivation or its runs or rule do not resolve; and it audits the same way; `stored.verification_node`, `verification_value` and `verification_derivation` are unchanged in signature and result | Add cut 18's fixture verifications (no derivation; derivation without report) through the writer and through import; assert acceptance, `derivation-unchecked` for the derivation-less one and for one whose runs are absent from the bundle, `ImportRefused` for one whose verdict contradicts its resolvable runs, and `check_verification`'s outcome equal to cut 18's on the same fixtures. **Negative:** a `report` member that is present and malformed (a missing key, a receipts list of one, a non-string diagnostic) is `MalformedRecord`, at `add`, at import and in the audit |
```

- **Selected:** the row in full — every arm of its mutation test, including
  the **Negative** — run portably; no host prerequisite: `test_corpus_write.py` and `test_import_derivation.py` for cut 18's fixtures through `add` and import, the four import outcomes, and the malformed-report refusals; `test_audit.py` for the outcome equality with cut 18.
- **Prior, not selected again:** none. The `V` table is new at this cut.
- **Deferred:** none.

### V7 — closes

```markdown
| **V7** | The production shape publishes: a `DatasetProductionVerification` becomes a record with no `verifies` edge and no `assessment` member, decodes to a `StoredVerification` with `assessment` `None`, is never selected by `gather`, and admits nothing; `admission_record` still refuses it | Publish one over a dataset-production pair; assert the record's relations are empty, the facet has no `assessment`, `decode_verification` round-trips, `gather` over every proposition selects it never, and `admission_record` raises `NotAnAssessmentVerification`. **Negative:** `publication_node` refuses a production shape given an `assessment_ref` and an assessment shape given none |
```

- **Selected:** the row in full — every arm of its mutation test, including
  the **Negative** — run portably; no host prerequisite: `test_verify.py` for the production publication, its round trip and `publication_node`'s two cross refusals; `test_evaluation.py` for `gather` never selecting it; the existing K5 arm for `admission_record`'s refusal.
- **Prior, not selected again:** none. The `V` table is new at this cut.
- **Deferred:** none.

### V8 — closes

```markdown
| **V8** | The analysis-spec record round-trips: `analysis_spec_node` writes a stamped record under `analysis-spec:<identity>` and `analysis_spec_value` restores a `FrozenSpec` equal member for member and by identity; a facet whose identity disagrees with its members, or a node whose id disagrees with its identity, is `MalformedRecord`; `stored_specs` supplies the audit; and the reproduction's step 10b lists the rule implementations as its only in-process input | Freeze a spec with a `Decimal` parameter, a seeded nondeterminism and an exclusion; build, add (the writer accepts it — the facet holds two strings), reopen, restore and assert equality of every member, `Decimal` type included, and `identity`; edit the projection text raw (a member changed; the same members re-ordered), keeping the facet's original `identity` and recomputing the semantic stamp so the stamp check passes and restoration is what detects the mismatch, and assert `MalformedRecord` from `restore`, a `derivation-malformed` finding from `audit_corpus` naming the record, the record absent from `stored_specs`' mapping and present in its findings, and `ImportRefused` as a bundle member; rename the id and assert `MalformedRecord`; run the audit with `stored_specs(view)` only and assert V2's outcome. Run 10b and assert `in_process == ["interpretation and equivalence RuleImplementations"]`. **Negative:** `restore` of a text whose mapping has an extra key, or a facet missing `identity`, is `MalformedRecord`; a stochastic-unseeded spec under a bitwise rule is refused by `restore` as by `freeze`; the constructor's argument list is still closed (R19's arm re-run) |
```

- **Selected:** the row in full — every arm of its mutation test, including
  the **Negative** — run through the certified engine on the certified volume, with the portable arms beside it: `test_spec.py` and `test_stored.py` for the round trip with a `Decimal`, the restamped raw edits, the id rename and the unfreezable refusal; `test_audit.py` for the `derivation-malformed` finding and `stored_specs`' two halves; `test_import_derivation.py` for the bundle refusal; the reproduction driver's step 10b for the in-process input list.
- **Prior, not selected again:** none. The `V` table is new at this cut.
- **Deferred:** none.

## 4. Accounting

Eight guarantee rows are read, **8 full/closed** (V1–V8), 0 partial, 0
re-reads counted. No row of another table is selected: R19's
stored-verification limitation (cut 18 §7) closes by V4 and is restated in
the results record as the cross-corpus arm only; J1 and J10 are re-read
informally by V5 and are not counted here. The N2 inventory therefore has
**8 declaration units**, one grouped unit per row. A grouped unit may expand
into lettered sabotage arms, but it is counted once here and may not be
silently split or merged after the freeze.

## 5. N2 and acceptance obligations

1. The declaration inventory names exactly the 8 frozen units in §4, each
   single-homed to the test that exercises it. Lettered sabotage arms
   normalize back to those units.
2. Every selected behavior marked durable in §3 runs through the certified
   engine on the certified kernel and volume tuple, on the volume beside the
   checkout; its portable arms run beside it. Capability refusal is an
   error, never a skip or waiver.
3. The aggregate runner `tools/cut21_acceptance.py` names
   `cut20_acceptance.py` as its prefix (`PREFIX_RUNNERS =
   ("cut20_acceptance.py",)`), then runs the verification acceptance module
   and the cut-21 N2 audit. Cut 20 is frozen and undischarged on the `domain`
   lane's branch, so under concurrency rule 5 this cut discharges after cut
   20 does, on the merged tree; the portable suite and the implementation do
   not wait.
4. `acceptance/n2_arms_cut21.py` declares the sabotage arms of the design's
   §10.3: in `verify.py` (drop `report` from the projection; skip the
   identity recomputation in `decode_verification`; accept a projection with
   a missing key; write `assessment` for the production shape; compute the
   assessment digest over the typed ref), in `stored.py` (return the typed
   ref from `assessment_value`; strip nothing in `local_id`; skip the identity
   check in `analysis_spec_value`), in `admission.py` (compare `run.ref` to
   the bare address), in `evaluation.py` (resolve `a.run` untyped), in
   `audit.py` (skip the scope comparison; skip the report comparison; take
   `certification=None` for a decoded report; compare `stored_value.run`
   through `run_ref` again; resolve the assessment's run bare; drop the
   `analysis-spec` branch; let `stored_specs` return the mapping alone), in
   `corpus.py` (call `_refuse_verification` after `append_intent`; return
   before the target check; resolve the target in `self._view` instead of
   `view` for import; skip `_refuse`'s spec restoration), and in `spec.py`
   (skip `restore`'s identity check; skip the unfreezable check in `restore`;
   decode with a float parser). `test_n2_cut21.py` audits them by the cut-12
   pattern, with the staleness probe's baseline taken from the tree.
5. V1's fresh-process decode deletes both run records first, so a decode that
   reads a run fails rather than passing by accident; a test that decodes in
   the writing process does not satisfy the cell.
6. V4's and V8's raw-write fixtures recompute the semantic stamp (and, for
   V4, the id and the relation source) so the stamp check passes and the
   derivation recomputation is what detects the forgery; a fixture the audit
   skips as `semantic-hash-stale` exercises nothing.
7. V5's head equality is against the head after settlement, and the
   assertion that no intent decodes to the invocation's token is present,
   as J1 requires.
8. V2's test file exists before the freeze and fails on the freeze tree at
   its first assertion; the plan's first task makes it pass without changing
   its assertions.
9. The cut document and declaration inventory are pinned by digest before
   discharge. No implementation discovery rewrites this frozen body; any
   deviation is dated in the results record.

## 6. Second reader

The second-reader charge is to verify every fenced row byte-exact against the
design's §8 table at the freeze commit; audit every selected clause against
§2; and force any unrun clause to remain deferred and its row partial.

The reader challenges especially:

- V1's "read, not recomputed" is asserted by deleting the runs before the
  decode, and 10b's *corpus* input list names the verification record alone
  for the report;
- V2's stored identity, derived identity and `admission_record`'s member are
  asserted equal in one assertion, and `admit` is reached, not only
  `lifecycle_state`;
- V4's forgeries decode — a `derivation-malformed` finding on a V4 fixture
  is a fixture error, not a detection;
- V5's `MalformedRecord` refusals come from `decode_verification` inside
  `_refuse`, before the intent, and the `VerificationTargetMismatch` arm
  resolves in the view the write reads;
- V6's `derivation-unchecked` is asserted only where the derivation is absent
  or does not resolve, and the contradicting report-less fixture is refused;
- V8's `Decimal` is asserted by type after the round trip, and the
  raw-edited projection keeps the original `identity`.

## 7. Limitations

Inherited from the design's §9, restated at the freeze:

- **The `proposition` member keeps two namespaces**; the claim sub-project
  owns it.
- **Derivation validation stays corpus-local**; cross-corpus recomputation is
  `world-resolution`'s.
- **A false certification is not detected**; the remedy is a superseding
  verification.
- **The rule implementations are in-process.**
- **Nothing re-stamps existing records.**
- **Belief input digests move** for every corpus; nothing on disk names one.
- **The freeze precedes the `domain` lane's merge**; the base contract's
  reader line for `decode_verification` is that merge's, and V-row arms
  assert under an agreeing profile.
