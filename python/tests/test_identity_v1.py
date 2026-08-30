"""``science.identity.v1``.

The four collisions computation §4.3 records get named tests of their own. §4.3's
point is that *two of the four were introduced by the fixes for the other two*,
so a suite that tests only the first pair passes on an encoding that is still not
injective.

Every non-ASCII literal below is written as an escape. A composed and a
decomposed form are the same glyph on screen, so writing them as glyphs makes the
normalization tests depend on what survived the editor.
"""

from decimal import Decimal

import pytest

from beliefs.errors import (
    BinaryFloatRefused,
    KeyCollision,
    LoneSurrogate,
    MalformedDomain,
    NonFiniteDecimal,
    NonStringKey,
    NullRefused,
    UnsupportedValueType,
)
from beliefs.identity import v1

E_ACUTE = "é"  # é, one code point
E_COMBINING = "é"  # e + U+0301 COMBINING ACUTE ACCENT


def enc(value: object) -> str:
    return v1.encode(value).decode("utf-8")


class TestTheFourCollisions:
    """§4.3's table, one test per row."""

    def test_binary_float_bytes_are_platform_dependent(self):
        with pytest.raises(BinaryFloatRefused):
            v1.encode(0.1 + 0.2)

    def test_decimal_does_not_share_an_encoding_with_a_string(self):
        assert enc(Decimal("0.5")) != enc("0.5")

    def test_absent_member_differs_from_a_present_null(self):
        # `{"x": null}` must not encode as `{}`. It does not encode at all.
        with pytest.raises(NullRefused):
            v1.encode({"x": None})
        assert enc({}) == "{}"

    def test_integer_does_not_share_an_encoding_with_a_decimal(self):
        assert enc(1) == "1"
        assert enc(Decimal("1.0")) == "1.0"
        assert enc(1) != enc(Decimal("1.0"))


class TestDecimals:
    @pytest.mark.parametrize(
        ("literal", "expected"),
        [
            ("1.00", "1.0"),
            ("1.500", "1.5"),
            ("0.0", "0.0"),
            ("1", "1.0"),  # a decimal always retains a fractional part
            ("100", "100.0"),
            ("1E+2", "100.0"),  # never exponent notation
            ("1E-2", "0.01"),
            ("-1.20", "-1.2"),
            ("0.10", "0.1"),
        ],
    )
    def test_canonical_spellings(self, literal, expected):
        assert enc(Decimal(literal)) == expected

    def test_negative_zero_folds_into_the_one_spelling_of_zero(self):
        # Not a collision — one value, and two spellings of it would break
        # well-definedness rather than injectivity. Refused all the same.
        assert enc(Decimal("-0.0")) == "0.0" == enc(Decimal("0.0"))

    @pytest.mark.parametrize("literal", ["NaN", "sNaN", "Infinity", "-Infinity"])
    def test_non_finite_decimals_are_refused_outright(self, literal):
        with pytest.raises(NonFiniteDecimal):
            v1.encode(Decimal(literal))


class TestBooleansAndIntegers:
    def test_booleans_encode_as_themselves(self):
        assert enc(True) == "true"
        assert enc(False) == "false"

    def test_a_boolean_is_not_an_integer(self):
        # `bool` subclasses `int` in Python. An int check ordered first would
        # encode True as 1 and collapse two types into one encoding.
        assert enc(True) != enc(1)
        assert enc(False) != enc(0)

    def test_integers_are_unbounded_and_signed(self):
        assert enc(-7) == "-7"
        assert enc(2**70) == str(2**70)


