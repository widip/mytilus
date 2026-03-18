from pathlib import Path

from nx_yaml import nx_compose_all

from widip.comput import SHELL
from widip.comput.computer import Ty
from widip.comput.loader import LoaderLiteral, loader_program_ty
from widip.comput.widish import Command, Literal, io_ty, shell_program_ty
from widip.metaprog import HIF_TO_LOADER, LOADER_TO_SHELL, incidences_to_program, repl_read
from widip.metaprog.widish import Parallel, Pipeline
from widip.state import loader_output, loader_state_update
from widip.state.core import InputOutputMap, StateUpdateMap
from widip.wire.hif import HyperGraph
from widip.wire.loader import LoaderMapping, LoaderScalar, loader_stream_ty
from widip.wire.widish import shell_id


def test_loader_empty_stream_is_identity():
    assert repl_read("") == shell_id()


def test_loader_scalar_program_is_functorial():
    program = LoaderLiteral("scalar")
    compiled = LOADER_TO_SHELL(program)

    assert program.dom == Ty()
    assert program.cod == loader_program_ty
    assert compiled == Literal("scalar")


def test_loader_translation_preserves_tagged_mapping_nodes():
    graph = nx_compose_all("!echo\n? scalar\n")
    program = incidences_to_program(graph)

    assert isinstance(program, LoaderMapping)
    assert program.tag == "echo"
    assert len(program.branches) == 1


def test_loader_translation_uses_hif_metaprogram():
    graph: HyperGraph = nx_compose_all("!echo scalar")

    assert incidences_to_program(graph) == HIF_TO_LOADER(graph)


def test_loader_tagged_scalar_stays_loader_node_until_compiled():
    program = incidences_to_program(nx_compose_all("!echo scalar"))
    compiled = LOADER_TO_SHELL(program)
    execution = SHELL.execution(io_ty, io_ty).output_diagram()

    assert isinstance(program, LoaderScalar)
    assert program.cod == loader_stream_ty
    assert compiled == Command(["echo", "scalar"]) @ io_ty >> execution


def test_loader_scalar_literal():
    execution = SHELL.execution(io_ty, io_ty).output_diagram()
    assert repl_read("scalar") == Literal("scalar") @ io_ty >> execution


def test_loader_state_projections_are_transported_by_state_layer():
    assert LOADER_TO_SHELL(loader_state_update()) == StateUpdateMap("loader", shell_program_ty, io_ty)
    assert LOADER_TO_SHELL(loader_output()) == InputOutputMap("loader", shell_program_ty, io_ty, io_ty)


def test_loader_empty_scalar_is_identity():
    assert repl_read("''") == shell_id()


def test_loader_tagged_scalar_is_command():
    execution = SHELL.execution(io_ty, io_ty).output_diagram()
    assert repl_read("!echo scalar") == Command(["echo", "scalar"]) @ io_ty >> execution


def test_loader_tag_only_is_command_with_no_scalar_argument():
    execution = SHELL.execution(io_ty, io_ty).output_diagram()
    assert repl_read("!cat") == Command(["cat"]) @ io_ty >> execution


def test_loader_sequence_is_pipeline():
    execution = SHELL.execution(io_ty, io_ty).output_diagram()
    expected = (
        (Command(["grep", "grep"]) @ io_ty >> execution)
        >> (Command(["wc", "-c"]) @ io_ty >> execution)
    )
    diagram = repl_read("- !grep grep\n- !wc -c\n")
    assert isinstance(diagram, Pipeline)
    assert diagram.specialize() == expected


def test_loader_shell_case_study_is_mapping_bubble():
    execution = SHELL.execution(io_ty, io_ty).output_diagram()
    expected = Parallel(
        (
            (Command(["cat", "examples/shell.yaml"]) @ io_ty >> execution)
            >> Parallel(
                (
                    (Command(["wc", "-c"]) @ io_ty >> execution),
                    Parallel(
                        (
                            (Command(["grep", "grep"]) @ io_ty >> execution)
                            >> (Command(["wc", "-c"]) @ io_ty >> execution),
                        )
                    ),
                    (Command(["tail", "-2"]) @ io_ty >> execution),
                )
            ),
        )
    )
    diagram = repl_read(Path("examples/shell.yaml").read_text())
    assert isinstance(diagram, Parallel)
    assert diagram == expected
