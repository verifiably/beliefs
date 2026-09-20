"""Cover the predicates that decide the admission-ramp survey's findings.

The survey itself is run by hand against roots outside this repository, so no
test here runs it against real data. What is covered is every predicate that
turns a corpus into a reported number — the class of code where the predecessor
survey shipped four defects, three found only in review, each of which changed a
figure.

Synthetic record, payload and scratch roots are built under `tmp_path`. Six cases
are required by the design (§4) rather than merely useful, because each is a
shape the real corpus may never produce, and an unexercised arm is an unmeasured
one:

1. no data package, with undeclared payload bytes present;
2. an unparseable data package;
3. a declared resource with bytes present and no recorded hash;
4. a preflight refusal and a retrieval failure over the same resource;
5. a declared local path that escapes its root;
6. a validated address that cannot be pinned — and *no request issued*.
"""

from __future__ import annotations

import importlib.util
import sys
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest
import yaml
from holdings_transport_fixtures import Scripted, scripted_seam

# `tools/` is not a package and deliberately is not on the import path — nothing
# in `src/` may depend on it. Load it by file instead, registering it in
# `sys.modules` first because `@dataclass` resolves annotations through there,
# and because the fail-closed test patches `survey_admission.socket`.
_SPEC = importlib.util.spec_from_file_location(
    "survey_admission", Path(__file__).parents[1] / "tools" / "survey_admission.py"
)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _MODULE
_SPEC.loader.exec_module(_MODULE)

BYTES_LOCAL = _MODULE.BYTES_LOCAL
BYTES_LOCATOR_UNTESTED = _MODULE.BYTES_LOCATOR_UNTESTED
BYTES_NO_LOCATOR = _MODULE.BYTES_NO_LOCATOR
BYTES_RETRIEVAL_FAILED = _MODULE.BYTES_RETRIEVAL_FAILED
BYTES_RETRIEVED = _MODULE.BYTES_RETRIEVED
CHECK_ABSENT = _MODULE.CHECK_ABSENT
CHECK_MATCH = _MODULE.CHECK_MATCH
CHECK_MISMATCH = _MODULE.CHECK_MISMATCH
CHECK_UNCHECKED = _MODULE.CHECK_UNCHECKED
PACKAGE_ABSENT = _MODULE.PACKAGE_ABSENT
PACKAGE_PRESENT = _MODULE.PACKAGE_PRESENT
PACKAGE_UNPARSEABLE = _MODULE.PACKAGE_UNPARSEABLE
NetworkProbe = _MODULE.NetworkProbe
PathRefusal = _MODULE.PathRefusal
ProbeOutcome = _MODULE.ProbeOutcome
byte_locator = _MODULE.byte_locator
render_report = _MODULE.render_report
resolve_declared_path = _MODULE.resolve_declared_path
survey = _MODULE.survey
to_artifact = _MODULE.to_artifact
validate_scratch = _MODULE.validate_scratch

SHA_OF_ABC = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
#: The same three bytes, correctly pinned under an algorithm this instrument does
#: not compute — so a *correct* record it must refuse rather than mis-report.
MD5_OF_ABC = "900150983cd24fb0d6963f7d28e17f72"


# ---------------------------------------------------------------------------
# Building a synthetic corpus
# ---------------------------------------------------------------------------


def write_record(
    records: Path,
    name: str,
    *,
    package: dict[str, Any] | str | None = None,
    frontmatter: dict[str, Any] | None = None,
) -> Path:
    directory = records / name
    directory.mkdir(parents=True)
    if frontmatter is not None:
        directory.joinpath("entity.md").write_text(f"---\n{yaml.safe_dump(frontmatter)}---\n\nbody\n")
    if isinstance(package, str):
        directory.joinpath("datapackage.yaml").write_text(package)
    elif package is not None:
        directory.joinpath("datapackage.yaml").write_text(yaml.safe_dump(package))
    return directory


def write_payload(payloads: Path, dataset: str, relative: str, content: bytes) -> Path:
    target = payloads / dataset / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    return target


