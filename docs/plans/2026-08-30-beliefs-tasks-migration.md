# Beliefs Tasks migration ledger

**Status:** Tasks migration complete on 2026-08-31; the deferred Nodes dependency is reconciled as `beliefs-eacbe2` → `nodes-ce28b8`.

## Scope and evidence

| Field | Audited value |
|---|---|
| Stable HEAD at audit | `b1e8d5d73383f4ff306db8fa7be8c19d59e57eda` |
| Tasks source commit | `e04d6a0347a95f22324e81b79d07821cf34a83c5` |
| Audit date | 2026-08-30 |
| Integrated documentation commit | `755029b748e1e2990d4548f30588a7cf2a356187` |
| Integrated Tasks commit and stable verification HEAD | `1ee81bb13d03da42bce78e1fc80e0d050636ce36` |
| Atoms Linux 7.1.11 certification | `914acb66e796f8691b7cc10bb7c28daa54dddfbf` |
| Intervening post-integration user commit | `0415208b1a747697fa3961ad2ebad6a3919ceb70` |
| Integration and canonical registration date | 2026-08-31 |
| Prefix | `beliefs` (pre-existing and preserved) |
| Authority read | Root README; every tracked document under `docs/`; code, tests, schemas, and package configuration; all local branches and linked worktrees; current history; existing task `beliefs-c88566`; integrated Atoms task records used below |
| Forward-only rule | Completed cuts 1–12 remain Git/document history. Only evidence-backed unfinished outcomes are candidates. |

The adoption ledger's Current state table is authoritative for what remains open, and the cut-12 roadmap is authoritative for order. The approved user/autonomy design adds repository-owned work without reopening closed guarantee rows. Claims were checked against the base tree before any correction.

The exact 2,580-pass/144-fail results from Steps 1, 3, and 6 remain historical evidence from before Atoms certified the host Linux 7.1.11 tuple. After Atoms commit `914acb66e796f8691b7cc10bb7c28daa54dddfbf` was integrated, the same Beliefs stable tree passed all 2,724 tests. The earlier fail-closed result was neither waived nor rewritten.

## Git state inspected

| Checkout or ref | Commit | State and disposition |
|---|---|---|
| Stable `main` at the repository root | `b1e8d5d73383f4ff306db8fa7be8c19d59e57eda` | Clean; local branch was four commits ahead of `origin/main`. Read only. |
| Migration branch `chore/tasks-migration-beliefs` | `b1e8d5d73383f4ff306db8fa7be8c19d59e57eda` at audit start | Dedicated linked worktree; clean before the documented migration edits. |
| Local `feat/composition-root-adapter` | `794ee05` | Fully merged: the branch tip is an ancestor of `main`, with no branch-only commit and no linked worktree. No active ownership inferred. |
| Linked stable worktree | `main` | Clean and read only. |
| Linked migration worktree | `chore/tasks-migration-beliefs` | The only writable checkout for this migration. |
| Stable `main` after initial integration | `1ee81bb13d03da42bce78e1fc80e0d050636ce36` | The documentation and Tasks commits were fast-forwarded and the stable gates and canonical registration passed. The later user start of `beliefs-c88566` was outside the migration and was not touched by it. |
| Stable `main` after the intervening user commit | `0415208b1a747697fa3961ad2ebad6a3919ceb70` | Clean. The user commit added `beliefs-5f2752` and `beliefs-abf8e8`, updated `beliefs-bc3aff`, and committed the previously separate `beliefs-c88566` start. Those task changes are outside the migration. |
| Atoms stable `main` | `914acb66e796f8691b7cc10bb7c28daa54dddfbf` | Clean; certified for the host Linux 7.1.11 tuple used by the final Beliefs stable gates. |

History confirms that conformance cut 12, successor admission, current-state curation, the package rename, and the holdings-boundary rename correction are ancestors of the audited base. No unmerged branch or dirty path carries unfinished implementation.

## Document classification

