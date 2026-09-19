---
id: beliefs-b22a0c
title: corpus.py's import call site calls _validated_retraction twice
status: idea
priority: 2
created: 2026-09-19T18:52:24Z
updated: 2026-09-19T18:52:24Z
depends: []
tags: [hygiene, conformance]
---

The import boundary calls _validated_retraction once to validate a retraction record and once more only to read the resolved arm back out, a plan-mandated shape from slice 2's Task 2, not a defect. Cheap cleanup candidate: read the arm from the first call's return instead of calling again.
