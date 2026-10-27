# Owned-replica publication review ledger

Task: beliefs-7c612b. Controller-owned record; reviewers remain read-only.

## Spec round 1

Reviewer: codex/gpt-6-astra. Frozen revision: 338c71f.
Verdict: accept; findings: none. Full report: task attachment builder-check-report.md.

## Spec round 2

Reviewer: claude-code/claude-opus-5-5, identity supplied in the relayed review.
Frozen revision: 338c71f, spec SHA-256
8a44f249e42e00aaaea2537b521ee914fbef766e546dcee2724eed32ba3a25f9.
Verdict: revise; findings: Important 1, Minor 5. Full report: spec-round-2-report.md.
The opening prose says four minors; the five enumerated findings and explicit
note instruction establish the recorded count of five.
User disposition: rule on the points, revise the spec, then start the plan.
Revised spec: deb8d99, docs/superpowers/specs/2026-10-27-owned-replica-publication-design.md.

Ruling: I1 accepted and addressed in deb8d99 §1. Why: decision 8's original
adopted-origin, downstream acceptance and registry-provenance reasons needed
answers; the later Own policy, new publication marker and unchanged admission
answer them. Fresh already permits unattributed copied records; this design
does not solve that authenticity limit. Cost: a wrong classification could
misattribute markerless records; the explicit-claim limit and marker guard remain.

Ruling: M1 accepted and addressed in deb8d99 §3. Why: scoped world opening may
perform recovery before ownership validation. Cost: callers must not read the
publication no-effects guarantee as a guarantee about earlier world recovery.

Ruling: M2 accepted and addressed in deb8d99 §3. Why: reuse
publication._HEX32.fullmatch instead of duplicating the ID grammar. Cost:
one existing private constant becomes an intra-package dependency.

Ruling: M3 accepted and addressed in deb8d99 §5. Why: amend the publication
and formal-model current-facing Y17 copies while preserving the frozen cut.
Cost: omitting either current copy leaves contradictory status; both are in Task 1.

Ruling: M4 accepted and addressed in deb8d99 §7. Why: explicitly test a marker
in captured_records but absent from the recorded map and selected tuple.
Cost: a weaker fixture could miss a selection-only scan; Task 2 pins full capture.

Ruling: M5 accepted and addressed in deb8d99 §6. Why: reusing acceptance_inputs
intentionally brings its all-mount reads, duplicate-carrier check and exactly-one
write-mount precondition into preview. Cost: some formerly successful previews
can fail; sci-9a7ce2 owns tests and disclosure, with no silent fallback.

No deferred minor findings from this review.

## Consumer handoff

sci-9a7ce2 implements the two science call sites and depends on beliefs-7c612b.
sci-775e90 depends on both and owns the live rerun; no live changes were made.

## Plan self-review

The controller checked spec coverage, step clarity, types, five review-focus
conditions and proportion. Nine distinct mutation units remain; a redundant
pre-intent unit was folded into an uncounted regression plus forwarding coverage
before the first frozen plan revision. No product code or tests were changed.
The user still reviews the frozen plan before implementation.
