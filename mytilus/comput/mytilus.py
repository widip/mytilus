"""Shell-language program constants."""

from . import computer
from ..wire.mytilus import io_ty


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


class Literal(ScalarProgram):
    """Closed literal shell program."""

    def __init__(self, text: str):
        self.text = text
        ShellProgram.__init__(self, repr(text))

    def partial_apply(self, program: "Command") -> "Command":
        return Command(program.argv + (self.text,))


class Command(ShellProgram):
    """Closed POSIX command shell program data."""

    def __init__(self, argv):
        self.argv = tuple(argv)
        ShellProgram.__init__(self, repr(self.argv))
