# Conformance cut 35 — results

**Cut:** `../designs/2026-09-20-conformance-cut-35.md`
**Freeze:** `f746cf7cf42e4baaf537fd408d86925716ee9c2f`; SHA-256 `d669f076f4dab0474888108d230a15e120cc76da4164a44446cf5d62ef91ddb0`
**Declaration:** `python/tests/n2_arms_cut35.py`; SHA-256 `5a384e510ebfdfe2ffad70bf6990f869a96e66c899e139959e053e35431e48df`
**Subject:** URL retrieval — the `url` locator, the network boundary and the acquisition operation
**Design:** `../superpowers/specs/2026-09-19-url-retrieval-design.md`
**Plan:** `../superpowers/plans/2026-09-20-url-retrieval.md`
**Discharged:** 2026-09-20 on `url-retrieval`, through `d525b7d`
**Runner:** `python/tools/cut35_acceptance.py`

## 1. What ran

The certified runner exported cut roots 4–35 to the certified cut-35 root
(`.work/acceptance/cut35`, beside the checkout on the repository's own
volume) and the reproduction root to the retained mm30 corpus, then ran the
complete prefix through cut 34 (the cut 34 runner and its own prefix
chain back through cut 17's nineteen phases) followed by cut 35. It exited **0**. Its
final declaration lines, verbatim, were:

```text
declared arms: 28 (= 27 declaration units; 8 guarantee rows)
guarantee rows exercised: 8 (6 newly closed: H4, G9, R10, T5, T1, T4; T2 and T7 partial)
```

Cut 35's own phases passed:

```text
[cut35 phase 2/3] test_url_retrieval_acceptance.py
27 passed in 41.81s
[cut35 phase 3/3] test_n2_cut35.py
10 passed in 21.05s
```

The whole chain ran in roughly 58 minutes of wall clock (14:05–15:03 UTC);
every earlier cut's phases passed (54 `passed` lines in the runner log, no
`failed` or `error`). No test reaches the network: every transport seam in the acceptance module
resolves to a public address and dials either the in-process TLS server on
loopback (the committed test certificate, `python/tests/fixtures/tls/`) or
the scripted fake.

All twenty-seven baselines reported **resolved**, and every one of the
twenty-eight mutations reported **sound**
(`test_every_live_check_resolves_and_passes_without_sabotage` and
`test_every_arm_fails_under_its_own_sabotage`, both in the `10 passed`
above). No unit was stale, vacuous, mixed or uncollected. `BI-11` is the
one unit homed to two arms, `BI-11a` and `BI-11b`, as the frozen §5
declares; every other unit is homed to exactly one.

| declaration unit | baseline | mutation | guarantee-row effect |
|---|---|---|---|
| H4-a | resolved | sound | H4 closes |
| H4-b | resolved | sound | H4 closes |
| G9-a | resolved | sound | G9 closes |
| R10-a | resolved | sound | R10 closes |
| T5-a | resolved | sound | T5 closes |
| T5-b | resolved | sound | T5 closes |
| T5-c | resolved | sound | T5 closes |
| T7-a | resolved | sound | T7 partial (same-root case read) |
| T7-b | resolved | sound | T7 partial (same-root case read) |
| T1-a | resolved | sound | T1 closes |
| T2-a | resolved | sound | T2 partial (`acquisition` read) |
| T2-b | resolved | sound | T2 partial (`acquisition` read) |
| T2-c | resolved | sound | T2 partial (`acquisition` read) |
| T2-d | resolved | sound | T2 partial (`acquisition` read) |
| T4-a | resolved | sound | T4 closes |
| T4-b | resolved | sound | T4 closes |
| BI-1 | resolved | sound | boundary invariant |
| BI-2 | resolved | sound | boundary invariant |
| BI-3 | resolved | sound | boundary invariant |
| BI-4 | resolved | sound | boundary invariant |
| BI-5 | resolved | sound | boundary invariant |
| BI-6 | resolved | sound | boundary invariant |
| BI-7 | resolved | sound | boundary invariant |
| BI-8 | resolved | sound | boundary invariant |
| BI-9 | resolved | sound | boundary invariant |
| BI-10 | resolved | sound | boundary invariant |
| BI-11 (arms a, b) | resolved | sound, sound | boundary invariant |

