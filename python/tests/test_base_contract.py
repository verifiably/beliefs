"""The `science` base contract.

The shipped document is loaded as itself rather than reconstructed in a fixture:
a test that builds its own copy of the contract asserts that the *test* is
well-formed, which is not the property anyone needs.
"""

import copy

import pytest
import yaml

from beliefs.contract import base
from beliefs.errors import MalformedContract, TagCollision

SOURCE = "<test>"


def parse(document: object) -> base.BaseContract:
    return base.parse_base_contract(document, source=SOURCE)


@pytest.fixture()
def document(base_contract_path) -> dict:
    return yaml.safe_load(base_contract_path.read_text(encoding="utf-8"))


class TestTheShippedContract:
    def test_it_loads(self, base_contract_path, request):
        assert request.node.get_closest_marker("xdist_group") is None
        contract = base.load_base_contract(base_contract_path)
        assert contract.name == "science"
        assert contract.version == 3

    def test_it_declares_the_closed_sets_7_1_names(self, base_contract_path):
        grammar = base.load_base_contract(base_contract_path).claim_grammar
        assert grammar.quantifiers == ("generic", "universal", "existential")
        assert grammar.polarities == ("positive", "negative", "unsigned")
        assert grammar.sign_inapt_tag == "inapt"
        assert grammar.layers == ("causal", "structural", "statistical", "methodological")

    def test_the_polarity_position_carries_four_inhabitants(self, base_contract_path):
        # Always emitted, with the inapt tag for the unit inhabitant.
        grammar = base.load_base_contract(base_contract_path).claim_grammar
        assert grammar.polarity_tags == ("positive", "negative", "unsigned", "inapt")

    def test_content_identity_is_derived_not_authored(self, base_contract_path, document):
        # The contract pairs *content-derived, moves on edit* with belief_input_digest.
        shipped = base.load_base_contract(base_contract_path)
        assert shipped.content_identity == parse(document).content_identity


class TestContentIdentity:
    def test_an_editorial_edit_moves_it(self, document):
        # Purely editorial changes move the contract identity — and so
        # belief_input_digest — while touching no declared schema.
        edited = copy.deepcopy(document)
        edited["version"] = document["version"] + 1
        assert parse(edited).content_identity != parse(document).content_identity

    def test_reformatting_does_not_move_it(self, base_contract_path):
        # The same rule, one level up: whitespace, key order and quoting style are
        # formatting, and an identity over raw bytes would make them significant.
        original = base_contract_path.read_text(encoding="utf-8")
        reformatted = yaml.safe_load(yaml.safe_dump(yaml.safe_load(original), default_flow_style=True, indent=7))
        assert parse(reformatted).content_identity == base.load_base_contract(base_contract_path).content_identity

    def test_a_comment_does_not_move_it(self, base_contract_path):
        # Recorded rather than hidden: the contract lists "a description, a comment, an
        # example" as editorial changes that move contract identity. A comment
        # does not survive parsing, so it moves nothing — and it should not,
        # under the reformatting rule above. The listing overstates by that one item.
        original = base_contract_path.read_text(encoding="utf-8")
        commented = "# an added comment\n" + original
        assert parse(yaml.safe_load(commented)).content_identity == parse(yaml.safe_load(original)).content_identity

    def test_it_is_domain_separated(self, document):
        from beliefs.identity import v1

        assert parse(document).content_identity == v1.digest("science.contract.v1", document)
        assert parse(document).content_identity != v1.digest("science.dataset.v1", document)


class TestTagsThatMustNotCollapse:
    def test_an_inapt_tag_that_is_also_a_polarity_is_refused(self, document):
        broken = copy.deepcopy(document)
        broken["claim_grammar"]["sign_inapt_tag"] = "unsigned"
        with pytest.raises(TagCollision):
            parse(broken)

    @pytest.mark.parametrize("closed_set", ["quantifiers", "polarities", "layers"])
    def test_a_duplicate_inside_a_closed_set_is_refused(self, document, closed_set):
        broken = copy.deepcopy(document)
        broken["claim_grammar"][closed_set] *= 2
        with pytest.raises(TagCollision):
            parse(broken)


