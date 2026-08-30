from __future__ import annotations

import pytest

from beliefs.errors import WorldUninitialized
from beliefs.world import WorldConfig, _load_world_mirror, _world_mirror_bytes


def test_world_config_resolves_paths_without_deduplicating_corpus_roots(tmp_path):
    root = tmp_path / "a" / ".." / "world"
    corpus = tmp_path / "corpus"

    config = WorldConfig(root, "1" * 32, (corpus, corpus / "."))

    assert config.world_root == root.resolve()
    assert config.corpus_roots == (corpus.resolve(), corpus.resolve())


@pytest.mark.parametrize("corpus_roots", ["corpus", b"corpus"])
def test_world_config_requires_corpus_roots_tuple(tmp_path, corpus_roots):
    with pytest.raises(TypeError, match="corpus_roots"):
        WorldConfig(tmp_path, "1" * 32, corpus_roots)


@pytest.mark.parametrize("world_id", ["", "A" * 32, "a" * 31, "g" * 32])
def test_world_config_refuses_malformed_id(tmp_path, world_id):
    with pytest.raises(ValueError, match="world_id"):
        WorldConfig(tmp_path, world_id, ())


def test_world_mirror_loader_requires_a_valid_file(tmp_path):
    with pytest.raises(WorldUninitialized):
        _load_world_mirror(tmp_path)

    (tmp_path / "world.yaml").write_text("world_id: " + "2" * 32 + "\n", encoding="utf-8")

    assert _load_world_mirror(tmp_path) == "2" * 32
    assert _world_mirror_bytes("2" * 32) == ("world_id: " + "2" * 32 + "\n").encode()


@pytest.mark.parametrize("contents", ["{}\n", "world_id: nope\n", "world_id: " + "3" * 32 + "\nextra: x\n", "world_id: 3\nworld_id: 4\n"])
def test_world_mirror_loader_refuses_malformed_shape(tmp_path, contents):
    (tmp_path / "world.yaml").write_text(contents, encoding="utf-8")

    with pytest.raises(WorldUninitialized):
        _load_world_mirror(tmp_path)