| Document | Classification | Evidence |
|---|---|---|
| `AGENTS.md` | authority/current | Repository authority and gates, added by this migration. |
| `README.md` | authority/current | Current package, cut-12 state, entry points, and guide navigation. |
| `docs/designs/2026-08-02-computation-reproducibility-design.md` | authority/current | Banked computation guarantees and open questions. |
| `docs/designs/2026-08-02-epistemic-kernel-design.md` | authority/current | Banked kernel guarantees and vocabulary. |
| `docs/designs/2026-08-02-substrate-consolidation-design.md` | authority/current | Banked substrate boundary. |
| `docs/designs/2026-08-02-world-addressing-design.md` | authority/current | Banked world-addressing contract. |
| `docs/designs/2026-08-03-correction-lifecycle-design.md` | authority/current | Banked correction contract; its remainder is current roadmap evidence. |
| `docs/designs/2026-08-03-normative-contract-design.md` | authority/current | Banked contract and adoption guarantees. |
| `docs/designs/2026-08-03-redesign-adoption-ledger.md` | authority/current | Authoritative Current state table at cut 12. |
| `docs/designs/2026-08-03-tamper-evident-log-design.md` | authority/current | Banked log guarantees and limitations. |
| `docs/designs/2026-08-03-world-index-packaging-design.md` | authority/current | Banked world packaging guarantees. |
| `docs/designs/2026-08-04-domain-extension-boundary-design.md` | authority/current | Banked domain-extension contract. |
| `docs/designs/2026-08-04-formal-model-and-claim-calculus-design.md` | authority/current | Banked formal model and claim calculus. |
| `docs/designs/2026-08-05-belief-policy-design.md` | authority/current | Banked belief-policy contract and successor question. |
| `docs/designs/2026-08-05-review-disposition-and-conformance-cut-1.md` | historical/superseded | Frozen review disposition and cut-1 evidence. |
| `docs/designs/2026-08-07-corpus-survey-and-vocabulary-admission-design.md` | authority/current | Banked vocabulary-admission rule. |
| `docs/designs/2026-08-07-multi-corpus-typing-exercise.md` | historical/superseded | Dated evidence exercise, not current authority. |
| `docs/designs/2026-08-08-contributor-guide-design.md` | authority/current | Banked guide contract. |
| `docs/designs/2026-08-08-world-address-ruling.md` | authority/current | Current ruling used by world-resolution work. |
| `docs/designs/2026-08-09-admission-ramp-design.md` | authority/current | Banked admission-ramp rule. |
| `docs/designs/2026-08-09-admission-ramp-survey.json` | historical/superseded | Dated survey evidence. |
| `docs/designs/2026-08-09-conformance-cut-2.md` | historical/superseded | Frozen cut body. |
| `docs/designs/2026-08-10-verified-holdings-record-design.md` | authority/current | Banked holdings record contract. |
| `docs/designs/2026-08-11-act-report-design.md` | authority/current | Banked operation and act-report contract. |
| `docs/designs/2026-08-11-conformance-cut-3.md` | historical/superseded | Frozen cut body. |
| `docs/designs/2026-08-17-conformance-cut-4.md` | historical/superseded | Frozen cut body. |
| `docs/designs/2026-08-18-composition-root-adapter-design.md` | authority/current | Banked composition-root adapter contract. |
| `docs/designs/2026-08-19-conformance-cut-5.md` | historical/superseded | Frozen cut body. |
| `docs/designs/2026-08-19-family-adapters-design.md` | authority/current | Banked family-adapter contract and consolidate deferral. |
| `docs/designs/2026-08-20-conformance-cut-6.md` | historical/superseded | Frozen cut body. |
| `docs/designs/2026-08-20-conformance-cut-7.md` | historical/superseded | Frozen cut body. |
| `docs/designs/2026-08-20-world-index-slice-2-design.md` | authority/current | Banked world-index epoch contract. |
| `docs/designs/2026-08-20-world-registry-design.md` | authority/current | Banked registry contract. |
| `docs/designs/2026-08-22-conformance-cut-8.md` | historical/superseded | Frozen cut body. |
| `docs/designs/2026-08-22-log-verification-design.md` | authority/current | Banked log-verification contract. |
| `docs/designs/2026-08-23-conformance-cut-9.md` | historical/superseded | Frozen cut body. |
| `docs/designs/2026-08-23-world-index-root-lifecycle-design.md` | authority/current | Banked root-lifecycle contract. |
| `docs/designs/2026-08-24-conformance-cut-10.md` | historical/superseded | Frozen cut body. |
| `docs/designs/2026-08-24-world-index-holdings-design.md` | authority/current | Banked holdings/world-index contract. |
| `docs/designs/2026-08-26-world-index-intent-boundary-design.md` | authority/current | Banked intent boundary. |
| `docs/designs/2026-08-27-conformance-cut-11.md` | historical/superseded | Frozen cut body. |
| `docs/designs/2026-08-29-conformance-cut-12.md` | historical/superseded | Frozen cut body. |
| `docs/designs/2026-08-29-successor-admission-design.md` | authority/current | Banked successor-admission contract delivered by cut 12. |
| `docs/guide/README.md` | authority/current | Current guide index and project-state orientation. |
| `docs/guide/claims-and-belief.md` | authority/current | Current guide synthesis. |
| `docs/guide/computation-and-reproducibility.md` | authority/current | Current guide synthesis. |
| `docs/guide/contracts-and-adoption.md` | authority/current | Current guide synthesis. |
| `docs/guide/foundations.md` | authority/current | Current foundational orientation. |
| `docs/guide/glossary.md` | authority/current | Current public vocabulary. |
| `docs/guide/identity-world-and-change.md` | authority/current | Current guide synthesis. |
| `docs/guide/open-questions.md` | authority/current | Living navigation for unresolved design questions. |
| `docs/plans/2026-08-08-contributor-guide.md` | historical/superseded | Delivered implementation plan. |
| `docs/plans/2026-08-18-conformance-cut-4-results.md` | historical/superseded | Dated discharge evidence. |
| `docs/plans/2026-08-19-conformance-cut-5-results.md` | historical/superseded | Dated discharge evidence. |
| `docs/plans/2026-08-20-conformance-cut-6-results.md` | historical/superseded | Dated discharge evidence. |
| `docs/plans/2026-08-20-conformance-cut-7-results.md` | historical/superseded | Dated discharge evidence. |
| `docs/plans/2026-08-22-conformance-cut-8-results.md` | historical/superseded | Dated discharge evidence. |
| `docs/plans/2026-08-22-log-verification-ledger.md` | historical/superseded | Delivered boundary ledger. |
| `docs/plans/2026-08-23-conformance-cut-9-results.md` | historical/superseded | Dated discharge evidence. |
| `docs/plans/2026-08-23-root-lifecycle-ledger.md` | historical/superseded | Delivered boundary ledger. |
| `docs/plans/2026-08-24-conformance-cut-10-results.md` | historical/superseded | Dated discharge evidence. |
| `docs/plans/2026-08-24-holdings-ledger.md` | historical/superseded | Delivered boundary ledger. |
| `docs/plans/2026-08-27-conformance-cut-11-results.md` | historical/superseded | Dated discharge evidence. |
| `docs/plans/2026-08-27-intent-boundary-ledger.md` | historical/superseded | Delivered boundary ledger. |
| `docs/plans/2026-08-28-current-state-evidence.md` | historical/superseded | Dated evidence for the current-state curation commit. |
| `docs/plans/2026-08-29-conformance-cut-12-results.md` | historical/superseded | Dated discharge evidence. |
| `docs/plans/2026-08-29-implementation-roadmap.md` | authority/current | Authoritative cut-12 ordering and candidate boundaries. |
| `docs/plans/2026-08-29-successor-admission-ledger.md` | historical/superseded | Delivered boundary ledger. |
| `docs/plans/2026-08-30-beliefs-tasks-migration.md` | historical/superseded | Migration and deferred cross-project dependency reconciliation are complete. |
| `docs/superpowers/plans/2026-08-09-cut-2-slice.md` | historical/superseded | Delivered implementation plan. |
| `docs/superpowers/plans/2026-08-10-bank-holdings-record.md` | historical/superseded | Delivered implementation plan. |
| `docs/superpowers/plans/2026-08-11-bank-act-report.md` | historical/superseded | Delivered implementation plan. |
| `docs/superpowers/plans/2026-08-12-cut-3-slice.md` | historical/superseded | Delivered implementation plan. |
| `docs/superpowers/plans/2026-08-17-cut-4-selection.md` | historical/superseded | Delivered implementation plan. |
| `docs/superpowers/plans/2026-08-17-python-tests-pyright.md` | historical/superseded | Delivered maintenance plan. |
| `docs/superpowers/plans/2026-08-19-family-adapters.md` | historical/superseded | Delivered implementation plan. |
| `docs/superpowers/plans/2026-08-20-world-index-slice-2.md` | historical/superseded | Delivered implementation plan. |
| `docs/superpowers/plans/2026-08-20-world-registry-slice-1.md` | historical/superseded | Delivered implementation plan. |
| `docs/superpowers/plans/2026-08-22-log-verification.md` | historical/superseded | Delivered implementation plan. |
| `docs/superpowers/plans/2026-08-23-root-lifecycle.md` | historical/superseded | Delivered implementation plan. |
| `docs/superpowers/plans/2026-08-24-holdings.md` | historical/superseded | Delivered implementation plan. |
| `docs/superpowers/plans/2026-08-27-intent-boundary.md` | historical/superseded | Delivered implementation plan. |
| `docs/superpowers/plans/2026-08-28-current-state-documentation-curation.md` | historical/superseded | Delivered documentation plan. |
| `docs/superpowers/plans/2026-08-29-implementation-roadmap.md` | historical/superseded | Delivered plan that produced the current roadmap. |
| `docs/superpowers/plans/2026-08-29-successor-admission.md` | historical/superseded | Delivered implementation plan. |
| `docs/superpowers/plans/2026-08-30-run-confinement.md` | active delivery | Current, not-yet-implemented cut-13 plan. |
| `docs/superpowers/specs/2026-08-17-conformance-cut-4-scope-design.md` | historical/superseded | Delivered scoping design. |
| `docs/superpowers/specs/2026-08-28-current-state-documentation-curation-design.md` | historical/superseded | Delivered documentation design. |
| `docs/superpowers/specs/2026-08-29-implementation-roadmap-design.md` | historical/superseded | Delivered ranking-method design. |
| `docs/superpowers/specs/2026-08-29-user-and-autonomy-layer-design.md` | active delivery | Approved umbrella design with unfinished Beliefs sub-projects. |
| `docs/superpowers/specs/2026-08-30-run-confinement-design.md` | active delivery | Current, planned, not-yet-implemented cut-13 design. |
| `docs/superpowers/specs/2026-08-31-coordination-and-view-kinds-design.md` | active delivery | Design and review are cleared and cut 14 is frozen before implementation; explicitly not implemented. |

