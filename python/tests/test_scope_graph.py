"""Declared scope graphs: validation, normalized comparison and selected context.

Scope containment design §§5–7.1; acceptance cases C1–C5, the graph parts of C7,
C9, C10 and C14. Checked reads of the selected context are test_scope_validity.py's.
"""

from __future__ import annotations

import itertools
from fractions import Fraction

import pytest
from scope_fixtures import (
    CASES,
    OWNERS,
    RULES,
    STAGE,
    VECTOR,
    endpoint_document,
    graph_profile,
    relation,
    relations_document,
    rule,
    term,
    union,
)

from beliefs.contract.domain import parse_domain_contract
from beliefs.errors import ProfileError
from beliefs.profile import compile_profile
from beliefs.restriction import (
    IntervalRestriction,
    ScopeComparison,
    co_scope,
    co_scope_by_dimension,
    compare_scopes,
    scope_contracts,
    scope_rule_ids,
)
from beliefs.scope_graph import compile_scope_graphs

INVERSE = {"equal": "equal", "narrower": "broader", "broader": "narrower", "unknown": "unknown"}


def on(value, dimension=STAGE):
    return {dimension: value}


def compare(profile, left, right, dimension=STAGE):
    return compare_scopes(on(left, dimension), on(right, dimension), profile)


def _members(value):
    return value.members if hasattr(value, "members") else (value,)


def _permutations(value):
    members = _members(value)
    return [union(*order) for order in itertools.permutations(members)] if len(members) > 1 else [value]


MATRIX = [
    # declared context, left, right, expected (design §6, C9/C10)
    ("none", {}, term("a"), union(term("a"), term("b")), "narrower"),
    ("disconnected", {"x-y": relation("x", "narrower", "y")}, term("a"), union(term("a"), term("b")), "narrower"),
    ("b-below-a", {"b-a": relation("b", "narrower", "a")}, term("a"), union(term("a"), term("b")), "equal"),
    ("a-equals-p", {"a-p": relation("a", "equal", "p")}, term("a"), term("p"), "equal"),
    ("redundant-member", {"a-p": relation("a", "narrower", "p")}, union(term("a"), term("p")), term("p"), "equal"),
    ("proper-in-union", {"a-p": relation("a", "narrower", "p")}, term("a"), union(term("p"), term("c")), "narrower"),
    (
        "siblings-may-cover",
        {"a-p": relation("a", "narrower", "p"), "b-p": relation("b", "narrower", "p")},
        union(term("a"), term("b")),
        term("p"),
        "unknown",
    ),
    (
        "cross-rule-equal-sets",
        {"ra-sx": relation(("R", "a"), "equal", ("S", "x")), "rb-sy": relation(("R", "b"), "equal", ("S", "y"))},
        rule("R", "a", "b"),
        rule("S", "x", "y"),
        "equal",
    ),
    (
        "equality-to-one-member",
        {"ra-sx": relation(("R", "a"), "equal", ("S", "x"))},
        rule("R", "a"),
        union(rule("S", "x"), rule("T", "z")),
        "unknown",
    ),
]


@pytest.mark.parametrize(("name", "table", "left", "right", "expected"), MATRIX, ids=[row[0] for row in MATRIX])
def test_declared_graph_comparison_matrix(base_contract, name, table, left, right, expected):
    profile = graph_profile(base_contract, table)
    dimension = CASES if name.startswith(("cross-rule", "equality-to")) else STAGE
    for left_order in _permutations(left):
        for right_order in _permutations(right):
            assert compare(profile, left_order, right_order, dimension).verdict == expected
            assert compare(profile, right_order, left_order, dimension).verdict == INVERSE[expected]
            assert co_scope(on(left_order, dimension), on(right_order, dimension), profile) == expected


