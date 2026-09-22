"""Frozen cut-37 declaration: eleven units, fifteen sabotage arms (L13-b homes two; L13-d four)."""

from n2_arms import Arm, Sabotage

DECLARATION_UNITS = (
    "L13-a",
    "L13-b",
    "L13-c",
    "L13-d",
    "L13-e",
    "L13-f",
    "L13-g",
    "L13-h",
    "BI-1",
    "BI-2",
    "BI-3",
)
_MODULE = "acceptance/test_l13_preimage_acceptance.py"
UNIT_CHECKS = {
    "L13-a": f"{_MODULE}::test_l13a_a_logged_removal_is_in_the_timeline_and_draws_record_removed_durably",
    "L13-b": f"{_MODULE}::test_l13b_the_surviving_preimage_classifies_the_removal_on_the_writable_root_durably",
    "L13-c": f"{_MODULE}::test_l13c_a_held_copy_of_another_version_of_the_record_resolves_nothing_durably",
    "L13-d": f"{_MODULE}::test_l13d_no_local_history_is_stated_and_a_held_copy_of_the_removed_bytes_resolves_durably",
    "L13-e": f"{_MODULE}::test_l13e_corrupt_local_history_refuses_the_act_and_touches_no_project_file_durably",
    "L13-f": f"{_MODULE}::test_l13f_a_removed_record_of_another_kind_classifies_as_not_a_verification_durably",
    "L13-g": f"{_MODULE}::test_l13g_retirement_appends_a_status_event_and_deletes_nothing_durably",
    "L13-h": f"{_MODULE}::test_l13h_preimage_gc_appears_in_no_chain_and_a_read_appends_nothing_durably",
    "BI-1": f"{_MODULE}::test_bi1_the_reads_are_inside_the_hold_after_the_captures_with_the_chains_arguments_durably",
    "BI-2": f"{_MODULE}::test_bi2_a_read_mutates_nothing_and_joins_no_write_inventory_durably",
    "BI-3": f"{_MODULE}::test_bi3_a_preimage_that_hashes_elsewhere_refuses_before_any_finding_durably",
}
CO_CITED = ()


def unit_of(row: str) -> str:
    """Numbered L13-b and L13-d arms share their declaration unit."""
    unit = row[:-1] if row in ("L13-b1", "L13-b2", "L13-d1", "L13-d2", "L13-d3", "L13-d4") else row
    if unit not in DECLARATION_UNITS:
        raise ValueError(f"{row!r} is not a cut-37 row")
    return unit


def _arm(row, assertion, module, before, after):
    return Arm(
        row=row,
        asserts=assertion,
        sabotage=Sabotage(module=module, before=before, after=after),
        checks=(UNIT_CHECKS[unit_of(row)],),
    )


