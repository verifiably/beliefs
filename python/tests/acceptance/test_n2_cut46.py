"""Cut 46 declaration accounting, freeze pin, and N2 audit."""

from __future__ import annotations

import ast
import subprocess
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import frozen_guards
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
from n2_arms_cut14 import CUT14_ARMS
from n2_arms_cut15 import CUT15_ARMS
from n2_arms_cut16 import CUT16_ARMS
from n2_arms_cut17 import CUT17_ARMS
from n2_arms_cut18 import CUT18_ARMS
from n2_arms_cut19 import CUT19_ARMS
from n2_arms_cut20 import CUT20_ARMS
from n2_arms_cut21 import CUT21_ARMS
from n2_arms_cut22 import CUT22_ARMS
from n2_arms_cut23 import CUT23_ARMS
from n2_arms_cut24 import CUT24_ARMS
from n2_arms_cut25 import CUT25_ARMS as FROZEN_CUT25_ARMS
from n2_arms_cut26 import CUT26_ARMS
from n2_arms_cut27 import CUT27_ARMS
from n2_arms_cut28 import CUT28_ARMS
from n2_arms_cut29 import CUT29_ARMS
from n2_arms_cut30 import CUT30_ARMS
from n2_arms_cut31 import CUT31_ARMS
from n2_arms_cut32 import CUT32_ARMS
from n2_arms_cut33 import CUT33_ARMS
from n2_arms_cut34 import CUT34_ARMS
from n2_arms_cut35 import CUT35_ARMS
from n2_arms_cut36 import CUT36_ARMS
from n2_arms_cut37 import CUT37_ARMS
from n2_arms_cut38 import CUT38_ARMS
from n2_arms_cut39 import CUT39_ARMS
from n2_arms_cut40 import CUT40_ARMS
from n2_arms_cut41 import CUT41_ARMS
from n2_arms_cut42 import CUT42_ARMS
from n2_arms_cut43 import CUT43_ARMS
from n2_arms_cut44 import CUT44_ARMS
from n2_arms_cut45 import CUT45_ARMS
from n2_arms_cut46 import (
    CO_CITED,
    CUT46_ARMS,
    DECLARATION_UNITS,
    UNIT_CHECKS,
    unit_of,
)
from test_n2 import audit, baseline, workers
from test_n2_cut25 import CUT25_ARMS
from test_n2_cut25 import RETARGETED_ROWS as CUT25_RETARGETED_ROWS

