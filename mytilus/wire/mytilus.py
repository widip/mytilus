"""Shell-specific wire combinators and structural boxes."""

from .services import Copy as CopyService, Delete
from .types import Id, Ty


io_ty = Ty("io")


def io_wires(n: int):
    """Return the monoidal product of ``n`` shell-stream wires."""
    wires = Ty()
    for _ in range(n):
        wires = wires @ io_ty
    return wires


def shell_id():
    """Identity shell process on one stream."""
    return Id(io_ty)


def Copy(n: int):
    """N-ary stream fan-out built from the cartesian copy service."""
    if n < 0:
        raise ValueError("copy arity must be non-negative")
    if n == 0:
        return Delete(io_ty)
    if n == 1:
        return shell_id()
    result = CopyService(io_ty)
    for copies in range(2, n):
        result = result >> io_wires(copies - 1) @ CopyService(io_ty)
    return result
