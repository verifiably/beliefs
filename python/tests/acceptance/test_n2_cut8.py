"""Cut 8's declaration accounting, its N2 audit, and its declaration-time obligations.

Three things, in the cut-7 pattern:

1. **The N2 audit.** Every one of the 53 arms in `n2_arms_cut8` is applied to a
   copy of the package and its named check is run one at a time; `vacuous`,
   `mixed`, `uncollected` and `stale` are reported as **malformed contract
   content** rather than as failing tests, because the finding is about the
   declaration and not about the code under test.
2. **The inventory.** The 53 units are reconciled against the frozen cut's own
   §3 dispositions and §4 accounting, parsed out of the document rather than
   restated — a table that agreed with a copy of the cut would be agreeing with
   itself.
3. **Cut 8 §5's obligations 1–6 and both §6 freeze obligations**, as
   declaration-time checks. Obligation 7 (summary-line accounting) is the
   results record's and is homed at Task 12, where the counts are claimed.

**Obligation 1 is discharged two ways, and the split is stated.** Every arm that
judges a chain on disk names its builder in `FABRICATION_BY_UNIT`; those
builders are catalogued in `test_world_log_codecs.CUT8_FABRICATIONS` with the
engine's own verdict, and this module runs `inspect_chain` over each. The arms
that hand a chain *view* to a stubbed seam cannot meet the obligation literally
— there is no directory to inspect, which is the point of a stand-in inspection
— so they are named in `VIEW_LEVEL_UNITS` with a reason, and the obligation's
*purpose* is run over them instead: a structural well-formedness predicate over
the linearization, pinned against the engine on the three defect classes a view
can express.
"""

from __future__ import annotations

import re
import subprocess
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from n2_arms import (
    CLASS_NODE_BY_CONSTRUCTION,
    MIXED_BY_CONSTRUCTION,
    STALE_BY_CONSTRUCTION,
    UNCOLLECTED_BY_CONSTRUCTION,
    VACUOUS_BY_CONSTRUCTION,
    Arm,
)
from n2_arms_cut5 import CUT5_ARMS
from n2_arms_cut6 import CUT6_ARMS
from n2_arms_cut7 import CUT7_ARMS
from n2_arms_cut8 import (
    CUT8_ARMS,
    FABRICATION_BY_UNIT,
    LABELED_UNITS,
    ROW_UNITS,
    VIEW_LEVEL_GROUNDS,
    VIEW_LEVEL_UNITS,
)
from test_n2 import MalformedArm, audit, baseline
from test_world_arrival import pending_view
from test_world_log_audit import surfaced, world_chain
from test_world_log_codecs import (
    ABSENT_CHAIN,
    CUT8_CORPUS_ID,
    CUT8_FABRICATIONS,
    CUT8_SIBLING_ID,
    IN_ROOT_CARRIERS,
    MANIFEST,
    RECORD,
    capture_at,
    coordinated_truncation,
    corpus_root_at,
    four_state_classes,
    inspected,
    manifest_remint,
    rewritten_tail,
    rolled_back_creation,
    settled_corpus,
)

from science import root as science_root
from science.world import logmodel

WORKERS = 8

REPO_ROOT = Path(__file__).resolve().parents[3]
FROZEN_CUT = REPO_ROOT / "docs" / "designs" / "2026-08-22-conformance-cut-8.md"

CUT8_FREEZE_COMMIT = "117f37e"
"""The commit the cut was frozen at. Cut 7's declarations and runner join the
earlier cuts' frozen set here, pinned at this commit rather than at cut 6's,
because slice 3 begins with them exactly as the freeze left them."""

CUT6_SOURCE_COMMIT = "4a7dc19dd08d8899417d17f7dfee9eb2dbd1318e"

