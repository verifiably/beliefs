"""The fixture-bound rules store: a world holds a rule, verifies it, and runs it.

A derivation receipt names the exact rule that produced its map, so the world
has to be able to *hold* that rule — store its normative fixtures, store one or
more conforming implementations of it, and prove at any later moment that the
implementation it is about to run is still the one the receipt names. Slice 2's
specification §4 pins the two identities that make this possible, and both
domain strings are minted here:

* a **fixture-set identity** is `science.fixture-set.v1` over the sorted
  `(member name, member content digest)` pairs; and
* a **rule identity** is `science.enumeration-rule.v1` over
  `(symbol, fixture-set identity)`.

A **member content digest** is the 64-character lowercase SHA-256 hex digest of
that member's exact bytes, and an implementation's content identity is the same
digest over its source. A runnable binding is therefore the exact pair
`(rule_identity, implementation_identity)`, stored as::

    rules/<rule_identity>/rule.yaml
    rules/<rule_identity>/fixtures/<fixture members>
    rules/<rule_identity>/implementations/<implementation_identity>

The layout keeps the normative half — the symbol and its fixtures — shared, and
several conforming implementations of one rule beside each other without
pretending they are one implementation. Nothing here selects among them: a
receipt resolves the exact pair it names, never "the implementation this
installation would choose today". There is deliberately no registry, no entry
point, and no installed default to consult.

**The loader is a trusted-code admission boundary, not a sandbox.** An
implementation is executable content, and executing it is exactly what holding
it means. What this module guarantees is *which* bytes run: an explicit install
act admitted them, their digest names them, and the normative fixtures pass
against them at admission and again at every resolution. It is not a security
boundary and does not pretend to be one. The rule ABI is correspondingly small:
the entry point receives one immutable projection value and returns one
projection value. No world, corpus, path or executor is reachable from it.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from hashlib import sha256
from importlib import resources
from pathlib import Path
from types import MappingProxyType

import yaml
from nodes.core.write_plan import CreateOp, DeleteOp, WritePlan

from beliefs.errors import RuleBindingUnknown, RuleCollision, RuleNonconformant, RuleNotHeld
from beliefs.identity import v1
from beliefs.world import epoch
from beliefs.world.registry import World, _ManifestLoader

__all__ = [
    "FIXTURE_SET_DOMAIN",
    "RULE_DOMAIN",
    "RuleBinding",
    "RuleBundle",
    "RuleRemovalReport",
    "binding_for",
    "fixture_set_identity",
    "implementation_identity",
    "install_rule_binding",
    "member_content_digest",
    "parse_rule_document",
    "remove_rule_binding",
    "rule_document_bytes",
    "rule_identity",
    "shipped_rule_bundles",
]

FIXTURE_SET_DOMAIN = "science.fixture-set.v1"
RULE_DOMAIN = "science.enumeration-rule.v1"

_SYMBOL = re.compile(r"^[a-z][a-z0-9_]*$")
_MEMBER_NAME = re.compile(r"^[a-z0-9][a-z0-9._-]*$")

_SHIPPED: tuple[tuple[str, str], ...] = (
    ("certification", "enumerate_certifications"),
    ("coreference", "reduce_coreference"),
    ("producer", "derive_producer_snapshot"),
    ("retraction", "enumerate_retractions"),
)
"""The four v1 enumeration rules this package ships, as `(module, symbol)`.

