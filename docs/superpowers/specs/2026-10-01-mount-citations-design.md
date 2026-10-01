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
**Status:** implemented and discharged as cut 44 on 2026-10-01; [results](../../plans/2026-10-01-conformance-cut-44-results.md). Main integration remains Task 10.

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
   - `_refuse_facets`' `bearer_refusal` and `validity_refusal`: a `produces` target and
     `producers`, over the session. The retrieval act-report is read only in the
     dataset's own corpus (decision 3a);
   - `_refuse_supersedes_same_kind`: the `supersedes` target's kind (a check on the
     successor's relation; `supersede` still resolves its predecessor in the write root,
     decision 1).

   So `beliefs-9ce6e4` covers an `assesses` edge to a mount's proposition, and a
   verification whose target assessment lives in a mount. A verification's compared runs
   are not read from a view. The verify path takes them as `RunClosure` values
   (`verify.build_verification`), so the caller resolves them over its mounts, and
   science already reads every mount. `beliefs-724941` closes with this spec's approval,
   and no sibling task is filed.

3. **A cited record is read where it is held and decoded under the writer's profile.
   A citation across differing contract identities refuses.** The mount view hands each
   check the holding corpus's `ReadView`, but the check decodes with the writer's
   profile. The record being written is typed under that profile, and it names what it
   cites in that profile's terms. Spec restoration (`_refuse_r20_contradiction`) types
   the writer's estimand under the writer's profile before the target is ever read. A
   claim operator only the mount's contract declares therefore refuses at restoration,
   whichever profile the target would be decoded under; round 2 reproduced this.
   Decoding under the holder's profile therefore cannot admit a write the writer's
   profile refuses. It differs only when the two profiles give one namespace *different*
   identities, and then decoding under either would equate two contracts silently. So
   when a citation's holder is a read mount whose manifest pins, for a namespace the
   writer's profile also pins, a different identity, the write refuses
   `CitationContractMismatch`, a new `ContractMismatch` subclass. It names the read mount,
   the namespace and both pins. Contract succession is its own design (session mounts
   limitation 1's kin).
   - Namespaces only one side pins do not refuse. A mount's corpus-local contract (mm30's
     `mm30`) is the expected case. A citation whose content needs it fails the writer's
     own decode, as it does today.
   - Eligibility reads only base-profile content: the `empirical-observation` facet's
     payload schema and an act-report's `operation`. Every corpus a session mounts or an
     epoch reads pins the shipped base (session mounts limitation 1; a corpus pinning
     another base is excluded as `base-pin` damage). The base pin never differs, and every
     profile gives eligibility the same answer. So `audit_world` keeps its one `profile`
     argument and needs no per-corpus profile map (decision 8).
   This is a **policy choice**, not a derived necessity. Round 2 disproved one witness
   for holder-profile decoding: the mount-only operator, which restoration refuses first.
   It did not show that the two decodings can never differ. Where they could, the
   contracts' identities differ, and the kernel has no rule saying which decoding is
   right. It refuses instead of choosing.
   *Rejected (round 1 draft):* decoding under the holder's profile. It picks the
   holder's reading where the kernel has no basis to prefer it, and the one witness
   found was unobservable.