FROZEN_PRIOR_CUT_FILES = {
    "python/tests/n2_arms_cut5.py": CUT6_SOURCE_COMMIT,
    "python/tests/n2_arms_cut6.py": CUT6_SOURCE_COMMIT,
    "python/tools/cut5_acceptance.py": CUT6_SOURCE_COMMIT,
    "python/tools/cut6_acceptance.py": CUT6_SOURCE_COMMIT,
    "python/tests/acceptance/test_n2_cut6.py": "c8c0b12",
    # Cut 7's own declarations and runner. R13 froze `n2_arms_cut7.py` "ever";
    # the runner is frozen on the same footing, and cut 8 chains it as its sole
    # prior-cut prefix rather than editing it.
    "python/tests/n2_arms_cut7.py": CUT8_FREEZE_COMMIT,
    "python/tools/cut7_acceptance.py": CUT8_FREEZE_COMMIT,
}
"""Each prior-cut surface and the commit whose content it must still hold."""


# --- the N2 audit ---------------------------------------------------------------


@pytest.fixture(scope="session")
def findings(tmp_path_factory) -> tuple:
    """The 53 arms, audited against the present tree in both directions."""
    root_path = tmp_path_factory.mktemp("n2-cut8")
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        return tuple(pool.map(lambda pair: audit(pair[1], root_path / f"arm{pair[0]}"), enumerate(CUT8_ARMS)))


def _report(reason: str, findings: tuple, verdict: str) -> None:
    offending = [finding for finding in findings if finding.verdict == verdict]
    if offending:
        raise MalformedArm(
            reason + "\n" + "\n".join(f"  {finding.arm.label}\n    {finding.detail}" for finding in offending)
        )


class TestEveryCut8ArmAssertsSomething:
    def test_no_arm_survives_its_own_sabotage(self, findings):
        _report("these cut-8 arms survive their own sabotage:", findings, "vacuous")

    def test_no_arm_mixes_a_passing_check_with_a_failing_one(self, findings):
        _report("these cut-8 arms mix passing and failing checks:", findings, "mixed")

    def test_no_sabotage_stops_a_check_from_running(self, findings):
        _report("these cut-8 sabotages prevent a check from running:", findings, "uncollected")

    def test_no_sabotage_has_gone_stale(self, findings):
        _report("these cut-8 sabotages no longer match exactly once:", findings, "stale")

    def test_every_check_resolves_and_passes_without_the_sabotage(self):
        every = Arm(
            row="N2",
            asserts="every declared cut-8 check resolves and passes against the real package",
            sabotage=CUT8_ARMS[0].sabotage,
            checks=tuple(dict.fromkeys(check for arm in CUT8_ARMS for check in arm.checks)),
        )
        finding = baseline(every)
        assert finding.verdict == "resolved", finding.detail


# --- the inventory, read out of the frozen cut ----------------------------------

ROW_LINE = re.compile(r"^\| (L\d+) \| ")
UNIT_COUNT = re.compile(r"(?:Selected|\*\*Full\*\*) \((\d+) units?\)")
LABELED_ITEM = re.compile(r"^\d+\. \*\*")
ACCOUNTING_PAIR = re.compile(r"\b(L\d+) (\d+)\b")
ACCOUNTING_TOTAL = re.compile(r"\*\*(\d+) selected \+ (\d+) labeled = (\d+) declaration units\*\*")


def frozen_dispositions() -> dict[str, int]:
    """§3.1's selected-unit count per row, parsed out of the frozen document.

    The disposition bullet can run over several lines — L7's does — so the count
    is looked for in every line after a row's table line until one carries it.
    """
    counts: dict[str, int] = {}
    row: str | None = None
    for line in FROZEN_CUT.read_text(encoding="utf-8").splitlines():
        heading = ROW_LINE.match(line)
        if heading:
            row = heading.group(1)
            continue
        if row is None:
            continue
        found = UNIT_COUNT.search(line)
        if found:
            counts[row] = int(found.group(1))
            row = None
    return counts


def frozen_accounting() -> tuple[dict[str, int], tuple[int, int, int]]:
    """§4's own recount: per-row units, and the selected/labeled/total triple."""
    text = " ".join(FROZEN_CUT.read_text(encoding="utf-8").split())
    section = text.split("## 4. Accounting", 1)[1].split("## 5.", 1)[0]
    per_row = {row: int(count) for row, count in ACCOUNTING_PAIR.findall(section)}
    total = ACCOUNTING_TOTAL.search(section)
    assert total is not None, "§4 states no selected/labeled total"
    return per_row, (int(total.group(1)), int(total.group(2)), int(total.group(3)))


