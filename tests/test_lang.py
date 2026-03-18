from widip.comput import SHELL
from widip.comput.computer import Ty
from widip.comput.widish import Command, Literal, ShellProgram, io_ty, shell_program_ty
from widip.metaprog import SHELL_TO_PYTHON
from widip.metaprog.widish import Parallel, Pipeline, ShellSpecializer, parallel
from widip.state.widish import ShellExecution
from widip.wire.widish import Copy


def box_names(diagram):
    return tuple(layer[1].name for layer in diagram.inside)


def test_command_programs_have_shell_program_type():
    command = Command(["echo", "hello"])
    assert isinstance(command, ShellProgram)
    assert command.dom == Ty()
    assert command.cod == shell_program_ty


def test_commands_run_through_stateful_execution():
    execution = SHELL.execution(io_ty, io_ty).output_diagram()
    program = Command(["echo", "hello"])
    runnable = program @ io_ty >> execution
    assert runnable.dom == io_ty
    assert runnable.cod == io_ty


def test_sh_command_runs_through_shell_runner():
    execution = SHELL.execution(io_ty, io_ty).output_diagram()
    program = Command(["sh", "-c", "read line; printf 'shell:%s' \"$line\"", "sh"]) @ io_ty >> execution

    assert SHELL_TO_PYTHON(program)("world\n") == "shell:world"


def test_shell_language_chooses_shell_program_type_and_execution():
    execution = SHELL.execution(io_ty, io_ty)
    assert SHELL.program_ty == shell_program_ty
    assert isinstance(execution, ShellExecution)
    assert execution.dom == shell_program_ty @ io_ty
    assert execution.cod == shell_program_ty @ io_ty


def test_copy_has_expected_shell_types():
    assert Copy(3).dom == io_ty
    assert Copy(3).cod == io_ty @ io_ty @ io_ty


def test_parallel_helper_builds_parallel_bubble():
    execution = SHELL.execution(io_ty, io_ty).output_diagram()
    branches = (
        Literal("a") @ io_ty >> execution,
        Literal("b") @ io_ty >> execution,
        Literal("c") @ io_ty >> execution,
    )
    assert parallel(branches) == Parallel(branches)


def test_shell_bubbles_are_lowered_by_shell_specializer():
    execution = SHELL.execution(io_ty, io_ty).output_diagram()
    pipeline = Pipeline((Literal("a") @ io_ty >> execution,))
    parallel_bubble = Parallel((Literal("a") @ io_ty >> execution,))

    assert ShellSpecializer()(pipeline) == pipeline.specialize()
    assert ShellSpecializer()(parallel_bubble) == parallel_bubble.specialize()


def test_sequence_bubble_specializes_to_pipeline():
    execution = SHELL.execution(io_ty, io_ty).output_diagram()
    first = Literal("a") @ io_ty >> execution
    second = Literal("b") @ io_ty >> execution
    bubble = Pipeline((first, second))

    assert bubble.specialize() == first >> second


def test_mapping_bubble_specializes_to_primitive_command_diagram():
    execution = SHELL.execution(io_ty, io_ty).output_diagram()
    branches = (
        Literal("a") @ io_ty >> execution,
        Literal("b") @ io_ty >> execution,
        Literal("c") @ io_ty >> execution,
    )
    bubble = Parallel(branches)
    specialized = bubble.specialize()
    names = box_names(specialized)

    assert specialized.dom == io_ty
    assert specialized.cod == io_ty
    assert any(name.startswith("('tee', '/tmp/widip-") for name in names)
    assert any(name.startswith("('cat', '/tmp/widip-") for name in names)
    assert "merge[3]" not in names
    assert "∆" not in names


def test_discorun_parallel_example_runs():
    execution = SHELL.execution(io_ty, io_ty).output_diagram()
    program = Parallel(
        (
            Command(["cat"]) @ io_ty >> execution,
            Command(["grep", "-c", "x"]) @ io_ty >> execution,
            Command(["wc", "-l"]) @ io_ty >> execution,
        )
    )
    assert SHELL_TO_PYTHON(program)("a\nx\n") == "a\nx\n1\n2\n"


def test_parallel_preserves_argv_literals_without_shell_reparsing():
    execution = SHELL.execution(io_ty, io_ty).output_diagram()
    program = Parallel(
        (
            Command(["printf", "%s", "a|b"]) @ io_ty >> execution,
            Command(["printf", "%s", "c&d"]) @ io_ty >> execution,
        )
    )

    assert SHELL_TO_PYTHON(program)("") == "a|bc&d"


def test_parallel_specializer_inlines_native_command_diagram():
    execution = SHELL.execution(io_ty, io_ty).output_diagram()
    program = Parallel(
        (
            Command(["printf", "%s", "left"]) @ io_ty >> execution,
            Command(["printf", "%s", "right"]) @ io_ty >> execution,
        )
    )
    specialized = ShellSpecializer()(program)
    names = box_names(specialized)

    assert any(name.startswith("('tee', '/tmp/widip-") for name in names)
    assert any(name.startswith("('cat', '/tmp/widip-") for name in names)
    assert "merge[2]" not in names
    assert "∆" not in names
    assert SHELL_TO_PYTHON(program)("") == "leftright"


def test_stateful_shell_execution_preserves_program_state():
    program = Command(["printf", "hello"])
    runner = SHELL_TO_PYTHON(program @ io_ty >> SHELL.execution(io_ty, io_ty))
    state, output = runner("")

    assert callable(state)
    assert state("") == "hello"
    assert output == "hello"
