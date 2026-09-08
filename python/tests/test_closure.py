"""G3's selected arms: the closure is the digest's meaning.

Deferred: the corpus-move negative — the slice has no corpora and no location
input, so that arm cannot fail here and waits on world persistence (cut 2
§4.2).
"""

import copy
import inspect
from dataclasses import replace

import pytest
from profiles import pins_for

from beliefs.closure import Closure, RetractionEnumeration, build_closure
from beliefs.consulted import CorpusPins, consulted_contracts
from beliefs.contract import domain
from beliefs.dataset import DatasetDeclaration, ResourceDeclaration
from beliefs.lineage import Basis, LineageSnapshot, Producer, Route
from beliefs.profile import compile_profile
from beliefs.record import AssessmentValue, RunInput, RunValue
from beliefs.verification import Verification


def closure_kwargs() -> dict:
    """A complete, valid kwargs dict for `build_closure`: two assessments on one
    proposition, each with a held observes input, an admitting verification, a
    two-root snapshot, a retraction enumeration, a consulted pair list, and
    `("science.belief.v1", "impl-1")`. Fresh objects every call — the values
    are frozen, but tests build modified copies from a clean baseline."""
    a1 = AssessmentValue(
        spec="spec-a", run="run-a", proposition="p1", outcome="supported", interpretation_rule="rule-1"
    )
    a2 = AssessmentValue(spec="spec-b", run="run-b", proposition="p1", outcome="refuted", interpretation_rule="rule-1")
    runs = {
        "run-a": RunValue(
            ref="run-a",
            spec="spec-a",
            inputs=(
                RunInput(
                    role="observes",
                    dataset=DatasetDeclaration(
                        resources=(ResourceDeclaration(name="r-a", digest=f"sha256:{'a' * 64}"),)
                    ),
                ),
            ),
        ),
        "run-b": RunValue(
            ref="run-b",
            spec="spec-b",
            inputs=(
                RunInput(
                    role="observes",
                    dataset=DatasetDeclaration(
                        resources=(ResourceDeclaration(name="r-b", digest=f"sha256:{'b' * 64}"),)
                    ),
                ),
            ),
        ),
    }
    verifications = (
        Verification(ref="v-a", assessment=a1.identity(), scope="clean-environment", verdict="passed"),
        Verification(ref="v-b", assessment=a2.identity(), scope="clean-environment", verdict="passed"),
    )
    snapshot = LineageSnapshot(
        roots=("d1", "d2"),
        bases={
            "d1": Basis(
                tag="single",
                routes=(
                    Route(
                        dataset="d1",
                        stored_run="run-p1",
                        resolved_run="run-p1",
                        stored_ancestor="d2",
                        resolved_ancestor="d2",
                        transforms=(),
                    ),
                ),
            ),
        },
        producers={"d1": (Producer(stored_run="run-p1", resolved_run="run-p1", transforms=()),)},
    )
    retractions = RetractionEnumeration(found=(("r-ref-1", "upheld"),), coverage=("corpus-1",))
    consulted = (("science", "sci-id-1"), ("testing", "testing-id-1"))
    return {
        "proposition": "p1",
        "assessments": (a1, a2),
        "runs": runs,
        "verifications": verifications,
        "snapshot": snapshot,
        "producer_snapshot_identity": "producer-snapshot-1",
        "retractions": retractions,
        "consulted": consulted,
        "binding": ("science.belief.v1", "impl-1"),
        "observed_facets": (),
    }


def test_recomputation_from_the_named_closure_is_byte_identical():
    first = build_closure(**closure_kwargs()).digest()
    second = build_closure(**closure_kwargs()).digest()
    assert first == second


# --- one-field mutations, one per projection key (G3's member-mutation arm) ---


def _mutate_facet(kwargs: dict) -> dict:
    kwargs = dict(kwargs)
    a1, a2 = kwargs["assessments"]
    kwargs["assessments"] = (replace(a1, estimate="mutated-estimate"), a2)
    return kwargs


def _mutate_proposition(kwargs: dict) -> dict:
    # Both assessments swapped off the queried proposition: `ours` becomes
    # empty, so the projected `propositions` list moves from `["p1"]` to `[]`.
    kwargs = dict(kwargs)
    a1, a2 = kwargs["assessments"]
    kwargs["assessments"] = (replace(a1, proposition="p1-other"), replace(a2, proposition="p1-other"))
    return kwargs


