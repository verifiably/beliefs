---
id: beliefs-54e7b8
title: audit_world drops corpus-damaged for a construction-damaged corpus excluded at scope base
status: todo
priority: 2
size: s
complexity: mid
process: direct
created: 2026-10-01T18:41:31Z
updated: 2026-10-09T11:14:10Z
depends: []
parent: beliefs-7e341d
tags: [audit]
agent: claude-code/claude-opus-5-5
---

Why: audit_world (python/src/beliefs/audit.py) drops a corpus's construction damage when the corpus is also excluded at scope base. The per-corpus loop handles a base-pin damage report first, then 'if scope in ("base", "malformed"): excluded.add(corpus_id); excluded_scope[...] = scope; continue', and only after that appends the construction damage report's findings and the 'corpus-damaged' construction:<n> finding. Construction never reads the base pin (corpus.py ReadView construction), and open_world_view calls _require_base_pin only after ReadView.opened_at succeeds (world/view.py). So a corpus that both fails construction and pins a non-shipped base is classified construction-damaged, not base-pin, and its findings carry profile-mismatch (base) but neither the construction failures nor corpus-damaged. Found at cut 44's final re-review; pre-existing.

Ruling (scope 2026-10-09): report the construction damage report's findings and its corpus-damaged finding before the exclusion's continue, and keep the exclusion at scope base. Reclassifying it as base-pin damage is rejected: that finding says no record was read, which is false once construction has read records.

Done when: a test reproduces it with test_world_audit.py's _cross_world (damage(BETA, 'parse-error'), rewrite BETA's manifest science pin to science:+'0'*64, audit_world) and asserts audit.corpora[BETA] carries the construction findings, corpus-damaged and excluded:base; test_j19_an_excluded_holder_is_unresolved still sees excluded:base; test_arm_staleness stays at zero stale.

Where: audit.py audit_world's per-corpus loop; test_world_audit.py; brief docs/notes/2026-10-09-mount-citations-follow-ups-brief.md.

## Notes

- 2026-10-09T11:14:08Z (main): scope: scoped; ruled report-before-exclusion over base-pin reclassification, set todo P2 s/mid/direct under goal beliefs-7e341d; brief: docs/notes/2026-10-09-mount-citations-follow-ups-brief.md
