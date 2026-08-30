"""Pure derivation: the captured view, the four subjects, and their receipts.

Every identity here is asserted as a **relation** — a projection digested under
its pinned domain, or two captures compared — never as a literal digest. The
shipped fixtures are normative content this slice keeps editing, so a pinned
constant would be a test of the fixture bytes rather than of the rule
(`test_world_rules.py` says the same thing about rule identities).

The reducers under test are the **shipped bytes**, loaded through the rules
store's own entry-point loader. That is deliberate: a test that imported
`rules_v1.producer` would exercise a module the store never runs, and would
miss exactly the failure the store exists to prevent — an implementation whose
behaviour depends on the installation around it.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, fields

import pytest

from beliefs.closure import RetractionEnumeration, build_closure
from beliefs.errors import RuleNonconformant
from beliefs.identity import v1
from beliefs.lineage import LineageSnapshot
from beliefs.world import derive, epoch, rules

# --- building captures -------------------------------------------------------


def state(seed: str) -> str:
    """A readable stand-in for a captured corpus-state identity."""
    return (seed * 64)[:64]


def digest(seed: str) -> str:
    """A readable stand-in for a rule, implementation, or subject identity."""
    return (seed * 64)[:64]


def record(
    address: str,
    *,
    uid: str | None = None,
    kind: str = "dataset",
    deprecated_ids: tuple[str, ...] = (),
    produces: tuple[str, ...] = (),
    retraction: derive.CapturedRetraction | None = None,
    certification: derive.CapturedCertification | None = None,
    coreference: derive.CapturedCoreference | None = None,
) -> derive.CapturedRecord:
    return derive.CapturedRecord(
        address=address,
        uid=uid if uid is not None else f"uid-{address}",
        kind=kind,
        deprecated_ids=deprecated_ids,
        produces=produces,
        retraction=retraction,
        certification=certification,
        coreference=coreference,
    )


def corpus(corpus_id: str, *records: derive.CapturedRecord, at: str = "a") -> derive.CapturedCorpus:
    return derive.CapturedCorpus(corpus_id=corpus_id, corpus_state=state(at), records=records)


def capture(*corpora: derive.CapturedCorpus) -> derive.Capture:
    return derive.Capture(corpora=corpora)


# --- running the shipped reducers --------------------------------------------


def shipped(symbol: str) -> rules.RuleBundle:
    for bundle in rules.shipped_rule_bundles():
        if bundle.symbol == symbol:
            return bundle
    raise AssertionError(f"no shipped bundle defines {symbol!r}")


def reduce_with(symbol: str, value: object) -> object:
    """Run one shipped implementation over one projection value, through the
    store's own ABI — so the value the rule sees is the frozen one."""
    return rules._load_entry_point(symbol, shipped(symbol).implementation)(value)


def snapshot_of(captured: derive.Capture) -> derive.ProducerSnapshot:
    return derive.producer_snapshot(reduce_with("derive_producer_snapshot", captured.rule_input()))


def enumeration_of(captured: derive.Capture) -> RetractionEnumeration:
    return derive.retraction_enumeration(reduce_with("enumerate_retractions", captured.rule_input()))


def inventory_of(captured: derive.Capture) -> derive.CertificationInventory:
    return derive.certification_inventory(reduce_with("enumerate_certifications", captured.rule_input()))


def coreference_of(captured: derive.Capture) -> derive.CoreferenceMap:
    return derive.coreference_map(reduce_with("reduce_coreference", captured.rule_input()))


# --- shared shapes -----------------------------------------------------------


def retraction(target: str, resolution: str = "upheld") -> derive.CapturedRetraction:
    return derive.CapturedRetraction(target=target, resolution=resolution)


def certification(kind: str, ref: str) -> derive.CapturedCertification:
    return derive.CapturedCertification(kind=kind, ref=ref)


def attestation(
    left: str,
    right: str,
    *,
    stance: int = 1,
    actor: str = "alice",
    grounds: str = "grounds-1",
    event_token: str = "event-1",
) -> derive.CapturedCoreference:
    return derive.CapturedCoreference(
        endpoints=(left, right),
        stance=stance,
        actor=actor,
        grounds=grounds,
        event_token=event_token,
    )


TWO_CORPORA = capture(
    corpus(
        "corpus-a",
        record("run:alpha", kind="run", produces=("dataset:two", "dataset:one")),
        record("dataset:one"),
        at="a",
    ),
    corpus(
        "corpus-b",
        record("run:beta", kind="run", produces=("dataset:one",)),
        record("dataset:two", deprecated_ids=("dataset:retired",)),
        at="b",
    ),
)


# --- Step 1: the address map and the producers map ---------------------------


