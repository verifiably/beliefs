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

    @pytest.mark.parametrize("field", ["contract", "version", "claim_grammar"])
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
