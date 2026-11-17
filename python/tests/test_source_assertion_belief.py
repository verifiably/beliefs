"""Inertness of stored `source-assertion` records in belief evaluation and claim views."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from authority import ACTOR
from domain_facet_fixtures import CLAIM_FACET
from fixtures_cut3 import only_assessed_key
from fixtures_cut4 import raw_write, reopen
from profiles import pins_for
from test_belief import PROFILE
from test_evaluation import OTHER_PROPOSITION_REF, PROPOSITION_REF, _fixture

from beliefs import stored
from beliefs.belief import Availability, Belief, NoBelief, SuppliedContext
from beliefs.corpus import lineage_snapshot
from beliefs.evaluation import claim_view, evaluate_over, evaluate_over_traced, gather
from beliefs.policy import BELIEF_V1, BELIEF_V1_FIXTURES, BELIEF_V1_RULE, PolicyBinding
from beliefs.resolution import build_snapshot
from beliefs.source_assertion import Bearing, Reading, Representation, SourceAssertion, Span
from beliefs.world import registry


def _assertion(
    source_id: str,
    proposition_id: str,
    *,
    sign: str,
    quote: str,
    locator: str,
    extent: str = "full",
    attributed_to: str | None = None,
) -> SourceAssertion:
    return SourceAssertion(
        source=source_id,
        read=Reading(
            representation=Representation(
                sha256="a" * 64,
                media_type="application/pdf",
                extent=extent,
            ),
            span=Span(quote=quote, locator=locator),
            extracted_by=ACTOR,
            attributed_to=attributed_to,
        ),
        bears_on=Bearing(sign=sign, proposition=proposition_id),
        recorded_by=ACTOR,
    )


def test_stored_assertions_move_no_belief_byte(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path, PROPOSITION_REF)
    before = evaluate_over(fixture.view, fixture.proposition, **fixture.kwargs)
    assert isinstance(before, Belief)
    assert before.value == 2
    before_view = claim_view(fixture.view, fixture.proposition, **fixture.kwargs)

    source = stored.source_node(title="Smith 2024", identifiers={"doi": "10.1000/smith-2024"})
    assertions = (
        (
            _assertion(
                source.id,
                PROPOSITION_REF,
                sign="asserts",
                quote="Gene X increases phenotype Y.",
                locator="Results, para 1",
            ),
            "Assertion 1",
            "",
        ),
        (
            _assertion(
                source.id,
                PROPOSITION_REF,
                sign="denies",
                quote="Gene X did not increase phenotype Y in cohort B.",
                locator="Abstract, line 4",
                extent="abstract",
                attributed_to="Smith et al. (2024)",
            ),
            "Assertion 2",
            "Contradictory subgroup statement in abstract.",
        ),
        (
            _assertion(
                source.id,
                PROPOSITION_REF,
                sign="hypothesizes",
                quote="We hypothesize Gene X regulates phenotype Y.",
                locator="Discussion, para 3",
                attributed_to="MSigDB curators",
            ),
            "Assertion 3",
            "",
        ),
        (
            _assertion(
                source.id,
                OTHER_PROPOSITION_REF,
                sign="asserts",
                quote="Other gene affects phenotype Y.",
                locator="Results, para 5",
                attributed_to="Other curators",
            ),
            "Unrelated assertion",
            "Targets an unrelated proposition.",
        ),
    )

    raw_write(tmp_path, source)
    nodes = [stored.source_assertion_node(value, title=title, body=body) for value, title, body in assertions]
    for node in nodes:
        raw_write(tmp_path, node)

    view = reopen(tmp_path)
    assert view.holds(source.id)
    for (value, _, body), node in zip(assertions, nodes, strict=True):
        assert view.holds(node.id)
        stored_node = view.get(node.id)
        assert stored_node.body == body
        assert stored.source_assertion_value(stored_node) == value

    after = evaluate_over(view, fixture.proposition, **fixture.kwargs)
    assert after == before
    assert isinstance(after, Belief)
    assert after.belief_input_digest == before.belief_input_digest
    # ClaimView.snapshot digests the full captured corpus (`view.iter_stored()`), so adding
    # source/source-assertion records moves `snapshot` while leaving every belief and pair verdict identical.
    after_view = claim_view(view, fixture.proposition, **fixture.kwargs)
    assert after_view.snapshot != before_view.snapshot
    assert after_view.beliefs == before_view.beliefs
    assert after_view == replace(before_view, snapshot=after_view.snapshot)

    traced_answer, _admission = evaluate_over_traced(view, fixture.proposition, **fixture.kwargs)
    assert traced_answer == before

    inputs = gather(
        view,
        fixture.proposition,
        key=only_assessed_key(view, fixture.proposition, profile=fixture.gather_kwargs["profile"]),
        observations={},
        **fixture.gather_kwargs,
    )
    assert inputs.records().source_assertions == ()
    assert "source-assertion" not in {kind for kind, _ in inputs.read_trace}
    assert set(inputs.read_trace) <= inputs.declared_refs()


def test_assertions_alone_yield_no_belief(tmp_path: Path) -> None:
    (tmp_path / "corpus.yaml").write_bytes(
        registry.manifest_bytes(registry.CorpusManifest(2, "c1" + "0" * 30, pins_for(PROFILE)))
    )
    prop = stored.proposition_node("p", title="p", claim=CLAIM_FACET)
    source = stored.source_node(title="Paper", identifiers={"pmid": "12345"})
    raw_write(tmp_path, prop)
    raw_write(tmp_path, source)
    for sign, locator in (("asserts", "p1"), ("denies", "p2"), ("hypothesizes", "p3")):
        value = _assertion(
            source.id,
            prop.id,
            sign=sign,
            quote=f"Statement ({sign})",
            locator=locator,
            attributed_to="Curator",
        )
        raw_write(tmp_path, stored.source_assertion_node(value, title=sign))

    view = reopen(tmp_path)
    answer = evaluate_over(
        view,
        prop.id,
        availability=Availability(
            observations={},
            implementations={BELIEF_V1.identity: BELIEF_V1},
            fixtures={BELIEF_V1_RULE: BELIEF_V1_FIXTURES},
        ),
        context=SuppliedContext(
            snapshot=lineage_snapshot(view, ()),
            producer_snapshot_identity="producer-snapshot-1",
            node_corpus={},
            pins={"c1": pins_for(PROFILE)},
        ),
        profile=PROFILE,
        resolution=build_snapshot(readable={}),
        binding=PolicyBinding(rule=BELIEF_V1_RULE, implementation=BELIEF_V1.identity),
    )
    assert answer == NoBelief("no-eligible-assessment")
