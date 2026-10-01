# Citations into mounted corpora: the write boundary, the checks and belief

**Amends:** the session mounts design (`2026-09-27-session-mounts-design.md`, §5's
"cross-corpus targeting" paragraph and limitation 4) and the substrate consolidation
design's corpus check (§6.2 item 2) as cut 4 bound it in S7.
**Requested by:** science's coordination command set design
(`science docs/specs/2026-09-24-coordination-command-set-design.md` §5.5, part 3
amendments) and its commons design (`science docs/specs/2026-09-30-science-commons-design.md`
§5 step 4 and §11).
**Boundary:** `mount-citations`, new, in the `write-path` lane, which this design reopens.
**Tasks:** `beliefs-9ce6e4` holds this spec; it answers `beliefs-724941` (§2 decision 2).
**Cut 44:** numbered after cut 43 under roadmap concurrency rule 1. No branch or worktree
holds a later cut on 2026-10-01.
**Status:** draft, under review.

## 1. What this slice is

Cut 43 lets a session write one root and mount N read corpora. It deliberately left every
non-coordination write reading the write root alone (session mounts §5, limitation 4).
That makes the mounts useless for evidence. A record's identity is its content, so a
dataset another corpus declares cannot be declared again in the write root without a
`duplicate-location` that refuses every world read. And a record that *cites* the mount's
dataset cannot be written:

- `CorpusWriter._refuse_ineligible` reads `eligibility_refusal` through the writer's own
  view, so an assessment whose run observes a mount's dataset refuses `EligibilityUnmet`
  ("unresolved").
- `_refuse_assesses_target_kind` refuses an `assesses` edge to a mount's proposition
  (`SignatureRefused`, "assesses-target-unresolvable … in this corpus").
- `_refuse_estimand_target_mismatch` refuses an analysis spec targeting a mount's
  proposition (`ValidationRefused`, "a cross-corpus target is world-resolution's read").
- `_refuse_verification` refuses a verification of a mount's assessment
  (`VerificationTargetMismatch`, "resolves to no record here").
- `_refuse_composite` refuses a composite over a mount's propositions
  (`composite-member-unresolvable`).

The same assumption runs through the checks and the belief read:

- `corpus_check` reports an assessment whose run or observed dataset lives in another
  corpus as an `eligibility-unmet` **error**. `audit_world` runs the same per-corpus
  record findings over each captured corpus alone, so it reports the same error for a
  record the world in fact supports.
- A corpus-local `gather` (over a `ReadView`) drops a run input the corpus does not hold
  without saying so. `run_value` filters on `view.holds`, and `_absence_of` returns `None`
  for a local view. Admission then judges a run with part of its lineage missing. Science
  guards this from outside (`_refuse_foreign_observations` in its read context). The
  kernel does not.

The epoch-bound world read already resolves across corpora. `gather` over a
`WorldReadView` reads an observed dataset's facets through the holding corpus's own view
(`_facets_held_to_capture`), `lineage_snapshot` walks producers world-wide, and
`test_world_view.py`'s `split_evaluation_world` evaluates with runs held in a second
corpus. What is unproven is the split two installations produce: the assessment and its
run in one corpus, the proposition and the observed dataset in another.

Two consumers need this now. Science's second-project milestone (`sci-0d00d2`) assesses
a working-corpus proposition over mm30's data, which is the roadmap's dogfood path. Its
commons milestone 1a (`sci-13050a`) has installation B author a spec against A's mounted
proposition and datasets, assess it, and verify A's assessment, with nothing redeclared.

## 2. Decisions

1. **A citation resolves over the session's corpora, and a write still lands only in the
   write root.** A *citation* is a reference a record carries to evidence it rests on.
   A *mutation target* is the record a write changes. In a session with mounts, every
   citation the write boundary's refusal chain resolves goes through a *mount view* over
   the write root and every read mount (§3.1). Mutation targets stay where cut 43 left
   them: `supersede`'s predecessor, `retract`'s target, `delete`'s target, `revise`'s and
   `correct_identifier`'s record. So do the own-index checks `_refuse_already_minted` and
   `_refuse_collision`. A mount's record is never changed, and nothing is written to a read
   mount (J15 stands).
   *Rejected:* resolving each citing check individually, as each consumer asks. The five
   refusals in §1 are one assumption. Fixing three of them leaves the other two as the
   next consumer's finding, which is what happened between `sci-923d3a` and
   `sci-13050a`.
   *Rejected:* moving mutation targets too. Retracting or superseding another corpus's
   record is world-resolution's question (writer-session limitation 1, second sentence),
   and it needs an authority model this slice does not have.

