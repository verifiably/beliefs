"""Live view-query evaluation (live-query design §6.1 and the plan's Review Focus)."""

from __future__ import annotations

import pytest
from dataset_fixtures import dataset_ref
from test_world_build import ALPHA, BETA
from test_world_selection import query

from beliefs.identity import v1
from beliefs.world.live import LIVE_SELECTION_VERSION, CaptureStamp, LiveSelection
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