def frozen_labeled_count() -> int:
    text = FROZEN_CUT.read_text(encoding="utf-8")
    section = text.split("### 3.3 Labeled declarations", 1)[1].split("## 4. Accounting", 1)[0]
    return len([line for line in section.splitlines() if LABELED_ITEM.match(line)])


def declared_units() -> tuple[str, ...]:
    return tuple(arm.row for arm in CUT8_ARMS)


def row_of(unit: str) -> str:
    return unit if unit.startswith("D") else unit.split("u")[0]


class TestTheCut8InventoryIsExact:
    def test_the_declared_units_are_unique_and_number_fifty_three(self):
        units = declared_units()
        assert len(units) == 53
        assert len(set(units)) == 53

    def test_the_selected_partition_is_the_frozen_cuts_own(self):
        # Three independent statements of one partition: §3.1's dispositions,
        # §4's recount, and this table. All three must agree.
        dispositions = frozen_dispositions()
        accounting, _total = frozen_accounting()
        assert dispositions == ROW_UNITS
        assert accounting == ROW_UNITS
        assert sum(ROW_UNITS.values()) == 43

    def test_the_selected_and_labeled_totals_are_the_frozen_ones(self):
        _per_row, (selected, labeled, total) = frozen_accounting()
        assert (selected, labeled, total) == (43, 10, 53)
        assert frozen_labeled_count() == 10
        assert len(LABELED_UNITS) == 10

    def test_every_row_carries_exactly_the_units_the_cut_selects(self):
        declared = Counter(row_of(unit) for unit in declared_units() if not unit.startswith("D"))
        assert dict(declared) == ROW_UNITS

    def test_the_labeled_declarations_are_declared_once_each(self):
        labeled = [unit for unit in declared_units() if unit.startswith("D")]
        assert tuple(labeled) == LABELED_UNITS

    def test_l6_is_unread_and_declared_by_nothing(self):
        assert "L6" not in ROW_UNITS
        assert "L6" not in frozen_dispositions()
        assert "**L6** (the genesis baseline reaching pre-log history) is not read" in " ".join(
            FROZEN_CUT.read_text(encoding="utf-8").split()
        )
        assert not [unit for unit in declared_units() if row_of(unit) == "L6"]

    def test_every_arm_has_one_source_mutation_and_one_exact_check_node(self):
        for arm in CUT8_ARMS:
            assert arm.checks, arm.row
            assert len(arm.checks) == len(set(arm.checks)), arm.row
            assert arm.sabotage.before != arm.sabotage.after, arm.row
            assert arm.asserts.strip(), arm.row

    def test_no_declared_arm_names_anything_coarser_than_a_test(self):
        for arm in CUT8_ARMS:
            for check in arm.checks:
                parts = check.split("::")
                assert len(parts) >= 2, check
                assert parts[-1].startswith("test_"), check

    def test_every_sabotage_names_a_present_module_and_applies_exactly_once(self):
        package = Path(science_root.__file__).resolve().parent
        for arm in CUT8_ARMS:
            target = package / arm.sabotage.module
            assert target.is_file(), f"{arm.row}: {arm.sabotage.module} does not exist"
            source = target.read_text(encoding="utf-8")
            assert source.count(arm.sabotage.before) == 1, (
                f"{arm.row}: the sabotage pattern matches {source.count(arm.sabotage.before)} times in "
                f"{arm.sabotage.module}"
            )

    def test_every_check_lives_in_the_file_the_frozen_table_names(self):
        # The declaration's own single-homing: one file per unit, and it is the
        # file the frozen table names. A node that drifted to another module
        # would still resolve, and would silently rehome the claim.
        homes = {check.split("::")[0] for arm in CUT8_ARMS for check in arm.checks}
        assert homes == {
            "test_capability_boundary.py",
            "test_world_anchor_act.py",
            "test_world_arrival.py",
            "test_world_log_audit.py",
            "test_world_log_codecs.py",
            "test_world_log_evaluator.py",
            "test_world_log_replay.py",
        }
        for arm in CUT8_ARMS:
            assert len({check.split("::")[0] for check in arm.checks}) == 1, arm.row


