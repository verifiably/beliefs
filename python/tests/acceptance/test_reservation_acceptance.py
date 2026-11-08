"""Exposure events and reservation assignments over a registered durable corpus.

The design's three worked examples (`mm`'s 2026-11-06 phase-2 unmask event, `mm`'s
`## Assignment 2026-11-06`, sun's epoch assignment 17 with its `agent/K5` knowledge event),
a scoped sun reservation note, and a snapshot near the design's size estimate, each written
through the composition root's own writer onto the certified volume and read back from disk.

Values are the examples' real ones where the sources hold them: sun's three input digests,
the seven epoch bounds, assignment 17's instant, the `agent/K1` to `agent/K5` observers, and
the `mm` event's accession, release, attempt, freeze prefix and atoms event. Where the design
abbreviates a digest with `…` (the `mm` inputs, the freeze, the D1 atoms event), the digest here
is a **stand-in**: the sha256 of a label (extending the real prefix where one is given), plausible
in form and not the digest of any real file. `<HH:MM:SS>` and `<32 hex>` placeholders are filled
the same way.

`testing/cohort` (`fixtures/contracts/testing.yaml`, a sort bound to a dataset identity) stands
in for `mm/cohort`, and the testing claim's proposition for a sun hypothesis.
"""

from __future__ import annotations

import hashlib
from dataclasses import replace
from itertools import pairwise
from pathlib import Path

import pytest
from fixtures_cut3 import TESTING_CLAIM, TESTING_PROFILE
from fixtures_cut4 import path_for, reopen
from nodes.core.frontmatter import node_from_markdown, node_to_markdown
from nodes.core.node import Node
from profiles import pins_for

from beliefs import stored
from beliefs.audit import NO_EVIDENCE, audit_corpus
from beliefs.corpus import CorpusWriter, corpus_check
from beliefs.errors import ReservationRefused
from beliefs.permit import Authority, WritePermit
from beliefs.projection import project_claim
from beliefs.reservation import (
    OPEN,
    ExposureEvent,
    Group,
    IntervalUnit,
    ReservationAssignment,
    TermUnit,
    assignment_changes_of,
    assignment_head,
    exposure_events,
)
from beliefs.root import open_corpus

COHORT = "testing/cohort"  # stands in for `mm/cohort`
SESSION = "session:4c9a1e07d2b85f3364e0a9c71b2d8f5e"  # stand-in for `session:<32 hex>`: the writing session
RECONCILE_SESSION = "session:b71d3a9e40c2f6851e9a7d03c4b62f18"  # stand-in: the phase-2 reconcile session


def _stand_in(label: str, prefix: str = "") -> str:
    """A stand-in hex digest for a value the design abbreviates: the real `prefix` where one is
    given, extended to 64 hex from the sha256 of `label`. Not the digest of any real file."""
    return prefix + hashlib.sha256(label.encode("utf-8")).hexdigest()[: 64 - len(prefix)]


def _sha(label: str, prefix: str = "") -> str:
    return "sha256:" + _stand_in(label, prefix)


def _writer(root: Path) -> CorpusWriter:
    """The composition root's writer over the registered root, under the testing profile (whose
    `cohort` sort the term units name) and bound to a `session:` actor, as the examples'
    `recorded_by` and `assigned_by` are."""
    writer = open_corpus(root, authority=Authority(WritePermit.full(), SESSION), profile=TESTING_PROFILE)
    writer.adopt_manifest(profile=pins_for(TESTING_PROFILE))
    return writer


def _relations(node: Node) -> set[tuple[str, str]]:
    """The edges as a set (ruling R5: order is free)."""
    return {(relation.predicate, relation.target) for relation in node.relations}


def _read(**fields: object) -> ExposureEvent:
    defaults: dict[str, object] = {
        "channel": "read",
        "units": (),
        "effect": "exposing",
        "bound": (),
        "recorded_by": SESSION,
        "propositions": (),
        "evidence": (),
    }
    return ExposureEvent(**{**defaults, **fields})  # type: ignore[arg-type]


