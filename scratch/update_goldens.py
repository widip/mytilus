import os
import sys
from pathlib import Path

# Add current directory to path so mytilus can be imported
sys.path.insert(0, os.getcwd())

from nx_yaml import nx_compose_all
from mytilus.metaprog.hif import HIFToLoader
from mytilus.state.loader import LoaderToShell
from mytilus.state.shell import ShellSpecializer
from mytilus.files import diagram_draw, normalize_svg

FIXTURE_DIR = Path("tests/mytilus")

def update_goldens():
    hif_to_loader = HIFToLoader()
    loader_to_shell = LoaderToShell()
    
    for yaml_path in FIXTURE_DIR.glob("*.yaml"):
        print(f"Updating {yaml_path}")
        path = yaml_path.with_suffix("")
        yaml_text = yaml_path.read_text()
        
        mprog = hif_to_loader(nx_compose_all(yaml_text))
        
        # 1. Update prog.svg
        loader_prog = loader_to_shell(mprog)
        prog = ShellSpecializer()(loader_prog)
        prog_svg_path = path.with_suffix(".prog.svg")
        diagram_draw(prog_svg_path, prog)
        
        # 2. Update mprog.svg (just in case, although probably unchanged)
        mprog_svg_path = path.with_suffix(".mprog.svg")
        mprog.draw(path=str(mprog_svg_path),
                   textpad=(0.3, 0.1),
                   fontsize=12,
                   fontsize_types=8)
        mprog_svg_path.write_text(normalize_svg(mprog_svg_path.read_text()))

if __name__ == "__main__":
    update_goldens()
