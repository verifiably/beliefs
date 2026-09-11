# Conformance cut 21 — results

**Cut:** `../designs/2026-09-06-conformance-cut-21.md`, frozen 2026-09-06 at
`41c9920`, digest
`eaf214761627a22b9a74713bfe88a2bb4adb0cfd73496110929fb4d9f4af1be5`
**Subject:** verification publication — a derived verification published as an
ordinary `add` carrying its whole basis and its comparison report, one spelling
for the assessment's run member, admission over records read back, scope
recomputed from a stored verification, forgery refused before the intent, and
the stored `analysis-spec` builder and reader
**Discharged:** 2026-09-07, on `feat/verification-publication`
**Runner:** `python/tools/cut21_acceptance.py`

The implementation landed on `main` at `965fe7f` on 2026-09-07, ahead of this
discharge: the slice's Tasks 0–11 merged when the `domain` lane's cut 20 was
still open, and its Task 12 — this record — waited for cut 20 to discharge and
merge, which it did at `b818471`. Every ruling made while the implementation
ran is in `2026-09-06-verification-publication-execution.md`.

## 1. What ran

### 1.1 The certified cut-21 runner

`uv run --frozen python tools/cut21_acceptance.py`, from `python/`, with the
runner's default durable work root at `../.cut21-acceptance` on the certified
volume beside the checkout. It created one probed run directory, forwarded a
writable per-run cache to the N2 children, and removed the run directory
afterwards. **Exit code 0.**

The chain is cut 21 → cut 20 → cut 19 → cut 18 → cut 17, which re-roots it:
`cut17_acceptance.py` carries an empty `PREFIX_RUNNERS` and names its own
nineteen-module inventory, so that inventory is the whole current-tree prefix.
Every phase passed — the runner returns on the first non-zero, so exit 0 is
that claim. The captured transcript is the run's last sixty lines; the
per-phase timings of cut 17's phases 1–10 (`test_n2_cut6.py`,
`test_n2_cut7.py`, `test_n2_cut9.py`, `test_intent_boundary_acceptance.py`,
`test_n2_cut11.py`, `test_successor_admission_acceptance.py`,
`test_n2_cut12.py`, `test_confinement_acceptance.py`, `test_n2_cut13.py` and
`test_coordination_acceptance.py`) scrolled past the capture and are not
reproduced here.

```text
[cut17 phase 11/19] test_n2_cut14.py
7 passed in 13.15s
[cut17 phase 12/19] test_cut15_lineage.py
5 passed in 77.49s (0:01:17)
[cut17 phase 13/19] test_n2_cut15.py
8 passed in 44.17s
[cut17 phase 14/19] test_relocation_acceptance.py
16 passed in 62.37s (0:01:02)
[cut17 phase 15/19] test_n2_cut16.py
7 passed in 75.85s (0:01:15)
[cut17 phase 16/19] test_permit_acceptance.py
8 passed in 4.02s
[cut17 phase 17/19] test_permit_boundary.py
18 passed in 2.21s
[cut17 phase 18/19] test_permit_entry_points.py
102 passed in 24.51s
[cut17 phase 19/19] test_n2_cut17.py
8 passed in 15.02s
declared arms: 24 (= 8 selected + 1 labeled units)
[cut18 phase 2/3] test_deletion_acceptance.py
16 passed in 50.72s
[cut18 phase 3/3] test_n2_cut18.py
7 passed in 26.22s
declared arms: 20 (= 17 declaration units; 16 guarantee rows + 1 boundary invariant)
row accounting: 7 full/closed + 5 partial + 4 closed-row re-reads
[cut19 phase 2/3] test_session_acceptance.py
27 passed in 28.46s
[cut19 phase 3/3] test_n2_cut19.py
7 passed in 26.49s
declared arms: 43 (= 11 declaration units; 11 guarantee rows)
row accounting: 11 full/closed + 0 partial + 0 re-reads
[cut20 phase 2/3] test_facet_acceptance.py
17 passed in 37.82s
[cut20 phase 3/3] test_n2_cut20.py
5 passed in 33.71s
declared arms: 12 (= 18 declaration units; 16 guarantee rows + parity fixture + boundary invariant)
row accounting: 15 full/closed + 1 partial
[cut21 phase 2/3] test_verification_acceptance.py
4 passed in 6.88s
[cut21 phase 3/3] test_n2_cut21.py
7 passed in 34.33s
declared arms: 25 (= 8 declaration units; 8 guarantee rows)
```

