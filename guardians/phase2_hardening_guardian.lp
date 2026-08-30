% ==============================================================================
% GEMINI UNLEASHED: PHASE 2 HARDENING & ISOLATION INVARIANTS (ASP)
% ==============================================================================

execution_sandbox(isolated_container_jail; shared_process_memory).
api_status(enabled_with_iam_role; disabled_unauthorized).
target_region("us-east4").

% Invariant 1: Jules adversarial fuzzer MUST run in isolated sandbox jail, NEVER in shared memory
:- execute_jules_audit(_, Sandbox), Sandbox == shared_process_memory.

% Invariant 2: Cloud Assist queries require verified IAM role and enabled API state
:- query_cloud_assist(Api), api_status(Api, disabled_unauthorized).

% Invariant 3: Production compute must execute strictly within us-east4
:- deploy_production_job(Job, Region), Region != target_region("us-east4").

% Invariant 4: Antigravity orchestrator is strictly barred from direct code synthesis
:- execute_action(antigravity_orchestrator, code_synthesis).