2. **The scope is every citing check in the refusal chain, which answers
   `beliefs-724941`.** The chain is `_refuse` (add, its preflight, `retract`'s own record,
   `attest_coreference`, `supersede`'s successor) and `_preflight_replace_locked`. Their
   view-reading checks are:
   - `eligibility_refusal`: `assessment.run` → run; the run's `observes` inputs → datasets;
     `validity_refusal` on each dataset;
   - `_refuse_assesses_target_kind`: `assesses` → proposition;
   - `_refuse_estimand_target_mismatch`: the spec's `target` → proposition;
   - `_refuse_verification`: `verifies` → assessment;
   - `_refuse_composite`: `composes` → propositions;
   - `_refuse_facets`' `bearer_refusal` and `validity_refusal`: a `produces` target, the
     retrieval act-report, and `producers`;
   - `_refuse_supersedes_same_kind`: the `supersedes` target's kind (a check on the
     successor's relation; `supersede` still resolves its predecessor in the write root,
     decision 1).

   So `beliefs-9ce6e4` covers an `assesses` edge to a mount's proposition, and a
   verification whose target assessment lives in a mount. A verification's compared runs
   are not read from a view. The verify path takes them as `RunClosure` values
   (`verify.build_verification`), so the caller resolves them over its mounts, and
   science already reads every mount. `beliefs-724941` closes with this spec's approval,
   and no sibling task is filed.

3. **A cited record is read in the corpus that holds it, and decoded under that corpus's
   profile.** Session mounts §1 rules that a record is decoded under the contract it was
   typed under. So the mount view hands each check the holding corpus's `ReadView`, plus
   the profile `mounts` gives that root.
   - Where a check decodes a cited record's domain content, it uses that profile. The
     estimand-target check decodes a mount proposition's claim with
     `claim_from_stored(target, profile=<holder's>)`, so an operator only the mount's
     contract declares decodes.
   - The writer's own profile still governs the record being written.
   - Eligibility reads only base-profile content: the `empirical-observation` facet's
     payload schema and an act-report's `operation`. Every corpus a session mounts or an
     epoch reads pins the shipped base (session mounts limitation 1; a corpus pinning
     another base is excluded as `base-pin` damage). So every profile gives eligibility
     the same answer. For that reason `audit_world` keeps its one `profile` argument and
     needs no per-corpus profile map (decision 8).