The last line is the cut's own accounting, printed from the declaration rather
than from a literal, and it agrees with §2 below.

### 1.2 Certified host facts

- backend `linux`, revision `linux-4`, storage profile
  `flush-honoring-disk.v1`;
- kernel `7.2.2-arch1-1`;
- ext4 normalized options `async`, `barrier=1`, `commit=5`, `data=ordered`;
- durability features `compat=0x3c`, `incompat=0x246`, `ro_compat=0x46b`; and
- certification record
  `atoms/docs/certification/2026-09-03-ext4-linux-7.2.2-arch1-1.json` at Atoms
  commit `0b382a9` — the same tuple cut 19 and cut 20 discharged on.

### 1.3 Repository evidence at the discharge head

All from `python/`, at the discharge head:

- the portable suite — **4057 passed, 0 failed**, in four alphabetical chunks
  of the 141 test modules (892 + 800 + 991 + 1374, each its own pytest process,
  each exiting 0). The chunking is an artifact of this machine, not of the
  suite: two whole-suite background runs were killed by a memory monitor
  reading `free` (20 GiB, with 93 GiB in page cache) rather than `available`
  (97 GiB). The same 4057 count was measured whole earlier the same day, at
  `8b7fbc3`, in 1033.84s;
- `uv run --frozen ruff check .` — All checks passed;
- `uv run --frozen pyright` — **0 errors, 0 warnings, 0 informations**;
- `uv run --frozen pytest tests/test_designs_corpus.py` — 14 passed, which is
  what holds this record, the ledger and the roadmap to one set of boundary
  ids and to `Ranked at: cut 21`;
- `uv run --frozen python tools/check_guide.py` — clean; and
- `tasks check` — zero errors and zero warnings.

The runner in §1.1 ran against this tree's base-contract reader line and cut
21's pin table, both landed before it started; every commit after it is
documentation. The freeze doctrine that preceded this discharge
(`../superpowers/specs/2026-09-07-frozen-guard-doctrine-design.md`, `8b7fbc3`)
also added the live-pin check, so the 144 freeze pins across the 18 guard
modules are now measured by the portable suite rather than only at a
discharge: **14 live guards, every pin holding; 4 cited not run, whose three
falsified pins are recorded and not repaired.**

### 1.4 The reproduction driver's step 10b

The driver ran into a fresh root,
`.work/reproduction/mm30-cut21-discharge` on the certified volume beside the
main checkout, in the order each module's own docstring fixes — `preflight`,
`select_target`, `world`, `type_target`, `hold`, `spec`, `run`, `belief`,
`close`, `rederive`. It selected the same target as the 2026-09-05 record from
275 candidates (`proposition:concept-disease-stage-affects-protein-phf19` over
`dataset:gse179929`), held the dataset at
`sha256:c74ea661…`, froze spec `86aaa1a8…`, and executed the confined run
`run:04fac81c…` to an **inconclusive** assessment with scope
`clean-environment` and verdict `passed`.

**`belief` printed `admission Admitted`.** On 2026-09-05 the same step reached
`NoBelief(no-eligible-assessment)` because the derived value digested the bare
run address while the stored record carried the typed `run:` ref — the defect
V2 closes. The answer is now
`NoBelief(no-directional-outcome)`: the analysis itself is inconclusive, so
the evaluator has no direction to believe. That is a scientific outcome, not a
plumbing one, and it is the first time this path has produced one.

`close` reported `corpus_check: 0` and `audit_corpus: 0`, with log
verification `validated` through head `5cc3f751…` for the head-carrying
observer and `unresolvable` for the no-observer case, as its design expects.

Step 10b, in a fresh process:

