"""Diagram tests for Sec. 6.2.2 and Futamura projections."""

from discorun.comput import computer
from discorun.metaprog import core as metaprog_core
from discorun.state.core import InputOutputMap
from mytilus.comput import python as comput_python
from mytilus.metaprog import (
    PYTHON_COMPILER,
    PYTHON_COMPILER_GENERATOR,
    PYTHON_EVALUATOR_BOX,
    PYTHON_INTERPRETER_BOX,
    PYTHON_PROGRAMS,
    PYTHON_RUNTIME,
    PYTHON_SPECIALIZER_BOX,
)


def closed_value(value, name, cod=comput_python.program_ty):
    box = computer.Box(name, computer.Ty(), cod)
    box.value = value
    return box


def eval_closed(diagram):
    return PYTHON_RUNTIME(diagram)()


TEXTBOOK_PROJECTION_KW = {
    "specializer_box": PYTHON_SPECIALIZER_BOX,
    "evaluator_box": PYTHON_EVALUATOR_BOX,
}
TEXTBOOK_EQUATION_KW = {
    **TEXTBOOK_PROJECTION_KW,
    "evaluator": PYTHON_PROGRAMS.evaluator,
}


def test_runtime_evaluates_equation():
    program = closed_value(lambda static_input, runtime_input: static_input + runtime_input, "X")
    static_input = closed_value(7, "y")
    equation = metaprog_core.eq_2(program, static_input, **TEXTBOOK_EQUATION_KW)

    assert PYTHON_SPECIALIZER_BOX.dom == computer.Ty()
    assert PYTHON_INTERPRETER_BOX.dom == computer.Ty()
    assert isinstance(PYTHON_EVALUATOR_BOX, InputOutputMap)
    assert PYTHON_EVALUATOR_BOX.dom == PYTHON_SPECIALIZER_BOX.cod @ PYTHON_SPECIALIZER_BOX.cod
    assert eval_closed(equation)(5) == 12


def test_sec_6_2_2_partial_application():
    program = closed_value(lambda static_input, runtime_input: static_input + runtime_input, "X")
    static_input = closed_value(7, "y")
    residual_from_section = metaprog_core.sec_6_2_2_partial_application(
        program,
        static_input,
        **TEXTBOOK_EQUATION_KW,
    )
    residual_from_equation = metaprog_core.eq_2(program, static_input, **TEXTBOOK_EQUATION_KW)
    expected = (PYTHON_SPECIALIZER_BOX @ program >> PYTHON_EVALUATOR_BOX) @ static_input >> PYTHON_EVALUATOR_BOX

    assert residual_from_section == expected
    assert residual_from_equation == expected
    assert eval_closed(residual_from_section)(5) == 12
    assert eval_closed(residual_from_equation)(5) == 12


def test_eq_3_is_specializer_self_application():
    program = closed_value(lambda static_input, runtime_input: f"{static_input}:{runtime_input}", "X")
    static_input = closed_value("alpha", "y")
    left = metaprog_core.eq_2(program, static_input, **TEXTBOOK_EQUATION_KW)
    right = metaprog_core.eq_3(program, static_input, **TEXTBOOK_EQUATION_KW)
    expected_right = (
        ((PYTHON_SPECIALIZER_BOX @ PYTHON_SPECIALIZER_BOX >> PYTHON_EVALUATOR_BOX) @ program
         >> PYTHON_EVALUATOR_BOX) @ static_input
        >> PYTHON_EVALUATOR_BOX
    )

    assert right == expected_right
    assert eval_closed(left)("beta") == eval_closed(right)("beta")


def test_tuple_data_stays_atomic_across_universal_evaluator_wires():
    append_program = closed_value(lambda xs, ys: xs + ys, "X")
    static_tuple = closed_value(("a", "a", "b"), "y")
    residual_left = eval_closed(metaprog_core.eq_2(append_program, static_tuple, **TEXTBOOK_EQUATION_KW))
    residual_right = eval_closed(metaprog_core.eq_3(append_program, static_tuple, **TEXTBOOK_EQUATION_KW))

    assert residual_left(("c", "d")) == ("a", "a", "b", "c", "d")
    assert residual_left(("c", "d")) == residual_right(("c", "d"))


