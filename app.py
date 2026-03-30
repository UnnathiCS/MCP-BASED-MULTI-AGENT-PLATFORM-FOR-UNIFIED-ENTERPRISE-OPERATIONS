import streamlit as st
import requests
import uuid

# =========================
# CONFIG
# =========================

SUPPORT_TEXT_API = "http://127.0.0.1:8000/it-support/text"
SUPPORT_VOICE_API = "http://127.0.0.1:8000/it-support/voice"
DOCUMENT_API = "http://127.0.0.1:8001/review"

st.set_page_config(
    page_title="Enterprise AI Agent Dashboard",
    layout="wide"
)

# =========================
# UTILITIES
# =========================

def check_agent_status(url):
    try:
        requests.get(url, timeout=2)
        return True
    except:
        return False


def risk_color(level):
    if level == "Low":
        return "green"
    if level == "Medium":
        return "orange"
    return "red"


# =========================
# SIDEBAR
# =========================

st.sidebar.title("AI Agent Control Panel")

support_status = check_agent_status("http://127.0.0.1:8000/docs")
doc_status = check_agent_status("http://127.0.0.1:8001/docs")

st.sidebar.markdown("### Agent Status")

st.sidebar.write(
    f"IT Support Agent: {'🟢 Running' if support_status else '🔴 Offline'}"
)

st.sidebar.write(
    f"Document Review Agent: {'🟢 Running' if doc_status else '🔴 Offline'}"
)

st.sidebar.markdown("---")

st.sidebar.info(
"""
System Architecture

Dashboard → Streamlit  
Support Agent → FastAPI (8000)  
Document Agent → FastAPI (8001)
"""
)

# =========================
# TITLE
# =========================

st.title("Enterprise AI Multi-Agent System")

st.write(
"""
This system demonstrates two enterprise AI agents:

• **IT Support Agent** → resolves IT issues (text + voice)  
• **Document Review Agent** → analyzes contracts and policies
"""
)

# =========================
# TABS
# =========================

tab1, tab2 = st.tabs(["IT Support Agent", "Document Review Agent"])

# =========================================================
# IT SUPPORT AGENT
# =========================================================

with tab1:

    st.header("IT Support Assistant")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # ----------------------
    # TEXT SUPPORT
    # ----------------------

    st.subheader("Text Support")

    user_input = st.text_input("Describe your IT issue")

    if st.button("Submit Text Ticket"):

        if user_input:

            ticket_id = str(uuid.uuid4())[:8]

            payload = {
                "ticket_id": ticket_id,
                "message": user_input
            }

            try:

                response = requests.post(
                    SUPPORT_TEXT_API,
                    json=payload
                )

                result = response.json()

                st.session_state.chat_history.append({
                    "user": user_input,
                    "response": result
                })

            except:

                st.error("Support Agent not reachable")

    # ----------------------
    # VOICE SUPPORT
    # ----------------------

    st.subheader("Voice Support")

    voice_file = st.file_uploader(
        "Upload voice request (.wav)",
        type=["wav"]
    )

    if st.button("Submit Voice Ticket"):

        if voice_file:

            ticket_id = str(uuid.uuid4())[:8]

            files = {
                "audio": (
                    voice_file.name,
                    voice_file,
                    "audio/wav"
                )
            }

            params = {
                "ticket_id": ticket_id
            }

            try:

                response = requests.post(
                    SUPPORT_VOICE_API,
                    params=params,
                    files=files
                )

                result = response.json()

                st.session_state.chat_history.append({
                    "user": "[Voice Request]",
                    "response": result
                })

            except:

                st.error("Voice Support Agent not reachable")

    # ----------------------
    # CHAT HISTORY
    # ----------------------

    st.subheader("Support Conversation")

    for chat in reversed(st.session_state.chat_history):

        st.markdown(f"**User:** {chat['user']}")

        res = chat["response"]

        st.write("Decision:", res.get("decision"))
        st.write("Reason:", res.get("reason"))

        if res.get("answer"):
            st.success(res["answer"])

        if res.get("severity"):
            st.warning(f"Severity: {res['severity']}")

        st.markdown("---")

# =========================================================
# DOCUMENT REVIEW AGENT
# =========================================================

with tab2:

    st.header("Document Risk Review")

    uploaded_file = st.file_uploader(
        "Upload document",
        type=["pdf"]
    )

    if uploaded_file:

        if st.button("Analyze Document"):

            files = {
                "file": (
                    uploaded_file.name,
                    uploaded_file,
                    "application/pdf"
                )
            }

            try:

                response = requests.post(
                    DOCUMENT_API,
                    files=files,
                    timeout=120
                )

                result = response.json()

                st.subheader("Analysis Result")

                st.write("Document Type:", result.get("document_type"))

                if "risk_level" in result:
                    st.write("Risk Level:", result["risk_level"])

                if "risk_score" in result:
                    st.write("Risk Score:", result["risk_score"])

                if "clause_analysis" in result:

                    st.markdown("### Clause Analysis")

                    for clause, details in result["clause_analysis"].items():

                        st.write("Clause:", clause)
                        st.write("Status:", details.get("status"))
                        st.write("Similarity:", details.get("similarity_score"))

                        if details.get("snippet"):
                            st.caption(details["snippet"])

                        st.markdown("---")

                if result.get("suggestions"):

                    st.markdown("### Suggestions")

                    for clause, suggestion in result["suggestions"].items():
                        st.warning(f"{clause}: {suggestion}")

            except Exception as e:

                st.error("Document Review Agent Error")
                st.text(str(e))