"""Unit tests for the mm30 reproduction driver under `tools/reproduction/`.

The driver is throwaway by declaration; these tests guard the bridges it
crosses between kernel spellings and the pure functions its steps rely on.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from beliefs.belief import Belief, NoBelief  # noqa: E402
from beliefs.policy import PolicyBinding  # noqa: E402
from reproduction import answers, findings  # noqa: E402


def test_a_finding_class_outside_the_four_is_refused(tmp_path, monkeypatch):
    monkeypatch.setattr(findings.paths, "FINDINGS", tmp_path / "f.jsonl")
    with pytest.raises(ValueError):
        findings.record(1, "oops", "reason")


def test_answer_payload_distinguishes_beliefs_by_value_and_digest():
    binding = PolicyBinding(rule="science.belief.v1", implementation="impl-1")
    one = answers.payload(Belief(1, "sha256:" + "a" * 64, binding))
    other = answers.payload(Belief(99, "sha256:" + "b" * 64, binding))
    assert one != other and one["value"] == 1 and other["belief_input_digest"].endswith("b" * 64)
    assert answers.payload(NoBelief("no-eligible-assessment")) == {
        "kind": "NoBelief",
        "reason": "no-eligible-assessment",
        "detail": "",
    }
