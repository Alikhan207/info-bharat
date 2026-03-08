/**
 * Info-Bharat — Citizen Portal Component
 * 
 * 4-step guided eligibility flow:
 * Step 1: Role Selection
 * Step 2: Context Collection (State, Age, Income, Aadhaar, Category)
 * Step 3: Natural Language Query
 * Step 4: Results (Confidence Meter + Scheme Cards + AI Guidance + TTS)
 */

import React, { useState } from "react";
import ConfidenceMeter from "./ConfidenceMeter";
import MiddlemanAlert from "./MiddlemanAlert";
import SchemeCard from "./SchemeCard";
import JourneyLog from "./JourneyLog";
import { useEligibilityEngine } from "../hooks/useEligibilityEngine";
import { useLanguage } from "../hooks/useLanguage";
import { ttsSpeak } from "../utils/ttsHelper";

export type CitizenRole = "student" | "farmer" | "senior" | "bpl" | "women" | "pwd";

interface CitizenProfile {
  role: CitizenRole | null;
  state: string;
  age: string;
  income: string;
  category: string;
  aadhaar_linked: boolean | null;
}

const ROLES: { id: CitizenRole; label: string; emoji: string }[] = [
  { id: "student", label: "Student", emoji: "🎓" },
  { id: "farmer", label: "Farmer", emoji: "🌾" },
  { id: "senior", label: "Senior Citizen", emoji: "👴" },
  { id: "bpl", label: "BPL Household", emoji: "🏠" },
  { id: "women", label: "Women / SHG", emoji: "👩" },
  { id: "pwd", label: "Person with Disability", emoji: "♿" },
];

const INDIAN_STATES = [
  "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
  "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
  "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
  "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
  "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
  "Delhi", "Jammu & Kashmir", "Ladakh",
];

export default function CitizenPortal() {
  const [step, setStep] = useState(1);
  const [profile, setProfile] = useState<CitizenProfile>({
    role: null, state: "", age: "", income: "", category: "", aadhaar_linked: null,
  });
  const [query, setQuery] = useState("");
  const { language, t } = useLanguage();
  const { evaluate, result, loading, journeyLog } = useEligibilityEngine();

  const handleRoleSelect = (role: CitizenRole) => {
    setProfile(p => ({ ...p, role }));
    setStep(2);
  };

  const handleContextSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setStep(3);
  };

  const handleQuerySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await evaluate(profile, query, language);
    setStep(4);
  };

  // Step 1 — Role Selection
  if (step === 1) return (
    <div className="citizen-portal step-1">
      <h2>{t("who_are_you")}</h2>
      <p className="subtitle">{t("role_subtitle")}</p>
      <div className="role-grid">
        {ROLES.map(role => (
          <button
            key={role.id}
            className="role-card"
            onClick={() => handleRoleSelect(role.id)}
          >
            <span className="role-emoji">{role.emoji}</span>
            <span className="role-label">{t(role.id)}</span>
          </button>
        ))}
      </div>
    </div>
  );

  // Step 2 — Context Collection
  if (step === 2) return (
    <div className="citizen-portal step-2">
      <h2>{t("tell_us_about_yourself")}</h2>
      <form onSubmit={handleContextSubmit}>
        <div className="form-group">
          <label>{t("state_of_residence")}</label>
          <select value={profile.state} onChange={e => setProfile(p => ({ ...p, state: e.target.value }))} required>
            <option value="">{t("select_state")}</option>
            {INDIAN_STATES.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>

        <div className="form-group">
          <label>{t("age")}</label>
          <input type="number" min="1" max="120" placeholder={t("enter_age")}
            value={profile.age} onChange={e => setProfile(p => ({ ...p, age: e.target.value }))} required />
        </div>

        <div className="form-group">
          <label>{t("annual_income")}</label>
          <input type="text" placeholder={t("income_placeholder")}
            value={profile.income} onChange={e => setProfile(p => ({ ...p, income: e.target.value }))} required />
        </div>

        <div className="form-group">
          <label>{t("social_category")}</label>
          <select value={profile.category} onChange={e => setProfile(p => ({ ...p, category: e.target.value }))} required>
            <option value="">{t("select_category")}</option>
            <option value="GENERAL">General</option>
            <option value="OBC">OBC</option>
            <option value="SC">SC</option>
            <option value="ST">ST</option>
            <option value="MINORITY">Minority</option>
          </select>
        </div>

        <div className="form-group">
          <label>{t("aadhaar_linked")}</label>
          <div className="radio-group">
            <label><input type="radio" onChange={() => setProfile(p => ({ ...p, aadhaar_linked: true }))} /> {t("yes")}</label>
            <label><input type="radio" onChange={() => setProfile(p => ({ ...p, aadhaar_linked: false }))} /> {t("no")}</label>
            <label><input type="radio" onChange={() => setProfile(p => ({ ...p, aadhaar_linked: null }))} /> {t("unsure")}</label>
          </div>
        </div>

        <button type="submit" className="btn-primary">{t("next")}</button>
      </form>
    </div>
  );

  // Step 3 — Natural Language Query
  if (step === 3) return (
    <div className="citizen-portal step-3">
      <h2>{t("describe_situation")}</h2>
      <p className="subtitle">{t("query_subtitle")}</p>
      <form onSubmit={handleQuerySubmit}>
        <textarea
          rows={5}
          placeholder={t("query_placeholder")}
          value={query}
          onChange={e => setQuery(e.target.value)}
          required
        />
        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? t("evaluating") : t("find_schemes")}
        </button>
      </form>
    </div>
  );

  // Step 4 — Results
  if (step === 4 && result) return (
    <div className="citizen-portal step-4">
      {result.middleman_alert && <MiddlemanAlert alert={result.middleman_alert} />}

      <ConfidenceMeter score={result.confidence} />

      {result.ai_guidance && (
        <div className="ai-guidance">
          <div className="guidance-header">
            <h3>{t("ai_guidance")}</h3>
            <button className="tts-btn" onClick={() => ttsSpeak(result.ai_guidance, language)}>
              🔊 {t("listen")}
            </button>
          </div>
          <p>{result.ai_guidance}</p>
        </div>
      )}

      <div className="scheme-results">
        {result.eligible_schemes?.map(s => (
          <SchemeCard key={s.scheme_id} scheme={s} status="eligible" />
        ))}
        {result.near_miss_schemes?.map(s => (
          <SchemeCard key={s.scheme_id} scheme={s} status="near_miss" />
        ))}
        {result.ineligible_schemes?.map(s => (
          <SchemeCard key={s.scheme_id} scheme={s} status="ineligible" />
        ))}
      </div>

      <JourneyLog entries={journeyLog} />

      <button onClick={() => { setStep(1); setQuery(""); }} className="btn-secondary">
        {t("start_over")}
      </button>
    </div>
  );

  return null;
}
