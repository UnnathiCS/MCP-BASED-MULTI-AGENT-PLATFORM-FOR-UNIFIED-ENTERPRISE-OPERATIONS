import streamlit as st
import requests
import json

# Architecture:
# Streamlit Dashboard (this file)
# ↓
# Support Agent (FastAPI) - http://127.0.0.1:8000
# Document Review Agent (FastAPI) - http://127.0.0.1:8001
# ↓
# Future: MCP Orchestration Layer to coordinate agents

API_URL = "http://127.0.0.1:8001/review"
CUSTOMER_API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Enterprise AI Agent Dashboard",
    layout="wide"
)

# ===============================
# Sidebar Navigation
# ===============================

st.sidebar.title("🤖 AI Agent Suite")

agent_choice = st.sidebar.radio(
    "Select Agent",
    [
        "📄 Document Review Agent",
        "📧 Email Agent (Coming Soon)",
        "🎧 Voice Agent (Coming Soon)",
        "🛠 Support Agent"
    ]
)


# Activity feed (simple in-memory session store for demo/teaching)
if "activity_feed" not in st.session_state:
    st.session_state.activity_feed = []


def append_activity(entry: str):
    st.session_state.activity_feed.insert(0, entry)


def check_agent_running(url: str):
    try:
        r = requests.get(url + "/docs", timeout=2)
        return True
    except Exception:
        return False

# ===============================
# DOCUMENT REVIEW AGENT UI
# ===============================

if agent_choice == "📄 Document Review Agent":

    st.title("📄 Document Review Agent")
    st.markdown("Upload a legal document to assess compliance risk.")

    uploaded_file = st.file_uploader("Upload PDF Document", type=["pdf"])

    if uploaded_file is not None:

        if st.button("Analyze Document"):

            with st.spinner("Analyzing document..."):

                files = {"file": uploaded_file.getvalue()}

                response = requests.post(API_URL, files=files)

                if response.status_code != 200:
                    st.error("Error connecting to backend.")
                else:
                    result = response.json()

                    # -----------------------------
                    # Display Document Type
                    # -----------------------------
                    st.subheader("📌 Document Classification")
                    st.write(f"**Type:** {result.get('document_type', 'N/A')}")

                    # -----------------------------
                    # Risk and Compliance
                    # -----------------------------
                    risk_level = result.get("risk_level", "N/A")
                    compliance_score = result.get("compliance_score", 0)

                    color = "green" if risk_level in ["Low"] else ("orange" if risk_level in ["Moderate"] else "red")

                    st.subheader("⚠️ Risk Assessment")
                    st.markdown(f"<h2 style='color:{color};'>{risk_level} </h2>", unsafe_allow_html=True)

                    st.write(f"**Compliance Score:** {compliance_score}%")

                    # -----------------------------
                    # Agent collaboration message (if any)
                    # -----------------------------
                    agent_action = result.get("agent_action")
                    if agent_action:
                        st.warning(f"⚠ {agent_action}")

                    # -----------------------------
                    # Support ticket (if created)
                    # -----------------------------
                    if result.get("support_ticket"):
                        st.markdown("### 🔔 Support Ticket Created")
                        ticket = result["support_ticket"]
                        try:
                            st.json(ticket)
                        except Exception:
                            st.write(ticket)

                    # -----------------------------
                    # Clause Analysis + Coverage
                    # -----------------------------
                    st.subheader("📑 Clause Analysis")

                    clause_analysis = result.get("clause_analysis", {})
                    coverage = result.get("coverage", {})

                    for clause, details in clause_analysis.items():
                        status = details.get("status", "Unknown")
                        symbol = coverage.get(clause, "-")

                        with st.expander(f"{symbol} {clause} — {status}"):
                            st.write(f"**Similarity Score:** {details.get('similarity_score')}")
                            st.write(f"**Weight:** {details.get('weight')}")
                            st.markdown("**Evidence Snippet:**")
                            st.info(details.get('snippet', ""))

                    # -----------------------------
                    # Explanation
                    # -----------------------------
                    st.subheader("🧠 AI Explanation")
                    st.write(result.get("explanation", ""))

                    # -----------------------------
                    # Suggestions
                    # -----------------------------
                    suggestions = result.get("suggestions", {})

                    if suggestions:
                        st.subheader("🔧 Suggested Improvements")
                        for clause, suggestion in suggestions.items():
                            st.warning(f"**{clause}:** {suggestion}")
                    else:
                        st.success("No improvements required. Document meets compliance standards.")

                    # log activity
                    append_activity(f"Document analyzed — Type: {result.get('document_type', 'N/A')} | Risk: {risk_level}")


# ===============================
# PLACEHOLDER PAGES
# ===============================

elif agent_choice == "📧 Email Agent (Coming Soon)":
    st.title("📧 Email Agent")
    st.info("This module will manage automated email triaging and responses.")

elif agent_choice == "🎧 Voice Agent (Coming Soon)":
    st.title("🎧 Voice Agent")
    st.info("This module will handle voice-based compliance queries using Whisper ASR.")

elif agent_choice == "🛠 Support Agent":
    st.title("🛠 Support Agent")

    st.markdown("Use this panel to submit text or voice support requests to the Support Agent API.")

    st.subheader("Text Support Request")
    ticket_id = st.text_input("Ticket ID (optional)")
    message = st.text_area("Message")

    if st.button("Send Text Request"):
        payload = {"ticket_id": ticket_id or "UI-" + str(len(st.session_state.activity_feed) + 1), "message": message}
        try:
            r = requests.post(CUSTOMER_API_URL + "/it-support/text", json=payload, timeout=5)
            if r.status_code == 200:
                res = r.json()
                st.success(f"Decision: {res.get('decision')}")
                st.write(f"Category: {res.get('category')}")
                st.write(f"Priority: {res.get('priority')}")
                st.write(f"Reason: {res.get('reason')}")
                st.write(f"Answer: {res.get('answer')}")
                append_activity(f"Ticket {payload['ticket_id']} created via UI — {res.get('decision')}")
            else:
                st.error("Support agent returned an error.")
        except Exception:
            st.error("Unable to reach Support Agent API.")

    st.subheader("Voice Support Request (upload audio)")
    voice_ticket = st.text_input("Voice Ticket ID (optional)")
    audio_file = st.file_uploader("Upload audio file (wav/mp3)", type=["wav", "mp3"] )

    if st.button("Send Voice Request"):
        if audio_file is None:
            st.error("Please upload an audio file.")
        else:
            files = {"audio": (audio_file.name, audio_file, audio_file.type)}
            params = {"ticket_id": voice_ticket or "UI-VOICE-" + str(len(st.session_state.activity_feed) + 1)}
            try:
                r = requests.post(CUSTOMER_API_URL + "/it-support/voice", params=params, files=files, timeout=10)
                if r.status_code == 200:
                    res = r.json()
                    st.success(f"Decision: {res.get('decision')}")
                    append_activity(f"Voice request {params['ticket_id']} processed — {res.get('decision')}")
                else:
                    st.error("Support agent voice endpoint returned an error.")
            except Exception:
                st.error("Unable to reach Support Agent API.")

    # Activity feed
    st.sidebar.subheader("Activity Feed")
    for entry in st.session_state.activity_feed[:20]:
        st.sidebar.write(entry)