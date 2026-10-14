---
id: beliefs-a1a767
title: "The contract names stored.source_assertion_value, which does not exist"
status: idea
priority: 2
created: 2026-09-11T11:42:27Z
updated: 2026-10-14T01:35:21Z
depends: []
parent: beliefs-9396cf
tags: [contract]
---

contracts/science/CONTRACT.yaml declares source-assertion's reader as stored.source_assertion_value; no such function is defined in stored.py and no source-assertion builder exists, so the kind cannot be minted through a builder or read through its declared reader. Found 2026-09-10 while looking for a source referrer in slice 2b.
