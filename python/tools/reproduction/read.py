"""Step 12: read the composite, in a fresh process, twice (composite-claims design §6, §9; U8, U10)."""

from __future__ import annotations

import json
import sys

from beliefs.belief import NotReached
from beliefs.composite import read_composite
from beliefs.identity import v1
from reproduction import belief, findings, paths, state, vocabulary, world


def main(argv: list[str]) -> int:
    st = state.load()
    again = "--again" in argv
    view = world.open_writer().read_view
    reading = read_composite(
        view,
        st["composite_ref"],
        context=belief.context(view),
        availability=belief.availability(view),
        resolution=vocabulary.snapshot(),
        binding=belief.BINDING,
        profile=vocabulary.profile(),
    )
    encoded = v1.encode(reading.projection())
    out = paths.WORK / ("reading-2.json" if again else "reading-1.json")
    out.write_bytes(encoded)
    rows = {
        row.ref: (
            row.role.sign,
            row.belief.__class__.__name__,
            "not-reached" if isinstance(row.identification, NotReached) else list(row.identification),
        )
        for row in reading.rows
    }
    if again:
        equal = (paths.WORK / "reading-1.json").read_bytes() == encoded
        state.save(reading_equal=equal, reading_rows=rows)
        findings.record(12, "closed" if equal else "defect", f"second-process reading {'equal' if equal else 'DIFFERS'}; rows {rows}")
    else:
        state.save(reading_rows=rows)
    print(json.dumps({"standing": reading.standing.projection(), "nodes": dict(reading.projection()["node_outcomes"]), "rows": rows}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