3a. **The acquisition-boundary invariants are judged over the session, in both
   directions; a retrieval report is local to its dataset.** `bearer_refusal` and
   `validity_refusal` are the resulting-state invariants on the `produces` edge. The
   resulting state is the session's. So with read mounts every judgment of them reads
   the session, on every path that makes one:
   - add and its preflight, replace, `revise` (`_revise_dataset_locked`),
     `correct_identifier`, both `_ImportView` overlays (acquisition's arriving report,
     and `import_bundle`), and the eligibility judgment of an observed dataset.

   Two lookups make up the judgment, and both read the session:
   - **Producers of a dataset.** This is the union, over the write root (or the overlay,
     on an import path) and every read mount, of each corpus's own `producers(ref,
     aliases=…)`, held or dangling, whether or not anything holds `ref`.
     `ReadView.producers` deliberately counts dangling edges: a run written before its
     dataset is still a producer.
   - **A `produces` target of a run.** `bearer_refusal` resolves and reads each target
     to see whether it carries the `empirical-observation` facet. The target is resolved
     over the session: the overlay or the write root, then every read mount. Two holders
     refuse as decision 4 says.

   Both directions are therefore covered:
   - A dataset carrying the facet refuses when any session corpus's run names it, whether
     it is minted by add or acquisition, gains the facet by revise, or arrives in an
     import.
   - A run, written or imported, refuses when it produces a facet-bearing dataset any
     session corpus holds.

   **The retrieval report stays with its dataset.** `validity_refusal` resolves an
   `empirical-observation` payload's `retrieval` act-report in the corpus holding the
   dataset, or the overlay for a candidate, and nowhere else. The kernel's only path
   that writes a retrieval report is acquisition. It mints the report and its dataset
   together in one corpus, so no kernel write produces a dataset whose report lives
   elsewhere. This is an explicit restriction. A dataset in W naming a report held only
   in M refuses `facet-retrieval-unresolved` at the write boundary, exactly as
   `corpus_check(W)` reports it, and `audit_world`'s per-corpus finding agrees. So the
   write, the single-corpus check and the world audit give one answer, and none of them
   reports a false error.
   *Rejected:* answering producers from the holder alone. A candidate has no holder, so
   the dangling-edge rule would vanish. A held dataset would also be judged without
   producers held elsewhere.
   *Rejected:* session-wide retrieval resolution. Nothing writes the split, and
   supporting it would need a local-unresolved and world-resolved reporting rule in two
   checks, for a state only a raw write creates.

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
     Otherwise it resolves through the epoch's
     address map (`corpus_of`) to another covered corpus, and is read from that corpus's
     captured records. A mapped address cannot be held twice at a published epoch,
     because publication refuses W8b. A drift record in the citing corpus that duplicates
     another corpus's mapped address is judged locally, as today. The next epoch build
     refuses that duplicate.
   - **Retrieval reports** are read from the dataset's own captured corpus only
     (decision 3a).
   - **Producers.** These are the union of two sets, by decision 3a's rule:
     - every present, non-excluded covered corpus's captured records (drift producers
       included);
     - the epoch's own record of the dataset's producers (`published_producers`), which
       the epoch derived from every covered corpus at publication.

     The second set is what keeps a producer held in an absent, damaged or excluded
     corpus from vanishing. Removing a producer's carrier never restores eligibility. A
     dataset the epoch does not map (a drift record) has no published producers. If any
     covered corpus is then absent, damaged or excluded, its producer set is incomplete,
     and a judgment that would otherwise pass is `eligibility-unresolved`, with cause
     `producers-incomplete:<corpus ids>`.
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
                 read_mounts: Collection[Path]) -> None: ...
    def holder(self, ref: str) -> ReadView | None: ...
    # the read protocol the refusal chain uses, answered from the one holder:
    def resolve(self, ref: str) -> str | None: ...
    def holds(self, ref: str) -> bool: ...
    def get(self, ref: str) -> Node: ...
    def producers(self, dataset: str, *, aliases: tuple[str, ...] = ()) -> tuple[str, ...]: ...
    # the union over every session corpus, dangling edges included (decision 3a)
    def iter_stored(self) -> Iterator[Node]: ...  # every session corpus's records
```

- `holder(ref)` asks the write root's view and every read mount's view.
  - One holder: its view is returned. If that holder is a read mount whose manifest pins
    a different identity for a namespace `own_profile` pins, `CitationContractMismatch`
    is raised instead (decision 3). The manifest is loaded when the mount's view opens.
  - None: the result is `None`.
  - More than one: it raises `AddressMapConflict(Finding("error", "duplicate-location",
    ref, <sorted corpus ids>, …))` (decision 4).
- `resolve`, `holds` and `get` answer from `holder(ref)`. `get` raises `RefError` for a
  ref nothing holds, as `ReadView.get` does.
- `producers` does not consult `holder`. It is the sorted union of each session corpus's
  own `producers(dataset, aliases=aliases)`, and it answers for a ref nothing holds
  (decision 3a). `iter_stored` exists only for `_producer_ids`' protocol and yields every
  session corpus's records.
