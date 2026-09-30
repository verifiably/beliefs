"""Keep scoped fixture consumers together without grouping unrelated tests."""

from types import SimpleNamespace
from typing import cast

import pytest
from conftest import pytest_collection_modifyitems


def test_grouping_uses_fixture_closure_and_closest_override():
    class Item:
        def __init__(self, nodeid, closure, definitions):
            self.nodeid = nodeid
            self._fixtureinfo = SimpleNamespace(
                names_closure=closure,
                name2fixturedefs={name: [SimpleNamespace(scope=scope) for scope in scopes] for name, scopes in definitions.items()},
            )
            self.groups = []

        def add_marker(self, marker):
            self.groups.append(marker.mark.args[0])

    items = [
        Item("tests/a.py::TestCases::test_indirect", ("indirect", "module_dep"), {"indirect": ("function",), "module_dep": ("module",)}),
        Item("tests/a.py::TestCases::test_both", ("module_dep", "class_dep"), {"module_dep": ("module",), "class_dep": ("class",)}),
        Item("tests/a.py::TestCases::test_class", ("class_dep",), {"class_dep": ("class",)}),
        Item("tests/a.py::TestCases::test_override", ("overridden",), {"overridden": ("module", "function")}),
        Item("tests/a.py::test_session", ("session_dep", "function_dep"), {"session_dep": ("session",), "function_dep": ("function",)}),
    ]
    pytest_collection_modifyitems(cast(list[pytest.Item], items))
    assert [item.groups for item in items] == [
        ["tests/a.py"],
        ["tests/a.py"],
        ["tests/a.py::TestCases"],
        [],
        [],
    ]
