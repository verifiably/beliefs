**Accept — ready to merge.** The frozen beliefs range `1024ee6..56d4381` implements the approved ownership amendment without changing recovery code, registry provenance, or publication formats. No Critical, Important, or Minor findings. The controller can record this review, finish task lifecycle work for beliefs-7c612b, and integrate locally.

Reviewer identity: **codex/gpt-6-astra**, verified this turn by `timeout 2 relay model --harness codex --pretty` (exit 0).

**Strengths**

- `.worktrees/7c612b-replica-publication/python/src/beliefs/publish.py:251` finishes admission validation before inspecting ownership. The marker veto reads the entire captured holder, including records absent from the selection/index. Only eligible declared holders are excluded from attribution.
- `.worktrees/7c612b-replica-publication/python/src/beliefs/publish.py:318` validates exact container/member types and every identifier at the shared preparation boundary. The three public APIs remain keyword-only and preserve existing earlier preconditions.
- `.worktrees/7c612b-replica-publication/python/src/beliefs/session/writer.py:595` adds only the argument and forwarding. Existing currency, permission, and resolver checks still precede opening the world; malformed ownership does not displace those refusals.
- `.worktrees/7c612b-replica-publication/python/tests/acceptance/test_owned_replica_publication_acceptance.py:198` distinguishes successful source-independent reconstruction from refusal after removing a frozen coordination anchor. Both outcomes are tested without weakening recovery.
- `.worktrees/7c612b-replica-publication/python/tests/acceptance/test_n2_cut47.py:30` checks exact nine-unit accounting, independent mutations, passing baselines, frozen declarations, and preservation of earlier check ownership. The three cut-46 retargets preserve their original mutation semantics.
- Current-facing guides, both Y17 statements, roadmap accounting, and results agree. They explicitly leave science wiring and the live milestone result to sci-9a7ce2 and sci-775e90.

**Findings**

Critical: none.  
Important: none.  
Minor: none.

**Disposition of every execution-ledger ruling**

I reviewed all eight `Ruling:` entries in `.worktrees/7c612b-replica-publication/.superpowers/sdd/2026-10-27-owned-replica-publication/progress.md`.

1. **P1, shared durable fixture: accept.**  
   **Why:** `66cba34` extracts the existing verified restore/admission setup and adds the distinct Fresh writer without duplicating arrival logic. Both acceptance modules passed.  
   **Cost:** Shared-fixture regressions could affect earlier coverage; the fourteen legacy acceptance cases provide the required regression evidence.

2. **P2, expected-marker mutation: accept.**  
   **Why:** At `feaf73b`, Y17-x invents an attribution during `_expected_marker` reconstruction. Its local and remote-with-snapshot cases detect that change. Mark-only recovery is correctly reported as separate evidence.  
   **Cost:** Treating mark-only as the mutation killer would overstate proof; the final results explicitly avoid that claim.

3. **P3, pre-intent ordering evidence: accept with its stated limit.**  
   **Why:** The call order and portable/durable refusal tests establish that marker refusal precedes publication intent and operations writes. Y17-v tests forwarding, not an independent ordering sabotage.  
   **Cost:** There is no dedicated mutation proof for this ordering guarantee. That limit remains explicit at `56d4381`.

4. **Task 1 navigation/count expansion: accept.**  
   **Why:** `d7d10a0` makes the frozen cut discoverable without claiming discharge; `56d4381` updates the resulting current-state links and accounting after successful conformance.  
   **Cost:** Additional status surfaces can drift. Their final values and the documentation checks agree.

5. **Task 2 corrected guard filter: accept.**  
   **Why:** Replacing the nonexistent filter with the actual source-site guard corrects the command without weakening its assertions. The later complete cut-46 guard proves all 36 mutations.  
   **Cost:** A filtered check alone could miss coverage; the full guard removes that concern for this revision.

6. **First Task 3 retry ruling: reject as superseded, consistent with the ledger.**  
   **Why:** Replacing a resolver after intent does not erase frozen coordination anchors. The unchanged `coordination.bounds` requires the anchored mount set, and the new negative cases demonstrate `mounts-changed`.  
   **Cost:** Relying on the original ruling would promise successful binding that the implementation correctly refuses. The final tests and documentation no longer make that promise.

7. **Replacement Task 3 recovery ruling: accept.**  
   **Why:** At `66cba34`, successful source-deleted retries use writer-only coordination mounts from the start while selecting records from the replica-containing world. Separate source-anchored cases retain the refusal. This isolates attribution independence without waiving coordination evidence.  
   **Cost:** Successful reconstruction does not guarantee successful binding after losing a required coordination anchor. The spec, results, and guide disclose this limitation.

8. **Task 4 isolated test environment: accept.**  
   **Why:** The successful successor uses unchanged implementation `feaf73b`, preserves historical assertions/pins, and isolates host Git configuration after a recorded baseline failure. The original failure remains separate evidence; permanent harness isolation is tracked by beliefs-23f259.  
   **Cost:** The passing result establishes the isolated environment, not compatibility with the host’s global Git hooks.

I also checked the earlier attached design rulings I1 and M1–M5 against the final implementation and documents. Their dispositions remain supported; none introduces a deferred finding.

**Verification and limits**

I inspected recorded test evidence rather than rerunning the suite:

- Baseline: 6,230 non-N2 Python, 46 standalone N2, and 155 TypeScript passes; one Python skip.
- Focused evidence: 144 preparation/legacy/scoped passes, 24 scoped-door passes, 15 new durable passes, 14 legacy durable passes, and 577 permit/composition passes.
- Mutation guards: nine new checks and thirteen cut-46 checks passed, covering all nine new and 36 legacy mutations.
- Final checks: 6,278 Python passes and one skip; 45 documentation/runner passes; `just check` reports zero errors/warnings. The affected TypeScript selection was empty.
- Independently recomputed the successor log hash: `ef93d1794f7a51c4e913ba7de44cf90b6d037a97c693b0d8df70946643b15005`. Its 78 phases contain 1,189 summarized passes plus nine final guard dots, matching 1,198. The execution metadata records exit 0 and 2171.879 seconds.
- Verified the cut-freeze and canonical-declaration hashes. Only the cut’s status line changed after freeze; product code/tests did not change after the successful successor revision.

My branch-range `git diff --check` reports trailing whitespace only in `.worktrees/7c612b-replica-publication/tasks/files/beliefs-7c612b/cut47-runner-host-home.log:66`. This is preserved raw failure output, not a product defect; retain its exact bytes. The reported working-diff check should not be interpreted as a clean branch-range whitespace check.

**Declined to judge**

- Science consumer implementation and the live milestone outcome: separately assigned to sci-9a7ce2 and sci-775e90; this branch correctly makes no claim that they are complete.
- Permanent N2 host-environment isolation: tracked by beliefs-23f259. I assessed the isolated run’s validity, not an unimplemented harness repair.

**Verdict: accept; ready for local merge.** Review remained read-only: no files, index, branch state, or task notes changed; nothing pushed and no surviving processes launched. Integration remains the controller’s next step for `design/7c612b-replica-publication` in `.worktrees/7c612b-replica-publication`.

Not rerun: the 36-minute successor or test suites; recorded logs, metadata, hashes, and connected code were inspected. Remaining limits are explicit ownership claims, frozen coordination anchors, and pending science integration.
