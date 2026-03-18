"""Chapter 2 computing structures and distinguished program languages."""

from . import computer
from .loader import loader_program_ty
from .widish import shell_program_ty
from ..state.core import Execution
from ..state.loader import LoaderExecution
from ..state.widish import ShellExecution


class MonoidalComputer(computer.Category):
    """
    The ambient computer category may contain more than one program language type.
    """


class ProgramClosedCategory(MonoidalComputer):
    """
    Sec. 8.3: a program-closed category chooses one distinguished program type.
    """

    def __init__(self, program_ty: computer.ProgramTy):
        self.program_ty = program_ty
        MonoidalComputer.__init__(self)

    def evaluator(self, A: computer.Ty, B: computer.Ty):
        return computer.Computer(self.program_ty, A, B)

    def execution(self, A: computer.Ty, B: computer.Ty):
        return Execution(
            "{}",
            self.program_ty,
            A,
            B,
        )


class LoaderLanguage(ProgramClosedCategory):
    """Program-closed category for the YAML loader language."""

    def __init__(self):
        ProgramClosedCategory.__init__(self, loader_program_ty)

    def execution(self, A: computer.Ty, B: computer.Ty):
        del A, B
        return LoaderExecution()


class ShellLanguage(ProgramClosedCategory):
    """Program-closed category with the shell as distinguished language."""

    def __init__(self):
        ProgramClosedCategory.__init__(self, shell_program_ty)

    def execution(self, A: computer.Ty, B: computer.Ty):
        del A, B
        return ShellExecution()


LOADER = LoaderLanguage()
SHELL = ShellLanguage()
