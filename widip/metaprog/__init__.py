"""
Chapter 6. Computing programs.
Metaprograms are programs that compute programs.
"""

from . import core
from . import widish as metaprog_widish


SHELL_SPECIALIZER = metaprog_widish.ShellSpecializer()
PROGRAM_FUNCTOR = core.ProgramFunctor()
METAPROGRAM_FUNCTOR = core.MetaprogramFunctor()
