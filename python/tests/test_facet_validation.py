# python/tests/test_facet_validation.py
"""§3.4's grammar at validation time, and §4.1's compiled products — immutable, one registry, private."""

import copy
from dataclasses import FrozenInstanceError
from typing import cast

import pytest
from nodes.core.errors import FacetError, UnknownKindError
from nodes.core.node import Node
from nodes.core.registry import Registry

import beliefs.profile as profile_module
from beliefs.contract import domain, parse_base_contract
from beliefs.contract.base import FacetUse
from beliefs.contract.document import load_document
from beliefs.errors import FacetPayloadRefused, ProfileError
from beliefs.facets import validate_payload
from beliefs.profile import compile_profile


@pytest.fixture()
def testing(base_contract, testing_document):
    return domain.parse_domain_contract(testing_document, source="<t>", base=base_contract, predecessor=None)


@pytest.fixture()
def profile(base_contract, testing):
    return compile_profile(base_contract, [testing])


def reparse(document, source="<t>"):
    return parse_base_contract(document, source=source)


class TestCompiledProducts:
    def test_kinds_and_facets_are_compiled(self, profile):
        assert profile.kinds["dataset"].covered == ("dataset", "empirical-observation", "lineage-basis")
        assert profile.kinds["dataset"].role == "world"
        assert profile.kinds["instrument-certification"].domain is None
        assert profile.kinds["discussion"].role == "prose" and profile.kinds["discussion"].domain is None
        assert profile.facets["empirical-observation"].shape == "schema"
        assert profile.facets["testing/axis"].attaches_to == frozenset({"dataset"})

    def test_nothing_compiled_is_mutable(self, profile):
        with pytest.raises(TypeError):
            profile.kinds["x"] = None  # type: ignore[index]
        with pytest.raises(TypeError):
            profile.kinds["dataset"].facets["x"] = FacetUse(True, True)  # type: ignore[index]
        with pytest.raises((TypeError, AttributeError)):
            profile.facets["empirical-observation"].fields.pop("locator")  # type: ignore[attr-defined]
        with pytest.raises(AttributeError):
            profile.kinds["dataset"].facets["dataset"].required = False  # type: ignore[misc]
        assert "registry" not in dir(profile)  # no public registry, no public route to `register`
        with pytest.raises(FrozenInstanceError):
            profile._registry = Registry()  # type: ignore[misc]  # the private slot is frozen with the rest

    def test_facets_of_a_kind_include_attached_domain_facets(self, profile):
        assert set(profile.facets_of("dataset")) == {
            "dataset",
            "empirical-observation",
            "lineage-basis",
            "display",
            "testing/axis",
            "testing/annotation",
        }
        assert set(profile.facets_of("run")) == {"run", "run-closure"}
        assert set(profile.facets_of("discussion")) == {"display"}

    def test_one_kindspec_per_kind_registered_once_and_validation_is_exposed_without_the_registry(
        self, base_contract, testing, monkeypatch
    ):
        calls: list[str] = []
        original = Registry.register

        def counting(self, spec):
            calls.append(spec.name)
            return original(self, spec)

        monkeypatch.setattr(Registry, "register", counting)
        compiled = compile_profile(base_contract, [testing])
        assert sorted(calls) == sorted(compiled.kinds) and len(calls) == len(set(calls))
        compiled.validate_document(
            Node(id="dataset:x", kind="dataset", title="x", facets={"dataset": {"resources": []}})
        )
        with pytest.raises(FacetError, match="unexpected"):
            compiled.validate_document(
                Node(id="dataset:y", kind="dataset", title="y", facets={"dataset": {}, "biology/gene-axis": {}})
            )
        with pytest.raises(UnknownKindError):
            compiled.validate_document(Node(id="divergence:z", kind="divergence", title="z", facets={}))
        codes = [
            v.code for v in compiled.document_violations(Node(id="dataset:w", kind="dataset", title="w", facets={}))
        ]
        assert codes == ["facet-missing"]

    def test_a_domain_facet_attaching_to_an_undeclared_or_prose_kind_refuses_the_compile(
        self, base_contract, testing_document
    ):
        for kind in ("divergence", "discussion"):
            doc = copy.deepcopy(testing_document)
            doc["facets"]["axis"]["attaches_to"] = [kind]
            contract = domain.parse_domain_contract(doc, source="<t>", base=base_contract, predecessor=None)
            with pytest.raises(ProfileError, match=kind):
                compile_profile(base_contract, [contract])

    def test_a_ref_field_naming_an_undeclared_kind_refuses_the_compile(self, base_contract, testing_document):
        doc = copy.deepcopy(testing_document)
        doc["facets"]["axis"]["fields"]["vocabulary"]["kinds"] = ["ontology"]
        contract = domain.parse_domain_contract(doc, source="<t>", base=base_contract, predecessor=None)
        with pytest.raises(ProfileError, match="ontology"):
            compile_profile(base_contract, [contract])

    def test_every_profile_has_an_identity_and_undomained_kinds_encode_without_null(self, base_contract):
        compiled = compile_profile(base_contract, [])
        assert len(compiled.compiled_identity) == 64
        projection = cast(dict, compiled.projection()["kinds"])["instrument-certification"]
        assert "domain" not in projection and projection["role"] == "world"

    def test_the_compiled_identity_moves_on_every_behavioural_declaration(self, base_contract, testing_document):
        base_identity = compile_profile(base_contract, []).compiled_identity
        contract = domain.parse_domain_contract(testing_document, source="<t>", base=base_contract, predecessor=None)
        with_facets = compile_profile(base_contract, [contract]).compiled_identity
        assert with_facets != base_identity
        doc = copy.deepcopy(testing_document)
        doc["facets"]["axis"]["attaches_to"] = ["dataset", "proposition"]
        moved = domain.parse_domain_contract(doc, source="<t>", base=base_contract, predecessor=None)
        assert compile_profile(base_contract, [moved]).compiled_identity != with_facets
        doc = copy.deepcopy(testing_document)
        doc["facets"]["axis"]["description"] = "editorial"
        editorial = domain.parse_domain_contract(doc, source="<t>", base=base_contract, predecessor=None)
        assert compile_profile(base_contract, [editorial]).compiled_identity == with_facets

    def test_reordering_declarations_moves_neither_identity_nor_coverage(self, base_contract_path):
        doc = cast(dict, load_document(base_contract_path, source="<t>"))
        reordered = copy.deepcopy(doc)
        reordered["kinds"] = dict(reversed(list(doc["kinds"].items())))
        reordered["kinds"]["dataset"]["facets"] = dict(reversed(list(doc["kinds"]["dataset"]["facets"].items())))
        reordered["facets"] = dict(reversed(list(doc["facets"].items())))
        reordered["relations"] = dict(reversed(list(doc["relations"].items())))
        a = compile_profile(reparse(doc, "<a>"), [])
        b = compile_profile(reparse(reordered, "<b>"), [])
        assert a.compiled_identity == b.compiled_identity
        assert a.kinds["dataset"].covered == b.kinds["dataset"].covered

    def test_moving_a_relation_between_groups_moves_the_compiled_identity(self, base_contract_path):
        doc = cast(dict, load_document(base_contract_path, source="<t>"))
        moved = copy.deepcopy(doc)
        moved["relations"]["grounded-in"]["group"] = "lifecycle"
        assert (
            compile_profile(reparse(doc, "<a>"), []).compiled_identity
            != compile_profile(reparse(moved, "<b>"), []).compiled_identity
        )


