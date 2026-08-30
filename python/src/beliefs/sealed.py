"""``sealed`` — close a class to subclassing at runtime.

Opacity is worth exactly what `isinstance` is worth. A type whose only route in
is a validated constructor still admits an unchecked object if it can be
subclassed: the subclass defines its own `__init__`, mints whatever it likes, and
the result satisfies `isinstance(x, Claim)`. Every downstream reader that trusts
a `Claim` unconditionally — which is the whole point of checking once, at one
place (M13) — is then wrong, with no line of the checked type edited.

`typing.final` states the rule for a static checker and enforces nothing at run
time, which is the wrong half: the object that reaches a reader is a runtime
object, and the code that would subclass is exactly the code not being type
checked. So both are used together — `@final` for the reader and the checker,
`@sealed` for the guarantee.

A shared base class would be the obvious alternative and is the wrong one twice
over: it is inheritance where composition does, and the base would itself be
subclassable, which reopens the hole one level up.
"""

from __future__ import annotations

from typing import TypeVar

from beliefs.errors import SubclassRefused

__all__ = ["sealed"]

T = TypeVar("T", bound=type)


def sealed(cls: T) -> T:
    """Refuse every subclass of ``cls``, at class-creation time."""

    def __init_subclass__(subclass: type, **kwargs: object) -> None:
        raise SubclassRefused(
            f"{cls.__name__} is sealed and cannot be subclassed. Its guarantee is that holding one means "
            "it was checked; a subclass could mint an unchecked object that still satisfies isinstance()."
        )

    cls.__init_subclass__ = classmethod(__init_subclass__)  # type: ignore[assignment]
    return cls
