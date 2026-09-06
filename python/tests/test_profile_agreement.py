# python/tests/test_profile_agreement.py
"""§5.1 and F5: writer and port hold a profile; every write path rechecks the pins under its lock."""

import pytest
from authority import FULL
from nodes.core.corpus import Corpus
from nodes.core.node import Node
from nodes.core.write_plan import DefaultExecutor
from profiles import BASE, WITH_BIOLOGY, WITH_BIOLOGY_OTHER, pins_for
from test_corpus_write import OperationRecorder

from beliefs import stored
from beliefs.corpus import CorpusWriter, ReadView
from beliefs.errors import ContractMismatch, FacetPayloadRefused, ValidationRefused

PINNED = [{"name": "m", "digest": "sha256:" + "1" * 64}]
IMPORT = {"observer": "o", "instrument": "i", "opened_at": "2026-09-05T00:00:00Z", "closed_at": "2026-09-05T00:00:01Z"}


def _writer(root, profile=BASE):
    port = OperationRecorder(root, authority=FULL, profile=profile)
    writer = CorpusWriter(root, DefaultExecutor, authority=FULL, profile=profile, operation_port=port)
    writer.adopt_manifest(profile=pins_for(profile))
    return writer, port


def _rewrite_biology_pin(root):
    text = (root / "corpus.yaml").read_text()
    (root / "corpus.yaml").write_text(text.replace(pins_for(WITH_BIOLOGY).domains["biology"], pins_for(WITH_BIOLOGY_OTHER).domains["biology"]))


def test_a_writer_requires_a_compiled_profile_and_a_port_agreeing_with_it(tmp_path):
    with pytest.raises(TypeError):
        CorpusWriter(tmp_path, DefaultExecutor, authority=FULL)  # type: ignore[call-arg]
    port = OperationRecorder(tmp_path, authority=FULL, profile=WITH_BIOLOGY)
    with pytest.raises(ValueError, match="profile"):
        CorpusWriter(tmp_path, DefaultExecutor, authority=FULL, profile=BASE, operation_port=port)
    assert WITH_BIOLOGY.compiled_identity == WITH_BIOLOGY_OTHER.compiled_identity  # description-only variants
    with pytest.raises(ValueError, match="profile"):
        CorpusWriter(tmp_path, DefaultExecutor, authority=FULL, profile=WITH_BIOLOGY_OTHER, operation_port=port)


def test_adopt_manifest_writes_only_the_held_profiles_pins(tmp_path):
    writer = CorpusWriter(tmp_path, DefaultExecutor, authority=FULL, profile=BASE)
    with pytest.raises(ContractMismatch):
        writer.adopt_manifest(profile=pins_for(WITH_BIOLOGY))
    assert list(tmp_path.rglob("*")) == []


@pytest.mark.parametrize("path", ["add", "delete", "revise", "import", "intent", "port-execute", "port-fulfilling"])
def test_every_write_path_rechecks_the_pins_after_a_manifest_change(tmp_path, path):
    tmp_path = tmp_path / path
    writer, port = _writer(tmp_path, WITH_BIOLOGY)
    p = writer.add(stored.proposition_node("p", title="p", claim={"operator": "affects"}))
    before = sorted(str(x.relative_to(tmp_path)) for x in tmp_path.rglob("*") if x.is_file())
    _rewrite_biology_pin(tmp_path)
    q = stored.proposition_node("q", title="q", claim={"operator": "affects"})
    with pytest.raises(ContractMismatch, match="manifest pins"):
        if path == "add":
            writer.add(q)
        elif path == "delete":
            writer.delete(p.id)
        elif path == "revise":
            writer.revise(p.model_copy(update={"title": "renamed"}))
        elif path == "import":
            writer.import_bundle([q], observer="o", instrument="i", opened_at="T0", closed_at="T1")
        elif path == "intent":
            port.append_intent(b"intent")
        elif path == "port-execute":
            port.execute(())
        else:
            port.execute_fulfilling((), "ab" * 32)
    after = sorted(str(x.relative_to(tmp_path)) for x in tmp_path.rglob("*") if x.is_file())
    assert before == after and port.intents == [] and port.executed == [] and port.fulfilling == []


