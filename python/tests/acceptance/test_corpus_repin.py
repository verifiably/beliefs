"""Certified-engine manifest replacement, interruption and recovery evidence."""

from hashlib import sha256

import pytest
from authority import FULL
from fixtures.repin import repin_chain
from profiles import pins_for

from beliefs import root as composition
from beliefs import stored
from beliefs.claim import Referent, build_claim
from beliefs.decode import WireClaim, decode_claim
from beliefs.errors import ContractMismatch
from beliefs.projection import project_claim
from beliefs.resolution import build_snapshot
from beliefs.world import corpus_state_identity, load_manifest
from beliefs.world.logmodel import RegisteredEntryView, SettledEntryView, WellFormedView


def chain(root):
    view = composition.log_seam().inspect_detached(root)
    assert isinstance(view, WellFormedView)
    return view


def pending(root):
    view = chain(root)
    settled = {entry.registration for entry in view.entries if isinstance(entry, SettledEntryView)}
    return [entry for entry in view.entries if isinstance(entry, RegisteredEntryView) and entry.digest not in settled]


def claim(profile, sort="entity"):
    return build_claim(
        profile, operator="repin/relates", roles={"subject": Referent(f"repin/{sort}", "EX:a")}, layer="structural"
    )


def test_repin_real_engine_journey(durable_root):
    _, contracts, profiles, _ = repin_chain()
    writer = composition.open_corpus(durable_root, authority=FULL, profile=profiles[0])
    original = writer.adopt_manifest(profile=pins_for(profiles[0]))
    node = stored.proposition_node("original", title="original", claim=project_claim(claim(profiles[0])))
    node.facets["repin/label"] = {"value": "kept"}
    minted = writer.add(node)
    path = durable_root / "proposition" / "original.md"
    record_bytes = path.read_bytes()
    genesis = chain(durable_root).genesis
    old_port = writer.operations
    for index in (1, 2):
        before = (durable_root / "corpus.yaml").read_bytes()
        state_before = corpus_state_identity(durable_root)
        updated = writer.repin_domain(
            predecessor=contracts[index - 1], successor=contracts[index], profile=profiles[index]
        )
        after = (durable_root / "corpus.yaml").read_bytes()
        assert updated.corpus_id == original.corpus_id
        assert corpus_state_identity(durable_root) != state_before
        entries = [entry for entry in chain(durable_root).entries if isinstance(entry, RegisteredEntryView)]
        entry = entries[-1]
        assert entry.fulfills is None
        assert dict(entry.initial)["corpus.yaml"].content_hash == "sha256:" + sha256(before).hexdigest()
        assert dict(entry.final)["corpus.yaml"].content_hash == "sha256:" + sha256(after).hexdigest()
        with pytest.raises(ContractMismatch):
            writer.add(stored.proposition_node("stale", title="stale", claim=project_claim(claim(profiles[index - 1]))))
        with pytest.raises(ContractMismatch):
            old_port.add(node)
        writer = composition.open_corpus(durable_root, authority=FULL, profile=profiles[index])
        read = writer.read_view.get(minted.id)
        assert (read.id, read.uid, read.facets) == (minted.id, minted.uid, minted.facets)
        assert path.read_bytes() == record_bytes
        decoded, _ = decode_claim(
            WireClaim(**project_claim(claim(profiles[0]))), profile=profiles[index], snapshot=build_snapshot()
        )
        assert project_claim(decoded) == project_claim(claim(profiles[0]))
        writer.add(
            stored.proposition_node(
                f"added-{index}", title="new sort", claim=project_claim(claim(profiles[index], f"added-{index + 1}"))
            )
        )
    assert chain(durable_root).genesis == genesis
    assert load_manifest(durable_root).profile == pins_for(profiles[2])


