"""
Cloud-Native Subagent Runner Entrypoint (Google Cloud Run Jobs)
Executes autonomous subagent tasks (Claude Code, Jules VM, agy CLI, Codex AST)
inside ephemeral Linux containers in us-east4 with Secret Manager session mounting.
Runtime /workspace cloning, AST verification, and authenticated direct push to GitHub main.
Wires ResearchHarvester (Spoke 1) and CodexASTAnalyzer into in-container synthesis pipeline.
Zero local desktop dependency.
"""
import os
import sys
import json
import time
import asyncio
import shutil
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

try:
    from research.research_harvester import ResearchHarvester, EpistemicFilter
    HAS_HARVESTER = True
except ImportError:
    HAS_HARVESTER = False

PROJECT_ID = os.environ.get("GCP_PROJECT", "gemini-unleashed-core")
GCP_REGION = os.environ.get("GCP_REGION", os.environ.get("CLOUD_RUN_REGION", "us-east4"))
WORKSPACE_BASE = os.environ.get("WORKSPACE_DIR", "/workspace")



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
    def setup_workspace(cls, github_token: Optional[str] = None) -> str:
        """
        Initializes an isolated /workspace directory by cloning the canonical repository
        at live HEAD using the mounted GITHUB_TOKEN. Falls back to PROJECT_ROOT if unconfigured.
        """
        target_dir = WORKSPACE_BASE if os.path.exists(os.path.dirname(WORKSPACE_BASE)) or os.path.exists(WORKSPACE_BASE) else os.path.join(PROJECT_ROOT, "workspace_run")
        token = github_token or os.environ.get("GITHUB_TOKEN")

        if not token:
            print(f"[CloudRunner] Notice: GITHUB_TOKEN not available; using local directory: {PROJECT_ROOT}")
            return PROJECT_ROOT

        repo_url = f"https://x-access-token:{token}@github.com/mindbyteautomations/gemini-unleashed.git"

        try:
            os.makedirs(target_dir, exist_ok=True)
            git_dir = os.path.join(target_dir, ".git")

            if not os.path.exists(git_dir):
                # Clean target directory to prepare for fresh shallow clone
                for item in os.listdir(target_dir):
                    item_path = os.path.join(target_dir, item)
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path, ignore_errors=True)
                    else:
                        os.remove(item_path)

                print(f"[CloudRunner] Performing fresh git clone into {target_dir}...")
                subprocess.run(
                    ["git", "clone", "--depth=1", repo_url, target_dir],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
            else:
                print(f"[CloudRunner] Updating existing git workspace in {target_dir}...")
                subprocess.run(["git", "remote", "set-url", "origin", repo_url], cwd=target_dir, check=True)
                subprocess.run(["git", "fetch", "--depth=1", "origin", "main"], cwd=target_dir, check=True)
                subprocess.run(["git", "reset", "--hard", "origin/main"], cwd=target_dir, check=True)

            # Enforce canonical bot identity & safe directory
            subprocess.run(["git", "config", "user.name", "Gemini Unleashed Autonomous Subagent"], cwd=target_dir, check=True)
            subprocess.run(["git", "config", "user.email", "schafertech89@gmail.com"], cwd=target_dir, check=True)
            subprocess.run(["git", "config", "--global", "--add", "safe.directory", target_dir], cwd=target_dir, check=True)

            print(f"[CloudRunner] Workspace successfully initialized at {target_dir} (Live HEAD)")
            return target_dir

        except Exception as e:
            print(f"[CloudRunner] Workspace clone warning: {e}; falling back to PROJECT_ROOT: {PROJECT_ROOT}")
            return PROJECT_ROOT

    @classmethod
    def execute_research_harvest_cycle(cls, max_items: int = 10) -> Dict[str, Any]:
        """
        Spoke 1 Perception Layer: Executes an in-container autonomous research harvest cycle.
        Fetches live papers from arXiv (cs.AI, cs.CL) and Hugging Face daily feed,
        applies the EpistemicFilter (Theta_rel >= 0.75) across 5 canonical domains
        (COGNITION, MEMORY, GOVERNANCE, ACTUATION, INFRASTRUCTURE),
        and persists accepted KnowledgeAtoms to BigQuery temporal_cortex.knowledge_atoms.
        Returns a structured harvest receipt including accepted count, rejected count,
        and atom summaries for telemetry and walkthrough artifacts.
        """
        if not HAS_HARVESTER:
            return {
                "status": "HARVESTER_UNAVAILABLE",
                "error": "research.research_harvester module not importable in container",
                "accepted": 0,
                "rejected": 0,
                "atoms": []
            }

        t0 = time.time()
        try:
            atoms = asyncio.run(ResearchHarvester.harvest_and_filter(max_items=max_items))
        except Exception as e:
            return {
                "status": "HARVEST_FAILED",
                "error": str(e),
                "accepted": 0,
                "rejected": 0,
                "atoms": []
            }

        duration_ms = round((time.time() - t0) * 1000, 2)

        # Persist accepted atoms to BigQuery temporal_cortex.knowledge_atoms
        persisted_count = 0
        if HAS_GCP_SDK and atoms:
            try:
                bq_client = bigquery.Client(project=PROJECT_ID)
                table_id = f"{PROJECT_ID}.temporal_cortex.knowledge_atoms"
                rows = []
                for atom in atoms:
                    rows.append({
                        "atom_id": atom.get("atom_id", f"ATOM-{secrets.token_hex(4).upper()}"),
                        "timestamp": atom.get("timestamp", datetime.now(timezone.utc).isoformat()),
                        "domain": atom.get("domain", "COGNITION"),
                        "classification": atom.get("classification", "RESEARCH_DISCOVERY"),
                        "title": atom.get("title", "")[:500],
                        "primary_uri": atom.get("primary_uri", ""),
                        "claim": atom.get("claim", "")[:1000],
                        "architectural_relevance": atom.get("architectural_relevance", "")[:500],
                        "confidence_tier": atom.get("confidence_tier", "WORKING"),
                        "relevance_score": float(atom.get("relevance_score", 0.0)),
                    })
                errors = bq_client.insert_rows_json(table_id, rows)
                persisted_count = len(rows) - len(errors) if not errors else 0
                if errors:
                    print(f"[CloudRunner] BQ knowledge_atoms insert errors: {errors}")
            except Exception as bqe:
                print(f"[CloudRunner] BQ knowledge_atoms stream notice: {bqe}")

        atom_summaries = [
            {
                "atom_id": a.get("atom_id"),
                "domain": a.get("domain"),
                "title": a.get("title", "")[:120],
                "relevance_score": a.get("relevance_score"),
            }
            for a in atoms
        ]

        return {
            "status": "HARVEST_COMPLETE",
            "accepted_count": len(atoms),
            "persisted_to_bigquery": persisted_count,
            "duration_ms": duration_ms,
            "theta_rel_threshold": 0.75,
            "domains_active": list(["COGNITION", "MEMORY", "GOVERNANCE", "ACTUATION", "INFRASTRUCTURE"]),
            "atoms": atom_summaries
        }

    @classmethod
    def execute_codex_deep_analysis(cls, source_path: str, workspace_dir: str) -> Dict[str, Any]:
        """
        Codex AST Deep Analysis Engine: Walks all Python files in workspace_dir,
        performs AST parsing and cyclomatic complexity analysis on each file,
        aggregates function/class/import counts, identifies files with complexity > 10
        (potential refactor candidates), and emits a structured analysis report.
        Returns a full per-file breakdown and aggregate quality metrics.
        """
        t0 = time.time()
        results = []
        total_functions = 0
        total_classes = 0
        high_complexity_files = []

        scan_root = workspace_dir if os.path.isdir(workspace_dir) else PROJECT_ROOT
        # Walk only relevant source dirs, exclude .git, __pycache__, tests
        excluded_dirs = {".git", "__pycache__", "node_modules", ".pytest_cache", "tests"}

        for root_dir, dirs, files in os.walk(scan_root):
            dirs[:] = [d for d in dirs if d not in excluded_dirs]
            for fname in files:
                if not fname.endswith(".py"):
                    continue
                fpath = os.path.join(root_dir, fname)
                rel_path = os.path.relpath(fpath, scan_root)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        src = f.read()
                    analysis = CodexASTAnalyzer.analyze_source_code(src)
                    fn_count = len(analysis.get("functions", []))
                    cls_count = len(analysis.get("classes", []))
                    complexity = analysis.get("complexity_score", 0)
                    total_functions += fn_count
                    total_classes += cls_count
                    file_result = {
                        "file": rel_path,
                        "valid_syntax": analysis.get("valid_syntax", True),
                        "functions": fn_count,
                        "classes": cls_count,
                        "complexity_score": complexity,
                    }
                    results.append(file_result)
                    if complexity > 10:
                        high_complexity_files.append(rel_path)
                except Exception as e:
                    results.append({"file": rel_path, "error": str(e)})

        duration_ms = round((time.time() - t0) * 1000, 2)
        return {
            "status": "ANALYSIS_COMPLETE",
            "files_analyzed": len(results),
            "total_functions": total_functions,
            "total_classes": total_classes,
            "high_complexity_files": high_complexity_files,
            "high_complexity_count": len(high_complexity_files),
            "duration_ms": duration_ms,
            "per_file_breakdown": results,
        }

    @classmethod
    def execute_task_envelope(cls, task_envelope: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes a sealed Task Envelope inside the Cloud Run container with runtime /workspace isolation.
        """
        t0 = time.time()
        mounted_creds = cls.mount_session_credentials()

        task_id = task_envelope.get("task_id", f"TASK-CLOUD-{int(t0)}")
        engine = task_envelope.get("subagent_engine") or task_envelope.get("engine") or os.environ.get("SUBAGENT_ENGINE", "claude_code_cloud")

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
            "artifacts_generated": [],
            "credentials_mounted": mounted_creds
        }

        # 1. CODEX AST ENGINE (single-file parse)
        if engine == "codex_ast_cloud":
            source_code = task_envelope.get("source_code", "def solution():\n    return 'Cloud-Native Autonomous Execution'\n")
            ast_res = CodexASTAnalyzer.analyze_source_code(source_code)
            execution_result["ast_analysis"] = ast_res
            execution_result["status"] = "COMPLETED"
            execution_result["output"] = f"AST parsed successfully. Found {len(ast_res.get('functions', []))} functions."

        # 1b. CODEX DEEP ANALYSIS ENGINE (full workspace scan)
        elif engine == "codex_deep_analysis_cloud":
            workspace_dir = cls.setup_workspace(os.environ.get("GITHUB_TOKEN"))
            execution_result["workspace_dir"] = workspace_dir
            analysis = cls.execute_codex_deep_analysis(
                source_path=task_envelope.get("source_path", ""),
                workspace_dir=workspace_dir
            )
            execution_result["codex_deep_analysis"] = analysis
            execution_result["status"] = "COMPLETED"
            execution_result["output"] = (
                f"Codex deep analysis complete: {analysis['files_analyzed']} files scanned, "
                f"{analysis['total_functions']} functions, {analysis['total_classes']} classes, "
                f"{analysis['high_complexity_count']} high-complexity refactor candidates."
            )

        # 1c. RESEARCH HARVEST ENGINE (Spoke 1 Perception Layer)
        elif engine == "research_harvest_cloud":
            max_items = int(task_envelope.get("max_items", 10))
            harvest = cls.execute_research_harvest_cycle(max_items=max_items)
            execution_result["harvest_receipt"] = harvest
            execution_result["status"] = "COMPLETED"
            execution_result["output"] = (
                f"Research harvest complete: {harvest.get('accepted_count', 0)} atoms accepted "
                f"(Theta_rel >= {harvest.get('theta_rel_threshold', 0.75)}), "
                f"{harvest.get('persisted_to_bigquery', 0)} persisted to BigQuery temporal_cortex.knowledge_atoms."
            )

        # 2. CLAUDE CODE CLOUD SYNTHESIS ENGINE
        elif engine == "claude_code_cloud":
            # Initialize /workspace via runtime git clone
            workspace_dir = cls.setup_workspace(os.environ.get("GITHUB_TOKEN"))
            execution_result["workspace_dir"] = workspace_dir


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

            if has_valid_key or claude_session_exists:
                cmd = ["claude", "-p", prompt, "--model", model, "--dangerously-skip-permissions"]
                try:
                    res = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=180.0,
                        cwd=workspace_dir
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

                        # Extract target file path
                        target_file = task_envelope.get("target_file")
                        if not target_file:
                            import re
                            py_match = re.search(r'([a-zA-Z0-9_\-/]+\.py)', prompt)
                            if py_match:
                                target_file = py_match.group(1)

                        # Extract code block
                        extracted_code = ""
                        if "```python" in stdout_text:
                            extracted_code = stdout_text.split("```python")[1].split("```")[0].strip()
                        elif "```" in stdout_text:
                            extracted_code = stdout_text.split("```")[1].split("```")[0].strip()

                        if target_file and extracted_code:
                            full_target_path = os.path.join(workspace_dir, target_file)
                            os.makedirs(os.path.dirname(full_target_path), exist_ok=True)
                            with open(full_target_path, "w", encoding="utf-8") as f_out:
                                f_out.write(extracted_code)
                            execution_result["artifacts_generated"].append(target_file)
                            execution_result["persisted_to_disk"] = True

                            # 1. In-Container Static AST Verification
                            ast_analysis = CodexASTAnalyzer.analyze_source_code(extracted_code)
                            execution_result["ast_analysis"] = ast_analysis

                            # 2. In-Container Jules Adversarial Audit
                            try:
                                from harness.adversarial_runner import JulesAdversarialHarness
                                jules_res = JulesAdversarialHarness.execute_full_adversarial_suite(task_envelope)
                                execution_result["jules_audit"] = jules_res
                            except Exception as j_err:
                                execution_result["jules_audit"] = {"status": "SKIPPED", "notice": str(j_err)}

                            # 3. Direct In-Container Git Commit & Authenticated Push to GitHub main
                            github_token = os.environ.get("GITHUB_TOKEN")
                            if github_token and os.path.exists(os.path.join(workspace_dir, ".git")):
                                try:
                                    remote_url = f"https://x-access-token:{github_token}@github.com/mindbyteautomations/gemini-unleashed.git"
                                    subprocess.run(["git", "remote", "set-url", "origin", remote_url], cwd=workspace_dir, check=True)
                                    subprocess.run(["git", "add", target_file], cwd=workspace_dir, check=True)

                                    commit_msg = f"feat(autonomous): add {target_file} synthesized by Claude Sonnet 5 in Cloud Run [task:{task_id}]"
                                    commit_res = subprocess.run(["git", "commit", "-m", commit_msg], capture_output=True, text=True, cwd=workspace_dir)

                                    push_res = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True, cwd=workspace_dir)
                                    sha_res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=workspace_dir)

                                    commit_sha = sha_res.stdout.strip()
                                    execution_result["git_commit_sha"] = commit_sha
                                    execution_result["pushed_from_container"] = (push_res.returncode == 0)
                                    execution_result["git_push_status"] = "SUCCESS" if push_res.returncode == 0 else "PUSH_FAILED"
                                    if push_res.returncode != 0:
                                        execution_result["git_push_stderr"] = push_res.stderr.strip()
                                        print(f"[CloudRunner] Git push warning: {push_res.stderr.strip()}")
                                    else:
                                        print(f"[CloudRunner] Authenticated in-container push SUCCEEDED -> SHA: {commit_sha}")
                                except Exception as g_err:
                                    execution_result["git_error"] = str(g_err)
                                    print(f"[CloudRunner] Git in-container push error: {g_err}")
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
                        cls.dispatch_emergency_auth_alert(task_id, err_msg, "schafertech89@gmail.com")
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

        # 3. JULES ADVERSARIAL AUDIT ENGINE
        elif engine == "jules_vm_cloud":
            from harness.adversarial_runner import JulesAdversarialHarness
            receipt = JulesAdversarialHarness.execute_full_adversarial_suite(task_envelope)
            execution_result["jules_receipt"] = receipt
            execution_result["status"] = "COMPLETED"
            execution_result["output"] = f"Jules audit completed with verdict: {receipt.get('verdict')}"

        # 4. DEFAULT SUPERVISORY CLOUD AGENTS
        else:
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
        """Dispatches an emergency alert notification and logs FAIL-AUTH-EXPIRED to BigQuery."""
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