- `acquisition_view(base, *, local) -> ProducerView` builds the view the writer
  hands `bearer_refusal` and `validity_refusal` (decision 3a). `base` is the path's
  resolution view: the citation view, or an `_ImportView` overlay. `local` is the path's
  corpus-local view: `self._view` on the add, replace, revise and correct-identifier
  paths, and the `_ImportView` overlay itself on an import path. It is never the
  citation view.
  - `resolve` and `get` of a ref the base does not hold fall through to the read mounts,
    with decision 4's duplicate refusal. This is the `produces`-target lookup.
  - `producers` is the union of the base's and every read mount's.
  - The retrieval report is read from the dataset's own corpus only.
    `validity_refusal(view, node, profile, *, reports: ReportView | None = None)` gains
    `reports`, a `holds`/`get` pair. It resolves `retrieval` through `reports`, which
    defaults to `view`, so every caller outside this slice is unchanged.
    - On every `_refuse_facets` path, the dataset judged is the write root's record or
      an arriving one, so the writer passes `reports=local`.
    - In eligibility, the observed dataset is held somewhere in the session, so the
      writer passes `reports=citations.holder(dataset)`, the holding corpus's own view.
    - `bearer_refusal` is unchanged.
- A read mount's view is opened at its first use in one refusal chain, inside that mount's
  `capture()` hold (decision 5). All read-mount holds are released when the chain ends,
  on every exit path. A `BuildContended` from any hold propagates.
- It writes nothing, and it imports nothing from `atoms`. The capture hold comes through
  the existing `_operation_lock_for`, which `world/live.py` already uses.

The checks of decision 2 take the view as today (`view: ReadView | _ImportView | None`)
and decode with the writer's profile (decision 3). `eligibility_refusal` judges each
observed dataset with the session's producers on every path (decision 3a). How the run
and the datasets are *found*, and where the report is read, depends on the path's view:
- **Citation view** (add, its preflight, replace): the run and each dataset are found
  over the mount view. Each dataset is judged with `validity_refusal(view, dataset,
  profile, reports=view.holder(dataset))`.
- **An `_ImportView` overlay** (`import_bundle`, the acquired dataset): the run and each
  dataset are found through the overlay, keeping import resolution local (decision 1).
  Each dataset is judged with `validity_refusal(citations.acquisition_view(overlay,
  local=overlay), dataset, profile, reports=overlay)`. So an imported assessment whose
  local run observes a local facet-bearing dataset is refused when any read mount holds
  that dataset's producer.

`_refuse_ineligible` takes `view` as today. It picks the arm by whether `view` is an
`_ImportView`, and the eligibility predicate takes the validity view and the report view
as separate arguments from the resolution view. With a plain `ReadView` (no read mounts)
every answer is that view's, so behaviour is unchanged (decision 6).

### 3.2 The writer and the session