class TestNoPriorCutDeclarationIsRehomedOrEdited:
    def test_the_frozen_prior_cut_files_are_byte_identical_to_their_pinned_versions(self):
        for path, pin in FROZEN_PRIOR_CUT_FILES.items():
            completed = subprocess.run(
                ["git", "-C", str(REPO_ROOT), "diff", "--quiet", pin, "HEAD", "--", path],
                check=False,
            )
            assert completed.returncode == 0, (
                f"{path} has moved since {pin}; cuts 5–7's declarations, runners and pinned audits are "
                "frozen, and cut 8 edits none of them"
            )

    def test_the_guard_covers_cut_7s_declarations_and_runner(self):
        assert "python/tests/n2_arms_cut7.py" in FROZEN_PRIOR_CUT_FILES
        assert "python/tools/cut7_acceptance.py" in FROZEN_PRIOR_CUT_FILES

    def test_no_cut8_arm_claims_a_check_a_prior_cut_declared(self):
        prior = {check for arm in (*CUT5_ARMS, *CUT6_ARMS, *CUT7_ARMS) for check in arm.checks}
        ours = {check for arm in CUT8_ARMS for check in arm.checks}
        assert not prior & ours

    def test_no_prior_cut_arm_claims_a_cut8_unit(self):
        prior = {arm.row for arm in (*CUT5_ARMS, *CUT6_ARMS, *CUT7_ARMS)}
        assert not prior & set(declared_units())


# --- §5's obligation 1: every fabricated chain, inspected ------------------------


@pytest.mark.parametrize(
    ("name", "builder", "defect"), CUT8_FABRICATIONS, ids=[entry[0] for entry in CUT8_FABRICATIONS]
)
def test_every_catalogued_fabrication_is_what_the_engine_says_it_is(tmp_path, name, builder, defect):
    """Cut 8 §5's obligation 1, run by the engine's own validator.

    A well-formed fabrication must inspect **well formed**; a fabrication whose
    point is the defect must carry exactly that one defect class and no other.
    An absent chain is neither, and is marked as such in the catalogue.
    """
    chain = builder(tmp_path / name)
    view = inspected(chain.root)

    if defect is None:
        assert type(view) is logmodel.WellFormedView, f"{name}: {view}"
    elif defect == ABSENT_CHAIN:
        assert view == logmodel.AbsentView(), f"{name}: {view}"
    else:
        assert type(view) is logmodel.MalformedView, f"{name}: {view}"
        assert view.defect.kind == defect, f"{name}: {view.defect.kind}"


class TestTheFabricationCatalogueIsTheDeclarationsOwn:
    def test_every_unit_fabrication_is_catalogued(self):
        catalogued = {name for name, _builder, _defect in CUT8_FABRICATIONS}
        named = {name for names in FABRICATION_BY_UNIT.values() for name in names}
        assert named <= catalogued, sorted(named - catalogued)

    def test_every_catalogued_fabrication_is_claimed_by_a_unit(self):
        # Otherwise the catalogue could pass over the one fabrication a
        # declaration actually rests on, by carrying a different one instead.
        catalogued = {name for name, _builder, _defect in CUT8_FABRICATIONS}
        named = {name for names in FABRICATION_BY_UNIT.values() for name in names}
        assert catalogued == named, sorted(catalogued - named)

    def test_every_declared_unit_states_its_fabrication_or_states_why_not(self):
        units = set(declared_units())
        on_disk = set(FABRICATION_BY_UNIT)
        view_level = set(VIEW_LEVEL_UNITS)
        static = {"L1u1", "L12u2"}
        assert on_disk <= units
        assert view_level <= units
        assert not on_disk & view_level
        assert units - on_disk - view_level == static

    def test_the_view_level_departure_states_a_reason_for_each_unit(self):
        # Two admissible grounds and no third: the arm reads no chain at all, or
        # it hands a view to a stubbed inspection because the stand-in is what
        # lets it state lock order, precedence or refusal placement. Free-text
        # prose would let a fabrication nobody inspected be excused by wording.
        for unit, reason in VIEW_LEVEL_UNITS.items():
            assert reason.startswith(VIEW_LEVEL_GROUNDS), f"{unit}: {reason}"


