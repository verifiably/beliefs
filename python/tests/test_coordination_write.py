from copy import deepcopy

import pytest
import yaml
from coordination_fixtures import (
    COORDINATION_DOCUMENT,
    Recorder,
    content_for,
    coordination_contract,
    coordination_profile,
    mounted_root,
    raw_add,
    raw_coordination_node,
)
from nodes.core.relations import Relation
from nodes.core.write_plan import DefaultExecutor

from beliefs import stored
from beliefs.contract import parse_base_contract
from beliefs.coordination import CoordinationAddress, CoordinationRefused, coordination_revision
from beliefs.corpus import CoordinationResolver, CorpusWriter, corpus_check
from beliefs.errors import (
    ContractMismatch,
    CoordinationUnavailable,
    PredecessorMismatch,
    PredecessorNotStanding,
    ProjectNotResolvable,
    ValidationRefused,
)
from beliefs.profile import compile_profile

A, B, C, D = (character * 32 for character in "abcd")


def writer_with_resolver(root, profile):
    mounted_root(root, profile)
    resolver = CoordinationResolver({root: profile})
    return CorpusWriter(root, DefaultExecutor, coordination_resolver=resolver), resolver


def writer_with_document(root, base_contract, document):
    profile = coordination_profile(base_contract, document=document)
    return writer_with_resolver(root, profile)[0]


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


def test_project_and_subordinate_genesis_have_adapter_owned_shape(tmp_path, base_contract, monkeypatch):
    profile = coordination_profile(base_contract)
    writer, resolver = writer_with_resolver(tmp_path, profile)
    values = iter((A, B, C, D))
    monkeypatch.setattr("beliefs.corpus.secrets.token_hex", lambda _: next(values))
    project = writer.mint_coordination("project", content=content_for("project", name="Old name"))
    question = writer.mint_coordination(
        "question", project=CoordinationAddress(A), content=content_for("question")
    )
    assert (project.id, project.uid, project.relations) == (f"project:{A}.{B}", B, [])
    assert (question.id, question.uid, question.relations) == (f"question:{A}.{C}.{D}", D, [])
    assert set(project.facets) == {stored.COORDINATION_FACET}
    assert resolver.resolve(CoordinationAddress(A)) == project
    assert resolver.resolve(CoordinationAddress(A, C)) == question


def test_a_coordination_call_without_a_destination_mount_plans_nothing(tmp_path, base_contract):
    profile = coordination_profile(base_contract)
    mounted_root(tmp_path, profile, Recorder)
    Recorder.plans = []
    writer = CorpusWriter(tmp_path, Recorder, coordination_resolver=CoordinationResolver({}))
    with pytest.raises(CoordinationUnavailable):
        writer.mint_coordination("project", content=content_for("project"))
    assert Recorder.plans == []


def test_a_mounted_profile_without_a_coordination_contract_authorizes_nothing(tmp_path, base_contract):
    profile = compile_profile(base_contract, [])
    mounted_root(tmp_path, profile)
    writer = CorpusWriter(
        tmp_path,
        DefaultExecutor,
        coordination_resolver=CoordinationResolver({tmp_path: profile}),
    )
    with pytest.raises(ValidationRefused, match="not declared"):
        writer.mint_coordination("project", content=content_for("project"))


def test_a_subordinate_requires_one_resolvable_project(tmp_path, base_contract):
    profile = coordination_profile(base_contract)
    writer, _ = writer_with_resolver(tmp_path, profile)
    with pytest.raises(ProjectNotResolvable) as caught:
        writer.mint_coordination("task", project=CoordinationAddress(A), content=content_for("task"))
    assert caught.value.tips == ()


@pytest.mark.parametrize("mutation", ["missing", "extra", "bad-at", "bad-status", "world-depends", "coord-about"])
def test_content_is_closed_and_tier_checked(tmp_path, base_contract, mutation):
    profile = coordination_profile(base_contract)
    writer, _ = writer_with_resolver(tmp_path, profile)
    project = writer.mint_coordination("project", content=content_for("project"))
    project_address = coordination_revision(project).address
    kind = "task" if mutation in {"bad-status", "world-depends"} else "note"
    content = content_for(kind)
    if mutation == "missing":
        del content["author"]
    elif mutation == "extra":
        content["extra"] = True
    elif mutation == "bad-at":
        content["at"] = "today"
    elif mutation == "bad-status":
        content["status"] = "later"
    elif mutation == "world-depends":
        content["depends"] = ["dataset:x"]
    else:
        content["about"] = [str(project_address)]
    with pytest.raises(ValidationRefused):
        writer.mint_coordination(kind, project=project_address, content=content)


