from discopy import python

from mytilus.comput import computer
from mytilus.comput.computer import Box, ComputableFunction, Computer, Copy, Program, ProgramTy, Ty
from mytilus.comput.mytilus import io_ty
from mytilus.pcc import LOADER, MonoidalComputer, ProgramClosedCategory, SHELL
from mytilus.state import (
    Execution,
    InputOutputMap,
    Process,
    StateUpdateMap,
    execute,
    fixed_state,
    simulate,
)
from mytilus.state.loader import LoaderExecution
from mytilus.state.mytilus import ShellExecution
from mytilus.state.python import ProcessRunner
from mytilus.wire.loader import loader_stream_ty


X, Y, A, B = Ty("X"), Ty("Y"), Ty("A"), Ty("B")
P = ProgramTy("P")
H_ty, L_ty = ProgramTy("H"), ProgramTy("L")


def test_eq_7_1_process_is_a_pair_of_functions():
    q = Process("q", X, A, B)
    expected = Copy(X @ A) >> q.state_update_diagram() @ q.output_diagram()

    assert isinstance(q.state_update_diagram(), StateUpdateMap)
    assert isinstance(q.output_diagram(), InputOutputMap)
    assert q.state_update_diagram().dom == X @ A
    assert q.state_update_diagram().cod == X
    assert q.output_diagram().dom == X @ A
    assert q.output_diagram().cod == B
    assert q == expected


def test_fig_7_2_simulation_is_postcomposition_with_state_map():
    q = Process("q", X, A, B)
    s = Box("s", X, Y)

    simulated = simulate(q, s)

    assert simulated == q >> s @ B
    assert simulated.dom == X @ A
    assert simulated.cod == Y @ B


def test_process_maps_are_overrideable_methods():
    state_update = Box("u", X @ A, X)
    output = Box("v", X @ A, B)

    class CustomProcess(Process):
        def state_update_diagram(self):
            return state_update

        def output_diagram(self):
            return output

    q = CustomProcess("q", X, A, B)

    assert q.state_update_diagram() == state_update
    assert q.output_diagram() == output
    assert q == Copy(X @ A) >> state_update @ output


def test_sec_7_3_program_execution_is_stateful():
    execution = Execution(
        "{}",
        P,
        A,
        B,
    )

    assert execution.dom == P @ A
    assert execution.cod == P @ B
    assert execution.universal_ev() == fixed_state(Computer(P, A, B))
    assert execution.state_update_diagram() == StateUpdateMap("{}", P, A)
    assert execution.output_diagram() == InputOutputMap("{}", P, A, B)
    assert execution.state_update_diagram().cod == P
    assert execution.output_diagram().cod == B


def test_execution_universal_evaluator_is_overrideable_method():
    universal_ev = Box("ev", P @ A, P @ B)

    class CustomExecution(Execution):
        def universal_ev(self):
            return universal_ev

    execution = CustomExecution("q", P, A, B)

    assert execution.universal_ev() == universal_ev
    assert execution.specialize() == universal_ev


def test_process_runner_interprets_generic_state_projections():
    class DummyRunner(ProcessRunner):
        def __init__(self):
            ProcessRunner.__init__(self)

        def process_ar_map(self, box, dom, cod):
            return python.Function(lambda *_xs: None, dom, cod)

    runner = DummyRunner()
    state_update = runner.ar_map(StateUpdateMap("q", X, A))
    output = runner.ar_map(InputOutputMap("q", X, A, B))

    assert state_update("state", "input") == "state"
    assert output(lambda value: f"out:{value}", "input") == "out:input"


def test_process_runner_interprets_generic_structural_boxes():
    class DummyRunner(ProcessRunner):
        def __init__(self):
            ProcessRunner.__init__(self)

        def process_ar_map(self, box, dom, cod):
            return python.Function(lambda *_xs: None, dom, cod)

    runner = DummyRunner()

    assert runner.ar_map(Copy(X))("value") == ("value", "value")
    assert runner.ar_map(computer.Delete(X))("value") == ()
    assert runner.ar_map(computer.Swap(X, Y))("left", "right") == ("right", "left")


def test_loader_and_shell_projections_live_in_state():
    assert LoaderExecution().state_update_diagram() == LOADER.execution(
        loader_stream_ty, loader_stream_ty
    ).state_update_diagram()
    assert LoaderExecution().output_diagram() == LOADER.execution(
        loader_stream_ty, loader_stream_ty
    ).output_diagram()
    assert ShellExecution().state_update_diagram() == SHELL.execution(io_ty, io_ty).state_update_diagram()
    assert ShellExecution().output_diagram() == SHELL.execution(io_ty, io_ty).output_diagram()


def test_sec_7_4_fixed_state_lifts_a_function_to_a_process():
    g = ComputableFunction("g", X, A, B)
    hat_g = fixed_state(g)

    assert hat_g == (Copy(X) @ A >> X @ g)
    assert hat_g.dom == X @ A
    assert hat_g.cod == X @ B


def test_sec_7_4_execute_uses_stateful_execution():
    Q = Program("Q", P, X)
    q = execute(Q, A, B)

    assert q == Q @ A >> Execution(
        "{}",
        P,
        A,
        B,
    ).specialize()
    assert q.dom == X @ A
    assert q.cod == P @ B


def test_sec_8_3_program_closed_category_chooses_a_language_type():
    computer_category = MonoidalComputer()
    high_level = ProgramClosedCategory(H_ty)
    low_level = ProgramClosedCategory(L_ty)

    assert isinstance(high_level, MonoidalComputer)
    assert isinstance(low_level, MonoidalComputer)
    assert high_level.program_ty == H_ty
    assert low_level.program_ty == L_ty
    assert high_level.evaluator(A, B) == Computer(H_ty, A, B)
    assert low_level.evaluator(A, B) == Computer(L_ty, A, B)
    assert high_level.execution(A, B).universal_ev() == fixed_state(Computer(H_ty, A, B))
    assert low_level.execution(A, B).universal_ev() == fixed_state(Computer(L_ty, A, B))
    assert computer_category.ob == high_level.ob == low_level.ob
    assert computer_category.ar == high_level.ar == low_level.ar
