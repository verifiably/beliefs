---
id: beliefs-4a2998
title: "Open one citation scope per import bundle, not per record"
status: todo
priority: 3
size: s
complexity: mid
process: direct
created: 2026-10-01T18:25:11Z
updated: 2026-10-09T11:14:11Z
depends: []
parent: beliefs-7e341d
tags: [performance]
agent: claude-code/claude-opus-5-5
---

Why: CorpusWriter._validate_import_bundle (python/src/beliefs/corpus.py) calls self._refuse(record, document_validated=True, view=union, ...) once per bundle member, and _refuse opens its own citation scope (_citing) each time. In a session with read mounts, each scope opens every read mount's ReadView inside its capture hold and indexes it whole, so an import of N records with M read mounts re-indexes N x M times and takes and releases each mount's capture N times. From cut 44's final whole-branch review (mount-citations).

Approach: wrap the bundle's refusal loop in one self._citing() scope so the mounts open once per bundle (the outermost scope wins; _citing already nests). Keep cut 32's pinned self._refuse(record, ...) call sites byte-exact.

Done when: a test with a multi-record bundle under read mounts shows each mount opened once (e.g. by counting ReadView.opened_at calls), the existing import refusals under mounts (J16's reverse-direction and imported-assessment cases) still pass, and test_arm_staleness stays at zero stale.

Where: corpus.py _validate_import_bundle and _citing; test_mount_citations.py; brief docs/notes/2026-10-09-mount-citations-follow-ups-brief.md.

## Notes

- 2026-10-09T11:14:09Z (main): scope: scoped; confirmed the per-member scope at corpus.py _validate_import_bundle, set todo P3 s/mid/direct under goal beliefs-7e341d; brief: docs/notes/2026-10-09-mount-citations-follow-ups-brief.md
