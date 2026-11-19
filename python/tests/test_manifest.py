from __future__ import annotations

import shutil

import pytest
from authority import FULL
from fixtures_cut6 import BIOLOGY_ID, PINS, SCIENCE_ID, manifest_document
from nodes.core.write_plan import DefaultExecutor
from profiles import WITH_BIOLOGY

from beliefs.corpus import CorpusWriter, corpus_check
from beliefs.errors import ManifestAlreadyPresent, ManifestMalformed, ManifestMissing
from beliefs.world import CorpusManifest, ForkedFrom, load_manifest, manifest_bytes, manifest_projection


def write_manifest(root, document: str) -> None:
    (root / "corpus.yaml").write_text(document, encoding="utf-8")


def test_missing_manifest_refuses(tmp_path):
    with pytest.raises(ManifestMissing):
        load_manifest(tmp_path)


def test_loads_fresh_manifest(tmp_path):
    write_manifest(tmp_path, manifest_document())

    manifest = load_manifest(tmp_path)

    assert manifest == CorpusManifest(2, "1" * 32, PINS)
    assert manifest_projection(manifest) == {
        "manifest_version": 2,
        "corpus_id": "1" * 32,
        "profile": {"science_contract": SCIENCE_ID, "domains": {"biology": BIOLOGY_ID}},
    }


def test_loads_forked_manifest(tmp_path):
    write_manifest(
        tmp_path,
        manifest_document() + "forked_from:\n" + "  corpus_id: " + "2" * 32 + "\n  corpus_state: " + "3" * 64 + "\n",
    )

    manifest = load_manifest(tmp_path)

    assert manifest.forked_from == ForkedFrom("2" * 32, "3" * 64)
    assert manifest_projection(manifest)["forked_from"] == {"corpus_id": "2" * 32, "corpus_state": "3" * 64}


@pytest.mark.parametrize(
    "document",
    (
        manifest_document().replace("manifest_version: 2", "manifest_version: 3"),
        manifest_document() + "extra: refused\n",
        manifest_document().replace("  domains:\n", "  extra: refused\n  domains:\n"),
        manifest_document()
        + "forked_from:\n"
        + "  corpus_id: "
        + "2" * 32
        + "\n  corpus_state: "
        + "3" * 64
        + "\n  extra: refused\n",
        manifest_document().replace("    biology:", "    biology: ignored\n    biology:"),
    ),
)
def test_closed_manifest_shapes_refuse(tmp_path, document):
    write_manifest(tmp_path, document)

    with pytest.raises(ManifestMalformed):
        load_manifest(tmp_path)


@pytest.mark.parametrize(
    "document",
    (
        manifest_document().replace("corpus_id: " + "1" * 32, "corpus_id: " + "A" * 32),
        manifest_document().replace("corpus_id: " + "1" * 32, "corpus_id: " + "1" * 31),
        manifest_document().replace(SCIENCE_ID, "science:" + "A" * 64),
        manifest_document().replace(SCIENCE_ID, "science:" + "a" * 63),
        manifest_document().replace(SCIENCE_ID, "biology:" + "a" * 64),
        manifest_document().replace("biology", "science", 1),
        manifest_document().replace(BIOLOGY_ID, "chemistry:" + "b" * 64),
    ),
)
def test_manifest_identities_refuse_malformed_values(tmp_path, document):
    write_manifest(tmp_path, document)

    with pytest.raises(ManifestMalformed):
        load_manifest(tmp_path)


def test_projection_and_bytes_ignore_yaml_format_and_mapping_order(tmp_path):
    write_manifest(
        tmp_path,
        "profile: {domains: {biology: "
        + BIOLOGY_ID
        + "}, science_contract: "
        + SCIENCE_ID
        + "}\ncorpus_id: "
        + "1" * 32
        + "\nmanifest_version: 2\n",
    )
    compact = load_manifest(tmp_path)
    write_manifest(tmp_path, manifest_document())
    expanded = load_manifest(tmp_path)

    assert manifest_projection(compact) == manifest_projection(expanded)
    assert manifest_bytes(compact) == manifest_bytes(expanded)


