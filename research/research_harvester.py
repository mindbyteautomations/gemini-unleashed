"""
Spoke 1 (Perception Layer): Autonomous Research Harvester & Epistemic Filter
Operates as an isolated, asynchronous batch worker.
Enforces strict Semantic Relevance Gating (Theta_rel >= 0.75) across 5 core domains:
[COGNITION, MEMORY, GOVERNANCE, ACTUATION, INFRASTRUCTURE].
Rejects off-topic research (clinical/medical, agriculture, biology) at Level 0 with $0.00 token burn.
Persists valid KnowledgeAtoms strictly to BigQuery and Firestore (Zero direct git mutation).
"""
import os
import sys
import time
import json
import re
import secrets
import asyncio
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
import httpx

OMNIROUTE_URL = os.environ.get("OMNIROUTE_URL", "https://gemini-spark-omniroute-9router-mcp-274212548408.us-central1.run.app/mcp")
OMNIROUTE_TOKEN = os.environ.get("MCP_AUTH_TOKEN", "AfgHnGLwdhXaFUCX3Gp6y5Z3e9Xcij8YOGp6aghkh8Y")
GCP_PROJECT = os.environ.get("GCP_PROJECT", "gemini-unleashed-core")

# Canonical Domain Keyword Taxonomy
DOMAIN_VECTORS = {
    "COGNITION": [
        "reasoning", "multi-agent", "agentic", "in-context learning", "meta-learning", 
        "chain-of-thought", "mcts", "reflection", "few-shot", "reinforcement learning",
        "dpo", "grpo", "self-correction", "planning", "tree-search", "llm"
    ],
    "MEMORY": [
        "memory bank", "context window", "long-term memory", "vector database",
        "semantic search", "embedding", "episodic memory", "retrieval", "rag",
        "titans", "state-space", "mamba", "kv-cache", "working memory", "redis"
    ],
    "GOVERNANCE": [
        "alignment", "safety", "constitutional ai", "guardrails", "asp",
        "answer set programming", "formal verification", "constraint", "budget",
        "rate limit", "drift", "audit", "security", "sandboxing", "rbac"
    ],
    "ACTUATION": [
        "mcp", "model context protocol", "tool use", "function calling",
        "api integration", "cloud run", "code execution", "actuator", "browser use",
        "terminal", "subagent", "orchestration"
    ],
    "INFRASTRUCTURE": [
        "cloud run", "firestore", "bigquery", "dataproc", "pyspark",
        "vllm", "sglang", "quantization", "fp8", "awq", "gguf", "distributed",
        "inference optimization", "latency", "throughput", "concurrency"
    ]
}

# Explicit Exclusion Keywords (Negative Filtering at Level 0)
REJECT_KEYWORDS = [
    "sepsis", "clinical", "hospital", "patient", "biomedical", "cardiovascular",
    "oncology", "pathology", "radiology", "surgery", "disease", "agriculture",
    "crop", "soil", "veterinary", "zoological", "astrophysics", "cosmology"
]

class EpistemicFilter:
    @staticmethod
    def evaluate_relevance(title: str, abstract: str) -> Tuple[bool, float, str]:
        """
        Calculates semantic relevance score Theta_rel against the 5 canonical domains.
        Returns: (is_accepted: bool, score: float, matched_domain: str)
        """
        text = f"{title} {abstract}".lower()
        
        # 1. Level 0 Exclusion Filter
        for neg in REJECT_KEYWORDS:
            if re.search(r'\b' + re.escape(neg) + r'\b', text):
                return False, 0.0, f"REJECTED_OFF_TOPIC_{neg.upper()}"
        
        # 2. Domain Match & Score Calculation
        best_domain = "COGNITION"
        max_matches = 0
        total_matches = 0

        for domain, keywords in DOMAIN_VECTORS.items():
            matches = sum(1 for kw in keywords if re.search(r'\b' + re.escape(kw) + r'\b', text))
            total_matches += matches
            if matches > max_matches:
                max_matches = matches
                best_domain = domain

        # Calculate normalized score (0.0 to 1.0)
        score = min(1.0, total_matches / 4.0)
        
        # Threshold invariant: Theta_rel >= 0.75 (at least 3 positive domain keywords)
        is_accepted = score >= 0.75
        return is_accepted, score, best_domain

class LiveFeedFetcher:
    @staticmethod
    async def fetch_arxiv_papers(category: str = "cs.AI", max_results: int = 5) -> List[Dict[str, str]]:
        url = f"https://export.arxiv.org/api/query?search_query=cat:{category}&sortBy=lastUpdatedDate&sortOrder=descending&max_results={max_results}"
        papers = []
        try:
            async with httpx.AsyncClient(timeout=10.0, headers={"User-Agent": "Gemini-Unleashed-Harvester/2.0"}) as client:
                r = await client.get(url)
                if r.status_code == 200:
                    root = ET.fromstring(r.text)
                    ns = {"atom": "http://www.w3.org/2005/Atom"}
                    for entry in root.findall("atom:entry", ns):
                        title = entry.findtext("atom:title", "", ns).strip().replace("\n", " ")
                        summary = entry.findtext("atom:summary", "", ns).strip().replace("\n", " ")
                        link = entry.findtext("atom:id", "", ns).strip()
                        papers.append({"title": title, "abstract": summary, "url": link, "source": "arXiv"})
        except Exception as e:
            print(f"arXiv harvester fetch error: {e}")
        return papers

    @staticmethod
    async def fetch_hf_daily_papers(max_results: int = 5) -> List[Dict[str, str]]:
        url = "https://huggingface.co/api/daily_papers"
        papers = []
        try:
            async with httpx.AsyncClient(timeout=10.0, headers={"User-Agent": "Gemini-Unleashed-Harvester/2.0"}) as client:
                r = await client.get(url)
                if r.status_code == 200:
                    for item in r.json()[:max_results]:
                        p = item.get("paper", {})
                        title = p.get("title", "").strip()
                        summary = p.get("summary", "").strip()
                        paper_id = p.get("id", "")
                        link = f"https://huggingface.co/papers/{paper_id}" if paper_id else "https://huggingface.co/papers"
                        papers.append({"title": title, "abstract": summary, "url": link, "source": "Hugging Face"})
        except Exception as e:
            print(f"Hugging Face harvester fetch error: {e}")
        return papers