class TestPayloadValidation:
    def facet(self, profile):
        return profile.facets["empirical-observation"]

    def test_a_valid_declaration_validates(self, profile):
        validate_payload(self.facet(profile), {"locator": "accession:GSE179929", "attested_by": "keith"}, where="d")

    @pytest.mark.parametrize(
        "payload, reason",
        [
            ({"boundary": "acquisition", "source": "x", "asserted_by": "y"}, "unknown key"),
            ({"attested_by": "keith"}, "missing required field 'locator'"),
            ({"locator": "ftp:x", "attested_by": "keith"}, "scheme 'ftp'"),
            ({"locator": "accession:", "attested_by": "keith"}, "empty"),
            ({"locator": "url", "attested_by": "keith"}, "empty"),
            ({"locator": 7, "attested_by": "keith"}, "locator"),
            ({"locator": "url:x", "attested_by": ""}, "attested_by"),
            ({"locator": "url:x", "attested_by": "k", "retrieval": "dataset:z"}, "kind 'dataset'"),
            ({"locator": "url:x", "attested_by": "k", "retrieval": "act-report:"}, "empty"),
            ({"locator": "url:x", "attested_by": "k", "retrieval": None}, "null"),
            ({"locator": "url:x", "attested_by": {"name": "k"}}, "nested"),
            ({"locator": "url:x", "attested_by": ["k"]}, "nested"),
            ({"locator": "url:x", "attested_by": ("k",)}, "nested"),
        ],
    )
    def test_every_malformation_is_refused_with_its_reason(self, profile, payload, reason):
        with pytest.raises(FacetPayloadRefused, match=reason):
            validate_payload(self.facet(profile), payload, where="d")

    def test_integer_and_boolean_keep_their_types(self, profile):
        annotation = profile.facets["testing/annotation"]
        validate_payload(annotation, {"note": "n", "count": 3, "final": False}, where="d")
        with pytest.raises(FacetPayloadRefused, match="integer"):
            validate_payload(annotation, {"note": "n", "count": True}, where="d")
        with pytest.raises(FacetPayloadRefused, match="integer"):
            validate_payload(annotation, {"note": "n", "count": 3.5}, where="d")
        with pytest.raises(FacetPayloadRefused, match="boolean"):
            validate_payload(annotation, {"note": "n", "final": 1}, where="d")

    def test_a_reader_shaped_facet_validates_nothing_here(self, profile):
        validate_payload(profile.facets["dataset"], {"anything": "goes"}, where="d")


