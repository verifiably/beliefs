"""Cut 20: the declared facet boundary over registered durable corpora."""
from __future__ import annotations

import copy
import inspect
import shutil
import tempfile
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path

import pytest
from authority import ACTOR, FULL
from coordination_fixtures import coordination_contract
from fixtures_cut4 import raw_write, reopen
from nodes.core.errors import UnknownKindError
from nodes.core.node import Node
from nodes.core.registry import KindSpec, Registry, ShapeSpec
from nodes.core.relations import Relation
from profiles import BASE, WITH_BIOLOGY, pins_for
from test_dataset_revision import ALICE, BOB, revised
from test_durable_families import chain_entries
from test_facet_seams import IMPORT, PINNED, acquired, producing

from beliefs import stored
from beliefs.contract import parse_domain_contract
from beliefs.contract.practice import load_practice, parse_practice
from beliefs.corpus import CorpusWriter, corpus_check, eligibility_refusal
from beliefs.errors import (
    AcquisitionBoundaryRefused,
    ActorMismatch,
    ContractMismatch,
    FacetPayloadRefused,
    ImportRefused,
    MalformedContract,
    ProfileError,
    ReviseOutsideAllowlist,
    ValidationRefused,
)
from beliefs.profile import compile_profile, shipped_base_contract
from beliefs.root import init_corpus_root, metadata_root_for, open_corpus


@pytest.fixture()
def corpora(work_directory):
    roots = []
    def make(*, authority=FULL, profile=BASE):
        root = Path(tempfile.mkdtemp(prefix="facet-", dir=work_directory))
        roots.append(root)
        init_corpus_root(root, authority=authority)
        writer = open_corpus(root, authority=authority, profile=profile)
        writer.adopt_manifest(profile=pins_for(profile))
        return writer
    yield make
    for root in roots:
        shutil.rmtree(root)
        shutil.rmtree(metadata_root_for(root))


def contents(root):
    return {p.relative_to(root): sha256(p.read_bytes()).hexdigest() for p in root.rglob("*") if p.is_file()}


@contextmanager
def refused(writer, error, **kwargs):
    before, head = contents(writer.root), chain_entries(writer.root)[-1][0]
    with pytest.raises(error, **kwargs) as caught:
        yield caught
    assert contents(writer.root) == before
    assert chain_entries(writer.root)[-1][0] == head


def test_d2_interpretation_is_separable_from_identity_durably(corpora):
    from nodes.core.projection import to_canonical_json

    from beliefs.dataset import dataset_address
    from beliefs.world import corpus_state_identity
    w = corpora(profile=WITH_BIOLOGY)
    original = w.add(acquired("d", ACTOR))
    address = dataset_address(stored.dataset_declaration(original))
    states = [corpus_state_identity(w.root)]
    identities = [to_canonical_json(original)]
    current = original
    for axis in ("rows", "columns"):
        current = w.revise(revised(current, **{"biology/gene-axis": {"axis": axis}}))
        assert current.id == original.id and current.uid == original.uid
        assert dataset_address(stored.dataset_declaration(current)) == address
        states.append(corpus_state_identity(w.root))
        identities.append(to_canonical_json(reopen(w.root).get(current.id)))
    assert len(set(states)) == len(set(identities)) == 3
    assert [n.id for n in reopen(w.root).iter_stored()] == [original.id]
    different = stored.dataset_node("different", title="different", resources=[{"name": "m", "digest": "sha256:" + "2" * 64}])
    assert dataset_address(stored.dataset_declaration(w.add(different))) != address


