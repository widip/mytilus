from functools import partial
from pathlib import Path

from nx_yaml import nx_compose_all

from discorun.metaprog import core as metaprog_core

from ..comput import python as comput_python
from ..comput import shell as shell_lang
from ..metaprog.hif import HIFToLoader
from ..wire import partial as partial_category
from .loader import LoaderToShell
from .shell import ShellPythonRuntime, ShellToPythonProgram, merge_triples, shell_uev


def assert_partial_ast_equal(actual, expected):
    assert isinstance(actual, partial)
    assert isinstance(expected, partial)
    assert actual.func is expected.func
    assert actual.keywords == expected.keywords
    assert len(actual.args) == len(expected.args)
    for actual_arg, expected_arg in zip(actual.args, expected.args):
        if isinstance(expected_arg, partial):
            assert_partial_ast_equal(actual_arg, expected_arg)
            continue
        assert actual_arg is expected_arg if callable(expected_arg) else actual_arg == expected_arg


def test_shell_specializer_box_lowering():
    shell_specializer = metaprog_core.SpecializerBox(shell_lang.shell_program_ty, name="shell_pev")

    lowering = ShellToPythonProgram()
    lowered = lowering(shell_specializer)

    runtime = ShellPythonRuntime()
    interpreted = runtime(lowered)

    assert partial_category.is_partial_arrow(interpreted)
    specializer_fn = interpreted()

    assert callable(specializer_fn)
    assert specializer_fn is comput_python.pev


def test_shell_interpreter_box_lowering():
    shell_interpreter = metaprog_core.InterpreterBox(shell_lang.shell_program_ty, name="shell_uev")

    lowering = ShellToPythonProgram()
    lowered = lowering(shell_interpreter)

    runtime = ShellPythonRuntime()
    interpreted = runtime(lowered)

    assert partial_category.is_partial_arrow(interpreted)
    interpreter_fn = interpreted()

    assert callable(interpreter_fn)
    assert interpreter_fn is comput_python.uev


def test_yaml_loaded_shell_program_compiles_to_python_partial_ast():
    yaml_text = Path("examples/hello-world.yaml").read_text()
    shell_program = LoaderToShell()(HIFToLoader()(nx_compose_all(yaml_text)))
    lowered = ShellToPythonProgram()(shell_program)
    command_box, _ = lowered.boxes

    command_arrow = partial_category.PartialArrow(
        partial(comput_python.constant, command_box.value),
        (),
        (object,),
    )
    output_arrow = partial_category.PartialArrow(
        shell_uev,
        (object, str, int, str),
        (str, int, str),
    )

    runtime = ShellPythonRuntime()
    compiled = runtime(lowered)

    expected = partial(
        partial_category.then_term,
        partial(
            partial_category.then_term,
            partial(partial_category.identity_term),
            (str, int, str),
            partial(
                partial_category.tensor_term,
                partial(
                    partial_category.tensor_term,
                    partial(partial_category.identity_term),
                    0,
                    (),
                    command_arrow.term,
                    (object,),
                ),
                0,
                (object,),
                partial(partial_category.identity_term),
                (str, int, str),
            ),
        ),
        (object, str, int, str),
        partial(
            partial_category.tensor_term,
            partial(
                partial_category.tensor_term,
                partial(partial_category.identity_term),
                0,
                (),
                output_arrow.term,
                (str, int, str),
            ),
            4,
            (str, int, str),
            partial(partial_category.identity_term),
            (),
        ),
    )

    assert partial_category.is_partial_arrow(compiled)
    assert command_arrow.term.func is comput_python.constant
    assert output_arrow.term.func is shell_uev
    assert_partial_ast_equal(compiled.term, expected)
    assert compiled("", 0, "") == ("Hello world!\n", 0, "")


def test_shell_yaml_compiles_to_python_partial_ast():
    yaml_text = Path("examples/shell.yaml").read_text()
    shell_program = LoaderToShell()(HIFToLoader()(nx_compose_all(yaml_text)))
    lowered = ShellToPythonProgram()(shell_program)
    cat_box, _, _, _, wc_box, _, grep_box, _, wc_again_box, _, tail_box, _, _ = lowered.boxes

    triple = (str, int, str)
    pair = triple + triple
    triple3 = pair + triple
    io = partial_category.PartialArrow.id((str, int, str))
    output_arrow = partial_category.PartialArrow(
        shell_uev,
        (object,) + triple,
        triple,
    )
    copy_arrow = partial_category.PartialArrow(
        partial(comput_python.copy_op, 2),
        triple,
        pair,
    )
    merge_arrow = partial_category.PartialArrow(
        merge_triples,
        triple3,
        triple,
    )

    def command_arrow(box):
        return partial_category.PartialArrow(
            partial(comput_python.constant, box.value),
            (),
            (object,),
        )

    def layer(left, box, right):
        return partial_category.PartialArrow.id(left) @ box @ partial_category.PartialArrow.id(right)

    runtime = ShellPythonRuntime()
    compiled = runtime(lowered)

    expected = (
        io
        >> layer((), command_arrow(cat_box), triple)
        >> layer((), output_arrow, ())
        >> layer((), copy_arrow, ())
        >> layer(triple, copy_arrow, ())
        >> layer((), command_arrow(wc_box), triple3)
        >> layer((), output_arrow, pair)
        >> layer(triple, command_arrow(grep_box), pair)
        >> layer(triple, output_arrow, triple)
        >> layer(triple, command_arrow(wc_again_box), pair)
        >> layer(triple, output_arrow, triple)
        >> layer(pair, command_arrow(tail_box), triple)
        >> layer(pair, output_arrow, ())
        >> layer((), merge_arrow, ())
    )

    assert partial_category.is_partial_arrow(compiled)
    assert output_arrow.term.func is shell_uev
    assert copy_arrow.term.func is comput_python.copy_op
    assert merge_arrow.term.func is merge_triples
    assert_partial_ast_equal(compiled.term, expected.term)
    assert compiled("", 0, "") == (
        "73\n23\n  ? !grep grep: !wc -c\n  ? !tail -2\n",
        0,
        "",
    )
