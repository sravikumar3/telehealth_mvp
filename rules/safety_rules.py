"""
rules/safety_rules.py
----------------------
This is the SAFETY RULES ENGINE.
It works like a checklist of known dangers.
Before giving any recommendation, the system runs every rule here.

How it works:
  - Each rule has a TRIGGER (what to look for) and an ACTION (what to do)
  - If the patient's data matches a trigger, the rule fires and adds a warning
  - No AI needed here — these are hard-coded medical safety rules
"""

from schemas.models import Warning, PatientIntake
from typing import List


# ─── RULE DEFINITIONS ────────────────────────────────────────────────────────
# Each rule is a dict with:
#   rule_id   : unique name
#   check     : a function that returns True if the rule should fire
#   warning   : the message to show if it fires
#   severity  : "high", "medium", "low"

SAFETY_RULES = [

    {
        "rule_id": "R_EMERG_01",
        "description": "Chest pain in patient over 35 — possible cardiac event",
        "check": lambda intake: (
            any(kw in intake.symptom_text.lower()
                for kw in ["chest pain", "chest tightness", "chest pressure"])
            and intake.age > 35
        ),
        "warning": "EMERGENCY: Chest pain in patient >35. Treat as cardiac event. Allopathy only.",
        "severity": "high",
    },

    {
        "rule_id": "R_HERB_DRUG_01",
        "description": "St. John's Wort with antidepressants (SSRIs) — dangerous interaction",
        "check": lambda intake: (
            any("ssri" in m.lower() or "sertraline" in m.lower()
                or "fluoxetine" in m.lower() or "escitalopram" in m.lower()
                for m in intake.medications)
        ),
        "warning": "INTERACTION: SSRIs detected. St. John's Wort is contraindicated. Consult psychiatrist before any herbal additions.",
        "severity": "high",
    },

    {
        "rule_id": "R_AYURV_CONTRA_01",
        "description": "High BP patients and warming Ayurvedic herbs",
        "check": lambda intake: (
            "hypertension" in [c.lower() for c in intake.comorbidities]
        ),
        "warning": "CAUTION: Patient has hypertension. Avoid warming herbs (pippalī, śuṇṭhī). Use alternative herb set.",
        "severity": "medium",
    },

    {
        "rule_id": "R_ANTICOAG_01",
        "description": "Blood thinners + herbal supplements can cause bleeding",
        "check": lambda intake: (
            any("warfarin" in m.lower() or "aspirin" in m.lower()
                or "clopidogrel" in m.lower()
                for m in intake.medications)
        ),
        "warning": "CAUTION: Anticoagulant medication detected. Many herbal remedies interact. Herb-drug review required.",
        "severity": "high",
    },

    {
        "rule_id": "R_DIABETES_01",
        "description": "Diabetes patients need blood sugar monitoring with herbal remedies",
        "check": lambda intake: (
            "diabetes" in [c.lower() for c in intake.comorbidities]
            and any("metformin" in m.lower() or "insulin" in m.lower()
                    for m in intake.medications)
        ),
        "warning": "CAUTION: Diabetic patient on medication. Some Ayurvedic herbs lower blood sugar — risk of hypoglycemia.",
        "severity": "medium",
    },

]


# ─── MAIN FUNCTION: Run all rules ─────────────────────────────────────────────

def run_safety_checks(intake: PatientIntake) -> List[Warning]:
    """
    Pass a PatientIntake object in.
    Get back a list of Warning objects that fired.

    Usage:
        warnings = run_safety_checks(patient_intake)
        if warnings:
            print("Warnings found:", warnings)
    """
    fired_warnings: List[Warning] = []

    for rule in SAFETY_RULES:
        try:
            if rule["check"](intake):
                fired_warnings.append(Warning(
                    rule_id=rule["rule_id"],
                    message=rule["warning"],
                    severity=rule["severity"],
                ))
                print(f"  [Safety] Rule fired: {rule['rule_id']}")
        except Exception as e:
            print(f"  [Safety] Rule {rule['rule_id']} check failed: {e}")

    return fired_warnings
