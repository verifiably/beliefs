# URL Retrieval Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land the `url` locator, move the network discipline into the kernel behind a transport seam, build the `acquisition` operation that mints a dataset beside its act-report in one transaction, and discharge H4, G9, R10, T5, T1 and T4 (T2 and T7 partial) at conformance cut 35.

**Architecture:** `holdings/records.py` gains `UrlLocator` as the second arm of the locator union; `intents/holdings.py` (the shared source, regenerated into `holdings/qualify.py`), `intents/evidence.py`, `stored.py` and the fixture-bound reducer learn the arm. `holdings/transport.py` is the survey instrument's preflight, pinned connection and streaming fetch made total over a `UrlSeam`. `holdings/boundary.py` gains the URL `look` (a `re-check` intent, then the request with nothing held) and classifies store refusals by phase and cause inside `write`. `holdings/acquire.py` orchestrates one operation intent, per-resource looks and materializations with the cooperative stop, and a closing transaction carrying the dataset and the report. `session/writer.py` exposes the route. Cut 35 freezes before code and discharges on the certified volume.

**Tech Stack:** Python 3.11+ (`uv run --frozen` from `python/`), pytest, `nodes.core`, `atoms` (the certified engine), `http.client` + `ssl` (stdlib only), the N2 harness (`python/tests/test_n2.py`, `n2_arms.py`, `arm_staleness.py`), `tasks`.

**Spec:** `docs/superpowers/specs/2026-09-19-url-retrieval-design.md` (approved for planning 2026-09-20 at `395b550` after four reviews; review log §17).

## Global Constraints

- **Baseline is `main` at `728a178`** (code unchanged since `3873d16`). Work in the worktree `.worktrees/url-retrieval` (branch `url-retrieval`); every path below is relative to the repository root, and paths shown to the user carry the worktree prefix. Exports for a worktree on `WORK_ROOT`: `SCIENCE_MM30_ROOT` and every `SCIENCE_CUT*_ROOT` name the **main checkout's** `.work/…` (memory `worktree-on-work-root-needs-cut-root-exports`; ~190 `CapabilityUnavailable` failures are a missing export, not a regression).
- Frozen declarations (`n2_arms_cut*.py`) and frozen cut bodies (§§2–7 of every cut document) stay byte-exact; a pinned line a change moves is re-targeted in the live guard's `_LIVE_SABOTAGES`, never in the frozen file (spec §11.5). After every task that touches `holdings/records.py`, `holdings/boundary.py`, `holdings/rules_v1/holdings.py` or `holdings/qualify.py`, run `cd python && uv run --frozen pytest tests/test_arm_staleness.py tests/acceptance/test_n2_cut10.py -q -k "not sabotage and not findings"` and re-target any cut-10 pin the change moved.
- `holdings/qualify.py` is **generated**: edit `intents/holdings.py`, then `cd python && uv run --frozen python tools/regen_holdings_interior.py` (spec §7). Never hand-edit the generated file.
- The `url` canonical form is decision 1's, exactly; `http` and `https` only; fragment and userinfo refused; a `url` observation never spells `Absent` (spec §3).
- A refused redirect hop is `retrieval-failed` named by ordinal and a fixed category, never bytes or host; `byte-locator-untested` only for the declared URL's own preflight and the post-stop skip (decisions 5, 6). No hop URL enters any record, entry, reason or exception text.
- The request target is the canonical path and query byte-exact (empty `?` kept); `Host` is the canonical authority with a non-default port (decision 8). An incomplete body yields no finalized digest (decision 7).
- `StoreWriteRefused` only for an `ExecutionError` from the `store_write` call with `applied == 0` and a cause in `{ProjectApprovalRefused, PreconditionRefused, PendingUnresolved}`; everything else propagates (decision 10). `acquire` catches exactly `StoreWriteRefused`.
- No lock is held across a network request (decision 15). No test reaches the network (decision 9).
- **Lock order at the close is session, then root** — `ScopedWriter._act`'s only order. `acquire` enters the caller's `hold` before `writer._operation`, and neither is entered around the request. Under the closing lock the writer's view is rebuilt (`writer._reconstruct()`) before any ref or address resolves: holdings publications go through the holdings seam, past the writer's cached index, and `_SettlingHold` rebuilds only when `unresolved` is set.
- A transport failure is named by a fixed category — `timeout`, `tls`, `connection`, `protocol` — never by the exception's text (a certificate error names the redirected host). `http.client.HTTPException` is a `Failed`, not an escape. Every exceptional exit unlinks the scratch file; `look` unlinks its retrieved file when publication fails.
- The canonical path keeps the trailing slash RFC 3986 §5.2.4 leaves after a final `.` or `..` segment (`/a/.` → `/a/`, `/a/b/..` → `/a/`); an IPv6 host keeps its brackets; port `0` is refused at construction.
- Each read is bounded by the remaining allowance plus one byte, so the ceiling is exceeded by exactly one byte before refusal; `timeout_seconds` is finite.
- `look` refuses a scratch root under either root before its intent; `acquire` validates the request's dataset shape (title, locator, domain facets) through the writer before its intent.
- Unit tests run over the scripted fake **and** the in-process TLS server (`python/tests/holdings_transport_fixtures.py`); the acceptance module runs its success, truncation, redirect and ceiling cases through that server, the seam's context trusting the committed test certificate with `check_hostname` and `CERT_REQUIRED` intact.
- Both `CONTRACT.yaml` copies are unchanged and their identities equal before and after (§12 — Task 1 verifies). No TypeScript changes.
- `science.belief.v1`'s answers over every existing fixture are unchanged; P1–P9 green at every commit.
- Conventional commits, no attribution trailers. `tasks check` before every commit; the pre-commit hook runs `just hook-pre-commit` (~20 s). `just test-fast` while working; never the full suite after every edit (AGENTS.md). Every commit message names the row(s) or invariant(s) it serves.

---

## File map

| File | Responsibility |
| --- | --- |
| `python/src/beliefs/errors.py` | `AcquisitionRefused(WriteRefused)`, `StoreWriteRefused(ScienceError)`; `UrlLocatorDeferred` removed (Tasks 1, 4, 5) |
| `python/src/beliefs/holdings/records.py` | `UrlLocator`, `url_locator`, `Locator`; the observation's second arm (Task 1) |
| `python/src/beliefs/stored.py` | `holdings_observation_value` decodes both arms (Task 1) |
| `python/src/beliefs/intents/holdings.py` → `holdings/qualify.py` (generated) | `_location`'s `url` arm (Task 2) |
| `python/src/beliefs/intents/evidence.py` | the location key from `canonical()` (Task 2) |
| `python/src/beliefs/holdings/rules_v1/holdings.py`, `rules_v1/fixtures/holdings.url.yaml` | the reducer's location key; the url fixture (Task 2) |
| `python/src/beliefs/holdings/transport.py` (new) | `RetrievalBounds`, `UrlSeam`, `url_seam`, `preflight`, `PinnedHTTPSConnection`, `retrieve`, `refuse_scratch_root` (Task 3) |
| `python/tests/holdings_transport_fixtures.py` (new) | `Scripted`, `ScriptedConnection`, `scripted_seam` — the scripted fake; `Served`, `LocalTlsServer`, `tls_seam` — the in-process TLS server (Task 3) |
| `python/tests/fixtures/tls/server.pem`, `python/tests/fixtures/tls/server.key` (new) | the test certificate the local server presents and the test seam's context trusts: SANs `example.org`, `mirror.example.org`, `localhost`; a hundred years (Task 3) |
| `python/src/beliefs/holdings/boundary.py` | `intent_payload` over `Locator`; `look`; `store_refusal`; `write`'s wrap (Task 4) |
| `python/src/beliefs/boundary.py` | `_mint_acquisition_report` (Task 5) |
| `python/src/beliefs/corpus.py` | `_append_operation_intent(port=)`, `_publish_operation_report(operations=, port=)`, `_refuse_acquired_dataset`, `_refuse_dataset_shape` (`_refuse_facets`' shape half factored out) (Task 5) |
| `python/src/beliefs/holdings/acquire.py` (new) | `ResourceRequest`, `AcquisitionRequest`, `Stop`, `AcquisitionOutcome`, `acquire` (Task 5) |
| `python/src/beliefs/session/writer.py` | `ScopedWriter.acquire`, `ScopedWriter._closing_hold` (Task 6) |
| `python/tools/survey_admission.py` | imports the kernel transport; `NetworkProbe.fetch` is an adapter over `retrieve` to the `ProbeOutcome` vocabulary (Task 6) |
| `python/tests/test_holdings_records.py`, `test_holdings_stored.py`, `test_intents_holdings.py`, `test_intent_evidence.py`, `test_holdings_reduce.py`, `test_holdings_transport.py` (new), `test_holdings_boundary.py`, `test_holdings_acquire.py` (new), `test_report.py`, `test_session_routes.py`, `test_admission_survey.py`, `acceptance/test_n2_cut10.py` | unit coverage and the cut-10 re-target (Tasks 1–6) |
| `python/tests/acceptance/test_url_retrieval_acceptance.py`, `python/tests/n2_arms_cut35.py`, `python/tests/acceptance/n2_arms_cut35.py`, `python/tests/acceptance/test_n2_cut35.py`, `python/tools/cut35_acceptance.py` | the twenty-seven declaration units, the sabotages, the guard, the runner (Task 8) |
| `docs/designs/2026-09-20-conformance-cut-35.md`, `docs/plans/2026-09-20-conformance-cut-35-results.md`, the ledger, the roadmap, the guide, `README.md`, the holdings, act-report, admission-ramp, computation and world-index-holdings designs (dated notes), the reproduction record §14 | freeze, discharge, amendments (Tasks 0, 7, 9) |

---

### Task 0: Freeze cut 35 and file the tasks

**Files:**
- Create: `docs/designs/2026-09-20-conformance-cut-35.md`
- Modify: `README.md` (the design table gains the cut-35 row, status "frozen"; "Every conformance cut through **cut 34**" stays until discharge), `docs/guide/contracts-and-adoption.md` (`sources` gains the cut document; after the cut-34 paragraph: "Cut 35 is frozen and not yet discharged: URL retrieval and the acquisition operation (H4, G9, R10, T5, T1, T4; T2 and T7 partial; `../designs/2026-09-20-conformance-cut-35.md`)")
- Tasks: filed at the planning commit (Step 3); `tasks start` the Task-0 step child

**Interfaces:**
- Produces: `CUT35_FREEZE_COMMIT` and `CUT35_FROZEN_SHA256`, pinned by Task 8's guard; the step-child ids every later commit closes.

- [ ] **Step 1: Confirm the baseline and the lane**

Run `git -C /mnt/ssd/Dropbox/beliefs log --oneline -1`; `main` is at `728a178` or a descendant touching none of `holdings/`, `intents/`, `corpus.py`, `stored.py`, `boundary.py`, `session/writer.py`, `errors.py`. If it moved, `git merge --ff-only main` in the worktree (or rebase), re-read spec §1's baseline claims against the tree and record any drift in spec §17. `tasks prime` inside the worktree: `beliefs-d13fe8` is `doing`, owned by this branch; the roadmap's lane table shows no open kernel lane.

- [ ] **Step 2: Claim the cut number**

`git worktree list`, then for each worktree `ls <wt>/docs/designs/*conformance-cut-3[5-9]*.md` and `for b in $(git branch --format='%(refname:short)'); do git ls-tree -r --name-only $b docs/designs | grep -i 'cut-3[5-9]'; done`. Nothing may match (spec §11.4 scanned 2026-09-19; re-scan now). If something does, the number is the next unclaimed one and every `35` below moves with it. The highest discharged runner is `python/tools/cut34_acceptance.py`.

- [ ] **Step 3: The tasks are filed**

Filed at the planning commit so `tasks check` links every heading: `beliefs-d13fe8` carries the spec and this plan; its step children are listed in the table below, one per `### Task N:` heading. Each `<taskN-id>` below is the id in this list.

| task | id |
|---|---|
| Task 0 | `beliefs-4b4317` |
| Task 1 | `beliefs-4754b1` |
| Task 2 | `beliefs-53b8e8` |
| Task 3 | `beliefs-8831ed` |
| Task 4 | `beliefs-853055` |
| Task 5 | `beliefs-059224` |
| Task 6 | `beliefs-3ea5ac` |
| Task 7 | `beliefs-a74957` |
| Task 8 | `beliefs-eea81b` |
| Task 9 | `beliefs-cb43c2` |

`tasks start <step>` before each task; `tasks done <step> "<what landed>"` in its commit.

- [ ] **Step 4: Write and freeze the cut document**

`docs/designs/2026-09-20-conformance-cut-35.md` on cut 34's shape (`docs/designs/2026-09-19-conformance-cut-34.md`): `**Status:**` "frozen 2026-09-20, before implementation; H4, G9, R10, T5, T1, T4 are open, T2 and T7 partial"; `**Design:**` the spec path with its approval commit; `**Plan:**` this document; `**Numbered after** cut 34 under roadmap concurrency rule 1`; §1 what this cut is (spec §1 condensed: the URL arm deferred at cut 10, no boundary opens an `acquisition`, the rows read and the two named remainders); §2 the boundary — the file map's surfaces; §3 selection — the twenty-seven units, single-homed, quoting the row texts byte-exact from the holdings design §6 (H4), the admission ramp §6.3 (G9), computation §7.3 (R10) and the act-report design §5 (T1, T2, T4, T5, T7) at freeze, then spec §11.2's unit table verbatim; §4 accounting — "**27 declaration units**, sixteen against rows and eleven boundary invariants; H4, G9, R10, T5, T1 and T4 close; T2 stays partial on the `audit` and `re-check` operation kinds; T7 stays partial on its cross-root case"; §5 N2 and acceptance obligations — spec §11.3's table verbatim, `PREFIX_RUNNERS = ("cut34_acceptance.py",)`, `PHASE_MODULES = ("test_url_retrieval_acceptance.py", "test_n2_cut35.py")`; §6 second reader — four things to check: that the close's lock order is session then root and the view is rebuilt under it before any ref resolves; that BI-2's assertions read every published byte of the observer root and the exception text, not only the entry; that T5-a's classification is read from the transport's phase value and never from a message; that BI-11's production refusal is a real `ExecutionError` from `run_transaction` with a `ProjectApprovalRefused` cause; §7 limitations — spec §13 restated. Then `cd python && uv run --frozen pytest tests/test_designs_corpus.py tests/test_check_guide.py -q` green (the newest *results* record is cut 34's, so a frozen 35 passes).

```bash
tasks done beliefs-4b4317 "cut 35 frozen"
git add docs/designs/2026-09-20-conformance-cut-35.md README.md docs/guide/contracts-and-adoption.md tasks
git commit -m "docs(cut): freeze conformance cut 35, URL retrieval and the acquisition operation"
git rev-parse HEAD                                          # CUT35_FREEZE_COMMIT
sha256sum docs/designs/2026-09-20-conformance-cut-35.md     # CUT35_FROZEN_SHA256
```

---

### Task 1: The `url` locator, the record's second arm, the codec

**Files:**
- Modify: `python/src/beliefs/holdings/records.py` (the whole locator section; `HoldingsObservation`; `holdings_observation`), `python/src/beliefs/stored.py:825-855` (`holdings_observation_value`), `python/src/beliefs/errors.py:857-863` (`UrlLocatorDeferred` deleted)
- Modify: `python/tests/test_holdings_records.py` (the deferral test replaced), `python/tests/test_holdings_stored.py`, `python/tests/acceptance/test_n2_cut10.py` (the J3 re-target)
- Test: as above

**Interfaces:**
- Produces: `records.UrlLocator(url: str)` with `.canonical() -> "url:" + url`; `records.url_locator(spelling: str) -> UrlLocator`; `records.Locator = StoreLocator | UrlLocator`; `HoldingsObservation.location: Locator`; `holdings_observation(location: Locator, ...)`. Tasks 2–5 and 8 consume all of these.

- [ ] **Step 1: The failing tests**

Replace `test_url_locator_refuses_with_the_named_deferral` in `python/tests/test_holdings_records.py` (and drop `UrlLocatorDeferred` from its imports; add `UrlLocator`, `url_locator` is already imported) with:

```python
CANONICAL = [
    # (spelling, canonical): one row per profile clause of decision 1
    ("HTTPS://Example.ORG/data", "https://example.org/data"),
    ("https://example.org:443/data", "https://example.org/data"),
    ("http://example.org:80/data", "http://example.org/data"),
    ("https://example.org:8443/data", "https://example.org:8443/data"),
    ("https://example.org", "https://example.org/"),
    ("https://example.org/a/./b/../c", "https://example.org/a/c"),
    ("https://example.org/a/%7e/%2f/%41", "https://example.org/a/~/%2F/A"),
    ("https://example.org/p?b=%2f&a", "https://example.org/p?b=%2f&a"),
    ("https://example.org/p?", "https://example.org/p?"),
    ("https://example.org/p?B=1", "https://example.org/p?B=1"),
    ("https://example.org/a/.", "https://example.org/a/"),
    ("https://example.org/a/b/..", "https://example.org/a/"),
    ("https://example.org/a/b/", "https://example.org/a/b/"),
    ("https://example.org/..", "https://example.org/"),
    ("https://[2001:DB8::1]:8443/x", "https://[2001:db8::1]:8443/x"),
    ("https://[2001:db8::1]:443/x", "https://[2001:db8::1]/x"),
]


@pytest.mark.parametrize("spelling,canonical", CANONICAL)
def test_url_locator_canonicalizes_under_the_banked_profile(spelling: str, canonical: str):
    locator = url_locator(spelling)
    assert locator.url == canonical
    assert locator.canonical() == "url:" + canonical
    assert url_locator(canonical) == locator


@pytest.mark.parametrize(
    "spelling",
    [
        "https://example.org/p#frag",
        "https://example.org/p#",
        "https://user@example.org/p",
        "https://user:pw@example.org/p",
        "ftp://example.org/p",
        "https:///p",
        "https://exämple.org/p",
        "https://example.org/a b",
        "https://example.org/a\tb",
        "https://example.org/%zz",
        "https://example.org/%4",
        "https://example.org:0/p",
        "https://[2001:db8::1/p",
        "https://[example.org]/p",
        "",
        "example.org/p",
    ],
)
def test_url_locator_refuses_rather_than_repairs(spelling: str):
    with pytest.raises(MalformedRecord):
        url_locator(spelling)


def test_a_trailing_dot_segment_names_the_directory_and_not_its_parent():
    assert url_locator("https://example.org/a/.") == url_locator("https://example.org/a/")
    assert url_locator("https://example.org/a/.") != url_locator("https://example.org/a")
    assert url_locator("https://example.org/a/b/..") != url_locator("https://example.org/a")


def test_a_url_locator_is_constructed_canonical_or_refused():
    assert UrlLocator("https://example.org/") == url_locator("https://EXAMPLE.org")
    with pytest.raises(MalformedRecord):
        UrlLocator("https://EXAMPLE.org/")


def test_a_url_observation_carries_the_url_arm_in_its_facet_and_identity():
    record = observation(location=url_locator("https://example.org/data"))
    assert record.facet()["location"] == {"type": "url", "url": "https://example.org/data"}
    other = observation(location=url_locator("https://example.org/other"))
    assert record.identity() != other.identity()


def test_a_url_observation_never_spells_absent():
    with pytest.raises(MalformedRecord):
        observation(location=url_locator("https://example.org/data"), outcome=Absent())


def test_supersession_never_crosses_the_url_and_store_arms():
    store = observation()
    with pytest.raises(MalformedRecord):
        observation(location=url_locator("https://example.org/data"), supersedes=(store,))
```

In `python/tests/test_holdings_stored.py` add (import `url_locator` and `Found`, and the decode helpers the module already uses):

```python
def test_a_url_observation_round_trips_through_the_stored_codec():
    record = holdings_observation(
        location=url_locator("https://example.org/data"), outcome=Found("sha256:" + "ab" * 32),
        observer="o", instrument="i", event_token="t", observed_at="2026-09-20T00:00:00Z",
    )
    node = stored.holdings_observation_node(record)
    assert stored.holdings_observation_value(node) == record


@pytest.mark.parametrize(
    "location",
    [
        {"type": "url"},
        {"type": "url", "url": "https://example.org/", "store_id": "a" * 32},
        {"type": "s3", "url": "https://example.org/"},
        {"type": "url", "url": "https://EXAMPLE.org/"},
    ],
)
def test_the_codec_refuses_a_location_outside_the_two_arms(location):
    record = holdings_observation(
        location=url_locator("https://example.org/data"), outcome=Found("sha256:" + "ab" * 32),
        observer="o", instrument="i", event_token="t", observed_at="2026-09-20T00:00:00Z",
    )
    node = stored.holdings_observation_node(record)
    facet = dict(node.facets["holdings-observation"])
    facet["location"] = location
    with pytest.raises(MalformedRecord):
        stored.holdings_observation_value(node.model_copy(update={"facets": {"holdings-observation": facet}}))
```

- [ ] **Step 2: Run them to verify they fail**

Run: `cd python && uv run --frozen pytest tests/test_holdings_records.py tests/test_holdings_stored.py -q`
Expected: FAIL — `url_locator` raises `UrlLocatorDeferred`; `UrlLocator` is not defined.

- [ ] **Step 3: The locator**

In `python/src/beliefs/holdings/records.py`, replace `url_locator` and extend the union. Add to the imports `import ipaddress` and `from urllib.parse import urlsplit`; drop `NoReturn` and `UrlLocatorDeferred`; add `"UrlLocator"` and `"Locator"` to `__all__`.