**Staleness evidence.** The slice moved **five** pinned `before` strings out
from under four earlier guards, and each was re-targeted in the commit that
moved it. Two belong to cut 10, whose guard is cited-not-run (its bytes are
pinned by cut 17's content hash, so its `_LIVE_SABOTAGES` cannot be
edited), and were recorded in `python/tests/cited_not_run.py`'s
`stale_arms` register for `test_n2_cut10.py`, the mechanism that register
already used for `H4u1[12]` and `J8[27]`: `J3[22]`, moved by Task 1 when the
named deferral `UrlLocatorDeferred` that J3 pinned was deleted and
`url_locator` became the real `UrlLocator` (`b34bcb5`); and `L7u2[17]`,
moved by Task 4 when `write`'s `store_write` call went inside the
`StoreWriteRefused` wrap (`bb9a92d`). Three belong to live guards and were
re-targeted in their `_LIVE_SABOTAGES` tables: cut 17's `E6a`, whose pin
carried `_append`'s `location: StoreLocator` annotation, widened to
`Locator` by Task 4 (`bb9a92d`); cut 16's `T2a`, whose pin
`operation_port.execute_fulfilling([operation], intent_digest)` became
`execute_fulfilling(plan, intent_digest)` when Task 5 gave
`_publish_operation_report` its `operations=` plan (`229d9d6`); and cut
19's `J11b`, whose one-line pin
`self._session._require_current(self._invocation)` came to occur twice in
`session/writer.py` once Task 6 added `_closing_hold` with the same currency
re-check, and now matches the two-line sequence through `commit = perform()`
unique to `_act` (`c72b24a`). Every re-target was verified against the
frozen declaration's own property: no frozen `n2_arms_cut*.py` file changed,
each re-targeted `after` still fails the check the frozen arm requires, and
`tests/test_arm_staleness.py` reported `8 passed` after each move and on
the discharge commit (`8 passed in 0.60s`), identical to the tree's
baseline before the lane opened. Task 8 created files only and moved no
pin.

The full repository gate (`just hook-pre-push`) was started on the discharge
commit `d525b7d` with the certified exports as a detached run and had not
finished when this record was written (its log stood at the Python suite's
first quarter, with `ruff`, `pyright` — `0 errors, 0 warnings, 0
informations` — `tsc --noEmit` and Biome already green). Pre-push gate:
recorded at merge (§6). `just check` passed on every commit of the lane
through the pre-commit hook; `tasks check` reported zero errors and zero
warnings throughout. `just test-fast` on the tree after Task 6 reported
`5171 passed, 1 skipped in 186.75s`; the one Python skip is the intentional
causal-only fixture arm cut 33's record named
(`tests/test_composite.py:119`). No capability refusal or waiver occurred.

## 2. Accounting

The cut carries **27 declaration units**: sixteen against rows — H4 (2),
G9 (1), R10 (1), T5 (3), T7 (2), T1 (1), T2 (4), T4 (2) — and eleven
boundary invariants holding the locator, the transport, the look, the
acquisition's close, the reducer and its successor binding, the evidence
key and the materialization classification. **H4, G9, R10, T5, T1 and T4
close in full.** **T2 stays partial** on the `audit` and `re-check`
operation kinds, which no boundary opens (decision 12): `acquisition` is
read to success, through root-selection and intent-append failure, and
through the second fulfillment; `run-attempt`, `import`, `move`,
`consolidate` and `corpus-write` were read by cuts 3, 5, 16 and 18
(decision 12). **T7 stays
partial** on its cross-root case, owned by `cross-root-publication` (tier
3); the same-root case is read in full.

