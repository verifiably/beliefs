"""Frozen cut-33 declaration: eleven units, each homing one sabotage arm."""

from n2_arms import Arm, Sabotage

DECLARATION_UNITS = ("C7-a", "C7-b", "C7-c", "C3-a", "C3-b", "C10-a", "BI-1", "BI-2", "BI-3", "BI-4", "BI-5")
UNIT_CHECKS = {
    "C7-a": "acceptance/test_correction_acceptance.py::test_c7a_retiring_one_conflicting_route_certifies_over_the_survivor",
    "C7-b": "acceptance/test_correction_acceptance.py::test_c7b_retiring_every_route_is_not_certified_with_lineage_incomplete",
    "C7-c": "acceptance/test_correction_acceptance.py::test_c7c_the_stored_basis_is_byte_unchanged_and_retract_writes_one_record",
    "C3-a": "acceptance/test_correction_acceptance.py::test_c3a_an_uncovered_retraction_moves_nothing_and_coverage_is_a_digest_member",
    "C3-b": "acceptance/test_correction_acceptance.py::test_c3b_an_in_coverage_move_leaves_the_digest_and_moves_the_receipts",
    "C10-a": "acceptance/test_correction_acceptance.py::test_c10a_raw_written_refused_shapes_are_reported_by_both_audits",
    "BI-1": "acceptance/test_correction_acceptance.py::test_bi1_node_standing_subtracts_at_the_read",
    "BI-2": "acceptance/test_correction_acceptance.py::test_bi2_a_retracted_verification_leaves_the_read_set",
    "BI-3": "acceptance/test_correction_acceptance.py::test_bi3_the_enumeration_is_the_views_and_input_scoped",
    "BI-4": "acceptance/test_correction_acceptance.py::test_bi4_an_unreadable_found_retraction_refuses",
    "BI-5": "acceptance/test_correction_acceptance.py::test_bi5_a_resolution_disagreement_refuses",
}
CO_CITED = ()


def unit_of(row: str) -> str:
    """Each row is exactly one declared unit, including its own suffix."""
    if row not in DECLARATION_UNITS:
        raise ValueError(f"{row!r} is not a cut-33 row")
    return row


def _arm(row, assertion, module, before, after):
    return Arm(
        row=row,
        asserts=assertion,
        sabotage=Sabotage(module=module, before=before, after=after),
        checks=(UNIT_CHECKS[unit_of(row)],),
    )


CUT33_ARMS = (
    _arm(
        "C7-a",
        "Retiring one conflicting route leaves independent standing ancestry.",
        "lineage.py",
        "    return tuple(route for route in snapshot.bases[dataset].routes if route.identity not in retired)",
        "    return tuple(snapshot.bases[dataset].routes)",
    ),
    _arm(
        "C7-b",
        "Retiring every route reports lineage-incomplete.",
        "lineage.py",
        '            findings.append("lineage-incomplete")  # every route retired: no standing ancestry',
        "            pass  # every route retired: no standing ancestry",
    ),
    _arm(
        "C7-c",
        "Retraction writes one record without rewriting its dataset basis.",
        "corpus.py",
        '            self._refuse(record, document_validated=True)\n            try:\n                self._view.get(target_ref)\n            except RefError as caught:\n                raise RelocationTargetMissing(\n                    f"{target_ref}: the target no longer resolves in this corpus; a concurrent move "\n                    "or deletion removed it (world-changing families §3.6)"\n                ) from caught\n            return self._corpus.add(record)',
        '            self._refuse(record, document_validated=True)\n            try:\n                self._view.get(target_ref)\n            except RefError as caught:\n                raise RelocationTargetMissing(\n                    f"{target_ref}: the target no longer resolves in this corpus; a concurrent move "\n                    "or deletion removed it (world-changing families §3.6)"\n                ) from caught\n            if target["arm"] == "route":\n                rewritten = self._view.get(target_ref).model_copy(deep=True)\n                basis = rewritten.facets[stored.LINEAGE_BASIS_FACET]\n                basis["routes"] = [route for route in basis["routes"] if route.get("identity") != target["route_identity"]]\n                self._corpus.add(stored.stamp_semantic_identity(rewritten))\n            return self._corpus.add(record)',
    ),
    _arm(
        "C3-a",
        "The retraction coverage declaration is a digest member.",
        "closure.py",
        '            "coverage": list(retractions.coverage),',
        '            "coverage": [],',
    ),
    _arm(
        "C3-b",
        "In-coverage relocation changes receipts without changing the belief input digest.",
        "evaluation.py",
        "    enumeration = view.retraction_enumeration() if world else local_retraction_enumeration(view)",
        '    enumeration = view.retraction_enumeration() if world else local_retraction_enumeration(view)\n    if world:\n        enumeration = RetractionEnumeration(enumeration.found, tuple(f"{c}@{s}" for c, s in view.stamp.coverage))',
    ),
    _arm(
        "C10-a",
        "Both audits report each raw-written refused retraction target.",
        "corpus.py",
        '            except ScienceError as refused:\n                findings.append(\n                    Finding(\n                        severity="error",\n                        code="retraction-target-invalid",\n                        ref=node.id,\n                        detail="target",\n                        message=str(refused),\n                    )\n                )\n',
        "            except ScienceError:\n                continue\n",
    ),
    _arm(
        "BI-1",
        "Standing subtraction happens at the evaluator read boundary.",
        "evaluation.py",
        "        if node.id in subtracted:\n            continue  # a standing retraction names it: a lookup, never decoded",
        "        if False:\n            continue  # a standing retraction names it: a lookup, never decoded",
    ),
    _arm(
        "BI-2",
        "Standing subtraction happens at the evaluator read boundary.",
        "evaluation.py",
        "        if node.id in subtracted:\n            continue  # the amended G8 clause (§7a): it leaves the read set; `active` recomputes over what remains",
        "        if False:\n            continue  # the amended G8 clause (§7a): it leaves the read set; `active` recomputes over what remains",
    ),
    _arm(
        "BI-3",
        "The epoch enumeration is scoped to the proposition inputs.",
        "evaluation.py",
        "        found=tuple(sorted((ref, recorded) for ref, recorded in enumeration.found if ref in taken)),",
        "        found=tuple(sorted(enumeration.found)),",
    ),
    _arm(
        "BI-4",
        "A found but unreadable retraction refuses.",
        "evaluation.py",
        "        except (ScienceError, RefError) as caught:\n            raise RetractionUnreadable(ref, str(caught)) from caught",
        "        except (ScienceError, RefError):\n            continue",
    ),
    _arm(
        "BI-5",
        "A resolution disagreement refuses.",
        "evaluation.py",
        "        if computed != recorded:\n            raise RetractionResolutionDisagreement(ref, recorded, computed)",
        "        if False:\n            raise RetractionResolutionDisagreement(ref, recorded, computed)",
    ),
)
