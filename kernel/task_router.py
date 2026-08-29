"""
Task Router — Actuator Phenotype Selector
Selects the optimal execution actuator (Antigravity, Jules, Gemini Core)
based on task envelope requirements, risk profile, and cost.
"""
from typing import Dict, Any, Tuple

class TaskRouter:
    @classmethod
    def select_actuator(cls, task_envelope: Dict[str, Any]) -> Tuple[str, str]:
        """
        Routes a Task Envelope to the most suitable worker.
        """
        req_actions = task_envelope.get("scope", {}).get("allowed_actions", [])
        risk_level = task_envelope.get("authorization", {}).get("policy_level", 3)
        objective = task_envelope.get("objective", {}).get("description", "").lower()

        # Claude Code CLI terminal & full-stack refactoring -> Claude Code Specialist
        if any(a in req_actions for a in ["claude_code_exec", "claude_code_refactor", "claude_code_cli_exec", "claude_code_diff"]) or "claude" in objective or "terminal_coding" in objective:
            return "claude_code_specialist", "Selected Claude Code Specialist for interactive CLI terminal coding & multi-file refactoring."

        # AST analysis, static code intelligence, code synthesis -> Codex
        elif any(a in req_actions for a in ["analyze_ast", "synthesize_code", "refactor_module", "codex_code_synthesis", "codex_ast_analysis"]) or "ast" in objective or "synthesize" in objective or "refactor" in objective:
            return "codex_agent", "Selected Codex Specialist for AST analysis and deterministic code synthesis."

        # Asynchronous GitHub PR workflow -> Jules
        elif "create_pull_request" in req_actions or "github_issue" in objective:
            return "jules_worker", "Selected Jules Worker for asynchronous Git/PR implementation."

        # Interactive engineering, testing, multi-agent coordination -> Antigravity
        elif "run_tests" in req_actions or "deploy" in req_actions or "architecture" in objective or "adversarial_test" in req_actions:
            return "antigravity_orchestrator", "Selected Antigravity Orchestrator for interactive engineering & test execution."

        # High-level synthesis, hypothesis generation, research -> Gemini Core
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