The module is the implementation resource `rules_v1/<module>.py` and the prefix
of its fixture members, `rules_v1/fixtures/<module>.<case>.yaml`. Fixture
members are *discovered*, never listed here: a normative fixture set grows as
the contract gains cases, and a second list of them would be a place for the
shipped bytes and the shipped identity to disagree.
"""

_RULES_PACKAGE = "beliefs.world.rules_v1"


class _RuleRefusal(Exception):
    """A check inside this module failed.

    Private on purpose: the same failure is `RuleNonconformant` when it happens
    while admitting content and `RuleNotHeld` when it happens while resolving
    stored content, and only the call site knows which it is doing.
    """


@dataclass(frozen=True)
class RuleBinding:
    """The exact runnable pair a receipt names."""

    rule_identity: str
    implementation_identity: str

    def __post_init__(self) -> None:
        _require_digest(self.rule_identity, "rule_identity")
        _require_digest(self.implementation_identity, "implementation_identity")


@dataclass(frozen=True)
class RuleBundle:
    """Installable content: one symbol, its fixture members, one implementation.

    Fixture members are held in whatever order the caller supplies and ordered
    by name wherever identity or storage depends on it, so a bundle assembled
    from a directory listing and one assembled by hand are the same bundle.
    """

    symbol: str
    fixtures: tuple[tuple[str, bytes], ...]
    implementation: bytes

    def __post_init__(self) -> None:
        _require_symbol(self.symbol)
        if type(self.fixtures) is not tuple:
            raise TypeError("fixtures must be an exact tuple")
        if type(self.implementation) is not bytes:
            raise TypeError("implementation must be exact bytes")
        seen: set[str] = set()
        for member in self.fixtures:
            if type(member) is not tuple or len(member) != 2:
                raise TypeError("each fixture must be an exact (name, content) pair")
            name, content = member
            _require_member_name(name)
            if type(content) is not bytes:
                raise TypeError(f"fixture {name!r} content must be exact bytes")
            if name in seen:
                raise ValueError(f"fixture name {name!r} occurs twice")
            seen.add(name)


@dataclass(frozen=True)
class _StoredRule:
    """One exact pair's stored members, each verified to recompute its own
    name. It says what the store *holds under this name*, not whether running
    it still works — `_HeldRule` is that, and is strictly stronger."""

    binding: RuleBinding
    symbol: str
    document: bytes
    fixtures: tuple[tuple[str, bytes], ...]
    source: bytes


@dataclass(frozen=True)
class _HeldRule:
    """A verified binding: the stored symbol, the exact source, and the entry
    point loaded from it. Build and receipt code takes the callable *and* the
    bytes, because a receipt records what it ran, not what it meant to run."""

    binding: RuleBinding
    symbol: str
    source: bytes
    invoke: Callable[[object], object]


# --- identities -------------------------------------------------------------


def member_content_digest(content: bytes) -> str:
    """The 64-character lowercase SHA-256 hex digest of a member's exact bytes."""
    if type(content) is not bytes:
        raise TypeError("a member content digest is taken over exact bytes")
    return sha256(content).hexdigest()


def implementation_identity(implementation: bytes) -> str:
    """An implementation's content identity: the digest of its source bytes."""
    return member_content_digest(implementation)


def fixture_set_identity(fixtures: Iterable[tuple[str, bytes]]) -> str:
    """`science.fixture-set.v1` over sorted `(name, member content digest)` pairs."""
    return v1.digest(
        FIXTURE_SET_DOMAIN,
        [[name, member_content_digest(content)] for name, content in _ordered(fixtures)],
    )


def rule_identity(symbol: str, fixtures: Iterable[tuple[str, bytes]]) -> str:
    """`science.enumeration-rule.v1` over `(symbol, fixture-set identity)`.

    The pair is encoded as a two-member list, the same shape the fixture-set
    pairs use, so one reading of "a pair" serves both formulas.
    """
    return v1.digest(RULE_DOMAIN, [_require_symbol(symbol), fixture_set_identity(fixtures)])


def binding_for(bundle: RuleBundle) -> RuleBinding:
    """The exact pair this bundle would be held as."""
    return RuleBinding(
        rule_identity(bundle.symbol, bundle.fixtures),
        implementation_identity(bundle.implementation),
    )


# --- the closed documents ---------------------------------------------------


def rule_document_bytes(symbol: str) -> bytes:
    """`rule.yaml`: exactly the rule symbol, and nothing else."""
    return yaml.safe_dump({"symbol": _require_symbol(symbol)}, sort_keys=True, allow_unicode=True).encode("utf-8")


def parse_rule_document(content: bytes) -> str:
    """The symbol a stored `rule.yaml` carries, or a refusal.

    A document that is not exactly `{symbol: <symbol>}` — a duplicate key, an
    unknown key, a missing or non-symbol value — means the store cannot say
    which entry point the rule names, so the binding is not held.
    """
    try:
        document = yaml.load(content.decode("utf-8"), Loader=_ManifestLoader)
        if type(document) is not dict or set(document) != {"symbol"}:
            raise ValueError("a rule document must have exactly ['symbol']")
        return _require_symbol(document["symbol"])
    except Exception as caught:
        raise RuleNotHeld(f"malformed rule document: {caught}") from caught


