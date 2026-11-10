"""Domain contracts under base v2, and succession.

The succession checks are here. The deferred check — *"consulted belief
digests move"* on an additive successor — needs belief, which this module does not
compute, and is not asserted anywhere below.
"""

import copy
import json

import pytest
import yaml

from beliefs.contract import domain
from beliefs.errors import MalformedContract, SubclassRefused, SuccessionViolation
from beliefs.identity import v1
from beliefs.patterns import IdentifierClass

HEX = {digit: digit * 64 for digit in "0123456789abcdef"}


@pytest.fixture()
def parse(base_contract):
    def _parse(
        document: object,
        source: str = "<test>",
        predecessor: domain.DomainContract | None = None,
    ) -> domain.DomainContract:
        return domain.parse_domain_contract(document, source=source, base=base_contract, predecessor=predecessor)

    return _parse


def successor_document(document, predecessor, **sections):
    successor = copy.deepcopy(document)
    successor["lineage"] = {"successor": predecessor.content_identity}
    successor["version"] = predecessor.version + 1
    successor.update(sections)
    return successor


class TestTheTestingContract:
    def test_v2_testing_contract_parses(self, parse, testing_document):
        contract = parse(testing_document)
        assert contract.namespace == "testing"
        assert contract.predecessor is None  # genesis
        assert set(contract.sorts) == {
            "entity",
            "outcome",
            "method",
            "level",
            "measure",
            "identification",
            "cohort",
            "event",
            "product",
            "procedure-spec",
            "population",
        }
        assert set(contract.dimensions) == {"population", "setting", "follow-up"}
        assert set(contract.templates) == {"affects", "correlates-with", "transforms", "measured-by"}
        assert set(contract.instantiations) == {
            "affects-entity-outcome",
            "affects-entity-entity",
            "correlates-entity-outcome",
            "correlates-event-product",
            "transforms-entities",
            "measured-by-entity-method",
            "promotes",
        }
        assert set(contract.bridges) == {"promotes"}
        assert set(contract.estimands) == {
            "instantiation:affects-entity-outcome",
            "instantiation:affects-entity-entity",
            "instantiation:correlates-event-product",
            "bridge:promotes",
            "instantiation:promotes",
        }
        assert set(contract.duration_conventions) == {"day"}
        assert contract.duration_conventions["day"].fields == {"unit": "hours", "length": 24}
        assert set(contract.facets) == {"testing/axis", "testing/annotation"}
        assert (
            len(contract.quantity_kinds),
            len(contract.units),
            len(contract.constants),
            len(contract.conversions),
            len(contract.transformations),
        ) == (10, 15, 1, 6, 8)

    def test_the_declarations_read_as_written(self, parse, testing_document):
        contract = parse(testing_document)
        affects = contract.templates["affects"]
        assert (affects.sign_apt, affects.layers, affects.forms, affects.edge) == (
            True,
            ("causal", "statistical"),
            ("polar", "null"),
            ("cause", "effect"),
        )
        assert affects.roles["cause"] == domain.RoleDecl(
            name="cause", arity="one", min=1, max=1, coefficients=False, constraint=()
        )
        parties = contract.templates["correlates-with"].roles["parties"]
        assert (parties.arity, parties.min, parties.max) == ("many", 2, 2)
        transforms = contract.templates["transforms"]
        assert transforms.roles["inputs"].coefficients is True
        assert (transforms.roles["facilitators"].min, transforms.roles["facilitators"].max) == (0, None)
        assert transforms.edge == ("inputs", "outputs")
        assert contract.templates["measured-by"].edge is None

        assert contract.instantiations["affects-entity-entity"].roles == {
            "cause": ("entity",),
            "effect": ("entity", "outcome"),
        }
        bridge = contract.bridges["promotes"]
        assert (bridge.template, bridge.mapping, bridge.layers) == ("affects", "narrower", ("causal",))

        population = contract.dimensions["population"]
        assert (population.restriction_sort, population.placement, population.applies_to) == (
            "cohort",
            "claim",
            ("affects", "correlates-with", "promotes"),
        )
        assert contract.dimensions["follow-up"].placement == "applicability"
        assert contract.sorts["entity"].categories == ("set",)
        assert contract.sorts["entity"].identifier_class == IdentifierClass("EX", "EX:[a-z0-9\\-]+")
        assert contract.sorts["procedure-spec"].identifier_class is None

    def test_term_identifiers_are_namespaced(self, parse, testing_document):
        # Authored, stable, namespaced — and it is what enters π_claim.
        assert parse(testing_document).term("affects") == "testing/affects"

    def test_the_sort_and_the_dimension_population_coexist(self, parse, testing_document):
        # Separate tables are separate namespaces (R13).
        contract = parse(testing_document)
        assert "population" in contract.sorts and "population" in contract.dimensions


