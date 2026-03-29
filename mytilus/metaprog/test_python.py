from discorun.comput import computer
from discorun.metaprog import core as metaprog_core

from ..comput import python as comput_python
from .python import PythonRuntime


def test_python_runtime_exposes_top_level_pev_and_uev():
    runtime = PythonRuntime()
    specializer = runtime(metaprog_core.SpecializerBox(comput_python.program_ty))
    interpreter = runtime(metaprog_core.InterpreterBox(comput_python.program_ty))

    assert specializer() is comput_python.pev
    assert interpreter() is comput_python.uev


def test_python_runtime_combines_computations_and_data_services():
    runtime = PythonRuntime()
    evaluator = runtime(computer.Computer(comput_python.program_ty, computer.Ty("A"), computer.Ty("B")))
    residual_program = runtime(comput_python.runtime_value_box(lambda value: value + 3))

    assert evaluator(lambda value: value + 1, 2) == 3
    assert residual_program()(4) == 7
