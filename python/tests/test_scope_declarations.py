"""Declared scope relations: grammar, admission, succession and register coverage.

Scope containment design §§4, 5 and 8; acceptance cases C7, C8, C15 and C16.
Graph semantics (C1–C5, C9–C14) are tested in test_scope_graph.py.
"""

from __future__ import annotations

import copy
import dataclasses
import hashlib
from pathlib import Path

import pytest
from conftest import REPO_ROOT
from scope_fixtures import (
    RULE_A,
    VECTOR,
    apply_change,
    endpoint_contract,
    endpoint_document,
    scope_contract,
    scope_document,
    scope_profile,
)

from beliefs import errors
from beliefs.contract.base import parse_base_contract
from beliefs.contract.document import load_document
from beliefs.contract.domain import DECLARATION_FAMILIES
from beliefs.contract.scope import CompiledScopeRelation, RuleScopeEndpoint, ScopeRelationDecl, TermScopeEndpoint
from beliefs.corpus import _registers_report
from beliefs.profile import _shipped_domain_history, compile_profile
from beliefs.register import (
    ENTRY_KINDS,
    REGISTER_DOMAIN,
    AssumptionsRegister,
    RegisterEntry,
    register_entry_keys,
    register_identity,
)

SCOPE_KEYS = sorted(VECTOR["schema"])


def _scope_vocabulary(contract) -> dict[str, object]:
    return {key: value for key, value in contract.claim_vocabulary().items() if key.startswith("scope-relation:")}


def _compiled(profile) -> dict[str, object]:
    return {term: relation.schema_projection() for term, relation in profile.scope_relations.items()}


def test_scope_relation_schema_and_identity(base_contract):
    contract = scope_contract(base_contract)
    assert contract.content_identity == VECTOR["identity"]
    assert _scope_vocabulary(contract) == VECTOR["schema"]
    for key, expected_semantic_fields in VECTOR["schema"].items():
        declared = contract.scope_relations[key.removeprefix("scope-relation:")]
        assert type(declared) is ScopeRelationDecl
        assert declared.schema_projection() == expected_semantic_fields
        assert declared.retired is False

    profile = scope_profile(base_contract, contract)
    assert _compiled(profile) == VECTOR["compiled"]
    for term, relation in profile.scope_relations.items():
        assert type(relation) is CompiledScopeRelation
        assert relation.term == term
        assert relation.contract == "scope-relations"
    narrower = profile.scope_relations["scope-relations/special-within-general"].declaration
    assert narrower.left == TermScopeEndpoint("testing/stage", "EX:special")
    rule = profile.scope_relations["scope-relations/restricted-within-case"].declaration
    assert rule.left == RuleScopeEndpoint(RULE_A, ("EX:restricted",))
    with pytest.raises(dataclasses.FrozenInstanceError):
        narrower.left.term = "EX:other"  # type: ignore[misc]
    with pytest.raises(errors.MalformedContract):
        RuleScopeEndpoint(RULE_A, ("EX:a", "EX:b"))
    with pytest.raises(errors.MalformedContract):
        RuleScopeEndpoint(RULE_A, ["EX:a"])  # type: ignore[arg-type]

    # A local declaration is qualified at compile; retirement stays outside the
    # immutable semantic projection and inside the compiled one.
    local = endpoint_document()
    for change in VECTOR["local"]["changes"]:
        apply_change(local, change)
    local_contract = endpoint_contract(base_contract, local)
    assert _scope_vocabulary(local_contract) == VECTOR["local"]["schema"]
    assert local_contract.retired_identifiers() == {"scope-relation:early-within-late"}
    assert _compiled(compile_profile(base_contract, [local_contract])) == VECTOR["local"]["compiled"]

    # Domain identity is the document's; the base cutover does not move it, and a
    # contract without the optional table keeps its bytes and identity.
    assert endpoint_contract(base_contract).content_identity == (
        "c7b1edf87238636685aea10852029a0320e373a1ca8b5de7388d34d50b6008e0"
    )
    assert endpoint_contract(base_contract).scope_relations == {}

    # The base owns the closed relation vocabulary, and the profile projects it.
    assert base_contract.version == 6
    assert base_contract.scope_grammar.version == 1
    assert base_contract.scope_grammar.relations == ("equal", "narrower")
    bare = compile_profile(base_contract, [endpoint_contract(base_contract)])
    assert bare.projection()["scope_grammar"] == {"version": 1, "relations": ["equal", "narrower"]}
    assert bare.projection()["scope_relations"] == {}
    assert profile.projection()["scope_relations"] == VECTOR["compiled"]
    assert profile.compiled_identity != bare.compiled_identity
    assert profile.activated_contracts["scope-relations"] == VECTOR["identity"]

    assert register_entry_keys(contract) == {
        "scope-relation:scope-relations/" + key.removeprefix("scope-relation:") for key in SCOPE_KEYS
    }