_LIVE_SABOTAGES = {
    # Repository reformat, 2026-10-09 (beliefs-a555d6): `ruff format` re-wrapped the
    # anchored lines. Derived by tools/retarget_formatted_arms.py, so this arm applied to
    # the formatted source is exactly the formatted declared sabotage.
    "Y17-i": Sabotage(
        module="publish.py",
        before=(
            "    for holder in sorted(grouped):\n"
            "        if holder not in admissions:\n"
            "            raise PublicationRefused(\n"
            '                "attribution-holder-unregistered",\n'
            "                corpus_ids=(holder,),\n"
            "                refs=tuple(sorted(grouped[holder])),\n"
            "            )\n"
            "    replicas = tuple(holder for holder in sorted(grouped) if type(admissions[holder].provenance) is ReplicaOf)\n"
        ),
        after=(
            "    replicas = tuple(\n"
            "        holder\n"
            "        for holder in sorted(grouped)\n"
            "        if holder in admissions and type(admissions[holder].provenance) is ReplicaOf\n"
            "    )\n"
        ),
    ),
    # Repository reformat, 2026-10-09 (beliefs-a555d6): `ruff format` re-wrapped the
    # anchored lines. Derived by tools/retarget_formatted_arms.py, so this arm applied to
    # the formatted source is exactly the formatted declared sabotage.
    "Y17-n": Sabotage(
        module="publish.py",
        before=(
            "        selection=tuple(i for i, _ in a.snapshot.records),\n"
            "        attributions=a.snapshot.attributions,\n"
            "    )\n"
        ),
        after=(
            "        selection=tuple(i for i, _ in a.snapshot.records),\n"
            '        attributions=None if a.opened.intent.destination.type == "remote" else a.snapshot.attributions,\n'
            "    )\n"
        ),
    ),
    # Repository reformat, 2026-10-09 (beliefs-a555d6): `ruff format` re-wrapped the
    # anchored lines. Derived by tools/retarget_formatted_arms.py, so this arm applied to
    # the formatted source is exactly the formatted declared sabotage.
    "Y18-a": Sabotage(
        module="publication.py",
        before=(
            "    if type(source) is not dict or set(source) not in (\n"
            '        {"world_id", "epoch", "view"},\n'
            '        {"world_id", "epoch", "view", "attributions"},\n'
            "    ):\n"
        ),
        after="    if type(source) is not dict:\n",
    ),
    # Repository reformat, 2026-10-09 (beliefs-a555d6): `ruff format` re-wrapped the
    # anchored lines. Derived by tools/retarget_formatted_arms.py, so this arm applied to
    # the formatted source is exactly the formatted declared sabotage.
    "Y18-d": Sabotage(
        module="publication.py",
        before="            or row[0] not in selection\n",
        after="",
    ),
    # Repository reformat, 2026-10-09 (beliefs-a555d6): `ruff format` re-wrapped the
    # anchored lines. Derived by tools/retarget_formatted_arms.py, so this arm applied to
    # the formatted source is exactly the formatted declared sabotage.
    "Y18-j": Sabotage(
        module="corpus.py",
        before=(
            "            if (\n"
            "                node.kind != MARKER_KIND\n"
            "                or publication_content_malformed(node)\n"
            "                or not marker_consistent(node)\n"
            "                or _marker_release_malformed(\n"
            "                    node,\n"
            '                    ("coordination:" + self._profile.activated_contracts["coordination"])\n'
            '                    if "coordination" in self._profile.activated_contracts\n'
            "                    else None,\n"
            "                )\n"
            "            ):\n"
        ),
        after="            if node.kind != MARKER_KIND or publication_content_malformed(node) or not marker_consistent(node):\n",
    ),
    # Repository reformat, 2026-10-09 (beliefs-a555d6): `ruff format` re-wrapped the
    # anchored lines. Derived by tools/retarget_formatted_arms.py, so this arm applied to
    # the formatted source is exactly the formatted declared sabotage.
    "Y18-k": Sabotage(
        module="corpus.py",
        before=(
            "    return publication_content_malformed(node) or (\n"
            "        node.kind == MARKER_KIND and _marker_release_malformed(node, coordination_pin)\n"
            "    )\n"
        ),
        after="    return publication_content_malformed(node)\n",
    ),
    # Repository reformat, 2026-10-09 (beliefs-a555d6): `ruff format` re-wrapped the
    # anchored lines. Derived by tools/retarget_formatted_arms.py, so this arm applied to
    # the formatted source is exactly the formatted declared sabotage.
    "Y18-o": Sabotage(
        module="publish.py",
        before=(
            "    return not _marker_release_malformed(\n"
            '        node, load_manifest(_remote_export(r.op, mark.corpus_id)).profile.domains.get("coordination")\n'
            "    )\n"
        ),
        after="    return True\n",
    ),
}
CUT46_ARMS = tuple(
    replace(arm, sabotage=_LIVE_SABOTAGES[arm.row]) if arm.row in _LIVE_SABOTAGES else arm for arm in CUT46_ARMS
)

REPO_ROOT = Path(__file__).resolve().parents[3]
FROZEN_CUT = REPO_ROOT / "docs" / "designs" / "2026-10-02-conformance-cut-46.md"
CUT46_FREEZE_COMMIT = "5981ae6"
CUT46_FROZEN_SHA256 = "aa87d32a6cd7d1541bf76d7bf9de55b640771c6ac2f13bb4d967a4a577e9953b"
FROZEN_DECLARATION = "python/tests/n2_arms_cut46.py"
CUT46_DECLARATION_SHA256 = "da3e36e19ecf87d3da17da009350bf0c82fcc29315323057f64e9c781cf6dc04"

# The frozen cut's §4: 36 declaration units, each with its own arm.
FROZEN_ARMS, FROZEN_UNITS = 36, 36