class TestAddressMap:
    def test_every_live_address_maps_to_its_corpus_and_uid(self):
        assert derive.address_map(TWO_CORPORA) == {
            "dataset:one": ("corpus-a", "uid-dataset:one"),
            "dataset:retired": ("corpus-b", "uid-dataset:two"),
            "dataset:two": ("corpus-b", "uid-dataset:two"),
            "run:alpha": ("corpus-a", "uid-run:alpha"),
            "run:beta": ("corpus-b", "uid-run:beta"),
        }

    def test_a_deprecated_address_is_a_publication_member(self):
        # §7.2: a retired address answers out of the epoch, so it survives its
        # corpus being absent. Losing it is the defect this arm names.
        mapping = derive.address_map(TWO_CORPORA)
        assert mapping["dataset:retired"] == mapping["dataset:two"]

    def test_the_mapping_is_singular(self):
        # World §4.3's invariant: one address, one answer. A second claim on one
        # address is corruption, refused rather than resolved by insertion order.
        clash = capture(
            corpus("corpus-a", record("dataset:one"), at="a"),
            corpus("corpus-b", record("dataset:one", uid="uid-other"), at="b"),
        )
        with pytest.raises(ValueError, match="dataset:one"):
            derive.address_map(clash)

    def test_a_deprecated_entry_may_not_shadow_a_live_address(self):
        clash = capture(
            corpus(
                "corpus-a",
                record("dataset:one"),
                record("dataset:two", deprecated_ids=("dataset:one",)),
                at="a",
            )
        )
        with pytest.raises(ValueError, match="dataset:one"):
            derive.address_map(clash)

    def test_the_projection_is_sorted_and_encodable(self):
        projection = derive.address_map_projection(derive.address_map(TWO_CORPORA))
        assert projection == {
            "addresses": [
                {"address": "dataset:one", "corpus_id": "corpus-a", "uid": "uid-dataset:one"},
                {"address": "dataset:retired", "corpus_id": "corpus-b", "uid": "uid-dataset:two"},
                {"address": "dataset:two", "corpus_id": "corpus-b", "uid": "uid-dataset:two"},
                {"address": "run:alpha", "corpus_id": "corpus-a", "uid": "uid-run:alpha"},
                {"address": "run:beta", "corpus_id": "corpus-b", "uid": "uid-run:beta"},
            ]
        }
        assert v1.encode(projection)


class TestProducersMap:
    def test_every_produces_edge_contributes_its_run_under_its_dataset(self):
        assert dict(snapshot_of(TWO_CORPORA).producers) == {
            "dataset:one": ("run:alpha", "run:beta"),
            "dataset:two": ("run:alpha",),
        }

    def test_a_run_in_a_second_covered_corpus_is_not_omitted(self):
        # The omission arm: a reducer that stopped at the first corpus would
        # publish `dataset:one` with one producer instead of two.
        assert snapshot_of(TWO_CORPORA).producers["dataset:one"] == ("run:alpha", "run:beta")

    def test_the_same_edge_seen_twice_contributes_once(self):
        twice = capture(
            corpus(
                "corpus-a",
                record("run:alpha", kind="run", produces=("dataset:one", "dataset:one")),
                at="a",
            )
        )
        assert dict(snapshot_of(twice).producers) == {"dataset:one": ("run:alpha",)}

    def test_datasets_runs_and_coverage_are_sorted(self):
        unsorted = capture(
            corpus("corpus-b", record("run:zulu", kind="run", produces=("dataset:zeta",)), at="b"),
            corpus(
                "corpus-a",
                record("run:alpha", kind="run", produces=("dataset:zeta", "dataset:alpha")),
                at="a",
            ),
        )
        assert snapshot_of(unsorted).projection() == {
            "producers": [
                {"dataset": "dataset:alpha", "runs": ["run:alpha"]},
                {"dataset": "dataset:zeta", "runs": ["run:alpha", "run:zulu"]},
            ],
            "coverage": ["corpus-a", "corpus-b"],
        }

    def test_the_map_member_carries_the_producers_without_the_coverage(self):
        # §6.1 stores the map and the snapshot separately; only the snapshot
        # declares what it was built over.
        assert derive.producers_map_projection(snapshot_of(TWO_CORPORA).producers) == {
            "producers": [
                {"dataset": "dataset:one", "runs": ["run:alpha", "run:beta"]},
                {"dataset": "dataset:two", "runs": ["run:alpha"]},
            ]
        }


class TestSnapshotIsSemanticNotPositional:
    def test_moving_an_unchanged_entity_moves_the_receipt_but_not_the_snapshot(self):
        # `run:beta` moves from corpus-b to corpus-a. The producers map and the
        # declared coverage are unchanged, so the snapshot identity is unchanged
        # — that is what makes it semantic. Its location and both captured
        # states did change, so the address map and the receipt both move.
        here = capture(
            corpus("corpus-a", record("run:beta", kind="run", produces=("dataset:one",)), at="a"),
            corpus("corpus-b", at="b"),
        )
        there = capture(
            corpus("corpus-a", at="c"),
            corpus("corpus-b", record("run:beta", kind="run", produces=("dataset:one",)), at="d"),
        )

        assert snapshot_of(here).identity() == snapshot_of(there).identity()
        assert derive.address_map(here) != derive.address_map(there)
        assert here.corpus_states != there.corpus_states
        assert receipts_over(here)[0].identity() != receipts_over(there)[0].identity()

    def test_narrower_producer_coverage_moves_snapshot_and_belief(self):
        # corpus-b holds no `produces` edge, so narrowing coverage to corpus-a
        # leaves the producers map byte-identical. The coverage declaration is
        # itself a member of the snapshot identity, so the identity moves — and
        # because the snapshot identity is the epoch's one belief input, the
        # belief-input digest moves with it.
        wide = capture(
            corpus("corpus-a", record("run:alpha", kind="run", produces=("dataset:one",)), at="a"),
            corpus("corpus-b", record("dataset:one"), at="b"),
        )
        narrow = capture(corpus("corpus-a", record("run:alpha", kind="run", produces=("dataset:one",)), at="a"))

        assert dict(snapshot_of(wide).producers) == dict(snapshot_of(narrow).producers)
        assert snapshot_of(wide).coverage == ("corpus-a", "corpus-b")
        assert snapshot_of(narrow).coverage == ("corpus-a",)
        assert snapshot_of(wide).identity() != snapshot_of(narrow).identity()
        assert belief_digest(snapshot_of(wide)) != belief_digest(snapshot_of(narrow))


