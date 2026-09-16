"""Cut 31 canonical declaration: the twenty-six estimand-typing sabotages.

One arm per mechanism of the design's §10.3, homed by declaration unit exactly
as the frozen cut document's §5 homes them. Each `before` block is copied
verbatim from the kernel tree Task 11 found, occurs exactly once in the module
it names, and each arm's `checks` name the acceptance test of its own row —
the row's unit is what the arm is an arm of, so the check that must fail is
the one that reads the whole row.
"""

from n2_arms import Arm, Sabotage

DECLARATION_UNITS = ("Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8", "Q9", "Q10")
_A = "acceptance/test_estimand_acceptance.py"
UNIT_CHECKS = {
    "Q1": f"{_A}::test_q1_the_estimands_structure_is_kernel_owned_and_closed",
    "Q2": f"{_A}::test_q2_estimands_is_domain_issued_operator_bound_and_succession_governed",
    "Q3": f"{_A}::test_q3_an_estimand_is_unconstructible_outside_its_claims_operator_declaration",
    "Q4": f"{_A}::test_q4_applicability_is_a_qualifier_map_over_the_target_operators_dimensions",
    "Q5": f"{_A}::test_q5_estimate_and_uncertainty_are_typed_on_the_specs_scale",
    "Q6": f"{_A}::test_q6_structural_match_is_checked_at_the_write_boundary_and_under_audit",
    "Q7": f"{_A}::test_q7_every_member_enters_identity_and_only_members_do",
    "Q8": f"{_A}::test_q8_the_estimands_contracts_are_consulted",
    "Q9": f"{_A}::test_q9_commensuration_is_total_decidable_and_unread_by_v1",
    "Q10": f"{_A}::test_q10_the_reproduction_recreates_re_authors_and_re_derives_from_disk",
}
CO_CITED = ()
"""No cut-31 check is any prior cut's: `test_estimand_acceptance.py` is this
cut's own module and no earlier arm names a node id in it."""


def unit_of(row: str) -> str:
    """Rows are `<unit>` or `<unit>-<letter>`."""
    unit, hyphen, suffix = row.partition("-")
    if unit not in DECLARATION_UNITS or (hyphen and not (len(suffix) == 1 and suffix.islower())):
        raise ValueError(f"{row!r} is not a cut-31 row")
    return unit


def _arm(row, assertion, module, before, after):
    return Arm(
        row=row,
        asserts=assertion,
        sabotage=Sabotage(module=module, before=before, after=after),
        checks=(UNIT_CHECKS[unit_of(row)],),
    )


