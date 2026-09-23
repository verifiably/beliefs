"""Acceptance re-export of the one canonical cut-39 arm table."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_spec = spec_from_file_location("_cut39_canonical", Path(__file__).resolve().parents[1] / "n2_arms_cut39.py")
assert _spec is not None and _spec.loader is not None
_table = module_from_spec(_spec)
_spec.loader.exec_module(_table)
CUT39_ARMS = _table.CUT39_ARMS
DECLARATION_UNITS = _table.DECLARATION_UNITS
UNIT_CHECKS = _table.UNIT_CHECKS
unit_of = _table.unit_of
CO_CITED = _table.CO_CITED
REPLACE_UNREGISTERED = _table.REPLACE_UNREGISTERED
ROLLBACK_MEANS = _table.ROLLBACK_MEANS
