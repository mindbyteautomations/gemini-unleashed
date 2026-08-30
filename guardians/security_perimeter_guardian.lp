% ==============================================================================
% GEMINI UNLEASHED: STRICT SECURITY & REAL INGRESS INVARIANTS (ASP)
% ==============================================================================

ingress_target(real_componecat_saas; self_loopback_mock).
auth_policy(authenticated_oidc; unauthenticated_public).
secret_validity(valid_credential; dummy_mock_none).

% Invariant 1: Strictly forbid unauthenticated public ingress on state gateways
:- deploy_cloud_service(Service, auth_policy(unauthenticated_public)), is_state_gateway(Service).

% Invariant 2: Strictly forbid dummy string secrets in Secret Manager
:- mount_secret_in_job(SecretName, secret_validity(dummy_mock_none)).

% Invariant 3: Prohibit claiming catalog sync when target is a loopback mock server
:- certify_catalog_sync(Target), Target == self_loopback_mock.

% Invariant 4: Dead-Man's switch MUST trigger active Pub/Sub or Gmail dispatch on staleness
:- evaluate_dead_man(State), is_stale(State), not active_alert_dispatched(dev_mindbyte_net).
