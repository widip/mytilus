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

    def compile_command_argument(self, argument):
        """Compile one loader scalar argument to a shell argv item."""
        if isinstance(argument, str):
            return argument
        if not isinstance(argument, loader_wire.LoaderScalar):
            raise TypeError(f"unsupported command argument: {argument!r}")
        if argument.tag:
            if isinstance(argument.value, tuple):
                argv = (
                    argument.tag,
                    *(self.compile_command_argument(value) for value in argument.value),
                )
            else:
                argv = (
                    (argument.tag,)
                    if not argument.value
                    else (argument.tag, self.compile_command_argument(argument.value))
                )
            return shell_lang.Command(argv)
        if isinstance(argument.value, tuple):
            raise TypeError(f"untagged argv tuple is unsupported: {argument.value!r}")
        if not isinstance(argument.value, str):
            raise TypeError(f"untagged scalar argument must be a string: {argument.value!r}")
        return argument.value

    def command_argv(self, node: loader_wire.LoaderScalar):
        """Build argv for a tagged loader scalar."""
        if isinstance(node.value, tuple):
            return (
                node.tag,
                *(self.compile_command_argument(value) for value in node.value),
            )
        if not node.value:
            return (node.tag,)
        return (node.tag, self.compile_command_argument(node.value))

    def compile_scalar(self, node: loader_wire.LoaderScalar):
        """Compile one YAML scalar node to the shell backend."""
        execution = SHELL.execution(
            shell_lang.io_ty,
            shell_lang.io_ty,
        ).output_diagram()
        if node.tag:
            argv = self.command_argv(node)
            return shell_lang.Command(argv) @ shell_lang.io_ty >> execution
        if isinstance(node.value, tuple):
            raise TypeError(f"untagged argv tuple is unsupported: {node.value!r}")
        if not node.value:
            return shell_wire.shell_id()
        return shell_lang.Literal(node.value) @ shell_lang.io_ty >> execution
