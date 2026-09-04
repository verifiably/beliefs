# Write permits — design (the `write-permits` slice)

**Date:** 2026-09-04
**Status:** implemented and discharged 2026-09-04; conformance cut 17 (16 in
the frozen text, renumbered by §14) froze before implementation at `c2f87b3`
and its 8 selected + 1 labeled units passed through 24 sabotage arms after the
current-tree prefix of §13.2. Results:
`../plans/2026-09-04-conformance-cut-17-results.md`.
**Scope:** the `beliefs` half of the command framework's write boundary — the
user and autonomy layer design
(`../superpowers/specs/2026-08-29-user-and-autonomy-layer-design.md`) §5.2 and
§8 item 2, as the `science` repository's command-framework design §4 pins it:
the closed act-family enumeration, the closed `KIND_ACTS` route map, the
`WritePermit` value, the `Authority` that binds a permit and an actor at every
construction seam, the `RequiredCapabilities` value `science` compiles a
declaration to, `PermitExceeded`, the check at every write entry point before
any effect, the removal of every caller-supplied `actor` from those entry
points, and the static inventory that holds the set of entry points closed.
No store change, no `atoms` or `nodes` change, no new record kind, no
amendment to any contract.
**Inherits:** the layer design §5.2 (the rule text — every write entry point
takes a permit checked against what is emitted; the actor stops being
caller-supplied at the writer boundary) and the `science` command-framework
design §3.3, §4.1–§4.4 and §6.3 (the contract: value names, constructor
names, the entry points named as binding seams, the families no write class
maps to, the refusal envelope). Where those documents decide a point this one
cites it. The act-report design (`2026-08-11-act-report-design.md`) §3 and
the family-adapters design (`2026-08-19-family-adapters-design.md`) own the
intent and the four corpus families this document binds; the holdings design
(`2026-08-24-world-index-holdings-design.md`) owns the act context; the
run-confinement design (`2026-08-30-run-confinement-design.md`) owns the run
boundary; the substrate design's S8 (`2026-08-02-substrate-consolidation-design.md`)
and cut 8's declarations over the composition surface own the static-boundary
pattern §5 reuses. Each is amended only by the dated notes §10 lists.
**Out of scope:** the writer session, its ledger, `WriterSession.scoped`, the
`corpus-write` operation kind and its act-report amendment (`beliefs-afbbff`,
the session task, which consumes §3's values unchanged); `publish` and its
act family (sub-project 5); the actor sandbox and endpoint handle
(sub-project 6); any `science` code.

**Sources, read at design time:** `python/src/beliefs/corpus.py`,
`boundary.py`, `replay.py`, `runrecord.py`, `report.py`, `stored.py`,
`coordination.py`, `root.py`, `errors.py`, `holdings/boundary.py`,
`holdings/seam.py`, `world/registry.py`, `world/epoch.py`, `world/rules.py`,
`world/anchors.py`, `world/verify.py`; `python/tests/test_capability_boundary.py`;
the `science` repository's `docs/specs/2026-08-31-command-framework-design.md`
and its plan's Task 12 *Consumes* block, which names the values this
document exports.

---

## 1. Problem

Every durable write in `beliefs` already funnels through two primitives: the
`OperationPort` (`append_intent`, `execute`, `execute_fulfilling`) for corpus
chains and the world `WritePlanExecutor` for registry, epoch, rule and anchor
files. Both are certified and both are unguarded by *authority*: nothing says
which kinds a holder may mint or which acts it may open, and every entry
point that appends an intent — `import_bundle`, the run boundary, the holdings
acts, `World.admit`, epoch deletion, anchoring, admission — takes `actor` as
an ordinary keyword the caller spells. `CorpusWriter.__init__` is public, so a
writer can be constructed around the composition root with any port at all.

The layer design's guardrail story rests on the opposite: a command's body
may invoke a broader writer than its declaration claims, so the kernel — not
the declaration — refuses the overreach, and the actor is fixed where the
request stops being trusted. Sub-project 6's sandbox will make that boundary
mechanical; this slice makes it *exist*. Until it does, `science`'s Task 12
cannot open a session, and the interactive path has no permit to exercise
daily.

## 2. Decisions

1. **Two closed dimensions, both owned here.** A permit is a frozenset of
   record kinds and a frozenset over a closed enumeration of act families:
   `corpus-write`, `run`, `holdings`, `registry`, `epoch`, `lifecycle`.
   `publish` is not a member; sub-project 5 adds it by amendment, the same
   amendment that adds its operation kind.
2. **`KIND_ACTS` is a literal, complete over today's 21 kinds, and validation
   data only** (command-framework §4.1). The declaration selects a route; the
   map says whether the selection is admissible. No requirement is derived by
   union.
3. **Authority binds once, at construction, with no default.** The frozen
   value `Authority(permit, actor)` enters at `open_corpus`, `open_world`, the
   `OperationPort`, the holdings `ActContext` and the root lifecycle acts, and
   nowhere else. Every in-`beliefs` caller states it; a writer and a port that
   disagree refuse construction.
4. **The actor is bound with the permit, now.** Every write entry point loses
   its `actor` keyword and reads the bound actor. The session task then only
   mints a session identity and binds it. Signatures change once.
5. **The check lives in the entry point, before its first effect.** Each
   inventoried definition calls `authority.require(family, kinds)` before it
   appends an intent or submits a plan, and a static test holds the inventory
   closed in both directions (§5). Port-level inspection is rejected (§11).
6. **A permit violation is refused with nothing written.** On the run
   boundary that means no intent and no refusal report — minting the report
   is itself a write the permit did not cover. Elsewhere `PermitExceeded`
   propagates as raised, a `WriteRefused` subclass with structured fields.
7. **`RequiredCapabilities` compiles to a permit, and coverage is one
   function.** `permit_covers(ceiling, required)` is what the session task's
   `scoped` calls; the requirement is the invocation's own ceiling. This
   document ships the value and the function; the session is the consumer.
8. **Write permits open the `authority` lane and land before
   `consolidate-family`.** The diff is additive per seam; the later merge
   resolves toward it, and the static inventory makes that lane's new acts
   fail until they take a permit.

## 3. The values — `beliefs/permit.py`

### 3.1 Act families

```python
ActFamily = Literal["corpus-write", "run", "holdings", "registry", "epoch", "lifecycle"]
ACT_FAMILIES: frozenset[str]
COMMAND_REACHABLE_FAMILIES = frozenset({"corpus-write", "run", "holdings"})
```

The second set is command-framework §4.4 as data: `registry`, `epoch` and
`lifecycle` write without corpus-chain evidence and no write class maps to
them. `RequiredCapabilities` (§3.5) can never name one.

### 3.2 `KIND_ACTS`

A frozen mapping from every mintable kind to the families admissible as its
minting route. It is exported read-only and a test holds its key set equal to
`stored.WORLD_KINDS ∪ coordination.COORDINATION_KINDS`, so a kind added to
either set without a route fails the suite.

| kind | admissible routes | why |
|---|---|---|
| `proposition`, `source-assertion`, `assessment`, `analysis-spec`, `source`, `verification`, `instrument-certification`, `coreference-attestation`, `retraction` | `{corpus-write}` | minted only through `CorpusWriter.add` and the corpus families |
| `run` | `{run, corpus-write}` | the run boundary publishes it fulfilling a run intent; the add path can mint a `run` record directly (cut 15's R23 arm does) |
| `dataset` | `{corpus-write}` | `publication_plan` mints only the `run` record; the dataset it produces is a relation target, never a record the boundary writes |
| `act-report` | `{corpus-write, run}` | `import_bundle` and the run boundary each close their intent with one; the holdings acts fulfill theirs with a `holdings-observation` and mint no report |
| `holdings-observation` | `{holdings}` | minted only by the four holdings acts through the store seam |
| `project`, `question`, `hypothesis`, `topic`, `theme`, `task`, `decision`, `note` | `{corpus-write}` | the coordination family door is a corpus write (command-framework §3.3) |

Domain kinds are absent because no domain pack exists. The domain-boundary
design owes this table an amendment on the first kind it mints; until then
the completeness test above is what refuses a silent addition.
`verification`'s single route is the state of the tree: the open
`verification-publication` boundary may add `run` when it lands.

### 3.3 `WritePermit`

```python
@dataclass(frozen=True)
class WritePermit:
    kinds: frozenset[str]          # ⊆ KIND_ACTS.keys()
    act_families: frozenset[str]   # ⊆ ACT_FAMILIES

    @classmethod
    def full(cls) -> "WritePermit": ...   # every kind, every family
```

Construction refuses a kind or family outside the closed sets with
`ValueError`, and refuses anything that is not a `frozenset` of exact
strings with `TypeError`. `full()` is the launcher constructors' permit
(command-framework §5.1) and the test helper's; it is the only convenience
constructor on purpose — a narrower permit is spelled out.

### 3.4 `Authority`

```python
@dataclass(frozen=True)
class Authority:
    permit: WritePermit
    actor: str

    def require(self, family: str, kinds: Iterable[str] = ()) -> None: ...
```

The actor rule is the one `world/registry._require_actor`, `report.py`,
`holdings/boundary.py`, `stored.py` and `world/anchors.py` each restate
today — an exact `str`, non-empty, `v1`-encodable — single-homed here; the
five restatements import it. `require` raises `PermitExceeded` (§3.6) naming
the family when the permit lacks it, else the first kind, in the caller's
order, that the permit lacks. It has no other outcome: no return value, no
logging, no partial grant.

### 3.5 `RequiredCapabilities` and coverage

```python
@dataclass(frozen=True)
class RequiredCapabilities:
    permit: WritePermit

    @classmethod
    def none(cls): ...                                   # empty, empty
    @classmethod
    def coordination(cls): ...                           # COORDINATION_KINDS, {corpus-write}
    @classmethod
    def for_kinds(cls, kinds: Iterable[str], routes: Mapping[str, str]): ...
    @classmethod
    def publishes(cls): ...                              # raises today

def permit_covers(ceiling: WritePermit, required: RequiredCapabilities) -> bool: ...
```

`for_kinds` is command-framework §3.3 as a function: every kind must exist in
`KIND_ACTS`; a route-ambiguous kind must appear in `routes`; a single-route
kind may be omitted and its route derived; a `routes` key outside `kinds`, or
a route `KIND_ACTS` does not admit for its kind, raises `ValueError`. The
resulting families are exactly the selected routes. `publishes()` raises
`ValueError("publish is not an act family")` until sub-project 5 amends §3.1
— which is how the `science` build learns it cannot ship a `publishes`-class
command yet, at build time rather than at the first act.

`permit_covers` is subset inclusion on both dimensions and nothing else. The
full permit covers every constructible requirement (a test enumerates the
constructors); an empty requirement is covered by every permit.

### 3.6 `PermitExceeded`

In `errors.py`, beside the other `WriteRefused` subclasses:

```python
class PermitExceeded(WriteRefused):
    requirement: PermitFact    # the family or kind the act needed
    capability: PermitSummary  # the permit's kinds and families, sorted tuples
```

`PermitFact` is a frozen `(dimension, name)` pair — `("family", "run")` or
`("kind", "source")` — and `PermitSummary` a frozen pair of sorted tuples.
Both are plain data so the `science` dispatcher can place them in the
refusal envelope's `data` without reaching into the exception. The message is
prefix-stable: `permit exceeded: <dimension> <name> is not permitted`.

Beside it, `ActorMismatch(WriteRefused)`: raised by `retract` when the
retraction facet's `actor` is not the bound one, and by `add` when a `run`
record's closure names another actor in its occurrence (§4.2). It is not a
permit refusal — the permit may well cover the kind — and so is its own
class.

## 4. Binding seams and the entry-point inventory

### 4.1 Where authority enters

| seam | signature after this slice | binds to |
|---|---|---|
| `root.open_corpus` | `(corpus_root, *, authority, coordination_resolver=None)` | the `DurableOperationPort` and the `CorpusWriter`, one value for both |
| `corpus.CorpusWriter.__init__` | `(root, executor_factory, *, authority, operation_port=None, coordination_resolver=None)` | the writer; a port whose `authority` differs raises `ValueError` at construction |
| `root.DurableOperationPort.__init__` | `(root, *, backend, storage, metadata_root, authority)` | the port; `OperationPort` (the protocol in `runrecord.py`) gains a read-only `authority` property, and every test port implements it |
| `root.open_world` | `(config, *, authority)` | the `World`, as `world.authority` |
| `holdings.boundary.ActContext` | `(observer_root, store_root, observer, instrument, authority, seam)` | the four holdings acts |
| `root.init_corpus_root`, `init_world_root`, `init_store_root`, `fork_corpus`, `fork_store`, `replicate_root`, `restore_root`, `migrate_root_to_lifecycle_v3` | each gains `*, authority` | the lifecycle acts |

There is no default at any seam. A caller that has no permit to state has no
business writing, and a test that wants a full one imports the helper of
§9.2.

### 4.2 The inventory

Every definition below reaches a write primitive and therefore calls
`authority.require(<family>, <kinds>)` before it. The kinds column is what the
definition actually emits — judged from the record or bundle in hand, never
from a declaration.

| enclosing definition | family | kinds required | actor today → after |
|---|---|---|---|
| `CorpusWriter.add` | `corpus-write` | `node.kind` | none → a `run` record carrying the run-closure facet is decoded (`decode_run_closure`) and its `occurrence.actor` must equal the bound actor, else `ActorMismatch`; `add` already refuses every other actor-bearing kind (`act-report`, `retraction`, `holdings-observation`, the coordination kinds), so no other record through `add` names an actor |
| `CorpusWriter.retract` | `corpus-write` | `retraction` | authored into the retraction facet → the facet's `actor` must equal the bound actor or the write refuses (`ActorMismatch`, a `WriteRefused`) |
| `CorpusWriter.supersede`, `CorpusWriter.revise` | `corpus-write` | `proposition` | none → none |
| `CorpusWriter.mint_coordination`, `CorpusWriter.revise_coordination` | `corpus-write` | the coordination kind | none → none |
| `CorpusWriter.import_bundle` | `corpus-write` | every member's kind, then `act-report` | `actor` keyword → removed; the intent's actor is the bound one. Members are stored verbatim: an imported run closure or retraction naming a foreign actor is **provenance**, attributed to the importer by the intent and never rewritten — the one deliberate route for a record whose actor is not the bound one |
| `CorpusWriter.adopt_manifest` | `lifecycle` | — | none → none |
| `boundary.execute_assessment_run` | `run` | `run`, `act-report` | `actor` keyword → removed; read from `port.authority` |
| `boundary.execute_production_run` | `run` | `run`, `act-report` | same |
| `holdings.boundary.recheck`, `write`, `delete`, `move`, and the private helpers `_append` and `_publish` they call | `holdings` | `holdings-observation` | `ctx.actor` → `ctx.authority.actor` |
| `world.registry._locked_admit` (serving `World.admit` and `root.admit_arrival`), `World._terminal` (serving `retire` and `depart`) | `registry` | — | `actor` keywords → removed; `world.authority.actor` |
| `world.anchors._anchor_heads` (serving `root.anchor_heads`) | `registry` | — | same |
| `world.epoch.build_epoch`, `world.epoch.delete_epoch` | `epoch` | — | `delete_epoch`'s keyword → removed |
| `world.rules.install_rule_binding`, `remove_rule_binding` (and `root.install_shipped_world_rules` through the former) | `epoch` | — | none → none |
| `root.init_corpus_root`, `init_world_root`, `init_store_root`, `fork_corpus`, `fork_store`, `_fork_resume` (the pending-fork resume both fork acts reach), `replicate_root`, `restore_root.grant` (the nested closure `restore_root` hands to `_restore_root`, which makes the grant call — `restore_root` itself calls no primitive and is not inventoried), `migrate_root_to_lifecycle_v3` | `lifecycle` | — | none → none; `init_world_root`'s `mkdir` moves after its `require` (§5 arm 2) |

`replay.replay` re-enters the two run entry points and calls no primitive
itself; it loses its `actor` keyword and is not inventoried. `root.audit_log`
writes nothing (verify §6.1) and keeps `actor` as the label its report
carries; it is a read and is not inventoried. `Occurrence.actor`,
`AdmissionRecord.actor`, `StatusRecord.actor`, `LogHeadRecord.actor`,
`EpochDeletionReport.actor` and the act-report's `actor` are *values* that
record who acted; they keep their fields and are populated from the bound
authority by the definitions above.

### 4.3 The primitives, and the call graph

The inventory is closed against this set of calls, by attribute name on any
receiver: `append_intent`, `execute`, `execute_fulfilling`,
`publish_fulfilling`, `store_write`, `store_delete`, `store_move`, `add` on a
`_corpus` receiver, `register_root`, and the five engine callbacks `root.py`
binds under private names — `_replicate_root_callback`,
`_fork_root_callback`, `_resume_fork_root_callback`,
`_grant_read_serviceability_callback` (restore's grant) and
`_migrate_root_to_lifecycle_v3_callback`. The bodies that *implement* a
primitive are excluded by exact name — `DurableOperationPort.*`,
`DurableExecutor.*`, `_mapped_submit.submit`, and the `_store_*` seam
implementations in `root.py` — and that exclusion list is compared for
equality, never containment, so a fifth implementation is a failure.

**The rule attaches to the definition that makes the call, public or
private.** The inventory is not a list of public names: it is the set of
enclosing definitions in which a primitive call appears. A private helper
that calls a primitive — `holdings.boundary._append`, `_publish`,
`world.registry._locked_admit`, `World._terminal`, `world.anchors._anchor_heads`
— is inventoried under its own name and requires before its own call, and
so is a **nested** definition, under its qualified name (`restore_root.grant`);
public callers are inventoried only where they call a primitive themselves
(`write`, `delete` and `move` call `store_*` directly and so appear beside
their helpers). A definition that only calls other inventoried definitions —
`replay.replay`, `root.admit_arrival`, `root.anchor_heads`,
`root.install_shipped_world_rules` — is not inventoried; the authority it
passes down is required where the write happens. A redundant `require` on a
path that requires twice is harmless and is not a finding.

## 5. The static boundary — `tests/test_permit_boundary.py`

The S8 pattern, applied to authority. Each arm is a static AST predicate over
the **imported** package (`Path(beliefs.__file__)`), so a sabotage harness on
`PYTHONPATH` is what gets inspected; each is asserted in both directions; a
synthetic offender proves the check can speak and a synthetic satisfied module
proves it can be satisfied; every allowlist is compared by equality.

1. **The inventory is closed.** `WRITE_ENTRY_POINTS`, a frozen map from
   enclosing qualified definition to family, equals the set of definitions
   the AST finds calling a §4.3 primitive, less the §4.3 implementations. A
   caller missing from the map fails; a map entry that calls no primitive
   fails.
2. **Every entry point requires before it writes, unconditionally.** Each
   inventoried definition contains a call spelled
   `<receiver>.require(<family literal>, …)` whose family equals the map's,
   and the statement carrying it is a **top-level statement of the
   definition's body** — its parent is the body list, not an `if`, `try`,
   `with`, `for` or `match` — **and is that call and nothing else**: an
   `Expr` whose value is the `require` `Call` directly, so
   `flag and authority.require(...)`, a `require` inside a conditional
   expression, a lambda, or a comprehension is not a check. **One exact
   alternative shape exists, for the two `run`-family entry points only**
   (§6's translation): a top-level `Try` whose body is exactly the one
   `Expr(Call(require))` statement, with exactly one handler,
   `except PermitExceeded as <name>`, whose body is exactly one `return` of a
   `RunRefused(...)` call, and no `else` or `finally`. Any other `try` around
   a `require`, a body of more than that statement, a second handler, a
   handler body that does anything else, or the shape in a definition whose
   family is not `run`, fails. No statement before it
   contains a §4.3 primitive call, a call to a `BYTE_MUTATION_PRIMITIVES`
   name, or `mkdir`; statements before it may validate and compute (parsing
   the bundle whose kinds `import_bundle` must name is the reason the rule is
   not "first statement"). Source position alone is not the test: a
   conditional `require`, or one placed after `init_world_root`'s `mkdir`,
   fails. A `require` whose family is not a string literal fails: the family
   is design text, not data.
3. **No entry point takes an actor.** No inventoried definition has a
   parameter named `actor`, and no public function in the seam modules
   (`corpus.py`, `boundary.py`, `replay.py`, `root.py`, `holdings/boundary.py`,
   `world/registry.py`, `world/epoch.py`, `world/rules.py`, `world/anchors.py`)
   has one, less an exact read-only exception set compared by equality:
   `{"root.audit_log", "holdings.boundary.intent_payload"}` — the audit,
   which writes nothing and labels its report (§4.2), and the holdings
   intent serializer, a pure function from an actor to payload bytes that the
   holdings acts call with the bound actor and the intent-gate tests call
   directly.
   The record dataclasses that carry an `actor` field are listed by name and
   are the only other `actor` spellings permitted outside `permit.py`.
4. **Authority enters only at the seams.** `Authority(` is constructed in
   `permit.py` and nowhere else in the package; the seams *receive* one.
   Tests construct their own.
5. **Offender and satisfied arms.** A synthetic module that calls
   `append_intent` without `require`, one that requires after the append, one
   that requires under an `if`, one that requires behind `flag and …`, one
   that calls `mkdir` before requiring, one that requires the wrong family,
   one that takes `actor`, one that wraps `require` in a `try` with a second
   statement in its body, one whose handler does more than return a
   `RunRefused`, and one that uses the run shape under a non-`run` family are
   each caught;
   a synthetic module that does everything right passes, as does one that
   parses its input before requiring and a `run`-family module using the
   exact `try` shape.

This is what makes a concurrent lane's new act — `consolidate-family`'s
relocation and deletion acts — fail the suite until it is inventoried and
requires a permit. The map is edited by hand, in the design that adds the
act, never generated.

## 6. Refusal semantics and effect ordering

- **Before the intent.** For every family that opens an intent — `import`,
  `run-attempt`, the assessment run, the holdings acts — `require` runs
  before `append_intent`. The chain head after a refusal equals the head
  before it; the durable suite asserts this over the real port.
- **The run boundary translates.** `PermitExceeded` inside
  `execute_assessment_run` or `execute_production_run` becomes
  `RunRefused(reason="permit-exceeded", report=None, intent=None,
  registration=None, detail=<the exception's message>)`, through the one
  `try` shape §5 arm 2 admits: the `require` is the try body, the handler
  returns the `RunRefused`, and nothing else sits between them. No report is
  minted: `_refused` is not called, because a refusal report is an
  `act-report` write and the permit that failed may not cover it. The reason
  string joins the run boundary's stable reason vocabulary.
- **Member by member, whole bundle.** `import_bundle` judges every member's
  kind and then `act-report` before its intent; a single unpermitted member
  refuses the bundle with `PermitExceeded` naming that kind, and nothing is
  appended. Its own `ImportRefused` path (a refusing report fulfilling the
  intent) is reached only after the permit check has passed.
- **Structure over string.** The dispatcher on the other side of the boundary
  reads `requirement` and `capability`; the message exists for a person.
  Neither is repaired, retried or written around by anything in `beliefs`.

## 7. Guarantees

The `E` table. Rows are frozen; ids are never renumbered.

| # | Guarantee | Mutation test |
|---|---|---|
| **E1** | Every write entry point judges the act family and the kinds it actually emits against the bound permit before any effect, and a violation is `PermitExceeded` naming the requirement and the capability | For each inventoried definition: bind a permit lacking its family → refused, chain head and world root unchanged; bind a permit with the family but lacking one emitted kind → refused naming that kind; bind the exact requirement → the act succeeds. **Negative:** a permit naming every kind but not the family is refused on the family, and one naming the family but a superset of the wrong kinds is refused on the first missing kind, in the caller's order |
| **E2** | Authority binds once at the construction seams, with no default, no per-call permit, and no writer whose port disagrees with it | Every seam signature has `authority` keyword-only with no default (inspected by signature); construct a `CorpusWriter` over a port bound to another authority → `ValueError` before any write; assert no entry point accepts a `permit` or `authority` argument per call. **Negative:** two writers over one port with the port's own authority both construct — the refusal is disagreement, not sharing |
| **E3** | The actor is bound with the permit; no write entry point takes an actor, and every intent, registration and actor-bearing record a write produces carries the bound actor — imported members excepted, which are provenance | Static arm 3 (§5); for each intent-opening entry point, decode the appended intent and assert `actor` equals the bound one; for `retract`, a retraction whose facet names another actor → `ActorMismatch`, nothing written; for `add`, a `run` record whose closure occurrence names another actor → `ActorMismatch`, nothing written, while a `run` record without the closure facet is minted. **Negative:** the same records under an authority whose actor matches are minted; the same closure inside an `import_bundle` member is stored verbatim and the import intent carries the bound actor |
| **E4** | `KIND_ACTS` is closed and complete over the kernel and coordination kinds; a requirement selecting an inadmissible route, an unknown kind, or an ambiguous kind without a selection is refused at construction; `publishes()` is refused while `publish` is not an act family | The key set equals `WORLD_KINDS ∪ COORDINATION_KINDS`; `for_kinds({"run"}, {})` → `ValueError` (ambiguous, unselected); `for_kinds({"run"}, {"run": "holdings"})` → `ValueError` (inadmissible); `for_kinds({"proposition"}, {})` derives `corpus-write`; `for_kinds({"x"}, {})` → `ValueError`; `publishes()` → `ValueError`. **Negative:** a `routes` key outside `kinds` is refused even when its route would be admissible |
| **E5** | A permit covers a requirement exactly when the requirement's kinds and families are subsets of the permit's; the full permit covers every constructible requirement; an empty requirement is covered by every permit | Enumerate the constructors under `full()` → all covered; a one-kind requirement against a permit with the family but not the kind → not covered, and the converse; `none()` against the empty permit → covered. **Negative:** coverage is judged on the requirement's selected routes, not on `KIND_ACTS`'s union — a `run`-kind requirement routed `corpus-write` is covered by a permit holding `corpus-write` and not `run` |
| **E6** | The set of write entry points is closed and held statically in both directions: every definition reaching a write primitive, public or private, is inventoried with its family, requires unconditionally at the top level of its body before any primitive, byte-mutation or `mkdir` call, and takes no actor; the check catches a synthetic offender and passes a synthetic satisfied module | §5 arms 1–5, each with its offender and its satisfied counterpart; add a synthetic primitive caller to the imported package → arm 1 fails naming it; remove an inventoried definition's `require` → arm 2 fails; move it after the append → arm 2 fails; wrap it in `if` → arm 2 fails; guard it with `flag and` → arm 2 fails; add a statement to a run entry point's `try` body, or a second handler → arm 2 fails; move `init_world_root`'s `mkdir` before it → arm 2 fails; add an `actor` parameter → arm 3 fails; add a second read-only exception → arm 3 fails on equality |
| **E7** | On the run boundary a permit violation surfaces as `RunRefused` with reason `permit-exceeded`, no intent appended and no report minted; on every other boundary the raised `PermitExceeded`; the corpus chain and the world root are byte-identical before and after in every case | Through a real port: an assessment run under a permit lacking `run` → `RunRefused(permit-exceeded)`, `report is None`, `intent is None`, chain head unchanged; the same over `execute_production_run`; a holdings act under a permit lacking `holdings` → `PermitExceeded`, store chain unchanged; `World.admit` under a permit lacking `registry` → `PermitExceeded`, registry directory unchanged. **Negative:** a run refused for a *non-permit* reason after the check still mints its refusal report exactly as today — the permit changes only what happens before the intent |
| **E8** | `import_bundle` is judged member by member before its intent; one unpermitted member refuses the bundle whole, naming that member's kind, with no intent appended and no record minted | A bundle of permitted members plus one `source` under a permit lacking `source` → `PermitExceeded(("kind","source"))`, chain head unchanged, no record present; the same bundle under a permit holding every member kind and `act-report` → imported with one fulfilling report. **Negative:** a permit holding every member kind but not `act-report` is refused on `act-report`, before the intent |

## 8. Limitations

1. **In-`beliefs` code is trusted.** The check is in the entry point, so a
   module inside the package that reaches a primitive without `require` is
   caught by the static test, not by the running system. The threat this
   slice answers is the `science` handler that exceeds its declaration; a
   hostile `beliefs` module is out of scope, as it is for S8.
2. **Domain kinds are unrouted** until the domain-boundary design amends
   §3.2. A domain pack that mints a kind before then fails the completeness
   test — the intended outcome.
3. **`publish` does not exist.** `publishes()` refuses; a `publishes`-class
   command cannot be built. Sub-project 5 adds the family, the operation
   kind and the route in one amendment.
4. **Direct construction is possible and permitted.** `CorpusWriter(...)`
   with an in-memory executor and a full authority is how the unit suite
   works. The boundary is that the authority must be *stated*; that it is
   stated truthfully is the launcher's obligation, and sub-project 6's
   sandbox is what makes stating it the only way in.
5. **No ledger, no session.** A refused act leaves no trace anywhere; a
   permitted act leaves exactly the trace it leaves today. Evidence that a
   session performed an act is the session task's.

## 9. Conformance cut 16

Cut 15 is discharged (`../plans/2026-09-01-conformance-cut-15-results.md`),
and no other cut is frozen; this cut takes 16 and names
`cut15_acceptance.py` as its prefix runner. `consolidate-family` freezes a
later number after this document lands (decision 8) and serializes its
discharge after cut 16's under concurrency rule 5.

### 9.1 Selection

Every row of §7 in full: E1–E8. Eight rows, 8 selected units, carried by the
arms §9.3 declares. No row of another table is selected: the slice adds
guarantees and closes none.

### 9.2 Where the arms live

**Portable suite** (no host prerequisite): `test_permit.py` — the values,
`KIND_ACTS` completeness, requirement construction and its refusals,
coverage, `PermitExceeded`'s fields and message; `test_permit_boundary.py` —
§5's five static arms with their offender and satisfied modules;
`test_corpus_write.py`, `test_import_bundle.py`, `test_retract.py`,
`test_holdings_boundary.py`, `test_boundary.py` and the world tests, each
gaining the E1/E3/E7/E8 refusals over the in-memory executor and test ports.
A shared helper, `tests/authority.py`, exports `FULL = Authority(WritePermit.full(), "test-actor")`
and `narrowed(*, kinds=(), families=())`; every existing test that passed
`actor=` moves to it.

**Durable suite**, on the certified volume beside the checkout:
`acceptance/test_permit_acceptance.py` — E1, E2, E7 and E8 through
`open_corpus` and `open_world` over registered roots, the chain-head and
world-root byte-identity assertions, the run boundary through the real
`DurableOperationPort` under the confinement gate, and a holdings act through
`holdings_seam()`.

### 9.3 N2

`acceptance/n2_arms_cut16.py` declares one lettered arm per selected unit
with its sabotage in `permit.py` (drop a family from `ACT_FAMILIES`; make
`require` return instead of raise; make `permit_covers` ignore kinds; derive
an ambiguous route silently), in `corpus.py` and `boundary.py` (move a
`require` after its `append_intent`; call `_refused` in the run handler;
widen the handler to `except WriteRefused`),
in `holdings/boundary.py` and `world/registry.py` (remove a `require` from a
private helper), in `root.py` (wrap `init_world_root`'s `require` in `if`;
guard it with `flag and`; move its `mkdir` above it; drop `migrate_root_to_lifecycle_v3`'s and `restore_root.grant`'s), and in
`test_permit_boundary.py`'s own inventory (drop an entry; compare the
implementation exclusions or the read-only exception set by containment). `test_n2_cut16.py` audits them
by the cut-12 pattern, and `tools/cut16_acceptance.py` runs
`PREFIX_RUNNERS = ("cut15_acceptance.py",)` then its phase modules.

## 10. What changes elsewhere

- **Implementation surface.** The landed change adds `permit.py`, rewrites
  `corpus.py`, `boundary.py`, `root.py`, `report.py`, `runrecord.py`,
  `stored.py`, `holdings/boundary.py`, `world/registry.py`, `world/epoch.py`,
  `world/rules.py`, `world/anchors.py`, and `world/verify.py`, and adds the
  static, per-entry-point, durable, and cut-17 tests plus the acceptance
  conftest migrations. Task 11 also repins cut 7's audit of the deliberately
  migrated cut-6 acceptance module; no frozen declaration body moves.

- **The `authority` lane.** The roadmap's lane table gains `authority` with
  `write-permits` as its one boundary and a shared surface of `corpus.py`,
  `boundary.py`, `replay.py`, `root.py`, `runrecord.py`,
  `holdings/boundary.py`, `world/registry.py`, `world/epoch.py`,
  `world/rules.py`, `world/anchors.py` and `errors.py`. It touches every
  other lane; concurrency rule 3 is satisfied by naming them here, and the
  later merge resolves toward this one.
- **The ledger's `Current state`** records the implementation in its summary
  and drops the completed `write-permits` row; the roadmap drops the same id
  from its boundary index, tier-1 table, and authority lane.
- **The guarantee inventory.** `GUARANTEE_TABLES` gains `E` with eight rows
  and `TABLE_OWNERS` names this document; the README moves to fourteen
  frozen tables and the new row total, and lists this document.
- **The guide** cites this document from `foundations.md` and adds glossary
  entries for *write permit*, *authority* and *act family*.
- **Dated amendment notes**, frozen cut text untouched: the act-report
  design §3, where the intent's `actor` is described as caller-supplied —
  it is now bound at the seam; the family-adapters design, where
  `import_bundle` takes `actor`; the holdings design, where `ActContext`
  carries `actor`; the computation design and the run-confinement design,
  where the run entry points take `actor`; world-registry and world-index
  root-lifecycle designs, where `admit`/`retire`/`depart` and the lifecycle
  acts are spelled without authority.
- **`test_capability_boundary.py`** is untouched: its `ENGINE_CALL_SITES`
  and allowlists still hold, because this slice adds no engine call and no
  raw write.
- **The `science` repository** consumes `beliefs.permit.RequiredCapabilities`,
  `beliefs.permit.KIND_ACTS` and `beliefs.errors.PermitExceeded` exactly as its
  plan's Task 12 *Consumes* block names them; nothing here changes that block.

## 11. Alternatives rejected

- **Port-level inspection.** Decode each intent payload and each plan's
  paths to a family and kinds and judge at the port. It cannot lie around,
  but the intent append is itself the first effect, so the check must run in
  two phases with two mappings, and refusals name paths rather than acts.
  In-`beliefs` code is trusted (§8.1); the static inventory gives the
  closure the port would have given, at design time.
- **Both layers.** Two mappings from writes to families that must agree,
  for a threat the package does not carry.
- **Permit now, actor later.** Halves this diff and doubles the signature
  churn; leaves "no caller-supplied actor" open until the session task.
- **A per-call permit argument.** The spec's own rejection: a request that
  carries a permit is a request that chooses its permit.
- **Deriving requirements as the union of `KIND_ACTS` routes.** Over-requires
  and wrongly refuses a session holding one valid route (command-framework
  §3.3).
- **A default full authority at the seams.** Every existing caller would keep
  working and the boundary would be a convention. The test churn (§9.2) is
  the cost of a boundary that is stated everywhere.

## 12. Verification

The repository gates, from `python/`: `uv run --frozen pytest`,
`uv run --frozen ruff check .`, `uv run --frozen pyright`; from `ts/`:
`npm ci`, `npm test`, `npm run typecheck`, `npm run check` — the TypeScript
package is untouched and its gates are the proof. The cut is discharged by
`tools/cut16_acceptance.py` on the certified volume beside the checkout with
the confinement gate satisfied, and its results record lands with the ledger
and roadmap re-rank in one commit under concurrency rule 2.

## 13. Implementation amendment — 2026-09-04

This section amends the implementation mechanics after checking the frozen
design against the current tree. It does not rewrite §7's or §9's frozen
bodies. Where it changes a cut disposition it is the current ruling, and the
cut-16 results record cites both the freeze (`c2f87b3`) and this amendment.

### 13.1 Cut 10 is cited, not run

Two frozen cut-10 arms, `H4u1` and `J8`, sabotage the **entire body** of
`holdings.boundary._publish`. E6 requires `_publish` to begin with its
`require` statement, so from this tree onward those two `before` blocks
match nothing and cut 10's audit would report them stale. On cut 9's and
cut 14's exact mechanism: the whole cut-10 surface — its design, its
declaration file, its acceptance module and its runner — is left
byte-identical and pinned so by cut 16's checks; cut 10 is **cited, not
run**, from cut 16's tree onward, its discharge standing as
`../plans/2026-08-24-conformance-cut-10-results.md`; and the successor
coverage for the two arms is carried by cut 16's own `E1` and `E7` holdings
arms plus one labeled unit, `K1`, that re-declares `H4u1`'s sabotage —
dropping the `publish_fulfilling` call — over the new `_publish` body, with
`H4u1`'s check co-cited. The eight other cut-10 arms keep matching, because
`ActContext.actor` survives as a read-only property (§13.3).

### 13.2 The runner names an inventory

§9.3's "names `cut15_acceptance.py` as its prefix runner" cannot hold
literally: that runner chains `cut14_acceptance.py`, which runs
`test_n2_cut10.py`, and both runners' probes call the lifecycle acts by
their pre-permit signatures. `tools/cut16_acceptance.py` therefore names
**no prefix runner** and defines the current-tree prefix as cut 14's module
inventory less `test_n2_cut10.py`, followed by cut 15's three phase modules,
then its own — the exact ordered list Task 13 of the implementation plan
fixes. The two older runners are left unchanged, the frozen commands of the
trees they discharged on. Cuts after 16 name `cut16_acceptance.py`.

### 13.3 Names that pinned sabotages spell

Pinned cut-3 and cut-11 arms sabotage `boundary.py` lines that spell the
name `actor` (`AssessmentRunIntent(spec.identity, secrets.token_hex(16), actor)`,
`_refused("no-frozen-spec", subject, actor, observer, started_at)`, …), and
pinned cut-10 arms spell `ctx.actor`. Removing the `actor` *parameter* is
§4.2's rule; the *name* survives as a local, `actor = port.authority.actor`,
bound immediately after the run boundary's `try` shape, and as a read-only
`ActContext.actor` property over `authority.actor`. Neither is a parameter
and neither is caller-supplied; the pinned blocks keep matching.

### 13.4 E6's inventory-side mutations are inline arms

§9.3 lists sabotages "in `test_permit_boundary.py`'s own inventory". The N2
harness copies `src/beliefs` alone, so a test file cannot be an N2 sabotage
target. Those mutations are carried instead as the static test's own
offender arms (§5 arm 5), run inline in the unit suite; the N2 arms for E6
sabotage the package (remove or displace a `require`) and are checked by the
static test.

### 13.5 Two seam details

`world.verify._admit_arrival` drops its `actor` keyword and reads
`world.authority`; `_audit_log` keeps `actor` as the label its report
carries (§4.2). `install_shipped_world_rules` needs no signature change: it
reaches `install_rule_binding`, which requires on `world.authority`.

### 13.6 `_fork_resume` is a primitive implementation

A pinned cut-9 arm spells `fork_corpus`'s retry block verbatim —
`pending = _fork_pending(dest)` … `_fork_resume(dest, pending)` … — so
`_fork_resume` can take no authority. It is the one body that invokes the
engine's `resume_fork_root` callback with the production tuple, exactly as
`_store_append_intent` is the one body that invokes `append_intent`: §4.3's
implementation list gains `root.py:_fork_resume`, compared by equality like
the rest, and §4.2's lifecycle row loses it. Its two callers, `fork_corpus`
and `fork_store`, are inventoried (each also calls `_fork_root_callback`
directly) and require `lifecycle` as their first statement, before the
pinned block. This narrows the second review finding's remedy without
reopening it: the caller is held, the implementation is named.

### 13.7 Ungoverned kinds are a third permit dimension

§3.2 calls `KIND_ACTS` complete over "every mintable kind". The tree mints
more: `CorpusWriter.add` accepts any kind outside `stored.SEMANTIC_DOMAINS`
that carries no semantic-identity facet (`_refuse_governed_stamp`), and the
durable suites rely on it (`memo` records in `durable_fixture.py`). A permit
whose `kinds` are drawn from `KIND_ACTS` alone would make the full permit
refuse them. The permit therefore carries a third, boolean dimension,
**`ungoverned`**: whether the holder may mint kinds outside `KIND_ACTS`, and
only through `corpus-write` — an ungoverned kind has no other route.
`WritePermit.full()` sets it; every `RequiredCapabilities` constructor
leaves it unset, because a declaration names governed kinds and the
`science` build refuses an unknown one; `permit_covers` judges it by
implication (`not required.ungoverned or ceiling.ungoverned`);
`Authority.require` judges a kind in `KIND_ACTS` against `kinds` and any
other kind against `ungoverned` plus the family. `PermitSummary` carries the
flag. E4's completeness claim is unchanged — it is about governed kinds —
and E5's "both dimensions" reads as "every dimension".

## 14. Renumbering and relocation amendment — 2026-09-04

This section amends the cut's number and its inventory after the relocation
half of `consolidate-family` merged into `main` ahead of this slice. Like
§13 it rewrites nothing in §7 or §9; where it changes a disposition it is
the current ruling, and the results record cites the freeze (`c2f87b3`),
§13 (`a0f2302`) and this section.

### 14.1 The cut takes 17

§9 opens "no other cut is frozen; this cut takes 16", and decision 8 has
`consolidate-family` freezing a later number. Both were false when the
freeze landed: relocation froze cut 16 at `ca31a04` on 2026-09-03, ten hours
before `c2f87b3`, and discharged it at `b0882d3`
(`../plans/2026-09-03-conformance-cut-16-results.md`). Concurrency rule 1
claims a number at freeze in freeze order and never renumbers a discharged
cut, so this cut takes **17**, the next unclaimed number. §9's frozen body is
cited, not edited: every "16" in §9 and §13 that names *this* cut reads 17
by this ruling. The files are `tests/acceptance/n2_arms_cut17.py`,
`test_n2_cut17.py` and `tools/cut17_acceptance.py`; the results record is
`../plans/2026-09-04-conformance-cut-17-results.md`; the runner's work root
is `.cut17-acceptance` and its environment sets `SCIENCE_CUT{n}_ROOT` for
`n` in 4–17. Decision 8 keeps its substance: the deletion cut of
`consolidate-family` freezes after this one and its acts are held to §5's
inventory.

### 14.2 The prefix runs cut 16

§13.2's inventory extends by one cut. `tools/cut16_acceptance.py` chains
`cut15_acceptance.py`, and its probe calls `init_corpus_root(corpus_root)`
by the pre-permit signature, so it cannot be named as a prefix runner either.
`tools/cut17_acceptance.py` names no prefix runner and defines its prefix
as cut 14's module inventory less `test_n2_cut10.py`, then cut 15's three
phase modules, then cut 16's two (`test_relocation_acceptance.py`,
`test_n2_cut16.py`), then its own. Cut 16 is **run, not cited**: every one
of its 27 pinned `before` blocks spells a call site this slice preserves —
`_add_locked(node)`, `_delete_locked(<id>)`,
`_append_operation_intent(intent.kind, intent.event_token, intent.actor)`,
`execute_fulfilling([operation], intent_digest)` — and none spells the body
of a definition §14.3 inventories. The plan's staleness probe adds cut 16 to
its tuple with an empty expected stale set; a cut-16 arm that stops matching
is a defect of the task that broke it, never a citation.

### 14.3 The relocation seams

Cut 16 added five definitions in `corpus.py` that reach a §4.3 primitive.
§4.2's inventory gains them, all under `corpus-write`:

| enclosing definition | kinds required | first statement |
|---|---|---|
| `CorpusWriter._add_locked` | `node.kind` | `self.authority.require("corpus-write", (node.kind,))` |
| `CorpusWriter._replace_locked` | `node.kind` | the same |
| `CorpusWriter._delete_locked` | the kind of the record removed | `self.authority.require("corpus-write", (self._view.get(ref).kind,))` — a read inside the argument, no effect before the check |
| `CorpusWriter._append_operation_intent` | `act-report` — the fulfilment the intent opens | `self.authority.require("corpus-write", ("act-report",))` |
| `CorpusWriter._publish_operation_report` | `act-report` | the same |

`_preflight_add_locked` and `_preflight_replace_locked` call no primitive and
are not inventoried; the run-closure actor check E3 places on `add` lives in
`_preflight_add_locked`, so `add` and `_add_locked` share it.

**The intent's actor is judged, not taken.** Cut 16's T2b and T2c pin the
call `_append_operation_intent(intent.kind, intent.event_token, intent.actor)`,
so the definition keeps three positional parameters. The third is renamed
`intent_actor` and is a cross-check, never a source of identity: after the
`require`, `intent_actor != self.authority.actor` raises `ActorMismatch`
before anything is appended, and the intent is encoded from
`self.authority.actor`. This is `retract`'s rule (§4.2) applied to an
operation intent, and E3's arm 3 holds because the parameter is not named
`actor`.

**The two-root operations take no actor and judge every root before the
first intent.** `relocation.move` and `relocation.consolidate` lose their
`actor` keyword; `relocation.py` joins the seam modules arm 3 inspects. Each
begins by refusing a pair of writers whose bound actors differ
(`ActorMismatch`, before the locks), and builds its `OperationIntent` from
the shared bound actor. Because cut 16's T2b/T2c pin the order *intents,
then add, then delete*, a refusal at `_add_locked` or `_delete_locked` would
leave an appended intent in each root; so before its first
`_append_operation_intent` each operation requires, on every writer it will
write through, `corpus-write` with the record's kind and `act-report` — one
bare `require` per writer, explicit statements placed after the record is
resolved and before the intent token is minted. §4.3's redundant-require
rule makes the later checks in the inventoried helpers harmless repeats.
Neither operation is inventoried: neither calls a primitive itself.

### 14.4 Coverage, unchanged rows

No row of §7 changes. E1's "for each inventoried definition" and E6's
closed inventory reach the five definitions by construction, so
`test_permit_entry_points.py` and the static test cover them without a new
row. E3's intent arm gains `_append_operation_intent`. E7's "on every other
boundary the raised `PermitExceeded`; the corpus chain … byte-identical"
gains its two-root case in the durable suite: a `move` over registered roots
under a destination permit lacking the record's kind is refused, and both
chain heads are unchanged. The cut's N2 declaration adds arms for the
relocation seams — displace `_add_locked`'s `require` below its add; drop
`_append_operation_intent`'s `ActorMismatch`; drop `move`'s pre-intent
`require` on the destination — each named to a check in the unit or durable
suite. §9.1's accounting (8 selected units, no labeled unit beyond §13.1's
`K1`) is unchanged; the arm count grows.

### 14.5 What changes elsewhere, by this section

The roadmap's `authority` lane row, the ledger's `write-permits` row and the
README's design-table row each said "cut 16"; they read 17 from this commit.
The implementation plan (`../plans/2026-09-04-write-permits.md`) renumbers
its file names, runner, results record and commit messages to 17 outside
its verbatim quotation of §13 and its already-executed Task 1, adds the
relocation seams to Task 5, `relocation.py` to Task 11's seam modules, the
two-root refusal to Task 13 and the relocation arms to Task 14.
