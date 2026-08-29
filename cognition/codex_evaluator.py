"""
Codex Evaluator & Symbolic ASP/MTL Governance Validator
Provides AST analysis, static code intelligence evaluation, 6-stage lifecycle progression,
and symbolic invariant proofs (ASP & MTL) for candidate capability acquisitions.
"""
import os
import sys
import ast
import json
import time
import secrets
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

class CapabilityStage(str, Enum):
    DISCOVERED = "DISCOVERED"
    UNDERSTOOD = "UNDERSTOOD"
    IMPLEMENTED = "IMPLEMENTED"
    TESTED = "TESTED"
    VALIDATED = "VALIDATED"
    ASSIMILATED = "ASSIMILATED"

class CodexASTAnalyzer:
    @staticmethod
    def analyze_source_code(code_str: str) -> Dict[str, Any]:
        """
        Parses source code into AST, extracting functions, classes, imports,
        and cyclomatic complexity proxies.
        """
        try:
            tree = ast.parse(code_str)
        except SyntaxError as e:
            return {
                "valid_syntax": False,
                "error": str(e),
                "functions": [],
                "classes": [],
                "imports": [],
                "complexity_score": 0
            }

        functions = []
        classes = []
        imports = []
        branch_count = 0

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                functions.append(node.name)
            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)
            elif isinstance(node, ast.Import):
                for n in node.names:
                    imports.append(n.name)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module or "")
            elif isinstance(node, (ast.If, ast.For, ast.While, ast.Try, ast.ExceptHandler)):
                branch_count += 1

        return {
            "valid_syntax": True,
            "functions": functions,
            "classes": classes,
            "imports": imports,
            "branch_count": branch_count,
            "complexity_score": round(branch_count / max(1, len(functions)), 2)
        }

class ASPSymbolicGuardian:
    FORBIDDEN_OPS = {"modify_iam", "modify_billing", "direct_redis_mutate", "bypass_task_envelope"}

    @classmethod
    def verify_action_safety(cls, agent: str, authority_level: int, action: str) -> Tuple[bool, str]:
        """
        ASP Invariant 1:
        :- execute_action(Agent, Op), authority_level(Agent, 5), forbidden_op(Op).
        """
        if authority_level == 5 and action in cls.FORBIDDEN_OPS:
            return False, f"ASP_PROOF_FAILED: Agent '{agent}' with Authority Level 5 cannot execute forbidden operation '{action}'."
        return True, "ASP_PROOF_SATISFIED: Action complies with authority ceiling invariants."

    @classmethod
    def verify_merge_safety(cls, task_id: str, jules_receipt: Dict[str, Any]) -> Tuple[bool, str]:
        """
        ASP Invariant 2:
        :- merge_to_main(Task), not has_clean_jules_audit(Task).
        """
        verdict = jules_receipt.get("audit_verdict")
        crit = jules_receipt.get("critical_vulnerabilities", 1)
        high = jules_receipt.get("high_vulnerabilities", 1)

        if verdict == "AUDIT_PASSED_CLEAN" and crit == 0 and high == 0:
            return True, f"ASP_PROOF_SATISFIED: Jules Audit Receipt verified clean for task {task_id}."
        return False, f"ASP_PROOF_FAILED: Cannot merge task {task_id} to main without verified clean Jules Audit Receipt (verdict={verdict}, crit={crit}, high={high})."

    @classmethod
    def verify_memory_isolation(cls, agent: str, target_memory_plane: str) -> Tuple[bool, str]:
        """
        ASP Invariant 3:
        :- route_memory_write(Agent, redis_cloud_saas), agent(Agent).
        """
        if target_memory_plane == "redis_cloud_saas":
            return False, f"ASP_PROOF_FAILED: Agent '{agent}' write to '{target_memory_plane}' blocked. Memory plane is quarantined."
        return True, f"ASP_PROOF_SATISFIED: Target memory plane '{target_memory_plane}' is approved for internal agent state."

    @classmethod
    def verify_task_envelope_rollback(cls, task_envelope: Dict[str, Any]) -> Tuple[bool, str]:
        """
        ASP Invariant 4:
        :- mint_task_envelope(Task), not has_rollback_strategy(Task).
        """
        rollback = task_envelope.get("rollback")
        if not rollback or not rollback.get("method"):
            return False, "ASP_PROOF_FAILED: Task Envelope rejected. Non-negotiable rollback strategy is missing."
        return True, f"ASP_PROOF_SATISFIED: Rollback method '{rollback.get('method')}' verified."

