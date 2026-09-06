"""§4.2: the shipped base and stored tables are compiled from one packaged contract."""

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
    )
    assert stored.COVERED_FACETS["dataset"] == ("dataset", "empirical-observation", "lineage-basis")
    assert stored.COVERED_FACETS["run"] == ("run", "run-closure")
    assert "instrument-certification" not in stored.SEMANTIC_DOMAINS
    assert "discussion" not in stored.SEMANTIC_DOMAINS


def test_the_import_graph_is_acyclic():
    subprocess.run([sys.executable, "-c", "import beliefs.stored"], check=True)
