"""Opacity and determinism re-read against `claim_from_stored`."""

from __future__ import annotations

import inspect
import subprocess
import sys
import textwrap

import pytest
from domain_facet_fixtures import EX, GENE, OTHER_GENE
from nodes.core.node import Node
from test_decode import ADULTS, COHORT, COHORT_DATASET, ENTITY, OUTCOME, OUTCOME_SORT, member, population, ref
from test_decode import affects as _affects  # the wire-claim builder; a plain function there, not a fixture

from beliefs import decode, stored
from beliefs.claim import Claim, Referent
from beliefs.decode import claim_from_stored, decode_claim, stored_claim_terms
from beliefs.errors import MalformedWireClaim
from beliefs.projection import claim_identity, project_claim
from beliefs.resolution import BindingCheckReceipt, build_snapshot

# `profile` and `readable` are copied from test_decode.py rather than imported directly: importing
# pytest fixture functions by name and also taking them as same-named test parameters (the brief's
# suppressed-unused-import approach) makes ruff flag every using test as F811, "redefinition of
# unused `profile`/`readable`" — it has no notion of pytest's fixture-injection semantics. Copied
# here verbatim (contracts and bindings are still read through the shared conftest.py fixtures
# `base_contract`/`testing_contract_path`, never redefined) so both files stay identical in effect.


@pytest.fixture()
def profile(base_contract, testing_contract_path):
    from beliefs.contract import load_domain_contract
    from beliefs.profile import compile_profile

    testing = load_domain_contract(testing_contract_path, base=base_contract, predecessor=None)
    return compile_profile(base_contract, [testing])


@pytest.fixture()
def readable():
    """Both vocabularies read, holding every term these tests bind."""
    return build_snapshot(readable={EX: [GENE, OTHER_GENE, OUTCOME], COHORT_DATASET: [ADULTS]})


@pytest.fixture()
def affects():
    """`test_decode.py`'s `affects` is a plain function, not a fixture; wrapped here so the
    tests below — which take it as a fixture, matching the brief — can call it as `affects()`."""
    return _affects


def stored_proposition(wire) -> Node:
    facet = {
        "operator": wire.operator,
        "roles": dict(wire.roles),
        "qualifiers": {k: dict(v) for k, v in wire.qualifiers.items()},
        "form": wire.form,
        "polarity": wire.polarity,
        "layer": wire.layer,
    }
    return stored.proposition_node("p", title="p", claim=facet)


class TestStoredClaimTerms:
    def test_reads_role_referents_and_qualifier_restrictions_without_a_profile(self, affects):
        # `some` is no kernel quantifier: the read types nothing, so it does not care.
        wire = affects(qualifiers=population(quantifier="some"))
        assert stored_claim_terms(stored_proposition(wire)) == (
            (Referent(sort=ENTITY, term=GENE), Referent(sort=OUTCOME_SORT, term=OUTCOME)),
            (Referent(sort=COHORT, term=ADULTS),),
        )

    @pytest.mark.parametrize(
        "mutate",
        [
            pytest.param(
                lambda w: {**w, "qualifiers": {"testing/population": {"restriction": ref(COHORT, ADULTS)}}},
                id="qualifier-body",
            ),
            pytest.param(lambda w: {**w, "roles": [ref(ENTITY, GENE)]}, id="roles-a-list"),
            pytest.param(lambda w: {**w, "roles": {"cause": [GENE]}}, id="terms-in-a-role"),
            pytest.param(lambda w: {**w, "roles": {"parties": [ref(ENTITY, GENE)]}}, id="member-without-coefficient"),
            pytest.param(lambda w: {**w, "roles": {"parties": [member(ENTITY, GENE, 0)]}}, id="coefficient-below-one"),
            pytest.param(lambda w: {**w, "roles": {"cause": ref(ENTITY, "")}}, id="an-empty-term"),
        ],
    )
    def test_refuses_a_malformed_facet(self, affects, mutate):
        node = stored_proposition(affects())
        bad = node.model_copy(
            update={"facets": {stored.PROPOSITION_FACET: mutate(node.facets[stored.PROPOSITION_FACET])}}
        )
        with pytest.raises(MalformedWireClaim):
            stored_claim_terms(bad)


