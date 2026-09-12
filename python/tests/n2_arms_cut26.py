"""Cut 26 canonical declaration: D1 in full, two sabotages that land in a copy of `nodes`."""

from n2_arms import Arm, Sabotage

DECLARATION_UNITS = ("D1",)

NODES_SOURCE_COMMIT = "d8ecf664c85b7d17488de9f8884e5ba5b302c821"
"""The `nodes` commit the `before` blocks below were written against. Human-read: the
harness audits whatever `nodes` the interpreter resolves, and the cut's results record
what that was at the discharge."""

UNIT_CHECKS = {"D1": "test_domain_boundary.py::test_d1_installed_nodes_is_invariant_under_namespace_renaming"}

CO_CITED = ("acceptance/test_facet_acceptance.py::test_d1_installed_nodes_takes_no_domain_argument",)
"""Cut 20's inspection arm, re-cited unchanged; not an arm of this cut."""


def unit_of(row: str) -> str:
    """Rows are `<unit>` or `<unit>-<letter>`."""
    unit, hyphen, suffix = row.partition("-")
    if unit not in DECLARATION_UNITS or (hyphen and not (len(suffix) == 1 and suffix.islower())):
        raise ValueError(f"{row!r} is not a cut-26 row")
    return unit


CUT26_ARMS = (
    Arm(
        row="D1-a",
        asserts="the boundary parser keeps a namespaced facet whatever its namespace says",
        sabotage=Sabotage(
            package="nodes",
            module="core/frontmatter.py",
            before='    facets = fm["facets"] if "facets" in fm else {}  # absence defaults; null does not\n',
            after=(
                '    facets = fm["facets"] if "facets" in fm else {}  # absence defaults; null does not\n'
                '    facets = {k: v for k, v in facets.items() if not k.startswith("biology/")}\n'
            ),
        ),
        checks=(UNIT_CHECKS["D1"],),
    ),
    Arm(
        row="D1-b",
        asserts="registry validation counts a namespaced facet as present whatever its namespace says",
        sabotage=Sabotage(
            package="nodes",
            module="core/registry.py",
            before="        present = set(node.facets)\n        missing = required - present\n",
            after=(
                '        present = {name for name in node.facets if not name.startswith("biology/")}\n'
                "        missing = required - present\n"
            ),
        ),
        checks=(UNIT_CHECKS["D1"],),
    ),
)