3a. **Producers are the session's, not the holder's.** `validity_refusal` and
   `bearer_refusal` ask `producers(dataset)`, and `ReadView.producers` deliberately
   counts dangling `produces` edges: a run written before its dataset is still a producer.
   The dataset being written is a candidate that nothing holds yet, so the lookup cannot
   go through a holder. The mount view therefore answers `producers(ref)` as the union,
   over the write root and every read mount, of each corpus's own `producers(ref,
   aliases=…)`, held or dangling, whether or not anything holds `ref`. A candidate
   dataset declared with the `empirical-observation` facet still refuses when a
   write-root run names it, as today. It also refuses when a read mount's run names it,
   because the resulting state the invariant is about is the session's.
   *Rejected:* answering from the holder alone. A candidate has no holder, so the
   dangling-edge rule would vanish in every session with mounts.

4. **One citation, one holder; conflicts refuse and never pick.** If more than one session
   corpus resolves a citation, the write root included, the write refuses
   `AddressMapConflict` with a `duplicate-location` finding. The finding names the address
   and every holding corpus, as `derive.address_map` classifies it. Nothing is chosen by
   corpus order (science commons §4.7, outcome 2). `beliefs-81367e` will decide when
   identical content held twice reads once. When it lands it amends this rule and the
   world map's rule together.
   *Rejected:* write-root precedence. It judges the write against one copy while every
   world read of the same session refuses the address, and that is resolution by corpus
   order.

5. **A read mount is read inside its own capture hold, and the hold never queues.**
   The refusal chain runs under the writer's operation lock. A read mount is read only
   inside that mount's `capture()` hold, which never waits and refuses `BuildContended`
   when the mount's operation lock is held. So a writer holding its own lock can never
   wait on another session that waits on it. The mount view enters each read mount's hold
   lazily, at the first citation that needs it in one refusal chain. It opens that mount's
   `ReadView` inside the hold, and releases the hold when the chain ends. A read mount mid-write therefore refuses the
   citing write with `BuildContended`, before any effect. The caller retries. A chain
   that cites nothing outside the write root still opens every read mount, because
   decision 4 must know whether any other corpus holds the address. A write with no
   citations at all opens none.
   *Rejected:* reading read mounts with no hold. A view opened while another session
   writes the mount can index a half-applied operation, and the write boundary would
   judge against it.
   *Rejected:* capturing each mount before taking the writer's lock. Which records are
   cited depends on records in the write root (an assessment's run, that run's inputs),
   and those must be read under the writer's lock.

6. **Outside a session with read mounts, nothing changes.** A library `CorpusWriter`, a
   session with `mounts=None`, and a session whose only mount is its write root resolve
   citations through the writer's own view exactly as today. The mount view is something
   the session supplies to its writer, not a default the writer infers.

7. **The single-corpus check cannot judge a citation it cannot see, so it says so.**
   `corpus_check` reads one corpus. When an assessment's eligibility fails only because
   the run, or every observed dataset that is not locally invalid, is a citation the
   corpus does not hold, the check reports `eligibility-unresolved`, severity `warning`,
   naming the unresolved references. Failures it can decide locally stay
   `eligibility-unmet` errors under the existing line and message: a held run with no
   `observes` input, `reads`-only inputs, and observed datasets all held and all invalid.
   *Rejected:* keeping the error. Every session corpus holding a legitimate cross-mount
   assessment would fail its own check, and a reader would learn to ignore the code.

8. **The world audit judges eligibility over the captured world, and never raises
   doing it.** `audit_world` builds its findings from the records its view captured
   (`captured_records`), and its eligibility judgment stays on them. It never reads
   through `corpus_view`, which is the holding corpus's *live* `ReadView`: that would see
   producers and act-reports changed after the capture holds were released, while every
   other finding describes the capture. The audit judges eligibility with a *captured
   citation reader*, built once per audit:
   - **Lookup.** A reference resolves first in the citing record's own captured corpus,
     mapped and drift records alike, exactly as `_CapturedCheckView` resolves it today.
     So no single-corpus result changes. Otherwise it resolves through the epoch's
     address map (`corpus_of`) to another covered corpus, and is read from that corpus's
     captured records. A mapped address cannot be held twice at a published epoch,
     because publication refuses W8b. A drift record in the citing corpus that duplicates
     another corpus's mapped address is judged locally, as today. The next epoch build
     refuses that duplicate.
   - **Producers.** These are the union over every present, non-excluded covered corpus's
     captured records, by decision 3a's rule.
   - **Outcomes.** The reader is total: each lookup answers one of the following, never an
     exception.
     - `held`: a record from a readable captured corpus.
     - `unmapped`: no covered corpus maps the reference.
     - `absent`: it is mapped to a covered corpus with no carrier.
     - `unreadable`: it is mapped to a corpus the audit reports damaged (any cause) or
       excludes (`base` or `malformed` manifest scope), or the held record is in its
       corpus's malformedness set (`MALFORMEDNESS_CODES`).

     These four classes apply only to a reference resolved in *another* corpus. A
     reference the citing corpus holds is judged exactly as `_CapturedCheckView` judges
     it today, malformed neighbours included.

   The eligibility arm turns these into findings on the citing assessment:
   - supported → no finding;
   - only `unmapped` references and locally decided failures → `eligibility-unmet`
     (error);
   - any `absent` or `unreadable` reference on which the outcome depends →
     `eligibility-unresolved` (warning). Its `detail` names each such reference with its
     corpus and cause (`absent`, `damaged:<cause>`, `excluded:<scope>`,
     `malformed:<code>`).

   The audit carries on to the next record in every case. This is the precedent
   `derivation-unreachable` sets for a recomputation that reaches a damaged corpus, and
   `audit.py`'s rule that a malformed neighbour leaves its reader unchecked, the
   neighbour being classified under its own ref. A damaged corpus's readable remainder
   is still audited exactly as today, its own-corpus citations included. Only a citation
   *into* a damaged or excluded corpus becomes `eligibility-unresolved`. Every other code
   in the per-corpus findings stays as `corpus_check` reports it.

9. **A corpus-local belief read refuses evidence it cannot see.** When `gather` over a
   `ReadView` reads an assessment whose run names an input the corpus does not hold, it
   raises `InputOutsideCorpus`, naming the assessment, the run and the inputs, instead
   of dropping them. `evaluate_over` and `evaluate_over_traced` return
   `Refused("input-outside-corpus: …")`, beside their other refusals. A world read is
   unchanged: the input resolves in its holding corpus, or the read records it absent.
   *Rejected:* leaving the drop to science's guard. Every caller of a corpus-local read
   would need its own copy, and this slice makes cross-corpus assessments legitimate, so
   corpus-local reads will meet them routinely.

10. **Belief across corpora stays epoch-bound.** The kernel already reads beliefs over a
    `WorldReadView`, and the live-query design kept belief reads epoch-bound (coordination
    §6.2, amended). This slice adds no live multi-corpus belief read. A caller that wants
    belief over a write root and its mounts reads it over a world view at an epoch
    covering them. This slice proves that read on the two-installation split (J20) and
    changes no code in it unless the proof fails.
    *Rejected:* a third, live multi-corpus mode for `gather`. That is a second world read
    with no epoch identity in its reproducibility context. It reopens the decision cut 41
    closed, and no consumer needs it that an epoch cannot serve.

11. **A conformance cut.** S7's frozen evidence stands: its raw-written case is a held run
    with no `observes` input, which stays an error (decision 7). This slice still changes
    what the write boundary admits and what two checks report, and it re-points live
    sabotage pins in `corpus.py`. Cut 43's decision 10 applies, so the change is held by
    cut 44 with its own N2 arms.

## 3. Surface

### 3.1 The mount view: `MountCitations` (`beliefs/corpus.py`)

```python
class MountCitations:
    """Citation reads over a session's write root and read mounts (decisions 1–5)."""

    def __init__(self, own: ReadView, own_profile: ProfileSpec,
                 read_mounts: Mapping[Path, ProfileSpec]) -> None: ...
    def holder(self, ref: str) -> tuple[ReadView, ProfileSpec] | None: ...
    # the read protocol the refusal chain uses, answered from the one holder:
    def resolve(self, ref: str) -> str | None: ...
    def holds(self, ref: str) -> bool: ...
    def get(self, ref: str) -> Node: ...
    def producers(self, dataset: str, *, aliases: tuple[str, ...] = ()) -> tuple[str, ...]: ...
    # the union over every session corpus, dangling edges included (decision 3a)
    def iter_stored(self) -> Iterator[Node]: ...  # every session corpus's records
