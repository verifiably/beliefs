"""`read_composite` (design §6, U8): rows equal the wrapper's answers; the node receipt sits on the reading."""

from __future__ import annotations

from dataclasses import replace

import pytest
from domain_facet_fixtures import over_kwargs
from profiles import pins_for
from test_composite_boundary import GENE, SNAPSHOT, A, _build, _claim, _estimand, _proposition, _writer
from test_evaluation import _observations  # the held byte observations helper, keyed by dataset address

from beliefs import stored
from beliefs.belief import Availability, Belief, NoBelief, NotReached, Refused, SuppliedContext
from beliefs.composite import CompositeError, CompositeNode, CompositeReading, build_composite, read_composite
from beliefs.corpus import lineage_snapshot
from beliefs.evaluation import evaluate_over
from beliefs.identity import v1
from beliefs.policy import BELIEF_V1, BELIEF_V1_FIXTURES, BELIEF_V1_RULE, PolicyBinding, PolicyImplementation
from beliefs.projection import project_claim
from beliefs.resolution import TermOutcome, build_snapshot

BINDING = PolicyBinding(rule=BELIEF_V1_RULE, implementation=BELIEF_V1.identity)


@pytest.fixture()
def corpus(tmp_path):
    """Three propositions over an acyclic graph a→b, b⊣c, a→c: `ab` assessed once
    (supported, verified, held), `bc` unassessed, `ac` (unsigned) superseded by `ac2` (positive)."""
    w = _writer(tmp_path / "corpus")
    ab = _proposition(w, "ab", _claim("EX:a", "EX:b"))
    _proposition(w, "bc", _claim("EX:b", "EX:c", polarity="negative"))
    ac = _proposition(w, "ac", _claim("EX:a", "EX:c", polarity="unsigned"))
    ac2 = w.supersede(stored.proposition_node("ac2", title="ac2", claim=project_claim(_claim("EX:a", "EX:c"))), of=ac.id)
    # One admitted assessment of `ab`: an observing run over a held dataset, a passed clean-environment verification,
    # typed under the profile that restores it (Step 4).
    from test_evaluation import seed_assessed_proposition

    dataset_address = seed_assessed_proposition(w, ab.id, slug="a-ab", estimand=_estimand(_claim("EX:a", "EX:b")), applicability={})
    return w, dataset_address, ac.id, ac2.id


def _inputs(w, dataset_address, *, hold=True, with_policy=True):
    view = w.read_view
    context = SuppliedContext(
        snapshot=lineage_snapshot(view, (dataset_address,)),
        producer_snapshot_identity="producer-snapshot-1",
        node_corpus={},
        pins={"c1": pins_for(w.profile)},
    )
    availability = Availability(
        observations=_observations("a") if hold else {},
        implementations={BELIEF_V1.identity: BELIEF_V1} if with_policy else {},
        fixtures={BELIEF_V1_RULE: BELIEF_V1_FIXTURES},
    )
    return {"context": context, "availability": availability, "resolution": SNAPSHOT, "binding": BINDING, "profile": w.profile}


def test_rows_equal_the_wrapper_answers_and_columns_share_one_admission(corpus):
    w, dataset_address, ac, ac2 = corpus
    minted = w.add(stored.composite_node(_build(w, ["proposition:ab", "proposition:bc", ac]), title="g"))
    reading = read_composite(w.read_view, minted.id, **_inputs(w, dataset_address))
    assert reading.identity == stored.stored_semantic_hash(w.read_view.get(minted.id))
    by_ref = {row.ref: row for row in reading.rows}
    for ref, row in by_ref.items():
        assert row.belief == evaluate_over(w.read_view, ref, **over_kwargs(_inputs(w, dataset_address)))
    assert isinstance(by_ref["proposition:ab"].belief, Belief) and by_ref["proposition:ab"].identification == ("EX:observational",)
    assert by_ref["proposition:bc"].belief == NoBelief("no-eligible-assessment") and by_ref["proposition:bc"].identification == ()
    assert by_ref[ac].resolution.state == "superseded" and by_ref[ac].resolution.successors == (ac2,)
    assert {row.role.sign for row in reading.rows} == {"positive", "negative", "unsigned"}
    assert set(reading.node_outcomes) == {"node:0", "node:1", "node:2"} and reading.standing.state == "active"


def test_withholding_follows_the_evaluator(corpus):
    w, dataset_address, _, _ = corpus
    minted = w.add(stored.composite_node(_build(w, ["proposition:ab"]), title="g"))
    unheld = read_composite(w.read_view, minted.id, **_inputs(w, dataset_address, hold=False)).rows[0]
    assert unheld.belief == evaluate_over(w.read_view, "proposition:ab", **over_kwargs(_inputs(w, dataset_address, hold=False)))
    assert isinstance(unheld.belief, NoBelief) and unheld.identification == ()
    no_policy = read_composite(w.read_view, minted.id, **_inputs(w, dataset_address, with_policy=False)).rows[0]
    assert no_policy.belief == NoBelief("unavailable-policy-unheld") and no_policy.identification == NotReached()


