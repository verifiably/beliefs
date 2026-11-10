"""Comparability operates only on declared properties and exact coefficients."""

import ast
import re
from pathlib import Path


def test_no_declaration_identifier_or_decimal_literal_in_comparability():
    source = Path(__file__).resolve().parents[1] / "src/beliefs/comparability.py"
    tree = ast.parse(source.read_text())
    precision = {
        id(keyword.value)
        for statement in tree.body
        if isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Name)
        and statement.targets[0].id == "CONTEXT"
        and isinstance(statement.value, ast.Call)
        and isinstance(statement.value.func, ast.Attribute)
        and isinstance(statement.value.func.value, ast.Name)
        and statement.value.func.value.id == "decimal"
        and statement.value.func.attr == "Context"
        and not statement.value.args
        and len(statement.value.keywords) == 1
        for keyword in statement.value.keywords
        if keyword.arg == "prec" and isinstance(keyword.value, ast.Constant) and keyword.value.value == 34
    }
    assert len(precision) == 1
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            value = node.value
            if isinstance(value, str):
                assert re.fullmatch(r"[a-z][a-z0-9-]*/[a-z][a-z0-9-]*", value) is None
            elif isinstance(value, (int, float)) and not isinstance(value, bool):
                assert not isinstance(value, float)
                assert value in {0, 1, -1} or id(node) in precision
        if isinstance(node, ast.Name):
            assert node.id != "float"