## Drift corrections

| Claim | Evidence | Correction | Outward-grep result |
|---|---|---|---|
| The guide said the agentic surface had no design. | The approved user/autonomy design is present and its sub-project 0 is delivered, while the surface itself is not implemented. | `docs/guide/README.md` and `docs/guide/foundations.md` now distinguish approved design from unfinished implementation and keep salvage undesigned. | Searches of the README, guide, roadmap, and active specs found no remaining current-facing claim that both areas lack designs. |
| The run-confinement design said it was not planned. | The detailed run-confinement implementation plan is tracked beside it and names cut 13. | Its status now says designed and planned, not implemented, and links the plan. | The paired design and plan now agree; no other current status repeats the stale claim. |
| The current roadmap and active cut-13 design/plan used the pre-rename executable package path, import name, and captured package-tree prose. | The tree, package metadata, imports, and tests use `python/src/beliefs` and `beliefs.*`; the rename is in base history. | Executable source paths, module invocations, imports, test module names, the roadmap's domain-lane path, and the cut-13 plan's three captured-package-tree references now use `beliefs`. Frozen identity domains such as `science.environment.v2`, `science.boundary-receipt.v2`, `science.run.v2`, and sandbox paths under `/science/` remain unchanged. | Negative searches across the current roadmap and active cut-13 pair find no `python/src/science`, `src/science`, `from science.`, `import science.`, or stale `science tree` package prose, and find no accidental `beliefs.*.vN` identity replacement. Historical plans and cut evidence were not rewritten. |

The open coordination question, cut-12 ranking, and Current state table remain intentionally unchanged. The approved user/autonomy design says the coordination bullet leaves the guide only when sub-project 1's design lands and that the roadmap re-ranks in the same later commit. Existing task `beliefs-c88566` owns that design decision.

## Candidate outcomes