FROZEN_PRIOR_CUT_FILES = {
    "python/tests/n2_arms_cut3.py": "1e92471",
    "python/tests/n2_arms_cut5.py": "1e92471",
    "python/tests/n2_arms_cut6.py": "fdea7a7",
    "python/tests/n2_arms_cut7.py": "8ca085e",
    "python/tests/acceptance/n2_arms_cut8.py": "5a02ca2",
    "python/tests/acceptance/n2_arms_cut9.py": "c7817ba",
    "python/tests/acceptance/n2_arms_cut10.py": "5a02ca2",
    "python/tests/acceptance/n2_arms_cut11.py": "5a02ca2",
    "python/tests/acceptance/n2_arms_cut12.py": "5dff360",
    "python/tests/acceptance/n2_arms_cut13.py": "7504d69",
    "python/tests/acceptance/n2_arms_cut14.py": "f982778",
    "python/tests/acceptance/n2_arms_cut15.py": "8a4d43b",
    "python/tests/n2_arms_cut16.py": "b0882d3",
    "python/tests/acceptance/n2_arms_cut17.py": "c367070",
    "python/tests/n2_arms_cut18.py": "e0bc65c",
    "python/tests/acceptance/n2_arms_cut19.py": "8723fac",
    "python/tests/n2_arms_cut20.py": "8639771",
    "python/tests/acceptance/n2_arms_cut20.py": "d5e203c",
    "python/tests/acceptance/n2_arms_cut21.py": "804cfac",
    "python/tests/acceptance/n2_arms_cut22.py": "4d93b64",
    "python/tests/acceptance/n2_arms_cut23.py": "2283527",
    "python/tests/acceptance/n2_arms_cut24.py": "79f118f",
    "python/tests/n2_arms_cut25.py": "5072609",
    "python/tests/acceptance/n2_arms_cut25.py": "515fc8b",
    "python/tests/n2_arms_cut26.py": "16926ad",
    "python/tests/acceptance/n2_arms_cut27.py": "3674da8",
    "python/tests/acceptance/n2_arms_cut28.py": "d11baf9",
    "python/tests/acceptance/n2_arms_cut29.py": "0e57a52",
    "python/tests/acceptance/n2_arms_cut30.py": "31b083e",
    "python/tests/n2_arms_cut31.py": "2977a83",
    "python/tests/n2_arms_cut32.py": "44343da",
    "python/tests/n2_arms_cut33.py": "d4d6432",
    "python/tests/n2_arms_cut34.py": "1b7e9f2",
    "python/tests/n2_arms_cut35.py": "d525b7d",
    "python/tests/n2_arms_cut36.py": "5e9a9e4",
    "python/tests/n2_arms_cut37.py": "2223f95",
    "python/tests/n2_arms_cut38.py": "b4d71dd",
    "python/tests/n2_arms_cut39.py": "4cb09d8",
    "python/tests/n2_arms_cut40.py": "0f490bd",
    "python/tests/n2_arms_cut41.py": "235af2d",
    "python/tests/n2_arms_cut42.py": "f625e21",
    "python/tests/n2_arms_cut43.py": "0494fd9",
    "python/tests/n2_arms_cut44.py": "cac773c",
    "python/tests/n2_arms_cut45.py": "d466f5f",
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
    *CUT14_ARMS,
    *CUT15_ARMS,
    *CUT16_ARMS,
    *CUT17_ARMS,
    *CUT18_ARMS,
    *CUT19_ARMS,
    *CUT20_ARMS,
    *CUT21_ARMS,
    *CUT22_ARMS,
    *CUT23_ARMS,
    *CUT24_ARMS,
    *CUT25_ARMS,
    *CUT26_ARMS,
    *CUT27_ARMS,
    *CUT28_ARMS,
    *CUT29_ARMS,
    *CUT30_ARMS,
    *CUT31_ARMS,
    *CUT32_ARMS,
    *CUT33_ARMS,
    *CUT34_ARMS,
    *CUT35_ARMS,
    *CUT36_ARMS,
    *CUT37_ARMS,
    *CUT38_ARMS,
    *CUT39_ARMS,
    *CUT40_ARMS,
    *CUT41_ARMS,
    *CUT42_ARMS,
    *CUT43_ARMS,
    *CUT44_ARMS,
    *CUT45_ARMS,
)