class TestTopLevelFields:
    @pytest.mark.parametrize("section", ["operators", "edges", "vocabulary"])
    def test_a_v1_or_unknown_top_level_field_is_refused(self, parse, testing_document, section):
        testing_document[section] = {}
        with pytest.raises(MalformedContract, match=f"unknown field.*{section}"):
            parse(testing_document)

    def test_v1_biology_document_refuses(self, parse):
        # The pack the package shipped under base v1, verbatim but for comments.
        # A v1 document cannot parse under base v2 by accident.
        document = yaml.safe_load(
            """
contract: biology
version: 1
lineage: genesis

sorts:
  molecular-entity:
    vocabulary: { namespace: HGNC, release: "2026-07-01" }

dimensions: {}

operators:
  affects-molecular-entity-molecular-entity:
    arity: 2
    arg_sorts: [molecular-entity, molecular-entity]
    sign_apt: true
    layers: [causal, structural, statistical]
    dimensions: []
  associates-with-molecular-entity-molecular-entity:
    arity: 2
    arg_sorts: [molecular-entity, molecular-entity]
    sign_apt: true
    layers: [statistical, causal]
    dimensions: []
  regulates-molecular-entity-molecular-entity:
    arity: 2
    arg_sorts: [molecular-entity, molecular-entity]
    sign_apt: true
    layers: [causal]
    dimensions: []

facets:
  gene-axis:
    attaches_to: [dataset]
    fields:
      axis: { type: string, required: true }
      namespace: { type: string, required: true }
"""
        )
        with pytest.raises(MalformedContract, match="operators"):
            parse(document)

    @pytest.mark.parametrize("section", ["templates", "instantiations", "bridges", "estimands", "duration_conventions"])
    def test_the_optional_tables_may_be_absent(self, parse, testing_document, section):
        del testing_document[section]
        if section in ("templates", "instantiations", "bridges"):
            # The estimands and dimensions name them; drop those too.
            testing_document.pop("estimands", None)
            for dimension in testing_document["dimensions"].values():
                dimension["applies_to"] = []
            if section == "templates":
                testing_document.pop("bridges", None)
        contract = parse(testing_document)
        assert getattr(contract, section) == {}

    def test_a_domain_declaring_kinds_or_relations_is_refused(self, parse, testing_document):
        for section in ("kinds", "relations"):
            doc = copy.deepcopy(testing_document)
            doc[section] = {}
            with pytest.raises(MalformedContract, match=f"a domain contract declares no {section}"):
                parse(doc)


class TestNamespaceRules:
    def test_a_domain_contract_named_science_is_refused(self, parse, testing_document):
        testing_document["contract"] = "science"
        with pytest.raises(MalformedContract, match="domain-issued without exception"):
            parse(testing_document)

    def test_a_domain_contract_cannot_claim_the_coordination_namespace(self, parse, testing_document):
        testing_document["contract"] = "coordination"
        with pytest.raises(MalformedContract, match="reserved"):
            parse(testing_document)

    def test_a_namespaced_reference_is_deferred_to_compile(self, parse, testing_document):
        testing_document["instantiations"]["affects-entity-outcome"]["roles"]["effect"] = ["other/thing"]
        testing_document["dimensions"]["population"]["restriction_sort"] = "other/cohort"
        testing_document["dimensions"]["population"]["applies_to"] = ["other/relates"]
        contract = parse(testing_document)
        assert contract.instantiations["affects-entity-outcome"].roles["effect"] == ("other/thing",)
        assert contract.dimensions["population"].restriction_sort == "other/cohort"
        assert contract.dimensions["population"].applies_to == ("other/relates",)

    def test_a_bare_undeclared_sort_is_refused(self, parse, testing_document):
        testing_document["instantiations"]["affects-entity-outcome"]["roles"]["effect"] = ["thing"]
        with pytest.raises(MalformedContract, match="not a sort this contract declares"):
            parse(testing_document)

    @pytest.mark.parametrize(
        ("path", "value"),
        [
            (("instantiations", "affects-entity-outcome", "roles", "effect"), ["testing/outcome"]),
            (("dimensions", "population", "restriction_sort"), "testing/cohort"),
            (("dimensions", "population", "applies_to"), ["testing/affects"]),
            (("instantiations", "affects-entity-outcome", "template"), "testing/affects"),
            (("bridges", "promotes", "template"), "testing/affects"),
        ],
    )
    def test_a_self_prefixed_local_reference_is_refused(self, parse, testing_document, path, value):
        target = testing_document
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value
        with pytest.raises(MalformedContract, match="own namespace"):
            parse(testing_document)

    @pytest.mark.parametrize(
        ("path", "value"),
        [
            (("dimensions", "population", "restriction_sort"), "science/cohort"),
            (("instantiations", "affects-entity-outcome", "roles", "effect"), ["science/outcome"]),
            (("dimensions", "population", "applies_to"), ["science/affects"]),
        ],
    )
    def test_the_base_namespace_is_refused(self, parse, testing_document, path, value):
        target = testing_document
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value
        with pytest.raises(MalformedContract, match="base contract"):
            parse(testing_document)

    def test_a_malformed_reference_is_refused(self, parse, testing_document):
        for bad in ("Other/thing", "other/", "/thing", "a/b/c"):
            broken = copy.deepcopy(testing_document)
            broken["instantiations"]["affects-entity-outcome"]["roles"]["effect"] = [bad]
            with pytest.raises(MalformedContract):
                parse(broken)


