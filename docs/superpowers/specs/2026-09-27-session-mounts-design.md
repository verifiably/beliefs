# The attended session over a write root and N mounted corpora

**Amends:** the writer-session design (`../../designs/2026-09-05-writer-session-design.md`,
§3.1 and limitation 1) and its guarantee row J9.
**Requested by:** science's projects design
(`science docs/specs/2026-09-23-projects-corpora-and-workspaces-design.md` §3.1, §9.2) and
its coordination command set design
(`science docs/specs/2026-09-24-coordination-command-set-design.md` §6).
**Boundary:** `multi-corpus-session`, new, in the `write-path` lane, which this design
reopens.
**Task:** `beliefs-fe7149`
**Cut:** the next number free at freeze (roadmap concurrency rule 1). The number is 42 if
this cut freezes before `beliefs-3ce305`'s cut does, and 43 otherwise. This spec calls it
**cut N**.
**Status:** draft for user review, 2026-09-27

## 1. What this slice is

A session opens over one corpus. `open_attended_session` refuses unless
`world_config.corpus_roots` names exactly one root, and its `CoordinationResolver` mounts
only that root (`session/__init__.py`). The writer-session design put the limit there on
purpose (limitation 1, "One corpus root"), waiting for a caller that needed more.

Science now needs more. Its second-project milestone (projects design §9.2, criterion 1)
opens one session that writes a fresh working corpus and reads the reproduced mm30 corpus
beside it. The two corpora pin different contracts. The working corpus pins base, `biology`
and coordination v2. The mm30 corpus pins base, `biology` and its corpus-local `mm30`
contract, and no coordination contract (its `corpus.yaml` today). A record must be decoded
under the contract it was typed under, so each corpus is read under the profile its own
manifest pins, never under the writer's.

A reading of the tree on 2026-09-27 found that most of the machinery already exists, and
that three things are missing:

- `CoordinationResolver` takes `{root: profile}` for any number of roots. It checks each
  mount's manifest pins against the profile it is given, and it unions revisions across
  mounts, so tips are already world-wide over whatever it mounts.
- `CorpusWriter.revise_coordination` resolves predecessors through the resolver, and the
  corpus check exempts coordination `supersedes` edges from `supersession-target-missing`
  (`corpus.py`, the supersession arm). So a revision written to one corpus whose
  predecessor is stored in another was provided for.
- The publish doors (`publication_doors._open_publication`, `_judge`) read
  `resolver.mounted()`, anchor every mount other than the written root, and refuse
  `chain-absent` or `chain-malformed` for one. The publish act was designed for a resolver
  with several mounts.
- `reconcile_sessions` already walks every configured root under one lock-coherent hold.

The missing three:

1. **No way to name the write root.** The session takes the only root it will accept.
2. **No way to build a mount's profile from its manifest.** The kernel compiles a profile
   from documents the caller chooses (`compile_profile`). Nothing resolves a manifest's pins
   to documents, so a caller must know every mount's contracts in advance, and science's
   rule "availability never becomes activation" (coordination command set §6) has no
   kernel home.
3. **The session mounts one root.** The resolver it builds is `{root: coordination}`.

After this slice, a launcher compiles one profile per configured root with
`compile_mount_profile` and opens a session naming its write root and those mounts. The
session writes only its write root and resolves coordination over every root. Science's
sessionless read context calls the same function and builds its own resolver.

## 2. Decisions

1. **The write root is a required argument, and it is one of `corpus_roots`.**
   `open_attended_session` takes `write_root: Path` by keyword, with no default, and refuses
   a write root that is not in `world_config.corpus_roots` after resolution. A one-root
   configuration passes that root. Science's configuration may default `write_root` when
   `corpus_roots` has one entry (its own §6 rule). The kernel does not infer it.
   *Rejected:* a `write_root` field on `WorldConfig`. `WorldConfig` is the world's read set,
   and `reconcile_sessions`, the read side and the publish act take it without any notion of
   a writer. A field only the session reads would sit on every other consumer's value.
   *Rejected:* defaulting to the sole root when there is one. A default makes the write
   destination implicit on the path where it most often goes unexamined, and the two-root
   case would still need the argument.

