"""Stateful shell-to-Python runtime transformations."""

from collections.abc import Callable

from discopy import monoidal, python

from discorun.comput import computer
import mytilus.metaprog as mytilus_metaprog
import mytilus.pcc as mytilus_pcc
from ..comput import mytilus as shell_lang
from ..comput import python as comput_python
from discorun.metaprog import core as metaprog_core
from ..metaprog import python as metaprog_python
from discorun.state import core as state_core
from .mytilus import Parallel as ShellParallel
from .mytilus import Pipeline as ShellPipeline
from .mytilus import shell_program_runner


_PATHS_ATTR = "_mytilus_runtime_paths"


def _run_paths(paths, stdin):
    """Execute all independent pipelines sequentially and concatenate outputs."""
    outputs = []
    for path in paths:
        output = stdin
        for stage in path:
            output = comput_python.run(stage, output)
        outputs.append(output)
    if not outputs:
        return stdin
    if len(outputs) == 1:
        return outputs[0]
    return "".join(outputs)


def runtime_values(value):
    """Normalize interpreter output values under the runtime tuple convention."""
    if isinstance(value, tuple) and len(value) == 1:
        value = value[0]
    if isinstance(value, tuple):
        return value
    return (value,)


class ShellToPythonProgram(state_core.ProcessSimulation):
    """Map shell programs and their evaluators to Python-program equivalents."""

    def __init__(self):
        state_core.ProcessSimulation.__init__(self)

    def simulation(self, item):
        if isinstance(item, shell_lang.ShellProgram):
            return comput_python.runtime_value_box(
                shell_program_runner(item),
                name=item.name,
                cod=mytilus_metaprog.PYTHON_PROGRAMS.program_ty,
            )
        return mytilus_pcc.SHELL.simulate(item, mytilus_metaprog.PYTHON_PROGRAMS)

    def out(self, output):
        if mytilus_pcc.SHELL.is_evaluator(output):
            return mytilus_pcc.SHELL.simulate(output, mytilus_metaprog.PYTHON_PROGRAMS)
        return state_core.ProcessSimulation.out(self, output)


class ProcessRunner(state_core.ProcessRunner):
    """Python interpretation of generic Eq. 7.1 process projections."""

    def __init__(self, data_services=None):
        self.data_services = comput_python.PythonDataServices() if data_services is None else data_services
        state_core.ProcessRunner.__init__(self, cod=python.Category())

    def object(self, ob):
        del ob
        return object

    def state_update_ar(self, dom, cod):
        return python.Function(lambda state, _input: state, dom, cod)

    def output_ar(self, dom, cod):
        return python.Function(lambda state, input_value: comput_python.uev(state, input_value), dom, cod)

    def map_structural(self, box, dom, cod):
        del dom, cod
        if not isinstance(box, (computer.Copy, computer.Delete, computer.Swap)):
            return None
        return self.data_services(box)


class ShellInterpreter(ProcessRunner, metaprog_core.Interpreter):
    """Interpret shell diagrams as Python callables."""

    def __init__(self, specialize_shell, program_functor, python_runtime):
        self.specialize_shell = specialize_shell
        self.program_functor = program_functor
        self.python_runtime = python_runtime
        ProcessRunner.__init__(self, data_services=comput_python.ShellPythonDataServices())

    def object(self, ob):
        del self
        if isinstance(ob, computer.ProgramOb):
            return Callable
        return str

    def interpret(self, other):
        return monoidal.Functor.__call__(self, other)

    def process_ar_map(self, box, dom, cod):
        if isinstance(box, ShellPipeline):
            paths = ((),)
            for stage in (self(stage) for stage in box.stages):
                paths = tuple(
                    prefix + suffix
                    for prefix in paths
                    for suffix in getattr(stage, _PATHS_ATTR, ((stage,),))
                )
            function = python.Function(lambda stdin, _paths=paths: _run_paths(_paths, stdin), dom, cod)
            function.__dict__[_PATHS_ATTR] = paths
            return function
        if isinstance(box, ShellParallel):
            branch_paths = tuple(
                path
                for branch in (self(branch) for branch in box.branches)
                for path in getattr(branch, _PATHS_ATTR, ((branch,),))
            )
            if not branch_paths:
                branch_paths = ((),)
            function = python.Function(lambda stdin, _paths=branch_paths: _run_paths(_paths, stdin), dom, cod)
            function.__dict__[_PATHS_ATTR] = branch_paths
            return function
        if isinstance(box, (shell_lang.ShellProgram, computer.Computer)):
            runner = self.python_runtime(self.program_functor(box))
            runner.__dict__[_PATHS_ATTR] = ((runner,),)
            return runner
        raise TypeError(f"unsupported shell interpreter box: {box!r}")


class ShellPythonRuntime(metaprog_python.PythonRuntime):
    """Python runtime with shell-specific object interpretation."""

    def _identity_object(self, ob):
        return comput_python.ShellPythonDataServices.object(self, ob)
