"""A run session's kernel staging: pinned anchors and the bind check, over plain directories."""

from __future__ import annotations

import os
import shutil
import stat
from dataclasses import replace
from pathlib import Path

import pytest

from beliefs.adapter import SANDBOX_ENV
from beliefs.confinement import DEVICES, MountPlan, mount_plan
from beliefs.errors import ConfinementNotEstablished
from beliefs.session.staging import RunStaging

SESSION_A = "a" * 32
SESSION_B = "b" * 32
LOADER = "/usr/lib/ld-linux-x86-64.so.2"


def _staging(tmp_path: Path, session: str = SESSION_A) -> RunStaging:
    ops = tmp_path / "ops"
    ops.mkdir(exist_ok=True)
    return RunStaging(ops, session)


def _laid_out(staging: RunStaging, invocation: str = "i1") -> MountPlan:
    """A mount plan over a real tree: the snapshot in the cache, the bundle and the
    output root in one execution's scratch beneath the invocation's staging."""
    scratch = staging.invocation_dir(invocation) / "run-1"
    snapshot = staging.cache_dir() / "env-1"
    for directory in (scratch / "bundle", scratch / "out" / "inputs", snapshot / SANDBOX_ENV.lstrip("/")):
        directory.mkdir(parents=True)
    loader = snapshot / LOADER.lstrip("/")
    loader.parent.mkdir(parents=True)
    loader.write_bytes(b"\x7fELF")
    return mount_plan(snapshot=snapshot, loader=LOADER, bundle=scratch / "bundle", output_root=scratch / "out")


def _with_source(plan: MountPlan, role: str, source: str) -> MountPlan:
    binds = tuple(
        (sandbox, source if planned == role else host, access)
        for (sandbox, host, access), planned in zip(plan.binds, plan.roles)
    )
    return replace(plan, binds=binds)


def _swap_for_symlink(anchor: Path, outside: Path) -> None:
    """The reviewer's reproduction: the anchor moves outside and a symlink takes its
    place, so the anchor and every source beneath it resolve outside together."""
    anchor.rename(outside)
    anchor.symlink_to(outside, target_is_directory=True)


# --- establishment ------------------------------------------------------------------
def test_two_sessions_on_one_operations_root_stage_the_same_invocation_apart(tmp_path):
    first, second = _staging(tmp_path, SESSION_A), _staging(tmp_path, SESSION_B)
    try:
        ops = tmp_path / "ops"
        a, b = first.invocation_dir("i1"), second.invocation_dir("i1")
        assert a == ops / "scratch" / SESSION_A / "i1"
        assert b == ops / "scratch" / SESSION_B / "i1"
        assert a != b and a.is_dir() and b.is_dir()
        assert first.cache_dir() == second.cache_dir() == ops / "scratch" / "environments"
        for directory in (a, a.parent, b.parent, first.cache_dir()):
            assert stat.S_IMODE(directory.lstat().st_mode) == 0o700
    finally:
        first.close()
        second.close()


def test_an_invocation_directory_is_reused_by_its_later_executions(tmp_path):
    staging = _staging(tmp_path)
    try:
        assert staging.invocation_dir("i1") == staging.invocation_dir("i1")
    finally:
        staging.close()


def test_an_invocation_directory_that_already_exists_is_refused(tmp_path):
    staging = _staging(tmp_path)
    try:
        staging.invocation_dir("i0")
        (tmp_path / "ops" / "scratch" / SESSION_A / "i1").mkdir()
        with pytest.raises(ConfinementNotEstablished, match="i1 already exists"):
            staging.invocation_dir("i1")
    finally:
        staging.close()


def test_a_session_directory_that_already_exists_is_refused(tmp_path):
    staging = _staging(tmp_path)
    try:
        (tmp_path / "ops" / "scratch" / SESSION_A).mkdir(parents=True)
        with pytest.raises(ConfinementNotEstablished, match=f"{SESSION_A} already exists"):
            staging.invocation_dir("i1")
    finally:
        staging.close()


def test_a_symlinked_operations_root_is_refused_at_the_pin(tmp_path):
    real = tmp_path / "real-ops"
    real.mkdir()
    (tmp_path / "ops").symlink_to(real, target_is_directory=True)
    with pytest.raises(OSError):
        RunStaging(tmp_path / "ops", SESSION_A)


def test_a_symlinked_scratch_directory_is_refused_at_creation(tmp_path):
    staging = _staging(tmp_path)
    try:
        elsewhere = tmp_path / "elsewhere"
        elsewhere.mkdir()
        (tmp_path / "ops" / "scratch").symlink_to(elsewhere, target_is_directory=True)
        with pytest.raises(ConfinementNotEstablished):
            staging.invocation_dir("i1")
        with pytest.raises(ConfinementNotEstablished):
            staging.cache_dir()
        assert list(elsewhere.iterdir()) == []
    finally:
        staging.close()


# --- the bind check -----------------------------------------------------------------
def test_binds_beneath_the_invocation_staging_and_the_cache_pass(tmp_path):
    staging = _staging(tmp_path)
    try:
        plan = _laid_out(staging)
        staging.check_binds(plan, "i1")
        assert {host for _, host, access in plan.binds if access == "dev"} == set(DEVICES)
    finally:
        staging.close()


