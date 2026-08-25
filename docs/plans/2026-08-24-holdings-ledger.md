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

10. **R10 — recheck reads before binding when it cannot establish a path.**
    An intent is always appended first. `store_genesis` is a coherent-chain
    read and therefore refuses metadata-less and unserviceable replicas; the
    boundary maps those `read_path` results to inconclusive attempts before
    binding. A `PathObservedView` is bound to the store genesis before it can
    mint an observation.

11. **R11 — holdings intents use canonical JSON.** The payload is compact,
    sorted UTF-8 JSON so the later pure rule can use `json.loads`; `v1.encode`
    is not JSON and cannot support that rule.

12. **R12 — a move names two different intent kinds.** `move-source` and
    `move-destination` carry independently minted event tokens, so each
    observation transaction fulfills exactly its own location intent.

13. **R13 — Task 4's first-green pins are not all red-first.** The three
    original recheck tests were watched red for the missing boundary. The
    recheck mapping and crash-window additions first passed against that core;
    the mutation-act batch was red for missing exports, and the later intent
    validation/lifecycle fixtures were red before their targeted changes.

14. **R14 — Task 4 review closed five test-construction gaps.** L10 u2 now
    performs a real failed restore and asserts its `refuted`, read-only-
    unserviceable result; the `ReadUnestablishedView` mapping has a direct
    verbatim-report pin; H1 u3 substitutes both a wrong-kind and a missing
    final-state row; the move test decodes both intents and pairs their distinct
    tokens, locations, and fulfillments; and every pre-mutation window starts
    with state whose preservation is observable. The H1 u3 test was watched
    fail as two `DID NOT RAISE` cases against a deliberate mint-from-return
    sabotage, then pass when the existing `_final` lookup and absent-state type
    guard were restored. The other review amendments pin already-correct
    production behavior and required no production change.

15. **R15 — Task 4's second review restored the two omitted success pins.**
    H1 u3 again exercises a real successful delete and requires the engine's
    actual `AbsentStateView` final row to publish `Absent()`, alongside the
    retained wrong-kind and missing-row refusals. J9's successful move now
    binds each returned record to its corresponding locator and binds each
    intent-ordered registration to exactly that record's stored path. Both
    amendments passed first against the existing production behavior; mutation
    checks then watched the delete test fail when the valid result was discarded
    and the move test fail when the publication locations were swapped.

16. **R16 — canonical path-state facts stay engine-owned.** The chain views
    continue to carry opaque decoded engine states for replay, with no second
    Science summary and no representation flip. `LogSeam.state_facts` is the
    narrow encoder capability: the composition root alone calls atoms
    `state_to_json`, the default refuses loudly when unwired, and mechanical
    holdings capture only changes the returned ordered tuples into JSON lists.
    Task 7's derivation and validation interfaces forward the same required
    callable.

17. **R17 — Task 5's red/green history is explicit.** The real chain-conversion
    test was red on the missing registered metadata fields; the preflight test
    was red on the missing lock-held coverage core; and the capture batch was
    red on the missing project module. The state-facts boundary pins were red
    on the absent seam and root encoder. After the first capture green, the
    garbage-record construction exposed decode during `_root_state_for` before
    the hold and drove its whole-capture `CorpusStateMalformed` conversion.
    The real-chain test's first run failed because its dataset fixture omitted
    the already-required content identity, then passed with a valid dataset;
    it pin-tested existing production behavior rather than driving it.

18. **R18 — extracted coverage keeps cut 7's live sabotage sites.** The three
    admission/liveness/carrier predicates remain inside one nested, live
    `resolve` function so the frozen X5/X7 byte mutations still apply exactly
    once after their extraction from `_preflight`. Both preflight and holdings
    capture execute those same predicates through `_locked_resolve_coverage`.

19. **R19 — Task 5 review closed three defects and one stale claim.** The
    frozen cut-8 declaration file is restored byte-for-byte to `55b6de7`;
    `RegisteredEntryView` therefore keeps `None` defaults solely for those
    frozen stand-in constructors, while the production root supplies both
    binding fields and capture refuses a missing one before emitting anything.
    Corpus-open translation is limited to `NodesError`, `UnicodeError`, and
    `OSError`, record translation spans only record opening/enumeration and
    canonicalization, and state-fact plus executor-factory failures propagate
    unchanged. The real-chain schema test now compares every emitted state
    fact pair byte-for-byte with atoms `state_to_json`; empty and reversed
    encoder mutations were each watched fail. Finally, the logmodel and root
    prose now state the one permitted re-encoding precisely: mechanical
    projection delegates it to the composition root's engine-owned codec,
    while replay still interprets nothing. The missing-metadata and two
    exception-propagation tests were watched red before their fixes.

