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
        manifest_document()
        + "forked_from:\n"
        + "  corpus_id: "
        + "2" * 32
        + "\n  corpus_state: "
        + "3" * 64
        + "\n",
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
    second = CorpusWriter(tmp_path / "second", DefaultExecutor, authority=FULL, profile=WITH_BIOLOGY).adopt_manifest(profile=PINS)

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

    findings = corpus_check(CorpusWriter(malformed, DefaultExecutor, authority=FULL, profile=WITH_BIOLOGY).read_view, WITH_BIOLOGY)

    assert [(finding.severity, finding.code, finding.ref) for finding in findings] == [
        ("error", "manifest-malformed", "corpus.yaml"),
        ("error", "profile-mismatch", "corpus.yaml")
    ]
    assert findings[0].detail
    assert corpus_check(CorpusWriter(tmp_path / "absent", DefaultExecutor, authority=FULL, profile=WITH_BIOLOGY).read_view, WITH_BIOLOGY) == ()
