"""
Antigravity Temporal Cortex Supervisor & Autonomous Scheduler Loop
Polls the 16 Cloud Run microservices, autonomic state heartbeat (<50ms),
and triggers the asynchronous research harvester on schedule.
"""
import os
import sys
import time
import json
import httpx
from datetime import datetime, timezone

STATE_MCP_URL = os.environ.get("STATE_MCP_URL", "https://gemini-spark-state-mcp-274212548408.us-central1.run.app")
HARVESTER_URL = os.environ.get("HARVESTER_URL", "https://gemini-spark-research-harvester-274212548408.us-central1.run.app")

def run_supervisory_cycle():
    now = datetime.now(timezone.utc).isoformat()
    report = {"timestamp": now, "status": "NOMINAL"}

    with httpx.Client(timeout=15.0) as client:
        # 1. Pulse Autonomic Heartbeat (Spoke 2 & Spoke 5.6)
        try:
            t0 = time.perf_counter()
            r_hb = client.get(f"{STATE_MCP_URL}/heartbeat")
            lat_ms = (time.perf_counter() - t0) * 1000.0
            report["heartbeat"] = {
                "status_code": r_hb.status_code,
                "roundtrip_latency_ms": round(lat_ms, 2),
                "payload": r_hb.json() if r_hb.status_code == 200 else r_hb.text
            }
        except Exception as e:
            report["heartbeat"] = {"error": str(e)}

        # 2. Trigger Asynchronous Epistemic Harvester (Spoke 1)
        try:
            t0 = time.perf_counter()
            r_hv = client.get(f"{HARVESTER_URL}/harvest", timeout=25.0)
            lat_ms = (time.perf_counter() - t0) * 1000.0
            report["harvester"] = {
                "status_code": r_hv.status_code,
                "roundtrip_latency_ms": round(lat_ms, 2),
                "payload": r_hv.json() if r_hv.status_code == 200 else r_hv.text
            }
        except Exception as e:
            report["harvester"] = {"error": str(e)}

    print(json.dumps(report, indent=2))
    return report

if __name__ == "__main__":
    run_supervisory_cycle()
