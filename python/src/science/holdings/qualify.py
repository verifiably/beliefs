# GENERATED from science/intents/holdings.py by tools/regen_holdings_interior.py.
# Edit the source and regenerate; hand edits here are discarded.
# ruff: noqa: I001 -- this source permits exactly one top-level import in the rule dialect
"""Pure holdings-intent qualification helpers shipped with the rule."""

import json


ACT_KINDS = ("re-check", "write", "delete", "move-source", "move-destination")
MUTATING_KINDS = ("write", "delete", "move-source", "move-destination")
HOLDINGS_INTENT_DOMAIN = "science.holdings-intent.v1"


def _lower_hex(value, width):
    return isinstance(value, str) and len(value) == width and all(character in "0123456789abcdef" for character in value)


def _store_path(value):
    if not isinstance(value, str) or not value or "\x00" in value or value.startswith("/") or value.endswith("/"):
        return False
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return all(component and component not in (".", "..") and not component.startswith(".#~") for component in value.split("/"))


def _location(value):
    if not isinstance(value, dict) or set(value) != {"relative_path", "store_id", "type"}:
        return None
    if value["type"] != "store" or not _lower_hex(value["store_id"], 32) or not _store_path(value["relative_path"]):
        return None
    return "store:" + value["store_id"] + ":" + value["relative_path"]


def decode_holdings_intent(row):
    """Return a validated holdings intent, or ``None`` for another domain."""
    try:
        value = json.loads(bytes.fromhex(row["entry"]["payload"]).decode("utf-8"))
    except (ValueError, UnicodeError, KeyError, TypeError):
        return None
    if not isinstance(value, dict) or value.get("domain") != HOLDINGS_INTENT_DOMAIN:
        return None
    valid = (
        set(value) == {"actor", "domain", "event_token", "kind", "location"}
        and isinstance(value["actor"], str)
        and bool(value["actor"])
        and isinstance(value["event_token"], str)
        and bool(value["event_token"])
        and value["kind"] in ACT_KINDS
        and _location(value["location"]) is not None
    )
    if not valid:
        raise ValueError("malformed holdings intent at " + row["digest"])
    return {
        "digest": row["digest"],
        "event_token": value["event_token"],
        "kind": value["kind"],
        "location": _location(value["location"]),
    }


def holdings_layout_path(path):
    prefix = "holdings-observation/"
    suffix = ".md"
    return (
        isinstance(path, str)
        and path.startswith(prefix)
        and path.endswith(suffix)
        and _lower_hex(path[len(prefix):-len(suffix)], 64)
    )


def _file(facts):
    return any(pair[0] == "kind" and pair[1] == "file" for pair in facts)


def qualify_intent(intent, registrations, observations_by_path):
    """Classify one intent by matched, unresolved, non-qualifying precedence."""
    unresolved = False
    for registration in registrations:
        settlement = registration["settlement"]
        if settlement is None:
            unresolved = True
            continue
        if settlement == "rolled-back":
            continue
        for path, facts in registration["final"]:
            if not _file(facts):
                continue
            observation = observations_by_path.get(path)
            if observation is not None:
                if observation["location"] == intent["location"] and observation["event_token"] == intent["event_token"]:
                    return "matched"
            elif holdings_layout_path(path):
                unresolved = True
    return "unresolved" if unresolved else "unmatched"