| Outcome | Evidence | Sources | Active state | Size | Proposed status | Blockers | Disposition | Task ID |
|---|---|---|---|---|---|---|---|---|
| Preserve completed cuts 1–12 | Cut results, code, tests, and ancestry prove delivery; unchecked historical plan boxes do not contradict it. | Adoption ledger; cut results; history | No active branch | n/a | n/a | n/a | no task: completed history | n/a |
| Deliver run confinement and discharge cut 13 | Tier-1 boundary is fully designed and planned but absent from code. | Roadmap `run-confinement`; run-confinement design and plan | No active branch or owner | xl | todo | none | create | `beliefs-739255` |
| Deliver the full workflow surface | Cut 3 explicitly left multi-rule, family, wildcard, and definition-equality workflows outside the minimal adapter. | Roadmap `workflow-surface`; computation design | No active branch or owner | xl | todo | `beliefs-739255`, by strict execution-lane order | create | `beliefs-73be28` |
| Deliver consolidate, move, and managed deletion | The roadmap groups the last mutation family with run-boundary and formal-model ride-alongs. | Roadmap `consolidate-family`; family-adapters and correction designs | No active branch or owner | xl | todo | none | create | `beliefs-676a2c` |
| Deliver URL acquisition and act-report coverage | URL locators and remote acquisition remain open; act-report remainders explicitly ride with the boundary. | Roadmap `url-retrieval`; holdings and act-report designs | No active branch or owner | l | todo | none | create | `beliefs-d13fe8` |
| Deliver world resolution and packaging remainder | The write boundary and index have landed; the read-side resolution rows and packaging ride-along remain open. | Roadmap `world-resolution`; world addressing and packaging designs | No active branch or owner | xl | todo | none | create | `beliefs-d248ba` |
| Deliver the domain boundary, biology pack, and second parity fixture | Domain kinds remain absent; the approved biology pack and second fixture ride with this boundary. | Roadmap `domain-boundary`; domain design; user/autonomy design §8 | No active branch or owner | xl | todo | none | create | `beliefs-bc3aff` |
| Deliver event-level L8 and the log remainder | The ordered-cuts predicate exists; event-level relation and log relabels remain. | Roadmap `event-level-l8`; log design | No active branch or owner | l | todo | `beliefs-d248ba`, by strict world-read-lane order | create | `beliefs-b34652` |
| Deliver the first full contract cut | Contract identity, certification, legacy-check, and rules-store rows remain; roadmap makes this the post-lane join. | Roadmap `contract-cut`; normative contract design | No active branch or owner | xl | todo | CLI: `beliefs-73be28`; `beliefs-aa27da`; `beliefs-d13fe8`; `beliefs-b34652`; `beliefs-bc3aff`; `beliefs-a7df71`; `beliefs-3ea822`. Deferred: Nodes `nodes-remainder`. | create | `beliefs-eacbe2` |
| Complete the correction lifecycle | C7–C10 remainders remain and C7 requires the consolidate surface. | Roadmap `correction-remainder`; correction lifecycle design | No active branch or owner | xl | todo | `beliefs-676a2c` | create | `beliefs-aa27da` |
| Close L13 through a public preimage seam | L13 needs blob bytes rather than only a path; Atoms owns the audited seam. | Roadmap `l13-preimage`; Atoms task `atoms-38887b` | No active branch or owner | m | todo | `atoms-38887b` | create | `beliefs-a7df71` |
| Certify publication persistence | X2 needs Atoms A8 extended through the publication path. | Roadmap `persistence-cut`; Atoms task `atoms-f5779f` | No active branch or owner | l | todo | `atoms-f5779f` | create | `beliefs-3ea822` |
| Nodes damaged-corpus and manifest remainder | The roadmap assigns this work to Nodes behind Nodes' own design gate. | Roadmap `nodes-remainder` | No Beliefs-owned state | n/a | n/a | future Nodes outcome | no task: producer-owned | n/a |
| Design authority snapshot labels | W9/W14 remain blocked on authority snapshot governance. | Roadmap `authority-labels`; open questions | No active branch or owner | l | idea | unresolved design evidence, not a task edge | create | `beliefs-84d7b0` |
| Design coordination and view kinds (sub-project 1, coordination-addressing) | The exact existing task record was audited through the CLI; it owns the tier-3 answer and next re-rank. | User/autonomy design §§4.1–4.2, §8; roadmap | No active branch or owner | n/a | n/a | n/a | preserve (no task mutation) | beliefs-c88566 |
| Deliver coordination and view kinds | The approved umbrella design specifies the governed kinds and guarantee rows, while the existing task owns the design that must land first. | User/autonomy design §§4.1–4.2, §8; roadmap `coordination-addressing` | No active branch or owner | xl | todo | `beliefs-c88566` | create | `beliefs-acc2e9` |
| Design weighted-belief semantics | S6(h) awaits an estimand-typing and weighting ruling. | Roadmap `weighted-belief`; belief policy; open questions | No active branch or owner | l | idea | unresolved design evidence, not a task edge | create | `beliefs-638318` |
| Design the higher-order extraction path | M12 awaits a ruling for extraction and higher-order records. | Roadmap `extraction-path`; formal-model design; open questions | No active branch or owner | l | idea | unresolved design evidence, not a task edge | create | `beliefs-9e1f60` |
| Design cross-root publication residue | T7's cross-root case remains an explicit design question. | Roadmap `cross-root-publication`; act-report design; open questions | No active branch or owner | l | idea | unresolved design evidence, not a task edge | create | `beliefs-256f17` |
| Enforce write permits at every Beliefs write entry point | The approved command-framework design requires permits in the kernel writer, family adapters, run boundary, and publish path; none exists in code. | User/autonomy design §5.2 and §8 item 2 | No active branch or owner | xl | todo | none | create | `beliefs-96a24a` |
| Implement the Beliefs publish act and governed records | The approved design specifies the act, publication marker/binding, recovery, and act-report amendment; no publish entry point or record kinds exist. | User/autonomy design §§4.1, 6, and §8 item 5 | No active branch or owner | xl | todo | `beliefs-acc2e9`; `beliefs-b34652` (completion of the world-read lane) | create | `beliefs-1a5157` |
| Build the command framework and dogfood commands | The approved design assigns the daily surface, generated adapters, CLI/MCP, and command set to the Science repository. | User/autonomy design §5 and §8 items 2 and 4 | No Beliefs-owned state | n/a | n/a | Beliefs permits and roadmap lanes are consumer dependencies | no task: Science-owned | n/a |
| Build the autonomy envelope and loop | The approved design assigns sandbox, lease, tiers, trajectory, and priority loop to the Autonomy repository. | User/autonomy design §7 and §8 items 6 and 7 | No Beliefs-owned state | n/a | n/a | Science command outcomes are consumer dependencies | no task: Autonomy-owned | n/a |

Every `create` row uses the `migration` tag plus one stable lane or concern tag. Each body states the outcome, acceptance evidence, sources, and uncertainty. The four tier-3 design decisions are `idea`; unfinished designed delivery is `todo`; no `doing` or `blocked` state is inferred from branch names or dependencies.

The candidate table remains the 2026-08-30 audit and creation record. After initial integration, separate user activity on 2026-08-31 started `beliefs-c88566` in stable `main` (`doing`, owner `main`, updated `2026-08-31T09:25:24Z`). Canonical registry commands preserved working-tree blob `9abf319cfb58704a5bee937d3193831c79ff4972` byte-for-byte; the later user commit `0415208b1a747697fa3961ad2ebad6a3919ceb70` then tracked that exact blob alongside three other user-owned task changes. Both activities are outside the migration, and this ledger finalization neither copies nor rewrites them.

### Reviewed task body: Deliver run confinement and discharge cut 13

Outcome: Beliefs executes the confinement-capable boundary policy inside a fresh, digest-verified runtime closure and admits `clean-environment` only through the confined evidence join.

Acceptance evidence: Freeze cut 13 before implementation; deliver the runtime closure, snapshot, sandbox, probe, receipt, run-domain dispatch, fourth scope row, and admission join specified by the approved plan; pass its negative harnesses and complete Python and TypeScript gates on the certified kernel/volume tuple; discharge the selected rows, update the adoption ledger and roadmap, and bank the results.

Sources: `docs/plans/2026-08-29-implementation-roadmap.md` `run-confinement`; `docs/superpowers/specs/2026-08-30-run-confinement-design.md`; and `docs/superpowers/plans/2026-08-30-run-confinement.md`.

Uncertainty: The implementation is fully planned but absent. Capability admission remains kernel- and volume-specific and must fail closed on uncertified tuples.

Initial fields: priority `1`; status `todo`; size `xl`; tags `migration`, `execution`, `conformance`.

### Reviewed task body: Deliver the full workflow surface

Outcome: Beliefs supports the designed multi-rule, family, wildcard, definition-equality, and multi-product workflow surface beyond the cut-3 minimal adapter.

