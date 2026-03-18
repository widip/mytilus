"""
Diagram-first Python realization of metaprogram specialization and runtime.
"""

from functools import partial

from discopy import python
from discopy.utils import tuplify, untuplify

from ..comput import ProgramClosedCategory
from ..comput import computer
from ..comput import python as comput_python
from . import core as metaprog_core


PYTHON_OBJECT = comput_python.program_ty
PYTHON_PROGRAMS = ProgramClosedCategory(PYTHON_OBJECT)


def _evaluator(A, B):
    return PYTHON_PROGRAMS.evaluator(A, B)


class PythonSpecializer(metaprog_core.SpecializerBox):
    """Native specializer metaprogram: ``S : I -> obj``."""

    def __init__(self):
        metaprog_core.SpecializerBox.__init__(self, PYTHON_OBJECT, name="S")


class PythonInterpreter(metaprog_core.InterpreterBox):
    """Native interpreter metaprogram: ``H : I -> obj``."""

    def __init__(self):
        metaprog_core.InterpreterBox.__init__(self, PYTHON_OBJECT, name="H")


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


def apply_value(function, argument):
    """Public evaluator application helper shared by runtime interpreters."""
    return _apply_value(function, argument)


sec_6_2_2_partial_application = partial(
    metaprog_core.sec_6_2_2_partial_application,
    specializer_box=PYTHON_SPECIALIZER_BOX,
    evaluator_box=PYTHON_EVALUATOR_BOX,
    evaluator=_evaluator,
)

eq_2 = partial(
    metaprog_core.eq_2,
    specializer_box=PYTHON_SPECIALIZER_BOX,
    evaluator_box=PYTHON_EVALUATOR_BOX,
    evaluator=_evaluator,
)

eq_3 = partial(
    metaprog_core.eq_3,
    specializer_box=PYTHON_SPECIALIZER_BOX,
    evaluator_box=PYTHON_EVALUATOR_BOX,
    evaluator=_evaluator,
)

first_futamura_projection = partial(
    metaprog_core.first_futamura_projection,
    specializer_box=PYTHON_SPECIALIZER_BOX,
    evaluator_box=PYTHON_EVALUATOR_BOX,
)

eq_4 = partial(
    metaprog_core.eq_4,
    specializer_box=PYTHON_SPECIALIZER_BOX,
    evaluator_box=PYTHON_EVALUATOR_BOX,
)

compiler = partial(
    metaprog_core.compiler,
    specializer_box=PYTHON_SPECIALIZER_BOX,
    evaluator_box=PYTHON_EVALUATOR_BOX,
)

compiler_generator = partial(
    metaprog_core.compiler_generator,
    specializer_box=PYTHON_SPECIALIZER_BOX,
    evaluator_box=PYTHON_EVALUATOR_BOX,
)

eq_5 = partial(
    metaprog_core.eq_5,
    specializer_box=PYTHON_SPECIALIZER_BOX,
    evaluator_box=PYTHON_EVALUATOR_BOX,
)


class PythonRuntime(metaprog_core.Interpreter):
    """Runtime functor from computer diagrams to executable Python functions."""

    def __init__(self):
        metaprog_core.Interpreter.__init__(
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
            return python.Function(apply_value, dom, cod)
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