def test_d4_one_kindspec_per_kind_compiled_from_the_profile(corpora, monkeypatch, testing_document):
    w = corpora()
    calls = []
    register = Registry.register
    def counted(self, spec):
        calls.append(spec.name)
        return register(self, spec)
    monkeypatch.setattr(Registry, "register", counted)
    domain = parse_domain_contract(testing_document, source="fixture", base=shipped_base_contract(), predecessor=None)
    profile = compile_profile(shipped_base_contract(), [domain], coordination=coordination_contract())
    assert "testing/axis" in profile.facets_of("dataset")
    assert sorted(calls) == sorted(profile.kinds) and len(calls) == len(set(calls))
    for kind, compiled in profile.kinds.items():
        profile.validate_document(Node(id=f"{kind}:x", kind=kind, title="x", facets={key: {} for key, use in compiled.facets.items() if use.required}))
    with pytest.raises(UnknownKindError):
        profile.validate_document(Node(id="divergence:x", kind="divergence", title="x"))
    assert set(stored.WORLD_RELATIONS) == {name for name, decl in shipped_base_contract().relations.items() if decl.group == "world"}
    assert "WORLD_KINDS: tuple[str, ...] = tuple(" in Path(stored.__file__).read_text()
    changed_document = copy.deepcopy(testing_document)
    changed_document["facets"]["axis"]["attaches_to"] = ["dataset", "proposition"]
    changed_domain = parse_domain_contract(changed_document, source="fixture", base=shipped_base_contract(), predecessor=None)
    changed_profile = compile_profile(shipped_base_contract(), [changed_domain], coordination=coordination_contract())
    assert changed_profile.compiled_identity != profile.compiled_identity
    assert "testing/axis" in changed_profile.facets_of("proposition")
    assert not tuple(reopen(w.root).iter_stored())


def test_d5_manifest_pin_projection_and_refusals(corpora, tmp_path):
    import yaml

    from beliefs.contract.document import load_document
    from beliefs.errors import ManifestMalformed
    from beliefs.world import corpus_state_identity, load_manifest
    duplicate = tmp_path / "duplicate.yaml"
    duplicate.write_text("facets: {}\nfacets: {}\n")
    with pytest.raises(MalformedContract, match="duplicate"):
        load_document(duplicate, source="fixture")
    w = corpora(profile=WITH_BIOLOGY)
    path = w.root / "corpus.yaml"
    original = yaml.safe_load(path.read_text())
    assert load_manifest(w.root).profile == pins_for(WITH_BIOLOGY)
    original["profile"]["domains"]["chemistry"] = "chemistry:" + "c" * 64
    path.write_text(yaml.safe_dump(original))
    state = corpus_state_identity(w.root)
    reordered = copy.deepcopy(original)
    reordered["profile"]["domains"] = dict(reversed(list(reordered["profile"]["domains"].items())))
    path.write_text(yaml.safe_dump(reordered, default_flow_style=True, sort_keys=False))
    (w.root / "notes.txt").write_text("unrelated")
    assert corpus_state_identity(w.root) == state
    changed = copy.deepcopy(original)
    changed["profile"]["domains"]["chemistry"] = "chemistry:" + "d" * 64
    path.write_text(yaml.safe_dump(changed))
    assert corpus_state_identity(w.root) != state
    changed = copy.deepcopy(original)
    changed["forked_from"] = {"corpus_id": "2" * 32, "corpus_state": "3" * 64}
    path.write_text(yaml.safe_dump(changed))
    assert corpus_state_identity(w.root) != state
    good = yaml.safe_dump(original)
    for malformed in (good + "extra: refused\n", good.replace("biology:", "biology: ignored\n    biology:"), good.replace(pins_for(BASE).science_contract, "science:bad")):
        path.write_text(malformed)
        with pytest.raises(ManifestMalformed):
            corpus_state_identity(w.root)


def test_d8_contributions_compose_without_collision(corpora, testing_document):
    w = corpora()
    base = shipped_base_contract()
    for section in ("kinds", "relations"):
        with refused(w, MalformedContract):
            parse_domain_contract({**testing_document, section: {}}, source="fixture", base=base, predecessor=None)
    first = parse_domain_contract(testing_document, source="fixture", base=base, predecessor=None)
    other_document = copy.deepcopy(testing_document)
    other_document["contract"] = "another"
    other = parse_domain_contract(other_document, source="fixture", base=base, predecessor=None)
    combined = compile_profile(base, [first, other])
    assert {"testing/axis", "another/axis"} <= set(combined.facets_of("dataset"))
    with refused(w, ProfileError):
        compile_profile(base, [first, first])
    doc = copy.deepcopy(testing_document)
    doc["facets"]["axis"]["attaches_to"] = ["divergence"]
    second = parse_domain_contract(doc, source="fixture", base=base, predecessor=None)
    with refused(w, ProfileError):
        compile_profile(base, [second])


def test_d9_practices_carry_no_vocabulary(corpora, tmp_path):
    import yaml
    from test_practice import GOOD
    w = corpora()
    for section in ("vocabulary", "sorts", "dimensions", "operators", "facets", "kinds", "relations"):
        with refused(w, MalformedContract):
            parse_practice({**GOOD, section: {}}, source="fixture")
    path = tmp_path / "PRACTICE.yaml"
    path.write_text(yaml.safe_dump(GOOD))
    assert load_practice(path) == parse_practice(GOOD, source="fixture")
    assert "practice" not in inspect.signature(compile_profile).parameters


