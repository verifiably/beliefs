"""The declared sample-label convention; this is not clinical diagnosis."""


def stage_token(sample: str, separator: str) -> str:
    if not separator or separator not in sample:
        raise ValueError("sample carries no group token")
    token = sample.rsplit(separator, 1)[-1]
    if token not in {"NDMM", "PD"}:
        raise ValueError("unknown group token; expected NDMM or PD")
    return token