def test_fresh_id_is_opaque_and_survives_root_moves_and_reclones(tmp_path):
    first_root = tmp_path / "first"
    first = CorpusWriter(first_root, DefaultExecutor, authority=FULL, profile=WITH_BIOLOGY).adopt_manifest(profile=PINS)
    moved = tmp_path / "moved"
    shutil.move(first_root, moved)
    clone = tmp_path / "clone"
    shutil.copytree(moved, clone)
    second = CorpusWriter(tmp_path / "second", DefaultExecutor, authority=FULL, profile=WITH_BIOLOGY).adopt_manifest(
        profile=PINS
    )

    assert load_manifest(moved).corpus_id == load_manifest(clone).corpus_id == first.corpus_id
    assert second.corpus_id != first.corpus_id


def test_existing_manifest_refuses_remint(tmp_path):
    writer = CorpusWriter(tmp_path, DefaultExecutor, authority=FULL, profile=WITH_BIOLOGY)
    first = writer.adopt_manifest(profile=PINS)

    with pytest.raises(ManifestAlreadyPresent):
        writer.adopt_manifest(profile=PINS)
    assert load_manifest(tmp_path) == first


def test_corpus_check_distinguishes_malformed_from_absent_manifest(tmp_path):
    malformed = tmp_path / "malformed"
    malformed.mkdir()
    write_manifest(malformed, "manifest_version: wrong\n")

    findings = corpus_check(
        CorpusWriter(malformed, DefaultExecutor, authority=FULL, profile=WITH_BIOLOGY).read_view, WITH_BIOLOGY
    )

    assert [(finding.severity, finding.code, finding.ref) for finding in findings] == [
        ("error", "manifest-malformed", "corpus.yaml"),
        ("error", "profile-mismatch", "corpus.yaml"),
    ]
    assert findings[0].detail
    absent = corpus_check(
        CorpusWriter(tmp_path / "absent", DefaultExecutor, authority=FULL, profile=WITH_BIOLOGY).read_view,
        WITH_BIOLOGY,
    )
    # No manifest finding at all. The one warning is the register hygiene
    # report's: the empty corpus holds no assumptions register for the
    # activated `biology` contract (design section 9.2).
    assert [(finding.severity, finding.code, finding.detail) for finding in absent] == [
        ("warning", "register-missing", "biology")
    ]


@pytest.fixture
def repin_setup(tmp_path):
    from fixtures.repin import PortableFactory, repin_chain
    from profiles import pins_for

    data = repin_chain()
    factory = PortableFactory()
    writer = CorpusWriter(tmp_path, factory, authority=FULL, profile=data[2][0])
    writer.adopt_manifest(profile=pins_for(data[2][0]))
    factory.plans.clear()
    factory.recoveries.clear()
    return writer, factory, data


def test_repin_preserves_manifest_and_hashes_original_bytes(repin_setup):
    from dataclasses import replace
    from hashlib import sha256

    from nodes.core.write_plan import ReplaceOp
    from profiles import pins_for

    writer, factory, (_, contracts, profiles, _) = repin_setup
    before = replace(load_manifest(writer.root), forked_from=ForkedFrom("b" * 32, "c" * 64))
    original = b"# original presentation\n" + manifest_bytes(before)
    (writer.root / "corpus.yaml").write_bytes(original)
    result = writer.repin_domain(predecessor=contracts[0], successor=contracts[1], profile=profiles[1])
    assert result == replace(before, profile=pins_for(profiles[1]))
    assert factory.plans == [[ReplaceOp("corpus.yaml", manifest_bytes(result), sha256(original).hexdigest())]]
    assert len(factory.recoveries) == 1
    assert writer._state.unresolved
    assert load_manifest(writer.root) == result


