"""
agents/normalization_agent.py
------------------------------
AGENT 1: NORMALIZATION AGENT
-----------------------------
PURPOSE: Convert the patient's messy free-text symptoms into clean, structured data.

EXAMPLE:
  Input:  "My chest hurts and I've been sweating a lot for 2 days"
  Output: [
    SymptomObject(name="chest pain", icd_code="R07.9", severity=7),
    SymptomObject(name="diaphoresis", icd_code="R61",  severity=5),
  ]

HOW IT WORKS:
  1. We send the patient's text to the LLM (Claude/GPT)
  2. We give the LLM very specific instructions (a "prompt")
  3. We tell it to respond ONLY in JSON format
  4. We parse the JSON and turn it into our SymptomObject schema
"""

import json
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from langchain_core.messages import HumanMessage, SystemMessage
from schemas.models import PatientIntake, NormalizedSymptoms, SymptomObject


# ─── THE PROMPT: Instructions we give the LLM ────────────────────────────────

NORMALIZATION_SYSTEM_PROMPT = """
You are a clinical NLP specialist. Your job is to convert patient symptom descriptions 
into structured medical data.

Given a patient description, extract ALL symptoms and return ONLY a JSON object.
No explanation, no markdown — just the raw JSON.

JSON format:
{
  "symptoms": [
    {
      "name": "symptom name in English",
      "icd_code": "ICD-10 code if known, else null",
      "severity": <integer 1-10 based on description>,
      "duration_days": <integer or null>
    }
  ]
}

Rules:
- Extract every symptom mentioned
- Severity: 1-3 = mild, 4-6 = moderate, 7-10 = severe
- Use standard medical terminology for names
- If patient uses Hindi/Telugu/other language, translate to English
"""


# ─── THE AGENT CLASS ──────────────────────────────────────────────────────────

class NormalizationAgent:
    """
    This class is the Normalization Agent.
    
    To use it:
        agent = NormalizationAgent()
        result = agent.run(patient_intake)
    """

    def __init__(self):
        # Initialize the LLM connection
        # In production, use your actual API key via environment variable
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",       # Fast and cheap model
            temperature=0,             # 0 = deterministic (no creativity — we want facts)
            openai_api_key=os.getenv("OPENAI_API_KEY", "your-api-key-here"),
        )

    def run(self, intake: PatientIntake) -> NormalizedSymptoms:
        """
        Main function. Takes a PatientIntake, returns NormalizedSymptoms.
        """
        print(f"[NormalizationAgent] Processing: '{intake.symptom_text}'")

        # Build the user message with patient info
        user_message = f"""
Patient information:
- Age: {intake.age}, Sex: {intake.sex}
- Duration: {intake.duration_days} days
- Languages: {intake.language_pref}

Symptom description: "{intake.symptom_text}"

Extract all symptoms from this description.
"""

        try:
            # Call the LLM
            response = self.llm.invoke([
                SystemMessage(content=NORMALIZATION_SYSTEM_PROMPT),
                HumanMessage(content=user_message),
            ])

            # Parse the JSON response
            raw_json = response.content.strip()

            # Sometimes LLMs add markdown code fences — remove them
            raw_json = raw_json.replace("```json", "").replace("```", "").strip()

            data = json.loads(raw_json)

            # Convert raw dict to our Pydantic schema objects
            symptoms = [SymptomObject(**s) for s in data["symptoms"]]

            print(f"[NormalizationAgent] Found {len(symptoms)} symptoms")
            return NormalizedSymptoms(symptoms=symptoms, raw_text=intake.symptom_text)

        except Exception as e:
            print(f"[NormalizationAgent] LLM failed: {e}. Using fallback.")
            return self._fallback_normalization(intake)

    def _fallback_normalization(self, intake: PatientIntake) -> NormalizedSymptoms:
        """
        If the LLM fails or is unavailable, use a simple keyword-based fallback.
        This is the 'rule-only' mode mentioned in the project document.
        """
        KEYWORD_MAP = {
            "chest pain": SymptomObject(name="chest pain", icd_code="R07.9", severity=8, duration_days=intake.duration_days),
            "headache": SymptomObject(name="headache", icd_code="R51", severity=5, duration_days=intake.duration_days),
            "fever": SymptomObject(name="fever", icd_code="R50.9", severity=6, duration_days=intake.duration_days),
            "cough": SymptomObject(name="cough", icd_code="R05", severity=4, duration_days=intake.duration_days),
            "fatigue": SymptomObject(name="fatigue", icd_code="R53.83", severity=5, duration_days=intake.duration_days),
            "nausea": SymptomObject(name="nausea", icd_code="R11.0", severity=4, duration_days=intake.duration_days),
        }

        found = []
        text_lower = intake.symptom_text.lower()
        for keyword, symptom_obj in KEYWORD_MAP.items():
            if keyword in text_lower:
                found.append(symptom_obj)

        # If nothing matched, create a generic symptom
        if not found:
            found.append(SymptomObject(
                name="unspecified complaint",
                icd_code="R69",
                severity=3,
                duration_days=intake.duration_days,
            ))

        return NormalizedSymptoms(symptoms=found, raw_text=intake.symptom_text)
