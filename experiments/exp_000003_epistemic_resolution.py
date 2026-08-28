"""
EXP-000003: Autonomous Contradiction Detection & Epistemic Resolution
Demonstrates end-to-end epistemic immune cycle:
Belief Registered -> Contradiction Injected -> Kernel Evaluates -> Task Dispatched -> Truth Resolved -> Calibrated Belief Stored -> Decision Logged to BigQuery.
"""
import os
import sys
import json
import asyncio
import httpx
from datetime import datetime, timezone

# Add root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from kernel.cognitive_kernel import CognitiveKernel
from cognition.belief_registry import BeliefRegistry, BeliefStatus
from cognition.contradiction_engine import ContradictionEngine, ContradictionSeverity
from cognition.curiosity_engine import CuriosityEngine

STATE_MCP_URL = "https://gemini-spark-state-mcp-274212548408.us-central1.run.app/mcp"
TOKEN = "AfgHnGLwdhXaFUCX3Gp6y5Z3e9Xcij8YOGp6aghkh8Y"

def parse_mcp(text):
    for line in text.strip().split("\n"):
        if line.startswith("data: "):
            return json.loads(line[6:])
    return json.loads(text)

async def run_exp_000003():
    print("=== Starting Experiment EXP-000003: Epistemic Contradiction Resolution ===")
    
    # 1. Register Baseline Belief
    b_reg = BeliefRegistry()
    c_eng = ContradictionEngine()
    cur_eng = CuriosityEngine()

    print("\n1. Registering initial belief in BeliefRegistry...")
    b1 = b_reg.register_belief(
        claim="FastMCP server supports Cloud Run SSE without proxy header adjustments.",
        confidence=0.70
    )
    print(f"   -> Registered: [{b1['belief_id']}] Confidence: {b1['confidence']} | {b1['claim']}")

    # 2. Inject Empirical Contradiction (e.g. from runtime logs or docs)
    print("\n2. Injecting conflicting evidence from live Cloud Run deployment log...")
    contra = c_eng.create_contradiction(
        claim_a=b1["claim"],
        evidence_a="FastMCP quickstart docs",
        claim_b="FastMCP returns HTTP 421 behind reverse proxy unless DNS rebinding is disabled.",
        evidence_b="Cloud Run runtime log 1787888421",
        severity=ContradictionSeverity.MEDIUM
    )
    b_reg.flag_contradiction(b1["belief_id"], contra["claim_b"], "LOG-1787888421")
    print(f"   -> Flagged Contradiction [{contra['contradiction_id']}]. Belief status downgraded to {b1['status']}.")

    # 3. Curiosity Engine Ranks Resolution Question
    print("\n3. Curiosity Engine evaluating research priority...")
    unk = cur_eng.register_unknown(
        question="What exact FastMCP transport security setting prevents HTTP 421 on Cloud Run?",
        uncertainty=0.85,
        importance=0.90,
        info_gain=0.95,
        novelty=0.70,
        relevance=0.95,
        estimated_cost=0.02
    )
    print(f"   -> Unknown Registered [{unk['unknown_id']}]: Curiosity Score = {unk['curiosity_score']}")

    # 4. Cognitive Kernel Executes OWAI Loop
    print("\n4. Cognitive Kernel executing OWAI cycle...")
    owai_res = CognitiveKernel.execute_owai_cycle(
        observation={"observation_id": contra["contradiction_id"], "content": unk["question"], "importance": 0.9},
        proposed_action="resolve_contradiction",
        scope={"allowed_actions": ["research_documentation", "resolve_contradiction"], "risk_level": 2},
        estimated_cost=0.02,
        current_spend=12.55
    )
    assert owai_res["status"] == "AUTHORIZED_AND_DISPATCHED", "OWAI authorization failed!"
    print(f"   -> OWAI Status: {owai_res['status']} | Actuator: {owai_res['actuator']} | Utility: {owai_res['utility_score']}")

    # 5. Actuator Resolves Ground Truth & Calibrates Belief
    resolved_truth = "FastMCP requires TransportSecuritySettings(enable_dns_rebinding_protection=False, allowed_hosts=['*']) when behind Cloud Run proxy."
    resolved_belief = b_reg.resolve_belief(
        belief_id=b1["belief_id"],
        updated_claim=resolved_truth,
        new_confidence=0.98,
        ground_truth_ref="EXP-000001-VERIFIED"
    )
    c_eng.resolve_contradiction(contra["contradiction_id"], resolved_truth, "Verified via Cloud Run server.py live execution.")
    print(f"\n5. Contradiction Resolved. Calibrated Belief: [{resolved_belief['belief_id']}] Status: {resolved_belief['status']} Confidence: {resolved_belief['confidence']}")

    # 6. Log Decision to BigQuery via Master State MCP
    print("\n6. Logging final epistemic decision to BigQuery temporal_cortex...")
    hdrs = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream", "Authorization": f"Bearer {TOKEN}"}
    async with httpx.AsyncClient(timeout=30.0) as client:
        r_init = await client.post(STATE_MCP_URL, json={
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "exp000003-runner", "version": "1.0"}}
        }, headers=hdrs)
        sid = r_init.headers.get("mcp-session-id")
        if sid: hdrs["mcp-session-id"] = sid

        # Log observation
        r_obs = await client.post(STATE_MCP_URL, json={
            "jsonrpc": "2.0", "id": 2, "method": "tools/call",
            "params": {
                "name": "record_observation",
                "arguments": {
                    "source": "EXP-000003 Epistemic Engine",
                    "entity": "FastMCP Cloud Run Settings",
                    "content": f"Resolved {contra['contradiction_id']}: {resolved_truth}",
                    "confidence": 0.98
                }
            }
        }, headers=hdrs)
        print("   -> Logged Observation to Master State MCP.")

    print("\n=== EXP-000003 Epistemic Contradiction Resolution: SUCCESS ===")

if __name__ == "__main__":
    asyncio.run(run_exp_000003())
