"""
Chapter 6. Computing programs.
Metaprograms are programs that compute programs.
"""

from . import core
from . import widish as metaprog_widish


SHELL_SPECIALIZER = metaprog_widish.ShellSpecializer()
SHELL_INTERPRETER = metaprog_widish.ShellInterpreter(SHELL_SPECIALIZER)
SHELL_TO_PYTHON = SHELL_INTERPRETER
PROGRAM_FUNCTOR = core.ProgramFunctor()
METAPROGRAM_FUNCTOR = core.MetaprogramFunctor()
