"""
Capability Graph — Directed Acyclic Graph (DAG) of System Capabilities
Resolves dependencies, prerequisites, and operational risk boundaries.
"""
from typing import Dict, List, Set, Optional

class CapabilityGraph:
    def __init__(self):
        # Directed dependencies: capability -> required prerequisites
        self.dependencies: Dict[str, List[str]] = {
            "state_persistence": [],
            "temporal_cortex_telemetry": ["state_persistence"],
            "semantic_memory_search": ["state_persistence"],
            "workspace_drive_docs": ["state_persistence"],
            "workspace_gmail_send": ["workspace_drive_docs"],
            "workspace_directory_admin": ["workspace_drive_docs"],
            "github_repo_management": [],
            "jules_task_dispatch": ["github_repo_management"],
            "cloud_run_deployment": ["github_repo_management", "temporal_cortex_telemetry"],
            "nvidia_nim_inference": ["state_persistence"],
            "developer_knowledge_search": [],
            "codex_ast_analysis": ["state_persistence"],
            "codex_code_synthesis": ["codex_ast_analysis", "github_repo_management"],
            "codex_refactor_evaluate": ["codex_ast_analysis"],
            "iam_and_billing_mutation": ["cloud_run_deployment"]
        }

    def validate_prerequisites(self, capability: str, active_capabilities: Set[str]) -> bool:
        """
        Validates whether all required prerequisite capabilities are available.
        """
        prereqs = self.dependencies.get(capability, [])
        for p in prereqs:
            if p not in active_capabilities:
                return False
        return True

    def get_prerequisite_chain(self, capability: str) -> List[str]:
        chain = []
        visited = set()

        def dfs(node):
            for prereq in self.dependencies.get(node, []):
                if prereq not in visited:
                    visited.add(prereq)
                    dfs(prereq)
                    chain.append(prereq)

        dfs(capability)
        return chain

if __name__ == "__main__":
    cg = CapabilityGraph()
    print("Prerequisite chain for 'cloud_run_deployment':", cg.get_prerequisite_chain("cloud_run_deployment"))
    
    active = {"github_repo_management", "state_persistence", "temporal_cortex_telemetry"}
    is_valid = cg.validate_prerequisites("cloud_run_deployment", active)
    print("Can deploy Cloud Run with active capabilities?:", is_valid)