class TestOpacity:
    def test_the_signature_names_no_wire_type(self):
        signature = inspect.signature(claim_from_stored)
        assert "WireClaim" not in str(signature)
        assert signature.return_annotation != "WireClaim"

    def test_it_delegates_to_decode_claim(self, profile, readable, affects, monkeypatch):
        seen = []
        real = decode.decode_claim
        monkeypatch.setattr(decode, "decode_claim", lambda wire, **kw: seen.append(wire) or real(wire, **kw))
        claim, receipt = claim_from_stored(stored_proposition(affects()), profile=profile, snapshot=readable)
        assert len(seen) == 1 and isinstance(seen[0], decode.WireClaim)
        assert isinstance(claim, Claim) and isinstance(receipt, BindingCheckReceipt)

    def test_the_restored_claim_is_the_constructor_s_own(self, profile, readable, affects):
        claim, _ = claim_from_stored(stored_proposition(affects()), profile=profile, snapshot=readable)
        direct, _ = decode_claim(affects(), profile=profile, snapshot=readable)
        assert project_claim(claim) == project_claim(direct)
        assert claim_identity(claim) == claim_identity(direct)  # π_claim accepts it; the brand chain is intact

    def test_the_wire_type_stays_confined(self):
        # The existing scan in test_decode.py asserts no signature outside decode mentions WireClaim;
        # this re-read asserts the new function is inside decode.py and the scan still passes.
        assert claim_from_stored.__module__ == "beliefs.decode"


class TestFunctionOfItsArguments:
    def test_identical_across_processes(self, profile, readable, affects, base_contract_path, testing_contract_path):
        claim, receipt = claim_from_stored(stored_proposition(affects()), profile=profile, snapshot=readable)
        wire = affects()
        script = textwrap.dedent(f"""
            from pathlib import Path
            from beliefs.contract import load_base_contract, load_domain_contract
            from beliefs.contract.domain import DatasetBinding, ReleaseBinding
            from beliefs.profile import compile_profile
            from beliefs.decode import claim_from_stored
            from beliefs.projection import claim_identity
            from beliefs.resolution import build_snapshot
            from beliefs import stored

            base = load_base_contract(Path({str(base_contract_path)!r}))
            testing = load_domain_contract(Path({str(testing_contract_path)!r}), base=base, predecessor=None)
            profile = compile_profile(base, [testing])
            EX = ReleaseBinding(namespace="EX", release="2026-01-01")
            COHORT = DatasetBinding(dataset="dataset:" + "0" * 64)
            snapshot = build_snapshot(readable={{EX: [{GENE!r}, {OTHER_GENE!r}, {OUTCOME!r}], COHORT: [{ADULTS!r}]}})
            node = stored.proposition_node(
                "p",
                title="p",
                claim={{
                    "operator": {wire.operator!r},
                    "roles": {dict(wire.roles)!r},
                    "qualifiers": {{}},
                    "form": {wire.form!r},
                    "polarity": {wire.polarity!r},
                    "layer": {wire.layer!r},
                }},
            )
            decoded, emitted = claim_from_stored(node, profile=profile, snapshot=snapshot)
            print(claim_identity(decoded))
            print(emitted.identity())
        """)
        out = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            check=True,
            cwd=str(base_contract_path.parent),
        ).stdout.split()
        assert out == [claim_identity(claim), receipt.identity()]

    def test_availability_stays_a_parameter(self, profile, affects):
        with pytest.raises(MalformedWireClaim):
            claim_from_stored(stored_proposition(affects()), profile=profile, snapshot=None)  # type: ignore[arg-type]

    @pytest.mark.parametrize(
        "mutate",
        [
            lambda f: {k: v for k, v in f.items() if k != "polarity"},  # missing field
            lambda f: {**f, "extra": "x"},  # extra field
            lambda f: {**f, "roles": "not-a-map"},  # malformed field
            lambda f: {
                **f,
                "roles": {"cause": [ref(ENTITY, GENE)], "effect": ref(OUTCOME_SORT, OUTCOME)},
            },  # member shape
            lambda f: {**f, "qualifiers": {"dim": {"quantifier": "all"}}},  # malformed qualifier body
            lambda f: {**f, "qualifiers": {"dim": {"quantifier": "all", "restriction": ADULTS}}},  # v1 restriction
        ],
    )
    def test_refuses_before_delegation_and_mints_nothing(self, profile, readable, affects, monkeypatch, mutate):
        node = stored_proposition(affects())
        bad = node.model_copy(
            update={"facets": {stored.PROPOSITION_FACET: mutate(node.facets[stored.PROPOSITION_FACET])}}
        )
        monkeypatch.setattr(decode, "decode_claim", lambda *a, **k: pytest.fail("delegated on malformed input"))
        with pytest.raises(MalformedWireClaim):
            claim_from_stored(bad, profile=profile, snapshot=readable)

    def test_a_wrong_kind_refuses_before_delegation(self, profile, readable, monkeypatch):
        monkeypatch.setattr(decode, "decode_claim", lambda *a, **k: pytest.fail("delegated"))
        with pytest.raises(MalformedWireClaim):
            claim_from_stored(
                stored.source_node(title="s", identifiers={"doi": "10.1234/x"}), profile=profile, snapshot=readable
            )

    def test_no_key_error_or_attribute_error_escapes(self, profile, readable, affects):
        node = stored_proposition(affects()).model_copy(update={"facets": {}})
        with pytest.raises(MalformedWireClaim):
            claim_from_stored(node, profile=profile, snapshot=readable)
