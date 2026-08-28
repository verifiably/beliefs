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
5. **R5 — durable Task 3 tests use the certified-volume fixture.** The
   plan's literal `tmp_path` examples would place engine-backed writes on
   the scratch volume. The implemented tests use `certified_work`, as the
   plan's own global durable-arm rule requires.
6. **R6 — cut 8 is historical, not a current-tree gate.** The plan's
   instruction to keep cut 8 exit 0 contradicted root-lifecycle ledger R15:
   that slice deliberately deleted the store refusal cut 8 certified and
   made cut 9 the successor certification. Cut 8 therefore remains cited by
   its frozen results record; current-tree tasks run cuts 9 onward. The plan
   was corrected at this boundary rather than weakening or rewriting a
   historical cut.
7. **R7 — value-width run tests cross an explicit test port.** The
   production entrypoints and the `fixtures_cut3` run/replay helpers all keep
   the required port. Existing value-only tests bind those helpers through
   three small wrappers over one no-I/O `MemoryPort`; no default or portless
   production path was added.
8. **R8 — every signature-anchored cut-3 arm moves with the port.** Besides
   the planned T2 replay rebase, the required parameter made R17's assessment
   and production signature mutations and R21's supplied-manifest mutation
   stale. Each was rebased onto the widened signature with its original check
   unchanged; the cut-1–3 audit then passed all 37 checks.
9. **R9 — an unpublishable refusal fails at the publication boundary.** A
   pre-intent report with an unencodable identity field previously existed
   only in memory for a stored-codec test. With terminal publication required,
   the same construction raises `MalformedRecord` before returning; the test
   now pins that fail-early behavior.
10. **R10 — the holdings interior moved without a semantic rewrite.** The
    maintained `science.intents.holdings` bytes were copied exactly from the
    prior rule body, and the generated file is only the two-line provenance
    header plus those bytes. The changed implementation identity therefore
    names the generated artifact rather than a hand-authored behavioral
    change.
11. **R11 — holdings parsing stays owned by its dialect.** The gate uses a
    tolerant JSON sniff only to select the domain-bearing branch, then calls
    the shared holdings decoder. Canonical v1 decoding governs the two
    domainless shapes. This preserves official holdings payloads containing
    escaped non-ASCII text without creating a second holdings schema.
12. **R12 — record capture is descriptor-bound on the certified Linux
    tuple.** Namespace descent opens each component relative to its parent
    with `O_DIRECTORY | O_NOFOLLOW`; leaves are classified through
    `O_PATH | O_NOFOLLOW` and reopened only through their held descriptor.
    Non-regular, failed, and over-ceiling leaves are withheld whole.
13. **R13 — act-report validation is one stored-record authority.** The
    writer's exact facet, entry-outcome, relation, and identity checks moved
    intact to `stored.act_report_facet`; the writer maps its
    `MalformedRecord` to `ValidationRefused`, while qualification maps the
    same refusal to `RecordUndecodable`. Identity encoding failures are also
    normalized at that shared boundary.
14. **R14 — qualification has one precedence implementation.** The reducer
    returns immediately on a match, otherwise suppresses every qualification
    finding when any pointer is unresolved, and emits the attempt plus
    per-registration reasons only after all pointers resolve non-qualifying.
    Final-state facts, never captured bytes alone, decide whether a pointer
    published a record.
15. **R15 — verifier-shape cut-9 sabotages move with the verifier lift.**
    Task 10 replaces the report constructor and widens restore's captured
    input tuple, making cut 9's L10u12 and V7 source strings stale while
    leaving both guarantees unchanged. Their sabotages are rebased onto the
    new constructor and assembly shape with their original checks unchanged.
    Cut 10's predecessor guard pins the rebased file by exact SHA-256 content,
    while the live cut-9 mutation audit proves the successor sabotages remain
    sound.
16. **R16 — qualification loads after world-package initialization.** A
    top-level verifier import of the reducer closes a cycle when callers
    import `science.intents.reduce` first: the reducer names the world log
    model while the world package re-exports anchors, which import the
    verifier. The report's qualification type is therefore type-checking-only
    and `evaluate_log` loads the reducer after it has established a
    well-formed view; there is still one reducer implementation and no
    fallback path.
17. **R17 — completion is a projection of the shared shape predicates.**
    `CLOSED`, `INDETERMINATE`, and `UNFINISHED` remain the exported reading,
    but report/run evidence now passes through `science.intents.shapes` like
    verifier qualification. The import stays local because the intent layer
    already names report values; this is cycle placement, not a second
    predicate implementation.
18. **R18 — cut 3's T3 sabotages move with completion.** Replacing the
    report-specific predicate made cut 3's matching and non-qualifying source
    strings stale. Both arms now sabotage the shared `shapes.mismatch` decision
    with their original checks unchanged. `n2_arms_cut3.py` was already a
    successor-rebased declaration under R8 and is deliberately absent from
    cut 11's frozen prior-file pins.