# --- the purpose of obligation 1, over the view-level fabrications ---------------


def view_defect(view: logmodel.WellFormedView) -> str | None:
    """The engine's structural taxonomy, over what a *linearization* can express.

    `inspect_chain` reads a directory; a `WellFormedView` is what it produced,
    so most of the taxonomy — a sibling branch, a missing predecessor, a
    name/bytes mismatch — is unspellable in one by construction. What a view can
    still get wrong is the part this reimplements: the genesis's identity and
    position, the tip, settlement pairing and duplication, and `fulfills`
    resolution. `test_the_view_predicate_agrees_with_the_engine` pins it against
    `inspect_chain` on the three classes both can express.
    """
    entries = view.entries
    if not entries or entries[0] is not view.genesis:
        return "genesis-count"
    digests = [entry.digest for entry in entries]
    if len(set(digests)) != len(digests):
        return "duplicate-registration"
    if view.tip != digests[-1]:
        return "missing-predecessor"
    registrations: dict[str, logmodel.RegisteredEntryView] = {}
    settled: set[str] = set()
    fulfilled: set[str] = set()
    intents = {entry.digest for entry in entries if type(entry) is logmodel.IntentEntryView}
    for index, entry in enumerate(entries):
        if type(entry) is logmodel.RegisteredEntryView:
            if any(other.txid == entry.txid for other in registrations.values()):
                return "duplicate-registration"
            if entry.fulfills is not None and entry.fulfills not in intents:
                return "fulfills-invalid"
            registrations[entry.digest] = entry
        elif type(entry) is logmodel.SettledEntryView:
            registration = registrations.get(entry.registration)
            if registration is None or digests.index(entry.registration) > index:
                return "settlement-unregistered"
            if registration.txid != entry.txid:
                return "settlement-txid-mismatch"
            if entry.registration in settled:
                return "duplicate-settlement"
            settled.add(entry.registration)
            if entry.committed and registration.fulfills is not None:
                if registration.fulfills in fulfilled:
                    return "duplicate-fulfillment"
                fulfilled.add(registration.fulfills)
    return None


def test_the_view_predicate_agrees_with_the_engine(tmp_path):
    """The view predicate is not a second, weaker standard.

    For each defect class a linearization can express, the same shape is built
    on disk and inspected by the engine, and built as a view and read by the
    predicate. The two must name the same kind — otherwise the view-level check
    would be a standard invented for the convenience of the arms it excuses.
    """
    from test_world_log_codecs import duplicate_fulfillment, fulfills_missing_intent
    from test_world_log_codecs import duplicate_settlement as on_disk_duplicate_settlement

    def engine_kind(build, name: str) -> str:
        view = inspected(build(tmp_path / name).root)
        assert type(view) is logmodel.MalformedView
        return view.defect.kind

    healthy = inspected(settled_corpus(tmp_path / "healthy").root)
    assert type(healthy) is logmodel.WellFormedView
    assert view_defect(healthy) is None

    genesis = healthy.genesis
    _, registration, settlement = healthy.entries
    assert type(registration) is logmodel.RegisteredEntryView
    assert type(settlement) is logmodel.SettledEntryView

    twice = logmodel.WellFormedView(
        genesis=genesis,
        entries=(genesis, registration, settlement, logmodel.SettledEntryView(
            digest="9" * 64, txid=registration.txid, registration=registration.digest, committed=True
        )),
        tip="9" * 64,
        pending=(),
    )
    assert view_defect(twice) == engine_kind(on_disk_duplicate_settlement, "dup-settlement")

    unresolved = logmodel.RegisteredEntryView(
        digest="8" * 64,
        txid="tx-2",
        initial=registration.initial,
        final=registration.final,
        fulfills="e" * 64,
    )
    dangling = logmodel.WellFormedView(
        genesis=genesis, entries=(genesis, registration, settlement, unresolved), tip="8" * 64, pending=()
    )
    assert view_defect(dangling) == engine_kind(fulfills_missing_intent, "fulfills-missing")

    intent = logmodel.IntentEntryView(digest="7" * 64, payload=b"an intent")
    first = logmodel.RegisteredEntryView(
        digest="6" * 64, txid="tx-a", initial=(), final=(), fulfills=intent.digest
    )
    second = logmodel.RegisteredEntryView(
        digest="5" * 64, txid="tx-b", initial=(), final=(), fulfills=intent.digest
    )
    doubled = logmodel.WellFormedView(
        genesis=genesis,
        entries=(
            genesis,
            intent,
            first,
            logmodel.SettledEntryView(digest="4" * 64, txid="tx-a", registration=first.digest, committed=True),
            second,
            logmodel.SettledEntryView(digest="3" * 64, txid="tx-b", registration=second.digest, committed=True),
        ),
        tip="3" * 64,
        pending=(),
    )
    assert view_defect(doubled) == engine_kind(duplicate_fulfillment, "dup-fulfillment")


