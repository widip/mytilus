from discorun.comput.computer import ProgramTy, Ty
from discorun.pcc.core import ProgramClosedCategory


H_ty, L_ty = ProgramTy("H"), ProgramTy("L")


def test_high_level_interpreter_is_typed_evaluator():
    A, B = Ty("A"), Ty("B")
    category = ProgramClosedCategory(H_ty)
    evaluator = category.evaluator(A, B)
    execution = category.execution(A, B)

    assert evaluator == execution.output_diagram()
    assert evaluator.dom == H_ty @ A
    assert evaluator.cod == B


def test_low_level_interpreter_is_typed_evaluator():
    A, B = Ty("A"), Ty("B")
    category = ProgramClosedCategory(L_ty)
    evaluator = category.evaluator(A, B)
    execution = category.execution(A, B)

    assert evaluator == execution.output_diagram()
    assert evaluator.dom == L_ty @ A
    assert evaluator.cod == B


def test_program_closed_simulation_transports_program_types_and_evaluators():
    A = Ty("A")
    high = ProgramClosedCategory(H_ty)
    low = ProgramClosedCategory(L_ty)

    assert high.simulate(H_ty, low) == L_ty
    assert high.simulate(high.evaluator(A, H_ty @ A), low) == low.evaluator(A, L_ty @ A)


def test_program_closed_run_is_execution_specialization():
    A, B = Ty("A"), Ty("B")
    category = ProgramClosedCategory(H_ty)

    assert category.run(A, B) == category.execution(A, B).specialize()