@pytest.fixture
def roots(tmp_path: Path) -> tuple[Path, Path, Path]:
    records = tmp_path / "records"
    payloads = tmp_path / "payloads"
    scratch = tmp_path / "scratch"
    for path in (records, payloads, scratch):
        path.mkdir()
    return records, payloads, scratch


# ---------------------------------------------------------------------------
# The three axes
# ---------------------------------------------------------------------------


def test_local_bytes_matching_the_record_report_match_on_both_axes(roots: tuple[Path, Path, Path]) -> None:
    records, payloads, _ = roots
    write_record(
        records,
        "d",
        package={"resources": [{"path": "a.txt", "hash": f"sha256:{SHA_OF_ABC}", "bytes": 3}]},
    )
    write_payload(payloads, "d", "a.txt", b"abc")

    result = survey(records, payloads)

    [resource] = result.resources
    assert resource.byte_observation == BYTES_LOCAL
    assert resource.hash_result == CHECK_MATCH
    assert resource.byte_count_result == CHECK_MATCH


def test_the_two_integrity_axes_are_independent(roots: tuple[Path, Path, Path]) -> None:
    """A digest can disagree while the byte count agrees, and the row must say so."""
    records, payloads, _ = roots
    write_record(records, "d", package={"resources": [{"path": "a.txt", "hash": "sha256:" + "0" * 64, "bytes": 3}]})
    write_payload(payloads, "d", "a.txt", b"abc")

    [resource] = survey(records, payloads).resources

    assert resource.hash_result == CHECK_MISMATCH
    assert resource.byte_count_result == CHECK_MATCH


def test_a_byte_count_can_disagree_while_the_digest_agrees(roots: tuple[Path, Path, Path]) -> None:
    """The mirror of the case above, and the reason the count is its own axis.

    A recorded byte count that contradicts bytes whose digest matches is a defect
    in the record, not in the bytes — and folding the two axes together would
    report it as agreement.
    """
    records, payloads, _ = roots
    write_record(records, "d", package={"resources": [{"path": "a.txt", "hash": f"sha256:{SHA_OF_ABC}", "bytes": 99}]})
    write_payload(payloads, "d", "a.txt", b"abc")

    [resource] = survey(records, payloads).resources

    assert resource.hash_result == CHECK_MATCH
    assert resource.byte_count_result == CHECK_MISMATCH
    assert resource.observed_bytes == 3


def test_a_probe_reports_a_byte_count_mismatch_too(roots: tuple[Path, Path, Path]) -> None:
    records, payloads, _ = roots
    write_record(records, "d", package=_remote_package("https://a.example/x.bin"))
    probe = RecordingProbe({"https://a.example/x.bin": ProbeOutcome(BYTES_RETRIEVED, digest=SHA_OF_ABC, size=99)})

    [resource] = survey(records, payloads, probe).resources

    assert resource.hash_result == CHECK_MATCH
    assert resource.byte_count_result == CHECK_MISMATCH


def test_bytes_present_with_no_recorded_hash_is_absent_not_match(roots: tuple[Path, Path, Path]) -> None:
    """Required case 3. Obtained and unpinned is neither a match nor a mismatch:
    nothing in the record says which bytes are the right ones."""
    records, payloads, _ = roots
    write_record(records, "d", package={"resources": [{"path": "a.txt"}]})
    write_payload(payloads, "d", "a.txt", b"abc")

    [resource] = survey(records, payloads).resources

    assert resource.byte_observation == BYTES_LOCAL
    assert resource.hash_result == CHECK_ABSENT
    assert resource.byte_count_result == CHECK_ABSENT
    assert resource.observed_hash == f"sha256:{SHA_OF_ABC}"


# ---------------------------------------------------------------------------
# Digests keep their algorithm
# ---------------------------------------------------------------------------


