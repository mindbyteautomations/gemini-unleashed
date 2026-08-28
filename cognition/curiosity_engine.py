"""
Curiosity Engine — Mathematical Curiosity-Driven Research Prioritizer
Ranks unknowns by expected information gain vs resource cost.
"""
import secrets
from datetime import datetime, timezone
from typing import Dict, Any, List

class CuriosityEngine:
    def __init__(self):
        self.unknowns: Dict[str, Dict[str, Any]] = {}

    @staticmethod
    def calculate_curiosity_score(
        uncertainty: float,
        importance: float,
        info_gain: float,
        novelty: float,
        relevance: float,
        cost_usd: float
    ) -> float:
        """
        Curiosity = (Uncertainty * Importance * InfoGain * Novelty * Relevance) / (Cost + 0.1)
        """
        numerator = uncertainty * importance * info_gain * novelty * relevance
        denominator = max(0.01, cost_usd + 0.10)
        return round((numerator * 10.0) / denominator, 3)

    def register_unknown(
        self,
        question: str,
        uncertainty: float = 0.8,
        importance: float = 0.8,
        info_gain: float = 0.7,
        novelty: float = 0.6,
        relevance: float = 0.9,
        estimated_cost: float = 0.02
    ) -> Dict[str, Any]:
        unk_id = f"UNK-{secrets.token_hex(3).upper()}"
        score = self.calculate_curiosity_score(uncertainty, importance, info_gain, novelty, relevance, estimated_cost)
        
        unknown = {
            "unknown_id": unk_id,
            "question": question,
            "uncertainty": uncertainty,
            "importance": importance,
            "estimated_cost_usd": estimated_cost,
            "curiosity_score": score,
            "status": "OPEN",
            "registered_at": datetime.now(timezone.utc).isoformat()
        }
        self.unknowns[unk_id] = unknown
        return unknown

    def get_ranked_queue(self) -> List[Dict[str, Any]]:
        return sorted(self.unknowns.values(), key=lambda x: x["curiosity_score"], reverse=True)

if __name__ == "__main__":
    ce = CuriosityEngine()
    ce.register_unknown("How to optimize BigQuery partition pruning for temporal cortex?", 0.7, 0.9, 0.8, 0.5, 0.9, 0.01)
    ce.register_unknown("What is the cheapest way to run continuous vector indexing?", 0.9, 0.8, 0.8, 0.9, 0.8, 0.03)
    
    print("Ranked Curiosity Queue:")
    for rank, unk in enumerate(ce.get_ranked_queue(), 1):
        print(f" {rank}. [{unk['unknown_id']}] Score: {unk['curiosity_score']:5.2f} | {unk['question']}")