- `CorpusWriter.__init__` gains `read_mounts: Collection[Path] | None = None`. Each
  element must be a `Path`, otherwise `TypeError`. The writer resolves each element. One
  that resolves to the writer's own root raises `ValueError`, and so do two that resolve
  to one path. The writer stores the resolved tuple, sorted.
  - The writer's *citation view* is `MountCitations(self._view, self._profile,
    read_mounts)` when `read_mounts` is non-empty, and `self._view` otherwise.
  - Every check of decision 2 defaults to the citation view, not `self._view`. That
    includes `_refuse_facets`, so the default reaches every caller that passes no view:
    `_refuse`, `_preflight_replace_locked`, `revise` (`_revise_dataset_locked`) and
    `correct_identifier` (decision 3a).
  - Mutation-target reads and the own-index checks keep `self._view` and
    `self._corpus.index` (decision 1).
  - `_refuse_facets` hands `bearer_refusal` and `validity_refusal`
    `citations.acquisition_view(reading, local=…)` when `read_mounts` is set, and passes
    `validity_refusal` `reports=local`. `reading` is the view it was given, or the
    citation view. `local` is that view when it is an `_ImportView` overlay, and
    `self._view` otherwise. Without read mounts it hands them `reading`, as today. So the `_ImportView` overlays themselves are unchanged. Their resolution
    of retraction targets, coreference endpoints and every other relation stays local
    (decision 1). Only the acquisition-boundary judgment on an import path reads the
    session.
- `open_attended_session`'s `writer_factory` builds `read_mounts` from the session's
  **normalized** mount mapping (`mounted`), the one check 4 of session mounts §3.2
  already built with resolved keys and `_mount_resolver` receives. It omits `root`, the
  write root already resolved at check 3:
  `tuple(sorted(path for path in mounted if path != root))`. It passes `None` when no read mount remains. Filtering the raw
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
- **Mounts must agree on shared namespaces to be cited.** A citation into a mount that
  pins a different identity of a namespace the working corpus pins refuses
  `CitationContractMismatch` (decision 3). mm30 and a working corpus agree when they pin
  the same `biology` identity. The plan reads mm30's manifest and records whether they
  do, since the second-project milestone depends on it.
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
`errors.py` (`InputOutsideCorpus`, `CitationContractMismatch`). No other kernel lane is open on 2026-10-01. The
documents every lane rewrites are the adoption ledger, the roadmap, the guide index and
`test_designs_corpus.py`.

## 7. Guarantee rows

New rows J16–J21 in the `J` table.

| row | guarantee | mutation test |
|---|---|---|
| **J16** | In a session with read mounts, the write boundary resolves the citations of decision 2 over the write root and every read mount, reads each cited record in its holding corpus under the writer's profile, refuses a citation across differing identities of one namespace, and judges producers over the whole session on every path. The write lands in the write root alone | Corpus M (read mount) pins base, `biology` and a test-local contract W does not pin. M holds a dataset with a valid empirical-observation facet, a proposition, and an assessment with its run. In a session writing W: a run observing M's dataset, then an assessment of M's proposition over that run → written to W. An analysis spec targeting M's proposition → written. **Contracts:** M2 pins a different identity of a test-local namespace W also pins (two versions of one fixture contract), and citing M2's proposition → `CitationContractMismatch` naming M2, the namespace and both pins. **Producers:** each of these is set up by library writers on one root at a time, which cannot see the other corpora, so dangling edges are legal.<br>- A run in W whose `produces` names an address nothing holds, then a dataset at that address declared with the facet → `AcquisitionBoundaryRefused`, as on a one-root writer. The same with the dangling edge in M's run → refused.<br>- M3 holds a run producing M's facet-bearing dataset. An assessment over a W run observing that dataset → `EligibilityUnmet` naming M3's run.<br>- W holds a dataset without the facet, and M's run produces it. `revise` adding the facet → refused.<br>- M's run produces the address an `acquire` in the session would mint → the acquisition refuses.<br>- **Reverse direction:** `import_bundle` in the session of a bundle holding a run whose `produces` names M's facet-bearing dataset → `ImportRefused` naming the run as `member`, whose `__cause__` is `AcquisitionBoundaryRefused`. A plain write of such a run → `AcquisitionBoundaryRefused`.<br>- **Imported assessment:** W holds a facet-bearing dataset and a run observing it, and M holds a run producing that dataset. `import_bundle` of a bundle holding only an assessment over W's run → `ImportRefused` naming the assessment as `member`, whose `__cause__` is `EligibilityUnmet` naming M's run.<br>- **Split retrieval:** a dataset written in W whose payload's `retrieval` names an acquisition report held only in M → `FacetPayloadRefused` (`facet-retrieval-unresolved`). The same dataset raw-written into W, then an assessment over a W run observing it → `EligibilityUnmet` naming `facet-retrieval-unresolved`. The same dataset raw-written into W → `corpus_check(W)` and `audit_world` both report `facet-retrieval-unresolved`, and no other finding on it. A verification of M's assessment → written. A composite over M's propositions → written. M's tree hash is unchanged (J15). A session whose `mounts` names the write root by a symlinked path → opens, and J16's writes behave the same. **Negative:** the same writes through a library `CorpusWriter` on W, and through a session with `mounts=None`, refuse as §1 lists, with today's messages |
| **J17** | A citation two session corpora resolve refuses `AddressMapConflict` (`duplicate-location`, naming both), and a read mount whose operation lock is held refuses `BuildContended`. Both happen before any effect, with nothing written | M1 and M2 both hold a dataset at one address (a raw write into M2). An assessment over a run observing it → `AddressMapConflict` naming M1 and M2, and W unchanged. The same with the address held by W and M1 → refuses naming both. With M's operation lock held by another holder, an assessment citing M → `BuildContended`, and W unchanged. **Negative:** a write citing only W's records while M's lock is held → `BuildContended` (decision 5: the chain opens every read mount), and a write citing nothing (a proposition) → written |
| **J18** | `corpus_check` reports an assessment whose eligibility rests on references the corpus does not hold as `eligibility-unresolved` (warning). Locally decided failures stay `eligibility-unmet` (error) | W after J16's session: `corpus_check(W)` → one `eligibility-unresolved` warning per cross-mount assessment, naming the references, and no error. A raw-written assessment over a held run with no `observes` input → `eligibility-unmet` error (S7's case, unchanged). A run observing one held invalid dataset and one unheld dataset → `eligibility-unresolved`. **Negative:** a run observing only held invalid datasets → `eligibility-unmet` |
| **J19** | `audit_world` judges eligibility across covered corpora from the captured records, never raising: supported → no finding, unmapped → `eligibility-unmet`, held by an absent, damaged or excluded corpus, or by a malformed record → `eligibility-unresolved` naming the corpus and cause, and the audit continues | Publish an epoch over W and M after J16's session: `audit_world` → no eligibility finding. **Captured, not live:** the test wraps `open_world_view` so that, after the view captures and before the audit reads it, M's carrier loses the dataset's retrieval act-report (a raw delete) → still no eligibility finding. Remove M's carrier → `eligibility-unresolved` naming M, `absent`. Make one of M's files fail construction → `eligibility-unresolved` naming M, `damaged:construction`, with W's other records still audited and M's readable remainder audited as today. **Absent producer:** W holds an assessment, its run and the facet-bearing dataset that run observes, and M holds a run producing that dataset. Over an epoch covering both → `eligibility-unmet`. Remove M's carrier → still `eligibility-unmet`, because the epoch's published producers name M's run. A drift dataset in W, produced by nothing present, while M is absent → `eligibility-unresolved`, `producers-incomplete:M`. Make M's dataset's semantic stamp stale (a raw write before the epoch) → `eligibility-unresolved`, `malformed:semantic-hash-stale`, beside M's own `semantic-hash-stale` finding. Rebuild with W's run observing an M dataset that carries no empirical-observation facet (a well-formed record, so not in M's malformedness set) → `eligibility-unmet`. A malformed-payload dataset is the `unreadable` case, not this one: `facet-payload-malformed` is a malformedness code. **Negative:** an epoch covering W alone (M not admitted) → `eligibility-unmet`, since no covered corpus maps the dataset |
| **J20** | Belief over a world read gathers, admits and evaluates the two-installation split: assessment and run in W, proposition and observed dataset in M | Over the J19 epoch: `evaluate_over(world_view, M's proposition, …)` → the same answer, admission and `node_corpus` attribution (assessment and run → W, the others → M) as the same records evaluated from one corpus, and a lineage snapshot that reaches M's dataset. **Negative:** with M's carrier absent → `NoBelief("unavailable-corpus-absent")` naming M |
| **J21** | A corpus-local belief read refuses an assessment whose run names an input the corpus does not hold. It supersedes B4's absent-dataset clause ("nothing refuses"), cited (§13) | W holds a proposition P, assessed in the session over a run observing M's dataset. `gather(ReadView(W), P)` → `InputOutsideCorpus` naming the assessment, run and dataset, and `evaluate_over` → `Refused("input-outside-corpus: …")`. **Negative:** the same proposition over a world view → evaluates (J20) |

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

J16–J21 run in full on the certified volume, beside the checkout.
- W pins base, `biology`, coordination v2 and version 1 of a test-local fixture contract
  `fixture`.
- M pins base, `biology` and a second test-local contract W does not pin.
- M2 pins `fixture` version 2, the decision 3 mismatch.

`test_world_view.py`'s portable world tests do not reach `tests/acceptance`. J19 and J20
run there, against a published epoch.

### 8.3 N2 sabotages — `n2_arms_cut44.py`

| arm | sabotage | check that fails |
|---|---|---|
| J16a | `_refuse_ineligible` reads `self._view` whatever `read_mounts` says | J16's assessment over M's dataset refuses |
| J16b | `_refuse_assesses_target_kind` reads `self._view` | J16's assessment of M's proposition refuses |
| J16c | `_refuse_verification` reads `self._view` | J16's verification of M's assessment refuses |
| J16d | the `CitationContractMismatch` guard removed from `holder` | J16's M2 citation is written |
| J16e | `writer_factory` passes `read_mounts=None` | J16's writes refuse |
| J16f | `MountCitations.producers` answers from `holder(ref)` | J16's assessment over the M3-produced dataset is written |
| J16h | on the revise path, `_refuse_facets` hands `local` (`self._view`) to both judgments instead of `acquisition_view(reading, local=…)` | J16's revise case is written |
| J16m | on an `_ImportView` path, eligibility judges validity over the overlay alone | J16's imported-assessment case is written |
| J16i | `_refuse_facets` hands an `_ImportView` overlay to the judgments without `acquisition_view` | J16's acquire case mints |
| J16j | `acquisition_view` resolves `produces` targets in `base` only | J16's reverse-direction import is accepted |
| J16k | `_refuse_facets` passes `reports=base` (the citation view) instead of `local` | J16's split-retrieval write is accepted |
| J16l | eligibility passes `reports=view` (the citation view) instead of the dataset's holder | J16's assessment over the raw-written split dataset is written |
| J16g | `writer_factory` filters the raw `mounts` keys | J16's symlinked-write-root session refuses or contends instead of writing |
| J17a | `holder` returns the first holder in corpus order | J17's two-mount case writes |
| J17b | read-mount views open without the capture hold | J17's held-lock case writes |
| J18a | the `eligibility-unresolved` arm emits `eligibility-unmet` | J18's session corpus reports an error |
| J18b | the arm reports `eligibility-unresolved` only when no observed dataset is held | J18's mixed case (one held invalid, one unheld) reports `eligibility-unmet` |
| J19a | `audit_world`'s eligibility arm reads the captured corpus alone | J19's supported case reports `eligibility-unmet` |
| J19b | an absent holder is treated as unmapped | J19's absent-carrier case reports `eligibility-unmet` |
| J19c | the captured citation reader reads a cross-corpus holder through `corpus_view` | J19's post-capture case reports `eligibility-unmet` (`facet-retrieval-unresolved`) |
| J19d | the reader lets `CorpusDamaged` propagate | J19's damaged-holder case raises instead of returning an audit |
| J19e | the reader's producers omit `published_producers` | J19's absent-producer case reports no finding |
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
6. **Retrieval reports stay with their datasets** (decision 3a). A split dataset and
   report refuses everywhere.
7. **No world-wide bearer finding.** `corpus_check`'s and `audit_world`'s
   `facet-bearer-produced` findings stay per corpus. A raw-written run in one corpus that
   produces another corpus's facet-bearing dataset is reported by `audit_world` only
   through the eligibility of an assessment observing that dataset. Decision 8's
   producers are world-wide, so such an assessment is unmet. The write boundary refuses
   the state in both directions (decision 3a).

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

**Round 2 (2026-10-01), revise: P1 3, P2 1.** All four were accepted after checking the
code.
1. Eligibility still judged an observed dataset through its holder's view, without the
   session's producers. `validity_refusal` now runs over the mount view itself, and J16
   gains the M3-produced case.
2. `_revise_dataset_locked` and `correct_identifier` call `_refuse_facets` with the
   local view, and acquisition kept a local overlay. The writer's citation view is now
   the default for `_refuse_facets` on every caller. Both `_ImportView` overlays draw
   producers from the session while keeping their own resolution. J16 gains the revise
   and acquire cases, with J16h and J16i.
3. An absent producer restored eligibility. The audit's producers now include the
   epoch's `published_producers`. An unmapped dataset with an unreadable corpus is
   `producers-incomplete`. J19 gains the absent-producer case and J19e.
4. J16d could not reach its check. Restoration types the writer's estimand under the
   writer's profile first, so holder-profile decoding is unobservable. Decision 3 now
   decodes under the writer's profile and refuses a citation across differing
   identities of a shared namespace (`CitationContractMismatch`). J16d arms that
   guard.

**Round 3 (2026-10-01), revise: P1 1, P2 1.** Both were accepted after checking the
code.
1. An imported run producing a mount's facet-bearing dataset passed, because
   `bearer_refusal` resolves `produces` targets, and the overlay resolved them locally.
   Decision 3a now judges both invariants over the session in both directions, through
   one `acquisition_view`. The overlays themselves stay local. J16 gains the
   reverse-direction cases and J16j.
2. A cross-corpus retrieval report would have passed the write and then failed both
   checks. Retrieval reports are now explicitly local to their dataset (decision 3a,
   limitation 6), so the write, `corpus_check` and `audit_world` agree. J16 gains the
   split case and J16k.

Decision 3's mismatch rule is now stated as a policy choice (the reviewer's
clarification). Limitation 7 records that the bearer findings stay per corpus.