def _knowledge(
    observer: str, account: str, through: str, *, observed_at: str, evidence: tuple[str, ...]
) -> ExposureEvent:
    """A sun `agent/K<n>` entry: a knowledge channel, no subject, one interval reaching back to the
    start of time and ending at the date of use (or the stated cutoff)."""
    return ExposureEvent(
        channel="knowledge",
        subjects=(),
        units=(IntervalUnit(OPEN, through),),
        effect="exposing",
        read_class="training-knowledge",
        bound=(),
        account=account,
        observer=observer,
        recorded_by=SESSION,
        observed_at=observed_at,
        propositions=(),
        evidence=evidence,
    )


def _assignment(**fields: object) -> ReservationAssignment:
    defaults: dict[str, object] = {
        "scope": None,
        "applies": None,
        "predecessor": None,
        "evidence": (),
        "flagged": None,
        "account": None,
        "participants": (),
        "prior_runs": (),
        "assigned_by": SESSION,
    }
    return ReservationAssignment(**{**defaults, **fields})  # type: ignore[arg-type]


def _event_node(writer: CorpusWriter, value: ExposureEvent, title: str, body: str = "") -> Node:
    return writer.add(stored.exposure_event_node(value, title=title, body=body))


def _source(writer: CorpusWriter, accession: str) -> str:
    return writer.add(stored.source_node(title=accession, identifiers={"accession": accession})).id


# --- mm: the 2026-11-06 phase-2 unmask and `## Assignment 2026-11-06` --------------------------


def _mm_unmask(subject: str) -> ExposureEvent:
    """Ledger §7, 2026-11-06: GSE24080, cohort uams-tt2-tt3, phase-2 unmask completed."""
    return _read(
        subjects=(subject,),
        units=(TermUnit(COHORT, "uams-tt2-tt3"),),
        read_class="unmask",
        bound=(("freeze", _sha("mm freeze 3f3a832745fd2919", "3f3a832745fd2919")),),
        account=(
            "phase-2 unmask completed (release gse24080-pilot-v2r2-2026-11-06, attempt d3e989d0fadb422f)"
            " — exploratory description (design 2026-10-18)"
        ),
        observer=RECONCILE_SESSION,
        observed_at="2026-11-06T15:12:08Z",  # stand-in for <HH:MM:SS>
        evidence=("atoms-event:3d426b17308814dd4a97e7c44e8b6a300325506715a22b5d5af438cb0ece41a8",),
    )


def _mm_d1(subject: str) -> ExposureEvent:
    """Ledger §7, 2026-11-06: phase-2 inspection recorded (event 97e776294ae2b49b)."""
    return _read(
        subjects=(subject,),
        units=(TermUnit(COHORT, "uams-tt2-tt3"),),
        read_class="D1",
        account="phase-2 inspection recorded (event 97e776294ae2b49b) — exploratory description (design 2026-10-18)",
        observer=RECONCILE_SESSION,
        observed_at="2026-11-06T16:03:41Z",  # stand-in for <HH:MM:SS>
        evidence=("atoms-event:" + _stand_in("mm D1 atoms event", "97e776294ae2b49b"),),
    )


_HARVEST = (
    "arrayexpress",
    "biostudies",
    "cbioportal",
    "dbgap",
    "ega",
    "geo-gse",
    "geo-gsm",
    "gdc",
    "jga",
    "mmrf-commpass",
    "pride",
    "sra",
)  # stand-in names for the design's "12 harvest tables" (`harvest/…tsv`)


def _mm_inputs() -> tuple[tuple[str, str], ...]:
    """The 18 inputs left once the ledger digest becomes `events`; stand-in digests throughout."""
    names = [
        "amendment-3",
        "amendment-4",
        "amendment-5",
        "amendment-7",
        "catchments.yaml",
        *(f"harvest/{name}.tsv" for name in _HARVEST),
        "roster.yaml",
    ]
    return tuple(sorted((name, _sha(f"mm input {name}")) for name in names))


