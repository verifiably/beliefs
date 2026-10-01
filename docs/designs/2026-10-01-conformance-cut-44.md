# Conformance cut 44 — mount citations

**Status:** discharged 2026-10-01; J16–J21 closed; [results](../plans/2026-10-01-conformance-cut-44-results.md). Frozen body below unchanged.
**Design:** [mount citations design](../superpowers/specs/2026-10-01-mount-citations-design.md), approved 2026-10-01.
**Plan:** [implementation plan](../superpowers/plans/2026-10-01-mount-citations.md).
**Numbered** after cut 43 under roadmap rule 1. The branch scan on 2026-10-01 found no `conformance-cut-44` or later document on any branch or remote ref.

## 1. What this cut is

Cut 43 lets a session write one root and mount N read corpora, but left every non-coordination write reading the write root alone. A record's identity is its content, so a dataset another corpus declares cannot be declared again in the write root without a `duplicate-location` that refuses every world read, and a record that cites the mount's dataset cannot be written: the writer's eligibility, `assesses`-target, estimand-target, verification and composite checks each refuse a citation the write root does not hold.

The same assumption runs through the checks and the belief read. `corpus_check` reports an assessment whose run or observed dataset lives in another corpus as an `eligibility-unmet` error; `audit_world` runs the same per-corpus record findings over each captured corpus alone, so it reports that error for a record the world supports; and a corpus-local `gather` drops a run input the corpus does not hold without saying so, so admission judges a run with part of its lineage missing. The epoch-bound world read already resolves across corpora; what is unproven is the split two installations produce, with the assessment and its run in one corpus and the proposition and observed dataset in another.

This cut lets the session's write boundary resolve those citations over the write root and every read mount, reports unresolvable eligibility as a warning rather than an error, makes the world audit judge eligibility over its capture, proves the two-installation split evaluates over a world read, and makes a corpus-local belief read refuse an input it does not hold. Science's second-project milestone and its commons milestone 1a consume it.

The cut opens `mount-citations` in the `write-path` lane, which it reopens, on the path to the second-project milestone. Mutation targets stay in the write root.

## 2. The boundary

The files Tasks 1–5 change or create are:

- `python/src/beliefs/errors.py`, `python/src/beliefs/corpus.py` (`MountCitations`, `_SessionOverlay`, `EligibilityOutcome`, `eligibility_outcome`, the writer's citation scope, `_refuse_cited`, `_refuse_facets`, `_refuse_ineligible`, `_record_findings`' arm);
- `python/src/beliefs/acquisition.py` (`reports=`), `python/src/beliefs/session/__init__.py`, `python/src/beliefs/audit.py`, `python/src/beliefs/evaluation.py`;
- `python/tests/test_mount_citations.py` (new), `test_session_writer.py`, `test_read_side.py`, `test_world_audit.py`, `test_domain_facet_read.py`, `test_world_view.py`;
- `python/tests/acceptance/test_n2_cut20.py` and `python/tests/acceptance/test_n2_cut22.py` (re-targets, §5).

Every new N2 sabotage targets `corpus.py`, `session/__init__.py`, `audit.py` or `evaluation.py` as specified in §5. Task 6 adds `python/tests/acceptance/test_mount_citations_acceptance.py`; Task 7 adds the declarations, guard, runner and recent-cut row.

## 3. Selection

Six guarantee rows are selected from the writer-session design. Their text is byte-exact from the linked mount citations design §7 at freeze.