**Round 4 (2026-10-01), revise: P2 2, P3 1.** All three were accepted after checking the
code.
1. For a candidate, the retrieval lookup went to `base`, which can be the session-wide
   citation view, and eligibility kept session-wide report lookup. `acquisition_view`
   now takes `local`: the writer's own view, or the import overlay. Candidates read
   reports there, and eligibility reads the observed dataset's holder. J16 gains the
   raw-written split-dataset assessment and J16l. J16k is re-targeted at `local`.
2. J16h's sabotage was masked by the wrapper. It now bypasses `acquisition_view` on
   the revise path.
3. An import refusal surfaces as `ImportRefused`, whose cause is
   `AcquisitionBoundaryRefused` (`corpus.py`, `import_bundle`'s member loop). J16's
   import expectation is corrected.

**Round 5 (2026-10-01), revise: P1 1, P2 1, P3 1.** All three were accepted after checking
the code.
1. `import_bundle` passes its overlay to `_refuse_ineligible` directly, so an imported
   assessment was judged without mount producers. Eligibility on an overlay path now
   finds records through the overlay but judges validity with the session's producers
   (§3.1). J16 gains the imported-assessment case and J16m.
2. J16h's sabotage still saw mount producers, because on revise `reading` is the
   citation view. It now passes `local` to both judgments.
3. J16's plain-write expectation now names `AcquisitionBoundaryRefused`.

## 13. Planning notes

- 2026-10-01, at planning (plan `../plans/2026-10-01-mount-citations.md`):
  - **Decision 9 supersedes a frozen clause.** Row B4 (cut 22, the biology-pack design
    §7) states that `gather` over an observed dataset node absent from the view leaves
    it out: "the run value carries no such input, no `FacetRead` and no `observes`
    entry exist, nothing refuses". Its check is
    `test_domain_facet_read.py::test_an_absent_observed_dataset_is_absent_from_gather`.
    J21 refuses exactly that read on a corpus-local view, so "nothing refuses" no longer
    holds there. B4's other clauses stand: every read is validated, and only held
    datasets are read.
    - The rounds 1–6 reviews did not see this. It is resolved the way cut 43 resolved
      J9's two-root clause. J21 is the successor of B4's absent-dataset clause, the
      cut 44 document cites it, and B4's frozen declaration is not edited.
    - B4b's check keeps its node id, because the frozen declaration pins it. Its body
      now asserts the J21 refusal, with a docstring naming the supersession.
    - B4b's sabotage is re-targeted in `test_n2_cut22.py`'s `_LIVE_SABOTAGES` to J21a's
      mutation. The two arms share it, as J9a and J12a share theirs.
    - *Rejected:* dropping decision 9. Admission would keep judging a run with part of
      its lineage silently missing, and science's guard would stay the only defence.
  - **Foreseen re-targets.** Two live pins move:
    - cut 20's F4 (`reason = validity_refusal(view, view.get(dataset_ref), profile)` in
      `eligibility_refusal`) moves into `eligibility_outcome` with the judge and reports
      arguments. It is re-targeted in `test_n2_cut20.py`'s `_LIVE_SABOTAGES` with the
      same mutation, reading the facet directly.
    - cut 22's B4b, above.

    Cut 32's `_refuse` pins (`reading = self._view if view is None else view`, the
    `_refuse_supersedes_same_kind` lines) and the pinned `self._refuse(record, …)` call
    sites stay byte-exact. `_refuse` becomes a wrapper that opens the citation scope.
    Its body moves unchanged into `_refuse_cited`, which first rebinds a `None` view to
    the citation view. Any further stale arm is a finding against this spec.
  - **`eligibility_refusal` keeps its string return.** §3.3's structured outcome is a new
    `eligibility_outcome(view, node, profile, *, judge=None, reports=None) ->
    EligibilityOutcome | None`. `eligibility_refusal` becomes its string projection with
    the same keyword arguments. Frozen acceptance callers that compare its string
    (`test_facet_acceptance.py`, `test_acquisition.py`) are therefore untouched.
    `EligibilityOutcome(reason, unresolved=())` is `unresolved` exactly when
    `unresolved` is non-empty.
  - **mm30 can be cited from a shipped-pack working corpus.** The relocated replica pins
    `biology:24bcec43…` (reproduction §23.2), which is
    `shipped_domain_contract("biology").content_identity`. Decision 3's guard passes for
    a working corpus on the shipped pack.
  - **`producers-incomplete` is judged per dataset, and the scan continues.**
    - A known producer always decides a dataset: it is produced, whatever else is
      unreadable.
    - An own dataset the epoch never mapped, with no known producer, while a covered
      corpus is unreadable, is treated as an unresolved reference. Its cause is
      `producers-incomplete:<corpus ids>`.
    - Eligibility goes on to the run's other observed datasets, so a later valid one
      still supports the edge.

    This replaces the draft plan's early abort, which turned definite failures into
    warnings and skipped later valid datasets (plan review 1, P2).
  - **Portable fixtures.**
    - The writer tests use roots W, M and M3 on `profile_with()` (testing plus the
      fixture `biology`), so `typed_estimand()`'s `testing/affects` decodes.
    - M2 is on `profile_with("other")`, decision 3's mismatch.
    - M4 is on the testing contract alone, a namespace set without `biology`.
    - The world-audit tests keep `WITH_BIOLOGY`, which `corpora` pins in every
      manifest. Eligibility decodes no estimand. Acquisition's certified path is not portable, so J16i checks the seam
    acquisition calls, `CorpusWriter._refuse_acquired_dataset` (`holdings/acquire.py`).


