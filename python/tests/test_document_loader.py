"""A duplicate mapping key is refused at load, at every depth, never kept last."""

import pytest

from beliefs.contract.document import load_document
from beliefs.errors import MalformedContract


def test_a_top_level_duplicate_key_is_refused(tmp_path):
    path = tmp_path / "c.yaml"
    path.write_text("contract: a\ncontract: b\n")
    with pytest.raises(MalformedContract, match="duplicate key 'contract'"):
        load_document(path, source="<test>")


def test_a_nested_duplicate_key_is_refused(tmp_path):
    path = tmp_path / "c.yaml"
    path.write_text(
        "facets:\n  x:\n    fields:\n      locator: {type: string, required: true}\n      locator: {type: string, required: true}\n"
    )
    with pytest.raises(MalformedContract, match="duplicate key 'locator'"):
        load_document(path, source="<test>")


def test_a_well_formed_document_loads_as_plain_values(tmp_path):
    path = tmp_path / "c.yaml"
    path.write_text("a: 1\nb: [x, y]\nc: {d: true}\n")
    assert load_document(path, source="<test>") == {"a": 1, "b": ["x", "y"], "c": {"d": True}}


def test_a_non_string_mapping_key_is_refused_not_crashed(tmp_path):
    path = tmp_path / "c.yaml"
    path.write_text("? [a, b]\n: 1\n")
    with pytest.raises(MalformedContract, match="not a string"):
        load_document(path, source="<test>")


def test_malformed_yaml_is_refused_as_a_contract_error(tmp_path):
    path = tmp_path / "c.yaml"
    path.write_text("a: [\n")
    with pytest.raises(MalformedContract, match="not well-formed YAML"):
        load_document(path, source="<test>")


def test_a_single_quoted_pattern_keeps_its_escape_verbatim(tmp_path):
    # Identifier-class patterns are written as single-quoted scalars, which keep
    # the backslash: `\-` reaches the pattern grammar as two characters.
    path = tmp_path / "c.yaml"
    path.write_text("identifier_class: { prefix: EX, pattern: 'EX:[a-z0-9\\-]+' }\n")
    assert load_document(path, source="<test>") == {"identifier_class": {"prefix": "EX", "pattern": "EX:[a-z0-9\\-]+"}}


def test_a_double_quoted_pattern_with_a_class_escape_is_refused(tmp_path):
    # A double-quoted scalar reads `\-` as a YAML escape, which YAML does not
    # define, so the document is refused rather than read with the escape lost.
    path = tmp_path / "c.yaml"
    path.write_text('identifier_class: { prefix: EX, pattern: "EX:[a-z0-9\\-]+" }\n')
    with pytest.raises(MalformedContract, match="not well-formed YAML"):
        load_document(path, source="<test>")
