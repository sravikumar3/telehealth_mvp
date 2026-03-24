# AI Integrative Multilingual Telehealth Orchestrator — MVP
## HYSEA Capstone Project | Infosys Limited

---

## 🗂️ Project Structure

```
telehealth_mvp/
│
├── main.py                    ← FastAPI backend server (START HERE to run the API)
├── requirements.txt           ← Python packages to install
│
├── schemas/
│   └── models.py              ← Data blueprints (PatientIntake, FinalCarePlan, etc.)
│
├── agents/
│   ├── orchestrator.py        ← BRAIN: runs all agents in order
│   ├── normalization_agent.py ← Agent 1: raw text → structured symptoms
│   ├── triage_agent.py        ← Agent 2: decides urgency level
│   └── allopathy_agent.py     ← Agent 3: generates treatment plan
│
├── rules/
│   └── safety_rules.py        ← Hard-coded drug interaction & safety checks
│
├── ui/
│   └── app.py                 ← Streamlit patient-facing web UI
│
└── audit_logs/                ← Auto-created: stores every consultation log
```

---

## 🚀 How to Set Up and Run (Step by Step)

### Step 1: Install Python
Make sure you have Python 3.10 or newer.
```bash
python --version   # Should show 3.10 or higher
```

### Step 2: Create a virtual environment (good practice)
```bash
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
```

### Step 3: Install dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Set your OpenAI API key
```bash
# Mac/Linux
export OPENAI_API_KEY="sk-your-key-here"

# Windows
set OPENAI_API_KEY=sk-your-key-here
```
> Note: You can also create a `.env` file with: `OPENAI_API_KEY=sk-your-key-here`

### Step 5: Start the backend API server
```bash
uvicorn main:app --reload --port 8000
```
Open http://localhost:8000/docs to see the interactive API documentation.

### Step 6: Start the Streamlit UI (in a new terminal)
```bash
streamlit run ui/app.py
```
Open http://localhost:8501 to use the app.

---

## 🧪 Test the API directly

You can test the system without the UI using curl:

```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_hash": "p_test001",
    "age": 45,
    "sex": "M",
    "symptom_text": "chest pain and sweating for 2 days",
    "duration_days": 2,
    "comorbidities": ["hypertension"],
    "medications": ["amlodipine"],
    "modality_preferences": ["allopathy"],
    "language_pref": "en"
  }'
```

---

## 📊 MVP Features (Phase 1)

| Feature | Status |
|---------|--------|
| Patient intake form (Streamlit) | ✅ Done |
| Symptom normalization (LLM) | ✅ Done |
| Triage / risk stratification | ✅ Done |
| Allopathy plan generation | ✅ Done |
| Safety & drug interaction rules | ✅ Done |
| Audit logging | ✅ Done |
| REST API (FastAPI) | ✅ Done |
| Explainability output | ✅ Done |

---

## 🔮 Future Phases

| Phase | What to add |
|-------|------------|
| Phase 2 | Ayurveda agent + multilingual glossary + Hindi/Telugu UI |
| Phase 3 | Herb-drug interaction checker + multi-modal synthesis |
| Phase 4 | Homeopathy agent + home remedial evidence categorization |
| Phase 5 | Speech input + historical pattern personalization |

---

## ⚠️ Important Disclaimer

This system is a **proof-of-concept** built for an academic capstone project.
It is NOT a certified medical device and should NOT be used for actual clinical decisions.
Always consult a licensed healthcare provider.
