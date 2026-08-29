"""
Pytest Suite for Unified Developer Subagent Suite & Claude Code CLI
Validates CLI availability, Task Envelope authorization, forbidden operation interception,
and task routing across all 7 developer subagents.
"""
import os
import sys
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from actuators.claude_code_actuator import ClaudeCodeActuator
from kernel.task_router import TaskRouter
from policies.security_guardian import SecurityGuardian

class TestClaudeCodeActuator:
    def test_cli_installed_and_version(self):
        """Claude Code CLI is installed and returns valid version."""
        status = ClaudeCodeActuator.check_cli_available()
        assert status["installed"] is True
        assert "2.1." in status["version"]
        assert status["status"] == "AVAILABLE"

    def test_task_envelope_security_rejection(self):
        """Unapproved actions in task envelope are deterministically rejected."""
        unauthorized_envelope = {
            "task_id": "TASK-CLAUDE-SEC-01",
            "scope": {
                "allowed_actions": ["synthesize_code"],
                "forbidden_actions": ["claude_code_exec", "modify_iam"]
            },
            "authorization": {"policy_level": 5}
        }
        res = ClaudeCodeActuator.execute_refactor_session(
            prompt="Audit code",
            task_envelope=unauthorized_envelope
        )
        assert res["status"] == "DENIED_BY_SECURITY"

    def test_task_router_selects_claude_code_cli(self):
        """Task Router directs CLI terminal coding and full-stack refactoring to claude_code_cli."""
        task = {
            "task_id": "TASK-CLAUDE-ROUTER-01",
            "objective": {"description": "Perform full-stack codebase refactor with claude CLI ultracode"},
            "scope": {"allowed_actions": ["claude_code_exec", "claude_code_refactor"]},
            "authorization": {"policy_level": 5}
        }
        actuator, reason = TaskRouter.select_actuator(task)
        assert actuator == "claude_code_cli"
        assert "Claude Code CLI" in reason

    def test_task_router_selects_all_7_subagents(self):
        """Task Router properly routes across all 7 specialized subagent engines."""
        subagent_tasks = [
            ({"scope": {"allowed_actions": ["claude_code_exec"]}}, "claude_code_cli"),
            ({"scope": {"allowed_actions": ["jules_exec"]}}, "jules_cli"),
            ({"scope": {"allowed_actions": ["agy_exec"]}}, "antigravity_cli"),
            ({"scope": {"allowed_actions": ["gcloud_exec"]}}, "gcloud_cli"),
            ({"scope": {"allowed_actions": ["copilot_complete"]}}, "github_copilot"),
            ({"scope": {"allowed_actions": ["gemini_agent_dispatch"]}}, "gemini_managed_agent"),
            ({"scope": {"allowed_actions": ["analyze_ast"]}}, "codex_agent"),
            ({"scope": {"allowed_actions": ["reason_and_plan"]}}, "gemini_core"),
        ]
        for task_spec, expected_actuator in subagent_tasks:
            envelope = {"task_id": "TASK-SUBAGENT-TEST", "objective": {"description": "Test routing"}, **task_spec}
            actuator, _ = TaskRouter.select_actuator(envelope)
            assert actuator == expected_actuator