def test_answers_before_admission_carry_not_reached(corpus):
    w, dataset_address, *_ = corpus
    minted = w.add(stored.composite_node(_build(w, ["proposition:ab"]), title="g"))
    inputs = _inputs(w, dataset_address)

    fixtures_unheld = read_composite(
        w.read_view,
        minted.id,
        **{**inputs, "availability": replace(inputs["availability"], fixtures={})},
    ).rows[0]
    assert fixtures_unheld.belief == NoBelief("unavailable-fixtures-unheld")
    assert fixtures_unheld.identification == NotReached()

    broken = PolicyImplementation(identity=BELIEF_V1.identity, aggregate=lambda _problem: 999)
    fixture_failure = read_composite(
        w.read_view,
        minted.id,
        **{
            **inputs,
            "availability": replace(inputs["availability"], implementations={BELIEF_V1.identity: broken}),
        },
    ).rows[0]
    assert isinstance(fixture_failure.belief, Refused)
    assert fixture_failure.belief.reason.startswith("implementation-fails-fixtures")
    assert fixture_failure.identification == NotReached()

    gather_exception = read_composite(
        w.read_view,
        minted.id,
        **{
            **inputs,
            "context": replace(
                inputs["context"],
                pins={"c1": replace(pins_for(w.profile), science_contract="science:" + "0" * 64)},
            ),
        },
    ).rows[0]
    assert isinstance(gather_exception.belief, Refused)
    assert gather_exception.identification == NotReached()

    absent_context = replace(
        inputs["context"],
        snapshot=replace(inputs["context"].snapshot, not_present={dataset_address: "corpus-elsewhere"}),
    )
    corpus_absent = read_composite(
        w.read_view,
        minted.id,
        **{**inputs, "context": absent_context},
    ).rows[0]
    assert isinstance(corpus_absent.belief, NoBelief)
    assert corpus_absent.belief.reason == "unavailable-corpus-absent"
    assert corpus_absent.identification == NotReached()


def test_two_inconclusive_admitted_assessments_keep_their_terms(corpus):
    w, dataset_address, *_ = corpus
    from test_evaluation import seed_assessed_proposition

    bc = _estimand(_claim("EX:b", "EX:c", polarity="negative"))
    seed_assessed_proposition(w, "proposition:bc", slug="i-1", outcome="inconclusive", estimand=bc, applicability={})
    seed_assessed_proposition(w, "proposition:bc", slug="i-2", outcome="inconclusive", estimand=bc, applicability={})
    minted = w.add(stored.composite_node(_build(w, ["proposition:bc"]), title="g"))
    row = read_composite(w.read_view, minted.id, **_inputs(w, dataset_address)).rows[0]
    assert row.belief == NoBelief("no-directional-outcome")
    assert row.identification == ("EX:observational",)


def test_the_reading_admits_each_member_once_and_never_calls_admit_itself(corpus, monkeypatch):
    """Two traps, because the two declared mutations differ: a second
    `belief.admitted` call over the gathered records, and a direct
    `admission.admit` call per gathered assessment. `admit` is counted through
    the module `belief.admitted` resolves it from, so a `read_composite` that
    imported it itself would still be counted — `admit` has one home."""
    from beliefs import admission as admission_module
    from beliefs import belief as belief_module

    admitted_calls, admit_calls = [], []
    original_admitted, original_admit = belief_module.admitted, belief_module.admit

    def trap_admitted(*args, **kwargs):
        admitted_calls.append(1)
        return original_admitted(*args, **kwargs)

    def trap_admit(*args, **kwargs):
        admit_calls.append(1)
        return original_admit(*args, **kwargs)

    monkeypatch.setattr(belief_module, "admitted", trap_admitted)
    monkeypatch.setattr(belief_module, "admit", trap_admit)
    monkeypatch.setattr(admission_module, "admit", trap_admit)
    w, dataset_address, *_ = corpus
    minted = w.add(stored.composite_node(_build(w, ["proposition:ab", "proposition:bc"]), title="g"))
    read_composite(w.read_view, minted.id, **_inputs(w, dataset_address))
    assert admitted_calls == [1, 1]  # one per member, from the evaluator
    assert admit_calls == [1]  # `ab` has one distinct assessment; `bc` has none — nothing outside the evaluator called it


