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

5. **R5 — the store path grammar is an atoms-free mirror with an engine
   agreement pin.** `science.holdings.records` mirrors the engine's pure
   relative-path grammar because the capability boundary forbids an atoms
   import below `science/root.py`; `test_the_path_grammar_agrees_with_the_engine`
   pins the mirror to `atoms.core.paths.require_rel_path` across accepted and
   refused spellings.

6. **R6 — Task 1 review pins preceded one review fix.** The exact-facet and
   direct-constructor refusal tests passed on their first run against the
   initial Task 1 implementation; they pin that existing contract. The three
   lone-surrogate construction cases were watched red and drove the shared
   identity-text validation.

7. **R7 — Task 2's epoch exclusion is a contract pin.** The declared
   no-epoch-membership test passed in Task 2's focused red run, pinning the
   existing epoch inventory rather than claiming a new behavior.

8. **R8 — the shared submit keeps cut 9's live mutation site.** Moving the
   executor's exception ladder directly to module scope made the frozen L2u1/V11
   sabotage stale by indentation. `_mapped_submit` therefore holds one nested,
   live `submit` function: every durable executor and holdings store transaction
   still crosses the one mapping and the one `run_transaction` call, while cut
   9's behavioral mutation continues to apply exactly once.

9. **R9 — Task 3 review pins preceded no production change.** The create,
   replace, and delete spec contracts; ordered final-state rows; destination
   no-clobber behavior; read-unestablished and raise-through mappings; and the
   three delegated seam callables all passed on their first run. The move spec
   pin alone was red because its test expected caller order for
   `registered_paths`; `build_spec` canonically orders the produced spec as
   destination then source. Correcting that literal turned the pin green;
   production remained unchanged.

## Heads

| Task | Science head |
|---|---|
| 0 | 178ff77 |
| 1 | f7df31d |
| 2 | 5e88932 |
