"""
schemas/models.py
-----------------
These are the DATA BLUEPRINTS for our system.
Think of them as "forms" — every piece of data must match the form exactly.
Pydantic automatically validates the data and gives helpful errors if something is wrong.
"""

from pydantic import BaseModel, Field
from typing import List, Optional


# ─── INPUT: What the patient tells us ────────────────────────────────────────

class PatientIntake(BaseModel):
    """
    This is filled when a patient submits the form.
    Every field is validated automatically by Pydantic.
    """
    patient_hash: str = Field(..., description="Anonymous ID like p_abc123")
    age: int = Field(..., ge=0, le=120, description="Patient age in years")
    sex: str = Field(..., description="M or F — used for clinical relevance")
    symptom_text: str = Field(..., description="Raw text: e.g. 'chest pain and sweating'")
    duration_days: int = Field(..., ge=0, description="How many days symptoms have lasted")
    comorbidities: List[str] = Field(default=[], description="e.g. ['hypertension', 'diabetes']")
    medications: List[str] = Field(default=[], description="e.g. ['amlodipine', 'metformin']")
    modality_preferences: List[str] = Field(
        default=["allopathy"],
        description="Which systems patient wants: allopathy, ayurveda, homeopathy"
    )
    language_pref: str = Field(default="en", description="Language code: en, hi, te, ta, bn, mr")


# ─── NORMALIZED SYMPTOMS: After AI processes raw text ────────────────────────

class SymptomObject(BaseModel):
    """
    After the Normalization Agent runs, we get structured symptoms.
    Example: "chest pain" → SymptomObject(name='chest pain', icd_code='R07.9', severity=8)
    """
    name: str
    icd_code: Optional[str] = None       # International disease code
    severity: int = Field(..., ge=1, le=10)  # 1=mild, 10=very severe
    duration_days: Optional[int] = None


class NormalizedSymptoms(BaseModel):
    symptoms: List[SymptomObject]
    raw_text: str


# ─── TRIAGE RESULT: Risk level decision ──────────────────────────────────────

class TriageResult(BaseModel):
    """
    The Triage Agent outputs this.
    risk_level controls the entire care path downstream.
    """
    risk_level: str = Field(
        ...,
        description="One of: emergent | urgent | routine | self-care"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="0.0 to 1.0")
    justification: str = Field(..., description="Why this risk level was chosen")
    triggered_rules: List[str] = Field(default=[], description="Safety rules that fired")


# ─── CARE PLAN: The final recommendation ─────────────────────────────────────

class CarePlanStep(BaseModel):
    """One step in the patient's care journey."""
    step_number: int
    action: str           # e.g. "Visit cardiologist"
    modality: str         # e.g. "allopathy"
    urgency: str          # e.g. "within 24 hours"
    notes: Optional[str] = None


class Warning(BaseModel):
    """A safety warning — e.g. drug-herb interaction."""
    rule_id: str
    message: str
    severity: str         # "high", "medium", "low"


class FinalCarePlan(BaseModel):
    """
    This is the COMPLETE OUTPUT of the whole system.
    Everything gets merged here at the end.
    """
    patient_hash: str
    risk_level: str
    triage_justification: str
    care_path: List[CarePlanStep]
    warnings: List[Warning]
    allopathy_plan: Optional[str] = None
    provenance: List[str] = Field(default=[], description="Source citations")
    explainability: dict = Field(default={}, description="Why each recommendation was made")
    language: str = "en"
