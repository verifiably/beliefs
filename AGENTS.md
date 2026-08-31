# Repository guidance

## Authority

- Treat `docs/designs/2026-08-03-redesign-adoption-ledger.md` as the authority for what is built or open, `docs/plans/2026-08-29-implementation-roadmap.md` as the authority for delivery order, the guide as navigation, and the banked designs as the source of guarantees.
- Verify status and checklist claims against code, tests, history, branches, and worktrees. Unchecked historical plan boxes are not evidence that work remains.
- Preserve frozen conformance-cut bodies and historical evidence. Correct stale current-facing claims in the same change that makes them stale.

## Repository gates

- From `python/`, run `uv run --frozen pytest`, `uv run --frozen ruff check .`, and `uv run --frozen pyright`.
- From `ts/`, run `npm ci`, `npm test`, `npm run typecheck`, and `npm run check`.
- `CapabilityUnavailable` is a fail-closed result, not a waiver. Run the Python suite on the certified kernel and volume tuple or report the exact mismatch.

## Tasks workflow

- Run `tasks prime` at the start of a work session and `tasks ready` before choosing work.
- Run `tasks start ID` before implementation, add concise notes as evidence changes, and close the task with a one-line result in the same commit as the work.
- Never edit `tasks/*.md` directly; use the `tasks` CLI for every task mutation.
- Before completion, run `tasks check`. Require zero errors and report every warning. Registration-only `unreachable_dep` and `cycle_unverifiable` warnings are environmental on machines without all referenced projects; resolve every other warning.
