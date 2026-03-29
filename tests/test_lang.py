from discorun.comput.computer import Ty
from mytilus.comput import python as comput_python
from mytilus.comput.shell import Command, Empty, Literal, ShellProgram, io_ty, shell_program_ty
import mytilus.metaprog as mytilus_metaprog
from mytilus.metaprog import python as metaprog_python
from mytilus.pcc import SHELL
from discorun.state import core as state_core
from mytilus.state import SHELL_INTERPRETER, SHELL_PROGRAM_TO_PYTHON
from mytilus.metaprog.shell import (
    Parallel,
    Pipeline,
)
from mytilus.state.shell import (
    ShellExecution,
    ShellSpecializer,
    parallel,
    shell_program_runner,
)
from mytilus.wire.shell import Copy


def box_names(diagram):
    """Recursively extract box and bubble names for diagram inspection."""
    if hasattr(diagram, "boxes"):
        names = []
        for layer in diagram.inside:
            box = layer[1]
            names.append(box.name)
            if hasattr(box, "inside"):
                 # Recurse into bubble if it hasn't been lowered yet.
                 if hasattr(box, "arg"):
                     names.extend(box_names(box.arg))
        return tuple(names)
    if hasattr(diagram, "arg"):
        return box_names(diagram.arg)
        return (diagram.name,) + box_names(diagram.arg)
    return (getattr(diagram, "name", ""),)


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

    assert SHELL_INTERPRETER(program)("world\n") == ("shell:world", 0, "")


def test_tagged_mapping_style_command_substitution_runs_in_argv():
    execution = SHELL.execution(io_ty, io_ty).output_diagram()
    program = Command(["echo", "Hello", "World", Command(["echo", "Foo"]), "!"]) @ io_ty >> execution

    assert SHELL_INTERPRETER(program)("") == ("Hello World Foo !\n", 0, "")


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

    # Specialized bubbles may be diagrams or bubbles depending on the runtime.
    # We check they have matching domains and codomains and interpretation.
    s_pipeline = ShellSpecializer()(pipeline)
    s_bubble = ShellSpecializer()(parallel_bubble)
    assert s_pipeline.dom == pipeline.dom and s_pipeline.cod == pipeline.cod
    assert s_bubble.dom == parallel_bubble.dom and s_bubble.cod == parallel_bubble.cod
    assert SHELL_INTERPRETER(s_pipeline)("") == SHELL_INTERPRETER(pipeline)("")
    assert SHELL_INTERPRETER(s_bubble)("") == SHELL_INTERPRETER(parallel_bubble)("")


def test_sequence_bubble_specializes_to_pipeline():
    execution = SHELL.execution(io_ty, io_ty).output_diagram()
    first = Literal("a") @ io_ty >> execution
    second = Literal("b") @ io_ty >> execution
    bubble = Pipeline((first, second))

    assert bubble.specialize() == first >> second


def test_mapping_bubble_specializes_to_parallel_shell_bubble():
    execution = SHELL.execution(io_ty, io_ty).output_diagram()
    branches = (
        Literal("a") @ io_ty >> execution,
        Literal("b") @ io_ty >> execution,
        Literal("c") @ io_ty >> execution,
    )
    bubble = Parallel(branches)
    specialized = bubble.specialize()
    names = box_names(specialized)

    assert isinstance(specialized, Parallel)
    assert specialized.dom == io_ty
    assert specialized.cod == io_ty
    assert not any(name.startswith("('tee',") for name in names)
    print(f"DEBUG SPEC: {specialized}")
    print(f"DEBUG NAMES: {names}")
    assert not any(name.startswith("('cat', '/tmp/mytilus-") for name in names)
    assert any(name.startswith("Merge(") or "Merge" in name for name in names)
    assert any(name.startswith("Copy(") or "∆" in name or "Copy(" in name for name in names)
    assert SHELL_INTERPRETER(bubble)("") == ("abc", 0, "")


def test_discorun_parallel_example_runs():
    execution = SHELL.execution(io_ty, io_ty).output_diagram()
    program = Parallel(
        (
            Command(["cat"]) @ io_ty >> execution,
            Command(["grep", "-c", "x"]) @ io_ty >> execution,
            Command(["wc", "-l"]) @ io_ty >> execution,
        )
    )
    assert SHELL_INTERPRETER(program)("a\nx\n") == ("a\nx\n1\n2\n", 0, "")


