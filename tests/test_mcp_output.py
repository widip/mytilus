import sys
import io
import unittest
from mytilus.mcp import run_mytilus

class TestMCP(unittest.TestCase):
    def test_run_echo(self):
        result = run_mytilus("!echo hello world")
        self.assertEqual(result, "hello world")

    def test_run_pipeline(self):
        result = run_mytilus("- !echo hello\n- !grep h")
        self.assertEqual(result, "hello")

    def test_run_error(self):
        result = run_mytilus("!bash {-c, 'exit 1'}")
        self.assertIn("[PROCESS EXITED WITH CODE 1]", result)

if __name__ == "__main__":
    unittest.main()
