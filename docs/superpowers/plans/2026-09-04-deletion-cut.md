# Deletion cut implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build managed `delete` — the third world-changing operation — together with the deletion cut's assigned ride-alongs (the semantic audit, explicit-import derivation validation, the claim restore seam, and the instrumented belief resolver), and discharge conformance cut 17, closing G2c, G8, C6, R5, W16, M1 and M5.

**Architecture:** `delete` joins `CorpusWriter` beside `add` as an **ordinary write**: no intent, no act-report, one engine effect under the per-root lock, no referential check and no tombstone — the managed/raw asymmetry lives entirely in log verification, never in the corpus read. The ride-alongs add three small modules that **compose** existing seams rather than widening them: `beliefs.audit` (a pure semantic audit over a `ReadView` that mints nothing), `beliefs.evaluation` (the one corpus-backed belief evaluation path, instrumented at read time), and one function in `decode.py` (`claim_from_stored`, keeping `WireClaim` confined). Explicit import gains derivation recomputation over evidence the caller supplies explicitly.

**Tech Stack:** Python 3.12+, `nodes` core (`Node`, `Relation`, `DeleteOp`, `DefaultExecutor`), the certified `atoms` engine behind `beliefs.root`, pytest, ruff, pyright, `uv`.

**Spec:** `docs/designs/2026-09-03-world-changing-families-design.md` — §2.2, §2.3, §2.5, §3.0, §3.1, §3.6, §6.2, §6.3, §7 and §8 are this plan's sources. Read it alongside this plan; every task below argues from a numbered section of it.

**Task record:** `beliefs-676a2c` ("Deliver consolidate, move, and managed deletion"). It is already `doing` and claimed; run `tasks note beliefs-676a2c "<one line>"` at each task's end. Its children are added by Task 1 from this plan's headings.

## Global Constraints

- **The cut is frozen before its code exists.** Task 1 lands the frozen cut document; no later task may add, remove, or reword a selected arm. A post-freeze discovery is a dated deviation in the results record (Task 11) and a ruling in the rulings ledger, never an edit to the frozen text.
- **Gates, from `AGENTS.md`.** From `python/`: `uv run --frozen pytest`, `uv run --frozen ruff check .`, `uv run --frozen pyright`. From `ts/`: `npm ci`, `npm test`, `npm run typecheck`, `npm run check`. Before completion: `tasks check`, zero errors, every warning reported — registration-only `unreachable_dep` and `cycle_unverifiable` warnings are environmental.
- **Always `--frozen`.** Never let a test run resolve new dependencies.
- **Do not pass `-q` to pytest.** `python/pyproject.toml` already sets `addopts = "-q --ignore=tests/acceptance"`; doubling it hides the summary line, and any claim about test counts must quote that line. Never pipe pytest through `tail` without `set -o pipefail`.
- **Discharge runs on the certified volume**, which is the repository's own. `/tmp`, `/dev/shm` and the scratch volume all fail the durability allowlist; the acceptance work directory lives beside the checkout (`.cut17-acceptance`). `CapabilityUnavailable` is a fail-closed result, not a waiver.
- **Conventional commits, and no AI-attribution trailer or footer** other than the session trailer the harness requires.
- **One worktree for the lane**, `.worktrees/consolidate-family`, on branch `design/consolidate-family`. `main` is checked out at the repository root, so the final merge runs **from the root, not from this worktree**.
- **Every mutation is an `atoms` effect** executed by the certified engine under the per-root operation lock. The semantic audit and the evaluation seam **write nothing and mint nothing**.
- **`delete` mints no intent and no report, refuses on no inbound reference, and leaves no tombstone** (§3.1). Any implementation that does one of these is wrong even if every test passes.
- **Files shared with other lanes**, per roadmap concurrency rule 3: `errors.py`, `python/tests/test_designs_corpus.py`, the adoption ledger, the roadmap, the guide index, plus `world/verify.py`, `report.py`, `corpus.py`, `stored.py`, `decode.py`. A later merge resolves toward the earlier one.
- **Reuse before you write.** Test helpers already exist for almost everything here: `tests/test_relocation.py` (`_writer`, `_node`, `MOVE_FIELDS`), `tests/test_corpus_write.py` (`OperationRecorder`), `tests/fixtures_cut4.py` (`path_for`, `raw_write`, `reopen`), `tests/test_belief.py` (`scenario`), `tests/test_world_epoch.py` (`make_world`, `publish`, `derivation_bindings`), `tests/test_relocation_rows.py` (`_belief_digest`, `_duplicate_datasets`), `tests/test_world_log_audit.py` (`held_verification`, `config_for`, `audit`), `tests/acceptance/conftest.py` (`durable_root`, `durable_writer`), `tests/acceptance/durable_fixture.py`. Read a helper before writing a rival.

## Interfaces verified against the tree

Do not re-derive these; they were inspected while writing this plan.

| fact | consequence |
|---|---|
| `CorpusWriter._delete_locked(ref)` exists (`corpus.py`): reads the node under the lock, builds `DeleteOp(path, member_content_digest(rendered))`, executes through `self._corpus.executor.execute`, then `_reconstruct()` | `delete` is a thin public wrapper: lock, resolve, refuse excluded kinds, call it |
| `relocation.EXCLUDED_KINDS = ("act-report", "holdings-observation", *COORDINATION_KINDS)` and `_refuse_excluded_kind` raise `RelocationKindExcluded` | the table moves to `corpus.py` as `EXCLUDED_MUTATION_KINDS`; `relocation.py` imports it |
| `_refuse_family_kinds` also refuses kinds a `CoordinationResolver` profile names as coordination kinds | `delete`'s exclusion consults that profile too |
| `retract` and `supersede` already re-resolve under the lock and raise `RelocationTargetMissing` on a locally absent target (cut 16, §3.6) | the deletion re-resolution arm is a **test**, not new code: produce the absence with a real `delete` |
| `stored.verification_node(slug, *, title, assessment, assessment_ref, scope, verdict, supersedes=None)`; the facet carries only `assessment`, `scope`, `verdict`, `supersedes`; `stored.verification_value(node) -> Verification(ref=node.id, ...)` | a stored verification names **no run**, so recomputation needs a new optional facet member (Task 3) |
| `runrecord.decode_run_closure(node) -> RunClosure` rebuilds a persisted run's typed closure; `decode_run_record(node) is None` when the node carries no projection | recomputation decodes runs from the corpus; a run without a projection is *unchecked*, never refused |
| `verify._resolve_rule(original, *, specs, held_rules) -> (rule, implementation_identity, implementation, spec)`; `implementation.evaluate(original.result, replayed.result) -> verdict` | the audit recomputes a **verdict** from evidence the caller supplies |
| `assess.build_assessment(run, *, specs, implementations) -> AssessmentValue \| AssessmentFinding`; `stored.assessment_value(node) -> AssessmentValue` | R22's recomputation is one call and one comparison |
| `corpus.corpus_check(view) -> tuple[Finding, ...]` classifies malformed records (`semantic-hash-stale`, `retraction-target-invalid`, `retraction-cycle`, …) and reads no standing and no belief | the semantic audit runs it **first** (Ω_valid) and skips every ref it flagged |
| `corpus._producers_of(view, dataset) -> list[Producer]` and `stored.basis_routes(node)` | the forged-`single(A)` audit is a set comparison of resolved producers against basis routes |
| `import_bundle(records, *, actor, observer, instrument, opened_at, closed_at)`; `_validate_import_bundle(bundle) -> (findings, payload)` runs entirely before the payload transaction and after the intent | derivation validation slots into `_validate_import_bundle`; a mismatch is `ImportRefused` before any payload write |
| `decode_claim(wire: WireClaim, *, profile: ProfileSpec, snapshot: ResolutionSnapshot) -> tuple[Claim, BindingCheckReceipt]`; `_wire_parts` refuses malformed shape; `test_decode.py::TestM13TheWireTypeIsConfinedToTheDecodeModule::test_no_signature_outside_decode_mentions_the_wire_type` scans signatures | `claim_from_stored` lives **in** `decode.py` and mentions `WireClaim` nowhere in its signature |
| `stored.PROPOSITION_FACET == "proposition"`; `stored.proposition_node(slug, *, title, claim)` stores `claim` as that facet verbatim; `projection.project_claim(claim)` yields `{operator, args, qualifiers, polarity, layer}` | a stored claim facet is a full `π_claim` projection; a facet carrying fewer or more keys is refused, not repaired |
| `belief.evaluate(*, proposition, records, availability, context, binding, profile)`; step 1 refuses a non-`PolicyBinding` binding; `Records(claims, assessments, runs, source_assertions, verifications)`; `SuppliedContext(snapshot, producer_snapshot_identity, retractions, node_corpus, pins)` | `evaluate_over` guards the binding first, then composes `gather` with `evaluate` |
| `closure.build_closure` keyword arguments, in order: `proposition, assessments, runs, verifications, snapshot, producer_snapshot_identity, retractions, consulted, binding` | `EvaluationInputs`' first nine fields are exactly these |
| `corpus.run_value(view, ref) -> RunValue` reads the run and each held input dataset's declaration; `stored.inputs_of(node, role)`; `stored.OBSERVES`; `record.dataset_address(declaration)` | the dataset reads `gather` traces are the `observes` inputs `run_value` resolved |
| `consulted.consulted_contracts(*, claims, profile, node_corpus, pins, closure_nodes)` | `gather` computes `consulted` exactly as `evaluate` does |
| `verification.lifecycle_state(verifications)` is pure; `ADMITTED`, `INVALIDATED`, `NOT_ADMITTED`; standing retractions filter through `corpus.standing_in_local_view(view, ref)` (see `acceptance/test_n2_cut5.py::test_verification_retractions_recompute_admission_and_belief`) | the G2c walk is that test's shape, run over durable records for **every** table row |
| `world/verify.py::_removal_findings` emits `record-removed` (warning) and, given a held copy with a failing verdict, `failing-verification-removed` (error); `root.audit_log(config, subject, target_root, observers, *, actor, history)` | G8's managed-versus-raw asymmetry is asserted through `audit_log` with `history={digest: rendered bytes}` |
| `holdings.boundary.delete(ctx, location, *, standing=()) -> PublishedObservation` records an `Absent` observation; `holdings.adapter.dataset_observations(declaration, active, blocked)` turns reduced heads into `ByteObservation`s | R5's negative (a) is the delete act, a reduction, the adapter, then `evaluate` |
| `python/tools/cut16_acceptance.py` names `cut15_acceptance.py` as prefix and sets `SCIENCE_CUT{4..16}_ROOT` | cut 17's runner names `cut16_acceptance.py` and sets `range(4, 18)` |
| `tests/acceptance/test_n2_cut16.py` pins the freeze commit, the frozen file digest, §§2–7 byte-exact, and the accounting phrases; `FROZEN_PRIOR_CUT_FILES` pins every prior arm table | cut 17's copy adds `python/tests/n2_arms_cut16.py` at its last commit |
| `test_designs_corpus.py` counts design documents (`_COUNT_WORDS` has 43 and 45, not 44 or 46), checks the README table lists every design, and holds `Ranked at` to the newest results record | the freeze adds a document (46) and a README row; the re-rank waits for discharge |
| `tools/roadmap_status.py::ACCOUNTING` has one row per discharged cut | discharge adds row 17 |

## File Structure

| file | responsibility | task |
|---|---|---|
| `docs/designs/2026-09-04-conformance-cut-17.md` | the frozen deletion cut | 1 |
| `docs/designs/2026-09-03-world-changing-families-design.md` | status line only | 1, 11 |
| `python/src/beliefs/errors.py` | `DeletionRefused`, `DeletionTargetMissing`, `DeletionKindExcluded` | 2 |
| `python/src/beliefs/corpus.py` | `EXCLUDED_MUTATION_KINDS`, `CorpusWriter.delete`, `_refuse_excluded_kind`; import derivation validation | 2, 4 |
| `python/src/beliefs/relocation.py` | imports the shared exclusion table | 2 |
| `python/src/beliefs/stored.py` | the optional `derivation` member of the verification facet; `verification_derivation` | 3 |
| `python/src/beliefs/audit.py` | `DerivationEvidence`, `check_verification`, `check_assessment`, `check_lineage_basis`, `audit_corpus` | 3 |
| `python/src/beliefs/decode.py` | `claim_from_stored` | 5 |
| `python/src/beliefs/evaluation.py` | `ReadRef`, `EvaluationInputs`, `gather`, `evaluate_over` | 6 |
| `python/tests/test_deletion.py` | the operation, its refusals, T8 and C1 re-reads, re-resolution after a delete | 2 |
| `python/tests/test_audit.py` | the semantic audit: Ω_valid ordering, three contradiction findings, mints nothing | 3 |
| `python/tests/test_import_derivation.py` | R19 and R22's import clauses and transition (b) | 4 |
| `python/tests/test_claim_restore.py` | M13 and M11 re-read against `claim_from_stored` | 5 |
| `python/tests/test_evaluation.py` | M1: containment and the sabotage shape | 6 |
| `python/tests/test_deletion_rows.py` | G2c, G8, C6, S5, R23, W16, M3 (admission order), M5 | 7 |
| `python/tests/acceptance/test_deletion_acceptance.py` | every selected arm on the certified engine, including R5 and the audit halves of G8/C6 | 8 |
| `python/tests/n2_arms_cut17.py`, `python/tests/acceptance/test_n2_cut17.py` | the N2 declaration inventory and freeze pin | 9 |
| `python/tools/cut17_acceptance.py` | the runner, with cut 16's as prefix | 9 |
| `docs/plans/2026-09-04-conformance-cut-17-results.md`, `docs/plans/2026-09-04-deletion-rulings-ledger.md` | the discharge record and the rulings ledger | 10, 11 |
| the adoption ledger, the roadmap, `tools/roadmap_status.py`, `README.md`, `docs/guide/contracts-and-adoption.md` | re-rank and current state | 1, 11 |

---

### Task 1: Freeze conformance cut 17