class MetricTemporalEvaluator:
    @staticmethod
    def evaluate_jules_bounded_time(dispatch_time: float, completion_time: float, max_seconds: float = 180.0) -> bool:
        """MTL Formula 1: Jules dispatch bounded execution (<= 180s)."""
        duration = completion_time - dispatch_time
        return duration <= max_seconds

    @staticmethod
    def evaluate_rollback_liveness(exploit_detect_time: float, revert_time: float, max_seconds: float = 15.0) -> bool:
        """MTL Formula 2: Rollback liveness on exploit detection (<= 15s)."""
        duration = revert_time - exploit_detect_time
        return duration <= max_seconds

    @staticmethod
    def evaluate_brier_logging_liveness(exp_end_time: float, commit_time: float, max_seconds: float = 5.0) -> bool:
        """MTL Formula 3: Brier calibration commit (<= 5s)."""
        duration = commit_time - exp_end_time
        return duration <= max_seconds

class CapabilityLifecycleController:
    @classmethod
    def progress_capability(
        cls,
        capability_name: str,
        code_artifact: str,
        jules_receipt: Dict[str, Any],
        task_envelope: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enforces the 6-stage lifecycle:
        DISCOVERED -> UNDERSTOOD -> IMPLEMENTED -> TESTED -> VALIDATED -> ASSIMILATED
        """
        history = []
        now = datetime.now(timezone.utc).isoformat()

        # Phase 1: DISCOVERED
        history.append({"stage": CapabilityStage.DISCOVERED.value, "timestamp": now, "status": "CONFIRMED"})

        # Phase 2: UNDERSTOOD
        history.append({"stage": CapabilityStage.UNDERSTOOD.value, "timestamp": now, "status": "CONFIRMED"})

        # Phase 3: IMPLEMENTED (AST analysis by Codex)
        ast_res = CodexASTAnalyzer.analyze_source_code(code_artifact)
        if not ast_res["valid_syntax"]:
            return {
                "capability": capability_name,
                "current_stage": CapabilityStage.IMPLEMENTED.value,
                "status": "FAILED_SYNTAX_ERROR",
                "details": ast_res,
                "history": history
            }
        history.append({"stage": CapabilityStage.IMPLEMENTED.value, "timestamp": now, "status": "CONFIRMED", "ast": ast_res})

        # Phase 4: TESTED (Jules Red-Teaming Receipt)
        if jules_receipt.get("audit_verdict") != "AUDIT_PASSED_CLEAN":
            return {
                "capability": capability_name,
                "current_stage": CapabilityStage.TESTED.value,
                "status": "FAILED_JULES_REDTEAM",
                "details": jules_receipt,
                "history": history
            }
        history.append({"stage": CapabilityStage.TESTED.value, "timestamp": now, "status": "CONFIRMED", "jules_receipt_id": jules_receipt.get("receipt_id")})

        # Phase 5: VALIDATED (ASP Proofs)
        asp_ok, asp_msg = ASPSymbolicGuardian.verify_merge_safety(task_envelope.get("task_id", "TASK-001"), jules_receipt)
        if not asp_ok:
            return {
                "capability": capability_name,
                "current_stage": CapabilityStage.VALIDATED.value,
                "status": "FAILED_ASP_PROOF",
                "reason": asp_msg,
                "history": history
            }
        
        env_ok, env_msg = ASPSymbolicGuardian.verify_task_envelope_rollback(task_envelope)
        if not env_ok:
            return {
                "capability": capability_name,
                "current_stage": CapabilityStage.VALIDATED.value,
                "status": "FAILED_ROLLBACK_INVARIANT",
                "reason": env_msg,
                "history": history
            }
        history.append({"stage": CapabilityStage.VALIDATED.value, "timestamp": now, "status": "CONFIRMED", "proof": asp_msg})

        # Phase 6: ASSIMILATED (Ready for canonical commit to main)
        history.append({"stage": CapabilityStage.ASSIMILATED.value, "timestamp": now, "status": "READY_FOR_MERGE"})

        return {
            "capability": capability_name,
            "current_stage": CapabilityStage.ASSIMILATED.value,
            "status": "FULL_LIFECYCLE_COMPLIANT",
            "history": history
        }

if __name__ == "__main__":
    sample_code = """
def sample_codex_function(data: dict) -> dict:
    # Deterministic transformation
    if not data:
        return {}
    return {"processed": True, "count": len(data)}
"""
    print("=== Testing Codex Evaluator & 6-Stage Lifecycle ===")
    analysis = CodexASTAnalyzer.analyze_source_code(sample_code)
    print("AST Analysis:", json.dumps(analysis, indent=2))

    sample_receipt = {
        "receipt_id": "RCPT-JULES-20260829-001",
        "task_id": "TASK-20260829-001",
        "audit_verdict": "AUDIT_PASSED_CLEAN",
        "critical_vulnerabilities": 0,
        "high_vulnerabilities": 0
    }
    sample_envelope = {
        "task_id": "TASK-20260829-001",
        "rollback": {"method": "git_revert"}
    }
    lifecycle_res = CapabilityLifecycleController.progress_capability(
        "codex_code_synthesis",
        sample_code,
        sample_receipt,
        sample_envelope
    )
    print("\nLifecycle Result:", json.dumps(lifecycle_res, indent=2))
