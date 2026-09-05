"""One serialization of the evaluator's answer, used by step 8 and step 10a alike.

A Belief is its value, its input digest and its policy binding; dropping any
of the three would let Belief(1) compare equal to Belief(99).
"""

from __future__ import annotations

from beliefs.belief import Belief, NoBelief, Refused


def payload(answer: Belief | NoBelief | Refused) -> dict:
    if isinstance(answer, Belief):
        return {
            "kind": "Belief",
            "value": answer.value,
            "belief_input_digest": answer.belief_input_digest,
            "policy_binding": [answer.policy_binding.rule, answer.policy_binding.implementation],
        }
    if isinstance(answer, NoBelief):
        return {"kind": "NoBelief", "reason": answer.reason, "detail": answer.detail}
    if isinstance(answer, Refused):
        return {"kind": "Refused", "reason": answer.reason}
    raise TypeError(f"not an evaluator answer: {type(answer).__name__}")