def test_every_view_level_fabrication_is_structurally_well_formed(tmp_path):
    """Obligation 1's *purpose*, over the fabrications that cannot meet it
    literally: none of the views the view-level units hand to a stubbed seam
    carries a structural defect it claims not to have."""
    corpus = corpus_root_at(tmp_path, CUT8_CORPUS_ID, name="corpus")
    world = tmp_path / "world"
    world.mkdir()
    (world / "world.yaml").write_bytes(b"world_id: " + b"f" * 32 + b"\n")

    views = {
        "surfaced:corpus": surfaced(corpus, "corpus", science_root.GENESIS_PAYLOAD),
        "surfaced:world": surfaced(world, "world", science_root._world_genesis_payload("f" * 32)),
        "world_chain": world_chain("1" * 64),
        "world_chain:rolled-back": world_chain("1" * 64, committed=False),
        "world_chain:trailing": world_chain("1" * 64, trailing=True),
    }
    views["pending_view"] = pending_view(views["surfaced:corpus"])

    for name, view in views.items():
        assert view_defect(view) is None, f"{name}: {view_defect(view)}"
        assert view.genesis is view.entries[0], name
        assert view.tip == view.entries[-1].digest, name


# --- §5's obligations 2–6 and §6's two freeze obligations ------------------------


def test_obligation_two_the_rollback_arm_is_settled_and_absent(tmp_path):
    """§5.2. L2u1's fabrication carries a genuinely rolled-back settlement and a
    genuinely absent path — a refusal before registration, or a missing
    settlement, would make the arm vacuous."""
    chain = rolled_back_creation(tmp_path)
    view = inspected(chain.root)
    assert type(view) is logmodel.WellFormedView
    settlements = [entry for entry in view.entries if type(entry) is logmodel.SettledEntryView]
    assert [entry.committed for entry in settlements] == [True, False]
    assert not (chain.root / RECORD).exists()


def test_obligation_three_the_rewrite_differs_byte_wise_beyond_the_anchor(tmp_path):
    """§5.3. L5u1's rewrite really rewrote: at least one entry beyond the maximal
    anchor, and the envelope bytes differ from the ones they replaced."""
    chain = rewritten_tail(tmp_path)
    assert len(chain.added) >= 1
    assert set(chain.added).isdisjoint(chain.replaced)
    assert chain.anchor and chain.anchor not in chain.removed
    view = inspected(chain.root)
    assert type(view) is logmodel.WellFormedView
    beyond = [entry.digest for entry in view.entries][view.entries.index(view.genesis) + 3 :]
    assert len(beyond) == len(chain.added)


