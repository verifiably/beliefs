from profiles import WITH_BIOLOGY, WITH_BIOLOGY_OTHER, pins_for

PINS = pins_for(WITH_BIOLOGY)
OTHER_PINS = pins_for(WITH_BIOLOGY_OTHER)
SCIENCE_ID = PINS.science_contract
BIOLOGY_ID = PINS.domains["biology"]
OTHER_BIOLOGY_ID = OTHER_PINS.domains["biology"]


def manifest_document(corpus_id: str = "1" * 32) -> str:
    return (
        "manifest_version: 2\n"
        f"corpus_id: {corpus_id}\n"
        "profile:\n"
        f"  science_contract: {SCIENCE_ID}\n"
        "  domains:\n"
        f"    biology: {BIOLOGY_ID}\n"
    )
