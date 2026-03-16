"""Loader-specific program transformations."""

from ..comput import computer
from ..comput import loader as loader_lang
from ..comput import widish as shell_lang
from ..state import loader as loader_state
from ..wire import loader as loader_wire
from .widish import Parallel, Pipeline


class LoaderToShell(computer.Functor):
    """Compile loader programs and execution boxes into shell diagrams."""

    def __init__(self):
        computer.Functor.__init__(
            self,
            self.ob_map,
            self.ar_map,
            dom=computer.Category(),
            cod=computer.Category(),
        )

    @staticmethod
    def ob_map(ob):
        if ob == loader_lang.loader_program_ty:
            return shell_lang.shell_program_ty
        if ob == loader_wire.loader_stream_ty:
            return shell_lang.io_ty
        return ob

    def __call__(self, other):
        if isinstance(other, loader_wire.LoaderSequence):
            return Pipeline(tuple(self(stage) for stage in other.stages))
        if isinstance(other, loader_wire.LoaderMapping):
            return Parallel(tuple(self(branch) for branch in other.branches))
        return computer.Functor.__call__(self, other)

    @staticmethod
    def ar_map(ar):
        if isinstance(ar, loader_lang.LoaderEmpty):
            return shell_lang.Empty()
        if isinstance(ar, loader_lang.LoaderLiteral):
            return shell_lang.Literal(ar.text)
        if isinstance(ar, loader_lang.LoaderCommand):
            return shell_lang.Command(ar.argv)
        if isinstance(ar, loader_state.LoaderStateUpdate):
            return shell_lang.ShellStateUpdate()
        if isinstance(ar, loader_state.LoaderOutput):
            return shell_lang.ShellOutput()
        return ar
