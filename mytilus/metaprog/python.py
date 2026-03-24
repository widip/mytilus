"""Diagram-first Python realization of metaprogram specialization and runtime."""

from ..comput import python as comput_python


class PythonRuntime(
    comput_python.PythonComputations,
    comput_python.PythonDataServices,
):
    """Runtime functor from computer diagrams to executable Python functions."""

    object_interpreter = staticmethod(comput_python.PythonDataServices.object)

    def __init__(self):
        comput_python.PythonComputations.__init__(self)

    def _identity_object(self, ob):
        return self.object_interpreter(self, ob)

    def _identity_arrow(self, box):
        dom, cod = self(box.dom), self(box.cod)
        mapped = comput_python.PythonComputations.map_computation(self, box, dom, cod)
        if mapped is not None:
            return mapped
        return comput_python.PythonDataServices.ar_map(self, box)