def test_both_digests_are_recorded_algorithm_qualified(roots: tuple[Path, Path, Path]) -> None:
    """The artifact must yield §6.2's projection without an outside assertion.

    That projection folds `<algorithm>:<hex>` strings. An artifact holding bare
    hex cannot say which algorithm pinned the bytes — a 64-character digest is
    producible by more than one — so the address would depend on prose or on
    re-reading source roots that a frozen measurement is meant to replace.
    """
    records, payloads, _ = roots
    write_record(records, "d", package={"resources": [{"path": "a.txt", "hash": f"sha256:{SHA_OF_ABC}"}]})
    write_payload(payloads, "d", "a.txt", b"abc")

    [resource] = survey(records, payloads).resources

    assert resource.recorded_hash == f"sha256:{SHA_OF_ABC}"
    assert resource.observed_hash == f"sha256:{SHA_OF_ABC}"
    assert resource.hash_result == CHECK_MATCH


def test_a_digest_recorded_in_uppercase_hex_normalizes_and_still_matches(
    roots: tuple[Path, Path, Path],
) -> None:
    """Hex case is presentation. Two records pinning identical bytes in different
    case must fold to one basis, or the projection gives the same dataset two
    addresses."""
    records, payloads, _ = roots
    write_record(records, "d", package={"resources": [{"path": "a.txt", "hash": f"sha256:{SHA_OF_ABC.upper()}"}]})
    write_payload(payloads, "d", "a.txt", b"abc")

    [resource] = survey(records, payloads).resources

    assert resource.recorded_hash == f"sha256:{SHA_OF_ABC}"
    assert resource.hash_result == CHECK_MATCH


def test_a_digest_recorded_without_an_algorithm_is_refused(roots: tuple[Path, Path, Path]) -> None:
    """Bare hex names no algorithm, and the instrument has none to supply. Calling
    it sha256 is the assumption that cost the artifact this fact; calling it no
    digest would drop a declared pin and move the dataset off a content basis
    silently. Both are unreportable, so the run stops."""
    records, payloads, _ = roots
    write_record(records, "d", package={"resources": [{"path": "a.txt", "hash": SHA_OF_ABC}]})
    write_payload(payloads, "d", "a.txt", b"abc")

    with pytest.raises(ValueError, match="not <algorithm>:<hex>"):
        survey(records, payloads)


def test_a_digest_under_an_algorithm_this_instrument_cannot_compute_is_refused(
    roots: tuple[Path, Path, Path],
) -> None:
    """The md5 of `abc` is a correct pin, and this instrument still cannot check it.

    Parsing it and comparing it to a sha256 observation reports `mismatch` — which
    says the bytes disagree with the record, when nothing compared them. Which
    algorithms the *profile* accepts is open (§6.2); which one this tool observes
    is settled by its own code, and the two must not be conflated.
    """
    records, payloads, _ = roots
    write_record(records, "d", package={"resources": [{"path": "a.txt", "hash": f"md5:{MD5_OF_ABC}"}]})
    write_payload(payloads, "d", "a.txt", b"abc")

    with pytest.raises(ValueError, match="this instrument observes only sha256"):
        survey(records, payloads)


def test_a_digest_of_the_wrong_width_is_refused(roots: tuple[Path, Path, Path]) -> None:
    """`sha256:a` is not a sha256 digest, and the prefix does not make it one.
    Admitting it would put a dataset on a content basis identifying no bytes."""
    records, payloads, _ = roots
    write_record(records, "d", package={"resources": [{"path": "a.txt", "hash": "sha256:a"}]})
    write_payload(payloads, "d", "a.txt", b"abc")

    with pytest.raises(ValueError, match="1 hex digits, not the 64"):
        survey(records, payloads)


def test_a_hash_field_that_is_not_a_digest_is_refused(roots: tuple[Path, Path, Path]) -> None:
    """A YAML `hash: 12345` parses to an int and used to read as no digest at all."""
    records, payloads, _ = roots
    write_record(records, "d", package={"resources": [{"path": "a.txt", "hash": 12345}]})
    write_payload(payloads, "d", "a.txt", b"abc")

    with pytest.raises(ValueError, match="not <algorithm>:<hex>"):
        survey(records, payloads)


def test_a_retrieval_reporting_no_digest_is_refused(roots: tuple[Path, Path, Path]) -> None:
    """`retrieved` with the hash axis `unchecked` claims bytes in hand and says
    nothing about which bytes — the one combination this instrument exists to make
    unreportable."""
    records, payloads, _ = roots
    write_record(records, "d", package=_remote_package("https://a.example/x.bin"))
    probe = RecordingProbe({"https://a.example/x.bin": ProbeOutcome(BYTES_RETRIEVED, size=3)})

    with pytest.raises(ValueError, match="no digest or size"):
        survey(records, payloads, probe)


