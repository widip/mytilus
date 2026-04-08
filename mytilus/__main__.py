import sys
import argparse
import logging
import os
import tempfile
import pathlib


DEFAULT_SHELL_SOURCE = pathlib.Path("bin/yaml/shell.yaml")


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


def launch_shell(draw, watch, script_args):
    if not DEFAULT_SHELL_SOURCE.exists():
        DEFAULT_SHELL_SOURCE.parent.mkdir(exist_ok=True)
        with DEFAULT_SHELL_SOURCE.open('w') as f:
            f.write("# Mytilus default shell source\n")
    shell_main(DEFAULT_SHELL_SOURCE, draw, watch, script_args=script_args)


def run_requested_mode(args, draw):
    if args.interactive and not args.command_text and not args.file_name:
        return launch_shell(draw, args.watch, script_args=args.script_args)
    if args.interactive:
        # Run command then start shell.
        if args.command_text:
            mytilus_source_main(args.command_text, draw, script_args=args.script_args)
        if args.file_name:
            mytilus_main(args.file_name, draw, script_args=args.script_args)
        return launch_shell(draw, args.watch, script_args=args.script_args)
    if args.command_text:
        return mytilus_source_main(args.command_text, draw, script_args=args.script_args)
    if args.file_name:
        return mytilus_main(args.file_name, draw, script_args=args.script_args)
    return launch_shell(draw, args.watch, script_args=args.script_args)


def interactive_followup_requested(args):
    return args.interactive and (args.command_text is not None or args.file_name is not None)


def build_arguments(args):
    parser = argparse.ArgumentParser(prog="mytilus")

    parser.add_argument(
        "-n", "--no-draw",
        dest="draw",
        action="store_false",
        help="Skip SVG diagram rendering when loading a file"
    )
    parser.add_argument(
        "--draw",
        dest="draw",
        action="store_true",
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
    parser.add_argument("script_args", nargs=argparse.REMAINDER)
    parser.set_defaults(draw=True)
    args = parser.parse_args(args)
    if args.command_text is not None and args.file_name is not None:
        parser.error("cannot use -c/--command with a file name")
    return args


def main():
    # 1. Binary Scoping: Prepend the directory of the mytilus executable to PATH.
    # This allows mytilus to find itself if it was called by full path.
    bin_ptr = sys.argv[0]
    bin_dir = os.path.dirname(os.path.abspath(bin_ptr))
    os.environ["PATH"] = f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}"

    # 1b. Project bin/ Scoping: If the mytilus package is running from a source checkout,
    # ensure the repository's bin/ directory is in the PATH to find local YAML tools.
    package_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    repo_bin = os.path.join(package_root, "bin")
    if os.path.isdir(repo_bin):
        os.environ["PATH"] = f"{repo_bin}{os.pathsep}{os.environ.get('PATH', '')}"

    args = build_arguments(sys.argv[1:])
    draw = args.draw

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    if args.trace:
        os.environ["MYTILUS_TRACE"] = "1"

    # 2. Prepend the directory of the YAML file being executed to PATH.
    # This allows sibling YAML "binaries" to be resolved by name.
    if args.file_name:
        script_dir = os.path.dirname(os.path.abspath(args.file_name))
        os.environ["PATH"] = f"{script_dir}{os.pathsep}{os.environ.get('PATH', '')}"

    logging.debug(f'running "{args.file_name}" file with draw={draw} watch={args.watch}')
    if interactive_followup_requested(args):
        run_requested_mode(args, draw)
        launch_shell(draw, args.watch)
        return

    return run_requested_mode(args, draw)

if __name__ == "__main__":
    sys.exit(main())