class TestRefusals:
    def test_an_unknown_field_is_refused_never_ignored(self, document):
        broken = copy.deepcopy(document)
        broken["extra"] = 1
        with pytest.raises(MalformedContract, match="unknown field"):
            parse(broken)

    def test_an_unknown_grammar_field_is_refused(self, document):
        broken = copy.deepcopy(document)
        broken["claim_grammar"]["extra"] = 1
        with pytest.raises(MalformedContract, match="unknown field"):
            parse(broken)

    @pytest.mark.parametrize(
        "field", ["contract", "version", "claim_grammar", "measurement_grammar", "kinds", "relations", "facets"]
    )
    def test_a_missing_field_is_refused(self, document, field):
        broken = copy.deepcopy(document)
        del broken[field]
        with pytest.raises(MalformedContract, match="missing field"):
            parse(broken)

    @pytest.mark.parametrize(
        "field",
        [
            "version",
            "tag_encoding",
            "quantifiers",
            "polarities",
            "sign_inapt_tag",
            "forms",
            "layers",
            "role_categories",
            "binding_kinds",
            "mapping_types",
            "placements",
            "reserved_roles",
        ],
    )
    def test_a_missing_grammar_field_is_refused(self, document, field):
        broken = copy.deepcopy(document)
        del broken["claim_grammar"][field]
        with pytest.raises(MalformedContract, match="missing field"):
            parse(broken)

    def test_a_foreign_tag_encoding_is_refused(self, document):
        # The rule this enforces: an implementation must never
        # choose its own serialization for a tag.
        broken = copy.deepcopy(document)
        broken["claim_grammar"]["tag_encoding"] = "science.identity.v2"
        with pytest.raises(MalformedContract, match="tag_encoding"):
            parse(broken)

    @pytest.mark.parametrize("closed_set", ["quantifiers", "polarities", "layers"])
    def test_an_empty_closed_set_is_refused(self, document, closed_set):
        # An operator admitting no layer would make Claim uninhabited
        # there, and the same argument reaches every closed set.
        broken = copy.deepcopy(document)
        broken["claim_grammar"][closed_set] = []
        with pytest.raises(MalformedContract):
            parse(broken)

    @pytest.mark.parametrize("tag", ["Causal", "causal tag", "", "causal/sub", "1causal", None, 3])
    def test_a_malformed_tag_is_refused(self, document, tag):
        broken = copy.deepcopy(document)
        broken["claim_grammar"]["layers"] = [tag]
        with pytest.raises(MalformedContract):
            parse(broken)

    def test_a_contract_named_something_else_is_refused(self, document):
        broken = copy.deepcopy(document)
        broken["contract"] = "biology"
        with pytest.raises(MalformedContract, match="base contract"):
            parse(broken)

    @pytest.mark.parametrize("version", [0, -1, True, "1", 1.0])
    def test_a_non_positive_integer_version_is_refused(self, document, version):
        broken = copy.deepcopy(document)
        broken["version"] = version
        with pytest.raises(MalformedContract, match="positive integer"):
            parse(broken)

    def test_a_non_mapping_document_is_refused(self):
        with pytest.raises(MalformedContract, match="mapping"):
            parse([1, 2, 3])

    def test_malformed_yaml_never_escapes_as_a_parser_error(self, tmp_path):
        path = tmp_path / "CONTRACT.yaml"
        path.write_text("contract: science\n  version: [\n", encoding="utf-8")
        with pytest.raises(MalformedContract, match="not well-formed YAML"):
            base.load_base_contract(path)


@pytest.mark.parametrize("kind", ["dataset", "discussion"])
def test_explicit_null_kind_facets_are_not_an_empty_deferred_declaration(document, kind):
    document["kinds"][kind]["facets"] = None
    with pytest.raises(MalformedContract, match=rf"kinds.{kind}.facets: expected a mapping"):
        parse(document)