def test_d10_facets_stay_facets(corpora):
    corpora()
    for name, method in inspect.getmembers(CorpusWriter, inspect.isfunction):
        if not name.startswith("_"):
            assert not {"facet", "facet_key"} & inspect.signature(method).parameters.keys()
    assert set(inspect.signature(CorpusWriter.retract).parameters) == {"self", "record"}
    assert set(inspect.signature(CorpusWriter.supersede).parameters) == {"self", "successor", "of"}


def test_g5_no_divergence_kind_exists(corpora):
    w = corpora()
    assert "divergence" not in w.profile.kinds
    with refused(w, ValidationRefused, match="kind-unknown"):
        w.add(Node(id="divergence:x", kind="divergence", title="x"))


def test_f1_payload_contract_enforced_at_every_entry(corpora):
    malformed = [
        {"locator": "url:x", "attested_by": ACTOR, "extra": "x"},
        {"attested_by": ACTOR}, {"locator": 3, "attested_by": ACTOR},
        {"locator": "ftp:x", "attested_by": ACTOR}, {"locator": "url:", "attested_by": ACTOR},
        {"boundary": "acquisition", "source": "dataset:gse179929", "asserted_by": "mm30-reproduction"},
    ]
    from beliefs import relocation
    for payload in malformed:
        w, target = corpora(), corpora()
        good = w.add(acquired("good", ACTOR))
        bad = stored.dataset_node("bad", title="bad", resources=PINNED, empirical_observation=payload)
        with refused(w, FacetPayloadRefused):
            w.add(bad)
        with refused(w, FacetPayloadRefused):
            w.revise(revised(good, **{"empirical-observation": payload}))
        with pytest.raises(ImportRefused) as caught:
            target.import_bundle([bad], **IMPORT)
        assert caught.value.member == bad.id and isinstance(caught.value.__cause__, FacetPayloadRefused)
        assert not reopen(target.root).holds(bad.id)
        raw_write(w.root, bad)
        w._reconstruct()
        assert ("facet-payload-malformed", bad.id) in {(f.code, f.ref) for f in corpus_check(w.read_view, BASE)}
        with refused(target, FacetPayloadRefused):
            relocation.move(w, target, bad.id, **IMPORT)
        assert reopen(w.root).holds(bad.id)


def test_f2_bearer_invariant_over_resulting_state(corpora, tmp_path):
    _durable_production_collision(corpora, tmp_path)
    w = corpora()
    d = w.add(acquired("d", ACTOR))
    with refused(w, AcquisitionBoundaryRefused):
        w.add(producing("r", d.id))
    source = stored.source_node("s", title="s", identifiers={"doi": "10.1/x"})
    source.relations.append(Relation(source=source.id, predicate="produces", target=d.id))
    with refused(w, AcquisitionBoundaryRefused):
        w.add(stored.stamp_semantic_identity(source))
    other = corpora()
    other.add(producing("r", "dataset:d"))
    with refused(other, AcquisitionBoundaryRefused):
        other.add(acquired("d", ACTOR))
    for members in ([acquired("x", "foreign"), producing("r", "dataset:x")], [producing("r", "dataset:x"), acquired("x", "foreign")]):
        target = corpora()
        with pytest.raises(ImportRefused) as caught:
            target.import_bundle(members, **IMPORT)
        assert isinstance(caught.value.__cause__, AcquisitionBoundaryRefused)
        assert {n.kind for n in reopen(target.root).iter_stored()} == {"act-report"}
    raw_write(w.root, producing("r", d.id))
    assert "facet-bearer-produced" in {f.code for f in corpus_check(reopen(w.root), BASE)}


