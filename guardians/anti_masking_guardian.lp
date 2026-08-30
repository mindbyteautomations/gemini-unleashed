% ==============================================================================
% GEMINI UNLEASHED: SONNET 5 ULTRACODE & ANTI-MASKING INVARIANTS (ASP)
% ==============================================================================

model_identifier("claude-sonnet-5").
model_identifier("claude-3-7-sonnet") :- fail.
model_identifier("claude-3-5-sonnet") :- fail.

execution_mode("ultracode").

% Invariant 1: Strictly forbid deprecated or retired model identifiers
:- configure_runner(Model, _), not model_identifier(Model).

% Invariant 2: Strictly require ultracode execution profile for high-speed synthesis
:- configure_runner(_, Profile), Profile != "ultracode".

% Invariant 3: Zero exception swallowing - Non-zero CLI exit code MUST propagate
:- exit_status(cli, Code), Code != 0, container_exit_code(0).

% Invariant 4: No fake fallback success reporting
:- fallback_executed(codex_agent), reported_status("SUCCESS_CLAUDE_COMPLETED").
