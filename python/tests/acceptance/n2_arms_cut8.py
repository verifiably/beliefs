"""Cut 8's 53 frozen log-verification arms and the sabotages they must not survive.

**43 selected + 10 labeled = 53**, one declaration unit per `Selected` and
`Labeled` bullet of `docs/designs/2026-08-22-conformance-cut-8.md` §3, counted
once at its home. `test_n2_cut8.py` reconciles this table against §4's
accounting and audits every arm; nothing here restates a clause another row
owns.

**`row` is the unit id, not the frozen row.** Cut 8's accounting is by *unit* —
`L4` alone carries seven of them — and an arm table keyed by row could not say
which of the seven a sabotage falsified. The row is recoverable from the id and
`ROW_UNITS` states the partition the cut's §4 accounting fixes.

**Every check is one test function, fully qualified.** The frozen cut's table
names each check as ``<file>::<function>``; where that function lives inside a
class the *resolvable* node id carries the class between the two, exactly as
cut 7 records. The file and the function name are the frozen ones, verbatim.

**Fabrication provenance is declared, not assumed.** Cut 8 §5's obligation 1
requires every fabricated chain a declared arm rests on to pass `inspect_chain`
at declaration time. `FABRICATION_BY_UNIT` names, per unit, the on-disk builders
in `test_world_log_codecs.CUT8_FABRICATIONS` its arm judges;
`VIEW_LEVEL_UNITS` names the units whose arms do not turn on a chain, with the
ground for each. `test_n2_cut8.py` enforces both halves, the second per unit.
"""

from __future__ import annotations

from n2_arms import Arm, Sabotage

__all__ = [
    "CUT8_ARMS",
    "FABRICATION_BY_UNIT",
    "LABELED_UNITS",
    "ROW_UNITS",
    "VIEW_LEVEL_GROUNDS",
    "VIEW_LEVEL_UNITS",
]


ROW_UNITS: dict[str, int] = {
    "L1": 1,
    "L2": 5,
    "L3": 4,
    "L4": 7,
    "L5": 2,
    "L7": 2,
    "L8": 2,
    "L9": 5,
    "L10": 1,
    "L11": 4,
    "L12": 5,
    "L13": 5,
}
"""Cut 8 §4's selected-unit partition, verbatim: 43 across twelve rows."""

LABELED_UNITS: tuple[str, ...] = ("D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D10")
"""§3.3's ten labeled declarations, in the order the cut states them."""


# --- shared sabotages ---------------------------------------------------------
#
# A sabotage is shared only where two arms turn on the *same* Science behaviour.
# Cut 8 §1 is why that happens as often as it does here: the engine detects a
# defect and this cut certifies the evaluator's reading of it, so six defect
# arms have one Science-side mechanism between them and pretending otherwise
# would be six sabotages dressing up one fact.

_MALFORMED_EXIT = Sabotage(
    module="world/verify.py",
    before='    if type(view) is MalformedView:\n        return _report("malformed", bound=labels,',
    after='    if False:\n        return _report("malformed", bound=labels,',
)
"""Step 1 no longer stops on a malformed chain: the view falls through to the
well-formed branch, which refuses it as a type error rather than judging it."""

_DEFECT_REF = Sabotage(
    module="world/verify.py",
    before='        ref=defect.subject if defect.subject is not None else "chain",',
    after='        ref="chain",',
)
"""The malformed finding stops naming the offending entry."""

_DEFECT_DETAIL = Sabotage(
    module="world/verify.py",
    before='        detail=f"kind={defect.kind}",',
    after='        detail="kind=malformed",',
)
"""The malformed finding stops naming the defect *class* — the exact thing cut
8 §5's obligation 1 requires a defect arm to assert."""

_MALFORMED_JUDGES_ANCHORS = Sabotage(
    module="world/verify.py",
    before='        return _report("malformed", bound=labels, findings=tuple(findings) + (_defect_finding(view.defect),))',
    after=(
        '        return _report(\n'
        '            "malformed",\n'
        '            anchored_through="a head no step judged",\n'
        "            bound=labels,\n"
        "            findings=tuple(findings) + (_defect_finding(view.defect),),\n"
        "        )"
    ),
)
"""The malformed exit states an anchor judgment it never made — L9's ordering
claim inverted."""

_ANCHOR_UNREACHABLE = Sabotage(
    module="world/verify.py",
    before="        elif anchor.head not in positions:",
    after="        elif False:",
)
"""An anchored head this chain's ancestry cannot reach no longer refutes."""

_UNREACHABLE_REF = Sabotage(
    module="world/verify.py",
    before='                    code="anchor-unreachable",\n                    ref=anchor.head,',
    after='                    code="anchor-unreachable",\n                    ref="chain",',
)
"""The refutation stops naming the unreachable anchored head."""

_ANCHOR_GENESIS_NEVER = Sabotage(
    module="world/verify.py",
    before="        if anchor.genesis != chain_genesis:",
    after="        if False:",
)
"""A head anchored under another genesis stops reading as a replacement."""

_ANCHOR_GENESIS_ALWAYS = Sabotage(
    module="world/verify.py",
    before="        if anchor.genesis != chain_genesis:",
    after="        if True:",
)
"""...and the mirror of it: every anchor read as a replacement, so a corpus
replacement is reported by the wrong mechanism."""

_SUBJECT_FILTER = Sabotage(
    module="world/verify.py",
    before="            if anchor.subject != subject:",
    after="            if False:",
)
"""The subject filter stops filtering: one corpus's anchors pool with another's,
which is the elimination-matching L4 forbids."""

_ELIGIBILITY = Sabotage(
    module="world/verify.py",
    before='            if kind == "world" and anchor.provenance != "supplied-export":',
    after="            if False:",
)
"""L11's carrier-specific eligibility collapses: an in-root epoch anchors the
world chain."""