def test_pipeline_copy_replays_prefix_command_per_parallel_branch(tmp_path):
    execution = SHELL.execution(io_ty, io_ty).output_diagram()
    counter = tmp_path / "counter.txt"
    counter.write_text("0")
    increment_script = (
        "data=$(cat); "
        "count=$(cat \"$1\"); "
        "count=$((count+1)); "
        "printf '%s' \"$count\" > \"$1\"; "
        "printf '%s' \"$data\""
    )
    prefix = Command(["sh", "-c", increment_script, "sh", str(counter)]) @ io_ty >> execution
    program = Pipeline(
        (
            prefix,
            Parallel(
                (
                    Command(["cat"]) @ io_ty >> execution,
                    Command(["cat"]) @ io_ty >> execution,
                )
            ),
        )
    )

    assert SHELL_INTERPRETER(program)("hello") == ("hellohello", 0, "")
    assert counter.read_text() == "1"


def test_parallel_preserves_argv_literals_without_shell_reparsing():
    execution = SHELL.execution(io_ty, io_ty).output_diagram()
    program = Parallel(
        (
            Command(["printf", "%s", "a|b"]) @ io_ty >> execution,
            Command(["printf", "%s", "c&d"]) @ io_ty >> execution,
        )
    )

    assert SHELL_INTERPRETER(program)("") == ("a|bc&d", 0, "")


def test_parallel_specializer_preserves_parallel_shell_bubble():
    execution = SHELL.execution(io_ty, io_ty).output_diagram()
    program = Parallel(
        (
            Command(["printf", "%s", "left"]) @ io_ty >> execution,
            Command(["printf", "%s", "right"]) @ io_ty >> execution,
        )
    )
    specialized = ShellSpecializer()(program)
    names = box_names(specialized)

    assert isinstance(specialized, Parallel)
    assert not any(name.startswith("('tee',") for name in names)
    assert not any(name.startswith("('cat', '/tmp/mytilus-") for name in names)
    # Modernized architecture lowers to Parallel blocks containing Copy/Merge nodes.
    assert "∆" in names or any("Merge" in n for n in names)
    assert SHELL_INTERPRETER(program)("") == ("leftright", 0, "")


def test_stateful_shell_execution_preserves_program_state():
    program = Command(["printf", "hello"])
    runner = SHELL_INTERPRETER(program @ io_ty >> SHELL.execution(io_ty, io_ty))
    state, output = runner("")

    assert callable(state)
    assert state("") == ("hello", 0, "")
    assert output == ("hello", 0, "")


def test_shell_to_python_program_maps_shell_scalars_to_python_program_boxes():
    transform = SHELL_PROGRAM_TO_PYTHON
    source_boxes = (Empty(), Literal("literal"), Command(["printf", "x"]))

    for source in source_boxes:
        mapped = transform(source)
        assert mapped.dom == Ty()
        assert mapped.cod == comput_python.program_ty
        actual_fn = mapped.boxes[0].value
        assert actual_fn("stdin\n", 0, "") == shell_program_runner(source).term("stdin\n", 0, "")


def test_shell_to_python_program_maps_shell_evaluator_box():
    transform = SHELL_PROGRAM_TO_PYTHON
    evaluator = SHELL.evaluator(io_ty, io_ty)

    mapped = transform(evaluator)

    assert mapped == mytilus_metaprog.PYTHON_PROGRAMS.evaluator(io_ty, io_ty)


def test_shell_to_python_program_maps_process_projection_boxes():
    transform = SHELL_PROGRAM_TO_PYTHON
    state_update = state_core.StateUpdateMap("shell", shell_program_ty, io_ty)
    output = state_core.InputOutputMap("shell", shell_program_ty, io_ty, io_ty)

    mapped_state_update = transform(state_update)
    mapped_output = transform(output)

    assert mapped_state_update.X == comput_python.program_ty
    assert mapped_state_update.A == io_ty
    assert mapped_output.X == comput_python.program_ty
    assert mapped_output.A == io_ty
    assert mapped_output.B == io_ty