@pytest.mark.parametrize("fault", ["unparsed", "uncompiled", "same", "jump", "wrong-old", "wrong-target", "activation"])
def test_repin_pure_refusal_has_no_io(repin_setup, fault):
    from beliefs.errors import ScienceError
    from beliefs.profile import compile_profile, shipped_base_contract

    writer, factory, (_, contracts, profiles, _) = repin_setup
    args = {"predecessor": contracts[0], "successor": contracts[1], "profile": profiles[1]}
    if fault == "unparsed":
        args["predecessor"] = object()
    if fault == "uncompiled":
        args["profile"] = object()
    if fault == "same":
        args["successor"] = contracts[0]
    if fault == "jump":
        args.update(successor=contracts[2], profile=profiles[2])
    if fault == "wrong-old":
        args.update(predecessor=contracts[1], successor=contracts[2], profile=profiles[2])
    if fault == "wrong-target":
        args["profile"] = profiles[0]
    if fault == "activation":
        args["profile"] = compile_profile(shipped_base_contract(), [])
    original = (writer.root / "corpus.yaml").read_bytes()
    with pytest.raises((ScienceError, TypeError)):
        writer.repin_domain(**args)
    assert factory.recoveries == factory.plans == []
    assert (writer.root / "corpus.yaml").read_bytes() == original


def test_repin_requires_recovery_callback(tmp_path):
    from fixtures.repin import repin_chain
    from profiles import pins_for

    from beliefs.errors import ScienceError

    _, contracts, profiles, _ = repin_chain()
    writer = CorpusWriter(tmp_path, DefaultExecutor, authority=FULL, profile=profiles[0])
    writer.adopt_manifest(profile=pins_for(profiles[0]))
    with pytest.raises(ScienceError, match="recovery"):
        writer.repin_domain(predecessor=contracts[0], successor=contracts[1], profile=profiles[1])


@pytest.mark.parametrize("visibility", ["old", "target"])
def test_repin_recovers_before_reading_visible_target(repin_setup, visibility):
    from dataclasses import replace

    from profiles import pins_for

    writer, factory, (_, contracts, profiles, _) = repin_setup
    old = load_manifest(writer.root)
    (writer.root / "corpus.yaml").write_bytes(manifest_bytes(replace(old, profile=pins_for(profiles[1]))))

    def recover(root):
        assert writer._state.unresolved
        if visibility == "old":
            (root / "corpus.yaml").write_bytes(manifest_bytes(old))

    factory.recovery = recover
    from beliefs.errors import ContractMismatch

    if visibility == "old":
        writer.repin_domain(predecessor=contracts[0], successor=contracts[1], profile=profiles[1])
    else:
        writer._state.unresolved = False
        with pytest.raises(ContractMismatch):
            writer.repin_domain(predecessor=contracts[0], successor=contracts[1], profile=profiles[1])
        assert factory.plans == []
    assert len(factory.recoveries) == 1 and writer._state.unresolved


def test_repin_validation_refusal_leaves_recovered_state_unresolved(repin_setup):
    writer, factory, (_, contracts, profiles, _) = repin_setup
    writer._state.unresolved = False

    def recover(root):
        assert writer._state.unresolved
        (root / "corpus.yaml").write_text("broken: true\n")

    factory.recovery = recover
    with pytest.raises(ManifestMalformed):
        writer.repin_domain(predecessor=contracts[0], successor=contracts[1], profile=profiles[1])
    assert writer._state.unresolved and factory.plans == []


@pytest.mark.parametrize("kind", ["missing", "symlink", "directory", "fifo", "malformed"])
def test_repin_refuses_nonregular_manifest(repin_setup, kind):
    import os

    from beliefs.errors import ScienceError

    writer, factory, (_, contracts, profiles, _) = repin_setup
    path = writer.root / "corpus.yaml"
    original = path.read_bytes()
    path.unlink()
    if kind == "symlink":
        (writer.root / "other").write_bytes(original)
        path.symlink_to("other")
    if kind == "directory":
        path.mkdir()
    if kind == "fifo":
        os.mkfifo(path)
    if kind == "malformed":
        path.write_text("manifest_version: 3\n")
    with pytest.raises(ScienceError):
        writer.repin_domain(predecessor=contracts[0], successor=contracts[1], profile=profiles[1])
    assert factory.plans == []