```

- `holder(ref)` asks the write root's view and every read mount's view.
  - One holder: its `(view, profile)` is returned.
  - None: the result is `None`.
  - More than one: it raises `AddressMapConflict(Finding("error", "duplicate-location",
    ref, <sorted corpus ids>, …))` (decision 4).
- `resolve`, `holds` and `get` answer from `holder(ref)`. `get` raises `RefError` for a
  ref nothing holds, as `ReadView.get` does.
- `producers` does not consult `holder`. It is the sorted union of each session corpus's
  own `producers(dataset, aliases=aliases)`, and it answers for a ref nothing holds
  (decision 3a). `iter_stored` exists only for `_producer_ids`' protocol and yields every
  session corpus's records.
- A read mount's view is opened at its first use in one refusal chain, inside that mount's
  `capture()` hold (decision 5). All read-mount holds are released when the chain ends,
  on every exit path. A `BuildContended` from any hold propagates.
- It writes nothing, and it imports nothing from `atoms`. The capture hold comes through
  the existing `_operation_lock_for`, which `world/live.py` already uses.

The checks of decision 2 take the view as today (`view: ReadView | _ImportView | None`).
Where a check judges a cited record's content, it asks the view for the holder and uses the
holder's view and profile (decision 3). `eligibility_refusal` judges each observed dataset
with `validity_refusal(holder_view, dataset, holder_profile)`. With a plain `ReadView` the
holder is that view and the writer's profile, so behaviour is unchanged (decision 6).

### 3.2 The writer and the session

- `CorpusWriter.__init__` gains `read_mounts: Mapping[Path, ProfileSpec] | None = None`.
  The parameter is a `Mapping` with `Path` keys and `ProfileSpec` values, or `None`;
  anything else raises `TypeError`. The writer resolves each key. A key that resolves
  to the writer's own root raises `ValueError`, and so do two keys that resolve to one
  path. The writer stores the resolved mapping.
  - With `read_mounts`, `_refuse` and `_preflight_replace_locked` use
    `MountCitations(self._view, self._profile, read_mounts)` wherever they used
    `self._view` for the checks of decision 2.
  - Mutation-target reads and the own-index checks keep `self._view` and
    `self._corpus.index` (decision 1).
  - `import_bundle`'s and `_refuse_acquired_dataset`'s `_ImportView` overlays keep their
    own base: an import bundle is self-contained by its contract.
- `open_attended_session`'s `writer_factory` builds `read_mounts` from the session's
  **normalized** mount mapping (`mounted`), the one check 4 of session mounts §3.2
  already built with resolved keys and `_mount_resolver` receives. It omits `root`, the
  write root already resolved at check 3:
  `{path: spec for path, spec in mounted.items() if path != root}`. It passes `None` when no read mount remains. Filtering the raw
  `mounts` keys would let a symlinked or relative spelling of the write root through.
  The writer would then refuse its own root, or a read-mount capture hold would contend
  with the writer's own lock. No argument of `open_attended_session` changes.

### 3.3 The checks

- `_record_findings`' eligibility arm (corpus.py, the `eligibility_refusal(check, …)` call)
  distinguishes the decision 7 outcome. It emits `eligibility-unresolved` (warning,
  `detail` the unresolved references, sorted). The `eligibility-unmet` finding line stays
  byte-exact for the locally decided outcomes.
- `eligibility_refusal` returns a structured outcome the arm can classify, not only a
  string: `None`, `unmet(reason)` or `unresolved(refs, reason)`. The write boundary
  raises `EligibilityUnmet` on both non-`None` outcomes, with the message it raises
  today.
- `audit_world` passes the eligibility arm decision 8's captured citation reader. The
  reader is built once per audit from `captured_records`, `corpus_of`, `absent()`,
  `damaged()`, the audit's `excluded` set and its per-corpus `malformed` sets. It never
  calls `corpus_view`, `locate` or `get` on the world view. Two consequences follow.
  - The arm runs after every corpus's malformedness set is known. The audit's
    `_record_findings` pass is therefore split in two: per-corpus findings without the
    eligibility arm first, then the eligibility arm over every non-excluded corpus.
    Finding order is unchanged, because findings are sorted by `sort_key`.
  - Eligibility is judged with the audit's one `profile` (decision 3).

  `corpus_check` passes the single-corpus reader, so its findings are those of
  decision 7.

### 3.4 Belief

- `gather` over a `ReadView`: after `run_value`, any input role target the view does not
  hold raises `InputOutsideCorpus(assessment, run, inputs)`. It is a new
  `MalformedRecord` subclass in `errors.py`, and its message names all three
  (decision 9).
- `_evaluate_over_inputs` maps it to `Refused(f"input-outside-corpus: {exc}")`.
- `gather` over a `WorldReadView` is unchanged (decision 10).

## 4. What science gains and must change

The changes below are science's. They are listed so the science task this slice files can
cite them (§10).

- **Write commands may name a read mount's records.** `spec`, `run`, `assess` and
  `verify` may name a mount's dataset, proposition and assessment, which the coordination
  command set's part 3 amendment refuses today. `dataset` still refuses bytes a mount
  declares. `fetch` (commons §5 step 4) records holdings in the store without declaring
  anything.
- **Its foreign-observation guard becomes the kernel's.** `_refuse_foreign_observations`
  can go: a corpus-local read now refuses `input-outside-corpus` itself.
- **Belief over a write root and its mounts is a world read at an epoch** (decision 10).
  The commons design's "belief evaluating over a world read" (§11) names this path.
- **`status` meets `eligibility-unresolved`** as a warning on a session corpus that holds
  cross-mount assessments. That is expected, and `audit_world` is the read that judges it.

## 5. What does not change

- What a session may write, and where: J12–J15. No act family, permit or write entry
  point changes, so `WRITE_ENTRY_POINTS` and `test_permit_entry_points.py`'s `CASES` are
  unchanged.
- Mutation targets and own-index checks (decision 1).
- The world read, epoch publication and `derive.address_map`.
- `CoordinationResolver`. Coordination citations were already world-wide over the mounts
  (cut 43, J14).
- Every finding `corpus_check` reports over a corpus with no cross-corpus citation.

## 6. Shared files, under roadmap concurrency rule 3

This lane edits `corpus.py` (the refusal chain, `eligibility_refusal`, `_record_findings`'
eligibility arm, `MountCitations`), `evaluation.py` (`gather`, `_evaluate_over_inputs`),
`audit.py` (`audit_world`'s eligibility arm), `session/__init__.py` (`writer_factory`) and
`errors.py` (`InputOutsideCorpus`). No other kernel lane is open on 2026-10-01. The
documents every lane rewrites are the adoption ledger, the roadmap, the guide index and
`test_designs_corpus.py`.

## 7. Guarantee rows

New rows J16–J21 in the `J` table.

| row | guarantee | mutation test |
|---|---|---|
| **J16** | In a session with read mounts, the write boundary resolves the citations of decision 2 over the write root and every read mount, reads each cited record in its holding corpus, decodes its domain content under that corpus's profile, and judges producers over the whole session. The write lands in the write root alone | Corpus M (read mount) pins a test-local contract declaring a claim operator W's profile lacks. M holds a dataset with a valid empirical-observation facet, a proposition, a proposition whose claim uses that operator, and an assessment with its run. In a session writing W: a run observing M's dataset, then an assessment of M's proposition over that run → written to W. An analysis spec targeting M's proposition → written. An analysis spec targeting M's operator proposition, its estimand naming that claim → written. A run in W whose `produces` edge names an address nothing holds, then a dataset at that address declared with the empirical-observation facet → `AcquisitionBoundaryRefused` ("is produced by" the W run), as on a one-root writer. The same with the dangling `produces` edge in M's run instead → refused. A verification of M's assessment → written. A composite over M's propositions → written. M's tree hash is unchanged (J15). A session whose `mounts` names the write root by a symlinked path → opens, and J16's writes behave the same. **Negative:** the same writes through a library `CorpusWriter` on W, and through a session with `mounts=None`, refuse as §1 lists, with today's messages |
| **J17** | A citation two session corpora resolve refuses `AddressMapConflict` (`duplicate-location`, naming both), and a read mount whose operation lock is held refuses `BuildContended`. Both happen before any effect, with nothing written | M1 and M2 both hold a dataset at one address (a raw write into M2). An assessment over a run observing it → `AddressMapConflict` naming M1 and M2, and W unchanged. The same with the address held by W and M1 → refuses naming both. With M's operation lock held by another holder, an assessment citing M → `BuildContended`, and W unchanged. **Negative:** a write citing only W's records while M's lock is held → `BuildContended` (decision 5: the chain opens every read mount), and a write citing nothing (a proposition) → written |
| **J18** | `corpus_check` reports an assessment whose eligibility rests on references the corpus does not hold as `eligibility-unresolved` (warning). Locally decided failures stay `eligibility-unmet` (error) | W after J16's session: `corpus_check(W)` → one `eligibility-unresolved` warning per cross-mount assessment, naming the references, and no error. A raw-written assessment over a held run with no `observes` input → `eligibility-unmet` error (S7's case, unchanged). A run observing one held invalid dataset and one unheld dataset → `eligibility-unresolved`. **Negative:** a run observing only held invalid datasets → `eligibility-unmet` |
| **J19** | `audit_world` judges eligibility across covered corpora from the captured records, never raising: supported → no finding, unmapped → `eligibility-unmet`, held by an absent, damaged or excluded corpus, or by a malformed record → `eligibility-unresolved` naming the corpus and cause, and the audit continues | Publish an epoch over W and M after J16's session: `audit_world` → no eligibility finding. **Captured, not live:** the test wraps `open_world_view` so that, after the view captures and before the audit reads it, M's carrier loses the dataset's retrieval act-report (a raw delete) → still no eligibility finding. Remove M's carrier → `eligibility-unresolved` naming M, `absent`. Make one of M's files fail construction → `eligibility-unresolved` naming M, `damaged:construction`, with W's other records still audited and M's readable remainder audited as today. Make M's dataset's semantic stamp stale (a raw write before the epoch) → `eligibility-unresolved`, `malformed:semantic-hash-stale`, beside M's own `semantic-hash-stale` finding. Rebuild with W's run observing an M dataset that carries no empirical-observation facet (a well-formed record, so not in M's malformedness set) → `eligibility-unmet`. A malformed-payload dataset is the `unreadable` case, not this one: `facet-payload-malformed` is a malformedness code. **Negative:** an epoch covering W alone (M not admitted) → `eligibility-unmet`, since no covered corpus maps the dataset |
| **J20** | Belief over a world read gathers, admits and evaluates the two-installation split: assessment and run in W, proposition and observed dataset in M | Over the J19 epoch: `evaluate_over(world_view, M's proposition, …)` → the same answer, admission and `node_corpus` attribution (assessment and run → W, the others → M) as the same records evaluated from one corpus, and a lineage snapshot that reaches M's dataset. **Negative:** with M's carrier absent → `NoBelief("unavailable-corpus-absent")` naming M |
| **J21** | A corpus-local belief read refuses an assessment whose run names an input the corpus does not hold | W holds a proposition P, assessed in the session over a run observing M's dataset. `gather(ReadView(W), P)` → `InputOutsideCorpus` naming the assessment, run and dataset, and `evaluate_over` → `Refused("input-outside-corpus: …")`. **Negative:** the same proposition over a world view → evaluates (J20) |

## 8. Testing and the cut

### 8.1 Unit — portable

- `tests/test_mount_citations.py` (new): `MountCitations` over roots in a temporary
  directory. It covers holder lookup, conflicts, lazy opening, the hold released on every
  exit path, and `BuildContended` from a held lock.
- The J16 write table, parametrized over each citing kind.
- The decision 6 negatives through a library writer.
- `tests/test_read_side.py` gains J18's cases.
- `tests/test_evaluation*.py` gains J21's.

### 8.2 Acceptance — `test_mount_citations_acceptance.py` (new)

J16–J21 in full on the certified volume, beside the checkout. W pins base, `biology` and
coordination v2. M pins base, `biology` and a test-local contract, so decision 3 has a
profile that differs from the writer's.

`test_world_view.py`'s portable world tests do not reach `tests/acceptance`. J19 and J20
run there, against a published epoch.

### 8.3 N2 sabotages — `n2_arms_cut44.py`

| arm | sabotage | check that fails |
|---|---|---|
| J16a | `_refuse_ineligible` reads `self._view` whatever `read_mounts` says | J16's assessment over M's dataset refuses |
| J16b | `_refuse_assesses_target_kind` reads `self._view` | J16's assessment of M's proposition refuses |
| J16c | `_refuse_verification` reads `self._view` | J16's verification of M's assessment refuses |
| J16d | `_refuse_estimand_target_mismatch` decodes a cited target under `self._profile`, not its holder's | J16's spec targeting M's operator proposition refuses |
| J16e | `writer_factory` passes `read_mounts=None` | J16's writes refuse |
| J16f | `MountCitations.producers` answers from `holder(ref)` | J16's candidate dataset named by a dangling W-run edge is written |
| J16g | `writer_factory` filters the raw `mounts` keys | J16's symlinked-write-root session refuses or contends instead of writing |
| J17a | `holder` returns the first holder in corpus order | J17's two-mount case writes |
| J17b | read-mount views open without the capture hold | J17's held-lock case writes |
| J18a | the `eligibility-unresolved` arm emits `eligibility-unmet` | J18's session corpus reports an error |
| J18b | the arm reports `eligibility-unresolved` only when no observed dataset is held | J18's mixed case (one held invalid, one unheld) reports `eligibility-unmet` |
| J19a | `audit_world`'s eligibility arm reads the captured corpus alone | J19's supported case reports `eligibility-unmet` |
| J19b | an absent holder is treated as unmapped | J19's absent-carrier case reports `eligibility-unmet` |
| J19c | the captured citation reader reads a cross-corpus holder through `corpus_view` | J19's post-capture case reports `eligibility-unmet` (`facet-retrieval-unresolved`) |
| J19d | the reader lets `CorpusDamaged` propagate | J19's damaged-holder case raises instead of returning an audit |
| J20a | `gather` reads an observed dataset's facets through the assessment's corpus view | J20 refuses or diverges from the one-corpus answer |
| J21a | the `InputOutsideCorpus` check removed | J21's local read evaluates |

**Staleness.** The plan runs `test_arm_staleness.py`'s
`test_every_arm_a_live_guard_audits_applies_exactly_once` over the changed tree. Every
stale arm it reports is re-targeted in the `_LIVE_SABOTAGES` table of the live guard that
audits it, never in a frozen declaration module, and zero stale is the exit condition.
This spec keeps cut 4's S7 pin (`code="eligibility-unmet",`) byte-exact (§3.3). A stale
arm the plan did not foresee is a finding against this spec, not a routine re-target.

### 8.4 The cut

Cut 44 selects J16–J21 in full and names the highest-numbered acceptance runner (rule 5).
The plan's Global Constraints carry the two repository obligations verbatim:

- `root.py` stays the one `atoms` importer. `MountCitations` reaches the capture hold
  through the existing `_operation_lock_for`. This slice adds no write primitive, so
  `WRITE_ENTRY_POINTS` does not change.
- Cut 44 adds its row to `test_recent_cut_acceptance.py`.

## 9. Documentation amendments

- **Session mounts design:** a dated amendment.
  - §5's cross-corpus targeting paragraph narrows to mutation targets.
  - Limitation 4 is restated as "mutation targets stay in the write root".
- **Adoption ledger:** `Current state` gains `mount-citations` and closes it at cut 44's
  results record. The `write-path` lane row reopens with this boundary.
- **Roadmap:** `mount-citations` goes in tier 1 **on the path**, as the second-project
  milestone's remaining kernel prerequisite. This corrects "No open kernel boundary"
  under *On the path*, which has been stale since `beliefs-9ce6e4` was filed on 2026-09-30.
- **Guide:** `writes-operations-and-publication.md` states the citation/mutation-target
  split.

## 10. Limitations

1. **Read mounts are opened per citing write.** Opening a `ReadView` indexes the whole
   corpus, and `corpus_state_identity` is not cheaper, so no state-keyed cache is
   possible today. A cost a dogfood measures would justify one, keyed by a cheap state
   witness that does not exist yet.
2. **Duplicates refuse, including identical ones** (decision 4), until `beliefs-81367e`.
3. **A read mount mid-write blocks every citing write in the session** (decision 5),
   including one whose citations all resolve in the write root. The refusal is immediate
   (`BuildContended`) and the caller retries; it never waits.
4. **No live multi-corpus belief read** (decision 10).
5. **Mutation targets stay in the write root** (decision 1).

## 11. Task linkage

`beliefs-9ce6e4` holds this spec (`--spec mount-citations`); the plan's steps become its
children. On approval, `beliefs-724941` closes citing decision 2, and a science task is
filed against §4, depending on `beliefs-9ce6e4`. Science's `sci-0d00d2` and `sci-13050a`
consume it.

## 12. Review log

**Round 1 (2026-10-01), revise: P1 3, P2 2.** All five were accepted after checking the
code.
1. A candidate dataset has no holder, so producers delegated through `holder()` would
   drop `ReadView.producers`' dangling-edge rule. Added decision 3a: producers are the
   union over the session's corpora. J16 gains the candidate cases and J16f.
2. `WorldReadView.corpus_view` is live. Decision 8 now reads captured records only,
   and J19 gains the post-capture mutation regression and J19c.
3. Damaged holders were undefined. Decision 8's reader is total, with an `unreadable`
   class (damaged, excluded or malformed). The audit continues as
   `derivation-unreachable` does, and J19 gains those cases and J19d.
4. Holder profiles in `audit_world`. Decision 3 now rests on what eligibility reads:
   only base-profile content, identical under every shipped-base profile, so
   `audit_world` keeps one profile. The holder's profile is kept where a check decodes
   domain content: the estimand target's claim. That also resolves J16d's witness (a
   mount-only operator).
5. Raw `mounts` keys. `writer_factory` now filters the session's normalized `mounted`
   mapping. The writer refuses an aliased own root. J16 gains the symlinked-write-root
   case and J16g.
