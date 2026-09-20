# Conformance cut 35 — URL retrieval and the acquisition operation

**Status:** discharged 2026-09-20 on the certified volume; results: `../plans/2026-09-20-conformance-cut-35-results.md`
**Design:** `../superpowers/specs/2026-09-19-url-retrieval-design.md`, approved for implementation planning 2026-09-20 at `395b550` after four reviews; implementation not yet started.
**Plan:** `../superpowers/plans/2026-09-20-url-retrieval.md`.
**Numbered after** cut 34 under roadmap concurrency rule 1. No other worktree or branch held a cut numbered 35–39 at freeze; cut 34 is the highest discharged runner.

## 1. What this cut is

Cut 10 landed verified holdings store-side and deferred the URL arm whole:
`holdings.records.url_locator` refuses with `UrlLocatorDeferred`, the
locator union has one arm, the holdings intent payload and the reducer's
location key spell only `store`, and no act dereferences a network
location. The act-report design gave every boundary operation a terminal
record and named `acquisition` as an operation kind, but no boundary opens
one: today `import`, `move`, `consolidate`, `run-attempt` and
`corpus-write` open intents and mint reports, and nothing else does. The
empirical-observation facet already admits a `url` locator scheme and a
`retrieval` reference to an acquisition report, so a dataset can say it
was acquired while nothing can acquire one. Cut 29 made every dataset id
derive from its content identity, so a dataset declared with a locator and
no digest — the ramp's eleven — is not a record this kernel can hold: the
ramp's "declaration pin" has no stored declaration to pin.

This cut lands the `url` locator with the banked canonicalization profile
as the second arm of the locator union everywhere the first arm is
spelled; moves the survey instrument's network discipline into the kernel
as the URL dereference boundary of a pure look, behind an injectable
transport seam, with the timeout, byte ceiling and redirect bound as
explicit, recorded instrument inputs; and builds the `acquisition`
operation — one operation intent, per resource a URL look and an optional
managed materialization into the session's store, and one closing
act-report published in the same registered transaction as the dataset it
mints, whose empirical-observation facet names the report through
`retrieval`.

It reads the rows the roadmap assigns: H4's remote arm, G9's
location-is-not-the-discriminator arm at a URL, R10's "the acquisition
path records dataset provenance instead", T5's began-ness and post-stop-
skip arms, T7's same-root case, and the ride-along T1 (the raw-write
negative), T2 (the acquisition kind to success, root-selection and intent-
append failure, the second fulfillment) and T4 (the coverage projection
clause, the unfinished operation that blocks nothing, the observation-
deletion negative).

Rows that close here: H4, G9, R10, T5, T1, T4. Rows that stay partial,
each with a named remainder: T7 on its cross-root case, which the roadmap
already assigns to `cross-root-publication` (tier 3); T2 on the `audit`
and `re-check` operation kinds, which have no boundary that opens an
intent.

## 2. The boundary

The surfaces on which a sabotage may land are:

- `python/src/beliefs/holdings/records.py`, `transport.py`,
  `holdings/boundary.py`, `acquire.py`, `adapter.py`, `rules_v1/holdings.py`,
  `qualify.py`;
- `python/src/beliefs/boundary.py` (`_mint_acquisition_report`),
  `corpus.py` (`_publish_operation_report`'s plan parameter, the overlay
  validation the acquisition calls), `stored.py`
  (`holdings_observation_value`), `errors.py`, `intents/evidence.py`,
  `intents/holdings.py`, `session/writer.py` (`acquire`), `world/verify.py`;
- `python/tests/test_holdings_records.py`, `test_holdings_transport.py`,
  `test_holdings_boundary.py`, `test_holdings_acquire.py`,
  `test_holdings_reduce.py`, `test_holdings_stored.py`, `test_report.py`,
  `test_intent_evidence.py`, `test_intents_holdings.py`,
  `test_session_routes.py`, `test_session_reconcile.py`,
  `test_admission_survey.py`;
- `python/tests/acceptance/test_url_retrieval_acceptance.py`,
  `python/tests/acceptance/n2_arms_cut35.py`,
  `python/tests/acceptance/test_n2_cut35.py`, and
  `python/tools/cut35_acceptance.py`;
- this cut, the adoption ledger, roadmap, guide, README, and the holdings,
  admission-ramp, act-report, computation and world-index-holdings
  amendments.

Frozen declarations and cut bodies through cut 34 remain byte-exact.

