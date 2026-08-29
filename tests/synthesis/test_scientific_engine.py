"""
Sprint 2 Unit & Integration Pytest Suite
Validates:
1. Mathematical metrics: Brier Calibration, Pheromone Error Density, and VCAR.
2. Scaffold-and-Inflate synthesis report generation (>= 2,500 words, TeX equations).
3. Google Workspace Drive dynamic directory resolution & Gmail DWD dispatch payload.
4. Dataproc dynamic batchId parameterization.
5. Cloud Scheduler cron specification and pulse execution.
"""
import os
import sys
import json
import pytest
from datetime import datetime, timezone

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from synthesis.scientific_engine import (
    EpistemicTelemetryCalculator,
    ScientificSynthesisEngine
)
from workspace.drive_sync import WorkspaceDriveSync, DWD_CLIENT_ID
from pipelines.dataproc_knowledge_etl import (
    generate_dynamic_batch_id,
    launch_dataproc_serverless_batch
)
from synthesis.synthesis_scheduler import SynthesisScheduler, CRON_NAME, CRON_SCHEDULE

class TestEpistemicTelemetryMath:
    def test_brier_score_calculation(self):
        """Brier calibration score accurately computes mean squared error."""
        preds = [
            {"forecast_prob": 0.95, "actual_outcome": 1.0},
            {"forecast_prob": 0.90, "actual_outcome": 1.0}
        ]
        # ( (0.05)^2 + (0.10)^2 ) / 2 = (0.0025 + 0.01) / 2 = 0.00625 -> 0.0062
        bs = EpistemicTelemetryCalculator.calculate_brier_score(preds)
        assert bs == 0.0062
        assert bs < 0.10  # Elite threshold

    def test_pheromone_density_calculation(self):
        """Pheromone density properly applies exponential temporal decay."""
        now = datetime.now(timezone.utc).timestamp()
        events = [
            {"severity_weight": 1.0, "timestamp_epoch": now - 3600},   # 1 hour ago
            {"severity_weight": 0.5, "timestamp_epoch": now - 7200}    # 2 hours ago
        ]
        density = EpistemicTelemetryCalculator.calculate_pheromone_density(events, window_hours=24.0, decay_constant_lambda=0.05)
        assert density > 0.0
        assert density < 2.0

    def test_vcar_calculation(self):
        """VCAR properly calculates verified capabilities per dollar-risk-time unit."""
        vcar = EpistemicTelemetryCalculator.calculate_vcar(
            new_validated_capabilities=4,
            time_days=1.0,
            resource_cost_usd=14.20,
            risk_class_multiplier=1.2
        )
        # 4 / (1.0 * 14.20 * 1.2) = 4 / 17.04 = 0.2347
        assert vcar == 0.2347
        assert vcar > 0.0

class TestScientificSynthesisEngine:
    def test_scaffold_and_inflate_report(self):
        """Report meets minimum 2,500 words, TeX equations, and schema structure."""
        report = ScientificSynthesisEngine.generate_scaffold_and_inflate_report(spend_usd=14.20)
        
        assert report["synthesis_id"].startswith("SYNTH-")
        assert report["word_count"] >= 2500
        assert report["equations_count"] >= 5
        assert len(report["sections"]) >= 4
        assert "brier_calibration_score" in report["metrics"]
        assert "pheromone_error_density" in report["metrics"]
        assert "vcar_score" in report["metrics"]
        assert report["provenance"]["author_agent"] == "antigravity_lead_actuator"

    def test_daily_synthesis_pipeline_execution(self):
        """Full pipeline executes and generates both report and workspace dispatch payload."""
        res = ScientificSynthesisEngine.execute_daily_synthesis_pipeline(recipient_email="dev@mindbyte.net")
        
        report = res["report_payload"]
        dispatch = res["dispatch_payload"]
        
        assert report["word_count"] >= 2500
        assert dispatch["dispatch_id"].startswith("DISPATCH-")
        assert dispatch["target_recipient"] == "dev@mindbyte.net"
        assert dispatch["dwd_client_id"] == "101699370717430009479"
        assert "Autonomous-Workspace-State/Syntheses/" in dispatch["drive_target_path"]
        assert dispatch["delivery_status"] == "DELIVERED_PARALLEL_SYNC"

class TestWorkspaceDriveSync:
    def test_drive_hierarchy_resolution(self):
        """Dynamic directory traversal resolves Autonomous-Workspace-State/Syntheses/YYYY/MM."""
        syncer = WorkspaceDriveSync(impersonated_user="dev@mindbyte.net")
        folder_info = syncer.get_or_create_folder_hierarchy("2026", "08")
        
        assert folder_info["target_path"] == "Autonomous-Workspace-State/Syntheses/2026/08"
        assert "month_folder_id" in folder_info
        assert len(folder_info["month_folder_id"]) > 0

    def test_parallel_sync_dispatch(self):
        """Parallel sync dispatches Drive upload and Gmail notification."""
        syncer = WorkspaceDriveSync(impersonated_user="dev@mindbyte.net")
        dispatch = syncer.execute_parallel_sync(
            synthesis_id="SYNTH-TEST-001",
            filename="test_synthesis.md",
            markdown_content="# Test Content",
            html_content="<h1>Test Content</h1>",
            recipient_email="dev@mindbyte.net"
        )
        assert dispatch["delivery_status"] == "DELIVERED_PARALLEL_SYNC"
        assert dispatch["sender_identity"] == "dev@mindbyte.net"

class TestDataprocBatchParameterization:
    def test_dynamic_batch_id_format(self):
        """Dynamic batch ID begins with 'dataproc-etl-' followed by timestamp."""
        batch_id = generate_dynamic_batch_id()
        assert batch_id.startswith("dataproc-etl-")
        timestamp_part = batch_id.replace("dataproc-etl-", "")
        assert timestamp_part.isdigit()

    def test_launch_payload_contains_batch_id(self):
        """Launcher formats payload with unique batch ID and service account."""
        res = launch_dataproc_serverless_batch(project_id="gemini-unleashed-core")
        assert res["batch_id"].startswith("dataproc-etl-")
        assert res["project_id"] == "gemini-unleashed-core"
        assert res["region"] == "us-central1"

class TestCloudSchedulerCron:
    def test_scheduler_job_manifest(self):
        """Cloud Scheduler job manifest conforms to GCP standards and OIDC SA auth."""
        manifest = SynthesisScheduler.get_scheduler_job_manifest()
        assert manifest["schedule"] == "0 7 * * *"
        assert manifest["timeZone"] == "America/New_York"
        assert manifest["httpTarget"]["oidcToken"]["serviceAccountEmail"] == "gemini-spark-mcp-sa@gemini-unleashed-core.iam.gserviceaccount.com"

    def test_scheduled_pulse_execution(self):
        """Scheduled pulse executes synthesis and returns clean status."""
        pulse_res = SynthesisScheduler.execute_scheduled_synthesis_pulse(recipient_email="dev@mindbyte.net")
        assert pulse_res["status"] == "SUCCESS_PULSE_COMPLETED"
        assert pulse_res["cron_name"] == CRON_NAME
        assert pulse_res["word_count"] >= 2500
