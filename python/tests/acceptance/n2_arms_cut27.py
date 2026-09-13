"""Cut 27 canonical declaration: R23, W8a, X5, W13 and S9 over the slice 3 seams."""

from n2_arms import Arm, Sabotage

DECLARATION_UNITS = ("R23", "W8a", "X5", "W13", "S9")
_A = "acceptance/test_world_audit_acceptance.py"
UNIT_CHECKS = {
    "R23": f"{_A}::test_the_literal_omission_is_malformed_and_the_consistent_one_refuted_durably",
    "W8a": f"{_A}::test_every_coverage_declaration_must_agree_durably",
    "X5": f"{_A}::test_two_carriers_of_one_id_refuse_the_build_durably",
    "W13": f"{_A}::test_root_move_rename_and_clone_change_no_identity_durably",
    "S9": f"{_A}::test_a_damaged_carrier_is_reported_and_never_served_durably",
}
CO_CITED = ()


def unit_of(row: str) -> str:
    """Rows are `<unit>` or `<unit>-<letter>`."""
    unit, hyphen, suffix = row.partition("-")
    if unit not in DECLARATION_UNITS or (hyphen and not (len(suffix) == 1 and suffix.islower())):
        raise ValueError(f"{row!r} is not a cut-27 row")
    return unit


