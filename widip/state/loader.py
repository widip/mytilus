"""Loader-specific stateful execution."""

from ..comput import loader as loader_lang
from ..comput.loader import loader_program_ty
from ..comput import widish as shell_lang
from ..pcc import LOADER, SHELL
from ..wire import loader as loader_wire
from ..wire.loader import loader_stream_ty
from ..wire import widish as shell_wire
from .core import Execution, ProcessSimulation
from .widish import Parallel, Pipeline


class LoaderExecution(Execution):
    """Stateful execution process for loader programs."""

    def __init__(self):
        Execution.__init__(
            self,
            "loader",
            loader_program_ty,
            loader_stream_ty,
            loader_stream_ty,
        )


class LoaderToShell(ProcessSimulation):
    """State-aware loader-to-shell specializer."""

    def __init__(self):
        ProcessSimulation.__init__(self)

    def simulation(self, item):
        if item == loader_stream_ty:
            return shell_lang.io_ty
        if isinstance(item, loader_lang.LoaderEmpty):
            return shell_lang.Empty()
        if isinstance(item, loader_lang.LoaderLiteral):
            return shell_lang.Literal(item.text)
        if LOADER.is_evaluator(item):
            return SHELL.evaluator(
                self.simulation(item.A),
                self.simulation(item.B),
            )
        return LOADER.simulate(item, SHELL)

    def __call__(self, other):
        if isinstance(other, loader_wire.LoaderScalar):
            return self.compile_scalar(other)
        if isinstance(other, loader_wire.LoaderSequence):
            return Pipeline(tuple(self(stage) for stage in other.stages))
        if isinstance(other, loader_wire.LoaderMapping):
            return Parallel(tuple(self(branch) for branch in other.branches))
        return ProcessSimulation.__call__(self, other)

    def compile_scalar(self, node: loader_wire.LoaderScalar):
        """Compile one YAML scalar node to the shell backend."""
        execution = SHELL.execution(
            shell_lang.io_ty,
            shell_lang.io_ty,
        ).output_diagram()
        if node.tag:
            argv = (node.tag,) if not node.value else (node.tag, node.value)
            return shell_lang.Command(argv) @ shell_lang.io_ty >> execution
        if not node.value:
            return shell_wire.shell_id()
        return shell_lang.Literal(node.value) @ shell_lang.io_ty >> execution