def test_relocation_rechecks_at_the_destination(tmp_path):
    from fixtures_cut6 import PINS
    from test_relocation import _writer as relocation_writer

    from beliefs import relocation

    source = relocation_writer(tmp_path / "s", domains=PINS.domains)
    destination = relocation_writer(tmp_path / "d", domains=PINS.domains)
    node = source.add(stored.proposition_node("p", title="p", claim={"operator": "affects"}))
    _rewrite_biology_pin(tmp_path / "d")
    with pytest.raises(ContractMismatch):
        relocation.move(source, destination, node.id, observer="o", instrument="i", opened_at="2026-09-05T00:00:00Z", closed_at="2026-09-05T00:00:01Z")
    assert source.read_view.holds(node.id) and not destination.read_view.holds(node.id)


def test_a_validated_read_refuses_a_corpus_pinning_another_base_but_iteration_does_not(tmp_path):
    writer, _ = _writer(tmp_path)
    node = writer.add(stored.proposition_node("p", title="p", claim={"operator": "affects"}))
    text = (tmp_path / "corpus.yaml").read_text()
    (tmp_path / "corpus.yaml").write_text(text.replace(pins_for(BASE).science_contract, "science:" + "f" * 64))
    view = ReadView(Corpus(tmp_path))  # construction never checks
    assert [n.id for n in view.iter_stored()] == [node.id]
    with pytest.raises(ContractMismatch, match="science_contract"):
        view.get(node.id)


def test_an_unknown_kind_and_an_undeclared_facet_key_are_refused_at_add(tmp_path):
    writer, _ = _writer(tmp_path)
    with pytest.raises(ValidationRefused, match="kind-unknown"):
        writer.add(Node(id="divergence:d", kind="divergence", title="d", facets={}))
    node = stored.proposition_node("p", title="p", claim={"operator": "affects"})
    node.facets["biology/gene-axis"] = {"axis": "rows"}
    with pytest.raises(ValidationRefused, match="facet-unexpected"):
        writer.add(stored.stamp_semantic_identity(node))


def test_a_prose_kind_is_admitted_with_display_only(tmp_path):
    writer, _ = _writer(tmp_path)
    writer.add(Node(id="discussion:d", kind="discussion", title="d", facets={"display": {"display_statement": "x"}}))
    with pytest.raises(ValidationRefused, match="facet-unexpected"):
        writer.add(Node(id="discussion:e", kind="discussion", title="e", facets={"dataset": {}}))


def test_a_malformed_schema_facet_is_refused_at_add(tmp_path):
    writer, _ = _writer(tmp_path)
    node = stored.dataset_node(
        "d", title="d", resources=PINNED,
        empirical_observation={"boundary": "acquisition", "source": "dataset:gse", "asserted_by": "driver"},
    )
    with pytest.raises(FacetPayloadRefused, match="unknown key"):
        writer.add(node)


def test_profile_type_and_foreign_base_refuse_before_opening(tmp_path, base_contract_path):
    import yaml

    from beliefs.contract import parse_base_contract
    from beliefs.profile import compile_profile

    with pytest.raises(TypeError, match="ProfileSpec"):
        CorpusWriter(tmp_path, DefaultExecutor, authority=FULL, profile=None)  # type: ignore[arg-type]
    document = yaml.safe_load(base_contract_path.read_text())
    document["version"] += 1
    foreign = compile_profile(parse_base_contract(document, source="<foreign-base>"), [])
    with pytest.raises(ContractMismatch, match="shipped base"):
        CorpusWriter(tmp_path, DefaultExecutor, authority=FULL, profile=foreign)
    assert not tmp_path.joinpath("corpus.yaml").exists()


def test_writer_requires_the_mounted_profile(tmp_path):
    from beliefs.corpus import CoordinationResolver

    _writer(tmp_path, WITH_BIOLOGY)
    resolver = CoordinationResolver({tmp_path: WITH_BIOLOGY})
    with pytest.raises(ContractMismatch, match="mounted coordination profile"):
        CorpusWriter(tmp_path, DefaultExecutor, authority=FULL, profile=BASE, coordination_resolver=resolver)


