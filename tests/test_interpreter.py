from widip.compiler import Eval_H, Eval_L, H_ty, L_ty
from widip.comput.computer import Computer, Ty


def test_high_level_interpreter_is_typed_evaluator():
    A, B = Ty("A"), Ty("B")
    evaluator = Eval_H(A, B)
    assert isinstance(evaluator, Computer)
    assert evaluator.dom == Computer(H_ty, A, B).dom
    assert evaluator.cod == Computer(H_ty, A, B).cod


def test_low_level_interpreter_is_typed_evaluator():
    A, B = Ty("A"), Ty("B")
    evaluator = Eval_L(A, B)
    assert isinstance(evaluator, Computer)
    assert evaluator.dom == Computer(L_ty, A, B).dom
    assert evaluator.cod == Computer(L_ty, A, B).cod
