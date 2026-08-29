% ==============================================================================
% GEMINI UNLEASHED: EMERGENCY REMEDIATION SAFETY INVARIANTS (ASP)
% ==============================================================================

subagent(claude_code_cli; jules_cli; antigravity_cli; gcloud_cli; cloud_code_assist; github_copilot; gemini_managed_agent).
auth_state(claude_code_cli, unauthenticated).
heartbeat_state(flatlined).
componecat_state(empty).

% Invariant 1: No subagent task dispatch without verified interactive OAuth authentication
:- dispatch_subagent_task(Subagent, _), auth_state(Subagent, unauthenticated).

% Invariant 2: Heartbeat flatline triggers immediate operational freeze
:- resume_normal_operations, heartbeat_state(flatlined).

% Invariant 3: Componecat registry must be populated before sprint closure
:- close_sprint(SprintId), componecat_state(empty).