@pytest.fixture(scope="session")
def findings(tmp_path_factory):
    workspace = tmp_path_factory.mktemp("n2-cut46")
    with ThreadPoolExecutor(max_workers=workers()) as pool:
        return tuple(
            pool.map(
                lambda pair: audit(pair[1], workspace / f"arm{pair[0]}"),
                enumerate(CUT46_ARMS),
            )
        )


def test_the_inventory_is_exactly_the_frozen_rows_units() -> None:
    assert DECLARATION_UNITS == (
        "Y5-c",
        "Y5-d",
        "Y5-e",
        "Y17-a",
        "Y17-b",
        "Y17-c",
        "Y17-d",
        "Y17-e",
        "Y17-f",
        "Y17-g",
        "Y17-h",
        "Y17-i",
        "Y17-j",
        "Y17-k",
        "Y17-l",
        "Y17-m",
        "Y17-n",
        "Y17-o",
        "Y17-p",
        "Y18-a",
        "Y18-b",
        "Y18-c",
        "Y18-d",
        "Y18-e",
        "Y18-f",
        "Y18-g",
        "Y18-h",
        "Y18-i",
        "Y18-j",
        "Y18-k",
        "Y18-l",
        "Y18-m",
        "Y18-n",
        "Y18-o",
        "Y18-p",
        "Y18-q",
    )
    assert (FROZEN_ARMS, FROZEN_UNITS) == (36, 36)
    assert len(CUT46_ARMS) == FROZEN_ARMS and len(DECLARATION_UNITS) == FROZEN_UNITS
    assert all(arm.sabotage.package == "beliefs" for arm in CUT46_ARMS)
    assert set(UNIT_CHECKS) == set(DECLARATION_UNITS)
    assert {check for arm in CUT46_ARMS for check in arm.checks} == set(UNIT_CHECKS.values())
    homed = {unit: sum(unit_of(arm.row) == unit for arm in CUT46_ARMS) for unit in DECLARATION_UNITS}
    assert homed == dict.fromkeys(DECLARATION_UNITS, 1)


def test_each_arm_is_unique_and_carries_an_exact_check() -> None:
    rows = [arm.row for arm in CUT46_ARMS]
    assert len(rows) == len(set(rows))
    befores = [arm.sabotage.before for arm in CUT46_ARMS]
    assert len(befores) == len(set(befores))
    for arm in CUT46_ARMS:
        assert arm.asserts.strip()
        assert arm.checks and len(arm.checks) == len(set(arm.checks))
        assert arm.sabotage.before != arm.sabotage.after
        for check in arm.checks:
            parts = check.split("::")
            assert len(parts) >= 2 and parts[-1].startswith("test_"), check


def test_each_sabotage_names_one_real_source_site_and_keeps_the_module_importable() -> None:
    """A syntax error never counts as killing the named acceptance check."""
    package = REPO_ROOT / "python" / "src" / "beliefs"
    for arm in CUT46_ARMS:
        target = package / arm.sabotage.module
        assert target.is_file(), f"{arm.row}: missing {arm.sabotage.module}"
        source = target.read_text(encoding="utf-8")
        assert source.count(arm.sabotage.before) == 1, arm.row
        mutated = source.replace(arm.sabotage.before, arm.sabotage.after)
        ast.parse(mutated)


def test_every_acceptance_test_the_arms_name_exists() -> None:
    """The cited set is a subset of the module's tests, with one member per unit."""
    tests = REPO_ROOT / "python" / "tests"
    for check in UNIT_CHECKS.values():
        module, name = check.split("::")
        names = {
            node.name
            for node in ast.parse((tests / module).read_text(encoding="utf-8")).body
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
        }
        assert name in names, check
    assert len(set(UNIT_CHECKS.values())) == len(DECLARATION_UNITS)
    values = list(UNIT_CHECKS.values())
    assert {c for c in values if values.count(c) > 1} <= set(CO_CITED)


def test_every_live_check_resolves_and_passes_without_sabotage() -> None:
    every = Arm(
        row="N2",
        asserts="every cut-46 check passes against the real package",
        sabotage=CUT46_ARMS[0].sabotage,
        checks=tuple(dict.fromkeys(check for arm in CUT46_ARMS for check in arm.checks)),
    )
    finding = baseline(every)
    assert finding.verdict == "resolved", finding.detail


