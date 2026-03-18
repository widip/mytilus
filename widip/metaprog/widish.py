"""Shell-specific program transformations and interpreters."""

from collections.abc import Callable
from itertools import count

from discopy import monoidal, python

from .core import Specializer
from . import core as metaprog_core
from . import python as metaprog_python
from ..comput import computer
from ..comput import widish as shell_lang
from ..state import core as state_core
from ..state.widish import parallel_io_diagram, shell_program_runner
from ..wire import widish as shell_wire


def _pipeline_diagram(stages):
    """Compose shell stages from top to bottom, skipping identities."""
    result = shell_wire.shell_id()
    identity = shell_wire.shell_id()
    for stage in stages:
        if stage == identity:
            continue
        result = stage if result == identity else result >> stage
    return result


def _tensor_all(diagrams):
    """Tensor shell stages left-to-right for bubble drawing."""
    diagrams = tuple(diagrams)
    if not diagrams:
        return computer.Id()
    result = diagrams[0]
    for diagram in diagrams[1:]:
        result = result @ diagram
    return result


def _specialize_shell(diagram, next_temp):
    """Recursively lower shell bubbles using one shared temp-path allocator."""
    if isinstance(diagram, Pipeline):
        return diagram.specialize(next_temp)
    if isinstance(diagram, Parallel):
        return diagram.specialize(next_temp)
    if isinstance(diagram, monoidal.Bubble):
        return _specialize_shell(diagram.arg, next_temp)
    if isinstance(diagram, computer.Box):
        return diagram
    if isinstance(diagram, computer.Diagram):
        result = computer.Id(diagram.dom)
        for left, box, right in diagram.inside:
            result = result >> left @ _specialize_shell(box, next_temp) @ right
        return result
    return diagram


def _has_shell_bubble(diagram) -> bool:
    """Detect whether a shell diagram still contains unspecialized bubbles."""
    if isinstance(diagram, monoidal.Bubble):
        return True
    if not isinstance(diagram, computer.Diagram):
        return False
    return any(isinstance(layer[1], monoidal.Bubble) for layer in diagram.inside)


class ShellSpecializer(Specializer):
    """Lower shell bubbles to their executable wiring."""

    def __init__(self):
        self._next_temp = count()
        Specializer.__init__(
            self,
            self.ob_map,
            self.ar_map,
            dom=computer.Category(),
            cod=computer.Category(),
        )

    @staticmethod
    def ob_map(ob):
        return ob

    def __call__(self, other):
        return _specialize_shell(other, self._next_temp)

    @staticmethod
    def ar_map(ar):
        return ar


class ShellInterpreter(metaprog_core.Interpreter):
    """Interpret shell diagrams as Python callables."""

    def __init__(self, specialize_shell):
        self.specialize_shell = specialize_shell
        metaprog_core.Interpreter.__init__(
            self,
            ob=self.ob_map,
            ar=self.ar_map,
            dom=computer.Category(),
            cod=python.Category(),
        )

    @staticmethod
    def ob_map(ob):
        if (
            isinstance(ob, computer.Ty)
            and len(ob) == 1
            and isinstance(ob.inside[0], computer.ProgramOb)
        ):
            return Callable
        return str

    def __call__(self, other):
        if _has_shell_bubble(other):
            return monoidal.Functor.__call__(self, self.specialize_shell(other))
        return monoidal.Functor.__call__(self, other)

    def ar_map(self, box):
        dom, cod = self(box.dom), self(box.cod)
        projection = state_core.ProcessRunner.projection_ar_map(self, box, dom, cod)
        structural = state_core.ProcessRunner.structural_ar_map(self, box, dom, cod)
        if projection is not None:
            return projection
        if structural is not None:
            return structural
        if isinstance(box, shell_lang.ShellProgram):
            return python.Function(lambda: shell_program_runner(box), dom, cod)
        if isinstance(box, computer.Computer):
            return python.Function(metaprog_python.apply_value, dom, cod)
        raise TypeError(f"unsupported shell interpreter box: {box!r}")


class Pipeline(monoidal.Bubble, computer.Box):
    """Bubble grouping shell stages in sequence."""

    def __init__(self, stages):
        self.stages = tuple(stages)
        monoidal.Bubble.__init__(
            self,
            _pipeline_diagram(self.stages),
            dom=shell_lang.io_ty,
            cod=shell_lang.io_ty,
            draw_vertically=True,
            drawing_name="seq",
        )

    def specialize(self, next_temp=None):
        next_temp = count() if next_temp is None else next_temp
        return _pipeline_diagram(tuple(_specialize_shell(stage, next_temp) for stage in self.stages))


class Parallel(monoidal.Bubble, computer.Box):
    """Bubble grouping parallel shell branches."""

    def __init__(self, branches):
        self.branches = tuple(branches)
        monoidal.Bubble.__init__(
            self,
            _tensor_all(self.branches) if self.branches else shell_wire.shell_id(),
            dom=shell_lang.io_ty,
            cod=shell_lang.io_ty,
            drawing_name="map",
        )

    def specialize(self, next_temp=None):
        next_temp = count() if next_temp is None else next_temp
        return parallel_io_diagram(
            tuple(_specialize_shell(branch, next_temp) for branch in self.branches),
            next_temp,
        )


def pipeline(stages):
    """Build a shell pipeline bubble."""
    stages = tuple(stages)
    if not stages:
        return shell_wire.shell_id()
    return Pipeline(stages)


def parallel(branches):
    """Build a shell parallel bubble."""
    branches = tuple(branches)
    if not branches:
        return shell_wire.shell_id()
    return Parallel(branches)
