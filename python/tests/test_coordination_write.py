from copy import deepcopy

import pytest
import yaml
from coordination_fixtures import (
    COORDINATION_DOCUMENT,
    coordination_profile,
    mounted_root,
    raw_add,
    raw_coordination_node,
)
from nodes.core.relations import Relation
from nodes.core.write_plan import DefaultExecutor

from beliefs import stored
from beliefs.contract import parse_base_contract
from beliefs.coordination import CoordinationAddress, CoordinationRefused
from beliefs.corpus import CoordinationResolver, CorpusWriter, corpus_check
from beliefs.errors import ContractMismatch

A, B, C, D = (character * 32 for character in "abcd")


def test_resolver_reopens_every_mount_and_is_order_inert(tmp_path, base_contract):
    profile = coordination_profile(base_contract)
    left = mounted_root(tmp_path / "left", profile)
    right = mounted_root(tmp_path / "right", profile)
    first = raw_coordination_node("project", A, C)
    second = raw_coordination_node("project", A, D)
    raw_add(left, first)
    forward = CoordinationResolver({left: profile, right: profile})
    assert forward.resolve(CoordinationAddress(A)) == first
    raw_add(right, second)
    refusal = CoordinationRefused("divergent-view", (C, D))
    assert forward.resolve(CoordinationAddress(A)) == refusal
    assert CoordinationResolver({right: profile, left: profile}).resolve(CoordinationAddress(A)) == refusal


def test_a_pinned_address_reads_an_immutable_superseded_revision(tmp_path, base_contract):
    profile = coordination_profile(base_contract)
    root = mounted_root(tmp_path, profile)
    old = raw_coordination_node("project", A, C)
    new = raw_coordination_node("project", A, D, supersedes=(old.id,))
    raw_add(root, old, new)
    resolver = CoordinationResolver({root: profile})
    assert resolver.resolve(CoordinationAddress(A)) == new
    assert resolver.resolve(CoordinationAddress(A, revision=C)) == old


def test_malformed_facets_are_reported_and_excluded_from_tips(tmp_path, base_contract):
    profile = coordination_profile(base_contract)
    root = mounted_root(tmp_path, profile)
    valid = raw_coordination_node("project", A, C)
    malformed = raw_coordination_node("project", A, D)
    malformed.facets[stored.COORDINATION_FACET]["project"] = "bad"
    raw_add(root, valid, malformed)
    assert CoordinationResolver({root: profile}).resolve(CoordinationAddress(A)) == valid
    findings = corpus_check(CorpusWriter(root, DefaultExecutor).read_view)
    assert [(finding.code, finding.ref) for finding in findings if finding.code.startswith("coordination-")] == [
        ("coordination-facet-malformed", malformed.id)
    ]


def test_a_raw_local_cycle_has_no_tip_and_has_an_audit_finding(tmp_path, base_contract):
    profile = coordination_profile(base_contract)
    root = mounted_root(tmp_path, profile)
    first = raw_coordination_node("project", A, C)
    second = raw_coordination_node("project", A, D)
    first.relations = [Relation(source=first.id, predicate=stored.SUPERSEDES, target=second.id)]
    second.relations = [Relation(source=second.id, predicate=stored.SUPERSEDES, target=first.id)]
    raw_add(root, first, second)
    assert CoordinationResolver({root: profile}).resolve(CoordinationAddress(A)) is None
    assert any(
        finding.code == "coordination-supersession-cycle"
        for finding in corpus_check(CorpusWriter(root, DefaultExecutor).read_view)
    )


def test_resolver_requires_the_mounted_base_and_activated_contracts(
    tmp_path, base_contract, base_contract_path
):
    profile = coordination_profile(base_contract)
    root = mounted_root(tmp_path, profile)

    changed_coordination = deepcopy(COORDINATION_DOCUMENT)
    changed_coordination["description"] = "A different coordination contract"
    wrong_coordination = coordination_profile(base_contract, document=changed_coordination)

    changed_base = yaml.safe_load(base_contract_path.read_text(encoding="utf-8"))
    changed_base["version"] += 1
    wrong_base = coordination_profile(parse_base_contract(changed_base, source="<changed-base>"))

    for supplied in (wrong_coordination, wrong_base):
        with pytest.raises(ContractMismatch):
            CoordinationResolver({root: supplied})
