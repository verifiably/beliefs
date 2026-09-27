# Conformance cut 43 — the multi-corpus session

**Status:** discharged 2026-09-27; J12–J15 closed; [results](../plans/2026-09-27-conformance-cut-43-results.md). Frozen body below unchanged.
**Design:** [session-mounts design](../superpowers/specs/2026-09-27-session-mounts-design.md), approved 2026-09-27.
**Plan:** [implementation plan](../superpowers/plans/2026-09-27-session-mounts.md).
**Numbered** after cut 42 (`design/publish`) under roadmap rule 1; its discharge serializes after cut 42's under rule 5. The branch scan on 2026-09-27 found `design/publish: conformance-cut-42` and no cut 43 document on any branch. The cut 42 document hash was `5887bb87dc30d7451c3302651d546aa941cea70be6e99b7223fbd537d45faf35`.

## 1. What this cut is

A session currently accepts one corpus root and mounts only that root for coordination. Science's second-project milestone needs a session that writes a selected corpus while reading each configured corpus under the profile compiled from its own manifest. The kernel already resolves coordination over any number of supplied mounts; this cut adds manifest-based profile compilation, names the write root, mounts every configured corpus, and reconciles session acts against the corpus that holds each registration. The launcher supplies the available domain documents.

The cut opens `multi-corpus-session` on the path to the second-project milestone. It shares `session/` with the existing `write-path` surface and `world-read` is the other open kernel lane.

## 2. The boundary

The files Tasks 1–5 change or create are:

- `python/src/beliefs/mount.py` (new), `python/src/beliefs/errors.py`;
- `python/src/beliefs/session/__init__.py`, `python/src/beliefs/session/reconcile.py`;
- `python/tests/test_mount.py` (new), `test_session_writer.py`, `test_session_routes.py`, `test_profile_agreement.py`, `test_session_reconcile.py`;
- `python/tests/acceptance/test_session_acceptance.py`, `test_n2_cut19.py`, and `python/tests/acceptance/test_session_mounts_acceptance.py` (new);
- `python/tests/n2_arms_cut43.py`, `python/tests/acceptance/n2_arms_cut43.py`, `python/tests/acceptance/test_n2_cut43.py`, `python/tools/cut43_acceptance.py` (new), and `python/tests/test_recent_cut_acceptance.py`.

Every new N2 sabotage targets `session/__init__.py`, `mount.py` or `session/reconcile.py` as specified in §5.

## 3. Selection

Four guarantee rows are selected from the writer-session design. Their text is byte-exact from the linked session-mounts design §7 at freeze.

```markdown
| **J12** | A session opens over a write root and a mount set. It opens when `write_root` is one of `corpus_roots` and `mounts` is `None` or covers exactly `corpus_roots`. It refuses at open with no session directory when `corpus_roots` is empty, when `write_root` is outside it, when `mounts` omits or adds a root or names one root twice, when a read mount's manifest does not load, and when the writer's profile is not the write mount's | Open over a two-root world with each root as the write root in turn → opens, `corpus_root` is the named one. Open over: zero roots; a write root outside the set; mounts missing one root; mounts with an extra root; mounts naming one root by two paths (a symlink); a read mount with no manifest; `profile` differing from `mounts[write_root]` → `SessionRefused` or `ContractMismatch` as §3.2 lists, no `sessions/` entry. **Negative:** a one-root world with `write_root` set to that root writes the same `session-open` key set, world id and permit summary that J9's case asserts |
| **J13** | `compile_mount_profile` activates exactly the manifest's pins, each resolved by namespace and content identity against the shipped base, the shipped coordination contracts, the shipped domain packs and `available`. A pin nothing resolves refuses `MountPinUnresolved` naming the root, namespace and pin, and an available document the manifest does not pin is never activated | Compile a corpus pinning base, `biology` and coordination v2 with nothing available → its pins; a corpus pinning a test-local domain contract with that contract available → its pins; the same with the contract absent → `MountPinUnresolved` naming it; with an extra unpinned contract available → activated set unchanged; a corpus pinning an unshipped base identity → `MountPinUnresolved` on `science`. Pass each result to `CoordinationResolver` → accepted. **Negative:** an available contract with the pinned namespace and a different identity does not satisfy the pin |
| **J14** | A session with mounts resolves coordination over every mounted corpus: tips, revise predecessors, divergence, the initial project and `standing` | Mint a project in corpus B (a read mount, written by a library writer before open); open a session writing A with `project` set to B's address → opens with B's revision pinned in `session-open`. Revise that project in the session → the revision is in A, the address resolves to it, `standing("project")` lists it once. Then, with the session still open, revise the same project from its B revision through a library writer on B alone (whose own resolver sees only B) → two tips, one per root, and the session resolves the address to `divergent-view` naming both. **Negative:** the same session opened with `mounts` covering only A refuses at open (J12), and a session with `mounts=None` refuses `revise_coordination` with `CoordinationUnavailable` |
| **J15** | A session never writes a read mount | Hash every read mount's tree, its metadata sibling and its chain before open. Run a lifecycle with an ordinary write, a coordination mint and a revision of a read-mount predecessor, then close and reconcile. Hash again → equal. Reconciliation reports no finding against a read mount. **Reconciliation matches by corpus:** over stand-in views, a ledger whose act line names corpus A while the fulfilling registration is committed in B's chain under the session's actor yields `session-entry-foreign` in B and `session-act-unverified` for the act naming A; the same ledger with the act naming B yields neither. **Negative:** a writer factory bound to a read mount changes that mount's hash, and the check fails |
```