def belief_digest(snapshot: derive.ProducerSnapshot) -> str:
    """One proposition's belief-input digest with this snapshot supplied."""
    return build_closure(
        proposition="proposition:one",
        assessments=(),
        runs={},
        verifications=(),
        snapshot=LineageSnapshot(roots=(), bases={}, producers={}),
        producer_snapshot_identity=snapshot.identity(),
        retractions=RetractionEnumeration(found=(), coverage=("corpus-a",)),
        consulted=(),
        binding=(digest("1"), digest("2")),
    ).digest()


# --- Step 2: retraction, certification, and coreference ----------------------

RETRACTIONS = capture(
    corpus(
        "corpus-a",
        record("retraction:two", kind="retraction", retraction=retraction("dataset:one", "upheld")),
        record("retraction:one", kind="retraction", retraction=retraction("dataset:one", "overturned")),
        at="a",
    ),
    corpus(
        "corpus-b",
        record("retraction:three", kind="retraction", retraction=retraction("dataset:two", "upheld")),
        at="b",
    ),
)


class TestRetractionEnumeration:
    def test_every_retraction_record_is_visited(self):
        assert enumeration_of(RETRACTIONS).found == (
            ("retraction:one", "overturned"),
            ("retraction:three", "upheld"),
            ("retraction:two", "upheld"),
        )

    def test_several_retractions_of_one_target_are_all_found(self):
        # The target-loss arm: `retraction:one` and `retraction:two` name one
        # target, and an enumeration keyed by target would publish one of them.
        found = dict(enumeration_of(RETRACTIONS).found)
        assert {"retraction:one", "retraction:two"} <= set(found)

    def test_a_non_retraction_record_contributes_nothing(self):
        mixed = capture(
            corpus(
                "corpus-a",
                record("dataset:one"),
                record("retraction:one", kind="retraction", retraction=retraction("dataset:one", "upheld")),
                at="a",
            )
        )
        assert enumeration_of(mixed).found == (("retraction:one", "upheld"),)

    def test_the_enumeration_carries_its_coverage(self):
        assert enumeration_of(RETRACTIONS).coverage == ("corpus-a", "corpus-b")


class TestRetractionDiscoveryMap:
    def test_several_event_tokens_group_under_one_target(self):
        assert derive.retraction_discovery_map(RETRACTIONS) == {
            "dataset:one": ("retraction:one", "retraction:two"),
            "dataset:two": ("retraction:three",),
        }

    def test_retraction_map_is_bounded_by_coverage(self):
        # An enumeration is only as good as its stated scope. Dropping corpus-b
        # from coverage drops its retraction from the map *and* narrows the
        # coverage the enumeration declares, so the bound is visible rather than
        # silent.
        narrow = capture(RETRACTIONS.corpora[0])
        assert derive.retraction_discovery_map(narrow) == {
            "dataset:one": ("retraction:one", "retraction:two"),
        }
        assert enumeration_of(narrow).coverage == ("corpus-a",)
        assert enumeration_of(narrow).found == (
            ("retraction:one", "overturned"),
            ("retraction:two", "upheld"),
        )

    def test_the_projection_is_sorted_and_encodable(self):
        projection = derive.retraction_discovery_map_projection(derive.retraction_discovery_map(RETRACTIONS))
        assert projection == {
            "targets": [
                {"target": "dataset:one", "retractions": ["retraction:one", "retraction:two"]},
                {"target": "dataset:two", "retractions": ["retraction:three"]},
            ]
        }
        assert v1.encode(projection)


CERTIFICATIONS = capture(
    corpus(
        "corpus-a",
        record("cert:two", kind="instrument-certification", certification=certification("verification", "ref-2")),
        record("cert:one", kind="instrument-certification", certification=certification("assessment", "ref-1")),
        at="a",
    ),
    corpus(
        "corpus-b",
        record("cert:three", kind="instrument-certification", certification=certification("verification", "ref-1")),
        record("cert:four", kind="instrument-certification", certification=certification("verification", "ref-2")),
        at="b",
    ),
)


class TestCertificationInventory:
    def test_kinds_and_refs_are_sorted_and_distinct(self):
        assert inventory_of(CERTIFICATIONS).projection() == {
            "by_kind": [
                {"kind": "assessment", "refs": ["ref-1"]},
                {"kind": "verification", "refs": ["ref-1", "ref-2"]},
            ],
            "coverage": ["corpus-a", "corpus-b"],
        }

    def test_the_inventory_is_location_free(self):
        # `ref-2` is certified in both corpora and enters once, carrying no
        # corpus. Nothing in the projection names where a ref lives.
        by_kind = inventory_of(CERTIFICATIONS).projection()["by_kind"]
        assert b"corpus" not in v1.encode(by_kind)
        assert inventory_of(CERTIFICATIONS).by_kind["verification"] == ("ref-1", "ref-2")

    def test_the_inventory_is_resolution_free(self):
        # A captured certification carries a kind and a ref and nothing else;
        # whether the ref resolves is a property of the reading world.
        assert {one.name for one in fields(derive.CapturedCertification)} == {"kind", "ref"}


