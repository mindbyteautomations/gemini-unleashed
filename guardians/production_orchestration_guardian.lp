% ==============================================================================
% GEMINI UNLEASHED: PRODUCTION MULTI-AGENT ORCHESTRATION INVARIANTS (ASP)
% ==============================================================================

synthesis_result(code_diff_generated; meta_commentary_only).
region_target("us-east4").
pipeline_stage(cloud_assist; claude_synthesis; codex_ast; jules_audit; git_commit).

% Invariant 1: Prohibit certifying synthesis if zero code diffs were generated
:- certify_task(Task), task_output(Task, synthesis_result(meta_commentary_only)).

% Invariant 2: Pipeline MUST execute all 4 active stages before git merge
:- merge_codebase(Task), not executed_stage(Task, pipeline_stage(cloud_assist)).
:- merge_codebase(Task), not executed_stage(Task, pipeline_stage(claude_synthesis)).
:- merge_codebase(Task), not executed_stage(Task, pipeline_stage(codex_ast)).
:- merge_codebase(Task), not executed_stage(Task, pipeline_stage(jules_audit)).

% Invariant 3: Production compute must execute exclusively within us-east4
:- deploy_production_job(Job, Region), Region != region_target("us-east4").

% Invariant 4: Zero in-memory direct code synthesis by Antigravity
:- execute_action(antigravity, author_code_directly).
