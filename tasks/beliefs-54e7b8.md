---
id: beliefs-54e7b8
title: audit_world drops corpus-damaged for a construction-damaged corpus excluded at scope base
status: idea
priority: 2
created: 2026-10-01T18:41:31Z
updated: 2026-10-01T18:41:31Z
depends: []
tags: [audit]
agent: claude-code/claude-opus-5-5
---

Pre-existing; found at cut 44's final re-review (mount-citations). In python/src/beliefs/audit.py, audit_world's per-corpus loop handles a base-pin damage report first, then 'if scope in ("base", "malformed"): excluded.add(corpus_id); excluded_scope[...] = scope; continue', and only after that appends the construction damage report's findings and the 'corpus-damaged' construction:<n> finding. Construction never reads the base pin (corpus.py ReadView construction) and open_world_view calls _require_base_pin only after ReadView.opened_at succeeds (world/view.py), so a corpus that both fails construction and pins a non-shipped base is classified construction-damaged, not base-pin; the audit then excludes it at scope base and continues before reporting the damage. Its per-corpus findings carry profile-mismatch (base) but neither the construction failures nor corpus-damaged. Reproduce with test_world_audit.py's _cross_world: damage(BETA, 'parse-error'), rewrite BETA's manifest science pin to science:+'0'*64, audit_world → audit.corpora[BETA] has no corpus-damaged. Fix: report the damage (report.findings plus corpus-damaged) before the exclusion's continue, or classify such a corpus as base-pin damage; decide which, add the test, and check that the J19 excluded-holder test (test_j19_an_excluded_holder_is_unresolved) still sees excluded:base or update it with the ruling.
