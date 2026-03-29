from discopy import monoidal
from discopy.cat import Category as Cat
from discorun.comput import computer
from discorun.comput import boxes as discorun_comput_boxes
from discorun.state import core as state_core
from discorun.wire import services as wire_services
from ..comput import python as comput_python
from ..metaprog import shell as shell_lang # Pipeline/Parallel are currently here
from ..wire import partial as partial_category


def _run_paths(paths, stdin):
    """Execute independent pipelines sequentially under runtime normalization."""
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
    return (value,)


class ProcessRunner(comput_python.PythonDataServices, state_core.ProcessRunner):
    """Python interpretation of generic Eq. 7.1 process projections."""

    def __init__(self):
        comput_python.PythonDataServices.__init__(self)
        state_core.ProcessRunner.__init__(self, cod=Cat(partial_category.Ty, partial_category.PartialArrow))

    def __call__(self, other):
        if isinstance(other, state_core.StateUpdateMap):
            return self.state_update_ar(self(other.dom), self(other.cod))
        if isinstance(other, state_core.InputOutputMap):
            return self.output_ar(self(other.dom), self(other.cod))
        return comput_python.PythonDataServices.__call__(self, other)

    def object(self, ob):
        # Override to ensure Python atom types.
        return comput_python.PythonDataServices.object(self, ob)

    def ar_map(self, box):
        dom, cod = self(box.dom), self(box.cod)
        shared = state_core.ProcessRunner.map_shared_ar(self, box, dom, cod)
        if shared is not None:
            return shared
        if isinstance(box, wire_services.Copy):
            return self.copy_ar(dom, cod)
        if isinstance(box, wire_services.Delete):
            return self.delete_ar(dom, cod)
        if isinstance(box, wire_services.Swap):
            return self.swap_ar(self(box.left), self(box.right), dom, cod)
        return self.process_ar_map(box, dom, cod)

    def state_update_ar(self, dom, cod):
        return partial_category.PartialArrow(lambda state, _input: state, dom, cod)

    def output_ar(self, dom, cod):
        return partial_category.PartialArrow(
            lambda state, input_value: comput_python.uev(state, input_value),
            dom,
            cod,
        )

    def process_ar_map(self, box, dom, cod):
        """Standard functorial interpretation via categorical composition."""
        if partial_category.is_partial_arrow(box):
            return box
        try:
            return self.data_ar(box, dom, cod)
        except TypeError:
            pass
        if isinstance(box, monoidal.Bubble):
            return self(box.arg)
        raise TypeError(f"unsupported process runner box: {box!r}")
