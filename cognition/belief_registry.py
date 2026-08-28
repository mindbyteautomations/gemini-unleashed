"""
Belief Registry — Epistemic State & Confidence Calibration
Maintains machine-readable beliefs with explicit certainty ratings.
"""
import json
import secrets
from enum import Enum
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

class BeliefStatus(str, Enum):
    KNOWN = "KNOWN"              # Independently verified by ground-truth observation
    BELIEVED = "BELIEVED"        # High confidence based on empirical evidence
    UNCERTAIN = "UNCERTAIN"      # Plausible hypothesis requiring verification
    CONTRADICTED = "CONTRADICTED"# Conflicting evidence flagged for research
    STALE = "STALE"              # Verification validity window has expired

class BeliefRegistry:
    def __init__(self):
        self.beliefs: Dict[str, Dict[str, Any]] = {}

    def register_belief(
        self,
        claim: str,
        confidence: float = 0.80,
        status: BeliefStatus = BeliefStatus.BELIEVED,
        evidence: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        bel_id = f"BEL-{secrets.token_hex(3).upper()}"
        now = datetime.now(timezone.utc).isoformat()
        
        belief = {
            "belief_id": bel_id,
            "claim": claim,
            "confidence": min(1.0, max(0.0, float(confidence))),
            "status": status.value,
            "evidence": evidence or [],
            "counter_evidence": [],
            "registered_at": now,
            "last_verified_at": now
        }
        self.beliefs[bel_id] = belief
        return belief

    def flag_contradiction(self, belief_id: str, counter_claim: str, evidence_ref: str) -> Optional[Dict[str, Any]]:
        if belief_id in self.beliefs:
            bel = self.beliefs[belief_id]
            bel["status"] = BeliefStatus.CONTRADICTED.value
            bel["counter_evidence"].append({"counter_claim": counter_claim, "evidence": evidence_ref})
            bel["confidence"] = round(bel["confidence"] * 0.5, 2)
            return bel
        return None

    def resolve_belief(self, belief_id: str, updated_claim: str, new_confidence: float, ground_truth_ref: str) -> Optional[Dict[str, Any]]:
        if belief_id in self.beliefs:
            bel = self.beliefs[belief_id]
            bel["claim"] = updated_claim
            bel["status"] = BeliefStatus.KNOWN.value if new_confidence >= 0.90 else BeliefStatus.BELIEVED.value
            bel["confidence"] = new_confidence
            bel["evidence"].append(ground_truth_ref)
            bel["last_verified_at"] = datetime.now(timezone.utc).isoformat()
            return bel
        return None

if __name__ == "__main__":
    reg = BeliefRegistry()
    b1 = reg.register_belief("Cloud Run FastMCP requires enable_dns_rebinding_protection=False", 0.95)
    print("Registered Belief:", json.dumps(b1, indent=2))
    
    c1 = reg.flag_contradiction(b1["belief_id"], "FastMCP DNS rebinding is active by default", "DOC-404")
    print("\nContradicted Belief:", json.dumps(c1, indent=2))
    
    r1 = reg.resolve_belief(b1["belief_id"], "Cloud Run FastMCP requires explicit DNS rebinding disablement behind reverse proxy", 0.99, "EXP-000001")
    print("\nResolved Belief:", json.dumps(r1, indent=2))
