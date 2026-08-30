"""Versioned canonical-value contracts.

Versions live side by side and never share a digest domain, so a v2 encoding can
never be mistaken for a v1 one (computation §4.3).
"""

from beliefs.identity.v1 import check_domain, digest, encode

__all__ = ["check_domain", "digest", "encode"]
