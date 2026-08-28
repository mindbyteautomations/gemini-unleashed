"""
Security Guardian & Constitutional Firewall
Enforces Can Do vs May Do vs Contextual Task Authorization.
Protects Level 0/1 Invariants (Genesis, IAM, Billing).
"""
import json
import os
from typing import Dict, Any, Tuple

class SecurityGuardian:
    FORBIDDEN_AUTONOMOUS_ACTIONS = {
        "modify_genesis",
        "modify_constitution",
        "modify_iam",
        "create_service_account",
        "grant_roles",
        "modify_billing",
        "delete_database",
        "access_production_root_secrets"
    }

    @classmethod
    def evaluate_action(
        cls,
        actor: str,
        action: str,
        task_envelope: Dict[str, Any] = None
    ) -> Tuple[bool, str]:
        """
        Deterministic security check.
        """
        # 1. Check Level 0/1 Invariants
        if action in cls.FORBIDDEN_AUTONOMOUS_ACTIONS:
            if actor != "human_operator":
                return False, f"SECURITY DENIAL: Action '{action}' is a Level 0/1 constitutional invariant and cannot be executed autonomously by '{actor}'."

        # 2. Check Task Envelope Context if provided
        if task_envelope:
            scope = task_envelope.get("scope", {})
            forbidden = set(scope.get("forbidden_actions", []))
            allowed = set(scope.get("allowed_actions", []))

            if action in forbidden:
                return False, f"TASK DENIAL: Action '{action}' is explicitly forbidden in Task Envelope '{task_envelope.get('task_id')}'."

            if allowed and action not in allowed:
                return False, f"TASK DENIAL: Action '{action}' is not in the allowed actions list for Task Envelope '{task_envelope.get('task_id')}'."

        return True, f"SECURITY APPROVAL: Action '{action}' authorized for actor '{actor}'."

if __name__ == "__main__":
    print("--- Security Guardian Test Matrix ---")
    print(SecurityGuardian.evaluate_action("gemini_core", "modify_iam"))
    print(SecurityGuardian.evaluate_action("jules_worker", "create_pull_request"))
    print(SecurityGuardian.evaluate_action("human_operator", "modify_iam"))
