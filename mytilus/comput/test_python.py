import pytest

from discorun.comput import computer
from discorun.metaprog import core as metaprog_core

from . import python as comput_python


def test_uev_keeps_tuple_outputs_atomic():
    result = comput_python.uev(lambda xs: xs + ("c",), ("a", "b"))

    assert result == (("a", "b", "c"),)


def test_run_unwraps_one_uev_result_for_runtime_use():
    result = comput_python.run(lambda xs: xs + ("c",), ("a", "b"))

    assert result == ("a", "b", "c")


def test_runtime_values_reuses_python_tuple_convention():
    assert comput_python.runtime_values("x") == ("x",)
    assert comput_python.runtime_values(("x",)) == ("x",)
    assert comput_python.runtime_values(("a", "b")) == ("a", "b")


def test_pev_returns_tuple_wrapped_residual_program():
    residual, = comput_python.pev(lambda static_input, runtime_input: static_input + runtime_input, 7)

    assert residual(5) == 12


def test_python_computations_interpret_evaluator_specializer_and_interpreter_boxes():
    computations = comput_python.PythonComputations()
    evaluator = computations(computer.Computer(comput_python.program_ty, computer.Ty("A"), computer.Ty("B")))
    specializer = computations(metaprog_core.SpecializerBox(comput_python.program_ty))
    interpreter = computations(metaprog_core.InterpreterBox(comput_python.program_ty))

    assert evaluator(lambda value: value + 1, 2) == (3,)
    assert specializer() is comput_python.pev
    assert specializer()(lambda x, y: x + y, 7)[0](5) == 12
    assert interpreter() is comput_python.uev
    assert interpreter()(lambda value: value + 1, 2) == (3,)


def test_python_data_services_do_not_interpret_evaluator_boxes():
    data_services = comput_python.PythonDataServices()

    with pytest.raises(TypeError):
        data_services(computer.Computer(comput_python.program_ty, computer.Ty("A"), computer.Ty("B")))
