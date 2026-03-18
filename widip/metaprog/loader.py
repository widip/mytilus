"""Loader-specific program transformations."""

from nx_yaml import nx_compose_all

from .core import Specializer
from .hif import HIFToLoader
from ..comput import computer
from ..comput import loader as loader_lang
from ..comput import widish as shell_lang
from ..state.core import map_process_box
from ..state.widish import shell_stage as shell_io_stage
from ..wire.hif import HyperGraph
from ..wire import loader as loader_wire
from ..wire import widish as shell_wire
from .widish import Parallel, Pipeline


def _compile_scalar(node: loader_wire.LoaderScalar):
    """Compile one YAML scalar node to the shell backend."""
    if node.tag:
        argv = (node.tag,) if not node.value else (node.tag, node.value)
        return shell_io_stage(shell_lang.Command(argv))
    if not node.value:
        return shell_wire.shell_id()
    return shell_io_stage(shell_lang.Literal(node.value))


class LoaderToShell(Specializer):
    """Compile loader nodes, programs, and execution boxes into shell diagrams."""

    def __init__(self):
        Specializer.__init__(
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
        if isinstance(other, loader_wire.LoaderScalar):
            return _compile_scalar(other)
        if isinstance(other, loader_wire.LoaderSequence):
            return Pipeline(tuple(self(stage) for stage in other.stages))
        if isinstance(other, loader_wire.LoaderMapping):
            return Parallel(tuple(self(branch) for branch in other.branches))
        return Specializer.__call__(self, other)

    def ar_map(self, ar):
        ar = map_process_box(ar, self.ob_map)
        if isinstance(ar, loader_lang.LoaderEmpty):
            return shell_lang.Empty()
        if isinstance(ar, loader_lang.LoaderLiteral):
            return shell_lang.Literal(ar.text)
        return ar


HIF_TO_LOADER = HIFToLoader()
LOADER_TO_SHELL = LoaderToShell()