_UNBOUND_EXIT = Sabotage(
    module="world/verify.py",
    before='    if not bound:\n        return _report(\n            "unresolvable",\n            unanchored_tail=digests,',
    after='    if False:\n        return _report(\n            "unresolvable",\n            unanchored_tail=digests,',
)
"""An empty observer set stops being `unresolvable` and reaches replay, which
turns "nothing anchors this" into a verdict."""

_PENDING_EXIT = Sabotage(
    module="world/verify.py",
    before='    if pending:\n        return _report(\n            "unresolvable",\n            anchored_through=anchored_through,',
    after='    if False:\n        return _report(\n            "unresolvable",\n            anchored_through=anchored_through,',
)
"""Step 3 stops deciding: a pending registration reaches replay, and the
copied-root state is inferred from disk after all."""

_ABSENT_REFUTES = Sabotage(
    module="world/verify.py",
    before='        if bound:\n            return _report("refuted", bound=labels, findings=tuple(findings) + _absence_findings(bound))',
    after='        if False:\n            return _report("refuted", bound=labels, findings=tuple(findings) + _absence_findings(bound))',
)
"""A wholly absent chain stops refuting against a surviving anchor — kernel
§8.7's detectable journal removal, undone."""

_ABSENCE_REF = Sabotage(
    module="world/verify.py",
    before='            code="anchor-chain-absent",\n            ref=anchor.head,',
    after='            code="anchor-chain-absent",\n            ref="chain",',
)
"""The removal finding stops naming the head that no longer exists."""

_COMMITTED_ONLY = Sabotage(
    module="world/verify.py",
    before="        entry.registration for entry in view.entries if type(entry) is SettledEntryView and entry.committed",
    after="        entry.registration for entry in view.entries if type(entry) is SettledEntryView",
)
"""Settlement stops gating the transition: a rolled-back registration replays as
though it had committed."""

_ABSENCE_AGREES = Sabotage(
    module="world/verify.py",
    before="        if modeled.get(path, absent_state) != scanned.get(path, absent_state)",
    after=(
        "        if scanned.get(path, absent_state) != absent_state\n"
        "        and modeled.get(path, absent_state) != scanned.get(path, absent_state)"
    ),
)
"""A path the timeline produced and the disk has lost stops disagreeing — the
raw deletion the head comparison exists to catch."""

_EXTENT_NO_ANCHOR = Sabotage(
    module="world/verify.py",
    before="    top = max(placed)\n    return digests[top], digests[top + 1 :]",
    after="    return None, digests",
)
"""The maximal anchored head is never reported, so `anchored-through` says
nothing about a chain that is genuinely anchored."""

_EXTENT_NO_RESIDUE = Sabotage(
    module="world/verify.py",
    before="    return digests[top], digests[top + 1 :]",
    after="    return digests[top], ()",
)
"""L5's residue is dropped: the report claims an anchor covers the whole chain."""

_GENESIS_FORM = Sabotage(
    module="world/verify.py",
    before="    except ValueError as caught:\n        return _genesis_defect(genesis, str(caught)), None",
    after="    except ValueError:\n        return None, None",
)
"""An undecodable or wrong-form genesis payload stops being malformed."""

_PRESENTED_MANIFEST = Sabotage(
    module="world/verify.py",
    before="        if presented.corpus_id != subject.corpus_id:  # pyright: ignore[reportAttributeAccessIssue]",
    after="        if False:",
)
"""A manifest re-minted to another corpus stops being reported as a mismatch."""

_BOUND_DROPS_THE_HEAD = Sabotage(
    module="world/verify.py",
    before='        f"subject={_subject_label(anchor.subject)} genesis={anchor.genesis} head={anchor.head}"',
    after='        f"subject={_subject_label(anchor.subject)} genesis={anchor.genesis}"',
)
"""The observer bound stops stating which head each admitted anchor claimed."""

_NO_INCOMPARABLE_PAIR = Sabotage(
    module="world/verify.py",
    before="    for anchor in unplaced:\n        for other in unplaced:",
    after="    for anchor in ():\n        for other in unplaced:",
)
"""Two mutually incomparable anchored heads stop being stated as a pair."""

_INTENT_INVENTORY = Sabotage(
    module="world/verify.py",
    before="    intents = tuple(entry.digest for entry in view.entries if type(entry) is IntentEntryView)",
    after="    intents = ()",
)
"""§10.1's deferral stops being stated in the report: a forged intent beyond the
anchor is carried by nothing."""

_NO_REMOVAL_FINDING = Sabotage(
    module="world/verify.py",
    before="                findings.extend(_removal_findings(path, entry.txid, held))",
    after="                pass  # a logged removal draws no finding",
)
"""Logged becomes permitted: a committed removal of a registered record is no
longer reported at all."""

_NO_CLASSIFICATION = Sabotage(
    module="world/verify.py",
    before="    resolved = held.get(path)",
    after="    resolved = None",
)
"""Held historical bytes stop resolving, so no removal is ever classified."""

_CLASSIFIES_ANY_COPY = Sabotage(
    module="world/verify.py",
    before="    resolved = held.get(path)",
    after="    resolved = held.get(path) or next(iter(held.values()), None)",
)
"""...and the opposite failure: a held copy claiming *another* record classifies
this removal, which is the honest absence L13 turns on."""

_HISTORY_KEY_FORM = Sabotage(
    module="world/verify.py",
    before="        if not CONTENT_HASH.fullmatch(key):",
    after="        if False:",
)
"""A `history` key outside the content-hash form stops refusing the act."""

_STORE_REFUSAL = Sabotage(
    module="world/verify.py",
    before="    raise StoreSubjectUnsupported(",
    after="    raise TypeError(  # not the contracted refusal",
)
"""The store subject stops refusing with the contracted error."""

