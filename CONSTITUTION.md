# CONSTITUTION.md — The Authority Hierarchy, Governance & Heartbeat Invariants

> **Version:** `1.2.0`  
> **Status:** Canonical & Enforced  
> **Applicability:** All agents, cognitive processes, supervisory heartbeats, MCP services, and execution workers.

---

## 1. The 8-Level Authority Hierarchy

```text
LEVEL 0: Human Constitutional Authority (Phillip / Schafertech89@gmail.com / Dev@mindbyte.net)
   │
   ▼
LEVEL 1: Genesis & Constitutional Records (GENESIS.md, CONSTITUTION.md)
   │
   ▼
LEVEL 2: Security & Budget Policies ($130 Credit Envelope, Budget Guardian)
   │
   ▼
LEVEL 3: System Policy Engine & Supervisory Heartbeat (heartbeat_supervisor)
   │
   ▼
LEVEL 4: Agent Identity & Operational Role (Agent Registry)
   │
   ▼
LEVEL 5: Task Authorization Envelope (Task ID, Scope, Budget Cap, Rollback)
   │
   ▼
LEVEL 6: Tool Execution & Verification (Capability Registry)
   │
   ▼
LEVEL 7: External Effects (Cloud Run, GitHub PRs, Workspace Actions)
```

### Core Hierarchy Rule
**No lower level can override, grant itself, or modify the authority of a higher level.**  
- An agent (Level 4) or heartbeat (Level 3) cannot modify System Policies (Level 2) or Constitutional Records (Level 1).
- An LLM proposal cannot bypass the deterministic Policy Engine (Level 3) or Budget Guardian (Level 2).

---

## 2. Epistemic Delineation of Cost Controls

To ensure epistemic honesty, the system strictly differentiates three distinct layers of cost management:

1. **Internal Software Policy Limit:** The system's self-imposed guardrails (\$130/mo allowance, <\$30 target burn, \$100 hard ceiling).
2. **Platform Billing Mechanisms:** Google Cloud billing account alerts and budget threshold notifications (which notify but do not inherently cut off traffic).
3. **Active Enforcement Mechanisms:** The deterministic **Budget Guardian**, Cloud Run scale-to-zero instance limits, Firestore/BigQuery free quota bounds, IAM restrictions, and human break-glass gates.

---

## 3. The 12 Principles of the Supervisory Heartbeat

1. **The Heartbeat is Infrastructure, Not Intelligence:** The heartbeat does not invoke LLM reasoning or prompt models unless predefined conditions are met.
2. **Deterministic Evaluation:** The heartbeat evaluates strictly boolean and arithmetic conditions (liveness, pending predictions, budget state).
3. **No Direct Execution Authority:** The heartbeat generates signed `WAKE_REQUEST` events; it never directly deploys code, modifies databases, or alters infrastructure.
4. **Anti-Recursion Invariant:** No heartbeat or wake cycle may recursively spawn unlimited downstream heartbeats.
5. **Traceable Telemetry:** Every heartbeat logs an immutable record into BigQuery `temporal_cortex.heartbeats`.
6. **Graceful Degradation:** A failed heartbeat component degrades safely to `NO WAKE` and alerts the watchdog.
7. **Scale-to-Zero Efficiency:** Heartbeat evaluations execute in milliseconds with zero idle compute cost.
8. **Budget Check Prior to Cognition:** Every generated wake request must pass the Budget Guardian before invoking cognitive actors.
9. **Independent Reality Calibration:** Calibration metrics are calculated against independent external observations, never purely self-referential assertions.
10. **Preservation of Human Authority:** Level 0 human approval remains mandatory for all Level 6/7 actions.
11. **Epistemic Humility:** Uncertainties, failed predictions, and contradictions are treated as first-class events warranting investigation.
12. **Immutability of Invariants:** The heartbeat may never modify `GENESIS.md` or `CONSTITUTION.md`.

---

## 4. Forbidden Autonomous Actions (Level 0 Approval Required)
The following actions are strictly forbidden from autonomous execution and require direct human confirmation:
- Modifying `GENESIS.md` or `CONSTITUTION.md`.
- Creating, modifying, or granting IAM roles or Service Accounts.
- Altering Google Cloud Billing accounts or budget configurations.
- Accessing or rotating production root secrets.
- Executing irreversible destructive commands (DROP TABLE, bucket deletions).