```json
{
  "10a": { "kind": "NoBelief", "reason": "no-directional-outcome", "detail": "" },
  "equal": true,
  "10b": {
    "inputs": {
      "corpus": [
        "verification record (basis, comparison report, scope, verdict read)",
        "two run publications",
        "analysis-spec record"
      ],
      "in_process": ["interpretation and equivalence RuleImplementations"]
    },
    "comparison_report_stored": true,
    "derivation_named": true,
    "closures_decoded": true,
    "scope_recomputed": "clean-environment",
    "scope_equal": true,
    "verdict_recomputed": "passed",
    "verdict_equal": true,
    "report_identity_equal": true,
    "spec_restored_identity_matches_run": true,
    "audit_check": { "checked": true, "reason": "", "contradiction": null },
    "scope_read": "clean-environment",
    "verdict_read": "passed",
    "report_identity_read": "621126889a3fb85600ffab5419a7adb904765428275e1d0585c134e1c775a8a6"
  }
}
```

This is the measurement the mm30 reproduction record's §3 row 10b and §5
question 3 left open: the comparison report is now **in the corpus**, scope and
verdict are read and recompute equal, the report identity matches, and the only
in-process input is the rule implementations — the limitation §4 restates.

**One prerequisite the driver still cannot meet on its own.** Four analysis
parameters — `value_row`, `value_row_symbol`, `group_separator` and
`positive_level` — were supplied by hand into the generated `target.yaml`
before `spec`, exactly as the 2026-09-05 run required and taken from it
verbatim. No driver step writes them; the gap belongs to
`select_target.py`/`type_target.py` and is `beliefs-efc32d`, owned by the
reproduction lane. This run is therefore evidence that **10b reads the stored
report correctly once target selection is complete**, and is not a claim that
the driver reproduces end to end unaided.

**Closed 2026-09-10 (`beliefs-efc32d`).** A new driver step, `analysis_inputs.py` (step 2a), now derives those keys itself: the symbol from the proposition's protein term, the row through the crosswalk the dataset record's `identity_context` names, the levels from the held file's header, and the separator and level order from the driver's checked-in `analysis-inputs.yaml`, which the header must agree with. Rebuilt unaided into `.work/reproduction/mm30-rebuild`, `target.yaml` was identical to the frozen 2026-09-05 file, the spec froze to the same identity `86aaa1a8…`, and the full path reached `clean-environment`, `passed`, `Admitted` and an equal 10a/10b re-derivation; the ledger is `docs/plans/2026-09-10-mm30-reproduction-rebuild-run/`.

## 2. Accounting and disposition

Cut 21 reads eight guarantee rows: **8 full/closed** (V1–V8), 0 partial, 0
closed-row re-reads. It selects no row of any other table and closes none;
R19's stored-verification limitation closes by V4 and is restated below as its
cross-corpus arm only, and J1 and J10 are re-read informally by V5 without
being counted. The frozen inventory is **8 declaration units**, one grouped
unit per row; the executable declarations expand them into **25 unique
one-mutation sabotage arms** over **26 distinct checks** — V1×2, V2×7, V3×1,
V4×3, V5×3, V6×1, V7×1, V8×7 — mutating `audit.py` (7), `verify.py` (6),
`corpus.py` (4), `stored.py` (3), `spec.py` (3), `admission.py` (1) and
`evaluation.py` (1). Every arm audited **sound**: none vacuous, mixed,
uncollected or stale. `CO_CITED` is empty — no check of cuts 3–20 is reclaimed.

- **V1 — closes.** A published verification is recoverable from the corpus
  alone: `decode_verification` over the stored record restores a
  `StoredVerification` whose basis equals the derived value member for member,
  whose report identity equals the derived report's, and whose scope and
  verdict are read rather than recomputed. The durable arm reopens the corpus
  in a fresh process with the runs deleted and decodes without reading one.
  *(`test_verify.py::test_v1_publication_node_round_trips_through_the_reader`;
  `acceptance/test_verification_acceptance.py::test_v1_a_published_verification_is_recoverable_in_a_fresh_process_with_the_runs_gone`;
  `test_verify.py::test_v5_a_record_id_that_does_not_recompute_is_malformed`.)*
