"""Shell-specific stateful execution."""

import subprocess
from collections.abc import Callable

from discopy import monoidal, python

from discorun.comput import computer
from discorun.metaprog import core as metaprog_core
from discorun.state import core as state_core
from discorun.state.core import Execution, InputOutputMap

import mytilus.metaprog as mytilus_metaprog
import mytilus.pcc as mytilus_pcc

from ..comput import python as comput_python
from ..comput import shell as shell_lang
from ..metaprog import python as metaprog_python
from ..metaprog import shell as metaprog_shell
from ..wire import shell as shell_wire
from .python import ProcessRunner, _run_paths


_PATHS_ATTR = "_mytilus_runtime_paths"


class SubstitutionPipeline:
    """Sequence of shell subprograms used inside command substitution."""

    def __init__(self, stages):
        self.stages = tuple(stages)


class SubstitutionParallel:
    """Parallel shell subprogram branches used inside command substitution."""

    def __init__(self, branches):
        self.branches = tuple(branches)


def _resolve_command_substitution(argument, stdin: str) -> str:
    """Evaluate one command-substitution argument."""
    if isinstance(argument, (shell_lang.Command, SubstitutionPipeline, SubstitutionParallel)):
        # Shell command substitution strips trailing newlines.
        return _compile_shell_program(argument)(stdin).rstrip("\n")
    if isinstance(argument, shell_lang.Literal):
        return argument.text
    if isinstance(argument, shell_lang.Empty):
        return ""
    if not isinstance(argument, str):
        raise TypeError(f"unsupported command argument type: {argument!r}")
    return argument


def _resolve_command_argv(argv, stdin: str) -> tuple[str, ...]:
    """Resolve a shell command argv tuple to plain subprocess arguments."""
    return tuple(_resolve_command_substitution(argument, stdin) for argument in argv)


def _resolve_terminal_passthrough_argument(argument):
    """Resolve one passthrough-safe argv item without running nested subprograms."""
    if isinstance(argument, str):
        return argument
    if isinstance(argument, shell_lang.Literal):
        return argument.text
    if isinstance(argument, shell_lang.Empty):
        return ""
    return None


def _resolve_terminal_passthrough_argv(argv):
    """Resolve argv when a top-level command can safely own the terminal."""
    resolved = tuple(_resolve_terminal_passthrough_argument(argument) for argument in argv)
    if any(argument is None for argument in resolved):
        return None
    return resolved


def parallel_io_diagram(branches):
    """Lower shell-IO branching to structural shell parallel composition."""
    branches = tuple(branches)
    if not branches:
        return shell_wire.shell_id()
    if len(branches) == 1:
        return branches[0]
    return Parallel(branches)


def _compile_shell_program(program):
    """Compile one shell program value to a Python stream transformer."""
    if isinstance(program, shell_lang.Empty):
        return lambda stdin: stdin
    if isinstance(program, shell_lang.Literal):
        return lambda _stdin: program.text
    if isinstance(program, SubstitutionPipeline):
        stage_runners = tuple(_compile_shell_program(stage) for stage in program.stages)

        def run(stdin: str) -> str:
            output = stdin
            for stage_runner in stage_runners:
                output = stage_runner(output)
            return output

        return run
    if isinstance(program, SubstitutionParallel):
        branch_runners = tuple(_compile_shell_program(branch) for branch in program.branches)

        def run(stdin: str) -> str:
            if not branch_runners:
                return stdin
            return "".join(branch_runner(stdin) for branch_runner in branch_runners)

        return run
    if isinstance(program, shell_lang.Command):

        def run(stdin: str) -> str:
            completed = subprocess.run(
                _resolve_command_argv(program.argv, stdin),
                input=stdin,
                text=True,
                capture_output=True,
                check=True,
            )
            return completed.stdout

        return run
    raise TypeError(f"unsupported shell program: {program!r}")


