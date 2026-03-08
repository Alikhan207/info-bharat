/**
 * Info-Bharat — useEligibilityEngine Hook
 * 
 * Manages the full eligibility evaluation flow:
 * 1. Client-side middleman detection (instant)
 * 2. Client-side confidence scoring
 * 3. API call to Trust & Integrity Engine (Lambda in production, 
 *    Claude API directly in prototype)
 * 4. Journey log management
 */

import { useState, useCallback } from "react";
import { detectMiddleman } from "../utils/middlemanDetector";

export interface EligibilityResult {
  confidence: number;
  middleman_alert: object | null;
  eligible_schemes: SchemeResult[];
  near_miss_schemes: NearMissResult[];
  ineligible_schemes: SchemeResult[];
  ai_guidance: string;
  status: "complete" | "withheld" | "error";
}

export interface SchemeResult {
  scheme_id: string;
  scheme_name: string;
  eligible: boolean;
  rejection_reason?: string;
}

export interface NearMissResult extends SchemeResult {
  gap_count: number;
  fix_instructions: string;
}

export interface JourneyEntry {
  timestamp: string;
  action: string;
  detail: string;
}

const API_BASE = process.env.REACT_APP_API_URL || "https://api.info-bharat.gov.in";

export function useEligibilityEngine() {
  const [result, setResult] = useState<EligibilityResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [journeyLog, setJourneyLog] = useState<JourneyEntry[]>([]);

  const log = (action: string, detail: string) => {
    setJourneyLog(prev => [
      ...prev,
      { timestamp: new Date().toLocaleTimeString("en-IN"), action, detail }
    ]);
  };

  const evaluate = useCallback(async (profile: object, query: string, language: string) => {
    setLoading(true);
    setError(null);
    log("Session started", `Role: ${(profile as any).role}, State: ${(profile as any).state}`);

    try {
      // Step 1: Client-side middleman detection (instant safety gate)
      const middlemanResult = detectMiddleman(query);
      if (middlemanResult.detected) {
        log("⚠️ Middleman alert", "Exploitation signal detected in query");
      }

      // Step 2: Call Trust & Integrity Engine
      log("Evaluating eligibility", "Sending to deterministic engine...");
      const response = await fetch(`${API_BASE}/evaluate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ profile, query, language, session_id: generateSessionId() }),
      });

      if (!response.ok) throw new Error(`API error: ${response.status}`);

      const data: EligibilityResult = await response.json();

      log("Evaluation complete", `Confidence: ${data.confidence}%`);
      if (data.status === "withheld") {
        log("⏸ Recommendations withheld", `Confidence ${data.confidence}% below 40% threshold`);
      } else {
        log("✓ Results ready", `${data.eligible_schemes?.length ?? 0} eligible, ${data.near_miss_schemes?.length ?? 0} near-miss`);
      }

      setResult(data);
    } catch (err: any) {
      setError(err.message);
      log("❌ Error", err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  return { evaluate, result, loading, error, journeyLog };
}

function generateSessionId(): string {
  // Generates a non-identifying session ID (no PII)
  return `session_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
}
