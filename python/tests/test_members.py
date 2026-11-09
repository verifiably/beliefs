"""Members and the canonical NFC member key (R10)."""

import unicodedata

import pytest

from beliefs.claim import Member, Referent, canonical_members, member_key
from beliefs.errors import CoefficientRefused, DuplicateMember

COMPOSED = unicodedata.normalize("NFC", "é")
DECOMPOSED = unicodedata.normalize("NFD", "é")


def test_members_sort_by_nfc_key() -> None:
    assert COMPOSED != DECOMPOSED
    e1 = Member(Referent("x", COMPOSED))
    z = Member(Referent("x", "z"))
    ordered = canonical_members([e1, z], where="role")
    assert [m.referent.term for m in ordered] == ["z", COMPOSED]
    ordered = canonical_members([Member(Referent("x", DECOMPOSED)), z], where="role")
    assert [m.referent.term for m in ordered] == ["z", DECOMPOSED]
    assert member_key(Referent("x", COMPOSED)) == member_key(Referent("x", DECOMPOSED))


def test_duplicate_by_key_refuses() -> None:
    with pytest.raises(DuplicateMember):
        canonical_members([Member(Referent("x", COMPOSED)), Member(Referent("x", DECOMPOSED))], where="role")


def test_astral_sorts_by_code_point() -> None:
    bmp = "Ａ"
    astral = "\U0001f600"
    assert sorted([bmp, astral], key=lambda s: s.encode("utf-16-be")) == [astral, bmp]  # code-unit order differs
    ordered = canonical_members([Member(Referent("x", astral)), Member(Referent("x", bmp))], where="role")
    assert [m.referent.term for m in ordered] == [bmp, astral]


@pytest.mark.parametrize("bad", [True, 0, -1, 1.0, "1"])
def test_coefficient_refusals(bad: object) -> None:
    with pytest.raises(CoefficientRefused):
        Member(Referent("x", "a"), bad)  # type: ignore[arg-type]


def test_member_keeps_spelling() -> None:
    ordered = canonical_members([Member(Referent("x", DECOMPOSED))], where="role")
    assert ordered[0].referent.term == DECOMPOSED
    assert ordered[0].coefficient == 1
