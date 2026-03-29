"""Shell-specific wire combinators and structural boxes."""

from discopy import monoidal
from discorun.comput import computer
from discorun.wire.services import Copy as CopyService, Delete
from discorun.wire.types import Id, Ty


io_ty = Ty("stdout") @ Ty("rc") @ Ty("stderr")


def io_wires(n: int):
    """Return the monoidal product of ``n`` shell-stream wires."""
    wires = Ty()
    for _ in range(n):
        wires = wires @ io_ty
    return wires


def shell_id():
    """Identity shell process on one stream."""
    return Id(io_ty)


def Copy(n: int, unit=io_ty):
    """N-ary stream fan-out built from the cartesian copy service."""
    if n < 0:
        raise ValueError("copy arity must be non-negative")
    if n == 0:
        return Delete(unit)
    if n == 1:
        return Id(unit)
    result = CopyService(unit)
    for copies in range(2, n):
        result = result >> Id(unit ** (copies - 1)) @ CopyService(unit)
    return result


class Merge(computer.Box):
    """N-ary stream fan-in (merger) for shell status triples."""

    def __init__(self, n: int, unit=io_ty):
        self.n = n
        monoidal.Box.__init__(
            self,
            name=f"Merge({n})",
            dom=unit ** n,
            cod=unit,
        )
