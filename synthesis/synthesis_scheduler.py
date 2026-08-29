"""
Cloud Scheduler Synthesis Cron Trigger & Runner
Orchestrates the 'daily-scientific-synthesis-0700' cron (0 7 * * * EST).
Triggers the Scaffold-and-Inflate synthesis engine, parallel Drive ingress hook,
and Gmail delivery to dev@mindbyte.net with OIDC Service Account authorization.
"""
import os
import sys
import json
import time
import secrets
from datetime import datetime, timezone
from typing import Dict, Any, Optional

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from synthesis.scientific_engine import ScientificSynthesisEngine
from policies.budget_guardian import BudgetGuardian

CRON_NAME = "daily-scientific-synthesis-0700"
CRON_SCHEDULE = "0 7 * * *"  # 07:00 AM EST / EDT daily
TIMEZONE_STR = "America/New_York"
TARGET_SERVICE_ACCOUNT = "gemini-spark-mcp-sa@gemini-unleashed-core.iam.gserviceaccount.com"

class SynthesisScheduler:
    @staticmethod
    def get_scheduler_job_manifest() -> Dict[str, Any]:
        """Returns the formal Google Cloud Scheduler Job specification."""
        return {
            "name": f"projects/gemini-unleashed-core/locations/us-central1/jobs/{CRON_NAME}",
            "schedule": CRON_SCHEDULE,
            "timeZone": TIMEZONE_STR,
            "httpTarget": {
                "uri": "https://gemini-spark-state-mcp-274212548408.us-central1.run.app/trigger-synthesis",
                "httpMethod": "POST",
                "oidcToken": {
                    "serviceAccountEmail": TARGET_SERVICE_ACCOUNT,
                    "audience": "https://gemini-spark-state-mcp-274212548408.us-central1.run.app"
                },
                "headers": {
                    "Content-Type": "application/json",
                    "User-Agent": "Google-Cloud-Scheduler/1.0"
                },
                "body": json.dumps({"trigger_source": CRON_NAME, "recipient": "dev@mindbyte.net"}).encode("utf-8").decode("utf-8")
            },
            "attemptDeadline": "300s",
            "retryConfig": {
                "retryCount": 3,
                "minBackoffDuration": "5s",
                "maxBackoffDuration": "60s"
            }
        }

    @classmethod
    def execute_scheduled_synthesis_pulse(
        cls,
        dry_run: bool = False,
        recipient_email: str = "dev@mindbyte.net"
    ) -> Dict[str, Any]:
        """
        Executes a complete scheduled pulse of the scientific synthesis pipeline.
        """
        t0 = time.time()
        print(f"=== Triggering Scheduled Pulse: [{CRON_NAME}] ({CRON_SCHEDULE} {TIMEZONE_STR}) ===")
        
        # 1. Budget Gate Check
        b_eval = BudgetGuardian.evaluate_spend(14.20, 0.05)
        if not b_eval.action_allowed:
            print(f"[SynthesisScheduler] Throttled by Budget Guardian ({b_eval.budget_state.value}): {b_eval.reason}")
            return {
                "status": "THROTTLED_BY_BUDGET",
                "budget_state": b_eval.budget_state.value,
                "reason": b_eval.reason
            }

        # 2. Run Engine Pipeline
        res = ScientificSynthesisEngine.execute_daily_synthesis_pipeline(
            recipient_email=recipient_email,
            spend_usd=14.20
        )
        duration_sec = round(time.time() - t0, 3)

        execution_record = {
            "cron_name": CRON_NAME,
            "schedule": CRON_SCHEDULE,
            "timezone": TIMEZONE_STR,
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": duration_sec,
            "synthesis_id": res["report_payload"]["synthesis_id"],
            "word_count": res["report_payload"]["word_count"],
            "equations_count": res["report_payload"]["equations_count"],
            "drive_target_path": res["dispatch_payload"]["drive_target_path"],
            "email_status": res["dispatch_payload"]["delivery_status"],
            "status": "SUCCESS_PULSE_COMPLETED"
        }

        print("\n=== Scheduled Synthesis Pulse Execution Completed ===")
        print(json.dumps(execution_record, indent=2))
        return execution_record

if __name__ == "__main__":
    SynthesisScheduler.execute_scheduled_synthesis_pulse()
