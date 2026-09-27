"""Frozen cut-42 declaration: fourteen units, fourteen sabotage arms, one each."""

from n2_arms import Arm, Sabotage

DECLARATION_UNITS = (
    "Y11-a",
    "Y12-a",
    "Y12-b",
    "Y12-c",
    "Y13-a",
    "Y13-b",
    "Y13-c",
    "Y14-a",
    "Y14-b",
    "Y15-a",
    "Y15-b",
    "Y16-a",
    "Y16-b",
    "Y16-c",
)
_MODULE = "acceptance/test_publish_remote_acceptance.py"
UNIT_CHECKS = {
    "Y11-a": f"{_MODULE}::test_y11_a_a_listing_that_disagrees_is_transport_incomplete_durably",
    "Y12-a": f"{_MODULE}::test_y12_a_a_crash_inside_push_leaves_the_mark_and_blocks_the_next_publish_durably",
    "Y12-b": f"{_MODULE}::test_y12_b_a_resume_after_the_mark_never_rereads_staging_durably",
    "Y12-c": f"{_MODULE}::test_y12_c_a_mark_disagreeing_with_its_export_fails_closed_durably",
    "Y13-a": f"{_MODULE}::test_y13_a_an_abandoned_transport_is_an_orphan_the_next_publish_supersedes_durably",
    "Y13-b": f"{_MODULE}::test_y13_b_an_orphan_named_by_an_abandoned_attempt_is_not_retired_durably",
    "Y13-c": f"{_MODULE}::test_y13_c_an_export_damaged_after_the_mark_closes_as_an_orphan_durably",
    "Y14-a": f"{_MODULE}::test_y14_a_a_stranded_marked_attempt_blocks_until_resumed_durably",
    "Y14-b": f"{_MODULE}::test_y14_b_an_attempt_without_a_mark_never_blocks_durably",
    "Y15-a": f"{_MODULE}::test_y15_a_a_crash_at_every_remote_step_resumes_to_one_binding_and_one_report_durably",
    "Y15-b": f"{_MODULE}::test_y15_b_a_remote_step_8_refusal_is_an_orphan_the_next_publish_names_durably",
    "Y16-a": f"{_MODULE}::test_y16_a_a_recipient_restores_admits_and_reads_the_current_publication_durably",
    "Y16-b": f"{_MODULE}::test_y16_b_sibling_publications_are_divergent_until_one_supersedes_both_durably",
    "Y16-c": f"{_MODULE}::test_y16_c_a_held_root_with_an_unreadable_record_file_refuses_capture_damaged_durably",
}
CO_CITED = ()


def unit_of(row: str) -> str:
    """Every arm homes its own unit; no row shares one."""
    if row not in DECLARATION_UNITS:
        raise ValueError(f"{row!r} is not a cut-42 row")
    return row


def _arm(row, module, assertion, before, after):
    return Arm(
        row=row,
        asserts=assertion,
        sabotage=Sabotage(module=module, before=before, after=after),
        checks=(UNIT_CHECKS[unit_of(row)],),
    )


CUT42_ARMS = (
    _arm(
        "Y11-a",
        "publish.py",
        "The remote's enumeration of the publication's whole namespace must equal the local listing of every export-root file and the sibling, by name and SHA-256.",
        "    if listing != expected:",
        "    if {name: listing.get(name) for name in expected} != expected:",
    ),
    _arm(
        "Y12-a",
        "publish.py",
        "The transport mark is written create-only after the export root validates and before the first push.",
        '    write_create_only(a.op / "transport.v1", encode_mark(mark))',
        "    pass",
    ),
    _arm(
        "Y12-b",
        "publish.py",
        "Once the transport mark exists a retry resumes at step 7 from the mark and never re-runs steps 1–6.",
        '    if (op / "transport.v1").is_file():',
        "    if False:",
    ),
    _arm(
        "Y12-c",
        "publish.py",
        "A mark that disagrees with the export root's manifest and chain, sibling identity or export marker fails closed with nothing written.",
        "    return not _export_agrees(r, mark)",
        "    return False",
    ),
    _arm(
        "Y13-a",
        "publication_doors.py",
        "An abandoned transport closes with a report carrying (corpus_id, marker), which the next publication's marker supersedes.",
        "        return (entry.outcome.corpus_id, entry.outcome.marker)",
        "        return None",
    ),
    _arm(
        "Y13-b",
        "publication_doors.py",
        "The fold reads an orphan as standing and retiring nothing, so the next publication supersedes every orphan its intent named.",
        "                    orphans.add(outcome.orphan)  # possibly shared: an orphan that retires nothing",
        "                    orphans.add(outcome.orphan)\n                    retired.update(intent.marker_tips)",
    ),
    _arm(
        "Y13-c",
        "publish.py",
        "An export root that fails evaluation against its own chain and sibling before push closes the attempt as a standing orphan.",
        '    return _evaluate_export(r, mark) != "validated"',
        "    return False",
    ),
    _arm(
        "Y14-a",
        "publish.py",
        "A publish refuses publish-unfinished before its intent while an unfinished attempt for the same view and destination has a transport mark.",
        '        if blocking:\n            raise PublicationRefused("publish-unfinished", tokens=blocking)',
        '        if False:\n            raise PublicationRefused("publish-unfinished", tokens=blocking)',
    ),
    _arm(
        "Y14-b",
        "publish.py",
        "An unfinished attempt without a transport mark never blocks a publish.",
        '        blocking = tuple(token for token in unfinished_attempts(writer, view, destination, seam) if (_op_dir(operations_root, token) / "transport.v1").is_file())',
        "        blocking = tuple(unfinished_attempts(writer, view, destination, seam))",
    ),
    _arm(
        "Y15-a",
        "publish.py",
        "A crash at any remote step resumes to exactly one binding and one report whose entries run staging, export, reveal, transport, binding.",
        "    entries = (*entries, PublicationTransportEntry(r.subject, transported))",
        "    entries = entries",
    ),
    _arm(
        "Y15-b",
        "publish.py",
        "A remote step-8 refusal carries remotely_revealed: true and is an orphan.",
        "        remotely_revealed=remote, clock=a.clock, seam=a.seam, port=a.port,",
        "        remotely_revealed=False, clock=a.clock, seam=a.seam, port=a.port,",
    ),
    _arm(
        "Y16-a",
        "transport.py",
        "A recipient restores and admits a raw remote copy against the transported artifact, and a copy missing any file never validates.",
        "        dirnames[:] = sorted(dirnames)",
        '        dirnames[:] = sorted(name for name in dirnames if name != ".#~chain")',
    ),
    _arm(
        "Y16-b",
        "publication_arrival.py",
        "Publication reading answers divergent-publication for sibling markers and the one tip again once a marker superseding both arrives.",
        "    return DivergentPublication(tips)",
        "    return CurrentPublication(*tips[0])",
    ),
    _arm(
        "Y16-c",
        "publication_arrival.py",
        "Publication reading refuses a held root with a record it cannot read or decode as capture-damaged.",
        '        raise PublicationReadingRefused("capture-damaged", corpus_id) from caught',
        "        return ()",
    ),
)
