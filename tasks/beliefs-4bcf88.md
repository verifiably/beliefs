---
id: beliefs-4bcf88
title: "Composite claims: the kind that places kernel §11's inquiry, patch-definition and structural-chain"
status: done
priority: 2
size: l
complexity: high
process: planned
owner: design/composite-claim
created: 2026-09-13T00:35:00Z
updated: 2026-09-16T20:22:24Z
started: 2026-09-16T10:43:08Z
completed: 2026-09-16T20:22:24Z
depends: []
tags: [design]
spec: docs/designs/2026-09-12-composite-claims-design.md
plan: docs/superpowers/plans/2026-09-12-composite-claims.md
---

The second spec from the 2026-09-12 models assessment. A structure (a causal DAG, the predecessor's h00 working model, inquiry DAGs and patch-definitions) is a set of propositions over a declared node set with derived, never authored, belief. Kernel §11 left inquiry / patch-definition / structural-chain unplaced; this design places them. Off the path; before the contract-cut freeze; after estimand-typing.

## Notes

- 2026-09-13T00:41:23Z (design/composite-claim): parked (waiting on user, review): Spec drafted; review it, then write the implementation plan
- 2026-09-13T01:05:00Z (design/composite-claim): Spec review 1: four findings (negative polarity kept as a sign; reading names every evaluator input; supersedes same_kind on the shared path and under audit; build_composite takes a ResolutionSnapshot and returns a receipt), all taken
- 2026-09-13T01:11:40Z (design/composite-claim): Spec review 2: four findings (reading goes through evaluate_over; identification follows current admission via a traced wrapper; U3 split form vs vocabulary; node receipt on CompositeReading), all taken; same_kind stays declarative
- 2026-09-13T01:26:36Z (design/composite-claim): Spec review 3: two findings (admitted set survives NoBelief arms as reached/not-reached; admission-once asserted by a call trap), both taken
- 2026-09-13T01:56:09Z (design/composite-claim): parked (waiting on user, review): Plan drafted; review it, then Task 0 opens the lane after estimand-typing merges
- 2026-09-13T02:13:20Z (design/composite-claim): Plan review 1: twelve findings (field sets extend the estimand baseline; assesses target-kind guard; step-5 contradiction arm; whole node-set contract and retirement in classify; restoration errors translated; reading refuses not-member; supported shapes enforced; acyclic typed reading fixture; U10 receipt not-consulted for PHF19; traps exercise the reading; YAML mutations and NotReached equality), all taken
- 2026-09-13T02:32:38Z (design/composite-claim): Plan review 2: two findings (unresolved assesses target refuses on the shared path, add and import; U4 test builds a typed assessment, fixture estimand rows moved to Task 2), both taken
- 2026-09-13T02:52:33Z (design/composite-claim): Plan review 3: one finding (same-bundle import rebuilds the bundle after the new assessment's run exists), taken
- 2026-09-13T09:05:03Z (design/composite-claim): Plan cleared 2026-09-13 after three reviews. Execution waits on Task 0: estimand-typing (beliefs-59f846, branch design/estimand-typing) must merge into main first, then rule 6, then the cut number and freeze.
- 2026-09-13T09:05:04Z (design/composite-claim): parked (waiting on agent, dependency): Plan cleared 2026-09-13; execution waits on Task 0's merge, rule-6 and freeze gates
- 2026-09-16T10:43:08Z (design/composite-claim): process: planned — the spec and plan exist and cleared three reviews each on 2026-09-13; a drift re-review against main at 8aa5903 precedes the freeze because the lane branched before the estimand-typing implementation landed
- 2026-09-16T10:43:08Z (design/composite-claim): lane admitted under rule 6 at main 8aa5903: open kernel lanes none (estimand-typing closed at cut 31; world-read, mutation, acquisition all waiting); on-path state: no boundary (roadmap tier 1 'On the path' is empty since cut 30); this is the only open kernel lane
- 2026-09-16T11:13:30Z (design/composite-claim): Pre-freeze drift review 2026-09-16 against main 8aa5903 (two parallel readers, spec and plan): spec 20 findings (one blocking: a kinds:[composite] view predicate is gated by the coordination contract's literal kinds list, so the one amendment adds the kind and the relation) and plan 23 findings (blocking: no docs/designs/README.md; the guard's three prefix regexes and table_words; dataset_node is keyword-only; the shipped biology pack has no succession route, so its edges: row is dropped and spec limitation 18 files it; a new .cut32-acceptance root is a red test; the cut Status line and Remaining boundary are guarded; the parity fixture generator). All taken; recorded in spec §15 and the plan's self-review.
- 2026-09-16T11:17:41Z (design/composite-claim): Cut 32 frozen at ff03b00 (2026-09-16); Task 0 done. Execution begins at Task 1 under subagent-driven-development; the pre-freeze drift review's design-level changes (limitation 18: no biology edges row; check_composite in both audit dispatches; the coordination amendment covers kinds and relations) were taken without a user pass and stand unless overridden
- 2026-09-16T20:22:24Z (design/composite-claim): Conformance cut 32 discharged 2026-09-16 (freeze ff03b00, discharge 44343da, fix round caa4adb): U1-U10 close in full over 26 one-mutation sabotage arms, every arm sound in both directions; gate 4934 passed, 2 skipped and TS 154 passed. The composite kind, its closed grammar, the composes signature, supersedes declared same_kind, the domain edges: table, the boundary, the audit codes and the traced reading are built; kernel §11's first open question closes and §4.4's open row keeps only search. Results record docs/plans/2026-09-16-conformance-cut-32-results.md; composite-claims entered and closed in the ledger and the roadmap in that same commit.
