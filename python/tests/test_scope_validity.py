"""Checked scope context at authoring and freezing; current-profile validity.

Scope containment design §§7.2–7.3; acceptance cases C6, C7 (held boundary),
C11–C14 at authoring. Snapshot capture and replay are test_scope_evaluation.py's.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from fixtures_cut3 import TESTING_CLAIM, UNCONSULTED, spec_draft, spec_rules
from nodes.core.node import Node
from scope_fixtures import CASES, endpoint_document, relation, relations_document
from test_dependencies import Records

from beliefs import errors
from beliefs.applicability import ScopedRestriction, build_applicability
from beliefs.assumptions import AssumptionInstance
from beliefs.classification_rule import ClassificationRule
from beliefs.contract.domain import parse_domain_contract
from beliefs.dependencies import dependency_closure
from beliefs.estimand import Control, MeasuredBinding, OutputSpec, RoleTermLevels, ValueReference, build_estimand
from beliefs.measurement import Measure, Observable
from beliefs.procedure import Procedure
from beliefs.profile import compile_profile, shipped_base_contract
from beliefs.restriction import RuleRestriction
from beliefs.scope_checks import author_scope_reader
from beliefs.spec import freeze
from beliefs.target import target_projection
from beliefs.target_validity import target_scope_requirements

BASE = shipped_base_contract()
OBSERVABLE = Observable("testing/abundance", "testing/entity")


def _rule(definition: str, classes: str = "testing/level") -> ClassificationRule:
    return ClassificationRule(classes, (OBSERVABLE,), definition, None, None, None)


def _procedure(name: str, validated_in) -> Procedure:
    return Procedure(
        kind="testing/assay" if validated_in is not None else "testing/estimator",
        name=name,
        definition="Fixture procedure.",
        yields=(OBSERVABLE,) if validated_in is not None else (),
        scale=None,
        validated_in=validated_in if validated_in is not None else {},
        compatible_with=(),
        evidence=(),
        implementation=None,
        inputs=None,
        parameters={},
        external=None,
    )


class World:
    """Held rules R (target scope), T (intermediary) and S (validated scope); a
    procedure validated in S{x}; target scope R{a}. R{a} < T{m} is declared by one
    owner and T{m} < S{x} by another, so the proof needs the intermediate rule."""

    def __init__(self, *, t_rule: ClassificationRule | None = None):
        self.records = Records()
        self.r = self.records.put(_rule("Rule R: all of S's conditions and one more."))
        self.s = self.records.put(_rule("Rule S."))
        self.t = self.records.put(t_rule if t_rule is not None else _rule("Rule T: intermediate."))
        self.x = "classification-rule:" + "9" * 64  # disconnected and never held
        self.validated = {CASES: RuleRestriction(self.s, ("EX:x",))}
        self.procedure = self.records.put(_procedure("Assay", self.validated))
        self.estimator = self.records.put(_procedure("Estimator", None))
        self.scope_values = {CASES: ScopedRestriction("existential", RuleRestriction(self.r, ("EX:a",)))}

    def tables(self, *, retire_second: bool = False, extra: bool = False):
        first = {"r-t": relation((self.r, "a"), "narrower", (self.t, "m"))}
        if extra:
            first["x-y"] = relation((self.x, "q"), "narrower", (self.x.replace("9", "8"), "r"))
        second = {"t-s": relation((self.t, "m"), "narrower", (self.s, "x"), retired=retire_second)}
        return first, second

    def profile(self, *tables):
        owners = ("scope-relations", "scope-relations-b")
        contracts = [
            parse_domain_contract(relations_document(table, namespace=owner), source=owner, base=BASE, predecessor=None)
            for owner, table in zip(owners, tables, strict=False)
        ]
        endpoints = parse_domain_contract(endpoint_document(), source="testing", base=BASE, predecessor=None)
        return compile_profile(BASE, [endpoints, *contracts])

    def applicability(self, profile, *, values=None):
        values = self.scope_values if values is None else values
        return build_applicability(profile, TESTING_CLAIM, values, snapshot=UNCONSULTED)[0]

    def estimand(self, profile, *, assumptions=(), procedure=None, scope=None):
        response = MeasuredBinding(
            "cause",
            None,
            Measure(
                OBSERVABLE,
                "testing/tpm",
                None,
                "ratio",
                "level",
                "testing/identity",
                self.procedure if procedure is None else procedure,
            ),
            None,
            None,
        )
        estimand, _ = build_estimand(
            profile,
            TESTING_CLAIM,
            snapshot=UNCONSULTED,
            form="contrast",
            functional="testing/difference-of-means",
            bindings={"response": response, "grouping": _grouping()},
            outputs={"estimate": OutputSpec("response-difference", "real")},
            reference=ValueReference(Decimal(0)),
            control=Control("testing/randomized", (), "testing/independent-groups", "testing/cohort-enrolment"),
            uncertainty="interval",
            assumptions=assumptions,
            calibration=None,
            applicability=self.applicability(profile, values=scope),
            records=self.records,
        )
        return estimand

    def freeze(self, profile, estimand):
        draft = spec_draft(estimand=estimand, applicability=self.applicability(profile))
        return freeze(
            draft,
            held_rules=spec_rules(),
            rule_procedures={"median-difference/v1": self.estimator},
            profile=profile,
            claim=TESTING_CLAIM,
            records=self.records,
        )


def _corrupt(node, facet):
    """The same id and kind with a facet that no longer decodes."""
    return Node(id=node.id, kind=node.kind, title=node.title, facets={**node.facets, facet: {"bad": True}})


def _grouping():
    from beliefs.claim import Referent

    return RoleTermLevels("cause", None, (Referent("testing/entity", "EX:ndmm"), Referent("testing/entity", "EX:pd")))


def _validity(world: World) -> AssumptionInstance:
    return AssumptionInstance(
        "testing/procedure-validity", {"record": world.procedure, "co_scope": "unknown", "dimensions": CASES}
    )


def test_current_scope_requirements():
    world = World()
    bare = world.profile()
    declared = world.profile(*world.tables(extra=True))

    # Without the declaration the waiver is not licensed (C6: matching rows or labels alone stay unknown).
    assert world.estimand(bare).assumptions == (_validity(world),)
    # With the explicit two-owner proof the procedure-validity assumption is not required.
    estimand = world.estimand(declared)
    assert estimand.assumptions == ()
    spec = world.freeze(declared, estimand)
    reader = author_scope_reader(declared, world.records)
    requirements = target_scope_requirements(spec.assessed_target, reader=reader)
    assert requirements.required == ()
    assert requirements.missing == ()  # explicit proof present
    reads = reader.reads
    assert {world.r, world.s, world.t} <= set(reads)
    assert world.x not in reads  # a disconnected rule is neither read nor required to be held
    assert [c.relations for c in reader.comparisons] == [("scope-relations-b/t-s", "scope-relations/r-t")]

    # Additional explicit assumptions remain accepted.
    extra = AssumptionInstance(
        "testing/procedure-validity", {"record": world.procedure, "co_scope": "broader", "dimensions": CASES}
    )
    frozen = world.freeze(declared, world.estimand(declared, assumptions=(extra,)))
    assert (
        target_scope_requirements(frozen.assessed_target, reader=author_scope_reader(declared, world.records)).missing
        == ()
    )


@pytest.mark.parametrize("failure", ["missing", "corrupt", "wrong-kind", "wrong-classes-sort"])
def test_invalid_selected_rules_refuse(failure):
    world = World(t_rule=_rule("Rule T.", "testing/stage") if failure == "wrong-classes-sort" else None)
    declared = world.profile(*world.tables())
    if failure == "missing":
        del world.records.nodes[world.t]
    elif failure == "corrupt":
        world.records.nodes[world.t] = _corrupt(world.records.nodes[world.t], "classification-rule")
    elif failure == "wrong-kind":
        world.records.nodes[world.t] = world.records.nodes[world.procedure]
    # The checked use refuses before any assumption is suppressed; there is no smaller-graph fallback.
    with pytest.raises(errors.ScopeDependencyIneligible) as refused:
        world.estimand(declared)
    assert world.t in refused.value.record_ids
    # Same-rule comparisons need no graph record at all.
    reader = author_scope_reader(declared, world.records)
    same = reader.compare(
        {CASES: RuleRestriction(world.r, ("EX:a",))}, {CASES: RuleRestriction(world.r, ("EX:a", "EX:b"))}
    )
    assert same.verdict == "narrower" and reader.reads == ()


def test_nested_frozen_entries_survive_relation_successors():
    world = World()
    first, second = world.tables()
    original = world.profile(first, second)
    spec = world.freeze(original, world.estimand(original))
    target = spec.assessed_target
    projection = target_projection(target)
    roots = [entry.id for entry in target.dependencies]

    added = world.profile({**first, "extra": relation((world.r, "b"), "narrower", (world.t, "m"))}, second)
    retired = world.profile(*world.tables(retire_second=True))
    for profile in (original, added, retired):
        # Stored entries are body-derived: no relation context enters them, and the
        # target bytes and key are unchanged under every successor table.
        assert dependency_closure(roots, world.records, profile) == target.dependencies
        assert target_projection(target) == projection
        assert world.t not in {entry.id for entry in target.dependencies}
    # Original-pin replay keeps its result; a changed table alone is no corruption.
    assert target_scope_requirements(target, reader=author_scope_reader(original, world.records)).missing == ()
    assert target_scope_requirements(target, reader=author_scope_reader(added, world.records)).missing == ()

    # Real body/entry corruption still refuses.
    world.records.nodes[world.procedure] = _corrupt(world.records.nodes[world.procedure], "procedure")
    with pytest.raises(errors.MalformedRecord):
        dependency_closure(roots, world.records, original)


def test_retired_waiver_requires_an_explicit_assumption():
    world = World()
    original = world.profile(*world.tables())
    stale = world.estimand(original)
    assert stale.assumptions == ()
    retired = world.profile(*world.tables(retire_second=True))
    target = world.freeze(original, stale).assessed_target

    requirements = target_scope_requirements(target, reader=author_scope_reader(retired, world.records))
    assert requirements.required == requirements.missing == (_validity(world),)
    # Freezing the stale waiver under the successor refuses, naming the missing particulars.
    with pytest.raises(errors.ScopeValidityIncompatible) as refused:
        world.freeze(retired, stale)
    assert refused.value.missing == (_validity(world),)
    # A newly authored estimand carries the now-required assumption and freezes.
    fresh = world.estimand(retired)
    assert fresh.assumptions == (_validity(world),)
    assert world.freeze(retired, fresh).assessed_target.estimand.assumptions == (_validity(world),)
