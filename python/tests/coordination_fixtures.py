from copy import deepcopy

from beliefs.contract.coordination import parse_coordination_contract

COORDINATION_DOCUMENT = {
    "contract": "coordination",
    "version": 1,
    "lineage": "genesis",
    "description": "Project coordination records",
    "address_root": "project",
    "query_vocabulary": {
        "kinds": [
            "proposition",
            "source-assertion",
            "assessment",
            "analysis-spec",
            "run",
            "verification",
            "dataset",
            "source",
            "holdings-observation",
            "retraction",
            "instrument-certification",
            "coreference-attestation",
            "act-report",
        ],
        "relations": [
            "assesses",
            "observes",
            "reads",
            "transforms",
            "produces",
            "produced_by",
            "executes",
            "targets",
            "verifies",
            "member_of",
            "grounded-in",
        ],
    },
    "kinds": {
        **{
            kind: {
                "fields": ["name", "body", "author", "at", "query"],
                "query_versions": ["science.view-query.v1"],
            }
            for kind in ("project", "question", "hypothesis", "topic", "theme")
        },
        "task": {
            "fields": ["name", "body", "author", "at", "status", "depends"],
            "query_versions": [],
        },
        "decision": {
            "fields": ["name", "body", "author", "at"],
            "query_versions": [],
        },
        "note": {
            "fields": ["name", "body", "author", "at", "about"],
            "query_versions": [],
        },
    },
}


def coordination_contract(document=None, predecessor=None):
    return parse_coordination_contract(
        deepcopy(COORDINATION_DOCUMENT if document is None else document),
        source="<coordination-test>",
        predecessor=predecessor,
    )