def test_w18c_a_query_kind_outside_the_contract_refuses(tmp_path, base_contract):
    document = deepcopy(COORDINATION_DOCUMENT)
    document["query_vocabulary"]["kinds"].remove("dataset")
    writer = writer_with_document(tmp_path, base_contract, document)
    query = {
        "version": "science.view-query.v1",
        "clauses": [{"all": [{"kinds": ["dataset"]}]}],
    }
    with pytest.raises(ValidationRefused, match="world kind"):
        writer.mint_coordination("project", content=content_for("project", query=query))


def test_w18d_a_query_relation_outside_the_contract_refuses(tmp_path, base_contract):
    document = deepcopy(COORDINATION_DOCUMENT)
    document["query_vocabulary"]["relations"].remove("reads")
    writer = writer_with_document(tmp_path, base_contract, document)
    query = {
        "version": "science.view-query.v1",
        "clauses": [
            {
                "all": [
                    {
                        "closure": {
                            "anchor": "dataset:not-held",
                            "predicates": ["reads"],
                            "direction": "out",
                        }
                    }
                ]
            }
        ],
    }
    with pytest.raises(ValidationRefused, match="relation"):
        writer.mint_coordination("project", content=content_for("project", query=query))


def test_query_syntax_is_refused_but_world_anchors_need_not_resolve(tmp_path, base_contract):
    writer = writer_with_document(tmp_path, base_contract, COORDINATION_DOCUMENT)
    with pytest.raises(ValidationRefused) as caught:
        writer.mint_coordination("project", content=content_for("project", query={"bad": True}))
    assert isinstance(caught.value.__cause__, ValueError)

    query = {
        "version": "science.view-query.v1",
        "clauses": [{"all": [{"addresses": ["dataset:not-held"]}]}],
    }
    assert writer.mint_coordination("project", content=content_for("project", query=query))


def test_an_earlier_contract_version_authorizes_nothing_added_later(tmp_path, base_contract):
    genesis = coordination_contract()
    document = deepcopy(COORDINATION_DOCUMENT)
    document.update(version=2, lineage={"successor": genesis.content_identity})
    document["kinds"]["publication"] = {
        "fields": ["name", "body", "author", "at"],
        "query_versions": [],
    }
    amended = coordination_contract(document, genesis)
    old_profile = compile_profile(base_contract, [], coordination=genesis)
    assert "publication" in compile_profile(base_contract, [], coordination=amended).coordination_kinds
    mounted_root(tmp_path, old_profile)
    writer = CorpusWriter(
        tmp_path,
        DefaultExecutor,
        coordination_resolver=CoordinationResolver({tmp_path: old_profile}),
    )
    project = writer.mint_coordination("project", content=content_for("project"))
    with pytest.raises(ValidationRefused, match="not declared"):
        writer.mint_coordination(
            "publication",
            project=coordination_revision(project).address,
            content=content_for("decision"),
        )


def test_revision_is_a_new_whole_record_and_the_old_revision_remains_pinnable(
    tmp_path, base_contract
):
    profile = coordination_profile(base_contract)
    writer, resolver = writer_with_resolver(tmp_path, profile)
    project = writer.mint_coordination("project", content=content_for("project", name="Old"))
    address = coordination_revision(project).address
    revised = writer.revise_coordination(
        "project",
        address,
        predecessors=(project.uid,),
        content=content_for("project", name="New"),
    )
    assert revised.uid != project.uid
    assert revised.relations[0].target == project.id
    assert resolver.resolve(address) == revised
    assert resolver.resolve(address.pinned(project.uid)) == project


def test_continuity_is_checked_before_standing(tmp_path, base_contract):
    profile = coordination_profile(base_contract)
    writer, _ = writer_with_resolver(tmp_path, profile)
    project = writer.mint_coordination("project", content=content_for("project"))
    project_address = coordination_revision(project).address
    task = writer.mint_coordination("task", project=project_address, content=content_for("task"))
    with pytest.raises(PredecessorMismatch):
        writer.revise_coordination(
            "project",
            project_address,
            predecessors=(task.uid,),
            content=content_for("project"),
        )


def test_a_superseded_predecessor_refuses_at_commit(tmp_path, base_contract):
    profile = coordination_profile(base_contract)
    writer, _ = writer_with_resolver(tmp_path, profile)
    first = writer.mint_coordination("project", content=content_for("project"))
    address = coordination_revision(first).address
    writer.revise_coordination(
        "project",
        address,
        predecessors=(first.uid,),
        content=content_for("project", name="second"),
    )
    with pytest.raises(PredecessorNotStanding):
        writer.revise_coordination(
            "project",
            address,
            predecessors=(first.uid,),
            content=content_for("project", name="stale"),
        )