19. **R19 — the agreement matrix is a first-run-green lock.** Task 12 adds
    no behavior: it composes the regenerated holdings rule, verifier reducer,
    and completion projection already landed by Tasks 5–11. All fifteen rows
    passed on first execution, so the matrix records agreement rather than
    repairing a divergence.
20. **R20 — holdings agreement is asserted at the rule's exported width.**
    The regenerated rule deliberately projects both unresolved and unmatched
    intents to the same blocked row with reason `unsettled`; no hidden status
    is available to assert. The matrix therefore pins each case's complete
    exported `active`/`blocked` value (including heads) while the verifier side
    separately pins the finer qualification status.
21. **R21 — cut 11 pins the rebased cut-9 declarations.** Task 10 necessarily
    changed `n2_arms_cut9.py` under R15, so cut 11's predecessor guard reads
    that file at Task 10 head `c7817ba`, not at its pre-lift freeze commit.
    The exact-content pin in cut 10 and the live cut-9 mutation audit both
    passed before cut 11's own arms ran.
22. **R22 — the cut-11 acceptance chain is green on the certified volume.**
    The unchanged prefix reported `39 passed`, `23 passed`, `42 passed`,
    `23 passed`, and `36 passed`; cut 11 then reported `18 passed` for its
    durable arms and `17 passed` for its N2 harness. The runner printed 32
    declared lettered arms normalizing to the 26 frozen units.
23. **R23 — Task 13 declarations follow the landed source anchors.** The
    prescribed plan strings for L7u2d/L7u12, L7u11, J1, J2, and J11 retained
    comments or widths absent from the landed implementation; J12a names the
    landed `evidence` local. Their mutations were narrowed to the exact
    implemented branch each frozen claim describes. No predicate or expected
    verdict changed, and the structural audit requires each adjusted source
    string to match exactly once.
24. **R24 — declaration units do not cap their sub-arms.** Independent review
    found that the first Task 13 table normalized 32 lettered arms to all 26
    unit names while omitting label 7's two explicit error arms and label 8's
    named codec arms. The table now declares 44 lettered arms while preserving
    the frozen 26-unit partition: both terminal boundaries, both error classes,
    incomplete projection, Decimal injectivity, both wrong-shape directions,
    relation projection, v1 inverse behavior, and run-facet agreement each
    have a source mutation and exact check.
25. **R25 — the expanded cut-11 acceptance chain supersedes R22's run.** The
    unchanged prefix again reported `39 passed`, `23 passed`, `42 passed`,
    `23 passed`, and `36 passed`; cut 11 again reported `18 passed` for its
    durable arms and `17 passed` for its N2 harness. The corrected runner
    printed 44 declared lettered arms normalizing to the 26 frozen units.
26. **R26 — parametrized matrices are armed at their full function width.**
    The N2 harness defines a parametrized test function as one check whose
    parameters are its data. J12 therefore names the complete eight-row run
    agreement function and seven-row holdings function, not one selected node;
    every row executes under each sabotage. J5 separately arms rollback, and
    J6 separately arms total order, both malformed carriage exits, and retired
    field absence. The declaration table is 49 lettered arms over 26 units.
27. **R27 — caller capture and report exactness are independently armed.**
    Audit/restore's shared assembly and arrival's separate assembly each have a
    held-capture omission sabotage; cut 11 observes the shared branch through
    audit while cut 9 retains ownership of restore's held-boundary check. The
    evaluator's required typed input is separate. Gate outcomes cover foreign,
    domainless, malformed, undecodable, and the real Unicode holdings writer.
    Report rows separately pin shape and `fulfilled_by` absence for every
    nonmatched status. The resulting table is 61 lettered arms over the same 26
    frozen units, with no prior check rehomed.
28. **R28 — captured content and every finding severity are observable.** The
    capture itself is armed for complete sorted output, the shared assembly is
    armed for forwarding that exact value, and intermediate namespace descent
    has its own no-follow mutation. The two reduction findings each assert and
    arm warning severity. The complete table is 66 lettered arms over 26 units.
29. **R29 — the definitive cut-11 acceptance chain is green.** After the
    exhaustive review reported no findings, the unchanged prefix reported
    `39 passed`, `23 passed`, `42 passed`, `23 passed`, and `36 passed`; cut 11
    reported `18 passed` for its durable arms and `17 passed` for its N2
    harness. The runner printed 66 declared lettered arms normalizing to the 26
    frozen units.

## Heads

| Task | Science head |
|---|---|
| 0 | 76e76d8 |
| 1 | fac2c80 |
| 2 | 1d25baf |
| 3 | e05c60c |
| 4 | 4b7e1df |
| 5 | 6ed0c8f |
| 6 | e7338a3 |
| 7 | 2a8ed87 |
| 8 | 3d267e0 |
| 9 | aefcbb0 |
| 10 | c7817ba |
| 11 | 3c77a5b |
| 12 | 8472939 |

(Appended at every task boundary.)
