"""
main.py  —  FastAPI Backend
----------------------------
This is the WEB SERVER for our system.

FastAPI creates REST API endpoints that:
  - Accept patient data as JSON
  - Run the full pipeline
  - Return the care plan as JSON

Why FastAPI?
  - Very fast (async)
  - Auto-generates API documentation at /docs
  - Pydantic integration built-in

To run this server:
  uvicorn main:app --reload --port 8000

Then open:
  http://localhost:8000/docs  ← Interactive API documentation (try it out here!)
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from schemas.models import PatientIntake, FinalCarePlan
from agents.orchestrator import TelehealthOrchestrator
import uvicorn

# ─── CREATE THE APP ───────────────────────────────────────────────────────────

app = FastAPI(
    title="AI Telehealth Orchestrator — MVP",
    description="Integrative multilingual telehealth decision support system",
    version="1.0.0",
)

# Allow the Streamlit frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── INITIALIZE ORCHESTRATOR ──────────────────────────────────────────────────
# We initialize once at startup — agents are expensive to create repeatedly
orchestrator = TelehealthOrchestrator()


# ─── ENDPOINTS ────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    """Health check endpoint."""
    return {"status": "running", "version": "1.0.0"}


@app.post("/analyze", response_model=FinalCarePlan)
def analyze_patient(intake: PatientIntake) -> FinalCarePlan:
    """
    MAIN ENDPOINT: Submit patient intake, get care plan back.

    Send a POST request with JSON body like:
    {
        "patient_hash": "p_001",
        "age": 45,
        "sex": "M",
        "symptom_text": "chest pain and sweating for 2 days",
        "duration_days": 2,
        "comorbidities": ["hypertension"],
        "medications": ["amlodipine"],
        "modality_preferences": ["allopathy"],
        "language_pref": "en"
    }
    """
    try:
        care_plan = orchestrator.run(intake)
        return care_plan
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")


@app.get("/health")
def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "agents": ["normalization", "triage", "safety", "allopathy", "synthesizer"],
        "version": "mvp_v1.0",
    }


# ─── RUN THE SERVER ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
