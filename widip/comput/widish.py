"""Shell-language program constants."""

import shlex
import subprocess

from . import computer
from ..wire.widish import io_ty


shell_program_ty = computer.ProgramTy("sh")


class ShellProgram(computer.Program):
    """Closed shell program constant."""

    def __init__(self, name: str):
        computer.Program.__init__(self, name, shell_program_ty, computer.Ty())

    def run(self, stdin: str) -> str:
        raise NotImplementedError


class ScalarProgram(ShellProgram):
    """Closed shell program representing scalar content."""

    def partial_apply(self, program: "Command") -> "Command":
        raise NotImplementedError


class Empty(ScalarProgram):
    """Closed empty scalar program, acting as the identity on streams."""

    def __init__(self):
        ScalarProgram.__init__(self, repr(""))

    def run(self, stdin: str) -> str:
        return stdin

    def partial_apply(self, program: "Command") -> "Command":
        return Command(program.argv)


class Literal(ScalarProgram):
    """Closed literal shell program."""

    def __init__(self, text: str):
        self.text = text
        ShellProgram.__init__(self, repr(text))

    def run(self, stdin: str) -> str:
        del stdin
        return self.text

    def partial_apply(self, program: "Command") -> "Command":
        return Command(program.argv + (self.text,))


class Command(ShellProgram):
    """Closed POSIX command shell program."""

    def __init__(self, argv):
        self.argv = tuple(argv)
        ShellProgram.__init__(self, shlex.join(self.argv))

    def run(self, stdin: str) -> str:
        completed = subprocess.run(
            self.argv,
            input=stdin,
            text=True,
            capture_output=True,
            check=True,
        )
        return completed.stdout


class ShellStateUpdate(computer.Box):
    """State projection box for shell execution."""

    def __init__(self):
        computer.Box.__init__(self, "sta(shell)", shell_program_ty @ io_ty, shell_program_ty)


class ShellOutput(computer.Box):
    """Observable-output box for shell execution."""

    def __init__(self):
        computer.Box.__init__(self, "out(shell)", shell_program_ty @ io_ty, io_ty)