def test_f3_attestation_bound_and_preserved(corpora):
    w = corpora(authority=ALICE)
    with refused(w, ActorMismatch):
        w.add(acquired("wrong", "bob"))
    d = w.add(acquired("d", "alice"))
    bob = open_corpus(w.root, authority=BOB, profile=BASE)
    with refused(bob, ActorMismatch):
        bob.revise(revised(d, **{"empirical-observation": {"locator": "url:y", "attested_by": "alice"}}))
    with refused(bob, ActorMismatch):
        bob.revise(revised(d, **{"empirical-observation": {"locator": "url:x", "attested_by": "bob"}}))
    changed = bob.revise(revised(d, **{"empirical-observation": {"locator": "url:y", "attested_by": "bob"}}))
    target = corpora()
    target.import_bundle([changed], **IMPORT)
    assert reopen(target.root).get(d.id).facets == changed.facets
    from beliefs import relocation
    moved = corpora()
    relocation.move(target, moved, d.id, **IMPORT)
    assert reopen(moved.root).get(d.id).facets == changed.facets
    own = w.add(stored.dataset_node("own", title="own", resources=[{"name": "n", "digest": "sha256:" + "2" * 64}], empirical_observation={"locator": "url:x", "attested_by": "alice"}))
    own = w.revise(revised(own, **{"empirical-observation": {"locator": "url:y", "attested_by": "alice"}}))
    kept = bob.revise(own.model_copy(update={"title": "Bob edits prose"}))
    assert kept.facets["empirical-observation"] == own.facets["empirical-observation"]


def test_f4_eligibility_reads_the_validity_predicate(corpora, acquisition_report):
    for variant in ("payload", "absent", "basis", "deleted-retrieval"):
        w = corpora()
        good = w.add(acquired("good", ACTOR))
        bad = acquired("bad", ACTOR)
        expected = "facet-payload-malformed"
        if variant == "payload":
            bad.facets["empirical-observation"] = {"locator": 3, "attested_by": ACTOR}
        elif variant == "absent":
            del bad.facets["empirical-observation"]
            expected = "no-empirical-observation-facet"
        elif variant == "basis":
            bad.facets["lineage-basis"] = {"tag": "single", "routes": []}
            expected = "facet-bearer-produced"
        else:
            report = stored.act_report_node(acquisition_report)
            w.import_bundle([report], **IMPORT)
            bad.facets["empirical-observation"]["retrieval"] = report.id
            from fixtures_cut4 import path_for
            path_for(w.root, report.id).unlink()
            expected = "facet-retrieval-unresolved"
        raw_write(w.root, stored.stamp_semantic_identity(bad))
        run = w.add(stored.run_node("r", title="r", spec="analysis-spec:s", observes=[bad.id]))
        assessment = stored.assessment_node("a", title="a", spec="analysis-spec:s", run=run.id, proposition="proposition:p", outcome="supported", interpretation_rule="rule:threshold")
        reason = eligibility_refusal(reopen(w.root), assessment, BASE)
        assert reason is not None and expected in reason
        run.relations.append(Relation(source=run.id, predicate="observes", target=good.id))
        raw_write(w.root, stored.stamp_semantic_identity(run))
        assert eligibility_refusal(reopen(w.root), assessment, BASE) is None
        if variant != "absent":
            assert expected in {f.code for f in corpus_check(reopen(w.root), BASE)}


def test_f5_profile_agreement_rechecked_under_the_lock(corpora, tmp_path, monkeypatch):
    _pin_change_after_intent(corpora, tmp_path, monkeypatch)
    w = corpora()
    stale = w.add(acquired("stale", ACTOR))
    stale.facets["empirical-observation"]["locator"] = "url:changed"
    raw_write(w.root, stale)
    path = w.root / "corpus.yaml"
    path.write_text(path.read_text().replace(pins_for(BASE).science_contract, "science:" + "f" * 64))
    with refused(w, ContractMismatch):
        w.add(acquired("d", ACTOR))
    assert [f.code for f in corpus_check(reopen(w.root), BASE)] == ["profile-mismatch"]
    domain = corpora(profile=WITH_BIOLOGY)
    d = domain.add(acquired("d", ACTOR))
    d.facets["empirical-observation"]["locator"] = "url:raw-change"
    raw_write(domain.root, d)
    path = domain.root / "corpus.yaml"
    pin = pins_for(WITH_BIOLOGY).domains["biology"]
    path.write_text(path.read_text().replace(pin, "biology:" + "e" * 64))
    assert {"profile-mismatch", "semantic-hash-stale"} <= {f.code for f in corpus_check(reopen(domain.root), WITH_BIOLOGY)}