def test_first_projection_builds_c1_compiler():
    source_program = lambda runtime_input: runtime_input * 2 + 3
    compiler_c1 = eval_closed(
        metaprog_core.first_futamura_projection(PYTHON_INTERPRETER_BOX, **TEXTBOOK_PROJECTION_KW),
    )
    compiled_program = compiler_c1(source_program)
    compiled_from_eq_2 = eval_closed(
        metaprog_core.eq_2(
            PYTHON_INTERPRETER_BOX,
            closed_value(source_program, "y"),
            **TEXTBOOK_EQUATION_KW,
        ),
    )

    assert compiled_program(9) == source_program(9)
    assert compiled_program(9) == compiled_from_eq_2(9)


def test_second_projection_builds_c2_compiler():
    source_program = lambda runtime_input: runtime_input - 11
    compiler_c1 = eval_closed(
        metaprog_core.first_futamura_projection(PYTHON_INTERPRETER_BOX, **TEXTBOOK_PROJECTION_KW),
    )
    compiler_c2 = eval_closed(
        metaprog_core.compiler(PYTHON_INTERPRETER_BOX, **TEXTBOOK_PROJECTION_KW),
    )

    assert compiler_c2(source_program)(30) == source_program(30)
    assert compiler_c2(source_program)(30) == compiler_c1(source_program)(30)


def test_third_projection_builds_c3_compiler_generator():
    source_program = lambda runtime_input: runtime_input**2
    compiler_c2_from_eq_4 = eval_closed(
        metaprog_core.eq_4(PYTHON_INTERPRETER_BOX, **TEXTBOOK_PROJECTION_KW),
    )
    compiler_c2_from_eq_5 = eval_closed(
        metaprog_core.eq_5(PYTHON_INTERPRETER_BOX, **TEXTBOOK_PROJECTION_KW),
    )
    compiler_c3 = eval_closed(
        metaprog_core.compiler_generator(**TEXTBOOK_PROJECTION_KW),
    )
    expected_eq_4 = (
        (PYTHON_SPECIALIZER_BOX @ PYTHON_SPECIALIZER_BOX >> PYTHON_EVALUATOR_BOX) @ PYTHON_INTERPRETER_BOX
        >> PYTHON_EVALUATOR_BOX
    )
    interpreter = eval_closed(PYTHON_INTERPRETER_BOX)

    assert metaprog_core.eq_4(PYTHON_INTERPRETER_BOX, **TEXTBOOK_PROJECTION_KW) == expected_eq_4
    assert compiler_c2_from_eq_4(source_program)(8) == 64
    assert compiler_c2_from_eq_4(source_program)(8) == compiler_c2_from_eq_5(source_program)(8)
    assert compiler_c2_from_eq_4(source_program)(8) == compiler_c3(interpreter)(source_program)(8)


def test_exported_compiler_and_generator_constants():
    source_program = lambda runtime_input: runtime_input + 100
    compiler_value = eval_closed(PYTHON_COMPILER)
    compiler_generator_value = eval_closed(PYTHON_COMPILER_GENERATOR)
    interpreter = eval_closed(PYTHON_INTERPRETER_BOX)

    assert compiler_value(source_program)(1) == 101
    assert compiler_generator_value(interpreter)(source_program)(1) == 101


def test_sec_6_2_2_accepts_arbitrary_static_input_type():
    data_ty = computer.Ty("Data")
    program = closed_value(lambda static_input, runtime_input: f"{static_input}|{runtime_input}", "X")
    static_input = closed_value("alpha", "y", cod=data_ty)

    residual = metaprog_core.eq_2(program, static_input, **TEXTBOOK_EQUATION_KW)

    assert residual.dom == computer.Ty()
    assert residual.cod == PYTHON_EVALUATOR_BOX.cod
    assert eval_closed(residual)("beta") == "alpha|beta"