def test_a_resource_with_no_bytes_and_no_locator_is_reported_as_such(roots: tuple[Path, Path, Path]) -> None:
    records, payloads, _ = roots
    write_record(records, "d", package={"resources": [{"path": "gone.txt", "hash": "sha256:" + "0" * 64}]})

    [resource] = survey(records, payloads).resources

    assert resource.byte_observation == BYTES_NO_LOCATOR
    assert resource.hash_result == CHECK_UNCHECKED
    assert resource.byte_count_result == CHECK_UNCHECKED


def test_bytes_resolve_against_the_payload_root_as_well_as_the_record_root(
    roots: tuple[Path, Path, Path],
) -> None:
    """The split root is a property of the corpus and a place the instrument can
    silently under-count, so it is asserted rather than assumed."""
    records, payloads, _ = roots
    write_record(records, "d", package={"resources": [{"path": "nested/a.txt", "hash": f"sha256:{SHA_OF_ABC}"}]})
    write_payload(payloads, "d", "nested/a.txt", b"abc")

    [resource] = survey(records, payloads).resources

    assert resource.byte_observation == BYTES_LOCAL
    assert resource.hash_result == CHECK_MATCH


# ---------------------------------------------------------------------------
# The dataset collection — the denominator that must survive
# ---------------------------------------------------------------------------


def test_no_package_with_undeclared_payload_bytes(roots: tuple[Path, Path, Path]) -> None:
    """Required case 1, and the mirror image of a hash with no bytes.

    The record must still appear, and no basis may be derived from bytes it never
    declared.
    """
    records, payloads, _ = roots
    write_record(records, "d", frontmatter={"kind": "dataset", "origin": "external"})
    write_payload(payloads, "d", "stray.bin", b"abc")

    result = survey(records, payloads)

    [dataset] = result.datasets
    assert dataset.package_state == PACKAGE_ABSENT
    assert dataset.declared_resource_count == 0
    assert dataset.unmatched_payload_files == ["d/stray.bin"]
    assert result.resources == []
    # No basis is derived from the undeclared bytes: the evidence reports only
    # what the record states, and it states no digest.
    assert dataset.basis_evidence.declared_resources_with_digest == 0
    assert dataset.basis_evidence.authority_and_provenance == {"origin": "external"}


def test_an_unparseable_package_yields_a_dataset_row_and_a_failure(roots: tuple[Path, Path, Path]) -> None:
    """Required case 2. A silent skip would shrink the denominator without saying so."""
    records, payloads, _ = roots
    write_record(records, "d", package="resources: [oh: [dear\n")

    result = survey(records, payloads)

    [dataset] = result.datasets
    assert dataset.package_state == PACKAGE_UNPARSEABLE
    assert dataset.declared_resource_count == 0
    [failure] = result.failures
    assert failure.path == "d/datapackage.yaml"
    assert failure.reason


def test_a_resource_entry_without_a_path_is_a_failure_not_a_silent_drop(
    roots: tuple[Path, Path, Path],
) -> None:
    records, payloads, _ = roots
    write_record(records, "d", package={"resources": [{"name": "nameless"}]})

    result = survey(records, payloads)

    [dataset] = result.datasets
    assert dataset.package_state == PACKAGE_UNPARSEABLE
    assert result.resources == []
    assert "declares no path" in result.failures[0].reason


def test_declared_bytes_are_not_reported_as_unmatched(roots: tuple[Path, Path, Path]) -> None:
    """The unmatched list is the evidence for undeclared bytes; a declared
    resource appearing in it would manufacture the very finding it exists to make."""
    records, payloads, _ = roots
    write_record(records, "d", package={"resources": [{"path": "a.txt"}]})
    write_payload(payloads, "d", "a.txt", b"abc")
    write_payload(payloads, "d", "b.txt", b"abc")

    [dataset] = survey(records, payloads).datasets

    assert dataset.unmatched_payload_files == ["d/b.txt"]