class TestSortBindings:
    def test_each_arm_parses_from_the_fixture(self, parse, testing_document):
        sorts = parse(testing_document).sorts
        assert sorts["entity"].binding == domain.ReleaseBinding(namespace="EX", release="2026-01-01")
        assert sorts["cohort"].binding == domain.DatasetBinding(dataset="dataset:" + HEX["0"])
        assert sorts["method"].binding == domain.SchemeBinding(scheme="EX", version="1")
        assert sorts["event"].binding == domain.SelectionBinding(
            dataset="dataset:" + HEX["1"],
            rule="classification-rule:" + HEX["2"],
            selected="dataset:" + HEX["3"],
            annotator="EX-annotator",
        )
        assert sorts["product"].binding == domain.RunOutputBinding(run="run:" + HEX["4"], dataset="dataset:" + HEX["5"])
        assert sorts["procedure-spec"].binding == domain.WorldKindBinding(world_kind="procedure")

    def test_six_binding_arms_project_injectively(self):
        # The kind tag is in every projection, so two arms whose remaining fields
        # coincide (`dataset` alone, against `run-output`'s `dataset`) never encode alike.
        bindings = [
            domain.ReleaseBinding(namespace="EX", release="2026-01-01"),
            domain.DatasetBinding(dataset="dataset:" + HEX["0"]),
            domain.SchemeBinding(scheme="EX", version="2026-01-01"),
            domain.SelectionBinding(
                dataset="dataset:" + HEX["0"],
                rule="classification-rule:" + HEX["0"],
                selected="dataset:" + HEX["0"],
                annotator="EX",
            ),
            domain.RunOutputBinding(run="run:" + HEX["0"], dataset="dataset:" + HEX["0"]),
            domain.WorldKindBinding(world_kind="procedure"),
        ]
        projections = [binding.projection() for binding in bindings]
        assert [p["kind"] for p in projections] == [
            "release",
            "dataset",
            "scheme",
            "selection",
            "run-output",
            "world-kind",
        ]
        assert [binding.kind for binding in bindings] == [p["kind"] for p in projections]
        assert len({v1.encode(p) for p in projections}) == 6

    def test_distinct_values_on_one_arm_project_distinctly(self):
        bindings = [
            domain.ReleaseBinding(namespace="EX", release="2026-01-01"),
            domain.ReleaseBinding(namespace="EX", release="2027-01-01"),
            domain.ReleaseBinding(namespace="OTHER", release="2026-01-01"),
        ]
        assert len({v1.encode(binding.projection()) for binding in bindings}) == 3

    @pytest.mark.parametrize(
        ("binding", "match"),
        [
            ({"kind": "ontology", "namespace": "EX", "release": "1"}, "kind"),
            ({"namespace": "EX", "release": "1"}, "kind"),
            ({"kind": "release", "namespace": "EX", "release": "1", "dataset": "dataset:" + HEX["0"]}, "unknown field"),
            ({"kind": "dataset", "dataset": "dataset:" + HEX["0"], "release": "1"}, "unknown field"),
            ({"kind": "release", "namespace": "EX"}, "missing field"),
            ({"kind": "release", "namespace": "EX", "release": ""}, "empty string"),
            ({"kind": "release", "namespace": "cafe\u0301", "release": "1"}, "NFC"),
            ({"kind": "release", "namespace": "EX", "release": 2026}, "not a string"),
            ({"kind": "scheme", "scheme": "EX", "version": None}, "not a string"),
            ({"kind": "dataset", "dataset": HEX["0"]}, "dataset:"),
            ({"kind": "dataset", "dataset": "dataset:" + HEX["a"].upper()}, "dataset:"),
            ({"kind": "dataset", "dataset": "sha256:" + HEX["0"]}, "dataset:"),
            (
                {
                    "kind": "selection",
                    "dataset": "dataset:" + HEX["0"],
                    "rule": "procedure:" + HEX["0"],
                    "selected": "dataset:" + HEX["0"],
                    "annotator": "EX",
                },
                "classification-rule:",
            ),
            (
                {
                    "kind": "selection",
                    "dataset": "dataset:" + HEX["0"],
                    "rule": "classification-rule:" + HEX["0"],
                    "selected": "dataset:abc",
                    "annotator": "EX",
                },
                "dataset:",
            ),
            ({"kind": "run-output", "run": "dataset:" + HEX["0"], "dataset": "dataset:" + HEX["0"]}, "run:"),
            ({"kind": "run-output", "run": "run:" + HEX["0"], "dataset": "run:" + HEX["0"]}, "dataset:"),
            ({"kind": "world-kind", "world_kind": "nonexistent"}, "world kind"),
            ({"kind": "world-kind", "world_kind": "classification-ruled"}, "world kind"),
            ("dataset:" + HEX["0"], "mapping"),
        ],
    )
    def test_a_malformed_binding_is_refused(self, parse, testing_document, binding, match):
        testing_document["sorts"]["entity"]["binding"] = binding
        if isinstance(binding, dict) and binding.get("kind") == "world-kind":
            del testing_document["sorts"]["entity"]["identifier_class"]
        with pytest.raises(MalformedContract, match=match):
            parse(testing_document)

    def test_a_prose_kind_is_not_a_world_kind(self, base_contract, parse, testing_document):
        prose = sorted(name for name, kind in base_contract.kinds.items() if kind.role != "world")
        assert prose, "the base contract declares a non-world kind to test against"
        testing_document["sorts"]["procedure-spec"]["binding"]["world_kind"] = prose[0]
        with pytest.raises(MalformedContract, match="world kind"):
            parse(testing_document)

    def test_the_arms_check_their_fields_at_construction(self):
        # Callers construct bindings directly (`build_snapshot` keys), so the
        # grammar holds at construction too, not only at parse.
        with pytest.raises(MalformedContract):
            domain.DatasetBinding(dataset="dataset:")
        with pytest.raises(MalformedContract):
            domain.RunOutputBinding(run="run:" + HEX["0"], dataset="nothing")
        with pytest.raises(MalformedContract):
            domain.ReleaseBinding(namespace="EX", release="")

    def test_the_base_cannot_be_constructed(self):
        with pytest.raises(TypeError):
            domain.SortBinding()

    def test_no_seventh_arm_can_be_declared(self):
        with pytest.raises(SubclassRefused):

            class Forged(domain.SortBinding):  # type: ignore[misc]
                kind = "forged"

    @pytest.mark.parametrize(
        "arm",
        [
            domain.ReleaseBinding,
            domain.DatasetBinding,
            domain.SchemeBinding,
            domain.SelectionBinding,
            domain.RunOutputBinding,
            domain.WorldKindBinding,
        ],
    )
    def test_each_arm_is_sealed(self, arm):
        # A subclass overriding `projection` would reopen the collision with the
        # constructor check still in place.
        with pytest.raises(SubclassRefused):
            type("Forged", (arm,), {})