DUPLICATES = capture(
    corpus(
        "corpus-a",
        record(
            "coref:one",
            kind="coreference-attestation",
            coreference=attestation("address-b", "address-a", event_token="event-1"),
        ),
        record(
            "coref:two",
            kind="coreference-attestation",
            coreference=attestation("address-a", "address-b", event_token="event-2"),
        ),
        record(
            "coref:three",
            kind="coreference-attestation",
            coreference=attestation("address-a", "address-b", grounds="grounds-2", event_token="event-3"),
        ),
        record(
            "coref:four",
            kind="coreference-attestation",
            coreference=attestation(
                "address-a", "address-b", stance=-1, actor="bob", grounds="grounds-3", event_token="event-4"
            ),
        ),
        at="a",
    )
)


class TestCoreferenceReduction:
    def test_duplicate_submissions_do_not_add_weight(self):
        # `coref:one` and `coref:two` differ only in their event token, which is
        # outside the ruled distinct key, so they are one unit.
        assert dict(coreference_of(DUPLICATES).pairs) == {("address-a", "address-b"): (1, 3)}

    def test_endpoints_are_stored_sorted_whichever_way_they_were_submitted(self):
        reversed_only = capture(
            corpus("corpus-a", record("coref:one", coreference=attestation("address-z", "address-a")), at="a")
        )
        assert coreference_of(reversed_only).projection() == {
            "pairs": [{"endpoints": ["address-a", "address-z"], "balance": 1, "distinct_key_count": 1}]
        }

    def test_pairs_are_sorted(self):
        many = capture(
            corpus(
                "corpus-a",
                record("coref:one", coreference=attestation("address-c", "address-a")),
                record("coref:two", coreference=attestation("address-b", "address-a")),
                at="a",
            )
        )
        pairs = coreference_of(many).projection()["pairs"]
        assert isinstance(pairs, list)
        assert [pair["endpoints"] for pair in pairs] == [
            ["address-a", "address-b"],
            ["address-a", "address-c"],
        ]

    def test_the_map_carries_no_coverage_and_no_edge_state(self):
        # `active`, `inactive` and `indeterminate` are query-time states and
        # never members, and the coreference subject declares no coverage — so
        # the same attestations under two coverages are one identity.
        projection = coreference_of(DUPLICATES).projection()
        assert set(projection) == {"pairs"}
        pairs = projection["pairs"]
        assert isinstance(pairs, list)
        assert set(pairs[0]) == {"endpoints", "balance", "distinct_key_count"}

        wider = capture(DUPLICATES.corpora[0], corpus("corpus-b", at="b"))
        assert coreference_of(wider).identity() == coreference_of(DUPLICATES).identity()

    def test_the_map_type_carries_the_reductions_invariants_itself(self):
        # Not only the parser: a value built by hand digests just as readily as
        # one parsed from a rule's return, so an unordered pair would mint a
        # second, wrong identity for a reduction the rule got right.
        with pytest.raises(ValueError, match="left < right"):
            derive.CoreferenceMap(pairs={("address-b", "address-a"): (1, 1)})
        with pytest.raises(ValueError, match="unit-weight"):
            derive.CoreferenceMap(pairs={("address-a", "address-b"): (3, 2)})
        with pytest.raises(ValueError, match="no distinct key"):
            derive.CoreferenceMap(pairs={("address-a", "address-b"): (0, 0)})
        with pytest.raises(ValueError, match="two endpoints"):
            derive.CoreferenceMap(pairs={("address-a",): (1, 1)})  # pyright: ignore[reportArgumentType]


# --- Step 3: subject identities and the one receipt contract -----------------


class TestSubjectIdentities:
    def test_the_producer_snapshot_digests_its_projection_under_its_domain(self):
        snapshot = snapshot_of(TWO_CORPORA)
        assert derive.PRODUCER_SNAPSHOT_DOMAIN == "science.producer-snapshot.v1"
        assert snapshot.identity() == v1.digest(derive.PRODUCER_SNAPSHOT_DOMAIN, snapshot.projection())

    def test_the_retraction_enumeration_digests_its_projection_under_its_domain(self):
        enumeration = enumeration_of(RETRACTIONS)
        assert derive.RETRACTION_ENUMERATION_DOMAIN == "science.retraction-enumeration.v1"
        assert derive.retraction_enumeration_projection(enumeration) == {
            "found": [
                ["retraction:one", "overturned"],
                ["retraction:three", "upheld"],
                ["retraction:two", "upheld"],
            ],
            "coverage": ["corpus-a", "corpus-b"],
        }
        assert derive.retraction_enumeration_identity(enumeration) == v1.digest(
            derive.RETRACTION_ENUMERATION_DOMAIN, derive.retraction_enumeration_projection(enumeration)
        )

    def test_the_certification_inventory_digests_its_projection_under_its_domain(self):
        inventory = inventory_of(CERTIFICATIONS)
        assert derive.CERTIFICATION_INVENTORY_DOMAIN == "science.certification-inventory.v1"
        assert inventory.identity() == v1.digest(derive.CERTIFICATION_INVENTORY_DOMAIN, inventory.projection())

    def test_the_coreference_map_digests_its_projection_under_its_domain(self):
        coreference = coreference_of(DUPLICATES)
        assert derive.COREFERENCE_MAP_DOMAIN == "science.coreference-map.v1"
        assert coreference.identity() == v1.digest(derive.COREFERENCE_MAP_DOMAIN, coreference.projection())

    def test_the_four_domains_are_distinct(self):
        domains = (
            derive.PRODUCER_SNAPSHOT_DOMAIN,
            derive.RETRACTION_ENUMERATION_DOMAIN,
            derive.CERTIFICATION_INVENTORY_DOMAIN,
            derive.COREFERENCE_MAP_DOMAIN,
        )
        assert len(set(domains)) == 4

    def test_a_rule_return_round_trips_through_its_subject_value(self):
        # The subject value parses the rule's return and re-emits §7.6's exact
        # projection. Equality of the two is what licenses digesting the parsed
        # value rather than the bytes the rule happened to hand back.
        for parse, symbol in (
            (lambda produced: derive.producer_snapshot(produced).projection(), "derive_producer_snapshot"),
            (
                lambda produced: derive.retraction_enumeration_projection(derive.retraction_enumeration(produced)),
                "enumerate_retractions",
            ),
            (lambda produced: derive.certification_inventory(produced).projection(), "enumerate_certifications"),
            (lambda produced: derive.coreference_map(produced).projection(), "reduce_coreference"),
        ):
            for captured in (TWO_CORPORA, RETRACTIONS, CERTIFICATIONS, DUPLICATES):
                produced = reduce_with(symbol, captured.rule_input())
                assert parse(produced) == produced

    def test_a_rule_return_of_the_wrong_shape_is_nonconformant(self):
        with pytest.raises(RuleNonconformant):
            derive.producer_snapshot({"producers": [], "coverage": ["a"], "extra": []})
        with pytest.raises(RuleNonconformant):
            derive.retraction_enumeration({"found": [["ref"]], "coverage": []})
        with pytest.raises(RuleNonconformant):
            derive.certification_inventory({"by_kind": [{"kind": "k"}], "coverage": []})
        with pytest.raises(RuleNonconformant):
            derive.coreference_map({"pairs": [{"endpoints": ["b", "a"], "balance": 1, "distinct_key_count": 1}]})


