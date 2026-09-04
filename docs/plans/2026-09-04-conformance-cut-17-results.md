# Conformance cut 17 — discharge results

**Date:** 2026-09-04
**Subject:** managed deletion and the mutation lane's assigned ride-alongs
(`../designs/2026-09-03-world-changing-families-design.md` §2.2, §2.3, §2.5,
§3.0, §3.1, §3.6, §6.2, §6.3 and §7), measured against the frozen cut at
`2071be0`.

The frozen §§2–7 remain byte-exact. This discharge changes only the cut's
status line.

## 1. What ran

All Python commands ran from `python/`. The certified runner executed at
`71358f06744610f7d9eff6bb0ef8ec6b5b89057d` with its default durable work root
beside the checkout (`python/../.cut17-acceptance`, on the same volume as the
repository). It scoped XDG cache state to that disposable work root, probed
the certified durability tuple through `init_corpus_root`, ran cut 16 as its
sole prefix — which itself chains cut 15 and cut 14 — and then ran the two
cut-17 phases.

`uv run --frozen python tools/cut17_acceptance.py`

```text
[cut17 phase 1/3] cut16_acceptance.py
[cut17 phase 2/3] test_deletion_acceptance.py
16 passed in 47.55s
[cut17 phase 3/3] test_n2_cut17.py
7 passed in 23.71s
declared arms: 20 (= 17 declaration units; 16 guarantee rows + 1 boundary invariant)
row accounting: 7 full/closed + 5 partial + 4 closed-row re-reads
```

The inherited cut-16 runner completed its cut-15 prefix — which completed its
own cut-14 prefix — and every one of their phases before the cut-17 phases:
`test_n2_cut14.py` reported `declared arms: 29`, `test_n2_cut15.py`
`declared arms: 30`, and `test_n2_cut16.py` `declared arms: 27` with
`row accounting: 3 full/closed + 5 partial + 1 closed-row re-read`. The probe
accepted, so no capability refusal or tuple mismatch banner was emitted, and
the aggregate runner exited 0.

### 1.1 Certified host facts

- backend `linux`, revision `linux-4`, storage profile
  `flush-honoring-disk.v1`;
- kernel `7.2.2-arch1-1`;
- ext4 normalized options `async`, `barrier=1`, `commit=5`, `data=ordered`;
- durability features `compat=0x3c`, `incompat=0x246`,
  `ro_compat=0x46b`; and
- certification record
  `atoms/docs/certification/2026-09-03-ext4-linux-7.2.2-arch1-1.json` at
  Atoms commit `0b382a9`.

### 1.2 Repository evidence at the certified head

- `uv run --frozen pytest` — **3329 passed in 842.45s (0:14:02)**;
- `uv run --frozen ruff check .` — All checks passed;
- `uv run --frozen pyright` — **0 errors, 0 warnings, 0 informations**;
- `npm ci && npm test && npm run typecheck && npm run check` in `ts/` —
  **101 tests passed** across 5 files, `tsc --noEmit` clean, and biome
  checked 13 files with no fixes applied; and
- `tasks check` — zero errors and zero warnings.

`tests/test_production.py::test_r23_replay_cardinality_one_address_two_edges_nothing_mutated`
is a known flake under the full suite; it passed in this run, so no separate
re-run was needed.

The final discharge commit re-ran the repository's documentation, task, and
whitespace gates; that commit does not claim to know its own id.

## 2. Accounting and disposition

Cut 17 reads sixteen guarantee rows: **7 full/closed** (G2c, G8, C6, R5, W16,
M1, M5), **5 partial** (S5, R23, R19, R22, M3), and **4 closed-row re-reads**
(C1, T8, M11, M13). The boundary-invariant declaration adds no row and brings
the frozen inventory to **17 declaration units**. The executable declarations
expand those units into **20 unique one-mutation sabotage arms** over the
sixteen durable checks of `tests/acceptance/test_deletion_acceptance.py`
(G8 and C6 share one check).

- **G2c — closes.** The kernel §3.3 lifecycle table is walked row by row over
  durable records, `active` read under the standing-retraction amendment, and
  admission holds only for `clean-environment, passed` with no active
  `failed`. The raw-deletion negative runs on the same records: raw-delete a
  failing verification and the assessment returns to admitted, undetected on
  read. `delete` itself is asserted to be an ordinary write — one registered
  transaction under the root's lock and no operation intent.
- **G8 — closes.** Raw removal of the failing verification restores admission
  undetectably on the corpus read, and the asymmetry is read through
  `audit_log` over a real chain: the log audit **refutes** the raw removal,
  while a managed `delete` of the same record **validates** with
  `record-removed` and, given the held copy, `failing-verification-removed`
  at error severity.