def test_revision_requires_an_unpinned_address_and_distinct_nonempty_predecessors(
    tmp_path, base_contract
):
    profile = coordination_profile(base_contract)
    writer, _ = writer_with_resolver(tmp_path, profile)
    first = writer.mint_coordination("project", content=content_for("project"))
    address = coordination_revision(first).address
    cases = (
        (address.pinned(first.uid), (first.uid,)),
        (address, ()),
        (address, (first.uid, first.uid)),
    )
    for candidate, predecessors in cases:
        with pytest.raises(ValidationRefused):
            writer.revise_coordination(
                "project",
                candidate,
                predecessors=predecessors,
                content=content_for("project"),
            )


def test_two_roots_diverge_and_one_all_tip_revision_repairs_without_deleting_siblings(
    tmp_path, base_contract
):
    profile = coordination_profile(base_contract)
    left = mounted_root(tmp_path / "left", profile)
    right = mounted_root(tmp_path / "right", profile)
    left_writer = CorpusWriter(
        left,
        DefaultExecutor,
        coordination_resolver=CoordinationResolver({left: profile}),
    )
    project = left_writer.mint_coordination("project", content=content_for("project"))
    address = coordination_revision(project).address
    raw_add(right, project.model_copy(deep=True))
    left_tip = left_writer.revise_coordination(
        "project",
        address,
        predecessors=(project.uid,),
        content=content_for("project", name="left"),
    )
    right_writer = CorpusWriter(
        right,
        DefaultExecutor,
        coordination_resolver=CoordinationResolver({right: profile}),
    )
    right_tip = right_writer.revise_coordination(
        "project",
        address,
        predecessors=(project.uid,),
        content=content_for("project", name="right"),
    )
    resolver = CoordinationResolver({left: profile, right: profile})
    assert resolver.resolve(address) == CoordinationRefused(
        "divergent-view", (left_tip.uid, right_tip.uid)
    )
    repair_writer = CorpusWriter(left, DefaultExecutor, coordination_resolver=resolver)
    repair = repair_writer.revise_coordination(
        "project",
        address,
        predecessors=(right_tip.uid, left_tip.uid),
        content=content_for("project", name="repaired"),
    )
    assert resolver.resolve(address) == repair
    assert resolver.resolve(address.pinned(left_tip.uid)) == left_tip
    assert resolver.resolve(address.pinned(right_tip.uid)) == right_tip
    assert [relation.target for relation in repair.relations] == sorted((left_tip.id, right_tip.id))
    assert not any(
        finding.code == "supersession-target-missing"
        for finding in corpus_check(CorpusWriter(left, DefaultExecutor).read_view)
    )


def test_superseding_only_one_standing_sibling_is_lawful_and_remains_divergent(
    tmp_path, base_contract
):
    profile = coordination_profile(base_contract)
    left = mounted_root(tmp_path / "left", profile)
    right = mounted_root(tmp_path / "right", profile)
    first = raw_coordination_node("project", A, C)
    second = raw_coordination_node("project", A, D)
    raw_add(left, first)
    raw_add(right, second)
    resolver = CoordinationResolver({left: profile, right: profile})
    writer = CorpusWriter(left, DefaultExecutor, coordination_resolver=resolver)
    successor = writer.revise_coordination(
        "project",
        CoordinationAddress(A),
        predecessors=(first.uid,),
        content=content_for("project", name="partial"),
    )
    assert resolver.resolve(CoordinationAddress(A)) == CoordinationRefused(
        "divergent-view", (second.uid, successor.uid)
    )


def test_a_subordinate_revision_refuses_while_its_project_is_divergent(
    tmp_path, base_contract
):
    profile = coordination_profile(base_contract)
    left = mounted_root(tmp_path / "left", profile)
    right = mounted_root(tmp_path / "right", profile)
    first = raw_coordination_node("project", A, C)
    second = raw_coordination_node("project", A, D)
    raw_add(left, first)
    raw_add(right, second)
    resolver = CoordinationResolver({left: profile, right: profile})
    writer = CorpusWriter(left, DefaultExecutor, coordination_resolver=resolver)
    with pytest.raises(ProjectNotResolvable) as caught:
        writer.mint_coordination(
            "task", project=CoordinationAddress(A), content=content_for("task")
        )
    assert caught.value.tips == (C, D)