def test_f6_dataset_revision_changes_interpretation_and_prose_only(corpora):
    from test_dataset_revision import test_every_preserved_field_is_refused_when_moved

    from beliefs.errors import RevisionTargetMissing
    w = corpora(authority=ALICE, profile=WITH_BIOLOGY)
    d = w.add(acquired("d", "alice"))
    for field in ("id", "uid", "kind", "coordination-kind", "relations", "deprecated_ids", "metadata", "dataset", "lineage-basis"):
        before = contents(w.root)
        test_every_preserved_field_is_refused_when_moved((w, d), field, RevisionTargetMissing if field in ("id", "uid") else ReviseOutsideAllowlist)
        assert contents(w.root) == before
    with refused(w, ReviseOutsideAllowlist):
        w.revise(revised(d, **{"empirical-observation": None}))
    domain = w.revise(revised(d, **{"biology/gene-axis": {"axis": "rows"}}))
    changed = w.revise(revised(domain, **{"biology/gene-axis": None, "display": {"display_statement": "new"}}))
    assert "biology/gene-axis" not in changed.facets and changed.id == d.id
    plain_writer = corpora(authority=ALICE)
    plain = plain_writer.add(stored.dataset_node("plain", title="plain", resources=PINNED))
    with refused(plain_writer, ActorMismatch):
        plain_writer.revise(revised(plain, **{"empirical-observation": {"locator": "url:x", "attested_by": "bob"}}))
    plain_writer.revise(revised(plain, **{"empirical-observation": {"locator": "url:x", "attested_by": "alice"}}))
    produced_writer = corpora(authority=ALICE)
    produced = produced_writer.add(stored.dataset_node("produced", title="produced", resources=PINNED))
    produced_writer.add(producing("r", produced.id))
    with refused(produced_writer, AcquisitionBoundaryRefused):
        produced_writer.revise(revised(produced, **{"empirical-observation": {"locator": "url:x", "attested_by": "alice"}}))


def test_f7_retrieval_resolves_or_refuses(corpora, acquisition_report):
    w = corpora()
    with refused(w, FacetPayloadRefused, match="retrieval-unresolved"):
        w.add(acquired("d", ACTOR, retrieval="act-report:" + "0" * 64))
    wrong = w.import_bundle([stored.source_node("s", title="s", identifiers={"doi": "10.1/x"})], **IMPORT)
    with refused(w, FacetPayloadRefused, match="not an acquisition"):
        w.add(acquired("d", ACTOR, retrieval=f"act-report:{wrong.identity()}"))
    report = stored.act_report_node(acquisition_report)
    w.import_bundle([report], **IMPORT)
    assert w.add(acquired("d", ACTOR, retrieval=report.id)).facets["empirical-observation"]["retrieval"] == report.id


def test_f8_every_builder_facet_is_declared(corpora, acquisition_report):
    from closure_fixtures import make_closure
    from coordination_fixtures import content_for
    from fixtures_cut3 import spec_draft, spec_rules
    from test_holdings_records import observation

    from beliefs.corpus import CoordinationResolver
    from beliefs.runrecord import projection_text
    from beliefs.spec import freeze
    profile = compile_profile(shipped_base_contract(), [], coordination=coordination_contract())
    w = corpora(profile=profile)
    coordinated = open_corpus(w.root, authority=FULL, profile=profile, coordination_resolver=CoordinationResolver({w.root: profile}))
    closure = make_closure()
    builders = {
        "governed_node": stored.governed_node("source", "g", "g", {"source": {"identifiers": {"doi": "x"}}}, ()),
        "act_report_node": stored.act_report_node(acquisition_report),
        "proposition_node": stored.proposition_node("p", title="p", claim={"operator": "affects"}, display_statement="shown"),
        "source_node": stored.source_node("s", title="s", identifiers={"doi": "x"}),
        "dataset_node": acquired("d", ACTOR),
        "run_node": producing("r", "dataset:x"),
        "run_publication_node": stored.run_publication_node("rp", title="rp", projection=projection_text(closure).decode(), spec="analysis-spec:s"),
        "assessment_node": stored.assessment_node("a", title="a", spec="analysis-spec:s", run="run:r", proposition="proposition:p", outcome="supported", interpretation_rule="rule:r"),
        "verification_node": stored.verification_node("v", title="v", assessment="a", assessment_ref="assessment:a", scope="same-environment", verdict="passed"),
        "analysis_spec_node": stored.analysis_spec_node(freeze(spec_draft(), held_rules=spec_rules())),
        "retraction_node": stored.retraction_node(title="r", target=stored.NodeTarget("dataset:d", "dataset:d", "1" * 64), reason="authored-error", rationale="wrong", grounds=["source:s"], actor=ACTOR, event_token="e"),
        "holdings_observation_node": stored.holdings_observation_node(observation()),
    }
    assert set(builders) == {name for name, value in vars(stored).items() if name.endswith("_node") and not name.startswith("_") and callable(value)}
    for node in builders.values():
        profile.validate_document(node)
    profile.validate_document(coordinated.mint_coordination("project", content=content_for("project")))
    node = builders["dataset_node"].model_copy(deep=True)
    node.facets["provenance"] = {}
    with refused(w, ValidationRefused, match="unexpected"):
        w.add(node)


