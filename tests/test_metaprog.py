import pytest
from nx_yaml import nx_compose_all

from widip.comput.computer import *
from widip.metaprog import SHELL_SPECIALIZER
from widip.metaprog.core import MetaprogramComputation, MetaprogramFunctor, ProgramComputation, ProgramFunctor, Specializer
from widip.metaprog.hif import HIFToLoader
from widip.state.loader import LoaderToShell
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

    graph = nx_compose_all("a")
    loader_to_shell = LoaderToShell()

    assert Specializer().metaprogram_dom() == Ty()
    assert HIFToLoader().metaprogram_dom() == Ty()
    assert loader_to_shell.metaprogram_dom() == Ty()
    assert SHELL_SPECIALIZER.metaprogram_dom() == Ty()
    assert isinstance(loader_to_shell, Specializer)
    assert isinstance(SHELL_SPECIALIZER, Specializer)
    assert HIFToLoader().specialize(graph) == HIFToLoader()(graph)
