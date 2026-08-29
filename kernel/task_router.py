"""
Task Router — Actuator Phenotype Selector with Autonomic Circuit Breaker
Selects the optimal execution actuator across the Unified Developer Subagent Suite.
Enforces 3-state Circuit Breaker governance: [HEALTHY] -> [FALLBACK_ACTIVE] -> [CIRCUIT_BREAKER_DEGRADED].
Gracefully falls back from unauthenticated engines without unhandled exceptions or silent quality masking.
"""
from enum import Enum
from typing import Dict, Any, Tuple, Optional

class CircuitBreakerState(str, Enum):
    HEALTHY = "HEALTHY"
    FALLBACK_ACTIVE = "FALLBACK_ACTIVE"
    CIRCUIT_BREAKER_DEGRADED = "CIRCUIT_BREAKER_DEGRADED"

class TaskRouter:
    _circuit_breaker_state: CircuitBreakerState = CircuitBreakerState.HEALTHY
    _consecutive_fallbacks: int = 0
    MAX_CONSECUTIVE_FALLBACKS: int = 3

    @classmethod
    def get_circuit_breaker_state(cls) -> CircuitBreakerState:
        return cls._circuit_breaker_state

    @classmethod
    def reset_circuit_breaker(cls):
        cls._circuit_breaker_state = CircuitBreakerState.HEALTHY
        cls._consecutive_fallbacks = 0

    @classmethod
    def select_actuator(
        cls,
        task_envelope: Dict[str, Any],
        bypass_auth_check: bool = False
    ) -> Tuple[str, str]:
        """
        Routes a Task Envelope to the most suitable subagent worker with failover protection.
        """
        req_actions = task_envelope.get("scope", {}).get("allowed_actions", [])
        risk_level = task_envelope.get("authorization", {}).get("policy_level", 3)
        objective = task_envelope.get("objective", {}).get("description", "").lower()

        # 1. Claude Code CLI (Sonnet 5 ultracode) candidate
        if any(a in req_actions for a in ["claude_code_exec", "claude_code_refactor", "claude_code_cli_exec", "claude_code_diff"]) or "claude" in objective or "terminal_coding" in objective or "ultracode" in objective:
            if not bypass_auth_check:
                try:
                    from actuators.claude_code_actuator import ClaudeCodeActuator
                    auth = ClaudeCodeActuator.check_auth_status()
                    if not auth.get("authenticated", False):
                        cls._consecutive_fallbacks += 1
                        if cls._consecutive_fallbacks >= cls.MAX_CONSECUTIVE_FALLBACKS:
                            cls._circuit_breaker_state = CircuitBreakerState.CIRCUIT_BREAKER_DEGRADED
                            return (
                                "codex_agent",
                                f"CIRCUIT_BREAKER_DEGRADED: Claude Code unauthenticated ({cls._consecutive_fallbacks} times). "
                                f"Tripped degraded circuit breaker; escalated to Codex Specialist. Action required: run 'claude' in terminal."
                            )
                        else:
                            cls._circuit_breaker_state = CircuitBreakerState.FALLBACK_ACTIVE
                            return (
                                "codex_agent",
                                f"FALLBACK_ACTIVE: Claude Code unauthenticated ({auth.get('status')}). "
                                f"Autonomously routed to Codex Specialist (action required: run 'claude' in terminal)."
                            )
                    else:
                        cls.reset_circuit_breaker()
                        return "claude_code_cli", "Selected Claude Code CLI (Sonnet 5 ultracode) for multi-file codebase refactoring & terminal synthesis."
                except Exception as e:
                    cls._circuit_breaker_state = CircuitBreakerState.FALLBACK_ACTIVE
                    return "codex_agent", f"FALLBACK_ACTIVE: Auth probe notice ({e}); routed to Codex Specialist."
            else:
                return "claude_code_cli", "Selected Claude Code CLI (Sonnet 5 ultracode) for multi-file codebase refactoring & terminal synthesis."

        # 2. Jules CLI / Worker -> Sandboxed PR implementation & adversarial auditing
        elif any(a in req_actions for a in ["jules_exec", "create_pull_request", "jules_test"]) or "jules" in objective or "github_issue" in objective:
            return "jules_cli", "Selected Jules CLI Worker for asynchronous Git/PR implementation and sandboxed security audit."

        # 3. Antigravity CLI (agy) -> Process management, local testing, & multi-agent orchestration
        elif any(a in req_actions for a in ["agy_exec", "run_tests", "deploy", "architecture", "adversarial_test"]) or "antigravity" in objective or "agy" in objective:
            return "antigravity_cli", "Selected Antigravity CLI (agy) for process supervision, interactive testing, & multi-agent mesh orchestration."

        # 4. gcloud CLI -> Infrastructure lifecycle, IAM, Cloud Run, & Pub/Sub
        elif any(a in req_actions for a in ["gcloud_exec", "provision_infra", "cloud_run_deploy", "pubsub_manage"]) or "gcloud" in objective or "infrastructure" in objective:
            return "gcloud_cli", "Selected gcloud CLI for Cloud Run, Pub/Sub, and infrastructure lifecycle operations."

        # 5. Cloud Code Assist & GitHub Copilot -> Inline diff generation & autocompletion
        elif any(a in req_actions for a in ["copilot_complete", "cloud_code_diff"]) or "copilot" in objective or "inline_diff" in objective:
            return "github_copilot", "Selected GitHub Copilot / Cloud Code Assist for inline diff generation and code completion."

        # 6. Gemini Managed Antigravity Agent / Gemini Cloud Assist -> Cloud-native autonomous research & assist
        elif any(a in req_actions for a in ["gemini_agent_dispatch", "gemini_cloud_assist"]) or "gemini_agent" in objective or "cloud_assist" in objective:
            return "gemini_managed_agent", "Selected Gemini Managed Antigravity Agent for cloud-native autonomous subagent reasoning."

        # 7. Codex Specialist -> AST parsing, symbol tables, & deterministic code synthesis
        elif any(a in req_actions for a in ["analyze_ast", "synthesize_code", "refactor_module", "codex_code_synthesis", "codex_ast_analysis"]) or "ast" in objective or "synthesize" in objective:
            return "codex_agent", "Selected Codex Specialist for AST analysis and deterministic code synthesis."

        # 8. High-level synthesis, hypothesis generation, research -> Gemini Core
        else:
            return "gemini_core", "Selected Gemini Core for reasoning, planning, and evaluation."

if __name__ == "__main__":
    test_task = {
        "task_id": "TASK-000010",
        "objective": {"description": "Implement feature and create pull request"},
        "scope": {"allowed_actions": ["create_pull_request", "write_code"]},
        "authorization": {"policy_level": 3}
    }
    actuator, reason = TaskRouter.select_actuator(test_task)
    print(f"Task: {test_task['task_id']} -> Actuator: {actuator} | Reason: {reason}")
