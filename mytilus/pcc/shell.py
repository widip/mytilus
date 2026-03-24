"""Program-closed category with shell as distinguished language."""

from discorun.comput import computer
from discorun.pcc.core import ProgramClosedCategory

from ..comput.shell import shell_program_ty


class ShellLanguage(ProgramClosedCategory):
    """Program-closed category with shell as distinguished language."""

    def __init__(self):
        ProgramClosedCategory.__init__(self, shell_program_ty)

    def execution(self, A: computer.Ty, B: computer.Ty):
        del A, B
        from ..state.shell import ShellExecution

        return ShellExecution()
