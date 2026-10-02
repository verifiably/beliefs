# Conformance cut 45 — belief acceptance

**Status:** discharged 2026-10-02; G10–G13 closed. Frozen before product implementation at `4bec463`; results: `../plans/2026-10-02-conformance-cut-45-results.md`.
**Spec:** `../superpowers/specs/2026-10-02-belief-acceptance-design.md`.
**Plan:** `../superpowers/plans/2026-10-02-belief-acceptance.md`.
Numbered after cut 44 under the roadmap's successor rule.

## 1. What this cut is

A caller-supplied predicate and opaque immutable statement select assessments,
verifications and corrections before effects. Science supplies trust decisions;
Beliefs applies timing and returns reproducible selection. Singleton holders are
milestone 1a only; overlapping publications revisit this contract in beliefs-81367e.

## 2. The boundary

`belief-acceptance` reopens `world-read`: belief.py, evaluation.py, closure.py,
corpus.py and world/view.py. No write primitive, trust registry or new dependency.
Unrestricted projection bytes remain unchanged. Accepted dependencies are unfiltered.

## 3. Selection

| **G10** | Assessment acceptance precedes evidence reads and identity collapse | All-rejected yields `no-eligible-assessment`; excluded facet-disagreeing twin is inert; accepting both still refuses; excluded malformed assessment is not decoded; canonical address and corpus are passed to the predicate |
| **G11** | Verification acceptance precedes lifecycle and supersession | Rejected failure cannot invalidate; rejected pass cannot admit; rejected superseder cannot clear an accepted failure; accepted failure or pass naming a rejected twin's stored address still applies to the accepted identical assessment; rejected-only identities admit nothing; twin edge bookkeeping does not widen correction scope |
| **G12** | Correction acceptance precedes every standing effect | Rejected node and route retractions are inert; rejected counter cannot restore; filtered resolution changes are legitimate; rejected malformed snapshot-fold candidate is never facet-validated; accepted malformed chain refuses; mapped-only local oracle ignores drift-only aliases; split-corpus disagreement still refuses with unrelated exclusions; unchanged chains retain receipt-fidelity checks; filtered snapshot history alone enters the digest |
| **G13** | Policy and selection are reproducible and reported | Complete policy/exclusions on completed selection outcomes, including late consulted-contract refusals and late dependency-absence answers; every incomplete answer has empty exclusions; supplied acceptance context fails before reads; pure incomplete context refuses after the binding guard and before the consulted walk; policy mutation moves filtered digest; unrelated exclusion changes report but not digest; gather and pure-evaluation closures agree |

All checks below are in `test_acceptance.py`; the exact function is
`test_<lowercase-unit-with-underscore>_<suffix>`. Each row declares one arm/unit.

| Unit | Test suffix / decisive assertion | Mutation responsibility |
|---|---|---|
| G10-a | `all_assessments_rejected`: NoBelief/no-eligible-assessment, empty reached set | Bypass assessment selection |
| G10-b | `contradictory_twin`: rejected disagreeing twin inert; both accepted refuse | Bypass assessment selection before collapse |
| G10-c | `malformed_assessment`: rejected malformed facet never decoded | Move assessment decode ahead of selection |
| G10-d | `canonical_holder`: callback receives holding corpus and live address, including alias inputs | Pass a deprecated assessment address |
| G10-e | `manifest_preflight`: missing/malformed manifest raises before iteration/resolution/callback | Skip filtered local manifest preflight |
| G10-f | `accepted_attribution`: rejected holder never joins identity attribution | Attribute a rejected twin |
| G11-a | `rejected_failure`: accepted evidence remains admitted | Bypass verification selection for a failure |
| G11-b | `rejected_pass`: no accepted pass means no admission | Bypass verification selection for a pass |
| G11-c | `rejected_superseder`: rejected later pass cannot clear accepted failure | Include rejected superseding verification |
| G11-d | `failure_names_rejected_twin`: accepted failing edge to rejected twin invalidates accepted identical assessment | Populate verification targets from accepted assessments only |
| G11-e | `pass_names_rejected_twin`: accepted passing edge to rejected twin admits accepted identical assessment | Test verifies membership against visited |
| G11-f | `edge_scope`: rejected-only identity admits nothing; correction of rejected twin stays out of closure | Union verification targets into correction scope |
| G12-a | `node_retraction`: rejected node correction cannot subtract evidence | Bypass ordinary retraction selection |
| G12-b | `route_retraction`: rejected route correction cannot retire lineage | Retire a rejected route target |
| G12-c | `counter_retraction`: rejected counter cannot restore its accepted target | Include rejected counters in facets |
| G12-d | `changed_chain_receipt`: excluded reachable counter permits changed resolution; multi-hop C_c(r) is honored | Require receipt comparison despite excluded transitive counter |
| G12-e | `malformed_snapshot_candidate`: rejected malformed record outside chain cannot poison fold | Validate snapshot facet before selection |
| G12-f | `accepted_snapshot_chain`: accepted malformed chain still raises RetractionUnreadable | Omit accepted chain-member validation |
| G12-g | `mapped_oracle`: post-epoch record/alias does not enter ordinary local oracle | Use full captured resolver for L_c |
| G12-h | `split_with_exclusion`: split-corpus local/world disagreement still refuses with unrelated exclusion | Skip L_c-vs-W comparison |
| G12-i | `unchanged_receipt`: unrelated exclusion cannot hide corrupt surviving receipt | Disable all receipt checks on any exclusion |
| G12-j | `snapshot_root`: rejected post-epoch snapshot root is inert | Use unrestricted snapshot fold |
| G12-k | `snapshot_history`: only surviving filtered chain/history enters closure and trace | Reuse unfiltered cached history |
| G12-l | `accept_all_refusal_parity`: same refusal/absence/admission outcomes as unrestricted | Omit filtered receipt-fidelity check |
| G13-a | `policy_validation`: exact bool, callable, nonempty exact str and v1 encoding; exception propagates | Coerce result with bool instead of rejecting |
| G13-b | `complete_report`: every irrelevant exclusion appears once, sorted | Apply relation matching before predicate |
| G13-c | `early_error`: caught pre-completion error reports empty incomplete exclusions under both scan orders | Expose decisions while incomplete |
| G13-d | `late_error`: caught late consulted error retains completed exclusions and original reason | Reset report in exception handler |
| G13-e | `late_absence`: supplied lineage snapshot not_present yields unavailable-corpus-absent with complete report | Mark every absence incomplete |
| G13-f | `supplied_context`: forged gather context raises before reads even without policy | Remove supplied-acceptance guard |
| G13-g | `pure_incomplete`: pure refusal after binding guard and before consulted walk; wrapper bad-binding refusal carries empty incomplete report before reads | Remove pure incomplete guard |
| G13-h | `closure_statement`: statement changes digest; unrelated exclusion does not; both closure paths agree | Omit acceptance_policy from projection |
| G13-i | `two_policies`: same view, different calls, no decision/snapshot cache leakage | Return unrestricted snapshot cache on filtered call |
| G13-j | `capture_integrity`: damaged/absent coverage cannot be hidden by reject-all | Return rejected-pool answer before coverage checks |