_SECOND_SUMMARY_MODEL = Sabotage(
    module="world/verify.py",
    before="def registered_surface_paths(root: Path, kind: RootKind) -> tuple[str, ...]:",
    after=(
        "class FileState:\n"
        '    """A second summary model, minted above the composition root."""\n\n'
        "    def __init__(self, content_hash: str) -> None:\n"
        "        self.content_hash = content_hash\n\n\n"
        "def registered_surface_paths(root: Path, kind: RootKind) -> tuple[str, ...]:"
    ),
)
"""L12's one state vocabulary forks: the world layer mints a state class."""

_AUDIT_READS_DETACHED = Sabotage(
    module="world/verify.py",
    before="        view = seam.inspect_registered(root)\n        presented = _presented_identity(config, root_kind, root)",
    after="        view = seam.inspect_detached(root)\n        presented = _presented_identity(config, root_kind, root)",
)
"""The audit consumes the wrong inspection mode — §2.1's contract, and the half
of D10 that says each boundary consumes the mode it is contracted to."""

_ARRIVAL_PENDING_CAUSE = Sabotage(
    module="world/verify.py",
    before='    if report.pending:\n        return "pending"',
    after='    if False:\n        return "pending"',
)
"""§6.2's cause ranking stops reading the report's `pending` field, which is the
one cause no outcome names."""

_ARRIVAL_CAUSE_ORDER = Sabotage(
    module="world/verify.py",
    before="        cause = _arrival_cause(report)\n        if cause is not None:",
    after="        cause = _arrival_cause(report)\n        if False:",
)
"""Report-based refusals stop outranking everything after them."""

_ARRIVAL_SUBJECT_MISMATCH = Sabotage(
    module="world/verify.py",
    before="        if manifest.corpus_id != provenance.parent_corpus_id:",
    after="        if False:",
)
"""§6.3's lifecycle refusal stops firing, so a validated chain is admitted under
another corpus's identity."""

_UNSETTLED_PUBLICATION_ORDERS = Sabotage(
    module="world/verify.py",
    before="        if type(entry) is SettledEntryView and entry.committed and entry.registration in publications:",
    after="        if type(entry) is SettledEntryView and entry.registration in publications:",
)
"""A **rolled-back** publication is read as the moment the epoch was published,
so the archetypal unordered pair answers ordered.

Not `_epochs_ordered`'s final comparison: a rolled-back publication returns
`unordered` from the early exit above it, so closing the comparison alone would
leave the arm's own case untouched — a vacuous sabotage, which is exactly what
this harness exists to refuse."""

_EPOCH_SEQUENCE = Sabotage(
    module="world/verify.py",
    before="    first = _packaging_identity(e1)\n    second = _packaging_identity(e2)",
    after="    sequence = 0  # an epoch sequence number, consulted\n    first = _packaging_identity(e1)\n    second = _packaging_identity(e2)",
)
"""The predicate acquires a sequence number — L8's negative, falsified."""

_BARE_ADMIT = Sabotage(
    module="world/registry.py",
    before="        if type(provenance) is ReplicaOf:\n            raise ReplicaAdmissionRequiresVerification(",
    after="        if False:\n            raise ReplicaAdmissionRequiresVerification(",
)
"""`World.admit` stops refusing a replica, so a bare admit holds a verdict it
never obtained."""

_RETIREMENT_DELETES = Sabotage(
    module="world/registry.py",
    before='            self._executor_factory(self.config.world_root).execute(\n                [CreateOp(f"registry/{digest}.yaml", _record_bytes(status_projection(candidate)))]\n            )',
    after=(
        '            for _prior in sorted((self.config.world_root / "registry").glob("*.yaml")):\n'
        "                _prior.unlink()\n"
        '            self._executor_factory(self.config.world_root).execute(\n'
        '                [CreateOp(f"registry/{digest}.yaml", _record_bytes(status_projection(candidate)))]\n'
        "            )"
    ),
)
"""Retirement stops being append-only."""

_LOG_HEAD_ACCEPTS_A_WORLD = Sabotage(
    module="world/anchors.py",
    before='_LOG_HEAD_SUBJECT_KINDS = frozenset({"corpus", "store"})',
    after='_LOG_HEAD_SUBJECT_KINDS = frozenset({"corpus", "store", "world"})',
)
"""A registry log-head record becomes constructible for a world subject."""

_EXPORT_GENESIS_UNBOUND = Sabotage(
    module="world/anchors.py",
    before=(
        "    if named != world_id:\n"
        '        raise WorldIdMismatch(f"{world_root}: the chain genesis names world_id {named!r}, '
        'not {world_id!r}")'
    ),
    after=(
        "    if False:\n"
        '        raise WorldIdMismatch(f"{world_root}: the chain genesis names world_id {named!r}, '
        'not {world_id!r}")'
    ),
)
"""The exported subject stops binding to the **genesis**.

Closing the configuration comparison instead would be vacuous: the genesis check
below it reaches the same `WorldIdMismatch` by a second route, and an arm that
mutated one alone would score sound on a defect the code still catches."""

_NO_COLLISION = Sabotage(
    module="world/anchors.py",
    before='        if target.read_bytes() != content:\n            raise LogHeadCollision(f"{target}: a content-addressed log-head record path holds different bytes")\n        return None',
    after="        return None",
)
"""A same-name record holding different bytes stops being a collision."""

_INTENT_ENTRY_RECORDS_GC = Sabotage(
    module="world/logmodel.py",
    before="class IntentEntryView:\n    digest: str\n    payload: bytes",
    after="class IntentEntryView:\n    digest: str\n    payload: bytes\n    preimage_gc: bool = False",
)
"""An entry class acquires a preimage-collection member — the taxonomy width
L13u5 declares, falsified."""