def test_a_payload_copy_of_a_declared_resource_is_not_unmatched(
    roots: tuple[Path, Path, Path],
) -> None:
    """Claims are declared relative paths, not the file that won resolution.

    With copies under both roots the record-root copy resolves first; recording
    that absolute path as the claim left the payload copy looking undeclared.
    """
    records, payloads, _ = roots
    directory = write_record(records, "d", package={"resources": [{"path": "crosswalk.csv"}]})
    directory.joinpath("crosswalk.csv").write_bytes(b"abc")
    write_payload(payloads, "d", "crosswalk.csv", b"abc")

    [dataset] = survey(records, payloads).datasets

    assert dataset.unmatched_payload_files == []


def test_a_symlinked_payload_directory_is_refused_not_walked(roots: tuple[Path, Path, Path]) -> None:
    """The door, not just the children.

    Guarding only the entries *inside* the payload directory leaves the case
    where the dataset's directory is itself the link: every file behind it then
    enumerates as though it sat inside the payload root. Here `outside/secret.bin`
    is reachable that way, and must not appear.

    The declared side needs the same door guarded. `outside/a.txt` is the file a
    declared resource names, so resolving through the link reads bytes from
    outside the root and then cannot say where it read them — an observation the
    survey has no honest place to record.
    """
    records, payloads, _ = roots
    outside = payloads.parent / "outside"
    outside.mkdir()
    (outside / "secret.bin").write_bytes(b"abc")
    (outside / "a.txt").write_bytes(b"abc")
    write_record(records, "d", package={"resources": [{"path": "a.txt"}]})
    (payloads / "d").symlink_to(outside, target_is_directory=True)

    result = survey(records, payloads)

    [dataset] = result.datasets
    assert dataset.unmatched_payload_files == [], "a file outside the payload root was enumerated as inside it"
    assert not any("secret.bin" in name for name in dataset.unmatched_payload_files)
    # Refused, and said so: a silent skip reads as a dataset with no undeclared
    # bytes, which is a finding rather than a gap.
    [failure] = result.failures
    assert (failure.root, failure.path) == ("payloads", "d")
    assert "symlink" in failure.reason
    # The resource is a question not asked, not a hashed observation: bytes were
    # behind the link and none were read.
    [resource] = result.resources
    assert resource.byte_observation == BYTES_LOCATOR_UNTESTED
    assert resource.reason == "dataset directory is a symlink"
    assert resource.observed_hash is None
    assert resource.hash_result == CHECK_UNCHECKED


def test_a_symlinked_record_directory_is_not_walked_either(roots: tuple[Path, Path, Path]) -> None:
    records, payloads, _ = roots
    outside = records.parent / "outside-record"
    outside.mkdir()
    (outside / "entity.md").write_text("---\nkind: dataset\n---\n")
    (records / "linked").symlink_to(outside, target_is_directory=True)

    assert survey(records, payloads).datasets == []


def test_basis_evidence_records_what_the_record_states(roots: tuple[Path, Path, Path]) -> None:
    records, payloads, _ = roots
    write_record(
        records,
        "d",
        package={"resources": [{"path": "a.txt", "hash": "sha256:" + "0" * 64}, {"path": "b.txt"}]},
        frontmatter={
            "kind": "dataset",
            "origin": "external",
            "accessions": ["GEO: GSE1"],
            "access": {"level": "public", "source_url": "https://example.org/study"},
        },
    )

    [dataset] = survey(records, payloads).datasets

    # An accession and a source URL are authority-side, not content basis: they
    # name a work and a page, and neither pins bytes.
    assert dataset.basis_evidence.authority_and_provenance == {
        "origin": "external",
        "accessions": ["GEO: GSE1"],
        "access.source_url": "https://example.org/study",
    }
    assert dataset.basis_evidence.declared_resources_with_digest == 1


def test_an_unreadable_entity_still_yields_a_dataset_row(roots: tuple[Path, Path, Path]) -> None:
    records, payloads, _ = roots
    directory = write_record(records, "d", package={"resources": []})
    directory.joinpath("entity.md").write_text("no frontmatter here\n")

    result = survey(records, payloads)

    assert len(result.datasets) == 1
    assert result.datasets[0].basis_evidence.authority_and_provenance == {}
    assert result.failures[0].path == "d/entity.md"


