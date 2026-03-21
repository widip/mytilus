"""
Chapter 6. Computing programs.
Metaprograms are programs that compute programs.
"""

from . import core
from . import mytilus as metaprog_mytilus


SHELL_SPECIALIZER = metaprog_mytilus.ShellSpecializer()
PROGRAM_FUNCTOR = core.ProgramFunctor()
METAPROGRAM_FUNCTOR = core.MetaprogramFunctor()
