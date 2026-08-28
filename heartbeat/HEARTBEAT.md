# HEARTBEAT.md — The Deterministic Supervisory Subsystem

> **Module:** `heartbeat/`  
> **Identity:** `heartbeat_supervisor` (Authority Level 3)  
> **Execution Model:** Deterministic, scale-to-zero, event-driven supervisor.

---

## 1. Role & Purpose
The **Heartbeat** is the temporal clock and supervisor of the cognitive system. Its purpose is to answer one fundamental question deterministically:

> **"Does the current state of the system warrant waking cognitive reasoning?"**

It performs zero natural-language reasoning, burns no unnecessary tokens, and costs \$0.00 while idle.

---

## 2. The 6 Deterministic Wake Conditions

The heartbeat inspects the system state and evaluates six specific boolean triggers:

```text
                               ┌─────────────────────────┐
                               │   HEARTBEAT SUPERVISOR  │
                               └────────────┬────────────┘
                                            │
        ┌───────────────────────────────────┼───────────────────────────────────┐
        ▼                                   ▼                                   ▼
[1. PREDICTION DUE]              [2. EXPERIMENT PENDING]             [3. SERVICE FAILURE]
Target date reached in           Active EXP-XXXXXX awaiting          1+ Cloud Run MCP
temporal_cortex.predictions      verification evaluation             services unreachable
        │                                   │                                   │
        ▼                                   ▼                                   ▼
[4. CONTRADICTION DETECTED]      [5. HIGH-VALUE UNKNOWN]             [6. TASK SCHEDULED]
Conflicting evidence logged      Curiosity Score >= 8.0              Queued Task Envelope
in Firestore/BigQuery            and budget available                ready for execution
```

---

## 3. Wake Cycle State Machine

```text
                [SLEEP]
                   │
            Heartbeat Trigger
                   │
                   ▼
         [EVALUATE 6 CONDITIONS]
                   │
          ┌────────┴────────┐
          ▼                 ▼
     [NO MATCH]         [MATCH]
          │                 │
     Record Status          ▼
    (BQ heartbeats)   [WAKE_REQUEST GENERATED]
          │                 │
          ▼                 ▼
       [SLEEP]        [BUDGET GUARDIAN PASS?]
                            │
                     ┌──────┴──────┐
                     ▼             ▼
                   [DENIED]      [APPROVED]
                     │             │
                   Record          ▼
                   Warning    [DISPATCH TO COGNITION]
                                   │
                                   ▼
                             [TASK EXECUTED]
                                   │
                                   ▼
                              [LOG TO BQ]
                                   │
                                   ▼
                                [SLEEP]
```

---

## 4. Anti-Recursion Safety Invariants
1. A wake cycle cannot trigger another heartbeat directly.
2. If a wake event fails or encounters an unhandled error, it transitions to `DEGRADED` status and logs a diagnostic record rather than looping.
3. Maximum wake frequency is throttled by the Budget Guardian.
