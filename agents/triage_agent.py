"""
agents/triage_agent.py
-----------------------
AGENT 2: TRIAGE AGENT
----------------------
PURPOSE: Decide how urgent the patient's situation is.

OUTPUT (one of four levels):
  - emergent  : Call ambulance NOW (chest pain, stroke symptoms, etc.)
  - urgent    : See a doctor today
  - routine   : Schedule appointment this week
  - self-care : Can manage at home with guidance

HOW IT WORKS:
  1. FIRST, run hard safety rules (no AI — instant decisions for clear emergencies)
  2. THEN, use an ML-style scoring approach (weighted symptoms)
  3. This "hybrid rule + ML" is exactly what the project document specifies!

WHY NO FULL ML MODEL IN MVP?
  Training a real gradient boosting model needs labeled data we don't have yet.
  This rule-based scoring gives us the same behavior for the MVP phase.
"""

from schemas.models import NormalizedSymptoms, TriageResult, PatientIntake
from typing import List


# ─── EMERGENCY KEYWORDS: These trigger immediate "emergent" classification ────

EMERGENCY_PATTERNS = [
    ("chest pain", 35),         # (symptom keyword, min age to trigger)
    ("chest tightness", 35),
    ("difficulty breathing", 0),
    ("can't breathe", 0),
    ("stroke", 0),
    ("unconscious", 0),
    ("seizure", 0),
    ("severe bleeding", 0),
    ("paralysis", 0),
]

# ─── SYMPTOM URGENCY SCORES: Higher = more urgent ─────────────────────────────

URGENCY_SCORES = {
    "chest pain": 9,
    "diaphoresis": 7,          # Sweating
    "difficulty breathing": 8,
    "high fever": 7,
    "fever": 5,
    "headache": 3,
    "nausea": 3,
    "fatigue": 2,
    "cough": 3,
    "vomiting": 4,
    "dizziness": 5,
    "unspecified complaint": 2,
}

# ─── COMORBIDITY MULTIPLIERS: Some conditions raise urgency ──────────────────

COMORBIDITY_MULTIPLIERS = {
    "hypertension": 1.3,
    "diabetes": 1.2,
    "heart disease": 1.5,
    "copd": 1.3,
    "kidney disease": 1.2,
}


class TriageAgent:
    """
    Triage Agent — no LLM needed here, pure rule-based scoring.
    This is faster and more reliable for life-or-death decisions.
    """

    def run(self, intake: PatientIntake, normalized: NormalizedSymptoms) -> TriageResult:
        print(f"[TriageAgent] Evaluating {len(normalized.symptoms)} symptoms...")

        # ── STEP 1: Check emergency patterns first ────────────────────────────
        for pattern, min_age in EMERGENCY_PATTERNS:
            if (pattern in intake.symptom_text.lower()
                    and intake.age >= min_age):
                print(f"  [TriageAgent] EMERGENCY rule fired: {pattern}")
                return TriageResult(
                    risk_level="emergent",
                    confidence=0.97,
                    justification=f"Emergency pattern detected: '{pattern}' in patient aged {intake.age}.",
                    triggered_rules=[f"R_EMERG: {pattern}"],
                )

        # ── STEP 2: Calculate urgency score from symptoms ─────────────────────
        base_score = 0
        triggered_rules = []

        for symptom in normalized.symptoms:
            score = URGENCY_SCORES.get(symptom.name.lower(), 3)
            # Severity multiplier: severity 8-10 counts more
            severity_mult = 1.0 + (symptom.severity - 5) * 0.1
            base_score += score * max(0.5, severity_mult)

        # Normalize to 0-10
        base_score = min(10, base_score / max(1, len(normalized.symptoms)))

        # ── STEP 3: Apply comorbidity multipliers ─────────────────────────────
        multiplier = 1.0
        for comorbidity in intake.comorbidities:
            if comorbidity.lower() in COMORBIDITY_MULTIPLIERS:
                multiplier = max(multiplier, COMORBIDITY_MULTIPLIERS[comorbidity.lower()])
                triggered_rules.append(f"Comorbidity: {comorbidity}")

        final_score = base_score * multiplier

        # Duration also raises urgency: >7 days = more concerning
        if intake.duration_days > 7:
            final_score *= 1.15
            triggered_rules.append("Duration >7 days")

        print(f"  [TriageAgent] Final urgency score: {final_score:.2f}")

        # ── STEP 4: Convert score to risk level ───────────────────────────────
        if final_score >= 8:
            risk_level = "urgent"
            confidence = 0.85
            justification = f"High urgency score ({final_score:.1f}/10). Multiple severe symptoms detected."
        elif final_score >= 5:
            risk_level = "routine"
            confidence = 0.80
            justification = f"Moderate urgency score ({final_score:.1f}/10). Schedule appointment soon."
        else:
            risk_level = "self-care"
            confidence = 0.75
            justification = f"Low urgency score ({final_score:.1f}/10). Symptoms appear mild."

        return TriageResult(
            risk_level=risk_level,
            confidence=confidence,
            justification=justification,
            triggered_rules=triggered_rules,
        )
