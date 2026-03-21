from discorun.comput.computer import Computer, ProgramTy, Ty
from discorun.pcc.core import ProgramClosedCategory


H_ty, L_ty = ProgramTy("H"), ProgramTy("L")


def test_high_level_interpreter_is_typed_evaluator():
    A, B = Ty("A"), Ty("B")
    evaluator = ProgramClosedCategory(H_ty).evaluator(A, B)
    assert isinstance(evaluator, Computer)
    assert evaluator.dom == Computer(H_ty, A, B).dom
    assert evaluator.cod == Computer(H_ty, A, B).cod


def test_low_level_interpreter_is_typed_evaluator():
    A, B = Ty("A"), Ty("B")
    evaluator = ProgramClosedCategory(L_ty).evaluator(A, B)
    assert isinstance(evaluator, Computer)
    assert evaluator.dom == Computer(L_ty, A, B).dom
    assert evaluator.cod == Computer(L_ty, A, B).cod


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
