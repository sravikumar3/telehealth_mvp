"""
agents/allopathy_agent.py
--------------------------
AGENT 3: ALLOPATHY SPECIALIST AGENT
-------------------------------------
PURPOSE: Generate an evidence-based allopathic (modern medicine) treatment plan.

This agent uses the LLM with a very specific medical prompt to generate:
  - Recommended specialist to see
  - Likely investigations (blood tests, ECG, etc.)
  - First-line treatments (per standard guidelines)
  - Red flags to watch for
  - Source references (provenance)

IMPORTANT SAFETY NOTE:
  This is a DECISION SUPPORT tool, not a replacement for a real doctor.
  The system always reminds users of this.
"""

import json
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from schemas.models import PatientIntake, NormalizedSymptoms, TriageResult


ALLOPATHY_SYSTEM_PROMPT = """
You are an experienced clinical decision support system following WHO and ICMR guidelines.
You help general practitioners by suggesting evidence-based management plans.

Given patient information, generate a structured treatment recommendation.
Respond ONLY in JSON. No markdown, no explanation.

JSON format:
{
  "specialist": "which specialist to refer to",
  "urgency_note": "how urgently to see the specialist",
  "investigations": ["list", "of", "tests", "to", "order"],
  "first_line_treatment": ["step 1", "step 2", ...],
  "red_flags": ["warning signs that need emergency care"],
  "sources": ["WHO guideline XYZ", "ICMR 2023 protocol for..."],
  "disclaimer": "This is a clinical support tool, not a substitute for medical examination."
}

Always follow evidence-based guidelines. Do not recommend specific drug dosages.
Always include a disclaimer.
"""


class AllopathyAgent:
    """
    Allopathy Specialist Agent.
    Produces a structured clinical plan using LLM + evidence-based prompting.
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,   # Very low creativity — we want factual medical info
            openai_api_key=os.getenv("OPENAI_API_KEY", "your-api-key-here"),
        )

    def run(
        self,
        intake: PatientIntake,
        normalized: NormalizedSymptoms,
        triage: TriageResult,
    ) -> dict:
        """
        Returns a dict with the complete allopathic care plan.
        """
        print("[AllopathyAgent] Generating treatment plan...")

        # Don't generate a plan for emergencies — send to ER directly
        if triage.risk_level == "emergent":
            return {
                "specialist": "Emergency Department",
                "urgency_note": "IMMEDIATE — call ambulance or go to ER now",
                "investigations": ["12-lead ECG", "Troponin", "CBC", "CMP"],
                "first_line_treatment": ["Call 108 (Indian emergency number)", "Do not eat or drink", "Sit or lie down comfortably"],
                "red_flags": ["Loss of consciousness", "Severe chest pain radiating to arm/jaw"],
                "sources": ["AHA STEMI Guidelines 2023"],
                "disclaimer": "This is an AI tool. Call emergency services immediately.",
            }

        # Build the prompt with patient data
        symptom_list = ", ".join([s.name for s in normalized.symptoms])
        comorbidities = ", ".join(intake.comorbidities) if intake.comorbidities else "none"
        medications = ", ".join(intake.medications) if intake.medications else "none"

        user_message = f"""
Patient: {intake.age}-year-old {intake.sex}
Risk level: {triage.risk_level}
Symptoms: {symptom_list}
Duration: {intake.duration_days} days
Comorbidities: {comorbidities}
Current medications: {medications}

Generate an evidence-based allopathic management plan for this patient.
"""

        try:
            response = self.llm.invoke([
                SystemMessage(content=ALLOPATHY_SYSTEM_PROMPT),
                HumanMessage(content=user_message),
            ])

            raw_json = response.content.strip()
            raw_json = raw_json.replace("```json", "").replace("```", "").strip()
            plan = json.loads(raw_json)
            print("[AllopathyAgent] Plan generated successfully")
            return plan

        except Exception as e:
            print(f"[AllopathyAgent] LLM failed: {e}. Using fallback.")
            return self._fallback_plan(triage)

    def _fallback_plan(self, triage: TriageResult) -> dict:
        """Simple fallback if LLM is unavailable."""
        return {
            "specialist": "General Practitioner",
            "urgency_note": f"See a doctor — risk level: {triage.risk_level}",
            "investigations": ["Complete blood count", "Basic metabolic panel"],
            "first_line_treatment": ["Consult a licensed physician"],
            "red_flags": ["Worsening symptoms", "High fever", "Difficulty breathing"],
            "sources": ["Clinical judgment — LLM unavailable"],
            "disclaimer": "AI system in fallback mode. Please see a doctor.",
        }
