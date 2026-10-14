---
id: beliefs-a1a767
title: "The contract names stored.source_assertion_value, which does not exist"
status: idea
priority: 2
reviewed: true
created: 2026-09-11T11:42:27Z
updated: 2026-10-14T08:55:40Z
depends: [beliefs-595a53]
parent: beliefs-9396cf
tags: [contract]
---

contracts/science/CONTRACT.yaml declares source-assertion's reader as stored.source_assertion_value; no such function is defined in stored.py and no source-assertion builder exists, so the kind cannot be minted through a builder or read through its declared reader. Found 2026-09-10 while looking for a source referrer in slice 2b.

## Notes

- 2026-10-14T01:35:26Z (main): scope: briefed; stored reader and dedicated builder remain absent, but record.SourceAssertion and G1 value tests exist (d1fd379); reader declarations are descriptive and validate_payload skips reader-shaped facets. File design beliefs-595a53 for the stored projection, anchoring, validation and inertness, dependent on existing endpoint inventory beliefs-9c375c; no generic reader dispatcher or duplicate endpoint research; original body preserved; checked main 31f8ad9; brief: docs/notes/2026-10-13-empirical-evidence-boundaries-brief.md
- 2026-10-14T08:55:40Z (main): 2026-10-14 brief review: its design beliefs-595a53 now waits on beliefs-1d023a as well as beliefs-9c375c and is P3; see the brief's stored source-assertion alternatives.