CUT37_ARMS = (
    _arm(
        "L13-a",
        "A cooperatively logged removal always draws the record-removed policy finding.",
        "world/verify.py",
        "        findings.extend(_removal_findings(removal, held, preimages, state_facts))",
        "        pass  # a logged removal draws no finding",
    ),
    _arm(
        "L13-b1",
        "The removed file state's digest is available to resolve its surviving preimage.",
        "world/verify.py",
        "    facts = _file_facts(state, state_facts)\n    return None if facts is None else facts[0]",
        "    facts = _file_facts(state, state_facts)\n    return None  # no digest, ever",
    ),
    _arm(
        "L13-b2",
        "The preimage read uses the removed state's declared byte length.",
        "world/verify.py",
        "        evidence[(removal.txid, removal.path)] = seam.read_preimage(\n"
        "            root, removal.txid, removal.path, byte_len\n"
        "        )",
        "        evidence[(removal.txid, removal.path)] = seam.read_preimage(\n"
        "            root, removal.txid, removal.path, 0\n"
        "        )",
    ),
    _arm(
        "L13-c",
        "A held copy resolves a removal only when its digest matches the removed state.",
        "world/verify.py",
        "    if digest in held:\n        return (removed, _classification(removal, digest, \"held-copy\", held[digest]))",
        "    if held:\n        return (removed, _classification(removal, digest, \"held-copy\", next(iter(held.values()))))",
    ),
    _arm(
        "L13-d1",
        "An unavailable preimage is stated as refused rather than not consulted.",
        "world/verify.py",
        "    if type(evidence) is PreimageUnavailable:\n"
        "        return (removed, _unclassified(removal, digest, \"refused\", evidence.reason))",
        "    if False:\n"
        "        return (removed, _unclassified(removal, digest, \"refused\", evidence.reason))",
    ),
    _arm(
        "L13-d2",
        "A detached arrival does not read local preimages.",
        "world/verify.py",
        "            PresentedManifest(manifest.corpus_id),\n"
        "            seam.absent_state,\n"
        "            seam.state_facts,\n"
        "            history,\n"
        "        )",
        "            PresentedManifest(manifest.corpus_id),\n"
        "            seam.absent_state,\n"
        "            seam.state_facts,\n"
        "            history,\n"
        "            preimages=_read_preimages(seam, root, view) if type(view) is WellFormedView else NO_PREIMAGES,\n"
        "        )",
    ),
    _arm(
        "L13-d3",
        "A removal whose bytes cannot be resolved carries the stated absence finding.",
        "world/verify.py",
        "    return (removed, _unclassified(removal, digest, \"not-consulted\", None))",
        "    return (removed,)",
    ),
    _arm(
        "L13-e",
        "Corrupt local preimage history refuses the act rather than becoming absent evidence.",
        "root.py",
        "    except MetadataStoreInvalid as caught:\n"
        "        raise LogEvidenceRefused(\"preimage\", \"MetadataStoreInvalid\", str(caught)) from caught",
        "    except MetadataStoreInvalid as caught:\n        return PreimageUnavailable(str(caught))",
    ),
    _arm(
        "L13-d4",
        "Lifecycle unavailability remains evidence rather than refusing the audit.",
        "root.py",
        "    except PreconditionRefused as caught:\n        return PreimageUnavailable(str(caught))",
        "    except PreconditionRefused as caught:\n"
        "        raise LogEvidenceRefused(\"preimage\", \"PreconditionRefused\", str(caught)) from caught",
    ),
    _arm(
        "L13-f",
        "Resolved bytes of another record kind classify as that kind, never as a verification.",
        "world/verify.py",
        "    if node.kind != \"verification\":\n        return Finding(",
        "    if False:\n        return Finding(",
    ),
    _arm(
        "L13-g",
        "Corpus retirement appends a status record and deletes no registry record.",
        "world/registry.py",
        '            self._executor_factory(self.config.world_root).execute(\n'
        '                [CreateOp(f"registry/{digest}.yaml", _record_bytes(status_projection(candidate)))]\n'
        "            )",
        '            for _prior in sorted((self.config.world_root / "registry").glob("*.yaml")):\n'
        "                _prior.unlink()\n"
        '            self._executor_factory(self.config.world_root).execute(\n'
        '                [CreateOp(f"registry/{digest}.yaml", _record_bytes(status_projection(candidate)))]\n'
        "            )",
    ),
    _arm(
        "L13-h",
        "The closed log-entry taxonomy records no preimage collection event.",
        "world/logmodel.py",
        "class IntentEntryView:\n    digest: str\n    payload: bytes",
        "class IntentEntryView:\n    digest: str\n    payload: bytes\n    preimage_gc: bool = False",
    ),
    _arm(
        "BI-1",
        "Preimages are read under the audit hold after both captures.",
        "world/verify.py",
        "        preimages = (\n"
        "            _read_preimages(seam, root, view)\n"
        "            if type(view) is WellFormedView\n"
        "            else NO_PREIMAGES\n"
        "        )\n"
        "    return evaluate_log(",
        "    preimages = (\n"
        "        _read_preimages(seam, root, view)\n"
        "        if type(view) is WellFormedView\n"
        "        else NO_PREIMAGES\n"
        "    )\n"
        "    return evaluate_log(",
    ),
    _arm(
        "BI-2",
        "Reading preimages mutates no project file.",
        "world/verify.py",
        "    evidence: dict[tuple[str, str], PreimageEvidence] = {}\n"
        "    for removal in committed_removals(view, seam.absent_state):",
        "    evidence: dict[tuple[str, str], PreimageEvidence] = {}\n"
        '    (root / "corpus.yaml").write_bytes(b"")\n'
        "    for removal in committed_removals(view, seam.absent_state):",
    ),
    _arm(
        "BI-3",
        "Preimage bytes are re-hashed against the removed state's digest before any finding.",
        "world/verify.py",
        "        if actual != digest:",
        "        if False:",
    ),
)
