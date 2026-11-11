"""Estimand meaning comes from declarations and public traversal seams."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "src" / "beliefs"


def test_no_functional_name_branches():
    failures = []
    for path in ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.IfExp)):
                for comparison in (n for n in ast.walk(node.test) if isinstance(n, ast.Compare)):
                    operands = (comparison.left, *comparison.comparators)
                    if any(isinstance(o, ast.Constant) and isinstance(o.value, str) for o in operands) and any(
                        isinstance(o, ast.Attribute)
                        and o.attr == "functional"
                        or isinstance(o, ast.Name)
                        and o.id == "functional"
                        for o in operands
                    ):
                        failures.append((str(path.relative_to(ROOT)), node.lineno))
            if (
                isinstance(node, ast.Match)
                and (
                    isinstance(node.subject, ast.Attribute)
                    and node.subject.attr == "functional"
                    or isinstance(node.subject, ast.Name)
                    and node.subject.id == "functional"
                )
                and any(
                    isinstance(c.pattern, ast.MatchValue)
                    and isinstance(c.pattern.value, ast.Constant)
                    and isinstance(c.pattern.value.value, str)
                    for c in node.cases
                )
            ):
                failures.append((str(path.relative_to(ROOT)), node.lineno))
    assert not failures, failures


def test_no_private_estimand_or_applicability_traversal_imports():
    failures = [
        (str(path.relative_to(ROOT)), n.lineno, alias.name)
        for path in ROOT.rglob("*.py")
        for n in ast.walk(ast.parse(path.read_text()))
        if isinstance(n, ast.ImportFrom) and n.module in {"beliefs.estimand", "beliefs.applicability"}
        for alias in n.names
        if alias.name.startswith("_")
    ]
    assert not failures, failures
