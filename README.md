# Info-Bharat 🇮🇳
### India's First AI-Powered Citizen Entitlement Advocate

> **AWS AI for Bharat Hackathon — AI for Communities Theme**  
> Team: Info-Bharat | Lead: Mohammed Ali Khan

---

## 🔴 Honest Note on AWS Deployment — Read First

We attempted to deploy the production architecture on Amazon Web Services. Multiple signup attempts were made across several days. Despite completing all required steps — payment method, identity verification, support plan selection — the account remained on "incomplete setup" with services inaccessible.

**Evidence of attempt:** See [`docs/aws-activation-failure.md`](docs/aws-activation-failure.md)

Rather than give up and submit nothing, we made a deliberate choice:

> *"The architecture is real. The logic is real. The problem is real. If AWS won't activate in time, we'll prove the concept another way."*

**The working prototype uses:**
- **Claude API (Anthropic)** — same model family as Amazon Bedrock (Claude Sonnet)
- **Vercel** — static hosting, equivalent to S3 + CloudFront for prototype purposes
- **Browser-native JavaScript** — the deterministic eligibility engine runs client-side

**The production architecture remains unchanged** — Lambda, DynamoDB, Bedrock, API Gateway. The code scaffolding for all Lambda functions is in this repository, ready to deploy the moment an AWS account activates.

We believe judges should reward teams that fight through adversity, not give up. This is that submission.

---

## 🌐 Live Prototype