def test_relation_free_and_declared_acceptance_cases(base_contract):
    bare = graph_profile(base_contract)
    # C1: without declarations distinct terms and rules stay unknown; same-rule arithmetic is unchanged.
    assert compare(bare, term("special"), term("general")).verdict == "unknown"
    assert compare(bare, rule("R", "a"), rule("S", "a"), CASES).verdict == "unknown"
    assert compare(bare, rule("R", "a"), rule("R", "a", "b"), CASES).verdict == "narrower"
    assert compare(bare, rule("R", "a", "b"), rule("R", "b", "c"), CASES).verdict == "unknown"

    # C2: a declared strict relation is directional and dimension-specific.
    document = endpoint_document()
    document["dimensions"]["stage-two"] = dict(document["dimensions"]["stage"])
    declared = graph_profile(
        base_contract, {"special-general": relation("special", "narrower", "general")}, endpoint_doc=document
    )
    assert compare(declared, term("special"), term("general")).verdict == "narrower"
    assert compare(declared, term("general"), term("special")).verdict == "broader"
    assert compare(declared, term("special"), term("general"), "testing/stage-two").verdict == "unknown"

    # C3: declared equality holds in both orders; the terms stay distinct values.
    equal = graph_profile(base_contract, {"a-b": relation("a", "equal", "b")})
    assert compare(equal, term("a"), term("b")).verdict == compare(equal, term("b"), term("a")).verdict == "equal"
    assert term("a") != term("b")

    # C4: strict closure, equality then strictness, and unknown siblings.
    chain = graph_profile(base_contract, {"a-b": relation("a", "narrower", "b"), "b-c": relation("b", "narrower", "c")})
    assert compare(chain, term("a"), term("c")).verdict == "narrower"
    mixed = graph_profile(base_contract, {"a-b": relation("a", "equal", "b"), "b-c": relation("b", "narrower", "c")})
    assert compare(mixed, term("a"), term("c")).verdict == "narrower"
    siblings = graph_profile(
        base_contract, {"a-p": relation("a", "narrower", "p"), "b-p": relation("b", "narrower", "p")}
    )
    assert compare(siblings, term("a"), term("b")).verdict == "unknown"

    # Numeric comparison is untouched and selects nothing.
    def hours(high):
        return {"testing/follow-up": IntervalRestriction("testing/hour", Fraction(0), Fraction(high), True, False)}

    numeric = compare_scopes(hours(2), hours(4), chain)
    assert numeric.verdict == "narrower" and numeric.relations == ()
    folded = compare_scopes({STAGE: term("a")}, {}, chain)
    assert folded.verdict == "narrower" and folded.relations == ()


def test_operand_component_context(base_contract):
    chain = {"a-b": relation("a", "narrower", "b"), "b-c": relation("b", "narrower", "c")}
    profile = graph_profile(
        base_contract, chain, {"x-y": relation("x", "narrower", "y")}, {"q-z": relation("q", "narrower", "z")}
    )
    owner, second, third = (f"{namespace}/" for namespace in OWNERS)

    # The whole operand component, including an intermediary, never only a winning path.
    result = compare(profile, term("a"), term("c"))
    assert result.verdict == "narrower"
    assert result.relations == (f"{owner}a-b", f"{owner}b-c")
    assert result.by_dimension == {STAGE: "narrower"}

    # Unknown across two components keeps both; a third component is absent.
    across = compare(profile, term("a"), term("x"))
    assert across.verdict == "unknown"
    assert across.relations == tuple(sorted((f"{owner}a-b", f"{owner}b-c", f"{second}x-y")))
    assert f"{third}q-z" not in across.relations
    assert scope_contracts(across, profile) == {"scope-relations", "scope-relations-b", "testing"}

    # Atoms outside the graph contribute nothing; relation-free paths select nothing.
    assert compare(profile, term("m"), term("n")).relations == ()
    assert compare(profile, rule("R", "a"), rule("R", "a", "b"), CASES).relations == ()
    assert scope_contracts(compare(profile, term("m"), term("n")), profile) == frozenset()

    # Rule roots include the intermediate rule of a selected component.
    rules = graph_profile(
        base_contract,
        {"ra-sx": relation(("R", "a"), "narrower", ("S", "x")), "sx-tz": relation(("S", "x"), "narrower", ("T", "z"))},
    )
    nested = compare(rules, rule("R", "a"), rule("T", "z"), CASES)
    assert nested.verdict == "narrower"
    assert scope_rule_ids(nested, rules) == tuple(sorted(RULES.values()))
    assert scope_contracts(nested, rules) == {"scope-relations", "testing"}

    # Duplicate consistent facts keep both owners in provenance.
    duplicate = graph_profile(
        base_contract, {"a-b": relation("a", "narrower", "b")}, {"a-within-b": relation("a", "narrower", "b")}
    )
    both = compare(duplicate, term("a"), term("b"))
    assert both.relations == tuple(sorted((f"{owner}a-b", f"{second}a-within-b")))
    assert scope_contracts(both, duplicate) == {"scope-relations", "scope-relations-b", "testing"}

    # C10: a disconnected activation changes no verdict, context or owner set.
    for candidate in (
        graph_profile(base_contract),
        graph_profile(base_contract, {"x-y": relation("x", "narrower", "y")}),
    ):
        plain = compare(candidate, term("a"), union(term("a"), term("b")))
        assert (plain.verdict, plain.relations, scope_contracts(plain, candidate)) == ("narrower", (), frozenset())

    # A comparison is computed, never supplied.
    with pytest.raises(TypeError):
        ScopeComparison({}, {}, {}, "equal", ())  # type: ignore[call-arg]
    with pytest.raises((AttributeError, TypeError)):
        result.verdict = "equal"  # type: ignore[misc]
    with pytest.raises(TypeError):
        result.by_dimension[STAGE] = "equal"  # type: ignore[index]
    assert co_scope_by_dimension(on(term("a")), on(term("c")), profile) == {STAGE: "narrower"}
    assert scope_contracts(result, graph_profile(base_contract, chain)) == {"scope-relations", "testing"}
    with pytest.raises(ProfileError):
        scope_contracts(result, graph_profile(base_contract))


