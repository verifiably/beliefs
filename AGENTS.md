# Repository guidance

## Authority

- Treat `docs/designs/2026-08-03-redesign-adoption-ledger.md` as the authority for what is built or open, `docs/plans/2026-08-29-implementation-roadmap.md` as the authority for delivery order, the guide as navigation, and the banked designs as the source of guarantees.
- Verify status and checklist claims against code, tests, history, branches, and worktrees. Unchecked historical plan boxes are not evidence that work remains.
- Preserve frozen conformance-cut bodies and historical evidence. Correct stale current-facing claims in the same change that makes them stale.

## Repository gates

- From the repository root, run `just check` (ruff, pyright, biome, tsc, `tasks check`) and `just test` (parallel Python tests outside N2, standalone N2, then the TypeScript suite). `just gate` runs both. These recipes run through the vendored timing wrapper `tools/tt`, so every run is recorded (ops `docs/specs/2026-09-04-test-ci-audit-design.md`).
- The Python test phases, should you need them individually from `python/`, are `host-budget run -- uv run --frozen pytest -n auto --dist=worksteal --ignore=tests/test_n2.py` and `host-budget run -- uv run --frozen pytest tests/test_n2.py`. Both must pass for a full verdict. N2 refuses to run without the `OPS_WORKERS` that `host-budget run` sets; set `OPS_WORKERS=<n>` where it is absent, as CI does. Python checks are `uv run --frozen ruff check .` and `uv run --frozen pyright`; from `ts/`, run `npm test`, `npm run typecheck`, and `npm run check`. `npm ci` is installation, not a gate: `just setup` runs it after `git worktree add` and after a dependency change.
- Tests: `just test-fast` while working; the pre-push hook runs `just gate`. Run `just test` yourself only if hooks are not installed. Never run the full suite after every edit: the historical serial gate took about 18 min, and the baseline week (beliefs-f253a1) found hand-run full suites costing 2.4x the pre-push hook itself. On the certified 16-worker host, the 2026-09-26 fast-loop median was 87.17 s across three runs, and two complete gates took 235.75 and 237.47 s (beliefs-9b248a).
- The git hooks in `.githooks/` run `just hook-pre-commit` (about 20 s) at pre-commit and `just hook-pre-push` (the complete two-phase gate) at pre-push. A commit that stages nothing under `python/` or `ts/` runs `just hook-pre-commit-docs` instead (ops-check and `tasks check`, well under a second), because the language checks read only those trees. On a fresh clone run `git config core.hooksPath .githooks` once. `just check` has passed on `main` since 2026-09-07; it was red until beliefs-97eb6d and beliefs-0e0c9c.
- Remote CI: `.github/workflows/ci.yml` runs `just ci-python` (Python 3.11 and 3.13) and `just ci-typescript` (Node 20 and 24) on pushes to `main` and on pull requests. It runs the recipes rather than `just gate` because the `tasks` binary is not on a runner. It costs nothing: verifiably/beliefs is public, and standard GitHub-hosted runners are free in public repositories on every plan, drawing on no private-repo minute allowance. Larger, GPU and macOS runners are billed even on public repos, so CI stays on standard Linux.
- `CapabilityUnavailable` is a fail-closed result, not a waiver. Run the Python suite on the certified kernel and volume tuple or report the exact mismatch. Concretely: on the certified tuple the suite runs closed and that exception is a failure. CI sets `VERIFIABLY_UNCERTIFIED_HOST=1`, which converts *only* that exception into a skip naming the missing capability; every other failure still fails, and only an explicit `1` disarms anything. A green CI is therefore evidence about the portable tests and never about the capability-dependent ones — those are proven only by a run on the certified tuple, which the pre-push gate does.

## Tasks workflow

- Run `tasks prime` at the start of a work session and `tasks ready` before choosing work.
- Run `tasks start ID` before implementation, add concise notes as evidence changes, and close the task with a one-line result in the same commit as the work.
- Never edit `tasks/*.md` directly; use the `tasks` CLI for every task mutation.

- A `doing` task is a live claim. Run `tasks prime` inside the worktree you are about to touch, not the main checkout; treat every `doing` task whose `updated` is recent as owned by a running agent and confirm with the user before starting or resuming it.
- `tasks start` records the branch as owner. Add a note naming the agent and process (`tasks note ID "claimed by <agent>, pid <n>"`) so the next session can tell a live claim from a stale one.
- Before completion, run `tasks check`. Require zero errors and report every warning. Registration-only `unreachable_dep` and `cycle_unverifiable` warnings are environmental on machines without all referenced projects; resolve every other warning.

## Design documents

- Design specs live in `docs/superpowers/specs/` and implementation plans in `docs/superpowers/plans/`, and both are committed: every frozen conformance-cut document cites its slice's design by that path, and the results record cites the plan. A slice's spec and plan enter the tree with the lane's first commit.

## Cut plans

Every conformance-cut plan's Global Constraints carry the two tested obligations
below verbatim, beside the lane's own. Cuts 34 and 35 both omitted them and paid
in fix rounds after the final review (cut-34 results §7; cut-35 results §3.2 and
`docs/plans/2026-09-20-url-retrieval-execution-ledger.md`, Task 4 reopened).

- **`root.py` is the one `atoms` importer** (`test_capability_boundary.py`,
  `TestTheCompositionRootIsTheOneAtomsImporter`). A classification over engine
  cause types, a predicate over engine exceptions, or any other engine-typed
  behaviour lives in `root.py` and reaches its boundary through a seam callable
  (cut 35's `StoreActSeam.store_refusal`, `b065711`), never as an import in the
  boundary module. Every new caller of a write primitive joins
  `WRITE_ENTRY_POINTS` in `test_permit_boundary.py` and gains a `Case` in
  `test_permit_entry_points.py`'s `CASES`; the inventory is closed in both
  directions.
- **Every discharged cut adds its row to `test_recent_cut_acceptance.py`**: the
  runner import, its `(runner, cut, accounting)` parametrization entry with the
  declared-arm, declaration-unit and guarantee-row counts, and the cut's
  guarantee-rows-exercised line. Cuts 33, 34 and 35 landed theirs at `f4c2cef`,
  `c77b2aa` and after cut 35's final review; the plan's runner task owns the row.