- **C6 — closes.** The raw-deletion negative over verification retraction:
  raw deletion of a verification still restores admission undetectably on
  read, and the lifecycle is a pure function of the verifications present —
  no cross-call memory survives to detect it.
- **R5 — closes.** Negative (a): destroying the last held copy of an
  `observes` input through the managed `holdings.delete` act, which records
  an `absent` observation, leaves the input no longer held, replay
  eligibility failing, and admission **changed**.
- **W16 — closes.** Its one remaining arm: the divergent-lineage `conflict`
  written by `consolidate` still stands after deleting either producing run.
  Divergence is decided on the basis tag before any comparison, so a
  partly-resolvable conflict is still `lineage-divergent` and independence
  over it stays `not-certified`.
- **M1 — closes.** Every value the `Belief` arm reads through the
  instrumented resolver is contained in the declared closure, over a durable
  corpus exercising every closure member. The sabotage reads one extra
  value — a verification of an unrelated proposition — through `gather` and
  nothing else: the containment check fails while the belief digest is
  unchanged. The row closes carrying its own resolver bound (§4).
- **M5 — closes.** Restriction-only, quantifier-only, and
  present-versus-absent qualification each give a different `I_claim` over
  records minted into a registered root; dropping the qualifier map from
  `π_claim` collapses the founding case to one identity; re-serializing the
  qualifier map in a different key order leaves the identity unchanged.
- **S5 — part.** The deletion half: deleting an ancestor named by a basis
  yields `lineage-incomplete`, `not-certified`, a moved `belief_input_digest`
  and no belief rise; deleting a divergent producer restores the certificate,
  belief **does** rise, and the epistemic readings — corpus read, lineage
  traversal, admission, belief — are indistinguishable from a corpus in which
  that run never existed. Log verification is deliberately not one of those
  readings (§7 of the frozen cut). **Remainder:** cross-corpus reach.
- **R23 — part.** The deletion clauses: the stored basis ref and its `null`
  resolution are recorded separately, so deleting the producing run leaves
  the dataset not reading as a root, emits `lineage-incomplete`, makes
  independence `not-certified` and moves the belief digest; the same for a
  deleted ancestor; a second surviving run producing the same address by
  another route does not repair the first basis. The §11.14 residue after
  deleting `R2` is indistinguishable from a corpus where `R2` never existed.
  The audit detects the forged `single(A)` while `B`'s producing run stands,
  and once `B`'s run is deleted too the **semantic** contradiction finding
  disappears — the log audit still reports the committed removals.
  **Remainder:** producer-snapshot, coverage, cross-corpus-divergence,
  explicit-import and rules-store clauses.
- **R19 — part.** Explicit-import derivation validation over complete closure
  evidence refuses a contradicted verification **before any payload write**,
  and no file exists afterwards. Transition (b) runs end to end: a forged
  verification whose runs do not resolve imports unvalidated and admits;
  mounting the runs changes nothing; admission is still unchanged until an
  audit runs; the audit emits the contradiction finding and **mints nothing**;
  a separate constructor act naming its own contract identity and epoch mints
  the superseding verification, and admission changes because of that node.
  Negatives (d) and (e) hold with log-backed raw-write detection.
  **Remainder:** cross-corpus recomputation through the world resolver, and
  scope recomputation (§4).
- **R22 — part.** Negative (c)'s explicit-import clause: import recomputes
  the assessment facet from the run and refuses a mismatch; a raw-written
  assessment is caught only under audit. **Remainder:** the
  unresolvable-interpretation-rule refusal, which needs the rules store and
  its resolver.
- **M3 — part.** A raw-written cyclic configuration is classified malformed
  by the audit **before** any standing or belief evaluation — the arms
  instrument both readings to raise and the audit still classifies. The
  admission-order negative holds: no topological rank is stored anywhere, and
  re-admitting the same records in a different order leaves every identity
  and the `belief_input_digest` unchanged. **Remainder:** the coreference
  arm; the concrete-cycle arms stay a banked limitation.
- **C1 — closed-row re-read.** Under §2.2's narrowing, retraction is still
  additive with a deletion API in existence: the target's bytes, address and
  resolution are unchanged after `retract`, and no ordinary API edits,
  removes or re-addresses a retraction target.
- **T8 — closed-row re-read.** Against `delete`: no ordinary API deletes a
  report, `delete` refuses an act-report subject on the excluded-kinds
  precondition, and `delete` mints no report of its own.
