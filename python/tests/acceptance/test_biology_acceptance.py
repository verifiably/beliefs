"""Cut 22's durable biology facet arm and TypeScript contract-scope half."""

from __future__ import annotations

import subprocess
from dataclasses import replace
from pathlib import Path

import pytest
from authority import FULL
from domain_facet_fixtures import PROPOSITION_REF, kwargs_for, profile_with, seed
from profiles import pins_for
from test_evaluation import GENE, OTHER_GENE
from test_session_acceptance import adopted

from beliefs.belief import Belief, Refused
from beliefs.errors import ContractMismatch
from beliefs.evaluation import evaluate_over, gather
from beliefs.root import open_corpus

REPO_ROOT = Path(__file__).resolve().parents[3]
BIOLOGY_CLAIM = {
    "operator": "biology/affects",
    "args": [GENE, OTHER_GENE],
    "qualifiers": {},
    "polarity": "positive",
    "layer": "causal",
}


def test_d6_the_facet_read_is_consulted_over_bytes_the_engine_committed(work_directory):
    profile = profile_with()
    root = adopted(work_directory, "corpus", pins=pins_for(profile), profile=profile)
    writer = open_corpus(root, authority=FULL, profile=profile)
    view = seed(writer, axis="rows", claim=BIOLOGY_CLAIM)
    result = evaluate_over(view, PROPOSITION_REF, **kwargs_for(view, profile))
    assert isinstance(result, Belief)
    reopened = open_corpus(root, authority=FULL, profile=profile).read_view
    gathered_kwargs = {k: v for k, v in kwargs_for(reopened, profile).items() if k != "availability"}
    inputs = gather(reopened, PROPOSITION_REF, **gathered_kwargs)
    assert inputs.claim is not None and inputs.claim.operator == "biology/affects"
    assert [row.key for row in inputs.observed_facets] == ["biology/gene-axis"]
    assert "biology" in dict(inputs.consulted)
    bumped = profile_with("fixture, bumped")
    with pytest.raises(ContractMismatch):
        open_corpus(root, authority=FULL, profile=bumped).add(reopened.get(PROPOSITION_REF))
    original_pins = kwargs_for(reopened, profile)["context"].pins
    mismatched = kwargs_for(reopened, bumped)
    mismatched["context"] = replace(mismatched["context"], pins=original_pins)
    refused = evaluate_over(reopened, PROPOSITION_REF, **mismatched)
    assert isinstance(refused, Refused) and refused.reason.startswith("profile-pin-mismatch: biology")


def test_b6_typescript_refuses_what_python_refuses():
    completed = subprocess.run(
        ["npx", "vitest", "run", "tests/contract-scope.test.ts"],
        cwd=REPO_ROOT / "ts",
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
