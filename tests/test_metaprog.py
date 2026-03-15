import pytest

from widip.computer import *
from widip.metaprog import *
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
    
    comp.draw(path=svg_path(f"{test_name}_comp.svg"))
    prog.draw(path=svg_path(f"{test_name}_prog.svg"))
    mprog.draw(path=svg_path(f"{test_name}_mprog.svg"))


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
    assert H_to_L.universal_ev() == h_ev
    assert L_to_H.universal_ev() == l_ev
    request.node.draw_objects = (h_ev, l_ev, H_to_L)

def test_fig_6_3_eq_0(request):
    """
    Fig. 6.3 {X}H y = {H}L(X, y)
    """
    # comp = ComputableFunction("f", X, A, B)
    # prog = Program("f", L_ty, X)
    # mprog = Metaprogram("F", L_ty)
    # right = MetaprogramFunctor()(mprog)
    # assert right == prog
    # right = ProgramFunctor()(right)
    # assert right == comp
    # request.node.draw_objects = (comp, prog, mprog)