## 3. Selection

Twenty-seven declaration units are selected and single-homed here. The
quoted row text is byte-exact from the named design at freeze.

```markdown
| **H4** | no silent act, and no laundered non-answer | an act records every outcome it established or fails, never a transient report and a dropped record / an inconclusive attempt reports through its own channel and never mints `absent` / a mutating act runs inside its intent–fulfillment ordering or fails |
```

```markdown
> **`G9`.** A dataset reaches **held** only when **every** resource its
> declaration names has a byte observation whose digest matches the digest
> recorded for it. Declaration does not promote, presence does not promote, a
> proper subset does not promote, and no API accepts an authored `held`.
```

```markdown
| **R10** | Runs begin at the most upstream held form | Attempt a run whose input is a URL or an accession rather than a held dataset; assert refusal and that the acquisition path records dataset provenance instead. **Negative:** assert no fallback synthesizes a dataset entity from the URL |
```

```markdown
| **T1** | Only the boundary mints an act-report | Attempt to author one through every construction path — direct authoring, and any API taking report fields as input; assert no such path exists. Explicitly import another observer's report and assert it enters **structurally validated, not operation-authenticated, attributed, and inert** — nothing derivable exists to recompute, and no validation state is written. **Negative:** raw-write a self-consistent report; assert it is not detected on read, and that an audit detects it **only with the tamper log implemented and a valid anchored observer set** — otherwise the raw write remains undetectable, and the design text claims no more |
| **T2** | One started operation, one intent, one terminal record — and no act precedes the intent | Run each operation kind to success; assert exactly one qualifying fulfillment: the `run` where one is minted, the act-report otherwise. **Positive:** a post-intent attempt that mints no run closes through **exactly one** qualifying act-report. Attempt a second fulfilling registration on one intent → **malformed**, the log's rule as built. Make root selection fail, then the intent append fail; assert in each case **no act began** — no request issued, no lease taken, **no record minted** (an `event_token` generated in memory and carried by no intent and no record is not a mint). **Negative (a):** a missing-spec run request refuses **pre-intent**; assert a surviving boundary publishes an *unfulfilling* act-report, that it fulfills nothing, and that a crash there leaves no trace. **Negative (b):** a complete non-conforming execution mints a **run**, never an act-report. **Negative (c):** a dataset-production attempt opens the **operation intent** — assert the assessment-run intent cannot be spelled without a `spec_identity` |
| **T4** | The report layer is inert by type | Add and remove reports and entries; assert the belief digest, admission, eligibility, and the coverage projection are byte-unchanged. Assert an **unfinished operation blocks nothing**: a location with no unmatched holdings intent projects normally while its operation's intent stands unmatched. **Negative:** delete an observation a report references; assert exactly the record-layer consequences occur — the active set and projection move as the holdings design says — while the report is unchanged and confers no protection |
| **T5** | Outcome vocabularies are reserved per act kind | Attempt `byte-locator-untested` on a managed-mutation, record-import, and subject-evaluation entry; assert each is unspellable. Attempt it on a locator act whose request **began**; assert refusal — that is `retrieval-failed`'s territory. Assert a preflight refusal and a deliberate post-stop skip both spell `byte-locator-untested` with distinct reasons. Assert no entry outcome constructs an observation — reports reference products and never mint them |
| **T7** | A successful acquisition's provenance reference and report publish together, and no identity cycle exists | Assert no path publishes the dataset's provenance reference and the act-report in separate transactions or separate roots — the attempt is refused, never half-ordered. Mutate the report; assert the dataset **address** is byte-unchanged (the §6.2 basis excludes provenance) while the dataset's record bytes — its node-content identity — and the corpus-state identity **move** with the reference |
```

Spec §11.2's unit table, verbatim:

| unit | row | what it reads |
|---|---|---|
| H4-a | H4 | an established remote `found` publishes; a publication failure after `Retrieved` raises and the chain carries the unmatched re-check intent, no transient report |
| H4-b | H4 | timeout, ceiling, `404`, `500`, refused hop, unpinnable context: each mints nothing, never `absent`, carries no digest, and the standing URL observation's identity is unchanged |
| G9-a | G9 | `found` at a URL, no store copy → `held` via `dataset_observations` and `admission_state`; the URL then fails → still `held` |
| R10-a | R10 | the minted dataset's facet carries `locator`, `attested_by` = actor, `retrieval` → an `acquisition` report whose entry references the observation; `validity_refusal` is `None` |
| T5-a | T5 | a `Failed` retrieval spells `retrieval-failed`; the sabotage classifying it untested fails |
| T5-b | T5 | a preflight refusal and a post-stop skip: both `byte-locator-untested`, reasons distinct |
| T5-c | T5 | the report references observations the acts published; a report whose ref resolves to no observation refuses at the close and the operation reads unfinished |
| T7-a | T7 | dataset and report in one registered transaction (one chain registration carries both paths); a wrong-root writer refuses before the intent |
| T7-b | T7 | two roots, same bytes: equal dataset ids, distinct node-content and corpus-state identities |
| T1-a | T1 | a raw-written self-consistent report: readable, `corpus_check` silent; log verification under an anchored observer set refutes; under none, unresolvable |
| T2-a | T2 | acquisition to success: one intent, one qualifying report, `closed`, intent chain position before every act |
| T2-b | T2 | store-less session with materialization, and a port-less writer: no request, no intent, no record |
| T2-c | T2 | intent append refused by the port: no request, no record |
| T2-d | T2 | a second `execute_fulfilling` on the operation intent is refused by the coordinator; a raw second fulfillment reads `MalformedView` with kind `duplicate-fulfillment` |
| T4-a | T4 | reports added and removed: reducer outputs byte-identical; an unmatched acquisition intent blocks nothing |
| T4-b | T4 | deleting a referenced URL observation moves the active set; the report is byte-unchanged and `cite` resolves |
| BI-1 | — | the canonicalization table through the durable path: two spellings of one URL are one location in the reducer |
| BI-2 | — | a presigned hop and a token-bearing-hostname hop: the query, the token and the host occur in no published record, no entry, no reason and no exception text; the entry reads `retrieval-failed` with ordinal and category |
| BI-3 | — | the pinned connection dials the validated address with name validation; an unpinnable context issues no request |
| BI-4 | — | the ceiling ends the stream; no digest is finalized or published for the partial body; the bound is named on the entry |
| BI-5 | — | an expectation mismatch: `found(D')` with `expected = D`, no dataset, the adapter reports `mismatch` |
| BI-6 | — | an already-held address: no second dataset, observation and report published, the old `retrieval` unchanged |
| BI-7 | — | a crash between the URL look's intent and its publication: the reducer reports no blocked entry for the URL location |
| BI-8 | — | no lock across the request |
| BI-9 | — | the successor rule: the old binding's receipt still validates where held; the new fixture reduces |
| BI-10 | — | a URL re-check intent and its fulfilling observation decode through `intents/evidence.py` and the generated helper; the reduction matches them and `reconcile` reports nothing |
| BI-11 | — | the materialization classification: a production-seam store refusal (a read-only replica, `ProjectApprovalRefused` cause) on the first and on the last resource each returns a stopped outcome with no dataset; a publication failure after a committed materialization propagates `ExecutionError` and the operation reads unfinished; a terminal session failure propagates and is never a stop; **negative:** an unexpected engine failure (`ExecutionError` with `applied=None` from a `RuntimeError` cause) propagates and the operation reads unfinished, never a stop |

## 4. Accounting

**27 declaration units**, sixteen against rows and eleven boundary
invariants; H4, G9, R10, T5, T1 and T4 close; T2 stays partial on the
`audit` and `re-check` operation kinds; T7 stays partial on its
cross-root case.

## 5. N2 and acceptance obligations

Acceptance has one arm per declaration unit. Each N2 sabotage has a
byte-exact `before` block copied from the tree at freeze and parsed after
mutation.