def _anchor(tmp_path: Path, which: str) -> Path:
    scratch = tmp_path / "ops" / "scratch"
    return {
        "operations root": tmp_path / "ops",
        "scratch": scratch,
        "session": scratch / SESSION_A,
        "invocation": scratch / SESSION_A / "i1",
        "cache": scratch / "environments",
    }[which]


@pytest.mark.parametrize("which", ["operations root", "scratch", "session", "invocation", "cache"])
def test_an_anchor_replaced_by_a_symlink_to_an_outside_copy_refuses(tmp_path, which):
    staging = _staging(tmp_path)
    try:
        plan = _laid_out(staging)
        _swap_for_symlink(_anchor(tmp_path, which), tmp_path / "outside")
        with pytest.raises(ConfinementNotEstablished, match="symlink|pinned"):
            staging.check_binds(plan, "i1")
    finally:
        staging.close()


@pytest.mark.parametrize("which", ["invocation", "cache"])
def test_an_anchor_replaced_by_another_directory_refuses(tmp_path, which):
    staging = _staging(tmp_path)
    try:
        plan = _laid_out(staging)
        anchor = _anchor(tmp_path, which)
        anchor.rename(tmp_path / "moved")
        shutil.copytree(tmp_path / "moved", anchor, symlinks=True)
        with pytest.raises(ConfinementNotEstablished, match="pinned"):
            staging.check_binds(plan, "i1")
    finally:
        staging.close()


def test_a_symlink_component_inside_the_staging_tree_refuses(tmp_path):
    staging = _staging(tmp_path)
    try:
        plan = _laid_out(staging)
        invocation = staging.invocation_dir("i1")
        (invocation / "run-1").rename(invocation / "run-real")
        (invocation / "run-1").symlink_to("run-real", target_is_directory=True)
        with pytest.raises(ConfinementNotEstablished, match="symlink"):
            staging.check_binds(plan, "i1")
    finally:
        staging.close()


def test_a_final_symlink_source_refuses(tmp_path):
    staging = _staging(tmp_path)
    try:
        plan = _laid_out(staging)
        bundle = staging.invocation_dir("i1") / "run-1" / "bundle"
        bundle.rename(bundle.with_name("bundle-real"))
        bundle.symlink_to("bundle-real", target_is_directory=True)
        with pytest.raises(ConfinementNotEstablished, match="symlink"):
            staging.check_binds(plan, "i1")
    finally:
        staging.close()


def test_a_source_outside_both_anchors_refuses(tmp_path):
    staging = _staging(tmp_path)
    try:
        plan = _laid_out(staging)
        outside = tmp_path / "outside" / "bundle"
        outside.mkdir(parents=True)
        with pytest.raises(ConfinementNotEstablished, match="beneath"):
            staging.check_binds(_with_source(plan, "bundle", str(outside)), "i1")
    finally:
        staging.close()


def test_another_invocations_staging_is_outside_this_invocations_anchor(tmp_path):
    staging = _staging(tmp_path)
    try:
        plan = _laid_out(staging, "i1")
        staging.invocation_dir("i2")
        with pytest.raises(ConfinementNotEstablished, match="beneath"):
            staging.check_binds(plan, "i2")
    finally:
        staging.close()


@pytest.mark.parametrize("component", ["..", ".", ""])
def test_a_source_with_a_dot_dot_dot_or_empty_component_refuses(tmp_path, component):
    staging = _staging(tmp_path)
    try:
        plan = _laid_out(staging)
        invocation = str(staging.invocation_dir("i1"))
        source = {
            "..": f"{invocation}/run-1/../run-1/bundle",
            ".": f"{invocation}/run-1/./bundle",
            "": f"{invocation}/run-1//bundle",
        }[component]
        with pytest.raises(ConfinementNotEstablished, match="component"):
            staging.check_binds(_with_source(plan, "bundle", source), "i1")
    finally:
        staging.close()


def test_the_anchor_itself_is_not_a_bind_source(tmp_path):
    staging = _staging(tmp_path)
    try:
        plan = _laid_out(staging)
        with pytest.raises(ConfinementNotEstablished, match="component"):
            staging.check_binds(_with_source(plan, "bundle", str(staging.invocation_dir("i1"))), "i1")
    finally:
        staging.close()


def test_a_device_bind_naming_another_source_refuses(tmp_path):
    staging = _staging(tmp_path)
    try:
        plan = _laid_out(staging)
        with pytest.raises(ConfinementNotEstablished, match="beneath"):
            staging.check_binds(_with_source(plan, "device", "/etc/passwd"), "i1")
    finally:
        staging.close()


def test_an_invocation_never_staged_refuses(tmp_path):
    staging = _staging(tmp_path)
    try:
        plan = _laid_out(staging, "i1")
        with pytest.raises(ConfinementNotEstablished, match="i9"):
            staging.check_binds(plan, "i9")
    finally:
        staging.close()


def test_close_releases_every_descriptor_and_is_idempotent(tmp_path):
    before = len(os.listdir("/proc/self/fd"))
    staging = _staging(tmp_path)
    _laid_out(staging)
    staging.invocation_dir("i2")
    assert len(os.listdir("/proc/self/fd")) > before
    staging.close()
    staging.close()
    assert len(os.listdir("/proc/self/fd")) == before
    with pytest.raises(ConfinementNotEstablished, match="closed"):
        staging.invocation_dir("i3")