20. **R20 — initial corpus open translates decode failures, not Science
    refusals.** `_root_state_for` is solely the corpus open/decode boundary:
    an existing `ScienceError` (including the executor-factory invariant)
    propagates unchanged, while any other exception arising from that call is
    translated to `CorpusStateMalformed` naming the corpus. The admitted but
    never Science-opened corpus carrying malformed YAML was watched leak
    `yaml.parser.ParserError` before the scoped translation, then pass; the
    executor-factory regression stayed green. Later chain projection and seam
    calls remain outside any broad translation.

21. **R21 — the pure rule imports only JSON through the admitted exec
    namespace.** `qualify.py` is both the directly checkable helper and the
    first exact source in the bundle; its one top-level `import json` supplies
    the reducer source that follows it. The four admission fixtures execute
    those concatenated bytes, pinning import availability without a Science
    import in either rule source.

22. **R22 — qualification is corpus-local while head classification spans
    coverage.** One corpus's intent and registration consult only records
    captured from that same corpus; observations still aggregate across the
    declared coverage for supersession and active-head classification.
    Identical record references imported into multiple corpora contribute one
    head, while the same reference with different content refuses.

23. **R23 — Task 6's red/green history is explicit.** The reducer suite was
    first red on the absent pure helper. Its focused cycles then watched the
    missing-record precedence, fixture admission, corpus-local qualification,
    duplicate-reference collapse, and combined contested/incommensurable
    reasons fail before their production changes. The real boundary + capture
    crash-window tests passed on their first run against the completed reducer;
    they pin the already-green composition rather than having driven it.

24. **R24 — Task 6 review closed one alias and two fixture/walk gaps.** Record
    deduplication now compares the full captured canonical text before handing
    the narrower parsed value to reduction; an `observed_at`-only collision was
    watched return one head before the fix and refuse afterward. Every fixture
    corpus state now has Task 5's bare 64-hex form, and each fixture record is
    exact `to_canonical_json` output from the production holdings builder; an
    ordinary test reconstructs the builder value and compares all bytes. The
    fixture-shape test was watched fail first on the prefixed state. Finally,
    explicit dangling-tail and cross-location predecessor pins passed against
    the existing walk; removing either condition made its test fail, confirming
    both exercise their named branch.

25. **R25 — the receipt returns the reducer's two member sequences.** Task 7's
    illustrative annotation says `tuple[dict, dict, HoldingsReceipt]`, while
    Task 6's admitted rule returns `active` and `blocked` lists and Task 8's
    declared adapter consumes each as a `Sequence[Mapping]`. `derive_holdings`
    therefore returns those two list values directly, not one-key wrapper
    dictionaries. If the annotation rather than the two adjacent interfaces was
    intended as authority, Task 8 would need to unwrap a shape its own signature
    does not accept.

26. **R26 — receipt validation reuses the established lock split.** The exact
    binding resolves through `_locked_resolve_rule_binding` under
    `registry._locked_barrier`; that hold is released before `capture_coverage`
    takes any corpus capture lock and before admitted rule code runs. Validation
    then selects the inclusive prefix ending at each named digest from the
    current validated chain projection and requires the freshly captured corpus
    state to equal the named state. This is the same world-lock/corpus-lock split
    as the existing epoch receipt validator, with no new lock order.

27. **R27 — mapping-form receipts exist only for the malformed verdict.** A
    mapping is inspected against the closed receipt shape before any world or
    corpus read, but even a structurally valid mapping reports `malformed`: only
    the sealed `HoldingsReceipt` constructor establishes a receipt that may
    reach availability and re-reduction. This is the narrow reading of Task 7's
    "accept a Mapping form in validation for exactly this arm."

28. **R28 — Task 7's red/green history is one cohesive batch.** All receipt
    tests were written before `science.holdings.receipt` existed and the first
    focused run failed during collection on that missing module. The first
    implementation made all twelve cases green together; later edits removed a
    tautological test assertion, made state-facts forwarding observable during
    validation, narrowed mapping admission, and changed the moved-state fixture
    to add a valid stored dataset before re-running the same green suite. A
    later active-writer arm was watched escape `BuildContended` before the
    validator classified that one computability refusal as `unresolvable`.
    The production-seam H3 u3 construction passed first against the completed
    prefix logic: it pins the real root conversion and engine chain ordering
    rather than claiming to have driven them.

29. **R29 — H3 u3 crosses the production append and chain seams.** The durable
    arm initializes and admits a real corpus, derives through
    `_log_seam().inspect_registered` and `.state_facts`, appends the unmatched
    holdings intent through `holdings_seam().append_intent`, then revalidates
    the old receipt and derives the new one. It asserts equal corpus-state
    identities beside different chain heads and receipt identities, plus the
    changed unsettled output. The smaller mutable-view arm remains as the
    isolated prefix-selection check.

## Heads

| Task | Science head |
|---|---|
| 0 | 178ff77 |
| 1 | f7df31d |
| 2 | 5e88932 |
| 3 | 8658789 |
| 4 | 86cbe29 |
| 5 | 7003f32 |
| 6 | d6615ca |
