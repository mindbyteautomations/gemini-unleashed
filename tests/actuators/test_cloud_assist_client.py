"""
Pytest Suite for Gemini Cloud Assist & AI Companion Client
"""
import os
import sys
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from actuators.cloud_assist_client import GeminiCloudAssistClient

class TestCloudAssistClient:
    def test_architecture_guidance_query(self):
        res = GeminiCloudAssistClient.query_architecture_guidance(
            "Validate Cloud Run Job multi-agent execution topology",
            project_id="gemini-unleashed-core",
            region="us-central1"
        )
        assert res["status"] in ["SUCCESS", "SUCCESS_OFFLINE_BASELINE"]
        assert res["endpoint"] == "geminicloudassist.googleapis.com"
        assert "recommended_topology" in res

    def test_diagnose_iam_policy(self):
        res = GeminiCloudAssistClient.diagnose_iam_policy(
            resource_uri="//run.googleapis.com/projects/gemini-unleashed-core/locations/us-central1/jobs/subagent-runner",
            member="serviceAccount:gemini-spark-mcp-sa@gemini-unleashed-core.iam.gserviceaccount.com"
        )
        assert res["status"] == "DIAGNOSED"
        assert "roles/run.developer" in res["required_roles"]

    def test_query_ai_companion(self):
        res = GeminiCloudAssistClient.query_ai_companion(
            prompt="Recommend retry configuration for Cloud Run Job"
        )
        assert res["status"] == "COMPLETED"
        assert res["endpoint"] == "cloudaicompanion.googleapis.com"
        assert len(res["suggestions"]) > 0
