"""Frozen cut-47 declaration: 9 units and 9 independent mutation arms."""

from n2_arms import Arm, Sabotage

DECLARATION_UNITS = (
    "Y5-f",
    "Y17-q",
    "Y17-r",
    "Y17-s",
    "Y17-t",
    "Y17-u",
    "Y17-v",
    "Y17-w",
    "Y17-x",
)
UNIT_CHECKS = {
    "Y5-f": "test_owned_replica_publication.py::test_y5_f_declaration_validation",
    "Y17-q": "test_owned_replica_publication.py::test_y17_q_owned_replica",
    "Y17-r": "test_owned_replica_publication.py::test_y17_r_explicit_scope",
    "Y17-s": "test_owned_replica_publication.py::test_y17_s_captured_marker_veto",
    "Y17-t": "test_owned_replica_publication.py::test_y17_t_refusal_order",
    "Y17-u": "test_owned_replica_publication.py::test_y17_u_mixed_origins",
    "Y17-v": "test_owned_replica_publication.py::test_y17_v_preview_matches_freeze",
    "Y17-w": "test_session_publish_door.py::test_y17_w_scoped_ownership",
    "Y17-x": "test_owned_replica_publication.py::test_y17_x_frozen_owned_marker",
}
CO_CITED = ()


def unit_of(row: str) -> str:
    if row not in DECLARATION_UNITS:
        raise ValueError(f"{row!r} is not a cut-47 row")
    return row


def _arm(row, module, assertion, before, after):
    return Arm(
        row=row,
        asserts=assertion,
        sabotage=Sabotage(module=module, before=before, after=after),
        checks=(UNIT_CHECKS[unit_of(row)],),
    )


CUT47_ARMS = (
    _arm(
        "Y5-f",
        "publish.py",
        "Reject malformed ownership before preparation.",
        ("    _require_own_corpora(own_corpora)\n"),
        "",
    ),
    _arm(
        "Y17-q",
        "publish.py",
        "An explicitly own markerless replica contributes no carried origins.",
        ("        if holder not in own_corpora and type(admissions[holder].provenance) is ReplicaOf\n"),
        ("        if type(admissions[holder].provenance) is ReplicaOf\n"),
    ),
    _arm(
        "Y17-r",
        "publish.py",
        "An unselected declaration does not exempt selected foreign holders.",
        ("        if holder not in own_corpora and type(admissions[holder].provenance) is ReplicaOf\n    )\n"),
        ("        if not own_corpora and type(admissions[holder].provenance) is ReplicaOf\n    )\n"),
    ),
    _arm(
        "Y17-s",
        "publish.py",
        "Any captured marker vetoes declaration, even outside the recorded index.",
        (
            "        if holder in own_corpora and any(node.kind == MARKER_KIND for node in read.captured_records(holder)):\n"
        ),
        ("        if False and any(node.kind == MARKER_KIND for node in read.captured_records(holder)):\n"),
    ),
    _arm(
        "Y17-t",
        "publish.py",
        "Every admission is checked before sorted ownership marker refusals.",
        (
            "    for holder in sorted(grouped):\n"
            "        if holder not in admissions:\n"
            "            raise PublicationRefused(\n"
            '                "attribution-holder-unregistered",\n'
            "                corpus_ids=(holder,),\n"
            "                refs=tuple(sorted(grouped[holder])),\n"
            "            )\n"
            "    for holder in sorted(grouped):\n"
            "        if holder in own_corpora and any(node.kind == MARKER_KIND for node in read.captured_records(holder)):\n"
            "            raise PublicationRefused(\n"
            '                "attribution-own-source-invalid",\n'
            "                corpus_ids=(holder,),\n"
            "                refs=tuple(sorted(grouped[holder])),\n"
            '                field="marker-present",\n'
            "            )\n"
        ),
        (
            "    for holder in sorted(grouped):\n"
            "        if holder in own_corpora and any(node.kind == MARKER_KIND for node in read.captured_records(holder)):\n"
            "            raise PublicationRefused(\n"
            '                "attribution-own-source-invalid",\n'
            "                corpus_ids=(holder,),\n"
            "                refs=tuple(sorted(grouped[holder])),\n"
            '                field="marker-present",\n'
            "            )\n"
            "    for holder in sorted(grouped):\n"
            "        if holder not in admissions:\n"
            "            raise PublicationRefused(\n"
            '                "attribution-holder-unregistered",\n'
            "                corpus_ids=(holder,),\n"
            "                refs=tuple(sorted(grouped[holder])),\n"
            "            )\n"
        ),
    ),
    _arm(
        "Y17-u",
        "publish.py",
        "Mixed selections retain exact forwarded origins of the remaining carriers.",
        ("        if holder in sources:\n"),
        ("        if holder in sources and not own_corpora:\n"),
    ),
    _arm(
        "Y17-v",
        "publish.py",
        "Publish freezes the same own-only values preview returns.",
        ("        world, resolver, view, own_pins=load_manifest(writer.root).profile, own_corpora=own_corpora\n"),
        ("        world, resolver, view, own_pins=load_manifest(writer.root).profile\n"),
    ),
    _arm(
        "Y17-w",
        "session/writer.py",
        "Scoped publish forwards the exact declaration after preflight.",
        ("            hold=self._closing_hold,\n            own_corpora=own_corpora,\n"),
        ("            hold=self._closing_hold,\n"),
    ),
    _arm(
        "Y17-x",
        "publish.py",
        "Local and remote-with-snapshot reconstruction preserves frozen own-only shape.",
        ("        selection=tuple(i for i, _ in a.snapshot.records),\n        attributions=a.snapshot.attributions,\n"),
        (
            "        selection=tuple(i for i, _ in a.snapshot.records),\n"
            "        attributions=a.snapshot.attributions or ((a.snapshot.records[0][0], a.request.world_id, a.opened.intent.event_token),),\n"
        ),
    ),
)