_UNREGISTERED_WRITE = Sabotage(
    module="corpus.py",
    before="def _operation_lock_for(root: Path) -> OperationLock:",
    after=(
        "def _unregistered_write(root: Path, path: str, content: bytes) -> None:\n"
        '    """A cooperative mutation path that skips registration."""\n'
        "    (root / path).write_bytes(content)\n\n\n"
        "def _operation_lock_for(root: Path) -> OperationLock:"
    ),
)
"""The write API gains a path to a registered surface that the engine never
sees."""

_STATES_NOT_DECODED = Sabotage(
    module="root.py",
    before="    return tuple((path, state_from_json(state)) for path, state in surface)",
    after="    return tuple((path, state) for path, state in surface)",
)
"""The chain's `PathStateJSON` stops being decoded, so the two atoms forms never
meet in one comparable value."""

_RESERVED_LEAF_ALLOWED = Sabotage(
    module="root.py",
    before="            if component.startswith(SCRATCH_SIGIL):",
    after="            if False:",
)
"""A cooperative plan may name the chain's own leaf, so appending the log
becomes a registrable act."""

_PENDING_MAPPINGS_DRIFT = Sabotage(
    module="root.py",
    before=(
        "            # The same gate, before the intent entry is appended: the two\n"
        "            # mappings state one engine contract and must not drift.\n"
        "            raise ExecutionError(str(caught), index=None, applied=0) from caught"
    ),
    after=(
        "            # The same gate, before the intent entry is appended: the two\n"
        "            # mappings state one engine contract and must not drift.\n"
        "            raise ExecutionError(str(caught), index=None, applied=None) from caught"
    ),
)
"""The **operation port's** pending mapping stops proving that nothing was
applied, so the two Science maps of one engine contract disagree.

Pointed at the second mapping rather than the executor's: the executor's is the
one an earlier draft armed, and the production comment beside this one says the
two "must not drift" — a claim nothing falsified until the arm asserted them
equal. A mutation of the executor's mapping fails the same check by the same
assertion."""

_OPEN_WORLD_MIRROR = Sabotage(
    module="root.py",
    before="    mirror_id = _load_world_mirror(config.world_root)\n    if mirror_id != config.world_id:",
    after="    mirror_id = _load_world_mirror(config.world_root)\n    if False:",
)
"""`open_world` stops refusing the `world.yaml` mirror disagreement."""

_OPEN_WORLD_GENESIS = Sabotage(
    module="root.py",
    before="    _require_world_genesis(config.world_root, head.genesis_payload, config.world_id)\n    return World(",
    after="    return World(",
)
"""`open_world` stops reading the genesis, so an edited configuration opens a
world the chain was never minted under."""


# --- the 53 declarations ------------------------------------------------------