def test_genuinely_empty_deferred_declarations_remain_accepted(document):
    contract = parse(document)
    for kind in ("instrument-certification",):
        assert not contract.kinds[kind].facets


class TestClaimGrammarV2:
    """The six closed sets base v2 adds (design §8.1), each refused unless exactly the operated set."""

    def test_v2_closed_sets_parse(self, base_contract_path):
        grammar = base.load_base_contract(base_contract_path).claim_grammar
        assert grammar.version == 2
        assert grammar.forms == ("polar", "null")
        assert grammar.role_categories == ("set", "temporal", "class", "pattern")
        assert grammar.binding_kinds == ("release", "dataset", "scheme", "selection", "run-output", "world-kind")
        assert grammar.mapping_types == ("exact", "narrower", "broader", "contextual")
        assert grammar.placements == ("claim", "applicability")
        assert dict(grammar.reserved_roles) == {"within-model": base.ReservedRole(world_kind="procedure")}
        assert grammar.quantifiers == ("generic", "universal", "existential")
        assert grammar.layers == ("causal", "structural", "statistical", "methodological")

    def test_the_supported_sets_are_the_spec_values(self):
        assert base.SUPPORTED_FORMS == ("polar", "null")
        assert base.SUPPORTED_ROLE_CATEGORIES == ("set", "temporal", "class", "pattern")
        assert base.SUPPORTED_BINDING_KINDS == (
            "release",
            "dataset",
            "scheme",
            "selection",
            "run-output",
            "world-kind",
        )
        assert base.SUPPORTED_MAPPING_TYPES == ("exact", "narrower", "broader", "contextual")
        assert base.SUPPORTED_PLACEMENTS == ("claim", "applicability")

    def test_the_reserved_roles_are_read_only(self, base_contract):
        with pytest.raises(TypeError):
            base_contract.claim_grammar.reserved_roles["other"] = base.ReservedRole("procedure")  # type: ignore[index]

    def test_widened_form_set_refuses(self, document):
        document["claim_grammar"]["forms"] = ["polar", "null", "value"]
        with pytest.raises(MalformedContract, match="forms"):
            parse(document)

    def test_null_value_in_closed_set_refuses(self, document):
        # A bare YAML `null` is a null value, never the form tag `"null"`.
        loaded = yaml.safe_load("forms: [polar, null]")
        assert loaded["forms"] == ["polar", None]
        document["claim_grammar"]["forms"] = loaded["forms"]
        with pytest.raises(MalformedContract, match="forms"):
            parse(document)

    def test_narrowed_binding_kinds_refuses(self, document):
        document["claim_grammar"]["binding_kinds"] = ["release", "dataset", "scheme", "selection", "run-output"]
        with pytest.raises(MalformedContract, match="binding_kinds"):
            parse(document)

    @pytest.mark.parametrize(
        ("closed_set", "tags"),
        [
            ("role_categories", ["set", "temporal", "class"]),
            ("mapping_types", ["exact", "narrower", "broader", "contextual", "related"]),
            ("placements", ["claim"]),
        ],
    )
    def test_every_new_closed_set_must_be_exact(self, document, closed_set, tags):
        document["claim_grammar"][closed_set] = tags
        with pytest.raises(MalformedContract, match=closed_set):
            parse(document)

    @pytest.mark.parametrize("closed_set", ["forms", "role_categories", "binding_kinds", "mapping_types", "placements"])
    def test_a_duplicate_inside_a_new_closed_set_is_refused(self, document, closed_set):
        document["claim_grammar"][closed_set] *= 2
        with pytest.raises(TagCollision):
            parse(document)

    def test_reserved_role_names_a_world_kind(self, document):
        document["claim_grammar"]["reserved_roles"] = {"within-model": {"world_kind": "nowhere"}}
        with pytest.raises(MalformedContract, match="nowhere"):
            parse(document)

    def test_a_reserved_role_naming_a_prose_kind_refuses(self, document):
        document["claim_grammar"]["reserved_roles"] = {"within-model": {"world_kind": "discussion"}}
        with pytest.raises(MalformedContract, match="discussion"):
            parse(document)

    @pytest.mark.parametrize(
        "entry",
        [None, {}, {"world_kind": "procedure", "extra": 1}, {"world_kind": None}, {"world_kind": 3}],
    )
    def test_a_malformed_reserved_role_entry_refuses(self, document, entry):
        document["claim_grammar"]["reserved_roles"] = {"within-model": entry}
        with pytest.raises(MalformedContract):
            parse(document)

    @pytest.mark.parametrize(
        "roles",
        [
            None,
            [],
            {},
            {"Within Model": {"world_kind": "procedure"}},
            {"within-world": {"world_kind": "procedure"}},
            {"within-model": {"world_kind": "procedure"}, "within-world": {"world_kind": "procedure"}},
        ],
    )
    def test_a_malformed_reserved_roles_table_refuses(self, document, roles):
        document["claim_grammar"]["reserved_roles"] = roles
        with pytest.raises(MalformedContract):
            parse(document)

    @pytest.mark.parametrize("version", [1, 3])
    def test_a_claim_grammar_version_other_than_2_refuses(self, document, version):
        document["claim_grammar"]["version"] = version
        with pytest.raises(MalformedContract, match="version"):
            parse(document)

    def test_the_three_new_kinds(self, base_contract):
        register = base_contract.kinds["assumptions-register"]
        assert register.role == "world"
        assert register.domain == "science.assumptions-register.v2"
        assert dict(register.facets) == {"assumptions-register": base.FacetUse(required=True, covered=True)}
        facet = base_contract.facets["assumptions-register"]
        assert facet.shape == "reader"
        for name in ("procedure", "referent-mapping", "proxy-model", "classification-rule"):
            kind = base_contract.kinds[name]
            assert kind.role == "world"
            assert kind.domain == f"science.{name}.v1"
            assert dict(kind.facets) == {name: base.FacetUse(required=True, covered=True)}


