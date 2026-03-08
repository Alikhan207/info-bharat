/**
 * Info-Bharat — Middleman Detector (Frontend)
 * 
 * Client-side version of the detection logic.
 * Runs BEFORE the API call so citizens get instant alerts.
 * The Lambda function also runs this — defence in depth.
 */

const EXPLOITATION_PHRASES = [
  "paid agent", "paid an agent", "gave money to", "gave cash to",
  "agent charged", "agent asked for", "had to pay", "need to pay",
  "they asked money", "asked for money", "took money", "taking money",
  "demanded money", "bribe for", "commission for application",
  "paid broker", "broker charged", "dalal", "dalalal", "sarkari agent",
];

const EXPLOITATION_PATTERNS = [
  /\bpaid\b.*\bagent\b/i,
  /\bagent\b.*\bpaid\b/i,
  /₹\s*\d+.*\bagent\b/i,
  /\bagent\b.*₹\s*\d+/i,
  /rs\.?\s*\d+.*\bagent\b/i,
  /\bpaisa\s+diya\b/i,
  /\bpaise\s+maange\b/i,
];

export interface MiddlemanDetectionResult {
  detected: boolean;
  severity: "high" | "none";
  message: string | null;
}

export function detectMiddleman(queryText: string): MiddlemanDetectionResult {
  const lower = queryText.toLowerCase();

  const phraseMatch = EXPLOITATION_PHRASES.some(phrase => lower.includes(phrase));
  const patternMatch = EXPLOITATION_PATTERNS.some(pattern => pattern.test(lower));

  const detected = phraseMatch || patternMatch;

  return {
    detected,
    severity: detected ? "high" : "none",
    message: detected
      ? "It sounds like someone may have charged you money. ALL scheme applications are FREE in India. No agent is authorised to charge fees."
      : null,
  };
}
