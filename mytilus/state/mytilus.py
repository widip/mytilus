"""Shell-specific stateful execution."""

import subprocess

from ..comput import computer
from ..comput import mytilus as shell_lang
from ..metaprog import mytilus as metaprog_mytilus
from .core import Execution, InputOutputMap
from ..wire import mytilus as shell_wire


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
        return shell_program_runner(argument)(stdin).rstrip("\n")
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


def shell_program_runner(program):
    """Compile a shell program constant into a Python stream transformer."""
    if isinstance(program, shell_lang.Empty):
        return lambda stdin: stdin
    if isinstance(program, shell_lang.Literal):
        return lambda _stdin: program.text
    if isinstance(program, SubstitutionPipeline):
        stage_runners = tuple(shell_program_runner(stage) for stage in program.stages)

        def run(stdin: str) -> str:
            output = stdin
            for stage_runner in stage_runners:
                output = stage_runner(output)
            return output

        return run
    if isinstance(program, SubstitutionParallel):
        branch_runners = tuple(shell_program_runner(branch) for branch in program.branches)

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


class Pipeline(metaprog_mytilus.Pipeline):
    """State-aware pipeline bubble."""

    def specialize(self):
        return metaprog_mytilus.Pipeline.specialize(self)


class Parallel(metaprog_mytilus.Parallel):
    """State-aware parallel bubble."""

    def specialize(self):
        return parallel_io_diagram(
            tuple(metaprog_mytilus.ShellSpecializer()(branch) for branch in self.branches),
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


class ShellSpecializer(metaprog_mytilus.ShellSpecializer):
    """State-aware shell bubble specializer."""

    def __init__(self):
        metaprog_mytilus.ShellSpecializer.__init__(self)


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
