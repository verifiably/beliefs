from __future__ import annotations

import json
import os
import subprocess
from decimal import Decimal

import pytest
import yaml
from fixtures_cut6 import BIOLOGY_ID, PINS, SCIENCE_ID, manifest_document
from nodes.core.corpus import Corpus
from nodes.core.errors import CollisionError, ValidationError
from nodes.core.frontmatter import node_to_markdown
from nodes.core.relations import Relation

from beliefs import stored
from beliefs.consulted import CorpusPins
from beliefs.errors import (
    CorpusStateMalformed,
    IdentityError,
    KeyCollision,
    ManifestMalformed,
    ManifestMissing,
)
from beliefs.identity import v1
from beliefs.world import CorpusManifest, ForkedFrom, _lift_json, corpus_state_identity, manifest_bytes

# The monkeypatched globals below are the implementation's own bindings, so the
# patches have to land on the implementation module rather than on the package
# facade that re-exports it.
from beliefs.world import registry as world


def _state_root(tmp_path, node):
    root = tmp_path / "corpus"
    root.mkdir()
    manifest = CorpusManifest(2, "1" * 32, PINS)
    (root / "corpus.yaml").write_bytes(manifest_bytes(manifest))
    Corpus(root).add(node)
    return root


def _replace(root, node):
    Corpus(root).add(node)
    return corpus_state_identity(root)


def _git(root, *args):
    return subprocess.run(
        ["git", *args], cwd=root, check=True, stdout=subprocess.PIPE, text=True
    ).stdout.strip()


def test_json_lift_tags_every_type_uniformly():
    value = json.loads(
        '{"n":null,"b":true,"i":1,"d":1.25,"s":"x","a":[null],"o":{"null":null}}',
        parse_int=Decimal,
        parse_float=Decimal,
    )
    assert _lift_json(value) == [
        "object",
        {
            "n": ["null"],
            "b": ["boolean", True],
            "i": ["number", Decimal(1)],
            "d": ["number", Decimal("1.25")],
            "s": ["string", "x"],
            "a": ["array", [["null"]]],
            "o": ["object", {"null": ["null"]}],
        },
    ]


def test_authored_null_marker_object_does_not_collide_with_null():
    assert v1.encode(_lift_json({"tag": "null"})) != v1.encode(_lift_json(None))


def test_lift_preserves_array_order():
    first = json.loads("[1,2]", parse_int=Decimal)
    second = json.loads("[2,1]", parse_int=Decimal)
    assert v1.encode(_lift_json(first)) != v1.encode(_lift_json(second))


def test_projection_numbers_reach_the_lift_as_decimals(tmp_path, monkeypatch):
    root = _state_root(tmp_path, stored.run_node("numbers", title="numbers", spec="analysis-spec:s1"))
    seen = []
    lift = _lift_json

    monkeypatch.setattr(world, "to_canonical_json", lambda _node: '{"n":1e+16,"m":1e-7}')

    def observe(value):
        seen.append(value)
        return lift(value)

    monkeypatch.setattr(world, "_lift_json", observe)
    corpus_state_identity(root)

    assert seen[0] == {"n": Decimal("1E+16"), "m": Decimal("1E-7")}
    assert all(not isinstance(value, float) for value in seen)


def test_node_content_and_produces_relations_move_state_while_semantic_identity_stands(tmp_path):
    run = stored.run_node("state", title="state", spec="analysis-spec:s1", produces=("dataset:a",))
    root = _state_root(tmp_path, run)
    semantic = stored.stored_semantic_hash(run)
    states = [corpus_state_identity(root)]
    body_edit = run.model_copy(update={"body": "changed"})
    states.append(_replace(root, body_edit))
    removed = body_edit.model_copy(update={"relations": []})
    states.append(_replace(root, removed))
    added = removed.model_copy(
        update={
            "relations": [Relation(source=run.id, predicate=stored.PRODUCES, target="dataset:b")]
        }
    )
    states.append(_replace(root, added))
    retargeted = added.model_copy(
        update={
            "relations": [Relation(source=run.id, predicate=stored.PRODUCES, target="dataset:c")]
        }
    )
    states.append(_replace(root, retargeted))
    facet_only = retargeted.model_copy(deep=True)
    facet_only.facets["review"] = {"member": "changed"}
    states.append(_replace(root, facet_only))
    assert len(set(states)) == len(states)
    assert {
        stored.stored_semantic_hash(node) for node in (run, body_edit, removed, added, retargeted, facet_only)
    } == {semantic}


