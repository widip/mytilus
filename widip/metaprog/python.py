"""
Diagram-first Python realization of Sec. 6.2.2 and Futamura projections.

`PythonSpecializer` and `PythonInterpreter` are native metaprogram boxes
(`I -> P_python`). Equations are composed as diagrams and interpreted by a
runtime functor.
"""

from functools import partial

from discopy import monoidal, python
from discopy.utils import tuplify, untuplify

from ..comput import computer
from ..comput import python as comput_python


PYTHON_OBJECT = comput_python.program_ty


def _pack_value(value):
    return tuplify((value, ))


def _unpack_value(value):
    return untuplify(tuplify(value))


def _value_name(value) -> str:
    if isinstance(value, str):
        return repr(value)
    if callable(value):
        return getattr(value, "__name__", type(value).__name__)
    return str(value)


class PythonObject(computer.Box):
    """Closed Python object constant encoded on one object wire."""

    def __init__(self, value, name=None):
        self.value = value
        computer.Box.__init__(self, _value_name(value) if name is None else name, computer.Ty(), PYTHON_OBJECT)


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
PYTHON_EVALUATOR_BOX = computer.Computer(PYTHON_OBJECT, PYTHON_OBJECT, PYTHON_OBJECT)


class PythonSpecializerFunctor(computer.Functor):
    """Diagram pass that normalizes occurrences of native specializer boxes."""

    def __init__(self):
        computer.Functor.__init__(
            self,
            ob=lambda ob: ob,
            ar=self.ar_map,
            dom=computer.Category(),
            cod=computer.Category(),
        )

    @staticmethod
    def ar_map(ar):
        if isinstance(ar, PythonSpecializer):
            return PythonSpecializer()
        return ar


class PythonInterpreterFunctor(computer.Functor):
    """Diagram pass that normalizes occurrences of native interpreter boxes."""

    def __init__(self):
        computer.Functor.__init__(
            self,
            ob=lambda ob: ob,
            ar=self.ar_map,
            dom=computer.Category(),
            cod=computer.Category(),
        )

    @staticmethod
    def ar_map(ar):
        if isinstance(ar, PythonInterpreter):
            return PythonInterpreter()
        return ar


PYTHON_SPECIALIZER = PythonSpecializerFunctor()
PYTHON_INTERPRETER = PythonInterpreterFunctor()


def _partial_evaluate(program, static_input):
    return lambda runtime_input: program(static_input, runtime_input)


def _universal_evaluate(program, runtime_input):
    return program(runtime_input)


def _apply_value(function, argument):
    function = _unpack_value(function)
    argument = _unpack_value(argument)
    try:
        return _pack_value(function(argument))
    except TypeError:
        return _pack_value(partial(function, argument))


def python_object(value, name=None):
    """Encode a closed Python value as a unit-to-object diagram."""
    return PythonObject(value, name=name)


def _as_closed_object(value, default_name):
    if isinstance(value, computer.Diagram):
        if value.dom != computer.Ty() or value.cod != PYTHON_OBJECT:
            raise TypeError(f"expected closed object diagram I->obj, got {value.dom}->{value.cod}")
        return value
    return python_object(value, default_name)


def sec_6_2_2_partial_application(program, static_input):
    """Sec. 6.2.2 as a diagram: ``pev(X, y)``."""
    program = _as_closed_object(program, "X")
    static_input = _as_closed_object(static_input, "y")
    return (
        (PYTHON_SPECIALIZER_BOX @ program >> PYTHON_EVALUATOR_BOX) @ static_input
        >> PYTHON_EVALUATOR_BOX
    )


def eq_2(program, static_input):
    """Eq. (2): ``pev X y = uev S (X, y)`` (left side as native specializer box)."""
    return sec_6_2_2_partial_application(program, static_input)


def eq_3(program, static_input):
    """Eq. (3): ``uev S (X, y) = uev (pev S X) y``."""
    program = _as_closed_object(program, "X")
    static_input = _as_closed_object(static_input, "y")
    return (
        ((PYTHON_SPECIALIZER_BOX @ PYTHON_SPECIALIZER_BOX >> PYTHON_EVALUATOR_BOX) @ program
         >> PYTHON_EVALUATOR_BOX) @ static_input
        >> PYTHON_EVALUATOR_BOX
    )


def first_futamura_projection(interpreter):
    """`C1` as a diagram: partially evaluate the specializer on an interpreter."""
    interpreter = _as_closed_object(interpreter, "H")
    return PYTHON_SPECIALIZER_BOX @ interpreter >> PYTHON_EVALUATOR_BOX


def eq_4(interpreter):
    """Eq. (4): ``C2 = pev S H = uev S (S, H)``."""
    interpreter = _as_closed_object(interpreter, "H")
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
    interpreter = _as_closed_object(interpreter, "H")
    return compiler_generator() @ interpreter >> PYTHON_EVALUATOR_BOX


class PythonRuntime(monoidal.Functor):
    """Runtime functor from computer diagrams to executable Python functions."""

    def __init__(self, *diagram_transforms):
        self.diagram_transforms = diagram_transforms or (PYTHON_SPECIALIZER, PYTHON_INTERPRETER)
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

    def normalize(self, diagram):
        if not isinstance(diagram, computer.Diagram):
            return diagram
        for transform in self.diagram_transforms:
            diagram = transform(diagram)
        return diagram

    def __call__(self, other):
        if isinstance(other, computer.Diagram):
            other = self.normalize(other)
        return monoidal.Functor.__call__(self, other)

    def ar_map(self, box):
        dom, cod = self(box.dom), self(box.cod)
        if isinstance(box, PythonObject):
            return python.Function(lambda: _pack_value(box.value), dom, cod)
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


PYTHON_RUNTIME = PythonRuntime(PYTHON_SPECIALIZER, PYTHON_INTERPRETER)
PYTHON_COMPILER = compiler(PYTHON_INTERPRETER_BOX)
PYTHON_COMPILER_GENERATOR = compiler_generator()
