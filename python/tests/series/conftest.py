"""Real parsed synthetic time vocabulary for finite reader tests."""

import pytest

from beliefs.contract.domain import parse_domain_contract
from beliefs.profile import compile_profile


@pytest.fixture
def series_profile(base_contract, testing_document):
    from .fixtures import time_document

    return compile_profile(
        base_contract,
        [
            parse_domain_contract(testing_document, source="<series testing>", base=base_contract, predecessor=None),
            parse_domain_contract(
                time_document(), source="<synthetic time, not admission>", base=base_contract, predecessor=None
            ),
        ],
    )


@pytest.fixture
def time_roles():
    from beliefs.contract.base import TimeRoles

    return TimeRoles(
        "urn:beliefs:source:bipm-si-brochure",
        "si-brochure/duration",
        "si-brochure/frequency",
        "si-brochure/second",
        "si-brochure/hertz",
    )


@pytest.fixture
def author_profile(base_contract, testing_document):
    from time_roles_fixture import time_contract

    row = testing_document["functionals"]["difference-of-means"]
    testing_document["functionals"]["series-contrast"] = {**row, "response_axis": "regular-elapsed"}
    return compile_profile(
        base_contract,
        [
            parse_domain_contract(testing_document, source="<series authoring>", base=base_contract, predecessor=None),
            time_contract(base_contract),
        ],
    )