CUT31_ARMS = (
    # --- Q1: the structure is kernel-owned and closed ----------------------
    _arm("Q1-a", "A scale outside the base contract's closed set is refused, never admitted by the implementation.",
         "estimand.py",
         "        if measure.scale not in grammar.scales:\n",
         "        if False:  # the closed set widened in code, with the contract untouched\n"),
    _arm("Q1-b", "The grammar's members are exactly the contract's; an unknown key is refused at load.",
         "contract/base.py",
         "    _exact_fields(estimand, _ESTIMAND_GRAMMAR_FIELDS, estimand_where)\n",
         "    pass  # an unknown grammar key admitted\n"),

    # --- Q2: `estimands:` is domain-issued, operator-bound, governed -------
    _arm("Q2-a", "An `estimands:` key names an operator the contract itself declares.",
         "contract/domain.py",
         "    if name not in operators:\n",
         "    if False:\n"),
    _arm("Q2-b", "A `level_sorts` index lies inside Fin(arity).",
         "contract/domain.py",
         "        if int(key) >= arity:\n",
         "        if False:\n"),
    _arm("Q2-c", "An estimand declaration is claim vocabulary, so succession governs it.",
         "contract/domain.py",
         '            *((f"estimand:{name}", decl) for name, decl in self.estimands.items()),\n',
         "            *(),  # the estimand declarations left out of the claim vocabulary\n"),

    # --- Q3: unconstructible outside the operator's declaration ------------
    _arm("Q3-a", "A slot the operator declares no level sort for admits no levels contrast.",
         "estimand.py",
         "            if level_sort is None:\n",
         "            if False:\n"),
    _arm("Q3-b", "A referent that is `not-member` of a vocabulary that was read refuses; nothing is minted.",
         "estimand.py",
         "    refused = sorted(label for label, outcome in outcomes.items() if outcome.refuses)\n",
         "    refused = sorted(label for label, outcome in outcomes.items() if False)\n"),
    _arm("Q3-c", "A conditioning set holds each member once.",
         "estimand.py",
         "            if earlier == later:\n",
         "            if False:\n"),
    _arm("Q3-d", "A binary float never reaches a decimal member; it is refused, not coerced.",
         "estimand.py",
         '    if type(value) is not Decimal:\n        raise error(f"{where}: expected a Decimal, found {type(value).__name__} — binary floats are refused at the boundary")\n',
         "    if type(value) is not Decimal:\n        value = Decimal(str(value))  # the binary float coerced instead of refused\n"),
    _arm("Q3-e", "A multiplicative scale admits no reference at or below zero.",
         "estimand.py",
         '        if measure.scale == "multiplicative" and reference <= 0:\n',
         "        if False:\n"),
    _arm("Q3-f", "A continuous contrast's increment is strictly positive.",
         "estimand.py",
         '        if _finite(self.increment, "contrast.increment", ContrastRefused) <= 0:\n',
         '        if _finite(self.increment, "contrast.increment", ContrastRefused) < 0:\n'),
    _arm("Q3-g", "`claim` is the identity of the `Claim` handed in, never a string off the wire.",
         "estimand.py",
         "    identity = claim_identity(claim)\n",
         "    identity = claim.operator  # the wire's operator string, not the Claim's identity\n"),

    # --- Q4: applicability over the target operator's dimensions -----------
    _arm("Q4-a", "Every check `Claim._checked` performs on a qualifier is performed on the applicability map.",
         "estimand.py",
         "    checked = Claim._checked(profile, operator=claim.operator, args=claim.args, qualifiers=qualifiers, polarity=polarity, layer=claim.layer)\n",
         '    checked = type("_Unchecked", (), {"qualifiers": MappingProxyType(dict(qualifiers))})  # routed around Claim._checked\n'),

    # --- Q5: estimate and uncertainty typed on the spec's scale ------------
    _arm("Q5-a", "A rule's estimate is checked at the derivation, and the finding names that violation.",
         "assess.py",
         "            estimate = check_estimate(cast(Decimal, estimate), scale)\n",
         "            estimate = cast(Decimal, estimate)  # a string estimate admitted past the derivation\n"),
    _arm("Q5-b", "An interval contains the estimate it is an interval around.",
         "estimand.py",
         "        if not (low <= estimate <= high):\n",
         "        if False:\n"),
    _arm("Q5-c", "A rule yields outcome, estimate and uncertainty only; the reference and scale stay the spec's.",
         "assess.py",
         '        extra = sorted(set(derived) - {"outcome", "estimate", "uncertainty"})\n',
         "        extra = []  # a rule restating the spec's reference or scale admitted\n"),

    # --- Q6: structural match at the boundary and under audit --------------
    _arm("Q6-a", "The spec's estimand names its target's operator; the claim identity alone does not clear it.",
         "corpus.py",
         "        if spec.estimand.operator != claim.operator:\n",
         "        if False:\n"),
    _arm("Q6-b", "The spec's estimand names its target's claim identity.",
         "corpus.py",
         "        if spec.estimand.claim != claim_identity(claim):\n",
         "        if False:\n"),
    _arm("Q6-c", "A raw-written mismatching spec is contradicted under audit.",
         "audit.py",
         '            elif node.kind == "analysis-spec":\n                outcome = check_spec_target(view, node, profile=profile)\n',
         "            elif False:\n                outcome = check_spec_target(view, node, profile=profile)\n"),

    # --- Q7: every member enters identity, and only members do -------------
    _arm("Q7-a", "`claim` is a member of the estimand's projection, so two claims are two estimands.",
         "estimand.py",
         '        "claim": estimand.claim,\n        "operator": estimand.operator,\n',
         '        "operator": estimand.operator,\n'),
    _arm("Q7-b", "`increment` is a member, so per-unit and per-ten-units are two estimands.",
         "estimand.py",
         '        contrast |= {"kind": "continuous", "quantity": _referent(estimand.contrast.quantity), "increment": estimand.contrast.increment}\n',
         '        contrast |= {"kind": "continuous", "quantity": _referent(estimand.contrast.quantity)}\n'),
    _arm("Q7-c", "The grammar identity is a member of the spec projection.",
         "spec.py",
         '        "estimand_grammar": ESTIMAND_GRAMMAR,\n',
         "        # the grammar member dropped from the spec projection\n"),

    # --- Q8: the estimand's contracts are consulted ------------------------
    _arm("Q8-a", "An assessment reaches the contracts its estimand binds, which its claim need not reach.",
         "consulted.py",
         "    for estimand in estimands.values():\n",
         "    for estimand in ():  # the estimand walk dropped\n"),

    # --- Q9: commensuration is total, decidable and unread by v1 -----------
    _arm("Q9-a", "`control.identification` is the one member outside the commensuration key.",
         "estimand.py",
         '    del control["identification"]\n',
         '    control["identification"] = control["identification"]  # left inside the key\n'),

    # --- Q10: the transition is a recreation, not a migration --------------
    _arm("Q10-a", "A pre-grammar projection is refused by its own name; its prose members are never read as typed.",
         "spec.py",
         '    if isinstance(mapping, dict) and "estimand_grammar" not in mapping:\n',
         '    if isinstance(mapping, dict) and "estimand_grammar" not in mapping and not isinstance(mapping.get("estimand"), str):\n'),
    _arm("Q10-b", "A pre-grammar spec is named by its own audit code, never folded into `derivation-malformed`.",
         "audit.py",
         '                Finding(severity="error", code="spec-pre-grammar", ref=node.id, detail=str(refused), message=f"{node.id}: pre-grammar spec; the corpus was not recreated (decision 10)")\n',
         '                Finding(severity="error", code="derivation-malformed", ref=node.id, detail=str(refused), message=f"{node.id}: pre-grammar spec; the corpus was not recreated (decision 10)")\n'),
)