def test_retired_relations_and_exact_pins(base_contract):
    owner = f"{OWNERS[0]}/"
    live = graph_profile(
        base_contract, {"a-b": relation("a", "narrower", "b"), "x-y": relation("x", "narrower", "y", retired=True)}
    )
    assert compare(live, term("a"), term("b")).verdict == "narrower"
    assert compare(live, term("a"), term("b")).relations == (f"{owner}a-b",)
    assert compare(live, term("x"), term("y")).verdict == "unknown"
    assert compare(live, term("x"), term("y")).relations == ()
    duplicate = graph_profile(
        base_contract, {"a-b": relation("a", "narrower", "b"), "a-b-old": relation("a", "narrower", "b", retired=True)}
    )
    assert compare(duplicate, term("a"), term("b")).relations == (f"{owner}a-b",)

    # The original exact pin keeps its proof; its successor withdraws it explicitly.
    genesis_doc = relations_document({"a-b": relation("a", "narrower", "b")})
    genesis = parse_domain_contract(genesis_doc, source="genesis", base=base_contract, predecessor=None)
    successor_doc = relations_document({"a-b": relation("a", "narrower", "b", retired=True)})
    successor_doc.update(version=2, lineage={"successor": genesis.content_identity})
    successor = parse_domain_contract(successor_doc, source="successor", base=base_contract, predecessor=genesis)
    endpoints = parse_domain_contract(endpoint_document(), source="testing", base=base_contract, predecessor=None)
    original = compile_profile(base_contract, [endpoints, genesis])
    withdrawn = compile_profile(base_contract, [endpoints, successor])
    assert compare(original, term("a"), term("b")).verdict == "narrower"
    assert compare(withdrawn, term("a"), term("b")).verdict == "unknown"
    assert original.compiled_identity != withdrawn.compiled_identity
    assert "scope_graphs" not in original.projection()


def _graph_contracts(base_contract, case):
    return [
        parse_domain_contract(
            relations_document(table, namespace=owner), source=owner, base=base_contract, predecessor=None
        )
        for owner, table in zip(OWNERS, case["contracts"], strict=False)
    ]


@pytest.mark.parametrize("case", VECTOR["graph_refusals"], ids=lambda case: case["name"])
def test_graph_conflicts_refuse(base_contract, case):
    contracts = _graph_contracts(base_contract, case)
    endpoints = parse_domain_contract(endpoint_document(), source="testing", base=base_contract, predecessor=None)
    with pytest.raises(ProfileError):
        compile_profile(base_contract, [endpoints, *contracts])


@pytest.mark.parametrize("case", VECTOR["graph_accepts"], ids=lambda case: case["name"])
def test_consistent_graphs_compile(base_contract, case):
    contracts = _graph_contracts(base_contract, case)
    endpoints = parse_domain_contract(endpoint_document(), source="testing", base=base_contract, predecessor=None)
    profile = compile_profile(base_contract, [endpoints, *contracts])
    live = [relation for relation in profile.scope_relations.values() if not relation.declaration.retired]
    assert compile_scope_graphs(profile.scope_relations.values()).keys() == {r.declaration.dimension for r in live}


def test_graph_order_and_representative_invariance(base_contract):
    table = {
        "z-eq-m": relation("z", "equal", "m"),
        "m-eq-b": relation("m", "equal", "b"),
        "b-p": relation("b", "narrower", "p"),
        "q-p": relation("q", "narrower", "p"),
    }
    reference = graph_profile(base_contract, table)
    cases = [
        (term("z"), term("p")),
        (union(term("m"), term("p")), term("p")),
        (union(term("b"), term("q")), term("p")),
        (term("z"), union(term("p"), term("c"))),
        (union(term("z"), term("b")), term("m")),
    ]
    expected = [(compare(reference, a, b).verdict, compare(reference, a, b).relations) for a, b in cases]
    assert [verdict for verdict, _ in expected] == ["narrower", "equal", "unknown", "narrower", "equal"]
    for order in itertools.permutations(table):
        shuffled = graph_profile(base_contract, {name: table[name] for name in order})
        assert [(compare(shuffled, a, b).verdict, compare(shuffled, a, b).relations) for a, b in cases] == expected
    # Splitting the same facts across owners in either activation order selects them all.
    first, rest = dict(list(table.items())[:2]), dict(list(table.items())[2:])
    split = graph_profile(base_contract, first, rest)
    swapped = graph_profile(base_contract, rest, first)
    for a, b in cases:
        assert compare(split, a, b).verdict == compare(swapped, a, b).verdict == compare(reference, a, b).verdict
        assert len(compare(split, a, b).relations) == len(compare(reference, a, b).relations)