| arm | module | sabotage | check |
|---|---|---|---|
| H4-a | `holdings/boundary.py` | `look`'s publication failure is caught and an `InconclusiveLook` returned | H4-a |
| H4-b | `holdings/boundary.py` | a `Failed` retrieval publishes `Absent()` | H4-b |
| G9-a | `holdings/adapter.py` | a head whose location key starts with `url:` never joins | G9-a |
| R10-a | `holdings/acquire.py` | the dataset's `retrieval` member is omitted | R10-a |
| T5-a | `holdings/boundary.py` | `Failed` → `InconclusiveLook("byte-locator-untested", ...)` | T5-a |
| T5-b | `holdings/acquire.py` | the skip reason becomes the preflight reason | T5-b |
| T5-c | `holdings/acquire.py` | the close does not check that each `PublishedObservation` ref resolves | T5-c |
| T7-a | `holdings/acquire.py` | the dataset publishes by `writer._add_locked` before the report's transaction | T7-a |
| T7-b | `stored.py` | `dataset_node` folds `retrieval` into the address | T7-b |
| T1-a | `world/verify.py` | `registered_surface_paths` excludes paths under `act-report/` from the corpus surface, so replay never sees the raw-created report | T1-a |
| T2-a | `holdings/acquire.py` | the first look runs before `_append_operation_intent` | T2-a |
| T2-b | `holdings/acquire.py` | the port check moves after the first look | T2-b |
| T2-c | `holdings/acquire.py` | an append failure is caught and the looks proceed | T2-c |
| T2-d | `holdings/acquire.py` | the close publishes the report twice under the one intent, swallowing the refusal | T2-d |
| T4-a | `holdings/rules_v1/holdings.py` | an unmatched `acquisition` operation intent adds an `unsettled` reason | T4-a |
| T4-b | `holdings/rules_v1/holdings.py` | a head referenced by a report's entry is retained after deletion (the rule reads reports) | T4-b |
| BI-1 | `holdings/records.py` | host case is preserved | BI-1 |
| BI-2 | `holdings/transport.py` | the refused-hop reason carries the hop's host | BI-2 |
| BI-3 | `holdings/transport.py` | `connect` dials the host name, not the pinned address | BI-3 |
| BI-4 | `holdings/transport.py` | the ceiling returns `Retrieved` with the running hash's digest | BI-4 |
| BI-5 | `holdings/acquire.py` | a mismatch still mints the dataset from the found digest | BI-5 |
| BI-6 | `holdings/acquire.py` | an existing address is revised to the new report | BI-6 |
| BI-7 | `holdings/boundary.py` | the URL look's intent kind becomes `write` | BI-7 |
| BI-8 | `holdings/acquire.py` | `retrieve` runs under `_operation_lock_for(root)` | BI-8 |
| BI-9 | `holdings/qualify.py` | `_location` returns `None` for the `url` arm (the generated copy is what the rule bundle reads) | BI-9 |
| BI-10 | `intents/evidence.py` | the location key reverts to the store fields | BI-10 |
| BI-11a | `holdings/boundary.py` | the `StoreWriteRefused` wrap widens from the `store_write` call to the whole of `write` | BI-11 (the publication failure reads as a stop; its fixture raises `ExecutionError(applied=0)` from a `PreconditionRefused` cause, so only the phase, not the predicate, keeps it out) |
| BI-11b | `holdings/boundary.py` | `store_refusal` returns `True` for every `ExecutionError` | BI-11 (the unexpected engine failure reads as a stop) |

Both directions are required: the check passes on the real tree and fails
under sabotage. The runner uses
`PREFIX_RUNNERS = ("cut34_acceptance.py",)` and carries
`PHASE_MODULES = ("test_url_retrieval_acceptance.py", "test_n2_cut35.py")`.

## 6. Second reader

Four things to check: that the close's lock order is session then root
and the view is rebuilt under it before any ref resolves; that BI-2's
assertions read every published byte of the observer root and the
exception text, not only the entry; that T5-a's classification is read
from the transport's phase value and never from a message; that BI-11's
production refusal is a real `ExecutionError` from `run_transaction` with
a `ProjectApprovalRefused` cause.

## 7. Limitations

1. **A URL never mints `absent`**: remote disappearance is observable only
   as repeated inconclusive attempts.
2. **Credential-free authoring of the declared URL is the caller's
   obligation**; the hop rule (decision 6) closes only the server-chosen
   half.
3. **Internationalized host names refuse at construction.** IDNA is a
   canonicalization amendment; filed as an idea.
4. **The materialization buffers the whole resource** once, bounded by the
   ceiling; a streaming store seam is an atoms request nobody has made.
5. **No retry, no proxy, no authentication.**
6. **A look-only acquisition through the session still needs a bound
   store**, because `holdings_context` does; `acquire` over a hand-built
   `ActContext` has the same shape. A store-less look route is not
   designed here.
7. **T2 stays partial on `audit` and `re-check`**; `act-report-remainder`
   keeps the two as its remainder.
8. **The reducer's rule identity moves**; receipts under the old binding
   validate only where the old implementation is held.
9. **A raw-written `url` intent with a non-canonical spelling** is an
   unmatched intent forever; the audit reports nothing about it, on the
   same grounds cut 25 gave for sources.