@pytest.mark.parametrize("change", ["drop", "required", "type", "attachment", "add"])
def test_repin_facet_preservation(repin_setup, change):
    from copy import deepcopy

    from beliefs.contract.domain import parse_domain_contract
    from beliefs.errors import RepinRefused
    from beliefs.profile import compile_profile, shipped_base_contract

    writer, factory, (documents, contracts, _, _) = repin_setup
    document = deepcopy(documents[1])
    facet = document["facets"]["label"]
    if change == "drop":
        del document["facets"]["label"]
    if change == "required":
        facet["fields"]["more"] = {"type": "string", "required": True}
    if change == "type":
        facet["fields"]["value"]["type"] = "integer"
    if change == "attachment":
        facet["attaches_to"] = ["source"]
    if change == "add":
        document["facets"]["other"] = deepcopy(facet)
    successor = parse_domain_contract(
        document, source="facet successor", base=shipped_base_contract(), predecessor=contracts[0]
    )
    target = compile_profile(shipped_base_contract(), [successor])
    if change == "add":
        writer.repin_domain(predecessor=contracts[0], successor=successor, profile=target)
    else:
        with pytest.raises(RepinRefused, match="facet"):
            writer.repin_domain(predecessor=contracts[0], successor=successor, profile=target)
        assert factory.plans == factory.recoveries == []


def test_repin_recovery_error_never_submits(repin_setup):
    writer, factory, (_, contracts, profiles, _) = repin_setup

    def fail(root):
        raise RuntimeError("unsettled")

    factory.recovery = fail
    with pytest.raises(RuntimeError, match="unsettled"):
        writer.repin_domain(predecessor=contracts[0], successor=contracts[1], profile=profiles[1])
    assert factory.plans == [] and writer._state.unresolved


def test_repin_during_capture_refuses(repin_setup):
    from beliefs.errors import BuildHold

    writer, factory, (_, contracts, profiles, _) = repin_setup
    with writer._state.lock.capture(), pytest.raises(BuildHold):
        writer.repin_domain(predecessor=contracts[0], successor=contracts[1], profile=profiles[1])
    assert factory.plans == factory.recoveries == []


def test_capture_during_repin_refuses(repin_setup):
    from beliefs.errors import BuildContended

    writer, factory, (_, contracts, profiles, _) = repin_setup

    def recover(root):
        with pytest.raises(BuildContended), writer._state.lock.capture():
            pytest.fail("capture entered during re-pin")

    factory.recovery = recover
    writer.repin_domain(predecessor=contracts[0], successor=contracts[1], profile=profiles[1])


@pytest.mark.parametrize("fault", ["namespace", "base", "activation", "unrelated", "coordination"])
def test_repin_unsupported_transition_has_no_effect(repin_setup, base_contract_path, fault):
    from copy import deepcopy

    import yaml

    from beliefs.contract import parse_base_contract, parse_domain_contract
    from beliefs.errors import ScienceError
    from beliefs.profile import compile_profile, shipped_base_contract, shipped_coordination

    writer, factory, (documents, contracts, profiles, _) = repin_setup
    args = {"predecessor": contracts[0], "successor": contracts[1], "profile": profiles[1]}
    document = deepcopy(documents[0])
    document["contract"] = "other"
    other = parse_domain_contract(document, source="other", base=shipped_base_contract(), predecessor=None)
    if fault == "namespace":
        args["successor"] = other
    elif fault == "base":
        document = yaml.safe_load(base_contract_path.read_text())
        document["claim_grammar"]["layers"].append("speculative")
        base = parse_base_contract(document, source="wide")
        args["successor"] = parse_domain_contract(documents[0], source="other base", base=base, predecessor=None)
    elif fault == "activation":
        args["profile"] = compile_profile(shipped_base_contract(), [contracts[1], other])
    elif fault == "unrelated":
        args["profile"] = compile_profile(shipped_base_contract(), [other])
    else:
        args["predecessor"] = shipped_coordination(2)
        args["successor"] = shipped_coordination(3)
    before = (writer.root / "corpus.yaml").read_bytes()
    with pytest.raises(ScienceError):
        writer.repin_domain(**args)
    assert (writer.root / "corpus.yaml").read_bytes() == before
    assert not factory.plans and not factory.recoveries
