"""The shipped base and stored tables are compiled from one packaged contract."""

import subprocess
import sys
from importlib import resources

from beliefs import stored
from beliefs.profile import shipped_base, shipped_base_contract


def test_the_packaged_copy_is_byte_identical_to_the_normative_file(base_contract_path):
    packaged = resources.files("beliefs").joinpath("contracts/science/CONTRACT.yaml").read_bytes()
    assert packaged == base_contract_path.read_bytes()


def test_the_shipped_base_is_compiled_once():
    assert shipped_base() is shipped_base()
    assert shipped_base().base_contract_identity == shipped_base_contract().content_identity


def test_stored_tables_are_views_over_the_shipped_base():
    world = {name: kind for name, kind in shipped_base().kinds.items() if kind.role == "world"}
    assert stored.WORLD_KINDS == tuple(world)
    assert stored.PROSE_KINDS == tuple(name for name, kind in shipped_base().kinds.items() if kind.role == "prose")
    assert stored.SEMANTIC_DOMAINS == {name: kind.domain for name, kind in world.items() if kind.domain is not None}
    assert stored.COVERED_FACETS == {name: kind.covered for name, kind in world.items() if kind.domain is not None}
    assert stored.WORLD_RELATIONS == tuple(
        name for name, relation in shipped_base().relations.items() if relation.group == "world"
    )


def test_membership_is_exactly_what_it_was_before_this_slice():
    assert stored.WORLD_KINDS == (
        "proposition",
        "source-assertion",
        "assessment",
        "analysis-spec",
        "run",
        "verification",
        "dataset",
        "source",
        "holdings-observation",
        "retraction",
        "instrument-certification",
        "coreference-attestation",
        "act-report",
        "composite",
        "exposure-event",
        "reservation-assignment",
        "assumptions-register",
        "procedure",
        "referent-mapping",
        "proxy-model",
        "classification-rule",
    )
    assert stored.PROSE_KINDS == ("interpretation", "discussion", "story")
    assert stored.WORLD_RELATIONS == (
        "assesses",
        "observes",
        "reads",
        "transforms",
        "produces",
        "produced_by",
        "executes",
        "targets",
        "verifies",
        "member_of",
        "grounded-in",
        "composes",
        "exposes",
        "concerns",
        "attested-by",
        "considers",
        "evidenced-by",
        "flags",
        "reports",
        "applies",
    )
    assert stored.COVERED_FACETS["dataset"] == ("dataset", "empirical-observation", "lineage-basis")
    assert stored.COVERED_FACETS["run"] == ("run", "run-closure")
    for kind in ("procedure", "referent-mapping", "proxy-model", "classification-rule"):
        assert stored.COVERED_FACETS[kind] == (kind,)
    assert "instrument-certification" not in stored.SEMANTIC_DOMAINS
    assert "discussion" not in stored.SEMANTIC_DOMAINS


def test_the_import_graph_is_acyclic():
    subprocess.run([sys.executable, "-c", "import beliefs.stored"], check=True)


def test_base_cutover_refuses_v3_corpus(tmp_path):
    from pathlib import Path

    import pytest
    from test_read_side import seed

    from beliefs.contract.document import parse_document
    from beliefs.errors import ContractMismatch, MountPinUnresolved
    from beliefs.identity import v1
    from beliefs.mount import compile_mount_profile
    from beliefs.profile import shipped_domain_contract

    document = parse_document((Path(__file__).parent / "fixtures/science-v3.yaml").read_text(), source="<original v3>")
    old_identity = v1.digest("science.contract.v1", document)
    assert old_identity == "fe98a998e5a6a9a7988f4ab8708e2167a9e873744345732a330bdb39c257f437"
    node = stored.proposition_node("historical", title="Untouched coarse claim", claim={"operator": "affects"})
    view = seed(tmp_path, node, science_contract="science:" + old_identity)
    before = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    assert [n.id for n in view.iter_stored()] == [node.id]
    with pytest.raises(ContractMismatch, match="science_contract"):
        view.get(node.id)
    with pytest.raises(MountPinUnresolved):
        compile_mount_profile(tmp_path, available=(shipped_domain_contract("general"),))
    after = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    assert after == before
    assert stored.SEMANTIC_DOMAINS["assessment"] == "science.assessment.v2"
    from beliefs.dependencies import ASSESSMENT_FACET_DOMAIN

    assert ASSESSMENT_FACET_DOMAIN == "science.assessment-facet.v2"


def test_previous_base_generation_refused_by_name():
    from pathlib import Path

    import pytest

    from beliefs.contract import load_base_contract
    from beliefs.errors import MalformedContract

    # Base v6 adds `scope_grammar`; each earlier generation is refused by that field's absence, by
    # name, and never read as an implicit upgrade.
    for generation in ("science-v4.yaml", "science-v5.yaml"):
        with pytest.raises(MalformedContract, match=r"missing field\(s\) scope_grammar"):
            load_base_contract(Path(__file__).parent / "fixtures" / generation)


def test_base_cutover_refuses_v5_corpus(tmp_path):
    from pathlib import Path

    import pytest
    from test_read_side import seed

    from beliefs.contract.document import parse_document
    from beliefs.errors import ContractMismatch, MountPinUnresolved
    from beliefs.identity import v1
    from beliefs.mount import compile_mount_profile
    from beliefs.profile import shipped_domain_contract

    document = parse_document((Path(__file__).parent / "fixtures/science-v5.yaml").read_text(), source="<original v5>")
    old_identity = v1.digest("science.contract.v1", document)
    assert old_identity == "08f0b96b11a9bb54eb20a52fb90a8cc647cedfc78375a64f2c0039ea4b9df52b"
    assert shipped_base_contract().content_identity != old_identity
    node = stored.proposition_node("historical", title="Untouched v5 claim", claim={"operator": "affects"})
    view = seed(tmp_path, node, science_contract="science:" + old_identity)
    before = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    assert [n.id for n in view.iter_stored()] == [node.id]
    with pytest.raises(ContractMismatch, match="science_contract"):
        view.get(node.id)
    with pytest.raises(MountPinUnresolved):
        compile_mount_profile(tmp_path, available=(shipped_domain_contract("general"),))
    after = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    assert after == before
