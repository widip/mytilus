import mytilus.__main__ as mytilus_main


def test_build_arguments_enables_draw_by_default():
    args = mytilus_main.build_arguments([])

    assert args.draw is True
    assert args.watch is False


def test_build_arguments_no_draw_disables_draw():
    args = mytilus_main.build_arguments(["--no-draw"])

    assert args.draw is False
    assert args.watch is False


def test_build_arguments_accepts_opt_in_draw_and_watch_flags():
    args = mytilus_main.build_arguments(["--draw", "--watch"])

    assert args.draw is True
    assert args.watch is True