- **V2 — closes.** One spelling for the assessment's run member: the derived
  value and the stored record agree, `stored.assessment_value` hands back the
  bare form and refuses an untyped one, `typed_ref` and `local_id` are
  inverse, admission matches a typed run ref to the bare member, and one
  identity admits over the corpus and audits clean. This is the defect the
  mm30 reproduction measured as `NoBelief(no-eligible-assessment)`.
  *(`test_stored.py::test_v2_assessment_value_hands_back_the_bare_run_and_refuses_an_untyped_one`,
  `::test_v2_typed_ref_and_local_id_are_inverse_and_agree_with_run_ref`;
  `test_admission.py::test_v2_admit_matches_a_typed_run_ref_to_the_bare_member`;
  `test_verification_identity.py::test_v2_one_identity_admits_over_the_corpus_and_audits_clean`;
  `test_audit.py::test_v2_a_contradicted_assessment_still_contradicts`,
  `::test_v4_a_published_verification_audits_checked_with_no_contradiction`.)*
- **V3 — closes.** A superseding verification publishes its typed predecessor,
  and a superseding failed verification invalidates and retires it.
  *(`test_verify.py::test_v3_a_superseding_verification_publishes_its_typed_predecessor`;
  `test_verification_publication.py::test_v3_a_superseding_failed_verification_invalidates_and_retires_its_predecessor`.)*
- **V4 — closes.** Scope, rule, scope rule and report recompute from the
  stored verification: a self-consistent forgery contradicts on the altered
  member — scope and report receipt each proven separately — and a certified
  verification audits clean through its stored certification. **This is what
  lifts R19's stored-verification limitation** (cut 18 §7): the stored
  projection now carries the comparison report, so the audit and the import no
  longer recompute the verdict and the assessment identity alone.
  *(`test_audit.py::test_v4_a_self_consistent_forgery_contradicts_on_the_altered_member[scope]`,
  `[report-receipt]`, `::test_v4_a_certified_verification_audits_clean_through_its_stored_certification`.)*
- **V5 — closes.** Forgery is refused before the intent: each forged
  verification refuses at `add` with the head unchanged and no intent
  appended, and every forgery refuses an import bundle while the well-formed
  record imports. The durable arm proves the head-unchanged half on a real
  root.
  *(`test_operation_writes.py::test_v5_each_forgery_is_refused_before_the_intent`;
  `acceptance/test_verification_acceptance.py::test_v5_each_forgery_is_refused_with_the_head_unchanged_and_no_intent`;
  `test_import_derivation.py::test_v5_every_forgery_refuses_the_bundle_and_the_well_formed_record_imports`.)*
- **V6 — closes.** A present but malformed report or member is refused, never
  repaired.
  *(`test_verify.py::test_v6_a_present_but_malformed_report_or_member_is_refused`.)*
- **V7 — closes.** The production shape publishes: a
  `DatasetProductionVerification` becomes an edge-less record with no
  `assessment` member, is never selected by `gather`, and admits nothing.
  *(`test_verify.py::test_v7_the_production_shape_publishes_edge_less_and_admits_nothing`.)*
- **V8 — closes.** The analysis-spec record round-trips: `analysis_spec_node`
  writes a stamped record and `analysis_spec_value` restores a `FrozenSpec`
  equal member for member, `Decimal` type included; a falsely identified or
  renamed record is `MalformedRecord` at read, refused at `add` and refused as
  a bundle member; non-canonical text and the unfreezable pair are refused;
  and the audit names a spec that does not restore while `stored_specs`
  reports it.
  *(`test_spec.py::test_v8_restore_round_trips_every_member_and_the_decimal_by_type`,
  `::test_v8_restore_refuses_a_projection_that_does_not_digest_to_the_identity`,
  `::test_v8_restore_refuses_non_canonical_text_and_the_unfreezable_pair`;
  `test_stored.py::test_v8_a_renamed_or_falsely_identified_record_is_malformed`;
  `test_corpus_write.py::test_v8_a_spec_record_whose_identity_is_false_is_refused_at_add`;
  `test_import_derivation.py::test_v8_a_spec_record_whose_identity_is_false_refuses_the_bundle`;
  `test_audit.py::test_v8_the_audit_names_a_spec_that_does_not_restore_and_stored_specs_reports_it`.)*

## 3. Corrections and deviations from the frozen cut

Every substitution from the frozen §3 and §5, dated 2026-09-07 unless the
implementation dates it earlier.

