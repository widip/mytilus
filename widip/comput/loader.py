"""Loader-language program constants."""

import shlex

from . import computer


loader_program_ty = computer.ProgramTy("yaml")


class LoaderProgram(computer.Program):
    """Closed program in the YAML loader language."""

    def __init__(self, name: str):
        computer.Program.__init__(self, name, loader_program_ty, computer.Ty())


class LoaderScalar(LoaderProgram):
    """Closed loader program representing scalar content."""

    def partial_apply(self, program: "LoaderCommand") -> "LoaderCommand":
        raise NotImplementedError


class LoaderEmpty(LoaderScalar):
    """Empty scalar in the loader language."""

    def __init__(self):
        LoaderScalar.__init__(self, repr(""))

    def partial_apply(self, program: "LoaderCommand") -> "LoaderCommand":
        return LoaderCommand(program.argv)


class LoaderLiteral(LoaderScalar):
    """Literal scalar in the loader language."""

    def __init__(self, text: str):
        self.text = text
        LoaderScalar.__init__(self, repr(text))

    def partial_apply(self, program: "LoaderCommand") -> "LoaderCommand":
        return LoaderCommand(program.argv + (self.text,))


class LoaderCommand(LoaderProgram):
    """Loader-language command program before backend interpretation."""

    def __init__(self, argv):
        self.argv = tuple(argv)
        LoaderProgram.__init__(self, shlex.join(self.argv))