class TestSortDeclarations:
    def test_the_schema_projection(self, parse, testing_document):
        sorts = parse(testing_document).sorts
        assert sorts["entity"].schema_projection() == {
            "binding": {"kind": "release", "namespace": "EX", "release": "2026-01-01"},
            "identifier_class": {"prefix": "EX", "pattern": "EX:[a-z0-9\\-]+"},
            "categories": ["set"],
        }
        assert sorts["procedure-spec"].schema_projection() == {
            "binding": {"kind": "world-kind", "world_kind": "procedure"},
            "categories": [],
        }

    def test_categories_are_a_set(self, parse, testing_document):
        testing_document["sorts"]["outcome"]["categories"] = ["temporal", "class"]
        reordered = copy.deepcopy(testing_document)
        reordered["sorts"]["outcome"]["categories"] = ["class", "temporal"]
        assert (
            parse(testing_document).sorts["outcome"].schema_projection()
            == parse(reordered).sorts["outcome"].schema_projection()
        )

    def test_an_identifier_class_on_a_world_kind_sort_is_refused(self, parse, testing_document):
        testing_document["sorts"]["procedure-spec"]["identifier_class"] = {
            "prefix": "procedure",
            "pattern": "procedure:.+",
        }
        with pytest.raises(MalformedContract, match="identifier_class"):
            parse(testing_document)

    @pytest.mark.parametrize("sort", ["entity", "cohort", "method", "event", "product"])
    def test_an_identifier_class_is_required_on_every_other_arm(self, parse, testing_document, sort):
        del testing_document["sorts"][sort]["identifier_class"]
        with pytest.raises(MalformedContract, match="identifier_class"):
            parse(testing_document)

    @pytest.mark.parametrize(
        "identifier_class",
        [
            {"prefix": "EX", "pattern": "EX:cafe\u0301"},  # not NFC
            {"prefix": "EX", "pattern": "OTHER:[a-z]+"},  # does not begin with the prefix
            {"prefix": "EX", "pattern": "EX:\\d+"},  # outside the portable subset
            {"prefix": "EX", "pattern": 5},
            {"prefix": "EX"},
            {"prefix": "EX", "pattern": "EX:.+", "flags": "i"},
        ],
    )
    def test_a_malformed_identifier_class_is_refused(self, parse, testing_document, identifier_class):
        testing_document["sorts"]["entity"]["identifier_class"] = identifier_class
        with pytest.raises(MalformedContract):
            parse(testing_document)

    @pytest.mark.parametrize("categories", [["subset"], ["set", "set"], "set", [None]])
    def test_a_category_outside_the_base_set_is_refused(self, parse, testing_document, categories):
        testing_document["sorts"]["entity"]["categories"] = categories
        with pytest.raises(MalformedContract):
            parse(testing_document)

    def test_the_v1_vocabulary_field_is_refused(self, parse, testing_document):
        testing_document["sorts"]["entity"]["vocabulary"] = {"namespace": "EX", "release": "2026-01-01"}
        with pytest.raises(MalformedContract, match="unknown field"):
            parse(testing_document)


