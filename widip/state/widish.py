"""Shell-specific stateful execution."""

from ..comput import computer
from ..comput.widish import ShellOutput, ShellStateUpdate, io_ty, shell_program_ty
from . import Execution, ProgramClosedCategory


class ShellExecution(Execution):
    """Stateful shell evaluator P x io -> P x io."""

    def __init__(self):
        Execution.__init__(
            self,
            shell_program_ty,
            io_ty,
            io_ty,
            universal_ev_diagram=computer.Computer(shell_program_ty, io_ty, shell_program_ty @ io_ty),
            state_update_diagram=ShellStateUpdate(),
            output_diagram=ShellOutput(),
        )


class ShellLanguage(ProgramClosedCategory):
    """Program-closed category with the shell as distinguished language."""

    def __init__(self):
        ProgramClosedCategory.__init__(self, shell_program_ty)

    def execution(self, A: computer.Ty, B: computer.Ty):
        del A, B
        return ShellExecution()
