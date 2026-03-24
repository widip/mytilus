from mytilus.comput.shell import io_ty
from mytilus.pcc import LOADER, SHELL
from mytilus.state.loader import LoaderExecution
from mytilus.state.shell import ShellExecution
from mytilus.wire.loader import loader_stream_ty


def test_loader_and_shell_projections_live_in_state():
    assert LoaderExecution().state_update_diagram() == LOADER.execution(
        loader_stream_ty, loader_stream_ty
    ).state_update_diagram()
    assert LoaderExecution().output_diagram() == LOADER.execution(
        loader_stream_ty, loader_stream_ty
    ).output_diagram()
    assert ShellExecution().state_update_diagram() == SHELL.execution(io_ty, io_ty).state_update_diagram()
    assert ShellExecution().output_diagram() == SHELL.execution(io_ty, io_ty).output_diagram()