# ---------------------------------------------------------------------------
# Local declared paths
# ---------------------------------------------------------------------------


def test_an_absolute_declared_path_is_refused(tmp_path: Path) -> None:
    refusal = resolve_declared_path(tmp_path, "d", "/etc/passwd")
    assert isinstance(refusal, PathRefusal)
    assert "absolute" in refusal.reason


def test_an_upward_traversing_declared_path_is_refused(tmp_path: Path) -> None:
    refusal = resolve_declared_path(tmp_path, "d", "../../etc/passwd")
    assert isinstance(refusal, PathRefusal)
    assert "traverses upward" in refusal.reason


def test_a_symlink_escaping_declared_path_is_refused(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_bytes(b"abc")
    dataset = tmp_path / "root" / "d"
    dataset.mkdir(parents=True)
    (dataset / "link").symlink_to(outside)

    refusal = resolve_declared_path(tmp_path / "root", "d", "link/secret.txt")

    assert isinstance(refusal, PathRefusal)
    assert "symlink" in refusal.reason


def test_a_symlinked_dataset_directory_is_refused_before_the_path_is_joined(tmp_path: Path) -> None:
    """Resolving the base directory hides the escape: every path under the link
    resolves *inside* the link's target, so the escape check passes."""
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "a.txt").write_bytes(b"abc")
    root = tmp_path / "root"
    root.mkdir()
    (root / "d").symlink_to(outside, target_is_directory=True)

    refusal = resolve_declared_path(root, "d", "a.txt")

    assert isinstance(refusal, PathRefusal)
    assert refusal.reason == "dataset directory is a symlink"


def test_an_escaping_path_is_untested_rather_than_read(roots: tuple[Path, Path, Path]) -> None:
    """Required case 5, at the survey level: refused before any read, and the
    refusal is a question not asked rather than a finding about the resource."""
    records, payloads, _ = roots
    outside = records.parent / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_bytes(b"abc")
    directory = write_record(records, "d", package={"resources": [{"path": "link/secret.txt"}]})
    (directory / "link").symlink_to(outside)

    [resource] = survey(records, payloads).resources

    assert resource.byte_observation == BYTES_LOCATOR_UNTESTED
    assert "symlink" in (resource.reason or "")
    assert resource.observed_hash is None


# ---------------------------------------------------------------------------
# Probing: retrieval failure, and the adapter over the kernel transport
# ---------------------------------------------------------------------------


class RecordingProbe:
    """A probe that records every URL it was asked to fetch."""

    def __init__(self, outcomes: dict[str, ProbeOutcome]) -> None:
        self.outcomes = outcomes
        self.asked: list[str] = []

    def fetch(self, url: str) -> ProbeOutcome:
        self.asked.append(url)
        return self.outcomes[url]


def _remote_package(url: str) -> dict[str, Any]:
    return {
        "resources": [
            {"path": "a.bin", "hash": f"sha256:{SHA_OF_ABC}", "bytes": 3, "source": {"type": "remote", "ref": url}}
        ]
    }


def test_a_preflight_refusal_and_a_retrieval_failure_are_never_collapsed(
    roots: tuple[Path, Path, Path],
) -> None:
    """Required case 4. The same resource shape yields two different axis values,
    because one was never attempted and the other was."""
    records, payloads, _ = roots
    write_record(records, "refused", package=_remote_package("https://a.example/x.bin"))
    write_record(records, "failed", package=_remote_package("https://b.example/x.bin"))
    probe = RecordingProbe(
        {
            "https://a.example/x.bin": ProbeOutcome(BYTES_LOCATOR_UNTESTED, reason="scheme ftp is not approved"),
            "https://b.example/x.bin": ProbeOutcome(BYTES_RETRIEVAL_FAILED, reason="status 503"),
        }
    )

    by_dataset = {r.dataset: r for r in survey(records, payloads, probe).resources}

    assert by_dataset["refused"].byte_observation == BYTES_LOCATOR_UNTESTED
    assert by_dataset["failed"].byte_observation == BYTES_RETRIEVAL_FAILED
    for resource in by_dataset.values():
        assert resource.reason
        assert resource.probed_at
        assert resource.hash_result == CHECK_UNCHECKED