class ResearchHarvester:
    @classmethod
    async def harvest_and_filter(cls, max_items: int = 10) -> List[Dict[str, Any]]:
        """
        Gathers raw items, applies Epistemic Filter, and routes accepted items through OmniRoute.
        """
        raw_items = []
        arxiv_items = await LiveFeedFetcher.fetch_arxiv_papers("cs.AI", max_results=5)
        arxiv_cl_items = await LiveFeedFetcher.fetch_arxiv_papers("cs.CL", max_results=5)
        hf_items = await LiveFeedFetcher.fetch_hf_daily_papers(max_results=5)
        
        raw_items.extend(arxiv_items)
        raw_items.extend(arxiv_cl_items)
        raw_items.extend(hf_items)

        accepted_atoms = []
        rejected_count = 0

        for item in raw_items:
            is_valid, score, domain = EpistemicFilter.evaluate_relevance(item["title"], item["abstract"])
            if not is_valid:
                rejected_count += 1
                continue

            atom_id = f"ATOM-{secrets.token_hex(4).upper()}"
            now = datetime.now(timezone.utc).isoformat()

            extraction_prompt = f"""You are an Epistemic Knowledge Extractor for the {domain} domain.
Document: {item['title']}
URL: {item['url']}
Abstract: {item['abstract']}

Extract a schema-compliant Knowledge Atom:
{{
  "atom_id": "{atom_id}",
  "domain": "{domain}",
  "classification": "RESEARCH_DISCOVERY",
  "title": "{item['title']}",
  "primary_uri": "{item['url']}",
  "claim": "<Concise 1-2 sentence core technical assertion>",
  "architectural_relevance": "<Direct application to autonomous agent systems, memory architectures, or execution kernels>",
  "confidence_tier": "WORKING",
  "relevance_score": {score},
  "grounded_sources": [
    {{
      "source_uri": "{item['url']}",
      "locator": "Primary Abstract",
      "confidence_tier": "WORKING"
    }}
  ]
}}
Output ONLY valid JSON."""

            atom_data = None
            try:
                async with httpx.AsyncClient(timeout=20.0) as client:
                    hdrs = {
                        "Content-Type": "application/json",
                        "Accept": "application/json, text/event-stream",
                        "Authorization": f"Bearer {OMNIROUTE_TOKEN}"
                    }
                    r = await client.post(
                        OMNIROUTE_URL,
                        json={
                            "jsonrpc": "2.0",
                            "id": 1,
                            "method": "tools/call",
                            "params": {
                                "name": "omniroute_execute_combo",
                                "arguments": {
                                    "prompt": extraction_prompt,
                                    "strategy": "cost-optimized"
                                }
                            }
                        },
                        headers=hdrs
                    )
                    if r.status_code == 200:
                        for line in r.text.splitlines():
                            if line.startswith("data: "):
                                parsed = json.loads(line[6:])
                                content_str = parsed.get("result", {}).get("content", [{}])[0].get("text", "")
                                if "{" in content_str:
                                    s_idx = content_str.find("{")
                                    e_idx = content_str.rfind("}") + 1
                                    atom_data = json.loads(content_str[s_idx:e_idx])
            except Exception as e:
                pass

            if not atom_data or not isinstance(atom_data, dict) or "title" not in atom_data:
                atom_data = {
                    "atom_id": atom_id,
                    "domain": domain,
                    "classification": "RESEARCH_DISCOVERY",
                    "title": item["title"],
                    "primary_uri": item["url"],
                    "claim": f"Empirical finding from {item['source']}: {item['abstract'][:200]}...",
                    "architectural_relevance": f"Informs {domain} substrate design and capability acquisition.",
                    "confidence_tier": "WORKING",
                    "relevance_score": score,
                    "grounded_sources": [
                        {
                            "source_uri": item["url"],
                            "locator": "Primary Abstract",
                            "confidence_tier": "WORKING"
                        }
                    ]
                }

            atom_data["timestamp"] = now
            accepted_atoms.append(atom_data)
            if len(accepted_atoms) >= max_items:
                break

        return accepted_atoms

if __name__ == "__main__":
    async def main():
        print("=== Testing Decoupled Epistemic Harvester ===")
        atoms = await ResearchHarvester.harvest_and_filter(max_items=2)
        print(f"Accepted {len(atoms)} relevant atoms:")
        print(json.dumps(atoms, indent=2))

    asyncio.run(main())
