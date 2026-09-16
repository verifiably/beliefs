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
    def test_it_loads(self, base_contract_path):
        contract = base.load_base_contract(base_contract_path)
        assert contract.name == "science"
        assert contract.version == 1

    def test_it_declares_the_closed_sets_7_1_names(self, base_contract_path):
        grammar = base.load_base_contract(base_contract_path).claim_grammar
        assert grammar.quantifiers == ("generic", "universal", "existential")
        assert grammar.polarities == ("positive", "negative", "unsigned")
        assert grammar.sign_inapt_tag == "inapt"
        assert grammar.layers == ("causal", "structural", "statistical", "methodological")

    def test_the_polarity_position_carries_four_inhabitants(self, base_contract_path):
        # §7.5: always emitted, with the inapt tag for the unit inhabitant.
        grammar = base.load_base_contract(base_contract_path).claim_grammar
        assert grammar.polarity_tags == ("positive", "negative", "unsigned", "inapt")

    def test_content_identity_is_derived_not_authored(self, base_contract_path, document):
        # §7.3 pairs *content-derived, moves on edit* with belief_input_digest.
        shipped = base.load_base_contract(base_contract_path)
        assert shipped.content_identity == parse(document).content_identity


class TestContentIdentity:
    def test_an_editorial_edit_moves_it(self, document):
        # §7.3: purely editorial changes move the contract identity — and so
        # belief_input_digest — while touching no declared schema.
        edited = copy.deepcopy(document)
        edited["claim_grammar"]["version"] = 2
        assert parse(edited).content_identity != parse(document).content_identity

    def test_reformatting_does_not_move_it(self, base_contract_path):
        # D5's rule, one level up: whitespace, key order and quoting style are
        # formatting, and an identity over raw bytes would make them significant.
        original = base_contract_path.read_text(encoding="utf-8")
        reformatted = yaml.safe_load(yaml.safe_dump(yaml.safe_load(original), default_flow_style=True, indent=7))
        assert parse(reformatted).content_identity == base.load_base_contract(base_contract_path).content_identity

    def test_a_comment_does_not_move_it(self, base_contract_path):
        # Recorded rather than hidden: §7.3 lists "a description, a comment, an
        # example" as editorial changes that move contract identity. A comment
        # does not survive parsing, so it moves nothing — and it should not,
        # under the reformatting rule above. §7.3 overstates by that one item.
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

    @pytest.mark.parametrize("field", ["contract", "version", "claim_grammar", "kinds", "relations", "facets"])
    def test_a_missing_field_is_refused(self, document, field):
        broken = copy.deepcopy(document)
        del broken[field]
        with pytest.raises(MalformedContract, match="missing field"):
            parse(broken)

    @pytest.mark.parametrize(
        "field", ["version", "tag_encoding", "quantifiers", "polarities", "sign_inapt_tag", "layers"]
    )
    def test_a_missing_grammar_field_is_refused(self, document, field):
        broken = copy.deepcopy(document)
        del broken["claim_grammar"][field]
        with pytest.raises(MalformedContract, match="missing field"):
            parse(broken)

    def test_a_foreign_tag_encoding_is_refused(self, document):
        # The rule this enforces is §7.4 row 5's: an implementation must never
        # choose its own serialization for a tag.
        broken = copy.deepcopy(document)
        broken["claim_grammar"]["tag_encoding"] = "science.identity.v2"
        with pytest.raises(MalformedContract, match="tag_encoding"):
            parse(broken)

    @pytest.mark.parametrize("closed_set", ["quantifiers", "polarities", "layers"])
    def test_an_empty_closed_set_is_refused(self, document, closed_set):
        # §6.2: an operator admitting no layer would make Claim uninhabited
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


class TestEstimandGrammar:
    def test_the_shipped_base_declares_the_three_closed_sets(self, base_contract):
        grammar = base_contract.estimand_grammar
        assert grammar.version == 1
        assert grammar.contrast_kinds == ("levels", "continuous")
        assert grammar.scales == ("additive", "multiplicative")
        assert grammar.uncertainty_kinds == ("interval", "standard-error")

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
        document["estimand_grammar"]["scales"] = ["additive", "additive"]
        with pytest.raises(TagCollision):
            parse_base_contract(document, source="<dup>")

    def test_the_grammar_enters_the_compiled_identity(self, base_contract_path):
        import yaml

        from beliefs.contract.base import parse_base_contract
        from beliefs.profile import compile_profile

        document = yaml.safe_load(base_contract_path.read_text(encoding="utf-8"))
        before = compile_profile(parse_base_contract(document, source="<a>"), []).compiled_identity
        document["estimand_grammar"]["scales"] = ["additive", "multiplicative", "ordinal"]
        after = compile_profile(parse_base_contract(document, source="<b>"), []).compiled_identity
        assert before != after


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
        assert set(supersedes.sources) == set(supersedes.targets) == {"proposition", "composite"}
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
