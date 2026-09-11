"""M13 and M11 re-read against `claim_from_stored` (design §2.5)."""

from __future__ import annotations

import inspect
import subprocess
import sys
import textwrap

import pytest
from nodes.core.node import Node
from test_decode import ADULTS, COHORT_DATASET, EX, GENE, OTHER_GENE, OUTCOME
from test_decode import affects as _affects  # the wire-claim builder; a plain function there, not a fixture

from beliefs import decode, stored
from beliefs.claim import Claim
from beliefs.decode import claim_from_stored, decode_claim
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
    facet = {"operator": wire.operator, "args": list(wire.args), "qualifiers": {k: dict(v) for k, v in wire.qualifiers.items()}, "polarity": wire.polarity, "layer": wire.layer}
    return stored.proposition_node("p", title="p", claim=facet)


class TestM13Opacity:
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
        assert claim_identity(claim) == claim_identity(direct)   # π_claim accepts it; the brand chain is intact

    def test_the_wire_type_stays_confined(self):
        # The existing scan in test_decode.py asserts no signature outside decode mentions WireClaim;
        # this re-read asserts the new function is inside decode.py and the scan still passes.
        assert claim_from_stored.__module__ == "beliefs.decode"


class TestM11FunctionOfItsArguments:
    def test_identical_across_processes(self, profile, readable, affects, base_contract_path, testing_contract_path):
        claim, receipt = claim_from_stored(stored_proposition(affects()), profile=profile, snapshot=readable)
        wire = affects()
        script = textwrap.dedent(f"""
            from pathlib import Path
            from beliefs.contract import load_base_contract, load_domain_contract
            from beliefs.contract.domain import VocabularyBinding
            from beliefs.profile import compile_profile
            from beliefs.decode import claim_from_stored
            from beliefs.projection import claim_identity
            from beliefs.resolution import build_snapshot
            from beliefs import stored

            base = load_base_contract(Path({str(base_contract_path)!r}))
            testing = load_domain_contract(Path({str(testing_contract_path)!r}), base=base, predecessor=None)
            profile = compile_profile(base, [testing])
            EX = VocabularyBinding(namespace="EX", release="2026-01-01", dataset_identity=None)
            COHORT = VocabularyBinding(namespace=None, release=None, dataset_identity="0" * 64)
            snapshot = build_snapshot(readable={{EX: [{GENE!r}, {OTHER_GENE!r}, {OUTCOME!r}], COHORT: [{ADULTS!r}]}})
            node = stored.proposition_node(
                "p",
                title="p",
                claim={{
                    "operator": {wire.operator!r},
                    "args": [{wire.args[0]!r}, {wire.args[1]!r}],
                    "qualifiers": {{}},
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
            lambda f: {k: v for k, v in f.items() if k != "polarity"},        # missing field
            lambda f: {**f, "extra": "x"},                                   # extra field
            lambda f: {**f, "args": "not-a-list"},                          # malformed field
            lambda f: {**f, "qualifiers": {"dim": {"quantifier": "all"}}},  # malformed qualifier body
        ],
    )
    def test_refuses_before_delegation_and_mints_nothing(self, profile, readable, affects, monkeypatch, mutate):
        node = stored_proposition(affects())
        bad = node.model_copy(update={"facets": {stored.PROPOSITION_FACET: mutate(node.facets[stored.PROPOSITION_FACET])}})
        monkeypatch.setattr(decode, "decode_claim", lambda *a, **k: pytest.fail("delegated on malformed input"))
        with pytest.raises(MalformedWireClaim):
            claim_from_stored(bad, profile=profile, snapshot=readable)

    def test_a_wrong_kind_refuses_before_delegation(self, profile, readable, monkeypatch):
        monkeypatch.setattr(decode, "decode_claim", lambda *a, **k: pytest.fail("delegated"))
        with pytest.raises(MalformedWireClaim):
            claim_from_stored(stored.source_node(title="s", identifiers={"doi": "10.1234/x"}), profile=profile, snapshot=readable)

    def test_no_key_error_or_attribute_error_escapes(self, profile, readable, affects):
        node = stored_proposition(affects()).model_copy(update={"facets": {}})
        with pytest.raises(MalformedWireClaim):
            claim_from_stored(node, profile=profile, snapshot=readable)
