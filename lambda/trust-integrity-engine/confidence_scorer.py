"""
Info-Bharat — Confidence Scorer

confidence = verified_attributes / required_attributes × 100

The refusal engine uses this score.
If confidence < 40%, recommendations are withheld entirely.
A wrong recommendation is worse than no recommendation.
"""

from dataclasses import dataclass, field
from typing import List


# Attributes required to make reliable scheme recommendations
REQUIRED_ATTRIBUTES = [
    "state",        # State of residence — schemes vary dramatically by state
    "age",          # Age determines eligibility for many schemes
    "income",       # Annual household income — most schemes are income-gated
    "category",     # SC/ST/OBC/General — many schemes are category-specific
    "aadhaar",      # Aadhaar linkage status — required for scheme disbursement
]

# Attributes that are optional but improve recommendation accuracy
OPTIONAL_ATTRIBUTES = [
    "land_holding",     # For farmer schemes (PM-KISAN etc.)
    "bpl_card",         # BPL card holder status
    "disability",       # For disability schemes (IGNDPS etc.)
    "pregnant",         # For maternity schemes (PM Matru Vandana etc.)
    "student",          # For scholarship schemes
    "bank_account",     # For DBT-eligible scheme filtering
]


@dataclass
class ConfidenceResult:
    score: float                          # 0-100
    tier: str                             # "high" | "medium" | "low" | "withheld"
    verified_count: int
    required_count: int
    missing_required: List[str] = field(default_factory=list)
    optional_present: List[str] = field(default_factory=list)


class ConfidenceScorer:

    def score(self, citizen_profile: dict) -> float:
        """
        Returns confidence score 0-100.
        Only required attributes count toward the base score.
        Optional attributes can boost above 100 (capped at 100).
        """
        verified = 0
        for attr in REQUIRED_ATTRIBUTES:
            val = citizen_profile.get(attr)
            if val and val not in ("", "unknown", "unsure", None):
                verified += 1

        base_score = (verified / len(REQUIRED_ATTRIBUTES)) * 100

        # Optional attributes add a small boost (max 10 points)
        optional_boost = 0
        for attr in OPTIONAL_ATTRIBUTES:
            if citizen_profile.get(attr) not in ("", None):
                optional_boost += 2

        return min(100.0, base_score + optional_boost)

    def get_missing(self, citizen_profile: dict) -> List[str]:
        """Returns list of missing required attributes with human-readable labels."""
        labels = {
            "state": "State of residence",
            "age": "Age",
            "income": "Annual household income",
            "category": "Social category (General/OBC/SC/ST)",
            "aadhaar": "Aadhaar card status",
        }
        missing = []
        for attr in REQUIRED_ATTRIBUTES:
            val = citizen_profile.get(attr)
            if not val or val in ("", "unknown", "unsure", None):
                missing.append(labels.get(attr, attr))
        return missing

    def get_tier(self, score: float) -> str:
        if score >= 80:
            return "high"
        elif score >= 40:
            return "medium"
        else:
            return "low"
