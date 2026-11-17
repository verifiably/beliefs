"""Pair comparison captures and checks its own scope context.

Scope containment design §7.4; acceptance cases C11, C12 and C17 for pairwise
convertibility and synthesis.
"""

from __future__ import annotations

from dataclasses import replace

from fixtures_cut4 import raw_write, reopen
from lineage_fixtures import node_retraction
from profiles import pins_for
from scope_fixtures import CASES
from test_scope_evaluation import Scene, _HeldView

from beliefs.applicability import ScopedRestriction
from beliefs.belief import Belief
from beliefs.comparability import ComparabilitySnapshot
from beliefs.eligibility import closure_eligibility
from beliefs.restriction import RuleRestriction, co_scope
from beliefs.target_comparison import PermittedUnder, TargetNotConvertible


def _rows(scene, profile):
    world = scene.world
    s_scope = {CASES: ScopedRestriction("existential", RuleRestriction(world.s, ("EX:x",)))}
    return [
        ("a", world.estimand(profile, procedure=scene.universal, scope=world.scope_values), world.scope_values),
        ("c", world.estimand(profile, procedure=scene.universal, scope=s_scope), s_scope),
        ("d", world.estimand(profile, procedure=scene.universal, scope={}), {}),
    ]


def _pair(view, left, right):
    return next(p for p in view.pairs if {p.left, p.right} == {left, right})


def test_pair_only_scope_context_is_captured(tmp_path):
    scene = Scene(tmp_path / "corpus", rows=_rows)
    profile, t = scene.profile(), scene.world.t
    evaluation = scene.evaluate(profile)
    a, c = scene.key("a"), scene.key("c")
    pair = _pair(evaluation.view, a, c)
    assert isinstance(pair.synthesis, PermittedUnder)
    assert pair.evidence is not None
    assert t in pair.evidence.dependencies.closure.reads
    assert "scope-relations-b" in dict(pair.evidence.consulted)
    assert "scope-terms" in dict(pair.evidence.consulted)  # the intermediate rule's body terms
    left_inputs, right_inputs = evaluation.traces[a][2], evaluation.traces[c][2]
    assert left_inputs is not None and right_inputs is not None
    assert t not in left_inputs.dependencies.closure.reads
    assert t not in right_inputs.dependencies.closure.reads
    assert "scope-relations-b" not in dict(left_inputs.consulted)
    # Both compared assessments are in the pair's dependency assessment map.
    identities = {value.identity() for value in pair.evidence.dependencies.assessments.values()}
    assert {scene.identity("a"), scene.identity("c")} <= identities
    keyed_digests_before_pair = {key: scene.replay(profile, key) for key in (a, c)}
    keyed_digests_after_pair = {key: evaluation.view.beliefs[key] for key in (a, c)}
    assert keyed_digests_after_pair == keyed_digests_before_pair
    assert all(isinstance(answer, Belief) for answer in keyed_digests_after_pair.values())


def test_pair_rule_or_pin_omission_refuses(tmp_path):
    missing = Scene(tmp_path / "missing", rows=_rows, t_held=False)
    evaluation = missing.evaluate(missing.profile())
    pair = _pair(evaluation.view, missing.key("a"), missing.key("c"))
    assert isinstance(pair.synthesis, TargetNotConvertible)  # no synthesis permission
    assert pair.evidence is not None and missing.world.t in pair.evidence.dependencies.closure.reads
    assert isinstance(evaluation.view.beliefs[missing.key("a")], Belief)  # the keyed beliefs never needed it

    # A retracted selected rule cannot be evaded by another proof in its component.
    retracted = Scene(tmp_path / "retracted", rows=_rows)
    raw_write(retracted.root, node_retraction(retracted.world.records.nodes[retracted.world.t], "retract-t"))
    pair = _pair(retracted.evaluate(retracted.profile()).view, retracted.key("a"), retracted.key("c"))
    assert isinstance(pair.synthesis, TargetNotConvertible)

    # Withholding the pair-only relation owner's pin returns no permission.
    scene = Scene(tmp_path / "pins", rows=_rows)
    profile = scene.profile()
    pins = pins_for(profile)
    reduced = replace(pins, domains={ns: pin for ns, pin in pins.domains.items() if ns != "scope-relations-b"})
    view = reopen(scene.root)
    from domain_facet_fixtures import EX, GENE, OTHER_GENE, PHENO
    from test_scope_evaluation import BINDING, PROPOSITION

    from beliefs.evaluation import _evaluate_claim
    from beliefs.resolution import build_snapshot

    evaluation = _evaluate_claim(
        view,
        PROPOSITION,
        availability=scene.availability(),
        context=replace(scene.context(profile, view), pins={"c1": reduced}),
        profile=profile,
        resolution=build_snapshot(readable={EX: [GENE, PHENO, OTHER_GENE]}),
        binding=BINDING,
    )
    pair = _pair(evaluation.view, scene.key("a"), scene.key("c"))
    assert not isinstance(pair.synthesis, PermittedUnder)
    assert isinstance(evaluation.view.beliefs[scene.key("a")], Belief)


