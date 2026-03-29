from discorun.metaprog import core as metaprog_core

from ..comput import python as comput_python
from ..comput import shell as shell_lang
from ..wire import partial as partial_category
from .shell import ShellPythonRuntime, ShellToPythonProgram


def test_shell_specializer_box_lowering():
    shell_specializer = metaprog_core.SpecializerBox(shell_lang.shell_program_ty, name="shell_pev")

    lowering = ShellToPythonProgram()
    lowered = lowering(shell_specializer)

    runtime = ShellPythonRuntime()
    interpreted = runtime(lowered)

    assert partial_category.is_partial_arrow(interpreted)
    specializer_fn = interpreted()

    assert callable(specializer_fn)
    assert specializer_fn is comput_python.pev


def test_shell_interpreter_box_lowering():
    shell_interpreter = metaprog_core.InterpreterBox(shell_lang.shell_program_ty, name="shell_uev")

    lowering = ShellToPythonProgram()
    lowered = lowering(shell_interpreter)

    runtime = ShellPythonRuntime()
    interpreted = runtime(lowered)

    assert partial_category.is_partial_arrow(interpreted)
    interpreter_fn = interpreted()

    assert callable(interpreter_fn)
    assert interpreter_fn is comput_python.uev
