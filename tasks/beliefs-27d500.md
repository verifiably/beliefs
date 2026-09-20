---
id: beliefs-27d500
title: "Cut-35 review follow-ups: polish items deferred at merge"
status: idea
priority: 2
created: 2026-09-20T15:50:53Z
updated: 2026-09-20T15:50:53Z
depends: []
tags: [holdings, hygiene]
agent: "claude-code/claude-opus-5[1m]"
---

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