class TestEstimandGrammar:
    def test_the_shipped_base_declares_the_three_closed_sets(self, base_contract):
        grammar = base_contract.estimand_grammar
        assert grammar.version == 2
        assert grammar.forms == base.SUPPORTED_ESTIMAND_FORMS
        assert grammar.uncertainty_kinds == ("interval", "standard-error", "covariance")

    def test_a_base_contract_lacking_the_grammar_is_refused(self, base_contract_path):
        import yaml

        from beliefs.contract.base import parse_base_contract
        from beliefs.errors import MalformedContract

        document = yaml.safe_load(base_contract_path.read_text(encoding="utf-8"))
        del document["estimand_grammar"]
        with pytest.raises(MalformedContract, match="estimand_grammar"):
            parse_base_contract(document, source="<no-grammar>")

    def test_another_tag_encoding_is_refused(self, base_contract_path):
        import yaml

        from beliefs.contract.base import parse_base_contract
        from beliefs.errors import MalformedContract

        document = yaml.safe_load(base_contract_path.read_text(encoding="utf-8"))
        document["estimand_grammar"]["tag_encoding"] = "science.identity.v2"
        with pytest.raises(MalformedContract, match="tag_encoding"):
            parse_base_contract(document, source="<encoding>")

    def test_a_duplicate_tag_in_a_closed_set_is_refused(self, base_contract_path):
        import yaml

        from beliefs.contract.base import parse_base_contract
        from beliefs.errors import TagCollision

        document = yaml.safe_load(base_contract_path.read_text(encoding="utf-8"))
        document["estimand_grammar"]["forms"] = ["contrast", "contrast"]
        with pytest.raises(TagCollision):
            parse_base_contract(document, source="<dup>")

    @pytest.mark.parametrize(
        ("closed_set", "tags", "unoperable"),
        [
            ("forms", [*base.SUPPORTED_ESTIMAND_FORMS, "rank-contrast"], "rank-contrast"),
            ("reference_kinds", ["value", "null", "unknown"], "unknown"),
            ("uncertainty_kinds", ["interval", "standard-error", "covariance", "credible"], "credible"),
            ("forms", ["contrast"], "quantity"),
        ],
    )
    def test_a_closed_set_must_exactly_match_the_tags_the_kernel_operates(self, document, closed_set, tags, unoperable):
        document["estimand_grammar"][closed_set] = tags
        with pytest.raises(MalformedContract, match=unoperable):
            parse(document)

    def test_old_field_set_and_version_are_refused(self, document):
        document["estimand_grammar"] = {
            "version": 1,
            "tag_encoding": "science.identity.v1",
            "contrast_kinds": ["levels", "continuous"],
            "scales": ["additive", "multiplicative"],
            "uncertainty_kinds": ["interval", "standard-error"],
        }
        with pytest.raises(MalformedContract):
            parse(document)

    def test_another_estimand_grammar_version_is_refused(self, document):
        document["estimand_grammar"]["version"] = 3
        with pytest.raises(MalformedContract):
            parse(document)