`url-retrieval` — the `acquisition` lane's only boundary — closes with this
cut and leaves the ledger's table and the roadmap's boundary index in the
same commit. `act-report-remainder`, the ride-along, does not close: it
becomes an off-path boundary of its own carrying T2's two operation kinds
(§5).

The global corpus is **183 of 216 guarantee rows closed, 33 open**, a
six-row increase from cut 34's 177. `python/tools/roadmap_status.py` carries
the cut-35 accounting (added as
`35: ("conformance-cut-35-results §2", "H4, G9, R10, T5, T1, T4", "T2, T7")`
in `ACCOUNTING`, the plan's own place to record a new cut) and produces the
roadmap's Appendix A with the six rows closed, T2 and T7 partial at cut 35,
the G and H tables fully closed for the first time, and no row reopened.
T7 was never selected before this cut; it enters the accounting as partial.

The cut changes no grammar, no kind and no contract: both `CONTRACT.yaml`
copies are byte-identical before and after the lane. The
holdings-observation record gains the second arm of its banked locator
union, `url`, under the unchanged `science.holdings-observation.v1`
(construction now accepts what §2 of the holdings design banked); the
operation-kind enum is unchanged (`acquisition` was a member since 2026-08-11); the
act-report's entry vocabulary is unchanged (`byte-locator-untested` and
`retrieval-failed` were reserved for the locator act at the same date). The
holdings reducer's rule identity moves (decision 14): receipts under the
old binding validate where the old implementation is held, which BI-9
reads.

## 3. Evidence

No prior frozen declaration or cut body changed. Cut 35's §§2–7 remain
byte-exact to the freeze object; only its status line changes at
discharge. The cut-35 declaration remains byte-exact at its pinned
SHA-256. Historical evidence in prior results records and the reproduction
record is unchanged except by the addendum this cut adds to the
reproduction record (§4).

### 3.1 Corrections carried by the cut document

The frozen cut required no post-freeze supplement. Its `Plan:` field cites
the implementation plan (`../superpowers/plans/2026-09-20-url-retrieval.md`)
rather than the design spec, on cut 34's pattern, which the review accepted
as intended. Three claims in the frozen body are superseded by what the
tree established and are recorded here rather than edited there:

- **§3's BI-11 row and §6's fourth check name `ProjectApprovalRefused` as
  the read-only replica's cause.** The fixture (`replicate_root`, then a
  `store_write` against the replica, which reads `READ_ONLY_UNSERVICEABLE`)
  refuses with `ExecutionError(applied=0)` from a **`PreconditionRefused`**
  cause — in the routine set, so the classification is unchanged. The live
  spec was corrected at `696198c` (§5's parenthetical, the BI-11 row, and a
  §17 entry); `test_bi11_the_materialization_classification` asserts the
  cause the fixture produces, `type(cause.__cause__) is PreconditionRefused`,
  through a direct `write` against the replica before its five labelled
  blocks. A reader of the frozen cut alone sees the stale name.
