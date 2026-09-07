# Repository guidance

## Authority

- Treat `docs/designs/2026-08-03-redesign-adoption-ledger.md` as the authority for what is built or open, `docs/plans/2026-08-29-implementation-roadmap.md` as the authority for delivery order, the guide as navigation, and the banked designs as the source of guarantees.
- Verify status and checklist claims against code, tests, history, branches, and worktrees. Unchecked historical plan boxes are not evidence that work remains.
- Preserve frozen conformance-cut bodies and historical evidence. Correct stale current-facing claims in the same change that makes them stale.

## Repository gates

- From the repository root, run `just check` (ruff, pyright, biome, tsc, `tasks check`) and `just test` (the serial pytest gate and the TypeScript suite). `just gate` runs both. These recipes run exactly the commands below, through the vendored timing wrapper `tools/tt`, so every run is recorded (ops `docs/specs/2026-09-04-test-ci-audit-design.md`).
- The commands the recipes run, should you need one on its own: from `python/`, `uv run --frozen pytest`, `uv run --frozen ruff check .`, and `uv run --frozen pyright`; from `ts/`, `npm test`, `npm run typecheck`, and `npm run check`. `npm ci` is installation, not a gate, and is not in the recipes.
- The git hooks in `.githooks/` run `just hook-pre-commit` (about 18 s) at pre-commit and `just hook-pre-push` (the full suite, about 18 min) at pre-push. On a fresh clone run `git config core.hooksPath .githooks` once. `just check` has passed on `main` since 2026-09-07; it was red until beliefs-97eb6d and beliefs-0e0c9c.
- Remote CI: `.github/workflows/ci.yml` runs `just ci-python` (Python 3.11 and 3.13) and `just ci-typescript` (Node 20 and 24) on pushes to `main` and on pull requests. It runs the recipes rather than `just gate` because the `tasks` binary is not on a runner. It costs nothing: `verifiably/beliefs` is public, and standard GitHub-hosted runners are free in public repositories on every plan, drawing on no private-repo minute allowance. Larger, GPU and macOS runners are billed even on public repos, so CI stays on standard Linux.
- `CapabilityUnavailable` is a fail-closed result, not a waiver. Run the Python suite on the certified kernel and volume tuple or report the exact mismatch.

## Tasks workflow

- Run `tasks prime` at the start of a work session and `tasks ready` before choosing work.
- Run `tasks start ID` before implementation, add concise notes as evidence changes, and close the task with a one-line result in the same commit as the work.
- Never edit `tasks/*.md` directly; use the `tasks` CLI for every task mutation.
- A `doing` task is a live claim. Run `tasks prime` inside the worktree you are about to touch, not the main checkout; treat every `doing` task whose `updated` is recent as owned by a running agent and confirm with the user before starting or resuming it.
- `tasks start` records the branch as owner. Add a note naming the agent and process (`tasks note ID "claimed by <agent>, pid <n>"`) so the next session can tell a live claim from a stale one.
- Before completion, run `tasks check`. Require zero errors and report every warning. Registration-only `unreachable_dep` and `cycle_unverifiable` warnings are environmental on machines without all referenced projects; resolve every other warning.