class TestMeasurementGrammar:
    def test_the_shipped_base_declares_the_nine_closed_sets(self, base_contract):
        grammar = base_contract.measurement_grammar
        assert grammar.version == 1
        assert grammar.value_types == ("level", "difference", "ratio")
        assert grammar.levels_of_measurement == ("nominal", "ordinal", "interval", "ratio")
        assert grammar.scale_orientations == ("higher-is-more", "higher-is-less")
        assert grammar.transformation_kinds == ("identity", "affine", "logarithm", "monotone")
        assert grammar.monotone_directions == ("increasing", "decreasing")
        assert grammar.transformation_domains == ("real", "nonnegative", "positive", "unit-interval")
        assert grammar.conversion_kinds == ("multiplicative", "affine")
        assert grammar.cardinalities == ("one-to-one", "many-to-one", "one-to-many", "many-to-many")
        assert grammar.evidence_modes == (
            "observation",
            "annotation",
            "simulation",
            "derivation",
            "literature-extraction",
        )

    def test_a_base_lacking_the_grammar_is_refused(self, document):
        del document["measurement_grammar"]
        with pytest.raises(MalformedContract, match="measurement_grammar"):
            parse(document)

    def test_another_tag_encoding_is_refused(self, document):
        document["measurement_grammar"]["tag_encoding"] = "science.identity.v2"
        with pytest.raises(MalformedContract, match="tag_encoding"):
            parse(document)

    def test_a_duplicate_tag_is_refused(self, document):
        document["measurement_grammar"]["value_types"] = ["level", "level"]
        with pytest.raises(TagCollision):
            parse(document)

    @pytest.mark.parametrize(
        ("closed_set", "tags", "difference"),
        [
            ("value_types", ["level", "difference", "ratio", "count"], "count"),
            ("levels_of_measurement", ["ordinal", "interval", "ratio"], "nominal"),
            ("conversion_kinds", ["multiplicative", "affine", "logarithmic"], "logarithmic"),
            (
                "evidence_modes",
                [
                    "observation",
                    "annotation",
                    "simulation",
                    "derivation",
                    "literature-extraction",
                    "simulation-calibrated",
                ],
                "simulation-calibrated",
            ),
        ],
    )
    def test_a_closed_set_must_exactly_match(self, document, closed_set, tags, difference):
        document["measurement_grammar"][closed_set] = tags
        with pytest.raises(MalformedContract, match=difference):
            parse(document)

    @pytest.mark.parametrize("version", [0, True, "1", 2])
    def test_an_unsupported_version_is_refused(self, document, version):
        document["measurement_grammar"]["version"] = version
        with pytest.raises(MalformedContract, match="version"):
            parse(document)

    def test_an_unknown_grammar_field_is_refused(self, document):
        document["measurement_grammar"]["extra"] = []
        with pytest.raises(MalformedContract, match="unknown field"):
            parse(document)

    def test_the_grammar_enters_the_compiled_identity(self, base_contract):
        from beliefs.identity import v1
        from beliefs.profile import PROFILE_DOMAIN, compile_profile

        compiled = compile_profile(base_contract, [])
        without_measurement = compiled.projection()
        assert v1.digest(PROFILE_DOMAIN, without_measurement) == compiled.compiled_identity
        without_measurement.pop("measurement_grammar", None)
        assert v1.digest(PROFILE_DOMAIN, without_measurement) != compiled.compiled_identity

    def test_closed_set_order_does_not_move_the_compiled_identity(self, document):
        from beliefs.profile import compile_profile

        before = compile_profile(parse(document), []).compiled_identity
        for tags in document["measurement_grammar"].values():
            if isinstance(tags, list):
                tags.reverse()
        after = compile_profile(parse(document), []).compiled_identity
        assert after == before