- **M11 — closed-row re-read.** `claim_from_stored` is a function of its
  arguments over a durable record: the same stored facet decodes identically
  in two separate processes; availability is a parameter, not ambient, and
  substituting an empty snapshot changes the answer; a wrong kind and a
  missing, extra or malformed facet field are each refused before delegation,
  with nothing minted.
- **M13 — closed-row re-read.** §2.5's opacity arms against the new route: no
  `WireClaim` appears in or out of `claim_from_stored`'s signature; the
  function delegates to the module's `decode_claim` seam rather than typing
  the value itself; and the brand chain stays intact through the restore
  route.
- **Boundary re-resolution after a real deletion.** One declaration unit,
  both entry points exercised: after `delete` removes a previously resolved
  target, `retract` and `supersede` each re-resolve under the lock
  immediately before plan construction and refuse `RelocationTargetMissing`.
  The absence is produced by `delete`, never by a filesystem call.

`delete` contributes no T2 arm: it opens no operation and mints no terminal
record (§3.1 of the families design, §4 of the frozen cut).

## 3. Corrections and deviations

There is no frozen-cut deviation. The cut-17 audit pins the freeze commit
`2071be0`, the frozen whole-file digest, byte-exact §§2–7, and the exact
17-unit accounting phrases.

The deviations below are from the *design's* expectations, not from the
frozen cut's selection or accounting. Each is recorded in
`2026-09-04-deletion-rulings-ledger.md` with its reasoning.

- **The verification derivation member is optional** (ruling R2). The
  verification facet gains an optional `derivation`; a verification without
  one is *unchecked*, never refused, so existing fixtures stay valid and
  `verification-publication` can later write derived verifications carrying
  it. A verification with no derivation member therefore imports unchecked
  rather than refused (ruling R13), with a `derivation-unchecked` finding
  like any other unrecomputable member.
- **Scope is not recomputed** (ruling R3). The stored projection carries no
  comparison report, so the audit and the import recompute the verdict and
  the assessment identity only. This is the frozen §7 limitation, restated
  as an implementation ruling.
- **Evidence is explicit** (ruling R4). `DerivationEvidence` is supplied by
  the caller and `NO_EVIDENCE` is an explicit empty value; an unresolvable
  derivation is an import **finding**, never a silent pass.
- **The semantic audit is its own module** (ruling R5, the ledger's fifth
  ruling — not the guarantee row of the same label). `beliefs.audit`
  composes `corpus_check`, and `world/verify.py` is untouched by this cut,
  contrary to design §9's expectation, because the contradiction findings
  are semantic recomputation and not log evaluation.
- **Ω_valid's skip set is the malformedness codes** (ruling R10). `flagged`
  in the audit is narrowed to `semantic-hash-missing`,
  `semantic-hash-stale`, `coordination-facet-malformed` and
  `derivation-malformed` rather than every `corpus_check` finding: the
  spec's Ω_valid is about malformed classification, not about every finding
  a corpus check can report.
- **An unreadable neighbour leaves a derivation unchecked, never aborting**
  (ruling R11). A neighbour record that cannot be read leaves the audited
  record's derivation *unchecked* with a reason naming the neighbour;
  `audit_corpus` never raises on a bad neighbour file, and a
  `MalformedRecord` raised from a record's own members becomes a
  `derivation-malformed` finding.
- **`check_assessment` compares only the comparable members** (ruling R12):
  `outcome`, `interpretation_rule`, `estimate`, `uncertainty`, `estimand`
  and `applicability`, plus `spec` and a `run_ref`-normalized `run`.
  `proposition` is excluded because the stored facet carries a corpus ref
  and the derivation a claim target — different namespaces, not a
  disagreement.
- **`gather` traces the `assesses` ref it actually read** (ruling R15), not
  the one requested. Non-`observes` declarations that cross `run_value` are
  outside M1's traced set because no closure member declares them; this is
  stated in the module's own docstring and carried into §4 below rather than
  narrowed in code.
- **S5's belief-rise arm is required and constructible** (ruling R16).
  Observed datasets are minted at their content addresses so belief's
  `certify` keys resolve against the snapshot's bases; the durable arm uses
  the same construction.
- **Two of the plan's minimum N2 sabotages were substituted** (ruling R18).
  The intent-before-`_delete_locked` mutation is homed under G2c instead of
  its planned row; G8's arm flips the held verdict in `world/verify.py`; and
  M13's arm binds `decode_claim` as an import-time default rather than
  taking a `Claim._checked` self-typing path. Every declaration unit stays
  covered and all 20 arms audited sound.

