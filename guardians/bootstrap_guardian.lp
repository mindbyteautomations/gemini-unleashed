% ==============================================================================
% GEMINI UNLEASHED: CLEAN BOOTSTRAP SAFETY INVARIANTS (ASP)
% ==============================================================================

execution_host(gcp_cloud_run_job; local_desktop_windows).
billing_mode(subscription_oauth_volume; unauthorized_pay_per_token_api).

% Invariant 1: Strictly forbid local desktop execution for all agent workers
:- execute_agent_task(_, Host), Host == local_desktop_windows.

% Invariant 2: Strictly forbid switching to pay-per-token API keys when subscription volume exists
:- configure_claude_runtime(_, Billing), Billing == unauthorized_pay_per_token_api.

% Invariant 3: Container images must be lean (<600MB) and multi-stage compiled
:- deploy_container_image(Image, SizeMB), SizeMB > 600.

% Invariant 4: No tool execution without verified pre-turn CAP v1.0 WAVA artifact
:- execute_agent_turn(Agent), not produced_wava_artifact(Agent).