class TestCompositeGrammarAndKind:
    def test_the_shipped_base_declares_the_grammar_and_the_kind(self, base_contract):
        assert base_contract.composite_grammar.version == 1
        assert base_contract.composite_grammar.shapes == ("dag",)
        kind = base_contract.kinds["composite"]
        assert kind.role == "world" and kind.domain == "science.composite.v1"
        assert kind.facets["composite"].required and kind.facets["composite"].covered
        assert not kind.facets["display"].covered

    def test_the_two_relations(self, base_contract):
        composes = base_contract.relations["composes"]
        assert (composes.group, composes.sources, composes.targets) == ("world", ("composite",), ("proposition",))
        assert composes.same_kind is False
        supersedes = base_contract.relations["supersedes"]
        assert (
            set(supersedes.sources) == set(supersedes.targets) == {"proposition", "composite", "reservation-assignment"}
        )
        assert supersedes.same_kind is True
        assert base_contract.relations["assesses"].targets == ("proposition",)

    def test_a_base_contract_lacking_the_grammar_is_refused(self, document):
        del document["composite_grammar"]
        with pytest.raises(MalformedContract, match="composite_grammar"):
            parse(document)

    def test_an_unknown_grammar_field_is_refused(self, document):
        document["composite_grammar"]["directed"] = True
        with pytest.raises(MalformedContract, match="directed"):
            parse(document)

    def test_a_duplicate_shape_is_refused(self, document):
        document["composite_grammar"]["shapes"] = ["dag", "dag"]
        with pytest.raises(TagCollision):
            parse(document)

    def test_same_kind_on_unequal_endpoint_sets_is_refused(self, document):
        document["relations"]["composes"]["same_kind"] = True
        with pytest.raises(MalformedContract, match="same_kind"):
            parse(document)

    @pytest.mark.parametrize(
        ("sources", "targets"),
        [
            (["composite", "proposition"], ["proposition"]),  # a widened source
            (["composite"], ["proposition", "composite"]),  # a widened target
            (["proposition"], ["composite"]),  # the pair swapped
        ],
    )
    def test_a_composes_signature_outside_composite_to_proposition_is_refused(self, document, sources, targets):
        """`composes` has one signature and the kernel owns it. Both
        endpoints are named kinds, so kind-existence admits every row here —
        the refusal is the signature's own."""
        document["relations"]["composes"]["sources"] = sources
        document["relations"]["composes"]["targets"] = targets
        with pytest.raises(MalformedContract, match="one signature and no other"):
            parse(document)

    def test_same_kind_must_be_a_boolean(self, document):
        document["relations"]["supersedes"]["same_kind"] = "yes"
        with pytest.raises(MalformedContract, match="same_kind"):
            parse(document)

    def test_an_unsupported_shape_is_refused(self, document):
        document["composite_grammar"]["shapes"] = ["dag", "pag"]
        with pytest.raises(MalformedContract, match="pag"):
            parse(document)

    def test_the_grammar_and_the_rule_enter_the_identities(self, document):
        from beliefs.profile import compile_profile

        before = parse(copy.deepcopy(document))
        document["composite_grammar"]["version"] = 2
        after = parse(document)
        assert before.content_identity != after.content_identity
        assert compile_profile(before, []).compiled_identity != compile_profile(after, []).compiled_identity
        assert compile_profile(before, []).composite_grammar == before.composite_grammar
