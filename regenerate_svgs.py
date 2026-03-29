import os
import shutil
from pathlib import Path
import subprocess

def regenerate():
    print("Running tests to generate new SVGs...")
    # Use -m "not needs_terminal" or similar if possible, but runner.py tests are fast.
    subprocess.run(["./.venv/bin/pytest", "tests/test_runner.py"], capture_output=True)
    
    tmp_run_dir = Path("/tmp/pytest-of-widip/pytest-current")
    if not tmp_run_dir.exists():
        print("Error: Pytest temp dir not found.")
        return

    # Find all yaml files in tests/mytilus
    mytilus_tests_dir = Path("tests/mytilus")
    yaml_files = list(mytilus_tests_dir.glob("*.yaml"))
    
    for yaml_file in yaml_files:
        case_id = yaml_file.stem
        print(f"Checking case {case_id}...")
        
        # Pytest basetemp structure for parametrized tests: 
        # test_shell_runner_files_<case_id>_0/
        gen_dir = next(tmp_run_dir.glob(f"test_shell_runner_files_{case_id}_0"), None)
        if not gen_dir:
            # Try without underscore if pytest names it differently
            gen_dir = next(tmp_run_dir.glob(f"test_shell_runner_files_{case_id}0"), None)
            
        if gen_dir:
            for svg_type in ["prog", "mprog"]:
                gen_svg = gen_dir / f"{case_id}.{svg_type}.svg"
                target_svg = mytilus_tests_dir / f"{case_id}.{svg_type}.svg"
                if gen_svg.exists():
                    print(f"  Updating {target_svg.name}")
                    shutil.copy(gen_svg, target_svg)
                else:
                    print(f"  Warning: {gen_svg.name} not found in {gen_dir}")
        else:
            print(f"  Warning: No test directory found for case {case_id}")

if __name__ == "__main__":
    regenerate()
