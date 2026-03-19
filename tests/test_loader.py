from pathlib import Path

from nx_yaml import nx_compose_all

from widip.comput.computer import Ty
from widip.comput.loader import LoaderLiteral, loader_program_ty
from widip.comput.widish import Command, Literal, io_ty, shell_program_ty
from widip.metaprog.hif import HIFToLoader
from widip.pcc import SHELL
from widip.state.core import InputOutputMap, StateUpdateMap
from widip.state.loader import LoaderExecution, LoaderToShell
from widip.state.widish import Parallel, Pipeline
from widip.wire.hif import HyperGraph
from widip.wire.loader import LoaderMapping, LoaderScalar, LoaderSequence, loader_stream_ty
from widip.wire.widish import shell_id


def test_loader_empty_stream_is_identity():
    assert LoaderToShell()(HIFToLoader()(nx_compose_all(""))) == shell_id()


def test_loader_scalar_program_is_functorial():
    program = LoaderLiteral("scalar")
    compiled = LoaderToShell()(program)

    assert program.dom == Ty()
    assert program.cod == loader_program_ty
    assert compiled == Literal("scalar")


def test_loader_translation_flattens_tagged_scalar_mapping_into_argv():
    graph = nx_compose_all("!echo\n? scalar\n")
    program = HIFToLoader()(graph)

    assert isinstance(program, LoaderScalar)
    assert program.tag == "echo"
    assert program.value == ("scalar",)


def test_loader_translation_uses_hif_metaprogram():
    graph: HyperGraph = nx_compose_all("!echo scalar")

    assert HIFToLoader().specialize(graph) == HIFToLoader()(graph)


def test_loader_tagged_scalar_stays_loader_node_until_compiled():
    program = HIFToLoader()(nx_compose_all("!echo scalar"))
    compiled = LoaderToShell()(program)
    execution = SHELL.execution(io_ty, io_ty).output_diagram()

    assert isinstance(program, LoaderScalar)
    assert program.cod == loader_stream_ty
    assert compiled == Command(["echo", "scalar"]) @ io_ty >> execution


def test_loader_scalar_literal():
    execution = SHELL.execution(io_ty, io_ty).output_diagram()
    assert LoaderToShell()(HIFToLoader()(nx_compose_all("scalar"))) == Literal("scalar") @ io_ty >> execution


def test_loader_state_projections_are_reparametrized_by_state_functor():
    execution = LoaderExecution()
    assert LoaderToShell()(execution.state_update_diagram()) == StateUpdateMap("loader", shell_program_ty, io_ty)
    assert LoaderToShell()(execution.output_diagram()) == InputOutputMap("loader", shell_program_ty, io_ty, io_ty)


def test_loader_empty_scalar_is_identity():
    assert LoaderToShell()(HIFToLoader()(nx_compose_all("''"))) == shell_id()


def test_loader_tagged_scalar_is_command():
    execution = SHELL.execution(io_ty, io_ty).output_diagram()
    assert LoaderToShell()(HIFToLoader()(nx_compose_all("!echo scalar"))) == Command(["echo", "scalar"]) @ io_ty >> execution


def test_loader_tag_only_is_command_with_no_scalar_argument():
    execution = SHELL.execution(io_ty, io_ty).output_diagram()
    assert LoaderToShell()(HIFToLoader()(nx_compose_all("!cat"))) == Command(["cat"]) @ io_ty >> execution


def test_loader_sequence_is_pipeline():
    execution = SHELL.execution(io_ty, io_ty).output_diagram()
    expected = (
        (Command(["grep", "grep"]) @ io_ty >> execution)
        >> (Command(["wc", "-c"]) @ io_ty >> execution)
    )
    diagram = LoaderToShell()(HIFToLoader()(nx_compose_all("- !grep grep\n- !wc -c\n")))
    assert isinstance(diagram, Pipeline)
    assert diagram.specialize() == expected


def test_loader_tagged_sequence_compiles_like_untagged_sequence():
    tagged_program = HIFToLoader()(nx_compose_all("!echo\n- foo\n- bar\n"))
    untagged_program = LoaderSequence(tagged_program.stages)

    assert isinstance(tagged_program, LoaderSequence)
    assert tagged_program.tag == "echo"
    assert LoaderToShell()(tagged_program) == LoaderToShell()(untagged_program)


def test_loader_tagged_mapping_of_scalars_is_command():
    execution = SHELL.execution(io_ty, io_ty).output_diagram()
    tagged_program = HIFToLoader()(nx_compose_all("!echo\n? foo\n? bar\n"))

    assert isinstance(tagged_program, LoaderScalar)
    assert tagged_program.tag == "echo"
    assert tagged_program.value == ("foo", "bar")
    assert LoaderToShell()(tagged_program) == Command(["echo", "foo", "bar"]) @ io_ty >> execution


def test_loader_tagged_mapping_with_non_scalar_value_stays_mapping():
    tagged_program = HIFToLoader()(nx_compose_all("!echo\n? foo: !wc -c\n"))

    assert isinstance(tagged_program, LoaderMapping)
    assert tagged_program.tag == "echo"


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
    diagram = LoaderToShell()(HIFToLoader()(nx_compose_all(Path("examples/shell.yaml").read_text())))
    assert isinstance(diagram, Parallel)
    assert diagram == expected
