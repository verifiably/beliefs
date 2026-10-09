---
id: beliefs-97fa19
title: A portable test that live guards check .py pins only through the frozen_guards predicates
status: todo
priority: 3
size: xs
complexity: low
process: direct
created: 2026-10-09T23:29:51Z
updated: 2026-10-09T23:29:51Z
depends: []
tags: [conformance, testing]
agent: claude-code/claude-opus-5-5
---

beliefs-ea5ec7 rewrote the 37 live guards' pin checks to call frozen_guards.commit_pin_holds / content_pin_holds, but nothing keeps a new guard from reintroducing a byte-exact check (git diff --quiet <pin> HEAD, or sha256 equality over a .py target). Such a guard passes today and turns red only at the next reformat (a ruff upgrade), at its next discharge.

Done:
- A test in python/tests/test_frozen_guards.py that walks every live guard's AST and fails on a subprocess call whose argv holds "diff" and "--quiet", and on a sha256(...).hexdigest() comparison whose target is not a design-doc body. Cut 7's assert_cut5_matcher_migration (two historical commits) and the CUTN_FROZEN_SHA256 doc checks stay allowed, named explicitly.
- RED on a scratch guard that uses git diff --quiet; GREEN over the 39 live guards.
