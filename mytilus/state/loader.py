"""Loader-specific stateful execution."""

import mytilus.pcc as mytilus_pcc

from ..comput import loader as loader_lang
from ..comput.loader import loader_program_ty
from ..comput import shell as shell_lang
from ..wire import loader as loader_wire
from ..wire.loader import loader_stream_ty
from ..wire import shell as shell_wire
from discorun.state.core import Execution, ProcessSimulation
from .shell import Parallel, Pipeline, SubstitutionParallel, SubstitutionPipeline


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
        if mytilus_pcc.LOADER.is_evaluator(item):
            return mytilus_pcc.SHELL.evaluator(
                self.simulation(item.A),
                self.simulation(item.B),
            )
        return mytilus_pcc.LOADER.simulate(item, mytilus_pcc.SHELL)

    def __call__(self, other):
        if isinstance(other, loader_wire.LoaderScalar):
            return self.compile_scalar(other)
        if isinstance(other, loader_wire.LoaderSequence):
            return Pipeline(tuple(self(stage) for stage in other.stages))
        if isinstance(other, loader_wire.LoaderMapping):
            return Parallel(tuple(self(branch) for branch in other.branches))
        return ProcessSimulation.__call__(self, other)

    def compile_subprogram(self, node):
        """Compile one loader node to a shell subprogram for substitution."""
        if isinstance(node, loader_wire.LoaderScalar):
            if node.tag:
                return shell_lang.Command(self.command_argv(node))
            if isinstance(node.value, tuple):
                raise TypeError(f"untagged argv tuple is unsupported: {node.value!r}")
            if not isinstance(node.value, str):
                raise TypeError(f"untagged scalar argument must be a string: {node.value!r}")
            if not node.value:
                return shell_lang.Empty()
            return shell_lang.Literal(node.value)
        if isinstance(node, loader_wire.LoaderSequence):
            return SubstitutionPipeline(tuple(self.compile_subprogram(stage) for stage in node.stages))
        if isinstance(node, loader_wire.LoaderMapping):
            return SubstitutionParallel(tuple(self.compile_subprogram(branch) for branch in node.branches))
        raise TypeError(f"unsupported substitution node: {node!r}")

    def compile_command_argument(self, argument):
        """Compile one loader scalar argument to a shell argv item."""
        if isinstance(argument, str):
            return argument
        if isinstance(argument, (loader_wire.LoaderSequence, loader_wire.LoaderMapping)):
            return self.compile_subprogram(argument)
        if not isinstance(argument, loader_wire.LoaderScalar):
            raise TypeError(f"unsupported command argument: {argument!r}")
        if argument.tag:
            return self.compile_subprogram(argument)
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
        execution = mytilus_pcc.SHELL.execution(
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
