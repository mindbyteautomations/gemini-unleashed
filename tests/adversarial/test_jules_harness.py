"""
Adversarial Pytest Suite for Jules Testing Harness & Codex Capabilities Integration
Validates 7 adversarial exploit vectors, non-bypassable denial contracts,
ASP symbolic proofs, MTL metrics, and 6-stage capability lifecycle progression.
"""
import os
import sys
import json
import pytest
from datetime import datetime, timezone

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from harness.adversarial_runner import AdversarialRunner
from cognition.codex_evaluator import (
    CodexASTAnalyzer,
    ASPSymbolicGuardian,
    MetricTemporalEvaluator,
    CapabilityLifecycleController,
    CapabilityStage
)
from policies.security_guardian import SecurityGuardian
from policies.budget_guardian import BudgetGuardian, BudgetState
from kernel.task_router import TaskRouter

class TestJulesAdversarialHarness:
    def test_vector_1_i_state_violation(self):
        """Vector 1: Direct unmediated state mutation attempt must be denied."""
        res = AdversarialRunner.test_vector_1_i_state_violation()
        assert res["denial_enforced"] is True
        assert res["exit_status"] == "DENIED_BY_SECURITY"

    def test_vector_2_privilege_escalation(self):
        """Vector 2: Level 5 agents attempting root/IAM/billing operations must be denied."""
        res = AdversarialRunner.test_vector_2_privilege_escalation()
        assert res["denial_enforced"] is True
        assert res["tests_run"] == 8  # 4 ops * 2 agents (jules_worker, codex_agent)

    def test_vector_3_task_envelope_tampering(self):
        """Vector 3: Scope breach and forbidden actions must be denied."""
        res = AdversarialRunner.test_vector_3_task_envelope_tampering()
        assert res["denial_enforced"] is True
        assert res["exit_status"] == "TASK_DENIAL"

    def test_vector_4_metabolic_token_exhaustion(self):
        """Vector 4: Budget circuit breaker must trigger BLACK state on >$100 projected burn."""
        res = AdversarialRunner.test_vector_4_metabolic_token_exhaustion()
        assert res["denial_enforced"] is True
        assert res["circuit_breaker_active"] is True
        assert res["exit_status"] == "DENIED_BY_BUDGET_BLACK"

    def test_vector_5_memory_plane_contamination(self):
        """Vector 5: Write to consumer Redis SaaS must be blocked; Firestore approved."""
        res = AdversarialRunner.test_vector_5_memory_plane_contamination()
        assert res["denial_enforced"] is True
        assert res["exit_status"] == "DENIED_BY_MEMORY_ISOLATION"

    def test_vector_6_clock_drift_and_race(self):
        """Vector 6: Distributed mutex contention returns HTTP 200 noop_lease_active."""
        res = AdversarialRunner.test_vector_6_clock_drift_and_race_condition()
        assert res["denial_enforced"] is True
        assert res["exit_status"] == "MUTEX_ENFORCED"
        assert res["noop_response"]["status_code"] == "noop_lease_active"

    def test_vector_7_transport_malformations(self):
        """Vector 7: Transport errors (401 unauthenticated, 405 method not allowed) rejected."""
        res = AdversarialRunner.test_vector_7_transport_malformations()
        assert res["denial_enforced"] is True
        assert res["exit_status"] == "TRANSPORT_HARDENED"
        assert 401 in res["checked_statuses"]
        assert 405 in res["checked_statuses"]

    def test_full_adversarial_suite_and_receipt(self):
        """Full suite execution must return AUDIT_PASSED_CLEAN sealed receipt."""
        suite_res = AdversarialRunner.run_full_adversarial_suite()
        receipt = suite_res["audit_receipt"]
        assert receipt["vectors_tested"] >= 7
        assert receipt["critical_vulnerabilities"] == 0
        assert receipt["high_vulnerabilities"] == 0
        assert receipt["audit_verdict"] == "AUDIT_PASSED_CLEAN"
        assert receipt["receipt_id"].startswith("RCPT-JULES-")
        assert receipt["task_id"].startswith("TASK-")