def _mutate_verification_verdict(kwargs: dict) -> dict:
    kwargs = dict(kwargs)
    v_a, v_b = kwargs["verifications"]
    kwargs["verifications"] = (replace(v_a, verdict="failed"), v_b)
    return kwargs


def _mutate_observes(kwargs: dict) -> dict:
    kwargs = dict(kwargs)
    runs = dict(kwargs["runs"])
    run_a = runs["run-a"]
    new_dataset = DatasetDeclaration(resources=(ResourceDeclaration(name="r-a", digest=f"sha256:{'c' * 64}"),))
    runs["run-a"] = replace(run_a, inputs=(RunInput(role="observes", dataset=new_dataset),))
    kwargs["runs"] = runs
    return kwargs


def _mutate_lineage(kwargs: dict) -> dict:
    kwargs = dict(kwargs)
    snapshot = kwargs["snapshot"]
    route = snapshot.bases["d1"].routes[0]
    unresolved = replace(route, resolved_run=None, resolved_ancestor=None)
    kwargs["snapshot"] = LineageSnapshot(
        roots=snapshot.roots, bases={"d1": Basis(tag="single", routes=(unresolved,))}, producers=snapshot.producers
    )
    return kwargs


def _mutate_producer_snapshot_identity(kwargs: dict) -> dict:
    kwargs = dict(kwargs)
    kwargs["producer_snapshot_identity"] = "producer-snapshot-2"
    return kwargs


def _mutate_retraction_resolution(kwargs: dict) -> dict:
    kwargs = dict(kwargs)
    retractions = kwargs["retractions"]
    kwargs["retractions"] = RetractionEnumeration(found=(("r-ref-1", "overturned"),), coverage=retractions.coverage)
    return kwargs


def _mutate_implementation_identity(kwargs: dict) -> dict:
    # Also P3's positive: the belief digest is a function of the binding.
    kwargs = dict(kwargs)
    rule, _impl = kwargs["binding"]
    kwargs["binding"] = (rule, "impl-2")
    return kwargs


def _mutate_consulted(kwargs: dict) -> dict:
    kwargs = dict(kwargs)
    consulted = kwargs["consulted"]
    namespace, _identity = consulted[0]
    kwargs["consulted"] = ((namespace, "sci-id-2"), *consulted[1:])
    return kwargs


MEMBER_MUTATIONS = [
    ("assessment_facets", _mutate_facet),
    ("propositions", _mutate_proposition),
    ("verifications", _mutate_verification_verdict),
    ("observes", _mutate_observes),
    ("lineage", _mutate_lineage),
    ("producer_snapshot", _mutate_producer_snapshot_identity),
    ("retractions", _mutate_retraction_resolution),
    ("policy_binding", _mutate_implementation_identity),
    ("consulted", _mutate_consulted),
]


@pytest.mark.parametrize(("key", "mutate"), MEMBER_MUTATIONS, ids=[key for key, _ in MEMBER_MUTATIONS])
def test_each_member_moves_the_digest(key, mutate):
    baseline = build_closure(**closure_kwargs()).digest()
    mutated = build_closure(**mutate(closure_kwargs())).digest()
    assert mutated != baseline, f"projection key {key!r} did not move the digest"


def test_the_keyed_facet_permutation_moves_it():
    # a1 supported + a2 refuted (baseline) vs a1 refuted + a2 supported: the
    # bag of facet digests is identical (same two outcomes occur once each,
    # against identical proposition/interpretation_rule), but the pairing with
    # each assessment's identity differs.
    baseline = build_closure(**closure_kwargs()).digest()
    kwargs = closure_kwargs()
    a1, a2 = kwargs["assessments"]
    assert a1.outcome == "supported"
    assert a2.outcome == "refuted"
    kwargs["assessments"] = (replace(a1, outcome="refuted"), replace(a2, outcome="supported"))
    swapped = build_closure(**kwargs).digest()
    assert swapped != baseline


def test_a_producing_run_deletion_moves_it():
    baseline = build_closure(**closure_kwargs()).digest()
    kwargs = closure_kwargs()
    snapshot = kwargs["snapshot"]
    route = snapshot.bases["d1"].routes[0]
    deleted = replace(route, resolved_run=None, resolved_ancestor=None)
    assert deleted.stored_run == route.stored_run
    assert deleted.stored_ancestor == route.stored_ancestor
    kwargs["snapshot"] = LineageSnapshot(
        roots=snapshot.roots, bases={"d1": Basis(tag="single", routes=(deleted,))}, producers=snapshot.producers
    )
    assert build_closure(**kwargs).digest() != baseline