class TestStrings:
    def test_strings_are_nfc_normalized(self):
        assert E_ACUTE != E_COMBINING
        assert enc(E_ACUTE) == enc(E_COMBINING) == '"é"'

    def test_quote_and_backslash_are_escaped(self):
        assert enc('a"b') == '"a\\"b"'
        assert enc("a\\b") == '"a\\\\b"'

    def test_control_characters_take_the_short_form_where_one_exists(self):
        assert enc("\n") == '"\\n"'
        assert enc("\t") == '"\\t"'
        assert enc("\r") == '"\\r"'
        assert enc("\b") == '"\\b"'
        assert enc("\f") == '"\\f"'

    def test_other_control_characters_take_lowercase_four_digit_hex(self):
        assert enc("\x00") == '"\\u0000"'
        assert enc("\x1f") == '"\\u001f"'

    def test_non_ascii_and_solidus_are_never_escaped(self):
        # Both escapes are optional in JSON, and an option is a place two
        # implementations can differ.
        assert enc("é") == '"é"'
        assert enc("日") == '"日"'
        assert enc("a/b") == '"a/b"'
        assert enc("\x7f") == '"\x7f"'  # DEL is not a C0 control

    def test_lone_surrogates_are_refused(self):
        with pytest.raises(LoneSurrogate):
            v1.encode("\ud800")


class TestObjects:
    def test_keys_sort_by_code_point(self):
        assert enc({"b": 1, "a": 2}) == '{"a":2,"b":1}'

    def test_key_order_is_inert(self):
        assert enc({"a": 1, "b": 2}) == enc({"b": 2, "a": 1})

    def test_astral_keys_sort_by_code_point_not_utf16_code_unit(self):
        # U+FF03 is a lone BMP code point; U+1F600 is astral and encodes in
        # UTF-16 as the surrogate pair D83D DE00. By code point U+FF03 < U+1F600;
        # by UTF-16 code unit D83D < FF03, so the two orders disagree.
        # JavaScript's default sort uses the wrong one, which is why this exists.
        assert enc({"\U0001f600": 1, "＃": 2}) == '{"＃":2,"\U0001f600":1}'

    def test_post_normalization_key_collisions_are_rejected(self):
        with pytest.raises(KeyCollision):
            v1.encode({E_COMBINING: 1, E_ACUTE: 2})

    def test_keys_are_normalized_before_they_are_sorted_and_emitted(self):
        assert enc({E_COMBINING: 1}) == enc({E_ACUTE: 1}) == '{"é":1}'

    def test_non_string_keys_are_refused(self):
        with pytest.raises(NonStringKey):
            v1.encode({1: "a"})

    def test_nesting_is_checked_at_every_depth(self):
        # §4.3: injectivity cannot come from a top-level discriminator, so a null
        # three levels down has to be caught on its own.
        with pytest.raises(NullRefused):
            v1.encode({"a": [{"b": None}]})


class TestUnsupported:
    @pytest.mark.parametrize("value", [(1, 2), {1, 2}, object(), b"bytes"])
    def test_unadmitted_types_are_refused(self, value):
        with pytest.raises(UnsupportedValueType):
            v1.encode(value)

    def test_a_tuple_is_not_an_array(self):
        # Admitting both would give an array two spellings in one language and
        # one in the other.
        with pytest.raises(UnsupportedValueType):
            v1.encode((1, 2))
        assert enc([1, 2]) == "[1,2]"


class TestDigest:
    def test_domain_separation_keeps_identical_payloads_apart(self):
        payload = {"x": 1}
        assert v1.digest("science.run.v1", payload) != v1.digest("science.dataset.v1", payload)

    def test_v2_is_disjoint_from_v1_by_construction(self):
        payload = {"x": 1}
        assert v1.digest("science.run.v1", payload) != v1.digest("science.run.v2", payload)

    @pytest.mark.parametrize(
        "domain",
        [
            "run.v1",  # not under `science`
            "science.v1",  # no kind segment
            "science.run",  # unversioned
            "science.run.v0",  # versions are positive
            "science.Run.v1",  # not lowercase
            "science.run.v1\nscience.dataset.v1",  # would forge the separator
            "",
        ],
    )
    def test_malformed_domains_are_refused(self, domain):
        with pytest.raises(MalformedDomain):
            v1.digest(domain, {"x": 1})

    def test_the_separator_cannot_be_forged_from_the_payload(self):
        # The newline separator is only safe because the domain grammar excludes
        # it; assert the property rather than trusting the grammar to stay put.
        assert v1.digest("science.run.v1", "x") != v1.digest("science.run.v1", "\nx")
