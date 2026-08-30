% ==============================================================================
% GEMINI UNLEASHED: SCHEDULER METHOD & WORKSTATION PURITY INVARIANTS (ASP)
% ==============================================================================

scheduler_method("POST").
scheduler_method("GET") :- fail.

commit_source(cloud_run_job_container).
commit_source(local_windows_desktop) :- fail.

% Invariant 1: Cloud Scheduler MUST use POST for /dead-man-switch and /heartbeat
:- bind_scheduler(Job, Route, Method), Route == "/dead-man-switch", Method != "POST".
:- bind_scheduler(Job, Route, Method), Route == "/heartbeat", Method != "POST".

% Invariant 2: Strictly forbid committing code from local Windows desktop
:- git_commit_action(Source), Source == local_windows_desktop.

% Invariant 3: Prohibit active services or schedulers in us-central1
:- service_active(Service, "us-central1").
:- scheduler_active(Job, "us-central1").