def test_profile_imports_nothing_from_stored():
    assert "stored" not in profile_module.__dict__


@pytest.mark.parametrize("kind", ["dataset", "discussion"])
def test_coordination_kind_collision_refused(base_contract, kind):
    from coordination_fixtures import COORDINATION_DOCUMENT, coordination_contract

    doc = copy.deepcopy(COORDINATION_DOCUMENT)
    doc["kinds"][kind] = doc["kinds"].pop("note")
    with pytest.raises(ProfileError, match=kind):
        compile_profile(base_contract, [], coordination=coordination_contract(doc))


def test_coordination_facet_and_single_registration(base_contract, monkeypatch):
    from coordination_fixtures import coordination_contract

    calls = []
    original = Registry.register

    def register(self, spec):
        calls.append(spec.name)
        return original(self, spec)

    monkeypatch.setattr(Registry, "register", register)
    profile = compile_profile(base_contract, [], coordination=coordination_contract())
    assert sorted(calls) == sorted(profile.kinds)
    assert set(profile.facets_of("project")) == {"coordination"}
    assert profile.facets["coordination"].contract == "coordination"
    profile.validate_document(Node(id="project:x", kind="project", title="x", facets={"coordination": {}}))
    with pytest.raises(FacetError, match="missing"):
        profile.validate_document(Node(id="project:x", kind="project", title="x"))


def test_coordination_facet_collision_refused(base_contract_path):
    from coordination_fixtures import coordination_contract

    doc = cast(dict, load_document(base_contract_path, source="<t>"))
    doc["facets"]["coordination"] = {"shape": "reader", "reader": "test"}
    with pytest.raises(ProfileError, match="coordination"):
        compile_profile(reparse(doc), [], coordination=coordination_contract())


def test_base_ref_kind_resolution_refused(base_contract_path):
    doc = cast(dict, load_document(base_contract_path, source="<t>"))
    doc["facets"]["empirical-observation"]["fields"]["retrieval"]["kinds"] = ["missing"]
    with pytest.raises(ProfileError, match="missing"):
        compile_profile(reparse(doc), [])


def test_unknown_kind_facets_refused(profile):
    with pytest.raises(ProfileError, match="missing"):
        profile.facets_of("missing")


@pytest.mark.parametrize("payload", [None, [], "text", 1])
def test_payload_must_be_a_mapping(profile, payload):
    with pytest.raises(FacetPayloadRefused, match="mapping"):
        validate_payload(profile.facets["empirical-observation"], payload, where="test")


def test_mixed_unknown_keys_refused(profile):
    with pytest.raises(FacetPayloadRefused, match="unknown key"):
        validate_payload(profile.facets["empirical-observation"], {1: "x", "z": "x"}, where="test")


def test_domain_facets_refuse_coordination_kind(base_contract, testing_document):
    from coordination_fixtures import coordination_contract

    testing_document["facets"]["axis"]["attaches_to"] = ["project"]
    contract = domain.parse_domain_contract(testing_document, source="<t>", base=base_contract, predecessor=None)
    with pytest.raises(ProfileError, match="project"):
        compile_profile(base_contract, [contract], coordination=coordination_contract())


def test_registry_allows_only_declared_facets_and_implicit_governed_stamp(profile):
    profile.validate_document(
        Node(
            id="dataset:x",
            kind="dataset",
            title="x",
            facets={
                "dataset": {},
                "semantic-identity": {},
                "testing/axis": {"axis": "x"},
                "display": {},
            },
        )
    )
    with pytest.raises(FacetError, match="unexpected"):
        profile.validate_document(
            Node(id="discussion:x", kind="discussion", title="x", facets={"semantic-identity": {}})
        )
    with pytest.raises(TypeError):
        profile.facets_of("dataset")["x"] = None
    with pytest.raises(TypeError):
        profile.relations["x"] = None
    with pytest.raises(AttributeError):
        profile.relations["retracts"].sources += ("dataset",)


@pytest.mark.parametrize(
    "path, value",
    [
        (("kinds", "dataset", "domain"), "science.dataset.v2"),
        (("kinds", "dataset", "facets", "display", "required"), True),
        (("kinds", "dataset", "facets", "display", "covered"), True),
        (("relations", "retracts", "sources"), ["dataset"]),
        (("relations", "retracts", "targets"), ["dataset"]),
        (("facets", "empirical-observation", "fields", "attested_by", "type"), "string"),
        (("facets", "empirical-observation", "fields", "attested_by", "required"), False),
        (("facets", "empirical-observation", "fields", "locator", "schemes"), ["url"]),
        (("facets", "empirical-observation", "fields", "retrieval", "kinds"), ["dataset"]),
    ],
)
def test_behavioral_projection_changes_identity(base_contract_path, path, value):
    doc = cast(dict, load_document(base_contract_path, source="<t>"))
    before = compile_profile(reparse(doc), []).compiled_identity
    target = doc
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    assert compile_profile(reparse(doc), []).compiled_identity != before
