# INVENTORY.md — Genesis 1.1 Infrastructure & Services Inventory

> **Inventory Date:** `2026-08-28T04:28:00Z`  
> **GCP Project:** `gemini-unleashed-core` (Project #`274212548408`, Region: `us-central1`)  
> **Monthly Budget Allowance:** \$130.00 / month (Target Burn: <\$30.00/mo, Hard Ceiling: \$100.00/mo)

---

## 1. Cloud Run MCP Services (11 Deployed Microservices)

All microservices run on Cloud Run with Scale-to-Zero ($0.00 idle compute cost) and RFC 8414 OAuth 2.0 Discovery.

| Service Name | Cloud Run URL | Primary Responsibility |
| :--- | :--- | :--- |
| **`gemini-spark-state-mcp`** | `https://gemini-spark-state-mcp-274212548408.us-central1.run.app` | Master State, Cognitive Cycles, Event Ledger, Temporal Cortex |
| **`gemini-spark-workspace-admin-mcp`** | `https://gemini-spark-workspace-admin-mcp-274212548408.us-central1.run.app` | 55 Tools for Google Workspace, Gmail, Drive, Docs, Admin |
| **`gemini-spark-github-mcp`** | `https://gemini-spark-github-mcp-274212548408.us-central1.run.app` | GitHub Repo Management, Branches, PRs, Code Search |
| **`gemini-spark-cli-mcp`** | `https://gemini-spark-cli-mcp-274212548408.us-central1.run.app` | Cloud SDK, Vertex AI, BigQuery, Cloud Storage runner |
| **`gemini-spark-context7-mcp`** | `https://gemini-spark-context7-mcp-274212548408.us-central1.run.app` | Real-time Library Docs Resolution & Google ADC |
| **`gemini-spark-jules-cli-mcp`** | `https://gemini-spark-jules-cli-mcp-274212548408.us-central1.run.app` | Google Jules CLI Agent Execution & Tasks |
| **`gemini-spark-jules-api-mcp`** | `https://gemini-spark-jules-api-mcp-274212548408.us-central1.run.app` | Google Jules REST API Integration |
| **`gemini-spark-stitch-mcp`** | `https://gemini-spark-stitch-mcp-274212548408.us-central1.run.app` | Google Stitch UI Design System & Screen Generator |
| **`gemini-spark-nvidia-nim-mcp`** | `https://gemini-spark-nvidia-nim-mcp-274212548408.us-central1.run.app` | NVIDIA NIM Catalog, Model Cards, Inference Hub |
| **`gemini-spark-developer-knowledge-mcp`** | `https://gemini-spark-developer-knowledge-mcp-274212548408.us-central1.run.app` | Google Grounded Search across 13 developer domains |
| **`gemini-spark-antigravity-sdk-mcp`** | `https://gemini-spark-antigravity-sdk-mcp-274212548408.us-central1.run.app` | Exhaustive 13 Antigravity SDK Tool Definitions |
| **`gemini-spark-componecat-mcp`** | `https://gemini-spark-componecat-mcp-274212548408.us-central1.run.app` | ComponeCat UI component design and generation bridge |
| **`gemini-spark-copilot-mcp`** | `https://gemini-spark-copilot-mcp-274212548408.us-central1.run.app` | Full GitHub Copilot features: GPT-4o, Claude 3.5 Sonnet, o1, code review, test generator |
| **`gemini-spark-omniroute-9router-mcp`** | `https://gemini-spark-omniroute-9router-mcp-274212548408.us-central1.run.app` | Synthesized OmniRoute + 9Router AI Gateway: 100% free-tier models & RTK token compression |

---

## 2. Databases & Storage Substrates

| Substrate | Instance / Dataset | Free Tier Policy |
| :--- | :--- | :--- |
| **Firestore Native** | `projects/gemini-unleashed-core/databases/(default)` (us-central1) | 50,000 reads/day, 20,000 writes/day, 1GB storage ($0.00) |
| **BigQuery Temporal Cortex** | `gemini-unleashed-core:temporal_cortex` (us-central1) | 10 GB storage free, 1 TB queries processed/month ($0.00) |
| **Redis Agent Memory** | `https://gcp-us-east4.memory.redis.io` (Store ID: `2809754f6de54933a262d320c7cd7f58`) | 30 MB fixed memory plan ($0.00) |
| **Google Cloud Storage** | `gs://run-sources-gemini-unleashed-core-us-central1` | Source code artifacts & builds |

---

## 3. Service Accounts & Identities

| Service Account | Role / Purpose |
| :--- | :--- |
| **`gemini-spark-mcp-sa@gemini-unleashed-core.iam.gserviceaccount.com`** | Runtime service account for Cloud Run MCP servers (DWD Client ID: `101699370717430009479`) |
| **`gemini-unleashed-agent@gemini-unleashed-core.iam.gserviceaccount.com`** | AI Platform & Datastore User |
| **`vertex-express@gemini-unleashed-core.iam.gserviceaccount.com`** | Vertex AI Express User |