- **§5's sabotage module and wording diverge from the declaration for
  seven arms** (§3.2's table). The declaration is sha-pinned and every arm
  is sound; the frozen table is the plan's draft, and the arms pin the tree.
- **`LifecycleState.READ_ONLY`**, which the spec's BI-11 fixture text named,
  does not exist; the replica's states are `READ_ONLY_SERVICEABLE` and
  `READ_ONLY_UNSERVICEABLE`. Corrected in the spec at `696198c`.

### 3.2 Deviations from the plan, all reviewed and taken

**Frozen §5 versus the declaration.** Every arm whose module or sabotage
differs from the frozen §5 row, with the reason:

| arm | frozen §5 | declaration (`n2_arms_cut35.py`) | why |
|---|---|---|---|
| H4-b | `holdings/boundary.py`: a `Failed` retrieval publishes `Absent()` | `holdings/boundary.py`: the `NotAttempted` branch publishes a `Found` observation with an all-zero digest before returning its `InconclusiveLook` | `holdings_observation` refuses `Absent()` at a `url` location by construction (Task 1's "a url location never establishes absent"), so the frozen sabotage would raise inside the sabotaged tree rather than publish; the arm spells the publication the record layer accepts, and the check's "mints nothing, carries no digest, identity unchanged" fails under it |
| T2-c | `holdings/acquire.py`: an append failure is caught and the looks proceed | `corpus.py`: `_append_operation_intent` catches the port's `ExecutionError` and continues with a zero digest, so the looks proceed | the append and its port call live in `corpus.py`; `acquire.py` carries no line around the append for a catch to land on |
| T2-d | `holdings/acquire.py`: the close publishes the report twice under the one intent, swallowing the refusal | `root.py`: the defect mapping's `DefectKind.DUPLICATE_FULFILLMENT` member maps to `"fulfills-invalid"` | a second fulfillment's refusal is the engine's (`execute_fulfilling` refuses it before `acquire.py` can swallow anything), so the check reads the raw second fulfillment as `MalformedView` with kind `duplicate-fulfillment` and the arm sabotages the classification (planning correction (c)) |
| T4-a | `holdings/rules_v1/holdings.py`: an unmatched `acquisition` intent adds an `unsettled` reason | `holdings/qualify.py`: the same sabotage | `qualify.py` is the generated first half of the concatenated bundle, "the generated copy is what the rule bundle reads" (§5's own BI-9 note); the sabotage must land where the bundle reads it |
| T4-b | `holdings/rules_v1/holdings.py`: a head referenced by a report's entry is retained after deletion | `holdings/rules_v1/holdings.py`, as §5 names it — the plan's brief had re-sited it to `corpus.py`'s `_delete_locked` | `writer.delete` refuses `act-report` and `holdings-observation` by the banked kind exclusion (world-changing families §3.0, built at cut 18), so a `_delete_locked` sabotage can never bite: the managed delete never reaches it for these kinds. The spec's §11.2 test text `writer.delete(...)` was wrong for the same reason; both T4 tests assert the refusal (`DeletionKindExcluded`) and remove the record raw, on cut 18's G8 shape |
| BI-1 | `holdings/records.py`: host case is preserved | `holdings/records.py`: the default port is elided no longer | `urlsplit` lowercases scheme and host itself, so a "host case is preserved" sabotage has no line to land on; default-port elision is the profile's own rule (planning correction (n)) |
| BI-11a | `holdings/boundary.py`: the wrap widens to the whole of `write` | `holdings/boundary.py`: the wrap widens from the `store_write` call through `_final` and the publication — the `before` is the seam call `ctx.seam.store_refusal(caught)` | the plan's bytes predate `b065711`, after which the predicate is reached through the seam; same claim, the tree's bytes |
| BI-11b | `holdings/boundary.py`: `store_refusal` returns `True` for every `ExecutionError` | `root.py`: `_store_refusal`'s predicate line becomes `return True` | the predicate moved to the composition root at `b065711` (below); same claim, the tree's module |

The staleness guard's site test (`test_every_sabotage_names_one_real_source_site`) holds every `before` to exactly one occurrence in its named module, so a mis-sited arm would have read `stale`; none did.

**Read at freeze.** Three sabotage sites the plan left to the tree's bytes,
plus two the tree's layout forced:

- **T1-a** (`world/verify.py`): `before` is the two-line
  `_claimed_by_the_corpus_layout` definition; `after` conjoins
  `and not path.startswith("act-report/")` around the parenthesised
  original expression.
- **T2-d** (`root.py`, not `world/logmodel.py`): `grep -n
  '"duplicate-fulfillment"'` finds the closed mapping member at
  `root.py:1479`; `logmodel.py:118` is the taxonomy's string set, not the
  mapping. `before` is the mapping line, `after` maps it to
  `"fulfills-invalid"`.
- **T4-b** (`holdings/rules_v1/holdings.py`): `before` is the unique
  `_check_walks(by_location, observations)` call; `after` precedes it with a
  scan of every captured `act-report` whose entry names an observation
  absent from the capture, synthesising a `found` head at the entry's
  subject.
- **BI-10** (`intents/evidence.py`): the plan's one-line `before` does not
  occur — the tree formats the `ObservationEvidence(...)` call over four
  lines — so both `before` and `after` were rewritten in that layout.
- **BI-11a / BI-11b**: as tabled above, targeting `holdings/boundary.py`'s
  seam call and `root.py`'s predicate.

**Code and test deviations, by task.**

- **The `store_refusal` classifier lives in the composition root and rides
  the seam (`b065711`).** The plan placed it in `holdings/boundary.py` with
  the atoms cause types imported there, which violates the tested
  composition-root invariant (`root.py` is the one `atoms` importer;
  `test_capability_boundary.py`). The predicate moved verbatim to
  `root.py` as `_store_refusal`, `StoreActSeam` gained
  `store_refusal: Callable[[Exception], bool]`, `write` calls
  `ctx.seam.store_refusal(caught)`, and `ledgered_seam` delegates it. The
  same fix inventoried `look` in `WRITE_ENTRY_POINTS` with an E1 case in
  `test_permit_entry_points.py`, and added `holdings/boundary.py`,
  `holdings/acquire.py` and `holdings/transport.py` to
  `RAW_WRITE_ALLOWLIST` for their scratch-file `unlink` cleanups.
  Classification semantics are unchanged. Task 4 was reopened for this after
  Task 5 found the three failures.
- **The cut-10 pin re-targets go through `cited_not_run.py`, not
  `_LIVE_SABOTAGES`** (Task 1's Step 6, Task 4): cut 10's guard is
  cited-not-run and hash-pinned by cut 17, so `J3[22]` and `L7u2[17]` are
  registered as `stale_arms` there; the live re-targets are cut 17's `E6a`,
  cut 16's `T2a` and cut 19's `J11b` (§1's staleness evidence).
- **`intents/evidence.py` changed in Task 1, not Task 2**: the union type
  forced `decode_record` onto `value.location.canonical()` (byte-identical
  for the store arm) a task early; Task 2 verified it in place.
- **Task 3's transport code deviated from the plan's verbatim text only
  under lint and type gates**: `# noqa: B018` on the two `.port` accesses
  whose side effect is the range check; `socket.timeout` restored beside
  `TimeoutError` in the transport-failure parametrization after `ruff
  --fix` collapsed the deliberate dual spelling into a duplicate case;
  `fetch`'s `tmp_path` made keyword-only and typed; `isinstance`
  narrowings added after `== Failed(...)` equalities.
- **Task 4's fixture**: `TransactionHalted` is imported from
  `atoms.core.errors`, not `atoms.chain.errors`; the replica test asserts
  `PreconditionRefused` (§3.1).
- **Task 5's acquisition**: `pins_for` comes from the test helper
  `profiles`, not `beliefs.corpus`; the lock probes run `lock.capture()` on
  a helper thread (`OperationLock` has no non-blocking acquire); the
  `no-port` spoil constructs its writer with the durable executor factory
  so the refusal under test is the port's; each pre-intent refusal is
  parametrized with its exact type (`AcquisitionRefused`,
  `PreconditionRefused` for a store-less materialization, `MalformedRecord`,
  `ValidationRefused`) rather than one broad tuple; the positive test runs
  under `WITH_BIOLOGY` and asserts the minted facet set including the
  `semantic-identity` the dataset node stamps; a hold-order test was added
  for decision 15.
- **Task 6's session route**: the reconciliation test asserts equality of
  the URL and store shapes' findings plus membership of
  `session-outcome-unknown`, because the fixture ledger always carries a
  `session-unclosed` finding the plan's exact list omitted; the survey's
  local `MalformedRecord` class was replaced by the kernel's; the whole
  "Preflight" section of `test_admission_survey.py` went with the names it
  called (covered by `test_holdings_transport.py` since Task 3);
  `test_session_writer.py`'s method inventory gained `acquire`.
- **Task 8's checks** (all recorded in its report): T4-a's added report
  comes from an unpinnable acquisition, since a second look publishes an
  identity-bearing observation; T2-d's raw duplicate copies the root
  without its metadata sibling (a copy with it is `binding-mismatched` and
  refuses inspection); the H4-b/T2-a/BI-7 registration counts are over
  fulfilling registrations, since `adopt_manifest` registers a transaction
  fulfilling nothing; BI-7 reads "unmatched" through
  `qualify.decode_holdings_intent`/`qualify_intent`, the reduction's output
  carrying no per-intent status; BI-9 rebuilds the cut-34 bundle from
  `git show 3873d16:` (the cut-10 results record pins no rule identity) and
  validates the old binding's receipt over a store-only coverage, since the
  old rule cannot read a URL location; BI-8's session half re-composes Task
  6's lock probe over the `session` fixture.
- **T2-b's store-less half runs off the certified volume** (a `tmp_path`
  session with no bound store); its port-less half runs on it.

**Planning corrections recorded before implementation.** Eighteen
corrections (a)–(r) found while writing the plan are recorded in spec §17
at `5417455`; the plan's Task 0 brief had omitted the recording step and it
was taken in a fix round. They cover, among others, the `port=` override on
the writer's intent and report members (the session's ledgered port is a
separate object), the close's session-then-root lock order through
`hold`, `_reconstruct` under the closing lock before any ref resolves,
transport failures by fixed category with `HTTPException` classified and
every exceptional exit unlinking the scratch file, the sixth category
`malformed` for a server-supplied `Location`, the trailing slash after a
final dot-segment, IPv6 brackets on the wire, port `0` refused, and the
survey's `NetworkProbe.fetch` as an adapter over `retrieve`.

### 3.3 Limitations found at review

Review findings the lane deferred rather than fixed, by task; each is a
limitation of the code or its tests as they stand, none reopens a row.

- **Task 0**: the cut's `Plan:` field cites the implementation plan rather
  than the spec (accepted, §3.1).
- **Task 1**: decision 1 is silent on an empty port (`:`), a leading-zero
  port (`:0443`) and a percent-encoded host — spec §13 candidates, not
  code; `%2E` is decoded before dot-segment removal (RFC order) where
  decision 1's listing reads the other way — a spec clarification;
  `_normalized_path`'s error text carries the path (construction-time, the
  caller's own spelling); the task report's early GREEN blocks lacked
  summary lines.
- **Task 2**: the intent shape's `_url` scheme check is case-sensitive and
  looser than `_canonical_url`, so a non-canonical `url` key never matches
  an observation and the strict gate is the codec — a spec-note candidate
  (§7's limitation 9 covers the consequence).
- **Task 3**: `content-encoding <value> is not identity` echoes a server
  header value into a reason (plan-mandated); `int(declared_length)`
  accepts `+4`/`-1`/underscore spellings (only the fake reaches it);
  `ip_address()` sits outside the `try` in `preflight`; the TLS fixture's
  `handle_error` swallows every handler exception and its comment names the
  wrong seam; the timeout is per operation, not wall clock (a docstring
  sentence). Resolved at review: hop 0's spelling refuses bytes outside
  0x21–0x7E through `_canonical_url`.
- **Task 4**: `look` is defined before `ActContext`; no `look` test with a
  valid `expected=` digest (Task 5's acquisition tests cover the
  expectation path).
- **Task 5**: `test_a_stop_mints_nothing_and_the_hold_enters_before_the_root_lock`
  is misnamed (no stop) and proves hold-with-root-free only, not
  root-inside-hold; `..._reads_unfinished` never asserts `UNFINISHED`;
  `_publish_operation_report` silently ignores `operation=` when
  `operations=` is given and accepts `operations=()`; `closed_at` is
  stamped before the closing locks; `Stop.reason` carries `str(refused)`
  — in memory only, never to be copied into a record;
  `AcquisitionOutcome` cannot distinguish already-held from
  expectation-mismatch; `_refuse_acquired_dataset` duplicates
  `_validate_import_bundle`'s overlay idiom.
- **Task 6**: `survey_admission.APPROVED_SCHEMES` is dead and its comment
  stale; `resolver=`/`connect=` lost their annotations; the
  `test_admission_survey._SPEC` comment is stale and case 6's "no request
  issued" is proven only in `test_holdings_transport.py`; the reconcile test
  could assert the exact finding list; no arm sabotages `_closing_hold`'s
  currency re-check (a candidate row for a later cut).
- **Task 7**: the report's run command carried the session's
  `SCIENCE_CUT*_ROOT` exports beyond cut 34's command (inert for the mm30
  driver).
- **Task 8**: T2-b's store-less half runs off the certified volume; BI-9
  shells `git show 3873d16:` and so needs history (commented);
  `test_n2_cut35.py:310` carries a trailing "Export the live tuple" comment
  followed by nothing.

The frozen §7's nine limitations stand as banked: a URL never mints
`absent`; credential-free authoring of the declared URL is the caller's
obligation; internationalized host names refuse at construction (filed,
§5); the materialization buffers the whole resource once; no retry, proxy
or authentication; a look-only acquisition through the session still needs
a bound store (filed, §5); T2 stays partial on `audit` and `re-check`
(§5); the reducer's rule identity moves; a raw-written non-canonical `url`
intent is unmatched forever.

## 4. Reproduction measurement

The reproduction record's §14 addendum
(`../designs/2026-09-05-mm30-reproduction.md`) re-ran
`reproduction.rederive` on 2026-09-20 in a fresh process at `c72b24a`
against the existing cut-32/33/34 corpus. No contract succeeded, so the
corpus was neither recreated nor moved aside — read in place, as at §13.
`MM30_PREDECESSOR` again had to be set explicitly, the same declared-default
defect §13 recorded.

The slice adds the `url` locator, the two-arm codec, the `url` arm of the
intent shape, the transport, the URL look, the acquisition operation and its
session route, none of it reached by the mm30 driver: `grep -n
derive_holdings python/tools/reproduction/*.py` is empty, so the reducer —
and its moved rule identity — is never invoked by this corpus. All five
stored holdings observations in mm30's corpus are `store` locations; read
through the widened two-arm codec, all five decode without error and each
decoded `location_facet()` is byte-identical to the stored facet (the
snippet and its output are in §14.1).

The fresh answer was `NoBelief(reason="no-directional-outcome")`, equal to
the recorded answer (`rederived_equal: true`). `state.json` was rewritten
with byte-identical content (a full-file diff against the pre-run copy is
empty; `assessment_identity_derived`, `assessment_identity_stored`,
`claim_identity`, `composite_identity`, `corpus_check_findings` and
`audit_findings` all unchanged); only `findings.jsonl` gained the run's own
log lines. No pinned digest moved. The `url` arm and the `acquisition`
operation are exercised by the acceptance module alone.

## 5. Remaining boundary

`url-retrieval` closes in full at this cut: H4, G9, R10, T5, T1 and T4
close, T7's same-root case is read, and the `acquisition` lane has no
further open boundary.

**T2** remains partial on the `audit` and `re-check` operation kinds, the
two members of the enum no boundary opens as an operation (the audit
evaluator is read-only and its reporting wrapper — act-report design §4 —
is unbuilt; the URL look appends a `re-check` holdings intent, which is an
act, not an operation). `act-report-remainder` carries exactly this
remainder as an off-path boundary of its own, re-homed to the `world-read`
lane's column (`audit.py`, `world/audit.py`, `holdings/boundary.py`) and
ranked after `l13-preimage`; its task is `beliefs-86b150`, replacing the
ride on `beliefs-d13fe8`.

**T7** remains partial on its cross-root case, owned by
`cross-root-publication` (tier 3, `beliefs-256f17`), unchanged by this cut.

**C10** remains partial on the `instrument-certification` eligibility arm,
owned by `contract-cut`, untouched here.

Two ideas are filed rather than left as hidden limitations, neither of
which reopens a row this cut closes: `beliefs-1af7a7`, IDNA host names in
the `url` locator (§7 item 3: a non-ASCII host refuses at construction, and
an IDNA canonicalization rule is a profile amendment to holdings §2); and
`beliefs-940592`, a store-less look route through the session (§7 item 6:
`acquire` through the session needs a bound store because
`holdings_context` does, and a look-only acquisition over a store-less
session is undesigned). The `audit` and `re-check` wrappers, which spec
§16 named as a third idea, are carried by `beliefs-86b150` instead, since
the boundary now has its own task.

## 6. Main integration

Filled at merge.

## 7. Execution rulings

Every `Ruling:` entry from the execution ledger, in chronological order:

- **Re-target cut 10's `J3` through `tests/cited_not_run.py`'s `stale_arms`,
  not the plan's `_LIVE_SABOTAGES` edit in `test_n2_cut10.py`** (Task 1).
  The plan's Step 6 premise — that cut 10's guard is live — does not hold:
  the guard is cited-not-run, its bytes pinned by cut 17's content hash, and
  the tree's re-target mechanism for it is the register already used for
  `H4u1[12]` and `J8[27]`. Task 2's "as Task 1 Step 6 did" means the same
  route. Cost if wrong: a `J3` pin recorded in the wrong register, which
  `test_arm_staleness.py` catches (it passed).
- **Accept `intents/evidence.py`'s switch to `value.location.canonical()`
  in Task 1** (Task 2 Step 4's exact change, done a task early because
  pyright fails on the widened union). Cost if wrong: none; Task 2's
  dispatch noted it and verified it in place.
- **Correct the live spec's BI-11 cause (`ProjectApprovalRefused` →
  `PreconditionRefused`) with a §17 note, and leave the frozen cut-35 §3/§6
  text untouched** (Task 4). Frozen bodies are byte-exact by constraint;
  this record's §3.1 records the discrepancy and Task 8's arm asserts the
  cause the fixture produces, which is in the closed routine set. Cost if
  wrong: a reader of the frozen cut alone sees the stale cause name until
  this record.
- **Move the `store_refusal` predicate to `root.py` on the seam and
  inventory `look`** (Task 4, reopened after Task 5). The plan's placement
  in `holdings/boundary.py` with atoms cause types imports `atoms` outside
  the composition root, a tested invariant the spec did not account for.
  Cost if wrong: a seam-field churn across four constructors; classification
  semantics unchanged either way.
- **Target BI-11a at `holdings/boundary.py`'s seam call and BI-11b at
  `root.py`'s predicate, with the plan's claims** (Task 8). The plan's
  `before` bytes predate `b065711`; the arms pin behaviour, not the plan's
  draft bytes. Cost if wrong: a mis-targeted arm reads `stale` in the runner
  and is caught there (both read `sound`).
- **Carry the frozen-§5 divergence table into this record rather than a
  code change** (Task 8's review, resolved into Task 9). The declaration is
  sha-pinned and every arm sound; the recording is the deliverable. Cost if
  wrong: none against the evidence; a reader comparing §5 to the
  declaration without this table would think seven arms mis-sited.