def test_every_arm_fails_under_its_own_sabotage(findings) -> None:
    unsound = [finding for finding in findings if finding.verdict != "sound"]
    assert not unsound, "\n".join(f"{finding.arm.label}: {finding.verdict}: {finding.detail}" for finding in unsound)


def _frozen_body(text: str) -> str:
    """§§2–7: from the boundary heading to the first heading past the limitations.

    A dated supplement in §8 is outside the original freeze, using the same
    slicing rule as cuts 19, 25, 30 and 31.
    """
    start = text.index("## 2. The boundary")
    end = text.index("\n## 8.", start) if "\n## 8." in text[start:] else len(text)
    return text[start:end].rstrip("\n")


def _show(commit: str, path: str) -> str:
    return subprocess.run(
        ["git", "-C", str(REPO_ROOT), "show", f"{commit}:{path}"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def test_the_freeze_commit_and_sections_two_through_seven_are_pinned() -> None:
    """Once frozen, §§2–7 are byte-exact against the freeze commit."""
    assert (
        subprocess.run(
            ["git", "-C", str(REPO_ROOT), "merge-base", "--is-ancestor", CUT46_FREEZE_COMMIT, "HEAD"],
            check=False,
        ).returncode
        == 0
    ), CUT46_FREEZE_COMMIT
    current = FROZEN_CUT.read_text(encoding="utf-8")
    frozen = _show(CUT46_FREEZE_COMMIT, str(FROZEN_CUT.relative_to(REPO_ROOT)))
    assert sha256(frozen.encode("utf-8")).hexdigest() == CUT46_FROZEN_SHA256
    assert _frozen_body(current) == _frozen_body(frozen)
    assert "**36 arms, 36 declaration units, three exercised rows**" in current
    assert '("cut45_acceptance.py",)' in current


def test_the_declaration_is_byte_exact_against_its_pinned_digest() -> None:
    """The arms the guard audits are the arms the accounting freezes on."""
    assert frozen_guards.content_pin_holds(REPO_ROOT, FROZEN_DECLARATION, CUT46_DECLARATION_SHA256)
    shim = (REPO_ROOT / "python" / "tests" / "acceptance" / "n2_arms_cut46.py").read_text(encoding="utf-8")
    assert "n2_arms_cut46.py" in shim  # the acceptance copy re-exports, never restates


def test_prior_declarations_are_frozen_and_no_check_is_reclaimed() -> None:
    assert (
        tuple(
            frozen if live.row in CUT25_RETARGETED_ROWS else live
            for live, frozen in zip(CUT25_ARMS[: len(FROZEN_CUT25_ARMS)], FROZEN_CUT25_ARMS, strict=True)
        )
        == FROZEN_CUT25_ARMS
    )
    for path, pin in FROZEN_PRIOR_CUT_FILES.items():
        assert frozen_guards.commit_pin_holds(REPO_ROOT, path, pin), f"{path} moved since {pin}"
    prior = {check for arm in PRIOR_ARMS for check in arm.checks}
    for arm in CUT46_ARMS:
        reclaimed = set(arm.checks) & prior
        assert reclaimed <= set(CO_CITED), arm.row


def test_row_parser_accepts_only_exact_declared_units() -> None:
    for unit in DECLARATION_UNITS:
        assert unit_of(unit) == unit
    for row in (
        "",
        "Z1",
        "J16",
        "J16-n",
        "J17-c",
        "J18-c",
        "J19-f",
        "J20-b",
        "J21-b",
        "J12-a",
    ):
        with pytest.raises(ValueError, match="is not a cut-46 row"):
            unit_of(row)


# Export the live tuple so arm_staleness.audited_arms measures every audited arm.


@pytest.mark.parametrize("row", ("Y5-c", "Y17-c", "Y18-i"))
def test_pilot_arm(row, tmp_path):
    (arm,) = (arm for arm in CUT46_ARMS if arm.row == row)
    normal = baseline(arm)
    assert normal.verdict == "resolved", normal.detail
    mutated = audit(arm, tmp_path / row)
    assert mutated.verdict == "sound", mutated.detail