def _parse_fixture_document(name: str, content: bytes) -> tuple[object, object]:
    """A fixture: exactly `input` and `expected`, closed the same way."""
    try:
        document = yaml.load(content.decode("utf-8"), Loader=_ManifestLoader)
        if type(document) is not dict or set(document) != {"input", "expected"}:
            raise ValueError("a fixture document must have exactly ['expected', 'input']")
        return document["input"], document["expected"]
    except Exception as caught:
        raise _RuleRefusal(f"fixture {name!r} is malformed: {caught}") from caught


# --- running an implementation ----------------------------------------------


def _load_entry_point(symbol: str, source: bytes) -> Callable[[object], object]:
    namespace: dict[str, object] = {"__name__": f"<rule {symbol}>", "__file__": f"<rule {symbol}>"}
    try:
        exec(compile(source, f"<rule {symbol}>", "exec"), namespace)  # noqa: S102 — admitted trusted content
    except Exception as caught:
        raise _RuleRefusal(f"implementation of {symbol!r} does not load: {caught}") from caught
    entry = namespace.get(symbol)
    if not callable(entry):
        raise _RuleRefusal(f"implementation defines no callable {symbol!r}")

    def invoke(value: object) -> object:
        """The whole rule ABI: one immutable projection value in, one
        projection value out. Every caller goes through here — a fixture run
        and a build run must hand the entry point the same shapes, or the
        fixtures are checking an ABI nobody else uses."""
        return entry(_frozen(value))

    return invoke


def _frozen(value: object) -> object:
    """The rule's argument, with nothing it can write through.

    A projection value is data; handing a reducer a live mapping would let one
    fixture's outcome depend on an earlier one's mutations, which is exactly
    the non-determinism the fixtures exist to exclude.
    """
    if type(value) is dict:
        return MappingProxyType({key: _frozen(member) for key, member in value.items()})
    if type(value) is list:
        return tuple(_frozen(member) for member in value)
    return value


def _run_fixtures(
    symbol: str,
    invoke: Callable[[object], object],
    fixtures: Sequence[tuple[str, bytes]],
) -> None:
    if not fixtures:
        raise _RuleRefusal(f"{symbol!r} has no fixture member; an unbound rule is never conformant")
    for name, content in fixtures:
        supplied, expected = _parse_fixture_document(name, content)
        try:
            produced = invoke(supplied)
        except Exception as caught:
            raise _RuleRefusal(f"{symbol!r} raised on fixture {name!r}: {caught}") from caught
        try:
            same = v1.encode(produced) == v1.encode(expected)
        except Exception as caught:
            raise _RuleRefusal(f"{symbol!r} returned a non-projection value on fixture {name!r}: {caught}") from caught
        if not same:
            raise _RuleRefusal(f"{symbol!r} does not satisfy fixture {name!r}")


# --- the shipped bundles ----------------------------------------------------


def shipped_rule_bundles() -> tuple[RuleBundle, ...]:
    """The four v1 enumeration rules this package ships, read from package
    content. Nothing installs them; that act is the composition root's."""
    package = resources.files(_RULES_PACKAGE)
    bundles: list[RuleBundle] = []
    for module, symbol in _SHIPPED:
        prefix = f"{module}."
        fixtures = tuple(
            sorted(
                (member.name, member.read_bytes())
                for member in (package / "fixtures").iterdir()
                if member.is_file() and member.name.startswith(prefix) and member.name.endswith(".yaml")
            )
        )
        if not fixtures:
            raise RuleNonconformant(f"{_RULES_PACKAGE} ships no fixture member for {module!r}")
        bundles.append(RuleBundle(symbol, fixtures, (package / f"{module}.py").read_bytes()))
    return tuple(bundles)


# --- installation -----------------------------------------------------------