Acceptance evidence: Approve and freeze a cut after run confinement; implement the full workflow declarations and run paths without weakening confinement; discharge R2, R16, R20, R21's workflow arms and R23's second-production arm with positive and negative tests; update the adoption ledger and roadmap; and pass the complete repository gates.

Sources: `docs/plans/2026-08-29-implementation-roadmap.md` `workflow-surface`; `docs/designs/2026-08-02-computation-reproducibility-design.md`; and cut 3's deferred workflow accounting.

Uncertainty: The banked design fixes the outcome, but its cut scope and implementation plan do not yet exist.

Initial fields: priority `1`; status `todo`; size `xl`; tags `migration`, `execution`, `workflow`.

### Reviewed task body: Deliver consolidate, move, and managed deletion

Outcome: Beliefs completes the stored-record mutation family with consolidate, cross-corpus move, and managed deletion semantics, including the assigned run-boundary and formal-model ride-alongs.

Acceptance evidence: Freeze a mutation-lane cut; implement the family through the governed write boundary and world registry; prove digest invariance, history preservation, deletion negatives, replica behavior, explicit-import audit behavior, and retraction-graph ordering; discharge the roadmap rows; update current status; and pass all repository gates.

Sources: `docs/plans/2026-08-29-implementation-roadmap.md` `consolidate-family`, `run-boundary-remainder`, and `formal-model-remainder`; `docs/designs/2026-08-19-family-adapters-design.md`; and `docs/designs/2026-08-03-correction-lifecycle-design.md`.

Uncertainty: The outcome is buildable, but the exact cut and interaction between consolidate and deletion need a dedicated design and plan.

Initial fields: priority `2`; status `todo`; size `xl`; tags `migration`, `mutation`, `world`.

### Reviewed task body: Deliver URL acquisition and act-report coverage

Outcome: Beliefs acquires datasets through canonical URL locators under the banked network discipline and closes the act-report remainder with the new acquisition operation surface.

Acceptance evidence: Design and freeze the acquisition cut; implement canonicalization, network and redirect policy, provenance, refusal reporting, and same-root behavior; cover H4, G9, R10, T5, T7's same-root case and T1/T2/T4 with deterministic tests; update current status; and pass the complete gates.

Sources: `docs/plans/2026-08-29-implementation-roadmap.md` `url-retrieval` and `act-report-remainder`; `docs/designs/2026-08-10-verified-holdings-record-design.md`; and `docs/designs/2026-08-11-act-report-design.md`.

Uncertainty: Canonicalization and network discipline are banked, but the concrete retrieval cut and supported transport behavior are not planned.

Initial fields: priority `2`; status `todo`; size `l`; tags `migration`, `acquisition`, `act-report`.

### Reviewed task body: Deliver world resolution and packaging remainder

Outcome: Beliefs resolves the world read side across corpora, including views, coreference, snapshot clauses, and the packaging/import/audit ride-along.

Acceptance evidence: Freeze a world-read cut; implement resolution states and cross-corpus queries against the landed write boundary and index; exercise omission, divergence, coverage, snapshot, packaging, and audit negatives; discharge every roadmap row assigned to `world-resolution` and `packaging-remainder`; update current status; and pass all gates.

Sources: `docs/plans/2026-08-29-implementation-roadmap.md` `world-resolution` and `packaging-remainder`; `docs/designs/2026-08-02-world-addressing-design.md`; `docs/designs/2026-08-08-world-address-ruling.md`; and `docs/designs/2026-08-03-world-index-packaging-design.md`.

Uncertainty: The required write and index prerequisites have landed, but the resolver cut and its public query shape are not yet planned.

Initial fields: priority `2`; status `todo`; size `xl`; tags `migration`, `world-read`, `resolution`.

### Reviewed task body: Deliver the domain boundary, biology pack, and second parity fixture

Outcome: Beliefs admits governed domain kinds through a compiled domain boundary, ships the GO/HP/EFO/MONDO biology bindings and mm30 operator vocabulary, and proves a second Python/TypeScript parity fixture.

Acceptance evidence: Design and freeze the domain cut; implement domain-pack compilation and refusal behavior without project-local suppressions; add the biology pack and second `science.identity.v1` parity fixture; discharge D1, D2, D4–D6, D8–D10 and G5; update current status; and pass the Python and TypeScript gates.

Sources: `docs/plans/2026-08-29-implementation-roadmap.md` `domain-boundary` and `parity-fixture-2`; `docs/designs/2026-08-04-domain-extension-boundary-design.md`; and `docs/superpowers/specs/2026-08-29-user-and-autonomy-layer-design.md` §4.3 and §8 item 3.

Uncertainty: The domain contract is banked, but distribution/governance details and the exact biology bindings require the boundary's design cycle.

Initial fields: priority `2`; status `todo`; size `xl`; tags `migration`, `domain`, `parity`.

### Reviewed task body: Deliver event-level L8 and the log remainder

Outcome: Beliefs extends the world-read lane with the event-level relation required by L8 and closes the assigned L1, L4, and L10 log remainder.

Acceptance evidence: After world resolution lands, freeze and implement the event-level successor to ordered cuts; add positive, divergence, corruption, and relabel evidence; discharge L8 and the ride-along rows; update the adoption ledger and roadmap; and pass the complete gates.

Sources: `docs/plans/2026-08-29-implementation-roadmap.md` `event-level-l8` and `log-remainder`; `docs/designs/2026-08-03-tamper-evident-log-design.md`; and `docs/designs/2026-08-22-log-verification-design.md`.

Uncertainty: The ordered-cuts predicate exists, but the event-level relation's design and cut plan do not.

Initial fields: priority `2`; status `todo`; size `l`; tags `migration`, `world-read`, `log`.

### Reviewed task body: Deliver the first full contract cut

Outcome: Beliefs freezes and implements the first full successor contract after every oracle-amending lane, including certification cadence, conformance-package split, rules-store resolution, and legacy-check disposition.

Acceptance evidence: Wait for the execution (`beliefs-73be28`), acquisition (`beliefs-d13fe8`), mutation (`beliefs-aa27da`), world-read (`beliefs-b34652`), domain (`beliefs-bc3aff`), L13 (`beliefs-a7df71`), and persistence (`beliefs-3ea822`) endpoints, plus the resolved Nodes producer `nodes-ce28b8` (`nodes-remainder`); design the successor identities and governance decisions; freeze before implementation; discharge N1–N10, P1 and the assigned certification/resolver/rules-store arms; update the authority artifacts and roadmap; and pass all Python, TypeScript, corpus, and parity gates.