class TestTemplates:
    @pytest.mark.parametrize("role", ["within-model"])
    def test_a_reserved_role_name_is_refused(self, parse, testing_document, role):
        testing_document["templates"]["measured-by"]["roles"][role] = {"arity": "one"}
        with pytest.raises(MalformedContract, match="within-model"):
            parse(testing_document)

    def test_an_edge_without_the_causal_layer_is_refused(self, parse, testing_document):
        testing_document["templates"]["affects"]["layers"] = ["statistical"]
        with pytest.raises(MalformedContract, match="causal"):
            parse(testing_document)

    @pytest.mark.parametrize(
        "edge",
        [
            {"cause": "cause", "effect": "cause"},
            {"cause": "cause", "effect": "outcome"},
            {"cause": "agent", "effect": "effect"},
            {"cause": "cause"},
            {"cause": "cause", "effect": "effect", "sign": "+"},
            {"cause": 0, "effect": 1},
        ],
    )
    def test_a_malformed_edge_is_refused(self, parse, testing_document, edge):
        testing_document["templates"]["affects"]["edge"] = edge
        with pytest.raises(MalformedContract):
            parse(testing_document)

    @pytest.mark.parametrize("field", ["min", "max"])
    def test_min_or_max_on_a_one_role_is_refused(self, parse, testing_document, field):
        testing_document["templates"]["affects"]["roles"]["cause"][field] = 1
        with pytest.raises(MalformedContract, match=f"{field}.*`one`"):
            parse(testing_document)

    @pytest.mark.parametrize("value", [True, False])
    def test_coefficients_on_a_one_role_is_refused(self, parse, testing_document, value):
        # A coefficient has no meaning on a role holding one referent, so the
        # field never reaches a `one` role's schema projection, even as `false`.
        testing_document["templates"]["affects"]["roles"]["cause"]["coefficients"] = value
        with pytest.raises(MalformedContract, match="coefficients.*`one`"):
            parse(testing_document)

    @pytest.mark.parametrize(
        "role",
        [
            {"arity": "several"},
            {"arity": 2},
            {"arity": "many", "min": -1},
            {"arity": "many", "min": True},
            {"arity": "many", "min": 3, "max": 2},
            {"arity": "many", "max": 0},
            {"arity": "many", "coefficients": "yes"},
            {"arity": "many", "constraint": ["subset"]},
            {"arity": "many", "constraint": ["set", "set"]},
            {"arity": "many", "position": 0},
            {},
        ],
    )
    def test_a_malformed_role_is_refused(self, parse, testing_document, role):
        testing_document["templates"]["correlates-with"]["roles"]["parties"] = role
        with pytest.raises(MalformedContract):
            parse(testing_document)

    def test_a_role_constraint_names_base_categories(self, parse, testing_document):
        testing_document["templates"]["correlates-with"]["roles"]["parties"]["constraint"] = ["temporal", "set"]
        assert parse(testing_document).templates["correlates-with"].roles["parties"].constraint == ("temporal", "set")

    @pytest.mark.parametrize("forms", [["polar", "conditional"], [], ["polar", "polar"], ["polar", None], "polar"])
    def test_forms_outside_the_base_set_are_refused(self, parse, testing_document, forms):
        testing_document["templates"]["affects"]["forms"] = forms
        with pytest.raises(MalformedContract):
            parse(testing_document)

    def test_null_on_a_sign_inapt_template_is_refused(self, parse, testing_document):
        testing_document["templates"]["measured-by"]["forms"] = ["polar", "null"]
        with pytest.raises(MalformedContract, match="null"):
            parse(testing_document)

    @pytest.mark.parametrize("layers", [[], ["teleological"], ["causal", "causal"]])
    def test_layers_outside_the_base_set_are_refused(self, parse, testing_document, layers):
        testing_document["templates"]["measured-by"]["layers"] = layers
        with pytest.raises(MalformedContract):
            parse(testing_document)

    def test_sign_apt_must_be_a_boolean(self, parse, testing_document):
        testing_document["templates"]["affects"]["sign_apt"] = "yes"
        with pytest.raises(MalformedContract, match="true or false"):
            parse(testing_document)

    def test_an_unknown_template_field_is_refused(self, parse, testing_document):
        testing_document["templates"]["affects"]["arity"] = 2
        with pytest.raises(MalformedContract, match="unknown field"):
            parse(testing_document)

    def test_the_definition_is_outside_the_schema_projection(self, parse, testing_document):
        before = parse(testing_document)
        testing_document["templates"]["affects"]["definition"] = "Its cause changes its effect."
        after = parse(testing_document)
        assert after.templates["affects"].definition == "Its cause changes its effect."
        assert after.claim_vocabulary() == before.claim_vocabulary()
        assert after.content_identity != before.content_identity

    def test_an_external_reference_carries_a_base_mapping_type(self, parse, testing_document):
        testing_document["templates"]["affects"]["external"] = {"reference": "RO:0002410", "mapping": "contextual"}
        template = parse(testing_document).templates["affects"]
        assert template.external == domain.ExternalRef(reference="RO:0002410", mapping="contextual")
        assert template.schema_projection()["external"] == {"reference": "RO:0002410", "mapping": "contextual"}

    @pytest.mark.parametrize(
        "external",
        [
            {"reference": "RO:0002410", "mapping": "equivalent"},
            {"reference": "", "mapping": "exact"},
            {"reference": "RO:0002410"},
        ],
    )
    def test_a_malformed_external_reference_is_refused(self, parse, testing_document, external):
        testing_document["templates"]["affects"]["external"] = external
        with pytest.raises(MalformedContract):
            parse(testing_document)

    def test_the_schema_projection_holds_sets_as_sets(self, parse, testing_document):
        forward = parse(testing_document).templates["transforms"].schema_projection()
        testing_document["templates"]["transforms"]["layers"] = ["causal", "structural"]
        assert parse(testing_document).templates["transforms"].schema_projection() == forward
        assert forward == {
            "roles": {
                "inputs": {"arity": "many", "min": 1, "coefficients": True, "constraint": []},
                "outputs": {"arity": "many", "min": 1, "coefficients": True, "constraint": []},
                "facilitators": {"arity": "many", "min": 0, "coefficients": False, "constraint": []},
            },
            "sign_apt": False,
            "layers": ["causal", "structural"],
            "forms": ["polar"],
            "edge": {"cause": "inputs", "effect": "outputs"},
        }


class TestDimensions:
    @pytest.mark.parametrize("placement", ["estimand", None, 1])
    def test_a_placement_outside_the_base_set_is_refused(self, parse, testing_document, placement):
        testing_document["dimensions"]["setting"]["placement"] = placement
        with pytest.raises(MalformedContract, match="placement"):
            parse(testing_document)

    @pytest.mark.parametrize("field", ["placement", "applies_to", "restriction_sort"])
    def test_every_field_is_required(self, parse, testing_document, field):
        del testing_document["dimensions"]["setting"][field]
        with pytest.raises(MalformedContract, match="missing field"):
            parse(testing_document)

    def test_applies_to_is_a_set(self, parse, testing_document):
        testing_document["dimensions"]["population"]["applies_to"] = ["affects", "affects"]
        with pytest.raises(MalformedContract, match="twice"):
            parse(testing_document)

    def test_an_undeclared_restriction_sort_is_refused(self, parse, testing_document):
        testing_document["dimensions"]["population"]["restriction_sort"] = "nowhere"
        with pytest.raises(MalformedContract, match="not a sort"):
            parse(testing_document)

    def test_the_schema_projection(self, parse, testing_document):
        assert parse(testing_document).dimensions["population"].schema_projection() == {
            "restriction_sort": "cohort",
            "placement": "claim",
            "applies_to": ["affects", "correlates-with", "promotes"],
        }