def install_rule_binding(world: World, bundle: RuleBundle) -> RuleBinding:
    """Hold one exact pair, in one create-only world-root transaction.

    Identities are computed and the implementation is run against every fixture
    *before* a write plan exists, so nonconformant content never reaches the
    executor. Exact, byte-identical reinstallation is idempotent success and
    submits no transaction at all; a content-addressed path holding different
    bytes is a collision, never an overwrite.
    """
    world.authority.require("epoch")
    binding = binding_for(bundle)
    members = _member_bytes(bundle, binding)
    with world._state.lock:
        try:
            invoke = _load_entry_point(bundle.symbol, bundle.implementation)
            _run_fixtures(bundle.symbol, invoke, _ordered(bundle.fixtures))
        except _RuleRefusal as caught:
            raise RuleNonconformant(f"{binding.rule_identity}: {caught}") from caught
        plan = _create_only_plan(world.config.world_root, members)
        if plan:
            world._executor_factory(world.config.world_root).execute(plan)
    return binding


def _member_bytes(bundle: RuleBundle, binding: RuleBinding) -> tuple[tuple[str, bytes], ...]:
    """Every stored path this binding owns, in one deterministic order."""
    directory = f"rules/{binding.rule_identity}"
    return (
        (f"{directory}/rule.yaml", rule_document_bytes(bundle.symbol)),
        *(
            (f"{directory}/fixtures/{name}", content)
            for name, content in _ordered(bundle.fixtures)
        ),
        (f"{directory}/implementations/{binding.implementation_identity}", bundle.implementation),
    )


def _create_only_plan(world_root: Path, members: Sequence[tuple[str, bytes]]) -> WritePlan:
    plan: list[CreateOp] = []
    for path, content in members:
        target = world_root / path
        if target.is_symlink() or (target.exists() and not target.is_file()):
            raise RuleCollision(f"{target}: a content-addressed rule path is not a regular file")
        if target.exists():
            if target.read_bytes() != content:
                raise RuleCollision(f"{target}: a content-addressed rule path holds different bytes")
            continue
        plan.append(CreateOp(path, content))
    return plan


# --- held resolution --------------------------------------------------------


def _resolve_rule_binding(world: World, binding: RuleBinding) -> _HeldRule:
    """The verified callable and the exact source bytes for one held pair.

    Held **iff** every check succeeds: the stored fixture bytes recompute the
    fixture-set identity, the stored symbol and that identity recompute the
    directory name, the named implementation's bytes recompute its content
    name, and the entry point loaded from those bytes satisfies every stored
    fixture. Anything else is `RuleNotHeld` — this store resolves the exact
    pair it was asked for or nothing.
    """
    with world._state.lock:
        return _locked_resolve_rule_binding(world.config.world_root, binding)


def _locked_resolve_rule_binding(world_root: Path, binding: RuleBinding) -> _HeldRule:
    """The held check itself: every stored member recomputes its own name, and
    the entry point loaded from those bytes satisfies every stored fixture. The
    caller holds the world lock; this must not take it, and the lock is not
    reentrant."""
    directory = world_root / "rules" / binding.rule_identity
    try:
        stored = _locked_stored_rule(world_root, binding)
        invoke = _load_entry_point(stored.symbol, stored.source)
        _run_fixtures(stored.symbol, invoke, stored.fixtures)
    except _RuleRefusal as caught:
        raise RuleNotHeld(f"{directory}: {caught}") from caught
    return _HeldRule(binding, stored.symbol, stored.source, invoke)


def _locked_resolve_rule_bindings(
    world_root: Path, bindings: Mapping[str, RuleBinding]
) -> Mapping[str, _HeldRule]:
    """Every named exact pair, resolved under one already-held world lock.

    A build resolves its four bindings at preflight and the same four again
    before publication, and both moments want the same thing: all of them held,
    or the first refusal. Resolution runs in sorted key order so that a world
    holding none of them refuses on the same one every time — a refusal whose
    identity depended on mapping order would make the failure mode unpinnable.

    The caller holds the world lock; this must not take it, and the lock is not
    reentrant.
    """
    return MappingProxyType(
        {name: _locked_resolve_rule_binding(world_root, bindings[name]) for name in sorted(bindings)}
    )


