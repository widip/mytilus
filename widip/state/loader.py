"""Loader-specific stateful execution."""

from ..comput import computer
from ..comput.loader import loader_program_ty
from ..wire.loader import loader_stream_ty
from . import Execution, ProgramClosedCategory, out


class LoaderStateUpdate(computer.Box):
    """State projection box for loader execution."""

    def __init__(self):
        computer.Box.__init__(self, "sta(loader)", loader_program_ty @ loader_stream_ty, loader_program_ty)


class LoaderOutput(computer.Box):
    """Observable-output box for loader execution."""

    def __init__(self):
        computer.Box.__init__(self, "out(loader)", loader_program_ty @ loader_stream_ty, loader_stream_ty)


class LoaderExecution(Execution):
    """Stateful execution process for loader programs."""

    def __init__(self):
        Execution.__init__(
            self,
            loader_program_ty,
            loader_stream_ty,
            loader_stream_ty,
            universal_ev_diagram=computer.Computer(
                loader_program_ty,
                loader_stream_ty,
                loader_program_ty @ loader_stream_ty,
            ),
            state_update_diagram=LoaderStateUpdate(),
            output_diagram=LoaderOutput(),
        )


class LoaderLanguage(ProgramClosedCategory):
    """Program-closed category for the YAML loader language."""

    def __init__(self):
        ProgramClosedCategory.__init__(self, loader_program_ty)

    def execution(self, A: computer.Ty, B: computer.Ty):
        del A, B
        return LoaderExecution()


def loader_execution() -> computer.Diagram:
    """Projection to observable output of loader execution."""
    from . import LOADER

    return out(LOADER.execution(loader_stream_ty, loader_stream_ty))


def run_loader_program(program: computer.Diagram) -> computer.Diagram:
    """Execute a closed loader program on one loader stream wire."""
    return program @ loader_stream_ty >> loader_execution()
