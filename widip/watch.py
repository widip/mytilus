from pathlib import Path
import sys
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from yaml import YAMLError

from discopy.utils import tuplify, untuplify

from .files import diagram_draw, file_diagram
from .metaprog import SHELL_TO_PYTHON, repl_read


# TODO watch functor ??

class ShellHandler(FileSystemEventHandler):
    """Reload the shell on change."""
    def on_modified(self, event):
        if event.src_path.endswith(".yaml"):
            print(f"reloading {event.src_path}")
            try:
                fd = file_diagram(str(event.src_path))
                diagram_draw(Path(event.src_path), fd)
                diagram_draw(Path(event.src_path+".2"), fd)
            except YAMLError as e:
                print(e)

def watch_main():
    """the process manager for the reader and """
    #  TODO watch this path to reload changed files,
    # returning an IO as always and maintaining the contract.
    print(f"watching for changes in current path")
    observer = Observer()
    shell_handler = ShellHandler()
    observer.schedule(shell_handler, ".", recursive=True)
    observer.start()
    return observer

def shell_main(file_name, draw=True):
    try:
        while True:
            observer = watch_main()
            try:
                prompt = f"--- !{file_name}\n"
                source = input(prompt)
                source_d = repl_read(source)
                # source_d.draw(
                #         textpad=(0.3, 0.1),
                #         fontsize=12,
                #         fontsize_types=8)
                path = Path(file_name)

                if draw:
                    diagram_draw(path, source_d)
                result_ev = SHELL_TO_PYTHON(source_d)("")
                print(result_ev)
            except KeyboardInterrupt:
                print()
            except YAMLError as e:
                print(e)
            finally:
                observer.stop()
    except EOFError:
        print("⌁")
        exit(0)

def widish_main(file_name, draw):
    fd = file_diagram(file_name)
    path = Path(file_name)
    if draw:
        diagram_draw(path, fd)
    runner = SHELL_TO_PYTHON(fd)

    run_res = runner("") if sys.stdin.isatty() else runner(sys.stdin.read())

    print(*(tuple(x.rstrip() for x in tuplify(untuplify(run_res)) if x)), sep="\n")