@pytest.mark.parametrize("case", VECTOR["parse_refusals"], ids=lambda case: case["name"])
def test_closed_scope_declaration_fields(base_contract, case):
    document = scope_document()
    apply_change(document, case)
    with pytest.raises(getattr(errors, case["outcome"])):
        scope_contract(base_contract, document)


@pytest.mark.parametrize("case", VECTOR["compile_refusals"], ids=lambda case: case["name"])
def test_scope_declarations_refuse_at_compile(base_contract, case):
    document = scope_document()
    apply_change(document, case)
    contract = scope_contract(base_contract, document)
    with pytest.raises(getattr(errors, case["outcome"])):
        scope_profile(base_contract, contract)


def test_union_dimensions_admit_leaf_endpoints(base_contract):
    document = endpoint_document()
    document["dimensions"]["stages"] = {
        "restriction_sort": "stage",
        "restriction": {"form": "union", "of": {"form": "term", "sort": "stage"}},
        "placement": "applicability",
        "applies_to": ["affects"],
    }
    document["scope_relations"] = {
        "a-b": {
            "dimension": "stages",
            "relation": "equal",
            "left": {"sort": "stage", "term": "EX:a"},
            "right": {"sort": "stage", "term": "EX:b"},
        }
    }
    profile = compile_profile(base_contract, [endpoint_contract(base_contract, document)])
    assert profile.scope_relations["testing/a-b"].declaration.dimension == "testing/stages"


@pytest.mark.parametrize(
    ("mutate", "match"),
    [
        (lambda grammar: grammar.update(relations=["equal", "narrower", "within"]), "scope_grammar"),
        (lambda grammar: grammar.update(relations=["equal"]), "scope_grammar"),
        (lambda grammar: grammar.update(version=2), "scope_grammar"),
        (lambda grammar: grammar.update(extra=True), "scope_grammar"),
    ],
)
def test_the_base_scope_grammar_is_closed(base_contract_path, mutate, match):
    document = load_document(base_contract_path, source="base")
    assert isinstance(document, dict)
    mutate(document["scope_grammar"])
    with pytest.raises(errors.MalformedContract, match=match):
        parse_base_contract(document, source="base")


def test_relation_succession_and_retirement(base_contract):
    genesis = scope_contract(base_contract)

    def successor(edit) -> dict:
        document = scope_document()
        document["version"] = 2
        document["lineage"] = {"successor": genesis.content_identity}
        edit(document["scope_relations"])
        return document

    def refused(edit) -> None:
        with pytest.raises(errors.SuccessionViolation):
            scope_contract(base_contract, successor(edit), predecessor=genesis)

    # Same name, different meaning: dimension, relation or either endpoint.
    refused(lambda table: table["special-within-general"].update(relation="equal"))
    refused(lambda table: table["special-within-general"].update(dimension="testing/case-status"))
    refused(lambda table: table["special-within-general"]["left"].update(term="EX:other"))
    refused(lambda table: table["restricted-within-case"]["right"].update(classes=["EX:other"]))
    refused(lambda table: table.pop("special-within-general"))

    # Editorial prose and retirement are not redefinition.
    editorial = scope_contract(
        base_contract,
        successor(lambda table: table["special-within-general"].update(description="Clarified prose.")),
        predecessor=genesis,
    )
    assert _scope_vocabulary(editorial) == _scope_vocabulary(genesis)

    def correct(table) -> None:
        table["special-within-general"]["retired"] = True
        table["special-within-general-corrected"] = {
            "dimension": "testing/stage",
            "relation": "equal",
            "left": {"sort": "testing/stage", "term": "EX:special"},
            "right": {"sort": "testing/stage", "term": "EX:general"},
        }

    retired = scope_contract(base_contract, successor(correct), predecessor=genesis)
    assert retired.retired_identifiers() == {"scope-relation:special-within-general"}
    assert (
        _scope_vocabulary(retired)["scope-relation:special-within-general"]
        == (VECTOR["schema"]["scope-relation:special-within-general"])
    )
    before, after = scope_profile(base_contract, genesis), scope_profile(base_contract, retired)
    assert after.scope_relations["scope-relations/special-within-general"].schema_projection()["retired"] is True
    assert after.scope_relations["scope-relations/special-within-general-corrected"].declaration.relation == "equal"
    assert after.compiled_identity != before.compiled_identity
    # A retired relation stays register-addressable.
    assert "scope-relation:scope-relations/special-within-general" in register_entry_keys(retired)

    # Retirement is one-way.
    unretired = copy.deepcopy(successor(correct))
    unretired["version"] = 3
    unretired["lineage"] = {"successor": retired.content_identity}
    del unretired["scope_relations"]["special-within-general"]["retired"]
    with pytest.raises(errors.SuccessionViolation, match="un-retires"):
        scope_contract(base_contract, unretired, predecessor=retired)


