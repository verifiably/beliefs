"""The one `Authority` every act of the exercise binds."""

from __future__ import annotations

from beliefs.permit import Authority, WritePermit

ACTOR = "mm30-reproduction"
AUTHORITY = Authority(WritePermit.full(), ACTOR)
