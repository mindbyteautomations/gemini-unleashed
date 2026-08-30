% ==============================================================================
% GEMINI UNLEASHED: UNIFIED CLOUD TOOLCHAIN SAFETY INVARIANTS (ASP)
% ==============================================================================

subagent(antigravity_orchestrator).
subagent(claude_sonnet_5_ultracode).
subagent(jules_vm_auditor).
subagent(codex_ast_specialist).
subagent(gemini_custom_agent).
subagent(gemini_cloud_assist).

role(antigravity_orchestrator, dispatcher_only).
role(claude_sonnet_5_ultracode, primary_synthesis).
role(jules_vm_auditor, adversarial_validation).
role(codex_ast_specialist, static_linter).
role(gemini_cloud_assist, architecture_guidance).

% Invariant 1: Antigravity is strictly forbidden from direct code authoring
:- execute_action(antigravity_orchestrator, direct_code_authoring).

% Invariant 2: Cloud CLI commands MUST route through cloudcli.googleapis.com MCP gateway
:- execute_cloud_infrastructure_mutation(Cmd), not routed_via("cloudcli.googleapis.com/mcp").

% Invariant 3: Claude Code MUST execute strictly on claude-sonnet-5 in ultracode profile
:- dispatch_synthesis(Engine, Model, Profile), Engine == "claude_code_cloud", Model != "claude-sonnet-5".
:- dispatch_synthesis(Engine, Model, Profile), Engine == "claude_code_cloud", Profile != "ultracode".

% Invariant 4: No git merge to main without clean Jules audit AND clean Codex AST validation
:- merge_to_main(Task), not jules_audit_passed(Task).
:- merge_to_main(Task), not codex_ast_verified(Task).

% Invariant 5: Total Polling Ban - Zero polling loops allowed during asynchronous tasks
:- execute_task(Task), is_polling_loop(Task).