Nine declaration units are selected, one per arm:

| unit | row | check |
|---|---|---|
| J12-a | J12 | acceptance: the zero-root and outside-write-root membership cases |
| J12-b | J12 | acceptance: the exact mount-set refusal cases |
| J12-c | J12 | acceptance: selecting the second root as write root writes that root |
| J13-a | J13 | `test_mount.py::test_a_same_namespace_document_of_another_identity_does_not_satisfy_the_pin` |
| J13-b | J13 | `test_mount.py::test_an_available_unpinned_document_is_never_activated` |
| J14-a | J14 | acceptance: a project on a read mount resolves at open |
| J15-a | J15 | acceptance: lifecycle hashes of read mounts remain unchanged |
| J15-b | J15 | `test_session_reconcile.py::test_a_registration_in_another_corpus_than_its_act_names_is_foreign_there` |
| J15-c | J15 | `test_session_reconcile.py::test_an_act_naming_a_corpus_that_does_not_hold_it_is_unverified` |

The acceptance module declares 13 test cases.

## 4. Accounting

**9 arms, 9 declaration units**, four rows; recent-cut row `(9, 9, 4)`. The cut is frozen before its code exists. On this branch's tree, 204 of 235 rows are closed and 31 are open. Cut 42's rows join at the Task 5 merge; Task 7 re-ranks the merged tree.

## 5. N2 and acceptance obligations

| arm | sabotage | check that fails |
|---|---|---|
| J12a | the write-root membership check removed | the outside-write-root case opens |
| J12b | the mount-set equality check removed | the missing-mount case opens |
| J12c | the writer factory binds `corpus_roots[0]` instead of `write_root` | the second-root-as-write-root case writes the wrong root |
| J13a | resolution matches on namespace only | the different-identity negative activates |
| J13b | every available contract is activated | the extra-contract case gains a namespace |
| J14a | the resolver is built over `{write_root: mounts[write_root]}` only | the read-mount project does not resolve at open |
| J15a | the writer factory binds the first read mount whose profile matches the writer's | the read mount's hash changes |
| J15b | `reconcile` builds a session's act index over every corpus, not the chain's own | the A-named act over B's registration lacks `session-entry-foreign` in B |
| J15c | the committed set holds digests, not `(corpus_id, digest)` pairs | the act naming A is not `session-act-unverified` |

Cut 19's J9a is re-targeted in `test_n2_cut19.py`'s `_LIVE_SABOTAGES` table: change `if write_root not in world_config.corpus_roots:` to `if False:`. Its zero-root case supplies an adopted, well-formed write root, so removal of this membership check opens the session and makes the case fail. The other cut-19 pins remain byte-exact.

The runner declares `PREFIX_RUNNERS = ("cut42_acceptance.py",)` and `PHASE_MODULES = ("test_session_mounts_acceptance.py", "test_n2_cut43.py")`.

## 6. Second reader

Check that J9a's re-target is observable: its zero-root case passes an adopted, well-formed write root so the membership check is the only refusal. Check that J15-a hashes each read mount's metadata sibling as well as its tree and chain before and after the lifecycle.

## 7. Limitations

1. Every mount pins the shipped base; a corpus typed under an earlier base refuses `MountPinUnresolved`. Base succession is a separate design.
2. A read mount's chain is not verified at open. Coordination reads use the records `ReadView` sees; publish refuses a malformed chain at step 0, and reconciliation reports it.
3. There is no cache.
4. Ordinary writes do not target another corpus; that remains with the world-resolution lane.
