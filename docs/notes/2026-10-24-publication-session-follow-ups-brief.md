# Publication follow-ups after science commons 1a

## Problem

Complete the kernel's session boundary for retiring a shared publication and
recovering a publish whose original session will never return. Two other ideas
ask about epoch coverage and execution locators; the former already has an
explicit contract, and the latter duplicates an older task.

## Current behaviour and evidence

Read on main at `802286e`, 2026-10-24; no suites run during this scope pass.
Session doors landed at `b923277` (`beliefs-f24fe9`). Science commons 1a's
source record `sci-13050a` reports its merge at `c8a2cd7`; its linked spec's
sections 5, 10 and 11 were read through `tasks doc`.

- `session/writer.py` under `python/src/beliefs/` exposes restore, admission,
  publish and resume doors, but no retirement door. `record_sharing` accepts
  only `bound` and `mounted`. `world/registry.py:World._terminal` requires
  registry authority and returns a `StatusRecord` carrying the actor. An
  identical status by that actor is idempotent; another actor's terminal
  record refuses. `session/ledger.py:SharingLine` has no status-record field.
- `publish.py:resume_publish` checks the intent's actor before transport or
  operation cleanup. A marked unfinished remote attempt blocks its
  `(view, destination)` pair. The sharing-door design's decision 12 expressly
  defers succession; the local-publish design's decision 9 and
  `test_resume_refuses_another_actor_and_another_profile_writing_nothing`
  preserve that refusal.
- `world/epoch.py:_declared_coverage` explicitly forbids substituting the
  registry's live set. `test_world_build.py`'s
  `test_preflight_pins_a_sorted_carrier_mapping_and_never_substitutes_live_ids`
  admits three corpora and captures only two. `world/view.py` reports absence
  within that coverage; `publish.py:publication_preview` uses that view.
  By contrast, `world/live.py:_coverage` reports missing live admissions.
  The packaging design sections 5 and 5.4 (`15b6e08`) explain the bound.
  Thus `beliefs-79d2ce` describes permitted behaviour, not a missing refusal.
  "Every epoch" is too broad: a later build can explicitly cover the corpus
  once its carrier is configured.
- `beliefs-6d6bb6` duplicates shelved `beliefs-42d201`. Commons sections 5
  and 7.2 already place locators out of band in milestone 1 and in the
  catalog's execution claim in milestone 2, with recipe validation as the
  check. The older task's 1a wake condition is now met; it was related
  context, not a member processed by this pass.

## Constraints

Retirement is irreversible. Science owns keep/dependency/supersession policy;
the kernel owns the authorized act and its evidence. Existing
`beliefs-918fd2` owns overlapping-publication reads and already blocks
milestone 1b through `beliefs-81367e`; do not duplicate that design.

Keep the sharing design's liveness, currency, evidence-before-effect checks
and terminal ledger-failure behaviour. Recovery must preserve the original
intent and identify the successor honestly. Frozen cut bodies stay intact;
any changed guarantee is superseded by citation. A new cut carries both
AGENTS.md obligations (the sole atoms importer and the acceptance inventory).
No shared resource names are declared in this project's task configuration.

## Alternatives

1. **Lean: design each missing boundary separately.** Compose retirement over
   `World.retire`, and require explicit authority and recorded succession for
   recovery. Keep declared epoch coverage and the existing locator task.
2. **Allow any same-world actor to resume.** Less ceremony, but it erases the
   reason for the frozen actor refusal and does not establish who delegated
   the attempt. Reject this as an implementation default.
3. **Defer both doors to surface workarounds.** This leaves milestone 1b
   without ledgered retirement and marked attempts stranded. Keep these
   limitations visible until the designs land, not as the target behaviour.

## Unanswered questions

- Retirement designer: how does `retire(corpus_id, *, evidence)` bind the pin
  to the target without taking the existing doors' root and observers?
  How is its status record evidenced in the current sharing schema, and
  what happens after a committed retirement but failed ledger append,
  including a retry under another actor? Settle schema and cut requirements.
- Recovery designer: who can authorize succession, how is that grant bound
  to one intent, and which actor each resulting record names? Cover attempts
  before and after the transport mark, concurrent/stale sessions and crashes.
- A future explicit pass on `beliefs-42d201` can use 1a's outcome to decide
  whether publisher-stated locators add anything to catalog claims. This
  pass neither answers that policy question nor unshelves the task.

## Proposed decomposition

- `beliefs-182296` groups this follow-up work.
- `beliefs-c0d952` designs ledgered retirement (priority 2, medium, high
  complexity, planned); `beliefs-a989fb` waits on it.
- `beliefs-8abd52` designs successor-actor recovery (priority 2, large, high
  complexity, planned); `beliefs-b427db` waits on it.

Both waiting members remain ideas until those decisions are settled. Each
design records its result here and wakes its idea with a finding note.

Approved and applied after the scope pass, 2026-10-24: `beliefs-79d2ce`
dropped against the existing declared-coverage contract; `beliefs-6d6bb6`
dropped in favor of `beliefs-42d201`. The canonical locator task remains
shelved.

## Retirement design decision (beliefs-c0d952, 2026-10-29)

Approved at revision 3 (`578a014`) after three review rounds:
`../superpowers/specs/2026-10-29-publication-retirement-door-design.md`. It answers the
retirement designer's questions above:

- **Binding without new arguments: not attempted.** The door is
  `ScopedWriter.retire(root, observers, *, evidence) -> SharingLine` and binds the
  evidence exactly as `admit_publication` does. The registry records nothing about a
  publication but its corpus id, so a corpus-id-only door could bind nothing else.
- **Status-record evidence: the line's `corpus`.** A world holds one terminal status per
  corpus, so the eleven-field `sharing` line is unchanged. The verdict is `retired` when
  the door wrote the status and `already-retired` when it found one.
- **Recovery and cross-actor retry: accepted.** A ledger failure ends the session, so
  every retry is another actor's. The door reads the registry before acting and
  re-ledgers any actor's `retired` status with no second act. A flush or fsync failure
  can leave the first line on disk, so readers accept a `retired` and an
  `already-retired` line for one status.
- **Scope of the target: self-replicas only.** A corpus that was not admitted as
  `ReplicaOf` itself refuses `StatusTargetUnknown`; a departed corpus refuses
  `StatusTerminal`. `record_sharing` keeps refusing `retired`.
- **Schema and cut: neither.** The ledger schema is unchanged and no frozen guarantee
  changes. Writers stay single across processes.

Implementation handoff: beliefs-a989fb builds the door in its own lane, as a `direct`
task against the design. It also lands the sharing-design amendment, the adoption-ledger
line and the `docs/guide/open-questions.md` correction, each with the code that makes it
true. Science's Task 13 adopts the signature and the two verdicts (design §6).