CUT27_ARMS = (
    Arm(
        row="W8a-a",
        asserts="Malformedness is decided before rule or corpus availability.",
        sabotage=Sabotage(
            module="world/read.py",
            before='    fault = _contract_fault(kind, member, receipt, published)\n    if fault is not None:\n        return derive.ReceiptOutcome(kind, "malformed", fault)\n    # Past this point the five identity members are present and well formed,\n    # so the reads below can name them without re-checking that they exist.\n    named_states = cast(Sequence[tuple[str, str]], receipt.corpus_states)\n    binding = rules.RuleBinding(\n        cast(str, receipt.rule_identity), cast(str, receipt.implementation_identity)\n    )\n    with registry._locked_barrier(world) as world_root:\n        try:\n            held = rules._locked_resolve_rule_binding(world_root, binding)\n        except RuleNotHeld as caught:\n            return derive.ReceiptOutcome(\n                kind,\n                "unresolvable",\n                f"the exact pair this receipt names is not held here: {caught}",\n            )',
            after='    # Past this point the five identity members are present and well formed,\n    # so the reads below can name them without re-checking that they exist.\n    named_states = cast(Sequence[tuple[str, str]], receipt.corpus_states)\n    binding = rules.RuleBinding(\n        cast(str, receipt.rule_identity), cast(str, receipt.implementation_identity)\n    )\n    with registry._locked_barrier(world) as world_root:\n        try:\n            held = rules._locked_resolve_rule_binding(world_root, binding)\n        except RuleNotHeld as caught:\n            return derive.ReceiptOutcome(\n                kind,\n                "unresolvable",\n                f"the exact pair this receipt names is not held here: {caught}",\n            )\n    fault = _contract_fault(kind, member, receipt, published)\n    if fault is not None:\n        return derive.ReceiptOutcome(kind, "malformed", fault)',
        ),
        checks=(f"{_A}::test_every_coverage_declaration_must_agree_durably",),
    ),
    Arm(
        row="W8a-b",
        asserts="The snapshot, receipt and epoch all declare the same coverage.",
        sabotage=Sabotage(
            module="world/read.py",
            before="if subject_coverage is not None and subject_coverage != declared:",
            after="if False:",
        ),
        checks=(f"{_A}::test_every_coverage_declaration_must_agree_durably",),
    ),
    Arm(
        row="W8a-c",
        asserts="A literal omission disagrees with the receipt subject before reconstruction.",
        sabotage=Sabotage(
            module="world/read.py",
            before="if member_identity != receipt.subject_identity:",
            after="if False:",
        ),
        checks=(f"{_A}::test_the_literal_omission_is_malformed_and_the_consistent_one_refuted_durably",),
    ),
    Arm(
        row="W8a-d",
        asserts="All malformed evidence leaves a snapshot unchecked.",
        sabotage=Sabotage(
            module="world/audit.py",
            before='if any(outcome.outcome == "refuted" for outcome in well_formed):',
            after='if any(outcome.outcome in ("refuted", "malformed") for outcome in outcomes):',
        ),
        checks=(f"{_A}::test_an_all_malformed_snapshot_is_unchecked_with_a_finding_per_pair_durably",),
    ),
    Arm(
        row="W8a-e",
        asserts="An unreadable carrier is reported while its neighbor is evaluated.",
        sabotage=Sabotage(
            module="world/audit.py",
            before="unreadable.append((name, str(caught)))",
            after="continue",
        ),
        checks=(f"{_A}::test_an_unreadable_carrier_is_a_finding_and_the_next_carrier_is_still_evaluated_durably",),
    ),
    Arm(
        row="W8a-f",
        asserts="Corpus construction damage makes receipt validation unresolvable.",
        sabotage=Sabotage(
            module="world/read.py",
            before="except CorpusStateMalformed as caught:",
            after="except ManifestMalformed as caught:",
        ),
        checks=(
            f"{_A}::test_the_evaluator_answers_unresolvable_for_a_damaged_carrier_and_the_edge_is_indeterminate_durably",
        ),
    ),
    Arm(
        row="W8a-g",
        asserts="A retained carrier with unreadable bytes is an audit finding.",
        sabotage=Sabotage(
            module="world/audit.py",
            before="except (EpochMalformed, OSError) as caught:",
            after="except EpochMalformed as caught:",
        ),
        checks=(f"{_A}::test_an_unreadable_carrier_is_a_finding_and_the_next_carrier_is_still_evaluated_durably",),
    ),
    Arm(
        row="W8a-h",
        asserts="Imported anchors require an independent registry record.",
        sabotage=Sabotage(
            module="world/audit.py",
            before="recorded = {(record.subject, record.genesis, record.head) for record in view.log_heads}",
            after="recorded = {(anchors.CorpusSubject(a.subject), a.genesis_digest, a.head_digest) for e in opened.values() for a in e.anchors}",
        ),
        checks=(f"{_A}::test_a_built_epochs_anchors_are_corroborated_and_an_imported_ones_are_not_durably",),
    ),
    Arm(
        row="W8a-i",
        asserts="Import writes only the eleven members and never current.",
        sabotage=Sabotage(
            module="world/importing.py",
            before='[CreateOp(f"epochs/{packaging_identity}/{member}", members[member]) for member in epoch.EPOCH_MEMBERS]',
            after='[CreateOp(f"epochs/{packaging_identity}/{member}", members[member]) for member in epoch.EPOCH_MEMBERS] + [CreateOp(f"epochs/{epoch.CURRENT_POINTER}", epoch._current_pointer_bytes(packaging_identity))]',
        ),
        checks=(f"{_A}::test_import_refuses_a_write_and_audit_and_query_write_nothing_durably",),
    ),
    Arm(
        row="W8a-j",
        asserts="Import records no build-origin log head.",
        sabotage=Sabotage(
            module="world/importing.py",
            before='[CreateOp(f"epochs/{packaging_identity}/{member}", members[member]) for member in epoch.EPOCH_MEMBERS]',
            after='[CreateOp(f"epochs/{packaging_identity}/{member}", members[member]) for member in epoch.EPOCH_MEMBERS] + epoch._locked_log_head_records(world_root, packaging_identity, members)',
        ),
        checks=(f"{_A}::test_a_built_epochs_anchors_are_corroborated_and_an_imported_ones_are_not_durably",),
    ),
    Arm(
        row="W8a-k",
        asserts="Import derives the packaging identity from members, not the source directory.",
        sabotage=Sabotage(
            module="world/importing.py",
            before="packaging_identity = epoch.packaging_identity_of(members)",
            after="packaging_identity = Path(source).name",
        ),
        checks=(f"{_A}::test_an_unresolvable_receipt_imports_with_a_finding_and_a_later_audit_evaluates_it_durably",),
    ),
    Arm(
        row="W8a-l",
        asserts="A carrier of a different world is refused before writing.",
        sabotage=Sabotage(
            module="world/importing.py",
            before="if carrier.world_anchor.subject != world.config.world_id:",
            after="if False:",
        ),
        checks=(f"{_A}::test_a_carrier_of_another_world_is_refused_durably",),
    ),
    Arm(
        row="R23-a",
        asserts="A consistent omission refuted by reconstruction is refused at import.",
        sabotage=Sabotage(
            module="world/importing.py",
            before='(("malformed-receipt", "malformed"), ("refuted-receipt", "refuted"))',
            after='(("malformed-receipt", "malformed"),)',
        ),
        checks=(f"{_A}::test_the_literal_omission_is_malformed_and_the_consistent_one_refuted_durably",),
    ),
    Arm(
        row="R23-b",
        asserts="A snapshot query reduces all retained receipts naming its subject.",
        sabotage=Sabotage(
            module="world/audit.py",
            before="        for name in sorted(opened)\n        if opened[name].receipts[member].subject_identity == subject_identity",
            after="        for name in sorted(opened)[-1:]\n        if opened[name].receipts[member].subject_identity == subject_identity",
        ),
        checks=(f"{_A}::test_a_validating_receipt_beside_a_malformed_one_is_checked_durably",),
    ),
    Arm(
        row="R23-c",
        asserts="Post-publication records are reported as unmapped drift.",
        sabotage=Sabotage(
            module="audit.py",
            before="for uid in moved.unmapped:",
            after="for uid in ():",
        ),
        checks=(f"{_A}::test_drift_absence_and_unreachable_recomputation_are_findings_durably",),
    ),
    Arm(
        row="R23-d",
        asserts="An attestation endpoint resolves against the whole world.",
        sabotage=Sabotage(
            module="audit.py",
            before="located = view.locate(endpoint)",
            after="located = view.locate(endpoint) if view.corpus_view(node.id).resolve(endpoint) is not None else Unknown(view.stamp)",
        ),
        checks=(f"{_A}::test_attestation_endpoints_and_shared_identifiers_are_findings_durably",),
    ),
    Arm(
        row="R23-e",
        asserts="Every normalized source identifier participates in shared-identifier findings.",
        sabotage=Sabotage(
            module="audit.py",
            before="for scheme, value in normalized.items():",
            after="for scheme, value in [source_basis.basis(normalized)]:",
        ),
        checks=(f"{_A}::test_attestation_endpoints_and_shared_identifiers_are_findings_durably",),
    ),
    Arm(
        row="S9-a",
        asserts="Report-mode construction damage is a finding rather than an open refusal.",
        sabotage=Sabotage(
            module="world/view.py",
            before='            except CorpusStateMalformed:\n                if on_damage == "refuse":\n                    raise',
            after="            except CorpusStateMalformed:\n                raise",
        ),
        checks=(f"{_A}::test_a_damaged_carrier_is_reported_and_never_served_durably",),
    ),
    Arm(
        row="S9-b",
        asserts="No corpus state is claimed over a collected remainder.",
        sabotage=Sabotage(
            module="world/view.py",
            before="                remainder, findings = _collecting_view(carrier)\n                damaged.append",
            after='                remainder, findings = _collecting_view(carrier)\n                states[corpus_id] = "0" * 64\n                captured[corpus_id] = {node.uid: node for node in remainder}\n                damaged.append',
        ),
        checks=(f"{_A}::test_the_default_open_still_refuses_and_no_state_identity_is_taken_over_a_remainder_durably",),
    ),
    Arm(
        row="S9-c",
        asserts="Every mapped read into a damaged carrier raises CorpusDamaged.",
        sabotage=Sabotage(
            module="world/view.py",
            before="        entry = self._recorded.get(ref)\n        if entry is not None and entry[0] in self._damaged_ids:\n            raise CorpusDamaged(ref, entry[0], self._stamp)",
            after="        return",
        ),
        checks=(f"{_A}::test_a_damaged_carrier_is_reported_and_never_served_durably",),
    ),
    Arm(
        row="S9-d",
        asserts="Per-record findings judge the detached capture, not later live bytes.",
        sabotage=Sabotage(
            module="audit.py",
            before="_CapturedCheckView(view.captured_records(corpus_id))",
            after="_CapturedCheckView(tuple(view.corpus_view(next(n.id for n in view.iter_stored() if view.corpus_of(n.id) == corpus_id)).iter_stored()))",
        ),
        checks=(f"{_A}::test_the_world_audit_reproduces_every_per_record_finding_durably",),
    ),
    Arm(
        row="S9-e",
        asserts="A foreign base pin admits no captured records.",
        sabotage=Sabotage(
            module="world/view.py",
            before='                damaged.append(DamageReport(corpus_id, carrier, "base-pin", ()))\n                all_captured[corpus_id] = ()',
            after='                damaged.append(DamageReport(corpus_id, carrier, "base-pin", ()))\n                all_captured[corpus_id] = tuple(view.iter_stored())',
        ),
        checks=(f"{_A}::test_a_foreign_base_pin_is_base_pin_damage_durably",),
    ),
    Arm(
        row="S9-f",
        asserts="A healthy attestation over a damaged endpoint yields an unreachable finding.",
        sabotage=Sabotage(
            module="audit.py",
            before="except CorpusDamaged:",
            after="except IdentifierMalformed:",
        ),
        checks=(f"{_A}::test_attestation_endpoints_and_shared_identifiers_are_findings_durably",),
    ),
    Arm(
        row="S9-g",
        asserts="A recomputation reaching damage is unreachable, not malformed.",
        sabotage=Sabotage(
            module="audit.py",
            before="except CorpusDamaged as unreachable:",
            after="except RuleUnbound as unreachable:",
        ),
        checks=(f"{_A}::test_drift_absence_and_unreachable_recomputation_are_findings_durably",),
    ),
    Arm(
        row="X5-a",
        asserts="Two live carriers of one corpus id refuse the build without offering a repair.",
        sabotage=Sabotage(
            module="world/registry.py",
            before="                carriers.append(root)",
            after="                if not carriers:\n                    carriers.append(root)",
        ),
        checks=(f"{_A}::test_two_carriers_of_one_id_refuse_the_build_durably",),
    ),
    Arm(
        row="W13-a",
        asserts="Corpus state and belief identity are invariant under root relocation.",
        sabotage=Sabotage(
            module="world/registry.py",
            before='    projection = {\n        "manifest": manifest_projection(manifest),',
            after='    projection = {\n        "root": str(corpus_root),\n        "manifest": manifest_projection(manifest),',
        ),
        checks=(f"{_A}::test_root_move_rename_and_clone_change_no_identity_durably",),
    ),
    Arm(
        row="W13-b",
        asserts="Published coverage uses corpus identity, never carrier directory names.",
        sabotage=Sabotage(
            module="world/epoch.py",
            before="captured.append(derive.CapturedCorpus(corpus_id, before, records))",
            after="captured.append(derive.CapturedCorpus(Path(carrier).name, before, records))",
        ),
        checks=(f"{_A}::test_root_move_rename_and_clone_change_no_identity_durably",),
    ),
)