def test_relation_reordering_moves_state(tmp_path):
    run = stored.run_node(
        "ordered",
        title="ordered",
        spec="analysis-spec:s1",
        produces=("dataset:a", "dataset:b"),
    )
    root = _state_root(tmp_path, run)
    before = corpus_state_identity(root)
    reversed_run = run.model_copy(update={"relations": list(reversed(run.relations))})
    assert _replace(root, reversed_run) != before


def test_filesystem_and_formatting_changes_are_inert(tmp_path):
    run = stored.run_node("inert", title="inert", spec="analysis-spec:s1")
    root = _state_root(tmp_path, run)
    (root / "corpus.yaml").write_bytes(
        manifest_bytes(
            CorpusManifest(
                2,
                "1" * 32,
                CorpusPins(
                    science_contract=SCIENCE_ID,
                    domains={"biology": BIOLOGY_ID, "chemistry": "chemistry:" + "c" * 64},
                ),
            )
        )
    )
    expected = corpus_state_identity(root)
    original = Corpus(root).store.path_for(run.id)
    renamed = root / "renamed" / original.name
    renamed.parent.mkdir()
    original.rename(renamed)
    (root / "editor.txt").write_text("one\n", encoding="utf-8")
    (root / "editor.txt").write_text("two\n\n", encoding="utf-8")
    parsed = yaml.safe_load((root / "corpus.yaml").read_text(encoding="utf-8"))
    assert list(parsed["profile"]["domains"]) == ["biology", "chemistry"]
    parsed["profile"]["domains"] = dict(reversed(tuple(parsed["profile"]["domains"].items())))
    assert list(parsed["profile"]["domains"]) == ["chemistry", "biology"]
    (root / "corpus.yaml").write_text(
        yaml.safe_dump(parsed, default_flow_style=True, sort_keys=False), encoding="utf-8"
    )
    for path in root.rglob("*"):
        os.utime(path, None)
    assert corpus_state_identity(root) == expected


def test_every_semantic_manifest_member_moves_state(tmp_path):
    run = stored.run_node("manifest", title="manifest", spec="analysis-spec:s1")
    root = _state_root(tmp_path, run)
    original = manifest_bytes(
        CorpusManifest(2, "1" * 32, PINS, ForkedFrom("2" * 32, "3" * 64))
    )
    (root / "corpus.yaml").write_bytes(original)
    states = [corpus_state_identity(root)]

    for old, new in (
        (SCIENCE_ID, "science:" + "c" * 64),
        (BIOLOGY_ID, "biology:" + "d" * 64),
        ("1" * 32, "4" * 32),
        ("3" * 64, "5" * 64),
    ):
        (root / "corpus.yaml").write_bytes(original.replace(old.encode(), new.encode(), 1))
        states.append(corpus_state_identity(root))

    assert len(set(states)) == 5


@pytest.mark.parametrize(
    "document",
    (
        manifest_document() + "extra: refused\n",
        manifest_document().replace("    biology:", "    biology: ignored\n    biology:"),
        manifest_document().replace(SCIENCE_ID, "science:" + "A" * 64),
    ),
)
def test_manifest_damage_refuses_before_digesting(tmp_path, monkeypatch, document):
    root = tmp_path / "corpus"
    root.mkdir()
    (root / "corpus.yaml").write_text(document, encoding="utf-8")
    monkeypatch.setattr(world.v1, "digest", lambda *_args: pytest.fail("digest was reached"))

    with pytest.raises(ManifestMalformed):
        corpus_state_identity(root)


def test_missing_manifest_stays_distinct(tmp_path):
    with pytest.raises(ManifestMissing):
        corpus_state_identity(tmp_path)