def test_unreadable_manifest_refuses_before_any_write(tmp_path):
    writer, port = _writer(tmp_path)
    (tmp_path / "corpus.yaml").write_text("profile: [bad")
    with pytest.raises(ContractMismatch, match="manifest pins cannot be read"):
        writer.add(Node(id="discussion:x", kind="discussion", title="x"))
    assert list(tmp_path.rglob("*.md")) == []
    assert port.intents == port.executed == port.fulfilling == []


def test_missing_declared_facet_refuses_before_add(tmp_path):
    writer, _ = _writer(tmp_path)
    with pytest.raises(ValidationRefused, match="facet-missing"):
        writer.add(Node(id="proposition:x", kind="proposition", title="x"))
    assert not writer.read_view.holds("proposition:x")


@pytest.mark.parametrize("method", ["append_intent", "execute", "execute_fulfilling"])
def test_durable_port_rechecks_under_its_lock_before_engine_calls(tmp_path, monkeypatch, method):
    from contextlib import contextmanager

    from beliefs import root

    tmp_path = tmp_path / method
    _writer(tmp_path, WITH_BIOLOGY)
    calls = []

    @contextmanager
    def change_pins_at_lock_entry(_root):
        _rewrite_biology_pin(tmp_path)
        yield

    monkeypatch.setattr(root, "_operation_lock_for", change_pins_at_lock_entry)
    monkeypatch.setattr(root, "append_intent", lambda *args: calls.append(args))
    monkeypatch.setattr(root.DurableExecutor, "execute", lambda *args: calls.append(args))
    port = root.DurableOperationPort(tmp_path, backend=root._PRODUCTION_BACKEND, storage=root.PRODUCTION_STORAGE,
                                     metadata_root=tmp_path / "metadata", authority=FULL, profile=WITH_BIOLOGY)
    assert port.profile is WITH_BIOLOGY
    with pytest.raises(ContractMismatch):
        if method == "append_intent":
            port.append_intent(b"intent")
        elif method == "execute":
            port.execute(())
        else:
            port.execute_fulfilling((), "ab" * 32)
    assert calls == []


@pytest.fixture()
def holdings_context(tmp_path):
    from contextlib import contextmanager

    from beliefs.holdings.boundary import ActContext
    from beliefs.holdings.seam import FileStateView, PathObservedView, StoreActSeam, StoreOutcomeView

    intents, published = [], []
    held = False

    @contextmanager
    def corpus_lock(_root):
        nonlocal held
        assert not held
        held = True
        try:
            yield
        finally:
            held = False

    def append(_root, payload):
        assert held
        intents.append(payload)
        return "ab" * 32

    def publish(_root, plan, intent):
        assert held
        published.append((plan, intent))

    state = FileStateView("sha256:" + "1" * 64)
    seam = StoreActSeam(corpus_lock=corpus_lock, append_intent=append, publish_fulfilling=publish,
                       read_path=lambda *_: PathObservedView(state),
                       store_write=lambda _root, path, _bytes: StoreOutcomeView("tx", ((path, state),)),
                       store_delete=lambda *_: StoreOutcomeView("unused", ()),
                       store_move=lambda *_: StoreOutcomeView("unused", ()),
                       store_genesis=lambda _: b'{"domain":"science.store-root.v1","store_id":"11111111111111111111111111111111"}')
    ctx = ActContext(tmp_path / "corpus", tmp_path / "store", "o", "i", FULL, seam, WITH_BIOLOGY)
    return ctx, intents, published