Sources: `docs/plans/2026-08-29-implementation-roadmap.md` `contract-cut` and join rule; `docs/designs/2026-08-03-normative-contract-design.md`; and `docs/guide/open-questions.md` Contracts and adoption.

Uncertainty: The roadmap fixes the join point, but successor identities, certification cadence, normative artifact shape, and legacy-check ruling need their design cycle. The Nodes producer `nodes-ce28b8` is resolved but unfinished and remains a blocker.

Initial fields: priority `2`; status `todo`; size `xl`; tags `migration`, `contract`, `conformance`.

### Reviewed task body: Complete the correction lifecycle

Outcome: Beliefs completes standing-retraction evaluation, conflict semantics, semantic snapshots, coverage, audit reporting, and correction succession over the delivered consolidate family.

Acceptance evidence: After consolidate lands, design and freeze the correction cut; implement and test C7–C10's remaining arms including uncovered corpora, exact-state receipts, mount and raw-write negatives; update the adoption ledger and roadmap; and pass the complete gates.

Sources: `docs/plans/2026-08-29-implementation-roadmap.md` `correction-remainder`; `docs/designs/2026-08-03-correction-lifecycle-design.md`; and the cut-5 correction accounting.

Uncertainty: Consolidate is a proven prerequisite; the semantic-snapshot kind and evaluator are this outcome's still-unplanned work.

Initial fields: priority `3`; status `todo`; size `xl`; tags `migration`, `mutation`, `correction`.

### Reviewed task body: Close L13 through a public preimage seam

Outcome: Beliefs strengthens L13 from path evidence to held-copy byte matching through the narrow public Atoms preimage reader.

Acceptance evidence: Consume the reviewed seam delivered by `atoms-38887b`; design the Beliefs-side classification and refusal boundary; verify indexed preimage bytes under the correct lease and corruption semantics; discharge L13 with positive and negative evidence; update current status; and pass the complete gates.

Sources: `docs/plans/2026-08-29-implementation-roadmap.md` `l13-preimage`; `docs/designs/2026-08-03-tamper-evident-log-design.md`; and Atoms task `atoms-38887b`.

Uncertainty: Atoms has the internal verified reader but has not delivered the public seam, so the exact consumer interface remains pending there.

Initial fields: priority `3`; status `todo`; size `m`; tags `migration`, `cross-repo`, `log`.

### Reviewed task body: Certify publication persistence

Outcome: Beliefs closes X2 with persistence-cut certification that exercises its real publication path through the Atoms durability boundary.

Acceptance evidence: Consume the Atoms harness delivered by `atoms-f5779f`; extend the Beliefs-side composition test across each X2 stage without a duplicate transaction authority; record reproducible zero-violation evidence or fail closed; discharge X2; update current status; and pass both affected repositories' complete gates.

Sources: `docs/plans/2026-08-29-implementation-roadmap.md` `persistence-cut`; cut 7's X2 accounting; and Atoms task `atoms-f5779f`.

Uncertainty: The current publication path exists, but its cross-repository persistence-cut harness and certified hardware scope do not.

Initial fields: priority `3`; status `todo`; size `l`; tags `migration`, `cross-repo`, `durability`.

### Reviewed task body: Design authority snapshot labels

Outcome: Beliefs gains an approved design for pinning, versioning, distributing, and amending the authority snapshots used by labels and ambiguous-search refusal.

Acceptance evidence: Resolve who accepts authorities, how a snapshot is identified and bumped, whether a bump is an amendment act, and how offline deterministic readers consume it; map the decision to W9 and W14; produce an implementation plan only after the design is approved.

Sources: `docs/plans/2026-08-29-implementation-roadmap.md` `authority-labels`; `docs/designs/2026-08-08-world-address-ruling.md`; and `docs/guide/open-questions.md` Identity, world, and change.

Uncertainty: No authority set, governance rule, implementation commitment, active branch, or owner is established.

Initial fields: priority `4`; status `idea`; size `l`; tags `migration`, `design`, `authority`.

### Reviewed task body: Deliver coordination and view kinds

Outcome: Beliefs implements governed view and coordination kinds, opaque project identity, `(project, local id)` addressing, and the revision/tip rules that close W11, W12, and W13's two-project negative.

Acceptance evidence: Begin only after `beliefs-c88566` approves the dedicated design; freeze the resulting mutation-lane cut; compile the independently versioned coordination contract into `ProfileSpec`; implement factories, address and predecessor checks, divergence refusal, and guarantee-row tests; update foundations, the open question, adoption ledger, and roadmap; and pass all gates.

Sources: `docs/superpowers/specs/2026-08-29-user-and-autonomy-layer-design.md` §§4.1–4.2 and §8 item 1; `docs/plans/2026-08-29-implementation-roadmap.md` `coordination-addressing`; and existing task `beliefs-c88566`.

Uncertainty: The approved umbrella design fixes the outcome, but `beliefs-c88566` still owns the dedicated design decisions, including the closed view-query language.

Initial fields: priority `2`; status `todo`; size `xl`; tags `migration`, `mutation`, `coordination`.

### Reviewed task body: Design weighted-belief semantics

Outcome: Beliefs gains an approved successor-policy design for unequal evidence weights grounded in estimand typing rather than unowned constants.

Acceptance evidence: Assign estimand-typing ownership; decide which study-design or precision evidence may affect weights and whether constants are global or domain-scoped; specify identity, receipts, failure behavior, and S6(h); produce an implementation plan only after approval.

Sources: `docs/plans/2026-08-29-implementation-roadmap.md` `weighted-belief`; `docs/designs/2026-08-05-belief-policy-design.md`; and `docs/guide/open-questions.md` Weighted belief.

Uncertainty: Estimand compatibility and an owner are unresolved, so implementation status is not yet justified.

Initial fields: priority `4`; status `idea`; size `l`; tags `migration`, `design`, `belief`.

### Reviewed task body: Design the higher-order extraction path

Outcome: Beliefs gains an approved extraction design that re-homes higher-order records and defines how claims may address internal records without weakening the kernel boundary.

Acceptance evidence: Classify the eleven higher-order records, fix the extraction step and admitted kinds, specify identity, provenance, refusal, and migration-free handling, map the ruling to M12, and produce an implementation plan only after approval.