CUT8_ARMS: tuple[Arm, ...] = (
    Arm(
        row="L1u1",
        asserts=(
            "no cooperative mutation path skips registration, asserted over the composition surface: "
            "`science.root` is the only atoms importer, every registered-surface mutation flows through "
            "`run_transaction`, and genesis registration and intent append are protocol entries rather "
            "than application mutations"
        ),
        sabotage=_UNREGISTERED_WRITE,
        checks=("test_capability_boundary.py::test_no_cooperative_mutation_path_skips_registration",),
    ),
    Arm(
        row="L2u1",
        asserts=(
            "a rolled-back registered creation leaves the record's absence **not** refuted — no transition "
            "— with the fabricated entry asserted `settled(rolled-back)` and the path asserted absent"
        ),
        sabotage=_COMMITTED_ONLY,
        checks=("test_world_log_replay.py::test_rolled_back_creation_absence_is_not_refuted",),
    ),
    Arm(
        row="L2u2",
        asserts="a committed creation whose record is then raw-deleted is refuted at replay",
        sabotage=_ABSENCE_AGREES,
        checks=("test_world_log_replay.py::test_committed_creation_raw_deleted_is_refuted",),
    ),
    Arm(
        row="L2u3",
        asserts="two settlements for one registration are malformed at step 1, the finding naming the entry",
        sabotage=_DEFECT_REF,
        checks=("test_world_log_evaluator.py::test_duplicate_settlement_is_malformed_at_step_one",),
    ),
    Arm(
        row="L2u4",
        asserts=(
            "a copied root's pending entry is unresolvable at step 3 in **both** variants — the copy caught "
            "before apply and after apply — never refuted as a disk mismatch and never inferred from disk"
        ),
        sabotage=_PENDING_EXIT,
        checks=("test_world_log_evaluator.py::test_copied_root_pending_is_unresolvable_in_both_variants",),
    ),
    Arm(
        row="L2u5",
        asserts=(
            "**partial.** Further mutation on a pending root is refused through the engine's shared gate, "
            "mapped to a refusal that proves nothing was applied, over two of the three commands the frozen "
            "clause enumerates — `run_transaction` and `append_intent`, whose two Science mappings are "
            "asserted equal. Unrun: `register_root`'s existing-chain arm, which both initializers call bare, "
            "so no Science mapping stands there to falsify"
        ),
        sabotage=_PENDING_MAPPINGS_DRIFT,
        checks=("test_world_arrival.py::test_pending_root_refuses_further_mutation_via_the_gate",),
    ),
    Arm(
        row="L3u1",
        asserts=(
            "truncation to a valid prefix behind the anchored head is refuted at step 2, the finding naming "
            "the unreachable anchored head"
        ),
        sabotage=_UNREACHABLE_REF,
        checks=(
            "test_world_log_evaluator.py::test_valid_prefix_truncation_refutes_naming_the_unreachable_head",
        ),
    ),
    Arm(
        row="L3u2",
        asserts=(
            "an interior entry deleted or rewritten is malformed at step 1, the finding naming the exact "
            "defect class, and the chain is never silently validated"
        ),
        sabotage=_DEFECT_DETAIL,
        checks=("test_world_log_evaluator.py::test_interior_damage_is_malformed",),
    ),
    Arm(
        row="L3u3",
        asserts="a sibling branch beside the retained original is malformed at step 1, never a silent fork",
        sabotage=_MALFORMED_EXIT,
        checks=("test_world_log_evaluator.py::test_sibling_branch_is_malformed",),
    ),
    Arm(
        row="L3u4",
        asserts="an orphan entry is malformed at step 1, never silently validated",
        sabotage=_MALFORMED_EXIT,
        checks=("test_world_log_evaluator.py::test_orphan_entry_is_malformed",),
    ),
    Arm(
        row="L4u1",
        asserts=(
            "chain deletion against a surviving registry log-head record is refuted — kernel §8.7's "
            "detectable journal removal — the finding naming the head that no longer exists"
        ),
        sabotage=_ABSENCE_REF,
        checks=("test_world_log_evaluator.py::test_chain_deletion_refutes_against_a_registry_anchor",),
    ),
    Arm(
        row="L4u2",
        asserts=(
            "with two anchored corpora and one arriving chainless the subject binding refutes exactly the "
            "arriving one and never the sibling — never by elimination or by opaque genesis digest alone"
        ),
        sabotage=_SUBJECT_FILTER,
        checks=("test_world_log_evaluator.py::test_two_anchored_corpora_refute_exactly_the_chainless_one",),
    ),
    Arm(
        row="L4u3",
        asserts=(
            "a raw manifest re-mint A → B with the chain present, verified selecting A: A-bound anchors stay "
            "admitted, the mismatch is reported separately, and replay refutes the edit"
        ),
        sabotage=_PRESENTED_MANIFEST,
        checks=("test_world_log_evaluator.py::test_manifest_remint_reports_mismatch_and_replay_refutes",),
    ),
    Arm(
        row="L4u4",
        asserts=(
            "an edited configuration `world_id` against a present world chain yields a subject-mismatch "
            "finding **and** `open_world`'s operation refusal, the chain verdict derived independently"
        ),
        sabotage=_OPEN_WORLD_GENESIS,
        checks=(
            (
                "test_world_log_audit.py::TestTheWorldMirrorIsReportedAndNeverRaised::"
                "test_edited_world_configuration_mismatch_and_refusal"
            ),
        ),
    ),
    Arm(
        row="L4u5",
        asserts=(
            "a self-consistent alternative chain under the same constant genesis and `corpus_id` is refuted "
            "through anchored-head unreachability, never through a genesis comparison"
        ),
        sabotage=_ANCHOR_GENESIS_ALWAYS,
        checks=("test_world_log_evaluator.py::test_same_genesis_alternative_chain_refutes_by_ancestry",),
    ),
    Arm(
        row="L4u6",
        asserts=(
            "a W1 head exported and the local world rewritten to W2: verification selecting W1 is refuted as "
            "removal/replacement, while selecting W2 is a separate-world audit and never a verdict about W1"
        ),
        sabotage=_ANCHOR_GENESIS_NEVER,
        checks=("test_world_log_audit.py::test_exported_w1_head_refutes_rewritten_world",),
    ),
    Arm(
        row="L4u7",
        asserts=(
            "chain deletion **plus** a manifest re-mint as B, verified selecting A with A's anchor supplied, "
            "is refuted as removal — the presented manifest never discards the anchor into empty-set "
            "unresolvable"
        ),
        sabotage=_ABSENT_REFUTES,
        checks=(
            "test_world_log_evaluator.py::test_deletion_plus_remint_refutes_as_removal_under_selected_subject",
        ),
    ),
    Arm(
        row="L5u1",
        asserts=(
            "a consistent tail-and-surface rewrite beyond the maximal anchor validates, undetected — the "
            "pinned negative, with the rewrite asserted to differ byte-wise over at least one entry"
        ),
        sabotage=_EXTENT_NO_ANCHOR,
        checks=("test_world_log_replay.py::test_consistent_tail_rewrite_beyond_anchor_validates",),
    ),
    Arm(
        row="L5u2",
        asserts="the report's unanchored-tail extent covers the rewritten span exactly",
        sabotage=_EXTENT_NO_RESIDUE,
        checks=("test_world_log_replay.py::test_unanchored_tail_extent_covers_the_rewrite",),
    ),
    Arm(
        row="L7u1",
        asserts=(
            "a `fulfills` naming a missing intent, or a present entry that is not one, is malformed at step 1 "
            "with the exact defect class named"
        ),
        sabotage=_DEFECT_DETAIL,
        checks=(
            "test_world_log_evaluator.py::test_fulfills_naming_missing_or_nonancestor_intent_is_malformed",
        ),
    ),
    Arm(
        row="L7u2",
        asserts=(
            "a second committed registration fulfilling one intent is malformed, classified before any "
            "qualification is attempted"
        ),
        sabotage=_MALFORMED_EXIT,
        checks=("test_world_log_evaluator.py::test_duplicate_committed_fulfillment_is_malformed",),
    ),
    Arm(
        row="L8u1",
        asserts=(
            "E2 orders after E1 iff E2's build-start world head descends from E1's settled publication entry, "
            "with a rolled-back publication answering unordered — asserted by entry class"
        ),
        sabotage=_UNSETTLED_PUBLICATION_ORDERS,
        checks=(
            (
                "test_world_log_audit.py::TestTheOrderedCutsPredicate::"
                "test_epochs_ordered_by_descent_and_unordered_without_settled_publication"
            ),
        ),
    ),
    Arm(
        row="L8u2",
        asserts="epoch sequence numbers are read by nothing — no member carries one and the predicate names none",
        sabotage=_EPOCH_SEQUENCE,
        checks=(
            (
                "test_world_log_audit.py::TestTheOrderedCutsPredicate::"
                "test_epoch_sequence_numbers_are_read_by_nothing"
            ),
        ),
    ),
    Arm(
        row="L9u1",
        asserts=(
            "an old reachable anchor plus a newer anchored head absent from the chain is refuted, never "
            "validated-through-the-old"
        ),
        sabotage=_ANCHOR_UNREACHABLE,
        checks=("test_world_log_evaluator.py::test_old_anchor_never_validates_past_a_missing_newer_head",),
    ),
    Arm(
        row="L9u2",
        asserts="two mutually incomparable anchored heads for one genesis are refuted, stated once as a pair",
        sabotage=_NO_INCOMPARABLE_PAIR,
        checks=("test_world_log_evaluator.py::test_incomparable_anchored_heads_refute",),
    ),
    Arm(
        row="L9u3",
        asserts="the empty observer set is unresolvable with the observer bound recorded, replay not reached",
        sabotage=_UNBOUND_EXIT,
        checks=("test_world_log_evaluator.py::test_empty_observer_set_is_unresolvable_with_bound_recorded",),
    ),
    Arm(
        row="L9u4",
        asserts="`anchored-through` and the observer set are report fields, present in every outcome",
        sabotage=_BOUND_DROPS_THE_HEAD,
        checks=("test_world_log_evaluator.py::test_anchored_through_and_observer_set_are_report_fields",),
    ),
    Arm(
        row="L9u5",
        asserts="malformed structure stops evaluation before any anchor judgment",
        sabotage=_MALFORMED_JUDGES_ANCHORS,
        checks=("test_world_log_evaluator.py::test_malformed_structure_stops_before_anchor_judgment",),
    ),
    Arm(
        row="L10u1",
        asserts=(
            "a copy presenting the parent genesis under a fresh `corpus_id` manifest refuses `SubjectMismatch` "
            "— the chain refuses to verify under the new identity, reached through the arrival act"
        ),
        sabotage=_ARRIVAL_SUBJECT_MISMATCH,
        checks=(
            (
                "test_world_arrival.py::TestTheRefusalOrdering::"
                "test_fresh_manifest_over_parent_chain_refuses_subject_mismatch"
            ),
        ),
    ),
    Arm(
        row="L11u1",
        asserts=(
            "an epoch stored inside the world root is ineligible for the world subject while byte-identical "
            "content supplied as an export is eligible, and the same stored epoch anchors a corpus"
        ),
        sabotage=_ELIGIBILITY,
        checks=(
            (
                "test_world_log_evaluator.py::"
                "test_in_root_epoch_ineligible_for_world_subject_but_eligible_for_corpus"
            ),
        ),
    ),
    Arm(
        row="L11u2",
        asserts=(
            "a registry log-head record carrying a `world` subject is unconstructible through the anchor act "
            "and never accepted as an anchor"
        ),
        sabotage=_LOG_HEAD_ACCEPTS_A_WORLD,
        checks=("test_world_log_codecs.py::test_world_subject_registry_record_is_unconstructible",),
    ),
    Arm(
        row="L11u3",
        asserts=(
            "coordinated truncation of world chain, registry and in-root epochs with no exported holder is "
            "undetected — the surviving-observer negative, with all three carriers asserted truncated"
        ),
        sabotage=_UNBOUND_EXIT,
        checks=(
            "test_world_log_audit.py::test_coordinated_truncation_without_exported_holder_is_undetected",
        ),
    ),
    Arm(
        row="L11u4",
        asserts="the same coordinated truncation with one exported epoch supplied is refuted",
        sabotage=_UNREACHABLE_REF,
        checks=("test_world_log_audit.py::test_coordinated_truncation_with_one_exported_epoch_refutes",),
    ),
    Arm(
        row="L12u1",
        asserts=(
            "each typed state class — absence, directory, symlink target, mode — round-trips through "
            "registration fingerprints and replay; a subset pass is malformed declaration content"
        ),
        sabotage=_STATES_NOT_DECODED,
        checks=("test_world_log_replay.py::test_all_four_state_classes_round_trip",),
    ),
    Arm(
        row="L12u2",
        asserts=(
            "no second summary model: Science fingerprints exclusively through the atoms capture command, "
            "asserted over the package surface"
        ),
        sabotage=_SECOND_SUMMARY_MODEL,
        checks=("test_capability_boundary.py::test_science_fingerprints_only_through_the_capture_command",),
    ),
    Arm(
        row="L12u3",
        asserts="appending the log is not recursively registered",
        sabotage=_RESERVED_LEAF_ALLOWED,
        checks=("test_world_log_replay.py::test_log_appends_are_not_recursively_registered",),
    ),
    Arm(
        row="L12u4",
        asserts=(
            "a raw edit of the log path within the anchored prefix is caught at step 1 as interior damage or "
            "at step 2 as prefix truncation"
        ),
        sabotage=_ANCHOR_UNREACHABLE,
        checks=(
            "test_world_log_evaluator.py::test_raw_log_edit_within_anchored_prefix_is_malformed_or_refuted",
        ),
    ),
    Arm(
        row="L12u5",
        asserts=(
            "a structurally valid raw append beyond the maximal anchor — most sharply a forged intent — "
            "passes steps 1 and 2 and is reported as L5's residue"
        ),
        sabotage=_INTENT_INVENTORY,
        checks=("test_world_log_evaluator.py::test_valid_raw_append_beyond_anchor_passes_as_the_residue",),
    ),
    Arm(
        row="L13u1",
        asserts=(
            "a cooperatively logged verification removal is present in the replayed timeline **and** draws the "
            "policy finding naming the deleted record"
        ),
        sabotage=_NO_REMOVAL_FINDING,
        checks=(
            "test_world_log_replay.py::test_cooperative_verification_removal_is_in_timeline_with_finding",
        ),
    ),
    Arm(
        row="L13u2",
        asserts=(
            "where supplied `history` bytes resolve, the removal is classified as a failing verification's and "
            "the finding names the matched digest (the match being path-based, R16)"
        ),
        sabotage=_NO_CLASSIFICATION,
        checks=(
            "test_world_log_replay.py::test_failing_classification_resolves_through_history_naming_digest",
        ),
    ),
    Arm(
        row="L13u3",
        asserts=(
            "with no copy held the deletion is still detected and the semantic classification is honestly "
            "absent — never guessed from a copy claiming another record"
        ),
        sabotage=_CLASSIFIES_ANY_COPY,
        checks=("test_world_log_replay.py::test_without_history_deletion_detected_classification_absent",),
    ),
    Arm(
        row="L13u4",
        asserts="corpus retirement appends a status event and deletes nothing",
        sabotage=_RETIREMENT_DELETES,
        checks=(
            "test_world_arrival.py::TestWhatIsAdmitted::test_retirement_appends_status_and_deletes_nothing",
        ),
    ),
    Arm(
        row="L13u5",
        asserts=(
            "preimage-blob GC appears in no chain, asserted as a taxonomy fact over the entry classes, with "
            "the declaration stating that width"
        ),
        sabotage=_INTENT_ENTRY_RECORDS_GC,
        checks=("test_world_log_codecs.py::test_no_entry_class_records_preimage_gc",),
    ),
    Arm(
        row="D1",
        asserts=(
            "an undecodable or wrong-form genesis payload, or a non-empty baseline, is malformed before anchor "
            "evaluation; a valid world genesis naming a different `world_id` is subject-mismatch, never "
            "malformed (spec §4.2, §1.3)"
        ),
        sabotage=_GENESIS_FORM,
        checks=(
            "test_world_log_evaluator.py::test_genesis_form_malformation_and_world_id_mismatch_split",
        ),
    ),
    Arm(
        row="D2",
        asserts=(
            "arrival causes rank malformed > refuted > pending > chainless, derived from report fields and "
            "not from precedence steps (spec §6.2)"
        ),
        sabotage=_ARRIVAL_PENDING_CAUSE,
        checks=(
            "test_world_arrival.py::TestTheArrivalCauses::test_arrival_cause_ranking_from_report_fields",
        ),
    ),
    Arm(
        row="D3",
        asserts=(
            "`World.admit` refuses `ReplicaOf` with `ReplicaAdmissionRequiresVerification`; `admit_arrival` "
            "commits through the same admission core and the record's identity is unamended (spec §6.2)"
        ),
        sabotage=_BARE_ADMIT,
        checks=(
            "test_world_arrival.py::TestWhatIsAdmitted::test_bare_admit_refusal_and_shared_core_identity",
        ),
    ),
    Arm(
        row="D4",
        asserts=(
            "report-based refusals outrank the subject-mismatch refusal, and that refusal precedes the "
            "admission transaction (spec §6.3)"
        ),
        sabotage=_ARRIVAL_CAUSE_ORDER,
        checks=(
            (
                "test_world_arrival.py::TestTheRefusalOrdering::"
                "test_refusal_ordering_report_causes_then_mismatch_then_admission"
            ),
        ),
    ),
    Arm(
        row="D5",
        asserts=(
            "`open_world`'s `world.yaml` mirror-agreement check refuses on mismatch, and the world audit "
            "remains callable on exactly the worlds `open_world` refuses (spec §6.1, §6.3)"
        ),
        sabotage=_OPEN_WORLD_MIRROR,
        checks=(
            (
                "test_world_log_audit.py::TestTheWorldMirrorIsReportedAndNeverRaised::"
                "test_mirror_branch_refuses_open_world_and_audit_stays_callable"
            ),
        ),
    ),
    Arm(
        row="D6",
        asserts=(
            "the log-head and head-artifact codecs round-trip the store arm, the evaluator refuses "
            "`StoreSubjectUnsupported`, and neither act's signature can spell a store (spec §3.1, §10.2)"
        ),
        sabotage=_STORE_REFUSAL,
        checks=("test_world_log_codecs.py::test_store_subject_shape_only_across_codecs_and_evaluator",),
    ),
    Arm(
        row="D7",
        asserts=(
            "`export_head_artifact` refuses a `World(world_id)` disagreeing with configuration or genesis, a "
            "corpus subject resolves under the exactly-one-carrier rule, the function takes no actor and "
            "writes nothing, and the bytes decode under `science.head-artifact.v1` (spec §3.2)"
        ),
        sabotage=_EXPORT_GENESIS_UNBOUND,
        checks=("test_world_anchor_act.py::test_export_binds_subject_and_takes_no_actor",),
    ),
    Arm(
        row="D8",
        asserts=(
            "`AnchorSubjectUnknown` for an unknown `corpus_id`, `AnchorTargetUnresolvable` for zero or "
            "multiple carriers, byte-identical re-anchoring idempotent with no transaction, a same-name "
            "different-bytes record a collision, and terminal corpora anchorable (spec §3.1, §3.3)"
        ),
        sabotage=_NO_COLLISION,
        checks=("test_world_anchor_act.py::test_anchor_act_refusals_idempotency_and_terminal_corpora",),
    ),
    Arm(
        row="D9",
        asserts=(
            "a malformed `history` key, or bytes not hashing to their key, refuses the act; keys are exactly "
            "`sha256:<64 lowercase hex>`; every classified finding names the matched digest (spec §5.3)"
        ),
        sabotage=_HISTORY_KEY_FORM,
        checks=(
            "test_world_log_replay.py::test_history_validation_refusals_and_digest_named_findings",
        ),
    ),
    Arm(
        row="D10",
        asserts=(
            "audit and arrival share the one read-only evaluator and no third path evaluates; the staging leaf "
            "is never a foreign-leaf defect; `MalformedChain` carries one deterministic first defect; detached "
            "mode requires no metadata root (spec §2.1, §4.1, §6.1–§6.2)"
        ),
        sabotage=_AUDIT_READS_DETACHED,
        checks=("test_world_log_audit.py::test_one_evaluator_one_inspection_contract",),
    ),
)


