# Canonical Active System Summary (CAP v1.0 / $I_{\text{gate}}$ Normalized)

> **Generated At:** 2026-08-29T03:37:00Z  
> **Target GCP Project:** `gemini-unleashed-core` (#`274212548408`, Region: `us-central1`)  
> **Constitutional Status:** 100% COMPLIANT (CAP v1.0, Ingestion Gate $I_{\text{gate}}$, State Invariant $I_{\text{state}}$)

---

## 1. Microservice Ecosystem & Runtime Map (16/16 Active Services)

| Service Name | Architectural Role & Spoke | Endpoint / URI | Latency Benchmark | Security & Auth |
| :--- | :--- | :--- | :--- | :--- |
| `gemini-spark-state-mcp` | Spoke 2: Autonomic State & Pub/Sub Gateway | `https://gemini-spark-state-mcp-274212548408.us-central1.run.app` | **0.04ms** (SLO <50ms) | OAuth 2.0 / Bearer |
| `gemini-spark-research-harvester` | Spoke 1: Epistemic Harvester (Vertex AI 768d) | `https://gemini-spark-research-harvester-274212548408.us-central1.run.app` | ~2,500ms | OIDC SA Token (`--no-allow-unauthenticated`) |
| `gemini-spark-omniroute-9router-mcp` | Inference Hub: Multi-Model Gateway & Free Pool | `https://gemini-spark-omniroute-9router-mcp-274212548408.us-central1.run.app/mcp` | ~3,000ms | MCP Token Header |
| `gemini-spark-episodic-memory-mcp` | Spoke 2: Internal Episodic Memory & LangCache | `https://gemini-spark-redis-memory-mcp-274212548408.us-central1.run.app` | <50ms | MCP Token Header |
| `gemini-spark-componecat-mcp` | Spoke 4: Capability & Component Catalog | `https://gemini-spark-componecat-mcp-274212548408.us-central1.run.app` | <100ms | OAuth 2.0 / Bearer |
| `gemini-spark-workspace-admin-mcp`| Spoke 3: Google Workspace DWD Administration | `https://gemini-spark-workspace-admin-mcp-274212548408.us-central1.run.app` | <1,200ms | DWD Super-Admin SA |
| `gemini-spark-github-mcp` | Spoke 5: Versioned Canonical Ledger & AST | `https://gemini-spark-github-mcp-274212548408.us-central1.run.app` | <2,500ms | Secret Manager PAT |

---

## 2. Telemetry Persistence Pipeline (Direct BigQuery + Dead-Letter Queue)

```
[ gemini-spark-state-mcp ]
           │ (0.04ms Sync Publish)
           ▼
[ Pub/Sub: cognitive-telemetry-sink ]
           │
           ├─► [ Direct Ingestion: cognitive-telemetry-bq-sub ] ──► [ BigQuery: temporal_cortex.heartbeats ]
           │                      │ (After 5 failed attempts)
           │                      ▼
           └────────────────► [ Dead-Letter Topic: cognitive-telemetry-dlq ] ──► [ Subscription: cognitive-telemetry-dlq-sub ]
```

---

## 3. Epistemic Curiosity Engine (768-dim Continuous Vector Geometry)

$$\mathcal{C}(U) = \frac{\max_{\text{domain}}(\cos(\vec{d}, \vec{C}_{\text{domain}})) \cdot I(U) \cdot R(U)}{C_{\text{est}} + \epsilon}$$

- **Vector Model:** Vertex AI `text-embedding-004` (768 continuous dimensions)
- **Domain Centroids:** Pre-computed 768-dim embeddings for `COGNITION`, `MEMORY`, `GOVERNANCE`, `ACTUATION`, `INFRASTRUCTURE`.
- **Gating Invariant:** Requires $\text{CosineSim} \ge 0.55$ and normalized $\mathcal{C}(U) \ge 0.35$.
- **Ingestion Sources:** arXiv Atom API (`cs.AI`, `cs.CL`, `cs.LG`) and Hugging Face Daily Papers API.

---

## 4. State Plane Segregation & Governance Boundaries

1. **Gemini Spark SaaS Isolation:** The 30MB Redis Cloud SaaS instance (`gcp-us-east4.memory.redis.io`, Store ID `2809754f6de54933a262d320c7cd7f58`) is strictly quarantined for the consumer Gemini Spark web interface.
2. **Internal Agent Core Substrate:** Internal agent working memory, task deduplication, and distributed locks reside exclusively within Google Cloud native storage (`Firestore Native`, `BigQuery`, and `Cloud Pub/Sub`).
3. **Distributed Mutual Exclusion:** `heartbeat/scheduler.py` enforces distributed lease locking on `locks/heartbeat_supervisor` (240s TTL) to prevent dual-scheduler split-brain race conditions.
