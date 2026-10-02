"""Cut 45: caller acceptance precedes semantic reads and standing effects."""

from dataclasses import FrozenInstanceError, replace
from typing import Any

import pytest
from test_belief import scenario

from beliefs import belief
from beliefs.errors import LoneSurrogate, MalformedRecord


def test_acceptance_value_validation():
    policy_type: Any = belief.AcceptancePolicy
    context_type = belief.AcceptanceContext
    for text in ("", 1, None):
        with pytest.raises(MalformedRecord, match="acceptance-statement-not-text"):
            policy_type(lambda _c, _r: True, text)
    with pytest.raises(MalformedRecord, match="acceptance-predicate-not-callable"):
        policy_type(None, "policy")
    with pytest.raises(LoneSurrogate):
        policy_type(lambda _c, _r: True, "\ud800")
    with pytest.raises(LoneSurrogate):
        context_type("\ud800", (), False)
    with pytest.raises(MalformedRecord, match="incomplete-acceptance-exclusions"):
        context_type("policy", (("c", "assessment:a"),), False)
    selection = context_type("policy", (("z", "a"), ("a", "b"), ("z", "a")), True)
    assert selection.excluded == (("a", "b"), ("z", "a"))
    with pytest.raises(FrozenInstanceError):
        selection.statement = "changed"  # pyright: ignore[reportAttributeAccessIssue]


def test_g13_g_pure_incomplete(monkeypatch):
    selection = belief.AcceptanceContext("policy", (), False)
    kwargs = scenario()
    kwargs["context"] = replace(kwargs["context"], acceptance=selection)

    def unexpected_consulted(**_kwargs):
        pytest.fail("incomplete selection reached the consulted walk")

    monkeypatch.setattr(belief, "consulted_contracts", unexpected_consulted)
    answer, admission = belief.evaluate_traced(**kwargs)
    assert isinstance(answer, belief.Refused)
    assert answer.reason == "acceptance-selection-incomplete"
    assert answer.acceptance == selection
    assert admission == belief.NotReached()
    answer, admission = belief.evaluate_traced(**scenario(context=kwargs["context"], binding=object()))
    assert isinstance(answer, belief.Refused) and answer.reason.startswith("binding-not-exact")
    assert answer.acceptance == selection and admission == belief.NotReached()


def test_pure_completed_context_accompanies_every_answer():
    selection = belief.AcceptanceContext("policy", (("c", "unrelated"),), True)
    kwargs = scenario()
    kwargs["context"] = replace(kwargs["context"], acceptance=selection)
    assert isinstance(belief.evaluate(**kwargs), belief.Belief)
    assert belief.evaluate(**kwargs).acceptance == selection
    unavailable = replace(kwargs["availability"], fixtures={})
    answer = belief.evaluate(**scenario(context=kwargs["context"], availability=unavailable))
    assert isinstance(answer, belief.NoBelief) and answer.acceptance == selection
    answer = belief.evaluate(**scenario(context=kwargs["context"], binding=object()))
    assert isinstance(answer, belief.Refused) and answer.acceptance == selection
