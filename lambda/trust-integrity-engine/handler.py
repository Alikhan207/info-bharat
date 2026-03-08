"""
Info-Bharat — Trust & Integrity Engine
AWS Lambda Handler (Python 3.11)

This is the core deterministic processing layer.
AI (Amazon Bedrock) is invoked ONLY after this engine completes —
and only to explain outcomes, never to determine them.
"""

import json
import boto3
from middleman_detector import MiddlemanDetector
from confidence_scorer import ConfidenceScorer
from refusal_engine import RefusalEngine
from eligibility_validator import EligibilityValidator
from nearmiss_analyser import NearMissAnalyser

# Initialize AWS clients
bedrock = boto3.client("bedrock-runtime", region_name="ap-south-1")
dynamodb = boto3.resource("dynamodb", region_name="ap-south-1")
schemes_table = dynamodb.Table("info_bharat_schemes")
journeys_table = dynamodb.Table("info_bharat_journeys")


def lambda_handler(event, context):
    """
    Main entry point for citizen eligibility evaluation.

    Flow:
    1. Parse citizen profile from request
    2. Middleman detection (safety gate)
    3. Confidence scoring
    4. Refusal check (confidence < 40% → withhold)
    5. Eligibility validation against DynamoDB scheme rules
    6. Near-miss analysis
    7. Invoke Bedrock for explanation (deterministic output only)
    8. Log journey (anonymised)
    9. Return structured response

    The AI layer never receives raw citizen input.
    It only receives the structured output of steps 2-6.
    """
    try:
        body = json.loads(event.get("body", "{}"))
        citizen_profile = body.get("profile", {})
        query_text = body.get("query", "")
        language = body.get("language", "en")
        session_id = body.get("session_id", "anonymous")

        # ── STEP 1: MIDDLEMAN DETECTION ──────────────────────────────────────
        # Safety gate — runs before any eligibility logic.
        # If exploitation is detected, we warn the citizen immediately.
        detector = MiddlemanDetector()
        middleman_result = detector.scan(query_text, citizen_profile)

        # ── STEP 2: CONFIDENCE SCORING ───────────────────────────────────────
        # confidence = verified_attributes / required_attributes × 100
        scorer = ConfidenceScorer()
        confidence = scorer.score(citizen_profile)

        # ── STEP 3: REFUSAL ENGINE ───────────────────────────────────────────
        # If confidence < 40%, we withhold recommendations entirely.
        # A wrong recommendation is worse than no recommendation.
        refusal_engine = RefusalEngine(threshold=40)
        if refusal_engine.should_refuse(confidence):
            return _build_response(200, {
                "status": "withheld",
                "confidence": confidence,
                "reason": refusal_engine.get_reason(citizen_profile),
                "middleman_alert": middleman_result.alert,
                "missing_attributes": scorer.get_missing(citizen_profile),
                "guidance": "Please provide complete information to receive scheme recommendations."
            })

        # ── STEP 4: ELIGIBILITY VALIDATION ───────────────────────────────────
        # Matches citizen profile against DynamoDB scheme rules.
        # Deterministic — no AI involved.
        validator = EligibilityValidator(schemes_table)
        eligibility_results = validator.evaluate(citizen_profile)

        # ── STEP 5: NEAR-MISS ANALYSIS ───────────────────────────────────────
        # Identifies schemes where citizen almost qualifies.
        # Generates specific actionable guidance for each near-miss.
        analyser = NearMissAnalyser(schemes_table)
        near_miss_results = analyser.find(citizen_profile, eligibility_results)

        # ── STEP 6: BUILD DETERMINISTIC SUMMARY ──────────────────────────────
        # This is ALL that gets sent to Bedrock — never raw citizen data.
        deterministic_summary = {
            "eligible_schemes": [r.to_dict() for r in eligibility_results if r.eligible],
            "ineligible_schemes": [r.to_dict() for r in eligibility_results if not r.eligible],
            "near_miss_schemes": [r.to_dict() for r in near_miss_results],
            "confidence_score": confidence,
            "middleman_detected": middleman_result.detected,
            "language": language,
        }

        # ── STEP 7: BEDROCK EXPLANATION LAYER ────────────────────────────────
        # AI explains rule outcomes. It does NOT determine eligibility.
        explanation = _invoke_bedrock(deterministic_summary, language)

        # ── STEP 8: ANONYMISED JOURNEY LOG ───────────────────────────────────
        _log_journey(session_id, deterministic_summary, journeys_table)

        return _build_response(200, {
            "status": "complete",
            "confidence": confidence,
            "middleman_alert": middleman_result.alert,
            "eligible_schemes": deterministic_summary["eligible_schemes"],
            "near_miss_schemes": deterministic_summary["near_miss_schemes"],
            "ineligible_schemes": deterministic_summary["ineligible_schemes"],
            "ai_guidance": explanation,
            "language": language,
        })

    except Exception as e:
        print(f"Error in trust_integrity_engine: {str(e)}")
        return _build_response(500, {"error": "Internal processing error", "detail": str(e)})


