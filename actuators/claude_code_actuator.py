"""
Claude Code CLI Actuator Bridge
Provides programmatic execution, Task Envelope scope gating, timeout protection,
and telemetry logging for Anthropic Claude Code CLI (@anthropic-ai/claude-code).
Operates strictly under Authority Level 5 governance.
"""
import os
import sys
import json
import time
import secrets
import subprocess
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from policies.security_guardian import SecurityGuardian
from policies.budget_guardian import BudgetGuardian

class ClaudeCodeActuator:
    CLI_COMMAND = "claude"

    @classmethod
    def check_cli_available(cls) -> Dict[str, Any]:
        """Verifies if the Claude Code CLI binary is available in the environment."""
        try:
            res = subprocess.run(
                [cls.CLI_COMMAND, "--version"],
                capture_output=True,
                text=True,
                shell=True,
                timeout=5
            )
            if res.returncode == 0:
                version_str = res.stdout.strip()
                return {
                    "installed": True,
                    "version": version_str,
                    "cli_path": cls.CLI_COMMAND,
                    "status": "AVAILABLE"
                }
            return {
                "installed": False,
                "error": res.stderr.strip(),
                "status": "ERROR"
            }
        except Exception as e:
            return {
                "installed": False,
                "error": str(e),
                "status": "NOT_FOUND"
            }

    @classmethod
    def execute_refactor_session(
        cls,
        prompt: str,
        task_envelope: Dict[str, Any],
        timeout_seconds: float = 60.0
    ) -> Dict[str, Any]:
        """
        Executes a bounded, non-interactive Claude Code CLI command with Task Envelope validation.
        """
        t0 = time.time()
        now_iso = datetime.now(timezone.utc).isoformat()
        exec_id = f"CLAUDE-EXEC-{secrets.token_hex(4).upper()}"

        # 1. Security & Task Envelope Gating
        is_allowed, sec_msg = SecurityGuardian.evaluate_action(
            actor="claude_code_specialist",
            action="claude_code_exec",
            task_envelope=task_envelope
        )
        if not is_allowed:
            return {
                "exec_id": exec_id,
                "status": "DENIED_BY_SECURITY",
                "reason": sec_msg,
                "timestamp": now_iso
            }

        # 2. Budget Guardian Check
        b_eval = BudgetGuardian.evaluate_spend(14.20, 0.05)
        if not b_eval.action_allowed:
            return {
                "exec_id": exec_id,
                "status": "DENIED_BY_BUDGET",
                "reason": b_eval.reason,
                "timestamp": now_iso
            }

        # 3. Subprocess Execution (with non-interactive flags or dry-run fallback)
        cmd = [cls.CLI_COMMAND, "-p", prompt]
        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                stdin=subprocess.DEVNULL,
                shell=True,
                timeout=timeout_seconds,
                cwd=PROJECT_ROOT
            )
            duration_ms = (time.time() - t0) * 1000.0
            
            return {
                "exec_id": exec_id,
                "task_id": task_envelope.get("task_id", "TASK-GENERIC"),
                "status": "COMPLETED" if res.returncode == 0 else "EXECUTION_ERROR",
                "exit_code": res.returncode,
                "output": res.stdout.strip(),
                "stderr": res.stderr.strip(),
                "duration_ms": round(duration_ms, 2),
                "timestamp": now_iso
            }
        except subprocess.TimeoutExpired:
            duration_ms = (time.time() - t0) * 1000.0
            return {
                "exec_id": exec_id,
                "task_id": task_envelope.get("task_id", "TASK-GENERIC"),
                "status": "TIMEOUT_KILLED",
                "duration_ms": round(duration_ms, 2),
                "reason": f"Execution exceeded bounded timeout limit of {timeout_seconds}s.",
                "timestamp": now_iso
            }
        except Exception as e:
            duration_ms = (time.time() - t0) * 1000.0
            return {
                "exec_id": exec_id,
                "task_id": task_envelope.get("task_id", "TASK-GENERIC"),
                "status": "PROCESS_FAILED",
                "error": str(e),
                "duration_ms": round(duration_ms, 2),
                "timestamp": now_iso
            }

if __name__ == "__main__":
    print("=== Testing Claude Code CLI Actuator ===")
    status = ClaudeCodeActuator.check_cli_available()
    print("CLI Status:", json.dumps(status, indent=2))
