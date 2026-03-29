from functools import partial
from collections.abc import Callable

from discopy import python
from discopy.utils import tuplify, untuplify

from discorun.comput import computer
from discorun.metaprog import core as metaprog_core
from discorun.wire.services import DataServiceFunctor


program_ty = computer.ProgramTy("python")


def _apply_static_input(program, static_input, runtime_input):
    return program(
        static_input,
        untuplify(tuplify(runtime_input)),
    )


def _constant(value):
    return tuplify((value,))


def uev(function, argument):
    """DisCoPy-level universal evaluator ``{} : P x A -> B``."""
    # Standard Python function application.
    return tuplify(
        (
            untuplify(tuplify(function))(
                untuplify(tuplify(argument)),
            ),
        ),
    )


def run(function, argument):
    """Evaluate one program and return the underlying Python value."""
    return untuplify(uev(function, argument))


def runtime_values(value):
    """Normalize one runtime value under the Python-computation tuple convention."""
    return value if isinstance(value, tuple) else (value,)


def pipe(stages, *, input):
    """Run one pipeline in ``subprocess.PIPE`` style from ``input`` to final stdout."""
    stdout = input
    for stage in stages:
        stdout = run(stage, stdout)
    return stdout


def pev(program, static_input):
    """DisCoPy-level partial evaluator ``[] : P x X -> P``."""
    program = untuplify(tuplify(program))
    static_input = untuplify(tuplify(static_input))
    return tuplify((partial(_apply_static_input, program, static_input),))


def runtime_value_box(value, *, name=None, cod=None):
    """Build one closed computation box carrying a runtime value."""
    from discorun.comput import boxes as comput_boxes
    cod = program_ty if cod is None else cod
    return comput_boxes.Data(cod, value=value, name=name)


class PythonComputations(metaprog_core.Specializer, metaprog_core.Interpreter):
    """Interpret evaluators, specializers, and interpreters as Python functions."""

    def __init__(self):
        self.program_ty = program_ty
        metaprog_core.Specializer.__init__(
            self,
            dom=computer.Category(),
            cod=python.Category(),
        )

    def _identity_object(self, ob):
        # Chapter 7 status-triple wires carry actual Python data.
        if isinstance(ob, type):
            return ob
        name = getattr(ob, "name", None)
        if name in ("stdout", "stderr"):
            return str
        if name == "rc":
            return int
        if name in ("sh", "python"):
            from collections.abc import Callable
            return Callable
        return object

    def _is_evaluator_box(self, box):
        return isinstance(box, computer.Computer) or (
            getattr(box, "process_name", None) == "{}"
            and isinstance(getattr(box, "X", None), computer.ProgramTy)
            and hasattr(box, "A")
            and hasattr(box, "B")
            and getattr(box, "dom", None) == box.X @ box.A
            and getattr(box, "cod", None) == box.B
        )

    def map_computation(self, box, dom, cod):
        if self._is_evaluator_box(box):
            return python.Function(uev, dom, cod)
        return None

    def _identity_arrow(self, box):
        dom, cod = self(box.dom), self(box.cod)
        mapped = self.map_computation(box, dom, cod)
        if mapped is not None:
            return mapped
        return box

    def specialize(self, other):
        if not isinstance(other, metaprog_core.SpecializerBox):
            return metaprog_core.Specializer.specialize(self, other)
        dom, cod = self(other.dom), self(other.cod)
        if other.dom == computer.Ty() and other.cod == program_ty:
            return python.Function(lambda: pev, dom, cod)
        raise TypeError(f"unsupported Python specializer box: {other!r}")

    def interpret(self, other):
        if not isinstance(other, metaprog_core.InterpreterBox):
            return metaprog_core.Interpreter.interpret(self, other)
        dom, cod = self(other.dom), self(other.cod)
        if other.dom == computer.Ty() and other.cod == program_ty:
            return python.Function(lambda: uev, dom, cod)
        raise TypeError(f"unsupported Python interpreter box: {other!r}")


class PythonDataServices(DataServiceFunctor):
    """Interpret structural services and closed computer boxes as Python functions."""

    def __init__(self):
        DataServiceFunctor.__init__(
            self,
            dom=computer.Category(),
            cod=python.Category(),
        )

    def object(self, ob):
        # Chapter 7 status-triple wires carry actual Python data.
        if isinstance(ob, type):
            return ob
        name = getattr(ob, "name", None)
        if name in ("stdout", "stderr"):
            return str
        if name == "rc":
            return int
        if name in ("sh", "python"):
            from collections.abc import Callable
            return Callable
        return object

    def copy_ar(self, dom, cod):
        return python.Function.copy(dom, n=2)

    def delete_ar(self, dom, cod):
        return python.Function.discard(dom)

    def swap_ar(self, left, right, dom, cod):
        del dom, cod
        return python.Function.swap(left, right)

    def data_ar(self, box, dom, cod):
        if isinstance(box, computer.Box) and box.dom == computer.Ty() and hasattr(box, "value"):
            return python.Function(partial(_constant, box.value), dom, cod)
        raise TypeError(f"unsupported Python data-service box: {box!r}")


