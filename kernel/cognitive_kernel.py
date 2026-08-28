"""
Cognitive Kernel — The Central OWAI Loop Orchestrator
Coordinates the Observe -> Warrant -> Authorize -> Act -> Integrate cycle.
"""
import os
import sys
import time
import json
import secrets
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from policies.budget_guardian import BudgetGuardian
from policies.security_guardian import SecurityGuardian
from kernel.task_router import TaskRouter

class CognitiveKernel:
    @classmethod
    def calculate_utility(
        cls,
        mission_value: float,
        info_gain: float,
        capability_gain: float,
        cost_usd: float,
        risk_level: int
    ) -> float:
        """
        Calculates action utility under resource scarcity:
        Utility = (Mission Value + Info Gain + Capability Gain) / (Cost + Risk/10 + 0.1)
        """
        numerator = mission_value + info_gain + capability_gain
        denominator = cost_usd + (risk_level * 0.1) + 0.10
        return round(numerator / denominator, 3)

    @classmethod
    def execute_owai_cycle(
        cls,
        observation: Dict[str, Any],
        proposed_action: str,
        scope: Dict[str, Any],
        estimated_cost: float = 0.02,
        current_spend: float = 12.50
    ) -> Dict[str, Any]:
        cycle_id = f"cycle-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-{secrets.token_hex(3)}"
        task_id = f"TASK-{secrets.token_hex(3).upper()}"
        now = datetime.now(timezone.utc).isoformat()

        # 1. OBSERVE
        obs_id = observation.get("observation_id", f"OBS-{secrets.token_hex(4)}")
        obs_content = observation.get("content", "Raw environmental observation")

        # 2. WARRANT (Utility check under budget constraints)
        utility = cls.calculate_utility(
            mission_value=observation.get("importance", 0.8),
            info_gain=0.75,
            capability_gain=0.5,
            cost_usd=estimated_cost,
            risk_level=scope.get("risk_level", 2)
        )
        warranted = utility > 2.0

        if not warranted:
            return {
                "cycle_id": cycle_id,
                "status": "REJECTED_UNWARRANTED",
                "utility": utility,
                "reason": "Calculated utility below activation threshold (low info gain / high cost)."
            }

        # 3. AUTHORIZE (Budget Guardian & Security Guardian Gate)
        b_eval = BudgetGuardian.evaluate_spend(current_spend, estimated_cost)
        if not b_eval.action_allowed:
            return {
                "cycle_id": cycle_id,
                "status": "DENIED_BY_BUDGET",
                "budget_state": b_eval.budget_state.value,
                "reason": b_eval.reason
            }

        task_envelope = {
            "task_id": task_id,
            "created_at": now,
            "origin": {"actor": "gemini_core", "cycle_id": cycle_id},
            "objective": {"description": f"Execute action '{proposed_action}' on observation {obs_id}"},
            "authorization": {"policy_level": scope.get("risk_level", 2), "human_approval_required": False},
            "scope": scope,
            "budget": {"max_usd": estimated_cost * 2},
            "success_criteria": ["task_completed_without_error"],
            "rollback": {"method": "git_revert"}
        }

        # 4. ACT (Task Router delegates to specialized actuator)
        actuator, routing_reason = TaskRouter.select_actuator(task_envelope)
        s_eval, s_msg = SecurityGuardian.evaluate_action(actuator, proposed_action, task_envelope)
        if not s_eval:
            return {
                "cycle_id": cycle_id,
                "status": "DENIED_BY_SECURITY",
                "reason": s_msg
            }

        # 5. INTEGRATE (Synthesize outcome and return execution bundle)
        return {
            "cycle_id": cycle_id,
            "status": "AUTHORIZED_AND_DISPATCHED",
            "task_envelope": task_envelope,
            "actuator": actuator,
            "routing_reason": routing_reason,
            "utility_score": utility,
            "budget_state": b_eval.budget_state.value,
            "timestamp": now
        }

if __name__ == "__main__":
    print("=== Testing Cognitive Kernel OWAI Loop ===")
    sample_obs = {
        "observation_id": "OBS-001",
        "content": "Contradiction detected in Cloud Run FastMCP configuration.",
        "importance": 0.90
    }
    sample_scope = {
        "allowed_actions": ["research_documentation", "resolve_contradiction"],
        "forbidden_actions": ["modify_iam", "modify_billing"],
        "risk_level": 2
    }
    res = CognitiveKernel.execute_owai_cycle(
        observation=sample_obs,
        proposed_action="resolve_contradiction",
        scope=sample_scope,
        estimated_cost=0.03,
        current_spend=14.00
    )
    print(json.dumps(res, indent=2))
