"""
Chapter 6. Computing programs.
Metaprograms are programs that compute programs.
"""

from discorun.pcc.core import ProgramClosedCategory
from discorun.metaprog import core as metaprog_core

import mytilus.comput.python as comput_python
import mytilus.metaprog.mytilus as metaprog_mytilus
import mytilus.metaprog.python as metaprog_python


SHELL_SPECIALIZER = metaprog_mytilus.ShellSpecializer()

PYTHON_PROGRAMS = ProgramClosedCategory(comput_python.program_ty)
PYTHON_SPECIALIZER_BOX = metaprog_core.SpecializerBox(comput_python.program_ty, name="S")
PYTHON_INTERPRETER_BOX = metaprog_core.InterpreterBox(comput_python.program_ty, name="H")
PYTHON_EVALUATOR_BOX = PYTHON_PROGRAMS.evaluator(
    comput_python.program_ty,
    comput_python.program_ty,
)

PYTHON_RUNTIME = metaprog_python.PythonRuntime()
PYTHON_COMPILER = metaprog_core.compiler(
    PYTHON_INTERPRETER_BOX,
    specializer_box=PYTHON_SPECIALIZER_BOX,
    evaluator_box=PYTHON_EVALUATOR_BOX,
)
PYTHON_COMPILER_GENERATOR = metaprog_core.compiler_generator(
    specializer_box=PYTHON_SPECIALIZER_BOX,
    evaluator_box=PYTHON_EVALUATOR_BOX,
)
