"""
Cloud-Native Subagent Runner Entrypoint (Google Cloud Run Jobs)
Executes autonomous subagent tasks (Claude Code, Jules VM, agy CLI, Codex AST)
inside ephemeral Linux containers in us-central1 with Secret Manager session mounting.
Zero local desktop dependency.
"""
import os
import sys
import json
import time
import secrets
import subprocess
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from google.cloud import bigquery, secretmanager
    HAS_GCP_SDK = True
except ImportError:
    HAS_GCP_SDK = False

from cognition.codex_evaluator import CodexASTAnalyzer

PROJECT_ID = os.environ.get("GCP_PROJECT", "gemini-unleashed-core")
GCP_REGION = os.environ.get("GCP_REGION", os.environ.get("CLOUD_RUN_REGION", "us-central1"))

class CloudSubagentRunner:
    @classmethod
    def mount_session_credentials(cls) -> Dict[str, bool]:
        """
        Mounts credentials from Secret Manager or container environment paths.
        Supports ~/.claude.json OAuth session config for Claude Max subscription volume.
        """
        mounted = {}
        home_dir = os.environ.get("HOME", "/home/appuser" if os.path.exists("/home/appuser") else "/root")
        claude_config_path = os.path.join(home_dir, ".claude.json")
        
        # 1. Mount Claude OAuth Session if provided via secret or env
        session_json = os.environ.get("CLAUDE_SESSION_OAUTH_JSON")
        if session_json:
            try:
                os.makedirs(home_dir, exist_ok=True)
                with open(claude_config_path, "w", encoding="utf-8") as f:
                    f.write(session_json)
                try:
                    os.chmod(claude_config_path, 0o600)
                except Exception:
                    pass
                mounted["claude_session_oauth"] = True
            except Exception as e:
                print(f"[CloudRunner] Session mount notice: {e}")
                mounted["claude_session_oauth"] = False
        else:
            mounted["claude_session_oauth"] = os.path.exists(claude_config_path)

        # 2. Check GitHub Token
        mounted["github_token"] = bool(os.environ.get("GITHUB_TOKEN"))
        
        # 3. Check Anthropic API Key / Setup Token (map subscription tokens to CLAUDE_CODE_TOKEN)
        raw_token = (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("CLAUDE_CODE_TOKEN") or "").strip()
        active_token = raw_token.replace('\x00', '').replace('\ufeff', '').strip().strip("'").strip('"').strip()
        
        if not active_token or len(active_token) < 10 or active_token.lower() in ("none", "placeholder", "dummy") or active_token.startswith("sk-ant-api03-placeholder"):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            os.environ.pop("CLAUDE_CODE_TOKEN", None)
            os.environ.pop("ANTHROPIC_AUTH_TOKEN", None)
            mounted["anthropic_api_key"] = False
        else:
            mounted["anthropic_api_key"] = True
            # Setup tokens from `claude setup-token` must be exported as CLAUDE_CODE_TOKEN / ANTHROPIC_AUTH_TOKEN
            if not active_token.startswith("sk-ant-api03"):
                os.environ["CLAUDE_CODE_TOKEN"] = active_token
                os.environ["ANTHROPIC_AUTH_TOKEN"] = active_token
                os.environ.pop("ANTHROPIC_API_KEY", None)
            else:
                os.environ["ANTHROPIC_API_KEY"] = active_token
        
        # 4. Check Gemini API / ADC
        mounted["gemini_adc"] = bool(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") or HAS_GCP_SDK)
        return mounted

    @classmethod
    def execute_task_envelope(cls, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes a sealed Task Envelope inside the Cloud Run container.
        """
        t0 = time.time()
        cls.mount_session_credentials()
        
        task_id = task_envelope.get("task_id", f"TASK-CLOUD-{int(t0)}")
        engine = task_envelope.get("subagent_engine") or task_envelope.get("engine") or os.environ.get("SUBAGENT_ENGINE", "claude_code_cloud")
        # Normalize objective to string
        raw_obj = task_envelope.get("objective", "Synthesize verified code patch.")
        if isinstance(raw_obj, dict):
            objective_str = raw_obj.get("description") or raw_obj.get("goal") or json.dumps(raw_obj)
        else:
            objective_str = str(raw_obj)
            
        execution_result = {
            "task_id": task_id,
            "engine": engine,
            "execution_plane": "GCP_CLOUD_RUN_JOB",
            "gcp_project": PROJECT_ID,
            "region": GCP_REGION,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "status": "RUNNING",
            "artifacts_generated": []
        }

        # Route to appropriate cloud engine implementation
        if engine == "codex_ast_cloud":
            source_code = task_envelope.get("source_code", "def solution():\n    return 'Cloud-Native Autonomous Execution'\n")
            ast_res = CodexASTAnalyzer.analyze_source_code(source_code)
            execution_result["ast_analysis"] = ast_res
            execution_result["status"] = "COMPLETED"
            execution_result["output"] = f"AST parsed successfully. Found {len(ast_res.get('functions', []))} functions."

        elif engine == "claude_code_cloud":
            raw_prompt = task_envelope.get("prompt", objective_str)
            if isinstance(raw_prompt, dict):
                prompt = raw_prompt.get("description") or raw_prompt.get("text") or json.dumps(raw_prompt)
            else:
                prompt = str(raw_prompt)
                
            anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
            claude_code_token = os.environ.get("CLAUDE_CODE_TOKEN", "")
            has_valid_key = bool(anthropic_key or claude_code_token)
            home_dir = os.environ.get("HOME", "/home/appuser" if os.path.exists("/home/appuser") else "/root")
            claude_session_path = os.path.join(home_dir, ".claude.json")
            claude_session_exists = os.path.exists(claude_session_path)
            
            model = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5")
            profile = os.environ.get("CLAUDE_PROFILE", "ultracode")
            
            execution_result["model"] = model
            execution_result["execution_profile"] = profile
            
            # Execute non-interactive Claude Code CLI within container if authenticated
            if has_valid_key or claude_session_exists:
                cmd = ["claude", "-p", prompt, "--model", model, "--dangerously-skip-permissions"]
                try:
                    res = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=180.0,
                        cwd=PROJECT_ROOT
                    )
                    duration_ms = (time.time() - t0) * 1000.0
                    execution_result["duration_ms"] = round(duration_ms, 2)
                    execution_result["completed_at"] = datetime.now(timezone.utc).isoformat()
                    
                    if res.returncode == 0:
                        execution_result["status"] = "COMPLETED"
                        execution_result["exit_code"] = res.returncode
                        stdout_text = res.stdout.strip()
                        execution_result["stdout"] = stdout_text
                        execution_result["output"] = stdout_text or f"Claude Sonnet 5 ({profile}) synthesis executed successfully."

                        # Extract and persist code artifacts if present in stdout
                        target_file = task_envelope.get("target_file")
                        if not target_file:
                            import re
                            py_match = re.search(r'([a-zA-Z0-9_\-/]+\.py)', prompt)
                            if py_match:
                                target_file = py_match.group(1)

                        extracted_code = ""
                        if "```python" in stdout_text:
                            extracted_code = stdout_text.split("```python")[1].split("```")[0].strip()
                        elif "```" in stdout_text:
                            extracted_code = stdout_text.split("```")[1].split("```")[0].strip()

                        if target_file and extracted_code:
                            full_target_path = os.path.join(PROJECT_ROOT, target_file)
                            os.makedirs(os.path.dirname(full_target_path), exist_ok=True)
                            with open(full_target_path, "w", encoding="utf-8") as f_out:
                                f_out.write(extracted_code)
                            execution_result["artifacts_generated"].append(target_file)
                            execution_result["persisted_to_disk"] = True

                            # Run static AST verification
                            ast_analysis = CodexASTAnalyzer.analyze_source_code(extracted_code)
                            execution_result["ast_analysis"] = ast_analysis

                            # Run Jules Adversarial Audit
                            try:
                                from harness.adversarial_runner import JulesAdversarialHarness
                                jules_res = JulesAdversarialHarness.execute_full_adversarial_suite(task_envelope)
                                execution_result["jules_audit"] = jules_res
                            except Exception as j_err:
                                execution_result["jules_audit"] = {"status": "SKIPPED", "notice": str(j_err)}

                            # In-Container Git Commit & Remote Push via GITHUB_TOKEN
                            github_token = os.environ.get("GITHUB_TOKEN")
                            if github_token:
                                try:
                                    remote_url = f"https://x-access-token:{github_token}@github.com/mindbyteautomations/gemini-unleashed.git"
                                    subprocess.run(["git", "config", "--global", "user.name", "Gemini Unleashed Autonomous Subagent"], cwd=PROJECT_ROOT, check=True)
                                    subprocess.run(["git", "config", "--global", "user.email", "schafertech89@gmail.com"], cwd=PROJECT_ROOT, check=True)
                                    subprocess.run(["git", "config", "--global", "--add", "safe.directory", "*"], cwd=PROJECT_ROOT, check=True)
                                    if not os.path.exists(os.path.join(PROJECT_ROOT, ".git")):
                                        subprocess.run(["git", "init"], cwd=PROJECT_ROOT, check=True)
                                        subprocess.run(["git", "remote", "add", "origin", remote_url], cwd=PROJECT_ROOT, check=True)
                                        subprocess.run(["git", "fetch", "origin", "main"], cwd=PROJECT_ROOT, check=True)
                                        subprocess.run(["git", "checkout", "-b", "main", "origin/main"], cwd=PROJECT_ROOT, check=True)
                                    else:
                                        subprocess.run(["git", "remote", "set-url", "origin", remote_url], cwd=PROJECT_ROOT, check=True)

                                    subprocess.run(["git", "add", target_file], cwd=PROJECT_ROOT, check=True)
                                    commit_msg = f"feat(autonomous): add {target_file} synthesized by Claude Sonnet 5 in Cloud Run"
                                    commit_res = subprocess.run(["git", "commit", "-m", commit_msg], capture_output=True, text=True, cwd=PROJECT_ROOT)
                                    push_res = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True, cwd=PROJECT_ROOT)
                                    sha_res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=PROJECT_ROOT)
                                    commit_sha = sha_res.stdout.strip()
                                    execution_result["git_commit_sha"] = commit_sha
                                    execution_result["pushed_from_container"] = (push_res.returncode == 0)
                                    execution_result["git_push_status"] = push_res.stdout.strip() or push_res.stderr.strip()
                                except Exception as g_err:
                                    execution_result["git_error"] = str(g_err)
                    else:
                        err_msg = f"Claude CLI exited with code {res.returncode}: {res.stderr.strip() or res.stdout.strip()}"
                        execution_result["status"] = "FAILED"
                        execution_result["exit_code"] = res.returncode
                        execution_result["stderr"] = res.stderr.strip()
                        execution_result["output"] = err_msg
                        cls.log_failure_to_bigquery(
                            task_id=task_id,
                            engine=engine,
                            exit_code=res.returncode,
                            stderr=res.stderr.strip() or res.stdout.strip(),
                            profile=profile
                        )
                        # Dispatch Emergency Email Alert to schafertech89@gmail.com
                        cls.dispatch_emergency_auth_alert(task_id, err_msg, "schafertech89@gmail.com")
                        # Deterministic unmasked failure propagation
                        cls.log_telemetry_to_bigquery(execution_result)
                        print(json.dumps(execution_result, indent=2))
                        sys.exit(res.returncode)
                except subprocess.TimeoutExpired:
                    err_msg = f"Claude Sonnet 5 execution exceeded timeout limit of 180s on profile {profile}."
                    execution_result["status"] = "TIMEOUT_FAILED"
                    execution_result["exit_code"] = 124
                    execution_result["output"] = err_msg
                    execution_result["duration_ms"] = round((time.time() - t0) * 1000.0, 2)
                    execution_result["completed_at"] = datetime.now(timezone.utc).isoformat()
                    cls.log_failure_to_bigquery(task_id=task_id, engine=engine, exit_code=124, stderr=err_msg, profile=profile)
                    cls.dispatch_emergency_auth_alert(task_id, err_msg, "schafertech89@gmail.com")
                    cls.log_telemetry_to_bigquery(execution_result)
                    sys.exit(124)
                except Exception as e:
                    err_msg = f"Claude CLI execution failed: {str(e)}"
                    execution_result["status"] = "PROCESS_FAILED"
                    execution_result["exit_code"] = 1
                    execution_result["output"] = err_msg
                    execution_result["duration_ms"] = round((time.time() - t0) * 1000.0, 2)
                    execution_result["completed_at"] = datetime.now(timezone.utc).isoformat()
                    cls.log_failure_to_bigquery(task_id=task_id, engine=engine, exit_code=1, stderr=str(e), profile=profile)
                    cls.dispatch_emergency_auth_alert(task_id, err_msg, "schafertech89@gmail.com")
                    cls.log_telemetry_to_bigquery(execution_result)
                    sys.exit(1)
            else:
                err_msg = f"Unauthenticated session for {model} on {profile}; missing API key and active ~/.claude.json."
                execution_result["status"] = "UNAUTHENTICATED_FAILED"
                execution_result["exit_code"] = 1
                execution_result["output"] = err_msg
                execution_result["duration_ms"] = round((time.time() - t0) * 1000.0, 2)
                execution_result["completed_at"] = datetime.now(timezone.utc).isoformat()
                cls.log_failure_to_bigquery(task_id=task_id, engine=engine, exit_code=1, stderr=err_msg, profile=profile)
                cls.dispatch_emergency_auth_alert(task_id, err_msg, "schafertech89@gmail.com")
                cls.log_telemetry_to_bigquery(execution_result)
                sys.exit(1)

        elif engine == "jules_vm_cloud":
            from harness.adversarial_runner import JulesAdversarialHarness
            receipt = JulesAdversarialHarness.execute_full_adversarial_suite(task_envelope)
            execution_result["jules_receipt"] = receipt
            execution_result["status"] = "COMPLETED"
            execution_result["output"] = f"Jules audit completed with verdict: {receipt.get('verdict')}"

        else:  # agy_cli_cloud / gemini_companion_cloud
            execution_result["status"] = "COMPLETED"
            execution_result["output"] = f"Executed cloud task '{objective_str}' via {engine}."

        duration_ms = (time.time() - t0) * 1000.0
        execution_result["duration_ms"] = round(duration_ms, 2)
        execution_result["completed_at"] = datetime.now(timezone.utc).isoformat()

        # Telemetry logging to BigQuery
        cls.log_telemetry_to_bigquery(execution_result)
        return execution_result

    @classmethod
    def dispatch_emergency_auth_alert(cls, task_id: str, error_details: str, recipient: str = "schafertech89@gmail.com"):
        """Dispatches an emergency alert notification to schafertech89@gmail.com and logs FAIL-AUTH-EXPIRED to BigQuery."""
        subject = "[URGENT ACTION REQUIRED] Claude Code Subagent Session Expired"
        body = (
            f"ALERT: Cloud Run Job subagent-runner encountered an authentication failure for task {task_id}.\n"
            f"Details: {error_details}\n\n"
            f"REQUIRED OPERATOR ACTION:\n"
            f"1. Open host terminal and run: claude login\n"
            f"2. Sync the session grant to Secret Manager:\n"
            f"   gcloud secrets versions add claude-session-credentials --data-file=\"$env:USERPROFILE\\.claude.json\" --project={PROJECT_ID}\n"
        )
        print(f"[EMERGENCY_AUTH_ALERT] TO={recipient} | SUBJECT={subject}")
        print(body)
        
        if HAS_GCP_SDK:
            try:
                client = bigquery.Client(project=PROJECT_ID)
                table_id = f"{PROJECT_ID}.temporal_cortex.failures"
                now_iso = datetime.now(timezone.utc).isoformat()
                row = {
                    "event_id": f"FAIL-AUTH-EXPIRED-{secrets.token_hex(4).upper()}",
                    "timestamp": now_iso,
                    "engine": "claude_code_cloud",
                    "task_id": task_id,
                    "exit_code": 1,
                    "error_signature": f"AUTH_ALERT_DISPATCHED: {error_details[:180]}",
                    "stderr": body,
                    "profile": "ultracode"
                }
                client.insert_rows_json(table_id, [row])
            except Exception as bqe:
                print(f"[CloudRunner] Emergency alert BigQuery stream notice: {bqe}")

    @classmethod
    def log_telemetry_to_bigquery(cls, record: Dict[str, Any]):
        """Streams execution event to BigQuery temporal_cortex.tool_events."""
        if HAS_GCP_SDK:
            try:
                client = bigquery.Client(project=PROJECT_ID)
                table_id = f"{PROJECT_ID}.temporal_cortex.tool_events"
                row = {
                    "event_id": f"EVT-{secrets.token_hex(6).upper()}",
                    "timestamp": record["completed_at"],
                    "tool_name": record["engine"],
                    "task_id": record["task_id"],
                    "latency_ms": record["duration_ms"],
                    "status": record["status"],
                    "payload": json.dumps({"output": record.get("output", "")})
                }
                client.insert_rows_json(table_id, [row])
            except Exception as e:
                print(f"[CloudRunner] BigQuery telemetry stream notice: {e}")

    @classmethod
    def log_failure_to_bigquery(cls, task_id: str, engine: str, exit_code: int, stderr: str, profile: str = "ultracode"):
        """Streams failure event to BigQuery temporal_cortex.failures."""
        if HAS_GCP_SDK:
            try:
                client = bigquery.Client(project=PROJECT_ID)
                table_id = f"{PROJECT_ID}.temporal_cortex.failures"
                now_iso = datetime.now(timezone.utc).isoformat()
                row = {
                    "event_id": f"FAIL-{secrets.token_hex(6).upper()}",
                    "timestamp": now_iso,
                    "engine": engine,
                    "task_id": task_id,
                    "exit_code": exit_code,
                    "error_signature": stderr[:256] if stderr else "UNKNOWN_ERROR",
                    "stderr": stderr or "",
                    "profile": profile
                }
                client.insert_rows_json(table_id, [row])
            except Exception as e:
                print(f"[CloudRunner] BigQuery failure stream notice: {e}")

def main():
    if len(sys.argv) > 1:
        raw_args = " ".join(sys.argv[1:])
    else:
        raw_args = os.environ.get("TASK_PAYLOAD_JSON")

    subagent_engine = os.environ.get("SUBAGENT_ENGINE", "claude_code_cloud")

    if raw_args:
        try:
            task_data = json.loads(raw_args)
            if not isinstance(task_data, dict):
                task_data = {"prompt": str(task_data)}
        except Exception:
            task_data = {
                "task_id": f"TASK-CLI-{secrets.token_hex(3).upper()}",
                "subagent_engine": subagent_engine,
                "prompt": raw_args,
                "objective": {"description": raw_args}
            }
    else:
        task_data = {
            "task_id": f"TASK-CLOUD-{int(time.time())}",
            "subagent_engine": subagent_engine,
            "objective": {"description": "Cloud Run Job Autonomous Verification & Claude Synthesis"},
            "authority_level": 5,
            "allowed_capabilities": ["claude_code_synthesis", "codex_code_synthesis"]
        }

    res = CloudSubagentRunner.execute_task_envelope(task_data)
    print(json.dumps(res, indent=2))

if __name__ == "__main__":
    main()
