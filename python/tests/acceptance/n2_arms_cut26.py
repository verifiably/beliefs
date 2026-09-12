"""Acceptance re-export of the one canonical cut-26 arm table."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_spec = spec_from_file_location("_cut26_canonical", Path(__file__).resolve().parents[1] / "n2_arms_cut26.py")
assert _spec is not None and _spec.loader is not None
_table = module_from_spec(_spec)
_spec.loader.exec_module(_table)
CUT26_ARMS = _table.CUT26_ARMS
DECLARATION_UNITS = _table.DECLARATION_UNITS
UNIT_CHECKS = _table.UNIT_CHECKS
CO_CITED = _table.CO_CITED
NODES_SOURCE_COMMIT = _table.NODES_SOURCE_COMMIT
unit_of = _table.unit_of