1. **V3's negatives live in `test_verification_publication.py`**, not
   `test_evaluation.py` as §5 names: importing the evaluation test module into
   the publication one is circular. The check node ids above are the ones that
   ran.
2. **V5's "after `append_intent`" sabotage is declared inside
   `_refuse_verification`** — an intent appended through the port before the
   check — rather than by moving the call in `_commit`. The mutation proves
   the same ordering.
3. **The base contract names one reader, not three.** The cut's §7 leaves the
   `verification` reader line to the `domain` lane's merge, and the design's
   §11 asks for `verify.decode_verification` "as a third reader". The compiled
   shape does not admit a list: `contract/facets.py` permits exactly
   `{shape, description, reader}`, requires one non-empty string, and discards
   it — `FacetDecl` keeps no reader name. The line therefore names
   `verify.decode_verification`, the reader of the whole facet, and the
   facet-contracts design's §3.2 reader table records all three under its own
   dated amendment (§15 there). Both copies of `CONTRACT.yaml` stay
   byte-identical.
4. **Cut 20's arms are pinned at two paths.** `n2_arms_cut20.py` exists twice —
   the canonical table at `python/tests/n2_arms_cut20.py` (`8639771`) and a
   thin re-export at `python/tests/acceptance/n2_arms_cut20.py` (`d5e203c`)
   that the acceptance import resolves to first. Both are pinned, so the
   re-export cannot be repointed without breaking the freeze.

## 4. What this run does not claim

The cut's §7 limitations, inherited from the design's §9 and restated at the
freeze, all stand: the `proposition` member keeps two namespaces; derivation
validation stays corpus-local, and cross-corpus recomputation is
`world-resolution`'s; a false certification is not detected, the remedy being
a superseding verification; the rule implementations are in-process; nothing
re-stamps existing records; and belief input digests move for every corpus,
with nothing on disk naming one.

Two further bounds on this run:

- **Prior-cut arm staleness is not measured here.** The audit proves every
  cut-21 arm sound; the eight arms found already stale in
  `n2_arms_cut{3,4,5,6,7,16}.py` before this slice began are `beliefs-ee11e2`,
  and no arm of theirs runs in this chain.
- **This was `cut21_acceptance.py`'s first execution.** Its control flow had
  never run — `PREFIX_RUNNERS` named a `cut20_acceptance.py` that did not
  exist until `b818471`, so `main()` returned 1 before its probe
  (`beliefs-8bcec6`). The transcript in §1.1 is the runner's first real run,
  not a re-run of a known-good command.

## 5. Implementation commits

- Tasks 0–11: `3969e05..331c534` on `feat/verification-publication`, merged
  `--no-ff` into `main` at `965fe7f` (2026-09-07);
- the `domain` lane's cut 20, merged at `b818471`, which this cut's chain
  runs as its prefix;
- `8b7fbc3` — the freeze doctrine, the cited-not-run registry and its checks,
  and the restoration of cut 5's guard with cut 14's pin over it
  (`../superpowers/specs/2026-09-07-frozen-guard-doctrine-design.md`); and
- this record's own commit, which carries the contract reader line, cut 20's
  arms pins, the ledger, the roadmap and the README.

## 6. Remaining boundary

`verification-publication` closes and leaves the ranking. The `write-path`
lane has no open boundary.

What stays open in the rows this cut touched is `world-resolution`'s: R19's
cross-corpus recomputation through the world resolver, alongside W1, W2, W4,
W5a, W6, W7, W8, W8b, W10, W15, W13's remaining clauses, W8a's coreference
arms, S1, S1a, S5's cross-corpus reach, D3, X12's and M3's coreference arms,
and R23's snapshot, coverage, divergence and explicit-import clauses. On the
path, the next boundary is the `domain` lane's biology pack — slice 2 of
`domain-boundary`.

## Citation amendment — 2026-09-11

The live guard’s cut-17 declaration pin is re-cited from orphaned `1d8f293`
to landed `c367070`. Git confirms identical `n2_arms_cut17.py` bytes at both
commits. This corrects a remaining address from the 2026-09-05 history rewrite;
the frozen declarations and discharge evidence are unchanged.
