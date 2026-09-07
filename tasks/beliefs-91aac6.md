---
id: beliefs-91aac6
title: A stored analysis-spec builder and reader
status: done
priority: 2
size: m
owner: feat/verification-publication
created: 2026-09-05T20:00:55Z
updated: 2026-09-07T01:15:35Z
depends: []
tags: [computation, stored, reproduction-finding]
---

Finding from the mm30 reproduction record (docs/designs/2026-09-05-mm30-reproduction.md, §6, step 4): analysis-spec is a stored kind (stored.py's kinds table, semantic domain science.analysis-spec.v1, the r20 check on import) with no kernel builder and no reader; the record was hand-built and stamped through stamp_semantic_identity, and nothing restores a FrozenSpec from it (step 10b's in-process input). Owner: the computation-reproducibility design and stored.py; lands through whichever kernel lane next rewrites stored.py's facet contract (domain) or verify/evaluation (write-path), never from the reproduction lane. Deliverable: stored.analysis_spec_node(FrozenSpec) and a reader that restores the frozen members and identity.

## Notes

- 2026-09-07T01:15:35Z (feat/verification-publication): stored.analysis_spec_node / analysis_spec_value over canonical projection text; spec.restore recomputes the identity and coerces nothing; the preflight, the r20 check and audit_corpus restore every spec; stored_specs returns specs and findings
