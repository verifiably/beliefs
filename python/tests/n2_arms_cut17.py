"""Cut 17's 17 frozen declaration units and their source sabotages.

One unit per row selection of `docs/designs/2026-09-04-conformance-cut-17.md`
§3, plus the boundary invariant — sixteen guarantee rows and one invariant,
counted once each in §4. Lettered arms (`R23a`, `M11b`, …) normalize back to
their unit through `unit_of`; the inventory is the tuple below and nothing
else.

Every arm names one source mutation and the durable check it must turn red.
The checks are cut 17's own — `tests/acceptance/test_deletion_acceptance.py`,
the module that runs on the certified engine and volume — so no arm here
borrows a prior cut's evidence and `CO_CITED` is empty.
"""

from n2_arms import Arm, Sabotage

_ACCEPTANCE = "acceptance/test_deletion_acceptance.py"

_G2C = f"{_ACCEPTANCE}::test_g2c_lifecycle_walk_over_durable_records"
_G8_C6 = f"{_ACCEPTANCE}::test_g8_c6_raw_removal_refutes_and_managed_delete_validates"
_R5 = f"{_ACCEPTANCE}::test_r5_the_managed_holdings_delete_ends_heldness_and_changes_admission"
_S5 = f"{_ACCEPTANCE}::test_s5_deletion_half_durably"
_R23 = f"{_ACCEPTANCE}::test_r23_deletion_and_audit_clauses_durably"
_W16 = f"{_ACCEPTANCE}::test_w16_conflict_survives_deleting_either_producer_durably"
_C1 = f"{_ACCEPTANCE}::test_c1_retraction_never_removes_its_target_durably"
_T8 = f"{_ACCEPTANCE}::test_t8_delete_refuses_an_act_report_durably"
_M13 = f"{_ACCEPTANCE}::test_m13_claim_from_stored_is_opaque_over_a_durable_record"
_M11 = f"{_ACCEPTANCE}::test_m11_claim_from_stored_is_a_function_of_its_arguments_over_a_durable_record"
_R19 = f"{_ACCEPTANCE}::test_r19_import_validation_and_transition_b_durably"
_R22 = f"{_ACCEPTANCE}::test_r22_import_recomputation_and_audit_durably"
_M1 = f"{_ACCEPTANCE}::test_m1_containment_over_a_durable_corpus"
_M3 = f"{_ACCEPTANCE}::test_m3_audit_classification_and_admission_order_durably"
_M5 = f"{_ACCEPTANCE}::test_m5_qualification_identity_durably"
_BOUNDARY = f"{_ACCEPTANCE}::test_boundary_reresolution_after_a_durable_delete"