```python
_DEFAULT_PORTS = MappingProxyType({"https": 443, "http": 80})
_UNRESERVED = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~")
_HEX = frozenset("0123456789abcdefABCDEF")


def _normalized_path(path: str) -> str:
    """Percent-encoding normalized (uppercase hex, unreserved decoded), then
    dot-segments removed (RFC 3986 §5.2.4); the path component only."""
    out: list[str] = []
    index = 0
    while index < len(path):
        character = path[index]
        if character != "%":
            out.append(character)
            index += 1
            continue
        pair = path[index + 1 : index + 3]
        if len(pair) != 2 or any(digit not in _HEX for digit in pair):
            raise MalformedRecord(f"url path {path!r} carries a malformed percent-encoding")
        decoded = chr(int(pair, 16))
        out.append(decoded if decoded in _UNRESERVED else "%" + pair.upper())
        index += 3
    segments: list[str] = []
    directory = False  # RFC 3986 §5.2.4: a final `.` or `..` leaves the trailing slash
    for segment in "".join(out).split("/")[1:]:
        if segment == ".":
            directory = True
            continue
        if segment == "..":
            if segments:
                segments.pop()
            directory = True
            continue
        segments.append(segment)
        directory = False
    normalized = "/" + "/".join(segments)
    if directory and not normalized.endswith("/"):
        normalized += "/"
    return normalized


def _canonical_url(spelling: str) -> str:
    if not isinstance(spelling, str) or not spelling:
        raise MalformedRecord("a url locator is a non-empty string")
    if any(not (0x21 <= ord(character) <= 0x7E) for character in spelling):
        raise MalformedRecord(f"url {spelling!r} carries a non-ASCII, whitespace or control byte")
    if "#" in spelling:
        raise MalformedRecord(f"url {spelling!r} carries a fragment; a fragment never names a location")
    try:
        parts = urlsplit(spelling)
    except ValueError as caught:  # an unbalanced IPv6 bracket
        raise MalformedRecord(f"url {spelling!r} does not split: {caught}") from caught
    scheme = parts.scheme.lower()
    if scheme not in _DEFAULT_PORTS:
        raise MalformedRecord(f"url {spelling!r}: scheme {parts.scheme!r} is outside http and https")
    if "@" in parts.netloc:
        raise MalformedRecord(f"url {spelling!r} carries userinfo; a credential never enters a location")
    host = parts.hostname
    if not host:
        raise MalformedRecord(f"url {spelling!r} names no host")
    if parts.netloc.startswith("["):
        try:
            ipaddress.IPv6Address(host)
        except ValueError as caught:
            raise MalformedRecord(f"url {spelling!r}: a bracketed host is an IPv6 literal") from caught
        host = f"[{host}]"  # `hostname` strips the brackets; the authority keeps them
    try:
        port = parts.port
    except ValueError as caught:
        raise MalformedRecord(f"url {spelling!r} carries a malformed port") from caught
    if port == 0:
        raise MalformedRecord(f"url {spelling!r} names port 0; no service listens there and nothing repairs it")
    authority = host if port in (None, _DEFAULT_PORTS[scheme]) else f"{host}:{port}"
    path = _normalized_path(parts.path or "/")
    query = "?" + parts.query if "?" in spelling else ""
    return f"{scheme}://{authority}{path}{query}"


@sealed
@final
@dataclass(frozen=True)
class UrlLocator:
    url: str

    def __post_init__(self) -> None:
        if _canonical_url(self.url) != self.url:
            raise MalformedRecord(f"url locator {self.url!r} is not the canonical spelling; construct it with url_locator")

    def canonical(self) -> str:
        return f"url:{self.url}"


def url_locator(spelling: str) -> UrlLocator:
    """Canonicalize under holdings §2's exact profile, or refuse."""
    return UrlLocator(_canonical_url(spelling))


Locator = StoreLocator | UrlLocator
```

`urlsplit` lowercases `.hostname`; `parts.port` raises `ValueError` on a non-numeric port. `"?" in spelling` is sound because a fragment was refused first.

Then the record: `HoldingsObservation.location: Locator`; in `__post_init__` replace the `StoreLocator` check with `if not isinstance(self.location, (StoreLocator, UrlLocator)): raise MalformedRecord("a holdings observation names a store or url locator")` and add, after the outcome check:

```python
        if isinstance(self.location, UrlLocator) and isinstance(self.outcome, Absent):
            raise MalformedRecord("a url location never establishes absent; only a store dereference can")
```

In `facet()`, replace the `"location"` member with `"location": self.location_facet()` and add:

```python
    def location_facet(self) -> dict[str, str]:
        if isinstance(self.location, UrlLocator):
            return {"type": "url", "url": self.location.url}
        return {"type": "store", "store_id": self.location.store_id, "relative_path": self.location.relative_path}
```

In `holdings_observation(...)`: `location: Locator`, and its first check becomes the same two-arm `isinstance`. The per-location `supersedes` check already compares `canonical()` strings and needs no change.

- [ ] **Step 4: The codec**

In `python/src/beliefs/stored.py`, `holdings_observation_value` (line 825): import `UrlLocator` beside `StoreLocator` from `beliefs.holdings.records` (line 83) and replace the location checks with:

```python
        location = facet["location"]
        outcome = facet["outcome"]
        if not isinstance(location, dict) or not isinstance(location.get("type"), str):
            raise MalformedRecord("a holdings observation location is a store or url locator")
        if location["type"] == "store" and set(location) == {"type", "store_id", "relative_path"}:
            decoded_location: StoreLocator | UrlLocator = StoreLocator(location["store_id"], location["relative_path"])
        elif location["type"] == "url" and set(location) == {"type", "url"}:
            decoded_location = UrlLocator(location["url"])
        else:
            raise MalformedRecord("a holdings observation location is a store or url locator")
```

and `location=decoded_location` in the constructor call. Delete `class UrlLocatorDeferred` from `python/src/beliefs/errors.py` (lines 857–863) and its `__all__` entry if listed (`grep -n UrlLocatorDeferred python/src/beliefs/errors.py`).

- [ ] **Step 5: Run the tests**

Run: `cd python && uv run --frozen pytest tests/test_holdings_records.py tests/test_holdings_stored.py tests/test_holdings_boundary.py tests/test_holdings_reduce.py -q`
Expected: PASS (the reducer and boundary see only store records and are untouched here).

- [ ] **Step 6: Re-target cut 10's J3 pin**

`python/tests/acceptance/n2_arms_cut10.py:459` pins the deleted `raise UrlLocatorDeferred(...)` line and a check that no longer exists. In `python/tests/acceptance/test_n2_cut10.py`, after the imports, add on `test_n2_cut22.py`'s pattern (import `Sabotage` from `n2_arms` and `replace` from `dataclasses`):

```python
# URL retrieval, cut 35, 2026-09-20: the deferral J3 pinned ended by design.
# The arm's claim — construction refuses what it must — keeps a live check on
# the successor's userinfo refusal. The frozen declaration is not touched.
_LIVE_SABOTAGES = {
    "J3": replace(
        next(arm for arm in CUT10_ARMS if arm.row == "J3"),
        sabotage=Sabotage(
            module="holdings/records.py",
            before='    if "@" in parts.netloc:\n        raise MalformedRecord(f"url {spelling!r} carries userinfo; a credential never enters a location")',
            after='    if False:\n        raise MalformedRecord(f"url {spelling!r} carries userinfo; a credential never enters a location")',
        ),
        checks=("test_holdings_records.py::test_url_locator_refuses_rather_than_repairs",),
    ),
}
CUT10_ARMS = tuple(_LIVE_SABOTAGES.get(arm.row, arm) for arm in CUT10_ARMS)
```

`_LIVE_SABOTAGES` here maps a row to a whole re-targeted `Arm` (the check moved too), so `arm_staleness.re_targeted_rows` reads its keys; the guard's own tests over `CUT10_ARMS` see the live tuple. Then: `cd python && uv run --frozen pytest tests/test_arm_staleness.py tests/acceptance/test_n2_cut10.py -q -k "not findings"` green, and `uv run --frozen pytest tests/test_designs_corpus.py -q` green (the corpus guard reads no source).

- [ ] **Step 7: Contract identities unchanged**

```bash
cd python && uv run --frozen python - <<'EOF'
from beliefs.contract.base import load_base_contract  # if the name differs: grep -n "def load" src/beliefs/contract/base.py
EOF
```

Simpler and exact: `git stash -q && cd python && uv run --frozen python -c "from beliefs.profile import compiled_identity_of_shipped as f; print(f())" ; cd .. && git stash pop -q` — if no such helper exists, compare `sha256sum python/src/beliefs/contracts/science/CONTRACT.yaml ts/src/contracts/science/CONTRACT.yaml` (or wherever the second copy lives: `find . -name CONTRACT.yaml -not -path '*/node_modules/*'`) before and after this task: both digests unchanged.

- [ ] **Step 8: Commit**

```bash
tasks done beliefs-4754b1 "url locator, the record's second arm, the codec; cut 10 J3 re-targeted"
git add python/src/beliefs/holdings/records.py python/src/beliefs/stored.py python/src/beliefs/errors.py python/tests tasks
git commit -m "feat(holdings): the url locator under the banked profile — BI-1, T7"
```

---

### Task 2: The shared intent source, the evidence key, the reducer

**Files:**
- Modify: `python/src/beliefs/intents/holdings.py` (`_location`), then regenerate `python/src/beliefs/holdings/qualify.py`
- Modify: `python/src/beliefs/intents/evidence.py:107-110`, `python/src/beliefs/holdings/rules_v1/holdings.py:14-19`
- Create: `python/src/beliefs/holdings/rules_v1/fixtures/holdings.url.yaml`
- Test: `python/tests/test_intents_holdings.py`, `test_intent_evidence.py`, `test_holdings_reduce.py`

**Interfaces:**
- Consumes: `UrlLocator`, `holdings_observation` (Task 1).
- Produces: `decode_holdings_intent` accepting `{"type": "url", "url": ...}` and returning `"location": "url:<url>"`; `ObservationEvidence(location=value.location.canonical(), ...)`; the reducer keying url heads as `url:<url>`; a bundle whose identities differ from cut 10's.

- [ ] **Step 1: The failing tests**

`python/tests/test_intent_evidence.py`, beside `test_holdings_observation_decodes_location_and_token` (copy its fixture shape for a node under the holdings layout path; the decode entry point the module uses):

```python
def test_a_url_observation_decodes_to_url_evidence():
    record = holdings_observation(
        location=url_locator("https://example.org/data"), outcome=Found("sha256:" + "ab" * 32),
        observer="o", instrument="i", event_token="tok", observed_at="2026-09-20T00:00:00Z",
    )
    node = stored.holdings_observation_node(record)
    evidence = decode_record(f"holdings-observation/{record.identity()}.md", node_to_markdown(node).encode())
    assert evidence == ObservationEvidence("url:https://example.org/data", "tok")


def test_a_url_intent_decodes_through_the_shared_shape_and_matches_its_observation():
    payload = intent_payload(location=url_locator("https://example.org/data"), act_kind="re-check", event_token="tok", actor="actor:a")
    row = {"digest": "1" * 64, "entry": {"payload": payload.hex()}}
    decoded = decode_holdings_intent(row)
    assert decoded == {"digest": "1" * 64, "actor": "actor:a", "event_token": "tok", "kind": "re-check", "location": "url:https://example.org/data"}
    assert shapes.decode_intent("1" * 64, payload).shape == "holdings"
    assert shapes.mismatch(shapes.decode_intent("1" * 64, payload), ObservationEvidence("url:https://example.org/data", "tok")) is None
```