def _locked_stored_rule(world_root: Path, binding: RuleBinding) -> _StoredRule:
    """The stored members of one exact pair, each recomputing its own name.

    This is the *naming* half of the held check, without the *running* half.
    The two answer different questions. "Are these the bytes this pair names?"
    is what makes an act on stored content safe: without it a tampered member
    could be run — or deleted — under a name it no longer has. "Does this
    implementation still satisfy its fixtures?" is what makes it trustworthy to
    run, and an act that only deletes does not need an answer.

    Resolution needs both and takes both. Removal (§4.3) needs the first alone,
    so that a store you can install into does not become a store you cannot
    clean up: an intact, correctly named binding whose implementation has
    stopped conforming is exactly the binding an operator most needs to be able
    to unhold. The caller holds the world lock and names the refusal;
    `_RuleRefusal` stays neutral between them.
    """
    directory = world_root / "rules" / binding.rule_identity
    try:
        document = _read_member(directory / "rule.yaml")
        symbol = parse_rule_document(document)
        fixtures = _read_fixtures(directory / "fixtures")
        if rule_identity(symbol, fixtures) != binding.rule_identity:
            raise _RuleRefusal("the stored symbol and fixtures do not recompute the rule identity")
        source = _read_member(directory / "implementations" / binding.implementation_identity)
        if implementation_identity(source) != binding.implementation_identity:
            raise _RuleRefusal("the stored implementation does not recompute its content identity")
    except RuleNotHeld as caught:
        raise _RuleRefusal(str(caught)) from caught
    return _StoredRule(binding, symbol, document, fixtures, source)


def _read_member(path: Path) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise _RuleRefusal(f"{path.name!r}: no regular stored member")
    return path.read_bytes()


def _read_fixtures(directory: Path) -> tuple[tuple[str, bytes], ...]:
    if directory.is_symlink() or not directory.is_dir():
        raise _RuleRefusal(f"{directory}: no fixture directory")
    members: list[tuple[str, bytes]] = []
    for path in directory.iterdir():
        if path.is_symlink() or not path.is_file() or not _MEMBER_NAME.fullmatch(path.name):
            raise _RuleRefusal(f"{path.name!r} is not a regular fixture member")
        members.append((path.name, path.read_bytes()))
    return _ordered(members)


# --- explicit removal -------------------------------------------------------


@dataclass(frozen=True)
class RuleRemovalReport:
    """What one removal unheld, and what evidence it severed.

    `severed_receipts` names every receipt carried by a retained epoch of this
    world that named the removed pair and so loses *this* store's resolution
    path. Whether such a receipt is `unresolvable` is not this world's call
    alone — another consulted store may hold the same pair — so the report
    states what was severed here and stops there.

    Identities are sorted and distinct. Two epochs may carry the same receipt;
    the receipt severed is one receipt either way.
    """

    binding: RuleBinding
    severed_receipts: tuple[str, ...]


def remove_rule_binding(world: World, binding: RuleBinding) -> RuleRemovalReport:
    """Unhold one exact pair, in one delete-only world-root transaction.

    The act is the inverse of `install_rule_binding` and nothing wider. It
    deletes the named implementation member and — only when that was the final
    implementation held for the rule — the shared normative half, `rule.yaml`
    and every fixture member. Every stored member is verified to recompute its
    own name first, because deleting the fixtures means asserting they are the
    fixtures this pair names; the fixtures are *not* run, because a binding
    whose implementation has stopped conforming is still one an operator must
    be able to unhold (`_locked_stored_rule` carries the full reasoning).

    A sibling implementation of the same rule is not a successor to be tidied
    away: it is another held pair, and receipts naming it keep resolving.
    Emptied directories are nonsemantic and are left where they are; there is
    no tombstone and no sweep.

    The sever report is computed from the retained epochs *before* anything is
    deleted, and a carrier this world cannot read refuses the whole act. That
    ordering is the point of the report: removal may make evidence
    unresolvable, but it may not do so silently, and a scan that quietly
    skipped a damaged epoch would be exactly that.
    """
    world.authority.require("epoch")
    with world._state.lock:
        world_root = world.config.world_root
        directory = world_root / "rules" / binding.rule_identity
        try:
            stored = _locked_stored_rule(world_root, binding)
            held = _held_implementations(directory / "implementations")
        except _RuleRefusal as caught:
            raise RuleBindingUnknown(
                f"{binding.rule_identity}/{binding.implementation_identity}: no stored exact pair: {caught}"
            ) from caught
        severed = _severed_receipts(world_root, binding)
        world._executor_factory(world_root).execute(_delete_plan(stored, held))
    return RuleRemovalReport(binding, severed)