def test_consulted_failed_proxy_context_is_retained(tmp_path):
    scene = Scene(tmp_path / "corpus", rows=_rows)
    profile, world = scene.profile(), scene.world
    records = _HeldView(reopen(scene.root), set())
    snapshot = ComparabilitySnapshot(profile, records, lambda id: closure_eligibility((id,), records, profile))
    s_scope = {CASES: RuleRestriction(world.s, ("EX:x",))}
    r_scope = {CASES: RuleRestriction(world.r, ("EX:a",))}
    disconnected = {CASES: RuleRestriction(world.r, ("EX:z",))}
    # A candidate whose comparison is consulted and then rejected keeps its context.
    first = snapshot.compare_scope(r_scope, s_scope)
    second = snapshot.compare_scope(disconnected, s_scope)
    assert first.verdict == "narrower" and second.verdict == "unknown"
    assert snapshot.scope_comparisons == (first, second)
    assert world.t in snapshot.reads and world.t in snapshot.states
    # The pure structural verdict reads nothing and grants nothing on its own.
    assert co_scope(r_scope, s_scope, profile) == "narrower"


def test_pair_context_does_not_leak(tmp_path):
    scene = Scene(tmp_path / "corpus", rows=_rows)
    evaluation = scene.evaluate(scene.profile())
    t = scene.world.t
    for left, right in (("a", "d"), ("c", "d")):
        pair = _pair(evaluation.view, scene.key(left), scene.key(right))
        assert pair.evidence is not None
        assert t not in pair.evidence.dependencies.closure.reads
        assert "scope-relations-b" not in dict(pair.evidence.consulted)
    assert t in _pair(evaluation.view, scene.key("a"), scene.key("c")).evidence.dependencies.closure.reads  # type: ignore[union-attr]


def test_scope_context_end_to_end_under_original_and_successor_pins(tmp_path):
    """Authoring, freezing, stored reads, capture, pure recomputation and pair
    comparison, under the original relation owner and its retiring successor."""

    def rows(scene, profile):
        world = scene.world
        return [*_rows(scene, profile), ("b", world.estimand(profile), world.scope_values)]

    scene = Scene(tmp_path / "corpus", rows=rows)
    original, successor = scene.profile(), scene.profile(retire=True)
    keys = {letter: scene.key(letter) for letter in ("a", "b", "c", "d")}
    before, after = scene.evaluate(original), scene.evaluate(successor)
    for letter in ("a", "b", "c", "d"):
        assert isinstance(before.view.beliefs[keys[letter]], Belief)
    assert isinstance(_pair(before.view, keys["a"], keys["c"]).synthesis, PermittedUnder)
    # The successor withdraws the proof: the stale waiver key alone loses its belief,
    # the unaffected keys keep theirs and their digests, and the pair is no longer permitted.
    assert not isinstance(after.view.beliefs[keys["b"]], Belief)
    for letter in ("a", "c", "d"):
        assert after.view.beliefs[keys[letter]] == before.view.beliefs[keys[letter]]
    assert not isinstance(_pair(after.view, keys["a"], keys["c"]).synthesis, PermittedUnder)
    # Pure recomputation over each key's captured inputs agrees under both pins.
    for profile, evaluation in ((original, before), (successor, after)):
        for key in keys.values():
            assert scene.replay(profile, key) == evaluation.view.beliefs[key]
