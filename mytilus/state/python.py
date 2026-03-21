"""Stateful shell-to-Python runtime transformations."""

from collections.abc import Callable

from discopy import monoidal, python

from ..comput import computer
from ..comput import mytilus as shell_lang
from ..metaprog import core as metaprog_core
from ..metaprog import python as metaprog_python
from ..pcc import SHELL
from . import core as state_core
from .mytilus import Parallel as ShellParallel
from .mytilus import Pipeline as ShellPipeline
from .mytilus import ShellSpecializer, shell_program_runner


_PATHS_ATTR = "_mytilus_runtime_paths"


def _runner_paths(runner):
    """Return execution paths carried by one interpreted shell stage."""
    paths = getattr(runner, _PATHS_ATTR, None)
    if paths is None:
        return ((runner,),)
    return paths


def _compose_paths(prefixes, suffixes):
    """Compose two path sets by Cartesian product."""
    return tuple(prefix + suffix for prefix in prefixes for suffix in suffixes)


def _run_paths(paths, stdin):
    """Execute all independent pipelines sequentially and concatenate outputs."""
    outputs = []
    for path in paths:
        output = stdin
        for stage in path:
            output = stage(output)
        outputs.append(output)
    if not outputs:
        return stdin
    if len(outputs) == 1:
        return outputs[0]
    return "".join(outputs)


def _path_runner(paths, dom, cod):
    """Build a Python runner while preserving expanded pipeline-path metadata."""
    function = python.Function(lambda stdin, _paths=paths: _run_paths(_paths, stdin), dom, cod)
    function.__dict__[_PATHS_ATTR] = paths
    return function


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
        return monoidal.Functor.__call__(self, other)

    def process_ar_map(self, box, dom, cod):
        if isinstance(box, ShellPipeline):
            paths = ((),)
            for stage in (self(stage) for stage in box.stages):
                paths = _compose_paths(paths, _runner_paths(stage))
            return _path_runner(paths, dom, cod)
        if isinstance(box, ShellParallel):
            branch_paths = tuple(
                path
                for branch in (self(branch) for branch in box.branches)
                for path in _runner_paths(branch)
            )
            if not branch_paths:
                branch_paths = ((),)
            return _path_runner(branch_paths, dom, cod)
        if isinstance(box, (shell_lang.ShellProgram, computer.Computer)):
            runner = self.python_runtime(self.program_functor(box))
            runner.__dict__[_PATHS_ATTR] = ((runner,),)
            return runner
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
