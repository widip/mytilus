"""Diagram tests for Sec. 6.2.2 and Futamura projections."""

from widip.comput import computer
from widip.metaprog.python import (
    PYTHON_COMPILER,
    PYTHON_COMPILER_GENERATOR,
    PYTHON_EVALUATOR_BOX,
    PYTHON_INTERPRETER,
    PYTHON_INTERPRETER_BOX,
    PYTHON_RUNTIME,
    PYTHON_SPECIALIZER,
    PYTHON_SPECIALIZER_BOX,
    compiler,
    compiler_generator,
    eq_2,
    eq_3,
    eq_4,
    eq_5,
    first_futamura_projection,
    python_object,
    sec_6_2_2_partial_application,
)


def eval_closed(diagram):
    return PYTHON_RUNTIME(diagram)()


def test_runtime_uses_functor_diagram_transforms():
    program = python_object(lambda static_input, runtime_input: static_input + runtime_input, "add")
    static_input = python_object(7, "seven")
    equation = eq_2(program, static_input)

    assert isinstance(PYTHON_SPECIALIZER, computer.Functor)
    assert isinstance(PYTHON_INTERPRETER, computer.Functor)
    assert PYTHON_SPECIALIZER_BOX.dom == computer.Ty()
    assert PYTHON_INTERPRETER_BOX.dom == computer.Ty()
    assert isinstance(PYTHON_EVALUATOR_BOX, computer.Computer)
    assert PYTHON_EVALUATOR_BOX.dom == PYTHON_SPECIALIZER_BOX.cod @ PYTHON_SPECIALIZER_BOX.cod
    assert PYTHON_RUNTIME.normalize(equation) == PYTHON_INTERPRETER(PYTHON_SPECIALIZER(equation))


def test_sec_6_2_2_partial_application():
    program = python_object(lambda static_input, runtime_input: static_input + runtime_input, "add")
    static_input = python_object(7, "seven")
    residual_from_section = sec_6_2_2_partial_application(program, static_input)
    residual_from_equation = eq_2(program, static_input)
    expected = (PYTHON_SPECIALIZER_BOX @ program >> PYTHON_EVALUATOR_BOX) @ static_input >> PYTHON_EVALUATOR_BOX

    assert residual_from_section == expected
    assert residual_from_equation == expected
    assert eval_closed(residual_from_section)(5) == 12
    assert eval_closed(residual_from_equation)(5) == 12


def test_eq_3_is_specializer_self_application():
    program = python_object(lambda static_input, runtime_input: f"{static_input}:{runtime_input}", "format")
    static_input = python_object("alpha", "alpha")
    left = eq_2(program, static_input)
    right = eq_3(program, static_input)
    expected_right = (
        ((PYTHON_SPECIALIZER_BOX @ PYTHON_SPECIALIZER_BOX >> PYTHON_EVALUATOR_BOX) @ program
         >> PYTHON_EVALUATOR_BOX) @ static_input
        >> PYTHON_EVALUATOR_BOX
    )

    assert right == expected_right
    assert eval_closed(left)("beta") == eval_closed(right)("beta")


def test_tuple_data_stays_atomic_across_universal_evaluator_wires():
    append_program = python_object(lambda xs, ys: xs + ys, "append")
    static_tuple = python_object(("a", "a", "b"), "tuple_static")
    residual_left = eval_closed(eq_2(append_program, static_tuple))
    residual_right = eval_closed(eq_3(append_program, static_tuple))

    assert residual_left(("c", "d")) == ("a", "a", "b", "c", "d")
    assert residual_left(("c", "d")) == residual_right(("c", "d"))


def test_first_projection_builds_c1_compiler():
    source_program = lambda runtime_input: runtime_input * 2 + 3
    compiler_c1 = eval_closed(first_futamura_projection(PYTHON_INTERPRETER_BOX))
    compiled_program = compiler_c1(source_program)
    compiled_from_eq_2 = eval_closed(eq_2(PYTHON_INTERPRETER_BOX, python_object(source_program, "X")))

    assert compiled_program(9) == source_program(9)
    assert compiled_program(9) == compiled_from_eq_2(9)


def test_second_projection_builds_c2_compiler():
    source_program = lambda runtime_input: runtime_input - 11
    compiler_c1 = eval_closed(first_futamura_projection(PYTHON_INTERPRETER_BOX))
    compiler_c2 = eval_closed(compiler(PYTHON_INTERPRETER_BOX))

    assert compiler_c2(source_program)(30) == source_program(30)
    assert compiler_c2(source_program)(30) == compiler_c1(source_program)(30)


def test_third_projection_builds_c3_compiler_generator():
    source_program = lambda runtime_input: runtime_input**2
    compiler_c2_from_eq_4 = eval_closed(eq_4(PYTHON_INTERPRETER_BOX))
    compiler_c2_from_eq_5 = eval_closed(eq_5(PYTHON_INTERPRETER_BOX))
    compiler_c3 = eval_closed(compiler_generator())
    expected_eq_4 = (
        (PYTHON_SPECIALIZER_BOX @ PYTHON_SPECIALIZER_BOX >> PYTHON_EVALUATOR_BOX) @ PYTHON_INTERPRETER_BOX
        >> PYTHON_EVALUATOR_BOX
    )
    interpreter = eval_closed(PYTHON_INTERPRETER_BOX)

    assert eq_4(PYTHON_INTERPRETER_BOX) == expected_eq_4
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