def _severed_receipts(world_root: Path, binding: RuleBinding) -> tuple[str, ...]:
    """Every retained receipt identity that loses this store's resolution path.

    Sorted and distinct: two epochs may carry one receipt, and the receipt
    severed is one receipt either way.

    A receipt the carrier layer could read but that did not carry all five of
    §7.5's identity members is *not* severed, and this is the one subtlety
    worth stating. Such a receipt has no identity to report, but the reason it
    is left out is not that it is awkward to name: §7.5 puts an unsound receipt
    contract at outcome ``malformed``, which is decided before resolvability is
    ever asked, so no change to what this store holds can move it. It was
    already the validator's finding, and it still is.
    """
    pair = (binding.rule_identity, binding.implementation_identity)
    severed: set[str] = set()
    for receipt in epoch._retained_receipt_bindings_locked(world_root):
        identity = receipt.identity
        if identity is not None and receipt.binding == pair:
            severed.add(identity)
    return tuple(sorted(severed))


def _held_implementations(directory: Path) -> tuple[str, ...]:
    """Every implementation member name held for one rule, sorted.

    Removal turns on whether the named pair is the rule's last one, so the
    sibling set is read with the same discipline as the fixture set: a stored
    entry that is not a regular content-addressed member leaves the store
    unable to say what is held, and removal refuses rather than guesses.
    """
    if directory.is_symlink() or not directory.is_dir():
        raise _RuleRefusal(f"{directory}: no implementation directory")
    names: list[str] = []
    for path in directory.iterdir():
        if path.is_symlink() or not path.is_file() or not re.fullmatch(r"[0-9a-f]{64}", path.name):
            raise _RuleRefusal(f"{path.name!r} is not a content-addressed implementation member")
        names.append(path.name)
    return tuple(sorted(names))


def _delete_plan(stored: _StoredRule, held: Sequence[str]) -> WritePlan:
    """The one transaction, innermost member first.

    Every path and every `expected_digest` comes from the members
    `_locked_stored_rule` just verified, so the bytes the plan claims to delete
    are the bytes whose names were checked — the plan does not go back to the
    directory for a second, unverified listing.

    The implementation goes before the normative half it was verified against,
    so no prefix of the plan ever leaves a rule holding fixtures it cannot bind
    to an implementation from.
    """
    prefix = f"rules/{stored.binding.rule_identity}"
    implementation = stored.binding.implementation_identity
    plan = [DeleteOp(f"{prefix}/implementations/{implementation}", member_content_digest(stored.source))]
    if tuple(held) == (implementation,):
        plan.extend(
            DeleteOp(f"{prefix}/fixtures/{name}", member_content_digest(content))
            for name, content in stored.fixtures
        )
        plan.append(DeleteOp(f"{prefix}/rule.yaml", member_content_digest(stored.document)))
    return plan


# --- shared checks ----------------------------------------------------------


def _ordered(fixtures: Iterable[tuple[str, bytes]]) -> tuple[tuple[str, bytes], ...]:
    members = tuple(sorted(fixtures))
    for name, _content in members:
        _require_member_name(name)
    if len({name for name, _content in members}) != len(members):
        raise ValueError("fixture names must be distinct")
    return members


def _require_symbol(symbol: object) -> str:
    if type(symbol) is not str or not _SYMBOL.fullmatch(symbol):
        raise ValueError(f"{symbol!r} is not a rule symbol; expected a lowercase Python identifier")
    return symbol


def _require_member_name(name: object) -> str:
    """A member name is relative and one path component. It becomes a path
    under the world root, so a separator, a traversal or a leading dot is
    refused here rather than discovered by the filesystem."""
    if type(name) is not str or not _MEMBER_NAME.fullmatch(name):
        raise ValueError(f"{name!r} is not a relative fixture member name")
    return name


def _require_digest(value: object, location: str) -> str:
    if type(value) is not str or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValueError(f"{location} must be 64 lowercase hexadecimal characters")
    return value
