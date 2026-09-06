"""E1 over every inventoried definition (design §4.2, §7 E1).

One case per entry point, keyed by its `WRITE_ENTRY_POINTS` name. `prepare`
performs every setup effect under a full authority; `act` performs exactly the
protected call under the authority being judged; `probe` reads the state a
refused act must leave unchanged. The tests derive E1's three directions.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pytest
from authority import ACTOR, lacking, narrowed
from test_permit_boundary import WRITE_ENTRY_POINTS

from beliefs import root as science_root
from beliefs.corpus import CorpusWriter
from beliefs.errors import PermitExceeded, PermitFact
from beliefs.permit import Authority
from beliefs.world import registry

_STATE: dict[Path, dict] = {}
"""Per-work-directory handles prepare leaves for act."""


@dataclass(frozen=True)
class Case:
    key: str
    family: str
    kinds: tuple[str, ...]
    needs_volume: bool
    prepare: Callable[[Path, object], None]   # (work, request): setup effects under a full authority
    act: Callable[[Authority, Path], object]
    probe: Callable[[Path], object]

    @property
    def id(self) -> str:
        return self.key.replace("/", ".").replace(":", ".")


def _chain(root: Path) -> int:
    from beliefs.world.logmodel import WellFormedView

    view = science_root._log_seam().inspect_registered(root)
    assert type(view) is WellFormedView
    return len(view.entries)


def _tree(root: Path) -> list[tuple[str, str, str]]:
    """Every entry under `root` with its type and, for files, its content digest —
    a created directory or a changed byte is an effect (design §6)."""
    from hashlib import sha256

    if not root.exists():
        return []
    return sorted(
        (p.relative_to(root).as_posix(), "f" if p.is_file() else "d" if p.is_dir() else "o",
         sha256(p.read_bytes()).hexdigest() if p.is_file() else "")
        for p in root.rglob("*")
    )


def _nothing(_work: Path, _request) -> None:
    return None


# --- corpus-write family, in-memory executor -------------------------------------

def _writer(authority: Authority, work: Path, *, port: bool = False) -> CorpusWriter:
    from test_corpus_write import Recorder

    if not port:
        return CorpusWriter(work / "corpus", Recorder, authority=authority)
    from nodes.core.write_plan import DefaultExecutor
    from test_import_bundle import FakePort

    root = work / "corpus"
    return CorpusWriter(
        root,
        DefaultExecutor,
        authority=authority,
        operation_port=FakePort(root, authority=authority),
    )


def _reset_recorder() -> None:
    from test_corpus_write import Recorder

    Recorder.plans = []


def _corpus_probe(work: Path):
    """Every plan the recorder applied, and the corpus tree itself: a late check
    that let a plan through shows in both."""
    from test_corpus_write import Recorder

    result = (list(Recorder.plans), _tree(work / "corpus"))
    if not _STATE.get(work, {}).get("port"):
        return result
    from test_import_bundle import FakePort

    return (*result, list(FakePort.intents), list(FakePort.executed), list(FakePort.fulfilling))


def _prepare_corpus(minter=None, *, port: bool = False):
    """Mint `minter(writer)` under a full authority (or nothing), then reset the recorder."""

    def prepare(work: Path, _request) -> None:
        state: dict = {"port": port}
        if minter is not None:
            state["target"] = minter(_writer(lacking(), work))
        if port:
            from fixtures_cut6 import PINS
            from test_import_bundle import FakePort

            _writer(lacking(), work, port=True).adopt_manifest(profile=PINS)
            FakePort.intents, FakePort.executed, FakePort.fulfilling = [], [], []
        _STATE[work] = state
        _reset_recorder()

    return prepare


def _add(authority, work):
    from test_corpus_write import observed_dataset

    return _writer(authority, work).add(observed_dataset())


def _retract(authority, work):
    from test_retract import retraction_for

    return _writer(authority, work).retract(retraction_for(_STATE[work]["target"]))


def _supersede(authority, work):
    from test_supersede import prop

    return _writer(authority, work).supersede(
        prop("p2", claim_op="causes"), of=_STATE[work]["target"].id
    )


def _revise(authority, work):
    return _writer(authority, work).revise(_STATE[work]["target"])


def _add_locked(authority, work):
    from test_revise import prop

    return _writer(authority, work)._add_locked(prop("p"))


def _replace_locked(authority, work):
    target = _STATE[work]["target"]
    return _writer(authority, work)._replace_locked(target.model_copy(update={"title": "changed"}))


def _delete_locked(authority, work):
    return _writer(authority, work)._delete_locked(_STATE[work]["target"].id)


def _append_operation_intent(authority, work):
    return _writer(authority, work, port=True)._append_operation_intent("move", "ab" * 8, ACTOR)


def _publish_operation_report(authority, work):
    from test_import_bundle import FakePort

    from beliefs.report import Moved, OperationIntent

    writer = _writer(authority, work, port=True)
    intent = OperationIntent("move", "ab" * 8, ACTOR)
    report = writer._relocation_report(
        intent,
        subject="proposition:p",
        observer="o",
        instrument="i",
        opened_at="T0",
        closed_at="T1",
        outcome=Moved(writer.corpus_id, writer.corpus_id, "proposition:p"),
    )
    return writer._publish_operation_report(report, FakePort.intent_digest)


def _commit_fulfilling(authority, work):
    """The routed commit seam itself (writer-session design §13 item 13): its own
    `require`, judged on the kinds the plan emits, with nothing else in front of it."""
    from nodes.core.frontmatter import node_to_markdown
    from nodes.core.write_plan import CreateOp, DefaultExecutor
    from test_import_bundle import FakePort, prop

    from beliefs.corpus import _Fulfillment, _root_state_for

    root = work / "corpus"
    executor = _root_state_for(root, DefaultExecutor).executors(root)
    scope = _Fulfillment(authority, FakePort(root, authority=authority))
    plan = [CreateOp(path="proposition/p1.md", content=node_to_markdown(prop("p1")).encode("utf-8"))]
    return executor.commit_fulfilling(scope, plan)


def _prepare_coordination(with_project: bool):
    """Mount the corpus under the coordination profile (a `base_contract` session
    fixture compiles it) and, for revision, mint the project — all in prepare, so
    `act` constructs a writer over the mounted root and mounts nothing."""

    def prepare(work: Path, request) -> None:
        from coordination_fixtures import content_for, coordination_profile
        from test_coordination_write import writer_with_resolver

        profile = coordination_profile(request.getfixturevalue("base_contract"))
        writer, resolver = writer_with_resolver(work / "corpus", profile, authority=lacking())
        state: dict = {"resolver": resolver}
        if with_project:
            state["project"] = writer.mint_coordination("project", content=content_for("project"))
        _STATE[work] = state

    return prepare


def _coordination_writer(authority: Authority, work: Path) -> CorpusWriter:
    from test_coordination_write import (
        DefaultExecutor,  # the executor `writer_with_resolver` binds; same class, same root state
    )

    return CorpusWriter(work / "corpus", DefaultExecutor, authority=authority, coordination_resolver=_STATE[work]["resolver"])


def _mint_coordination(authority, work):
    from coordination_fixtures import content_for

    return _coordination_writer(authority, work).mint_coordination("project", content=content_for("project"))


def _revise_coordination(authority, work):
    from coordination_fixtures import content_for

    from beliefs.coordination import coordination_revision

    project = _STATE[work]["project"]
    return _coordination_writer(authority, work).revise_coordination(
        "project",
        coordination_revision(project).address,
        predecessors=(project.uid,),
        content=content_for("project", name="renamed"),
    )


def _coordination_probe(work: Path):
    return _tree(work / "corpus")


def _prepare_import(work: Path, _request) -> None:
    from test_import_bundle import FakePort

    _STATE[work] = {}
    _reset_recorder()
    FakePort.intents, FakePort.executed, FakePort.fulfilling = [], [], []


def _import_bundle(authority, work):
    from test_corpus_write import Recorder
    from test_import_bundle import FakePort, prop

    writer = CorpusWriter(work / "corpus", Recorder, authority=authority, operation_port=FakePort(work / "corpus", authority=authority))
    return writer.import_bundle([prop("p1")], observer="o", instrument="i", opened_at="T0", closed_at="T1")


def _import_probe(work: Path):
    """The port's three collections — the intent is the first effect import could
    make — beside the recorder and the corpus tree."""
    from test_import_bundle import FakePort

    return (list(FakePort.intents), list(FakePort.executed), list(FakePort.fulfilling), _corpus_probe(work))


def _adopt_manifest(authority, work):
    from fixtures_cut6 import PINS

    return _writer(authority, work).adopt_manifest(profile=PINS)


# --- run family, memory port ---------------------------------------------------------

class _Port:
    def __init__(self, authority: Authority) -> None:
        from fixtures_cut3 import MemoryPort

        self._inner = MemoryPort()
        self.authority = authority
        self.appended: list = []

    def append_intent(self, payload):
        self.appended.append(payload)
        return self._inner.append_intent(payload)

    def preflight(self, plan) -> None:
        pass

    def execute(self, plan):
        self.appended.append(plan)

    def execute_fulfilling(self, plan, fulfills) -> str:
        self.appended.append(plan)
        return "r" * 64


def _fact_from(detail: str) -> PermitFact:
    words = detail.split()  # "permit exceeded: <dimension> <name> is not permitted"
    return PermitFact(words[2], words[3])


def _run(shape: str):
    def act(authority, work):
        from fixtures_cut3 import run_assessment, run_production

        from beliefs.boundary import RunRefused

        _STATE.setdefault(work, {})["port"] = port = _Port(authority)
        outcome = (run_assessment if shape == "assessment" else run_production)(work, port=port)
        if isinstance(outcome, RunRefused) and outcome.reason == "permit-exceeded":
            raise PermitExceeded(_fact_from(outcome.detail), authority.permit.summary())
        return outcome

    return act


def _run_probe(work: Path) -> list:
    port = _STATE.get(work, {}).get("port")
    return list(port.appended) if port is not None else []


# --- holdings family, certified volume ----------------------------------------------

def _context(authority: Authority, work: Path):
    from beliefs.holdings.boundary import ActContext
    from beliefs.root import holdings_seam

    return ActContext(work / "observer", work / "store", "observer", "instrument", authority, holdings_seam())


def _prepare_holdings(held: tuple[str, ...] = (), *, intent: bool = False):
    def prepare(work: Path, _request) -> None:
        from beliefs.holdings import boundary
        from beliefs.holdings.boundary import StoreLocator
        from beliefs.root import init_corpus_root, init_store_root

        init_corpus_root(work / "observer", authority=lacking())
        store_id = init_store_root(work / "store", authority=lacking())
        ctx = _context(lacking(), work)
        for name in held:
            ctx.seam.store_write(ctx.store_root, name, b"held")
        state = {"store_id": store_id}
        if intent:
            state["token"], state["intent"] = boundary._append(ctx, StoreLocator(store_id, "held.bin"), "write")
        _STATE[work] = state

    return prepare


def _holdings(act: str):
    def run(authority, work):
        from beliefs.holdings import boundary
        from beliefs.holdings.boundary import StoreLocator
        from beliefs.holdings.records import Found

        ctx, store_id = _context(authority, work), _STATE[work]["store_id"]
        if act == "recheck":
            return boundary.recheck(ctx, StoreLocator(store_id, "held.bin"))
        if act == "write":
            return boundary.write(ctx, StoreLocator(store_id, "written.bin"), b"bytes")
        if act == "delete":
            return boundary.delete(ctx, StoreLocator(store_id, "held.bin"))
        if act == "move":
            return boundary.move(ctx, StoreLocator(store_id, "held.bin"), StoreLocator(store_id, "moved.bin"))
        if act == "_append":
            return boundary._append(ctx, StoreLocator(store_id, "held.bin"), "write")
        return boundary._publish(ctx, StoreLocator(store_id, "held.bin"), Found("sha256:" + "1" * 64),
                                 _STATE[work]["token"], _STATE[work]["intent"], ())

    return run


def _holdings_probe(work: Path):
    return (_chain(work / "observer") if (work / "observer").exists() else 0, _tree(work / "store"))


# --- registry and epoch families, default executor ----------------------------------

def _rebind(world: registry.World, authority: Authority) -> registry.World:
    return registry.World(
        world.config, world._executor_factory, chain_head=world._chain_head,
        corpus_executor_factory=world._corpus_executor_factory, authority=authority,
    )


def _prepare_admitted(work: Path, _request=None) -> None:
    from test_world_epoch import admitted_world

    world, _recorder, bindings, roots = admitted_world(work, ("a" * 32,))
    _STATE[work] = {"world": world, "bindings": bindings, "roots": roots}


def _prepare_fresh(work: Path, _request) -> None:
    from test_world_registry import write_manifest

    _prepare_admitted(work)
    write_manifest(work / "fresh", "b" * 32)


def _admit(authority, work):
    return _rebind(_STATE[work]["world"], authority).admit(work / "fresh", provenance=registry.Fresh())


def _retire(authority, work):
    return _rebind(_STATE[work]["world"], authority).retire(next(iter(_STATE[work]["roots"])))


def _prepare_anchor(work: Path, _request) -> None:
    from test_world_anchor_act import ALPHA, anchorable_world

    world, _recorder, heads, _roots = anchorable_world(work, ALPHA, authority=lacking())
    _STATE[work] = {"world": world, "heads": heads}


def _anchor(authority, work):
    from test_world_anchor_act import ALPHA, anchor

    return anchor(_rebind(_STATE[work]["world"], authority), _STATE[work]["heads"], ALPHA)


def _build_epoch(authority, work):
    from beliefs.world import epoch

    state = _STATE[work]
    return epoch.build_epoch(_rebind(state["world"], authority), coverage=frozenset(state["roots"]), bindings=state["bindings"])


def _prepare_retained(work: Path, _request) -> None:
    from test_world_gc import three_retained

    world, _recorder, _bindings, (first, _second, _third) = three_retained(work)
    _STATE[work] = {"world": world, "first": first}


def _delete_epoch(authority, work):
    from beliefs.world import epoch

    return epoch.delete_epoch(_rebind(_STATE[work]["world"], authority), _STATE[work]["first"].packaging_identity)


def _install_rule(authority, work):
    from test_world_rules import bundle, make_world

    from beliefs.world import rules

    return rules.install_rule_binding(make_world(work, authority=authority), bundle())


def _prepare_installed(work: Path, _request) -> None:
    from test_world_rules import bundle, make_world

    from beliefs.world import rules

    _STATE[work] = {"binding": rules.install_rule_binding(make_world(work, authority=lacking()), bundle())}


def _remove_rule(authority, work):
    from test_world_rules import make_world

    from beliefs.world import rules

    return rules.remove_rule_binding(make_world(work, authority=authority), _STATE[work]["binding"])


def _world_probe(work: Path):
    return _tree(work / "world")


# --- lifecycle family, certified volume ----------------------------------------------

def _prepare_lifecycle(act: str):
    def prepare(work: Path, _request) -> None:
        from test_fork_acts import _parent_corpus
        from test_restore_root import _head_of, _seeded_store, _store_record

        from beliefs.root import init_corpus_root, init_store_root, replicate_root

        if act == "replicate_root":
            init_corpus_root(work / "source", authority=lacking())
        elif act == "migrate_root_to_lifecycle_v3":
            (work / "bare").mkdir(exist_ok=True)
        elif act == "fork_corpus":
            _STATE[work] = {"parent": _parent_corpus(work)}
        elif act == "fork_store":
            init_store_root(work / "parent-store", authority=lacking())
        elif act == "restore_root":
            root, store_id = _seeded_store(work)
            genesis, head = _head_of(root)
            replicate_root(root, work / "restored", authority=lacking())
            _STATE[work] = {"store_id": store_id, "carrier": _store_record(store_id, genesis, head)}

    return prepare


def _lifecycle(act: str):
    def run(authority, work):
        from beliefs.root import (
            fork_corpus,
            fork_store,
            init_corpus_root,
            init_store_root,
            init_world_root,
            migrate_root_to_lifecycle_v3,
            replicate_root,
            restore_root,
        )
        from beliefs.world import WorldConfig, anchors, verify

        if act == "init_corpus_root":
            return init_corpus_root(work / "corpus", authority=authority)
        if act == "init_world_root":
            return init_world_root(WorldConfig(work / "world", "0" * 32, ()), authority=authority)
        if act == "init_store_root":
            return init_store_root(work / "store", authority=authority)
        if act == "replicate_root":
            return replicate_root(work / "source", work / "replica", authority=authority)
        if act == "migrate_root_to_lifecycle_v3":
            return migrate_root_to_lifecycle_v3(work / "bare", authority=authority)
        if act == "fork_corpus":
            return fork_corpus(_STATE[work]["parent"], work / "child", authority=authority)
        if act == "fork_store":
            return fork_store(work / "parent-store", work / "child-store", authority=authority)
        state = _STATE[work]
        return restore_root(work / "restored", anchors.StoreSubject(state["store_id"]),
                            verify.ObserverSet((state["carrier"],)), authority=authority)

    return run


def _lifecycle_probe(work: Path):
    return _tree(work)


def _lifecycle_case(name: str, act: str) -> Case:
    return Case(f"root.py:{name}", "lifecycle", (), True, _prepare_lifecycle(act), _lifecycle(act), _lifecycle_probe)


def _mint_eligible(writer):
    from test_retract import mint_eligible_assessment

    return mint_eligible_assessment(writer)


def _mint_predecessor(writer):
    from test_supersede import prop

    return writer.add(prop("p1"))


def _mint_proposition(writer):
    from test_revise import prop

    return writer.add(prop("p"))


CASES = (
    Case("corpus.py:CorpusWriter.add", "corpus-write", ("dataset",), False, _prepare_corpus(), _add, _corpus_probe),
    Case("corpus.py:CorpusWriter.retract", "corpus-write", ("retraction",), False, _prepare_corpus(_mint_eligible), _retract, _corpus_probe),
    Case("corpus.py:CorpusWriter.supersede", "corpus-write", ("proposition",), False, _prepare_corpus(_mint_predecessor), _supersede, _corpus_probe),
    Case("corpus.py:CorpusWriter.revise", "corpus-write", ("proposition",), False, _prepare_corpus(_mint_proposition), _revise, _corpus_probe),
    Case("corpus.py:CorpusWriter.mint_coordination", "corpus-write", ("project",), False, _prepare_coordination(False), _mint_coordination, _coordination_probe),
    Case("corpus.py:CorpusWriter.revise_coordination", "corpus-write", ("project",), False, _prepare_coordination(True), _revise_coordination, _coordination_probe),
    Case("corpus.py:CorpusWriter.import_bundle", "corpus-write", ("proposition", "act-report"), False, _prepare_import, _import_bundle, _import_probe),
    Case("corpus.py:CorpusWriter.adopt_manifest", "lifecycle", (), False, _prepare_corpus(), _adopt_manifest, _corpus_probe),
    Case("corpus.py:CorpusWriter._add_locked", "corpus-write", ("proposition",), False, _prepare_corpus(), _add_locked, _corpus_probe),
    Case("corpus.py:CorpusWriter._replace_locked", "corpus-write", ("proposition",), False, _prepare_corpus(_mint_proposition), _replace_locked, _corpus_probe),
    Case("corpus.py:CorpusWriter._delete_locked", "corpus-write", ("proposition",), False, _prepare_corpus(_mint_proposition), _delete_locked, _corpus_probe),
    Case("corpus.py:CorpusWriter._append_operation_intent", "corpus-write", ("act-report",), False, _prepare_corpus(port=True), _append_operation_intent, _corpus_probe),
    Case("corpus.py:CorpusWriter._publish_operation_report", "corpus-write", ("act-report",), False, _prepare_corpus(port=True), _publish_operation_report, _corpus_probe),
    Case("corpus.py:_RoutedExecutor.commit_fulfilling", "corpus-write", ("proposition",), False, _prepare_corpus(port=True), _commit_fulfilling, _corpus_probe),
    Case("boundary.py:execute_assessment_run", "run", ("run", "act-report"), False, _nothing, _run("assessment"), _run_probe),
    Case("boundary.py:execute_production_run", "run", ("run", "act-report"), False, _nothing, _run("production"), _run_probe),
    Case("holdings/boundary.py:recheck", "holdings", ("holdings-observation",), True, _prepare_holdings(("held.bin",)), _holdings("recheck"), _holdings_probe),
    Case("holdings/boundary.py:write", "holdings", ("holdings-observation",), True, _prepare_holdings(), _holdings("write"), _holdings_probe),
    Case("holdings/boundary.py:delete", "holdings", ("holdings-observation",), True, _prepare_holdings(("held.bin",)), _holdings("delete"), _holdings_probe),
    Case("holdings/boundary.py:move", "holdings", ("holdings-observation",), True, _prepare_holdings(("held.bin",)), _holdings("move"), _holdings_probe),
    Case("holdings/boundary.py:_append", "holdings", ("holdings-observation",), True, _prepare_holdings(), _holdings("_append"), _holdings_probe),
    Case("holdings/boundary.py:_publish", "holdings", ("holdings-observation",), True, _prepare_holdings(("held.bin",), intent=True), _holdings("_publish"), _holdings_probe),
    Case("world/registry.py:_locked_admit", "registry", (), False, _prepare_fresh, _admit, _world_probe),
    Case("world/registry.py:World._terminal", "registry", (), False, _prepare_admitted, _retire, _world_probe),
    Case("world/anchors.py:_anchor_heads", "registry", (), False, _prepare_anchor, _anchor, _world_probe),
    Case("world/epoch.py:build_epoch", "epoch", (), False, _prepare_admitted, _build_epoch, _world_probe),
    Case("world/epoch.py:delete_epoch", "epoch", (), False, _prepare_retained, _delete_epoch, _world_probe),
    Case("world/rules.py:install_rule_binding", "epoch", (), False, _nothing, _install_rule, _world_probe),
    Case("world/rules.py:remove_rule_binding", "epoch", (), False, _prepare_installed, _remove_rule, _world_probe),
    _lifecycle_case("init_corpus_root", "init_corpus_root"),
    _lifecycle_case("init_world_root", "init_world_root"),
    _lifecycle_case("init_store_root", "init_store_root"),
    _lifecycle_case("replicate_root", "replicate_root"),
    _lifecycle_case("migrate_root_to_lifecycle_v3", "migrate_root_to_lifecycle_v3"),
    _lifecycle_case("restore_root.grant", "restore_root"),
    _lifecycle_case("fork_corpus", "fork_corpus"),
    _lifecycle_case("fork_store", "fork_store"),
)


def test_the_cases_cover_the_inventory_exactly():
    keys = [case.key for case in CASES]
    assert len(keys) == len(set(keys))
    assert set(keys) == set(WRITE_ENTRY_POINTS)
    for case in CASES:
        assert case.family == WRITE_ENTRY_POINTS[case.key], case.key


def _work(case: Case, tmp_path: Path, request, sub: str) -> Path:
    base = request.getfixturevalue("certified_work") if case.needs_volume else tmp_path
    work = base / (case.id + sub)
    work.mkdir(parents=True, exist_ok=True)
    return work


@pytest.mark.parametrize("case", CASES, ids=[case.id for case in CASES])
def test_e1_the_family_is_refused_with_no_effect(case, tmp_path, request):
    work = _work(case, tmp_path, request, "-family")
    case.prepare(work, request)
    before = case.probe(work)
    with pytest.raises(PermitExceeded) as caught:
        case.act(lacking(families=(case.family,)), work)
    assert caught.value.requirement == PermitFact("family", case.family)
    assert case.probe(work) == before


@pytest.mark.parametrize("case", [case for case in CASES if case.kinds], ids=[case.id for case in CASES if case.kinds])
def test_e1_each_emitted_kind_is_refused_by_name_with_no_effect(case, tmp_path, request):
    for kind in case.kinds:
        work = _work(case, tmp_path, request, f"-{kind}")
        case.prepare(work, request)
        before = case.probe(work)
        with pytest.raises(PermitExceeded) as caught:
            case.act(lacking(kinds=(kind,)), work)
        assert caught.value.requirement == PermitFact("kind", kind)
        assert case.probe(work) == before


@pytest.mark.parametrize("case", CASES, ids=[case.id for case in CASES])
def test_e1_the_exact_requirement_is_accepted(case, tmp_path, request):
    work = _work(case, tmp_path, request, "-exact")
    case.prepare(work, request)
    authority = narrowed(kinds=case.kinds, families=(case.family,))
    if case.key == "root.py:migrate_root_to_lifecycle_v3":
        from atoms.core.errors import PreconditionRefused  # the engine's own refusal, past the permit

        with pytest.raises(PreconditionRefused):
            case.act(authority, work)
        return
    case.act(authority, work)
