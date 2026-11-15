"""Load the admitted SI Brochure vocabulary for shared time-role tests."""

from pathlib import Path
from typing import Any, cast

from beliefs.contract.document import load_document
from beliefs.contract.domain import parse_domain_contract

TIME_FIXTURE = Path(__file__).resolve().parents[2] / "domains" / "si-brochure" / "DOMAIN.yaml"


def time_document():
    return cast(dict[str, Any], load_document(TIME_FIXTURE, source=str(TIME_FIXTURE)))


def time_contract(base):
    return parse_domain_contract(time_document(), source=str(TIME_FIXTURE), base=base, predecessor=None)
