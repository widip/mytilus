"""
Tests for the Python specializer and Futamura projections.

References:
- `62-compilers.tex`, lines 60-67: Eq. (2) and Eq. (3) for the specializer.
- `62-compilers.tex`, lines 92-102: `C2 = pev S_L H` and `C3 = pev S_L S`.
- `62-compilers.tex`, lines 128-130: `C1 = uev C2` and `C2 = uev C3`.
"""

from discopy import python

from widip.metaprog.python import (
    PYTHON_COMPILER,
    PYTHON_COMPILER_GENERATOR,
    PYTHON_INTERPRETER,
    PYTHON_SPECIALIZER,
    compiler,
    compiler_generator,
    eq_2,
    eq_3,
    eq_4,
    eq_5,
    first_futamura_projection,
    sec_6_2_2_partial_application,
)


def test_sec_6_2_2_partial_application():
    program = python.Function(
        inside=lambda static_input, runtime_input: static_input + runtime_input,
        dom=(object, object),
        cod=object,
    )
    residual_from_section = sec_6_2_2_partial_application(program, 7)
    residual_from_specializer = PYTHON_SPECIALIZER(program, 7)

    assert residual_from_section(5) == 12
    assert residual_from_specializer(5) == 12


def test_eq_2_is_specializer_interpretation():
    program = python.Function(
        inside=lambda static_input, runtime_input: static_input * runtime_input + 1,
        dom=(object, object),
        cod=object,
    )
    left = eq_2(program, 4)
    right = PYTHON_SPECIALIZER(program, 4)

    assert left(6) == right(6)


def test_eq_3_is_specializer_self_application():
    program = python.Function(
        inside=lambda static_input, runtime_input: f"{static_input}:{runtime_input}",
        dom=(object, object),
        cod=object,
    )
    left = eq_2(program, "alpha")
    right = eq_3(program, "alpha")

    assert left("beta") == right("beta")


def test_first_projection_builds_c1_compiler():
    source_program = python.Function(
        inside=lambda runtime_input: runtime_input * 2 + 3,
        dom=object,
        cod=object,
    )
    compiler_c1 = first_futamura_projection(PYTHON_INTERPRETER)
    compiled_program = compiler_c1(source_program)

    assert compiled_program(9) == PYTHON_INTERPRETER(source_program, 9)


def test_second_projection_builds_c2_compiler():
    source_program = python.Function(
        inside=lambda runtime_input: runtime_input - 11,
        dom=object,
        cod=object,
    )
    compiler_c1 = first_futamura_projection(PYTHON_INTERPRETER)
    compiler_c2 = compiler(PYTHON_INTERPRETER)

    assert compiler_c2(source_program)(30) == PYTHON_INTERPRETER(source_program, 30)
    assert compiler_c2(source_program)(30) == compiler_c1(source_program)(30)


def test_third_projection_builds_c3_compiler_generator():
    source_program = python.Function(
        inside=lambda runtime_input: runtime_input**2,
        dom=object,
        cod=object,
    )
    compiler_c2_from_eq_4 = eq_4(PYTHON_INTERPRETER)
    compiler_c2_from_eq_5 = eq_5(PYTHON_INTERPRETER)
    compiler_c3 = compiler_generator()

    assert compiler_c2_from_eq_4(source_program)(8) == 64
    assert compiler_c2_from_eq_4(source_program)(8) == compiler_c2_from_eq_5(source_program)(8)
    assert compiler_c2_from_eq_4(source_program)(8) == compiler_c3(PYTHON_INTERPRETER)(source_program)(8)


def test_exported_compiler_and_generator_constants():
    source_program = python.Function(
        inside=lambda runtime_input: runtime_input + 100,
        dom=object,
        cod=object,
    )

    assert PYTHON_COMPILER(source_program)(1) == 101
    assert PYTHON_COMPILER_GENERATOR(PYTHON_INTERPRETER)(source_program)(1) == 101