Sources: `docs/plans/2026-08-29-implementation-roadmap.md` `extraction-path`; `docs/designs/2026-08-04-formal-model-and-claim-calculus-design.md`; and `docs/guide/open-questions.md` Higher-order records.

Uncertainty: The kernel limitation is explicit, but no extraction mechanism, kind allocation, branch, or owner exists.

Initial fields: priority `4`; status `idea`; size `l`; tags `migration`, `design`, `formal-model`.

### Reviewed task body: Design cross-root publication residue

Outcome: Beliefs gains an approved rule for the cross-root provenance/report residue in T7 without creating an unguarded write path.

Acceptance evidence: Decide how a dataset provenance reference and acquiring report cross roots, where their durable identities live, how refusal and retry work, and how the result composes with existing act reports and publication; map the ruling to T7 and plan implementation only after approval.

Sources: `docs/plans/2026-08-29-implementation-roadmap.md` `cross-root-publication`; `docs/designs/2026-08-11-act-report-design.md`; and `docs/guide/open-questions.md` The act-report's residue.

Uncertainty: Cross-root publication is currently refused and no acceptable authority or transport rule has been selected.

Initial fields: priority `4`; status `idea`; size `l`; tags `migration`, `design`, `publication`.

### Reviewed task body: Enforce write permits at every Beliefs write entry point

Outcome: Every Beliefs write entry point enforces a session-bound closed permit against the actual emitted kind or act and fixes actor identity at the trusted writer boundary.

Acceptance evidence: Design the Beliefs half of the command-framework boundary; cover `CorpusWriter.add`, family adapters, run entry points, and the future publish entry point; refuse declaration mismatch and body overreach before effects; prevent requests from carrying permits or actor strings; expose the writer-session contract needed by Science; and pass direct, bypass, and end-to-end negative tests plus the complete gates.

Sources: `docs/superpowers/specs/2026-08-29-user-and-autonomy-layer-design.md` §5.2 and §8 item 2.

Uncertainty: The cross-repository endpoint and launcher live partly in Science, so the Beliefs API boundary needs its own design and coordinated consumer tests; no permit type exists today.

Initial fields: priority `2`; status `todo`; size `xl`; tags `migration`, `writer`, `permits`.

### Reviewed task body: Implement the Beliefs publish act and governed records

Outcome: Beliefs publishes an immutable selected view through a recoverable governed act, with publication marker and binding revisions, exact retry, terminal reporting, and recipient admission refusal.

Acceptance evidence: After coordination/view delivery and the world-read lane, bank the coordination-contract and act-report amendments; implement request fixation, staging, exact-prefix recovery, head export, replication, restore, reveal, atomic source binding/report, orphan repair semantics, and marker-required arrival; test every recovery-table state and destination refusal; and pass the complete gates before any real publish runs.

Sources: `docs/superpowers/specs/2026-08-29-user-and-autonomy-layer-design.md` §§4.1 and 6 and §8 item 5; `docs/designs/2026-08-11-act-report-design.md`; and the root-lifecycle and log-verification designs.

Uncertainty: Destination-specific remote transport remains for Science, while this task owns only the Beliefs act and records. The prerequisite coordination and world-read outcomes are unfinished.

Initial fields: priority `2`; status `todo`; size `xl`; tags `migration`, `publication`, `coordination`.

## Deferred foreign dependencies

| Local task | Future project/outcome | Evidence | Status |
|---|---|---|---|
| `beliefs-eacbe2` | Nodes `nodes-ce28b8` (`nodes-remainder`) | The roadmap makes `contract-cut` a join after every oracle-amending lane; integrated Nodes task `nodes-ce28b8` delivers the reserved-path, recoverable-construction, and digest-ID remainder. The CLI edge resolves against the six-project portfolio registry. | reconciled |

## Verification

