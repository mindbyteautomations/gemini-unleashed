% ==============================================================================
% GEMINI UNLEASHED: SPRINT 1 CODEX & JULES SAFETY INVARIANTS (ASP)
% ==============================================================================

agent(codex_agent).
agent(jules_worker).
authority_level(codex_agent, 5).
authority_level(jules_worker, 5).

forbidden_op(modify_iam).
forbidden_op(modify_billing).
forbidden_op(direct_redis_mutate).
forbidden_op(bypass_task_envelope).

% Invariant 1: Authority Level 5 agents CANNOT execute root system mutations
:- execute_action(Agent, Op), authority_level(Agent, 5), forbidden_op(Op).

% Invariant 2: No code merge to main without verified Jules Audit Receipt
has_clean_jules_audit(Task) :- jules_verdict(Task, "AUDIT_PASSED_CLEAN"), critical_vulns(Task, 0), high_vulns(Task, 0).
:- merge_to_main(Task), not has_clean_jules_audit(Task).

% Invariant 3: Memory Plane Isolation - Reject any agent write to Redis Cloud SaaS
memory_plane(redis_cloud_saas, quarantined_consumer).
memory_plane(firestore_native, internal_agent).
:- route_memory_write(Agent, redis_cloud_saas), agent(Agent).

% Invariant 4: Rollback Strategy MUST be defined on all Task Envelopes
:- mint_task_envelope(Task), not has_rollback_strategy(Task).
