import json

import pytest

from beliefs.errors import MalformedClosure, SeedClaimMalformed
from beliefs.recipe import job_key
from beliefs.seeds import bind, record_digest_of
from beliefs.spec import derive_seed

CONFIG = {
    "seed_roots": {"model-initialization": "11"},
    "seed_derivation_rule": "seed-derivation/v1",
}


def test_the_seed_is_the_v1_derivation_over_this_job_key(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    seed = bind(CONFIG)("fit", {"sample": "a"}, "model-initialization")
    assert seed == derive_seed(11, job_key("fit", (("sample", "a"),)), "model-initialization")


def test_two_instances_of_one_family_draw_different_seeds(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    seed = bind(CONFIG)
    assert seed("fit", {"sample": "a"}, "model-initialization") != seed(
        "fit", {"sample": "b"}, "model-initialization"
    )


def test_the_claim_is_written_under_a_digest_name_carrying_its_own_tuple(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    value = bind(CONFIG)("fit", {"sample": "a"}, "model-initialization")
    claims = sorted((tmp_path / ".seeds").glob("*.json"))
    assert len(claims) == 1
    record = json.loads(claims[0].read_text())
    assert record == {
        "rule": "fit",
        "wildcards": {"sample": "a"},
        "job_key": job_key("fit", (("sample", "a"),)),
        "stream": "model-initialization",
        "seed": value,
    }
    assert claims[0].stem == record_digest_of(record)


def test_two_streams_in_one_job_write_two_claims(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    seed = bind({"seed_roots": {"a": "11", "b": "12"}, "seed_derivation_rule": "seed-derivation/v1"})
    seed("fit", {}, "a")
    seed("fit", {}, "b")
    assert len(list((tmp_path / ".seeds").glob("*.json"))) == 2


def test_a_repeated_claim_fails_inside_the_job_rather_than_overwriting(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    seed = bind(CONFIG)
    seed("fit", {"sample": "a"}, "model-initialization")
    with pytest.raises(SeedClaimMalformed):
        seed("fit", {"sample": "a"}, "model-initialization")


def test_a_deterministic_config_has_no_roots_so_binding_refuses() -> None:
    with pytest.raises(MalformedClosure):
        bind({})


def test_a_non_integral_root_is_refused_rather_than_coerced() -> None:
    with pytest.raises(MalformedClosure):
        bind(
            {
                "seed_roots": {"model-initialization": "eleven"},
                "seed_derivation_rule": "seed-derivation/v1",
            }
        )
