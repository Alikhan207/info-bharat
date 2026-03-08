"""
Info-Bharat — Middleman Detector
Runs BEFORE any eligibility logic as a citizen safety gate.

All government scheme applications in India are free.
Any agent charging fees is exploiting citizens.
This module detects and warns.
"""

import re
from dataclasses import dataclass
from typing import Optional


# Exploitation keywords — tested across 15 phrase patterns
# Covers Hindi-English code-mixing common in rural citizen queries
EXPLOITATION_PATTERNS = [
    # Payment keywords
    r"\bpaid\b", r"\bpay\b", r"\bcharge[ds]?\b", r"\bfee[s]?\b",
    r"\brupee[s]?\b.*\bagent\b", r"\bagent\b.*\brupee[s]?\b",
    r"₹\s*\d+", r"rs\.?\s*\d+",

    # Agent/broker keywords
    r"\bagent\b", r"\bbroker\b", r"\bdalalal\b", r"\bmiddleman\b",
    r"\bdalal\b", r"\bsarkari\s+agent\b",

    # Bribe/corruption
    r"\bbribe\b", r"\bkickback\b", r"\bcommission\b.*\bapplication\b",
    r"\bgave\s+money\b", r"\bgave\s+cash\b",

    # Common Hindi phrases (transliterated)
    r"\bpaisa\s+diya\b", r"\bpaisa\s+liya\b", r"\bpaise\s+maange\b",
    r"\bdene\s+ke\s+liye\b.*\bform\b",
]

EXPLOITATION_PHRASES = [
    "paid agent", "paid an agent", "gave money to", "gave cash to",
    "agent charged", "agent asked for", "had to pay", "need to pay",
    "they asked money", "asked for money", "took money", "taking money",
    "demanded money", "bribe for", "commission for application",
]


@dataclass
class MiddlemanDetectionResult:
    detected: bool
    confidence: float  # 0.0 to 1.0
    triggers: list
    alert: Optional[dict]


class MiddlemanDetector:
    """
    Scans citizen query text for exploitation signals.
    If detected, fires an alert before any eligibility guidance is given.

    This is a citizen protection mechanism, not a disqualifier.
    Detecting exploitation does not affect scheme eligibility.
    """

    def scan(self, query_text: str, citizen_profile: dict) -> MiddlemanDetectionResult:
        query_lower = query_text.lower()
        triggers = []

        # Pattern matching
        for pattern in EXPLOITATION_PATTERNS:
            if re.search(pattern, query_lower):
                triggers.append({"type": "pattern", "match": pattern})

        # Phrase matching
        for phrase in EXPLOITATION_PHRASES:
            if phrase in query_lower:
                triggers.append({"type": "phrase", "match": phrase})

        detected = len(triggers) > 0
        confidence = min(1.0, len(triggers) / 3.0)  # cap at 1.0

        alert = None
        if detected:
            alert = {
                "severity": "HIGH",
                "title": "⚠️ Possible Exploitation Detected",
                "message": (
                    "It sounds like someone may have charged you money to apply for a government scheme. "
                    "ALL government scheme applications in India are FREE. "
                    "No agent, broker, or government official is authorised to charge fees."
                ),
                "helplines": [
                    {"name": "National Helpline", "number": "1800-111-555"},
                    {"name": "Anti-Corruption Hotline", "number": "1031"},
                    {"name": "PM Grievance Portal", "url": "pgportal.gov.in"},
                ],
                "action": (
                    "You can apply for all schemes directly at your nearest "
                    "Common Service Centre (CSC) at no cost, or online at india.gov.in"
                ),
            }

        return MiddlemanDetectionResult(
            detected=detected,
            confidence=confidence,
            triggers=triggers,
            alert=alert
        )
