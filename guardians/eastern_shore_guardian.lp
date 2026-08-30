% ==============================================================================
% GEMINI UNLEASHED: OPERATION EASTERN SHORE & ARTIFACT PERSISTENCE INVARIANTS (ASP)
% ==============================================================================

region_status("us-east4", canonical_active).
region_status("us-central1", decommissioned_purged).

% Invariant 1: Prohibit running active schedulers or services in us-central1
:- service_active(Service, "us-central1").
:- scheduler_active(Job, "us-central1").

% Invariant 2: Synthesis tasks MUST write real files to disk and commit to Git
:- complete_task(Task), not artifact_persisted_to_file(Task).
:- complete_task(Task), not git_committed(Task).

% Invariant 3: All synthesis MUST pass through Codex AST and Jules validation
:- assimilate_artifact(File), not ast_verified(File).
:- assimilate_artifact(File), not jules_audited(File).

% Invariant 4: Schedulers in us-east4 MUST be deployed and active
:- service_active("gemini-spark-state-mcp", "us-east4"), not scheduler_active("dead-man-switch-hourly", "us-east4").