- 2026-10-01, at Task 5 (belief reads):
  - **J20 compares verdict, binding and admission, not `belief_input_digest`.** The
    split world and the one-corpus baseline agree on the belief value, the policy
    binding and the admission. The digest differs by construction: the closure
    projection names `producer_snapshot` (the world's epoch identity against
    `producer-snapshot-1`) and the retraction `coverage` (the carriers' corpus ids
    against the single corpus id). Those are the two fields that name a corpus; every
    other closure member is equal.
  - **Tests that relied on the silent drop.** None beyond B4b's check. The rest of
    `just test-fast` is green, including `test_publication_arrival.py` and
    `test_facet_read.py`, which also seed `observes_missing`.

- 2026-10-01, at Task 7 (N2 declarations):
  - **J16-c's check was reshaped.** It was vacuous: a report-less verification never reads the view (cut 18 R2), so the
    `view=self._view` mutation changed nothing. The check now writes a published, report-carrying verification over a
    mount assessment, and the mutation and check id are unchanged.

- 2026-10-01, after the cut-44 runner's prefix chain:
  - **B4's supersession also reaches cut 23's durable test tail**, the corpus-local read after M is removed in
    `test_evaluation_reports_an_absent_corpus_and_attributes_at_the_read_durably`, which now asserts J21's refusal. No
    other acceptance test changed.

