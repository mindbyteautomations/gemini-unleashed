# Canonical Active System Summary (CAP v1.0 / $I_{\text{gate}}$ Normalized)

> **Generated At:** 2026-08-29T04:10:00Z  
> **Target GCP Project:** `gemini-unleashed-core` (#`274212548408`, Region: `us-central1`)  
> **Constitutional Status:** 100% COMPLIANT (CAP v1.0, Ingestion Gate $I_{\text{gate}}$, State Invariant $I_{\text{state}}$)  
> **Active Milestone:** Sprint 1 — Jules Adversarial Testing Harness & Codex Capabilities Integration  

---

## 1. Microservice Ecosystem & Runtime Map (16/16 Active Services)

| Service Name | Architectural Role & Spoke | Endpoint / URI | Latency Benchmark | Security & Auth |
| :--- | :--- | :--- | :--- | :--- |
| `gemini-spark-state-mcp` | Spoke 2: Autonomic State & Pub/Sub Gateway | `https://gemini-spark-state-mcp-274212548408.us-central1.run.app` | **0.05ms** (SLO <50ms) | OAuth 2.0 / Bearer + `/launch-dataproc-etl` |
| `gemini-spark-research-harvester` | Spoke 1: Epistemic Harvester (Vertex AI 768d) | `https://gemini-spark-research-harvester-274212548408.us-central1.run.app` | ~2,500ms | OIDC SA Token (`--no-allow-unauthenticated`) |
| `gemini-spark-episodic-memory-mcp` | Spoke 2: Internal Episodic Memory (Firestore v1.0.0) | `https://gemini-spark-episodic-memory-mcp-274212548408.us-central1.run.app` | <50ms | Zero-Trust OIDC / MCP Token (`--no-allow-unauthenticated`) |
| `gemini-spark-omniroute-9router-mcp` | Inference Hub: Multi-Model Gateway & Free Pool | `https://gemini-spark-omniroute-9router-mcp-274212548408.us-central1.run.app/mcp` | ~3,000ms | MCP Token Header |
| `gemini-spark-componecat-mcp` | Spoke 4: Capability & Component Catalog | `https://gemini-spark-componecat-mcp-274212548408.us-central1.run.app` | <100ms | OAuth 2.0 / Bearer |
| `gemini-spark-workspace-admin-mcp`| Spoke 3: Google Workspace DWD Administration | `https://gemini-spark-workspace-admin-mcp-274212548408.us-central1.run.app` | <1,200ms | DWD Super-Admin SA |
| `gemini-spark-github-mcp` | Spoke 5: Versioned Canonical Ledger & AST | `https://gemini-spark-github-mcp-274212548408.us-central1.run.app` | <2,500ms | Secret Manager PAT |

---

## 2. Multi-Topic Telemetry & Grounding Sinks

```
[ gemini-spark-state-mcp ]
           │ (0.05ms Sync Publish)
           ▼
[ Pub/Sub: heartbeat-telemetry-sink ] ──► [ Direct BQ: heartbeat-telemetry-bq-sub ] ──► [ BigQuery: temporal_cortex.heartbeats ]
                                                        │ (After 5 failed attempts)
                                                        ▼
[ Pub/Sub: observations-telemetry-sink ] ──► [ Direct BQ: observations-telemetry-bq-sub ] ──► [ BigQuery: temporal_cortex.observations ]
                                                        │ (After 5 failed attempts)
                                                        ▼
                                       [ Dead-Letter Topic: cognitive-telemetry-dlq ] ──► [ Subscription: cognitive-telemetry-dlq-sub ]
```

---

## 3. Automated Data Metabolism Layer (Dataproc Serverless PySpark)

- **Main Script:** `gs://gemini-unleashed-core-spark/pipelines/dataproc_knowledge_etl.py`
- **Dynamic Launcher:** `POST https://gemini-spark-state-mcp-274212548408.us-central1.run.app/launch-dataproc-etl`
- **Scheduled Trigger:** Cloud Scheduler job `dataproc-knowledge-etl-daily` (`0 6 * * *` UTC)
- **Execution Mode:** Clusterless Dataproc Serverless Batch with `roles/bigquery.readSessionUser`
- **Grounding Synchronization:** Outputs `gs://gemini-unleashed-core-spark/artifacts/ACTIVE_SUMMARY.md` and atomically updates Firestore `cortex/canonical_state`.

---

## 4. State Plane Segregation & Governance Boundaries

1. **Gemini Spark SaaS Isolation:** The 30MB Redis Cloud SaaS instance (`gcp-us-east4.memory.redis.io`, Store ID `2809754f6de54933a262d320c7cd7f58`) is strictly quarantined for the consumer Gemini Spark web interface.
2. **Internal Agent Core Substrate:** Internal agent working memory, task deduplication, and distributed locks reside exclusively within Google Cloud native storage (`Firestore Native`, `BigQuery`, and `Cloud Pub/Sub`).
3. **Distributed Mutual Exclusion & Clock Invariance:** Server-side transactional leases (`locks/research_harvester`, 240s TTL) enforce atomic `firestore.SERVER_TIMESTAMP` transforms to eliminate host NTP clock drift. Mutex skips return `HTTP 200 OK` (`noop_lease_active`) to terminate scheduled crons without retry storms.
