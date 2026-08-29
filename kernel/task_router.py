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

        # 1. Claude Code CLI (Sonnet 5 ultracode) -> Multi-file terminal refactoring & code generation
        if any(a in req_actions for a in ["claude_code_exec", "claude_code_refactor", "claude_code_cli_exec", "claude_code_diff"]) or "claude" in objective or "terminal_coding" in objective or "ultracode" in objective:
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
