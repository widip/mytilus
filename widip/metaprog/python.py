"""
Diagram-first Python realization of Sec. 6.2.2 and Futamura projections.

`PythonSpecializer` and `PythonInterpreter` are native metaprogram boxes
(`I -> P_python`). Equations are composed as diagrams and interpreted by a
runtime functor.
"""

from functools import partial

from discopy import monoidal, python
from discopy.utils import tuplify, untuplify

from ..comput import ProgramClosedCategory
from ..comput import computer
from ..comput import python as comput_python


PYTHON_OBJECT = comput_python.program_ty
PYTHON_PROGRAMS = ProgramClosedCategory(PYTHON_OBJECT)


def _evaluator(A, B):
    return PYTHON_PROGRAMS.evaluator(A, B)


class PythonSpecializer(computer.Box):
    """Native specializer metaprogram: ``S : I -> obj``."""

    def __init__(self):
        computer.Box.__init__(self, "S", computer.Ty(), PYTHON_OBJECT)


class PythonInterpreter(computer.Box):
    """Native interpreter metaprogram: ``H : I -> obj``."""

    def __init__(self):
        computer.Box.__init__(self, "H", computer.Ty(), PYTHON_OBJECT)


PYTHON_SPECIALIZER_BOX = PythonSpecializer()
PYTHON_INTERPRETER_BOX = PythonInterpreter()
PYTHON_EVALUATOR_BOX = _evaluator(PYTHON_OBJECT, PYTHON_OBJECT)


def _partial_evaluate(program, static_input):
    return lambda runtime_input: program(static_input, runtime_input)


def _universal_evaluate(program, runtime_input):
    return program(runtime_input)


def _apply_value(function, argument):
    function = untuplify(tuplify(function))
    argument = untuplify(tuplify(argument))
    try:
        return tuplify((function(argument), ))
    except TypeError:
        return tuplify((partial(function, argument), ))


def sec_6_2_2_partial_application(program, static_input):
    """Sec. 6.2.2 as a diagram: ``pev(X, y)``."""
    return (
        (PYTHON_SPECIALIZER_BOX @ program >> PYTHON_EVALUATOR_BOX) @ static_input
        >> _evaluator(static_input.cod, PYTHON_OBJECT)
    )


def eq_2(program, static_input):
    """Eq. (2): ``pev X y = uev S (X, y)`` (left side as native specializer box)."""
    return sec_6_2_2_partial_application(program, static_input)


def eq_3(program, static_input):
    """Eq. (3): ``uev S (X, y) = uev (pev S X) y``."""
    return (
        ((PYTHON_SPECIALIZER_BOX @ PYTHON_SPECIALIZER_BOX >> PYTHON_EVALUATOR_BOX) @ program
         >> PYTHON_EVALUATOR_BOX) @ static_input
        >> _evaluator(static_input.cod, PYTHON_OBJECT)
    )


def first_futamura_projection(interpreter):
    """`C1` as a diagram: partially evaluate the specializer on an interpreter."""
    return PYTHON_SPECIALIZER_BOX @ interpreter >> PYTHON_EVALUATOR_BOX


def eq_4(interpreter):
    """Eq. (4): ``C2 = pev S H = uev S (S, H)``."""
    return (
        (PYTHON_SPECIALIZER_BOX @ PYTHON_SPECIALIZER_BOX >> PYTHON_EVALUATOR_BOX) @ interpreter
        >> PYTHON_EVALUATOR_BOX
    )


def compiler(interpreter):
    """`C2`: second Futamura projection as a diagram."""
    return eq_4(interpreter)


def compiler_generator():
    """`C3 = pev S S`: third Futamura projection as a diagram."""
    return PYTHON_SPECIALIZER_BOX @ PYTHON_SPECIALIZER_BOX >> PYTHON_EVALUATOR_BOX


def eq_5(interpreter):
    """Eq. (5): ``uev S (S, H) = uev (pev S S) H``."""
    return compiler_generator() @ interpreter >> PYTHON_EVALUATOR_BOX


class PythonRuntime(monoidal.Functor):
    """Runtime functor from computer diagrams to executable Python functions."""

    def __init__(self):
        monoidal.Functor.__init__(
            self,
            ob=self.ob_map,
            ar=self.ar_map,
            dom=computer.Category(),
            cod=python.Category(),
        )

    @staticmethod
    def ob_map(_ob):
        return object

    def ar_map(self, box):
        dom, cod = self(box.dom), self(box.cod)
        if (
            isinstance(box, computer.Box)
            and box.dom == computer.Ty()
            and not isinstance(
                box,
                (
                    PythonSpecializer,
                    PythonInterpreter,
                    computer.Computer,
                    computer.Copy,
                    computer.Delete,
                    computer.Swap,
                ),
            )
        ):
            return python.Function(lambda value=box.value: tuplify((value, )), dom, cod)
        if isinstance(box, PythonSpecializer):
            return python.Function(lambda: _partial_evaluate, dom, cod)
        if isinstance(box, PythonInterpreter):
            return python.Function(lambda: _universal_evaluate, dom, cod)
        if isinstance(box, computer.Computer):
            return python.Function(_apply_value, dom, cod)
        if isinstance(box, computer.Copy):
            return python.Function.copy(dom, n=2)
        if isinstance(box, computer.Delete):
            return python.Function.discard(dom)
        if isinstance(box, computer.Swap):
            return python.Function.swap(self(box.left), self(box.right))
        raise TypeError(f"unsupported Python metaprogram box: {box!r}")


PYTHON_RUNTIME = PythonRuntime()
PYTHON_COMPILER = compiler(PYTHON_INTERPRETER_BOX)
PYTHON_COMPILER_GENERATOR = compiler_generator()
