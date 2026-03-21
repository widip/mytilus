"""Loader-language program constants."""

from . import computer


loader_program_ty = computer.ProgramTy("yaml")


class LoaderProgram(computer.Program):
    """Closed program in the YAML loader language."""

    def __init__(self, name: str):
        computer.Program.__init__(self, name, loader_program_ty, computer.Ty())


class LoaderScalarProgram(LoaderProgram):
    """Closed loader program representing YAML scalar content."""


class LoaderEmpty(LoaderScalarProgram):
    """Empty scalar in the loader language."""

    def __init__(self):
        LoaderScalarProgram.__init__(self, repr(""))


class LoaderLiteral(LoaderScalarProgram):
    """Literal scalar in the loader language."""

    def __init__(self, text: str):
        self.text = text
        LoaderScalarProgram.__init__(self, repr(text))
