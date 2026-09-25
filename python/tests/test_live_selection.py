"""Live view-query evaluation (live-query design §6.1 and the plan's Review Focus)."""

from __future__ import annotations

import pytest
from coordination_fixtures import raw_coordination_node
from dataset_fixtures import dataset_ref, pinned
from fixtures_cut4 import raw_write
from test_world_build import ALPHA, BETA
from test_world_receipts import corpora, world_over
from test_world_selection import PROJECT, query

from beliefs import stored
from beliefs.errors import ResolutionRefused
from beliefs.identity import v1
from beliefs.world import registry
from beliefs.world.live import LIVE_SELECTION_VERSION, CaptureStamp, LiveSelection, evaluate_live_query
from beliefs.world.read import BoundStamp
from beliefs.world.selection import Selection, Unresolved

WORLD = "f" * 32
STATE = "a" * 64
DATASETS = query([{"kinds": ["dataset"]}])


def sample(**overrides) -> LiveSelection:
    fields: dict[str, object] = {
        "stamp": CaptureStamp(WORLD, ((ALPHA, STATE),)),
        "query": DATASETS,
        "selected": (dataset_ref("d-a"),),
        "contributing": (ALPHA,),
        "absent": (),
        "unresolved": (),
    }
    fields.update(overrides)
    return LiveSelection(**fields)  # type: ignore[arg-type]


class TestTypes:
    def test_a_capture_stamp_is_one_world_and_sorted_distinct_states(self):
        assert CaptureStamp(WORLD, ()).coverage == ()
        with pytest.raises(ValueError):
            CaptureStamp("not-a-world", ())
        with pytest.raises(ValueError):
            CaptureStamp(WORLD, (("b" * 32, STATE), ("a" * 32, STATE)))
        with pytest.raises(ValueError):
            CaptureStamp(WORLD, (("a" * 32, STATE), ("a" * 32, STATE)))
        with pytest.raises(ValueError):
            CaptureStamp(WORLD, (("a" * 32, "not-a-state"),))
        with pytest.raises(TypeError):
            CaptureStamp(WORLD, [("a" * 32, STATE)])  # type: ignore[arg-type]

    def test_a_live_selection_is_neither_a_selection_nor_bound(self):
        live = sample()
        assert not isinstance(live, Selection) and not isinstance(live.stamp, BoundStamp)
        projection = live.projection()
        assert set(projection) == {"version", "capture", "query", "selected", "contributing", "absent", "unresolved"}
        assert projection["version"] == LIVE_SELECTION_VERSION == "science.live-selection.v1"
        assert projection["capture"] == {"world": WORLD, "coverage": [[ALPHA, STATE]]}
        assert live.identity() == v1.digest(LIVE_SELECTION_VERSION, projection)
        assert sample(stamp=CaptureStamp(WORLD, ((ALPHA, "b" * 64),))).identity() != live.identity()

    def test_complete_follows_the_selection_rule(self):
        assert sample().complete
        assert not sample(absent=(BETA,)).complete
        assert not sample(unresolved=(Unresolved("run:r", "produces", "dataset:x", "not-present", BETA),)).complete
        assert sample(unresolved=(Unresolved("run:r", "produces", "dataset:x", "unknown", None),)).complete


def datasets(*slugs):
    return tuple(stored.dataset_node(title=slug, resources=pinned(slug)) for slug in slugs)


def two_corpora(tmp_path, alpha=(), beta=()):
    roots = corpora(tmp_path, {ALPHA: (*datasets("d-a"), *alpha), BETA: (*datasets("d-b"), *beta)})
    return world_over(tmp_path, roots), roots


class TestEvaluation:
    def test_types_refuse(self, tmp_path):
        world, _roots = two_corpora(tmp_path)
        with pytest.raises(TypeError):
            evaluate_live_query(object(), DATASETS)  # type: ignore[arg-type]
        with pytest.raises(TypeError):
            evaluate_live_query(world, {"version": "science.view-query.v1", "clauses": []})  # type: ignore[arg-type]

    def test_a_never_published_world_selects_from_every_admitted_corpus(self, tmp_path):
        world, roots = two_corpora(tmp_path)
        live = evaluate_live_query(world, DATASETS)
        assert live.selected == tuple(sorted((dataset_ref("d-a"), dataset_ref("d-b"))))
        assert live.contributing == tuple(sorted((ALPHA, BETA))) and live.complete
        assert live.stamp.world_id == WORLD
        assert dict(live.stamp.coverage) == {c: registry.corpus_state_identity(r) for c, r in roots.items()}

    def test_a_retired_address_resolves_to_its_live_record(self, tmp_path):
        retired = datasets("d-old")[0].id
        (renamed,) = datasets("d-new")
        renamed.deprecated_ids = [retired]
        world, _roots = two_corpora(tmp_path, alpha=(renamed,))
        assert evaluate_live_query(world, query([{"addresses": [retired]}])).selected == (renamed.id,)

    def test_a_world_with_nothing_admitted_selects_nothing_and_is_complete(self, tmp_path):
        live = evaluate_live_query(world_over(tmp_path, {}), DATASETS)
        assert (live.selected, live.stamp.coverage, live.absent, live.complete) == ((), (), (), True)

    def test_a_corpus_holding_only_coordination_records_is_captured_and_contributes_nothing(self, tmp_path):
        roots = corpora(tmp_path, {ALPHA: (raw_coordination_node("project", PROJECT, "4" * 32),), BETA: datasets("d-b")})
        live = evaluate_live_query(world_over(tmp_path, roots), DATASETS)
        assert live.selected == (dataset_ref("d-b"),) and live.contributing == (BETA,)
        assert set(dict(live.stamp.coverage)) == {ALPHA, BETA}

    def test_a_configured_root_with_an_unreadable_manifest_refuses(self, tmp_path):
        roots = corpora(tmp_path, {ALPHA: datasets("d-a")})
        broken = tmp_path / "broken"
        broken.mkdir()
        (broken / "corpus.yaml").write_text("not: [a manifest\n", encoding="utf-8")
        world = world_over(tmp_path, roots, also_configured=(broken,))
        with pytest.raises(ResolutionRefused, match="cannot read"):
            evaluate_live_query(world, DATASETS)

    def test_an_unchanged_world_answers_identically_and_a_write_moves_only_its_corpus(self, tmp_path):
        world, roots = two_corpora(tmp_path)
        first = evaluate_live_query(world, DATASETS)
        assert evaluate_live_query(world, DATASETS).identity() == first.identity()
        (late,) = datasets("d-late")
        raw_write(roots[ALPHA], late)
        moved = evaluate_live_query(world, DATASETS)
        assert late.id in moved.selected
        assert dict(moved.stamp.coverage)[ALPHA] != dict(first.stamp.coverage)[ALPHA]
        assert dict(moved.stamp.coverage)[BETA] == dict(first.stamp.coverage)[BETA]
