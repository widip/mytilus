from widip.computer import Box, ComputableFunction, Computer, Copy, Program, ProgramTy, Ty
from widip.state import (
    Execution,
    MonoidalComputer,
    Process,
    ProgramClosedCategory,
    execute,
    fixed_state,
    out,
    simulate,
    sta,
)


X, Y, A, B = Ty("X"), Ty("Y"), Ty("A"), Ty("B")
P = ProgramTy("P")
H_ty, L_ty = ProgramTy("H"), ProgramTy("L")


def test_eq_7_1_process_is_a_pair_of_functions():
    q = Process("q", X, A, B)
    expected = Copy(X @ A) >> sta(q) @ out(q)

    assert sta(q).dom == X @ A
    assert sta(q).cod == X
    assert out(q).dom == X @ A
    assert out(q).cod == B
    assert q == expected


def test_fig_7_2_simulation_is_postcomposition_with_state_map():
    q = Process("q", X, A, B)
    s = Box("s", X, Y)

    simulated = simulate(q, s)

    assert simulated == q >> s @ B
    assert simulated.dom == X @ A
    assert simulated.cod == Y @ B


def test_sec_7_3_program_execution_is_stateful():
    execution = Execution(P, A, B)

    assert execution.dom == P @ A
    assert execution.cod == P @ B
    assert execution.universal_ev() == Computer(P, A, P @ B)
    assert sta(execution).cod == P
    assert out(execution).cod == B


def test_sec_7_4_fixed_state_lifts_a_function_to_a_process():
    g = ComputableFunction("g", X, A, B)
    hat_g = fixed_state(g)

    assert hat_g == (Copy(X) @ A >> X @ g)
    assert hat_g.dom == X @ A
    assert hat_g.cod == X @ B


def test_sec_7_4_execute_uses_stateful_execution():
    Q = Program("Q", P, X)
    q = execute(Q, A, B)

    assert q == Q @ A >> Execution(P, A, B)
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
    assert high_level.execution(A, B).universal_ev() == Computer(H_ty, A, H_ty @ B)
    assert low_level.execution(A, B).universal_ev() == Computer(L_ty, A, L_ty @ B)
    assert computer_category.ob == high_level.ob == low_level.ob
    assert computer_category.ar == high_level.ar == low_level.ar
