import pytest
from coordination_fixtures import coordination_profile, mounted_root, raw_add, raw_coordination_node
from nodes.core.relations import Relation

from beliefs import stored
from beliefs.coordination import CoordinationAddress, CoordinationRefused
from beliefs.corpus import CoordinationResolver
from beliefs.errors import MalformedRecord

A, B, C, D, E, F = (character * 32 for character in "abcdef")
P, Q, R = (character * 32 for character in "123")


def test_standing_lists_every_address_of_a_kind_in_address_order(tmp_path, base_contract):
    profile = coordination_profile(base_contract)
    root = mounted_root(tmp_path, profile)
    second = raw_coordination_node("project", B, D)
    first = raw_coordination_node("project", A, C)
    task = raw_coordination_node("task", A, E, local=F)
    raw_add(root, second, first, task)
    resolver = CoordinationResolver({root: profile})
    standing = resolver.standing("project")
    assert list(standing.items()) == [(CoordinationAddress(A), first), (CoordinationAddress(B), second)]
    assert dict(resolver.standing("task")) == {CoordinationAddress(A, F): task}
    assert dict(resolver.standing("question")) == {}


def test_standing_resolves_each_address_to_its_tip(tmp_path, base_contract):
    profile = coordination_profile(base_contract)
    root = mounted_root(tmp_path, profile)
    old = raw_coordination_node("project", A, C)
    new = raw_coordination_node("project", A, D, supersedes=(old.id,))
    raw_add(root, old, new)
    assert dict(CoordinationResolver({root: profile}).standing("project")) == {CoordinationAddress(A): new}


def test_standing_within_one_project_narrows_subordinates(tmp_path, base_contract):
    profile = coordination_profile(base_contract)
    root = mounted_root(tmp_path, profile)
    ours = raw_coordination_node("task", A, P, local=Q)
    theirs = raw_coordination_node("task", B, R, local=C)
    raw_add(root, raw_coordination_node("project", A, D), raw_coordination_node("project", B, E), ours, theirs)
    resolver = CoordinationResolver({root: profile})
    assert dict(resolver.standing("task", project=CoordinationAddress(A))) == {CoordinationAddress(A, Q): ours}
    assert dict(resolver.standing("task")) == {CoordinationAddress(A, Q): ours, CoordinationAddress(B, C): theirs}
    assert dict(resolver.standing("project", project=CoordinationAddress(B))) == {
        CoordinationAddress(B): raw_coordination_node("project", B, E)
    }


def test_a_divergent_address_is_listed_with_its_tips_across_mounts(tmp_path, base_contract):
    profile = coordination_profile(base_contract)
    left = mounted_root(tmp_path / "left", profile)
    right = mounted_root(tmp_path / "right", profile)
    raw_add(left, raw_coordination_node("project", A, C))
    raw_add(right, raw_coordination_node("project", A, D))
    assert dict(CoordinationResolver({left: profile, right: profile}).standing("project")) == {
        CoordinationAddress(A): CoordinationRefused("divergent-view", (C, D))
    }
    assert dict(CoordinationResolver({left: profile}).standing("project")) == {
        CoordinationAddress(A): raw_coordination_node("project", A, C)
    }


def test_standing_agrees_with_resolve_including_an_address_without_a_tip(tmp_path, base_contract):
    profile = coordination_profile(base_contract)
    root = mounted_root(tmp_path, profile)
    first = raw_coordination_node("project", A, C)
    second = raw_coordination_node("project", A, D)
    first.relations = [Relation(source=first.id, predicate=stored.SUPERSEDES, target=second.id)]
    second.relations = [Relation(source=second.id, predicate=stored.SUPERSEDES, target=first.id)]
    raw_add(root, first, second, raw_coordination_node("project", B, E))
    resolver = CoordinationResolver({root: profile})
    standing = resolver.standing("project")
    assert standing[CoordinationAddress(A)] is None
    assert {address: resolver.resolve(address) for address in standing} == dict(standing)


def test_an_address_whose_revisions_disagree_on_kind_is_malformed(tmp_path, base_contract):
    profile = coordination_profile(base_contract)
    root = mounted_root(tmp_path, profile)
    raw_add(root, raw_coordination_node("project", A, C), raw_coordination_node("question", A, D))
    with pytest.raises(MalformedRecord, match=f"coord:{A}"):
        CoordinationResolver({root: profile}).standing("project")


@pytest.mark.parametrize(
    ("kind", "project"),
    [
        ("claim", None),
        ("project", CoordinationAddress(A, B)),
        ("task", CoordinationAddress(A, revision=B)),
    ],
)
def test_standing_refuses_a_non_coordination_kind_or_a_non_project_scope(tmp_path, base_contract, kind, project):
    profile = coordination_profile(base_contract)
    resolver = CoordinationResolver({mounted_root(tmp_path, profile): profile})
    with pytest.raises(ValueError):
        resolver.standing(kind, project=project)