def test_an_unresolvable_member_refuses_the_reading(corpus):
    w, dataset_address, *_ = corpus
    minted = w.add(stored.composite_node(_build(w, ["proposition:ab", "proposition:bc"]), title="g"))
    w.delete("proposition:bc")
    with pytest.raises(CompositeError) as caught:
        read_composite(w.read_view, minted.id, **_inputs(w, dataset_address))
    assert caught.value.code == "composite-member-unresolvable"


def test_a_memberless_composite_reads_no_rows_and_a_node_receipt(corpus):
    w, dataset_address, *_ = corpus
    value, _ = build_composite(w.profile, w.read_view, shape="dag", nodes=[A, CompositeNode(GENE, "EX:z")], members=[], snapshot=build_snapshot(), slug="m")
    minted = w.add(stored.composite_node(value, title="m"))
    unconsulted = {**_inputs(w, dataset_address), "resolution": build_snapshot()}
    reading = read_composite(w.read_view, minted.id, **unconsulted)
    assert reading.rows == ()
    assert reading.node_outcomes == {"node:0": TermOutcome.NOT_CONSULTED, "node:1": TermOutcome.NOT_CONSULTED}
    assert v1.encode(reading.projection())  # canonically encodable


def test_the_reading_refuses_a_node_the_consulted_vocabulary_excludes(corpus):
    w, dataset_address, *_ = corpus
    value, _ = build_composite(w.profile, w.read_view, shape="dag", nodes=[A, CompositeNode(GENE, "EX:z")], members=[], snapshot=build_snapshot(), slug="m")
    minted = w.add(stored.composite_node(value, title="m"))
    with pytest.raises(CompositeError) as caught:
        read_composite(w.read_view, minted.id, **_inputs(w, dataset_address))  # SNAPSHOT consults EX and lacks z
    assert caught.value.code == "composite-node-not-member" and "node:1" in str(caught.value)


def test_the_reading_has_no_public_constructor(corpus):
    """`identity` is the content hash `read_composite` takes over the facet it read.
    A public constructor would let a hand-authored value pair any identity with any
    rows and project it as a reading — `Composite`'s gate, for the same reason."""
    w, dataset_address, *_ = corpus
    minted = w.add(stored.composite_node(_build(w, ["proposition:ab"]), title="g"))
    read = read_composite(w.read_view, minted.id, **_inputs(w, dataset_address))
    with pytest.raises(CompositeError) as caught:
        CompositeReading()  # type: ignore[call-arg]
    assert caught.value.code == "composite-unread"
    with pytest.raises(CompositeError) as caught:
        CompositeReading._checked(object(), **{f: getattr(read, f) for f in ("ref", "identity", "shape", "nodes", "standing", "node_outcomes", "rows")})
    assert caught.value.code == "composite-unread"


def test_a_superseded_composite_reports_its_successor(corpus):
    w, dataset_address, *_ = corpus
    first = w.add(stored.composite_node(_build(w, ["proposition:ab"], slug="v1"), title="v1"))
    second = w.supersede(stored.composite_node(_build(w, ["proposition:ab", "proposition:bc"], slug="v2"), title="v2"), of=first.id)
    reading = read_composite(w.read_view, first.id, **_inputs(w, dataset_address))
    assert reading.standing.state == "superseded" and reading.standing.successors == (second.id,)


def _assessments_naming(view, ref: str) -> set[str]:
    return {
        node.id
        for node in view.iter_stored()
        if node.kind == "assessment"
        and any(r.predicate == stored.ASSESSES and r.target == ref for r in node.relations)
    }


def test_the_identification_column_reads_only_the_assessments_naming_the_member(corpus, monkeypatch):
    """Design §6.2: the column is the admitted assessments *of that member*. A
    scan over every stored assessment decodes records the column cannot use,
    and makes one member's reading depend on another's records."""
    from test_evaluation import seed_assessed_proposition

    w, dataset_address, *_ = corpus
    seed_assessed_proposition(
        w, "proposition:bc", slug="i-bc",
        estimand=_estimand(_claim("EX:b", "EX:c", polarity="negative")), applicability={},
    )
    minted = w.add(stored.composite_node(_build(w, ["proposition:ab"]), title="g"))
    unrelated = _assessments_naming(w.read_view, "proposition:bc")
    assert unrelated

    decoded: list[str] = []
    original = stored.assessment_value

    def counting(node, **kwargs):
        decoded.append(node.id)
        return original(node, **kwargs)

    monkeypatch.setattr(stored, "assessment_value", counting)
    reading = read_composite(w.read_view, minted.id, **_inputs(w, dataset_address))

    assert reading.rows[0].identification == ("EX:observational",)
    assert not (set(decoded) & unrelated)