A ninth ruling is procedural and changes no behavior: the tasks CLI cannot
attach a plan outside `docs/plans/`, so the eleven task children carry their
plan and step in prose bodies (ruling R9, filed upstream as `tasks-1eb9d2`).
Two further rulings record where a decision was homed rather than what it
decided — `EXCLUDED_MUTATION_KINDS` lives in `corpus.py` and `relocation.py`
imports it (ruling R1), and the family-adapters design's frozen
`import_bundle` signature listing was not edited for the widened `evidence`
keyword (ruling R17).

One implementation discovery is banked without changing the frozen
selection: nothing refuses a divergent `assesses` edge at admission, and M1
detects it. That is a candidate audit finding for a later cut (ruling R19,
the ledger's nineteenth ruling), outside this cut's frozen selection.

## 4. What this run does not claim

- **Nothing here closes L13.** Removal classification stays a path match
  against a held copy, never a match by bytes.
- **Scope is not recomputed.** A stored verification carries no comparison
  report, so the audit and the import recompute the verdict and the
  assessment identity only; scope recomputation waits on
  `verification-publication`.
- **The audit is corpus-local.** It runs over a `ReadView` and
  caller-supplied evidence; nothing here resolves across corpora, and it
  writes nothing and mints nothing.
- **M1's traced set is bounded by the resolver, and by what the closure
  declares.** A read that never crosses the instrumented resolver is
  invisible, and non-`observes` declarations that cross `run_value` are
  outside the traced set because no closure member declares them.
- **M11's determinism is asserted across processes, not across checkouts.**
  The durable arm decodes the same stored facet in two separate processes
  against one checkout.
- S5 remains part on its cross-corpus reach; R23 on its producer-snapshot,
  coverage, cross-corpus-divergence, explicit-import and rules-store
  clauses; R19 on cross-corpus recomputation; R22 on the
  unresolvable-interpretation-rule refusal; M3 on its coreference arm and
  its banked concrete-cycle limitation.
- **T2 is untouched.** `delete` opens no operation and mints no terminal
  record, so it contributes no act-report arm.
- **No interrupted operation is completed.** `delete` is one transaction and
  has no prefix set.

## 5. Implementation commits

| commit | subject |
|---|---|
| `d3b7186` | chore(tasks): close Task 1, freeze conformance cut 17 |
| `69e3aa1` | feat(corpus): add managed delete as an ordinary write |
| `5f93239` | feat(audit): add the corpus-local semantic audit and the verification derivation member |
| `7a3664a` | fix(audit): report malformed records instead of aborting the audit |
| `d617e57` | fix(audit): leave a record unchecked when a neighbour cannot be read |
| `a325aa6` | feat(import): recompute verification and assessment derivations at explicit import |
| `6dabf80` | test(audit): assert the checked arms of verification recomputation |
| `705222a` | feat(decode): add claim_from_stored, the M13-conforming restore seam |
| `b013a26` | fix(decode): reuse _wire_parts for claim_from_stored's qualifier-body check |
| `75a9291` | feat(evaluation): add the instrumented resolver and the corpus-backed evaluation path |
| `fae2dd4` | chore(tasks): note task 6's landing on the deletion-cut goal |
| `c061592` | fix(evaluation): trace the proposition ref the resolver read, not the one requested |
| `89dd217` | test(deletion): pin the frozen cut-17 rows over the ordinary-write delete |
| `6dd283a` | test(deletion): run S5's belief rise and unify the row fixture builder |
| `e7c9e64` | test(cut17): add the durable deletion arms |
| `00cd3b8` | test(cut17): add the N2 declarations and the acceptance runner |
| `71358f0` | docs(mutation): record the deletion cut's implementation rulings |

This results record is committed with the discharge change and therefore does
not embed its own commit id.

## 6. Remaining boundary

`consolidate-family` closes with this discharge: managed deletion was the last
world-changing family it owned, and every row it carried is either closed here
or re-homed to a boundary the ledger's table already lists. Its two assigned
ride-alongs close with it — `run-boundary-remainder`, whose R22 explicit-import
and audit arms are read here, and `formal-model-remainder`, whose M1, M5 and
M3 audit and admission-order arms are read here. No new boundary is created.

`world-resolution` takes every cross-corpus remainder: R19's cross-corpus
recomputation through the world resolver, S5's cross-corpus reach, M3's
coreference arm, and R23's producer-snapshot, coverage and
cross-corpus-divergence clauses.

`contract-cut` takes R22's unresolvable-interpretation-rule resolver arm and
R23's rules-store clauses.

C3 stays with `correction-remainder`, which is now the mutation lane's only
open boundary. T2's other operation-family clauses stay with
`act-report-remainder`; `delete` adds no arm to them. L13 stays with
`l13-preimage`, unmoved by this cut.
