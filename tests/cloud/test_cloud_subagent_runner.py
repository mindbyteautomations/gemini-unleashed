"""
Pytest Suite for Cloud-Native Subagent Runner & Dispatcher
Validates CloudSubagentJobPayload schema compliance, Cloud Run Job execution,
Secret Manager credential mounting, and zero-desktop execution guarantees.
"""
import os
import sys
import json
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from cloud.subagent_runner import CloudSubagentRunner
from cloud.cloud_job_dispatcher import CloudJobDispatcher

class TestCloudSubagentRunner:
    def test_credential_mount_check(self):
        """Verifies session credentials mounting logic."""
        mounted = CloudSubagentRunner.mount_session_credentials()
        assert isinstance(mounted, dict)
        assert "claude_session_oauth" in mounted
        assert "github_token" in mounted

    def test_codex_ast_cloud_execution(self):
        """Codex AST Cloud execution parses code and returns clean metadata."""
        task = {
            "task_id": "TASK-CLOUD-TEST-01",
            "subagent_engine": "codex_ast_cloud",
            "source_code": "def process_telemetry(data):\n    return data * 2\n",
            "objective": {"description": "Parse telemetry logic"}
        }
        res = CloudSubagentRunner.execute_task_envelope(task)
        assert res["task_id"] == "TASK-CLOUD-TEST-01"
        assert res["execution_plane"] == "GCP_CLOUD_RUN_JOB"
        assert res["status"] == "COMPLETED"
        assert "ast_analysis" in res
        assert "process_telemetry" in res["ast_analysis"]["functions"]

    def test_cloud_job_dispatcher_payload_conforms_to_schema(self):
        """Dispatcher constructs a valid CloudSubagentJobPayload."""
        task_env = {
            "task_id": "TASK-DISPATCH-TEST-01",
            "objective": {"description": "Cloud Run Job schema check"},
            "scope": {"allowed_actions": ["codex_code_synthesis"]}
        }
        dispatch_out = CloudJobDispatcher.dispatch_cloud_job("codex_ast_cloud", task_env)
        payload = dispatch_out["job_payload"]
        
        assert payload["job_id"].startswith("JOB-")
        assert payload["execution_plane"] == "GCP_CLOUD_RUN_JOB"
        assert payload["gcp_project"] == "gemini-unleashed-core"
        assert payload["service_account"] == "gemini-spark-mcp-sa@gemini-unleashed-core.iam.gserviceaccount.com"
        assert payload["container_image"] == "gcr.io/gemini-unleashed-core/subagent-runner:v1.0.1"
        assert len(payload["secrets_mounted"]) >= 2
        assert dispatch_out["status"] == "DISPATCH_CONFIRMED"