**[info-bharat.vercel.app](https://info-bharat.vercel.app)**

- ✅ All 4 modules functional
- ✅ Real Claude AI (Sonnet) — same model as Amazon Bedrock
- ✅ 7 Indian languages + Text-to-Speech
- ✅ 89KB — loads in under 1 second on 2G
- ✅ No login required

---

## 💡 What Info-Bharat Does

India has **1,000+ government welfare schemes**. Over **800 million citizens** are eligible for at least one. Most never receive them — due to:

| Problem | Scale |
|---------|-------|
| Rejection without explanation | Citizens denied with no reason given |
| Middleman exploitation | Agents charge ₹500–₹2,000 per application |
| Documentation confusion | Valid applicants fail paperwork hurdles |
| Zero feedback loop | Government has no visibility into scheme failures |

**The reframing question:**  
Every existing platform asks: *"Which schemes exist?"*  
Info-Bharat asks: ***"Why are eligible citizens still not receiving them?"***

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CITIZEN INTERFACE                         │
│         React Web App  (S3 + CloudFront CDN)                │
│   Citizen Portal | Community | Government | Reversal        │
│   7 Languages | Text-to-Speech | Mobile Responsive          │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS
┌────────────────────────▼────────────────────────────────────┐
│              Amazon API Gateway (HTTP API)                   │
│  POST /evaluate  |  GET /community  |  GET /government      │
└───────┬──────────────────────────────────┬──────────────────┘
        │                                  │
┌───────▼──────────────────┐   ┌───────────▼─────────────────┐
│   AWS Lambda             │   │   AWS Lambda                │
│   Trust & Integrity      │   │   Pattern Aggregator        │
│   Engine (Python 3.11)   │   │   (anonymised community     │
│                          │   │    data processing)         │
│  middleman_detector.py   │   └───────────┬─────────────────┘
│  confidence_scorer.py    │               │
│  refusal_engine.py       │   ┌───────────▼─────────────────┐
│  eligibility_validator.py│   │   Amazon DynamoDB           │
│  nearmiss_analyser.py    │   │   district_metrics table    │
└───────┬──────────────────┘   └─────────────────────────────┘
        │
┌───────▼──────────────────────────────────────────────────────┐
│                  Amazon DynamoDB                              │
│  schemes_db       — 1,200+ eligibility rules                 │
│  citizen_journeys — anonymised session logs                  │
└───────┬──────────────────────────────────────────────────────┘
        │ (deterministic output only — AI never sees raw input)
┌───────▼──────────────────────────────────────────────────────┐
│              Amazon Bedrock — Claude Sonnet                   │
│  Receives: validated eligibility result                      │
│  Generates: citizen guidance | grievance letters             │
│             multilingual explanations                        │
│  NEVER determines eligibility — only explains outcomes       │
└──────────────────────────────────────────────────────────────┘
```

**Key design principle:** AI explains. Rules decide. Citizens are protected first.

---

## 📁 Repository Structure

```
info-bharat/
│
├── info-bharat.html          # ← Working prototype (single file, 89KB)
│                               All 4 modules, real Claude AI, 7 languages
│
├── src/                      # React frontend (production build)
│   ├── components/
│   │   ├── CitizenPortal.tsx
│   │   ├── CommunityIntelligence.tsx
│   │   ├── GovernmentDashboard.tsx
│   │   ├── RejectionReversal.tsx
│   │   ├── ConfidenceMeter.tsx
│   │   ├── MiddlemanAlert.tsx
│   │   ├── SchemeCard.tsx
│   │   └── JourneyLog.tsx
│   ├── hooks/
│   │   ├── useEligibilityEngine.ts
│   │   ├── useConfidenceScorer.ts
│   │   └── useLanguage.ts
│   └── utils/
│       ├── schemeRules.ts
│       ├── middlemanDetector.ts
│       └── ttsHelper.ts
│
├── lambda/                   # AWS Lambda functions (Python 3.11)
│   ├── trust-integrity-engine/
│   │   ├── handler.py        # Main Lambda entry point
│   │   ├── middleman_detector.py
│   │   ├── confidence_scorer.py
│   │   ├── refusal_engine.py
│   │   ├── eligibility_validator.py
│   │   ├── nearmiss_analyser.py
│   │   └── requirements.txt
│   ├── pattern-aggregator/
│   │   ├── handler.py
│   │   └── requirements.txt
│   ├── scheme-validator/
│   │   ├── handler.py
│   │   └── requirements.txt
│   └── community-aggregator/
│       ├── handler.py
│       └── requirements.txt
│
├── database/
│   ├── schema.sql            # DynamoDB table definitions
│   └── migrations/
│       └── 001_seed_schemes.sql
│
├── scripts/
│   └── seed_schemes.py       # Seed 6 prototype schemes into DynamoDB
│
├── docs/
│   ├── aws-activation-failure.md   # Evidence of AWS signup attempt
│   ├── ARCHITECTURE.md             # Detailed architecture decisions
│   └── DESIGN.md                   # Design philosophy & system design
│
├── template.yaml             # AWS SAM template for one-click deploy
├── .gitignore
└── README.md
```

---

## 🔧 Four Modules

### 1. Citizen Portal
- Role-based profiling: Student, Farmer, Senior, BPL, Women/SHG, PwD
- 4-step eligibility flow: Role → Context → Query → Guidance
- **Confidence Score** = verified attributes / required attributes × 100
- **Refusal Engine** — withholds recommendations when confidence < 40%
- **Middleman Detection** — real-time keyword scan before any guidance
- **Rejection Explainability** — which rule caused the denial
- **Near-Miss Guidance** — "You don't qualify now, but fix X to qualify"
- **7 Languages** — English, Hindi, Kannada, Tamil, Telugu, Marathi, Bengali
- **Text-to-Speech** — full audio playback for low-literacy citizens

### 2. Rejection Reversal Engine
- Citizen describes rejection in natural language
- System classifies: legitimate denial vs. bureaucratic error
- AI generates formal grievance letter → ready to submit at pgportal.gov.in

### 3. Community Intelligence
- Rejection heatmap by district — systemic failures, not individual ones
- Exploitation concentration map — organised middleman networks by geography
- Scheme performance vs. design intent
- Near-miss population sizing

### 4. Government Dashboard
- District Collector: anomaly alerts + action buttons (Investigate / Alert Police / Plan Camp)
- State Secretary: cross-district urgency comparison
- Central Ministry: ₹840Cr undelivered benefits estimate, policy flaw detection

---

## ⚡ Performance

| Metric | Prototype | Production Target |
|--------|-----------|-------------------|
| Middleman detection | < 10ms | < 10ms |
| Confidence scoring | < 5ms | < 5ms |
| Lambda eligibility engine | — | < 200ms (warm) |
| DynamoDB scheme lookup | — | < 10ms |
| AI guidance generation | 1.8–3.2s | < 3s (Bedrock) |
| End-to-end | < 4s | < 4s |
| File size | 89KB | N/A (CDN) |

---

## 💰 Cost Model

| Stage | Monthly Cost | Users |
|-------|-------------|-------|
| Prototype (now) | ₹0 | Unlimited (static) |
| MVP on AWS Free Tier | ~₹2,500 | 10,000 |
| Production | ~₹28,000 | 100,000 |

**ROI:** ₹0.28 per citizen guided vs ₹500–2,000 charged by middlemen.

---

## 🗺️ Roadmap

**Phase 2 (Months 3–6):** Full AWS deploy, 1,200+ schemes, MyScheme.gov.in live feed  
**Phase 3 (Months 6–12):** Voice via Amazon Transcribe, WhatsApp, offline mode  
**Phase 4 (Year 2):** Policy simulation engine, Open NGO API, CPGRAMS integration

**3-Year Impact Targets:**
- 10 million citizen queries processed
- ₹5,000 crore in benefits correctly routed
- 50,000 exploitation attempts detected
- Policy recommendations to 5 state governments

---

## 🛠️ Running Locally

```bash
# Prototype (zero dependencies)
open info-bharat.html

# Or serve locally
python -m http.server 8000
# Visit http://localhost:8000/info-bharat.html
```

---

## 📜 License

MIT — built for India, open for India.