BINDINGS = {
    "producer": (digest("1"), digest("2")),
    "retraction-enumeration": (digest("3"), digest("4")),
    "certification-enumeration": (digest("5"), digest("6")),
    "coreference-reduction": (digest("7"), digest("8")),
}


def receipts_over(captured: derive.Capture) -> tuple[derive.DerivationReceipt, ...]:
    return derive.derivation_receipts(
        snapshot=snapshot_of(captured),
        enumeration=enumeration_of(captured),
        inventory=inventory_of(captured),
        coreference=coreference_of(captured),
        corpus_states=captured.corpus_states,
        bindings=BINDINGS,
    )


class TestReceipts:
    def test_the_four_kinds_arrive_in_epoch_member_order(self):
        assert tuple(one.kind for one in receipts_over(TWO_CORPORA)) == (
            "producer",
            "retraction-enumeration",
            "certification-enumeration",
            "coreference-reduction",
        )
        assert tuple(one.member for one in receipts_over(TWO_CORPORA)) == tuple(epoch.RECEIPT_KINDS)

    def test_a_receipt_identity_digests_the_five_members_under_one_domain(self):
        one = receipts_over(TWO_CORPORA)[0]
        assert one.identity() == epoch.receipt_identity(
            one.kind, one.subject_identity, one.corpus_states, one.rule_identity, one.implementation_identity
        )
        assert one.identity() == v1.digest(
            epoch.RECEIPT_DOMAIN,
            [
                one.kind,
                one.subject_identity,
                [list(pair) for pair in sorted(one.corpus_states)],
                one.rule_identity,
                one.implementation_identity,
            ],
        )

    def test_the_kind_discriminant_keeps_the_four_subjects_disjoint(self):
        # One domain, four kinds: two receipts differing only in their kind have
        # different identities even over one subject identity.
        states = (("corpus-a", state("a")),)
        common = {
            "subject_identity": digest("9"),
            "corpus_states": states,
            "rule_identity": digest("1"),
            "implementation_identity": digest("2"),
        }
        producer = derive.DerivationReceipt(kind="producer", **common)
        coreference = derive.DerivationReceipt(kind="coreference-reduction", **common)
        assert producer.identity() != coreference.identity()

    def test_all_four_carry_the_same_states_and_their_exact_binding(self):
        produced = receipts_over(TWO_CORPORA)
        assert {one.corpus_states for one in produced} == {
            (("corpus-a", state("a")), ("corpus-b", state("b"))),
        }
        assert {one.kind: (one.rule_identity, one.implementation_identity) for one in produced} == BINDINGS

    def test_a_binding_set_that_is_not_the_four_kinds_refuses(self):
        with pytest.raises(ValueError, match="binding"):
            derive.derivation_receipts(
                snapshot=snapshot_of(TWO_CORPORA),
                enumeration=enumeration_of(TWO_CORPORA),
                inventory=inventory_of(TWO_CORPORA),
                coreference=coreference_of(TWO_CORPORA),
                corpus_states=TWO_CORPORA.corpus_states,
                bindings={"producer": (digest("1"), digest("2"))},
            )

    def test_a_subject_coverage_that_disagrees_with_the_captured_states_refuses(self):
        # §7.5: "the exact captured corpus-state identity for every covered
        # corpus". A subject declaring one coverage beside states naming
        # another is a receipt whose two halves describe two builds.
        wide = capture(
            corpus("corpus-a", record("run:alpha", kind="run", produces=("dataset:one",)), at="a"),
            corpus("corpus-b", at="b"),
        )
        narrow = capture(wide.corpora[0])
        for subject, pattern in (
            ({"snapshot": snapshot_of(narrow)}, "producer snapshot"),
            ({"enumeration": enumeration_of(narrow)}, "retraction enumeration"),
            ({"inventory": inventory_of(narrow)}, "certification inventory"),
        ):
            arguments = {
                "snapshot": snapshot_of(wide),
                "enumeration": enumeration_of(wide),
                "inventory": inventory_of(wide),
                "coreference": coreference_of(wide),
                "corpus_states": wide.corpus_states,
                "bindings": BINDINGS,
                **subject,
            }
            with pytest.raises(ValueError, match=pattern):
                derive.derivation_receipts(**arguments)  # pyright: ignore[reportArgumentType]

    def test_each_receipt_names_its_own_subject_identity(self):
        produced = {one.kind: one.subject_identity for one in receipts_over(TWO_CORPORA)}
        assert produced == {
            "producer": snapshot_of(TWO_CORPORA).identity(),
            "retraction-enumeration": derive.retraction_enumeration_identity(enumeration_of(TWO_CORPORA)),
            "certification-enumeration": inventory_of(TWO_CORPORA).identity(),
            "coreference-reduction": coreference_of(TWO_CORPORA).identity(),
        }

    def test_the_enumeration_and_the_inventory_live_in_their_receipts(self):
        produced = {one.kind: one for one in receipts_over(RETRACTIONS)}
        assert produced["retraction-enumeration"].enumeration == derive.retraction_enumeration_projection(
            enumeration_of(RETRACTIONS)
        )
        assert produced["certification-enumeration"].inventory == inventory_of(RETRACTIONS).projection()
        assert produced["producer"].enumeration is None
        assert produced["producer"].inventory is None
        assert produced["coreference-reduction"].enumeration is None
        assert produced["coreference-reduction"].inventory is None

    def test_the_projection_bearing_members_match_the_declared_key_sets(self):
        for one in receipts_over(RETRACTIONS):
            carried = set(epoch.RECEIPT_IDENTITY_KEYS)
            if one.enumeration is not None:
                carried.add("enumeration")
            if one.inventory is not None:
                carried.add("inventory")
            assert carried == set(epoch.RECEIPT_KEYS[one.member])

    def test_a_projection_on_the_wrong_kind_refuses(self):
        with pytest.raises(ValueError, match="enumeration"):
            derive.DerivationReceipt(
                kind="producer",
                subject_identity=digest("9"),
                corpus_states=(("corpus-a", state("a")),),
                rule_identity=digest("1"),
                implementation_identity=digest("2"),
                enumeration={"found": [], "coverage": []},
            )

    def test_repeated_or_unsorted_states_refuse(self):
        for states in (
            (("corpus-b", state("b")), ("corpus-a", state("a"))),
            (("corpus-a", state("a")), ("corpus-a", state("b"))),
        ):
            with pytest.raises(ValueError, match="corpus_states"):
                derive.DerivationReceipt(
                    kind="producer",
                    subject_identity=digest("9"),
                    corpus_states=states,
                    rule_identity=digest("1"),
                    implementation_identity=digest("2"),
                )


