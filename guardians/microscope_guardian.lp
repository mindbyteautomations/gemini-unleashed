% ==============================================================================
% GEMINI UNLEASHED: FORENSIC REAL-EXECUTION INVARIANTS (ASP)
% ==============================================================================

job_execution_status(succeeded; failed; timed_out; concealed_pending).
remote_http_status(200..599).
route_status(deployed_live; local_uncommitted_ghost).

% Invariant 1: Prohibit certifying Cloud Run Job without verified SUCCEEDED execution status
:- certify_job(JobName), execution_status(JobName, Status), Status != succeeded.

% Invariant 2: Prohibit Cloud Scheduler jobs pointing to undeployed ghost routes
:- bind_scheduler_target(Service, Route), route_status(Route, local_uncommitted_ghost).

% Invariant 3: Prohibit claiming remote sync on HTTP 404
:- certify_remote_catalog_sync(OrgId), remote_http_status(Status), Status != 200, Status != 201.

% Invariant 4: Cloud Run Job container MUST have credentials mounted in runtime spec
:- deploy_cloud_subagent(Job), not mounted_secret(Job, "anthropic-credentials").
