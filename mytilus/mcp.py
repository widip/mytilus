import sys
import os
import io
import logging
import pathlib
from typing import Optional

from fastmcp import FastMCP
import yaml

# Mytilus imports
import mytilus.state as mytilus_state
from mytilus.files import source_diagram

# Special logger for Mytilus tracing.
trace_logger = logging.getLogger("mytilus.trace")

# Setup logging
logger = logging.getLogger("mytilus.mcp")

mcp = FastMCP("Mytilus")

@mcp.tool()
def run_mytilus(document: str) -> str:
    """
    Execute a Mytilus YAML command document. Mytilus is a structured shell 
    where YAML tags represent commands and document structure represents 
    pipelines and parallel execution.
    
    Args:
        document: The Mytilus YAML document to execute (e.g., '!echo hello').
    """
    # Ensure trace mode is active for MCP tool invocations
    os.environ.setdefault("MYTILUS_TRACE", "1")
    
    # Configure trace logger for MCP if not already configured.
    # We do this here once to avoid global side-effects on import.
    if not trace_logger.handlers:
        trace_logger.setLevel(logging.INFO)
        trace_logger.propagate = False
        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setLevel(logging.INFO)
        trace_logger.addHandler(stderr_handler)

    logger.info(f"Executing Mytilus document: {document}")
    
    try:
        fd = source_diagram(document)
        runner = mytilus_state.SHELL_INTERPRETER(fd)
        
        # Mytilus runners expect a status triple or a string. 
        # For a clean start, we pass an empty stdin.
        res = runner("") 
        
        output = io.StringIO()

        # runtime_values handles the extraction of (stdout, rc, stderr) triples 
        # or other values from the execution result.
        for value in mytilus_state.runtime_values(res):
            if isinstance(value, tuple) and len(value) == 3:
                stdout, rc, stderr = value
                output.write(stdout)
                if stderr:
                    if not stdout.endswith('\n') and stdout:
                        output.write('\n')
                    output.write(f"[STDERR]\n{stderr}")
                if rc != 0:
                    if not (stdout.endswith('\n') or (stderr and stderr.endswith('\n'))):
                        output.write('\n')
                    output.write(f"[PROCESS EXITED WITH CODE {rc}]\n")
            else:
                output.write(str(value))
        
        return output.getvalue().strip() or "[Command executed successfully with no output]"
        
    except yaml.YAMLError as e:
        return f"YAML Syntax Error: {str(e)}"
    except Exception as e:
        logger.exception("Error executing Mytilus command")
        return f"Error: {str(e)}"

@mcp.resource("mytilus://skill")
def get_mytilus_skill() -> str:
    """The Mytilus design philosophy and usage guidelines as defined in SKILL.md."""
    skill_path = pathlib.Path(__file__).parent / "SKILL.md"
    if skill_path.exists():
        return skill_path.read_text()
    return "Mytilus SKILL.md not found."

@mcp.prompt("mytilus/skill-introduction")
def introduce_mytilus_skill():
    """An introduction to the Mytilus design philosophy for AI agents."""
    return "Please read the Mytilus SKILL.md (resource mytilus://skill) to understand the design philosophy, usage guidelines, and preferred structured command language for this environment."


if __name__ == "__main__":
    mcp.run()
