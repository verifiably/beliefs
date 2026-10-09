"""The formatted twin of a sabotage: what `tools/retarget_formatted_arms.py` derives.

Every case runs the real pinned ruff, because the derivation's guarantee is about what ruff
does: the derived arm applied to the formatted source is exactly ruff's formatting of the
declared sabotage applied to the source before formatting.
"""

from __future__ import annotations

import pytest
from n2_arms import Sabotage
from retarget_formatted_arms import Retarget, RetargetRefused, derive_one, render, ruff_formatter

FORMAT = ruff_formatter("synthetic.py")


def _derive(original: str, before: str, after: str) -> tuple[str, str]:
    formatted = FORMAT(original)
    derived = derive_one(original, formatted, before, after, FORMAT)
    assert formatted.replace(*derived) == FORMAT(original.replace(before, after))
    return derived


def test_a_rewrapped_statement_carries_its_sabotage() -> None:
    original = "def f(a,b):\n    return a\n\nvalue = f(1,2)\n"

    assert _derive(original, "value = f(1,2)\n", "value = f(2,1)\n") == ("value = f(1, 2)\n", "value = f(2, 1)\n")


def test_an_after_that_rewraps_its_statement_is_taken_whole() -> None:
    original = "def f(*args):\n    return args\n\n\nvalue = f(1, 2)\n"
    long_call = "f(" + ", ".join(f"argument_number_{n}" for n in range(12)) + ")"

    before, after = _derive(original, "f(1, 2)", long_call)

    assert before == "value = f(1, 2)\n"
    assert after.count("\n") > 1


def test_a_sabotage_inside_one_line_becomes_that_whole_line() -> None:
    assert _derive("if x==1:\n    pass\n", "==1", "==2") == ("if x == 1:\n", "if x == 2:\n")


def test_a_region_that_is_not_unique_widens_until_it_is() -> None:
    original = "def a():\n    return None\n\n\ndef b():\n    return None\n"

    assert _derive(original, "def b():\n    return None", "def b():\n    return 1") == (
        "def b():\n    return None\n",
        "def b():\n    return 1\n",
    )


@pytest.mark.parametrize(
    ("original", "occurrences"),
    [("y = 2\n", 0), ("x = 1\nx = 1\n", 2)],
)
def test_an_arm_already_stale_before_formatting_is_refused(original: str, occurrences: int) -> None:
    with pytest.raises(RetargetRefused, match=f"occurs {occurrences} times"):
        derive_one(original, FORMAT(original), "x = 1\n", "x = 3\n", FORMAT)


def test_a_sabotage_formatting_erases_is_refused() -> None:
    original = "x = [1,2]\n"

    with pytest.raises(RetargetRefused, match="vanishes under formatting"):
        derive_one(original, FORMAT(original), "x = [1,2]\n", "x = [1, 2]\n", FORMAT)


def test_an_after_that_is_not_python_is_refused_with_ruffs_error() -> None:
    original = "x = 1\n"

    with pytest.raises(RetargetRefused, match="ruff cannot format"):
        derive_one(original, FORMAT(original), "x = 1\n", "def (\n", FORMAT)


def test_render_spells_entries_that_evaluate_back_to_themselves() -> None:
    entries = (
        Retarget("test_n2_cut99.py", 0, "Z1", "m.py", "a\n", "b\n", "    x = 1\n", "    x = 2\n"),
        Retarget("test_n2_cut99.py", 3, "Z2-a", "w/r.py", "c", "d", "if a:\n    b = '1'\n", 'if a:\n    b = "2"\n'),
    )

    table = eval("{" + render(entries) + "}", {"Sabotage": Sabotage})

    assert table == {
        "Z1": Sabotage(module="m.py", before="    x = 1\n", after="    x = 2\n"),
        "Z2-a": Sabotage(module="w/r.py", before="if a:\n    b = '1'\n", after='if a:\n    b = "2"\n'),
    }
