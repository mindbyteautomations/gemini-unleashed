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

        # Asynchronous GitHub PR workflow -> Jules
        if "create_pull_request" in req_actions or "github_issue" in objective:
            return "jules_worker", "Selected Jules Worker for asynchronous Git/PR implementation."

        # Interactive engineering, testing, multi-agent coordination -> Antigravity
        elif "run_tests" in req_actions or "deploy" in req_actions or "architecture" in objective:
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
