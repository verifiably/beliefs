# URL retrieval — the `url` locator, the network boundary and the acquisition operation

**Date:** 2026-09-19
**Status:** draft, under review
**Boundary:** `url-retrieval` (`beliefs-d13fe8`), tier 1 off the path, row 1 after cut 34; carries `act-report-remainder` (T1, T2, T4) as the roadmap's ride-along
**Lane:** `acquisition`, worktree `.worktrees/url-retrieval`, branch `url-retrieval`
**Sources:** `../../designs/2026-08-10-verified-holdings-record-design.md` (§2 the `url` locator profile, §3 the two act shapes, the dereference boundary and the network discipline, §4, §5, §6 H1–H4, §7 items 4 and 8),
`../../designs/2026-08-24-world-index-holdings-design.md` (§1 item 1 the named deferral, §3, §4, §5),
`../../designs/2026-08-11-act-report-design.md` (§2 the record and the entry vocabularies, §3 the completion discipline, §4 provenance, T1–T8),
`../../designs/2026-08-09-admission-ramp-design.md` (§4 the instrument's network discipline, §6.6 the unpinned locator),
`../../designs/2026-08-02-computation-reproducibility-design.md` (§4.7 the acquisition provenance record, R10),
`../../designs/2026-09-05-facet-contracts-design.md` (§5.2, §6 the empirical-observation contract),
`2026-09-14-world-resolution-slice-5-design.md` (decisions 2–5: dataset ids derive from content identity, one record per byte set),
`../../designs/2026-09-09-session-routes-design.md` (§3.3 `holdings_context`, §4 the ledgered routes),
`../../designs/2026-08-24-conformance-cut-10.md` and `../../plans/2026-08-24-conformance-cut-10-results.md` (the labeled URL deferral, H4's store instantiation, G9's independence arm),
`../../designs/2026-08-11-conformance-cut-3.md` §4.2, `../../designs/2026-09-03-conformance-cut-16.md` §T2 and `../../designs/2026-09-04-conformance-cut-18.md` §4 (the T-row arm splits this slice inherits),
`../../plans/2026-08-29-implementation-roadmap.md` (tier 1 off-path row 1, Appendix B, concurrency rules)
**Measured against:** `main` at `728a178` (code unchanged since `3873d16`, the cut 34 verification commit)

## 1. What this slice is

Cut 10 landed verified holdings **store-side** and deferred the URL arm whole:
`holdings.records.url_locator` refuses with `UrlLocatorDeferred`, the
locator union has one arm, the holdings intent payload and the reducer's
location key spell only `store`, and no act dereferences a network
location. The act-report design gave every boundary operation a terminal
record and named `acquisition` as an operation kind, but no boundary opens
one: today `import`, `move`, `consolidate`, `run-attempt` and
`corpus-write` open intents and mint reports, and nothing else does. The
empirical-observation facet already admits a `url` locator scheme and a
`retrieval` reference to an acquisition report (facet-contracts §6), so a
dataset can *say* it was acquired while nothing can acquire one. Cut 29
made every dataset id derive from its content identity, so a dataset
declared with a locator and no digest — the ramp's eleven — is not a
record this kernel can hold: the ramp's "declaration pin" has no stored
declaration to pin.

The admission ramp's survey instrument (`python/tools/survey_admission.py`)
already carries the network discipline the holdings design inherits — the
https-only scheme set, the non-public-address refusal, per-hop redirect
revalidation, the pinned validated resolution with hostname and TLS
validation intact, the fail-closed rule, the timeout and the streaming
byte ceiling — as a hand-run tool that mints no world record.

This slice:

1. lands the **`url` locator** with the banked canonicalization profile
   (holdings §2), as the second arm of the locator union everywhere the
   first arm is spelled — the record, its stored codec, the holdings
   intent payload, the qualification helper and the fixture-bound reducer;
2. moves the survey instrument's **network discipline into the kernel** as
   the URL dereference boundary of a pure look, behind an injectable
   transport seam, with the timeout, byte ceiling and redirect bound as
   explicit, recorded instrument inputs;
3. builds the **`acquisition` operation**: one operation intent, per
   resource a URL look and an optional managed materialization into the
   session's store, and one closing act-report published **in the same
   registered transaction as the dataset it mints**, whose
   empirical-observation facet names the report through `retrieval`;
4. reads the rows the roadmap assigns: **H4**'s remote arm, **G9**'s
   location-is-not-the-discriminator arm at a URL, **R10**'s "the
   acquisition path records dataset provenance instead", **T5**'s
   began-ness and post-stop-skip arms, **T7**'s same-root case, and the
   ride-along **T1** (the raw-write negative), **T2** (the acquisition
   kind to success, root-selection and intent-append failure, the second
   fulfillment) and **T4** (the coverage projection clause, the unfinished
   operation that blocks nothing, the observation-deletion negative).

Rows that close here: H4, G9, R10, T5, T1, T4. Rows that stay partial,
each with a named remainder: **T7** on its cross-root case, which the
roadmap already assigns to `cross-root-publication` (tier 3); **T2** on
the `audit` and `re-check` operation kinds, which have no boundary that
opens an intent (decision 12). The roadmap's Appendix B says the
ride-along closes T2 in full; the tree says it cannot, and this document
corrects the roadmap at the results record rather than reading a row
closed over kinds nothing ran.

The measurement this slice serves: the natural-systems v2 Dryad pilot
(`ns-006fda`) acquires a seeded sample of public datasets by URL. Dryad's
file downloads redirect to presigned object-store URLs; the pilot bounds
each record at 200 MiB and forbids inferring a numeric time axis from
anything but the bytes. Every one of those facts lands on a decision below.

## 2. Decisions

1. **The `url` locator is constructed canonical, under the banked profile,
   with `http` and `https` the only schemes it spells.** `url_locator(str)`
   returns a `UrlLocator` whose one field is the canonical absolute URL:
   scheme and host lowercased; the default port (`443` for `https`, `80`
   for `http`) elided and any other port kept; an empty path written `/`;
   dot-segments removed (RFC 3986 §5.2.4); percent-encoding normalized in
   the **path only** — uppercase hex, unreserved characters (`ALPHA`,
   `DIGIT`, `-`, `.`, `_`, `~`) decoded; the query preserved byte-exact
   including the presence of an empty `?`; a fragment or userinfo
   **refused** at construction (`MalformedRecord`), as are a scheme outside
   the two, an empty host, a non-ASCII byte anywhere, whitespace, and a
   control character. The profile is defined for exactly the two schemes
   because default-port elision is: a third scheme arrives by amendment
   with its own rule (holdings §7 item 4). `http` is constructible so that
   a `byte-locator-untested` entry can name its subject; the boundary
   refuses it at preflight (decision 6). Canonical key: `url:<canonical>`;
   facet encoding `{"type": "url", "url": <canonical>}`. Equality is field
   equality of the canonical form, so H2's per-location walk and the
   reducer's location key are byte equality. *Rejected:* storing the
   caller's spelling and canonicalizing at comparison — the reducer is a
   pure rule over stored bytes and two spellings of one location would be
   two locations in it. *Rejected:* internationalized host names — IDNA is
   a canonicalization rule of its own; a non-ASCII host refuses at
   construction and is a limitation (§13).

2. **The URL look is a pure dereference of holdings §3's first shape, and
   it appends a `re-check` holdings intent naming its URL location before
   the request.** The banked text says a URL look is intent-free because
   no chain position orders a network read and no URL location can be
   unsettled. Both stay true: the intent's kind is `re-check`, which the
   reducer never counts toward `unsettled`, and an unmatched one reads as a
   look that never became a finding — the act's failure, never the
   record's (H4). What the intent buys is the **registration**: every
   committed write in this kernel fulfills an intent — the store seam has
   only `publish_fulfilling`, and the writer session's `LedgeredPort`
   refuses a non-fulfilling `execute` — so an observation with no intent
   has no way to publish. *Rejected:* publishing the URL observation inside
   the operation's closing transaction — it would make every look wait for
   the acquisition, which holdings §3 forbids, and lose an established
   finding on a crash before the close. The holdings design §3 gains a
   dated note (§14). The intent payload's `location` gains the `url` arm;
   `qualify.decode_holdings_intent` decodes both arms.

3. **An acquisition is one operation over a request of one or more
   resources, opened after root selection and permit checks and before any
   request, closed by one act-report in the observer root.** The request
   is a value: a dataset `title`; the dataset's `locator` — the
   empirical-observation facet's value, any scheme the facet admits
   (`url:`, `accession:`, `instrument:`), naming the most upstream form
   outside the held boundary (for a Dryad record, the dataset's own URL or
   DOI); the **retrieval bounds** (decision 7); and one `ResourceRequest`
   per declared resource — `name`, the retrieval `url` (a `UrlLocator`),
   an optional `expected` digest, and an optional `materialize`
   destination (a `StoreLocator` in the bound store). The operation runs:
   (a) **checks before effects**: `corpus-write` on `dataset` and
   `act-report` and `holdings` on `holdings-observation` are required of
   the bound authority; the writer's root must be the act context's
   observer root; the writer must have an operation port; a request that
   materializes anything needs the store bound; a malformed request
   refuses — all before any intent, `AcquisitionRefused(WriteRefused)`,
   nothing appended, nothing minted (T2's root-selection arm); (b) the
   **operation intent** `acquisition` is appended in the observer root
   (T2: no act precedes it); (c) per resource in request order, the URL
   look (decision 2, decisions 5–9), then, where `materialize` names a
   destination, the managed write (decision 10); (d) the **close**: the
   dataset is minted when decision 4's condition holds, and the closing
   transaction publishes `[dataset?, act-report]` fulfilling the operation
   intent. The dataset's facet `retrieval` names the report's node id; the
   report's `DeclarationPinEntry` names the dataset's address as subject
   and its id as the pinned declaration. No identity cycle: the dataset's
   **address** is the basis projection over its digests, computable before
   the report exists and excluding provenance; only the dataset's
   node-content identity carries the reference (T7). Dataset validation
   runs over an overlay view carrying the report as an arriving member —
   the `_ImportView` shape import already uses — so `retrieval` resolves
   to an `acquisition` report at the write boundary exactly as
   facet-contracts §5.2 step 5 requires. The dataset's `attested_by` is the
   bound actor (§5.3 there). *Rejected:* a dataset per resource — a Dryad
   record is one dataset with several files, and the address is the fold
   over every declared digest.

4. **The dataset mints iff every look established `found` and every
   supplied expectation equals its look's digest; otherwise the operation
   still closes, with the entries recording what happened, and mints no
   dataset.** An inconclusive look, an expectation mismatch, or a
   materialization refusal leaves the report to say so; `closed` is the
   operation's completion reading either way, because the operator
   survived and reported. **Unfinished** is reserved for the operator that
   did not (act-report §3.3). *Rejected:* refusing the acquisition on a
   mismatch — G9 requires a wrong-bytes retrieval to be reported as a
   mismatch, not as a failure to retrieve, and the observation carrying
   `expected` is exactly that channel; refusing would discard an
   established finding, which H4 forbids.

5. **The cooperative stop.** After the first resource that did not
   complete — a look that established nothing (a preflight refusal, a
   transport failure, a bound exceeded, a non-200 status, a refused hop) or
   a materialization the store refused (decision 10) — the remaining
   resources are **skipped**: no intent appended, no request issued, and
   each records `byte-locator-untested` with reason `skipped-after-stop`,
   distinct from a preflight refusal's reason (T5's two-reasons arm). The
   dataset cannot mint without every resource, so continuing would spend
   requests to establish findings the operation cannot use; a caller who
   wants them runs a second acquisition. *Rejected:* looking at every resource
   regardless — more evidence per run, but it makes the skip arm
   unconstructible and the pilot's per-record budget harder to hold.

6. **Every redirect hop is revalidated by the same preflight, and no hop
   URL ever enters a record, a report entry, an error or an exception
   message.** The presigned object-store URL a repository redirects to
   carries a signature in its query: bytes the holdings design says
   structure cannot classify, and which the caller — who authored only the
   declared URL — never had the chance to keep credential-free. The same
   holds for a **token-bearing hostname**, which the holdings design names
   beside the signed query as structure cannot classify. So the
   observation's location is the **declared canonical URL**, the entry's
   subject is the same, and a hop is named by its **ordinal and a fixed
   refusal category** only — never its bytes, never its host: the
   categories are the closed set `scheme`, `no-host`, `unresolvable`,
   `non-public-address`, `unpinnable`, and a refused hop reads
   `retrieval-failed` with reason `redirect hop 2 refused: non-public-
   address`. It is `retrieval-failed`, not `byte-locator-untested`, because
   the declared URL's request **began** — T5 reserves `byte-locator-
   untested` for a locator act where no request or dereference began, and
   only the declared URL's own preflight and the post-stop skip are that
   (decision 5). A redirect chain longer than `max_redirects` reads
   `retrieval-failed` with the bound named. Preflight per hop: scheme
   `https` (an `http` locator or hop is refused here, not at construction);
   the host resolves to at least one address and every address is global
   (`ipaddress.is_global`); a `Location` is joined against the hop it came
   from before it is revalidated, in memory only. *Rejected:* recording the
   final resolved URL as a second location — it names an access grant, not
   a location, and would put the grant into immutable content. *Rejected:*
   naming the refused hop's host — a hostname can carry the grant.

7. **The retrieval bounds are explicit inputs of every look and are
   recorded on every locator entry.** `RetrievalBounds(timeout_seconds,
   max_bytes, max_redirects)` is a required member of the request; the
   boundary has no default. Each `LocatorEntry.instrument_inputs` carries
   the three as string pairs in a fixed order, beside whatever outcome
   they caused. The timeout bounds the connect and every read; the ceiling
   is streaming — the hash is updated as chunks arrive, the stream ends at
   the first byte past `max_bytes`, and the running hash is **discarded,
   never finalized**: an incomplete body — over the ceiling, short or long
   against `Content-Length`, or cut by a transport failure — yields a
   `Failed` that carries no digest, mints nothing, and leaves no scratch
   file; the entry reads `retrieval-failed` naming the ceiling or the
   cause. *Rejected:* kernel defaults — the ramp records that
   its own 512 MB ceiling misreported its three largest resources and
   forbids promoting an instrument choice into the profile.

8. **The bytes on the wire are the resource's bytes, or the look fails.**
   The request is the ramp's `GET`, and it transmits the canonical locator
   **faithfully**: the request target is the canonical path and query
   byte-exact — an empty `?` included — and the `Host` header is the
   canonical authority, the host plus `:port` whenever the port is not the
   scheme's default; the survey instrument dropped an empty query and
   omitted the port, and the kernel does neither. It sends
   `Accept-Encoding: identity`; a response whose `Content-Encoding` is present and not
   `identity` is `retrieval-failed` (the hashed stream would not be the
   resource), as is a body shorter or longer than a declared
   `Content-Length`, a status other than `200` (a `404` included — the
   holdings design's rule that a URL never mints `absent` stands whole),
   and a redirect without a `Location`. Only a complete `200` body hashed
   end to end establishes `found`. The bytes stream to a **scratch file**
   under a caller-named scratch root that refuses the observer root, the
   store root and every descendant of either, hashed as they arrive; the
   look deletes its own file when its resource is done, success or not.
   *Rejected:* an in-memory buffer — it costs the same peak memory (the
   store seam takes `bytes`) and loses the path a streaming store seam
   would later take.

9. **The transport is a seam.** `UrlSeam(resolve, connect)`: `resolve(host,
   port) -> addresses` and `connect(approved, timeout) ->
   HTTPSConnection`. The production seam is the survey instrument's,
   moved: the system resolver, and a connection that dials the **validated
   address** while keeping `server_hostname` as the name so SNI and
   certificate verification run against it; a context that cannot pin
   with `check_hostname` and `CERT_REQUIRED` intact raises inside the seam
   and the look reads `byte-locator-untested` with that reason and issues
   no request — the fail-closed rule, inherited whole. Unit and acceptance
   tests inject a seam whose resolver answers a global address and whose
   connection dials an in-process TLS server or a scripted fake; **no test
   reaches the network**, and the acceptance suite on the certified tuple
   asserts it (the seam counts requests). Retrieval is
   **unauthenticated-only**: the seam offers no header, token or grant
   parameter, and typed grants stay holdings §7 item 8's amendment.

10. **Materialization is the managed `write` act, per resource, at a
    caller-named destination, with `expected` set to the look's digest.**
    The write appends its own holdings intent, runs the store transaction,
    and records the destination's post-state hash from the engine's
    verified final surface — never the stream's digest (H1). Atoms' commit
    verification makes a destination whose post-state differs from the
    written bytes uncommittable, so a `found(D'')` with `expected = D` at
    the store location is unconstructible from this path. **A store
    refusal is classified inside `write`, by phase.** The production seam
    maps every engine refusal — approval, spec validation, precondition,
    capability, pending, halted, protocol — to `nodes.core.errors
    .ExecutionError`, which is not a `ScienceError`; and the same type is
    raised by the intent append and by the observation's publication, so
    neither the exception's class nor its base says which phase failed.
    `write` therefore wraps **exactly the `seam.store_write` call** and
    re-raises an `ExecutionError` from it as `StoreWriteRefused(ScienceError)`,
    carrying the location and the engine's message, with the cause chained.
    Nothing else in `write` is wrapped: an `ExecutionError` from `_append`
    (the intent) or from `_publish_record` (the observation, after a
    committed store transaction) propagates as itself — an established
    post-state that cannot be recorded fails loudly (H4) and leaves the
    location unsettled under its unmatched mutating intent (H2) — and a
    `SessionProtocolError` or `SessionLedgerFailed` from the ledgered
    seam's guard propagates as itself from whichever phase raised it,
    because a session that is no longer current or a ledger that cannot be
    written is terminal, not a refusal. `delete` and `move` are unchanged:
    no caller of theirs has a stop to make. `acquire` catches exactly
    `StoreWriteRefused` and treats it as a **stop** (decision 5): the
    resource's `ManagedMutationEntry` is absent and its look's entry
    present — the store leg's story is the record layer's, and the report
    never restates what the chain proves (act-report §2.2) — every later
    resource is skipped, the operation **closes**, no dataset mints, and
    the outcome's `stop` names the resource, the phase `materialize` and
    the refusal's message (§6). A stop forbids the mint whatever its phase:
    the request asked for materialized bytes, and a dataset minted without
    them would read `held` on the URL observation alone while the caller
    learns of the missing copy only from the report. Every other exception
    propagates unchanged and the operation stays unfinished under its
    intent (§4's raise rule). *Rejected:* catching `ScienceError` in
    `acquire` — it would miss every real refusal (an `ExecutionError`) and
    swallow the two terminal session failures. *Rejected:* catching
    `ExecutionError` around the whole of `write` — a publication failure
    after a committed materialization would read as a stop, and the chain's
    unmatched intent would then disagree with a report that says the
    operator survived and knew. An existing file at the destination is replaced
    (the seam's `ReplaceFile` effect), the prior observation superseded
    only if the caller supplied it as standing. *Rejected:* a kernel-chosen
    content-addressed layout — the store's namespace is the caller's
    (the reproduction names its own paths), and a layout ruling is not
    this slice's.

11. **One record per byte set holds: when the derived address is already
    held in the observer root, the acquisition mints no dataset and pins
    nothing, while its observations and its report publish.** The report
    then carries no `DeclarationPinEntry`; the existing dataset's
    `retrieval` keeps naming the operation that first minted it — that
    reference is that record's provenance, and rewriting it would edit
    evidence (T8). The second acquisition is corroboration, discoverable
    by digest through the coverage projection and by the report's entries.
    *Rejected:* `revise` of the existing dataset to the new report.

12. **T2's "run each operation kind to success" is read for the kinds with
    a boundary; `audit` and `re-check` have none and T2 stays partial on
    them.** Cuts 3, 5, 16 and 18 read `run-attempt`, `import`, `move`,
    `consolidate` and `corpus-write`; this cut reads `acquisition`. An
    `audit` operation is the boundary wrapper act-report §4 describes —
    the read-only evaluator's findings recorded as `SubjectEvaluationEntry`
    outcomes under a wrapper's intent — and a `re-check` operation is the
    same wrapper over holdings re-checks; neither exists, and both sit on
    `audit.py` and `world/audit.py`, the world-read lane's surface. Building
    them here would open a second surface inside a lane that already spans
    `holdings/`, `corpus.py` and the session. `act-report-remainder`
    therefore does not leave the ledger table: it stays with T2's two
    kinds as its remainder, off the path, and the roadmap's Appendix B and
    ride-along row are corrected at the results record. *Rejected:* thin
    wrappers in this slice.

13. **T2's second-fulfillment clause reads through the engine's rule as
    built.** Atoms' coordinator refuses a registration whose `fulfills`
    an earlier committed registration already fulfills, and its chain
    inspector reports a settlement committing a second fulfillment as
    malformed — the beliefs chain reader carries that defect as
    `MalformedView` with kind `duplicate-fulfillment`, one member of the
    closed taxonomy in `world/logmodel.py`. The arm: after a successful
    acquisition, a second `execute_fulfilling` naming the same operation
    intent is refused; a raw-written second fulfillment reads
    `duplicate-fulfillment` through the chain view and the operation's
    completion is undecidable from a malformed chain (the reduction never
    runs over one).

14. **The holdings reducer gains the `url` location arm; its implementation
    identity moves, and its rule identity moves with the new fixture.**
    One reducer over one record kind: a second bundle for URL-bearing
    coverages would let a coverage reduce under a rule blind to half its
    records, H3's second arm reopened. The rules store is create-only, so
    every earlier receipt stays `validated` wherever its binding is still
    held, and `unresolvable` — never `refuted` — where it is not.
    `qualify.py` and `rules_v1/holdings.py` change together (the bundle
    concatenates them); the edits are placed to leave cut 10's five pinned
    lines in `rules_v1/holdings.py` byte-intact where they can be, and any
    pin a change moves is re-targeted in `test_n2_cut10.py`'s live table
    (§11.5).

15. **No lock is held across a network request.** The look takes the
    corpus lock to append its intent and again to publish; the request
    runs between them with nothing held. The session route is a multi-act
    route on the pattern of `holdings_context`, not one `_act`: the
    ledgered seam and port record every commit, and the invocation's
    currency is checked at each. *Rejected:* wrapping the acquisition in
    `ScopedWriter._act` — it would hold the root's operation lock across
    the network for every other writer.

16. **`UrlLocatorDeferred` is deleted, not retained.** The error named a
    deferral that ends here; keeping it would be a compatibility layer
    with no caller. The frozen test that imports it is edited to the
    successor contract, as cuts 31–33 edited frozen modules, and cut 10's
    J3 arm is re-targeted in the live guard (§11.5) to a construction
    refusal the successor keeps — userinfo — so the arm's assertion
    ("construction refuses what it must") keeps a live check. The frozen
    cut-10 document and its declaration file are not touched.

## 3. The locator (`holdings/records.py`)

```
UrlLocator(url: str)            # canonical absolute URL, decision 1
  .canonical() -> "url:" + url
url_locator(spelling: str) -> UrlLocator      # canonicalize or refuse
Locator = StoreLocator | UrlLocator
HoldingsObservation.location: Locator
```

`holdings_observation(...)` accepts either arm; `supersedes` still requires
every predecessor at the same canonical location. `facet()` encodes the
`url` arm as decision 1 states. `stored.holdings_observation_value` decodes
both arms and refuses a location dict whose `type` is neither, or whose
key set is not exactly the arm's. `ALGORITHM_WIDTHS`, `Found`, `Absent`,
`expected`'s same-algorithm rule and `observed_at`'s encoding are
unchanged. A `url` location with an `absent` outcome is **refused at
construction**: no act can establish it (holdings §2), so the record layer
refuses to spell it rather than trusting every act to know.

The canonicalization is a pure function with a table-driven test (§11.1):
one row per profile clause, each with the accepted spelling, the canonical
form, and the spelling that must be refused.

## 4. The transport (`holdings/transport.py`)

The survey instrument's `preflight`, `Approved`, `Refused`,
`PinnedHTTPSConnection`, `pinned_connection`, `PinningUnavailable` and the
streaming fetch move here, renamed for the kernel and made total over the
seam:

```
RetrievalBounds(timeout_seconds: float, max_bytes: int, max_redirects: int)
UrlSeam(resolve: Resolver, connect: ConnectionFactory)
url_seam() -> UrlSeam                        # production: system resolver + pinned TLS

retrieve(locator: UrlLocator, bounds, seam, scratch: Path) -> Retrieved | NotAttempted | Failed
  Retrieved(digest: str, size: int, path: Path)   # scratch file, caller deletes
  NotAttempted(reason: str)                       # -> byte-locator-untested: the declared URL's own preflight
  Failed(reason: str)                             # -> retrieval-failed: everything after the first request, refused hops included; no digest
```

The three-way result is the **phase** the look classifies from (world-index
holdings §4.1's rule for the store command, applied to the network): a
refusal before any request is `NotAttempted`; a request that was made and
did not yield the complete bytes is `Failed`; the look never infers the
class from an exception type or message. `retrieve` never raises for a
transport, resolution, status or bound condition; a programming or
environment failure raises, and the look aborts loudly, minting nothing
and filing no entry — the durable unmatched re-check intent marks the
attempt (world-index holdings §4.1 item 3, unchanged).

Preflight per hop (decision 6); the connection (decision 9); the request
target, the `Host` authority and the body (decision 8); the scratch root
(decision 8). A `Failed` never carries a digest: the running hash of an
incomplete body is dropped with the scratch file (decision 7). The survey
instrument keeps its own copies of nothing: it imports the kernel's
transport and its tests move with the code, so the ramp's instrument and
the kernel's boundary cannot drift apart.

## 5. The URL look (`holdings/boundary.py`)

```
look(ctx: ActContext, location: UrlLocator, *, bounds, seam, scratch,
     expected: str | None = None,
     standing: tuple[HoldingsObservation, ...] = ()) -> LookResult

LookResult = PublishedLook(record, ref, retrieved: Retrieved)
           | InconclusiveLook(report: "byte-locator-untested" | "retrieval-failed", reason)
```

1. `ctx.authority.require("holdings", ("holdings-observation",))`.
2. `_append(ctx, location, "re-check")` — the holdings intent, `location`
   in the `url` arm (decision 2); `intent_payload` takes a `Locator`.
3. `retrieve(...)` with nothing held (decision 15).
4. `NotAttempted` → `InconclusiveLook("byte-locator-untested", reason)`;
   `Failed` → `InconclusiveLook("retrieval-failed", reason)`; nothing
   minted, the standing observation untouched (H4 u2, remote).
5. `Retrieved` → `holdings_observation(location, Found(digest), expected=,
   ...)` superseding the supplied standing heads, published through
   `_publish_record` fulfilling the intent; a publication failure after an
   established finding **raises** (H4 u1, remote). The scratch file is
   handed back in `PublishedLook.retrieved` for the materialization and
   deleted by the caller of `look` — the acquisition — when the resource
   is done; a standalone `look` caller owns the same duty.

`recheck`, `write`, `delete` and `move` are unchanged; `_bind` still binds
a `StoreLocator`. `ActContext` gains nothing: the scratch root and the seam
are `look`'s own parameters, because a store-only context has no use for
them.

## 6. The acquisition (`holdings/acquire.py`)

```
ResourceRequest(name, url: UrlLocator, expected: str | None, materialize: StoreLocator | None)
AcquisitionRequest(title, locator: str, resources: tuple[ResourceRequest, ...],
                   bounds: RetrievalBounds, domain_facets: Mapping | None = None)
Stop(resource: str, phase: "look" | "materialize", reason: str)
AcquisitionOutcome(report: ActReport, report_ref: str, dataset: Node | None,
                   entries: tuple[Entry, ...], stop: Stop | None)
                   # stop is None iff every resource completed; dataset is None whenever stop is set

acquire(ctx: ActContext, writer: CorpusWriter, request, *, seam: UrlSeam, scratch: Path,
        standing: Mapping[str, tuple[HoldingsObservation, ...]] = {}) -> AcquisitionOutcome
```

On `relocation.py`'s pattern — a module function over the writer's
private operation members, not a writer method — because the operation
spans the holdings boundary and the corpus writer and belongs to neither.

1. **Checks, before any effect** (decision 3a). The request is validated
   as a value: resource names unique and non-empty; `locator` a string the
   facet's `locator` type accepts (`scheme:rest`, scheme in the facet's
   declared set); `expected` canonical where given; `materialize` naming
   the bound store's identity; bounds positive. `writer.root ==
   ctx.observer_root` (T7's same-root case is the only case; a mismatch is
   `AcquisitionRefused` before the intent). `writer._operation_port` is
   not `None`. The three permit requirements. `scratch` is not under
   either root.
2. **Open**: `intent = OperationIntent("acquisition", token, actor)`;
   `intent_digest = writer._append_operation_intent(...)`; `opened_at`.
3. **Per resource**, in order, until the cooperative stop (decision 5):
   `look(...)` with the resource's `expected` and `standing.get(url key)`;
   on `PublishedLook`, `LocatorEntry(subject=url canonical,
   PublishedObservation(ref), instrument_inputs=bounds)`; then, if
   `materialize`: `write(ctx, destination, bytes, expected=look digest,
   standing=standing.get(store key))` → `ManagedMutationEntry(subject=store
   canonical, PublishedObservation(ref))`; a `StoreWriteRefused` out of
   `write` — and only that — is a stop with phase `materialize` (decision
   10): the scratch file is deleted, no mutation entry is filed, and the
   operation goes to step 4; any other exception propagates after the
   scratch file is deleted.
   On `InconclusiveLook`, the entry's outcome is `ByteLocatorUntested(
   reason)` or `RetrievalFailed(reason)` and it is a stop with phase `look`.
   After a stop, every later resource gets `ByteLocatorUntested(
   "skipped-after-stop")` with no intent and no request.
4. **Close**. `mint = stop is None and all expectations equal`. If
   `mint`: `address = dataset_address(declaration)`; if the writer's view
   already resolves `address` → no dataset (decision 11); else the dataset
   node is built by `stored.dataset_node(title, resources=[(name, digest)],
   empirical_observation={locator, attested_by: actor, retrieval:
   <report id>}, domain_facets)`. The report is minted first — its
   identity does not depend on the dataset's record bytes, only on the
   dataset's address in the pin entry's subject — so the dataset can name
   it. `_mint_acquisition_report(intent, observer, instrument, opened_at,
   closed_at, entries)` in `boundary.py`, beside the import and relocation
   minters; its entries are the sequence step 3 built, followed by
   `DeclarationPinEntry(subject=address, PinnedDeclaration(dataset id))`
   when a dataset is minted. The dataset is validated through the writer's
   ordinary `_refuse(node, view=overlay)` where `overlay` is an
   `_ImportView` over the local view plus the report node, so
   facet-contracts §5.2 steps 1–5 all run and `retrieval` resolves; the
   `provenance` flag is **not** set — the attester must be the bound
   actor. Then `writer._publish_operation_report(report, intent_digest,
   operations=[dataset op?, report op])` — the member gains a plan
   parameter, executing every op in one registered transaction fulfilling
   the operation intent (T7). The corpus lock is held for the validation
   and the publication together.

The report's `subject` per entry is the canonical locator string;
`observer` and `instrument` are the act context's; `opened_at` and
`closed_at` are the operation's own clock reads, data never read.

**Provenance, R10.** What computation §4.7 lists as the acquisition
provenance record is discharged across three records this slice makes
inseparable: the dataset's empirical-observation facet (the locator, the
attester, the reference to the report), the report (the instrument's
identity, the bounds as parameters, the retrieval outcome per resource by
reference to its observation, the timestamps), and the observations (what
the source served, hashed, at which canonical location, and what was
expected). The fetch procedure's code identity is the `instrument` string,
under the survey instrument's commit-pinning discipline; no second
provenance object is minted (act-report §4). The run boundary's refusal of
a URL input is cut 3's standing arm, cited.

## 7. The stored codec, the intent and the reducer

- `stored.holdings_observation_value` (§3) and `stored.holdings_observation_node`
  (unchanged: the facet is the record's own).
- `holdings/boundary.intent_payload(location: Locator, ...)` encodes
  `{"type": "url", "url": ...}` for the second arm.
- `intents/holdings.py` is the **shared source** of the holdings-intent
  shape; `holdings/qualify.py` is generated from it by
  `python/tools/regen_holdings_interior.py` and is never hand-edited
  (`test_intents_holdings.py` pins the header and the bytes). The change
  lands in the source and is regenerated: `_location` accepts `{"type":
  "url", "url": <str>}` and returns `"url:" + url`; it validates the value
  is a non-empty ASCII string with no fragment and no userinfo — the pure
  rule cannot import the constructor, so it re-states the two refusals the
  walk depends on and trusts construction for the rest (a non-canonical
  spelling raw-written into an intent is a location no act will ever
  fulfill, and the reducer's answer for it is `unmatched`, which is true).
  `decode_holdings_intent` therefore decodes a URL intent for the
  reduction, `intents/shapes.decode_intent`, and the session's
  `reconcile`; without the source change every URL intent would decode as
  `malformed`.
- `intents/evidence.py` builds `ObservationEvidence`'s location key from
  the record — `value.location.canonical()` — instead of the store fields
  it spells today, so a URL observation decodes to `url:<canonical>`
  evidence rather than raising `AttributeError` inside the reduction. Its
  key and the intent's `_location` key are one spelling, pinned by a test
  that decodes a URL intent and its fulfilling observation and asserts the
  reduction matches them.
- `holdings/rules_v1/holdings.py` derives the location key from the
  `type` (`store:` + id + path, or `url:` + url); every walk, coalescing
  and blocking rule is location-generic already. A new fixture
  `holdings.url.yaml` carries a coverage with one `url` head, one `store`
  head, and a `url` re-check intent with no fulfillment (a look that never
  became a finding: no `unsettled` entry).
- `holdings/adapter.dataset_observations` is location-generic; the
  `ByteObservation.location` it emits for a URL head is the canonical key.
- `holdings/project.capture_coverage` carries every record already.

## 8. The session route (`session/writer.py`)

```
ScopedWriter.acquire(request, *, instrument: str, scratch: Path,
                     seam: UrlSeam | None = None,
                     standing: Mapping[...] = {}) -> AcquisitionOutcome
```

Builds `holdings_context(instrument=...)` (so a store-less session refuses
`SessionProtocolError` before any intent — T2's root-selection arm through
the session), takes `url_seam()` when none is supplied, and calls
`acquire(ctx, self._writer, ...)` under no lock of its own (decision 15).
Every intent and every commit is ledgered by the seam and port the context
and writer already carry; `reconcile` hears the `acquisition` operation
intent through the existing operation-kind decoding and needs no new
shape. The route is the surface the natural-systems pilot drives; a
`beliefs` command over it is sub-project 4's, not this slice's.

## 9. The rows, read exactly

### 9.1 Closed here

- **H4** — remote instantiation: (u1) an established remote `found`
  publishes or the look raises; (u2) an inconclusive remote attempt —
  timeout, ceiling, non-200 including 404, transport failure, unpinnable
  context, refused hop — reports through the entry, mints nothing, never
  `absent`, never supersedes the standing URL observation; (u3) the
  materialization's mutating act runs inside its intent–fulfillment
  ordering — cut 10's H4 u3, cited, with the URL leg's re-check intent
  shown to block nothing.
- **G9** — the location arm: an active `found` at a URL location with no
  store copy reads `held` through the adapter and `admission_state`; a
  later look that fails leaves the observation active and the answer
  unchanged (R5's answer, the holdings side). The independence sabotage is
  cut 10's, cited.
- **R10** — §6's provenance paragraph; the negative is cut 3's, cited.
- **T5** — (a) `byte-locator-untested` on a locator entry whose request
  began is refused: the boundary classifies from the transport's phase,
  and a sabotage that classifies a `Failed` as untested fails the check;
  (b) a preflight refusal and a post-stop skip both spell
  `byte-locator-untested` with distinct reasons; (c) no entry outcome
  constructs an observation — the report's `PublishedObservation` refs
  resolve to observations the acts published, and a report minted with a
  ref no act published is refused at the close; the type-union arms are
  cut 3's, cited.
- **T1** — the raw-write negative: a self-consistent act-report written
  raw into a corpus is read like any record and reported by nothing at
  `corpus_check`; the log verification act over that corpus under a valid
  anchored observer set refutes; under no anchor it is unresolvable — the
  design text claims no more. The import arm is cut 5's, cited.
- **T4** — the coverage projection clause: with reports added and
  removed, the reducer's active and blocked sets are byte-identical
  (relabel: the projection was built at cut 10 and is read under T4
  here); an unmatched `acquisition` operation intent produces no blocked
  entry; the observation-deletion negative: deleting a URL observation a
  report references moves the active set exactly as the holdings design
  says, the report is byte-unchanged and `cite` still resolves its entry.

### 9.2 Partial, with the remainder named

- **T2** — read here: `acquisition` to success (one intent, one qualifying
  act-report, `completion` reads `closed`, the operation intent's chain
  position precedes every holdings intent and registration of the
  operation); root-selection failure and intent-append failure each leave
  no request, no intent, no record; the second fulfillment (decision 13).
  Remainder: the `audit` and `re-check` operation kinds (decision 12).
- **T7** — read here: the same-root case — the dataset's provenance
  reference and the report publish in one registered transaction in one
  root, and a request against a writer of another root refuses before the
  intent; two acquisitions of the same bytes in two fresh roots yield one
  dataset address and two node-content identities. Remainder: the
  cross-root case, `cross-root-publication`, tier 3, unchanged.

## 10. What this slice does not build

1. Typed retrieval grants and any authenticated retrieval (holdings §7
   item 8); the seam has no channel for grant material.
2. A `beliefs acquire` command (sub-project 4).
3. The `audit` and `re-check` operation wrappers (decision 12).
4. Retry. The pilot's "retry transient errors twice" is the caller's loop
   over whole acquisitions; each attempt is its own operation with its own
   report.
5. Recency (holdings §7 item 1); an object-store locator type (§7 item 4).
6. A streaming store write; the ceiling bounds the buffer.
7. Proxy configuration; the pinned connection dials the validated address
   directly and `https_proxy` is not read.

## 11. Testing and the cut

### 11.1 Unit

`python/tests/test_holdings_records.py` (extended; the deferral test
replaced): the canonicalization table — scheme and host case, default port
elided and `8443` kept, empty path, dot-segments (`/a/./b/../c` → `/a/c`),
percent-encoding (`%7e` → `~`, `%2f` kept as `%2F`, `%41` → `A`), query
byte-exact (`?b=%2f&a` unchanged, `?` kept), and one refusal each for
fragment, userinfo, `ftp`, empty host, a non-ASCII host, a space, a
control character; `UrlLocator` equality; a `url` observation with
`Absent` refuses; `supersedes` across a `url` and a `store` location
refuses; the facet and identity of a `url` observation; round-trip through
`stored.holdings_observation_value`, and the decode refusals for an
unknown `type` and a wrong key set.

`python/tests/test_holdings_transport.py` (new): preflight's refusals
(scheme, no host, unresolvable, non-global address) each `NotAttempted`
with the reason; a validated address that cannot be pinned issues no
request (the seam's request counter is zero); the pinned connection dials
the address and validates the name (the survey test moved); a relative
`Location` is joined before revalidation; a refused hop is `Failed` with
its ordinal and category and never the hop's bytes or host — one case
with a signed query (`X-Amz-Signature=…`) and one with a token-bearing
hostname (`https://tok3n-9f2a.example.net/…`), asserting neither the
query, the token nor the host occurs in the reason or in any exception
text; too many redirects is `Failed` naming the bound; a non-identity
`Content-Encoding`, a short and a long body against `Content-Length`, a
`404`, a `500`, a redirect without `Location`, and a timeout are each
`Failed` **carrying no digest**; the ceiling ends the stream at `max_bytes
+ 1` and the `Failed` carries no digest and leaves no scratch file; the
request as the in-process server receives it for
`https://example.org:8443/data?` has target `/data?` and `Host:
example.org:8443`, and for `https://example.org/a/./b/` has target
`/a/b/` and `Host: example.org`; a complete `200` body is `Retrieved` with
the sha256 of the bytes and the scratch path; the scratch root refuses
either root or a descendant; the look's file is deleted on every path.

`python/tests/test_holdings_boundary.py` (extended): `look` appends a
`re-check` intent naming the URL location, publishes `found` fulfilling
it, and raises on a publication failure after `Retrieved`; an
inconclusive look mints nothing and leaves the standing observation's
identity unchanged; `intent_payload` over a `UrlLocator`.

`python/tests/test_holdings_acquire.py` (new), over `tmp_path` roots with a
scripted seam: the happy path (one resource, materialized) — one operation
intent before every holdings intent, one report, the dataset at its
derived address with `retrieval` naming the report, the report's three
entries in order, `completion` `closed`; two resources with the second
failing — first entry `PublishedObservation`, second `RetrievalFailed`, no
dataset, closed, `stop.phase == "look"`; three resources with the first
refused at preflight — entries `ByteLocatorUntested(reason)`,
`ByteLocatorUntested("skipped-after-stop")` twice, **zero** requests
issued, exactly one holdings intent (the first resource's re-check
intent precedes its preflight); an expectation mismatch — observation `found(D')` with
`expected = D`, no dataset, `dataset_observations` reports the mismatch;
an existing address — no second dataset, observation and report
published; every pre-intent refusal (wrong root, no port, store-less
materialization, malformed request, scratch under a root) leaves the
chain and the corpus byte-identical and issues no request; a store
refusal on the **first** of two resources closes with that resource's
mutation entry absent, the second resource skipped, no dataset,
`stop == Stop(name, "materialize", reason)` and the outcome returned, not
raised; a store refusal on the **last** resource closes the same way with
every earlier resource's entries intact and no dataset; the refusal is
provoked through the **production seam** — a store root the engine
refuses to mutate (a read-only replica, cut 10's lifecycle machinery),
so the `StoreWriteRefused` wraps a real `ExecutionError` from
`run_transaction`, not a fake; a publication failure **after** a
committed materialization (`publish_fulfilling` raising `ExecutionError`)
propagates as `ExecutionError`, the operation reads unfinished, and the
store location is unsettled under its unmatched intent; a session closed
between the look and the write (`SessionProtocolError` from the guard)
propagates, and a ledger that cannot be written (`SessionLedgerFailed`)
propagates — neither is a stop;
no lock held across the request (the seam's `connect` acquires
`_operation_lock_for(root)` non-blocking and succeeds).

`python/tests/test_holdings_reduce.py` and `test_holdings_stored.py`
(extended): the `url` fixture reduces; a mixed coverage's active set
carries both keys; the rule bundle's identities differ from cut 10's
recorded pair and `install_rule_binding` of the new bundle beside a
world holding the old one leaves the old receipt `validated`.

`python/tests/test_report.py` (extended): `_mint_acquisition_report`
refuses a non-acquisition intent; the entry order is identity-bearing
across the three entry kinds.

`python/tests/test_intent_evidence.py` and `test_intents_holdings.py`
(extended): a URL observation decodes to `ObservationEvidence("url:…",
token)`; a URL re-check intent decodes through `decode_holdings_intent`
and `shapes.decode_intent`; the generated `qualify.py` still equals the
header plus the source bytes.

`python/tests/test_session_routes.py` and `test_session_reconcile.py`
(extended): `acquire` through a session ledgers every commit; a
store-less session refuses before the intent; `reconcile` over a session
whose chain holds a URL re-check intent and its fulfilling observation
reports nothing, and over one whose URL intent is unfulfilled reports the
same interrupted-act finding a store re-check would.

`python/tests/test_admission_survey.py`: the transport tests move to
`test_holdings_transport.py`; the instrument's remaining tests import the
kernel's seam.

### 11.2 Acceptance

`python/tests/acceptance/test_url_retrieval_acceptance.py` (new), on the
certified tuple through the durable writer session and the production
store seam, with an injected `UrlSeam` over an in-process TLS server whose
certificate the seam's context trusts; one check per declaration unit:

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
| BI-11 | — | the materialization classification: a production-seam store refusal on the first and on the last resource each returns a stopped outcome with no dataset; a publication failure after a committed materialization propagates `ExecutionError` and the operation reads unfinished; a terminal session failure propagates and is never a stop |

Twenty-seven units: sixteen against rows, eleven boundary invariants.

### 11.3 N2 sabotages

`python/tests/acceptance/n2_arms_cut35.py`, one `Arm` per unit; every
`before` string occurs exactly once in its module at freeze; the mutated
module is `ast.parse`d.

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
| BI-11 | `holdings/boundary.py` | the `StoreWriteRefused` wrap widens from the `store_write` call to the whole of `write` | BI-11 (the publication failure reads as a stop) |

Both directions are required: the check passes on the real tree and fails
under sabotage.

### 11.4 The cut

Conformance cut **35**, claimed at freeze (rule 1) after scanning every
worktree and branch for a cut numbered 35–39 (none at 2026-09-19: `main`,
`url-retrieval`, `.worktrees/audio-baseline`, `.worktrees/atoms`,
`.worktrees/nodes`, every ref of `git branch -a`). The runner
`python/tools/cut35_acceptance.py` names `"cut34_acceptance.py"` in
`PREFIX_RUNNERS` (rule 5) and carries `PHASE_MODULES =
("test_url_retrieval_acceptance.py", "test_n2_cut35.py")`. Declaration
units: H4-a–b, G9-a, R10-a, T5-a–c, T7-a–b, T1-a, T2-a–d, T4-a–b,
BI-1–BI-11 — twenty-seven. Frozen by dated
commit after review clears; invalidated frozen evidence is pinned and
cited, never edited. The results record states six rows closed (H4, G9,
R10, T5, T1, T4), two partial (T2, T7), **183 of 216**.

### 11.5 Frozen evidence and live tests

- Cut 10's **J3** arm pins `url_locator`'s deferral line and its check
  `test_url_locator_refuses_with_the_named_deferral`. The frozen
  declaration is untouched; `test_n2_cut10.py` gains a `_LIVE_SABOTAGES`
  entry for `J3` whose sabotage makes `url_locator` accept userinfo and
  whose check is the successor's userinfo refusal, and the staleness
  registry records the moved pin exactly as cut 34 recorded its six.
- Cut 10's five arms on `holdings/rules_v1/holdings.py` and the cut-10
  arms on `holdings/boundary.py` and `holdings/records.py` are checked
  against the staleness probe at every task; a pin a change moves is
  re-targeted in the live guard in the same commit, never in the frozen
  file.
- `test_holdings_records.py`'s deferral test is edited to the successor
  contract (the cut 31–33 precedent for frozen modules); `errors.py` loses
  `UrlLocatorDeferred` (decision 16).
- Cut 3's T5 type-union checks, cut 5's T1 import check and cut 16's T2
  root-local checks are unchanged and cited.

## 12. Shared files, under roadmap concurrency rule 3

`errors.py` (`AcquisitionRefused`, `StoreWriteRefused`; `UrlLocatorDeferred` removed),
`python/tests/test_designs_corpus.py`, the ledger, the roadmap and the
guide index, as every lane. Beyond those: `holdings/records.py`,
`holdings/boundary.py`, `intents/holdings.py` (the source) and
`holdings/qualify.py` (regenerated from it), `intents/evidence.py`,
`holdings/rules_v1/holdings.py` and its fixtures, `holdings/transport.py`
(new), `holdings/acquire.py` (new), `boundary.py`
(`_mint_acquisition_report`), `corpus.py` (`_publish_operation_report`'s
plan parameter; the overlay validation the acquisition calls), `stored.py`
(`holdings_observation_value`), `session/writer.py` (`acquire`),
`python/tools/survey_admission.py` (imports the kernel transport), and the
holdings, act-report and admission-ramp designs (dated notes). `corpus.py`
and `stored.py` are on the world-read lane's shared-surface column; that
lane is not open, and if it opens beside this one the later merge resolves
toward the earlier. Both `CONTRACT.yaml` copies are unchanged: the
holdings-observation facet is reader-shaped, and the empirical-observation
facet already admits `url`; the plan verifies by comparing contract
identities before and after. No TypeScript changes: the parity surface
decodes no holdings record.

## 13. Limitations and open questions this slice files

1. **A URL never mints `absent`** (holdings §2, unchanged): remote
   disappearance is observable only as repeated inconclusive attempts.
2. **Credential-free authoring of the declared URL is the caller's
   obligation** (holdings §2), unchanged; the hop rule (decision 6) closes
   only the server-chosen half.
3. **Internationalized host names refuse at construction.** IDNA is a
   canonicalization amendment; filed as an idea.
4. **The materialization buffers the whole resource** once, bounded by the
   ceiling; a streaming store seam is an atoms request nobody has made.
5. **No retry, no proxy, no authentication** (§10).
6. **A look-only acquisition through the session still needs a bound
   store**, because `holdings_context` does; `acquire` over a hand-built
   `ActContext` has the same shape. A store-less look route is not
   designed here.
7. **T2 stays partial on `audit` and `re-check`** (decision 12);
   `act-report-remainder` keeps the two as its remainder.
8. **The reducer's rule identity moves** (decision 14); receipts under the
   old binding validate only where the old implementation is held.
9. **A raw-written `url` intent with a non-canonical spelling** is an
   unmatched intent forever (§7); the audit reports nothing about it, on
   the same grounds cut 25 gave for sources.

## 14. Design amendments and records this slice lands

- Holdings record design §3: dated notes at "a URL look is intent-free" and
  "a `url` re-check needs no intent" (decision 2), and at §2's `url` row
  recording the two-scheme construction rule (decision 1) and the hop rule
  (decision 6: a hop is named by ordinal and category, never bytes or host,
  and a refused hop is `retrieval-failed`).
- Admission ramp §4: a dated note that "a hop refused at preflight ends the
  attempt as `byte-locator-untested` with the hop named" is superseded at
  the kernel by decision 6 — the instrument's own vocabulary was written
  before T5 reserved the word.
- Act-report design §2.2 and §3.1: a dated note naming the `acquisition`
  operation as built, its entry sequence, and decision 11's no-pin case.
- Admission ramp §4: a dated note that the instrument now runs on the
  kernel's transport; §6.6: a dated note that under cut 29 the "declared
  with a locator and no digest" record is the acquisition **request**, and
  the pin is the mint.
- Computation design §4.7: a dated note mapping the provenance record's
  members onto the three records (§6).
- World-index holdings design §1 item 1, §3, §6: dated closure notes.
- Adoption ledger `Current state`: H4, G9, R10, T5, T1, T4 close;
  `url-retrieval` leaves the table; `act-report-remainder` stays with T2's
  remainder; the summary paragraph names cut 35.
- Roadmap: off-path row 1 discharged and later rows renumber; the
  `acquisition` lane closes with `url-retrieval`; the ride-along table's
  `act-report-remainder` row becomes an off-path boundary row carrying
  T2's two kinds, ranked in breadth order after `l13-preimage`, and
  re-homes to the `world-read` lane's column, since the `audit` wrapper
  lands on `audit.py` and `world/audit.py` and the `re-check` wrapper on
  `holdings/boundary.py`; Appendix A and B.
- Guide: the kinds and outcomes tables (`url` locator, `acquisition`
  operation), open-questions (the act-report residue loses "new operation
  kinds — closed at five", which cut 16 already widened), glossary.
- README and the corpus guard: cut 35's row; this document's promoted row
  at banking.

## 15. The reproduction

The reproduction re-runs under this slice into the corpus at
`.work/reproduction/mm30`, read in place (no contract succeeds), and
appends §14 to its record: the same `NoBelief` answer, no digest moved,
every stored holdings observation a `store` location decoding under the
widened codec. The `url` arm is exercised only by the acceptance module;
mm30's corpus acquires nothing by URL. If a digest moves, that is a finding
against §7 and the cut does not freeze until it is explained.

## 16. Task linkage

`beliefs-d13fe8` is the boundary task and carries `--spec url-retrieval`
for this document; the implementation plan attaches to it, its `### Task
N:` headings becoming step children with explicit complexity and
`--process direct`. The ideas this slice files at the cut: the IDNA
amendment (§13 item 3), the `audit` and `re-check` operation wrappers
(decision 12, noted on the ledger row rather than a new task until the
world-read lane's next slice is designed), and a store-less look route
(§13 item 6).

## 17. Review log

- 2026-09-19 — drafted against `main` at `728a178`.
- 2026-09-20 — first review, six findings, all confirmed against the
  tree. Changed: `holdings/qualify.py` is generated from
  `intents/holdings.py` and `intents/evidence.py` spells a store-only
  location key — both named in §7 and §12, the evidence key built from the
  record's `canonical()`, reconciliation covered (BI-10); a refused hop is
  named by ordinal and a fixed category, never its host, because a
  hostname can carry the grant (decision 6), tested with a token-bearing
  hostname beside the signed query (BI-2); a refused hop is
  `retrieval-failed`, since the declared URL's request began (decision 6,
  §4); the request target and `Host` transmit the canonical locator
  faithfully — empty `?` and non-default port included — and the actual
  request is tested (decision 8); a materialization refusal is a stop with
  a defined return contract — `AcquisitionOutcome.stop`, remaining
  resources skipped, no mint, no raise past a closed report — tested on
  the first and the last resource (decisions 5, 10, §6); an incomplete
  body yields no finalized or published digest rather than "is never
  hashed" (decision 7, §4, BI-4); the preflight-refusal test issues zero
  requests while keeping its one holdings intent (§11.1).
- 2026-09-20 — second review, one blocker, confirmed: the production seam
  maps every engine refusal to `nodes.core.errors.ExecutionError`, not a
  `ScienceError`, and the same type comes from the intent append and the
  publication. Changed: `write` classifies by phase — exactly the
  `store_write` call is wrapped as `StoreWriteRefused(ScienceError)`,
  `acquire` catches exactly that, and intent, publication and session
  failures propagate as themselves (decision 10, §6); BI-11 reads the
  classification with a production-seam refusal, a publication failure
  after a committed materialization, and a terminal session failure.
