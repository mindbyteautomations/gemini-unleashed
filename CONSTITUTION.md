# CONSTITUTION.md — The Authority Hierarchy & Operational Invariants

> **Status:** Canonical & Enforced  
> **Applicability:** All agents, cognitive processes, MCP services, and execution workers.

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
LEVEL 3: System Policy Engine & Constitutional Firewall
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
- An agent (Level 4) cannot modify System Policies (Level 2/3) or Constitutional Records (Level 1).
- An LLM proposal cannot bypass the deterministic Policy Engine (Level 3) or Budget Guardian (Level 2).

---

## 2. The Three Questions of Governance

Before any tool is executed, three independent gates must pass:

1. **CAPABILITY (Can the system do this?):** Does the tool exist and function?
2. **AUTHORIZATION (Is this actor allowed to do this?):** Does the requesting agent's role permit this risk level?
3. **CONTEXT (Is it permitted NOW, for THIS task?):** Does the active Task Envelope explicitly authorize this scope, budget, and action?

---

## 3. Strict Budget Invariant ($130 Monthly Envelope)

1. **Monthly Credit Allowance:** \$130.00 / month.
2. **Target Operational Burn:** <\$30.00 / month.
3. **Automated Throttling (YELLOW: \$30–\$60/mo):** Background research throttled.
4. **Automated Freeze (ORANGE: \$60–\$80/mo):** All automated research suspended.
5. **Hard Circuit Breaker (RED: \$80–\$100/mo):** All autonomous execution halted.
6. **Zero Out-of-Pocket Guarantee:** Under no circumstances may an agent perform actions that risk billing beyond available cloud credits.

---

## 4. Forbidden Autonomous Actions (Level 0 Approval Required)
The following actions are strictly forbidden from autonomous execution and require direct human confirmation:
- Modifying `GENESIS.md` or `CONSTITUTION.md`.
- Creating, modifying, or granting IAM roles or Service Accounts.
- Altering Google Cloud Billing accounts or budget configurations.
- Accessing or rotating production root secrets.
- Executing irreversible destructive commands (DROP TABLE, deletion of storage buckets).
