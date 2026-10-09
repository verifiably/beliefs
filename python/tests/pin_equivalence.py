"""Whether two versions of a frozen Python file differ only by formatting.

A freeze pin names the bytes a cut audited. Formatting changes no meaning, so a pin on a
`.py` target holds when the file is byte-identical to the pinned original or equivalent
to it under the four rules `equivalent` applies (frozen guard doctrine §8). Every other
target stays byte-exact. Only the standard library is read, so a formatter upgrade
cannot change a verdict. The comparison fails closed: it can be stricter than
formatting needs, never looser than its rules.
"""

from __future__ import annotations

import ast
import inspect
import io
import re
import tokenize
from collections.abc import Iterator

# A comment a tool reads by physical line: the line's code must survive unchanged.
_DIRECTIVE = re.compile(r"#\s*(type:|noqa|pyright:|mypy:|pragma|fmt:|isort:|ruff:)", re.IGNORECASE)
# A shebang or a coding cookie only works on these lines, so a comment there keeps its line.
_HEADER_LINES = 2
_DOCSTRING_OWNERS = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
# A branch keyword with no node of its own, so which side of it a comment sits on is
# counted from the tokens.
_BRANCH_KEYWORDS = frozenset({"else", "finally"})

Anchor = tuple[int | None, int, int, int]
Comment = tuple[str, Anchor, int | None, str | None]


def equivalent(original: bytes, current: bytes, *, path: str) -> bool:
    """Whether `current` keeps every meaning `original` had.

    Both sides are read as Python reads source, from bytes, so a coding cookie decides
    their text. Beyond byte identity they must agree on four things: the detected
    encoding; the syntax tree, with each docstring compared after `inspect.cleandoc`;
    every comment's text and its anchor among the statements and nodes around it; and,
    for a directive comment, the code on its physical line.
    """
    if original == current:
        return True
    if not path.endswith(".py"):
        return False
    try:
        if _encoding(original) != _encoding(current):
            return False
        before, after = _tree(original), _tree(current)
        if ast.dump(before) != ast.dump(after):
            return False
        return _comments(original, before) == _comments(current, after)
    except (SyntaxError, ValueError, tokenize.TokenError):
        return False


def _encoding(source: bytes) -> str:
    return tokenize.detect_encoding(io.BytesIO(source).readline)[0]


def _tree(source: bytes) -> ast.Module:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not isinstance(node, _DOCSTRING_OWNERS) or not node.body:
            continue
        first = node.body[0]
        if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
            first.value.value = inspect.cleandoc(first.value.value)
    return tree


def _preorder(node: ast.AST) -> Iterator[ast.AST]:
    yield node
    for child in ast.iter_child_nodes(node):
        yield from _preorder(child)


def _comments(source: bytes, tree: ast.Module) -> list[Comment]:
    """Each comment as its text, its position anchor, its header line, its directive line."""
    statements = [node for node in _preorder(tree) if isinstance(node, ast.stmt)]
    starts = [line for node in _preorder(tree) if isinstance(line := getattr(node, "lineno", None), int)]
    comments: list[Comment] = []
    branches = 0
    for token in tokenize.tokenize(io.BytesIO(source).readline):
        if token.type == tokenize.NAME and token.string in _BRANCH_KEYWORDS:
            branches += 1
        if token.type != tokenize.COMMENT:
            continue
        line = token.start[0]
        comments.append(
            (
                token.string,
                _anchor(statements, starts, line, branches),
                line if line <= _HEADER_LINES else None,
                token.line[: token.start[1]].rstrip() if _DIRECTIVE.match(token.string) else None,
            )
        )
    return comments


def _anchor(statements: list[ast.stmt], starts: list[int], line: int, branches: int) -> Anchor:
    """Where a comment on `line` sits among the statements and nodes around it.

    The anchor is the innermost statement whose lines hold `line` (None when none does),
    the first statement that starts after `line`, the first positioned node of any kind
    that starts after it (`starts` holds each such node's first line), and the number of
    `else` and `finally` keywords before the comment (`branches`), which have no node to
    start after. A missing following statement or node is numbered past the end.
    Statements and nodes are numbered in pre-order, so a nested statement follows its
    parent and the last containing match is the innermost; equal trees number them
    alike. A comment moved to another statement, to another branch of one statement, or
    between the elements of one multi-line expression therefore changes its anchor.
    """
    containing = [
        index
        for index, statement in enumerate(statements)
        if statement.lineno <= line <= (statement.end_lineno or statement.lineno)
    ]
    following = next(
        (index for index, statement in enumerate(statements) if statement.lineno > line),
        len(statements),
    )
    next_node = next((index for index, start in enumerate(starts) if start > line), len(starts))
    return (containing[-1] if containing else None, following, next_node, branches)
