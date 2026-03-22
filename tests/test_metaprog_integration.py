from nx_yaml import nx_compose_all

from discorun.comput.computer import Ty
from discorun.metaprog.core import Specializer
from mytilus.metaprog.hif import HIFToLoader
from mytilus.metaprog.mytilus import ShellSpecializer
from mytilus.state.loader import LoaderToShell


def test_specializers_are_unit_metaprograms_with_partial_evaluators():
    graph = nx_compose_all("a")
    loader_to_shell = LoaderToShell()
    shell_specializer = ShellSpecializer()

    assert Specializer().metaprogram_dom() == Ty()
    assert HIFToLoader().metaprogram_dom() == Ty()
    assert loader_to_shell.metaprogram_dom() == Ty()
    assert shell_specializer.metaprogram_dom() == Ty()
    assert isinstance(loader_to_shell, Specializer)
    assert isinstance(shell_specializer, Specializer)
    assert HIFToLoader().specialize(graph) == HIFToLoader()(graph)
