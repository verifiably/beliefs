"""D9: a practice carries procedure and no vocabulary (design §3.6)."""

import inspect

import pytest

from beliefs.contract.practice import Practice, parse_practice
from beliefs.errors import MalformedContract
from beliefs.profile import compile_profile

GOOD = {
    "practice": "causal-modeling",
    "version": 1,
    "description": "How we do it",
    "guidance": ["docs/practices/causal.md"],
}


def test_a_practice_parses_to_its_four_fields():
    assert parse_practice(GOOD, source="<t>") == Practice(
        "causal-modeling", 1, "How we do it", ("docs/practices/causal.md",)
    )


@pytest.mark.parametrize("section", ["vocabulary", "sorts", "dimensions", "operators", "facets", "kinds"])
def test_a_practice_declaring_vocabulary_or_schema_is_refused(section):
    with pytest.raises(MalformedContract, match=f"{section}.*practice"):
        parse_practice({**GOOD, section: {}}, source="<t>")


def test_unknown_keys_and_a_missing_field_are_refused():
    with pytest.raises(MalformedContract, match="unknown"):
        parse_practice({**GOOD, "skills": []}, source="<t>")
    with pytest.raises(MalformedContract, match="missing"):
        parse_practice({key: value for key, value in GOOD.items() if key != "guidance"}, source="<t>")


def test_a_non_string_key_is_refused_as_a_malformed_contract():
    with pytest.raises(MalformedContract, match="key.*not a string"):
        parse_practice({**GOOD, 1: "invalid"}, source="<t>")


def test_compile_profile_accepts_no_practice():
    assert "practice" not in inspect.signature(compile_profile).parameters