CUT17_ARMS = (
    # --- G2c: the lifecycle walk, and `delete`'s committed shape -------------
    Arm(
        row="G2c",
        asserts="`delete` is an ordinary write: one registered transaction, no operation intent",
        sabotage=Sabotage(
            module="corpus.py",
            before=("            self._refuse_excluded_kind(node)\n            self._delete_locked(node.id)\n"),
            after=(
                "            self._refuse_excluded_kind(node)\n"
                '            self._append_operation_intent("delete", secrets.token_hex(16), "actor")\n'
                "            self._delete_locked(node.id)\n"
            ),
        ),
        checks=(_G2C,),
    ),
    # --- G8: the log half of the asymmetry (§5 obligation 4) -----------------
    Arm(
        row="G8",
        asserts="the managed removal of a held failing verification classifies at error severity",
        sabotage=Sabotage(
            module="world/verify.py",
            before='    if held.verdict == "failed":\n',
            after='    if held.verdict == "passed":\n',
        ),
        checks=(_G8_C6,),
    ),
    # --- C6: the raw removal stays undetectable on the corpus read -----------
    Arm(
        row="C6",
        asserts="the lifecycle is a pure function of the verifications present — no cross-call memory",
        sabotage=Sabotage(
            module="verification.py",
            before=(
                "    live = active(verifications)\n"
                '    if any(v.verdict == "failed" for v in live):\n'
                "        return INVALIDATED\n"
            ),
            after=(
                "    live = active(verifications)\n"
                '    memory = lifecycle_state.__dict__.setdefault("_seen_failure", set())\n'
                '    if any(v.verdict == "failed" for v in live):\n'
                "        memory.update(v.assessment for v in live)\n"
                "    if any(v.assessment in memory for v in verifications):\n"
                "        return INVALIDATED\n"
            ),
        ),
        checks=(_G8_C6,),
    ),
    # --- R5: the last held copy ---------------------------------------------
    Arm(
        row="R5",
        asserts="heldness is read from published observations and never re-derived from the declaration",
        sabotage=Sabotage(
            module="holdings/adapter.py",
            before=(
                "    return DatasetAnswer(tuple(ByteObservation(digest, location) "
                "for digest, location in sorted(observations)))\n"
            ),
            after=(
                "    if not observations:\n"
                '        return DatasetAnswer(tuple(ByteObservation(digest, "declared") '
                "for digest in sorted(declared)))\n"
                "    return DatasetAnswer(tuple(ByteObservation(digest, location) "
                "for digest, location in sorted(observations)))\n"
            ),
        ),
        checks=(_R5,),
    ),
    # --- S5: the deleted ancestor -------------------------------------------
    Arm(
        row="S5",
        asserts="a basis route's ancestor resolution is a real lookup, so a deleted ancestor reads `null`",
        sabotage=Sabotage(
            module="corpus.py",
            before='                resolved_ancestor=view.resolve(str(route.get("ancestor", ""))),\n',
            after='                resolved_ancestor=str(route.get("ancestor", "")),\n',
        ),
        checks=(_S5,),
    ),
    # --- R23: the separated resolution, and the forged `single(A)` -----------
    Arm(
        row="R23a",
        asserts="a stamped basis that omits a resolving producer is contradicted while that run stands",
        sabotage=Sabotage(
            module="audit.py",
            before="    omitted = sorted(producers - named_resolved)\n",
            after="    omitted = []\n",
        ),
        checks=(_R23,),
    ),
    Arm(
        row="R23b",
        asserts="a basis route's run resolution is a real lookup, so a deleted producing run reads `null`",
        sabotage=Sabotage(
            module="corpus.py",
            before='                resolved_run=view.resolve(str(route.get("run", ""))),\n',
            after='                resolved_run=str(route.get("run", "")),\n',
        ),
        checks=(_R23,),
    ),
    # --- W16: the conflict basis decided on its tag --------------------------
    Arm(
        row="W16",
        asserts="a `conflict` basis decides `lineage-divergent` on the tag alone, before any resolution",
        sabotage=Sabotage(
            module="lineage.py",
            before=(
                '        if basis.tag == "conflict":\n'
                '            findings.append("lineage-divergent")\n'
                "            continue  # decided on the tag alone, before resolution or comparison\n"
            ),
            after=(
                '        if basis.tag == "conflict":\n'
                "            if all(r.resolved_run is not None for r in basis.routes):\n"
                '                findings.append("lineage-divergent")\n'
                "            continue\n"
            ),
        ),
        checks=(_W16,),
    ),
    # --- C1: retraction is additive -----------------------------------------
    Arm(
        row="C1",
        asserts="retraction never reaches the delete seam — its target's bytes and address are untouched",
        sabotage=Sabotage(
            module="corpus.py",
            before=(
                "                ) from caught\n"
                "            return self._corpus.add(record)\n"
                "\n"
                "    def supersede(self, successor: Node, *, of: str) -> Node:\n"
            ),
            after=(
                "                ) from caught\n"
                "            self._delete_locked(target_ref)\n"
                "            return self._corpus.add(record)\n"
                "\n"
                "    def supersede(self, successor: Node, *, of: str) -> Node:\n"
            ),
        ),
        checks=(_C1,),
    ),
    # --- T8: no ordinary API deletes a report --------------------------------
    Arm(
        row="T8",
        asserts="`act-report` is excluded from every world-changing operation, `delete` included",
        sabotage=Sabotage(
            module="corpus.py",
            before=(
                'EXCLUDED_MUTATION_KINDS: tuple[str, ...] = ("act-report", "holdings-observation", '
                "*COORDINATION_KINDS)\n"
            ),
            after=(
                'EXCLUDED_MUTATION_KINDS: tuple[str, ...] = ("holdings-observation", *COORDINATION_KINDS)\n'
            ),
        ),
        checks=(_T8,),
    ),
    # --- M13: the restore seam delegates -------------------------------------
    Arm(
        row="M13",
        asserts="the restore seam delegates typing to `decode_claim` rather than deciding it itself",
        sabotage=Sabotage(
            module="decode.py",
            before=(
                "def claim_from_stored(node: Node, *, profile: ProfileSpec, snapshot: ResolutionSnapshot)"
                " -> tuple[Claim, BindingCheckReceipt]:\n"
            ),
            after=(
                "def claim_from_stored(  # the seam is bound at import, so the call never reaches the module\n"
                "    node: Node, *, profile: ProfileSpec, snapshot: ResolutionSnapshot, decode_claim=decode_claim\n"
                ") -> tuple[Claim, BindingCheckReceipt]:\n"
            ),
        ),
        checks=(_M13,),
    ),
    # --- M11: a function of its arguments ------------------------------------
    Arm(
        row="M11a",
        asserts="an inexact stored claim facet refuses before delegation, and is never repaired",
        sabotage=Sabotage(
            module="decode.py",
            before=(
                "    keys = set(facet)\n"
                "    if keys != _STORED_CLAIM_KEYS:\n"
                "        missing, extra = sorted(_STORED_CLAIM_KEYS - keys), sorted(keys - _STORED_CLAIM_KEYS)\n"
                '        raise MalformedWireClaim(f"{node.id}: claim facet missing {missing}, extra {extra};'
                ' refused, never repaired")\n'
            ),
            after="",
        ),
        checks=(_M11,),
    ),
    Arm(
        row="M11b",
        asserts="availability stays a parameter — the seam never supplies a snapshot of its own",
        sabotage=Sabotage(
            module="decode.py",
            before="    wire = WireClaim(\n",
            after=(
                "    if snapshot is None:\n"
                "        from beliefs.resolution import build_snapshot\n"
                "\n"
                "        snapshot = build_snapshot(readable={})\n"
                "    wire = WireClaim(\n"
            ),
        ),
        checks=(_M11,),
    ),
    # --- R19: refused before any payload write -------------------------------
    Arm(
        row="R19",
        asserts="a contradicted derivation refuses the import before any bundle member lands",
        sabotage=Sabotage(
            module="corpus.py",
            before=(
                "            contradiction = outcome.contradiction\n"
                "            if contradiction is not None:\n"
                "                raise ImportRefused(\n"
                '                    f"{contradiction.message}: {contradiction.detail}", member=record.id\n'
                "                )\n"
            ),
            after=(
                "            contradiction = outcome.contradiction\n"
                "            if contradiction is not None:\n"
                '                findings.add(f"derivation-contradicted: {record.id}: {contradiction.message}")\n'
            ),
        ),
        checks=(_R19,),
    ),
    # --- R22: the assessment facet is recomputed from the run ----------------
    Arm(
        row="R22",
        asserts="the stored assessment outcome is recomputed and compared, not taken on trust",
        sabotage=Sabotage(
            module="audit.py",
            before=('_COMPARABLE_ASSESSMENT_MEMBERS = (\n    "outcome",\n    "interpretation_rule",\n'),
            after=('_COMPARABLE_ASSESSMENT_MEMBERS = (\n    "interpretation_rule",\n'),
        ),
        checks=(_R22,),
    ),
    # --- M1: containment over the instrumented resolver ----------------------
    Arm(
        row="M1",
        asserts="the recorded read-set is contained in the declared closure, and a wider read breaks it",
        sabotage=Sabotage(
            module="evaluation.py",
            before="    return value.assessment in ids\n",
            after="    return True\n",
        ),
        checks=(_M1,),
    ),
    # --- M3: Ω_valid before any standing or belief evaluation ----------------
    Arm(
        row="M3",
        asserts="the audit classifies malformedness before any standing evaluation (§5 obligation 5)",
        sabotage=Sabotage(
            module="audit.py",
            before="    findings = list(corpus_check(view))\n",
            after=(
                "    from beliefs import corpus as _corpus_module\n"
                "\n"
                '    _corpus_module.standing_in_local_view(view, "corpus")\n'
                "    findings = list(corpus_check(view))\n"
            ),
        ),
        checks=(_M3,),
    ),
    # --- M5: the qualification is part of the identity -----------------------
    Arm(
        row="M5",
        asserts="the qualifier map is projected, so each qualification difference moves `I_claim`",
        sabotage=Sabotage(
            module="projection.py",
            before=(
                '        "qualifiers": {\n'
                '            dimension: {"quantifier": qualifier.quantifier, '
                '"restriction": qualifier.restriction.term}\n'
                "            for dimension, qualifier in claim.qualifiers.items()\n"
                "        },\n"
            ),
            after='        "qualifiers": {},\n',
        ),
        checks=(_M5,),
    ),
    # --- the boundary invariant (§3.6) ---------------------------------------
    Arm(
        row="boundary-reresolution-after-delete-a",
        asserts="`retract` re-resolves its target under the lock immediately before writing",
        sabotage=Sabotage(
            module="corpus.py",
            before=(
                "            self._refuse(record, document_validated=True)\n"
                "            try:\n"
                "                self._view.get(target_ref)\n"
            ),
            after=(
                "            self._refuse(record, document_validated=True)\n"
                "            try:\n"
                "                pass\n"
            ),
        ),
        checks=(_BOUNDARY,),
    ),
    Arm(
        row="boundary-reresolution-after-delete-b",
        asserts="`supersede` re-resolves its predecessor under the lock immediately before writing",
        sabotage=Sabotage(
            module="corpus.py",
            before=(
                "            self._refuse(candidate)\n"
                "            try:\n"
                "                self._view.get(predecessor_id)\n"
            ),
            after=("            self._refuse(candidate)\n            try:\n                pass\n"),
        ),
        checks=(_BOUNDARY,),
    ),
)

_UNIT_OF = {
    "R23a": "R23",
    "R23b": "R23",
    "M11a": "M11",
    "M11b": "M11",
    "boundary-reresolution-after-delete-a": "boundary-reresolution-after-delete",
    "boundary-reresolution-after-delete-b": "boundary-reresolution-after-delete",
}


def unit_of(row: str) -> str:
    return _UNIT_OF.get(row, row)


DECLARATION_UNITS = (
    "G2c",
    "G8",
    "C6",
    "R5",
    "S5",
    "R23",
    "W16",
    "C1",
    "T8",
    "M13",
    "M11",
    "R19",
    "R22",
    "M1",
    "M3",
    "M5",
    "boundary-reresolution-after-delete",
)

CO_CITED: dict[str, tuple[str, ...]] = {}