def test_a_second_producer_moves_it():
    baseline = build_closure(**closure_kwargs()).digest()
    kwargs = closure_kwargs()
    snapshot = kwargs["snapshot"]
    producers = dict(snapshot.producers)
    producers["d1"] = (*producers["d1"], Producer(stored_run="run-p2", resolved_run="run-p2", transforms=()))
    kwargs["snapshot"] = LineageSnapshot(roots=snapshot.roots, bases=snapshot.bases, producers=producers)
    assert build_closure(**kwargs).digest() != baseline


def test_a_narrower_coverage_snapshot_moves_it():
    # `producer_snapshot_identity` differs — the identity covers the coverage,
    # so in-slice this is the same mechanism as the member-mutation case above;
    # banked here under its own name (D §5.1's coverage arm).
    baseline = build_closure(**closure_kwargs()).digest()
    kwargs = closure_kwargs()
    kwargs["producer_snapshot_identity"] = "narrower-coverage-producer-snapshot"
    assert build_closure(**kwargs).digest() != baseline


def test_the_same_binding_resolves_identically_elsewhere():
    # P3 negative: the digest is a function of the closure kwargs only.
    parameters = inspect.signature(build_closure).parameters
    assert set(parameters) == {
        "proposition",
        "assessments",
        "runs",
        "verifications",
        "snapshot",
        "producer_snapshot_identity",
        "retractions",
            "consulted",
            "binding",
            "observed_facets",
        }
    assert all(p.kind is inspect.Parameter.KEYWORD_ONLY for p in parameters.values())

    here = build_closure(**closure_kwargs()).digest()
    elsewhere = build_closure(**closure_kwargs()).digest()
    assert here == elsewhere


# --- M6/M8 completions and D6's arms: the consulted member ---


def _successor_document(document: dict, predecessor, **sections) -> dict:
    # Cut 1's exact document-mutation pattern
    # (test_domain_contract.py::TestSuccession.successor_document).
    successor = copy.deepcopy(document)
    successor["lineage"] = {"successor": predecessor.content_identity}
    successor["version"] = predecessor.version + 1
    successor.update(sections)
    return successor


def test_an_additive_successor_moves_consulted_digests(base_contract, testing_document):
    # M6: the real succession path, not a hand-typed string — the "additive
    # successor" is the loaded artifact.
    genesis = domain.parse_domain_contract(testing_document, source="<test>", base=base_contract, predecessor=None)
    operators = copy.deepcopy(testing_document["operators"])
    operators["precedes"] = {
        "arity": 2,
        "arg_sorts": ["entity", "entity"],
        "sign_apt": False,
        "layers": ["structural"],
        "dimensions": [],
    }
    document = _successor_document(testing_document, genesis, operators=operators)
    successor = domain.parse_domain_contract(document, source="<test>", base=base_contract, predecessor=genesis)
    assert set(successor.operators) == {"affects", "subtype-of", "correlates-with", "measured-by", "precedes"}

    kwargs = closure_kwargs()
    kwargs["consulted"] = (("testing", genesis.content_identity),)
    baseline = build_closure(**kwargs).digest()
    kwargs["consulted"] = (("testing", successor.content_identity),)
    mutated = build_closure(**kwargs).digest()
    assert mutated != baseline


def test_an_editorial_bump_moves_the_belief_digest(base_contract, testing_document):
    # M8's editorial-bump digest half: cut 1's editorial-change fixture
    # pattern (test_domain_contract.py::TestSuccession
    # ::test_an_editorial_change_is_accepted_and_moves_contract_identity).
    genesis = domain.parse_domain_contract(testing_document, source="<test>", base=base_contract, predecessor=None)
    operators = copy.deepcopy(testing_document["operators"])
    operators["affects"]["description"] = "Reworded. Meaning-bearing fields untouched."
    document = _successor_document(testing_document, genesis, operators=operators)
    successor = domain.parse_domain_contract(document, source="<test>", base=base_contract, predecessor=genesis)
    assert successor.content_identity != genesis.content_identity  # editorial, still moves contract identity

    kwargs = closure_kwargs()
    kwargs["consulted"] = (("testing", genesis.content_identity),)
    baseline = build_closure(**kwargs).digest()
    kwargs["consulted"] = (("testing", successor.content_identity),)
    mutated = build_closure(**kwargs).digest()
    assert mutated != baseline


