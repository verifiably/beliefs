"""Cut 17 declaration accounting and N2 audit."""

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
from n2_arms_cut14 import CUT14_ARMS
from n2_arms_cut15 import CUT15_ARMS
from n2_arms_cut16 import CUT16_ARMS
from n2_arms_cut17 import CO_CITED, CUT17_ARMS, LABELED_UNITS, ROW_UNITS, unit_of
from test_n2 import audit, baseline

import beliefs.root as science_root

# Live facet-contract matcher migration, 2026-09-07; canonical table remains frozen at c367070.
_LIVE_SABOTAGES = {
    "E1c": Sabotage(
        module="corpus.py",
        before='        self._authority.require("corpus-write", (node.kind,))\n        with self._operation:\n            self._require_pins_agree()\n            self._refuse_family_kinds(node)\n            self._refuse(node)',
        after="        with self._operation:\n            self._require_pins_agree()\n            self._refuse_family_kinds(node)\n            self._refuse(node)",
    ),
    "E1r": Sabotage(
        module="corpus.py",
        before='        self.authority.require("corpus-write", (node.kind,))\n        self._preflight_add_locked(node, provenance=provenance)\n        return self._corpus.add(node)',
        after='        self._preflight_add_locked(node, provenance=provenance)\n        result = self._corpus.add(node)\n        self.authority.require("corpus-write", (node.kind,))\n        return result',
    ),
    "E6a": Sabotage(
        module="holdings/boundary.py",
        before='def _append(ctx: ActContext, location: StoreLocator, kind: str) -> tuple[str, str]:\n    ctx.authority.require("holdings", ("holdings-observation",))\n    token = secrets.token_hex(16)\n    from beliefs.corpus import require_pins_agree\n\n    with ctx.seam.corpus_lock(ctx.observer_root):\n        require_pins_agree(ctx.observer_root, ctx.profile)\n        intent = ctx.seam.append_intent(\n            ctx.observer_root, intent_payload(location=location, act_kind=kind, event_token=token, actor=ctx.actor)\n        )\n    return token, intent',
        after='def _append(ctx: ActContext, location: StoreLocator, kind: str) -> tuple[str, str]:\n    token = secrets.token_hex(16)\n    from beliefs.corpus import require_pins_agree\n\n    with ctx.seam.corpus_lock(ctx.observer_root):\n        require_pins_agree(ctx.observer_root, ctx.profile)\n        intent = ctx.seam.append_intent(\n            ctx.observer_root, intent_payload(location=location, act_kind=kind, event_token=token, actor=ctx.actor)\n        )\n    ctx.authority.require("holdings", ("holdings-observation",))\n    return token, intent',
    ),
    "K1": Sabotage(
        module="holdings/boundary.py",
        before="        ctx.seam.publish_fulfilling(ctx.observer_root, plan, intent)",
        after="        pass  # established finding silently dropped",
    ),
}
CUT17_ARMS = tuple(
    replace(arm, sabotage=_LIVE_SABOTAGES[arm.row]) if arm.row in _LIVE_SABOTAGES else arm for arm in CUT17_ARMS
)

WORKERS = 8
REPO_ROOT = Path(__file__).resolve().parents[3]
FROZEN_CUT = REPO_ROOT / "docs" / "designs" / "2026-09-04-write-permits-design.md"
CUT17_FREEZE_COMMIT = "c2f87b3"
IMPLEMENTATION_AMENDMENT_COMMIT = "b25fcc7"
RENUMBERING_AMENDMENT_COMMIT = "e6b8c0b"
FROZEN_PRIOR_CUT_FILES = {
    "python/tests/n2_arms_cut3.py": "1e92471",
    "python/tests/n2_arms_cut5.py": "1e92471",
    "python/tests/n2_arms_cut6.py": "fdea7a7e2f8780f8ddfec3a6a700333a28e648cd",
    "python/tests/n2_arms_cut7.py": "8ca085e8cf860efc9b7504f0961523e5e2a0438f",
    "python/tests/acceptance/n2_arms_cut8.py": "5a02ca299ba2de1b71702f834ac4fc44781c0eef",
    "python/tests/acceptance/n2_arms_cut9.py": "c7817ba5b32c72fc6b967cda85f9b1c4ef9f6198",
    "python/tests/acceptance/n2_arms_cut10.py": "5a02ca299ba2de1b71702f834ac4fc44781c0eef",
    "python/tests/acceptance/n2_arms_cut11.py": "5a02ca299ba2de1b71702f834ac4fc44781c0eef",
    "python/tests/acceptance/n2_arms_cut12.py": "5dff360a83c5e48c81824f04dd648adb972e790a",
    "python/tests/acceptance/n2_arms_cut13.py": "7504d6906a8729f8e04097083396a50afc464f9b",
    "python/tests/acceptance/n2_arms_cut14.py": "f982778",
    "python/tests/acceptance/n2_arms_cut15.py": "8a4d43b",
    "python/tests/n2_arms_cut16.py": "b0882d3",
}
FROZEN_CUT10_SHA256 = {
    "python/tests/acceptance/n2_arms_cut10.py": "e7e3cf02f8d033a9bf507b6eba0f4968bcf702c901ad3a753013f062c02e5ae8",
    "python/tests/acceptance/test_n2_cut10.py": "4058b86679b9a7b17bbfd5115ba3e7c21896e2316c384d700c4af052674dc650",
    "python/tools/cut10_acceptance.py": "39a1e333d8b99bacf0bcdc416e86ef6d68e97be797c6acc3c31c922bab838edf",
    "docs/designs/2026-08-24-conformance-cut-10.md": "17dcc49b5a7e2207baeae3990d04f5cb35c499156f9c2cbf1c996b6587cefc64",
    "docs/plans/2026-08-24-conformance-cut-10-results.md": "83fa5f7cb0ea0abaf82db765162792b2862d6cd9e0feec1eabe2aaaac85d224b",
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
)


