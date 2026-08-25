# ruff: noqa: F821 -- qualification globals are supplied by source concatenation
# pyright: reportUndefinedVariable=false
"""Reduce captured holdings evidence to active and blocked projections."""


def _observation(row):
    document = json.loads(row["canonical"])
    if document.get("kind") != "holdings-observation":
        return None
    facet = document["facets"]["holdings-observation"]
    if facet["kind"] != "holdings-observation":
        return None
    ref = document["id"].split(":", 1)[1]
    location = facet["location"]
    return {
        "ref": ref,
        "path": "holdings-observation/" + ref.replace(":", "__") + ".md",
        "location": location["type"] + ":" + location["store_id"] + ":" + location["relative_path"],
        "outcome": dict(facet["outcome"]),
        "expected": facet.get("expected"),
        "event_token": facet["event_token"],
        "supersedes": tuple(facet["supersedes"]),
    }


def _member(head, observations):
    reached = set()
    pending = list(head["supersedes"])
    while pending:
        ref = pending.pop()
        predecessor = observations.get(ref)
        if predecessor is None or ref in reached:
            continue
        reached.add(ref)
        pending.extend(predecessor["supersedes"])
    history = []
    for ref in sorted(reached):
        predecessor = observations[ref]
        row = {"ref": ref, "outcome": dict(predecessor["outcome"])}
        if predecessor["expected"] is not None:
            row["expected"] = predecessor["expected"]
        history.append(row)
    value = {
        "head": head["ref"],
        "location": head["location"],
        "outcome": dict(head["outcome"]),
        "history": history,
    }
    if head["expected"] is not None:
        value["expected"] = head["expected"]
    return value


def _visit(ref, location, observations, visiting, visited):
    if ref in visiting:
        raise ValueError("supersession cycle at " + location)
    if ref in visited:
        return
    visiting.add(ref)
    for predecessor in observations[ref]["supersedes"]:
        if predecessor in observations:
            if observations[predecessor]["location"] != location:
                raise ValueError("supersession crosses locations at " + location)
            _visit(predecessor, location, observations, visiting, visited)
    visiting.discard(ref)
    visited.add(ref)


def _check_walks(by_location, observations):
    for location, members in by_location.items():
        visiting = set()
        visited = set()
        for member in members:
            _visit(member["ref"], location, observations, visiting, visited)


def _head_reasons(heads):
    reasons = set()
    findings = {head["outcome"]["finding"] for head in heads}
    if len(findings) > 1:
        reasons.add("contested")
    found = [head["outcome"]["digest"] for head in heads if head["outcome"]["finding"] == "found"]
    by_algorithm = {}
    for digest in found:
        by_algorithm.setdefault(digest.split(":", 1)[0], set()).add(digest)
    if len(by_algorithm) > 1:
        reasons.add("incommensurable")
    if any(len(digests) > 1 for digests in by_algorithm.values()):
        reasons.add("contested")
    return reasons


def _unsettled(corpus, observations_by_path):
    chain = corpus["chain"]
    settlements = {
        row["entry"]["registration"]: row["entry"]["outcome"]
        for row in chain
        if row["entry"]["kind"] == "settled"
    }
    intents = []
    for index, row in enumerate(chain):
        if row["entry"]["kind"] != "intent":
            continue
        value = decode_holdings_intent(row)
        if value is not None:
            value["index"] = index
            intents.append(value)
    registrations = {}
    for row in chain:
        entry = row["entry"]
        if entry["kind"] == "registered" and "fulfills" in entry:
            registrations.setdefault(entry["fulfills"], []).append({
                "settlement": settlements.get(row["digest"]),
                "final": entry["final"],
            })
    statuses = {
        value["digest"]: qualify_intent(value, registrations.get(value["digest"], ()), observations_by_path)
        for value in intents
    }
    blocked = set()
    for value in intents:
        if value["kind"] not in MUTATING_KINDS or statuses[value["digest"]] == "matched":
            continue
        repaired = any(
            later["index"] > value["index"]
            and later["kind"] == "re-check"
            and later["location"] == value["location"]
            and statuses[later["digest"]] == "matched"
            for later in intents
        )
        if not repaired:
            blocked.add(value["location"])
    return blocked


def reduce_holdings(capture):
    observations = {}
    by_location = {}
    paths_by_corpus = []
    for corpus in capture["corpora"]:
        observations_by_path = {}
        for row in corpus["records"]:
            value = _observation(row)
            if value is None:
                continue
            previous = observations.get(value["ref"])
            if previous is not None and previous != value:
                raise ValueError("holdings observation reference collision at " + value["ref"])
            if previous is None:
                observations[value["ref"]] = value
                by_location.setdefault(value["location"], []).append(value)
            observations_by_path[value["path"]] = value
        paths_by_corpus.append(observations_by_path)

    _check_walks(by_location, observations)
    reasons = {}
    heads = {}
    for location, members in by_location.items():
        superseded = {ref for member in members for ref in member["supersedes"] if ref in observations}
        heads[location] = sorted((member for member in members if member["ref"] not in superseded), key=lambda item: item["ref"])
        reasons[location] = _head_reasons(heads[location])
    for corpus, observations_by_path in zip(capture["corpora"], paths_by_corpus):
        for location in _unsettled(corpus, observations_by_path):
            reasons.setdefault(location, set()).add("unsettled")

    active = []
    blocked = []
    for location in sorted(set(heads) | set(reasons)):
        projections = [_member(head, observations) for head in heads.get(location, ())]
        if reasons.get(location):
            blocked.append({"location": location, "reasons": sorted(reasons[location]), "heads": projections})
        else:
            active.extend(projections)
    active.sort(key=lambda item: item["head"])
    return {"active": active, "blocked": blocked}
