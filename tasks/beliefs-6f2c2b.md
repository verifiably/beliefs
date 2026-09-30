---
id: beliefs-6f2c2b
title: Pin composite_identity in the mm30 recreation verdict
status: todo
priority: 3
size: xs
complexity: low
process: direct
created: 2026-09-30T10:37:37Z
updated: 2026-09-30T10:37:37Z
depends: []
parent: beliefs-cde4d9
tags: [reproduction]
agent: claude-code/claude-opus-5-5
---

Why: reproduction.verdict leaves composite_identity unchecked because the audit brief grouped it with the run-varying identities. It is not run-varying: composite.composite_identity hashes the facet, whose content is the three authored nodes and the member claim identities, with no run input. The first one-command recreation (record §25.2) confirmed it: ef546cde… equals the fixture's.

Done: EXPECTED['composite'] carries composite_identity with the fixture's full value; record §25.1's key count and §25.2's bullet on it are corrected in the same change (a new short addendum note or an in-place fix of the current-facing count, whichever AGENTS.md's freeze rule allows for an addendum).

Verification: just test-one tests/test_reproduction_driver.py (the parametrized group test covers the new key); the verdict over .work/reproduction/mm30-fresh-2026-09-30 still passes, if the directory is kept.

## Notes

- 2026-09-30T10:37:37Z (main): concerns: beliefs-9e0b42 extension — the verdict can pin composite_identity, which the brief misclassified as run-varying
