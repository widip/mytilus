from functools import partial

import pytest

from discorun.comput import computer
from discorun.metaprog import core as metaprog_core

from . import python as comput_python


def assert_partial_ast_equal(actual, expected):
    assert isinstance(actual, partial)
    assert isinstance(expected, partial)
    assert actual.func is expected.func
    assert actual.keywords == expected.keywords
    assert len(actual.args) == len(expected.args)
    for actual_arg, expected_arg in zip(actual.args, expected.args):
        if isinstance(expected_arg, partial):
            assert_partial_ast_equal(actual_arg, expected_arg)
            continue
        assert actual_arg is expected_arg if callable(expected_arg) else actual_arg == expected_arg


def test_uev_keeps_tuple_outputs_atomic():
    result = comput_python.uev(lambda xs: xs + ("c",), ("a", "b"))

    assert result == ("a", "b", "c")


def test_run_unwraps_one_uev_result_for_runtime_use():
    result = comput_python.run(lambda xs: xs + ("c",), ("a", "b"))

    assert result == ("a", "b", "c")


def test_runtime_values_reuses_python_tuple_convention():
    assert comput_python.runtime_values("x") == ("x",)
    assert comput_python.runtime_values(("x",)) == ("x",)
    assert comput_python.runtime_values(("a", "b")) == ("a", "b")


def test_pev_returns_residual_partial_program():
    program = lambda static_input, runtime_input: static_input + runtime_input
    residual = comput_python.pev(program, 7)
    expected = partial(comput_python.apply_static_input, program, 7)

    assert_partial_ast_equal(residual, expected)
    assert residual(5) == 12


def test_python_computations_interpret_evaluator_specializer_and_interpreter_boxes():
    computations = comput_python.PythonComputations()
    evaluator = computations(computer.Computer(comput_python.program_ty, computer.Ty("A"), computer.Ty("B")))
    specializer = computations(metaprog_core.SpecializerBox(comput_python.program_ty))
    interpreter = computations(metaprog_core.InterpreterBox(comput_python.program_ty))
    expected_specializer = partial(comput_python.constant, comput_python.pev)
    expected_interpreter = partial(comput_python.constant, comput_python.uev)

    assert evaluator(lambda value: value + 1, 2) == 3
    assert_partial_ast_equal(specializer.term, expected_specializer)
    assert specializer() is comput_python.pev
    assert specializer()(lambda x, y: x + y, 7)(5) == 12
    assert_partial_ast_equal(interpreter.term, expected_interpreter)
    assert interpreter() is comput_python.uev
    assert interpreter()(lambda value: value + 1, 2) == 3


def test_python_data_services_do_not_interpret_evaluator_boxes():
    data_services = comput_python.PythonDataServices()

    with pytest.raises(TypeError):
        data_services(computer.Computer(comput_python.program_ty, computer.Ty("A"), computer.Ty("B")))
