"""
Pytest Suite for Unified Developer Subagent Suite Executable Tool Wrappers
Tests real tool execution, explicit error handling, and binary validations.
"""
import os
import sys
import unittest.mock
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from actuators.subagent_tool_wrappers import (
    SubagentToolSuite,
    SubagentConfigurationError,
    SubagentExecutionError
)
from actuators.claude_code_actuator import ClaudeCodeActuator

class TestSubagentToolSuite:
    def test_gcloud_cmd_execution(self):
        """gcloud tool wrapper executes real command and returns output."""
        res = SubagentToolSuite.run_gcloud_cmd(["config", "get-value", "project"])
        assert res["subagent"] == "gcloud_cli"
        assert res["exit_code"] == 0
        assert "gemini-unleashed-core" in res["stdout"]

    def test_codex_ast_execution(self):
        """Codex tool wrapper executes real AST parsing and returns symbol table."""
        code = "def calculate_entropy(x):\n    return x * 0.5\n"
        res = SubagentToolSuite.run_codex_ast(code)
        assert res["subagent"] == "codex_agent"
        assert res["status"] == "COMPLETED"
        assert "calculate_entropy" in res["ast_analysis"]["functions"]

    def test_codex_ast_empty_code_raises_error(self):
        """Codex tool wrapper raises SubagentConfigurationError on empty code."""
        with pytest.raises(SubagentConfigurationError):
            SubagentToolSuite.run_codex_ast("   ")

    def test_claude_synthesis_unauthenticated_raises_configuration_error(self):
        """Claude Code synthesis raises SubagentConfigurationError when unauthenticated."""
        auth_status = ClaudeCodeActuator.check_auth_status()
        if not auth_status.get("authenticated"):
            with pytest.raises(SubagentConfigurationError) as exc_info:
                SubagentToolSuite.run_claude_synthesis(
                    prompt="Refactor auth",
                    task_envelope={"task_id": "TASK-TEST-001"}
                )
            assert "[claude_code_cli]" in str(exc_info.value)

    def test_copilot_diff_execution(self):
        """Copilot tool wrapper reads target file and returns diff metadata."""
        target_file = os.path.join(PROJECT_ROOT, "kernel", "task_router.py")
        res = SubagentToolSuite.run_copilot_diff(
            file_path=target_file,
            instruction="Optimize router lookup table"
        )
        assert res["subagent"] == "github_copilot"
        assert res["status"] == "DIFF_GENERATED"
        assert res["original_lines"] > 0

    def test_antigravity_task_execution(self):
        """Antigravity CLI wrapper executes process tasks within active kernel."""
        res = SubagentToolSuite.run_antigravity_task("inspect_memory")
        assert res["subagent"] == "antigravity_cli"
        assert res["status"] == "COMPLETED"

    def test_gemini_agent_execution(self):
        """Gemini Managed Agent wrapper routes autonomous reasoning tasks."""
        res = SubagentToolSuite.run_gemini_agent(
            task_description="Analyze substrate liveness",
            context_payload={"subsystem": "temporal_cortex"}
        )
        assert res["subagent"] == "gemini_managed_agent"
        assert res["status"] == "COMPLETED"

    def test_execute_synthesis_with_fallback(self):
        """execute_synthesis_with_fallback executes safely via fallback when Claude Code is unauthenticated."""
        with unittest.mock.patch("actuators.claude_code_actuator.ClaudeCodeActuator.check_auth_status", return_value={"authenticated": False, "error": "Simulated unauthenticated"}):
            res = SubagentToolSuite.execute_synthesis_with_fallback(
                prompt="Generate parser",
                task_envelope={"task_id": "TASK-FALLBACK-01"},
                source_code_fallback="def parser(): return True\n"
            )
            assert res["status"] == "COMPLETED"
            assert res["subagent"] == "codex_agent"
            assert res["mode"] == "FALLBACK_AUTONOMIC"