def test_d1_installed_nodes_takes_no_domain_argument(corpora):
    corpora()
    for callable in (Registry.register, KindSpec, ShapeSpec):
        assert not {"domain", "contract", "vocabulary"} & inspect.signature(callable).parameters.keys()


def test_boundary_no_read_entry_point_gained_an_argument(corpora):
    from beliefs.corpus import ReadView, standing_in_local_view
    corpora()
    for callable in (ReadView.get, ReadView.iter_stored, standing_in_local_view):
        assert not {"profile", "domain", "contract", "vocabulary"} & inspect.signature(callable).parameters.keys()


def _durable_production_collision(corpora, tmp_path):
    from atoms.chain.model import IntentEntry, RegisteredEntry
    from fixtures_cut3 import DATA_ADDRESS, READS_ADDRESS, MemoryPort, run_production

    from beliefs.boundary import RunMinted, RunRefused
    from beliefs.production import mint_dataset
    first = run_production(tmp_path / "first", port=MemoryPort())
    assert isinstance(first, RunMinted)
    w = corpora()
    address = mint_dataset(first.run, existing_bases={}).address
    bearer = w.add(stored.dataset_node(address.removeprefix("dataset:"), title="bearer", resources=[{"name": n, "digest": d} for n, d in first.run.result.outputs], empirical_observation={"locator": "url:x", "attested_by": ACTOR}))
    before = contents(w.root)
    held_before = contents(tmp_path / "first" / "held")
    assert held_before
    start = len(chain_entries(w.root))
    result = run_production(tmp_path / "second", port=w._operation_port, held_inputs={
        DATA_ADDRESS: tmp_path / "first" / "held" / "data.txt",
        READS_ADDRESS: tmp_path / "first" / "held" / "palette.txt",
    })
    assert isinstance(result, RunRefused) and result.reason == "acquisition-boundary"
    entries = chain_entries(w.root)[start:]
    intents = [(digest, entry) for digest, entry in entries if isinstance(entry, IntentEntry)]
    registrations = [entry for _, entry in entries if isinstance(entry, RegisteredEntry)]
    assert len(intents) == len(registrations) == 1
    assert registrations[0].fulfills == intents[0][0]
    after = contents(w.root)
    assert {path: digest for path, digest in after.items() if path in before} == before
    assert all(path.parts[0] in {".#~chain", "act-report"} for path in after.keys() - before.keys())
    nodes = tuple(reopen(w.root).iter_stored())
    assert [node.id for node in nodes if node.kind != "act-report"] == [bearer.id]
    assert len([node for node in nodes if node.kind == "act-report"]) == 1
    assert held_before == contents(tmp_path / "first" / "held")


def _pin_change_after_intent(corpora, tmp_path, monkeypatch):
    from atoms.chain.model import IntentEntry, RegisteredEntry
    from fixtures_cut3 import run_production
    w = corpora()
    port = w._operation_port
    assert port is not None
    append = port.append_intent
    snapshot = []
    def changed(payload):
        digest = append(payload)
        path = w.root / "corpus.yaml"
        path.write_text(path.read_text().replace(pins_for(BASE).science_contract, "science:" + "f" * 64))
        snapshot.append(contents(w.root))
        return digest
    monkeypatch.setattr(port, "append_intent", changed)
    start = len(chain_entries(w.root))
    with pytest.raises(ContractMismatch):
        run_production(tmp_path / "pin-changed", port=port)
    assert len(snapshot) == 1 and contents(w.root) == snapshot[0]
    entries = chain_entries(w.root)[start:]
    assert len(entries) == 1 and isinstance(entries[0][1], IntentEntry)
    assert not any(isinstance(entry, RegisteredEntry) for _, entry in entries)
    assert not tuple(reopen(w.root).iter_stored())