class TestBeliefBoundary:
    def test_the_coreference_receipt_carries_no_semantic_identity_or_belief_input(self):
        # §7.5: coreference is outside belief, so its receipt carries no
        # semantic identity. The contract is one shape for all four, so the
        # absence has to be a property of the *field set* — a receipt with
        # nowhere to put one cannot acquire one for the coreference kind alone.
        assert {one.name for one in fields(derive.DerivationReceipt)} == {
            "kind",
            "subject_identity",
            "corpus_states",
            "rule_identity",
            "implementation_identity",
            "enumeration",
            "inventory",
        }
        coreference = {one.kind: one for one in receipts_over(DUPLICATES)}["coreference-reduction"]
        assert coreference.subject_identity == coreference_of(DUPLICATES).identity()
        assert derive.BELIEF_INPUT_KIND != coreference.kind

    def test_the_snapshot_identity_is_the_epochs_only_belief_input(self):
        produced = receipts_over(TWO_CORPORA)
        assert derive.BELIEF_INPUT_KIND == "producer"
        assert derive.belief_input_identity(produced) == snapshot_of(TWO_CORPORA).identity()

    def test_belief_input_identity_refuses_a_set_without_exactly_one_producer(self):
        produced = receipts_over(TWO_CORPORA)
        with pytest.raises(ValueError, match="producer"):
            derive.belief_input_identity(tuple(one for one in produced if one.kind != "producer"))

    def test_receipt_outcomes_are_the_closed_four(self):
        assert derive.RECEIPT_OUTCOMES == ("validated", "refuted", "unresolvable", "malformed")


# --- Step 5: the shipped fixtures are normative ------------------------------


FAILURE_MODE_FIXTURES = {
    # Step 5's five named failure modes, each with the shipped fixture whose
    # expected bytes an implementation with that defect cannot produce.
    #
    # This is a *claim*, not documentation: `TestFixturesDiscriminate` runs a
    # reducer carrying each defect and asserts the named fixture is among the
    # ones that refuse it. A filename list on its own would prove nothing —
    # `rules._run_fixtures` only ever checks the shipped implementation, so a
    # fixture gutted down to its happy path stays green forever.
    #
    # `deprecated-address loss` is the one that is only half a rule's business:
    # publishing retired addresses is the address map's job and the address map
    # is not a rule (§5.2 names four), so the fixture pins the half a rule can
    # lose — the retired addresses ride in the captured view every reducer
    # reads, and are not producers. `TestAddressMap` covers the other half.
    "omission": "producer.every-corpus.yaml",
    "wrong sorting": "coreference.unsorted.yaml",
    "duplicate coreference weighting": "coreference.duplicates.yaml",
    "deprecated-address loss": "producer.deprecated-address.yaml",
    "retraction target loss": "retraction.several-per-target.yaml",
}