# --- cut 8 §5's obligation 1, declared per unit --------------------------------


FABRICATION_BY_UNIT: dict[str, tuple[str, ...]] = {
    "L2u1": ("rolled_back_creation",),
    "L2u2": ("populated_corpus",),
    "L2u3": ("duplicate_settlement",),
    "L2u4": ("pending_before_apply", "pending_after_apply"),
    "L3u1": ("truncated_prefix",),
    "L3u2": ("interior_deleted", "interior_rewritten"),
    "L3u3": ("sibling_branch",),
    "L3u4": ("orphan_entry",),
    "L4u1": ("deleted_chain",),
    "L4u2": ("settled_corpus",),
    "L4u3": ("manifest_remint",),
    "L4u5": ("alternative_chain",),
    "L4u6": ("rewritten_world",),
    "L4u7": ("deletion_plus_remint",),
    "L5u1": ("rewritten_tail",),
    "L5u2": ("rewritten_tail",),
    "L7u1": ("fulfills_missing_intent", "fulfills_non_intent"),
    "L7u2": ("duplicate_fulfillment",),
    "L9u1": ("settled_corpus",),
    "L9u2": ("settled_corpus",),
    "L9u3": ("settled_corpus",),
    "L9u4": ("populated_corpus",),
    "L9u5": ("interior_deleted", "populated_corpus"),
    "L11u1": ("settled_world", "settled_corpus"),
    "L11u3": ("coordinated_truncation", "settled_world"),
    "L11u4": ("coordinated_truncation",),
    "L12u1": ("four_state_classes",),
    "L12u3": ("settled_corpus",),
    "L12u4": ("interior_rewritten", "truncated_prefix"),
    "L12u5": ("forged_intent_beyond_the_anchor",),
    "L13u1": ("removed_record",),
    "L13u2": ("removed_record",),
    "L13u3": ("removed_record",),
    "D1": (
        "undecodable_genesis",
        "wrong_form_genesis",
        "populated_baseline",
        "foreign_world_genesis",
    ),
    "D9": ("removed_record",),
}
"""Which catalogued on-disk fabrications each unit's arm judges.

`test_world_log_codecs.CUT8_FABRICATIONS` carries the engine's own verdict over
each, and `test_n2_cut8.py` runs `inspect_chain` over every one of them — so
cut 8 §5's obligation 1 is discharged by the validator rather than by a view
nobody inspected. Units absent from this table judge no chain at all: they are
static claims over the package surface (L1u1, L12u2), codec and taxonomy claims
(L11u2, L13u5, D6), act-level claims that read a *head* rather than a chain
(D7, D8), or the view-level units below.
"""

