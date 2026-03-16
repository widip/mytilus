"""Shell-specific program transformations and interpreters."""

from discopy import monoidal, python

from ..comput import computer
from ..comput import widish as shell_lang
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


def _shell_stage(program):
    """Run a primitive shell program through the standard shell evaluator."""
    return program @ shell_lang.io_ty >> shell_lang.ShellOutput()


def _parallel_diagram(branches):
    """Lower a parallel bubble to compact shell wiring."""
    branches = tuple(branches)
    if not branches:
        return shell_wire.shell_id()
    if len(branches) == 1:
        return branches[0]
    return shell_wire.Copy(len(branches)) >> _tensor_all(branches) >> shell_wire.Merge(len(branches))


class Pipeline(monoidal.Bubble, computer.Box):
    """Bubble grouping shell stages in sequence."""

    def __init__(self, stages):
        self.stages = tuple(stages)
        arg = _pipeline_diagram(self.stages)
        monoidal.Bubble.__init__(
            self,
            arg,
            dom=shell_lang.io_ty,
            cod=shell_lang.io_ty,
            draw_vertically=True,
            drawing_name="seq",
        )

    def specialize(self):
        return _pipeline_diagram(tuple(specialize_shell(stage) for stage in self.stages))


class Parallel(monoidal.Bubble, computer.Box):
    """Bubble grouping parallel shell branches."""

    def __init__(self, branches):
        self.branches = tuple(branches)
        arg = _tensor_all(self.branches) if self.branches else shell_wire.shell_id()
        monoidal.Bubble.__init__(
            self,
            arg,
            dom=shell_lang.io_ty,
            cod=shell_lang.io_ty,
            drawing_name="map",
        )

    def specialize(self):
        return _parallel_diagram(tuple(specialize_shell(branch) for branch in self.branches))


Sequence = Pipeline
Mapping = Parallel


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


class ShellSpecializer(computer.Functor):
    """Lower shell bubbles to their executable wiring."""

    def __init__(self):
        computer.Functor.__init__(self, self.ob_map, self.ar_map, dom=computer.Category(), cod=computer.Category())

    @staticmethod
    def ob_map(ob):
        return ob

    def __call__(self, other):
        if isinstance(other, Pipeline):
            return _pipeline_diagram(tuple(self(stage) for stage in other.stages))
        if isinstance(other, Parallel):
            return _parallel_diagram(tuple(self(branch) for branch in other.branches))
        if isinstance(other, monoidal.Bubble):
            return self(other.arg)
        return computer.Functor.__call__(self, other)

    @staticmethod
    def ar_map(ar):
        return ar


def specialize_shell(diagram: computer.Diagram) -> computer.Diagram:
    """Recursively lower shell bubbles to plain shell wiring."""
    return ShellSpecializer()(diagram)


class ShellRunner(monoidal.Functor):
    """Interpret shell diagrams as Python callables over stateful text streams."""

    def __init__(self):
        monoidal.Functor.__init__(
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
            return shell_lang.ShellProgram
        return str

    def __call__(self, box):
        if isinstance(box, Pipeline):
            return self(box.specialize())
        if isinstance(box, Parallel):
            return self(box.specialize())
        if isinstance(box, monoidal.Bubble):
            return self(box.arg)
        return monoidal.Functor.__call__(self, box)

    def ar_map(self, box):
        dom, cod = self(box.dom), self(box.cod)

        if isinstance(box, shell_lang.ShellProgram):
            return python.Function(lambda: box, dom, cod)
        if isinstance(box, shell_lang.ShellStateUpdate):
            return python.Function(lambda program, _stdin: program, dom, cod)
        if isinstance(box, shell_lang.ShellOutput):
            return python.Function(lambda program, stdin: program.run(stdin), dom, cod)
        if isinstance(box, computer.Copy):
            return python.Function.copy(dom, n=2)
        if isinstance(box, shell_wire.Merge):
            return python.Function(lambda *parts: "".join(parts), dom, cod)
        if isinstance(box, computer.Delete):
            return python.Function.discard(dom)
        if isinstance(box, computer.Swap):
            return python.Function.swap(self(box.left), self(box.right))

        raise TypeError(f"unsupported shell box: {box!r}")


def compile_shell_program(diagram: computer.Diagram) -> python.Function:
    """Compile a shell diagram into an executable Python function."""
    from . import SHELL_RUNNER

    return SHELL_RUNNER(diagram)
