import os
import sys
import subprocess
import logging
import re
import shlex

from discorun.comput import computer
from discorun.comput import boxes as comput_boxes
from ..wire.shell import io_ty


shell_program_ty = computer.ProgramTy("sh")


class ShellProgram(computer.Program):
    """Closed shell program constant."""

    def __init__(self, name: str):
        computer.Program.__init__(self, name, shell_program_ty, computer.Ty())


class ScalarProgram(ShellProgram):
    """Closed shell program representing scalar content."""

    def partial_apply(self, program: "Command") -> "Command":
        raise NotImplementedError


class Empty(ScalarProgram):
    """Closed empty scalar program, acting as the identity on streams."""

    def __init__(self):
        ScalarProgram.__init__(self, repr(""))

    def partial_apply(self, program: "Command") -> "Command":
        return Command(program.argv)


class Literal(comput_boxes.Data, ScalarProgram):
    """Closed literal shell program."""

    def __init__(self, text: str):
        self.text = text
        comput_boxes.Data.__init__(self, P=shell_program_ty, value=text, name=repr(text))

    def partial_apply(self, program: "Command") -> "Command":
        return Command(program.argv + (self.text,))


class Command(ShellProgram):
    """Closed POSIX command shell program data."""

    def __init__(self, argv):
        self.argv = tuple(argv)
        ShellProgram.__init__(self, repr(self.argv))


def map_argv(argv):
    """Resolve argument placeholders like (ARG 0) to actual sys.argv values."""
    for arg in argv:
        match = re.match(r"^\(ARG (\d+)\)$", arg)
        if match:
            # Shift by 2 to skip ['mytilus', 'file.yaml'] in the process argv
            i = int(match.group(1)) + 2
            yield sys.argv[i] if i < len(sys.argv) else ""
        else:
            yield arg

def subprocess_run(argv, prev_stdout, prev_rc, prev_stderr):
    """Hardened subprocess execution with status-triple propagation."""
    # Status-triple hardening: skip and propagate if previous command failed.
    if prev_rc != 0:
        return (prev_stdout, prev_rc, prev_stderr)

    argv = list(map_argv(argv))
    trace_logger = logging.getLogger("mytilus.trace")
    if os.getenv("MYTILUS_TRACE") == "1":
        trace_logger.info(f"+ {shlex.join(argv)}")

    completed = subprocess.run(
        argv,
        input=prev_stdout,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0 and os.getenv("MYTILUS_TRACE") == "1":
        trace_logger.info(f"  (exit {completed.returncode})")
    return (completed.stdout, completed.returncode, prev_stderr + completed.stderr)
