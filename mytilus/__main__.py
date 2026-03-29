import sys
import argparse
import logging
import os
import tempfile


DEFAULT_SHELL_SOURCE = "bin/yaml/shell.yaml"


def configure_matplotlib_cache():
    """Set a writable default MPLCONFIGDIR when the environment does not provide one."""
    cache_dir = os.path.join(tempfile.gettempdir(), "mytilus-mpl")
    os.makedirs(cache_dir, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", cache_dir)


def enable_diagram_drawing():
    """Configure Matplotlib only when diagram rendering is explicitly requested."""
    configure_matplotlib_cache()
    import matplotlib

    matplotlib.use("agg")

from .watch import shell_main, mytilus_main, mytilus_source_main


def launch_shell(draw, watch):
    if not os.path.exists(DEFAULT_SHELL_SOURCE):
        # Ensure the directory exists if we want to support creating the file,
        # but for now let's just use a fallback or ensure it doesn't crash.
        # The current shell_main will try to read it.
        os.makedirs(os.path.dirname(DEFAULT_SHELL_SOURCE), exist_ok=True)
        with open(DEFAULT_SHELL_SOURCE, 'w') as f:
            f.write("# Mytilus default shell source\n")
    shell_main(DEFAULT_SHELL_SOURCE, draw, watch)


def run_requested_mode(args, draw):
    if args.command_text is not None:
        logging.debug("running inline command text")
        return mytilus_source_main(args.command_text, draw)
    elif args.file_name is None:
        logging.debug("Starting shell")
        launch_shell(draw, args.watch)
        return 0
    else:
        return mytilus_main(args.file_name, draw)


def interactive_followup_requested(args):
    return args.interactive and (args.command_text is not None or args.file_name is not None)


def build_arguments(args):
    parser = argparse.ArgumentParser(prog="mytilus")

    parser.add_argument(
        "--draw",
        action="store_true",
        help="Draw JPG diagrams before running"
    )
    parser.add_argument(
        "-n", "--no-draw",
        dest="draw",
        action="store_false",
        help=argparse.SUPPRESS
    )
    parser.add_argument(
        "-w", "--watch",
        action="store_true",
        help="Watch YAML files for changes in the interactive shell"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "-c", "--command",
        dest="command_text",
        help="Inline YAML command document to run"
    )
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Enter the mytilus REPL after running a file or inline command"
    )
    parser.add_argument(
        "-l", "--login",
        action="store_true",
        help="Ignored; for compatibility with login shells"
    )
    parser.add_argument(
        "-x", "--trace",
        action="store_true",
        help="Print commands and their arguments as they are executed"
    )
    parser.add_argument(
        "file_name",
        nargs="?",
        help="The yaml file to run, if not provided it will start a shell"
    )
    parser.set_defaults(draw=False)
    args = parser.parse_args(args)
    if args.command_text is not None and args.file_name is not None:
        parser.error("cannot use -c/--command with a file name")
    return args


def main(argv):
    args = build_arguments(argv[1:])
    draw = args.draw

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    if args.trace:
        os.environ["MYTILUS_TRACE"] = "1"

    logging.debug(f'running "{args.file_name}" file with draw={draw} watch={args.watch}')
    if interactive_followup_requested(args):
        run_requested_mode(args, draw)
        launch_shell(draw, args.watch)
        return

    sys.exit(run_requested_mode(args, draw))

if __name__ == "__main__":
    main(sys.argv)