def _mm_groups() -> tuple[Group, ...]:
    """The two groups the design shows of the section's 516."""
    return (
        Group((TermUnit(COHORT, "a20-mm-patients-pone2015"),), "unresolved", "unresolved", None),
        Group(
            tuple(
                TermUnit(COHORT, term)
                for term in (
                    "bcd-25-0005-antigen-loss-cohort",
                    "friedrich-2023",
                    "leblay-2024",
                    "mm-antigen-escape-bcma-gprc5d",
                )
            ),
            "open",
            "discovery",
            None,
        ),
    )


_MM_ASSIGNED_AT = "2026-11-06T16:20:00Z"  # both sections; stand-in for <HH:MM:SS>


def _mm_chain(writer: CorpusWriter) -> tuple[ReservationAssignment, ReservationAssignment, str]:
    """The preceding 2026-11-06 section (a chain root that considered the unmask) and the section
    after the D1 event, which considers both and cites the D1 event; the same `assigned_at`."""
    subject = _source(writer, "GSE24080")
    unmask = _event_node(writer, _mm_unmask(subject), "GSE24080 cohort uams-tt2-tt3: phase-2 unmask completed").id
    d1 = _event_node(writer, _mm_d1(subject), "GSE24080 cohort uams-tt2-tt3: phase-2 D1 inspection").id
    common: dict[str, object] = {
        "chain": "mm-roster",
        "rule_name": "mm-phase-1-protocol-8",
        "rule_version": "amendment-7",
        "inputs": _mm_inputs(),
        "groups": _mm_groups(),
        "assigned_at": _MM_ASSIGNED_AT,
    }
    preceding = _assignment(**common, events=(unmask,))
    writer.add(stored.reservation_assignment_node(preceding, title="mm reservation assignment, 2026-11-06"))
    section = _assignment(**common, events=tuple(sorted((unmask, d1))), predecessor=preceding.id, evidence=(d1,))
    title = "mm reservation assignment, 2026-11-06 (phase-2 D1 on uams-tt2-tt3 recorded)"
    writer.supersede(stored.reservation_assignment_node(section, title=title), of=preceding.id)
    return preceding, section, d1


def test_the_mm_unmask_event_is_written_and_read_back(durable_root):
    writer = _writer(durable_root)
    subject = _source(writer, "GSE24080")
    value = _mm_unmask(subject)
    body = (
        "Release gse24080-pilot-v2r2-2026-11-06, attempt d3e989d0fadb422f. Exploratory\n"
        "description (design 2026-10-18). The roster entry was already exposed whole\n"
        "(ledger §4.1), so this read changed no role.\n"
    )
    minted = _event_node(writer, value, "GSE24080 cohort uams-tt2-tt3: phase-2 unmask completed", body)
    assert minted.id == value.id
    # The hand-written web-search line: three subjects, the whole study, an external task token.
    keats = tuple(sorted(_source(writer, accession) for accession in ("GSE36822", "GSE36823", "GSE36824")))
    search = _read(
        subjects=keats,
        read_class="web-search",
        account="result-bearing Keats 2012 abstract text in web search; whole-study exposure",
        observer="codex",
        observed_at="2026-11-06T18:30:00Z",  # stand-in: the line carries a date only
        evidence=("task:mm-7e6495",),
    )
    _event_node(writer, search, "GSE36822, GSE36823, GSE36824: Keats 2012 abstract in web search")

    view = reopen(durable_root)
    node = view.get(value.id)
    assert stored.exposure_event_value(node) == value
    assert (node.title, node.body.strip()) == ("GSE24080 cohort uams-tt2-tt3: phase-2 unmask completed", body.strip())
    assert _relations(node) == {("exposes", subject)}
    assert exposure_events(view, subject=subject) == (value,)
    assert exposure_events(view, subject=keats[1]) == (search,)
    assert exposure_events(view) == (value, search)
    assert _relations(view.get(search.id)) == {("exposes", ref) for ref in keats}