class TestCodexCapabilitiesAndASP:
    def test_codex_ast_analysis(self):
        """Codex AST Analyzer properly parses valid and invalid Python structures."""
        valid_code = """
class DataPipeline:
    def process(self, item: dict) -> bool:
        if item:
            return True
        return False
"""
        res_valid = CodexASTAnalyzer.analyze_source_code(valid_code)
        assert res_valid["valid_syntax"] is True
        assert "DataPipeline" in res_valid["classes"]
        assert "process" in res_valid["functions"]
        assert res_valid["branch_count"] == 1

        invalid_code = "def broken_syntax(:"
        res_invalid = CodexASTAnalyzer.analyze_source_code(invalid_code)
        assert res_invalid["valid_syntax"] is False

    def test_asp_symbolic_guardian_invariants(self):
        """ASP Symbolic Guardian enforces clingo invariant proofs."""
        # Invariant 1: Authority Level 5 cannot execute forbidden op
        ok1, msg1 = ASPSymbolicGuardian.verify_action_safety("codex_agent", 5, "modify_iam")
        assert not ok1
        assert "ASP_PROOF_FAILED" in msg1

        # Invariant 2: Merge safety requires clean Jules audit
        clean_receipt = {"audit_verdict": "AUDIT_PASSED_CLEAN", "critical_vulnerabilities": 0, "high_vulnerabilities": 0}
        dirty_receipt = {"audit_verdict": "AUDIT_REJECTED_EXPLOIT_DETECTED", "critical_vulnerabilities": 1, "high_vulnerabilities": 0}
        
        ok2_clean, _ = ASPSymbolicGuardian.verify_merge_safety("TASK-100", clean_receipt)
        assert ok2_clean is True

        ok2_dirty, msg2_dirty = ASPSymbolicGuardian.verify_merge_safety("TASK-100", dirty_receipt)
        assert ok2_dirty is False
        assert "ASP_PROOF_FAILED" in msg2_dirty

        # Invariant 3: Memory plane isolation
        ok3_redis, _ = ASPSymbolicGuardian.verify_memory_isolation("codex_agent", "redis_cloud_saas")
        assert ok3_redis is False

        ok3_fs, _ = ASPSymbolicGuardian.verify_memory_isolation("codex_agent", "firestore_native")
        assert ok3_fs is True

        # Invariant 4: Rollback strategy presence
        env_with_rb = {"task_id": "TASK-100", "rollback": {"method": "git_revert"}}
        env_no_rb = {"task_id": "TASK-100"}
        assert ASPSymbolicGuardian.verify_task_envelope_rollback(env_with_rb)[0] is True
        assert ASPSymbolicGuardian.verify_task_envelope_rollback(env_no_rb)[0] is False

    def test_metric_temporal_logic(self):
        """MTL formulas evaluate bounded timing constraints."""
        # Formula 1: Jules execution <= 180s
        assert MetricTemporalEvaluator.evaluate_jules_bounded_time(100.0, 150.0, 180.0) is True
        assert MetricTemporalEvaluator.evaluate_jules_bounded_time(100.0, 300.0, 180.0) is False

        # Formula 2: Rollback liveness <= 15s
        assert MetricTemporalEvaluator.evaluate_rollback_liveness(10.0, 22.0, 15.0) is True
        assert MetricTemporalEvaluator.evaluate_rollback_liveness(10.0, 30.0, 15.0) is False

        # Formula 3: Brier logging <= 5s
        assert MetricTemporalEvaluator.evaluate_brier_logging_liveness(50.0, 53.0, 5.0) is True
        assert MetricTemporalEvaluator.evaluate_brier_logging_liveness(50.0, 60.0, 5.0) is False

    def test_six_stage_capability_lifecycle(self):
        """6-Stage Lifecycle progression: DISCOVERED -> UNDERSTOOD -> IMPLEMENTED -> TESTED -> VALIDATED -> ASSIMILATED."""
        code = "def generated_tool(): return {'status': 'ok'}"
        clean_receipt = {
            "receipt_id": "RCPT-JULES-20260829-001",
            "task_id": "TASK-20260829-001",
            "audit_verdict": "AUDIT_PASSED_CLEAN",
            "critical_vulnerabilities": 0,
            "high_vulnerabilities": 0
        }
        envelope = {
            "task_id": "TASK-20260829-001",
            "rollback": {"method": "git_revert"}
        }

        res = CapabilityLifecycleController.progress_capability(
            "codex_code_synthesis",
            code,
            clean_receipt,
            envelope
        )
        assert res["status"] == "FULL_LIFECYCLE_COMPLIANT"
        assert res["current_stage"] == CapabilityStage.ASSIMILATED.value
        assert len(res["history"]) == 6
