"""
Budget Guardian — Deterministic Cost Controller & Circuit Breaker
Enforces the $130.00/month Google Cloud Credit Envelope.
Guarantees $0.00 out-of-pocket expenditure.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Tuple

class BudgetState(str, Enum):
    GREEN = "GREEN"      # <$30/mo: Normal autonomous operation
    YELLOW = "YELLOW"    # $30-$60/mo: Background research throttled
    ORANGE = "ORANGE"    # $60-$80/mo: Automated research halted; user tasks only
    RED = "RED"          # $80-$100/mo: Strict freeze; human approval mandatory
    BLACK = "BLACK"      # >$100/mo: Circuit Breaker — Absolute Execution Halt

@dataclass
class BudgetEvaluation:
    current_burn: float
    budget_state: BudgetState
    action_allowed: bool
    remaining_credit: float
    reason: str

class BudgetGuardian:
    MONTHLY_CREDIT_ALLOWANCE: float = 130.00
    TARGET_BURN_CEILING: float = 30.00
    HARD_STOP_CEILING: float = 100.00

    @classmethod
    def evaluate_spend(cls, current_spend: float, estimated_task_cost: float = 0.0) -> BudgetEvaluation:
        """
        Deterministic spend evaluation.
        No LLM reasoning, no subjective exceptions.
        """
        projected = current_spend + estimated_task_cost
        remaining = max(0.0, cls.MONTHLY_CREDIT_ALLOWANCE - projected)

        if projected < 30.00:
            return BudgetEvaluation(
                current_burn=projected,
                budget_state=BudgetState.GREEN,
                action_allowed=True,
                remaining_credit=remaining,
                reason="Spend is well within target operational envelope (<$30.00)."
            )
        elif projected < 60.00:
            return BudgetEvaluation(
                current_burn=projected,
                budget_state=BudgetState.YELLOW,
                action_allowed=True,
                remaining_credit=remaining,
                reason="Spend in caution band ($30-$60). Background research throttled."
            )
        elif projected < 80.00:
            return BudgetEvaluation(
                current_burn=projected,
                budget_state=BudgetState.ORANGE,
                action_allowed=False,
                remaining_credit=remaining,
                reason="Spend in warning band ($60-$80). Automated research suspended."
            )
        elif projected <= 100.00:
            return BudgetEvaluation(
                current_burn=projected,
                budget_state=BudgetState.RED,
                action_allowed=False,
                remaining_credit=remaining,
                reason="Spend approaching hard stop ($80-$100). Requires direct human approval."
            )
        else:
            return BudgetEvaluation(
                current_burn=projected,
                budget_state=BudgetState.BLACK,
                action_allowed=False,
                remaining_credit=remaining,
                reason="CIRCUIT BREAKER TRIGGERED: Monthly spend exceeds $100.00 hard limit. ALL execution halted to protect zero out-of-pocket invariant."
            )

if __name__ == "__main__":
    test_cases = [12.50, 42.00, 72.00, 95.00, 105.00]
    print("--- Budget Guardian Test Matrix ---")
    for spend in test_cases:
        res = BudgetGuardian.evaluate_spend(spend, 0.05)
        print(f"Spend: ${spend:6.2f} -> State: {res.budget_state.value:<6} | Allowed: {str(res.action_allowed):<5} | Reason: {res.reason}")
