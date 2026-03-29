from discopy.cat import Category as Cat
from discorun.state import core as state_core
from ..comput import python as comput_python
from ..wire import partial as partial_category


class PythonRuntime(
    state_core.ProcessRunner,
    comput_python.PythonComputations,
    comput_python.PythonDataServices,
):
    """Runtime functor from computer diagrams to executable Python functions."""

    object_interpreter = staticmethod(comput_python.PythonDataServices.object)

    def __init__(self):
        comput_python.PythonComputations.__init__(self)
        state_core.ProcessRunner.__init__(self, cod=Cat(partial_category.Ty, partial_category.PartialArrow))

    def process_ar_map(self, box, dom, cod):
        """Standard functorial interpretation via categorical composition."""
        if partial_category.is_partial_arrow(box):
            return box
        mapped = comput_python.PythonComputations.map_computation(self, box, dom, cod)
        if mapped is not None:
            return mapped
        try:
            return self.data_ar(box, dom, cod)
        except TypeError:
            pass
        raise TypeError(f"unsupported python runtime box: {box!r}")

    def object(self, ob):
        return self.object_interpreter(self, ob)

    def state_update_ar(self, dom, cod):
        return partial_category.PartialArrow(comput_python.keep_state, dom, cod)

    def output_ar(self, dom, cod):
        return partial_category.PartialArrow(comput_python.uev, dom, cod)

    def _identity_object(self, ob):
        return self.object_interpreter(self, ob)

    def _identity_arrow(self, box):
        dom, cod = self(box.dom), self(box.cod)
        # 1. Prioritize specialized processing hooks.
        try:
            return self.process_ar_map(box, dom, cod)
        except (TypeError, AttributeError):
            pass

        # 2. Fallback to standard PCC/Computation mapping.
        mapped = comput_python.PythonComputations.map_computation(self, box, dom, cod)
        if mapped is not None:
            return mapped
        return comput_python.PythonDataServices.ar_map(self, box)
