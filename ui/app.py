"""
ui/app.py  —  Streamlit Frontend
----------------------------------
This is the PATIENT-FACING UI.
Streamlit turns Python code into a web app automatically — no HTML/CSS needed!

To run this:
  streamlit run ui/app.py

It calls the FastAPI backend at http://localhost:8000/analyze
Make sure the backend is running first!
"""

import streamlit as st
import requests
import json
import hashlib
import time

# ─── PAGE CONFIG ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="AI Telehealth Assistant",
    page_icon="🏥",
    layout="wide",
)

# ─── HEADER ──────────────────────────────────────────────────────────────────

st.title("🏥 AI Integrative Telehealth Assistant")
st.markdown("*Powered by Infosys AI — HYSEA Capstone Project*")
st.divider()

# ─── SIDEBAR: System info ─────────────────────────────────────────────────────

with st.sidebar:
    st.header("ℹ️ About")
    st.info("""
    This system provides AI-assisted healthcare navigation across:
    - 🩺 Allopathy (Modern Medicine)
    - 🌿 Ayurveda *(Phase 2)*
    - 💊 Homeopathy *(Phase 4)*

    **Disclaimer:** This is a decision support tool.
    Always consult a licensed physician.
    """)

    st.header("⚙️ Settings")
    api_url = st.text_input("API URL", value="http://localhost:8000")
    st.caption("Make sure the FastAPI server is running")

# ─── MAIN FORM ────────────────────────────────────────────────────────────────

st.subheader("📋 Patient Intake Form")

col1, col2 = st.columns(2)

with col1:
    age = st.number_input("Age", min_value=1, max_value=120, value=35)
    sex = st.radio("Biological Sex", ["M", "F"], horizontal=True)
    duration_days = st.number_input("Symptom duration (days)", min_value=0, max_value=365, value=2)
    language = st.selectbox(
        "Preferred language",
        options=["en", "hi", "te", "ta", "bn", "mr"],
        format_func=lambda x: {
            "en": "English", "hi": "Hindi", "te": "Telugu",
            "ta": "Tamil", "bn": "Bengali", "mr": "Marathi"
        }[x]
    )

with col2:
    symptom_text = st.text_area(
        "Describe your symptoms",
        placeholder="e.g. I have chest pain and I'm sweating a lot...\nआप हिंदी में भी लिख सकते हैं।",
        height=120,
    )
    comorbidities = st.multiselect(
        "Known medical conditions",
        ["hypertension", "diabetes", "heart disease", "asthma", "kidney disease", "thyroid disorder"],
    )
    medications = st.text_input(
        "Current medications (comma separated)",
        placeholder="e.g. amlodipine, metformin"
    )

# ─── SUBMIT ───────────────────────────────────────────────────────────────────

st.divider()
submit = st.button("🔍 Analyze & Get Care Plan", type="primary", use_container_width=True)

if submit:
    if not symptom_text.strip():
        st.error("Please describe your symptoms.")
    else:
        # Build the patient hash (anonymized ID from age+sex)
        patient_hash = "p_" + hashlib.md5(f"{age}{sex}{time.time()}".encode()).hexdigest()[:8]

        # Parse medications
        meds_list = [m.strip() for m in medications.split(",") if m.strip()]

        # Build the intake payload
        payload = {
            "patient_hash": patient_hash,
            "age": age,
            "sex": sex,
            "symptom_text": symptom_text,
            "duration_days": duration_days,
            "comorbidities": comorbidities,
            "medications": meds_list,
            "modality_preferences": ["allopathy"],
            "language_pref": language,
        }

        # Call the API
        with st.spinner("Analyzing your symptoms..."):
            try:
                response = requests.post(f"{api_url}/analyze", json=payload, timeout=30)
                response.raise_for_status()
                result = response.json()

                # ── Display Results ────────────────────────────────────────────

                st.success("Analysis complete!")
                st.divider()

                # Risk Level — colored badge
                risk = result["risk_level"]
                risk_colors = {
                    "emergent": "🔴",
                    "urgent": "🟠",
                    "routine": "🟡",
                    "self-care": "🟢",
                }
                st.subheader(f"{risk_colors.get(risk, '⚪')} Risk Level: {risk.upper()}")
                st.caption(result.get("triage_justification", ""))

                # Emergency alert
                if risk == "emergent":
                    st.error("⚠️ EMERGENCY: Please call 108 or go to the nearest emergency room immediately!")

                st.divider()

                # Care Path
                st.subheader("🗺️ Your Care Plan")
                care_path = result.get("care_path", [])
                for step in care_path:
                    with st.expander(f"Step {step['step_number']}: {step['action']}", expanded=True):
                        st.write(f"**Urgency:** {step['urgency']}")
                        if step.get("notes"):
                            st.write(f"**Notes:** {step['notes']}")

                st.divider()

                # Warnings
                warnings = result.get("warnings", [])
                if warnings:
                    st.subheader("⚠️ Safety Warnings")
                    for w in warnings:
                        if w["severity"] == "high":
                            st.error(f"🔴 {w['message']}")
                        elif w["severity"] == "medium":
                            st.warning(f"🟠 {w['message']}")
                        else:
                            st.info(f"🔵 {w['message']}")

                st.divider()

                # Detailed allopathy plan
                allo_raw = result.get("allopathy_plan")
                if allo_raw:
                    allo = json.loads(allo_raw)
                    st.subheader("🩺 Allopathic Treatment Plan")

                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.write("**Recommended Specialist:**", allo.get("specialist"))
                        st.write("**Urgency:**", allo.get("urgency_note"))
                        st.write("**Investigations:**")
                        for inv in allo.get("investigations", []):
                            st.write(f"  • {inv}")
                    with col_b:
                        st.write("**First-line treatment:**")
                        for tx in allo.get("first_line_treatment", []):
                            st.write(f"  • {tx}")
                        st.write("**Red flags (go to ER if):**")
                        for rf in allo.get("red_flags", []):
                            st.write(f"  ⚠️ {rf}")

                    if allo.get("sources"):
                        st.caption("📚 Sources: " + " | ".join(allo["sources"]))

                # Disclaimer
                st.divider()
                st.info("⚕️ **Disclaimer:** This AI tool is for informational support only. It is not a substitute for professional medical advice, diagnosis, or treatment. Always consult a qualified healthcare provider.")

                # Explainability
                with st.expander("🔬 How was this decision made? (Explainability)"):
                    expl = result.get("explainability", {})
                    st.json(expl)

            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to the API server. Make sure to run: `uvicorn main:app --reload` first.")
            except Exception as e:
                st.error(f"Error: {e}")
