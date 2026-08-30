"""Unit tests for RouterCloudAssistAdapter."""

import pytest
from actuators.router_cloud_assist_adapter import (
    RouterCloudAssistAdapter,
    QuotaCheckError,
    EnvelopeFormatError,
)


class TestRouterCloudAssistAdapter:
    def test_init_and_quota_check_nominal(self):
        adapter = RouterCloudAssistAdapter(quota_store={"gemini-unleashed-core": {"cloudaicompanion.googleapis.com": 200}})
        quota = adapter.check_iam_quota("gemini-unleashed-core", "cloudaicompanion.googleapis.com")
        assert quota["project_id"] == "gemini-unleashed-core"
        assert quota["service"] == "cloudaicompanion.googleapis.com"
        assert quota["limit"] == 1000
        assert quota["used"] == 200
        assert quota["remaining"] == 800
        assert quota["allowed"] is True

    def test_quota_check_invalid_inputs(self):
        adapter = RouterCloudAssistAdapter()
        with pytest.raises(QuotaCheckError):
            adapter.check_iam_quota("", "cloudaicompanion.googleapis.com")
        with pytest.raises(QuotaCheckError):
            adapter.check_iam_quota("gemini-unleashed-core", "")

    def test_format_sealed_envelope(self):
        adapter = RouterCloudAssistAdapter()
        envelope = {
            "task_id": "TASK-TEST-001",
            "objective": "Verify sealing",
            "authority_level": 5
        }
        sealed = adapter.format_sealed_envelope(envelope)
        assert sealed["version"] == "1.0"
        assert "envelope_id" in sealed
        assert "sealed_at" in sealed
        assert "payload" in sealed
        assert "checksum" in sealed
        assert len(sealed["checksum"]) == 64  # sha256 hex digest

    def test_format_sealed_envelope_invalid_payload(self):
        adapter = RouterCloudAssistAdapter()
        with pytest.raises(EnvelopeFormatError):
            adapter.format_sealed_envelope("not-a-dict")
