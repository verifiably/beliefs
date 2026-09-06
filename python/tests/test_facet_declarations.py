"""Design §3.1, §3.2, §3.4: the declaration grammar's closure, in the base contract."""

import copy
from typing import Any, cast

import pytest

from beliefs.contract import base
from beliefs.contract.facets import FacetDecl, FieldDecl, parse_facet_declarations
from beliefs.errors import MalformedContract


def parse(document):
    return base.parse_base_contract(document, source="<test>")


class TestTheShippedDeclarations:
    def test_the_thirteen_world_kinds_and_three_prose_kinds_are_declared(self, base_contract):
        assert {n for n, k in base_contract.kinds.items() if k.role == "prose"} == {
            "interpretation",
            "discussion",
            "story",
        }
        assert {n for n, k in base_contract.kinds.items() if k.role == "world"} == {
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
        }

    def test_the_deferred_kinds_carry_no_domain_and_no_facets(self, base_contract):
        for name in ("instrument-certification", "coreference-attestation"):
            assert base_contract.kinds[name].domain is None
            assert base_contract.kinds[name].facets == {}
            assert base_contract.kinds[name].role == "world"

    def test_a_prose_kind_may_carry_display_only_and_no_domain(self, base_contract):
        assert dict(base_contract.kinds["discussion"].facets) == {
            "display": base_contract.kinds["proposition"].facets["display"]
        }
        assert base_contract.kinds["discussion"].domain is None

    def test_a_prose_kind_declaring_a_domain_or_another_facet_is_refused(self, base_contract_path):
        from beliefs.contract.document import load_document

        doc = cast(dict[str, Any], load_document(base_contract_path, source="<t>"))
        bad = copy.deepcopy(doc)
        bad["kinds"]["story"]["domain"] = "science.story.v1"
        with pytest.raises(MalformedContract, match="prose"):
            parse(bad)
        bad = copy.deepcopy(doc)
        bad["kinds"]["story"]["facets"]["dataset"] = {"required": False, "covered": False}
        with pytest.raises(MalformedContract, match="prose"):
            parse(bad)

    def test_a_domain_string_is_checked_and_null_facets_are_refused(self, base_contract_path):
        from beliefs.contract.document import load_document

        doc = cast(dict[str, Any], load_document(base_contract_path, source="<t>"))
        bad = copy.deepcopy(doc)
        bad["kinds"]["dataset"]["domain"] = "dataset-v1"
        with pytest.raises(MalformedContract, match="science.<kind>.v<n>"):
            parse(bad)
        bad = copy.deepcopy(doc)
        bad["facets"]["empirical-observation"]["description"] = 7
        with pytest.raises(MalformedContract, match="description"):
            parse(bad)
        bad = copy.deepcopy(doc)
        bad["facets"] = None
        with pytest.raises(MalformedContract, match="mapping"):
            parse(bad)

    def test_dataset_declares_its_four_facets(self, base_contract):
        facets = base_contract.kinds["dataset"].facets
        assert facets["dataset"].required and facets["dataset"].covered
        assert not facets["empirical-observation"].required and facets["empirical-observation"].covered
        assert not facets["lineage-basis"].required and facets["lineage-basis"].covered
        assert not facets["display"].required and not facets["display"].covered

    def test_relations_come_in_two_groups(self, base_contract):
        world = {name for name, decl in base_contract.relations.items() if decl.group == "world"}
        lifecycle = {name for name, decl in base_contract.relations.items() if decl.group == "lifecycle"}
        assert world == {
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
        }
        assert lifecycle == {"supersedes", "retracts", "succeeded-by", "anchored_in"}
        assert base_contract.relations["retracts"].sources == ("retraction",)
        assert base_contract.relations["retracts"].targets == ("assessment", "retraction", "verification")

    def test_empirical_observation_is_the_one_schema_shaped_facet(self, base_contract):
        schema_shaped = [key for key, decl in base_contract.facets.items() if decl.shape == "schema"]
        assert schema_shaped == ["empirical-observation"]
        fields = base_contract.facets["empirical-observation"].fields
        assert fields["locator"] == FieldDecl("locator", "locator", True, (), ("accession", "url", "instrument"))
        assert fields["attested_by"] == FieldDecl("attested_by", "actor", True, (), ())
        assert fields["retrieval"] == FieldDecl("retrieval", "ref", False, ("act-report",), ())

    def test_every_facet_a_kind_names_is_declared(self, base_contract):
        for kind in base_contract.kinds.values():
            for key in kind.facets:
                assert key in base_contract.facets, f"{kind.name} names undeclared facet {key!r}"