def test_git_is_not_an_identity_member(tmp_path):
    run = stored.run_node("git", title="git", spec="analysis-spec:s1")
    root = _state_root(tmp_path, run)
    before = corpus_state_identity(root)

    _git(root, "init", "-q")
    _git(
        root,
        "-c",
        "user.name=Science Tests",
        "-c",
        "user.email=science@example.invalid",
        "commit",
        "--allow-empty",
        "-qm",
        "initial",
    )
    first_head = _git(root, "rev-parse", "HEAD")
    changed = run.model_copy(update={"body": "changed"})
    after_change = _replace(root, changed)

    assert after_change != before
    assert _git(root, "rev-parse", "HEAD") == first_head

    _git(root, "add", "-A")
    _git(
        root,
        "-c",
        "user.name=Science Tests",
        "-c",
        "user.email=science@example.invalid",
        "commit",
        "-qm",
        "record corpus",
    )
    assert _git(root, "rev-parse", "HEAD") != first_head
    assert corpus_state_identity(root) == after_change


def test_malformed_node_wraps_the_nodes_failure(tmp_path):
    run = stored.run_node("malformed", title="malformed", spec="analysis-spec:s1")
    root = _state_root(tmp_path, run)
    Corpus(root).store.path_for(run.id).write_text("not a node", encoding="utf-8")

    with pytest.raises(CorpusStateMalformed) as refused:
        corpus_state_identity(root)

    assert isinstance(refused.value.__cause__, ValidationError)


def test_duplicate_uid_wraps_the_corpus_failure(tmp_path):
    first = stored.run_node("first", title="first", spec="analysis-spec:s1")
    root = _state_root(tmp_path, first)
    second = stored.run_node("second", title="second", spec="analysis-spec:s1").model_copy(
        update={"uid": first.uid}
    )
    path = Corpus(root).store.path_for(second.id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(node_to_markdown(second), encoding="utf-8")

    with pytest.raises(CorpusStateMalformed) as refused:
        corpus_state_identity(root)

    assert isinstance(refused.value.__cause__, CollisionError)


def test_projection_failure_is_the_exact_cause(tmp_path, monkeypatch):
    root = _state_root(tmp_path, stored.run_node("projection", title="projection", spec="analysis-spec:s1"))
    failure = ValidationError("projection failed")

    def fail(_node):
        raise failure

    monkeypatch.setattr(world, "to_canonical_json", fail)
    with pytest.raises(CorpusStateMalformed) as refused:
        corpus_state_identity(root)
    assert refused.value.__cause__ is failure


def test_json_failure_is_the_exact_cause(tmp_path, monkeypatch):
    root = _state_root(tmp_path, stored.run_node("json", title="json", spec="analysis-spec:s1"))
    monkeypatch.setattr(world, "to_canonical_json", lambda _node: "{")

    with pytest.raises(CorpusStateMalformed) as refused:
        corpus_state_identity(root)

    assert isinstance(refused.value.__cause__, json.JSONDecodeError)


def test_lift_failure_is_the_exact_cause(tmp_path, monkeypatch):
    root = _state_root(tmp_path, stored.run_node("lift", title="lift", spec="analysis-spec:s1"))
    failure = TypeError("lift failed")

    def fail(_value):
        raise failure

    monkeypatch.setattr(world, "_lift_json", fail)
    with pytest.raises(CorpusStateMalformed) as refused:
        corpus_state_identity(root)
    assert refused.value.__cause__ is failure


def test_node_content_identity_failure_is_the_exact_cause(tmp_path, monkeypatch):
    root = _state_root(tmp_path, stored.run_node("identity", title="identity", spec="analysis-spec:s1"))
    failure = IdentityError("identity failed")

    def fail(_domain, _value):
        raise failure

    monkeypatch.setattr(world.v1, "digest", fail)
    with pytest.raises(CorpusStateMalformed) as refused:
        corpus_state_identity(root)
    assert refused.value.__cause__ is failure


def test_nfc_key_collision_is_the_exact_cause(tmp_path, monkeypatch):
    root = _state_root(tmp_path, stored.run_node("collision", title="collision", spec="analysis-spec:s1"))
    monkeypatch.setattr(world, "to_canonical_json", lambda _node: '{"e\\u0301":1,"\\u00e9":2}')

    with pytest.raises(CorpusStateMalformed) as refused:
        corpus_state_identity(root)

    assert isinstance(refused.value.__cause__, KeyCollision)