def test_the_mm_assignment_chain_supersedes_by_content_not_date(durable_root):
    writer = _writer(durable_root)
    subject = _source(writer, "GSE24080")
    unmask = _event_node(writer, _mm_unmask(subject), "unmask").id
    preceding = _assignment(
        chain="mm-roster",
        rule_name="mm-phase-1-protocol-8",
        rule_version="amendment-7",
        inputs=_mm_inputs(),
        groups=_mm_groups(),
        events=(unmask,),
        assigned_at=_MM_ASSIGNED_AT,
    )
    writer.add(stored.reservation_assignment_node(preceding, title="mm reservation assignment, 2026-11-06"))
    # A later date alone is no new assignment (ruling R3a): the derivation must change.
    dated = replace(preceding, predecessor=preceding.id, assigned_at="2026-11-06T23:59:59Z")
    with pytest.raises(ReservationRefused) as caught:
        writer.supersede(stored.reservation_assignment_node(dated, title="same section, later"), of=preceding.id)
    assert caught.value.code == "assignment-unchanged"

    d1 = _event_node(writer, _mm_d1(subject), "D1").id
    section = replace(preceding, events=tuple(sorted((unmask, d1))), predecessor=preceding.id, evidence=(d1,))
    assert section.assigned_at == preceding.assigned_at  # the same date, to the second
    writer.supersede(stored.reservation_assignment_node(section, title="after D1"), of=preceding.id)

    view = reopen(durable_root)
    assert section.id != preceding.id
    assert stored.reservation_assignment_value(view.get(section.id)) == section
    assert stored.reservation_assignment_value(view.get(preceding.id)) == preceding
    assert assignment_head(view, "mm-roster") == section
    assert assignment_changes_of(view, section.id) == ()
    assert assignment_changes_of(view, preceding.id) == ()
    assert _relations(view.get(section.id)) == {
        ("considers", unmask),
        ("considers", d1),
        ("evidenced-by", d1),
        (stored.SUPERSEDES, preceding.id),
    }
    assert _relations(view.get(preceding.id)) == {("considers", unmask)}


# --- sun: epoch assignments 16 and 17 and a reservation note --------------------------------------

_EPOCH_BOUNDS = (
    "2007-11-01T00:00:00Z",
    "2008-12-01T00:00:00Z",
    "2019-12-01T00:00:00Z",
    "2021-01-01T00:00:00Z",
    "2025-09-29T00:00:00Z",
    "2026-10-29T00:00:00Z",
)
_PROGRAM_ROLES = (
    ("open", "exploration"),  # X-pre24
    ("withheld", "guard"),  # G-24a
    ("reserved", "reserved (retrospective)"),  # R-24
    ("withheld", "guard"),  # G-24b
    ("open", "exploration"),  # X-25
    ("withheld", "guard"),  # G-P
    ("reserved", "reserved pool"),  # R-P
)


def _epochs(roles: tuple[tuple[str, str], ...]) -> tuple[Group, ...]:
    edges = (OPEN, *_EPOCH_BOUNDS, OPEN)
    return tuple(
        Group((IntervalUnit(start, end),), role, label, None)
        for (start, end), (role, label) in zip(pairwise(edges), roles, strict=True)
    )


_SUN_INPUTS = (
    ("boundary-table", "sha256:a4b5b8812c9e966f013c55655176cbd22531e7afd0c304cb93cc38e00e50e4a0"),
    ("named-series", "sha256:1d1e6f4b9e75fe219327ae93454d9526833fbbf0159976573a4acc8c2de64eca"),
    ("rule", "sha256:6504868faa3d230913d67b1b2ef7d7b7c3f06ef0e00726af14f327addee8d9ff"),
)