@pytest.mark.parametrize("when", ["before-intent", "before-publication"])
def test_holdings_pin_refusal_leaves_no_publication(tmp_path, holdings_context, when):
    from dataclasses import replace

    from beliefs.holdings.boundary import write
    from beliefs.holdings.records import StoreLocator

    ctx, intents, published = holdings_context
    _writer(tmp_path / "corpus", WITH_BIOLOGY)
    if when == "before-intent":
        _rewrite_biology_pin(ctx.observer_root)
    else:
        inner = ctx.seam.store_write

        def store_write_then_rewrite(store_root, relative_path, content):
            result = inner(store_root, relative_path, content)
            _rewrite_biology_pin(ctx.observer_root)
            return result

        ctx = replace(ctx, seam=replace(ctx.seam, store_write=store_write_then_rewrite))
    with pytest.raises(ContractMismatch):
        write(ctx, StoreLocator("1" * 32, "f.txt"), b"bytes")
    assert len(intents) == (0 if when == "before-intent" else 1)
    assert published == []
    assert list(ctx.observer_root.rglob("*.md")) == []


def test_holdings_context_requires_a_compiled_profile(holdings_context):
    from dataclasses import replace

    ctx, _, _ = holdings_context
    with pytest.raises(TypeError, match="ProfileSpec"):
        replace(ctx, profile=None)


def test_a_dangling_manifest_is_not_treated_as_an_unpinned_corpus(tmp_path):
    writer = CorpusWriter(tmp_path, DefaultExecutor, authority=FULL, profile=BASE)
    (tmp_path / "corpus.yaml").symlink_to("missing.yaml")
    with pytest.raises(ContractMismatch, match="manifest pins cannot be read"):
        writer.add(Node(id="discussion:x", kind="discussion", title="x"))
    assert list(tmp_path.rglob("*.md")) == []


def test_durable_port_requires_a_compiled_profile(tmp_path):
    from beliefs import root

    with pytest.raises(TypeError, match="ProfileSpec"):
        root.DurableOperationPort(tmp_path, backend=root._PRODUCTION_BACKEND, storage=root.PRODUCTION_STORAGE,
                                  metadata_root=tmp_path / "metadata", authority=FULL, profile=None)  # type: ignore[arg-type]


@pytest.mark.parametrize("operation", ["add", "import", "move", "consolidate"])
def test_provenance_reaches_facet_validation(tmp_path, monkeypatch, operation):
    from beliefs import relocation

    source, _ = _writer(tmp_path / operation / "source")
    destination, _ = _writer(tmp_path / operation / "destination")
    node = stored.proposition_node("p", title="p", claim={"operator": "affects"})
    if operation in {"move", "consolidate"}:
        source.add(node)
    if operation == "consolidate":
        destination.add(node.model_copy(update={"uid": "f" * 32}))
    seen = []
    original = CorpusWriter._refuse_facets

    def record_provenance(self, record, *, view=None, provenance=False):
        seen.append((record.id, provenance))
        return original(self, record, view=view, provenance=provenance)

    monkeypatch.setattr(CorpusWriter, "_refuse_facets", record_provenance)
    if operation == "add":
        destination.add(node)
    elif operation == "import":
        destination.import_bundle([node], observer="o", instrument="i", opened_at="T0", closed_at="T1")
    elif operation == "move":
        relocation.move(source, destination, node.id, observer="o", instrument="i", opened_at="T0", closed_at="T1")
    else:
        relocation.consolidate((destination, node.id), (source, node.id), rationale="keep",
                               observer="o", instrument="i", opened_at="T0", closed_at="T1")
    expected = [(node.id, operation != "add")] * (2 if operation in {"move", "consolidate"} else 1)
    assert seen == expected


def test_profile_is_required_at_each_public_write_construction():
    import inspect

    from beliefs.holdings.boundary import ActContext
    from beliefs.root import DurableOperationPort, open_corpus

    for construction in (CorpusWriter, DurableOperationPort, open_corpus, ActContext):
        assert inspect.signature(construction).parameters["profile"].default is inspect.Parameter.empty


def test_facet_refusal_code_comes_from_registry_not_record_text(tmp_path):
    writer, _ = _writer(tmp_path)
    with pytest.raises(ValidationRefused, match="facet-unexpected"):
        writer.add(Node(id="discussion:missing", kind="discussion", title="x", facets={"undeclared": {}}))