class TestInstantiationsAndBridges:
    @pytest.mark.parametrize("mapping", ["exact", "broader"])
    def test_an_exact_or_broader_bridge_is_refused(self, parse, testing_document, mapping):
        testing_document["bridges"]["promotes"]["mapping"] = mapping
        with pytest.raises(MalformedContract, match=mapping):
            parse(testing_document)

    def test_a_mapping_outside_the_base_set_is_refused(self, parse, testing_document):
        testing_document["bridges"]["promotes"]["mapping"] = "equivalent"
        with pytest.raises(MalformedContract, match="mapping"):
            parse(testing_document)

    def test_a_bridge_may_omit_layers(self, parse, testing_document):
        del testing_document["bridges"]["promotes"]["layers"]
        bridge = parse(testing_document).bridges["promotes"]
        assert bridge.layers is None
        assert "layers" not in bridge.schema_projection()

    @pytest.mark.parametrize("layers", [[], ["teleological"]])
    def test_bridge_layers_outside_the_base_set_are_refused(self, parse, testing_document, layers):
        testing_document["bridges"]["promotes"]["layers"] = layers
        with pytest.raises(MalformedContract):
            parse(testing_document)

    def test_template_bridge_name_collision_refuses(self, parse, testing_document):
        # Templates and bridges are both operators, identified only as
        # `<namespace>/<name>` (P13).
        testing_document["bridges"]["affects"] = testing_document["bridges"].pop("promotes")
        testing_document["dimensions"]["population"]["applies_to"] = ["affects", "correlates-with"]
        del testing_document["estimands"]["bridge:promotes"]
        with pytest.raises(MalformedContract, match="operator"):
            parse(testing_document)

    @pytest.mark.parametrize("table", ["instantiations", "bridges"])
    @pytest.mark.parametrize("sorts", [[], ["entity", "entity"], "entity"])
    def test_a_role_lists_a_set_of_sorts(self, parse, testing_document, table, sorts):
        name = "promotes" if table == "bridges" else "affects-entity-outcome"
        testing_document[table][name]["roles"]["cause"] = sorts
        with pytest.raises(MalformedContract):
            parse(testing_document)

    def test_the_schema_projections(self, parse, testing_document):
        contract = parse(testing_document)
        assert contract.instantiations["affects-entity-entity"].schema_projection() == {
            "template": "affects",
            "roles": {"cause": ["entity"], "effect": ["entity", "outcome"]},
        }
        assert contract.bridges["promotes"].schema_projection() == {
            "template": "affects",
            "mapping": "narrower",
            "roles": {"cause": ["entity"], "effect": ["outcome"]},
            "layers": ["causal"],
        }


class TestEstimandKeys:
    def test_estimands_key_by_typed_target(self, parse, testing_document):
        contract = parse(testing_document)
        bridge = contract.estimands["bridge:promotes"]
        instantiation = contract.estimands["instantiation:promotes"]
        assert bridge.target == "bridge:promotes"
        assert instantiation.target == "instantiation:promotes"
        assert bridge.level_sorts == {"cause": "level"}
        assert instantiation.level_sorts == {"subject": "level"}
        assert bridge.schema_projection() != instantiation.schema_projection()

    @pytest.mark.parametrize(
        "key",
        [
            "promotes",
            "operator:promotes",
            "bridge:affects-entity-outcome",
            "instantiation:nowhere",
            "template:affects",
            "instantiation:testing/promotes",
            "instantiation:",
        ],
    )
    def test_a_key_naming_no_declaration_of_its_kind_refuses(self, parse, testing_document, key):
        testing_document["estimands"][key] = copy.deepcopy(testing_document["estimands"]["bridge:promotes"])
        with pytest.raises(MalformedContract):
            parse(testing_document)


class TestDurationConventions:
    def test_the_schema_projection_is_the_mapping(self, parse, testing_document):
        assert parse(testing_document).duration_conventions["day"].schema_projection() == {
            "unit": "hours",
            "length": 24,
        }

    @pytest.mark.parametrize("value", [True, 1.5, None, ["hours"], {"x": 1}])
    def test_a_field_is_a_string_or_an_integer(self, parse, testing_document, value):
        testing_document["duration_conventions"]["day"]["unit"] = value
        with pytest.raises(MalformedContract):
            parse(testing_document)


