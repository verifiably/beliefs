---
id: beliefs-27d500
title: "Cut-35 review polish: thirteen mechanical fixes in holdings, corpus and their tests"
status: todo
priority: 3
size: m
complexity: low
process: direct
created: 2026-09-20T15:50:53Z
updated: 2026-10-09T11:32:05Z
depends: []
tags: [holdings, hygiene]
agent: "claude-code/claude-opus-5[1m]"
---

Why: cut 35's final review (url-retrieval, merged 2026-09-20) deferred these as minor; an audit on 2026-10-09 against main `ad76060` found every one still open and none filed elsewhere. Two of them hide real failures: a resolver returning a non-IP string raises `ValueError` instead of a refusal (1), and a fixture's `handle_error` swallows handler exceptions that should fail a test (2).

Done when: each item below is fixed as stated, items marked "test" gain a test that fails before the fix, and `just test-fast` passes. No behaviour outside these lines changes; no conformance cut is needed.

Where to look (paths from the repository root; `src/` = `python/src/beliefs/`):

1. `src/holdings/transport.py:216`: `ipaddress.ip_address(...)` runs outside the `try` at 209–213. Catch `ValueError` and return the `unresolvable` refusal. Test: a scripted resolver returning `"not-an-ip"`.
2. `python/tests/holdings_transport_fixtures.py:171-172`: `handle_error` is `pass`. Swallow only the expected `ssl.SSLError`/`ConnectionResetError`; delegate everything else so it surfaces.
3. `src/holdings/transport.py:63-66`: give `RetrievalBounds` a docstring saying `timeout_seconds` bounds each socket operation (passed to `seam.connect` at :244), not the whole retrieval.
4. `src/holdings/acquire.py:222` (and the `assert` at :240): replace the production `assert address is not None` with an explicit `AcquisitionRefused`.
5. `src/holdings/acquire.py:48-49`: `LOCATOR_SCHEMES` is a literal copied from CONTRACT.yaml. Derive it from the loaded contract, or add a test that pins it equal to the contract's set.
6. `src/corpus.py:2697-2716`: `_publish_operation_report` silently ignores `operation=` when `operations=` is given and accepts `operations=()`. Refuse both-given and empty. Test both. Callers: `acquire.py:250`, `relocation.py`, `audit_operation.py:103`, `recheck.py:140`.
7. `src/corpus.py:3473-3488`: `_refuse_acquired_dataset` repeats `_validate_import_bundle`'s overlay idiom (:3211ff). Extract one helper; the existing tests cover both callers.
8. `src/holdings/acquire.py:113-117`: give `Stop` a docstring saying `reason` is in-memory diagnostics only and is never copied into a record.
10. `python/tests/test_holdings_acquire.py:391`: `..._the_hold_enters_before_the_root_lock` has no stop and proves only that the hold is taken while the root lock is free. Rename it to what it asserts, or add a root-inside-hold probe. `:281` (`..._reads_unfinished`) never asserts `UNFINISHED`, so add the assertion.
11. `python/tools/survey_admission.py`: `APPROVED_SCHEMES` (:73-74) is dead, so delete it. Restore the `Resolver`/`ConnectionFactory` annotations on `resolver=`/`connect=` (:299, :303). `python/tests/test_admission_survey.py:37`'s comment about patching `survey_admission.socket` is stale, so rewrite it.
12. `python/tests/test_capability_boundary.py:493-496`: the transport allowlist comment explains `unlink` only. Name the scratch-file `target.open("wb")` (`transport.py:291`) too.
15. `python/tests/acceptance/test_url_retrieval_acceptance.py:908-910`: BI-9 shells `git show 3873d16:` for the cut-34 holdings rule bundle (four fixtures, `qualify.py`, `rules_v1/holdings.py`), so a clone without that history fails. Vendor those bytes as test data beside the module, with an assertion that they rebuild the old binding's identity. Do not skip silently.
16. `src/holdings/acquire.py:223`: `closed_at` is stamped before the closing locks are taken (also deferred by the review, ledger Task 5). Stamp it inside the `with outer, writer._operation:` block.

Moved out (not this task): item 9 (`AcquisitionOutcome` cannot tell already-held from expectation-mismatch; an API decision with no consumer) → . Item 13 (port and percent-encoded-host canonicalization; intents `_url` looser than the profile) → beliefs-1af7a7. Item 14 (a cut arm for `_closing_hold`'s currency check) → .

Sources: `docs/plans/2026-09-20-url-retrieval-execution-ledger.md` (Task 5 minor (deferred) lines), the cut-35 results record, `docs/superpowers/specs/2026-09-19-url-retrieval-design.md` §13.

Original checklist (2026-09-20):
- [ ] transport `ip_address()` outside the try
- [ ] fixture `handle_error` swallows every handler exception
- [ ] `RetrievalBounds.timeout_seconds` is per socket operation (docstring)
- [ ] `acquire.py` production `assert address is not None` → explicit refusal
- [ ] `LOCATOR_SCHEMES` hand-copied from the contract
- [ ] `_publish_operation_report` accepts both `operation=` and `operations=` and `operations=()`
- [ ] `_refuse_acquired_dataset` duplicates `_validate_import_bundle`'s overlay idiom
- [ ] `Stop.reason` docstring: never copy into a record
- [ ] `AcquisitionOutcome` cannot distinguish already-held from mismatch
- [ ] test names `..._the_hold_enters_before_the_root_lock` and `..._reads_unfinished` vs what they assert
- [ ] `survey_admission` `APPROVED_SCHEMES` dead, `resolver=`/`connect=` annotations lost, `_SPEC` comment stale
- [ ] capability-boundary allowlist comment for transport should name `open("wb")` too
- [ ] spec §13 candidates: empty/leading-zero port and percent-encoded host, intents `_url` looser than the profile
- [ ] a cut row for `_closing_hold`'s currency check
- [ ] BI-9 shells `git show` (needs history)

## Notes

- 2026-10-09T11:32:03Z (main): scope: scoped; audited all 15 items against main ad76060 (all open, none filed elsewhere); body rewritten with file:line and fix per item, plus the review's deferred closed_at item; items 9, 13 and 14 moved to beliefs-9c4a4f, beliefs-1af7a7 and beliefs-bd85d0 (9 and 14 shelved); todo P3 m/low/direct
