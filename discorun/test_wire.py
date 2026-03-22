from discorun.comput.computer import Box as ComputerBox
from discorun.comput.computer import Copy as ComputerCopy
from discorun.comput.computer import Ty as ComputerTy
from discorun.wire.functions import Box
from discorun.wire.services import Copy, Delete, Swap
from discorun.wire.types import Diagram, Id, Ty


def test_wire_exports_chapter_one_primitives():
    A, B = Ty("A"), Ty("B")

    assert Ty is ComputerTy
    assert Box is ComputerBox
    assert Copy is ComputerCopy
    assert isinstance(Id(A), Diagram)
    assert Copy(A).dom == A
    assert Copy(A).cod == A @ A
    assert Delete(A).dom == A
    assert Delete(A).cod == Ty()
    assert Swap(A, B).dom == A @ B
    assert Swap(A, B).cod == B @ A
