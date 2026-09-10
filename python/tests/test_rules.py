"""The reference rules the kernel ships, keyed by rule identity (session-routes design §5)."""

from __future__ import annotations

import pytest
from fixtures_cut3 import spec_draft

from beliefs.errors import UnfreezableSpec
from beliefs.identity import v1
from beliefs.recipe import ResultManifest
from beliefs.replay import CONTENT_EQUALITY
from beliefs.rules import (
    CONTENT_IDENTITY_RULE,
    OUTCOME_FILE,
    OUTCOME_FILE_RULE,
    OUTCOME_FILE_V1,
    REFERENCE_RULES,
    interpret_outcome_file,
    outcome_digest,
)
from beliefs.spec import (
    BITWISE_EQUIVALENCE_RULES,
    SPEC_DOMAIN,
    StochasticUnseeded,
    freeze,
    frozen_projection,
    implementation_conforms,
    restore,
)


def test_every_reference_rule_conforms_and_carries_a_kernel_identity():
    assert set(REFERENCE_RULES) == {OUTCOME_FILE_RULE, CONTENT_IDENTITY_RULE}
    for identity, impl in REFERENCE_RULES.items():
        assert identity.startswith("beliefs/") and identity.endswith("/v1")
        assert impl.fixtures, identity
        assert implementation_conforms(impl), identity


def test_the_outcome_rule_maps_each_canonical_line_and_refuses_the_rest():
    for outcome in ("supported", "refuted", "inconclusive"):
        assert interpret_outcome_file(ResultManifest(outputs=((OUTCOME_FILE, outcome_digest(outcome)),))) == {
            "outcome": outcome
        }
    with pytest.raises(ValueError, match="canonical"):
        interpret_outcome_file(ResultManifest(outputs=((OUTCOME_FILE, "sha256:" + "0" * 64),)))
    with pytest.raises(ValueError, match=OUTCOME_FILE):
        interpret_outcome_file(ResultManifest(outputs=(("outputs/stats.tsv", "sha256:" + "0" * 64),)))
    assert OUTCOME_FILE_V1.identity == "impl-outcome-file-1"


def test_content_equality_keeps_its_identity_and_is_no_longer_vacuous():
    assert REFERENCE_RULES[CONTENT_IDENTITY_RULE] is CONTENT_EQUALITY
    assert CONTENT_EQUALITY.identity == "impl-eq-1"
    assert len(CONTENT_EQUALITY.fixtures) == 2
    assert implementation_conforms(CONTENT_EQUALITY)


def _kernel_draft(**overrides):
    return spec_draft(
        interpretation_rule=OUTCOME_FILE_RULE,
        equivalence_rule=CONTENT_IDENTITY_RULE,
        **overrides,
    )


def test_freeze_binds_the_reference_rules():
    frozen = freeze(_kernel_draft(), held_rules=REFERENCE_RULES)
    assert frozen.rule_bindings == (
        (CONTENT_IDENTITY_RULE, "impl-eq-1"),
        (OUTCOME_FILE_RULE, "impl-outcome-file-1"),
    )


def test_the_kernel_equality_identity_is_bitwise_at_freeze():
    assert CONTENT_IDENTITY_RULE in BITWISE_EQUIVALENCE_RULES
    with pytest.raises(UnfreezableSpec):
        freeze(
            _kernel_draft(nondeterminism=StochasticUnseeded(rationale="honest")),
            held_rules=REFERENCE_RULES,
        )


def test_the_kernel_equality_identity_is_bitwise_at_restore():
    mapping = frozen_projection(freeze(_kernel_draft(), held_rules=REFERENCE_RULES))
    mapping["nondeterminism"] = StochasticUnseeded(rationale="honest").projection()
    identity = v1.digest(SPEC_DOMAIN, mapping)
    with pytest.raises(UnfreezableSpec):
        restore(identity, v1.encode(mapping))
