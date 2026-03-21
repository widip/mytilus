"""Program-closed category for the YAML loader language."""

from ..comput import computer
from ..comput.loader import loader_program_ty
from .core import ProgramClosedCategory


class LoaderLanguage(ProgramClosedCategory):
    """Program-closed category for the YAML loader language."""

    def __init__(self):
        ProgramClosedCategory.__init__(self, loader_program_ty)

    def execution(self, A: computer.Ty, B: computer.Ty):
        del A, B
        from ..state.loader import LoaderExecution

        return LoaderExecution()


LOADER = LoaderLanguage()
