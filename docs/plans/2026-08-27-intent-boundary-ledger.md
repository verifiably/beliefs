# Intent-boundary slice — execution ledger

Plan: `docs/superpowers/plans/2026-08-27-intent-boundary.md`
Specification: `docs/superpowers/specs/2026-08-26-world-index-intent-boundary-design.md`
Frozen cut: `docs/designs/2026-08-27-conformance-cut-11.md`
Freeze hash: `9711886`

Rulings are written at task boundaries, never rewritten after the fact.

## Rulings

1. **R1 — the certified engine is standing authority.** Atoms remote
   `main` `038513f` is the binding engine contract (cut 11 §2: no atoms
   change ships with this slice); no task edits atoms.
2. **R2 — host recertification is a separate prerequisite.** The Linux
   7.1.9 ext4 tuple was certified and merged into the local Atoms `main`
   at `77a89e2` before this slice began. It changes no engine behavior and
   no Atoms change ships with this Science slice.
3. **R3 — the moving host tuple remains a separate prerequisite.** The host
   advanced to Linux 7.1.10 during Task 2. Its exact ext4 tuple independently
   passed 3,281 crash prefixes with zero violations and was merged into local
   Atoms `main` at `dd658ac`; the Science slice still ships no Atoms change.
4. **R4 — the projection copy must not name a mutation primitive.** Task 2's
   full gate showed that importing the `copy` module collides with the
   capability audit's raw-write vocabulary. Importing `deepcopy` directly
   preserves the projection rebuild and the audit's unspellability claim.

## Heads

| Task | Science head |
|---|---|
| 0 | 76e76d8 |
| 1 | fac2c80 |

(Appended at every task boundary.)
