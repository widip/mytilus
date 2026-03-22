from discorun.comput import computer
from discorun.state import core as state_core

from .python import ProcessRunner, _run_paths


def test_process_runner_output_projection_uses_uev():
    runner = ProcessRunner()
    output = runner.ar_map(state_core.InputOutputMap("{}", computer.ProgramTy("P"), computer.Ty("A"), computer.Ty("B")))

    assert output(lambda value: value + 1, 2) == (3,)


def test_run_paths_uses_runtime_normalization_between_stages():
    paths = ((lambda text: text.upper(), lambda text: f"{text}!"),)

    assert _run_paths(paths, "hi") == "HI!"