class TestSuccession:
    """The adopted succession rules, refused at contract load.

    Every case below goes through `parse_domain_contract`, not through
    `check_succession` directly. The check being *reachable* is not the property
    that matters; the property is that no contract reaches a caller without it.
    """

    @pytest.fixture()
    def genesis(self, parse, testing_document):
        return parse(testing_document)

    def test_genesis_is_compared_against_nothing(self, parse, testing_document):
        assert parse(testing_document, predecessor=None).predecessor is None

    def test_genesis_with_a_predecessor_supplied_is_refused(self, parse, testing_document, genesis):
        with pytest.raises(SuccessionViolation, match="declares genesis"):
            parse(testing_document, predecessor=genesis)

    def test_a_successor_with_no_predecessor_supplied_is_refused(self, parse, testing_document, genesis):
        document = successor_document(testing_document, genesis)
        with pytest.raises(SuccessionViolation, match="two-contract check"):
            parse(document, predecessor=None)

    def test_an_additive_successor_is_accepted(self, parse, testing_document, genesis):
        templates = copy.deepcopy(testing_document["templates"])
        templates["precedes"] = {
            "roles": {"earlier": {"arity": "one"}, "later": {"arity": "one"}},
            "sign_apt": False,
            "layers": ["structural"],
            "forms": ["polar"],
        }
        successor = parse(successor_document(testing_document, genesis, templates=templates), predecessor=genesis)
        assert "precedes" in successor.templates

    def test_an_editorial_change_is_accepted_and_moves_contract_identity(self, parse, testing_document, genesis):
        templates = copy.deepcopy(testing_document["templates"])
        templates["affects"]["description"] = "Reworded. Meaning-bearing fields untouched."
        templates["affects"]["definition"] = "Prose, outside the schema projection."
        successor = parse(successor_document(testing_document, genesis, templates=templates), predecessor=genesis)
        assert successor.content_identity != genesis.content_identity

    @pytest.mark.parametrize(
        ("section", "name", "field", "value", "tag"),
        [
            ("templates", "measured-by", "sign_apt", True, "template:measured-by"),
            ("templates", "affects", "layers", ["causal"], "template:affects"),
            ("templates", "affects", "forms", ["polar"], "template:affects"),
            ("templates", "affects", "edge", {"cause": "effect", "effect": "cause"}, "template:affects"),
            (
                "templates",
                "affects",
                "roles",
                {"cause": {"arity": "one"}, "effect": {"arity": "many"}},
                "template:affects",
            ),
            (
                "instantiations",
                "affects-entity-outcome",
                "roles",
                {"cause": ["entity"], "effect": ["entity"]},
                "instantiation:affects-entity-outcome",
            ),
            ("bridges", "promotes", "mapping", "contextual", "bridge:promotes"),
            ("dimensions", "population", "placement", "applicability", "dimension:population"),
            ("dimensions", "population", "applies_to", ["affects"], "dimension:population"),
            ("dimensions", "population", "restriction_sort", "entity", "dimension:population"),
            (
                "sorts",
                "entity",
                "binding",
                {"kind": "release", "namespace": "EX", "release": "2027-01-01"},
                "sort:entity",
            ),
            ("sorts", "entity", "identifier_class", {"prefix": "EX", "pattern": "EX:.+"}, "sort:entity"),
            ("sorts", "entity", "categories", [], "sort:entity"),
            ("estimands", "bridge:promotes", "measure_sort", "outcome", "estimand:bridge:promotes"),
            ("duration_conventions", "day", "length", 25, "duration-convention:day"),
        ],
    )
    def test_redefining_a_declared_schema_is_refused(
        self, parse, testing_document, genesis, section, name, field, value, tag
    ):
        document = successor_document(testing_document, genesis)
        document[section][name][field] = value
        with pytest.raises(SuccessionViolation, match=f"{tag} has a different canonical schema projection"):
            parse(document, predecessor=genesis)

    def test_a_successor_rewriting_a_namespaced_sort_is_refused(self, parse, testing_document, genesis):
        document = successor_document(testing_document, genesis)
        document["instantiations"]["affects-entity-outcome"]["roles"]["effect"] = ["other/outcome"]
        with pytest.raises(SuccessionViolation, match="different canonical schema projection"):
            parse(document, predecessor=genesis)

    @pytest.mark.parametrize(
        ("section", "name", "tag"),
        [
            ("templates", "measured-by", "template:measured-by"),
            ("instantiations", "transforms-entities", "instantiation:transforms-entities"),
            ("estimands", "instantiation:promotes", "estimand:instantiation:promotes"),
            ("duration_conventions", "day", "duration-convention:day"),
            ("dimensions", "follow-up", "dimension:follow-up"),
        ],
    )
    def test_dropping_a_declaration_is_refused(self, parse, testing_document, genesis, section, name, tag):
        document = successor_document(testing_document, genesis)
        del document[section][name]
        if section == "templates":
            # Its instantiations name it; drop them in step so the drop is what is refused.
            for inst in [n for n, body in document["instantiations"].items() if body["template"] == name]:
                del document["instantiations"][inst]
                document["estimands"].pop(f"instantiation:{inst}", None)
        with pytest.raises(SuccessionViolation, match=f"drops claim-vocabulary declaration.*{tag}"):
            parse(document, predecessor=genesis)

    def test_a_mismatched_predecessor_identity_is_refused(self, parse, testing_document, genesis):
        document = copy.deepcopy(testing_document)
        document["lineage"] = {"successor": "f" * 64}
        document["version"] = 2
        with pytest.raises(SuccessionViolation, match="content identity is"):
            parse(document, predecessor=genesis)

    def test_succession_keys_are_typed(self, genesis):
        tags = {key.split(":")[0] for key, _ in genesis._declarations()}
        assert tags == {
            "sort",
            "dimension",
            "template",
            "instantiation",
            "bridge",
            "estimand",
            "duration-convention",
            "quantity-kind",
            "unit",
            "constant",
            "conversion",
            "transformation",
        }
        keys = set(genesis.claim_vocabulary())
        # The same local name in two tables is two keys.
        assert {"sort:population", "dimension:population"} <= keys
        assert {"instantiation:promotes", "bridge:promotes"} <= keys
        assert {"estimand:instantiation:promotes", "estimand:bridge:promotes"} <= keys
        assert "duration-convention:day" in keys

    def test_un_retiring_an_instantiation_is_refused(self, parse, testing_document, genesis):
        retired = successor_document(testing_document, genesis)
        retired["instantiations"]["affects-entity-entity"]["retired"] = True
        tombstoned = parse(retired, predecessor=genesis)
        assert "instantiation:affects-entity-entity" in tombstoned.retired_identifiers()

        revived = successor_document(retired, tombstoned)
        revived["instantiations"]["affects-entity-entity"]["retired"] = False
        with pytest.raises(SuccessionViolation, match="un-retires instantiation:affects-entity-entity"):
            parse(revived, predecessor=tombstoned)


