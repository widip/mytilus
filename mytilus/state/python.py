"""Python-side runtime helpers for stateful interpreters."""

from discopy import python

from discorun.comput import computer
from discorun.state import core as state_core

from ..comput import python as comput_python


def _run_paths(paths, stdin):
    """Execute all independent pipelines sequentially and concatenate outputs."""
    outputs = []
    for path in paths:
        output = stdin
        for stage in path:
            output = comput_python.run(stage, output)
        outputs.append(output)
    if not outputs:
        return stdin
    if len(outputs) == 1:
        return outputs[0]
    return "".join(outputs)


def runtime_values(value):
    """Normalize interpreter output values under the runtime tuple convention."""
    return comput_python.runtime_values(value)


class ProcessRunner(state_core.ProcessRunner):
    """Python interpretation of generic Eq. 7.1 process projections."""

    def __init__(self, data_services=None):
        self.data_services = comput_python.ShellPythonDataServices() if data_services is None else data_services
        state_core.ProcessRunner.__init__(self, cod=python.Category())

    def object(self, ob):
        del ob
        return object

    def state_update_ar(self, dom, cod):
        return python.Function(lambda state, _input: state, dom, cod)

    def output_ar(self, dom, cod):
        return python.Function(lambda state, input_value: comput_python.uev(state, input_value), dom, cod)

    def map_structural(self, box, dom, cod):
        del dom, cod
        if not isinstance(box, (computer.Copy, computer.Delete, computer.Swap)):
            return None
        return self.data_services(box)
