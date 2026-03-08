"""
Info-Bharat — Eligibility Validator

Deterministic rule matching against DynamoDB scheme database.
No AI. No approximation. Binary eligibility per scheme rule set.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any


@dataclass
class EligibilityResult:
    scheme_id: str
    scheme_name: str
    eligible: bool
    failed_rules: List[dict] = field(default_factory=list)
    passed_rules: List[dict] = field(default_factory=list)
    rejection_reason: Optional[str] = None  # Specific rule that caused rejection

    def to_dict(self) -> dict:
        return {
            "scheme_id": self.scheme_id,
            "scheme_name": self.scheme_name,
            "eligible": self.eligible,
            "rejection_reason": self.rejection_reason,
            "failed_rules": self.failed_rules,
            "passed_rules": self.passed_rules,
        }


class EligibilityValidator:
    """
    Evaluates a citizen profile against all scheme rules in DynamoDB.

    Rule evaluation is strictly deterministic:
    - Income thresholds are exact comparisons
    - Age limits are numeric comparisons
    - Category requirements are set membership checks
    - State availability is a lookup

    If a rule fails, we record WHICH rule failed — this becomes
    the 'rejection reason' fed to Bedrock for explanation.
    """

    def __init__(self, schemes_table):
        self.table = schemes_table
        self._scheme_cache = None

    def _load_schemes(self) -> List[dict]:
        if self._scheme_cache is None:
            response = self.table.scan()
            self._scheme_cache = response.get("Items", [])
        return self._scheme_cache

    def evaluate(self, profile: dict) -> List[EligibilityResult]:
        schemes = self._load_schemes()
        results = []

        for scheme in schemes:
            result = self._evaluate_scheme(profile, scheme)
            results.append(result)

        return results

    def _evaluate_scheme(self, profile: dict, scheme: dict) -> EligibilityResult:
        scheme_id = scheme["scheme_id"]
        scheme_name = scheme["scheme_name"]
        rules = scheme.get("eligibility_rules", {})

        passed = []
        failed = []
        rejection_reason = None

        # ── INCOME CHECK ─────────────────────────────────────────────────────
        if "max_annual_income" in rules:
            citizen_income = self._parse_income(profile.get("income"))
            max_income = int(rules["max_annual_income"])
            if citizen_income is not None and citizen_income <= max_income:
                passed.append({"rule": "income", "detail": f"Income ₹{citizen_income} ≤ ₹{max_income}"})
            elif citizen_income is not None:
                failed.append({"rule": "income", "detail": f"Income ₹{citizen_income} exceeds limit ₹{max_income}"})
                if not rejection_reason:
                    rejection_reason = f"Annual income ₹{citizen_income:,} exceeds the scheme limit of ₹{max_income:,}"

        # ── AGE CHECK ────────────────────────────────────────────────────────
        if "min_age" in rules or "max_age" in rules:
            citizen_age = self._parse_age(profile.get("age"))
            if citizen_age is not None:
                min_age = int(rules.get("min_age", 0))
                max_age = int(rules.get("max_age", 150))
                if min_age <= citizen_age <= max_age:
                    passed.append({"rule": "age", "detail": f"Age {citizen_age} within {min_age}-{max_age}"})
                else:
                    failed.append({"rule": "age", "detail": f"Age {citizen_age} outside {min_age}-{max_age}"})
                    if not rejection_reason:
                        rejection_reason = f"Age {citizen_age} is outside the eligible range of {min_age}-{max_age} years"

        # ── CATEGORY CHECK ───────────────────────────────────────────────────
        if "eligible_categories" in rules:
            citizen_category = profile.get("category", "").upper()
            eligible_cats = [c.upper() for c in rules["eligible_categories"]]
            if citizen_category in eligible_cats or "ALL" in eligible_cats:
                passed.append({"rule": "category", "detail": f"Category {citizen_category} is eligible"})
            else:
                failed.append({"rule": "category", "detail": f"Category {citizen_category} not in {eligible_cats}"})
                if not rejection_reason:
                    rejection_reason = f"This scheme is available only for {', '.join(rules['eligible_categories'])} categories"

        # ── STATE AVAILABILITY ───────────────────────────────────────────────
        if "available_states" in rules:
            citizen_state = profile.get("state", "").lower()
            available = [s.lower() for s in rules["available_states"]]
            if "all" in available or citizen_state in available:
                passed.append({"rule": "state", "detail": "Scheme available in your state"})
            else:
                failed.append({"rule": "state", "detail": f"Scheme not available in {citizen_state}"})
                if not rejection_reason:
                    rejection_reason = f"This scheme is not yet available in {profile.get('state', 'your state')}"

        # ── AADHAAR REQUIREMENT ──────────────────────────────────────────────
        if rules.get("requires_aadhaar"):
            aadhaar_linked = profile.get("aadhaar_linked", False)
            if aadhaar_linked:
                passed.append({"rule": "aadhaar", "detail": "Aadhaar linked"})
            else:
                failed.append({"rule": "aadhaar", "detail": "Aadhaar not linked"})
                if not rejection_reason:
                    rejection_reason = "Aadhaar must be linked to your bank account for this scheme's direct benefit transfer"

        eligible = len(failed) == 0 and len(passed) > 0

        return EligibilityResult(
            scheme_id=scheme_id,
            scheme_name=scheme_name,
            eligible=eligible,
            failed_rules=failed,
            passed_rules=passed,
            rejection_reason=rejection_reason,
        )

    def _parse_income(self, income_val: Any) -> Optional[int]:
        if income_val is None or income_val in ("", "unsure", "unknown"):
            return None
        try:
            return int(str(income_val).replace(",", "").replace("₹", "").strip())
        except (ValueError, TypeError):
            return None

    def _parse_age(self, age_val: Any) -> Optional[int]:
        if age_val is None or age_val in ("", "unsure", "unknown"):
            return None
        try:
            return int(str(age_val).strip())
        except (ValueError, TypeError):
            return None
