"""
Info-Bharat — Near-Miss Analyser

Identifies schemes where the citizen almost qualifies.
Generates specific, actionable guidance for each near-miss case.

This is one of Info-Bharat's most distinctive features —
no static system can do this.
"""

from dataclasses import dataclass, field
from typing import List
from eligibility_validator import EligibilityResult


@dataclass
class NearMissResult:
    scheme_id: str
    scheme_name: str
    gap_count: int           # How many rules are failing
    gaps: List[dict]         # Specific gaps with fix instructions
    fix_instructions: str    # Human-readable path to eligibility

    def to_dict(self) -> dict:
        return {
            "scheme_id": self.scheme_id,
            "scheme_name": self.scheme_name,
            "gap_count": self.gap_count,
            "gaps": self.gaps,
            "fix_instructions": self.fix_instructions,
        }


# Near-miss threshold: schemes failing at most this many rules
NEAR_MISS_MAX_GAPS = 2


class NearMissAnalyser:
    """
    For each ineligible scheme, checks if the citizen is "close" to qualifying.
    A scheme is a near-miss if it fails ≤ 2 rules.

    For each near-miss, generates specific instructions:
    - Income gap: "Your income is ₹X above the limit — if your income decreases..."
    - Aadhaar gap: "Link your Aadhaar to your bank account at your nearest bank branch"
    - Age gap: "You will become eligible in N years when you turn M"
    """

    def __init__(self, schemes_table):
        self.table = schemes_table

    def find(self, profile: dict, eligibility_results: List[EligibilityResult]) -> List[NearMissResult]:
        near_misses = []

        for result in eligibility_results:
            if result.eligible:
                continue  # Already eligible — not a near-miss

            gap_count = len(result.failed_rules)
            if gap_count == 0 or gap_count > NEAR_MISS_MAX_GAPS:
                continue  # Either no rules or too many gaps

            gaps = []
            instructions = []

            for rule in result.failed_rules:
                gap, instruction = self._generate_fix(rule, profile)
                gaps.append(gap)
                instructions.append(instruction)

            near_misses.append(NearMissResult(
                scheme_id=result.scheme_id,
                scheme_name=result.scheme_name,
                gap_count=gap_count,
                gaps=gaps,
                fix_instructions=" ".join(instructions),
            ))

        return near_misses

    def _generate_fix(self, failed_rule: dict, profile: dict) -> tuple:
        rule_type = failed_rule.get("rule")
        detail = failed_rule.get("detail", "")

        if rule_type == "aadhaar":
            return (
                {"type": "aadhaar", "description": "Aadhaar not linked to bank account"},
                "Visit your nearest bank branch with your Aadhaar card to link it. "
                "This is free and takes about 15 minutes. "
                "You can also do this at your nearest Common Service Centre (CSC)."
            )

        elif rule_type == "income":
            return (
                {"type": "income", "description": detail},
                "If your household income changes, you may become eligible. "
                "Contact your local Gram Panchayat for income certificate assistance."
            )

        elif rule_type == "age":
            return (
                {"type": "age", "description": detail},
                "You do not currently meet the age requirement. "
                "Check back when you meet the age criteria — your other details already qualify."
            )

        elif rule_type == "category":
            return (
                {"type": "category", "description": detail},
                "This scheme has category-specific eligibility. "
                "Contact your local tehsildar to verify your category certificate."
            )

        elif rule_type == "state":
            return (
                {"type": "state", "description": detail},
                "This scheme is not currently available in your state. "
                "Check india.gov.in for state-specific equivalent schemes."
            )

        else:
            return (
                {"type": "other", "description": detail},
                "Contact your nearest Gram Panchayat or Common Service Centre for guidance."
            )
