import subprocess
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import pytest
from n2_arms import Arm, Sabotage
from n2_arms_cut3 import CUT3_ARMS
from n2_arms_cut5 import CUT5_ARMS
from n2_arms_cut6 import CUT6_ARMS
from n2_arms_cut7 import CUT7_ARMS
from n2_arms_cut8 import CUT8_ARMS
from n2_arms_cut9 import CUT9_ARMS
from n2_arms_cut10 import CUT10_ARMS
from n2_arms_cut11 import CUT11_ARMS
from n2_arms_cut12 import CUT12_ARMS
from n2_arms_cut13 import CUT13_ARMS
from n2_arms_cut14 import CO_CITED, CUT14_ARMS, LABELED_UNITS, ROW_UNITS, unit_of
from test_n2 import audit, baseline

import beliefs.root as science_root

# Live profile-pin matcher migration, 2026-09-08; canonical table remains frozen at f982778.
_LIVE_SABOTAGES = {
    "W18j": Sabotage(
        module="consulted.py",
        before="    consulted: dict[str, str] = {BASE_NAMESPACE: base_identity}",
        after='    consulted: dict[str, str] = {BASE_NAMESPACE: base_identity}\n    if "coordination" in pins[corpora[0]].domains:\n        consulted["coordination"] = pins[corpora[0]].domains["coordination"]',
    ),
}
CUT14_ARMS = tuple(
    replace(arm, sabotage=_LIVE_SABOTAGES[arm.row]) if arm.row in _LIVE_SABOTAGES else arm for arm in CUT14_ARMS
)

WORKERS = 8
REPO_ROOT = Path(__file__).resolve().parents[3]
CUT14_FREEZE_COMMIT = "c07bf72"
IMPLEMENTATION_AMENDMENT_COMMIT = "09b0b58"
FROZEN_PRIOR_CUT_FILES = {
    "python/tests/n2_arms_cut5.py": "1e92471",
    "python/tests/n2_arms_cut6.py": "fdea7a7e2f8780f8ddfec3a6a700333a28e648cd",
    "python/tests/n2_arms_cut7.py": "8ca085e8cf860efc9b7504f0961523e5e2a0438f",
    "python/tests/acceptance/n2_arms_cut8.py": "5a02ca299ba2de1b71702f834ac4fc44781c0eef",
    "python/tests/acceptance/n2_arms_cut9.py": "c7817ba5b32c72fc6b967cda85f9b1c4ef9f6198",
    "python/tests/acceptance/n2_arms_cut10.py": "5a02ca299ba2de1b71702f834ac4fc44781c0eef",
    "python/tests/acceptance/n2_arms_cut11.py": "5a02ca299ba2de1b71702f834ac4fc44781c0eef",
    "python/tests/acceptance/n2_arms_cut12.py": "5dff360a83c5e48c81824f04dd648adb972e790a",
    "python/tests/acceptance/n2_arms_cut13.py": "7504d6906a8729f8e04097083396a50afc464f9b",
}
FROZEN_CUT5_SHA256 = {
    "python/tests/n2_arms_cut5.py": "dd99a0e0c95519a640f3f50e956566546e342765dc03f511f96d451bf87ce60b",
    "python/tests/acceptance/test_n2_cut5.py": "df589285dd377709c322a2a3958196f3e8a8c65032af8d79863b548584e41798",
    "docs/designs/2026-08-19-conformance-cut-5.md": "683dc249b1898179beaac9c9a550bca5b43f5fe3af9a107f0fc7ee47d58cbdd0",
    "docs/plans/2026-08-19-conformance-cut-5-results.md": "3a24efe3678b99d977a6ddd4f464e600479fb689dedd6df3f5647cb58f6f32de",
}

PRIOR_ARMS = (
    *CUT3_ARMS,
    *CUT5_ARMS,
    *CUT6_ARMS,
    *CUT7_ARMS,
    *CUT8_ARMS,
    *CUT9_ARMS,
    *CUT10_ARMS,
    *CUT11_ARMS,
    *CUT12_ARMS,
    *CUT13_ARMS,
)


@pytest.fixture(scope="session")
def findings(tmp_path_factory):
    root = tmp_path_factory.mktemp("n2-cut14")
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        return tuple(
            pool.map(
                lambda pair: audit(pair[1], root / f"arm{pair[0]}"),
                enumerate(CUT14_ARMS),
            )
        )


def test_no_cut14_arm_is_vacuous_mixed_uncollected_or_stale(findings):
    for verdict in ("vacuous", "mixed", "uncollected", "stale"):
        offending = [finding for finding in findings if finding.verdict == verdict]
        assert not offending, "\n".join(
            f"{finding.arm.label}: {finding.detail}" for finding in offending
        )


def test_every_declared_check_passes_without_sabotage():
    every = Arm(
        "N2",
        "all cut-14 checks pass",
        CUT14_ARMS[0].sabotage,
        tuple(dict.fromkeys(check for arm in CUT14_ARMS for check in arm.checks)),
    )
    finding = baseline(every)
    assert finding.verdict == "resolved", finding.detail


def test_the_29_arms_are_unique_and_account_for_every_selected_unit():
    rows = tuple(arm.row for arm in CUT14_ARMS)
    assert len(rows) == len(set(rows)) == 29
    assert ROW_UNITS == {"W11": 2, "W12": 1, "W13": 1, "W17": 14, "W18": 11}
    assert sum(ROW_UNITS.values()) == 29
    assert {unit_of(row) for row in rows} == (
        {f"W11u{n}" for n in range(1, 3)}
        | {"W12u1", "W13u1"}
        | {f"W17u{n}" for n in range(1, 15)}
        | {f"W18u{n}" for n in range(1, 12)}
    )
    assert LABELED_UNITS == () and CO_CITED == {}


def test_the_design_freeze_and_approved_amendment_are_ancestors():
    for commit in (CUT14_FREEZE_COMMIT, IMPLEMENTATION_AMENDMENT_COMMIT):
        assert (
            subprocess.run(
                ["git", "-C", str(REPO_ROOT), "merge-base", "--is-ancestor", commit, "HEAD"],
                check=False,
            ).returncode
            == 0
        )


def test_prior_declarations_and_the_whole_cited_cut5_surface_are_unchanged():
    for path, commit in FROZEN_PRIOR_CUT_FILES.items():
        assert (
            subprocess.run(
                ["git", "-C", str(REPO_ROOT), "diff", "--quiet", commit, "HEAD", "--", path],
                check=False,
            ).returncode
            == 0
        )
    for path, expected in FROZEN_CUT5_SHA256.items():
        assert sha256((REPO_ROOT / path).read_bytes()).hexdigest() == expected


def test_every_arm_has_one_source_mutation_and_exact_check_nodes():
    package = Path(science_root.__file__).resolve().parent
    for arm in CUT14_ARMS:
        assert arm.checks and len(arm.checks) == len(set(arm.checks)), arm.row
        assert arm.sabotage.before != arm.sabotage.after and arm.asserts.strip(), arm.row
        target = package / arm.sabotage.module
        assert target.is_file(), f"{arm.row}: missing {arm.sabotage.module}"
        assert target.read_text(encoding="utf-8").count(arm.sabotage.before) == 1, arm.row
        for check in arm.checks:
            parts = check.split("::")
            assert len(parts) >= 2 and parts[-1].startswith("test_"), check


def test_no_cut14_arm_rehomes_a_prior_cuts_check():
    prior = {check for arm in PRIOR_ARMS for check in arm.checks}
    for arm in CUT14_ARMS:
        assert not (set(arm.checks) & prior), arm.row
