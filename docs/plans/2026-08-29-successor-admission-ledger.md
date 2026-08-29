# Successor-admission slice — execution ledger

Plan: `docs/superpowers/plans/2026-08-29-successor-admission.md`
Specification: `docs/superpowers/specs/2026-08-29-successor-admission-design.md`
Frozen cut: `docs/designs/2026-08-29-conformance-cut-12.md`
Freeze hash: (recorded in the commit after the freeze)

Rulings are written at task boundaries, never rewritten after the fact.

## Rulings

1. **R1 — the certified engine is standing authority.** Atoms remote
   `main` `038513f` is the binding engine contract (cut 12 §2: no atoms
   change ships with this slice); no task edits atoms.
2. **R2 — the core's anchor line is frozen text.** `admit_successor`'s first body line is byte-identical before and after Task 3, so cut 3's three G4 sabotages keep matching exactly once.
3. **R3 — two cut-11 anchors move in whitespace only.** Task 5's factoring re-indents `if payload is None:` / `pointer_unresolved` and `except RecordUndecodable:` / `pointer_unresolved` by the loop's new depth; replacement text and checks are untouched; Task 7 pins `n2_arms_cut11.py` at that commit.
