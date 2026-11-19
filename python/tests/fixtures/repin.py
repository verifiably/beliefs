"""Same-base domain chains and an explicitly recovery-capable portable executor."""

from copy import deepcopy

from nodes.core.write_plan import DefaultExecutor

from beliefs.contract.domain import parse_domain_contract
from beliefs.profile import compile_profile, shipped_base_contract
from beliefs.register import AssumptionsRegister, RegisterEntry, register_entry_keys, register_identity


def repin_chain(document=None, count=3):
    base = shipped_base_contract()
    current = (
        deepcopy(document)
        if document is not None
        else {
            "contract": "repin",
            "version": 1,
            "lineage": "genesis",
            "sorts": {
                "entity": {
                    "binding": {"kind": "scheme", "scheme": "EX", "version": "1"},
                    "identifier_class": {"prefix": "EX", "pattern": "EX:[a-z]+"},
                }
            },
            "dimensions": {},
            "templates": {
                "relates": {
                    "roles": {"subject": {"arity": "one"}},
                    "sign_apt": False,
                    "layers": ["structural"],
                    "forms": ["polar"],
                }
            },
            "instantiations": {"entity": {"template": "relates", "roles": {"subject": ["entity"]}}},
            "facets": {
                "label": {"attaches_to": ["proposition"], "fields": {"value": {"type": "string", "required": True}}}
            },
        }
    )
    documents, contracts, profiles, registers = [], [], [], []
    for version in range(1, count + 1):
        current = deepcopy(current)
        current["version"] = version
        current["lineage"] = "genesis" if not contracts else {"successor": contracts[-1].content_identity}
        if version > 1:
            current.setdefault("sorts", {})[f"added-{version}"] = deepcopy(
                current["sorts"][next(iter(current["sorts"]))]
            )
            if "entity" in current.get("instantiations", {}):
                current["instantiations"][f"added-{version}"] = {
                    "template": "relates",
                    "roles": {"subject": [f"added-{version}"]},
                }
        contract = parse_domain_contract(
            current, source="repin fixture", base=base, predecessor=contracts[-1] if contracts else None
        )
        register = AssumptionsRegister(
            describes=f"{contract.namespace}:{contract.content_identity}",
            previous=register_identity(registers[-1]) if registers else None,
            entries={key: RegisterEntry("c", "l", "n", status="provisional") for key in register_entry_keys(contract)},
        )
        documents.append(current)
        contracts.append(contract)
        profiles.append(compile_profile(base, [contract]))
        registers.append(register)
    return documents, contracts, profiles, registers


class PortableFactory:
    """No pending transaction is possible; tests may replace the recovery callback."""

    def __init__(self):
        self.plans = []
        self.recoveries = []
        self.recovery = None

    def recover(self, root):
        self.recoveries.append(root)
        if self.recovery is not None:
            self.recovery(root)

    def __call__(self, root):
        factory = self
        inner = DefaultExecutor(root)

        class Executor:
            def execute(self, plan):
                factory.plans.append(list(plan))
                inner.execute(plan)

        return Executor()