def _invoke_bedrock(deterministic_summary: dict, language: str) -> str:
    """
    Invoke Amazon Bedrock (Claude Sonnet) to generate citizen guidance.

    IMPORTANT: Only the deterministic summary is sent — never raw citizen input.
    The AI layer explains outcomes. It does not determine them.
    """
    language_names = {
        "en": "English", "hi": "Hindi", "kn": "Kannada",
        "ta": "Tamil", "te": "Telugu", "mr": "Marathi", "bn": "Bengali"
    }
    lang_name = language_names.get(language, "English")

    eligible = deterministic_summary["eligible_schemes"]
    near_miss = deterministic_summary["near_miss_schemes"]
    ineligible = deterministic_summary["ineligible_schemes"]

    prompt = f"""You are a citizen welfare advisor for the Indian government.

A deterministic eligibility engine has evaluated a citizen's profile against government scheme rules.
Here are the validated results:

ELIGIBLE SCHEMES: {json.dumps(eligible, indent=2)}
NEAR-MISS SCHEMES (almost qualify): {json.dumps(near_miss, indent=2)}
INELIGIBLE SCHEMES: {json.dumps(ineligible, indent=2)}
CONFIDENCE SCORE: {deterministic_summary['confidence_score']}%
MIDDLEMAN DETECTED: {deterministic_summary['middleman_detected']}

Your task:
1. Explain the results clearly in {lang_name}
2. For each eligible scheme, explain HOW to apply and WHAT documents are needed
3. For each near-miss scheme, explain EXACTLY what the citizen needs to change to qualify
4. For each ineligible scheme, explain WHY they don't qualify (be specific about which rule)
5. If middleman was detected, add a strong warning that all scheme applications are FREE
6. Be empathetic, clear, and actionable — this citizen may have low literacy

DO NOT guess or invent eligibility rules. Only explain the results provided above.
Respond in {lang_name}."""

    response = bedrock.invoke_model(
        modelId="anthropic.claude-sonnet-4-5",
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "messages": [{"role": "user", "content": prompt}]
        }),
        contentType="application/json",
        accept="application/json"
    )

    result = json.loads(response["body"].read())
    return result["content"][0]["text"]


def _log_journey(session_id: str, summary: dict, table) -> None:
    """
    Log anonymised session data for community intelligence.
    No PII is stored. Only aggregate signals.
    """
    import time
    table.put_item(Item={
        "session_id": session_id,
        "timestamp": int(time.time()),
        "eligible_count": len(summary["eligible_schemes"]),
        "near_miss_count": len(summary["near_miss_schemes"]),
        "confidence_score": str(summary["confidence_score"]),
        "middleman_detected": summary["middleman_detected"],
        "language": summary["language"],
        # NOTE: No citizen name, address, income, or identifying information stored
    })


def _build_response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
        },
        "body": json.dumps(body, ensure_ascii=False)
    }
