from discorun.comput import computer

from ..comput import shell as shell_lang
from .shell import (
    ShellPythonRuntime,
    ShellRuntime,
    ShellToPythonProgram,
    SubstitutionParallel,
    SubstitutionPipeline,
    shell_program_runner,
)


def test_shell_runtime_lowers_shell_programs_and_evaluator_through_python_state_runtime():
    runtime = ShellRuntime()
    program_functor = ShellToPythonProgram()
    python_runtime = ShellPythonRuntime()
    source_program = shell_lang.Command(["printf", "hello"])
    source_evaluator = computer.Computer(shell_lang.shell_program_ty, shell_lang.io_ty, shell_lang.io_ty)

    residual_program = runtime(source_program)
    lowered_program = python_runtime(program_functor(source_program))
    evaluator = runtime(source_evaluator)
    lowered_evaluator = python_runtime(program_functor(source_evaluator))
    runner = residual_program()[0]
    lowered_runner = lowered_program()[0]

    assert runner("") == "hello"
    assert runner("") == lowered_runner("")
    assert evaluator(lowered_runner, "") == lowered_evaluator(lowered_runner, "")


def test_shell_program_runner_delegates_to_shell_runtime_lowering():
    runtime = ShellRuntime()
    stdin = "stdin\n"
    programs = (
        shell_lang.Empty(),
        shell_lang.Literal("literal"),
        shell_lang.Command(["printf", "command"]),
    )

    for program in programs:
        assert shell_program_runner(program)(stdin) == runtime(program)()[0](stdin)


def test_shell_program_runner_keeps_substitution_helpers_executable():
    stdin = "stdin\n"
    programs = (
        SubstitutionPipeline((shell_lang.Literal("first"), shell_lang.Literal("second"))),
        SubstitutionParallel((shell_lang.Literal("left"), shell_lang.Literal("right"))),
    )

    assert shell_program_runner(programs[0])(stdin) == "second"
    assert shell_program_runner(programs[1])(stdin) == "leftright"
