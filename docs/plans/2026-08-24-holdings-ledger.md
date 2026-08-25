# Holdings slice — execution ledger

Plan: `docs/superpowers/plans/2026-08-24-holdings.md`
Specification: `docs/superpowers/specs/2026-08-24-world-index-holdings-design.md`
Frozen cut: `docs/designs/2026-08-24-conformance-cut-10.md`
Freeze hash: `2186a71`

Rulings are written at task boundaries, never rewritten after the fact.

## Rulings

1. **R1 — the atoms seam is landed authority.** The atoms design gate
   was approved at atoms `558817b` against Science authority `b231e08`;
   `read_path_state` and `TransactionOutcome.final_states` are
   implemented, reviewed (five findings closed), merged `--no-ff`, and
   pushed — the atoms remote `main` stands at `038513f` with its suite
   at `6234 passed, 7 skipped` on the merged head. That head is Task 3's
   binding engine contract; no Science task edits atoms.

2. **R2 — the compatibility assertion follows the public refusal contract.**
   The fresh baseline exposed the private concrete cause
   `_OutsideVocabulary(PreconditionRefused)` at
   `python/tests/test_world_arrival.py:700`; Science production already
   catches `PreconditionRefused` and preserves `engine_error`. The test
   therefore asserts `isinstance(cause, PreconditionRefused)` rather than
   the private concrete type; production is unchanged.

3. **R3 — Task 5 may modify the omitted epoch module.** Task 5's Files
   list omitted `python/src/science/world/epoch.py`, although its behavior
   and gate require coverage extraction there. Task 5 is authorized to
   modify that file.

4. **R4 — the baseline typing gate is enforceable.** The four intentional
   invalid-input test cases that predated this plan use explicit typing
   escapes or a non-shadowing local, preserving runtime validation while
   making Pyright pass.

## Heads

| Task | Science head |
|---|---|