- 2026-10-01, at Task 9 (results, `../../plans/2026-10-01-conformance-cut-44-results.md`):
  - **Acceptance fixtures.** §8.2 and the J16 row describe M pinning a test-local
    namespace W lacks, and M2 on version 2 of the fixture contract. The durable module
    (`test_mount_citations_acceptance.py`) uses `profile_with()` for M and M3 and
    `biology("other")` for M2, as the portable tests do, so that it runs on the certified
    volume without a further test-local contract. The decision 3 mismatch is therefore
    exercised on `biology`. No durable case covers a namespace only M pins; a world read
    over that shape is filed as `beliefs-d69102`, since `consulted_contracts` takes its
    corpora only from attributed nodes.
  - **J20's "the others → M".** `gather` attributes only assessments, runs and datasets
    (decision 10), so `node_corpus` carries no entry for the proposition. The durable case
    checks the proposition's corpus through the world view's `corpus_of`, and the
    observed datasets through `node_corpus`.
  - **§3.2 drift.**
    - The session passes `()`, not `None`, when no read mount remains, and when `mounts`
      is `None`. The writer treats an empty collection as no read mounts.
    - `acquisition_view(reading, local=…)` was built as `MountCitations.overlay(base)`,
      returning a `_SessionOverlay` over `base` whose producers and `produces` resolution
      read the session.
    - The old `eligibility_refusal` docstring's rationale was dropped when its body moved
      into `eligibility_outcome`. It is still true of the code (only `observes` inputs are
      read, and nothing reaches the registry compile), so `eligibility_outcome`'s
      docstring restores it: `reads` inputs never confer eligibility.
