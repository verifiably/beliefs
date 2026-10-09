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
of `beliefs` (abf8e8), becomes live only when another component itself consumes
the coordination contract, or a distinct constraint regime is documented. A
science adapter that delegates writes to `tasks` does neither: `tasks` never
reads the contract (§3). The outcome wanted is one decision on
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

**Research tasks and dev tasks: one system or two.** Science's coordination
`task` is a governed record in a world's corpus. It is attributed, belief-inert,
and reaches other worlds only through the corpus's own publication. A `tasks`
record is a markdown file beside a checkout, outside both. Much of what makes
`tasks` useful is behaviour rather than storage: the derived ready queue,
claims and liveness, notes as attributed acts, shelving with a wake condition,
and the scope and curate passes. Four ways to share it:

1. **Two systems, joined by opaque references (lean).** Port a `tasks`
   behaviour into science's coordination kinds only when a science measurement
   asks for it, the rule the coordination command set already applies to
   `topic`, `theme` and `note` (its §11). `tasks-96b215` may give a read-only
   bridge: if nodes reads an unchanged task record, science can index dev tasks
   with no dependency in either direction. The cost is duplication, and porting
   on measured need keeps it to what is actually used.
2. **Bring `tasks` into `verifiably`.** The twenty-odd projects that run `tasks`
   daily would then follow verifiably's release cadence and
   governance. The dependency points the wrong way.
3. **An external dependency (ff2529).** Science's task writes shell out to
   `tasks` through a versioned coordination-contract amendment. This reverses
   part of what landed on 2026-09-24, and it moves a world's tasks out of its
   corpus. Science still consumes the contract and `tasks` never reads it, so
   this is not a second consumer and does not wake abf8e8.
4. **A common core both build on.** `tasks` is Rust and science is Python, so
   the core is either cross-language or duplicated anyway. Its home sits
   outside one of the two boundaries whichever repository holds it. This is
   the most work, for the least-measured need.

**Decided 2026-10-09 by the user: 1, two systems.** 2 and 4 are rejected:
they put a cross-boundary dependency in place before any measurement asks for
one. 3 is rejected with them, so beliefs-ff2529 is dropped. `tasks-96b215`
now informs only the read-only bridge in alternative 1.

**The stack-less profile (44c0fd)** is shelved by the user's call on
2026-10-09. One project uses the pattern, and its home is revisited when a
second project builds or asks for it.

## 5. Unanswered questions

| Question | Who or what answers it |
|---|---|
| Can the nodes standard read an unchanged task record, relations included? | `tasks-96b215`. Its answer bears only on alternative 1's read-only bridge. |
| Which stack-less hypothesis/evidence/question fields have no home in coordination v3? | beliefs-bcfa20, shelved with 44c0fd |
| Should research tasks and dev tasks be one system at all? | Answered 2026-10-09: no, two systems (§4, alternative 1). |
| Where would a stack-less profile live: `beliefs`, a nodes example profile, or its own repository? | Deferred. The user shelved it until a second project builds or asks for the pattern. |

## 6. Proposed decomposition

- Goal beliefs-614364 closed 2026-10-09 on the decision. The shelved ideas stand alone, with beliefs-bcfa20 under beliefs-44c0fd.
- beliefs-ff2529 is dropped by the 2026-10-09 decision. `tasks-96b215`
  (existing, `tasks` project) no longer wakes it. If its finding shows nodes
  reads an unchanged task record, the bridge is filed then as a science idea.
- beliefs-44c0fd and its research child beliefs-bcfa20 are shelved until a
  second project builds or asks for the hand-kept hypothesis/evidence/question
  pattern. bcfa20 is the first step when they wake.
- beliefs-abf8e8 is shelved until another component itself consumes the
  coordination contract (not through science), or a distinct constraint regime
  is documented, such as a domain pack whose owner and release cadence differ
  from `beliefs`'.
- No design task: the decision needs none.

(Revised 2026-10-09 after a review of this brief: §1 and §4's alternative 3 no
longer treat delegated writes as a second consumer, and §4 records the user's
answers on one system and on the stack-less profile.)
