"""
Componecat Capability Catalog Direct HTTPS Ingress Client
Extracts 17 Cloud Run microservice contracts from schemas/capability_registry.json,
formats a valid ComponecatSyncPayload, and executes direct HTTPS ingestion to
the official Componecat Collection Ingress API (https://app.componecat.ai/api/collections).
Handles HTTP status codes (200/201 vs 401/403/404/500) with authentic network telemetry.
"""
import os
import sys
import json
import time
import secrets
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

COMPONECAT_ORG_ID = "019f8165-da76-74c3-8dce-be745244e59a"
COMPONECAT_DIRECT_API = "https://app.componecat.ai/api/collections"

def compile_componecat_sync_payload() -> Dict[str, Any]:
    registry_path = os.path.join(PROJECT_ROOT, "schemas", "capability_registry.json")
    with open(registry_path, "r", encoding="utf-8") as f:
        reg_data = json.load(f)

    services = reg_data.get("services", [])
    contracts = []
    
    level_1_count = 0
    level_2_count = 0
    level_3_count = 0

    for s in services:
        s_name = s.get("service_name", "")
        r_tier = s.get("risk_class", "LEVEL_2_INTERNAL")
        auth_lvl = s.get("authority_level", 5)
        sla = s.get("sla_latency_target_ms", 1000.0)
        uri = s.get("runtime_uri", "")

        if "LEVEL_1" in r_tier or "LEVEL_0" in r_tier:
            level_1_count += 1
        elif "LEVEL_2" in r_tier:
            level_2_count += 1
        else:
            level_3_count += 1

        for cap in s.get("capabilities", []):
            cap_id = cap.get("name") or cap.get("tool") or f"cap_{s_name}"
            contracts.append({
                "service_name": s_name,
                "capability_id": cap_id,
                "authority_level": auth_lvl,
                "risk_tier": r_tier,
                "endpoint_uri": uri,
                "sla_target_ms": sla
            })

    now_iso = datetime.now(timezone.utc).isoformat()

    payload = {
        "org_id": COMPONECAT_ORG_ID,
        "sync_timestamp": now_iso,
        "total_services": len(services),
        "capability_contracts": contracts,
        "risk_classification_summary": {
            "level_1_count": level_1_count,
            "level_2_count": level_2_count,
            "level_3_count": level_3_count
        }
    }
    return payload

def dispatch_direct_componecat_sync(
    payload: Dict[str, Any],
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Dispatches direct HTTPS POST request to Componecat collections API.
    Captures live HTTP status, headers, and duration.
    """
    json_bytes = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "GeminiUnleashed-ComponecatSync/2.0",
        "X-Componecat-Organization": COMPONECAT_ORG_ID
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    req = urllib.request.Request(COMPONECAT_DIRECT_API, data=json_bytes, headers=headers, method="POST")
    t0 = time.time()

    try:
        with urllib.request.urlopen(req, timeout=10.0) as resp:
            status_code = resp.status
            resp_body = resp.read().decode("utf-8")
            duration_ms = (time.time() - t0) * 1000.0
            
            return {
                "http_status": status_code,
                "endpoint": COMPONECAT_DIRECT_API,
                "duration_ms": round(duration_ms, 2),
                "response": resp_body[:1000],
                "verified": status_code in (200, 201)
            }
    except urllib.error.HTTPError as he:
        duration_ms = (time.time() - t0) * 1000.0
        err_body = he.read().decode("utf-8", errors="ignore")
        return {
            "http_status": he.code,
            "endpoint": COMPONECAT_DIRECT_API,
            "duration_ms": round(duration_ms, 2),
            "error_reason": str(he.reason),
            "response": err_body[:500],
            "verified": False
        }
    except Exception as e:
        duration_ms = (time.time() - t0) * 1000.0
        return {
            "http_status": 0,
            "endpoint": COMPONECAT_DIRECT_API,
            "duration_ms": round(duration_ms, 2),
            "error": str(e),
            "verified": False
        }

def execute_componecat_sync() -> Dict[str, Any]:
    payload = compile_componecat_sync_payload()
    print(f"=== Initiating Direct Componecat HTTPS Sync [{COMPONECAT_ORG_ID}] ===")
    print(f"Target Endpoint: {COMPONECAT_DIRECT_API}")
    print(f"Total Services: {payload['total_services']} | Contracts: {len(payload['capability_contracts'])}")

    telemetry = dispatch_direct_componecat_sync(payload)
    print(f"Direct Ingress Result: HTTP {telemetry['http_status']} ({telemetry['duration_ms']}ms)")

    sync_record = {
        "sync_payload": payload,
        "transmission_telemetry": telemetry,
        "recorded_at": datetime.now(timezone.utc).isoformat()
    }
    
    out_path = os.path.join(PROJECT_ROOT, "schemas", "componecat_live_sync.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(sync_record, f, indent=2)

    return sync_record

if __name__ == "__main__":
    execute_componecat_sync()
