"""Program-closed category with shell as distinguished language."""

from ..comput import computer
from ..comput.widish import shell_program_ty
from .core import ProgramClosedCategory


class ShellLanguage(ProgramClosedCategory):
    """Program-closed category with shell as distinguished language."""

    def __init__(self):
        ProgramClosedCategory.__init__(self, shell_program_ty)

    def execution(self, A: computer.Ty, B: computer.Ty):
        del A, B
        from ..state.widish import ShellExecution

        return ShellExecution()


SHELL = ShellLanguage()
