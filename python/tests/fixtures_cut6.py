from beliefs.consulted import CorpusPins

SCIENCE_ID = "science:" + "a" * 64
BIOLOGY_ID = "biology:" + "b" * 64
PINS = CorpusPins(science_contract=SCIENCE_ID, domains={"biology": BIOLOGY_ID})


def manifest_document(corpus_id: str = "1" * 32) -> str:
    return (
        "manifest_version: 2\n"
        f"corpus_id: {corpus_id}\n"
        "profile:\n"
        f"  science_contract: {SCIENCE_ID}\n"
        "  domains:\n"
        f"    biology: {BIOLOGY_ID}\n"
    )