class TestRetirementIsOneWay:
    """`retired` sits outside the canonical schema projection, so the schema
    comparison cannot see it. That is correct — inside, retiring an identifier
    would itself read as a redefinition and be refused — but it means retirement
    needs a rule of its own beside the schema check, not instead of it.
    """

    @pytest.fixture()
    def genesis(self, parse, testing_document):
        return parse(testing_document)

    @pytest.fixture()
    def tombstoned(self, parse, testing_document, genesis):
        document = successor_document(testing_document, genesis)
        document["templates"]["affects"]["retired"] = True
        return document, parse(document, predecessor=genesis)

    def test_retiring_is_permitted(self, tombstoned):
        _, contract = tombstoned
        assert contract.templates["affects"].retired is True
        assert contract.retired_identifiers() == frozenset({"template:affects"})

    def test_un_retiring_is_refused(self, parse, tombstoned):
        document, contract = tombstoned
        revived = successor_document(document, contract)
        revived["templates"]["affects"]["retired"] = False
        with pytest.raises(SuccessionViolation, match="un-retires template:affects"):
            parse(revived, predecessor=contract)

    def test_dropping_the_retired_field_entirely_is_also_un_retiring(self, parse, tombstoned):
        # The default is `false`, so an omission is a resurrection written a
        # second way.
        document, contract = tombstoned
        revived = successor_document(document, contract)
        del revived["templates"]["affects"]["retired"]
        with pytest.raises(SuccessionViolation, match="un-retires template:affects"):
            parse(revived, predecessor=contract)

    @pytest.mark.parametrize(
        ("section", "name", "tag"),
        [
            ("dimensions", "setting", "dimension"),
            ("sorts", "outcome", "sort"),
            ("bridges", "promotes", "bridge"),
            ("instantiations", "promotes", "instantiation"),
        ],
    )
    def test_it_covers_every_retirable_table(self, parse, testing_document, genesis, section, name, tag):
        document = successor_document(testing_document, genesis)
        document[section][name]["retired"] = True
        contract = parse(document, predecessor=genesis)

        revived = successor_document(document, contract)
        revived[section][name]["retired"] = False
        with pytest.raises(SuccessionViolation, match=f"un-retires {tag}:{name}"):
            parse(revived, predecessor=contract)

    def test_dropping_a_tombstone_is_refused(self, parse, tombstoned):
        document, contract = tombstoned
        dropped = successor_document(document, contract)
        dropped["templates"].pop("affects")
        for inst in ["affects-entity-outcome", "affects-entity-entity"]:
            del dropped["instantiations"][inst]
            del dropped["estimands"][f"instantiation:{inst}"]
        del dropped["bridges"]["promotes"]
        del dropped["estimands"]["bridge:promotes"]
        for dimension in dropped["dimensions"].values():
            dimension["applies_to"] = [o for o in dimension["applies_to"] if o not in ("affects", "promotes")]
        with pytest.raises(SuccessionViolation, match="drops claim-vocabulary"):
            parse(dropped, predecessor=contract)

    def test_a_tombstone_may_not_be_redefined(self, parse, tombstoned):
        document, contract = tombstoned
        edited = successor_document(document, contract)
        edited["templates"]["affects"]["sign_apt"] = False
        edited["templates"]["affects"]["forms"] = ["polar"]
        with pytest.raises(SuccessionViolation, match="different canonical schema projection"):
            parse(edited, predecessor=contract)

    def test_estimands_and_duration_conventions_carry_no_retired(self, parse, testing_document):
        for section, name in (("estimands", "bridge:promotes"), ("duration_conventions", "day")):
            document = copy.deepcopy(testing_document)
            document[section][name]["retired"] = True
            with pytest.raises(MalformedContract):
                parse(document)


class TestDomainFacets:
    def test_the_testing_contract_declares_two_namespaced_facets(self, parse, testing_document):
        contract = parse(testing_document)
        assert set(contract.facets) == {"testing/axis", "testing/annotation"}
        assert contract.facets["testing/axis"].attaches_to == ("dataset",)
        assert contract.facets["testing/annotation"].attaches_to == ("dataset", "proposition")

    def test_a_domain_facet_requires_attaches_to_and_fields(self, parse, testing_document):
        doc = copy.deepcopy(testing_document)
        del doc["facets"]["axis"]["attaches_to"]
        with pytest.raises(MalformedContract, match="attaches_to"):
            parse(doc)

    def test_a_domain_facet_may_not_declare_a_shape(self, parse, testing_document):
        doc = copy.deepcopy(testing_document)
        doc["facets"]["axis"]["shape"] = "schema"
        with pytest.raises(MalformedContract, match="unknown key"):
            parse(doc)

    def test_facets_enter_the_content_identity(self, parse, testing_document):
        before = parse(testing_document).content_identity
        doc = copy.deepcopy(testing_document)
        doc["facets"]["axis"]["fields"]["axis"]["required"] = False
        assert parse(doc).content_identity != before

    def test_a_contract_without_facets_still_loads(self, parse, testing_document):
        doc = copy.deepcopy(testing_document)
        del doc["facets"]
        assert parse(doc).facets == {}


class TestTheLoadBoundary:
    def test_reading_a_file_runs_the_succession_check(self, tmp_path, base_contract, parse, testing_document):
        # The gap this closes: a loader that parsed without checking would let a
        # malformed successor through the boundary most callers actually use.
        genesis = parse(testing_document)
        document = successor_document(testing_document, genesis)
        document["templates"]["affects"]["sign_apt"] = False
        document["templates"]["affects"]["forms"] = ["polar"]

        path = tmp_path / "successor.yaml"
        path.write_text(json.dumps(document), encoding="utf-8")
        with pytest.raises(SuccessionViolation, match="different canonical schema projection"):
            domain.load_domain_contract(path, base=base_contract, predecessor=genesis)

    def test_the_fixture_file_loads(self, base_contract, testing_contract_path):
        contract = domain.load_domain_contract(testing_contract_path, base=base_contract, predecessor=None)
        assert contract.namespace == "testing"

    def test_the_predecessor_has_no_default(self, base_contract, testing_contract_path):
        # An omission must not be spellable: a default would make the check
        # skippable by saying nothing.
        with pytest.raises(TypeError):
            domain.load_domain_contract(testing_contract_path, base=base_contract)  # type: ignore[call-arg]
        with pytest.raises(TypeError):
            domain.parse_domain_contract({}, source="<test>", base=base_contract)  # type: ignore[call-arg]


class TestParallelGenesis:
    def test_a_second_genesis_in_one_namespace_is_not_prevented(self, parse, testing_document):
        # The succession rules treat this as an escape hatch and say so: the rules enforce
        # immutability *within a declared lineage*, not across a namespace.
        # Closing it needs governance, not typing, and it is left open. Asserted
        # here so the hole is visible in the suite rather than only in prose.
        first = parse(testing_document)
        forked = copy.deepcopy(testing_document)
        forked["templates"]["affects"]["sign_apt"] = False
        forked["templates"]["affects"]["forms"] = ["polar"]
        second = parse(forked)  # also genesis, same namespace, incompatible schema

        assert first.namespace == second.namespace
        assert first.claim_vocabulary() != second.claim_vocabulary()
