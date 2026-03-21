from discorun.comput.computer import Box as ComputerBox
from discorun.comput.computer import Copy as ComputerCopy
from discorun.comput.computer import Ty as ComputerTy
from mytilus.comput.mytilus import io_ty as shell_io_ty
from discorun.wire.functions import Box
from mytilus.wire.loader import loader_id, loader_stream_ty
from discorun.wire.services import Copy, Delete, Swap
from discorun.wire.types import Diagram, Id, Ty
from mytilus.wire.mytilus import Copy as ShellCopy, shell_id


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


def test_loader_wire_module_exports_loader_specific_wiring():
    assert loader_id().dom == loader_stream_ty
    assert loader_id().cod == loader_stream_ty


def test_mytilus_wire_module_exports_shell_specific_wiring():
    assert shell_id().dom == shell_io_ty
    assert shell_id().cod == shell_io_ty
    assert ShellCopy(3).dom == shell_io_ty
    assert ShellCopy(3).cod == shell_io_ty @ shell_io_ty @ shell_io_ty
