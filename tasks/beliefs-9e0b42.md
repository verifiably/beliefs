---
id: beliefs-9e0b42
title: One-command mm30 recreation that ends in a checked verdict
status: doing
priority: 3
size: m
complexity: mid
process: direct
owner: main
created: 2026-09-10T22:01:42Z
updated: 2026-09-30T09:47:52Z
started: 2026-09-30T09:47:52Z
depends: []
parent: beliefs-cde4d9
tags: [reproduction]
---

Why: The mm30 recreation's step order is written in three plan documents that disagree, and a loop over the steps cannot report truthfully. Five steps (belief, rederive, close, compose's receipt check, read --again) record a defect and exit zero, and rederive needs the cut-22 archive at `<work dir>.cut22`, which a fresh directory lacks (inventory, beliefs-b9c3ea). One command that ends in a checked verdict makes "reproduces unaided" something a run can show.

Done:
1. Prior-archive override. `paths.PRIOR` reads an environment variable (suggested `MM30_CUT22_ARCHIVE`) beside the two `paths.py` already reads, defaulting to today's sibling. A missing archive still raises; nothing stands in for it.
2. Verdict step, `python -m reproduction.verdict`. Read-only over the work directory's `state.json` and `findings.jsonl`. It checks every line of the brief's "The minimal terminal verdict" and exits non-zero naming each failed line. The run-invariant expected values are committed with the driver, copied from the fixture's `state.json`, so the step needs no fixture on disk. Run, assessment, verification and composite identities are compared only with each other. Any findings line of class `defect` or `host` fails, and so does any line outside `closed` beyond the five the brief names.
3. Recipe. One `just` recipe taking the fresh work directory and the predecessor root, with the cut-22 and cut-31 archives defaulting to the fixture's siblings and overridable. It checks both archives exist before step 0, runs the brief's sequence one process per line, stops at the first non-zero exit, runs the verdict last, and fails when the tracked Snakefile differs afterwards (`git diff --quiet` on `python/tools/reproduction/analysis/workflow/Snakefile`). It is not part of any gate. It deletes nothing.
4. Certified-host run. Run the recipe once into a fresh directory under the main checkout's `.work/reproduction/`, from the worktree's canonical path. Append the result to the reproduction record as a new addendum: the verdict's output, the wall time, and the directory's name and size (the fixture's is about 420 MB, nearly all `scratch/`). Whether that directory is kept is the user's call.

A step that refuses, or a verdict line that fails, is a finding. Record it and file it through the lane that owns the surface; do not relax the verdict or work around the step. Two outcomes are not established and this run measures them: that `preflight` passes on this host today, and that a recreation under the current contracts yields the recorded authored identities.

Verification: Focused tests in `python/tests/test_reproduction_driver.py` for the verdict (a passing state; one failing case per verdict group; a `defect` line; an unexpected non-`closed` line; a missing key) and for the override (the variable moves `PRIOR`; a missing archive raises). Run `just test-one tests/test_reproduction_driver.py`, then `just test-fast`. The certified-host run in item 4 is the end-to-end check.

Out of scope: `relocate.py`; retained audit reports (beliefs-b36632, beliefs-9d2b68); promoting the driver to a surface (design §8 item 3 declares the scripts throwaway); editing the historical plan documents whose step orders are stale.

Where to look: `docs/notes/2026-09-29-reproduction-audit-backlog-brief.md`, Recipe inventory (sequence, inputs, exit-code table, verdict lines); `python/tools/reproduction/paths.py`, `rederive.py::prior_state`, `transition.py`, `state.py`, `findings.py`; `docs/superpowers/specs/2026-09-05-mm30-reproduction-design.md` §8, §13, §14; `docs/designs/2026-09-05-mm30-reproduction.md` §16 (canonical path), §17 (predecessor location), §24 (step 13); `justfile`.

## Original capture

The ten-step order (preflight, world, concepts, select_target, analysis_inputs, type_target, hold, spec, run, belief, close, rederive) is spelled out separately in three plan docs and fixed only by each module's docstring; the 2026-09-10 rebuild retyped it as a shell loop. A justfile recipe taking SCIENCE_MM30_ROOT would make 'reproduces unaided' literally one command. The design declares the scripts throwaway, so scope this as a recipe, not a promoted surface.

## Scoping context (2026-09-29)

The current driver also has compose and two fresh-process read calls. world.main refuses an existing work root; rederive requires the preserved cut-22 state; several steps record defects but return zero. A shell loop needs a precise input and terminal-verdict contract before it can promise reproduction. Keep this an idea pending a bounded invocation inventory. Handoff: docs/notes/2026-09-29-reproduction-audit-backlog-brief.md

## Notes

- 2026-09-29T22:59:41Z (main): scope: briefed; current sequence and success verdict need an invocation inventory; research beliefs-b9c3ea; brief: docs/notes/2026-09-29-reproduction-audit-backlog-brief.md
- 2026-09-29T23:16:01Z (research/beliefs-b9c3ea): finding (beliefs-b9c3ea, 2026-09-29): a recipe alone cannot report truthfully. Five steps (belief, rederive, close, compose's receipt check, read --again) record a defect and exit zero, and rederive needs the cut-22 archive at <work dir>.cut22, which a fresh directory lacks. Scope as: a just recipe over the design §13/§14 order with analysis_inputs restored, a read-only verdict step over state.json and findings.jsonl, and an environment override for paths.PRIOR. Body's ten-step order is stale. Inventory: docs/notes/2026-09-29-reproduction-audit-backlog-brief.md, Recipe inventory
- 2026-09-30T00:19:13Z (main): finding (beliefs-0c1cc9, 2026-09-29): step 13 is python -m reproduction.transition --archive <root>. The recipe must pass --archive, because a fresh work directory has no .cut31 sibling. The step compiles the successor profile from the work directory's held lists, so it runs after lists and concepts; in an empty directory it raises from vocabulary._document. It has not run inside a fresh recreation: record §24 used copies of the fixture's held lists. rederive.prior_state still has no override for the cut-22 archive
- 2026-09-30T09:20:25Z (main): scope: scoped; P3/m/mid/direct; rewritten as a cut-22 archive override, a read-only verdict step, a just recipe and one certified-host run; original capture preserved; brief: docs/notes/2026-09-29-reproduction-audit-backlog-brief.md
- 2026-09-30T09:47:52Z (main): started
  provenance: {"harness_session":"claude-code:581b2a04-8931-471b-95f2-248506884c02","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-30T09:47:52Z (main): claimed by claude-code/claude-opus-5-5, pid 3352969
