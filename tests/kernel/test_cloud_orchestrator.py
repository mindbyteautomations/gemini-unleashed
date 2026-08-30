"""
Pytest Suite for Cloud Subagent Orchestrator & Registry Schema Validation
"""
import os
import sys
import json
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from kernel.orchestrator import CloudSubagentOrchestrator

import unittest.mock

class TestCloudOrchestrator:
    def test_registry_schema_file_validity(self):
        schema_path = os.path.join(PROJECT_ROOT, "schemas", "cloud_subagent_registry.json")
        assert os.path.exists(schema_path)
        with open(schema_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["title"] == "UnifiedCloudSubagentRegistry"
        assert data["properties"]["registry_version"]["enum"] == ["1.3.0"]

    def test_asp_guardian_invariants_file_validity(self):
        asp_path = os.path.join(PROJECT_ROOT, "guardians", "unified_toolchain_guardian.lp")
        assert os.path.exists(asp_path)
        with open(asp_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "subagent(antigravity_orchestrator)" in content
        assert "role(claude_sonnet_5_ultracode, primary_synthesis)" in content

    def test_orchestrator_pipeline_execution(self):
        task_env = {
            "task_id": "TASK-ORCH-TEST-01",
            "prompt": "Synthesize optimized BigQuery streaming connector",
            "objective": {"description": "Synthesize BigQuery connector"}
        }
        with unittest.mock.patch("cloud.subagent_runner.CloudSubagentRunner.execute_task_envelope", return_value={
            "status": "COMPLETED",
            "exit_code": 0,
            "output": "Synthesized verified code diff.",
            "synthesized_code": "def connector(): return True\n"
        }):
            res = CloudSubagentOrchestrator.execute_multi_agent_pipeline(task_env)
            assert res["task_id"] == "TASK-ORCH-TEST-01"
            assert res["orchestrator"] == "antigravity_cloud_orchestrator"
            assert res["final_verdict"] == "PIPELINE_VERIFIED_AND_ASSIMILATED"
            assert "stage_0_cloud_assist" in res["stages"]
            assert "stage_1_synthesis" in res["stages"]
            assert "stage_2_ast_proof" in res["stages"]
            assert "stage_3_adversarial_audit" in res["stages"]
            assert "stage_4_mcp_provisioning" in res["stages"]