class ManifestFaultBackend:
    """Trace real publishes; optionally halt all subsequent publishes, including rollback."""

    def __init__(self, inner, manifest, *, stop=None):
        self.inner, self.manifest, self.stop = inner, manifest, stop
        self.publishes = []
        self.armed = True

    def __getattr__(self, name):
        target = getattr(self.inner, name)
        if name not in ("exchange", "transfer_noclobber", "link_anchor"):
            return target

        def publish(*args, **kwargs):
            if self.armed and self.stop is not None and len(self.publishes) >= self.stop:
                raise OSError("manifest publish interrupted")
            result = target(*args, **kwargs)
            self.publishes.append((name, self.manifest.read_bytes()))
            return result

        return publish


def test_manifest_publish_trace(durable_root, monkeypatch):
    _, contracts, profiles, _ = repin_chain()
    writer = composition.open_corpus(durable_root, authority=FULL, profile=profiles[0])
    writer.adopt_manifest(profile=pins_for(profiles[0]))
    before = (durable_root / "corpus.yaml").read_bytes()
    backend = ManifestFaultBackend(composition._PRODUCTION_BACKEND, durable_root / "corpus.yaml")
    monkeypatch.setattr(composition, "_PRODUCTION_BACKEND", backend)
    writer.repin_domain(predecessor=contracts[0], successor=contracts[1], profile=profiles[1])
    print(
        "manifest publish calls:",
        [(i, name, "old" if value == before else "target") for i, (name, value) in enumerate(backend.publishes)],
    )
    assert [(name, value == before) for name, value in backend.publishes][8] == ("exchange", False)


@pytest.mark.parametrize("stop,visible", [(8, "old"), (9, "target")])
def test_repin_interrupted_then_recovered(durable_root, monkeypatch, stop, visible):
    from nodes.core.write_plan import ExecutionError

    _, contracts, profiles, _ = repin_chain()
    writer = composition.open_corpus(durable_root, authority=FULL, profile=profiles[0])
    writer.adopt_manifest(profile=pins_for(profiles[0]))
    backend = ManifestFaultBackend(composition._PRODUCTION_BACKEND, durable_root / "corpus.yaml", stop=stop)
    monkeypatch.setattr(composition, "_PRODUCTION_BACKEND", backend)
    with pytest.raises(ExecutionError):
        writer.repin_domain(predecessor=contracts[0], successor=contracts[1], profile=profiles[1])
    assert pending(durable_root), "a real transaction must remain unsettled"
    assert load_manifest(durable_root).profile == pins_for(profiles[0 if visible == "old" else 1])
    # Recovery is attempted before manifest validation and itself refuses while faulted.
    with pytest.raises(ExecutionError, match="recovery failed"):
        writer.repin_domain(predecessor=contracts[0], successor=contracts[1], profile=profiles[1])
    assert pending(durable_root)
    backend.armed = False
    try:
        writer.repin_domain(predecessor=contracts[0], successor=contracts[1], profile=profiles[1])
    except ContractMismatch:
        # The engine may finish a target-visible transaction; retry does not report success.
        assert visible == "target"
        assert load_manifest(durable_root).profile == pins_for(profiles[1])
    else:
        assert visible == "old"
    assert not pending(durable_root)
    assert load_manifest(durable_root).profile == pins_for(profiles[1])


def test_manifest_stale_preimage_refused(durable_root):
    from nodes.core.write_plan import ExecutionError, ReplaceOp

    _, _, profiles, _ = repin_chain()
    writer = composition.open_corpus(durable_root, authority=FULL, profile=profiles[0])
    writer.adopt_manifest(profile=pins_for(profiles[0]))
    before = (durable_root / "corpus.yaml").read_bytes()
    entries = chain(durable_root).entries
    with pytest.raises(ExecutionError):
        composition.durable_executor_factory()(durable_root).execute([ReplaceOp("corpus.yaml", b"stale", "0" * 64)])
    assert (durable_root / "corpus.yaml").read_bytes() == before
    assert chain(durable_root).entries == entries