```markdown
| **J16** | In a session with read mounts, the write boundary resolves the citations of decision 2 over the write root and every read mount, reads each cited record in its holding corpus under the writer's profile, refuses a citation across differing identities of one namespace, and judges producers over the whole session on every path. The write lands in the write root alone | Corpus M (read mount) pins base, `biology` and a test-local contract W does not pin. M holds a dataset with a valid empirical-observation facet, a proposition, and an assessment with its run. In a session writing W: a run observing M's dataset, then an assessment of M's proposition over that run → written to W. An analysis spec targeting M's proposition → written. **Contracts:** M2 pins a different identity of a test-local namespace W also pins (two versions of one fixture contract), and citing M2's proposition → `CitationContractMismatch` naming M2, the namespace and both pins. **Producers:** each of these is set up by library writers on one root at a time, which cannot see the other corpora, so dangling edges are legal.<br>- A run in W whose `produces` names an address nothing holds, then a dataset at that address declared with the facet → `AcquisitionBoundaryRefused`, as on a one-root writer. The same with the dangling edge in M's run → refused.<br>- M3 holds a run producing M's facet-bearing dataset. An assessment over a W run observing that dataset → `EligibilityUnmet` naming M3's run.<br>- W holds a dataset without the facet, and M's run produces it. `revise` adding the facet → refused.<br>- M's run produces the address an `acquire` in the session would mint → the acquisition refuses.<br>- **Reverse direction:** `import_bundle` in the session of a bundle holding a run whose `produces` names M's facet-bearing dataset → `ImportRefused` naming the run as `member`, whose `__cause__` is `AcquisitionBoundaryRefused`. A plain write of such a run → `AcquisitionBoundaryRefused`.<br>- **Imported assessment:** W holds a facet-bearing dataset and a run observing it, and M holds a run producing that dataset. `import_bundle` of a bundle holding only an assessment over W's run → `ImportRefused` naming the assessment as `member`, whose `__cause__` is `EligibilityUnmet` naming M's run.<br>- **Split retrieval:** a dataset written in W whose payload's `retrieval` names an acquisition report held only in M → `FacetPayloadRefused` (`facet-retrieval-unresolved`). The same dataset raw-written into W, then an assessment over a W run observing it → `EligibilityUnmet` naming `facet-retrieval-unresolved`. The same dataset raw-written into W → `corpus_check(W)` and `audit_world` both report `facet-retrieval-unresolved`, and no other finding on it. A verification of M's assessment → written. A composite over M's propositions → written. M's tree hash is unchanged (J15). A session whose `mounts` names the write root by a symlinked path → opens, and J16's writes behave the same. **Negative:** the same writes through a library `CorpusWriter` on W, and through a session with `mounts=None`, refuse as §1 lists, with today's messages |
| **J17** | A citation two session corpora resolve refuses `AddressMapConflict` (`duplicate-location`, naming both), and a read mount whose operation lock is held refuses `BuildContended`. Both happen before any effect, with nothing written | M1 and M2 both hold a dataset at one address (a raw write into M2). An assessment over a run observing it → `AddressMapConflict` naming M1 and M2, and W unchanged. The same with the address held by W and M1 → refuses naming both. With M's operation lock held by another holder, an assessment citing M → `BuildContended`, and W unchanged. **Negative:** a write citing only W's records while M's lock is held → `BuildContended` (decision 5: the chain opens every read mount), and a write citing nothing (a proposition) → written |
| **J18** | `corpus_check` reports an assessment whose eligibility rests on references the corpus does not hold as `eligibility-unresolved` (warning). Locally decided failures stay `eligibility-unmet` (error) | W after J16's session: `corpus_check(W)` → one `eligibility-unresolved` warning per cross-mount assessment, naming the references, and no error. A raw-written assessment over a held run with no `observes` input → `eligibility-unmet` error (S7's case, unchanged). A run observing one held invalid dataset and one unheld dataset → `eligibility-unresolved`. **Negative:** a run observing only held invalid datasets → `eligibility-unmet` |
| **J19** | `audit_world` judges eligibility across covered corpora from the captured records, never raising: supported → no finding, unmapped → `eligibility-unmet`, held by an absent, damaged or excluded corpus, or by a malformed record → `eligibility-unresolved` naming the corpus and cause, and the audit continues | Publish an epoch over W and M after J16's session: `audit_world` → no eligibility finding. **Captured, not live:** the test wraps `open_world_view` so that, after the view captures and before the audit reads it, M's carrier loses the dataset's retrieval act-report (a raw delete) → still no eligibility finding. Remove M's carrier → `eligibility-unresolved` naming M, `absent`. Make one of M's files fail construction → `eligibility-unresolved` naming M, `damaged:construction`, with W's other records still audited and M's readable remainder audited as today. **Absent producer:** W holds an assessment, its run and the facet-bearing dataset that run observes, and M holds a run producing that dataset. Over an epoch covering both → `eligibility-unmet`. Remove M's carrier → still `eligibility-unmet`, because the epoch's published producers name M's run. A drift dataset in W, produced by nothing present, while M is absent → `eligibility-unresolved`, `producers-incomplete:M`. Make M's dataset's semantic stamp stale (a raw write before the epoch) → `eligibility-unresolved`, `malformed:semantic-hash-stale`, beside M's own `semantic-hash-stale` finding. Rebuild with W's run observing an M dataset that carries no empirical-observation facet (a well-formed record, so not in M's malformedness set) → `eligibility-unmet`. A malformed-payload dataset is the `unreadable` case, not this one: `facet-payload-malformed` is a malformedness code. **Negative:** an epoch covering W alone (M not admitted) → `eligibility-unmet`, since no covered corpus maps the dataset |
| **J20** | Belief over a world read gathers, admits and evaluates the two-installation split: assessment and run in W, proposition and observed dataset in M | Over the J19 epoch: `evaluate_over(world_view, M's proposition, …)` → the same answer, admission and `node_corpus` attribution (assessment and run → W, the others → M) as the same records evaluated from one corpus, and a lineage snapshot that reaches M's dataset. **Negative:** with M's carrier absent → `NoBelief("unavailable-corpus-absent")` naming M |
| **J21** | A corpus-local belief read refuses an assessment whose run names an input the corpus does not hold. It supersedes B4's absent-dataset clause ("nothing refuses"), cited (§13) | W holds a proposition P, assessed in the session over a run observing M's dataset. `gather(ReadView(W), P)` → `InputOutsideCorpus` naming the assessment, run and dataset, and `evaluate_over` → `Refused("input-outside-corpus: …")`. **Negative:** the same proposition over a world view → evaluates (J20) |
```

Twenty-four declaration units are selected, one per arm:

| unit | row | check |
|---|---|---|
| J16-a | J16 | `test_mount_citations.py::test_an_assessment_over_a_mount_dataset_and_proposition_is_written` |
| J16-b | J16 | the same |
| J16-c | J16 | `::test_a_verification_of_a_mount_assessment_is_written` |
| J16-d | J16 | `::test_a_citation_across_differing_identities_refuses` |
| J16-e | J16 | `test_session_writer.py::test_the_session_writer_cites_its_read_mounts` |
| J16-f | J16 | `::test_an_assessment_over_a_dataset_a_third_mount_produces_refuses` |
| J16-g | J16 | `test_session_writer.py::test_a_symlinked_write_root_mount_key_is_filtered_after_normalization` |
| J16-h | J16 | `::test_revise_adding_the_facet_to_a_dataset_a_mount_run_produces_refuses` |
| J16-i | J16 | `::test_an_acquired_dataset_a_mount_run_produces_refuses` |
| J16-j | J16 | `::test_an_imported_run_producing_a_mount_observation_refuses` |
| J16-k | J16 | `::test_a_dataset_whose_retrieval_report_is_in_a_mount_refuses` |
| J16-l | J16 | `::test_an_assessment_over_a_raw_split_dataset_refuses` |
| J16-m | J16 | `::test_an_imported_assessment_over_a_dataset_a_mount_produces_refuses` |
| J17-a | J17 | `::test_a_ref_held_twice_refuses_duplicate_location_naming_both` |
| J17-b | J17 | `::test_a_held_read_mount_lock_refuses_build_contended` |
| J18-a | J18 | `test_read_side.py::test_a_dataset_the_corpus_does_not_hold_is_eligibility_unresolved` |
| J18-b | J18 | `test_read_side.py::test_one_held_invalid_and_one_unheld_dataset_is_unresolved` |
| J19-a | J19 | `test_world_audit.py::test_j19_a_supported_cross_corpus_citation_has_no_finding` |
| J19-b | J19 | `::test_j19_b_an_absent_holder_is_unresolved` |
| J19-c | J19 | `::test_j19_c_the_judgment_reads_the_capture_not_the_live_carrier` |
| J19-d | J19 | `::test_j19_d_a_damaged_holder_is_unresolved_and_the_audit_continues` |
| J19-e | J19 | `::test_j19_e_an_absent_producer_keeps_the_dataset_produced` |
| J20-a | J20 | `test_world_view.py::test_j20_the_two_installation_split_evaluates_as_one_corpus` |
| J21-a | J21 | `test_domain_facet_read.py::test_an_absent_observed_dataset_is_absent_from_gather` |

## 4. Accounting

**24 arms, 24 declaration units**, six rows; recent-cut row `(24, 24, 6)`. The cut is frozen before its code exists. The acceptance module (Task 6) declares 10 test cases.

## 5. N2 and acceptance obligations

Each `before` is copied from the tree and checked with `source.count(before) == 1`; each `after` must parse.

| arm | module | before | after | check |
|---|---|---|---|---|
| J16-a | `corpus.py` | `        self._refuse_ineligible(node, view=view)\n` | `        self._refuse_ineligible(node, view=self._view)\n` | `test_mount_citations.py::test_an_assessment_over_a_mount_dataset_and_proposition_is_written` |
| J16-b | `corpus.py` | `        self._refuse_assesses_target_kind(node, view=reading)\n` | `        self._refuse_assesses_target_kind(node, view=self._view)\n` | the same |
| J16-c | `corpus.py` | `            self._refuse_verification(node, view=self._view if view is None else view)\n` | `            self._refuse_verification(node, view=self._view)\n` | `::test_a_verification_of_a_mount_assessment_is_written` |
| J16-d | `corpus.py` | `        if root is not None:\n            self._refuse_contract_mismatch(root)\n` | `        if False:\n            self._refuse_contract_mismatch(root)\n` | `::test_a_citation_across_differing_identities_refuses` |
| J16-e | `session/__init__.py` | `            read_mounts=read_mounts,\n` | `            read_mounts=(),\n` | `test_session_writer.py::test_the_session_writer_cites_its_read_mounts` |
| J16-f | `corpus.py` | the four-line body of `MountCitations.producers` | `        holder = self.holder(dataset)\n        return () if holder is None else holder.producers(dataset, aliases=aliases)\n` | `::test_an_assessment_over_a_dataset_a_third_mount_produces_refuses` |
| J16-g | `session/__init__.py` | `    read_mounts = tuple(sorted(path for path in mounted if path != root)) if mounted is not None else ()\n` | `    read_mounts = tuple(sorted(Path(key) for key in mounts if Path(key) != root)) if mounts is not None else ()\n` | `test_session_writer.py::test_a_symlinked_write_root_mount_key_is_filtered_after_normalization` |
| J16-h | `corpus.py` | `        self._refuse_facets(restamped, provenance=True)\n` | `        self._refuse_facets(restamped, view=self._view, provenance=True)\n` | `::test_revise_adding_the_facet_to_a_dataset_a_mount_run_produces_refuses` |
| J16-i | `corpus.py` | `_SessionOverlay.producers`' `for` loop (two lines) | `        pass\n` | `::test_an_acquired_dataset_a_mount_run_produces_refuses` |
| J16-j | `corpus.py` | `_SessionOverlay.resolve`'s first body line | `        view = self._base if self._base.holds(ref) else None\n` | `::test_an_imported_run_producing_a_mount_observation_refuses` |
| J16-k | `corpus.py` | `            local = reading if isinstance(reading, _ImportView) else self._view\n` | `            local = reading\n` | `::test_a_dataset_whose_retrieval_report_is_in_a_mount_refuses` |
| J16-l | `corpus.py` | `                judge, reports = reading, citations.holder\n` | `                judge, reports = reading, None\n` | `::test_an_assessment_over_a_raw_split_dataset_refuses` |
| J16-m | `corpus.py` | `                judge, reports = citations.overlay(reading), (lambda _ref: reading)\n` | `                judge, reports = None, (lambda _ref: reading)\n` | `::test_an_imported_assessment_over_a_dataset_a_mount_produces_refuses` |
| J17-a | `corpus.py` | `        if len(found) > 1:\n` | `        if False:\n` | `::test_a_ref_held_twice_refuses_duplicate_location_naming_both` |
| J17-b | `corpus.py` | `            self._holds.enter_context(_operation_lock_for(root).capture())\n` | `            pass\n` | `::test_a_held_read_mount_lock_refuses_build_contended` |
| J18-a | `corpus.py` | `        if outcome is not None and outcome.unresolved:\n` | `        if False:\n` | `test_read_side.py::test_a_dataset_the_corpus_does_not_hold_is_eligibility_unresolved` |
| J18-b | `corpus.py` | `        tuple(unresolved),\n    )\n` | `        tuple(unresolved) if len(unresolved) == len(observed) else (),\n    )\n` | `test_read_side.py::test_one_held_invalid_and_one_unheld_dataset_is_unresolved` |
| J19-a | `audit.py` | `        second = _record_findings(captured, profile, scope, disagreeing, citations=reader)\n` | `        second = _record_findings(captured, profile, scope, disagreeing)\n` | `test_world_audit.py::test_j19_a_supported_cross_corpus_citation_has_no_finding` |
| J19-b | `audit.py` | `    causes = {corpus_id: "absent" for corpus_id in view.absent()}\n` | `    causes = {}\n` | `::test_j19_b_an_absent_holder_is_unresolved` |
| J19-c | `audit.py` | `        return self._readable.get(corpus_id)\n` | `        return self._view.corpus_view(ref)\n` | `::test_j19_c_the_judgment_reads_the_capture_not_the_live_carrier` |
| J19-d | `audit.py` | `        if cause is not None:\n            self.unreadable[ref] = f"{corpus_id} {cause}"\n            return None\n` | `        if cause is not None:\n            raise CorpusDamaged(f"eligibility:{ref}", corpus_id, self._view.stamp)\n` | `::test_j19_d_a_damaged_holder_is_unresolved_and_the_audit_continues` |
| J19-e | `audit.py` | `        found.update(self._view.published_producers(dataset))\n` | `        pass\n` | `::test_j19_e_an_absent_producer_keeps_the_dataset_produced` |
| J20-a | `evaluation.py` | `_facets_held_to_capture(profile, view, target) if world else read_observed_facets(profile, view, target)` | `read_observed_facets(profile, view.corpus_view(stored.typed_ref("run", a.run)) if world else view, target)` | `test_world_view.py::test_j20_the_two_installation_split_evaluates_as_one_corpus` |
| J21-a | `evaluation.py` | `        if outside:\n            raise InputOutsideCorpus(a.identity(), ref, tuple(sorted(set(outside))))\n` | `` | `test_domain_facet_read.py::test_an_absent_observed_dataset_is_absent_from_gather` |

- **J16-g:** the `after` filters the raw keys, so a symlinked key survives, reaches the writer, and is refused there as the writer's own root.
- **Shared checks:** J16-a and J16-b name one check. The pair is listed in `CO_CITED`, as the N2 declaration format requires for two units citing one test, in the tuple shape cut 43's module uses.
- **J16-i and J16-j:** their `before` text is spelled from the tree after Task 1, where each is unique: J16-i is `_SessionOverlay.producers`' `for` loop (two lines) and J16-j is `_SessionOverlay.resolve`'s first body line. Neither line exists at freeze.
- **J20-a:** its line may be a live pin elsewhere; the shared `before` is fine because this lane does not change it.
- **J21-a and B4b:** cut 22's B4b re-target (Task 5) uses J21-a's `before`. The two arms share the mutation and differ in their check.

Two live pins move (spec §13):

- Cut 20's F4 (`reason = validity_refusal(view, view.get(dataset_ref), profile)` in `eligibility_refusal`) moves into `eligibility_outcome` with the judge and reports arguments. It is re-targeted in `test_n2_cut20.py`'s `_LIVE_SABOTAGES` with the same mutation, reading the facet directly.
- Cut 22's B4b is re-targeted in `test_n2_cut22.py`'s `_LIVE_SABOTAGES` to J21-a's mutation. B4b's check keeps its node id, because the frozen declaration pins it; its body now asserts the J21 refusal, with a docstring naming the supersession.

B4's absent-dataset clause ("nothing refuses") is cited as superseded by J21, as cut 43 cited J9's two-root clause as superseded by J12. B4's frozen declaration is not edited, and B4b shares J21-a's mutation. B4's other clauses stand: every read is validated, and only held datasets are read. Cut 32's `_refuse` pins and the pinned `self._refuse(record, …)` call sites stay byte-exact; `_refuse` becomes a wrapper that opens the citation scope, and its body moves unchanged into `_refuse_cited`.

The runner declares `PREFIX_RUNNERS = ("cut43_acceptance.py",)` and `PHASE_MODULES = ("test_mount_citations_acceptance.py", "test_n2_cut44.py")`.

## 6. Second reader

- J17-b's check holds the mount's operation lock from a second holder (a library writer's `_state.lock`), not the session's own.
- J19-c's post-capture mutation happens after `open_world_view` returns, so the judgment must read the capture and not the live carrier.
- J16-g's symlink is a key of `mounts`, not a configured root.

## 7. Limitations

1. **Read mounts are opened per citing write.** Opening a `ReadView` indexes the whole corpus, and `corpus_state_identity` is not cheaper, so no state-keyed cache is possible today. A cost a dogfood measures would justify one, keyed by a cheap state witness that does not exist yet.
2. **Duplicates refuse, including identical ones**, until `beliefs-81367e`.
3. **A read mount mid-write blocks every citing write in the session**, including one whose citations all resolve in the write root. The refusal is immediate (`BuildContended`) and the caller retries; it never waits.
4. **No live multi-corpus belief read.**
5. **Mutation targets stay in the write root.**
6. **Retrieval reports stay with their datasets.** A split dataset and report refuses everywhere.
7. **No world-wide bearer finding.** `corpus_check`'s and `audit_world`'s `facet-bearer-produced` findings stay per corpus. A raw-written run in one corpus that produces another corpus's facet-bearing dataset is reported by `audit_world` only through the eligibility of an assessment observing that dataset. Producers are world-wide, so such an assessment is unmet. The write boundary refuses the state in both directions.
