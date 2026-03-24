from mytilus.comput.shell import io_ty as shell_io_ty
from mytilus.wire.loader import loader_id, loader_stream_ty
from mytilus.wire.shell import Copy as ShellCopy, shell_id


def test_loader_wire_module_exports_loader_specific_wiring():
    assert loader_id().dom == loader_stream_ty
    assert loader_id().cod == loader_stream_ty


def test_mytilus_wire_module_exports_shell_specific_wiring():
    assert shell_id().dom == shell_io_ty
    assert shell_id().cod == shell_io_ty
    assert ShellCopy(3).dom == shell_io_ty
    assert ShellCopy(3).cod == shell_io_ty @ shell_io_ty @ shell_io_ty
