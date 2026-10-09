# Coordination outside the kernel — brief

**Date:** 2026-10-09. **Ideas:** beliefs-ff2529, beliefs-44c0fd, beliefs-abf8e8.

## 1. Problem

Coordination is recorded in three places today. `science` mints `project`,
`question`, `hypothesis`, `task` and `decision` records into a world's corpus.
The `tasks` CLI keeps every repository's development work as markdown records.
Projects with no science stack keep hypotheses, evidence and open questions as
hand-written markdown. Two ideas ask that these converge: realize the
coordination `task` kind through `tasks` records (ff2529), and give stack-less
projects a small hypothesis/evidence/question profile that `beliefs` could later
subsume (44c0fd). A third, splitting `contracts/coordination` and `domains/` out
of `beliefs` (abf8e8), becomes live only if either convergence gives the
coordination contract a second consumer. The outcome wanted is one decision on
whether the three stay separate, joined by opaque references, or converge, and
in which direction.

## 2. Current behaviour and evidence

- **The kernel's coordination kinds are in use, not proposed.** Coordination
  contract v3 (`python/src/beliefs/contracts/coordination/v3/CONTRACT.yaml`)
  declares `project`, `question`, `hypothesis`, `topic`, `theme`, `task`,
  `decision`, `note`, `publication` and `publication-binding`. Its `hypothesis`
  carries `name`, `body`, `author`, `at` and `query` and nothing else: no kill
  condition and no refuted-with-reason state, and no `evidence` kind at all.
- **Science mints them.** Science's coordination command set
  (`science` `docs/specs/2026-09-24-coordination-command-set-design.md`, parts
  1–3 implemented 2026-09-24 to 2026-09-30) adds commands that mint and revise
  `project`, `question`, `hypothesis`, `task` and `decision` records in the
  corpus. ff2529 (filed 2026-09-16) predates this. Its "not minting task content
  in the corpus a second time" now describes the alternative to what landed,
  not the status quo.
- **The stack-less pattern is still hand-kept and growing.** The project 44c0fd
  cites still keeps its hypotheses, evidence and open-questions files by hand,
  and they have grown to roughly 340, 1,100 and 460 lines. Each hypothesis names
  the observation that would kill it, and each evidence entry names a
  reproducing command. That is one observed consumer. "The next work project will
  build it again" is projected.
- **The format question is already a research task.** `tasks-96b215` (todo,
  P2/s/mid/direct, in the `tasks` project) asks whether the nodes on-disk
  standard reads an unchanged task record. On completion it wakes ff2529.
- **No second consumer of a split exists.** Ledger §5 and the user/autonomy
  design §3.2 split a distribution only on an observed second consumer. The
  coordination contract's one consumer is `science`. `domains/` holds `biology`
  alone, and natural-systems defers its pack's route until the pack exists
  (`ns-437ab5`, done; beliefs-f484a7, shelved).

## 3. Constraints

- `tasks` never learns that `beliefs` exists. References from a task to science
  records stay opaque, as `source` is today (ff2529; the rule quick-add follows
  between `tasks` and mindful).
- Hypotheses do not become a `tasks` kind. That is the proto-science path the
  user/autonomy design §1 rejects.
- Coordination records are governed and belief-inert (user/autonomy §4.1). The
  queue is derived and never stored (§4.4). Autonomy reaches science only
  through commands as tools (§7.4).
- Profiles live downstream of `nodes` (nodes README). A stack-less project
  takes on no science dependency.
- Splits are drawn on observed consumers only (ledger §5).
- This repository is public. Material from a work project enters it only as
  structure (field names, required properties), never as content.

## 4. Alternatives

1. **Stay separate, joined by opaque references.** Science's coordination kinds
   serve research inside a world. `tasks` serves development work. Stack-less
   projects keep markdown. Costs nothing, but the hand-kept pattern gets rebuilt
   per project, and a research `task` and a dev task stay two systems.
2. **A stack-less profile first, subsumed later (44c0fd).** A small nodes
   profile with `hypothesis`, `evidence` and `question` kinds, and the kill
   condition and reproducing command required by the profile's check. Science's
   coordination contract later admits these as a lite tier. This needs the
   contract's `hypothesis` to grow the kill condition, or the profile to map onto
   it lossily.
3. **Realize the coordination `task` through `tasks` records (ff2529).** A
   versioned coordination-contract amendment: science's task writes shell out to
   `tasks`, and the corpus-write adapter records the act with the task id. This
   reverses part of what landed on 2026-09-24 and makes `tasks` the
   coordination contract's second realization, which is the trigger abf8e8
   waits for.

**Current lean:** 1 for `task` until `tasks-96b215` reports, because
alternative 3 now means unwinding landed science work and needs that format
answer first. Take 2 only if the field mapping (below) shows the kill condition
and reproducing command have no home in the v3 kinds, and only once a second
project actually asks for it.

## 5. Unanswered questions

| Question | Who or what answers it |
|---|---|
| Can the nodes standard read an unchanged task record, relations included? | `tasks-96b215` |
| Which stack-less hypothesis/evidence/question fields have no home in coordination v3? | beliefs-bcfa20 |
| Should research tasks and dev tasks be one system at all? | The user. It is a scope choice that no measurement settles. |
| Where would a stack-less profile live: `beliefs`, a nodes example profile, or its own repository? | The user, after beliefs-bcfa20 |

## 6. Proposed decomposition

- Goal beliefs-614364 owns this cluster.
- `tasks-96b215` (existing, `tasks` project) → wakes beliefs-ff2529.
- beliefs-bcfa20 (research, child of the goal) → wakes beliefs-44c0fd.
- beliefs-abf8e8 is shelved until a second consumer is observed: `tasks` under
  alternative 3, or a domain pack owned outside `beliefs`.
- No design task yet. One follows only if the user picks alternative 2 or 3.