**Files:**
- Create: `docs/designs/2026-09-04-conformance-cut-17.md`
- Modify: `docs/designs/2026-09-03-world-changing-families-design.md` (status line), `docs/designs/2026-08-03-redesign-adoption-ledger.md` (the `consolidate-family` row's owner cell), `README.md`, `docs/guide/contracts-and-adoption.md`, `python/tests/test_designs_corpus.py` (`_COUNT_WORDS`)

**Interfaces:**
- Consumes: design §6.2, §6.3, §7 and §8; the frozen rows in their source tables.
- Produces: the frozen arm inventory every later task tests against; the 17 declaration units Task 9 must declare exactly.

- [ ] **Step 1: Confirm the number**

```bash
ls docs/designs/ docs/plans/ | grep -o 'conformance-cut-[0-9]*' | sort -t- -k3 -n | tail -1
```
Expected: `conformance-cut-16`. Take **17**. If another lane has frozen a 17 since, take 18 and substitute throughout (roadmap concurrency rule 1).

- [ ] **Step 2: Extract the frozen rows byte-exact**

The cut quotes each row inside a ```` ```markdown ```` fence, exactly as its source table holds it. Generate them rather than retyping:

```bash
cd docs/designs
for spec in G2c:2026-08-02-epistemic-kernel-design.md G8:2026-08-02-epistemic-kernel-design.md \
  C6:2026-08-03-correction-lifecycle-design.md C1:2026-08-03-correction-lifecycle-design.md \
  R5:2026-08-02-computation-reproducibility-design.md R19:2026-08-02-computation-reproducibility-design.md \
  R22:2026-08-02-computation-reproducibility-design.md R23:2026-08-02-computation-reproducibility-design.md \
  S5:2026-08-02-substrate-consolidation-design.md W16:2026-08-02-world-addressing-design.md \
  T8:2026-08-11-act-report-design.md M13:2026-08-04-formal-model-and-claim-calculus-design.md \
  M11:2026-08-04-formal-model-and-claim-calculus-design.md M1:2026-08-04-formal-model-and-claim-calculus-design.md \
  M3:2026-08-04-formal-model-and-claim-calculus-design.md M5:2026-08-04-formal-model-and-claim-calculus-design.md; do
  r=${spec%%:*}; f=${spec#*:}
  n=$(grep -c "^| \*\*$r\*\* |\|^| $r |" "$f"); [ "$n" = 1 ] || { echo "$r: $n matches in $f"; exit 1; }
done
```
Expected: no output. Each row is one line; paste each grep hit verbatim into its fence.

- [ ] **Step 3: Write the frozen cut document**

`docs/designs/2026-09-04-conformance-cut-17.md`, modelled on `2026-09-03-conformance-cut-16.md` section for section. Its content:

```markdown
# Conformance cut 17 — managed deletion

**Status:** Frozen 2026-09-04.

**Sources:** `2026-09-03-world-changing-families-design.md` §2.2, §2.3, §2.5,
§3.0, §3.1, §3.6, §6.2, §6.3 and §7, and the frozen G, C, R, S, W, T and M
rows quoted below.

## 1. What this cut is

Cut 17 is the frozen acceptance boundary for managed deletion and the
mutation lane's assigned ride-alongs: the ordinary-write `delete`, the
managed/raw asymmetry under log verification, the deletion clauses the
relocation cut deferred, the claim restore seam, the instrumented belief
resolver, explicit-import derivation validation, and the semantic audit
those rows read through. The selection was frozen before implementation.

The selection rule is cut 5's: a clause is selected only when its source
mutation and every named check run entirely inside §2. A row with any unrun
arm is partial. Prior evidence remains evidence but is not selected again.

## 2. The boundary

In scope:

- the public `delete` entry point on `CorpusWriter`: one engine effect under
  the root's lock, no intent, no act-report, no referential check, no
  tombstone (§3.1);
- the excluded kinds common to every world-changing operation (§3.0);
- re-resolution by `retract` and `supersede` after a real `delete` (§3.6);
- log verification's reading of a managed deletion against a raw `unlink`
  (§3.1's asymmetry table), through the existing removal findings;
- the managed holdings deletion act as R5's last-held-copy transition;
- the corpus-local semantic audit: malformed classification first, then
  derivation recomputation for verifications and assessments and basis
  recomputation for datasets, over evidence the caller supplies; it writes
  nothing and mints nothing;
- explicit-import derivation validation over the same evidence, refusing a
  contradicted verification or assessment before any payload write;
- `decode.claim_from_stored`, the M13-conforming restore seam (§6.3); and
- `beliefs.evaluation`, the instrumented resolver and the only corpus-backed
  evaluation path (§6.3).

Out of scope:

- `move` and `consolidate` beyond producing the states this cut deletes from;
- cross-corpus record reads through the world resolver (R19's cross-corpus
  recomputation, S5's cross-corpus reach, M3's coreference arm);
- the rules store and the unresolvable-interpretation-rule refusal (R22);
- producer-snapshot, coverage and divergence clauses (R23);
- scope recomputation for a stored verification: the stored projection
  carries no comparison report, so only the verdict and the assessment
  identity are recomputed (limitation, §7);
- L13's preimage resolver: removal classification stays a path match; and
- the concrete-cycle constructions M3's banked limitation names.

## 3. Selection
```

Then one `### <row> — <reading>` section per row in this order, each with its fenced row and three bullets (**Selected**, **Prior, not selected again**, **Deferred**). The readings, verbatim from design §6.2/§6.3 and §7 where they narrow:

- **G2c — closes.** Selected: the kernel §3.3 lifecycle-table walk re-run over durable records — every row of the table, `active` read under the standing-retraction amendment — plus the raw-deletion negative: raw-delete a failing verification and assert the assessment returns to admitted, undetected on read. Prior: cut 2's value-level walk and cut 5's positive retraction states. Deferred: none.
- **G8 — closes.** Selected: raw-delete the failing verification → admission restored, undetected on read; the log audit **refutes** the raw removal, while a managed `delete` of the same record **validates** with `record-removed` and, given the held copy, `failing-verification-removed` at error severity. Prior: attaching the failure, recency and passing-sibling negatives, the standing-retraction clearing (cuts 2, 5). Deferred: none.
- **C6 — closes.** Selected: the raw-deletion negative over verification retraction — raw deletion of a verification still restores admission undetectably on read. Prior: cut 5's positive retraction states. Deferred: none.
- **R5 — closes.** Selected: negative (a) — destroy the last held copy of an `observes` input through `holdings.delete`, the managed act recording an `absent` observation; assert the input is no longer held, eligibility fails, and admission changes. Prior: the digest, admission and eligibility thirds (cuts 2, 3), negative (b). Deferred: none.
- **S5 — part.** Selected: the deletion half — delete an ancestor named by a basis → `lineage-incomplete`, `not-certified`, `belief_input_digest` moved, no belief rise; delete a divergent producer → certificate restored, belief may rise, and the epistemic readings (corpus read, lineage traversal, admission, belief) are indistinguishable from a corpus in which that run never existed (§7's scoping: log verification is *not* one of those readings). Prior: cut 4's corpus-local walk. Deferred: cross-corpus reach → `world-resolution`.
- **R23 — part.** Selected: the deletion clauses — delete the producing run and the ancestor, stored ref and `null` resolution recorded separately, a second surviving run does not repair the first basis; the §11.14 residue after deleting `R2`; the conflict surviving deletion of either producing run; the audit detecting the forged `single(A)` while `B`'s run stands, and its contradiction finding disappearing once `B`'s run is deleted too (§7: the **semantic** contradiction finding disappears; the log audit still reports the committed removals). Prior: cuts 3, 15, 16. Deferred: producer-snapshot, coverage, cross-corpus divergence, explicit-import and rules-store clauses.
- **W16 — closes.** Selected: its remaining arm — the divergent-lineage conflict still stands after deleting either producing run. Prior: cut 16's whole selection. Deferred: none.
- **C1 — re-read.** Selected: under §2.2's narrowing, retraction remains additive and its operation never edits, removes or re-addresses its target — asserted while a deletion API exists, so the reading postdates it. Prior: cut 5's pre-amendment reading. Deferred: none.
- **T8 — re-read.** Selected: the edit/supersede/delete clause against `delete` — no ordinary API deletes a report, `delete` refuses an act-report subject, and `delete` mints no report of its own. Prior: cut 16's re-read against the relocation operations. Deferred: none.
- **M13 — re-read.** Selected: §2.5's opacity arms against `claim_from_stored` — no `WireClaim` in or out of its signature; delegation to `decode_claim` with the own-typing-path sabotage; the brand chain intact through the new route. Prior: cut 1's closure. Deferred: none.
- **M11 — re-read.** Selected: §2.5's decode arms against `claim_from_stored` — determinism across processes and checkouts; availability as a parameter with the ambient sabotage; refusal before delegation on a wrong kind and on a missing, extra or malformed facet field, with nothing minted. Prior: cut 1's closure; the raw-written negative is not re-run. Deferred: none.
- **R19 — part.** Selected: explicit-import derivation validation over complete closure evidence, refusing before any payload write; transition (b) end to end — import a forged verification whose runs do not resolve (enters unvalidated and admits), then mount the runs, admission still unchanged until the audit runs, the audit emits the contradiction finding and mints nothing, a separate constructor act naming its own contract identity and epoch mints the superseding verification, and admission changes because of that node; negatives (d) and (e) with log-backed raw-write detection. Prior: cut 3's constructor clauses, cut 4's transition (a) and read-side negatives. Deferred: cross-corpus recomputation → `world-resolution`; scope recomputation (§2, §7).
- **R22 — part.** Selected: negative (c)'s explicit-import clause — import recomputes the assessment facet from the run and refuses a mismatch — and its caught-only-under-audit clause. Prior: cuts 3 and 4. Deferred: the unresolvable-interpretation-rule refusal → `contract-cut`.
- **M1 — closes.** Selected: the containment assertion over a corpus exercising every closure member, on the `Belief` arm; and the sabotage — one extra value read through `gather`, a run or verification of a different proposition, nothing else changed, and the check fails while the digest is unchanged. The stated scope limitation is preserved verbatim (Appendix C's resolver bound). Prior: none. Deferred: none.
- **M3 — part.** Selected: a raw-written cyclic configuration classified malformed by the audit before any standing or belief evaluation, with no reading invoked on it; and the admission-order negative — no topological rank is stored, and re-admitting the same records in a different order leaves every identity and the belief digest unchanged. Prior: cuts 5 and 16. Deferred: the coreference arm → `world-resolution`; the concrete-cycle arms stay a banked limitation.
- **M5 — closes.** Selected: its prior clauses re-run durably — restriction-only, quantifier-only, and present-versus-absent qualification identity; the qualifier-map sabotage; the key-order negative — over records minted into a registered root. Prior: cuts 1 and 5. Deferred: none.

Then:

```markdown
### Boundary invariants

- **Selected:** after a real `delete` removes a previously resolved target,
  `retract` and `supersede` each re-resolve under the lock immediately
  before plan construction and refuse `RelocationTargetMissing`. One
  declaration unit, both entry points exercised, the absence produced by
  `delete` and not by a filesystem call.
- **Prior, not selected again:** cut 16's moved-away arm.
- **Deferred:** none.

## 4. Accounting

Sixteen guarantee rows are read: **7 full/closed** (G2c, G8, C6, R5, W16,
M1, M5), **5 partial** (S5, R23, R19, R22, M3), and **4 closed-row re-reads**
(C1, T8, M11, M13). The boundary-invariant declaration adds no row. The N2
inventory therefore has **17 declaration units**: one grouped unit for each
row selection and one for the boundary invariant. A grouped unit may expand
into lettered sabotage arms, but it is counted once here and may not be
silently split or merged after the freeze.

`delete` contributes no T2 arm: it opens no operation and mints no terminal
record (§3.1).

## 5. N2 and acceptance obligations

1. The declaration inventory names exactly the 17 frozen units in §4, each
   single-homed to the test that exercises it. Lettered sabotage arms
   normalize back to those units.
2. Every selected behavior runs portably and again through the certified
   engine on the certified kernel and volume tuple. Capability refusal is an
   error, never a skip or waiver.
3. The aggregate runner names `cut16_acceptance.py` as its prefix, then runs
   the deletion acceptance module and the cut-17 N2 audit.
4. G8's asymmetry runs through `audit_log` over a real chain: the raw arm
   must read `refuted` and the managed arm `validated` with both removal
   findings. A test that asserts only the corpus read does not satisfy the
   cell.
5. The audit's Ω_valid ordering is asserted by instrumentation: standing and
   belief evaluation are made to raise, and the audit must still classify.
6. The cut document and declaration inventory are pinned by digest before
   discharge. No implementation discovery rewrites this frozen body; any
   deviation is dated in the results record.

## 6. Second reader

The second-reader charge is to verify every fenced row byte-exact against its
source table at the freeze commit; audit every selected clause against §2;
and force any unrun clause to remain deferred and its row partial.

The reader challenges especially:

- S5's *indistinguishable* claim is asserted over the epistemic readings only
  and never over log verification (§7);
- R23's *audit reports nothing* is asserted as the absence of the semantic
  contradiction finding, not the absence of all findings (§7);
- `delete` mints nothing: the arms assert no intent appended and no report
  minted, and the operation enum carries no `delete` kind;
- the deleted-target fixture is produced by a real `delete`;
- M1's sabotage reads an **unrelated** run or verification through `gather`
  and the digest is unchanged while the check fails;
- `claim_from_stored` refuses **before** delegating and never repairs.

## 7. Limitations

- **L13 is not closed.** Removal classification matches a held copy by
  claimed path, never by bytes.
- **Scope is not recomputed.** A stored verification carries no comparison
  report, so the audit and the import recompute the verdict and the
  assessment identity only; scope recomputation waits on
  `verification-publication`.
- **The audit is corpus-local**, over a `ReadView` and caller-supplied
  evidence; nothing here resolves across corpora.
- **M1's resolver bound** and **M3's concrete-cycle arms** remain
  limitations, ranked nowhere.
- **No interrupted operation is ever completed** (design §8); `delete` is one
  transaction and has no prefix set.
```

- [ ] **Step 4: Update the design's status line**

In `2026-09-03-world-changing-families-design.md`:

```markdown
**Status:** Banked 2026-09-03. Relocation cut 16 discharged 2026-09-04;
deletion cut frozen as conformance cut 17 (2026-09-04).
```

- [ ] **Step 5: Update the ledger row, README, guide and guard**

- Ledger row `consolidate-family`, owner cell: replace `relocation cut 16 discharged, deletion cut not yet frozen` with `relocation cut 16 discharged, deletion cut frozen as cut 17`.
- `README.md`: add the table row `| `2026-09-04-conformance-cut-17.md` | the frozen deletion cut: managed \`delete\` as an ordinary write, the audit and import ride-alongs, 7 rows closing, 5 partial, 4 closed-row re-reads |` after the cut-16 row; change `Forty-five documents` to `Forty-six documents` and the range's far end to `through 2026-09-04`.
- `docs/guide/contracts-and-adoption.md`: add `  - ../designs/2026-09-04-conformance-cut-17.md` to `sources:` after the cut-16 line; set `updated: 2026-09-04`; after the sentence ending "Managed deletion remains for its later freeze." replace that sentence with "The deletion cut is frozen as cut 17 and not yet discharged."
- `python/tests/test_designs_corpus.py`: add `44: "Forty-four",` and `46: "Forty-six",` to `_COUNT_WORDS`.

- [ ] **Step 6: Run the guards**

```bash
cd python && uv run --frozen pytest tests/test_designs_corpus.py tests/test_check_guide.py
```
Expected: PASS.

- [ ] **Step 7: Attach the plan to the task record and add its children**

```bash
tasks edit beliefs-676a2c --plan deletion-cut
for t in "Task 1: Freeze conformance cut 17" "Task 2: The deletion refusal vocabulary and the public delete" \
  "Task 3: The verification derivation member and the semantic audit" \
  "Task 4: Explicit-import derivation validation" "Task 5: The claim restore seam" \
  "Task 6: The instrumented resolver" "Task 7: The deletion rows, portable" \
  "Task 8: The durable arms" "Task 9: N2 declarations and the acceptance runner" \
  "Task 10: The rulings ledger" "Task 11: Gates, discharge, re-rank, and merge"; do
  tasks add "${t#*: }" --parent beliefs-676a2c --plan deletion-cut --step "$t" -p 2 --size m --tag migration
done
tasks check
```
Expected: zero errors. If `--plan` expects a different topic spelling, `tasks check` says so; use the spelling it accepts and note it in the rulings ledger.

- [ ] **Step 8: Commit**

```bash
git add docs README.md python/tests/test_designs_corpus.py tasks
git commit -m "docs(mutation): freeze conformance cut 17, the deletion cut"
tasks start <task-1-child-id> && tasks done <task-1-child-id> "cut 17 frozen"
```
Record the freeze commit's short id: Task 9 pins it.

---

### Task 2: The deletion refusal vocabulary and the public `delete`

**Files:**
- Modify: `python/src/beliefs/errors.py` (beside `RelocationTargetMissing`), `python/src/beliefs/corpus.py` (beside `add`), `python/src/beliefs/relocation.py` (`EXCLUDED_KINDS`)
- Test: `python/tests/test_deletion.py`

**Interfaces:**
- Consumes: `CorpusWriter._delete_locked(ref)`, `_refuse_family_kinds`' coordination-profile lookup, `RefError`.
- Produces: `CorpusWriter.delete(ref: str) -> None`; `corpus.EXCLUDED_MUTATION_KINDS: tuple[str, ...]`; `errors.DeletionRefused(WriteRefused)`, `DeletionTargetMissing(DeletionRefused)`, `DeletionKindExcluded(DeletionRefused)`.

- [ ] **Step 1: Write the failing tests**

`python/tests/test_deletion.py`:

```python
"""The ordinary-write `delete` (world-changing families §3.1)."""

from __future__ import annotations

import pytest
from fixtures_cut4 import path_for
from nodes.core.errors import RefError
from test_relocation import _node, _writer

from beliefs import stored
from beliefs.corpus import EXCLUDED_MUTATION_KINDS, CorpusWriter
from beliefs.errors import (
    DeletionKindExcluded,
    DeletionRefused,
    DeletionTargetMissing,
    RelocationTargetMissing,
    WriteRefused,
)
from beliefs.report import OPERATION_KINDS


@pytest.fixture()
def writer(tmp_path) -> CorpusWriter:
    return _writer(tmp_path / "corpus")


def test_delete_removes_exactly_one_record_and_mints_nothing(writer):
    kept = writer.add(_node())
    doomed = writer.add(_node())
    port = writer._operation_port
    intents_before, executed_before = len(port.intents), len(port.executed)

    writer.delete(doomed.id)

    assert writer.read_view.resolve(doomed.id) is None
    with pytest.raises(RefError):
        writer.read_view.get(doomed.id)
    assert writer.read_view.get(kept.id) == kept
    assert not path_for(writer.root, doomed.id).exists()
    assert len(port.intents) == intents_before, "delete appends no intent"
    assert not port.fulfilling, "delete fulfills nothing"
    assert len(port.executed) == executed_before + 1, "one engine effect"
    assert [type(op).__name__ for op in port.executed[-1]] == ["DeleteOp"]
    assert not any(node.kind == "act-report" for node in writer.read_view.iter_stored())


def test_the_operation_enum_carries_no_delete_kind():
    assert "delete" not in OPERATION_KINDS


def test_delete_leaves_no_tombstone_and_the_corpus_reads_as_if_never_minted(tmp_path):
    with_delete = _writer(tmp_path / "a")
    never = _writer(tmp_path / "b")
    shared = _node()
    with_delete.add(shared)
    doomed = with_delete.add(_node())
    never.add(shared)

    with_delete.delete(doomed.id)

    assert sorted(n.id for n in with_delete.read_view.iter_stored()) == sorted(
        n.id for n in never.read_view.iter_stored()
    )
    assert sorted(p.name for p in with_delete.root.rglob("*") if p.is_file() and not p.name.startswith(".")) == sorted(
        p.name for p in never.root.rglob("*") if p.is_file() and not p.name.startswith(".")
    )


def test_delete_refuses_a_missing_target(writer):
    with pytest.raises(DeletionTargetMissing):
        writer.delete("note:absent")


def test_delete_resolves_a_deprecated_id_to_the_live_record(writer):
    # A ref that resolves through `deprecated_ids` deletes the record it resolves to.
    node = writer.add(_node().model_copy(update={"deprecated_ids": ["note:old-name"]}))
    writer.delete("note:old-name")
    assert writer.read_view.resolve(node.id) is None


@pytest.mark.parametrize("kind", ["act-report", "holdings-observation", "project", "note-revision-like"])
def test_delete_refuses_every_excluded_kind(writer, kind, monkeypatch):
    # Bypass the add path: excluded kinds cannot be minted through `add`, so the
    # record is placed by a raw write and `delete` is asked to remove it.
    if kind == "note-revision-like":
        pytest.skip("placeholder for the coordination-profile case below")
    from fixtures_cut4 import raw_write

    node = stored._node(kind, "raw", "raw", {}, ())
    raw_write(writer.root, node)
    writer._reconstruct()
    with pytest.raises(DeletionKindExcluded):
        writer.delete(node.id)
    assert path_for(writer.root, node.id).exists()


def test_the_exclusion_table_is_the_relocation_table():
    from beliefs import relocation

    assert relocation.EXCLUDED_KINDS is EXCLUDED_MUTATION_KINDS
    assert set(EXCLUDED_MUTATION_KINDS) >= {"act-report", "holdings-observation", "project"}


def test_delete_accepts_a_retraction(writer):
    from test_retract import retraction_for  # verify the helper name; see Step 2

    target = writer.add(stored.proposition_node("p", title="p", claim={"operator": "affects"}))
    retraction = writer.retract(retraction_for(target, "grounds"))
    writer.delete(retraction.id)
    assert writer.read_view.resolve(retraction.id) is None
    assert writer.read_view.get(target.id) == target


def test_inbound_references_never_prevent_deletion(writer):
    from nodes.core.relations import Relation

    target = writer.add(_node())
    referrer = writer.add(
        _node().model_copy(update={"relations": [Relation(source="note:ref", predicate="cites", target=target.id)]})
    )
    writer.delete(target.id)
    assert writer.read_view.resolve(target.id) is None
    assert writer.read_view.get(referrer.id).relations[0].target == target.id, "the dangling reference stays"


def test_deletion_refusals_are_write_refusals():
    assert issubclass(DeletionRefused, WriteRefused)
    assert issubclass(DeletionTargetMissing, DeletionRefused)
    assert issubclass(DeletionKindExcluded, DeletionRefused)


# --- T8 re-read against delete -------------------------------------------------


def test_t8_delete_refuses_an_act_report_and_mints_none(writer):
    from test_relocation_rows import _stored_act_report  # verify; cut 16's T8 test builds one

    report = _stored_act_report(writer)
    with pytest.raises(DeletionKindExcluded):
        writer.delete(report.id)
    assert writer.read_view.get(report.id) == report
    assert sum(1 for n in writer.read_view.iter_stored() if n.kind == "act-report") == 1


# --- C1 re-read under §2.2's narrowing ----------------------------------------


def test_c1_retract_never_deletes_or_re_addresses_its_target(writer, monkeypatch):
    from test_retract import retraction_for

    target = writer.add(stored.proposition_node("p", title="p", claim={"operator": "affects"}))
    before = path_for(writer.root, target.id).read_bytes()
    calls: list[str] = []
    original = CorpusWriter._delete_locked
    monkeypatch.setattr(CorpusWriter, "_delete_locked", lambda self, ref: calls.append(ref) or original(self, ref))
    writer.retract(retraction_for(target, "grounds"))
    assert calls == [], "the retraction operation never reaches the delete seam"
    assert path_for(writer.root, target.id).read_bytes() == before
    assert writer.read_view.resolve(target.id) == target.id


# --- §3.6 re-resolution after a real delete -----------------------------------


def test_retract_refuses_a_target_deleted_under_it(writer, monkeypatch):
    """The target resolves at entry and is deleted before plan construction."""
    from test_retract import retraction_for

    target = writer.add(stored.proposition_node("p", title="p", claim={"operator": "affects"}))
    record = retraction_for(target, "grounds")
    original_refuse = CorpusWriter._refuse

    def delete_then_refuse(self, node, **kwargs):
        if node.kind == "retraction":
            self._delete_locked(target.id)
        return original_refuse(self, node, **kwargs)

    monkeypatch.setattr(CorpusWriter, "_refuse", delete_then_refuse)
    with pytest.raises(RelocationTargetMissing):
        writer.retract(record)
    assert writer.read_view.resolve(record.id) is None


def test_supersede_refuses_a_predecessor_deleted_under_it(writer, monkeypatch):
    predecessor = writer.add(stored.proposition_node("p", title="p", claim={"operator": "affects"}))
    successor = stored.proposition_node("q", title="q", claim={"operator": "causes"})
    original_refuse = CorpusWriter._refuse

    def delete_then_refuse(self, node, **kwargs):
        if node.kind == "proposition" and node.id == successor.id:
            self._delete_locked(predecessor.id)
        return original_refuse(self, node, **kwargs)

    monkeypatch.setattr(CorpusWriter, "_refuse", delete_then_refuse)
    with pytest.raises(RelocationTargetMissing):
        writer.supersede(successor, of=predecessor.id)
    assert writer.read_view.resolve(successor.id) is None
```

Before running: replace the two `# verify` imports with the real helper names — `grep -n "def retraction\|def _retraction" tests/test_retract.py tests/acceptance/test_n2_cut5.py` and `grep -n "act.report" tests/test_relocation_rows.py`. If no shared helper exists, define `retraction_for(target, ground)` and `_stored_act_report(writer)` at the top of this module (an act-report enters a corpus only through `import_bundle` of a foreign report — see `test_import_bundle.py::test_foreign_act_report_enters_inert`). Delete the `note-revision-like` parametrization placeholder and add instead a coordination-profile case: build a writer with a `CoordinationResolver` mounting a profile (see `coordination_fixtures.py`) and assert `delete` refuses a kind that profile names.

- [ ] **Step 2: Run to verify failure**

```bash
cd python && uv run --frozen pytest tests/test_deletion.py
```
Expected: FAIL — `ImportError: cannot import name 'DeletionKindExcluded'`.

- [ ] **Step 3: Implement**

`errors.py`, after `RelocationTargetMissing`:

```python
class DeletionRefused(WriteRefused):
    """`delete`'s own refusals (world-changing families §3.1).

    Deletion is a storage operation, not an epistemic one: it refuses on what
    it cannot resolve or must not touch, never on what names the target.
    """


class DeletionTargetMissing(DeletionRefused):
    """The ref resolves to no record in this corpus."""


class DeletionKindExcluded(DeletionRefused):
    """The record's kind is excluded from every world-changing operation:
    act-reports (T8), coordination records, and holdings observations (§3.0).
    """
```

`corpus.py`, module level near `_OPERATION_LOCKS`:

```python
EXCLUDED_MUTATION_KINDS: tuple[str, ...] = ("act-report", "holdings-observation", *COORDINATION_KINDS)
"""The kinds no world-changing operation accepts (§3.0): as a `delete` target,
a `move` subject, or a `consolidate` input. `relocation.py` imports this."""
```

`CorpusWriter`, after `add`:

```python
    def delete(self, ref: str) -> None:
        """Remove exactly one record's file — an ordinary write, like `add`.

        No intent, no act-report, one engine effect (§3.1): an act-report is a
        live corpus node, so a delete that minted one would be distinguishable
        from a raw `unlink` on an ordinary read, and the managed/raw asymmetry
        would collapse. No referential check: the records naming the target
        keep naming it, and withdrawing epistemic force is retraction's job.
        No tombstone: the chain's committed removal is the history.
        """
        with self._operation:
            try:
                node = self._view.get(ref)
            except RefError as caught:
                raise DeletionTargetMissing(f"{ref}: no record resolves in this corpus") from caught
            self._refuse_excluded_kind(node)
            self._delete_locked(node.id)

    def _refuse_excluded_kind(self, node: Node) -> None:
        profile = (
            self._coordination_resolver.profile(self._corpus.store.root)
            if self._coordination_resolver is not None
            else None
        )
        if node.kind in EXCLUDED_MUTATION_KINDS or (profile is not None and node.kind in profile.coordination_kinds):
            raise DeletionKindExcluded(f"{node.id}: kind {node.kind!r} is excluded from every world-changing operation")
```

`relocation.py`: replace the `EXCLUDED_KINDS = (...)` line with `from beliefs.corpus import EXCLUDED_MUTATION_KINDS as EXCLUDED_KINDS` (keep the existing `from beliefs.corpus import CorpusWriter` import; merge them into one import line) and drop the now-unused `COORDINATION_KINDS` import if nothing else uses it.

- [ ] **Step 4: Run to verify pass, plus the neighbours**

```bash
cd python && uv run --frozen pytest tests/test_deletion.py tests/test_relocation.py tests/test_corpus_write.py tests/test_retract.py tests/test_supersede.py
cd python && uv run --frozen ruff check . && uv run --frozen pyright
```
Expected: PASS; ruff and pyright clean.

- [ ] **Step 5: Commit**

```bash
git add python/src/beliefs/errors.py python/src/beliefs/corpus.py python/src/beliefs/relocation.py python/tests/test_deletion.py
git commit -m "feat(corpus): add managed delete as an ordinary write"
tasks note beliefs-676a2c "Task 2: public delete lands as an ordinary write; T8 and C1 re-read; re-resolution after delete pinned"
```

---

### Task 3: The verification derivation member and the semantic audit

**Files:**
- Modify: `python/src/beliefs/stored.py` (`verification_node`, new `verification_derivation`)
- Create: `python/src/beliefs/audit.py`
- Test: `python/tests/test_audit.py`

**Interfaces:**
- Consumes: `corpus.corpus_check`, `corpus._producers_of`, `stored.basis_routes`, `stored.assessment_value`, `stored.verification_value`, `runrecord.decode_run_closure`, `verify._resolve_rule`, `assess.build_assessment`, `record.ASSESSMENT_DOMAIN`, `identity.v1`.
- Produces:

```python
# stored.py
def verification_node(slug, *, title, assessment, assessment_ref, scope, verdict,
                      supersedes=None, derivation: tuple[str, str] | None = None) -> Node
def verification_derivation(node: Node) -> tuple[str, str] | None   # (original run ref, replayed run ref); MalformedRecord when malformed

# audit.py
@final @dataclass(frozen=True)
class DerivationEvidence:
    specs: Mapping[str, FrozenSpec]
    held_rules: Mapping[str, EquivalenceImplementation]
    implementations: Mapping[str, RuleImplementation]
NO_EVIDENCE: DerivationEvidence          # every mapping empty — an explicit "nothing held"

@final @dataclass(frozen=True)
class DerivationOutcome:
    checked: bool
    reason: str                          # why unchecked; "" when checked
    contradiction: Finding | None        # set only when checked and contradicted

def check_verification(view: ReadView | _ImportView, node: Node, *, evidence: DerivationEvidence) -> DerivationOutcome
def check_assessment(view: ReadView | _ImportView, node: Node, *, evidence: DerivationEvidence) -> DerivationOutcome
def check_lineage_basis(view: ReadView, node: Node) -> DerivationOutcome
def audit_corpus(view: ReadView, *, evidence: DerivationEvidence) -> tuple[Finding, ...]
```

Finding codes, all `severity="error"`: `verification-derivation-contradicted`, `assessment-derivation-contradicted`, `lineage-basis-contradicted`.

- [ ] **Step 1: Write the failing tests**

`python/tests/test_audit.py`:

```python
"""The corpus-local semantic audit (world-changing families §6.3, §7)."""

from __future__ import annotations

import pytest
from fixtures_cut4 import raw_write
from nodes.core.relations import Relation
from test_relocation import _writer

from beliefs import audit, belief, corpus, stored
from beliefs.audit import NO_EVIDENCE, DerivationEvidence, audit_corpus, check_lineage_basis
from beliefs.errors import MalformedRecord


@pytest.fixture()
def writer(tmp_path):
    return _writer(tmp_path / "corpus")


class TestTheDerivationMember:
    def test_a_verification_may_name_its_two_runs(self):
        node = stored.verification_node(
            "v", title="v", assessment="a" * 64, assessment_ref="assessment:a",
            scope="clean-environment", verdict="passed", derivation=("run:orig", "run:replay"),
        )
        assert stored.verification_derivation(node) == ("run:orig", "run:replay")
        assert stored.verification_value(node).verdict == "passed"

    def test_a_verification_without_one_reads_none(self):
        node = stored.verification_node(
            "v", title="v", assessment="a" * 64, assessment_ref="assessment:a",
            scope="clean-environment", verdict="passed",
        )
        assert stored.verification_derivation(node) is None

    @pytest.mark.parametrize("bad", [{"original": "run:o"}, {"original": 1, "replayed": "run:r"}, {"original": "run:o", "replayed": "run:r", "extra": 1}, "run:o"])
    def test_a_malformed_member_refuses_rather_than_repairs(self, bad):
        node = stored.verification_node(
            "v", title="v", assessment="a" * 64, assessment_ref="assessment:a",
            scope="clean-environment", verdict="passed",
        )
        facet = {**node.facets[stored.VERIFICATION_FACET], "derivation": bad}
        malformed = node.model_copy(update={"facets": {stored.VERIFICATION_FACET: facet}})
        with pytest.raises(MalformedRecord):
            stored.verification_derivation(malformed)

    def test_the_member_is_covered_by_the_semantic_stamp(self):
        without = stored.verification_node("v", title="v", assessment="a" * 64, assessment_ref="assessment:a", scope="clean-environment", verdict="passed")
        with_it = stored.verification_node("v", title="v", assessment="a" * 64, assessment_ref="assessment:a", scope="clean-environment", verdict="passed", derivation=("run:o", "run:r"))
        assert stored.recompute_semantic_hash(without) != stored.recompute_semantic_hash(with_it)


class TestOmegaValidComesFirst:
    def test_a_malformed_record_is_classified_and_nothing_reads_it(self, writer, monkeypatch):
        """M3's audit arm: a raw-written cyclic retraction pair is malformed
        (its content identities cannot close), and the audit says so before
        any standing or belief evaluation — asserted by making both raise."""
        from test_deletion_rows import raw_cyclic_retraction_pair  # Task 7 defines it; see note

        raw_cyclic_retraction_pair(writer)
        monkeypatch.setattr(corpus, "standing_in_local_view", lambda *a, **k: pytest.fail("standing was evaluated"))
        monkeypatch.setattr(belief, "evaluate", lambda *a, **k: pytest.fail("belief was evaluated"))
        findings = audit_corpus(writer.read_view, evidence=NO_EVIDENCE)
        assert findings and all(finding.severity == "error" for finding in findings)
        assert {finding.code for finding in findings} <= {"semantic-hash-stale", "semantic-hash-missing", "retraction-target-invalid", "retraction-cycle"}

    def test_a_flagged_record_is_not_recomputed(self, writer, monkeypatch):
        calls: list[str] = []
        monkeypatch.setattr(audit, "check_verification", lambda view, node, *, evidence: calls.append(node.id) or audit.DerivationOutcome(False, "stub", None))
        bad = stored.verification_node("v", title="v", assessment="a" * 64, assessment_ref="assessment:a", scope="clean-environment", verdict="passed")
        raw_write(writer.root, bad)  # unstamped: semantic-hash-missing
        writer._reconstruct()
        audit_corpus(writer.read_view, evidence=NO_EVIDENCE)
        assert calls == []


class TestTheAuditMintsNothing:
    def test_audit_writes_no_file_and_appends_no_intent(self, writer):
        writer.add(stored.proposition_node("p", title="p", claim={"operator": "affects"}))
        before = sorted(p for p in writer.root.rglob("*") if p.is_file())
        port = writer._operation_port
        audit_corpus(writer.read_view, evidence=NO_EVIDENCE)
        assert sorted(p for p in writer.root.rglob("*") if p.is_file()) == before
        assert port.intents == [] and port.fulfilling == []


class TestLineageBasisRecomputation:
    def test_a_forged_single_is_contradicted_while_the_second_producer_stands(self, writer):
        """R23's audit clause: `single(A)` stamped, `B` also produces → finding;
        delete `B`'s run → the semantic finding disappears (§7)."""
        from test_relocation_rows import _basis_route  # the cut-16 helper; verify its signature

        dataset = writer.add(stored.dataset_node("d", title="d", resources=[{"name": "m", "digest": "sha256:" + "1" * 64}]))
        run_a = writer.add(_producing_run("a", dataset.id))
        run_b = writer.add(_producing_run("b", dataset.id))
        forged = dataset.model_copy(update={"facets": {**dataset.facets, stored.LINEAGE_BASIS_FACET: {"tag": "single", "routes": [_basis_route(run_a.id)]}}})
        raw_write(writer.root, stored.stamp_semantic_identity(forged))
        writer._reconstruct()

        codes = [f.code for f in audit_corpus(writer.read_view, evidence=NO_EVIDENCE)]
        assert codes == ["lineage-basis-contradicted"]

        writer.delete(run_b.id)
        assert [f.code for f in audit_corpus(writer.read_view, evidence=NO_EVIDENCE)] == []

    def test_a_basis_naming_every_producer_is_not_contradicted(self, writer):
        ...  # stamp single(A) with only A producing; assert no finding


def _producing_run(slug: str, dataset_id: str):
    """A minimal run node holding a `produces` edge to `dataset_id`. Build it
    with `stored.run_node` — check its signature — and add the relation
    `Relation(source=f"run:{slug}", predicate=stored.PRODUCES, target=dataset_id)`."""
    ...
```

`TestVerificationRecomputation` and `TestAssessmentRecomputation` need real run closures; they are written in Task 4 alongside the import tests, where the fixture that produces two persisted runs is built once (`tests/fixtures_cut15.py::run_workflow` produces real closures; `runrecord.publication_plan` persists one). In this task, cover them with the **unchecked** arms only:

```python
class TestUncheckedIsNotContradicted:
    def test_a_verification_without_a_derivation_member_is_unchecked(self, writer):
        node = writer.add(stored.verification_node("v", title="v", assessment="a" * 64, assessment_ref="assessment:a", scope="clean-environment", verdict="passed"))
        outcome = audit.check_verification(writer.read_view, node, evidence=NO_EVIDENCE)
        assert outcome == audit.DerivationOutcome(False, "no derivation member", None)

    def test_a_verification_whose_runs_do_not_resolve_is_unchecked(self, writer):
        node = writer.add(stored.verification_node("v", title="v", assessment="a" * 64, assessment_ref="assessment:a", scope="clean-environment", verdict="passed", derivation=("run:o", "run:r")))
        outcome = audit.check_verification(writer.read_view, node, evidence=NO_EVIDENCE)
        assert not outcome.checked and "run:o" in outcome.reason and outcome.contradiction is None

    def test_an_assessment_whose_run_carries_no_closure_is_unchecked(self, writer):
        ...  # a run node with no run-closure projection → reason mentions "projection"
```

Replace every `...` with the real construction before running; the design forbids placeholders in landed tests. For the M3 arm's `raw_cyclic_retraction_pair`, define it **here** (Task 7 imports it from this module): two `stored.retraction_node(...)` values whose `target` members name each other's ids with fabricated `content_identity` values, written with `raw_write` and stamped with `stored.stamp_semantic_identity` — identity recomputation over such a pair cannot close, which is exactly why the frozen row calls a refused hand-written pair a non-test for *acyclicity* and why this cut reads it for **classification** only.

- [ ] **Step 2: Run to verify failure**

```bash
cd python && uv run --frozen pytest tests/test_audit.py
```
Expected: FAIL — `ModuleNotFoundError: No module named 'beliefs.audit'`.

- [ ] **Step 3: Implement the stored member**

`stored.py`: add `derivation: tuple[str, str] | None = None` to `verification_node`; when given, `facet["derivation"] = {"original": derivation[0], "replayed": derivation[1]}`. Add:

```python
def verification_derivation(node: Node) -> tuple[str, str] | None:
    """The two run refs a stored verification names, or `None` when it names
    none. Refuses a malformed member rather than repairing it (M11): a
    derivation that cannot be read is not a derivation that reads as absent."""
    facet = _facet(node, VERIFICATION_FACET)
    if facet is None:
        raise MalformedRecord(f"{node.id}: a verification carries a {VERIFICATION_FACET!r} facet")
    member = facet.get("derivation")
    if member is None:
        return None
    if not isinstance(member, Mapping) or set(member) != {"original", "replayed"}:
        raise MalformedRecord(f"{node.id}: a derivation member names exactly `original` and `replayed`")
    original, replayed = member["original"], member["replayed"]
    if type(original) is not str or type(replayed) is not str or not original.startswith("run:") or not replayed.startswith("run:"):
        raise MalformedRecord(f"{node.id}: derivation runs are `run:` refs")
    return original, replayed
```

- [ ] **Step 4: Implement the audit module**

`python/src/beliefs/audit.py`:

```python
"""The corpus-local semantic audit (world-changing families §6.3, §7).

Pure over a read view and caller-supplied evidence: it writes nothing, mints
nothing, and invokes no standing or belief evaluation. Ω_valid comes first —
`corpus_check` classifies what is malformed, and nothing malformed is read
again below it — and only then is a well-formed record's derivation
recomputed. A derivation that cannot be recomputed here is **unchecked**,
never contradicted and never validated; "cannot be checked here" is a reason,
not a verdict.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import final

from nodes.core.node import Node

from beliefs import stored
from beliefs.assess import AssessmentValue, build_assessment
from beliefs.corpus import Finding, ReadView, _ImportView, _producers_of, corpus_check
from beliefs.errors import MalformedRecord, RuleUnbound
from beliefs.identity import v1
from beliefs.record import ASSESSMENT_DOMAIN
from beliefs.runrecord import decode_run_closure
from beliefs.sealed import sealed
from beliefs.spec import FrozenSpec, RuleImplementation
from beliefs.verify import EquivalenceImplementation, _resolve_rule

__all__ = ["NO_EVIDENCE", "DerivationEvidence", "DerivationOutcome", "audit_corpus",
           "check_assessment", "check_lineage_basis", "check_verification"]


@sealed
@final
@dataclass(frozen=True)
class DerivationEvidence:
    """What the caller holds: frozen specs, equivalence-rule implementations
    keyed by identity, and interpretation-rule implementations keyed by
    identity. Supplied explicitly, never ambient (M11's doctrine)."""

    specs: Mapping[str, FrozenSpec]
    held_rules: Mapping[str, EquivalenceImplementation]
    implementations: Mapping[str, RuleImplementation]


NO_EVIDENCE = DerivationEvidence(specs={}, held_rules={}, implementations={})


@sealed
@final
@dataclass(frozen=True)
class DerivationOutcome:
    checked: bool
    reason: str
    contradiction: Finding | None


def _unchecked(reason: str) -> DerivationOutcome:
    return DerivationOutcome(checked=False, reason=reason, contradiction=None)


def _closure(view: ReadView | _ImportView, ref: str):
    if not view.holds(ref):
        return None, f"{ref} does not resolve here"
    node = view.get(ref)
    if node.kind != "run":
        return None, f"{ref} is not a run"
    try:
        return decode_run_closure(node), ""
    except MalformedRecord as refused:
        return None, f"{ref} carries no run-closure projection: {refused}"


def check_verification(view: ReadView | _ImportView, node: Node, *, evidence: DerivationEvidence) -> DerivationOutcome:
    derivation = stored.verification_derivation(node)   # MalformedRecord propagates: refuse, never repair
    if derivation is None:
        return _unchecked("no derivation member")
    original, why = _closure(view, derivation[0])
    if original is None:
        return _unchecked(why)
    replayed, why = _closure(view, derivation[1])
    if replayed is None:
        return _unchecked(why)
    try:
        _rule, _implementation_identity, implementation, spec = _resolve_rule(
            original, specs=evidence.specs, held_rules=evidence.held_rules
        )
    except RuleUnbound as unbound:
        return _unchecked(str(unbound))
    if original.recipe.shape != replayed.recipe.shape:
        return _unchecked("mixed shapes")
    stored_value = stored.verification_value(node)
    verdict = implementation.evaluate(original.result, replayed.result)
    assessment = None
    if spec is not None:
        assessment = v1.digest(ASSESSMENT_DOMAIN, {"spec": spec.identity, "run": original.address(), "proposition": spec.target})
    disagreements = []
    if verdict != stored_value.verdict:
        disagreements.append(f"verdict stored={stored_value.verdict!r} recomputed={verdict!r}")
    if assessment is not None and assessment != stored_value.assessment:
        disagreements.append("assessment identity differs from the original run's derivation")
    if not disagreements:
        return DerivationOutcome(checked=True, reason="", contradiction=None)
    return DerivationOutcome(
        checked=True,
        reason="",
        contradiction=Finding(
            severity="error",
            code="verification-derivation-contradicted",
            ref=node.id,
            detail="; ".join(disagreements),
            message=f"{node.id}: the stored verification contradicts its recomputed derivation",
        ),
    )


def check_assessment(view: ReadView | _ImportView, node: Node, *, evidence: DerivationEvidence) -> DerivationOutcome:
    stored_value = stored.assessment_value(node)
    closure, why = _closure(view, stored_value.run)
    if closure is None:
        return _unchecked(why)
    derived = build_assessment(closure, specs=evidence.specs, implementations=evidence.implementations)
    if not isinstance(derived, AssessmentValue):
        return _unchecked(derived.reason)
    if derived == stored_value:
        return DerivationOutcome(checked=True, reason="", contradiction=None)
    return DerivationOutcome(
        checked=True,
        reason="",
        contradiction=Finding(
            severity="error",
            code="assessment-derivation-contradicted",
            ref=node.id,
            detail=f"stored outcome={stored_value.outcome!r} recomputed={derived.outcome!r}",
            message=f"{node.id}: the stored assessment facet contradicts the facet derived from its run",
        ),
    )


def check_lineage_basis(view: ReadView, node: Node) -> DerivationOutcome:
    """A stamped basis must name every resolved producer of its dataset. A
    producer the basis omits is what a raw-forged `single(A)` looks like while
    `B`'s run stands; once `B`'s run is gone, nothing contradicts it (§7)."""
    if stored.lineage_basis(node) is None:
        return _unchecked("no stamped basis")
    named = {route.get("run") for route in stored.basis_routes(node)}
    named_resolved = {view.resolve(str(run)) for run in named}
    producers = {p.resolved_run for p in _producers_of(view, node.id) if p.resolved_run is not None}
    omitted = sorted(producers - named_resolved)
    if not omitted:
        return DerivationOutcome(checked=True, reason="", contradiction=None)
    return DerivationOutcome(
        checked=True,
        reason="",
        contradiction=Finding(
            severity="error",
            code="lineage-basis-contradicted",
            ref=node.id,
            detail=",".join(omitted),
            message=f"{node.id}: the stamped basis omits a producing run that resolves here",
        ),
    )


def audit_corpus(view: ReadView, *, evidence: DerivationEvidence) -> tuple[Finding, ...]:
    """Ω_valid first, then recomputation over what is well-formed. No standing,
    no belief, no write, no mint."""
    findings = list(corpus_check(view))
    flagged = {finding.ref for finding in findings}
    for node in view.iter_stored():
        if node.id in flagged:
            continue
        if node.kind == "verification":
            outcome = check_verification(view, node, evidence=evidence)
        elif node.kind == "assessment":
            outcome = check_assessment(view, node, evidence=evidence)
        elif node.kind == "dataset":
            outcome = check_lineage_basis(view, node)
        else:
            continue
        if outcome.contradiction is not None:
            findings.append(outcome.contradiction)
    return tuple(sorted(findings, key=lambda finding: finding.sort_key))
```

Verify before use: `Finding`'s constructor and `sort_key` (in `corpus.py`), `_ImportView.holds/get`, the import path of `EquivalenceImplementation` (grep `class EquivalenceImplementation`), `Producer.resolved_run`, and whether `corpus_check` handles a raw-written record whose `iter_stored` decode fails (if `iter_stored` raises on a malformed file, catch `MalformedRecord` in `audit_corpus`'s loop and skip — the classification is already in `findings`). Read `beliefs/sealed.py` for the `@sealed` decorator; if it is not importable this way, follow how `belief.py` imports it.

- [ ] **Step 5: Run to verify pass**

```bash
cd python && uv run --frozen pytest tests/test_audit.py tests/test_stored.py tests/test_verification_lifecycle.py
cd python && uv run --frozen ruff check . && uv run --frozen pyright
```
Expected: PASS; clean.

- [ ] **Step 6: Commit**

```bash
git add python/src/beliefs/stored.py python/src/beliefs/audit.py python/tests/test_audit.py
git commit -m "feat(audit): add the corpus-local semantic audit and the verification derivation member"
tasks note beliefs-676a2c "Task 3: semantic audit lands, Omega-valid first, three contradiction findings, mints nothing"
```

---

### Task 4: Explicit-import derivation validation

**Files:**
- Modify: `python/src/beliefs/corpus.py` (`import_bundle`, `_validate_import_bundle`)
- Test: `python/tests/test_import_derivation.py`; extend `python/tests/test_audit.py` with `TestVerificationRecomputation` and `TestAssessmentRecomputation`

**Interfaces:**
- Consumes: `audit.check_verification`, `audit.check_assessment`, `audit.DerivationEvidence`, `audit.NO_EVIDENCE`.
- Produces: `import_bundle(records, *, actor, observer, instrument, opened_at, closed_at, evidence: DerivationEvidence = NO_EVIDENCE)`; import findings `derivation-unchecked: <id>: <reason>`; `ImportRefused` with `member=<id>` on a contradiction, before any payload write.

- [ ] **Step 1: Build the two-run fixture once**

At the top of `python/tests/test_import_derivation.py`, a module-level fixture that yields **persisted** original and replayed runs plus the evidence to recompute over them. Two sources already do the hard part: `tests/fixtures_cut15.py::run_workflow` (a real Snakemake run through the boundary, producing a `RunClosure`) and `tests/test_run_persistence.py` (how a closure is persisted into a corpus with `runrecord.publication_plan` and read back by `decode_run_closure`). Read both, then write:

```python
@pytest.fixture()
def derived(tmp_path):
    """Two persisted assessment-shaped runs of one recipe, a frozen spec, the
    held equivalence and interpretation implementations, and the verification
    `build_verification` derives from them. Returns a SimpleNamespace with
    `writer, original, replayed, spec, evidence, verification` where
    `verification` is the `RunVerification` value."""
```

Persist both runs through `writer.import_bundle` or `writer.add` — whichever `test_run_persistence.py` uses — so each is a `run` node carrying `RUN_CLOSURE_FACET`. If a real workflow run is too heavy for a portable test, `tests/closure_fixtures.py` may hold a synthetic `RunClosure` builder; prefer that and say so in the rulings ledger.

- [ ] **Step 2: Write the failing tests**

```python
class TestR19ExplicitImport:
    def test_a_forged_verification_with_resolvable_runs_is_refused_before_any_write(self, derived):
        genuine = derived.verification
        forged = stored.verification_node(
            "forged", title="forged", assessment=genuine.assessment,
            assessment_ref="assessment:a", scope=genuine.scope,
            verdict="passed" if genuine.verdict != "passed" else "failed",
            derivation=(run_ref(genuine.original), run_ref(genuine.replayed)),
        )
        before = sorted(p for p in derived.writer.root.rglob("*.md"))
        with pytest.raises(ImportRefused) as refused:
            derived.writer.import_bundle([forged], evidence=derived.evidence, **IMPORT_FIELDS)
        assert refused.value.member == forged.id
        assert not path_for(derived.writer.root, forged.id).exists()
        # the refusal report is the import family's own; no bundle member landed
        assert [p for p in derived.writer.root.rglob("*.md") if p not in before and "act-report" not in str(p)] == []

    def test_an_import_whose_runs_do_not_resolve_proceeds_with_a_finding(self, tmp_path):
        writer = _writer(tmp_path / "c")
        unresolvable = stored.verification_node("v", title="v", assessment="a" * 64, assessment_ref="assessment:a", scope="clean-environment", verdict="passed", derivation=("run:nowhere", "run:nowhere-2"))
        report = writer.import_bundle([unresolvable], **IMPORT_FIELDS)
        findings = _report_findings(report)   # read the stored act-report entry's findings; see test_import_bundle.py::test_unresolved_foreign_input_admits_with_finding
        assert any(f.startswith("derivation-unchecked: verification:v") for f in findings)
        assert writer.read_view.get(unresolvable.id).facets[stored.VERIFICATION_FACET].get("validated") is None

    def test_no_validation_state_is_written_onto_a_verification(self, derived):
        node = _stored_from(derived.verification)   # helper: RunVerification -> verification_node with derivation
        derived.writer.import_bundle([node], evidence=derived.evidence, **IMPORT_FIELDS)
        assert "validated" not in derived.writer.read_view.get(node.id).facets[stored.VERIFICATION_FACET]

    def test_a_genuine_verification_imports(self, derived):
        node = _stored_from(derived.verification)
        derived.writer.import_bundle([node], evidence=derived.evidence, **IMPORT_FIELDS)
        assert derived.writer.read_view.get(node.id).kind == "verification"


class TestR19TransitionB:
    def test_forged_unavailable_to_available(self, derived_unmounted):
        """Import the forgery while its runs are absent → admits; mount the
        runs → admission unchanged; audit → contradiction, mints nothing;
        constructor act → superseding verification; admission changes because
        of that node."""
        w = derived_unmounted.writer
        forged = ...  # verification_node with derivation naming the not-yet-imported runs, verdict "passed"
        w.import_bundle([forged], evidence=derived_unmounted.evidence, **IMPORT_FIELDS)
        assert _admission(w, derived_unmounted.assessment_identity) == ADMITTED

        w.import_bundle([derived_unmounted.original_node, derived_unmounted.replayed_node], **IMPORT_FIELDS)  # the mount
        assert _admission(w, derived_unmounted.assessment_identity) == ADMITTED, "mounting is not an epistemic event"

        files = sorted(p for p in w.root.rglob("*.md"))
        findings = audit_corpus(w.read_view, evidence=derived_unmounted.evidence)
        assert [f.code for f in findings] == ["verification-derivation-contradicted"]
        assert sorted(p for p in w.root.rglob("*.md")) == files, "the audit mints nothing"
        assert _admission(w, derived_unmounted.assessment_identity) == ADMITTED, "the audit alone changes nothing"

        superseding = build_verification(derived_unmounted.original, derived_unmounted.replayed, specs=..., held_rules=..., contract_identity="science:" + "c" * 64, epoch="epoch:" + "e" * 64)
        node = _stored_from(superseding, supersedes=forged.id)
        w.import_bundle([node], evidence=derived_unmounted.evidence, **IMPORT_FIELDS)
        assert _admission(w, derived_unmounted.assessment_identity) != ADMITTED
        assert audit_corpus(w.read_view, evidence=derived_unmounted.evidence) == () or all(f.ref == forged.id for f in audit_corpus(...))


class TestR19NegativesDAndE:
    def test_a_raw_written_forgery_is_caught_only_under_audit(self, derived):
        raw_write(derived.writer.root, stored.stamp_semantic_identity(forged))
        derived.writer._reconstruct()
        assert derived.writer.read_view.get(forged.id).kind == "verification"     # not refused, not detected on read
        assert corpus_check(derived.writer.read_view) == ()                        # the corpus check says nothing
        assert [f.code for f in audit_corpus(derived.writer.read_view, evidence=derived.evidence)] == ["verification-derivation-contradicted"]

    def test_a_self_consistent_raw_run_is_not_detected_and_an_unaudited_forgery_is_indistinguishable(self, derived):
        ...  # raw-write a run whose projection decodes; assert corpus_check and the read say nothing; assert a forged verification
             # and a genuine one differ on no read-path predicate until `audit_corpus` runs — log-backed detection is Task 8's durable arm


class TestR22ExplicitImport:
    def test_import_recomputes_the_assessment_facet_and_refuses_a_mismatch(self, derived):
        genuine = build_assessment(derived.original, specs=derived.evidence.specs, implementations=derived.evidence.implementations)
        forged = _assessment_node_from(genuine, outcome="supported" if genuine.outcome != "supported" else "refuted")
        with pytest.raises(ImportRefused):
            derived.writer.import_bundle([forged], evidence=derived.evidence, **IMPORT_FIELDS)
        assert not path_for(derived.writer.root, forged.id).exists()

    def test_a_raw_written_assessment_is_caught_only_under_audit(self, derived):
        ...  # raw_write the forged assessment; read says nothing; audit_corpus emits assessment-derivation-contradicted
```

Fill every `...` with real code before running. `_admission(w, identity)` is `lifecycle_state(tuple(v for v in (stored.verification_value(n) for n in w.read_view.iter_stored() if n.kind == "verification") if v.assessment == identity))`. `IMPORT_FIELDS = {"actor": "a", "observer": "o", "instrument": "i", "opened_at": "2026-09-04T00:00:00Z", "closed_at": "2026-09-04T00:00:01Z"}`.

- [ ] **Step 3: Run to verify failure**

```bash
cd python && uv run --frozen pytest tests/test_import_derivation.py
```
Expected: FAIL — `TypeError: import_bundle() got an unexpected keyword argument 'evidence'`.

- [ ] **Step 4: Implement**

In `import_bundle`'s signature add `evidence: DerivationEvidence = NO_EVIDENCE` (import lazily inside `corpus.py` if `audit` importing `corpus` makes a cycle: `from beliefs.audit import NO_EVIDENCE, DerivationEvidence` at module top of `corpus.py` **will** be circular, since `audit.py` imports `corpus`. Resolve by defining `DerivationEvidence`, `NO_EVIDENCE` and `DerivationOutcome` in a new tiny module `beliefs/evidence.py` that imports nothing from `corpus`, re-exported by `audit.py`; `corpus.py` imports from `evidence.py` and calls `check_verification`/`check_assessment` through a **local** import inside `_validate_import_bundle`). Pass `evidence` to `_validate_import_bundle(bundle, evidence)`, and after the retraction and cycle checks:

```python
        from beliefs.audit import check_assessment, check_verification

        findings = {
            f"unresolved: {record.id} -> {relation.target}"
            for record in records
            for relation in record.relations
            if not union.holds(relation.target)
        }
        for record in records:
            if record.kind == "verification":
                outcome = check_verification(union, record, evidence=evidence)
            elif record.kind == "assessment":
                outcome = check_assessment(union, record, evidence=evidence)
            else:
                continue
            if outcome.contradiction is not None:
                raise ImportRefused(f"{record.id}: {outcome.contradiction.message}", member=record.id)
            if not outcome.checked:
                findings.add(f"derivation-unchecked: {record.id}: {outcome.reason}")
```

`MalformedRecord` from `verification_derivation` must surface as `ImportRefused(..., member=record.id)` — wrap the two calls in the same `try/except ScienceError` shape the retraction block uses.

- [ ] **Step 5: Run to verify pass**

```bash
cd python && uv run --frozen pytest tests/test_import_derivation.py tests/test_import_bundle.py tests/test_audit.py
cd python && uv run --frozen ruff check . && uv run --frozen pyright
```
Expected: PASS; clean.

- [ ] **Step 6: Commit**

```bash
git add python/src/beliefs python/tests/test_import_derivation.py python/tests/test_audit.py
git commit -m "feat(import): recompute verification and assessment derivations at explicit import"
tasks note beliefs-676a2c "Task 4: explicit import refuses contradicted derivations before any payload write; R19 transition (b) runs end to end"
```

---

### Task 5: The claim restore seam

**Files:**
- Modify: `python/src/beliefs/decode.py`
- Test: `python/tests/test_claim_restore.py`

**Interfaces:**
- Consumes: `decode_claim`, `WireClaim`, `stored.PROPOSITION_FACET`, `projection.project_claim`.
- Produces: `decode.claim_from_stored(node: Node, *, profile: ProfileSpec, snapshot: ResolutionSnapshot) -> tuple[Claim, BindingCheckReceipt]`.

- [ ] **Step 1: Write the failing tests**

`python/tests/test_claim_restore.py`, reusing `test_decode.py`'s fixtures (`profile`, `readable`, `affects`, the contract paths — import them or copy the fixture definitions; do not redefine the contracts):

```python
"""M13 and M11 re-read against `claim_from_stored` (design §2.5)."""

from __future__ import annotations

import inspect
import subprocess
import sys
import textwrap

import pytest
from nodes.core.node import Node
from test_decode import affects, profile, readable, base_contract_path, testing_contract_path  # noqa: F401 — fixtures

from beliefs import decode, stored
from beliefs.claim import Claim
from beliefs.decode import claim_from_stored, decode_claim
from beliefs.errors import MalformedWireClaim
from beliefs.projection import claim_identity, project_claim
from beliefs.resolution import BindingCheckReceipt


def stored_proposition(wire) -> Node:
    facet = {"operator": wire.operator, "args": list(wire.args), "qualifiers": {k: dict(v) for k, v in wire.qualifiers.items()}, "polarity": wire.polarity, "layer": wire.layer}
    return stored.proposition_node("p", title="p", claim=facet)


class TestM13Opacity:
    def test_the_signature_names_no_wire_type(self):
        signature = inspect.signature(claim_from_stored)
        assert "WireClaim" not in str(signature)
        assert signature.return_annotation != "WireClaim"

    def test_it_delegates_to_decode_claim(self, profile, readable, affects, monkeypatch):
        seen = []
        real = decode.decode_claim
        monkeypatch.setattr(decode, "decode_claim", lambda wire, **kw: seen.append(wire) or real(wire, **kw))
        claim, receipt = claim_from_stored(stored_proposition(affects()), profile=profile, snapshot=readable)
        assert len(seen) == 1 and isinstance(seen[0], decode.WireClaim)
        assert isinstance(claim, Claim) and isinstance(receipt, BindingCheckReceipt)

    def test_the_restored_claim_is_the_constructor_s_own(self, profile, readable, affects):
        claim, _ = claim_from_stored(stored_proposition(affects()), profile=profile, snapshot=readable)
        direct, _ = decode_claim(affects(), profile=profile, snapshot=readable)
        assert project_claim(claim) == project_claim(direct)
        assert claim_identity(claim) == claim_identity(direct)   # π_claim accepts it; the brand chain is intact

    def test_the_wire_type_stays_confined(self):
        # The existing scan in test_decode.py asserts no signature outside decode mentions WireClaim;
        # this re-read asserts the new function is inside decode.py and the scan still passes.
        assert claim_from_stored.__module__ == "beliefs.decode"


class TestM11FunctionOfItsArguments:
    def test_identical_across_processes(self, profile, readable, affects, base_contract_path, testing_contract_path):
        claim, receipt = claim_from_stored(stored_proposition(affects()), profile=profile, snapshot=readable)
        script = textwrap.dedent(...)   # mirror test_decode.py::TestM11DecodeIsAFunctionOfItsArguments, building the stored node
                                        # with stored.proposition_node and calling claim_from_stored; print claim_identity and receipt.identity()
        out = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, check=True).stdout.split()
        assert out == [claim_identity(claim), receipt.identity()]

    def test_availability_stays_a_parameter(self, profile, affects):
        with pytest.raises(MalformedWireClaim):
            claim_from_stored(stored_proposition(affects()), profile=profile, snapshot=None)  # type: ignore[arg-type]

    @pytest.mark.parametrize(
        "mutate",
        [
            lambda f: {k: v for k, v in f.items() if k != "polarity"},        # missing field
            lambda f: {**f, "extra": "x"},                                   # extra field
            lambda f: {**f, "args": "not-a-list"},                          # malformed field
            lambda f: {**f, "qualifiers": {"dim": {"quantifier": "all"}}},  # malformed qualifier body
        ],
    )
    def test_refuses_before_delegation_and_mints_nothing(self, profile, readable, affects, monkeypatch, mutate):
        node = stored_proposition(affects())
        bad = node.model_copy(update={"facets": {stored.PROPOSITION_FACET: mutate(node.facets[stored.PROPOSITION_FACET])}})
        monkeypatch.setattr(decode, "decode_claim", lambda *a, **k: pytest.fail("delegated on malformed input"))
        with pytest.raises(MalformedWireClaim):
            claim_from_stored(bad, profile=profile, snapshot=readable)

    def test_a_wrong_kind_refuses_before_delegation(self, profile, readable, monkeypatch):
        monkeypatch.setattr(decode, "decode_claim", lambda *a, **k: pytest.fail("delegated"))
        with pytest.raises(MalformedWireClaim):
            claim_from_stored(stored.source_node("s", title="s", identifiers={"doi": "10.1/x"}), profile=profile, snapshot=readable)

    def test_no_key_error_or_attribute_error_escapes(self, profile, readable, affects):
        node = stored_proposition(affects()).model_copy(update={"facets": {}})
        with pytest.raises(MalformedWireClaim):
            claim_from_stored(node, profile=profile, snapshot=readable)
```

- [ ] **Step 2: Run to verify failure**

```bash
cd python && uv run --frozen pytest tests/test_claim_restore.py
```
Expected: FAIL — `ImportError: cannot import name 'claim_from_stored'`.

- [ ] **Step 3: Implement**

`decode.py`, after `decode_claim`; add `"claim_from_stored"` to `__all__`:

```python
_STORED_CLAIM_KEYS = frozenset({"operator", "args", "qualifiers", "polarity", "layer"})


def claim_from_stored(node: Node, *, profile: ProfileSpec, snapshot: ResolutionSnapshot) -> tuple[Claim, BindingCheckReceipt]:
    """Restore a `Claim` from a stored proposition's covered claim facet.

    The wire value is built **here** and consumed **here** — `WireClaim` still
    never leaves this module (M13) — and typing is delegated to `decode_claim`
    rather than duplicated, so the check still happens once, in one place.
    Every ill-formed input refuses **before** delegation, with nothing minted
    and no `KeyError` or `AttributeError` on the way in (M11): a restore helper
    is exactly where "be liberal in what you accept" would defeat the row.
    """
    if not isinstance(node, Node) or node.kind != "proposition":
        raise MalformedWireClaim(f"claim_from_stored restores a proposition node, found {type(node).__name__}")
    facet = node.facets.get("proposition")  # stored.PROPOSITION_FACET; restated to keep decode.py free of stored.py
    if not isinstance(facet, Mapping):
        raise MalformedWireClaim(f"{node.id}: no covered claim facet")
    keys = set(facet)
    if keys != _STORED_CLAIM_KEYS:
        missing, extra = sorted(_STORED_CLAIM_KEYS - keys), sorted(keys - _STORED_CLAIM_KEYS)
        raise MalformedWireClaim(f"{node.id}: claim facet missing {missing}, extra {extra}; refused, never repaired")
    if isinstance(facet["args"], str) or not isinstance(facet["args"], Sequence):
        raise MalformedWireClaim(f"{node.id}: args is not a sequence")
    if not isinstance(facet["qualifiers"], Mapping):
        raise MalformedWireClaim(f"{node.id}: qualifiers is not a mapping")
    wire = WireClaim(
        operator=facet["operator"],
        args=tuple(facet["args"]),
        qualifiers=facet["qualifiers"],
        polarity=facet["polarity"],
        layer=facet["layer"],
    )
    return decode_claim(wire, profile=profile, snapshot=snapshot)
```

`decode_claim`'s `_wire_parts` performs the remaining field-level checks (non-string members, unknown qualifier fields) and refuses them as `MalformedWireClaim` before anything is typed, which keeps "refusal before typing" true for the fields this helper does not itself inspect. If `grep -n "import" decode.py` shows `stored` is already imported, use `stored.PROPOSITION_FACET` instead of the literal.

- [ ] **Step 4: Run to verify pass**

```bash
cd python && uv run --frozen pytest tests/test_claim_restore.py tests/test_decode.py tests/test_claim.py
cd python && uv run --frozen ruff check . && uv run --frozen pyright
```
Expected: PASS, including `test_no_signature_outside_decode_mentions_the_wire_type`.

- [ ] **Step 5: Commit**

```bash
git add python/src/beliefs/decode.py python/tests/test_claim_restore.py
git commit -m "feat(decode): add claim_from_stored, the M13-conforming restore seam"
tasks note beliefs-676a2c "Task 5: claim_from_stored lands; M11 and M13 re-read against the new route"
```

---

### Task 6: The instrumented resolver

**Files:**
- Create: `python/src/beliefs/evaluation.py`
- Test: `python/tests/test_evaluation.py`

**Interfaces:**
- Consumes: `stored.assessment_value`, `stored.verification_value`, `corpus.run_value`, `decode.claim_from_stored`, `consulted.consulted_contracts`, `closure.build_closure`, `belief.evaluate`, `record.dataset_address`, `stored.ASSESSES`, `stored.OBSERVES`.
- Produces: exactly the surface design §6.3 specifies:

```python
ReadRef: TypeAlias = tuple[str, str]
READ_KINDS = ("assessment", "proposition", "run", "verification", "dataset", "retraction", "contract", "producer-snapshot")

@final @dataclass(frozen=True)
class EvaluationInputs:
    proposition: str
    assessments: tuple[AssessmentValue, ...]
    runs: Mapping[str, RunValue]
    verifications: tuple[Verification, ...]
    snapshot: LineageSnapshot
    producer_snapshot_identity: str
    retractions: RetractionEnumeration
    consulted: tuple[tuple[str, str], ...]
    binding: tuple[str, str]
    claim: Claim | None
    read_trace: tuple[ReadRef, ...]
    def closure(self) -> Closure
    def declared_refs(self) -> frozenset[ReadRef]
    def records(self) -> Records

def gather(view: ReadView, proposition: str, *, context: SuppliedContext, profile: ProfileSpec,
           resolution: ResolutionSnapshot, binding: PolicyBinding) -> EvaluationInputs
def evaluate_over(view: ReadView, proposition: str, *, availability: Availability, context: SuppliedContext,
                  profile: ProfileSpec, resolution: ResolutionSnapshot, binding: object) -> Belief | NoBelief | Refused
```

- [ ] **Step 1: Write the failing tests**

`python/tests/test_evaluation.py`. The corpus must exercise **every** closure member: two assessments on the proposition over two runs with `observes` datasets carrying the empirical facet, a passing clean-environment verification each, the proposition node with a full claim facet (`test_claim_restore.stored_proposition`), plus an **unrelated** proposition with its own assessment, run and verification. `context` supplies the snapshot (`corpus.lineage_snapshot(view, roots)`), a producer-snapshot identity, a `RetractionEnumeration`, `node_corpus` and `pins`; `availability`, `binding` and `profile` come from `test_belief.scenario()`'s values (`BELIEF_V1`, `BELIEF_V1_RULE`, `BELIEF_V1_FIXTURES`, `PROFILE` — import them). Verify `stored.assessment_node`/`stored.run_node` signatures first (`grep -n "^def assessment_node\|^def run_node" src/beliefs/stored.py`).

```python
def test_evaluate_over_is_the_corpus_backed_path_and_yields_a_belief(corpus_fixture):
    result = evaluate_over(corpus_fixture.view, corpus_fixture.proposition, **corpus_fixture.kwargs)
    assert isinstance(result, Belief)


def test_m1_every_read_through_the_resolver_is_inside_the_declared_closure(corpus_fixture):
    inputs = gather(corpus_fixture.view, corpus_fixture.proposition, **corpus_fixture.gather_kwargs)
    assert set(inputs.read_trace) <= inputs.declared_refs()
    assert {kind for kind, _ in inputs.read_trace} == set(READ_KINDS) - {"retraction", "contract", "producer-snapshot"}, "every corpus-read kind is exercised"
    assert inputs.closure().digest() == evaluate(proposition=..., records=inputs.records(), ...).belief_input_digest


def test_the_records_are_already_proposition_scoped(corpus_fixture):
    inputs = gather(...)
    assert all(a.proposition == corpus_fixture.proposition for a in inputs.assessments)
    assert set(inputs.runs) == {a.run for a in inputs.assessments}
    assert all(v.assessment in {a.identity() for a in inputs.assessments} for v in inputs.verifications)


def test_m1_sabotage_shape_an_unrelated_verification_read_fails_containment(corpus_fixture, monkeypatch):
    """The sabotage N2 declares: `gather` reads one verification belonging to a
    different proposition; the digest is unchanged and the check fails."""
    import beliefs.evaluation as evaluation

    honest = gather(...)
    monkeypatch.setattr(evaluation, "_verification_selected", lambda value, ids: True)  # the one predicate the sabotage flips
    leaky = gather(...)
    assert leaky.closure().digest() == honest.closure().digest()
    assert not set(leaky.read_trace) <= leaky.declared_refs()


def test_the_binding_is_guarded_before_any_read(corpus_fixture, monkeypatch):
    import beliefs.evaluation as evaluation
    monkeypatch.setattr(evaluation, "gather", lambda *a, **k: pytest.fail("read before the binding was refused"))
    result = evaluate_over(corpus_fixture.view, corpus_fixture.proposition, **{**corpus_fixture.kwargs, "binding": ("rule", "impl")})
    assert isinstance(result, Refused) and result.reason.startswith("binding-not-exact")


def test_a_proposition_with_no_claim_record_consults_only_the_base_contract(corpus_fixture):
    ...  # delete the proposition node's assesses edge target? No — build a second fixture whose assessment's
         # `assesses` target does not resolve; assert inputs.claim is None, records().claims == {}, and
         # ("proposition", ...) not in read_trace (nothing handed out, nothing traced)


def test_no_belief_and_refused_arms_assert_no_containment(corpus_fixture):
    ...  # an availability with no fixtures → NoBelief; assert evaluate_over returns it and gather was still called once (the guard is on the Belief arm only)


def test_the_nine_fields_are_build_closure_s_keywords_in_order():
    import inspect
    from beliefs.closure import build_closure
    params = [p for p in inspect.signature(build_closure).parameters if p != "self"]
    fields = [f.name for f in dataclasses.fields(EvaluationInputs)][:9]
    assert fields == params
```

- [ ] **Step 2: Run to verify failure**

```bash
cd python && uv run --frozen pytest tests/test_evaluation.py
```
Expected: FAIL — `ModuleNotFoundError: No module named 'beliefs.evaluation'`.

- [ ] **Step 3: Implement**

`python/src/beliefs/evaluation.py`:

```python
"""The instrumented resolver — the only corpus-backed belief evaluation path
(world-changing families §6.3, formal model M1).

`gather` is **the** resolver: every value a belief evaluation obtains from a
corpus comes through it, and it appends to `read_trace` at the moment each
value is handed out. It filters at read time — matched assessments first,
then exactly what they reach — because `belief.Records` is an unfiltered
pool by contract, and a resolver that read the pool would record reads the
digest legitimately omits. `declared_refs` mirrors `build_closure`'s
filtering member for member, and containment is `read_trace ⊆ declared_refs`.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TypeAlias, final

from beliefs.belief import Availability, Belief, NoBelief, Records, Refused, SuppliedContext, evaluate
from beliefs.claim import Claim
from beliefs.closure import Closure, RetractionEnumeration, build_closure
from beliefs.consulted import consulted_contracts
from beliefs.corpus import ReadView, run_value
from beliefs.decode import claim_from_stored
from beliefs.errors import ContractDisagreement
from beliefs.lineage import LineageSnapshot
from beliefs.policy import PolicyBinding
from beliefs.profile import ProfileSpec
from beliefs.record import AssessmentValue, RunValue, dataset_address
from beliefs.resolution import ResolutionSnapshot
from beliefs.sealed import sealed
from beliefs import stored
from beliefs.verification import Verification

ReadRef: TypeAlias = tuple[str, str]
READ_KINDS = ("assessment", "proposition", "run", "verification", "dataset", "retraction", "contract", "producer-snapshot")


@sealed
@final
@dataclass(frozen=True)
class EvaluationInputs:
    """`build_closure`'s argument set, plus what was read to obtain it."""

    proposition: str
    assessments: tuple[AssessmentValue, ...]
    runs: Mapping[str, RunValue]
    verifications: tuple[Verification, ...]
    snapshot: LineageSnapshot
    producer_snapshot_identity: str
    retractions: RetractionEnumeration
    consulted: tuple[tuple[str, str], ...]
    binding: tuple[str, str]
    claim: Claim | None
    read_trace: tuple[ReadRef, ...]

    def closure(self) -> Closure:
        return build_closure(
            proposition=self.proposition, assessments=self.assessments, runs=self.runs,
            verifications=self.verifications, snapshot=self.snapshot,
            producer_snapshot_identity=self.producer_snapshot_identity, retractions=self.retractions,
            consulted=self.consulted, binding=self.binding,
        )

    def declared_refs(self) -> frozenset[ReadRef]:
        ours = tuple(a for a in self.assessments if a.proposition == self.proposition)
        ids = {a.identity() for a in ours}
        refs: set[ReadRef] = set()
        refs.update(("assessment", identity) for identity in ids)
        if ours:
            refs.update(("proposition", a.proposition) for a in ours)
        refs.update(("run", a.run) for a in ours)
        refs.update(("verification", v.ref) for v in self.verifications if v.assessment in ids)
        for a in ours:
            run = self.runs.get(a.run)
            if run is None:
                continue
            for entry in run.inputs:
                if entry.role == stored.OBSERVES and (address := dataset_address(entry.dataset)) is not None:
                    refs.add(("dataset", address))
        refs.update(("retraction", ref) for ref, _ in self.retractions.found)
        refs.update(("contract", identity) for _, identity in self.consulted)
        refs.add(("producer-snapshot", self.producer_snapshot_identity))
        return frozenset(refs)

    def records(self) -> Records:
        return Records(
            claims={self.proposition: self.claim} if self.claim is not None else {},
            assessments=self.assessments,
            runs=self.runs,
            source_assertions=(),
            verifications=self.verifications,
        )


def _verification_selected(value: Verification, ids: frozenset[str]) -> bool:
    """The one predicate M1's sabotage flips: an unrelated verification read
    through the resolver must fail containment while leaving the digest alone."""
    return value.assessment in ids


def gather(view: ReadView, proposition: str, *, context: SuppliedContext, profile: ProfileSpec,
           resolution: ResolutionSnapshot, binding: PolicyBinding) -> EvaluationInputs:
    trace: list[ReadRef] = []
    matched: list[AssessmentValue] = []
    proposition_refs: list[str] = []
    for node in view.iter_stored():
        if node.kind != "assessment":
            continue
        value = stored.assessment_value(node)
        if value.proposition != proposition:
            continue           # a lookup, not a value handed out
        matched.append(value)
        trace.append(("assessment", value.identity()))
        proposition_refs.extend(r.target for r in node.relations if r.predicate == stored.ASSESSES)
    ids = frozenset(a.identity() for a in matched)

    runs: dict[str, RunValue] = {}
    for a in matched:
        if a.run in runs or not view.holds(a.run):
            continue
        runs[a.run] = run_value(view, a.run)
        trace.append(("run", a.run))
        for entry in runs[a.run].inputs:
            if entry.role == stored.OBSERVES and (address := dataset_address(entry.dataset)) is not None:
                trace.append(("dataset", address))

    verifications: list[Verification] = []
    for node in view.iter_stored():
        if node.kind != "verification":
            continue
        value = stored.verification_value(node)
        if _verification_selected(value, ids):
            verifications.append(value)
            trace.append(("verification", value.ref))

    claim: Claim | None = None
    for ref in dict.fromkeys(proposition_refs):
        if view.holds(ref):
            claim, _receipt = claim_from_stored(view.get(ref), profile=profile, snapshot=resolution)
            trace.append(("proposition", proposition))
            break

    consulted = consulted_contracts(
        claims={proposition: claim} if claim is not None else {},
        profile=profile, node_corpus=context.node_corpus, pins=context.pins,
        closure_nodes=tuple(sorted(ids)),
    )
    return EvaluationInputs(
        proposition=proposition, assessments=tuple(matched), runs=runs, verifications=tuple(verifications),
        snapshot=context.snapshot, producer_snapshot_identity=context.producer_snapshot_identity,
        retractions=context.retractions, consulted=consulted,
        binding=(binding.rule, binding.implementation), claim=claim, read_trace=tuple(trace),
    )


def evaluate_over(view: ReadView, proposition: str, *, availability: Availability, context: SuppliedContext,
                  profile: ProfileSpec, resolution: ResolutionSnapshot, binding: object) -> Belief | NoBelief | Refused:
    """`evaluate`'s step-1 guard first, then `gather`, then `evaluate`."""
    if not isinstance(binding, PolicyBinding):
        return Refused(f"binding-not-exact: {binding!r} is not a PolicyBinding(rule, implementation) pair")
    try:
        inputs = gather(view, proposition, context=context, profile=profile, resolution=resolution, binding=binding)
    except ContractDisagreement as exc:
        return Refused(f"consulted-contracts-disagree: {exc}")
    return evaluate(proposition=proposition, records=inputs.records(), availability=availability,
                    context=context, binding=binding, profile=profile)
```

Verify before use: `AssessmentValue.identity()`, `RunValue.inputs[i].role`/`.dataset`, where `PolicyBinding` and `ContractDisagreement` live (grep), and that `consulted_contracts` raises `ContractDisagreement` (it does in `evaluate`). If `evaluate` recomputes `consulted` itself (it does), `EvaluationInputs.consulted` and `evaluate`'s must agree — the containment test's digest equality asserts it.

- [ ] **Step 4: Run to verify pass**

```bash
cd python && uv run --frozen pytest tests/test_evaluation.py tests/test_belief.py tests/test_closure.py
cd python && uv run --frozen ruff check . && uv run --frozen pyright
```
Expected: PASS; clean.

- [ ] **Step 5: Commit**

```bash
git add python/src/beliefs/evaluation.py python/tests/test_evaluation.py
git commit -m "feat(evaluation): add the instrumented resolver and the corpus-backed evaluation path"
tasks note beliefs-676a2c "Task 6: beliefs.evaluation lands; M1 containment holds and its sabotage shape fails"
```

---

### Task 7: The deletion rows, portable

**Files:**
- Test: `python/tests/test_deletion_rows.py`

**Interfaces:**
- Consumes: `CorpusWriter.delete`, `audit_corpus`, `evaluate_over`, `relocation.consolidate`, `corpus.lineage_snapshot`, `lineage.certify`, `lifecycle_state`, the cut-16 helpers in `test_relocation_rows.py` (`_duplicate_datasets`, `_belief_digest`, `_basis_route`, `_world_for`).
- Produces: the portable evidence Task 8 re-runs durably, and the `raw_cyclic_retraction_pair` helper Task 3's audit test imports (define it in `test_audit.py` and import it here instead if Task 3 already did — one definition).

- [ ] **Step 1: Write the tests, one section per frozen row**

```python
"""Frozen cut-17 row evidence over the ordinary-write `delete`."""

# --- G2c: the lifecycle-table walk under the amended "active", plus the raw-deletion negative ---

@pytest.mark.parametrize("row", LIFECYCLE_ROWS)   # (verifications to mint, expected state), one per kernel §3.3 row,
                                                   # each verification a stored node; "active" = not superseded AND not
                                                   # targeted by a standing retraction — include a row where a standing
                                                   # retraction of the failure restores admission and one where a passing
                                                   # sibling does not
def test_g2c_every_lifecycle_row_over_stored_records(writer, row): ...

def test_g2c_g8_c6_raw_deletion_restores_admission_undetected_on_read(writer):
    # mint pass + fail → INVALIDATED; os.unlink(path_for(root, fail.id)); writer._reconstruct()
    # → ADMITTED through evaluate_over/lifecycle over the corpus; corpus_check(view) == (); no finding on read

# --- G8 and C6: the managed half reads the same on the corpus; the log half is Task 8's ---

def test_g8_managed_delete_reads_identically_to_raw_on_the_corpus(tmp_path):
    # two corpora, same records; one raw-unlinks the failing verification, the other calls delete;
    # assert identical iter_stored ids, identical admission, identical corpus_check → ()

# --- S5's deletion half ---

def test_s5_deleting_a_basis_ancestor_yields_incomplete_and_moves_the_digest(writer, world):
    # dataset D with stamped basis naming run R and ancestor A; snapshot = lineage_snapshot(view, [D]);
    # certify → independent; delete A; new snapshot → "lineage-incomplete" in findings, state not-certified;
    # belief digest via _belief_digest-style evaluate moves; belief value does not rise

def test_s5_deleting_a_divergent_producer_restores_the_certificate_indistinguishably(tmp_path):
    # corpus X: R1 produces D from A (stamped), R2 produces byte-identical D from B → lineage-divergent;
    # delete R2 → certified again. corpus Y: same records, R2 never added. Assert for the epistemic readings:
    # sorted iter_stored ids equal, lineage_snapshot projections equal, certify equal, belief digest equal,
    # admission equal. (Log verification is NOT compared — §7.)

# --- R23's deletion and audit clauses ---

def test_r23_stored_ref_and_null_resolution_are_recorded_separately(writer):
    # after deleting the producing run, the Route in the snapshot has stored_run == the ref and resolved_run is None,
    # and snapshot_projection shows both members

def test_r23_a_second_surviving_run_does_not_repair_the_first_basis(writer): ...
def test_r23_the_residue_after_deleting_r2(tmp_path): ...   # the same construction as S5's second test, asserted as R23 words it
def test_r23_the_audit_detects_a_forged_single_while_b_stands_then_reports_no_contradiction(writer):
    # reuse test_audit's construction; assert code present, delete B's run, assert the contradiction finding absent
    # (not "no findings": corpus_check may still be empty here, but the assertion is about the contradiction code)

# --- W16's remaining arm ---

def test_w16_the_conflict_survives_deleting_either_producing_run(tmp_path):
    # _duplicate_datasets → consolidate → survivor basis tag "conflict"; delete run A in one copy of the state and
    # run B in another; in both, stored.lineage_basis(survivor)["tag"] == "conflict", divergence_state → lineage-divergent,
    # certify → not-certified

# --- M3: the audit arm (imports raw_cyclic_retraction_pair) and the admission-order negative ---

def test_m3_admission_order_leaves_every_identity_and_the_digest_unchanged(tmp_path):
    # the same record set added in two orders into two corpora; assert stored_semantic_hash per id equal,
    # ids equal, and the belief digest equal; assert no facet anywhere carries a rank/order member

# --- M5, portable half (the durable re-run is Task 8) ---

def test_m5_qualification_participates_in_stored_identity(writer):
    # proposition nodes whose claim facets differ only in restriction / only in quantifier / one omitting a dimension
    # → distinct stored_semantic_hash and distinct claim_identity(claim_from_stored(...)); key order → unchanged
```

Write every body in full. For the `LIFECYCLE_ROWS`, enumerate kernel §3.3's four table rows plus the two "active" amendments (superseded pass admits nothing; standing retraction clears a failure). Use `evaluate_over` for admission where a full belief scenario is available (it makes the M1 seam load-bearing), and `lifecycle_state` over `stored.verification_value` values filtered by `standing_in_local_view` otherwise.

- [ ] **Step 2: Run, iterate to green**

```bash
cd python && uv run --frozen pytest tests/test_deletion_rows.py tests/test_audit.py
```
Expected: PASS. If a row cannot be made to fail before `delete` existed (it should — `delete` is new), record why in the rulings ledger.

- [ ] **Step 3: Full portable suite and gates**

```bash
cd python && uv run --frozen pytest
cd python && uv run --frozen ruff check . && uv run --frozen pyright
```
Expected: PASS with the summary line quoted in the task note; clean.

- [ ] **Step 4: Commit**

```bash
git add python/tests/test_deletion_rows.py python/tests/test_audit.py
git commit -m "test(deletion): pin the frozen cut-17 rows over the ordinary-write delete"
tasks note beliefs-676a2c "Task 7: portable row evidence for G2c, G8, C6, S5, R23, W16, M3 and M5 passes (<summary line>)"
```

---

### Task 8: The durable arms

**Files:**
- Create: `python/tests/acceptance/test_deletion_acceptance.py`

**Interfaces:**
- Consumes: every portable arm of Tasks 2–7, `tests/acceptance/conftest.py` fixtures, `root.audit_log`, `holdings.boundary`.
- Produces: the durable checks Task 9's declarations name.

- [ ] **Step 1: Write the module**

Every selected arm re-runs against the **certified engine** through `open_corpus` on `durable_root` (the portable tests prove behaviour; only this module supports a discharge claim). A durable arm **errors rather than skips** when the certified tuple is unavailable — the `durable_root` fixture already does this. One test per declaration unit, named for its row:

```python
def test_g2c_lifecycle_walk_over_durable_records(durable_writer): ...
def test_g8_c6_raw_removal_refutes_and_managed_delete_validates(work_directory, durable_root):
    """The log half. Build a world config over the durable corpus (see
    test_lifecycle_wrappers.py:173 for an `audit_log` call over a real root),
    take the failing verification's rendered bytes as `history`, then:
      raw arm: os.unlink the file; audit_log → report.verdict == "refuted"
      managed arm (a second durable root): writer.delete(...); audit_log → "validated",
        with finding codes ["record-removed", "failing-verification-removed"] and the
        second at severity "error"; the corpus read is identical in both arms."""
def test_r5_the_managed_holdings_delete_ends_heldness_and_changes_admission(certified_work):
    """Write the observed dataset's bytes to a durable store root through
    holdings.boundary.write, reduce to heads (holdings.reduce + project; see
    tests/acceptance/test_n2_cut10.py for the reduction path), adapt with
    dataset_observations into Availability.observations, evaluate → Belief.
    Then holdings.boundary.delete the location (an `absent` observation),
    reduce again, adapt → the dataset is no longer held, admission through
    evaluate is NoBelief('unavailable-input-unheld'), and the input's
    eligibility fails."""
def test_s5_deletion_half_durably(durable_writer): ...
def test_r23_deletion_and_audit_clauses_durably(durable_writer): ...
def test_w16_conflict_survives_deleting_either_producer_durably(work_directory): ...
def test_c1_retraction_never_removes_its_target_durably(durable_writer): ...
def test_t8_delete_refuses_an_act_report_durably(durable_writer): ...
def test_m13_claim_from_stored_is_opaque_over_a_durable_record(durable_writer): ...
def test_m11_claim_from_stored_is_a_function_of_its_arguments_over_a_durable_record(durable_writer): ...
def test_r19_import_validation_and_transition_b_durably(durable_writer): ...
def test_r22_import_recomputation_and_audit_durably(durable_writer): ...
def test_m1_containment_over_a_durable_corpus(durable_writer): ...
def test_m3_audit_classification_and_admission_order_durably(work_directory): ...
def test_m5_qualification_identity_durably(durable_writer): ...
def test_boundary_reresolution_after_a_durable_delete(durable_writer): ...
```

Each body mirrors its portable twin and additionally reloads the view (`reopen(durable_root)` / `open_corpus`) before asserting, so the assertion is about bytes the engine committed. For `delete`, assert through `atoms`' chain (`test_durable_families.chain_entries`) that the removal is **one** registered transaction carrying a `DeleteOp`-shaped final of `absent`, with **no** intent entry appended for it.

- [ ] **Step 2: Run on the certified volume**

```bash
cd python && uv run --frozen pytest tests/acceptance/test_deletion_acceptance.py
```
Expected: PASS. If the `durable_root` fixture raises `UncertifiedVolume`, the kernel has outrun the `atoms` A8 allowlist (`atoms-recertify.timer`) — report the exact mismatch; do not skip.

- [ ] **Step 3: Commit**

```bash
git add python/tests/acceptance/test_deletion_acceptance.py
git commit -m "test(cut17): add the durable deletion arms"
tasks note beliefs-676a2c "Task 8: durable arms pass on the certified tuple (<n> passed)"
```

---

### Task 9: N2 declarations and the acceptance runner

**Files:**
- Create: `python/tests/n2_arms_cut17.py`, `python/tests/acceptance/test_n2_cut17.py`, `python/tools/cut17_acceptance.py`

**Interfaces:**
- Consumes: the 17 frozen units; the freeze commit id from Task 1; every durable check in Task 8.
- Produces: `CUT17_ARMS`, `DECLARATION_UNITS`, `unit_of`, `CO_CITED`; the runner Task 11 executes.

- [ ] **Step 1: Declare the arms**

`python/tests/n2_arms_cut17.py`, following `n2_arms_cut16.py`: one or more lettered `Arm`s per unit, each with a **one-mutation** sabotage against real module text and the exact durable check that must fail. `DECLARATION_UNITS` is exactly:

```python
DECLARATION_UNITS = ("G2c", "G8", "C6", "R5", "S5", "R23", "W16", "C1", "T8", "M13", "M11",
                     "R19", "R22", "M1", "M3", "M5", "boundary-reresolution-after-delete")
```

Sabotages the frozen text requires, at minimum:

| unit | sabotage | what must fail |
|---|---|---|
| G8 | `corpus.py`: make `delete` append an operation intent before `_delete_locked` | the managed arm no longer reads like a raw unlink on the chain, and `test_g8_c6_...` |
| T8 | `corpus.py`: drop `"act-report"` from `EXCLUDED_MUTATION_KINDS` | `test_t8_delete_refuses_an_act_report_durably` |
| C1 | `corpus.py`: `retract` calls `self._delete_locked(target_ref)` before `return self._corpus.add(record)` | `test_c1_retraction_never_removes_its_target_durably` |
| M13 | `decode.py`: `claim_from_stored` returns `Claim._checked(...)` itself instead of delegating | `test_m13_...` (the delegation assertion) |
| M11 | `decode.py`: `claim_from_stored` builds `build_snapshot(readable={})` when `snapshot is None` | `test_m11_...` (availability as a parameter) |
| M11 | `decode.py`: drop the `keys != _STORED_CLAIM_KEYS` refusal | the refusal-before-delegation arm |
| M1 | `evaluation.py`: `_verification_selected` returns `True` | `test_m1_containment_over_a_durable_corpus` |
| M3 | `audit.py`: call `standing_in_local_view` inside `audit_corpus` before `corpus_check` | the Ω_valid arm |
| R19 | `corpus.py`: replace `raise ImportRefused(f"{record.id}: {outcome.contradiction.message}", ...)` with `findings.add(...)` | the refused-before-write arm |
| R23 | `audit.py`: `omitted = []` | the forged-`single(A)` arm |
| S5 / R23 | `corpus.py`: `lineage_snapshot` substitutes `resolved_run=str(route.get("run", ""))` (never `None`) | the incomplete/`null`-resolution arms |
| boundary | `corpus.py`: remove the final under-lock `self._view.get(target_ref)` in `retract` | the re-resolution arm |

Every other unit gets at least one sabotage in the same spirit. `CO_CITED` lists any check a prior cut's arm already names (avoid it; a new durable check per unit is the rule).

- [ ] **Step 2: The N2 audit module**

`python/tests/acceptance/test_n2_cut17.py`, copied from `test_n2_cut16.py` with: `FROZEN_CUT = .../2026-09-04-conformance-cut-17.md`; `CUT17_FREEZE_COMMIT = "<Task 1's short id>"`; `CUT17_FROZEN_SHA256 = sha256 of the file at that commit` (`git show <commit>:docs/designs/2026-09-04-conformance-cut-17.md | sha256sum`); `FROZEN_PRIOR_CUT_FILES` gains `"python/tests/n2_arms_cut16.py": "<git log -1 --format=%h -- python/tests/n2_arms_cut16.py>"`; `PRIOR_ARMS` gains `*CUT16_ARMS`; the accounting assertions become `"**17 declaration units**"`, `"Sixteen guarantee rows are read: **7 full/closed**"`, `"**5 partial**"`, `"**4 closed-row re-reads**"`; `test_the_inventory_is_exactly_the_seventeen_frozen_units` asserts the tuple above.

- [ ] **Step 3: The runner**

`python/tools/cut17_acceptance.py`, copied from `cut16_acceptance.py` with every `16` → `17`, `PREFIX_RUNNERS = ("cut16_acceptance.py",)`, `PHASE_MODULES = ("test_deletion_acceptance.py", "test_n2_cut17.py")`, `DEFAULT_WORK = PYTHON_ROOT.parent / ".cut17-acceptance"`, `SCIENCE_CUT{n}_ROOT` for `range(4, 18)`, `run_prefix` setting `SCIENCE_CUT16_ROOT`, and the final two prints reading `(= {units} declaration units; 16 guarantee rows + 1 boundary invariant)` and `row accounting: 7 full/closed + 5 partial + 4 closed-row re-reads`.

- [ ] **Step 4: Run the N2 audit and the runner**

```bash
cd python && uv run --frozen pytest tests/acceptance/test_n2_cut17.py
cd python && uv run --frozen python tools/cut17_acceptance.py
```
Expected: every arm `sound`, baseline `resolved`, runner exit 0 with the two accounting lines. A `vacuous`, `stale` or `mixed` verdict is a defect in the arm or the test — fix the test or the sabotage, never the frozen count.

- [ ] **Step 5: Commit**

```bash
git add python/tests/n2_arms_cut17.py python/tests/acceptance/test_n2_cut17.py python/tools/cut17_acceptance.py
git commit -m "test(cut17): add the N2 declarations and the acceptance runner"
tasks note beliefs-676a2c "Task 9: <n> arms normalize to the frozen 17 units; certified runner exited 0"
```

---

### Task 10: The rulings ledger

**Files:**
- Create: `docs/plans/2026-09-04-deletion-rulings-ledger.md`

- [ ] **Step 1: Write every ruling made so far**

Modelled on `docs/plans/2026-09-03-relocation-rulings-ledger.md`. Seed it with the rulings this plan already makes, then add each one the implementation forced:

- **R1 — The exclusion table has one home.** `EXCLUDED_MUTATION_KINDS` lives in `corpus.py`; `relocation.py` imports it.
- **R2 — A stored verification names its runs optionally.** The verification facet gains an optional `derivation` member; a verification without one is unchecked, never refused, so existing fixtures stay valid and `verification-publication` later writes derived verifications carrying it.
- **R3 — Scope is not recomputed.** The stored projection carries no comparison report; the audit and the import recompute verdict and assessment identity only (frozen §7).
- **R4 — Evidence is explicit.** `DerivationEvidence` is supplied by the caller; `NO_EVIDENCE` is an explicit empty value, and an unresolvable derivation is an import **finding**, never a silent pass.
- **R5 — The semantic audit is its own module.** `beliefs.audit` composes `corpus_check`; `world/verify.py` is untouched by this cut, contrary to design §9's expectation, because the contradiction findings are semantic recomputation and not log evaluation.
- **R6 — Ω_valid is instrumentation-tested.** Standing and belief evaluation are made to raise; the audit must still classify.
- **R7 — The cyclic pair is read for classification only.** The raw pair is malformed by identity recomputation; the cut asserts its classification and never its acyclicity (the banked limitation stands).
- **R8 — `gather` locates the claim through the `assesses` edge**, never by decoding every proposition, so an unrelated claim is neither read nor traced.

- [ ] **Step 2: Commit**

```bash
git add docs/plans/2026-09-04-deletion-rulings-ledger.md
git commit -m "docs(mutation): record the deletion cut's implementation rulings"
```

---

### Task 11: Gates, discharge, re-rank, and merge

**Files:**
- Create: `docs/plans/2026-09-04-conformance-cut-17-results.md`
- Modify: `docs/designs/2026-09-04-conformance-cut-17.md` (status line only), `docs/designs/2026-09-03-world-changing-families-design.md` (status line), the adoption ledger's `Current state`, `docs/plans/2026-08-29-implementation-roadmap.md` (rewritten whole), `python/tools/roadmap_status.py` (`ACCOUNTING[17]`), `README.md` (status paragraph), `docs/guide/contracts-and-adoption.md`

- [ ] **Step 1: Run every gate**

```bash
cd python && uv run --frozen pytest
cd python && uv run --frozen ruff check .
cd python && uv run --frozen pyright
cd ts && npm ci && npm test && npm run typecheck && npm run check
cd python && uv run --frozen python tools/cut17_acceptance.py
```
Expected: all pass. Quote pytest's summary line and the runner's accounting lines. A discharge over a red gate is not a discharge.

- [ ] **Step 2: Write the results record**

`docs/plans/2026-09-04-conformance-cut-17-results.md`, following the cut-16 record section for section: §1 what ran (commit, certified host facts from the runner's probe, the exact command and its output); §1.2 repository evidence; §2 accounting and per-row disposition (7 full/closed, 5 partial, 4 re-reads, 17 units, the arm count); §3 corrections and deviations (R2–R5 from the rulings ledger are **deviations from the design's expectations**, not from the frozen cut; say so); §4 what this run does not claim — nothing closes L13; scope is not recomputed; the audit is corpus-local; R19, R22, S5, R23, M3 stay part on their named remainders; T2 is untouched; **§5 implementation commits**; **§6 Remaining boundary** naming, in prose with row labels, what stays open: R19's cross-corpus arm (`world-resolution`), R22's resolver arm (`contract-cut`), R23's snapshot/coverage/divergence (`world-resolution`) and rules-store clauses (`contract-cut`), S5's cross-corpus reach (`world-resolution`), M3's coreference arm (`world-resolution`), C3 (`correction-remainder`), T2 (`act-report-remainder`).

Set the frozen cut's status line to `**Status:** Frozen 2026-09-04. Discharged 2026-09-04 (\`../plans/2026-09-04-conformance-cut-17-results.md\`).` and the design's to `... deletion cut 17 discharged 2026-09-04.`

- [ ] **Step 3: Re-rank**

- Ledger `Current state`: heading and anchor become `(2026-09-04)` (already); "Implemented through conformance cut **17**"; add a bullet **Managed deletion and the mutation-lane ride-alongs** naming what landed and which rows closed; delete the `consolidate-family`, `run-boundary-remainder` and `formal-model-remainder` rows from the boundary table (every row they owned is closed or re-homed to a boundary the table already lists — check R19's cross-corpus arm and M3's coreference arm are named in `world-resolution`'s row and R22's resolver arm in `contract-cut`'s); `correction-remainder`'s row drops "after `consolidate-family` only in the serial mutation lane".
- Roadmap: rewrite whole. `Ranked at: cut 17`; the intro paragraph states what cut 17 delivered; the boundary index and tier 1 drop `consolidate-family`, `run-boundary-remainder`, `formal-model-remainder`; `correction-remainder` becomes the mutation lane's first boundary; Appendix A is regenerated from `tools/roadmap_status.py` after adding `17: ("conformance-cut-17-results §2", "G2c, G8, C6, R5, W16, M1, M5", "S5, R23, R19, R22, M3")`; Appendix B drops every row this cut closed and rewrites the remainders of S5, R23, R19, R22, M3, C1/T8/M11/M13 (now closed, gone); Appendix C keeps M3's concrete-cycle arms and adds M1's resolver bound and the scope-recomputation limitation under R19.
- README status paragraph: "through **cut 17**", the new capability sentence, the results link. Guide: add the results record to `sources:` and the discharge sentence.

```bash
cd python && uv run --frozen python tools/roadmap_status.py
cd python && uv run --frozen pytest tests/test_designs_corpus.py tests/test_check_guide.py
```
Expected: PASS — `Ranked at` matches the newest results record; the ledger names every row §6 leaves open.

- [ ] **Step 4: Close the task record**

`beliefs-676a2c`'s outcome is now delivered in full: consolidate, move and managed deletion, with the assigned ride-alongs.

```bash
tasks done <task-11-child-id> "discharged"
tasks done beliefs-676a2c "Cut 17 discharged: managed delete, the semantic audit, import derivation validation, claim_from_stored and the instrumented resolver land; G2c, G8, C6, R5, W16, M1 and M5 close"
tasks check
```
Expected: zero errors; report every warning.

- [ ] **Step 5: Commit and merge from the repository root**

```bash
git add docs README.md python/tools/roadmap_status.py tasks
git commit -m "docs(mutation): discharge conformance cut 17 and re-rank the roadmap"

cd <repo-root>        # where main is checked out
git merge --no-ff design/consolidate-family
```
Then, from the root, re-run `uv run --frozen pytest tests/test_designs_corpus.py` and `tasks check` on `main`, and only then remove the worktree (`git worktree remove .worktrees/consolidate-family`) — the rulings ledger is already committed to its tracked path.

---

## Self-Review

**Spec coverage.** §2.2 (C1 re-read) → Tasks 2, 7. §2.3 (T8 re-read against `delete`) → Task 2. §2.5 (M11/M13 re-reads) → Task 5. §3.0 → Task 2 (`EXCLUDED_MUTATION_KINDS`, shared with relocation). §3.1 → Task 2 (no intent, no report, no referential check, no tombstone; the asymmetry table → Task 8's G8 arm). §3.6's deleted-target arm → Task 2. §6.2's every row → Tasks 2, 7, 8. §6.3: R19 → Tasks 3, 4, 8; R22 → Tasks 3, 4; M1 → Task 6; M3 → Tasks 3, 7; M5 → Tasks 7, 8. §7's two narrowings → Task 1's frozen §2/§6 and Task 7's assertions. §8 → Task 1's §7 and Task 11's §4. §9 → Global Constraints and ruling R5. §10 (a separate discharge commit, rulings committed before worktree removal) → Tasks 10, 11.

**Accepted gaps, stated in the frozen cut.** Scope is not recomputed (no comparison report in the stored projection). The audit is corpus-local. Neither weakens a *selected* clause: R19 and R22 stay part, and the frozen §2 names both exclusions.

**Placeholder scan.** Tasks 3, 4, 6, 7 and 8 carry `...` in test *sketches* with the instruction to fill them before running; every implementation code block is complete. The two `# verify` helper imports in Task 2 are resolved by the grep commands beside them.

**Type consistency.** `DerivationEvidence(specs, held_rules, implementations)`, `NO_EVIDENCE`, `DerivationOutcome(checked, reason, contradiction)` — identical across Tasks 3, 4 and 9 (the circular-import note in Task 4 moves their *definition* to `evidence.py` without renaming). `check_verification(view, node, *, evidence)` and `check_assessment` share one shape. `claim_from_stored(node, *, profile, snapshot)` in Tasks 5 and 6. `_verification_selected(value, ids)` is the single sabotage site named in Tasks 6 and 9. `CorpusWriter.delete(ref)` and `EXCLUDED_MUTATION_KINDS` in Tasks 2, 7, 8 and 9. `DECLARATION_UNITS` in Task 9 equals the 17 units Task 1 freezes.

**Accessors to verify before use, not assume:** `stored.assessment_node`, `stored.run_node`, `Finding.sort_key`, `Producer.resolved_run`, `AssessmentValue.identity`, the `@sealed` import, `EquivalenceImplementation`'s module, `ImportRefused.member`, the run-persistence path (`runrecord.publication_plan` vs the boundary), and the holdings reduction path for R5. Each task says to check and to add the missing pieces with unit tests in the same commit.

---

### Task 12: Reconcile with the write-permits lane and renumber the cut to 18

**Why this task exists.** The write-permits lane renumbered its cut to 17 at 09:41 (`398491d`) and merged into `main` at 17:24 (`da37650`); this lane froze "cut 17" at 10:50 (`2071be0`) and discharged at 18:25. Under roadmap concurrency rule 1 (numbers are claimed at freeze, in freeze order) the deletion cut is **cut 18**, its runner's prefix is the permits lane's `cut17_acceptance.py` (rule 5), and under rule 3 this later merge resolves every shared file toward `main`. The permits design's §4.2 inventory holds every write entry point statically (its E6), so the new `CorpusWriter.delete` must require the `corpus-write` permit and be inventoried by a dated amendment, exactly as that design's §14.3 inventoried the relocation seams.

**Files:**
- Merge: `main` into `design/consolidate-family` (conflicts: `README.md`, the adoption ledger, the roadmap, `python/src/beliefs/corpus.py`, `python/tests/test_relocation.py`, and three add/add pairs — the results record, `test_n2_cut17.py`, `cut17_acceptance.py` — where the permits lane keeps the 17 name and this lane's files are renamed to 18).
- Rename: `docs/designs/2026-09-04-conformance-cut-17.md` → `…-cut-18.md`; `docs/plans/2026-09-04-conformance-cut-17-results.md` (ours) → `…-cut-18-results.md`; `python/tests/n2_arms_cut17.py` → `n2_arms_cut18.py`; `python/tests/acceptance/test_n2_cut17.py` (ours) → `test_n2_cut18.py`; `python/tools/cut17_acceptance.py` (ours) → `cut18_acceptance.py`.
- Modify: `python/src/beliefs/corpus.py` (`delete` requires the permit), `python/tests/test_permit_boundary.py` (`WRITE_ENTRY_POINTS` gains `CorpusWriter.delete`), `python/tests/test_permit_entry_points.py` (an E1 case for `delete`), `docs/designs/2026-09-04-write-permits-design.md` (a dated §15 amendment inventorying `delete`), `python/tools/roadmap_status.py` (`ACCOUNTING[18]`), `python/tests/test_designs_corpus.py` (`_COUNT_WORDS` 47/48), the guide, the design status line, the rulings ledger's scope line.

- [ ] **Step 1: Merge `main`, resolving toward it.** `git merge main`; in every content conflict keep `main`'s side and re-apply this lane's additions on top (the ledger's cut-17 bullet and boundary-table edits stay; ours become cut 18); for the three add/add pairs keep `main`'s file under the 17 name and `git mv` ours to the 18 name.
- [ ] **Step 2: Renumber.** Inside the cut document: title, §1, §5 item 3 (`cut17_acceptance.py` as prefix), status line; append `## 8. Renumbering amendment — 2026-09-04` stating rule 1's ordering and that §§2–7 are otherwise byte-identical to the freeze at `2071be0`. In `test_n2_cut18.py`: `CUT18_FREEZE_COMMIT = "2071be0"`, `RENUMBERING_AMENDMENT_COMMIT = <the renumbering commit>`; the freeze test compares current §§2–7 to the amendment commit's byte-exact **and** to the freeze commit's after substituting `cut 17→cut 18`, `Cut 17→Cut 18`, `cut-17→cut-18`, `cut16_acceptance→cut17_acceptance`; `FROZEN_PRIOR_CUT_FILES` gains `python/tests/acceptance/n2_arms_cut17.py` at its last commit and `PRIOR_ARMS` gains the permits lane's `CUT17_ARMS`; `DECLARATION_UNITS`/accounting unchanged. Runner: `PREFIX_RUNNERS = ("cut17_acceptance.py",)`, `range(4, 19)`, `SCIENCE_CUT17_ROOT` in `run_prefix`, `.cut18-acceptance`.
- [ ] **Step 3: Gate `delete`.** First statement of `delete`, before the lock: `self._authority.require("corpus-write", (self._view.get(ref).kind,))` — wait: the ref must resolve first for `DeletionTargetMissing`; so resolve under the lock, then `require` on `node.kind` before `_refuse_excluded_kind` (the redundant `require` inside `_delete_locked` is the design's §4.3 harmless repeat). Add `"CorpusWriter.delete": "corpus-write"` to `WRITE_ENTRY_POINTS`; add an E1 `Case` for it (prepare: add a record under full authority; act: `delete` under the judged authority; probe: the record's file and the chain length); a `lacking`/`narrowed` authority must refuse `PermitExceeded` with the file untouched. Write the §15 amendment in the permits design (table row for `CorpusWriter.delete`, kinds required = the deleted record's kind, first statement as above), dated, without touching its §7 or §9 (pinned by the permits N2 test). Update the roadmap's "36-definition" sentence to 37.
- [ ] **Step 4: Re-rank on top of `main`.** Ledger `Current state`: "through conformance cut **18**", the cut-17 bullet stays, our bullet becomes cut 18, the boundary table as our Task 11 left it applied to `main`'s table; roadmap rewritten whole from `main`'s version: `Ranked at: cut 18`, intro paragraphs for 17 (theirs, kept) and 18 (ours), `ACCOUNTING[18]` and Appendix A regenerated, B/C as ours; README: "through **cut 18**", count word `Forty-seven`, the cut-18 row; guide: sources and "Eighteen conformance cuts"; the design status line ("deletion cut 18 discharged"); the rulings ledger's scope path.
- [ ] **Step 5: Gates on the merged tree**, all of them: pytest (summary line), ruff, pyright, ts, `uv run --frozen python tools/cut18_acceptance.py` (prefix chain cut17→16→…), docs guards + both N2 static tests (`test_n2_cut17.py` theirs, `test_n2_cut18.py` ours), `tasks check`. The results record's §1/§1.2/§5 are refreshed to the merged head; §3 gains the dated renumbering deviation and the permit gating.
- [ ] **Step 6: Commit.** Conventional commits: the merge commit; `refactor(cut18): renumber the deletion cut to 18 and gate delete behind the corpus-write permit`; `docs(mutation): discharge conformance cut 18 on the merged tree`. No merge into `main`.
