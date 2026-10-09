---
id: beliefs-ea5ec7
title: Let freeze pins hold modulo formatting so frozen modules can be formatted
status: doing
priority: 3
size: m
complexity: high
process: planned
owner: freeze-pins-modulo-format
created: 2026-10-09T15:44:29Z
updated: 2026-10-09T21:04:15Z
started: 2026-10-09T20:39:57Z
depends: [beliefs-a555d6]
tags: [hygiene, conformance]
source: beliefs-a555d6
spec: docs/superpowers/specs/2026-10-09-freeze-pins-modulo-formatting-design.md
---

Why: beliefs-a555d6 excludes from ruff format every Python file a freeze pin names, because a pin's claim is byte-exact. Today that is 52 existing files: 48 commit pins checked with git diff --quiet <commit> HEAD, plus content pins as sha256 of the bytes (tests/frozen_guards.py::holds). Left alone, that exclude is permanent and grows with every freeze. The byte-exact rule exists so "a reader can tell that the record they are citing is the record that was made" (docs/superpowers/specs/2026-09-07-frozen-guard-doctrine-design.md §3). Formatting changes no meaning, so the freeze can hold that guarantee up to formatting, with the original bytes still recoverable from git.

Evidence 2026-10-09: on a scratch copy, ruff format reformats 31 of the 52 pinned Python files that still exist. All 31 pass this equivalence: equal ast.dump with each docstring compared after inspect.cleandoc, and an equal sequence of COMMENT tokens. The 1 missing target (python/tests/n2_arms_cut25.py) is an already-falsified pin and is out of scope. The comparator uses only the stdlib, so a ruff upgrade cannot falsify a pin. String literals, including N2 before/after texts and implicit concatenations, compare by value, so frozen arm declarations keep their meaning.

Done:
- Amend the frozen guard doctrine. A pin holds when the target is byte-identical (unchanged), or when it is equivalent to the pinned original under the comparator above, for .py targets only. Non-Python targets (docs) stay byte-exact. The amendment names the last byte-exact commit, so a cited SHA-256 in a results record can be checked with git show <that commit>:<path>.
- holds() changes to match:
  - A commit pin compares git show <commit>:<path> with the working file.
  - A content pin resolves its sha256 to the original bytes by scanning the target path's history for a matching blob, then applies the same comparison. Failing to resolve it is a broken pin, never a pass.
- No FROZEN_* table, cited guard or declaration is edited (doctrine §3).
- Remove beliefs-a555d6's format exclude and its pin-derived test, and format the 31 files in one commit added to .git-blame-ignore-revs.

Verification:
- Unit tests for the comparator: a formatting-only change holds; a changed string literal, a changed comment and a changed statement each break the pin; an unresolvable content pin breaks.
- broken_pins over every guard is unchanged before and after the format commit; the already-falsified pins stay falsified.
- ruff format --check passes with no exclude, and just gate is green.

## Notes

- 2026-10-09T20:39:57Z (main): started
  provenance: {"harness_session":"claude-code:a233969f-f70d-44bc-b4af-5c85f11ac5bd","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-09T20:40:04Z (freeze-pins-modulo-format): resumed
  provenance: {"harness_session":"claude-code:a233969f-f70d-44bc-b4af-5c85f11ac5bd","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-09T20:40:13Z (freeze-pins-modulo-format): claimed by claude-code/claude-opus-5-5, worktree .worktrees/freeze-pins-modulo-format; trial: not enrolled
- 2026-10-09T20:45:15Z (freeze-pins-modulo-format): spec drafted: 34 files reformat (31 table-pinned + 3), all equivalent; live guards (37) re-check pins byte-exact at discharge and 21 live pins assert absence of n2_arms_cut25.py — both outside the original done-list, now in scope
- 2026-10-09T20:45:53Z (freeze-pins-modulo-format): parked (waiting on user, review): user reviews docs/superpowers/specs/2026-10-09-freeze-pins-modulo-formatting-design.md (commit 00d625a in .worktrees/freeze-pins-modulo-format); on approval, agent writes the implementation plan
  provenance: {"harness_session":"claude-code:a233969f-f70d-44bc-b4af-5c85f11ac5bd","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-09T21:02:19Z (freeze-pins-modulo-format): resumed
  provenance: {"harness_session":"claude-code:a233969f-f70d-44bc-b4af-5c85f11ac5bd","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-09T21:02:19Z (freeze-pins-modulo-format): review: spec round 1 — verdict: revise; findings: must-fix 1, should-fix 2; reviewer: unverified (pasted by user)
- 2026-10-09T21:03:16Z (freeze-pins-modulo-format): spec round 1 revisions: comparator reads bytes under PEP 263, requires equal detected encoding, anchors each comment to its statement and directive comments to an unchanged physical line (prototype: 34/34 still equivalent, 4 negatives break); content cache keyed by repo root; four-commit order keeps pre-commit format check green
- 2026-10-09T21:04:15Z (freeze-pins-modulo-format): parked (waiting on user, review): user reviews round-2 spec docs/superpowers/specs/2026-10-09-freeze-pins-modulo-formatting-design.md (commit 89c9cf9 in .worktrees/freeze-pins-modulo-format); on approval, agent writes the implementation plan
  provenance: {"harness_session":"claude-code:a233969f-f70d-44bc-b4af-5c85f11ac5bd","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