def _ledger_entries() -> tuple[ExposureEvent, ...]:
    """The `agent/K1` to `agent/K5` entries of the sun exposure ledger as knowledge events (observers
    and dates of use from the ledger; the accounts abridged). A subset of the ledger: its other entries
    would be events too, and change nothing here."""
    return (
        _knowledge(
            "claude-code/claude-opus-5-5",
            "agent/K1: general training knowledge, knowledge cutoff June 2026 (rule §8).",
            "2026-07-01T00:00:00Z",
            observed_at="2026-07-01T00:00:00Z",
            evidence=(),
        ),
        _knowledge(
            "codex/gpt-6-astra",
            "agent/K2: used 2026-10-29 for sun-eef745; no provider-stated cutoff, date of use (rule §8).",
            "2026-10-30T00:00:00Z",
            observed_at="2026-10-29T00:00:00Z",
            evidence=("task:sun-eef745",),
        ),
        _knowledge(
            "codex/gpt-6.1-sol",
            "agent/K3: used 2026-10-29 for sun-83c888; no provider-stated cutoff, date of use (rule §8).",
            "2026-10-30T00:00:00Z",
            observed_at="2026-10-29T00:00:00Z",
            evidence=("task:sun-83c888",),
        ),
        _knowledge(
            "codex/gpt-6-astra",
            "agent/K4: used 2026-10-29 by the OMNI and GOES work; no provider-stated cutoff (rule §8).",
            "2026-10-30T00:00:00Z",
            observed_at="2026-10-29T00:00:00Z",
            evidence=(),
        ),
        _knowledge(
            "agy/gemini-4-argon",
            "agent/K5: used 2026-11-06 for sun-7bfa16; no provider-stated cutoff, date of use (rule §8).",
            "2026-11-07T00:00:00Z",
            observed_at="2026-11-06T00:00:00Z",
            evidence=("task:sun-7bfa16",),
        ),
    )


_EXTENSION = (
    "Possible training exposure through the actual UTC date of use; no provider-stated cutoff,"
    " no specific learned result asserted (rule §8)."
)
_ASSIGNED_17 = "2026-11-07T14:40:51Z"


def _extensions() -> tuple[ExposureEvent, ExposureEvent]:
    """The 2026-11-07 date-of-use extensions for `agent/K3` and `agent/K5`; K5's is the design's example."""
    k3 = _knowledge(
        "codex/gpt-6.1-sol", _EXTENSION, _ASSIGNED_17, observed_at=_ASSIGNED_17, evidence=("task:sun-7bfa16",)
    )
    k5 = _knowledge(
        "agy/gemini-4-argon", _EXTENSION, _ASSIGNED_17, observed_at=_ASSIGNED_17, evidence=("task:sun-7bfa16",)
    )
    return k3, k5


_BODY_17 = (
    "Supersedes assignment 16 under unchanged rule version 3 after ledgering the\n"
    "2026-11-07 date-of-use extensions for agent/K5 and agent/K3 (sun-7bfa16). Epoch\n"
    "bounds, guards, prospective start and named series inherited unchanged.\n"
)


def _sun_program(writer: CorpusWriter) -> tuple[ReservationAssignment, ReservationAssignment, tuple[str, str]]:
    """Assignment 16 (a chain root over the K1–K5 entries) and assignment 17, its successor over the
    same seven epochs, which considers the two extensions as well and cites them as evidence."""
    earlier = tuple(sorted(_event_node(writer, event, "sun ledger entry").id for event in _ledger_entries()))
    k3, k5 = _extensions()
    extensions = (
        _event_node(writer, k3, "agent/K3 date-of-use extension, 2026-11-07").id,
        _event_node(writer, k5, "agent/K5 date-of-use extension, 2026-11-07").id,
    )
    sixteen = _assignment(
        chain="sun-epochs",
        rule_name="epoch-reservation-rule",
        rule_version="3",
        inputs=_SUN_INPUTS,
        events=earlier,
        groups=_epochs(_PROGRAM_ROLES),
        account="Supersedes assignment 15 after ledgering the agent/K5 entry; bounds and guards unchanged.",
        assigned_at="2026-11-06T12:00:00Z",  # stand-in: assignment 16's instant is not in the design
    )
    writer.add(stored.reservation_assignment_node(sixteen, title="sun epoch assignment 16"))
    seventeen = replace(
        sixteen,
        events=tuple(sorted((*earlier, *extensions))),
        predecessor=sixteen.id,
        evidence=tuple(sorted(extensions)),
        account=(
            "Inherits bounds, guards, prospective start and named series from assignment 16;"
            " no release, no new series, no revised minimum."
        ),
        assigned_at=_ASSIGNED_17,
    )
    writer.supersede(
        stored.reservation_assignment_node(seventeen, title="sun epoch assignment 17", body=_BODY_17), of=sixteen.id
    )
    return sixteen, seventeen, extensions


