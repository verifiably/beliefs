"""`read_composite` (design §6, U8): rows equal the wrapper's answers; the node receipt sits on the reading."""

from __future__ import annotations

import pytest
from profiles import pins_for
from test_composite_boundary import GENE, SNAPSHOT, A, _build, _claim, _estimand, _proposition, _writer
from test_evaluation import _observations  # the held byte observations helper, keyed by dataset address

from beliefs import stored
from beliefs.belief import Availability, Belief, NoBelief, NotReached, SuppliedContext
from beliefs.closure import RetractionEnumeration
from beliefs.composite import CompositeError, CompositeNode, build_composite, read_composite
from beliefs.corpus import lineage_snapshot
from beliefs.evaluation import evaluate_over
from beliefs.identity import v1
from beliefs.policy import BELIEF_V1, BELIEF_V1_FIXTURES, BELIEF_V1_RULE, PolicyBinding
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
        retractions=RetractionEnumeration(found=(), coverage=("c1",)),
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
        assert row.belief == evaluate_over(w.read_view, ref, **_inputs(w, dataset_address))
    assert isinstance(by_ref["proposition:ab"].belief, Belief) and by_ref["proposition:ab"].identification == ("EX:observational",)
    assert by_ref["proposition:bc"].belief == NoBelief("no-eligible-assessment") and by_ref["proposition:bc"].identification == ()
    assert by_ref[ac].resolution.state == "superseded" and by_ref[ac].resolution.successors == (ac2,)
    assert {row.role.sign for row in reading.rows} == {"positive", "negative", "unsigned"}
    assert set(reading.node_outcomes) == {"node:0", "node:1", "node:2"} and reading.standing.state == "active"


def test_withholding_follows_the_evaluator(corpus):
    w, dataset_address, _, _ = corpus
    minted = w.add(stored.composite_node(_build(w, ["proposition:ab"]), title="g"))
    unheld = read_composite(w.read_view, minted.id, **_inputs(w, dataset_address, hold=False)).rows[0]
    assert unheld.belief == evaluate_over(w.read_view, "proposition:ab", **_inputs(w, dataset_address, hold=False))
    assert isinstance(unheld.belief, NoBelief) and unheld.identification == ()
    no_policy = read_composite(w.read_view, minted.id, **_inputs(w, dataset_address, with_policy=False)).rows[0]
    assert no_policy.belief == NoBelief("unavailable-policy-unheld") and no_policy.identification == NotReached()


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


def test_a_superseded_composite_reports_its_successor(corpus):
    w, dataset_address, *_ = corpus
    first = w.add(stored.composite_node(_build(w, ["proposition:ab"], slug="v1"), title="v1"))
    second = w.supersede(stored.composite_node(_build(w, ["proposition:ab", "proposition:bc"], slug="v2"), title="v2"), of=first.id)
    reading = read_composite(w.read_view, first.id, **_inputs(w, dataset_address))
    assert reading.standing.state == "superseded" and reading.standing.successors == (second.id,)
