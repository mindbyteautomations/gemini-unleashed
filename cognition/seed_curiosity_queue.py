"""
Seed Curiosity Queue — Initial Knowledge & Epistemic Research Seeder
Populates Firestore Native (unknowns/), BigQuery Temporal Cortex, and local registries
with high-value, mathematically ranked research questions.
"""
import os
import sys
import json
import secrets
import httpx
import asyncio
from datetime import datetime, timezone

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from cognition.curiosity_engine import CuriosityEngine

STATE_MCP_URL = "https://gemini-spark-state-mcp-274212548408.us-central1.run.app/mcp"
TOKEN = "AfgHnGLwdhXaFUCX3Gp6y5Z3e9Xcij8YOGp6aghkh8Y"

INITIAL_CURIOSITY_ITEMS = [
    {
        "question": "How to optimize BigQuery partition pruning on temporal_cortex tables to minimize query scanning costs for high-frequency heartbeat queries?",
        "domain": "Temporal Cortex Telemetry",
        "uncertainty": 0.85,
        "importance": 0.95,
        "info_gain": 0.90,
        "novelty": 0.70,
        "relevance": 0.95,
        "cost": 0.01
    },
    {
        "question": "What is the optimal embedding dimensions and index type in Redis Agent Memory to achieve sub-5ms semantic recall across 10,000+ episodic interactions?",
        "domain": "Semantic Memory",
        "uncertainty": 0.80,
        "importance": 0.90,
        "info_gain": 0.85,
        "novelty": 0.80,
        "relevance": 0.90,
        "cost": 0.02
    },
    {
        "question": "How can Antigravity and Jules collaborate hierarchically where Antigravity architects multi-agent plans and Jules executes isolated pull request workers?",
        "domain": "Multi-Agent Engineering",
        "uncertainty": 0.90,
        "importance": 0.95,
        "info_gain": 0.95,
        "novelty": 0.85,
        "relevance": 0.95,
        "cost": 0.03
    },
    {
        "question": "What NVIDIA NIM models on build.nvidia.com provide the highest reasoning benchmark per token for secondary hypothesis verification?",
        "domain": "Model Ecosystems",
        "uncertainty": 0.75,
        "importance": 0.85,
        "info_gain": 0.80,
        "novelty": 0.90,
        "relevance": 0.85,
        "cost": 0.01
    },
    {
        "question": "How can Cloud Run container concurrency and CPU startup boost be tuned to achieve zero-cost cold starts while handling bursty MCP traffic?",
        "domain": "Cloud Infrastructure",
        "uncertainty": 0.70,
        "importance": 0.90,
        "info_gain": 0.80,
        "novelty": 0.60,
        "relevance": 0.90,
        "cost": 0.01
    },
    {
        "question": "What mathematical formula best balances exploration of novel capabilities vs exploitation of verified skills under a strict $130 monthly credit budget?",
        "domain": "Epistemic Economics",
        "uncertainty": 0.95,
        "importance": 0.95,
        "info_gain": 0.95,
        "novelty": 0.90,
        "relevance": 0.95,
        "cost": 0.02
    },
    {
        "question": "How can Google Workspace Alert Center API be integrated into the supervisory heartbeat to detect suspicious phishing or security anomalies in mindbyte.net?",
        "domain": "Security & Workspace",
        "uncertainty": 0.80,
        "importance": 0.85,
        "info_gain": 0.85,
        "novelty": 0.75,
        "relevance": 0.85,
        "cost": 0.01
    },
    {
        "question": "What automated statistical test can reliably verify whether an agent's confidence calibration is improving over time without human intervention?",
        "domain": "Metacognitive Calibration",
        "uncertainty": 0.90,
        "importance": 0.90,
        "info_gain": 0.90,
        "novelty": 0.85,
        "relevance": 0.90,
        "cost": 0.02
    }
]

def parse_mcp(text):
    for line in text.strip().split("\n"):
        if line.startswith("data: "):
            return json.loads(line[6:])
    return json.loads(text)

async def seed_curiosity_queue():
    print("=== Seeding Initial Curiosity Queue ===")
    engine = CuriosityEngine()
    seeded_items = []

    # 1. Rank items locally
    for item in INITIAL_CURIOSITY_ITEMS:
        unk = engine.register_unknown(
            question=item["question"],
            uncertainty=item["uncertainty"],
            importance=item["importance"],
            info_gain=item["info_gain"],
            novelty=item["novelty"],
            relevance=item["relevance"],
            estimated_cost=item["cost"]
        )
        unk["domain"] = item["domain"]
        seeded_items.append(unk)

    ranked_items = sorted(seeded_items, key=lambda x: x["curiosity_score"], reverse=True)

    # 2. Write to local cognition/UNKNOWNS.md
    md_lines = [
        "# UNKNOWNS.md — Active Epistemic Curiosity Queue\n\n",
        f"> **Last Updated:** `{datetime.now(timezone.utc).isoformat()}`\\\n",
        f"> **Total Ranked Unknowns:** `{len(ranked_items)}`\\\n",
        "> **Formula:** $\\text{Curiosity} = \\frac{\\text{Uncertainty} \\times \\text{Importance} \\times \\text{InfoGain} \\times \\text{Novelty} \\times \\text{Relevance}}{\\text{Cost} + 0.10} \\times 10$\n\n---\n\n"
    ]

    for rank, unk in enumerate(ranked_items, 1):
        md_lines.append(f"### {rank}. `[{unk['unknown_id']}]` {unk['domain']} (Score: **{unk['curiosity_score']}**)\n")
        md_lines.append(f"**Question:** {unk['question']}\\\n")
        md_lines.append(f"**Parameters:** Uncertainty: `{unk['uncertainty']}` &bull; Importance: `{unk['importance']}` &bull; Estimated Cost: `\\${unk['estimated_cost_usd']:.2f}` &bull; Status: `{unk['status']}`\n\n")

    with open("cognition/UNKNOWNS.md", "w", encoding="utf-8") as f:
        f.writelines(md_lines)
    print("Saved ranked queue to cognition/UNKNOWNS.md")

    # 3. Stream to Master State MCP (Firestore + BigQuery)
    hdrs = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Authorization": f"Bearer {TOKEN}"
    }

    async with httpx.AsyncClient(timeout=45.0) as client:
        r_init = await client.post(STATE_MCP_URL, json={
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "curiosity-seeder", "version": "1.0"}}
        }, headers=hdrs)
        sid = r_init.headers.get("mcp-session-id")
        if sid: hdrs["mcp-session-id"] = sid

        print("\nStreaming top ranked unknowns into Firestore Native & BigQuery...")
        for unk in ranked_items[:5]:
            r_unk = await client.post(STATE_MCP_URL, json={
                "jsonrpc": "2.0", "id": 2, "method": "tools/call",
                "params": {
                    "name": "record_unknown",
                    "arguments": {
                        "question": unk["question"],
                        "importance": unk["importance"],
                        "estimated_cost": unk["estimated_cost_usd"]
                    }
                }
            }, headers=hdrs)
            res_text = parse_mcp(r_unk.text).get("result", {}).get("content", [{}])[0].get("text", "")
            print(f" -> Recorded: [{unk['unknown_id']}] (Score: {unk['curiosity_score']:5.2f})")

    print("\n=== Curiosity Queue Successfully Populated and Active ===")

if __name__ == "__main__":
    asyncio.run(seed_curiosity_queue())
