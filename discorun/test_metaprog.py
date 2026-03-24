import pytest

from discorun.comput.computer import *
from discorun.metaprog.core import MetaprogramComputation, MetaprogramFunctor, ProgramComputation, ProgramFunctor, Specializer
from os import path


# TODO deduplicate with SVG write logic from test_lang.py
SVG_ROOT_PATH = path.join("tests", "svg")

def svg_path(basename):
    return path.join(SVG_ROOT_PATH, basename)


@pytest.fixture(autouse=True)
def after_each_test(request):
    yield
    test_name = request.node.name

    data = getattr(request.node, "draw_objects", None)
    if not data:
        raise AttributeError(f"test {test_name} did not set draw_objects (left, right) attribute for drawing")
        
    comp, prog, mprog = data
    
    from pathlib import Path
    from mytilus.files import diagram_draw
    
    diagram_draw(Path(svg_path(f"{test_name}_comp.svg")), comp)
    diagram_draw(Path(svg_path(f"{test_name}_prog.svg")), prog)
    diagram_draw(Path(svg_path(f"{test_name}_mprog.svg")), mprog)


A, B, X = Ty("A"), Ty("B"), Ty("X")
H_ty, L_ty = ProgramTy("H"), ProgramTy("L")
h_ev = ComputableFunction("{H}", X, A, B)
l_ev = ComputableFunction("{L}", X, A, B)
H_to_L = ProgramComputation("H", L_ty, X, A, B)
L_to_H = ProgramComputation("L", H_ty, X, A, B)


def test_sec_6_2_2(request):
    """
    Sec. 6.2.2 {H}L = h, {L}H = l
    """
    program_f = ProgramFunctor()
    request.node.draw_objects = (h_ev, l_ev, H_to_L)
    assert program_f(H_to_L) == h_ev
    assert program_f(L_to_H) == l_ev

def test_fig_6_3_eq_0(request):
    """
    Fig. 6.3 right-hand side: {H}L(X, y)
    """
    x_program = Program("X", H_ty, Ty())
    interpreter = ProgramComputation("H", L_ty, H_ty, A, B)

    transformed = x_program @ A >> ProgramFunctor()(interpreter)
    expected = x_program @ A >> ComputableFunction("{H}", H_ty, A, B)

    request.node.draw_objects = (expected, transformed, interpreter)
    assert transformed == expected


def test_fig_6_3_eq_1(request):
    """
    Fig. 6.3 right-hand side after one metaprogram rewrite: {pev(H)L X}L y
    """
    x_program = Program("X", H_ty, Ty())
    compiler = MetaprogramComputation("H", L_ty, L_ty, H_ty, A, B)

    transformed = x_program @ A >> MetaprogramFunctor()(compiler)
    expected = (
        x_program @ A
        >> ProgramComputation("{H}", L_ty, Ty(), H_ty, L_ty) @ A
        >> Computer(L_ty, A, B)
    )

    request.node.draw_objects = (expected, transformed, compiler)
    assert MetaprogramFunctor()(compiler) == compiler.partial_ev()
    assert transformed == expected


def test_specializers_are_unit_metaprograms_with_partial_evaluators(request):
    request.node.draw_objects = (h_ev, l_ev, H_to_L)

    specializer = Specializer()

    assert specializer.metaprogram_dom() == Ty()
    assert specializer(A @ B) == A @ B
    assert specializer.specialize(H_to_L) == H_to_L