2. **The session takes precompiled mounts; the kernel owns how they are compiled.**
   `open_attended_session` takes `mounts: Mapping[Path, ProfileSpec] | None`, which replaces
   `coordination: ProfileSpec | None`. The launcher builds the mapping with one new public
   function, `compile_mount_profile(root, *, available)` (§3.1).
   *Rejected:* the session takes the launcher's available documents (science's
   `contracts ∪ read_contracts`) and compiles internally. Science's sessionless reads need
   the same compile with no session (its §6: "in the session's resolver and in the
   sessionless read context a CLI read builds alike"). Compiling inside the session would
   leave science to reimplement the function, or call a private one. One public function,
   called by both, keeps one resolution rule.

3. **Every configured root is mounted, or none is.** When `mounts` is supplied, its keys,
   after resolution, must be exactly the set of `corpus_roots`, and two keys resolving to
   one root refuse. `mounts=None` opens a session with no resolver, as `coordination=None`
   does today, and every coordination act refuses `CoordinationUnavailable`.
   *Rejected:* allowing a subset. Coordination §6.3 makes tip resolution world-wide. A
   session mounting part of the world would resolve an address to a tip another configured
   corpus has already superseded, and would report it as standing.
   A root whose manifest pins no coordination contract (mm30) is still mounted. Its
   profile declares no coordination kinds, so the resolver collects no revisions from it,
   but the publish act anchors every mounted chain, and the world-wide rule counts it.

4. **The writer's profile is its own mount's profile.** When `mounts` is supplied,
   `require_profile_compatible(profile, mounts[write_root])` holds, as it holds today for
   `coordination`. Science's launcher passes its stated writer profile for the write root
   (coordination command set §6: stated, never inferred), and the resolver checks it
   against the write root's pins.

5. **A pin resolves by namespace and content identity, and only pins activate.**
   `compile_mount_profile` reads the root's manifest and resolves each pin, never
   activating anything the manifest does not pin. The science pin must be the shipped
   base's identity. A `coordination` pin resolves against the shipped coordination
   contracts, versions 1 and 2. Every other pin resolves against the shipped domain pack of
   that namespace, if there is one, and the `available` domain contracts of that namespace.
   The candidate whose `content_identity` equals the pinned identity is the one activated.
   No candidate, and the function refuses `MountPinUnresolved`, naming the root, the
   namespace and the pin. Two candidates cannot disagree: equal content identity means
   equal content.
   *Rejected:* resolving by namespace alone and checking identity afterwards. An available
   document of the right namespace and a later identity (a successor of `biology`, say)
   would be the only candidate, and a name-first rule invites "the newest one" as a
   fallback. Identity-first leaves nothing to fall back to.

6. **Read mounts are checked for what reading them needs, and no more.** At open, each
   read mount's manifest must load. The resolver's constructor already loads it, and the
   session re-raises `ManifestMissing` and `ManifestMalformed` as `SessionRefused` naming
   the root, as it does for the write root. Its pins must match its supplied profile (the
   resolver's `ContractMismatch`). A read mount's chain is not inspected at open. The
   writer-session design checks the write root's chain because every `act` line must be
   verifiable against it, and a session writes no act against a read mount. Readers that
   need a read mount's chain check it where they need it: the publish act refuses
   `chain-absent` or `chain-malformed` for a mount at its step 0, and reconciliation reports
   what it finds.

7. **The session writes nothing to a read mount.** The writer factory binds `write_root`
   and nothing else, the operation port is the write root's, and the resolver only reads.
   A coordination revision whose predecessor is stored in a read mount is written into the
   write root. This is the one property the slice exists to keep, and it has its own row
   (J15).

8. **The ledger does not change.** `session-open` carries no corpus field today. Each
   `act` line carries the corpus id of the root it wrote, which is the write root's, read
   once at open as today. Reconciliation already matches act lines to chains by corpus id
   across every configured root, so an actor-matching entry in a read mount's chain would
   be classified `session-entry-foreign`, which is the detection we want. No line kind, no
   key, no reader rule moves.
   *Rejected:* recording the mount set in `session-open`. Nothing reads it. The initial
   project and every `select` are pinned to a revision, so resolution is replayable without
   knowing which mounts produced it.

9. **No cache.** `compile_mount_profile` compiles on every call. A session opens once, and a
   CLI read compiles once per command. If measured cost ever warrants a cache, one keyed by
   the pinned identities can be added without changing the interface.

10. **A conformance cut, not an amendment.** The selection design shipped without a cut on
    the condition that no live sabotage pin moved and no cut's evidence was invalidated
    (its decision 8). This slice fails both. Cut 19's live arm J9a pins
    `if len(world_config.corpus_roots) != 1:`, and J9's frozen evidence opens "configs with
    zero and two corpus roots → `SessionRefused`". After this slice a two-root configuration
    with a write root opens. So J9's two-root clause is superseded by a successor row and
    cited (§9), and the change is held by a cut with its own N2 arms.
    *Rejected:* an amendment with J9a re-pointed and unit tests alone. That edits what a
    frozen row's evidence means without a cut that says so, which is the path the
    freeze-and-supersede discipline closes.

## 3. Surface

### 3.1 `compile_mount_profile` — `beliefs/mount.py` (new)

```python
def compile_mount_profile(root: Path, *, available: Iterable[DomainContract] = ()) -> ProfileSpec:
    """The profile a corpus's own manifest pins (decision 5)."""
```

- `root` must be a `Path` (`TypeError`), and every element of `available` must be a parsed
  `DomainContract` (`UnparsedContract`, as `compile_profile` refuses). The launcher parses
  each document with its own base and predecessor. The kernel does not load files here.
- `load_manifest(root)`. `ManifestMissing` and `ManifestMalformed` propagate.
- The science pin must equal `"science:" + shipped_base_contract().content_identity`,
  otherwise `MountPinUnresolved(root, "science", pin)`.
- Each domain pin, in namespace order, resolves by decision 5. The first that does not
  resolve refuses, naming that pin.
- The result is `compile_profile(shipped_base_contract(), <resolved domains in namespace
  order>, coordination=<resolved coordination or None>)`. A `ProfileError` from compilation
  propagates. The pins of the result equal the manifest's pins by construction; the
  resolver's constructor checks that again.

The module imports `profile`, `contract`, `errors` and `world.load_manifest`, and nothing
from `atoms`. `root.py` remains the only `atoms` importer.

`MountPinUnresolved(ProfileError)` joins `errors.py`, with `root: Path`, `namespace: str`
and `pin: str` attributes, and a message naming all three.

### 3.2 `open_attended_session` — `session/__init__.py`

```python
def open_attended_session(
    world_config: WorldConfig,
    operations_root: Path,
    *,
    write_root: Path,
    profile: ProfileSpec,
    mounts: Mapping[Path, ProfileSpec] | None = None,
    store_root: Path | None = None,
    snapshot_resolver: SnapshotResolver | None = None,
    project: CoordinationAddress | None = None,
) -> WriterSession:
```

`coordination` is removed. It has one caller outside this repository (science's launcher),
which moves to `mounts` in `sci-923d3a`. Under the no-compatibility-layer rule there is no
shim.

The checks run in this order. Every refusal comes before the session directory exists, so
none creates one:

1. Types: `world_config` an exact `WorldConfig`, `operations_root` and `write_root` `Path`s,
   `profile` a `ProfileSpec`. `mounts`, when supplied, is a `Mapping` with `Path` keys and
   `ProfileSpec` values. Anything else raises `TypeError`.
2. `project` with `mounts=None` refuses `SessionRefused` (as today with
   `coordination=None`).
3. An empty `corpus_roots` refuses `SessionRefused` ("a session needs at least one corpus
   root").
4. `write_root.resolve()` not in `corpus_roots` refuses `SessionRefused`, naming the write
   root.
5. With `mounts`: two keys resolving to one path, or a resolved key set other than
   `corpus_roots`, refuses `SessionRefused`, naming the missing and the extra roots.
6. `require_profile_compatible(profile, mounts[write_root] if mounts else None)`
   (`ContractMismatch`).
7. The write root's manifest loads (`SessionRefused`), `require_pins_agree(write_root,
   profile)` holds (`ContractMismatch`), and its detached view is a `WellFormedView`
   (`SessionRefused`). These are today's checks on today's root.
8. `store_root` checks, unchanged.
9. `CoordinationResolver(mounts)`, when `mounts` is supplied. A read mount whose manifest
   does not load re-raises as `SessionRefused` naming the root. A pin mismatch propagates as
   the resolver's `ContractMismatch`.
10. `project` resolves through the resolver (unchanged).

The writer factory, `WriterSession(corpus_root=…, corpus_id=…)`, and reconciliation are
unchanged except that they take `write_root` where they took the sole root.
`SessionRefused`'s docstring changes from "not exactly one corpus root" to "no corpus
root, or a write root or mount set that does not match the configured roots".

## 4. Coordination over every mount

Nothing in `CoordinationResolver` changes. The behaviours below are what a session gains by
building the resolver over every root, and §9's J14 holds each of them:

- An unpinned address resolves over the union of every mount's revisions. A revision stored
  only in a read mount is a tip.
- `revise_coordination` in the session accepts a predecessor stored in a read mount. The
  revision is written into the write root, and afterwards the address resolves to it.
- Tips of one address stored in two different mounts, neither superseding the other,
  resolve to `divergent-view`, as they would in one corpus.
- The initial `project` at open resolves over every mount, so a project minted in a read
  mount can be the initial selection.
- `standing(kind, project=…)` enumerates over every mount.

## 5. What does not change

- The ledger: every line kind, key set and reader rule (decision 8).
- `CoordinationResolver`, `CorpusWriter`, `reconcile_sessions` and the publish act's code.
- Science's read side (`ReadContext.views`). It already opens one view per configured
  root; its resolver moves to per-mount profiles in science's own task.
- The scoped writer's permit, the claim protocol and the lifecycle (J1–J8, J10, J11).
- Cross-corpus *targeting* for ordinary writes. A non-coordination `supersede`, `revise` or
  `retract` resolves its target in the write root and refuses `target-missing` when the
  target lives elsewhere, as today. The world-resolution lane owns that (writer-session
  limitation 1's second sentence stands).

## 6. Shared files, under roadmap concurrency rule 3

This lane rewrites `session/__init__.py` and adds `mount.py`. Its overlap with the open
`world-read` lane (`publish`, cut 42 or 43) is:

- `errors.py` (one class), `python/tests/test_designs_corpus.py`, the adoption ledger, the
  roadmap and the guide index. Every lane rewrites these.
- No file in `world-read`'s shared-surface column. `corpus.py` is read, not edited.

Every existing test that calls `open_attended_session` (the session, selection, publish
and acceptance suites) gains `write_root=` and moves from `coordination=` to `mounts=`. The
publish lane's branch will meet those call sites at merge, and the later merge resolves
toward the earlier one.

## 7. Guarantee rows

Four new rows in the `J` table. J9's two-root clause is superseded by J12 and cited
(§8.3). J9's text and its other clauses stand.

| row | guarantee | mutation test |
|---|---|---|
| **J12** | A session opens over a write root and a mount set. It opens when `write_root` is one of `corpus_roots` and `mounts` is `None` or covers exactly `corpus_roots`. It refuses at open with no session directory when `corpus_roots` is empty, when `write_root` is outside it, when `mounts` omits or adds a root or names one root twice, when a read mount's manifest does not load, and when the writer's profile is not the write mount's | Open over a two-root world with each root as the write root in turn → opens, `corpus_root` is the named one. Open over: zero roots; a write root outside the set; mounts missing one root; mounts with an extra root; mounts naming one root by two paths (a symlink); a read mount with no manifest; `profile` differing from `mounts[write_root]` → `SessionRefused` or `ContractMismatch` as §3.2 lists, no `sessions/` entry. **Negative:** a one-root world with `write_root` set to that root writes the same `session-open` key set, world id and permit summary that J9's case asserts |
| **J13** | `compile_mount_profile` activates exactly the manifest's pins, each resolved by namespace and content identity against the shipped base, the shipped coordination contracts, the shipped domain packs and `available`. A pin nothing resolves refuses `MountPinUnresolved` naming the root, namespace and pin, and an available document the manifest does not pin is never activated | Compile a corpus pinning base, `biology` and coordination v2 with nothing available → its pins; a corpus pinning a test-local domain contract with that contract available → its pins; the same with the contract absent → `MountPinUnresolved` naming it; with an extra unpinned contract available → activated set unchanged; a corpus pinning an unshipped base identity → `MountPinUnresolved` on `science`. Pass each result to `CoordinationResolver` → accepted. **Negative:** an available contract with the pinned namespace and a different identity does not satisfy the pin |
| **J14** | A session with mounts resolves coordination over every mounted corpus: tips, revise predecessors, divergence, the initial project and `standing` | Mint a project in corpus B (a read mount, written by a library writer before open); open a session writing A with `project` set to B's address → opens with B's revision pinned in `session-open`. Revise that project in the session → the revision is in A, the address resolves to it, `standing("project")` lists it once. Then, with the session still open, revise the same project from its B revision through a library writer on B alone (whose own resolver sees only B) → two tips, one per root, and the session resolves the address to `divergent-view` naming both. **Negative:** the same session opened with `mounts` covering only A refuses at open (J12), and a session with `mounts=None` refuses `revise_coordination` with `CoordinationUnavailable` |
| **J15** | A session never writes a read mount | Hash every read mount's tree, its metadata sibling and its chain before open. Run a lifecycle with an ordinary write, a coordination mint and a revision of a read-mount predecessor, then close and reconcile. Hash again → equal. Reconciliation reports no finding against a read mount. **Negative:** a writer factory bound to a read mount changes that mount's hash, and the check fails |

## 8. Testing and the cut

### 8.1 Unit — portable

`tests/test_mount.py` (new): each J13 case over roots built in a temporary directory,
through `adopt_manifest` with the pins under test. The test-local domain contract is a
fixture document parsed with `parse_domain_contract`, with the shipped base and no
predecessor.

`tests/test_session*.py`: the existing opens move to `write_root=` and `mounts=`. The J12
refusal table is parametrized there and asserts no `sessions/` entry for each case.

### 8.2 Acceptance — `test_session_mounts_acceptance.py` (new)

J12, J14 and J15 in full on the certified volume, beside the checkout (the durable arms'
home). There are two corpora: A pins base, `biology` and coordination v2, and B pins base,
`biology`, coordination v2 and the test-local contract. B pins coordination so it can hold
the J14 predecessor. A third corpus, C, pins no coordination, and a J12 case mounts it
beside A to cover the mm30 shape (decision 3).

### 8.3 N2 sabotages — `n2_arms_cutN.py`

One arm per mutation that must fail a check:

| arm | sabotage | check that fails |
|---|---|---|
| J12a | the write-root membership check removed | the outside-write-root case opens |
| J12b | the mount-set equality check removed | the missing-mount case opens |
| J12c | the writer factory binds `corpus_roots[0]` instead of `write_root` | the second-root-as-write-root case writes the wrong root |
| J13a | resolution matches on namespace only | the different-identity negative activates |
| J13b | every available contract is activated | the extra-contract case gains a namespace |
| J14a | the resolver is built over `{write_root: mounts[write_root]}` only | the read-mount project does not resolve at open |
| J15a | the writer factory binds the first read mount | the read mount's hash changes |

Cut 19's J9a pins `if len(world_config.corpus_roots) != 1:`, which this slice removes. Cut
N's runner re-targets J9a in its `_LIVE_SABOTAGES` table to the empty-roots refusal. J9's
zero-root evidence still holds, and a sabotage of that check still fails J9's zero-root
case. J9a's frozen declaration is not edited, and cut N's document cites J12 as the
successor of J9's two-root clause. `test_arm_staleness.py` then sees no stale pin.

J9's case in `test_session_acceptance.py` opens a two-root configuration and expects
`SessionRefused`. That configuration now opens, so cut N's commit removes the two-root
case from J9's parametrization (J12 covers it) and passes `write_root` to the rest. The
edit is named in cut N's document. It is the only change to cut 19's acceptance module;
the other refusing configurations stay as they are.

### 8.4 The cut

Cut N selects J12–J15 in full and names the highest-numbered acceptance runner (rule 5).
If it freezes after `beliefs-3ce305`'s cut, its discharge waits for that cut's. The plan's
Global Constraints carry the two repository obligations verbatim:

- `root.py` stays the one `atoms` importer. `mount.py` imports none of it, and this slice
  adds no write primitive, so `WRITE_ENTRY_POINTS` does not change.
- Cut N adds its row to `test_recent_cut_acceptance.py`.

## 9. Documentation amendments

- The writer-session design gets a dated amendment section: §3.1's signature and checks,
  limitation 1 retired in its first sentence, and J9's two-root clause pointing at J12.
- The adoption ledger's `Current state` gains `multi-corpus-session` and closes it at
  cut N's results record. The `write-path` lane row reopens with this boundary.
- The roadmap places `multi-corpus-session` in tier 1 **on the path**: it is a prerequisite
  of the second-project milestone, which is the next measurement of the success criterion
  (roadmap, "On the path"). Rule 6's two-lane limit holds, with `world-read` as the second
  open kernel lane.
- Science: `sci-923d3a` consumes `write_root`, `mounts` and `compile_mount_profile`.
  Science's §6 names this task for both keys.

## 10. Limitations

1. **Every mount pins the shipped base.** A corpus typed under an earlier base contract
   refuses `MountPinUnresolved` on `science`. The runtime ships one base, and a profile
   compiled under another base is the case `compile_profile` refuses. Base succession is
   its own design.
2. **A read mount's chain is not verified at open** (decision 6). A session over a read
   mount whose chain is malformed opens. Its coordination reads come from the records
   `ReadView` sees, the publish act refuses at step 0, and reconciliation reports the chain.
3. **No cache** (decision 9).
4. **Ordinary writes do not target another corpus** (§5). This is unchanged, and it stays
   with the world-resolution lane.

## 11. Task linkage

`beliefs-fe7149` holds this spec (`--spec session-mounts`). The plan's steps become its
children. `beliefs-c08725` (relocating the mm30 corpus) is independent of this code and
feeds the same milestone.