PRE_CHANGE_PINS = {
    # namespace, history directory → contract identity, register identity, DOMAIN.yaml sha256, REGISTER.json sha256.
    # Recorded at beliefs d7c1b6c before the base v6 edit.
    ("general", "history/cd89bb6dbf4d28a13b04ca89ddd35d9a4da83bace06e8265ee60048fd0dec48f"): (
        "cd89bb6dbf4d28a13b04ca89ddd35d9a4da83bace06e8265ee60048fd0dec48f",
        "assumptions-register:02642579cb0fe2330553586e4c22d56f76a227e14b0d2fe849c6917992c3dbf9",
        "d5e7ec6c792d12d9afb08cdc58f7ce15f8512d09f525769e6ee75369841ac6a7",
        "96946aaf8ee11ede7ecddbafd27348600dce9ecac35a236342389c1807d12c24",
    ),
    ("general", ""): (
        "e74a497975e4a536f1bcbef26de73558d8a528276f4754082c6dd2d399f447ee",
        "assumptions-register:6939b589ff96806160232b13cba8b32019c7fc80caba0b4b06b9e7d676c98095",
        "53f9036e01080d007db4f20db9b81acecf78548512b849b81a5b340d8240b05d",
        "dbf7a185d89d202304d8944971007c8b9dd3b82ed86393946b9fbab9bae46f79",
    ),
    ("biology", ""): (
        "05e6f4fd06de8112d8f13d235c0793b6767404208cbf4210b7b9b24fc1840aca",
        "assumptions-register:f81b9ad496b745d850a872260f3f691020ab5ab9e3eb2b64758aeaf5dd1cfb67",
        "11308699feb1d7f402b81b6ff1451806490b41ac71df9100658d74bbad85616c",
        "bf8d07f7367b82fbbb037116111c1fdb6fcac88146ca7e4a0aab009a3b607f27",
    ),
    ("si-brochure", ""): (
        "79d06b3be2148612502eac3826ae7f88f520a16f46f666c986a053dadd9ff788",
        "assumptions-register:d08a4d0e77fb5ca1239a197806fe49e73c91f324ca8c0c57ae726692ae911660",
        "0ed3aa32e19fdf72881bd46b38f1b4b59f08c62c4da6a62f53d9be0dede7111a",
        "6be65c0d5713934a821fd32e8018a8368d1f2f9678980d9348fac482efbdbde3",
    ),
}
PRE_CHANGE_INVENTORY_SHA256 = "d38916d218ebe19f7a0df691df23835445ef495aa556edbabb1d0cd01cc35405"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_existing_register_pins_unchanged(base_contract):
    from test_shipped_contract_checks import _load_checker

    assert REGISTER_DOMAIN == "science.assumptions-register.v2"
    assert len(ENTRY_KINDS) == 22
    assert ENTRY_KINDS[-1] == "scope-relation"
    assert DECLARATION_FAMILIES[-1] == ("scope-relation", "scope_relations")

    observed = {}
    for namespace in ("general", "biology", "si-brochure"):
        for revision in _shipped_domain_history(namespace):
            directory = REPO_ROOT / "domains" / namespace / revision.directory
            observed[namespace, revision.directory] = (
                revision.contract.content_identity,
                register_identity(revision.register),
                _sha256(directory / "DOMAIN.yaml"),
                _sha256(directory / "REGISTER.json"),
            )
    assert observed == PRE_CHANGE_PINS
    assert _sha256(REPO_ROOT / "contracts/source-ownership/INVENTORY.json") == PRE_CHANGE_INVENTORY_SHA256
    checker = _load_checker()
    assert checker.SOURCE_INVENTORY_SHA256 == PRE_CHANGE_INVENTORY_SHA256
    assert checker.check(REPO_ROOT) == []

    # A register describing a relation-owning contract covers the new family
    # under register v2, with the design §4 field mapping, and audits cleanly.
    contract = scope_contract(base_contract)
    profile = scope_profile(base_contract, contract)
    entry = RegisterEntry(
        "Endpoint definitions and universe; same case and occasion; unclassified cases excluded.",
        "Proper containment; definitional counterexample establishing properness; defining source revision.",
        "No empirical validation, imported ontology closure, sibling disjointness or wider inference.",
        status="provisional",
    )
    covered = AssumptionsRegister(
        describes=f"scope-relations:{contract.content_identity}",
        previous=None,
        entries=dict.fromkeys(register_entry_keys(contract), entry),
    )
    identity = register_identity(covered)
    pins = {"testing": profile.activated_contracts["testing"], "scope-relations": contract.content_identity}
    findings = _registers_report({identity: covered}, pins, profile)
    assert not [f for f in findings if f.code == "register-entry-unknown"]
    stray = AssumptionsRegister(
        describes=covered.describes,
        previous=None,
        entries={"scope-relation:scope-relations/undeclared": entry},
    )
    unknown = [
        f.detail
        for f in _registers_report({register_identity(stray): stray}, pins, profile)
        if f.code == "register-entry-unknown"
    ]
    assert unknown == ["scope-relation:scope-relations/undeclared"]