VIEW_LEVEL_GROUNDS = ("no chain read", "stand-in inspection")
"""The only two grounds on which a declared unit may omit an on-disk chain."""

VIEW_LEVEL_UNITS: dict[str, str] = {
    "L2u5": "no chain read: the engine's pending refusal is injected and the arm judges the mapping",
    "L4u4": "stand-in inspection: the arm's claim is the open-refuses/audit-reports split, not the chain",
    "L8u1": "stand-in inspection: a fabricated world chain, paired with epochs a real build published",
    "L8u2": "stand-in inspection: the same pair, plus a source-level read of the predicate",
    "L10u1": "stand-in inspection: the arm's claim is where the arrival refusal sits, not the chain",
    "L11u2": "no chain read: a codec, an act signature and a carrier factory",
    "L13u4": "no chain read: the arm's claim is that the registry is append-only across a retirement",
    "L13u5": "no chain read: a taxonomy fact over the closed entry-class union",
    "D2": "stand-in inspection: the arm's claim is the cause ranking derived from report fields",
    "D3": "stand-in inspection: the arm's claim is admission identity across the two routes",
    "D4": "stand-in inspection: the arm's claim is the order the three refusals fire in",
    "D5": "stand-in inspection: the arm's claim is the open-refuses/audit-stays-callable split",
    "D6": "no chain read: codecs, the evaluator's store refusal, and two act signatures",
    "D7": "no chain read: the export act reads a head, never a chain",
    "D8": "no chain read: the anchor act reads a head, never a chain",
    "D10": "stand-in inspection: clause 1 counts evaluator calls; clauses 2-4 are already on disk",
}
"""The declared units whose arms rest on a chain **view** handed to a stubbed
seam, rather than on a directory `inspect_chain` can read — with the ground.

Cut 8 §5's obligation 1 cannot be met literally for these, but the reason is
narrower than "no directory exists", and the narrower statement is the honest
one: **the arm's claim does not turn on the chain**. It turns on lock order,
precedence, refusal placement, admission identity, or the count of evaluator
calls, and the stand-in inspection is what lets the arm state that without a
chain standing in the way. Three of them — L10u1, D3, D4 — do run over real
roots with a real executor and could have been converted the way L4u6, L11u3 and
L11u4 were; they were not, because the conversion would rewrite Task 9's
reviewed arrival fixtures without changing what the arms assert. That is a cost,
recorded here rather than argued away.

What `test_n2_cut8.py` runs over them instead is the obligation's *purpose*,
**per unit**: each stand-in unit supplies the views its arm hands to the seam,
and a structural well-formedness predicate reads them — pinned against the
engine on the three defect classes a linearized view can express. So a
fabrication still cannot smuggle in the malformation it claims not to have, and
a unit cannot be excused by wording and checked by nothing.
"""