def test_a_successful_probe_is_compared_and_stamped(roots: tuple[Path, Path, Path]) -> None:
    records, payloads, _ = roots
    write_record(records, "d", package=_remote_package("https://a.example/x.bin"))
    probe = RecordingProbe({"https://a.example/x.bin": ProbeOutcome(BYTES_RETRIEVED, digest=SHA_OF_ABC, size=3)})

    [resource] = survey(records, payloads, probe).resources

    assert resource.byte_observation == BYTES_RETRIEVED
    assert resource.hash_result == CHECK_MATCH
    assert resource.byte_count_result == CHECK_MATCH
    assert resource.probed_at


def test_a_retrieved_mismatch_is_not_a_retrieval_failure(roots: tuple[Path, Path, Path]) -> None:
    """A retrieval that succeeds and disagrees with the record is the most
    informative result the run can produce, and must not read as a failure to look."""
    records, payloads, _ = roots
    write_record(records, "d", package=_remote_package("https://a.example/x.bin"))
    probe = RecordingProbe({"https://a.example/x.bin": ProbeOutcome(BYTES_RETRIEVED, digest="0" * 64, size=3)})

    [resource] = survey(records, payloads, probe).resources

    assert resource.byte_observation == BYTES_RETRIEVED
    assert resource.hash_result == CHECK_MISMATCH


def test_without_a_probe_a_remote_locator_is_untested_and_never_fetched(
    roots: tuple[Path, Path, Path],
) -> None:
    records, payloads, _ = roots
    write_record(records, "d", package=_remote_package("https://a.example/x.bin"))

    [resource] = survey(records, payloads, None).resources

    assert resource.byte_observation == BYTES_LOCATOR_UNTESTED
    assert resource.reason == "no probe was run"


def test_a_local_source_ref_is_not_a_byte_locator() -> None:
    """`{type: local, ref: ...}` is acquisition provenance for the build, not a
    way to retrieve the published resource."""
    assert byte_locator({"source": {"type": "local", "ref": "/build/out/a.bin"}}, "a.bin") is None
    assert byte_locator({"source": {"type": "remote", "ref": "not-a-url"}}, "a.bin") is None
    assert byte_locator({"source": {"type": "remote", "ref": "https://a.example/x"}}, "a.bin") == "https://a.example/x"


def test_a_url_valued_declared_path_is_the_resource_s_byte_locator() -> None:
    """The defect this guards cost every remote resource in the predecessor's
    store its locator: they are declared by URL in `path`, not in `source`."""
    url = "https://ftp.example.org/series/GSE1_matrix.txt.gz"
    assert byte_locator({}, url) == url
    # And it wins over a source that says nothing useful.
    assert byte_locator({"source": {"type": "local", "ref": "/build/x"}}, url) == url


def test_the_probe_maps_the_kernel_result_to_the_instrument_vocabulary(tmp_path: Path) -> None:
    seam, log = scripted_seam({"/data": Scripted(200, {"Content-Length": "7"}, (b"payload",))})
    probe = NetworkProbe(tmp_path / "scratch", resolver=seam.resolve, connect=seam.connect)
    outcome = probe.fetch("https://example.org/data")
    assert outcome == ProbeOutcome(BYTES_RETRIEVED, digest=sha256(b"payload").hexdigest(), size=7)
    assert list((tmp_path / "scratch").iterdir()) == []  # the probe deletes the kernel's scratch file
    assert len(log.requests) == 1
    failing, _ = scripted_seam({"/data": Scripted(500, {}, (b"",))})
    assert NetworkProbe(tmp_path / "scratch", resolver=failing.resolve, connect=failing.connect).fetch("https://example.org/data") == ProbeOutcome(BYTES_RETRIEVAL_FAILED, reason="status 500")
    untested, _ = scripted_seam({}, unpinnable=True)
    assert NetworkProbe(tmp_path / "scratch", resolver=untested.resolve, connect=untested.connect).fetch("https://example.org/data") == ProbeOutcome(BYTES_LOCATOR_UNTESTED, reason="unpinnable")
    assert NetworkProbe(tmp_path / "scratch", resolver=seam.resolve, connect=seam.connect).fetch("https://user@example.org/data") == ProbeOutcome(BYTES_LOCATOR_UNTESTED, reason="malformed url")


