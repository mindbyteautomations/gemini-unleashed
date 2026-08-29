"""
Pytest Suite for Cloud Monitoring Dead-Man's Switch
Validates heartbeat liveness evaluation, staleness threshold detection,
and alert dispatching.
"""
import os
import sys
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from monitoring.dead_man_switch import DeadManSwitchMonitor, MAX_LIVENESS_DELTA_SECONDS

class TestDeadManSwitch:
    def test_nominal_liveness_check(self):
        """Nominal heartbeat within 60 minutes reports HEALTHY_LIVENESS_VERIFIED."""
        res = DeadManSwitchMonitor.evaluate_liveness(force_stale_delta=900.0)  # 15 minutes
        assert res["status"] == "HEALTHY_LIVENESS_VERIFIED"
        assert res["alert_triggered"] is False
        assert res["staleness_seconds"] == 900.0

    def test_stale_flatline_triggers_alert(self):
        """Heartbeat older than 60 minutes triggers FLATLINE_ALERT and dispatches notification."""
        res = DeadManSwitchMonitor.evaluate_liveness(force_stale_delta=4500.0)  # 75 minutes
        assert res["status"] == "FLATLINE_ALERT"
        assert res["alert_triggered"] is True
        assert "dispatch_details" in res
        assert res["dispatch_details"]["recipient"] == "dev@mindbyte.net"

    def test_scheduler_manifest_definition(self):
        """Dead-Man's switch Cloud Scheduler job definition has required retry config."""
        config = DeadManSwitchMonitor.get_scheduler_config()
        assert config["schedule"] == "0 * * * *"
        assert config["retryConfig"]["retryCount"] == 5
        assert config["retryConfig"]["minBackoffDuration"] == "10s"
