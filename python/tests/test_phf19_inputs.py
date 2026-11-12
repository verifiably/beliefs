"""Synthetic references are complete small files, never a real release claim."""

import json
from pathlib import Path

import pytest
from conftest import REPO_ROOT
from reproduction import analysis_inputs as inputs

FIXTURE = REPO_ROOT / "fixtures/phf19"


def declaration():
    return json.loads((FIXTURE / "declaration.json").read_text())


def resolved():
    return inputs.resolve_phf19(
        declaration(),
        predecessor=FIXTURE / "predecessor",
        hgnc=FIXTURE / "hgnc.tsv",
        ensembl=FIXTURE / "ensembl.gtf.gz",
    )


def test_selected_question_and_provenance_are_explicit():
    assert hasattr(inputs, "resolve_phf19"), "explicit PHF19 resolver is missing"
    value = resolved()
    assert (value.feature, value.gene, value.factor, value.baseline, value.comparison) == (
        "ENSG00000119403",
        "hgnc:24566",
        "concept:disease-stage",
        "level:ndmm",
        "level:pd",
    )
    assert value.mapping_members == b"ensembl:ENSG00000119403\thgnc:24566\n"
    assert value.mapping.cardinality == "one-to-one" and value.mapping.aggregation is None
    assert value.mapping.source_sort == "biology/ensembl-gene" and value.mapping.target_sort == "biology/gene"
    assert value.mapping.reference["evidence"] == "synthetic"


@pytest.mark.parametrize(
    "key,value",
    [
        ("feature", "ENSG00000121410"),
        ("gene", "protein:PHF19"),
        ("factor", "concept:other"),
        ("hgnc_release", "latest"),
        ("assembly", "GRCm39"),
        ("comparison", "level:ndmm"),
    ],
)
def test_altered_question_or_release_refuses(key, value):
    d = declaration()
    d[key] = value
    with pytest.raises(inputs.InputsRefused):
        inputs.resolve_phf19(
            d, predecessor=FIXTURE / "predecessor", hgnc=FIXTURE / "hgnc.tsv", ensembl=FIXTURE / "ensembl.gtf.gz"
        )


def test_reference_byte_pin_is_checked_before_correspondence(tmp_path):
    bad = tmp_path / "hgnc.tsv"
    bad.write_bytes((FIXTURE / "hgnc.tsv").read_bytes() + b"\n")
    with pytest.raises(inputs.InputsRefused, match="digest"):
        inputs.resolve_phf19(
            declaration(), predecessor=FIXTURE / "predecessor", hgnc=bad, ensembl=FIXTURE / "ensembl.gtf.gz"
        )


def test_membership_is_complete_and_not_filtered_by_selected_row():
    assert inputs.hgnc_members((FIXTURE / "hgnc.tsv").read_bytes()) == b"hgnc:24566\nhgnc:5\n"


@pytest.mark.parametrize("content", [b"symbol\nPHF19\n", b"hgnc_id\nHGNC:0\n", b"hgnc_id\nHGNC:5\nHGNC:5\n"])
def test_invalid_or_duplicate_member_ids_refuse(content):
    with pytest.raises(inputs.InputsRefused):
        inputs.hgnc_members(content)


def test_synthetic_reference_cannot_masquerade_as_pinned_real_release():
    d = declaration()
    d["evidence"] = "held-release"
    with pytest.raises(inputs.InputsRefused):
        inputs.resolve_phf19(
            d, predecessor=FIXTURE / "predecessor", hgnc=FIXTURE / "hgnc.tsv", ensembl=FIXTURE / "ensembl.gtf.gz"
        )


def test_incomplete_or_stale_membership_derivation_refuses():
    from hashlib import sha256

    from reproduction import vocabulary

    original = (FIXTURE / "hgnc.tsv").read_bytes()
    members = inputs.hgnc_members(original)
    manifest = {
        "release": "2025-09-05",
        "source_sha256": sha256(original).hexdigest(),
        "parser_sha256": sha256(Path(inputs.__file__).read_bytes()).hexdigest(),
        "output_sha256": sha256(members).hexdigest(),
        "member_count": 2,
    }
    vocabulary.check_members(original, members, json.dumps(manifest).encode())
    with pytest.raises(RuntimeError, match="incomplete"):
        vocabulary.check_members(original, b"hgnc:24566\n", json.dumps(manifest).encode())


@pytest.mark.parametrize("change", ["duplicate", "unapproved", "wrong-link"])
def test_ambiguous_or_unapproved_correspondence_refuses_even_with_matching_byte_pin(tmp_path, change):
    from hashlib import sha256

    content = (FIXTURE / "hgnc.tsv").read_bytes()
    if change == "duplicate":
        content += b"HGNC:6\tother\tApproved\tENSG00000119403\n"
    elif change == "unapproved":
        content = content.replace(b"PHF19\tApproved", b"PHF19\tWithdrawn")
    else:
        content = content.replace(b"ENSG00000119403", b"ENSG00000121410")
    path = tmp_path / "hgnc.tsv"
    path.write_bytes(content)
    d = declaration()
    d["digests"]["hgnc"] = sha256(content).hexdigest()
    with pytest.raises(inputs.InputsRefused, match="correspondence"):
        inputs.resolve_phf19(d, predecessor=FIXTURE / "predecessor", hgnc=path, ensembl=FIXTURE / "ensembl.gtf.gz")