@dataclass(frozen=True)
class Mutation:
    """One deliberately defective reducer, and every shipped fixture of its
    rule that must refuse it.

    The set is exact in both directions. A fixture that refuses a defect it was
    not written for is worth knowing about, and a fixture that stops refusing
    the defect it exists for is the regression Step 5 is guarding against.
    """

    symbol: str
    source: bytes
    refused_by: frozenset[str]


MUTATIONS: dict[str, Mutation] = {
    "omission": Mutation(
        "derive_producer_snapshot",
        b'''
def derive_producer_snapshot(capture):
    producers = {}
    first = None
    for record in capture["records"]:
        if first is None:
            first = record["corpus_id"]
        if record["corpus_id"] != first:
            continue
        for dataset in record["produces"]:
            producers.setdefault(dataset, set()).add(record["address"])
    return {
        "producers": [
            {"dataset": d, "runs": sorted(r)} for d, r in sorted(producers.items())
        ],
        "coverage": sorted(capture["coverage"]),
    }
''',
        frozenset({"producer.basic.yaml", "producer.every-corpus.yaml"}),
    ),
    "deprecated-address loss": Mutation(
        "derive_producer_snapshot",
        b'''
def derive_producer_snapshot(capture):
    producers = {}
    for record in capture["records"]:
        for dataset in record["produces"]:
            for address in (record["address"], *record["deprecated_ids"]):
                producers.setdefault(dataset, set()).add(address)
    return {
        "producers": [
            {"dataset": d, "runs": sorted(r)} for d, r in sorted(producers.items())
        ],
        "coverage": sorted(capture["coverage"]),
    }
''',
        frozenset({"producer.deprecated-address.yaml"}),
    ),
    "retraction target loss": Mutation(
        "enumerate_retractions",
        b'''
def enumerate_retractions(capture):
    by_target = {}
    for record in capture["records"]:
        retraction = record["retraction"]
        if retraction is None:
            continue
        by_target[retraction["target"]] = (record["address"], retraction["resolution"])
    return {
        "found": [[ref, resolution] for ref, resolution in sorted(by_target.values())],
        "coverage": sorted(capture["coverage"]),
    }
''',
        frozenset({"retraction.several-per-target.yaml"}),
    ),
    "location leakage": Mutation(
        "enumerate_certifications",
        b'''
def enumerate_certifications(capture):
    by_kind = {}
    for record in capture["records"]:
        certification = record["certification"]
        if certification is None:
            continue
        key = certification["kind"] + "@" + record["corpus_id"]
        by_kind.setdefault(key, set()).add(certification["ref"])
    return {
        "by_kind": [{"kind": k, "refs": sorted(r)} for k, r in sorted(by_kind.items())],
        "coverage": sorted(capture["coverage"]),
    }
''',
        frozenset({"certification.basic.yaml", "certification.location-free.yaml"}),
    ),
    "duplicate coreference weighting": Mutation(
        "reduce_coreference",
        b'''
def reduce_coreference(capture):
    units = {}
    for record in capture["records"]:
        a = record["coreference"]
        if a is None:
            continue
        endpoints = tuple(sorted(a["endpoints"]))
        units.setdefault(endpoints, set()).add(
            (a["stance"], a["actor"], a["grounds"], a["event_token"])
        )
    return {
        "pairs": [
            {
                "endpoints": [left, right],
                "balance": sum(s for s, _a, _g, _e in d),
                "distinct_key_count": len(d),
            }
            for (left, right), d in sorted(units.items())
        ]
    }
''',
        frozenset({"coreference.basic.yaml", "coreference.duplicates.yaml"}),
    ),
    "wrong sorting": Mutation(
        "reduce_coreference",
        b'''
def reduce_coreference(capture):
    units = {}
    for record in capture["records"]:
        a = record["coreference"]
        if a is None:
            continue
        endpoints = tuple(a["endpoints"])
        units.setdefault(endpoints, set()).add((a["stance"], a["actor"], a["grounds"]))
    return {
        "pairs": [
            {
                "endpoints": [left, right],
                "balance": sum(s for s, _a, _g in d),
                "distinct_key_count": len(d),
            }
            for (left, right), d in units.items()
        ]
    }
''',
        frozenset(
            {"coreference.basic.yaml", "coreference.duplicates.yaml", "coreference.unsorted.yaml"}
        ),
    ),
}


def refusing_fixtures(symbol: str, source: bytes) -> frozenset[str]:
    """Which of `symbol`'s shipped fixtures this implementation fails.

    The verdict is the store's own, one fixture at a time:
    `rules._load_entry_point` gives the ABI a rule is actually run under, and
    `rules._run_fixtures` is the `v1.encode(produced) == v1.encode(expected)`
    comparison that decides conformance at install and at every resolution. A
    raise is a refusal too — an implementation that blows up on a fixture has
    not satisfied it, and `_run_fixtures` already folds that into
    `_RuleRefusal`.
    """
    invoke = rules._load_entry_point(symbol, source)
    refused: set[str] = set()
    for member in shipped(symbol).fixtures:
        try:
            rules._run_fixtures(symbol, invoke, (member,))
        except rules._RuleRefusal:
            refused.add(member[0])
    return frozenset(refused)


