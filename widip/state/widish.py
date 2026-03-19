"""Shell-specific stateful execution."""

import subprocess

from ..comput import widish as shell_lang
from ..metaprog import widish as metaprog_widish
from .core import Execution
from ..wire import widish as shell_wire


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
    if isinstance(program, shell_lang.Command):
        def run(stdin: str) -> str:
            completed = subprocess.run(
                program.argv,
                input=stdin,
                text=True,
                capture_output=True,
                check=True,
            )
            return completed.stdout

        return run
    raise TypeError(f"unsupported shell program: {program!r}")


class Pipeline(metaprog_widish.Pipeline):
    """State-aware pipeline bubble."""

    def specialize(self):
        return metaprog_widish.Pipeline.specialize(self)


class Parallel(metaprog_widish.Parallel):
    """State-aware parallel bubble."""

    def specialize(self):
        return parallel_io_diagram(
            tuple(metaprog_widish.ShellSpecializer()(branch) for branch in self.branches),
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


class ShellSpecializer(metaprog_widish.ShellSpecializer):
    """State-aware shell bubble specializer."""

    def __init__(self):
        metaprog_widish.ShellSpecializer.__init__(self)


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
