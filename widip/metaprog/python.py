"""
Python realization of textbook partial evaluation and Futamura projections.

References:
- `61-concept.tex`, Fig. 6.1 and surrounding text:
  metaprograms compute programs and evaluators run programs.
- `62-compilers.tex`, lines 60-131:
  Eq. (2), Eq. (3), Eq. (4), Eq. (5), and definitions of `C1`, `C2`, `C3`.

Implemented equations (same numbering as the text):
- Eq. (2): `pev X_L y = uev S_L (X, y)`.
- Eq. (3): `uev S_L (X, y) = uev (pev S_L X)_L y`.
- Eq. (4): `pev S_L H = uev S_L (S, H)`.
- Eq. (5): `uev S_L (S, H) = uev (pev S_L S)_L H`.

Section mapping:
- Sec. 6.2.2: `sec_6_2_2_partial_application`, `PYTHON_SPECIALIZER`.
- Supercompilation / Futamura projections:
  `first_futamura_projection`, `compiler` (`C2`), `compiler_generator` (`C3`).
"""

from discopy import python


def sec_6_2_2_partial_application(program, static_input):
    """Sec. 6.2.2: partial evaluation as residual-program construction."""
    return python.Function(
        inside=lambda runtime_input: program(static_input, runtime_input),
        dom=object,
        cod=object,
    )


PYTHON_SPECIALIZER = python.Function(
    inside=sec_6_2_2_partial_application,
    dom=(python.Function, object),
    cod=python.Function,
)


def eq_2(program, static_input):
    """Eq. (2): evaluate the specializer program `S` on `(X, y)`."""
    return PYTHON_SPECIALIZER(program, static_input)


def eq_3(program, static_input):
    """Eq. (3): evaluate `pev S X` on `y`."""
    return PYTHON_SPECIALIZER(PYTHON_SPECIALIZER, program)(static_input)


def high_to_low_interpreter(source_program, runtime_input):
    """`H`: interpreter that executes one source program on one runtime input."""
    return source_program(runtime_input)


PYTHON_INTERPRETER = python.Function(
    inside=high_to_low_interpreter,
    dom=(python.Function, object),
    cod=object,
)


def first_futamura_projection(interpreter):
    """`C1 = pev H`: compiler from partial evaluation of an interpreter."""
    return python.Function(
        inside=lambda source_program: eq_2(interpreter, source_program),
        dom=python.Function,
        cod=python.Function,
    )


def eq_4(interpreter):
    """Eq. (4): `C2 = pev S H = uev S (S, H)`."""
    return PYTHON_SPECIALIZER(PYTHON_SPECIALIZER, interpreter)


def compiler(interpreter):
    """`C2`: the compiler from the second Futamura projection."""
    return eq_4(interpreter)


def compiler_generator():
    """`C3 = pev S S`: the compiler generator from the third projection."""
    return PYTHON_SPECIALIZER(PYTHON_SPECIALIZER, PYTHON_SPECIALIZER)


def eq_5(interpreter):
    """Eq. (5): evaluate `C3` on `H` to obtain `C2`."""
    return compiler_generator()(interpreter)


PYTHON_COMPILER = compiler(PYTHON_INTERPRETER)
PYTHON_COMPILER_GENERATOR = compiler_generator()