@pytest.fixture(scope="session")
def findings(tmp_path_factory):
    root = tmp_path_factory.mktemp("n2-cut17")
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        return tuple(pool.map(lambda pair: audit(pair[1], root / f"arm{pair[0]}"), enumerate(CUT17_ARMS)))


def test_the_inventory_is_eight_selected_and_one_labeled() -> None:
    assert ROW_UNITS == {
        "E1": 1,
        "E2": 1,
        "E3": 1,
        "E4": 1,
        "E5": 1,
        "E6": 1,
        "E7": 1,
        "E8": 1,
    }
    assert LABELED_UNITS == ("K1",)


def test_the_arm_rows_are_unique() -> None:
    rows = [arm.row for arm in CUT17_ARMS]
    assert len(rows) == len(set(rows))


def test_every_declared_unit_is_carried_by_at_least_one_arm() -> None:
    carried = {unit_of(arm.row) for arm in CUT17_ARMS}
    assert set(ROW_UNITS) | set(LABELED_UNITS) <= carried


def test_every_check_resolves_and_passes_without_sabotage() -> None:
    every = Arm(row="N2", asserts="every cut-17 check passes against the real package",
                sabotage=CUT17_ARMS[0].sabotage,
                checks=tuple(dict.fromkeys(check for arm in CUT17_ARMS for check in arm.checks)))
    finding = baseline(every)
    assert finding.verdict == "resolved", finding.detail


def test_every_arm_fails_under_its_sabotage(findings) -> None:
    unsound = [finding for finding in findings if finding.verdict != "sound"]
    assert not unsound, "\n".join(f"{f.arm.label}: {f.verdict}: {f.detail}" for f in unsound)


def _section(text: str, heading: str) -> str:
    start = text.index(heading)
    end = text.find("\n## ", start + 1)
    return text[start:] if end == -1 else text[start:end]


def test_the_frozen_cut_and_the_amendment_are_ancestors_and_the_frozen_sections_are_byte_exact() -> None:
    for commit in (CUT17_FREEZE_COMMIT, IMPLEMENTATION_AMENDMENT_COMMIT, RENUMBERING_AMENDMENT_COMMIT):
        assert subprocess.run(["git", "-C", str(REPO_ROOT), "merge-base", "--is-ancestor", commit, "HEAD"], check=False).returncode == 0
    frozen = subprocess.run(["git", "-C", str(REPO_ROOT), "show", f"{CUT17_FREEZE_COMMIT}:{FROZEN_CUT.relative_to(REPO_ROOT)}"],
                            check=True, capture_output=True, text=True).stdout
    text = FROZEN_CUT.read_text(encoding="utf-8")
    for heading in ("## 7. Guarantees", "## 9. Conformance cut 16"):
        assert _section(text, heading) == _section(frozen, heading), heading


def test_every_arm_has_one_source_mutation_and_exact_check_nodes() -> None:
    package = Path(science_root.__file__).resolve().parent
    for arm in CUT17_ARMS:
        assert arm.checks and len(arm.checks) == len(set(arm.checks)), arm.row
        assert arm.sabotage.before != arm.sabotage.after and arm.asserts.strip(), arm.row
        target = package / arm.sabotage.module
        assert target.is_file(), f"{arm.row}: missing {arm.sabotage.module}"
        assert target.read_text(encoding="utf-8").count(arm.sabotage.before) == 1, arm.row
        for check in arm.checks:
            parts = check.split("::")
            assert len(parts) >= 2 and parts[-1].startswith("test_"), check


def test_prior_declarations_and_the_whole_cited_cut10_surface_are_unchanged() -> None:
    for path, pin in FROZEN_PRIOR_CUT_FILES.items():
        assert subprocess.run(["git", "-C", str(REPO_ROOT), "diff", "--quiet", pin, "HEAD", "--", path], check=False).returncode == 0, path
    for path, expected in FROZEN_CUT10_SHA256.items():
        assert sha256((REPO_ROOT / path).read_bytes()).hexdigest() == expected, path
    prior = {check for arm in PRIOR_ARMS for check in arm.checks}
    for arm in CUT17_ARMS:
        assert set(arm.checks) & prior <= set(CO_CITED.get(arm.row, ())), arm.row
