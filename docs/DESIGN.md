# Info-Bharat — Design Decisions

## Core Design Principle

**AI explains. Rules decide. Citizens are protected first.**

Amazon Bedrock is invoked only AFTER the deterministic Trust & Integrity Engine completes. The AI layer cannot override eligibility decisions — it can only explain them. This prevents AI hallucinations from giving citizens false hope or wrong guidance about their legal entitlements.

---

## Why Deterministic-First?

Welfare scheme eligibility is governed by law. Rules are binary:
- Income is either below threshold or above it
- Age either meets requirements or doesn't
- Aadhaar is either linked or not

AI hallucination in this domain causes real harm:
- A citizen told they're eligible who isn't may spend money on applications
- A citizen wrongly told they're ineligible may never receive benefits they're owed
- A citizen given wrong documentation requirements wastes days at government offices

**The Trust & Integrity Engine runs first. Every time. No exceptions.**

---

## The Confidence Threshold

`confidence = verified_attributes / required_attributes × 100`

Below 40%: recommendations are withheld entirely.

This is a deliberate, conservative choice. When we don't know enough about a citizen's situation to evaluate their eligibility reliably, we say so — and tell them exactly what information we need. A partial recommendation based on insufficient data is worse than no recommendation.

---

## The Middleman Detection Layer

This runs as the very first step — before eligibility, before confidence scoring, before anything else.

Rationale: A citizen mentioning they paid an agent is in an active exploitation situation. Their most urgent need is not scheme guidance — it is protection. We fire the alert immediately, provide helpline numbers, and explain that all applications are free.

Detection does not affect eligibility evaluation. A citizen can be both exploited and eligible.

---

## Why No PII Storage?

Citizens using Info-Bharat are often from marginalised communities. Storing their income, caste, family details, and health conditions creates risk:
- Data breach exposure
- Potential government misuse
- Chilling effect on usage

We store only aggregate signals:
- Eligible count (not which schemes)
- Near-miss count
- Middleman detection boolean
- Language used
- State only (not district, not village)
- Confidence score

Session IDs are randomly generated and not linked to citizen identity.

---

## The Near-Miss Feature

This is Info-Bharat's most distinctive capability.

Every existing system tells a citizen: "You qualify" or "You don't qualify."

Info-Bharat tells a citizen: "You don't qualify for PM-KISAN because your Aadhaar isn't linked to your bank account. Here's exactly how to fix that at your nearest bank branch — it's free and takes 15 minutes."

The near-miss analyser triggers when a scheme fails ≤ 2 rules. It generates specific, actionable instructions per failed rule type — not generic advice.

---

## Language + TTS Architecture

7 languages are supported: English, Hindi, Kannada, Tamil, Telugu, Marathi, Bengali.

Implementation:
- UI strings: pre-translated JSON per language, instant switch
- AI guidance: Bedrock generates responses in the requested language natively
- TTS: Web Speech API (native browser) — no third-party dependency, works on 2G

The TTS choice was deliberate. Rural India has millions of low-literacy or non-literate citizens who may be assisted by a family member typing queries but need to hear the guidance themselves. TTS is not a feature — it is an accessibility requirement.

---

## The Three-Layer Intelligence Model

### Layer 1: Individual
Each citizen gets personalised guidance. This is the visible product.

### Layer 2: Community
When thousands of citizens from the same district describe similar rejections, that's not individual failure — it's systemic failure. The anonymised Community Intelligence layer surfaces these patterns: district heatmaps, exploitation concentration by geography, scheme performance vs. design intent.

### Layer 3: Government
The Government Dashboard converts community patterns into policy intelligence. A District Collector can see: "PM-KISAN rejections in Nalanda district have spiked 3× this month — Aadhaar linkage is the primary failure point." An action button lets them plan a Aadhaar-bank linkage camp.

This closes the loop that has never existed in Indian welfare delivery.
