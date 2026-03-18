"""Shell-specific stateful execution."""

import subprocess

from ..comput import computer
from ..comput import widish as shell_lang
from .core import Execution, InputOutputMap
from ..wire import widish as shell_wire


def shell_stage(program):
    """Run one primitive shell program on the standard shell stream."""
    return program @ shell_lang.io_ty >> InputOutputMap(
        "shell",
        shell_lang.shell_program_ty,
        shell_lang.io_ty,
        shell_lang.io_ty,
    )


def _temp_path(next_temp) -> str:
    """Allocate a deterministic temporary pathname for shell IO wiring."""
    return f"/tmp/widip-{next(next_temp):04d}.tmp"


def parallel_io_diagram(branches, next_temp):
    """Lower shell-IO branching to file-backed tee/cat process wiring."""
    branches = tuple(branches)
    if not branches:
        return shell_wire.shell_id()
    if len(branches) == 1:
        return branches[0]

    input_path = _temp_path(next_temp)
    output_paths = tuple(_temp_path(next_temp) for _ in branches)
    stages = [shell_stage(shell_lang.Command(("tee", input_path)))]

    for branch, output_path in zip(branches, output_paths):
        stages.extend(
            (
                shell_stage(shell_lang.Command(("cat", input_path))),
                branch,
                shell_stage(shell_lang.Command(("tee", output_path))),
            )
        )

    stages.append(shell_stage(shell_lang.Command(("cat",) + output_paths)))

    result = shell_wire.shell_id()
    for stage in stages:
        result = stage if result == shell_wire.shell_id() else result >> stage
    return result


def shell_program_runner(program):
    """Compile one shell-language program to a Python text transformer."""
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