def test_a_divergent_assesses_edge_is_skipped_by_both_columns(corpus):
    """Both columns select membership by the assesses edge before decoding."""
    from fixtures_cut4 import raw_write, reopen
    from nodes.core.relations import Relation

    w, dataset_address, *_ = corpus
    minted = w.add(stored.composite_node(_build(w, ["proposition:ab"]), title="g"))
    assessment = next(iter(_assessments_naming(w.read_view, "proposition:ab")))
    node = w.read_view.get(assessment)
    node.relations = [
        Relation(source=node.id, predicate=r.predicate, target="proposition:bc")
        if r.predicate == stored.ASSESSES
        else r
        for r in node.relations
    ]
    raw_write(w.root, node)  # the stamp covers the facet, not the relations

    row = read_composite(reopen(w.root), minted.id, **_inputs(w, dataset_address)).rows[0]
    assert row.belief == NoBelief("no-eligible-assessment") and row.identification == ()


def test_a_composite_ref_that_resolves_nowhere_refuses_under_its_own_code(corpus):
    """`read_composite`'s own `view.get`: the composite is unresolvable, which is
    not what `composite-member-unresolvable` says."""
    w, dataset_address, *_ = corpus
    with pytest.raises(CompositeError) as caught:
        read_composite(w.read_view, "composite:missing", **_inputs(w, dataset_address))
    assert caught.value.code == "composite-unresolvable"


def test_a_pre_grammar_assessment_elsewhere_is_not_decoded(corpus):
    """An unrelated malformed assessment cannot poison this member's read."""
    from fixtures_cut4 import raw_write, reopen

    from beliefs.evaluation import gather

    w, dataset_address, *_ = corpus
    minted = w.add(stored.composite_node(_build(w, ["proposition:ab"]), title="g"))
    pre_grammar = stored.stamp_semantic_identity(
        stored._node(
            "assessment", "pre", "pre",
            {stored.ASSESSMENT_FACET: {
                "spec": "spec-old", "run": "run:x", "proposition": "proposition:elsewhere",
                "outcome": "supported", "interpretation_rule": "rule-1", "estimand": "prose",
            }},
            (),
        )
    )
    raw_write(w.root, pre_grammar)
    view = reopen(w.root)
    inputs = _inputs(w, dataset_address)
    gathered = gather(view, "proposition:ab", context=inputs["context"], profile=inputs["profile"],
                      resolution=inputs["resolution"], binding=inputs["binding"])
    assert len(gathered.assessments) == 1
    row = read_composite(view, minted.id, **inputs).rows[0]
    assert isinstance(row.belief, Belief) and row.identification == ("EX:observational",)


def test_a_retracted_support_reaches_the_composite_member(corpus):
    from test_local_standing import retracts

    w, dataset_address, *_ = corpus
    minted = w.add(stored.composite_node(_build(w, ["proposition:ab"]), title="g"))
    before = read_composite(w.read_view, minted.id, **_inputs(w, dataset_address)).rows[0]
    assert isinstance(before.belief, Belief)
    w.retract(retracts(w.read_view.get("assessment:a-ab"), "withdraw-support"))
    after = read_composite(w.read_view, minted.id, **_inputs(w, dataset_address)).rows[0]
    assert after.belief == NoBelief("no-eligible-assessment")
    assert after.identification == ()


@pytest.mark.parametrize("surviving", [False, True])
def test_identification_never_decodes_a_retracted_malformed_assessment(corpus, surviving):
    from fixtures_cut4 import raw_write, reopen
    from test_evaluation import seed_assessed_proposition
    from test_local_standing import retracts

    w, dataset_address, *_ = corpus
    if surviving:
        seed_assessed_proposition(
            w, "proposition:ab", slug="survivor",
            estimand=_estimand(_claim("EX:a", "EX:b")), applicability={},
        )
    minted = w.add(stored.composite_node(_build(w, ["proposition:ab"]), title="g"))
    malformed = w.read_view.get("assessment:a-ab")
    malformed.facets[stored.ASSESSMENT_FACET]["outcome"] = "malformed"
    malformed = stored.stamp_semantic_identity(malformed)
    raw_write(w.root, malformed)
    raw_write(w.root, stored.stamp_semantic_identity(retracts(malformed, "withdraw-malformed")))
    view = reopen(w.root)
    inputs = _inputs(w, dataset_address)
    expected = evaluate_over(view, "proposition:ab", **over_kwargs(inputs))
    if surviving:
        assert isinstance(expected, Belief)
    else:
        assert expected == NoBelief("no-eligible-assessment")
    row = read_composite(view, minted.id, **inputs).rows[0]
    assert row.belief == expected
    assert row.identification == (("EX:observational",) if surviving else ())