def test_the_sun_assignment_17_over_interval_units(durable_root):
    writer = _writer(durable_root)
    sixteen, seventeen, extensions = _sun_program(writer)

    view = reopen(durable_root)
    node = view.get(seventeen.id)
    read = stored.reservation_assignment_value(node)
    assert read == seventeen
    assert node.body.strip() == _BODY_17.strip()
    assert [group.units for group in read.groups] == [
        (IntervalUnit(OPEN, "2007-11-01T00:00:00Z"),),
        (IntervalUnit("2007-11-01T00:00:00Z", "2008-12-01T00:00:00Z"),),
        (IntervalUnit("2008-12-01T00:00:00Z", "2019-12-01T00:00:00Z"),),
        (IntervalUnit("2019-12-01T00:00:00Z", "2021-01-01T00:00:00Z"),),
        (IntervalUnit("2021-01-01T00:00:00Z", "2025-09-29T00:00:00Z"),),
        (IntervalUnit("2025-09-29T00:00:00Z", "2026-10-29T00:00:00Z"),),
        (IntervalUnit("2026-10-29T00:00:00Z", OPEN),),
    ]
    assert read.groups == sixteen.groups
    assert seventeen.id != sixteen.id  # the epochs are unchanged; `events` grew
    assert assignment_changes_of(view, seventeen.id) == ()
    assert assignment_head(view, "sun-epochs") == seventeen
    assert read.evidence == tuple(sorted(extensions))
    assert _relations(node) == {
        *(("considers", ref) for ref in seventeen.events),
        *(("evidenced-by", ref) for ref in extensions),
        (stored.SUPERSEDES, sixteen.id),
    }
    assert len(seventeen.events) == 7
    k5 = stored.exposure_event_value(view.get(extensions[1]))
    assert k5 == _extensions()[1]
    assert (k5.channel, k5.subjects, k5.units) == ("knowledge", (), (IntervalUnit(OPEN, _ASSIGNED_17),))
    assert _relations(view.get(k5.id)) == set()  # no subject, no proposition, no kernel evidence


def test_a_scoped_sun_reservation_note_applies_the_program_assignment(durable_root):
    writer = _writer(durable_root)
    _, program, _ = _sun_program(writer)
    hypothesis = writer.add(
        stored.proposition_node("sun-hypothesis", title="a sun hypothesis", claim=project_claim(TESTING_CLAIM))
    ).id
    # Per-hypothesis roles over the same seven intervals (illustrative: no hypothesis exists in sun yet).
    roles = (
        ("open", "exposed"),
        ("withheld", "guard"),
        ("unresolved", "unresolved"),
        ("withheld", "guard"),
        ("open", "exposed"),
        ("withheld", "guard"),
        ("reserved", "reserved"),
    )
    note = _assignment(
        chain="sun-epochs",
        rule_name="epoch-reservation-rule",
        rule_version="3",
        inputs=_SUN_INPUTS,
        events=program.events,
        scope=hypothesis,
        applies=program.id,
        groups=_epochs(roles),
        account=(
            "Per epoch: R-24 unresolved for this hypothesis (unknown-epoch ledger lines); R-P reserved."
            " Separation: the guards. Bounds chosen by the program rule at assignment 1, before any result."
        ),
        participants=tuple(sorted(("codex/gpt-6.1-sol", SESSION))),
        # stand-in: the phase-2b catalog publication commit, an earlier run the completion accounts for
        prior_runs=("commit:65266f068e33a975a2a2f26b84c294641eed1104",),
        assigned_at="2026-11-07T15:00:00Z",
    )
    writer.add(stored.reservation_assignment_node(note, title="sun reservation note: a sun hypothesis"))

    view = reopen(durable_root)
    assert stored.reservation_assignment_value(view.get(note.id)) == note
    assert assignment_head(view, "sun-epochs", scope=hypothesis) == note
    assert assignment_head(view, "sun-epochs") == program  # the program-level chain is a separate chain
    assert assignment_changes_of(view, note.id) == ()
    assert _relations(view.get(note.id)) == {
        *(("considers", ref) for ref in program.events),
        ("concerns", hypothesis),
        ("applies", program.id),
    }