def test_obligation_four_two_distinct_anchored_corpora(tmp_path):
    """§5.4. L4u2 constructs two distinct corpus roots with distinct
    `corpus_id`s, both anchorable, before either chain is removed."""
    first = settled_corpus(tmp_path, corpus_id=CUT8_CORPUS_ID, name="first")
    second = settled_corpus(tmp_path, corpus_id=CUT8_SIBLING_ID, name="second")
    assert first.root != second.root
    assert CUT8_CORPUS_ID != CUT8_SIBLING_ID
    assert first.tip != second.tip
    for chain in (first, second):
        assert type(inspected(chain.root)) is logmodel.WellFormedView


def test_obligation_five_all_three_in_root_carriers_are_truncated(tmp_path):
    """§5.5. L11u3's truncation really truncated all three in-root carriers — a
    partial truncation would refute for the wrong reason."""
    chain = coordinated_truncation(tmp_path)
    assert len(chain.removed) == 2
    assert not (chain.root / "registry").exists()
    assert not (chain.root / "epochs").exists()
    for carrier in IN_ROOT_CARRIERS:
        assert not (chain.root / carrier).exists()
    assert (chain.root / "world.yaml").is_file()


def test_obligation_six_all_four_state_classes(tmp_path):
    """§5.6. L12u1's round trip covers all four typed state classes; a subset is
    malformed declaration content, not a pass."""
    chain = four_state_classes(tmp_path)
    disk = capture_at(chain.root, *chain.paths)
    assert {type(state).__name__ for _path, state in disk} == {
        "AbsentState",
        "DirectoryState",
        "FileState",
        "SymlinkState",
    }
    view = inspected(chain.root)
    assert type(view) is logmodel.WellFormedView
    (created,) = [entry for entry in view.entries if type(entry) is logmodel.RegisteredEntryView]
    assert created.final == disk


def test_freeze_obligation_the_remint_is_the_only_delta(tmp_path):
    """§6, first. L4u3's re-mint interposes no other mutation: the manifest is
    the only path where the logged surface and the disk disagree."""
    chain = manifest_remint(tmp_path)
    view = inspected(chain.root)
    assert type(view) is logmodel.WellFormedView
    surface = dict(view.genesis.baseline)
    committed = {
        entry.registration
        for entry in view.entries
        if type(entry) is logmodel.SettledEntryView and entry.committed
    }
    for entry in view.entries:
        if type(entry) is logmodel.RegisteredEntryView and entry.digest in committed:
            surface.update(entry.final)
    disk = capture_at(chain.root, *chain.paths)
    assert [path for path, state in disk if surface[path] != state] == [MANIFEST]
    assert len(chain.paths) == 2, "a one-path surface would make 'only delta' vacuous"


def test_freeze_obligation_the_unordered_case_is_a_rolled_back_publication():
    """§6, second. L8u1's unordered case is constructed from a genuinely
    rolled-back publication entry, asserted **by entry class** — never from two
    arbitrary epochs."""
    ordered = world_chain("1" * 64)
    rolled_back = world_chain("1" * 64, committed=False)
    (settled,) = [entry for entry in ordered.entries if type(entry) is logmodel.SettledEntryView]
    (reverted,) = [entry for entry in rolled_back.entries if type(entry) is logmodel.SettledEntryView]
    assert settled.committed is True
    assert reverted.committed is False
    assert settled.registration == reverted.registration
    assert view_defect(ordered) is None
    assert view_defect(rolled_back) is None


# --- the harness's own verdicts, preserved --------------------------------------


@pytest.mark.parametrize(
    ("arm", "verdict"),
    [
        (VACUOUS_BY_CONSTRUCTION, "vacuous"),
        (MIXED_BY_CONSTRUCTION, "mixed"),
        (UNCOLLECTED_BY_CONSTRUCTION, "uncollected"),
        (STALE_BY_CONSTRUCTION, "stale"),
    ],
)
def test_the_harness_preserves_each_malformed_verdict(tmp_path, arm, verdict):
    assert audit(arm, tmp_path / verdict).verdict == verdict


def test_the_harness_rejects_a_class_node(tmp_path):
    with pytest.raises(MalformedArm, match="one test function"):
        audit(CLASS_NODE_BY_CONSTRUCTION, tmp_path / "class-node")