def test_a_refused_redirect_hop_is_retrieval_failed_by_ordinal_and_category(tmp_path: Path) -> None:
    seam, _ = scripted_seam({"/data": Scripted(302, {"Location": "https://tok3n-9f2a.example.net/data?X-Amz-Signature=abc"})})
    resolver = lambda host, _port: ["10.1.1.1"] if host != "example.org" else seam.resolve(host, 0)
    outcome = NetworkProbe(tmp_path / "scratch", resolver=resolver, connect=seam.connect).fetch("https://example.org/data")
    assert outcome == ProbeOutcome(BYTES_RETRIEVAL_FAILED, reason="redirect hop 1 refused: non-public-address")


# ---------------------------------------------------------------------------
# Scratch safety, root identity, and the artifact
# ---------------------------------------------------------------------------


def test_a_scratch_root_inside_a_corpus_root_is_refused(tmp_path: Path) -> None:
    records = tmp_path / "records"
    payloads = tmp_path / "payloads"
    for path in (records, payloads):
        path.mkdir()

    for scratch in (records, records / "nested", payloads / "deep" / "nested"):
        with pytest.raises(SystemExit):
            validate_scratch(scratch, records, payloads)

    validate_scratch(tmp_path / "elsewhere", records, payloads)


def test_root_identity_moves_with_observed_content_and_not_with_location(
    tmp_path: Path,
) -> None:
    def build(where: Path, content: bytes) -> tuple[str, str]:
        records, payloads = where / "records", where / "payloads"
        for path in (records, payloads):
            path.mkdir(parents=True)
        write_record(records, "d", package={"resources": [{"path": "a.txt"}]})
        write_payload(payloads, "d", "a.txt", content)
        result = survey(records, payloads)
        return result.record_root_identity, result.payload_root_identity

    here = build(tmp_path / "here", b"abc")
    same_elsewhere = build(tmp_path / "there", b"abc")
    changed = build(tmp_path / "changed", b"different")

    assert here == same_elsewhere, "identity must not depend on where the roots sit"
    assert here[1] != changed[1], "identity must move when observed payload content moves"


def test_the_artifact_holds_every_unit_level_observation(roots: tuple[Path, Path, Path]) -> None:
    records, payloads, _ = roots
    write_record(records, "declared", package={"resources": [{"path": "a.txt"}]})
    write_payload(payloads, "declared", "a.txt", b"abc")
    write_record(records, "silent", frontmatter={"kind": "dataset"})
    write_payload(payloads, "silent", "stray.bin", b"abc")
    write_record(records, "broken", package="resources: [oh: [dear\n")

    artifact = to_artifact(survey(records, payloads))

    assert [d["dataset"] for d in artifact["datasets"]] == ["broken", "declared", "silent"]
    assert len(artifact["resources"]) == 1
    assert len(artifact["failures"]) == 1
    assert artifact["record_root_identity"].startswith("sha256:")
    assert artifact["probed"] is False


def test_the_report_renders_from_the_artifact(roots: tuple[Path, Path, Path]) -> None:
    """Rendering from the artifact is what keeps prose and data from drifting, so
    the report must reflect an artifact it is handed rather than a survey it re-runs."""
    records, payloads, _ = roots
    write_record(records, "d", package={"resources": [{"path": "a.txt", "hash": "sha256:" + "0" * 64}]})
    write_payload(payloads, "d", "a.txt", b"abc")

    artifact = to_artifact(survey(records, payloads))
    report = render_report(artifact)

    assert "Mismatches: 1" in report
    assert "d/a.txt" in report

    artifact["resources"] = []
    artifact["datasets"] = []
    assert "Mismatches: 0" in render_report(artifact)


