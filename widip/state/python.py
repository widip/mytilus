"""Stateful shell-to-Python runtime transformations."""

from collections.abc import Callable

from discopy import monoidal, python

from ..comput import computer
from ..comput import widish as shell_lang
from ..metaprog import core as metaprog_core
from ..metaprog import python as metaprog_python
from ..pcc import SHELL
from . import core as state_core
from .widish import Parallel as ShellParallel
from .widish import Pipeline as ShellPipeline
from .widish import ShellSpecializer, shell_program_runner


def _has_shell_bubble(diagram) -> bool:
    """Detect whether a shell diagram still contains unspecialized bubbles."""
    if isinstance(diagram, monoidal.Bubble):
        return True
    if not isinstance(diagram, computer.Diagram):
        return False
    return any(isinstance(layer[1], monoidal.Bubble) for layer in diagram.inside)


class ShellToPythonProgram(state_core.ProcessSimulation):
    """Map shell programs and their evaluators to Python-program equivalents."""

    def __init__(self):
        state_core.ProcessSimulation.__init__(self)

    def simulation(self, item):
        if isinstance(item, shell_lang.ShellProgram):
            return metaprog_python.runtime_value_box(
                shell_program_runner(item),
                name=item.name,
            )
        return SHELL.simulate(item, metaprog_python.PYTHON_PROGRAMS)


class ProcessRunner(state_core.ProcessRunner):
    """Python interpretation of generic Eq. 7.1 process projections."""

    def __init__(self):
        state_core.ProcessRunner.__init__(self, cod=python.Category())

    def object(self, ob):
        del ob
        return object

    def state_update_value(self, state, _input):
        del self
        return state

    def output_value(self, state, input_value):
        del self
        return state(input_value)

    def state_update_ar(self, dom, cod):
        return python.Function(self.state_update_value, dom, cod)

    def output_ar(self, dom, cod):
        return python.Function(self.output_value, dom, cod)

    def map_structural(self, box, dom, cod):
        del cod
        return metaprog_python.map_structural_box(self, box, dom)


class ShellInterpreter(ProcessRunner, metaprog_core.Interpreter):
    """Interpret shell diagrams as Python callables."""

    def __init__(self, specialize_shell, program_functor, python_runtime):
        self.specialize_shell = specialize_shell
        self.program_functor = program_functor
        self.python_runtime = python_runtime
        ProcessRunner.__init__(self)

    def object(self, ob):
        del self
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

    def process_ar_map(self, box, dom, cod):
        if isinstance(box, ShellPipeline):
            stages = tuple(self(stage) for stage in box.stages)

            def run(stdin):
                output = stdin
                for stage in stages:
                    output = stage(output)
                return output

            return python.Function(run, dom, cod)
        if isinstance(box, ShellParallel):
            branches = tuple(self(branch) for branch in box.branches)

            def run(stdin):
                if not branches:
                    return stdin
                if len(branches) == 1:
                    return branches[0](stdin)
                return "".join(branch(stdin) for branch in branches)

            return python.Function(run, dom, cod)
        if isinstance(box, (shell_lang.ShellProgram, computer.Computer)):
            return self.python_runtime(self.program_functor(box))
        raise TypeError(f"unsupported shell interpreter box: {box!r}")


SHELL_SPECIALIZER = ShellSpecializer()
SHELL_PROGRAM_TO_PYTHON = ShellToPythonProgram()


class ShellPythonRuntime(metaprog_python.PythonRuntime):
    """Python runtime with shell-specific object interpretation."""

    def object(self, ob):
        if (
            isinstance(ob, computer.Ty)
            and len(ob) == 1
            and isinstance(ob.inside[0], computer.ProgramOb)
        ):
            return Callable
        return str


SHELL_PYTHON_RUNTIME = ShellPythonRuntime()
SHELL_INTERPRETER = ShellInterpreter(
    SHELL_SPECIALIZER,
    SHELL_PROGRAM_TO_PYTHON,
    SHELL_PYTHON_RUNTIME,
)
