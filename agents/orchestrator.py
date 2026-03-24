"""
agents/orchestrator.py
-----------------------
THE ORCHESTRATOR — The Brain of the System
-------------------------------------------
PURPOSE: Run all agents IN ORDER and combine results into a FinalCarePlan.

This is the most important file. It:
  1. Takes a PatientIntake as input
  2. Calls each agent one by one (like an assembly line)
  3. Handles errors gracefully
  4. Returns a complete FinalCarePlan

FLOW:
  PatientIntake
    → NormalizationAgent  (raw text → structured symptoms)
    → TriageAgent         (structured symptoms → risk level)
    → SafetyRules         (patient data → warnings list)
    → AllopathyAgent      (everything → treatment plan)
    → Synthesizer         (all results → final JSON)

This matches the Architecture Overview in your project document exactly:
  Intake → Normalization → Triage → Orchestrator → Specialist → Safety →
  Synthesis → Translation → Clinician Feedback → Audit Store
"""

import json
import hashlib
import datetime
import os
from pathlib import Path

from schemas.models import PatientIntake, FinalCarePlan, CarePlanStep
from agents.normalization_agent import NormalizationAgent
from agents.triage_agent import TriageAgent
from agents.allopathy_agent import AllopathyAgent
from rules.safety_rules import run_safety_checks


class TelehealthOrchestrator:
    """
    The main pipeline. Initialize once, call .run(intake) for each patient.
    """

    def __init__(self):
        # Initialize all agents
        self.normalization_agent = NormalizationAgent()
        self.triage_agent = TriageAgent()
        self.allopathy_agent = AllopathyAgent()

        # Audit log directory
        self.audit_dir = Path("audit_logs")
        self.audit_dir.mkdir(exist_ok=True)

        print("[Orchestrator] All agents initialized.")

    def run(self, intake: PatientIntake) -> FinalCarePlan:
        """
        Main pipeline. Takes PatientIntake, returns FinalCarePlan.

        Usage:
            orchestrator = TelehealthOrchestrator()
            plan = orchestrator.run(patient_intake)
        """
        print(f"\n{'='*50}")
        print(f"[Orchestrator] Starting pipeline for: {intake.patient_hash}")
        print(f"{'='*50}")

        # ── STEP 1: Normalize symptoms ────────────────────────────────────────
        print("\n[STEP 1] Normalizing symptoms...")
        normalized = self.normalization_agent.run(intake)

        # ── STEP 2: Triage ────────────────────────────────────────────────────
        print("\n[STEP 2] Running triage...")
        triage = self.triage_agent.run(intake, normalized)
        print(f"  Risk level: {triage.risk_level} (confidence: {triage.confidence:.0%})")

        # ── STEP 3: Safety checks ─────────────────────────────────────────────
        print("\n[STEP 3] Running safety checks...")
        warnings = run_safety_checks(intake)
        print(f"  Warnings found: {len(warnings)}")

        # ── STEP 4: Generate allopathy plan ───────────────────────────────────
        print("\n[STEP 4] Generating allopathy plan...")
        allo_plan = self.allopathy_agent.run(intake, normalized, triage)

        # ── STEP 5: Synthesize everything into a FinalCarePlan ────────────────
        print("\n[STEP 5] Synthesizing final care plan...")
        care_path = self._build_care_path(triage, allo_plan)
        final_plan = FinalCarePlan(
            patient_hash=intake.patient_hash,
            risk_level=triage.risk_level,
            triage_justification=triage.justification,
            care_path=care_path,
            warnings=warnings,
            allopathy_plan=json.dumps(allo_plan, indent=2),
            provenance=allo_plan.get("sources", []),
            explainability={
                "triage_score_rules": triage.triggered_rules,
                "triage_confidence": triage.confidence,
                "symptoms_detected": [s.name for s in normalized.symptoms],
                "safety_rules_fired": [w.rule_id for w in warnings],
            },
            language=intake.language_pref,
        )

        # ── STEP 6: Save to audit log ─────────────────────────────────────────
        self._save_audit_log(intake, final_plan)

        print(f"\n[Orchestrator] Pipeline complete. Risk: {final_plan.risk_level}")
        return final_plan

    def _build_care_path(self, triage, allo_plan: dict) -> list:
        """Convert allopathy plan into ordered CarePlanStep list."""
        steps = []

        # Step 1: See specialist
        steps.append(CarePlanStep(
            step_number=1,
            action=f"Consult {allo_plan.get('specialist', 'General Practitioner')}",
            modality="allopathy",
            urgency=allo_plan.get("urgency_note", "As soon as possible"),
            notes=f"Risk level: {triage.risk_level}",
        ))

        # Step 2: Investigations
        investigations = allo_plan.get("investigations", [])
        if investigations:
            steps.append(CarePlanStep(
                step_number=2,
                action=f"Get tests: {', '.join(investigations[:3])}",
                modality="allopathy",
                urgency="Before specialist visit if possible",
                notes="Bring reports to consultation",
            ))

        # Step 3: First-line treatment
        treatments = allo_plan.get("first_line_treatment", [])
        if treatments:
            steps.append(CarePlanStep(
                step_number=3,
                action=f"Initial care: {treatments[0]}",
                modality="allopathy",
                urgency="Start immediately",
                notes="; ".join(treatments[1:3]) if len(treatments) > 1 else None,
            ))

        return steps

    def _save_audit_log(self, intake: PatientIntake, plan: FinalCarePlan):
        """
        Save a JSON audit log for every consultation.
        Required by the project spec: 'Persist JSON transcript (hashed patient_id, timestamp, model_version)'
        """
        log_entry = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "patient_hash": intake.patient_hash,
            "risk_level": plan.risk_level,
            "symptoms_count": len(plan.explainability.get("symptoms_detected", [])),
            "warnings_count": len(plan.warnings),
            "language": plan.language,
            "model_version": "mvp_v1.0",
        }

        log_file = self.audit_dir / f"{intake.patient_hash}_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(log_file, "w") as f:
            json.dump(log_entry, f, indent=2)

        print(f"  [Audit] Log saved: {log_file.name}")