class TestFixturesDiscriminate:
    """Step 5's point: the fixtures are normative because they *catch* things.

    `rules._run_fixtures` only ever runs the shipped implementation, so nothing
    in the store notices a fixture that has stopped discriminating. These arms
    are that notice.
    """

    def test_every_shipped_implementation_satisfies_every_shipped_fixture(self):
        # The positive direction. Without it the arms below would still pass
        # against a fixture set that refuses everything, defect or not.
        for bundle in rules.shipped_rule_bundles():
            assert refusing_fixtures(bundle.symbol, bundle.implementation) == frozenset(), bundle.symbol

    @pytest.mark.parametrize("mode", sorted(MUTATIONS))
    def test_a_defective_reducer_is_refused_by_exactly_the_named_fixtures(self, mode):
        mutation = MUTATIONS[mode]
        assert refusing_fixtures(mutation.symbol, mutation.source) == mutation.refused_by

    @pytest.mark.parametrize("mode", sorted(FAILURE_MODE_FIXTURES))
    def test_each_named_failure_mode_is_caught_by_its_dedicated_fixture(self, mode):
        # This is what makes `FAILURE_MODE_FIXTURES` a claim rather than a list.
        assert FAILURE_MODE_FIXTURES[mode] in MUTATIONS[mode].refused_by


class TestShippedFixtures:
    def test_the_named_failure_modes_all_have_a_shipped_fixture(self):
        shipped_names = {name for bundle in rules.shipped_rule_bundles() for name, _content in bundle.fixtures}
        assert set(FAILURE_MODE_FIXTURES.values()) <= shipped_names

    def test_every_shipped_fixture_carries_a_captured_view(self):
        # One captured-record model: every fixture's input is the same shape,
        # so the four reducers really do read one enumeration pass.
        for bundle in rules.shipped_rule_bundles():
            for name, content in bundle.fixtures:
                supplied, _expected = rules._parse_fixture_document(name, content)
                assert isinstance(supplied, dict), name
                assert set(supplied) == {"coverage", "records"}, name
                for entry in supplied["records"]:
                    assert set(entry) == {
                        "address",
                        "certification",
                        "coreference",
                        "corpus_id",
                        "deprecated_ids",
                        "kind",
                        "produces",
                        "retraction",
                        "uid",
                    }, name

    def test_each_packaged_bundle_installs_and_evaluates_to_the_same_expected_bytes(self, tmp_path):
        from nodes.core.write_plan import DefaultExecutor

        from beliefs.world.registry import World, WorldConfig

        world = World(
            WorldConfig(tmp_path / "world", "f" * 32, ()),
            DefaultExecutor,
            chain_head=lambda root: pytest.fail(f"{root}: a derivation arm read a chain"),
            corpus_executor_factory=DefaultExecutor,
        )
        for bundle in rules.shipped_rule_bundles():
            binding = rules.install_rule_binding(world, bundle)
            held = rules._resolve_rule_binding(world, binding)
            assert held.source == bundle.implementation
            for name, content in bundle.fixtures:
                supplied, expected = rules._parse_fixture_document(name, content)
                assert v1.encode(held.invoke(supplied)) == v1.encode(expected), name

    def test_a_shipped_fixture_input_is_a_capture_projection(self):
        # The fixtures are normative for the *model*, not only for the rule: a
        # `Capture` built here projects into the shape the fixtures document.
        projection = TWO_CORPORA.rule_input()
        assert set(projection) == {"coverage", "records"}
        assert projection["coverage"] == ["corpus-a", "corpus-b"]
        records = projection["records"]
        assert isinstance(records, list)
        assert records[0] == {
            "address": "dataset:one",
            "certification": None,
            "coreference": None,
            "corpus_id": "corpus-a",
            "deprecated_ids": [],
            "kind": "dataset",
            "produces": [],
            "retraction": None,
            "uid": "uid-dataset:one",
        }
        assert v1.encode(projection["coverage"])


# --- purity ------------------------------------------------------------------


class TestPurity:
    def test_no_shipped_implementation_imports_or_opens_anything(self):
        # A reducer cannot reach a corpus root, a registry, a current pointer or
        # an installed default because it has no way to *name* one: the loader
        # execs it in a namespace holding only builtins, and there is no import
        # in the source to bring one in.
        forbidden = {"open", "__import__", "eval", "exec", "compile", "input", "globals", "vars"}
        for bundle in rules.shipped_rule_bundles():
            tree = ast.parse(bundle.implementation, filename=bundle.symbol)
            assert not [node for node in ast.walk(tree) if isinstance(node, ast.Import | ast.ImportFrom)]
            names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
            assert not names & forbidden, bundle.symbol

    def test_a_reducer_sees_only_immutable_values(self):
        # The rule ABI freezes the whole captured view, recursively: one
        # fixture's outcome cannot depend on an earlier one's mutations.
        source = (
            b"def look(capture):\n"
            b"    record = capture['records'][0]\n"
            b"    return {'kinds': [\n"
            b"        type(capture).__name__,\n"
            b"        type(capture['records']).__name__,\n"
            b"        type(record).__name__,\n"
            b"        type(record['deprecated_ids']).__name__,\n"
            b"    ]}\n"
        )
        entry = rules._load_entry_point("look", source)
        assert entry(TWO_CORPORA.rule_input()) == {
            "kinds": ["mappingproxy", "tuple", "mappingproxy", "tuple"]
        }

    def test_deriving_twice_from_one_capture_gives_one_answer(self):
        assert snapshot_of(TWO_CORPORA).identity() == snapshot_of(TWO_CORPORA).identity()
        assert derive.address_map(TWO_CORPORA) == derive.address_map(TWO_CORPORA)
        assert receipts_over(TWO_CORPORA) == receipts_over(TWO_CORPORA)

    def test_the_capture_model_refuses_a_repeated_corpus(self):
        with pytest.raises(ValueError, match="corpus-a"):
            capture(corpus("corpus-a", at="a"), corpus("corpus-a", at="b"))
