"""The formatting-equivalence comparator behind every `.py` freeze pin (doctrine §8)."""

from __future__ import annotations

import pin_equivalence

ORIGINAL = b'''"""A frozen declaration.

    Its docstring is indented the old way.
    """
from n2_arms import Arm
ARMS = (Arm(row='W1', asserts="x", before='    return None  # type: ignore[return-value]',
           after="pass"),)  # the arms

def f(a,b):
    # leading note
    return a+b
'''

# ORIGINAL as `ruff format` (0.16.1, line length 120) writes it.
FORMATTED = b'''"""A frozen declaration.

Its docstring is indented the old way.
"""

from n2_arms import Arm

ARMS = (Arm(row="W1", asserts="x", before="    return None  # type: ignore[return-value]", after="pass"),)  # the arms


def f(a, b):
    # leading note
    return a + b
'''


def same(original: bytes, current: bytes) -> bool:
    return pin_equivalence.equivalent(original, current, path="python/tests/n2_arms_cut99.py")


def test_identical_bytes_hold_for_any_target() -> None:
    assert pin_equivalence.equivalent(b"\xff not python", b"\xff not python", path="docs/x.md")


def test_a_formatting_only_change_holds() -> None:
    assert same(ORIGINAL, FORMATTED)


def test_line_endings_alone_hold() -> None:
    assert same(FORMATTED, FORMATTED.replace(b"\n", b"\r\n"))


def test_a_re_indented_trailing_block_comment_holds() -> None:
    assert same(b"if x:\n    y = 1\n    # done\nz = 2\n", b"if x:\n    y = 1\n# done\nz = 2\n")


def test_a_non_python_target_is_byte_exact() -> None:
    assert not pin_equivalence.equivalent(b"# Cut\n", b"# Cut \n", path="docs/designs/cut.md")


def test_a_changed_string_literal_breaks() -> None:
    assert not same(FORMATTED, FORMATTED.replace(b'asserts="x"', b'asserts="y"'))


def test_a_changed_statement_breaks() -> None:
    assert not same(FORMATTED, FORMATTED.replace(b"return a + b", b"return a - b"))


def test_a_changed_comment_breaks() -> None:
    assert not same(FORMATTED, FORMATTED.replace(b"# leading note", b"# leading notes"))


def test_a_changed_docstring_text_breaks_but_its_indentation_does_not() -> None:
    assert same(ORIGINAL, FORMATTED)
    assert not same(FORMATTED, FORMATTED.replace(b"the old way", b"the new way"))


def test_a_type_ignore_moved_to_another_statement_breaks() -> None:
    assert not same(
        b"x = f(1)  # type: ignore[arg-type]\ny = g(2)\n",
        b"x = f(1)\ny = g(2)  # type: ignore[arg-type]\n",
    )


def test_a_plain_comment_moved_across_a_statement_breaks() -> None:
    assert not same(b"x = 1\n# note\ny = 2\n", b"x = 1\ny = 2\n# note\n")


def test_a_directive_whose_line_was_reformatted_breaks() -> None:
    assert not same(
        b"def f(\n    a, b\n):  # type: ignore\n    pass\n",
        b"def f(a, b):  # type: ignore\n    pass\n",
    )


def test_a_coding_cookie_moved_below_line_two_breaks() -> None:
    """The review's reproduction: the moved cookie turns 'é' into 'Ã©' on execution."""
    literal = "é".encode("latin-1")
    original = b"# coding: latin-1\nx = '" + literal + b"'\n"
    moved = b"\n\n# coding: latin-1\nx = '" + literal + b"'\n"
    assert not same(original, moved)


def test_unparseable_input_breaks() -> None:
    assert not same(FORMATTED, FORMATTED + b"def (:\n")
    assert not same(b"x = 1\n", b"x = 1\0\n")
