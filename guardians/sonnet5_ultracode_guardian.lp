% ==============================================================================
% GEMINI UNLEASHED: CLAUDE SONNET 5 ULTRACODE & ZERO-FALLBACK INVARIANTS (ASP)
% ==============================================================================

role(antigravity, pure_orchestrator).
role(claude_code, primary_coding_specialist).

model_target("claude-sonnet-5").
profile_target("ultracode").
alert_recipient("schafertech89@gmail.com").

% Invariant 1: Antigravity MUST NOT author production code directly
:- execute_action(antigravity, direct_code_synthesis), not emergency_override_active.

% Invariant 2: Claude Code MUST run strictly on Sonnet 5 in ultracode profile
:- configure_claude(Model, _), Model != "claude-sonnet-5".
:- configure_claude(_, Profile), Profile != "ultracode".

% Invariant 3: Zero-Fallback Law - strictly forbid falling back when Claude auth fails
:- handle_auth_failure(claude_code), fallback_to(codex_agent).

% Invariant 4: Auth failure MUST trigger emergency email to schafertech89@gmail.com
:- handle_auth_failure(claude_code), not dispatch_alert_email(alert_recipient("schafertech89@gmail.com")).