class TestTheGrammarsClosure:
    @pytest.fixture()
    def document(self, base_contract_path) -> dict[str, Any]:
        from beliefs.contract.document import load_document

        return cast(dict[str, Any], load_document(base_contract_path, source="<test>"))

    def _with_field(self, document: dict[str, Any], field: object) -> dict[str, Any]:
        doc = copy.deepcopy(document)
        doc["facets"]["empirical-observation"]["fields"]["extra"] = field
        return doc

    def test_required_is_a_mandatory_boolean(self, document):
        with pytest.raises(MalformedContract, match="required"):
            parse(self._with_field(document, {"type": "string"}))
        with pytest.raises(MalformedContract, match="required"):
            parse(self._with_field(document, {"type": "string", "required": "yes"}))

    def test_kinds_only_with_ref_and_schemes_only_with_locator(self, document):
        with pytest.raises(MalformedContract, match="kinds"):
            parse(self._with_field(document, {"type": "string", "required": True, "kinds": ["dataset"]}))
        with pytest.raises(MalformedContract, match="kinds"):
            parse(self._with_field(document, {"type": "ref", "required": True}))
        with pytest.raises(MalformedContract, match="schemes"):
            parse(self._with_field(document, {"type": "ref", "required": True, "kinds": ["dataset"], "schemes": ["x"]}))
        with pytest.raises(MalformedContract, match="schemes"):
            parse(self._with_field(document, {"type": "locator", "required": True}))

    def test_kinds_and_schemes_are_non_empty_distinct_sets(self, document):
        with pytest.raises(MalformedContract, match="non-empty"):
            parse(self._with_field(document, {"type": "ref", "required": True, "kinds": []}))
        with pytest.raises(MalformedContract, match="duplicate"):
            parse(self._with_field(document, {"type": "locator", "required": True, "schemes": ["url", "url"]}))

    def test_an_unknown_type_and_an_unknown_field_key_are_refused(self, document):
        with pytest.raises(MalformedContract, match="type"):
            parse(self._with_field(document, {"type": "float", "required": True}))
        with pytest.raises(MalformedContract, match="unknown field"):
            parse(self._with_field(document, {"type": "string", "required": True, "default": "x"}))

    def test_a_field_name_must_be_an_identifier(self, document):
        doc = copy.deepcopy(document)
        doc["facets"]["empirical-observation"]["fields"]["Bad-Name"] = {"type": "string", "required": True}
        with pytest.raises(MalformedContract, match="identifier"):
            parse(doc)

    def test_a_kind_naming_an_undeclared_facet_is_refused(self, document):
        doc = copy.deepcopy(document)
        doc["kinds"]["dataset"]["facets"]["mystery"] = {"required": False, "covered": False}
        with pytest.raises(MalformedContract, match="mystery"):
            parse(doc)

    def test_a_shape_must_be_reader_or_schema_and_match_its_body(self, document):
        doc = copy.deepcopy(document)
        doc["facets"]["dataset"]["shape"] = "magic"
        with pytest.raises(MalformedContract, match="shape"):
            parse(doc)
        doc = copy.deepcopy(document)
        doc["facets"]["dataset"]["fields"] = {}
        with pytest.raises(MalformedContract, match="reader-shaped"):
            parse(doc)
        doc = copy.deepcopy(document)
        del doc["facets"]["empirical-observation"]["fields"]
        with pytest.raises(MalformedContract, match="schema-shaped"):
            parse(doc)

    def test_a_relation_must_name_a_group_and_declared_kinds(self, document):
        doc = copy.deepcopy(document)
        doc["relations"]["observes"]["group"] = "other"
        with pytest.raises(MalformedContract, match="group"):
            parse(doc)
        doc = copy.deepcopy(document)
        doc["relations"]["observes"]["targets"] = ["divergence"]
        with pytest.raises(MalformedContract, match="divergence"):
            parse(doc)

    def test_the_content_identity_covers_the_new_sections(self, document):
        before = parse(document).content_identity
        doc = copy.deepcopy(document)
        doc["facets"]["empirical-observation"]["fields"]["locator"]["schemes"].append("ftp")
        assert parse(doc).content_identity != before


def test_parse_facet_declarations_namespaces_domain_keys():
    declared = parse_facet_declarations(
        {"gene-axis": {"attaches_to": ["dataset"], "fields": {"axis": {"type": "string", "required": True}}}},
        where="<test>: facets",
        namespace="biology",
    )
    assert set(declared) == {"biology/gene-axis"}
    assert declared["biology/gene-axis"] == FacetDecl(
        key="biology/gene-axis",
        shape="schema",
        fields={"axis": FieldDecl("axis", "string", True, (), ())},
        attaches_to=("dataset",),
        description=None,
    )
