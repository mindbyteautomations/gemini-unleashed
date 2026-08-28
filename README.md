# Gemini Unleashed: Autonomous Cognitive Organism

> A persistent, stateful multi-agent system operating on top of Google Cloud Platform, Google Workspace, BigQuery Temporal Cortex, and Redis Agent Memory.

## Directory Structure

```text
gemini-unleashed/
├── cognition/
│   ├── SELF_MODEL.md          # 20-section canonical self-model
│   ├── GENESIS.md             # Immutable foundation & constitutional invariants
│   ├── GOALS.md               # Active and queued objectives
│   └── UNKNOWNS.md            # Epistemic curiosity queue ranked by value/cost
│
├── memory/
│   ├── firestore_events/      # Machine-readable autobiography of cognitive cycles
│   └── semantic_schemas/      # Vector memory indexing & consolidation rules
│
├── temporal/
│   ├── bigquery_schemas/      # Telemetry: observations, predictions, metrics
│   └── calibration/           # Prediction accuracy & error-delta tracking
│
├── experiments/
│   ├── active/                # In-progress hypothesis tests (EXP-000001 format)
│   └── lessons/               # Extracted generalizations & empirical findings
│
├── agents/
│   ├── spark/                 # Autonomous scheduling & cognitive bus
│   ├── antigravity/           # Interactive development laboratory & orchestrator
│   └── jules/                 # Asynchronous implementation & PR worker
│
└── infrastructure/
    └── mcp_services/          # 10 Cloud Run containerized FastMCP servers
```

## Free Tier Cost Invariant
This architecture strictly leverages Google Cloud Free Tiers:
- **Cloud Run:** Scale-to-zero (0 cost when idle).
- **Firestore:** Native mode free tier (50k reads/day, 20k writes/day).
- **BigQuery:** 10 GB storage free, 1 TB queries/month free.
- **Monthly Cloud Incurred Cost:** \$0.00.