# --- size and audit ---------------------------------------------------------------------------------

_GROUPS = 520
_EVENTS = 600
_ESTIMATE = 150_000  # the design's "near 150 KB" for ~500 groups and ~600 considered events


def _cohort(i: int) -> str:
    """A cohort term of the roster's typical length (`a20-mm-patients-pone2015`)."""
    return f"gse{24000 + i}-mm-cohort-{i:03d}"


def _snapshot_group(i: int) -> Group:
    unit = (TermUnit(COHORT, _cohort(i)),)
    if i % 3 == 0:
        return Group(unit, "open", "discovery", None)
    if i % 3 == 1:
        return Group(unit, "unresolved", "unresolved", None)
    return Group(unit, "reserved", "reserved (A1)", _sha(f"mm basis {i}"))


def test_a_snapshot_near_the_size_estimate_round_trips(durable_root):
    writer = _writer(durable_root)
    subject = _source(writer, "GSE24080")
    considered = tuple(
        sorted(
            _event_node(
                writer,
                _read(
                    subjects=(subject,),
                    units=(TermUnit(COHORT, _cohort(i % _GROUPS)),),
                    read_class="D1",
                    account=f"phase-2 inspection {i} — exploratory description (design 2026-10-18)",
                    observer=RECONCILE_SESSION,
                    observed_at=f"2026-11-{1 + i // 144:02d}T{(i // 6) % 24:02d}:{(i % 6) * 10:02d}:00Z",
                ),
                f"phase-2 inspection {i}",
            ).id
            for i in range(_EVENTS)
        )
    )
    assert len(set(considered)) == _EVENTS
    groups = tuple(_snapshot_group(i) for i in range(_GROUPS))  # term order is index order
    value = _assignment(
        chain="mm-roster",
        rule_name="mm-phase-1-protocol-8",
        rule_version="amendment-7",
        inputs=_mm_inputs(),
        events=considered,
        groups=groups,
        assigned_at=_MM_ASSIGNED_AT,
    )
    node = stored.reservation_assignment_node(value, title="mm reservation assignment, 520 groups")
    rendered = node_to_markdown(node)
    assert node_from_markdown(rendered) == node

    minted = writer.add(node)
    written = path_for(durable_root, minted.id).read_bytes()
    assert written == node_to_markdown(minted).encode("utf-8")
    view = reopen(durable_root)
    assert node_from_markdown(written.decode("utf-8")) == view.get(value.id)
    assert stored.reservation_assignment_value(view.get(value.id)) == value
    assert len(view.get(value.id).relations) == _EVENTS
    print(f"the {_GROUPS}-group record with {_EVENTS} considered events is {len(written)} bytes")
    assert _ESTIMATE / 2 < len(written) < _ESTIMATE * 2, f"{len(written)} bytes"


def test_corpus_check_is_clean_after_the_chain(durable_root):
    writer = _writer(durable_root)
    _, section, _ = _mm_chain(writer)
    view = reopen(durable_root)
    assert assignment_head(view, "mm-roster") == section
    assert corpus_check(view, TESTING_PROFILE) == ()
    assert audit_corpus(view, evidence=NO_EVIDENCE, profile=TESTING_PROFILE) == ()
