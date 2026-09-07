"""Acceptance re-export of the one canonical cut-20 arm table."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_spec = spec_from_file_location("_cut20_canonical", Path(__file__).resolve().parents[1] / "n2_arms_cut20.py")
assert _spec is not None and _spec.loader is not None
_table = module_from_spec(_spec)
_spec.loader.exec_module(_table)
CUT20_ARMS = _table.CUT20_ARMS
DECLARATION_UNITS = _table.DECLARATION_UNITS
UNIT_CHECKS = _table.UNIT_CHECKS
unit_of = _table.unit_of
CO_CITED = _table.CO_CITED
