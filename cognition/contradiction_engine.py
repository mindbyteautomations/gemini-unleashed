"""
Contradiction Engine — Epistemic Immune System
Identifies conflicting evidence and generates structured contradiction objects.
"""
import secrets
from enum import Enum
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

class ContradictionSeverity(str, Enum):
    LOW = "LOW"            # Non-blocking documentation discrepancy
    MEDIUM = "MEDIUM"      # Configuration or capability ambiguity
    CRITICAL = "CRITICAL"  # Security invariant or budget boundary clash

class ContradictionEngine:
    def __init__(self):
        self.contradictions: Dict[str, Dict[str, Any]] = {}

    def create_contradiction(
        self,
        claim_a: str,
        evidence_a: str,
        claim_b: str,
        evidence_b: str,
        severity: ContradictionSeverity = ContradictionSeverity.MEDIUM
    ) -> Dict[str, Any]:
        contra_id = f"CONTRA-{secrets.token_hex(3).upper()}"
        now = datetime.now(timezone.utc).isoformat()

        contra = {
            "contradiction_id": contra_id,
            "claim_a": claim_a,
            "evidence_a": evidence_a,
            "claim_b": claim_b,
            "evidence_b": evidence_b,
            "severity": severity.value,
            "status": "UNRESOLVED",
            "detected_at": now,
            "resolution": None
        }
        self.contradictions[contra_id] = contra
        return contra

    def resolve_contradiction(self, contradiction_id: str, resolved_truth: str, rationale: str) -> Optional[Dict[str, Any]]:
        if contradiction_id in self.contradictions:
            contra = self.contradictions[contradiction_id]
            contra["status"] = "RESOLVED"
            contra["resolution"] = {
                "resolved_truth": resolved_truth,
                "rationale": rationale,
                "resolved_at": datetime.now(timezone.utc).isoformat()
            }
            return contra
        return None

if __name__ == "__main__":
    ce = ContradictionEngine()
    c = ce.create_contradiction(
        claim_a="Cloud Run service is completely private.",
        evidence_a="IAM policy says internal-only",
        claim_b="Endpoint responds to public curl.",
        evidence_b="HTTP 200 from external network",
        severity=ContradictionSeverity.CRITICAL
    )
    print("Logged Contradiction:", json.dumps(c, indent=2))