(`decode_record` is whatever name `test_intent_evidence.py` already calls for a record's evidence — read its existing holdings test; `intent_payload` comes from `beliefs.holdings.boundary` after Task 4 widens it — for this task construct the payload bytes by hand with `json.dumps({..., "location": {"type": "url", "url": "https://example.org/data"}}, sort_keys=True, separators=(",", ":")).encode()` and swap to `intent_payload` in Task 4.)

`python/tests/test_holdings_reduce.py`: beside `test_the_bundle_concatenates_the_helper_source`:

```python
def test_the_url_fixture_ships_and_reduces():
    names = [name for name, _ in holdings_rule_bundle().fixtures]
    assert "holdings.url.yaml" in names


def test_a_mixed_coverage_keys_url_and_store_heads_by_their_canonical_forms():
    url_record = observation(REF_A, location={"type": "url", "url": "https://example.org/data"})
    store_record = observation(REF_B)
    result = invoke(capture(corpus(records=[url_record, store_record])))
    assert sorted(head["location"] for head in result["active"]) == sorted(
        ["url:https://example.org/data", OTHER_LOCATION_KEY_OF(store_record)]
    )
```

(`observation`, `capture`, `corpus`, `invoke` are the module's own helpers; read how `observation` takes a location — extend it to accept a url dict, and replace `OTHER_LOCATION_KEY_OF(...)` with the store key the helper already builds.)

- [ ] **Step 2: Run them to verify they fail**

Run: `cd python && uv run --frozen pytest tests/test_intent_evidence.py tests/test_holdings_reduce.py -q`
Expected: FAIL — `AttributeError: 'UrlLocator' object has no attribute 'store_id'` in evidence; `ValueError("malformed holdings intent")` from the shared shape; a `KeyError('store_id')` in the reducer.

- [ ] **Step 3: The shared shape**

In `python/src/beliefs/intents/holdings.py` replace `_location`:

```python
def _url(value):
    if not isinstance(value, str) or not value or not value.isascii() or "#" in value:
        return False
    if any(character.isspace() or ord(character) < 0x21 or ord(character) > 0x7E for character in value):
        return False
    scheme, separator, rest = value.partition("://")
    if separator != "://" or scheme not in ("http", "https"):
        return False
    authority = rest.split("/", 1)[0].split("?", 1)[0]
    return bool(authority) and "@" not in authority


def _location(value):
    if not isinstance(value, dict) or "type" not in value:
        return None
    if value["type"] == "store":
        if set(value) != {"relative_path", "store_id", "type"}:
            return None
        if not _lower_hex(value["store_id"], 32) or not _store_path(value["relative_path"]):
            return None
        return "store:" + value["store_id"] + ":" + value["relative_path"]
    if value["type"] == "url":
        if set(value) != {"type", "url"} or not _url(value["url"]):
            return None
        return "url:" + value["url"]
    return None
```

Then `cd python && uv run --frozen python tools/regen_holdings_interior.py` and confirm `git diff --stat src/beliefs/holdings/qualify.py` shows the same change.

- [ ] **Step 4: The evidence key and the reducer**

`python/src/beliefs/intents/evidence.py:107-110`: replace the f-string with `value.location.canonical()`:

```python
        return ObservationEvidence(value.location.canonical(), value.event_token)
```

`python/src/beliefs/holdings/rules_v1/holdings.py:14-19`: replace the `"location"` member's expression with a helper placed above `_observation`, keeping every other line byte-identical (cut 10 pins lines in this module):

```python
def _location_key(location):
    if location["type"] == "url":
        return "url:" + location["url"]
    return location["type"] + ":" + location["store_id"] + ":" + location["relative_path"]
```

and `"location": _location_key(location),`. Run the staleness probe named in the global constraints; if a cut-10 `before` string in this module moved, re-target it in `test_n2_cut10.py`'s `_LIVE_SABOTAGES` as Task 1 Step 6 did.

- [ ] **Step 5: The fixture**

Generate the exact canonical projection and payload with a throwaway script (never committed), then write `holdings.url.yaml` from its output on `holdings.basic.yaml`'s shape:

```bash
cd python && uv run --frozen python - <<'EOF'
import json
from nodes.core.frontmatter import to_canonical_json  # the same import test_holdings_reduce.py uses
from beliefs import stored
from beliefs.holdings.records import Found, holdings_observation, url_locator, StoreLocator
url = holdings_observation(location=url_locator("https://example.org/data"), outcome=Found("sha256:" + "11" * 32),
    observer="observer", instrument="instrument", event_token="token-url", observed_at="2026-01-01T00:00:00Z")
store = holdings_observation(location=StoreLocator("d" * 32, "artifact.bin"), outcome=Found("sha256:" + "22" * 32),
    observer="observer", instrument="instrument", event_token="token-store", observed_at="2026-01-01T00:00:00Z")
for uid, rec in (("a" * 32, url), ("b" * 32, store)):
    node = stored.holdings_observation_node(rec).model_copy(update={"uid": uid})
    print(uid, node.id, to_canonical_json(node))
payload = json.dumps({"actor": "actor", "domain": "science.holdings-intent.v1", "event_token": "token-unfulfilled",
    "kind": "re-check", "location": {"type": "url", "url": "https://example.org/other"}}, sort_keys=True, separators=(",", ":")).encode()
print(payload.hex())
EOF
```

The fixture: one corpus, both records, a chain of genesis + the url re-check intent above with **no** registration for it + a registered-and-settled entry publishing both records' paths (the `final` rows as `holdings.basic.yaml` writes them). `expected.active` carries both heads sorted by head reference bytes with `location` `url:https://example.org/data` and `store:dddd…:artifact.bin`; `expected.blocked: []` — the unfulfilled re-check intent is a look that never became a finding, never `unsettled`. Run `uv run --frozen pytest tests/test_holdings_reduce.py tests/test_intents_holdings.py -q`; `test_fixture_records_are_exact_production_canonical_projections` holds the fixture to the codec.

- [ ] **Step 6: Run the tests and the staleness probe**

Run: `cd python && uv run --frozen pytest tests/test_intent_evidence.py tests/test_intents_holdings.py tests/test_holdings_reduce.py tests/test_holdings_receipt.py tests/test_arm_staleness.py -q`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
tasks done beliefs-53b8e8 "url arm in the shared intent shape, the evidence key and the reducer; url fixture"
git add python/src/beliefs/intents python/src/beliefs/holdings python/tests tasks
git commit -m "feat(holdings): url locations in the intent shape, the evidence key and the reducer — BI-9, BI-10"
```

---

### Task 3: The transport

**Files:**
- Create: `python/src/beliefs/holdings/transport.py`, `python/tests/holdings_transport_fixtures.py`, `python/tests/test_holdings_transport.py`

**Interfaces:**
- Consumes: `UrlLocator` (Task 1).
- Produces: `RetrievalBounds(timeout_seconds: float, max_bytes: int, max_redirects: int)`; `UrlSeam(resolve, connect)`; `url_seam() -> UrlSeam`; `Approved(host, port, target, authority, address)`; `preflight(url: str, resolver) -> Approved | Refused`; `REFUSAL_CATEGORIES`; `retrieve(locator, bounds, seam, scratch) -> Retrieved | NotAttempted | Failed`; `refuse_scratch_root(scratch, roots)`; `PinnedHTTPSConnection`, `pinned_connection`, `PinningUnavailable`, `system_resolver`; `TRANSPORT_CATEGORIES = ("timeout", "tls", "connection", "protocol")`. Test fixtures: `Scripted`, `RequestLog`, `ScriptedConnection`, `scripted_seam(script, *, log=None, unpinnable=False) -> (UrlSeam, RequestLog)`; `Served`, `LocalTlsServer(script)` (a context manager with `.port` and `.log`), `tls_seam(server) -> (UrlSeam, RequestLog)`; the certificate files under `python/tests/fixtures/tls/`. Tasks 4, 5, 6 and 8 consume these.

- [ ] **Step 1: The fixtures module**

`python/tests/holdings_transport_fixtures.py`:

First the certificate, generated once and committed (the key is a test-only secret for a name no resolver answers; every test seam's resolver answers `PUBLIC` and the connection dials loopback):

```bash
mkdir -p python/tests/fixtures/tls && cd python/tests/fixtures/tls
openssl req -x509 -newkey rsa:2048 -nodes -keyout server.key -out server.pem -days 36500 \
  -subj "/CN=example.org" -addext "subjectAltName=DNS:example.org,DNS:mirror.example.org,DNS:localhost"
```

Then `python/tests/holdings_transport_fixtures.py`:

```python
"""Two injected transports: a scripted fake, and an in-process TLS server on a
loopback port presenting the committed test certificate. No test reaches the
network: every seam's resolver answers a fixed global address and its
connection dials the fake or the loopback server."""

from __future__ import annotations

import ssl
import threading
from dataclasses import dataclass, field
from http.client import HTTPSConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from beliefs.holdings.transport import Approved, PinnedHTTPSConnection, PinningUnavailable, UrlSeam

PUBLIC = "93.184.216.34"
TLS_DIR = Path(__file__).parent / "fixtures" / "tls"
CERT = TLS_DIR / "server.pem"
KEY = TLS_DIR / "server.key"


@dataclass
class Scripted:
    """One scripted response: status, headers, body chunks; or the exception
    the request or a read raises (`OSError`, `HTTPException`, or anything else
    to prove an unexpected failure propagates)."""

    status: int = 200
    headers: dict[str, str] = field(default_factory=dict)
    chunks: tuple[bytes, ...] = (b"",)
    raise_on_read: BaseException | None = None
    raise_on_request: BaseException | None = None


@dataclass
class RequestLog:
    requests: list[tuple[str, str, dict[str, str]]] = field(default_factory=list)
    dialled: list[tuple[str, str, int]] = field(default_factory=list)
    reads: list[int] = field(default_factory=list)
    """Every `read(size)` the transport asked for, in order."""


class _Response:
    def __init__(self, scripted: Scripted, log: RequestLog) -> None:
        self.status = scripted.status
        self._headers = scripted.headers
        self._pending = b"".join(scripted.chunks)
        self._boundaries = [len(chunk) for chunk in scripted.chunks]
        self._raise = scripted.raise_on_read
        self._log = log

    def getheader(self, name: str) -> str | None:
        for key, value in self._headers.items():
            if key.lower() == name.lower():
                return value
        return None

    def read(self, size: int) -> bytes:
        """Honours `size` like `HTTPResponse.read(amt)`: at most `size` bytes,
        and never past the current scripted chunk, so a test can shape reads."""
        self._log.reads.append(size)
        if self._raise is not None:
            raise self._raise
        if not self._pending:
            return b""
        limit = min(size, self._boundaries[0]) if self._boundaries and self._boundaries[0] else size
        out, self._pending = self._pending[:limit], self._pending[limit:]
        if self._boundaries:
            self._boundaries[0] -= len(out)
            if self._boundaries[0] <= 0:
                self._boundaries.pop(0)
        return out


class ScriptedConnection:
    """Answers each request from `script`, keyed by request target."""

    def __init__(self, approved: Approved, script: dict[str, Scripted], log: RequestLog) -> None:
        self._approved = approved
        self._script = script
        self._log = log
        log.dialled.append((approved.host, approved.address, approved.port))

    def request(self, method: str, target: str, headers: dict[str, str]) -> None:
        self._log.requests.append((method, target, dict(headers)))
        self._target = target
        scripted = self._script[target]
        if scripted.raise_on_request is not None:
            raise scripted.raise_on_request

    def getresponse(self) -> Any:
        return _Response(self._script[self._target], self._log)

    def close(self) -> None:
        pass


def scripted_seam(script: dict[str, Scripted], *, log: RequestLog | None = None, unpinnable: bool = False) -> tuple[UrlSeam, RequestLog]:
    log = RequestLog() if log is None else log

    def connect(approved: Approved, timeout: float) -> Any:
        del timeout
        if unpinnable:
            raise PinningUnavailable("cannot pin the validated address with hostname validation intact")
        return ScriptedConnection(approved, script, log)

    return UrlSeam(resolve=lambda _host, _port: [PUBLIC], connect=connect), log


# --- the in-process TLS server -----------------------------------------------


@dataclass
class Served:
    """One response the local server sends. `truncate_chunked` announces a
    chunked body, sends part of one chunk and closes: the client's read raises
    `http.client.IncompleteRead`. A `Content-Length` that disagrees with the
    body is sent as written and the connection closed after the body."""

    status: int = 200
    headers: dict[str, str] = field(default_factory=dict)
    body: bytes = b""
    truncate_chunked: bool = False


class LocalTlsServer:
    """An HTTPS server on `127.0.0.1:<free port>` presenting `CERT`; it records
    every request it parses into `self.log` exactly as received."""

    def __init__(self, script: dict[str, Served]) -> None:
        self.log = RequestLog()
        log = self.log

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *_args: Any) -> None:
                pass

            def do_GET(self) -> None:
                log.requests.append(("GET", self.path, {key: value for key, value in self.headers.items()}))
                served = script.get(self.path)
                if served is None:
                    self.send_response(404)
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                    return
                self.send_response(served.status)
                if served.truncate_chunked:
                    self.send_header("Transfer-Encoding", "chunked")
                    self.end_headers()
                    self.wfile.write(f"{len(served.body) + 16:x}\r\n".encode() + served.body)
                    self.wfile.flush()
                    self.close_connection = True
                    return
                for key, value in served.headers.items():
                    self.send_header(key, value)
                declared = served.headers.get("Content-Length")
                if declared is None:
                    self.send_header("Content-Length", str(len(served.body)))
                elif declared != str(len(served.body)):
                    self.close_connection = True
                self.end_headers()
                self.wfile.write(served.body)

        class Server(ThreadingHTTPServer):
            daemon_threads = True

            def handle_error(self, request: Any, client_address: Any) -> None:
                pass  # a client that rejects the certificate is a test's expected outcome

        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(str(CERT), str(KEY))
        self._server = Server(("127.0.0.1", 0), Handler)
        self._server.socket = context.wrap_socket(self._server.socket, server_side=True)
        self.port: int = self._server.server_address[1]
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    def __enter__(self) -> LocalTlsServer:
        self._thread.start()
        return self

    def __exit__(self, *_exc: object) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(5)


def tls_seam(server: LocalTlsServer) -> tuple[UrlSeam, RequestLog]:
    """The production pinned connection over the local server: the resolver
    answers a global address for every name, the connection dials loopback on
    the server's port with `server_hostname` the approved name, and the context
    trusts `CERT` with `check_hostname` and `CERT_REQUIRED` intact — a name the
    certificate does not carry fails the handshake."""
    context = ssl.create_default_context(cafile=str(CERT))
    assert context.check_hostname and context.verify_mode == ssl.CERT_REQUIRED
    log = server.log

    def connect(approved: Approved, timeout: float) -> HTTPSConnection:
        log.dialled.append((approved.host, approved.address, approved.port))
        return PinnedHTTPSConnection(approved.host, "127.0.0.1", server.port, timeout, context)

    return UrlSeam(resolve=lambda _host, _port: [PUBLIC], connect=connect), log
```

`PinnedHTTPSConnection`'s `port` is the port it dials (`self.port` in `connect`); the `Host` header is the one `retrieve` sends explicitly, so the server sees the canonical authority while the socket goes to its own port.

- [ ] **Step 2: The failing tests**

`python/tests/test_holdings_transport.py`:

```python
"""The URL dereference boundary: preflight, the pinned connection, the fetch."""

from __future__ import annotations

import socket
import ssl
from hashlib import sha256
from http.client import BadStatusLine, IncompleteRead
from pathlib import Path
from typing import Any

import pytest
from holdings_transport_fixtures import PUBLIC, LocalTlsServer, RequestLog, Scripted, Served, scripted_seam, tls_seam

from beliefs.errors import MalformedRecord
from beliefs.holdings import transport
from beliefs.holdings.records import url_locator
from beliefs.holdings.transport import (
    Approved,
    Failed,
    NotAttempted,
    PinnedHTTPSConnection,
    PinningUnavailable,
    Retrieved,
    RetrievalBounds,
    pinned_connection,
    preflight,
    refuse_scratch_root,
    retrieve,
)

BOUNDS = RetrievalBounds(timeout_seconds=5.0, max_bytes=64, max_redirects=3)
DATA = url_locator("https://example.org/data")
SIGNED_HOP = "https://bucket.s3.example/data?X-Amz-Signature=deadbeefcafe&X-Amz-Credential=AKIA"
TOKEN_HOST_HOP = "https://tok3n-9f2a.example.net/data"


def ok(body: bytes, **headers: str) -> Scripted:
    return Scripted(200, {"Content-Length": str(len(body)), **headers}, (body,))


def fetch(script, locator=DATA, bounds=BOUNDS, tmp_path=None, **seam_kwargs):
    seam, log = scripted_seam(script, **seam_kwargs)
    return retrieve(locator, bounds, seam, tmp_path), log


# --- preflight ---------------------------------------------------------------


@pytest.mark.parametrize("url,category", [("http://example.org/", "scheme"), ("https://example.org/", "unresolvable")])
def test_preflight_refuses_with_a_category(url, category):
    def failing(_host, _port):
        raise OSError("no such host")

    decision = preflight(url, failing)
    assert decision == transport.Refused(category)


def test_preflight_refuses_a_non_public_address():
    assert preflight("https://example.org/", lambda _h, _p: ["10.0.0.7"]) == transport.Refused("non-public-address")
    assert preflight("https://example.org/", lambda _h, _p: []) == transport.Refused("unresolvable")


def test_preflight_approves_with_the_faithful_target_and_authority():
    approved = preflight("https://example.org:8443/data?", lambda _h, _p: [PUBLIC])
    assert approved == Approved(host="example.org", port=8443, target="/data?", authority="example.org:8443", address=PUBLIC)
    assert preflight("https://example.org/a/b/", lambda _h, _p: [PUBLIC]).authority == "example.org"


# --- the request as sent -----------------------------------------------------


def test_the_request_transmits_the_canonical_locator_faithfully(tmp_path):
    result, log = fetch({"/data?": ok(b"x")}, url_locator("https://example.org:8443/data?"), tmp_path=tmp_path)
    assert isinstance(result, Retrieved)
    (method, target, headers), = log.requests
    assert (method, target) == ("GET", "/data?")
    assert headers["Host"] == "example.org:8443"
    assert headers["Accept-Encoding"] == "identity"
    result, log = fetch({"/a/b/": ok(b"x")}, url_locator("https://example.org/a/./b/"), tmp_path=tmp_path)
    assert log.requests[0][1] == "/a/b/" and log.requests[0][2]["Host"] == "example.org"


# --- the pinned connection ---------------------------------------------------


def test_the_pinned_connection_dials_the_validated_address_and_validates_the_name(monkeypatch):
    dialled: list[tuple[str, int]] = []
    wrapped: list[str] = []
    sentinel = object()

    class FakeContext:
        check_hostname = True
        verify_mode = ssl.CERT_REQUIRED

        def wrap_socket(self, sock: Any, *, server_hostname: str) -> Any:
            assert sock is sentinel
            wrapped.append(server_hostname)
            return sentinel

    monkeypatch.setattr(transport.socket, "create_connection", lambda address, timeout: dialled.append(address) or sentinel)
    connection = PinnedHTTPSConnection("host.example", PUBLIC, 443, 5.0, FakeContext())
    connection.connect()
    assert dialled == [(PUBLIC, 443)]
    assert wrapped == ["host.example"]


@pytest.mark.parametrize("check_hostname,verify_mode", [(False, ssl.CERT_REQUIRED), (True, ssl.CERT_NONE)])
def test_a_context_that_would_skip_validation_refuses_to_pin(monkeypatch, check_hostname, verify_mode):
    class Lax:
        pass

    context = Lax()
    context.check_hostname = check_hostname  # type: ignore[attr-defined]
    context.verify_mode = verify_mode  # type: ignore[attr-defined]
    monkeypatch.setattr(transport.ssl, "create_default_context", lambda: context)
    with pytest.raises(PinningUnavailable):
        pinned_connection(Approved("host.example", 443, "/a", "host.example", PUBLIC), 5.0)


def test_an_unpinnable_context_issues_no_request(tmp_path, monkeypatch):
    monkeypatch.setattr(transport.socket, "create_connection", lambda *a, **k: pytest.fail("a socket was opened"))
    result, log = fetch({"/data": ok(b"x")}, tmp_path=tmp_path, unpinnable=True)
    assert result == NotAttempted("unpinnable")
    assert log.requests == []


# --- redirects ---------------------------------------------------------------


def test_a_relative_location_is_joined_before_it_is_revalidated(tmp_path):
    result, log = fetch({"/data": Scripted(302, {"Location": "/moved"}), "/moved": ok(b"body")}, tmp_path=tmp_path)
    assert isinstance(result, Retrieved)
    assert [target for _m, target, _h in log.requests] == ["/data", "/moved"]


@pytest.mark.parametrize("hop", [SIGNED_HOP, TOKEN_HOST_HOP])
def test_a_refused_hop_is_failed_by_ordinal_and_category_and_never_by_its_bytes(tmp_path, hop):
    seam, log = scripted_seam({"/data": Scripted(302, {"Location": hop})})
    private = transport.UrlSeam(resolve=lambda host, _p: ["10.1.1.1"] if host != "example.org" else [PUBLIC], connect=seam.connect)
    result = retrieve(DATA, BOUNDS, private, tmp_path)
    assert result == Failed("redirect hop 1 refused: non-public-address")
    for secret in ("X-Amz-Signature", "deadbeefcafe", "AKIA", "tok3n-9f2a", "s3.example", "example.net"):
        assert secret not in result.reason
    assert len(log.requests) == 1


def test_too_many_redirects_is_failed_naming_the_bound(tmp_path):
    script = {f"/h{i}": Scripted(302, {"Location": f"/h{i + 1}"}) for i in range(6)}
    script["/data"] = Scripted(302, {"Location": "/h0"})
    result, _ = fetch(script, tmp_path=tmp_path)
    assert result == Failed("redirect limit 3 exceeded")


def test_a_redirect_without_a_location_is_failed(tmp_path):
    result, _ = fetch({"/data": Scripted(302, {})}, tmp_path=tmp_path)
    assert result == Failed("redirect without a location")


# --- the body ----------------------------------------------------------------


@pytest.mark.parametrize(
    "scripted,reason",
    [
        (Scripted(404, {}, (b"",)), "status 404"),
        (Scripted(500, {}, (b"",)), "status 500"),
        (Scripted(200, {"Content-Length": "4", "Content-Encoding": "gzip"}, (b"abcd",)), "content-encoding gzip is not identity"),
        (Scripted(200, {"Content-Length": "8"}, (b"abcd",)), "body shorter than content-length 8"),
        (Scripted(200, {"Content-Length": "2"}, (b"abcd",)), "body longer than content-length 2"),
        (Scripted(200, {}, (b"ab",), raise_on_read=socket.timeout("timed out")), "transport failure: timeout"),
    ],
)
def test_an_incomplete_or_wrong_body_is_failed_carrying_no_digest(tmp_path, scripted, reason):
    result, _ = fetch({"/data": scripted}, tmp_path=tmp_path)
    assert result == Failed(reason)
    assert not hasattr(result, "digest")
    assert list(tmp_path.iterdir()) == []


def test_the_ceiling_ends_the_stream_and_finalizes_no_digest(tmp_path):
    body = b"x" * 65
    result, log = fetch({"/data": Scripted(200, {}, (body[:32], body[32:]))}, tmp_path=tmp_path)
    assert result == Failed("exceeded the 64-byte streaming ceiling")
    assert log.reads == [65, 33]  # each read asks for the remaining allowance plus one
    assert list(tmp_path.iterdir()) == []


def test_each_read_is_bounded_by_the_remaining_allowance_plus_one(tmp_path):
    result, log = fetch({"/data": Scripted(200, {}, (b"y" * 1000,))}, tmp_path=tmp_path)
    assert result == Failed("exceeded the 64-byte streaming ceiling")
    assert log.reads == [65]  # one read of 65 bytes, never 1 MiB against a 64-byte ceiling


@pytest.mark.parametrize(
    "raised,category",
    [
        (socket.timeout("timed out"), "timeout"),
        (TimeoutError("timed out"), "timeout"),
        (ssl.SSLCertVerificationError("hostname 'tok3n-9f2a.example.net' doesn't match"), "tls"),
        (ssl.SSLError(1, "tlsv1 alert"), "tls"),
        (ConnectionResetError("peer reset"), "connection"),
        (IncompleteRead(b"ab", 6), "protocol"),
        (BadStatusLine("garbage"), "protocol"),
    ],
)
def test_a_transport_failure_is_failed_by_category_and_leaves_no_scratch(tmp_path, raised, category):
    result, _ = fetch({"/data": Scripted(200, {}, (b"ab",), raise_on_read=raised)}, tmp_path=tmp_path)
    assert result == Failed(f"transport failure: {category}")
    assert list(tmp_path.iterdir()) == []
    result, log = fetch({"/data": Scripted(raise_on_request=raised)}, tmp_path=tmp_path)
    assert result == Failed(f"transport failure: {category}")
    assert "tok3n" not in result.reason and "example.net" not in result.reason and "peer" not in result.reason
    assert len(log.requests) == 1


def test_a_programming_failure_mid_stream_raises_and_leaves_no_scratch(tmp_path):
    with pytest.raises(RuntimeError, match="boom"):
        fetch({"/data": Scripted(200, {}, (b"ab",), raise_on_read=RuntimeError("boom"))}, tmp_path=tmp_path)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("timeout", [float("inf"), float("nan"), 0, -1.0, True])
def test_bounds_refuse_a_non_finite_or_non_positive_timeout(timeout):
    with pytest.raises(MalformedRecord):
        RetrievalBounds(timeout_seconds=timeout, max_bytes=1, max_redirects=0)


def test_a_complete_body_is_retrieved_with_its_digest_and_scratch_path(tmp_path):
    result, _ = fetch({"/data": ok(b"payload")}, tmp_path=tmp_path)
    assert isinstance(result, Retrieved)
    assert result.digest == "sha256:" + sha256(b"payload").hexdigest()
    assert result.size == 7
    assert result.path.parent == tmp_path and result.path.read_bytes() == b"payload"


def test_the_scratch_root_refuses_the_roots_and_their_descendants(tmp_path):
    (tmp_path / "observer").mkdir()
    for scratch in (tmp_path / "observer", tmp_path / "observer" / "tmp"):
        with pytest.raises(MalformedRecord):
            refuse_scratch_root(scratch, (tmp_path / "observer", tmp_path / "store"))
    refuse_scratch_root(tmp_path / "scratch", (tmp_path / "observer", tmp_path / "store"))


# --- the in-process TLS server: real framing, real reads, real validation ------


def test_over_tls_a_complete_body_is_retrieved_and_the_request_arrives_faithfully(tmp_path):
    with LocalTlsServer({"/data?": Served(body=b"payload")}) as server:
        seam, log = tls_seam(server)
        result = retrieve(url_locator("https://example.org:8443/data?"), BOUNDS, seam, tmp_path)
    assert isinstance(result, Retrieved)
    assert result.digest == "sha256:" + sha256(b"payload").hexdigest() and result.size == 7
    ((method, target, headers),) = log.requests
    assert (method, target, headers["Host"], headers["Accept-Encoding"]) == ("GET", "/data?", "example.org:8443", "identity")
    assert log.dialled == [("example.org", PUBLIC, 8443)]
    result.path.unlink()


def test_over_tls_a_truncated_chunked_body_is_a_protocol_failure_with_no_scratch(tmp_path):
    with LocalTlsServer({"/data": Served(body=b"partial", truncate_chunked=True)}) as server:
        seam, _ = tls_seam(server)
        result = retrieve(DATA, BOUNDS, seam, tmp_path)
    assert result == Failed("transport failure: protocol")
    assert list(tmp_path.iterdir()) == []


def test_over_tls_a_redirect_is_followed_and_each_hop_revalidated(tmp_path):
    script = {"/data": Served(302, {"Location": "https://mirror.example.org/moved"}), "/moved": Served(body=b"moved")}
    with LocalTlsServer(script) as server:
        seam, log = tls_seam(server)
        result = retrieve(DATA, BOUNDS, seam, tmp_path)
    assert isinstance(result, Retrieved) and result.size == 5
    assert [(target, headers["Host"]) for _m, target, headers in log.requests] == [("/data", "example.org"), ("/moved", "mirror.example.org")]
    assert [host for host, _a, _p in log.dialled] == ["example.org", "mirror.example.org"]
    result.path.unlink()


def test_over_tls_the_ceiling_ends_the_stream_one_byte_past_the_bound(tmp_path):
    with LocalTlsServer({"/data": Served(body=b"z" * 4096)}) as server:
        seam, _ = tls_seam(server)
        result = retrieve(DATA, BOUNDS, seam, tmp_path)
    assert result == Failed("exceeded the 64-byte streaming ceiling")
    assert list(tmp_path.iterdir()) == []


def test_over_tls_a_certificate_failure_after_a_credential_bearing_redirect_names_only_its_category(tmp_path):
    with LocalTlsServer({"/data": Served(302, {"Location": TOKEN_HOST_HOP})}) as server:
        seam, log = tls_seam(server)
        result = retrieve(DATA, BOUNDS, seam, tmp_path)
    assert result == Failed("transport failure: tls")
    assert "tok3n-9f2a" not in result.reason and "example.net" not in result.reason
    assert len(log.requests) == 1  # the second hop's handshake never completed, so the server parsed no request
    assert [host for host, _a, _p in log.dialled] == ["example.org", "tok3n-9f2a.example.net"]
```

- [ ] **Step 3: Run them to verify they fail**

Run: `cd python && uv run --frozen pytest tests/test_holdings_transport.py -q`
Expected: FAIL at import — `beliefs.holdings.transport` does not exist.

- [ ] **Step 4: The transport**

`python/src/beliefs/holdings/transport.py`:

```python
"""The URL dereference boundary (url-retrieval design §4).

The survey instrument's preflight, pinned connection and streaming fetch,
made total over an injectable seam: `retrieve` answers with the **phase** the
look classifies from and never raises for a resolution, transport, status or
bound condition. Nothing here reads the network unless the production seam is
supplied; every test injects a scripted one.
"""

from __future__ import annotations

import hashlib
import ipaddress
import math
import socket
import ssl
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from http.client import HTTPException, HTTPSConnection
from pathlib import Path
from typing import Any, final
from urllib.parse import urljoin, urlsplit

from beliefs.errors import MalformedRecord
from beliefs.holdings.records import UrlLocator
from beliefs.sealed import sealed

__all__ = [
    "REFUSAL_CATEGORIES",
    "TRANSPORT_CATEGORIES",
    "Approved",
    "Failed",
    "NotAttempted",
    "PinnedHTTPSConnection",
    "PinningUnavailable",
    "Refused",
    "Retrieved",
    "RetrievalBounds",
    "UrlSeam",
    "pinned_connection",
    "preflight",
    "refuse_scratch_root",
    "retrieve",
    "system_resolver",
    "url_seam",
]

CHUNK = 1024 * 1024
REDIRECTS = (301, 302, 303, 307, 308)
REFUSAL_CATEGORIES = ("scheme", "no-host", "unresolvable", "non-public-address", "unpinnable")
"""The closed set a refused hop is named by (decision 6); never a host, never bytes."""
TRANSPORT_CATEGORIES = ("timeout", "tls", "connection", "protocol")
"""The closed set a failure after the request began is named by; never the exception's text,
which for a certificate error carries the redirected host."""

Resolver = Callable[[str, int], list[str]]
ConnectionFactory = Callable[["Approved", float], HTTPSConnection]


@sealed
@final
@dataclass(frozen=True)
class RetrievalBounds:
    timeout_seconds: float
    max_bytes: int
    max_redirects: int

    def __post_init__(self) -> None:
        if (
            not isinstance(self.timeout_seconds, (int, float))
            or isinstance(self.timeout_seconds, bool)
            or not math.isfinite(self.timeout_seconds)
            or self.timeout_seconds <= 0
        ):
            raise MalformedRecord("timeout_seconds must be a finite positive number")
        for name in ("max_bytes", "max_redirects"):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise MalformedRecord(f"{name} must be a non-negative integer")

    def instrument_inputs(self) -> tuple[tuple[str, str], ...]:
        return (
            ("timeout_seconds", repr(float(self.timeout_seconds))),
            ("max_bytes", str(self.max_bytes)),
            ("max_redirects", str(self.max_redirects)),
        )


@dataclass(frozen=True)
class Approved:
    """A hop that cleared preflight: the address validated, the request as it will be sent."""

    host: str
    port: int
    target: str
    authority: str
    address: str


@dataclass(frozen=True)
class Refused:
    category: str


@sealed
@final
@dataclass(frozen=True)
class Retrieved:
    digest: str
    size: int
    path: Path


@sealed
@final
@dataclass(frozen=True)
class NotAttempted:
    reason: str


@sealed
@final
@dataclass(frozen=True)
class Failed:
    reason: str


@dataclass(frozen=True)
class UrlSeam:
    resolve: Resolver
    connect: ConnectionFactory


class PinningUnavailable(RuntimeError):
    """The validated address cannot be used with name validation intact; no request is issued."""


def _transport_category(caught: OSError | HTTPException) -> str:
    """The fixed name a failure after the request began is reported by. Order
    matters: `socket.timeout` is a `TimeoutError` is an `OSError`; `ssl.SSLError`
    is an `OSError`; `RemoteDisconnected` is both an `OSError` and an `HTTPException`."""
    if isinstance(caught, TimeoutError):
        return "timeout"
    if isinstance(caught, ssl.SSLError):
        return "tls"
    if isinstance(caught, OSError):
        return "connection"
    return "protocol"


def system_resolver(host: str, port: int) -> list[str]:
    infos = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
    return [str(info[4][0]) for info in infos]


class PinnedHTTPSConnection(HTTPSConnection):
    """Dials the validated address; keeps `host` as the name so SNI and the certificate validate against it."""

    def __init__(self, host: str, address: str, port: int, timeout: float, context: ssl.SSLContext) -> None:
        super().__init__(host, port=port, timeout=timeout, context=context)
        self._address = address
        self._pinned_context = context

    def connect(self) -> None:
        sock = socket.create_connection((self._address, self.port), self.timeout)
        self.sock = self._pinned_context.wrap_socket(sock, server_hostname=self.host)


def pinned_connection(approved: Approved, timeout: float) -> HTTPSConnection:
    context = ssl.create_default_context()
    if not context.check_hostname or context.verify_mode != ssl.CERT_REQUIRED:
        raise PinningUnavailable("cannot pin the validated address with hostname validation intact")
    return PinnedHTTPSConnection(approved.host, approved.address, approved.port, timeout, context)


def url_seam() -> UrlSeam:
    """The production seam: the system resolver and the pinned TLS connection."""
    return UrlSeam(resolve=system_resolver, connect=pinned_connection)


def preflight(url: str, resolver: Resolver) -> Approved | Refused:
    """Decide whether a hop may be requested at all; every refusal is a fixed category."""
    parts = urlsplit(url)
    if parts.scheme != "https":
        return Refused("scheme")
    if not parts.hostname:
        return Refused("no-host")
    try:
        port = 443 if parts.port is None else parts.port  # an explicit port is sent as given, `0` included
        addresses = resolver(parts.hostname, port)
    except (OSError, ValueError):
        return Refused("unresolvable")
    if not addresses:
        return Refused("unresolvable")
    if any(not ipaddress.ip_address(address).is_global for address in addresses):
        return Refused("non-public-address")
    target = (parts.path or "/") + ("?" + parts.query if "?" in url.split("#", 1)[0] else "")
    authority = parts.hostname if port == 443 else f"{parts.hostname}:{port}"
    return Approved(host=parts.hostname, port=port, target=target, authority=authority, address=addresses[0])


def refuse_scratch_root(scratch: Path, roots: tuple[Path, ...]) -> None:
    resolved = Path(scratch).resolve()
    for root in roots:
        bound = Path(root).resolve()
        if resolved == bound or bound in resolved.parents:
            raise MalformedRecord(f"scratch root {str(scratch)!r} lies under a corpus or store root {str(root)!r}")


def retrieve(locator: UrlLocator, bounds: RetrievalBounds, seam: UrlSeam, scratch: Path) -> Retrieved | NotAttempted | Failed:
    """One GET of the declared URL, every hop revalidated, the body streamed to scratch and hashed as it arrives."""
    if type(locator) is not UrlLocator:
        raise MalformedRecord("retrieve takes a UrlLocator")
    current = locator.url
    for hop in range(bounds.max_redirects + 1):
        decision = preflight(current, seam.resolve)
        if isinstance(decision, Refused):
            if hop == 0:
                return NotAttempted(decision.category)
            return Failed(f"redirect hop {hop} refused: {decision.category}")
        try:
            connection = seam.connect(decision, bounds.timeout_seconds)
        except PinningUnavailable:
            return NotAttempted("unpinnable") if hop == 0 else Failed(f"redirect hop {hop} refused: unpinnable")
        try:
            try:
                connection.request(
                    "GET", decision.target, headers={"Host": decision.authority, "Accept-Encoding": "identity"}
                )
                response = connection.getresponse()
            except (OSError, HTTPException) as caught:
                return Failed(f"transport failure: {_transport_category(caught)}")
            if response.status in REDIRECTS:
                location = response.getheader("Location")
                if not location:
                    return Failed("redirect without a location")
                current = urljoin(current, location)
                continue
            if response.status != 200:
                return Failed(f"status {response.status}")
            encoding = response.getheader("Content-Encoding")
            if encoding is not None and encoding.strip().lower() != "identity":
                return Failed(f"content-encoding {encoding.strip().lower()} is not identity")
            return _stream(response, response.getheader("Content-Length"), bounds, scratch)
        finally:
            connection.close()
    return Failed(f"redirect limit {bounds.max_redirects} exceeded")


def _stream(response: Any, declared_length: str | None, bounds: RetrievalBounds, scratch: Path) -> Retrieved | Failed:
    scratch.mkdir(parents=True, exist_ok=True)
    target = scratch / f"retrieve-{datetime.now(UTC).strftime('%Y%m%dT%H%M%S%f')}-{id(response)}"
    try:
        outcome = _stream_into(response, declared_length, bounds, target)
    except BaseException:
        target.unlink(missing_ok=True)  # an unexpected failure propagates, and leaves no scratch file behind
        raise
    if isinstance(outcome, Failed):
        target.unlink(missing_ok=True)
    return outcome


def _stream_into(response: Any, declared_length: str | None, bounds: RetrievalBounds, target: Path) -> Retrieved | Failed:
    hasher = hashlib.sha256()
    size = 0
    with target.open("wb") as handle:
        while True:
            try:
                chunk = response.read(min(CHUNK, bounds.max_bytes - size + 1))  # never past the ceiling plus one
            except (OSError, HTTPException) as caught:
                return Failed(f"transport failure: {_transport_category(caught)}")
            if not chunk:
                break
            size += len(chunk)
            if size > bounds.max_bytes:
                return Failed(f"exceeded the {bounds.max_bytes}-byte streaming ceiling")
            hasher.update(chunk)
            handle.write(chunk)
    if declared_length is not None:
        try:
            expected = int(declared_length)
        except ValueError:
            return Failed("malformed content-length")
        if size < expected:
            return Failed(f"body shorter than content-length {expected}")
        if size > expected:
            return Failed(f"body longer than content-length {expected}")
    return Retrieved(digest=f"sha256:{hasher.hexdigest()}", size=size, path=target)
```

The running hash of an incomplete body is dropped with the `Failed` (decision 7); add `(Scripted(200, {"Content-Length": "many"}, (b"ab",)), "malformed content-length")` to the parametrized body test.

- [ ] **Step 5: Run the tests**

Run: `cd python && uv run --frozen pytest tests/test_holdings_transport.py -q && uv run --frozen ruff check src/beliefs/holdings/transport.py tests/holdings_transport_fixtures.py tests/test_holdings_transport.py && uv run --frozen pyright src/beliefs/holdings/transport.py`
Expected: PASS, clean.

- [ ] **Step 6: Commit**

```bash
tasks done beliefs-8831ed "the URL transport behind a seam: preflight categories, faithful request, pinned TLS, no digest for an incomplete body"
git add python/src/beliefs/holdings/transport.py python/tests/holdings_transport_fixtures.py python/tests/test_holdings_transport.py tasks
git commit -m "feat(holdings): the URL transport seam — BI-2, BI-3, BI-4"
```

---

### Task 4: The URL look, and the store refusal classified by phase and cause

**Files:**
- Modify: `python/src/beliefs/holdings/boundary.py` (`intent_payload`, `_append` over `Locator`; `look`, `PublishedLook`, `InconclusiveLook`; `store_refusal`; `write`'s wrap), `python/src/beliefs/errors.py` (`StoreWriteRefused` after `AcquisitionBoundaryRefused`, line 1468)
- Test: `python/tests/test_holdings_boundary.py`, `python/tests/test_intent_evidence.py` (swap the hand-built payload for `intent_payload`)

**Interfaces:**
- Consumes: `UrlLocator`, `Locator` (Task 1); `RetrievalBounds`, `UrlSeam`, `retrieve`, `Retrieved`, `NotAttempted`, `Failed`, `refuse_scratch_root` (Task 3); `scripted_seam` (Task 3 fixtures).
- Produces: `intent_payload(*, location: Locator, act_kind, event_token, actor) -> bytes`; `look(ctx, location: UrlLocator, *, bounds, seam, scratch, expected=None, standing=()) -> PublishedLook | InconclusiveLook`; `PublishedLook(record, ref, retrieved)`; `InconclusiveLook(report, reason)`; `store_refusal(caught: ExecutionError) -> bool`; `errors.StoreWriteRefused(location: str, detail: str)`. Task 5 consumes all of these.

- [ ] **Step 1: The failing tests**

Append to `python/tests/test_holdings_boundary.py` (add the imports `from holdings_transport_fixtures import Scripted, scripted_seam`, `from beliefs.errors import StoreWriteRefused`, `from beliefs.holdings.boundary import InconclusiveLook, PublishedLook, look, store_refusal`, `from beliefs.holdings.records import url_locator`, `from beliefs.holdings.transport import RetrievalBounds`, and from the engine `from atoms.core.errors import PreconditionRefused, ProjectApprovalRefused, SpecValidationError, CapabilityUnavailable` and `from atoms.chain.errors import ChainStateInvalid, PendingUnresolved, TransactionHalted` — take each name from the module `root.py` imports it from, lines 37 and 100–112):

```python
BOUNDS = RetrievalBounds(timeout_seconds=5.0, max_bytes=1 << 20, max_redirects=3)
DATA = url_locator("https://example.org/data")


def _intents(root):
    view = science_root._log_seam().inspect_registered(root)
    assert isinstance(view, WellFormedView)
    return [entry for entry in view.entries if isinstance(entry, IntentEntryView)]


def test_intent_payload_spells_the_url_arm():
    payload = json.loads(intent_payload(location=DATA, act_kind="re-check", event_token="t", actor=ACTOR))
    assert payload["location"] == {"type": "url", "url": "https://example.org/data"}


def test_a_url_look_appends_a_recheck_intent_and_publishes_found_fulfilling_it(certified_work, tmp_path):
    ctx, _ = context(certified_work)
    seam, log = scripted_seam({"/data": Scripted(200, {"Content-Length": "7"}, (b"payload",))})
    result = look(ctx, DATA, bounds=BOUNDS, seam=seam, scratch=tmp_path / "scratch")
    assert isinstance(result, PublishedLook)
    assert result.record.outcome == Found("sha256:" + sha256(b"payload").hexdigest())
    assert result.ref == f"holdings-observation:{result.record.identity()}"
    assert result.retrieved.path.read_bytes() == b"payload"
    (intent,) = _intents(ctx.observer_root)
    assert json.loads(intent.payload)["kind"] == "re-check"
    assert json.loads(intent.payload)["location"] == {"type": "url", "url": "https://example.org/data"}
    assert json.loads(intent.payload)["event_token"] == result.record.event_token
    assert len(log.requests) == 1
    result.retrieved.path.unlink()


def test_an_inconclusive_url_look_mints_nothing_and_leaves_the_standing_observation(certified_work, tmp_path):
    ctx, _ = context(certified_work)
    seam, _ = scripted_seam({"/data": Scripted(200, {"Content-Length": "7"}, (b"payload",))})
    standing = look(ctx, DATA, bounds=BOUNDS, seam=seam, scratch=tmp_path / "s")
    assert isinstance(standing, PublishedLook)
    standing.retrieved.path.unlink()
    identity = standing.record.identity()
    failing, _ = scripted_seam({"/data": Scripted(404, {}, (b"",))})
    result = look(ctx, DATA, bounds=BOUNDS, seam=failing, scratch=tmp_path / "s", standing=(standing.record,))
    assert result == InconclusiveLook("retrieval-failed", "status 404")
    assert standing.record.identity() == identity
    assert len(list((ctx.observer_root / "holdings-observation").iterdir())) == 1
    assert len(_intents(ctx.observer_root)) == 2
    untested, _ = scripted_seam({}, unpinnable=True)
    assert look(ctx, DATA, bounds=BOUNDS, seam=untested, scratch=tmp_path / "s") == InconclusiveLook("byte-locator-untested", "unpinnable")


def test_a_url_look_that_established_found_but_cannot_publish_raises(certified_work, tmp_path):
    ctx, _ = context(certified_work)

    def raise_publish(_root, _plan, _fulfills):
        raise ExecutionError("cannot publish", index=None, applied=0)

    ctx = replace(ctx, seam=replace(ctx.seam, publish_fulfilling=raise_publish))
    seam, _ = scripted_seam({"/data": Scripted(200, {"Content-Length": "1"}, (b"x",))})
    with pytest.raises(ExecutionError, match="cannot publish"):
        look(ctx, DATA, bounds=BOUNDS, seam=seam, scratch=tmp_path / "s")
    assert not (ctx.observer_root / "holdings-observation").exists()
    assert len(_intents(ctx.observer_root)) == 1
    assert list((tmp_path / "s").iterdir()) == []  # the retrieved file never reached a caller who could delete it


def test_a_url_look_refuses_a_scratch_root_under_either_root_before_any_intent(certified_work):
    ctx, _ = context(certified_work)
    seam, log = scripted_seam({"/data": Scripted(200, {"Content-Length": "1"}, (b"x",))})
    for scratch in (ctx.observer_root, ctx.observer_root / "scratch", ctx.store_root, ctx.store_root / "deep" / "er"):
        with pytest.raises(MalformedRecord, match="scratch root"):
            look(ctx, DATA, bounds=BOUNDS, seam=seam, scratch=scratch)
    assert _intents(ctx.observer_root) == [] and log.requests == []


def test_a_url_look_with_a_non_sha256_expectation_refuses_before_the_intent(certified_work, tmp_path):
    ctx, _ = context(certified_work)
    seam, log = scripted_seam({})
    with pytest.raises(MalformedRecord):
        look(ctx, DATA, bounds=BOUNDS, seam=seam, scratch=tmp_path / "s", expected="md5:" + "ab" * 16)
    assert _intents(ctx.observer_root) == [] and log.requests == []


@pytest.mark.parametrize(
    "cause,applied,routine",
    [
        (ProjectApprovalRefused("root not writable"), 0, True),
        (PreconditionRefused("precondition"), 0, True),
        (PendingUnresolved("pending"), 0, True),
        (SpecValidationError("spec"), 0, False),
        (CapabilityUnavailable("capability"), 0, False),
        (ChainStateInvalid("chain"), None, False),
        (TransactionHalted("halted"), None, False),
        (RuntimeError("internal"), None, False),
        (ProjectApprovalRefused("wrong applied"), None, False),
        (None, 0, False),
    ],
)
def test_store_refusal_is_true_for_exactly_the_routine_causes(cause, applied, routine):
    error = ExecutionError("mapped", index=None, applied=applied)
    error.__cause__ = cause
    assert store_refusal(error) is routine


def test_write_wraps_a_routine_store_refusal_and_nothing_else(certified_work):
    ctx, store_id = context(certified_work)

    def refusing(_root, _path, _content):
        raise ExecutionError("refused", index=None, applied=0) from ProjectApprovalRefused("read-only")

    with pytest.raises(StoreWriteRefused) as caught:
        write(replace(ctx, seam=replace(ctx.seam, store_write=refusing)), StoreLocator(store_id, "held.bin"), b"x")
    assert caught.value.location == f"store:{store_id}:held.bin"
    assert isinstance(caught.value.__cause__, ExecutionError)

    def internal(_root, _path, _content):
        raise ExecutionError("internal", index=None, applied=None) from RuntimeError("boom")

    with pytest.raises(ExecutionError, match="internal"):
        write(replace(ctx, seam=replace(ctx.seam, store_write=internal)), StoreLocator(store_id, "held.bin"), b"x")

    def refusing_publish(_root, _plan, _fulfills):
        raise ExecutionError("publish", index=None, applied=0) from PreconditionRefused("shape")

    with pytest.raises(ExecutionError, match="publish"):
        write(replace(ctx, seam=replace(ctx.seam, publish_fulfilling=refusing_publish)), StoreLocator(store_id, "held2.bin"), b"x")


def test_write_against_a_read_only_replica_raises_store_write_refused_from_the_production_seam(certified_work):
    ctx, store_id = context(certified_work)
    ctx.seam.store_write(ctx.store_root, "held.bin", b"payload")
    replica = certified_work / "replica"
    replicate_root(ctx.store_root, replica, authority=FULL)
    assert read_lifecycle_state(replica) in (LifecycleState.METADATA_LESS, LifecycleState.READ_ONLY_UNSERVICEABLE, LifecycleState.READ_ONLY)
    with pytest.raises(StoreWriteRefused) as caught:
        write(replace(ctx, store_root=replica), StoreLocator(store_id, "held.bin"), b"other")
    cause = caught.value.__cause__
    assert isinstance(cause, ExecutionError) and cause.applied == 0
    assert isinstance(cause.__cause__, ProjectApprovalRefused)
```

If `replicate_root` yields a state the engine refuses with a cause other than `ProjectApprovalRefused` (read it from the failure), the last test asserts the cause the engine actually raises **if it is in the routine set**; if the engine's refusal for that state is not routine, use `restore_root` as `test_recheck_of_an_unserviceable_restored_root_mints_nothing_never_absent` does and record which lifecycle state produces `ProjectApprovalRefused` in spec §17 — BI-11's acceptance test needs one.

- [ ] **Step 2: Run them to verify they fail**

Run: `cd python && uv run --frozen pytest tests/test_holdings_boundary.py -q -k "url_look or store_refusal or wraps or replica or intent_payload"`
Expected: FAIL — `look`, `store_refusal` and `StoreWriteRefused` do not exist; `intent_payload` refuses a `UrlLocator`.

- [ ] **Step 3: The error**

`python/src/beliefs/errors.py`, after `AcquisitionBoundaryRefused` (line 1468):

```python
class StoreWriteRefused(ScienceError):
    """The store transaction of a managed `write` was a routine engine refusal
    (url-retrieval design decision 10): `applied == 0` and a
    `ProjectApprovalRefused`, `PreconditionRefused` or `PendingUnresolved`
    cause. Raised for that phase only; the intent append and the publication
    raise as themselves."""

    def __init__(self, location: str, detail: str) -> None:
        super().__init__(f"{location}: the store refused the write: {detail}")
        self.location = location
        self.detail = detail
```

- [ ] **Step 4: The boundary**

In `python/src/beliefs/holdings/boundary.py`:

Imports: `from atoms.chain.errors import PendingUnresolved` and `from atoms.core.errors import PreconditionRefused, ProjectApprovalRefused` (the modules `root.py` uses); `from nodes.core.errors import ExecutionError`; `from beliefs.errors import MalformedRecord, StoreIdMismatch, StoreWriteRefused`; `from beliefs.holdings.records import (Absent, Found, HoldingsObservation, Locator, StoreLocator, UrlLocator, holdings_observation, require_canonical_digest)`; `from beliefs.holdings.transport import Failed, NotAttempted, Retrieved, RetrievalBounds, UrlSeam, refuse_scratch_root, retrieve`.

`intent_payload` takes `location: Locator` and encodes:

```python
    location_facet = (
        {"type": "url", "url": location.url}
        if isinstance(location, UrlLocator)
        else {"relative_path": location.relative_path, "store_id": location.store_id, "type": "store"}
    )
```

with `"location": location_facet` in the JSON (keys sorted by `sort_keys=True`, so the store arm's bytes are unchanged). `_append(ctx, location: Locator, kind)` — the annotation only.

The classifier and the look, placed after `InconclusiveAttempt`:

```python
_ROUTINE_REFUSALS = (ProjectApprovalRefused, PreconditionRefused, PendingUnresolved)


def store_refusal(caught: ExecutionError) -> bool:
    """A routine engine refusal of the store transaction (decision 10): raised
    before any mutation or refusing cleanly, `applied == 0`, and a cause in the
    closed set. `_mapped_submit` wraps every exception as `ExecutionError`, so
    neither the class nor the phase alone says a refusal happened."""
    return caught.applied == 0 and type(caught.__cause__) in _ROUTINE_REFUSALS


@dataclass(frozen=True)
class PublishedLook:
    record: HoldingsObservation
    ref: str
    retrieved: Retrieved


@dataclass(frozen=True)
class InconclusiveLook:
    report: str
    reason: str


def look(
    ctx: ActContext,
    location: UrlLocator,
    *,
    bounds: RetrievalBounds,
    seam: UrlSeam,
    scratch: Path,
    expected: str | None = None,
    standing: tuple[HoldingsObservation, ...] = (),
) -> PublishedLook | InconclusiveLook:
    """The URL pure look (url-retrieval design §5): a `re-check` intent for the
    registration, the request with nothing held, then a published `found` or an
    inconclusive attempt that mints nothing. The caller deletes `retrieved.path`
    on a `PublishedLook`; every other exit leaves no file."""
    ctx.authority.require("holdings", ("holdings-observation",))
    if type(location) is not UrlLocator:
        raise MalformedRecord("a URL look takes a UrlLocator")
    if expected is not None:
        require_canonical_digest(expected, "a holdings observation's expected digest")
        if expected.split(":", 1)[0] != "sha256":
            raise MalformedRecord("a found observation's expected digest must use the found digest's algorithm")
    refuse_scratch_root(scratch, (ctx.observer_root, ctx.store_root))
    token, intent = _append(ctx, location, "re-check")
    result = retrieve(location, bounds, seam, scratch)
    if isinstance(result, NotAttempted):
        return InconclusiveLook("byte-locator-untested", result.reason)
    if isinstance(result, Failed):
        return InconclusiveLook("retrieval-failed", result.reason)
    record = holdings_observation(
        location=location, outcome=Found(result.digest), expected=expected, observer=ctx.observer,
        instrument=ctx.instrument, event_token=token,
        observed_at=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"), supersedes=standing,
    )
    try:
        published = _publish_record(ctx, record, intent)
    except BaseException:
        result.path.unlink(missing_ok=True)  # ownership never reached the caller
        raise
    return PublishedLook(published.record, f"holdings-observation:{record.identity()}", result)
```

`write`: replace the line `state = _final(ctx.seam.store_write(ctx.store_root, location.relative_path, content), location.relative_path)` with:

```python
    try:
        outcome = ctx.seam.store_write(ctx.store_root, location.relative_path, content)
    except ExecutionError as caught:
        if store_refusal(caught):
            raise StoreWriteRefused(location.canonical(), str(caught)) from caught
        raise
    state = _final(outcome, location.relative_path)
```

Nothing else in `write` is wrapped. Add `"InconclusiveLook"`, `"PublishedLook"`, `"look"`, `"store_refusal"` to `__all__` if the module keeps one.

- [ ] **Step 5: Run the tests, the lint and the staleness probe**

Run: `cd python && uv run --frozen pytest tests/test_holdings_boundary.py tests/test_intent_evidence.py tests/test_pin_recheck_inventory.py tests/test_arm_staleness.py tests/acceptance/test_n2_cut10.py -q -k "not findings"`
Expected: PASS. `test_holdings_uses_one_guarded_intent_and_publication_route_and_the_shared_lock` sees `look` on the same `_append`/`_publish_record` route as `recheck`. Re-target any cut-10 pin `write`'s edit moved (the frozen J-arms pin lines in this module).

- [ ] **Step 6: Commit**

```bash
tasks done beliefs-853055 "the URL look under a re-check intent; store refusals classified by phase and cause inside write"
git add python/src/beliefs/holdings/boundary.py python/src/beliefs/errors.py python/tests tasks
git commit -m "feat(holdings): the URL look and the store-refusal classifier — H4, BI-7, BI-11"
```

---

### Task 5: The acquisition operation

**Files:**
- Create: `python/src/beliefs/holdings/acquire.py`, `python/tests/test_holdings_acquire.py`
- Modify: `python/src/beliefs/boundary.py` (`_mint_acquisition_report` after `_mint_relocation_report`, line 281), `python/src/beliefs/corpus.py:2259-2296` (`_append_operation_intent`, `_publish_operation_report` gain `port`/`operations`; `_refuse_acquired_dataset` beside `_refuse_malformed_act_report`, line 3035), `python/src/beliefs/errors.py` (`AcquisitionRefused` after `AcquisitionBoundaryRefused`)
- Test: `python/tests/test_holdings_acquire.py`, `python/tests/test_report.py`

**Interfaces:**
- Consumes: Tasks 1–4's names; `CorpusWriter._create_op`, `_refuse`, `_operation`, `read_view`, `root`; `_ImportView`, `Index`; `stored.dataset_node`, `stored.act_report_node`; `dataset_address`, `DatasetDeclaration`, `ResourceDeclaration`.
- Produces: `acquire.ResourceRequest(name, url, expected=None, materialize=None)`; `acquire.AcquisitionRequest(title, locator, resources, bounds, domain_facets=None)`; `acquire.Stop(resource, phase, reason)`; `acquire.AcquisitionOutcome(report, report_ref, dataset, entries, stop)`; `acquire.acquire(ctx, writer, request, *, seam, scratch, standing=None, port=None, hold=None) -> AcquisitionOutcome` (`hold: Callable[[], AbstractContextManager[object]] | None`, entered before the root lock at the close); `acquire.SKIPPED_AFTER_STOP = "skipped-after-stop"`; `boundary._mint_acquisition_report(intent, *, observer, instrument, opened_at, closed_at, entries)`; `CorpusWriter._append_operation_intent(kind, token, actor, *, port=None)`; `CorpusWriter._publish_operation_report(report, intent_digest, *, operation=None, operations=None, port=None)`; `CorpusWriter._refuse_acquired_dataset(node, report)`; `CorpusWriter._refuse_dataset_shape(node)`; `errors.AcquisitionRefused(WriteRefused)`. Tasks 6 and 8 consume these.

- [ ] **Step 1: The failing tests**

`python/tests/test_report.py`, beside `test_the_two_relocation_operation_kinds_are_admitted`:

```python
def test_an_acquisition_report_requires_an_acquisition_intent_and_keeps_entry_order():
    from beliefs.boundary import _mint_acquisition_report

    entries = (
        LocatorEntry("url:https://example.org/a", PublishedObservation("holdings-observation:" + "a" * 64), (("timeout_seconds", "5.0"),)),
        ManagedMutationEntry("store:" + "d" * 32 + ":a.bin", PublishedObservation("holdings-observation:" + "b" * 64)),
        DeclarationPinEntry("dataset:sha256:" + "c" * 64, PinnedDeclaration("dataset:sha256:" + "c" * 64)),
    )
    intent = OperationIntent("acquisition", "tok", "actor:a")
    fields = dict(observer="o", instrument="i", opened_at="2026-09-20T00:00:00Z", closed_at="2026-09-20T00:00:01Z")
    report = _mint_acquisition_report(intent, entries=entries, **fields)
    assert report.operation == "acquisition" and report.entries == entries
    permuted = _mint_acquisition_report(intent, entries=(entries[1], entries[0], entries[2]), **fields)
    assert permuted.identity() != report.identity()
    with pytest.raises(MalformedRecord):
        _mint_acquisition_report(OperationIntent("import", "tok", "actor:a"), entries=entries, **fields)
```

`python/tests/test_holdings_acquire.py` (new). It runs over the certified volume like `test_holdings_boundary.py` (real engine, `certified_work`), a writer opened with `open_corpus` over the observer root and a manifest adopted with `pins_for(BASE)` (`from test_holdings_receipt import ...`? — no: `from profiles import BASE` and `from beliefs.corpus import pins_for` as `test_world_view_acceptance.durable_world` does), and the scripted seam:

```python
"""The acquisition operation (url-retrieval design §6)."""

from __future__ import annotations

import json
import threading
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import pytest
from authority import FULL
from holdings_transport_fixtures import PUBLIC, Scripted, scripted_seam
from nodes.core.errors import ExecutionError
from profiles import BASE
from test_holdings_boundary import _intents, context  # Task 4's helper and the store/observer context

from beliefs import root as science_root, stored
from beliefs.corpus import _operation_lock_for, pins_for
from beliefs.dataset import DatasetDeclaration, ResourceDeclaration, dataset_address
from beliefs.errors import AcquisitionRefused, MalformedRecord, SessionProtocolError, StoreWriteRefused
from beliefs.holdings.acquire import SKIPPED_AFTER_STOP, AcquisitionOutcome, AcquisitionRequest, ResourceRequest, Stop, acquire
from beliefs.holdings.adapter import DatasetAnswer, DatasetBlocked, dataset_observations
from beliefs.holdings.records import Found, StoreLocator, url_locator
from beliefs.holdings.transport import RetrievalBounds
from beliefs.report import CLOSED, UNFINISHED, ByteLocatorUntested, DeclarationPinEntry, LocatorEntry, ManagedMutationEntry, RetrievalFailed, completion
from beliefs.root import open_corpus
from beliefs.world.logmodel import IntentEntryView, RegisteredEntryView, WellFormedView

BOUNDS = RetrievalBounds(timeout_seconds=5.0, max_bytes=1 << 20, max_redirects=3)
A, B, C = b"alpha bytes", b"beta bytes", b"gamma bytes"


def digest(body: bytes) -> str:
    return "sha256:" + sha256(body).hexdigest()


def ok(body: bytes) -> Scripted:
    return Scripted(200, {"Content-Length": str(len(body))}, (body,))


def resource(name: str, path: str, *, expected=None, store_id=None) -> ResourceRequest:
    return ResourceRequest(
        name=name, url=url_locator(f"https://example.org/{path}"), expected=expected,
        materialize=None if store_id is None else StoreLocator(store_id, f"acquired/{name}.bin"),
    )


def request(*resources: ResourceRequest, title="Dryad record 1") -> AcquisitionRequest:
    return AcquisitionRequest(title=title, locator="url:https://example.org/dataset/1", resources=resources, bounds=BOUNDS)


@pytest.fixture()
def acquisition(certified_work, tmp_path):
    ctx, store_id = context(certified_work)
    writer = open_corpus(ctx.observer_root, authority=FULL, profile=BASE)
    writer.adopt_manifest(profile=pins_for(BASE))
    return ctx, store_id, writer, tmp_path / "scratch"


def chain(root):
    view = science_root._log_seam().inspect_registered(root)
    assert isinstance(view, WellFormedView)
    return view.entries


def test_the_happy_path_mints_the_dataset_beside_its_report_in_one_transaction(acquisition):
    ctx, store_id, writer, scratch = acquisition
    seam, log = scripted_seam({"/a": ok(A)})
    assert not writer.read_view.holds("holdings-observation:" + "0" * 64)  # the index is built and cached before the looks publish past it
    outcome = acquire(ctx, writer, request(resource("a", "a", store_id=store_id)), seam=seam, scratch=scratch)
    assert outcome.stop is None and outcome.dataset is not None
    address = dataset_address(DatasetDeclaration((ResourceDeclaration("a", digest(A)),)))
    assert outcome.dataset.id == address
    facet = outcome.dataset.facets["empirical-observation"]
    assert facet == {"locator": "url:https://example.org/dataset/1", "attested_by": ctx.actor, "retrieval": outcome.report_ref}
    kinds = [type(entry) for entry in outcome.entries]
    assert kinds == [LocatorEntry, ManagedMutationEntry, DeclarationPinEntry]
    assert outcome.entries[0].subject == "url:https://example.org/a"
    assert outcome.entries[0].instrument_inputs == BOUNDS.instrument_inputs()
    assert outcome.entries[2] == DeclarationPinEntry(address, PinnedDeclaration(address))
    view = writer.read_view
    assert view.holds(outcome.report_ref) and view.holds(address)
    entries = chain(ctx.observer_root)
    intents = [e for e in entries if isinstance(e, IntentEntryView)]
    assert json.loads(intents[0].payload)["kind"] == "acquisition"  # the operation intent precedes every act
    assert [json.loads(i.payload).get("kind") for i in intents[1:]] == ["re-check", "write"]
    closing = [e for e in entries if isinstance(e, RegisteredEntryView)][-1]
    paths = {path for path, _ in closing.final}
    assert paths == {writer._relative_path(outcome.dataset), writer._relative_path(view.get(outcome.report_ref))}
    assert completion(OperationIntent("acquisition", json.loads(intents[0].payload)["event_token"], ctx.actor),
                      registrations_of(entries), {outcome.report_ref: report_of(view, outcome.report_ref)}) == CLOSED
    assert len(log.requests) == 1
    assert list(scratch.iterdir()) == []
```

(`registrations_of` and `report_of` are two five-line helpers at the top of the module: the `Registration(intent_token, pointer)` tuple built from the chain's registered entries whose `fulfills` is the operation intent's digest, and the `ActReport` read back through `stored.act_report_facet` into `boundary_values._mint_report` — copy the shape `test_stored_act_report.py` uses to read a stored report back; if none exists, assert `completion` over `(Registration(token, outcome.report_ref),)` with `held={outcome.report_ref: outcome.report}`.)

```python
def test_a_failing_second_look_closes_with_no_dataset_and_a_look_stop(acquisition):
    ctx, store_id, writer, scratch = acquisition
    seam, log = scripted_seam({"/a": ok(A), "/b": Scripted(500, {}, (b"",))})
    outcome = acquire(ctx, writer, request(resource("a", "a"), resource("b", "b")), seam=seam, scratch=scratch)
    assert outcome.dataset is None
    assert outcome.stop == Stop("b", "look", "status 500")
    assert [type(e.outcome) for e in outcome.entries] == [PublishedObservation, RetrievalFailed]
    assert writer.read_view.holds(outcome.report_ref)
    assert len(log.requests) == 2


def test_a_preflight_refusal_on_the_first_resource_skips_the_rest_with_zero_requests(acquisition):
    ctx, store_id, writer, scratch = acquisition
    seam, log = scripted_seam({}, unpinnable=True)
    outcome = acquire(ctx, writer, request(resource("a", "a"), resource("b", "b"), resource("c", "c")), seam=seam, scratch=scratch)
    assert [e.outcome for e in outcome.entries] == [
        ByteLocatorUntested("unpinnable"), ByteLocatorUntested(SKIPPED_AFTER_STOP), ByteLocatorUntested(SKIPPED_AFTER_STOP)
    ]
    assert log.requests == []
    assert [json.loads(i.payload).get("kind") for i in _intents(ctx.observer_root)] == ["acquisition", "re-check"]


def test_an_expectation_mismatch_mints_no_dataset_and_the_adapter_reports_mismatch(acquisition):
    ctx, store_id, writer, scratch = acquisition
    seam, _ = scripted_seam({"/a": ok(A)})
    outcome = acquire(ctx, writer, request(resource("a", "a", expected=digest(B))), seam=seam, scratch=scratch)
    assert outcome.dataset is None and outcome.stop is None
    record = stored.holdings_observation_value(writer.read_view.get(outcome.entries[0].outcome.ref))
    assert record.outcome == Found(digest(A)) and record.expected == digest(B)
    answer = dataset_observations(
        DatasetDeclaration((ResourceDeclaration("a", digest(B)),)),
        [{"head": "h", "location": "url:https://example.org/a", "outcome": {"finding": "found", "digest": digest(A)}, "expected": digest(B), "history": []}],
        [],
    )
    assert isinstance(answer, DatasetAnswer) and answer.observations[0].digest == digest(A)


def test_an_already_held_address_mints_no_second_dataset(acquisition):
    ctx, store_id, writer, scratch = acquisition
    seam, _ = scripted_seam({"/a": ok(A)})
    first = acquire(ctx, writer, request(resource("a", "a")), seam=seam, scratch=scratch)
    second = acquire(ctx, writer, request(resource("a", "a")), seam=seam, scratch=scratch)
    assert second.dataset is None and second.stop is None
    assert [type(e) for e in second.entries] == [LocatorEntry]
    assert writer.read_view.get(first.dataset.id).facets["empirical-observation"]["retrieval"] == first.report_ref
    assert len(list((ctx.observer_root / "holdings-observation").iterdir())) == 2


@pytest.mark.parametrize(
    "spoil",
    ["wrong-root", "no-port", "store-less-materialize", "scratch-under-root", "foreign-store", "malformed-facet"],
)
def test_every_pre_intent_refusal_leaves_the_chain_and_corpus_untouched_and_issues_no_request(acquisition, certified_work, spoil):
    ctx, store_id, writer, scratch = acquisition
    seam, log = scripted_seam({"/a": ok(A)})
    before = chain(ctx.observer_root)
    req = request(resource("a", "a", store_id=store_id))
    kwargs = dict(seam=seam, scratch=scratch)
    if spoil == "wrong-root":
        other = certified_work / "other"
        science_root.init_corpus_root(other, authority=FULL)
        writer = open_corpus(other, authority=FULL, profile=BASE)
    elif spoil == "no-port":
        from beliefs.corpus import CorpusWriter
        from nodes.core.executor import DefaultExecutor  # the executor the portable tests use; read test_session_writer.py's import
        writer = CorpusWriter(ctx.observer_root, DefaultExecutor, authority=FULL, profile=BASE)
    elif spoil == "store-less-materialize":
        ctx = replace(ctx, store_root=certified_work / "nowhere")
    elif spoil == "scratch-under-root":
        kwargs["scratch"] = ctx.observer_root / "scratch"
    elif spoil == "foreign-store":
        req = request(replace(resource("a", "a"), materialize=StoreLocator("f" * 32, "x.bin")))
    elif spoil == "malformed-facet":
        req = AcquisitionRequest(
            title="t", locator="url:https://example.org/dataset/1", resources=(resource("a", "a"),), bounds=BOUNDS,
            domain_facets={"ns/x": {"k": object()}},  # namespaced, so the request accepts it; the profile's payload validation does not
        )
    with pytest.raises((AcquisitionRefused, MalformedRecord, ValidationRefused, ExecutionError, FileNotFoundError)):
        acquire(ctx, writer, req, **kwargs)
    assert chain(ctx.observer_root) == before
    assert log.requests == []
    assert not any(node.kind in ("act-report", "dataset", "holdings-observation") for node in writer.read_view.iter_stored())


def test_the_request_refuses_an_unnamespaced_domain_facet_as_a_value():
    with pytest.raises(MalformedRecord, match="namespaced"):
        AcquisitionRequest(
            title="t", locator="url:https://example.org/d", resources=(resource("a", "a"),), bounds=BOUNDS,
            domain_facets={"unnamespaced": {"k": 1}},
        )


def test_a_registered_domain_facet_lands_on_the_minted_dataset(acquisition):
    ctx, store_id, writer, scratch = acquisition
    seam, _ = scripted_seam({"/a": ok(A)})
    facets = REGISTERED_DOMAIN_FACETS  # a facet the base profile registers; read one off `grep -rn "domain_facets=" python/tests/test_stored*.py python/tests/test_corpus*.py`
    req = AcquisitionRequest(title="t", locator="url:https://example.org/d", resources=(resource("a", "a"),), bounds=BOUNDS, domain_facets=facets)
    outcome = acquire(ctx, writer, req, seam=seam, scratch=scratch)
    assert outcome.dataset is not None
    for key, payload in facets.items():
        assert outcome.dataset.facets[key] == dict(payload)
```

(`ValidationRefused` and `FacetPayloadRefused` are the writer's refusal types for a payload the profile rejects; if the profile refuses the `object()` payload under `FacetPayloadRefused` or at `stored.dataset_node` under a `pydantic` error, add that type to the tuple — the assertion that matters is the untouched chain, the empty request log and the empty corpus. `REGISTERED_DOMAIN_FACETS` is a module constant the implementer fills from an existing test that adds a dataset with `domain_facets`; if none exists, the positive case passes `domain_facets=None` and asserts the facet set is exactly `{"dataset", "empirical-observation"}`.)

(For `store-less-materialize`, `store_genesis` over a missing root raises: the plan accepts the engine's own error type there and asserts only that nothing was appended and no request issued; read what `ctx.seam.store_genesis` raises for an absent root and narrow the `raises` tuple to that type and `AcquisitionRefused`.)

```python
def _read_only_store(ctx, certified_work):
    """A store the engine refuses to mutate, from the production seam (Task 4's last test)."""
    replica = certified_work / "replica"
    science_root.replicate_root(ctx.store_root, replica, authority=FULL)
    return replace(ctx, store_root=replica)


def test_a_store_refusal_on_the_first_resource_stops_skips_and_mints_nothing(acquisition, certified_work):
    ctx, store_id, writer, scratch = acquisition
    ctx = _read_only_store(ctx, certified_work)
    seam, log = scripted_seam({"/a": ok(A), "/b": ok(B)})
    outcome = acquire(ctx, writer, request(resource("a", "a", store_id=store_id), resource("b", "b")), seam=seam, scratch=scratch)
    assert outcome.dataset is None
    assert outcome.stop is not None and (outcome.stop.resource, outcome.stop.phase) == ("a", "materialize")
    assert [type(e) for e in outcome.entries] == [LocatorEntry, LocatorEntry]
    assert outcome.entries[1].outcome == ByteLocatorUntested(SKIPPED_AFTER_STOP)
    assert len(log.requests) == 1
    assert writer.read_view.holds(outcome.report_ref)
    assert list(scratch.iterdir()) == []


def test_a_store_refusal_on_the_last_resource_keeps_the_earlier_entries_and_mints_nothing(acquisition, certified_work):
    ctx, store_id, writer, scratch = acquisition
    ctx = _read_only_store(ctx, certified_work)
    seam, log = scripted_seam({"/a": ok(A), "/b": ok(B)})
    outcome = acquire(ctx, writer, request(resource("a", "a"), resource("b", "b", store_id=store_id)), seam=seam, scratch=scratch)
    assert outcome.dataset is None and outcome.stop.phase == "materialize" and outcome.stop.resource == "b"
    assert [type(e) for e in outcome.entries] == [LocatorEntry, LocatorEntry]
    assert all(type(e.outcome) is PublishedObservation for e in outcome.entries)
    assert len(log.requests) == 2


def test_a_publication_failure_after_a_committed_materialization_propagates_and_reads_unfinished(acquisition):
    ctx, store_id, writer, scratch = acquisition
    calls = {"n": 0}
    inner = ctx.seam.publish_fulfilling

    def flaky(root, plan, fulfills):
        calls["n"] += 1
        if calls["n"] == 2:  # the look's observation published; the write's does not
            raise ExecutionError("publish", index=None, applied=0) from PreconditionRefused("shape")
        return inner(root, plan, fulfills)

    ctx = replace(ctx, seam=replace(ctx.seam, publish_fulfilling=flaky))
    seam, _ = scripted_seam({"/a": ok(A)})
    with pytest.raises(ExecutionError, match="publish"):
        acquire(ctx, writer, request(resource("a", "a", store_id=store_id)), seam=seam, scratch=scratch)
    intents = _intents(ctx.observer_root)
    assert [json.loads(i.payload).get("kind") for i in intents] == ["acquisition", "re-check", "write"]
    assert (ctx.store_root / "acquired" / "a.bin").read_bytes() == A
    assert not any(node.kind == "act-report" for node in writer.read_view.iter_stored())


def test_an_unexpected_engine_failure_in_the_store_propagates_and_is_never_a_stop(acquisition):
    ctx, store_id, writer, scratch = acquisition

    def internal(_root, _path, _content):
        raise ExecutionError("internal", index=None, applied=None) from RuntimeError("boom")

    ctx = replace(ctx, seam=replace(ctx.seam, store_write=internal))
    seam, _ = scripted_seam({"/a": ok(A)})
    with pytest.raises(ExecutionError, match="internal"):
        acquire(ctx, writer, request(resource("a", "a", store_id=store_id)), seam=seam, scratch=scratch)
    assert not any(node.kind == "act-report" for node in writer.read_view.iter_stored())


def test_a_session_failure_between_the_look_and_the_write_propagates(acquisition):
    ctx, store_id, writer, scratch = acquisition

    def closed(_root, _path, _content):
        raise SessionProtocolError("the invocation is no longer current")

    ctx = replace(ctx, seam=replace(ctx.seam, store_write=closed))
    seam, _ = scripted_seam({"/a": ok(A)})
    with pytest.raises(SessionProtocolError):
        acquire(ctx, writer, request(resource("a", "a", store_id=store_id)), seam=seam, scratch=scratch)


def test_no_lock_is_held_across_the_request(acquisition):
    ctx, store_id, writer, scratch = acquisition
    seam, _ = scripted_seam({"/a": ok(A)})
    seen: list[bool] = []
    inner = seam.connect

    def probing(approved, timeout):
        lock = _operation_lock_for(ctx.observer_root)
        acquired = lock.acquire(blocking=False)
        seen.append(acquired)
        if acquired:
            lock.release()
        return inner(approved, timeout)

    acquire(ctx, writer, request(resource("a", "a")), seam=replace(seam, connect=probing), scratch=scratch)
    assert seen == [True]


def test_a_report_naming_an_observation_no_act_published_refuses_at_the_close(acquisition, monkeypatch):
    """T5-c: the close checks every PublishedObservation ref resolves."""
    ctx, store_id, writer, scratch = acquisition
    from beliefs.holdings import acquire as module

    real = module.look

    def forged(*args, **kwargs):
        result = real(*args, **kwargs)
        return replace(result, ref="holdings-observation:" + "0" * 64)

    monkeypatch.setattr(module, "look", forged)
    seam, _ = scripted_seam({"/a": ok(A)})
    with pytest.raises(AcquisitionRefused, match="no act published"):
        acquire(ctx, writer, request(resource("a", "a")), seam=seam, scratch=scratch)
    assert not any(node.kind == "act-report" for node in writer.read_view.iter_stored())
```

```python
def test_the_close_rebuilds_the_writers_view_before_it_resolves_the_looks_observations(acquisition, monkeypatch):
    """The looks publish through the holdings seam, past the writer's cached index;
    without `_reconstruct` under the closing lock the close refuses its own observations."""
    ctx, store_id, writer, scratch = acquisition
    seam, _ = scripted_seam({"/a": ok(A)})
    rebuilt: list[int] = []
    real = type(writer)._reconstruct

    def counting(self):
        rebuilt.append(1)
        return real(self)

    monkeypatch.setattr(type(writer), "_reconstruct", counting)
    writer.read_view  # cache the index
    outcome = acquire(ctx, writer, request(resource("a", "a")), seam=seam, scratch=scratch)
    assert outcome.dataset is not None and rebuilt  # the close rebuilt at least once before resolving
```

(`_operation_lock_for(root)` may hand out an `RLock` re-entrant to the calling thread — the probe runs on the calling thread, so `acquire(blocking=False)` succeeds if **no other** thread holds it and also if this thread holds it; to make the check meaningful, run the probe on a helper thread: `threading.Thread(target=lambda: seen.append(lock.acquire(blocking=False)))`, join it, release from that thread if acquired. Write the probe that way.)

- [ ] **Step 2: Run them to verify they fail**

Run: `cd python && uv run --frozen pytest tests/test_holdings_acquire.py tests/test_report.py -q -k "acquisition or acquire"`
Expected: FAIL at import — `beliefs.holdings.acquire` and `_mint_acquisition_report` do not exist.

- [ ] **Step 3: The report minter and the error**

`python/src/beliefs/boundary.py`, after `_mint_relocation_report`:

```python
def _mint_acquisition_report(
    intent: OperationIntent,
    *,
    observer: str,
    instrument: str,
    opened_at: str,
    closed_at: str,
    entries: tuple[Entry, ...],
) -> ActReport:
    """The acquisition operation's terminal record (url-retrieval design §6):
    per resource a locator entry and, where materialized, a mutation entry, in
    request order; then the declaration pin when a dataset minted."""
    if type(intent) is not OperationIntent or intent.kind != "acquisition":
        raise MalformedRecord("an acquisition report requires an acquisition operation intent")
    return _mint_report(
        operation="acquisition",
        event_token=intent.event_token,
        actor=intent.actor,
        observer=observer,
        instrument=instrument,
        opened_at=opened_at,
        closed_at=closed_at,
        entries=entries,
    )
```

(import `Entry` from `beliefs.report` beside the names the module already imports.) `python/src/beliefs/errors.py`, after `AcquisitionBoundaryRefused`:

```python
class AcquisitionRefused(WriteRefused):
    """An acquisition request refused before its intent — the wrong root, no
    operation port, a store-less materialization, a malformed request — or at
    its close, when the report would name an observation no act published
    (url-retrieval design §6 steps 1 and 4)."""
```

- [ ] **Step 4: The writer's two ports and the overlay validation**

`python/src/beliefs/corpus.py`:

`_append_operation_intent(self, kind, token, intent_actor, *, port: OperationPort | None = None)`: `operation_port = self._operation_port if port is None else port` in place of the assert's left side (keep the `assert operation_port is not None`).

`_publish_operation_report(self, report, intent_digest, *, operation: CreateOp | None = None, operations: Sequence[CreateOp] | None = None, port: OperationPort | None = None)`: the same port selection; `plan = list(operations) if operations is not None else [self._create_op(stored.act_report_node(report)) if operation is None else operation]`; `operation_port.execute_fulfilling(plan, intent_digest)`. Existing callers pass `operation=` and are unchanged.

Beside `_refuse_malformed_act_report`:

```python
    def _refuse_dataset_shape(self, node: Node) -> None:
        """The request-only half of a dataset's validation, run before an
        acquisition opens its intent (url-retrieval design §6 step 1): family,
        document, registry membership and every facet payload's shape. Nothing
        here reads the view — the report the record will name does not exist
        yet — so `attested_by`, bearer and validity are the close's."""
        self._refuse_family_kinds(node)
        self._refuse_invalid(node)
        self._refuse_facet_shapes(node)

    def _refuse_acquired_dataset(self, node: Node, report: Node) -> None:
        """Validate a dataset the acquisition mints beside its report
        (url-retrieval design §6 step 4): the report is an arriving member of the
        same transaction, so `retrieval` resolves through the overlay exactly as
        an import's members resolve through theirs. The attester is the bound
        actor — `provenance` is not set."""
        self._refuse_family_kinds(node)
        union_index = Index.build(self._view.iter_stored())
        try:
            union_index.assert_addable(report)
            union_index.upsert(report)
            union_index.assert_addable(node)
        except CollisionError as caught:
            raise CollisionRefused(str(caught)) from caught
        self._refuse(node, view=_ImportView(self._view, (report,), union_index))
        self._refuse_foreign_closure_actor(node)
```

(`CollisionError`/`CollisionRefused` are the names `_validate_import_bundle` already uses.) Factor the first half of `_refuse_facets` (line 3221: the `validate_document` try/except and the `validate_payload` loop, everything before `reading = ...`) into `_refuse_facet_shapes(self, node)` and have `_refuse_facets` call it; its behaviour is unchanged (`tests/test_corpus*.py` green).

- [ ] **Step 5: The operation**

`python/src/beliefs/holdings/acquire.py`:

```python
"""The acquisition operation (url-retrieval design §6).

One operation intent, then per resource a URL look and an optional managed
materialization, then one closing transaction carrying the dataset and the
act-report. The cooperative stop (decision 5) skips every resource after the
first that did not complete; a stop forbids the mint (decision 10).
"""

from __future__ import annotations

import secrets
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import final

from nodes.core.node import Node

from beliefs import boundary as boundary_values
from beliefs import stored
from beliefs.corpus import CorpusWriter
from beliefs.dataset import DatasetDeclaration, ResourceDeclaration, dataset_address
from beliefs.errors import AcquisitionRefused, MalformedRecord, StoreWriteRefused
from beliefs.holdings.boundary import ActContext, InconclusiveLook, look, write
from beliefs.holdings.records import HoldingsObservation, StoreLocator, UrlLocator, require_canonical_digest
from beliefs.holdings.transport import RetrievalBounds, UrlSeam, refuse_scratch_root
from beliefs.report import (
    ActReport,
    ByteLocatorUntested,
    DeclarationPinEntry,
    Entry,
    LocatorEntry,
    ManagedMutationEntry,
    OperationIntent,
    PinnedDeclaration,
    PublishedObservation,
    RetrievalFailed,
)
from beliefs.runrecord import OperationPort
from beliefs.sealed import sealed
from beliefs.world.anchors import parse_store_genesis

__all__ = ["SKIPPED_AFTER_STOP", "AcquisitionOutcome", "AcquisitionRequest", "ResourceRequest", "Stop", "acquire"]

SKIPPED_AFTER_STOP = "skipped-after-stop"
LOCATOR_SCHEMES = ("accession", "url", "instrument")
"""The empirical-observation facet's declared schemes (CONTRACT.yaml); the profile validates again at the write."""
PROBE_DIGEST = "sha256:" + "0" * 64
PROBE_REPORT = "act-report:" + "0" * 64
"""Placeholders the pre-intent shape check builds the dataset with; the shape check resolves neither."""


@sealed
@final
@dataclass(frozen=True)
class ResourceRequest:
    name: str
    url: UrlLocator
    expected: str | None = None
    materialize: StoreLocator | None = None

    def __post_init__(self) -> None:
        if type(self.name) is not str or not self.name:
            raise MalformedRecord("a resource request names its resource")
        if type(self.url) is not UrlLocator:
            raise MalformedRecord("a resource request retrieves a UrlLocator")
        if self.expected is not None:
            require_canonical_digest(self.expected, "a resource request's expected digest")
            if self.expected.split(":", 1)[0] != "sha256":
                raise MalformedRecord("an expected digest must use the instrument's algorithm, sha256")
        if self.materialize is not None and type(self.materialize) is not StoreLocator:
            raise MalformedRecord("a materialization destination is a StoreLocator")


@sealed
@final
@dataclass(frozen=True)
class AcquisitionRequest:
    title: str
    locator: str
    resources: tuple[ResourceRequest, ...]
    bounds: RetrievalBounds
    domain_facets: Mapping[str, Mapping[str, object]] | None = None

    def __post_init__(self) -> None:
        if type(self.title) is not str or not self.title:
            raise MalformedRecord("an acquisition request titles its dataset")
        scheme, separator, rest = self.locator.partition(":") if type(self.locator) is str else ("", "", "")
        if separator != ":" or not rest or scheme not in LOCATOR_SCHEMES:
            raise MalformedRecord(f"an acquisition's locator is `<scheme>:<rest>` with scheme in {LOCATOR_SCHEMES}")
        if type(self.resources) is not tuple or not self.resources or any(type(r) is not ResourceRequest for r in self.resources):
            raise MalformedRecord("an acquisition request names at least one ResourceRequest")
        names = [resource.name for resource in self.resources]
        if len(names) != len(set(names)):
            raise MalformedRecord("resource names are unique within one request")
        if type(self.bounds) is not RetrievalBounds:
            raise MalformedRecord("an acquisition request carries RetrievalBounds")
        if self.domain_facets is not None and (
            not isinstance(self.domain_facets, Mapping)
            or any(
                type(key) is not str or "/" not in key or not isinstance(payload, Mapping) or any(type(k) is not str for k in payload)
                for key, payload in self.domain_facets.items()
            )
        ):
            raise MalformedRecord("domain_facets maps namespaced `<namespace>/<name>` keys to mappings with string keys")


@sealed
@final
@dataclass(frozen=True)
class Stop:
    resource: str
    phase: str
    reason: str


@sealed
@final
@dataclass(frozen=True)
class AcquisitionOutcome:
    report: ActReport
    report_ref: str
    dataset: Node | None
    entries: tuple[Entry, ...]
    stop: Stop | None


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def acquire(
    ctx: ActContext,
    writer: CorpusWriter,
    request: AcquisitionRequest,
    *,
    seam: UrlSeam,
    scratch: Path,
    standing: Mapping[str, tuple[HoldingsObservation, ...]] | None = None,
    port: OperationPort | None = None,
    hold: Callable[[], AbstractContextManager[object]] | None = None,
) -> AcquisitionOutcome:
    """`hold` is the caller's outer lock for the close — the session route passes
    the one `ScopedWriter._act` takes first — entered before the root lock and
    never around a request (decision 15; the session's session-then-root order)."""
    standing = {} if standing is None else standing
    if type(request) is not AcquisitionRequest:
        raise MalformedRecord("acquire takes an AcquisitionRequest")
    # 1. Checks, before any effect (spec §6 step 1).
    ctx.authority.require("holdings", ("holdings-observation",))
    ctx.authority.require("corpus-write", ("dataset", "act-report"))
    if Path(writer.root).resolve() != Path(ctx.observer_root).resolve():
        raise AcquisitionRefused("the writer's root is not the act context's observer root; an acquisition publishes in one root")
    if port is None and writer._operation_port is None:
        raise AcquisitionRefused("this corpus has no operation port; acquisition is a boundary operation")
    refuse_scratch_root(scratch, (ctx.observer_root, ctx.store_root))
    if any(resource.materialize is not None for resource in request.resources):
        store_id, _ = parse_store_genesis(ctx.seam.store_genesis(ctx.store_root))
        for resource in request.resources:
            if resource.materialize is not None and resource.materialize.store_id != store_id:
                raise AcquisitionRefused(f"{resource.name}: its destination names store {resource.materialize.store_id}, not the bound {store_id}")
    writer._refuse_dataset_shape(  # the request-only metadata, before any effect: title, locator, domain facets
        stored.dataset_node(
            title=request.title,
            resources=[{"name": r.name, "digest": r.expected or PROBE_DIGEST} for r in request.resources],
            empirical_observation={"locator": request.locator, "attested_by": ctx.actor, "retrieval": PROBE_REPORT},
            domain_facets=request.domain_facets,
        )
    )
    # 2. Open.
    intent = OperationIntent("acquisition", secrets.token_hex(16), ctx.actor)
    opened_at = _now()
    intent_digest = writer._append_operation_intent(intent.kind, intent.event_token, intent.actor, port=port)
    # 3. Resources, in order, until the cooperative stop.
    entries: list[Entry] = []
    digests: dict[str, str] = {}
    published: set[str] = set()
    stop: Stop | None = None
    inputs = request.bounds.instrument_inputs()
    for resource in request.resources:
        subject = resource.url.canonical()
        if stop is not None:
            entries.append(LocatorEntry(subject, ByteLocatorUntested(SKIPPED_AFTER_STOP), inputs))
            continue
        result = look(
            ctx, resource.url, bounds=request.bounds, seam=seam, scratch=scratch,
            expected=resource.expected, standing=standing.get(subject, ()),
        )
        if isinstance(result, InconclusiveLook):
            outcome = ByteLocatorUntested(result.reason) if result.report == "byte-locator-untested" else RetrievalFailed(result.reason)
            entries.append(LocatorEntry(subject, outcome, inputs))
            stop = Stop(resource.name, "look", result.reason)
            continue
        entries.append(LocatorEntry(subject, PublishedObservation(result.ref), inputs))
        published.add(result.ref)
        digests[resource.name] = result.retrieved.digest
        try:
            if resource.materialize is not None:
                destination = resource.materialize
                try:
                    materialized = write(
                        ctx, destination, result.retrieved.path.read_bytes(), expected=result.retrieved.digest,
                        standing=standing.get(destination.canonical(), ()),
                    )
                except StoreWriteRefused as refused:
                    stop = Stop(resource.name, "materialize", str(refused))
                    continue
                ref = f"holdings-observation:{materialized.record.identity()}"
                entries.append(ManagedMutationEntry(destination.canonical(), PublishedObservation(ref)))
                published.add(ref)
        finally:
            result.retrieved.path.unlink(missing_ok=True)
    # 4. Close.
    expectations_hold = all(r.expected is None or digests.get(r.name) == r.expected for r in request.resources)
    mint = stop is None and expectations_hold
    address: str | None = None
    if mint:
        declaration = DatasetDeclaration(tuple(ResourceDeclaration(r.name, digests[r.name]) for r in request.resources))
        address = dataset_address(declaration)
        assert address is not None  # every resource found and pinned sha256
    closed_at = _now()
    dataset: Node | None = None
    outer = nullcontext() if hold is None else hold()
    with outer, writer._operation:  # session (the caller's hold), then root: `_act`'s order
        writer._reconstruct()  # the looks published through the holdings seam, past this writer's cached index
        for ref in sorted(published):
            if writer.read_view.resolve(ref) is None:
                raise AcquisitionRefused(f"{ref}: the report would reference an observation no act published")
        held = address is not None and writer.read_view.resolve(address) is not None
        report_entries = tuple(entries) + ((DeclarationPinEntry(address, PinnedDeclaration(address)),) if mint and not held else ())
        report = boundary_values._mint_acquisition_report(  # pyright: ignore[reportPrivateUsage]
            intent, observer=ctx.observer, instrument=ctx.instrument, opened_at=opened_at, closed_at=closed_at,
            entries=report_entries,
        )
        report_node = stored.act_report_node(report)
        operations = []
        if mint and not held:
            assert address is not None
            dataset = stored.dataset_node(
                title=request.title,
                resources=[{"name": r.name, "digest": digests[r.name]} for r in request.resources],
                empirical_observation={"locator": request.locator, "attested_by": ctx.actor, "retrieval": report_node.id},
                domain_facets=request.domain_facets,
            )
            writer._refuse_acquired_dataset(dataset, report_node)
            operations.append(writer._create_op(dataset))
        operations.append(writer._create_op(report_node))
        writer._publish_operation_report(report, intent_digest, operations=tuple(operations), port=port)
    return AcquisitionOutcome(report, report_node.id, dataset, report_entries, stop)
```

Notes for the implementer: imports `from collections.abc import Callable, Mapping` and `from contextlib import AbstractContextManager, nullcontext`. `writer._operation` is the `_SettlingHold` `add` uses (`with self._operation:`); its `__enter__` settles only when `unresolved` is set, and the looks' publications never set it (they go through `ctx.seam.publish_fulfilling`, a different port), so the close calls `writer._reconstruct()` itself — the same call `test_audit.py` makes after an out-of-band write — before resolving any ref or the address; `_publish_operation_report` runs `_reconstruct` again afterwards so `writer.read_view` sees the transaction. The look and the write take the corpus lock only inside `_append` and `_publish_record`, so nothing is held across `retrieve`; `hold` and `writer._operation` are entered at the close only. `parse_store_genesis` is what `boundary._bind` uses. If `stored.dataset_node` refuses `domain_facets=None`, pass `{}`. If the profile's payload validation of `empirical-observation` pattern-checks `retrieval` more tightly than `act-report:<64 hex>`, shape `PROBE_REPORT` to pass it; the shape check never resolves the ref.

- [ ] **Step 6: Run the tests and the lint**

Run: `cd python && uv run --frozen pytest tests/test_holdings_acquire.py tests/test_report.py tests/test_holdings_boundary.py tests/test_pin_recheck_inventory.py -q && uv run --frozen ruff check src tests && uv run --frozen pyright src/beliefs/holdings/acquire.py src/beliefs/corpus.py src/beliefs/boundary.py`
Expected: PASS, clean. `just test-fast` green.

- [ ] **Step 7: Commit**

```bash
tasks done beliefs-059224 "the acquisition operation: intent, looks, materialization, the cooperative stop, one closing transaction with the dataset"
git add python/src/beliefs/holdings/acquire.py python/src/beliefs/boundary.py python/src/beliefs/corpus.py python/src/beliefs/errors.py python/tests tasks
git commit -m "feat(holdings): the acquisition operation — R10, T2, T5, T7, BI-5, BI-6, BI-8"
```

---

### Task 6: The session route, reconciliation, and the instrument on the kernel transport

**Files:**
- Modify: `python/src/beliefs/session/writer.py:329-345` (`ScopedWriter.acquire` after `holdings_context`), `python/tools/survey_admission.py:255-480` (the transport section replaced by imports), `python/tests/test_admission_survey.py` (the moved tests deleted; the fakes updated to `target`/`authority`)
- Test: `python/tests/test_session_routes.py`, the module holding `reconcile` tests (`grep -ln "reconcile(" python/tests/test_session*.py`), `python/tests/test_admission_survey.py`

**Interfaces:**
- Consumes: `acquire`, `AcquisitionRequest`, `AcquisitionOutcome` (Task 5); `url_seam`, `UrlSeam`, `Approved`, `preflight`, `PinnedHTTPSConnection`, `pinned_connection`, `PinningUnavailable`, `system_resolver` (Task 3).
- Produces: `ScopedWriter.acquire(request, *, instrument, scratch, seam=None, standing=None) -> AcquisitionOutcome`; `ScopedWriter._closing_hold() -> AbstractContextManager[None]`; `survey_admission` importing the kernel transport, `NetworkProbe.fetch` an adapter over `retrieve`.

- [ ] **Step 1: The failing tests**

`python/tests/test_session_routes.py` — the durable session over the certified volume, because the route's close checks that every published observation resolves and the module's `FakeSeam` publishes nothing to disk (add imports `from holdings_transport_fixtures import Scripted, scripted_seam`, `from beliefs.holdings.acquire import AcquisitionRequest, ResourceRequest`, `from beliefs.holdings.records import url_locator`, `from beliefs.holdings.transport import RetrievalBounds`, `from beliefs.root import init_corpus_root, init_store_root, open_corpus`, `from beliefs.session import open_attended_session`, `from beliefs.world.registry import WorldConfig`, `from beliefs.corpus import pins_for`):

```python
ACQUIRES = RequiredCapabilities.for_kinds({"holdings-observation", "dataset", "act-report"}, {"act-report": "corpus-write"})


def _acquisition_request():
    return AcquisitionRequest(
        title="t", locator="url:https://example.org/dataset",
        resources=(ResourceRequest("a", url_locator("https://example.org/a")),),
        bounds=RetrievalBounds(5.0, 1 << 20, 3),
    )


def _durable_session(certified_work):
    corpus_root, store_root = certified_work / "corpus", certified_work / "store"
    init_corpus_root(corpus_root, authority=FULL)
    open_corpus(corpus_root, authority=FULL, profile=BASE).adopt_manifest(profile=pins_for(BASE))
    init_store_root(store_root, authority=FULL)
    config = WorldConfig(certified_work / "world", "a" * 32, (corpus_root,))
    return open_attended_session(config, certified_work / "ops", profile=BASE, store_root=store_root)


def test_acquire_through_a_session_ledgers_every_commit(certified_work, tmp_path):
    session = _durable_session(certified_work)
    session.claim_invocation("A", "acquire", DIGEST)
    scoped = session.scoped(ACQUIRES, "A")
    transport, log = scripted_seam({"/a": Scripted(200, {"Content-Length": "1"}, (b"x",))})
    outcome = scoped.acquire(_acquisition_request(), instrument="inst", scratch=tmp_path / "scratch", seam=transport)
    assert outcome.dataset is not None and len(log.requests) == 1
    session.close_invocation("A", {"done": []})
    session.close()
    acts = open_ledger_reader(session.operations_root, session.session_id).acts()
    assert len(acts) == 2  # the look's fulfilling publication and the closing transaction
    assert {pair[1] for act in acts for pair in act.record_ids} >= {outcome.report_ref, outcome.dataset.id}


ACQUIRES_AND_ADDS = RequiredCapabilities.for_kinds(
    {"holdings-observation", "dataset", "act-report", "proposition"}, {"act-report": "corpus-write"}
)


def test_the_close_takes_the_session_lock_before_the_root_lock_and_a_concurrent_act_completes(certified_work, tmp_path, monkeypatch):
    """Session, then root, is the only order `_act` takes; the close takes the same
    one, and holds neither around the request — so an act on another thread
    completes while the acquisition is open, and the close never waits on a
    thread that waits on it."""
    from beliefs import corpus as corpus_module

    session = _durable_session(certified_work)
    session.claim_invocation("A", "acquire", DIGEST)
    scoped = session.scoped(ACQUIRES_AND_ADDS, "A")
    owned: list[bool] = []
    real_enter = corpus_module._SettlingHold.__enter__

    def probing(self):
        owned.append(session._lock._is_owned())
        return real_enter(self)

    monkeypatch.setattr(corpus_module._SettlingHold, "__enter__", probing)
    transport, _ = scripted_seam({"/a": Scripted(200, {"Content-Length": "1"}, (b"x",))})
    opened, added = threading.Event(), threading.Event()

    def gated_connect(approved, timeout):
        opened.set()  # the operation intent is open and the request is about to go out
        assert added.wait(30), "the concurrent add did not complete while the request was open"
        return transport.connect(approved, timeout)

    def add_while_open():
        assert opened.wait(30)
        scoped.add(proposition("p"))
        added.set()

    partner = threading.Thread(target=add_while_open, daemon=True)
    partner.start()
    outcome = scoped.acquire(
        _acquisition_request(), instrument="inst", scratch=tmp_path / "scratch", seam=replace(transport, connect=gated_connect)
    )
    partner.join(30)
    assert not partner.is_alive() and outcome.dataset is not None
    assert owned and all(owned)  # every root-lock entry under the session saw the session lock owned first
    session.close_invocation("A", {"done": []})
    session.close()
    assert len(open_ledger_reader(session.operations_root, session.session_id).acts()) == 3  # the add, the look, the close


def test_acquire_on_a_store_less_session_refuses_before_any_intent(tmp_path):
    session, ports = make_session(tmp_path)
    session.claim_invocation("A", "acquire", DIGEST)
    scoped = session.scoped(ACQUIRES, "A")
    transport, log = scripted_seam({})
    with pytest.raises(SessionProtocolError, match="no store"):
        scoped.acquire(_acquisition_request(), instrument="inst", scratch=tmp_path / "scratch", seam=transport)
    assert ports[-1].calls == [] and log.requests == []
```

(`RequiredCapabilities.for_kinds`' second argument maps a kind to the family that mints it where the default is not `corpus-write`; read `test_session_routes.RUNS` for the shape and `permit.KIND_ACTS` for `act-report`. `DIGEST`, `make_session`, `open_ledger_reader`, `proposition` and `threading` are the module's existing names — `test_a_holdings_write_and_a_corpus_add_on_two_threads_both_complete` is the two-thread precedent; add `from dataclasses import replace`. `RLock._is_owned` is CPython's and is what the ownership probe reads.)

`python/tests/test_session_reconcile.py`, beside `holdings_intent`:

```python
def url_intent(digest: str, session: str = S1) -> IntentEntryView:
    payload = intent_payload(location=url_locator("https://example.org/a"), act_kind="re-check", event_token="tok", actor=f"session:{session}")
    return IntentEntryView(digest=digest, payload=payload)


def test_a_url_recheck_intent_and_its_fulfillment_reconcile_to_nothing():
    chains = {CORPUS: view(url_intent(I), registration(R, I), settled(R, True))}
    assert reconcile([ledger(opens=("A",), acts=(("A", R, I),), closes=("A",))], chains) == ()


def test_an_unfulfilled_url_recheck_intent_reads_as_a_store_one_does():
    chains = {CORPUS: view(url_intent(I))}
    store = {CORPUS: view(holdings_intent(I))}
    ledgers = [ledger(opens=("A",), closed=False)]
    assert codes(reconcile(ledgers, chains)) == codes(reconcile(ledgers, store)) == [("session-outcome-unknown", "warning", I)]
```

(import `url_locator` beside `StoreLocator`.) Add `url_intent` to the `parametrize` lists that run `run_intent` and `holdings_intent` through the session-unknown and actor cases.

`python/tests/test_admission_survey.py`: delete the five transport tests — `test_the_pinned_connection_dials_the_validated_address_and_validates_the_name`, `test_a_context_that_would_skip_validation_refuses_to_pin`, `test_a_validated_address_that_cannot_be_pinned_issues_no_request`, `test_a_refused_redirect_hop_ends_the_attempt_as_untested`, `test_a_relative_redirect_is_resolved_before_it_is_revalidated` — and `_RedirectingConnection` (the behaviour they read lives in `test_holdings_transport.py` since Task 3, and a refused hop is now `retrieval-failed`). Add the adapter's tests (import `Scripted`, `scripted_seam` from `holdings_transport_fixtures`):

```python
def test_the_probe_maps_the_kernel_result_to_the_instrument_vocabulary(tmp_path: Path) -> None:
    seam, log = scripted_seam({"/data": Scripted(200, {"Content-Length": "7"}, (b"payload",))})
    probe = NetworkProbe(tmp_path / "scratch", resolver=seam.resolve, connect=seam.connect)
    outcome = probe.fetch("https://example.org/data")
    assert outcome == ProbeOutcome(BYTES_RETRIEVED, digest=sha256(b"payload").hexdigest(), size=7)
    assert list((tmp_path / "scratch").iterdir()) == []  # the probe deletes the kernel's scratch file
    assert len(log.requests) == 1
    failing, _ = scripted_seam({"/data": Scripted(500, {}, (b"",))})
    assert NetworkProbe(tmp_path / "scratch", resolver=failing.resolve, connect=failing.connect).fetch("https://example.org/data") == ProbeOutcome(BYTES_RETRIEVAL_FAILED, reason="status 500")
    untested, _ = scripted_seam({}, unpinnable=True)
    assert NetworkProbe(tmp_path / "scratch", resolver=untested.resolve, connect=untested.connect).fetch("https://example.org/data") == ProbeOutcome(BYTES_LOCATOR_UNTESTED, reason="unpinnable")
    assert NetworkProbe(tmp_path / "scratch", resolver=seam.resolve, connect=seam.connect).fetch("https://user@example.org/data") == ProbeOutcome(BYTES_LOCATOR_UNTESTED, reason="malformed url")


def test_a_refused_redirect_hop_is_retrieval_failed_by_ordinal_and_category(tmp_path: Path) -> None:
    seam, _ = scripted_seam({"/data": Scripted(302, {"Location": "https://tok3n-9f2a.example.net/data?X-Amz-Signature=abc"})})
    resolver = lambda host, _port: ["10.1.1.1"] if host != "example.org" else seam.resolve(host, 0)  # noqa: E731
    outcome = NetworkProbe(tmp_path / "scratch", resolver=resolver, connect=seam.connect).fetch("https://example.org/data")
    assert outcome == ProbeOutcome(BYTES_RETRIEVAL_FAILED, reason="redirect hop 1 refused: non-public-address")
```

(`ProbeOutcome.digest` stays bare hex — `qualify(outcome.digest)` prefixes it at the comparison; the adapter strips the kernel's `sha256:`.)

- [ ] **Step 2: Run them to verify they fail**

Run: `cd python && uv run --frozen pytest tests/test_session_routes.py -q -k acquire`
Expected: FAIL — `ScopedWriter` has no attribute `acquire`.

- [ ] **Step 3: The route**

`python/src/beliefs/session/writer.py`, after `holdings_context`:

```python
    def acquire(
        self,
        request: AcquisitionRequest,
        *,
        instrument: str,
        scratch: Path,
        seam: UrlSeam | None = None,
        standing: Mapping[str, tuple[HoldingsObservation, ...]] | None = None,
    ) -> AcquisitionOutcome:
        """This invocation's acquisition route (url-retrieval design §8): the
        holdings context supplies the ledgered store seam, `operation_port()` the
        ledgered operation port, and no lock of this facade is held across the
        request (decision 15)."""
        from beliefs.holdings.acquire import acquire as run_acquisition
        from beliefs.holdings.transport import url_seam

        ctx = self.holdings_context(instrument=instrument)
        return run_acquisition(
            ctx, self._writer, request, seam=url_seam() if seam is None else seam, scratch=scratch,
            standing=standing, port=self.operation_port(), hold=self._closing_hold,
        )

    @contextmanager
    def _closing_hold(self) -> Iterator[None]:
        """The acquisition's close under this session's lock, taken before the
        root lock exactly as `_act` takes it, currency re-checked on entry (§13
        item 18). The ledgered port's `execute_fulfilling` re-enters the same
        `RLock` inside."""
        with self._session._lock:
            self._session._require_current(self._invocation)
            yield
```

(type-only imports of `AcquisitionRequest`, `AcquisitionOutcome`, `UrlSeam`, `HoldingsObservation`, `Mapping`, `Path` under `TYPE_CHECKING` as the module does for `ActContext`.) `holdings_context` raises `SessionProtocolError` for a store-less session before any intent, which is T2-b's session arm.

- [ ] **Step 4: The instrument**

In `python/tools/survey_admission.py` delete `Approved`, `Refused`, `Resolver`, `system_resolver`, `preflight`, `ConnectionFactory`, `PinnedHTTPSConnection`, `PinningUnavailable`, `pinned_connection`, `NetworkProbe._request` and the streaming body of `NetworkProbe.fetch` (lines 255–480's transport half and the loop) — the instrument keeps its own copies of nothing (spec §4). Import `RetrievalBounds`, `UrlSeam`, `Failed`, `NotAttempted`, `pinned_connection`, `system_resolver`, `retrieve` from `beliefs.holdings.transport` and `url_locator` from `beliefs.holdings.records`. `NetworkProbe` keeps its constructor signature and the `ProbeOutcome` vocabulary and becomes the adapter:

```python
    def __init__(self, scratch, *, resolver=system_resolver, timeout=DEFAULT_TIMEOUT_SECONDS, max_bytes=DEFAULT_MAX_BYTES, max_redirects=5, connect=None) -> None:
        self._scratch = scratch
        self._bounds = RetrievalBounds(timeout, max_bytes, max_redirects)
        self._seam = UrlSeam(resolve=resolver, connect=connect or pinned_connection)

    def fetch(self, url: str) -> ProbeOutcome:
        """The kernel's retrieval, read into the survey's vocabulary: the kernel's
        phase is the survey's byte observation, and its reasons are already free of
        every hop's bytes."""
        try:
            locator = url_locator(url)
        except MalformedRecord:
            return ProbeOutcome(BYTES_LOCATOR_UNTESTED, reason="malformed url")
        result = retrieve(locator, self._bounds, self._seam, self._scratch)
        if isinstance(result, NotAttempted):
            return ProbeOutcome(BYTES_LOCATOR_UNTESTED, reason=result.reason)
        if isinstance(result, Failed):
            return ProbeOutcome(BYTES_RETRIEVAL_FAILED, reason=result.reason)
        result.path.unlink()
        return ProbeOutcome(BYTES_RETRIEVED, digest=result.digest.partition(":")[2], size=result.size)
```

(keep the parameter annotations the module already spells.) Run `uv run --frozen pytest tests/test_admission_survey.py -q`.

- [ ] **Step 5: Run the tests**

Run: `cd python && uv run --frozen pytest tests/test_session_routes.py tests/test_session_writer.py tests/test_admission_survey.py -q` and the reconcile module; then `just test-fast`.
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
tasks done beliefs-3ea5ac "the session acquisition route; reconciliation over URL intents; the instrument on the kernel transport"
git add python/src/beliefs/session/writer.py python/tools/survey_admission.py python/tests tasks
git commit -m "feat(session): the acquisition route, and the survey instrument on the kernel transport — T2, BI-10"
```

---

### Task 7: The reproduction re-runs

**Files:**
- Modify: `docs/designs/2026-09-05-mm30-reproduction.md` (append §14)

**Interfaces:**
- Consumes: everything above. Produces: the transition measurement the results record cites.

- [ ] **Step 1: Run**

From `python/`, with `SCIENCE_MM30_ROOT=/mnt/ssd/Dropbox/beliefs/.work/reproduction/mm30` (the main checkout's; the driver resolves the main checkout through the worktree's real path, `beliefs-51ffdf`): run the driver as cut 34's Task 6 did (`sed -n '/### Task 6/,/### Task 7/p' docs/superpowers/plans/2026-09-19-correction-remainder-slice-2.md` for the exact command and the `state.json` fields read). Nothing is recreated or moved aside: no contract succeeded; every stored holdings observation in mm30's corpus is a `store` location and decodes under the widened codec; the reducer is not invoked by the driver (`grep -n derive_holdings python/tools/reproduction/*.py` is empty), so no rule identity is read there.

- [ ] **Step 2: Record**

Append `## 14. Addendum — URL retrieval, 2026-09-20` to the record: the same evaluator answer as §13; `found=()` and coverage unchanged; every holdings observation decoded under the two-arm codec with its identity unchanged (the facet's `store` encoding is byte-identical); the `url` arm and the `acquisition` operation exercised by the acceptance module only, mm30's corpus acquiring nothing by URL. If any pinned value differs, stop: that is a finding against spec §7 and the cut does not freeze its results until it is explained (spec §15).

```bash
tasks done beliefs-a74957 "reproduction re-run: same answer, no digest moved, store observations decode unchanged"
git add docs/designs/2026-09-05-mm30-reproduction.md tasks
git commit -m "docs(reproduction): re-run under URL retrieval; nothing moves"
```

---

### Task 8: Acceptance, the N2 declaration, the guard and the runner

**Files:**
- Create: `python/tests/acceptance/test_url_retrieval_acceptance.py`, `python/tests/n2_arms_cut35.py`, `python/tests/acceptance/n2_arms_cut35.py` (the re-export shim on `acceptance/n2_arms_cut34.py`'s shape), `python/tests/acceptance/test_n2_cut35.py`, `python/tools/cut35_acceptance.py`

**Interfaces:**
- Consumes: the frozen cut document, `CUT35_FREEZE_COMMIT`, `CUT35_FROZEN_SHA256` (Task 0); every module above.
- Produces: H4-a–b, G9-a, R10-a, T5-a–c, T7-a–b, T1-a, T2-a–d, T4-a–b, BI-1–BI-11 discharged on the certified volume.

- [ ] **Step 1: The acceptance module**

One test per unit over the certified volume, named exactly as `UNIT_CHECKS` names it (Step 2). Fixtures at the top of the module: `certified_work` (the shared conftest fixture; on the cut-35 root it reads `SCIENCE_CUT10_ROOT`, which the runner exports); `observer(certified_work)` = Task 5's `acquisition` fixture shape (a registered observer root with a manifest, a store root, the production seam, `open_corpus`); `session(certified_work)` = Task 6's `_durable_session`; `transport(script, **kw)` = `scripted_seam`; `served(script)` = `LocalTlsServer(script)` entered for the test and `tls_seam` over it (spec §11.2: the acceptance seam is the production pinned connection over the in-process TLS server, its context trusting the committed certificate; the scripted fake is used only where a behaviour cannot be provoked over real framing — the unpinnable context, the raised exception classes); `chain(root)`, `intents(root)` from Task 4/5's tests; `read_only_store(ctx, certified_work)` from Task 5. Each test is the Task 1–6 unit test re-composed over the durable roots:

- `test_h4a_an_established_remote_found_publishes_or_the_look_raises` — first the positive half over the TLS server (`served({"/data": Served(body=b"payload")})`): the look publishes `Found(sha256 of the bytes)` and the server's log carries the faithful request; then Task 4's publication-failure test through the durable session's context (`replace(ctx, seam=replace(ctx.seam, publish_fulfilling=raise_publish))`): `ExecutionError` propagates, no observation directory, the chain carries the unmatched re-check intent and no registration for it, and no act-report.
- `test_h4b_an_inconclusive_remote_attempt_mints_nothing_and_never_absent` — a standing URL `found` over the TLS server; then, in turn, a timeout (scripted, `raise_on_read=socket.timeout(...)`), a truncated chunked body over the TLS server (`Served(body=b"partial", truncate_chunked=True)` → `retrieval-failed`, `transport failure: protocol`), the ceiling over the TLS server (`max_bytes=4` against a 5-byte body), a `404` and a `500` over the TLS server, a refused hop (a resolver answering `10.0.0.1` for the hop's host), an unpinnable seam: each `InconclusiveLook`, `hasattr(result, "digest")` false, the observation directory still holds exactly one record whose identity is the standing one, and no observation anywhere spells `absent` (`stored.holdings_observation_value` over every stored holdings record).
- `test_g9a_a_url_location_holds_without_a_store_copy` — `acquire` one resource without `materialize`; `dataset_observations(declaration, active, blocked)` over `derive_holdings(world, {corpus_id}, binding, ...)`'s outputs (`test_holdings_receipt.admitted_world`'s shape over the observer root, the shipped bundle installed) is a `DatasetAnswer` whose `admission_state` is `Held`; then a re-look through a failing seam (`500`) leaves the reduction's active set byte-identical and the answer `Held`.
- `test_r10a_the_acquisition_records_dataset_provenance` — after a materialized acquisition: the dataset's facet equals `{"locator": request.locator, "attested_by": actor, "retrieval": report_ref}`; the report's entries reference the two observations; `validity_refusal(writer.read_view, dataset, BASE) is None`; the run boundary's refusal of a URL input is cut 3's arm (`n2_arms_cut3.py` R10) and is cited, not re-run.
- `test_t5a_a_began_request_never_spells_untested` — a `500` after the request began: the entry's outcome is `RetrievalFailed("status 500")` and the module-level assertion `type(entry.outcome) is not ByteLocatorUntested`; the frozen row's "attempt it on a locator act whose request began; assert refusal" is the sabotage direction (T5-a's arm makes `look` classify `Failed` as untested and this test fails).
- `test_t5b_a_preflight_refusal_and_a_post_stop_skip_spell_distinct_reasons` — Task 5's zero-request test: `ByteLocatorUntested("unpinnable")` then `ByteLocatorUntested("skipped-after-stop")` twice, reasons distinct, zero requests, exactly one re-check intent.
- `test_t5c_no_entry_outcome_constructs_an_observation` — Task 5's forged-ref test (`monkeypatch` `acquire.look` to return a ref no act published): `AcquisitionRefused`, no act-report, the operation intent unmatched (`completion` reads `UNFINISHED` over the chain's registrations); and, positively, every `PublishedObservation` ref in a successful report resolves to a `holdings-observation` node whose `event_token` equals the token of a re-check or write intent in the chain.
- `test_t7a_the_dataset_and_its_report_publish_in_one_transaction_in_one_root` — Task 5's happy-path assertions over the closing registration's `final` rows (both paths in the one registration); then a writer over a second registered root with the same context: `AcquisitionRefused` before the intent (chain unchanged in both roots, zero requests).
- `test_t7b_the_address_is_unchanged_while_the_record_bytes_move` — two observer roots, the same scripted bytes: equal dataset ids, distinct `retrieval` refs, distinct `node_to_markdown` bytes, and distinct corpus-state identities (`stored`/`world` — the identity `capture_coverage` reports as `corpus_state`, or `Corpus(root).state_identity()`; read `test_holdings_capture.py` for the accessor).
- `test_t1a_a_raw_written_report_is_undetected_on_read_and_refuted_under_anchors` — on `test_deletion_acceptance.test_g8_c6_raw_removal_refutes_and_managed_delete_validates`'s shape: `raw_write(root, stored.act_report_node(report))` of a self-consistent acquisition report (mint it with `_mint_acquisition_report` over a real intent token); `writer.read_view.holds(ref)`; `corpus_check(view, BASE) == ()`; `_audit_log(writer)` under the root's own anchored observer set is `refuted` with the raw path among its disagreements; `_audit_log` with an **empty** observer set is `unresolvable` (copy `_audit_log` and `_log_observer` from that module).
- `test_t2a_an_acquisition_closes_through_exactly_one_report_after_its_intent` — the happy path: exactly one act-report in the root; `completion(...) == CLOSED`; the operation intent's chain index is below every re-check and write intent's and every registration's.
- `test_t2b_root_selection_failure_begins_no_act` — Task 6's store-less session and Task 5's port-less writer: chain unchanged, no request, no record.
- `test_t2c_intent_append_failure_begins_no_act` — a writer whose port's `append_intent` raises `ExecutionError("refused", index=None, applied=0)` (wrap the durable port in a small refusing proxy passed as `port=`): the error propagates, no request issued, chain and corpus unchanged.
- `test_t2d_a_second_fulfillment_is_refused_and_a_raw_one_is_malformed` — after the happy path, `writer._publish_operation_report(outcome.report, intent_digest, operations=(writer._create_op(some_other_node),))` with the same `intent_digest` raises `ExecutionError` whose message carries "already fulfills" (the coordinator's rule, `commands.py:316`); then, over a copy of the root, append a raw settlement/registration pair fulfilling the same intent with the chain codec `test_world_log_codecs.py` uses to write entries, and `science_root._log_seam().inspect_registered(copy)` is `MalformedView` with `defect.kind == "duplicate-fulfillment"`.
- `test_t4a_reports_leave_the_projection_unchanged_and_an_unfinished_operation_blocks_nothing` — fixed holdings evidence (one acquisition's observations), then reports added and removed around it: reduce (`derive_holdings`); run a second acquisition through an **unpinnable** seam (it adds one act-report and one unmatched re-check intent and publishes no observation — a second look that published would add an identity-bearing observation and move the active set, which is H4's business, not T4's); reduce: the `active` and `blocked` outputs are byte-identical (`output_digest`), the receipt's coverage state differs; `writer.delete(that report's ref)` and reduce: still byte-identical; then append an `acquisition` operation intent through the port with no fulfillment and reduce again: `blocked == []`.
- `test_t4b_deleting_a_referenced_observation_moves_the_active_set_and_not_the_report` — `writer.delete(observation ref)` after a URL acquisition: the active set loses the head, the report's bytes (`node_to_markdown`) are unchanged and `cite(report, 0)` resolves.
- `test_bi1_two_spellings_of_one_url_are_one_location` — two looks at `https://EXAMPLE.org:443/a/./b` and `https://example.org/a/b` through the same script: one location key in the reduction with two heads coalesced as agreeing (both in `active`, same `location`).
- `test_bi2_no_hop_bytes_enter_any_record_or_reason` — three hops through `acquire`, each a **stopped outcome, not an exception** (a refused hop is `Failed`, the look `InconclusiveLook`, the operation `Stop(resource, "look", reason)` and a closed report): the signed-query hop and the token-host hop refused at preflight (Task 3's two cases, a resolver answering `10.1.1.1` for the hop's host), and the token-host hop approved at preflight but refused by certificate validation over the TLS server (`served({"/a": Served(302, {"Location": TOKEN_HOST_HOP})})` → `Stop("a", "look", "transport failure: tls")`). For each run, `outcome.stop is not None`, the entry reads `RetrievalFailed(...)` naming the ordinal and category (or the transport category), and for each secret string — the signature, the credential, the token, both hosts — assert it occurs in no file under the observer root (`rglob("*")`, read as bytes), under the scratch root, in no entry's `subject` or `reason`, in `outcome.stop.reason`, and in the report's `node_to_markdown` bytes.
- `test_bi3_the_pinned_connection_dials_the_validated_address` — Task 3's two pinning tests over the production `pinned_connection` with `create_connection` monkeypatched (no socket opens); and `acquire` with an unpinnable seam issues zero requests.
- `test_bi4_the_ceiling_finalizes_no_digest` — `acquire` over the TLS server with `max_bytes` below the body: the entry reads `RetrievalFailed("exceeded the N-byte streaming ceiling")`, no observation minted, scratch empty; the server's log shows one request.
- `test_bi5_an_expectation_mismatch_mints_no_dataset_and_reports_mismatch` — Task 5's expectation test over the reduction: `dataset_observations` over the real `derive_holdings` outputs, `admission_state` reports a `mismatch` finding.
- `test_bi6_an_already_held_address_mints_no_second_dataset` — Task 5's test.
- `test_bi7_the_url_looks_intent_blocks_nothing` — a look whose `publish_fulfilling` raises after `Retrieved` (the re-check intent unmatched); reduce: `blocked == []` and the reduction's qualification reads the intent `unmatched` (read it off the rule's output shape or the `unsettled` absence).
- `test_bi8_no_lock_is_held_across_the_request` — Task 5's helper-thread probe, and Task 6's session-route check: the concurrent `add` completes while the request is open, and every `_SettlingHold.__enter__` during the route saw the session lock owned.
- `test_bi9_the_successor_rule_keeps_old_receipts_validatable` — install the shipped bundle; derive a receipt; `validate_holdings_receipt` → `validated`; assert the binding's `rule_identity` and `implementation_identity` differ from the pair `docs/plans/2026-08-24-conformance-cut-10-results.md` records (grep it; if it records none, assert they differ from `git show 3873d16:python/src/beliefs/holdings/rules_v1/holdings.py`'s bundle identity computed in-test); a receipt minted under the **old** bundle (installed from those bytes as a second `RuleBundle`) still validates in the same world.
- `test_bi10_url_intents_and_observations_decode_and_reconcile` — over the durable session after `acquire`: `reconcile_sessions` over its ledger and chain yields no finding; `decode_intent` over the chain's re-check intent is a `DecodedIntent` of shape `holdings` with the `url:` key; `evidence.decode_record` (the evidence module's entry point) over the observation file yields `ObservationEvidence("url:…", token)`.
- `test_bi11_the_materialization_classification` — Task 5's two `_read_only_store` tests (first and last resource), the publication-failure-after-materialization test with `ExecutionError(applied=0) from PreconditionRefused`, the `SessionProtocolError` test, and the `RuntimeError`-cause negative — all five in one test function, each assertion block labeled.

- [ ] **Step 2: The declaration file**

`python/tests/n2_arms_cut35.py` on `n2_arms_cut34.py`'s shape: `DECLARATION_UNITS` = the twenty-seven; `_MODULE = "acceptance/test_url_retrieval_acceptance.py"`; `UNIT_CHECKS` to the names above; `CO_CITED = ()`; `unit_of` (`"BI-11"` is a unit; `"BI-11a"` is not — the two lettered sabotage arms share the unit through `unit_of(row.rstrip("ab"))` only for `BI-11a`/`BI-11b`: write `unit_of` as "strip a trailing `a`/`b` when the remainder is `BI-11`"); `CUT35_ARMS` with `before` copied verbatim from the tree at freeze:

| arm | module | `before` (as Tasks 1–6 write it) | `after` |
|---|---|---|---|
| H4-a | `holdings/boundary.py` | `    except BaseException:\n        result.path.unlink(missing_ok=True)  # ownership never reached the caller\n        raise` | `    except BaseException as caught:\n        result.path.unlink(missing_ok=True)  # ownership never reached the caller\n        if isinstance(caught, ExecutionError):\n            return InconclusiveLook("retrieval-failed", str(caught))\n        raise` — an established `found` whose publication failed reads as an inconclusive attempt instead of raising |
| H4-b | `holdings/boundary.py` | `    if isinstance(result, NotAttempted):\n        return InconclusiveLook("byte-locator-untested", result.reason)` | `    if isinstance(result, NotAttempted):\n        _publish_record(ctx, holdings_observation(location=location, outcome=Found("sha256:" + "0" * 64), expected=expected, observer=ctx.observer, instrument=ctx.instrument, event_token=token, observed_at=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"), supersedes=standing), intent)\n        return InconclusiveLook("byte-locator-untested", result.reason)` — a non-answer laundered into a finding (the unpinnable case in the check); "exactly one record, the standing one" fails |
| G9-a | `holdings/adapter.py` | `        if (found := _joined(member, declared)) is not None` | `        if not cast(str, member["location"]).startswith("url:") and (found := _joined(member, declared)) is not None` |
| R10-a | `holdings/acquire.py` | `                empirical_observation={"locator": request.locator, "attested_by": ctx.actor, "retrieval": report_node.id},` | `                empirical_observation={"locator": request.locator, "attested_by": ctx.actor},` |
| T5-a | `holdings/boundary.py` | `        return InconclusiveLook("retrieval-failed", result.reason)` | `        return InconclusiveLook("byte-locator-untested", result.reason)` — a began request classified as untested |
| T5-b | `holdings/acquire.py` | `            entries.append(LocatorEntry(subject, ByteLocatorUntested(SKIPPED_AFTER_STOP), inputs))` | `            entries.append(LocatorEntry(subject, ByteLocatorUntested(stop.reason), inputs))` |
| T5-c | `holdings/acquire.py` | `        for ref in sorted(published):\n            if writer.read_view.resolve(ref) is None:` | `        for ref in ():\n            if writer.read_view.resolve(ref) is None:` |
| T7-a | `holdings/acquire.py` | `            writer._refuse_acquired_dataset(dataset, report_node)\n            operations.append(writer._create_op(dataset))` | `            writer._refuse_acquired_dataset(dataset, report_node)\n            (writer._operation_port if port is None else port).execute([writer._create_op(dataset)])` — the dataset lands in its own non-fulfilling transaction before the report's; the closing registration no longer carries both paths |
| T7-b | `stored.py` | `    return _node("dataset", address.partition(":")[2], title, facets, ())` | `    return _node("dataset", address.partition(":")[2] + ("-" + str(empirical_observation.get("retrieval"))[-8:] if empirical_observation is not None and "retrieval" in empirical_observation else ""), title, facets, ())` — the id moves with the report; two acquisitions of one byte set no longer share an id |
| T1-a | `world/verify.py` | the body of `_claimed_by_the_corpus_layout` (line 259; two lines — copy them at freeze) | the same expression conjoined with `not path.startswith("act-report/")`, so a raw-created report is outside the surface and replay never sees it |
| T2-a | `holdings/acquire.py` | `    intent_digest = writer._append_operation_intent(intent.kind, intent.event_token, intent.actor, port=port)` | `    look(ctx, request.resources[0].url, bounds=request.bounds, seam=seam, scratch=scratch)\n    intent_digest = writer._append_operation_intent(intent.kind, intent.event_token, intent.actor, port=port)` — a look (and its re-check intent) precedes the operation intent |
| T2-b | `holdings/acquire.py` | `    if port is None and writer._operation_port is None:\n        raise AcquisitionRefused("this corpus has no operation port; acquisition is a boundary operation")` | `    if False:\n        raise AcquisitionRefused("this corpus has no operation port; acquisition is a boundary operation")` |
| T2-c | `corpus.py` | `        digest = operation_port.append_intent(_encode_operation_intent(kind, token, self.authority.actor))` | `        try:\n            digest = operation_port.append_intent(_encode_operation_intent(kind, token, self.authority.actor))\n        except ExecutionError:\n            digest = "0" * 64` — the append failure swallowed; the looks proceed and "no request issued" fails |
| T2-d | the module holding the closed defect mapping (`grep -n '"duplicate-fulfillment"' python/src/beliefs/root.py python/src/beliefs/world/logmodel.py` at freeze) | the mapping member for the engine's second-fulfillment defect | mapped to `"fulfills-invalid"`; the check asserts `defect.kind == "duplicate-fulfillment"`. The coordinator's refusal of a second `execute_fulfilling` is the engine's rule and is read, not sabotaged |
| T4-a | `holdings/qualify.py` | `    if not isinstance(value, dict) or value.get("domain") != HOLDINGS_INTENT_DOMAIN:\n        return None` | `    if not isinstance(value, dict) or value.get("domain") != HOLDINGS_INTENT_DOMAIN:\n        return {"digest": row["digest"], "actor": "x", "event_token": str((value or {}).get("event_token", "")) if isinstance(value, dict) else "", "kind": "write", "location": "url:https://sabotage.example/"}` — an `acquisition` operation intent reads as an unmatched write and blocks a location |
| T4-b | `corpus.py` | the first statement of `CorpusWriter._delete_locked` (read it at freeze) | preceded by a scan: `        for other in self._view.iter_stored():\n            facet = other.facets.get("act-report")\n            if isinstance(facet, dict) and any(node_id in str(entry) for entry in facet.get("entries", ())):\n                raise WriteRefused(f"{node_id}: referenced by {other.id}")` — the report confers protection; the check's `delete` refuses |
| BI-1 | `holdings/records.py` | `    authority = host if port in (None, _DEFAULT_PORTS[scheme]) else f"{host}:{port}"` | `    authority = host if port is None else f"{host}:{port}"` — the default port is kept, so `https://EXAMPLE.org:443/a/./b` and `https://example.org/a/b` are two locations in the reducer (spec §11.3 named host case; `urlsplit` already lowercases both scheme and host, so neither is a mutation) |
| BI-2 | `holdings/transport.py` | `            return Failed(f"redirect hop {hop} refused: {decision.category}")` | `            return Failed(f"redirect hop {hop} to {urlsplit(current).hostname} refused: {decision.category}")` |
| BI-3 | `holdings/transport.py` | `        sock = socket.create_connection((self._address, self.port), self.timeout)` | `        sock = socket.create_connection((self.host, self.port), self.timeout)` |
| BI-4 | `holdings/transport.py` | `            if size > bounds.max_bytes:\n                return Failed(f"exceeded the {bounds.max_bytes}-byte streaming ceiling")` | `            if size > bounds.max_bytes:\n                return Retrieved(digest=f"sha256:{hasher.hexdigest()}", size=size, path=target)` |
| BI-5 | `holdings/acquire.py` | `    expectations_hold = all(r.expected is None or digests.get(r.name) == r.expected for r in request.resources)` | `    expectations_hold = True` |
| BI-6 | `holdings/acquire.py` | `        held = address is not None and writer.read_view.resolve(address) is not None` | `        held = False` |
| BI-7 | `holdings/boundary.py` | `    token, intent = _append(ctx, location, "re-check")\n    result = retrieve(location, bounds, seam, scratch)` | `    token, intent = _append(ctx, location, "write")\n    result = retrieve(location, bounds, seam, scratch)` |
| BI-8 | `holdings/acquire.py` | `        result = look(\n            ctx, resource.url, bounds=request.bounds, seam=seam, scratch=scratch,\n            expected=resource.expected, standing=standing.get(subject, ()),\n        )` | `        with writer._operation:\n            result = look(ctx, resource.url, bounds=request.bounds, seam=seam, scratch=scratch, expected=resource.expected, standing=standing.get(subject, ()))` |
| BI-9 | `holdings/qualify.py` | `    if value["type"] == "url":\n        if set(value) != {"type", "url"} or not _url(value["url"]):\n            return None\n        return "url:" + value["url"]` | `    if value["type"] == "url":\n        return None` |
| BI-10 | `intents/evidence.py` | `        return ObservationEvidence(value.location.canonical(), value.event_token)` | `        return ObservationEvidence(f"store:{value.location.store_id}:{value.location.relative_path}", value.event_token)` |
| BI-11a | `holdings/boundary.py` | `    try:\n        outcome = ctx.seam.store_write(ctx.store_root, location.relative_path, content)\n    except ExecutionError as caught:\n        if store_refusal(caught):\n            raise StoreWriteRefused(location.canonical(), str(caught)) from caught\n        raise\n    state = _final(outcome, location.relative_path)` | `    try:\n        outcome = ctx.seam.store_write(ctx.store_root, location.relative_path, content)\n        state = _final(outcome, location.relative_path)\n        if isinstance(state, FileStateView):\n            return _publish_record(ctx, holdings_observation(location=location, outcome=Found(state.content_hash), expected=expected, observer=ctx.observer, instrument=ctx.instrument, event_token=token, observed_at=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"), supersedes=standing), intent)\n    except ExecutionError as caught:\n        if store_refusal(caught):\n            raise StoreWriteRefused(location.canonical(), str(caught)) from caught\n        raise` — the wrap widened to the publication; the check's publication failure (`applied=0`, `PreconditionRefused`) reads as a stop |
| BI-11b | `holdings/boundary.py` | `    return caught.applied == 0 and type(caught.__cause__) in _ROUTINE_REFUSALS` | `    return True` |

Every `before` must occur exactly once in its module and the mutated module must `ast.parse`; no two arms share a `before`. Where the table says "read at freeze", the implementer copies the exact bytes from the tree and records the choice in the results record. `python/tests/acceptance/n2_arms_cut35.py` re-exports the five names.

- [ ] **Step 3: The guard and the runner**

`python/tests/acceptance/test_n2_cut35.py` on `test_n2_cut34.py`'s shape: `FROZEN_CUT = REPO_ROOT / "docs" / "designs" / "2026-09-20-conformance-cut-35.md"`, `CUT35_FREEZE_COMMIT`, `CUT35_FROZEN_SHA256` (Task 0), `FROZEN_DECLARATION = "python/tests/n2_arms_cut35.py"` with `CUT35_DECLARATION_SHA256` pinned once final, `FROZEN_PRIOR_CUT_FILES` = cut 34's dict plus `"python/tests/n2_arms_cut34.py": "<git log -1 --format=%h -- python/tests/n2_arms_cut34.py>"`, `PRIOR_ARMS` extended with `CUT34_ARMS`, the inventory test asserting twenty-seven with the two lettered arms homed to `BI-11` (`len(CUT35_ARMS) == 28`, `len(DECLARATION_UNITS) == 27`, and `homed == {unit: 2 if unit == "BI-11" else 1 ...}`), the freeze-pin test asserting `"**27 declaration units**"` and `'("cut34_acceptance.py",)'`, `test_every_acceptance_test_the_arms_name_exists` over the new module, the staleness audit with the tree's baseline. `python/tools/cut35_acceptance.py` is `cut34_acceptance.py` with `34→35`, `PREFIX_RUNNERS = ("cut34_acceptance.py",)`, `PHASE_MODULES = ("test_url_retrieval_acceptance.py", "test_n2_cut35.py")`, `DEFAULT_WORK = MAIN_CHECKOUT / ".work" / "acceptance" / "cut35"`, `declared_accounting` from `n2_arms_cut35` counting rows `{H4, G9, R10, T5, T7, T1, T2, T4}` and printing "guarantee rows exercised: 8 (6 newly closed: H4, G9, R10, T5, T1, T4; T2 and T7 partial)".

- [ ] **Step 4: Freeze the declaration, discharge, commit**

Pin `CUT35_DECLARATION_SHA256`; `cd python && uv run --frozen pytest tests/acceptance/test_n2_cut35.py -q -k "not sabotage"`; then on the certified volume `SCIENCE_CUT35_ROOT=/mnt/ssd/Dropbox/beliefs/.work/acceptance/cut35 uv run --frozen python tools/cut35_acceptance.py` (the runner exports the prefix chain's roots itself), then `just hook-pre-push`. Record both summary lines. Every arm `sound`, the baseline `resolved`, no `stale`.

```bash
tasks check
tasks done beliefs-eea81b "cut 35 discharged on the certified volume: 27 units, 28 arms sound"
git add python/tests/acceptance python/tests/n2_arms_cut35.py python/tools/cut35_acceptance.py tasks
git commit -m "test(cut): discharge conformance cut 35 — H4, G9, R10, T5, T1, T4; T2, T7 partial; BI-1..11"
```

---

### Task 9: Results record, ledger, roadmap, guide, amendments, closeout

**Files:**
- Create: `docs/plans/2026-09-20-conformance-cut-35-results.md`
- Modify: `docs/designs/2026-09-20-conformance-cut-35.md` (`**Status:**` only), the spec (`**Status:**`), `docs/designs/2026-08-03-redesign-adoption-ledger.md` (`Current state`: a new built bullet for URL retrieval and the acquisition operation; `url-retrieval` leaves the open table; `act-report-remainder`'s row becomes "T2's `audit` and `re-check` operation kinds"; the summary names cut 35; **183 of 216**), `docs/plans/2026-08-29-implementation-roadmap.md` (rewritten whole: `Ranked at: cut 35`; a `Cut 35 (2026-09-20)` paragraph; tier 1 off-path row 1 removed and later rows renumbered; the ride-along table loses `act-report-remainder`, which becomes an off-path boundary row after `l13-preimage` in the `world-read` lane's column; the lane table's `acquisition` row "closed 2026-09-20 at cut 35"; Appendix A regenerated by `python/tools/roadmap_status.py`; Appendix B rows G9, R10, H4, T5, T1, T4 removed, T2 and T7 rewritten; the boundary index row for `act-report-remainder` re-pointed to its own task), `docs/guide/contracts-and-adoption.md` (the cut-35 line as discharged; totals), `README.md` ("through **cut 35**"; the table row; "The latest discharged boundary is cut 35"), the guide's kinds/outcomes tables (`url` locator; `acquisition` operation; `grep -rn "byte-locator-untested\|holdings observation" docs/guide/*.md`), `docs/guide/open-questions.md` (the act-report residue: "new operation kinds — closed at five" is stale since cut 16; `acquisition` is built), the dated notes of spec §14 in `2026-08-10-verified-holdings-record-design.md` (§2 url row; §3 "intent-free" sentences), `2026-08-11-act-report-design.md` (§2.2, §3.1), `2026-08-09-admission-ramp-design.md` (§4, §6.6), `2026-08-02-computation-reproducibility-design.md` (§4.7), `2026-08-24-world-index-holdings-design.md` (§1 item 1, §3, §6)
- Tasks: step children done as their commits land; `beliefs-d13fe8` at the results commit; ideas filed (spec §16); `act-report-remainder`'s task re-scoped

- [ ] **Step 1: Status lines** — the cut document: "discharged 2026-09-20 on the certified volume; results: `../plans/2026-09-20-conformance-cut-35-results.md`"; the spec: "discharged at conformance cut 35 on 2026-09-20; results: `../../plans/2026-09-20-conformance-cut-35-results.md`".

- [ ] **Step 2: The results record** — on cut 34's shape (`docs/plans/2026-09-19-conformance-cut-34-results.md`): §1 what ran (both summary lines verbatim; the per-unit table with 28 arms over 27 units); §2 accounting (H4, G9, R10, T5, T1, T4 closed; T2 partial on `audit`/`re-check`; T7 partial on cross-root; the global count 183/216); §3 evidence (corrections carried by the cut document; deviations from the plan, every "read at freeze" choice recorded; limitations found at review); §4 the reproduction (§14 of the record); §5 `## Remaining boundary` — T2's two operation kinds, T7's cross-root case, and the ideas filed; §6 main integration (filled at merge); §7 execution rulings.

- [ ] **Step 3: Ledger, roadmap, guide, README, the amendments** — as the Files block says. `cd python && uv run --frozen python tools/roadmap_status.py` for Appendix A; `uv run --frozen pytest tests/test_designs_corpus.py tests/test_check_guide.py -q` green (`test_the_roadmap_and_ledger_name_the_same_boundaries` and `test_the_ledger_summary_names_the_newest_remaining_boundary` hold the three documents together).

- [ ] **Step 4: Tasks**

```bash
tasks edit beliefs-d13fe8 --title "Deliver URL acquisition and act-report coverage"   # unchanged; the ride-along's remainder moves to its own task:
tasks add "Open the audit and re-check operation kinds: T2's remainder" -p 3 --size m --complexity mid --tag migration --tag act-report \
  -b "act-report-remainder after cut 35: T2 reads every built operation kind; audit and re-check have no boundary that opens an intent and mints a report (act-report design §4's wrapper). Surface: audit.py, world/audit.py, holdings/boundary.py — the world-read lane's column. Off the path."
tasks add "IDNA host names in the url locator" --status idea --tag holdings \
  -b "url-retrieval design §13.3: a non-ASCII host refuses at construction; an IDNA canonicalization rule is a profile amendment to holdings §2."
tasks add "A store-less look route through the session" --status idea --tag holdings --tag session \
  -b "url-retrieval design §13.6: acquire through the session needs a bound store because holdings_context does; a look-only acquisition over a store-less session is undesigned."
tasks done beliefs-cb43c2 "results record, ledger, roadmap, guide, amendments"
tasks done beliefs-d13fe8 "URL retrieval discharged at cut 35: the url locator, the transport, the acquisition operation; H4, G9, R10, T5, T1, T4 closed; T2 and T7 partial; results docs/plans/2026-09-20-conformance-cut-35-results.md"
tasks check
git add docs README.md tasks
git commit -m "docs(cut): discharge conformance cut 35; URL retrieval closes H4, G9, R10, T5, T1 and T4"
```

(the new T2 task's id goes into the roadmap's boundary index row for `act-report-remainder`; `tasks edit` its `--depends` on nothing.)

- [ ] **Step 5: Merge** — from the main checkout: `git merge --no-ff url-retrieval -m "merge: URL retrieval — conformance cut 35"`, `just gate` on the merged tree, then record the merge commit in the results record's §6 (`docs(cut35): record merged-main verification`). The lane is closed: `git worktree unlock .worktrees/url-retrieval` then `git worktree remove .worktrees/url-retrieval` after the results record and every ledger under it are on `main` (memory `execution-ledgers-are-durable-artifacts`).

---

## Self-review

**Spec coverage.** Decision 1 → Task 1; decision 2 → Task 4 (`look`'s `re-check` intent), Task 2 (`_location`'s url arm); decision 3 → Task 5 (`AcquisitionRequest`, the four steps, the overlay validation); decision 4 → Task 5 (`mint = stop is None and expectations_hold`); decision 5 → Task 5 (the stop and `SKIPPED_AFTER_STOP`); decision 6 → Task 3 (`preflight` categories, `Failed(f"redirect hop … refused: …")`); decision 7 → Task 3 (`RetrievalBounds`, `_stream_into` dropping the hash), Task 5 (`instrument_inputs` on every entry); decision 8 → Task 3 (`target`, `authority`, `Accept-Encoding`, the body rules, `refuse_scratch_root`); decision 9 → Task 3 (`UrlSeam`, `url_seam`, the fixtures); decision 10 → Task 4 (`store_refusal`, the wrap), Task 5 (`except StoreWriteRefused`); decision 11 → Task 5 (`held`); decision 12 → Task 9 (the new task and the ledger row); decision 13 → Task 8 (T2-d); decision 14 → Task 2 (the fixture and the reducer key), Task 8 (BI-9); decision 15 → Task 5 (locks only inside the acts and the close), Task 6 (no `_act` wrap); decision 16 → Task 1 (the deletion and the J3 re-target). §3 → Task 1; §4 → Task 3; §5 → Task 4; §6 → Task 5; §7 → Task 2; §8 → Task 6; §9 → Task 8; §11.1 → Tasks 1–6; §11.2–11.4 → Task 8; §11.5 → Task 1 Step 6 and the global constraint; §12 → the file map; §13 → Task 9's ideas; §14 → Task 9; §15 → Task 7; §16 → Task 0 Step 3 and Task 9.

**Planning corrections, to record in spec §17 at Task 0.** (a) Spec §6 has `acquire` call `writer._append_operation_intent` and `_publish_operation_report`, which use the writer's own port; under the session the ledgered port is a separate object (`ScopedWriter.operation_port()`), so both members gain a `port=` override and the session route passes it (Task 5 Step 4, Task 6 Step 3). (b) Spec §11.1's session-route test cannot run over the routes module's `FakeSeam`, which publishes nothing to disk, while the close checks every published observation resolves; the session test runs over the certified volume with the production seam (Task 6). (c) Spec §11.3's T2-d sabotage named `acquire.py`; a second fulfillment's refusal is the engine's, so the arm sabotages the defect mapping's `duplicate-fulfillment` member instead (Task 8). (d) `AcquisitionOutcome.entries` is the report's entries, the declaration-pin entry included. (e) Spec §6 step 4 resolves the looks' refs through `writer.read_view`; those publications go through the holdings seam and never set the writer's `unresolved`, so the close rebuilds the view (`_reconstruct`) under its lock before resolving anything (Task 5). (f) Spec §6/§8 left the close's lock order implicit; the session takes session-then-root everywhere, so `acquire` gains `hold`, entered before the root lock, and the route passes `_closing_hold` (Tasks 5, 6). (g) Decision 6's rule extends to transport failures: a certificate error's text names the redirected host, so a failure after the request began is named by a fixed category (`timeout`, `tls`, `connection`, `protocol`), `HTTPException` included, and every exceptional exit unlinks the scratch file (Task 3). (h) Decision 1's profile is read strictly: the trailing slash after a final dot-segment is kept, an IPv6 host keeps its brackets (its literal is not compressed — a limitation beside IDNA), and port `0` is refused (Task 1). (i) Decision 7's ceiling bounds each read by the remaining allowance plus one, and `timeout_seconds` is finite (Task 3). (j) Decision 8's scratch exclusion is `look`'s own, before its intent, not only `acquire`'s (Task 4). (k) §6 step 1's "validated as a value" covers the dataset's request-only metadata: `domain_facets` at the request, and the dataset's shape through `_refuse_dataset_shape` before the intent (Task 5). (l) §4's "keeps its own copies of nothing": the survey's `NetworkProbe.fetch` is an adapter over `retrieve`, and a refused hop reads `retrieval-failed` there too (Task 6). (m) §11.2's in-process TLS server is a committed test certificate plus `LocalTlsServer`/`tls_seam`; the unit and acceptance suites run their success, truncation, redirect, ceiling and certificate-failure cases through it (Tasks 3, 8). (n) Three checks read differently from §11.2/§11.3: T4-a's added report comes from an unpinnable acquisition, since a second look publishes an identity-bearing observation; BI-2's refused hops are stopped outcomes, never exceptions; BI-1's arm sabotages default-port elision, since `urlsplit` lowercases scheme and host itself (Task 8).

**Placeholder scan.** `<taskN-id>` is filled at the planning commit (Task 0 Step 3). "Read at freeze" appears for three sabotage sites whose exact bytes are the tree's at the freeze (T1-a, T2-d, T4-b) — the behavior of each `after` is fixed above; the implementer copies the bytes and records the choice (Task 9 Step 2). Task 5's `registrations_of`/`report_of` helpers are named with their shape; Task 6's `ACQUIRES` capability is spelled with the reference to `RUNS`.

**Type consistency.** `UrlLocator(url)`, `url_locator(spelling)`, `Locator` (Tasks 1, 2, 4, 5); `RetrievalBounds(timeout_seconds, max_bytes, max_redirects)` with `.instrument_inputs()` (Tasks 3, 5, 8); `Approved(host, port, target, authority, address)` (Tasks 3, 6); `retrieve(locator, bounds, seam, scratch) -> Retrieved(digest, size, path) | NotAttempted(reason) | Failed(reason)` (Tasks 3, 4); `look(ctx, location, *, bounds, seam, scratch, expected=None, standing=()) -> PublishedLook(record, ref, retrieved) | InconclusiveLook(report, reason)` (Tasks 4, 5, 8); `store_refusal(caught) -> bool`; `StoreWriteRefused(location, detail)` (Tasks 4, 5); `ResourceRequest(name, url, expected=None, materialize=None)`, `AcquisitionRequest(title, locator, resources, bounds, domain_facets=None)`, `Stop(resource, phase, reason)`, `AcquisitionOutcome(report, report_ref, dataset, entries, stop)`, `acquire(ctx, writer, request, *, seam, scratch, standing=None, port=None, hold=None)` (Tasks 5, 6, 8); `CorpusWriter._refuse_dataset_shape(node)` (Task 5); `ScopedWriter._closing_hold()` (Task 6); `_mint_acquisition_report(intent, *, observer, instrument, opened_at, closed_at, entries)` (Tasks 5, 8); `CorpusWriter._append_operation_intent(kind, token, actor, *, port=None)`, `_publish_operation_report(report, digest, *, operation=None, operations=None, port=None)`, `_refuse_acquired_dataset(node, report)` (Tasks 5, 6, 8); `ScopedWriter.acquire(request, *, instrument, scratch, seam=None, standing=None)` (Tasks 6, 8); `scripted_seam(script, *, log=None, unpinnable=False) -> (UrlSeam, RequestLog)`, `Scripted(status, headers, chunks, raise_on_read=None, raise_on_request=None)`, `RequestLog(requests, dialled, reads)`, `Served(status, headers, body, truncate_chunked=False)`, `LocalTlsServer(script)` with `.port`/`.log`, `tls_seam(server) -> (UrlSeam, RequestLog)` (Tasks 3–6, 8); `TRANSPORT_CATEGORIES` (Tasks 3, 8).
