"""
Info-Bharat — Refusal Engine

The principle: A wrong recommendation is worse than no recommendation.
If we cannot confidently evaluate a citizen's eligibility,
we withhold recommendations and tell them exactly what information we need.

Threshold: 40% confidence
Below this, the AI layer is not invoked at all.
"""


class RefusalEngine:

    def __init__(self, threshold: float = 40.0):
        self.threshold = threshold

    def should_refuse(self, confidence_score: float) -> bool:
        return confidence_score < self.threshold

    def get_reason(self, citizen_profile: dict) -> str:
        missing = []
        checks = {
            "state": "your state of residence",
            "age": "your age",
            "income": "your annual household income",
            "category": "your social category (General/OBC/SC/ST)",
            "aadhaar": "your Aadhaar card status",
        }
        for field, label in checks.items():
            val = citizen_profile.get(field)
            if not val or val in ("", "unknown", "unsure", None):
                missing.append(label)

        if missing:
            return (
                f"We need more information to give you accurate scheme recommendations. "
                f"Please provide: {', '.join(missing)}. "
                f"Giving incomplete recommendations could mislead you — we prefer to be accurate."
            )
        return "Insufficient information to make a reliable recommendation."