## 4. Accounting

**34 arms, 34 declaration units**, four guarantee rows, G10–G13; recent-cut row
`(34, 34, 4)`. Unit counts are 6, 6, 12, 10. Eight durable acceptance functions
exercise twins, verifications, node/routes, counter/receipt fidelity, snapshot
history, reporting, statement/cache isolation and accept-all refusal parity.

## 5. N2 and acceptance obligations

Each declared mutation bypasses its responsible branch above; source before-text
must occur exactly once and after-text must parse. Normal checks pass; each named
check fails under its own mutation. Frozen canonical declarations remain immutable.
The implementation plan fixes the seams; the canonical arm table pins their exact
text before discharge. M1 (cut 18) and C3-b (cut 33) receive live override retargets
without changing assertions or checks. Other stale arms require explicit disposition.

`PREFIX_RUNNERS = ("cut44_acceptance.py",)`.
`PHASE_MODULES = ("test_belief_acceptance.py", "test_n2_cut45.py")`.
The runner uses the certified main-checkout work root and the existing test front
door. Missing capability is refusal, never skip. Accept-all matches unrestricted
refusal/absence/admission as well as values; a stricter behavior requires amendment.

Ordinary L_c uses only epoch-mapped records and a resolver restricted to the
recorded address map, with surviving inventoried facets F_c. W folds their union
through the world resolver. Compare L_c vs W for every surviving correction;
compare receipt vs L_c unless an original reachable in-corpus counter was excluded.
The packaged discovery map supplies original written targets, without rejected
facet decoding. Snapshot standing deliberately uses all captured records/resolvers.
Only filtered snapshot history enters trace, scoped.found and closure.

Completion follows all candidate scans/folds and correction scoping, before claim
lookup/consulted contracts. Early answers expose empty incomplete exclusions;
late caught errors keep completed reports. Supplied lineage not_present reaches
late absence; run/claim late-absence branches are defensive for world reads.
The wrapper's binding guard receives the initial incomplete context before reads.

## 6. Second reader

Verification edges are checked by stored address against accepted AND rejected
structural assessment targets, then by accepted semantic identity. A rejected twin
never joins visited or correction scope. A drift node with live id equal to a
mapped deprecated address distinguishes the full-capture resolver from the mapped
resolver, independently of iteration order. Receipt tests coherently repackage
corrupt resolutions so packaging checks cannot hide a missing fidelity check.
Early/late errors test the actual completion boundary; supplied snapshot absence
uses real lineage data rather than an unreachable monkeypatch.

## 7. Limitations

The statement describes supplied selection and authenticates no trust state.
Overlapping holders, publication attribution, epoch derivation amendments,
contract freeze and N2 preflight optimization remain their own tasks. Current
capture/damage/binding/absence checks remain unconditional. No acceptance runner
has yet discharged this cut; portable tests alone cannot do so.
