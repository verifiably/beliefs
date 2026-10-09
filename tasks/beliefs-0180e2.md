---
id: beliefs-0180e2
title: "Pin comparator follow-ups: memoize equivalent, directive search, edge tests"
status: todo
priority: 3
size: s
complexity: low
process: direct
created: 2026-10-09T23:10:48Z
updated: 2026-10-09T23:10:48Z
depends: []
tags: [hygiene, conformance]
agent: claude-code/claude-opus-5-5
---

Deferred minors from beliefs-ea5ec7's task and final reviews (docs/superpowers/plans/2026-10-09-freeze-pins-modulo-formatting.md, Execution amendments).

Done:
- Memoize pin_equivalence.equivalent on (sha256(original), sha256(current), path is .py): the all-live-pins check repeats 36 distinct comparisons 687 times (12.9 s vs 4.3 s for the old git diff loop under load 12). Key on the current bytes so a later edit is never masked.
- _DIRECTIVE.match -> .search, so '# long  # noqa: E501' counts as a directive; add a test.
- Tests: else/finally anchor part outside if/else (try/finally, for/while-else, a comment crossing a conditional expression's else); the decorator gap asserted as holding; a whitespace-only change to a non-docstring triple-quoted string breaks; re-indented class/function docstrings hold; the line 1-2 header clause in isolation (encoding unchanged); declaration_digest/declaration_commit raise ValueError on two matching constants.
- Document that _original_with_digest caches a miss; decide whether RecursionError should return False.
- Spec §3 / doctrine §8: the decorator gap is anywhere among the decorators above the def line (FunctionDef.lineno is the def line), not only 'between a decorator and its def'.
- test_every_declaration_pin_in_a_live_guard_holds docstring: drop the 'ten of these files' count.
- beliefs-bd85d0 cites n2_arms_cut38.py:256; note that the line is read at 3ae5a96 (doctrine §8).