| Command or inspection | Result | Commit containing result |
|---|---|---|
| Portfolio-registry `tasks dep beliefs-eacbe2 --on nodes-ce28b8`, `tasks show beliefs-eacbe2`, and `tasks check` | The CLI added the verified Nodes producer as a resolved dependency; show reported the exact edge and no warnings; check returned empty errors and warnings. | Reconciliation commit (this commit) |
| Reconciliation `uv run --frozen pytest -q`, `uv run --frozen ruff check .`, `uv run --frozen pyright`, `npm test`, `npm run typecheck`, and `npm run check` | Passed: 2,724 Python tests; Ruff passed; Pyright reported 0 errors, 0 warnings, and 0 information messages; 5 TypeScript files and 101 tests passed; typecheck and Biome passed. | Reconciliation commit (this commit) |
| Reconciliation exact document coverage comparison, duplicate check, seven-section count, and `git diff --check` | All 92 denominator documents are classified exactly once; no duplicate classification exists; exactly seven required sections exist; coverage and whitespace checks produced no output. | Reconciliation commit (this commit) |
| Exact Python baseline helper in `record` mode | Kernel `7.1.11-arch1-1`: exactly 2,580 passed, 144 failed, 144 exception lines, 144 exact ext4 `CapabilityUnavailable` signatures, and 144 unique failed nodes. Control file preserved for identical-set comparison. | Base tree; control artifact outside Git |
| `uv run --frozen ruff check .` | Passed with `All checks passed!` before edits. | Base tree |
| `uv run --frozen pyright` | Passed with 0 errors, 0 warnings, 0 information messages before edits. | Base tree |
| `npm ci` | Installed the locked dependency tree; npm reported six audit findings and two ignored build-script warnings. Setup changed no tracked file. | Base tree |
| `npm test` | Passed: 5 files, 101 tests. | Base tree |
| `npm run typecheck` | Passed with no TypeScript error. | Base tree |
| `npm run check` | Passed: Biome checked 13 files with no fixes. | Base tree |
| `python/tools/check_guide.py` and `pytest -q tests/test_designs_corpus.py tests/test_check_guide.py` | Passed; focused documentation guards reported 22 passing tests. | Base tree plus documentation reconciliation |
| Required outward status search, exact document coverage comparison, seven-section count, and `git diff --check` | Outward matches reviewed; all 91 denominator documents are classified exactly once; exactly seven required sections exist; coverage and whitespace checks produced no output. | Documentation reconciliation commit `755029b748e1e2990d4548f30588a7cf2a356187` |
| Exact Python helper in `check` mode | Passed: exactly 2,580 passed and the identical 144 failed nodes, with 144 exception lines and 144 exact ext4 `CapabilityUnavailable` signatures. | Documentation reconciliation commit `755029b748e1e2990d4548f30588a7cf2a356187` |
| `uv run --frozen ruff check .` and `uv run --frozen pyright` after reconciliation | Ruff passed; Pyright reported 0 errors, 0 warnings, and 0 information messages. | Documentation reconciliation commit `755029b748e1e2990d4548f30588a7cf2a356187` |
| `npm test`, `npm run typecheck`, and `npm run check` after reconciliation | Passed: 5 files and 101 tests; TypeScript reported no error; Biome checked 13 files with no fix. | Documentation reconciliation commit `755029b748e1e2990d4548f30588a7cf2a356187` |
| Temporary-registry Familiar, Atoms, and Beliefs `tasks init`, with Beliefs initialized twice | All returned their exact prefixes and empty warning arrays; the second Beliefs initialization was idempotent. | Tasks initialization commit `1ee81bb13d03da42bce78e1fc80e0d050636ce36` |
| Pre-mutation full `tasks show beliefs-c88566` snapshot and post-mutation sorted JSON comparison | Byte-identical; the existing task's ID, timestamps, body, state, priority, size, tags, owner, dependencies, structured fields, and notes were not changed. | Tasks initialization commit `1ee81bb13d03da42bce78e1fc80e0d050636ce36` |
| Eighteen reviewed `tasks add` calls, verified through `tasks show`, plus reviewed `tasks dep` calls | All emitted IDs are recorded above; all stored fields and bodies match the reviewed ledger; every dependency resolves. At creation, the store had 19 tasks: 4 idea and 15 todo, with no inferred owner. The pending Nodes dependency is recorded separately rather than as a dangling CLI edge. | Tasks initialization commit `1ee81bb13d03da42bce78e1fc80e0d050636ce36` |
| Temporary-registry `tasks check`, `tasks prime`, and complete field/dependency audit | Passed with empty error and warning arrays, prefix `beliefs`, and exact stored bodies/dependency sets. | Tasks initialization commit `1ee81bb13d03da42bce78e1fc80e0d050636ce36` |
| Temporary-registry `tasks ready` | Passed with seven ready tasks and an empty warning array. | Tasks initialization commit `1ee81bb13d03da42bce78e1fc80e0d050636ce36` |
| Exact Python helper in `check` mode after task creation | Passed: exactly 2,580 passed and the identical 144 failed nodes, with 144 exception lines and 144 exact ext4 `CapabilityUnavailable` signatures. | Tasks initialization commit `1ee81bb13d03da42bce78e1fc80e0d050636ce36` |
| `uv run --frozen ruff check .` and `uv run --frozen pyright` after task creation | Ruff passed; Pyright reported 0 errors, 0 warnings, and 0 information messages. | Tasks initialization commit `1ee81bb13d03da42bce78e1fc80e0d050636ce36` |
| `npm test`, `npm run typecheck`, and `npm run check` after task creation | Passed: 5 files and 101 tests; TypeScript reported no error; Biome checked 13 files with no fix. | Tasks initialization commit `1ee81bb13d03da42bce78e1fc80e0d050636ce36` |
| Initial integration | Stable `main` was fast-forwarded through the documentation and Tasks commits to `1ee81bb13d03da42bce78e1fc80e0d050636ce36`. | Stable `main` |
| Atoms stable inspection | Clean at `914acb66e796f8691b7cc10bb7c28daa54dddfbf`, with the host Linux 7.1.11 tuple certified. | Atoms stable `main` |
| Stable `uv run --frozen pytest -q` after Atoms certification | Passed: exactly 2,724 tests in 413.46 seconds. This all-green result follows the committed Atoms recertification; it preserves the earlier 2,580-pass/144-fail evidence as the prior fail-closed state. | Stable `main` at `1ee81bb13d03da42bce78e1fc80e0d050636ce36` |
| Stable `uv run --frozen ruff check .` and `uv run --frozen pyright` | Ruff passed with `All checks passed!`; Pyright reported 0 errors and 0 warnings. | Stable `main` at `1ee81bb13d03da42bce78e1fc80e0d050636ce36` |
| Stable `npm test`, `npm run typecheck`, and `npm run check` | Passed: 5 files and 101 tests; TypeScript reported no error; Biome passed. | Stable `main` at `1ee81bb13d03da42bce78e1fc80e0d050636ce36` |
| Canonical Beliefs registration from the stable repository root, repeated twice | Both normal `tasks init` calls returned prefix `beliefs`; the second registration was idempotent. | Canonical Tasks registry |
| Original canonical `tasks check`, `tasks prime`, and `tasks ready` snapshot | Check returned no errors or warnings; prime reported prefix `beliefs`, 4 idea, 14 todo, and 1 doing; ready returned six tasks and no warnings. | Canonical Tasks registry immediately after registration |
| Stable `beliefs-c88566` preservation | Post-integration user activity changed the task to `doing`, owner `main`, updated `2026-08-31T09:25:24Z`; canonical commands preserved working-tree blob `9abf319cfb58704a5bee937d3193831c79ff4972` byte-for-byte. User commit `0415208b1a747697fa3961ad2ebad6a3919ceb70` now tracks that same blob. This activity is not part of the migration. | Stable `main` after the intervening user commit |
| Intervening post-integration user commit | Added `beliefs-5f2752` and `beliefs-abf8e8`, updated `beliefs-bc3aff`, and committed the prior `beliefs-c88566` start. The migration did not modify those task records. | Stable `main` at `0415208b1a747697fa3961ad2ebad6a3919ceb70` |
| Fresh canonical `tasks check`, `tasks prime`, and `tasks ready` after the user commit | Check returned no errors or warnings; prime reported prefix `beliefs`, 5 idea, 15 todo, and 1 doing; ready returned seven tasks and no warnings. | Canonical Tasks registry at stable `main` `0415208b1a747697fa3961ad2ebad6a3919ceb70` |
| Stable working-tree inspection after the user commit and fresh Tasks checks | Clean. | Stable `main` at `0415208b1a747697fa3961ad2ebad6a3919ceb70` |
| Finalization exact document coverage comparison, seven-section count, and `git diff --check` | All 91 denominator documents remained classified exactly once; exactly seven required sections remained; coverage and whitespace checks produced no output. | Ledger-finalization commit `737d0b245bc77e8b78775ea821b776a17c90d29b` |