class ShellRuntime(metaprog_core.Interpreter):
    """Runtime functor lowering shell state diagrams through the Python runtime."""

    def __init__(self, program_functor=None, python_runtime=None):
        if program_functor is None:
            program_functor = ShellToPythonProgram()
        if python_runtime is None:
            python_runtime = ShellPythonRuntime()
        self.program_functor = program_functor
        self.python_runtime = python_runtime
        metaprog_core.Interpreter.__init__(
            self,
            dom=computer.Category(),
            cod=self.python_runtime.cod,
        )

    def _identity_object(self, ob):
        return self.python_runtime(self.program_functor(ob))

    def _identity_arrow(self, box):
        return self.python_runtime(self.program_functor(box))


def shell_program_runner(program):
    """Compile a shell program constant into a Python stream transformer."""
    if isinstance(program, (SubstitutionPipeline, SubstitutionParallel)):
        return _compile_shell_program(program)
    return ShellRuntime()(program)()[0]


class ShellToPythonProgram(state_core.ProcessSimulation):
    """Map shell programs and their evaluators to Python-program equivalents."""

    def __init__(self):
        state_core.ProcessSimulation.__init__(self)

    def simulation(self, item):
        if isinstance(item, shell_lang.ShellProgram):
            return comput_python.runtime_value_box(
                _compile_shell_program(item),
                name=item.name,
                cod=mytilus_metaprog.PYTHON_PROGRAMS.program_ty,
            )
        return mytilus_pcc.SHELL.simulate(item, mytilus_metaprog.PYTHON_PROGRAMS)

    def out(self, output):
        if mytilus_pcc.SHELL.is_evaluator(output):
            return mytilus_pcc.SHELL.simulate(output, mytilus_metaprog.PYTHON_PROGRAMS)
        return state_core.ProcessSimulation.out(self, output)


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
        if isinstance(box, Pipeline):
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
        if isinstance(box, Parallel):
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

    object_interpreter = staticmethod(comput_python.ShellPythonDataServices.object)


def terminal_passthrough_command(diagram):
    """Return the top-level command when one command can own the terminal."""
    if not isinstance(diagram, computer.Diagram):
        return None

    inside = getattr(diagram, "inside", ())
    if len(inside) != 2:
        return None

    _, command_box, _ = inside[0]
    _, output_box, _ = inside[1]

    if not isinstance(command_box, shell_lang.Command):
        return None
    if not isinstance(output_box, InputOutputMap):
        return None
    if output_box.process_name != "shell":
        return None
    if output_box.X != shell_lang.shell_program_ty:
        return None
    if output_box.A != shell_lang.io_ty or output_box.B != shell_lang.io_ty:
        return None
    if _resolve_terminal_passthrough_argv(command_box.argv) is None:
        return None

    return command_box


def run_terminal_command(program: shell_lang.Command):
    """Run one shell command attached directly to the current terminal."""
    argv = _resolve_terminal_passthrough_argv(program.argv)
    if argv is None:
        raise TypeError(f"terminal passthrough requires plain argv: {program.argv!r}")
    completed = subprocess.run(
        argv,
        check=True,
    )
    return completed.returncode


class Pipeline(metaprog_shell.Pipeline):
    """State-aware pipeline bubble."""

    def specialize(self):
        return metaprog_shell.Pipeline.specialize(self)


class Parallel(metaprog_shell.Parallel):
    """State-aware parallel bubble."""

    def specialize(self):
        return parallel_io_diagram(
            tuple(metaprog_shell.ShellSpecializer()(branch) for branch in self.branches),
        )


def pipeline(stages):
    """Build a state-aware shell pipeline bubble."""
    stages = tuple(stages)
    if not stages:
        return shell_wire.shell_id()
    return Pipeline(stages)


def parallel(branches):
    """Build a state-aware shell parallel bubble."""
    branches = tuple(branches)
    if not branches:
        return shell_wire.shell_id()
    return Parallel(branches)


class ShellSpecializer(metaprog_shell.ShellSpecializer):
    """State-aware shell bubble specializer."""

    def __init__(self):
        metaprog_shell.ShellSpecializer.__init__(self)


class ShellExecution(Execution):
    """Stateful shell evaluator P x io -> P x io."""

    def __init__(self):
        Execution.__init__(
            self,
            "shell",
            shell_lang.shell_program_ty,
            shell_lang.io_ty,
            shell_lang.io_ty,
        )
