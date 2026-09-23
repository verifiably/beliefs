"""Frozen cut-39 declaration: thirteen units, fourteen sabotage arms (W17-p-e homes two)."""

from n2_arms import Arm, Sabotage

# Task 0's engine probes, as the frozen cut records them (§4, §5); they select
# the first row of the accounting table.
REPLACE_UNREGISTERED = "accepted"
ROLLBACK_MEANS = "patched create effect"
RETRY_AFTER_ROLLBACK = "same intent"

DECLARATION_UNITS = (
    "W17-p-a",
    "W17-p-b",
    "W17-p-c",
    "W17-p-d",
    "W17-p-e",
    "W17-p-f",
    "Y1-a",
    "Y1-b",
    "Y2-a",
    "Y3-a",
    "Y4-a",
    "Y4-b",
    "Y4-c",
)
_MODULE = "acceptance/test_publication_records_acceptance.py"
UNIT_CHECKS = {
    "W17-p-a": f"{_MODULE}::test_w17_p_a_a_second_writer_between_tip_read_and_append_is_refused_durably",
    "W17-p-b": f"{_MODULE}::test_w17_p_b_a_supersession_after_the_intent_commits_a_lawful_sibling_durably",
    "W17-p-c": f"{_MODULE}::test_w17_p_c_a_revision_past_its_anchor_is_not_present_durably",
    "W17-p-d": f"{_MODULE}::test_w17_p_d_mount_order_moves_neither_anchors_nor_tips_durably",
    "W17-p-e": f"{_MODULE}::test_w17_p_e_the_chain_not_the_directory_says_which_revisions_exist_durably",
    "W17-p-f": f"{_MODULE}::test_w17_p_f_a_rolled_back_creation_is_absent_and_its_retry_present_once_durably",
    "Y1-a": f"{_MODULE}::test_y1_a_version_and_door_refusals_durably",
    "Y1-b": f"{_MODULE}::test_y1_b_publication_records_are_inert_to_the_world_and_to_belief_durably",
    "Y2-a": f"{_MODULE}::test_y2_a_the_committed_binding_is_the_factory_of_its_decoded_intent_durably",
    "Y3-a": f"{_MODULE}::test_y3_a_the_audit_reads_publish_intents_by_their_domain_durably",
    "Y4-a": f"{_MODULE}::test_y4_a_one_fulfilling_submission_each_way_and_no_binding_on_refusal_durably",
    "Y4-b": f"{_MODULE}::test_y4_b_a_remotely_revealed_refusal_is_an_orphan_until_a_shared_publish_retires_it_durably",
    "Y4-c": f"{_MODULE}::test_y4_c_a_lost_refusal_report_refuses_rather_than_dropping_the_orphan_durably",
}
CO_CITED = ()


def unit_of(row: str) -> str:
    """W17-p-e2 shares W17-p-e's declaration unit."""
    unit = "W17-p-e" if row == "W17-p-e2" else row
    if unit not in DECLARATION_UNITS:
        raise ValueError(f"{row!r} is not a cut-39 row")
    return unit


def _arm(row, assertion, module, before, after):
    return Arm(
        row=row,
        asserts=assertion,
        sabotage=Sabotage(module=module, before=before, after=after),
        checks=(UNIT_CHECKS[unit_of(row)],),
    )


