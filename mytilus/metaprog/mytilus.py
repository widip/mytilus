"""Shell-specific program transformations and interpreters."""

from discopy import monoidal

from discorun.metaprog.core import Specializer
from discorun.comput import computer
from ..comput import mytilus as shell_lang
from ..wire import mytilus as shell_wire


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


def _specialize_shell(diagram):
    """Recursively lower shell bubbles."""
    if isinstance(diagram, Pipeline):
        return diagram.specialize()
    if isinstance(diagram, Parallel):
        return diagram.specialize()
    if isinstance(diagram, monoidal.Bubble):
        return _specialize_shell(diagram.arg)
    if isinstance(diagram, computer.Box):
        return diagram
    if isinstance(diagram, computer.Diagram):
        result = computer.Id(diagram.dom)
        for left, box, right in diagram.inside:
            result = result >> left @ _specialize_shell(box) @ right
        return result
    return diagram


class ShellSpecializer(Specializer):
    """Lower shell bubbles to their executable wiring."""

    def __init__(self):
        Specializer.__init__(
            self,
            dom=computer.Category(),
            cod=computer.Category(),
        )

    def __call__(self, other):
        return _specialize_shell(other)

    def ar_map(self, ar):
        del self
        return ar


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

    def specialize(self):
        return _pipeline_diagram(
            tuple(_specialize_shell(stage) for stage in self.stages),
        )


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

    def specialize(self):
        return Parallel(
            tuple(_specialize_shell(branch) for branch in self.branches),
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