def _bumped(base_contract, testing_document, description: str):
    document = copy.deepcopy(testing_document)
    document["description"] = description
    testing = domain.parse_domain_contract(document, source="<test>", base=base_contract, predecessor=None)
    return compile_profile(base_contract, [testing])


def test_an_activated_but_unconsulted_bump_is_absent(base_contract, testing_document):
    # M8 negative half + D6: an extra pinned-but-unread namespace is bumped;
    # the walk output — and hence the digest — is unchanged.
    profile = _bumped(base_contract, testing_document, "v1")
    real = pins_for(profile)
    pins_v1 = CorpusPins(science_contract=real.science_contract, domains={**real.domains, "unrelated": "unrelated:" + "1" * 64})
    pins_v2 = CorpusPins(science_contract=real.science_contract, domains={**real.domains, "unrelated": "unrelated:" + "2" * 64})
    consulted_v1 = consulted_contracts(
        claims={}, profile=profile, node_corpus={}, pins={"c1": pins_v1}, closure_nodes=()
    )
    consulted_v2 = consulted_contracts(
        claims={}, profile=profile, node_corpus={}, pins={"c1": pins_v2}, closure_nodes=()
    )
    assert consulted_v1 == consulted_v2
    assert all(namespace != "unrelated" for namespace, _ in consulted_v1)

    kwargs = closure_kwargs()
    kwargs["consulted"] = consulted_v1
    baseline = build_closure(**kwargs).digest()
    kwargs["consulted"] = consulted_v2
    assert build_closure(**kwargs).digest() == baseline


def test_the_base_contract_arm_at_the_eligibility_hinge(base_contract, testing_document, base_contract_path):
    # D6: bump the *base* contract editorially and pin the bumped profile;
    # the digest moves even though this closure reads no base-profile facet.
    # The base parser takes exact top-level fields, so the editorial edit
    # goes on a facet's `description`, which `contract/facets.py` accepts.
    import yaml

    from beliefs.contract.base import parse_base_contract

    document = yaml.safe_load(base_contract_path.read_text(encoding="utf-8"))
    document["facets"]["empirical-observation"]["description"] = "bumped for the eligibility-hinge arm"
    bumped_base = parse_base_contract(document, source="<bumped base>")
    testing_v1 = domain.parse_domain_contract(testing_document, source="<test>", base=base_contract, predecessor=None)
    testing_v2 = domain.parse_domain_contract(testing_document, source="<test>", base=bumped_base, predecessor=None)
    profile_v1 = compile_profile(base_contract, [testing_v1])
    profile_v2 = compile_profile(bumped_base, [testing_v2])
    consulted_v1 = consulted_contracts(
        claims={}, profile=profile_v1, node_corpus={}, pins={"c1": pins_for(profile_v1)}, closure_nodes=()
    )
    consulted_v2 = consulted_contracts(
        claims={}, profile=profile_v2, node_corpus={}, pins={"c1": pins_for(profile_v2)}, closure_nodes=()
    )

    kwargs = closure_kwargs()
    kwargs["consulted"] = consulted_v1
    baseline = build_closure(**kwargs).digest()
    kwargs["consulted"] = consulted_v2
    assert build_closure(**kwargs).digest() != baseline


def test_reinterpretation_without_byte_changes_still_moves():
    # D6 negative: same records byte-for-byte, different consulted identity →
    # different digest. Two beliefs can never share one digest.
    kwargs = closure_kwargs()
    baseline = build_closure(**kwargs).digest()
    kwargs = closure_kwargs()
    kwargs["consulted"] = tuple(
        (namespace, "testing-id-reinterpreted" if namespace == "testing" else identity)
        for namespace, identity in kwargs["consulted"]
    )
    mutated = build_closure(**kwargs).digest()
    assert mutated != baseline


def test_closure_is_sealed_against_subclassing():
    from beliefs.errors import SubclassRefused

    with pytest.raises(SubclassRefused):

        class Subclass(Closure):  # type: ignore[misc]
            pass