CUT39_ARMS = (
    _arm(
        "W17-p-a",
        "The binding door's guard recomputes the standing tips rather than trusting the intent's `binding_tips`.",
        "publication_doors.py",
        "        tips, markers = _judge(writer, resolver, opened, seam)",
        "        if True:\n"
        "            return None  # the intent's tips trusted, nothing recomputed\n"
        "        tips, markers = _judge(writer, resolver, opened, seam)",
    ),
    _arm(
        "W17-p-b",
        "The guard bounds the written root at the intent's position, not at its current tip.",
        "publication_doors.py",
        "        tips = standing_at(mounts, address, BINDING_KIND, written=written, position=opened.digest, anchors=intent.anchors, seam=seam)",
        "        tips = standing_at(mounts, address, BINDING_KIND, written=written, position=seam.inspect_written(written).tip, anchors=intent.anchors, seam=seam)",
    ),
    _arm(
        "W17-p-c",
        "The other roots' bound is the intent's anchor, not their current heads.",
        "coordination.py",
        "        found.append(ChainBound(root, corpus_id, view, placement.head, False))",
        "        found.append(ChainBound(root, corpus_id, view, len(view.entries) - 1, False))",
    ),
    _arm(
        "W17-p-d",
        "The anchors are ordered by `corpus_id`, not by mount path.",
        "publication_doors.py",
        "        anchors.sort(key=lambda anchor: anchor.corpus_id)",
        "        pass  # anchors left in mount-path order",
    ),
    _arm(
        "W17-p-e",
        "The present set is the chain's inventory, not the resolver's live read.",
        "coordination.py",
        "        records = present_records(bound, prefix, seam)",
        '        records = tuple((p.relative_to(bound.root).as_posix(), p.read_bytes()) for p in sorted((bound.root / kind).glob(f"{address.project}.{address.local}.*.md")))',
    ),
    _arm(
        "W17-p-e2",
        "A rewrite over an unregistered file is not a creation, so the rewritten file refuses `history-violated`.",
        "coordination.py",
        "    return initial.get(path, seam.absent_state) == seam.absent_state and seam.is_file(final[path])",
        "    return seam.is_file(final[path])",
    ),
    _arm(
        "W17-p-f",
        "Rolled-back registrations are not counted in the inventory's replay.",
        "coordination.py",
        "        if type(entry) is SettledEntryView and entry.committed and entry.registration in registrations:",
        "        if type(entry) is SettledEntryView and entry.registration in registrations:",
    ),
    _arm(
        "Y1-a",
        "`revise_coordination` refuses both publication kinds with `KindNotMintedHere`.",
        "corpus.py",
        "        if kind in PUBLICATION_KINDS:\n"
        '            raise KindNotMintedHere(f"{kind!r} is minted only by the publish doors")\n'
        '        self._authority.require("corpus-write", (kind,))\n'
        "        with self._operation:\n"
        "            self._require_pins_agree()\n"
        "            validated = self._validated_coordination_content(kind, content)\n"
        "            if not isinstance(address, CoordinationAddress) or address.revision is not None:",
        '        self._authority.require("corpus-write", (kind,))\n'
        "        with self._operation:\n"
        "            self._require_pins_agree()\n"
        "            validated = self._validated_coordination_content(kind, content)\n"
        "            if not isinstance(address, CoordinationAddress) or address.revision is not None:",
    ),
    _arm(
        "Y1-b",
        "A publication binding stays out of the world-index maps.",
        "world/epoch.py",
        "        if node.kind in stored.WORLD_KINDS",
        '        if node.kind in stored.WORLD_KINDS or node.kind == "publication-binding"',
    ),
    _arm(
        "Y2-a",
        "The committed binding is the factory over the intent, reading no clock.",
        "publication_doors.py",
        "    binding = binding_record(intent, corpus_id=corpus_id, marker=marker, artifact=artifact)",
        '    binding = binding_record(__import__("dataclasses").replace(intent, at=clock()), corpus_id=corpus_id, marker=marker, artifact=artifact)',
    ),
    _arm(
        "Y3-a",
        "`decode_intent` dispatches a publish payload by its domain.",
        "intents/shapes.py",
        '        if sniffed["domain"] == PUBLISH_INTENT_DOMAIN:',
        "        if False:",
    ),
    _arm(
        "Y4-a",
        "A refusing guard's fallback is written in place of the success plan, never beside it.",
        "publication_doors.py",
        '        return [writer._create_op(stored.act_report_node(report_of(judged["outcome"])))]',
        '        return [*plan, writer._create_op(stored.act_report_node(report_of(judged["outcome"])))]',
    ),
    _arm(
        "Y4-b",
        "Every remotely revealed refusal is an orphan, whatever its reason.",
        "publication_doors.py",
        '            if outcome["type"] != "bound" and outcome.get("remotely_revealed") is True:',
        '            if outcome["type"] == "predecessor-not-standing" and outcome.get("remotely_revealed") is True:',
    ),
    _arm(
        "Y4-c",
        "The fold refuses a publish intent whose report file is missing rather than skipping it.",
        "publication_doors.py",
        "        if type(records) is PositionRefused:\n            yield intent, records\n            continue",
        "        if type(records) is PositionRefused:\n            continue",
    ),
)
